from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from codex_room.db import Database
from codex_room.models import (
    AGENT_C_INTEGRATOR_INSTRUCTIONS,
    AddAgentRequest,
    AgentDecision,
    AgentStatus,
    CreateRoomRequest,
    ObserverMessageRequest,
    Outcome,
    PrepareRoundRequest,
    RoomStatus,
    default_agent_instructions,
)
from codex_room.orchestrator import RoomRuntime

from .fakes import FakeAgentAdapter, wait_until


class FailingCAgentAdapter(FakeAgentAdapter):
    async def start_agent(self, agent, cwd):
        if agent["agent_key"] == "agent_c":
            raise RuntimeError("simulated C thread creation failure")
        return await super().start_agent(agent, cwd)


@pytest.fixture
async def runtime_factory(tmp_path):
    runtimes: list[RoomRuntime] = []

    async def make(adapter: FakeAgentAdapter, name: str = "three.db") -> RoomRuntime:
        runtime = RoomRuntime(Database(tmp_path / name), adapter, tmp_path / "data")
        await runtime.initialize()
        runtimes.append(runtime)
        return runtime

    yield make
    await asyncio.gather(*(runtime.close() for runtime in runtimes), return_exceptions=True)


@pytest.mark.asyncio
async def test_add_c_preserves_ab_and_enforces_newcomer_boundary(runtime_factory):
    old_public = "OLD_PUBLIC_CANARY_7f91"
    old_private = "OLD_PRIVATE_CANARY_6c22"
    old_overlay = "OLD_OVERLAY_CANARY_5a13"
    new_shared = "NEW_SHARED_EVENT_a83d"
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")], "agent_c": [(Outcome.PASS, "")]})
    runtime = await runtime_factory(adapter)
    created = await runtime.create_room(
        CreateRoomRequest(topic="earlier opening", starting_agent="agent_a", auto_start=False)
    )
    room_id = created["id"]
    prepared = await runtime.prepare_round(
        room_id,
        PrepareRoundRequest(
            prompt=old_public,
            starting_agent="agent_a",
            participant_private={"agent_a": old_private},
            participant_overlays={"agent_a": old_overlay},
        ),
    )
    await runtime.start_round(room_id, prepared["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)

    before = {agent["agent_key"]: agent["thread_id"] for agent in await runtime.db.get_agents(room_id)}
    max_before = max(event["sequence_no"] for event in await runtime.db.get_events(room_id))
    joined = await runtime.add_agent(room_id, AddAgentRequest())
    after = {agent["agent_key"]: agent["thread_id"] for agent in joined["agents"]}
    assert after["agent_a"] == before["agent_a"]
    assert after["agent_b"] == before["agent_b"]
    assert after["agent_c"] not in {before["agent_a"], before["agent_b"]}
    assert adapter.starts[-1][0] == "agent_c"
    c = await runtime.db.get_agent(room_id, "agent_c")
    assert c and c["developer_instructions"] == AGENT_C_INTEGRATOR_INSTRUCTIONS
    state = await runtime.db.get_round_agent_state(joined["active_round_id"], c["id"])
    assert state and state["context_consumed_at"]
    assert state["delivery_start_sequence"] == max_before
    await asyncio.sleep(0.08)
    assert not adapter.calls["agent_c"]

    event = await runtime.observer_message(
        room_id, ObserverMessageRequest(target="all", content=new_shared)
    )
    assert event["destination"] == "all"
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 1)
    prompt = adapter.calls["agent_c"][0]["prompt"]
    assert new_shared in prompt
    assert old_public not in prompt
    assert old_private not in prompt
    assert old_overlay not in prompt
    assert "earlier opening" not in prompt


@pytest.mark.asyncio
async def test_newcomer_without_a_delivery_does_not_block_existing_boundary(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.MESSAGE, "A opens a two-agent boundary")],
            "agent_b": [(Outcome.PASS, "")],
        },
        blocked_calls={"agent_b": {1}},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Freeze membership at the delivery boundary",
            starting_agent="agent_a",
            max_consecutive_passes=10,
        )
    )
    room_id = snapshot["id"]
    await wait_until(lambda: len(adapter.calls["agent_b"]) == 1)

    await runtime.add_agent(room_id, AddAgentRequest())
    assert not adapter.calls["agent_c"]
    adapter.release_call("agent_b", 1)

    await wait_until(lambda: _room_has_status(runtime, room_id, RoomStatus.FINISHED))
    events = await runtime.db.get_events(room_id)
    boundary = next(
        event for event in events if event["event_type"] == "reactions_settled"
    )["metadata"]["boundaries"][0]
    assert boundary["delivery_cohort"] == ["agent_b"]
    assert not adapter.calls["agent_c"]


