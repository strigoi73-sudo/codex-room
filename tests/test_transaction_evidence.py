from __future__ import annotations

import asyncio
import json

import pytest

from codex_room.db import Database
from codex_room.models import (
    CreateRoomRequest,
    RoomStatus,
    SourceEvidenceRequest,
    TransactionAction,
    TransactionDecision,
)
from codex_room.orchestrator import RoomRuntime
from codex_room.transaction_evidence import plan_source_evidence

from .fakes import FakeAgentAdapter, wait_until


@pytest.fixture
async def evidence_runtime_factory(tmp_path):
    runtimes: list[RoomRuntime] = []

    async def make(adapter: FakeAgentAdapter, name: str = "evidence.db") -> RoomRuntime:
        runtime = RoomRuntime(Database(tmp_path / name), adapter, tmp_path / "data")
        await runtime.initialize()
        runtimes.append(runtime)
        return runtime

    yield make
    await asyncio.gather(*(runtime.close() for runtime in runtimes), return_exceptions=True)


def _request(operation: str, path: str, **kwargs) -> SourceEvidenceRequest:
    return SourceEvidenceRequest(
        operation=operation,
        source=kwargs.pop("source", "workspace"),
        room_id=kwargs.pop("room_id", None),
        path=path,
        **kwargs,
    )


def test_source_evidence_planner_selects_existing_primitives_mechanically() -> None:
    single = plan_source_evidence([_request("READ", "one.txt")])
    assert single["operation"] == "read"

    reads = plan_source_evidence(
        [_request("READ", "one.txt"), _request("READ", "two.txt")]
    )
    assert reads["operation"] == "read_many"
    assert [item["path"] for item in reads["reads"]] == ["one.txt", "two.txt"]

    searches = plan_source_evidence(
        [
            _request("SEARCH", ".", query="alpha", max_matches=10),
            _request("SEARCH", ".", query="beta", max_matches=20),
        ]
    )
    assert searches["operation"] == "bundle"
    assert [item["request"]["query"] for item in searches["requests"]] == [
        "alpha",
        "beta",
    ]

    oversized_reads = plan_source_evidence(
        [
            _request("READ", "one.txt", max_bytes=100_000),
            _request("READ", "two.txt", max_bytes=100_000),
        ]
    )
    assert oversized_reads["operation"] == "bundle"

    mixed = plan_source_evidence(
        [
            _request("FIND", ".", include_globs=["*.txt"]),
            _request("READ", "one.txt"),
        ]
    )
    assert mixed["operation"] == "bundle"
    assert [item["request"]["operation"] for item in mixed["requests"]] == [
        "find",
        "read",
    ]


@pytest.mark.asyncio
async def test_transaction_evidence_requeues_same_assignment_with_transient_content(
    evidence_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.EVIDENCE,
                evidence_requests=[
                    _request("READ", "one.txt"),
                    _request("READ", "two.txt"),
                ],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Evidence integrated.",
            ),
        ]
    )

    runtime = await evidence_runtime_factory(adapter)
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Read two known source files.",
            work_model_version=2,
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    workspace = runtime.workspace(room_id)
    (workspace / "one.txt").write_text("alpha evidence\n", encoding="utf-8")
    (workspace / "two.txt").write_text("beta evidence\n", encoding="utf-8")

    await runtime.start_round(room_id, snapshot["active_round_id"])

    async def finished() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.FINISHED)

    await wait_until(finished)

    assert len(adapter.calls["agent_c"]) == 2
    first_prompt = adapter.calls["agent_c"][0]["prompt"]
    assert "<deterministic_evidence>" in first_prompt
    assert "<deterministic_capabilities>" in first_prompt
    assert "codex-room-cap invoke CAPABILITY_ID" in first_prompt
    assert "codex-room-cap source" not in first_prompt
    resumed = adapter.calls["agent_c"][1]["prompt"]
    assert "<resolved_source_evidence>" in resumed
    assert "alpha evidence" in resumed
    assert "beta evidence" in resumed

    async with runtime.db.connect() as db:
        row = await runtime.db._fetchone(
            db,
            "SELECT * FROM assignment_evidence ORDER BY created_at LIMIT 1",
            (),
        )
    assert row is not None
    assert row["state"] == "consumed"
    assert row["transient_result_json"] is None
    assert json.loads(row["execution_plan_json"])["operation"] == "read_many"
    durable = json.loads(row["durable_result_json"])
    assert durable["ok"] is True
    assert durable["evidence"]["operation"] == "read_many"

    exported = await runtime.db.snapshot(room_id, event_limit=None)
    assert exported is not None
    assignment = exported["active_round"]["transaction_state"]["tasks"][0]["assignments"][0]
    assert assignment["evidence"][0]["execution_plan"]["operation"] == "read_many"
    assert assignment["evidence"][0]["durable_result"]["ok"] is True
    assert "transient_result_json" not in assignment["evidence"][0]

    evidence_events = [
        event
        for event in exported["events"]
        if event.get("metadata", {}).get("type") == "deterministic_source_evidence"
    ]
    assert len(evidence_events) == 1
    assert evidence_events[0]["metadata"]["plan_operation"] == "read_many"


@pytest.mark.asyncio
async def test_pending_transaction_evidence_recovers_after_restart(
    evidence_runtime_factory,
    monkeypatch,
):
    import codex_room.orchestrator as orchestrator_module

    real_execute = orchestrator_module.execute_source_evidence

    def crash_before_execution(*_args, **_kwargs):
        raise RuntimeError("simulated host crash before evidence execution")

    monkeypatch.setattr(
        orchestrator_module, "execute_source_evidence", crash_before_execution
    )
    first_adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    first_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.EVIDENCE,
            evidence_requests=[_request("READ", "recover.txt")],
        )
    )
    first = await evidence_runtime_factory(first_adapter, "restart-evidence.db")
    snapshot = await first.create_room(
        CreateRoomRequest(
            topic="Recover pending source evidence.",
            work_model_version=2,
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    (first.workspace(room_id) / "recover.txt").write_text(
        "restart-safe evidence\n", encoding="utf-8"
    )
    await first.start_round(room_id, snapshot["active_round_id"])

    async def evidence_pending() -> bool:
        async with first.db.connect() as db:
            row = await first.db._fetchone(
                db,
                "SELECT state FROM assignment_evidence ORDER BY created_at LIMIT 1",
                (),
            )
        return bool(row and row["state"] == "pending")

    await wait_until(evidence_pending)
    await first.close()

    monkeypatch.setattr(
        orchestrator_module, "execute_source_evidence", real_execute
    )
    second_adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    second_adapter.decisions["agent_c"].append(
        TransactionDecision(
            action=TransactionAction.COMPLETE,
            message="Recovered evidence integrated.",
        )
    )
    second = await evidence_runtime_factory(second_adapter, "restart-evidence.db")

    async def finished() -> bool:
        room = await second.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.FINISHED)

    await wait_until(finished)
    assert len(second_adapter.calls["agent_c"]) == 1
    assert "restart-safe evidence" in second_adapter.calls["agent_c"][0]["prompt"]

    async with second.db.connect() as db:
        row = await second.db._fetchone(
            db,
            "SELECT * FROM assignment_evidence ORDER BY created_at LIMIT 1",
            (),
        )
    assert row is not None
    assert row["state"] == "consumed"
    assert row["transient_result_json"] is None
