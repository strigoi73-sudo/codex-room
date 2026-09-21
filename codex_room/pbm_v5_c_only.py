"""Controlled PBM v5 variant: compare the existing Desktop baseline with C-only Room."""

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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import pbm, pbm_context, pbm_v4, pbm_v5

VERSION = "v5"
TASK_ID = pbm_v4.TASK_ID
PASTE = pbm_v4.PASTE
BASELINE_RUN_ID = "pbm-v5-benchmark-20260921T130735334526Z"
EXPECTED_BENCHMARK_FINGERPRINT = (
    "492f8ce7d2cc49094abe993db7a20cad2a355ef277a90efd41fe26697b0cbc1b"
)
ACTIVE_POINTER = pbm.PROJECT_ROOT / "output" / "pbm" / "v5-c-only-active.json"
STATE_DIR = "v5-c-only"
BUNDLE_ROOT = pbm.PROJECT_ROOT / "output" / "pbm" / "v5-c-only-bundles"
TERMINAL_ROOM_STATUSES = {"finished", "stopped", "error", "archived"}

C_ONLY_PERSONALITY = """CONTROLLED PBM C-ONLY CONDITION

For this measured benchmark only, complete the benchmark using Agent C alone.

You must not delegate benchmark work to Agent A or Agent B. Do not invoke Agent A or Agent B, request their cognition, assign them work, or use results from them. A and B must remain idle throughout the measured Round.

You may use your own Agent C cognition, ordinary native tools, deterministic Room capabilities, evidence requests, context refresh, and Agent-C-only continuation mechanics as needed. Choose your own sequencing, verification, model, and reasoning effort within the ordinary Room rules.

If you cannot complete the benchmark without Agent A or Agent B, do not delegate to them. Settle without claiming successful completion instead.
"""


class PBMV5COnlyError(pbm.PBMError):
    """Raised when the controlled C-only benchmark cannot preserve its contract."""


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
        raise PBMV5COnlyError(f"C-only PBM state not found: {run_id}")
    return _read_json(path)


def _save_state(run_id: str, state: dict[str, Any]) -> None:
    _write_json(_state_path(run_id), state)


def _new_run_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"pbm-v5-c-only-{stamp}"


def _active_run() -> str | None:
    if not ACTIVE_POINTER.is_file():
        return None
    try:
        value = _read_json(ACTIVE_POINTER)
    except (OSError, json.JSONDecodeError):
        return None
    run_id = value.get("run_id")
    if isinstance(run_id, str) and _state_path(run_id).is_file():
        state = _load_state(run_id)
        if not state.get("complete") and not state.get("aborted"):
            return run_id
    return None


def _clear_active_if(run_id: str) -> None:
    if not ACTIVE_POINTER.is_file():
        return
    try:
        value = _read_json(ACTIVE_POINTER)
    except (OSError, json.JSONDecodeError):
        return
    if value.get("run_id") == run_id:
        ACTIVE_POINTER.unlink(missing_ok=True)


def _variant_fingerprint() -> str:
    source = Path(__file__).resolve().read_bytes()
    payload = (
        EXPECTED_BENCHMARK_FINGERPRINT.encode("ascii")
        + b"\0"
        + BASELINE_RUN_ID.encode("utf-8")
        + b"\0"
        + C_ONLY_PERSONALITY.encode("utf-8")
        + b"\0"
        + source
    )
    return hashlib.sha256(payload).hexdigest()


def _baseline_result_path() -> Path:
    return pbm.run_root(BASELINE_RUN_ID) / TASK_ID / "desktop" / "result.json"


def _baseline_result() -> dict[str, Any]:
    path = _baseline_result_path()
    if not path.is_file():
        raise PBMV5COnlyError(
            "The verified Desktop baseline result is missing: "
            f"{path}"
        )
    result = _read_json(path)
    problems = []
    if result.get("classification") != "VALID":
        problems.append("Desktop baseline classification is not VALID")
    if result.get("benchmark_fingerprint") != EXPECTED_BENCHMARK_FINGERPRINT:
        problems.append("Desktop baseline benchmark fingerprint does not match")
    quality = result.get("quality") or {}
    if quality.get("pass") is not True or quality.get("score") != 100:
        problems.append("Desktop baseline is not PASS / 100")
    if problems:
        raise PBMV5COnlyError("; ".join(problems))
    return result


