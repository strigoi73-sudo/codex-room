from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from codex_room.agent import AgentTurnTerminalError
from codex_room.db import Database
from codex_room.models import (
    CreateRoomRequest,
    PrepareRoundRequest,
    RoomStatus,
    SourceEvidenceRequest,
    TransactionAction,
    TransactionDecision,
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
    assert "bounded to the current logical Assignment" in adapter.calls["agent_c"][0]["prompt"]
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
