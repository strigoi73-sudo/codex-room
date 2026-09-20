from __future__ import annotations

import json
from pathlib import Path

from codex_room import pbm, pbm_onepaste
from codex_room import pbm_onepaste_room as room_control


def write_result(root: Path, task_id: str, arm: str) -> None:
    path = root / task_id / arm / "result.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")


def test_pbm_v3_inherits_v1_workload_and_is_current() -> None:
    v1 = pbm.load_manifest("v1")
    v3 = pbm.load_manifest("v3")

    assert pbm.current_version() == "v3"
    assert v3["schema_version"] == 3
    assert v3["asset_version"] == "v1"
    assert [task["id"] for task in v3["tasks"]] == [
        task["id"] for task in v1["tasks"]
    ]
    assert v3["one_paste_protocol"]["desktop_initial_pastes"] == 1
    assert v3["one_paste_protocol"]["room_initial_pastes"] == 1
    assert v3["one_paste_protocol"]["desktop_cli_fallback"] is False


def test_v3_fingerprint_binds_controller_implementation() -> None:
    manifest = pbm.load_manifest("v3")
    implementation = manifest["implementation_files"]

    assert "codex_room/pbm_onepaste.py" in implementation
    assert "codex_room/pbm_onepaste_room.py" in implementation
    assert "codex_room/pbm_onepaste_server.py" in implementation
    assert pbm.benchmark_fingerprint("v3") != pbm.benchmark_fingerprint("v2")


def test_onepaste_sequence_preserves_alternating_arm_order(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(pbm, "OUTPUT_ROOT", tmp_path / "runs")
    run = pbm.new_run("pbm-v3-sequence", "v3")
    run_id = run["run_id"]
    root = Path(run["run_root"])

    first = pbm_onepaste.next_action(run_id, "desktop")
    room_wait = pbm_onepaste.next_action(run_id, "room")
    assert first["task_id"] == "t01-mechanical-change"
    assert first["action"] == "run_task"
    assert room_wait["action"] == "wait"

    write_result(root, "t01-mechanical-change", "desktop")
    room = pbm_onepaste.next_action(run_id, "room")
    assert room["task_id"] == "t01-mechanical-change"
    assert room["action"] == "run_task"

    write_result(root, "t01-mechanical-change", "room")
    second = pbm_onepaste.next_action(run_id, "room")
    desktop_wait = pbm_onepaste.next_action(run_id, "desktop")
    assert second["task_id"] == "t02-bounded-investigation"
    assert second["action"] == "run_task"
    assert desktop_wait["action"] == "wait"


def test_desktop_next_stages_only_one_active_task(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(pbm, "OUTPUT_ROOT", tmp_path / "runs")
    controller = tmp_path / "controller"
    monkeypatch.setattr(pbm_onepaste, "CONTROLLER_ROOT", controller)
    monkeypatch.setattr(pbm_onepaste, "ACTIVE_DIR", controller / "active")
    monkeypatch.setattr(
        pbm_onepaste,
        "ACTIVE_TASK_FILE",
        controller / "ACTIVE_TASK.md",
    )
    monkeypatch.setattr(
        pbm_onepaste,
        "capture_context",
        lambda run_id, label: None,
    )

    run = pbm.new_run("pbm-v3-stage", "v3")
    action = pbm_onepaste.desktop_next(run["run_id"])

    assert action["action"] == "run_task"
    assert action["task_id"] == "t01-mechanical-change"
    assert (controller / "ACTIVE_TASK.md").is_file()
    assert (controller / "active" / "workspace" / "settings.py").is_file()
    assert len(action["delegated_prompt"].encode("utf-8")) <= 1000
    assert not (controller / "active" / "graders").exists()


def test_room_controller_launcher_is_detached_and_coordination_only() -> None:
    launcher = room_control.controller_launcher_text()
    worker = room_control.controller_worker_text(
        "http://127.0.0.1:9999/room/run?token=test"
    )

    assert "Start-Process" in launcher
    assert "Start-Job" not in launcher
    assert "$WorkerArgument = '\"' + $Worker + '\"'" in launcher
    assert "'-File', $WorkerArgument" in launcher
    assert "does not solve benchmark tasks" in launcher
    assert "Invoke-RestMethod" in worker
    assert "-TimeoutSec 86400" in worker


def test_desktop_driver_requires_native_tasks_and_forbids_cli_fallback() -> None:
    driver = (
        pbm.PROJECT_ROOT / "pbm_desktop_controller" / "DRIVER.md"
    ).read_text(encoding="utf-8")

    assert "native fresh-task creation" in driver
    assert "Do not substitute Codex CLI" in driver
    assert "desktop-next" in driver
    assert "desktop-finish" in driver
    assert "finalize" in driver


def test_room_driver_is_coordination_only() -> None:
    driver = (
        pbm.version_root("v3") / "room-driver.md"
    ).read_text(encoding="utf-8")

    assert "coordination-only PBM controller" in driver
    assert "PBM_ROOM_CLIENT.ps1" in driver
    assert "Do not solve" in driver


def test_room_controller_enters_principal_wait_after_staging(
    monkeypatch,
    tmp_path: Path,
) -> None:
    version = tmp_path / "v3"
    version.mkdir()
    (version / "room-driver.md").write_text(
        "# test room driver\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "room-shared"
    captured: dict[str, object] = {}
    calls: list[tuple[str, str]] = []

    def fake_create_room(
        base: str,
        *,
        title: str,
        topic: str,
        max_turns: int,
    ) -> dict[str, object]:
        captured.update(
            base=base,
            title=title,
            topic=topic,
            max_turns=max_turns,
        )
        return {"id": "room-preflight", "active_round_id": "round-preflight"}

    def fake_http_json(
        method: str,
        url: str,
        payload: dict[str, object] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, object]:
        assert (workspace / "PBM_ROOM_DRIVER.md").is_file()
        assert (workspace / "PBM_ROOM_CLIENT.ps1").is_file()
        assert (workspace / "PBM_ROOM_WORKER.ps1").is_file()
        calls.append((method, url))
        return {"ok": True}

    monkeypatch.setattr(room_control, "create_room", fake_create_room)
    monkeypatch.setattr(
        room_control,
        "room_workspace",
        lambda room_id: workspace,
    )
    monkeypatch.setattr(pbm, "version_root", lambda version_name=None: version)
    monkeypatch.setattr(room_control, "http_json", fake_http_json)

    result = room_control.make_controller_room(
        base="http://127.0.0.1:8765",
        coordinator_url="http://127.0.0.1:9999",
        token="test-token",
    )

    assert "CONSULT_PRINCIPAL" in str(captured["topic"])
    assert result["room_id"] == "room-preflight"
    assert calls == [
        (
            "POST",
            "http://127.0.0.1:8765/api/rooms/room-preflight/"
            "rounds/round-preflight/start",
        )
    ]
