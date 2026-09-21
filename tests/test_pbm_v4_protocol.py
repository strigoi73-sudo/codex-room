from __future__ import annotations

import json
from pathlib import Path

from codex_room import pbm, pbm_v4, pbm_v4_protocol


def test_protocol_runner_uses_one_shared_active_pair(tmp_path, monkeypatch) -> None:
    active = tmp_path / "active.json"
    monkeypatch.setattr(pbm_v4_protocol, "ACTIVE_POINTER", active)

    state_root = tmp_path / "run"

    monkeypatch.setattr(
        pbm_v4_protocol,
        "_state_path",
        lambda _run_id: state_root / "v4-protocol" / "state.json",
    )

    state = {
        "run_id": "pbm-v4-canary-protocol-test",
        "mode": "canary",
        "benchmark_fingerprint": "fingerprint",
        "repo": {"head": "abc"},
        "complete": False,
        "aborted": False,
    }
    pbm_v4_protocol._write_json(
        state_root / "v4-protocol" / "state.json",
        state,
    )
    pbm_v4_protocol._write_json(
        active,
        {
            "run_id": state["run_id"],
            "mode": "canary",
            "benchmark_fingerprint": "fingerprint",
            "repo_head": "abc",
        },
    )

    pointer = pbm_v4_protocol._active_run()

    assert pointer is not None
    assert pointer["run_id"] == state["run_id"]


def test_desktop_adapter_requires_native_child_and_no_room_wait() -> None:
    text = (
        pbm.PROJECT_ROOT / "pbm_desktop_controller" / "V4_PROTOCOL.md"
    ).read_text(encoding="utf-8")

    assert "native Codex fresh-task creation mechanism" in text
    assert "desktop-monitor-start" in text
    assert "Do not poll or wait for the measured child" in text
    assert "Do not substitute Codex CLI" in text
    assert "Do not wait for Room" in text
    assert "Do not ask the principal to run PBM preparation" in text


def test_room_adapter_launches_detached_worker_and_does_not_poll() -> None:
    text = (pbm.version_root("v4") / "ROOM_PROTOCOL.md").read_text(
        encoding="utf-8"
    )

    assert "deterministic PBM v4 Room worker" in text
    assert "do not poll the measured Room" in text
    assert "Do not invoke A or B" in text


def test_protocol_wrappers_preserve_shell() -> None:
    for path in (
        pbm.PROJECT_ROOT / "pbm-v4-protocol.ps1",
        pbm.PROJECT_ROOT / "pbm_desktop_controller" / "PBM-V4.ps1",
    ):
        text = path.read_text(encoding="utf-8")
        assert "$LASTEXITCODE" in text
        assert "finally {" in text
        assert "Pop-Location" in text
        assert "exit $protocolExit" not in text


def test_canary_and_benchmark_share_frozen_measured_prompt() -> None:
    assert pbm_v4_protocol.PASTE == pbm_v4.PASTE


def test_manifest_binds_protocol_implementation_files() -> None:
    files = set(pbm.load_manifest("v4")["implementation_files"])

    assert "codex_room/pbm_v4_protocol.py" in files
    assert "pbm-v4-protocol.ps1" in files
    assert "pbm_desktop_controller/V4_PROTOCOL.md" in files
    assert "benchmarks/pbm/v4/PROTOCOL.md" not in files
    assert "benchmarks/pbm/v4/ROOM_PROTOCOL.md" not in files
    assert (pbm.version_root("v4") / "PROTOCOL.md").is_file()
    assert (pbm.version_root("v4") / "ROOM_PROTOCOL.md").is_file()


def test_worker_pid_update_does_not_overwrite_terminal_platform_state(
    tmp_path, monkeypatch
) -> None:
    run_id = "pbm-v4-canary-protocol-worker-race"
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(pbm_v4_protocol, "PROTOCOL_LOCK_DIR", tmp_path / "lock")
    monkeypatch.setattr(
        pbm_v4_protocol,
        "_state_path",
        lambda _run_id: state_path,
    )
    pbm_v4_protocol._write_json(
        state_path,
        {
            "run_id": run_id,
            "mode": "canary",
            "desktop": {
                "status": "complete",
                "classification": "VALID",
            },
            "room": None,
        },
    )

    state = pbm_v4_protocol._mark_platform_worker_started(
        run_id,
        "desktop",
        1234,
    )

    assert state["desktop"]["status"] == "complete"
    assert state["desktop"]["classification"] == "VALID"
    assert state["desktop"]["worker_pid"] == 1234


