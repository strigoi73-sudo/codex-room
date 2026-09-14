# Codex Room — Decision Register

**Initialized:** 2026-09-08  
**Last updated:** 2026-09-12  
**Scope:** Settled architectural, governance, product-direction, and development-order decisions.  
**Freshness:** Later explicit user decisions supersede earlier entries. Implementation status is tracked primarily in Architecture & Current State and the Evidence Register.

## Decision status

- **ACTIVE** — current settled decision.
- **SUPERSEDED** — preserved for history; a later decision governs.

---

### D-001 — Product name is Codex Room
**Date:** 2026-09-08 or earlier  
**Status:** ACTIVE

The multi-agent system/product is named **Codex Room**. “Technobabble” refers to the prior ChatGPT Project/context and should not be used as the system name.

### D-002 — Fixed Personal production triad
**Date:** 2026-09-08 or earlier  
**Status:** ACTIVE

For the foreseeable future, the Personal architecture contains exactly three persistent production agents: A, B, and C. Do not add a fourth persistent production agent without an explicit new decision.

Temporary experimental participants do not themselves expand the production architecture.

### D-003 — A/B/C role differentiation and peer status
**Date:** 2026-09-08 or earlier  
**Status:** ACTIVE

- A — Implementer
- B — Verifier
- C — Integrator

A/B/C are epistemic peers. C may coordinate without gaining superior judgment.

**Principle:** **C controls coordination, not judgment.**

### D-004 — Ratified six-clause Constitution
**Date:** 2026-09-08 or earlier  
**Status:** ACTIVE

The six clauses reproduced in `03_CONSTITUTION_AND_INSTITUTIONAL_RULES.md` govern agent conduct. Their wording should not be casually rewritten.

### D-005 — Token/usage efficiency is the top-level development concern
**Date:** 2026-09-08  
**Status:** ACTIVE

Prioritize reductions in unnecessary model invocation, unnecessary context, duplicate cognition, retry waste, PASS waste, and other avoidable provider usage ahead of broader productization when those reductions materially improve operating economics without sacrificing correctness, safety, continuity, or useful work.

The exact operational wording of “token efficiency” remains subject to deliberate refinement; do not silently harden provisional wording into constitutional interpretation.

### D-006 — Selective invocation is the immediate efficiency problem to solve
**Date:** 2026-09-08  
**Status:** SUPERSEDED

Measured Room usage justified making unnecessary peer invocation the immediate efficiency problem. That investigation and implementation phase subsequently completed. Current work order is controlled by D-014 and Development Control.

### D-007 — Core/Room governance taxonomy
**Date:** 2026-09-08  
**Status:** ACTIVE

Use:

- **[CORE]** for host-runtime/codebase changes with cross-Room implications;
- **[ROOM]** for changes confined to one Room's state, profiles, artifacts, tools, knowledge, objectives, or operating rules;
- **[CORE + ROOM migration]** for a centrally implemented Core capability followed by Room-specific adoption.

A running Room may investigate/specify/test/evaluate CORE work but does not hot-patch the protected runtime hosting itself. Actual CORE implementation occurs outside the protected running Room through the cheapest authorized execution layer capable of safely performing the work and producing adequate evidence. Prefer one controlled writer, with independent review where useful.

### D-008 — Review validity follows exact artifact version
**Date:** 2026-09-08 or earlier  
**Status:** ACTIVE

**Handoffs protect the validity of review, not access to the file.**

A review applies to the reviewed bytes/version. Later mutation invalidates the old review for the new version without forbidding the mutation.

**Principle:** **Coordinate conflicts, don't freeze the organization.**

### D-009 — Institutional memory uses three strata
**Date:** 2026-09-08 or earlier  
**Status:** ACTIVE

Distinguish:

1. active Room context;
2. durable promoted institutional knowledge;
3. archived episodic history.

Preferred retrieval direction: **Room archive → searchable index → targeted retrieval → agent context.**

