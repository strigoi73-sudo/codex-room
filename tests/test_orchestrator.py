from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from codex_room.agent import (
    AgentRunResult,
    AgentTurnTerminalError,
    InterruptOutcome,
)
from codex_room.db import Database
from codex_room.models import (
    AgentDecision,
    CreateRoomRequest,
    NewTopicRequest,
    ObserverMessageRequest,
    Outcome,
    RoomStatus,
)
from codex_room.orchestrator import RoomRuntime

from .fakes import FakeAgentAdapter, LegacyPairDatabase, wait_until


async def _room_has_status(runtime: RoomRuntime, room_id: str, status: RoomStatus) -> bool:
    room = await runtime.db.get_room(room_id)
    return bool(room and room["status"] == status)


async def _agent_has_status(
    runtime: RoomRuntime, room_id: str, agent_key: str, status: str
) -> bool:
    agent = await runtime.db.get_agent(room_id, agent_key)
    return bool(agent and agent["status"] == status)


async def _has_stale_result(runtime: RoomRuntime, room_id: str, related_event_id: str) -> bool:
    events = await runtime.db.get_events(room_id)
    return any(
        event["event_type"] == "stale_result"
        and event["related_event_id"] == related_event_id
        for event in events
    )


async def _has_stale_failure(runtime: RoomRuntime, room_id: str) -> bool:
    return any(
        event["event_type"] == "stale_failure"
        for event in await runtime.db.get_events(room_id)
    )


async def _execution_has_state(
    runtime: RoomRuntime, batch_id: str, state: str
) -> bool:
    execution = await runtime.db.get_execution(batch_id)
    return bool(execution and execution["state"] == state)


def _usage_wall(when: str) -> AgentTurnTerminalError:
    return AgentTurnTerminalError(
        f"You've hit your usage limit. Please try again at {when}.",
        codex_error_info="usageLimitExceeded",
    )


async def _event_count(runtime: RoomRuntime, room_id: str, event_type: str) -> int:
    return sum(
        event["event_type"] == event_type
        for event in await runtime.db.get_events(room_id)
    )


async def _has_event_count(
    runtime: RoomRuntime, room_id: str, event_type: str, count: int
) -> bool:
    return await _event_count(runtime, room_id, event_type) == count


@pytest.fixture
async def runtime_factory(tmp_path):
    runtimes: list[RoomRuntime] = []

    async def make(
        adapter: FakeAgentAdapter,
        name: str = "room.db",
        *,
        triad: bool = False,
    ) -> RoomRuntime:
        database = Database(tmp_path / name) if triad else LegacyPairDatabase(tmp_path / name)
        runtime = RoomRuntime(database, adapter, tmp_path / "data")
        await runtime.initialize()
        runtimes.append(runtime)
        return runtime

    yield make
    await asyncio.gather(*(runtime.close() for runtime in runtimes), return_exceptions=True)


@pytest.mark.parametrize(
    ("reported", "expected"),
    [
        ("10:27 PM", "2026-09-06T22:27:00.000+00:00"),
        ("Sep 6th, 2026 1:33 AM", "2026-09-06T01:33:00.000+00:00"),
    ],
)
def test_usage_wall_schedule_parses_observed_codex_retry_forms(
    reported: str, expected: str
):
    schedule = RoomRuntime._usage_wall_schedule(
        _usage_wall(reported), now=datetime(2026, 9, 6, 20, tzinfo=UTC)
    )

    assert schedule == (expected, (
        datetime.fromisoformat(expected) + timedelta(seconds=60)
    ).isoformat(timespec="milliseconds"))


@pytest.mark.asyncio
async def test_usage_wall_suspends_then_targets_same_thread_continuation(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, "")]},
        failures={"agent_a": [_usage_wall("Jan 1, 2020 1:00 AM")]},
    )
    runtime = await runtime_factory(adapter, "usage-wall.db")
    room = await runtime.create_room(
        CreateRoomRequest(topic="Continue after reset", starting_agent="agent_a")
    )

    await wait_until(
        lambda: _event_count(runtime, room["id"], "usage_limit_suspended")
    )
    continuation = await runtime.db.get_usage_continuation(room["id"], "agent_a")
    assert continuation is not None
    assert continuation["state"] == "scheduled"
    assert continuation["wake_at"] > continuation["reported_retry_at"]
    assert (
        datetime.fromisoformat(continuation["wake_at"])
        - datetime.fromisoformat(continuation["reported_retry_at"])
    ).total_seconds() == 60
    assert len(adapter.calls["agent_a"]) == 1
    await asyncio.sleep(0.1)
    assert len(adapter.calls["agent_a"]) == 1
    assert adapter.calls["agent_b"] == []

    await runtime._watchdog_tick()
    await wait_until(lambda: len(adapter.completed_calls["agent_a"]) == 2)
    continued = adapter.calls["agent_a"][1]
    assert continued["thread_id"] == adapter.calls["agent_a"][0]["thread_id"]
    assert RoomRuntime.USAGE_CONTINUATION_INSTRUCTION in continued["prompt"]
    assert adapter.calls["agent_b"] == []
    assert adapter.usage_continuation_prepares == [
        {
            "agent_key": "agent_a",
            "thread_id": continued["thread_id"],
            "cwd": continued["cwd"],
        }
    ]
    await wait_until(
        lambda: _event_count(runtime, room["id"], "usage_continuation_completed")
    )
    continuation = await runtime.db.get_usage_continuation(room["id"], "agent_a")
    assert continuation and continuation["state"] == "completed"


@pytest.mark.asyncio
async def test_usage_wall_continuation_survives_restart(runtime_factory):
    first_adapter = FakeAgentAdapter(
        failures={"agent_a": [_usage_wall("Jan 1, 2020 1:00 AM")]}
    )
    first = await runtime_factory(first_adapter, "usage-restart.db")
    room = await first.create_room(
        CreateRoomRequest(topic="Survive restart", starting_agent="agent_a")
    )
    await wait_until(
        lambda: _event_count(first, room["id"], "usage_limit_suspended")
    )
    thread_id = first_adapter.calls["agent_a"][0]["thread_id"]
    await first.close()

    second_adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    second = await runtime_factory(second_adapter, "usage-restart.db")
    await second._watchdog_tick()
    await wait_until(lambda: len(second_adapter.completed_calls["agent_a"]) == 1)
    assert second_adapter.calls["agent_a"][0]["thread_id"] == thread_id
    assert RoomRuntime.USAGE_CONTINUATION_INSTRUCTION in (
        second_adapter.calls["agent_a"][0]["prompt"]
    )
    assert await _event_count(second, room["id"], "usage_continuation_wake") == 1


