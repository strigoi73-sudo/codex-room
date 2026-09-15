from __future__ import annotations

import argparse
import difflib
import hashlib
import inspect
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from .custom_capabilities import MAX_ENTRYPOINT_BYTES, MAX_MANIFEST_BYTES
from .custom_capability_registration import (
    MAX_CASE_JSON_BYTES,
    MAX_FIXTURE_FILES,
    MAX_FIXTURE_FILE_BYTES,
    MAX_FIXTURE_TOTAL_BYTES,
    MAX_VERIFICATION_CASES,
    CustomCapabilityVerificationError,
    verify_custom_capability_draft,
)
from .custom_registry import (
    CustomCapabilityRegistryError,
    invoke_bound_custom_capability,
    load_room_custom_capabilities,
    resolve_room_capability_context,
)
from .source_inspection import (
    INSPECT_SOURCE_IMPLEMENTATION_COMPONENTS,
    INSPECT_SOURCE_INPUT_SCHEMA,
    INSPECT_SOURCE_OUTPUT_SCHEMA,
    SourceInspectionError,
    inspect_source,
)

CAPABILITY_MARKER = 1
REGISTRY_MARKER = 1
MAX_JSON_BYTES = 50 * 1024 * 1024
MAX_INVOCATION_INPUT_FILE_BYTES = 1024 * 1024
MAX_FIND_FILES_RESULTS = 200
DEFAULT_FIND_FILES_RESULTS = 100
MAX_FIND_FILES_SCANNED_ENTRIES = 100_000
MAX_FIND_FILES_MATCH_BYTES = 48 * 1024
MAX_SEARCH_TEXT_FILES = 200
DEFAULT_SEARCH_TEXT_FILES = 100
MAX_SEARCH_TEXT_MATCHES = 100
DEFAULT_SEARCH_TEXT_MATCHES = 50
DEFAULT_SEARCH_TEXT_FILE_BYTES = 2 * 1024 * 1024
MAX_SEARCH_TEXT_FILE_BYTES = 10 * 1024 * 1024
MAX_SEARCH_TEXT_TOTAL_BYTES = 20 * 1024 * 1024
MAX_SEARCH_TEXT_MATCH_BYTES = 32 * 1024
MAX_SEARCH_TEXT_LOCATION_BYTES = 16 * 1024
SEARCH_TEXT_EXCERPT_CHARS = 240
MAX_SEARCH_TEXT_QUERY_CHARS = 4096
MAX_COMPARE_FILE_BYTES = 50 * 1024 * 1024
MAX_COMPARE_TEXT_BYTES = 2 * 1024 * 1024
MAX_COMPARE_TEXT_LINES = 20_000
MAX_COMPARE_DIFF_LINES = 200
MAX_COMPARE_DIFF_BYTES = 32 * 1024
DEFAULT_COMPARE_CONTEXT_LINES = 3
MAX_COMPARE_CONTEXT_LINES = 10
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class CapabilityUsageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CapabilitySpec:
    capability_id: str
    description: str
    origin: str
    scope: str
    version: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    durable_result_fields: tuple[str, ...]
    permissions: dict[str, bool]
    side_effects: str
    verification: dict[str, Any]
    handler: Callable[[Path, dict[str, Any]], dict[str, Any]]
    implementation_components: tuple[Any, ...]

    def implementation_sha256(self) -> str:
        digest = hashlib.sha256()
        digest.update(f"{self.capability_id}\n{self.version}\n".encode("utf-8"))
        digest.update(
            json.dumps(
                self.durable_result_fields,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
        for component in self.implementation_components:
            if callable(component):
                text = inspect.getsource(component)
            else:
                text = repr(component)
            digest.update(text.encode("utf-8"))
            digest.update(b"\n")
        return digest.hexdigest()

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.capability_id,
            "description": self.description,
            "origin": self.origin,
            "scope": self.scope,
            "version": self.version,
            "implementation_sha256": self.implementation_sha256(),
            "inspect": f"codex-room-cap inspect {self.capability_id}",
        }

    def manifest(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "durable_result_fields": list(self.durable_result_fields),
            "permissions": self.permissions,
            "side_effects": self.side_effects,
            "verification": self.verification,
            "invocation": {
                "inspect": f"codex-room-cap inspect {self.capability_id}",
                "invoke": (
                    f"codex-room-cap invoke {self.capability_id} "
                    "--input-json JSON_OBJECT"
                ),
                "invoke_file": (
                    f"codex-room-cap invoke {self.capability_id} "
                    "--input-file WORKSPACE_RELATIVE_JSON"
                ),
                **(
                    {"source_cli": "codex-room-cap source --help"}
                    if self.capability_id == "inspect_source"
                    else {}
                ),
            },
        }


def _workspace_path(root: Path, raw_path: str) -> tuple[Path, str]:
    if not raw_path:
        raise CapabilityUsageError("path must not be empty")
    supplied = Path(raw_path)
    if supplied.is_absolute():
        raise CapabilityUsageError("path must be relative to the Room workspace")
    try:
        root_resolved = root.resolve()
        candidate = (root_resolved / supplied).resolve(strict=False)
    except OSError as exc:
        raise CapabilityUsageError(f"path could not be resolved: {exc}") from exc
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise CapabilityUsageError("path must stay inside the Room workspace")
    return candidate, supplied.as_posix()


def _load_invocation_input_file(root: Path, raw_path: str) -> dict[str, Any]:
    path, _ = _workspace_path(root, raw_path)
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CapabilityUsageError(f"input file could not be inspected: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CapabilityUsageError("input file must be a regular workspace file")
    if metadata.st_size > MAX_INVOCATION_INPUT_FILE_BYTES:
        raise CapabilityUsageError("input file exceeds the size limit")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CapabilityUsageError(f"input file could not be read: {exc}") from exc
    if len(raw) > MAX_INVOCATION_INPUT_FILE_BYTES:
        raise CapabilityUsageError("input file exceeds the size limit")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapabilityUsageError(
            "input file must contain one UTF-8 JSON object"
        ) from exc
    if not isinstance(value, dict):
        raise CapabilityUsageError("input file must contain one JSON object")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_glob_patterns(raw_patterns: list[str], field_name: str) -> list[str]:
    normalized: list[str] = []
    for raw in raw_patterns:
        pattern = raw.replace("\\", "/")
        while pattern.startswith("./"):
            pattern = pattern[2:]
        if (
            not pattern
            or pattern.startswith("/")
            or any(part == ".." for part in pattern.split("/"))
        ):
            raise CapabilityUsageError(
                f"find_files input '{field_name}' must contain non-empty "
                "workspace-relative glob patterns"
            )
        normalized.append(pattern)
    return normalized


def _glob_variants(pattern: str) -> tuple[str, ...]:
    variants = {pattern}
    pending = [pattern]
    while pending:
        current = pending.pop()
        search_from = 0
        while True:
            index = current.find("**/", search_from)
            if index < 0:
                break
            without_zero_depth = current[:index] + current[index + 3 :]
            if without_zero_depth not in variants:
                variants.add(without_zero_depth)
                pending.append(without_zero_depth)
            search_from = index + 1
    return tuple(sorted(variants))


def _matches_globs(relative_path: str, patterns: list[str]) -> bool:
    path = PurePosixPath(relative_path)
    return any(
        path.match(variant)
        for pattern in patterns
        for variant in _glob_variants(pattern)
    )


def _is_hidden_relative(relative_path: str) -> bool:
    return any(part.startswith(".") for part in PurePosixPath(relative_path).parts)


def find_files(
    root: Path,
    raw_path: str = ".",
    *,
    include_globs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    include_hidden: bool = False,
    min_size_bytes: int | None = None,
    max_size_bytes: int | None = None,
    max_results: int = DEFAULT_FIND_FILES_RESULTS,
) -> dict[str, Any]:
    include_globs = list(include_globs or [])
    exclude_globs = list(exclude_globs or [])
    scan_root, relative_root = _workspace_path(root, raw_path)
    if not scan_root.exists() or not scan_root.is_dir():
        raise CapabilityUsageError("find_files path must be an existing directory")

    workspace_root = root.resolve()
    matches: list[dict[str, Any]] = []
    scanned_entries = 0
    truncation_reason: str | None = None

    def raise_walk_error(exc: OSError) -> None:
        raise CapabilityUsageError(f"find_files could not scan workspace: {exc}") from exc

    for current_raw, dirs, files in os.walk(
        scan_root,
        topdown=True,
        onerror=raise_walk_error,
        followlinks=False,
    ):
        current = Path(current_raw)
        dirs.sort()
        files.sort()

        kept_dirs: list[str] = []
        for dirname in dirs:
            if scanned_entries >= MAX_FIND_FILES_SCANNED_ENTRIES:
                truncation_reason = "scan_limit"
                break
            scanned_entries += 1
            candidate = current / dirname
            relative_to_scan = candidate.relative_to(scan_root).as_posix()
            if candidate.is_symlink():
                continue
            if not include_hidden and _is_hidden_relative(relative_to_scan):
                continue
            if exclude_globs and _matches_globs(relative_to_scan, exclude_globs):
                continue
            kept_dirs.append(dirname)
        if truncation_reason is not None:
            dirs[:] = []
            break
        dirs[:] = kept_dirs

        for filename in files:
            if scanned_entries >= MAX_FIND_FILES_SCANNED_ENTRIES:
                truncation_reason = "scan_limit"
                break
            scanned_entries += 1
            candidate = current / filename
            relative_to_scan = candidate.relative_to(scan_root).as_posix()
            try:
                metadata = candidate.lstat()
            except OSError as exc:
                raise CapabilityUsageError(
                    f"find_files could not inspect '{relative_to_scan}': {exc}"
                ) from exc
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                continue
            if not include_hidden and _is_hidden_relative(relative_to_scan):
                continue
            if include_globs and not _matches_globs(relative_to_scan, include_globs):
                continue
            if exclude_globs and _matches_globs(relative_to_scan, exclude_globs):
                continue
            if min_size_bytes is not None and metadata.st_size < min_size_bytes:
                continue
            if max_size_bytes is not None and metadata.st_size > max_size_bytes:
                continue
            if len(matches) >= max_results:
                truncation_reason = "max_results"
                break
            match = {
                "path": candidate.relative_to(workspace_root).as_posix(),
                "size_bytes": metadata.st_size,
            }
            prospective_match_bytes = len(
                json.dumps(
                    [*matches, match],
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            if prospective_match_bytes > MAX_FIND_FILES_MATCH_BYTES:
                truncation_reason = "result_bytes"
                break
            matches.append(match)
        if truncation_reason is not None:
            break

    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": "find_files",
        "ok": True,
        "evidence": {
            "path": relative_root,
            "matches": matches,
            "returned_count": len(matches),
            "scanned_entries": scanned_entries,
            "scan_limit_entries": MAX_FIND_FILES_SCANNED_ENTRIES,
            "match_byte_limit": MAX_FIND_FILES_MATCH_BYTES,
            "truncated": truncation_reason is not None,
            "truncation_reason": truncation_reason,
            "ordering": "sorted_depth_first",
            "symlinks_followed": False,
        },
    }


def _invoke_find_files(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "path",
        "include_globs",
        "exclude_globs",
        "include_hidden",
        "min_size_bytes",
        "max_size_bytes",
        "max_results",
    }
    unknown = sorted(set(inputs) - allowed)
    if unknown:
        raise CapabilityUsageError(
            "unknown find_files input field(s): " + ", ".join(unknown)
        )

    raw_path = inputs.get("path", ".")
    include_globs = inputs.get("include_globs", [])
    exclude_globs = inputs.get("exclude_globs", [])
    include_hidden = inputs.get("include_hidden", False)
    min_size_bytes = inputs.get("min_size_bytes")
    max_size_bytes = inputs.get("max_size_bytes")
    max_results = inputs.get("max_results", DEFAULT_FIND_FILES_RESULTS)

    if not isinstance(raw_path, str) or not raw_path:
        raise CapabilityUsageError("find_files input 'path' must be a non-empty string")
    if not isinstance(include_globs, list) or any(
        not isinstance(pattern, str) for pattern in include_globs
    ):
        raise CapabilityUsageError(
            "find_files input 'include_globs' must be a list of strings"
        )
    if not isinstance(exclude_globs, list) or any(
        not isinstance(pattern, str) for pattern in exclude_globs
    ):
        raise CapabilityUsageError(
            "find_files input 'exclude_globs' must be a list of strings"
        )
    if not isinstance(include_hidden, bool):
        raise CapabilityUsageError(
            "find_files input 'include_hidden' must be true or false"
        )
    for field_name, value in (
        ("min_size_bytes", min_size_bytes),
        ("max_size_bytes", max_size_bytes),
    ):
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            raise CapabilityUsageError(
                f"find_files input '{field_name}' must be a non-negative integer or null"
            )
    if (
        min_size_bytes is not None
        and max_size_bytes is not None
        and min_size_bytes > max_size_bytes
    ):
        raise CapabilityUsageError(
            "find_files input 'min_size_bytes' must not exceed 'max_size_bytes'"
        )
    if (
        not isinstance(max_results, int)
        or isinstance(max_results, bool)
        or not 1 <= max_results <= MAX_FIND_FILES_RESULTS
    ):
        raise CapabilityUsageError(
            f"find_files input 'max_results' must be an integer from 1 "
            f"to {MAX_FIND_FILES_RESULTS}"
        )

    normalized_include = _normalize_glob_patterns(include_globs, "include_globs")
    normalized_exclude = _normalize_glob_patterns(exclude_globs, "exclude_globs")
    return find_files(
        root,
        raw_path,
        include_globs=normalized_include,
        exclude_globs=normalized_exclude,
        include_hidden=include_hidden,
        min_size_bytes=min_size_bytes,
        max_size_bytes=max_size_bytes,
        max_results=max_results,
    )


def _normalize_search_glob_patterns(
    raw_patterns: list[str], field_name: str
) -> list[str]:
    normalized: list[str] = []
    for raw in raw_patterns:
        pattern = raw.replace("\\", "/")
        while pattern.startswith("./"):
            pattern = pattern[2:]
        if (
            not pattern
            or pattern.startswith("/")
            or any(part == ".." for part in pattern.split("/"))
        ):
            raise CapabilityUsageError(
                f"search_text input '{field_name}' must contain non-empty "
                "workspace-relative glob patterns"
            )
        normalized.append(pattern)
    return normalized


def _search_text_excerpt(line: str, start: int, end: int) -> tuple[str, int]:
    if len(line) <= SEARCH_TEXT_EXCERPT_CHARS:
        return line, 1

    window_start = max(0, start - 80)
    window_end = min(len(line), window_start + SEARCH_TEXT_EXCERPT_CHARS)
    if end > window_end:
        window_start = max(0, end - SEARCH_TEXT_EXCERPT_CHARS)
        window_end = min(len(line), window_start + SEARCH_TEXT_EXCERPT_CHARS)
    if window_end == len(line):
        window_start = max(0, window_end - SEARCH_TEXT_EXCERPT_CHARS)
    return line[window_start:window_end], window_start + 1


def search_text(
    root: Path,
    query: str,
    raw_path: str = ".",
    *,
    include_globs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    include_hidden: bool = False,
    case_sensitive: bool = True,
    max_files: int = DEFAULT_SEARCH_TEXT_FILES,
    max_matches: int = DEFAULT_SEARCH_TEXT_MATCHES,
    max_file_bytes: int = DEFAULT_SEARCH_TEXT_FILE_BYTES,
) -> dict[str, Any]:
    include_globs = list(include_globs or [])
    exclude_globs = list(exclude_globs or [])
    candidates_result = find_files(
        root,
        raw_path,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        include_hidden=include_hidden,
        max_results=max_files,
    )
    candidate_evidence = candidates_result["evidence"]
    candidates = candidate_evidence["matches"]

    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(query), flags)
    query_sha256 = hashlib.sha256(query.encode("utf-8")).hexdigest()

    transient_matches: list[dict[str, Any]] = []
    durable_locations: list[dict[str, Any]] = []
    files_searched = 0
    bytes_read = 0
    text_bytes_searched = 0
    skipped_non_text = 0
    skipped_oversize_files = 0
    truncation_reason: str | None = None

    for candidate in candidates:
        candidate_size = int(candidate["size_bytes"])
        if candidate_size > max_file_bytes:
            skipped_oversize_files += 1
            continue
        if bytes_read + candidate_size > MAX_SEARCH_TEXT_TOTAL_BYTES:
            truncation_reason = "total_bytes"
            break

        path, _ = _workspace_path(root, str(candidate["path"]))
        try:
            with path.open("rb") as handle:
                data = handle.read(max_file_bytes + 1)
        except OSError as exc:
            raise CapabilityUsageError(
                f"search_text could not read '{candidate['path']}': {exc}"
            ) from exc

        if bytes_read + len(data) > MAX_SEARCH_TEXT_TOTAL_BYTES:
            truncation_reason = "total_bytes"
            break
        bytes_read += len(data)
        if len(data) > max_file_bytes:
            skipped_oversize_files += 1
            continue

        if b"\x00" in data:
            skipped_non_text += 1
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            skipped_non_text += 1
            continue

        files_searched += 1
        text_bytes_searched += len(data)
        for line_number, line in enumerate(text.splitlines(), start=1):
            for found in pattern.finditer(line):
                if len(transient_matches) >= max_matches:
                    truncation_reason = "max_matches"
                    break

                excerpt, excerpt_start_column = _search_text_excerpt(
                    line, found.start(), found.end()
                )
                location = {
                    "path": str(candidate["path"]),
                    "line": line_number,
                    "column": found.start() + 1,
                }
                transient = {
                    **location,
                    "excerpt": excerpt,
                    "excerpt_start_column": excerpt_start_column,
                }
                prospective_match_bytes = len(
                    json.dumps(
                        [*transient_matches, transient],
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
                if prospective_match_bytes > MAX_SEARCH_TEXT_MATCH_BYTES:
                    truncation_reason = "result_bytes"
                    break
                prospective_location_bytes = len(
                    json.dumps(
                        [*durable_locations, location],
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
                if prospective_location_bytes > MAX_SEARCH_TEXT_LOCATION_BYTES:
                    truncation_reason = "durable_bytes"
                    break

                transient_matches.append(transient)
                durable_locations.append(location)
            if truncation_reason is not None:
                break
        if truncation_reason is not None:
            break

    candidate_truncated = bool(candidate_evidence["truncated"])
    candidate_truncation_reason = candidate_evidence["truncation_reason"]
    if truncation_reason is None and candidate_truncated:
        truncation_reason = (
            f"candidate_{candidate_truncation_reason}"
            if candidate_truncation_reason
            else "candidate_limit"
        )
    if truncation_reason is None and skipped_oversize_files:
        truncation_reason = "oversize_files"

    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": "search_text",
        "ok": True,
        "evidence": {
            "path": candidate_evidence["path"],
            "query_sha256": query_sha256,
            "query_length": len(query),
            "case_sensitive": case_sensitive,
            "locations": durable_locations,
            "match_count": len(durable_locations),
            "candidate_files_returned": len(candidates),
            "candidate_truncated": candidate_truncated,
            "candidate_truncation_reason": candidate_truncation_reason,
            "files_searched": files_searched,
            "bytes_read": bytes_read,
            "text_bytes_searched": text_bytes_searched,
            "skipped_non_text": skipped_non_text,
            "skipped_oversize_files": skipped_oversize_files,
            "max_file_bytes": max_file_bytes,
            "total_byte_limit": MAX_SEARCH_TEXT_TOTAL_BYTES,
            "match_byte_limit": MAX_SEARCH_TEXT_MATCH_BYTES,
            "durable_location_byte_limit": MAX_SEARCH_TEXT_LOCATION_BYTES,
            "truncated": truncation_reason is not None,
            "truncation_reason": truncation_reason,
            "ordering": "candidate_then_line_column",
        },
        "matches": transient_matches,
    }


def _invoke_search_text(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "path",
        "query",
        "include_globs",
        "exclude_globs",
        "include_hidden",
        "case_sensitive",
        "max_files",
        "max_matches",
        "max_file_bytes",
    }
    unknown = sorted(set(inputs) - allowed)
    if unknown:
        raise CapabilityUsageError(
            "unknown search_text input field(s): " + ", ".join(unknown)
        )

    raw_path = inputs.get("path", ".")
    query = inputs.get("query")
    include_globs = inputs.get("include_globs", [])
    exclude_globs = inputs.get("exclude_globs", [])
    include_hidden = inputs.get("include_hidden", False)
    case_sensitive = inputs.get("case_sensitive", True)
    max_files = inputs.get("max_files", DEFAULT_SEARCH_TEXT_FILES)
    max_matches = inputs.get("max_matches", DEFAULT_SEARCH_TEXT_MATCHES)
    max_file_bytes = inputs.get("max_file_bytes", DEFAULT_SEARCH_TEXT_FILE_BYTES)

    if not isinstance(raw_path, str) or not raw_path:
        raise CapabilityUsageError("search_text input 'path' must be a non-empty string")
    if (
        not isinstance(query, str)
        or not query
        or len(query) > MAX_SEARCH_TEXT_QUERY_CHARS
        or "\n" in query
        or "\r" in query
        or "\x00" in query
    ):
        raise CapabilityUsageError(
            "search_text input 'query' must be a non-empty single-line string "
            f"of at most {MAX_SEARCH_TEXT_QUERY_CHARS} characters"
        )
    try:
        query.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CapabilityUsageError(
            "search_text input 'query' must be valid UTF-8 text"
        ) from exc
    if not isinstance(include_globs, list) or any(
        not isinstance(pattern, str) for pattern in include_globs
    ):
        raise CapabilityUsageError(
            "search_text input 'include_globs' must be a list of strings"
        )
    if not isinstance(exclude_globs, list) or any(
        not isinstance(pattern, str) for pattern in exclude_globs
    ):
        raise CapabilityUsageError(
            "search_text input 'exclude_globs' must be a list of strings"
        )
    if not isinstance(include_hidden, bool):
        raise CapabilityUsageError(
            "search_text input 'include_hidden' must be true or false"
        )
    if not isinstance(case_sensitive, bool):
        raise CapabilityUsageError(
            "search_text input 'case_sensitive' must be true or false"
        )
    if (
        not isinstance(max_files, int)
        or isinstance(max_files, bool)
        or not 1 <= max_files <= MAX_SEARCH_TEXT_FILES
    ):
        raise CapabilityUsageError(
            f"search_text input 'max_files' must be an integer from 1 "
            f"to {MAX_SEARCH_TEXT_FILES}"
        )
    if (
        not isinstance(max_matches, int)
        or isinstance(max_matches, bool)
        or not 1 <= max_matches <= MAX_SEARCH_TEXT_MATCHES
    ):
        raise CapabilityUsageError(
            f"search_text input 'max_matches' must be an integer from 1 "
            f"to {MAX_SEARCH_TEXT_MATCHES}"
        )
    if (
        not isinstance(max_file_bytes, int)
        or isinstance(max_file_bytes, bool)
        or not 1 <= max_file_bytes <= MAX_SEARCH_TEXT_FILE_BYTES
    ):
        raise CapabilityUsageError(
            f"search_text input 'max_file_bytes' must be an integer from 1 "
            f"to {MAX_SEARCH_TEXT_FILE_BYTES}"
        )

    normalized_include = _normalize_search_glob_patterns(
        include_globs, "include_globs"
    )
    normalized_exclude = _normalize_search_glob_patterns(
        exclude_globs, "exclude_globs"
    )
    return search_text(
        root,
        query,
        raw_path,
        include_globs=normalized_include,
        exclude_globs=normalized_exclude,
        include_hidden=include_hidden,
        case_sensitive=case_sensitive,
        max_files=max_files,
        max_matches=max_matches,
        max_file_bytes=max_file_bytes,
    )


def _compare_regular_file(
    root: Path, raw_path: str, field_name: str
) -> tuple[Path, str, int]:
    path, relative = _workspace_path(root, raw_path)
    try:
        metadata = path.stat()
    except OSError as exc:
        raise CapabilityUsageError(
            f"compare_files could not inspect '{raw_path}': {exc}"
        ) from exc
    if not path.is_file():
        raise CapabilityUsageError(
            f"compare_files input '{field_name}' must name an existing regular file"
        )
    if metadata.st_size > MAX_COMPARE_FILE_BYTES:
        raise CapabilityUsageError(
            f"compare_files input '{field_name}' exceeds the "
            f"{MAX_COMPARE_FILE_BYTES}-byte file limit"
        )
    return path, relative, metadata.st_size


def _compare_file_bytes(
    left: Path, right: Path
) -> tuple[bool, str, str]:
    left_digest = hashlib.sha256()
    right_digest = hashlib.sha256()
    equal = True
    try:
        with left.open("rb") as left_handle, right.open("rb") as right_handle:
            while True:
                left_chunk = left_handle.read(1024 * 1024)
                right_chunk = right_handle.read(1024 * 1024)
                if left_chunk:
                    left_digest.update(left_chunk)
                if right_chunk:
                    right_digest.update(right_chunk)
                if left_chunk != right_chunk:
                    equal = False
                if not left_chunk and not right_chunk:
                    break
    except OSError as exc:
        raise CapabilityUsageError(f"compare_files could not read input: {exc}") from exc
    return equal, left_digest.hexdigest(), right_digest.hexdigest()


def _bounded_unified_diff(
    left_lines: list[str],
    right_lines: list[str],
    left_name: str,
    right_name: str,
    context_lines: int,
) -> tuple[list[str], bool, str | None]:
    diff_lines: list[str] = []
    truncation_reason: str | None = None
    for line in difflib.unified_diff(
        left_lines,
        right_lines,
        fromfile=left_name,
        tofile=right_name,
        n=context_lines,
        lineterm="",
    ):
        if len(diff_lines) >= MAX_COMPARE_DIFF_LINES:
            truncation_reason = "line_limit"
            break
        prospective_bytes = len(
            json.dumps(
                [*diff_lines, line],
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        if prospective_bytes > MAX_COMPARE_DIFF_BYTES:
            truncation_reason = "byte_limit"
            break
        diff_lines.append(line)
    return diff_lines, truncation_reason is not None, truncation_reason


def compare_files(
    root: Path,
    left_path: str,
    right_path: str,
    *,
    context_lines: int = DEFAULT_COMPARE_CONTEXT_LINES,
) -> dict[str, Any]:
    left, left_relative, left_size = _compare_regular_file(
        root, left_path, "left_path"
    )
    right, right_relative, right_size = _compare_regular_file(
        root, right_path, "right_path"
    )
    byte_equal, left_sha256, right_sha256 = _compare_file_bytes(left, right)

    text_status = "not_needed_equal" if byte_equal else "size_limit"
    text_lines_equal: bool | None = None
    diff_lines: list[str] = []
    diff_truncated = False
    diff_truncation_reason: str | None = None
    left_line_count: int | None = None
    right_line_count: int | None = None

    if not byte_equal and left_size <= MAX_COMPARE_TEXT_BYTES and right_size <= MAX_COMPARE_TEXT_BYTES:
        try:
            left_bytes = left.read_bytes()
            right_bytes = right.read_bytes()
        except OSError as exc:
            raise CapabilityUsageError(
                f"compare_files could not read bounded text input: {exc}"
            ) from exc

        if b"\x00" in left_bytes or b"\x00" in right_bytes:
            text_status = "non_text"
        else:
            try:
                left_text = left_bytes.decode("utf-8")
                right_text = right_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text_status = "non_text"
            else:
                left_lines = left_text.splitlines()
                right_lines = right_text.splitlines()
                left_line_count = len(left_lines)
                right_line_count = len(right_lines)
                text_lines_equal = left_lines == right_lines
                if (
                    left_line_count > MAX_COMPARE_TEXT_LINES
                    or right_line_count > MAX_COMPARE_TEXT_LINES
                ):
                    text_status = "line_limit"
                else:
                    text_status = "available"
                    diff_lines, diff_truncated, diff_truncation_reason = (
                        _bounded_unified_diff(
                            left_lines,
                            right_lines,
                            left_relative,
                            right_relative,
                            context_lines,
                        )
                    )

    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": "compare_files",
        "ok": True,
        "evidence": {
            "left": {
                "path": left_relative,
                "size_bytes": left_size,
                "sha256": left_sha256,
            },
            "right": {
                "path": right_relative,
                "size_bytes": right_size,
                "sha256": right_sha256,
            },
            "byte_equal": byte_equal,
            "file_byte_limit": MAX_COMPARE_FILE_BYTES,
            "text_diff": {
                "status": text_status,
                "text_byte_limit": MAX_COMPARE_TEXT_BYTES,
                "text_line_limit": MAX_COMPARE_TEXT_LINES,
                "left_line_count": left_line_count,
                "right_line_count": right_line_count,
                "text_lines_equal": text_lines_equal,
                "context_lines": context_lines,
                "returned_diff_lines": len(diff_lines),
                "diff_line_limit": MAX_COMPARE_DIFF_LINES,
                "diff_byte_limit": MAX_COMPARE_DIFF_BYTES,
                "truncated": diff_truncated,
                "truncation_reason": diff_truncation_reason,
            },
        },
        "diff": diff_lines,
    }


def _invoke_compare_files(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    allowed = {"left_path", "right_path", "context_lines"}
    unknown = sorted(set(inputs) - allowed)
    if unknown:
        raise CapabilityUsageError(
            "unknown compare_files input field(s): " + ", ".join(unknown)
        )

    left_path = inputs.get("left_path")
    right_path = inputs.get("right_path")
    context_lines = inputs.get("context_lines", DEFAULT_COMPARE_CONTEXT_LINES)

    for field_name, value in (
        ("left_path", left_path),
        ("right_path", right_path),
    ):
        if not isinstance(value, str) or not value:
            raise CapabilityUsageError(
                f"compare_files input '{field_name}' must be a non-empty string"
            )
    if (
        not isinstance(context_lines, int)
        or isinstance(context_lines, bool)
        or not 0 <= context_lines <= MAX_COMPARE_CONTEXT_LINES
    ):
        raise CapabilityUsageError(
            "compare_files input 'context_lines' must be an integer from 0 "
            f"to {MAX_COMPARE_CONTEXT_LINES}"
        )

    return compare_files(
        root,
        left_path,
        right_path,
        context_lines=context_lines,
    )


def assert_file(
    root: Path,
    raw_path: str,
    *,
    exists: bool = False,
    sha256_equals: str | None = None,
    json_valid: bool = False,
    required_keys: list[str] | None = None,
) -> dict[str, Any]:
    required_keys = list(required_keys or [])
    if not (exists or sha256_equals or json_valid or required_keys):
        raise CapabilityUsageError("at least one assertion is required")
    if sha256_equals is not None and not _SHA256_RE.fullmatch(sha256_equals):
        raise CapabilityUsageError("sha256 must be exactly 64 hexadecimal characters")
    if any(not key for key in required_keys):
        raise CapabilityUsageError("required JSON keys must not be empty")

    path, relative = _workspace_path(root, raw_path)
    present = path.exists()
    is_file = path.is_file() if present else False
    subject: dict[str, Any] = {"path": relative, "exists": present, "is_file": is_file}
    if is_file:
        subject["size_bytes"] = path.stat().st_size

    checks: list[dict[str, Any]] = []
    if exists:
        file_exists = present and is_file
        checks.append(
            {"name": "exists", "expected": True, "actual": file_exists, "ok": file_exists}
        )

    actual_sha256: str | None = None
    if sha256_equals is not None:
        if is_file:
            actual_sha256 = _sha256(path)
            subject["sha256"] = actual_sha256
        expected = sha256_equals.lower()
        checks.append(
            {
                "name": "sha256_equals",
                "expected": expected,
                "actual": actual_sha256,
                "ok": actual_sha256 == expected,
            }
        )

    parsed_json: Any = None
    json_error: str | None = None
    if json_valid or required_keys:
        if not is_file:
            json_error = "subject is not a regular file"
        elif path.stat().st_size > MAX_JSON_BYTES:
            json_error = f"JSON input exceeds {MAX_JSON_BYTES} bytes"
        else:
            try:
                parsed_json = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                json_error = f"{type(exc).__name__}: {exc}"

    if json_valid:
        checks.append(
            {
                "name": "json_valid",
                "expected": True,
                "actual": json_error is None,
                "ok": json_error is None,
                **({"detail": json_error} if json_error else {}),
            }
        )

    for key in required_keys:
        actual = json_error is None and isinstance(parsed_json, dict) and key in parsed_json
        detail = None
        if json_error:
            detail = json_error
        elif not isinstance(parsed_json, dict):
            detail = "JSON root is not an object"
        checks.append(
            {
                "name": "json_required_key",
                "key": key,
                "expected": True,
                "actual": actual,
                "ok": actual,
                **({"detail": detail} if detail else {}),
            }
        )

    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": "assert_file",
        "ok": all(item["ok"] for item in checks),
        "subject": subject,
        "checks": checks,
    }


def _invoke_assert_file(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    allowed = {"path", "exists", "sha256_equals", "json_valid", "required_keys"}
    unknown = sorted(set(inputs) - allowed)
    if unknown:
        raise CapabilityUsageError(
            "unknown assert_file input field(s): " + ", ".join(unknown)
        )
    raw_path = inputs.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise CapabilityUsageError("assert_file input 'path' must be a non-empty string")
    exists = inputs.get("exists", False)
    json_valid = inputs.get("json_valid", False)
    sha256_equals = inputs.get("sha256_equals")
    required_keys = inputs.get("required_keys", [])
    if not isinstance(exists, bool) or not isinstance(json_valid, bool):
        raise CapabilityUsageError("assert_file boolean inputs must be true or false")
    if sha256_equals is not None and not isinstance(sha256_equals, str):
        raise CapabilityUsageError("assert_file input 'sha256_equals' must be a string or null")
    if not isinstance(required_keys, list) or any(
        not isinstance(key, str) for key in required_keys
    ):
        raise CapabilityUsageError("assert_file input 'required_keys' must be a list of strings")
    return assert_file(
        root,
        raw_path,
        exists=exists,
        sha256_equals=sha256_equals,
        json_valid=json_valid,
        required_keys=required_keys,
    )


ASSERT_FILE_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["path"],
    "properties": {
        "path": {
            "type": "string",
            "description": "Room-workspace-relative path to inspect.",
        },
        "exists": {"type": "boolean", "default": False},
        "sha256_equals": {"type": ["string", "null"]},
        "json_valid": {"type": "boolean", "default": False},
        "required_keys": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
        },
    },
}

ASSERT_FILE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["codex_room_capability", "capability", "ok", "subject", "checks"],
    "properties": {
        "codex_room_capability": {"const": CAPABILITY_MARKER},
        "capability": {"const": "assert_file"},
        "ok": {"type": "boolean"},
        "subject": {"type": "object"},
        "checks": {"type": "array"},
        "capability_version": {"type": "string"},
        "implementation_sha256": {"type": "string"},
        "durable_result_fields": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}

FIND_FILES_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "path": {
            "type": "string",
            "default": ".",
            "description": "Room-workspace-relative directory to scan.",
        },
        "include_globs": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
        },
        "exclude_globs": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
        },
        "include_hidden": {"type": "boolean", "default": False},
        "min_size_bytes": {"type": ["integer", "null"], "minimum": 0},
        "max_size_bytes": {"type": ["integer", "null"], "minimum": 0},
        "max_results": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_FIND_FILES_RESULTS,
            "default": DEFAULT_FIND_FILES_RESULTS,
        },
    },
}