**Principle:** **Index broadly, retrieve narrowly.**

### D-010 — Personal first; Enterprise later
**Date:** 2026-09-08 or earlier  
**Status:** ACTIVE

Prioritize a viable Personal architecture before Enterprise-scale workforce management, administration, or organizational expansion.

### D-011 — Provider neutrality is a longer-term design goal
**Date:** 2026-09-08 or earlier  
**Status:** ACTIVE

Develop OpenAI/Codex first while avoiding unnecessary architectural coupling that would prevent future provider-neutral or mixed-provider designs. Provider expansion is not the current priority.

### D-012 — Stable recurring cognition is a candidate for deterministic tooling
**Date:** 2026-09-08  
**Status:** ACTIVE

When recurring model reasoning has become a stable deterministic procedure, consider compiling it into local software/state machines when the expected model-usage savings justify the maintenance cost.

### D-013 — Usage-limit failure should be recoverable without violating thread/overlap invariants
**Date:** 2026-09-08  
**Status:** ACTIVE

Usage-limit failures should be recoverable while preserving agent identity, persistent thread continuity where safely possible, serialized execution, and fail-closed behavior when safe recovery cannot be established. Immediate retry storms are not acceptable.

The implemented mechanism is summarized in Architecture & Current State and supported by the Evidence Register.

### D-014 — Finish the engineering foundation before Assurance Pass 2
**Date:** 2026-09-09  
**Status:** ACTIVE

Before launching Assurance Pass 2, establish the minimum professional engineering baseline needed to make later review efficient and durable:

1. real Git/source-control baseline;
2. sane source/runtime/generated boundaries without filesystem reorganization;
3. reproducible dependencies/environment;
4. one canonical full-test command;
5. minimal CI once the local foundation is stable;
6. current maintained project documentation.

**Principle:** **Professional-grade readiness, not professional-looking ceremony.**

Avoid GitFlow, heavyweight process, enterprise tooling, or other ceremony that does not solve a demonstrated need.

### D-015 — Selective invocation separates readability from immediate cognition
**Date:** 2026-09-09  
**Status:** ACTIVE

For agent MESSAGE outcomes, selective invocation may name the peers whose immediate cognition is useful while keeping the public message readable to authorized non-target peers.

Settled compatibility behavior:

- named `invoke_targets` wake only those peers;
- `["all"]` wakes all peers;
- omitted/null targets retain legacy all-peer fan-out;
- passive readable deliveries do not initiate turns or block settlement;
- earlier passive information is consumed on a later legitimate trigger in sequence order;
- private authorization and serialized/no-overlap execution remain intact.

Do not infer routing from prose labels such as “B:” or “C:”.

### D-016 — Compaction growth uses a deferred post-compaction baseline
**Date:** 2026-09-09  
**Status:** ACTIVE

After successful context compaction, do not use the pre-compaction input count as the 25,000-token growth baseline. Mark the baseline pending; the first later successful authoritative input measurement establishes it, and that establishment turn cannot compact again.

### D-017 — Usage walls schedule delayed same-agent continuation
**Date:** 2026-09-09  
**Status:** ACTIVE

For a positively identified usage-limit wall with a parseable provider retry time, persist a continuation for the same agent/thread and release it through the normal serialized queue at the reported retry time plus a 60-second grace period.

Repeated walls replace the schedule; stale work is cancelled by lifecycle/stop rules; unknown retry formats fail closed.

### D-018 — Allocate cognition once; execute at the cheapest capable layer; hand off exact evidence through Git/GitHub
**Date:** 2026-09-10  
**Amended:** 2026-09-10  
**Status:** ACTIVE

For external Codex Room development and maintenance, allocate cognition and execution to the cheapest authorized layer that can safely perform the work and produce adequate evidence. Do not delegate work to another model merely because that model has traditionally occupied an “execution” role.

Default operating policy:

