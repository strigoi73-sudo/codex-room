from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from codex_room.agent import CodexAgentAdapter, sdk_server_identity
from codex_room.main import create_app
from codex_room.status_tools import (
    AVAILABLE,
    INTERACTION_REQUIRED,
    UNKNOWN,
    summarize_codex_tool_inventory,
    summarize_room_status,
)

from .fakes import FakeAgentAdapter


class _VersionedFakeAdapter(FakeAgentAdapter):
    async def initialize(self):
        return {
            "authenticated": True,
            "provider": "fake",
            "runtime": {"name": "codex-app-server", "version": "0.154.0"},
        }


def test_sdk_server_identity_reads_camel_case_sdk_metadata():
    metadata = SimpleNamespace(
        serverInfo=SimpleNamespace(name="codex-app-server", version="0.154.0")
    )

    assert sdk_server_identity(metadata) == {
        "name": "codex-app-server",
        "version": "0.154.0",
    }


def test_sdk_server_identity_normalizes_sdk_backfilled_user_agent_version():
    metadata = SimpleNamespace(
        serverInfo=SimpleNamespace(
            name="codex_cli_rs",
            version="0.154.0 (Windows 11 10.0.26100; x86_64) codex_python_sdk/0.154.0",
        ),
        userAgent=(
            "codex_cli_rs/0.154.0 (Windows 11 10.0.26100; x86_64) "
            "codex_python_sdk/0.154.0"
        ),
    )

    assert sdk_server_identity(metadata) == {
        "name": "codex_cli_rs",
        "version": "0.154.0",
    }


def test_sdk_server_identity_fails_closed_when_user_agent_disagrees():
    metadata = SimpleNamespace(
        serverInfo=SimpleNamespace(name="codex_cli_rs", version="unsafe runtime identity"),
        userAgent="different-runtime/0.154.0 (Windows 11; x86_64)",
    )

    assert sdk_server_identity(metadata) is None


def test_codex_adapter_inspects_exact_app_server_inventory_methods(tmp_path):
    class RawClient:
        def __init__(self):
            self.calls = []

        async def request(self, method, params, *, response_model):
            self.calls.append((method, params))
            payloads = {
                "modelProvider/capabilities/read": {
                    "imageGeneration": False,
                    "namespaceTools": False,
                    "webSearch": True,
                },
                "config/read": {
                    "config": {"web_search": "cached"},
                    "layers": None,
                    "origins": {},
                },
                "skills/list": {"data": []},
                "mcpServerStatus/list": {"data": [], "nextCursor": None},
                "app/installed": {"apps": []},
                "plugin/installed": {
                    "marketplaces": [],
                    "marketplaceLoadErrors": [],
                },
            }
            return response_model.model_validate(payloads[method])

    raw = RawClient()
    adapter = CodexAgentAdapter()
    adapter._client = SimpleNamespace(_client=raw)

    inventory = asyncio.run(
        adapter.inspect_tools(tmp_path, thread_id="thread_status_fixture")
    )

    assert inventory["web_search"]["status"] == AVAILABLE
    assert inventory["web_search"]["mode"] == "cached"
    assert inventory["skills"]["status"] == "unavailable"
    assert inventory["mcp"]["status"] == "unavailable"
    assert inventory["apps"]["status"] == "unavailable"
    assert inventory["plugins"]["status"] == "unavailable"
    assert {method for method, _ in raw.calls} == {
        "modelProvider/capabilities/read",
        "config/read",
        "skills/list",
        "mcpServerStatus/list",
        "app/installed",
        "plugin/installed",
    }
    params = dict(raw.calls)
    assert params["mcpServerStatus/list"]["threadId"] == "thread_status_fixture"
    assert params["app/installed"]["threadId"] == "thread_status_fixture"
    assert params["skills/list"]["cwds"] == [str(tmp_path)]


def test_codex_tool_inventory_is_classified_and_sanitized():
    inventory = summarize_codex_tool_inventory(
        {
            "provider": {"webSearch": True},
            "config": {"config": {"web_search": "cached", "secret": "do-not-expose"}},
            "skills": {
                "data": [
                    {
                        "cwd": r"C:\secret\repo",
                        "errors": [],
                        "skills": [
                            {
                                "name": "Useful Skill",
                                "scope": "repo",
                                "enabled": True,
                                "path": r"C:\secret\repo\SKILL.md",
                                "description": "private source detail",
                            }
                        ],
                    }
                ]
            },
            "mcp": {
                "data": [
                    {
                        "name": "ready-server",
                        "authStatus": "oAuth",
                        "tools": {"secret-tool-name": {"inputSchema": {"token": "hidden"}}},
                    },
                    {
                        "name": "login-server",
                        "authStatus": "notLoggedIn",
                        "tools": {"another-tool": {}},
                    },
                ],
                "nextCursor": None,
            },
            "apps": {
                "apps": [
                    {
                        "id": "private-account-like-app-id",
                        "runtimeName": "Calendar",
                        "enabled": True,
                        "callable": True,
                    }
                ]
            },
            "plugins": {
                "marketplaces": [
                    {
                        "name": "local",
                        "path": r"C:\secret\marketplace.json",
                        "plugins": [
                            {
                                "name": "Research Plugin",
                                "installed": True,
                                "enabled": True,
                                "availability": "AVAILABLE",
                                "authPolicy": "ON_USE",
                            }
                        ],
                    }
                ],
                "marketplaceLoadErrors": [],
            },
        }
    )

    assert inventory["web_search"]["status"] == AVAILABLE
    assert inventory["web_search"]["mode"] == "cached"
    assert inventory["skills"]["status"] == AVAILABLE
    assert inventory["mcp"]["status"] == AVAILABLE
    assert inventory["mcp"]["interaction_required_count"] == 1
    assert inventory["mcp"]["items"][1]["status"] == INTERACTION_REQUIRED
    assert inventory["apps"]["status"] == AVAILABLE
    assert inventory["plugins"]["status"] == AVAILABLE

    rendered = json.dumps(inventory)
    assert r"C:\\secret" not in rendered
    assert "private-account-like-app-id" not in rendered
    assert "secret-tool-name" not in rendered
    assert "inputSchema" not in rendered
    assert "do-not-expose" not in rendered


