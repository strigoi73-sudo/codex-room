from __future__ import annotations

from typing import Any


AVAILABLE = "available"
INTERACTION_REQUIRED = "interaction_required"
UNAVAILABLE = "unavailable"
UNKNOWN = "unknown"
_ITEM_LIMIT = 25
_ASSIGNMENT_TEXT_LIMIT = 360


def _category(
    status: str,
    summary: str,
    *,
    items: list[dict[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "status": status,
        "summary": summary,
        "items": items or [],
        **extra,
    }


def _compact_text(value: Any, limit: int = _ASSIGNMENT_TEXT_LIMIT) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _enum_value(value: Any) -> Any:
    raw = getattr(value, "value", value)
    return raw if isinstance(raw, (str, int, float, bool)) or raw is None else str(raw)


def _status_rollup(items: list[dict[str, Any]]) -> str:
    statuses = {item.get("status") for item in items}
    if AVAILABLE in statuses:
        return AVAILABLE
    if INTERACTION_REQUIRED in statuses:
        return INTERACTION_REQUIRED
    if UNKNOWN in statuses:
        return UNKNOWN
    return UNAVAILABLE


def summarize_codex_tool_inventory(
    payloads: dict[str, dict[str, Any] | None],
) -> dict[str, dict[str, Any]]:
    """Sanitize and classify read-only App Server tool inventory results."""
    provider = payloads.get("provider")
    config = payloads.get("config")
    if provider is None:
        web = _category(UNKNOWN, "Web-search capability could not be inspected.")
    elif not bool(provider.get("webSearch")):
        web = _category(
            UNAVAILABLE,
            "The active model provider reports that web search is unavailable.",
        )
    elif config is None:
        web = _category(
            UNKNOWN,
            "The provider supports web search, but effective Room configuration could not be inspected.",
        )
    else:
        web_mode = (config.get("config") or {}).get("web_search")
        if web_mode == "disabled":
            web = _category(
                UNAVAILABLE,
                "Web search is disabled by effective Codex configuration.",
                mode="disabled",
            )
        else:
            web = _category(
                AVAILABLE,
                (
                    f"Web search is available in {web_mode} mode."
                    if web_mode
                    else "Web search is supported and not disabled by effective configuration."
                ),
                mode=web_mode or "default",
            )

    skills_payload = payloads.get("skills")
    if skills_payload is None:
        skills = _category(UNKNOWN, "Skill inventory could not be inspected.")
    else:
        raw_skills: list[dict[str, Any]] = []
        error_count = 0
        for entry in skills_payload.get("data") or []:
            error_count += len(entry.get("errors") or [])
            raw_skills.extend(entry.get("skills") or [])
        deduped: dict[tuple[str, str], dict[str, Any]] = {}
        for item in raw_skills:
            name = str(item.get("name") or "Unnamed skill")
            scope = str(_enum_value(item.get("scope")) or "unknown")
            deduped[(name, scope)] = {
                "name": name,
                "scope": scope,
                "enabled": bool(item.get("enabled")),
            }
        skill_items = list(deduped.values())
        enabled_count = sum(1 for item in skill_items if item["enabled"])
        skill_status = AVAILABLE if enabled_count else UNAVAILABLE
        summary = (
            f"{enabled_count} enabled skill(s) out of {len(skill_items)} discovered."
            if skill_items
            else "No skills are available for this Room workspace."
        )
        if error_count and not skill_items:
            skill_status = UNKNOWN
            summary = "Skill discovery reported errors and returned no usable inventory."
        skills = _category(
            skill_status,
            summary,
            items=skill_items[:_ITEM_LIMIT],
            total_count=len(skill_items),
            enabled_count=enabled_count,
            discovery_error_count=error_count,
            truncated=len(skill_items) > _ITEM_LIMIT,
        )

    mcp_payload = payloads.get("mcp")
    if mcp_payload is None:
        mcp = _category(UNKNOWN, "MCP server inventory could not be inspected.")
    else:
        mcp_items: list[dict[str, Any]] = []
        for raw in mcp_payload.get("data") or []:
            auth = str(_enum_value(raw.get("authStatus")) or "unknown")
            tools = raw.get("tools") or {}
            tool_count = len(tools) if isinstance(tools, dict) else 0
            if auth == "notLoggedIn":
                item_status = INTERACTION_REQUIRED
            elif tool_count and auth in {"bearerToken", "oAuth", "unsupported"}:
                item_status = AVAILABLE
            elif tool_count:
                item_status = UNKNOWN
            else:
                item_status = UNAVAILABLE
            mcp_items.append(
                {
                    "name": str(raw.get("name") or "Unnamed MCP server"),
                    "status": item_status,
                    "auth_status": auth,
                    "tool_count": tool_count,
                }
            )
        truncated = bool(mcp_payload.get("nextCursor"))
        status = _status_rollup(mcp_items)
        if not mcp_items:
            status = UNKNOWN if truncated else UNAVAILABLE
        elif status == UNAVAILABLE and truncated:
            status = UNKNOWN
        available_count = sum(1 for item in mcp_items if item["status"] == AVAILABLE)
        auth_count = sum(
            1 for item in mcp_items if item["status"] == INTERACTION_REQUIRED
        )
        mcp = _category(
            status,
            (
                f"{available_count} MCP server(s) expose usable tools; "
                f"{auth_count} require authentication."
                if mcp_items
                else "No configured MCP servers were reported."
            ),
            items=mcp_items[:_ITEM_LIMIT],
            total_count=len(mcp_items),
            available_count=available_count,
            interaction_required_count=auth_count,
            truncated=truncated or len(mcp_items) > _ITEM_LIMIT,
        )

    apps_payload = payloads.get("apps")
    if apps_payload is None:
        apps = _category(UNKNOWN, "Installed app inventory could not be inspected.")
    else:
        app_items: list[dict[str, Any]] = []
        for index, raw in enumerate(apps_payload.get("apps") or [], start=1):
            enabled = bool(raw.get("enabled"))
            callable_ = bool(raw.get("callable"))
            item_status = AVAILABLE if callable_ else UNKNOWN if enabled else UNAVAILABLE
            app_items.append(
                {
                    "name": str(raw.get("runtimeName") or f"Installed app {index}"),
                    "status": item_status,
                    "enabled": enabled,
                    "callable": callable_,
                }
            )
        apps = _category(
            _status_rollup(app_items) if app_items else UNAVAILABLE,
            (
                f"{sum(1 for item in app_items if item['callable'])} callable installed app(s) "
                f"out of {len(app_items)}."
                if app_items
                else "No installed apps were reported by the active runtime."
            ),
            items=app_items[:_ITEM_LIMIT],
            total_count=len(app_items),
            callable_count=sum(1 for item in app_items if item["callable"]),
            truncated=len(app_items) > _ITEM_LIMIT,
        )

    plugins_payload = payloads.get("plugins")
    if plugins_payload is None:
        plugins = _category(UNKNOWN, "Installed plugin inventory could not be inspected.")
    else:
        marketplace_errors = len(plugins_payload.get("marketplaceLoadErrors") or [])
        installed: dict[str, dict[str, Any]] = {}
        for marketplace in plugins_payload.get("marketplaces") or []:
            for raw in marketplace.get("plugins") or []:
                if not raw.get("installed"):
                    continue
                name = str(raw.get("name") or "Unnamed plugin")
                availability = str(_enum_value(raw.get("availability")) or "unknown")
                enabled = bool(raw.get("enabled"))
                if enabled and availability == "AVAILABLE":
                    item_status = AVAILABLE
                elif availability == "DISABLED_BY_ADMIN" or not enabled:
                    item_status = UNAVAILABLE
                else:
                    item_status = UNKNOWN
                installed[name] = {
                    "name": name,
                    "status": item_status,
                    "enabled": enabled,
                    "availability": availability,
                    "auth_policy": str(_enum_value(raw.get("authPolicy")) or "unknown"),
                }
        plugin_items = list(installed.values())
        status = _status_rollup(plugin_items) if plugin_items else UNAVAILABLE
        if marketplace_errors and not plugin_items:
            status = UNKNOWN
        plugins = _category(
            status,
            (
                f"{sum(1 for item in plugin_items if item['status'] == AVAILABLE)} enabled installed "
                f"plugin(s) out of {len(plugin_items)}."
                if plugin_items
                else "No installed plugins were reported."
            ),
            items=plugin_items[:_ITEM_LIMIT],
            total_count=len(plugin_items),
            marketplace_error_count=marketplace_errors,
            truncated=len(plugin_items) > _ITEM_LIMIT,
        )

    return {
        "workspace_files": _category(
            AVAILABLE,
            "Room agents have read/write access inside the shared Room workspace sandbox.",
        ),
        "command_execution": _category(
            AVAILABLE,
            "Local command execution is part of the inherited Codex runtime, subject to Room sandbox and approval policy.",
        ),
        "web_search": web,
        "skills": skills,
        "mcp": mcp,
        "apps": apps,
        "plugins": plugins,
    }


def summarize_capabilities(registry: dict[str, Any]) -> list[dict[str, Any]]:
    capabilities = []
    for item in registry.get("capabilities") or []:
        capabilities.append(
            {
                "id": item.get("id"),
                "description": item.get("description"),
                "origin": item.get("origin"),
                "scope": item.get("scope"),
                "version": item.get("version"),
            }
        )
    return capabilities


def summarize_command_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    if catalog.get("status") != "current":
        return {
            "status": UNKNOWN,
            "summary": "The exact-runtime command catalog is unavailable.",
            "runtime_version": catalog.get("runtime_version"),
            "command_count": 0,
        }
    count = int(catalog.get("command_count") or 0)
    return {
        "status": AVAILABLE,
        "summary": f"{count} exact-runtime built-in command(s) synchronized.",
        "runtime_version": catalog.get("runtime_version"),
        "command_count": count,
        "source_ref": catalog.get("source_ref"),
        "source_blob_sha": catalog.get("source_blob_sha"),
        "dynamic_overlays": catalog.get("dynamic_overlays") or [],
    }


def _latest_economics(room: dict[str, Any]) -> dict[str, dict[str, Any]]:
    agents = {item.get("agent_key") for item in room.get("agents") or []}
    latest: dict[str, dict[str, Any]] = {}
    for event in reversed(room.get("events") or []):
        source = event.get("source")
        if (
            source not in agents
            or source in latest
            or event.get("event_type") != "execution_economics"
        ):
            continue
        metadata = event.get("metadata") or {}
        latest[source] = {
            "created_at": event.get("created_at"),
            "tool_calls": metadata.get("tool_calls"),
            "failed_tool_calls": metadata.get("failed_tool_calls"),
            "peer_invocations": metadata.get("peer_invocations"),
            "usage_delta_status": metadata.get("usage_delta_status"),
            "usage_delta": {
                key: value
                for key, value in (metadata.get("usage_delta") or {}).items()
                if isinstance(value, (int, float))
            },
        }
    return latest


def summarize_room_status(
    room: dict[str, Any],
    *,
    coordinator_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_round = room.get("active_round")
    task = None
    assignments: list[dict[str, Any]] = []
    if active_round:
        tasks = ((active_round.get("transaction_state") or {}).get("tasks") or [])
        if tasks:
            task = next(
                (
                    candidate
                    for candidate in reversed(tasks)
                    if candidate.get("state") not in {"settled", "failed", "cancelled"}
                ),
                tasks[-1],
            )
            assignments = [
                {
                    "id": item.get("id"),
                    "agent_key": item.get("agent_key"),
                    "state": item.get("state"),
                    "instruction": _compact_text(item.get("instruction")),
                    "parent_assignment_id": item.get("parent_assignment_id"),
                }
                for item in task.get("assignments") or []
            ]

    agents = []
    for agent in room.get("agents") or []:
        execution = agent.get("execution") or {}
        agents.append(
            {
                "agent_key": agent.get("agent_key"),
                "name": agent.get("name"),
                "status": agent.get("status"),
                "work_state": execution.get("phase"),
                "execution_health": execution.get("health"),
                "pending_count": execution.get("pending_count", 0),
                "processing_count": execution.get("processing_count", 0),
                "model": execution.get("model"),
                "reasoning_effort": execution.get("reasoning_effort"),
                "model_recency": execution.get("model_recency"),
            }
        )

    return {
        "room": {
            "id": room.get("id"),
            "title": room.get("title"),
            "status": room.get("status"),
            "turn_count": room.get("turn_count"),
            "max_turns": room.get("max_turns"),
        },
        "round": (
            {
                "id": active_round.get("id"),
                "title": active_round.get("title"),
                "status": active_round.get("status"),
                "objective": active_round.get("prompt"),
                "completion_policy": active_round.get("completion_policy"),
                "turn_count": active_round.get("turn_count"),
            }
            if active_round
            else None
        ),
        "task": (
            {
                "id": task.get("id"),
                "state": task.get("state"),
                "required_contributors": task.get("required_contributors") or [],
                "c_cognition_ceiling": task.get("c_cognition_ceiling"),
                "assignments": assignments,
            }
            if task
            else None
        ),
        "agents": agents,
        "recent_economics": _latest_economics(room),
        "coordinator_context": coordinator_context,
    }


def build_status_tools_payload(
    room: dict[str, Any],
    *,
    coordinator_context: dict[str, Any] | None,
    capability_registry: dict[str, Any],
    inherited_tools: dict[str, Any],
    command_catalog: dict[str, Any],
    runtime_identity: dict[str, Any] | None,
) -> dict[str, Any]:
    runtime = runtime_identity if isinstance(runtime_identity, dict) else {}
    return {
        "work": summarize_room_status(
            room,
            coordinator_context=coordinator_context,
        ),
        "room_capabilities": summarize_capabilities(capability_registry),
        "codex": {
            "runtime": {
                "name": runtime.get("name"),
                "version": runtime.get("version"),
            },
            "commands": summarize_command_catalog(command_catalog),
            "tools": inherited_tools,
        },
    }
