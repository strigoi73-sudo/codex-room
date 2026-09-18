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
    PrepareRoundRequest,
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
    agent_a_prompt = adapter.calls["agent_a"][0]["prompt"]
    agent_b_prompt = adapter.calls["agent_b"][0]["prompt"]
    assert "<declared_sibling_assignments>" in agent_a_prompt
    assert 'agent="agent_b"' in agent_a_prompt
    assert "Audit failure modes independently." in agent_a_prompt
    assert "<declared_sibling_assignments>" in agent_b_prompt
    assert 'agent="agent_a"' in agent_b_prompt
    assert "Analyze the implementation path." in agent_b_prompt
    assert "sibling results remain independent until the join resolves" in agent_a_prompt
    assert "sibling results remain independent until the join resolves" in agent_b_prompt
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
    assert "<declared_sibling_assignments>" not in adapter.calls["agent_a"][0]["prompt"]
    assert "<declared_sibling_assignments>" not in adapter.calls["agent_b"][0]["prompt"]
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
async def test_transaction_nested_direct_return_bypasses_relay_parent(
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
                        "instruction": "Own this analysis and hand off the final check if useful.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="C integrated the directly returned final result.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegation_return_mode="coordinator",
            delegations=[
                {
                    "target": "agent_b",
                    "instruction": "Produce the finished result for C; A has no integration left.",
                    "config": None,
                }
            ],
        )
    )
    adapter.decisions["agent_b"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="B final direct result",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "nested-direct-return.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Nested direct return", work_model_version=2)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    assert len(adapter.calls["agent_a"]) == 1
    assert len(adapter.calls["agent_b"]) == 1
    c_prompt = adapter.calls["agent_c"][1]["prompt"]
    assert "B final direct result" in c_prompt
    assert 'result_source="agent_b"' in c_prompt
    assert "<task_coordination_status>" in c_prompt
    status_block = c_prompt.split("<task_coordination_status>", 1)[1].split(
        "</task_coordination_status>", 1
    )[0]
    assert "B final direct result" not in status_block
    assert 'return_mode="coordinator"' in status_block
    assert "<task_coordination_status>" not in adapter.calls["agent_a"][0]["prompt"]
    assert "<task_coordination_status>" not in adapter.calls["agent_b"][0]["prompt"]

    async with runtime.db.connect() as db:
        joins = await db.execute_fetchall(
            """SELECT j.* FROM assignment_joins j
               JOIN tasks t ON t.id=j.task_id WHERE t.room_id=?
               ORDER BY j.created_at, j.id""",
            (room_id,),
        )
        assignments = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? ORDER BY x.created_at, x.id""",
            (room_id,),
        )

    assert len(joins) == 2
    assert all(row["state"] == "released" for row in joins)
    assert {row["return_mode"] for row in joins} == {"parent", "coordinator"}
    a_assignment = next(row for row in assignments if row["agent_key"] == "agent_a")
    b_assignment = next(row for row in assignments if row["agent_key"] == "agent_b")
    assert a_assignment["state"] == "waived"
    assert b_assignment["state"] == "completed"
    assert a_assignment["result_event_id"] == b_assignment["result_event_id"]
    assert f'forwarded_assignment_id="{b_assignment["id"]}"' in c_prompt
    events = await runtime.db.get_events(room_id)
    direct_events = [
        event for event in events if event["event_type"] == "assignment_direct_return"
    ]
    assert len(direct_events) == 1
    assert direct_events[0]["metadata"]["source_assignment_id"] == b_assignment["id"]
    assert a_assignment["id"] in direct_events[0]["metadata"][
        "waived_relay_assignment_ids"
    ]
    released_events = [
        event for event in events if event["event_type"] == "assignment_join_released"
    ]
    assert len(released_events) == 2


@pytest.mark.asyncio
async def test_transaction_direct_return_child_failure_resumes_parent_for_recovery(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        failures={
            "agent_b": [
                RuntimeError("first verifier failure"),
                RuntimeError("terminal verifier failure"),
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
                        "instruction": "Own the result and recover if the verifier fails.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="C integrated A's degraded recovery.",
            ),
        ]
    )
    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegation_return_mode="coordinator",
                delegations=[
                    {
                        "target": "agent_b",
                        "instruction": "Return directly only if you produce the finished result.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A recovered after B failed.",
            ),
        ]
    )

    runtime = await transaction_runtime_factory(adapter, "direct-return-failure.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Direct return failure fallback", work_model_version=2)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_b"]) == 2
    assert len(adapter.calls["agent_a"]) == 2
    assert len(adapter.calls["agent_c"]) == 2
    assert "terminal verifier failure" in adapter.calls["agent_a"][1]["prompt"]
    assert "A recovered after B failed." in adapter.calls["agent_c"][1]["prompt"]

    events = await runtime.db.get_events(room_id)
    assert not any(
        event["event_type"] == "assignment_direct_return" for event in events
    )

    async with runtime.db.connect() as db:
        joins = await db.execute_fetchall(
            """SELECT j.* FROM assignment_joins j
               JOIN tasks t ON t.id=j.task_id WHERE t.room_id=?
               ORDER BY j.created_at, j.id""",
            (room_id,),
        )
        assignments = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? ORDER BY x.created_at, x.id""",
            (room_id,),
        )
    assert len(joins) == 2
    assert all(row["state"] == "released" for row in joins)
    a_assignment = next(row for row in assignments if row["agent_key"] == "agent_a")
    b_assignment = next(row for row in assignments if row["agent_key"] == "agent_b")
    assert a_assignment["state"] == "completed"
    assert b_assignment["state"] == "failed"


