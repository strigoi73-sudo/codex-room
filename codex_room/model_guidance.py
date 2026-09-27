from __future__ import annotations

from collections.abc import Mapping


MODEL_FAMILY_GUIDANCE: dict[str, str] = {
    "gpt-5.6-luna": (
        "Luna — Fast and economical. Well suited to focused, repetitive, "
        "and clearly bounded work."
    ),
    "gpt-5.6-terra": (
        "Terra — Balanced capability, speed, and cost. Well suited to "
        "general-purpose reasoning and everyday professional work."
    ),
    "gpt-5.6-sol": (
        "Sol — High-capability model for complex professional work, including "
        "demanding coding, research, analysis, and multi-step reasoning."
    ),
    "gpt-6-astra": (
        "Astra — Highest-capability model for especially difficult, ambiguous, "
        "or demanding end-to-end work."
    ),
}

REASONING_EFFORT_GUIDANCE: dict[str, str] = {
    "low": "Low — Efficient reasoning for straightforward work.",
    "medium": "Medium — Balanced reasoning for typical substantive work.",
    "high": "High — Deeper reasoning for difficult work.",
    "xhigh": (
        "XHigh — Greater reasoning investment for unusually demanding work."
    ),
    "max": "Max — Maximum reasoning investment for the most demanding work.",
}


def render_model_selection_guide(
    catalog: Mapping[str, tuple[str, str]],
) -> str:
    """Render compact, non-authoritative guidance for configurations in scope."""
    known_models: set[str] = set()
    known_efforts: set[str] = set()
    has_unlisted = False

    for model, effort in catalog.values():
        if model in MODEL_FAMILY_GUIDANCE:
            known_models.add(model)
        else:
            has_unlisted = True
        if effort in REASONING_EFFORT_GUIDANCE:
            known_efforts.add(effort)
        else:
            has_unlisted = True

    lines = [
        "<model_selection_guide>",
        "MODEL SELECTION GUIDE — ADVISORY ONLY",
        (
            "These descriptions are general background information, not routing "
            "rules, rankings, thresholds, or required escalation paths. Use your "
            "own judgment when allocating cognition."
        ),
    ]

    if known_models:
        lines.append("Model families:")
        lines.extend(
            f"- {description}"
            for model, description in MODEL_FAMILY_GUIDANCE.items()
            if model in known_models
        )

    if known_efforts:
        lines.append("Reasoning effort:")
        lines.extend(
            f"- {description}"
            for effort, description in REASONING_EFFORT_GUIDANCE.items()
            if effort in known_efforts
        )

    if has_unlisted:
        lines.append(
            "Unlisted native configurations remain selectable when CORE's "
            "authoritative model policy permits them; absence of advisory guidance "
            "is not evidence for or against selecting them."
        )

    lines.extend(
        [
            (
                "This guide changes no availability, authorization, validation, "
                "or execution rule."
            ),
            "</model_selection_guide>",
        ]
    )
    return "\n".join(lines)