def test_participant_map_values_enforce_prompt_ceiling() -> None:
    PrepareRoundRequest(
        prompt="ok",
        participant_private={"agent_c": "x" * 50_000},
        participant_overlays={"agent_c": "y" * 50_000},
    )
    for field in ("participant_private", "participant_overlays"):
        with pytest.raises(ValidationError, match="at most 50000 characters"):
            PrepareRoundRequest(prompt="too large", **{field: {"agent_c": "z" * 50_001}})


def test_fresh_ab_instruction_template_is_membership_generic() -> None:
    instructions = default_agent_instructions("Agent A", "Agent B")
    assert "Agent A, Agent B, and Agent C" in instructions
    assert "every participant has settled" in instructions
    assert "named Agent B" not in instructions


@pytest.mark.asyncio
async def test_failed_c_thread_start_compensates_without_touching_ab(runtime_factory):
    runtime = await runtime_factory(FailingCAgentAdapter())
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Remain two", starting_agent="agent_a", auto_start=False)
    )
    room_id = snapshot["id"]
    before = {item["agent_key"]: item["thread_id"] for item in snapshot["agents"]}
    with pytest.raises(RuntimeError, match="simulated C thread creation failure"):
        await runtime.add_agent(room_id, AddAgentRequest())
    after = {item["agent_key"]: item["thread_id"] for item in await runtime.db.get_agents(room_id)}
    assert after == before
    assert await runtime.db.get_agent(room_id, "agent_c") is None
    assert not any(
        event["event_type"] == "agent_added" for event in await runtime.db.get_events(room_id)
    )


@pytest.mark.asyncio
async def test_agent_c_compaction_keeps_its_thread_identity(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_c": [(Outcome.PASS, "")]},
        usages={
            "agent_c": [{
                "last": {"input_tokens": 77_520},
                "model_context_window": 258_400,
            }]
        },
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Compact C", include_agent_c=True, starting_agent="agent_c")
    )
    c_thread = next(item["thread_id"] for item in snapshot["agents"] if item["agent_key"] == "agent_c")

    async def checkpoint_exists() -> bool:
        return any(
            item["event_type"] == "context_checkpoint"
            and item["metadata"].get("agent") == "agent_c"
            for item in await runtime.db.get_events(snapshot["id"])
        )

    await wait_until(checkpoint_exists)
    assert adapter.compacted == ["agent_c"]
    current_c = await runtime.db.get_agent(snapshot["id"], "agent_c")
    assert current_c and current_c["thread_id"] == c_thread
    checkpoints = [
        item for item in await runtime.db.get_events(snapshot["id"])
        if item["event_type"] == "context_checkpoint"
    ]
    assert len(checkpoints) == 1
    assert checkpoints[0]["metadata"]["agent"] == "agent_c"


