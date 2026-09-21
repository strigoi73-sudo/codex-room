from __future__ import annotations

from codex_room import pbm, pbm_v5_c_only


def test_c_only_condition_preserves_frozen_user_mission() -> None:
    payload = pbm_v5_c_only._room_payload("pbm-v5-c-only-test")

    assert payload["topic"] == pbm_v5_c_only.PASTE
    assert payload["starting_agent"] == "agent_c"
    assert payload["required_contributors"] == []
    assert payload["agent_c_instructions"] == pbm_v5_c_only.C_ONLY_PERSONALITY
    assert "must not delegate benchmark work to Agent A or Agent B" in (
        payload["agent_c_instructions"]
    )


def test_c_only_violation_detects_a_or_b_delegation() -> None:
    round_item = {
        "events": [
            {
                "event_type": "agent_message",
                "source": "agent_c",
                "metadata": {
                    "transaction_action": "DELEGATE",
                    "delegations": [
                        {"target": "agent_a", "instruction": "do work"},
                        {"target": "agent_b", "instruction": "do work"},
                    ],
                },
            }
        ]
    }

    assert pbm_v5_c_only._c_only_violations(round_item) == [
        "Agent C delegated to agent_a during the C-only condition",
        "Agent C delegated to agent_b during the C-only condition",
    ]


def test_c_only_violation_detects_non_c_execution() -> None:
    round_item = {
        "events": [
            {
                "event_type": "execution_economics",
                "source": "agent_a",
                "metadata": {"usage_delta_status": "first_execution"},
            },
            {
                "event_type": "execution_economics",
                "source": "agent_c",
                "metadata": {"usage_delta_status": "first_execution"},
            },
        ]
    }

    assert pbm_v5_c_only._c_only_violations(round_item) == [
        "agent_a executed during the C-only condition"
    ]


def test_c_only_allows_agent_c_self_delegation() -> None:
    round_item = {
        "events": [
            {
                "event_type": "agent_message",
                "source": "agent_c",
                "metadata": {
                    "transaction_action": "DELEGATE",
                    "delegations": [
                        {"target": "agent_c", "instruction": "continue in fresh C assignment"}
                    ],
                },
            },
            {
                "event_type": "execution_economics",
                "source": "agent_c",
                "metadata": {"usage_delta_status": "computed"},
            },
        ]
    }

    assert pbm_v5_c_only._c_only_violations(round_item) == []


def test_controlled_variant_does_not_change_canonical_v5_fingerprint() -> None:
    assert (
        pbm.benchmark_fingerprint("v5")
        == pbm_v5_c_only.EXPECTED_BENCHMARK_FINGERPRINT
    )


def test_variant_fingerprint_is_distinct_from_benchmark_fingerprint() -> None:
    variant = pbm_v5_c_only._variant_fingerprint()

    assert len(variant) == 64
    assert variant != pbm_v5_c_only.EXPECTED_BENCHMARK_FINGERPRINT


def test_clear_active_pointer_after_terminal_state(tmp_path, monkeypatch) -> None:
    pointer = tmp_path / "active.json"
    pbm_v5_c_only._write_json(pointer, {"run_id": "run-1"})
    monkeypatch.setattr(pbm_v5_c_only, "ACTIVE_POINTER", pointer)

    pbm_v5_c_only._clear_active_if("run-1")

    assert not pointer.exists()