@pytest.mark.asyncio
async def test_repeated_usage_wall_reschedules_without_immediate_retry(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, "")]},
        failures={
            "agent_a": [
                _usage_wall("Jan 1, 2020 1:00 AM"),
                _usage_wall("Jan 1, 2020 2:00 AM"),
            ]
        },
    )
    runtime = await runtime_factory(adapter, "usage-reschedule.db")
    room = await runtime.create_room(
        CreateRoomRequest(topic="Reschedule", starting_agent="agent_a")
    )
    await wait_until(
        lambda: _event_count(runtime, room["id"], "usage_limit_suspended")
    )
    await runtime._watchdog_tick()
    await wait_until(
        lambda: _has_event_count(
            runtime, room["id"], "usage_limit_suspended", 2
        )
    )
    continuation = await runtime.db.get_usage_continuation(room["id"], "agent_a")
    assert continuation and continuation["state"] == "scheduled"
    assert continuation["reschedule_count"] == 1
    assert len(adapter.calls["agent_a"]) == 2
    await asyncio.sleep(0.1)
    assert len(adapter.calls["agent_a"]) == 2

    await runtime._watchdog_tick()
    await wait_until(lambda: len(adapter.completed_calls["agent_a"]) == 3)
    assert len(adapter.calls["agent_a"]) == 3


@pytest.mark.asyncio
async def test_non_usage_terminal_error_uses_existing_retry_path(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, "")]},
        failures={
            "agent_a": [
                AgentTurnTerminalError(
                    "generic system error", codex_error_info="internalServerError"
                )
            ]
        },
    )
    runtime = await runtime_factory(adapter, "non-usage-error.db")
    room = await runtime.create_room(
        CreateRoomRequest(topic="Ordinary retry", starting_agent="agent_a")
    )
    await wait_until(lambda: len(adapter.completed_calls["agent_a"]) == 2)
    assert await runtime.db.get_usage_continuation(room["id"], "agent_a") is None
    events = await runtime.db.get_events(room["id"])
    error = next(event for event in events if event["event_type"] == "agent_error")
    assert error["metadata"]["will_retry"] is True


@pytest.mark.asyncio
async def test_usage_wall_without_parseable_time_fails_closed(runtime_factory):
    adapter = FakeAgentAdapter(
        failures={"agent_a": [_usage_wall("whenever capacity returns")]}
    )
    runtime = await runtime_factory(adapter, "usage-invalid-time.db")
    room = await runtime.create_room(
        CreateRoomRequest(topic="Invalid reset", starting_agent="agent_a")
    )
    await wait_until(lambda: _room_has_status(runtime, room["id"], RoomStatus.ERROR))
    assert len(adapter.calls["agent_a"]) == 1
    assert await runtime.db.get_usage_continuation(room["id"], "agent_a") is None


@pytest.mark.asyncio
async def test_stop_cancels_usage_wall_continuation(runtime_factory):
    adapter = FakeAgentAdapter(
        failures={"agent_a": [_usage_wall("Jan 1, 2099 1:00 AM")]}
    )
    runtime = await runtime_factory(adapter, "usage-stop.db")
    room = await runtime.create_room(
        CreateRoomRequest(topic="Stop suspended work", starting_agent="agent_a")
    )
    await wait_until(
        lambda: _event_count(runtime, room["id"], "usage_limit_suspended")
    )
    await runtime.stop(room["id"])
    await runtime._watchdog_tick()
    continuation = await runtime.db.get_usage_continuation(room["id"], "agent_a")
    assert continuation and continuation["state"] == "cancelled"
    assert len(adapter.calls["agent_a"]) == 1


@pytest.mark.asyncio
async def test_distinct_threads_and_explicit_bidirectional_routing(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.MESSAGE, "A's independent view"), (Outcome.PASS, "")],
            "agent_b": [(Outcome.PASS, ""), (Outcome.MESSAGE, "B replies to A")],
        },
        synchronize_first_topic=True,
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(CreateRoomRequest(topic="Discuss durable queues"))
    a, b = snapshot["agents"]
    assert a["thread_id"] != b["thread_id"]

    async def routed_both_ways():
        events = await runtime.db.get_events(snapshot["id"])
        messages = [e for e in events if e["event_type"] == "agent_message"]
        return len(messages) >= 2

    await wait_until(routed_both_ways)
    await wait_until(lambda: len(adapter.calls["agent_a"]) >= 2)
    assert "A's independent view" in adapter.calls["agent_b"][1]["prompt"]
    assert "B replies to A" in adapter.calls["agent_a"][1]["prompt"]
    assert all(call["thread_id"] == a["thread_id"] for call in adapter.calls["agent_a"])
    assert all(call["thread_id"] == b["thread_id"] for call in adapter.calls["agent_b"])


@pytest.mark.asyncio
async def test_pass_does_not_create_followup_delivery(runtime_factory):
    adapter = FakeAgentAdapter(synchronize_first_topic=True)
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(CreateRoomRequest(topic="A quiet topic"))

    async def both_passed():
        events = await runtime.db.get_events(snapshot["id"])
        return len([e for e in events if e["event_type"] == "agent_pass"]) == 2

    await wait_until(both_passed)
    await asyncio.sleep(0.15)
    assert len(adapter.calls["agent_a"]) == 1
    assert len(adapter.calls["agent_b"]) == 1


@pytest.mark.asyncio
async def test_large_context_is_compacted_without_replacing_thread(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, "")]},
        usages={
            "agent_a": [{
                "last": {"input_tokens": 77_520},
                "model_context_window": 258_400,
            }]
        },
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Compact a large context", starting_agent="agent_a")
    )

    async def checkpoint_is_recorded():
        return any(
            event["event_type"] == "context_checkpoint"
            for event in await runtime.db.get_events(snapshot["id"])
        )

    await wait_until(checkpoint_is_recorded)
    assert adapter.compacted == ["agent_a"]
    events = await runtime.db.get_events(snapshot["id"])
    checkpoint = next(event for event in events if event["event_type"] == "context_checkpoint")
    assert checkpoint["event_class"] == "lifecycle"
    assert checkpoint["conversational"] is False
    assert checkpoint["metadata"] == {
        "agent": "agent_a",
        "input_tokens": 77_520,
        "model_context_window": 258_400,
        "threshold_ratio": 0.3,
        "batch_id": checkpoint["metadata"]["batch_id"],
        "result": "compacted",
        "growth_baseline_state": "pending",
    }
    current_agent = await runtime.db.get_agent(snapshot["id"], "agent_a")
    original_agent = next(agent for agent in snapshot["agents"] if agent["agent_key"] == "agent_a")
    assert current_agent["thread_id"] == original_agent["thread_id"]