- when the ChatGPT Codex Room Project already holds the relevant context, use that context for scoping, sequencing, tradeoffs, and review rather than asking another model to rediscover the same problem;
- when the Project has connected tools capable of performing a repository inspection, deterministic operation, or bounded edit safely and adequately, perform that work directly rather than delegating it to Codex;
- use deterministic local commands when the required evidence or operation depends on local machine state;
- use local Codex when the task requires local access unavailable to the Project, substantial implementation work better performed in the local development environment, failure-prone or scattered investigation, unresolved local ambiguity, or genuinely useful independent cognition;
- when Codex is used for already-understood work, give it phase-titled, explicit, scope-bounded prompts with verification requirements and stop conditions;
- use Git diffs, blob/commit identities, test outputs, and other exact artifacts as preferred handoff evidence instead of asking models to narrate mechanically available facts;
- use GitHub as the shared canonical history and review bridge between the Project and local development environment;
- use GitHub Actions and other deterministic software for routine mechanical verification when model judgment is unnecessary.

The execution hierarchy is a cost and capability preference, not an authority shortcut. Correctness, safety, continuity, adequate verification, and meaningful independent review take precedence over minimizing model calls. Independent review should remain genuinely independent when independence is the purpose.

**Principle:** **Reason where the relevant context already exists; execute at the cheapest capable layer; hand off exact evidence; duplicate cognition only when it earns its cost.**
### D-019 — Personal daily usage pacing limit is approved planned development
**Date:** 2026-09-11  
**Status:** ACTIVE

Codex Room Personal should provide a user-configurable **daily usage limit expressed as a percentage of the user's weekly Codex usage allowance**.

Settled product intent:

- the default daily limit is **one-seventh of the weekly allowance**, displayed approximately as **14.3%**;
- Codex Room should base pacing on Codex's structured account rate-limit/usage meter rather than estimate the weekly allowance from Room token counts;
- once the configured daily allowance has been reached according to the latest available Codex usage reading, Codex Room should stop initiating new model work under that pacing policy;
- an already-running model invocation may finish, so exact enforcement can overshoot the configured percentage;
- the provider's own usage/rate-limit enforcement remains authoritative.

This capability is **DECIDED / NOT IMPLEMENTED** and **PLANNED**. Approval does not start implementation. D-020 later inserted the permanent-triad / C-integration migration ahead of Assurance Pass 2; this usage-pacing decision does not displace that migration or A2.

The following details are intentionally left for implementation design rather than settled here: warning thresholds, UI presentation, carry-forward behavior, daily-period/time-zone semantics, polling cadence, and the exact SDK/app-server integration technique.

### D-020 — Permanent Personal triad, C-first coordination, and integration-before-closure
**Date:** 2026-09-11  
**Status:** ACTIVE

Codex Room Personal should align runtime behavior with the settled three-agent production architecture rather than treating Agent C as an optional addition.

Settled architecture and behavior:

- every new Personal Room contains A — Implementer, B — Verifier, and C — Integrator from creation; C is not optional for new Personal Rooms;
- historical two-agent Rooms remain valid historical state and must not be silently mutated merely because the new architecture is mandatory; an explicit upgrade/migration path may add C while preserving A/B identities and provenance;
- C is the human principal's default initial agent contact and the ordinary default Round starter;
- C decides the initial conversation dynamics and may selectively invoke A, B, both, or neither according to the work;
- A and B may communicate directly with each other without routing through C or obtaining C's permission;
- public inter-agent messages remain readable to the full authorized triad while `invoke_targets` determines which peers become immediately runnable, preserving the readable-vs-runnable distinction from D-015;
- C should remain durably aware of A/B exchanges through passive readable delivery without being invoked after every peer message;
- when material A/B work reaches a completion or settlement boundary, the runtime must provide C an integration opportunity before final Round closure if C has not yet integrated that work; this must be enforced mechanically rather than relying only on prompt compliance;
- C may synthesize, report, request follow-up, or redelegate after that integration turn; A/B/C remain epistemic peers and C gains no superior judgment;
- explicitly starting all participants independently remains available for experiments or tasks where independent first-pass cognition is deliberately desired.

