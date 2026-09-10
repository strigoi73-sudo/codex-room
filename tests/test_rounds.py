from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3

import pytest

import codex_room.db as db_module
from codex_room.db import Database, new_id, utc_now
from codex_room.exporter import as_json
from codex_room.models import (
    AGENT_A_IMPLEMENTER_INSTRUCTIONS,
    AGENT_B_VERIFIER_INSTRUCTIONS,
    CreateRoomRequest,
    ObserverMessageRequest,
    Outcome,
    PrepareRoundRequest,
    RoomStatus,
)
from codex_room.orchestrator import RoomRuntime

from .fakes import FakeAgentAdapter, wait_until


@pytest.fixture
async def runtime_factory(tmp_path):
    runtimes: list[RoomRuntime] = []

    async def make(adapter: FakeAgentAdapter, name: str = "rounds.db") -> RoomRuntime:
        runtime = RoomRuntime(Database(tmp_path / name), adapter, tmp_path / "data")
        await runtime.initialize()
        runtimes.append(runtime)
        return runtime

    yield make
    await asyncio.gather(*(runtime.close() for runtime in runtimes), return_exceptions=True)


async def _agent_status(runtime: RoomRuntime, room_id: str, key: str, status: str) -> bool:
    agent = await runtime.db.get_agent(room_id, key)
    return bool(agent and agent["status"] == status)


@pytest.mark.asyncio
async def test_a_first_round_stores_b_context_but_only_runs_a(runtime_factory):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="A opens",
            starting_agent="agent_a",
            max_consecutive_passes=10,
            auto_start=False,
        )
    )
    await asyncio.sleep(0.08)
    assert len(adapter.calls["agent_a"]) == len(adapter.calls["agent_b"]) == 0
    assert snapshot["status"] == RoomStatus.PREPARING
    await runtime.start_round(snapshot["id"], snapshot["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    await wait_until(lambda: _round_has_turns(runtime, snapshot["active_round_id"], 1))

    round_item = snapshot["active_round"]
    states = await runtime.db.get_round_agent_states(round_item["id"])
    b_state = next(state for state in states if state["agent_key"] == "agent_b")
    assert len(adapter.calls["agent_b"]) == 0
    assert b_state["context_stored_at"]
    assert b_state["context_consumed_at"] is None
    current = await runtime.db.get_round(round_item["id"])
    assert current["turn_count"] == 1
    assert current["consecutive_passes"] == 1


@pytest.mark.asyncio
async def test_b_first_round_stores_a_context_but_only_runs_b(runtime_factory):
    adapter = FakeAgentAdapter({"agent_b": [(Outcome.PASS, "")]})
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="B opens",
            starting_agent="agent_b",
            max_consecutive_passes=10,
            auto_start=False,
        )
    )
    await asyncio.sleep(0.08)
    assert len(adapter.calls["agent_a"]) == len(adapter.calls["agent_b"]) == 0
    assert snapshot["status"] == RoomStatus.PREPARING
    await runtime.start_round(snapshot["id"], snapshot["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_b"]) == 1)
    await asyncio.sleep(0.08)

    states = await runtime.db.get_round_agent_states(snapshot["active_round_id"])
    a_state = next(state for state in states if state["agent_key"] == "agent_a")
    assert len(adapter.calls["agent_a"]) == 0
    assert a_state["context_stored_at"]
    assert a_state["context_consumed_at"] is None


