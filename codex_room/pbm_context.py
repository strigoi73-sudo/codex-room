"""Context snapshots for PBM v2 and later benchmark protocols."""

from __future__ import annotations

import asyncio
import json
import os
import platform
import re
import shutil
import subprocess
from importlib import metadata
from pathlib import Path
from typing import Any

_CONTEXT_LABEL_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_SENSITIVE_KEYS = {
    "email",
    "accountid",
    "userid",
    "accesstoken",
    "refreshtoken",
    "idtoken",
    "apikey",
    "authorization",
    "credential",
    "credentials",
    "secret",
}


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def sanitize(value: Any) -> Any:
    """Remove identity/credential fields while preserving usage and rate-limit data."""
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if _normalized_key(key) in _SENSITIVE_KEYS:
                continue
            result[str(key)] = sanitize(item)
        return result
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _git(project_root: Path, *args: str) -> dict[str, Any]:
    process = subprocess.run(
        ["git", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return {
        "ok": process.returncode == 0,
        "exit_code": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr_type": None if process.returncode == 0 else "git_error",
    }


def repository_context(project_root: Path) -> dict[str, Any]:
    head = _git(project_root, "rev-parse", "HEAD")
    branch = _git(project_root, "symbolic-ref", "--short", "-q", "HEAD")
    status = _git(project_root, "status", "--short")
    return {
        "head": head["stdout"] if head["ok"] else None,
        "branch": branch["stdout"] if branch["ok"] and branch["stdout"] else None,
        "detached": not (branch["ok"] and bool(branch["stdout"])),
        "working_tree_clean": status["ok"] and not bool(status["stdout"]),
        "status_lines": status["stdout"].splitlines() if status["ok"] and status["stdout"] else [],
    }


def environment_context(project_root: Path) -> dict[str, Any]:
    try:
        codex_sdk_version = metadata.version("openai-codex")
    except metadata.PackageNotFoundError:
        codex_sdk_version = None
    try:
        disk = shutil.disk_usage(project_root)
        disk_free_bytes: int | None = disk.free
    except OSError:
        disk_free_bytes = None
    return {
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "disk_free_bytes": disk_free_bytes,
        "openai_codex_package_version": codex_sdk_version,
    }


def _response_payload(response: Any) -> dict[str, Any] | None:
    if response is None:
        return None
    if hasattr(response, "model_dump"):
        raw = response.model_dump(mode="json", by_alias=True)
        return sanitize(raw) if isinstance(raw, dict) else None
    if isinstance(response, dict):
        return sanitize(response)
    return None


async def _safe_request(
    request: Any,
    method: str,
    params: dict[str, Any],
    response_model: type[Any],
) -> dict[str, Any]:
    try:
        response = await request(method, params, response_model=response_model)
        payload = _response_payload(response)
        return {"status": "available", "data": payload}
    except Exception as exc:
        return {"status": "unavailable", "error_type": type(exc).__name__}


def _effective_config(payload: dict[str, Any] | None) -> dict[str, Any]:
    config = (payload or {}).get("config") or {}
    if not isinstance(config, dict):
        return {}
    aliases = {
        "model": ("model",),
        "model_reasoning_effort": ("model_reasoning_effort", "modelReasoningEffort"),
        "approval_policy": ("approval_policy", "approvalPolicy"),
        "sandbox_mode": ("sandbox_mode", "sandboxMode"),
        "web_search": ("web_search", "webSearch"),
    }
    result: dict[str, Any] = {}
    for canonical, candidates in aliases.items():
        for candidate in candidates:
            if candidate in config:
                result[canonical] = sanitize(config.get(candidate))
                break
    return result


async def _collect_native_base(project_root: Path) -> dict[str, Any]:
    """Inspect the pinned native Codex SDK without Room configuration overrides."""
    from openai_codex import AsyncCodex, CodexConfig
    from .agent import sdk_server_identity

    client = AsyncCodex(
        config=CodexConfig(codex_bin=os.environ.get("CODEX_ROOM_CODEX_BIN"))
    )
    result: dict[str, Any] = {}
    try:
        account_response = await client.account(refresh_token=False)
        root = getattr(account_response, "account", None)
        if root is None:
            root = getattr(account_response, "root", None)
        if root is not None and hasattr(root, "model_dump"):
            account = root.model_dump(mode="json")
        elif hasattr(account_response, "model_dump"):
            account = account_response.model_dump(mode="json")
        else:
            account = {"authenticated": True}
        if isinstance(account, dict):
            account.pop("email", None)
        result["account"] = {"status": "available", "data": sanitize(account)}
        result["runtime"] = sdk_server_identity(getattr(client, "metadata", None))

        low_level = getattr(client, "_client", None)
        request = getattr(low_level, "request", None)
        if not callable(request):
            unavailable = {"status": "unavailable", "error_type": "request_unavailable"}
            result["rate_limits"] = unavailable
            result["account_usage"] = dict(unavailable)
            result["effective_config"] = dict(unavailable)
            return result

        try:
            from openai_codex.generated.v2_all import (
                ConfigReadResponse,
                GetAccountRateLimitsResponse,
                GetAccountTokenUsageResponse,
            )
        except (ImportError, AttributeError) as exc:
            unavailable = {"status": "unavailable", "error_type": type(exc).__name__}
            result["rate_limits"] = unavailable
            result["account_usage"] = dict(unavailable)
            result["effective_config"] = dict(unavailable)
            return result

        rate_limits, account_usage, config = await asyncio.gather(
            _safe_request(
                request,
                "account/rateLimits/read",
                {},
                GetAccountRateLimitsResponse,
            ),
            _safe_request(
                request,
                "account/usage/read",
                {},
                GetAccountTokenUsageResponse,
            ),
            _safe_request(
                request,
                "config/read",
                {"cwd": str(project_root), "includeLayers": False},
                ConfigReadResponse,
            ),
        )
        result["rate_limits"] = rate_limits
        result["account_usage"] = account_usage
        if config.get("status") == "available":
            result["effective_config"] = {
                "status": "available",
                "data": _effective_config(config.get("data")),
            }
        else:
            result["effective_config"] = config
        return result
    except Exception as exc:
        result.setdefault(
            "account",
            {"status": "unavailable", "error_type": type(exc).__name__},
        )
        result.setdefault(
            "rate_limits",
            {"status": "unavailable", "error_type": type(exc).__name__},
        )
        result.setdefault(
            "account_usage",
            {"status": "unavailable", "error_type": type(exc).__name__},
        )
        result.setdefault(
            "effective_config",
            {"status": "unavailable", "error_type": type(exc).__name__},
        )
        result.setdefault("runtime", None)
        return result
    finally:
        try:
            await client.close()
        except Exception:
            pass


async def _collect_room_context(project_root: Path) -> dict[str, Any]:
    """Inspect the Codex runtime with the exact Room configuration overrides."""
    from .agent import CodexAgentAdapter

    adapter = CodexAgentAdapter()
    result: dict[str, Any] = {}
    try:
        account = await adapter.initialize()
        result["runtime"] = (account or {}).get("runtime")
        result["tool_inventory"] = await adapter.inspect_tools(project_root)

        sdk_client = getattr(adapter, "_client", None)
        low_level = getattr(sdk_client, "_client", None)
        request = getattr(low_level, "request", None)
        if not callable(request):
            result["effective_config"] = {
                "status": "unavailable",
                "error_type": "request_unavailable",
            }
            return result
        try:
            from openai_codex.generated.v2_all import ConfigReadResponse
        except (ImportError, AttributeError) as exc:
            result["effective_config"] = {
                "status": "unavailable",
                "error_type": type(exc).__name__,
            }
            return result

        config = await _safe_request(
            request,
            "config/read",
            {"cwd": str(project_root), "includeLayers": False},
            ConfigReadResponse,
        )
        if config.get("status") == "available":
            result["effective_config"] = {
                "status": "available",
                "data": _effective_config(config.get("data")),
            }
        else:
            result["effective_config"] = config
        return result
    except Exception as exc:
        result.setdefault("runtime", None)
        result.setdefault("tool_inventory", {})
        result.setdefault(
            "effective_config",
            {"status": "unavailable", "error_type": type(exc).__name__},
        )
        return result
    finally:
        try:
            await adapter.close()
        except Exception:
            pass


async def collect_native_context(project_root: Path) -> dict[str, Any]:
    """Collect read-only Codex context without purchasing any model turn."""
    from .agent import ROOM_MODEL, ROOM_REASONING_EFFORT

    native_base = await _collect_native_base(project_root)
    room = await _collect_room_context(project_root)
    return {
        "native_base": native_base,
        "room": room,
        "room_defaults": {
            "model": ROOM_MODEL,
            "reasoning_effort": ROOM_REASONING_EFFORT,
        },
    }


def _snapshot_path(run_root: Path, label: str) -> Path:
    if not _CONTEXT_LABEL_RE.fullmatch(label):
        raise ValueError(
            "PBM context label may contain only letters, digits, dot, underscore, and hyphen"
        )
    return run_root / "context" / f"{label}.json"


async def capture_snapshot(
    *,
    run_root: Path,
    label: str,
    project_root: Path,
    captured_at: str,
    if_missing: bool = False,
) -> dict[str, Any]:
    path = _snapshot_path(run_root, label)
    if if_missing and path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))

    run_meta = json.loads((run_root / "run.json").read_text(encoding="utf-8"))
    native = await collect_native_context(project_root)
    payload = {
        "schema": "pbm-context-snapshot-v2",
        "run_id": run_meta["run_id"],
        "benchmark_version": run_meta["benchmark_version"],
        "benchmark_fingerprint": run_meta["benchmark_fingerprint"],
        "label": label,
        "captured_at": captured_at,
        "repository": repository_context(project_root),
        "environment": environment_context(project_root),
        "native_codex": native,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload



def _protocol_snapshot(run_root: Path, label: str) -> dict[str, Any] | None:
    path = _snapshot_path(run_root, label)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _available_section_data(value: Any) -> tuple[str, dict[str, Any] | None]:
    if not isinstance(value, dict):
        return "unavailable", None
    status = str(value.get("status") or "unavailable")
    data = value.get("data")
    return status, data if isinstance(data, dict) else None


def _rate_limit_windows(value: Any) -> list[dict[str, Any]]:
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


def _account_usage_view(value: Any) -> dict[str, Any]:
    status, data = _available_section_data(value)
    result: dict[str, Any] = {"status": status}
    if status != "available" or data is None:
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
            {
                "start_date": item.get("startDate"),
                "tokens": item.get("tokens"),
            }
            for item in buckets
            if isinstance(item, dict)
        ]
    return result