@pytest.mark.asyncio
async def test_fanout_does_not_cancel_c_inflight_and_c_consumes_queued_message(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.MESSAGE, "A while C runs"), (Outcome.PASS, "")],
            "agent_b": [(Outcome.PASS, ""), (Outcome.PASS, "")],
            "agent_c": [(Outcome.MESSAGE, "C current result"), (Outcome.PASS, "")],
        },
        blocked_calls={"agent_c": {1}},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="C starts long work",
            include_agent_c=True,
            starting_agent="agent_c",
            max_consecutive_passes=10,
        )
    )
    room_id = snapshot["id"]
    await wait_until(
        lambda: _agents_have_statuses(runtime, room_id, {"agent_c": AgentStatus.RUNNING})
    )
    await runtime.observer_message(
        room_id, ObserverMessageRequest(target="agent_a", content="A should contribute")
    )
    await wait_until(lambda: len(adapter.completed_calls["agent_a"]) == 1)
    assert not adapter.interrupted
    adapter.release_call("agent_c", 1)
    await wait_until(lambda: len(adapter.completed_calls["agent_c"]) >= 2)
    assert "A while C runs" in adapter.calls["agent_c"][1]["prompt"]
    events = await runtime.db.get_events(room_id)
    assert any(
        item["event_type"] == "agent_message" and item["content"] == "C current result"
        for item in events
    )


@pytest.mark.asyncio
async def test_message_fans_out_to_every_other_member(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.MESSAGE, "A contribution")],
            "agent_b": [(Outcome.PASS, "")],
            "agent_c": [(Outcome.PASS, "")],
        }
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Three-way routing", include_agent_c=True, starting_agent="agent_a")
    )
    await wait_until(lambda: len(adapter.calls["agent_b"]) == 1 and len(adapter.calls["agent_c"]) == 1)
    assert "A contribution" in adapter.calls["agent_b"][0]["prompt"]
    assert "A contribution" in adapter.calls["agent_c"][0]["prompt"]
    event = next(
        item for item in await runtime.db.get_events(snapshot["id"])
        if item["event_type"] == "agent_message"
    )
    assert event["destination"] == "all"
    assert {item["agent_key"] for item in event["deliveries"]} == {"agent_b", "agent_c"}
    assert all(item["runnable"] for item in event["deliveries"])


@pytest.mark.asyncio
async def test_targeted_agent_message_is_public_but_wakes_only_selected_peer(
    runtime_factory,
):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [],
            "agent_c": [(Outcome.PASS, "")],
            "agent_b": [(Outcome.PASS, "")],
        }
    )
    adapter.decisions["agent_a"].append(
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="A public finding for C to act on",
            invoke_targets=["agent_c"],
        )
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Selective routing",
            include_agent_c=True,
            starting_agent="agent_a",
            max_consecutive_passes=10,
        )
    )
    room_id = snapshot["id"]

    await wait_until(lambda: len(adapter.calls["agent_c"]) == 1)
    await wait_until(lambda: _room_has_status(runtime, room_id, RoomStatus.FINISHED))
    assert not adapter.calls["agent_b"]

    message = next(
        event for event in await runtime.db.get_events(room_id)
        if event["event_type"] == "agent_message"
    )
    deliveries = {item["agent_key"]: item for item in message["deliveries"]}
    assert deliveries["agent_c"]["runnable"] is True
    assert deliveries["agent_c"]["status"] == "delivered"
    assert deliveries["agent_b"]["runnable"] is False
    assert deliveries["agent_b"]["status"] == "pending"
    assert message["metadata"]["runnable_recipients"] == ["agent_c"]
    assert message["metadata"]["readable_recipients"] == ["agent_b", "agent_c"]
    assert message["metadata"]["legacy_fanout_invocations_avoided"] == 1

    private_trigger = await runtime.observer_message(
        room_id,
        ObserverMessageRequest(target="agent_b", content="B now has legitimate work"),
    )
    await wait_until(lambda: len(adapter.calls["agent_b"]) == 1)
    prompt = adapter.calls["agent_b"][0]["prompt"]
    assert prompt.index("A public finding for C to act on") < prompt.index(
        "B now has legitimate work"
    )
    await asyncio.sleep(0.08)
    assert len(adapter.calls["agent_b"]) == 1
    assert len(adapter.calls["agent_a"]) == 1
    assert len(adapter.calls["agent_c"]) == 1
    stored_private = next(
        event for event in await runtime.db.get_events(room_id)
        if event["id"] == private_trigger["id"]
    )
    assert stored_private["visibility"] == "private"
    assert [item["agent_key"] for item in stored_private["deliveries"]] == ["agent_b"]


