from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from codex_room.agent import (
    AgentDecisionValidationError,
    AgentTurnTerminalError,
    AgentTurnStateUnknownError,
    CodexAgentAdapter,
    InterruptOutcome,
    ROOM_MODEL,
    ROOM_REASONING_EFFORT,
)
from codex_room.custom_capability_registration import VerificationReceipt
from codex_room.models import Outcome


class InitializingClient:
    def __init__(self, config) -> None:
        self.config = config
        self.closed = False

    async def account(self, *, refresh_token: bool):
        assert refresh_token is False
        return SimpleNamespace(
            model_dump=lambda **_kwargs: {"authenticated": True, "email": "hidden"}
        )

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_initialize_uses_explicit_codex_runtime(monkeypatch, tmp_path: Path):
    import openai_codex

    created: list[InitializingClient] = []

    def build_client(config=None):
        client = InitializingClient(config)
        created.append(client)
        return client

    runtime = tmp_path / "codex.exe"
    monkeypatch.setattr(openai_codex, "AsyncCodex", build_client)
    adapter = CodexAgentAdapter(codex_bin=str(runtime))

    account = await adapter.initialize()

    assert account == {"authenticated": True}
    assert created[0].config.codex_bin == str(runtime)
    assert created[0].config.config_overrides == (
        'model="gpt-5.6-terra"',
        'model_reasoning_effort="high"',
        "agents.enabled=false",
        "features.multi_agent_v2.enabled=false",
    )
    await adapter.close()
    assert created[0].closed is True


class CompactingThread:
    def __init__(self) -> None:
        self.id = "thread-one"
        self.compact_calls = 0
        self.reads = 0
        self.compaction_id: str | None = None

    async def compact(self) -> None:
        self.compact_calls += 1

    async def read(self, *, include_turns: bool = False):
        self.reads += 1
        # The first post-request read deliberately returns stale idle state. The
        # adapter must wait for the new persisted compaction item, not trust it.
        status_type = "active" if self.reads == 3 else "idle"
        if self.reads >= 4:
            self.compaction_id = "compact-new"
        turns = []
        if include_turns and self.compaction_id:
            turns = [SimpleNamespace(items=[SimpleNamespace(
                type="contextCompaction", id=self.compaction_id
            )])]
        status = SimpleNamespace(type=status_type)
        return SimpleNamespace(
            thread=SimpleNamespace(status=SimpleNamespace(root=status), turns=turns)
        )


class JsonRpcFailure(RuntimeError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"JSON-RPC error {code}: {message}")
        self.code = code


class BlockingHandle:
    def __init__(self, interrupt_error: Exception | None) -> None:
        self.interrupt_error = interrupt_error
        self.started = asyncio.Event()

    async def run(self):
        self.started.set()
        await asyncio.Event().wait()

    async def interrupt(self) -> None:
        if self.interrupt_error is not None:
            raise self.interrupt_error


class TurningThread:
    id = "thread-turning"

    def __init__(self, handle: BlockingHandle) -> None:
        self.handle = handle
        self.turn_kwargs: dict = {}

    async def read(self, **_kwargs):
        status = SimpleNamespace(type="idle")
        return SimpleNamespace(thread=SimpleNamespace(status=SimpleNamespace(root=status)))

    async def turn(self, _prompt: str, **kwargs):
        self.turn_kwargs = kwargs
        return self.handle


class HistoryHandle(BlockingHandle):
    id = "turn-expected"

    def __init__(self) -> None:
        super().__init__(None)
        self.cancelled = asyncio.Event()

    async def run(self):
        self.started.set()
        try:
            await asyncio.Event().wait()
        finally:
            self.cancelled.set()


class HistoryThread(TurningThread):
    id = "thread-history"

    def __init__(self, handle: HistoryHandle, turn_ids: list[str] | None = None) -> None:
        super().__init__(handle)
        self.turn_ids = turn_ids or [handle.id]
        self.reads = 0

    async def read(self, *, include_turns: bool = False):
        self.reads += 1
        if not include_turns:
            status = SimpleNamespace(type="idle")
            return SimpleNamespace(
                thread=SimpleNamespace(status=SimpleNamespace(root=status))
            )
        turns = [
            SimpleNamespace(
                id=turn_id,
                status=SimpleNamespace(value="completed"),
                error=None,
                started_at=1,
                completed_at=2,
                duration_ms=1000,
                items_view="full",
                items=[
                    SimpleNamespace(
                        type="agentMessage",
                        phase=SimpleNamespace(value="final_answer"),
                        text='{"outcome":"FINISH","message":"recovered"}',
                    )
                ],
            )
            for turn_id in self.turn_ids
        ]
        return SimpleNamespace(thread=SimpleNamespace(turns=turns))


class InterruptedRaceHandle:
    id = "turn-interrupted-race"

    def __init__(self) -> None:
        self.release_completion = asyncio.Event()
        self.cancelled = asyncio.Event()

    async def run(self):
        try:
            await self.release_completion.wait()
            # Let the interrupted history read return first, so this is a genuine
            # scheduling race rather than a pre-completed stream task.
            await asyncio.sleep(0)
            return SimpleNamespace(
                final_response='{"outcome":"FINISH","message":"notification wins"}',
                usage=None,
                items=[],
            )
        finally:
            self.cancelled.set()


class InterruptedRaceThread:
    id = "thread-interrupted-race"

    def __init__(self, handle: InterruptedRaceHandle) -> None:
        self.handle = handle

    async def read(self, *, include_turns: bool = False):
        assert include_turns
        self.handle.release_completion.set()
        turn = SimpleNamespace(
            id=self.handle.id,
            status=SimpleNamespace(value="interrupted"),
            error=None,
            items=[],
        )
        return SimpleNamespace(thread=SimpleNamespace(turns=[turn]))