@pytest.mark.asyncio
async def test_private_initialization_barrier_stores_without_running_or_cross_leaking(
    runtime_factory,
):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.PASS, ""), (Outcome.PASS, "")],
            "agent_b": [(Outcome.PASS, "")],
        }
    )
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Initial", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    baseline = {key: len(adapter.calls[key]) for key in ("agent_a", "agent_b")}

    prepared = await runtime.prepare_round(
        room["id"],
        PrepareRoundRequest(
            prompt="Shared experiment",
            agent_a_private="A-only package",
            agent_b_private="B-only package",
            starting_agent="agent_a",
        ),
    )
    await asyncio.sleep(0.08)
    assert {key: len(adapter.calls[key]) for key in baseline} == baseline
    private_events = [
        event for event in prepared["events"] if event["event_type"] == "private_initialization"
    ]
    assert len(private_events) == 2
    assert all(not event["deliveries"] for event in private_events)
    assert not any(event["event_type"] == "agent_pass" and event["round_id"] == prepared["active_round_id"] for event in prepared["events"])

    await runtime.start_round(room["id"], prepared["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_a"]) == baseline["agent_a"] + 1)
    a_prompt = adapter.calls["agent_a"][-1]["prompt"]
    assert "A-only package" in a_prompt
    assert "B-only package" not in a_prompt
    assert len(adapter.calls["agent_b"]) == baseline["agent_b"]

    await runtime.observer_message(
        room["id"], ObserverMessageRequest(target="agent_b", content="Now B may respond")
    )
    await wait_until(lambda: len(adapter.calls["agent_b"]) == baseline["agent_b"] + 1)
    b_prompt = adapter.calls["agent_b"][-1]["prompt"]
    assert "B-only package" in b_prompt
    assert "A-only package" not in b_prompt


@pytest.mark.asyncio
async def test_pass_state_resets_between_rounds(runtime_factory):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Pass in round one", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    await wait_until(lambda: _round_has_passes(runtime, room["active_round_id"], 1))
    first = await runtime.db.get_round(room["active_round_id"])
    assert first["consecutive_passes"] == 1

    prepared = await runtime.prepare_round(
        room["id"], PrepareRoundRequest(prompt="Round two", starting_agent="agent_b")
    )
    second = await runtime.db.get_round(prepared["active_round_id"])
    current_room = await runtime.db.get_room(room["id"])
    assert second["consecutive_passes"] == 0
    assert second["turn_count"] == 0
    assert current_room["consecutive_passes"] == 0


@pytest.mark.asyncio
async def test_preparation_and_control_events_do_not_count_as_passes(runtime_factory):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Initial", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    prepared = await runtime.prepare_round(
        room["id"],
        PrepareRoundRequest(
            prompt="Prepared only", agent_a_private="stored", starting_agent="agent_b"
        ),
    )
    round_events = [
        event for event in prepared["events"] if event["round_id"] == prepared["active_round_id"]
    ]
    assert round_events
    assert all(not event["counts_toward_pass"] for event in round_events)
    assert all(not event["turn_triggering"] for event in round_events)
    assert (await runtime.db.get_round(prepared["active_round_id"]))["consecutive_passes"] == 0


@pytest.mark.asyncio
async def test_backlog_is_coalesced_into_one_once_only_agent_run(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [
                (Outcome.PASS, ""),
                (Outcome.PASS, ""),
                (Outcome.PASS, ""),
            ]
        },
        delays={"agent_a": [0.01, 0.01, 0.01]},
        blocked_calls={"agent_a": {2}},
    )
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Initial", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    await runtime.observer_message(
        room["id"], ObserverMessageRequest(target="agent_a", content="occupy A")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    queued = []
    for content in ("unread one", "unread two", "unread three"):
        queued.append(
            await runtime.observer_message(
                room["id"], ObserverMessageRequest(target="agent_a", content=content)
            )
        )
    adapter.release_call("agent_a", 2)
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 3)
    await wait_until(lambda: len(adapter.completed_calls["agent_a"]) == 3)
    queued_ids = {event["id"] for event in queued}
    await wait_until(
        lambda: _events_have_delivery_status(runtime, room["id"], queued_ids, "delivered")
    )
    await wait_until(lambda: _round_has_turns(runtime, room["active_round_id"], 3))
    await wait_until(lambda: _pass_for_inputs(runtime, room["id"], queued_ids))
    assert len(adapter.calls["agent_a"]) == 3
    prompt = adapter.calls["agent_a"][2]["prompt"]
    assert all(item in prompt for item in ("unread one", "unread two", "unread three"))
    events = await runtime.db.get_events(room["id"])
    pass_event = next(
        event
        for event in reversed(events)
        if event["event_type"] == "agent_pass"
        and set(event["metadata"]["input_event_ids"]) == queued_ids
    )
    assert set(pass_event["metadata"]["input_event_ids"]) == {event["id"] for event in queued}
    delivery_batches = {
        event["deliveries"][0]["batch_id"]
        for event in events
        if event["id"] in {item["id"] for item in queued}
    }
    assert len(delivery_batches) == 1
    assert all(
        event["deliveries"][0]["status"] == "delivered"
        for event in events
        if event["id"] in {item["id"] for item in queued}
    )


