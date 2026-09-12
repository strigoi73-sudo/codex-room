from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from codex_room.capabilities import CapabilityUsageError, assert_file, main


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