FIND_FILES_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["codex_room_capability", "capability", "ok", "evidence"],
    "properties": {
        "codex_room_capability": {"const": CAPABILITY_MARKER},
        "capability": {"const": "find_files"},
        "ok": {"type": "boolean"},
        "evidence": {"type": "object"},
        "capability_version": {"type": "string"},
        "implementation_sha256": {"type": "string"},
        "durable_result_fields": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}

SEARCH_TEXT_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["query"],
    "properties": {
        "path": {
            "type": "string",
            "default": ".",
            "description": "Room-workspace-relative directory to search.",
        },
        "query": {
            "type": "string",
            "minLength": 1,
            "maxLength": MAX_SEARCH_TEXT_QUERY_CHARS,
            "description": "Single-line literal text to find.",
        },
        "include_globs": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
        },
        "exclude_globs": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
        },
        "include_hidden": {"type": "boolean", "default": False},
        "case_sensitive": {"type": "boolean", "default": True},
        "max_files": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_SEARCH_TEXT_FILES,
            "default": DEFAULT_SEARCH_TEXT_FILES,
        },
        "max_matches": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_SEARCH_TEXT_MATCHES,
            "default": DEFAULT_SEARCH_TEXT_MATCHES,
        },
        "max_file_bytes": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_SEARCH_TEXT_FILE_BYTES,
            "default": DEFAULT_SEARCH_TEXT_FILE_BYTES,
        },
    },
}

