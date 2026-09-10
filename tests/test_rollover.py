from __future__ import annotations

import asyncio
import hashlib
import json
import time

import pytest
from fastapi.testclient import TestClient

from codex_room.db import Database
from codex_room.institutional import publish_institutional_release
from codex_room.main import create_app
from codex_room.models import (
    AddAgentRequest,
    BindInstitutionalReleaseRequest,
    CreateRoomRequest,
    ObserverMessageRequest,
    Outcome,
    PrepareRoundRequest,
    RolloverRoomRequest,
    RoomStatus,
    UpdateRoomRequest,
)
from codex_room.orchestrator import RoomRuntime

from .fakes import FakeAgentAdapter, wait_until


def test_rollover_http_endpoint_leaves_successor_preparing(tmp_path):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    app = create_app(
        database_path=tmp_path / "rollover-api.db",
        data_root=tmp_path / "data",
        adapter=adapter,
    )
    with TestClient(app) as client:
        source = client.post(
            "/api/rooms",
            json={
                "title": "API source",
                "topic": "finish first",
                "starting_agent": "agent_a",
                "max_consecutive_passes": 1,
            },
        ).json()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            current = client.get(f"/api/rooms/{source['id']}").json()
            if current["status"] == RoomStatus.FINISHED and all(
                agent["execution"]["pending_count"] == 0
                and agent["execution"]["processing_count"] == 0
                and agent["execution"]["durable_execution_state"]
                not in {"claimed", "active", "recovering", "result_ready", "quarantined"}
                for agent in current["agents"]
            ):
                break
            time.sleep(0.02)
        response = client.post(
            f"/api/rooms/{source['id']}/rollover",
            json={"checkpoint": "visible API checkpoint"},
        )
        assert response.status_code == 201, response.text
        successor = response.json()
        assert successor["status"] == RoomStatus.PREPARING
        assert successor["active_round"]["prompt"] == "visible API checkpoint"


async def _finished_source(
    runtime: RoomRuntime,
    *,
    include_c: bool = False,
    topic: str = "source topic",
) -> dict:
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            title="Long-lived source",
            topic=topic,
            include_agent_c=include_c,
            starting_agent="agent_a",
            max_consecutive_passes=1,
        )
    )
    await wait_until(
        lambda: _room_has_status(runtime, snapshot["id"], RoomStatus.FINISHED)
    )
    await wait_until(lambda: _room_is_quiescent(runtime, snapshot["id"]))
    current = await runtime.snapshot(snapshot["id"])
    assert current is not None
    return current


async def _room_has_status(runtime: RoomRuntime, room_id: str, status: str) -> bool:
    room = await runtime.db.get_room(room_id)
    return bool(room and room["status"] == status)


async def _room_is_quiescent(runtime: RoomRuntime, room_id: str) -> bool:
    evidence = await runtime.db.get_delivery_execution(room_id)
    return all(
        not item.get("pending_count")
        and not item.get("processing_count")
        and (item.get("execution") or {}).get("state")
        not in {"claimed", "active", "recovering", "result_ready", "quarantined"}
        for item in evidence.values()
    )


def _publish_test_release(
    runtime: RoomRuntime,
    room_id: str,
    *,
    release_id: str = "bound-tools-v1",
    content: bytes = b"# durable coordinator",
):
    workspace = runtime.workspace(room_id)
    durable = workspace / "canonical" / "room-work.ps1"
    durable.parent.mkdir(exist_ok=True)
    durable.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    manifest = {
        "schemaVersion": 1,
        "releaseId": release_id,
        "createdInRoomId": room_id,
        "description": "Reviewed coordination tool.",
        "artifacts": [
            {
                "sourcePath": "canonical/room-work.ps1",
                "materializeTo": "room-work.ps1",
                "sha256": digest,
                "size": len(content),
                "kind": "tool",
                "verification": {
                    "command": "focused test",
                    "result": "passed",
                    "reviewer": "independent reviewer",
                    "reviewedHash": digest,
                },
            }
        ],
        "nonInheritedState": [".room-work.json", ".room-work.lock"],
    }
    manifest_path = workspace / "institutional" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return publish_institutional_release(workspace, runtime.data_root)


