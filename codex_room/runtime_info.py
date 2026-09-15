from __future__ import annotations

import hashlib
import platform
import subprocess
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

from . import __version__


_SOURCE_SUFFIXES = frozenset({".py", ".html", ".js", ".css", ".svg"})


def collect_runtime_provenance(
    *,
    model: str,
    reasoning_effort: str,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Capture deterministic process-start provenance without external services."""
    root = (project_root or Path(__file__).resolve().parent.parent).resolve()
    revision, dirty = _git_source_state(root)
    return {
        "captured_at": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "application": {
            "version": __version__,
            "source_revision": revision,
            "source_dirty": dirty,
            "source_fingerprint_sha256": _source_fingerprint(root),
        },
        "runtime": {
            "python_version": platform.python_version(),
            "openai_codex_version": _distribution_version("openai-codex"),
        },
        "room_policy": {
            "model": model,
            "reasoning_effort": reasoning_effort,
        },
    }


def _distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _git_source_state(project_root: Path) -> tuple[str | None, bool | None]:
    revision = _run_git(project_root, "rev-parse", "HEAD")
    if revision is None:
        return None, None
    status = _run_git(
        project_root,
        "status",
        "--porcelain",
        "--untracked-files=normal",
        "--",
        "codex_room",
        "pyproject.toml",
    )
    return revision, bool(status) if status is not None else None


def _run_git(project_root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(project_root), *args],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _source_fingerprint(project_root: Path) -> str:
    package_root = project_root / "codex_room"
    candidates = [project_root / "pyproject.toml"]
    if package_root.exists():
        candidates.extend(
            path
            for path in package_root.rglob("*")
            if path.is_file()
            and path.suffix in _SOURCE_SUFFIXES
            and "__pycache__" not in path.parts
        )
    digest = hashlib.sha256()
    for path in sorted(
        (candidate for candidate in candidates if candidate.is_file()),
        key=lambda item: item.relative_to(project_root).as_posix(),
    ):
        relative = path.relative_to(project_root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