@pytest.mark.asyncio
async def test_small_or_already_compacted_context_is_not_compacted_again(runtime_factory):
    small_adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, "")]},
        usages={
            "agent_a": [{
                "last": {"input_tokens": 77_519},
                "model_context_window": 258_400,
            }]
        },
    )
    small_runtime = await runtime_factory(small_adapter, "small-context.db")
    small = await small_runtime.create_room(
        CreateRoomRequest(topic="Keep a small context", starting_agent="agent_a")
    )
    await wait_until(lambda: len(small_adapter.completed_calls["agent_a"]) == 1)
    await asyncio.sleep(0.05)
    assert small_adapter.compacted == []
    assert not any(
        event["event_type"] == "context_checkpoint"
        for event in await small_runtime.db.get_events(small["id"])
    )

    automatic_adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, "")]},
        usages={
            "agent_a": [{
                "last": {"input_tokens": 100_000},
                "model_context_window": 258_400,
            }]
        },
        activities={
            "agent_a": [[{"type": "context_compaction", "status": "completed"}]]
        },
    )
    automatic_runtime = await runtime_factory(automatic_adapter, "automatic-context.db")
    automatic = await automatic_runtime.create_room(
        CreateRoomRequest(topic="Avoid double compaction", starting_agent="agent_a")
    )
    await wait_until(lambda: len(automatic_adapter.completed_calls["agent_a"]) == 1)
    await asyncio.sleep(0.05)
    assert automatic_adapter.compacted == []
    assert not any(
        event["event_type"] == "context_checkpoint"
        for event in await automatic_runtime.db.get_events(automatic["id"])
    )


@pytest.mark.asyncio
async def test_recent_manual_compaction_is_not_repeated_until_context_regrows(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [
                (Outcome.MESSAGE, "first"),
                (Outcome.PASS, ""),
            ],
            "agent_b": [(Outcome.MESSAGE, "reply")],
        },
        usages={
            "agent_a": [
                {"last": {"input_tokens": 80_000}, "model_context_window": 258_400},
                {"last": {"input_tokens": 81_000}, "model_context_window": 258_400},
            ]
        },
    )
    runtime = await runtime_factory(adapter)
    await runtime.create_room(
        CreateRoomRequest(topic="Compact once", starting_agent="agent_a")
    )

    await wait_until(lambda: len(adapter.completed_calls["agent_a"]) == 2)
    await asyncio.sleep(0.05)
    assert adapter.compacted == ["agent_a"]


def _p2_result(input_tokens: int) -> AgentRunResult:
    return AgentRunResult(
        decision=AgentDecision(outcome=Outcome.PASS),
        usage={
            "last": {"input_tokens": input_tokens},
            "model_context_window": 258_400,
        },
    )


async def _run_p2_check(
    runtime: RoomRuntime,
    room_id: str,
    round_id: str,
    agent: dict,
    input_tokens: int,
    batch_number: int,
) -> None:
    await runtime._maybe_compact_context(
        {
            "room_id": room_id,
            "round_id": round_id,
            "batch_id": f"p2_batch_{batch_number}",
        },
        agent,
        _p2_result(input_tokens),
    )


@pytest.mark.asyncio
async def test_post_compaction_baseline_prevents_successive_ratchet(runtime_factory):
    adapter = FakeAgentAdapter()
    runtime = await runtime_factory(adapter, "p2-no-ratchet.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="P2", starting_agent="agent_a", auto_start=False)
    )
    agent = await runtime.db.get_agent(snapshot["id"], "agent_a")
    round_id = snapshot["active_round_id"]

    for number, tokens in enumerate((80_000, 90_000, 115_000, 90_000, 115_000), 1):
        await _run_p2_check(runtime, snapshot["id"], round_id, agent, tokens, number)

    assert adapter.compacted == ["agent_a", "agent_a", "agent_a"]
    checkpoints = [
        event
        for event in await runtime.db.get_events(snapshot["id"])
        if event["event_type"] == "context_checkpoint"
    ]
    assert [item["metadata"]["input_tokens"] for item in checkpoints] == [
        80_000,
        115_000,
        115_000,
    ]
    assert checkpoints[0]["metadata"]["growth_baseline_input_tokens"] == 90_000
    assert checkpoints[1]["metadata"]["growth_baseline_input_tokens"] == 90_000
    assert checkpoints[2]["metadata"]["growth_baseline_state"] == "pending"


@pytest.mark.asyncio
async def test_post_compaction_growth_boundary(runtime_factory):
    adapter = FakeAgentAdapter()
    runtime = await runtime_factory(adapter, "p2-boundary.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="P2", starting_agent="agent_a", auto_start=False)
    )
    agent = await runtime.db.get_agent(snapshot["id"], "agent_a")
    round_id = snapshot["active_round_id"]

    await _run_p2_check(runtime, snapshot["id"], round_id, agent, 80_000, 1)
    await _run_p2_check(runtime, snapshot["id"], round_id, agent, 90_000, 2)
    await _run_p2_check(runtime, snapshot["id"], round_id, agent, 114_999, 3)
    assert adapter.compacted == ["agent_a"]
    await _run_p2_check(runtime, snapshot["id"], round_id, agent, 115_000, 4)
    assert adapter.compacted == ["agent_a", "agent_a"]


@pytest.mark.asyncio
async def test_legacy_checkpoint_establishes_conservatively_after_restart(
    runtime_factory,
):
    first_adapter = FakeAgentAdapter()
    first = await runtime_factory(first_adapter, "p2-legacy.db")
    snapshot = await first.create_room(
        CreateRoomRequest(topic="P2", starting_agent="agent_a", auto_start=False)
    )
    await first.db.create_event(
        snapshot["id"],
        "context_checkpoint",
        "room",
        "observer",
        "Legacy successful compaction",
        metadata={
            "agent": "agent_a",
            "input_tokens": 180_000,
            "model_context_window": 258_400,
            "threshold_ratio": 0.3,
            "batch_id": "legacy_batch",
            "result": "compacted",
        },
        discussion_id=snapshot["active_round_id"],
        round_id=snapshot["active_round_id"],
    )
    await first.close()

    second_adapter = FakeAgentAdapter()
    second = await runtime_factory(second_adapter, "p2-legacy.db")
    agent = await second.db.get_agent(snapshot["id"], "agent_a")
    await _run_p2_check(
        second,
        snapshot["id"],
        snapshot["active_round_id"],
        agent,
        50_000,
        1,
    )

    assert second_adapter.compacted == []
    checkpoint = await second.db.get_latest_successful_context_checkpoint(
        snapshot["id"], "agent_a"
    )
    assert checkpoint["metadata"]["growth_baseline_state"] == "established"
    assert checkpoint["metadata"]["growth_baseline_input_tokens"] == 50_000

    # Reaching the growth boundary cannot bypass the independent 30% trigger.
    await _run_p2_check(
        second,
        snapshot["id"],
        snapshot["active_round_id"],
        agent,
        75_000,
        2,
    )
    assert second_adapter.compacted == []
    await _run_p2_check(
        second,
        snapshot["id"],
        snapshot["active_round_id"],
        agent,
        77_520,
        3,
    )
    assert second_adapter.compacted == ["agent_a"]