@pytest.mark.asyncio
async def test_transaction_explicit_same_task_worker_context_lineage_reuses_thread(
    transaction_runtime_factory,
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
                    "instruction": "Perform the first bounded implementation pass.",
                    "config": None,
                }
            ],
        )
    )
    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A first pass complete.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A continued pass complete.",
            ),
        ]
    )

    runtime = await transaction_runtime_factory(adapter, "worker-context-lineage.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Worker context lineage",
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
        cursor = await db.execute(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id LIMIT 1""",
            (room_id,),
        )
        first_a = await cursor.fetchone()
    assert first_a is not None
    first_a_id = first_a["id"]
    first_a_thread = first_a["context_thread_id"]
    assert first_a_thread

    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Continue the same bounded objective using your prior local context.",
                        "config": None,
                        "context_from_assignment_id": first_a_id,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="C integrated the continued worker result.",
            ),
        ]
    )
    adapter.release_call("agent_c", 2)

    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_a"]) == 2
    assert adapter.calls["agent_a"][0]["thread_id"] == first_a_thread
    assert adapter.calls["agent_a"][1]["thread_id"] == first_a_thread
    assert len([item for item in adapter.context_starts if item[0] == "agent_a"]) == 1
    assert first_a_id in adapter.calls["agent_a"][1]["prompt"]

    async with runtime.db.connect() as db:
        a_assignments = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )
    assert len(a_assignments) == 2
    assert a_assignments[0]["task_id"] == a_assignments[1]["task_id"]
    assert a_assignments[1]["context_parent_assignment_id"] == first_a_id
    assert a_assignments[1]["context_thread_id"] == first_a_thread


@pytest.mark.asyncio
async def test_transaction_local_repair_loop_reuses_verifier_context_explicitly(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_a": {2}},
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Implement, repair if needed, and return the verified result.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="C integrated A's verified result.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegations=[
                {
                    "target": "agent_b",
                    "instruction": "Verify A's first implementation pass.",
                    "config": None,
                }
            ],
        )
    )
    adapter.decisions["agent_b"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="B found one defect.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="B re-verified the repair successfully.",
            ),
        ]
    )

    runtime = await transaction_runtime_factory(adapter, "local-repair-loop.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise local repair-loop context continuity",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    await wait_until(
        lambda: len(adapter.completed_calls["agent_b"]) == 1
        and len(adapter.calls["agent_a"]) == 2
    )

    async with runtime.db.connect() as db:
        b_rows = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_b'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )
    assert len(b_rows) == 1
    first_b_id = b_rows[0]["id"]
    first_b_thread = b_rows[0]["context_thread_id"]
    assert first_b_thread
    assert "B found one defect." in adapter.calls["agent_a"][1]["prompt"]
    assert f'assignment_id="{first_b_id}"' in adapter.calls["agent_a"][1]["prompt"]

    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_b",
                        "instruction": "Re-verify the repair using the same local verifier context.",
                        "config": None,
                        "context_from_assignment_id": first_b_id,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A repaired the defect and B re-verified it.",
            ),
        ]
    )
    adapter.release_call("agent_a", 2)

    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_a"]) == 3
    assert len(adapter.calls["agent_b"]) == 2
    assert adapter.calls["agent_b"][0]["thread_id"] == first_b_thread
    assert adapter.calls["agent_b"][1]["thread_id"] == first_b_thread
    assert len([item for item in adapter.context_starts if item[0] == "agent_b"]) == 1
    assert (
        "Provider context lineage explicitly continues from Assignment ID: "
        + first_b_id
        in adapter.calls["agent_b"][1]["prompt"]
    )
    assert "B re-verified the repair successfully." in adapter.calls["agent_a"][2]["prompt"]
    assert "A repaired the defect and B re-verified it." in adapter.calls["agent_c"][1]["prompt"]

    async with runtime.db.connect() as db:
        a_rows = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )
        b_rows = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_b'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )

    assert len(a_rows) == 1
    assert a_rows[0]["state"] == "completed"
    assert len(b_rows) == 2
    assert b_rows[1]["context_parent_assignment_id"] == first_b_id
    assert b_rows[1]["context_thread_id"] == first_b_thread


@pytest.mark.asyncio
async def test_transaction_same_task_worker_context_stays_fresh_without_explicit_lineage(
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
                        "instruction": "Perform bounded worker pass one.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Perform independent bounded worker pass two.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="C integrated both independent worker passes.",
            ),
        ]
    )
    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A independent pass one.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A independent pass two.",
            ),
        ]
    )

    runtime = await transaction_runtime_factory(adapter, "worker-context-fresh.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Worker context stays fresh",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_a"]) == 2
    assert adapter.calls["agent_a"][0]["thread_id"] != adapter.calls["agent_a"][1]["thread_id"]
    assert len([item for item in adapter.context_starts if item[0] == "agent_a"]) == 2

    async with runtime.db.connect() as db:
        a_assignments = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )
    assert len(a_assignments) == 2
    assert a_assignments[0]["task_id"] == a_assignments[1]["task_id"]
    assert a_assignments[0]["context_parent_assignment_id"] is None
    assert a_assignments[1]["context_parent_assignment_id"] is None
    assert (
        a_assignments[0]["context_thread_id"]
        != a_assignments[1]["context_thread_id"]
    )


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
async def test_bctx3_grace_allows_explicit_worker_context_continuation_into_successor_task(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {3}},
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Develop the first bounded objective.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task one integrated.",
            ),
        ]
    )
    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A task-one result.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A successor continuation result.",
            ),
        ]
    )

    runtime = await transaction_runtime_factory(adapter, "bctx3-grace-reuse.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Continue objective-local worker context when useful.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=6,
        )
    )
    room_id = snapshot["id"]

    await wait_until(
        lambda: len(adapter.completed_calls["agent_a"]) == 1
        and len(adapter.calls["agent_c"]) == 3
    )

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id",
            (room_id,),
        )
        a_rows = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )

    assert len(tasks) == 2
    assert tasks[0]["state"] == "settled"
    assert tasks[0]["worker_context_grace_remaining"] == 2
    assert len(a_rows) == 1
    first_a_id = a_rows[0]["id"]
    worker_thread = a_rows[0]["context_thread_id"]
    assert worker_thread
    grace_prompt = adapter.calls["agent_c"][2]["prompt"]
    assert "<worker_context_grace>" in grace_prompt
    assert f'id="{tasks[0]["id"]}"' in grace_prompt
    assert 'remaining_c_executions="2"' in grace_prompt
    assert f'assignment_id="{first_a_id}"' in grace_prompt

    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Continue the same objective-local line of work.",
                        "config": None,
                        "context_from_assignment_id": first_a_id,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task two integrated.",
            ),
        ]
    )
    adapter.release_call("agent_c", 3)

    async def stopped() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)

    assert len(adapter.calls["agent_a"]) == 2
    assert adapter.calls["agent_a"][0]["thread_id"] == worker_thread
    assert adapter.calls["agent_a"][1]["thread_id"] == worker_thread
    assert len([item for item in adapter.context_starts if item[0] == "agent_a"]) == 1

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id",
            (room_id,),
        )
        a_rows = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )

    assert len(a_rows) == 2
    assert a_rows[1]["task_id"] == tasks[1]["id"]
    assert a_rows[1]["context_parent_assignment_id"] == first_a_id
    assert a_rows[1]["context_thread_id"] == worker_thread
    assert tasks[0]["worker_context_grace_remaining"] == 0
    assert worker_thread in adapter.archived


@pytest.mark.asyncio
async def test_bctx3_grace_expires_after_two_c_executions_and_restart_finishes_archive(
    transaction_runtime_factory,
):
    first_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        archive_failures=1,
    )
    first_adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Create worker context for the first Task.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task one complete.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task two complete without reusing prior worker context.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task three complete after the second C grace execution.",
            ),
        ]
    )
    first_adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="A first-task result.",
        )
    )

    first = await transaction_runtime_factory(first_adapter, "bctx3-grace-restart.db")
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Expire unused worker context after two C executions.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=5,
        )
    )
    room_id = snapshot["id"]

    async def stopped() -> bool:
        room = await first.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)

    assert 'remaining_c_executions="2"' in first_adapter.calls["agent_c"][2]["prompt"]
    assert 'remaining_c_executions="1"' in first_adapter.calls["agent_c"][3]["prompt"]

    async with first.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id",
            (room_id,),
        )
        a_row = await first.db._fetchone(
            db,
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id LIMIT 1""",
            (room_id,),
        )

    assert a_row is not None
    worker_thread = a_row["context_thread_id"]
    assert worker_thread
    assert tasks[0]["worker_context_grace_remaining"] == 0
    assert tasks[0]["worker_context_grace_retirement_reason"] == "grace_expired"
    assert a_row["context_retired_at"] is not None
    assert a_row["context_archive_confirmed_at"] is None
    assert worker_thread not in first_adapter.archived
    await first.close()

    second_adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    second = await transaction_runtime_factory(
        second_adapter, "bctx3-grace-restart.db"
    )

    assert second_adapter.archived == [worker_thread]
    pending = await second.db.get_pending_worker_context_archives(room_id)
    assert pending == []
    async with second.db.connect() as db:
        recovered = await second.db._fetchone(
            db,
            "SELECT * FROM assignments WHERE id=?",
            (a_row["id"],),
        )
    assert recovered is not None
    assert recovered["context_archive_confirmed_at"] is not None


@pytest.mark.asyncio
async def test_bctx3_coordinator_can_retire_grace_context_early(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {3}},
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Create one worker context that C will later close.",
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
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="A completed the first Task.",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "bctx3-early-retire.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Explicitly close completed objective-local worker context.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=4,
        )
    )
    room_id = snapshot["id"]

    await wait_until(
        lambda: len(adapter.completed_calls["agent_a"]) == 1
        and len(adapter.calls["agent_c"]) == 3
    )
    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id",
            (room_id,),
        )
        a_row = await runtime.db._fetchone(
            db,
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_a'
               ORDER BY x.created_at, x.id LIMIT 1""",
            (room_id,),
        )

    assert len(tasks) == 2
    first_task_id = tasks[0]["id"]
    assert tasks[0]["worker_context_grace_remaining"] == 2
    assert a_row is not None
    worker_thread = a_row["context_thread_id"]
    assert worker_thread

    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="The prior bounded objective is closed; move on.",
            retire_context_task_ids=[first_task_id],
        )
    )
    adapter.release_call("agent_c", 3)

    async def stopped() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)

    async with runtime.db.connect() as db:
        first_task = await runtime.db._fetchone(
            db, "SELECT * FROM tasks WHERE id=?", (first_task_id,)
        )
        retired_a = await runtime.db._fetchone(
            db, "SELECT * FROM assignments WHERE id=?", (a_row["id"],)
        )

    assert first_task is not None
    assert first_task["worker_context_grace_remaining"] == 0
    assert (
        first_task["worker_context_grace_retirement_reason"]
        == "coordinator_closed_objective"
    )
    assert retired_a is not None
    assert retired_a["context_retired_at"] is not None
    assert retired_a["context_archive_confirmed_at"] is not None
    assert worker_thread in adapter.archived
    events = await runtime.db.get_events(room_id)
    retire_events = [
        event for event in events if event["event_type"] == "worker_context_retired"
    ]
    assert retire_events
    assert first_task_id in (
        retire_events[-1]["metadata"].get("retire_context_task_ids") or []
    )


@pytest.mark.asyncio
async def test_continuous_round_settles_bounded_tasks_and_reuses_coordinator_context_until_turn_limit(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="First bounded activity complete.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Second bounded activity complete.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Third bounded activity complete at the hard limit.",
            ),
        ]
    )

    runtime = await transaction_runtime_factory(adapter, "continuous-complete.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Stay busy.",
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
    context_threads = {call["thread_id"] for call in adapter.calls["agent_c"]}
    assert len(context_threads) == 1
    assert len([item for item in adapter.context_starts if item[0] == "agent_c"]) == 1
    assert all("<continuous_round>" in call["prompt"] for call in adapter.calls["agent_c"])
    assert all("Stay busy." in call["prompt"] for call in adapter.calls["agent_c"])

    exported = await runtime.db.snapshot(room_id, event_limit=None)
    assert exported is not None
    assert exported["active_round"]["completion_policy"] == "continuous"
    resumed = [
        event
        for event in exported["events"]
        if event["event_type"] == "continuous_round_resumed"
    ]
    assert len(resumed) == 2

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id", (room_id,)
        )
        assignments = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? ORDER BY x.created_at, x.id""",
            (room_id,),
        )

    assert len(tasks) == 3
    assert all(row["state"] == "settled" for row in tasks)
    assert tasks[0]["parent_task_id"] is None
    assert tasks[1]["parent_task_id"] == tasks[0]["id"]
    assert tasks[2]["parent_task_id"] == tasks[1]["id"]

    c_assignments = [row for row in assignments if row["agent_key"] == "agent_c"]
    assert len(c_assignments) == 3
    assert all(row["state"] == "completed" for row in c_assignments)
    assert {row["context_thread_id"] for row in c_assignments} == context_threads
    assert [row["task_id"] for row in c_assignments] == [row["id"] for row in tasks]

    assert [event["metadata"]["task_id"] for event in resumed] == [
        tasks[0]["id"],
        tasks[1]["id"],
    ]
    assert [event["metadata"]["successor_task_id"] for event in resumed] == [
        tasks[1]["id"],
        tasks[2]["id"],
    ]
    assert [event["metadata"]["successor_assignment_id"] for event in resumed] == [
        c_assignments[1]["id"],
        c_assignments[2]["id"],
    ]


