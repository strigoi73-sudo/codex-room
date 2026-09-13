from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .custom_capabilities import (
    ENTRYPOINT_NAME,
    CustomCapabilityPackage,
    CustomCapabilityPackageError,
    load_custom_capability_package,
)
from .custom_capability_registration import (
    CASE_TIMEOUT_SECONDS,
    MAX_CASE_JSON_BYTES,
    MAX_PROCESS_OUTPUT_BYTES,
    PACKAGES_PATH,
    REGISTRATIONS_PATH,
    VERIFICATIONS_PATH,
    CustomCapabilityPublicationError,
    CustomCapabilityRegistration,
    CustomCapabilityVerificationError,
    VerificationReceipt,
)


BINDINGS_PATH = Path("custom-capabilities") / "bindings"
MAX_REGISTRY_RECORD_BYTES = 256 * 1024
_ROOM_ID = re.compile(r"room_[A-Za-z0-9_-]{1,128}")
_CAPABILITY_ID = re.compile(r"[a-z][a-z0-9_]{0,63}")
_HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
_RESERVED_RESULT_FIELDS = {
    "codex_room_capability",
    "capability",
    "capability_version",
    "implementation_sha256",
    "package_sha256",
    "registration_sha256",
    "verification_sha256",
    "durable_result_fields",
}


class CustomCapabilityRegistryError(ValueError):
    """A published custom capability binding or invocation is invalid."""


@dataclass(frozen=True, slots=True)
class RoomCapabilityContext:
    workspace: Path
    data_root: Path
    room_id: str


@dataclass(frozen=True, slots=True)
class BoundCustomCapability:
    room_id: str
    binding_sha256: str
    registration: CustomCapabilityRegistration
    receipt: VerificationReceipt
    package: CustomCapabilityPackage
    package_root: Path

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.package.capability_id,
            "description": self.package.description,
            "origin": "custom",
            "scope": "lineage",
            "version": self.package.version,
            "implementation_sha256": self.package.implementation_sha256,
            "package_sha256": self.package.package_sha256,
            "registration_sha256": self.registration.registration_sha256,
            "inspect": f"codex-room-cap inspect {self.package.capability_id}",
        }

    def manifest(self) -> dict[str, Any]:
        return {
            **self.package.manifest(),
            "verification": {
                "status": "verified",
                "verification_sha256": self.receipt.verification_sha256,
                "registration_sha256": self.registration.registration_sha256,
                "package_sha256": self.package.package_sha256,
                "case_plan_sha256": self.receipt.case_plan_sha256,
                "case_count": len(self.receipt.cases),
            },
            "invocation": {
                "inspect": f"codex-room-cap inspect {self.package.capability_id}",
                "invoke": (
                    f"codex-room-cap invoke {self.package.capability_id} "
                    "--input-json JSON_OBJECT"
                ),
            },
        }


def resolve_room_capability_context(workspace: Path) -> RoomCapabilityContext | None:
    """Resolve only the canonical data/rooms/<room_id>/shared layout."""
    try:
        resolved = workspace.resolve(strict=True)
    except OSError:
        return None
    if resolved.name != "shared":
        return None
    room_root = resolved.parent
    rooms_root = room_root.parent
    if rooms_root.name != "rooms" or not _ROOM_ID.fullmatch(room_root.name):
        return None
    data_root = rooms_root.parent
    return RoomCapabilityContext(
        workspace=resolved,
        data_root=data_root,
        room_id=room_root.name,
    )


