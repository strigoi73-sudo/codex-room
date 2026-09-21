from __future__ import annotations

import json

from codex_room import pbm, pbm_v4, pbm_v4_canary


VERIFIED_V4_FINGERPRINT = "fc505df8c0578308f594e20c27d5a5e0ce68fa078a7c7c5935abc211550bec93"


def test_canary_uses_exact_v4_one_paste_prompt() -> None:
    assert pbm_v4_canary.PASTE == pbm_v4.PASTE
    assert pbm_v4_canary.PASTE == (
        "Read BENCHMARK.md and execute it exactly. "
        "Do not ask me questions. When complete, stop."
    )


def test_canary_asset_is_bounded_and_unambiguous() -> None:
    text = (pbm_v4_canary.CANARY_ROOT / "BENCHMARK.md").read_text(encoding="utf-8")

    assert "bounded protocol canary" in text
    assert "CANARY_COMPLETE.json" in text
    assert "Do not ask the principal a question." in text
    assert "Do not modify any other file." in text


def test_canary_marker_validation_is_exact(tmp_path) -> None:
    marker = tmp_path / "CANARY_COMPLETE.json"
    marker.write_text(
        json.dumps(pbm_v4_canary.EXPECTED_MARKER, indent=2) + "\n",
        encoding="utf-8",
    )
    assert pbm_v4_canary._marker_ok(tmp_path) is True

    marker.write_text('{"status":"complete"}\n', encoding="utf-8")
    assert pbm_v4_canary._marker_ok(tmp_path) is False


def test_canary_files_do_not_change_verified_v4_benchmark_fingerprint() -> None:
    assert pbm.benchmark_fingerprint("v4") == VERIFIED_V4_FINGERPRINT


def test_canary_wrapper_preserves_principal_shell_and_captures_native_exit() -> None:
    wrapper = (pbm.PROJECT_ROOT / "pbm-v4-canary.ps1").read_text(encoding="utf-8")

    assert "Push-Location $RepoRoot" in wrapper
    assert "$canaryExit = $LASTEXITCODE" in wrapper
    assert "finally {" in wrapper
    assert "Pop-Location" in wrapper
    assert "exit $canaryExit" not in wrapper


def test_canary_pair_verification_requires_both_valid_results(tmp_path, monkeypatch) -> None:
    run_id = "pbm-v4-canary-test"
    root = tmp_path / run_id
    root.mkdir()
    monkeypatch.setattr(pbm_v4_canary, "OUTPUT_ROOT", tmp_path)

    desktop = {
        "classification": "VALID",
        "benchmark_fingerprint": VERIFIED_V4_FINGERPRINT,
    }
    room = {
        "classification": "VALID",
        "benchmark_fingerprint": VERIFIED_V4_FINGERPRINT,
    }
    (root / "desktop-result.json").write_text(
        json.dumps(desktop), encoding="utf-8"
    )
    (root / "room-result.json").write_text(
        json.dumps(room), encoding="utf-8"
    )

    result = pbm_v4_canary.verify_pair(run_id)

    assert result["passed"] is True
    assert result["same_fingerprint"] is True

    room["classification"] = "INVALID"
    (root / "room-result.json").write_text(
        json.dumps(room), encoding="utf-8"
    )
    result = pbm_v4_canary.verify_pair(run_id)
    assert result["passed"] is False
