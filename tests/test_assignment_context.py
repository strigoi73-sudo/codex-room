from __future__ import annotations

import asyncio

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
        "otherwise do not assume unsupplied history from another Assignment"
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
    assert a_rows[1]["context_parent_assignment_id"] == first_a_id
    assert a_rows[1]["context_thread_id"] == worker_thread
    assert a_rows[1]["state"] == "completed"


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

def test_bctx3_retire_context_task_ids_validation_is_bounded() -> None:
    with pytest.raises(ValidationError, match="cannot contain duplicates"):
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="invalid duplicate retirement",
            retire_context_task_ids=["task_one", "task_one"],
        )
    with pytest.raises(ValidationError, match="at most 8 Task IDs"):
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="too many retirements",
            retire_context_task_ids=[f"task_{index}" for index in range(9)],
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
async def test_bctx3_history_recent_can_retrieve_completed_result_from_earlier_task_same_round(
    context_runtime_factory,
):
    token = "SAME-ROUND-A-4711"
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.DELEGATE,
                delegations=[
                    {
                        "target": "agent_a",
                        "instruction": "Produce one durable result for Task one.",
                        "config": None,
                    }
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task one integrated.",
            ),
            TransactionDecision(
                action=TransactionAction.HISTORY,
                history_requests=[
                    HistoryRequest(
                        operation="RECENT",
                        agent="agent_a",
                        max_results=1,
                    )
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Task two integrated the retrieved same-Round result.",
            ),
        ]
    )
    adapter.decisions["agent_a"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message=token,
        )
    )

    runtime = await context_runtime_factory(adapter, "bctx3-same-round-history.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Retrieve durable results across bounded Tasks in one Round.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            completion_policy="continuous",
            max_turns=5,
        )
    )
    room_id = snapshot["id"]

    async def stopped() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.STOPPED)

    await wait_until(stopped)

    assert len(adapter.calls["agent_c"]) == 4
    retrieved_prompt = adapter.calls["agent_c"][3]["prompt"]
    assert "<retrieved_room_history>" in retrieved_prompt
    assert token in retrieved_prompt

    exported = await runtime.db.snapshot(room_id, event_limit=None)
    assert exported is not None
    tasks = exported["active_round"]["transaction_state"]["tasks"]
    assert len(tasks) == 2
    first_a = next(
        item
        for item in tasks[0]["assignments"]
        if item["agent_key"] == "agent_a"
    )
    second_c = next(
        item
        for item in tasks[1]["assignments"]
        if item["agent_key"] == "agent_c"
    )
    assert second_c["context_event_ids"] == [first_a["result_event_id"]]

    history_events = [
        event
        for event in exported["active_round"]["events"]
        if event["event_type"] == "tool_activity"
        and event.get("metadata", {}).get("type") == "deterministic_room_history"
    ]
    assert len(history_events) == 1
    assert history_events[0]["metadata"]["selected_event_ids"] == [
        first_a["result_event_id"]
    ]


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


@pytest.mark.asyncio
async def test_assignment_context_history_search_matches_prior_round_prompt_and_returns_terminal_result(
    context_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
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
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 3)
    await wait_until(lambda: _finished(runtime, room_id))

    retrieved_prompt = adapter.calls["agent_c"][2]["prompt"]
    assert "<retrieved_room_history>" in retrieved_prompt
    assert "Launch marker is ALPHA-903." in retrieved_prompt

