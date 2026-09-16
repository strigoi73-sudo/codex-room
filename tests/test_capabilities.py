from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import codex_room.capabilities as capabilities
from codex_room.capabilities import (
    CapabilityUsageError,
    assert_file,
    compare_files,
    find_files,
    inspect_capability,
    invoke_capability,
    list_capabilities,
    main,
    search_text,
)


def test_assert_file_combines_exact_hash_and_json_checks(tmp_path: Path) -> None:
    artifact = tmp_path / "result.json"
    artifact.write_text('{"id": 7, "status": "ok"}', encoding="utf-8")
    expected_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()

    result = assert_file(
        tmp_path,
        "result.json",
        exists=True,
        sha256_equals=expected_hash,
        json_valid=True,
        required_keys=["id", "status"],
    )

    assert result["ok"] is True
    assert result["subject"]["sha256"] == expected_hash
    assert [check["name"] for check in result["checks"]] == [
        "exists",
        "sha256_equals",
        "json_valid",
        "json_required_key",
        "json_required_key",
    ]
    assert all(check["ok"] for check in result["checks"])


def test_assert_file_reports_false_assertion_without_execution_error(tmp_path: Path) -> None:
    artifact = tmp_path / "result.json"
    artifact.write_text('{"id": 7}', encoding="utf-8")

    result = assert_file(
        tmp_path,
        "result.json",
        json_valid=True,
        required_keys=["missing"],
    )

    assert result["ok"] is False
    missing = result["checks"][-1]
    assert missing["name"] == "json_required_key"
    assert missing["actual"] is False


@pytest.mark.parametrize("path", ["../outside.txt", "/tmp/outside.txt"])
def test_assert_file_rejects_workspace_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises(CapabilityUsageError, match="Room workspace"):
        assert_file(tmp_path, path, exists=True)


