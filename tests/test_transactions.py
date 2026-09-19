from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from codex_room.agent import InterruptOutcome
from codex_room.agent import AgentTurnInterruptedError, AgentTurnTerminalError
from codex_room.db import Database
from codex_room.exporter import as_markdown
from codex_room.models import (
    CreateRoomRequest,
    ObserverMessageRequest,
    PrincipalReplyRequest,
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
async def test_bctx3_worker_grace_cross_task_continuation_expiry_and_explicit_retirement(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {3, 5, 6}},
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Produce A's bounded contribution.",
                        "config": None,
                    },
                    {
                        "target": "agent_b",
                        "instruction": "Produce B's bounded contribution.",
                        "config": None,
                    },
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
                message="A task-two continuation result.",
            ),
        ]
    )
    adapter.decisions["agent_b"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="B task-one result.",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "bctx3-grace.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise bounded worker context grace.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=9,
        )
    )
    room_id = snapshot["id"]

    await wait_until(lambda: len(adapter.calls["agent_c"]) == 3)

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id",
            (room_id,),
        )
        worker_rows = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key IN ('agent_a','agent_b')
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )

    assert len(tasks) == 2
    task_one = tasks[0]
    task_two = tasks[1]
    assert task_one["state"] == "settled"
    assert task_two["state"] == "active"

    a_one = next(
        row
        for row in worker_rows
        if row["agent_key"] == "agent_a" and row["task_id"] == task_one["id"]
    )
    b_one = next(
        row
        for row in worker_rows
        if row["agent_key"] == "agent_b" and row["task_id"] == task_one["id"]
    )
    assert a_one["context_grace_state"] == "eligible"
    assert a_one["context_grace_remaining"] == 2
    assert b_one["context_grace_state"] == "eligible"
    assert b_one["context_grace_remaining"] == 2

    c_three_prompt = adapter.calls["agent_c"][2]["prompt"]
    assert "<worker_context_grace>" in c_three_prompt
    assert a_one["id"] in c_three_prompt
    assert b_one["id"] in c_three_prompt
    assert 'remaining_c_executions="2"' in c_three_prompt

    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": (
                            "Continue A's causally continuous work using the grace-eligible "
                            "provider context."
                        ),
                        "config": None,
                        "context_from_assignment_id": a_one["id"],
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

    await wait_until(lambda: len(adapter.calls["agent_c"]) == 5)

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id",
            (room_id,),
        )
        worker_rows = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key IN ('agent_a','agent_b')
               ORDER BY x.created_at, x.id""",
            (room_id,),
        )

    assert len(tasks) == 3
    task_two = tasks[1]
    task_three = tasks[2]
    assert task_two["state"] == "settled"
    assert task_three["state"] == "active"

    a_one = next(row for row in worker_rows if row["id"] == a_one["id"])
    b_one = next(row for row in worker_rows if row["id"] == b_one["id"])
    a_two = next(
        row
        for row in worker_rows
        if row["agent_key"] == "agent_a" and row["task_id"] == task_two["id"]
    )

    assert a_one["context_grace_state"] == "continued"
    assert a_one["context_grace_remaining"] == 0
    assert a_one["context_grace_continued_by_assignment_id"] == a_two["id"]
    assert a_two["context_parent_assignment_id"] == a_one["id"]
    assert a_two["context_thread_id"] == a_one["context_thread_id"]

    # B was not continued. The first and second subsequent C executions consumed
    # its two-turn grace, so CORE retired the provider thread.
    assert b_one["context_grace_state"] == "retired"
    assert b_one["context_grace_remaining"] == 0
    assert b_one["context_archived_at"] is not None
    assert b_one["context_thread_id"] in adapter.archived

    # A's continued context belongs to Task two now and receives a fresh grace
    # window when Task two settles.
    assert a_two["context_grace_state"] == "eligible"
    assert a_two["context_grace_remaining"] == 2
    assert a_two["context_thread_id"] not in adapter.archived

    c_five_prompt = adapter.calls["agent_c"][4]["prompt"]
    assert a_two["id"] in c_five_prompt
    assert b_one["id"] not in c_five_prompt

    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Task three closes the remaining prior worker objective.",
            retire_worker_context_task_ids=[task_two["id"]],
        )
    )
    adapter.release_call("agent_c", 5)

    # C's fifth execution is only the first post-Task-two execution. The explicit
    # close signal should retire A's Task-two context immediately rather than wait
    # for the automatic two-execution expiry.
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 6)

    async with runtime.db.connect() as db:
        cursor = await db.execute(
            "SELECT * FROM assignments WHERE id=?",
            (a_two["id"],),
        )
        a_two_final = await cursor.fetchone()

    assert a_two_final is not None
    assert a_two_final["context_grace_state"] == "retired"
    assert a_two_final["context_grace_remaining"] == 0
    assert a_two_final["context_archived_at"] is not None
    assert a_two_final["context_thread_id"] in adapter.archived

    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Finish the test Round at its configured hard boundary.",
        )
    )
    adapter.release_call("agent_c", 6)

    async def stopped() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)


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
async def test_transaction_interrupted_exact_turn_after_restart_retries_same_assignment(
    transaction_runtime_factory,
):
    class InterruptedOnResumeAdapter(FakeAgentAdapter):
        async def resume_agent(
            self,
            agent,
            cwd,
            thread_id,
            turn_id,
            on_progress=None,
            *,
            transactional=False,
        ):
            self.calls[agent["agent_key"]].append(
                {
                    "thread_id": thread_id,
                    "turn_id": turn_id,
                    "prompt": "[recovered interrupted exact turn]",
                    "cwd": str(cwd),
                    "recovered": True,
                }
            )
            if on_progress is not None:
                await on_progress()
            raise AgentTurnInterruptedError("Codex turn was interrupted")

    first_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {1}},
    )
    first = await transaction_runtime_factory(
        first_adapter, "transaction-interrupted-restart.db"
    )
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Retry an exact provider turn interrupted by process restart",
            work_model_version=2,
            provider_context_mode="assignment_thread",
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
    context_thread_id = original["sdk_thread_id"]
    await first.close()

    second_adapter = InterruptedOnResumeAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        turn_id_namespace="restart_retry",
    )
    second_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Recovered interrupted transaction assignment.",
        )
    )
    second = await transaction_runtime_factory(
        second_adapter, "transaction-interrupted-restart.db"
    )
    await wait_until(lambda: _room_finished(second, room_id))

    assert len(second_adapter.calls["agent_c"]) == 2
    recovered, retried = second_adapter.calls["agent_c"]
    assert recovered["recovered"] is True
    assert recovered["thread_id"] == context_thread_id
    assert recovered["turn_id"] == original_turn_id
    assert retried.get("recovered") is not True
    assert retried["thread_id"] == context_thread_id
    assert "Codex turn was interrupted" in retried["prompt"]

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
               ORDER BY created_at, batch_id""",
            (room_id, assignment_id),
        )
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=?",
            (room_id,),
        )

    assert len(assignments) == 1
    assert assignments[0]["state"] == "completed"
    assert len(executions) == 2
    assert executions[0]["batch_id"] == original_batch_id
    assert executions[0]["state"] == "failed"
    assert "Codex turn was interrupted" in executions[0]["error"]
    assert executions[1]["state"] == "settled"
    assert executions[1]["batch_id"] != original_batch_id
    assert all(row["assignment_id"] == assignment_id for row in executions)
    assert len(tasks) == 1
    assert tasks[0]["state"] == "settled"


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



