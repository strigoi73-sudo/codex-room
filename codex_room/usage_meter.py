from __future__ import annotations

from typing import Any


def _available_section_data(value: Any) -> tuple[str, dict[str, Any] | None]:
    if not isinstance(value, dict):
        return "unavailable", None
    status = str(value.get("status") or "unavailable")
    data = value.get("data")
    return status, data if isinstance(data, dict) else None


def rate_limit_windows(value: Any) -> list[dict[str, Any]]:
    status, data = _available_section_data(value)
    if status != "available" or data is None:
        return []

    snapshots: list[tuple[str | None, dict[str, Any]]] = []
    by_id = data.get("rateLimitsByLimitId")
    if isinstance(by_id, dict) and by_id:
        for limit_id, snapshot in sorted(by_id.items()):
            if isinstance(snapshot, dict):
                snapshots.append((str(limit_id), snapshot))
    else:
        snapshot = data.get("rateLimits")
        if isinstance(snapshot, dict):
            snapshots.append((None, snapshot))

    result: list[dict[str, Any]] = []
    for fallback_limit_id, snapshot in snapshots:
        limit_id = snapshot.get("limitId") or fallback_limit_id
        limit_name = snapshot.get("limitName")
        for window_name in ("primary", "secondary"):
            window = snapshot.get(window_name)
            if not isinstance(window, dict):
                continue
            result.append(
                {
                    "limit_id": limit_id,
                    "limit_name": limit_name,
                    "window": window_name,
                    "used_percent": window.get("usedPercent"),
                    "window_duration_mins": window.get("windowDurationMins"),
                    "resets_at": window.get("resetsAt"),
                }
            )
    return result


def account_usage_view(value: Any) -> dict[str, Any]:
    status, data = _available_section_data(value)
    result: dict[str, Any] = {"status": status}
    if status != "available" or data is None:
        if isinstance(value, dict) and value.get("error_type"):
            result["error_type"] = value.get("error_type")
        return result

    summary = data.get("summary")
    if isinstance(summary, dict):
        result["summary"] = {
            "lifetime_tokens": summary.get("lifetimeTokens"),
            "peak_daily_tokens": summary.get("peakDailyTokens"),
            "longest_running_turn_sec": summary.get("longestRunningTurnSec"),
            "current_streak_days": summary.get("currentStreakDays"),
            "longest_streak_days": summary.get("longestStreakDays"),
        }

    buckets = data.get("dailyUsageBuckets")
    if isinstance(buckets, list):
        result["daily_usage_buckets"] = [
            {"start_date": item.get("startDate"), "tokens": item.get("tokens")}
            for item in buckets
            if isinstance(item, dict)
        ]
    return result


def normalize_usage_meter(
    raw: dict[str, Any] | None, *, captured_at: str
) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    rate_limits = raw.get("rate_limits")
    rate_status, rate_data = _available_section_data(rate_limits)
    normalized_rate: dict[str, Any] = {
        "status": rate_status,
        "ordinary_usage_allowed": (
            rate_data.get("ordinaryUsageAllowed")
            if isinstance(rate_data, dict)
            else None
        ),
        "windows": rate_limit_windows(rate_limits),
    }
    if isinstance(rate_limits, dict) and rate_limits.get("error_type"):
        normalized_rate["error_type"] = rate_limits.get("error_type")
    return {
        "captured_at": captured_at,
        "rate_limits": normalized_rate,
        "account_usage": account_usage_view(raw.get("account_usage")),
    }


def _numeric_delta(before: Any, after: Any) -> int | float | None:
    if (
        isinstance(before, (int, float))
        and not isinstance(before, bool)
        and isinstance(after, (int, float))
        and not isinstance(after, bool)
    ):
        return after - before
    return None


def usage_meter_delta(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if before is None or after is None:
        return None

    before_usage = before.get("account_usage") or {}
    after_usage = after.get("account_usage") or {}
    before_summary = before_usage.get("summary") or {}
    after_summary = after_usage.get("summary") or {}
    lifetime_delta = _numeric_delta(
        before_summary.get("lifetime_tokens"),
        after_summary.get("lifetime_tokens"),
    )

    before_buckets = {
        item.get("start_date"): item.get("tokens")
        for item in (before_usage.get("daily_usage_buckets") or [])
        if isinstance(item, dict) and item.get("start_date")
    }
    daily_deltas: list[dict[str, Any]] = []
    for item in after_usage.get("daily_usage_buckets") or []:
        if not isinstance(item, dict):
            continue
        start_date = item.get("start_date")
        if start_date not in before_buckets:
            continue
        delta = _numeric_delta(before_buckets[start_date], item.get("tokens"))
        if delta is not None:
            daily_deltas.append(
                {
                    "start_date": start_date,
                    "before_tokens": before_buckets[start_date],
                    "after_tokens": item.get("tokens"),
                    "delta_tokens": delta,
                }
            )

    def window_key(item: dict[str, Any]) -> tuple[Any, Any, Any]:
        return (
            item.get("limit_id") or item.get("limit_name"),
            item.get("window"),
            item.get("window_duration_mins"),
        )

    before_windows = {
        window_key(item): item
        for item in ((before.get("rate_limits") or {}).get("windows") or [])
        if isinstance(item, dict)
    }
    window_deltas: list[dict[str, Any]] = []
    for after_item in ((after.get("rate_limits") or {}).get("windows") or []):
        if not isinstance(after_item, dict):
            continue
        key = window_key(after_item)
        before_item = before_windows.get(key)
        if before_item is None:
            continue
        reset_changed = before_item.get("resets_at") != after_item.get("resets_at")
        used_delta = (
            None
            if reset_changed
            else _numeric_delta(
                before_item.get("used_percent"),
                after_item.get("used_percent"),
            )
        )
        window_deltas.append(
            {
                "limit_id": after_item.get("limit_id"),
                "limit_name": after_item.get("limit_name"),
                "window": after_item.get("window"),
                "window_duration_mins": after_item.get("window_duration_mins"),
                "before_used_percent": before_item.get("used_percent"),
                "after_used_percent": after_item.get("used_percent"),
                "delta_percentage_points": used_delta,
                "before_resets_at": before_item.get("resets_at"),
                "after_resets_at": after_item.get("resets_at"),
                "reset_changed": reset_changed,
            }
        )
    return {
        "lifetime_tokens_delta": lifetime_delta,
        "daily_usage_bucket_deltas": daily_deltas,
        "rate_limit_window_deltas": window_deltas,
    }
