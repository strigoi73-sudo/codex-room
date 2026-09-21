from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from codex_room.codex_usage import (
    RolloutUsageError,
    analyze_rollout,
    extract_user_messages,
    main,
    select_rollout,
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def _meta(thread_id: str, *, parent: str | None = None) -> dict:
    payload = {
        "session_id": thread_id,
        "id": thread_id,
        "timestamp": "2026-09-15T12:00:00Z",
        "cwd": "C:\\Codex Room",
        "originator": "codex_desktop",
        "cli_version": "0.154.0",
        "source": "vscode",
        "model_provider": "openai",
    }
    if parent is not None:
        payload["parent_thread_id"] = parent
    return {
        "timestamp": "2026-09-15T12:00:00Z",
        "type": "session_meta",
        "payload": payload,
    }


def _usage(total: int, *, input_tokens: int, cached: int, output: int, reasoning: int) -> dict:
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "cache_write_input_tokens": 0,
        "output_tokens": output,
        "reasoning_output_tokens": reasoning,
        "total_tokens": total,
    }


def _token_event(total_usage: dict, last_usage: dict, timestamp: str) -> dict:
    return {
        "timestamp": timestamp,
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {
                "total_token_usage": total_usage,
                "last_token_usage": last_usage,
                "model_context_window": 200000,
            },
            "rate_limits": None,
        },
    }


def test_analyze_rollout_reports_cumulative_and_per_user_turn_usage(tmp_path: Path) -> None:
    path = tmp_path / "rollout.jsonl"
    first = _usage(100, input_tokens=80, cached=60, output=20, reasoning=5)
    second_total = _usage(260, input_tokens=220, cached=180, output=40, reasoning=12)
    second_last = _usage(160, input_tokens=140, cached=120, output=20, reasoning=7)
    _write_jsonl(
        path,
        [
            _meta("thread-1"),
            {
                "timestamp": "2026-09-15T12:00:01Z",
                "type": "event_msg",
                "payload": {"type": "user_message", "message": "first", "kind": "plain"},
            },
            _token_event(first, first, "2026-09-15T12:00:02Z"),
            {
                "timestamp": "2026-09-15T12:00:03Z",
                "type": "event_msg",
                "payload": {"type": "user_message", "message": "second", "kind": "plain"},
            },
            _token_event(second_total, second_last, "2026-09-15T12:00:04Z"),
            {
                "timestamp": "2026-09-15T12:00:05Z",
                "type": "event_msg",
                "payload": {"type": "context_compacted"},
            },
            {
                "timestamp": "2026-09-15T12:00:06Z",
                "type": "event_msg",
                "payload": {"type": "sub_agent_activity"},
            },
        ],
    )

    report = analyze_rollout(path)

    assert report["thread"]["id"] == "thread-1"
    assert report["thread"]["top_level"] is True
    assert report["counts"] == {
        "user_turns": 2,
        "token_count_updates": 2,
        "provider_response_usage_records": 0,
        "zero_delta_token_count_updates": 0,
        "custom_tool_calls": 0,
        "function_calls": 0,
        "tool_calls": 0,
        "context_compactions": 1,
        "sub_agent_activity": 1,
        "inter_agent_communication_metadata": 0,
    }
    assert report["final_total_usage"] == second_total
    assert report["final_last_usage"] == second_last
    assert report["user_turns"][0]["usage"] == first
    assert report["user_turns"][1]["usage"] == second_last
    assert report["token_updates"][1]["delta_from_previous_total"] == second_last
    serialized = json.dumps(report)
    assert "\"first\"" not in serialized
    assert "\"second\"" not in serialized


def test_select_latest_prefers_top_level_over_newer_child(tmp_path: Path) -> None:
    home = tmp_path / ".codex"
    top = home / "sessions/2026/09/15/rollout-top.jsonl"
    child = home / "sessions/2026/09/15/rollout-child.jsonl"
    _write_jsonl(top, [_meta("top")])
    _write_jsonl(child, [_meta("child", parent="top")])
    os.utime(top, ns=(1_000_000_000, 1_000_000_000))
    os.utime(child, ns=(2_000_000_000, 2_000_000_000))

    assert select_rollout(codex_home=home) == top
    assert (
        select_rollout(codex_home=home, allow_subagent_latest=True)
        == child
    )
    assert select_rollout(codex_home=home, thread_id="child") == child