@pytest.mark.asyncio
async def test_continuous_round_pass_settles_task_and_creates_successor_without_closing_round(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    runtime = await transaction_runtime_factory(adapter, "continuous-pass.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Stay busy.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=2,
        )
    )
    room_id = snapshot["id"]

    async def stopped() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)

    assert len(adapter.calls["agent_c"]) == 2
    assert adapter.calls["agent_c"][0]["thread_id"] == adapter.calls["agent_c"][1]["thread_id"]
    events = await runtime.db.get_events(room_id)
    assert sum(event["event_type"] == "agent_pass" for event in events) == 2
    resumed = [
        event for event in events if event["event_type"] == "continuous_round_resumed"
    ]
    assert len(resumed) == 1
    assert not any(
        event["event_type"] == "discussion_closed"
        and event.get("metadata", {}).get("reason") == "transaction_settled"
        for event in events
    )

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id", (room_id,)
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
    assert tasks[1]["parent_task_id"] == tasks[0]["id"]
    c_assignments = [row for row in assignments if row["agent_key"] == "agent_c"]
    assert len(c_assignments) == 2
    assert all(row["state"] == "passed" for row in c_assignments)
    assert len({row["context_thread_id"] for row in c_assignments}) == 1
    assert resumed[0]["metadata"]["successor_task_id"] == tasks[1]["id"]
    assert resumed[0]["metadata"]["successor_assignment_id"] == c_assignments[1]["id"]