The implementation scope is **[CORE + ROOM migration]**: CORE changes establish mandatory triad, C-first defaults, passive C awareness, and the integration-before-closure barrier for new operation; legacy A/B Rooms receive deliberate migration behavior rather than silent mutation.

**Reality:** IMPLEMENTED / VERIFIED — 2026-09-12. See E-027.

**Development order:** the migration was completed and adequately verified before A2. **A2 — Assurance Pass 2** is now the next assurance milestone, preserving D-014's requirement that the Engineering Foundation precede A2.


### D-021 — Repository `docs/project/` is the canonical home for maintained Project sources
**Date:** 2026-09-11  
**Status:** ACTIVE

The maintained Codex Room Project-source documents are canonically stored in the private GitHub repository `strigoi73-sudo/codex-room` under `docs/project/` on canonical `main`.

Settled source-of-truth rules:

- the repository copies under `docs/project/` are the authoritative maintained Project sources;
- Git/GitHub provide exact version history, diffs, provenance, and review identity for those documents just as they do for code;
- the live GPT Project custom instructions remain a bootstrap/runtime configuration, not a duplicate maintained Project source; they should identify the canonical repository, document ownership, and retrieval rules;
- GPT Project source attachments should not be maintained as parallel authoritative copies of the repository documents after cutover;
- retrieve only the Project documents relevant to the task rather than loading the entire package reflexively;
- for “where are we?”, “what’s next?”, or resume-after-context-switch questions, read the canonical `docs/project/06_DEVELOPMENT_CONTROL.md` before answering and verify consequential volatile repository facts directly when practical;
- when current Project-source content is consequential and repository access is unavailable, state that freshness cannot be verified rather than silently substituting stale remembered or uploaded text;
- live GPT Project instructions may be exported as dated handoff snapshots when useful, but no repository copy should become a second authoritative live-instructions source.

This decision changes the maintenance location and retrieval workflow, not the semantic ownership of the individual documents defined by the Package Index.


### D-022 — Agent-directed deterministic capabilities with rollover continuity
**Date:** 2026-09-12  
**Status:** ACTIVE

P4 should build a deterministic capability system rather than attempt to predict all future Room-specific software needs.

Settled direction:

- A/B/C decide when a subproblem warrants deterministic software;
- every new Personal Room receives a small CORE standard library of broadly useful deterministic primitives;
- built-in and custom capabilities share a registry/discovery/invocation model with stable identity, typed contracts, declared permissions/side effects, exact version/implementation identity, and verification/provenance metadata;
- when the standard library is insufficient, agents may create deterministic software and register it after adequate validation rather than repeatedly spending model cognition on the same mechanical procedure;
- registered custom capabilities belonging to a continuing body of work survive Room rollover and remain available to the successor at the exact inherited version unless deliberately retired or excluded;
- historical Rooms retain references to the exact versions they actually used;
- proven capabilities may later be promoted to broader Personal or CORE scope;
- registered capability status is stronger than arbitrary ad hoc code execution and therefore requires an explicit contract, implementation identity, permissions, and verification evidence.

This sets product architecture and continuity requirements. It does not claim that custom registration, rollover inheritance, Personal promotion, or the broader default library are implemented yet.

**Principle:** **Agents decide when cognition should become software; Codex Room makes that software discoverable, verifiable, persistent, and reusable.**

### D-023 — Persistent agent identity is separate from replaceable personality
**Date:** 2026-09-13  
**Status:** ACTIVE

Codex Room Personal should treat Agent A, Agent B, and Agent C as persistent organizational identities rather than permanent occupational roles.

Settled design:

