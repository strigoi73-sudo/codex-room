from __future__ import annotations

import json
import shutil
from pathlib import Path

from codex_room import pbm, pbm_context


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
        grade = pbm._run_grader(task["id"], workspace, "v1")

        assert isinstance(grade["pass"], bool)
        assert 0 <= grade["score"] <= 100
        assert isinstance(grade["checks"], list)
        assert grade["checks"]


def test_prepare_and_grade_mechanical_task(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pbm, "OUTPUT_ROOT", tmp_path / "runs")
    run = pbm.new_run("pbm-test", "v1")
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
    grade = pbm._run_grader("t01-mechanical-change", workspace, "v1")

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


def test_pbm_v2_inherits_frozen_v1_assets() -> None:
    v1 = pbm.load_manifest("v1")
    v2 = pbm.load_manifest("v2")

    assert v2["schema_version"] == 2
    assert v2["asset_version"] == "v1"
    assert [task["id"] for task in v2["tasks"]] == [task["id"] for task in v1["tasks"]]

    v1_task = pbm.task_info("t03-localized-bug", "v1")
    v2_task = pbm.task_info("t03-localized-bug", "v2")
    assert v2_task["asset_version"] == "v1"
    assert v2_task["prompt"] == v1_task["prompt"]
    assert pbm.benchmark_fingerprint("v2") != pbm.benchmark_fingerprint("v1")


def test_explicit_v1_and_v2_runs_keep_their_schema(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pbm, "OUTPUT_ROOT", tmp_path / "runs")

    v1 = pbm.new_run("pbm-v1-test", "v1")
    v2 = pbm.new_run("pbm-v2-test", "v2")

    assert v1["schema"] == "pbm-run-v1"
    assert v1["schema_version"] == 1
    assert v1["benchmark_version"] == "v1"
    assert v2["schema"] == "pbm-run-v2"
    assert v2["schema_version"] == 2
    assert v2["benchmark_version"] == "v2"


def test_context_sanitize_removes_identity_credentials_but_keeps_usage() -> None:
    source = {
        "email": "private@example.com",
        "accountId": "acct-secret",
        "accessToken": "secret-token",
        "totalTokens": 1234,
        "credits": {"remaining": 42},
        "nested": {"user_id": "private-user", "windowMinutes": 300},
    }

    sanitized = pbm_context.sanitize(source)

    assert "email" not in sanitized
    assert "accountId" not in sanitized
    assert "accessToken" not in sanitized
    assert "user_id" not in sanitized["nested"]
    assert sanitized["totalTokens"] == 1234
    assert sanitized["credits"]["remaining"] == 42
    assert sanitized["nested"]["windowMinutes"] == 300


def test_context_summary_surfaces_run_boundary_availability(tmp_path: Path) -> None:
    context = tmp_path / "context"
    context.mkdir()
    common = {
        "repository": {"head": "abc123", "working_tree_clean": True},
        "environment": {"openai_codex_package_version": "0.154.0"},
        "native_codex": {
            "account": {"data": {"runtime": {"name": "codex", "version": "0.154.0"}}},
            "rate_limits": {"status": "available"},
            "account_usage": {"status": "available"},
        },
    }
    for label, captured_at in (
        ("run-start", "2026-09-20T12:00:00+00:00"),
        ("task-t01-mechanical-change-pre", "2026-09-20T12:00:01+00:00"),
        ("run-end", "2026-09-20T13:00:00+00:00"),
    ):
        payload = {**common, "label": label, "captured_at": captured_at}
        (context / f"{label}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    summary = pbm_context.context_summary(tmp_path)

    assert summary["snapshot_count"] == 3
    assert summary["run_start"]["rate_limits_status"] == "available"
    assert summary["run_start"]["account_usage_status"] == "available"
    assert summary["run_end"]["repository_head"] == "abc123"


def test_current_pbm_is_v2() -> None:
    assert pbm.current_version() == "v2"
    assert pbm.load_manifest()["schema_version"] == 2
