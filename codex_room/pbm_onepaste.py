"""PBM v3 one-paste-per-platform deterministic coordinator."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from . import codex_usage, pbm, pbm_context
from . import pbm_onepaste_room as room_control

PROJECT_ROOT = pbm.PROJECT_ROOT
CONTROLLER_ROOT = PROJECT_ROOT / "pbm_desktop_controller"
ACTIVE_DIR = CONTROLLER_ROOT / "active"
ACTIVE_TASK_FILE = CONTROLLER_ROOT / "ACTIVE_TASK.md"
ACTIVE_POINTER = PROJECT_ROOT / "output" / "pbm" / "onepaste-active.json"


class OnePasteError(pbm.PBMError):
    """Raised when PBM v3 cannot preserve the one-paste benchmark contract."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def state_path(run_id: str) -> Path:
    return pbm.run_root(run_id) / "onepaste" / "state.json"


def load_state(run_id: str) -> dict[str, Any]:
    return load_json(state_path(run_id))


def save_state(run_id: str, value: dict[str, Any]) -> None:
    write_json(state_path(run_id), value)


def git(*args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise OnePasteError(f"git {' '.join(args)} failed")
    return process.stdout.strip()


def require_clean_main() -> None:
    branch = git("branch", "--show-current")
    if branch != "main":
        raise OnePasteError(
            f"PBM v3 requires canonical main; found {branch or 'detached HEAD'}"
        )
    if git("status", "--short"):
        raise OnePasteError("PBM v3 requires a clean tracked working tree")
    if pbm.current_version() != "v3":
        raise OnePasteError(
            f"PBM CURRENT must be v3; found {pbm.current_version()}"
        )


def sequence(run_meta: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in run_meta["schedule"]:
        first = str(item["first_arm"])
        second = "room" if first == "desktop" else "desktop"
        task_id = str(item["task_id"])
        result.append({"task_id": task_id, "platform": first})
        result.append({"task_id": task_id, "platform": second})
    return result


def result_path(run_id: str, task_id: str, platform: str) -> Path:
    return pbm.run_root(run_id) / task_id / platform / "result.json"


def next_action(run_id: str, platform: str) -> dict[str, Any]:
    if platform not in {"desktop", "room"}:
        raise OnePasteError("platform must be desktop or room")
    run_meta = load_json(pbm.run_root(run_id) / "run.json")
    for ordinal, item in enumerate(sequence(run_meta), start=1):
        if result_path(run_id, item["task_id"], item["platform"]).is_file():
            continue
        if item["platform"] == platform:
            return {
                "action": "run_task",
                "platform": platform,
                "task_id": item["task_id"],
                "sequence_ordinal": ordinal,
            }
        return {
            "action": "wait",
            "platform": platform,
            "waiting_for": item["platform"],
            "task_id": item["task_id"],
            "sequence_ordinal": ordinal,
        }
    return {"action": "complete", "platform": platform}


def capture_context(run_id: str, label: str) -> None:
    asyncio.run(
        pbm_context.capture_snapshot(
            run_root=pbm.run_root(run_id),
            label=label,
            project_root=PROJECT_ROOT,
            captured_at=pbm.utc_now(),
            if_missing=True,
        )
    )


def pair_complete(run_id: str, task_id: str) -> bool:
    return all(
        result_path(run_id, task_id, arm).is_file()
        for arm in ("desktop", "room")
    )


def all_complete(run_id: str) -> bool:
    meta = load_json(pbm.run_root(run_id) / "run.json")
    return all(
        result_path(run_id, item["task_id"], arm).is_file()
        for item in meta["schedule"]
        for arm in ("desktop", "room")
    )


def before_arm(run_id: str, task_id: str) -> None:
    if not any(
        result_path(run_id, task_id, arm).is_file()
        for arm in ("desktop", "room")
    ):
        capture_context(run_id, f"task-{task_id}-pre")


def after_arm(run_id: str, task_id: str) -> None:
    if pair_complete(run_id, task_id):
        capture_context(run_id, f"task-{task_id}-post")
    if all_complete(run_id):
        capture_context(run_id, "run-end")
        pbm.build_report(run_id)


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def server_health(url: str, token: str) -> bool:
    try:
        value = room_control.http_json(
            "GET",
            f"{url}/health?token={token}",
            timeout=1,
        )
    except room_control.RoomControlError:
        return False
    return isinstance(value, dict) and value.get("ok") is True


def start_server(run_id: str, port: int) -> subprocess.Popen[Any]:
    log_path = pbm.run_root(run_id) / "onepaste" / "coordinator.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("ab")
    kwargs: dict[str, Any] = {
        "cwd": str(PROJECT_ROOT),
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
            "codex_room.pbm_onepaste_server",
            "--run-id",
            run_id,
            "--port",
            str(port),
        ],
        **kwargs,
    )
    log_handle.close()
    return process


def init_run(
    controller_cwd: Path,
    room_base: str = room_control.DEFAULT_ROOM_BASE,
) -> dict[str, Any]:
    require_clean_main()
    expected = CONTROLLER_ROOT.resolve()
    if controller_cwd.resolve() != expected:
        raise OnePasteError(
            f"Desktop controller must be opened at {expected}; "
            f"found {controller_cwd.resolve()}"
        )
    room_control.require_health(room_base)

    if ACTIVE_POINTER.is_file():
        active = load_json(ACTIVE_POINTER)
        prior = active.get("run_id")
        if isinstance(prior, str) and (pbm.run_root(prior) / "run.json").is_file():
            if not all_complete(prior):
                state = load_state(prior)
                if server_health(
                    str(state["coordinator_url"]),
                    str(state["token"]),
                ):
                    return init_response(state, resumed=True)
                raise OnePasteError(
                    f"unfinished PBM v3 run {prior} exists but its coordinator "
                    "is not healthy"
                )

    run = pbm.new_run(version="v3")
    run_id = str(run["run_id"])
    capture_context(run_id, "run-start")
    token = secrets.token_urlsafe(24)
    port = free_port()
    coordinator_url = f"http://127.0.0.1:{port}"
    state = {
        "schema": "pbm-onepaste-state-v3",
        "run_id": run_id,
        "benchmark_version": "v3",
        "benchmark_fingerprint": run["benchmark_fingerprint"],
        "created_at": pbm.utc_now(),
        "room_base": room_base,
        "coordinator_url": coordinator_url,
        "token": token,
        "desktop_controller": {
            "cwd": str(expected),
            "thread_id": None,
        },
        "room_controller": None,
        "server": {"port": port, "pid": None},
    }
    save_state(run_id, state)
    process = start_server(run_id, port)
    state["server"]["pid"] = process.pid
    save_state(run_id, state)

    deadline = time.time() + 15
    while time.time() < deadline:
        if server_health(coordinator_url, token):
            break
        if process.poll() is not None:
            raise OnePasteError("PBM coordinator exited during startup")
        time.sleep(0.2)
    else:
        raise OnePasteError("PBM coordinator did not become healthy")

    controller = room_control.make_controller_room(
        base=room_base,
        coordinator_url=coordinator_url,
        token=token,
    )
    state = load_state(run_id)
    state["room_controller"] = controller
    save_state(run_id, state)
    write_json(
        ACTIVE_POINTER,
        {
            "run_id": run_id,
            "benchmark_version": "v3",
            "coordinator_url": coordinator_url,
        },
    )
    return init_response(state, resumed=False)


def init_response(state: dict[str, Any], *, resumed: bool) -> dict[str, Any]:
    return {
        "resumed": resumed,
        "run_id": state["run_id"],
        "benchmark_version": "v3",
        "benchmark_fingerprint": state["benchmark_fingerprint"],
        "coordinator_url": state["coordinator_url"],
        "room_controller": state["room_controller"],
        "room_paste": "Read PBM_ROOM_DRIVER.md and execute it exactly.",
    }


def register_desktop_controller(
    run_id: str,
    thread_id: str,
) -> dict[str, Any]:
    state = load_state(run_id)
    state["desktop_controller"]["thread_id"] = thread_id
    save_state(run_id, state)
    return {
        "run_id": run_id,
        "desktop_controller_thread_id": thread_id,
    }


def desktop_next(run_id: str, *, wait: bool = False) -> dict[str, Any]:
    while True:
        action = next_action(run_id, "desktop")
        if action["action"] != "wait" or not wait:
            break
        time.sleep(1)
    if action["action"] != "run_task":
        return action

    task_id = str(action["task_id"])
    before_arm(run_id, task_id)
    if ACTIVE_DIR.exists():
        shutil.rmtree(ACTIVE_DIR)
    ACTIVE_DIR.mkdir(parents=True)
    evidence = pbm.run_root(run_id) / task_id / "desktop"
    workspace = ACTIVE_DIR / "workspace"
    prepared = pbm.prepare_task(
        run_id=run_id,
        task_id=task_id,
        arm="desktop",
        workspace=workspace,
        evidence_dir=evidence,
    )
    task = pbm.task_info(task_id, "v3")
    ACTIVE_TASK_FILE.write_text(
        "# PBM v3 benchmark task\n\n"
        "You are a fresh native Codex Desktop benchmark task. "
        "Do not inspect the PBM harness, graders/oracles, prior task outputs, "
        "or the Room arm. Do not work outside active/workspace.\n\n"
        f"Assigned workspace: {workspace.resolve()}\n\n"
        "Change directory to that workspace before substantive work.\n\n"
        f"{task['prompt']}\n"
        "When complete, stop. Do not start another task.\n",
        encoding="utf-8",
    )
    delegated = (
        f"PBM {task_id}. Read ACTIVE_TASK.md in the current workspace and "
        "follow it exactly. Work only in active/workspace. Do not inspect "
        "parent or sibling benchmark files. When complete, stop."
    )
    if len(delegated.encode("utf-8")) > 1000:
        raise OnePasteError("Desktop delegated prompt exceeds native task limit")
    return {
        **action,
        "workspace": str(workspace.resolve()),
        "instruction_file": str(ACTIVE_TASK_FILE.resolve()),
        "delegated_prompt": delegated,
        "prepared": prepared,
    }


def rollout_duration(report: dict[str, Any]) -> float | None:
    updates = report.get("token_updates") or []
    if not updates:
        return None
    start = pbm._parse_time((updates[0] or {}).get("timestamp"))
    end = pbm._parse_time((updates[-1] or {}).get("timestamp"))
    if start is None or end is None:
        return None
    return max(0.0, round((end - start).total_seconds(), 3))


def desktop_finish(
    run_id: str,
    task_id: str,
    thread_id: str,
) -> dict[str, Any]:
    action = next_action(run_id, "desktop")
    if action.get("action") != "run_task" or action.get("task_id") != task_id:
        raise OnePasteError(f"{task_id} is not the current Desktop arm")
    evidence = pbm.run_root(run_id) / task_id / "desktop"
    prepared = load_json(evidence / "prepared.json")
    if prepared["benchmark_fingerprint"] != pbm.benchmark_fingerprint("v3"):
        raise OnePasteError("PBM benchmark bytes changed after Desktop preparation")

    workspace = Path(prepared["workspace"])
    rollout = codex_usage.select_rollout(
        codex_home=codex_usage.default_codex_home(),
        thread_id=thread_id,
        include_archived=True,
    )
    usage = codex_usage.analyze_rollout(rollout)
    grade = pbm._run_grader(task_id, workspace, "v3")
    direct_turns = int(usage["counts"]["user_turns"])
    warnings = (
        []
        if direct_turns == 0
        else [
            "delegated Desktop task expected 0 direct user turns; "
            f"observed {direct_turns}"
        ]
    )
    total = usage.get("final_total_usage") or {}
    normalized = {
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
    result = {
        "schema": "pbm-result-v3",
        "run_id": run_id,
        "task_id": task_id,
        "arm": "desktop",
        "benchmark_version": "v3",
        "benchmark_fingerprint": prepared["benchmark_fingerprint"],
        "completed_at": pbm.utc_now(),
        "valid_for_comparison": (
            not warnings and normalized["total_tokens"] is not None
        ),
        "protocol_warnings": warnings,
        "quality": grade,
        "usage": normalized,
        "duration_seconds": rollout_duration(usage),
        "provenance": {
            "rollout_path": usage["rollout_path"],
            "thread_id": usage["thread"]["id"],
            "cli_version": usage["thread"]["cli_version"],
            "source": usage["thread"]["source"],
            "cwd": usage["thread"]["cwd"],
            "controller_delegated": True,
            "direct_user_turns": direct_turns,
        },
    }
    write_json(evidence / "usage.json", usage)
    write_json(evidence / "grade.json", grade)
    write_json(evidence / "result.json", result)

    final_workspace = evidence / "workspace-final"
    if final_workspace.exists():
        shutil.rmtree(final_workspace)
    shutil.copytree(workspace, final_workspace)
    if ACTIVE_DIR.exists():
        shutil.rmtree(ACTIVE_DIR)
    ACTIVE_TASK_FILE.unlink(missing_ok=True)
    after_arm(run_id, task_id)
    return result


def controller_usage_desktop(run_id: str) -> dict[str, Any] | None:
    thread_id = (
        (load_state(run_id).get("desktop_controller") or {}).get("thread_id")
    )
    if not isinstance(thread_id, str) or not thread_id:
        return None
    try:
        path = codex_usage.select_rollout(
            codex_home=codex_usage.default_codex_home(),
            thread_id=thread_id,
            include_archived=True,
        )
        return codex_usage.analyze_rollout(path)
    except (OSError, codex_usage.RolloutUsageError):
        return None


def controller_usage_room(run_id: str) -> dict[str, Any] | None:
    state = load_state(run_id)
    info = state.get("room_controller") or {}
    room_id = info.get("room_id")
    round_id = info.get("round_id")
    if not isinstance(room_id, str) or not isinstance(round_id, str):
        return None
    try:
        export = room_control.http_json(
            "GET",
            f"{state['room_base']}/api/rooms/{room_id}/export?format=json",
            timeout=60,
        )
        return pbm.aggregate_room_export(export, round_id)
    except (room_control.RoomControlError, pbm.PBMError):
        return None


def total_tokens(value: dict[str, Any] | None, arm: str) -> int | None:
    if value is None:
        return None
    if arm == "desktop":
        total = (value.get("final_total_usage") or {}).get("total_tokens")
    else:
        total = (value.get("total") or {}).get("total_tokens")
    return int(total) if isinstance(total, (int, float)) else None


def finalize(run_id: str) -> dict[str, Any]:
    if not all_complete(run_id):
        raise OnePasteError("PBM run is not complete")
    capture_context(run_id, "run-end")
    report = pbm.build_report(run_id)
    desktop_controller = controller_usage_desktop(run_id)
    room_controller = controller_usage_room(run_id)
    d_overhead = total_tokens(desktop_controller, "desktop")
    r_overhead = total_tokens(room_controller, "room")
    d_tasks = int(report["aggregate"]["desktop_total_tokens"])
    r_tasks = int(report["aggregate"]["room_total_tokens"])
    value = {
        "schema": "pbm-onepaste-report-v3",
        "run_id": run_id,
        "benchmark_version": "v3",
        "benchmark_fingerprint": report["benchmark_fingerprint"],
        "task_usage": {
            "desktop_total_tokens": d_tasks,
            "room_total_tokens": r_tasks,
        },
        "controller_overhead": {
            "desktop_total_tokens": d_overhead,
            "room_total_tokens": r_overhead,
        },
        "all_in_usage": {
            "desktop_total_tokens": (
                None if d_overhead is None else d_tasks + d_overhead
            ),
            "room_total_tokens": (
                None if r_overhead is None else r_tasks + r_overhead
            ),
        },
        "desktop_controller_usage": desktop_controller,
        "room_controller_usage": room_controller,
    }
    write_json(pbm.run_root(run_id) / "pbm-onepaste-report.json", value)
    if ACTIVE_POINTER.is_file():
        active = load_json(ACTIVE_POINTER)
        if active.get("run_id") == run_id:
            ACTIVE_POINTER.unlink()
    pid = ((load_state(run_id).get("server") or {}).get("pid"))
    if isinstance(pid, int) and pid > 0:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbm-onepaste")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("init")
    command.add_argument("--controller-cwd", type=Path, required=True)
    command.add_argument(
        "--room-base",
        default=room_control.DEFAULT_ROOM_BASE,
    )

    command = sub.add_parser("register-desktop-controller")
    command.add_argument("--run-id", required=True)
    command.add_argument("--thread-id", required=True)

    command = sub.add_parser("desktop-next")
    command.add_argument("--run-id", required=True)
    command.add_argument("--wait", action="store_true")

    command = sub.add_parser("desktop-finish")
    command.add_argument("--run-id", required=True)
    command.add_argument("--task-id", required=True)
    command.add_argument("--thread-id", required=True)

    command = sub.add_parser("finalize")
    command.add_argument("--run-id", required=True)

    command = sub.add_parser("next")
    command.add_argument("--run-id", required=True)
    command.add_argument(
        "--platform",
        choices=["desktop", "room"],
        required=True,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            value = init_run(args.controller_cwd, args.room_base)
        elif args.command == "register-desktop-controller":
            value = register_desktop_controller(args.run_id, args.thread_id)
        elif args.command == "desktop-next":
            value = desktop_next(args.run_id, wait=args.wait)
        elif args.command == "desktop-finish":
            value = desktop_finish(
                args.run_id,
                args.task_id,
                args.thread_id,
            )
        elif args.command == "finalize":
            value = finalize(args.run_id)
        elif args.command == "next":
            value = next_action(args.run_id, args.platform)
        else:
            raise OnePasteError("unsupported command")
    except (
        OnePasteError,
        room_control.RoomControlError,
        pbm.PBMError,
        OSError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
