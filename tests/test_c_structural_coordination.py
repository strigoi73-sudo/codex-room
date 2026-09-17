from codex_room.personalities import default_agent_instructions


def test_c_structural_role_sequences_dependencies_and_allocates_context_aware_fallback() -> None:
    c_instructions = default_agent_instructions("Agent C", "Agent A")
    a_instructions = default_agent_instructions("Agent A", "Agent C")
    b_instructions = default_agent_instructions("Agent B", "Agent C")

    c_only_expectations = (
        "Before delegating multiple assignments concurrently",
        "Parallelize genuinely independent work",
        "sequence work whose useful completion depends on a prerequisite artifact, evidence, or result",
        "do not treat verification of an artifact as concurrent with creation or modification of that same artifact",
        "consider another bounded peer assignment before taking substantial tool-heavy execution onto C's own coordination assignment",
        "Prefer a fresh peer assignment when it can perform the work reliably with materially less accumulated context",
        "C may still do work directly when it is small, urgent, inseparable from integration, or another delegation is unlikely to earn its cost",
        "favor the capable assignment with the least unnecessary accumulated context",
        "subject to correctness, safety, continuity, and reliability",
    )

    for expectation in c_only_expectations:
        assert expectation in c_instructions
        assert expectation not in a_instructions
        assert expectation not in b_instructions


def test_c_structural_refinement_preserves_peer_judgment_and_selective_invocation() -> None:
    c_instructions = default_agent_instructions("Agent C", "Agent A")

    assert "Every additional peer invocation must be expected to earn its cognitive and token cost" in c_instructions
    assert "Use the fewest peers that can add sufficient value" in c_instructions
    assert "they do not authorize C to dictate a conclusion" in c_instructions
    assert "A and B may challenge the framing" in c_instructions
    assert "This coordination responsibility gives Agent C no superior judgment or authority" in c_instructions