def test_failed_or_incomplete_inventory_reports_unknown_instead_of_guessing():
    inventory = summarize_codex_tool_inventory(
        {
            "provider": {"webSearch": True},
            "config": None,
            "skills": None,
            "mcp": None,
            "apps": {"apps": [{"id": "x", "runtimeName": "Maybe", "enabled": True, "callable": False}]},
            "plugins": None,
        }
    )

    assert inventory["web_search"]["status"] == UNKNOWN
    assert inventory["skills"]["status"] == UNKNOWN
    assert inventory["mcp"]["status"] == UNKNOWN
    assert inventory["apps"]["status"] == "unavailable"
    assert inventory["plugins"]["status"] == UNKNOWN


def test_room_status_summarizes_current_task_assignments_agents_and_economics():
    room = {
        "id": "room_status",
        "title": "Status room",
        "status": "running",
        "turn_count": 7,
        "max_turns": 40,
        "agents": [
            {
                "id": "a",
                "agent_key": "agent_a",
                "name": "Agent A",
                "status": "running",
                "execution": {
                    "phase": "invoking",
                    "health": "healthy",
                    "pending_count": 0,
                    "processing_count": 1,
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "medium",
                    "model_recency": "current",
                },
            }
        ],
        "events": [
            {
                "event_type": "execution_economics",
                "source": "agent_a",
                "created_at": "2026-09-19T12:00:00+00:00",
                "metadata": {
                    "tool_calls": 2,
                    "failed_tool_calls": 0,
                    "peer_invocations": 1,
                    "usage_delta_status": "computed",
                    "usage_delta": {"total_tokens": 1234, "input_tokens": 1000},
                },
            }
        ],
        "active_round": {
            "id": "round_status",
            "title": "Inspect",
            "prompt": "Understand what the Room is doing.",
            "status": "running",
            "completion_policy": "auto_settle",
            "turn_count": 3,
            "transaction_state": {
                "tasks": [
                    {
                        "id": "task_status",
                        "state": "active",
                        "required_contributors": ["agent_a"],
                        "c_cognition_ceiling": "sol-high",
                        "assignments": [
                            {
                                "id": "assignment_status",
                                "agent_key": "agent_a",
                                "state": "running",
                                "instruction": "Inspect the current implementation.",
                                "parent_assignment_id": None,
                            }
                        ],
                    }
                ]
            },
        },
    }

    status = summarize_room_status(
        room,
        coordinator_context={
            "guidance_level": "consider",
            "last_execution_input_tokens": 70000,
        },
    )

    assert status["round"]["objective"] == "Understand what the Room is doing."
    assert status["task"]["id"] == "task_status"
    assert status["task"]["assignments"][0]["agent_key"] == "agent_a"
    assert status["agents"][0]["model"] == "gpt-5.6-sol"
    assert status["recent_economics"]["agent_a"]["usage_delta"]["total_tokens"] == 1234
    assert status["coordinator_context"]["guidance_level"] == "consider"


def test_status_tools_api_is_read_only_compact_and_no_store(tmp_path):
    tool_inventory = {
        "web_search": {
            "status": "available",
            "summary": "Web search is available in cached mode.",
            "items": [],
            "mode": "cached",
        },
        "skills": {
            "status": "available",
            "summary": "1 enabled skill.",
            "items": [{"name": "Skill One", "scope": "user", "enabled": True}],
            "total_count": 1,
            "enabled_count": 1,
        },
        "mcp": {
            "status": "interaction_required",
            "summary": "One server requires authentication.",
            "items": [
                {
                    "name": "example",
                    "status": "interaction_required",
                    "auth_status": "notLoggedIn",
                    "tool_count": 3,
                }
            ],
            "total_count": 1,
            "available_count": 0,
            "interaction_required_count": 1,
        },
        "apps": {
            "status": "unavailable",
            "summary": "No installed apps.",
            "items": [],
            "total_count": 0,
            "callable_count": 0,
        },
        "plugins": {
            "status": "unavailable",
            "summary": "No installed plugins.",
            "items": [],
            "total_count": 0,
        },
    }
    adapter = _VersionedFakeAdapter(tool_inventory=tool_inventory)
    app = create_app(
        database_path=tmp_path / "status-tools.db",
        data_root=tmp_path / "data",
        adapter=adapter,
    )

    with TestClient(app) as client:
        created = client.post(
            "/api/rooms",
            json={
                "title": "Status surface",
                "topic": "Show the principal what exists.",
                "auto_start": False,
            },
        )
        assert created.status_code == 201
        room_id = created.json()["id"]

        response = client.get(f"/api/rooms/{room_id}/status-tools")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["work"]["round"]["objective"] == "Show the principal what exists."
    assert len(payload["work"]["agents"]) == 3
    assert payload["codex"]["runtime"] == {
        "name": "codex-app-server",
        "version": "0.154.0",
    }
    assert payload["codex"]["tools"]["mcp"]["status"] == INTERACTION_REQUIRED
    assert payload["room_capabilities"]
    assert {item["id"] for item in payload["room_capabilities"]} >= {
        "assert_file",
        "inspect_source",
    }
