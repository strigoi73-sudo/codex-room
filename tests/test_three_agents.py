from __future__ import annotations

import asyncio
import hashlib

import pytest
from pydantic import ValidationError

import codex_room.db as db_module
from codex_room.db import Database
from codex_room.models import (
    AddAgentRequest,
    AgentDecision,
    AgentStatus,
    CreateRoomRequest,
    ObserverMessageRequest,
    Outcome,
    PrepareRoundRequest,
    RoomStatus,
)
from codex_room.personalities import (
    AGENT_A_DEFAULT_PERSONALITY,
    AGENT_B_DEFAULT_PERSONALITY,
    AGENT_C_DEFAULT_PERSONALITY,
    AGENT_C_INTEGRATOR_INSTRUCTIONS,
    AGENT_C_STRUCTURAL_INSTRUCTIONS,
    ROOM_PROTOCOL_INSTRUCTIONS,
    default_agent_instructions,
)
from codex_room.orchestrator import RoomRuntime

from .fakes import FakeAgentAdapter, wait_until


class FailingCAgentAdapter(FakeAgentAdapter):
    def __init__(self):
        super().__init__()
        self._c_start_count = 0

    async def start_agent(self, agent, cwd):
        if agent["agent_key"] == "agent_c":
            self._c_start_count += 1
            if self._c_start_count > 1:
                raise RuntimeError("simulated C thread creation failure")
        return await super().start_agent(agent, cwd)


async def _make_legacy_pair(runtime: RoomRuntime, room_id: str) -> None:
    """Simulate a persisted pre-D-020 A/B Room before any new Round work starts."""
    c = await runtime.db.get_agent(room_id, "agent_c")
    assert c is not None
    await runtime.db.remove_agent(room_id, "agent_c")
    if c.get("thread_id"):
        await runtime.adapter.archive_thread(c["thread_id"])


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
    await _make_legacy_pair(runtime, room_id)
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
    # The active legacy worker may append another legitimate pre-join event
    # between the observer's snapshot above and reserve_agent_c() acquiring its
    # transaction. C's actual join watermark must therefore be at or after the
    # last sequence observed before the join request, not equal to that stale read.
    assert state["delivery_start_sequence"] >= max_before
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
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    await _make_legacy_pair(runtime, room_id)
    await runtime.start_round(room_id, snapshot["active_round_id"])
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
    assert "every engaged participant has settled" in instructions
    assert "named Agent B" not in instructions


@pytest.mark.asyncio
async def test_personality_overrides_replace_defaults_but_preserve_protected_layers(
    runtime_factory,
):
    overrides = {
        "agent_a": "A_ROOM_PERSONALITY_CANARY",
        "agent_b": "B_ROOM_PERSONALITY_CANARY",
        "agent_c": "C_ROOM_PERSONALITY_CANARY",
    }
    defaults = {
        "agent_a": AGENT_A_DEFAULT_PERSONALITY,
        "agent_b": AGENT_B_DEFAULT_PERSONALITY,
        "agent_c": AGENT_C_DEFAULT_PERSONALITY,
    }
    runtime = await runtime_factory(FakeAgentAdapter())
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="personality layer composition",
            auto_start=False,
            agent_a_instructions=overrides["agent_a"],
            agent_b_instructions=overrides["agent_b"],
            agent_c_instructions=overrides["agent_c"],
        )
    )
    agents = {agent["agent_key"]: agent for agent in snapshot["agents"]}

    for key, agent in agents.items():
        effective = agent["developer_instructions"]
        assert agent["profile_snapshot"] == defaults[key]
        assert agent["room_override"] == overrides[key]
        assert overrides[key] in effective
        assert "PERSONALITY\n" in effective
        assert "INSTITUTIONAL IDENTITY AND PEER RULES" in effective
        assert "ROOM PROTOCOL" in effective
        assert ROOM_PROTOCOL_INSTRUCTIONS in effective
        assert "ROOM-SPECIFIC OVERRIDE" not in effective

    assert AGENT_C_STRUCTURAL_INSTRUCTIONS not in agents["agent_a"]["developer_instructions"]
    assert AGENT_C_STRUCTURAL_INSTRUCTIONS not in agents["agent_b"]["developer_instructions"]
    assert AGENT_C_STRUCTURAL_INSTRUCTIONS in agents["agent_c"]["developer_instructions"]
    assert "Every additional peer invocation must be expected to earn its cognitive and token cost" in agents["agent_c"]["developer_instructions"]
    assert "must give them meaningfully differentiated cognitive responsibilities" in agents["agent_c"]["developer_instructions"]
    assert "temporary task-specific working postures" in agents["agent_c"]["developer_instructions"]
    assert "temporary roles/personas" in agents["agent_c"]["developer_instructions"]
    assert "do not authorize C to dictate a conclusion" in agents["agent_c"]["developer_instructions"]
    for key in ("agent_a", "agent_b", "agent_c"):
        assert "Invocation requests cognition, not visibility" in agents[key]["developer_instructions"]
        assert "ordinary cross-reading does not require invocation" in agents[key]["developer_instructions"]
    assert "the first return is only a partial result" in agents["agent_c"]["developer_instructions"]
    assert "Wait until every requested contribution has returned" in agents["agent_c"]["developer_instructions"]


@pytest.mark.asyncio
async def test_default_profiles_are_neutral_and_not_composed_when_not_overridden(
    runtime_factory,
):
    defaults = {
        "agent_a": AGENT_A_DEFAULT_PERSONALITY,
        "agent_b": AGENT_B_DEFAULT_PERSONALITY,
        "agent_c": AGENT_C_DEFAULT_PERSONALITY,
    }
    runtime = await runtime_factory(FakeAgentAdapter(), "neutral-default-profiles.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="neutral defaults", auto_start=False)
    )
    agents = {agent["agent_key"]: agent for agent in snapshot["agents"]}
    assert set(defaults.values()) == {""}
    for key, agent in agents.items():
        assert agent["profile_snapshot"] == ""
        assert agent["room_override"] is None
        assert "PERSONALITY\n" not in agent["developer_instructions"]
        assert "INSTITUTIONAL IDENTITY AND PEER RULES" in agent["developer_instructions"]
        assert "ROOM PROTOCOL" in agent["developer_instructions"]

    assert AGENT_C_STRUCTURAL_INSTRUCTIONS not in agents["agent_a"]["developer_instructions"]
    assert AGENT_C_STRUCTURAL_INSTRUCTIONS not in agents["agent_b"]["developer_instructions"]
    assert AGENT_C_STRUCTURAL_INSTRUCTIONS in agents["agent_c"]["developer_instructions"]