class FailedRaceHandle(InterruptedRaceHandle):
    id = "turn-failed-race"

    async def run(self):
        try:
            await self.release_completion.wait()
            return SimpleNamespace(
                final_response='{"outcome":"FINISH","message":"must not win"}',
                usage=None,
                items=[],
            )
        finally:
            self.cancelled.set()


class FailedRaceThread:
    id = "thread-failed-race"

    def __init__(self, handle: FailedRaceHandle) -> None:
        self.handle = handle

    async def read(self, *, include_turns: bool = False):
        assert include_turns
        self.handle.release_completion.set()
        # Make the apparently successful notification result available before the
        # authoritative failed history response is returned.
        await asyncio.sleep(0)
        error = SimpleNamespace(
            message="authoritative failure",
            codex_error_info=SimpleNamespace(
                root=SimpleNamespace(value="usageLimitExceeded")
            ),
        )
        turn = SimpleNamespace(
            id=self.handle.id,
            status=SimpleNamespace(value="failed"),
            error=error,
            items=[],
        )
        return SimpleNamespace(thread=SimpleNamespace(turns=[turn]))


class InterruptedHistoryThread:
    id = "thread-genuine-interruption"

    def __init__(self, handle: HistoryHandle) -> None:
        self.handle = handle

    async def read(self, *, include_turns: bool = False):
        assert include_turns
        turn = SimpleNamespace(
            id=self.handle.id,
            status=SimpleNamespace(value="interrupted"),
            error=None,
            items=[],
        )
        return SimpleNamespace(thread=SimpleNamespace(turns=[turn]))


class InvalidDecisionHandle:
    id = "turn-invalid-decision"

    async def run(self):
        usage = SimpleNamespace(
            model_dump=lambda **_kwargs: {
                "input_tokens": 100,
                "cached_input_tokens": 0,
                "output_tokens": 20,
                "reasoning_output_tokens": 5,
                "total_tokens": 120,
            }
        )
        return SimpleNamespace(
            final_response=json.dumps(
                {
                    "action": "EVIDENCE",
                    "message": "inspect",
                    "delegations": None,
                    "evidence_requests": [
                        {
                            "operation": "SEARCH",
                            "source": "core",
                            "room_id": None,
                            "path": "",
                            "query": "TransactionAction",
                            "include_globs": [],
                            "exclude_globs": [],
                            "include_hidden": False,
                            "case_sensitive": True,
                            "max_files": 10,
                            "max_matches": 20,
                        }
                    ],
                    "history_requests": None,
                }
            ),
            usage=usage,
            items=[],
        )


@pytest.mark.asyncio
async def test_invalid_transaction_decision_retains_completed_turn_telemetry():
    adapter = CodexAgentAdapter()
    thread = SimpleNamespace(id="thread-invalid-decision")
    handle = InvalidDecisionHandle()

    with pytest.raises(AgentDecisionValidationError) as raised:
        await adapter._consume_handle(
            {"id": "agent-one"},
            thread,
            handle,
            transactional=True,
        )

    error = raised.value
    assert "Validation error:" in str(error)
    assert "path" in str(error)
    assert error.usage is not None
    assert error.usage["total_tokens"] == 120
    assert error.activity == []
    assert error.thread_id == "thread-invalid-decision"
    assert error.turn_id == "turn-invalid-decision"
    assert error.completion_source == "notification"


class FailedHistoryHandle:
    id = "turn-usage-wall"

    async def run(self):
        raise RuntimeError("You've hit your usage limit")


class FailedHistoryThread:
    id = "thread-usage-wall"

    async def read(self, *, include_turns: bool = False):
        assert include_turns
        error = SimpleNamespace(
            message=(
                "You've hit your usage limit. Please try again at "
                "Sep 6th, 2026 1:33 AM."
            ),
            codex_error_info=SimpleNamespace(
                root=SimpleNamespace(value="usageLimitExceeded")
            ),
        )
        turn = SimpleNamespace(
            id=FailedHistoryHandle.id,
            status=SimpleNamespace(value="failed"),
            error=error,
            items=[],
        )
        return SimpleNamespace(thread=SimpleNamespace(turns=[turn]))


@pytest.mark.asyncio
async def test_failed_notification_recovers_authoritative_usage_limit_code():
    adapter = CodexAgentAdapter()

    with pytest.raises(AgentTurnTerminalError) as raised:
        await adapter._run_with_reconciliation(
            FailedHistoryThread(), FailedHistoryHandle()
        )

    assert raised.value.codex_error_info == "usageLimitExceeded"
    assert "Sep 6th, 2026 1:33 AM" in str(raised.value)


@pytest.mark.asyncio
async def test_successful_notification_wins_interrupted_history_race():
    adapter = CodexAgentAdapter()
    adapter.RECONCILIATION_INTERVAL_SECONDS = 0.01
    adapter.RECONCILIATION_TERMINAL_GRACE_SECONDS = 0.05
    handle = InterruptedRaceHandle()

    result, completion_source = await adapter._run_with_reconciliation(
        InterruptedRaceThread(handle), handle
    )

    assert completion_source == "notification"
    assert result.final_response == '{"outcome":"FINISH","message":"notification wins"}'
    assert handle.cancelled.is_set()


@pytest.mark.asyncio
async def test_authoritative_failed_history_cannot_be_overridden_by_notification_success():
    adapter = CodexAgentAdapter()
    adapter.RECONCILIATION_INTERVAL_SECONDS = 0.01
    adapter.RECONCILIATION_TERMINAL_GRACE_SECONDS = 0.05
    handle = FailedRaceHandle()

    with pytest.raises(AgentTurnTerminalError) as raised:
        await adapter._run_with_reconciliation(FailedRaceThread(handle), handle)

    assert raised.value.codex_error_info == "usageLimitExceeded"
    assert handle.cancelled.is_set()


