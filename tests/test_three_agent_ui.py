from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from codex_room.exporter import as_markdown
from codex_room.main import create_app

from .fakes import FakeAgentAdapter


ROOT = Path(__file__).resolve().parents[1]


def _snapshot(agent_keys: tuple[str, ...]) -> dict:
    agents = [
        {
            "agent_key": key,
            "name": f"Name {key[-1].upper()}",
            "thread_id": f"thread-{key[-1]}",
            "profile_id": f"profile-{key[-1]}",
        }
        for key in agent_keys
    ]
    return {
        "id": "room-one",
        "title": "Membership export",
        "created_at": "2026-09-06T00:00:00Z",
        "status": "running",
        "topic": "Future prompt",
        "agents": agents,
        "rounds": [
            {
                "id": "round-one",
                "title": "Round",
                "status": "active",
                "starting_agent": "either",
                "turn_count": 1,
                "consecutive_passes": 0,
                "prompt": "Future prompt",
                "events": [
                    {
                        "id": "event-one",
                        "source": agent_keys[-1],
                        "destination": "all",
                        "created_at": "2026-09-06T00:01:00Z",
                        "event_type": "agent_message",
                        "event_class": "conversation",
                        "counts_as_turn": True,
                        "counts_toward_pass": False,
                        "metadata": {},
                        "content": "Independent contribution",
                    }
                ],
            }
        ],
    }


def test_markdown_export_uses_ordered_snapshot_membership() -> None:
    markdown = as_markdown(_snapshot(("agent_a", "agent_b", "agent_c")))
    assert markdown.index("Agent A thread") < markdown.index("Agent B thread") < markdown.index("Agent C thread")
    assert "- Agent C thread: `thread-c`" in markdown
    assert "- Agent C profile: `profile-c`" in markdown
    assert "#### Name C → all" in markdown


def test_markdown_export_keeps_two_agent_snapshots_two_agent() -> None:
    markdown = as_markdown(_snapshot(("agent_a", "agent_b")))
    assert "Agent A thread" in markdown and "Agent B thread" in markdown
    assert "Agent C thread" not in markdown


def test_static_ui_exposes_explicit_addition_and_dynamic_membership_hooks() -> None:
    html = (ROOT / "codex_room" / "static" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "codex_room" / "static" / "app.js").read_text(encoding="utf-8")
    assert 'name="include_agent_c"' in html
    assert 'id="add-agent-c"' in html
    assert 'id="agent-strip"' in html
    assert '<option value="all">All agents</option>' in html
    assert 'roomAction("agents", { agent_key: "agent_c" })' in javascript
    assert 'new Option("All participants independently", "either")' in javascript
    assert "without running any agent" in html
    assert "without running either agent" not in html
    assert "renderAgentStrip(room.agents || [])" in javascript
    assert "participant_private" in javascript and "participant_overlays" in javascript
    assert "executionSummary(agent.execution)" in javascript
    assert "Execution: ${phase} · ${health}" in javascript
    assert "execution.reason" in javascript
    assert 'setAttribute("aria-label", `${execution.text}. ${execution.title}`)' in javascript


def test_http_join_snapshot_and_ui_contract_integrate_without_activation(tmp_path: Path) -> None:
    adapter = FakeAgentAdapter()
    app = create_app(
        database_path=tmp_path / "ui-integration.db",
        data_root=tmp_path / "data",
        adapter=adapter,
    )
    with TestClient(app) as client:
        profiles = client.get("/api/profiles/defaults").json()
        assert "The Integrator" in profiles["agent_c"]["developer_instructions"]

        created = client.post(
            "/api/rooms",
            json={"title": "Expandable", "topic": "Old topic", "auto_start": False},
        ).json()
        original_ids = {agent["agent_key"]: agent["thread_id"] for agent in created["agents"]}
        assert set(original_ids) == {"agent_a", "agent_b"}

        joined_response = client.post(
            f"/api/rooms/{created['id']}/agents", json={"agent_key": "agent_c"}
        )
        assert joined_response.status_code == 201
        joined = joined_response.json()
        joined_ids = {agent["agent_key"]: agent["thread_id"] for agent in joined["agents"]}
        assert joined_ids["agent_a"] == original_ids["agent_a"]
        assert joined_ids["agent_b"] == original_ids["agent_b"]
        assert joined_ids["agent_c"] not in set(original_ids.values())
        assert adapter.calls["agent_c"] == []

        markdown = client.get(
            f"/api/rooms/{created['id']}/export?format=markdown"
        ).text
        assert f"- Agent C thread: `{joined_ids['agent_c']}`" in markdown
        assert client.get("/").status_code == 200
        assert client.get("/app.js").status_code == 200
