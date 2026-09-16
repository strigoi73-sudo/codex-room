from __future__ import annotations

import json

import pytest

from codex_room.evidence import execute_source_evidence
from codex_room.models import (
    TRANSACTION_DECISION_SCHEMA,
    EvidenceRequest,
    TransactionAction,
    TransactionDecision,
)


def _read(path: str) -> dict:
    return {
        "operation": "READ",
        "source": "workspace",
        "room_id": None,
        "path": path,
        "query": None,
        "patterns": None,
        "start_line": None,
        "max_lines": None,
        "max_results": None,
    }


def _search(query: str, path: str = ".") -> dict:
    return {
        "operation": "SEARCH",
        "source": "workspace",
        "room_id": None,
        "path": path,
        "query": query,
        "patterns": None,
        "start_line": None,
        "max_lines": None,
        "max_results": None,
    }


def _find(pattern: str = "*.py") -> dict:
    return {
        "operation": "FIND",
        "source": "workspace",
        "room_id": None,
        "path": ".",
        "query": None,
        "patterns": [pattern],
        "start_line": None,
        "max_lines": None,
        "max_results": None,
    }


def test_semantic_evidence_selects_direct_and_homogeneous_plans(tmp_path):
    (tmp_path / "one.txt").write_text("alpha\nbeta\n", encoding="utf-8")
    (tmp_path / "two.txt").write_text("beta\ngamma\n", encoding="utf-8")

    direct = execute_source_evidence(tmp_path, [_read("one.txt")])
    assert direct["ok"] is True
    assert direct["strategy"] == "read"
    assert direct["payload"]["items"][0]["content"] == "alpha\nbeta\n"

    reads = execute_source_evidence(
        tmp_path, [_read("one.txt"), _read("two.txt")]
    )
    assert reads["ok"] is True
    assert reads["strategy"] == "read_many"
    assert [item["path"] for item in reads["payload"]["items"]] == [
        "one.txt",
        "two.txt",
    ]

    searches = execute_source_evidence(
        tmp_path, [_search("alpha"), _search("gamma")]
    )
    assert searches["ok"] is True
    assert searches["strategy"] == "search_many"
    assert len(searches["payload"]["items"]) == 2
    assert searches["payload"]["items"][0]["matches"][0]["path"] == "one.txt"
    assert searches["payload"]["items"][1]["matches"][0]["path"] == "two.txt"


def test_semantic_evidence_uses_bundle_for_heterogeneous_known_requests(tmp_path):
    (tmp_path / "evidence.txt").write_text("known fact\n", encoding="utf-8")

    result = execute_source_evidence(
        tmp_path, [_read("evidence.txt"), _find("*.txt")]
    )

    assert result["ok"] is True
    assert result["strategy"] == "bundle"
    assert "strategy" not in result["payload"]
    assert result["payload"]["items"][0]["content"] == "known fact\n"
    assert result["payload"]["items"][1]["matches"][0]["path"] == "evidence.txt"
    assert result["durable"]["operation"] == "bundle"


def test_semantic_evidence_returns_bounded_error_instead_of_raising(tmp_path):
    result = execute_source_evidence(tmp_path, [_read("missing.txt")])

    assert result["ok"] is False
    assert result["strategy"] == "read"
    assert result["payload"]["items"] == []
    assert "path is unavailable" in result["payload"]["error"]
    assert result["durable"]["error"] == result["payload"]["error"]


def test_evidence_request_validation_and_transaction_exclusivity():
    with pytest.raises(ValueError, match="SEARCH requires query"):
        EvidenceRequest(
            operation="SEARCH",
            source="workspace",
            path=".",
        )
    with pytest.raises(ValueError, match="room source requires room_id"):
        EvidenceRequest(
            operation="FIND",
            source="room",
            path=".",
        )
    with pytest.raises(ValueError, match="READ accepts path/start_line/max_lines only"):
        EvidenceRequest(
            operation="READ",
            source="workspace",
            path="one.txt",
            query="not allowed",
        )

    decision = TransactionDecision(
        action=TransactionAction.EVIDENCE,
        evidence_requests=[
            EvidenceRequest(
                operation="READ",
                source="workspace",
                path="one.txt",
            )
        ],
    )
    assert decision.action == TransactionAction.EVIDENCE

    with pytest.raises(ValueError, match="delegations is valid only for DELEGATE"):
        TransactionDecision(
            action=TransactionAction.EVIDENCE,
            delegations=[
                {
                    "target": "agent_a",
                    "instruction": "Do something else",
                    "config": None,
                }
            ],
            evidence_requests=[
                EvidenceRequest(
                    operation="READ",
                    source="workspace",
                    path="one.txt",
                )
            ],
        )


def test_transaction_schema_exposes_semantic_evidence_not_transport_vocabulary():
    encoded = json.dumps(TRANSACTION_DECISION_SCHEMA, sort_keys=True)

    assert '"EVIDENCE"' in encoded
    assert '"READ"' in encoded
    assert '"SEARCH"' in encoded
    assert '"FIND"' in encoded
    assert "read_many" not in encoded
    assert "search_many" not in encoded
    assert "bundle" not in encoded
    assert "codex-room-cap" not in encoded
