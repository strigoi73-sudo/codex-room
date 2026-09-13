from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .custom_capabilities import (
    ENTRYPOINT_NAME,
    MANIFEST_NAME,
    CustomCapabilityPackage,
    CustomCapabilityPackageError,
    load_custom_capability_draft,
)


REGISTRY_ROOT = PurePosixPath("custom-capabilities")
PACKAGES_PATH = REGISTRY_ROOT / "packages"
VERIFICATIONS_PATH = REGISTRY_ROOT / "verifications"
REGISTRATIONS_PATH = REGISTRY_ROOT / "registrations"
VERIFIER_VERSION = "stdio-json-v1"
MAX_VERIFICATION_CASES = 16
MAX_CASE_NAME_CHARS = 120
MAX_CASE_JSON_BYTES = 64 * 1024
MAX_FIXTURE_FILES = 32
MAX_FIXTURE_FILE_BYTES = 64 * 1024
MAX_FIXTURE_TOTAL_BYTES = 256 * 1024
MAX_PROCESS_OUTPUT_BYTES = 64 * 1024
CASE_TIMEOUT_SECONDS = 5.0
_HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
_ROOM_ID = re.compile(r"room_[A-Za-z0-9_-]{1,128}")
_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}


class CustomCapabilityVerificationError(ValueError):
    """A custom capability draft failed deterministic registration verification."""


class CustomCapabilityPublicationError(ValueError):
    """A verified custom capability could not be published immutably."""


@dataclass(frozen=True, slots=True)
class VerificationReceipt:
    package_sha256: str
    manifest_sha256: str
    implementation_sha256: str
    case_plan_sha256: str
    cases: tuple[dict[str, Any], ...]
    verification_sha256: str

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "verifier": VERIFIER_VERSION,
            "execution_boundary": "ambient_room_sandbox_required",
            "package_sha256": self.package_sha256,
            "manifest_sha256": self.manifest_sha256,
            "implementation_sha256": self.implementation_sha256,
            "case_plan_sha256": self.case_plan_sha256,
            "case_count": len(self.cases),
            "cases": [dict(item) for item in self.cases],
            "passed": True,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "verification_sha256": self.verification_sha256,
        }

    def as_bytes(self) -> bytes:
        return _canonical_json_bytes(self.as_dict())

    @classmethod
    def create(
        cls,
        package: CustomCapabilityPackage,
        *,
        case_plan_sha256: str,
        cases: list[dict[str, Any]],
    ) -> "VerificationReceipt":
        provisional = cls(
            package_sha256=package.package_sha256,
            manifest_sha256=package.manifest_sha256,
            implementation_sha256=package.implementation_sha256,
            case_plan_sha256=case_plan_sha256,
            cases=tuple(cases),
            verification_sha256="",
        )
        verification_sha256 = hashlib.sha256(
            _canonical_json_bytes(provisional.payload())
        ).hexdigest()
        return cls(
            package_sha256=package.package_sha256,
            manifest_sha256=package.manifest_sha256,
            implementation_sha256=package.implementation_sha256,
            case_plan_sha256=case_plan_sha256,
            cases=tuple(cases),
            verification_sha256=verification_sha256,
        )

    @classmethod
    def from_dict(cls, raw: Any) -> "VerificationReceipt":
        if not isinstance(raw, dict):
            raise CustomCapabilityVerificationError(
                "Verification receipt must be a JSON object"
            )
        required = {
            "schema_version",
            "verifier",
            "execution_boundary",
            "package_sha256",
            "manifest_sha256",
            "implementation_sha256",
            "case_plan_sha256",
            "case_count",
            "cases",
            "passed",
            "verification_sha256",
        }
        if set(raw) != required:
            raise CustomCapabilityVerificationError(
                "Verification receipt fields do not match schema v1"
            )
        if (
            raw["schema_version"] != 1
            or raw["verifier"] != VERIFIER_VERSION
            or raw["execution_boundary"] != "ambient_room_sandbox_required"
            or raw["passed"] is not True
        ):
            raise CustomCapabilityVerificationError(
                "Verification receipt identity is invalid"
            )
        for field in (
            "package_sha256",
            "manifest_sha256",
            "implementation_sha256",
            "case_plan_sha256",
            "verification_sha256",
        ):
            if not isinstance(raw[field], str) or not _HEX_SHA256.fullmatch(raw[field]):
                raise CustomCapabilityVerificationError(
                    f"Verification receipt {field} is invalid"
                )
        cases = raw["cases"]
        if (
            not isinstance(cases, list)
            or not 1 <= len(cases) <= MAX_VERIFICATION_CASES
            or raw["case_count"] != len(cases)
            or any(not isinstance(item, dict) for item in cases)
        ):
            raise CustomCapabilityVerificationError(
                "Verification receipt cases are invalid"
            )
        receipt = cls(
            package_sha256=raw["package_sha256"],
            manifest_sha256=raw["manifest_sha256"],
            implementation_sha256=raw["implementation_sha256"],
            case_plan_sha256=raw["case_plan_sha256"],
            cases=tuple(dict(item) for item in cases),
            verification_sha256=raw["verification_sha256"],
        )
        expected = hashlib.sha256(_canonical_json_bytes(receipt.payload())).hexdigest()
        if expected != receipt.verification_sha256:
            raise CustomCapabilityVerificationError(
                "Verification receipt hash does not match its exact payload"
            )
        return receipt


