from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from codex_room.capabilities import (
    CapabilityUsageError,
    assert_file,
    inspect_capability,
    invoke_capability,
    list_capabilities,
    main,
)


def test_assert_file_combines_exact_hash_and_json_checks(tmp_path: Path) -> None:
    artifact = tmp_path / "result.json"
    artifact.write_text('{"id": 7, "status": "ok"}', encoding="utf-8")
    expected_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()

    result = assert_file(
        tmp_path,
        "result.json",
        exists=True,
        sha256_equals=expected_hash,
        json_valid=True,
        required_keys=["id", "status"],
    )

    assert result["ok"] is True
    assert result["subject"]["sha256"] == expected_hash
    assert [check["name"] for check in result["checks"]] == [
        "exists",
        "sha256_equals",
        "json_valid",
        "json_required_key",
        "json_required_key",
    ]
    assert all(check["ok"] for check in result["checks"])


def test_assert_file_reports_false_assertion_without_execution_error(tmp_path: Path) -> None:
    artifact = tmp_path / "result.json"
    artifact.write_text('{"id": 7}', encoding="utf-8")

    result = assert_file(
        tmp_path,
        "result.json",
        json_valid=True,
        required_keys=["missing"],
    )

    assert result["ok"] is False
    missing = result["checks"][-1]
    assert missing["name"] == "json_required_key"
    assert missing["actual"] is False


@pytest.mark.parametrize("path", ["../outside.txt", "/tmp/outside.txt"])
def test_assert_file_rejects_workspace_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises(CapabilityUsageError, match="Room workspace"):
        assert_file(tmp_path, path, exists=True)


def test_cli_emits_one_machine_readable_result(tmp_path: Path, monkeypatch, capsys) -> None:
    artifact = tmp_path / "data.json"
    artifact.write_text('{"id": 1}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["assert-file", "data.json", "--json-valid", "--required-key", "id"])

    assert exit_code == 0
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    payload = json.loads(output[0])
    assert payload["codex_room_capability"] == 1
    assert payload["capability"] == "assert_file"
    assert payload["ok"] is True


def test_exists_assertion_requires_regular_file(tmp_path: Path) -> None:
    directory = tmp_path / "artifact"
    directory.mkdir()

    result = assert_file(tmp_path, "artifact", exists=True)

    assert result["ok"] is False
    assert result["subject"]["exists"] is True
    assert result["subject"]["is_file"] is False
    assert result["checks"][0]["actual"] is False



def test_registry_exposes_assert_file_as_versioned_core_capability() -> None:
    registry = list_capabilities()

    assert registry["codex_room_registry"] == 1
    assert registry["operation"] == "list"
    assert len(registry["capabilities"]) == 1
    manifest = registry["capabilities"][0]
    assert manifest["id"] == "assert_file"
    assert manifest["origin"] == "core"
    assert manifest["scope"] == "core"
    assert manifest["version"] == "1"
    assert len(manifest["implementation_sha256"]) == 64
    assert manifest["permissions"] == {
        "workspace_read": True,
        "workspace_write": False,
        "network": False,
        "external_process": False,
    }
    assert manifest["side_effects"] == "none"
    assert manifest["verification"]["status"] == "verified"
    assert manifest["input_schema"]["required"] == ["path"]


def test_inspect_and_invoke_share_exact_registered_version(tmp_path: Path) -> None:
    artifact = tmp_path / "registered.json"
    artifact.write_text('{"probe": "P4.2"}', encoding="utf-8")

    inspected = inspect_capability("assert_file")["capability"]
    invoked = invoke_capability(
        tmp_path,
        "assert_file",
        {
            "path": "registered.json",
            "exists": True,
            "json_valid": True,
            "required_keys": ["probe"],
        },
    )

    assert invoked["ok"] is True
    assert invoked["capability_version"] == inspected["version"]
    assert invoked["implementation_sha256"] == inspected["implementation_sha256"]


def test_registered_invoke_rejects_unknown_input_fields(tmp_path: Path) -> None:
    with pytest.raises(CapabilityUsageError, match="unknown assert_file input field"):
        invoke_capability(
            tmp_path,
            "assert_file",
            {"path": "result.json", "invented": True},
        )


@pytest.mark.parametrize(
    ("argv", "expected_operation"),
    [
        (["list"], "list"),
        (["inspect", "assert_file"], "inspect"),
    ],
)
def test_registry_cli_emits_machine_readable_discovery(
    argv: list[str], expected_operation: str, capsys
) -> None:
    exit_code = main(argv)

    assert exit_code == 0
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    payload = json.loads(output[0])
    assert payload["codex_room_registry"] == 1
    assert payload["operation"] == expected_operation


def test_registry_cli_invokes_by_manifest_id(tmp_path: Path, monkeypatch, capsys) -> None:
    artifact = tmp_path / "probe.json"
    artifact.write_text('{"probe": "P4.2"}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "invoke",
            "assert_file",
            "--input-json",
            json.dumps(
                {
                    "path": "probe.json",
                    "exists": True,
                    "json_valid": True,
                    "required_keys": ["probe"],
                }
            ),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["codex_room_capability"] == 1
    assert payload["capability"] == "assert_file"
    assert payload["capability_version"] == "1"
    assert len(payload["implementation_sha256"]) == 64
    assert payload["ok"] is True