def _require_environment() -> dict[str, str]:
    repo = pbm_v4._require_clean_tree()
    if repo["branch"] != "main":
        raise PBMV5COnlyError(f"C-only PBM requires canonical main; found {repo['branch']}")
    if pbm.current_version() != VERSION:
        raise PBMV5COnlyError(f"PBM CURRENT must be {VERSION}")
    fingerprint = pbm.benchmark_fingerprint(VERSION)
    if fingerprint != EXPECTED_BENCHMARK_FINGERPRINT:
        raise PBMV5COnlyError(
            "Canonical PBM v5 fingerprint changed; refusing to compare against "
            f"the existing Desktop baseline. Expected {EXPECTED_BENCHMARK_FINGERPRINT}, "
            f"found {fingerprint}."
        )
    _baseline_result()
    return repo


def _room_payload(run_id: str) -> dict[str, Any]:
    return {
        "title": f"PBM v5 C-only — {run_id}",
        "topic": PASTE,
        "agent_c_instructions": C_ONLY_PERSONALITY,
        "auto_start": False,
        "max_turns": 120,
        "max_consecutive_passes": 3,
        "inactivity_seconds": 3600,
        "starting_agent": "agent_c",
        "completion_policy": "auto_settle",
        "required_contributors": [],
        "work_model_version": 2,
        "provider_context_mode": "assignment_thread",
    }


