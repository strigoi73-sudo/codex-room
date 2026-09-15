from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any

from .custom_registry import resolve_room_capability_context

CAPABILITY_MARKER = 1
MAX_FIND_RESULTS = 200
DEFAULT_FIND_RESULTS = 100
MAX_SCAN_ENTRIES = 100_000
MAX_FIND_RESULT_BYTES = 48 * 1024
MAX_SEARCH_FILES = 200
DEFAULT_SEARCH_FILES = 100
MAX_SEARCH_MATCHES = 100
DEFAULT_SEARCH_MATCHES = 50
MAX_SEARCH_FILE_BYTES = 2 * 1024 * 1024
MAX_SEARCH_TOTAL_BYTES = 20 * 1024 * 1024
MAX_SEARCH_MATCH_BYTES = 32 * 1024
MAX_QUERY_CHARS = 4096
SEARCH_EXCERPT_CHARS = 240
MAX_READ_FILE_BYTES = 2 * 1024 * 1024
MAX_READ_OUTPUT_BYTES = 128 * 1024
MAX_READ_LINES = 1000
MAX_BATCH_QUERIES = 16
MAX_BATCH_QUERY_CHARS = 16 * 1024
MAX_BATCH_READS = 16
MAX_BATCH_READ_OUTPUT_BYTES = 128 * 1024

CORE_READ_ENTRIES = frozenset(
    {
        ".github",
        ".gitignore",
        "Kill-Codex-Room.bat",
        "README.md",
        "Start-Codex-Room.cmd",
        "codex-room-cap.cmd",
        "codex_room",
        "constraints-test.txt",
        "docs",
        "pyproject.toml",
        "test-transcript-stability.ps1",
        "tests",
    }
)
_ROOM_ID = re.compile(r"room_[A-Za-z0-9_-]{1,128}")


class SourceInspectionError(ValueError):
    pass


