from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import codex_room.custom_capability_registration as registration
from codex_room.custom_capabilities import DRAFTS_PATH
from codex_room.custom_capability_registration import (
    CustomCapabilityPublicationError,
    CustomCapabilityVerificationError,
    VerificationReceipt,
    publish_verified_custom_capability,
    verify_custom_capability_draft,
)


def _manifest(capability_id: str = "count_lines") -> dict:
    return {
        "schema_version": 1,
        "id": capability_id,
        "version": "1",
        "description": "Count lines in explicit text or a workspace text file.",
        "scope": "lineage",
        "runtime": {
            "kind": "python",
            "entrypoint": "capability.py",
            "protocol": "stdio-json-v1",
        },
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "path": {"type": "string"},
            },
        },
        "output_schema": {
            "type": "object",
            "required": ["ok", "count"],
            "properties": {
                "ok": {"type": "boolean"},
                "count": {"type": "integer"},
            },
        },
        "durable_result_fields": ["count"],
        "permissions": {
            "workspace_read": True,
            "workspace_write": False,
            "network": False,
            "external_process": False,
        },
        "side_effects": "none",
    }


def _code() -> str:
    return """import json
import sys
from pathlib import Path

request = json.load(sys.stdin)
if "path" in request:
    text = Path(request["path"]).read_text(encoding="utf-8")
else:
    text = request["text"]
print(json.dumps({"ok": True, "count": len(text.splitlines())}, sort_keys=True))
"""


