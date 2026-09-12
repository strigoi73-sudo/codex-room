from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

CAPABILITY_MARKER = 1
MAX_JSON_BYTES = 50 * 1024 * 1024
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class CapabilityUsageError(ValueError):
    pass


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


def _error_payload(message: str) -> dict[str, Any]:
    return {
        "codex_room_capability": CAPABILITY_MARKER,
        "capability": "assert_file",
        "ok": False,
        "error": {"code": "invalid_request", "message": message},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-room-cap")
    subparsers = parser.add_subparsers(dest="command", required=True)
    assert_file_parser = subparsers.add_parser(
        "assert-file",
        help="Run exact read-only assertions against one Room-workspace file.",
    )
    assert_file_parser.add_argument("path")
    assert_file_parser.add_argument("--exists", action="store_true")
    assert_file_parser.add_argument("--sha256", dest="sha256_equals")
    assert_file_parser.add_argument("--json-valid", action="store_true")
    assert_file_parser.add_argument(
        "--required-key", action="append", default=[], dest="required_keys"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = assert_file(
            Path.cwd(),
            args.path,
            exists=args.exists,
            sha256_equals=args.sha256_equals,
            json_valid=args.json_valid,
            required_keys=args.required_keys,
        )
    except CapabilityUsageError as exc:
        print(json.dumps(_error_payload(str(exc)), sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
