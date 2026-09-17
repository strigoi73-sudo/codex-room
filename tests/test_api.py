from __future__ import annotations

import sqlite3
import time

from fastapi.testclient import TestClient

from codex_room.agent import ROOM_MODEL, ROOM_REASONING_EFFORT
from codex_room.main import create_app

from .fakes import FakeAgentAdapter


def test_health_exposes_runtime_provenance_and_maintenance_state(tmp_path):
    adapter = FakeAgentAdapter()
    app = create_app(
        database_path=tmp_path / "health.db",
        data_root=tmp_path / "data",
        adapter=adapter,
    )

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["codex"] == {"authenticated": True, "provider": "fake"}

    provenance = payload["provenance"]
    assert provenance["application"]["version"] == "0.1.0"
    assert len(provenance["application"]["source_fingerprint_sha256"]) == 64
    assert provenance["runtime"]["python_version"]
    assert "openai_codex_version" in provenance["runtime"]
    assert provenance["room_policy"] == {
        "model": ROOM_MODEL,
        "reasoning_effort": ROOM_REASONING_EFFORT,
    }

    watchdog = payload["maintenance"]["watchdog"]
    assert watchdog["status"] in {"starting", "healthy"}
    assert watchdog["failure_count"] == 0
    assert watchdog["consecutive_failures"] == 0
    assert watchdog["last_error"] is None


def test_http_create_state_and_exports(tmp_path):
    adapter = FakeAgentAdapter()
    app = create_app(
        database_path=tmp_path / "api.db",
        data_root=tmp_path / "data",
        adapter=adapter,
    )
    with TestClient(app) as client:
        created = client.post("/api/rooms", json={"title": "Test", "topic": "Hello"})
        assert created.status_code == 201
        payload = created.json()
        assert {agent["agent_key"] for agent in payload["agents"]} == {
            "agent_a", "agent_b", "agent_c"
        }
        assert len({agent["thread_id"] for agent in payload["agents"]}) == 3
        assert payload["active_round"]["starting_agent"] == "agent_c"
        assert payload["active_round"]["work_model_version"] == 2
        assert payload["active_round"]["provider_context_mode"] == "assignment_thread"

        room_id = payload["id"]
        state = client.get(f"/api/rooms/{room_id}")
        assert state.status_code == 200
        assert state.json()["title"] == "Test"

        json_export = client.get(f"/api/rooms/{room_id}/export?format=json")
        assert json_export.status_code == 200
        assert json_export.json()["id"] == room_id
        md_export = client.get(f"/api/rooms/{room_id}/export?format=markdown")
        assert md_export.status_code == 200
        assert "# Test" in md_export.text
        assert "Agent A thread" in md_export.text


def test_http_rejects_legacy_work_model_selection(tmp_path):
    adapter = FakeAgentAdapter()
    app = create_app(
        database_path=tmp_path / "v2-only-api.db",
        data_root=tmp_path / "data",
        adapter=adapter,
    )

    with TestClient(app) as client:
        legacy_room = client.post(
            "/api/rooms",
            json={
                "title": "Legacy request",
                "topic": "Should be rejected",
                "auto_start": False,
                "work_model_version": 1,
                "provider_context_mode": "persistent_agent_thread",
            },
        )
        assert legacy_room.status_code == 422

        persistent_context = client.post(
            "/api/rooms",
            json={
                "title": "Persistent-context request",
                "topic": "Should also be rejected",
                "auto_start": False,
                "work_model_version": 2,
                "provider_context_mode": "persistent_agent_thread",
            },
        )
        assert persistent_context.status_code == 422

        room = client.post(
            "/api/rooms",
            json={
                "title": "V2 room",
                "topic": "Use production defaults",
                "auto_start": False,
            },
        )
        assert room.status_code == 201
        room_id = room.json()["id"]

        legacy_round = client.post(
            f"/api/rooms/{room_id}/rounds",
            json={
                "title": "Legacy round request",
                "prompt": "Should also be rejected",
                "work_model_version": 1,
                "provider_context_mode": "persistent_agent_thread",
            },
        )
        assert legacy_round.status_code == 422


def test_legacy_ab_only_profile_update_preserves_c_default(tmp_path):
    adapter = FakeAgentAdapter()
    app = create_app(
        database_path=tmp_path / "legacy-profile-api.db",
        data_root=tmp_path / "data",
        adapter=adapter,
    )
    with TestClient(app) as client:
        before = client.get("/api/profiles/defaults").json()
        changed = client.put(
            "/api/profiles/defaults",
            json={
                "agent_a_name": "Legacy A",
                "agent_a_instructions": "legacy A personality",
                "agent_b_name": "Legacy B",
                "agent_b_instructions": "legacy B personality",
            },
        )
        assert changed.status_code == 200
        after = changed.json()
        assert after["agent_a"]["developer_instructions"] == "legacy A personality"
        assert after["agent_b"]["developer_instructions"] == "legacy B personality"
        assert after["agent_c"]["name"] == before["agent_c"]["name"]
        assert (
            after["agent_c"]["developer_instructions"]
            == before["agent_c"]["developer_instructions"]
        )