def test_standard_default_profiles_are_identically_neutral() -> None:
    defaults = {
        "agent_a": AGENT_A_DEFAULT_PERSONALITY,
        "agent_b": AGENT_B_DEFAULT_PERSONALITY,
        "agent_c": AGENT_C_DEFAULT_PERSONALITY,
    }
    assert defaults == {"agent_a": "", "agent_b": "", "agent_c": ""}


def test_room_protocol_makes_invocation_cognition_not_visibility_for_all_agents() -> None:
    instructions = {
        key: default_agent_instructions(name, "unused")
        for key, name in {
            "agent_a": "Agent A",
            "agent_b": "Agent B",
            "agent_c": "Agent C",
        }.items()
    }

    for text in instructions.values():
        assert "Invocation requests cognition, not visibility" in text
        assert "do not invoke a participant merely so they can see" in text
        assert "If no additional peer cognition is needed, set invoke_targets to `[]`" in text
        assert "normally return the result to C without invoking the other delegated peer" in text
        assert "ordinary cross-reading does not require invocation" in text


def test_c_structural_role_requires_economical_differentiated_dual_peer_delegation() -> None:
    c_instructions = default_agent_instructions("Agent C", "Agent A")
    a_instructions = default_agent_instructions("Agent A", "Agent C")
    b_instructions = default_agent_instructions("Agent B", "Agent C")

    assert "Every additional peer invocation must be expected to earn its cognitive and token cost" in c_instructions
    assert "Use the fewest peers that can add sufficient value" in c_instructions
    assert "If C invokes both A and B in the same delegation" in c_instructions
    assert "must give them meaningfully differentiated cognitive responsibilities" in c_instructions
    assert "Do not satisfy this rule with cosmetic labels" in c_instructions
    assert "substantially the same analysis in substantially the same way" in c_instructions
    assert "When independent verification is valuable, differentiate how independence is obtained" in c_instructions
    assert "temporary task-specific working postures" in c_instructions
    assert "temporary roles/personas" in c_instructions
    assert "not according to fixed A/B specialties" in c_instructions
    assert "They do not change a participant's persistent identity, saved profile" in c_instructions
    assert "they do not authorize C to dictate a conclusion" in c_instructions
    assert "may challenge the framing" in c_instructions

    assert "Every additional peer invocation must be expected to earn its cognitive and token cost" not in a_instructions
    assert "Every additional peer invocation must be expected to earn its cognitive and token cost" not in b_instructions
    assert "must give them meaningfully differentiated cognitive responsibilities" not in a_instructions
    assert "must give them meaningfully differentiated cognitive responsibilities" not in b_instructions


def test_v3_default_personality_hashes_remain_exact_migration_anchors() -> None:
    assert db_module._V3_DEFAULT_PERSONALITY_SHA256 == {
        "agent_a": "678d7c48cd652e9237fcfeadd8da20d3595aa708a79deb35cd531263d96e2477",
        "agent_b": "a0df11ad77c5849cfa39cadfc6efe0d4b302cac587fa5e2f60ab13db6327bd17",
        "agent_c": "5f7452ee2a40a9ed432d1cacbd404ff836a9539260d1ea1ac01035acd99f0fa9",
    }


def test_v4_default_personality_hashes_remain_exact_migration_anchors() -> None:
    assert db_module._V4_DEFAULT_PERSONALITY_SHA256 == {
        "agent_a": "ebe03e6456df6eb2ccbf4e82bdeedaf756a4075712266ba16b99201400583d11",
        "agent_b": "e52156bc3d24a9e39c2a04458edc15cd7fd71ad3164ef7de1d17fa0959488776",
        "agent_c": "cbea4f0090d33aa22079f9c6692569dac0193bd633e6ed61839f9019020d8706",
    }


def test_v5_default_personality_hashes_remain_exact_migration_anchors() -> None:
    assert db_module._V5_DEFAULT_PERSONALITY_SHA256 == {
        "agent_a": "49225250cd1fa14c1bb58e654cf4ede6e55dd7ff969013341552db5ee45a705d",
        "agent_b": "c1449f7edbb9f0e509a10ca4c5f4ff6146f285de242ea7a9fb195c527c810dd1",
        "agent_c": "59a9113aa443a7c0dbda65444c1e61039e79f27652b8be1ac53d9aad57fa3722",
    }


def test_v6_2_default_personality_hashes_remain_exact_migration_anchors() -> None:
    assert db_module._V6_2_DEFAULT_PERSONALITY_SHA256 == {
        "agent_a": "75719cad8fcfe3ea0cbc7c7f6fd903769aad1202732b0fae6f42b818b2616c42",
        "agent_b": "9b136b537a9c8d2dab39fed3f4aef5f68b33c7a3cdca22e9f961c227bd23cdf3",
        "agent_c": "78dda32bf9ffbf27818ea858f1c4395891b5357aa85c6ba11edd15c7ac60935d",
    }


def test_v7_default_personality_hashes_remain_exact_migration_anchors() -> None:
    assert db_module._V7_DEFAULT_PERSONALITY_SHA256 == {
        "agent_a": "5462686efba369af926bee543fdb27b53145fce9c02ad581eefca26057acc503",
        "agent_b": "ca4f58aee7040dccdbfecae94088d2ae88e1eb0366b7a20f234f7a27e0039c34",
        "agent_c": "1c19a8d4d39a7d148c29725f55ee0f8239c45503090f2eb77a143c3df88b1afa",
    }


