from __future__ import annotations

import asyncio
import json

import pytest
from pydantic import ValidationError

from codex_room.agent import AgentTurnTerminalError
from codex_room.db import Database
from codex_room.models import (
    CreateRoomRequest,
    HistoryRequest,
    ObserverMessageRequest,
    PrepareRoundRequest,
    RoomStatus,
    SourceEvidenceRequest,
    TransactionAction,
    TransactionDecision,
    TRANSACTION_DECISION_SCHEMA,
)
from codex_room.orchestrator import RoomRuntime

from .fakes import FakeAgentAdapter, wait_until


@pytest.fixture
async def context_runtime_factory(tmp_path):
    runtimes: list[RoomRuntime] = []

    async def make(adapter: FakeAgentAdapter, name: str = "assignment-context.db") -> RoomRuntime:
        runtime = RoomRuntime(Database(tmp_path / name), adapter, tmp_path / "data")
        await runtime.initialize()
        runtimes.append(runtime)
        return runtime

    yield make
    await asyncio.gather(*(runtime.close() for runtime in runtimes), return_exceptions=True)


async def _finished(runtime: RoomRuntime, room_id: str) -> bool:
    room = await runtime.db.get_room(room_id)
    return bool(room and room["status"] == RoomStatus.FINISHED)


def _usage_wall(when: str) -> AgentTurnTerminalError:
    return AgentTurnTerminalError(
        f"You've hit your usage limit. Please try again at {when}.",
        codex_error_info="usageLimitExceeded",
    )


class RefreshStartFailureAdapter(FakeAgentAdapter):
    async def start_context_thread(self, agent, cwd, *, label: str) -> str:
        if label.startswith("coordinator refresh "):
            raise RuntimeError("simulated coordinator refresh start failure")
        return await super().start_context_thread(agent, cwd, label=label)


class RefreshDuplicateThreadAdapter(FakeAgentAdapter):
    async def start_context_thread(self, agent, cwd, *, label: str) -> str:
        if label.startswith("coordinator refresh "):
            return self.context_starts[0][1]
        return await super().start_context_thread(agent, cwd, label=label)


class RefreshArchiveOnceFailureAdapter(FakeAgentAdapter):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._refresh_archive_failed = False

    async def archive_thread(self, thread_id: str) -> None:
        if not self._refresh_archive_failed:
            self._refresh_archive_failed = True
            raise RuntimeError("simulated old coordinator archive failure")
        await super().archive_thread(thread_id)


def test_transaction_provider_schema_omits_unsupported_unique_items() -> None:
    assert "uniqueItems" not in json.dumps(TRANSACTION_DECISION_SCHEMA)


def test_bctx4_refresh_decision_requires_bounded_checkpoint() -> None:
    with pytest.raises(
        ValidationError,
        match="REFRESH requires a non-empty coordinator checkpoint",
    ):
        TransactionDecision(action=TransactionAction.REFRESH)

    with pytest.raises(ValidationError, match="checkpoint is valid only for REFRESH"):
        TransactionDecision(
            action=TransactionAction.PASS,
            checkpoint="This checkpoint is invalid for PASS.",
        )

    with pytest.raises(ValidationError):
        TransactionDecision(
            action=TransactionAction.REFRESH,
            checkpoint="x" * 12_001,
        )


def test_delegation_context_policy_rejects_fresh_plus_explicit_lineage() -> None:
    with pytest.raises(
        ValidationError,
        match="fresh_context cannot be combined with context_from_assignment_id",
    ):
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "Invalid mixed context policy.",
                    "config": None,
                    "context_from_assignment_id": "assignment_prior",
                    "fresh_context": True,
                }
            ],
        )


def test_assignment_context_mode_requires_transaction_work_model() -> None:
    with pytest.raises(ValidationError, match="requires work_model_version=2"):
        CreateRoomRequest(
            topic="invalid",
            provider_context_mode="assignment_thread",
        )
    with pytest.raises(ValidationError, match="requires work_model_version=2"):
        PrepareRoundRequest(
            prompt="invalid",
            provider_context_mode="assignment_thread",
        )


def test_bctx2_transaction_decision_rejects_ambiguous_direct_return() -> None:
    with pytest.raises(
        ValidationError,
        match="coordinator delegation return requires exactly one child assignment",
    ):
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegation_return_mode="coordinator",
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "A",
                    "config": None,
                },
                {
                    "target": "agent_b",
                    "instruction": "B",
                    "config": None,
                },
            ],
        )

    with pytest.raises(
        ValidationError,
        match="delegation_return_mode is valid only for DELEGATE",
    ):
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="invalid routing metadata",
            delegation_return_mode="coordinator",
        )