def bind_custom_registration(
    data_root: Path,
    room_id: str,
    registration_sha256: str,
    *,
    reserved_capability_ids: set[str] | frozenset[str] = frozenset(),
) -> BoundCustomCapability:
    """Bind one exact verified registration to one Room/capability ID.

    Binding is single-assignment in schema v1. Repeating the same binding is
    idempotent; replacing it requires a future explicit supersession mechanism.
    """
    _validate_room_id(room_id)
    _validate_sha(registration_sha256, "registration SHA-256")
    resolved = _resolve_registration(
        data_root,
        registration_sha256,
        expected_room_id=room_id,
    )
    capability_id = resolved.package.capability_id
    if capability_id in reserved_capability_ids:
        raise CustomCapabilityRegistryError(
            f"Custom capability id collides with reserved CORE capability: {capability_id}"
        )

    binding_root = data_root / BINDINGS_PATH / room_id
    _ensure_real_registry_directory(data_root, data_root / "custom-capabilities")
    _ensure_real_registry_directory(data_root, data_root / BINDINGS_PATH)
    _ensure_real_registry_directory(data_root, binding_root)
    binding_payload = {
        "schema_version": 1,
        "room_id": room_id,
        "id": capability_id,
        "registration_sha256": registration_sha256,
    }
    binding_sha256 = hashlib.sha256(_canonical_json_bytes(binding_payload)).hexdigest()
    binding = {
        **binding_payload,
        "binding_sha256": binding_sha256,
    }
    binding_path = binding_root / f"{capability_id}.json"
    exact_bytes = _canonical_json_bytes(binding)
    if os.path.lexists(binding_path):
        existing = _read_json_record(binding_path, "custom capability binding")
        if existing != binding:
            raise CustomCapabilityRegistryError(
                f"Custom capability '{capability_id}' already has a different Room binding"
            )
    else:
        _write_exclusive(binding_path, exact_bytes, "custom capability binding")
    return BoundCustomCapability(
        room_id=room_id,
        binding_sha256=binding_sha256,
        registration=resolved.registration,
        receipt=resolved.receipt,
        package=resolved.package,
        package_root=resolved.package_root,
    )


