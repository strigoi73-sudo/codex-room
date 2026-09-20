from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOM_SKILLS_RELATIVE = Path(".agents") / "skills"
MAX_INHERITED_SKILL_FILES = 1024
MAX_INHERITED_SKILL_BYTES = 64 * 1024 * 1024


class RoomSkillInheritanceError(ValueError):
    """A Room-local skill tree is unsafe or exceeds rollover bounds."""


@dataclass(frozen=True, slots=True)
class _SkillFile:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class _SkillInventory:
    skill_names: tuple[str, ...]
    files: tuple[_SkillFile, ...]
    total_bytes: int
    tree_sha256: str

    def metadata(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "skill_count": len(self.skill_names),
            "skill_names": list(self.skill_names),
            "file_count": len(self.files),
            "total_bytes": self.total_bytes,
            "tree_sha256": self.tree_sha256,
        }


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_directory(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise RoomSkillInheritanceError(f"{label} may not be a symlink")
    mode = path.stat(follow_symlinks=False).st_mode
    if not stat.S_ISDIR(mode):
        raise RoomSkillInheritanceError(f"{label} must be a directory")


def _collect_package_files(package: Path, root: Path) -> list[_SkillFile]:
    files: list[_SkillFile] = []
    pending = [package]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(root).as_posix()
                if entry.is_symlink():
                    raise RoomSkillInheritanceError(
                        f"Room-local skill entry may not be a symlink: {relative}"
                    )
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    raise RoomSkillInheritanceError(
                        f"Room-local skill entry must be a regular file or directory: {relative}"
                    )
                file_stat = entry.stat(follow_symlinks=False)
                files.append(
                    _SkillFile(
                        path=relative,
                        size=file_stat.st_size,
                        sha256=_hash_file(path),
                    )
                )
    return files


def _inventory(workspace: Path) -> _SkillInventory:
    agents_root = workspace / ".agents"
    skills_root = workspace / ROOM_SKILLS_RELATIVE
    if agents_root.is_symlink():
        raise RoomSkillInheritanceError("Room-local .agents root may not be a symlink")
    if not agents_root.exists():
        return _finalize_inventory([], [])
    _require_directory(agents_root, label="Room-local .agents root")
    if skills_root.is_symlink():
        raise RoomSkillInheritanceError("Room-local skills root may not be a symlink")
    if not skills_root.exists():
        return _finalize_inventory([], [])
    _require_directory(skills_root, label="Room-local skills root")

    skill_names: list[str] = []
    files: list[_SkillFile] = []
    with os.scandir(skills_root) as entries:
        children = sorted(entries, key=lambda item: item.name)
    for entry in children:
        child = Path(entry.path)
        if entry.is_symlink():
            raise RoomSkillInheritanceError(
                f"Room-local skills root may not contain symlinks: {entry.name}"
            )
        if entry.is_file(follow_symlinks=False):
            continue
        if not entry.is_dir(follow_symlinks=False):
            raise RoomSkillInheritanceError(
                f"Room-local skills root contains an unsupported entry: {entry.name}"
            )
        skill_file = child / "SKILL.md"
        if skill_file.is_symlink():
            raise RoomSkillInheritanceError(
                f"Room-local skill SKILL.md may not be a symlink: {entry.name}/SKILL.md"
            )
        if not skill_file.exists():
            continue
        if not skill_file.is_file():
            raise RoomSkillInheritanceError(
                f"Room-local skill SKILL.md must be a regular file: {entry.name}/SKILL.md"
            )
        skill_names.append(entry.name)
        files.extend(_collect_package_files(child, skills_root))

    return _finalize_inventory(skill_names, files)


def _finalize_inventory(
    skill_names: list[str], files: list[_SkillFile]
) -> _SkillInventory:
    ordered_files = tuple(sorted(files, key=lambda item: item.path))
    total_bytes = sum(item.size for item in ordered_files)
    if len(ordered_files) > MAX_INHERITED_SKILL_FILES:
        raise RoomSkillInheritanceError(
            "Room-local skill inheritance exceeds "
            f"{MAX_INHERITED_SKILL_FILES} files"
        )
    if total_bytes > MAX_INHERITED_SKILL_BYTES:
        raise RoomSkillInheritanceError(
            "Room-local skill inheritance exceeds "
            f"{MAX_INHERITED_SKILL_BYTES} bytes"
        )
    canonical = json.dumps(
        [
            {"path": item.path, "sha256": item.sha256, "size": item.size}
            for item in ordered_files
        ],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _SkillInventory(
        skill_names=tuple(sorted(skill_names)),
        files=ordered_files,
        total_bytes=total_bytes,
        tree_sha256=hashlib.sha256(canonical).hexdigest(),
    )


def summarize_room_local_skills(workspace: Path) -> dict[str, Any]:
    """Return deterministic provenance for lineage-scoped Room-local skills."""
    return _inventory(workspace).metadata()


def inherit_room_local_skills(
    source_workspace: Path, staging_workspace: Path
) -> dict[str, Any]:
    """Copy valid Room-local skill packages into a staged rollover workspace."""
    inventory = _inventory(source_workspace)
    if not inventory.files:
        return inventory.metadata()

    destination_agents = staging_workspace / ".agents"
    destination_root = staging_workspace / ROOM_SKILLS_RELATIVE
    if destination_agents.is_symlink():
        raise RoomSkillInheritanceError(
            "Rollover destination .agents root may not be a symlink"
        )
    if destination_agents.exists() and not destination_agents.is_dir():
        raise RoomSkillInheritanceError(
            "Rollover destination .agents root must be a directory"
        )
    if destination_root.exists() or destination_root.is_symlink():
        raise RoomSkillInheritanceError(
            "Rollover destination already contains .agents/skills"
        )
    destination_agents.mkdir(parents=True, exist_ok=True)

    source_root = source_workspace / ROOM_SKILLS_RELATIVE
    for item in inventory.files:
        source = source_root.joinpath(*Path(item.path).parts)
        destination = destination_root.joinpath(*Path(item.path).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if _hash_file(destination) != item.sha256:
            raise RoomSkillInheritanceError(
                f"Room-local skill copy verification failed: {item.path}"
            )

    inherited = _inventory(staging_workspace)
    if inherited != inventory:
        raise RoomSkillInheritanceError(
            "Room-local skill rollover inventory changed during materialization"
        )
    return inherited.metadata()