@pytest.mark.asyncio
async def test_assignment_context_mode_reuses_one_thread_per_logical_assignment(
    context_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Return one bounded peer result.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated the peer result.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Bounded peer result.",
        )
    )

    runtime = await context_runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise assignment-scoped provider context.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    permanent_threads = {
        item["agent_key"]: item["thread_id"] for item in snapshot["agents"]
    }
    await wait_until(lambda: _finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    assert len(adapter.calls["agent_a"]) == 1
    c_thread = adapter.calls["agent_c"][0]["thread_id"]
    a_thread = adapter.calls["agent_a"][0]["thread_id"]
    assert adapter.calls["agent_c"][1]["thread_id"] == c_thread
    assert c_thread != a_thread
    assert c_thread != permanent_threads["agent_c"]
    assert a_thread != permanent_threads["agent_a"]
    assert (
        "bounded to the current declared Assignment context lineage"
        in adapter.calls["agent_c"][0]["prompt"]
    )
    assert (
        "CORE normally continues the latest completed same-worker provider context"
        in adapter.calls["agent_c"][0]["prompt"]
    )
    assert "Bounded peer result." in adapter.calls["agent_c"][1]["prompt"]

    exported = await runtime.db.snapshot(room_id, event_limit=None)
    assert exported is not None
    active_round = exported["active_round"]
    assert active_round["provider_context_mode"] == "assignment_thread"
    assignments = active_round["transaction_state"]["tasks"][0]["assignments"]
    context_by_agent = {
        item["agent_key"]: item["context_thread_id"] for item in assignments
    }
    assert context_by_agent["agent_c"] == c_thread
    assert context_by_agent["agent_a"] == a_thread


@pytest.mark.asyncio
async def test_assignment_context_mode_gives_same_agent_new_thread_for_new_assignment(
    context_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="First assignment complete.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Second assignment complete.",
            ),
        ]
    )
    runtime = await context_runtime_factory(adapter, "same-agent-distinct.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="First independent assignment.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _finished(runtime, room_id))
    first_thread = adapter.calls["agent_c"][0]["thread_id"]

    await runtime.observer_message(
        room_id,
        ObserverMessageRequest(
            target="agent_c",
            content="Second independent assignment.",
        ),
    )
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 2)
    await wait_until(lambda: _finished(runtime, room_id))
    second_thread = adapter.calls["agent_c"][1]["thread_id"]

    assert first_thread != second_thread
    assert len([item for item in adapter.context_starts if item[0] == "agent_c"]) == 2
    async with runtime.db.connect() as db:
        rows = await db.execute_fetchall(
            """SELECT x.context_thread_id FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_c'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )
    assert [row["context_thread_id"] for row in rows] == [
        first_thread,
        second_thread,
    ]


@pytest.mark.asyncio
async def test_assignment_context_mode_keeps_evidence_resume_on_same_thread(
    context_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.EVIDENCE,
                evidence_requests=[
                    SourceEvidenceRequest(
                        operation="READ",
                        source="workspace",
                        path="fact.txt",
                        max_lines=20,
                        max_bytes=4096,
                    )
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Evidence integrated.",
            ),
        ]
    )
    runtime = await context_runtime_factory(adapter, "assignment-evidence.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Read one fact and integrate it.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    (runtime.workspace(room_id) / "fact.txt").write_text(
        "assignment evidence survives the resume\n",
        encoding="utf-8",
    )
    await runtime.start_round(room_id, snapshot["active_round_id"])
    await wait_until(lambda: _finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    assert adapter.calls["agent_c"][0]["thread_id"] == adapter.calls["agent_c"][1]["thread_id"]
    assert len([item for item in adapter.context_starts if item[0] == "agent_c"]) == 1
    assert "assignment evidence survives the resume" in adapter.calls["agent_c"][1]["prompt"]
    assert "<deterministic_evidence>" in adapter.calls["agent_c"][0]["prompt"]
    assert "<room_history>" in adapter.calls["agent_c"][0]["prompt"]
    assert "<deterministic_capabilities>" in adapter.calls["agent_c"][0]["prompt"]
    assert "<transaction_continuation_delta>" in adapter.calls["agent_c"][1]["prompt"]
    assert "<deterministic_evidence>" not in adapter.calls["agent_c"][1]["prompt"]
    assert "<room_history>" not in adapter.calls["agent_c"][1]["prompt"]
    assert "<deterministic_capabilities>" not in adapter.calls["agent_c"][1]["prompt"]


@pytest.mark.asyncio
async def test_assignment_context_usage_wall_restart_reuses_exact_assignment_thread(
    context_runtime_factory,
):
    first_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        failures={"agent_c": [_usage_wall("Jan 1, 2020 1:00 AM")]},
    )
    first = await context_runtime_factory(first_adapter, "assignment-usage.db")
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Resume bounded context after provider usage reset.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    permanent_c = next(
        item["thread_id"] for item in snapshot["agents"] if item["agent_key"] == "agent_c"
    )

    async def suspended() -> bool:
        item = await first.db.get_usage_continuation(room_id, "agent_c")
        return bool(item and item["state"] == "scheduled")

    await wait_until(suspended)
    continuation = await first.db.get_usage_continuation(room_id, "agent_c")
    assert continuation is not None
    assignment_id = continuation["assignment_id"]
    context_thread = first_adapter.calls["agent_c"][0]["thread_id"]
    assert context_thread != permanent_c
    assert continuation["thread_id"] == context_thread
    await first.close()

    second_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        turn_id_namespace="after_restart",
    )
    second_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Completed after reset.",
        )
    )
    second = await context_runtime_factory(second_adapter, "assignment-usage.db")
    await second._watchdog_tick()
    await wait_until(lambda: _finished(second, room_id))

    assert len(second_adapter.calls["agent_c"]) == 1
    continued = second_adapter.calls["agent_c"][0]
    assert continued["thread_id"] == context_thread
    assert second_adapter.context_starts == []
    assert second_adapter.usage_continuation_prepares == [
        {
            "agent_key": "agent_c",
            "thread_id": context_thread,
            "cwd": continued["cwd"],
        }
    ]
    completed = await second.db.get_usage_continuation(room_id, "agent_c")
    assert completed is not None
    assert completed["state"] == "completed"
    assert completed["assignment_id"] == assignment_id


@pytest.mark.asyncio
async def test_assignment_context_exact_active_turn_recovers_by_recorded_thread(
    context_runtime_factory,
):
    first_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {1}},
    )
    first = await context_runtime_factory(first_adapter, "assignment-active.db")
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Recover exact bounded provider turn.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(first_adapter.calls["agent_c"]) == 1)

    async def active() -> bool:
        async with first.db.connect() as db:
            row = await first.db._fetchone(
                db,
                """SELECT state FROM agent_executions
                   WHERE room_id=? AND assignment_id IS NOT NULL
                   ORDER BY created_at DESC LIMIT 1""",
                (room_id,),
            )
        return bool(row and row["state"] == "active")

    await wait_until(active)
    async with first.db.connect() as db:
        original = await first.db._fetchone(
            db,
            """SELECT * FROM agent_executions
               WHERE room_id=? AND assignment_id IS NOT NULL
               ORDER BY created_at DESC LIMIT 1""",
            (room_id,),
        )
        assignment = await first.db._fetchone(
            db,
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               WHERE t.room_id=? ORDER BY x.created_at LIMIT 1""",
            (room_id,),
        )
    assert original is not None
    assert assignment is not None
    assert assignment["context_thread_id"] == original["sdk_thread_id"]
    context_thread = original["sdk_thread_id"]
    turn_id = original["sdk_turn_id"]
    await first.close()

    second_adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    second_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Recovered exact bounded turn.",
        )
    )
    second = await context_runtime_factory(second_adapter, "assignment-active.db")
    await wait_until(lambda: _finished(second, room_id))

    assert len(second_adapter.calls["agent_c"]) == 1
    recovered = second_adapter.calls["agent_c"][0]
    assert recovered["recovered"] is True
    assert recovered["thread_id"] == context_thread
    assert recovered["turn_id"] == turn_id
    assert second_adapter.context_starts == []