@pytest.mark.asyncio
async def test_context_compaction_failure_is_visible_and_nonfatal(runtime_factory):
    long_failure = "first line\nsecond line " + ("x" * 2_000)
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, "")]},
        usages={
            "agent_a": [{
                "last": {"input_tokens": 100_000},
                "model_context_window": 258_400,
            }]
        },
        compact_failures={"agent_a"},
        compact_error_messages={"agent_a": long_failure},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Survive compaction failure", starting_agent="agent_a")
    )

    async def failure_is_recorded():
        return any(
            event["event_type"] == "context_checkpoint"
            and event["status"] == "error"
            for event in await runtime.db.get_events(snapshot["id"])
        )

    await wait_until(failure_is_recorded)
    room = await runtime.db.get_room(snapshot["id"])
    events = await runtime.db.get_events(snapshot["id"])
    failure = next(event for event in events if event["event_type"] == "context_checkpoint")
    assert room["status"] == RoomStatus.RUNNING
    assert failure["metadata"]["result"] == "failed"
    diagnostic = failure["metadata"]["error"]
    assert len(diagnostic) == 500
    assert diagnostic.startswith("first line second line ")
    assert diagnostic.endswith("...")
    assert "\n" not in diagnostic
    assert failure["content"].endswith(diagnostic)
    assert len(failure["content"]) < 600
    assert failure["source"] == "room"
    assert failure["destination"] == "observer"
    assert failure["event_class"] == "lifecycle"
    assert failure["conversational"] is False
    assert failure["visibility"] == "mechanical"
    assert failure["agent_readable"] is False
    assert any(event["event_type"] == "agent_pass" for event in events)


@pytest.mark.asyncio
async def test_finish_preserves_peer_turn_that_is_already_running(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.FINISH, "A is ready"), (Outcome.PASS, "")],
            "agent_b": [(Outcome.MESSAGE, "B's in-flight result")],
        },
        synchronize_first_topic=True,
        delays={"agent_a": [0.01, 0.01], "agent_b": [0.15]},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(CreateRoomRequest(topic="Preserve the peer turn"))
    room_id = snapshot["id"]

    async def closed_after_preserved_result():
        room = await runtime.db.get_room(room_id)
        events = await runtime.db.get_events(room_id)
        return room and room["status"] == RoomStatus.FINISHED and any(
            event["event_type"] == "agent_message"
            and event["content"] == "B's in-flight result"
            for event in events
        )

    await wait_until(closed_after_preserved_result)
    events = await runtime.db.get_events(room_id)
    waiting = next(event for event in events if event["event_type"] == "finish_waiting")
    assert waiting["metadata"]["peer_status"] == "running"
    assert not any(
        event["event_type"] == "stale_result" and event["source"] == "room"
        for event in events
    )


@pytest.mark.asyncio
async def test_both_agents_finish_then_room_closes(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.FINISH, "A done")],
            "agent_b": [(Outcome.FINISH, "B done")],
        },
        synchronize_first_topic=True,
        delays={"agent_a": [0.01], "agent_b": [0.12]},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(CreateRoomRequest(topic="Reach mutual closure"))
    room_id = snapshot["id"]

    await wait_until(
        lambda: _room_has_status(runtime, room_id, RoomStatus.FINISHED)
    )
    events = await runtime.db.get_events(room_id)
    assert len([event for event in events if event["event_type"] == "agent_finish"]) == 2
    closed = next(event for event in events if event["event_type"] == "discussion_closed")
    assert closed["metadata"]["reason"] == "mutual_finish"
    assert not any(event["event_type"] == "stale_result" for event in events)


@pytest.mark.asyncio
async def test_finish_then_peer_pass_closes_room(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.FINISH, "A done")],
            "agent_b": [(Outcome.PASS, "")],
        },
        synchronize_first_topic=True,
        delays={"agent_a": [0.01], "agent_b": [0.12]},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(CreateRoomRequest(topic="Close by pass"))
    room_id = snapshot["id"]

    await wait_until(
        lambda: _room_has_status(runtime, room_id, RoomStatus.FINISHED)
    )
    events = await runtime.db.get_events(room_id)
    closed = next(event for event in events if event["event_type"] == "discussion_closed")
    assert closed["metadata"]["reason"] == "finish_and_pass"
    assert any(event["event_type"] == "agent_pass" for event in events)
    assert not any(event["event_type"] == "stale_result" for event in events)


@pytest.mark.asyncio
async def test_finish_then_peer_message_gives_finishing_agent_final_turn(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [
                (Outcome.FINISH, "A thought it was done"),
                (Outcome.FINISH, "A considered B's final point"),
            ],
            "agent_b": [(Outcome.MESSAGE, "B has one final point")],
        },
        synchronize_first_topic=True,
        delays={"agent_a": [0.01, 0.01], "agent_b": [0.12]},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(CreateRoomRequest(topic="Allow a final reaction"))
    room_id = snapshot["id"]

    await wait_until(
        lambda: _room_has_status(runtime, room_id, RoomStatus.FINISHED)
    )
    assert len(adapter.calls["agent_a"]) == 2
    assert "B has one final point" in adapter.calls["agent_a"][1]["prompt"]
    events = await runtime.db.get_events(room_id)
    assert any(event["event_type"] == "agent_reopened" for event in events)
    assert len([event for event in events if event["event_type"] == "agent_finish"]) == 2


@pytest.mark.asyncio
async def test_substantive_final_replies_reopen_and_continue_discussion(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [
                (Outcome.FINISH, "A thought it was done"),
                (Outcome.MESSAGE, "A adds another substantive answer"),
            ],
            "agent_b": [
                (Outcome.MESSAGE, "B challenges the conclusion"),
                (Outcome.PASS, ""),
            ],
        },
        synchronize_first_topic=True,
        delays={"agent_a": [0.01, 0.01], "agent_b": [0.12, 0.4]},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(CreateRoomRequest(topic="Continue if warranted"))
    room_id = snapshot["id"]

    await wait_until(lambda: len(adapter.calls["agent_b"]) == 2)
    room = await runtime.db.get_room(room_id)
    agent_b = await runtime.db.get_agent(room_id, "agent_b")
    assert room["status"] == RoomStatus.RUNNING
    assert agent_b["status"] == "running"
    assert "A adds another substantive answer" in adapter.calls["agent_b"][1]["prompt"]
    events = await runtime.db.get_events(room_id)
    assert len([event for event in events if event["event_type"] == "agent_reopened"]) >= 2