def _write_draft(
    workspace: Path,
    *,
    capability_id: str = "count_lines",
    code: str | None = None,
) -> Path:
    root = workspace.joinpath(*DRAFTS_PATH.parts, capability_id)
    root.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps(_manifest(capability_id), sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    (root / "capability.py").write_text(code or _code(), encoding="utf-8")
    return root


def _cases() -> list[dict]:
    return [
        {
            "name": "inline",
            "input": {"text": "one\ntwo\nthree\n"},
            "expected_output": {"ok": True, "count": 3},
        },
        {
            "name": "fixture",
            "input": {"path": "notes/sample.txt"},
            "expected_output": {"ok": True, "count": 2},
            "files": {"notes/sample.txt": "alpha\nbeta\n"},
        },
    ]


def test_verifier_runs_exact_cases_and_emits_hash_only_receipt(tmp_path: Path) -> None:
    _write_draft(tmp_path)

    receipt = verify_custom_capability_draft(tmp_path, "count_lines", _cases())

    assert receipt.verification_sha256 == hashlib.sha256(
        json.dumps(
            receipt.payload(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert receipt.payload()["case_count"] == 2
    assert [item["name"] for item in receipt.cases] == ["inline", "fixture"]
    assert all(item["expected_output_sha256"] == item["observed_output_sha256"] for item in receipt.cases)
    assert "one\ntwo" not in receipt.as_bytes().decode("utf-8")
    assert not any(path.name.startswith(".codex-room-verify-") for path in tmp_path.iterdir())


def test_verifier_rejects_output_mismatch(tmp_path: Path) -> None:
    _write_draft(tmp_path)
    cases = _cases()
    cases[0]["expected_output"]["count"] = 99

    with pytest.raises(CustomCapabilityVerificationError, match="did not match"):
        verify_custom_capability_draft(tmp_path, "count_lines", cases)


def test_verifier_requires_expected_durable_fields(tmp_path: Path) -> None:
    _write_draft(tmp_path)
    cases = _cases()
    cases[0]["expected_output"].pop("count")

    with pytest.raises(CustomCapabilityVerificationError, match="durable result fields"):
        verify_custom_capability_draft(tmp_path, "count_lines", cases)


@pytest.mark.parametrize("unsafe_path", ["../outside.txt", "C:/outside.txt", "folder\\file.txt", "con"])
def test_verifier_rejects_unsafe_fixture_paths(
    tmp_path: Path, unsafe_path: str
) -> None:
    _write_draft(tmp_path)
    cases = _cases()
    cases[0]["files"] = {unsafe_path: "unsafe"}

    with pytest.raises(CustomCapabilityVerificationError, match="fixture path"):
        verify_custom_capability_draft(tmp_path, "count_lines", cases)


def test_verifier_rejects_stderr_even_with_matching_json(tmp_path: Path) -> None:
    _write_draft(
        tmp_path,
        code=(
            "import json, sys\n"
            "json.load(sys.stdin)\n"
            "print('debug', file=sys.stderr)\n"
            "print(json.dumps({'ok': True, 'count': 3}))\n"
        ),
    )

    with pytest.raises(CustomCapabilityVerificationError, match="stderr"):
        verify_custom_capability_draft(tmp_path, "count_lines", [_cases()[0]])


def test_verifier_timeout_is_bounded(tmp_path: Path, monkeypatch) -> None:
    _write_draft(
        tmp_path,
        code=(
            "import json, sys, time\n"
            "json.load(sys.stdin)\n"
            "time.sleep(0.2)\n"
            "print(json.dumps({'ok': True, 'count': 3}))\n"
        ),
    )
    monkeypatch.setattr(registration, "CASE_TIMEOUT_SECONDS", 0.01)

    with pytest.raises(CustomCapabilityVerificationError, match="time limit"):
        verify_custom_capability_draft(tmp_path, "count_lines", [_cases()[0]])


def test_verifier_detects_draft_mutation_during_execution(tmp_path: Path) -> None:
    mutating = """import json
import sys
from pathlib import Path

json.load(sys.stdin)
workspace = Path(__file__).resolve().parents[2]
draft = workspace / ".codex-room" / "capability-drafts" / "count_lines" / "capability.py"
draft.write_text(draft.read_text(encoding="utf-8") + "\\n# mutated", encoding="utf-8")
print(json.dumps({"ok": True, "count": 3}))
"""
    _write_draft(tmp_path, code=mutating)

    with pytest.raises(CustomCapabilityVerificationError, match="changed during verification"):
        verify_custom_capability_draft(tmp_path, "count_lines", [_cases()[0]])


def test_receipt_parser_rejects_tampering(tmp_path: Path) -> None:
    _write_draft(tmp_path)
    receipt = verify_custom_capability_draft(tmp_path, "count_lines", _cases())
    raw = receipt.as_dict()
    raw["cases"][0]["name"] = "tampered"

    with pytest.raises(CustomCapabilityVerificationError, match="hash"):
        VerificationReceipt.from_dict(raw)


def test_publish_creates_content_addressed_package_verification_and_registration(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    data_root = tmp_path / "data"
    _write_draft(workspace)
    receipt = verify_custom_capability_draft(workspace, "count_lines", _cases())

    published = publish_verified_custom_capability(
        workspace,
        data_root,
        "room_abc123",
        "count_lines",
        receipt,
    )

    package_root = data_root / "custom-capabilities" / "packages" / published.package_sha256
    verification_file = (
        data_root
        / "custom-capabilities"
        / "verifications"
        / f"{receipt.verification_sha256}.json"
    )
    registration_file = (
        data_root
        / "custom-capabilities"
        / "registrations"
        / f"{published.registration_sha256}.json"
    )
    assert sorted(path.name for path in package_root.iterdir()) == [
        "capability.py",
        "manifest.json",
    ]
    assert hashlib.sha256((package_root / "capability.py").read_bytes()).hexdigest() == published.implementation_sha256
    assert json.loads(verification_file.read_text(encoding="utf-8")) == receipt.as_dict()
    assert json.loads(registration_file.read_text(encoding="utf-8")) == published.as_dict()
    assert published.room_id == "room_abc123"
    assert published.capability_id == "count_lines"


def test_publish_is_idempotent_for_same_exact_registration(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    data_root = tmp_path / "data"
    _write_draft(workspace)
    receipt = verify_custom_capability_draft(workspace, "count_lines", _cases())

    first = publish_verified_custom_capability(
        workspace, data_root, "room_repeat", "count_lines", receipt
    )
    second = publish_verified_custom_capability(
        workspace, data_root, "room_repeat", "count_lines", receipt
    )

    assert first == second
    assert len(list((data_root / "custom-capabilities" / "packages").glob("[0-9a-f]*"))) == 1
    assert len(list((data_root / "custom-capabilities" / "verifications").glob("*.json"))) == 1
    assert len(list((data_root / "custom-capabilities" / "registrations").glob("*.json"))) == 1


def test_publish_rejects_receipt_after_draft_changes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    data_root = tmp_path / "data"
    root = _write_draft(workspace)
    receipt = verify_custom_capability_draft(workspace, "count_lines", _cases())
    (root / "capability.py").write_text(_code() + "\n# changed\n", encoding="utf-8")

    with pytest.raises(CustomCapabilityPublicationError, match="does not match"):
        publish_verified_custom_capability(
            workspace, data_root, "room_changed", "count_lines", receipt
        )


def test_publish_rejects_corrupt_existing_content_addressed_package(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    data_root = tmp_path / "data"
    _write_draft(workspace)
    receipt = verify_custom_capability_draft(workspace, "count_lines", _cases())
    first = publish_verified_custom_capability(
        workspace, data_root, "room_corrupt", "count_lines", receipt
    )
    package_root = data_root / "custom-capabilities" / "packages" / first.package_sha256
    (package_root / "capability.py").write_text("corrupt", encoding="utf-8")

    with pytest.raises(CustomCapabilityPublicationError, match="bytes"):
        publish_verified_custom_capability(
            workspace, data_root, "room_corrupt", "count_lines", receipt
        )
