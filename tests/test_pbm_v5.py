from __future__ import annotations

from pathlib import Path

from codex_room import pbm_v5


def test_desktop_candidates_select_only_top_level_prepared_workspace(
    tmp_path, monkeypatch
) -> None:
    workspace = tmp_path / "desktop-workspace"
    workspace.mkdir()
    root_rollout = tmp_path / "root.jsonl"
    child_rollout = tmp_path / "child.jsonl"
    wrong_rollout = tmp_path / "wrong.jsonl"
    for path in (root_rollout, child_rollout, wrong_rollout):
        path.write_text("{}\n", encoding="utf-8")

    metas = {
        root_rollout: {
            "id": "root",
            "timestamp": "2026-09-21T10:00:01Z",
            "cwd": str(workspace),
        },
        child_rollout: {
            "id": "child",
            "parent_thread_id": "root",
            "timestamp": "2026-09-21T10:00:02Z",
            "cwd": str(tmp_path / ".codex" / "worktrees" / "abcd" / "repo"),
        },
        wrong_rollout: {
            "id": "wrong",
            "timestamp": "2026-09-21T10:00:03Z",
            "cwd": str(tmp_path / "somewhere-else"),
        },
    }

    monkeypatch.setattr(
        pbm_v5.codex_usage,
        "_rollout_paths",
        lambda *_args, **_kwargs: [root_rollout, child_rollout, wrong_rollout],
    )
    monkeypatch.setattr(
        pbm_v5.codex_usage,
        "_session_meta",
        lambda path: metas[path],
    )
    monkeypatch.setattr(
        pbm_v5.codex_usage,
        "_thread_id",
        lambda meta: meta.get("id"),
    )
    monkeypatch.setattr(
        pbm_v5.codex_usage,
        "_parent_thread_id",
        lambda meta: meta.get("parent_thread_id"),
    )

    result = pbm_v5._desktop_candidates(
        {
            "workspace": str(workspace),
            "prepared_at": "2026-09-21T10:00:00Z",
        }
    )

    assert result == [(root_rollout, "root")]


def test_lineage_paths_follow_native_parent_relationships(tmp_path, monkeypatch) -> None:
    paths = [tmp_path / f"{name}.jsonl" for name in ("root", "a", "b", "other")]
    for path in paths:
        path.write_text("{}\n", encoding="utf-8")

    metas = {
        paths[0]: {"id": "root"},
        paths[1]: {"id": "a", "parent_thread_id": "root"},
        paths[2]: {"id": "b", "parent_thread_id": "a"},
        paths[3]: {"id": "other"},
    }

    monkeypatch.setattr(
        pbm_v5.codex_usage,
        "_rollout_paths",
        lambda *_args, **_kwargs: paths,
    )
    monkeypatch.setattr(
        pbm_v5.codex_usage,
        "_session_meta",
        lambda path: metas[path],
    )
    monkeypatch.setattr(
        pbm_v5.codex_usage,
        "_thread_id",
        lambda meta: meta.get("id"),
    )
    monkeypatch.setattr(
        pbm_v5.codex_usage,
        "_parent_thread_id",
        lambda meta: meta.get("parent_thread_id"),
    )

    result = pbm_v5._lineage_paths("root")
    ids = {
        pbm_v5.codex_usage._thread_id(meta)
        for _path, meta in result
    }

    assert ids == {"root", "a", "b"}


