from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


MANIFEST_PATH = PurePosixPath("institutional/manifest.json")
REGISTRY_RELEASES_PATH = PurePosixPath("institutional/releases")
MAX_MANIFEST_BYTES = 1_000_000
MAX_ARTIFACTS = 256
MAX_ARTIFACT_BYTES = 512 * 1024 * 1024
MAX_RELEASE_BYTES = 1024 * 1024 * 1024
REQUIRED_NON_INHERITED_STATE = {".room-work.json", ".room-work.lock"}
_HEX_SHA256 = re.compile(r"[0-9A-Fa-f]{64}")
_RELEASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


class InstitutionalReleaseError(ValueError):
    """A durable release manifest or one of its artifacts is unsafe or inconsistent."""


@dataclass(frozen=True, slots=True)
class InstitutionalArtifact:
    source_path: PurePosixPath
    materialize_to: PurePosixPath
    sha256: str
    size: int
    kind: str


@dataclass(frozen=True, slots=True)
class InstitutionalRelease:
    release_id: str
    created_in_room_id: str
    description: str
    manifest_sha256: str
    manifest_bytes: bytes
    artifacts: tuple[InstitutionalArtifact, ...]
    non_inherited_state: tuple[PurePosixPath, ...]

    def metadata(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "created_in_room_id": self.created_in_room_id,
            "manifest_sha256": self.manifest_sha256,
            "artifact_count": len(self.artifacts),
            "artifact_bytes": sum(item.size for item in self.artifacts),
        }