@pytest.mark.asyncio
async def test_genuine_interruption_without_completion_remains_terminal():
    adapter = CodexAgentAdapter()
    adapter.RECONCILIATION_INTERVAL_SECONDS = 0.01
    adapter.RECONCILIATION_TERMINAL_GRACE_SECONDS = 0.01
    handle = HistoryHandle()

    with pytest.raises(AgentTurnTerminalError, match="interrupted"):
        await adapter._run_with_reconciliation(InterruptedHistoryThread(handle), handle)

    assert handle.cancelled.is_set()


class ResumeClient:
    def __init__(self, resumed_id: str = "thread-one", error: Exception | None = None) -> None:
        self.resumed_id = resumed_id
        self.error = error
        self.calls: list[tuple[str, dict]] = []

    async def thread_resume(self, thread_id: str, **kwargs):
        self.calls.append((thread_id, kwargs))
        if self.error is not None:
            raise self.error
        return SimpleNamespace(id=self.resumed_id)


class ContextStartThread:
    def __init__(self, thread_id: str) -> None:
        self.id = thread_id
        self.name: str | None = None

    async def set_name(self, name: str) -> None:
        self.name = name


class ContextStartClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.thread = ContextStartThread("thread-assignment")

    async def thread_start(self, **kwargs):
        self.calls.append(kwargs)
        return self.thread


class ExactUsageSystemErrorThread:
    def __init__(self, thread_id: str) -> None:
        self.id = thread_id

    async def read(self):
        status = SimpleNamespace(type="systemError")
        return SimpleNamespace(
            thread=SimpleNamespace(status=SimpleNamespace(root=status))
        )


class ExactUsageResumeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def thread_resume(self, thread_id: str, **kwargs):
        self.calls.append((thread_id, kwargs))
        return ExactUsageSystemErrorThread(thread_id)


@pytest.mark.asyncio
async def test_assignment_context_thread_start_does_not_replace_persistent_agent_cache(
    tmp_path: Path,
):
    adapter = CodexAgentAdapter()
    client = ContextStartClient()
    adapter._client = client
    permanent = SimpleNamespace(id="thread-permanent")
    adapter._threads["agent-one"] = permanent
    agent = {
        "id": "agent-one",
        "name": "Agent C",
        "thread_id": "thread-permanent",
        "developer_instructions": "persistent instructions",
    }

    thread_id = await adapter.start_context_thread(
        agent, tmp_path, label="assignment assignment-one"
    )

    assert thread_id == "thread-assignment"
    assert adapter._threads["agent-one"] is permanent
    assert client.thread.name == "Codex Room · Agent C · assignment assignment-one"
    assert client.calls[0]["ephemeral"] is False
    assert client.calls[0]["developer_instructions"] == "persistent instructions"


@pytest.mark.asyncio
async def test_assignment_context_usage_continuation_resumes_exact_non_agent_thread(
    tmp_path: Path,
):
    adapter = CodexAgentAdapter()
    client = ExactUsageResumeClient()
    adapter._client = client
    permanent = SimpleNamespace(id="thread-permanent")
    adapter._threads["agent-one"] = permanent
    agent = {
        "id": "agent-one",
        "thread_id": "thread-permanent",
        "developer_instructions": "persistent instructions",
    }

    await adapter.prepare_usage_continuation(
        agent, tmp_path, "thread-assignment"
    )

    assert adapter._threads["agent-one"] is permanent
    assert client.calls[0][0] == "thread-assignment"
    assert client.calls[0][1]["developer_instructions"] == "persistent instructions"
    assert "agent-one" in adapter._usage_continuation_agents


class UsageSystemErrorThread:
    id = "thread-one"

    async def read(self):
        status = SimpleNamespace(type="systemError")
        return SimpleNamespace(
            thread=SimpleNamespace(status=SimpleNamespace(root=status))
        )


class UsageResumeClient(ResumeClient):
    async def thread_resume(self, thread_id: str, **kwargs):
        self.calls.append((thread_id, kwargs))
        return UsageSystemErrorThread()


@pytest.mark.asyncio
async def test_usage_continuation_rebinds_same_system_error_thread(tmp_path: Path):
    adapter = CodexAgentAdapter()
    client = UsageResumeClient()
    adapter._client = client
    adapter._threads["agent-one"] = SimpleNamespace(id="thread-one")
    agent = {
        "id": "agent-one",
        "thread_id": "thread-one",
        "developer_instructions": "persistent instructions",
    }

    await adapter.prepare_usage_continuation(agent, tmp_path)

    assert adapter._threads["agent-one"].id == "thread-one"
    assert "agent-one" in adapter._usage_continuation_agents
    assert client.calls[0][0] == "thread-one"


@pytest.mark.asyncio
async def test_compact_agent_waits_until_persistent_thread_is_idle(tmp_path: Path):
    adapter = CodexAgentAdapter()
    adapter._client = object()
    thread = CompactingThread()
    adapter._threads["agent-one"] = thread
    agent = {"id": "agent-one", "thread_id": thread.id}

    await adapter.compact_agent(agent, tmp_path)

    assert thread.compact_calls == 1
    assert thread.reads == 4


@pytest.mark.asyncio
async def test_profile_rebind_replaces_only_selected_cache_entry(tmp_path: Path):
    adapter = CodexAgentAdapter()
    client = ResumeClient()
    adapter._client = client
    previous = SimpleNamespace(id="thread-one")
    other = SimpleNamespace(id="thread-other")
    adapter._threads.update({"agent-one": previous, "agent-other": other})
    agent = {
        "id": "agent-one",
        "thread_id": "thread-one",
        "developer_instructions": "triad instructions",
    }

    rebound_id = await adapter.rebind_agent_profile(agent, tmp_path)

    assert rebound_id == "thread-one"
    assert adapter._threads["agent-one"] is not previous
    assert adapter._threads["agent-other"] is other
    assert client.calls[0][0] == "thread-one"
    assert client.calls[0][1]["developer_instructions"] == "triad instructions"
    assert client.calls[0][1]["cwd"] == str(tmp_path)
    assert client.calls[0][1]["model"] == ROOM_MODEL


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("client", "message"),
    [
        (ResumeClient(resumed_id="thread-replacement"), "different Codex thread ID"),
        (ResumeClient(error=RuntimeError("resume failed")), "resume failed"),
    ],
)
async def test_profile_rebind_fails_closed_and_leaves_stale_cache_evicted(
    tmp_path: Path, client: ResumeClient, message: str
):
    adapter = CodexAgentAdapter()
    adapter._client = client
    previous = SimpleNamespace(id="thread-one")
    adapter._threads["agent-one"] = previous
    agent = {
        "id": "agent-one",
        "thread_id": "thread-one",
        "developer_instructions": "triad instructions",
    }

    with pytest.raises(RuntimeError, match=message):
        await adapter.rebind_agent_profile(agent, tmp_path)

    assert "agent-one" not in adapter._threads