@dataclass(frozen=True, slots=True)
class CustomCapabilityRegistration:
    registration_sha256: str
    room_id: str
    capability_id: str
    version: str
    package_sha256: str
    manifest_sha256: str
    implementation_sha256: str
    verification_sha256: str

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "room_id": self.room_id,
            "id": self.capability_id,
            "origin": "custom",
            "scope": "lineage",
            "version": self.version,
            "package_sha256": self.package_sha256,
            "manifest_sha256": self.manifest_sha256,
            "implementation_sha256": self.implementation_sha256,
            "verification_sha256": self.verification_sha256,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "registration_sha256": self.registration_sha256,
        }


def verify_custom_capability_draft(
    workspace: Path,
    capability_id: str,
    raw_cases: Any,
) -> VerificationReceipt:
    """Execute exact draft bytes against bounded exact-output cases.

    This verifier intentionally creates no new sandbox. It is designed to run through
    the same ambient Room command sandbox as ordinary agent-authored code.
    """
    package = load_custom_capability_draft(workspace, capability_id)
    cases = _normalize_cases(package, raw_cases)
    case_plan_sha256 = hashlib.sha256(_canonical_json_bytes(cases)).hexdigest()
    evidence: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix=".codex-room-verify-", dir=workspace) as raw_root:
        verification_root = Path(raw_root)
        executable_root = verification_root / "executable"
        executable_root.mkdir()
        executable = executable_root / ENTRYPOINT_NAME
        executable.write_bytes(package.entrypoint_bytes)

        for index, case in enumerate(cases, start=1):
            case_workspace = verification_root / f"case-{index:02d}" / "workspace"
            case_workspace.mkdir(parents=True)
            _materialize_fixtures(case_workspace, case["files"])
            observed = _run_case(executable, case_workspace, case["input"], case["name"])
            if observed != case["expected_output"]:
                raise CustomCapabilityVerificationError(
                    f"Verification case '{case['name']}' output did not match expected output"
                )
            evidence.append(
                {
                    "name": case["name"],
                    "input_sha256": hashlib.sha256(
                        _canonical_json_bytes(case["input"])
                    ).hexdigest(),
                    "expected_output_sha256": hashlib.sha256(
                        _canonical_json_bytes(case["expected_output"])
                    ).hexdigest(),
                    "observed_output_sha256": hashlib.sha256(
                        _canonical_json_bytes(observed)
                    ).hexdigest(),
                    "fixtures_sha256": hashlib.sha256(
                        _canonical_json_bytes(case["files"])
                    ).hexdigest(),
                }
            )

    try:
        current = load_custom_capability_draft(workspace, capability_id)
    except CustomCapabilityPackageError as exc:
        raise CustomCapabilityVerificationError(
            "Custom capability draft changed or became invalid during verification"
        ) from exc
    if (
        current.package_sha256 != package.package_sha256
        or current.manifest_sha256 != package.manifest_sha256
        or current.implementation_sha256 != package.implementation_sha256
    ):
        raise CustomCapabilityVerificationError(
            "Custom capability draft changed during verification"
        )

    return VerificationReceipt.create(
        package,
        case_plan_sha256=case_plan_sha256,
        cases=evidence,
    )