@pytest.mark.asyncio
async def test_continuous_round_child_assignment_completes_normally_and_preserves_scope(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                message="A has one bounded child task.",
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Perform exactly one bounded child task.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated the child result.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Completed another bounded coordinator activity.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Bounded child task complete.",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "continuous-child-scope.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Stay busy.",
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

    assert len(adapter.calls["agent_a"]) == 1
    child_prompt = adapter.calls["agent_a"][0]["prompt"]
    assert "<continuous_round>" in child_prompt
    assert "Child Assignments still complete normally." in child_prompt
    assert "Stay within your current Assignment" in child_prompt
    assert "requeues that coordinator Assignment" not in child_prompt

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id", (room_id,)
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
    assert tasks[1]["parent_task_id"] == tasks[0]["id"]
    a_assignments = [row for row in assignments if row["agent_key"] == "agent_a"]
    assert len(a_assignments) == 1
    assert a_assignments[0]["state"] == "completed"
    c_assignments = [row for row in assignments if row["agent_key"] == "agent_c"]
    assert len(c_assignments) == 2
    assert c_assignments[0]["task_id"] == tasks[0]["id"]
    assert c_assignments[1]["task_id"] == tasks[1]["id"]
    assert c_assignments[0]["context_thread_id"] == c_assignments[1]["context_thread_id"]


@pytest.mark.asyncio
async def test_continuous_successor_task_preserves_required_contributors_and_keeps_workers_task_local(
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
                        "instruction": "Contribute to bounded task one.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated bounded task one.",
            ),
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Contribute to bounded task two.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated bounded task two at the hard limit.",
            ),
        ]
    )
    adapter.decisions["agent_a"].extend(
        [
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A contribution for task one.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="A contribution for task two.",
            ),
        ]
    )

    runtime = await transaction_runtime_factory(adapter, "continuous-required.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Stay busy.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            required_contributors=["agent_a"],
            max_turns=6,
        )
    )
    room_id = snapshot["id"]

    async def stopped() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id", (room_id,)
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
    assert tasks[1]["parent_task_id"] == tasks[0]["id"]
    assert all(row["required_contributors_json"] == '["agent_a"]' for row in tasks)

    c_assignments = [row for row in assignments if row["agent_key"] == "agent_c"]
    a_assignments = [row for row in assignments if row["agent_key"] == "agent_a"]
    assert len(c_assignments) == 2
    assert len(a_assignments) == 2
    assert [row["task_id"] for row in c_assignments] == [row["id"] for row in tasks]
    assert [row["task_id"] for row in a_assignments] == [row["id"] for row in tasks]
    assert c_assignments[0]["context_thread_id"] == c_assignments[1]["context_thread_id"]
    assert a_assignments[0]["context_thread_id"] != a_assignments[1]["context_thread_id"]
    assert len([item for item in adapter.context_starts if item[0] == "agent_c"]) == 1
    assert len([item for item in adapter.context_starts if item[0] == "agent_a"]) == 2


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

    second_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        turn_id_namespace="after_restart",
    )
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