@pytest.mark.asyncio
async def test_same_task_worker_context_continues_implicitly(
    context_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {2}},
    )
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "Perform the first pass.",
                    "config": None,
                }
            ],
        )
    )
    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="IMPLICIT-CONTEXT-ALPHA",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Implicit continuation succeeded.",
            ),
        ]
    )

    runtime = await context_runtime_factory(adapter, "implicit-worker-context.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Keep same-worker context across causally continuous same-Task work.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    await wait_until(
        lambda: len(adapter.completed_calls["agent_a"]) == 1
        and len(adapter.calls["agent_c"]) == 2
    )

    async with runtime.db.connect() as db:
        first_a = await runtime.db._fetchone(
            db,
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id LIMIT 1""",
            (room_id,),
        )
    assert first_a is not None
    first_thread = first_a["context_thread_id"]
    assert first_thread

    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Continue the same Task without naming a context source.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated the implicit continuation.",
            ),
        ]
    )
    adapter.release_call("agent_c", 2)
    await wait_until(lambda: _finished(runtime, room_id))

    assert len(adapter.calls["agent_a"]) == 2
    assert adapter.calls["agent_a"][0]["thread_id"] == first_thread
    assert adapter.calls["agent_a"][1]["thread_id"] == first_thread
    assert len([item for item in adapter.context_starts if item[0] == "agent_a"]) == 1

    async with runtime.db.connect() as db:
        rows = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )
    assert len(rows) == 2
    assert rows[1]["context_parent_assignment_id"] == rows[0]["id"]
    assert rows[1]["context_thread_id"] == rows[0]["context_thread_id"]


@pytest.mark.asyncio
async def test_same_task_worker_can_request_fresh_context_explicitly(
    context_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {2}},
    )
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "Perform the first pass.",
                    "config": None,
                }
            ],
        )
    )
    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="FRESH-CONTEXT-PREVIOUS-PUBLIC-RESULT",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Fresh-context independent pass complete.",
            ),
        ]
    )

    runtime = await context_runtime_factory(adapter, "fresh-worker-context.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Allow an explicit same-Task provider-context reset.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    await wait_until(
        lambda: len(adapter.completed_calls["agent_a"]) == 1
        and len(adapter.calls["agent_c"]) == 2
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Reassess independently on a fresh provider context.",
                        "config": None,
                        "fresh_context": True,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated the fresh independent pass.",
            ),
        ]
    )
    adapter.release_call("agent_c", 2)
    await wait_until(lambda: _finished(runtime, room_id))

    assert len(adapter.calls["agent_a"]) == 2
    assert adapter.calls["agent_a"][0]["thread_id"] != adapter.calls["agent_a"][1]["thread_id"]
    assert len([item for item in adapter.context_starts if item[0] == "agent_a"]) == 2
    assert "FRESH-CONTEXT-PREVIOUS-PUBLIC-RESULT" in adapter.calls["agent_a"][1]["prompt"]

    async with runtime.db.connect() as db:
        rows = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )
    assert rows[1]["context_parent_assignment_id"] is None


@pytest.mark.asyncio
async def test_worker_receives_missed_public_room_delta_and_same_task_history(
    context_runtime_factory,
):
    marker = "PUBLIC-DEBATE-MARKER-731"
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Publish the first participant statement.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_b",
                        "instruction": "Respond to the participant statement already public in the Room.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated both participants.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message=marker,
        )
    )
    adapter.decisions["agent_b"].extend(
        [
            TransactionDecision(
                action=TransactionAction.HISTORY,
                history_requests=[
                    HistoryRequest(
                        operation="SEARCH",
                        query=marker,
                        agent="agent_a",
                        max_results=1,
                    )
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="B received public context and exact same-Task history.",
            ),
        ]
    )

    runtime = await context_runtime_factory(adapter, "public-room-delta.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise shared public conversation continuity.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _finished(runtime, room_id))

    assert len(adapter.calls["agent_b"]) == 2
    first_b_prompt = adapter.calls["agent_b"][0]["prompt"]
    second_b_prompt = adapter.calls["agent_b"][1]["prompt"]
    assert "<public_room_delta>" in first_b_prompt
    assert marker in first_b_prompt
    assert "<retrieved_room_history>" in second_b_prompt
    assert marker in second_b_prompt
    assert "<public_room_delta>" not in second_b_prompt

    events = await runtime.db.get_events(room_id)
    history = [
        event
        for event in events
        if event["event_type"] == "tool_activity"
        and event.get("metadata", {}).get("type") == "deterministic_room_history"
    ]
    assert len(history) == 1
    assert len(history[0]["metadata"]["selected_event_ids"]) == 1


@pytest.mark.asyncio
async def test_same_task_worker_delta_tracks_actual_provider_visibility(
    context_runtime_factory,
):
    marker = "PUBLIC-INFLIGHT-PEER-MARKER-914"
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_a": {1}},
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Begin the first A pass and stay in flight long enough for B to finish.",
                        "config": None,
                    },
                    {
                        "target": "agent_b",
                        "instruction": "Publish the peer fact while A is already running.",
                        "config": None,
                    },
                ],
            ),
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Continue A on the same Task and incorporate all unseen public peer input.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated the visibility-race regression.",
            ),
        ]
    )
    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A first pass completed after B had already published.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A second pass consumed the unseen peer result.",
            ),
        ]
    )
    adapter.decisions["agent_b"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message=marker,
        )
    )

    runtime = await context_runtime_factory(adapter, "provider-visibility-race.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Reproduce the concurrent public-delta visibility race.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    async def peer_marker_event():
        events = await runtime.db.get_events(room_id)
        return next((event for event in events if event["content"] == marker), None)

    await wait_until(peer_marker_event)
    peer_event = await peer_marker_event()
    assert peer_event is not None
    assert len(adapter.calls["agent_a"]) == 1
    assert len(adapter.completed_calls["agent_a"]) == 0

    async with runtime.db.connect() as db:
        first_execution = await runtime.db._fetchone(
            db,
            """SELECT e.public_context_through_sequence
               FROM agent_executions e
               JOIN agents a ON a.id=e.agent_id
               WHERE e.room_id=? AND a.agent_key='agent_a'
               ORDER BY e.created_at, e.batch_id
               LIMIT 1""",
            (room_id,),
        )
    assert first_execution is not None
    assert first_execution["public_context_through_sequence"] is not None
    assert int(first_execution["public_context_through_sequence"]) < int(
        peer_event["sequence_no"]
    )

    adapter.release_call("agent_a", 1)
    await wait_until(lambda: _finished(runtime, room_id))

    assert len(adapter.calls["agent_a"]) == 2
    assert (
        adapter.calls["agent_a"][0]["thread_id"]
        == adapter.calls["agent_a"][1]["thread_id"]
    )
    second_a_prompt = adapter.calls["agent_a"][1]["prompt"]
    assert "<public_room_delta>" in second_a_prompt
    assert marker in second_a_prompt

    async with runtime.db.connect() as db:
        executions = await db.execute_fetchall(
            """SELECT e.public_context_through_sequence
               FROM agent_executions e
               JOIN agents a ON a.id=e.agent_id
               WHERE e.room_id=? AND a.agent_key='agent_a'
               ORDER BY e.created_at, e.batch_id""",
            (room_id,),
        )
    assert len(executions) == 2
    assert executions[1]["public_context_through_sequence"] is not None
    assert int(executions[1]["public_context_through_sequence"]) >= int(
        peer_event["sequence_no"]
    )


@pytest.mark.asyncio
async def test_worker_public_delta_drains_oldest_first_without_skipping_event_cap(
    context_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {2}},
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Establish the A provider context.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Consume the first bounded public backlog prefix.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Consume the remaining public backlog.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Backlog drain complete.",
            ),
        ]
    )
    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A context established.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="First backlog prefix consumed.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Remaining backlog consumed.",
            ),
        ]
    )

    runtime = await context_runtime_factory(adapter, "provider-visibility-backlog.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Drain a bounded public-context backlog without gaps.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    round_id = snapshot["active_round_id"]

    await wait_until(
        lambda: len(adapter.completed_calls["agent_a"]) == 1
        and len(adapter.calls["agent_c"]) >= 2
    )

    markers = [f"PUBLIC-BACKLOG-{index:02d}" for index in range(60)]
    for marker in markers:
        await runtime.db.create_event(
            room_id,
            "agent_message",
            "agent_b",
            "all",
            marker,
            discussion_id=round_id,
            round_id=round_id,
            conversational=True,
            counts_as_turn=False,
            visibility="public",
            agent_readable=True,
            turn_triggering=False,
        )

    adapter.release_call("agent_c", 2)
    await wait_until(lambda: _finished(runtime, room_id))

    assert len(adapter.calls["agent_a"]) == 3
    first_backlog_prompt = adapter.calls["agent_a"][1]["prompt"]
    second_backlog_prompt = adapter.calls["agent_a"][2]["prompt"]
    first_seen = {marker for marker in markers if marker in first_backlog_prompt}
    second_seen = {marker for marker in markers if marker in second_backlog_prompt}

    assert markers[0] in first_seen
    assert markers[-1] not in first_seen
    assert markers[-1] in second_seen
    assert first_seen.isdisjoint(second_seen)
    assert first_seen | second_seen == set(markers)
    assert (
        "Additional newer public Room messages remain queued for a later worker Assignment"
        in first_backlog_prompt
    )


@pytest.mark.asyncio
async def test_explicit_worker_context_lineage_recovers_exact_active_turn_after_restart(
    context_runtime_factory,
):
    first_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {2}, "agent_a": {2}},
    )
    first_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "Complete worker pass one.",
                    "config": None,
                }
            ],
        )
    )
    first_adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Worker pass one complete.",
        )
    )

    first = await context_runtime_factory(first_adapter, "worker-lineage-restart.db")
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Recover explicit worker context lineage.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    await wait_until(
        lambda: len(first_adapter.completed_calls["agent_a"]) == 1
        and len(first_adapter.calls["agent_c"]) == 2
    )
    async with first.db.connect() as db:
        first_a = await first.db._fetchone(
            db,
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id LIMIT 1""",
            (room_id,),
        )
    assert first_a is not None
    first_a_id = first_a["id"]
    worker_thread = first_a["context_thread_id"]
    assert worker_thread

    first_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "Continue worker pass one using the explicit prior context.",
                    "config": None,
                    "context_from_assignment_id": first_a_id,
                }
            ],
        )
    )
    first_adapter.release_call("agent_c", 2)
    await wait_until(lambda: len(first_adapter.calls["agent_a"]) == 2)

    async def second_a_active() -> bool:
        async with first.db.connect() as db:
            row = await first.db._fetchone(
                db,
                """SELECT x.id AS assignment_id, x.context_parent_assignment_id,
                          x.context_thread_id, e.state AS execution_state,
                          e.sdk_thread_id, e.sdk_turn_id
                   FROM assignments x
                   JOIN tasks t ON t.id=x.task_id
                   JOIN agents a ON a.id=x.agent_id
                   JOIN agent_executions e ON e.assignment_id=x.id
                   WHERE t.room_id=? AND a.agent_key='agent_a'
                     AND x.id<>?
                   ORDER BY e.created_at DESC LIMIT 1""",
                (room_id, first_a_id),
            )
        return bool(
            row
            and row["execution_state"] == "active"
            and row["context_parent_assignment_id"] == first_a_id
            and row["context_thread_id"] == worker_thread
            and row["sdk_thread_id"] == worker_thread
            and row["sdk_turn_id"]
        )

    await wait_until(second_a_active)
    await first.close()

    second_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        turn_id_namespace="lineage_restart",
    )
    second_adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Recovered continued worker pass.",
        )
    )
    second_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Integrated recovered worker continuation.",
        )
    )
    second = await context_runtime_factory(second_adapter, "worker-lineage-restart.db")
    await wait_until(lambda: _finished(second, room_id))

    assert len(second_adapter.calls["agent_a"]) == 1
    recovered = second_adapter.calls["agent_a"][0]
    assert recovered["recovered"] is True
    assert recovered["thread_id"] == worker_thread
    assert second_adapter.context_starts == []

    async with second.db.connect() as db:
        a_rows = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )
    assert len(a_rows) == 2
    continued_rows = [row for row in a_rows if row["id"] != first_a_id]
    assert len(continued_rows) == 1
    continued = continued_rows[0]
    assert continued["context_parent_assignment_id"] == first_a_id
    assert continued["context_thread_id"] == worker_thread
    assert continued["state"] == "completed"