def test_http_new_topic_uses_v2_assignment_context(tmp_path):
    adapter = FakeAgentAdapter()
    app = create_app(
        database_path=tmp_path / "new-topic-v2.db",
        data_root=tmp_path / "data",
        adapter=adapter,
    )

    with TestClient(app) as client:
        created = client.post(
            "/api/rooms",
            json={
                "title": "Topic room",
                "topic": "Initial topic",
                "auto_start": False,
            },
        )
        assert created.status_code == 201
        room_id = created.json()["id"]

        changed = client.post(
            f"/api/rooms/{room_id}/new-topic",
            json={"topic": "Replacement topic"},
        )
        assert changed.status_code == 200
        active_round = changed.json()["active_round"]
        assert active_round["title"] == "New topic"
        assert active_round["work_model_version"] == 2
        assert active_round["provider_context_mode"] == "assignment_thread"


def test_http_profile_and_staged_round_endpoints(tmp_path):
    adapter = FakeAgentAdapter()
    app = create_app(
        database_path=tmp_path / "round-api.db",
        data_root=tmp_path / "data",
        adapter=adapter,
    )
    with TestClient(app) as client:
        profiles = client.get("/api/profiles/defaults")
        assert profiles.status_code == 200
        changed = client.put(
            "/api/profiles/defaults",
            json={
                "agent_a_name": "Explorer",
                "agent_a_instructions": "persistent A",
                "agent_b_name": "Reviewer",
                "agent_b_instructions": "persistent B",
                "agent_c_name": "Organizer",
                "agent_c_instructions": "persistent C",
            },
        )
        assert changed.status_code == 200

        room = client.post(
            "/api/rooms",
            json={"title": "Rounds", "topic": "Initial", "starting_agent": "agent_a"},
        ).json()
        deadline = time.monotonic() + 2
        while len(adapter.calls["agent_a"]) < 1 and time.monotonic() < deadline:
            time.sleep(0.01)
        time.sleep(0.05)
        baseline_calls = sum(len(calls) for calls in adapter.calls.values())
        prepared_response = client.post(
            f"/api/rooms/{room['id']}/rounds",
            json={
                "title": "Prepared via API",
                "prompt": "Public prompt",
                "agent_a_private": "A private",
                "agent_b_private": "B private",
                "starting_agent": "agent_b",
                "task_overlay": "temporary",
            },
        )
        assert prepared_response.status_code == 201
        prepared = prepared_response.json()
        assert prepared["status"] == "preparing"
        assert prepared["active_round"]["status"] == "preparing"
        assert prepared["active_round"]["work_model_version"] == 2
        assert prepared["active_round"]["provider_context_mode"] == "assignment_thread"
        assert sum(len(calls) for calls in adapter.calls.values()) == baseline_calls

        started = client.post(
            f"/api/rooms/{room['id']}/rounds/{prepared['active_round_id']}/start"
        )
        assert started.status_code == 200
        assert started.json()["active_round"]["starting_agent"] == "agent_b"
        export = client.get(f"/api/rooms/{room['id']}/export?format=json").json()
        assert len(export["rounds"]) == 2
        assert export["rounds"][1]["private_initialization"]["agent_a"]["present"] is True

def test_snapshot_returns_latest_window_and_export_returns_full_history(tmp_path):
    adapter = FakeAgentAdapter()
    database_path = tmp_path / "event-window.db"
    app = create_app(
        database_path=database_path,
        data_root=tmp_path / "data",
        adapter=adapter,
    )
    with TestClient(app) as client:
        created = client.post(
            "/api/rooms",
            json={
                "title": "Window",
                "topic": "Initial",
                "auto_start": False,
            },
        )
        assert created.status_code == 201
        room = created.json()
        room_id = room["id"]
        round_id = room["active_round_id"]

        with sqlite3.connect(database_path) as connection:
            existing_count, max_sequence = connection.execute(
                """SELECT COUNT(*), COALESCE(MAX(sequence_no), 0)
                   FROM events WHERE room_id=?""",
                (room_id,),
            ).fetchone()
            connection.executemany(
                """INSERT INTO events
                   (id, room_id, discussion_id, created_at, event_type, source,
                    destination, content, related_event_id, status, metadata_json,
                    round_id, sequence_no)
                   VALUES (?, ?, ?, ?, 'bulk_test_event', 'room', 'observer',
                           ?, NULL, 'recorded', '{}', ?, ?)""",
                [
                    (
                        f"bulk-{offset}",
                        room_id,
                        round_id,
                        room["created_at"],
                        f"bulk event {offset}",
                        round_id,
                        max_sequence + offset,
                    )
                    for offset in range(1, 2006)
                ],
            )
            connection.commit()

        expected_total = existing_count + 2005

        state = client.get(f"/api/rooms/{room_id}")
        assert state.status_code == 200
        snapshot = state.json()
        assert len(snapshot["events"]) == 2000
        assert snapshot["events"][0]["id"] == "bulk-6"
        assert snapshot["events"][-1]["id"] == "bulk-2005"
        assert snapshot["event_window"] == {
            "limit": 2000,
            "total": expected_total,
            "returned": 2000,
            "truncated": True,
            "first_sequence_no": max_sequence + 6,
            "last_sequence_no": max_sequence + 2005,
        }

        exported_response = client.get(f"/api/rooms/{room_id}/export?format=json")
        assert exported_response.status_code == 200
        exported = exported_response.json()
        assert len(exported["events"]) == expected_total
        assert exported["event_window"]["limit"] is None
        assert exported["event_window"]["total"] == expected_total
        assert exported["event_window"]["returned"] == expected_total
        assert exported["event_window"]["truncated"] is False
        assert any(event["id"] == "bulk-1" for event in exported["events"])
        assert exported["events"][-1]["id"] == "bulk-2005"