def test_e056_default_personality_hashes_remain_exact_migration_anchors() -> None:
    assert db_module._E056_DEFAULT_PERSONALITY_SHA256 == {
        "agent_a": "5b11450825c124cd423bc99ad8ff8cffd94a89eec0309750b5aa3cba392db8d5",
        "agent_b": "9532a31035d3c230d44e709d8e0c3ad4ebc94fc6454bfa3eff3c487500ca4ded",
        "agent_c": "8b689f1894125f106023958d16385c7656287cdfb57b6d3f476406ed164e3993",
    }


@pytest.mark.asyncio
async def test_exact_e056_defaults_migrate_to_neutral_without_overwriting_custom_text(
    tmp_path, monkeypatch
):
    old_defaults = {
        "agent_a": "Exact E-056 A migration fixture.",
        "agent_b": "Exact E-056 B migration fixture.",
        "agent_c": "Exact E-056 C migration fixture.",
    }
    monkeypatch.setattr(
        db_module,
        "_E056_DEFAULT_PERSONALITY_SHA256",
        {
            slot: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for slot, text in old_defaults.items()
        },
    )

    database = Database(tmp_path / "neutral-default-migration.db")
    await database.initialize()
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Agent B default",
        old_defaults["agent_b"],
        "Agent C default",
        old_defaults["agent_c"],
    )
    await database.initialize()
    migrated = await database.get_default_profiles()

    assert migrated["agent_a"]["developer_instructions"] == ""
    assert migrated["agent_b"]["developer_instructions"] == ""
    assert migrated["agent_c"]["developer_instructions"] == ""

    custom_b = old_defaults["agent_b"] + "\nCustom principal preference."
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Custom B",
        custom_b,
        "Agent C default",
        old_defaults["agent_c"],
    )
    await database.initialize()
    remigrated = await database.get_default_profiles()

    assert remigrated["agent_a"]["developer_instructions"] == ""
    assert remigrated["agent_b"]["developer_instructions"] == custom_b
    assert remigrated["agent_b"]["name"] == "Custom B"
    assert remigrated["agent_c"]["developer_instructions"] == ""


@pytest.mark.asyncio
async def test_exact_v7_defaults_migrate_without_overwriting_custom_text(
    tmp_path, monkeypatch
):
    old_defaults = {
        "agent_a": "Exact V7 A migration fixture.",
        "agent_b": "Exact V7 B migration fixture.",
        "agent_c": "Exact V7 C migration fixture.",
    }
    monkeypatch.setattr(
        db_module,
        "_V7_DEFAULT_PERSONALITY_SHA256",
        {
            slot: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for slot, text in old_defaults.items()
        },
    )

    database = Database(tmp_path / "personality-temperament-migration.db")
    await database.initialize()
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Agent B default",
        old_defaults["agent_b"],
        "Agent C default",
        old_defaults["agent_c"],
    )
    await database.initialize()
    migrated = await database.get_default_profiles()

    assert migrated["agent_a"]["developer_instructions"] == AGENT_A_DEFAULT_PERSONALITY
    assert migrated["agent_b"]["developer_instructions"] == AGENT_B_DEFAULT_PERSONALITY
    assert migrated["agent_c"]["developer_instructions"] == AGENT_C_DEFAULT_PERSONALITY

    custom_c = old_defaults["agent_c"] + "\nCustom principal preference."
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Agent B default",
        old_defaults["agent_b"],
        "Custom C",
        custom_c,
    )
    await database.initialize()
    remigrated = await database.get_default_profiles()

    assert remigrated["agent_a"]["developer_instructions"] == AGENT_A_DEFAULT_PERSONALITY
    assert remigrated["agent_b"]["developer_instructions"] == AGENT_B_DEFAULT_PERSONALITY
    assert remigrated["agent_c"]["developer_instructions"] == custom_c
    assert remigrated["agent_c"]["name"] == "Custom C"


@pytest.mark.asyncio
async def test_exact_v6_2_defaults_migrate_without_overwriting_custom_text(
    tmp_path, monkeypatch
):
    old_defaults = {
        "agent_a": "Exact V6.2 A migration fixture.",
        "agent_b": "Exact V6.2 B migration fixture.",
        "agent_c": "Exact V6.2 C migration fixture.",
    }
    monkeypatch.setattr(
        db_module,
        "_V6_2_DEFAULT_PERSONALITY_SHA256",
        {
            slot: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for slot, text in old_defaults.items()
        },
    )

    database = Database(tmp_path / "personality-v7-migration.db")
    await database.initialize()
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Agent B default",
        old_defaults["agent_b"],
        "Agent C default",
        old_defaults["agent_c"],
    )
    await database.initialize()
    migrated = await database.get_default_profiles()

    assert migrated["agent_a"]["developer_instructions"] == AGENT_A_DEFAULT_PERSONALITY
    assert migrated["agent_b"]["developer_instructions"] == AGENT_B_DEFAULT_PERSONALITY
    assert migrated["agent_c"]["developer_instructions"] == AGENT_C_DEFAULT_PERSONALITY

    custom_b = old_defaults["agent_b"] + "\nCustom principal preference."
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Custom B",
        custom_b,
        "Agent C default",
        old_defaults["agent_c"],
    )
    await database.initialize()
    remigrated = await database.get_default_profiles()

    assert remigrated["agent_a"]["developer_instructions"] == AGENT_A_DEFAULT_PERSONALITY
    assert remigrated["agent_b"]["developer_instructions"] == custom_b
    assert remigrated["agent_b"]["name"] == "Custom B"
    assert remigrated["agent_c"]["developer_instructions"] == AGENT_C_DEFAULT_PERSONALITY


