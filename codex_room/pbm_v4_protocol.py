"""PBM v4 common protocol runner with thin Desktop and Room adapters."""

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

from . import codex_usage, pbm, pbm_v4, pbm_v4_canary

VERSION = "v4"
TASK_ID = pbm_v4.TASK_ID
PASTE = pbm_v4.PASTE
ACTIVE_POINTER = pbm.PROJECT_ROOT / "output" / "pbm" / "v4-protocol-active.json"
DESKTOP_CONTROLLER_ROOT = pbm.PROJECT_ROOT / "pbm_desktop_controller"
DESKTOP_ACTIVE_ROOT = DESKTOP_CONTROLLER_ROOT / "active-v4"
DESKTOP_TASK_FILE = DESKTOP_ACTIVE_ROOT / "ACTIVE_TASK.md"
PROTOCOL_STATE_DIR = "v4-protocol"
PROTOCOL_BUNDLE_ROOT = pbm.PROJECT_ROOT / "output" / "pbm" / "protocol-bundles"
PROTOCOL_LOCK_DIR = pbm.PROJECT_ROOT / "output" / "pbm" / ".v4-protocol-state-lock"
ROOM_RUNNER_TITLE = "PBM v4 Room Runner"
TERMINAL_ROOM_STATUSES = {"finished", "stopped", "error", "archived"}


class PBMV4ProtocolError(pbm.PBMError):
    """Raised when the one-instruction PBM v4 protocol cannot be preserved."""


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _state_path(run_id: str) -> Path:
    return pbm.run_root(run_id) / PROTOCOL_STATE_DIR / "state.json"


def _load_state(run_id: str) -> dict[str, Any]:
    path = _state_path(run_id)
    if not path.is_file():
        raise PBMV4ProtocolError(f"PBM v4 protocol state not found: {run_id}")
    return _read_json(path)


def _save_state(run_id: str, state: dict[str, Any]) -> None:
    _write_json(_state_path(run_id), state)


@contextmanager
def _protocol_lock(timeout_seconds: float = 10.0) -> Iterator[None]:
    """Serialize short active-pair/state mutations across independent adapters."""

    PROTOCOL_LOCK_DIR.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout_seconds
    while True:
        try:
            PROTOCOL_LOCK_DIR.mkdir()
            break
        except FileExistsError:
            try:
                age = time.time() - PROTOCOL_LOCK_DIR.stat().st_mtime
            except OSError:
                age = 0.0
            if age > 60:
                try:
                    PROTOCOL_LOCK_DIR.rmdir()
                    continue
                except OSError:
                    pass
            if time.time() >= deadline:
                raise PBMV4ProtocolError("Timed out waiting for PBM v4 protocol state lock")
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            PROTOCOL_LOCK_DIR.rmdir()
        except OSError:
            pass


def _set_platform_state(
    run_id: str,
    platform: str,
    value: dict[str, Any],
) -> dict[str, Any]:
    with _protocol_lock():
        latest = _load_state(run_id)
        latest[platform] = value
        _save_state(run_id, latest)
        return latest


def _mark_platform_worker_started(
    run_id: str,
    platform: str,
    pid: int,
) -> dict[str, Any]:
    """Record a detached worker without overwriting a faster terminal update."""

    with _protocol_lock():
        latest = _load_state(run_id)
        current = latest.get(platform)
        if not isinstance(current, dict):
            raise PBMV4ProtocolError(f"{platform} protocol arm is not prepared")
        merged = {**current, "worker_pid": pid}
        if current.get("status") == "prepared":
            merged["status"] = "monitoring" if platform == "desktop" else "running"
        latest[platform] = merged
        _save_state(run_id, latest)
        return latest


def _result_path(state: dict[str, Any], platform: str) -> Path:
    root = pbm.run_root(str(state["run_id"]))
    if state["mode"] == "benchmark":
        return root / TASK_ID / platform / "result.json"
    return root / "canary" / platform / "result.json"


def _evidence_dir(state: dict[str, Any], platform: str) -> Path:
    return _result_path(state, platform).parent