@pytest.mark.asyncio
async def test_consumed_event_cannot_schedule_a_duplicate_turn(runtime_factory):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, ""), (Outcome.PASS, "")]})
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Initial", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    event = await runtime.observer_message(
        room["id"], ObserverMessageRequest(target="agent_a", content="consume once")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    await wait_until(
        lambda: _delivery_has_status(runtime, room["id"], event["id"], "delivered")
    )
    runtime.wake(room["id"], "agent_a")
    await asyncio.sleep(0.15)
    assert len(adapter.calls["agent_a"]) == 2
    stored = await runtime.db.get_event(event["id"])
    full = next(item for item in await runtime.db.get_events(room["id"]) if item["id"] == stored["id"])
    assert len(full["deliveries"]) == 1
    assert full["deliveries"][0]["consumed_at"]


@pytest.mark.asyncio
async def test_finish_boundary_rejects_old_late_delivery(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, ""), (Outcome.FINISH, "ready")]}
    )
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Initial", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    old_event = await runtime.db.create_event(
        room["id"], "observer_message", "observer", "agent_a", "old stored content"
    )
    await runtime.observer_message(
        room["id"], ObserverMessageRequest(target="agent_a", content="finish from this boundary")
    )
    await wait_until(lambda: _agent_status(runtime, room["id"], "agent_a", "ready_to_finish"))
    calls_at_finish = len(adapter.calls["agent_a"])
    agent = await runtime.db.get_agent(room["id"], "agent_a")
    async with runtime.db.connect() as db:
        await db.execute(
            """INSERT INTO deliveries (id, event_id, agent_id, status, attempts, queued_at)
               VALUES (?, ?, ?, 'pending', 0, ?)""",
            (new_id("delivery"), old_event["id"], agent["id"], utc_now()),
        )
        await db.commit()
    runtime.wake(room["id"], "agent_a")
    await wait_until(
        lambda: _delivery_has_status(runtime, room["id"], old_event["id"], "cancelled")
    )
    assert len(adapter.calls["agent_a"]) == calls_at_finish
    assert await _agent_status(runtime, room["id"], "agent_a", "ready_to_finish")
    stored = next(item for item in await runtime.db.get_events(room["id"]) if item["id"] == old_event["id"])
    assert stored["deliveries"][0]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_new_substantive_message_after_finish_reopens_exactly_once(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, ""), (Outcome.FINISH, "ready"), (Outcome.PASS, "")]}
    )
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Initial", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    await runtime.observer_message(
        room["id"], ObserverMessageRequest(target="agent_a", content="consider finishing")
    )
    await wait_until(lambda: _agent_status(runtime, room["id"], "agent_a", "ready_to_finish"))
    fresh = await runtime.observer_message(
        room["id"], ObserverMessageRequest(target="agent_a", content="genuinely new evidence")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 3)
    await asyncio.sleep(0.12)
    assert len(adapter.calls["agent_a"]) == 3
    assert "genuinely new evidence" in adapter.calls["agent_a"][2]["prompt"]
    events = await runtime.db.get_events(room["id"])
    assert len(
        [
            event
            for event in events
            if event["event_type"] == "agent_reopened"
            and event["related_event_id"] == fresh["id"]
        ]
    ) == 1