def test_canary_fixture_has_explicit_protocol_identity() -> None:
    fingerprint = pbm_v4_protocol._tree_fingerprint(
        pbm_v4_protocol.pbm_v4_canary.CANARY_ROOT
    )

    assert len(fingerprint) == 64
    assert fingerprint != pbm.benchmark_fingerprint("v4")

def test_desktop_native_delegation_expects_no_child_user_message() -> None:
    assert pbm_v4_protocol._desktop_intervention_reasons([]) == []


def test_desktop_child_user_message_is_post_launch_intervention() -> None:
    assert pbm_v4_protocol._desktop_intervention_reasons(["follow-up guidance"]) == [
        "Desktop measured child received post-launch user guidance: observed 1 user message(s)"
    ]

def test_battery_task_quality_reports_each_task_without_token_guessing() -> None:
    result = {
        "quality": {
            "checks": [
                {"name": task_id, "ok": True, "score": 100}
                for task_id in pbm_v4.BATTERY_TASK_IDS
            ]
        }
    }

    summary = pbm_v4_protocol._battery_task_quality(result)

    assert list(summary) == list(pbm_v4.BATTERY_TASK_IDS)
    assert all(item == {"pass": True, "score": 100} for item in summary.values())

def test_status_recovers_ready_unfinalized_pair(tmp_path, monkeypatch) -> None:
    run_id = "pbm-v4-canary-protocol-finalization-recovery"
    state_path = tmp_path / "state.json"
    desktop_result = tmp_path / "desktop-result.json"
    room_result = tmp_path / "room-result.json"

    monkeypatch.setattr(
        pbm_v4_protocol,
        "_state_path",
        lambda _run_id: state_path,
    )
    monkeypatch.setattr(
        pbm_v4_protocol,
        "_result_path",
        lambda _state, arm: desktop_result if arm == "desktop" else room_result,
    )

    pbm_v4_protocol._write_json(
        state_path,
        {
            "run_id": run_id,
            "mode": "canary",
            "benchmark_fingerprint": "benchmark",
            "canary_fingerprint": "canary",
            "desktop": {"status": "complete", "classification": "VALID"},
            "room": {"status": "complete", "classification": "VALID"},
            "complete": False,
            "aborted": False,
        },
    )
    pbm_v4_protocol._write_json(desktop_result, {"classification": "VALID"})
    pbm_v4_protocol._write_json(room_result, {"classification": "VALID"})

    finalized = []

    def fake_finalize(candidate_run_id):
        finalized.append(candidate_run_id)
        state = pbm_v4_protocol._read_json(state_path)
        state["complete"] = True
        state["comparison"] = {"comparable": True}
        pbm_v4_protocol._write_json(state_path, state)
        return {"run_id": candidate_run_id, "complete": True}

    monkeypatch.setattr(pbm_v4_protocol, "_finalize_if_ready", fake_finalize)

    result = pbm_v4_protocol.status(run_id)

    assert finalized == [run_id]
    assert result["complete"] is True
    assert result["active"] is False
    assert result["comparison"] == {"comparable": True}


def test_status_does_not_finalize_without_both_results(tmp_path, monkeypatch) -> None:
    run_id = "pbm-v4-canary-protocol-not-ready"
    state_path = tmp_path / "state.json"
    desktop_result = tmp_path / "desktop-result.json"
    room_result = tmp_path / "room-result.json"

    monkeypatch.setattr(
        pbm_v4_protocol,
        "_state_path",
        lambda _run_id: state_path,
    )
    monkeypatch.setattr(
        pbm_v4_protocol,
        "_result_path",
        lambda _state, arm: desktop_result if arm == "desktop" else room_result,
    )
    pbm_v4_protocol._write_json(
        state_path,
        {
            "run_id": run_id,
            "mode": "canary",
            "benchmark_fingerprint": "benchmark",
            "canary_fingerprint": "canary",
            "desktop": {"status": "complete", "classification": "VALID"},
            "room": {"status": "running"},
            "complete": False,
            "aborted": False,
        },
    )
    pbm_v4_protocol._write_json(desktop_result, {"classification": "VALID"})

    def fail_finalize(_run_id):
        raise AssertionError("status must not finalize before both results exist")

    monkeypatch.setattr(pbm_v4_protocol, "_finalize_if_ready", fail_finalize)

    result = pbm_v4_protocol.status(run_id)

    assert result["complete"] is False
    assert result["active"] is True

