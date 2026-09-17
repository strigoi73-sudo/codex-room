from __future__ import annotations

import asyncio
from collections import deque
import json

import pytest

from codex_room.agent import AgentDecisionValidationError
from codex_room.db import Database
from codex_room.models import (
    CreateRoomRequest,
    RoomStatus,
    TRANSACTION_DECISION_SCHEMA,
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


def test_transaction_decision_schema_matches_runtime_bounds() -> None:
    evidence_schema = TRANSACTION_DECISION_SCHEMA["properties"]["evidence_requests"]
    variants = evidence_schema["anyOf"][0]["items"]["anyOf"]

    assert len(variants) == 3
    for variant in variants:
        path_schema = variant["properties"]["path"]
        assert path_schema["minLength"] == 1
        assert path_schema["maxLength"] == 4096

    read = variants[0]["properties"]
    assert read["start_line"] == {"type": "integer", "minimum": 1}
    assert read["max_lines"] == {"type": "integer", "minimum": 1, "maximum": 1000}
    assert read["max_bytes"] == {
        "type": "integer",
        "minimum": 1,
        "maximum": 128 * 1024,
    }

    search = variants[1]["properties"]
    assert search["max_files"] == {"type": "integer", "minimum": 1, "maximum": 200}
    assert search["max_matches"] == {"type": "integer", "minimum": 1, "maximum": 100}

    find = variants[2]["properties"]
    assert find["max_results"] == {"type": "integer", "minimum": 1, "maximum": 200}

    delegation = TRANSACTION_DECISION_SCHEMA["properties"]["delegations"]["anyOf"][0]
    instruction = delegation["items"]["properties"]["instruction"]
    assert instruction == {"type": "string", "minLength": 1, "maxLength": 50_000}

    history = TRANSACTION_DECISION_SCHEMA["properties"]["history_requests"]["anyOf"][0]
    assert history["minItems"] == 1
    assert history["maxItems"] == 4
    for variant in history["items"]["anyOf"]:
        assert variant["properties"]["max_results"] == {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
        }


def test_history_runtime_accepts_four_individually_bounded_requests() -> None:
    decision = TransactionDecision(
        action=TransactionAction.HISTORY,
        history_requests=[
            {"operation": "RECENT", "query": None, "agent": key, "max_results": 10}
            for key in ("agent_a", "agent_b", "agent_c", None)
        ],
    )
    assert len(decision.history_requests or []) == 4


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
    assert "Every request path must be non-empty" in first_prompt
    assert "relative to the selected source" in first_prompt
    assert "never send an absolute filesystem path" in first_prompt
    assert "use '.' when the selected shared-workspace root itself is the target" in first_prompt
    assert "do not use an empty path or '.' as the CORE root" in first_prompt
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
    first_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        turn_id_namespace="before_restart",
    )
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
    first_room = await first.db.get_room(room_id)
    assert first_room is not None
    assert first_room["status"] == RoomStatus.RUNNING
    assert await first.db.has_active_transaction_task(
        room_id, snapshot["active_round_id"]
    )
    await first.close()

    monkeypatch.setattr(
        orchestrator_module, "execute_source_evidence", real_execute
    )
    second_adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        turn_id_namespace="after_restart",
    )
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

    await wait_until(lambda: len(second_adapter.completed_calls["agent_c"]) == 1)

    async def evidence_consumed() -> bool:
        async with second.db.connect() as db:
            row = await second.db._fetchone(
                db,
                "SELECT state FROM assignment_evidence ORDER BY created_at LIMIT 1",
                (),
            )
        return bool(row and row["state"] == "consumed")

    await wait_until(evidence_consumed)
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