@pytest.mark.asyncio
async def test_persistent_profiles_are_snapshotted_into_new_rooms(runtime_factory):
    adapter = FakeAgentAdapter()
    runtime = await runtime_factory(adapter, "profiles.db")
    await runtime.db.update_default_profiles(
        "Explorer", "persistent A personality", "Synthesizer", "persistent B personality"
    )
    room = await runtime.create_room(
        CreateRoomRequest(topic="Profile inheritance", starting_agent="agent_a")
    )
    agents = {agent["agent_key"]: agent for agent in room["agents"]}
    assert agents["agent_a"]["profile_snapshot"] == "persistent A personality"
    assert agents["agent_b"]["profile_snapshot"] == "persistent B personality"
    assert agents["agent_a"]["developer_instructions"] == "persistent A personality"
    assert agents["agent_b"]["developer_instructions"] == "persistent B personality"


@pytest.mark.asyncio
async def test_known_pair_profile_migration_repairs_only_live_unmodified_snapshots(
    tmp_path, monkeypatch
):
    database = Database(tmp_path / "profile-migration.db")
    await database.initialize()
    active_id = await database.create_room(
        CreateRoomRequest(topic="active triad", include_agent_c=True, auto_start=False)
    )
    archived_id = await database.create_room(
        CreateRoomRequest(topic="sealed predecessor", include_agent_c=True, auto_start=False)
    )
    sealed_id = await database.create_room(
        CreateRoomRequest(topic="sealed transitional predecessor", auto_start=False)
    )
    null_snapshot_id = await database.create_room(
        CreateRoomRequest(topic="legacy null snapshots", auto_start=False)
    )
    stale = {"agent_a": "known stale A", "agent_b": "known stale B"}
    stale_hashes = {
        key: hashlib.sha256(value.encode("utf-8")).hexdigest()
        for key, value in stale.items()
    }
    monkeypatch.setattr(db_module, "_LEGACY_PAIR_PROFILE_SHA256", stale_hashes)
    async with database.connect() as connection:
        for key, text in stale.items():
            await connection.execute(
                "UPDATE agent_profiles SET developer_instructions=? WHERE default_slot=?",
                (text, key),
            )
            await connection.execute(
                  """UPDATE agents SET profile_snapshot=?, developer_instructions=?
                     WHERE agent_key=? AND room_id IN (?, ?, ?, ?)""",
                (text, text, key, active_id, archived_id, sealed_id, null_snapshot_id),
            )
        await connection.execute(
            "UPDATE agents SET profile_snapshot=NULL WHERE room_id=?",
            (null_snapshot_id,),
        )
        await connection.execute(
            "UPDATE rooms SET status=?, metadata_json='{}' WHERE id=?",
            (RoomStatus.ARCHIVED, archived_id),
        )
        await connection.execute(
            "UPDATE rooms SET metadata_json=? WHERE id=?",
            ('{"sealed":true}', sealed_id),
        )
        await connection.commit()

    await database.initialize()
    defaults = await database.get_default_profiles()
    assert defaults["agent_a"]["developer_instructions"] == AGENT_A_IMPLEMENTER_INSTRUCTIONS
    assert defaults["agent_b"]["developer_instructions"] == AGENT_B_VERIFIER_INSTRUCTIONS
    active = {item["agent_key"]: item for item in await database.get_agents(active_id)}
    assert active["agent_a"]["profile_snapshot"] == AGENT_A_IMPLEMENTER_INSTRUCTIONS
    assert active["agent_b"]["profile_snapshot"] == AGENT_B_VERIFIER_INSTRUCTIONS
    archived = {item["agent_key"]: item for item in await database.get_agents(archived_id)}
    assert archived["agent_a"]["profile_snapshot"] == stale["agent_a"]
    assert archived["agent_b"]["profile_snapshot"] == stale["agent_b"]
    sealed = {item["agent_key"]: item for item in await database.get_agents(sealed_id)}
    assert sealed["agent_a"]["profile_snapshot"] == stale["agent_a"]
    assert sealed["agent_b"]["profile_snapshot"] == stale["agent_b"]
    null_snapshot = {
        item["agent_key"]: item for item in await database.get_agents(null_snapshot_id)
    }
    assert null_snapshot["agent_a"]["profile_snapshot"] == AGENT_A_IMPLEMENTER_INSTRUCTIONS
    assert null_snapshot["agent_b"]["profile_snapshot"] == AGENT_B_VERIFIER_INSTRUCTIONS
    active_room = await database.get_room(active_id)
    assert active_room is not None
    assert [item["id"] for item in active_room["metadata"]["profile_migrations"]] == [
        "triad_profiles_v1"
    ]

    await database.initialize()
    active_room = await database.get_room(active_id)
    assert active_room is not None
    assert len(active_room["metadata"]["profile_migrations"]) == 1


