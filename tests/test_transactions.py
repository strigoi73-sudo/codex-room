from __future__ import annotations

import asyncio

import pytest

from codex_room.agent import InterruptOutcome
from codex_room.agent import AgentTurnTerminalError
from codex_room.db import Database
from codex_room.exporter import as_markdown
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


def _transaction_usage_wall(when: str) -> AgentTurnTerminalError:
    return AgentTurnTerminalError(
        f"You've hit your usage limit. Please try again at {when}.",
        codex_error_info="usageLimitExceeded",
    )


@pytest.mark.asyncio
async def test_transaction_dual_delegation_releases_c_once_after_both_peers(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
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
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
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
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
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


@pytest.mark.asyncio
async def test_transaction_terminal_child_failure_releases_parent_with_degraded_status(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        failures={
            "agent_a": [
                RuntimeError("first child failure"),
                RuntimeError("terminal child failure"),
            ]
        },
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Attempt the delegated check.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="C handled the degraded child result.",
            ),
        ]
    )

    runtime = await transaction_runtime_factory(adapter, "child-failure.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Child failure release", work_model_version=2)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_a"]) == 2
    assert len(adapter.calls["agent_c"]) == 2
    assert "state=\"failed\"" in adapter.calls["agent_c"][1]["prompt"]
    assert "terminal child failure" in adapter.calls["agent_c"][1]["prompt"]

    async with runtime.db.connect() as db:
        joins = await db.execute_fetchall(
            """SELECT j.* FROM assignment_joins j
               JOIN tasks t ON t.id=j.task_id WHERE t.room_id=?""",
            (room_id,),
        )
        assignments = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=?""",
            (room_id,),
        )
    assert len(joins) == 1
    assert joins[0]["state"] == "released"
    assert next(
        row for row in assignments if row["agent_key"] == "agent_a"
    )["state"] == "failed"
    assert next(
        row for row in assignments if row["agent_key"] == "agent_c"
    )["state"] == "completed"


@pytest.mark.asyncio
async def test_transaction_stop_cancels_open_task_assignments_and_join(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_a": {1}},
        interrupt_outcomes={"agent_a": InterruptOutcome.INTERRUPTED},
    )
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "Remain in flight until the observer stops the Room.",
                    "config": None,
                }
            ],
        )
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="This result must not settle after Stop.",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "stop-cancel.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Stop transaction work", work_model_version=2)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)

    await runtime.stop(room_id, "transaction stop test")

    room = await runtime.db.get_room(room_id)
    assert room is not None
    assert room["status"] == RoomStatus.STOPPED
    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=?", (room_id,)
        )
        assignments = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id WHERE t.room_id=?""",
            (room_id,),
        )
        joins = await db.execute_fetchall(
            """SELECT j.* FROM assignment_joins j
               JOIN tasks t ON t.id=j.task_id WHERE t.room_id=?""",
            (room_id,),
        )
    assert tasks and all(row["state"] == "cancelled" for row in tasks)
    assert assignments and all(
        row["state"] in {"cancelled", "completed", "passed", "failed", "waived"}
        for row in assignments
    )
    assert joins and all(row["state"] == "cancelled" for row in joins)
    assert len(adapter.completed_calls["agent_a"]) == 0


