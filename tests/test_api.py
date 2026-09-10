from __future__ import annotations

import time

from fastapi.testclient import TestClient

from codex_room.main import create_app

from .fakes import FakeAgentAdapter


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
        assert payload["agents"][0]["thread_id"] != payload["agents"][1]["thread_id"]

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
        assert sum(len(calls) for calls in adapter.calls.values()) == baseline_calls

        started = client.post(
            f"/api/rooms/{room['id']}/rounds/{prepared['active_round_id']}/start"
        )
        assert started.status_code == 200
        assert started.json()["active_round"]["starting_agent"] == "agent_b"
        export = client.get(f"/api/rooms/{room['id']}/export?format=json").json()
        assert len(export["rounds"]) == 2
        assert export["rounds"][1]["private_initialization"]["agent_a"]["present"] is True
