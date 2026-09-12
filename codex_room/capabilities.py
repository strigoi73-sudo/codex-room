from __future__ import annotations

import argparse
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

CAPABILITY_MARKER = 1
REGISTRY_MARKER = 1
MAX_JSON_BYTES = 50 * 1024 * 1024
MAX_FIND_FILES_RESULTS = 200
DEFAULT_FIND_FILES_RESULTS = 100
MAX_FIND_FILES_SCANNED_ENTRIES = 100_000
MAX_FIND_FILES_MATCH_BYTES = 48 * 1024
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
                    ensure_ascii=False,
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
}


def list_capabilities() -> dict[str, Any]:
    summaries = [CORE_CAPABILITIES[key].summary() for key in sorted(CORE_CAPABILITIES)]
    return {
        "codex_room_registry": REGISTRY_MARKER,
        "operation": "list",
        "capabilities": summaries,
    }


def inspect_capability(capability_id: str) -> dict[str, Any]:
    spec = CORE_CAPABILITIES.get(capability_id)
    if spec is None:
        raise CapabilityUsageError(f"unknown capability: {capability_id}")
    return {
        "codex_room_registry": REGISTRY_MARKER,
        "operation": "inspect",
        "capability": spec.manifest(),
    }


def invoke_capability(
    root: Path, capability_id: str, inputs: dict[str, Any]
) -> dict[str, Any]:
    spec = CORE_CAPABILITIES.get(capability_id)
    if spec is None:
        raise CapabilityUsageError(f"unknown capability: {capability_id}")
    if not isinstance(inputs, dict):
        raise CapabilityUsageError("capability input must be a JSON object")
    result = spec.handler(root, inputs)
    result["capability_version"] = spec.version
    result["implementation_sha256"] = spec.implementation_sha256()
    result["durable_result_fields"] = list(spec.durable_result_fields)
    return result


def _error_payload(
    message: str, *, capability_id: str | None = None, operation: str = "invoke"
) -> dict[str, Any]:
    if operation in {"list", "inspect"}:
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

    inspect_parser = subparsers.add_parser(
        "inspect", help="Inspect one registered capability manifest."
    )
    inspect_parser.add_argument("capability_id")

    invoke_parser = subparsers.add_parser(
        "invoke", help="Invoke one registered deterministic capability."
    )
    invoke_parser.add_argument("capability_id")
    invoke_parser.add_argument(
        "--input-json",
        required=True,
        help="One JSON object matching the capability input schema.",
    )

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


def _print_result(result: dict[str, Any]) -> None:
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            result = list_capabilities()
        elif args.command == "inspect":
            result = inspect_capability(args.capability_id)
        elif args.command == "invoke":
            try:
                inputs = json.loads(args.input_json)
            except json.JSONDecodeError as exc:
                raise CapabilityUsageError(f"input JSON is invalid: {exc}") from exc
            result = invoke_capability(Path.cwd(), args.capability_id, inputs)
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
        capability_id = getattr(args, "capability_id", None)
        operation = args.command if args.command in {"list", "inspect"} else "invoke"
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
