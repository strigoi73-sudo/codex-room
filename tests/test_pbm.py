from __future__ import annotations

import json
import shutil
from pathlib import Path

from codex_room import pbm


def test_pbm_v1_manifest_has_eight_unique_tasks() -> None:
    manifest = pbm.load_manifest("v1")
    ids = [task["id"] for task in manifest["tasks"]]

    assert len(ids) == 8
    assert len(set(ids)) == 8
    assert manifest["mode"] == "naturalistic"


def test_every_pbm_v1_grader_executes_on_untouched_fixture(tmp_path: Path) -> None:
    manifest = pbm.load_manifest("v1")
    root = pbm.version_root("v1")

    for task in manifest["tasks"]:
        workspace = tmp_path / task["id"]
        shutil.copytree(root / task["fixture_dir"], workspace)
        grade = pbm._run_grader(task["id"], workspace)

        assert isinstance(grade["pass"], bool)
        assert 0 <= grade["score"] <= 100
        assert isinstance(grade["checks"], list)
        assert grade["checks"]


def test_prepare_and_grade_mechanical_task(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pbm, "OUTPUT_ROOT", tmp_path / "runs")
    run = pbm.new_run("pbm-test")
    evidence = Path(run["run_root"]) / "t01-mechanical-change" / "desktop"
    workspace = evidence / "workspace"

    prepared = pbm.prepare_task(
        run_id="pbm-test",
        task_id="t01-mechanical-change",
        arm="desktop",
        workspace=workspace,
        evidence_dir=evidence,
    )

    settings = workspace / "settings.py"
    settings.write_text(
        settings.read_text(encoding="utf-8").replace(
            "DEFAULT_RETRY_LIMIT = 3", "DEFAULT_RETRY_LIMIT = 5"
        ),
        encoding="utf-8",
    )
    grade = pbm._run_grader("t01-mechanical-change", workspace)

    assert prepared["benchmark_version"] == "v1"
    assert grade["pass"] is True
    assert grade["score"] == 100


def test_room_export_economics_aggregate() -> None:
    export = {
        "rounds": [
            {
                "id": "round-1",
                "status": "finished",
                "close_reason": "transaction_settled",
                "started_at": "2026-09-20T12:00:00+00:00",
                "ended_at": "2026-09-20T12:00:05+00:00",
                "events": [
                    {
                        "event_type": "execution_economics",
                        "source": "agent_c",
                        "metadata": {
                            "usage_delta_status": "first_execution",
                            "usage_delta": {
                                "input_tokens": 80,
                                "cached_input_tokens": 60,
                                "output_tokens": 20,
                                "reasoning_output_tokens": 5,
                                "total_tokens": 100,
                            },
                            "tool_calls": 1,
                            "failed_tool_calls": 0,
                            "peer_invocations": 1,
                        },
                    },
                    {
                        "event_type": "execution_economics",
                        "source": "agent_a",
                        "metadata": {
                            "usage_delta_status": "first_execution",
                            "usage_delta": {
                                "input_tokens": 120,
                                "cached_input_tokens": 90,
                                "output_tokens": 30,
                                "reasoning_output_tokens": 8,
                                "total_tokens": 150,
                            },
                            "tool_calls": 2,
                            "failed_tool_calls": 1,
                            "peer_invocations": 0,
                        },
                    },
                ],
            }
        ]
    }

    result = pbm.aggregate_room_export(export, "round-1")

    assert result["usage_complete"] is True
    assert result["total"]["total_tokens"] == 250
    assert result["tool_calls"] == 3
    assert result["failed_tool_calls"] == 1
    assert result["executions_by_agent"] == {"agent_a": 1, "agent_c": 1}
    assert result["duration_seconds"] == 5.0