@pytest.mark.asyncio
async def test_exact_v5_defaults_migrate_without_overwriting_custom_text(
    tmp_path, monkeypatch
):
    old_defaults = {
        "agent_a": "Exact V5 A migration fixture.",
        "agent_b": "Exact V5 B migration fixture.",
        "agent_c": "Exact V5 C migration fixture.",
    }
    monkeypatch.setattr(
        db_module,
        "_V5_DEFAULT_PERSONALITY_SHA256",
        {
            slot: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for slot, text in old_defaults.items()
        },
    )

    database = Database(tmp_path / "personality-v6-2-migration.db")
    await database.initialize()
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Agent B default",
        old_defaults["agent_b"],
        "Agent C default",
        old_defaults["agent_c"],
    )
    await database.initialize()
    migrated = await database.get_default_profiles()

    assert migrated["agent_a"]["developer_instructions"] == AGENT_A_DEFAULT_PERSONALITY
    assert migrated["agent_b"]["developer_instructions"] == AGENT_B_DEFAULT_PERSONALITY
    assert migrated["agent_c"]["developer_instructions"] == AGENT_C_DEFAULT_PERSONALITY

    custom_a = old_defaults["agent_a"] + "\nCustom principal preference."
    await database.update_default_profiles(
        "Custom A",
        custom_a,
        "Agent B default",
        old_defaults["agent_b"],
        "Agent C default",
        old_defaults["agent_c"],
    )
    await database.initialize()
    remigrated = await database.get_default_profiles()

    assert remigrated["agent_a"]["developer_instructions"] == custom_a
    assert remigrated["agent_a"]["name"] == "Custom A"
    assert remigrated["agent_b"]["developer_instructions"] == AGENT_B_DEFAULT_PERSONALITY
    assert remigrated["agent_c"]["developer_instructions"] == AGENT_C_DEFAULT_PERSONALITY


@pytest.mark.asyncio
async def test_exact_v4_defaults_migrate_without_overwriting_custom_text(
    tmp_path, monkeypatch
):
    old_defaults = {
        "agent_a": "Exact V4 A migration fixture.",
        "agent_b": "Exact V4 B migration fixture.",
        "agent_c": "Exact V4 C migration fixture.",
    }
    monkeypatch.setattr(
        db_module,
        "_V4_DEFAULT_PERSONALITY_SHA256",
        {
            slot: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for slot, text in old_defaults.items()
        },
    )

    database = Database(tmp_path / "personality-v5-migration.db")
    await database.initialize()
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Agent B default",
        old_defaults["agent_b"],
        "Agent C default",
        old_defaults["agent_c"],
    )
    await database.initialize()
    migrated = await database.get_default_profiles()

    assert migrated["agent_a"]["developer_instructions"] == AGENT_A_DEFAULT_PERSONALITY
    assert migrated["agent_b"]["developer_instructions"] == AGENT_B_DEFAULT_PERSONALITY
    assert migrated["agent_c"]["developer_instructions"] == AGENT_C_DEFAULT_PERSONALITY

    custom_c = old_defaults["agent_c"] + "\nCustom principal preference."
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Agent B default",
        old_defaults["agent_b"],
        "Custom C",
        custom_c,
    )
    await database.initialize()
    remigrated = await database.get_default_profiles()

    assert remigrated["agent_a"]["developer_instructions"] == AGENT_A_DEFAULT_PERSONALITY
    assert remigrated["agent_b"]["developer_instructions"] == AGENT_B_DEFAULT_PERSONALITY
    assert remigrated["agent_c"]["developer_instructions"] == custom_c
    assert remigrated["agent_c"]["name"] == "Custom C"


@pytest.mark.asyncio
async def test_exact_v3_defaults_migrate_without_overwriting_custom_text(
    tmp_path, monkeypatch
):
    old_defaults = {
        "agent_a": "Exact V3 A migration fixture.",
        "agent_b": "Exact V3 B migration fixture.",
        "agent_c": "Exact V3 C migration fixture.",
    }
    monkeypatch.setattr(
        db_module,
        "_V3_DEFAULT_PERSONALITY_SHA256",
        {
            slot: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for slot, text in old_defaults.items()
        },
    )

    database = Database(tmp_path / "personality-v4-migration.db")
    await database.initialize()
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Agent B default",
        old_defaults["agent_b"],
        "Agent C default",
        old_defaults["agent_c"],
    )
    await database.initialize()
    migrated = await database.get_default_profiles()

    assert migrated["agent_a"]["developer_instructions"] == AGENT_A_DEFAULT_PERSONALITY
    assert migrated["agent_b"]["developer_instructions"] == AGENT_B_DEFAULT_PERSONALITY
    assert migrated["agent_c"]["developer_instructions"] == AGENT_C_DEFAULT_PERSONALITY

    custom_b = old_defaults["agent_b"] + "\nCustom principal preference."
    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Custom B",
        custom_b,
        "Agent C default",
        old_defaults["agent_c"],
    )
    await database.initialize()
    remigrated = await database.get_default_profiles()

    assert remigrated["agent_a"]["developer_instructions"] == AGENT_A_DEFAULT_PERSONALITY
    assert remigrated["agent_b"]["developer_instructions"] == custom_b
    assert remigrated["agent_b"]["name"] == "Custom B"
    assert remigrated["agent_c"]["developer_instructions"] == AGENT_C_DEFAULT_PERSONALITY


