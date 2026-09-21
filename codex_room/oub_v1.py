"""OUB v1: naturalistic Desktop versus Room organizational-utility harness."""

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


VERSION = "v1"
TASK_ID = "o01-competing-root-causes"
FROZEN_BENCHMARK_FINGERPRINT = "d6ec60fca42c6dd436b15d4f8621bb711056b1da5aa93f5a6ecaee2188ba4835"
PASTE = (
    oub.version_root(VERSION)
    / "prompts"
    / "o01-competing-root-causes.txt"
).read_text(encoding="utf-8").strip()
OUTPUT_ROOT = oub.PROJECT_ROOT / "output" / "oub"
RUNS_ROOT = OUTPUT_ROOT / "runs"
ACTIVE_POINTER = OUTPUT_ROOT / "v1-active.json"
BUNDLE_ROOT = OUTPUT_ROOT / "v1-bundles"
LOCK_DIR = OUTPUT_ROOT / ".v1-state-lock"
TERMINAL_ROOM_STATUSES = pbm_v5.TERMINAL_ROOM_STATUSES
USAGE_FIELDS = pbm_v5.USAGE_FIELDS
SAFETY_TIMEOUT_SECONDS = 1800


class OUBV1Error(oub.OUBError):
    """Raised when OUB v1 cannot preserve its platform-comparison contract."""


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _run_root(run_id: str) -> Path:
    return RUNS_ROOT / run_id


def _state_path(run_id: str) -> Path:
    return _run_root(run_id) / "state.json"


def _load_state(run_id: str) -> dict[str, Any]:
    path = _state_path(run_id)
    if not path.is_file():
        raise OUBV1Error(f"OUB v1 state not found: {run_id}")
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
                raise OUBV1Error("Timed out waiting for OUB v1 state lock")
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


def _new_run_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"oub-v1-o01-{stamp}"


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


def _fixture_dir() -> Path:
    manifest = oub.load_manifest(VERSION)
    task = next(
        (
            item
            for item in manifest.get("tasks", [])
            if isinstance(item, dict) and item.get("id") == TASK_ID
        ),
        None,
    )
    if not isinstance(task, dict):
        raise OUBV1Error(f"OUB task missing from manifest: {TASK_ID}")
    path = oub.version_root(VERSION) / str(task["fixture_dir"])
    if not path.is_dir():
        raise OUBV1Error(f"OUB fixture directory missing: {path}")
    return path


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture_hashes(workspace: Path) -> dict[str, str]:
    source = _fixture_dir()
    result: dict[str, str] = {}
    for source_path in sorted(item for item in source.rglob("*") if item.is_file()):
        rel = source_path.relative_to(source).as_posix()
        workspace_path = workspace / rel
        if not workspace_path.is_file():
            raise OUBV1Error(f"Prepared fixture file missing: {rel}")
        result[rel] = _file_hash(workspace_path)
    return result


def _fixture_unchanged(workspace: Path, expected: dict[str, str]) -> tuple[bool, list[str]]:
    changed: list[str] = []
    for rel, digest in expected.items():
        path = workspace / rel
        if not path.is_file() or _file_hash(path) != digest:
            changed.append(rel)
    return not changed, changed


