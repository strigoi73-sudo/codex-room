from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import stat
import sys
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


DATABASE_NAME = "codex-room.db"
BACKUPS_NAME = "backups"
MANIFEST_NAME = "manifest.json"
MANIFEST_SCHEMA_VERSION = 1
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data"


class MaintenanceError(RuntimeError):
    """A maintenance operation could not be completed safely."""


def check_data_root(data_root: Path) -> dict[str, Any]:
    root = _absolute(data_root)
    _assert_real_directory(root, "data root")
    database = root / DATABASE_NAME
    _assert_regular_file(database, "Codex Room database")

    payload_files = list(_iter_data_payload_files(root))
    sqlite_health = _sqlite_health(database)
    total_bytes = database.stat().st_size + sum(path.stat().st_size for path in payload_files)

    return {
        "ok": True,
        "operation": "check",
        "data_root": str(root),
        "database": DATABASE_NAME,
        "sqlite": sqlite_health,
        "payload_file_count": len(payload_files) + 1,
        "payload_bytes": total_bytes,
        "wal_present": (root / f"{DATABASE_NAME}-wal").exists(),
        "shm_present": (root / f"{DATABASE_NAME}-shm").exists(),
    }


def create_backup(
    data_root: Path,
    *,
    backup_root: Path | None = None,
    offline_confirmed: bool = False,
) -> dict[str, Any]:
    if not offline_confirmed:
        raise MaintenanceError(
            "backup requires --offline-confirmed after the Codex Room service has been stopped"
        )

    root = _absolute(data_root)
    _assert_real_directory(root, "data root")
    database = root / DATABASE_NAME
    _assert_regular_file(database, "Codex Room database")
    # Fail before creating a backup if the source database itself is not healthy.
    source_health = _sqlite_health(database)

    destination_root = _absolute(backup_root or (root / BACKUPS_NAME))
    _validate_backup_root(root, destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)
    _assert_real_directory(destination_root, "backup root")

    backup_id = _new_backup_id()
    staging = destination_root / f".building-{backup_id}"
    final = destination_root / backup_id
    staging.mkdir(parents=False, exist_ok=False)

    try:
        _sqlite_backup(database, staging / DATABASE_NAME)
        for source in _iter_data_payload_files(root):
            relative = source.relative_to(root)
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        files = [_file_record(path, staging) for path in _iter_regular_tree_files(staging)]
        files.sort(key=lambda item: item["path"])
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "source": {
                "database": DATABASE_NAME,
                "scope": "data-root-excluding-backups-and-sqlite-sidecars",
            },
            "files": files,
        }
        (staging / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        verified = verify_backup(staging)
        os.replace(staging, final)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise

    return {
        "ok": True,
        "operation": "backup",
        "backup": str(final),
        "source_sqlite": source_health,
        "verification": {
            "file_count": verified["file_count"],
            "payload_bytes": verified["payload_bytes"],
            "sqlite": verified["sqlite"],
        },
    }


def verify_backup(backup_dir: Path) -> dict[str, Any]:
    root = _absolute(backup_dir)
    _assert_real_directory(root, "backup directory")
    manifest_path = root / MANIFEST_NAME
    _assert_regular_file(manifest_path, "backup manifest")
    if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise MaintenanceError("backup manifest exceeds the size limit")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MaintenanceError("backup manifest must be valid UTF-8 JSON") from exc

    expected_top = {"schema_version", "created_at", "source", "files"}
    if not isinstance(manifest, dict) or set(manifest) != expected_top:
        raise MaintenanceError("backup manifest has an unsupported structure")
    if manifest["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise MaintenanceError(
            f"unsupported backup manifest schema: {manifest['schema_version']!r}"
        )
    if not isinstance(manifest["created_at"], str) or not manifest["created_at"].strip():
        raise MaintenanceError("backup manifest created_at is invalid")
    if manifest["source"] != {
        "database": DATABASE_NAME,
        "scope": "data-root-excluding-backups-and-sqlite-sidecars",
    }:
        raise MaintenanceError("backup manifest source metadata is invalid")

    records = manifest["files"]
    if not isinstance(records, list) or not records:
        raise MaintenanceError("backup manifest files must be a non-empty array")

    expected: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "size"}:
            raise MaintenanceError(f"backup manifest files[{index}] is invalid")
        relative = _validated_manifest_path(record["path"], index)
        size = record["size"]
        digest = record["sha256"]
        if type(size) is not int or size < 0:
            raise MaintenanceError(f"backup manifest files[{index}].size is invalid")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)
        ):
            raise MaintenanceError(f"backup manifest files[{index}].sha256 is invalid")
        key = relative.as_posix()
        if key in expected:
            raise MaintenanceError(f"backup manifest contains duplicate path: {key}")
        expected[key] = record

    if DATABASE_NAME not in expected:
        raise MaintenanceError("backup manifest does not contain codex-room.db")

    actual_paths: dict[str, Path] = {}
    for path in _iter_regular_tree_files(root, exclude_names={MANIFEST_NAME}):
        key = path.relative_to(root).as_posix()
        actual_paths[key] = path

    if set(actual_paths) != set(expected):
        missing = sorted(set(expected) - set(actual_paths))
        extra = sorted(set(actual_paths) - set(expected))
        raise MaintenanceError(
            f"backup payload does not match manifest (missing={missing}, extra={extra})"
        )

    payload_bytes = 0
    for key, record in expected.items():
        path = actual_paths[key]
        size = path.stat().st_size
        payload_bytes += size
        if size != record["size"]:
            raise MaintenanceError(f"backup file size mismatch: {key}")
        if _sha256(path) != record["sha256"]:
            raise MaintenanceError(f"backup file hash mismatch: {key}")

    sqlite_health = _sqlite_health(root / DATABASE_NAME)
    return {
        "ok": True,
        "operation": "verify",
        "backup": str(root),
        "file_count": len(expected),
        "payload_bytes": payload_bytes,
        "sqlite": sqlite_health,
        "created_at": manifest["created_at"],
    }