@pytest.mark.asyncio
async def test_profile_rebind_rejects_active_sdk_turn(tmp_path: Path):
    adapter = CodexAgentAdapter()
    adapter._client = ResumeClient()
    adapter._active_handles["agent-one"] = object()
    agent = {
        "id": "agent-one",
        "thread_id": "thread-one",
        "developer_instructions": "triad instructions",
    }

    with pytest.raises(RuntimeError, match="SDK turn is active"):
        await adapter.rebind_agent_profile(agent, tmp_path)

    assert adapter._client.calls == []


@pytest.mark.asyncio
async def test_cancellation_preserves_primary_cause_when_turn_is_already_inactive(
    tmp_path: Path,
):
    adapter = CodexAgentAdapter()
    adapter._client = object()
    handle = BlockingHandle(
        JsonRpcFailure(-32600, "no active turn to interrupt")
    )
    thread = TurningThread(handle)
    adapter._threads["agent-one"] = thread
    agent = {"id": "agent-one", "thread_id": thread.id}

    task = asyncio.create_task(adapter.run_agent(agent, tmp_path, "prompt"))
    await handle.started.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    assert await adapter.has_active_run("agent-one") is False


@pytest.mark.asyncio
async def test_unknown_interrupt_retains_handle_until_retirement_is_confirmed(
    tmp_path: Path,
):
    adapter = CodexAgentAdapter()
    adapter._client = object()
    handle = BlockingHandle(RuntimeError("transport unavailable"))
    thread = TurningThread(handle)
    adapter._threads["agent-one"] = thread
    agent = {"id": "agent-one", "thread_id": thread.id}

    task = asyncio.create_task(adapter.run_agent(agent, tmp_path, "prompt"))
    await handle.started.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    assert await adapter.has_active_run("agent-one") is True
    assert await adapter.interrupt("agent-one") == InterruptOutcome.UNKNOWN

    handle.interrupt_error = JsonRpcFailure(-32600, "no active turn to interrupt")
    assert await adapter.interrupt("agent-one") == InterruptOutcome.ALREADY_INACTIVE
    assert await adapter.has_active_run("agent-one") is False


def test_only_exact_no_active_json_rpc_error_is_benign():
    assert CodexAgentAdapter._is_already_inactive_error(
        JsonRpcFailure(-32600, "no active turn to interrupt")
    )
    assert not CodexAgentAdapter._is_already_inactive_error(
        JsonRpcFailure(-32600, "invalid request")
    )
    assert not CodexAgentAdapter._is_already_inactive_error(
        JsonRpcFailure(-32000, "no active turn to interrupt")
    )


@pytest.mark.asyncio
async def test_exact_history_completion_recovers_a_lost_completion_notification(tmp_path: Path):
    adapter = CodexAgentAdapter()
    adapter._client = object()
    adapter.RECONCILIATION_INTERVAL_SECONDS = 0.01
    handle = HistoryHandle()
    thread = HistoryThread(handle)
    adapter._threads["agent-one"] = thread
    agent = {"id": "agent-one", "thread_id": thread.id}
    bound: list[tuple[str, str]] = []

    async def on_started(thread_id: str, turn_id: str) -> None:
        bound.append((thread_id, turn_id))

    result = await adapter.run_agent(agent, tmp_path, "prompt", on_started=on_started)

    assert result.decision.outcome == Outcome.FINISH
    assert result.decision.message == "recovered"
    assert result.completion_source == "history"
    assert result.thread_id == thread.id
    assert result.turn_id == handle.id
    assert bound == [(thread.id, handle.id)]
    assert thread.turn_kwargs["model"] == ROOM_MODEL
    assert thread.turn_kwargs["effort"] == ROOM_REASONING_EFFORT
    assert thread.reads >= 1
    assert handle.cancelled.is_set()


@pytest.mark.asyncio
async def test_run_agent_uses_explicit_per_turn_model_and_effort(tmp_path: Path):
    adapter = CodexAgentAdapter()
    adapter._client = object()
    adapter.RECONCILIATION_INTERVAL_SECONDS = 0.01
    handle = HistoryHandle()
    thread = HistoryThread(handle)
    adapter._threads["agent-one"] = thread
    agent = {"id": "agent-one", "thread_id": thread.id}

    await adapter.run_agent(
        agent,
        tmp_path,
        "prompt",
        model="gpt-5.6-luna",
        reasoning_effort="medium",
    )

    assert thread.turn_kwargs["model"] == "gpt-5.6-luna"
    assert thread.turn_kwargs["effort"] == "medium"


@pytest.mark.asyncio
async def test_run_agent_rejects_astra_without_room_authorization(tmp_path: Path):
    adapter = CodexAgentAdapter()
    agent = {"id": "agent-one", "thread_id": "thread-one"}

    with pytest.raises(ValueError, match="prohibited unless Astra"):
        await adapter.run_agent(
            agent,
            tmp_path,
            "prompt",
            model="gpt-6-astra",
            reasoning_effort="medium",
        )