def load_institutional_release(
    workspace: Path, *, expected_manifest_sha256: str | None = None
) -> InstitutionalRelease | None:
    """Read and verify one fixed-path, allowlisted durable release tree."""
    manifest_file = workspace.joinpath(*MANIFEST_PATH.parts)
    if not os.path.lexists(manifest_file):
        return None
    _assert_regular_file(workspace, MANIFEST_PATH, "manifest")
    manifest_bytes = manifest_file.read_bytes()
    if len(manifest_bytes) > MAX_MANIFEST_BYTES:
        raise InstitutionalReleaseError("Institutional manifest exceeds the size limit")
    try:
        raw = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstitutionalReleaseError("Institutional manifest must be valid UTF-8 JSON") from exc
    if not isinstance(raw, dict) or raw.get("schemaVersion") != 1:
        raise InstitutionalReleaseError("Institutional manifest schemaVersion must be 1")

    release_id = raw.get("releaseId")
    if not isinstance(release_id, str) or not _RELEASE_ID.fullmatch(release_id):
        raise InstitutionalReleaseError("Institutional releaseId is invalid")
    created_in_room_id = raw.get("createdInRoomId")
    if not isinstance(created_in_room_id, str) or not created_in_room_id.startswith("room_"):
        raise InstitutionalReleaseError("createdInRoomId must identify a Room")
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip() or len(description) > 1000:
        raise InstitutionalReleaseError("Institutional release description is invalid")

    raw_artifacts = raw.get("artifacts")
    if not isinstance(raw_artifacts, list) or not 1 <= len(raw_artifacts) <= MAX_ARTIFACTS:
        raise InstitutionalReleaseError("Institutional artifacts must be a non-empty bounded list")
    raw_state = raw.get("nonInheritedState")
    if not isinstance(raw_state, list):
        raise InstitutionalReleaseError("nonInheritedState must be a list")
    state_paths = tuple(
        _relative_path(item, f"nonInheritedState[{index}]")
        for index, item in enumerate(raw_state)
    )
    state_keys = {_path_key(item) for item in state_paths}
    if len(state_keys) != len(state_paths):
        raise InstitutionalReleaseError("nonInheritedState contains duplicate paths")
    if any(
        _paths_overlap(left, right)
        for index, left in enumerate(state_paths)
        for right in state_paths[index + 1 :]
    ):
        raise InstitutionalReleaseError("nonInheritedState contains overlapping paths")
    if not {_path_key(PurePosixPath(item)) for item in REQUIRED_NON_INHERITED_STATE} <= state_keys:
        raise InstitutionalReleaseError(
            "nonInheritedState must include .room-work.json and .room-work.lock"
        )

    artifacts: list[InstitutionalArtifact] = []
    source_keys: set[str] = set()
    destination_keys: set[str] = {_path_key(MANIFEST_PATH)}
    destination_paths: list[PurePosixPath] = [MANIFEST_PATH]
    total_size = 0
    for index, item in enumerate(raw_artifacts):
        if not isinstance(item, dict):
            raise InstitutionalReleaseError(f"artifacts[{index}] must be an object")
        allowed_artifact_fields = {
            "sourcePath",
            "materializeTo",
            "sha256",
            "size",
            "kind",
            "derivedFrom",
            "verification",
        }
        unknown_artifact_fields = set(item) - allowed_artifact_fields
        if unknown_artifact_fields:
            raise InstitutionalReleaseError(
                f"artifacts[{index}] has unknown fields: {sorted(unknown_artifact_fields)}"
            )
        source_path = _relative_path(item.get("sourcePath"), f"artifacts[{index}].sourcePath")
        destination = _relative_path(
            item.get("materializeTo"), f"artifacts[{index}].materializeTo"
        )
        source_key = _path_key(source_path)
        destination_key = _path_key(destination)
        if source_key == _path_key(MANIFEST_PATH):
            raise InstitutionalReleaseError("Institutional manifest must not list itself")
        if source_key in source_keys:
            raise InstitutionalReleaseError("Institutional source paths must be unique")
        if destination_key in destination_keys or any(
            _paths_overlap(destination, existing) for existing in destination_paths
        ):
            raise InstitutionalReleaseError("Institutional destinations must be noncolliding")
        if any(
            _paths_overlap(source_path, state_path)
            or _paths_overlap(destination, state_path)
            for state_path in state_paths
        ):
            raise InstitutionalReleaseError("Mutable Room state cannot be an artifact")
        digest = item.get("sha256")
        if not isinstance(digest, str) or not _HEX_SHA256.fullmatch(digest):
            raise InstitutionalReleaseError(f"artifacts[{index}].sha256 must be lowercase SHA-256")
        size = item.get("size")
        if not isinstance(size, int) or isinstance(size, bool) or not 0 <= size <= MAX_ARTIFACT_BYTES:
            raise InstitutionalReleaseError(f"artifacts[{index}].size is invalid")
        kind = item.get("kind")
        if kind not in {"tool", "test", "documentation"}:
            raise InstitutionalReleaseError(f"artifacts[{index}].kind is invalid")
        _validate_optional_provenance(item.get("derivedFrom"), index)
        _validate_artifact_verification(item.get("verification"), index, digest)
        _assert_regular_file(workspace, source_path, f"artifacts[{index}].sourcePath")
        source_file = workspace.joinpath(*source_path.parts)
        actual_size, actual_hash = _measure_file(source_file)
        digest = digest.lower()
        if actual_size != size or actual_hash != digest:
            raise InstitutionalReleaseError(
                f"Institutional artifact does not match manifest: {source_path.as_posix()}"
            )
        total_size += size
        if total_size > MAX_RELEASE_BYTES:
            raise InstitutionalReleaseError("Institutional release exceeds the total size limit")
        source_keys.add(source_key)
        destination_keys.add(destination_key)
        destination_paths.append(destination)
        artifacts.append(
            InstitutionalArtifact(source_path, destination, digest, size, kind)
        )

    allowed_fields = {
        "schemaVersion",
        "releaseId",
        "createdInRoomId",
        "description",
        "artifacts",
        "nonInheritedState",
        "verification",
    }
    unknown = set(raw) - allowed_fields
    if unknown:
        raise InstitutionalReleaseError(f"Institutional manifest has unknown fields: {sorted(unknown)}")
    _validate_optional_verification(raw.get("verification"), None)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    if expected_manifest_sha256 is not None and manifest_sha256 != expected_manifest_sha256:
        raise InstitutionalReleaseError("Institutional registry key does not match manifest bytes")
    return InstitutionalRelease(
        release_id=release_id,
        created_in_room_id=created_in_room_id,
        description=description.strip(),
        manifest_sha256=manifest_sha256,
        manifest_bytes=manifest_bytes,
        artifacts=tuple(artifacts),
        non_inherited_state=state_paths,
    )