def restore_backup(
    backup_dir: Path,
    data_root: Path,
    *,
    offline_confirmed: bool = False,
    confirm_replace_data: bool = False,
) -> dict[str, Any]:
    if not offline_confirmed:
        raise MaintenanceError(
            "restore requires --offline-confirmed after the Codex Room service has been stopped"
        )
    if not confirm_replace_data:
        raise MaintenanceError(
            "restore is destructive and requires --confirm-replace-data"
        )

    source = _absolute(backup_dir)
    verified = verify_backup(source)
    target = _absolute(data_root)
    target.parent.mkdir(parents=True, exist_ok=True)

    token = secrets.token_hex(5)
    candidate = target.parent / f".{target.name}.restore-{token}"
    rollback = target.parent / f".{target.name}.rollback-{token}"
    if candidate.exists() or rollback.exists():
        raise MaintenanceError("restore staging path already exists")

    manifest = _load_manifest(source)
    warnings: list[str] = []
    moved_old = False

    try:
        candidate.mkdir()
        for record in manifest["files"]:
            relative = PurePosixPath(record["path"])
            src = source.joinpath(*relative.parts)
            dst = candidate.joinpath(*relative.parts)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        # Preserve the operator's existing backup collection. Backups are deliberately
        # not part of backup payloads, so restoring data never destroys the recovery
        # material needed to perform or undo the operation.
        current_backups = target / BACKUPS_NAME
        if current_backups.exists():
            _copy_tree_strict(current_backups, candidate / BACKUPS_NAME)

        candidate_health = check_data_root(candidate)

        if target.exists():
            _assert_real_directory(target, "data root")
            os.replace(target, rollback)
            moved_old = True
        try:
            os.replace(candidate, target)
        except BaseException:
            if moved_old and rollback.exists() and not target.exists():
                os.replace(rollback, target)
            raise

        if rollback.exists():
            try:
                shutil.rmtree(rollback)
            except OSError as exc:
                warnings.append(f"restored successfully but rollback cleanup failed: {exc}")
    except BaseException:
        if candidate.exists():
            shutil.rmtree(candidate, ignore_errors=True)
        raise

    return {
        "ok": True,
        "operation": "restore",
        "backup": str(source),
        "data_root": str(target),
        "verification": verified,
        "restored_sqlite": candidate_health["sqlite"],
        "warnings": warnings,
    }


def _sqlite_health(database: Path) -> dict[str, Any]:
    _assert_regular_file(database, "SQLite database")
    try:
        connection = sqlite3.connect(str(database), timeout=30)
    except sqlite3.Error as exc:
        raise MaintenanceError(f"could not open SQLite database: {exc}") from exc
    try:
        quick_rows = [row[0] for row in connection.execute("PRAGMA quick_check")]
        if quick_rows != ["ok"]:
            raise MaintenanceError(f"SQLite quick_check failed: {quick_rows}")
        foreign_key_rows = list(connection.execute("PRAGMA foreign_key_check"))
        if foreign_key_rows:
            raise MaintenanceError(
                f"SQLite foreign_key_check found {len(foreign_key_rows)} violation(s)"
            )
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0])
    except sqlite3.DatabaseError as exc:
        raise MaintenanceError(f"SQLite integrity check failed: {exc}") from exc
    finally:
        connection.close()
    return {
        "quick_check": "ok",
        "foreign_key_violations": 0,
        "page_count": page_count,
        "journal_mode": journal_mode,
    }


def _sqlite_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        src = sqlite3.connect(str(source), timeout=30)
        dst = sqlite3.connect(str(destination), timeout=30)
    except sqlite3.Error as exc:
        raise MaintenanceError(f"could not open SQLite database for backup: {exc}") from exc
    try:
        src.backup(dst)
        dst.commit()
    except sqlite3.Error as exc:
        raise MaintenanceError(f"SQLite backup failed: {exc}") from exc
    finally:
        dst.close()
        src.close()
    _sqlite_health(destination)