@pytest.mark.asyncio
async def test_passive_delivery_cannot_claim_until_later_runnable_trigger(runtime_factory):
    runtime = await runtime_factory(FakeAgentAdapter())
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Durable passive backlog",
            starting_agent="agent_a",
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    round_id = snapshot["active_round_id"]
    passive = await runtime.db.create_event(
        room_id,
        "agent_message",
        "agent_b",
        "all",
        "passive first",
        deliver_to=("agent_a",),
        runnable_to=(),
        discussion_id=round_id,
        round_id=round_id,
    )
    await runtime.db.start_round(room_id, round_id)
    assert await runtime.db.claim_next_batch(room_id, "agent_a") is None

    trigger = await runtime.db.create_event(
        room_id,
        "observer_message",
        "observer",
        "agent_a",
        "trigger second",
        metadata={"private": True},
        deliver_to=("agent_a",),
        discussion_id=round_id,
        round_id=round_id,
    )
    later_passive = await runtime.db.create_event(
        room_id,
        "agent_message",
        "agent_b",
        "all",
        "passive after trigger",
        deliver_to=("agent_a",),
        runnable_to=(),
        discussion_id=round_id,
        round_id=round_id,
    )
    batch = await runtime.db.claim_next_batch(room_id, "agent_a")
    assert batch is not None
    assert [event["id"] for event in batch["events"]] == [passive["id"], trigger["id"]]
    assert batch["triggering_event_ids"] == [trigger["id"]]
    assert batch["passive_event_ids"] == [passive["id"]]
    stored_later = await runtime.db.get_events(room_id)
    later_delivery = next(
        event for event in stored_later if event["id"] == later_passive["id"]
    )["deliveries"][0]
    assert later_delivery["status"] == "pending"
    assert later_delivery["runnable"] is False


@pytest.mark.asyncio
async def test_passive_and_runnable_state_survives_restart(tmp_path):
    path = tmp_path / "selective-restart.db"
    first = RoomRuntime(Database(path), FakeAgentAdapter(), tmp_path / "first-data")
    await first.initialize()
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Restart routing",
            starting_agent="agent_a",
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    round_id = snapshot["active_round_id"]
    await first.db.create_event(
        room_id,
        "agent_message",
        "agent_b",
        "all",
        "persisted passive",
        deliver_to=("agent_a",),
        runnable_to=(),
        discussion_id=round_id,
        round_id=round_id,
    )
    await first.db.create_event(
        room_id,
        "observer_message",
        "observer",
        "agent_a",
        "persisted trigger",
        metadata={"private": True},
        deliver_to=("agent_a",),
        discussion_id=round_id,
        round_id=round_id,
    )
    await first.db.start_round(room_id, round_id)
    await first.close()

    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    restarted = RoomRuntime(Database(path), adapter, tmp_path / "second-data")
    await restarted.initialize()
    try:
        await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
        prompt = adapter.calls["agent_a"][0]["prompt"]
        assert prompt.index("persisted passive") < prompt.index("persisted trigger")
    finally:
        await restarted.close()


def test_invoke_targets_validation_and_room_membership() -> None:
    with pytest.raises(ValidationError, match="cannot be empty"):
        AgentDecision(outcome=Outcome.MESSAGE, message="bad", invoke_targets=[])
    with pytest.raises(ValidationError, match="cannot contain duplicates"):
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="bad",
            invoke_targets=["agent_b", "agent_b"],
        )
    with pytest.raises(ValidationError, match="cannot be combined"):
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="bad",
            invoke_targets=["all", "agent_b"],
        )
    with pytest.raises(ValidationError, match="valid only for MESSAGE"):
        AgentDecision(outcome=Outcome.PASS, invoke_targets=["agent_b"])

    decision = AgentDecision(
        outcome=Outcome.MESSAGE,
        message="C is unavailable in this Room",
        invoke_targets=["agent_c"],
    )
    with pytest.raises(ValueError, match="unavailable or unauthorized"):
        RoomRuntime._resolve_invoke_targets(
            decision,
            "agent_a",
            [{"agent_key": "agent_a"}, {"agent_key": "agent_b"}],
        )


