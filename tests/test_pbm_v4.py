from __future__ import annotations

from codex_room import pbm, pbm_v4


def test_v4_manifest_is_one_integrated_independent_mission() -> None:
    manifest = pbm.load_manifest("v4")

    assert manifest["schema_version"] == 4
    assert [item["id"] for item in manifest["tasks"]] == [
        "m01-integrated-mission"
    ]
    assert manifest["v4_protocol"]["desktop_principal_pastes"] == 1
    assert manifest["v4_protocol"]["room_principal_pastes"] == 1
    assert manifest["v4_protocol"]["cross_platform_coordination"] is False
    assert manifest["v4_protocol"]["same_fixture"] is True
    assert manifest["v4_protocol"]["same_grader"] is True
    assert manifest["v4_protocol"]["result_classifications"] == [
        "VALID",
        "INVALID",
        "FAILED",
    ]


def test_v4_reference_solution_proves_satisfiability_and_grader_coverage() -> None:
    result = pbm_v4.audit_assets()

    assert result["ok"] is True
    assert result["benchmark_version"] == "v4"
    assert result["reference_score"] == 100
    assert result["coverage_requirements"] == pbm.load_manifest("v4")[
        "coverage_requirements"
    ]


def test_v4_frozen_paste_matches_task_prompt() -> None:
    prompt = (
        pbm.version_root("v4")
        / "prompts"
        / "m01-integrated-mission.txt"
    ).read_text(encoding="utf-8").strip()

    assert prompt == pbm_v4.PASTE


def test_v4_room_intervention_detection_is_fail_closed() -> None:
    round_item = {
        "starting_agent": "agent_c",
        "work_model_version": 2,
        "provider_context_mode": "assignment_thread",
        "events": [
            {
                "event_type": "principal_message",
                "metadata": {"principal_channel": True},
            },
            {"event_type": "observer_message", "metadata": {}},
            {"event_type": "principal_reply", "metadata": {}},
        ],
    }

    reasons = pbm_v4.room_intervention_reasons(round_item)

    assert "Agent C requested substantive principal consultation" in reasons
    assert "observer message occurred during measured Room work" in reasons
    assert "principal reply occurred during measured Room work" in reasons
    assert pbm_v4._classification(reasons, []) == "INVALID"


def test_v4_failed_and_valid_classification_are_distinct_from_quality() -> None:
    assert pbm_v4._classification([], ["runtime failed"]) == "FAILED"
    assert pbm_v4._classification([], []) == "VALID"
    assert pbm_v4._classification(["human intervention"], ["runtime failed"]) == "INVALID"


def test_v4_wrapper_preserves_principal_shell_and_captures_native_exit() -> None:
    wrapper = (pbm.PROJECT_ROOT / "pbm-v4.ps1").read_text(encoding="utf-8")

    assert "Push-Location $RepoRoot" in wrapper
    assert "$pbmExit = $LASTEXITCODE" in wrapper
    assert "finally {" in wrapper
    assert "Pop-Location" in wrapper
    assert "exit $pbmExit" not in wrapper


def test_v4_readme_keeps_current_promotion_explicit() -> None:
    readme = (pbm.version_root("v4") / "README.md").read_text(encoding="utf-8")

    assert "fresh top-level native Codex Desktop task" in readme
    assert "Click **New round**" in readme
    assert "Do not send observer messages" in readme
    assert "CURRENT" in readme
    assert "remains unchanged" in readme