def test_lineage_usage_aggregates_root_and_descendants(tmp_path, monkeypatch) -> None:
    root = tmp_path / "root.jsonl"
    child = tmp_path / "child.jsonl"
    root.write_text("{}\n", encoding="utf-8")
    child.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(
        pbm_v5,
        "_lineage_paths",
        lambda _thread_id: [
            (root, {"id": "root"}),
            (child, {"id": "child", "parent_thread_id": "root"}),
        ],
    )

    reports = {
        root: {
            "thread": {"id": "root", "parent_thread_id": None, "cwd": "root"},
            "rollout_path": str(root),
            "final_total_usage": {
                "input_tokens": 100,
                "cached_input_tokens": 10,
                "output_tokens": 20,
                "reasoning_output_tokens": 5,
                "total_tokens": 120,
            },
            "counts": {"tool_calls": 2, "context_compactions": 0},
            "token_updates": [
                {"timestamp": "2026-09-21T10:00:00Z"},
                {"timestamp": "2026-09-21T10:00:10Z"},
            ],
        },
        child: {
            "thread": {
                "id": "child",
                "parent_thread_id": "root",
                "cwd": "managed-worktree",
            },
            "rollout_path": str(child),
            "final_total_usage": {
                "input_tokens": 50,
                "cached_input_tokens": 5,
                "output_tokens": 10,
                "reasoning_output_tokens": 2,
                "total_tokens": 60,
            },
            "counts": {"tool_calls": 1, "context_compactions": 1},
            "token_updates": [
                {"timestamp": "2026-09-21T10:00:02Z"},
                {"timestamp": "2026-09-21T10:00:15Z"},
            ],
        },
    }
    monkeypatch.setattr(
        pbm_v5.codex_usage,
        "analyze_rollout",
        lambda path: reports[path],
    )

    result = pbm_v5._lineage_usage("root")

    assert result["total_tokens"] == 180
    assert result["thread_count"] == 2
    assert result["descendant_count"] == 1
    assert result["tool_calls"] == 3
    assert result["context_compactions"] == 1
    assert result["duration_seconds"] == 15.0
    assert result["usage_complete"] is True


def test_comparison_uses_platform_aggregate_usage(tmp_path, monkeypatch) -> None:
    run_id = "pbm-v5-test"
    desktop_result = tmp_path / "desktop.json"
    room_result = tmp_path / "room.json"

    pbm_v5._write_json(
        desktop_result,
        {
            "classification": "VALID",
            "benchmark_fingerprint": "fp",
            "quality": {"pass": True, "score": 100, "checks": []},
            "usage": {
                "total_tokens": 200,
                "thread_count": 4,
                "descendant_count": 3,
            },
            "duration_seconds": 20,
        },
    )
    pbm_v5._write_json(
        room_result,
        {
            "classification": "VALID",
            "benchmark_fingerprint": "fp",
            "quality": {"pass": True, "score": 100, "checks": []},
            "usage": {
                "total_tokens": 300,
                "execution_count": 5,
                "peer_invocations": 4,
            },
            "duration_seconds": 30,
        },
    )

    monkeypatch.setattr(
        pbm_v5,
        "_result_path",
        lambda _state, arm: desktop_result if arm == "desktop" else room_result,
    )

    result = pbm_v5._comparison(
        {
            "run_id": run_id,
            "benchmark_fingerprint": "fp",
        }
    )

    assert result["comparable"] is True
    assert result["room_to_desktop_total_token_ratio"] == 1.5
    assert result["desktop"]["thread_count"] == 4
    assert result["desktop"]["descendant_count"] == 3
    assert result["room"]["peer_invocations"] == 4


def test_protocol_text_does_not_prescribe_desktop_subagent_choreography() -> None:
    protocol = (
        Path(__file__).parents[1]
        / "benchmarks"
        / "pbm"
        / "v5"
        / "PROTOCOL.md"
    ).read_text(encoding="utf-8")

    assert "does **not** prescribe either platform's internal workflow" in protocol
    assert "Any native descendant tasks created by Desktop are part of Desktop's platform execution" in protocol
    assert "PBM does not direct or message those descendants" in protocol


def test_worker_registration_does_not_clobber_terminal_state(
    tmp_path, monkeypatch
) -> None:
    run_id = "pbm-v5-worker-race"
    state_path = tmp_path / "state.json"
    lock = tmp_path / "lock"

    monkeypatch.setattr(pbm_v5, "_state_path", lambda _run_id: state_path)
    monkeypatch.setattr(pbm_v5, "LOCK_DIR", lock)

    pbm_v5._write_json(
        state_path,
        {
            "run_id": run_id,
            "desktop": {"status": "complete"},
            "room": {"status": "worker_error"},
        },
    )

    pbm_v5._record_worker_started(run_id, "desktop", 11, "monitoring")
    pbm_v5._record_worker_started(run_id, "room", 22, "running")

    state = pbm_v5._read_json(state_path)
    assert state["desktop"]["status"] == "complete"
    assert state["desktop"]["worker_pid"] == 11
    assert state["room"]["status"] == "worker_error"
    assert state["room"]["worker_pid"] == 22