@pytest.mark.asyncio
async def test_rollover_copies_only_stable_configuration_and_checkpoint(tmp_path):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = RoomRuntime(Database(tmp_path / "happy.db"), adapter, tmp_path / "data")
    await runtime.initialize()
    try:
        source = await runtime.create_room(
            CreateRoomRequest(
                title="Long-lived source",
                topic="OLD_PUBLIC_CANARY",
                include_agent_c=True,
                starting_agent="agent_a",
                max_consecutive_passes=1,
                auto_start=False,
            )
        )
        prepared = await runtime.prepare_round(
            source["id"],
            PrepareRoundRequest(
                title="Old configured round",
                prompt="OLD_PROMPT_CANARY",
                participant_private={"agent_a": "OLD_PRIVATE_CANARY"},
                participant_overlays={"agent_a": "OLD_OVERLAY_CANARY"},
                task_overlay="OLD_TASK_OVERLAY_CANARY",
                starting_agent="agent_a",
            ),
        )
        await runtime.db.create_event(
            source["id"],
            "context_checkpoint",
            "room",
            "observer",
            "OLD_SUMMARY_CANARY",
            round_id=prepared["active_round_id"],
        )
        await runtime.start_round(source["id"], prepared["active_round_id"])
        await wait_until(lambda: len(adapter.calls["agent_a"]) == 1)
        await wait_until(
            lambda: _room_has_status(runtime, source["id"], RoomStatus.FINISHED)
        )
        await wait_until(lambda: _room_is_quiescent(runtime, source["id"]))
        old_agents = await runtime.db.get_agents(source["id"])

        checkpoint = "MVP CHECKPOINT: continue only from this reviewed state."
        successor = await runtime.rollover(
            source["id"], RolloverRoomRequest(checkpoint=checkpoint)
        )

        predecessor = await runtime.db.get_room(source["id"])
        assert predecessor and predecessor["status"] == RoomStatus.ARCHIVED
        assert predecessor["metadata"]["sealed"] is True
        assert successor["status"] == RoomStatus.PREPARING
        assert successor["active_round"]["prompt"] == checkpoint
        assert successor["active_round"]["participant_private"] == {}
        assert successor["active_round"]["participant_overlays"] == {}
        new_agents = successor["agents"]
        assert [item["agent_key"] for item in new_agents] == ["agent_a", "agent_b", "agent_c"]
        assert {item["thread_id"] for item in new_agents}.isdisjoint(
            {item["thread_id"] for item in old_agents}
        )
        for old, new in zip(old_agents, new_agents, strict=True):
            for field in (
                "agent_key",
                "name",
                "developer_instructions",
                "profile_id",
                "profile_snapshot",
                "room_override",
            ):
                assert new[field] == old[field]
        exported = str(successor)
        for canary in (
            "OLD_PUBLIC_CANARY",
            "OLD_PROMPT_CANARY",
            "OLD_PRIVATE_CANARY",
            "OLD_OVERLAY_CANARY",
            "OLD_TASK_OVERLAY_CANARY",
            "OLD_SUMMARY_CANARY",
        ):
            assert canary not in exported

        await runtime.start_round(successor["id"], successor["active_round_id"])
        await wait_until(lambda: len(adapter.calls["agent_a"]) >= 2)
        prompt = adapter.calls["agent_a"][-1]["prompt"]
        assert prompt.count(checkpoint) == 1
        for canary in (
            "OLD_PUBLIC_CANARY",
            "OLD_PRIVATE_CANARY",
            "OLD_OVERLAY_CANARY",
            "OLD_SUMMARY_CANARY",
        ):
            assert canary not in prompt
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_rollover_materializes_verified_institutional_release_only(tmp_path):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = RoomRuntime(Database(tmp_path / "inherit.db"), adapter, tmp_path / "data")
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        workspace = runtime.workspace(source["id"])
        durable = workspace / "canonical" / "room-work.ps1"
        durable.parent.mkdir()
        durable.write_text("# durable coordinator", encoding="utf-8")
        (workspace / ".room-work.json").write_text('{"stale":true}', encoding="utf-8")
        (workspace / "runtime.log").write_text("do not inherit", encoding="utf-8")
        payload = durable.read_bytes()
        manifest = {
            "schemaVersion": 1,
            "releaseId": "room-tools-v1",
            "createdInRoomId": source["id"],
            "description": "Reviewed coordination tool.",
            "artifacts": [
                {
                    "sourcePath": "canonical/room-work.ps1",
                    "materializeTo": "room-work.ps1",
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "size": len(payload),
                    "kind": "tool",
                    "verification": {
                        "command": "focused test",
                        "result": "passed",
                        "reviewer": "independent reviewer",
                        "reviewedHash": hashlib.sha256(payload).hexdigest(),
                    },
                }
            ],
            "nonInheritedState": [".room-work.json", ".room-work.lock"],
        }
        manifest_path = workspace / "institutional" / "manifest.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        published = publish_institutional_release(workspace, runtime.data_root)

        successor = await runtime.rollover(
            source["id"],
            RolloverRoomRequest(
                checkpoint="institutional checkpoint",
                institutional_release_sha256=published.manifest_sha256,
            ),
        )
        successor_workspace = runtime.workspace(successor["id"])
        assert (successor_workspace / "room-work.ps1").read_bytes() == payload
        assert (successor_workspace / "institutional" / "manifest.json").is_file()
        assert not (successor_workspace / ".room-work.json").exists()
        assert not (successor_workspace / "runtime.log").exists()
        release = successor["metadata"]["institutional_release"]
        assert release["release_id"] == "room-tools-v1"
        assert release["manifest_sha256"] == hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest()
        events = await runtime.db.get_events(successor["id"])
        inherited = next(item for item in events if item["event_type"] == "rollover_checkpoint")
        assert inherited["metadata"]["institutional_release"] == release
        predecessor = await runtime.db.get_room(source["id"])
        assert predecessor is not None
        assert predecessor["metadata"]["rollover_successor"]["institutional_release"] == release
        assert successor["metadata"]["lineage"]["institutional_release"] == release

        await runtime.start_round(successor["id"], successor["active_round_id"])
        await wait_until(
            lambda: _room_has_status(runtime, successor["id"], RoomStatus.FINISHED)
        )
        await wait_until(lambda: _room_is_quiescent(runtime, successor["id"]))
        carried = await runtime.rollover(
            successor["id"], RolloverRoomRequest(checkpoint="next checkpoint")
        )
        assert (runtime.workspace(carried["id"]) / "room-work.ps1").read_bytes() == payload
        assert carried["metadata"]["institutional_release"] == release
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_existing_room_binds_release_once_and_carries_it_forward(tmp_path):
    runtime = RoomRuntime(
        Database(tmp_path / "bind.db"),
        FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]}),
        tmp_path / "data",
    )
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        workspace = runtime.workspace(source["id"])
        (workspace / ".room-work.json").write_text('{"stale":true}', encoding="utf-8")
        release = _publish_test_release(runtime, source["id"])
        request = BindInstitutionalReleaseRequest(
            institutional_release_sha256=release.manifest_sha256
        )

        bound = await runtime.bind_institutional_release(source["id"], request)
        assert bound["metadata"]["institutional_release"] == release.metadata()
        assert bound["metadata"]["lineage"]["institutional_release"] == release.metadata()
        events = await runtime.db.get_events(source["id"])
        audit = [
            event for event in events if event["event_type"] == "institutional_release_bound"
        ]
        assert len(audit) == 1
        assert audit[0]["metadata"]["institutional_release"] == release.metadata()
        assert audit[0]["conversational"] is False
        assert audit[0]["turn_triggering"] is False

        retried = await runtime.bind_institutional_release(source["id"], request)
        assert retried["metadata"] == bound["metadata"]
        events = await runtime.db.get_events(source["id"])
        assert sum(
            event["event_type"] == "institutional_release_bound" for event in events
        ) == 1

        successor = await runtime.rollover(
            source["id"], RolloverRoomRequest(checkpoint="implicit bound release")
        )
        successor_workspace = runtime.workspace(successor["id"])
        assert (successor_workspace / "room-work.ps1").read_bytes() == (
            workspace / "canonical" / "room-work.ps1"
        ).read_bytes()
        assert not (successor_workspace / ".room-work.json").exists()
        assert successor["metadata"]["institutional_release"] == release.metadata()
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_bind_release_validates_before_mutation_and_rejects_replacement(tmp_path):
    runtime = RoomRuntime(
        Database(tmp_path / "bind-guards.db"),
        FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]}),
        tmp_path / "data",
    )
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        before = await runtime.db.get_room(source["id"])
        with pytest.raises(ValueError, match="does not exist"):
            await runtime.bind_institutional_release(
                source["id"],
                BindInstitutionalReleaseRequest(institutional_release_sha256="0" * 64),
            )
        assert await runtime.db.get_room(source["id"]) == before
        assert not any(
            event["event_type"] == "institutional_release_bound"
            for event in await runtime.db.get_events(source["id"])
        )

        first = _publish_test_release(runtime, source["id"])
        await runtime.bind_institutional_release(
            source["id"],
            BindInstitutionalReleaseRequest(
                institutional_release_sha256=first.manifest_sha256
            ),
        )
        second = _publish_test_release(
            runtime,
            source["id"],
            release_id="bound-tools-v2",
            content=b"# incompatible replacement",
        )
        with pytest.raises(ValueError, match="already bound"):
            await runtime.bind_institutional_release(
                source["id"],
                BindInstitutionalReleaseRequest(
                    institutional_release_sha256=second.manifest_sha256
                ),
            )
        unchanged = await runtime.db.get_room(source["id"])
        assert unchanged
        assert unchanged["metadata"]["institutional_release"] == first.metadata()
        assert sum(
            event["event_type"] == "institutional_release_bound"
            for event in await runtime.db.get_events(source["id"])
        ) == 1
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_bind_release_rejects_sealed_and_inactive_rooms(tmp_path):
    runtime = RoomRuntime(
        Database(tmp_path / "bind-state-guards.db"),
        FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]}),
        tmp_path / "data",
    )
    await runtime.initialize()
    try:
        sealed = await _finished_source(runtime)
        release = _publish_test_release(runtime, sealed["id"])
        await runtime.rollover(
            sealed["id"], RolloverRoomRequest(checkpoint="seal source")
        )
        request = BindInstitutionalReleaseRequest(
            institutional_release_sha256=release.manifest_sha256
        )
        with pytest.raises(ValueError, match="sealed"):
            await runtime.bind_institutional_release(sealed["id"], request)

        inactive = await runtime.create_room(
            CreateRoomRequest(title="Inactive", topic="hold", auto_start=False)
        )
        await runtime.db.set_room_status(inactive["id"], RoomStatus.ERROR)
        with pytest.raises(ValueError, match="while Room is error"):
            await runtime.bind_institutional_release(inactive["id"], request)
        for room_id in (sealed["id"], inactive["id"]):
            room = await runtime.db.get_room(room_id)
            assert room and "institutional_release" not in room["metadata"]
            assert not any(
                event["event_type"] == "institutional_release_bound"
                for event in await runtime.db.get_events(room_id)
            )
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_bind_release_does_not_normalize_partial_metadata(tmp_path):
    runtime = RoomRuntime(
        Database(tmp_path / "bind-partial.db"),
        FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]}),
        tmp_path / "data",
    )
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        release = _publish_test_release(runtime, source["id"])
        current = await runtime.db.get_room(source["id"])
        assert current is not None
        partial = current["metadata"]
        partial["institutional_release"] = release.metadata()
        assert "institutional_release" not in partial.get("lineage", {})
        async with runtime.db.connect() as db:
            await db.execute(
                "UPDATE rooms SET metadata_json=? WHERE id=?",
                (json.dumps(partial), source["id"]),
            )
            await db.commit()

        with pytest.raises(ValueError, match="already bound"):
            await runtime.bind_institutional_release(
                source["id"],
                BindInstitutionalReleaseRequest(
                    institutional_release_sha256=release.manifest_sha256
                ),
            )

        unchanged = await runtime.db.get_room(source["id"])
        assert unchanged and unchanged["metadata"] == partial
        assert not any(
            event["event_type"] == "institutional_release_bound"
            for event in await runtime.db.get_events(source["id"])
        )
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_targeted_profile_rebind_preserves_identity_and_records_hash(tmp_path):
    adapter = FakeAgentAdapter()
    runtime = RoomRuntime(Database(tmp_path / "profile-rebind.db"), adapter, tmp_path / "data")
    await runtime.initialize()
    try:
        room = await runtime.create_room(
            CreateRoomRequest(
                title="Rebind diagnostic",
                topic="hold",
                include_agent_c=True,
                auto_start=False,
            )
        )
        await runtime.db.set_room_status(room["id"], RoomStatus.RUNNING)
        await runtime.ensure_workers(room["id"])
        before = {
            agent["agent_key"]: agent["thread_id"]
            for agent in await runtime.db.get_agents(room["id"])
        }
        selected = await runtime.db.get_agent(room["id"], "agent_b")
        assert selected is not None

        rebound = await runtime.rebind_agent_profile(room["id"], "agent_b")

        after = {agent["agent_key"]: agent["thread_id"] for agent in rebound["agents"]}
        assert after == before
        assert adapter.profile_rebinds == [
            {
                "agent_key": "agent_b",
                "thread_id": before["agent_b"],
                "developer_instructions": selected["developer_instructions"],
                "cwd": str(runtime.workspace(room["id"])),
            }
        ]
        events = await runtime.db.get_events(room["id"])
        audit = [event for event in events if event["event_type"] == "agent_profile_rebind"]
        assert len(audit) == 1
        assert audit[0]["metadata"] == {
            "agent_key": "agent_b",
            "thread_id": before["agent_b"],
            "developer_instructions_sha256": hashlib.sha256(
                selected["developer_instructions"].encode("utf-8")
            ).hexdigest(),
            "cache_entry_evicted": True,
            "result": "completed",
        }
        assert audit[0]["turn_triggering"] is False
        assert "awaits participant verification" in audit[0]["content"]
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_failed_profile_rebind_evicts_and_quarantines_without_identity_change(
    tmp_path,
):
    adapter = FakeAgentAdapter(profile_rebind_error=RuntimeError("simulated SDK failure"))
    runtime = RoomRuntime(
        Database(tmp_path / "profile-rebind-failure.db"), adapter, tmp_path / "data"
    )
    await runtime.initialize()
    try:
        room = await runtime.create_room(
            CreateRoomRequest(
                title="Failed rebind diagnostic",
                topic="hold",
                include_agent_c=True,
                auto_start=False,
            )
        )
        await runtime.db.set_room_status(room["id"], RoomStatus.RUNNING)
        await runtime.ensure_workers(room["id"])
        before = {
            agent["agent_key"]: agent["thread_id"]
            for agent in await runtime.db.get_agents(room["id"])
        }

        with pytest.raises(RuntimeError, match="simulated SDK failure"):
            await runtime.rebind_agent_profile(room["id"], "agent_b")

        after = {
            agent["agent_key"]: agent["thread_id"]
            for agent in await runtime.db.get_agents(room["id"])
        }
        assert after == before
        slot = runtime._worker_slots[(room["id"], "agent_b")]
        assert slot.quarantined is True
        assert slot.phase == "quarantined"
        assert slot.task is None
        events = await runtime.db.get_events(room["id"])
        audit = [event for event in events if event["event_type"] == "agent_profile_rebind"]
        assert len(audit) == 1
        assert audit[0]["status"] == "error"
        assert audit[0]["metadata"]["result"] == "failed"
        assert audit[0]["metadata"]["thread_id"] == before["agent_b"]
        assert "simulated SDK failure" not in str(audit[0])
        assert set(audit[0]["metadata"]) == {
            "agent_key",
            "thread_id",
            "developer_instructions_sha256",
            "cache_entry_evicted",
            "result",
        }
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_missing_selected_institutional_release_does_not_freeze_source(tmp_path):
    runtime = RoomRuntime(
        Database(tmp_path / "invalid-inherit.db"),
        FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]}),
        tmp_path / "data",
    )
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        with pytest.raises(ValueError, match="does not exist"):
            await runtime.rollover(
                source["id"],
                RolloverRoomRequest(
                    checkpoint="must not stage",
                    institutional_release_sha256="0" * 64,
                ),
            )
        unchanged = await runtime.db.get_room(source["id"])
        assert unchanged and unchanged["status"] == RoomStatus.FINISHED
        assert "rollover_pending" not in unchanged["metadata"]
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_room_workspace_manifest_is_never_implicitly_trusted(tmp_path):
    runtime = RoomRuntime(
        Database(tmp_path / "untrusted-manifest.db"),
        FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]}),
        tmp_path / "data",
    )
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        manifest = runtime.workspace(source["id"]) / "institutional" / "manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{"schemaVersion":1}', encoding="utf-8")
        successor = await runtime.rollover(
            source["id"], RolloverRoomRequest(checkpoint="empty inheritance")
        )
        assert list(runtime.workspace(successor["id"]).rglob("*")) == []
        assert "institutional_release" not in successor["metadata"]
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_rollover_rejects_nonquiescent_delivery(tmp_path):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = RoomRuntime(Database(tmp_path / "busy.db"), adapter, tmp_path / "data")
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        await runtime.db.create_event(
            source["id"],
            "observer_message",
            "observer",
            "agent_a",
            "queued canary",
            deliver_to=("agent_a",),
        )
        with pytest.raises(ValueError, match="quiescent"):
            await runtime.rollover(
                source["id"], RolloverRoomRequest(checkpoint="checkpoint")
            )
        assert (await runtime.db.get_room(source["id"]))["status"] == RoomStatus.FINISHED
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_reserved_rollover_freezes_ingress_and_abort_restores_source(tmp_path):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = RoomRuntime(Database(tmp_path / "freeze.db"), adapter, tmp_path / "data")
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        reservation = await runtime.db.reserve_rollover(
            source["id"], RolloverRoomRequest(checkpoint="checkpoint")
        )
        with pytest.raises(ValueError):
            await runtime.observer_message(
                source["id"], ObserverMessageRequest(target="all", content="must reject")
            )
        with pytest.raises(ValueError):
            await runtime.update_room(source["id"], UpdateRoomRequest(title="must reject"))
        with pytest.raises(ValueError):
            await runtime.add_agent(source["id"], AddAgentRequest())
        with pytest.raises(ValueError):
            await runtime.stop(source["id"])
        await runtime.db.abort_rollover(
            source["id"],
            reservation["operation_id"],
            reservation["successor_room_id"],
            "test abort",
        )
        restored = await runtime.db.get_room(source["id"])
        assert restored and restored["status"] == RoomStatus.FINISHED
        assert restored["metadata"]["rollover_history"][-1]["state"] == "aborted"
        assert await runtime.db.get_room(reservation["successor_room_id"]) is None
    finally:
        await runtime.close()