def _c_only_violations(round_item: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for event in round_item.get("events") or []:
        source = str(event.get("source") or "")
        event_type = str(event.get("event_type") or "")
        metadata = event.get("metadata") or {}

        if event_type == "execution_economics" and source in {"agent_a", "agent_b"}:
            reasons.append(f"{source} executed during the C-only condition")

        if metadata.get("transaction_action") == "DELEGATE":
            for delegation in metadata.get("delegations") or []:
                target = delegation.get("target") if isinstance(delegation, dict) else None
                if target in {"agent_a", "agent_b"}:
                    reasons.append(f"Agent C delegated to {target} during the C-only condition")

    return sorted(set(reasons))


def _spawn_worker(run_id: str) -> int:
    log_path = pbm.run_root(run_id) / STATE_DIR / "worker.log"
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
            "codex_room.pbm_v5_c_only",
            "worker",
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
        raise PBMV5COnlyError(f"C-only PBM run already active: {active}")

    repo = _require_environment()
    baseline = _baseline_result()
    health = pbm_v4._http_json("GET", f"{room_base}/api/health")
    if not isinstance(health, dict) or health.get("ok") is not True:
        raise PBMV5COnlyError("Codex Room health endpoint did not report ok=true")

    run_id = _new_run_id()
    run = pbm.new_run(run_id=run_id, version=VERSION)
    run_path = pbm.run_root(run_id) / "run.json"
    run_meta = _read_json(run_path)
    run_meta.update(
        {
            "mode": "controlled-c-only",
            "baseline_run_id": BASELINE_RUN_ID,
            "variant_fingerprint": _variant_fingerprint(),
        }
    )
    _write_json(run_path, run_meta)
    pbm_v4._capture_context(run_id, "protocol-start")

    room = pbm_v4._http_json("POST", f"{room_base}/api/rooms", _room_payload(run_id))
    if not isinstance(room, dict) or not room.get("id") or not room.get("active_round_id"):
        raise PBMV5COnlyError("C-only Room creation returned incomplete identifiers")

    room_id = str(room["id"])
    round_id = str(room["active_round_id"])
    workspace = pbm.PROJECT_ROOT / "data" / "rooms" / room_id / "shared"
    evidence = pbm.run_root(run_id) / TASK_ID / "room"
    pbm.prepare_task(
        run_id=run_id,
        task_id=TASK_ID,
        arm="room",
        workspace=workspace,
        evidence_dir=evidence,
        allow_existing=True,
    )
    pbm_v4.populate_battery_workspace(workspace, allow_existing=True)
    shutil.copy2(_baseline_result_path(), pbm.run_root(run_id) / "baseline-desktop-result.json")

    prepared_at = pbm.utc_now()
    state = {
        "schema": "pbm-v5-c-only-state-v1",
        "run_id": run_id,
        "benchmark_version": VERSION,
        "benchmark_fingerprint": run["benchmark_fingerprint"],
        "variant_fingerprint": _variant_fingerprint(),
        "baseline_run_id": BASELINE_RUN_ID,
        "repo": repo,
        "prepared_at": prepared_at,
        "room": {
            "status": "prepared",
            "room_base": room_base,
            "room_id": room_id,
            "round_id": round_id,
            "workspace": str(workspace.resolve()),
            "instruction": PASTE,
            "c_only_personality": C_ONLY_PERSONALITY,
            "worker_pid": None,
        },
        "baseline_desktop": {
            "classification": baseline.get("classification"),
            "score": (baseline.get("quality") or {}).get("score"),
            "total_tokens": (baseline.get("usage") or {}).get("total_tokens"),
            "duration_seconds": baseline.get("duration_seconds"),
            "root_thread_id": (baseline.get("provenance") or {}).get("root_thread_id"),
        },
        "complete": False,
        "aborted": False,
        "comparison": None,
        "error": None,
    }
    _save_state(run_id, state)
    _write_json(
        ACTIVE_POINTER,
        {
            "run_id": run_id,
            "benchmark_fingerprint": state["benchmark_fingerprint"],
            "variant_fingerprint": state["variant_fingerprint"],
        },
    )

    pid = _spawn_worker(run_id)
    state = _load_state(run_id)
    state["room"]["worker_pid"] = pid
    if state["room"]["status"] == "prepared":
        state["room"]["status"] = "running"
    _save_state(run_id, state)

    return {
        "action": "running",
        "run_id": run_id,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "variant_fingerprint": state["variant_fingerprint"],
        "baseline_run_id": BASELINE_RUN_ID,
        "baseline_desktop": state["baseline_desktop"],
        "room_id": room_id,
        "round_id": round_id,
        "workspace": str(workspace.resolve()),
        "instruction": PASTE,
        "condition": "Agent C only; A/B delegation or execution invalidates and stops the run.",
    }


def _finish(run_id: str) -> dict[str, Any]:
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
    invalid.extend(_c_only_violations(round_item))
    if pbm_v4._round_prompt(round_item) != PASTE:
        invalid.append("Measured Room prompt did not match the frozen PBM mission")

    try:
        aggregate = pbm.aggregate_room_export(export, round_id)
    except pbm.PBMError:
        aggregate = pbm_v5._empty_room_aggregate(round_item)

    non_c = {
        key: value
        for key, value in aggregate["executions_by_agent"].items()
        if key != "agent_c" and int(value or 0) > 0
    }
    if non_c:
        invalid.append(f"Non-C measured executions observed: {non_c}")

    failed = []
    if (
        str(round_item.get("status") or "") != "finished"
        or round_item.get("close_reason") != "transaction_settled"
    ):
        failed.append(
            "C-only Room did not settle cleanly: "
            f"status={round_item.get('status') or 'unknown'} "
            f"close_reason={round_item.get('close_reason') or 'unknown'}"
        )
    if not aggregate["usage_complete"]:
        failed.append("C-only Room execution usage is incomplete")
    if not pbm_v4._marker_ok(workspace):
        failed.append("C-only Room completion marker is missing or invalid")

    quality = pbm_v4.grade_battery(workspace)
    executions = pbm._room_execution_provenance(
        pbm.PROJECT_ROOT / "data" / "codex-room.db",
        room_id,
        round_id,
    )
    invalid = sorted(set(invalid))
    failed = sorted(set(failed))
    classification = pbm_v4._classification(invalid, failed)

    result = {
        "schema": "pbm-v5-c-only-result-v1",
        "run_id": run_id,
        "condition": "c-only",
        "benchmark_version": VERSION,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "variant_fingerprint": state["variant_fingerprint"],
        "completed_at": pbm.utc_now(),
        "classification": classification,
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

    evidence = pbm.run_root(run_id) / TASK_ID / "room"
    _write_json(evidence / "room-export.json", export)
    _write_json(evidence / "grade.json", quality)
    _write_json(evidence / "result.json", result)

    baseline = _baseline_result()
    d_tokens = (baseline.get("usage") or {}).get("total_tokens")
    c_tokens = (result.get("usage") or {}).get("total_tokens")
    d_duration = baseline.get("duration_seconds")
    c_duration = result.get("duration_seconds")

    comparable = (
        baseline.get("classification") == "VALID"
        and classification == "VALID"
        and baseline.get("benchmark_fingerprint") == result.get("benchmark_fingerprint")
    )
    comparison = {
        "schema": "pbm-v5-c-only-comparison-v1",
        "run_id": run_id,
        "baseline_run_id": BASELINE_RUN_ID,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "variant_fingerprint": state["variant_fingerprint"],
        "comparable": comparable,
        "desktop": {
            "classification": baseline.get("classification"),
            "score": (baseline.get("quality") or {}).get("score"),
            "total_tokens": d_tokens,
            "duration_seconds": d_duration,
            "thread_count": (baseline.get("usage") or {}).get("thread_count"),
            "descendant_count": (baseline.get("usage") or {}).get("descendant_count"),
        },
        "c_only_room": {
            "classification": classification,
            "score": (quality or {}).get("score"),
            "total_tokens": c_tokens,
            "duration_seconds": c_duration,
            "execution_count": aggregate["execution_count"],
            "executions_by_agent": aggregate["executions_by_agent"],
            "peer_invocations": aggregate["peer_invocations"],
        },
        "c_to_desktop_total_token_ratio": (
            round(float(c_tokens) / float(d_tokens), 4)
            if isinstance(c_tokens, (int, float))
            and isinstance(d_tokens, (int, float))
            and d_tokens > 0
            else None
        ),
        "c_to_desktop_duration_ratio": (
            round(float(c_duration) / float(d_duration), 4)
            if isinstance(c_duration, (int, float))
            and isinstance(d_duration, (int, float))
            and d_duration > 0
            else None
        ),
    }
    comparison["provider_usage_meter"] = pbm_context.protocol_usage_meter_summary(
        pbm.run_root(run_id)
    )
    _write_json(pbm.run_root(run_id) / "pbm-v5-c-only-comparison.json", comparison)

    state = _load_state(run_id)
    state["room"] = {
        **state["room"],
        "status": "complete",
        "classification": classification,
        "completed_at": result["completed_at"],
    }
    state["complete"] = True
    state["completed_at"] = pbm.utc_now()
    state["comparison"] = comparison
    _save_state(run_id, state)
    pbm_v4._capture_context(run_id, "protocol-complete")
    # Refresh the comparison's meter after the final capture.
    comparison["provider_usage_meter"] = pbm_context.protocol_usage_meter_summary(
        pbm.run_root(run_id)
    )
    _write_json(pbm.run_root(run_id) / "pbm-v5-c-only-comparison.json", comparison)
    state = _load_state(run_id)
    state["comparison"] = comparison
    _save_state(run_id, state)
    _clear_active_if(run_id)
    bundle_info = bundle(run_id)
    return {
        "run_id": run_id,
        "complete": True,
        "result": result,
        "comparison": comparison,
        "bundle": bundle_info,
    }


def worker(run_id: str, timeout_seconds: int = 7200) -> dict[str, Any]:
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
            current = _load_state(run_id)
            if current.get("aborted"):
                return {"run_id": run_id, "aborted": True}

            room = pbm_v4._http_json("GET", f"{base}/api/rooms/{room_id}")
            export = pbm_v4._http_json(
                "GET",
                f"{base}/api/rooms/{room_id}/export?format=json",
                timeout=30,
            )
            round_item = pbm_v5._room_round(export, round_id)
            violations = _c_only_violations(round_item)
            if violations or pbm_v4.room_intervention_reasons(round_item):
                if str(room.get("status") or "") not in TERMINAL_ROOM_STATUSES:
                    pbm_v4._http_json("POST", f"{base}/api/rooms/{room_id}/stop", {})
                break
            if str(room.get("status") or "") in TERMINAL_ROOM_STATUSES:
                break
            time.sleep(1)
        else:
            pbm_v4._http_json("POST", f"{base}/api/rooms/{room_id}/stop", {})
            raise PBMV5COnlyError(
                f"C-only Room {room_id} exceeded {timeout_seconds} seconds"
            )
        return _finish(run_id)
    except Exception as exc:
        state = _load_state(run_id)
        state["error"] = {
            "recorded_at": pbm.utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        state["room"] = {**state["room"], "status": "worker_error"}
        _save_state(run_id, state)
        try:
            bundle(run_id)
        except Exception:
            pass
        raise


def bundle(run_id: str) -> dict[str, Any]:
    root = pbm.run_root(run_id)
    if not root.is_dir():
        raise PBMV5COnlyError(f"C-only PBM run not found: {run_id}")
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
    return {
        "active": not state.get("complete") and not state.get("aborted"),
        **state,
    }


def abort(run_id: str | None = None) -> dict[str, Any]:
    if run_id is None:
        run_id = _active_run()
    if run_id is None:
        raise PBMV5COnlyError("No active C-only PBM run exists")

    state = _load_state(run_id)
    pid = (state.get("room") or {}).get("worker_pid")
    worker_action = "not_running"
    if isinstance(pid, int) and pid > 0:
        try:
            os.kill(pid, signal.SIGTERM)
            worker_action = "stop_requested"
        except ProcessLookupError:
            worker_action = "already_exited"
        except OSError as exc:
            worker_action = f"error: {type(exc).__name__}"

    room_action = "not_started"
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
                room_action = "stopped"
            else:
                room_action = f"already_{room.get('status')}"
        except pbm.PBMError as exc:
            room_action = f"error: {exc}"

    state = _load_state(run_id)
    state["aborted"] = True
    state["aborted_at"] = pbm.utc_now()
    _save_state(run_id, state)
    _clear_active_if(run_id)
    return {
        "run_id": run_id,
        "aborted": True,
        "worker_action": worker_action,
        "room_action": room_action,
        "bundle": bundle(run_id),
    }


def audit() -> dict[str, Any]:
    _require_environment()
    baseline = _baseline_result()
    return {
        "ok": True,
        "benchmark_version": VERSION,
        "benchmark_fingerprint": pbm.benchmark_fingerprint(VERSION),
        "variant_fingerprint": _variant_fingerprint(),
        "baseline_run_id": BASELINE_RUN_ID,
        "baseline_desktop": {
            "classification": baseline.get("classification"),
            "score": (baseline.get("quality") or {}).get("score"),
            "total_tokens": (baseline.get("usage") or {}).get("total_tokens"),
            "duration_seconds": baseline.get("duration_seconds"),
        },
        "condition": "C only; Agent A/B delegation or execution is invalid.",
    }


def _json_out(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbm-v5-c-only")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("prepare")
    command.add_argument("--room-base", default=pbm_v4.DEFAULT_ROOM_BASE)

    command = sub.add_parser("worker")
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
        elif args.command == "worker":
            value = worker(args.run_id)
        elif args.command == "status":
            value = status(args.run_id)
        elif args.command == "abort":
            value = abort(args.run_id)
        elif args.command == "bundle":
            value = bundle(args.run_id)
        elif args.command == "audit":
            value = audit()
        else:
            raise PBMV5COnlyError("unsupported C-only PBM command")
    except (
        PBMV5COnlyError,
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