@pytest.mark.asyncio
async def test_run_agent_allows_astra_with_room_authorization(tmp_path: Path):
    adapter = CodexAgentAdapter()
    adapter._client = object()
    adapter.RECONCILIATION_INTERVAL_SECONDS = 0.01
    handle = HistoryHandle()
    thread = HistoryThread(handle)
    adapter._threads["agent-one"] = thread
    agent = {"id": "agent-one", "thread_id": thread.id}

    await adapter.run_agent(
        agent,
        tmp_path,
        "prompt",
        model="gpt-6-astra",
        reasoning_effort="medium",
        allow_astra=True,
    )

    assert thread.turn_kwargs["model"] == "gpt-6-astra"
    assert thread.turn_kwargs["effort"] == "medium"


@pytest.mark.asyncio
async def test_completed_turn_with_different_id_cannot_satisfy_execution(tmp_path: Path):
    adapter = CodexAgentAdapter()
    adapter._client = object()
    adapter.RECONCILIATION_INTERVAL_SECONDS = 0.01
    handle = HistoryHandle()
    thread = HistoryThread(handle, turn_ids=["turn-someone-else"])
    adapter._threads["agent-one"] = thread
    agent = {"id": "agent-one", "thread_id": thread.id}

    task = asyncio.create_task(adapter.run_agent(agent, tmp_path, "prompt"))
    await asyncio.sleep(0.05)
    assert not task.done()
    assert thread.reads >= 1
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_restart_lookup_quarantines_when_exact_turn_is_absent(tmp_path: Path):
    adapter = CodexAgentAdapter()
    adapter._client = SimpleNamespace(
        _client=SimpleNamespace(
            _subscribe_turn_notifications=lambda _turn_id: SimpleNamespace()
        )
    )
    handle = HistoryHandle()
    thread = HistoryThread(handle, turn_ids=["turn-someone-else"])
    adapter._threads["agent-one"] = thread
    agent = {"id": "agent-one", "thread_id": thread.id}

    with pytest.raises(AgentTurnStateUnknownError, match="absent from complete thread history"):
        await adapter.resume_agent(agent, tmp_path, thread.id, handle.id)

    assert await adapter.has_active_run("agent-one") is False


def test_safe_activity_promotes_codex_room_capability_result() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "assert_file",
        "ok": True,
        "subject": {"path": "result.json", "exists": True, "is_file": True},
        "checks": [{"name": "exists", "expected": True, "actual": True, "ok": True}],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command="codex-room-cap assert-file result.json --exists",
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])

    assert activity == [
        {
            "type": "deterministic_capability",
            "status": "completed",
            "capability": "assert_file",
            "ok": True,
            "result": payload,
        }
    ]


def test_safe_activity_does_not_persist_arbitrary_command_output() -> None:
    item = SimpleNamespace(
        type="commandExecution",
        command="python secret_script.py",
        aggregated_output="sensitive output",
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item]) == [
        {"type": "command_execution", "status": "completed"}
    ]


def test_safe_activity_rejects_forged_or_chained_capability_command() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "assert_file",
        "ok": True,
        "subject": {"path": "result.json"},
        "checks": [],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command="echo codex-room-cap assert-file result.json --exists",
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )
    chained = SimpleNamespace(
        type="commandExecution",
        command="codex-room-cap assert-file result.json --exists ; echo forged",
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item, chained]) == [
        {"type": "command_execution", "status": "completed"},
        {"type": "command_execution", "status": "completed"},
    ]


def test_safe_activity_normalizes_pinned_sdk_camel_case_types() -> None:
    items = [
        SimpleNamespace(type="fileChange", status=SimpleNamespace(value="completed")),
        SimpleNamespace(type="mcpToolCall", status=SimpleNamespace(value="completed")),
        SimpleNamespace(type="dynamicToolCall", status=SimpleNamespace(value="failed")),
        SimpleNamespace(type="subAgentActivity", status=None),
        SimpleNamespace(type="webSearch", status=None),
    ]

    assert CodexAgentAdapter._safe_activity(items) == [
        {"type": "file_change", "status": "completed"},
        {"type": "mcp_tool_call", "status": "completed"},
        {"type": "dynamic_tool_call", "status": "failed"},
        {"type": "sub_agent_activity", "status": "completed"},
        {"type": "web_search", "status": "completed"},
    ]


def test_safe_activity_promotes_shell_wrapped_capability_from_parsed_action() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "assert_file",
        "ok": True,
        "subject": {"path": "p4_probe.json", "exists": True, "is_file": True},
        "checks": [{"name": "exists", "expected": True, "actual": True, "ok": True}],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe' "
            "-NoProfile -Command "
            "'codex-room-cap assert-file p4_probe.json --exists'"
        ),
        command_actions=[
            SimpleNamespace(
                root=SimpleNamespace(
                    type="unknown",
                    command="codex-room-cap assert-file p4_probe.json --exists",
                )
            )
        ],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item]) == [
        {
            "type": "deterministic_capability",
            "status": "completed",
            "capability": "assert_file",
            "ok": True,
            "result": payload,
        }
    ]


def test_safe_activity_rejects_shell_wrapped_chained_capability_action() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "assert_file",
        "ok": True,
        "subject": {"path": "p4_probe.json"},
        "checks": [],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "powershell.exe -Command "
            "'codex-room-cap assert-file p4_probe.json --exists; echo forged'"
        ),
        command_actions=[
            SimpleNamespace(
                root=SimpleNamespace(
                    type="unknown",
                    command=(
                        "codex-room-cap assert-file p4_probe.json --exists; echo forged"
                    ),
                )
            )
        ],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item]) == [
        {"type": "command_execution", "status": "completed"}
    ]