@pytest.mark.asyncio
async def test_retry_feedback_survives_claim_recovery_until_valid_decision(
    evidence_runtime_factory,
):
    adapter = FakeAgentAdapter({"agent_a": [], "agent_b": [], "agent_c": []})
    runtime = await evidence_runtime_factory(adapter, "retry-feedback-recovery.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Preserve retry feedback across claim recovery.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    round_id = snapshot["active_round_id"]
    await runtime.db.start_round(room_id, round_id)
    origin = await runtime.db.create_event(
        room_id,
        "observer_message",
        "observer",
        "agent_c",
        "Create one explicit transaction assignment.",
        discussion_id=round_id,
        round_id=round_id,
    )
    created = await runtime.db.create_transaction_task(
        room_id,
        round_id,
        origin["id"],
        "agent_c",
        required_contributors=["agent_c"],
    )
    assignment_id = created["assignment_ids"][0]

    first = await runtime.db.claim_next_assignment(
        room_id,
        "agent_c",
        worker_generation=0,
        model="gpt-5.6-terra",
        reasoning_effort="high",
    )
    assert first is not None
    assert await runtime.db.bind_execution_turn(
        first["batch_id"],
        "thr_retry_feedback",
        "turn_retry_feedback_1",
        0,
    )
    failure_detail = (
        "evidence_requests.0.path String should have at least 1 character."
    )
    failed = await runtime.db.fail_transaction_assignment(
        room_id,
        round_id,
        first["batch_id"],
        failure_detail,
        retryable=True,
    )
    assert failed["retried"] is True

    retry = await runtime.db.claim_next_assignment(
        room_id,
        "agent_c",
        worker_generation=0,
        model="gpt-5.6-terra",
        reasoning_effort="high",
    )
    assert retry is not None
    assert retry["retry_feedback"] == failure_detail

    recovered = await runtime.db.claim_next_assignment(
        room_id,
        "agent_c",
        worker_generation=0,
        model="gpt-5.6-terra",
        reasoning_effort="high",
    )
    assert recovered is not None
    assert recovered["recovered"] is True
    assert recovered["batch_id"] == retry["batch_id"]
    assert recovered["retry_feedback"] == failure_detail

    assert await runtime.db.bind_execution_turn(
        retry["batch_id"],
        "thr_retry_feedback",
        "turn_retry_feedback_2",
        0,
    )
    valid = TransactionDecision(
        action=TransactionAction.COMPLETE,
        message="Valid retry decision.",
    )
    assert await runtime.db.record_execution_result(
        retry["batch_id"],
        valid.model_dump(mode="json"),
        {"total_tokens": 10},
        [],
        "notification",
    )

    async with runtime.db.connect() as db:
        assignment = await runtime.db._fetchone(
            db,
            "SELECT resolution_reason FROM assignments WHERE id=?",
            (assignment_id,),
        )
    assert assignment is not None
    assert assignment["resolution_reason"] is None


@pytest.mark.asyncio
async def test_invalid_transaction_decision_retry_gets_feedback_and_keeps_telemetry(
    evidence_runtime_factory,
):
    invalid = AgentDecisionValidationError(
        (
            "Codex returned invalid Room decision JSON. Validation error: "
            "evidence_requests.0.path String should have at least 1 character."
        ),
        usage={
            "input_tokens": 20,
            "cached_input_tokens": 0,
            "output_tokens": 5,
            "reasoning_output_tokens": 1,
            "total_tokens": 25,
        },
        activity=[],
        thread_id="unused-by-fake",
        turn_id="unused-by-fake",
        completion_source="notification",
    )
    adapter = FakeAgentAdapter(
        {"agent_a": [], "agent_b": [], "agent_c": []},
        failures={"agent_c": [invalid]},
        usages={
            "agent_c": [
                {
                    "input_tokens": 40,
                    "cached_input_tokens": 20,
                    "output_tokens": 5,
                    "reasoning_output_tokens": 1,
                    "total_tokens": 45,
                },
                {
                    "input_tokens": 60,
                    "cached_input_tokens": 40,
                    "output_tokens": 5,
                    "reasoning_output_tokens": 1,
                    "total_tokens": 65,
                },
            ]
        },
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.EVIDENCE,
                evidence_requests=[_request("READ", "one.txt")],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Recovered after valid evidence.",
            ),
        ]
    )

    runtime = await evidence_runtime_factory(adapter, "invalid-decision-retry.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Recover from one invalid transaction decision.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    (runtime.workspace(room_id) / "one.txt").write_text(
        "recovered evidence\n", encoding="utf-8"
    )

    await runtime.start_round(room_id, snapshot["active_round_id"])

    async def finished() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.FINISHED)

    await wait_until(finished)

    assert len(adapter.calls["agent_c"]) == 3
    first_prompt = adapter.calls["agent_c"][0]["prompt"]
    retry_prompt = adapter.calls["agent_c"][1]["prompt"]
    evidence_resume_prompt = adapter.calls["agent_c"][2]["prompt"]

    assert "<retry_feedback>" not in first_prompt
    assert "<retry_feedback>" in retry_prompt
    assert "evidence_requests.0.path" in retry_prompt
    assert "<retry_feedback>" not in evidence_resume_prompt
    assert "<resolved_source_evidence>" in evidence_resume_prompt
    assert "recovered evidence" in evidence_resume_prompt

    async with runtime.db.connect() as db:
        rows = await db.execute_fetchall(
            """SELECT state, usage_json, activity_json, sdk_thread_id
               FROM agent_executions
               WHERE round_id=?
               ORDER BY created_at, batch_id""",
            (snapshot["active_round_id"],),
        )

    assert len(rows) == 3
    assert rows[0]["state"] == "failed"
    assert json.loads(rows[0]["usage_json"])["total_tokens"] == 25
    assert json.loads(rows[0]["activity_json"]) == []
    assert rows[0]["sdk_thread_id"] == rows[1]["sdk_thread_id"] == rows[2]["sdk_thread_id"]

    exported = await runtime.db.snapshot(room_id, event_limit=None)
    assert exported is not None
    failed_economics = [
        event
        for event in exported["events"]
        if event["event_type"] == "execution_economics"
        and event.get("metadata", {}).get("decision_validation_failed") is True
    ]
    assert len(failed_economics) == 1
    assert failed_economics[0]["metadata"]["usage_delta"]["total_tokens"] == 25

