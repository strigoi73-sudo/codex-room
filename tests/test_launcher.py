from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_launcher_uses_sdk_pinned_runtime_by_default() -> None:
    launcher = (ROOT / "Start-Codex-Room.cmd").read_text(encoding="utf-8")
    assert "OpenAI\\Codex\\bin" not in launcher
    assert "if defined CODEX_ROOM_CODEX_BIN" in launcher
    assert "Using SDK-pinned Codex runtime." in launcher
    assert "Using Codex runtime override:" in launcher
