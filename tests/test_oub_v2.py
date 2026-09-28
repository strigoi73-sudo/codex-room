from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

from codex_room import oub_v2


def test_oub_v2_audit_binds_frozen_three_task_sample() -> None:
    result = oub_v2.audit_harness()

    assert result["ok"] is True
    assert result["benchmark_version"] == "v2"
    assert result["task_ids"] == ["o2-1", "o2-2", "o2-3"]
    assert len(result["audited_feature_assets"]) == 6
    assert len(result["benchmark_fingerprint"]) == 64
    assert result["current_pointer"] == "v1"
    assert result["current_pointer_promoted"] is False


def test_oub_v2_mission_contains_only_public_specs_and_neutral_completion_signal() -> None:
    task = oub_v2._task("o2-1")
    mission = oub_v2._mission_text(task)

    assert "Add Progress Callback Hook to Audio Resolution for Byte Tracking" in mission
    assert "max_bytes" in mission
    assert '{"status":"complete"}' in mission
    assert "hidden tests" in mission.lower()
    assert "gold/reference patches" in mission.lower()
    assert "pytest.raises" not in mission
    assert "Agent A" not in mission
    assert "Agent B" not in mission
    assert "delegate" not in mission.lower()


def test_oub_v2_room_payload_preserves_naturalistic_orchestration() -> None:
    task = oub_v2._task("o2-2")
    payload = oub_v2._room_payload("oub-test", task)

    assert payload["starting_agent"] == "agent_c"
    assert payload["required_contributors"] == []
    assert payload["completion_policy"] == "auto_settle"
    assert payload["work_model_version"] == 2
    assert payload["provider_context_mode"] == "assignment_thread"
    assert payload["max_turns"] == 60
    assert payload["topic"] == oub_v2.PASTE
    assert "Agent A" not in payload["topic"]
    assert "Agent B" not in payload["topic"]
    assert "delegate" not in payload["topic"].lower()


def test_oub_v2_completion_marker_is_exact(tmp_path: Path) -> None:
    assert oub_v2._marker_ok(tmp_path) is False

    marker = tmp_path / "OUB_COMPLETE.json"
    marker.write_text('{"status":"complete"}\n', encoding="utf-8")
    assert oub_v2._marker_ok(tmp_path) is True

    marker.write_text('{"status":"complete","extra":true}\n', encoding="utf-8")
    assert oub_v2._marker_ok(tmp_path) is False