def _iter_data_payload_files(root: Path) -> Iterable[Path]:
    excluded_files = {
        DATABASE_NAME,
        f"{DATABASE_NAME}-wal",
        f"{DATABASE_NAME}-shm",
    }
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        filtered_dirs: list[str] = []
        for name in dirs:
            path = current_path / name
            _reject_link_or_reparse(path, "data directory")
            if current_path == root and name == BACKUPS_NAME:
                continue
            _assert_directory(path, "data directory")
            filtered_dirs.append(name)
        dirs[:] = filtered_dirs
        for name in files:
            path = current_path / name
            if current_path == root and name in excluded_files:
                continue
            _assert_regular_file(path, "data payload file")
            yield path


def _iter_regular_tree_files(
    root: Path, *, exclude_names: set[str] | None = None
) -> Iterable[Path]:
    excluded = exclude_names or set()
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in dirs:
            path = current_path / name
            _reject_link_or_reparse(path, "backup directory")
            _assert_directory(path, "backup directory")
        for name in files:
            if current_path == root and name in excluded:
                continue
            path = current_path / name
            _assert_regular_file(path, "backup payload file")
            yield path


def _copy_tree_strict(source: Path, destination: Path) -> None:
    _assert_real_directory(source, "backup collection")
    destination.mkdir(parents=True, exist_ok=True)
    for path in _iter_regular_tree_files(source):
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def _load_manifest(backup_dir: Path) -> dict[str, Any]:
    # Callers use this only after verify_backup() has accepted the same path.
    return json.loads((backup_dir / MANIFEST_NAME).read_text(encoding="utf-8"))


def _file_record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha256(path),
        "size": path.stat().st_size,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_manifest_path(value: Any, index: int) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise MaintenanceError(f"backup manifest files[{index}].path is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise MaintenanceError(f"backup manifest files[{index}].path is unsafe")
    if path.parts[0] == BACKUPS_NAME or path.parts == (MANIFEST_NAME,):
        raise MaintenanceError(f"backup manifest files[{index}].path is reserved")
    return path


def _validate_backup_root(data_root: Path, backup_root: Path) -> None:
    try:
        relative = backup_root.relative_to(data_root)
    except ValueError:
        return
    if relative.parts != (BACKUPS_NAME,):
        raise MaintenanceError(
            "a backup root inside the data root must be exactly data/backups"
        )


def _new_backup_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"backup-{timestamp}-{secrets.token_hex(4)}"


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _reject_link_or_reparse(path: Path, label: str) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise MaintenanceError(f"{label} could not be inspected: {path}: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise MaintenanceError(f"{label} must not be a symlink: {path}")
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if reparse_flag and attributes & reparse_flag:
        raise MaintenanceError(f"{label} must not be a reparse point: {path}")
    return metadata


def _assert_regular_file(path: Path, label: str) -> None:
    metadata = _reject_link_or_reparse(path, label)
    if not stat.S_ISREG(metadata.st_mode):
        raise MaintenanceError(f"{label} must be a regular file: {path}")


def _assert_directory(path: Path, label: str) -> None:
    metadata = _reject_link_or_reparse(path, label)
    if not stat.S_ISDIR(metadata.st_mode):
        raise MaintenanceError(f"{label} must be a directory: {path}")


def _assert_real_directory(path: Path, label: str) -> None:
    if not os.path.lexists(path):
        raise MaintenanceError(f"{label} does not exist: {path}")
    _assert_directory(path, label)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline operational maintenance for Codex Room persistent data"
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help=f"Codex Room data root (default: {DEFAULT_DATA_ROOT})",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser("check", help="check current persistent-data integrity")
    check.add_argument(
        "--offline-confirmed",
        action="store_true",
        help="assert that the Codex Room service is stopped",
    )

    backup = subcommands.add_parser("backup", help="create and verify a coherent backup")
    backup.add_argument("--backup-root", type=Path)
    backup.add_argument(
        "--offline-confirmed",
        action="store_true",
        help="assert that the Codex Room service is stopped",
    )

    verify = subcommands.add_parser("verify", help="verify a backup manifest, files, and SQLite")
    verify.add_argument("backup", type=Path)

    restore = subcommands.add_parser(
        "restore", help="verify and replace current persistent data from a backup"
    )
    restore.add_argument("backup", type=Path)
    restore.add_argument(
        "--offline-confirmed",
        action="store_true",
        help="assert that the Codex Room service is stopped",
    )
    restore.add_argument(
        "--confirm-replace-data",
        action="store_true",
        help="confirm destructive replacement of the current data root",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            if not args.offline_confirmed:
                raise MaintenanceError(
                    "check requires --offline-confirmed after the Codex Room service has been stopped"
                )
            result = check_data_root(args.data_root)
        elif args.command == "backup":
            result = create_backup(
                args.data_root,
                backup_root=args.backup_root,
                offline_confirmed=args.offline_confirmed,
            )
        elif args.command == "verify":
            result = verify_backup(args.backup)
        elif args.command == "restore":
            result = restore_backup(
                args.backup,
                args.data_root,
                offline_confirmed=args.offline_confirmed,
                confirm_replace_data=args.confirm_replace_data,
            )
        else:  # pragma: no cover - argparse owns command validation.
            parser.error("unknown command")
            return 2
    except (MaintenanceError, OSError) as exc:
        print(f"Codex Room maintenance error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
