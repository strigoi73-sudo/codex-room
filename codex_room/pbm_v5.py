"""PBM v5: platform-outcome Desktop versus Room benchmark."""

from __future__ import annotations

import argparse
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

from . import codex_usage, pbm, pbm_context, pbm_v4

VERSION = "v5"
TASK_ID = pbm_v4.TASK_ID
PASTE = pbm_v4.PASTE
ACTIVE_POINTER = pbm.PROJECT_ROOT / "output" / "pbm" / "v5-active.json"
STATE_DIR = "v5"
BUNDLE_ROOT = pbm.PROJECT_ROOT / "output" / "pbm" / "v5-bundles"
LOCK_DIR = pbm.PROJECT_ROOT / "output" / "pbm" / ".v5-state-lock"
TERMINAL_ROOM_STATUSES = {"finished", "stopped", "error", "archived"}
USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


class PBMV5Error(pbm.PBMError):
    """Raised when PBM v5 cannot preserve its platform-comparison contract."""


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _state_path(run_id: str) -> Path:
    return pbm.run_root(run_id) / STATE_DIR / "state.json"


def _load_state(run_id: str) -> dict[str, Any]:
    path = _state_path(run_id)
    if not path.is_file():
        raise PBMV5Error(f"PBM v5 state not found: {run_id}")
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
                raise PBMV5Error("Timed out waiting for PBM v5 state lock")
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
    return f"pbm-v5-benchmark-{stamp}"


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
    return pbm.run_root(str(state["run_id"])) / TASK_ID / arm / "result.json"


def _evidence_dir(state: dict[str, Any], arm: str) -> Path:
    return _result_path(state, arm).parent


def _require_repo() -> dict[str, str]:
    repo = pbm_v4._require_clean_tree()
    if repo["branch"] != "main":
        raise PBMV5Error(f"PBM v5 requires canonical main; found {repo['branch']}")
    if pbm.current_version() != VERSION:
        raise PBMV5Error(f"PBM CURRENT must be {VERSION}")
    return repo


def audit_assets() -> dict[str, Any]:
    manifest = pbm.load_manifest(VERSION)
    if manifest.get("asset_version") != "v4":
        raise PBMV5Error("PBM v5 must reuse the frozen PBM v4 battery assets")
    if tuple(manifest.get("battery_tasks") or []) != pbm_v4.BATTERY_TASK_IDS:
        raise PBMV5Error("PBM v5 battery tasks must match the frozen v4 battery")
    protocol = manifest.get("v5_protocol") or {}
    if protocol.get("comparison_unit") != "platform":
        raise PBMV5Error("PBM v5 comparison unit must be platform")
    if protocol.get("platform_internal_orchestration") != "unconstrained":
        raise PBMV5Error("PBM v5 must not prescribe platform-internal orchestration")
    if protocol.get("desktop_measurement_scope") != "root-thread-and-descendants":
        raise PBMV5Error("PBM v5 Desktop scope must include native descendants")
    if protocol.get("room_measurement_scope") != "measured-round-all-agents":
        raise PBMV5Error("PBM v5 Room scope must include all measured agents")

    v4_audit = pbm_v4.audit_assets()
    return {
        "ok": True,
        "benchmark_version": VERSION,
        "benchmark_fingerprint": pbm.benchmark_fingerprint(VERSION),
        "task_count": len(pbm_v4.BATTERY_TASK_IDS),
        "tasks": list(v4_audit["tasks"]),
        "reference_score": v4_audit["reference_score"],
        "reference_scores": v4_audit["reference_scores"],
    }


def _desktop_workspace(run_id: str) -> Path:
    return pbm.run_root(run_id) / STATE_DIR / "desktop-workspace"


def _prepare_workspace(
    run_id: str,
    arm: str,
    workspace: Path,
) -> None:
    pbm.prepare_task(
        run_id=run_id,
        task_id=TASK_ID,
        arm=arm,
        workspace=workspace,
        evidence_dir=pbm.run_root(run_id) / TASK_ID / arm,
        allow_existing=arm == "room",
    )
    pbm_v4.populate_battery_workspace(workspace, allow_existing=True)


