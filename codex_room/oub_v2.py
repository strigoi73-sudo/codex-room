"""OUB v2: naturalistic Desktop versus Room external-task harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import zipfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from . import oub, pbm, pbm_v4, pbm_v5


VERSION = "v2"
PASTE = "Read BENCHMARK.md and execute it exactly. Do not ask me questions. When complete, stop."
OUTPUT_ROOT = oub.PROJECT_ROOT / "output" / "oub"
RUNS_ROOT = OUTPUT_ROOT / "v2-runs"
ACTIVE_POINTER = OUTPUT_ROOT / "v2-active.json"
BUNDLE_ROOT = OUTPUT_ROOT / "v2-bundles"
LOCK_DIR = OUTPUT_ROOT / ".v2-state-lock"
MANIFEST_PATH = oub.version_root(VERSION) / "manifest.json"
SAMPLE_PATH = oub.version_root(VERSION) / "sample.json"
PLAN_PATH = oub.version_root(VERSION) / "phase3_plan.json"
GRADE_SCRIPT = oub.version_root(VERSION) / "grade_workspace_native.py"
TERMINAL_ROOM_STATUSES = pbm_v5.TERMINAL_ROOM_STATUSES
USAGE_FIELDS = pbm_v5.USAGE_FIELDS


class OUBV2Error(oub.OUBError):
    """Raised when OUB v2 cannot preserve its comparison contract."""


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _manifest() -> dict[str, Any]:
    try:
        value = _read_json(MANIFEST_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        raise OUBV2Error("Unable to load OUB v2 manifest") from exc
    if value.get("schema") != "oub-v2-manifest-v1":
        raise OUBV2Error("Unexpected OUB v2 manifest schema")
    return value


def _task(task_id: str) -> dict[str, Any]:
    for item in _manifest().get("tasks") or []:
        if isinstance(item, dict) and item.get("id") == task_id:
            return item
    raise OUBV2Error(f"OUB v2 task not found: {task_id}")


def _run_root(run_id: str) -> Path:
    return RUNS_ROOT / run_id


def _state_path(run_id: str) -> Path:
    return _run_root(run_id) / "state.json"


def _load_state(run_id: str) -> dict[str, Any]:
    path = _state_path(run_id)
    if not path.is_file():
        raise OUBV2Error(f"OUB v2 state not found: {run_id}")
    return _read_json(path)


def _save_state(run_id: str, state: dict[str, Any]) -> None:
    _write_json(_state_path(run_id), state)


@contextmanager
def _state_lock(timeout_seconds: float = 10.0) -> Iterator[None]:
    LOCK_DIR.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout_seconds
    while True:
        try:
            LOCK_DIR.mkdir()
            break
        except FileExistsError:
            try:
                age = time.time() - LOCK_DIR.stat().st_mtime
            except OSError:
                age = 0.0
            if age > 60:
                try:
                    LOCK_DIR.rmdir()
                    continue
                except OSError:
                    pass
            if time.time() >= deadline:
                raise OUBV2Error("Timed out waiting for OUB v2 state lock")
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            LOCK_DIR.rmdir()
        except OSError:
            pass


def _set_arm(run_id: str, arm: str, value: dict[str, Any]) -> dict[str, Any]:
    with _state_lock():
        state = _load_state(run_id)
        state[arm] = value
        _save_state(run_id, state)
        return state


def _new_run_id(task_id: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"oub-v2-{task_id}-{stamp}"


def _active_run() -> str | None:
    if not ACTIVE_POINTER.is_file():
        return None
    try:
        value = _read_json(ACTIVE_POINTER)
    except (OSError, json.JSONDecodeError):
        return None
    run_id = value.get("run_id")
    if isinstance(run_id, str) and _state_path(run_id).is_file():
        return run_id
    return None


def _clear_active_if(run_id: str) -> None:
    if _active_run() == run_id:
        ACTIVE_POINTER.unlink(missing_ok=True)


def _result_path(state: dict[str, Any], arm: str) -> Path:
    return _run_root(str(state["run_id"])) / arm / "result.json"


def _evidence_dir(state: dict[str, Any], arm: str) -> Path:
    return _result_path(state, arm).parent


def _git_blob_sha(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(oub.PROJECT_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise OUBV2Error(f"Asset is outside the Codex Room repository: {path}") from exc
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(oub.PROJECT_ROOT),
            "hash-object",
            f"--path={relative}",
            str(path.resolve()),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        raise OUBV2Error(
            f"Unable to hash canonical Git asset {relative}: "
            + (proc.stdout or "").strip()[-1000:]
        )
    return proc.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 1200,
    text: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=text,
        timeout=timeout,
        check=False,
    )


def _git_text(args: list[str], *, cwd: Path | None = None, timeout: int = 1200) -> str:
    proc = _git(args, cwd=cwd, timeout=timeout)
    if proc.returncode != 0:
        raise OUBV2Error(
            f"git {' '.join(args)} failed: {(proc.stdout or '').strip()[-2000:]}"
        )
    return str(proc.stdout)


def _mission_text(task: dict[str, Any]) -> str:
    sections = [
        f"# OUB v2 external task — {task['id']}",
        "",
        "Implement both externally authored feature requirements below in this repository.",
        "Preserve existing behavior except where the requirements call for a change.",
        "Use normal development and self-verification practices.",
        "",
        "Do not inspect benchmark harness files, hidden tests, gold/reference patches, "
        "the other platform's workspace, or prior benchmark results outside this workspace.",
        "",
    ]
    for feature in task["features"]:
        spec = oub.version_root(VERSION) / str(feature["spec_file"])
        sections.extend(
            [
                f"## Feature {feature['id']}",
                "",
                spec.read_text(encoding="utf-8").rstrip(),
                "",
            ]
        )
    sections.extend(
        [
            "## Completion signal",
            "",
            "After implementation and self-verification are complete, create "
            "OUB_COMPLETE.json with exactly this JSON object:",
            "",
            '{"status":"complete"}',
            "",
            "Then stop. The completion file is only a harness signal; it is not part of grading.",
            "",
        ]
    )
    return "\n".join(sections)


def _workspace_start_state(workspace: Path) -> dict[str, Any]:
    head = _git_text(["rev-parse", "HEAD"], cwd=workspace).strip()
    tree = _git_text(["rev-parse", "HEAD^{tree}"], cwd=workspace).strip()
    status = _git_text(["status", "--porcelain", "--untracked-files=all"], cwd=workspace)
    mission = workspace / "BENCHMARK.md"
    if not mission.is_file():
        raise OUBV2Error("Prepared OUB v2 workspace is missing BENCHMARK.md")
    return {
        "head": head,
        "tree": tree,
        "status": status,
        "mission_sha256": _sha256(mission),
    }


def _ensure_empty_existing_root(workspace: Path) -> None:
    existing_files = sorted(
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file()
    )
    if existing_files:
        raise OUBV2Error(
            "Room workspace contains pre-existing files before OUB v2 repository "
            "population: " + ", ".join(existing_files[:20])
        )


def _materialize_workspace(
    workspace: Path,
    task: dict[str, Any],
    *,
    allow_existing_root: bool = False,
) -> dict[str, Any]:
    if workspace.exists() and not allow_existing_root:
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    if allow_existing_root:
        _ensure_empty_existing_root(workspace)

    commands = [
        ["init"],
        ["config", "core.longpaths", "true"],
        # The same measured workspace is inspected by Windows Git and WSL Git.
        # Pin line-ending conversion in the repository itself so WSL does not
        # reinterpret a Windows autocrlf checkout as a repository-wide change.
        ["config", "core.autocrlf", "false"],
        ["remote", "add", "origin", str(task["project_url"])],
        ["fetch", "--depth", "1", "origin", str(task["base_commit"])],
        ["checkout", "--detach", "FETCH_HEAD"],
    ]
    for command in commands:
        proc = _git(command, cwd=workspace)
        if proc.returncode != 0:
            raise OUBV2Error(
                f"Unable to materialize {task['id']} ({' '.join(command)}): "
                f"{(proc.stdout or '').strip()[-2000:]}"
            )

    head = _git_text(["rev-parse", "HEAD"], cwd=workspace).strip()
    if head != task["base_commit"]:
        raise OUBV2Error(
            f"Prepared {task['id']} at {head}, expected {task['base_commit']}"
        )
    before = _git_text(
        ["status", "--porcelain", "--untracked-files=all"], cwd=workspace
    )
    if before:
        raise OUBV2Error("Fresh external repository checkout is unexpectedly dirty")

    exclude = workspace / ".git" / "info" / "exclude"
    existing = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
    additions = ["/BENCHMARK.md", "/OUB_COMPLETE.json"]
    with exclude.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        for item in additions:
            if item not in existing.splitlines():
                handle.write(item + "\n")

    (workspace / "BENCHMARK.md").write_text(
        _mission_text(task),
        encoding="utf-8",
    )
    state = _workspace_start_state(workspace)
    if state["status"]:
        raise OUBV2Error(
            "Prepared workspace is not clean after excluding harness-only files"
        )
    return state


def _marker_ok(workspace: Path) -> bool:
    marker = workspace / "OUB_COMPLETE.json"
    if not marker.is_file():
        return False
    try:
        value = _read_json(marker)
    except (OSError, json.JSONDecodeError):
        return False
    return value == {"status": "complete"}


def _mission_unchanged(workspace: Path, expected_sha256: str) -> bool:
    mission = workspace / "BENCHMARK.md"
    return mission.is_file() and _sha256(mission) == expected_sha256


def _wsl_path(path: Path) -> str:
    proc = subprocess.run(
        ["wsl.exe", "wslpath", "-a", "-u", str(path.resolve())],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        raise OUBV2Error(
            "Unable to translate path for WSL grading: "
            + (proc.stdout or "").strip()[-1000:]
        )
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise OUBV2Error("WSL path translation returned no path")
    return lines[-1]


def _grade(workspace: Path, task_id: str) -> dict[str, Any]:
    if not GRADE_SCRIPT.is_file():
        raise OUBV2Error("OUB v2 WSL grader script is missing")
    script_wsl = _wsl_path(GRADE_SCRIPT)
    workspace_wsl = _wsl_path(workspace)
    proc = subprocess.run(
        [
            "wsl.exe",
            "-e",
            "python3",
            script_wsl,
            "--task-id",
            task_id,
            "--workspace",
            workspace_wsl,
        ],
        cwd=oub.PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=7200,
        check=False,
    )
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise OUBV2Error(
            "OUB v2 grader returned non-JSON output: "
            + (proc.stdout or "").strip()[-2000:]
        ) from exc
    if proc.returncode == 3 or result.get("infrastructure_error"):
        raise OUBV2Error(
            "OUB v2 grading infrastructure failure: "
            + str(result.get("infrastructure_error") or "unknown")
        )
    if proc.returncode not in {0, 1}:
        raise OUBV2Error(f"OUB v2 grader exited unexpectedly: {proc.returncode}")
    return result


def _workspace_change_evidence(
    workspace: Path,
    evidence: Path,
    base_commit: str,
) -> dict[str, Any]:
    patch_proc = _git(
        ["diff", "--binary", base_commit, "--"],
        cwd=workspace,
        text=False,
    )
    if patch_proc.returncode != 0:
        raise OUBV2Error("Unable to capture final candidate patch")
    patch_path = evidence / "candidate.patch"
    patch_path.write_bytes(bytes(patch_proc.stdout))

    changed = [
        line.strip()
        for line in _git_text(
            ["diff", "--name-only", base_commit, "--"], cwd=workspace
        ).splitlines()
        if line.strip()
    ]
    raw = _git(
        ["ls-files", "--others", "--exclude-standard", "-z"],
        cwd=workspace,
        text=False,
    )
    if raw.returncode != 0:
        raise OUBV2Error("Unable to enumerate final untracked files")
    untracked = [
        item.decode("utf-8", errors="surrogateescape")
        for item in bytes(raw.stdout).split(b"\0")
        if item
    ]

    untracked_zip = evidence / "candidate-untracked.zip"
    with zipfile.ZipFile(
        untracked_zip,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for rel in untracked:
            path = workspace / rel
            if path.is_file():
                archive.write(path, rel)

    head = _git_text(["rev-parse", "HEAD"], cwd=workspace).strip()
    status = _git_text(
        ["status", "--porcelain", "--untracked-files=all"],
        cwd=workspace,
    )
    metadata = {
        "base_commit": base_commit,
        "final_head": head,
        "changed_tracked_paths": sorted(changed),
        "untracked_paths": sorted(untracked),
        "git_status": status,
        "candidate_patch_bytes": patch_path.stat().st_size,
        "candidate_untracked_zip_bytes": untracked_zip.stat().st_size,
    }
    _write_json(evidence / "workspace-change-metadata.json", metadata)
    return metadata


def audit_harness() -> dict[str, Any]:
    manifest = _manifest()
    sample = _read_json(SAMPLE_PATH)
    plan = _read_json(PLAN_PATH)

    if manifest.get("version") != VERSION or manifest.get("mode") != "naturalistic":
        raise OUBV2Error("OUB v2 manifest identity/mode changed unexpectedly")
    protocol = manifest.get("protocol") or {}
    if protocol.get("comparison_unit") != "platform":
        raise OUBV2Error("OUB v2 comparison unit must be platform")
    if protocol.get("platform_internal_orchestration") != "unconstrained":
        raise OUBV2Error("OUB v2 must not prescribe internal orchestration")
    if protocol.get("composite_winner_score") is not False:
        raise OUBV2Error("OUB v2 must not define a composite winner score")
    if manifest.get("mission_paste") != PASTE:
        raise OUBV2Error("OUB v2 measured mission paste changed unexpectedly")

    manifest_tasks = manifest.get("tasks") or []
    sample_tasks = sample.get("tasks") or []
    plan_tasks = plan.get("tasks") or []
    if len(manifest_tasks) != 3 or len(sample_tasks) != 3 or len(plan_tasks) != 3:
        raise OUBV2Error("OUB v2 must contain exactly the frozen three-task sample")

    sample_by_id = {item["sample_id"]: item for item in sample_tasks}
    plan_by_id = {item["sample_id"]: item for item in plan_tasks}
    audited_assets = []
    for task in manifest_tasks:
        task_id = str(task["id"])
        if task_id not in sample_by_id or task_id not in plan_by_id:
            raise OUBV2Error(f"OUB v2 task missing from frozen sample/plan: {task_id}")
        sample_task = sample_by_id[task_id]
        plan_task = plan_by_id[task_id]
        if task["base_commit"] != sample_task["base_commit"] or task["base_commit"] != plan_task["base_commit"]:
            raise OUBV2Error(f"OUB v2 base commit mismatch: {task_id}")
        expected_features = [int(x) for x in sample_task["features"]]
        actual_features = [int(item["id"]) for item in task["features"]]
        if actual_features != expected_features:
            raise OUBV2Error(f"OUB v2 feature identity mismatch: {task_id}")

        plan_blobs = plan_task.get("asset_git_blobs") or {}
        for feature in task["features"]:
            spec = oub.version_root(VERSION) / str(feature["spec_file"])
            tests = oub.version_root(VERSION) / str(feature["tests_file"])
            if not spec.is_file() or not tests.is_file():
                raise OUBV2Error(f"OUB v2 frozen task/grading asset missing: {task_id}")
            spec_blob = _git_blob_sha(spec)
            tests_blob = _git_blob_sha(tests)
            if spec_blob != feature["spec_git_blob"]:
                raise OUBV2Error(f"OUB v2 spec blob mismatch: {spec}")
            if tests_blob != feature["tests_git_blob"]:
                raise OUBV2Error(f"OUB v2 tests blob mismatch: {tests}")
            if spec_blob not in plan_blobs.values() or tests_blob not in plan_blobs.values():
                raise OUBV2Error(
                    f"OUB v2 asset is not bound by the Phase-3 plan: {task_id}"
                )
            audited_assets.append(
                {
                    "task_id": task_id,
                    "feature": int(feature["id"]),
                    "spec_git_blob": spec_blob,
                    "tests_git_blob": tests_blob,
                }
            )

        mission = _mission_text(task)
        lowered = mission.lower()
        if "gold/reference patches" not in lowered or "hidden tests" not in lowered:
            raise OUBV2Error("OUB v2 mission must preserve hidden-evaluation prohibition")
        if "agent a" in lowered or "agent b" in lowered or "delegate" in lowered:
            raise OUBV2Error("OUB v2 mission must not prescribe Room orchestration")

    if not GRADE_SCRIPT.is_file():
        raise OUBV2Error("OUB v2 grader is missing")

    return {
        "ok": True,
        "benchmark_version": VERSION,
        "benchmark_fingerprint": oub.benchmark_fingerprint(VERSION),
        "task_ids": [str(item["id"]) for item in manifest_tasks],
        "audited_feature_assets": audited_assets,
        "current_pointer": oub.current_version(),
        "current_pointer_promoted": oub.current_version() == VERSION,
    }


def _require_repo() -> dict[str, str]:
    repo = pbm_v4._require_clean_tree()
    if repo["branch"] != "main":
        raise OUBV2Error(f"OUB v2 requires canonical main; found {repo['branch']}")
    audit_harness()
    return repo


def _desktop_workspace(run_id: str) -> Path:
    return _run_root(run_id) / "desktop-workspace"


def _room_payload(run_id: str, task: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": f"OUB v2 {task['id']} — {run_id}",
        "topic": PASTE,
        "auto_start": False,
        "max_turns": int(task["room_max_turns"]),
        "max_consecutive_passes": 3,
        "inactivity_seconds": int(task["safety_timeout_seconds"]),
        "starting_agent": "agent_c",
        "completion_policy": "auto_settle",
        "required_contributors": [],
        "work_model_version": 2,
        "provider_context_mode": "assignment_thread",
    }


def _cleanup_failed_room_preparation(room_base: str, room_id: str) -> str:
    try:
        pbm_v4._http_json(
            "POST",
            f"{room_base}/api/rooms/{room_id}/archive",
            {},
        )
        return "archived"
    except Exception as archive_exc:
        try:
            pbm_v4._http_json(
                "POST",
                f"{room_base}/api/rooms/{room_id}/stop",
                {},
            )
            return f"stopped_after_archive_error:{type(archive_exc).__name__}"
        except Exception as stop_exc:
            return (
                "cleanup_failed:"
                f"{type(archive_exc).__name__}:"
                f"{type(stop_exc).__name__}"
            )


def _spawn_worker(kind: str, run_id: str) -> int:
    if kind not in {"desktop", "room"}:
        raise OUBV2Error(f"Unsupported OUB v2 worker: {kind}")
    log_path = _run_root(run_id) / f"{kind}-worker.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("ab")
    kwargs: dict[str, Any] = {
        "cwd": str(oub.PROJECT_ROOT),
        "stdin": subprocess.DEVNULL,
        "stdout": log_handle,
        "stderr": subprocess.STDOUT,
        "close_fds": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
        )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "codex_room.oub_v2",
            f"{kind}-worker",
            "--run-id",
            run_id,
        ],
        **kwargs,
    )
    log_handle.close()
    return int(process.pid)


def _record_worker_started(run_id: str, arm: str, pid: int, status: str) -> None:
    with _state_lock():
        state = _load_state(run_id)
        info = dict(state[arm])
        info["worker_pid"] = pid
        info["status"] = status
        state[arm] = info
        _save_state(run_id, state)


def _bind_desktop_root(run_id: str, thread_id: str, rollout: Path) -> None:
    with _state_lock():
        state = _load_state(run_id)
        desktop = dict(state["desktop"])
        existing = desktop.get("root_thread_id")
        if existing not in {None, thread_id}:
            raise OUBV2Error(
                f"Desktop root binding changed from {existing} to {thread_id}"
            )
        desktop["root_thread_id"] = thread_id
        desktop["root_rollout_path"] = str(rollout.resolve())
        desktop["root_bound_at"] = pbm.utc_now()
        desktop["status"] = "running"
        state["desktop"] = desktop
        _save_state(run_id, state)


def _record_worker_error(run_id: str, arm: str, exc: Exception) -> None:
    error = {
        "schema": "oub-v2-worker-error-v1",
        "run_id": run_id,
        "platform": arm,
        "recorded_at": pbm.utc_now(),
        "error_type": type(exc).__name__,
        "error": str(exc),
    }
    _write_json(_run_root(run_id) / f"{arm}-worker-error.json", error)
    try:
        state = _load_state(run_id)
        info = state.get(arm)
        if isinstance(info, dict):
            _set_arm(
                run_id,
                arm,
                {**info, "status": "worker_error", "worker_error": error},
            )
        bundle(run_id)
    except Exception:
        pass


def prepare(
    task_id: str,
    room_base: str = pbm_v4.DEFAULT_ROOM_BASE,
    *,
    start_workers: bool = True,
) -> dict[str, Any]:
    active = _active_run()
    if active is not None:
        raise OUBV2Error(f"OUB v2 run already active: {active}")

    repo = _require_repo()
    audit = audit_harness()
    task = _task(task_id)
    run_id = _new_run_id(task_id)
    run_root = _run_root(run_id)
    run_root.mkdir(parents=True, exist_ok=False)

    desktop_workspace = _desktop_workspace(run_id)
    desktop_start = _materialize_workspace(desktop_workspace, task)

    health = pbm_v4._http_json("GET", f"{room_base}/api/health")
    if not isinstance(health, dict) or health.get("ok") is not True:
        shutil.rmtree(run_root, ignore_errors=True)
        raise OUBV2Error("Codex Room health endpoint did not report ok=true")

    room_id: str | None = None
    try:
        room = pbm_v4._http_json(
            "POST",
            f"{room_base}/api/rooms",
            _room_payload(run_id, task),
        )
        if isinstance(room, dict) and room.get("id"):
            room_id = str(room["id"])
        if (
            not isinstance(room, dict)
            or room_id is None
            or not room.get("active_round_id")
        ):
            raise OUBV2Error("Measured Room creation returned incomplete identifiers")

        round_id = str(room["active_round_id"])
        room_workspace = oub.PROJECT_ROOT / "data" / "rooms" / room_id / "shared"
        room_start = _materialize_workspace(
            room_workspace,
            task,
            allow_existing_root=True,
        )
        if desktop_start != room_start:
            raise OUBV2Error("Desktop and Room prepared starting states differ")
    except Exception as exc:
        cleanup = (
            _cleanup_failed_room_preparation(room_base, room_id)
            if room_id is not None
            else "room_not_created"
        )
        shutil.rmtree(run_root, ignore_errors=True)
        raise OUBV2Error(
            f"OUB v2 Room preparation failed; cleanup={cleanup}: {exc}"
        ) from exc

    prepared_at = pbm.utc_now()
    state = {
        "schema": "oub-v2-state-v1",
        "run_id": run_id,
        "benchmark_version": VERSION,
        "task_id": task_id,
        "benchmark_fingerprint": audit["benchmark_fingerprint"],
        "prepared_at": prepared_at,
        "repo": repo,
        "workspace_start": desktop_start,
        "desktop": {
            "status": "waiting_for_root_task" if start_workers else "prepared",
            "workspace": str(desktop_workspace.resolve()),
            "instruction": PASTE,
            "prepared_at": prepared_at,
            "root_thread_id": None,
            "worker_pid": None,
        },
        "room": {
            "status": "prepared",
            "room_base": room_base,
            "room_id": room_id,
            "round_id": round_id,
            "workspace": str(room_workspace.resolve()),
            "instruction": PASTE,
            "prepared_at": prepared_at,
            "worker_pid": None,
        },
        "workers_started": False,
        "mechanical_only": not start_workers,
        "complete": False,
        "aborted": False,
        "comparison": None,
        "finalization_error": None,
    }
    _save_state(run_id, state)
    _write_json(
        ACTIVE_POINTER,
        {
            "run_id": run_id,
            "task_id": task_id,
            "benchmark_fingerprint": state["benchmark_fingerprint"],
            "repo_head": repo["head"],
        },
    )

    if start_workers:
        desktop_pid = _spawn_worker("desktop", run_id)
        room_pid = _spawn_worker("room", run_id)
        _record_worker_started(run_id, "desktop", desktop_pid, "monitoring")
        _record_worker_started(run_id, "room", room_pid, "running")
        with _state_lock():
            latest = _load_state(run_id)
            latest["workers_started"] = True
            _save_state(run_id, latest)

    return {
        "action": "ready" if start_workers else "prepared_mechanical_only",
        "run_id": run_id,
        "benchmark_version": VERSION,
        "task_id": task_id,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "safety_timeout_minutes": int(task["safety_timeout_seconds"]) // 60,
        "desktop_workspace": str(desktop_workspace.resolve()),
        "desktop_instruction": PASTE,
        "desktop_note": (
            "Open one fresh top-level native Codex Desktop task rooted at desktop_workspace "
            "and send desktop_instruction exactly once. Desktop may use native descendants "
            "however it chooses."
            if start_workers
            else "Mechanical-only preparation: do not start a Desktop task."
        ),
        "room_id": room_id,
        "room_round_id": round_id,
        "room_note": (
            "The measured Room starts automatically; normal A/B/C coordination is unrestricted."
            if start_workers
            else "Mechanical-only preparation: the Room round is prepared but not started."
        ),
        "workspace_start": desktop_start,
    }


def desktop_finish(
    run_id: str,
    root_thread_id: str,
    *,
    safety_timeout: bool = False,
) -> dict[str, Any]:
    state = _load_state(run_id)
    if state["benchmark_fingerprint"] != oub.benchmark_fingerprint(VERSION):
        raise OUBV2Error("OUB v2 bytes changed after preparation")

    task = _task(str(state["task_id"]))
    desktop = state["desktop"]
    workspace = Path(str(desktop["workspace"]))
    root_rollout = pbm_v5.codex_usage.select_rollout(
        codex_home=pbm_v5.codex_usage.default_codex_home(),
        thread_id=root_thread_id,
        include_archived=True,
    )
    root_usage = pbm_v5.codex_usage.analyze_rollout(root_rollout)
    messages = pbm_v5.codex_usage.extract_user_messages(root_rollout)
    lineage_usage = pbm_v5._lineage_usage(root_thread_id)

    invalid: list[str] = []
    if len(messages) != 1:
        invalid.append(
            f"expected exactly one Desktop principal message; observed {len(messages)}"
        )
    elif messages[0].strip() != PASTE:
        invalid.append("Desktop principal message did not match the frozen OUB v2 mission")

    cwd = (root_usage.get("thread") or {}).get("cwd")
    if not isinstance(cwd, str) or pbm_v5._norm(cwd) != pbm_v5._norm(workspace):
        invalid.append("Desktop root task was not rooted at the prepared OUB v2 workspace")
    if not _mission_unchanged(
        workspace, str(state["workspace_start"]["mission_sha256"])
    ):
        invalid.append("Desktop modified the frozen BENCHMARK.md mission")

    failed: list[str] = []
    if not lineage_usage["usage_complete"]:
        failed.append("Desktop lineage provider usage is incomplete")
    if not _marker_ok(workspace):
        failed.append("Desktop OUB_COMPLETE.json marker is missing or invalid")
    if safety_timeout:
        failed.append(
            f"Desktop exceeded OUB v2 safety ceiling of {task['safety_timeout_seconds']} seconds"
        )

    quality = _grade(workspace, str(state["task_id"]))
    evidence = _evidence_dir(state, "desktop")
    evidence.mkdir(parents=True, exist_ok=True)
    workspace_meta = _workspace_change_evidence(
        workspace, evidence, str(task["base_commit"])
    )
    result = {
        "schema": "oub-v2-platform-result-v1",
        "run_id": run_id,
        "platform": "desktop",
        "benchmark_version": VERSION,
        "task_id": state["task_id"],
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "completed_at": pbm.utc_now(),
        "classification": pbm_v4._classification(invalid, failed),
        "invalid_reasons": invalid,
        "failed_reasons": failed,
        "valid_for_comparison": not invalid and not failed,
        "quality": quality,
        "usage": {
            field: lineage_usage[field] for field in USAGE_FIELDS
        }
        | {
            "tool_calls": lineage_usage["tool_calls"],
            "context_compactions": lineage_usage["context_compactions"],
            "thread_count": lineage_usage["thread_count"],
            "descendant_count": lineage_usage["descendant_count"],
        },
        "duration_seconds": lineage_usage["duration_seconds"],
        "human_involvement": {
            "principal_message_count": len(messages),
            "substantive_intervention_count": max(0, len(messages) - 1),
        },
        "provenance": {
            "root_thread_id": root_thread_id,
            "root_rollout_path": str(root_rollout.resolve()),
            "root_cwd": cwd,
            "observed_principal_messages": messages,
            "lineage": lineage_usage["lineage"],
            "model_configurations": None,
            "workspace_changes": workspace_meta,
        },
    }

    _write_json(evidence / "usage.json", lineage_usage)
    _write_json(evidence / "grade.json", quality)
    _write_json(evidence / "result.json", result)
    shutil.copy2(workspace / "BENCHMARK.md", evidence / "BENCHMARK.md")
    if (workspace / "OUB_COMPLETE.json").is_file():
        shutil.copy2(workspace / "OUB_COMPLETE.json", evidence / "OUB_COMPLETE.json")

    _set_arm(
        run_id,
        "desktop",
        {
            **desktop,
            "status": "complete",
            "classification": result["classification"],
            "completed_at": result["completed_at"],
        },
    )
    _finalize_if_ready(run_id)
    return result


def desktop_worker(
    run_id: str,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    state = _load_state(run_id)
    task = _task(str(state["task_id"]))
    timeout = int(timeout_seconds or task["safety_timeout_seconds"])
    desktop = state["desktop"]
    root_thread_id = desktop.get("root_thread_id")
    stable_signature = None
    stable_since = None
    deadline = time.time() + timeout

    try:
        while time.time() < deadline:
            latest = _load_state(run_id)
            if latest.get("aborted"):
                return {"run_id": run_id, "platform": "desktop", "aborted": True}
            desktop = latest["desktop"]

            if not root_thread_id:
                candidates = pbm_v5._desktop_candidates(desktop)
                if len(candidates) > 1:
                    ids = ", ".join(thread_id for _, thread_id in candidates)
                    raise OUBV2Error(
                        "multiple top-level Desktop tasks were started in the prepared "
                        f"workspace: {ids}"
                    )
                if len(candidates) == 1:
                    rollout, root_thread_id = candidates[0]
                    _bind_desktop_root(run_id, root_thread_id, rollout)

            if root_thread_id:
                workspace = Path(str(desktop["workspace"]))
                if _marker_ok(workspace):
                    signature = pbm_v5._lineage_signature(root_thread_id)
                    now = time.time()
                    if signature != stable_signature:
                        stable_signature = signature
                        stable_since = now
                    elif stable_since is not None and now - stable_since >= 5.0:
                        return desktop_finish(run_id, root_thread_id)
                else:
                    stable_signature = None
                    stable_since = None
            time.sleep(1)

        if root_thread_id:
            return desktop_finish(
                run_id,
                root_thread_id,
                safety_timeout=True,
            )
        raise OUBV2Error("No measured Desktop root task appeared before safety timeout")
    except Exception as exc:
        _record_worker_error(run_id, "desktop", exc)
        raise


def room_finish(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    task = _task(str(state["task_id"]))
    room_info = state["room"]
    base = str(room_info["room_base"])
    room_id = str(room_info["room_id"])
    round_id = str(room_info["round_id"])
    workspace = Path(str(room_info["workspace"]))

    if state["benchmark_fingerprint"] != oub.benchmark_fingerprint(VERSION):
        raise OUBV2Error("OUB v2 bytes changed after preparation")

    room = pbm_v4._http_json("GET", f"{base}/api/rooms/{room_id}")
    export = pbm_v4._http_json(
        "GET",
        f"{base}/api/rooms/{room_id}/export?format=json",
        timeout=60,
    )
    round_item = pbm_v5._room_round(export, round_id)

    intervention_reasons = pbm_v4.room_intervention_reasons(round_item)
    invalid = list(intervention_reasons)
    if pbm_v4._round_prompt(round_item) != PASTE:
        invalid.append("Measured Room prompt did not match the frozen OUB v2 mission")
    if not _mission_unchanged(
        workspace, str(state["workspace_start"]["mission_sha256"])
    ):
        invalid.append("Room modified the frozen BENCHMARK.md mission")
    invalid = sorted(set(invalid))

    try:
        aggregate = pbm.aggregate_room_export(export, round_id)
    except pbm.PBMError:
        aggregate = pbm_v5._empty_room_aggregate(round_item)

    failed: list[str] = []
    if (
        str(round_item.get("status") or "") != "finished"
        or round_item.get("close_reason") != "transaction_settled"
    ):
        failed.append(
            "Measured Room did not settle cleanly: "
            f"status={round_item.get('status') or 'unknown'} "
            f"close_reason={round_item.get('close_reason') or 'unknown'}"
        )
    if not aggregate["usage_complete"]:
        failed.append("Room execution usage is incomplete")
    if not _marker_ok(workspace):
        failed.append("Room OUB_COMPLETE.json marker is missing or invalid")

    quality = _grade(workspace, str(state["task_id"]))
    executions = pbm._room_execution_provenance(
        oub.PROJECT_ROOT / "data" / "codex-room.db",
        room_id,
        round_id,
    )
    evidence = _evidence_dir(state, "room")
    evidence.mkdir(parents=True, exist_ok=True)
    workspace_meta = _workspace_change_evidence(
        workspace, evidence, str(task["base_commit"])
    )
    model_configs = sorted(
        {
            (str(item.get("model")), str(item.get("reasoning_effort")))
            for item in executions
            if item.get("model")
        }
    )
    result = {
        "schema": "oub-v2-platform-result-v1",
        "run_id": run_id,
        "platform": "room",
        "benchmark_version": VERSION,
        "task_id": state["task_id"],
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "completed_at": pbm.utc_now(),
        "classification": pbm_v4._classification(invalid, failed),
        "invalid_reasons": invalid,
        "failed_reasons": failed,
        "valid_for_comparison": not invalid and not failed,
        "quality": quality,
        "usage": {
            **aggregate["total"],
            "tool_calls": aggregate["tool_calls"],
            "failed_tool_calls": aggregate["failed_tool_calls"],
            "execution_count": aggregate["execution_count"],
            "peer_invocations": aggregate["peer_invocations"],
        },
        "duration_seconds": aggregate["duration_seconds"],
        "human_involvement": {
            "substantive_intervention_count": len(intervention_reasons),
            "intervention_reasons": intervention_reasons,
        },
        "provenance": {
            "room_id": room_id,
            "round_id": round_id,
            "room_status": room.get("status"),
            "round_status": round_item.get("status"),
            "close_reason": round_item.get("close_reason"),
            "executions_by_agent": aggregate["executions_by_agent"],
            "executions": executions,
            "model_configurations": [
                {"model": model, "reasoning_effort": effort}
                for model, effort in model_configs
            ],
            "workspace_changes": workspace_meta,
        },
    }

    _write_json(evidence / "room-export.json", export)
    _write_json(evidence / "grade.json", quality)
    _write_json(evidence / "result.json", result)
    shutil.copy2(workspace / "BENCHMARK.md", evidence / "BENCHMARK.md")
    if (workspace / "OUB_COMPLETE.json").is_file():
        shutil.copy2(workspace / "OUB_COMPLETE.json", evidence / "OUB_COMPLETE.json")

    _set_arm(
        run_id,
        "room",
        {
            **room_info,
            "status": "complete",
            "classification": result["classification"],
            "completed_at": result["completed_at"],
        },
    )
    _finalize_if_ready(run_id)
    return result


def room_worker(
    run_id: str,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    state = _load_state(run_id)
    task = _task(str(state["task_id"]))
    timeout = int(timeout_seconds or task["safety_timeout_seconds"])
    room_info = state["room"]
    base = str(room_info["room_base"])
    room_id = str(room_info["room_id"])
    round_id = str(room_info["round_id"])

    try:
        pbm_v4._http_json(
            "POST",
            f"{base}/api/rooms/{room_id}/rounds/{round_id}/start",
            {},
        )
        deadline = time.time() + timeout
        while time.time() < deadline:
            latest = _load_state(run_id)
            if latest.get("aborted"):
                return {"run_id": run_id, "platform": "room", "aborted": True}
            room = pbm_v4._http_json("GET", f"{base}/api/rooms/{room_id}")
            if str(room.get("status") or "") in TERMINAL_ROOM_STATUSES:
                break
            export = pbm_v4._http_json(
                "GET",
                f"{base}/api/rooms/{room_id}/export?format=json",
                timeout=30,
            )
            round_item = pbm_v5._room_round(export, round_id)
            if pbm_v4.room_intervention_reasons(round_item):
                pbm_v4._http_json("POST", f"{base}/api/rooms/{room_id}/stop", {})
                break
            time.sleep(1)
        else:
            pbm_v4._http_json("POST", f"{base}/api/rooms/{room_id}/stop", {})
            raise OUBV2Error(
                f"Measured Room {room_id} exceeded {timeout} seconds"
            )
        return room_finish(run_id)
    except Exception as exc:
        _record_worker_error(run_id, "room", exc)
        raise


def _comparison(state: dict[str, Any]) -> dict[str, Any]:
    desktop = _read_json(_result_path(state, "desktop"))
    room = _read_json(_result_path(state, "room"))
    same_fingerprint = (
        desktop.get("benchmark_fingerprint")
        == room.get("benchmark_fingerprint")
        == state.get("benchmark_fingerprint")
    )
    comparable = (
        desktop.get("classification") == "VALID"
        and room.get("classification") == "VALID"
        and same_fingerprint
    )

    d_tokens = (desktop.get("usage") or {}).get("total_tokens")
    r_tokens = (room.get("usage") or {}).get("total_tokens")
    token_ratio = (
        round(float(r_tokens) / float(d_tokens), 4)
        if isinstance(d_tokens, (int, float))
        and d_tokens > 0
        and isinstance(r_tokens, (int, float))
        else None
    )
    d_duration = desktop.get("duration_seconds")
    r_duration = room.get("duration_seconds")
    duration_ratio = (
        round(float(r_duration) / float(d_duration), 4)
        if isinstance(d_duration, (int, float))
        and d_duration > 0
        and isinstance(r_duration, (int, float))
        else None
    )

    def platform_summary(value: dict[str, Any], platform: str) -> dict[str, Any]:
        usage = value.get("usage") or {}
        quality = value.get("quality") or {}
        provenance = value.get("provenance") or {}
        summary = {
            "classification": value.get("classification"),
            "pass": quality.get("pass"),
            "passed_features": quality.get("passed_features"),
            "total_features": quality.get("total_features"),
            "total_tokens": usage.get("total_tokens"),
            "duration_seconds": value.get("duration_seconds"),
            "tool_calls": usage.get("tool_calls"),
            "human_involvement": value.get("human_involvement"),
            "model_configurations": provenance.get("model_configurations"),
        }
        if platform == "desktop":
            summary.update(
                {
                    "thread_count": usage.get("thread_count"),
                    "descendant_count": usage.get("descendant_count"),
                }
            )
        else:
            summary.update(
                {
                    "execution_count": usage.get("execution_count"),
                    "peer_invocations": usage.get("peer_invocations"),
                }
            )
        return summary

    return {
        "schema": "oub-v2-comparison-v1",
        "run_id": state["run_id"],
        "benchmark_version": VERSION,
        "task_id": state["task_id"],
        "benchmark_fingerprint": (
            state["benchmark_fingerprint"] if same_fingerprint else None
        ),
        "same_fingerprint": same_fingerprint,
        "comparable": comparable,
        "desktop": platform_summary(desktop, "desktop"),
        "room": platform_summary(room, "room"),
        "room_to_desktop_total_token_ratio": token_ratio,
        "room_to_desktop_duration_ratio": duration_ratio,
        "interpretation_note": (
            "OUB v2 reports objective feature-test outcomes, cost, duration, "
            "organization, model-allocation provenance where available, and human "
            "intervention separately. It does not compute a composite platform score "
            "or overall ranking."
        ),
    }


def _comparison_markdown(value: dict[str, Any]) -> str:
    desktop = value["desktop"]
    room = value["room"]
    lines = [
        f"# OUB v2 comparison — {value['task_id']} — {value['run_id']}",
        "",
        f"- Comparable: **{str(bool(value['comparable'])).lower()}**",
        f"- Same benchmark fingerprint: **{str(bool(value['same_fingerprint'])).lower()}**",
        "",
        "| Platform | Classification | Feature tests | Total tokens | Duration (s) |",
        "|---|---:|---:|---:|---:|",
        f"| Desktop | {desktop.get('classification')} | "
        f"{desktop.get('passed_features')}/{desktop.get('total_features')} | "
        f"{desktop.get('total_tokens')} | {desktop.get('duration_seconds')} |",
        f"| Room | {room.get('classification')} | "
        f"{room.get('passed_features')}/{room.get('total_features')} | "
        f"{room.get('total_tokens')} | {room.get('duration_seconds')} |",
        "",
        f"- Room/Desktop token ratio: {value.get('room_to_desktop_total_token_ratio')}",
        f"- Room/Desktop duration ratio: {value.get('room_to_desktop_duration_ratio')}",
        f"- Desktop measured threads: {desktop.get('thread_count')} "
        f"(descendants: {desktop.get('descendant_count')})",
        f"- Room measured executions: {room.get('execution_count')} "
        f"(peer invocations: {room.get('peer_invocations')})",
        "",
        value["interpretation_note"],
    ]
    return "\n".join(lines) + "\n"


def _finalize_if_ready(run_id: str) -> dict[str, Any] | None:
    with _state_lock():
        state = _load_state(run_id)
        if state.get("complete"):
            return {
                "run_id": run_id,
                "complete": True,
                "comparison": state.get("comparison"),
            }
        if state.get("aborted") or state.get("finalizing"):
            return None
        if not all(_result_path(state, arm).is_file() for arm in ("desktop", "room")):
            return None
        state["finalizing"] = True
        _save_state(run_id, state)

    try:
        state = _load_state(run_id)
        comparison = _comparison(state)
        root = _run_root(run_id)
        _write_json(root / "oub-v2-comparison.json", comparison)
        (root / "oub-v2-comparison.md").write_text(
            _comparison_markdown(comparison),
            encoding="utf-8",
        )
        with _state_lock():
            state = _load_state(run_id)
            state["finalizing"] = False
            state["complete"] = True
            state["completed_at"] = pbm.utc_now()
            state["comparison"] = comparison
            _save_state(run_id, state)
            _clear_active_if(run_id)
        evidence_bundle = bundle(run_id)
        return {
            "run_id": run_id,
            "complete": True,
            "comparison": comparison,
            "bundle": evidence_bundle,
        }
    except Exception as exc:
        with _state_lock():
            state = _load_state(run_id)
            state["finalizing"] = False
            state["finalization_error"] = {
                "recorded_at": pbm.utc_now(),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            _save_state(run_id, state)
        raise


def bundle(run_id: str) -> dict[str, Any]:
    root = _run_root(run_id)
    if not root.is_dir():
        raise OUBV2Error(f"OUB v2 run not found: {run_id}")
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    destination = BUNDLE_ROOT / f"{run_id}-evidence.zip"
    temp = destination.with_suffix(".tmp")
    temp.unlink(missing_ok=True)
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            if "desktop-workspace" in path.parts:
                continue
            archive.write(path, path.relative_to(root))
    os.replace(temp, destination)
    return {
        "run_id": run_id,
        "bundle_path": str(destination.resolve()),
        "size_bytes": destination.stat().st_size,
    }


def status(run_id: str | None = None) -> dict[str, Any]:
    if run_id is None:
        run_id = _active_run()
        if run_id is None:
            return {"active": False}
    state = _load_state(run_id)
    if (
        not state.get("complete")
        and not state.get("aborted")
        and all(_result_path(state, arm).is_file() for arm in ("desktop", "room"))
    ):
        _finalize_if_ready(run_id)
        state = _load_state(run_id)
    return {
        "active": not state.get("complete") and not state.get("aborted"),
        "run_id": run_id,
        "benchmark_version": state.get("benchmark_version"),
        "task_id": state.get("task_id"),
        "benchmark_fingerprint": state.get("benchmark_fingerprint"),
        "mechanical_only": state.get("mechanical_only"),
        "workers_started": state.get("workers_started"),
        "desktop": state.get("desktop"),
        "room": state.get("room"),
        "complete": state.get("complete"),
        "aborted": state.get("aborted"),
        "comparison": state.get("comparison"),
        "finalization_error": state.get("finalization_error"),
    }


def _stop_worker(pid: Any) -> str:
    if not isinstance(pid, int) or pid <= 0:
        return "not_running"
    try:
        os.kill(pid, signal.SIGTERM)
        return "stop_requested"
    except ProcessLookupError:
        return "already_exited"
    except OSError as exc:
        return f"error: {type(exc).__name__}"


def abort(run_id: str | None = None) -> dict[str, Any]:
    if run_id is None:
        run_id = _active_run()
    if run_id is None:
        raise OUBV2Error("No active OUB v2 run exists")

    state = _load_state(run_id)
    desktop_action = _stop_worker((state.get("desktop") or {}).get("worker_pid"))
    room_action = _stop_worker((state.get("room") or {}).get("worker_pid"))

    room_stop = "not_started"
    room_info = state.get("room")
    if isinstance(room_info, dict):
        try:
            room = pbm_v4._http_json(
                "GET",
                f"{room_info['room_base']}/api/rooms/{room_info['room_id']}",
            )
            if str(room.get("status") or "") not in TERMINAL_ROOM_STATUSES:
                pbm_v4._http_json(
                    "POST",
                    f"{room_info['room_base']}/api/rooms/{room_info['room_id']}/stop",
                    {},
                )
                room_stop = "stopped"
            else:
                room_stop = f"already_{room.get('status')}"
        except pbm.PBMError as exc:
            room_stop = f"error: {exc}"

    with _state_lock():
        state = _load_state(run_id)
        state["aborted"] = True
        state["aborted_at"] = pbm.utc_now()
        _save_state(run_id, state)
        _clear_active_if(run_id)

    return {
        "run_id": run_id,
        "aborted": True,
        "desktop_worker_action": desktop_action,
        "room_worker_action": room_action,
        "room_action": room_stop,
        "desktop_note": (
            "OUB does not own Desktop's native task lifecycle. If a measured Desktop "
            "task was started and remains active, stop it in Codex Desktop."
        ),
        "bundle": bundle(run_id),
    }


def grade_command(task_id: str, workspace: Path) -> dict[str, Any]:
    audit_harness()
    return _grade(workspace, task_id)


def _json_out(value: Any) -> None:
    # Keep CLI JSON safe on Windows consoles that still expose legacy code pages
    # such as cp1252. JSON unicode escapes preserve the exact string value while
    # avoiding host-terminal encoding failures after successful grading.
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oub-v2")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("prepare")
    command.add_argument("--task-id", required=True, choices=["o2-1", "o2-2", "o2-3"])
    command.add_argument("--room-base", default=pbm_v4.DEFAULT_ROOM_BASE)
    command.add_argument(
        "--no-start",
        action="store_true",
        help="prepare equivalent Desktop/Room workspaces without starting cognition",
    )

    command = sub.add_parser("desktop-worker")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("room-worker")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("grade")
    command.add_argument("--task-id", required=True, choices=["o2-1", "o2-2", "o2-3"])
    command.add_argument("--workspace", required=True)

    command = sub.add_parser("status")
    command.add_argument("--run-id")

    command = sub.add_parser("abort")
    command.add_argument("--run-id")

    command = sub.add_parser("bundle")
    command.add_argument("--run-id", required=True)

    sub.add_parser("audit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            value = prepare(
                args.task_id,
                args.room_base,
                start_workers=not args.no_start,
            )
        elif args.command == "desktop-worker":
            value = desktop_worker(args.run_id)
        elif args.command == "room-worker":
            value = room_worker(args.run_id)
        elif args.command == "grade":
            value = grade_command(args.task_id, Path(args.workspace))
        elif args.command == "status":
            value = status(args.run_id)
        elif args.command == "abort":
            value = abort(args.run_id)
        elif args.command == "bundle":
            value = bundle(args.run_id)
        elif args.command == "audit":
            value = audit_harness()
        else:
            raise OUBV2Error("unsupported OUB v2 command")
    except (
        OUBV2Error,
        oub.OUBError,
        pbm.PBMError,
        pbm_v5.PBMV5Error,
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    _json_out(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
