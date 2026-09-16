from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .source_inspection import SourceInspectionError, inspect_source


def _semantic_to_source_request(request: dict[str, Any]) -> dict[str, Any]:
    operation = str(request["operation"]).lower()
    source_request: dict[str, Any] = {
        "operation": operation,
        "source": request["source"],
        "path": request["path"],
    }
    if request.get("room_id") is not None:
        source_request["room_id"] = request["room_id"]

    if operation == "read":
        source_request["start_line"] = request.get("start_line") or 1
        source_request["max_lines"] = request.get("max_lines") or 400
    elif operation == "search":
        source_request["query"] = request["query"]
        source_request["max_matches"] = request.get("max_results") or 50
    elif operation == "find":
        if request.get("patterns"):
            source_request["include_globs"] = list(request["patterns"])
        source_request["max_results"] = request.get("max_results") or 100
    else:
        raise ValueError(f"unsupported semantic evidence operation: {operation}")
    return source_request


def _same(items: list[dict[str, Any]], field: str) -> bool:
    return len({item.get(field) for item in items}) <= 1


def _execution_plan(requests: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    source_requests = [_semantic_to_source_request(item) for item in requests]
    if len(source_requests) == 1:
        return source_requests[0]["operation"], source_requests[0]

    if (
        all(item["operation"] == "read" for item in source_requests)
        and _same(source_requests, "source")
        and _same(source_requests, "room_id")
    ):
        plan: dict[str, Any] = {
            "operation": "read_many",
            "source": source_requests[0]["source"],
            "reads": [
                {
                    "path": item["path"],
                    "start_line": item["start_line"],
                    "max_lines": item["max_lines"],
                }
                for item in source_requests
            ],
        }
        if source_requests[0].get("room_id") is not None:
            plan["room_id"] = source_requests[0]["room_id"]
        return "read_many", plan

    queries = [item.get("query") for item in source_requests]
    if (
        all(item["operation"] == "search" for item in source_requests)
        and _same(source_requests, "source")
        and _same(source_requests, "room_id")
        and _same(source_requests, "path")
        and _same(source_requests, "max_matches")
        and len(queries) == len(set(queries))
    ):
        plan = {
            "operation": "search_many",
            "source": source_requests[0]["source"],
            "path": source_requests[0]["path"],
            "queries": queries,
            "max_matches": source_requests[0]["max_matches"],
        }
        if source_requests[0].get("room_id") is not None:
            plan["room_id"] = source_requests[0]["room_id"]
        return "search_many", plan

    return (
        "bundle",
        {
            "operation": "bundle",
            "requests": [
                {"label": f"request-{index + 1}", "request": item}
                for index, item in enumerate(source_requests)
            ],
        },
    )


def _normalize_direct(
    request: dict[str, Any], result: dict[str, Any]
) -> list[dict[str, Any]]:
    item: dict[str, Any] = {
        "request_index": 0,
        "operation": request["operation"],
        "source": request["source"],
        "path": request["path"],
        "evidence": result["evidence"],
    }
    if request["operation"] == "READ":
        item["content"] = result.get("content", "")
    elif request["operation"] == "SEARCH":
        item["matches"] = result.get("matches", [])
    else:
        item["matches"] = result["evidence"].get("matches", [])
    return [item]


def _normalize_many(
    requests: list[dict[str, Any]],
    strategy: str,
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if strategy == "read_many":
        transient = result.get("reads", [])
        durable = result["evidence"].get("reads", [])
        for index, (request, read) in enumerate(zip(requests, transient, strict=False)):
            items.append(
                {
                    "request_index": index,
                    "operation": "READ",
                    "source": request["source"],
                    "path": request["path"],
                    "content": read.get("content", ""),
                    "evidence": durable[index] if index < len(durable) else {},
                }
            )
        return items

    if strategy == "search_many":
        transient = result.get("results", [])
        durable = result["evidence"].get("queries", [])
        for index, (request, search) in enumerate(zip(requests, transient, strict=False)):
            items.append(
                {
                    "request_index": index,
                    "operation": "SEARCH",
                    "source": request["source"],
                    "path": request["path"],
                    "matches": search.get("matches", []),
                    "evidence": durable[index] if index < len(durable) else {},
                }
            )
        return items

    by_label = {
        item.get("label"): item for item in result.get("items", []) if item.get("label")
    }
    for index, request in enumerate(requests):
        raw = by_label.get(f"request-{index + 1}")
        if raw is None:
            continue
        item = {
            "request_index": index,
            "operation": request["operation"],
            "source": request["source"],
            "path": request["path"],
            "evidence": raw.get("evidence", {}),
        }
        if request["operation"] == "READ":
            item["content"] = raw.get("content", "")
        else:
            item["matches"] = raw.get("matches", raw.get("evidence", {}).get("matches", []))
        items.append(item)
    return items


def durable_evidence_requests(
    requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return provenance-safe descriptors without retaining raw search/pattern text."""
    durable: list[dict[str, Any]] = []
    for request in requests:
        canonical = json.dumps(
            request,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        item: dict[str, Any] = {
            "operation": request["operation"],
            "source": request["source"],
            "path": request["path"],
            "request_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        }
        if request.get("room_id") is not None:
            item["room_id"] = request["room_id"]
        if request["operation"] == "READ":
            item["start_line"] = request.get("start_line") or 1
            item["max_lines"] = request.get("max_lines") or 400
        elif request["operation"] == "SEARCH":
            query = request["query"]
            item["query_sha256"] = hashlib.sha256(query.encode("utf-8")).hexdigest()
            item["query_length"] = len(query)
            item["max_results"] = request.get("max_results") or 50
        else:
            patterns = request.get("patterns") or []
            patterns_json = json.dumps(
                patterns,
                ensure_ascii=True,
                separators=(",", ":"),
            )
            item["patterns_sha256"] = hashlib.sha256(
                patterns_json.encode("utf-8")
            ).hexdigest()
            item["pattern_count"] = len(patterns)
            item["max_results"] = request.get("max_results") or 100
        durable.append(item)
    return durable


def execute_source_evidence(
    workspace: Path, requests: list[dict[str, Any]]
) -> dict[str, Any]:
    """Execute bounded semantic source evidence without exposing transport mechanics."""
    strategy, plan = _execution_plan(requests)
    durable_requests = durable_evidence_requests(requests)
    try:
        result = inspect_source(workspace, plan)
    except (SourceInspectionError, ValueError) as exc:
        error = " ".join(str(exc).split())[:1000]
        return {
            "ok": False,
            "strategy": strategy,
            "durable_requests": durable_requests,
            "durable": {"ok": False, "error": error},
            "payload": {"ok": False, "error": error, "items": []},
        }

    if len(requests) == 1:
        items = _normalize_direct(requests[0], result)
    else:
        items = _normalize_many(requests, strategy, result)
    durable = result["evidence"]
    return {
        "ok": bool(result.get("ok")),
        "strategy": strategy,
        "durable_requests": durable_requests,
        "durable": durable,
        "payload": {
            "ok": bool(result.get("ok")),
            "items": items,
            "truncated": bool(durable.get("truncated", False)),
            "truncation_reason": durable.get("truncation_reason"),
        },
    }
