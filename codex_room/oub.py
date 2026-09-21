"""Organizational Utility Benchmark asset audit and grading helpers."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_ROOT = PROJECT_ROOT / "benchmarks" / "oub"


class OUBError(RuntimeError):
    """Raised when OUB assets or grading violate the benchmark contract."""


def current_version() -> str:
    path = BENCHMARK_ROOT / "CURRENT"
    if not path.is_file():
        raise OUBError("OUB CURRENT pointer is missing")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise OUBError("OUB CURRENT pointer is empty")
    return value


def version_root(version: str) -> Path:
    root = BENCHMARK_ROOT / version
    if not root.is_dir():
        raise OUBError(f"Unknown OUB version: {version}")
    return root


def load_manifest(version: str) -> dict[str, Any]:
    path = version_root(version) / "manifest.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OUBError(f"Unable to load OUB manifest: {version}") from exc
    if not isinstance(value, dict):
        raise OUBError("OUB manifest must be a JSON object")
    return value


def benchmark_fingerprint(version: str) -> str:
    root = version_root(version)
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _task(manifest: dict[str, Any], task_id: str) -> dict[str, Any]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise OUBError("OUB manifest tasks must be a list")
    for item in tasks:
        if isinstance(item, dict) and item.get("id") == task_id:
            return item
    raise OUBError(f"OUB task not found: {task_id}")


def grade_workspace(
    workspace: Path,
    *,
    version: str = "v1",
    task_id: str = "o01-competing-root-causes",
) -> dict[str, Any]:
    manifest = load_manifest(version)
    task = _task(manifest, task_id)
    grader = version_root(version) / str(task["grader_file"])
    if not grader.is_file():
        raise OUBError(f"OUB grader missing: {grader}")
    proc = subprocess.run(
        [sys.executable, str(grader), str(workspace.resolve())],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        raise OUBError(
            "OUB grader failed: " + ((proc.stderr or proc.stdout).strip()[-1000:])
        )
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise OUBError("OUB grader returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise OUBError("OUB grader result must be an object")
    return result


def populate_reference_workspace(
    target: Path,
    *,
    version: str = "v1",
    task_id: str = "o01-competing-root-causes",
) -> None:
    manifest = load_manifest(version)
    task = _task(manifest, task_id)
    fixture = version_root(version) / str(task["fixture_dir"])
    reference = version_root(version) / str(task["reference_dir"])
    if not fixture.is_dir() or not reference.is_dir():
        raise OUBError("OUB fixture/reference directory is missing")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(fixture, target)
    for path in reference.rglob("*"):
        if path.is_file():
            rel = path.relative_to(reference)
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)


def audit_assets(version: str = "v1") -> dict[str, Any]:
    manifest = load_manifest(version)
    if manifest.get("schema") != "oub-manifest-v1":
        raise OUBError("Unexpected OUB manifest schema")
    if manifest.get("mode") != "naturalistic":
        raise OUBError("OUB v1 must use naturalistic platform orchestration")
    protocol = manifest.get("protocol")
    if not isinstance(protocol, dict):
        raise OUBError("OUB manifest protocol is missing")
    if protocol.get("comparison_unit") != "platform":
        raise OUBError("OUB comparison unit must be platform")
    if protocol.get("platform_internal_orchestration") != "unconstrained":
        raise OUBError("OUB must not prescribe internal orchestration")

    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 1:
        raise OUBError("OUB v1 must currently contain exactly one task")
    task = tasks[0]
    if not isinstance(task, dict) or task.get("id") != "o01-competing-root-causes":
        raise OUBError("OUB v1 O1 task identity changed unexpectedly")
    target_minutes = task.get("target_runtime_minutes")
    if not isinstance(target_minutes, int) or not 10 <= target_minutes <= 15:
        raise OUBError("O1 target runtime must remain within the 10–15 minute design budget")

    fixture = version_root(version) / str(task["fixture_dir"])
    fixture_files = sorted(path for path in fixture.rglob("*") if path.is_file())
    fixture_bytes = sum(path.stat().st_size for path in fixture_files)
    if len(fixture_files) > 10:
        raise OUBError("O1 fixture exceeds the ten-file investigation budget")
    if fixture_bytes > 30_000:
        raise OUBError("O1 fixture exceeds the 30 KB investigation budget")

    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td) / "workspace"
        populate_reference_workspace(workspace, version=version, task_id=str(task["id"]))
        grade = grade_workspace(workspace, version=version, task_id=str(task["id"]))

    if grade.get("score") != 100 or grade.get("pass") is not True:
        raise OUBError("O1 reference solution does not receive full credit")

    return {
        "ok": True,
        "benchmark_version": version,
        "benchmark_fingerprint": benchmark_fingerprint(version),
        "task_id": task["id"],
        "target_runtime_minutes": target_minutes,
        "fixture_file_count": len(fixture_files),
        "fixture_bytes": fixture_bytes,
        "reference_score": grade["score"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OUB asset audit and grader helper")
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--version", default=current_version())
    grade = sub.add_parser("grade")
    grade.add_argument("workspace")
    grade.add_argument("--version", default=current_version())
    grade.add_argument("--task-id", default="o01-competing-root-causes")
    args = parser.parse_args(argv)

    try:
        if args.command == "audit":
            result = audit_assets(args.version)
        else:
            result = grade_workspace(
                Path(args.workspace),
                version=args.version,
                task_id=args.task_id,
            )
    except OUBError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
