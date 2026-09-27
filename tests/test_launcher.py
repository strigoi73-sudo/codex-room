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


def test_launcher_forwards_optional_server_arguments() -> None:
    launcher = (ROOT / "Start-Codex-Room.cmd").read_text(encoding="utf-8")
    assert '".venv\\Scripts\\python.exe" -m codex_room %*' in launcher


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


def test_maintenance_wrapper_uses_repository_virtual_environment() -> None:
    wrapper = (ROOT / "codex-room-maint.cmd").read_text(encoding="utf-8")
    assert ".venv\\Scripts\\python.exe" in wrapper
    assert "-m codex_room.maintenance %*" in wrapper
    assert "exit /b %ERRORLEVEL%" in wrapper


def test_restart_script_preserves_browser_and_restarts_without_new_tab() -> None:
    restart = (ROOT / "Restart-Codex-Room.bat").read_text(encoding="utf-8")

    assert "MainWindowTitle" not in restart
    assert "CloseMainWindow" not in restart
    assert "Kill-Codex-Room.bat" in restart
    assert "timeout /t 5 /nobreak" in restart
    assert 'Start-Codex-Room.cmd" --no-browser' in restart
    assert restart.index("Kill-Codex-Room.bat") < restart.index("timeout /t 5 /nobreak")
    assert restart.index("timeout /t 5 /nobreak") < restart.index("Start-Codex-Room.cmd")


def test_restart_script_waits_for_api_readiness_before_success() -> None:
    restart = (ROOT / "Restart-Codex-Room.bat").read_text(encoding="utf-8")

    assert "Waiting for Codex Room API readiness..." in restart
    assert "http://127.0.0.1:8765/api/health" in restart
    assert "Invoke-RestMethod" in restart
    assert "$health.ok -eq $true" in restart
    assert "AddSeconds(30)" in restart
    assert "Codex Room API is ready." in restart
    assert "Restart failed because Codex Room API readiness was not confirmed." in restart
    assert restart.count("Kill-Codex-Room.bat") >= 2


def test_local_verifier_uses_inherited_wsl_working_directory() -> None:
    verifier = (ROOT / "verify-local.ps1").read_text(encoding="utf-8")

    assert "wslpath" not in verifier
    assert 'repo="$(pwd -P)"' in verifier
    assert '$startInfo.WorkingDirectory = $repoRoot' in verifier
    assert '$startInfo.RedirectStandardInput = $true' in verifier
    assert '$startInfo.Arguments =' in verifier
    assert '.ArgumentList' not in verifier
    assert '$process.StandardInput.Write($bash)' in verifier
    assert '$process.StandardInput.Close()' in verifier
    assert '$global:LASTEXITCODE = $process.ExitCode' in verifier
    assert '$bash | & $wsl' not in verifier
    assert "CODEX_ROOM_REPO=" not in verifier
    assert "WriteAllText" not in verifier
