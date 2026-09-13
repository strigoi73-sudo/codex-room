from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


DRAFTS_PATH = PurePosixPath(".codex-room/capability-drafts")
MANIFEST_NAME = "manifest.json"
ENTRYPOINT_NAME = "capability.py"
RUNTIME_KIND = "python"
RUNTIME_PROTOCOL = "stdio-json-v1"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_ENTRYPOINT_BYTES = 256 * 1024
MAX_DESCRIPTION_CHARS = 1000
MAX_SIDE_EFFECTS_CHARS = 1000
_CAPABILITY_ID_RE = re.compile(r"[a-z][a-z0-9_]{0,63}")
_VERSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}
_PERMISSION_KEYS = {
    "workspace_read",
    "workspace_write",
    "network",
    "external_process",
}
_REQUIRED_FIELDS = {
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
}


class CustomCapabilityPackageError(ValueError):
    """A draft custom capability package is unsafe or structurally invalid."""


@dataclass(frozen=True, slots=True)
class CustomCapabilityPackage:
    capability_id: str
    version: str
    description: str
    scope: str
    runtime: dict[str, str]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    durable_result_fields: tuple[str, ...]
    permissions: dict[str, bool]
    side_effects: str
    manifest_sha256: str
    implementation_sha256: str
    package_sha256: str
    manifest_bytes: bytes
    entrypoint_bytes: bytes

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.capability_id,
            "origin": "custom",
            "scope": self.scope,
            "version": self.version,
            "implementation_sha256": self.implementation_sha256,
            "package_sha256": self.package_sha256,
        }

    def manifest(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "description": self.description,
            "runtime": dict(self.runtime),
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "durable_result_fields": list(self.durable_result_fields),
            "permissions": dict(self.permissions),
            "side_effects": self.side_effects,
            "manifest_sha256": self.manifest_sha256,
            "permission_enforcement": {
                "mode": "ambient_room_sandbox",
                "per_capability_enforcement": False,
            },
        }


def draft_path(workspace: Path, capability_id: str) -> Path:
    _validate_identifier(capability_id, "capability id", _CAPABILITY_ID_RE)
    return workspace.joinpath(*DRAFTS_PATH.parts, capability_id)