@pytest.mark.asyncio
async def test_persistent_provider_context_mode_remains_default(
    context_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Default mode complete.",
        )
    )
    runtime = await context_runtime_factory(adapter, "persistent-default.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Preserve default behavior.", work_model_version=2)
    )
    room_id = snapshot["id"]
    permanent_c = next(
        item["thread_id"] for item in snapshot["agents"] if item["agent_key"] == "agent_c"
    )
    await wait_until(lambda: _finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 1
    assert adapter.calls["agent_c"][0]["thread_id"] == permanent_c
    assert adapter.context_starts == []
    exported = await runtime.db.snapshot(room_id, event_limit=None)
    assert exported is not None
    assert exported["active_round"]["provider_context_mode"] == "persistent_agent_thread"

@pytest.mark.asyncio
async def test_bctx3_pending_worker_context_retirement_recovers_after_restart(
    context_runtime_factory,
):
    first_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {3}},
    )
    first_adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Produce one worker context to retire later.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task one complete.",
            ),
        ]
    )
    first_adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Worker context established.",
        )
    )

    first = await context_runtime_factory(first_adapter, "bctx3-retirement-restart.db")
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Exercise restart-safe worker context retirement.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=20,
        )
    )
    room_id = snapshot["id"]

    await wait_until(lambda: len(first_adapter.calls["agent_c"]) == 3)

    async with first.db.connect() as db:
        row = await first.db._fetchone(
            db,
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id LIMIT 1""",
            (room_id,),
        )
    assert row is not None
    assignment_id = row["id"]
    context_thread_id = row["context_thread_id"]
    assert context_thread_id
    assert row["context_grace_state"] == "eligible"

    # Simulate a process loss after retirement was committed durably but before
    # the provider archive call/acknowledgement completed.
    async with first.db.connect() as db:
        await db.execute(
            """UPDATE assignments
               SET context_grace_remaining=0, context_grace_state='retire_pending'
               WHERE id=?""",
            (assignment_id,),
        )
        await db.commit()
    await first.db.set_room_status(room_id, RoomStatus.PAUSED)
    await first.close()

    second_adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    second = await context_runtime_factory(
        second_adapter, "bctx3-retirement-restart.db"
    )

    assert context_thread_id in second_adapter.archived
    async with second.db.connect() as db:
        retired = await second.db._fetchone(
            db,
            "SELECT * FROM assignments WHERE id=?",
            (assignment_id,),
        )
    assert retired is not None
    assert retired["context_grace_state"] == "retired"
    assert retired["context_archived_at"] is not None


def test_bctx3_worker_context_retirement_signal_is_bounded() -> None:
    with pytest.raises(
        ValidationError,
        match="retire_worker_context_task_ids accepts at most 8 Task IDs",
    ):
        TransactionDecision(
            action=TransactionAction.PASS,
            retire_worker_context_task_ids=[
                f"task_{index}" for index in range(9)
            ],
        )
    with pytest.raises(
        ValidationError,
        match="retire_worker_context_task_ids cannot contain duplicates",
    ):
        TransactionDecision(
            action=TransactionAction.PASS,
            retire_worker_context_task_ids=["task_one", "task_one"],
        )


def test_history_request_validation_is_bounded() -> None:
    with pytest.raises(ValidationError, match="SEARCH history retrieval"):
        HistoryRequest(operation="SEARCH", query="")
    with pytest.raises(ValidationError, match="query is valid only"):
        HistoryRequest(operation="RECENT", query="not allowed")
    with pytest.raises(ValidationError, match="less than or equal to 10"):
        HistoryRequest(operation="RECENT", max_results=11)
    with pytest.raises(ValidationError, match="at most 4 Room-history requests"):
        TransactionDecision(
            action=TransactionAction.HISTORY,
            history_requests=[
                HistoryRequest(operation="RECENT", max_results=1)
                for _ in range(5)
            ],
        )


@pytest.mark.asyncio
async def test_assignment_context_history_recent_recovers_prior_round_result_without_thread_inheritance(
    context_runtime_factory,
):
    token = "ORBIT-7429-CEDAR"
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message=token,
            ),
            TransactionDecision(
                action=TransactionAction.HISTORY,
                history_requests=[
                    HistoryRequest(
                        operation="RECENT",
                        agent="agent_c",
                        max_results=1,
                    )
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message=token,
            ),
        ]
    )
    runtime = await context_runtime_factory(adapter, "assignment-history-recent.db")
    first = await runtime.create_room(
        CreateRoomRequest(
            topic="Establish one continuity token.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            required_contributors=["agent_c"],
        )
    )
    room_id = first["id"]
    await wait_until(lambda: _finished(runtime, room_id))

    first_snapshot = await runtime.db.snapshot(room_id, event_limit=None)
    assert first_snapshot is not None
    first_round = first_snapshot["active_round"]
    first_assignment = first_round["transaction_state"]["tasks"][0]["assignments"][0]
    first_result_event_id = first_assignment["result_event_id"]

    prepared = await runtime.prepare_round(
        room_id,
        PrepareRoundRequest(
            title="Recall continuity token",
            prompt=(
                "Report the continuity token from the immediately preceding Round. "
                "Do not guess."
            ),
            starting_agent="agent_c",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            required_contributors=["agent_c"],
        ),
    )
    await runtime.start_round(room_id, prepared["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 3)
    await wait_until(lambda: _finished(runtime, room_id))

    establishment_thread = adapter.calls["agent_c"][0]["thread_id"]
    recall_thread = adapter.calls["agent_c"][1]["thread_id"]
    assert establishment_thread != recall_thread
    assert adapter.calls["agent_c"][2]["thread_id"] == recall_thread
    assert token not in adapter.calls["agent_c"][1]["prompt"]
    assert "<retrieved_room_history>" in adapter.calls["agent_c"][2]["prompt"]
    assert token in adapter.calls["agent_c"][2]["prompt"]

    exported = await runtime.db.snapshot(room_id, event_limit=None)
    assert exported is not None
    active_round = exported["active_round"]
    assignment = active_round["transaction_state"]["tasks"][0]["assignments"][0]
    assert assignment["context_event_ids"] == [first_result_event_id]
    history_events = [
        event
        for event in active_round["events"]
        if event["event_type"] == "tool_activity"
        and event.get("metadata", {}).get("type") == "deterministic_room_history"
    ]
    assert len(history_events) == 1
    assert history_events[0]["metadata"]["selected_event_ids"] == [first_result_event_id]


def test_bctx4_coordinator_context_economics_uses_cumulative_spend_for_refresh_pressure() -> None:
    economics = RoomRuntime._coordinator_context_economics(
        [
            {"task_id": "task_one", "task_state": "active", "usage": {"input_tokens": 22_066}},
            {"task_id": "task_one", "task_state": "active", "usage": {"input_tokens": 47_232}},
            {"task_id": "task_one", "task_state": "active", "usage": {"input_tokens": 82_469}},
            {"task_id": "task_one", "task_state": "active", "usage": {"input_tokens": 123_928}},
        ]
    )

    assert economics["last_execution_input_tokens"] == 41_459
    assert economics["cumulative_input_tokens"] == 123_928
    assert economics["refresh_pressure_input_tokens"] == 123_928
    assert economics["refresh_pressure_basis"] == "cumulative_provider_input"
    assert economics["guidance_level"] == "strongly_prefer"


def test_bctx4_coordinator_context_economics_advisory_levels() -> None:
    consider = RoomRuntime._coordinator_context_economics(
        [
            {
                "task_id": "task_one",
                "task_state": "settled",
                "usage": {
                    "input_tokens": 20_000,
                    "cached_input_tokens": 0,
                    "total_tokens": 20_100,
                },
            },
            {
                "task_id": "task_two",
                "task_state": "active",
                "usage": {
                    "input_tokens": 90_000,
                    "cached_input_tokens": 50_000,
                    "total_tokens": 90_200,
                },
            },
        ]
    )
    assert consider["baseline_input_tokens"] == 20_000
    assert consider["last_execution_input_tokens"] == 70_000
    assert consider["input_growth_from_baseline"] == 50_000
    assert consider["refresh_pressure_input_tokens"] == 90_000
    assert consider["refresh_pressure_basis"] == "cumulative_provider_input"
    assert consider["guidance_level"] == "consider"
    assert consider["settled_tasks_on_context"] == 1

    strongly_prefer = RoomRuntime._coordinator_context_economics(
        [
            {
                "task_id": "task_one",
                "task_state": "settled",
                "usage": {"input_tokens": 20_000, "total_tokens": 20_100},
            },
            {
                "task_id": "task_two",
                "task_state": "settled",
                "usage": {"input_tokens": 120_000, "total_tokens": 120_200},
            },
        ]
    )
    assert strongly_prefer["last_execution_input_tokens"] == 100_000
    assert strongly_prefer["refresh_pressure_input_tokens"] == 120_000
    assert strongly_prefer["refresh_pressure_basis"] == "cumulative_provider_input"
    assert strongly_prefer["guidance_level"] == "strongly_prefer"
    assert strongly_prefer["settled_tasks_on_context"] == 2


@pytest.mark.asyncio
async def test_bctx4_coordinator_context_economics_warns_and_resets_after_refresh(
    context_runtime_factory,
):
    checkpoint = (
        "Two bounded activities are complete. Continue the standing objective from a fresh "
        "coordinator context and choose the next useful activity from current deterministic state."
    )
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        usages={
            "agent_c": [
                {
                    "input_tokens": 20_000,
                    "cached_input_tokens": 0,
                    "total_tokens": 20_100,
                },
                {
                    "input_tokens": 120_000,
                    "cached_input_tokens": 60_000,
                    "total_tokens": 120_200,
                },
                {
                    "input_tokens": 150_000,
                    "cached_input_tokens": 80_000,
                    "total_tokens": 150_300,
                },
                {
                    "input_tokens": 18_000,
                    "cached_input_tokens": 0,
                    "total_tokens": 18_100,
                },
            ]
        },
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task one completed.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task two completed.",
            ),
            TransactionDecision(
                action=TransactionAction.REFRESH,
                checkpoint=checkpoint,
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Fresh coordinator context resumed correctly.",
            ),
        ]
    )

    runtime = await context_runtime_factory(adapter, "bctx4-refresh-economics.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise coordinator refresh economics.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=4,
        )
    )
    room_id = snapshot["id"]

    async def stopped() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)

    assert len(adapter.calls["agent_c"]) == 4
    first_prompt, second_prompt, third_prompt, refreshed_prompt = [
        call["prompt"] for call in adapter.calls["agent_c"]
    ]

    assert "<coordinator_context_economics>" in first_prompt
    assert "refresh_guidance_level: baseline_pending" in first_prompt
    assert "last_completed_execution_input_tokens: unavailable" in first_prompt

    assert "baseline_first_execution_input_tokens: 20000" in second_prompt
    assert "last_completed_execution_input_tokens: 20000" in second_prompt
    assert "refresh_guidance_level: normal" in second_prompt
    assert 'executions="1"' in second_prompt
    assert 'settled_tasks="1"' in second_prompt

    assert "baseline_first_execution_input_tokens: 20000" in third_prompt
    assert "last_completed_execution_input_tokens: 100000" in third_prompt
    assert "input_growth_from_baseline: 80000" in third_prompt
    assert "refresh_pressure_input_tokens: 120000" in third_prompt
    assert "refresh_pressure_basis: cumulative_provider_input" in third_prompt
    assert "refresh_guidance_level: strongly_prefer" in third_prompt
    assert "advisory_consider_input_tokens: 64000" in third_prompt
    assert "advisory_strongly_prefer_input_tokens: 96000" in third_prompt
    assert "CORE never auto-refreshes" in third_prompt
    assert 'executions="2"' in third_prompt
    assert 'settled_tasks="2"' in third_prompt

    old_thread = adapter.calls["agent_c"][2]["thread_id"]
    fresh_thread = adapter.calls["agent_c"][3]["thread_id"]
    assert fresh_thread != old_thread
    assert "<coordinator_continuity_checkpoint " in refreshed_prompt
    assert checkpoint in refreshed_prompt
    assert f'thread_id="{fresh_thread}"' in refreshed_prompt
    assert "refresh_guidance_level: baseline_pending" in refreshed_prompt
    assert "last_completed_execution_input_tokens: unavailable" in refreshed_prompt
    assert 'executions="0"' in refreshed_prompt


@pytest.mark.asyncio
async def test_bctx4_refresh_hands_off_checkpoint_once_and_preserves_successor_task_continuity(
    context_runtime_factory,
):
    checkpoint = (
        "Keep the standing objective active. The unresolved judgment is whether the next "
        "bounded activity should deepen the current line or open a new causally linked task."
    )
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.REFRESH,
                message="OLD_CONTEXT_ONLY_MARKER_SHOULD_NOT_REPLAY",
                checkpoint=checkpoint,
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task one completed after the fresh coordinator handoff.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task two completed at the configured hard boundary.",
            ),
        ]
    )

    runtime = await context_runtime_factory(adapter, "bctx4-refresh-success.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise deliberate coordinator context refresh.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=3,
        )
    )
    room_id = snapshot["id"]

    async def stopped() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)

    assert len(adapter.calls["agent_c"]) == 3
    old_thread = adapter.calls["agent_c"][0]["thread_id"]
    new_thread = adapter.calls["agent_c"][1]["thread_id"]
    assert old_thread != new_thread
    assert adapter.calls["agent_c"][2]["thread_id"] == new_thread
    assert len([item for item in adapter.context_starts if item[0] == "agent_c"]) == 2
    assert old_thread in adapter.archived
    assert new_thread not in adapter.archived

    refreshed_prompt = adapter.calls["agent_c"][1]["prompt"]
    assert "<coordinator_continuity_checkpoint " in refreshed_prompt
    assert checkpoint in refreshed_prompt
    assert "<task_coordination_status>" in refreshed_prompt
    assert "deterministic Room/Round/Task/Assignment/Join/Evidence/grace state" in refreshed_prompt
    assert "OLD_CONTEXT_ONLY_MARKER_SHOULD_NOT_REPLAY" not in refreshed_prompt

    successor_prompt = adapter.calls["agent_c"][2]["prompt"]
    assert "<coordinator_continuity_checkpoint " not in successor_prompt
    assert "<task_coordination_status>" in successor_prompt

    async with runtime.db.connect() as db:
        refresh_rows = await db.execute_fetchall(
            "SELECT * FROM coordinator_context_refreshes ORDER BY created_at, id"
        )
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id",
            (room_id,),
        )
        assignments = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? ORDER BY x.created_at, x.id""",
            (room_id,),
        )

    assert len(refresh_rows) == 1
    refresh = refresh_rows[0]
    assert refresh["state"] == "completed"
    assert refresh["checkpoint_text"] == checkpoint
    assert refresh["old_context_thread_id"] == old_thread
    assert refresh["new_context_thread_id"] == new_thread
    assert refresh["activated_at"] is not None
    assert refresh["completed_at"] is not None
    assert refresh["checkpoint_consumed_at"] is not None

    c_assignments = [row for row in assignments if row["agent_key"] == "agent_c"]
    assert len(tasks) == 2
    assert len(c_assignments) == 2
    assert c_assignments[0]["context_thread_id"] == new_thread
    assert c_assignments[1]["context_thread_id"] == new_thread

    events = await runtime.db.get_events(room_id)
    refreshed_events = [
        event
        for event in events
        if event["event_type"] == "coordinator_context_refreshed"
    ]
    assert len(refreshed_events) == 1
    assert refreshed_events[0]["metadata"]["old_context_thread_id"] == old_thread
    assert refreshed_events[0]["metadata"]["new_context_thread_id"] == new_thread

    exported = await runtime.db.snapshot(room_id, event_limit=None)
    assert exported is not None
    exported_assignments = [
        assignment
        for task in exported["rounds"][0]["transaction_state"]["tasks"]
        for assignment in task["assignments"]
        if assignment["agent_key"] == "agent_c"
    ]
    exported_refreshes = [
        item
        for assignment in exported_assignments
        for item in assignment["context_refreshes"]
    ]
    assert len(exported_refreshes) == 1
    assert exported_refreshes[0]["checkpoint_text"] == checkpoint
    assert exported_refreshes[0]["old_context_thread_id"] == old_thread
    assert exported_refreshes[0]["new_context_thread_id"] == new_thread