def test_provisional_desktop_id_resolves_unique_persisted_rollout(
    tmp_path, monkeypatch
) -> None:
    rollout = tmp_path / "rollout-child.jsonl"
    rollout.write_text("{}\n", encoding="utf-8")

    def missing_exact(**_kwargs):
        raise pbm_v4_protocol.codex_usage.RolloutUsageError("thread not found")

    monkeypatch.setattr(
        pbm_v4_protocol.codex_usage,
        "select_rollout",
        missing_exact,
    )
    monkeypatch.setattr(
        pbm_v4_protocol,
        "_desktop_rollout_candidates_since",
        lambda _desktop: [(rollout, "019f-real-thread")],
    )

    observed_rollout, observed_thread = pbm_v4_protocol._resolve_desktop_rollout(
        {"prepared_at": "2026-09-21T03:19:13-05:00"},
        "client-new-thread:temporary",
    )

    assert observed_rollout == rollout
    assert observed_thread == "019f-real-thread"


def test_provisional_desktop_id_fails_closed_on_ambiguous_rollouts(
    tmp_path, monkeypatch
) -> None:
    first = tmp_path / "rollout-first.jsonl"
    second = tmp_path / "rollout-second.jsonl"
    first.write_text("{}\n", encoding="utf-8")
    second.write_text("{}\n", encoding="utf-8")

    def missing_exact(**_kwargs):
        raise pbm_v4_protocol.codex_usage.RolloutUsageError("thread not found")

    monkeypatch.setattr(
        pbm_v4_protocol.codex_usage,
        "select_rollout",
        missing_exact,
    )
    monkeypatch.setattr(
        pbm_v4_protocol,
        "_desktop_rollout_candidates_since",
        lambda _desktop: [
            (first, "019f-first"),
            (second, "019f-second"),
        ],
    )

    try:
        pbm_v4_protocol._resolve_desktop_rollout(
            {"prepared_at": "2026-09-21T03:19:13-05:00"},
            "client-new-thread:temporary",
        )
    except pbm_v4_protocol.PBMV4ProtocolError as exc:
        assert "ambiguous" in str(exc)
    else:
        raise AssertionError("ambiguous provisional Desktop mapping must fail closed")


def test_status_can_recover_provisional_desktop_before_pair_finalization(
    tmp_path, monkeypatch
) -> None:
    run_id = "pbm-v4-canary-protocol-provisional-recovery"
    state_path = tmp_path / "state.json"
    desktop_result = tmp_path / "desktop-result.json"
    room_result = tmp_path / "room-result.json"

    monkeypatch.setattr(
        pbm_v4_protocol,
        "_state_path",
        lambda _run_id: state_path,
    )
    monkeypatch.setattr(
        pbm_v4_protocol,
        "_result_path",
        lambda _state, arm: desktop_result if arm == "desktop" else room_result,
    )

    pbm_v4_protocol._write_json(
        state_path,
        {
            "run_id": run_id,
            "mode": "canary",
            "benchmark_fingerprint": "benchmark",
            "canary_fingerprint": "canary",
            "desktop": {
                "status": "monitoring",
                "thread_id": "client-new-thread:temporary",
            },
            "room": {"status": "complete", "classification": "VALID"},
            "complete": False,
            "aborted": False,
        },
    )
    pbm_v4_protocol._write_json(room_result, {"classification": "VALID"})

    recovered = []

    def fake_recover(candidate_run_id):
        recovered.append(candidate_run_id)
        state = pbm_v4_protocol._read_json(state_path)
        state["desktop"] = {
            "status": "complete",
            "classification": "VALID",
            "thread_id": "019f-real-thread",
            "provisional_thread_id": "client-new-thread:temporary",
        }
        pbm_v4_protocol._write_json(state_path, state)
        pbm_v4_protocol._write_json(
            desktop_result,
            {"classification": "VALID"},
        )
        return True

    def fake_finalize(candidate_run_id):
        state = pbm_v4_protocol._read_json(state_path)
        state["complete"] = True
        state["comparison"] = {"comparable": True}
        pbm_v4_protocol._write_json(state_path, state)
        return {"run_id": candidate_run_id, "complete": True}

    monkeypatch.setattr(
        pbm_v4_protocol,
        "_recover_desktop_if_ready",
        fake_recover,
    )
    monkeypatch.setattr(
        pbm_v4_protocol,
        "_finalize_if_ready",
        fake_finalize,
    )

    result = pbm_v4_protocol.status(run_id)

    assert recovered == [run_id]
    assert result["complete"] is True
    assert result["desktop"]["thread_id"] == "019f-real-thread"
    assert result["desktop"]["provisional_thread_id"] == "client-new-thread:temporary"