@pytest.mark.asyncio
async def test_manual_stop_invalidates_a_later_running_result(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [
                (Outcome.PASS, ""),
                (Outcome.MESSAGE, "must not route after Stop"),
            ]
        },
        synchronize_first_topic=True,
        delays={"agent_a": [0.01, 0.3], "agent_b": [0.01]},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Stop race", max_consecutive_passes=10)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == len(adapter.calls["agent_b"]) == 1)
    trigger = await runtime.observer_message(
        room_id, ObserverMessageRequest(target="agent_a", content="Start a slow turn")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    await wait_until(lambda: _agent_has_status(runtime, room_id, "agent_a", "running"))

    await runtime.stop(room_id)
    await wait_until(lambda: _has_stale_result(runtime, room_id, trigger["id"]))
    events = await runtime.db.get_events(room_id)
    assert not any(
        event["event_type"] == "agent_message"
        and event["content"] == "must not route after Stop"
        for event in events
    )
    assert not any(
        task for (candidate, _), task in runtime._workers.items()
        if candidate == room_id and not task.done()
    )
    assert await _room_has_status(runtime, room_id, RoomStatus.STOPPED)


@pytest.mark.asyncio
async def test_message_sender_settles_after_exact_terminal_reactions(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_b": [(Outcome.MESSAGE, "B's bounded finding")],
            "agent_a": [(Outcome.PASS, "")],
            "agent_c": [(Outcome.FINISH, "C accepts")],
        }
    )
    runtime = await runtime_factory(adapter, "triad-causal.db", triad=True)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Causal closure",
            starting_agent="agent_b",
            max_consecutive_passes=10,
        )
    )

    await wait_until(lambda: _room_has_status(runtime, snapshot["id"], RoomStatus.FINISHED))
    events = await runtime.db.get_events(snapshot["id"])
    message = next(event for event in events if event["event_type"] == "agent_message")
    reactions = next(event for event in events if event["event_type"] == "reactions_settled")
    boundary = reactions["metadata"]["boundaries"][0]
    assert boundary["sender"] == "agent_b"
    assert boundary["message_event_id"] == message["id"]
    assert boundary["delivery_cohort"] == ["agent_a", "agent_c"]
    assert set(boundary["terminal_decision_event_ids"]) == {"agent_a", "agent_c"}
    assert len(adapter.calls["agent_b"]) == 1


@pytest.mark.asyncio
async def test_stop_quarantines_unconfirmed_turn_and_resume_never_overlaps(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.MESSAGE, "obsolete"), (Outcome.PASS, "")]},
        blocked_calls={"agent_a": {1}},
    )
    runtime = await runtime_factory(adapter)
    runtime.STOP_RETIRE_TIMEOUT_SECONDS = 0.05
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Held invocation", starting_agent="agent_a")
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)

    running = await runtime.snapshot(room_id)
    execution = next(
        agent["execution"] for agent in running["agents"]
        if agent["agent_key"] == "agent_a"
    )
    assert execution["phase"] == "invoking"
    assert execution["processing_count"] == 1
    assert execution["worker_alive"] is True
    assert execution["active_handle"] is True

    await runtime.stop(room_id)
    stopped = await runtime.snapshot(room_id)
    execution = next(
        agent["execution"] for agent in stopped["agents"]
        if agent["agent_key"] == "agent_a"
    )
    assert execution["phase"] == "stopping"
    assert execution["health"] == "progress_unobservable"
    with pytest.raises(ValueError, match="prior worker execution is still retiring"):
        await runtime.resume(room_id)
    assert len(adapter.calls["agent_a"]) == 1

    adapter.release_call("agent_a", 1)
    await wait_until(lambda: runtime._workers[(room_id, "agent_a")].done())
    await runtime.resume(room_id)
    await runtime.observer_message(
        room_id, ObserverMessageRequest(target="agent_a", content="Fresh work")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    assert adapter.calls["agent_a"][0]["thread_id"] == adapter.calls["agent_a"][1]["thread_id"]


@pytest.mark.asyncio
async def test_subscriber_receives_terminal_idle_execution_phase(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, "")]},
        blocked_calls={"agent_a": {1}},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Publish terminal phase", starting_agent="agent_a")
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)

    async with runtime.hub.subscribe(room_id) as queue:
        adapter.release_call("agent_a", 1)

        async def idle_state_arrived():
            while not queue.empty():
                payload = queue.get_nowait()
                if payload["kind"] != "state":
                    continue
                execution = next(
                    agent["execution"] for agent in payload["room"]["agents"]
                    if agent["agent_key"] == "agent_a"
                )
                if execution["phase"] == "idle":
                    return True
            return False

        await wait_until(idle_state_arrived)


@pytest.mark.asyncio
async def test_watchdog_publishes_long_running_health_without_external_input(runtime_factory):
    adapter = FakeAgentAdapter(blocked_calls={"agent_a": {1}})
    runtime = await runtime_factory(adapter)
    runtime.LONG_RUNNING_SECONDS = 0
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Observable held call", starting_agent="agent_a")
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)

    async with runtime.hub.subscribe(room_id) as queue:
        await runtime._watchdog_tick()
        payload = await asyncio.wait_for(queue.get(), timeout=1)
        assert payload["kind"] == "state"
        execution = next(
            agent["execution"] for agent in payload["room"]["agents"]
            if agent["agent_key"] == "agent_a"
        )
        assert execution["phase"] == "invoking"
        assert execution["health"] == "progress_unobservable"
        assert execution["processing_count"] == 1
        assert execution["worker_alive"] is True
        assert execution["active_handle"] is True

    adapter.release_call("agent_a", 1)


@pytest.mark.asyncio
async def test_agent_turn_execution_lease_fails_explicitly_instead_of_hanging(runtime_factory):
    adapter = FakeAgentAdapter(blocked_calls={"agent_a": {1}})
    runtime = await runtime_factory(adapter)
    runtime.AGENT_TURN_TIMEOUT_SECONDS = 0.05
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Bound a stuck turn", starting_agent="agent_a")
    )

    await wait_until(
        lambda: _room_has_status(runtime, snapshot["id"], RoomStatus.ERROR),
        timeout=5.0,
    )
    errors = [
        event
        for event in await runtime.db.get_events(snapshot["id"])
        if event["event_type"] == "agent_error"
    ]
    assert len(errors) == 1
    assert "execution lease" in errors[0]["content"]
    assert errors[0]["metadata"]["will_retry"] is False
    assert f'{snapshot["id"]}:agent_a' in adapter.interrupted


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("outcome", "message", "event_type"),
    [
        (Outcome.MESSAGE, "Recovered contribution", "agent_message"),
        (Outcome.PASS, "", "agent_pass"),
        (Outcome.FINISH, "Recovered conclusion", "agent_finish"),
    ],
)
async def test_retryable_attempt_failure_is_warning_and_success_records_recovery(
    runtime_factory, outcome, message, event_type
):
    adapter = FakeAgentAdapter(
        {"agent_a": [(outcome, message)]},
        failures={"agent_a": [RuntimeError("transient interruption")]},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Recover one logical turn", starting_agent="agent_a")
    )
    room_id = snapshot["id"]

    async def recovered_decision_exists():
        return any(
            event["event_type"] == event_type and event["source"] == "agent_a"
            for event in await runtime.db.get_events(room_id)
        )

    await wait_until(recovered_decision_exists)
    events = await runtime.db.get_events(room_id)
    warning = next(event for event in events if event["event_type"] == "agent_error")
    decision = next(
        event for event in events
        if event["event_type"] == event_type and event["source"] == "agent_a"
    )

    assert warning["status"] == "warning"
    assert warning["metadata"]["will_retry"] is True
    assert warning["metadata"]["operator_state"] == "recovered"
    assert "attempt interrupted — retrying" in warning["content"]
    assert decision["metadata"]["retry_recovery"] == {
        "status": "recovered",
        "attempt_failure_count": 1,
        "attempt_failure_event_ids": [warning["id"]],
        "attempt_batch_ids": [warning["metadata"]["batch_id"]],
    }

    # The recovery annotation is persisted, so a fresh database reader reaches
    # the same observer interpretation after restart/reconciliation.
    reopened = Database(runtime.db.path)
    reopened_decision = next(
        event for event in await reopened.get_events(room_id)
        if event["id"] == decision["id"]
    )
    assert reopened_decision["metadata"]["retry_recovery"]["status"] == "recovered"


