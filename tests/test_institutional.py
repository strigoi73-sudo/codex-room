from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from codex_room.institutional import (
    InstitutionalReleaseError,
    publish_institutional_release,
    load_institutional_release,
    resolve_institutional_release,
    stage_institutional_release,
    verify_materialized_release,
)


def _write_manifest(
    workspace: Path,
    artifacts: list[dict],
    *,
    non_inherited: list[str] | None = None,
) -> Path:
    manifest = {
        "schemaVersion": 1,
        "releaseId": "institution-v1",
        "createdInRoomId": "room_source",
        "description": "Focused durable tools and current operating guidance.",
        "artifacts": artifacts,
        "nonInheritedState": non_inherited
        if non_inherited is not None
        else [".room-work.json", ".room-work.lock"],
    }
    path = workspace / "institutional" / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _artifact(workspace: Path, source: str, destination: str, kind: str = "tool") -> dict:
    payload = (workspace / source).read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    return {
        "sourcePath": source,
        "materializeTo": destination,
        "sha256": digest,
        "size": len(payload),
        "kind": kind,
        "verification": {
            "command": "focused test",
            "result": "passed",
            "reviewer": "independent reviewer",
            "reviewedHash": digest,
        },
    }


def test_release_stages_only_allowlisted_files_and_manifest(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "tool.ps1").write_text("'durable'", encoding="utf-8")
    (source / ".room-work.json").write_text('{"stale":true}', encoding="utf-8")
    (source / "unlisted.log").write_text("runtime residue", encoding="utf-8")
    _write_manifest(source, [_artifact(source, "tool.ps1", "tool.ps1")])

    release = load_institutional_release(source)
    assert release is not None
    assert release.release_id == "institution-v1"
    assert release.metadata()["manifest_sha256"] == hashlib.sha256(
        (source / "institutional" / "manifest.json").read_bytes()
    ).hexdigest()

    staged = tmp_path / "staged"
    stage_institutional_release(release, source, staged)
    assert (staged / "tool.ps1").read_text(encoding="utf-8") == "'durable'"
    assert (staged / "institutional" / "manifest.json").is_file()
    assert not (staged / ".room-work.json").exists()
    assert not (staged / "unlisted.log").exists()


@pytest.mark.parametrize(
    ("source_path", "destination"),
    [
        ("../outside.txt", "tool.ps1"),
        ("tool.ps1", "../outside.ps1"),
        ("tool.ps1", ".room-work.json"),
        ("tool.ps1", "institutional/manifest.json"),
    ],
)
def test_release_rejects_unsafe_or_state_paths(tmp_path, source_path, destination):
    source = tmp_path / "source"
    source.mkdir()
    (source / "tool.ps1").write_text("safe", encoding="utf-8")
    artifact = _artifact(source, "tool.ps1", "tool.ps1")
    artifact["sourcePath"] = source_path
    artifact["materializeTo"] = destination
    _write_manifest(source, [artifact])

    with pytest.raises(InstitutionalReleaseError):
        load_institutional_release(source)


def test_release_rejects_hash_mismatch_and_missing_state_declaration(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "tool.ps1").write_text("safe", encoding="utf-8")
    artifact = _artifact(source, "tool.ps1", "tool.ps1")
    artifact["sha256"] = "0" * 64
    _write_manifest(source, [artifact])
    with pytest.raises(InstitutionalReleaseError, match="does not match"):
        load_institutional_release(source)

    artifact = _artifact(source, "tool.ps1", "tool.ps1")
    _write_manifest(source, [artifact], non_inherited=[])
    with pytest.raises(InstitutionalReleaseError, match="must include"):
        load_institutional_release(source)


def test_release_rejects_case_insensitive_destination_collision(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "one.txt").write_text("one", encoding="utf-8")
    (source / "two.txt").write_text("two", encoding="utf-8")
    _write_manifest(
        source,
        [
            _artifact(source, "one.txt", "Tool.txt"),
            _artifact(source, "two.txt", "tool.TXT"),
        ],
    )
    with pytest.raises(InstitutionalReleaseError, match="destinations must be noncolliding"):
        load_institutional_release(source)


def test_release_rejects_parent_child_destination_collision(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "one.txt").write_text("one", encoding="utf-8")
    (source / "two.txt").write_text("two", encoding="utf-8")
    _write_manifest(
        source,
        [
            _artifact(source, "one.txt", "tools"),
            _artifact(source, "two.txt", "tools/two.txt"),
        ],
    )
    with pytest.raises(InstitutionalReleaseError, match="destinations must be noncolliding"):
        load_institutional_release(source)


def test_publish_is_content_addressed_immutable_and_supports_path_remapping(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    canonical = workspace / "package" / "tool.ps1"
    canonical.parent.mkdir()
    canonical.write_text("reviewed bytes", encoding="utf-8")
    artifact = _artifact(workspace, "package/tool.ps1", "tool.ps1")
    manifest = _write_manifest(workspace, [artifact])

    published = publish_institutional_release(workspace, tmp_path / "data")
    release_root = tmp_path / "data" / "institutional" / "releases" / published.manifest_sha256
    assert release_root.name == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert (release_root / "package" / "tool.ps1").read_text(encoding="utf-8") == "reviewed bytes"
    assert not (release_root / "tool.ps1").exists()
    assert publish_institutional_release(workspace, tmp_path / "data") == published

    resolved = resolve_institutional_release(tmp_path / "data", published.manifest_sha256)
    staged = tmp_path / "staged-remapped"
    stage_institutional_release(resolved, release_root, staged)
    verify_materialized_release(resolved, staged, require_exact_inventory=True)
    assert (staged / "tool.ps1").read_text(encoding="utf-8") == "reviewed bytes"

    manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    replacement = publish_institutional_release(workspace, tmp_path / "data")
    assert replacement.manifest_sha256 != published.manifest_sha256
    assert (release_root / "institutional" / "manifest.json").read_bytes() == published.manifest_bytes


def test_resolver_rejects_registry_directory_not_matching_manifest(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "tool.ps1").write_text("safe", encoding="utf-8")
    _write_manifest(workspace, [_artifact(workspace, "tool.ps1", "tool.ps1")])
    published = publish_institutional_release(workspace, tmp_path / "data")
    wrong = "0" * 64
    wrong_root = tmp_path / "data" / "institutional" / "releases" / wrong
    shutil.copytree(
        tmp_path / "data" / "institutional" / "releases" / published.manifest_sha256,
        wrong_root,
    )
    with pytest.raises(InstitutionalReleaseError, match="registry key"):
        resolve_institutional_release(tmp_path / "data", wrong)

    release_root = (
        tmp_path / "data" / "institutional" / "releases" / published.manifest_sha256
    )
    (release_root / "unlisted.log").write_text("not part of the release", encoding="utf-8")
    with pytest.raises(InstitutionalReleaseError, match="inventory"):
        resolve_institutional_release(tmp_path / "data", published.manifest_sha256)


def test_release_requires_hash_bound_artifact_verification(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "tool.ps1").write_text("safe", encoding="utf-8")
    artifact = _artifact(source, "tool.ps1", "tool.ps1")
    artifact["verification"]["reviewedHash"] = "0" * 64
    _write_manifest(source, [artifact])
    with pytest.raises(InstitutionalReleaseError, match="does not match the artifact"):
        load_institutional_release(source)
