"""Room-side deterministic helpers for PBM v3 one-paste orchestration."""

from __future__ import annotations

import json
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from . import pbm

PROJECT_ROOT = pbm.PROJECT_ROOT
DEFAULT_ROOM_BASE = "http://127.0.0.1:8765"
TERMINAL_ROOM_STATUSES = {"finished", "error", "stopped", "paused"}


class RoomControlError(pbm.PBMError):
    """Raised when PBM cannot preserve the Room-side orchestration contract."""


def http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: float = 30.0,
) -> Any:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RoomControlError(f"HTTP {exc.code} for {url}: {detail[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise RoomControlError(
            f"Unable to reach {url}: {type(exc.reason).__name__}"
        ) from exc
    return {} if not raw else json.loads(raw.decode("utf-8-sig"))


def require_health(base: str) -> dict[str, Any]:
    value = http_json("GET", f"{base}/api/health")
    if not isinstance(value, dict) or value.get("ok") is not True:
        raise RoomControlError("Codex Room health endpoint did not report ok=true")
    return value


def create_room(
    base: str,
    *,
    title: str,
    topic: str,
    max_turns: int,
) -> dict[str, Any]:
    value = http_json(
        "POST",
        f"{base}/api/rooms",
        {
            "title": title,
            "topic": topic,
            "auto_start": False,
            "max_turns": max_turns,
            "max_consecutive_passes": 3,
            "inactivity_seconds": 900,
            "starting_agent": "agent_c",
            "completion_policy": "auto_settle",
            "required_contributors": [],
        },
    )
    if not isinstance(value, dict) or not value.get("id") or not value.get(
        "active_round_id"
    ):
        raise RoomControlError("Room creation returned incomplete identifiers")
    return value


def room_workspace(room_id: str) -> Path:
    return PROJECT_ROOT / "data" / "rooms" / room_id / "shared"


def controller_worker_text(endpoint: str) -> str:
    return f"""$ErrorActionPreference = 'Stop'
$Uri = '{endpoint}'
$Log = Join-Path $PSScriptRoot 'PBM_ROOM_CONTROLLER.log'
$Done = Join-Path $PSScriptRoot 'PBM_ROOM_CONTROLLER.done.json'

try {{
    $result = Invoke-RestMethod -Method Post -Uri $Uri -TimeoutSec 86400
    $result | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Done -Encoding UTF8
    "PBM Room controller completed at $([DateTime]::UtcNow.ToString('o'))" |
        Add-Content -LiteralPath $Log
}}
catch {{
    $_ | Out-String | Add-Content -LiteralPath $Log
    throw
}}
"""


def controller_launcher_text() -> str:
    return """$ErrorActionPreference = 'Stop'
$Worker = Join-Path $PSScriptRoot 'PBM_ROOM_WORKER.ps1'
$Log = Join-Path $PSScriptRoot 'PBM_ROOM_CONTROLLER.launch.log'

if (-not (Test-Path -LiteralPath $Worker)) {
    throw "PBM Room worker not found: $Worker"
}

$WorkerArgument = '"' + $Worker + '"'

$process = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $WorkerArgument
) -WindowStyle Hidden -PassThru

"Started PBM Room worker PID $($process.Id) at $([DateTime]::UtcNow.ToString('o'))" |
    Set-Content -LiteralPath $Log -Encoding UTF8

Write-Host "PBM Room background controller started. PID: $($process.Id)"
Write-Host 'This controller Room does not solve benchmark tasks itself.'
"""


def make_controller_room(
    *,
    base: str,
    coordinator_url: str,
    token: str,
) -> dict[str, Any]:
    title = "PBM v3 Controller — ACTIVE"
    created = create_room(
        base,
        title=title,
        topic=(
            "PBM v3 coordination-only controller. Do not solve benchmark tasks here. "
            "Immediately use CONSULT_PRINCIPAL to ask the human principal for the "
            "single PBM Room controller instruction, then wait. Do not invoke A or B "
            "and do not perform benchmark work before that private reply."
        ),
        max_turns=4,
    )
    room_id = str(created["id"])
    round_id = str(created["active_round_id"])
    workspace = room_workspace(room_id)
    workspace.mkdir(parents=True, exist_ok=True)

    shutil.copy2(
        pbm.version_root("v3") / "room-driver.md",
        workspace / "PBM_ROOM_DRIVER.md",
    )
    endpoint = f"{coordinator_url}/room/run?token={urllib.parse.quote(token)}"
    (workspace / "PBM_ROOM_WORKER.ps1").write_text(
        controller_worker_text(endpoint), encoding="utf-8"
    )
    (workspace / "PBM_ROOM_CLIENT.ps1").write_text(
        controller_launcher_text(), encoding="utf-8"
    )
    http_json(
        "POST",
        f"{base}/api/rooms/{room_id}/rounds/{round_id}/start",
        {},
    )
    return {
        "room_id": room_id,
        "round_id": round_id,
        "title": title,
        "workspace": str(workspace.resolve()),
    }


def prepare_task_room(
    *,
    run_id: str,
    task_id: str,
    base: str,
) -> dict[str, Any]:
    evidence = pbm.run_root(run_id) / task_id / "room"
    setup_path = evidence / "room-setup.json"
    if setup_path.is_file():
        return json.loads(setup_path.read_text(encoding="utf-8-sig"))

    task = pbm.task_info(task_id, "v3")
    created = create_room(
        base,
        title=f"PBM v3 — {task_id}",
        topic=str(task["prompt"]),
        max_turns=int(task["room_max_turns"]),
    )
    room_id = str(created["id"])
    round_id = str(created["active_round_id"])
    workspace = room_workspace(room_id)
    pbm.prepare_task(
        run_id=run_id,
        task_id=task_id,
        arm="room",
        workspace=workspace,
        evidence_dir=evidence,
        allow_existing=True,
    )
    setup = {
        "run_id": run_id,
        "task_id": task_id,
        "room_id": room_id,
        "round_id": round_id,
        "workspace": str(workspace.resolve()),
        "created_at": pbm.utc_now(),
    }
    evidence.mkdir(parents=True, exist_ok=True)
    setup_path.write_text(
        json.dumps(setup, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (evidence / "room-created.json").write_text(
        json.dumps(created, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return setup


def wait_terminal(
    base: str,
    room_id: str,
    *,
    timeout_seconds: int = 3600,
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        room = http_json("GET", f"{base}/api/rooms/{room_id}")
        if str(room.get("status")) in TERMINAL_ROOM_STATUSES:
            return room
        time.sleep(1)
    raise RoomControlError(f"Room {room_id} did not reach terminal state")


def execute_task(
    *,
    run_id: str,
    task_id: str,
    base: str,
    database: Path,
) -> dict[str, Any]:
    setup = prepare_task_room(run_id=run_id, task_id=task_id, base=base)
    room_id = str(setup["room_id"])
    round_id = str(setup["round_id"])
    http_json(
        "POST",
        f"{base}/api/rooms/{room_id}/rounds/{round_id}/start",
        {},
    )
    final = wait_terminal(base, room_id)

    evidence = pbm.run_root(run_id) / task_id / "room"
    (evidence / "room-final.json").write_text(
        json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    export = http_json(
        "GET",
        f"{base}/api/rooms/{room_id}/export?format=json",
        timeout=60,
    )
    export_path = evidence / "room-export.json"
    export_path.write_text(
        json.dumps(export, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    result = pbm.room_complete(
        run_id=run_id,
        task_id=task_id,
        room_id=room_id,
        round_id=round_id,
        export_path=export_path,
        database=database,
    )
    result["schema"] = "pbm-result-v3"
    (evidence / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
