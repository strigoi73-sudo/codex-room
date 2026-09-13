from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from codex_room.custom_capabilities import (
    DRAFTS_PATH,
    CustomCapabilityPackageError,
    draft_path,
    load_custom_capability_draft,
)


def _manifest(capability_id: str = "count_lines") -> dict:
    return {
        "schema_version": 1,
        "id": capability_id,
        "version": "1",
        "description": "Count lines in explicit input text.",
        "scope": "lineage",
        "runtime": {
            "kind": "python",
            "entrypoint": "capability.py",
            "protocol": "stdio-json-v1",
        },
        "input_schema": {
            "type": "object",
            "required": ["text"],
            "properties": {"text": {"type": "string"}},
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
            "workspace_read": False,
            "workspace_write": False,
            "network": False,
            "external_process": False,
        },
        "side_effects": "none",
    }


def _write_draft(
    workspace: Path,
    *,
    capability_id: str = "count_lines",
    manifest: dict | None = None,
    code: str = "import json, sys\nrequest = json.load(sys.stdin)\nprint(json.dumps({'ok': True, 'count': len(request['text'].splitlines())}))\n",
) -> tuple[Path, bytes, bytes]:
    root = workspace.joinpath(*DRAFTS_PATH.parts, capability_id)
    root.mkdir(parents=True)
    manifest_bytes = json.dumps(
        manifest or _manifest(capability_id),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    entrypoint_bytes = code.encode("utf-8")
    (root / "manifest.json").write_bytes(manifest_bytes)
    (root / "capability.py").write_bytes(entrypoint_bytes)
    return root, manifest_bytes, entrypoint_bytes


def test_valid_draft_has_exact_manifest_implementation_and_package_identity(tmp_path: Path) -> None:
    _, manifest_bytes, entrypoint_bytes = _write_draft(tmp_path)

    package = load_custom_capability_draft(tmp_path, "count_lines")

    assert package.summary() == {
        "id": "count_lines",
        "origin": "custom",
        "scope": "lineage",
        "version": "1",
        "implementation_sha256": hashlib.sha256(entrypoint_bytes).hexdigest(),
        "package_sha256": package.package_sha256,
    }
    assert package.manifest_sha256 == hashlib.sha256(manifest_bytes).hexdigest()
    digest = hashlib.sha256()
    digest.update(b"codex-room-custom-capability-package-v1\x00")
    digest.update(b"manifest.json\x00")
    digest.update(manifest_bytes)
    digest.update(b"\x00capability.py\x00")
    digest.update(entrypoint_bytes)
    assert package.package_sha256 == digest.hexdigest()
    assert package.durable_result_fields == ("count",)
    assert package.manifest()["permission_enforcement"] == {
        "mode": "ambient_room_sandbox",
        "per_capability_enforcement": False,
    }


def test_draft_path_rejects_path_traversal_identifiers(tmp_path: Path) -> None:
    with pytest.raises(CustomCapabilityPackageError, match="capability id"):
        draft_path(tmp_path, "../outside")


@pytest.mark.parametrize("capability_id", ["Uppercase", "has-dash", "con"])
def test_draft_path_rejects_nonportable_or_reserved_identifiers(
    tmp_path: Path, capability_id: str
) -> None:
    with pytest.raises(CustomCapabilityPackageError):
        draft_path(tmp_path, capability_id)


def test_draft_directory_chain_rejects_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    codex_room = tmp_path / ".codex-room"
    codex_room.mkdir()
    try:
        (codex_room / "capability-drafts").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("test platform cannot create directory symlinks")

    with pytest.raises(CustomCapabilityPackageError, match="without symlinks"):
        load_custom_capability_draft(tmp_path, "count_lines")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.update(extra=True), "unknown fields"),
        (lambda value: value.update(schema_version=2), "schema_version"),
        (lambda value: value.update(id="other"), "draft directory"),
        (lambda value: value.update(version="../1"), "version"),
        (lambda value: value.update(scope="personal"), "scope"),
        (
            lambda value: value.update(
                runtime={
                    "kind": "python",
                    "entrypoint": "other.py",
                    "protocol": "stdio-json-v1",
                }
            ),
            "runtime",
        ),
    ],
)
def test_manifest_rejects_identity_and_runtime_drift(
    tmp_path: Path, mutation, message: str
) -> None:
    manifest = _manifest()
    mutation(manifest)
    _write_draft(tmp_path, manifest=manifest)

    with pytest.raises(CustomCapabilityPackageError, match=message):
        load_custom_capability_draft(tmp_path, "count_lines")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value.update(input_schema={"type": "array"}),
            "input_schema",
        ),
        (
            lambda value: value["output_schema"]["properties"].pop("ok"),
            "undeclared properties",
        ),
        (
            lambda value: value["output_schema"].update(required=["count"]),
            "require property 'ok'",
        ),
        (
            lambda value: value.update(durable_result_fields=["missing"]),
            "undeclared output properties",
        ),
        (
            lambda value: value.update(durable_result_fields=["ok"]),
            "reserved envelope fields",
        ),
        (
            lambda value: value.update(
                permissions={
                    "workspace_read": False,
                    "workspace_write": False,
                    "network": False,
                }
            ),
            "permissions must declare exactly",
        ),
        (
            lambda value: value["permissions"].update(network="false"),
            "permission values must be booleans",
        ),
    ],
)
def test_manifest_rejects_invalid_contract_or_permission_declarations(
    tmp_path: Path, mutation, message: str
) -> None:
    manifest = _manifest()
    mutation(manifest)
    _write_draft(tmp_path, manifest=manifest)

    with pytest.raises(CustomCapabilityPackageError, match=message):
        load_custom_capability_draft(tmp_path, "count_lines")


def test_entrypoint_must_be_regular_utf8_syntax_valid_python(tmp_path: Path) -> None:
    _write_draft(tmp_path, code="this is not valid python !!!")

    with pytest.raises(CustomCapabilityPackageError, match="not valid Python"):
        load_custom_capability_draft(tmp_path, "count_lines")


def test_package_rejects_extra_unhashed_entries(tmp_path: Path) -> None:
    root, _, _ = _write_draft(tmp_path)
    (root / "notes.txt").write_text("not part of the package", encoding="utf-8")

    with pytest.raises(CustomCapabilityPackageError, match="unsupported entries"):
        load_custom_capability_draft(tmp_path, "count_lines")


def test_entrypoint_symlink_is_rejected_when_platform_supports_it(tmp_path: Path) -> None:
    root, _, _ = _write_draft(tmp_path)
    target = tmp_path / "outside.py"
    target.write_text("print('outside')", encoding="utf-8")
    (root / "capability.py").unlink()
    try:
        (root / "capability.py").symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("test platform cannot create symlinks")

    with pytest.raises(CustomCapabilityPackageError, match="regular file"):
        load_custom_capability_draft(tmp_path, "count_lines")


def test_manifest_required_fields_must_reference_declared_properties(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["input_schema"]["required"] = ["missing"]
    _write_draft(tmp_path, manifest=manifest)

    with pytest.raises(CustomCapabilityPackageError, match="undeclared properties"):
        load_custom_capability_draft(tmp_path, "count_lines")