def _room_payload(run_id: str) -> dict[str, Any]:
    return {
        "title": f"PBM v5 — {run_id}",
        "topic": PASTE,
        "auto_start": False,
        "max_turns": 80,
        "max_consecutive_passes": 3,
        "inactivity_seconds": 3600,
        "starting_agent": "agent_c",
        "completion_policy": "auto_settle",
        "required_contributors": [],
        "work_model_version": 2,
        "provider_context_mode": "assignment_thread",
    }


def _spawn_worker(kind: str, run_id: str) -> int:
    if kind not in {"desktop", "room"}:
        raise PBMV5Error(f"Unsupported PBM v5 worker: {kind}")
    log_path = pbm.run_root(run_id) / STATE_DIR / f"{kind}-worker.log"
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
            "codex_room.pbm_v5",
            f"{kind}-worker",
            "--run-id",
            run_id,
        ],
        **kwargs,
    )
    log_handle.close()
    return int(process.pid)


def prepare(room_base: str = pbm_v4.DEFAULT_ROOM_BASE) -> dict[str, Any]:
    active = _active_run()
    if active is not None:
        raise PBMV5Error(f"PBM v5 run already active: {active}")

    repo = _require_repo()
    audit = audit_assets()
    run_id = _new_run_id()
    run = pbm.new_run(run_id=run_id, version=VERSION)
    pbm_v4._capture_context(run_id, "protocol-start")

    desktop_workspace = _desktop_workspace(run_id)
    _prepare_workspace(run_id, "desktop", desktop_workspace)

    health = pbm_v4._http_json("GET", f"{room_base}/api/health")
    if not isinstance(health, dict) or health.get("ok") is not True:
        raise PBMV5Error("Codex Room health endpoint did not report ok=true")
    room = pbm_v4._http_json("POST", f"{room_base}/api/rooms", _room_payload(run_id))
    if not isinstance(room, dict) or not room.get("id") or not room.get("active_round_id"):
        raise PBMV5Error("Measured Room creation returned incomplete identifiers")

    room_id = str(room["id"])
    round_id = str(room["active_round_id"])
    room_workspace = pbm.PROJECT_ROOT / "data" / "rooms" / room_id / "shared"
    _prepare_workspace(run_id, "room", room_workspace)

    prepared_at = pbm.utc_now()
    state = {
        "schema": "pbm-v5-state-v1",
        "run_id": run_id,
        "benchmark_version": VERSION,
        "benchmark_fingerprint": run["benchmark_fingerprint"],
        "created_at": run["created_at"],
        "prepared_at": prepared_at,
        "repo": repo,
        "audit": audit,
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
            "benchmark_fingerprint": run["benchmark_fingerprint"],
            "repo_head": repo["head"],
        },
    )

    desktop_pid = _spawn_worker("desktop", run_id)
    room_pid = _spawn_worker("room", run_id)
    with _state_lock():
        state = _load_state(run_id)
        state["desktop"]["worker_pid"] = desktop_pid
        state["desktop"]["status"] = "monitoring"
        state["room"]["worker_pid"] = room_pid
        state["room"]["status"] = "running"
        _save_state(run_id, state)

    return {
        "action": "ready",
        "run_id": run_id,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "desktop_workspace": str(desktop_workspace.resolve()),
        "desktop_instruction": PASTE,
        "desktop_note": (
            "Open one fresh top-level native Codex Desktop task rooted at desktop_workspace "
            "and send desktop_instruction exactly once. Desktop may organize its own work "
            "and use any native descendants it chooses."
        ),
        "room_id": room_id,
        "room_title": room.get("title"),
        "room_round_id": round_id,
        "room_note": (
            "The measured Room has been prepared and is being started automatically. "
            "Normal A/B/C coordination is unrestricted by PBM."
        ),
    }


def _norm(value: str | Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(value)))


