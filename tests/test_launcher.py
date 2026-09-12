from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_launcher_uses_sdk_pinned_runtime_by_default() -> None:
    launcher = (ROOT / "Start-Codex-Room.cmd").read_text(encoding="utf-8")
    assert "OpenAI\\Codex\\bin" not in launcher
    assert "if defined CODEX_ROOM_CODEX_BIN" in launcher
    assert "Using SDK-pinned Codex runtime." in launcher
    assert "Using Codex runtime override:" in launcher


def test_launcher_exposes_room_capability_wrapper_to_agent_shells() -> None:
    launcher = (ROOT / "Start-Codex-Room.cmd").read_text(encoding="utf-8")
    wrapper = (ROOT / "codex-room-cap.cmd").read_text(encoding="utf-8")
    assert 'set "PATH=%CD%;%PATH%"' in launcher
    assert ".venv\\Scripts\\python.exe" in wrapper
    assert "-m codex_room.capabilities %*" in wrapper


def test_launcher_marks_dedicated_server_console() -> None:
    launcher = (ROOT / "Start-Codex-Room.cmd").read_text(encoding="utf-8")
    assert "title Codex Room Server" in launcher


def test_kill_script_targets_server_tree_and_dedicated_launcher_console() -> None:
    killer = (ROOT / "Kill-Codex-Room.bat").read_text(encoding="utf-8")

    assert "Start-Codex-Room.cmd" in killer
    assert "Codex Room Server" in killer
    assert "MainWindowTitle" in killer
    assert "ParentProcessId -eq $processId" in killer
    assert "Stop-Process -Id $process.ProcessId -Force" in killer
    assert "Get-Process -Id @($ordered.ProcessId)" in killer
    assert "shutdown left process ID(s)" in killer


def test_kill_script_does_not_pause_after_successful_shutdown() -> None:
    killer = (ROOT / "Kill-Codex-Room.bat").read_text(encoding="utf-8")

    assert 'if /I not "%~1"=="--dry-run" pause' not in killer
    assert "Failed to stop Codex Room cleanly." in killer
