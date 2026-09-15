from __future__ import annotations

import asyncio

import pytest

from codex_room.db import Database
from codex_room.models import (
    CreateRoomRequest,
    ObserverMessageRequest,
    RoomStatus,
    TransactionAction,
    TransactionDecision,
)
from codex_room.orchestrator import RoomRuntime

from .fakes import FakeAgentAdapter, wait_until


@pytest.fixture
async def transaction_runtime_factory(tmp_path):
    runtimes: list[RoomRuntime] = []

    async def make(adapter: FakeAgentAdapter, name: str = "transactions.db") -> RoomRuntime:
        runtime = RoomRuntime(Database(tmp_path / name), adapter, tmp_path / "data")
        await runtime.initialize()
        runtimes.append(runtime)
        return runtime

    yield make
    await asyncio.gather(*(runtime.close() for runtime in runtimes), return_exceptions=True)


async def _room_finished(runtime: RoomRuntime, room_id: str) -> bool:
    room = await runtime.db.get_room(room_id)
    return bool(room and room["status"] == RoomStatus.FINISHED)


@pytest.mark.asyncio
async def test_transaction_dual_delegation_releases_c_once_after_both_peers(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter()
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                message="A and B have distinct work.",
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Analyze the implementation path.",
                        "config": "luna-medium",
                    },
                    {
                        "target": "agent_b",
                        "instruction": "Audit failure modes independently.",
                        "config": "terra-medium",
                    },
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated A and B.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="A implementation result",
        )
    )
    adapter.decisions["agent_b"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="B failure-mode result",
        )
    )

    runtime = await transaction_runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Evaluate transaction coordination",
            work_model_version=2,
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    assert len(adapter.calls["agent_a"]) == 1
    assert len(adapter.calls["agent_b"]) == 1
    assert adapter.calls["agent_a"][0]["model"] == "gpt-5.6-luna"
    assert adapter.calls["agent_b"][0]["model"] == "gpt-5.6-terra"
    assert "A implementation result" in adapter.calls["agent_c"][1]["prompt"]
    assert "B failure-mode result" in adapter.calls["agent_c"][1]["prompt"]
    assert "<unread_room_events>" not in adapter.calls["agent_c"][1]["prompt"]

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=?", (room_id,)
        )
        joins = await db.execute_fetchall(
            """SELECT j.* FROM assignment_joins j
               JOIN tasks t ON t.id=j.task_id WHERE t.room_id=?""",
            (room_id,),
        )
        assignments = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? ORDER BY x.created_at, x.id""",
            (room_id,),
        )
        deliveries = await db.execute_fetchall(
            """SELECT d.* FROM deliveries d JOIN events e ON e.id=d.event_id
               WHERE e.room_id=? AND e.round_id=?""",
            (room_id, snapshot["active_round_id"]),
        )

    assert len(tasks) == 1
    assert tasks[0]["state"] == "settled"
    assert len(joins) == 1
    assert joins[0]["state"] == "released"
    assert {row["state"] for row in assignments} == {"completed"}
    assert sum(row["agent_key"] == "agent_c" for row in assignments) == 1
    assert deliveries == []


@pytest.mark.asyncio
async def test_transaction_nested_delegation_does_not_release_outer_join_early(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter()
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Own this analysis; ask B only if needed.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="C integrated A's final result.",
            ),
        ]
    )
    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_b",
                        "instruction": "Check one dependency for A.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A final after B",
            ),
        ]
    )
    adapter.decisions["agent_b"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="B dependency result",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "nested.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Nested delegation", work_model_version=2)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    assert len(adapter.calls["agent_a"]) == 2
    assert len(adapter.calls["agent_b"]) == 1
    assert "B dependency result" in adapter.calls["agent_a"][1]["prompt"]
    assert "A final after B" in adapter.calls["agent_c"][1]["prompt"]

    async with runtime.db.connect() as db:
        joins = await db.execute_fetchall(
            """SELECT j.* FROM assignment_joins j
               JOIN tasks t ON t.id=j.task_id WHERE t.room_id=?
               ORDER BY j.created_at""",
            (room_id,),
        )
    assert len(joins) == 2
    assert all(row["state"] == "released" for row in joins)


@pytest.mark.asyncio
async def test_transaction_observer_peer_message_creates_explicit_work_then_c_integration(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter()
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Initial task complete.",
        )
    )
    runtime = await transaction_runtime_factory(adapter, "observer.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Initial task", work_model_version=2)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="A answered observer follow-up.",
        )
    )
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="C integrated observer-directed A work.",
        )
    )

    await runtime.observer_message(
        room_id,
        ObserverMessageRequest(
            target="agent_a",
            content="Please have A examine this follow-up.",
        ),
    )
    await wait_until(
        lambda: len(adapter.completed_calls["agent_a"]) == 1
        and len(adapter.completed_calls["agent_c"]) == 2
    )
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert "Please have A examine this follow-up." in adapter.calls["agent_a"][0]["prompt"]
    assert "A answered observer follow-up." in adapter.calls["agent_c"][1]["prompt"]

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at", (room_id,)
        )
    assert len(tasks) == 2
    assert tasks[1]["parent_task_id"] == tasks[0]["id"]
    assert all(row["state"] == "settled" for row in tasks)