def _desktop_candidates(desktop: dict[str, Any]) -> list[tuple[Path, str]]:
    workspace = _norm(str(desktop["workspace"]))
    prepared_at = pbm._parse_time(desktop.get("prepared_at"))
    latest_by_thread: dict[str, Path] = {}

    for path in codex_usage._rollout_paths(  # type: ignore[attr-defined]
        codex_usage.default_codex_home(),
        include_archived=True,
    ):
        meta = codex_usage._session_meta(path)  # type: ignore[attr-defined]
        thread_id = codex_usage._thread_id(meta)  # type: ignore[attr-defined]
        if not isinstance(thread_id, str) or not thread_id:
            continue
        if codex_usage._parent_thread_id(meta) is not None:  # type: ignore[attr-defined]
            continue
        cwd = meta.get("cwd")
        if not isinstance(cwd, str) or _norm(cwd) != workspace:
            continue
        created = pbm._parse_time(meta.get("timestamp"))
        if prepared_at is not None and created is not None and created < prepared_at:
            continue
        if prepared_at is not None and created is None:
            continue
        current = latest_by_thread.get(thread_id)
        if current is None or path.stat().st_mtime_ns > current.stat().st_mtime_ns:
            latest_by_thread[thread_id] = path

    return sorted(
        [(path, thread_id) for thread_id, path in latest_by_thread.items()],
        key=lambda item: item[0].stat().st_mtime_ns,
    )


def _lineage_paths(root_thread_id: str) -> list[tuple[Path, dict[str, Any]]]:
    latest: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in codex_usage._rollout_paths(  # type: ignore[attr-defined]
        codex_usage.default_codex_home(),
        include_archived=True,
    ):
        meta = codex_usage._session_meta(path)  # type: ignore[attr-defined]
        thread_id = codex_usage._thread_id(meta)  # type: ignore[attr-defined]
        if not isinstance(thread_id, str) or not thread_id:
            continue
        prior = latest.get(thread_id)
        if prior is None or path.stat().st_mtime_ns > prior[0].stat().st_mtime_ns:
            latest[thread_id] = (path, meta)

    included = {root_thread_id}
    changed = True
    while changed:
        changed = False
        for thread_id, (_, meta) in latest.items():
            parent = codex_usage._parent_thread_id(meta)  # type: ignore[attr-defined]
            if parent in included and thread_id not in included:
                included.add(thread_id)
                changed = True

    if root_thread_id not in latest:
        raise PBMV5Error(f"Desktop root rollout not found: {root_thread_id}")
    return [latest[thread_id] for thread_id in sorted(included) if thread_id in latest]


def _lineage_signature(root_thread_id: str) -> tuple[tuple[str, int, int], ...]:
    items = []
    for path, _ in _lineage_paths(root_thread_id):
        stat = path.stat()
        items.append((str(path.resolve()), stat.st_size, stat.st_mtime_ns))
    return tuple(sorted(items))


def _lineage_usage(root_thread_id: str) -> dict[str, Any]:
    reports = [
        codex_usage.analyze_rollout(path)
        for path, _ in _lineage_paths(root_thread_id)
    ]
    totals = {field: 0 for field in USAGE_FIELDS}
    usage_complete = True
    tool_calls = 0
    context_compactions = 0
    starts = []
    ends = []

    for report in reports:
        total = report.get("final_total_usage")
        if not isinstance(total, dict):
            usage_complete = False
        else:
            for field in USAGE_FIELDS:
                value = total.get(field)
                if not isinstance(value, int):
                    usage_complete = False
                else:
                    totals[field] += value
        counts = report.get("counts") or {}
        tool_calls += int(counts.get("tool_calls") or 0)
        context_compactions += int(counts.get("context_compactions") or 0)
        updates = report.get("token_updates") or []
        if updates:
            first = pbm._parse_time((updates[0] or {}).get("timestamp"))
            last = pbm._parse_time((updates[-1] or {}).get("timestamp"))
            if first is not None:
                starts.append(first)
            if last is not None:
                ends.append(last)

    duration = None
    if starts and ends:
        duration = max(0.0, round((max(ends) - min(starts)).total_seconds(), 3))

    lineage = []
    for report in reports:
        thread = report.get("thread") or {}
        lineage.append(
            {
                "thread_id": thread.get("id"),
                "parent_thread_id": thread.get("parent_thread_id"),
                "cwd": thread.get("cwd"),
                "rollout_path": report.get("rollout_path"),
                "total_tokens": (report.get("final_total_usage") or {}).get("total_tokens"),
            }
        )

    return {
        **totals,
        "usage_complete": usage_complete,
        "tool_calls": tool_calls,
        "context_compactions": context_compactions,
        "thread_count": len(reports),
        "descendant_count": max(0, len(reports) - 1),
        "duration_seconds": duration,
        "lineage": lineage,
    }