class FailingStartAdapter(FakeAgentAdapter):
    def __init__(self, fail_at: int) -> None:
        super().__init__({"agent_a": [(Outcome.PASS, "")]})
        self.fail_at = fail_at

    async def start_agent(self, agent, cwd):
        if len(self.starts) + 1 == self.fail_at:
            raise RuntimeError("injected thread provisioning failure")
        return await super().start_agent(agent, cwd)


class PredecessorCollisionAdapter(FakeAgentAdapter):
    def __init__(self) -> None:
        super().__init__({"agent_a": [(Outcome.PASS, "")]})
        self.collision_thread_id: str | None = None

    async def start_agent(self, agent, cwd):
        if self.collision_thread_id is not None:
            thread_id = self.collision_thread_id
            self.starts.append((agent["agent_key"], thread_id))
            return thread_id
        return await super().start_agent(agent, cwd)


@pytest.mark.asyncio
async def test_predecessor_thread_collision_is_audited_but_never_archived(tmp_path):
    adapter = PredecessorCollisionAdapter()
    runtime = RoomRuntime(Database(tmp_path / "collision.db"), adapter, tmp_path / "data")
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        old_ids = {item["thread_id"] for item in source["agents"]}
        adapter.collision_thread_id = source["agents"][0]["thread_id"]

        with pytest.raises(RuntimeError, match="duplicate or predecessor"):
            await runtime.rollover(
                source["id"], RolloverRoomRequest(checkpoint="checkpoint")
            )

        restored = await runtime.db.get_room(source["id"])
        assert restored and restored["status"] == RoomStatus.FINISHED
        audit = restored["metadata"]["rollover_history"][-1]
        assert audit["state"] == "aborted"
        assert audit["orphaned_thread_ids"] == []
        assert audit["suspicious_thread_ids"] == [adapter.collision_thread_id]
        assert old_ids.isdisjoint(adapter.archived)
        assert {item["thread_id"] for item in await runtime.db.get_agents(source["id"])} == old_ids
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_provisioning_failure_rolls_back_and_audits_orphans(tmp_path):
    adapter = FailingStartAdapter(fail_at=4)
    runtime = RoomRuntime(Database(tmp_path / "failure.db"), adapter, tmp_path / "data")
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        old_ids = {item["thread_id"] for item in source["agents"]}
        with pytest.raises(RuntimeError, match="injected"):
            await runtime.rollover(
                source["id"], RolloverRoomRequest(checkpoint="checkpoint")
            )
        restored = await runtime.db.get_room(source["id"])
        assert restored and restored["status"] == RoomStatus.FINISHED
        audit = restored["metadata"]["rollover_history"][-1]
        assert audit["state"] == "aborted"
        assert len(audit["orphaned_thread_ids"]) == 1
        assert audit["orphaned_thread_ids"][0] in adapter.archived
        assert {item["thread_id"] for item in await runtime.db.get_agents(source["id"])} == old_ids
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_duplicate_rollover_requests_resolve_to_one_successor(tmp_path):
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = RoomRuntime(Database(tmp_path / "duplicate.db"), adapter, tmp_path / "data")
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        request = RolloverRoomRequest(checkpoint="same reviewed checkpoint")
        first, second = await asyncio.gather(
            runtime.rollover(source["id"], request),
            runtime.rollover(source["id"], request),
        )
        assert first["id"] == second["id"]
        rooms = await runtime.db.list_rooms(include_archived=True)
        assert len(rooms) == 2
        assert len(await runtime.db.get_agents(first["id"])) == 2
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_database_committed_rollover_rejects_release_identity_mismatch(tmp_path):
    runtime = RoomRuntime(
        Database(tmp_path / "duplicate-release.db"),
        FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]}),
        tmp_path / "data",
    )
    await runtime.initialize()
    try:
        source = await _finished_source(runtime)
        request = RolloverRoomRequest(checkpoint="same reviewed checkpoint")
        successor = await runtime.rollover(source["id"], request)
        same = await runtime.db.reserve_rollover(source["id"], request, None)
        assert same["already_committed"] is True
        assert same["successor_room_id"] == successor["id"]
        with pytest.raises(ValueError, match="another institutional release"):
            await runtime.db.reserve_rollover(
                source["id"],
                request,
                {
                    "release_id": "different-release",
                    "manifest_sha256": "0" * 64,
                },
            )
    finally:
        await runtime.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("fully_provisioned", [False, True])