SEARCH_TEXT_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "codex_room_capability",
        "capability",
        "ok",
        "evidence",
        "matches",
    ],
    "properties": {
        "codex_room_capability": {"const": CAPABILITY_MARKER},
        "capability": {"const": "search_text"},
        "ok": {"type": "boolean"},
        "evidence": {"type": "object"},
        "matches": {"type": "array"},
        "capability_version": {"type": "string"},
        "implementation_sha256": {"type": "string"},
        "durable_result_fields": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}

COMPARE_FILES_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["left_path", "right_path"],
    "properties": {
        "left_path": {
            "type": "string",
            "description": "First Room-workspace-relative regular file.",
        },
        "right_path": {
            "type": "string",
            "description": "Second Room-workspace-relative regular file.",
        },
        "context_lines": {
            "type": "integer",
            "minimum": 0,
            "maximum": MAX_COMPARE_CONTEXT_LINES,
            "default": DEFAULT_COMPARE_CONTEXT_LINES,
        },
    },
}

COMPARE_FILES_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "codex_room_capability",
        "capability",
        "ok",
        "evidence",
        "diff",
    ],
    "properties": {
        "codex_room_capability": {"const": CAPABILITY_MARKER},
        "capability": {"const": "compare_files"},
        "ok": {"type": "boolean"},
        "evidence": {"type": "object"},
        "diff": {"type": "array", "items": {"type": "string"}},
        "capability_version": {"type": "string"},
        "implementation_sha256": {"type": "string"},
        "durable_result_fields": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


def _invoke_inspect_source(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    try:
        return inspect_source(root, inputs)
    except SourceInspectionError as exc:
        raise CapabilityUsageError(str(exc)) from exc


CORE_CAPABILITIES: dict[str, CapabilitySpec] = {
    "assert_file": CapabilitySpec(
        capability_id="assert_file",
        description=(
            "Run exact read-only assertions against one Room-workspace file: "
            "regular-file existence, SHA-256 equality, JSON validity, and required "
            "top-level JSON keys."
        ),
        origin="core",
        scope="core",
        version="1",
        input_schema=ASSERT_FILE_INPUT_SCHEMA,
        output_schema=ASSERT_FILE_OUTPUT_SCHEMA,
        durable_result_fields=("subject", "checks"),
        permissions={
            "workspace_read": True,
            "workspace_write": False,
            "network": False,
            "external_process": False,
        },
        side_effects="none",
        verification={"status": "verified", "evidence": ["E-030"]},
        handler=_invoke_assert_file,
        implementation_components=(
            MAX_JSON_BYTES,
            _SHA256_RE.pattern,
            _workspace_path,
            _sha256,
            assert_file,
            _invoke_assert_file,
        ),
    ),
    "compare_files": CapabilitySpec(
        capability_id="compare_files",
        description=(
            "Compare two bounded Room-workspace regular files exactly by bytes and "
            "SHA-256. For small UTF-8 text differences, return a bounded unified "
            "diff transiently while durable evidence retains only identities, "
            "hashes, sizes, and diff status/count metadata."
        ),
        origin="core",
        scope="core",
        version="1",
        input_schema=COMPARE_FILES_INPUT_SCHEMA,
        output_schema=COMPARE_FILES_OUTPUT_SCHEMA,
        durable_result_fields=("evidence",),
        permissions={
            "workspace_read": True,
            "workspace_write": False,
            "network": False,
            "external_process": False,
        },
        side_effects="none",
        verification={"status": "verified", "evidence": ["E-032"]},
        handler=_invoke_compare_files,
        implementation_components=(
            MAX_COMPARE_FILE_BYTES,
            MAX_COMPARE_TEXT_BYTES,
            MAX_COMPARE_TEXT_LINES,
            MAX_COMPARE_DIFF_LINES,
            MAX_COMPARE_DIFF_BYTES,
            DEFAULT_COMPARE_CONTEXT_LINES,
            MAX_COMPARE_CONTEXT_LINES,
            _workspace_path,
            _compare_regular_file,
            _compare_file_bytes,
            _bounded_unified_diff,
            compare_files,
            _invoke_compare_files,
        ),
    ),
    "find_files": CapabilitySpec(
        capability_id="find_files",
        description=(
            "Find regular files under one Room-workspace directory using bounded, "
            "deterministic glob and size filters without following symlinks; return "
            f"at most {MAX_FIND_FILES_RESULTS} files, cap match evidence at "
            f"{MAX_FIND_FILES_MATCH_BYTES} bytes, and scan at most "
            f"{MAX_FIND_FILES_SCANNED_ENTRIES} entries."
        ),
        origin="core",
        scope="core",
        version="1",
        input_schema=FIND_FILES_INPUT_SCHEMA,
        output_schema=FIND_FILES_OUTPUT_SCHEMA,
        durable_result_fields=("evidence",),
        permissions={
            "workspace_read": True,
            "workspace_write": False,
            "network": False,
            "external_process": False,
        },
        side_effects="none",
        verification={"status": "verified", "evidence": ["E-032"]},
        handler=_invoke_find_files,
        implementation_components=(
            MAX_FIND_FILES_RESULTS,
            DEFAULT_FIND_FILES_RESULTS,
            MAX_FIND_FILES_SCANNED_ENTRIES,
            MAX_FIND_FILES_MATCH_BYTES,
            _workspace_path,
            _normalize_glob_patterns,
            _glob_variants,
            _matches_globs,
            _is_hidden_relative,
            find_files,
            _invoke_find_files,
        ),
    ),
    "inspect_source": CapabilitySpec(
        capability_id="inspect_source",
        description=(
            "Discover and inspect authorized read-only sources beyond the current "
            "Room workspace: the maintained CORE source surface and any Personal "
            "Room shared workspace. Supports bounded source discovery, file finding, "
            "literal text search, and UTF-8 text reads without granting cross-boundary "
            "write authority or exposing CORE runtime data."
        ),
        origin="core",
        scope="core",
        version="3",
        input_schema=INSPECT_SOURCE_INPUT_SCHEMA,
        output_schema=INSPECT_SOURCE_OUTPUT_SCHEMA,
        durable_result_fields=("evidence",),
        permissions={
            "workspace_read": True,
            "cross_room_read": True,
            "core_source_read": True,
            "workspace_write": False,
            "network": False,
            "external_process": False,
        },
        side_effects="none",
        verification={"status": "verified", "evidence": ["E-078", "E-081"]},
        handler=_invoke_inspect_source,
        implementation_components=(
            *INSPECT_SOURCE_IMPLEMENTATION_COMPONENTS,
            _invoke_inspect_source,
        ),
    ),
    "search_text": CapabilitySpec(
        capability_id="search_text",
        description=(
            "Search bounded UTF-8, NUL-free workspace text for a single-line "
            "literal string. Runtime results include bounded excerpts; durable "
            "Room evidence retains only query identity, locations, counts, and "
            "truncation metadata."
        ),
        origin="core",
        scope="core",
        version="1",
        input_schema=SEARCH_TEXT_INPUT_SCHEMA,
        output_schema=SEARCH_TEXT_OUTPUT_SCHEMA,
        durable_result_fields=("evidence",),
        permissions={
            "workspace_read": True,
            "workspace_write": False,
            "network": False,
            "external_process": False,
        },
        side_effects="none",
        verification={"status": "verified", "evidence": ["E-032"]},
        handler=_invoke_search_text,
        implementation_components=(
            MAX_SEARCH_TEXT_FILES,
            DEFAULT_SEARCH_TEXT_FILES,
            MAX_SEARCH_TEXT_MATCHES,
            DEFAULT_SEARCH_TEXT_MATCHES,
            DEFAULT_SEARCH_TEXT_FILE_BYTES,
            MAX_SEARCH_TEXT_FILE_BYTES,
            MAX_SEARCH_TEXT_TOTAL_BYTES,
            MAX_SEARCH_TEXT_MATCH_BYTES,
            MAX_SEARCH_TEXT_LOCATION_BYTES,
            SEARCH_TEXT_EXCERPT_CHARS,
            MAX_SEARCH_TEXT_QUERY_CHARS,
            MAX_FIND_FILES_SCANNED_ENTRIES,
            MAX_FIND_FILES_MATCH_BYTES,
            _workspace_path,
            _glob_variants,
            _matches_globs,
            _is_hidden_relative,
            find_files,
            _normalize_search_glob_patterns,
            _search_text_excerpt,
            search_text,
            _invoke_search_text,
        ),
    ),
}


def _room_custom_capabilities(root: Path) -> tuple[Any | None, dict[str, Any]]:
    context = resolve_room_capability_context(root)
    if context is None:
        return None, {}
    try:
        custom = load_room_custom_capabilities(
            context.data_root,
            context.room_id,
            reserved_capability_ids=frozenset(CORE_CAPABILITIES),
        )
    except CustomCapabilityRegistryError as exc:
        raise CapabilityUsageError(str(exc)) from exc
    return context, custom


def custom_capability_authoring_guide() -> dict[str, Any]:
    """Return the bounded package-v1 authoring contract on demand."""
    return {
        "codex_room_registry": REGISTRY_MARKER,
        "operation": "authoring",
        "schema_version": 1,
        "admission": (
            "Create a custom capability only when no adequate registered capability exists "
            "and the deterministic procedure has enough reuse, reliability, provenance, or "
            "mechanical-complexity value to justify registration."
        ),
        "draft_root": ".codex-room/capability-drafts/<id>",
        "package_v1": {
            "files": ["manifest.json", "capability.py"],
            "id_pattern": "^[a-z][a-z0-9_]{0,63}$",
            "id_note": "Windows-reserved device names are rejected even if they match the pattern.",
            "max_manifest_bytes": MAX_MANIFEST_BYTES,
            "max_entrypoint_bytes": MAX_ENTRYPOINT_BYTES,
            "manifest_required_fields": [
                "schema_version",
                "id",
                "version",
                "description",
                "scope",
                "runtime",
                "input_schema",
                "output_schema",
                "durable_result_fields",
                "permissions",
                "side_effects",
            ],
            "fixed_values": {
                "schema_version": 1,
                "scope": "lineage",
                "runtime": {
                    "kind": "python",
                    "entrypoint": "capability.py",
                    "protocol": "stdio-json-v1",
                },
            },
            "contract_rules": {
                "input_schema": "JSON Schema object contract",
                "output_schema": (
                    "JSON Schema object contract that declares and requires boolean 'ok'; "
                    "Codex Room registry-envelope property names are reserved"
                ),
                "durable_result_fields": (
                    "Unique non-envelope output property names that may persist in Room telemetry"
                ),
                "permissions": {
                    "workspace_read": "boolean",
                    "workspace_write": "boolean",
                    "network": "boolean",
                    "external_process": "boolean",
                },
                "side_effects": "Non-empty bounded description",
            },
            "entrypoint_protocol": (
                "Read one JSON object from stdin and write exactly one JSON object to stdout; "
                "successful output must include boolean 'ok'. Keep stderr empty on success."
            ),
        },
        "verification_cases_v1": {
            "format": f"JSON array with 1 to {MAX_VERIFICATION_CASES} cases",
            "max_case_json_bytes": MAX_CASE_JSON_BYTES,
            "max_fixture_files": MAX_FIXTURE_FILES,
            "max_fixture_file_bytes": MAX_FIXTURE_FILE_BYTES,
            "max_fixture_total_bytes": MAX_FIXTURE_TOTAL_BYTES,
            "required_fields": ["name", "input", "expected_output"],
            "optional_fields": ["files"],
            "rules": [
                "input and expected_output must be JSON objects",
                "expected_output must include boolean ok and every durable_result_field",
                "files, when present, maps safe workspace-relative paths to UTF-8 text fixtures",
                "verification compares observed output to expected_output exactly",
            ],
        },
        "register_command": (
            "codex-room-cap register CAPABILITY_ID --cases-file WORKSPACE_RELATIVE_JSON"
        ),
        "settlement": (
            "A successful register command means sandbox verification passed and protected "
            "host registration was requested. The capability is not active until that agent "
            "turn settles. On a later turn, rediscover it with list/inspect before invoking."
        ),
        "permission_enforcement": (
            "Manifest permissions are declarations. Codex Room does not provide a "
            "per-capability OS sandbox; execution inherits the ambient Room caller/sandbox."
        ),
    }


def list_capabilities(root: Path | None = None) -> dict[str, Any]:
    summaries = [CORE_CAPABILITIES[key].summary() for key in sorted(CORE_CAPABILITIES)]
    if root is not None:
        _, custom = _room_custom_capabilities(root)
        summaries.extend(custom[key].summary() for key in sorted(custom))
    summaries.sort(key=lambda item: item["id"])
    return {
        "codex_room_registry": REGISTRY_MARKER,
        "operation": "list",
        "capabilities": summaries,
    }


def inspect_capability(capability_id: str, root: Path | None = None) -> dict[str, Any]:
    spec = CORE_CAPABILITIES.get(capability_id)
    if spec is not None:
        manifest = spec.manifest()
    else:
        custom = {}
        if root is not None:
            _, custom = _room_custom_capabilities(root)
        binding = custom.get(capability_id)
        if binding is None:
            raise CapabilityUsageError(f"unknown capability: {capability_id}")
        manifest = binding.manifest()
    return {
        "codex_room_registry": REGISTRY_MARKER,
        "operation": "inspect",
        "capability": manifest,
    }


def invoke_capability(
    root: Path, capability_id: str, inputs: dict[str, Any]
) -> dict[str, Any]:
    spec = CORE_CAPABILITIES.get(capability_id)
    if spec is not None:
        if not isinstance(inputs, dict):
            raise CapabilityUsageError("capability input must be a JSON object")
        result = spec.handler(root, inputs)
        result["capability_version"] = spec.version
        result["implementation_sha256"] = spec.implementation_sha256()
        result["durable_result_fields"] = list(spec.durable_result_fields)
        return result

    context, custom = _room_custom_capabilities(root)
    binding = custom.get(capability_id)
    if context is None or binding is None:
        raise CapabilityUsageError(f"unknown capability: {capability_id}")
    try:
        return invoke_bound_custom_capability(context, binding, inputs)
    except CustomCapabilityRegistryError as exc:
        raise CapabilityUsageError(str(exc)) from exc


def register_custom_capability(
    root: Path,
    capability_id: str,
    cases_file: str,
) -> dict[str, Any]:
    context = resolve_room_capability_context(root)
    if context is None:
        raise CapabilityUsageError(
            "custom capability registration requires a canonical Room workspace"
        )
    cases_path, _ = _workspace_path(root, cases_file)
    try:
        metadata = cases_path.lstat()
    except OSError as exc:
        raise CapabilityUsageError(f"verification cases file could not be inspected: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CapabilityUsageError("verification cases file must be a regular workspace file")
    if metadata.st_size > 1024 * 1024:
        raise CapabilityUsageError("verification cases file exceeds the size limit")
    try:
        raw_cases = json.loads(cases_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapabilityUsageError("verification cases file must be valid UTF-8 JSON") from exc
    try:
        receipt = verify_custom_capability_draft(root, capability_id, raw_cases)
    except CustomCapabilityVerificationError as exc:
        raise CapabilityUsageError(str(exc)) from exc
    return {
        "codex_room_registry": REGISTRY_MARKER,
        "operation": "register",
        "ok": True,
        "state": "verification_passed_host_pending",
        "capability_id": capability_id,
        "registration_request": {
            "capability_id": capability_id,
            "receipt": receipt.as_dict(),
        },
    }


def _error_payload(
    message: str, *, capability_id: str | None = None, operation: str = "invoke"
) -> dict[str, Any]:
    if operation in {"list", "authoring", "inspect", "register"}:
        payload: dict[str, Any] = {
            "codex_room_registry": REGISTRY_MARKER,
            "operation": operation,
            "ok": False,
            "error": {"code": "invalid_request", "message": message},
        }
        if capability_id:
            payload["capability_id"] = capability_id
        return payload
    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": capability_id or "unknown",
        "ok": False,
        "error": {"code": "invalid_request", "message": message},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-room-cap")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List registered deterministic capabilities.")
    subparsers.add_parser(
        "authoring",
        help="Show the bounded custom capability package and verification contract.",
    )

    inspect_parser = subparsers.add_parser(
        "inspect", help="Inspect one registered capability manifest."
    )
    inspect_parser.add_argument("capability_id")

    register_parser = subparsers.add_parser(
        "register",
        help=(
            "Verify one custom capability draft and request protected host registration "
            "when the agent turn settles."
        ),
    )
    register_parser.add_argument("capability_id")
    register_parser.add_argument(
        "--cases-file",
        required=True,
        help="Workspace-relative UTF-8 JSON verification case file.",
    )

    invoke_parser = subparsers.add_parser(
        "invoke", help="Invoke one registered deterministic capability."
    )
    invoke_parser.add_argument("capability_id")
    invoke_inputs = invoke_parser.add_mutually_exclusive_group(required=True)
    invoke_inputs.add_argument(
        "--input-json",
        help="One JSON object matching the capability input schema.",
    )
    invoke_inputs.add_argument(
        "--input-file",
        help=(
            "Workspace-relative UTF-8 JSON object file. Prefer this when command-line "
            "JSON quoting would be fragile."
        ),
    )


    source_parser = subparsers.add_parser(
        "source",
        help="Invoke inspect_source without command-line JSON plumbing.",
    )
    source_ops = source_parser.add_subparsers(dest="source_operation", required=True)
    source_ops.add_parser("sources", help="Discover authorized inspection sources.")

    find_source = source_ops.add_parser("find", help="Find files in one authorized source.")
    find_source.add_argument("source", choices=("workspace", "core", "room"))
    find_source.add_argument("path")
    find_source.add_argument("--room-id")
    find_source.add_argument("--include-glob", action="append", default=[])
    find_source.add_argument("--exclude-glob", action="append", default=[])
    find_source.add_argument("--include-hidden", action="store_true")
    find_source.add_argument("--max-results", type=int, default=100)

    search_source = source_ops.add_parser("search", help="Search one literal string.")
    search_source.add_argument("source", choices=("workspace", "core", "room"))
    search_source.add_argument("path")
    search_source.add_argument("--room-id")
    search_source.add_argument("--query", required=True)
    search_source.add_argument("--include-glob", action="append", default=[])
    search_source.add_argument("--exclude-glob", action="append", default=[])
    search_source.add_argument("--include-hidden", action="store_true")
    search_source.add_argument("--ignore-case", action="store_false", dest="case_sensitive")
    search_source.add_argument("--max-files", type=int, default=100)
    search_source.add_argument("--max-matches", type=int, default=50)

    search_many = source_ops.add_parser(
        "search-many", help="Search several literal strings in one bounded source scan."
    )
    search_many.add_argument("source", choices=("workspace", "core", "room"))
    search_many.add_argument("path")
    search_many.add_argument("--room-id")
    search_many.add_argument("--query", action="append", required=True)
    search_many.add_argument("--include-glob", action="append", default=[])
    search_many.add_argument("--exclude-glob", action="append", default=[])
    search_many.add_argument("--include-hidden", action="store_true")
    search_many.add_argument("--ignore-case", action="store_false", dest="case_sensitive")
    search_many.add_argument("--max-files", type=int, default=100)
    search_many.add_argument("--max-matches", type=int, default=50)

    read_source = source_ops.add_parser("read", help="Read one bounded text range.")
    read_source.add_argument("source", choices=("workspace", "core", "room"))
    read_source.add_argument("path")
    read_source.add_argument("--room-id")
    read_source.add_argument("--start-line", type=int, default=1)
    read_source.add_argument("--max-lines", type=int, default=400)
    read_source.add_argument("--max-bytes", type=int, default=128 * 1024)

    read_many = source_ops.add_parser(
        "read-many", help="Read several bounded text ranges in one invocation."
    )
    read_many.add_argument("source", choices=("workspace", "core", "room"))
    read_many.add_argument("--room-id")
    read_many.add_argument(
        "--read",
        action="append",
        nargs=3,
        metavar=("PATH", "START_LINE", "MAX_LINES"),
        required=True,
    )
    read_many.add_argument("--max-bytes", type=int, default=128 * 1024)

    # Backward-compatible P4.1 command. New agent prompts use registry discovery/invoke.
    assert_file_parser = subparsers.add_parser(
        "assert-file",
        help="Compatibility alias for the registered assert_file capability.",
    )
    assert_file_parser.add_argument("path")
    assert_file_parser.add_argument("--exists", action="store_true")
    assert_file_parser.add_argument("--sha256", dest="sha256_equals")
    assert_file_parser.add_argument("--json-valid", action="store_true")
    assert_file_parser.add_argument(
        "--required-key", action="append", default=[], dest="required_keys"
    )
    return parser



def _source_cli_inputs(args: argparse.Namespace) -> dict[str, Any]:
    operation = args.source_operation.replace("-", "_")
    if operation == "sources":
        return {"operation": "sources"}

    inputs: dict[str, Any] = {
        "operation": operation,
        "source": args.source,
    }
    if getattr(args, "room_id", None) is not None:
        inputs["room_id"] = args.room_id
    if operation == "find":
        inputs.update(
            {
                "path": args.path,
                "include_globs": args.include_glob,
                "exclude_globs": args.exclude_glob,
                "include_hidden": args.include_hidden,
                "max_results": args.max_results,
            }
        )
    elif operation in {"search", "search_many"}:
        inputs.update(
            {
                "path": args.path,
                "include_globs": args.include_glob,
                "exclude_globs": args.exclude_glob,
                "include_hidden": args.include_hidden,
                "case_sensitive": args.case_sensitive,
                "max_files": args.max_files,
                "max_matches": args.max_matches,
            }
        )
        if operation == "search":
            inputs["query"] = args.query
        else:
            inputs["queries"] = args.query
    elif operation == "read":
        inputs.update(
            {
                "path": args.path,
                "start_line": args.start_line,
                "max_lines": args.max_lines,
                "max_bytes": args.max_bytes,
            }
        )
    elif operation == "read_many":
        reads: list[dict[str, Any]] = []
        for path, raw_start, raw_lines in args.read:
            try:
                start_line = int(raw_start)
                max_lines = int(raw_lines)
            except ValueError as exc:
                raise CapabilityUsageError(
                    "--read START_LINE and MAX_LINES must be integers"
                ) from exc
            reads.append(
                {
                    "path": path,
                    "start_line": start_line,
                    "max_lines": max_lines,
                }
            )
        inputs["reads"] = reads
        inputs["max_bytes"] = args.max_bytes
    return inputs


def _print_result(result: dict[str, Any]) -> None:
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            result = list_capabilities(Path.cwd())
        elif args.command == "authoring":
            result = custom_capability_authoring_guide()
        elif args.command == "inspect":
            result = inspect_capability(args.capability_id, Path.cwd())
        elif args.command == "register":
            result = register_custom_capability(
                Path.cwd(),
                args.capability_id,
                args.cases_file,
            )
        elif args.command == "invoke":
            if args.input_file is not None:
                inputs = _load_invocation_input_file(Path.cwd(), args.input_file)
            else:
                try:
                    inputs = json.loads(args.input_json)
                except json.JSONDecodeError as exc:
                    raise CapabilityUsageError(f"input JSON is invalid: {exc}") from exc
            if not isinstance(inputs, dict):
                raise CapabilityUsageError("capability input must be a JSON object")
            result = invoke_capability(Path.cwd(), args.capability_id, inputs)
        elif args.command == "source":
            result = invoke_capability(
                Path.cwd(),
                "inspect_source",
                _source_cli_inputs(args),
            )
        elif args.command == "assert-file":
            result = invoke_capability(
                Path.cwd(),
                "assert_file",
                {
                    "path": args.path,
                    "exists": args.exists,
                    "sha256_equals": args.sha256_equals,
                    "json_valid": args.json_valid,
                    "required_keys": args.required_keys,
                },
            )
        else:
            raise CapabilityUsageError(f"unsupported command: {args.command}")
    except CapabilityUsageError as exc:
        capability_id = (
            "inspect_source"
            if args.command == "source"
            else getattr(args, "capability_id", None)
        )
        operation = (
            args.command
            if args.command in {"list", "authoring", "inspect", "register"}
            else "invoke"
        )
        _print_result(
            _error_payload(
                str(exc), capability_id=capability_id, operation=operation
            )
        )
        return 2
    _print_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
