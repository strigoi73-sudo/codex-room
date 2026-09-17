from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one match, found {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_exact_count(path: str, old: str, new: str, expected: int) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{path}: expected {expected} matches, found {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def append_once(path: str, marker: str, addition: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if marker in text:
        return
    target.write_text(text.rstrip() + "\n\n" + addition.strip() + "\n", encoding="utf-8")


def patch_models() -> None:
    path = "codex_room/models.py"
    replace_once(
        path,
        '            if sum(item.max_results for item in self.history_requests) > 20:\n'
        '                raise ValueError("HISTORY accepts at most 20 requested results per action")\n',
        "",
    )
    replace_once(
        path,
        '                            "instruction": {"type": "string"},\n',
        '                            "instruction": {\n'
        '                                "type": "string",\n'
        '                                "minLength": 1,\n'
        '                                "maxLength": 50_000,\n'
        '                            },\n',
    )
    replace_once(
        path,
        '                                    "start_line": {"type": "integer"},\n'
        '                                    "max_lines": {"type": "integer"},\n'
        '                                    "max_bytes": {"type": "integer"},\n',
        '                                    "start_line": {\n'
        '                                        "type": "integer",\n'
        '                                        "minimum": 1,\n'
        '                                    },\n'
        '                                    "max_lines": {\n'
        '                                        "type": "integer",\n'
        '                                        "minimum": 1,\n'
        '                                        "maximum": 1000,\n'
        '                                    },\n'
        '                                    "max_bytes": {\n'
        '                                        "type": "integer",\n'
        '                                        "minimum": 1,\n'
        '                                        "maximum": 128 * 1024,\n'
        '                                    },\n',
    )
    replace_once(
        path,
        '                                    "max_files": {"type": "integer"},\n'
        '                                    "max_matches": {"type": "integer"},\n',
        '                                    "max_files": {\n'
        '                                        "type": "integer",\n'
        '                                        "minimum": 1,\n'
        '                                        "maximum": 200,\n'
        '                                    },\n'
        '                                    "max_matches": {\n'
        '                                        "type": "integer",\n'
        '                                        "minimum": 1,\n'
        '                                        "maximum": 100,\n'
        '                                    },\n',
    )
    replace_once(
        path,
        '                                    "include_hidden": {"type": "boolean"},\n'
        '                                    "max_results": {"type": "integer"},\n',
        '                                    "include_hidden": {"type": "boolean"},\n'
        '                                    "max_results": {\n'
        '                                        "type": "integer",\n'
        '                                        "minimum": 1,\n'
        '                                        "maximum": 200,\n'
        '                                    },\n',
    )
    replace_exact_count(
        path,
        '                                    "max_results": {"type": "integer"},\n',
        '                                    "max_results": {\n'
        '                                        "type": "integer",\n'
        '                                        "minimum": 1,\n'
        '                                        "maximum": 10,\n'
        '                                    },\n',
        2,
    )


def patch_orchestrator() -> None:
    path = "codex_room/orchestrator.py"
    replace_once(
        path,
        '        "Use atomic READ, SEARCH, or FIND requests and include only the source, path/query, "\n'
        '        "Room ID when applicable, and useful bounds. Every request path must be non-empty. "\n'
        '        "For source=\'core\', select a maintained top-level entry: use \'codex_room\' for CORE "\n',
        '        "Use atomic READ, SEARCH, or FIND requests and include only the source, path/query, "\n'
        '        "Room ID when applicable, and useful bounds. Every request path must be non-empty, "\n'
        '        "normalized, forward-slash, and relative to the selected source; never send an "\n'
        '        "absolute filesystem path. For source=\'workspace\' or source=\'room\', use \'.\' "\n'
        '        "when the selected shared-workspace root itself is the target. "\n'
        '        "For source=\'core\', select a maintained top-level entry: use \'codex_room\' for CORE "\n',
    )
    replace_once(
        path,
        '        "specific lexical query when you know the relevant concept; optionally restrict the "\n'
        '        "request to one agent and request only as many results as are likely necessary. CORE "\n',
        '        "specific lexical query when you know the relevant concept; optionally restrict the "\n'
        '        "request to one agent and request only as many results as are likely necessary. Each "\n'
        '        "HISTORY request may ask for 1-10 results, with at most 4 requests in one action. CORE "\n',
    )


def patch_db() -> None:
    path = "codex_room/db.py"
    replace_once(
        path,
        '            attempts = await self._fetchone(\n'
        '                db,\n'
        '                "SELECT COUNT(*) AS count FROM agent_executions WHERE assignment_id=?",\n'
        '                (assignment["id"],),\n'
        '            )\n'
        '            should_retry = (\n'
        '                retryable\n'
        '                and int(attempts["count"] if attempts else 0) < 2\n'
        '                and assignment["state"] == "running"\n'
        '            )\n',
        '            prior_failures = await self._fetchone(\n'
        '                db,\n'
        '                """SELECT COUNT(*) AS count FROM agent_executions\n'
        '                   WHERE assignment_id=? AND state=\'failed\'""",\n'
        '                (assignment["id"],),\n'
        '            )\n'
        '            # One retry belongs to the assignment\'s failure budget, not its\n'
        '            # successful EVIDENCE/HISTORY continuation count.\n'
        '            should_retry = (\n'
        '                retryable\n'
        '                and int(prior_failures["count"] if prior_failures else 0) < 1\n'
        '                and assignment["state"] == "running"\n'
        '            )\n',
    )


def patch_tests() -> None:
    path = "tests/test_transaction_evidence.py"
    replace_once(path, "import asyncio\nimport json\n", "import asyncio\nfrom collections import deque\nimport json\n")

    replace_once(
        path,
        '''def test_transaction_decision_schema_requires_nonempty_evidence_paths() -> None:\n    evidence_schema = TRANSACTION_DECISION_SCHEMA["properties"]["evidence_requests"]\n    variants = evidence_schema["anyOf"][0]["items"]["anyOf"]\n\n    assert len(variants) == 3\n    for variant in variants:\n        path_schema = variant["properties"]["path"]\n        assert path_schema["minLength"] == 1\n        assert path_schema["maxLength"] == 4096\n''',
        '''def test_transaction_decision_schema_matches_runtime_bounds() -> None:\n    evidence_schema = TRANSACTION_DECISION_SCHEMA["properties"]["evidence_requests"]\n    variants = evidence_schema["anyOf"][0]["items"]["anyOf"]\n\n    assert len(variants) == 3\n    for variant in variants:\n        path_schema = variant["properties"]["path"]\n        assert path_schema["minLength"] == 1\n        assert path_schema["maxLength"] == 4096\n\n    read = variants[0]["properties"]\n    assert read["start_line"] == {"type": "integer", "minimum": 1}\n    assert read["max_lines"] == {"type": "integer", "minimum": 1, "maximum": 1000}\n    assert read["max_bytes"] == {\n        "type": "integer",\n        "minimum": 1,\n        "maximum": 128 * 1024,\n    }\n\n    search = variants[1]["properties"]\n    assert search["max_files"] == {"type": "integer", "minimum": 1, "maximum": 200}\n    assert search["max_matches"] == {"type": "integer", "minimum": 1, "maximum": 100}\n\n    find = variants[2]["properties"]\n    assert find["max_results"] == {"type": "integer", "minimum": 1, "maximum": 200}\n\n    delegation = TRANSACTION_DECISION_SCHEMA["properties"]["delegations"]["anyOf"][0]\n    instruction = delegation["items"]["properties"]["instruction"]\n    assert instruction == {"type": "string", "minLength": 1, "maxLength": 50_000}\n\n    history = TRANSACTION_DECISION_SCHEMA["properties"]["history_requests"]["anyOf"][0]\n    assert history["minItems"] == 1\n    assert history["maxItems"] == 4\n    for variant in history["items"]["anyOf"]:\n        assert variant["properties"]["max_results"] == {\n            "type": "integer",\n            "minimum": 1,\n            "maximum": 10,\n        }\n\n\ndef test_history_runtime_accepts_four_individually_bounded_requests() -> None:\n    decision = TransactionDecision(\n        action=TransactionAction.HISTORY,\n        history_requests=[\n            {"operation": "RECENT", "query": None, "agent": key, "max_results": 10}\n            for key in ("agent_a", "agent_b", "agent_c", None)\n        ],\n    )\n    assert len(decision.history_requests or []) == 4\n''',
    )

    replace_once(
        path,
        '    assert "Every request path must be non-empty" in first_prompt\n'
        '    assert "do not use an empty path or \'.\' as the CORE root" in first_prompt\n',
        '    assert "Every request path must be non-empty" in first_prompt\n'
        '    assert "relative to the selected source" in first_prompt\n'
        '    assert "never send an absolute filesystem path" in first_prompt\n'
        '    assert "use \'.\' when the selected shared-workspace root itself is the target" in first_prompt\n'
        '    assert "do not use an empty path or \'.\' as the CORE root" in first_prompt\n',
    )

    append_once(
        path,
        "test_invalid_transaction_decision_after_evidence_continuation_gets_one_retry",
        r'''@pytest.mark.asyncio
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
''',
    )


def main() -> None:
    patch_models()
    patch_orchestrator()
    patch_db()
    patch_tests()
    print("Applied bounded transaction contract/retry robustness fix.")


if __name__ == "__main__":
    main()