async def test_restart_recovers_staged_rollover_without_split_brain(
    tmp_path, fully_provisioned
):
    path = tmp_path / f"restart-{fully_provisioned}.db"
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = RoomRuntime(Database(path), adapter, tmp_path / "data")
    await runtime.initialize()
    source = await _finished_source(runtime)
    reservation = await runtime.db.reserve_rollover(
        source["id"], RolloverRoomRequest(checkpoint="restart checkpoint")
    )
    successor_id = reservation["successor_room_id"]
    runtime._materialize_rollover_workspace(  # noqa: SLF001 - exercise saga crash boundary
        reservation["operation_id"], successor_id, None
    )
    successor_agents = await runtime.db.get_agents(successor_id)
    provision_count = len(successor_agents) if fully_provisioned else 1
    for index, agent in enumerate(successor_agents[:provision_count], start=1):
        await runtime.db.record_rollover_thread(
            source["id"],
            reservation["operation_id"],
            successor_id,
            agent["agent_key"],
            f"thr_recovery_{index}_{fully_provisioned}",
        )
    await runtime.close()

    recovered_adapter = FakeAgentAdapter()
    recovered = RoomRuntime(Database(path), recovered_adapter, tmp_path / "data")
    await recovered.initialize()
    try:
        predecessor = await recovered.db.get_room(source["id"])
        successor = await recovered.db.get_room(successor_id)
        if fully_provisioned:
            assert predecessor and predecessor["status"] == RoomStatus.ARCHIVED
            assert successor and successor["status"] == RoomStatus.PREPARING
            assert len(
                [
                    event
                    for event in await recovered.db.get_events(successor_id)
                    if event["event_type"] == "rollover_checkpoint"
                ]
            ) == 1
        else:
            assert predecessor and predecessor["status"] == RoomStatus.FINISHED
            assert successor is None
            assert "thr_recovery_1_False" in recovered_adapter.archived
    finally:
        await recovered.close()