def _is_link_or_reparse(item_stat: os.stat_result) -> bool:
    if stat.S_ISLNK(item_stat.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    file_attributes = getattr(item_stat, "st_file_attributes", 0)
    return bool(reparse_flag and file_attributes & reparse_flag)


def _normalized_relative_path(raw_path: str, *, allow_dot: bool) -> PurePosixPath:
    if not isinstance(raw_path, str) or not raw_path or "\x00" in raw_path or "\\" in raw_path:
        raise SourceInspectionError("path must be a non-empty normalized relative path")
    if raw_path == ".":
        if allow_dot:
            return PurePosixPath()
        raise SourceInspectionError("path must select an allowed CORE entry")
    path = PurePosixPath(raw_path)
    if path.is_absolute() or path.as_posix() != raw_path:
        raise SourceInspectionError("path must be a normalized relative path")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise SourceInspectionError("path must stay inside the selected read source")
    return path


def _assert_real_path(
    root: Path,
    relative: PurePosixPath,
    *,
    expect_directory: bool = False,
    expect_file: bool = False,
) -> Path:
    current = root
    try:
        root_stat = os.lstat(root)
    except OSError as exc:
        raise SourceInspectionError("selected read source is unavailable") from exc
    if _is_link_or_reparse(root_stat) or not stat.S_ISDIR(root_stat.st_mode):
        raise SourceInspectionError("selected read source is not a real directory")

    for index, part in enumerate(relative.parts):
        current = current / part
        try:
            item_stat = os.lstat(current)
        except OSError as exc:
            raise SourceInspectionError(f"path is unavailable: {relative.as_posix()}") from exc
        if _is_link_or_reparse(item_stat):
            raise SourceInspectionError("read paths must not traverse links or reparse points")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(item_stat.st_mode):
            raise SourceInspectionError("read path contains a non-directory component")

    if expect_directory:
        try:
            final_stat = os.lstat(current)
        except OSError as exc:
            raise SourceInspectionError("directory is unavailable") from exc
        if _is_link_or_reparse(final_stat) or not stat.S_ISDIR(final_stat.st_mode):
            raise SourceInspectionError("path must identify a real directory")
    if expect_file:
        try:
            final_stat = os.lstat(current)
        except OSError as exc:
            raise SourceInspectionError("file is unavailable") from exc
        if _is_link_or_reparse(final_stat) or not stat.S_ISREG(final_stat.st_mode):
            raise SourceInspectionError("path must identify a real regular file")
    return current


def _validate_core_path(relative: PurePosixPath) -> None:
    if not relative.parts or relative.parts[0] not in CORE_READ_ENTRIES:
        allowed = ", ".join(sorted(CORE_READ_ENTRIES))
        raise SourceInspectionError(
            "CORE reads are limited to the maintained source surface; "
            f"select one of: {allowed}"
        )


def _canonical_room_shared(data_root: Path, room_id: str) -> Path:
    if not isinstance(room_id, str) or not _ROOM_ID.fullmatch(room_id):
        raise SourceInspectionError("room_id must identify one canonical Room")
    rooms_root = data_root / "rooms"
    _assert_real_path(data_root, PurePosixPath("rooms"), expect_directory=True)
    room_root = _assert_real_path(
        rooms_root,
        PurePosixPath(room_id),
        expect_directory=True,
    )
    return _assert_real_path(
        room_root,
        PurePosixPath("shared"),
        expect_directory=True,
    )


def _resolve_source(
    workspace: Path,
    source: str,
    room_id: str | None,
) -> tuple[Path, dict[str, Any], bool]:
    if source == "workspace":
        if room_id is not None:
            raise SourceInspectionError("room_id is valid only when source is 'room'")
        context = resolve_room_capability_context(workspace)
        descriptor: dict[str, Any] = {"kind": "workspace"}
        if context is not None:
            descriptor["room_id"] = context.room_id
        return _assert_real_path(workspace, PurePosixPath(), expect_directory=True), descriptor, False

    context = resolve_room_capability_context(workspace)
    if context is None:
        raise SourceInspectionError(
            "CORE and cross-Room reads require a canonical Room shared workspace"
        )

    if source == "core":
        if room_id is not None:
            raise SourceInspectionError("room_id is valid only when source is 'room'")
        core_root = context.data_root.parent
        return _assert_real_path(core_root, PurePosixPath(), expect_directory=True), {"kind": "core"}, True

    if source == "room":
        if room_id is None:
            raise SourceInspectionError("source 'room' requires room_id")
        target = _canonical_room_shared(context.data_root, room_id)
        return target, {"kind": "room", "room_id": room_id}, False

    raise SourceInspectionError("source must be 'workspace', 'core', or 'room'")


def _existing_core_entries(core_root: Path) -> list[str]:
    entries: list[str] = []
    for name in sorted(CORE_READ_ENTRIES):
        candidate = core_root / name
        try:
            item_stat = os.lstat(candidate)
        except OSError:
            continue
        if _is_link_or_reparse(item_stat):
            continue
        if stat.S_ISREG(item_stat.st_mode) or stat.S_ISDIR(item_stat.st_mode):
            entries.append(name)
    return entries


def _source_inventory(workspace: Path) -> dict[str, Any]:
    context = resolve_room_capability_context(workspace)
    if context is None:
        raise SourceInspectionError(
            "source discovery requires a canonical Room shared workspace"
        )
    rooms_root = _assert_real_path(
        context.data_root,
        PurePosixPath("rooms"),
        expect_directory=True,
    )
    rooms: list[dict[str, Any]] = []
    for name in sorted(os.listdir(rooms_root)):
        if not _ROOM_ID.fullmatch(name):
            continue
        room_root = rooms_root / name
        try:
            room_stat = os.lstat(room_root)
            shared_stat = os.lstat(room_root / "shared")
        except OSError:
            continue
        if (
            _is_link_or_reparse(room_stat)
            or not stat.S_ISDIR(room_stat.st_mode)
            or _is_link_or_reparse(shared_stat)
            or not stat.S_ISDIR(shared_stat.st_mode)
        ):
            continue
        rooms.append({"room_id": name, "current": name == context.room_id})

    core_root = _assert_real_path(
        context.data_root.parent,
        PurePosixPath(),
        expect_directory=True,
    )
    return {
        "current_room_id": context.room_id,
        "core": {
            "source": "core",
            "allowed_entries": _existing_core_entries(core_root),
        },
        "rooms": rooms,
        "room_source_note": "Room reads expose only each Room's shared workspace.",
    }


def _normalize_patterns(raw_patterns: Any, field_name: str) -> list[str]:
    if raw_patterns is None:
        return []
    if not isinstance(raw_patterns, list) or any(
        not isinstance(item, str) for item in raw_patterns
    ):
        raise SourceInspectionError(f"{field_name} must be a list of strings")
    normalized: list[str] = []
    for raw in raw_patterns:
        if not raw or "\\" in raw or raw.startswith("/") or "\x00" in raw:
            raise SourceInspectionError(f"{field_name} contains an invalid pattern")
        if any(part == ".." for part in raw.split("/")):
            raise SourceInspectionError(f"{field_name} must stay inside the selected source")
        normalized.append(raw)
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


def _matches_patterns(relative_path: str, patterns: list[str]) -> bool:
    path = PurePosixPath(relative_path)
    return any(
        path.match(variant)
        for pattern in patterns
        for variant in _glob_variants(pattern)
    )


def _is_hidden(relative_path: str) -> bool:
    return any(part.startswith(".") for part in PurePosixPath(relative_path).parts)


def _find_entries(
    source_root: Path,
    relative_root: PurePosixPath,
    *,
    include_globs: list[str],
    exclude_globs: list[str],
    include_hidden: bool,
    max_results: int,
) -> tuple[list[dict[str, Any]], int, str | None]:
    scan_root = _assert_real_path(
        source_root,
        relative_root,
        expect_directory=True,
    )
    matches: list[dict[str, Any]] = []
    scanned_entries = 0
    truncation_reason: str | None = None

    def raise_walk_error(exc: OSError) -> None:
        raise SourceInspectionError(f"source scan failed: {exc}") from exc

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
            if scanned_entries >= MAX_SCAN_ENTRIES:
                truncation_reason = "scan_limit"
                break
            scanned_entries += 1
            candidate = current / dirname
            relative_to_scan = candidate.relative_to(scan_root).as_posix()
            try:
                item_stat = os.lstat(candidate)
            except OSError as exc:
                raise SourceInspectionError(
                    f"source entry could not be inspected: {relative_to_scan}"
                ) from exc
            if _is_link_or_reparse(item_stat) or not stat.S_ISDIR(item_stat.st_mode):
                continue
            if not include_hidden and _is_hidden(relative_to_scan):
                continue
            if exclude_globs and _matches_patterns(relative_to_scan, exclude_globs):
                continue
            kept_dirs.append(dirname)
        if truncation_reason is not None:
            dirs[:] = []
            break
        dirs[:] = kept_dirs

        for filename in files:
            if scanned_entries >= MAX_SCAN_ENTRIES:
                truncation_reason = "scan_limit"
                break
            scanned_entries += 1
            candidate = current / filename
            relative_to_scan = candidate.relative_to(scan_root).as_posix()
            try:
                item_stat = os.lstat(candidate)
            except OSError as exc:
                raise SourceInspectionError(
                    f"source entry could not be inspected: {relative_to_scan}"
                ) from exc
            if _is_link_or_reparse(item_stat) or not stat.S_ISREG(item_stat.st_mode):
                continue
            if not include_hidden and _is_hidden(relative_to_scan):
                continue
            if include_globs and not _matches_patterns(relative_to_scan, include_globs):
                continue
            if exclude_globs and _matches_patterns(relative_to_scan, exclude_globs):
                continue
            if len(matches) >= max_results:
                truncation_reason = "max_results"
                break

            relative_to_source = candidate.relative_to(source_root).as_posix()
            match = {
                "path": relative_to_source,
                "size_bytes": item_stat.st_size,
            }
            prospective_bytes = len(
                json.dumps(
                    [*matches, match],
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            if prospective_bytes > MAX_FIND_RESULT_BYTES:
                truncation_reason = "result_bytes"
                break
            matches.append(match)
        if truncation_reason is not None:
            break

    return matches, scanned_entries, truncation_reason


def _search_entries(
    source_root: Path,
    relative_root: PurePosixPath,
    *,
    include_globs: list[str],
    exclude_globs: list[str],
    include_hidden: bool,
    max_results: int,
) -> tuple[list[dict[str, Any]], int, str | None]:
    """Resolve a search target as one explicit file or a directory scan."""
    target = _assert_real_path(source_root, relative_root)
    try:
        target_stat = os.lstat(target)
    except OSError as exc:
        raise SourceInspectionError("search path is unavailable") from exc
    if _is_link_or_reparse(target_stat):
        raise SourceInspectionError("search paths must not traverse links or reparse points")
    if stat.S_ISDIR(target_stat.st_mode):
        return _find_entries(
            source_root,
            relative_root,
            include_globs=include_globs,
            exclude_globs=exclude_globs,
            include_hidden=include_hidden,
            max_results=max_results,
        )
    if not stat.S_ISREG(target_stat.st_mode):
        raise SourceInspectionError("search path must identify a real file or directory")

    relative_to_source = target.relative_to(source_root).as_posix()
    selected_name = target.name
    if not include_hidden and _is_hidden(relative_to_source):
        return [], 1, None
    if include_globs and not _matches_patterns(selected_name, include_globs):
        return [], 1, None
    if exclude_globs and _matches_patterns(selected_name, exclude_globs):
        return [], 1, None
    return [
        {"path": relative_to_source, "size_bytes": target_stat.st_size}
    ], 1, None


def _read_regular_bytes(source_root: Path, relative: PurePosixPath) -> tuple[Path, bytes]:
    path = _assert_real_path(source_root, relative, expect_file=True)
    item_stat = os.lstat(path)
    if item_stat.st_size > MAX_READ_FILE_BYTES:
        raise SourceInspectionError(
            f"file exceeds the {MAX_READ_FILE_BYTES}-byte inspection limit"
        )
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise SourceInspectionError("file could not be read") from exc
    if len(data) > MAX_READ_FILE_BYTES:
        raise SourceInspectionError(
            f"file exceeds the {MAX_READ_FILE_BYTES}-byte inspection limit"
        )
    return path, data


def _find_operation(
    workspace: Path,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    allowed = {
        "operation",
        "source",
        "room_id",
        "path",
        "include_globs",
        "exclude_globs",
        "include_hidden",
        "max_results",
    }
    unknown = sorted(set(inputs) - allowed)
    if unknown:
        raise SourceInspectionError("unknown find field(s): " + ", ".join(unknown))

    source = inputs.get("source", "workspace")
    room_id = inputs.get("room_id")
    raw_path = inputs.get("path", ".")
    include_hidden = inputs.get("include_hidden", False)
    max_results = inputs.get("max_results", DEFAULT_FIND_RESULTS)
    if not isinstance(source, str):
        raise SourceInspectionError("source must be a string")
    if not isinstance(include_hidden, bool):
        raise SourceInspectionError("include_hidden must be true or false")
    if (
        not isinstance(max_results, int)
        or isinstance(max_results, bool)
        or not 1 <= max_results <= MAX_FIND_RESULTS
    ):
        raise SourceInspectionError(
            f"max_results must be an integer from 1 to {MAX_FIND_RESULTS}"
        )

    source_root, descriptor, core = _resolve_source(workspace, source, room_id)
    relative = _normalized_relative_path(raw_path, allow_dot=not core)
    if core:
        _validate_core_path(relative)
    include_globs = _normalize_patterns(inputs.get("include_globs"), "include_globs")
    exclude_globs = _normalize_patterns(inputs.get("exclude_globs"), "exclude_globs")
    matches, scanned_entries, truncation_reason = _find_entries(
        source_root,
        relative,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        include_hidden=include_hidden,
        max_results=max_results,
    )
    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": "inspect_source",
        "ok": True,
        "evidence": {
            "operation": "find",
            "source": descriptor,
            "path": raw_path,
            "matches": matches,
            "returned_count": len(matches),
            "scanned_entries": scanned_entries,
            "scan_limit_entries": MAX_SCAN_ENTRIES,
            "truncated": truncation_reason is not None,
            "truncation_reason": truncation_reason,
            "symlinks_followed": False,
        },
    }


def _search_operation(
    workspace: Path,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    allowed = {
        "operation",
        "source",
        "room_id",
        "path",
        "query",
        "include_globs",
        "exclude_globs",
        "include_hidden",
        "case_sensitive",
        "max_files",
        "max_matches",
    }
    unknown = sorted(set(inputs) - allowed)
    if unknown:
        raise SourceInspectionError("unknown search field(s): " + ", ".join(unknown))

    query = inputs.get("query")
    if (
        not isinstance(query, str)
        or not query
        or "\n" in query
        or "\r" in query
        or len(query) > MAX_QUERY_CHARS
    ):
        raise SourceInspectionError(
            f"query must be one non-empty line of at most {MAX_QUERY_CHARS} characters"
        )
    source = inputs.get("source", "workspace")
    room_id = inputs.get("room_id")
    raw_path = inputs.get("path", ".")
    include_hidden = inputs.get("include_hidden", False)
    case_sensitive = inputs.get("case_sensitive", True)
    max_files = inputs.get("max_files", DEFAULT_SEARCH_FILES)
    max_matches = inputs.get("max_matches", DEFAULT_SEARCH_MATCHES)
    if not isinstance(source, str):
        raise SourceInspectionError("source must be a string")
    if not isinstance(include_hidden, bool) or not isinstance(case_sensitive, bool):
        raise SourceInspectionError("include_hidden and case_sensitive must be booleans")
    if (
        not isinstance(max_files, int)
        or isinstance(max_files, bool)
        or not 1 <= max_files <= MAX_SEARCH_FILES
    ):
        raise SourceInspectionError(
            f"max_files must be an integer from 1 to {MAX_SEARCH_FILES}"
        )
    if (
        not isinstance(max_matches, int)
        or isinstance(max_matches, bool)
        or not 1 <= max_matches <= MAX_SEARCH_MATCHES
    ):
        raise SourceInspectionError(
            f"max_matches must be an integer from 1 to {MAX_SEARCH_MATCHES}"
        )

    source_root, descriptor, core = _resolve_source(workspace, source, room_id)
    relative = _normalized_relative_path(raw_path, allow_dot=not core)
    if core:
        _validate_core_path(relative)
    include_globs = _normalize_patterns(inputs.get("include_globs"), "include_globs")
    exclude_globs = _normalize_patterns(inputs.get("exclude_globs"), "exclude_globs")
    candidates, scanned_entries, candidate_truncation = _search_entries(
        source_root,
        relative,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        include_hidden=include_hidden,
        max_results=max_files,
    )

    pattern = re.compile(re.escape(query), 0 if case_sensitive else re.IGNORECASE)
    transient_matches: list[dict[str, Any]] = []
    durable_locations: list[dict[str, Any]] = []
    bytes_read = 0
    files_searched = 0
    skipped_non_text = 0
    skipped_oversize = 0
    truncation_reason = candidate_truncation

    for candidate in candidates:
        size = int(candidate["size_bytes"])
        if size > MAX_SEARCH_FILE_BYTES:
            skipped_oversize += 1
            continue
        if bytes_read + size > MAX_SEARCH_TOTAL_BYTES:
            truncation_reason = "total_bytes"
            break
        relative_file = _normalized_relative_path(candidate["path"], allow_dot=False)
        path = _assert_real_path(source_root, relative_file, expect_file=True)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise SourceInspectionError(
                f"search could not read {candidate['path']}"
            ) from exc
        bytes_read += len(data)
        if len(data) > MAX_SEARCH_FILE_BYTES:
            skipped_oversize += 1
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
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in pattern.finditer(line):
                if len(transient_matches) >= max_matches:
                    truncation_reason = "max_matches"
                    break
                start = match.start()
                excerpt_start = max(0, start - 80)
                excerpt = line[excerpt_start : excerpt_start + SEARCH_EXCERPT_CHARS]
                location = {
                    "path": candidate["path"],
                    "line": line_number,
                    "column": start + 1,
                }
                prospective = {
                    **location,
                    "excerpt": excerpt,
                    "excerpt_start_column": excerpt_start + 1,
                }
                prospective_bytes = len(
                    json.dumps(
                        [*transient_matches, prospective],
                        ensure_ascii=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
                if prospective_bytes > MAX_SEARCH_MATCH_BYTES:
                    truncation_reason = "result_bytes"
                    break
                transient_matches.append(prospective)
                durable_locations.append(location)
            if truncation_reason in {"max_matches", "result_bytes"}:
                break
        if truncation_reason in {"max_matches", "result_bytes"}:
            break

    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": "inspect_source",
        "ok": True,
        "evidence": {
            "operation": "search",
            "source": descriptor,
            "path": raw_path,
            "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
            "query_length": len(query),
            "case_sensitive": case_sensitive,
            "locations": durable_locations,
            "match_count": len(transient_matches),
            "files_searched": files_searched,
            "bytes_read": bytes_read,
            "scanned_entries": scanned_entries,
            "skipped_non_text": skipped_non_text,
            "skipped_oversize": skipped_oversize,
            "truncated": truncation_reason is not None,
            "truncation_reason": truncation_reason,
            "symlinks_followed": False,
        },
        "matches": transient_matches,
    }



def _normalize_search_queries(raw_queries: Any) -> list[str]:
    if (
        not isinstance(raw_queries, list)
        or not 1 <= len(raw_queries) <= MAX_BATCH_QUERIES
        or any(not isinstance(query, str) for query in raw_queries)
    ):
        raise SourceInspectionError(
            f"queries must contain 1 to {MAX_BATCH_QUERIES} strings"
        )
    queries = list(raw_queries)
    if len(set(queries)) != len(queries):
        raise SourceInspectionError("queries must not contain duplicates")
    for query in queries:
        if (
            not query
            or "\n" in query
            or "\r" in query
            or len(query) > MAX_QUERY_CHARS
        ):
            raise SourceInspectionError(
                f"each query must be one non-empty line of at most "
                f"{MAX_QUERY_CHARS} characters"
            )
    if sum(len(query) for query in queries) > MAX_BATCH_QUERY_CHARS:
        raise SourceInspectionError(
            f"combined query text exceeds {MAX_BATCH_QUERY_CHARS} characters"
        )
    return queries


def _search_many_operation(
    workspace: Path,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    allowed = {
        "operation",
        "source",
        "room_id",
        "path",
        "queries",
        "include_globs",
        "exclude_globs",
        "include_hidden",
        "case_sensitive",
        "max_files",
        "max_matches",
    }
    unknown = sorted(set(inputs) - allowed)
    if unknown:
        raise SourceInspectionError(
            "unknown search_many field(s): " + ", ".join(unknown)
        )

    queries = _normalize_search_queries(inputs.get("queries"))
    source = inputs.get("source", "workspace")
    room_id = inputs.get("room_id")
    raw_path = inputs.get("path", ".")
    include_hidden = inputs.get("include_hidden", False)
    case_sensitive = inputs.get("case_sensitive", True)
    max_files = inputs.get("max_files", DEFAULT_SEARCH_FILES)
    max_matches = inputs.get("max_matches", DEFAULT_SEARCH_MATCHES)
    if not isinstance(source, str):
        raise SourceInspectionError("source must be a string")
    if not isinstance(include_hidden, bool) or not isinstance(case_sensitive, bool):
        raise SourceInspectionError(
            "include_hidden and case_sensitive must be booleans"
        )
    if (
        not isinstance(max_files, int)
        or isinstance(max_files, bool)
        or not 1 <= max_files <= MAX_SEARCH_FILES
    ):
        raise SourceInspectionError(
            f"max_files must be an integer from 1 to {MAX_SEARCH_FILES}"
        )
    if (
        not isinstance(max_matches, int)
        or isinstance(max_matches, bool)
        or not 1 <= max_matches <= MAX_SEARCH_MATCHES
    ):
        raise SourceInspectionError(
            f"max_matches must be an integer from 1 to {MAX_SEARCH_MATCHES}"
        )

    source_root, descriptor, core = _resolve_source(workspace, source, room_id)
    relative = _normalized_relative_path(raw_path, allow_dot=not core)
    if core:
        _validate_core_path(relative)
    include_globs = _normalize_patterns(inputs.get("include_globs"), "include_globs")
    exclude_globs = _normalize_patterns(inputs.get("exclude_globs"), "exclude_globs")
    candidates, scanned_entries, candidate_truncation = _search_entries(
        source_root,
        relative,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        include_hidden=include_hidden,
        max_results=max_files,
    )

    flags = 0 if case_sensitive else re.IGNORECASE
    patterns = [re.compile(re.escape(query), flags) for query in queries]
    transient_matches: list[dict[str, Any]] = []
    durable_locations: list[list[dict[str, Any]]] = [[] for _ in queries]
    bytes_read = 0
    files_searched = 0
    skipped_non_text = 0
    skipped_oversize = 0
    truncation_reason = candidate_truncation

    for candidate in candidates:
        size = int(candidate["size_bytes"])
        if size > MAX_SEARCH_FILE_BYTES:
            skipped_oversize += 1
            continue
        if bytes_read + size > MAX_SEARCH_TOTAL_BYTES:
            truncation_reason = "total_bytes"
            break
        relative_file = _normalized_relative_path(candidate["path"], allow_dot=False)
        path = _assert_real_path(source_root, relative_file, expect_file=True)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise SourceInspectionError(
                f"search_many could not read {candidate['path']}"
            ) from exc
        bytes_read += len(data)
        if len(data) > MAX_SEARCH_FILE_BYTES:
            skipped_oversize += 1
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
        for line_number, line in enumerate(text.splitlines(), start=1):
            stop = False
            for query_index, pattern in enumerate(patterns):
                for match in pattern.finditer(line):
                    if len(transient_matches) >= max_matches:
                        truncation_reason = "max_matches"
                        stop = True
                        break
                    start = match.start()
                    excerpt_start = max(0, start - 80)
                    excerpt = line[
                        excerpt_start : excerpt_start + SEARCH_EXCERPT_CHARS
                    ]
                    location = {
                        "path": candidate["path"],
                        "line": line_number,
                        "column": start + 1,
                    }
                    prospective = {
                        "query_index": query_index,
                        **location,
                        "excerpt": excerpt,
                        "excerpt_start_column": excerpt_start + 1,
                    }
                    prospective_bytes = len(
                        json.dumps(
                            [*transient_matches, prospective],
                            ensure_ascii=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    )
                    if prospective_bytes > MAX_SEARCH_MATCH_BYTES:
                        truncation_reason = "result_bytes"
                        stop = True
                        break
                    transient_matches.append(prospective)
                    durable_locations[query_index].append(location)
                if stop:
                    break
            if stop:
                break
        if truncation_reason in {"max_matches", "result_bytes"}:
            break

    grouped_results: list[dict[str, Any]] = []
    durable_queries: list[dict[str, Any]] = []
    for index, query in enumerate(queries):
        matches = [
            {key: value for key, value in match.items() if key != "query_index"}
            for match in transient_matches
            if match["query_index"] == index
        ]
        grouped_results.append({"query": query, "matches": matches})
        durable_queries.append(
            {
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                "query_length": len(query),
                "locations": durable_locations[index],
                "match_count": len(matches),
            }
        )

    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": "inspect_source",
        "ok": True,
        "evidence": {
            "operation": "search_many",
            "source": descriptor,
            "path": raw_path,
            "queries": durable_queries,
            "query_count": len(queries),
            "match_count": len(transient_matches),
            "case_sensitive": case_sensitive,
            "files_searched": files_searched,
            "bytes_read": bytes_read,
            "scanned_entries": scanned_entries,
            "skipped_non_text": skipped_non_text,
            "skipped_oversize": skipped_oversize,
            "truncated": truncation_reason is not None,
            "truncation_reason": truncation_reason,
            "symlinks_followed": False,
        },
        "results": grouped_results,
    }


def _read_operation(
    workspace: Path,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    allowed = {
        "operation",
        "source",
        "room_id",
        "path",
        "start_line",
        "max_lines",
        "max_bytes",
    }
    unknown = sorted(set(inputs) - allowed)
    if unknown:
        raise SourceInspectionError("unknown read field(s): " + ", ".join(unknown))

    source = inputs.get("source", "workspace")
    room_id = inputs.get("room_id")
    raw_path = inputs.get("path")
    start_line = inputs.get("start_line", 1)
    max_lines = inputs.get("max_lines", 400)
    max_bytes = inputs.get("max_bytes", MAX_READ_OUTPUT_BYTES)
    if not isinstance(source, str):
        raise SourceInspectionError("source must be a string")
    if not isinstance(raw_path, str):
        raise SourceInspectionError("read requires path")
    if (
        not isinstance(start_line, int)
        or isinstance(start_line, bool)
        or start_line < 1
    ):
        raise SourceInspectionError("start_line must be a positive integer")
    if (
        not isinstance(max_lines, int)
        or isinstance(max_lines, bool)
        or not 1 <= max_lines <= MAX_READ_LINES
    ):
        raise SourceInspectionError(
            f"max_lines must be an integer from 1 to {MAX_READ_LINES}"
        )
    if (
        not isinstance(max_bytes, int)
        or isinstance(max_bytes, bool)
        or not 1 <= max_bytes <= MAX_READ_OUTPUT_BYTES
    ):
        raise SourceInspectionError(
            f"max_bytes must be an integer from 1 to {MAX_READ_OUTPUT_BYTES}"
        )

    source_root, descriptor, core = _resolve_source(workspace, source, room_id)
    relative = _normalized_relative_path(raw_path, allow_dot=False)
    if core:
        _validate_core_path(relative)
    path, data = _read_regular_bytes(source_root, relative)
    if b"\x00" in data:
        raise SourceInspectionError("read supports UTF-8 text files only")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceInspectionError("read supports UTF-8 text files only") from exc
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.splitlines(keepends=True)
    start_index = min(start_line - 1, len(lines))
    selected = lines[start_index : start_index + max_lines]
    output_parts: list[str] = []
    output_bytes = 0
    byte_truncated = False
    for line in selected:
        encoded = line.encode("utf-8")
        remaining = max_bytes - output_bytes
        if remaining <= 0:
            byte_truncated = True
            break
        if len(encoded) <= remaining:
            output_parts.append(line)
            output_bytes += len(encoded)
            continue
        output_parts.append(encoded[:remaining].decode("utf-8", errors="ignore"))
        output_bytes = max_bytes
        byte_truncated = True
        break

    returned_lines = len("".join(output_parts).splitlines())
    line_truncated = start_index + len(selected) < len(lines)
    truncated = byte_truncated or line_truncated
    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": "inspect_source",
        "ok": True,
        "evidence": {
            "operation": "read",
            "source": descriptor,
            "path": raw_path,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
            "start_line": start_line,
            "returned_lines": returned_lines,
            "returned_bytes": output_bytes,
            "truncated": truncated,
            "truncation_reason": (
                "max_bytes"
                if byte_truncated
                else "max_lines"
                if line_truncated
                else None
            ),
        },
        "content": "".join(output_parts),
    }



def _read_many_operation(
    workspace: Path,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    allowed = {"operation", "source", "room_id", "reads", "max_bytes"}
    unknown = sorted(set(inputs) - allowed)
    if unknown:
        raise SourceInspectionError(
            "unknown read_many field(s): " + ", ".join(unknown)
        )

    source = inputs.get("source", "workspace")
    room_id = inputs.get("room_id")
    reads = inputs.get("reads")
    max_bytes = inputs.get("max_bytes", MAX_BATCH_READ_OUTPUT_BYTES)
    if not isinstance(source, str):
        raise SourceInspectionError("source must be a string")
    if (
        not isinstance(reads, list)
        or not 1 <= len(reads) <= MAX_BATCH_READS
        or any(not isinstance(item, dict) for item in reads)
    ):
        raise SourceInspectionError(
            f"reads must contain 1 to {MAX_BATCH_READS} objects"
        )
    if (
        not isinstance(max_bytes, int)
        or isinstance(max_bytes, bool)
        or not 1 <= max_bytes <= MAX_BATCH_READ_OUTPUT_BYTES
    ):
        raise SourceInspectionError(
            f"max_bytes must be an integer from 1 to "
            f"{MAX_BATCH_READ_OUTPUT_BYTES}"
        )

    transient_reads: list[dict[str, Any]] = []
    durable_reads: list[dict[str, Any]] = []
    total_bytes = 0
    batch_truncated = False
    for item in reads:
        allowed_item = {"path", "start_line", "max_lines", "max_bytes"}
        unknown_item = sorted(set(item) - allowed_item)
        if unknown_item:
            raise SourceInspectionError(
                "unknown read_many item field(s): " + ", ".join(unknown_item)
            )
        if "path" not in item:
            raise SourceInspectionError("each read_many item requires path")
        remaining = max_bytes - total_bytes
        if remaining <= 0:
            batch_truncated = True
            break
        item_max_bytes = item.get("max_bytes", MAX_READ_OUTPUT_BYTES)
        if (
            not isinstance(item_max_bytes, int)
            or isinstance(item_max_bytes, bool)
            or not 1 <= item_max_bytes <= MAX_READ_OUTPUT_BYTES
        ):
            raise SourceInspectionError(
                f"read item max_bytes must be an integer from 1 to "
                f"{MAX_READ_OUTPUT_BYTES}"
            )
        request = {
            "operation": "read",
            "source": source,
            "path": item["path"],
            "start_line": item.get("start_line", 1),
            "max_lines": item.get("max_lines", 400),
            "max_bytes": min(item_max_bytes, remaining),
        }
        if room_id is not None:
            request["room_id"] = room_id
        result = _read_operation(workspace, request)
        content = result["content"]
        evidence = result["evidence"]
        returned_bytes = int(evidence["returned_bytes"])
        total_bytes += returned_bytes
        durable_reads.append(evidence)
        transient_reads.append(
            {
                "path": evidence["path"],
                "start_line": evidence["start_line"],
                "content": content,
            }
        )
        if request["max_bytes"] < item_max_bytes and evidence["truncated"]:
            batch_truncated = True
            break

    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": "inspect_source",
        "ok": True,
        "evidence": {
            "operation": "read_many",
            "source": (
                durable_reads[0]["source"]
                if durable_reads
                else {"kind": source}
            ),
            "reads": durable_reads,
            "requested_count": len(reads),
            "returned_count": len(transient_reads),
            "returned_bytes": total_bytes,
            "truncated": batch_truncated or len(transient_reads) < len(reads),
            "truncation_reason": (
                "batch_max_bytes"
                if batch_truncated or len(transient_reads) < len(reads)
                else None
            ),
        },
        "reads": transient_reads,
    }


def inspect_source(workspace: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(inputs, dict):
        raise SourceInspectionError("capability input must be a JSON object")
    operation = inputs.get("operation")
    if operation == "sources":
        if set(inputs) != {"operation"}:
            raise SourceInspectionError("sources accepts only the operation field")
        return {
            "codex_room_capability": CAPABILITY_MARKER,
            "capability": "inspect_source",
            "ok": True,
            "evidence": {
                "operation": "sources",
                **_source_inventory(workspace),
            },
        }
    if operation == "find":
        return _find_operation(workspace, inputs)
    if operation == "search":
        return _search_operation(workspace, inputs)
    if operation == "search_many":
        return _search_many_operation(workspace, inputs)
    if operation == "read":
        return _read_operation(workspace, inputs)
    if operation == "read_many":
        return _read_many_operation(workspace, inputs)
    raise SourceInspectionError(
        "operation must be 'sources', 'find', 'search', 'search_many', "
        "'read', or 'read_many'"
    )


INSPECT_SOURCE_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["operation"],
    "properties": {
        "operation": {
            "type": "string",
            "enum": ["sources", "find", "search", "search_many", "read", "read_many"],
        },
        "source": {
            "type": "string",
            "enum": ["workspace", "core", "room"],
            "default": "workspace",
        },
        "room_id": {"type": ["string", "null"]},
        "path": {"type": "string", "default": "."},
        "query": {"type": "string", "minLength": 1, "maxLength": MAX_QUERY_CHARS},
        "queries": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_BATCH_QUERIES,
            "items": {"type": "string", "minLength": 1, "maxLength": MAX_QUERY_CHARS},
        },
        "reads": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_BATCH_READS,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path"],
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer", "minimum": 1, "default": 1},
                    "max_lines": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_READ_LINES,
                        "default": 400,
                    },
                    "max_bytes": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_READ_OUTPUT_BYTES,
                        "default": MAX_READ_OUTPUT_BYTES,
                    },
                },
            },
        },
        "include_globs": {"type": "array", "items": {"type": "string"}, "default": []},
        "exclude_globs": {"type": "array", "items": {"type": "string"}, "default": []},
        "include_hidden": {"type": "boolean", "default": False},
        "case_sensitive": {"type": "boolean", "default": True},
        "max_results": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_FIND_RESULTS,
            "default": DEFAULT_FIND_RESULTS,
        },
        "max_files": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_SEARCH_FILES,
            "default": DEFAULT_SEARCH_FILES,
        },
        "max_matches": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_SEARCH_MATCHES,
            "default": DEFAULT_SEARCH_MATCHES,
        },
        "start_line": {"type": "integer", "minimum": 1, "default": 1},
        "max_lines": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_READ_LINES,
            "default": 400,
        },
        "max_bytes": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_READ_OUTPUT_BYTES,
            "default": MAX_READ_OUTPUT_BYTES,
        },
    },
}

