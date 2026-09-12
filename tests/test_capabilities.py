from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import codex_room.capabilities as capabilities
from codex_room.capabilities import (
    CapabilityUsageError,
    assert_file,
    find_files,
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
    assert [item["id"] for item in registry["capabilities"]] == [
        "assert_file",
        "find_files",
    ]
    manifest = registry["capabilities"][0]
    assert manifest["id"] == "assert_file"
    assert manifest["origin"] == "core"
    assert manifest["scope"] == "core"
    assert manifest["version"] == "1"
    assert len(manifest["implementation_sha256"]) == 64
    assert "permissions" not in manifest
    assert "input_schema" not in manifest
    inspected = inspect_capability("assert_file")["capability"]
    assert inspected["permissions"] == {
        "workspace_read": True,
        "workspace_write": False,
        "network": False,
        "external_process": False,
    }
    assert inspected["side_effects"] == "none"
    assert inspected["verification"]["status"] == "verified"
    assert inspected["input_schema"]["required"] == ["path"]
    assert inspected["durable_result_fields"] == ["subject", "checks"]


def test_find_files_filters_globs_hidden_paths_and_size(tmp_path: Path) -> None:
    (tmp_path / "root.md").write_text("root", encoding="utf-8")
    (tmp_path / "root.txt").write_text("text", encoding="utf-8")
    (tmp_path / ".hidden.md").write_text("hidden", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("alpha", encoding="utf-8")
    (docs / "b.txt").write_text("beta", encoding="utf-8")
    hidden_docs = docs / ".hidden"
    hidden_docs.mkdir()
    (hidden_docs / "secret.md").write_text("secret", encoding="utf-8")
    nested = docs / "sub"
    nested.mkdir()
    (nested / "c.md").write_text("charlie", encoding="utf-8")

    result = find_files(
        tmp_path,
        include_globs=["**/*.md"],
        exclude_globs=["docs/sub/**"],
        min_size_bytes=4,
        max_size_bytes=5,
    )

    assert result["ok"] is True
    assert result["evidence"]["truncated"] is False
    assert result["evidence"]["truncation_reason"] is None
    assert result["evidence"]["symlinks_followed"] is False
    assert [item["path"] for item in result["evidence"]["matches"]] == [
        "root.md",
        "docs/a.md",
    ]
    assert [item["size_bytes"] for item in result["evidence"]["matches"]] == [4, 5]


def test_find_files_hidden_files_are_opt_in(tmp_path: Path) -> None:
    (tmp_path / ".hidden.txt").write_text("hidden", encoding="utf-8")
    (tmp_path / "visible.txt").write_text("visible", encoding="utf-8")

    default_result = find_files(tmp_path, include_globs=["*.txt"])
    hidden_result = find_files(
        tmp_path,
        include_globs=["*.txt"],
        include_hidden=True,
    )

    assert [item["path"] for item in default_result["evidence"]["matches"]] == [
        "visible.txt"
    ]
    assert [item["path"] for item in hidden_result["evidence"]["matches"]] == [
        ".hidden.txt",
        "visible.txt",
    ]


def test_find_files_reports_explicit_result_truncation(tmp_path: Path) -> None:
    for name in ("a.txt", "b.txt", "c.txt"):
        (tmp_path / name).write_text(name, encoding="utf-8")

    result = find_files(tmp_path, include_globs=["*.txt"], max_results=2)

    assert [item["path"] for item in result["evidence"]["matches"]] == [
        "a.txt",
        "b.txt",
    ]
    assert result["evidence"]["returned_count"] == 2
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "max_results"


def test_find_files_reports_explicit_scan_limit_truncation(
    tmp_path: Path, monkeypatch
) -> None:
    for name in ("a.txt", "b.txt", "c.txt"):
        (tmp_path / name).write_text(name, encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_FIND_FILES_SCANNED_ENTRIES", 2)

    result = find_files(tmp_path, include_globs=["*.txt"], max_results=10)

    assert [item["path"] for item in result["evidence"]["matches"]] == [
        "a.txt",
        "b.txt",
    ]
    assert result["evidence"]["scanned_entries"] == 2
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "scan_limit"


@pytest.mark.parametrize("path", ["../outside", "/tmp/outside"])
def test_find_files_rejects_workspace_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises(CapabilityUsageError, match="Room workspace"):
        find_files(tmp_path, path)


def test_registered_find_files_exposes_bounded_read_only_contract(tmp_path: Path) -> None:
    artifact = tmp_path / "probe.json"
    artifact.write_text('{"probe": true}', encoding="utf-8")

    inspected = inspect_capability("find_files")["capability"]
    invoked = invoke_capability(
        tmp_path,
        "find_files",
        {
            "include_globs": ["**/*.json"],
            "max_results": 10,
        },
    )

    assert inspected["origin"] == "core"
    assert inspected["scope"] == "core"
    assert inspected["version"] == "1"
    assert inspected["durable_result_fields"] == ["evidence"]
    assert inspected["permissions"] == {
        "workspace_read": True,
        "workspace_write": False,
        "network": False,
        "external_process": False,
    }
    assert inspected["side_effects"] == "none"
    assert inspected["verification"] == {"status": "verified", "evidence": ["E-032"]}
    assert invoked["capability_version"] == inspected["version"]
    assert invoked["implementation_sha256"] == inspected["implementation_sha256"]
    assert invoked["durable_result_fields"] == ["evidence"]
    assert [item["path"] for item in invoked["evidence"]["matches"]] == ["probe.json"]


@pytest.mark.parametrize(
    ("inputs", "match"),
    [
        ({"invented": True}, "unknown find_files input field"),
        ({"include_globs": "*.txt"}, "include_globs"),
        ({"exclude_globs": ["../*.txt"]}, "workspace-relative glob"),
        ({"include_hidden": 1}, "include_hidden"),
        ({"min_size_bytes": -1}, "min_size_bytes"),
        ({"min_size_bytes": 10, "max_size_bytes": 5}, "must not exceed"),
        ({"max_results": 0}, "max_results"),
        ({"max_results": 1001}, "max_results"),
    ],
)
def test_registered_find_files_rejects_invalid_inputs(
    tmp_path: Path, inputs: dict[str, object], match: str
) -> None:
    with pytest.raises(CapabilityUsageError, match=match):
        invoke_capability(tmp_path, "find_files", inputs)


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
    assert invoked["durable_result_fields"] == inspected["durable_result_fields"]


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
    assert payload["durable_result_fields"] == ["subject", "checks"]
    assert payload["ok"] is True