@pytest.mark.asyncio
async def test_multiple_retry_warnings_project_to_one_recovered_logical_turn(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, "")]},
        failures={
            "agent_a": [
                RuntimeError("first transient interruption"),
                RuntimeError("second transient interruption"),
            ]
        },
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Multiple retries", starting_agent="agent_a")
    )
    room_id = snapshot["id"]

    async def recovered_after_multiple_attempts():
        return any(
            event["event_type"] == "agent_pass" and event["source"] == "agent_a"
            for event in await runtime.db.get_events(room_id)
        )

    await wait_until(recovered_after_multiple_attempts, timeout=8.0)

    projected = await runtime.db.get_events(room_id)
    warnings = [event for event in projected if event["event_type"] == "agent_error"]
    success = next(
        event for event in projected
        if event["event_type"] == "agent_pass" and event["source"] == "agent_a"
    )
    # Simulate a pre-correction success event: legacy history has the same causal
    # identifiers but no stored recovery annotation.
    async with runtime.db.connect() as db:
        await db.execute(
            "UPDATE events SET metadata_json=json_remove(metadata_json, '$.retry_recovery') WHERE id=?",
            (success["id"],),
        )
        await db.commit()
    projected = await runtime.db.get_events(room_id)
    success = next(event for event in projected if event["id"] == success["id"])
    warnings = [event for event in projected if event["event_type"] == "agent_error"]
    recovery = success["metadata"]["retry_recovery"]
    assert recovery["status"] == "recovered"
    assert recovery["attempt_failure_count"] == 2
    assert recovery["attempt_failure_event_ids"] == [item["id"] for item in warnings]
    assert all(
        item["metadata"]["operator_state"] == "recovered"
        for item in warnings
    )


@pytest.mark.asyncio
async def test_retry_exhaustion_is_the_only_terminal_agent_error(runtime_factory):
    adapter = FakeAgentAdapter(
        failures={
            "agent_a": [
                RuntimeError("first transient interruption"),
                RuntimeError("second transient interruption"),
                RuntimeError("terminal interruption"),
            ]
        }
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Exhaust recovery", starting_agent="agent_a")
    )
    await wait_until(
        lambda: _room_has_status(runtime, snapshot["id"], RoomStatus.ERROR),
        timeout=8.0,
    )

    errors = [
        event for event in await runtime.db.get_events(snapshot["id"])
        if event["event_type"] == "agent_error"
    ]
    assert len(errors) == 3
    *warnings, terminal = errors
    assert all(warning["status"] == "warning" for warning in warnings)
    assert all(
        warning["metadata"]["operator_state"] == "recovery_failed"
        for warning in warnings
    )
    assert terminal["status"] == "error"
    assert terminal["metadata"]["will_retry"] is False
    assert terminal["metadata"]["operator_state"] == "terminal_failure"
    assert terminal["metadata"]["retry_recovery"]["status"] == "failed"
    assert terminal["metadata"]["retry_recovery"]["attempt_failure_event_ids"] == [
        warning["id"] for warning in warnings
    ]
    assert "agent error — recovery failed" in terminal["content"]
    assert not any(
        event["metadata"].get("retry_recovery", {}).get("status") == "recovered"
        for event in errors
    )


@pytest.mark.asyncio
async def test_stop_before_lease_expiry_cancels_without_false_error_or_retry(runtime_factory):
    adapter = FakeAgentAdapter(
        blocked_calls={"agent_a": {1}},
        interrupt_outcomes={"agent_a": InterruptOutcome.ALREADY_INACTIVE},
    )
    runtime = await runtime_factory(adapter)
    runtime.AGENT_TURN_TIMEOUT_SECONDS = 0.2
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Stop wins the timeout race", starting_agent="agent_a")
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)

    await runtime.stop(room_id)
    await asyncio.sleep(0.25)

    events = await runtime.db.get_events(room_id)
    assert (await runtime.db.get_room(room_id))["status"] == RoomStatus.STOPPED
    assert len(adapter.calls["agent_a"]) == 1
    assert not any(event["event_type"] == "agent_error" for event in events)
    delivered_event = next(event for event in events if event["deliveries"])
    assert delivered_event["deliveries"][0]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_late_failure_after_stop_cannot_resurrect_cancelled_delivery(runtime_factory):
    adapter = FakeAgentAdapter(
        blocked_calls={"agent_a": {1}},
        failures={"agent_a": [RuntimeError("late transport failure")]},
    )
    runtime = await runtime_factory(adapter)
    runtime.STOP_RETIRE_TIMEOUT_SECONDS = 0.05
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Reject a stale failure", starting_agent="agent_a")
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)

    await runtime.stop(room_id)
    adapter.release_call("agent_a", 1)
    await wait_until(lambda: _has_stale_failure(runtime, room_id))

    events = await runtime.db.get_events(room_id)
    delivered_event = next(event for event in events if event["deliveries"])
    assert delivered_event["deliveries"][0]["status"] == "cancelled"
    assert len(adapter.calls["agent_a"]) == 1
    assert not any(event["event_type"] == "agent_error" for event in events)
    assert (await runtime.db.get_room(room_id))["status"] == RoomStatus.STOPPED


