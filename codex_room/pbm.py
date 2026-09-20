"""Deterministic harness for PBM, the Codex Room performance benchmark."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import codex_usage, pbm_context

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PBM_ROOT = PROJECT_ROOT / "benchmarks" / "pbm"
OUTPUT_ROOT = PROJECT_ROOT / "output" / "pbm" / "runs"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class PBMError(ValueError):
    """Raised when PBM inputs or evidence are incomplete or inconsistent."""


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def current_version() -> str:
    value = (PBM_ROOT / "CURRENT").read_text(encoding="utf-8").strip()
    if not value:
        raise PBMError("PBM CURRENT is empty")
    return value


def version_root(version: str | None = None) -> Path:
    resolved = version or current_version()
    root = PBM_ROOT / resolved
    if not root.is_dir():
        raise PBMError(f"PBM version not found: {resolved}")
    return root


def load_manifest(version: str | None = None) -> dict[str, Any]:
    root = version_root(version)
    data = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if data.get("version") != root.name:
        raise PBMError("PBM manifest version does not match its directory")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise PBMError("PBM manifest contains no tasks")
    ids = [item.get("id") for item in tasks]
    if any(not isinstance(item, str) or not item for item in ids):
        raise PBMError("Every PBM task requires a non-empty id")
    if len(ids) != len(set(ids)):
        raise PBMError("PBM task ids must be unique")
    return data


def benchmark_fingerprint(version: str | None = None) -> str:
    root = version_root(version)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    roots = [root]
    asset_version = manifest.get("asset_version")
    if isinstance(asset_version, str) and asset_version and asset_version != root.name:
        roots.append(version_root(asset_version))

    digest = hashlib.sha256()
    for source_root in roots:
        prefix = source_root.name
        for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
            rel = f"{prefix}/{path.relative_to(source_root).as_posix()}"
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def task_info(task_id: str, version: str | None = None) -> dict[str, Any]:
    manifest = load_manifest(version)
    asset_version = manifest.get("asset_version") or manifest["version"]
    root = version_root(str(asset_version))
    for task in manifest["tasks"]:
        if task["id"] != task_id:
            continue
        prompt_path = root / task["prompt_file"]
        prompt = prompt_path.read_text(encoding="utf-8").rstrip() + "\n"
        guard = (
            "PBM benchmark rule: work only from the task prompt and task workspace. "
            "Do not inspect PBM manifests, benchmark harness code, graders/oracles, "
            "the other product arm, or prior PBM results.\n\n"
        )
        return {
            **task,
            "version": manifest["version"],
            "asset_version": str(asset_version),
            "schema_version": int(manifest.get("schema_version") or 1),
            "prompt": guard + prompt,
            "benchmark_fingerprint": benchmark_fingerprint(manifest["version"]),
        }
    raise PBMError(f"Unknown PBM task: {task_id}")


def _safe_run_id(run_id: str) -> str:
    if not RUN_ID_RE.fullmatch(run_id):
        raise PBMError("run id may contain only letters, digits, dot, underscore, and hyphen")
    return run_id


def run_root(run_id: str) -> Path:
    return OUTPUT_ROOT / _safe_run_id(run_id)


def new_run(run_id: str | None = None, version: str | None = None) -> dict[str, Any]:
    manifest = load_manifest(version)
    if run_id is None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"pbm-{manifest['version']}-{stamp}"
    root = run_root(run_id)
    if root.exists():
        raise PBMError(f"PBM run already exists: {run_id}")
    root.mkdir(parents=True)
    schedule = []
    for index, task in enumerate(manifest["tasks"], start=1):
        schedule.append(
            {
                "index": index,
                "task_id": task["id"],
                "first_arm": "desktop" if index % 2 else "room",
            }
        )
    schema_version = int(manifest.get("schema_version") or 1)
    payload = {
        "schema": f"pbm-run-v{schema_version}",
        "schema_version": schema_version,
        "run_id": run_id,
        "benchmark_version": manifest["version"],
        "benchmark_fingerprint": benchmark_fingerprint(manifest["version"]),
        "created_at": utc_now(),
        "mode": "naturalistic",
        "schedule": schedule,
    }
    (root / "run.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {**payload, "run_root": str(root)}


def _copy_fixture(source: Path, workspace: Path, *, allow_existing: bool) -> None:
    if workspace.exists() and not allow_existing and any(workspace.iterdir()):
        raise PBMError(f"workspace is not empty: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)
    for source_path in sorted(source.rglob("*")):
        rel = source_path.relative_to(source)
        destination = workspace / rel
        if source_path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        if destination.exists():
            raise PBMError(f"PBM fixture would overwrite existing path: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)


def prepare_task(
    *,
    run_id: str,
    task_id: str,
    arm: str,
    workspace: Path,
    evidence_dir: Path,
    allow_existing: bool = False,
) -> dict[str, Any]:
    if arm not in {"desktop", "room"}:
        raise PBMError("PBM arm must be desktop or room")
    expected_run = run_root(run_id) / "run.json"
    if not expected_run.is_file():
        raise PBMError(f"PBM run not found: {run_id}")
    run_meta = json.loads(expected_run.read_text(encoding="utf-8"))
    info = task_info(task_id, run_meta["benchmark_version"])
    root = version_root(info["asset_version"])
    fixture = root / info["fixture_dir"]
    if not fixture.is_dir():
        raise PBMError(f"fixture directory not found: {fixture}")
    if run_meta.get("benchmark_fingerprint") != info["benchmark_fingerprint"]:
        raise PBMError("PBM benchmark bytes changed after this run was created")
    _copy_fixture(fixture, workspace, allow_existing=allow_existing)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = evidence_dir / "prompt.txt"
    prompt_path.write_text(info["prompt"], encoding="utf-8")
    prepared = {
        "schema": f"pbm-prepared-v{info['schema_version']}",
        "run_id": run_id,
        "task_id": task_id,
        "arm": arm,
        "benchmark_version": info["version"],
        "benchmark_fingerprint": info["benchmark_fingerprint"],
        "workspace": str(workspace.resolve()),
        "prompt_path": str(prompt_path.resolve()),
        "prepared_at": utc_now(),
        "prepared_at_ns": time.time_ns(),
    }
    (evidence_dir / "prepared.json").write_text(
        json.dumps(prepared, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return prepared


def _run_grader(
    task_id: str, workspace: Path, version: str | None = None
) -> dict[str, Any]:
    info = task_info(task_id, version)
    grader = version_root(info["asset_version"]) / info["grader_file"]
    process = subprocess.run(
        [sys.executable, str(grader), str(workspace.resolve())],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise PBMError(f"grader failed for {task_id}: {detail[:1000]}")
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise PBMError(f"grader returned invalid JSON for {task_id}") from exc
    if not isinstance(result.get("score"), (int, float)) or not isinstance(
        result.get("pass"), bool
    ):
        raise PBMError(f"grader returned incomplete result for {task_id}")
    return result


def _norm_path(value: str | Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(value)))


def _desktop_rollout(
    workspace: Path, prepared_at_ns: int, thread_id: str | None, codex_home: Path
) -> tuple[Path, int]:
    if thread_id:
        return (
            codex_usage.select_rollout(
                codex_home=codex_home,
                thread_id=thread_id,
                include_archived=True,
            ),
            1,
        )
    target = _norm_path(workspace)
    candidates: list[Path] = []
    threshold = prepared_at_ns - 10_000_000_000
    for path in codex_usage._rollout_paths(codex_home, include_archived=True):
        try:
            if path.stat().st_mtime_ns < threshold:
                continue
            meta = codex_usage._session_meta(path)
        except (OSError, codex_usage.RolloutUsageError):
            continue
        if not codex_usage._is_top_level(meta):
            continue
        cwd = meta.get("cwd")
        if isinstance(cwd, str) and _norm_path(cwd) == target:
            candidates.append(path)
    if not candidates:
        raise PBMError(
            "No fresh top-level Codex Desktop rollout matched the exact PBM workspace. "
            "Open a new Desktop chat on the prepared folder, or complete with -ThreadId."
        )
    if len(candidates) != 1:
        ids = [codex_usage._thread_id(codex_usage._session_meta(item)) for item in candidates]
        raise PBMError(
            "Multiple fresh Desktop rollouts matched this workspace; rerun completion "
            f"with -ThreadId. Candidates: {ids}"
        )
    return candidates[0], 1


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _rollout_duration(report: dict[str, Any]) -> float | None:
    turns = report.get("user_turns") or []
    updates = report.get("token_updates") or []
    if not turns or not updates:
        return None
    start = _parse_time(turns[0].get("timestamp"))
    end = _parse_time(updates[-1].get("timestamp"))
    if start is None or end is None:
        return None
    return max(0.0, round((end - start).total_seconds(), 3))


def desktop_complete(
    *,
    run_id: str,
    task_id: str,
    thread_id: str | None = None,
    codex_home: Path | None = None,
) -> dict[str, Any]:
    evidence = run_root(run_id) / task_id / "desktop"
    prepared_path = evidence / "prepared.json"
    if not prepared_path.is_file():
        raise PBMError("Desktop arm has not been prepared")
    prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
    if prepared["benchmark_fingerprint"] != benchmark_fingerprint(
        prepared["benchmark_version"]
    ):
        raise PBMError("PBM benchmark bytes changed after Desktop preparation")
    workspace = Path(prepared["workspace"])
    rollout, candidate_count = _desktop_rollout(
        workspace,
        int(prepared["prepared_at_ns"]),
        thread_id,
        (codex_home or codex_usage.default_codex_home()).expanduser(),
    )
    usage = codex_usage.analyze_rollout(rollout)
    grade = _run_grader(task_id, workspace, prepared["benchmark_version"])
    protocol_warnings: list[str] = []
    user_turns = usage["counts"]["user_turns"]
    if user_turns != 1:
        protocol_warnings.append(
            f"fresh Desktop benchmark chat expected exactly 1 user turn; observed {user_turns}"
        )
    normalized = {
        "input_tokens": (usage.get("final_total_usage") or {}).get("input_tokens"),
        "cached_input_tokens": (usage.get("final_total_usage") or {}).get(
            "cached_input_tokens"
        ),
        "output_tokens": (usage.get("final_total_usage") or {}).get("output_tokens"),
        "reasoning_output_tokens": (usage.get("final_total_usage") or {}).get(
            "reasoning_output_tokens"
        ),
        "total_tokens": (usage.get("final_total_usage") or {}).get("total_tokens"),
        "provider_response_usage_records": usage["counts"][
            "provider_response_usage_records"
        ],
        "tool_calls": usage["counts"]["tool_calls"],
        "context_compactions": usage["counts"]["context_compactions"],
    }
    result = {
        "schema": f"pbm-result-v{int(load_manifest(prepared['benchmark_version']).get('schema_version') or 1)}",
        "run_id": run_id,
        "task_id": task_id,
        "arm": "desktop",
        "benchmark_version": prepared["benchmark_version"],
        "benchmark_fingerprint": prepared["benchmark_fingerprint"],
        "completed_at": utc_now(),
        "valid_for_comparison": not protocol_warnings
        and normalized["total_tokens"] is not None,
        "protocol_warnings": protocol_warnings,
        "quality": grade,
        "usage": normalized,
        "duration_seconds": _rollout_duration(usage),
        "provenance": {
            "rollout_path": usage["rollout_path"],
            "thread_id": usage["thread"]["id"],
            "cli_version": usage["thread"]["cli_version"],
            "source": usage["thread"]["source"],
            "cwd": usage["thread"]["cwd"],
            "candidate_count": candidate_count,
        },
    }
    (evidence / "usage.json").write_text(
        json.dumps(usage, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (evidence / "grade.json").write_text(
        json.dumps(grade, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (evidence / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def aggregate_room_export(export: dict[str, Any], round_id: str) -> dict[str, Any]:
    rounds = export.get("rounds") or []
    round_item = next((item for item in rounds if item.get("id") == round_id), None)
    if round_item is None:
        raise PBMError(f"Room export does not contain round {round_id}")
    economics = [
        event
        for event in round_item.get("events", [])
        if event.get("event_type") == "execution_economics"
    ]
    totals = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens": 0,
    }
    complete = True
    tool_calls = 0
    failed_tool_calls = 0
    peer_invocations = 0
    by_agent: dict[str, int] = {}
    for event in economics:
        metadata = event.get("metadata") or {}
        status = metadata.get("usage_delta_status")
        delta = metadata.get("usage_delta") or {}
        if status not in {"first_execution", "computed"} or not isinstance(delta, dict):
            complete = False
        for field in totals:
            value = delta.get(field)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                totals[field] += int(value)
        tool_calls += int(metadata.get("tool_calls") or 0)
        failed_tool_calls += int(metadata.get("failed_tool_calls") or 0)
        peer_invocations += int(metadata.get("peer_invocations") or 0)
        source = str(event.get("source") or "unknown")
        by_agent[source] = by_agent.get(source, 0) + 1
    started = _parse_time(round_item.get("started_at"))
    ended = _parse_time(round_item.get("ended_at"))
    duration = (
        max(0.0, round((ended - started).total_seconds(), 3))
        if started is not None and ended is not None
        else None
    )
    return {
        "round_status": round_item.get("status"),
        "close_reason": round_item.get("close_reason"),
        "execution_count": len(economics),
        "executions_by_agent": dict(sorted(by_agent.items())),
        "usage_complete": complete and bool(economics),
        "total": totals,
        "tool_calls": tool_calls,
        "failed_tool_calls": failed_tool_calls,
        "peer_invocations": peer_invocations,
        "duration_seconds": duration,
    }


def _room_execution_provenance(
    database: Path, room_id: str, round_id: str
) -> list[dict[str, Any]]:
    if not database.is_file():
        return []
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT e.batch_id, a.agent_key, e.model, e.reasoning_effort, e.state,
                   e.sdk_thread_id, e.sdk_turn_id
            FROM agent_executions e
            JOIN agents a ON a.id=e.agent_id
            WHERE e.room_id=? AND e.round_id=?
            ORDER BY e.rowid
            """,
            (room_id, round_id),
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def room_complete(
    *,
    run_id: str,
    task_id: str,
    room_id: str,
    round_id: str,
    export_path: Path,
    database: Path,
) -> dict[str, Any]:
    evidence = run_root(run_id) / task_id / "room"
    prepared_path = evidence / "prepared.json"
    if not prepared_path.is_file():
        raise PBMError("Room arm has not been prepared")
    prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
    if prepared["benchmark_fingerprint"] != benchmark_fingerprint(
        prepared["benchmark_version"]
    ):
        raise PBMError("PBM benchmark bytes changed after Room preparation")
    export = json.loads(export_path.read_text(encoding="utf-8-sig"))
    aggregate = aggregate_room_export(export, round_id)
    grade = _run_grader(
        task_id, Path(prepared["workspace"]), prepared["benchmark_version"]
    )
    executions = _room_execution_provenance(database, room_id, round_id)
    result = {
        "schema": "pbm-result-v1",
        "run_id": run_id,
        "task_id": task_id,
        "arm": "room",
        "benchmark_version": prepared["benchmark_version"],
        "benchmark_fingerprint": prepared["benchmark_fingerprint"],
        "completed_at": utc_now(),
        "valid_for_comparison": aggregate["usage_complete"],
        "protocol_warnings": (
            [] if aggregate["usage_complete"] else ["Room execution usage deltas are incomplete"]
        ),
        "quality": grade,
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
            "round_status": aggregate["round_status"],
            "close_reason": aggregate["close_reason"],
            "executions_by_agent": aggregate["executions_by_agent"],
            "executions": executions,
        },
    }
    (evidence / "grade.json").write_text(
        json.dumps(grade, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (evidence / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def build_report(run_id: str) -> dict[str, Any]:
    root = run_root(run_id)
    run_meta = json.loads((root / "run.json").read_text(encoding="utf-8"))
    manifest = load_manifest(run_meta["benchmark_version"])
    schema_version = int(manifest.get("schema_version") or 1)
    context = pbm_context.context_summary(root) if schema_version >= 2 else None
    pairs: list[dict[str, Any]] = []
    aggregate = {
        "desktop_total_tokens": 0,
        "room_total_tokens": 0,
        "desktop_quality_passes": 0,
        "room_quality_passes": 0,
        "complete_pairs": 0,
    }
    for task in manifest["tasks"]:
        entry: dict[str, Any] = {"task_id": task["id"], "title": task["title"]}
        results: dict[str, Any] = {}
        for arm in ("desktop", "room"):
            path = root / task["id"] / arm / "result.json"
            if path.is_file():
                results[arm] = json.loads(path.read_text(encoding="utf-8"))
        entry["results"] = results
        desktop = results.get("desktop")
        room = results.get("room")
        if desktop and room:
            aggregate["complete_pairs"] += 1
            d_total = desktop.get("usage", {}).get("total_tokens")
            r_total = room.get("usage", {}).get("total_tokens")
            if isinstance(d_total, (int, float)) and d_total > 0 and isinstance(
                r_total, (int, float)
            ):
                entry["room_to_desktop_total_token_ratio"] = round(r_total / d_total, 4)
            else:
                entry["room_to_desktop_total_token_ratio"] = None
        for arm, result in results.items():
            total = result.get("usage", {}).get("total_tokens")
            if isinstance(total, (int, float)):
                aggregate[f"{arm}_total_tokens"] += int(total)
            if result.get("quality", {}).get("pass") is True:
                aggregate[f"{arm}_quality_passes"] += 1
        pairs.append(entry)
    report = {
        "schema": f"pbm-report-v{schema_version}",
        "run_id": run_id,
        "benchmark_version": run_meta["benchmark_version"],
        "benchmark_fingerprint": run_meta["benchmark_fingerprint"],
        "generated_at": utc_now(),
        "aggregate": aggregate,
        "context": context,
        "pairs": pairs,
    }
    (root / "pbm-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        f"# PBM {run_meta['benchmark_version']} report — {run_id}",
        "",
        f"- Benchmark fingerprint: `{run_meta['benchmark_fingerprint']}`",
        f"- Complete pairs: {aggregate['complete_pairs']} / {len(manifest['tasks'])}",
        f"- Desktop quality passes: {aggregate['desktop_quality_passes']} / {len(manifest['tasks'])}",
        f"- Room quality passes: {aggregate['room_quality_passes']} / {len(manifest['tasks'])}",
    ]
    if context is not None:
        lines.extend(
            [
                f"- Context snapshots: {context['snapshot_count']}",
                f"- Run-start rate limits: {((context.get('run_start') or {}).get('rate_limits_status') or 'unavailable')}",
                f"- Run-start account usage: {((context.get('run_start') or {}).get('account_usage_status') or 'unavailable')}",
                f"- Run-end rate limits: {((context.get('run_end') or {}).get('rate_limits_status') or 'not yet captured')}",
                f"- Run-end account usage: {((context.get('run_end') or {}).get('account_usage_status') or 'not yet captured')}",
            ]
        )
    lines.extend(
        [
        "",
        "| Task | Desktop score | Desktop tokens | Room score | Room tokens | Room/Desktop |",
        "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for pair in pairs:
        desktop = pair["results"].get("desktop") or {}
        room = pair["results"].get("room") or {}
        ratio = pair.get("room_to_desktop_total_token_ratio")
        lines.append(
            "| {task} | {ds} | {dt} | {rs} | {rt} | {ratio} |".format(
                task=pair["task_id"],
                ds=(desktop.get("quality") or {}).get("score", "—"),
                dt=(desktop.get("usage") or {}).get("total_tokens", "—"),
                rs=(room.get("quality") or {}).get("score", "—"),
                rt=(room.get("usage") or {}).get("total_tokens", "—"),
                ratio=("—" if ratio is None else f"{ratio:.4f}"),
            )
        )
    (root / "pbm-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def _json_out(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbm", description="PBM deterministic harness")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("new-run")
    command.add_argument("--run-id")
    command.add_argument("--version")
    command.add_argument("--json", action="store_true")

    command = sub.add_parser("task")
    command.add_argument("--task-id", required=True)
    command.add_argument("--version")
    command.add_argument("--json", action="store_true")

    command = sub.add_parser("prepare")
    command.add_argument("--run-id", required=True)
    command.add_argument("--task-id", required=True)
    command.add_argument("--arm", choices=["desktop", "room"], required=True)
    command.add_argument("--workspace", type=Path, required=True)
    command.add_argument("--evidence-dir", type=Path, required=True)
    command.add_argument("--allow-existing", action="store_true")

    command = sub.add_parser("desktop-complete")
    command.add_argument("--run-id", required=True)
    command.add_argument("--task-id", required=True)
    command.add_argument("--thread-id")
    command.add_argument("--codex-home", type=Path)

    command = sub.add_parser("room-complete")
    command.add_argument("--run-id", required=True)
    command.add_argument("--task-id", required=True)
    command.add_argument("--room-id", required=True)
    command.add_argument("--round-id", required=True)
    command.add_argument("--export", type=Path, required=True)
    command.add_argument(
        "--database", type=Path, default=PROJECT_ROOT / "data" / "codex-room.db"
    )

    command = sub.add_parser("report")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("context-snapshot")
    command.add_argument("--run-id", required=True)
    command.add_argument("--label", required=True)
    command.add_argument("--if-missing", action="store_true")

    command = sub.add_parser("list")
    command.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "new-run":
            value = new_run(args.run_id, args.version)
        elif args.command == "task":
            value = task_info(args.task_id, args.version)
        elif args.command == "prepare":
            value = prepare_task(
                run_id=args.run_id,
                task_id=args.task_id,
                arm=args.arm,
                workspace=args.workspace,
                evidence_dir=args.evidence_dir,
                allow_existing=args.allow_existing,
            )
        elif args.command == "desktop-complete":
            value = desktop_complete(
                run_id=args.run_id,
                task_id=args.task_id,
                thread_id=args.thread_id,
                codex_home=args.codex_home,
            )
        elif args.command == "room-complete":
            value = room_complete(
                run_id=args.run_id,
                task_id=args.task_id,
                room_id=args.room_id,
                round_id=args.round_id,
                export_path=args.export,
                database=args.database,
            )
        elif args.command == "report":
            value = build_report(args.run_id)
        elif args.command == "context-snapshot":
            root = run_root(args.run_id)
            run_meta = json.loads((root / "run.json").read_text(encoding="utf-8"))
            if int(run_meta.get("schema_version") or 1) < 2:
                raise PBMError("context snapshots are not part of this PBM version")
            current_fingerprint = benchmark_fingerprint(run_meta["benchmark_version"])
            if run_meta.get("benchmark_fingerprint") != current_fingerprint:
                raise PBMError("PBM benchmark bytes changed after this run was created")
            value = asyncio.run(
                pbm_context.capture_snapshot(
                    run_root=root,
                    label=args.label,
                    project_root=PROJECT_ROOT,
                    captured_at=utc_now(),
                    if_missing=args.if_missing,
                )
            )
        elif args.command == "list":
            manifest = load_manifest()
            value = {
                "version": manifest["version"],
                "benchmark_fingerprint": benchmark_fingerprint(),
                "tasks": manifest["tasks"],
            }
        else:
            raise PBMError("unsupported PBM command")
    except (PBMError, ValueError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    _json_out(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