@pytest.mark.asyncio
async def test_exact_role_derived_defaults_migrate_without_overwriting_custom_text(tmp_path):
    database = Database(tmp_path / "personality-redesign-migration.db")
    await database.initialize()
    old_defaults = {
        "agent_a": "Agent A - The Implementer\n\nYou are backend-oriented and rigorous. You tend to turn agreed designs into small, auditable implementations; preserve invariants and compatibility; test failure paths; and publish exact evidence. This is a working tendency, not special authority or rigid ownership. Remain capable of investigation, critique, review, synthesis, and changing your mind. When delegated work produces a substantive result, communicate that result with MESSAGE rather than relying on PASS or FINISH to carry it; when C needs to integrate the result, normally invoke Agent C.",
        "agent_b": "Agent B - The Verifier\n\nYou are an independent adversarial verifier. You tend to challenge assumptions, reproduce claims from authoritative evidence, probe boundary and failure cases, and distinguish demonstrated guarantees from plausible stories. This is a working tendency, not special authority or rigid ownership. Remain capable of implementation, design, synthesis, and changing your mind. When delegated work produces a substantive result, communicate that result with MESSAGE rather than relying on PASS or FINISH to carry it; when C needs to integrate the result, normally invoke Agent C.",
        "agent_c": "Agent C — The Integrator\n\nYou tend to see systems rather than isolated pieces. You naturally look for relationships between ideas, tasks, people, tools, and processes. When others are focused on solving individual problems, you often ask how those solutions fit together, whether they duplicate something that already exists, and whether the overall arrangement is becoming more complicated than it needs to be.\n\nYou value simplicity, but not simplicity for its own sake. You are willing to accept complexity when the problem genuinely requires it. Your instinct is to ask whether each additional mechanism, rule, tool, or procedure is earning its cost.\n\nYou are pragmatic and somewhat skeptical of institutional inertia. Existing practices deserve consideration because they may embody lessons from past experience, but their existence alone does not make them correct. You are comfortable asking: Why do we do it this way? What problem was this originally meant to solve? Does that problem still exist? Are two mechanisms doing essentially the same job? Could this be accomplished with fewer moving parts? What would happen if we removed this entirely?\n\nThis does not make you reflexively contrarian. If an existing system works well and has a clear justification, you are willing to adopt it. Do not invent objections simply to differentiate yourself.\n\nYou prefer to understand the broader objective before optimizing a component. You tend to notice dependencies, coordination bottlenecks, redundant effort, mismatched assumptions, and places where individually reasonable decisions create an awkward overall system.\n\nIn group discussion, you often synthesize competing proposals rather than simply choosing between them. You may identify that two apparently different ideas address different parts of the same underlying problem, or that a disagreement results from participants optimizing for different criteria.\n\nYou are willing to disagree firmly when you believe the group is overengineering a problem, preserving an obsolete practice, or mistaking accumulated procedure for necessity. At the same time, update readily when another participant can explain evidence that justifies something you initially questioned.\n\nFavor coherent systems over collections of independent fixes; demonstrated need over hypothetical need; simple mechanisms over elaborate ones when both work; explicit reasoning over inherited convention; consolidation over duplication; adaptable rules over rigid bureaucracy; and useful structure over procedural ceremony.\n\nRemain curious and capable of independent investigation. You can build, test, research, review, criticize, persuade, or change your mind. This personality is a tendency in how you approach problems, not a restriction on what work you may perform. You are neither the group's moderator nor its manager and have no special authority. You are an equal peer whose distinctive contribution is to look at the whole system and ask whether it can be made more coherent, economical, or integrated.",
    }

    await database.update_default_profiles(
        "Agent A default",
        old_defaults["agent_a"],
        "Agent B default",
        old_defaults["agent_b"],
        "Agent C · The Integrator",
        old_defaults["agent_c"],
    )
    await database.initialize()
    migrated = await database.get_default_profiles()

    assert migrated["agent_a"]["developer_instructions"] == AGENT_A_DEFAULT_PERSONALITY
    assert migrated["agent_b"]["developer_instructions"] == AGENT_B_DEFAULT_PERSONALITY
    assert migrated["agent_c"]["developer_instructions"] == AGENT_C_DEFAULT_PERSONALITY
    assert migrated["agent_c"]["name"] == "Agent C default"

    custom_a = old_defaults["agent_a"] + "\nCustom principal preference."
    await database.update_default_profiles(
        "Custom A",
        custom_a,
        "Agent B default",
        old_defaults["agent_b"],
        "Agent C · The Integrator",
        old_defaults["agent_c"],
    )
    await database.initialize()
    remigrated = await database.get_default_profiles()

    assert remigrated["agent_a"]["developer_instructions"] == custom_a
    assert remigrated["agent_a"]["name"] == "Custom A"
    assert remigrated["agent_b"]["developer_instructions"] == AGENT_B_DEFAULT_PERSONALITY
    assert remigrated["agent_c"]["developer_instructions"] == AGENT_C_DEFAULT_PERSONALITY
    assert remigrated["agent_c"]["name"] == "Agent C default"


@pytest.mark.asyncio
async def test_failed_c_thread_start_compensates_without_touching_ab(runtime_factory):
    runtime = await runtime_factory(FailingCAgentAdapter())
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="Remain two", starting_agent="agent_a", auto_start=False)
    )
    room_id = snapshot["id"]
    await _make_legacy_pair(runtime, room_id)
    before = {
        item["agent_key"]: item["thread_id"]
        for item in await runtime.db.get_agents(room_id)
    }
    with pytest.raises(RuntimeError, match="simulated C thread creation failure"):
        await runtime.add_agent(room_id, AddAgentRequest())
    after = {item["agent_key"]: item["thread_id"] for item in await runtime.db.get_agents(room_id)}
    assert after == before
    assert await runtime.db.get_agent(room_id, "agent_c") is None
    assert not any(
        event["event_type"] == "agent_added" for event in await runtime.db.get_events(room_id)
    )


@pytest.mark.asyncio
async def test_new_room_is_permanent_triad_and_c_is_default_starter(runtime_factory):
    adapter = FakeAgentAdapter({"agent_c": [(Outcome.PASS, "")]})
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(topic="C receives the objective first", auto_start=False)
    )

    agents = {item["agent_key"]: item for item in snapshot["agents"]}
    assert set(agents) == {"agent_a", "agent_b", "agent_c"}
    assert len({item["thread_id"] for item in agents.values()}) == 3
    assert snapshot["active_round"]["starting_agent"] == "agent_c"

    await runtime.start_round(snapshot["id"], snapshot["active_round_id"])
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 1)
    await asyncio.sleep(0.05)
    assert not adapter.calls["agent_a"]
    assert not adapter.calls["agent_b"]