INSPECT_SOURCE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["codex_room_capability", "capability", "ok", "evidence"],
    "properties": {
        "codex_room_capability": {"const": CAPABILITY_MARKER},
        "capability": {"const": "inspect_source"},
        "ok": {"type": "boolean"},
        "evidence": {"type": "object"},
        "content": {"type": "string"},
        "matches": {"type": "array"},
        "results": {"type": "array"},
        "reads": {"type": "array"},
        "capability_version": {"type": "string"},
        "implementation_sha256": {"type": "string"},
        "durable_result_fields": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}

INSPECT_SOURCE_IMPLEMENTATION_COMPONENTS = (
    MAX_FIND_RESULTS,
    DEFAULT_FIND_RESULTS,
    MAX_SCAN_ENTRIES,
    MAX_FIND_RESULT_BYTES,
    MAX_SEARCH_FILES,
    DEFAULT_SEARCH_FILES,
    MAX_SEARCH_MATCHES,
    DEFAULT_SEARCH_MATCHES,
    MAX_SEARCH_FILE_BYTES,
    MAX_SEARCH_TOTAL_BYTES,
    MAX_SEARCH_MATCH_BYTES,
    MAX_QUERY_CHARS,
    SEARCH_EXCERPT_CHARS,
    MAX_READ_FILE_BYTES,
    MAX_READ_OUTPUT_BYTES,
    MAX_READ_LINES,
    MAX_BATCH_QUERIES,
    MAX_BATCH_QUERY_CHARS,
    MAX_BATCH_READS,
    MAX_BATCH_READ_OUTPUT_BYTES,
    tuple(sorted(CORE_READ_ENTRIES)),
    _ROOM_ID.pattern,
    _is_link_or_reparse,
    _normalized_relative_path,
    _assert_real_path,
    _validate_core_path,
    _canonical_room_shared,
    _resolve_source,
    _existing_core_entries,
    _source_inventory,
    _normalize_patterns,
    _glob_variants,
    _matches_patterns,
    _is_hidden,
    _find_entries,
    _read_regular_bytes,
    _find_operation,
    _search_operation,
    _normalize_search_queries,
    _search_many_operation,
    _read_operation,
    _read_many_operation,
    inspect_source,
)