def _bind_desktop_root(run_id: str, thread_id: str, rollout: Path) -> None:
    with _state_lock():
        state = _load_state(run_id)
        desktop = state["desktop"]
        existing = desktop.get("root_thread_id")
        if existing not in {None, thread_id}:
            raise PBMV5Error(
                f"Desktop root binding changed from {existing} to {thread_id}"
            )
        desktop["root_thread_id"] = thread_id
        desktop["root_rollout_path"] = str(rollout.resolve())
        desktop["root_bound_at"] = pbm.utc_now()
        desktop["status"] = "running"
        state["desktop"] = desktop
        _save_state(run_id, state)


def _task_quality(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for item in ((result.get("quality") or {}).get("checks") or []):
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, str) and name in pbm_v4.BATTERY_TASK_IDS:
            summary[name] = {
                "pass": bool(item.get("ok")),
                "score": item.get("score"),
            }
    return summary


def desktop_finish(run_id: str, root_thread_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    if state["benchmark_fingerprint"] != pbm.benchmark_fingerprint(VERSION):
        raise PBMV5Error("PBM v5 fingerprint changed after preparation")
    desktop = state["desktop"]
    workspace = Path(str(desktop["workspace"]))
    root_rollout = codex_usage.select_rollout(
        codex_home=codex_usage.default_codex_home(),
        thread_id=root_thread_id,
        include_archived=True,
    )
    root_usage = codex_usage.analyze_rollout(root_rollout)
    messages = codex_usage.extract_user_messages(root_rollout)
    lineage_usage = _lineage_usage(root_thread_id)

    invalid = []
    if len(messages) != 1:
        invalid.append(
            f"expected exactly one Desktop principal message; observed {len(messages)}"
        )
    elif messages[0].strip() != PASTE:
        invalid.append("Desktop principal message did not match the frozen PBM mission")

    cwd = (root_usage.get("thread") or {}).get("cwd")
    if not isinstance(cwd, str) or _norm(cwd) != _norm(workspace):
        invalid.append("Desktop root task was not rooted at the prepared PBM workspace")

    failed = []
    if not lineage_usage["usage_complete"]:
        failed.append("Desktop lineage provider usage is incomplete")
    if not pbm_v4._marker_ok(workspace):
        failed.append("Desktop completion marker is missing or invalid")

    quality = pbm_v4.grade_battery(workspace)
    result = {
        "schema": "pbm-v5-platform-result-v1",
        "run_id": run_id,
        "platform": "desktop",
        "benchmark_version": VERSION,
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
    pbm_v4._capture_context(run_id, "desktop-post")
    _finalize_if_ready(run_id)
    return result


def desktop_worker(run_id: str, timeout_seconds: int = 7200) -> dict[str, Any]:
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
                candidates = _desktop_candidates(desktop)
                if len(candidates) > 1:
                    ids = ", ".join(thread_id for _, thread_id in candidates)
                    raise PBMV5Error(
                        "multiple top-level Desktop tasks were started in the prepared "
                        f"workspace: {ids}"
                    )
                if len(candidates) == 1:
                    rollout, root_thread_id = candidates[0]
                    _bind_desktop_root(run_id, root_thread_id, rollout)

            if root_thread_id:
                workspace = Path(str(desktop["workspace"]))
                if pbm_v4._marker_ok(workspace):
                    signature = _lineage_signature(root_thread_id)
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
            return desktop_finish(run_id, root_thread_id)
        raise PBMV5Error("No measured Desktop root task appeared before timeout")
    except Exception as exc:
        _record_worker_error(run_id, "desktop", exc)
        raise


def _room_round(export: dict[str, Any], round_id: str) -> dict[str, Any]:
    matches = [
        item for item in (export.get("rounds") or [])
        if str(item.get("id")) == round_id
    ]
    if len(matches) != 1:
        raise PBMV5Error(
            f"Room export expected round {round_id}; observed {len(matches)} matches"
        )
    return matches[0]


def _empty_room_aggregate(round_item: dict[str, Any]) -> dict[str, Any]:
    return {
        "round_status": round_item.get("status"),
        "close_reason": round_item.get("close_reason"),
        "execution_count": 0,
        "executions_by_agent": {},
        "usage_complete": False,
        "total": {field: 0 for field in USAGE_FIELDS},
        "tool_calls": 0,
        "failed_tool_calls": 0,
        "peer_invocations": 0,
        "duration_seconds": None,
    }


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
    round_item = _room_round(export, round_id)
    invalid = pbm_v4.room_intervention_reasons(round_item)
    if pbm_v4._round_prompt(round_item) != PASTE:
        invalid.append("Measured Room prompt did not match the frozen PBM mission")
    invalid = sorted(set(invalid))

    try:
        aggregate = pbm.aggregate_room_export(export, round_id)
    except pbm.PBMError:
        aggregate = _empty_room_aggregate(round_item)

    failed = []
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
    if not pbm_v4._marker_ok(workspace):
        failed.append("Room completion marker is missing or invalid")

    quality = pbm_v4.grade_battery(workspace)
    executions = pbm._room_execution_provenance(
        pbm.PROJECT_ROOT / "data" / "codex-room.db",
        room_id,
        round_id,
    )
    result = {
        "schema": "pbm-v5-platform-result-v1",
        "run_id": run_id,
        "platform": "room",
        "benchmark_version": VERSION,
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
        },
    }
    evidence = _evidence_dir(state, "room")
    evidence.mkdir(parents=True, exist_ok=True)
    _write_json(evidence / "room-export.json", export)
    _write_json(evidence / "grade.json", quality)
    _write_json(evidence / "result.json", result)
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
    pbm_v4._capture_context(run_id, "room-post")
    _finalize_if_ready(run_id)
    return result


def room_worker(run_id: str, timeout_seconds: int = 7200) -> dict[str, Any]:
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
            round_item = _room_round(export, round_id)
            if pbm_v4.room_intervention_reasons(round_item):
                pbm_v4._http_json("POST", f"{base}/api/rooms/{room_id}/stop", {})
                break
            time.sleep(1)
        else:
            pbm_v4._http_json("POST", f"{base}/api/rooms/{room_id}/stop", {})
            raise PBMV5Error(f"Measured Room {room_id} exceeded {timeout_seconds} seconds")
        return room_finish(run_id)
    except Exception as exc:
        _record_worker_error(run_id, "room", exc)
        raise


def _record_worker_error(run_id: str, arm: str, exc: Exception) -> None:
    error = {
        "schema": "pbm-v5-worker-error-v1",
        "run_id": run_id,
        "platform": arm,
        "recorded_at": pbm.utc_now(),
        "error_type": type(exc).__name__,
        "error": str(exc),
    }
    _write_json(pbm.run_root(run_id) / STATE_DIR / f"{arm}-worker-error.json", error)
    try:
        state = _load_state(run_id)
        info = state.get(arm)
        if isinstance(info, dict):
            _set_arm(run_id, arm, {**info, "status": "worker_error", "worker_error": error})
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
        "schema": "pbm-v5-comparison-v1",
        "run_id": state["run_id"],
        "benchmark_version": VERSION,
        "benchmark_fingerprint": state["benchmark_fingerprint"] if same_fingerprint else None,
        "same_fingerprint": same_fingerprint,
        "comparable": comparable,
        "desktop": {
            "classification": desktop.get("classification"),
            "score": (desktop.get("quality") or {}).get("score"),
            "pass": (desktop.get("quality") or {}).get("pass"),
            "task_quality": _task_quality(desktop),
            "total_tokens": d_tokens,
            "duration_seconds": desktop.get("duration_seconds"),
            "thread_count": (desktop.get("usage") or {}).get("thread_count"),
            "descendant_count": (desktop.get("usage") or {}).get("descendant_count"),
        },
        "room": {
            "classification": room.get("classification"),
            "score": (room.get("quality") or {}).get("score"),
            "pass": (room.get("quality") or {}).get("pass"),
            "task_quality": _task_quality(room),
            "total_tokens": r_tokens,
            "duration_seconds": room.get("duration_seconds"),
            "execution_count": (room.get("usage") or {}).get("execution_count"),
            "peer_invocations": (room.get("usage") or {}).get("peer_invocations"),
        },
        "room_to_desktop_total_token_ratio": ratio,
    }