@pytest.mark.asyncio
async def test_bctx4_refresh_rejects_non_distinct_provider_context(
    context_runtime_factory,
):
    adapter = RefreshDuplicateThreadAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []}
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.REFRESH,
                checkpoint="The new C context must be distinct from this old context.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Stayed on the exact old context after duplicate refresh refusal.",
            ),
        ]
    )

    runtime = await context_runtime_factory(adapter, "bctx4-refresh-duplicate.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise distinct-thread enforcement during coordinator refresh.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    old_thread = adapter.calls["agent_c"][0]["thread_id"]
    assert adapter.calls["agent_c"][1]["thread_id"] == old_thread
    assert old_thread not in adapter.archived
    assert "did not return a distinct thread ID" in adapter.calls["agent_c"][1]["prompt"]

    async with runtime.db.connect() as db:
        row = await runtime.db._fetchone(
            db,
            """SELECT * FROM coordinator_context_refreshes
               ORDER BY created_at DESC, id DESC LIMIT 1""",
            (),
        )
    assert row is not None
    assert row["state"] == "failed"
    assert row["new_context_thread_id"] is None
    assert "did not return a distinct thread ID" in row["error"]


@pytest.mark.asyncio
async def test_bctx4_refresh_start_failure_falls_back_to_exact_old_context(
    context_runtime_factory,
):
    adapter = RefreshStartFailureAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []}
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.REFRESH,
                checkpoint="Preserve this bounded C checkpoint if refresh succeeds.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Continue safely on the old coordinator context after refresh failure.",
            ),
        ]
    )

    runtime = await context_runtime_factory(adapter, "bctx4-refresh-start-failure.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise pre-activation refresh failure.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    old_thread = adapter.calls["agent_c"][0]["thread_id"]
    assert adapter.calls["agent_c"][1]["thread_id"] == old_thread
    assert old_thread not in adapter.archived
    assert "Fresh coordinator context creation failed" in adapter.calls["agent_c"][1]["prompt"]

    async with runtime.db.connect() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM coordinator_context_refreshes ORDER BY created_at, id"
        )
    assert len(rows) == 1
    refresh = rows[0]
    assert refresh["state"] == "failed"
    assert refresh["old_context_thread_id"] == old_thread
    assert refresh["new_context_thread_id"] is None
    assert "simulated coordinator refresh start failure" in refresh["error"]

    events = await runtime.db.get_events(room_id)
    assert any(
        event["event_type"] == "coordinator_context_refresh_failed"
        for event in events
    )