@pytest.mark.asyncio
async def test_delivery_failure_compare_and_set_is_atomic_for_original_batch(runtime_factory):
    runtime = await runtime_factory(FakeAgentAdapter())
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Atomic batch failure",
            starting_agent="agent_a",
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    round_id = snapshot["active_round_id"]
    await runtime.db.create_event(
        room_id,
        "observer_message",
        "observer",
        "agent_a",
        "Second coalesced input",
        deliver_to=("agent_a",),
        discussion_id=round_id,
        round_id=round_id,
    )
    await runtime.db.create_event(
        room_id,
        "observer_message",
        "observer",
        "agent_a",
        "Third coalesced input",
        deliver_to=("agent_a",),
        discussion_id=round_id,
        round_id=round_id,
    )
    await runtime.db.start_round(room_id, round_id)
    batch = await runtime.db.claim_next_batch(room_id, "agent_a")
    assert batch is not None and len(batch["delivery_ids"]) == 2

    async with runtime.db.connect() as db:
        await db.execute(
            "UPDATE deliveries SET status='cancelled' WHERE id=?",
            (batch["delivery_ids"][0],),
        )
        await db.commit()
    changed = await runtime.db.fail_deliveries(
        batch["delivery_ids"],
        "must be all or none",
        retry=True,
        batch_id=batch["batch_id"],
    )

    async with runtime.db.connect() as db:
        rows = await db.execute_fetchall(
            "SELECT id, status FROM deliveries WHERE id IN (?, ?)",
            tuple(batch["delivery_ids"]),
        )
    statuses = {row["id"]: row["status"] for row in rows}
    assert changed == 0
    assert statuses[batch["delivery_ids"][0]] == "cancelled"
    assert statuses[batch["delivery_ids"][1]] == "processing"


@pytest.mark.asyncio
async def test_resume_with_no_runnable_work_closes_without_inactivity_timeout(runtime_factory):
    adapter = FakeAgentAdapter(blocked_calls={"agent_a": {1}})
    runtime = await runtime_factory(adapter)
    runtime.STOP_RETIRE_TIMEOUT_SECONDS = 0.05
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Stop and resume", starting_agent="agent_a")
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)

    await runtime.stop(room_id)
    adapter.release_call("agent_a", 1)
    await wait_until(lambda: runtime._workers[(room_id, "agent_a")].done())
    await runtime.resume(room_id)

    current = await runtime.db.get_room(room_id)
    round_item = await runtime.db.get_round(current["active_round_id"])
    assert current["status"] == RoomStatus.FINISHED
    assert round_item["close_reason"] == "resume_without_work"
    events = await runtime.db.get_events(room_id)
    assert events[-1]["event_type"] == "discussion_closed"
    assert events[-1]["metadata"]["reason"] == "resume_without_work"


@pytest.mark.asyncio
async def test_watchdog_reconciles_quiescent_round_without_waiting_for_timeout(runtime_factory):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Only the designated starter has work",
            starting_agent="agent_a",
            max_consecutive_passes=10,
        )
    )
    room_id = snapshot["id"]

    async def starter_pass_was_recorded():
        return any(
            event["event_type"] == "agent_pass" and event["source"] == "agent_a"
            for event in await runtime.db.get_events(room_id)
        )

    await wait_until(starter_pass_was_recorded)
    assert (await runtime.db.get_room(room_id))["status"] == RoomStatus.RUNNING

    await runtime._watchdog_tick()

    current = await runtime.db.get_room(room_id)
    round_item = await runtime.db.get_round(current["active_round_id"])
    assert current["status"] == RoomStatus.FINISHED
    assert round_item["close_reason"] == "quiescent_without_work"

