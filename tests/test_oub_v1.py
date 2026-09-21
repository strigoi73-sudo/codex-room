from __future__ import annotations

import json
from pathlib import Path

from codex_room import oub_v1


def test_oub_v1_harness_audit_binds_frozen_o1_assets() -> None:
    result = oub_v1.audit_harness()

    assert result["ok"] is True
    assert result["benchmark_version"] == "v1"
    assert result["task_id"] == "o01-competing-root-causes"
    assert (
        result["benchmark_fingerprint"]
        == "d6ec60fca42c6dd436b15d4f8621bb711056b1da5aa93f5a6ecaee2188ba4835"
    )
    assert result["asset_audit"]["reference_score"] == 100
    assert result["asset_audit"]["target_runtime_minutes"] == 12
    assert result["safety_timeout_seconds"] == 1800


def test_oub_v1_fixture_integrity_detects_mutation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    expected = oub_v1._prepare_workspace(workspace)

    ok, changed = oub_v1._fixture_unchanged(workspace, expected)
    assert ok is True
    assert changed == []

    target = workspace / "logs" / "worker.log"
    target.write_text(
        target.read_text(encoding="utf-8") + "tampered\n",
        encoding="utf-8",
    )

    ok, changed = oub_v1._fixture_unchanged(workspace, expected)
    assert ok is False
    assert changed == ["logs/worker.log"]


def test_oub_v1_room_payload_preserves_naturalistic_orchestration() -> None:
    payload = oub_v1._room_payload("oub-test")

    assert payload["starting_agent"] == "agent_c"
    assert payload["required_contributors"] == []
    assert payload["completion_policy"] == "auto_settle"
    assert payload["work_model_version"] == 2
    assert payload["provider_context_mode"] == "assignment_thread"
    assert payload["max_turns"] == 40
    assert "Agent A" not in payload["topic"]
    assert "Agent B" not in payload["topic"]
    assert "delegate" not in payload["topic"].lower()


def test_oub_v1_comparison_keeps_quality_and_cost_separate(
    tmp_path: Path, monkeypatch
) -> None:
    desktop_path = tmp_path / "desktop.json"
    room_path = tmp_path / "room.json"

    desktop_path.write_text(
        json.dumps(
            {
                "classification": "VALID",
                "benchmark_fingerprint": "fp",
                "quality": {"pass": False, "score": 85},
                "usage": {
                    "total_tokens": 200,
                    "thread_count": 1,
                    "descendant_count": 0,
                    "tool_calls": 4,
                },
                "duration_seconds": 100,
            }
        ),
        encoding="utf-8",
    )
    room_path.write_text(
        json.dumps(
            {
                "classification": "VALID",
                "benchmark_fingerprint": "fp",
                "quality": {"pass": True, "score": 100},
                "usage": {
                    "total_tokens": 300,
                    "execution_count": 3,
                    "peer_invocations": 2,
                    "tool_calls": 6,
                },
                "duration_seconds": 120,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        oub_v1,
        "_result_path",
        lambda _state, arm: desktop_path if arm == "desktop" else room_path,
    )

    result = oub_v1._comparison(
        {
            "run_id": "oub-test",
            "benchmark_fingerprint": "fp",
        }
    )

    assert result["comparable"] is True
    assert result["room_minus_desktop_score"] == 15
    assert result["room_to_desktop_total_token_ratio"] == 1.5
    assert result["room_to_desktop_duration_ratio"] == 1.2
    assert result["desktop"]["descendant_count"] == 0
    assert result["room"]["peer_invocations"] == 2
    assert "winner" in result["interpretation_note"].lower()


def test_oub_v1_required_artifacts_are_bounded(tmp_path: Path) -> None:
    assert oub_v1._required_artifacts_present(tmp_path) is False

    (tmp_path / "FINDINGS.json").write_text("{}\n", encoding="utf-8")
    assert oub_v1._required_artifacts_present(tmp_path) is False

    (tmp_path / "INCIDENT_REPORT.md").write_text("# report\n", encoding="utf-8")
    assert oub_v1._required_artifacts_present(tmp_path) is True