def test_safe_activity_records_registry_list_without_arbitrary_output() -> None:
    payload = {
        "codex_room_registry": 1,
        "operation": "list",
        "capabilities": [
            {
                "id": "assert_file",
                "description": "ignored in compact telemetry",
                "origin": "core",
                "scope": "core",
                "version": "1",
                "implementation_sha256": "a" * 64,
                "input_schema": {"type": "object"},
            }
        ],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command="powershell.exe -Command 'codex-room-cap list'",
        command_actions=[
            SimpleNamespace(
                root=SimpleNamespace(type="unknown", command="codex-room-cap list")
            )
        ],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item]) == [
        {
            "type": "deterministic_capability_registry",
            "status": "completed",
            "operation": "list",
            "capabilities": [
                {
                    "id": "assert_file",
                    "origin": "core",
                    "scope": "core",
                    "version": "1",
                    "implementation_sha256": "a" * 64,
                }
            ],
        }
    ]


def test_safe_activity_records_registry_list_from_outer_powershell_when_actions_are_empty() -> None:
    payload = {
        "codex_room_registry": 1,
        "operation": "list",
        "capabilities": [
            {
                "id": "assert_file",
                "origin": "core",
                "scope": "core",
                "version": "1",
                "implementation_sha256": "d" * 64,
            }
        ],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe' "
            "-NoProfile -Command 'codex-room-cap list'"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item]) == [
        {
            "type": "deterministic_capability_registry",
            "status": "completed",
            "operation": "list",
            "capabilities": [
                {
                    "id": "assert_file",
                    "origin": "core",
                    "scope": "core",
                    "version": "1",
                    "implementation_sha256": "d" * 64,
                }
            ],
        }
    ]


def test_safe_activity_rejects_chained_outer_powershell_registry_command() -> None:
    payload = {
        "codex_room_registry": 1,
        "operation": "list",
        "capabilities": [{"id": "assert_file"}],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "powershell.exe -NoProfile -Command "
            "'codex-room-cap list; echo forged'"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item]) == [
        {"type": "command_execution", "status": "completed"}
    ]


def test_safe_activity_records_registry_inspection() -> None:
    payload = {
        "codex_room_registry": 1,
        "operation": "inspect",
        "capability": {
            "id": "assert_file",
            "description": "Exact assertions.",
            "origin": "core",
            "scope": "core",
            "version": "1",
            "implementation_sha256": "b" * 64,
            "permissions": {"workspace_read": True},
            "side_effects": "none",
            "verification": {"status": "verified"},
            "input_schema": {"type": "object"},
        },
    }
    item = SimpleNamespace(
        type="commandExecution",
        command="codex-room-cap inspect assert_file",
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])

    assert activity[0]["type"] == "deterministic_capability_registry"
    assert activity[0]["operation"] == "inspect"
    assert activity[0]["capability"] == "assert_file"
    assert "input_schema" not in activity[0]["manifest"]
    assert activity[0]["manifest"]["implementation_sha256"] == "b" * 64


def test_safe_activity_promotes_outer_powershell_registry_invocation_without_actions() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "assert_file",
        "capability_version": "1",
        "implementation_sha256": "e" * 64,
        "ok": True,
        "subject": {"path": "probe.json", "exists": True, "is_file": True},
        "checks": [{"name": "exists", "expected": True, "actual": True, "ok": True}],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "powershell.exe -NoProfile -Command "
            "'codex-room-cap invoke assert_file --input-json "
            "\"{\\\"path\\\":\\\"probe.json\\\",\\\"exists\\\":true}\"'"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item]) == [
        {
            "type": "deterministic_capability",
            "status": "completed",
            "capability": "assert_file",
            "ok": True,
            "result": payload,
        }
    ]


def test_safe_activity_promotes_generic_registry_invocation() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "assert_file",
        "capability_version": "1",
        "implementation_sha256": "c" * 64,
        "ok": True,
        "subject": {"path": "probe.json", "exists": True, "is_file": True},
        "checks": [{"name": "exists", "expected": True, "actual": True, "ok": True}],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "powershell.exe -Command "
            "'codex-room-cap invoke assert_file --input-json ...'"
        ),
        command_actions=[
            SimpleNamespace(
                root=SimpleNamespace(
                    type="unknown",
                    command=(
                        "codex-room-cap invoke assert_file "
                        "--input-json '{\"path\":\"probe.json\",\"exists\":true}'"
                    ),
                )
            )
        ],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item]) == [
        {
            "type": "deterministic_capability",
            "status": "completed",
            "capability": "assert_file",
            "ok": True,
            "result": payload,
        }
    ]


def test_safe_activity_persists_only_declared_generic_capability_result_fields() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "search_text",
        "capability_version": "1",
        "implementation_sha256": "f" * 64,
        "ok": True,
        "durable_result_fields": ["evidence"],
        "evidence": {
            "match_count": 1,
            "matches": [{"path": "notes.txt", "line": 4, "excerpt": "needle"}],
        },
        "private_debug": "must not be persisted",
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "codex-room-cap invoke search_text "
            "--input-json '{\"query\":\"needle\"}'"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])

    assert activity == [
        {
            "type": "deterministic_capability",
            "status": "completed",
            "capability": "search_text",
            "ok": True,
            "result": {
                "codex_room_capability": 1,
                "capability": "search_text",
                "capability_version": "1",
                "implementation_sha256": "f" * 64,
                "ok": True,
                "durable_result_fields": ["evidence"],
                "evidence": payload["evidence"],
            },
        }
    ]


def test_safe_activity_handles_json_escaped_surrogate_text() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "find_files",
        "capability_version": "1",
        "implementation_sha256": "a" * 64,
        "ok": True,
        "durable_result_fields": ["evidence"],
        "evidence": {"matches": [{"path": "bad\udcff.txt", "size_bytes": 1}]},
    }
    item = SimpleNamespace(
        type="commandExecution",
        command="codex-room-cap invoke find_files --input-json '{}'",
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])

    assert activity[0]["type"] == "deterministic_capability"
    assert activity[0]["result"]["evidence"] == payload["evidence"]