def test_oub_v2_start_state_accepts_harness_files_without_dirtying_repo(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "oub@example.invalid"],
        cwd=workspace,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "OUB Test"],
        cwd=workspace,
        check=True,
    )
    (workspace / "source.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "source.txt"], cwd=workspace, check=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=workspace, check=True, capture_output=True)

    exclude = workspace / ".git" / "info" / "exclude"
    with exclude.open("a", encoding="utf-8") as handle:
        handle.write("/BENCHMARK.md\n/OUB_COMPLETE.json\n")
    (workspace / "BENCHMARK.md").write_text("mission\n", encoding="utf-8")

    state = oub_v2._workspace_start_state(workspace)

    assert len(state["head"]) == 40
    assert len(state["tree"]) == 40
    assert len(state["mission_sha256"]) == 64
    assert state["status"] == ""


def test_oub_v2_comparison_keeps_quality_cost_and_organization_separate(
    tmp_path: Path, monkeypatch
) -> None:
    desktop_path = tmp_path / "desktop.json"
    room_path = tmp_path / "room.json"
    common = {
        "benchmark_fingerprint": "fp",
        "classification": "VALID",
        "quality": {"pass": True, "passed_features": 2, "total_features": 2},
    }
    desktop_path.write_text(
        json.dumps(
            common
            | {
                "usage": {
                    "total_tokens": 200,
                    "thread_count": 1,
                    "descendant_count": 0,
                    "tool_calls": 4,
                },
                "duration_seconds": 100,
                "human_involvement": {"substantive_intervention_count": 0},
                "provenance": {"model_configurations": None},
            }
        ),
        encoding="utf-8",
    )
    room_path.write_text(
        json.dumps(
            common
            | {
                "usage": {
                    "total_tokens": 300,
                    "execution_count": 3,
                    "peer_invocations": 2,
                    "tool_calls": 6,
                },
                "duration_seconds": 120,
                "human_involvement": {"substantive_intervention_count": 0},
                "provenance": {
                    "model_configurations": [
                        {"model": "gpt-5.6-sol", "reasoning_effort": "high"}
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        oub_v2,
        "_result_path",
        lambda _state, arm: desktop_path if arm == "desktop" else room_path,
    )

    result = oub_v2._comparison(
        {
            "run_id": "oub-test",
            "task_id": "o2-1",
            "benchmark_fingerprint": "fp",
        }
    )

    assert result["comparable"] is True
    assert result["desktop"]["pass"] is True
    assert result["room"]["pass"] is True
    assert result["room_to_desktop_total_token_ratio"] == 1.5
    assert result["room_to_desktop_duration_ratio"] == 1.2
    assert result["desktop"]["descendant_count"] == 0
    assert result["room"]["peer_invocations"] == 2
    assert "score" not in result
    assert "overall ranking" in result["interpretation_note"].lower()


def test_oub_v2_parser_supports_mechanical_only_preparation() -> None:
    args = oub_v2.build_parser().parse_args(
        ["prepare", "--task-id", "o2-3", "--no-start"]
    )
    assert args.command == "prepare"
    assert args.task_id == "o2-3"
    assert args.no_start is True

def test_oub_v2_materialized_workspace_pins_cross_host_line_endings(
    tmp_path: Path,
) -> None:
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    subprocess.run(["git", "init"], cwd=upstream, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "oub@example.invalid"],
        cwd=upstream,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "OUB Test"],
        cwd=upstream,
        check=True,
    )
    (upstream / "source.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "source.txt"], cwd=upstream, check=True)
    subprocess.run(
        ["git", "commit", "-m", "base"],
        cwd=upstream,
        check=True,
        capture_output=True,
    )
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=upstream,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    workspace = tmp_path / "workspace"
    state = oub_v2._materialize_workspace(
        workspace,
        {
            "id": "cross-host-test",
            "project_url": str(upstream),
            "base_commit": base_commit,
            "features": [],
        },
    )

    autocrlf = subprocess.run(
        ["git", "config", "--get", "core.autocrlf"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    assert autocrlf == "false"
    assert state["head"] == base_commit
    assert state["status"] == ""

def test_oub_v2_json_output_is_safe_for_legacy_windows_code_pages(
    monkeypatch,
) -> None:
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1252", write_through=True)
    monkeypatch.setattr(oub_v2.sys, "stdout", stream)

    oub_v2._json_out({"status": "❌"})

    stream.flush()
    rendered = raw.getvalue().decode("cp1252")
    assert "\\u274c" in rendered
    assert json.loads(rendered) == {"status": "❌"}

def test_oub_v2_materialization_retries_external_fetch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    subprocess.run(["git", "init"], cwd=upstream, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "oub@example.invalid"],
        cwd=upstream,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "OUB Test"],
        cwd=upstream,
        check=True,
    )
    (upstream / "source.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "source.txt"], cwd=upstream, check=True)
    subprocess.run(
        ["git", "commit", "-m", "base"],
        cwd=upstream,
        check=True,
        capture_output=True,
    )
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=upstream,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    real_git = oub_v2._git
    fetch_attempts = 0
    sleeps: list[int] = []

    def flaky_git(args, *, cwd=None, timeout=1200, text=True):
        nonlocal fetch_attempts
        if args and args[0] == "fetch":
            fetch_attempts += 1
            if fetch_attempts < 3:
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=1,
                    stdout="transient fetch failure",
                )
        return real_git(args, cwd=cwd, timeout=timeout, text=text)

    monkeypatch.setattr(oub_v2, "_git", flaky_git)
    monkeypatch.setattr(oub_v2.time, "sleep", sleeps.append)

    workspace = tmp_path / "workspace"
    state = oub_v2._materialize_workspace(
        workspace,
        {
            "id": "fetch-retry-test",
            "project_url": str(upstream),
            "base_commit": base_commit,
            "features": [],
        },
    )

    assert fetch_attempts == 3
    assert sleeps == [1, 2]
    assert state["head"] == base_commit
    assert state["status"] == ""
