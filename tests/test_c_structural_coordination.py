from codex_room.personalities import default_agent_instructions


def test_c_structural_role_sequences_dependencies_and_allocates_context_aware_fallback() -> None:
    c_instructions = default_agent_instructions("Agent C", "Agent A")
    a_instructions = default_agent_instructions("Agent A", "Agent C")
    b_instructions = default_agent_instructions("Agent B", "Agent C")

    c_only_expectations = (
        "Before delegating multiple assignments concurrently, consider both dependency and interaction value",
        "whether seeing another participant's contribution before reasoning would materially improve the work",
        "Parallelize when independent cognition is valuable",
        "Sequence work when useful completion depends on a prerequisite artifact, evidence, or result",
        "when one participant's contribution should become substantive input to another participant's reasoning",
        "This includes rebuttal, critique, cross-examination responses, negotiation, iterative refinement, and dialogue where responsiveness is part of the objective",
        "When sequence matters and the principal has specified an order, follow that order",
        "without assigning permanent precedence to A or B",
        "Do not serialize independent work merely as a workaround for possible context-visibility defects",
        "concurrency remains appropriate when it adds value and the work is genuinely independent",
        "do not treat verification of an artifact as concurrent with creation or modification of that same artifact",
        "or when fallback work reaches C because another assignment failed or settled without producing it",
        "C should normally place substantial tool-heavy execution in a fresh bounded peer assignment rather than perform it itself",
        "This applies whether C is acting in its root coordination assignment or in a child assignment created by a peer",
        "Prefer the capable assignment with the least unnecessary accumulated context",
        "C may still execute directly when the work is demonstrably small in expected execution and context cost",
        "Do not infer that model execution will be cheap merely because the code or file change appears small",
        "Correctness, safety, continuity, and reliability remain controlling constraints",
    )

    for expectation in c_only_expectations:
        assert expectation in c_instructions
        assert expectation not in a_instructions
        assert expectation not in b_instructions

    assert "consider another bounded peer assignment" not in c_instructions
    assert "C's own coordination assignment" not in c_instructions


def test_c_structural_refinement_preserves_peer_judgment_and_selective_invocation() -> None:
    c_instructions = default_agent_instructions("Agent C", "Agent A")

    assert "Every additional peer invocation must be expected to earn its cognitive and token cost" in c_instructions
    assert "Use the fewest peers that can add sufficient value" in c_instructions
    assert "they do not authorize C to dictate a conclusion" in c_instructions
    assert "A and B may challenge the framing" in c_instructions
    assert "This coordination responsibility gives Agent C no superior judgment or authority" in c_instructions