@pytest.mark.asyncio
async def test_bctx4_archive_pending_refresh_recovers_after_restart_before_c_runs_new_context(
    context_runtime_factory,
):
    first_adapter = RefreshArchiveOnceFailureAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []}
    )
    first_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.REFRESH,
            checkpoint="Resume from this checkpoint only after the old C context is retired.",
        )
    )

    first = await context_runtime_factory(
        first_adapter, "bctx4-refresh-restart.db"
    )
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Exercise restart-safe fail-closed coordinator refresh.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    async def archive_pending() -> bool:
        async with first.db.connect() as db:
            row = await first.db._fetchone(
                db,
                """SELECT * FROM coordinator_context_refreshes
                   ORDER BY created_at DESC, id DESC LIMIT 1""",
                (),
            )
        return bool(row and row["state"] == "archive_pending")

    await wait_until(archive_pending)

    async with first.db.connect() as db:
        refresh = await first.db._fetchone(
            db,
            """SELECT * FROM coordinator_context_refreshes
               ORDER BY created_at DESC, id DESC LIMIT 1""",
            (),
        )
        assignment = await first.db._fetchone(
            db,
            "SELECT * FROM assignments WHERE id=?",
            (refresh["assignment_id"],),
        )

    assert refresh is not None
    assert assignment is not None
    old_thread = refresh["old_context_thread_id"]
    new_thread = refresh["new_context_thread_id"]
    assert new_thread
    assert old_thread != new_thread
    assert assignment["state"] == "refreshing"
    assert assignment["context_thread_id"] == new_thread
    assert len(first_adapter.calls["agent_c"]) == 1
    assert old_thread not in first_adapter.archived

    await first.close()

    second_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []}
    )
    second_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Recovered on the new C context after old-context archival.",
        )
    )
    second = await context_runtime_factory(
        second_adapter, "bctx4-refresh-restart.db"
    )

    await wait_until(lambda: _finished(second, room_id))

    assert old_thread in second_adapter.archived
    assert len(second_adapter.context_starts) == 0
    assert len(second_adapter.calls["agent_c"]) == 1
    assert second_adapter.calls["agent_c"][0]["thread_id"] == new_thread
    assert "<coordinator_continuity_checkpoint " in second_adapter.calls["agent_c"][0]["prompt"]
    assert (
        "Resume from this checkpoint only after the old C context is retired."
        in second_adapter.calls["agent_c"][0]["prompt"]
    )

    async with second.db.connect() as db:
        recovered_refresh = await second.db._fetchone(
            db,
            "SELECT * FROM coordinator_context_refreshes WHERE id=?",
            (refresh["id"],),
        )
        recovered_assignment = await second.db._fetchone(
            db,
            "SELECT * FROM assignments WHERE id=?",
            (refresh["assignment_id"],),
        )

    assert recovered_refresh is not None
    assert recovered_refresh["state"] == "completed"
    assert recovered_refresh["checkpoint_consumed_at"] is not None
    assert recovered_assignment is not None
    assert recovered_assignment["state"] == "completed"
    assert recovered_assignment["context_thread_id"] == new_thread