@pytest.mark.asyncio
async def test_transaction_turn_limit_stops_before_released_parent_can_run_again(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "Use the final available peer turn.",
                    "config": None,
                }
            ],
        )
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="A consumed turn two.",
        )
    )
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="This third turn must never execute.",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "turn-limit.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Bound transaction turns",
            work_model_version=2,
            max_turns=2,
        )
    )
    room_id = snapshot["id"]

    async def stopped() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)

    assert len(adapter.calls["agent_c"]) == 1
    assert len(adapter.calls["agent_a"]) == 1
    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=?", (room_id,)
        )
        assignments = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=?""",
            (room_id,),
        )
    assert tasks and tasks[0]["state"] == "cancelled"
    c_assignment = next(row for row in assignments if row["agent_key"] == "agent_c")
    assert c_assignment["state"] == "cancelled"


@pytest.mark.asyncio
async def test_transaction_pause_resume_uses_explicit_task_state_not_deliveries(
    transaction_runtime_factory,
):
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
                        "instruction": "Complete after the Room is paused.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="C resumed from explicit transaction state.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="A completed while paused.",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "pause-resume.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Pause transaction work", work_model_version=2)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)

    await runtime.pause(room_id)
    adapter.release_call("agent_a", 1)
    await wait_until(lambda: len(adapter.completed_calls["agent_a"]) == 1)
    await asyncio.sleep(0.05)
    assert len(adapter.calls["agent_c"]) == 1

    await runtime.resume(room_id)
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    assert "A completed while paused." in adapter.calls["agent_c"][1]["prompt"]


@pytest.mark.asyncio
async def test_transaction_quiescent_reconciler_does_not_close_active_task_without_deliveries(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    runtime = await transaction_runtime_factory(adapter, "quiescence.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Explicit task is authoritative",
            work_model_version=2,
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    round_id = snapshot["active_round_id"]
    await runtime.db.start_round(room_id, round_id)
    origin = await runtime.db.create_event(
        room_id,
        "round_start_turn",
        "room",
        "agent_c",
        "Begin explicit transaction work.",
        round_id=round_id,
        discussion_id=round_id,
    )
    await runtime.db.create_transaction_task(
        room_id,
        round_id,
        origin["id"],
        "agent_c",
    )

    closed = await runtime._reconcile_quiescent_room(room_id, round_id)

    assert closed is False
    room = await runtime.db.get_room(room_id)
    assert room is not None
    assert room["status"] == RoomStatus.RUNNING
    assert await runtime.db.has_active_transaction_task(room_id, round_id)


@pytest.mark.asyncio
async def test_transaction_completion_while_paused_settles_task_then_resume_closes_round(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {1}},
    )
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="C completed while the Room was paused.",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "paused-complete.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Complete while paused", work_model_version=2)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 1)

    await runtime.pause(room_id)
    adapter.release_call("agent_c", 1)
    await wait_until(lambda: len(adapter.completed_calls["agent_c"]) == 1)

    async def task_settled() -> bool:
        async with runtime.db.connect() as db:
            row = await runtime.db._fetchone(
                db,
                "SELECT state FROM tasks WHERE room_id=? ORDER BY created_at DESC LIMIT 1",
                (room_id,),
            )
        return bool(row and row["state"] == "settled")

    await wait_until(task_settled)
    paused = await runtime.db.get_room(room_id)
    assert paused is not None
    assert paused["status"] == RoomStatus.PAUSED

    await runtime.resume(room_id)
    await wait_until(lambda: _room_finished(runtime, room_id))

@pytest.mark.asyncio
async def test_transaction_required_contributor_blocks_settlement_until_peer_contributes(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="I would otherwise finish without A.",
            ),
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Provide the explicitly required independent contribution.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated the required A contribution.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="A required contribution",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "required-contributor.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Require A before settlement",
            work_model_version=2,
            required_contributors=["agent_a"],
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 3
    assert len(adapter.calls["agent_a"]) == 1
    assert "explicitly requires contribution from: agent_a" in adapter.calls["agent_c"][1]["prompt"]
    assert "A required contribution" in adapter.calls["agent_c"][2]["prompt"]

    async with runtime.db.connect() as db:
        task = await runtime.db._fetchone(
            db,
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at LIMIT 1",
            (room_id,),
        )
    assert task is not None
    assert task["state"] == "settled"
    assert task["required_contributors_json"] == '["agent_a"]'

    exported = await runtime.db.snapshot(room_id, event_limit=None)
    assert exported is not None
    active_round = exported["active_round"]
    assert active_round["work_model_version"] == 2
    transaction = active_round["transaction_state"]
    assert transaction["tasks"][0]["required_contributors"] == ["agent_a"]
    assert any(
        item["agent_key"] == "agent_a"
        for item in transaction["tasks"][0]["assignments"]
    )
    markdown = as_markdown(exported)
    assert "### Transaction work state" in markdown
    assert "Required contributors: agent_a" in markdown

@pytest.mark.asyncio
async def test_transaction_usage_wall_continuation_survives_restart_on_same_assignment(
    transaction_runtime_factory,
):
    first_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        failures={"agent_c": [_transaction_usage_wall("Jan 1, 2020 1:00 AM")]},
    )
    first = await transaction_runtime_factory(first_adapter, "transaction-usage-restart.db")
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Resume explicit assignment after provider usage reset",
            work_model_version=2,
        )
    )
    room_id = snapshot["id"]

    async def suspended() -> bool:
        continuation = await first.db.get_usage_continuation(room_id, "agent_c")
        return bool(continuation and continuation["state"] == "scheduled")

    await wait_until(suspended)
    continuation = await first.db.get_usage_continuation(room_id, "agent_c")
    assert continuation is not None
    assert continuation["assignment_id"] is not None
    assignment_id = continuation["assignment_id"]
    thread_id = first_adapter.calls["agent_c"][0]["thread_id"]
    await first.close()

    second_adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    second_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Completed after the usage reset.",
        )
    )
    second = await transaction_runtime_factory(second_adapter, "transaction-usage-restart.db")
    await second._watchdog_tick()
    await wait_until(lambda: _room_finished(second, room_id))

    assert len(second_adapter.calls["agent_c"]) == 1
    continued = second_adapter.calls["agent_c"][0]
    assert continued["thread_id"] == thread_id
    assert RoomRuntime.USAGE_CONTINUATION_INSTRUCTION in continued["prompt"]
    assert second_adapter.usage_continuation_prepares == [
        {
            "agent_key": "agent_c",
            "thread_id": thread_id,
            "cwd": continued["cwd"],
        }
    ]
    completed = await second.db.get_usage_continuation(room_id, "agent_c")
    assert completed is not None
    assert completed["state"] == "completed"
    assert completed["assignment_id"] == assignment_id

    async with second.db.connect() as db:
        assignments = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               WHERE t.room_id=?""",
            (room_id,),
        )
        executions = await db.execute_fetchall(
            """SELECT * FROM agent_executions
               WHERE room_id=? AND assignment_id=?
               ORDER BY created_at""",
            (room_id, assignment_id),
        )
    assert len(assignments) == 1
    assert assignments[0]["state"] == "completed"
    assert len(executions) == 2
    assert all(row["assignment_id"] == assignment_id for row in executions)