@pytest.mark.asyncio
async def test_transaction_new_round_cancels_old_work_and_late_result_cannot_settle(
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
                        "instruction": "Old-round work that will finish late.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="New round completed independently.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Late old-round result must not settle anything.",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "transaction-new-round.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Old transaction round", work_model_version=2)
    )
    room_id = snapshot["id"]
    old_round_id = snapshot["active_round_id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)

    prepared = await runtime.prepare_round(
        room_id,
        PrepareRoundRequest(
            title="Replacement",
            prompt="New transaction round",
            work_model_version=2,
        ),
    )
    new_round_id = prepared["active_round_id"]
    assert new_round_id != old_round_id
    await runtime.start_round(room_id, new_round_id)
    await wait_until(lambda: _room_finished(runtime, room_id))

    adapter.release_call("agent_a", 1)
    await wait_until(lambda: len(adapter.completed_calls["agent_a"]) == 1)
    await asyncio.sleep(0.05)

    async with runtime.db.connect() as db:
        old_tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? AND round_id=?",
            (room_id, old_round_id),
        )
        old_assignments = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               WHERE t.room_id=? AND t.round_id=?""",
            (room_id, old_round_id),
        )
        new_tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? AND round_id=?",
            (room_id, new_round_id),
        )
    assert old_tasks and all(row["state"] == "cancelled" for row in old_tasks)
    assert old_assignments and all(
        row["state"] in {"cancelled", "completed", "passed", "failed", "waived"}
        for row in old_assignments
    )
    assert new_tasks and new_tasks[0]["state"] == "settled"
    events = await runtime.db.get_events(room_id)
    assert not any(
        event["event_type"] == "agent_message"
        and event["content"] == "Late old-round result must not settle anything."
        for event in events
    )