def test_safe_activity_drops_search_text_runtime_excerpts_from_durable_evidence() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "search_text",
        "capability_version": "1",
        "implementation_sha256": "b" * 64,
        "ok": True,
        "durable_result_fields": ["evidence"],
        "evidence": {
            "query_sha256": "c" * 64,
            "query_length": 6,
            "locations": [{"path": "notes.txt", "line": 4, "column": 2}],
            "match_count": 1,
            "truncated": False,
        },
        "matches": [
            {
                "path": "notes.txt",
                "line": 4,
                "column": 2,
                "excerpt": "secret needle context",
                "excerpt_start_column": 1,
            }
        ],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "codex-room-cap invoke search_text "
            "--input-json '{\"query\":\"needle\"}'"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])

    result = activity[0]["result"]
    assert activity[0]["type"] == "deterministic_capability"
    assert activity[0]["capability"] == "search_text"
    assert result["evidence"] == payload["evidence"]
    assert "matches" not in result
    assert "secret needle context" not in json.dumps(result)


def test_safe_activity_drops_compare_files_diff_from_durable_evidence() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "compare_files",
        "capability_version": "1",
        "implementation_sha256": "d" * 64,
        "ok": True,
        "durable_result_fields": ["evidence"],
        "evidence": {
            "left": {"path": "a.txt", "sha256": "a" * 64, "size_bytes": 6},
            "right": {"path": "b.txt", "sha256": "b" * 64, "size_bytes": 5},
            "byte_equal": False,
            "text_diff": {"status": "available", "returned_diff_lines": 2},
        },
        "diff": ["-secret before", "+secret after"],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "codex-room-cap invoke compare_files "
            "--input-json '{\"left_path\":\"a.txt\",\"right_path\":\"b.txt\"}'"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])

    result = activity[0]["result"]
    assert activity[0]["type"] == "deterministic_capability"
    assert activity[0]["capability"] == "compare_files"
    assert result["evidence"] == payload["evidence"]
    assert "diff" not in result
    assert "secret before" not in json.dumps(result)


def test_safe_activity_rejects_invalid_durable_result_field_declaration() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "search_text",
        "ok": True,
        "durable_result_fields": "evidence",
        "evidence": {"match_count": 1},
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "codex-room-cap invoke search_text "
            "--input-json '{\"query\":\"needle\"}'"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item]) == [
        {"type": "command_execution", "status": "completed"}
    ]


def test_safe_activity_bounds_declared_capability_result_evidence() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "search_text",
        "capability_version": "1",
        "implementation_sha256": "f" * 64,
        "ok": True,
        "durable_result_fields": ["evidence"],
        "evidence": {"matches": [{"excerpt": "x" * 70000}]},
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "codex-room-cap invoke search_text "
            "--input-json '{\"query\":\"needle\"}'"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])
    result = activity[0]["result"]

    assert activity[0]["type"] == "deterministic_capability"
    assert activity[0]["capability"] == "search_text"
    assert result["durable_result_fields"] == ["evidence"]
    assert result["durable_result_truncated"] is True
    assert result["durable_result_original_bytes"] > 64 * 1024
    assert "evidence" not in result

def test_safe_activity_records_custom_registration_request_without_raw_cases() -> None:
    package = SimpleNamespace(
        package_sha256="b" * 64,
        manifest_sha256="a" * 64,
        implementation_sha256="c" * 64,
    )
    receipt = VerificationReceipt.create(
        package,
        case_plan_sha256="d" * 64,
        cases=[
            {
                "name": "basic",
                "input_sha256": "e" * 64,
                "expected_output_sha256": "f" * 64,
                "observed_output_sha256": "f" * 64,
                "fixtures_sha256": "0" * 64,
            }
        ],
    )
    payload = {
        "codex_room_registry": 1,
        "operation": "register",
        "ok": True,
        "state": "verification_passed_host_pending",
        "capability_id": "count_lines",
        "registration_request": {
            "capability_id": "count_lines",
            "receipt": receipt.as_dict(),
        },
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "codex-room-cap register count_lines "
            "--cases-file .codex-room/count_lines_cases.json"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])

    assert activity == [
        {
            "type": "deterministic_capability_registry",
            "status": "completed",
            "operation": "register",
            "capability": "count_lines",
            "registration_state": "verification_passed_host_pending",
            "registration_request": {
                "capability_id": "count_lines",
                "receipt": receipt.as_dict(),
            },
        }
    ]
    serialized = json.dumps(activity)
    assert "verification_passed_host_pending" in serialized
    assert "basic" in serialized
    assert "expected_output_sha256" in serialized


def test_safe_activity_preserves_custom_invocation_provenance_and_declared_result() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "count_lines",
        "capability_version": "1",
        "implementation_sha256": "a" * 64,
        "package_sha256": "b" * 64,
        "registration_sha256": "c" * 64,
        "verification_sha256": "d" * 64,
        "durable_result_fields": ["count"],
        "ok": True,
        "count": 3,
        "transient_detail": "do not persist",
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "codex-room-cap invoke count_lines "
            "--input-json '{\"text\":\"a\\nb\\nc\\n\"}'"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])
    result = activity[0]["result"]

    assert activity[0]["type"] == "deterministic_capability"
    assert activity[0]["capability"] == "count_lines"
    assert result["implementation_sha256"] == "a" * 64
    assert result["package_sha256"] == "b" * 64
    assert result["registration_sha256"] == "c" * 64
    assert result["verification_sha256"] == "d" * 64
    assert result["count"] == 3
    assert "transient_detail" not in result

