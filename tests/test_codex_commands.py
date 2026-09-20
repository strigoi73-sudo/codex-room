from __future__ import annotations

import base64
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from codex_room.codex_commands import (
    CodexCommandCatalog,
    parse_slash_command_source,
    sdk_server_identity,
)
from codex_room.main import create_app

from .fakes import FakeAgentAdapter


SOURCE = r'''
#[strum(serialize_all = "kebab-case")]
pub enum SlashCommand {
    Model,
    #[strum(to_string = "pwd", serialize = "cwd")]
    Pwd,
    #[strum(to_string = "stop", serialize = "clean")]
    Stop,
    DebugConfig,
    Side,
    Btw,
}

impl SlashCommand {
    pub fn description(self) -> &'static str {
        match self {
            SlashCommand::Model => "choose model",
            SlashCommand::Pwd => "show directory",
            SlashCommand::Stop => "stop terminals",
            SlashCommand::DebugConfig => "show config",
            SlashCommand::Side | SlashCommand::Btw => {
                "start a side conversation"
            }
        }
    }
}
'''


def _source_payload() -> dict[str, str]:
    return {
        "encoding": "base64",
        "sha": "a" * 40,
        "content": base64.b64encode(SOURCE.encode("utf-8")).decode("ascii"),
    }


def test_parser_preserves_order_canonical_names_aliases_and_descriptions():
    commands = parse_slash_command_source(SOURCE)

    assert [item["command"] for item in commands] == [
        "model",
        "pwd",
        "stop",
        "debug-config",
        "side",
        "btw",
    ]
    assert commands[1]["aliases"] == ["cwd"]
    assert commands[2]["aliases"] == ["clean"]
    assert commands[3]["display"] == "/debug-config"
    assert commands[4]["description"] == "start a side conversation"
    assert commands[5]["description"] == "start a side conversation"
    assert [item["presentation_order"] for item in commands] == list(range(6))


def test_exact_version_catalog_syncs_then_uses_cache(tmp_path):
    requested: list[str] = []

    def fetch_json(url: str) -> dict[str, str]:
        requested.append(url)
        assert parse_qs(urlparse(url).query)["ref"] == ["rust-v0.154.0"]
        return _source_payload()

    catalog = CodexCommandCatalog(tmp_path, fetch_json=fetch_json)
    first = catalog.resolve("0.154.0")
    second = catalog.resolve("0.154.0")

    assert first["status"] == "current"
    assert first["loaded_from"] == "upstream"
    assert first["runtime_version"] == "0.154.0"
    assert first["source_ref"] == "rust-v0.154.0"
    assert first["source_blob_sha"] == "a" * 40
    assert first["command_count"] == 6
    assert first["dynamic_overlays"] == [
        {
            "kind": "model_service_tiers",
            "source": "live_model_catalog",
            "included": False,
        }
    ]

    assert second["status"] == "current"
    assert second["loaded_from"] == "cache"
    assert len(requested) == 1


def test_new_runtime_never_falls_back_to_an_older_cached_catalog(tmp_path):
    def fetch_json(url: str) -> dict[str, str]:
        ref = parse_qs(urlparse(url).query)["ref"][0]
        if ref == "rust-v0.154.0":
            return _source_payload()
        raise OSError("offline")

    catalog = CodexCommandCatalog(tmp_path, fetch_json=fetch_json)
    assert catalog.resolve("0.154.0")["status"] == "current"

    changed = catalog.resolve("0.155.0")

    assert changed == {
        "status": "unavailable",
        "runtime_version": "0.155.0",
        "source_ref": "rust-v0.155.0",
        "error_code": "sync_failed",
        "reason": "Exact command catalog could not be synchronized for Codex 0.155.0.",
        "command_count": 0,
        "commands": [],
    }


def test_unknown_or_unsafe_runtime_version_fails_closed(tmp_path):
    catalog = CodexCommandCatalog(
        tmp_path,
        fetch_json=lambda _: (_ for _ in ()).throw(AssertionError("must not fetch")),
    )

    missing = catalog.resolve(None)
    unsafe = catalog.resolve("../../main")

    assert missing["status"] == "unavailable"
    assert missing["error_code"] == "runtime_version_unavailable"
    assert unsafe["status"] == "unavailable"
    assert unsafe["error_code"] == "runtime_version_unavailable"


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


class _VersionedFakeAdapter(FakeAgentAdapter):
    async def initialize(self):
        return {
            "authenticated": True,
            "provider": "fake",
            "runtime": {"name": "codex-app-server", "version": "0.154.0"},
        }


class _StubCatalog:
    def __init__(self) -> None:
        self.versions: list[str | None] = []

    def resolve(self, version: str | None):
        self.versions.append(version)
        return {
            "status": "current",
            "runtime_version": version,
            "command_count": 1,
            "commands": [{"command": "status", "display": "/status"}],
        }


def test_commands_api_binds_catalog_to_running_runtime_version(tmp_path):
    catalog = _StubCatalog()
    app = create_app(
        database_path=tmp_path / "commands.db",
        data_root=tmp_path / "data",
        adapter=_VersionedFakeAdapter(),
        command_catalog=catalog,
    )

    with TestClient(app) as client:
        response = client.get("/api/codex/commands")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["runtime_version"] == "0.154.0"
    assert catalog.versions == ["0.154.0"]