@pytest.mark.asyncio
async def test_restart_aborts_fully_provisioned_rollover_if_staged_release_drifted(tmp_path):
    path = tmp_path / "restart-release-drift.db"
    adapter = FakeAgentAdapter({"agent_a": [(Outcome.PASS, "")]})
    runtime = RoomRuntime(Database(path), adapter, tmp_path / "data")
    await runtime.initialize()
    source = await _finished_source(runtime)
    workspace = runtime.workspace(source["id"])
    tool = workspace / "tool.ps1"
    tool.write_text("reviewed", encoding="utf-8")
    payload = tool.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    manifest = {
        "schemaVersion": 1,
        "releaseId": "restart-release-v1",
        "createdInRoomId": source["id"],
        "description": "Recovery validation fixture.",
        "artifacts": [
            {
                "sourcePath": "tool.ps1",
                "materializeTo": "tool.ps1",
                "sha256": digest,
                "size": len(payload),
                "kind": "tool",
                "verification": {
                    "command": "focused test",
                    "result": "passed",
                    "reviewer": "independent reviewer",
                    "reviewedHash": digest,
                },
            }
        ],
        "nonInheritedState": [".room-work.json", ".room-work.lock"],
    }
    manifest_path = workspace / "institutional" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    release = publish_institutional_release(workspace, runtime.data_root)
    request = RolloverRoomRequest(
        checkpoint="restart release checkpoint",
        institutional_release_sha256=release.manifest_sha256,
    )
    reservation = await runtime.db.reserve_rollover(
        source["id"], request, release.metadata()
    )
    successor_id = reservation["successor_room_id"]
    runtime._materialize_rollover_workspace(  # noqa: SLF001
        reservation["operation_id"], successor_id, release
    )
    successor_agents = await runtime.db.get_agents(successor_id)
    expected_orphans: set[str] = set()
    for index, agent in enumerate(successor_agents, start=1):
        thread_id = f"thr_release_recovery_{index}"
        expected_orphans.add(thread_id)
        await runtime.db.record_rollover_thread(
            source["id"],
            reservation["operation_id"],
            successor_id,
            agent["agent_key"],
            thread_id,
        )
    (runtime.workspace(successor_id) / "tool.ps1").write_text("tampered", encoding="utf-8")
    await runtime.close()

    recovered_adapter = FakeAgentAdapter()
    recovered = RoomRuntime(Database(path), recovered_adapter, tmp_path / "data")
    await recovered.initialize()
    try:
        predecessor = await recovered.db.get_room(source["id"])
        assert predecessor and predecessor["status"] == RoomStatus.FINISHED
        assert await recovered.db.get_room(successor_id) is None
        assert expected_orphans <= set(recovered_adapter.archived)
        assert not recovered.workspace(successor_id).exists()
    finally:
        await recovered.close()
