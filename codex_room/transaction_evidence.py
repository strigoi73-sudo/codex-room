from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import SourceEvidenceRequest
from .source_inspection import (
    MAX_BATCH_READ_OUTPUT_BYTES,
    MAX_EVIDENCE_BUNDLE_OUTPUT_BYTES,
    SourceInspectionError,
    inspect_source,
)


@dataclass(frozen=True, slots=True)
class SourceEvidenceExecution:
    plan: dict[str, Any]
    result: dict[str, Any]
    durable_result: dict[str, Any]


def _atomic_request(request: SourceEvidenceRequest) -> dict[str, Any]:
    common: dict[str, Any] = {
        "source": request.source,
        "path": request.path,
    }
    if request.room_id is not None:
        common["room_id"] = request.room_id

    if request.operation == "READ":
        return {
            "operation": "read",
            **common,
            "start_line": request.start_line,
            "max_lines": request.max_lines,
            "max_bytes": request.max_bytes,
        }
    if request.operation == "SEARCH":
        return {
            "operation": "search",
            **common,
            "query": request.query,
            "include_globs": request.include_globs,
            "exclude_globs": request.exclude_globs,
            "include_hidden": request.include_hidden,
            "case_sensitive": request.case_sensitive,
            "max_files": request.max_files,
            "max_matches": request.max_matches,
        }
    if request.operation == "FIND":
        return {
            "operation": "find",
            **common,
            "include_globs": request.include_globs,
            "exclude_globs": request.exclude_globs,
            "include_hidden": request.include_hidden,
            "max_results": request.max_results,
        }
    raise ValueError(f"Unsupported source evidence operation: {request.operation}")


def plan_source_evidence(
    requests: list[SourceEvidenceRequest],
) -> dict[str, Any]:
    if not requests:
        raise ValueError("At least one source evidence request is required")
    atomic = [_atomic_request(item) for item in requests]
    if len(atomic) == 1:
        return atomic[0]

    if all(item["operation"] == "read" for item in atomic):
        source_keys = {(item["source"], item.get("room_id")) for item in atomic}
        if len(source_keys) == 1:
            source, room_id = next(iter(source_keys))
            plan: dict[str, Any] = {
                "operation": "read_many",
                "source": source,
                "reads": [
                    {
                        "path": item["path"],
                        "start_line": item["start_line"],
                        "max_lines": item["max_lines"],
                        "max_bytes": item["max_bytes"],
                    }
                    for item in atomic
                ],
                "max_bytes": MAX_BATCH_READ_OUTPUT_BYTES,
            }
            if room_id is not None:
                plan["room_id"] = room_id
            return plan

    if all(item["operation"] == "search" for item in atomic):
        shared_keys = (
            "source",
            "room_id",
            "path",
            "include_globs",
            "exclude_globs",
            "include_hidden",
            "case_sensitive",
            "max_files",
            "max_matches",
        )
        first = atomic[0]
        if all(
            all(item.get(key) == first.get(key) for key in shared_keys)
            for item in atomic[1:]
        ):
            plan = {
                "operation": "search_many",
                "source": first["source"],
                "path": first["path"],
                "queries": [item["query"] for item in atomic],
                "include_globs": first["include_globs"],
                "exclude_globs": first["exclude_globs"],
                "include_hidden": first["include_hidden"],
                "case_sensitive": first["case_sensitive"],
                "max_files": first["max_files"],
                "max_matches": first["max_matches"],
            }
            if first.get("room_id") is not None:
                plan["room_id"] = first["room_id"]
            return plan

    return {
        "operation": "bundle",
        "requests": [
            {"label": f"evidence-{index + 1}", "request": request}
            for index, request in enumerate(atomic)
        ],
        "max_bytes": MAX_EVIDENCE_BUNDLE_OUTPUT_BYTES,
    }


def execute_source_evidence(
    workspace: Path,
    requests: list[SourceEvidenceRequest],
) -> SourceEvidenceExecution:
    plan = plan_source_evidence(requests)
    try:
        result = inspect_source(workspace, plan)
    except SourceInspectionError as exc:
        result = {
            "codex_room_capability": 1,
            "capability": "inspect_source",
            "ok": False,
            "error": {
                "type": "invalid_source_evidence",
                "message": str(exc),
            },
        }
    durable_result: dict[str, Any] = {
        "codex_room_capability": result.get("codex_room_capability", 1),
        "capability": result.get("capability", "inspect_source"),
        "ok": bool(result.get("ok")),
    }
    if "evidence" in result:
        durable_result["evidence"] = result["evidence"]
    if "error" in result:
        durable_result["error"] = result["error"]
    return SourceEvidenceExecution(
        plan=plan,
        result=result,
        durable_result=durable_result,
    )