@pytest.mark.asyncio
async def test_peer_exchange_keeps_c_passive_then_integrates_once(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [],
            "agent_b": [(Outcome.PASS, "")],
            "agent_c": [(Outcome.FINISH, "Integrated")],
        },
        blocked_calls={"agent_b": {1}},
    )
    adapter.decisions["agent_a"].append(
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="A material result for B to verify",
            invoke_targets=["agent_b"],
        )
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Peer work then integration",
            starting_agent="agent_a",
            max_consecutive_passes=10,
        )
    )

    await wait_until(lambda: len(adapter.calls["agent_b"]) == 1)
    assert not adapter.calls["agent_c"]
    adapter.release_call("agent_b", 1)

    await wait_until(lambda: len(adapter.calls["agent_c"]) == 1)
    prompt = adapter.calls["agent_c"][0]["prompt"]
    assert "A material result for B to verify" in prompt
    assert "Integrate the unread peer work" in prompt
    await wait_until(lambda: _room_has_status(runtime, snapshot["id"], RoomStatus.FINISHED))
    events = await runtime.db.get_events(snapshot["id"])
    integration = [event for event in events if event["event_type"] == "integration_required"]
    assert len(integration) == 1
    assert integration[0]["metadata"]["pending_peer_sources"] == ["agent_a"]
    assert len(adapter.calls["agent_c"]) == 1


@pytest.mark.asyncio
async def test_c_multi_peer_delegation_batches_returns_until_full_cohort_settles(
    runtime_factory,
):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [],
            "agent_b": [],
            "agent_c": [],
        },
        blocked_calls={"agent_a": {1}},
    )
    adapter.decisions["agent_c"].extend(
        [
            AgentDecision(
                outcome=Outcome.MESSAGE,
                message=(
                    "A: assess the causal evidence. "
                    "B: design the practical implementation path."
                ),
                invoke_targets=["agent_a", "agent_b"],
            ),
            AgentDecision(outcome=Outcome.FINISH, message="Integrated both returns"),
        ]
    )
    adapter.decisions["agent_a"].append(
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="A causal-evidence return",
            invoke_targets=["agent_c"],
        )
    )
    adapter.decisions["agent_b"].append(
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="B implementation return",
            invoke_targets=["agent_c"],
        )
    )

    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Batch one C delegation cohort",
            starting_agent="agent_c",
            max_consecutive_passes=10,
        )
    )
    room_id = snapshot["id"]

    await wait_until(
        lambda: len(adapter.calls["agent_a"]) == 1
        and len(adapter.calls["agent_b"]) == 1
    )
    await wait_until(lambda: len(adapter.completed_calls["agent_b"]) == 1)
    assert len(adapter.calls["agent_c"]) == 1

    async def b_return_is_durable() -> bool:
        return any(
            event["event_type"] == "agent_message"
            and event["source"] == "agent_b"
            and event["content"] == "B implementation return"
            for event in await runtime.db.get_events(room_id)
        )

    await wait_until(b_return_is_durable)
    events = await runtime.db.get_events(room_id)
    b_return = next(
        event
        for event in events
        if event["event_type"] == "agent_message"
        and event["source"] == "agent_b"
        and event["content"] == "B implementation return"
    )
    b_to_c = next(
        delivery
        for delivery in b_return["deliveries"]
        if delivery["agent_key"] == "agent_c"
    )
    assert b_to_c["runnable"] is False
    assert b_return["metadata"]["requested_runnable_recipients"] == ["agent_c"]
    assert b_return["metadata"]["runnable_recipients"] == []
    assert b_return["metadata"]["deferred_runnable_recipients"] == ["agent_c"]

    adapter.release_call("agent_a", 1)
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 2)
    prompt = adapter.calls["agent_c"][1]["prompt"]
    assert "A causal-evidence return" in prompt
    assert "B implementation return" in prompt
    assert "All peers invoked by the same delegation have now settled" in prompt

    await wait_until(lambda: _room_has_status(runtime, room_id, RoomStatus.FINISHED))
    events = await runtime.db.get_events(room_id)
    cohort_triggers = [
        event
        for event in events
        if event["event_type"] == "delegation_cohort_settled"
    ]
    assert len(cohort_triggers) == 1
    assert cohort_triggers[0]["metadata"]["delegation_cohort"] == [
        "agent_a",
        "agent_b",
    ]
    assert cohort_triggers[0]["metadata"]["settlement_signals"] == {
        "agent_a": "MESSAGE",
        "agent_b": "MESSAGE",
    }
    assert len(adapter.calls["agent_c"]) == 2


@pytest.mark.asyncio
async def test_c_multi_peer_delegation_releases_after_message_and_pass_settle(
    runtime_factory,
):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [],
            "agent_b": [(Outcome.PASS, "")],
            "agent_c": [],
        },
        blocked_calls={"agent_a": {1}},
    )
    adapter.decisions["agent_c"].extend(
        [
            AgentDecision(
                outcome=Outcome.MESSAGE,
                message="Ask both peers for bounded contributions.",
                invoke_targets=["agent_a", "agent_b"],
            ),
            AgentDecision(outcome=Outcome.FINISH, message="Integrated available return"),
        ]
    )
    adapter.decisions["agent_a"].append(
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="A substantive return after B passed",
            invoke_targets=["agent_c"],
        )
    )

    runtime = await runtime_factory(adapter, "delegation-pass.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="One delegated peer passes",
            starting_agent="agent_c",
            max_consecutive_passes=10,
        )
    )

    await wait_until(lambda: len(adapter.completed_calls["agent_b"]) == 1)
    await asyncio.sleep(0.05)
    assert len(adapter.calls["agent_c"]) == 1

    adapter.release_call("agent_a", 1)
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 2)
    prompt = adapter.calls["agent_c"][1]["prompt"]
    assert "A substantive return after B passed" in prompt
    assert "agent_b: PASS" in prompt
    await wait_until(
        lambda: _room_has_status(runtime, snapshot["id"], RoomStatus.FINISHED)
    )