def _comparison_markdown(value: dict[str, Any]) -> str:
    desktop = value["desktop"]
    room = value["room"]
    meter = value.get("provider_usage_meter") or {}
    delta = meter.get("delta") or {}
    lines = [
        f"# PBM v5 comparison — {value['run_id']}",
        "",
        f"- Comparable: **{str(bool(value['comparable'])).lower()}**",
        f"- Same benchmark fingerprint: **{str(bool(value['same_fingerprint'])).lower()}**",
        "",
        "| Platform | Classification | Score | Total tokens | Duration (s) |",
        "|---|---:|---:|---:|---:|",
        f"| Desktop | {desktop.get('classification')} | {desktop.get('score')} | {desktop.get('total_tokens')} | {desktop.get('duration_seconds')} |",
        f"| Room | {room.get('classification')} | {room.get('score')} | {room.get('total_tokens')} | {room.get('duration_seconds')} |",
        "",
        f"- Room/Desktop token ratio: {value.get('room_to_desktop_total_token_ratio')}",
        f"- Desktop measured threads: {desktop.get('thread_count')} "
        f"(descendants: {desktop.get('descendant_count')})",
        f"- Room measured executions: {room.get('execution_count')} "
        f"(peer invocations: {room.get('peer_invocations')})",
        "",
        "## Provider usage meter",
        "",
        f"- Lifetime-token delta: {delta.get('lifetime_tokens_delta')}",
    ]
    return "\n".join(lines) + "\n"