@pytest.mark.asyncio
async def test_room_override_does_not_mutate_persistent_profile(runtime_factory):
    adapter = FakeAgentAdapter()
    runtime = await runtime_factory(adapter, "overrides.db")
    await runtime.db.update_default_profiles("A", "base A", "B", "base B")
    room = await runtime.create_room(
        CreateRoomRequest(
            topic="Override",
            starting_agent="agent_a",
            agent_a_instructions="only this room",
        )
    )
    agent_a = next(agent for agent in room["agents"] if agent["agent_key"] == "agent_a")
    defaults = await runtime.db.get_default_profiles()
    assert agent_a["profile_snapshot"] == "base A"
    assert agent_a["room_override"] == "only this room"
    assert "base A" in agent_a["developer_instructions"]
    assert "only this room" in agent_a["developer_instructions"]
    assert defaults["agent_a"]["developer_instructions"] == "base A"


@pytest.mark.asyncio
async def test_round_overlay_is_isolated_from_later_round(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, ""), (Outcome.PASS, ""), (Outcome.PASS, "")]}
    )
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Initial", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    first = await runtime.prepare_round(
        room["id"],
        PrepareRoundRequest(
            prompt="Overlay round",
            starting_agent="agent_a",
            agent_a_overlay="temporary divergent behavior",
        ),
    )
    await runtime.start_round(room["id"], first["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    assert "temporary divergent behavior" in adapter.calls["agent_a"][1]["prompt"]

    second = await runtime.prepare_round(
        room["id"], PrepareRoundRequest(prompt="Clean round", starting_agent="agent_a")
    )
    await runtime.start_round(room["id"], second["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 3)
    assert "temporary divergent behavior" not in adapter.calls["agent_a"][2]["prompt"]
    agent_a = await runtime.db.get_agent(room["id"], "agent_a")
    assert "temporary divergent behavior" not in agent_a["developer_instructions"]


@pytest.mark.asyncio
async def test_multi_round_export_separates_prompts_counters_events_and_profiles(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, "")], "agent_b": [(Outcome.PASS, "")]}
    )
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Round one prompt", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    await wait_until(lambda: _round_has_turns(runtime, room["active_round_id"], 1))
    thread_ids = {agent["agent_key"]: agent["thread_id"] for agent in room["agents"]}
    second = await runtime.prepare_round(
        room["id"],
        PrepareRoundRequest(
            title="Second experiment",
            prompt="Round two prompt",
            starting_agent="agent_b",
            agent_b_private="B private metadata",
            task_overlay="temporary task rule",
        ),
    )
    await runtime.start_round(room["id"], second["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_b"]) == 1)
    await wait_until(lambda: _round_has_turns(runtime, second["active_round_id"], 1))
    snapshot = await runtime.db.snapshot(room["id"])
    exported = json.loads(as_json(snapshot))

    assert {agent["agent_key"]: agent["thread_id"] for agent in exported["agents"]} == thread_ids
    assert len(exported["rounds"]) == 2
    first_round, second_round = exported["rounds"]
    assert first_round["id"] != second_round["id"]
    assert first_round["prompt"] == "Round one prompt"
    assert first_round["starting_agent"] == "agent_a"
    assert second_round["prompt"] == "Round two prompt"
    assert second_round["starting_agent"] == "agent_b"
    assert second_round["task_overlay"] == "temporary task rule"
    assert second_round["agent_b_private"] == "B private metadata"
    assert all(event["round_id"] == first_round["id"] for event in first_round["events"])
    assert all(event["round_id"] == second_round["id"] for event in second_round["events"])
    assert first_round["turn_count"] == second_round["turn_count"] == 1
    assert exported["topic"] == "Round one prompt"