def publish_institutional_release(workspace: Path, data_root: Path) -> InstitutionalRelease:
    """Publish a verified Room release into the immutable content-addressed registry."""
    release = load_institutional_release(workspace)
    if release is None:
        raise InstitutionalReleaseError(
            f"No institutional manifest exists at {MANIFEST_PATH.as_posix()}"
        )
    releases_root = data_root.joinpath(*REGISTRY_RELEASES_PATH.parts)
    releases_root.mkdir(parents=True, exist_ok=True)
    destination = releases_root / release.manifest_sha256
    if os.path.lexists(destination):
        existing = resolve_institutional_release(data_root, release.manifest_sha256)
        if existing.manifest_bytes != release.manifest_bytes:
            raise InstitutionalReleaseError("Institutional registry hash collision")
        return existing

    publishing_root = data_root / "institutional" / ".publishing"
    publishing_root.mkdir(parents=True, exist_ok=True)
    operation_root = publishing_root / f"publish_{uuid.uuid4().hex}"
    staging_release = operation_root / "release"
    try:
        staging_release.mkdir(parents=True, exist_ok=False)
        for artifact in release.artifacts:
            _assert_regular_file(workspace, artifact.source_path, "artifact source")
            source = workspace.joinpath(*artifact.source_path.parts)
            target = staging_release.joinpath(*artifact.source_path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        manifest_target = staging_release.joinpath(*MANIFEST_PATH.parts)
        manifest_target.parent.mkdir(parents=True, exist_ok=True)
        manifest_target.write_bytes(release.manifest_bytes)
        load_institutional_release(
            staging_release, expected_manifest_sha256=release.manifest_sha256
        )
        try:
            os.replace(staging_release, destination)
        except FileExistsError:
            existing = resolve_institutional_release(data_root, release.manifest_sha256)
            if existing.manifest_bytes != release.manifest_bytes:
                raise InstitutionalReleaseError("Institutional registry hash collision")
        return resolve_institutional_release(data_root, release.manifest_sha256)
    finally:
        if operation_root.exists():
            shutil.rmtree(operation_root)


def resolve_institutional_release(
    data_root: Path, manifest_sha256: str
) -> InstitutionalRelease:
    """Resolve and fully validate one explicitly selected registry release."""
    if not _HEX_SHA256.fullmatch(manifest_sha256):
        raise InstitutionalReleaseError("Institutional release hash must be lowercase SHA-256")
    manifest_sha256 = manifest_sha256.lower()
    release_root = data_root.joinpath(*REGISTRY_RELEASES_PATH.parts, manifest_sha256)
    if not os.path.lexists(release_root):
        raise InstitutionalReleaseError("Selected institutional release does not exist")
    release = load_institutional_release(
        release_root, expected_manifest_sha256=manifest_sha256
    )
    if release is None:  # pragma: no cover - lexists plus regular-file validation is decisive
        raise InstitutionalReleaseError("Selected institutional release has no manifest")
    expected_files = {_path_key(MANIFEST_PATH)} | {
        _path_key(artifact.source_path) for artifact in release.artifacts
    }
    if _regular_file_inventory(release_root) != expected_files:
        raise InstitutionalReleaseError("Institutional registry inventory does not match manifest")
    return release


def institutional_release_root(data_root: Path, manifest_sha256: str) -> Path:
    """Return the canonical root for one already validated release hash."""
    if not _HEX_SHA256.fullmatch(manifest_sha256):
        raise InstitutionalReleaseError("Institutional release hash must be lowercase SHA-256")
    manifest_sha256 = manifest_sha256.lower()
    return data_root.joinpath(*REGISTRY_RELEASES_PATH.parts, manifest_sha256)


def stage_institutional_release(
    release: InstitutionalRelease | None,
    source_workspace: Path,
    staging_workspace: Path,
) -> None:
    """Build a complete successor workspace without exposing a partial release."""
    staging_workspace.mkdir(parents=True, exist_ok=False)
    if release is None:
        return
    for artifact in release.artifacts:
        _assert_regular_file(source_workspace, artifact.source_path, "artifact source")
        source = source_workspace.joinpath(*artifact.source_path.parts)
        destination = staging_workspace.joinpath(*artifact.materialize_to.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        size, digest = _measure_file(destination)
        if size != artifact.size or digest != artifact.sha256:
            raise InstitutionalReleaseError(
                f"Staged artifact changed while copying: {artifact.source_path.as_posix()}"
            )
    manifest_destination = staging_workspace.joinpath(*MANIFEST_PATH.parts)
    manifest_destination.parent.mkdir(parents=True, exist_ok=True)
    manifest_destination.write_bytes(release.manifest_bytes)


def verify_materialized_release(
    release: InstitutionalRelease | None, workspace: Path, *, require_exact_inventory: bool = False
) -> None:
    """Verify staged successor bytes against an already validated registry release."""
    if not workspace.is_dir():
        raise InstitutionalReleaseError("Materialized institutional workspace is missing")
    expected_files: set[str] = set()
    if release is not None:
        for artifact in release.artifacts:
            _assert_regular_file(workspace, artifact.materialize_to, "materialized artifact")
            target = workspace.joinpath(*artifact.materialize_to.parts)
            size, digest = _measure_file(target)
            if size != artifact.size or digest != artifact.sha256:
                raise InstitutionalReleaseError(
                    f"Materialized artifact does not match release: {artifact.materialize_to.as_posix()}"
                )
            expected_files.add(_path_key(artifact.materialize_to))
        _assert_regular_file(workspace, MANIFEST_PATH, "materialized manifest")
        manifest = workspace.joinpath(*MANIFEST_PATH.parts).read_bytes()
        if manifest != release.manifest_bytes:
            raise InstitutionalReleaseError("Materialized manifest does not match release")
        expected_files.add(_path_key(MANIFEST_PATH))
    if require_exact_inventory:
        actual_files = _regular_file_inventory(workspace)
        if actual_files != expected_files:
            raise InstitutionalReleaseError("Staged workspace inventory does not match release")


def _relative_path(value: Any, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise InstitutionalReleaseError(f"{label} must be a normalized relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(part in {"", ".", ".."} for part in path.parts):
        raise InstitutionalReleaseError(f"{label} must be a normalized relative path")
    for part in path.parts:
        if any(character in part for character in '<>:"|?*') or part.endswith((" ", ".")):
            raise InstitutionalReleaseError(f"{label} is not portable")
        if part.split(".", 1)[0].upper() in _WINDOWS_RESERVED:
            raise InstitutionalReleaseError(f"{label} uses a reserved path component")
    return path


def _path_key(path: PurePosixPath) -> str:
    return path.as_posix().casefold()


def _paths_overlap(left: PurePosixPath, right: PurePosixPath) -> bool:
    left_parts = tuple(part.casefold() for part in left.parts)
    right_parts = tuple(part.casefold() for part in right.parts)
    shorter = min(len(left_parts), len(right_parts))
    return left_parts[:shorter] == right_parts[:shorter]


def _assert_regular_file(root: Path, relative: PurePosixPath, label: str) -> None:
    current = root
    try:
        root_stat = os.lstat(root)
    except OSError as exc:
        raise InstitutionalReleaseError(f"{label} root is unavailable") from exc
    if _is_link_or_reparse(root_stat):
        raise InstitutionalReleaseError(f"{label} traverses a link or reparse point")
    for index, part in enumerate(relative.parts):
        current = current / part
        try:
            item_stat = os.lstat(current)
        except OSError as exc:
            raise InstitutionalReleaseError(f"{label} is missing: {relative.as_posix()}") from exc
        if _is_link_or_reparse(item_stat):
            raise InstitutionalReleaseError(f"{label} traverses a link or reparse point")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(item_stat.st_mode):
            raise InstitutionalReleaseError(f"{label} has a non-directory parent")
    if not stat.S_ISREG(item_stat.st_mode):
        raise InstitutionalReleaseError(f"{label} must be a regular file")


def _is_link_or_reparse(item_stat: os.stat_result) -> bool:
    attributes = getattr(item_stat, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(item_stat.st_mode) or bool(attributes & reparse)


def _measure_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def _regular_file_inventory(root: Path) -> set[str]:
    try:
        root_stat = os.lstat(root)
    except OSError as exc:
        raise InstitutionalReleaseError("Institutional inventory root is unavailable") from exc
    if _is_link_or_reparse(root_stat) or not stat.S_ISDIR(root_stat.st_mode):
        raise InstitutionalReleaseError("Institutional inventory root must be a regular directory")
    inventory: set[str] = set()
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in directory_names:
            item_stat = os.lstat(current_path / name)
            if _is_link_or_reparse(item_stat):
                raise InstitutionalReleaseError("Staged workspace contains a link or reparse point")
        for name in file_names:
            item = current_path / name
            item_stat = os.lstat(item)
            if _is_link_or_reparse(item_stat) or not stat.S_ISREG(item_stat.st_mode):
                raise InstitutionalReleaseError("Staged workspace contains a non-regular file")
            relative = item.relative_to(root).as_posix()
            inventory.add(relative.casefold())
    return inventory


def _validate_optional_provenance(value: Any, index: int) -> None:
    if value is None:
        return
    if not isinstance(value, dict) or set(value) != {"roomId", "sourcePath", "sha256"}:
        raise InstitutionalReleaseError(f"artifacts[{index}].derivedFrom is invalid")
    if not isinstance(value["roomId"], str) or not value["roomId"].startswith("room_"):
        raise InstitutionalReleaseError(f"artifacts[{index}].derivedFrom.roomId is invalid")
    _relative_path(value["sourcePath"], f"artifacts[{index}].derivedFrom.sourcePath")
    if not isinstance(value["sha256"], str) or not _HEX_SHA256.fullmatch(value["sha256"]):
        raise InstitutionalReleaseError(f"artifacts[{index}].derivedFrom.sha256 is invalid")


def _validate_optional_verification(value: Any, index: int | None) -> None:
    if value is None:
        return
    label = "verification" if index is None else f"artifacts[{index}].verification"
    if not isinstance(value, (dict, list)):
        raise InstitutionalReleaseError(f"{label} must be an object or list")
    if len(json.dumps(value, ensure_ascii=False)) > 20_000:
        raise InstitutionalReleaseError(f"{label} is too large")


def _validate_artifact_verification(value: Any, index: int, digest: str) -> None:
    label = f"artifacts[{index}].verification"
    required = {"command", "result", "reviewer", "reviewedHash"}
    if not isinstance(value, dict) or set(value) != required:
        raise InstitutionalReleaseError(f"{label} must contain {sorted(required)}")
    for field in ("command", "result", "reviewer"):
        text = value[field]
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise InstitutionalReleaseError(f"{label}.{field} is invalid")
    reviewed_hash = value["reviewedHash"]
    if not isinstance(reviewed_hash, str) or not _HEX_SHA256.fullmatch(reviewed_hash):
        raise InstitutionalReleaseError(f"{label}.reviewedHash is invalid")
    if reviewed_hash.lower() != digest.lower():
        raise InstitutionalReleaseError(f"{label}.reviewedHash does not match the artifact")


def _main() -> None:
    parser = argparse.ArgumentParser(description="Manage immutable institutional releases")
    subcommands = parser.add_subparsers(dest="command", required=True)
    validate = subcommands.add_parser("validate", help="validate and hash a workspace manifest")
    validate.add_argument("--workspace", required=True, type=Path)
    publish = subcommands.add_parser("publish", help="publish a reviewed workspace manifest")
    publish.add_argument("--workspace", required=True, type=Path)
    publish.add_argument("--data-root", required=True, type=Path)
    arguments = parser.parse_args()
    if arguments.command == "validate":
        release = load_institutional_release(arguments.workspace)
        if release is None:
            raise InstitutionalReleaseError(
                f"No institutional manifest exists at {MANIFEST_PATH.as_posix()}"
            )
        print(json.dumps(release.metadata(), indent=2, sort_keys=True))
    elif arguments.command == "publish":
        release = publish_institutional_release(arguments.workspace, arguments.data_root)
        print(json.dumps(release.metadata(), indent=2, sort_keys=True))


if __name__ == "__main__":
    _main()