def publish_verified_custom_capability(
    workspace: Path,
    data_root: Path,
    room_id: str,
    capability_id: str,
    receipt: VerificationReceipt,
) -> CustomCapabilityRegistration:
    """Publish verified exact bytes and an immutable registration record.

    This host-side publisher never executes candidate code.
    """
    if not isinstance(room_id, str) or not _ROOM_ID.fullmatch(room_id):
        raise CustomCapabilityPublicationError("Registration room_id is invalid")
    package = load_custom_capability_draft(workspace, capability_id)
    _assert_receipt_matches_package(receipt, package)

    packages_root = data_root.joinpath(*PACKAGES_PATH.parts)
    verifications_root = data_root.joinpath(*VERIFICATIONS_PATH.parts)
    registrations_root = data_root.joinpath(*REGISTRATIONS_PATH.parts)
    packages_root.mkdir(parents=True, exist_ok=True)
    verifications_root.mkdir(parents=True, exist_ok=True)
    registrations_root.mkdir(parents=True, exist_ok=True)

    _publish_package_directory(packages_root, package)
    _publish_immutable_file(
        verifications_root / f"{receipt.verification_sha256}.json",
        receipt.as_bytes(),
        "verification receipt",
    )

    provisional = CustomCapabilityRegistration(
        registration_sha256="",
        room_id=room_id,
        capability_id=package.capability_id,
        version=package.version,
        package_sha256=package.package_sha256,
        manifest_sha256=package.manifest_sha256,
        implementation_sha256=package.implementation_sha256,
        verification_sha256=receipt.verification_sha256,
    )
    registration_sha256 = hashlib.sha256(
        _canonical_json_bytes(provisional.payload())
    ).hexdigest()
    registration = CustomCapabilityRegistration(
        registration_sha256=registration_sha256,
        room_id=room_id,
        capability_id=package.capability_id,
        version=package.version,
        package_sha256=package.package_sha256,
        manifest_sha256=package.manifest_sha256,
        implementation_sha256=package.implementation_sha256,
        verification_sha256=receipt.verification_sha256,
    )
    _publish_immutable_file(
        registrations_root / f"{registration_sha256}.json",
        _canonical_json_bytes(registration.as_dict()),
        "registration record",
    )
    return registration


def _normalize_cases(
    package: CustomCapabilityPackage, raw_cases: Any
) -> list[dict[str, Any]]:
    if (
        not isinstance(raw_cases, list)
        or not 1 <= len(raw_cases) <= MAX_VERIFICATION_CASES
    ):
        raise CustomCapabilityVerificationError(
            f"Verification requires 1 to {MAX_VERIFICATION_CASES} cases"
        )
    normalized: list[dict[str, Any]] = []
    names: set[str] = set()
    for index, raw in enumerate(raw_cases):
        if not isinstance(raw, dict):
            raise CustomCapabilityVerificationError(
                f"Verification case {index + 1} must be an object"
            )
        required = {"name", "input", "expected_output"}
        allowed = required | {"files"}
        if not required.issubset(raw) or set(raw) - allowed:
            raise CustomCapabilityVerificationError(
                f"Verification case {index + 1} fields are invalid"
            )
        name = raw["name"]
        if (
            not isinstance(name, str)
            or not name.strip()
            or len(name) > MAX_CASE_NAME_CHARS
            or name in names
        ):
            raise CustomCapabilityVerificationError(
                "Verification case names must be unique bounded strings"
            )
        names.add(name)
        inputs = raw["input"]
        expected = raw["expected_output"]
        if not isinstance(inputs, dict):
            raise CustomCapabilityVerificationError(
                f"Verification case '{name}' input must be a JSON object"
            )
        if not isinstance(expected, dict) or type(expected.get("ok")) is not bool:
            raise CustomCapabilityVerificationError(
                f"Verification case '{name}' expected_output must be an object with boolean ok"
            )
        missing_durable = sorted(
            set(package.durable_result_fields) - set(expected)
        )
        if missing_durable:
            raise CustomCapabilityVerificationError(
                f"Verification case '{name}' omits durable result fields: {missing_durable}"
            )
        if len(_canonical_json_bytes(inputs)) > MAX_CASE_JSON_BYTES:
            raise CustomCapabilityVerificationError(
                f"Verification case '{name}' input exceeds the size limit"
            )
        if len(_canonical_json_bytes(expected)) > MAX_CASE_JSON_BYTES:
            raise CustomCapabilityVerificationError(
                f"Verification case '{name}' expected_output exceeds the size limit"
            )
        files = _normalize_fixtures(raw.get("files", {}), name)
        normalized.append(
            {
                "name": name,
                "input": inputs,
                "expected_output": expected,
                "files": files,
            }
        )
    return normalized