@pytest.mark.asyncio
async def test_transaction_exact_active_turn_recovers_same_assignment_after_restart(
    transaction_runtime_factory,
):
    first_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {1}},
    )
    first = await transaction_runtime_factory(first_adapter, "transaction-active-restart.db")
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Recover the exact active transaction turn",
            work_model_version=2,
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(first_adapter.calls["agent_c"]) == 1)

    async def active_execution() -> bool:
        async with first.db.connect() as db:
            row = await first.db._fetchone(
                db,
                """SELECT state FROM agent_executions
                   WHERE room_id=? AND assignment_id IS NOT NULL
                   ORDER BY created_at DESC LIMIT 1""",
                (room_id,),
            )
        return bool(row and row["state"] == "active")

    await wait_until(active_execution)
    async with first.db.connect() as db:
        original = await first.db._fetchone(
            db,
            """SELECT * FROM agent_executions
               WHERE room_id=? AND assignment_id IS NOT NULL
               ORDER BY created_at DESC LIMIT 1""",
            (room_id,),
        )
    assert original is not None
    assignment_id = original["assignment_id"]
    original_batch_id = original["batch_id"]
    original_turn_id = original["sdk_turn_id"]
    thread_id = original["sdk_thread_id"]
    await first.close()

    second_adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    second_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Recovered exact transaction turn.",
        )
    )
    second = await transaction_runtime_factory(second_adapter, "transaction-active-restart.db")
    await wait_until(lambda: _room_finished(second, room_id))

    assert len(second_adapter.calls["agent_c"]) == 1
    recovered = second_adapter.calls["agent_c"][0]
    assert recovered["recovered"] is True
    assert recovered["thread_id"] == thread_id
    assert recovered["turn_id"] == original_turn_id

    async with second.db.connect() as db:
        executions = await db.execute_fetchall(
            """SELECT * FROM agent_executions
               WHERE room_id=? AND assignment_id=?
               ORDER BY created_at""",
            (room_id, assignment_id),
        )
    assert len(executions) == 1
    assert executions[0]["batch_id"] == original_batch_id
    assert executions[0]["state"] == "settled"