@pytest.mark.asyncio
async def test_peer_finish_does_not_stale_legitimate_inflight_result(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.MESSAGE, "A still has a result")],
            "agent_b": [(Outcome.FINISH, "B ready")],
        },
        synchronize_first_topic=True,
        delays={"agent_a": [0.18], "agent_b": [0.01]},
    )
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(CreateRoomRequest(topic="Concurrent finish"))
    await wait_until(
        lambda: _event_exists(runtime, room["id"], "agent_message", "A still has a result")
    )
    events = await runtime.db.get_events(room["id"])
    assert not any(event["event_type"] == "stale_result" for event in events)


async def _event_exists(
    runtime: RoomRuntime, room_id: str, event_type: str, content: str
) -> bool:
    events = await runtime.db.get_events(room_id)
    return any(event["event_type"] == event_type and event["content"] == content for event in events)


async def _round_has_turns(runtime: RoomRuntime, round_id: str, count: int) -> bool:
    round_item = await runtime.db.get_round(round_id)
    return bool(round_item and round_item["turn_count"] == count)


async def _round_has_passes(runtime: RoomRuntime, round_id: str, count: int) -> bool:
    round_item = await runtime.db.get_round(round_id)
    return bool(round_item and round_item["consecutive_passes"] == count)


async def _delivery_has_status(
    runtime: RoomRuntime, room_id: str, event_id: str, status: str
) -> bool:
    events = await runtime.db.get_events(room_id)
    event = next((item for item in events if item["id"] == event_id), None)
    return bool(event and event["deliveries"] and event["deliveries"][0]["status"] == status)


async def _events_have_delivery_status(
    runtime: RoomRuntime, room_id: str, event_ids: set[str], status: str
) -> bool:
    matching = [
        event for event in await runtime.db.get_events(room_id) if event["id"] in event_ids
    ]
    return len(matching) == len(event_ids) and all(
        event["deliveries"] and event["deliveries"][0]["status"] == status
        for event in matching
    )


async def _pass_for_inputs(
    runtime: RoomRuntime, room_id: str, input_ids: set[str]
) -> bool:
    return any(
        event["event_type"] == "agent_pass"
        and set(event.get("metadata", {}).get("input_event_ids", [])) == input_ids
        for event in await runtime.db.get_events(room_id)
    )


@pytest.mark.asyncio
async def test_manual_stop_still_stales_inflight_round_batch(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, ""), (Outcome.MESSAGE, "late invalid result")]},
        delays={"agent_a": [0.01, 0.25]},
    )
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Initial", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    trigger = await runtime.observer_message(
        room["id"], ObserverMessageRequest(target="agent_a", content="slow work")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    await runtime.stop(room["id"])
    await wait_until(lambda: _stale_for(runtime, room["id"], trigger["id"]))
    events = await runtime.db.get_events(room["id"])
    assert not any(event["event_type"] == "agent_message" and event["content"] == "late invalid result" for event in events)
    assert (await runtime.db.get_room(room["id"]))["status"] == RoomStatus.STOPPED