@pytest.mark.asyncio
async def test_bctx4_stop_cancels_archive_pending_refresh_without_running_new_context(
    context_runtime_factory,
):
    adapter = RefreshArchiveOnceFailureAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []}
    )
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.REFRESH,
            checkpoint="This checkpoint must not become runnable after human Stop.",
        )
    )

    runtime = await context_runtime_factory(adapter, "bctx4-refresh-stop.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise human Stop during a fail-closed coordinator refresh.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    async def archive_pending() -> bool:
        async with runtime.db.connect() as db:
            row = await runtime.db._fetchone(
                db,
                """SELECT * FROM coordinator_context_refreshes
                   ORDER BY created_at DESC, id DESC LIMIT 1""",
                (),
            )
        return bool(row and row["state"] == "archive_pending")

    await wait_until(archive_pending)
    assert len(adapter.calls["agent_c"]) == 1

    await runtime.stop(room_id, "Stop during pending coordinator refresh.")

    room = await runtime.db.get_room(room_id)
    assert room is not None
    assert room["status"] == RoomStatus.STOPPED

    async with runtime.db.connect() as db:
        refresh = await runtime.db._fetchone(
            db,
            """SELECT * FROM coordinator_context_refreshes
               ORDER BY created_at DESC, id DESC LIMIT 1""",
            (),
        )
        assignment = await runtime.db._fetchone(
            db,
            "SELECT * FROM assignments WHERE id=?",
            (refresh["assignment_id"],),
        )

    assert refresh is not None
    assert refresh["state"] == "cancelled"
    assert refresh["error"] == "room_lifecycle_change"
    assert assignment is not None
    assert assignment["state"] == "cancelled"
    assert len(adapter.calls["agent_c"]) == 1


@pytest.mark.asyncio
async def test_bctx3_history_recent_recovers_completed_prior_task_in_same_round(
    context_runtime_factory,
):
    token = "SAME-ROUND-6317"
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {2}},
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message=token,
            ),
            TransactionDecision(
                action=TransactionAction.HISTORY,
                history_requests=[
                    HistoryRequest(
                        operation="RECENT",
                        agent="agent_c",
                        max_results=1,
                    )
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Recovered the same-Round prior Task result.",
            ),
        ]
    )

    runtime = await context_runtime_factory(adapter, "bctx3-same-round-history.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Use bounded same-Round history across successor Tasks.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=3,
        )
    )
    room_id = snapshot["id"]

    await wait_until(lambda: len(adapter.calls["agent_c"]) == 2)
    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT rowid, id, created_at FROM tasks WHERE room_id=? ORDER BY rowid",
            (room_id,),
        )
        assert len(tasks) == 2
        await db.execute(
            "UPDATE tasks SET created_at=? WHERE id=?",
            (tasks[0]["created_at"], tasks[1]["id"]),
        )
        await db.commit()
        collided = await db.execute_fetchall(
            "SELECT rowid, id, created_at FROM tasks WHERE room_id=? ORDER BY rowid",
            (room_id,),
        )
    assert collided[0]["created_at"] == collided[1]["created_at"]
    adapter.release_call("agent_c", 2)

    async def stopped() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)

    assert len(adapter.calls["agent_c"]) == 3
    assert "<retrieved_room_history>" not in adapter.calls["agent_c"][1]["prompt"]
    assert "<retrieved_room_history>" in adapter.calls["agent_c"][2]["prompt"]
    assert token in adapter.calls["agent_c"][2]["prompt"]
    assert "an earlier completed Task in this Round" in adapter.calls["agent_c"][1]["prompt"]

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY rowid",
            (room_id,),
        )
        assignments = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? ORDER BY x.created_at, x.id""",
            (room_id,),
        )

    assert len(tasks) == 2
    assert all(row["state"] == "settled" for row in tasks)
    first_c = next(
        row
        for row in assignments
        if row["agent_key"] == "agent_c" and row["task_id"] == tasks[0]["id"]
    )
    second_c = next(
        row
        for row in assignments
        if row["agent_key"] == "agent_c" and row["task_id"] == tasks[1]["id"]
    )
    assert first_c["state"] == "completed"
    assert second_c["state"] == "completed"
    assert first_c["result_event_id"] in json.loads(
        second_c["context_event_ids_json"] or "[]"
    )

    events = await runtime.db.get_events(room_id)
    history_events = [
        event
        for event in events
        if event["event_type"] == "tool_activity"
        and event.get("metadata", {}).get("type") == "deterministic_room_history"
    ]
    assert len(history_events) == 1
    assert history_events[0]["metadata"]["selected_event_ids"] == [
        first_c["result_event_id"]
    ]


@pytest.mark.asyncio
async def test_assignment_context_history_search_matches_prior_round_prompt_and_returns_terminal_result(
    context_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {2}},
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Launch marker is ALPHA-903.",
            ),
            TransactionDecision(
                action=TransactionAction.HISTORY,
                history_requests=[
                    HistoryRequest(
                        operation="SEARCH",
                        query="Project Cedar",
                        agent="agent_c",
                        max_results=2,
                    )
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Recovered ALPHA-903.",
            ),
        ]
    )
    runtime = await context_runtime_factory(adapter, "assignment-history-search.db")
    first = await runtime.create_room(
        CreateRoomRequest(
            title="Project Cedar",
            topic="Retain the Project Cedar launch marker.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            required_contributors=["agent_c"],
        )
    )
    room_id = first["id"]
    await wait_until(lambda: _finished(runtime, room_id))

    prepared = await runtime.prepare_round(
        room_id,
        PrepareRoundRequest(
            title="Later unrelated round",
            prompt="Recover the relevant earlier launch marker.",
            starting_agent="agent_c",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            required_contributors=["agent_c"],
        ),
    )
    await runtime.start_round(room_id, prepared["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 2)
    async with runtime.db.connect() as db:
        rounds = await db.execute_fetchall(
            "SELECT rowid, id, created_at FROM rounds WHERE room_id=? ORDER BY rowid",
            (room_id,),
        )
        assert len(rounds) == 2
        await db.execute(
            "UPDATE rounds SET created_at=? WHERE id=?",
            (rounds[0]["created_at"], rounds[1]["id"]),
        )
        await db.commit()
        collided = await db.execute_fetchall(
            "SELECT rowid, id, created_at FROM rounds WHERE room_id=? ORDER BY rowid",
            (room_id,),
        )
    assert collided[0]["created_at"] == collided[1]["created_at"]
    adapter.release_call("agent_c", 2)
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 3)
    await wait_until(lambda: _finished(runtime, room_id))

    retrieved_prompt = adapter.calls["agent_c"][2]["prompt"]
    assert "<retrieved_room_history>" in retrieved_prompt
    assert "Launch marker is ALPHA-903." in retrieved_prompt

