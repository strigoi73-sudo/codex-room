from __future__ import annotations

import os
from pathlib import Path

import pytest

from codex_room.capabilities import CORE_CAPABILITIES, invoke_capability
from codex_room.source_inspection import SourceInspectionError, inspect_source


def _canonical_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    current = tmp_path / "data" / "rooms" / "room_current" / "shared"
    other = tmp_path / "data" / "rooms" / "room_other" / "shared"
    current.mkdir(parents=True)
    other.mkdir(parents=True)

    (tmp_path / "codex_room").mkdir()
    (tmp_path / "codex_room" / "db.py").write_text(
        "CORE_CANARY = 'core-value'\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_sample.py").write_text(
        "def test_sample():\n    assert True\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("CORE README\n", encoding="utf-8")
    (tmp_path / "data" / "private-runtime.txt").write_text(
        "MUST_NOT_BE_CORE_READABLE\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("SECRET=not-readable\n", encoding="utf-8")

    (current / "current.txt").write_text("current workspace\n", encoding="utf-8")
    (other / "notes.txt").write_text(
        "other room shared evidence\nSECOND_CANARY\n",
        encoding="utf-8",
    )
    (other.parent / "private.txt").write_text(
        "MUST_NOT_BE_CROSS_ROOM_READABLE\n",
        encoding="utf-8",
    )
    return current, other, tmp_path


def test_inspect_source_is_registered_read_only_core_capability() -> None:
    spec = CORE_CAPABILITIES["inspect_source"]

    assert spec.version == "3"
    assert spec.durable_result_fields == ("evidence",)
    assert spec.permissions["workspace_read"] is True
    assert spec.permissions["cross_room_read"] is True
    assert spec.permissions["core_source_read"] is True
    assert spec.permissions["workspace_write"] is False
    assert spec.side_effects == "none"


def test_sources_discovers_core_and_room_shared_workspaces(tmp_path: Path) -> None:
    current, _, _ = _canonical_fixture(tmp_path)

    result = inspect_source(current, {"operation": "sources"})
    evidence = result["evidence"]

    assert evidence["current_room_id"] == "room_current"
    assert "codex_room" in evidence["core"]["allowed_entries"]
    assert "README.md" in evidence["core"]["allowed_entries"]
    assert [item["room_id"] for item in evidence["rooms"]] == [
        "room_current",
        "room_other",
    ]
    assert next(
        item for item in evidence["rooms"] if item["room_id"] == "room_current"
    )["current"] is True
    assert evidence["room_source_note"] == (
        "Room reads expose only each Room's shared workspace."
    )


def test_read_core_source_allows_maintained_surface_and_blocks_runtime_data(
    tmp_path: Path,
) -> None:
    current, _, _ = _canonical_fixture(tmp_path)

    result = inspect_source(
        current,
        {
            "operation": "read",
            "source": "core",
            "path": "codex_room/db.py",
        },
    )

    assert result["content"] == "CORE_CANARY = 'core-value'\n"
    assert result["evidence"]["source"] == {"kind": "core"}
    assert result["evidence"]["path"] == "codex_room/db.py"

    for forbidden in ("data/private-runtime.txt", ".env"):
        with pytest.raises(SourceInspectionError, match="maintained source surface"):
            inspect_source(
                current,
                {
                    "operation": "read",
                    "source": "core",
                    "path": forbidden,
                },
            )


def test_cross_room_read_exposes_only_shared_workspace(tmp_path: Path) -> None:
    current, _, _ = _canonical_fixture(tmp_path)

    result = inspect_source(
        current,
        {
            "operation": "read",
            "source": "room",
            "room_id": "room_other",
            "path": "notes.txt",
        },
    )

    assert "SECOND_CANARY" in result["content"]
    assert result["evidence"]["source"] == {
        "kind": "room",
        "room_id": "room_other",
    }

    with pytest.raises(SourceInspectionError, match="stay inside"):
        inspect_source(
            current,
            {
                "operation": "read",
                "source": "room",
                "room_id": "room_other",
                "path": "../private.txt",
            },
        )


def test_find_and_search_work_across_authorized_sources(tmp_path: Path) -> None:
    current, _, _ = _canonical_fixture(tmp_path)

    found = inspect_source(
        current,
        {
            "operation": "find",
            "source": "core",
            "path": "codex_room",
            "include_globs": ["*.py"],
        },
    )
    assert [item["path"] for item in found["evidence"]["matches"]] == [
        "codex_room/db.py"
    ]

    searched = inspect_source(
        current,
        {
            "operation": "search",
            "source": "room",
            "room_id": "room_other",
            "path": ".",
            "query": "SECOND_CANARY",
        },
    )
    assert searched["matches"][0]["path"] == "notes.txt"
    assert searched["evidence"]["locations"] == [
        {"path": "notes.txt", "line": 2, "column": 1}
    ]


def test_read_content_is_transient_under_capability_durable_contract(
    tmp_path: Path,
) -> None:
    current, _, _ = _canonical_fixture(tmp_path)

    result = invoke_capability(
        current,
        "inspect_source",
        {
            "operation": "read",
            "source": "core",
            "path": "README.md",
        },
    )

    assert result["content"] == "CORE README\n"
    assert result["durable_result_fields"] == ["evidence"]
    assert result["capability_version"] == "2"
    assert len(result["implementation_sha256"]) == 64


def test_workspace_source_remains_available_outside_canonical_room(tmp_path: Path) -> None:
    (tmp_path / "local.txt").write_text("LOCAL_CANARY\n", encoding="utf-8")

    result = inspect_source(
        tmp_path,
        {
            "operation": "read",
            "source": "workspace",
            "path": "local.txt",
        },
    )

    assert result["content"] == "LOCAL_CANARY\n"
    assert result["evidence"]["source"] == {"kind": "workspace"}


def test_read_normalizes_platform_newlines_without_changing_raw_file_evidence(
    tmp_path: Path,
) -> None:
    raw = b"FIRST\r\nSECOND\rTHIRD\n"
    path = tmp_path / "mixed.txt"
    path.write_bytes(raw)

    result = inspect_source(
        tmp_path,
        {
            "operation": "read",
            "source": "workspace",
            "path": "mixed.txt",
        },
    )

    assert result["content"] == "FIRST\nSECOND\nTHIRD\n"
    assert result["evidence"]["size_bytes"] == len(raw)
    assert result["evidence"]["sha256"] == __import__("hashlib").sha256(raw).hexdigest()


def test_cross_boundary_sources_require_canonical_room_context(tmp_path: Path) -> None:
    with pytest.raises(SourceInspectionError, match="canonical Room"):
        inspect_source(
            tmp_path,
            {
                "operation": "read",
                "source": "core",
                "path": "README.md",
            },
        )

    with pytest.raises(SourceInspectionError, match="canonical Room"):
        inspect_source(tmp_path, {"operation": "sources"})


def test_inspection_rejects_symlink_or_reparse_escape(tmp_path: Path) -> None:
    current, other, root = _canonical_fixture(tmp_path)
    external = root / "outside.txt"
    external.write_text("OUTSIDE_CANARY\n", encoding="utf-8")
    link = other / "escape.txt"
    try:
        link.symlink_to(external)
    except (OSError, NotImplementedError):
        pytest.skip("test platform cannot create symlinks")

    found = inspect_source(
        current,
        {
            "operation": "find",
            "source": "room",
            "room_id": "room_other",
            "path": ".",
            "include_hidden": True,
        },
    )
    assert "escape.txt" not in {
        item["path"] for item in found["evidence"]["matches"]
    }

    with pytest.raises(SourceInspectionError, match="links or reparse points"):
        inspect_source(
            current,
            {
                "operation": "read",
                "source": "room",
                "room_id": "room_other",
                "path": "escape.txt",
            },
        )


def test_core_root_cannot_be_scanned_wholesale(tmp_path: Path) -> None:
    current, _, _ = _canonical_fixture(tmp_path)

    with pytest.raises(SourceInspectionError, match="allowed CORE entry"):
        inspect_source(
            current,
            {
                "operation": "find",
                "source": "core",
                "path": ".",
            },
        )


def test_read_is_bounded_and_reports_truncation(tmp_path: Path) -> None:
    current, other, _ = _canonical_fixture(tmp_path)
    (other / "long.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")

    result = inspect_source(
        current,
        {
            "operation": "read",
            "source": "room",
            "room_id": "room_other",
            "path": "long.txt",
            "start_line": 2,
            "max_lines": 1,
        },
    )

    assert result["content"] == "two\n"
    assert result["evidence"]["start_line"] == 2
    assert result["evidence"]["returned_lines"] == 1
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "max_lines"

def test_search_many_scans_once_and_groups_queries(tmp_path: Path) -> None:
    current, _, root = _canonical_fixture(tmp_path)
    (root / "codex_room" / "extra.py").write_text(
        "ALPHA one\nBETA two\nALPHA BETA\n",
        encoding="utf-8",
    )

    result = inspect_source(
        current,
        {
            "operation": "search_many",
            "source": "core",
            "path": "codex_room",
            "queries": ["ALPHA", "BETA"],
        },
    )

    assert result["evidence"]["operation"] == "search_many"
    assert result["evidence"]["query_count"] == 2
    assert result["evidence"]["files_searched"] == 2
    assert [item["query"] for item in result["results"]] == ["ALPHA", "BETA"]
    assert [len(item["matches"]) for item in result["results"]] == [2, 2]
    assert [item["match_count"] for item in result["evidence"]["queries"]] == [2, 2]


def test_search_many_rejects_duplicate_or_oversized_query_batch(tmp_path: Path) -> None:
    current, _, _ = _canonical_fixture(tmp_path)

    with pytest.raises(SourceInspectionError, match="duplicates"):
        inspect_source(
            current,
            {
                "operation": "search_many",
                "source": "core",
                "path": "codex_room",
                "queries": ["same", "same"],
            },
        )

    with pytest.raises(SourceInspectionError, match="1 to"):
        inspect_source(
            current,
            {
                "operation": "search_many",
                "source": "core",
                "path": "codex_room",
                "queries": [f"q{index}" for index in range(17)],
            },
        )


def test_read_many_returns_bounded_ranges_in_one_result(tmp_path: Path) -> None:
    current, other, _ = _canonical_fixture(tmp_path)
    (other / "first.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
    (other / "second.txt").write_text("alpha\nbeta\n", encoding="utf-8")

    result = inspect_source(
        current,
        {
            "operation": "read_many",
            "source": "room",
            "room_id": "room_other",
            "reads": [
                {"path": "first.txt", "start_line": 2, "max_lines": 1},
                {"path": "second.txt", "start_line": 1, "max_lines": 2},
            ],
        },
    )

    assert result["evidence"]["operation"] == "read_many"
    assert result["evidence"]["requested_count"] == 2
    assert result["evidence"]["returned_count"] == 2
    assert [item["content"] for item in result["reads"]] == ["two\n", "alpha\nbeta\n"]
    assert [item["path"] for item in result["evidence"]["reads"]] == [
        "first.txt",
        "second.txt",
    ]


def test_read_many_enforces_total_output_bound(tmp_path: Path) -> None:
    current, other, _ = _canonical_fixture(tmp_path)
    (other / "first.txt").write_text("abcdefghij\n", encoding="utf-8")
    (other / "second.txt").write_text("klmnopqrst\n", encoding="utf-8")

    result = inspect_source(
        current,
        {
            "operation": "read_many",
            "source": "room",
            "room_id": "room_other",
            "reads": [
                {"path": "first.txt"},
                {"path": "second.txt"},
            ],
            "max_bytes": 5,
        },
    )

    assert result["evidence"]["returned_bytes"] == 5
    assert result["evidence"]["returned_count"] == 1
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "batch_max_bytes"