@pytest.mark.asyncio
async def test_stop_then_fast_resume_cannot_revalidate_pre_stop_result(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [(Outcome.PASS, ""), (Outcome.MESSAGE, "pre-stop result")]},
        delays={"agent_a": [0.01, 0.3]},
    )
    runtime = await runtime_factory(adapter)
    room = await runtime.create_room(
        CreateRoomRequest(topic="Initial", starting_agent="agent_a", max_consecutive_passes=10)
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    trigger = await runtime.observer_message(
        room["id"], ObserverMessageRequest(target="agent_a", content="slow generation")
    )
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    await runtime.stop(room["id"])
    await runtime.resume(room["id"])
    await wait_until(lambda: _stale_for(runtime, room["id"], trigger["id"]))
    events = await runtime.db.get_events(room["id"])
    assert not any(
        event["event_type"] == "agent_message" and event["content"] == "pre-stop result"
        for event in events
    )


async def _stale_for(runtime: RoomRuntime, room_id: str, related_id: str) -> bool:
    return any(
        event["event_type"] == "stale_result" and event["related_event_id"] == related_id
        for event in await runtime.db.get_events(room_id)
    )


@pytest.mark.asyncio
async def test_legacy_room_migrates_to_initial_round_without_replacing_threads(tmp_path):
    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE rooms (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL,
          topic TEXT NOT NULL, discussion_id TEXT NOT NULL, created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL, max_turns INTEGER NOT NULL,
          max_consecutive_passes INTEGER NOT NULL, inactivity_seconds INTEGER NOT NULL,
          turn_count INTEGER NOT NULL DEFAULT 0, consecutive_passes INTEGER NOT NULL DEFAULT 0,
          metadata_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE agents (
          id TEXT PRIMARY KEY, room_id TEXT NOT NULL REFERENCES rooms(id), agent_key TEXT NOT NULL,
          name TEXT NOT NULL, thread_id TEXT, developer_instructions TEXT NOT NULL,
          status TEXT NOT NULL, last_error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          UNIQUE(room_id, agent_key), UNIQUE(thread_id)
        );
        CREATE TABLE events (
          id TEXT PRIMARY KEY, room_id TEXT NOT NULL REFERENCES rooms(id), discussion_id TEXT NOT NULL,
          created_at TEXT NOT NULL, event_type TEXT NOT NULL, source TEXT NOT NULL,
          destination TEXT NOT NULL, content TEXT NOT NULL, related_event_id TEXT,
          status TEXT NOT NULL, metadata_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE deliveries (
          id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id),
          agent_id TEXT NOT NULL REFERENCES agents(id), status TEXT NOT NULL,
          attempts INTEGER NOT NULL DEFAULT 0, queued_at TEXT NOT NULL,
          started_at TEXT, completed_at TEXT, error TEXT, UNIQUE(event_id, agent_id)
        );
        INSERT INTO rooms VALUES
          ('legacy-room','Legacy','stopped','Legacy topic','legacy-discussion',
           '2026-01-01T00:00:00+00:00','2026-01-01T01:00:00+00:00',40,3,900,2,1,'{}');
        INSERT INTO agents VALUES
          ('legacy-a','legacy-room','agent_a','A','thread-a','old A','idle',NULL,
           '2026-01-01T00:00:00+00:00','2026-01-01T01:00:00+00:00'),
          ('legacy-b','legacy-room','agent_b','B','thread-b','old B','idle',NULL,
           '2026-01-01T00:00:00+00:00','2026-01-01T01:00:00+00:00');
        INSERT INTO events VALUES
          ('legacy-event','legacy-room','legacy-discussion','2026-01-01T00:05:00+00:00',
           'agent_message','agent_a','agent_b','hello',NULL,'recorded','{}');
        """
    )
    connection.commit()
    connection.close()

    runtime = RoomRuntime(Database(path), FakeAgentAdapter(), tmp_path / "data")
    await runtime.initialize()
    try:
        snapshot = await runtime.db.snapshot("legacy-room")
        assert snapshot["active_round_id"] == "legacy-discussion"
        assert len(snapshot["rounds"]) == 1
        assert snapshot["rounds"][0]["prompt"] == "Legacy topic"
        assert snapshot["rounds"][0]["turn_count"] == 2
        assert {agent["thread_id"] for agent in snapshot["agents"]} == {"thread-a", "thread-b"}
        migrated_event = snapshot["rounds"][0]["events"][0]
        assert migrated_event["round_id"] == "legacy-discussion"
        assert migrated_event["event_class"] == "conversation"
        assert migrated_event["agent_readable"] is True
        async with runtime.db.connect() as db:
            columns = {
                row[1] for row in await db.execute_fetchall("PRAGMA table_info(deliveries)")
            }
        assert "runnable" in columns
    finally:
        await runtime.close()