def test_nested_subagent_source_parent_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "rollout.jsonl"
    record = _meta("child")
    record["payload"].pop("parent_thread_id", None)
    record["payload"]["source"] = {
        "sub_agent": {"parent_thread_id": "parent"}
    }
    _write_jsonl(path, [record])

    report = analyze_rollout(path)

    assert report["thread"]["parent_thread_id"] == "parent"
    assert report["thread"]["top_level"] is False


def test_cumulative_decrease_is_flagged_instead_of_emitting_negative_delta(
    tmp_path: Path,
) -> None:
    path = tmp_path / "rollout.jsonl"
    high = _usage(200, input_tokens=180, cached=150, output=20, reasoning=5)
    low = _usage(100, input_tokens=90, cached=70, output=10, reasoning=2)
    _write_jsonl(
        path,
        [
            _meta("thread-reset"),
            _token_event(high, high, "2026-09-15T12:00:01Z"),
            _token_event(low, low, "2026-09-15T12:00:02Z"),
        ],
    )

    report = analyze_rollout(path)

    assert report["token_updates"][1]["cumulative_decreased"] is True
    assert report["token_updates"][1]["delta_from_previous_total"] is None


def test_main_json_output_uses_exact_path(tmp_path: Path, capsys) -> None:
    path = tmp_path / "rollout.jsonl"
    total = _usage(50, input_tokens=40, cached=30, output=10, reasoning=3)
    _write_jsonl(path, [_meta("thread-json"), _token_event(total, total, "2026-09-15T12:00:01Z")])

    assert main(["--path", str(path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["thread"]["id"] == "thread-json"
    assert payload["final_total_usage"]["total_tokens"] == 50


def test_missing_rollouts_fail_cleanly(tmp_path: Path) -> None:
    with pytest.raises(RolloutUsageError, match="no rollout JSONL"):
        select_rollout(codex_home=tmp_path)

def test_rollout_summary_counts_provider_records_tool_calls_and_zero_delta(
    tmp_path: Path,
) -> None:
    path = tmp_path / "rollout.jsonl"
    total = _usage(100, input_tokens=80, cached=60, output=20, reasoning=5)
    _write_jsonl(
        path,
        [
            _meta("thread-summary"),
            _token_event(total, total, "2026-09-15T12:00:01Z"),
            {
                "timestamp": "2026-09-15T12:00:02Z",
                "type": "token_usage_record",
                "payload": {},
            },
            {
                "timestamp": "2026-09-15T12:00:03Z",
                "type": "response_item",
                "payload": {"type": "custom_tool_call"},
            },
            {
                "timestamp": "2026-09-15T12:00:04Z",
                "type": "response_item",
                "payload": {"type": "function_call"},
            },
            {
                "timestamp": "2026-09-15T12:00:05Z",
                "type": "inter_agent_communication_metadata",
                "payload": {},
            },
            _token_event(total, total, "2026-09-15T12:00:06Z"),
        ],
    )

    report = analyze_rollout(path)
    counts = report["counts"]

    assert counts["provider_response_usage_records"] == 1
    assert counts["zero_delta_token_count_updates"] == 1
    assert counts["custom_tool_calls"] == 1
    assert counts["function_calls"] == 1
    assert counts["tool_calls"] == 2
    assert counts["inter_agent_communication_metadata"] == 1



def test_extract_user_messages_supports_response_item_schema(tmp_path: Path) -> None:
    path = tmp_path / "rollout-modern.jsonl"
    prompt = "Read BENCHMARK.md and execute it exactly."
    _write_jsonl(
        path,
        [
            _meta("thread-modern"),
            {
                "timestamp": "2026-09-21T03:59:59Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "<environment_context>synthetic</environment_context>"},
                    ],
                    "internal_chat_message_metadata_passthrough": {
                        "content_item_kinds": ["environments.environment_context"],
                    },
                },
            },
            {
                "timestamp": "2026-09-21T04:00:00Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                    ],
                    "internal_chat_message_metadata_passthrough": {
                        "content_item_kinds": ["user.text"],
                    },
                },
            },
        ],
    )

    assert extract_user_messages(path) == [prompt]


def test_extract_user_messages_prefers_modern_record_when_both_schemas_exist(
    tmp_path: Path,
) -> None:
    path = tmp_path / "rollout-dual.jsonl"
    prompt = "delegated task prompt"
    _write_jsonl(
        path,
        [
            _meta("thread-dual"),
            {
                "timestamp": "2026-09-21T04:00:00Z",
                "type": "event_msg",
                "payload": {"type": "user_message", "message": prompt},
            },
            {
                "timestamp": "2026-09-21T04:00:00Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                    ],
                },
            },
        ],
    )

    assert extract_user_messages(path) == [prompt]