def _normalize_fixtures(raw: Any, case_name: str) -> dict[str, str]:
    if not isinstance(raw, dict) or len(raw) > MAX_FIXTURE_FILES:
        raise CustomCapabilityVerificationError(
            f"Verification case '{case_name}' files must be a bounded object"
        )
    normalized: dict[str, str] = {}
    keys: set[str] = set()
    total = 0
    for path, content in raw.items():
        if not isinstance(path, str):
            raise CustomCapabilityVerificationError(
                f"Verification case '{case_name}' fixture path is invalid"
            )
        safe_path = _safe_fixture_path(path)
        key = "/".join(part.casefold() for part in safe_path.parts)
        if key in keys:
            raise CustomCapabilityVerificationError(
                f"Verification case '{case_name}' fixture paths collide"
            )
        keys.add(key)
        if not isinstance(content, str):
            raise CustomCapabilityVerificationError(
                f"Verification case '{case_name}' fixture content must be UTF-8 text"
            )
        size = len(content.encode("utf-8"))
        if size > MAX_FIXTURE_FILE_BYTES:
            raise CustomCapabilityVerificationError(
                f"Verification case '{case_name}' fixture exceeds the per-file limit"
            )
        total += size
        if total > MAX_FIXTURE_TOTAL_BYTES:
            raise CustomCapabilityVerificationError(
                f"Verification case '{case_name}' fixtures exceed the total size limit"
            )
        normalized[safe_path.as_posix()] = content
    return dict(sorted(normalized.items()))


def _safe_fixture_path(raw_path: str) -> PurePosixPath:
    if (
        not raw_path
        or "\\" in raw_path
        or ":" in raw_path
        or raw_path.startswith("/")
    ):
        raise CustomCapabilityVerificationError("Verification fixture path is unsafe")
    path = PurePosixPath(raw_path)
    if not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise CustomCapabilityVerificationError("Verification fixture path is unsafe")
    for part in path.parts:
        if (
            part.casefold() in _WINDOWS_RESERVED
            or part.endswith(" ")
            or part.endswith(".")
        ):
            raise CustomCapabilityVerificationError("Verification fixture path is unsafe")
    return path