@pytest.mark.asyncio
async def test_future_round_configuration_is_membership_keyed(runtime_factory):
    adapter = FakeAgentAdapter({"agent_c": [(Outcome.PASS, "")]})
    runtime = await runtime_factory(adapter)
    initial = await runtime.create_room(
        CreateRoomRequest(topic="Two-member history", starting_agent="agent_a", auto_start=False)
    )
    await runtime.add_agent(initial["id"], AddAgentRequest())
    before_new_round = await runtime.db.snapshot(initial["id"])
    assert "agent_c" not in before_new_round["active_round"]["effective_agent_configuration"]
    assert "agent_c" not in before_new_round["active_round"]["private_initialization"]

    prepared = await runtime.prepare_round(
        initial["id"],
        PrepareRoundRequest(
            prompt="Fresh round",
            starting_agent="agent_c",
            participant_private={"agent_c": "C_ONLY_FUTURE"},
            participant_overlays={"agent_c": "C_OVERLAY_FUTURE"},
        ),
    )
    await runtime.start_round(initial["id"], prepared["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 1)
    prompt = adapter.calls["agent_c"][0]["prompt"]
    assert "Fresh round" in prompt
    assert "C_ONLY_FUTURE" in prompt
    assert "C_OVERLAY_FUTURE" in prompt
    refreshed = await runtime.db.snapshot(initial["id"])
    old_round = refreshed["rounds"][0]
    assert "agent_c" not in old_round["effective_agent_configuration"]
    assert "agent_c" not in old_round["private_initialization"]


@pytest.mark.asyncio
async def test_three_agent_finish_waits_for_running_peer_and_reopens(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.FINISH, "A done"), (Outcome.PASS, "")],
            "agent_b": [(Outcome.FINISH, "B done"), (Outcome.PASS, "")],
            "agent_c": [(Outcome.FINISH, "C done"), (Outcome.PASS, "")],
        },
        blocked_calls={"agent_c": {1}},
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Settle together", include_agent_c=True, starting_agent="either")
    )
    room_id = snapshot["id"]
    original_ids = {item["agent_key"]: item["thread_id"] for item in snapshot["agents"]}
    await wait_until(
        lambda: _agents_have_statuses(
            runtime,
            room_id,
            {"agent_a": AgentStatus.READY_TO_FINISH, "agent_b": AgentStatus.READY_TO_FINISH,
             "agent_c": AgentStatus.RUNNING},
        )
    )
    assert (await runtime.db.get_room(room_id))["status"] == RoomStatus.RUNNING
    adapter.release_call("agent_c", 1)
    await wait_until(lambda: _room_has_status(runtime, room_id, RoomStatus.FINISHED))

    await runtime.observer_message(
        room_id, ObserverMessageRequest(target="both", content="A genuinely new shared question")
    )
    await wait_until(
        lambda: all(len(adapter.calls[key]) >= 2 for key in ("agent_a", "agent_b", "agent_c"))
    )
    current_ids = {
        item["agent_key"]: item["thread_id"] for item in await runtime.db.get_agents(room_id)
    }
    assert current_ids == original_ids


async def _room_has_status(runtime: RoomRuntime, room_id: str, status: RoomStatus) -> bool:
    room = await runtime.db.get_room(room_id)
    return bool(room and room["status"] == status)


async def _agents_have_statuses(
    runtime: RoomRuntime, room_id: str, expected: dict[str, AgentStatus]
) -> bool:
    agents = {item["agent_key"]: item["status"] for item in await runtime.db.get_agents(room_id)}
    return all(agents.get(key) == value for key, value in expected.items())