def _finalize_if_ready(run_id: str) -> dict[str, Any] | None:
    with _state_lock():
        state = _load_state(run_id)
        if state.get("complete"):
            return {"run_id": run_id, "complete": True, "comparison": state.get("comparison")}
        if state.get("aborted") or state.get("finalizing"):
            return None
        if not all(_result_path(state, arm).is_file() for arm in ("desktop", "room")):
            return None
        state["finalizing"] = True
        _save_state(run_id, state)

    try:
        pbm_v4._capture_context(run_id, "protocol-complete")
        state = _load_state(run_id)
        comparison = _comparison(state)
        comparison["provider_usage_meter"] = pbm_context.protocol_usage_meter_summary(
            pbm.run_root(run_id)
        )
        root = pbm.run_root(run_id)
        _write_json(root / "pbm-v5-comparison.json", comparison)
        (root / "pbm-v5-comparison.md").write_text(
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
    root = pbm.run_root(run_id)
    if not root.is_dir():
        raise PBMV5Error(f"PBM v5 run not found: {run_id}")
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
        raise PBMV5Error("No active PBM v5 run exists")
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
            "PBM does not own Desktop's native task lifecycle. If the measured Desktop "
            "task is still active, stop it in Codex Desktop."
        ),
        "bundle": bundle(run_id),
    }


def _json_out(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbm-v5")
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
            value = audit_assets()
        else:
            raise PBMV5Error("unsupported PBM v5 command")
    except (
        PBMV5Error,
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
