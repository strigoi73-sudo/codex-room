from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import codex_room.maintenance as maintenance
from codex_room.maintenance import (
    MaintenanceError,
    check_data_root,
    create_backup,
    restore_backup,
    verify_backup,
)


def _make_data_root(root: Path) -> Path:
    root.mkdir(parents=True)
    database = root / "codex-room.db"
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute(
        "CREATE TABLE parent (id INTEGER PRIMARY KEY, value TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER NOT NULL "
        "REFERENCES parent(id))"
    )
    connection.execute("INSERT INTO parent(id, value) VALUES (1, 'original')")
    connection.execute("INSERT INTO child(id, parent_id) VALUES (1, 1)")
    connection.commit()
    connection.close()

    shared = root / "rooms" / "room_test" / "shared"
    shared.mkdir(parents=True)
    (shared / "note.txt").write_text("original workspace\n", encoding="utf-8")
    institutional = root / "institutional"
    institutional.mkdir()
    (institutional / "state.json").write_text('{"version":1}\n', encoding="utf-8")
    custom = root / "custom-capabilities" / "capability_x"
    custom.mkdir(parents=True)
    (custom / "manifest.json").write_text('{"id":"capability_x"}\n', encoding="utf-8")
    return root


def _database_value(root: Path) -> str:
    connection = sqlite3.connect(root / "codex-room.db")
    try:
        return connection.execute("SELECT value FROM parent WHERE id=1").fetchone()[0]
    finally:
        connection.close()


def test_check_reports_sqlite_and_payload_health(tmp_path: Path) -> None:
    root = _make_data_root(tmp_path / "data")

    result = check_data_root(root)

    assert result["ok"] is True
    assert result["sqlite"]["quick_check"] == "ok"
    assert result["sqlite"]["foreign_key_violations"] == 0
    assert result["payload_file_count"] == 4


def test_backup_uses_sqlite_backup_and_verifies_manifest(tmp_path: Path) -> None:
    root = _make_data_root(tmp_path / "data")

    result = create_backup(root, offline_confirmed=True)
    backup = Path(result["backup"])
    verified = verify_backup(backup)

    assert backup.parent == root / "backups"
    assert verified["ok"] is True
    assert verified["file_count"] == 4
    assert _database_value(backup) == "original"
    manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
    assert [item["path"] for item in manifest["files"]] == sorted(
        item["path"] for item in manifest["files"]
    )
    assert "codex-room.db-wal" not in {item["path"] for item in manifest["files"]}
    assert "codex-room.db-shm" not in {item["path"] for item in manifest["files"]}


def test_backup_requires_offline_confirmation(tmp_path: Path) -> None:
    root = _make_data_root(tmp_path / "data")

    with pytest.raises(MaintenanceError, match="offline-confirmed"):
        create_backup(root)


def test_verify_detects_payload_tampering(tmp_path: Path) -> None:
    root = _make_data_root(tmp_path / "data")
    backup = Path(create_backup(root, offline_confirmed=True)["backup"])
    payload = backup / "rooms" / "room_test" / "shared" / "note.txt"
    payload.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(MaintenanceError, match="hash mismatch|size mismatch"):
        verify_backup(backup)


def test_verify_rejects_manifest_path_traversal(tmp_path: Path) -> None:
    root = _make_data_root(tmp_path / "data")
    backup = Path(create_backup(root, offline_confirmed=True)["backup"])
    manifest_path = backup / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = "../escape"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(MaintenanceError, match="unsafe"):
        verify_backup(backup)


def test_restore_round_trip_preserves_backup_collection(tmp_path: Path) -> None:
    root = _make_data_root(tmp_path / "data")
    backup = Path(create_backup(root, offline_confirmed=True)["backup"])

    connection = sqlite3.connect(root / "codex-room.db")
    connection.execute("UPDATE parent SET value='changed' WHERE id=1")
    connection.commit()
    connection.close()
    note = root / "rooms" / "room_test" / "shared" / "note.txt"
    note.write_text("changed workspace\n", encoding="utf-8")

    result = restore_backup(
        backup,
        root,
        offline_confirmed=True,
        confirm_replace_data=True,
    )

    assert result["ok"] is True
    assert _database_value(root) == "original"
    assert note.read_text(encoding="utf-8") == "original workspace\n"
    restored_backup = root / "backups" / backup.name
    assert restored_backup.exists()
    assert verify_backup(restored_backup)["ok"] is True
    assert not list(root.parent.glob(f".{root.name}.restore-*"))
    assert not list(root.parent.glob(f".{root.name}.rollback-*"))


def test_restore_requires_both_explicit_confirmations(tmp_path: Path) -> None:
    root = _make_data_root(tmp_path / "data")
    backup = Path(create_backup(root, offline_confirmed=True)["backup"])

    with pytest.raises(MaintenanceError, match="offline-confirmed"):
        restore_backup(backup, root, confirm_replace_data=True)
    with pytest.raises(MaintenanceError, match="confirm-replace-data"):
        restore_backup(backup, root, offline_confirmed=True)


def test_restore_verifies_before_touching_current_data(tmp_path: Path) -> None:
    root = _make_data_root(tmp_path / "data")
    backup = Path(create_backup(root, offline_confirmed=True)["backup"])
    (backup / "rooms" / "room_test" / "shared" / "note.txt").write_text(
        "tampered\n", encoding="utf-8"
    )

    with pytest.raises(MaintenanceError, match="hash mismatch|size mismatch"):
        restore_backup(
            backup,
            root,
            offline_confirmed=True,
            confirm_replace_data=True,
        )

    assert _database_value(root) == "original"
    assert (root / "rooms" / "room_test" / "shared" / "note.txt").read_text(
        encoding="utf-8"
    ) == "original workspace\n"


def test_payload_symlink_is_rejected_when_supported(tmp_path: Path) -> None:
    root = _make_data_root(tmp_path / "data")
    link = root / "rooms" / "room_test" / "shared" / "linked.txt"
    try:
        link.symlink_to(root / "institutional" / "state.json")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(MaintenanceError, match="symlink|reparse"):
        check_data_root(root)


def test_restore_rolls_back_if_candidate_swap_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_data_root(tmp_path / "data")
    backup = Path(create_backup(root, offline_confirmed=True)["backup"])
    connection = sqlite3.connect(root / "codex-room.db")
    connection.execute("UPDATE parent SET value='current' WHERE id=1")
    connection.commit()
    connection.close()

    real_replace = maintenance.os.replace
    calls = 0

    def fail_candidate_swap(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated candidate swap failure")
        return real_replace(source, destination)

    monkeypatch.setattr(maintenance.os, "replace", fail_candidate_swap)

    with pytest.raises(OSError, match="simulated candidate swap failure"):
        restore_backup(
            backup,
            root,
            offline_confirmed=True,
            confirm_replace_data=True,
        )

    assert _database_value(root) == "current"
    assert not list(root.parent.glob(f".{root.name}.restore-*"))
    assert not list(root.parent.glob(f".{root.name}.rollback-*"))