@pytest.mark.asyncio
async def test_direct_peer_return_to_c_needs_no_synthetic_integration(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [],
            "agent_c": [(Outcome.FINISH, "Integrated directly")],
        }
    )
    adapter.decisions["agent_a"].append(
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="A returns the material result directly to C",
            invoke_targets=["agent_c"],
        )
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Direct return",
            starting_agent="agent_a",
            max_consecutive_passes=10,
        )
    )

    await wait_until(lambda: len(adapter.calls["agent_c"]) == 1)
    assert "A returns the material result directly to C" in adapter.calls["agent_c"][0]["prompt"]
    await wait_until(lambda: _room_has_status(runtime, snapshot["id"], RoomStatus.FINISHED))
    events = await runtime.db.get_events(snapshot["id"])
    assert not any(event["event_type"] == "integration_required" for event in events)
    assert len(adapter.calls["agent_c"]) == 1


@pytest.mark.asyncio
async def test_b_to_a_direct_exchange_also_defers_c_until_integration(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.PASS, "")],
            "agent_b": [],
            "agent_c": [(Outcome.FINISH, "Integrated B result")],
        },
        blocked_calls={"agent_a": {1}},
    )
    adapter.decisions["agent_b"].append(
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="B material result for A to inspect",
            invoke_targets=["agent_a"],
        )
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="B to A then C",
            starting_agent="agent_b",
            max_consecutive_passes=10,
        )
    )

    await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
    assert not adapter.calls["agent_c"]
    adapter.release_call("agent_a", 1)
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 1)
    assert "B material result for A to inspect" in adapter.calls["agent_c"][0]["prompt"]
    events = await runtime.db.get_events(snapshot["id"])
    integration = [event for event in events if event["event_type"] == "integration_required"]
    assert len(integration) == 1
    assert integration[0]["metadata"]["pending_peer_sources"] == ["agent_b"]


@pytest.mark.asyncio
async def test_c_can_redelegate_from_integration_and_receive_direct_followup(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [],
            "agent_b": [(Outcome.PASS, "")],
            "agent_c": [],
        }
    )
    adapter.decisions["agent_a"].extend(
        [
            AgentDecision(
                outcome=Outcome.MESSAGE,
                message="A first result for B",
                invoke_targets=["agent_b"],
            ),
            AgentDecision(
                outcome=Outcome.MESSAGE,
                message="A follow-up result returned to C",
                invoke_targets=["agent_c"],
            ),
        ]
    )
    adapter.decisions["agent_c"].extend(
        [
            AgentDecision(
                outcome=Outcome.MESSAGE,
                message="C requests one focused follow-up from A",
                invoke_targets=["agent_a"],
            ),
            AgentDecision(outcome=Outcome.FINISH, message="Integrated after follow-up"),
        ]
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Integrate then redelegate",
            starting_agent="agent_a",
            max_consecutive_passes=10,
        )
    )

    await wait_until(lambda: len(adapter.calls["agent_c"]) == 2)
    assert "A first result for B" in adapter.calls["agent_c"][0]["prompt"]
    assert "C requests one focused follow-up from A" in adapter.calls["agent_a"][1]["prompt"]
    assert "A follow-up result returned to C" in adapter.calls["agent_c"][1]["prompt"]
    await wait_until(lambda: _room_has_status(runtime, snapshot["id"], RoomStatus.FINISHED))
    events = await runtime.db.get_events(snapshot["id"])
    assert len([event for event in events if event["event_type"] == "integration_required"]) == 1


@pytest.mark.asyncio
async def test_pending_integration_trigger_is_idempotent_and_survives_restart(runtime_factory):
    first = await runtime_factory(FakeAgentAdapter(), "integration-restart.db")
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Durable integration trigger",
            starting_agent="agent_a",
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    round_id = snapshot["active_round_id"]
    await first.db.start_round(room_id, round_id)
    await first.db.set_room_status(room_id, RoomStatus.PAUSED)
    await first.db.create_event(
        room_id,
        "agent_message",
        "agent_a",
        "all",
        "Persisted passive A result",
        deliver_to=("agent_c",),
        runnable_to=(),
        discussion_id=round_id,
        round_id=round_id,
    )

    assert await first._schedule_c_integration_if_needed(room_id, round_id)
    assert await first._schedule_c_integration_if_needed(room_id, round_id)
    events = await first.db.get_events(room_id)
    assert len([event for event in events if event["event_type"] == "integration_required"]) == 1
    assert not first.adapter.calls["agent_c"]
    await first.close()

    second_adapter = FakeAgentAdapter({"agent_c": [(Outcome.FINISH, "Integrated after restart")]})
    second = await runtime_factory(second_adapter, "integration-restart.db")
    await second.resume(room_id)
    await wait_until(lambda: len(second_adapter.calls["agent_c"]) == 1)
    assert "Persisted passive A result" in second_adapter.calls["agent_c"][0]["prompt"]
    assert "Integrate the unread peer work" in second_adapter.calls["agent_c"][0]["prompt"]
    await wait_until(lambda: _room_has_status(second, room_id, RoomStatus.FINISHED))
    restarted_events = await second.db.get_events(room_id)
    assert len(
        [event for event in restarted_events if event["event_type"] == "integration_required"]
    ) == 1


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
        CreateRoomRequest(topic="Compact C", starting_agent="agent_c")
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
        CreateRoomRequest(topic="Three-way routing", starting_agent="agent_a")
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
async def test_empty_invoke_targets_publishes_message_without_waking_peers(runtime_factory):
    adapter = FakeAgentAdapter(
        {
            "agent_a": [(Outcome.PASS, "")],
            "agent_b": [(Outcome.PASS, "")],
            "agent_c": [],
        }
    )
    adapter.decisions["agent_c"].append(
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="C posts a public update that needs no peer cognition",
            invoke_targets=[],
        )
    )
    runtime = await runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="No-wake public message",
            starting_agent="agent_c",
            max_consecutive_passes=10,
        )
    )
    room_id = snapshot["id"]

    await wait_until(
        lambda: _room_has_status(runtime, room_id, RoomStatus.FINISHED)
    )
    assert not adapter.calls["agent_a"]
    assert not adapter.calls["agent_b"]
    assert "or [] for a public/readable message that should make no peer runnable" in (
        adapter.calls["agent_c"][0]["prompt"]
    )

    message = next(
        event for event in await runtime.db.get_events(room_id)
        if event["event_type"] == "agent_message"
    )
    deliveries = {item["agent_key"]: item for item in message["deliveries"]}
    assert set(deliveries) == {"agent_a", "agent_b"}
    assert all(item["runnable"] is False for item in deliveries.values())
    assert message["metadata"]["invoke_targets"] == []
    assert message["metadata"]["requested_runnable_recipients"] == []
    assert message["metadata"]["runnable_recipients"] == []
    assert message["metadata"]["readable_recipients"] == ["agent_a", "agent_b"]
    assert message["metadata"]["legacy_fanout_invocations_avoided"] == 2


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