def load_custom_capability_draft(
    workspace: Path, capability_id: str
) -> CustomCapabilityPackage:
    """Load and structurally verify one bounded custom capability draft package."""
    package_root = draft_path(workspace, capability_id)
    _assert_safe_draft_directory_chain(workspace, package_root)
    manifest_path = package_root / MANIFEST_NAME
    entrypoint_path = package_root / ENTRYPOINT_NAME

    manifest_bytes = _read_regular_file(
        manifest_path, "custom capability manifest", MAX_MANIFEST_BYTES
    )
    try:
        raw = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CustomCapabilityPackageError(
            "Custom capability manifest must be valid UTF-8 JSON"
        ) from exc
    if not isinstance(raw, dict):
        raise CustomCapabilityPackageError("Custom capability manifest must be a JSON object")
    missing = sorted(_REQUIRED_FIELDS - set(raw))
    unknown = sorted(set(raw) - _REQUIRED_FIELDS)
    if missing:
        raise CustomCapabilityPackageError(
            f"Custom capability manifest is missing fields: {missing}"
        )
    if unknown:
        raise CustomCapabilityPackageError(
            f"Custom capability manifest has unknown fields: {unknown}"
        )
    if raw["schema_version"] != 1:
        raise CustomCapabilityPackageError(
            "Custom capability manifest schema_version must be 1"
        )

    manifest_id = raw["id"]
    _validate_identifier(manifest_id, "manifest id", _CAPABILITY_ID_RE)
    if manifest_id != capability_id:
        raise CustomCapabilityPackageError(
            "Custom capability manifest id must match its draft directory"
        )
    version = raw["version"]
    _validate_identifier(version, "version", _VERSION_RE)

    description = raw["description"]
    if (
        not isinstance(description, str)
        or not description.strip()
        or len(description) > MAX_DESCRIPTION_CHARS
    ):
        raise CustomCapabilityPackageError("Custom capability description is invalid")

    if raw["scope"] != "lineage":
        raise CustomCapabilityPackageError(
            "Custom capability scope must be 'lineage' in package schema v1"
        )

    runtime = raw["runtime"]
    expected_runtime = {
        "kind": RUNTIME_KIND,
        "entrypoint": ENTRYPOINT_NAME,
        "protocol": RUNTIME_PROTOCOL,
    }
    if runtime != expected_runtime:
        raise CustomCapabilityPackageError(
            "Custom capability runtime must use python capability.py with stdio-json-v1"
        )

    input_schema = _validate_object_schema(raw["input_schema"], "input_schema")
    output_schema = _validate_object_schema(raw["output_schema"], "output_schema")
    _validate_output_ok_contract(output_schema)

    durable_result_fields = _validate_durable_result_fields(
        raw["durable_result_fields"], output_schema
    )
    permissions = _validate_permissions(raw["permissions"])

    side_effects = raw["side_effects"]
    if (
        not isinstance(side_effects, str)
        or not side_effects.strip()
        or len(side_effects) > MAX_SIDE_EFFECTS_CHARS
    ):
        raise CustomCapabilityPackageError("Custom capability side_effects is invalid")

    entrypoint_bytes = _read_regular_file(
        entrypoint_path, "custom capability entrypoint", MAX_ENTRYPOINT_BYTES
    )
    if b"\x00" in entrypoint_bytes:
        raise CustomCapabilityPackageError("Custom capability entrypoint must not contain NUL")
    try:
        entrypoint_text = entrypoint_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CustomCapabilityPackageError(
            "Custom capability entrypoint must be valid UTF-8 Python"
        ) from exc
    try:
        ast.parse(entrypoint_text, filename=ENTRYPOINT_NAME)
    except SyntaxError as exc:
        raise CustomCapabilityPackageError(
            f"Custom capability entrypoint is not valid Python: {exc.msg}"
        ) from exc

    _reject_extra_package_entries(package_root)

    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    implementation_sha256 = hashlib.sha256(entrypoint_bytes).hexdigest()
    package_digest = hashlib.sha256()
    package_digest.update(b"codex-room-custom-capability-package-v1\x00")
    package_digest.update(b"manifest.json\x00")
    package_digest.update(manifest_bytes)
    package_digest.update(b"\x00capability.py\x00")
    package_digest.update(entrypoint_bytes)

    return CustomCapabilityPackage(
        capability_id=manifest_id,
        version=version,
        description=description.strip(),
        scope="lineage",
        runtime=dict(runtime),
        input_schema=input_schema,
        output_schema=output_schema,
        durable_result_fields=durable_result_fields,
        permissions=permissions,
        side_effects=side_effects.strip(),
        manifest_sha256=manifest_sha256,
        implementation_sha256=implementation_sha256,
        package_sha256=package_digest.hexdigest(),
        manifest_bytes=manifest_bytes,
        entrypoint_bytes=entrypoint_bytes,
    )


def _validate_identifier(value: Any, label: str, pattern: re.Pattern[str]) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise CustomCapabilityPackageError(f"Custom capability {label} is invalid")
    if label in {"capability id", "manifest id"} and value.casefold() in _WINDOWS_RESERVED:
        raise CustomCapabilityPackageError(f"Custom capability {label} is reserved on Windows")


def _assert_safe_draft_directory_chain(workspace: Path, package_root: Path) -> None:
    current = workspace
    for part in (*DRAFTS_PATH.parts, package_root.name):
        current = current / part
        if not os.path.lexists(current):
            continue
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise CustomCapabilityPackageError(
                f"Custom capability draft path could not be inspected: {exc}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise CustomCapabilityPackageError(
                "Custom capability draft path must use real directories without symlinks"
            )