@pytest.mark.asyncio
async def test_new_topic_replacement_invalidates_old_result_without_routing(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [
                (Outcome.PASS, ""),
                (Outcome.MESSAGE, "obsolete old-topic answer"),
            ]
        },
        synchronize_first_topic=True,
        delays={"agent_a": [0.01, 0.3, 0.01], "agent_b": [0.01, 0.01]},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Old topic", max_consecutive_passes=10)
    )
    room_id = snapshot["id"]
    old_discussion_id = snapshot["discussion_id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == len(adapter.calls["agent_b"]) == 1)
    trigger = await runtime.observer_message(
        room_id, ObserverMessageRequest(target="agent_a", content="Slow old work")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    await wait_until(lambda: _agent_has_status(runtime, room_id, "agent_a", "running"))

    replaced = await runtime.new_topic(room_id, NewTopicRequest(topic="Replacement topic"))
    assert replaced["discussion_id"] != old_discussion_id
    await wait_until(lambda: _has_stale_result(runtime, room_id, trigger["id"]))
    events = await runtime.db.get_events(room_id)
    assert not any(
        event["event_type"] == "agent_message"
        and event["content"] == "obsolete old-topic answer"
        for event in events
    )


@pytest.mark.asyncio
async def test_genuinely_obsolete_discussion_result_is_recorded_as_stale(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [
                (Outcome.PASS, ""),
                (Outcome.MESSAGE, "result from obsolete discussion id"),
            ]
        },
        synchronize_first_topic=True,
        delays={"agent_a": [0.01, 0.3], "agent_b": [0.01]},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Original discussion", max_consecutive_passes=10)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == len(adapter.calls["agent_b"]) == 1)
    trigger = await runtime.observer_message(
        room_id, ObserverMessageRequest(target="agent_a", content="Work in old discussion")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    await wait_until(lambda: _agent_has_status(runtime, room_id, "agent_a", "running"))

    old_id, new_id = await runtime.db.begin_new_topic(room_id, "Direct replacement")
    assert old_id != new_id
    await wait_until(lambda: _has_stale_result(runtime, room_id, trigger["id"]))
    events = await runtime.db.get_events(room_id)
    stale = next(
        event
        for event in events
        if event["event_type"] == "stale_result" and event["related_event_id"] == trigger["id"]
    )
    assert stale["discussion_id"] == old_id
    assert stale["metadata"]["outcome"] == Outcome.MESSAGE
    assert not any(
        event["event_type"] == "agent_message"
        and event["content"] == "result from obsolete discussion id"
        for event in events
    )


@pytest.mark.asyncio
async def test_observer_message_reopens_naturally_finished_room(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.FINISH, "done"), (Outcome.PASS, "")],
            "agent_b": [(Outcome.PASS, "")],
        },
        synchronize_first_topic=True,
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(CreateRoomRequest(topic="Finish, then reopen"))
    room_id = snapshot["id"]

    async def finished():
        room = await runtime.db.get_room(room_id)
        return room and room["status"] == RoomStatus.FINISHED

    await wait_until(finished)
    original_ids = {a["agent_key"]: a["thread_id"] for a in await runtime.db.get_agents(room_id)}
    await runtime.observer_message(
        room_id, ObserverMessageRequest(target="agent_a", content="One more question")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    reopened = await runtime.db.get_room(room_id)
    retained_ids = {a["agent_key"]: a["thread_id"] for a in await runtime.db.get_agents(room_id)}
    events = await runtime.db.get_events(room_id)
    assert reopened["status"] == RoomStatus.RUNNING
    assert retained_ids == original_ids
    assert any(event["event_type"] == "discussion_reopened" for event in events)
    assert "One more question" in adapter.calls["agent_a"][1]["prompt"]


@pytest.mark.asyncio
async def test_observer_targeting_pause_and_resume(runtime_factory):
    adapter = FakeAgentAdapter(synchronize_first_topic=True)
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Initial", max_consecutive_passes=10)
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == len(adapter.calls["agent_b"]) == 1)

    await runtime.pause(room_id)
    event = await runtime.observer_message(
        room_id, ObserverMessageRequest(target="agent_a", content="Private evidence")
    )
    assert event["metadata"]["private"] is True
    await asyncio.sleep(0.12)
    assert len(adapter.calls["agent_a"]) == 1
    await runtime.resume(room_id)
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    assert "Private evidence" in adapter.calls["agent_a"][1]["prompt"]
    assert len(adapter.calls["agent_b"]) == 1

    await runtime.observer_message(
        room_id, ObserverMessageRequest(target="both", content="Shared evidence")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 3 and len(adapter.calls["agent_b"]) == 2)


@pytest.mark.asyncio
async def test_restart_retains_thread_ids_and_resumes_queues(runtime_factory, tmp_path):
    first_adapter = FakeAgentAdapter(synchronize_first_topic=True)
    first = await runtime_factory(first_adapter, "persistent.db")
    created = await first.create_room(CreateRoomRequest(topic="Persist me"))
    room_id = created["id"]
    await wait_until(lambda: len(first_adapter.calls["agent_a"]) == 1)
    original_ids = {a["agent_key"]: a["thread_id"] for a in await first.db.get_agents(room_id)}
    await first.close()

    second_adapter = FakeAgentAdapter()
    second = await runtime_factory(second_adapter, "persistent.db")
    restored_ids = {a["agent_key"]: a["thread_id"] for a in await second.db.get_agents(room_id)}
    assert restored_ids == original_ids
    assert second_adapter.starts == []
    await second.observer_message(
        room_id, ObserverMessageRequest(target="agent_b", content="After restart")
    )
    await wait_until(lambda: len(second_adapter.calls["agent_b"]) == 1)
    assert second_adapter.calls["agent_b"][0]["thread_id"] == original_ids["agent_b"]


@pytest.mark.asyncio
async def test_restart_reconciles_bound_exact_turn_without_replaying_delivery(runtime_factory):
    first_adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.FINISH, "durable completion")]},
        blocked_calls={"agent_a": {1}},
    )
    first = await runtime_factory(first_adapter, "exact-turn-restart.db")
    created = await first.create_room(
        CreateRoomRequest(topic="Crash-safe exact turn", starting_agent="agent_a")
    )
    room_id = created["id"]
    await wait_until(lambda: len(first_adapter.calls["agent_a"]) == 1)

    async def exact_turn_was_bound():
        evidence = await first.db.get_delivery_execution(room_id)
        return evidence["agent_a"].get("execution", {}).get("state") == "active"

    await wait_until(exact_turn_was_bound)
    before = await first.db.get_delivery_execution(room_id)
    execution = before["agent_a"]["execution"]
    assert execution["state"] == "active"
    assert execution["sdk_thread_id"] == first_adapter.calls["agent_a"][0]["thread_id"]
    assert execution["sdk_turn_id"] == "turn_fake_agent_a_1"

    await first.close()

    second_adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.FINISH, "durable completion")]}
    )
    second = await runtime_factory(second_adapter, "exact-turn-restart.db")

    async def settled_once():
        events = await second.db.get_events(room_id)
        return len(
            [
                event
                for event in events
                if event["event_type"] == "agent_finish"
                and event["content"] == "durable completion"
            ]
        ) == 1

    await wait_until(settled_once)
    recovered_calls = second_adapter.calls["agent_a"]
    assert len(recovered_calls) == 1
    assert recovered_calls[0]["recovered"] is True
    assert recovered_calls[0]["turn_id"] == execution["sdk_turn_id"]
    await wait_until(
        lambda: _execution_has_state(second, execution["batch_id"], "settled")
    )
    after_execution = await second.db.get_execution(execution["batch_id"])
    assert after_execution["state"] == "settled"


@pytest.mark.asyncio
async def test_turn_limit_stops_runaway_exchange(runtime_factory):
    decisions = [(Outcome.MESSAGE, "continue") for _ in range(10)]
    adapter = FakeAgentAdapter(
        {"agent_a": list(decisions), "agent_b": list(decisions)},
        synchronize_first_topic=True,
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(CreateRoomRequest(topic="Loop", max_turns=3))

    async def stopped():
        room = await runtime.db.get_room(snapshot["id"])
        return room and room["status"] == RoomStatus.STOPPED

    await wait_until(stopped)

    async def limit_was_recorded():
        events = await runtime.db.get_events(snapshot["id"])
        return any(event["event_type"] == "turn_limit" for event in events)

    await wait_until(limit_was_recorded)
    room = await runtime.db.get_room(snapshot["id"])
    events = await runtime.db.get_events(snapshot["id"])
    assert room["turn_count"] <= 3
    assert any(event["event_type"] == "turn_limit" for event in events)


@pytest.mark.asyncio
async def test_archive_and_deliberate_reset_are_auditable(runtime_factory):
    adapter = FakeAgentAdapter(synchronize_first_topic=True)
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(CreateRoomRequest(topic="Lifecycle"))
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    old_ids = {a["thread_id"] for a in await runtime.db.get_agents(room_id)}
    reset = await runtime.reset(room_id)
    new_ids = {a["thread_id"] for a in reset["agents"]}
    assert old_ids.isdisjoint(new_ids)
    assert old_ids.issubset(set(adapter.archived))
    assert any(event["event_type"] == "room_reset" for event in reset["events"])
    await runtime.archive(room_id)
    room = await runtime.db.get_room(room_id)
    assert room["status"] == RoomStatus.ARCHIVED


@pytest.mark.asyncio
async def test_agent_prompt_advertises_capability_discovery_not_one_hard_coded_tool(
    runtime_factory,
):
    adapter = FakeAgentAdapter()
    runtime = await runtime_factory(adapter, triad=True)
    await runtime.create_room(
        CreateRoomRequest(topic="Check an artifact", starting_agent="agent_c")
    )
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 1)

    prompt = adapter.calls["agent_c"][0]["prompt"]
    assert "codex-room-cap list" in prompt
    assert "codex-room-cap inspect CAPABILITY_ID" in prompt
    assert "codex-room-cap invoke CAPABILITY_ID --input-json JSON_OBJECT" in prompt
    assert "explicit inputs, objectively checkable outputs" in prompt
    assert "codex-room-cap assert-file RELATIVE_PATH" not in prompt