def _materialize_fixtures(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        target = root.joinpath(*PurePosixPath(relative).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="")


def _run_case(
    executable: Path,
    workspace: Path,
    inputs: dict[str, Any],
    case_name: str,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [sys.executable, "-I", str(executable)],
            input=_canonical_json_bytes(inputs),
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CASE_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CustomCapabilityVerificationError(
            f"Verification case '{case_name}' exceeded the time limit"
        ) from exc
    if (
        len(completed.stdout) > MAX_PROCESS_OUTPUT_BYTES
        or len(completed.stderr) > MAX_PROCESS_OUTPUT_BYTES
    ):
        raise CustomCapabilityVerificationError(
            f"Verification case '{case_name}' exceeded the output size limit"
        )
    if completed.returncode != 0:
        raise CustomCapabilityVerificationError(
            f"Verification case '{case_name}' exited with code {completed.returncode}"
        )
    if completed.stderr:
        raise CustomCapabilityVerificationError(
            f"Verification case '{case_name}' wrote to stderr"
        )
    try:
        observed = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CustomCapabilityVerificationError(
            f"Verification case '{case_name}' did not emit one UTF-8 JSON result"
        ) from exc
    if not isinstance(observed, dict) or type(observed.get("ok")) is not bool:
        raise CustomCapabilityVerificationError(
            f"Verification case '{case_name}' result must be an object with boolean ok"
        )
    return observed


def _assert_receipt_matches_package(
    receipt: VerificationReceipt, package: CustomCapabilityPackage
) -> None:
    if (
        receipt.package_sha256 != package.package_sha256
        or receipt.manifest_sha256 != package.manifest_sha256
        or receipt.implementation_sha256 != package.implementation_sha256
    ):
        raise CustomCapabilityPublicationError(
            "Verification receipt does not match the current exact draft package"
        )
    VerificationReceipt.from_dict(receipt.as_dict())


def _publish_package_directory(
    packages_root: Path, package: CustomCapabilityPackage
) -> None:
    destination = packages_root / package.package_sha256
    if os.path.lexists(destination):
        _verify_package_directory(destination, package)
        return

    staging_root = packages_root / ".publishing"
    staging_root.mkdir(exist_ok=True)
    stage = staging_root / f"publish_{uuid.uuid4().hex}"
    try:
        stage.mkdir()
        (stage / MANIFEST_NAME).write_bytes(package.manifest_bytes)
        (stage / ENTRYPOINT_NAME).write_bytes(package.entrypoint_bytes)
        _verify_package_directory(stage, package)
        try:
            os.rename(stage, destination)
        except FileExistsError:
            _verify_package_directory(destination, package)
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def _verify_package_directory(
    directory: Path, package: CustomCapabilityPackage
) -> None:
    try:
        metadata = directory.lstat()
    except OSError as exc:
        raise CustomCapabilityPublicationError(
            f"Published package could not be inspected: {exc}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CustomCapabilityPublicationError(
            "Published package path must be a real directory"
        )
    try:
        entries = sorted(item.name for item in directory.iterdir())
    except OSError as exc:
        raise CustomCapabilityPublicationError(
            f"Published package inventory could not be read: {exc}"
        ) from exc
    if entries != [ENTRYPOINT_NAME, MANIFEST_NAME]:
        raise CustomCapabilityPublicationError(
            "Published package inventory does not match the verified package"
        )
    expected = {
        MANIFEST_NAME: package.manifest_bytes,
        ENTRYPOINT_NAME: package.entrypoint_bytes,
    }
    for name, exact_bytes in expected.items():
        path = directory / name
        meta = path.lstat()
        if stat.S_ISLNK(meta.st_mode) or not stat.S_ISREG(meta.st_mode):
            raise CustomCapabilityPublicationError(
                "Published package contains a non-regular artifact"
            )
        if path.read_bytes() != exact_bytes:
            raise CustomCapabilityPublicationError(
                "Published package bytes do not match the verified package"
            )


def _publish_immutable_file(path: Path, exact_bytes: bytes, label: str) -> None:
    if os.path.lexists(path):
        _verify_immutable_file(path, exact_bytes, label)
        return
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        _verify_immutable_file(path, exact_bytes, label)
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
    _verify_immutable_file(path, exact_bytes, label)


def _verify_immutable_file(path: Path, exact_bytes: bytes, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CustomCapabilityPublicationError(
            f"Published {label} could not be inspected: {exc}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CustomCapabilityPublicationError(
            f"Published {label} must be a regular file"
        )
    try:
        actual = path.read_bytes()
    except OSError as exc:
        raise CustomCapabilityPublicationError(
            f"Published {label} could not be read: {exc}"
        ) from exc
    if actual != exact_bytes:
        raise CustomCapabilityPublicationError(
            f"Published {label} does not match its content-addressed identity"
        )


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CustomCapabilityVerificationError(
            "Verification data must be JSON-serializable"
        ) from exc