def _usage_meter_view(snapshot: dict[str, Any] | None) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    native = snapshot.get("native_codex") or {}
    base = native.get("native_base") or {}
    rate_status = (
        str((base.get("rate_limits") or {}).get("status") or "unavailable")
        if isinstance(base, dict)
        else "unavailable"
    )
    rate_data = (
        (base.get("rate_limits") or {}).get("data")
        if isinstance(base, dict) and isinstance(base.get("rate_limits"), dict)
        else None
    )
    return {
        "captured_at": snapshot.get("captured_at"),
        "rate_limits": {
            "status": rate_status,
            "ordinary_usage_allowed": (
                rate_data.get("ordinaryUsageAllowed")
                if isinstance(rate_data, dict)
                else None
            ),
            "windows": _rate_limit_windows(
                base.get("rate_limits") if isinstance(base, dict) else None
            ),
        },
        "account_usage": _account_usage_view(
            base.get("account_usage") if isinstance(base, dict) else None
        ),
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


def _usage_meter_delta(
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


def protocol_usage_meter_summary(run_root: Path) -> dict[str, Any]:
    """Summarize the provider meter at PBM protocol start and completion."""

    before = _usage_meter_view(_protocol_snapshot(run_root, "protocol-start"))
    after = _usage_meter_view(_protocol_snapshot(run_root, "protocol-complete"))
    return {
        "before": before,
        "after": after,
        "delta": _usage_meter_delta(before, after),
    }



def context_summary(run_root: Path) -> dict[str, Any]:
    context_dir = run_root / "context"
    if not context_dir.is_dir():
        return {
            "snapshot_count": 0,
            "labels": [],
            "run_start": None,
            "run_end": None,
        }
    snapshots: list[dict[str, Any]] = []
    for path in sorted(context_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        snapshots.append(payload)

    by_label = {item.get("label"): item for item in snapshots}
    def availability(item: dict[str, Any] | None) -> dict[str, Any] | None:
        if not item:
            return None
        native = item.get("native_codex") or {}
        base = native.get("native_base") or {}
        room = native.get("room") or {}
        return {
            "captured_at": item.get("captured_at"),
            "repository_head": (item.get("repository") or {}).get("head"),
            "working_tree_clean": (item.get("repository") or {}).get("working_tree_clean"),
            "native_runtime": base.get("runtime"),
            "room_runtime": room.get("runtime"),
            "openai_codex_package_version": (
                item.get("environment") or {}
            ).get("openai_codex_package_version"),
            "rate_limits_status": (base.get("rate_limits") or {}).get("status"),
            "account_usage_status": (base.get("account_usage") or {}).get("status"),
        }

    return {
        "snapshot_count": len(snapshots),
        "labels": sorted(str(item.get("label")) for item in snapshots if item.get("label")),
        "run_start": availability(by_label.get("run-start")),
        "run_end": availability(by_label.get("run-end")),
    }
