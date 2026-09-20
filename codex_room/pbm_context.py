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
    keys = (
        "model",
        "model_reasoning_effort",
        "approval_policy",
        "sandbox_mode",
        "web_search",
    )
    return {key: sanitize(config.get(key)) for key in keys if key in config}


async def collect_native_context(project_root: Path) -> dict[str, Any]:
    """Collect read-only Codex account/runtime/config/tool context without model turns."""
    from .agent import CodexAgentAdapter, ROOM_MODEL, ROOM_REASONING_EFFORT

    adapter = CodexAgentAdapter()
    result: dict[str, Any] = {
        "room_defaults": {
            "model": ROOM_MODEL,
            "reasoning_effort": ROOM_REASONING_EFFORT,
        }
    }
    try:
        account = await adapter.initialize()
        result["account"] = {"status": "available", "data": sanitize(account)}
        result["tool_inventory"] = await adapter.inspect_tools(project_root)

        sdk_client = getattr(adapter, "_client", None)
        low_level = getattr(sdk_client, "_client", None)
        request = getattr(low_level, "request", None)
        if not callable(request):
            result["rate_limits"] = {
                "status": "unavailable",
                "error_type": "request_unavailable",
            }
            result["account_usage"] = {
                "status": "unavailable",
                "error_type": "request_unavailable",
            }
            result["effective_config"] = {
                "status": "unavailable",
                "error_type": "request_unavailable",
            }
            return result

        try:
            from openai_codex.generated.v2_all import (
                ConfigReadResponse,
                GetAccountRateLimitsResponse,
                GetAccountTokenUsageResponse,
            )
        except (ImportError, AttributeError) as exc:
            error_type = type(exc).__name__
            result["rate_limits"] = {"status": "unavailable", "error_type": error_type}
            result["account_usage"] = {"status": "unavailable", "error_type": error_type}
            result["effective_config"] = {"status": "unavailable", "error_type": error_type}
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
        result.setdefault("tool_inventory", {})
        return result
    finally:
        try:
            await adapter.close()
        except Exception:
            pass


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
        return {
            "captured_at": item.get("captured_at"),
            "repository_head": (item.get("repository") or {}).get("head"),
            "working_tree_clean": (item.get("repository") or {}).get("working_tree_clean"),
            "runtime": ((native.get("account") or {}).get("data") or {}).get("runtime"),
            "openai_codex_package_version": (
                item.get("environment") or {}
            ).get("openai_codex_package_version"),
            "rate_limits_status": (native.get("rate_limits") or {}).get("status"),
            "account_usage_status": (native.get("account_usage") or {}).get("status"),
        }

    return {
        "snapshot_count": len(snapshots),
        "labels": sorted(str(item.get("label")) for item in snapshots if item.get("label")),
        "run_start": availability(by_label.get("run-start")),
        "run_end": availability(by_label.get("run-end")),
    }