def _read_regular_file(path: Path, label: str, byte_limit: int) -> bytes:
    if not os.path.lexists(path):
        raise CustomCapabilityPackageError(f"{label} is missing")
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CustomCapabilityPackageError(f"{label} could not be inspected: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CustomCapabilityPackageError(f"{label} must be a regular file")
    if metadata.st_size > byte_limit:
        raise CustomCapabilityPackageError(f"{label} exceeds the size limit")
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise CustomCapabilityPackageError(f"{label} could not be read: {exc}") from exc
    if len(data) > byte_limit:
        raise CustomCapabilityPackageError(f"{label} exceeds the size limit")
    return data


def _validate_object_schema(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("type") != "object":
        raise CustomCapabilityPackageError(f"Custom capability {label} must describe an object")
    properties = value.get("properties", {})
    if not isinstance(properties, dict):
        raise CustomCapabilityPackageError(
            f"Custom capability {label}.properties must be an object"
        )
    required = value.get("required", [])
    if (
        not isinstance(required, list)
        or any(not isinstance(item, str) or not item for item in required)
        or len(set(required)) != len(required)
    ):
        raise CustomCapabilityPackageError(
            f"Custom capability {label}.required must be unique field names"
        )
    missing_properties = sorted(set(required) - set(properties))
    if missing_properties:
        raise CustomCapabilityPackageError(
            f"Custom capability {label}.required names undeclared properties: "
            f"{missing_properties}"
        )
    return value


def _validate_output_ok_contract(output_schema: dict[str, Any]) -> None:
    properties = output_schema.get("properties", {})
    ok_schema = properties.get("ok")
    if not isinstance(ok_schema, dict) or ok_schema.get("type") != "boolean":
        raise CustomCapabilityPackageError(
            "Custom capability output_schema must declare boolean property 'ok'"
        )
    if "ok" not in output_schema.get("required", []):
        raise CustomCapabilityPackageError(
            "Custom capability output_schema must require property 'ok'"
        )


def _validate_durable_result_fields(
    value: Any, output_schema: dict[str, Any]
) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
    ):
        raise CustomCapabilityPackageError(
            "Custom capability durable_result_fields must be unique field names"
        )
    reserved = {
        "codex_room_capability",
        "capability",
        "capability_version",
        "implementation_sha256",
        "package_sha256",
        "durable_result_fields",
        "ok",
    }
    if reserved.intersection(value):
        raise CustomCapabilityPackageError(
            "Custom capability durable_result_fields contains reserved envelope fields"
        )
    properties = output_schema.get("properties", {})
    missing = sorted(set(value) - set(properties))
    if missing:
        raise CustomCapabilityPackageError(
            "Custom capability durable_result_fields names undeclared output properties: "
            f"{missing}"
        )
    return tuple(value)


def _validate_permissions(value: Any) -> dict[str, bool]:
    if not isinstance(value, dict) or set(value) != _PERMISSION_KEYS:
        raise CustomCapabilityPackageError(
            "Custom capability permissions must declare exactly workspace_read, "
            "workspace_write, network, and external_process"
        )
    if any(type(item) is not bool for item in value.values()):
        raise CustomCapabilityPackageError(
            "Custom capability permission values must be booleans"
        )
    return {key: value[key] for key in sorted(_PERMISSION_KEYS)}


def _reject_extra_package_entries(package_root: Path) -> None:
    try:
        entries = list(package_root.iterdir())
    except OSError as exc:
        raise CustomCapabilityPackageError(
            f"Custom capability package could not be listed: {exc}"
        ) from exc
    allowed = {MANIFEST_NAME, ENTRYPOINT_NAME}
    extras = sorted(item.name for item in entries if item.name not in allowed)
    if extras:
        raise CustomCapabilityPackageError(
            f"Custom capability package contains unsupported entries: {extras}"
        )