def test_cli_emits_one_machine_readable_result(tmp_path: Path, monkeypatch, capsys) -> None:
    artifact = tmp_path / "data.json"
    artifact.write_text('{"id": 1}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["assert-file", "data.json", "--json-valid", "--required-key", "id"])

    assert exit_code == 0
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    payload = json.loads(output[0])
    assert payload["codex_room_capability"] == 1
    assert payload["capability"] == "assert_file"
    assert payload["ok"] is True


def test_exists_assertion_requires_regular_file(tmp_path: Path) -> None:
    directory = tmp_path / "artifact"
    directory.mkdir()

    result = assert_file(tmp_path, "artifact", exists=True)

    assert result["ok"] is False
    assert result["subject"]["exists"] is True
    assert result["subject"]["is_file"] is False
    assert result["checks"][0]["actual"] is False



def test_registry_exposes_assert_file_as_versioned_core_capability() -> None:
    registry = list_capabilities()

    assert registry["codex_room_registry"] == 1
    assert registry["operation"] == "list"
    assert [item["id"] for item in registry["capabilities"]] == [
        "assert_file",
        "compare_files",
        "find_files",
        "inspect_source",
        "search_text",
    ]
    manifest = registry["capabilities"][0]
    assert manifest["id"] == "assert_file"
    assert manifest["origin"] == "core"
    assert manifest["scope"] == "core"
    assert manifest["version"] == "1"
    assert len(manifest["implementation_sha256"]) == 64
    assert "permissions" not in manifest
    assert "input_schema" not in manifest
    inspected = inspect_capability("assert_file")["capability"]
    assert inspected["permissions"] == {
        "workspace_read": True,
        "workspace_write": False,
        "network": False,
        "external_process": False,
    }
    assert inspected["side_effects"] == "none"
    assert inspected["verification"]["status"] == "verified"
    assert inspected["input_schema"]["required"] == ["path"]
    assert inspected["durable_result_fields"] == ["subject", "checks"]


def test_find_files_filters_globs_hidden_paths_and_size(tmp_path: Path) -> None:
    (tmp_path / "root.md").write_text("root", encoding="utf-8")
    (tmp_path / "root.txt").write_text("text", encoding="utf-8")
    (tmp_path / ".hidden.md").write_text("hidden", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("alpha", encoding="utf-8")
    (docs / "b.txt").write_text("beta", encoding="utf-8")
    hidden_docs = docs / ".hidden"
    hidden_docs.mkdir()
    (hidden_docs / "secret.md").write_text("secret", encoding="utf-8")
    nested = docs / "sub"
    nested.mkdir()
    (nested / "c.md").write_text("charlie", encoding="utf-8")

    result = find_files(
        tmp_path,
        include_globs=["**/*.md"],
        exclude_globs=["docs/sub/**"],
        min_size_bytes=4,
        max_size_bytes=5,
    )

    assert result["ok"] is True
    assert result["evidence"]["truncated"] is False
    assert result["evidence"]["truncation_reason"] is None
    assert result["evidence"]["symlinks_followed"] is False
    assert [item["path"] for item in result["evidence"]["matches"]] == [
        "root.md",
        "docs/a.md",
    ]
    assert [item["size_bytes"] for item in result["evidence"]["matches"]] == [4, 5]


def test_find_files_hidden_files_are_opt_in(tmp_path: Path) -> None:
    (tmp_path / ".hidden.txt").write_text("hidden", encoding="utf-8")
    (tmp_path / "visible.txt").write_text("visible", encoding="utf-8")

    default_result = find_files(tmp_path, include_globs=["*.txt"])
    hidden_result = find_files(
        tmp_path,
        include_globs=["*.txt"],
        include_hidden=True,
    )

    assert [item["path"] for item in default_result["evidence"]["matches"]] == [
        "visible.txt"
    ]
    assert [item["path"] for item in hidden_result["evidence"]["matches"]] == [
        ".hidden.txt",
        "visible.txt",
    ]


def test_find_files_never_follows_file_or_directory_symlinks(tmp_path: Path) -> None:
    target_file = tmp_path / "target.txt"
    target_file.write_text("target", encoding="utf-8")
    target_dir = tmp_path / "target_dir"
    target_dir.mkdir()
    (target_dir / "nested.txt").write_text("nested", encoding="utf-8")
    try:
        (tmp_path / "file_link.txt").symlink_to(target_file)
        (tmp_path / "dir_link").symlink_to(target_dir, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("test platform cannot create symlinks")

    result = find_files(tmp_path, include_globs=["*.txt"], include_hidden=True)
    paths = [item["path"] for item in result["evidence"]["matches"]]

    assert "file_link.txt" not in paths
    assert all(not path.startswith("dir_link/") for path in paths)
    assert "target.txt" in paths
    assert "target_dir/nested.txt" in paths


def test_find_files_reports_explicit_result_truncation(tmp_path: Path) -> None:
    for name in ("a.txt", "b.txt", "c.txt"):
        (tmp_path / name).write_text(name, encoding="utf-8")

    result = find_files(tmp_path, include_globs=["*.txt"], max_results=2)

    assert [item["path"] for item in result["evidence"]["matches"]] == [
        "a.txt",
        "b.txt",
    ]
    assert result["evidence"]["returned_count"] == 2
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "max_results"


def test_find_files_reports_explicit_scan_limit_truncation(
    tmp_path: Path, monkeypatch
) -> None:
    for name in ("a.txt", "b.txt", "c.txt"):
        (tmp_path / name).write_text(name, encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_FIND_FILES_SCANNED_ENTRIES", 2)

    result = find_files(tmp_path, include_globs=["*.txt"], max_results=10)

    assert [item["path"] for item in result["evidence"]["matches"]] == [
        "a.txt",
        "b.txt",
    ]
    assert result["evidence"]["scanned_entries"] == 2
    assert result["evidence"]["scan_limit_entries"] == 2
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "scan_limit"


def test_find_files_reports_explicit_match_byte_truncation(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_FIND_FILES_MATCH_BYTES", 45)

    result = find_files(tmp_path, include_globs=["*.txt"], max_results=10)

    assert [item["path"] for item in result["evidence"]["matches"]] == ["a.txt"]
    assert result["evidence"]["match_byte_limit"] == 45
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "result_bytes"


@pytest.mark.parametrize("path", ["../outside", "/tmp/outside"])
def test_find_files_rejects_workspace_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises(CapabilityUsageError, match="Room workspace"):
        find_files(tmp_path, path)


def test_find_files_does_not_silently_ignore_walk_errors(
    tmp_path: Path, monkeypatch
) -> None:
    def broken_walk(*args, **kwargs):
        kwargs["onerror"](OSError("denied"))
        return []

    monkeypatch.setattr(capabilities.os, "walk", broken_walk)

    with pytest.raises(CapabilityUsageError, match="could not scan workspace"):
        find_files(tmp_path)


def test_registered_find_files_exposes_bounded_read_only_contract(tmp_path: Path) -> None:
    artifact = tmp_path / "probe.json"
    artifact.write_text('{"probe": true}', encoding="utf-8")

    inspected = inspect_capability("find_files")["capability"]
    invoked = invoke_capability(
        tmp_path,
        "find_files",
        {
            "include_globs": ["**/*.json"],
            "max_results": 10,
        },
    )

    assert inspected["origin"] == "core"
    assert inspected["scope"] == "core"
    assert inspected["version"] == "1"
    assert inspected["durable_result_fields"] == ["evidence"]
    assert inspected["permissions"] == {
        "workspace_read": True,
        "workspace_write": False,
        "network": False,
        "external_process": False,
    }
    assert inspected["side_effects"] == "none"
    assert inspected["verification"] == {"status": "verified", "evidence": ["E-032"]}
    assert invoked["capability_version"] == inspected["version"]
    assert invoked["implementation_sha256"] == inspected["implementation_sha256"]
    assert invoked["durable_result_fields"] == ["evidence"]
    assert [item["path"] for item in invoked["evidence"]["matches"]] == ["probe.json"]


@pytest.mark.parametrize(
    ("inputs", "match"),
    [
        ({"invented": True}, "unknown find_files input field"),
        ({"include_globs": "*.txt"}, "include_globs"),
        ({"exclude_globs": ["../*.txt"]}, "workspace-relative glob"),
        ({"include_hidden": 1}, "include_hidden"),
        ({"min_size_bytes": -1}, "min_size_bytes"),
        ({"min_size_bytes": 10, "max_size_bytes": 5}, "must not exceed"),
        ({"max_results": 0}, "max_results"),
        ({"max_results": 201}, "max_results"),
    ],
)
def test_registered_find_files_rejects_invalid_inputs(
    tmp_path: Path, inputs: dict[str, object], match: str
) -> None:
    with pytest.raises(CapabilityUsageError, match=match):
        invoke_capability(tmp_path, "find_files", inputs)


def test_search_text_returns_literal_matches_and_private_runtime_excerpts(
    tmp_path: Path,
) -> None:
    (tmp_path / "root.txt").write_text(
        "Needle one\nneedle two\nx.needlex\n",
        encoding="utf-8",
    )
    (tmp_path / ".hidden.txt").write_text("needle hidden", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ignored.txt").write_text("needle ignored", encoding="utf-8")

    result = search_text(
        tmp_path,
        "needle",
        include_globs=["**/*.txt"],
        exclude_globs=["docs/**"],
        case_sensitive=False,
    )

    assert result["ok"] is True
    assert result["evidence"]["query_sha256"] == hashlib.sha256(b"needle").hexdigest()
    assert result["evidence"]["query_length"] == 6
    assert result["evidence"]["case_sensitive"] is False
    assert result["evidence"]["truncated"] is False
    assert result["evidence"]["locations"] == [
        {"path": "root.txt", "line": 1, "column": 1},
        {"path": "root.txt", "line": 2, "column": 1},
        {"path": "root.txt", "line": 3, "column": 3},
    ]
    assert [match["excerpt"] for match in result["matches"]] == [
        "Needle one",
        "needle two",
        "x.needlex",
    ]
    assert all("excerpt" not in item for item in result["evidence"]["locations"])
    assert "query" not in result["evidence"]


def test_search_text_bounds_long_line_excerpts(tmp_path: Path) -> None:
    line = ("a" * 500) + "needle" + ("b" * 500)
    (tmp_path / "long.txt").write_text(line, encoding="utf-8")

    result = search_text(tmp_path, "needle", include_globs=["*.txt"])

    match = result["matches"][0]
    assert len(match["excerpt"]) == capabilities.SEARCH_TEXT_EXCERPT_CHARS
    assert "needle" in match["excerpt"]
    assert match["column"] == 501
    assert match["excerpt_start_column"] > 1


def test_search_text_treats_query_as_literal_not_regex(tmp_path: Path) -> None:
    (tmp_path / "data.txt").write_text("a.b\naxb\n", encoding="utf-8")

    result = search_text(tmp_path, ".", include_globs=["*.txt"])

    assert result["evidence"]["locations"] == [
        {"path": "data.txt", "line": 1, "column": 2}
    ]


def test_search_text_case_sensitive_by_default(tmp_path: Path) -> None:
    (tmp_path / "data.txt").write_text("Needle\nneedle\n", encoding="utf-8")

    result = search_text(tmp_path, "needle", include_globs=["*.txt"])

    assert result["evidence"]["locations"] == [
        {"path": "data.txt", "line": 2, "column": 1}
    ]


def test_search_text_skips_non_utf8_and_nul_files(tmp_path: Path) -> None:
    (tmp_path / "good.txt").write_text("needle", encoding="utf-8")
    (tmp_path / "bad.txt").write_bytes(b"\xffneedle")
    (tmp_path / "contains-nul.txt").write_bytes(b"needle\x00rest")

    result = search_text(tmp_path, "needle", include_globs=["*.txt"])

    assert [item["path"] for item in result["evidence"]["locations"]] == ["good.txt"]
    assert result["evidence"]["files_searched"] == 1
    assert result["evidence"]["skipped_non_text"] == 2
    assert result["evidence"]["bytes_read"] == (
        len(b"\xffneedle") + len(b"needle") + len(b"needle\x00rest")
    )


def test_search_text_reports_oversized_files_as_incomplete(tmp_path: Path) -> None:
    (tmp_path / "a-large.txt").write_text("needle too large", encoding="utf-8")
    (tmp_path / "b-small.txt").write_text("needle", encoding="utf-8")

    result = search_text(
        tmp_path,
        "needle",
        include_globs=["*.txt"],
        max_file_bytes=6,
    )

    assert result["evidence"]["skipped_oversize_files"] == 1
    assert result["evidence"]["files_searched"] == 1
    assert result["evidence"]["locations"] == [
        {"path": "b-small.txt", "line": 1, "column": 1}
    ]
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "oversize_files"


def test_search_text_reports_candidate_truncation(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hit", encoding="utf-8")
    (tmp_path / "b.txt").write_text("hit", encoding="utf-8")

    result = search_text(
        tmp_path,
        "hit",
        include_globs=["*.txt"],
        max_files=1,
    )

    assert result["evidence"]["candidate_truncated"] is True
    assert result["evidence"]["candidate_truncation_reason"] == "max_results"
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "candidate_max_results"
    assert result["evidence"]["locations"] == [
        {"path": "a.txt", "line": 1, "column": 1}
    ]


def test_search_text_reports_match_limit_truncation(tmp_path: Path) -> None:
    (tmp_path / "data.txt").write_text("x x x", encoding="utf-8")

    result = search_text(
        tmp_path,
        "x",
        include_globs=["*.txt"],
        max_matches=2,
    )

    assert result["evidence"]["match_count"] == 2
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "max_matches"


def test_search_text_reports_result_byte_truncation(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "data.txt").write_text("needle", encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_SEARCH_TEXT_MATCH_BYTES", 1)

    result = search_text(tmp_path, "needle", include_globs=["*.txt"])

    assert result["evidence"]["match_count"] == 0
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "result_bytes"


def test_search_text_reports_durable_location_byte_truncation(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "data.txt").write_text("needle", encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_SEARCH_TEXT_LOCATION_BYTES", 1)

    result = search_text(tmp_path, "needle", include_globs=["*.txt"])

    assert result["evidence"]["match_count"] == 0
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "durable_bytes"


def test_search_text_reports_total_byte_truncation(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "a.txt").write_text("aaaa", encoding="utf-8")
    (tmp_path / "b.txt").write_text("bbbb", encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_SEARCH_TEXT_TOTAL_BYTES", 5)

    result = search_text(tmp_path, "z", include_globs=["*.txt"])

    assert result["evidence"]["bytes_read"] == 4
    assert result["evidence"]["files_searched"] == 1
    assert result["evidence"]["truncated"] is True
    assert result["evidence"]["truncation_reason"] == "total_bytes"


@pytest.mark.parametrize("path", ["../outside", "/tmp/outside"])
def test_search_text_rejects_workspace_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises(CapabilityUsageError, match="Room workspace"):
        search_text(tmp_path, "needle", path)


def test_registered_search_text_exposes_safe_durable_contract(tmp_path: Path) -> None:
    (tmp_path / "probe.txt").write_text("prefix needle suffix", encoding="utf-8")

    inspected = inspect_capability("search_text")["capability"]
    invoked = invoke_capability(
        tmp_path,
        "search_text",
        {
            "query": "needle",
            "include_globs": ["*.txt"],
        },
    )

    assert inspected["origin"] == "core"
    assert inspected["scope"] == "core"
    assert inspected["version"] == "1"
    assert inspected["durable_result_fields"] == ["evidence"]
    assert inspected["permissions"] == {
        "workspace_read": True,
        "workspace_write": False,
        "network": False,
        "external_process": False,
    }
    assert inspected["verification"] == {"status": "verified", "evidence": ["E-032"]}
    assert invoked["capability_version"] == inspected["version"]
    assert invoked["implementation_sha256"] == inspected["implementation_sha256"]
    assert invoked["durable_result_fields"] == ["evidence"]
    assert invoked["matches"][0]["excerpt"] == "prefix needle suffix"
    assert invoked["evidence"]["locations"] == [
        {"path": "probe.txt", "line": 1, "column": 8}
    ]
    assert "query" not in invoked["evidence"]


@pytest.mark.parametrize(
    ("inputs", "match"),
    [
        ({"query": "x", "invented": True}, "unknown search_text input field"),
        ({}, "query"),
        ({"query": ""}, "query"),
        ({"query": "a\nb"}, "single-line"),
        ({"query": "\udcff"}, "valid UTF-8"),
        ({"query": "x", "include_globs": "*.txt"}, "include_globs"),
        ({"query": "x", "exclude_globs": ["../*.txt"]}, "workspace-relative glob"),
        ({"query": "x", "include_hidden": 1}, "include_hidden"),
        ({"query": "x", "case_sensitive": 1}, "case_sensitive"),
        ({"query": "x", "max_files": 0}, "max_files"),
        ({"query": "x", "max_files": 201}, "max_files"),
        ({"query": "x", "max_matches": 0}, "max_matches"),
        ({"query": "x", "max_matches": 101}, "max_matches"),
        ({"query": "x", "max_file_bytes": 0}, "max_file_bytes"),
        (
            {"query": "x", "max_file_bytes": 10 * 1024 * 1024 + 1},
            "max_file_bytes",
        ),
    ],
)
def test_registered_search_text_rejects_invalid_inputs(
    tmp_path: Path, inputs: dict[str, object], match: str
) -> None:
    with pytest.raises(CapabilityUsageError, match=match):
        invoke_capability(tmp_path, "search_text", inputs)


def test_compare_files_reports_exact_equal_bytes_and_hashes(tmp_path: Path) -> None:
    content = b"same\nbytes\n"
    (tmp_path / "left.txt").write_bytes(content)
    (tmp_path / "right.txt").write_bytes(content)

    result = compare_files(tmp_path, "left.txt", "right.txt")

    expected_hash = hashlib.sha256(content).hexdigest()
    assert result["ok"] is True
    assert result["evidence"]["byte_equal"] is True
    assert result["evidence"]["left"]["sha256"] == expected_hash
    assert result["evidence"]["right"]["sha256"] == expected_hash
    assert result["evidence"]["left"]["size_bytes"] == len(content)
    assert result["evidence"]["right"]["size_bytes"] == len(content)
    assert result["evidence"]["text_diff"]["status"] == "not_needed_equal"
    assert result["diff"] == []


def test_compare_files_returns_bounded_transient_text_diff(tmp_path: Path) -> None:
    (tmp_path / "left.txt").write_text(
        "alpha\nbefore\nomega\n", encoding="utf-8"
    )
    (tmp_path / "right.txt").write_text(
        "alpha\nafter\nomega\n", encoding="utf-8"
    )

    result = compare_files(tmp_path, "left.txt", "right.txt", context_lines=1)

    assert result["evidence"]["byte_equal"] is False
    text_diff = result["evidence"]["text_diff"]
    assert text_diff["status"] == "available"
    assert text_diff["text_lines_equal"] is False
    assert text_diff["context_lines"] == 1
    assert text_diff["truncated"] is False
    assert any(line == "-before" for line in result["diff"])
    assert any(line == "+after" for line in result["diff"])
    assert all("before" not in json.dumps(value) for value in [result["evidence"]])


def test_compare_files_distinguishes_line_ending_only_changes(tmp_path: Path) -> None:
    (tmp_path / "left.txt").write_bytes(b"alpha\r\nbeta\r\n")
    (tmp_path / "right.txt").write_bytes(b"alpha\nbeta\n")

    result = compare_files(tmp_path, "left.txt", "right.txt")

    assert result["evidence"]["byte_equal"] is False
    assert result["evidence"]["text_diff"]["status"] == "available"
    assert result["evidence"]["text_diff"]["text_lines_equal"] is True
    assert result["diff"] == []


def test_compare_files_does_not_diff_binary_inputs(tmp_path: Path) -> None:
    (tmp_path / "left.bin").write_bytes(b"a\x00b")
    (tmp_path / "right.bin").write_bytes(b"a\x00c")

    result = compare_files(tmp_path, "left.bin", "right.bin")

    assert result["evidence"]["byte_equal"] is False
    assert result["evidence"]["text_diff"]["status"] == "non_text"
    assert result["diff"] == []


def test_compare_files_skips_text_diff_above_text_size_limit(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "left.txt").write_text("abcdef", encoding="utf-8")
    (tmp_path / "right.txt").write_text("abcdeg", encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_COMPARE_TEXT_BYTES", 5)

    result = compare_files(tmp_path, "left.txt", "right.txt")

    assert result["evidence"]["byte_equal"] is False
    assert result["evidence"]["text_diff"]["status"] == "size_limit"
    assert result["diff"] == []


def test_compare_files_skips_diff_above_text_line_limit(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "left.txt").write_text("a\nb\nc\n", encoding="utf-8")
    (tmp_path / "right.txt").write_text("a\nb\nd\n", encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_COMPARE_TEXT_LINES", 2)

    result = compare_files(tmp_path, "left.txt", "right.txt")

    text_diff = result["evidence"]["text_diff"]
    assert text_diff["status"] == "line_limit"
    assert text_diff["left_line_count"] == 3
    assert text_diff["right_line_count"] == 3
    assert result["diff"] == []


def test_compare_files_reports_diff_line_truncation(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "left.txt").write_text("a\nb\nc\n", encoding="utf-8")
    (tmp_path / "right.txt").write_text("x\ny\nz\n", encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_COMPARE_DIFF_LINES", 3)

    result = compare_files(tmp_path, "left.txt", "right.txt", context_lines=0)

    text_diff = result["evidence"]["text_diff"]
    assert text_diff["status"] == "available"
    assert text_diff["truncated"] is True
    assert text_diff["truncation_reason"] == "line_limit"
    assert text_diff["returned_diff_lines"] == 3


def test_compare_files_reports_diff_byte_truncation(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "left.txt").write_text("before\n", encoding="utf-8")
    (tmp_path / "right.txt").write_text("after\n", encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_COMPARE_DIFF_BYTES", 1)

    result = compare_files(tmp_path, "left.txt", "right.txt")

    text_diff = result["evidence"]["text_diff"]
    assert text_diff["truncated"] is True
    assert text_diff["truncation_reason"] == "byte_limit"
    assert result["diff"] == []


@pytest.mark.parametrize("path", ["../outside.txt", "/tmp/outside.txt"])
def test_compare_files_rejects_workspace_escape(tmp_path: Path, path: str) -> None:
    (tmp_path / "inside.txt").write_text("inside", encoding="utf-8")

    with pytest.raises(CapabilityUsageError, match="Room workspace"):
        compare_files(tmp_path, path, "inside.txt")


def test_compare_files_enforces_file_size_limit(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "left.txt").write_text("large", encoding="utf-8")
    (tmp_path / "right.txt").write_text("small", encoding="utf-8")
    monkeypatch.setattr(capabilities, "MAX_COMPARE_FILE_BYTES", 4)

    with pytest.raises(CapabilityUsageError, match="file limit"):
        compare_files(tmp_path, "left.txt", "right.txt")


def test_registered_compare_files_exposes_safe_durable_contract(tmp_path: Path) -> None:
    (tmp_path / "left.txt").write_text("before", encoding="utf-8")
    (tmp_path / "right.txt").write_text("after", encoding="utf-8")

    inspected = inspect_capability("compare_files")["capability"]
    invoked = invoke_capability(
        tmp_path,
        "compare_files",
        {"left_path": "left.txt", "right_path": "right.txt"},
    )

    assert inspected["origin"] == "core"
    assert inspected["scope"] == "core"
    assert inspected["version"] == "1"
    assert inspected["durable_result_fields"] == ["evidence"]
    assert inspected["permissions"] == {
        "workspace_read": True,
        "workspace_write": False,
        "network": False,
        "external_process": False,
    }
    assert inspected["side_effects"] == "none"
    assert inspected["verification"] == {"status": "verified", "evidence": ["E-032"]}
    assert invoked["capability_version"] == inspected["version"]
    assert invoked["implementation_sha256"] == inspected["implementation_sha256"]
    assert invoked["durable_result_fields"] == ["evidence"]
    assert invoked["evidence"]["byte_equal"] is False
    assert invoked["diff"]


@pytest.mark.parametrize(
    ("inputs", "match"),
    [
        ({"left_path": "a", "right_path": "b", "invented": True}, "unknown compare_files"),
        ({"right_path": "b"}, "left_path"),
        ({"left_path": "a"}, "right_path"),
        ({"left_path": "a", "right_path": "b", "context_lines": -1}, "context_lines"),
        ({"left_path": "a", "right_path": "b", "context_lines": 11}, "context_lines"),
        ({"left_path": "a", "right_path": "b", "context_lines": True}, "context_lines"),
    ],
)
def test_registered_compare_files_rejects_invalid_inputs(
    tmp_path: Path, inputs: dict[str, object], match: str
) -> None:
    with pytest.raises(CapabilityUsageError, match=match):
        invoke_capability(tmp_path, "compare_files", inputs)


def test_inspect_and_invoke_share_exact_registered_version(tmp_path: Path) -> None:
    artifact = tmp_path / "registered.json"
    artifact.write_text('{"probe": "P4.2"}', encoding="utf-8")

    inspected = inspect_capability("assert_file")["capability"]
    invoked = invoke_capability(
        tmp_path,
        "assert_file",
        {
            "path": "registered.json",
            "exists": True,
            "json_valid": True,
            "required_keys": ["probe"],
        },
    )

    assert invoked["ok"] is True
    assert invoked["capability_version"] == inspected["version"]
    assert invoked["implementation_sha256"] == inspected["implementation_sha256"]
    assert invoked["durable_result_fields"] == inspected["durable_result_fields"]


def test_registered_invoke_rejects_unknown_input_fields(tmp_path: Path) -> None:
    with pytest.raises(CapabilityUsageError, match="unknown assert_file input field"):
        invoke_capability(
            tmp_path,
            "assert_file",
            {"path": "result.json", "invented": True},
        )


@pytest.mark.parametrize(
    ("argv", "expected_operation"),
    [
        (["list"], "list"),
        (["inspect", "assert_file"], "inspect"),
    ],
)
def test_registry_cli_emits_machine_readable_discovery(
    argv: list[str], expected_operation: str, capsys
) -> None:
    exit_code = main(argv)

    assert exit_code == 0
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    payload = json.loads(output[0])
    assert payload["codex_room_registry"] == 1
    assert payload["operation"] == expected_operation


def test_registry_cli_invokes_by_manifest_id(tmp_path: Path, monkeypatch, capsys) -> None:
    artifact = tmp_path / "probe.json"
    artifact.write_text('{"probe": "P4.2"}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "invoke",
            "assert_file",
            "--input-json",
            json.dumps(
                {
                    "path": "probe.json",
                    "exists": True,
                    "json_valid": True,
                    "required_keys": ["probe"],
                }
            ),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["codex_room_capability"] == 1
    assert payload["capability"] == "assert_file"
    assert payload["capability_version"] == "1"
    assert len(payload["implementation_sha256"]) == 64
    assert payload["durable_result_fields"] == ["subject", "checks"]
    assert payload["ok"] is True

def test_custom_authoring_guide_is_bounded_and_encodes_host_pending_registration() -> None:
    guide = capabilities.custom_capability_authoring_guide()

    assert guide["codex_room_registry"] == 1
    assert guide["operation"] == "authoring"
    assert guide["schema_version"] == 1
    assert guide["draft_root"] == ".codex-room/capability-drafts/<id>"
    assert guide["package_v1"]["files"] == ["manifest.json", "capability.py"]
    assert guide["package_v1"]["fixed_values"]["scope"] == "lineage"
    assert guide["package_v1"]["fixed_values"]["runtime"] == {
        "kind": "python",
        "entrypoint": "capability.py",
        "protocol": "stdio-json-v1",
    }
    assert guide["verification_cases_v1"]["format"] == "JSON array with 1 to 16 cases"
    assert "verification_passed" not in json.dumps(guide)
    assert "not active until that agent turn settles" in guide["settlement"]
    assert "per-capability OS sandbox" in guide["permission_enforcement"]


def test_cli_authoring_emits_one_machine_readable_reference(capsys) -> None:
    assert main(["authoring"]) == 0

    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    payload = json.loads(output[0])
    assert payload["operation"] == "authoring"
    assert payload["schema_version"] == 1
    assert payload["register_command"].startswith("codex-room-cap register ")

def test_registry_cli_invokes_from_workspace_input_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    artifact = tmp_path / "probe.json"
    artifact.write_text('{"probe":"P4.4e"}', encoding="utf-8")
    input_file = tmp_path / "invoke-input.json"
    input_file.write_text(
        json.dumps(
            {
                "path": "probe.json",
                "exists": True,
                "json_valid": True,
                "required_keys": ["probe"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "invoke",
            "assert_file",
            "--input-file",
            "invoke-input.json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["capability"] == "assert_file"
    assert payload["ok"] is True


def test_registry_cli_rejects_non_object_or_escaping_input_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    outside = tmp_path.parent / "outside-invoke-input.json"
    outside.write_text('{"path":"probe.json"}', encoding="utf-8")
    local = tmp_path / "array.json"
    local.write_text("[]", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main(["invoke", "assert_file", "--input-file", "../outside-invoke-input.json"]) == 2
    escaped = json.loads(capsys.readouterr().out.strip())
    assert escaped["error"]["code"] == "invalid_request"
    assert "workspace" in escaped["error"]["message"]

    assert main(["invoke", "assert_file", "--input-file", "array.json"]) == 2
    non_object = json.loads(capsys.readouterr().out.strip())
    assert non_object["error"]["code"] == "invalid_request"
    assert "JSON object" in non_object["error"]["message"]

def test_source_cli_avoids_json_request_files_and_batches_workspace_reads(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "a.txt").write_text("ALPHA\nBETA\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("BETA\nGAMMA\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main(
        [
            "source",
            "search-many",
            "workspace",
            ".",
            "--query",
            "ALPHA",
            "--query",
            "BETA",
        ]
    ) == 0
    searched = json.loads(capsys.readouterr().out.strip())
    assert searched["capability"] == "inspect_source"
    assert searched["capability_version"] == "3"
    assert searched["evidence"]["operation"] == "search_many"
    assert searched["evidence"]["query_count"] == 2
    assert [item["query"] for item in searched["results"]] == ["ALPHA", "BETA"]

    assert main(
        [
            "source",
            "read-many",
            "workspace",
            "--read",
            "a.txt",
            "1",
            "1",
            "--read",
            "b.txt",
            "2",
            "1",
        ]
    ) == 0
    read = json.loads(capsys.readouterr().out.strip())
    assert read["capability"] == "inspect_source"
    assert read["evidence"]["operation"] == "read_many"
    assert [item["content"] for item in read["reads"]] == ["ALPHA\n", "GAMMA\n"]
    assert not list(tmp_path.glob("*invoke*.json"))


def test_inspect_source_manifest_advertises_direct_source_cli() -> None:
    inspected = inspect_capability("inspect_source")["capability"]

    assert inspected["version"] == "3"
    assert inspected["invocation"]["source_cli"] == "codex-room-cap source --help"
    assert inspected["verification"] == {"status": "verified", "evidence": ["E-078", "E-081", "E-097"]}

def test_source_cli_failure_is_attributed_to_inspect_source(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(
        ["source", "search", "workspace", ".", "--query", ""]
    ) == 2
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["codex_room_capability"] == 1
    assert payload["capability"] == "inspect_source"
    assert payload["ok"] is False

def test_source_bundle_cli_accepts_compact_plan_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    artifact = tmp_path / "notes.txt"
    artifact.write_text("alpha\nbeta\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    plan = {
        "requests": [
            {
                "label": "notes",
                "request": {
                    "operation": "read",
                    "source": "workspace",
                    "path": "notes.txt",
                    "start_line": 1,
                    "max_lines": 2,
                },
            }
        ]
    }

    exit_code = main(
        ["source", "bundle", "--plan-json", json.dumps(plan)]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["capability"] == "inspect_source"
    assert payload["capability_version"] == "3"
    assert payload["items"][0]["label"] == "notes"
    assert payload["items"][0]["content"] == "alpha\nbeta\n"


def test_source_bundle_cli_accepts_workspace_plan_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "notes.txt").write_text("canary\n", encoding="utf-8")
    plan = {
        "requests": [
            {
                "label": "notes",
                "request": {
                    "operation": "read",
                    "source": "workspace",
                    "path": "notes.txt",
                },
            }
        ]
    }
    (tmp_path / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["source", "bundle", "--plan-file", "plan.json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["items"][0]["content"] == "canary\n"

