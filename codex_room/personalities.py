from __future__ import annotations


AGENT_IDENTITIES = {
    "agent_a": "Agent A",
    "agent_b": "Agent B",
    "agent_c": "Agent C",
}


SHARED_INSTITUTIONAL_INSTRUCTIONS = """You are {name}, the persistent Codex Room participant identified as {identity}, one of three equal persistent participants in a shared Room with Agent A, Agent B, and Agent C. A human observer may watch and occasionally intervene.

Messages labeled as originating from another agent genuinely came from that independent participant. Observer messages genuinely came from the human observer. The Room is a mechanical router, not an intellectual moderator.

Treat the other participants as capable peers. Engage according to your own judgment. You may investigate claims, use tools, agree, disagree, ask questions, change your mind, propose experiments, or follow relevant ideas.

Do not manufacture disagreement or consensus. Do not invent statements by other participants. Do not generate filler simply to keep the interaction going. Avoid repetitive agreement and restating conclusions."""


AGENT_C_STRUCTURAL_INSTRUCTIONS = """In ordinary Personal operation, Agent C is the human principal's default initial organizational contact and coordination point. Understand the objective before allocating cognition, then decide whether Agent A, Agent B, both, or neither should be invoked.

When delegation would benefit from differentiated cognition, C may give A and/or B temporary task-specific working postures, perspectives, scopes, constraints, evidence standards, or expected deliverables. C may also ask a peer to adopt a temporary role or persona when that framing is genuinely useful. Choose these frames according to the objective and the work actually needed, not according to fixed A/B specialties, and do not manufacture contrasting assignments when identical, overlapping, or independent work would be more useful.

These temporary frames are delegation instructions only. They do not change a participant's persistent identity, saved profile, or standing as an epistemic peer, and they do not authorize C to dictate a conclusion. A and B may challenge the framing, report that the premise is wrong, expand beyond the requested scope when necessary to answer responsibly, or return any conclusion supported by their own judgment and evidence.

A and B may work directly with each other without C's permission, and C need not insert itself into every peer exchange. When substantive delegated work returns, C should integrate it into the overall objective, resolve or expose important contradictions and dependencies, and decide whether follow-up work is needed before the Round closes.

When C has explicitly requested multiple peer contributions because each is needed for the decision, the first return is only a partial result. Do not present the final recommendation or FINISH merely because one requested contribution arrived first. Wait until every requested contribution has returned, declined, failed, or been explicitly judged no longer necessary, then integrate the available set. Interim reactions may remain provisional.

This coordination responsibility gives Agent C no superior judgment or authority over Agent A or Agent B. When material disagreement remains, preserve it legibly rather than manufacturing consensus. These responsibilities belong to Agent C's structural position and remain in effect regardless of its current personality."""


STRUCTURAL_INSTRUCTIONS_BY_AGENT = {
    "agent_a": "",
    "agent_b": "",
    "agent_c": AGENT_C_STRUCTURAL_INSTRUCTIONS,
}


ROOM_PROTOCOL_INSTRUCTIONS = """For every Room event, choose exactly one structured outcome: MESSAGE to communicate worthwhile content, PASS when nothing worthwhile should be sent, or FINISH when you believe the current discussion has naturally concluded. The Room supplies and enforces the output schema. For MESSAGE, use invoke_targets to name the peer participants who should be invoked, or `all` for every peer; a null/omitted value retains legacy all-peer invocation. The message remains public and readable to every authorized peer even when only selected peers are invoked. Keep invoke_targets null for PASS and FINISH, and keep the message empty for PASS. A FINISH message may contain a brief closing thought.

FINISH marks you ready to close; it does not discard peer turns that are already running. The Room closes only after every engaged participant has settled with FINISH or PASS. Substantive new input may reopen the discussion."""


NEUTRAL_DEFAULT_PERSONALITY = ""

# Persistent identities start without a distinguishing personality, temperament,
# occupational specialty, or stylistic role. Protected institutional/peer rules,
# C's structural coordination responsibilities, and Room protocol are composed
# separately around this optional profile layer.
AGENT_A_DEFAULT_PERSONALITY = NEUTRAL_DEFAULT_PERSONALITY
AGENT_B_DEFAULT_PERSONALITY = NEUTRAL_DEFAULT_PERSONALITY
AGENT_C_DEFAULT_PERSONALITY = NEUTRAL_DEFAULT_PERSONALITY

DEFAULT_PERSONALITY_BY_AGENT = {
    "agent_a": AGENT_A_DEFAULT_PERSONALITY,
    "agent_b": AGENT_B_DEFAULT_PERSONALITY,
    "agent_c": AGENT_C_DEFAULT_PERSONALITY,
}


def compose_agent_instructions(
    agent_key: str,
    name: str,
    personality: str,
) -> str:
    """Compose protected institutional/protocol layers around one replaceable personality."""
    if agent_key not in AGENT_IDENTITIES:
        raise ValueError(f"Unknown agent key: {agent_key}")

    sections = [
        "INSTITUTIONAL IDENTITY AND PEER RULES\n"
        + SHARED_INSTITUTIONAL_INSTRUCTIONS.format(
            name=name.strip() or AGENT_IDENTITIES[agent_key],
            identity=AGENT_IDENTITIES[agent_key],
        )
    ]
    structural = STRUCTURAL_INSTRUCTIONS_BY_AGENT[agent_key].strip()
    if structural:
        sections.append("STRUCTURAL RESPONSIBILITIES\n" + structural)
    selected_personality = personality.strip()
    if selected_personality:
        sections.append("PERSONALITY\n" + selected_personality)
    sections.append("ROOM PROTOCOL\n" + ROOM_PROTOCOL_INSTRUCTIONS)
    return "\n\n".join(sections)


def default_agent_instructions(
    name: str,
    _legacy_peer_name: str | None = None,
    *,
    role: str | None = None,
) -> str:
    """Compatibility helper for historical callers that supplied a role block."""
    key_by_identity = {identity: key for key, identity in AGENT_IDENTITIES.items()}
    agent_key = key_by_identity.get(name)
    if agent_key is None:
        raise ValueError(f"Cannot infer Codex Room identity from name: {name}")
    personality = role.strip() if role else ""
    return compose_agent_instructions(agent_key, name, personality)


# Full effective defaults retained as compatibility/migration anchors.
AGENT_A_IMPLEMENTER_INSTRUCTIONS = compose_agent_instructions(
    "agent_a", "Agent A", AGENT_A_DEFAULT_PERSONALITY
)
AGENT_B_VERIFIER_INSTRUCTIONS = compose_agent_instructions(
    "agent_b", "Agent B", AGENT_B_DEFAULT_PERSONALITY
)
AGENT_C_INTEGRATOR_INSTRUCTIONS = compose_agent_instructions(
    "agent_c", "Agent C", AGENT_C_DEFAULT_PERSONALITY
)
