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