@pytest.mark.asyncio
async def test_transaction_c_private_principal_consultation_resumes_same_context_without_peers(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.CONSULT_PRINCIPAL,
                message="Should I use the conservative interpretation?",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated the principal's private answer.",
            ),
        ]
    )

    runtime = await transaction_runtime_factory(adapter, "principal-consult.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Consult the principal only if judgment is required",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    async def waiting_for_principal() -> bool:
        async with runtime.db.connect() as db:
            row = await db.execute_fetchall(
                """SELECT x.*, a.agent_key FROM assignments x
                   JOIN tasks t ON t.id=x.task_id
                   JOIN agents a ON a.id=x.agent_id
                   WHERE t.room_id=? AND x.state='waiting_principal'""",
                (room_id,),
            )
        return len(row) == 1 and row[0]["agent_key"] == "agent_c"

    await wait_until(waiting_for_principal)

    first_prompt = adapter.calls["agent_c"][0]["prompt"]
    assert "you MUST use CONSULT_PRINCIPAL" in first_prompt
    assert "NEVER use COMPLETE to ask the principal a question or request a response" in first_prompt
    assert "this action, not COMPLETE, is the required waiting mechanism" in first_prompt

    async with runtime.db.connect() as db:
        assignments = await db.execute_fetchall(
            """SELECT x.*, a.agent_key FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? ORDER BY x.created_at, x.id""",
            (room_id,),
        )
    c_assignment = next(row for row in assignments if row["agent_key"] == "agent_c")
    consultation_event_id = c_assignment["result_event_id"]
    context_thread_id = c_assignment["context_thread_id"]
    assert consultation_event_id
    assert context_thread_id

    events = await runtime.db.get_events(room_id)
    consultation = next(event for event in events if event["id"] == consultation_event_id)
    assert consultation["event_type"] == "principal_message"
    assert consultation["source"] == "agent_c"
    assert consultation["destination"] == "observer"
    assert consultation["visibility"] == "private"
    assert consultation["agent_readable"] is False
    assert consultation["turn_triggering"] is False
    assert consultation["metadata"]["private"] is True
    assert consultation["metadata"]["principal_channel"] is True
    assert consultation["deliveries"] == []
    assert adapter.calls["agent_a"] == []
    assert adapter.calls["agent_b"] == []

    await runtime.pause(room_id)
    reply = await runtime.principal_reply(
        room_id,
        PrincipalReplyRequest(
            consultation_event_id=consultation_event_id,
            content="Yes. Use the conservative interpretation and explain the consequence.",
        ),
    )
    assert reply["event_type"] == "principal_reply"
    assert reply["source"] == "observer"
    assert reply["destination"] == "agent_c"
    assert reply["visibility"] == "private"
    assert reply["agent_readable"] is False
    assert reply["turn_triggering"] is False
    assert reply["related_event_id"] == consultation_event_id

    with pytest.raises(ValueError):
        await runtime.principal_reply(
            room_id,
            PrincipalReplyRequest(
                consultation_event_id=consultation_event_id,
                content="This duplicate reply must fail closed.",
            ),
        )

    async with runtime.db.connect() as db:
        queued = await db.execute_fetchall(
            "SELECT * FROM assignments WHERE id=?",
            (c_assignment["id"],),
        )
    assert queued[0]["state"] == "queued"
    assert queued[0]["principal_reply_event_id"] == reply["id"]

    await runtime.resume(room_id)
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    assert adapter.calls["agent_c"][0]["thread_id"] == context_thread_id
    assert adapter.calls["agent_c"][1]["thread_id"] == context_thread_id
    assert "<private_principal_reply " in adapter.calls["agent_c"][1]["prompt"]
    assert (
        "Yes. Use the conservative interpretation and explain the consequence."
        in adapter.calls["agent_c"][1]["prompt"]
    )
    assert "CORE did not deliver the consultation or reply to A or B" in adapter.calls[
        "agent_c"
    ][1]["prompt"]
    assert adapter.calls["agent_a"] == []
    assert adapter.calls["agent_b"] == []

    events = await runtime.db.get_events(room_id)
    persisted_reply = next(event for event in events if event["id"] == reply["id"])
    assert persisted_reply["deliveries"] == []


@pytest.mark.asyncio
async def test_transaction_principal_wait_survives_runtime_restart(
    transaction_runtime_factory,
):
    first_adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    first_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.CONSULT_PRINCIPAL,
            message="Choose alpha or beta before I continue.",
        )
    )
    runtime1 = await transaction_runtime_factory(first_adapter, "principal-restart.db")
    snapshot = await runtime1.create_room(
        CreateRoomRequest(
            topic="Restart-safe principal consultation",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    async def waiting_state() -> bool:
        async with runtime1.db.connect() as db:
            rows = await db.execute_fetchall(
                """SELECT x.* FROM assignments x
                   JOIN tasks t ON t.id=x.task_id
                   WHERE t.room_id=? AND x.state='waiting_principal'""",
                (room_id,),
            )
        return len(rows) == 1

    await wait_until(waiting_state)
    async with runtime1.db.connect() as db:
        rows = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               WHERE t.room_id=? AND x.state='waiting_principal'""",
            (room_id,),
        )
    assignment = rows[0]
    consultation_event_id = assignment["result_event_id"]
    context_thread_id = assignment["context_thread_id"]
    await runtime1.close()

    second_adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    second_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Continued after the restart-safe private reply.",
        )
    )
    runtime2 = await transaction_runtime_factory(second_adapter, "principal-restart.db")
    room = await runtime2.db.get_room(room_id)
    assert room["status"] == RoomStatus.RUNNING

    async with runtime2.db.connect() as db:
        persisted = await db.execute_fetchall(
            "SELECT * FROM assignments WHERE id=?",
            (assignment["id"],),
        )
    assert persisted[0]["state"] == "waiting_principal"
    assert persisted[0]["context_thread_id"] == context_thread_id

    await runtime2.principal_reply(
        room_id,
        PrincipalReplyRequest(
            consultation_event_id=consultation_event_id,
            content="Use beta.",
        ),
    )
    await wait_until(lambda: _room_finished(runtime2, room_id))

    assert len(second_adapter.calls["agent_c"]) == 1
    assert second_adapter.calls["agent_c"][0]["thread_id"] == context_thread_id
    assert "Use beta." in second_adapter.calls["agent_c"][0]["prompt"]
    assert second_adapter.calls["agent_a"] == []
    assert second_adapter.calls["agent_b"] == []


@pytest.mark.asyncio
async def test_transaction_stop_cancels_private_principal_wait(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.CONSULT_PRINCIPAL,
            message="I need a principal decision before continuing.",
        )
    )
    runtime = await transaction_runtime_factory(adapter, "principal-stop.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Stop a principal consultation",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    async def consultation() -> dict | None:
        events = await runtime.db.get_events(room_id)
        return next(
            (event for event in events if event["event_type"] == "principal_message"),
            None,
        )

    await wait_until(consultation)
    consult = await consultation()
    assert consult is not None

    await runtime.stop(room_id)
    async with runtime.db.connect() as db:
        rows = await db.execute_fetchall(
            """SELECT x.* FROM assignments x
               JOIN tasks t ON t.id=x.task_id
               WHERE t.room_id=?""",
            (room_id,),
        )
    assert len(rows) == 1
    assert rows[0]["state"] == "cancelled"

    with pytest.raises(ValueError, match="stopped"):
        await runtime.principal_reply(
            room_id,
            PrincipalReplyRequest(
                consultation_event_id=consult["id"],
                content="A stopped Room must not resume from this reply.",
            ),
        )


@pytest.mark.asyncio
async def test_transaction_non_coordinator_cannot_consult_principal(
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
                        "instruction": "Perform the bounded worker analysis.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="C recovered after the invalid worker action.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.CONSULT_PRINCIPAL,
            message="A must not open a private principal side channel.",
        )
    )

    runtime = await transaction_runtime_factory(adapter, "principal-c-only.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Only C may consult the principal",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    events = await runtime.db.get_events(room_id)
    assert not any(event["event_type"] == "principal_message" for event in events)
    assert len(adapter.calls["agent_a"]) == 1
    assert len(adapter.calls["agent_c"]) == 2
    assert any(
        event["event_type"] == "agent_error"
        and "CONSULT_PRINCIPAL is valid only for Agent C" in event["content"]
        for event in events
    )

@pytest.mark.asyncio
async def test_transaction_c_can_select_ordinary_config_for_its_next_execution(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                message="Delegate one bounded dependency, then continue more cheaply.",
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Return the exact word READY.",
                        "config": "luna-low",
                    }
                ],
                next_self_config="luna-high",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated READY.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(action=TransactionAction.COMPLETE, message="READY")
    )

    runtime = await transaction_runtime_factory(adapter, "c-self-config.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise C ordinary self-routing",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    assert adapter.calls["agent_c"][0]["model"] == "gpt-5.6-terra"
    assert adapter.calls["agent_c"][0]["reasoning_effort"] == "high"
    assert adapter.calls["agent_c"][1]["model"] == "gpt-5.6-luna"
    assert adapter.calls["agent_c"][1]["reasoning_effort"] == "high"
    assert adapter.calls["agent_a"][0]["model"] == "gpt-5.6-luna"
    assert adapter.calls["agent_a"][0]["reasoning_effort"] == "low"

    async with runtime.db.connect() as db:
        rows = await db.execute_fetchall(
            """SELECT x.execution_config_id, t.c_cognition_ceiling
               FROM assignments x JOIN tasks t ON t.id=x.task_id
               JOIN agents a ON a.id=x.agent_id
               WHERE t.room_id=? AND a.agent_key='agent_c'""",
            (room_id,),
        )
    assert rows[0]["execution_config_id"] == "luna-high"
    assert rows[0]["c_cognition_ceiling"] == "sol-high"


@pytest.mark.asyncio
async def test_transaction_task_scoped_cognition_approval_allows_repeated_exceptional_c_turns_and_downgrade(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.CONSULT_PRINCIPAL,
                message="This Task would materially benefit from Sol/XHigh. Approve it for this Task?",
                requested_task_cognition_ceiling="sol-xhigh",
            ),
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                message="Use the approved ceiling for integration after A returns.",
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Return A-READY.",
                        "config": "luna-low",
                    }
                ],
                next_self_config="sol-xhigh",
            ),
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                message="The difficult step is done; downgrade after B returns.",
                delegations=[
                    {
                        "target": "agent_b",
                        "instruction": "Return B-READY.",
                        "config": "luna-medium",
                    }
                ],
                next_self_config="terra-low",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Integrated A-READY and B-READY.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(action=TransactionAction.COMPLETE, message="A-READY")
    )
    adapter.decisions["agent_b"].append(
        TransactionDecision(action=TransactionAction.COMPLETE, message="B-READY")
    )

    runtime = await transaction_runtime_factory(adapter, "c-task-cognition-approval.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise Task-scoped exceptional C cognition",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    async def consultation_ready() -> bool:
        events = await runtime.db.get_events(room_id)
        return any(
            event["event_type"] == "principal_message"
            and event["metadata"].get("requested_task_cognition_ceiling") == "sol-xhigh"
            for event in events
        )

    await wait_until(consultation_ready)
    events = await runtime.db.get_events(room_id)
    consultation = next(
        event
        for event in events
        if event["event_type"] == "principal_message"
        and event["metadata"].get("requested_task_cognition_ceiling") == "sol-xhigh"
    )
    assert consultation["visibility"] == "private"
    assert consultation["deliveries"] == []

    reply = await runtime.principal_reply(
        room_id,
        PrincipalReplyRequest(
            consultation_event_id=consultation["id"],
            content="Approved Sol/XHigh for this Task.",
            cognition_approval="approve",
        ),
    )
    assert reply["metadata"]["cognition_approval"] == "approve"
    assert reply["metadata"]["requested_task_cognition_ceiling"] == "sol-xhigh"

    await wait_until(lambda: _room_finished(runtime, room_id))

    assert [call["model"] for call in adapter.calls["agent_c"]] == [
        "gpt-5.6-terra",
        "gpt-5.6-sol",
        "gpt-5.6-sol",
        "gpt-5.6-terra",
    ]
    assert [call["reasoning_effort"] for call in adapter.calls["agent_c"]] == [
        "high",
        "xhigh",
        "xhigh",
        "low",
    ]
    assert adapter.calls["agent_a"][0]["reasoning_effort"] == "low"
    assert adapter.calls["agent_b"][0]["reasoning_effort"] == "medium"

    async with runtime.db.connect() as db:
        task = (
            await db.execute_fetchall(
                "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at LIMIT 1",
                (room_id,),
            )
        )[0]
    assert task["c_cognition_ceiling"] == "sol-xhigh"


@pytest.mark.asyncio
async def test_transaction_declined_task_cognition_request_keeps_ordinary_ceiling(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.CONSULT_PRINCIPAL,
                message="May I use Sol/Max for this Task?",
                requested_task_cognition_ceiling="sol-max",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Continued within the ordinary ceiling.",
            ),
        ]
    )
    runtime = await transaction_runtime_factory(adapter, "c-task-cognition-decline.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Decline exceptional C cognition",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    async def consultation_ready() -> bool:
        return any(
            event["event_type"] == "principal_message"
            for event in await runtime.db.get_events(room_id)
        )

    await wait_until(consultation_ready)
    consultation = next(
        event
        for event in await runtime.db.get_events(room_id)
        if event["event_type"] == "principal_message"
    )
    await runtime.principal_reply(
        room_id,
        PrincipalReplyRequest(
            consultation_event_id=consultation["id"],
            content="Declined Sol/Max for this Task.",
            cognition_approval="decline",
        ),
    )
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert len(adapter.calls["agent_c"]) == 2
    assert adapter.calls["agent_c"][1]["model"] == "gpt-5.6-terra"
    assert adapter.calls["agent_c"][1]["reasoning_effort"] == "high"
    async with runtime.db.connect() as db:
        task = (
            await db.execute_fetchall(
                "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at LIMIT 1",
                (room_id,),
            )
        )[0]
    assert task["c_cognition_ceiling"] == "sol-high"


def test_transaction_peer_delegation_cannot_use_exceptional_c_config() -> None:
    with pytest.raises(ValidationError):
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "Exceptional peer cognition is not authorized.",
                    "config": "sol-xhigh",
                }
            ],
        )

@pytest.mark.asyncio
async def test_transaction_exceptional_cognition_approval_expires_at_task_boundary(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        blocked_calls={"agent_c": {3}},
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.CONSULT_PRINCIPAL,
                message="Approve Sol/XHigh for this bounded Task?",
                requested_task_cognition_ceiling="sol-xhigh",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Finished the approved bounded Task.",
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Successor Task should be back under the ordinary ceiling.",
            ),
        ]
    )
    runtime = await transaction_runtime_factory(adapter, "c-task-ceiling-expiry.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise Task cognition ceiling expiry",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=8,
        )
    )
    room_id = snapshot["id"]

    async def consultation_ready() -> bool:
        return any(
            event["event_type"] == "principal_message"
            for event in await runtime.db.get_events(room_id)
        )

    await wait_until(consultation_ready)
    consultation = next(
        event
        for event in await runtime.db.get_events(room_id)
        if event["event_type"] == "principal_message"
    )
    await runtime.principal_reply(
        room_id,
        PrincipalReplyRequest(
            consultation_event_id=consultation["id"],
            content="Approved Sol/XHigh for this Task.",
            cognition_approval="approve",
        ),
    )
    await wait_until(lambda: len(adapter.calls["agent_c"]) >= 3)

    async with runtime.db.connect() as db:
        tasks = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE room_id=? ORDER BY created_at, id",
            (room_id,),
        )
    assert len(tasks) >= 2
    assert tasks[0]["state"] == "settled"
    assert tasks[0]["c_cognition_ceiling"] == "sol-xhigh"
    assert tasks[1]["state"] == "active"
    assert tasks[1]["c_cognition_ceiling"] == "sol-high"
    assert adapter.calls["agent_c"][1]["model"] == "gpt-5.6-sol"
    assert adapter.calls["agent_c"][1]["reasoning_effort"] == "xhigh"
    assert adapter.calls["agent_c"][2]["model"] == "gpt-5.6-terra"
    assert adapter.calls["agent_c"][2]["reasoning_effort"] == "high"

    await runtime.stop(room_id, "Task-boundary cognition test complete.")
    adapter.release_call("agent_c", 3)

@pytest.mark.asyncio
async def test_transaction_unapproved_exceptional_self_config_fails_closed(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.DELEGATE,
            message="Attempt an unauthorized exceptional continuation.",
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "This child must never become runnable.",
                    "config": "luna-low",
                }
            ],
            next_self_config="sol-xhigh",
        )
    )
    runtime = await transaction_runtime_factory(adapter, "c-unapproved-exceptional.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exceptional self config must fail closed",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: _room_finished(runtime, room_id))

    assert adapter.calls["agent_a"] == []
    events = await runtime.db.get_events(room_id)
    assert not any(
        event["event_type"] == "principal_message"
        for event in events
    )
    assert any(
        event["event_type"] == "agent_error"
        and "approved cognition ceiling" in event["content"]
        for event in events
    )

@pytest.mark.asyncio
async def test_recover_interrupted_work_settles_decision_recorded_execution_without_replay(
    transaction_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.CONSULT_PRINCIPAL,
            message="Wait for the principal.",
        )
    )
    runtime = await transaction_runtime_factory(adapter, "decision-recorded-recovery.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Exercise decision-recorded restart recovery",
            work_model_version=2,
            provider_context_mode="assignment_thread",
        )
    )
    room_id = snapshot["id"]

    async def waiting_with_execution() -> bool:
        async with runtime.db.connect() as db:
            rows = await db.execute_fetchall(
                """SELECT e.batch_id, e.state, e.decision_recorded_at
                   FROM agent_executions e
                   JOIN assignments x ON x.id=e.assignment_id
                   JOIN tasks t ON t.id=x.task_id
                   WHERE t.room_id=?
                     AND x.state='waiting_principal'
                     AND e.decision_recorded_at IS NOT NULL
                   ORDER BY e.created_at DESC
                   LIMIT 1""",
                (room_id,),
            )
        return len(rows) == 1

    await wait_until(waiting_with_execution)

    async with runtime.db.connect() as db:
        rows = await db.execute_fetchall(
            """SELECT e.batch_id
               FROM agent_executions e
               JOIN assignments x ON x.id=e.assignment_id
               JOIN tasks t ON t.id=x.task_id
               WHERE t.room_id=?
                 AND x.state='waiting_principal'
                 AND e.decision_recorded_at IS NOT NULL
               ORDER BY e.created_at DESC
               LIMIT 1""",
            (room_id,),
        )
        batch_id = rows[0]["batch_id"]
        await db.execute(
            """UPDATE agent_executions
               SET state='active', settled_at=NULL
               WHERE batch_id=?""",
            (batch_id,),
        )
        await db.commit()

    await runtime.db.recover_interrupted_work()

    async with runtime.db.connect() as db:
        row = (
            await db.execute_fetchall(
                """SELECT state, settled_at, decision_recorded_at
                   FROM agent_executions
                   WHERE batch_id=?""",
                (batch_id,),
            )
        )[0]

    assert row["decision_recorded_at"] is not None
    assert row["state"] == "settled"
    assert row["settled_at"] is not None
    agent_c = await runtime.db.get_agent(room_id, "agent_c")
    assert agent_c is not None
    assert agent_c["status"] == AgentStatus.IDLE
