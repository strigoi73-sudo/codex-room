from pathlib import Path
import shutil
import subprocess



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


def test_feature_verifier_owns_exact_head_operator_guardrails() -> None:
    verifier = (ROOT / "verify-feature.ps1").read_text(encoding="utf-8")

    assert "Kill-Codex-Room.bat" in verifier
    assert "verify-fast.cmd" in verifier
    assert "verify-full.cmd" in verifier
    assert '$verifyCommandName = if ($Mode -eq "Full") {' in verifier
    assert "$verifyCommand = Join-Path $repoRoot $verifyCommandName" in verifier
    assert "$verifyCommand = Join-Path $repoRoot (" not in verifier
    assert "git fetch origin --prune" in verifier
    assert "git switch --detach $Head" in verifier
    assert "git diff --check" in verifier
    assert "FocusedTests" in verifier
    assert "RESTORE" in verifier
    assert not any(
        line.strip().lower().startswith("exit ")
        for line in verifier.splitlines()
    )

def test_phase5_runner_owns_mechanical_operator_guardrails() -> None:
    runner = (ROOT / "oub-v2-phase5.ps1").read_text(encoding="utf-8")

    assert "ExpectedHead" in runner
    assert '"prepare", "--task-id", $taskId, "--no-start"' in runner
    assert "No Desktop benchmark worker will be started." in runner
    assert "No Room Round will be started." in runner
    assert "Failed to start the systemd user session" in runner
    assert "wrapper PID" in runner
    assert "ps -eo pid,ppid,etime,stat,pcpu,pmem,args" not in runner
    assert "$process.Kill($true)" in runner
    assert "Attempting fail-safe abort" in runner
    assert "I-028 PHASE 5 REQUESTED TASK SET: PASS" in runner
    assert "all_frozen_tasks_covered_by_this_run" in runner
    assert not any(
        line.strip().lower().startswith("exit ")
        for line in runner.splitlines()
    )


def test_phase5_runner_parses_as_powershell() -> None:
    if shutil.which("powershell.exe") is None:
        return

    script = ROOT / "oub-v2-phase5.ps1"
    escaped = str(script).replace("'", "''")
    command = (
        "$tokens = $null; $errors = $null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{escaped}', "
        "[ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { "
        "$errors | ForEach-Object { Write-Error $_.Message }; exit 1 }"
    )

    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