def _new_run_id(mode: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"pbm-v4-{mode}-protocol-{stamp}"


def _validate_mode(mode: str) -> str:
    if mode not in {"benchmark", "canary"}:
        raise PBMV4ProtocolError("mode must be benchmark or canary")
    return mode


def _tree_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _require_protocol_repo(mode: str) -> dict[str, str]:
    repo = pbm_v4._require_clean_tree()
    if repo["branch"] != "main":
        raise PBMV4ProtocolError(
            f"PBM v4 protocol requires canonical main; found {repo['branch']}"
        )
    if mode == "benchmark" and pbm.current_version() != "v4":
        raise PBMV4ProtocolError(
            "Full PBM v4 benchmark execution is not promoted yet; CURRENT must be v4"
        )
    return repo


def _active_run() -> dict[str, Any] | None:
    if not ACTIVE_POINTER.is_file():
        return None
    try:
        pointer = _read_json(ACTIVE_POINTER)
    except (OSError, json.JSONDecodeError):
        return None
    run_id = pointer.get("run_id")
    if not isinstance(run_id, str) or not _state_path(run_id).is_file():
        return None
    return pointer


def _clear_active_if(run_id: str) -> None:
    if not ACTIVE_POINTER.is_file():
        return
    try:
        pointer = _read_json(ACTIVE_POINTER)
    except (OSError, json.JSONDecodeError):
        return
    if pointer.get("run_id") == run_id:
        ACTIVE_POINTER.unlink(missing_ok=True)


def _ensure_run(mode: str) -> dict[str, Any]:
    mode = _validate_mode(mode)
    repo = _require_protocol_repo(mode)
    audit = pbm_v4.audit_assets()
    fingerprint = str(audit["benchmark_fingerprint"])
    canary_fingerprint = (
        _tree_fingerprint(pbm_v4_canary.CANARY_ROOT)
        if mode == "canary"
        else None
    )

    created_run_id: str | None = None
    with _protocol_lock():
        pointer = _active_run()
        if pointer is not None:
            run_id = str(pointer["run_id"])
            state = _load_state(run_id)
            if state.get("complete") or state.get("aborted"):
                _clear_active_if(run_id)
            else:
                if state.get("mode") != mode:
                    raise PBMV4ProtocolError(
                        f"Active PBM v4 protocol run {run_id} is {state.get('mode')}; "
                        "finish or abort it before starting a different mode"
                    )
                if state.get("benchmark_fingerprint") != fingerprint:
                    raise PBMV4ProtocolError(
                        "PBM v4 fingerprint changed while a protocol run is active"
                    )
                if (state.get("repo") or {}).get("head") != repo["head"]:
                    raise PBMV4ProtocolError(
                        "Repository HEAD changed while a protocol run is active"
                    )
                if state.get("canary_fingerprint") != canary_fingerprint:
                    raise PBMV4ProtocolError(
                        "PBM v4 canary fixture changed while a protocol run is active"
                    )
                return state

        run_id = _new_run_id(mode)
        run = pbm.new_run(run_id=run_id, version=VERSION)
        state = {
            "schema": "pbm-v4-protocol-state-v1",
            "run_id": run_id,
            "mode": mode,
            "benchmark_version": VERSION,
            "benchmark_fingerprint": fingerprint,
            "canary_fingerprint": canary_fingerprint,
            "created_at": pbm.utc_now(),
            "repo": repo,
            "audit": audit,
            "desktop": None,
            "room": None,
            "complete": False,
            "aborted": False,
        }
        _save_state(run_id, state)
        _write_json(
            ACTIVE_POINTER,
            {
                "run_id": run_id,
                "mode": mode,
                "benchmark_fingerprint": fingerprint,
                "canary_fingerprint": canary_fingerprint,
                "repo_head": repo["head"],
            },
        )
        created_run_id = run_id

    if created_run_id is not None:
        pbm_v4._capture_context(created_run_id, "protocol-start")
    return _load_state(run_id)


def _copy_canary_fixture(workspace: Path) -> None:
    source = pbm_v4_canary.CANARY_ROOT
    workspace.mkdir(parents=True, exist_ok=True)
    for source_path in sorted(source.rglob("*")):
        rel = source_path.relative_to(source)
        destination = workspace / rel
        if source_path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        if destination.exists():
            raise PBMV4ProtocolError(
                f"Canary fixture would overwrite existing path: {destination}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)


def _canary_marker_ok(workspace: Path) -> bool:
    path = workspace / "CANARY_COMPLETE.json"
    if not path.is_file():
        return False
    try:
        return _read_json(path) == pbm_v4_canary.EXPECTED_MARKER
    except (OSError, json.JSONDecodeError):
        return False


def _marker_ok(mode: str, workspace: Path) -> bool:
    if mode == "benchmark":
        return pbm_v4._marker_ok(workspace)
    return _canary_marker_ok(workspace)


def _quality(mode: str, workspace: Path) -> dict[str, Any]:
    if mode == "benchmark":
        return pbm._run_grader(TASK_ID, workspace, VERSION)
    passed = _canary_marker_ok(workspace)
    return {
        "pass": passed,
        "score": 100 if passed else 0,
        "checks": [
            {
                "name": "canary_completion_marker",
                "pass": passed,
            }
        ],
    }


def _prepare_workspace(
    state: dict[str, Any],
    platform: str,
    workspace: Path,
) -> None:
    evidence = _evidence_dir(state, platform)
    if state["mode"] == "benchmark":
        pbm.prepare_task(
            run_id=str(state["run_id"]),
            task_id=TASK_ID,
            arm=platform,
            workspace=workspace,
            evidence_dir=evidence,
            allow_existing=platform == "room",
        )
        return

    _copy_canary_fixture(workspace)
    evidence.mkdir(parents=True, exist_ok=True)
    _write_json(
        evidence / "prepared.json",
        {
            "schema": "pbm-v4-protocol-canary-prepared-v1",
            "run_id": state["run_id"],
            "arm": platform,
            "mode": "canary",
            "benchmark_version": VERSION,
            "benchmark_fingerprint": state["benchmark_fingerprint"],
            "workspace": str(workspace.resolve()),
            "prepared_at": pbm.utc_now(),
            "prepared_at_ns": time.time_ns(),
        },
    )


def desktop_prepare(mode: str) -> dict[str, Any]:
    state = _ensure_run(mode)
    run_id = str(state["run_id"])
    existing = state.get("desktop")
    result_path = _result_path(state, "desktop")

    if result_path.is_file():
        result = _read_json(result_path)
        return {
            "action": "complete",
            "run_id": run_id,
            "mode": state["mode"],
            "classification": result.get("classification"),
        }

    if isinstance(existing, dict):
        status = str(existing.get("status") or "")
        if status == "prepared":
            return {
                "action": "run_task",
                "run_id": run_id,
                "mode": state["mode"],
                "workspace": existing["workspace"],
                "delegated_prompt": existing["delegated_prompt"],
            }
        if status == "monitoring":
            return {
                "action": "already_started",
                "run_id": run_id,
                "mode": state["mode"],
                "thread_id": existing.get("thread_id"),
                "worker_pid": existing.get("worker_pid"),
            }
        raise PBMV4ProtocolError(
            f"Desktop protocol arm already exists with status {status or 'unknown'}; "
            "do not create a replacement measured task"
        )

    if DESKTOP_ACTIVE_ROOT.exists():
        shutil.rmtree(DESKTOP_ACTIVE_ROOT)
    workspace = DESKTOP_ACTIVE_ROOT / "workspace"
    _prepare_workspace(state, "desktop", workspace)

    DESKTOP_ACTIVE_ROOT.mkdir(parents=True, exist_ok=True)
    task_text = (
        f"# PBM v4 {state['mode']} measured execution\n\n"
        "You are the fresh measured Codex Desktop execution. Work only in the assigned "
        "workspace below. Do not inspect the PBM harness, graders, reference solution, "
        "other platform result, or prior PBM results.\n\n"
        f"Assigned workspace: {workspace.resolve()}\n\n"
        "Change directory to that workspace before substantive work. Then execute exactly:\n\n"
        f"{PASTE}\n\n"
        "Do not ask the principal for guidance. When the mission is complete, stop.\n"
    )
    DESKTOP_TASK_FILE.write_text(task_text, encoding="utf-8")
    delegated_prompt = (
        "PBM v4 measured execution. Read active-v4/ACTIVE_TASK.md in the current "
        "workspace and execute it exactly. Do not inspect parent or sibling benchmark "
        "files. When complete, stop."
    )
    desktop_state = {
        "status": "prepared",
        "workspace": str(workspace.resolve()),
        "delegated_prompt": delegated_prompt,
        "delegated_prompt_sha256": hashlib.sha256(
            delegated_prompt.encode("utf-8")
        ).hexdigest(),
        "prepared_at": pbm.utc_now(),
    }
    _set_platform_state(run_id, "desktop", desktop_state)
    return {
        "action": "run_task",
        "run_id": run_id,
        "mode": state["mode"],
        "workspace": str(workspace.resolve()),
        "delegated_prompt": delegated_prompt,
    }


def _rollout_duration(report: dict[str, Any]) -> float | None:
    updates = report.get("token_updates") or []
    if not updates:
        return None
    start = pbm._parse_time((updates[0] or {}).get("timestamp"))
    end = pbm._parse_time((updates[-1] or {}).get("timestamp"))
    if start is None or end is None:
        return None
    return max(0.0, round((end - start).total_seconds(), 3))


def _normalized_usage(usage: dict[str, Any]) -> dict[str, Any]:
    total = usage.get("final_total_usage") or {}
    return {
        "input_tokens": total.get("input_tokens"),
        "cached_input_tokens": total.get("cached_input_tokens"),
        "output_tokens": total.get("output_tokens"),
        "reasoning_output_tokens": total.get("reasoning_output_tokens"),
        "total_tokens": total.get("total_tokens"),
        "provider_response_usage_records": usage["counts"][
            "provider_response_usage_records"
        ],
        "tool_calls": usage["counts"]["tool_calls"],
        "context_compactions": usage["counts"]["context_compactions"],
    }


def _spawn_desktop_worker(run_id: str) -> int:
    log_path = pbm.run_root(run_id) / PROTOCOL_STATE_DIR / "desktop-worker.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("ab")
    kwargs: dict[str, Any] = {
        "cwd": str(pbm.PROJECT_ROOT),
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
            "codex_room.pbm_v4_protocol",
            "desktop-worker",
            "--run-id",
            run_id,
        ],
        **kwargs,
    )
    log_handle.close()
    return int(process.pid)


def desktop_monitor_start(run_id: str, thread_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    desktop = state.get("desktop")
    if not isinstance(desktop, dict) or desktop.get("status") != "prepared":
        raise PBMV4ProtocolError("Desktop protocol arm is not prepared")

    monitoring = {
        **desktop,
        "status": "prepared",
        "thread_id": thread_id,
        "monitor_started_at": pbm.utc_now(),
        "worker_pid": None,
    }
    _set_platform_state(run_id, "desktop", monitoring)
    pid = _spawn_desktop_worker(run_id)
    state = _mark_platform_worker_started(run_id, "desktop", pid)
    return {
        "action": "monitoring",
        "run_id": run_id,
        "mode": state["mode"],
        "thread_id": thread_id,
        "worker_pid": pid,
        "note": (
            "Detached deterministic Desktop monitor started. The controller does not "
            "need to wait for the measured child or for Room."
        ),
    }


def _rollout_stable_for(
    path: Path,
    *,
    prior_signature: tuple[int, int] | None,
    stable_since: float | None,
) -> tuple[tuple[int, int], float | None]:
    stat = path.stat()
    signature = (stat.st_size, stat.st_mtime_ns)
    now = time.time()
    if signature != prior_signature:
        return signature, now
    return signature, stable_since


def desktop_worker(run_id: str, timeout_seconds: int = 3600) -> dict[str, Any]:
    state = _load_state(run_id)
    desktop = state.get("desktop")
    if not isinstance(desktop, dict):
        raise PBMV4ProtocolError("Desktop protocol arm is not prepared")
    thread_id = desktop.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id:
        raise PBMV4ProtocolError("Desktop measured child thread id is unavailable")
    workspace = Path(str(desktop["workspace"]))

    deadline = time.time() + timeout_seconds
    rollout: Path | None = None
    signature: tuple[int, int] | None = None
    stable_since: float | None = None

    try:
        while time.time() < deadline:
            latest = _load_state(run_id)
            if latest.get("aborted"):
                return {
                    "run_id": run_id,
                    "aborted": True,
                    "platform": "desktop",
                }

            try:
                rollout = codex_usage.select_rollout(
                    codex_home=codex_usage.default_codex_home(),
                    thread_id=thread_id,
                    include_archived=True,
                )
            except codex_usage.RolloutUsageError:
                rollout = None

            if rollout is not None and _marker_ok(str(state["mode"]), workspace):
                signature, stable_since = _rollout_stable_for(
                    rollout,
                    prior_signature=signature,
                    stable_since=stable_since,
                )
                if (
                    stable_since is not None
                    and time.time() - stable_since >= 3.0
                ):
                    return desktop_finish(run_id, thread_id)
            else:
                signature = None
                stable_since = None

            time.sleep(1)

        if rollout is not None:
            # Preserve a deterministic FAILED/INVALID result on timeout when
            # rollout evidence exists, rather than requiring principal capture.
            return desktop_finish(run_id, thread_id)
        raise PBMV4ProtocolError(
            f"Desktop measured child {thread_id} produced no rollout within "
            f"{timeout_seconds} seconds"
        )
    except Exception as exc:
        error = {
            "schema": "pbm-v4-protocol-desktop-worker-error-v1",
            "run_id": run_id,
            "recorded_at": pbm.utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        _write_json(
            pbm.run_root(run_id) / PROTOCOL_STATE_DIR / "desktop-worker-error.json",
            error,
        )
        latest = _load_state(run_id)
        current = latest.get("desktop")
        if isinstance(current, dict):
            _set_platform_state(
                run_id,
                "desktop",
                {
                    **current,
                    "status": "worker_error",
                    "worker_error": error,
                },
            )
        try:
            bundle(run_id)
        except Exception:
            pass
        raise


def desktop_finish(run_id: str, thread_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    if state.get("benchmark_fingerprint") != pbm.benchmark_fingerprint(VERSION):
        raise PBMV4ProtocolError("PBM v4 fingerprint changed after Desktop preparation")
    desktop = state.get("desktop")
    if (
        not isinstance(desktop, dict)
        or desktop.get("status") not in {"prepared", "monitoring"}
    ):
        raise PBMV4ProtocolError("Desktop protocol arm is not prepared or monitoring")

    rollout = codex_usage.select_rollout(
        codex_home=codex_usage.default_codex_home(),
        thread_id=thread_id,
        include_archived=True,
    )
    usage = codex_usage.analyze_rollout(rollout)
    messages = codex_usage.extract_user_messages(rollout)
    workspace = Path(str(desktop["workspace"]))
    expected_prompt = str(desktop["delegated_prompt"])

    invalid: list[str] = []
    failed: list[str] = []
    if len(messages) != 1:
        invalid.append(
            f"expected exactly one delegated Desktop task message; observed {len(messages)}"
        )
    elif messages[0].strip() != expected_prompt:
        invalid.append("Desktop delegated task message did not match the protocol prompt")

    cwd = usage["thread"].get("cwd")
    if isinstance(cwd, str):
        if os.path.normcase(os.path.abspath(cwd)) != os.path.normcase(
            os.path.abspath(DESKTOP_CONTROLLER_ROOT)
        ):
            invalid.append("Desktop child task did not originate from the PBM controller workspace")
    else:
        failed.append("Desktop rollout cwd was unavailable")

    normalized = _normalized_usage(usage)
    if normalized["total_tokens"] is None:
        failed.append("Desktop provider usage was unavailable")
    if not _marker_ok(str(state["mode"]), workspace):
        failed.append("Desktop completion marker is missing or invalid")

    quality = _quality(str(state["mode"]), workspace)
    result = {
        "schema": "pbm-v4-protocol-platform-result-v1",
        "run_id": run_id,
        "platform": "desktop",
        "mode": state["mode"],
        "benchmark_version": VERSION,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "canary_fingerprint": state.get("canary_fingerprint"),
        "completed_at": pbm.utc_now(),
        "classification": pbm_v4._classification(invalid, failed),
        "invalid_reasons": invalid,
        "failed_reasons": failed,
        "valid_for_comparison": not invalid and not failed,
        "quality": quality,
        "usage": normalized,
        "duration_seconds": _rollout_duration(usage),
        "provenance": {
            "thread_id": usage["thread"].get("id"),
            "rollout_path": usage["rollout_path"],
            "cwd": cwd,
            "controller_delegated": True,
            "observed_task_messages": messages,
        },
    }
    evidence = _evidence_dir(state, "desktop")
    evidence.mkdir(parents=True, exist_ok=True)
    _write_json(evidence / "usage.json", usage)
    _write_json(evidence / "grade.json", quality)
    _write_json(evidence / "result.json", result)

    final_workspace = evidence / "workspace-final"
    if final_workspace.exists():
        shutil.rmtree(final_workspace)
    shutil.copytree(workspace, final_workspace)
    if DESKTOP_ACTIVE_ROOT.exists():
        shutil.rmtree(DESKTOP_ACTIVE_ROOT)

    _set_platform_state(
        run_id,
        "desktop",
        {
            **desktop,
            "status": "complete",
            "thread_id": thread_id,
            "classification": result["classification"],
            "completed_at": result["completed_at"],
        },
    )
    pbm_v4._capture_context(run_id, "desktop-protocol-post")
    result["protocol_finalization"] = _finalize_if_ready(run_id)
    return result


def _room_payload(state: dict[str, Any]) -> dict[str, Any]:
    max_turns = 12
    inactivity = 900
    if state["mode"] == "benchmark":
        manifest = pbm.load_manifest(VERSION)
        max_turns = int(manifest["tasks"][0].get("room_max_turns") or 80)
        inactivity = 3600
    return {
        "title": f"PBM v4 {state['mode']} — {state['run_id']}",
        "topic": PASTE,
        "auto_start": False,
        "max_turns": max_turns,
        "max_consecutive_passes": 3,
        "inactivity_seconds": inactivity,
        "starting_agent": "agent_c",
        "completion_policy": "auto_settle",
        "required_contributors": [],
        "work_model_version": 2,
        "provider_context_mode": "assignment_thread",
    }


def _spawn_room_worker(run_id: str) -> int:
    log_path = pbm.run_root(run_id) / PROTOCOL_STATE_DIR / "room-worker.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("ab")
    kwargs: dict[str, Any] = {
        "cwd": str(pbm.PROJECT_ROOT),
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
            "codex_room.pbm_v4_protocol",
            "room-worker",
            "--run-id",
            run_id,
        ],
        **kwargs,
    )
    log_handle.close()
    return int(process.pid)


def room_start(mode: str, room_base: str = pbm_v4.DEFAULT_ROOM_BASE) -> dict[str, Any]:
    state = _ensure_run(mode)
    run_id = str(state["run_id"])
    result_path = _result_path(state, "room")
    existing = state.get("room")

    if result_path.is_file():
        result = _read_json(result_path)
        return {
            "action": "complete",
            "run_id": run_id,
            "mode": state["mode"],
            "classification": result.get("classification"),
        }

    if isinstance(existing, dict):
        status = str(existing.get("status") or "")
        if status in {"prepared", "running"}:
            return {
                "action": "already_started",
                "run_id": run_id,
                "mode": state["mode"],
                "room_id": existing.get("room_id"),
                "worker_pid": existing.get("worker_pid"),
            }
        raise PBMV4ProtocolError(
            f"Room protocol arm already exists with status {status or 'unknown'}; "
            "do not create a replacement measured Room"
        )

    health = pbm_v4._http_json("GET", f"{room_base}/api/health")
    if not isinstance(health, dict) or health.get("ok") is not True:
        raise PBMV4ProtocolError("Codex Room health endpoint did not report ok=true")

    room = pbm_v4._http_json("POST", f"{room_base}/api/rooms", _room_payload(state))
    if not isinstance(room, dict) or not room.get("id") or not room.get("active_round_id"):
        raise PBMV4ProtocolError("Measured Room creation returned incomplete identifiers")
    room_id = str(room["id"])
    round_id = str(room["active_round_id"])
    workspace = pbm.PROJECT_ROOT / "data" / "rooms" / room_id / "shared"
    _prepare_workspace(state, "room", workspace)

    room_state = {
        "status": "prepared",
        "room_base": room_base,
        "room_id": room_id,
        "round_id": round_id,
        "workspace": str(workspace.resolve()),
        "prepared_at": pbm.utc_now(),
        "worker_pid": None,
    }
    _set_platform_state(run_id, "room", room_state)

    pid = _spawn_room_worker(run_id)
    state = _mark_platform_worker_started(run_id, "room", pid)
    return {
        "action": "started",
        "run_id": run_id,
        "mode": state["mode"],
        "room_id": room_id,
        "round_id": round_id,
        "worker_pid": pid,
    }


def _room_round(export: dict[str, Any], round_id: str) -> dict[str, Any]:
    matches = [
        item for item in (export.get("rounds") or [])
        if str(item.get("id")) == round_id
    ]
    if len(matches) != 1:
        raise PBMV4ProtocolError(
            f"Room export expected round {round_id}; observed {len(matches)} matches"
        )
    return matches[0]


def _empty_aggregate(round_item: dict[str, Any]) -> dict[str, Any]:
    return {
        "round_status": round_item.get("status"),
        "close_reason": round_item.get("close_reason"),
        "execution_count": 0,
        "executions_by_agent": {},
        "usage_complete": False,
        "total": {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
            "total_tokens": 0,
        },
        "tool_calls": 0,
        "failed_tool_calls": 0,
        "peer_invocations": 0,
        "duration_seconds": None,
    }


def _capture_room(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    room_info = state.get("room")
    if not isinstance(room_info, dict):
        raise PBMV4ProtocolError("Room protocol arm is not prepared")
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
    round_item = _room_round(export, round_id)

    invalid = pbm_v4.room_intervention_reasons(round_item)
    if pbm_v4._round_prompt(round_item) != PASTE:
        invalid.append("Measured Room prompt did not match the frozen PBM v4 mission prompt")
    invalid = sorted(set(invalid))

    try:
        aggregate = pbm.aggregate_room_export(export, round_id)
    except pbm.PBMError:
        aggregate = _empty_aggregate(round_item)

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
    if not _marker_ok(str(state["mode"]), workspace):
        failed.append("Room completion marker is missing or invalid")

    quality = _quality(str(state["mode"]), workspace)
    executions = pbm._room_execution_provenance(
        pbm.PROJECT_ROOT / "data" / "codex-room.db",
        room_id,
        round_id,
    )
    result = {
        "schema": "pbm-v4-protocol-platform-result-v1",
        "run_id": run_id,
        "platform": "room",
        "mode": state["mode"],
        "benchmark_version": VERSION,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "canary_fingerprint": state.get("canary_fingerprint"),
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
        },
    }
    evidence = _evidence_dir(state, "room")
    evidence.mkdir(parents=True, exist_ok=True)
    _write_json(evidence / "room-export.json", export)
    _write_json(evidence / "grade.json", quality)
    _write_json(evidence / "result.json", result)

    _set_platform_state(
        run_id,
        "room",
        {
            **room_info,
            "status": "complete",
            "classification": result["classification"],
            "completed_at": result["completed_at"],
        },
    )
    pbm_v4._capture_context(run_id, "room-protocol-post")
    result["protocol_finalization"] = _finalize_if_ready(run_id)
    return result


def room_worker(run_id: str, timeout_seconds: int = 3600) -> dict[str, Any]:
    state = _load_state(run_id)
    room_info = state.get("room")
    if not isinstance(room_info, dict):
        raise PBMV4ProtocolError("Room protocol arm is not prepared")
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
            room = pbm_v4._http_json("GET", f"{base}/api/rooms/{room_id}")
            status = str(room.get("status") or "")
            if status in TERMINAL_ROOM_STATUSES:
                break

            export = pbm_v4._http_json(
                "GET",
                f"{base}/api/rooms/{room_id}/export?format=json",
                timeout=30,
            )
            round_item = _room_round(export, round_id)
            if pbm_v4.room_intervention_reasons(round_item):
                pbm_v4._http_json(
                    "POST",
                    f"{base}/api/rooms/{room_id}/stop",
                    {},
                )
                break
            time.sleep(1)
        else:
            pbm_v4._http_json("POST", f"{base}/api/rooms/{room_id}/stop", {})
            raise PBMV4ProtocolError(
                f"Measured Room {room_id} exceeded {timeout_seconds} seconds"
            )

        return _capture_room(run_id)
    except Exception as exc:
        error = {
            "schema": "pbm-v4-protocol-room-worker-error-v1",
            "run_id": run_id,
            "recorded_at": pbm.utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        _write_json(
            pbm.run_root(run_id) / PROTOCOL_STATE_DIR / "room-worker-error.json",
            error,
        )
        state = _load_state(run_id)
        if isinstance(state.get("room"), dict):
            _set_platform_state(
                run_id,
                "room",
                {
                    **state["room"],
                    "status": "worker_error",
                    "worker_error": error,
                },
            )
        try:
            bundle(run_id)
        except Exception:
            pass
        raise


def _comparison(state: dict[str, Any]) -> dict[str, Any]:
    desktop = _read_json(_result_path(state, "desktop"))
    room = _read_json(_result_path(state, "room"))
    same_fingerprint = (
        desktop.get("benchmark_fingerprint") == room.get("benchmark_fingerprint")
    )
    comparable = (
        desktop.get("classification") == "VALID"
        and room.get("classification") == "VALID"
        and same_fingerprint
    )
    d_tokens = (desktop.get("usage") or {}).get("total_tokens")
    r_tokens = (room.get("usage") or {}).get("total_tokens")
    ratio = (
        round(float(r_tokens) / float(d_tokens), 4)
        if isinstance(d_tokens, (int, float))
        and d_tokens > 0
        and isinstance(r_tokens, (int, float))
        else None
    )
    return {
        "schema": "pbm-v4-protocol-comparison-v1",
        "run_id": state["run_id"],
        "mode": state["mode"],
        "benchmark_version": VERSION,
        "benchmark_fingerprint": (
            desktop.get("benchmark_fingerprint") if same_fingerprint else None
        ),
        "comparable": comparable,
        "same_fingerprint": same_fingerprint,
        "desktop": {
            "classification": desktop.get("classification"),
            "score": (desktop.get("quality") or {}).get("score"),
            "pass": (desktop.get("quality") or {}).get("pass"),
            "total_tokens": d_tokens,
            "duration_seconds": desktop.get("duration_seconds"),
        },
        "room": {
            "classification": room.get("classification"),
            "score": (room.get("quality") or {}).get("score"),
            "pass": (room.get("quality") or {}).get("pass"),
            "total_tokens": r_tokens,
            "duration_seconds": room.get("duration_seconds"),
            "peer_invocations": (room.get("usage") or {}).get("peer_invocations"),
        },
        "room_to_desktop_total_token_ratio": ratio,
    }


def bundle(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    root = pbm.run_root(run_id)
    PROTOCOL_BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    path = PROTOCOL_BUNDLE_ROOT / f"{run_id}-evidence.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(root.rglob("*")):
            if item.is_file():
                archive.write(item, Path("run") / item.relative_to(root))

        room_info = state.get("room")
        if isinstance(room_info, dict) and room_info.get("room_id"):
            try:
                export = pbm_v4._http_json(
                    "GET",
                    f"{room_info['room_base']}/api/rooms/{room_info['room_id']}/export?format=json",
                    timeout=60,
                )
                archive.writestr(
                    "live/room-export.json",
                    json.dumps(export, indent=2, sort_keys=True) + "\n",
                )
            except pbm.PBMError as exc:
                archive.writestr("live/room-export-error.txt", str(exc) + "\n")

        desktop_path = _result_path(state, "desktop")
        if desktop_path.is_file():
            result = _read_json(desktop_path)
            rollout = Path(
                str((result.get("provenance") or {}).get("rollout_path") or "")
            )
            if rollout.is_file():
                archive.write(rollout, "live/desktop-rollout.jsonl")

        archive.writestr(
            "README.txt",
            (
                "PBM v4 common-protocol evidence\n"
                f"run_id: {run_id}\n"
                f"mode: {state['mode']}\n"
                f"benchmark_fingerprint: {state['benchmark_fingerprint']}\n"
                f"canary_fingerprint: {state.get('canary_fingerprint')}\n"
            ),
        )
    return {
        "run_id": run_id,
        "bundle_path": str(path.resolve()),
        "size_bytes": path.stat().st_size,
    }


def _finalize_if_ready(run_id: str) -> dict[str, Any]:
    with _protocol_lock():
        state = _load_state(run_id)
        if state.get("complete"):
            comparison = state.get("comparison")
            return {
                "run_id": run_id,
                "complete": True,
                "comparison": comparison,
                "bundle": bundle(run_id),
            }

        ready = all(
            _result_path(state, arm).is_file()
            for arm in ("desktop", "room")
        )
        if not ready:
            claimed = False
        elif state.get("finalizing"):
            return {
                "run_id": run_id,
                "complete": False,
                "finalizing": True,
            }
        else:
            state["finalizing"] = True
            _save_state(run_id, state)
            claimed = True

    if not claimed:
        return {
            "run_id": run_id,
            "complete": False,
            "bundle": bundle(run_id),
        }

    try:
        state = _load_state(run_id)
        comparison = _comparison(state)
        root = pbm.run_root(run_id)
        _write_json(root / "pbm-v4-protocol-comparison.json", comparison)
        pbm_v4._capture_context(run_id, "protocol-complete")
        with _protocol_lock():
            state = _load_state(run_id)
            state["complete"] = True
            state["finalizing"] = False
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
        with _protocol_lock():
            state = _load_state(run_id)
            state["finalizing"] = False
            state["finalization_error"] = {
                "recorded_at": pbm.utc_now(),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            _save_state(run_id, state)
        raise


def status(run_id: str | None = None) -> dict[str, Any]:
    if run_id is None:
        pointer = _active_run()
        if pointer is None:
            return {"active": False}
        run_id = str(pointer["run_id"])
    state = _load_state(run_id)
    value = {
        "active": not state.get("complete") and not state.get("aborted"),
        "run_id": run_id,
        "mode": state["mode"],
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "canary_fingerprint": state.get("canary_fingerprint"),
        "desktop": state.get("desktop"),
        "room": state.get("room"),
        "complete": state.get("complete"),
        "aborted": state.get("aborted"),
    }
    return value


def _stop_owned_worker(pid: Any) -> str:
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
        pointer = _active_run()
        if pointer is None:
            raise PBMV4ProtocolError("No active PBM v4 protocol run exists")
        run_id = str(pointer["run_id"])
    state = _load_state(run_id)

    desktop_worker_action = "not_started"
    desktop_info = state.get("desktop")
    if isinstance(desktop_info, dict):
        desktop_worker_action = _stop_owned_worker(desktop_info.get("worker_pid"))

    room_action = "not_started"
    room_info = state.get("room")
    if isinstance(room_info, dict) and room_info.get("room_id"):
        try:
            room = pbm_v4._http_json(
                "GET",
                f"{room_info['room_base']}/api/rooms/{room_info['room_id']}",
            )
            if str(room.get("status")) not in TERMINAL_ROOM_STATUSES:
                pbm_v4._http_json(
                    "POST",
                    f"{room_info['room_base']}/api/rooms/{room_info['room_id']}/stop",
                    {},
                )
                room_action = "stopped"
            else:
                room_action = f"already_{room.get('status')}"
        except pbm.PBMError as exc:
            room_action = f"error: {exc}"

    with _protocol_lock():
        state = _load_state(run_id)
        state["aborted"] = True
        state["aborted_at"] = pbm.utc_now()
        state["abort_room_action"] = room_action
        _save_state(run_id, state)
        _clear_active_if(run_id)
    if DESKTOP_ACTIVE_ROOT.exists():
        shutil.rmtree(DESKTOP_ACTIVE_ROOT)
    evidence_bundle = bundle(run_id)
    return {
        "run_id": run_id,
        "aborted": True,
        "room_action": room_action,
        "desktop_worker_action": desktop_worker_action,
        "desktop_note": (
            "The owned deterministic Desktop monitor is stopped when possible. "
            "If the native measured Desktop child itself is still active, stop that "
            "native task through Codex Desktop."
        ),
        "bundle": evidence_bundle,
    }


def _room_client_text() -> str:
    repo = str(pbm.PROJECT_ROOT.resolve()).replace("'", "''")
    return f"""[CmdletBinding()]
param(
    [switch]$Canary
)

$ErrorActionPreference = 'Stop'
$RepoRoot = '{repo}'
$Wrapper = Join-Path $RepoRoot 'pbm-v4-protocol.ps1'

if (-not (Test-Path -LiteralPath $Wrapper)) {{
    throw "PBM v4 protocol wrapper not found: $Wrapper"
}}

$mode = if ($Canary) {{ 'canary' }} else {{ 'benchmark' }}

Push-Location $RepoRoot
try {{
    & $Wrapper room-start --mode $mode
    $protocolExit = $LASTEXITCODE
}}
finally {{
    Pop-Location
}}

if ($protocolExit -ne 0) {{
    throw "PBM v4 Room protocol failed with exit code $protocolExit"
}}
"""


def install_room_runner(
    room_base: str = pbm_v4.DEFAULT_ROOM_BASE,
) -> dict[str, Any]:
    health = pbm_v4._http_json("GET", f"{room_base}/api/health")
    if not isinstance(health, dict) or health.get("ok") is not True:
        raise PBMV4ProtocolError("Codex Room health endpoint did not report ok=true")

    rooms = pbm_v4._http_json("GET", f"{room_base}/api/rooms")
    existing = None
    if isinstance(rooms, list):
        existing = next(
            (
                item
                for item in rooms
                if isinstance(item, dict) and item.get("title") == ROOM_RUNNER_TITLE
            ),
            None,
        )

    if existing is None:
        existing = pbm_v4._http_json(
            "POST",
            f"{room_base}/api/rooms",
            {
                "title": ROOM_RUNNER_TITLE,
                "topic": (
                    "Persistent PBM v4 protocol runner. Do not start benchmark work "
                    "from this staging topic. The principal will initiate a controller "
                    "Round by pointing Agent C to PBM_ROOM_PROTOCOL.md."
                ),
                "auto_start": False,
                "max_turns": 8,
                "max_consecutive_passes": 2,
                "inactivity_seconds": 900,
                "starting_agent": "agent_c",
                "completion_policy": "auto_settle",
                "required_contributors": [],
                "work_model_version": 2,
                "provider_context_mode": "assignment_thread",
            },
        )

    room_id = str(existing["id"])
    workspace = pbm.PROJECT_ROOT / "data" / "rooms" / room_id / "shared"
    workspace.mkdir(parents=True, exist_ok=True)
    version_root = pbm.version_root(VERSION)
    shutil.copy2(
        version_root / "PROTOCOL.md",
        workspace / "PBM_COMMON_PROTOCOL.md",
    )
    shutil.copy2(
        version_root / "ROOM_PROTOCOL.md",
        workspace / "PBM_ROOM_PROTOCOL.md",
    )
    (workspace / "PBM_ROOM_CLIENT.ps1").write_text(
        _room_client_text(),
        encoding="utf-8",
    )
    return {
        "room_id": room_id,
        "title": ROOM_RUNNER_TITLE,
        "workspace": str(workspace.resolve()),
        "instruction": "Read PBM_ROOM_PROTOCOL.md and execute it exactly.",
        "canary_instruction": (
            "Read PBM_ROOM_PROTOCOL.md and execute it exactly in canary mode."
        ),
    }


def _json_out(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbm-v4-protocol")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("desktop-prepare")
    command.add_argument("--mode", choices=["benchmark", "canary"], default="benchmark")

    command = sub.add_parser("desktop-monitor-start")
    command.add_argument("--run-id", required=True)
    command.add_argument("--thread-id", required=True)

    command = sub.add_parser("desktop-worker")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("desktop-finish")
    command.add_argument("--run-id", required=True)
    command.add_argument("--thread-id", required=True)

    command = sub.add_parser("room-start")
    command.add_argument("--mode", choices=["benchmark", "canary"], default="benchmark")
    command.add_argument("--room-base", default=pbm_v4.DEFAULT_ROOM_BASE)

    command = sub.add_parser("room-worker")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("status")
    command.add_argument("--run-id")

    command = sub.add_parser("abort")
    command.add_argument("--run-id")

    command = sub.add_parser("bundle")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("install-room-runner")
    command.add_argument("--room-base", default=pbm_v4.DEFAULT_ROOM_BASE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "desktop-prepare":
            value = desktop_prepare(args.mode)
        elif args.command == "desktop-monitor-start":
            value = desktop_monitor_start(args.run_id, args.thread_id)
        elif args.command == "desktop-worker":
            value = desktop_worker(args.run_id)
        elif args.command == "desktop-finish":
            value = desktop_finish(args.run_id, args.thread_id)
        elif args.command == "room-start":
            value = room_start(args.mode, args.room_base)
        elif args.command == "room-worker":
            value = room_worker(args.run_id)
        elif args.command == "status":
            value = status(args.run_id)
        elif args.command == "abort":
            value = abort(args.run_id)
        elif args.command == "bundle":
            value = bundle(args.run_id)
        elif args.command == "install-room-runner":
            value = install_room_runner(args.room_base)
        else:
            raise PBMV4ProtocolError("unsupported PBM v4 protocol command")
    except (
        PBMV4ProtocolError,
        pbm.PBMError,
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
