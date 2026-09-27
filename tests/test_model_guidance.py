from __future__ import annotations

from codex_room.model_guidance import render_model_selection_guide
from codex_room.orchestrator import RoomRuntime


def _guide_block(prompt: str) -> str:
    return prompt.split("<model_selection_guide>", 1)[1].split(
        "</model_selection_guide>", 1
    )[0]


def test_model_selection_guide_is_compact_and_deduplicates_families() -> None:
    guide = render_model_selection_guide(
        {
            "luna-low": ("gpt-5.6-luna", "low"),
            "luna-high": ("gpt-5.6-luna", "high"),
            "astra-medium": ("gpt-6-astra", "medium"),
        }
    )

    assert guide.count("Luna —") == 1
    assert guide.count("Astra —") == 1
    assert "Terra —" not in guide
    assert "Sol —" not in guide
    assert "Low —" in guide
    assert "Medium —" in guide
    assert "High —" in guide
    assert "XHigh —" not in guide
    assert "Max —" not in guide
    assert "not routing rules, rankings, thresholds" in guide
    assert "changes no availability, authorization, validation" in guide


def test_unrestricted_prompt_keeps_unknown_native_config_selectable_without_invented_guidance() -> None:
    native_config = "native:gpt-test-frontier:ultra"
    prompt = RoomRuntime._transaction_execution_config_prompt(
        "agent_c",
        current_model="gpt-5.6-terra",
        current_effort="high",
        unrestricted_model_access=True,
        available_execution_configs={
            "luna-low": ("gpt-5.6-luna", "low"),
            "astra-high": ("gpt-6-astra", "high"),
            native_config: ("gpt-test-frontier", "ultra"),
        },
    )

    assert native_config in prompt
    guide = _guide_block(prompt)
    assert "Luna —" in guide
    assert "Astra —" in guide
    assert "gpt-test-frontier" not in guide
    assert "ultra" not in guide.lower()
    assert "Unlisted native configurations remain selectable" in guide


def test_default_prompt_guidance_excludes_astra_when_astra_is_unavailable() -> None:
    prompt = RoomRuntime._transaction_execution_config_prompt(
        "agent_c",
        astra_authorized=False,
    )

    guide = _guide_block(prompt)
    assert "Luna —" in guide
    assert "Terra —" in guide
    assert "Sol —" in guide
    assert "Astra —" not in guide
    assert "XHigh —" not in guide
    assert "Max —" not in guide


def test_default_prompt_guidance_includes_astra_only_when_authorized() -> None:
    prompt = RoomRuntime._transaction_execution_config_prompt(
        "agent_c",
        astra_authorized=True,
    )

    guide = _guide_block(prompt)
    assert "Astra —" in guide


def test_peer_prompt_does_not_receive_model_selection_guide() -> None:
    prompt = RoomRuntime._transaction_execution_config_prompt(
        "agent_a",
        unrestricted_model_access=True,
        available_execution_configs={
            "astra-high": ("gpt-6-astra", "high"),
        },
    )

    assert "<model_selection_guide>" not in prompt
    assert "Astra —" not in prompt