def load_room_custom_capabilities(
    data_root: Path,
    room_id: str,
    *,
    reserved_capability_ids: set[str] | frozenset[str] = frozenset(),
) -> dict[str, BoundCustomCapability]:
    _validate_room_id(room_id)
    binding_root = data_root / BINDINGS_PATH / room_id
    if not os.path.lexists(binding_root):
        return {}
    _assert_real_directory(binding_root, "Room custom capability binding directory")
    try:
        entries = sorted(binding_root.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        raise CustomCapabilityRegistryError(
            f"Room custom capability bindings could not be listed: {exc}"
        ) from exc

    resolved: dict[str, BoundCustomCapability] = {}
    for path in entries:
        if path.suffix != ".json":
            raise CustomCapabilityRegistryError(
                f"Room custom capability binding directory contains unsupported entry: {path.name}"
            )
        raw = _read_json_record(path, "custom capability binding")
        required = {
            "schema_version",
            "room_id",
            "id",
            "registration_sha256",
            "binding_sha256",
        }
        if set(raw) != required or raw.get("schema_version") != 1:
            raise CustomCapabilityRegistryError("Custom capability binding schema is invalid")
        if raw.get("room_id") != room_id:
            raise CustomCapabilityRegistryError("Custom capability binding Room identity is invalid")
        capability_id = raw.get("id")
        if (
            not isinstance(capability_id, str)
            or not _CAPABILITY_ID.fullmatch(capability_id)
            or path.name != f"{capability_id}.json"
        ):
            raise CustomCapabilityRegistryError("Custom capability binding id is invalid")
        if capability_id in reserved_capability_ids:
            raise CustomCapabilityRegistryError(
                f"Custom capability id collides with reserved CORE capability: {capability_id}"
            )
        registration_sha256 = raw.get("registration_sha256")
        _validate_sha(registration_sha256, "binding registration SHA-256")
        payload = {
            "schema_version": 1,
            "room_id": room_id,
            "id": capability_id,
            "registration_sha256": registration_sha256,
        }
        expected_binding_sha = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
        if raw.get("binding_sha256") != expected_binding_sha:
            raise CustomCapabilityRegistryError(
                "Custom capability binding hash does not match exact binding payload"
            )
        item = _resolve_registration(
            data_root,
            registration_sha256,
            expected_room_id=room_id,
            expected_capability_id=capability_id,
        )
        resolved[capability_id] = BoundCustomCapability(
            room_id=room_id,
            binding_sha256=expected_binding_sha,
            registration=item.registration,
            receipt=item.receipt,
            package=item.package,
            package_root=item.package_root,
        )
    return resolved


def invoke_bound_custom_capability(
    context: RoomCapabilityContext,
    binding: BoundCustomCapability,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    if binding.room_id != context.room_id:
        raise CustomCapabilityRegistryError("Custom capability binding belongs to another Room")
    if not isinstance(inputs, dict):
        raise CustomCapabilityRegistryError("Custom capability input must be a JSON object")
    if len(_canonical_json_bytes(inputs)) > MAX_CASE_JSON_BYTES:
        raise CustomCapabilityRegistryError("Custom capability input exceeds the size limit")
    _validate_contract_value(inputs, binding.package.input_schema, "input")

    executable = binding.package_root / ENTRYPOINT_NAME
    observed = _execute(executable, context.workspace, inputs, binding.package.capability_id)
    _validate_custom_result(binding.package, observed)

    current = load_room_custom_capabilities(
        context.data_root,
        context.room_id,
    ).get(binding.package.capability_id)
    if (
        current is None
        or current.registration.registration_sha256
        != binding.registration.registration_sha256
        or current.package.package_sha256 != binding.package.package_sha256
    ):
        raise CustomCapabilityRegistryError(
            "Custom capability binding or exact package changed during invocation"
        )

    result = {
        "codex_room_capability": 1,
        "capability": binding.package.capability_id,
        "capability_version": binding.package.version,
        "implementation_sha256": binding.package.implementation_sha256,
        "package_sha256": binding.package.package_sha256,
        "registration_sha256": binding.registration.registration_sha256,
        "verification_sha256": binding.receipt.verification_sha256,
        "durable_result_fields": list(binding.package.durable_result_fields),
        **observed,
    }
    return result


@dataclass(frozen=True, slots=True)
class _ResolvedRegistration:
    registration: CustomCapabilityRegistration
    receipt: VerificationReceipt
    package: CustomCapabilityPackage
    package_root: Path


def _resolve_registration(
    data_root: Path,
    registration_sha256: str,
    *,
    expected_room_id: str | None = None,
    expected_capability_id: str | None = None,
) -> _ResolvedRegistration:
    registration_path = data_root.joinpath(
        *REGISTRATIONS_PATH.parts,
        f"{registration_sha256}.json",
    )
    raw = _read_json_record(registration_path, "custom capability registration")
    required = {
        "schema_version",
        "room_id",
        "id",
        "origin",
        "scope",
        "version",
        "package_sha256",
        "manifest_sha256",
        "implementation_sha256",
        "verification_sha256",
        "registration_sha256",
    }
    if set(raw) != required:
        raise CustomCapabilityRegistryError("Custom capability registration schema is invalid")
    if (
        raw.get("schema_version") != 1
        or raw.get("origin") != "custom"
        or raw.get("scope") != "lineage"
    ):
        raise CustomCapabilityRegistryError("Custom capability registration identity is invalid")
    room_id = raw.get("room_id")
    capability_id = raw.get("id")
    if not isinstance(room_id, str) or not _ROOM_ID.fullmatch(room_id):
        raise CustomCapabilityRegistryError("Custom capability registration Room id is invalid")
    if not isinstance(capability_id, str) or not _CAPABILITY_ID.fullmatch(capability_id):
        raise CustomCapabilityRegistryError("Custom capability registration id is invalid")
    if expected_room_id is not None and room_id != expected_room_id:
        raise CustomCapabilityRegistryError("Custom capability registration belongs to another Room")
    if expected_capability_id is not None and capability_id != expected_capability_id:
        raise CustomCapabilityRegistryError("Custom capability registration id does not match binding")

    for field in (
        "package_sha256",
        "manifest_sha256",
        "implementation_sha256",
        "verification_sha256",
        "registration_sha256",
    ):
        _validate_sha(raw.get(field), f"registration {field}")
    if raw["registration_sha256"] != registration_sha256:
        raise CustomCapabilityRegistryError(
            "Custom capability registration filename does not match record identity"
        )

    provisional = CustomCapabilityRegistration(
        registration_sha256="",
        room_id=room_id,
        capability_id=capability_id,
        version=raw["version"],
        package_sha256=raw["package_sha256"],
        manifest_sha256=raw["manifest_sha256"],
        implementation_sha256=raw["implementation_sha256"],
        verification_sha256=raw["verification_sha256"],
    )
    expected_registration_sha = hashlib.sha256(
        _canonical_json_bytes(provisional.payload())
    ).hexdigest()
    if expected_registration_sha != registration_sha256:
        raise CustomCapabilityRegistryError(
            "Custom capability registration hash does not match exact payload"
        )
    registration = CustomCapabilityRegistration(
        registration_sha256=registration_sha256,
        room_id=room_id,
        capability_id=capability_id,
        version=raw["version"],
        package_sha256=raw["package_sha256"],
        manifest_sha256=raw["manifest_sha256"],
        implementation_sha256=raw["implementation_sha256"],
        verification_sha256=raw["verification_sha256"],
    )

    verification_path = data_root.joinpath(
        *VERIFICATIONS_PATH.parts,
        f"{registration.verification_sha256}.json",
    )
    verification_raw = _read_json_record(
        verification_path, "custom capability verification receipt"
    )
    try:
        receipt = VerificationReceipt.from_dict(verification_raw)
    except CustomCapabilityVerificationError as exc:
        raise CustomCapabilityRegistryError(str(exc)) from exc
    if receipt.verification_sha256 != registration.verification_sha256:
        raise CustomCapabilityRegistryError(
            "Custom capability verification filename does not match receipt identity"
        )

    package_root = data_root.joinpath(
        *PACKAGES_PATH.parts,
        registration.package_sha256,
    )
    try:
        package = load_custom_capability_package(
            package_root,
            expected_id=capability_id,
        )
    except CustomCapabilityPackageError as exc:
        raise CustomCapabilityRegistryError(str(exc)) from exc
    if (
        package.package_sha256 != registration.package_sha256
        or package.manifest_sha256 != registration.manifest_sha256
        or package.implementation_sha256 != registration.implementation_sha256
        or package.version != registration.version
    ):
        raise CustomCapabilityRegistryError(
            "Custom capability registration does not match exact published package"
        )
    if (
        receipt.package_sha256 != package.package_sha256
        or receipt.manifest_sha256 != package.manifest_sha256
        or receipt.implementation_sha256 != package.implementation_sha256
    ):
        raise CustomCapabilityRegistryError(
            "Custom capability verification does not match exact published package"
        )
    return _ResolvedRegistration(
        registration=registration,
        receipt=receipt,
        package=package,
        package_root=package_root,
    )


def _execute(
    executable: Path,
    workspace: Path,
    inputs: dict[str, Any],
    capability_id: str,
) -> dict[str, Any]:
    input_bytes = _canonical_json_bytes(inputs)
    with (
        tempfile.TemporaryFile() as stdin_file,
        tempfile.TemporaryFile() as stdout_file,
        tempfile.TemporaryFile() as stderr_file,
    ):
        stdin_file.write(input_bytes)
        stdin_file.seek(0)
        process = subprocess.Popen(
            [sys.executable, "-I", str(executable)],
            stdin=stdin_file,
            stdout=stdout_file,
            stderr=stderr_file,
            cwd=workspace,
        )
        started = time.monotonic()
        failure: str | None = None
        while process.poll() is None:
            if time.monotonic() - started > CASE_TIMEOUT_SECONDS:
                failure = "time"
                process.kill()
                break
            if (
                os.fstat(stdout_file.fileno()).st_size > MAX_PROCESS_OUTPUT_BYTES
                or os.fstat(stderr_file.fileno()).st_size > MAX_PROCESS_OUTPUT_BYTES
            ):
                failure = "output"
                process.kill()
                break
            time.sleep(0.01)
        process.wait()

        stdout_size = os.fstat(stdout_file.fileno()).st_size
        stderr_size = os.fstat(stderr_file.fileno()).st_size
        if failure == "time":
            raise CustomCapabilityRegistryError(
                f"Custom capability '{capability_id}' exceeded the time limit"
            )
        if (
            failure == "output"
            or stdout_size > MAX_PROCESS_OUTPUT_BYTES
            or stderr_size > MAX_PROCESS_OUTPUT_BYTES
        ):
            raise CustomCapabilityRegistryError(
                f"Custom capability '{capability_id}' exceeded the output size limit"
            )
        if process.returncode != 0:
            raise CustomCapabilityRegistryError(
                f"Custom capability '{capability_id}' exited with code {process.returncode}"
            )
        if stderr_size:
            raise CustomCapabilityRegistryError(
                f"Custom capability '{capability_id}' wrote to stderr"
            )
        stdout_file.seek(0)
        stdout = stdout_file.read(MAX_PROCESS_OUTPUT_BYTES + 1)

    try:
        observed = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CustomCapabilityRegistryError(
            f"Custom capability '{capability_id}' did not emit one UTF-8 JSON result"
        ) from exc
    if not isinstance(observed, dict):
        raise CustomCapabilityRegistryError(
            f"Custom capability '{capability_id}' result must be a JSON object"
        )
    return observed


def _validate_custom_result(
    package: CustomCapabilityPackage,
    observed: dict[str, Any],
) -> None:
    reserved = sorted((_RESERVED_RESULT_FIELDS - {"ok"}).intersection(observed))
    if reserved:
        raise CustomCapabilityRegistryError(
            f"Custom capability result attempted reserved envelope fields: {reserved}"
        )
    if type(observed.get("ok")) is not bool:
        raise CustomCapabilityRegistryError(
            "Custom capability result must include boolean ok"
        )
    missing_durable = sorted(set(package.durable_result_fields) - set(observed))
    if missing_durable:
        raise CustomCapabilityRegistryError(
            f"Custom capability result omitted durable fields: {missing_durable}"
        )
    _validate_contract_value(observed, package.output_schema, "result")


def _validate_contract_value(value: Any, schema: dict[str, Any], label: str) -> None:
    if schema.get("type") == "object":
        if not isinstance(value, dict):
            raise CustomCapabilityRegistryError(f"Custom capability {label} must be an object")
        missing = sorted(set(schema.get("required", [])) - set(value))
        if missing:
            raise CustomCapabilityRegistryError(
                f"Custom capability {label} omitted required fields: {missing}"
            )
        properties = schema.get("properties", {})
        for key, item in value.items():
            subschema = properties.get(key)
            if isinstance(subschema, dict):
                _validate_contract_value(item, subschema, f"{label}.{key}")
        return

    kind = schema.get("type")
    if kind is None:
        return
    valid = {
        "string": lambda item: isinstance(item, str),
        "boolean": lambda item: type(item) is bool,
        "integer": lambda item: type(item) is int,
        "number": lambda item: type(item) in {int, float},
        "array": lambda item: isinstance(item, list),
        "null": lambda item: item is None,
    }.get(kind)
    if valid is not None and not valid(value):
        raise CustomCapabilityRegistryError(
            f"Custom capability {label} does not match declared type {kind}"
        )
    if "const" in schema and value != schema["const"]:
        raise CustomCapabilityRegistryError(
            f"Custom capability {label} does not match declared const"
        )
    if "enum" in schema and isinstance(schema["enum"], list) and value not in schema["enum"]:
        raise CustomCapabilityRegistryError(
            f"Custom capability {label} does not match declared enum"
        )


def _read_json_record(path: Path, label: str) -> dict[str, Any]:
    if not os.path.lexists(path):
        raise CustomCapabilityRegistryError(f"{label} is missing")
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CustomCapabilityRegistryError(f"{label} could not be inspected: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CustomCapabilityRegistryError(f"{label} must be a regular file")
    if metadata.st_size > MAX_REGISTRY_RECORD_BYTES:
        raise CustomCapabilityRegistryError(f"{label} exceeds the size limit")
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise CustomCapabilityRegistryError(f"{label} could not be read: {exc}") from exc
    if len(raw_bytes) > MAX_REGISTRY_RECORD_BYTES:
        raise CustomCapabilityRegistryError(f"{label} exceeds the size limit")
    try:
        raw = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CustomCapabilityRegistryError(f"{label} must be valid UTF-8 JSON") from exc
    if not isinstance(raw, dict):
        raise CustomCapabilityRegistryError(f"{label} must be a JSON object")
    return raw


def _write_exclusive(path: Path, exact_bytes: bytes, label: str) -> None:
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        current = _read_json_record(path, label)
        if _canonical_json_bytes(current) != exact_bytes:
            raise CustomCapabilityRegistryError(f"{label} already exists with other bytes")
        return
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(exact_bytes)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _ensure_real_registry_directory(data_root: Path, path: Path) -> None:
    try:
        relative = path.relative_to(data_root)
    except ValueError as exc:
        raise CustomCapabilityRegistryError("Registry path escaped data root") from exc
    current = data_root
    if os.path.lexists(current):
        _assert_real_directory(current, "Codex Room data root")
    for part in relative.parts:
        current = current / part
        if not os.path.lexists(current):
            current.mkdir()
        _assert_real_directory(current, "Custom capability registry directory")


def _assert_real_directory(path: Path, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CustomCapabilityRegistryError(f"{label} could not be inspected: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CustomCapabilityRegistryError(f"{label} must be a real directory")


def _validate_room_id(room_id: Any) -> None:
    if not isinstance(room_id, str) or not _ROOM_ID.fullmatch(room_id):
        raise CustomCapabilityRegistryError("Room id is invalid")


def _validate_sha(value: Any, label: str) -> None:
    if not isinstance(value, str) or not _HEX_SHA256.fullmatch(value):
        raise CustomCapabilityRegistryError(f"{label} is invalid")


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CustomCapabilityRegistryError(
            "Custom capability registry data must be JSON-serializable"
        ) from exc
