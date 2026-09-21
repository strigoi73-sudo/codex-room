"""Bounded live protocol canary for PBM v4 one-paste execution."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import codex_usage, pbm, pbm_context, pbm_v4

CANARY_ROOT = pbm.PROJECT_ROOT / "benchmarks" / "pbm-canary" / "v4"
OUTPUT_ROOT = pbm.PROJECT_ROOT / "output" / "pbm" / "canaries"
BUNDLE_ROOT = pbm.PROJECT_ROOT / "output" / "pbm" / "canary-bundles"
PASTE = pbm_v4.PASTE
EXPECTED_MARKER = {"status": "complete", "protocol": "one-paste"}


class CanaryError(pbm.PBMError):
    """Raised when the PBM v4 live canary cannot preserve its protocol."""


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _new_run_id() -> str:
    return "pbm-v4-canary-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _root(run_id: str) -> Path:
    if not pbm.RUN_ID_RE.fullmatch(run_id):
        raise CanaryError("invalid canary run id")
    return OUTPUT_ROOT / run_id


def _state_path(run_id: str) -> Path:
    return _root(run_id) / "state.json"


def _load_state(run_id: str) -> dict[str, Any]:
    path = _state_path(run_id)
    if not path.is_file():
        raise CanaryError(f"PBM v4 canary state not found: {run_id}")
    return _read_json(path)


def _copy_canary(destination: Path) -> None:
    if not CANARY_ROOT.is_dir():
        raise CanaryError(f"canary asset directory is missing: {CANARY_ROOT}")
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted(CANARY_ROOT.rglob("*")):
        rel = source.relative_to(CANARY_ROOT)
        target = destination / rel
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            if target.exists():
                raise CanaryError(f"canary asset would overwrite existing path: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def _capture_context(run_id: str, label: str) -> None:
    asyncio.run(
        pbm_context.capture_snapshot(
            run_root=_root(run_id),
            label=label,
            project_root=pbm.PROJECT_ROOT,
            captured_at=pbm.utc_now(),
            if_missing=True,
        )
    )


def _marker_ok(workspace: Path) -> bool:
    marker = workspace / "CANARY_COMPLETE.json"
    if not marker.is_file():
        return False
    try:
        value = _read_json(marker)
    except (OSError, json.JSONDecodeError):
        return False
    return value == EXPECTED_MARKER


def _create_room(base: str, run_id: str) -> dict[str, Any]:
    health = pbm_v4._http_json("GET", f"{base}/api/health")
    if not isinstance(health, dict) or health.get("ok") is not True:
        raise CanaryError("Codex Room health endpoint did not report ok=true")
    payload = {
        "title": f"PBM v4 CANARY — {run_id} — READY",
        "topic": (
            "PBM v4 bounded canary staging placeholder. Do not start this initial Round. "
            "The principal will create exactly one measured canary Round."
        ),
        "auto_start": False,
        "max_turns": 12,
        "max_consecutive_passes": 3,
        "inactivity_seconds": 900,
        "starting_agent": "agent_c",
        "completion_policy": "auto_settle",
        "required_contributors": [],
        "work_model_version": 2,
        "provider_context_mode": "assignment_thread",
    }
    room = pbm_v4._http_json("POST", f"{base}/api/rooms", payload)
    if not isinstance(room, dict) or not room.get("id") or not room.get("active_round_id"):
        raise CanaryError("canary Room creation returned incomplete identifiers")
    return room


def prepare_pair(room_base: str = pbm_v4.DEFAULT_ROOM_BASE) -> dict[str, Any]:
    repo_state = pbm_v4._require_clean_tree()
    fingerprint = pbm.benchmark_fingerprint(pbm_v4.VERSION)
    run_id = _new_run_id()
    root = _root(run_id)
    if root.exists():
        raise CanaryError(f"canary run already exists: {run_id}")
    root.mkdir(parents=True)

    created_at = pbm.utc_now()
    _write_json(
        root / "run.json",
        {
            "schema": "pbm-v4-canary-run-v1",
            "run_id": run_id,
            "benchmark_version": pbm_v4.VERSION,
            "benchmark_fingerprint": fingerprint,
            "created_at": created_at,
        },
    )

    prepared_at_ns = time.time_ns()
    desktop_workspace = root / "desktop-workspace"
    _copy_canary(desktop_workspace)

    room = _create_room(room_base, run_id)
    room_id = str(room["id"])
    room_workspace = pbm.PROJECT_ROOT / "data" / "rooms" / room_id / "shared"
    _copy_canary(room_workspace)

    state = {
        "schema": "pbm-v4-canary-state-v1",
        "run_id": run_id,
        "created_at": created_at,
        "prepared_at_ns": prepared_at_ns,
        "benchmark_version": pbm_v4.VERSION,
        "benchmark_fingerprint": fingerprint,
        "repo": repo_state,
        "room_base": room_base,
        "room_id": room_id,
        "room_title": room.get("title"),
        "staging_round_id": str(room["active_round_id"]),
        "desktop_workspace": str(desktop_workspace.resolve()),
        "room_workspace": str(room_workspace.resolve()),
        "benchmark_paste": PASTE,
        "benchmark_paste_sha256": hashlib.sha256(PASTE.encode("utf-8")).hexdigest(),
    }
    _write_json(_state_path(run_id), state)
    _capture_context(run_id, "canary-prep")
    return {
        **state,
        "desktop_steps": [
            "Open a fresh top-level native Codex Desktop task rooted exactly at desktop_workspace.",
            "Paste benchmark_paste exactly once. Do not send a second benchmark instruction.",
        ],
        "room_steps": [
            "Open the prepared canary Room; do not start its staging Round.",
            "Click New round.",
            "Paste benchmark_paste exactly once into Public prompt.",
            "Keep Agent C as starter; prepare and start the Round.",
            "Do not intervene during measured canary work.",
        ],
    }


def _desktop_result(run_id: str, thread_id: str | None) -> dict[str, Any]:
    state = _load_state(run_id)
    if state["benchmark_fingerprint"] != pbm.benchmark_fingerprint(pbm_v4.VERSION):
        raise CanaryError("PBM v4 production bytes changed after canary preparation")

    workspace = Path(state["desktop_workspace"])
    rollout, candidate_count = pbm._desktop_rollout(
        workspace,
        int(state["prepared_at_ns"]),
        thread_id,
        codex_usage.default_codex_home().expanduser(),
    )
    usage = codex_usage.analyze_rollout(rollout)
    messages = pbm_v4._desktop_user_messages(rollout)

    invalid: list[str] = []
    failed: list[str] = []
    if len(messages) != 1:
        invalid.append(f"expected exactly one Desktop principal message; observed {len(messages)}")
    elif messages[0].strip() != PASTE:
        invalid.append("Desktop principal message did not exactly match the frozen one-paste prompt")
    cwd = usage["thread"].get("cwd")
    if isinstance(cwd, str) and os.path.normcase(os.path.abspath(cwd)) != os.path.normcase(os.path.abspath(workspace)):
        invalid.append("Desktop rollout cwd did not match canary workspace")
    if (usage.get("final_total_usage") or {}).get("total_tokens") is None:
        failed.append("Desktop provider usage was unavailable")
    if not _marker_ok(workspace):
        failed.append("Desktop canary completion marker is missing or invalid")

    normalized = {
        "input_tokens": (usage.get("final_total_usage") or {}).get("input_tokens"),
        "cached_input_tokens": (usage.get("final_total_usage") or {}).get("cached_input_tokens"),
        "output_tokens": (usage.get("final_total_usage") or {}).get("output_tokens"),
        "reasoning_output_tokens": (usage.get("final_total_usage") or {}).get("reasoning_output_tokens"),
        "total_tokens": (usage.get("final_total_usage") or {}).get("total_tokens"),
        "tool_calls": usage["counts"]["tool_calls"],
        "context_compactions": usage["counts"]["context_compactions"],
    }
    result = {
        "schema": "pbm-v4-canary-platform-result-v1",
        "run_id": run_id,
        "platform": "desktop",
        "classification": pbm_v4._classification(invalid, failed),
        "invalid_reasons": invalid,
        "failed_reasons": failed,
        "valid": not invalid and not failed,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "completed_at": pbm.utc_now(),
        "usage": normalized,
        "duration_seconds": pbm._rollout_duration(usage),
        "provenance": {
            "rollout_path": usage["rollout_path"],
            "thread_id": usage["thread"].get("id"),
            "cwd": cwd,
            "candidate_count": candidate_count,
        },
        "observed_principal_messages": messages,
    }
    _write_json(_root(run_id) / "desktop-usage.json", usage)
    _write_json(_root(run_id) / "desktop-result.json", result)
    _capture_context(run_id, "desktop-canary-post")
    return result


def _find_round(export: dict[str, Any]) -> dict[str, Any]:
    matches = [
        item for item in (export.get("rounds") or [])
        if pbm_v4._round_prompt(item) == PASTE
    ]
    if len(matches) != 1:
        raise CanaryError(
            f"expected exactly one canary Round with the frozen paste; observed {len(matches)}"
        )
    return matches[0]


def _room_result(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    if state["benchmark_fingerprint"] != pbm.benchmark_fingerprint(pbm_v4.VERSION):
        raise CanaryError("PBM v4 production bytes changed after canary preparation")

    base = str(state["room_base"])
    room_id = str(state["room_id"])
    room = pbm_v4._http_json("GET", f"{base}/api/rooms/{room_id}")
    export = pbm_v4._http_json(
        "GET", f"{base}/api/rooms/{room_id}/export?format=json", timeout=60
    )
    round_item = _find_round(export)
    invalid = pbm_v4.room_intervention_reasons(round_item)
    round_status = str(round_item.get("status") or "")
    room_status = str(room.get("status") or "")
    if round_status in {"active", "preparing"} and room_status == "running" and not invalid:
        raise CanaryError("Room canary Round is still active")

    aggregate = pbm.aggregate_room_export(export, str(round_item["id"]))
    failed: list[str] = []
    if round_status != "finished" or round_item.get("close_reason") != "transaction_settled":
        failed.append(
            f"Room canary did not settle cleanly: status={round_status or 'unknown'} "
            f"close_reason={round_item.get('close_reason') or 'unknown'}"
        )
    if not aggregate["usage_complete"]:
        failed.append("Room canary execution usage is incomplete")
    if not _marker_ok(Path(state["room_workspace"])):
        failed.append("Room canary completion marker is missing or invalid")

    result = {
        "schema": "pbm-v4-canary-platform-result-v1",
        "run_id": run_id,
        "platform": "room",
        "classification": pbm_v4._classification(invalid, failed),
        "invalid_reasons": invalid,
        "failed_reasons": failed,
        "valid": not invalid and not failed,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "completed_at": pbm.utc_now(),
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
            "round_id": round_item["id"],
            "room_status": room_status,
            "round_status": round_status,
            "close_reason": round_item.get("close_reason"),
            "executions_by_agent": aggregate["executions_by_agent"],
            "executions": pbm._room_execution_provenance(
                pbm.PROJECT_ROOT / "data" / "codex-room.db",
                room_id,
                str(round_item["id"]),
            ),
        },
    }
    _write_json(_root(run_id) / "room-export.json", export)
    _write_json(_root(run_id) / "room-result.json", result)
    _capture_context(run_id, "room-canary-post")
    return result


def status(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    root = _root(run_id)
    value: dict[str, Any] = {
        "run_id": run_id,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "aborted": (root / "aborted.json").is_file(),
        "desktop_result": None,
        "room_result": None,
        "room": None,
    }
    for platform in ("desktop", "room"):
        path = root / f"{platform}-result.json"
        if path.is_file():
            result = _read_json(path)
            value[f"{platform}_result"] = {
                "classification": result.get("classification"),
                "valid": result.get("valid"),
                "total_tokens": (result.get("usage") or {}).get("total_tokens"),
            }
    try:
        room = pbm_v4._http_json(
            "GET", f"{state['room_base']}/api/rooms/{state['room_id']}"
        )
        export = pbm_v4._http_json(
            "GET",
            f"{state['room_base']}/api/rooms/{state['room_id']}/export?format=json",
            timeout=30,
        )
        matches = [
            item for item in (export.get("rounds") or [])
            if pbm_v4._round_prompt(item) == PASTE
        ]
        value["room"] = {
            "room_id": state["room_id"],
            "status": room.get("status"),
            "canary_round_count": len(matches),
            "canary_round_status": matches[0].get("status") if len(matches) == 1 else None,
            "canary_round_close_reason": matches[0].get("close_reason") if len(matches) == 1 else None,
            "intervention_reasons": pbm_v4.room_intervention_reasons(matches[0])
            if len(matches) == 1
            else [],
        }
    except pbm.PBMError as exc:
        value["room"] = {"error": str(exc)}
    return value


def verify_pair(run_id: str) -> dict[str, Any]:
    root = _root(run_id)
    desktop_path = root / "desktop-result.json"
    room_path = root / "room-result.json"
    if not desktop_path.is_file() or not room_path.is_file():
        raise CanaryError("both canary platform results are required")
    desktop = _read_json(desktop_path)
    room = _read_json(room_path)
    same_fingerprint = desktop.get("benchmark_fingerprint") == room.get("benchmark_fingerprint")
    passed = (
        desktop.get("classification") == "VALID"
        and room.get("classification") == "VALID"
        and same_fingerprint
    )
    result = {
        "schema": "pbm-v4-canary-verification-v1",
        "run_id": run_id,
        "passed": passed,
        "same_fingerprint": same_fingerprint,
        "desktop_classification": desktop.get("classification"),
        "room_classification": room.get("classification"),
        "benchmark_fingerprint": desktop.get("benchmark_fingerprint")
        if same_fingerprint
        else None,
    }
    _write_json(root / "verification.json", result)
    return result


def abort(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    action = "not_attempted"
    try:
        room = pbm_v4._http_json(
            "GET", f"{state['room_base']}/api/rooms/{state['room_id']}"
        )
        if str(room.get("status")) not in {"finished", "stopped", "error", "archived"}:
            pbm_v4._http_json(
                "POST",
                f"{state['room_base']}/api/rooms/{state['room_id']}/stop",
                {},
            )
            action = "stopped"
        else:
            action = f"already_{room.get('status')}"
    except pbm.PBMError as exc:
        action = f"error: {exc}"
    record = {
        "schema": "pbm-v4-canary-abort-v1",
        "run_id": run_id,
        "aborted_at": pbm.utc_now(),
        "room_action": action,
        "desktop_note": "No canary background controller exists; an active native Desktop task must be stopped manually.",
    }
    _write_json(_root(run_id) / "aborted.json", record)
    return record


def bundle(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    root = _root(run_id)
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    path = BUNDLE_ROOT / f"{run_id}-evidence.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(root.rglob("*")):
            if item.is_file():
                archive.write(item, Path("run") / item.relative_to(root))
        try:
            export = pbm_v4._http_json(
                "GET",
                f"{state['room_base']}/api/rooms/{state['room_id']}/export?format=json",
                timeout=60,
            )
            archive.writestr(
                "live/room-export.json",
                json.dumps(export, indent=2, sort_keys=True) + "\n",
            )
        except pbm.PBMError as exc:
            archive.writestr("live/room-export-error.txt", str(exc) + "\n")
        desktop_result = root / "desktop-result.json"
        if desktop_result.is_file():
            result = _read_json(desktop_result)
            rollout = Path(str((result.get("provenance") or {}).get("rollout_path") or ""))
            if rollout.is_file():
                archive.write(rollout, "live/desktop-rollout.jsonl")
        archive.writestr(
            "README.txt",
            (
                f"PBM v4 one-paste canary evidence\nrun_id: {run_id}\n"
                f"benchmark_fingerprint: {state['benchmark_fingerprint']}\n"
            ),
        )
    return {
        "run_id": run_id,
        "bundle_path": str(path.resolve()),
        "size_bytes": path.stat().st_size,
    }


def probe_operations(room_base: str = pbm_v4.DEFAULT_ROOM_BASE) -> dict[str, Any]:
    prepared = prepare_pair(room_base)
    run_id = str(prepared["run_id"])
    before = status(run_id)
    aborted = abort(run_id)
    after = status(run_id)
    evidence = bundle(run_id)
    passed = (
        before.get("aborted") is False
        and aborted.get("room_action") in {"stopped", "already_stopped"}
        and after.get("aborted") is True
        and Path(evidence["bundle_path"]).is_file()
    )
    result = {
        "schema": "pbm-v4-canary-operations-probe-v1",
        "run_id": run_id,
        "passed": passed,
        "before": before,
        "aborted": aborted,
        "after": after,
        "bundle": evidence,
    }
    _write_json(_root(run_id) / "operations-probe.json", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbm-v4-canary")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("prepare-pair")
    command.add_argument("--room-base", default=pbm_v4.DEFAULT_ROOM_BASE)

    command = sub.add_parser("complete-desktop")
    command.add_argument("--run-id", required=True)
    command.add_argument("--thread-id")

    command = sub.add_parser("complete-room")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("status")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("verify-pair")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("abort")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("bundle")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("probe-operations")
    command.add_argument("--room-base", default=pbm_v4.DEFAULT_ROOM_BASE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare-pair":
            result = prepare_pair(args.room_base)
        elif args.command == "complete-desktop":
            result = _desktop_result(args.run_id, args.thread_id)
        elif args.command == "complete-room":
            result = _room_result(args.run_id)
        elif args.command == "status":
            result = status(args.run_id)
        elif args.command == "verify-pair":
            result = verify_pair(args.run_id)
        elif args.command == "abort":
            result = abort(args.run_id)
        elif args.command == "bundle":
            result = bundle(args.run_id)
        elif args.command == "probe-operations":
            result = probe_operations(args.room_base)
        else:
            raise CanaryError("unsupported canary command")
    except (
        CanaryError,
        pbm.PBMError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
