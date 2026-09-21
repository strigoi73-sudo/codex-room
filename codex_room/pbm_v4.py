"""PBM v4: independent complementary one-paste Desktop and Room benchmarks."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from . import codex_usage, pbm, pbm_context

VERSION = "v4"
TASK_ID = "m01-task-battery"
BATTERY_TASK_IDS = (
    "t01-mechanical-change",
    "t02-bounded-investigation",
    "t03-localized-bug",
    "t04-small-feature",
    "t05-state-mutation-bug",
    "t06-constrained-design",
    "t08-integrated-cli",
)
PASTE = "Read BENCHMARK.md and execute it exactly. Do not ask me questions. When complete, stop."
DEFAULT_ROOM_BASE = "http://127.0.0.1:8765"
V4_STATE_DIR = "v4"
BUNDLE_ROOT = pbm.PROJECT_ROOT / "output" / "pbm" / "bundles"


class PBMV4Error(pbm.PBMError):
    """Raised when PBM v4 cannot preserve its comparison contract."""


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _state_path(run_id: str) -> Path:
    return pbm.run_root(run_id) / V4_STATE_DIR / "state.json"


def _load_state(run_id: str) -> dict[str, Any]:
    path = _state_path(run_id)
    if not path.is_file():
        raise PBMV4Error(f"PBM v4 state not found for {run_id}")
    return _read_json(path)


def _git(*args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=pbm.PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise PBMV4Error(f"git {' '.join(args)} failed: {(process.stderr or process.stdout).strip()[:500]}")
    return process.stdout.strip()


def _require_clean_tree() -> dict[str, str]:
    status = _git("status", "--short")
    if status:
        raise PBMV4Error("PBM v4 preparation requires a clean tracked working tree")
    return {
        "branch": _git("branch", "--show-current") or "detached",
        "head": _git("rev-parse", "HEAD"),
    }


def _http_json(method: str, url: str, payload: dict[str, Any] | None = None, *, timeout: float = 30.0) -> Any:
    body = None
    headers: dict[str, str] = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PBMV4Error(f"HTTP {exc.code} for {url}: {detail[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise PBMV4Error(f"Unable to reach {url}: {type(exc.reason).__name__}") from exc
    return {} if not raw else json.loads(raw.decode("utf-8-sig"))


def _capture_context(run_id: str, label: str) -> None:
    asyncio.run(
        pbm_context.capture_snapshot(
            run_root=pbm.run_root(run_id),
            label=label,
            project_root=pbm.PROJECT_ROOT,
            captured_at=pbm.utc_now(),
            if_missing=True,
        )
    )


def _overlay_reference(source: Path, destination: Path) -> None:
    for item in sorted(source.rglob("*")):
        rel = item.relative_to(source)
        target = destination / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def populate_battery_workspace(
    workspace: Path,
    *,
    allow_existing: bool = False,
) -> None:
    """Populate one measured workspace with the seven-task PBM v4 battery."""

    workspace.mkdir(parents=True, exist_ok=True)
    mission_source = pbm.version_root(VERSION) / "fixtures" / TASK_ID / "BENCHMARK.md"
    mission_target = workspace / "BENCHMARK.md"
    if mission_target.exists():
        if not allow_existing and mission_target.read_bytes() != mission_source.read_bytes():
            raise PBMV4Error(f"battery mission would overwrite existing file: {mission_target}")
    else:
        shutil.copy2(mission_source, mission_target)

    tasks_root = workspace / "tasks"
    tasks_root.mkdir(parents=True, exist_ok=True)
    v1_root = pbm.version_root("v1")

    for task_id in BATTERY_TASK_IDS:
        info = pbm.task_info(task_id, "v1")
        source = v1_root / str(info["fixture_dir"])
        destination = tasks_root / task_id
        if destination.exists():
            if allow_existing:
                continue
            raise PBMV4Error(f"battery task workspace already exists: {destination}")
        shutil.copytree(source, destination)
        prompt = (v1_root / str(info["prompt_file"])).read_text(encoding="utf-8").rstrip()
        (destination / "TASK.md").write_text(prompt + "\n", encoding="utf-8")


def grade_battery(workspace: Path) -> dict[str, Any]:
    """Run the frozen task-specific graders and return one battery result."""

    checks: list[dict[str, Any]] = []
    scores: list[float] = []
    for task_id in BATTERY_TASK_IDS:
        task_workspace = workspace / "tasks" / task_id
        result = pbm._run_grader(task_id, task_workspace, "v1")
        score = float(result["score"])
        scores.append(score)
        checks.append(
            {
                "name": task_id,
                "ok": result.get("pass") is True,
                "score": result["score"],
                "result": result,
            }
        )

    passed = all(bool(item["ok"]) for item in checks)
    score = round(sum(scores) / len(scores)) if scores else 0
    return {
        "pass": passed,
        "score": score,
        "checks": checks,
        "task_count": len(checks),
    }


def audit_assets() -> dict[str, Any]:
    manifest = pbm.load_manifest(VERSION)
    if [item["id"] for item in manifest["tasks"]] != [TASK_ID]:
        raise PBMV4Error("PBM v4 manifest must expose the task battery as one measured mission")
    if tuple(manifest.get("battery_tasks") or []) != BATTERY_TASK_IDS:
        raise PBMV4Error("PBM v4 battery task list does not match the frozen task set")
    if list(manifest.get("coverage_requirements") or []) != list(BATTERY_TASK_IDS):
        raise PBMV4Error("PBM v4 coverage requirements must match the battery tasks")
    if "t07-spec-repair" in BATTERY_TASK_IDS:
        raise PBMV4Error("The known-inconsistent v1 t07 specification must not be in PBM v4")

    protocol = manifest.get("v4_protocol") or {}
    if protocol.get("cross_platform_coordination") is not False:
        raise PBMV4Error("PBM v4 must forbid live cross-platform coordination")
    if protocol.get("principal_initiations_per_platform") != 1:
        raise PBMV4Error("PBM v4 requires exactly one principal initiation per platform")
    if protocol.get("common_protocol") != "PROTOCOL.md":
        raise PBMV4Error("PBM v4 must bind the shared common protocol")
    if protocol.get("controller_is_measured") is not False:
        raise PBMV4Error("PBM v4 controller cognition must stay outside measured execution")
    if protocol.get("measured_execution_is_fresh") is not True:
        raise PBMV4Error("PBM v4 must use a fresh measured execution per platform")
    if protocol.get("automatic_pairing") is not True:
        raise PBMV4Error("PBM v4 must pair independent platform arms without principal relay")

    v1_root = pbm.version_root("v1")
    reference_root = pbm.version_root(VERSION) / "reference" / "battery"
    task_inventory: list[dict[str, str]] = []
    reference_scores: dict[str, int | float] = {}

    with tempfile.TemporaryDirectory(prefix="pbm-v4-battery-audit-") as temp_dir:
        audit_root = Path(temp_dir)

        for task_id in BATTERY_TASK_IDS:
            info = pbm.task_info(task_id, "v1")
            prompt = v1_root / str(info["prompt_file"])
            fixture = v1_root / str(info["fixture_dir"])
            grader = v1_root / str(info["grader_file"])
            reference = reference_root / task_id
            if (
                not prompt.is_file()
                or not fixture.is_dir()
                or not grader.is_file()
                or not reference.is_dir()
            ):
                raise PBMV4Error(f"PBM v4 battery asset is incomplete for {task_id}")

            workspace = audit_root / task_id
            shutil.copytree(fixture, workspace)
            _overlay_reference(reference, workspace)
            grade = pbm._run_grader(task_id, workspace, "v1")
            if grade.get("pass") is not True or grade.get("score") != 100:
                raise PBMV4Error(
                    f"PBM v4 known-good reference does not earn full credit for {task_id}"
                )
            reference_scores[task_id] = grade["score"]

            task_inventory.append(
                {
                    "id": task_id,
                    "category": str(info.get("category") or ""),
                    "title": str(info.get("title") or ""),
                }
            )

    return {
        "ok": True,
        "benchmark_version": VERSION,
        "benchmark_fingerprint": pbm.benchmark_fingerprint(VERSION),
        "coverage_requirements": list(BATTERY_TASK_IDS),
        "task_count": len(BATTERY_TASK_IDS),
        "tasks": task_inventory,
        "reference_score": round(
            sum(float(value) for value in reference_scores.values())
            / len(reference_scores)
        ),
        "reference_scores": reference_scores,
    }


def _create_prepared_room(base: str, run_id: str) -> dict[str, Any]:
    health = _http_json("GET", f"{base}/api/health")
    if not isinstance(health, dict) or health.get("ok") is not True:
        raise PBMV4Error("Codex Room health endpoint did not report ok=true")
    payload = {
        "title": f"PBM v4 — {run_id} — READY",
        "topic": (
            "PBM v4 staging placeholder. Do not start this initial Round. "
            "The principal will create one new measured Round after deterministic workspace preparation."
        ),
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
    room = _http_json("POST", f"{base}/api/rooms", payload)
    if not isinstance(room, dict) or not room.get("id") or not room.get("active_round_id"):
        raise PBMV4Error("Prepared Room creation returned incomplete identifiers")
    return room


def prepare_pair(room_base: str = DEFAULT_ROOM_BASE) -> dict[str, Any]:
    audit = audit_assets()
    repo_state = _require_clean_tree()
    run = pbm.new_run(version=VERSION)
    run_id = str(run["run_id"])
    _capture_context(run_id, "pair-prep")

    root = pbm.run_root(run_id)
    desktop_workspace = root / V4_STATE_DIR / "desktop-workspace"
    pbm.prepare_task(
        run_id=run_id,
        task_id=TASK_ID,
        arm="desktop",
        workspace=desktop_workspace,
        evidence_dir=root / TASK_ID / "desktop",
    )
    populate_battery_workspace(desktop_workspace, allow_existing=True)

    room = _create_prepared_room(room_base, run_id)
    room_id = str(room["id"])
    room_workspace = pbm.PROJECT_ROOT / "data" / "rooms" / room_id / "shared"
    pbm.prepare_task(
        run_id=run_id,
        task_id=TASK_ID,
        arm="room",
        workspace=room_workspace,
        evidence_dir=root / TASK_ID / "room",
        allow_existing=True,
    )
    populate_battery_workspace(room_workspace, allow_existing=True)

    state = {
        "schema": "pbm-v4-state-v1",
        "run_id": run_id,
        "benchmark_version": VERSION,
        "benchmark_fingerprint": run["benchmark_fingerprint"],
        "task_id": TASK_ID,
        "prepared_at": pbm.utc_now(),
        "repo": repo_state,
        "room_base": room_base,
        "desktop_workspace": str(desktop_workspace.resolve()),
        "room_id": room_id,
        "room_title": room.get("title"),
        "room_workspace": str(room_workspace.resolve()),
        "staging_round_id": str(room["active_round_id"]),
        "benchmark_paste": PASTE,
        "benchmark_paste_sha256": hashlib.sha256(PASTE.encode("utf-8")).hexdigest(),
        "audit": audit,
    }
    _write_json(_state_path(run_id), state)
    return {
        **state,
        "desktop_steps": [
            "Open a fresh top-level native Codex Desktop task rooted exactly at desktop_workspace.",
            "Paste benchmark_paste exactly once and do not send follow-up benchmark guidance.",
        ],
        "room_steps": [
            "Open the prepared Room; do not start its staging Round.",
            "Click New round.",
            "Paste benchmark_paste exactly once into Public prompt.",
            "Keep Agent C as starter, prepare the Round, then click Start round.",
            "Do not intervene during measured work.",
        ],
    }


def _desktop_user_messages(path: Path) -> list[str]:
    return codex_usage.extract_user_messages(path)


def _marker_ok(workspace: Path) -> bool:
    path = workspace / "PBM_COMPLETE.json"
    if not path.is_file():
        return False
    try:
        value = _read_json(path)
    except (OSError, json.JSONDecodeError):
        return False
    return value == {"status": "complete", "verification": "passed"}


def _classification(invalid_reasons: list[str], failed_reasons: list[str]) -> str:
    if invalid_reasons:
        return "INVALID"
    if failed_reasons:
        return "FAILED"
    return "VALID"


def complete_desktop(run_id: str, thread_id: str | None = None) -> dict[str, Any]:
    state = _load_state(run_id)
    if state["benchmark_fingerprint"] != pbm.benchmark_fingerprint(VERSION):
        raise PBMV4Error("PBM v4 bytes changed after pair preparation")
    result = pbm.desktop_complete(
        run_id=run_id,
        task_id=TASK_ID,
        thread_id=thread_id,
    )
    usage_path = Path(str(result["provenance"]["rollout_path"]))
    messages = _desktop_user_messages(usage_path)
    workspace = Path(state["desktop_workspace"])

    invalid: list[str] = []
    failed: list[str] = []
    if len(messages) != 1:
        invalid.append(f"expected exactly one Desktop principal message; observed {len(messages)}")
    elif messages[0].strip() != PASTE:
        invalid.append("Desktop principal message did not exactly match the frozen benchmark paste")
    if result["provenance"].get("cwd") and os.path.normcase(os.path.abspath(result["provenance"]["cwd"])) != os.path.normcase(os.path.abspath(workspace)):
        invalid.append("Desktop rollout cwd did not match the prepared benchmark workspace")
    if not result["provenance"].get("thread_id"):
        failed.append("Desktop thread id was unavailable")
    if (result.get("usage") or {}).get("total_tokens") is None:
        failed.append("Desktop provider usage was unavailable")
    if not _marker_ok(workspace):
        failed.append("PBM_COMPLETE.json completion marker is missing or invalid")

    result["schema"] = "pbm-v4-platform-result-v1"
    result["classification"] = _classification(invalid, failed)
    result["invalid_reasons"] = invalid
    result["failed_reasons"] = failed
    result["expected_principal_paste"] = PASTE
    result["observed_principal_messages"] = messages
    result["valid_for_comparison"] = result["classification"] == "VALID"
    _write_json(pbm.run_root(run_id) / TASK_ID / "desktop" / "result.json", result)
    _capture_context(run_id, "desktop-post")
    return result


def _round_prompt(round_item: dict[str, Any]) -> str | None:
    prompt = round_item.get("prompt")
    if isinstance(prompt, str):
        return prompt
    for event in round_item.get("events") or []:
        if event.get("event_type") == "round_context_stored" and isinstance(event.get("content"), str):
            return str(event["content"])
    return None


def _find_benchmark_round(export: dict[str, Any]) -> dict[str, Any]:
    matches = [
        item for item in (export.get("rounds") or [])
        if _round_prompt(item) == PASTE
    ]
    if len(matches) != 1:
        raise PBMV4Error(f"expected exactly one Room benchmark Round with the frozen paste; observed {len(matches)}")
    return matches[0]


def room_intervention_reasons(round_item: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if round_item.get("starting_agent") not in {None, "agent_c"}:
        reasons.append("benchmark Round did not start with Agent C")
    if round_item.get("work_model_version") not in {None, 2}:
        reasons.append("benchmark Round did not use production work-model v2")
    if round_item.get("provider_context_mode") not in {None, "assignment_thread"}:
        reasons.append("benchmark Round did not use assignment-thread provider context")

    for event in round_item.get("events") or []:
        event_type = str(event.get("event_type") or "")
        metadata = event.get("metadata") or {}
        if event_type == "observer_message":
            reasons.append("observer message occurred during measured Room work")
        elif event_type == "principal_reply":
            reasons.append("principal reply occurred during measured Room work")
        elif event_type == "principal_message" and metadata.get("principal_channel") is True:
            reasons.append("Agent C requested substantive principal consultation")
        elif event_type in {"room_paused", "room_resumed", "room_stopped"}:
            reasons.append(f"{event_type} occurred during measured Room work")
    return sorted(set(reasons))


def complete_room(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    if state["benchmark_fingerprint"] != pbm.benchmark_fingerprint(VERSION):
        raise PBMV4Error("PBM v4 bytes changed after pair preparation")
    base = str(state["room_base"])
    room_id = str(state["room_id"])
    room = _http_json("GET", f"{base}/api/rooms/{room_id}")
    export = _http_json("GET", f"{base}/api/rooms/{room_id}/export?format=json", timeout=60)
    round_item = _find_benchmark_round(export)

    round_status = str(round_item.get("status") or "")
    room_status = str(room.get("status") or "")
    invalid = room_intervention_reasons(round_item)
    if round_status in {"active", "preparing"} and room_status == "running" and not invalid:
        raise PBMV4Error("Room benchmark Round is still active")

    round_id = str(round_item["id"])
    workspace = Path(state["room_workspace"])
    grade = pbm._run_grader(TASK_ID, workspace, VERSION)
    aggregate = pbm.aggregate_room_export(export, round_id)
    executions = pbm._room_execution_provenance(
        pbm.PROJECT_ROOT / "data" / "codex-room.db",
        room_id,
        round_id,
    )

    failed: list[str] = []
    if round_status != "finished" or round_item.get("close_reason") != "transaction_settled":
        failed.append(
            f"Room benchmark did not settle cleanly: status={round_status or 'unknown'} "
            f"close_reason={round_item.get('close_reason') or 'unknown'}"
        )
    if not aggregate["usage_complete"]:
        failed.append("Room execution usage is incomplete")
    if not _marker_ok(workspace):
        failed.append("PBM_COMPLETE.json completion marker is missing or invalid")

    result = {
        "schema": "pbm-v4-platform-result-v1",
        "run_id": run_id,
        "task_id": TASK_ID,
        "arm": "room",
        "benchmark_version": VERSION,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "completed_at": pbm.utc_now(),
        "classification": _classification(invalid, failed),
        "invalid_reasons": invalid,
        "failed_reasons": failed,
        "valid_for_comparison": not invalid and not failed,
        "quality": grade,
        "usage": {
            **aggregate["total"],
            "tool_calls": aggregate["tool_calls"],
            "failed_tool_calls": aggregate["failed_tool_calls"],
            "execution_count": aggregate["execution_count"],
            "peer_invocations": aggregate["peer_invocations"],
        },
        "duration_seconds": aggregate["duration_seconds"],
        "expected_principal_paste": PASTE,
        "provenance": {
            "room_id": room_id,
            "round_id": round_id,
            "round_status": round_status,
            "room_status": room_status,
            "close_reason": round_item.get("close_reason"),
            "executions_by_agent": aggregate["executions_by_agent"],
            "executions": executions,
        },
    }
    evidence = pbm.run_root(run_id) / TASK_ID / "room"
    _write_json(evidence / "room-export.json", export)
    _write_json(evidence / "grade.json", grade)
    _write_json(evidence / "result.json", result)
    _capture_context(run_id, "room-post")
    return result


def status(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    root = pbm.run_root(run_id)
    result: dict[str, Any] = {
        "run_id": run_id,
        "benchmark_version": VERSION,
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "desktop_result": None,
        "room_result": None,
        "room": None,
        "aborted": (root / V4_STATE_DIR / "aborted.json").is_file(),
    }
    for arm in ("desktop", "room"):
        path = root / TASK_ID / arm / "result.json"
        if path.is_file():
            arm_result = _read_json(path)
            result[f"{arm}_result"] = {
                "classification": arm_result.get("classification"),
                "quality": arm_result.get("quality"),
                "total_tokens": (arm_result.get("usage") or {}).get("total_tokens"),
            }
    try:
        room = _http_json("GET", f"{state['room_base']}/api/rooms/{state['room_id']}")
        export = _http_json(
            "GET",
            f"{state['room_base']}/api/rooms/{state['room_id']}/export?format=json",
            timeout=30,
        )
        matching = [
            item for item in (export.get("rounds") or [])
            if _round_prompt(item) == PASTE
        ]
        result["room"] = {
            "room_id": state["room_id"],
            "title": state["room_title"],
            "status": room.get("status"),
            "benchmark_round_count": len(matching),
            "benchmark_round_status": matching[0].get("status") if len(matching) == 1 else None,
            "benchmark_round_close_reason": matching[0].get("close_reason") if len(matching) == 1 else None,
            "intervention_reasons": room_intervention_reasons(matching[0]) if len(matching) == 1 else [],
        }
    except PBMV4Error as exc:
        result["room"] = {"error": str(exc)}
    return result


def compare(run_id: str) -> dict[str, Any]:
    root = pbm.run_root(run_id)
    desktop_path = root / TASK_ID / "desktop" / "result.json"
    room_path = root / TASK_ID / "room" / "result.json"
    if not desktop_path.is_file() or not room_path.is_file():
        raise PBMV4Error("Both Desktop and Room results are required before comparison")
    desktop = _read_json(desktop_path)
    room = _read_json(room_path)
    same_fingerprint = desktop.get("benchmark_fingerprint") == room.get("benchmark_fingerprint")
    comparable = (
        desktop.get("classification") == "VALID"
        and room.get("classification") == "VALID"
        and same_fingerprint
    )
    d_tokens = (desktop.get("usage") or {}).get("total_tokens")
    r_tokens = (room.get("usage") or {}).get("total_tokens")
    ratio = (
        round(float(r_tokens) / float(d_tokens), 4)
        if isinstance(d_tokens, (int, float)) and d_tokens > 0 and isinstance(r_tokens, (int, float))
        else None
    )
    result = {
        "schema": "pbm-v4-comparison-v1",
        "run_id": run_id,
        "benchmark_version": VERSION,
        "benchmark_fingerprint": desktop.get("benchmark_fingerprint") if same_fingerprint else None,
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
            "executions": (room.get("provenance") or {}).get("executions"),
        },
        "room_to_desktop_total_token_ratio": ratio,
    }
    _write_json(root / "pbm-v4-comparison.json", result)
    lines = [
        f"# PBM v4 comparison — {run_id}",
        "",
        f"- Comparable: **{str(comparable).lower()}**",
        f"- Same fingerprint: **{str(same_fingerprint).lower()}**",
        "",
        "| Platform | Classification | Score | Pass | Tokens | Duration s |",
        "|---|---|---:|---|---:|---:|",
        f"| Desktop | {result['desktop']['classification']} | {result['desktop']['score']} | {result['desktop']['pass']} | {d_tokens} | {result['desktop']['duration_seconds']} |",
        f"| Room | {result['room']['classification']} | {result['room']['score']} | {result['room']['pass']} | {r_tokens} | {result['room']['duration_seconds']} |",
        "",
        f"- Room/Desktop token ratio: {ratio if ratio is not None else 'unavailable'}",
    ]
    (root / "pbm-v4-comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _capture_context(run_id, "pair-complete")
    return result


def abort(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    root = pbm.run_root(run_id)
    room_action = "not_attempted"
    try:
        room = _http_json("GET", f"{state['room_base']}/api/rooms/{state['room_id']}")
        if str(room.get("status")) not in {"finished", "stopped", "error", "archived"}:
            _http_json("POST", f"{state['room_base']}/api/rooms/{state['room_id']}/stop", {})
            room_action = "stopped"
        else:
            room_action = f"already_{room.get('status')}"
    except PBMV4Error as exc:
        room_action = f"error: {exc}"
    record = {
        "schema": "pbm-v4-abort-v1",
        "run_id": run_id,
        "aborted_at": pbm.utc_now(),
        "room_action": room_action,
        "note": "Desktop has no PBM background controller process; stop an active native Desktop task manually if needed.",
    }
    _write_json(root / V4_STATE_DIR / "aborted.json", record)
    return record


def bundle(run_id: str) -> dict[str, Any]:
    state = _load_state(run_id)
    root = pbm.run_root(run_id)
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    path = BUNDLE_ROOT / f"{run_id}-evidence.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(root.rglob("*")):
            if item.is_file():
                archive.write(item, Path("run") / item.relative_to(root))
        try:
            export = _http_json(
                "GET",
                f"{state['room_base']}/api/rooms/{state['room_id']}/export?format=json",
                timeout=60,
            )
            archive.writestr(
                "live/room-export.json",
                json.dumps(export, indent=2, sort_keys=True) + "\n",
            )
        except PBMV4Error as exc:
            archive.writestr("live/room-export-error.txt", str(exc) + "\n")

        desktop_result = root / TASK_ID / "desktop" / "result.json"
        if desktop_result.is_file():
            result = _read_json(desktop_result)
            rollout = Path(str((result.get("provenance") or {}).get("rollout_path") or ""))
            if rollout.is_file():
                archive.write(rollout, Path("live") / "desktop-rollout.jsonl")

        archive.writestr(
            "README.txt",
            (
                f"PBM v4 evidence bundle\nrun_id: {run_id}\n"
                f"benchmark_fingerprint: {state['benchmark_fingerprint']}\n"
            ),
        )
    return {"run_id": run_id, "bundle_path": str(path.resolve()), "size_bytes": path.stat().st_size}


def _json_out(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbm-v4")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("audit")

    command = sub.add_parser("prepare-pair")
    command.add_argument("--room-base", default=DEFAULT_ROOM_BASE)

    command = sub.add_parser("complete-desktop")
    command.add_argument("--run-id", required=True)
    command.add_argument("--thread-id")

    command = sub.add_parser("complete-room")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("status")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("compare")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("abort")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("bundle")
    command.add_argument("--run-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "audit":
            value = audit_assets()
        elif args.command == "prepare-pair":
            value = prepare_pair(args.room_base)
        elif args.command == "complete-desktop":
            value = complete_desktop(args.run_id, args.thread_id)
        elif args.command == "complete-room":
            value = complete_room(args.run_id)
        elif args.command == "status":
            value = status(args.run_id)
        elif args.command == "compare":
            value = compare(args.run_id)
        elif args.command == "abort":
            value = abort(args.run_id)
        elif args.command == "bundle":
            value = bundle(args.run_id)
        else:
            raise PBMV4Error("unsupported PBM v4 command")
    except (
        PBMV4Error,
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
