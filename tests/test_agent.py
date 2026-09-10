from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from codex_room.agent import (
    AgentTurnTerminalError,
    AgentTurnStateUnknownError,
    CodexAgentAdapter,
    InterruptOutcome,
    ROOM_MODEL,
    ROOM_REASONING_EFFORT,
)
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
    adapter._client = object()
    handle = HistoryHandle()
    thread = HistoryThread(handle, turn_ids=["turn-someone-else"])
    adapter._threads["agent-one"] = thread
    agent = {"id": "agent-one", "thread_id": thread.id}

    with pytest.raises(AgentTurnStateUnknownError, match="absent from complete thread history"):
        await adapter.resume_agent(agent, tmp_path, thread.id, handle.id)

    assert await adapter.has_active_run("agent-one") is False