@pytest.mark.asyncio
async def test_invalid_transaction_decision_after_evidence_continuation_gets_one_retry(
    evidence_runtime_factory,
):
    invalid = AgentDecisionValidationError(
        (
            "Codex returned invalid Room decision JSON. Validation error: "
            "history_requests.0.max_results Input should be less than or equal to 10"
        ),
        usage={
            "input_tokens": 20,
            "cached_input_tokens": 0,
            "output_tokens": 5,
            "reasoning_output_tokens": 1,
            "total_tokens": 25,
        },
        activity=[],
        thread_id="unused-by-fake",
        turn_id="unused-by-fake",
        completion_source="notification",
    )

    class FailSecondTransactionalCall(FakeAgentAdapter):
        async def run_agent_on_thread(self, agent, *args, **kwargs):
            if agent["agent_key"] == "agent_c" and len(self.calls["agent_c"]) == 1:
                self.failures.setdefault("agent_c", deque()).append(invalid)
            return await super().run_agent_on_thread(agent, *args, **kwargs)

    adapter = FailSecondTransactionalCall(
        {"agent_a": [], "agent_b": [], "agent_c": []}
    )
    adapter.decisions["agent_c"].extend(
        [
            TransactionDecision(
                action=TransactionAction.EVIDENCE,
                evidence_requests=[_request("READ", "one.txt")],
            ),
            TransactionDecision(
                action=TransactionAction.COMPLETE,
                message="Recovered after post-evidence validation retry.",
            ),
        ]
    )

    runtime = await evidence_runtime_factory(adapter, "post-evidence-invalid-retry.db")
    snapshot = await runtime.create_room(
        CreateRoomRequest(
            topic="Recover one malformed decision after evidence continuation.",
            work_model_version=2,
            provider_context_mode="assignment_thread",
            auto_start=False,
        )
    )
    room_id = snapshot["id"]
    (runtime.workspace(room_id) / "one.txt").write_text(
        "post-continuation evidence\n", encoding="utf-8"
    )

    await runtime.start_round(room_id, snapshot["active_round_id"])

    async def finished() -> bool:
        room = await runtime.db.get_room(room_id)
        return bool(room and room["status"] == RoomStatus.FINISHED)

    await wait_until(finished)

    assert len(adapter.calls["agent_c"]) == 3
    evidence_prompt = adapter.calls["agent_c"][1]["prompt"]
    retry_prompt = adapter.calls["agent_c"][2]["prompt"]
    assert "<resolved_source_evidence>" in evidence_prompt
    assert "post-continuation evidence" in evidence_prompt
    assert "<retry_feedback>" in retry_prompt
    assert "history_requests.0.max_results" in retry_prompt
    assert "<resolved_source_evidence>" in retry_prompt

    async with runtime.db.connect() as db:
        executions = await db.execute_fetchall(
            """SELECT state FROM agent_executions
               WHERE assignment_id IS NOT NULL AND round_id=?
               ORDER BY created_at, batch_id""",
            (snapshot["active_round_id"],),
        )
        task = await runtime.db._fetchone(
            db,
            "SELECT state FROM tasks WHERE round_id=?",
            (snapshot["active_round_id"],),
        )
        assignment = await runtime.db._fetchone(
            db,
            """SELECT state, resolution_reason FROM assignments
               WHERE task_id=(SELECT id FROM tasks WHERE round_id=?)""",
            (snapshot["active_round_id"],),
        )

    assert [row["state"] for row in executions] == ["settled", "failed", "settled"]
    assert task is not None and task["state"] == "settled"
    assert assignment is not None and assignment["state"] == "completed"
    assert assignment["resolution_reason"] is None

    exported = await runtime.db.snapshot(room_id, event_limit=None)
    assert exported is not None
    retry_errors = [
        event
        for event in exported["events"]
        if event["event_type"] == "agent_error"
        and event.get("metadata", {}).get("will_retry") is True
    ]
    assert len(retry_errors) == 1
