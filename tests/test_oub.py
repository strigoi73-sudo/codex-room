from __future__ import annotations

import json
from pathlib import Path

from codex_room import oub


def test_oub_v1_reference_audit_is_full_credit_and_bounded() -> None:
    result = oub.audit_assets("v1")
    assert result["ok"] is True
    assert result["task_id"] == "o01-competing-root-causes"
    assert result["reference_score"] == 100
    assert result["target_runtime_minutes"] == 12
    assert result["fixture_file_count"] == 10
    assert result["fixture_bytes"] <= 30_000
    assert len(result["benchmark_fingerprint"]) == 64


def test_o01_wrong_root_cause_loses_material_credit(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    oub.populate_reference_workspace(workspace)

    findings_path = workspace / "FINDINGS.json"
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    findings["primary_cause"] = "DB_POOL_EXHAUSTION"
    findings_path.write_text(
        json.dumps(findings, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = oub.grade_workspace(workspace)
    assert result["pass"] is False
    assert result["score"] == 85
    primary = next(item for item in result["checks"] if item["name"] == "primary_cause")
    assert primary["ok"] is False
    assert primary["awarded"] == 0


def test_o01_requires_falsification_not_only_correct_primary_cause(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    oub.populate_reference_workspace(workspace)

    findings_path = workspace / "FINDINGS.json"
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    findings["rejected_hypotheses"] = []
    findings_path.write_text(
        json.dumps(findings, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = oub.grade_workspace(workspace)
    assert result["pass"] is False
    assert result["score"] == 85
    failed = {
        item["name"]
        for item in result["checks"]
        if item["ok"] is False
    }
    assert failed == {
        "reject_duplicate_ingress",
        "reject_concurrent_claim",
        "reject_db_pool",
    }