- every persistent agent has a standard default personality;
- the human principal may replace the personality of A, B, or C without changing that agent's persistent identity, peer status, history, or protected structural responsibilities;
- a Room-specific personality override replaces the selected default personality rather than being appended to it as a competing instruction;
- shared institutional identity/peer rules and Room protocol remain protected outside the replaceable personality layer;
- C retains protected organizer/coordination responsibilities regardless of C's current personality;
- C's organizer status grants no superior judgment or authority over A or B;
- exact default-personality wording is deliberately below the Charter/Constitution level and may be refined empirically without reopening the three-agent architecture.

This decision supersedes D-020 only where D-020 names **Implementer / Verifier / Integrator** as permanent agent-role descriptors. D-020's permanent-triad, C-first coordination, direct peer communication, selective invocation, and integration-before-closure requirements remain active.

**Implementation status:** the protected-instruction / replaceable-personality composition model is **IMPLEMENTED / VERIFIED** by PR #28 and E-041. The existing default personality prose still contains the older Implementer / Verifier / Integrator labels pending the next deliberate personality-design slice; those labels are no longer the governing architectural definition of A, B, and C.

### D-024 — Persistent agents start from neutral default cognition
**Date:** 2026-09-14  
**Status:** ACTIVE

Codex Room Personal should not assign distinguishing personality, temperament, occupational identity, intellectual specialty, or stylistic role to Agent A, Agent B, or Agent C at startup.

Settled design:

- A/B/C remain persistent organizational identities and epistemic peers.
- The standard default profile body for A, B, and C is neutral/empty; fresh Rooms therefore do not compose a default `PERSONALITY` layer.
- Shared institutional identity/peer rules and Room protocol remain protected and continue to give every participant the context needed to understand the Room and its peers.
- C retains the protected organizer/coordination responsibilities established by D-020/D-023. This structural responsibility is not a personality or cognitive specialty and grants no superior judgment.
- A and B receive no protected occupational or cognitive specialization.
- Optional custom/default-profile text and Room-specific profile overrides remain supported. When explicitly supplied, they may shape a participant for that Room without changing persistent identity or protected structure.
- C may differentiate delegated work through task framing, participant-specific context, or ordinary coordination when useful. A future formal dynamic cognitive-posture capability may refine that behavior, but is not required by this decision and is not implemented by D-024.
- No participant is expected to be behaviorally recognizable from a startup temperament.

D-024 supersedes D-023 only where D-023 requires every persistent agent to have a non-neutral standard default personality. D-023's separation of persistent identity from replaceable profile content, protected institutional/structural layers, Room-specific replacement semantics, and C's no-superior-judgment coordination rule remain active.

**Principle:** **Start neutral; specialize work when the objective warrants it.**

### D-025 — C may assign temporary cognitive frames during delegation
**Date:** 2026-09-14  
**Status:** ACTIVE

Agent C's protected coordination responsibility includes discretion to shape delegated cognition for the current objective.

Settled design:

- when useful, C may give A and/or B temporary task-specific working postures, perspectives, scopes, constraints, evidence standards, expected deliverables, or temporary roles/personas;
- C should choose those frames from the needs of the objective rather than from fixed A/B specialties or startup personality;
- C is not required to differentiate peers. Identical, overlapping, sequential, or independent assignments remain valid when they better serve the work;
- temporary cognitive frames are delegation instructions only. They do not alter persistent identity, saved profile content, peer standing, or lineage;
- C's coordination authority does not extend to dictating conclusions. A/B may challenge the framing, reject a mistaken premise, expand scope when necessary to answer responsibly, or return any conclusion supported by their own judgment and evidence;
- no new persistent posture registry, database object, or UI mechanism is required for the initial capability. Natural-language delegation through the existing Room mechanism is sufficient until evidence demonstrates a need for stronger machinery.

D-025 builds on D-020's C-first coordination and D-024's neutral startup. It does not restore permanent personality differentiation.

**Principle:** **Start neutral; let C shape the cognition needed for the task without controlling the answer.**

