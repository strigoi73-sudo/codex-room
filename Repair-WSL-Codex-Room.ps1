[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "=== Codex Room WSL systemd repair ==="
Write-Host "Codex Room does not require systemd in its Ubuntu WSL environment."
Write-Host "This procedure backs up /etc/wsl.conf, sets boot.systemd=false, restarts WSL, and verifies startup."
Write-Host ""

$wslVersion = @(wsl.exe --version 2>&1)
$wslVersionExit = $LASTEXITCODE
if ($wslVersionExit -eq 0) {
    $wslVersion | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "WARNING: wsl.exe --version returned exit code $wslVersionExit."
}

$python = @'
from pathlib import Path
from datetime import datetime, timezone
import shutil

path = Path("/etc/wsl.conf")
text = path.read_text(encoding="utf-8") if path.exists() else ""
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

if path.exists():
    backup = Path(f"/etc/wsl.conf.codex-room-backup-{stamp}")
    shutil.copy2(path, backup)
    print(f"backup={backup}")
else:
    print("backup=(none; /etc/wsl.conf did not exist)")

lines = text.splitlines()
out = []
in_boot = False
boot_seen = False
systemd_written = False

for line in lines:
    stripped = line.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        if in_boot and not systemd_written:
            out.append("systemd=false")
            systemd_written = True
        in_boot = stripped.lower() == "[boot]"
        if in_boot:
            boot_seen = True
            systemd_written = False
        out.append(line)
        continue

    if in_boot and "=" in stripped and stripped.split("=", 1)[0].strip().lower() == "systemd":
        if not systemd_written:
            out.append("systemd=false")
            systemd_written = True
        continue

    out.append(line)

if in_boot and not systemd_written:
    out.append("systemd=false")
    systemd_written = True

if not boot_seen:
    if out and out[-1] != "":
        out.append("")
    out.extend(["[boot]", "systemd=false"])

path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
print("updated=/etc/wsl.conf")
print(path.read_text(encoding="utf-8"), end="")
'@

$repairOutput = @(wsl.exe -u root -- python3 -c $python 2>&1)
$repairExit = $LASTEXITCODE

if ($repairExit -ne 0) {
    Write-Host "ERROR: Could not update /etc/wsl.conf. Exit code: $repairExit"
    $repairOutput | ForEach-Object { Write-Host $_ }
    return
}

$repairOutput |
    Where-Object { $_ -notmatch "^wsl: Failed to start the systemd user session" } |
    ForEach-Object { Write-Host $_ }

Write-Host ""
Write-Host "Restarting WSL so the new init setting takes effect..."
wsl.exe --shutdown
$shutdownExit = $LASTEXITCODE
if ($shutdownExit -ne 0) {
    Write-Host "ERROR: wsl.exe --shutdown failed with exit code $shutdownExit."
    return
}

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=== Post-repair startup probe ==="
$probeOutput = @(wsl.exe -e sh -c 'printf "pid1=%s\n" "$(ps -p 1 -o comm=)"; printf "user=%s\n" "$(id -un)"' 2>&1)
$probeExit = $LASTEXITCODE
$probeText = $probeOutput -join [Environment]::NewLine
$warningStillPresent = $probeText -match "Failed to start the systemd user session"

$probeOutput | ForEach-Object { Write-Host $_ }

if ($probeExit -ne 0) {
    Write-Host ""
    Write-Host "ERROR: WSL startup probe failed with exit code $probeExit."
    return
}

if ($warningStillPresent) {
    Write-Host ""
    Write-Host "ERROR: The systemd user-session warning is still present after disabling systemd."
    Write-Host "Do not continue Phase 3 yet."
    return
}

Write-Host ""
Write-Host "=== Effective /etc/wsl.conf ==="
$configOutput = @(wsl.exe -u root -- cat /etc/wsl.conf 2>&1)
$configExit = $LASTEXITCODE
$configOutput | ForEach-Object { Write-Host $_ }

if ($configExit -ne 0) {
    Write-Host "ERROR: Could not read /etc/wsl.conf after repair."
    return
}

Write-Host ""
Write-Host "WSL systemd repair: PASS"