@pytest.mark.asyncio
async def test_c_can_redelegate_same_peer_with_stronger_execution_config(runtime_factory):
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_c": []}
    )
    adapter.decisions["agent_c"].extend(
        [
            AgentDecision(
                outcome=Outcome.MESSAGE,
                message="A: handle this routine bounded pass.",
                invoke_targets=["agent_a"],
                execution_configs=[{"target": "agent_a", "config": "luna-medium"}],
            ),
            AgentDecision(
                outcome=Outcome.MESSAGE,
                message="A: retry with stronger cognition because you requested escalation.",
                invoke_targets=["agent_a"],
                execution_configs=[{"target": "agent_a", "config": "terra-high"}],
            ),
            AgentDecision(outcome=Outcome.FINISH, message="Integrated escalated result"),
        ]
    )
    adapter.decisions["agent_a"].extend(
        [
            AgentDecision(
                outcome=Outcome.MESSAGE,
                message="I need stronger cognition for this dependency.",
                invoke_targets=["agent_c"],
            ),
            AgentDecision(
                outcome=Outcome.MESSAGE,
                message="Escalated work complete.",
                invoke_targets=["agent_c"],
            ),
        ]
    )

    runtime = await runtime_factory(adapter, "adaptive-execution.db")
    room = await runtime.create_room(
        CreateRoomRequest(
            topic="Adaptive execution trial",
            starting_agent="agent_c",
            max_consecutive_passes=10,
        )
    )

    await wait_until(lambda: len(adapter.calls["agent_a"]) == 2)
    await wait_until(lambda: len(adapter.calls["agent_c"]) == 3)

    assert adapter.calls["agent_a"][0]["model"] == "gpt-5.6-luna"
    assert adapter.calls["agent_a"][0]["reasoning_effort"] == "medium"
    assert adapter.calls["agent_a"][1]["model"] == "gpt-5.6-terra"
    assert adapter.calls["agent_a"][1]["reasoning_effort"] == "high"
    assert all(call["model"] == "gpt-5.6-terra" for call in adapter.calls["agent_c"])
    assert all(call["reasoning_effort"] == "high" for call in adapter.calls["agent_c"])

    messages = [
        event
        for event in await runtime.db.get_events(room["id"])
        if event["event_type"] == "agent_message" and event["source"] == "agent_c"
    ]
    assert [event["metadata"]["execution_configs"] for event in messages] == [
        [{"target": "agent_a", "config": "luna-medium"}],
        [{"target": "agent_a", "config": "terra-high"}],
    ]
    assert messages[0]["metadata"]["resolved_execution_configs"]["agent_a"] == {
        "config_id": "luna-medium",
        "model": "gpt-5.6-luna",
        "reasoning_effort": "medium",
    }
    assert messages[1]["metadata"]["resolved_execution_configs"]["agent_a"] == {
        "config_id": "terra-high",
        "model": "gpt-5.6-terra",
        "reasoning_effort": "high",
    }


def test_invoke_targets_validation_and_room_membership() -> None:
    no_wake = AgentDecision(
        outcome=Outcome.MESSAGE,
        message="public without runnable peers",
        invoke_targets=[],
    )
    assert no_wake.invoke_targets == []

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
    with pytest.raises(ValidationError, match="execution_configs is valid only for MESSAGE"):
        AgentDecision(
            outcome=Outcome.FINISH,
            message="done",
            execution_configs=[{"target": "agent_b", "config": "luna-medium"}],
        )
    with pytest.raises(ValidationError, match="cannot contain duplicate targets"):
        AgentDecision(
            outcome=Outcome.MESSAGE,
            message="bad",
            invoke_targets=["agent_a"],
            execution_configs=[
                {"target": "agent_a", "config": "luna-medium"},
                {"target": "agent_a", "config": "terra-high"},
            ],
        )

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


    selected = AgentDecision(
        outcome=Outcome.MESSAGE,
        message="delegate",
        invoke_targets=["agent_a"],
        execution_configs=[{"target": "agent_a", "config": "luna-medium"}],
    )
    assert RoomRuntime._resolve_execution_configs(
        selected, "agent_c", ("agent_a",)
    )["agent_a"]["model"] == "gpt-5.6-luna"
    assert RoomRuntime._resolve_execution_configs(
        selected, "agent_b", ("agent_a",)
    ) == {}

    invalid_target = AgentDecision(
        outcome=Outcome.MESSAGE,
        message="bad selection",
        invoke_targets=["agent_a"],
        execution_configs=[{"target": "agent_b", "config": "terra-high"}],
    )
    with pytest.raises(ValueError, match="only peers C is invoking"):
        RoomRuntime._resolve_execution_configs(
            invalid_target, "agent_c", ("agent_a",)
        )


@pytest.mark.asyncio
async def test_future_round_configuration_is_membership_keyed(runtime_factory):
    adapter = FakeAgentAdapter({"agent_c": [(Outcome.PASS, "")]})
    runtime = await runtime_factory(adapter)
    initial = await runtime.create_room(
        CreateRoomRequest(topic="Two-member history", starting_agent="agent_a", auto_start=False)
    )
    await _make_legacy_pair(runtime, initial["id"])
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
        CreateRoomRequest(topic="Settle together", starting_agent="either")
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