def test_safe_activity_records_compact_custom_authoring_reference() -> None:
    payload = {
        "codex_room_registry": 1,
        "operation": "authoring",
        "schema_version": 1,
        "package_v1": {"secret_detail": "not durable"},
    }
    item = SimpleNamespace(
        type="commandExecution",
        command="codex-room-cap authoring",
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    assert CodexAgentAdapter._safe_activity([item]) == [
        {
            "type": "deterministic_capability_registry",
            "status": "completed",
            "operation": "authoring",
            "authoring_schema_version": 1,
        }
    ]

def test_safe_activity_promotes_file_input_capability_invocation() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "assert_file",
        "capability_version": "1",
        "implementation_sha256": "a" * 64,
        "ok": True,
        "subject": {"path": "probe.json", "exists": True, "is_file": True},
        "checks": [],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command="codex-room-cap invoke assert_file --input-file invoke-input.json",
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])

    assert activity[0]["type"] == "deterministic_capability"
    assert activity[0]["status"] == "completed"
    assert activity[0]["capability"] == "assert_file"
    assert activity[0]["result"]["ok"] is True

def test_safe_activity_promotes_direct_source_cli_without_persisting_transient_content() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "inspect_source",
        "capability_version": "2",
        "implementation_sha256": "a" * 64,
        "ok": True,
        "durable_result_fields": ["evidence"],
        "evidence": {
            "operation": "search_many",
            "query_count": 2,
            "match_count": 3,
        },
        "results": [
            {"query": "sqlite", "matches": [{"excerpt": "private transient"}]}
        ],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command=(
            "codex-room-cap source search-many core codex_room "
            "--query sqlite --query backup"
        ),
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])

    assert activity == [
        {
            "type": "deterministic_capability",
            "status": "completed",
            "capability": "inspect_source",
            "ok": True,
            "result": {
                "codex_room_capability": 1,
                "capability": "inspect_source",
                "capability_version": "2",
                "implementation_sha256": "a" * 64,
                "ok": True,
                "durable_result_fields": ["evidence"],
                "evidence": payload["evidence"],
            },
        }
    ]



def test_safe_activity_promotes_direct_source_bundle_cli() -> None:
    payload = {
        "codex_room_capability": 1,
        "capability": "inspect_source",
        "capability_version": "3",
        "implementation_sha256": "a" * 64,
        "ok": True,
        "durable_result_fields": ["evidence"],
        "evidence": {
            "operation": "bundle",
            "requested_count": 2,
            "returned_count": 2,
            "truncated": False,
        },
        "items": [{"label": "private", "content": "transient"}],
    }
    item = SimpleNamespace(
        type="commandExecution",
        command="codex-room-cap source bundle --plan-file evidence-plan.json",
        command_actions=[],
        aggregated_output=json.dumps(payload),
        status=SimpleNamespace(value="completed"),
    )

    activity = CodexAgentAdapter._safe_activity([item])

    assert activity == [
        {
            "type": "deterministic_capability",
            "status": "completed",
            "capability": "inspect_source",
            "ok": True,
            "result": {
                "codex_room_capability": 1,
                "capability": "inspect_source",
                "capability_version": "3",
                "implementation_sha256": "a" * 64,
                "ok": True,
                "durable_result_fields": ["evidence"],
                "evidence": payload["evidence"],
            },
        }
    ]



class ModelListClient:
    async def models(self, include_hidden: bool = False):
        assert include_hidden is True
        payload = {
            "data": [
                {
                    "model": "gpt-5.6-sol",
                    "display_name": "Sol",
                    "supported_reasoning_efforts": [
                        {"reasoning_effort": "medium"},
                        {"reasoning_effort": "max"},
                    ],
                    "default_reasoning_effort": "medium",
                },
                {
                    "model": "gpt-test-frontier",
                    "display_name": "Test Frontier",
                    "supported_reasoning_efforts": [
                        {"reasoning_effort": "low"},
                        {"reasoning_effort": "ultra"},
                    ],
                    "default_reasoning_effort": "low",
                },
            ]
        }
        return SimpleNamespace(model_dump=lambda **_kwargs: payload)


@pytest.mark.asyncio
async def test_list_execution_configs_uses_native_model_effort_catalog():
    adapter = CodexAgentAdapter()
    adapter._client = ModelListClient()

    catalog = await adapter.list_execution_configs()

    assert catalog["sol-medium"] == {
        "model": "gpt-5.6-sol",
        "reasoning_effort": "medium",
        "display_name": "Sol",
    }
    assert catalog["sol-max"] == {
        "model": "gpt-5.6-sol",
        "reasoning_effort": "max",
        "display_name": "Sol",
    }
    assert catalog["native:gpt-test-frontier:ultra"] == {
        "model": "gpt-test-frontier",
        "reasoning_effort": "ultra",
        "display_name": "Test Frontier",
    }


@pytest.mark.asyncio
async def test_run_agent_unrestricted_policy_bypasses_room_astra_guard(tmp_path: Path):
    adapter = CodexAgentAdapter()
    adapter._client = object()
    adapter.RECONCILIATION_INTERVAL_SECONDS = 0.01
    handle = HistoryHandle()
    thread = HistoryThread(handle)
    adapter._threads["agent-one"] = thread
    agent = {"id": "agent-one", "thread_id": thread.id}

    await adapter.run_agent(
        agent,
        tmp_path,
        "prompt",
        model="gpt-6-astra",
        reasoning_effort="high",
        unrestricted_model_access=True,
    )

    assert thread.turn_kwargs["model"] == "gpt-6-astra"
    assert thread.turn_kwargs["effort"] == "high"



class PaginatedModelListClient:
    async def models(self, include_hidden: bool = False):
        assert include_hidden is True
        payload = {
            "data": [
                {
                    "model": "gpt-5.6-sol",
                    "display_name": "Sol",
                    "supported_reasoning_efforts": [
                        {"reasoning_effort": "high"},
                    ],
                    "default_reasoning_effort": "high",
                }
            ],
            "next_cursor": "more-models",
        }
        return SimpleNamespace(model_dump=lambda **_kwargs: payload)


@pytest.mark.asyncio
async def test_list_execution_configs_rejects_partial_paginated_catalog():
    adapter = CodexAgentAdapter()
    adapter._client = PaginatedModelListClient()

    with pytest.raises(RuntimeError, match="partial native catalog"):
        await adapter.list_execution_configs()