def _prepare_workspace(
    workspace: Path,
    *,
    allow_existing_root: bool = False,
) -> dict[str, str]:
    source = _fixture_dir()
    if workspace.exists() and not allow_existing_root:
        shutil.rmtree(workspace)

    workspace.mkdir(parents=True, exist_ok=True)

    if allow_existing_root:
        existing_files = sorted(
            path.relative_to(workspace).as_posix()
            for path in workspace.rglob("*")
            if path.is_file()
        )
        if existing_files:
            raise OUBV1Error(
                "Room workspace contains pre-existing files before OUB fixture "
                "population: " + ", ".join(existing_files)
            )

    for source_path in sorted(source.rglob("*")):
        rel = source_path.relative_to(source)
        destination = workspace / rel
        if source_path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        if destination.exists():
            raise OUBV1Error(
                f"OUB fixture would overwrite existing workspace path: {destination}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)

    return _fixture_hashes(workspace)


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


def _required_artifacts_present(workspace: Path) -> bool:
    return (
        (workspace / "FINDINGS.json").is_file()
        and (workspace / "INCIDENT_REPORT.md").is_file()
    )


def audit_harness() -> dict[str, Any]:
    asset = oub.audit_assets(VERSION)
    fingerprint = oub.benchmark_fingerprint(VERSION)
    if fingerprint != FROZEN_BENCHMARK_FINGERPRINT:
        raise OUBV1Error(
            "Frozen OUB v1 fingerprint changed: "
            f"expected {FROZEN_BENCHMARK_FINGERPRINT}, found {fingerprint}"
        )
    if current := oub.current_version():
        if current != VERSION:
            raise OUBV1Error(f"OUB CURRENT must be {VERSION}; found {current}")
    if PASTE != "Read BENCHMARK.md and execute it exactly. Do not ask me questions. When complete, stop.":
        raise OUBV1Error("OUB v1 measured mission changed unexpectedly")
    return {
        "ok": True,
        "benchmark_version": VERSION,
        "task_id": TASK_ID,
        "benchmark_fingerprint": fingerprint,
        "asset_audit": asset,
        "safety_timeout_seconds": SAFETY_TIMEOUT_SECONDS,
    }


def _require_repo() -> dict[str, str]:
    repo = pbm_v4._require_clean_tree()
    if repo["branch"] != "main":
        raise OUBV1Error(f"OUB v1 requires canonical main; found {repo['branch']}")
    audit_harness()
    return repo


def _desktop_workspace(run_id: str) -> Path:
    return _run_root(run_id) / "desktop-workspace"


def _room_payload(run_id: str) -> dict[str, Any]:
    return {
        "title": f"OUB v1 O1 — {run_id}",
        "topic": PASTE,
        "auto_start": False,
        "max_turns": 40,
        "max_consecutive_passes": 3,
        "inactivity_seconds": 1800,
        "starting_agent": "agent_c",
        "completion_policy": "auto_settle",
        "required_contributors": [],
        "work_model_version": 2,
        "provider_context_mode": "assignment_thread",
    }


def _spawn_worker(kind: str, run_id: str) -> int:
    if kind not in {"desktop", "room"}:
        raise OUBV1Error(f"Unsupported OUB v1 worker: {kind}")
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
            "codex_room.oub_v1",
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
        if info.get("status") in {"prepared", "waiting_for_root_task"}:
            info["status"] = status
        state[arm] = info
        _save_state(run_id, state)


def prepare(room_base: str = pbm_v4.DEFAULT_ROOM_BASE) -> dict[str, Any]:
    active = _active_run()
    if active is not None:
        raise OUBV1Error(f"OUB v1 run already active: {active}")

    repo = _require_repo()
    audit = audit_harness()
    run_id = _new_run_id()
    run_root = _run_root(run_id)
    run_root.mkdir(parents=True, exist_ok=False)

    desktop_workspace = _desktop_workspace(run_id)
    desktop_hashes = _prepare_workspace(desktop_workspace)

    health = pbm_v4._http_json("GET", f"{room_base}/api/health")
    if not isinstance(health, dict) or health.get("ok") is not True:
        raise OUBV1Error("Codex Room health endpoint did not report ok=true")

    room_id: str | None = None
    try:
        room = pbm_v4._http_json(
            "POST",
            f"{room_base}/api/rooms",
            _room_payload(run_id),
        )
        if isinstance(room, dict) and room.get("id"):
            room_id = str(room["id"])
        if (
            not isinstance(room, dict)
            or room_id is None
            or not room.get("active_round_id")
        ):
            raise OUBV1Error("Measured Room creation returned incomplete identifiers")

        round_id = str(room["active_round_id"])
        room_workspace = oub.PROJECT_ROOT / "data" / "rooms" / room_id / "shared"
        room_hashes = _prepare_workspace(
            room_workspace,
            allow_existing_root=True,
        )
        if desktop_hashes != room_hashes:
            raise OUBV1Error("Desktop and Room prepared fixture hashes differ")
    except Exception as exc:
        cleanup = (
            _cleanup_failed_room_preparation(room_base, room_id)
            if room_id is not None
            else "room_not_created"
        )
        shutil.rmtree(run_root, ignore_errors=True)
        raise OUBV1Error(
            f"OUB Room preparation failed before measurement; cleanup={cleanup}: {exc}"
        ) from exc

    prepared_at = pbm.utc_now()
    state = {
        "schema": "oub-v1-state-v1",
        "run_id": run_id,
        "benchmark_version": VERSION,
        "task_id": TASK_ID,
        "benchmark_fingerprint": audit["benchmark_fingerprint"],
        "prepared_at": prepared_at,
        "repo": repo,
        "audit": audit,
        "fixture_hashes": desktop_hashes,
        "desktop": {
            "status": "waiting_for_root_task",
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
            "benchmark_fingerprint": state["benchmark_fingerprint"],
            "repo_head": repo["head"],
        },
    )

    desktop_pid = _spawn_worker("desktop", run_id)
    room_pid = _spawn_worker("room", run_id)
    _record_worker_started(run_id, "desktop", desktop_pid, "monitoring")
    _record_worker_started(run_id, "room", room_pid, "running")

    return {
        "action": "ready",
        "run_id": run_id,
        "benchmark_version": VERSION,
        "task_id": TASK_ID,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "target_runtime_minutes": audit["asset_audit"]["target_runtime_minutes"],
        "safety_timeout_minutes": SAFETY_TIMEOUT_SECONDS // 60,
        "desktop_workspace": str(desktop_workspace.resolve()),
        "desktop_instruction": PASTE,
        "desktop_note": (
            "Open one fresh top-level native Codex Desktop task rooted at desktop_workspace "
            "and send desktop_instruction exactly once. Desktop may organize its work and "
            "use native descendants however it chooses."
        ),
        "room_id": room_id,
        "room_round_id": round_id,
        "room_note": (
            "The measured Room is started automatically. Normal A/B/C coordination is "
            "unrestricted by OUB."
        ),
    }


def _bind_desktop_root(run_id: str, thread_id: str, rollout: Path) -> None:
    with _state_lock():
        state = _load_state(run_id)
        desktop = dict(state["desktop"])
        existing = desktop.get("root_thread_id")
        if existing not in {None, thread_id}:
            raise OUBV1Error(
                f"Desktop root binding changed from {existing} to {thread_id}"
            )
        desktop["root_thread_id"] = thread_id
        desktop["root_rollout_path"] = str(rollout.resolve())
        desktop["root_bound_at"] = pbm.utc_now()
        desktop["status"] = "running"
        state["desktop"] = desktop
        _save_state(run_id, state)


def _grade(workspace: Path) -> dict[str, Any]:
    return oub.grade_workspace(workspace, version=VERSION, task_id=TASK_ID)


def desktop_finish(
    run_id: str,
    root_thread_id: str,
    *,
    safety_timeout: bool = False,
) -> dict[str, Any]:
    state = _load_state(run_id)
    if state["benchmark_fingerprint"] != oub.benchmark_fingerprint(VERSION):
        raise OUBV1Error("OUB v1 fingerprint changed after preparation")

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
        invalid.append("Desktop principal message did not match the frozen OUB mission")

    cwd = (root_usage.get("thread") or {}).get("cwd")
    if not isinstance(cwd, str) or pbm_v5._norm(cwd) != pbm_v5._norm(workspace):
        invalid.append("Desktop root task was not rooted at the prepared OUB workspace")

    fixture_ok, changed_fixture = _fixture_unchanged(
        workspace, dict(state["fixture_hashes"])
    )
    if not fixture_ok:
        invalid.append(
            "Desktop modified frozen starting evidence: " + ", ".join(changed_fixture)
        )

    failed: list[str] = []
    if not lineage_usage["usage_complete"]:
        failed.append("Desktop lineage provider usage is incomplete")
    if not _required_artifacts_present(workspace):
        failed.append("Desktop required OUB artifacts are missing")
    if safety_timeout:
        failed.append(
            f"Desktop exceeded OUB harness safety ceiling of {SAFETY_TIMEOUT_SECONDS} seconds"
        )

    quality = _grade(workspace)
    result = {
        "schema": "oub-v1-platform-result-v1",
        "run_id": run_id,
        "platform": "desktop",
        "benchmark_version": VERSION,
        "task_id": TASK_ID,
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
        "provenance": {
            "root_thread_id": root_thread_id,
            "root_rollout_path": str(root_rollout.resolve()),
            "root_cwd": cwd,
            "observed_principal_messages": messages,
            "lineage": lineage_usage["lineage"],
            "fixture_changed": changed_fixture,
        },
    }

    evidence = _evidence_dir(state, "desktop")
    evidence.mkdir(parents=True, exist_ok=True)
    _write_json(evidence / "usage.json", lineage_usage)
    _write_json(evidence / "grade.json", quality)
    _write_json(evidence / "result.json", result)
    final_workspace = evidence / "workspace-final"
    if final_workspace.exists():
        shutil.rmtree(final_workspace)
    shutil.copytree(workspace, final_workspace)

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
    timeout_seconds: int = SAFETY_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    state = _load_state(run_id)
    desktop = state["desktop"]
    root_thread_id = desktop.get("root_thread_id")
    stable_signature = None
    stable_since = None
    deadline = time.time() + timeout_seconds

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
                    raise OUBV1Error(
                        "multiple top-level Desktop tasks were started in the prepared "
                        f"workspace: {ids}"
                    )
                if len(candidates) == 1:
                    rollout, root_thread_id = candidates[0]
                    _bind_desktop_root(run_id, root_thread_id, rollout)

            if root_thread_id:
                workspace = Path(str(desktop["workspace"]))
                if _required_artifacts_present(workspace):
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
        raise OUBV1Error("No measured Desktop root task appeared before safety timeout")
    except Exception as exc:
        _record_worker_error(run_id, "desktop", exc)
        raise


def room_finish(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    room_info = state["room"]
    base = str(room_info["room_base"])
    room_id = str(room_info["room_id"])
    round_id = str(room_info["round_id"])
    workspace = Path(str(room_info["workspace"]))

    room = pbm_v4._http_json("GET", f"{base}/api/rooms/{room_id}")
    export = pbm_v4._http_json(
        "GET",
        f"{base}/api/rooms/{room_id}/export?format=json",
        timeout=60,
    )
    round_item = pbm_v5._room_round(export, round_id)

    invalid = pbm_v4.room_intervention_reasons(round_item)
    if pbm_v4._round_prompt(round_item) != PASTE:
        invalid.append("Measured Room prompt did not match the frozen OUB mission")

    fixture_ok, changed_fixture = _fixture_unchanged(
        workspace, dict(state["fixture_hashes"])
    )
    if not fixture_ok:
        invalid.append(
            "Room modified frozen starting evidence: " + ", ".join(changed_fixture)
        )
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
    if not _required_artifacts_present(workspace):
        failed.append("Room required OUB artifacts are missing")

    quality = _grade(workspace)
    executions = pbm._room_execution_provenance(
        oub.PROJECT_ROOT / "data" / "codex-room.db",
        room_id,
        round_id,
    )
    result = {
        "schema": "oub-v1-platform-result-v1",
        "run_id": run_id,
        "platform": "room",
        "benchmark_version": VERSION,
        "task_id": TASK_ID,
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
        "provenance": {
            "room_id": room_id,
            "round_id": round_id,
            "room_status": room.get("status"),
            "round_status": round_item.get("status"),
            "close_reason": round_item.get("close_reason"),
            "executions_by_agent": aggregate["executions_by_agent"],
            "executions": executions,
            "fixture_changed": changed_fixture,
        },
    }

    evidence = _evidence_dir(state, "room")
    evidence.mkdir(parents=True, exist_ok=True)
    _write_json(evidence / "room-export.json", export)
    _write_json(evidence / "grade.json", quality)
    _write_json(evidence / "result.json", result)
    final_workspace = evidence / "workspace-final"
    if final_workspace.exists():
        shutil.rmtree(final_workspace)
    shutil.copytree(workspace, final_workspace)

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
    timeout_seconds: int = SAFETY_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    state = _load_state(run_id)
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
        deadline = time.time() + timeout_seconds
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
            raise OUBV1Error(
                f"Measured Room {room_id} exceeded {timeout_seconds} seconds"
            )
        return room_finish(run_id)
    except Exception as exc:
        _record_worker_error(run_id, "room", exc)
        raise


def _record_worker_error(run_id: str, arm: str, exc: Exception) -> None:
    error = {
        "schema": "oub-v1-worker-error-v1",
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

    d_score = (desktop.get("quality") or {}).get("score")
    r_score = (room.get("quality") or {}).get("score")
    score_delta = (
        int(r_score) - int(d_score)
        if isinstance(d_score, int) and isinstance(r_score, int)
        else None
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

    return {
        "schema": "oub-v1-comparison-v1",
        "run_id": state["run_id"],
        "benchmark_version": VERSION,
        "task_id": TASK_ID,
        "benchmark_fingerprint": (
            state["benchmark_fingerprint"] if same_fingerprint else None
        ),
        "same_fingerprint": same_fingerprint,
        "comparable": comparable,
        "desktop": {
            "classification": desktop.get("classification"),
            "score": d_score,
            "pass": (desktop.get("quality") or {}).get("pass"),
            "total_tokens": d_tokens,
            "duration_seconds": d_duration,
            "thread_count": (desktop.get("usage") or {}).get("thread_count"),
            "descendant_count": (desktop.get("usage") or {}).get("descendant_count"),
            "tool_calls": (desktop.get("usage") or {}).get("tool_calls"),
        },
        "room": {
            "classification": room.get("classification"),
            "score": r_score,
            "pass": (room.get("quality") or {}).get("pass"),
            "total_tokens": r_tokens,
            "duration_seconds": r_duration,
            "execution_count": (room.get("usage") or {}).get("execution_count"),
            "peer_invocations": (room.get("usage") or {}).get("peer_invocations"),
            "tool_calls": (room.get("usage") or {}).get("tool_calls"),
        },
        "room_minus_desktop_score": score_delta,
        "room_to_desktop_total_token_ratio": token_ratio,
        "room_to_desktop_duration_ratio": duration_ratio,
        "interpretation_note": (
            "OUB reports outcome quality, cost, duration, and orchestration separately. "
            "It does not compute or declare a platform winner."
        ),
    }


def _comparison_markdown(value: dict[str, Any]) -> str:
    desktop = value["desktop"]
    room = value["room"]
    lines = [
        f"# OUB v1 O1 comparison — {value['run_id']}",
        "",
        f"- Comparable: **{str(bool(value['comparable'])).lower()}**",
        f"- Same benchmark fingerprint: **{str(bool(value['same_fingerprint'])).lower()}**",
        "",
        "| Platform | Classification | Score | Total tokens | Duration (s) |",
        "|---|---:|---:|---:|---:|",
        f"| Desktop | {desktop.get('classification')} | {desktop.get('score')} | "
        f"{desktop.get('total_tokens')} | {desktop.get('duration_seconds')} |",
        f"| Room | {room.get('classification')} | {room.get('score')} | "
        f"{room.get('total_tokens')} | {room.get('duration_seconds')} |",
        "",
        f"- Room minus Desktop score: {value.get('room_minus_desktop_score')}",
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
        _write_json(root / "oub-v1-comparison.json", comparison)
        (root / "oub-v1-comparison.md").write_text(
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
        raise OUBV1Error(f"OUB v1 run not found: {run_id}")
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    destination = BUNDLE_ROOT / f"{run_id}-evidence.zip"
    temp = destination.with_suffix(".tmp")
    temp.unlink(missing_ok=True)
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
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
        raise OUBV1Error("No active OUB v1 run exists")

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
            "OUB does not own Desktop's native task lifecycle. If the measured Desktop "
            "task is still active, stop it in Codex Desktop."
        ),
        "bundle": bundle(run_id),
    }


def _json_out(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oub-v1")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("prepare")
    command.add_argument("--room-base", default=pbm_v4.DEFAULT_ROOM_BASE)

    command = sub.add_parser("desktop-worker")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("room-worker")
    command.add_argument("--run-id", required=True)

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
            value = prepare(args.room_base)
        elif args.command == "desktop-worker":
            value = desktop_worker(args.run_id)
        elif args.command == "room-worker":
            value = room_worker(args.run_id)
        elif args.command == "status":
            value = status(args.run_id)
        elif args.command == "abort":
            value = abort(args.run_id)
        elif args.command == "bundle":
            value = bundle(args.run_id)
        elif args.command == "audit":
            value = audit_harness()
        else:
            raise OUBV1Error("unsupported OUB v1 command")
    except (
        OUBV1Error,
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
