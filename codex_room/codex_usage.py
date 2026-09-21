"""Read-only Codex rollout token-usage reporting.

This module parses local Codex rollout JSONL files without invoking Codex or
modifying rollout/state files. It is intended for operating-economics
comparison between ordinary Codex work and Codex Room executions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


class RolloutUsageError(ValueError):
    """Raised when a rollout cannot be selected or interpreted safely."""


def default_codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def _usage(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {field: 0 for field in USAGE_FIELDS}
    result: dict[str, int] = {}
    for field in USAGE_FIELDS:
        value = raw.get(field, 0)
        result[field] = (
            int(value)
            if isinstance(value, int) and not isinstance(value, bool)
            else 0
        )
    return result


def _usage_delta(
    end: dict[str, int], start: dict[str, int]
) -> dict[str, int] | None:
    if any(end[field] < start[field] for field in USAGE_FIELDS):
        return None
    return {field: end[field] - start[field] for field in USAGE_FIELDS}


def _rollout_paths(codex_home: Path, *, include_archived: bool) -> list[Path]:
    roots = [codex_home / "sessions"]
    if include_archived:
        roots.append(codex_home / "archived_sessions")
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        paths.extend(path for path in root.rglob("rollout-*.jsonl") if path.is_file())
    return paths


def _read_json_lines(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RolloutUsageError(
                        f"{path}: invalid JSON at line {line_number}: {exc.msg}"
                    ) from exc
                if not isinstance(value, dict):
                    raise RolloutUsageError(
                        f"{path}: line {line_number} is not a JSON object"
                    )
                yield line_number, value
    except OSError as exc:
        raise RolloutUsageError(f"could not read rollout: {path}") from exc


def _session_meta(path: Path) -> dict[str, Any]:
    for _, record in _read_json_lines(path):
        if record.get("type") != "session_meta":
            continue
        payload = record.get("payload")
        if isinstance(payload, dict):
            return payload
    return {}


def _thread_id(meta: dict[str, Any]) -> str | None:
    value = meta.get("session_id") or meta.get("id")
    return str(value) if value is not None else None


def _parent_thread_id(meta: dict[str, Any]) -> str | None:
    value = meta.get("parent_thread_id")
    if value is not None:
        return str(value)
    source = meta.get("source")
    if isinstance(source, dict):
        for key in ("sub_agent", "subagent", "agent_control"):
            nested = source.get(key)
            if isinstance(nested, dict):
                parent = nested.get("parent_thread_id")
                if parent is not None:
                    return str(parent)
    return None


def _is_top_level(meta: dict[str, Any]) -> bool:
    return _parent_thread_id(meta) is None


def select_rollout(
    *,
    codex_home: Path,
    path: Path | None = None,
    thread_id: str | None = None,
    include_archived: bool = False,
    allow_subagent_latest: bool = False,
) -> Path:
    if path is not None:
        resolved = path.expanduser().resolve()
        if not resolved.is_file():
            raise RolloutUsageError(f"rollout file not found: {resolved}")
        if resolved.suffix.lower() != ".jsonl":
            raise RolloutUsageError("only uncompressed .jsonl rollouts are supported")
        return resolved

    candidates = _rollout_paths(codex_home, include_archived=include_archived)
    if not candidates:
        raise RolloutUsageError(
            f"no rollout JSONL files found beneath {codex_home}"
        )

    if thread_id is not None:
        matches = []
        for candidate in candidates:
            meta = _session_meta(candidate)
            if _thread_id(meta) == thread_id:
                matches.append(candidate)
        if not matches:
            raise RolloutUsageError(f"thread not found: {thread_id}")
        return max(matches, key=lambda item: item.stat().st_mtime_ns)

    ordered = sorted(candidates, key=lambda item: item.stat().st_mtime_ns, reverse=True)
    if allow_subagent_latest:
        return ordered[0]

    for candidate in ordered:
        if _is_top_level(_session_meta(candidate)):
            return candidate
    raise RolloutUsageError(
        "no top-level rollout found; use --include-subagents-latest or --path"
    )


def extract_user_messages(path: Path) -> list[str]:
    """Extract user/delegated prompt text across known Codex rollout schemas."""

    legacy: list[str] = []
    response_items: list[str] = []

    for _, record in _read_json_lines(path):
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue

        if (
            record.get("type") == "event_msg"
            and payload.get("type") == "user_message"
            and isinstance(payload.get("message"), str)
        ):
            legacy.append(str(payload["message"]))
            continue

        if record.get("type") != "response_item":
            continue

        role = payload.get("role")
        payload_type = payload.get("type")
        if role != "user" and payload_type != "user_message":
            continue

        metadata = payload.get("internal_chat_message_metadata_passthrough")
        if isinstance(metadata, dict):
            kinds = metadata.get("content_item_kinds")
            if isinstance(kinds, list) and "user.text" not in kinds:
                # Codex may serialize environment/plugin context as role=user
                # response items. Those are not principal/delegated task messages.
                continue

        message = payload.get("message")
        if isinstance(message, str):
            response_items.append(message)
            continue

        content = payload.get("content")
        if not isinstance(content, list):
            continue

        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and item.get("type") in {
                None,
                "input_text",
                "text",
            }:
                parts.append(text)
        if parts:
            response_items.append("".join(parts))

    # Modern response_item messages and legacy event messages can coexist for
    # one logical turn. Prefer the richer modern representation when present.
    return response_items if response_items else legacy


def analyze_rollout(path: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    event_counts: Counter[str] = Counter()
    token_updates: list[dict[str, Any]] = []
    user_turns: list[dict[str, Any]] = []
    latest_total = {field: 0 for field in USAGE_FIELDS}
    active_turn: dict[str, Any] | None = None

    for line_number, record in _read_json_lines(path):
        record_type = str(record.get("type", "unknown"))
        event_counts[f"record:{record_type}"] += 1

        if record_type == "session_meta" and not meta:
            payload = record.get("payload")
            if isinstance(payload, dict):
                meta = payload
            continue

        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue

        payload_type = payload.get("type")
        if isinstance(payload_type, str):
            event_counts[f"payload:{payload_type}"] += 1

        if record_type == "event_msg" and payload_type == "user_message":
            if active_turn is not None:
                active_turn["end_total_usage"] = dict(latest_total)
                active_turn["usage"] = _usage_delta(
                    latest_total, active_turn["baseline_total_usage"]
                )
                user_turns.append(active_turn)
            active_turn = {
                "index": len(user_turns) + 1,
                "timestamp": record.get("timestamp"),
                "line": line_number,
                "baseline_total_usage": dict(latest_total),
            }
            continue

        if record_type != "event_msg" or payload_type != "token_count":
            continue

        info = payload.get("info")
        if not isinstance(info, dict):
            continue
        total = _usage(info.get("total_token_usage"))
        last = _usage(info.get("last_token_usage"))
        delta = _usage_delta(total, latest_total)
        token_updates.append(
            {
                "index": len(token_updates) + 1,
                "timestamp": record.get("timestamp"),
                "line": line_number,
                "total": total,
                "last": last,
                "delta_from_previous_total": delta,
                "cumulative_decreased": delta is None,
                "model_context_window": info.get("model_context_window"),
            }
        )
        latest_total = total

    if active_turn is not None:
        active_turn["end_total_usage"] = dict(latest_total)
        active_turn["usage"] = _usage_delta(
            latest_total, active_turn["baseline_total_usage"]
        )
        user_turns.append(active_turn)

    parent = _parent_thread_id(meta)
    report = {
        "schema": "codex-rollout-usage-v1",
        "rollout_path": str(path.resolve()),
        "file_size_bytes": path.stat().st_size,
        "modified_time_ns": path.stat().st_mtime_ns,
        "thread": {
            "id": _thread_id(meta),
            "parent_thread_id": parent,
            "top_level": parent is None,
            "source": meta.get("source"),
            "cwd": meta.get("cwd"),
            "originator": meta.get("originator"),
            "cli_version": meta.get("cli_version"),
            "model_provider": meta.get("model_provider"),
            "agent_nickname": meta.get("agent_nickname"),
            "agent_role": meta.get("agent_role"),
        },
        "counts": {
            "user_turns": len(user_turns),
            "token_count_updates": len(token_updates),
            "provider_response_usage_records": event_counts.get(
                "record:token_usage_record", 0
            ),
            "zero_delta_token_count_updates": sum(
                1
                for update in token_updates
                if update["delta_from_previous_total"] is not None
                and update["delta_from_previous_total"]["total_tokens"] == 0
            ),
            "custom_tool_calls": event_counts.get("payload:custom_tool_call", 0),
            "function_calls": event_counts.get("payload:function_call", 0),
            "tool_calls": (
                event_counts.get("payload:custom_tool_call", 0)
                + event_counts.get("payload:function_call", 0)
            ),
            "context_compactions": event_counts.get("payload:context_compacted", 0),
            "sub_agent_activity": event_counts.get("payload:sub_agent_activity", 0),
            "inter_agent_communication_metadata": event_counts.get(
                "record:inter_agent_communication_metadata", 0
            ),
        },
        "final_total_usage": dict(latest_total) if token_updates else None,
        "final_last_usage": token_updates[-1]["last"] if token_updates else None,
        "user_turns": user_turns,
        "token_updates": token_updates,
        "event_type_counts": dict(sorted(event_counts.items())),
    }
    return report


def _fmt(value: int | None) -> str:
    return "unavailable" if value is None else f"{value:,}"


def _print_usage(label: str, usage: dict[str, int] | None) -> None:
    print(label)
    if usage is None:
        print("  unavailable")
        return
    for field in USAGE_FIELDS:
        print(f"  {field}: {_fmt(usage[field])}")


def print_human(report: dict[str, Any], *, timeline: bool) -> None:
    thread = report["thread"]
    counts = report["counts"]
    print("Codex rollout usage")
    print(f"  path: {report['rollout_path']}")
    print(f"  thread_id: {thread['id'] or 'unavailable'}")
    print(f"  top_level: {str(thread['top_level']).lower()}")
    if thread["parent_thread_id"]:
        print(f"  parent_thread_id: {thread['parent_thread_id']}")
    if thread["source"] is not None:
        print(f"  source: {json.dumps(thread['source'], ensure_ascii=False)}")
    if thread["cwd"]:
        print(f"  cwd: {thread['cwd']}")
    if thread["cli_version"]:
        print(f"  cli_version: {thread['cli_version']}")
    print(f"  user_turns: {counts['user_turns']}")
    print(f"  token_count_updates: {counts['token_count_updates']}")
    print(
        f"  provider_response_usage_records: "
        f"{counts['provider_response_usage_records']}"
    )
    print(
        f"  zero_delta_token_count_updates: "
        f"{counts['zero_delta_token_count_updates']}"
    )
    print(f"  tool_calls: {counts['tool_calls']}")
    print(f"  context_compactions: {counts['context_compactions']}")
    print(f"  sub_agent_activity: {counts['sub_agent_activity']}")
    print(
        f"  inter_agent_communication_metadata: "
        f"{counts['inter_agent_communication_metadata']}"
    )
    _print_usage("Final cumulative usage:", report["final_total_usage"])
    _print_usage("Last provider usage:", report["final_last_usage"])

    turns = report["user_turns"]
    if turns:
        last_turn = turns[-1]
        _print_usage(
            f"Latest user-turn usage (turn {last_turn['index']}):",
            last_turn["usage"],
        )
    if timeline and report["token_updates"]:
        print("Token-update timeline:")
        for update in report["token_updates"]:
            total = update["total"]["total_tokens"]
            delta = update["delta_from_previous_total"]
            delta_total = None if delta is None else delta["total_tokens"]
            print(
                f"  #{update['index']} line={update['line']} "
                f"total={_fmt(total)} delta={_fmt(delta_total)}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-rollout-usage",
        description=(
            "Read local Codex rollout JSONL token counters without invoking Codex."
        ),
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=default_codex_home(),
        help="Codex home directory (default: CODEX_HOME or ~/.codex).",
    )
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument("--path", type=Path, help="Exact rollout .jsonl path.")
    selector.add_argument("--thread-id", help="Exact Codex thread/session id.")
    parser.add_argument(
        "--include-archived",
        action="store_true",
        help="Include archived_sessions when selecting by thread/latest.",
    )
    parser.add_argument(
        "--include-subagents-latest",
        action="store_true",
        help="Allow the latest rollout to be a child/subagent thread.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the complete machine-readable report.",
    )
    parser.add_argument(
        "--timeline",
        action="store_true",
        help="Show cumulative token-update progression in human output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        path = select_rollout(
            codex_home=args.codex_home.expanduser(),
            path=args.path,
            thread_id=args.thread_id,
            include_archived=args.include_archived,
            allow_subagent_latest=args.include_subagents_latest,
        )
        report = analyze_rollout(path)
    except RolloutUsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print_human(report, timeline=args.timeline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
