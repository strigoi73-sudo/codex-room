# Codex Room — Decision Register

**Initialized:** 2026-09-08
**Last updated:** 2026-09-26
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
**Status:** SUPERSEDED

The early formulation assigned occupational labels to A, B, and C. D-023 and D-024 superseded those permanent-role labels. Current Personal design treats A and B as operationally equivalent persistent epistemic peers with the same neutral default profile and no protected occupational or cognitive specialization. C is also an epistemic peer and retains protected coordination responsibilities.

The enduring principle survives in later active decisions:

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
**Amended:** 2026-09-16
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
- use deterministic local verification commands for routine mechanical verification when model judgment is unnecessary; GitHub-hosted automation may be reintroduced only when a demonstrated need justifies its operational cost and reliability tradeoffs.

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

This capability is **DECIDED / NOT IMPLEMENTED**. Approval does not start implementation.

**Readiness update — 2026-09-14:** implementation is deferred until Codex Room can correctly account for mixed subscription allowance and purchased credits. E-026 establishes access to structured rate-limit data, but does not establish the semantics needed to know how multiple usage pools are represented, prioritized, or consumed. The product intent above remains active; implementation should not proceed by assuming a single weekly pool.

Before implementation, deliberately resolve which usage pool the pacing policy governs, whether and how purchased credits alter or bypass the daily pacing limit, what provider-reported data can distinguish the relevant pools, and behavior when one pool is exhausted while another remains available.

Other details intentionally left for implementation design include warning thresholds, UI presentation, carry-forward behavior, daily-period/time-zone semantics, polling cadence, and the exact SDK/app-server integration technique.

### D-020 — Permanent Personal triad, C-first coordination, and integration-before-closure
**Date:** 2026-09-11
**Status:** ACTIVE

Codex Room Personal should align runtime behavior with the settled three-agent production architecture rather than treating Agent C as an optional addition.

Settled architecture and behavior:

- every new Personal Room contains Agent A, Agent B, and Agent C from creation; A and B have no permanent occupational specialization, and C is not optional for new Personal Rooms;
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

**Development-order record:** the migration was completed and adequately verified before A2, preserving D-014's sequencing requirement. A2 subsequently completed; current work order belongs only in Development Control.


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

This sets product architecture and continuity requirements. P4 subsequently implemented and verified the CORE registry, custom registration/invocation, and exact-version lineage rollover inheritance. Broader Personal-scope promotion remains future work only if demonstrated reuse justifies it; current implementation status belongs in Architecture & Current State and Development Control.

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

This decision supersedes the historical occupational-role labels in D-003 and D-020. D-020's permanent-triad, C-first coordination, direct peer communication, selective invocation, and integration-before-closure requirements remain active.

**Implementation status:** the protected-instruction / replaceable-profile composition model is **IMPLEMENTED / VERIFIED** by PR #28 and E-041. D-024 subsequently established neutral/empty standard profile bodies for A/B/C; occupational labels are not startup cognitive specializations.

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

### D-026 — Dual-peer delegation must be meaningfully differentiated
**Date:** 2026-09-14
**Status:** ACTIVE

Cognition should be allocated economically. Because A and B are neutral peers, substantially duplicate assignments are ordinarily redundant and do not justify the added token and coordination cost. C may select different admitted execution configurations for delegated peers, but model heterogeneity by itself does not make duplicate cognition valuable.

Settled design:

- every additional peer invocation must have expected marginal value;
- C should use the fewest peers that can add sufficient value to the objective;
- if one peer is sufficient, C should invoke one rather than both;
- if C invokes both A and B in the same delegation, their cognitive responsibilities **must be meaningfully differentiated**;
- differentiation must concern a substantive dimension expected to create complementary value, such as perspective, method, evidence source, scope, constraint, deliverable, verification responsibility, or another real division of cognitive work;
- cosmetic role labels do not satisfy the rule;
- C must not send A and B substantially the same analysis in substantially the same way;
- when independent verification is valuable, the independence should still be differentiated by method or responsibility—for example, one peer reconstructs from first principles while the other audits assumptions, evidence, or failure modes;
- A/B remain epistemic peers and may challenge their assigned frame or return any conclusion supported by their judgment.

D-026 supersedes D-025 only where D-025 allowed identical or overlapping dual-peer assignments merely because independent work might be useful. D-025's temporary cognitive-framing authority, identity protections, and no-dictated-conclusion guardrails remain active.

**Principle:** **Use the fewest peers that add sufficient value; if both peers are invoked, buy complementary cognition rather than duplicate cognition.**

### D-027 — Invocation is for immediate cognition, not message visibility
**Date:** 2026-09-14
**Status:** ACTIVE

Runnable peer invocation should be treated as an explicit purchase of additional cognition rather than as a message-delivery mechanism.

Settled design:

- all Room participants should invoke a peer only when that peer's immediate cognition is expected to add material value;
- public Room messages remain readable to authorized peers without making those peers runnable, so visibility, acknowledgment, or passive awareness is not a sufficient reason to invoke;
- `all` should be used only when every peer genuinely needs to run;
- if no additional peer cognition is needed, a MESSAGE should use `invoke_targets: []`, meaning public/readable delivery with no runnable peers; `null` retains the legacy all-peer fanout behavior;
- when A or B is completing a bounded delegation from C, that peer should normally return the result to C without invoking the other delegated peer;
- A/B may still invoke each other when additional cognition from that peer is materially necessary to complete or improve the delegated work;
- D-027 does not prohibit direct A/B collaboration and does not make C a permission gate. It distinguishes readable communication from runnable cognition;
- D-026 remains the stronger special case for C's dual-peer allocation: when C invokes both A and B, the two assignments must still be meaningfully differentiated.

D-027 generalizes the token-economy principle beyond C's initial allocation decision to every use of `invoke_targets`.

**Principle:** **Messages are public; invocations buy cognition. Wake a peer only when the work needs that peer to think now.**



### D-028 — Astra is prohibited for Codex Room execution
**Date:** 2026-09-15
**Status:** SUPERSEDED by D-051

Codex Room must not execute Room cognition on an Astra model.

Settled rule:

- Astra is excluded from every C-selectable execution configuration;
- the runtime must fail closed if an execution path attempts to start a Room turn with the currently identified Astra model `gpt-6-astra`;
- prompts, coordination policy, or later routing logic may not override this prohibition;
- admitted Luna, Terra, and Sol configurations remain available for bounded C-selected peer execution; the dedicated synthetic P1 benchmark series later closed without establishing a trustworthy automatic ranking, and no automatic model router is authorized;
- changing or removing this prohibition requires an explicit later human-principal decision.

This is a hard execution constraint, not an economic preference or default-selection heuristic.

### D-029 — Personal Rooms have bounded read access to CORE and other Room shared workspaces
**Date:** 2026-09-15
**Status:** ACTIVE

Personal Room agents should be able to inspect relevant evidence outside their current Room workspace without receiving cross-boundary mutation authority.

Settled design:

- a running Personal Room may inspect authorized CORE source and authorized shared workspaces belonging to other Rooms under the same Personal installation;
- CORE inspection is read-only and limited to the maintained source/repository surface needed to understand implementation, tests, documentation, launch/runtime configuration, and related evidence;
- protected runtime data, credentials/secrets, environment-private files, provider/account material, and other non-source host state are not part of this read surface;
- cross-Room inspection resolves only another Room's shared workspace. Explicitly private participant material, private overlays/initialization, protected Room metadata, and host database internals are not made generally readable by this decision;
- read access does not authorize a running Room to modify CORE or another Room. Existing CORE/Room write-governance boundaries continue to apply;
- retrieval should be on demand and bounded. CORE and other Rooms are not injected wholesale into agent context;
- the preferred implementation is through deterministic, inspectable read-only capabilities with path confinement, symlink/reparse protection, bounded output, and durable provenance rather than unrestricted host filesystem access.

This decision clarifies the CORE/Room boundary: **protection constrains mutation, not legitimate inspection.**

### D-030 — Transaction work state replaces conversational backlog as the authoritative scheduler
**Date:** 2026-09-15
**Status:** ACTIVE

The principal approves I-015 Stage A as Codex Room's coordination-stabilization architecture.

Settled direction:

- A/B/C remain the permanent Personal organization and remain epistemic peers; C retains coordination responsibility but no superior judgment;
- agents continue to decide intellectual questions: whether peer cognition is useful, whom to involve, how to frame assignments, what evidence matters, how to interpret disagreement, and what conclusion to reach;
- CORE owns declared mechanical work state through explicit **Task → Assignment → Join → Result/Integration → Settlement** transactions;
- transaction-enabled work must not use unread public conversation as an implicit runnable-work queue;
- public Room history remains readable/auditable, but cognition occurs only through an explicit assignment;
- delegation must be one atomic structured action that both defines the peer work and creates the runnable assignment(s); a separate routing field must not be able to contradict the declared delegation;
- dependency joins are deterministic CORE state. A parent assignment that delegates remains nonterminal until the required child assignments settle and the parent resumes;
- direct A/B collaboration remains allowed through nested explicit delegation;
- task settlement is determined by task/assignment/join state, not by participant membership, passive delivery counts, prose promises, or agent-level READY_TO_FINISH state;
- existing exact SDK-turn binding, serialized per-agent execution, recovery/provenance machinery, capability boundaries, Rooms/Rounds, persistent identities, and audit events should be reused rather than rewritten;
- legacy work-model-v1 Rounds retain their historical event/delivery interpretation. Transaction semantics are introduced behind an explicit work-model version and historical event streams are not silently reinterpreted;
- Stage A deliberately retains the current persistent SDK-thread/context model so coordination reliability can be isolated from the later Stage C memory/context experiment;
- implementation should proceed in bounded slices with deterministic invariant tests before naturalistic paid validation.

D-030 supersedes the **implementation mechanism**, but not the governing intent, of D-015/D-020/D-027 where those decisions relied on readable/runnable event deliveries, inferred delegation cohorts, or conversational settlement. Their principles remain active: selective cognition, public readability, C integration-before-closure, direct peer collaboration, and invocation economy.

**Principle:** **Agents decide the work; CORE makes declared work state reliable.**

### D-031 — Agents declare bounded deterministic intent; CORE owns source-evidence execution mechanics
**Date:** 2026-09-16
**Status:** ACTIVE

For transaction-enabled work, the ordinary agent interface for read-only source evidence should express the evidence needed, while CORE owns the mechanical invocation path.

Settled boundary:

- agents decide the intellectual need for deterministic evidence: what must be established, which logical source is relevant, which paths/search concepts/bounds matter, and how returned evidence affects judgment;
- for the bounded Stage-B source-evidence domain, agents should not need to choose or operate CLI mechanics such as executable discovery, registry ceremony, shell quoting, `bundle`, `read-many`, `search-many`, JSON transport, or plan-file fallbacks;
- CORE validates declared requests, enforces source authority and bounds, mechanically selects existing `inspect_source` primitives/batching, executes them, preserves provenance, and returns normalized evidence to the same open assignment;
- the first implementation is limited to read-only `READ`, `SEARCH`, and `FIND` source evidence. Arbitrary custom-capability brokerage remains outside this slice because it may require preserving a different sandbox/authority boundary;
- existing `inspect_source`, `bundle`, homogeneous batch operations, registry machinery, custom capabilities, source confinement, CLI commands, and shell access remain available as implementation primitives, compatibility/operator surfaces, or for work outside the structured evidence path;
- evidence-request identity and recovery must be explicit transaction state so restart/replay does not depend on prose or rediscovery;
- bulk retrieved content should remain operational/transient where possible, while durable records retain bounded request/result provenance and mechanical execution metadata.

This decision extends D-030's transaction principle into deterministic evidence acquisition. It does not change A/B/C authority or judgment and does not decide Stage C persistent-context architecture.

**Principle:** **Agents declare bounded deterministic intent; CORE owns deterministic execution mechanics.**

### D-032 — Provider context is transport; Assignment is the first bounded context unit
**Date:** 2026-09-16
**Amended:** 2026-09-18 by D-037
**Status:** ACTIVE

I-015 Stage C should test provider-context economy without redefining the persistent A/B/C organization or weakening the explicit transaction model.

Settled experimental boundary:

- persistent A/B/C identity remains application-level organizational state under D-020 and D-023; one forever-growing provider thread is not itself the definition of agent identity;
- the first Stage-C slice is opt-in only for work-model version 2 through `provider_context_mode="assignment_thread"`; existing version-1 behavior and ordinary version-2 `persistent_agent_thread` behavior remain unchanged;
- in assignment-thread mode, each logical transaction Assignment owns one durable provider thread;
- every execution that continues the same logical Assignment — including evidence resume, dependency/join resume, retry, usage-wall continuation, and exact-turn restart recovery — must use that same Assignment thread;
- different Assignments do not inherit one another's provider-thread history merely because they belong to the same persistent Room agent;
- CORE remains responsible for rebuilding the authoritative assignment envelope from durable Room/Round/Task/Assignment/Join/Evidence state, while the Assignment thread may retain bounded same-assignment conversational/provider context;
- D-009 remains the direction for continuity beyond one Assignment: archived or durable history should be indexed broadly and retrieved narrowly when the task actually needs it rather than injected wholesale;
- Stage C.1 does not yet settle an automatic summarization policy, a general memory index, provider-thread retention/archival policy, or production default activation;
- assignment-thread mode must retain exact thread/turn provenance and restart safety before any naturalistic economic comparison is valid.

This decision extends D-030 by separating **persistent organizational identity** from **provider context transport**. It does not change A/B/C peer status, C's coordination responsibility, evidence authority, or transaction settlement semantics.

**Principle:** **Preserve durable identity and explicit work state; bound provider context to the smallest unit that safely carries the work.**

### D-033 — Cross-Assignment continuity uses explicit bounded Room-history retrieval
**Date:** 2026-09-16
**Amended:** 2026-09-18 by D-037
**Status:** ACTIVE

Stage C.2 established that Assignment-bounded provider context materially reduces inherited replay cost but does not itself carry needed episodic continuity from earlier Rounds. The first continuity mechanism should therefore retrieve prior durable Room results explicitly rather than restore a forever-growing provider thread.

Settled boundary:

- transaction-enabled agents may declare a bounded `HISTORY` need when the current Assignment requires a specific fact or result from an earlier Round in the same Room;
- the first retrieval vocabulary is deliberately small: `RECENT` for a temporal dependency and lexical `SEARCH` for a known concept, with an optional agent filter and bounded result count;
- CORE owns mechanical selection from durable completed Assignment results, same-Room authorization, bounds, exact event provenance, and atomic attachment of selected result-event IDs to the requesting Assignment;
- `HISTORY` is nonterminal work on the same logical Assignment. It must not release joins or settle the Task; the same Assignment resumes on its existing provider context with the selected historical results added to its authoritative envelope;
- current Task/Assignment/Join/Evidence state remains authoritative and is not obtained through historical search. Source/file retrieval remains the separate `EVIDENCE` path;
- prior Room history is never injected wholesale merely because the same persistent agent previously saw it;
- the initial implementation should reuse the existing durable `context_event_ids` Assignment field and prior public terminal result events rather than introduce a separate memory database, summarizer, embedding index, or provider-thread archive;
- D-009 remains the longer-range direction. A broader searchable archive/index should be added only when ordinary use demonstrates that bounded recent/lexical result retrieval is insufficient.

This decision extends D-032 by supplying deliberate continuity across Assignment boundaries without redefining persistent A/B/C identity or undoing provider-context isolation.

**Principle:** **Retrieve the prior result the work needs; do not replay the history the agent once happened to see.**



### D-034 — Work-model v2 becomes the public default by clean cutover
**Date:** 2026-09-16
**Status:** ACTIVE

After I-015 Stage D passed the preregistered viability gate, the principal approved activation of the version-2 task-transaction architecture as Codex Room's normal public work model.

Settled cutover boundary:

- new Rooms created through the product/API use work-model version 2 with `provider_context_mode="assignment_thread"`;
- later staged Rounds and New Topic work created through the product/API use the same v2 + assignment-thread configuration;
- rollover successor opening Rounds use the same public v2 configuration;
- the public API does not offer work-model version 1 as a selectable production mode after cutover;
- legacy Rooms will be deleted rather than converted, so no Room-history migration or reinterpretation layer is required;
- historical v1 implementation paths and deterministic fixtures may remain internally where removing them provides no immediate product value; their continued presence does not make v1 a supported public operating mode;
- legacy historical evidence remains historical evidence and is not rewritten;
- activation must still pass the repository-standard deterministic verifier on the exact activation bytes before merge and ordinary use.

This decision completes the product-direction question left open by D-030 through D-033 after Stage D. It does not authorize unrelated v1-code cleanup merely for tidiness.

**Principle:** **Stage-D-proven transaction semantics are the production path; do not spend migration complexity on Rooms we intend to delete.**

### D-035 — C sequences dependent work and allocates substantial fallback to low-context capable assignments
**Date:** 2026-09-16
**Status:** ACTIVE

Ordinary Common Cause implementation exposed a coordination-economics failure that is not adequately addressed by peer-count limits or differentiated delegation alone. C may choose distinct assignments that are individually sensible yet still waste cognition if they are launched before their prerequisite results exist, and C may later absorb expensive fallback onto an already accumulated coordination context.

Settled coordination policy:

- before delegating multiple assignments concurrently, C must determine whether each assignment can produce a useful result without another assignment's output;
- genuinely independent work should remain parallel;
- work whose useful completion depends on a prerequisite artifact, evidence, or result should be sequenced after that prerequisite exists;
- verification of an artifact should not be treated as concurrent with creation or modification of that same artifact unless the peer assigned verification has meaningful independent work it can complete before the artifact exists;
- when delegated implementation, correction, or investigation fails to produce needed work, **or when fallback work reaches C because another assignment failed or settled without producing it**, C should normally place substantial tool-heavy execution in a fresh bounded peer assignment rather than perform it itself;
- that fallback rule applies whether C is acting in its root coordination assignment or in a child assignment created by a peer;
- when choosing where fallback should run, prefer the capable assignment with the least unnecessary accumulated context rather than automatically using the coordinator's already-large context;
- C may still execute directly when the work is demonstrably small in expected execution and context cost, urgent, inseparable from integration, or no fresh peer is likely to perform it reliably at lower total cost;
- a code/file change that looks small does not by itself establish that model execution will be cheap;
- correctness, safety, continuity, and reliability remain controlling constraints and override context-cost minimization;
- the rule is domain-general and does not make A a permanent implementer or B a permanent verifier in cognitive terms. Assignment responsibility is chosen from the task;
- the rule does not weaken A/B/C peer judgment and does not give C authority over conclusions.

The implementation is intentionally an instruction-level coordination refinement rather than a new CORE scheduler or persistent role system. PR #109 introduced dependency-aware sequencing plus the first context-aware fallback rule. PR #110 tightened the fallback wording so it covers substantial fallback reaching C from any failed/empty delegated path, including C child assignments, and replaces the earlier weaker “consider another bounded peer” wording.

Adoption boundary: the refined protected C structural instructions apply to **freshly composed Rooms going forward**. Existing Room snapshots are not retroactively rewritten. Rollover successors retain predecessor instructions unless a later deliberate mechanism changes that behavior.

Behavioral compliance remains an evidence question. Exact instruction regression/PR verification proves composition rather than universal compliance. E-125 later supplied naturalistic support for dependency-aware sequencing, and E-126 naturally exercised the tightened failed-delegation fallback successfully. Continue ordinary-use monitoring; Development Control owns current status and sequencing.

**Principle:** **Parallelize independence; sequence dependencies; put substantial fallback where capable cognition has the least unnecessary accumulated context.**

### D-036 — Round completion policy separates bounded activity settlement from standing objectives
**Date:** 2026-09-18
**Amended:** 2026-09-18 by D-037
**Status:** ACTIVE

Codex Room needs an explicit lifecycle distinction between an ordinary Round that should finish when its work settles and a standing Round objective that should remain active until the human or a hard runtime boundary stops it.

Settled boundary:

- every Round has an explicit `completion_policy`;
- `auto_settle` is the default and preserves ordinary transaction behavior: when the coordinator completes/passes, no transaction work remains, required contributors are satisfied, and no other settlement blocker applies, the Task may settle and the Round may close normally;
- `continuous` is an explicit per-Round policy for standing objectives such as `Stay busy.`;
- in `continuous` mode, child Assignments still complete normally and remain bounded by their own instructions;
- when the task coordinator reaches the ordinary settlement boundary with no open Assignments/Joins and no missing required contributor, CORE requeues that same coordinator Assignment instead of settling the Task, provided the hard turn limit has not fired;
- reusing the same coordinator Assignment preserves its assignment-scoped provider `context_thread_id`; CORE does not create a fresh coordinator Assignment for every bounded activity;
- `COMPLETE` or `PASS` therefore ends the coordinator's current bounded activity but does not by itself terminate a continuous Round;
- the Round objective remains authoritative on each resumed coordinator execution; CORE should not reinterpret a standing objective as “enough has been done” merely because one bounded activity finished;
- manual human stop, the hard Round turn limit, and genuine runtime boundaries remain valid termination mechanisms;
- continuous behavior is not a global default and does not change ordinary `auto_settle` Rounds.

This decision changes Round lifecycle semantics only. It does not change A/B/C epistemic status, delegation authority, child-assignment scope, or the public work-model-v2 transaction structure.

**Principle:** **Bounded activity can finish without finishing a standing objective; continuity must be explicit, mechanical, and still bounded by human/runtime stop conditions.**



### D-037 — Task is the bounded objective; provider context follows deliberate objective continuity
**Date:** 2026-09-18
**Amended:** 2026-09-18 — coordinator refresh economics guidance after naturalistic adoption evidence
**Status:** ACTIVE

The principal approves the bounded-context architecture synthesized after the naturalistic continuous-Round acceptance and subsequent CORE mapping.

The existing work-model-v2 **Task** is the bounded objective/activity unit. No new persistent Objective entity is authorized. A Round may contain one or more causally linked Tasks; Assignment remains the declared unit of agent work inside a Task, and Join remains the dependency/return mechanism.

Settled architecture:

- **Round scope:** the Round carries the human-facing objective/lifecycle. An ordinary `auto_settle` Round may still close when its bounded Task settles. A `continuous` Round keeps the standing Round objective active across multiple bounded Tasks until human stop, hard turn limit, or another genuine runtime boundary.
- **Task scope:** each bounded activity/objective has its own Task. In continuous mode, when the coordinator reaches the ordinary settlement boundary with no open Assignments/Joins and no missing required contributor, that Task should settle. If the Round remains active, CORE should create a successor Task linked through existing Task lineage instead of reopening the settled Task.
- **Coordinator continuity:** successor Tasks in one continuing Round may deliberately carry C's provider-context lineage forward so C retains organizational continuity across bounded objectives. This continuity must be explicit and provenance-preserving; it does not make the provider thread the authoritative work state. A later deliberate C checkpoint/refresh may end that lineage and start a fresh C context.
- **Worker objective-local continuity:** A/B provider context should be retained only for useful causally continuous work inside the same bounded Task, including implementation/verification/repair/re-verification loops. A new unrelated Task starts fresh worker context by default. Different Assignments therefore may share provider context only through an explicit same-objective context lineage; mere common agent identity is insufficient.
- **Direct result return:** nested delegation must support an explicit structured way for a child that now holds the required finished result to return it directly to the Task coordinator when the intermediate parent has no material intellectual work left. CORE must not infer relay bypass from prose. The mechanism must preserve settlement validity, provenance, and parent/Join terminal state.
- **Coordinator awareness:** C should receive compact authoritative Task/Assignment/Join status sufficient for coordination without automatic replay of worker transcripts or intermediate tool chatter.
- **Worker-context grace:** after a Task completes, its worker contexts remain eligible for deliberate continuation for **two subsequent C turns**, ending sooner if C explicitly moves past that objective. After the grace expires, those worker contexts should be retired so unrelated later work starts clean.
- **Historical continuity:** bounded `HISTORY` retrieval should be able to recover relevant completed Task results from earlier Tasks in the same Round as well as prior Rounds, while retaining explicit bounds, same-Room authority, and exact event provenance. Current Task/Assignment/Join/Evidence state remains authoritative.
- **C checkpoint/refresh:** coordinator refresh is a separate lifecycle mechanism. A refresh preserves a free-form C continuity checkpoint plus deterministic current organizational state, starts a fresh C provider context, and avoids wholesale transcript replay. After ordinary naturalistic use showed that C did not refresh even as its coordinator execution input load rose above 100K tokens, the principal approved deterministic self-telemetry plus advisory refresh guidance. Eligible root-coordinator turns receive exact-thread completed-execution economics. A last completed coordinator execution at roughly **64K input tokens** is an advisory point to actively consider `REFRESH` at the next clean bounded Task boundary; roughly **96K input tokens** is an advisory point to strongly prefer `REFRESH` unless a concrete continuity/integration reason justifies deferral. These ranges guide C's judgment only: they are not context-window occupancy claims and CORE must not auto-refresh solely because a numeric range is crossed. A successful refresh establishes a new provider-thread baseline.
- **Memory horizons:** worker active context, coordinator continuity context, and durable deterministic transaction/evidence state are distinct horizons. Persistent A/B/C identity remains application-level organizational state.

This decision **amends D-032**: Assignment remains the default first bounded provider-context unit, while explicit same-objective/coordinator continuity may carry one provider context across multiple Assignments or successor Tasks when that continuity is deliberate and bounded.

This decision **amends D-033**: bounded history retrieval remains explicit and provenance-preserving, and its eligible completed-result domain may include earlier completed Tasks in the same Round as well as earlier Rounds.

This decision **amends D-036**: the standing-objective distinction and explicit `continuous` policy remain active, but continuous mode should no longer preserve continuity by indefinitely requeueing the same Task/coordinator Assignment. The intended successor mechanism is bounded Task settlement followed by a successor Task while the Round remains active.

Implementation was deliberately divided into BCTX-1 through BCTX-4 so the design could be verified in bounded slices without a broad transaction rewrite. Those four slices subsequently completed and were exact-version verified; E-132 through E-139 record implementation and naturalistic refresh-economics evidence. The D-037 architecture remains active.

**Principle:** **Bound the objective in durable Task state; carry provider context only across continuity that the work actually needs.**

### D-038 — Private principal consultation is an explicit C-only transaction wait/resume primitive
**Date:** 2026-09-19
**Status:** ACTIVE

The principal authorized a private human↔coordinator channel so Agent C can request judgment, authorization, or material clarification from the human principal without invoking, delivering to, or otherwise involving Agents A or B.

Settled boundary:

- work-model v2 gains a structured nonterminal `CONSULT_PRINCIPAL` action;
- the initial authority is deliberately **C-only** and valid only from C's root coordinator Assignment. It is not a general hidden A/B side channel;
- the consultation message is a durable private observer event with no A/B delivery, no peer wakeup, and no generic agent-readable/turn-triggering semantics;
- `CONSULT_PRINCIPAL` moves the same C Assignment into durable `waiting_principal` state rather than completing it or creating a new Task;
- the principal replies to the exact consultation event. CORE binds that reply atomically to the exact waiting Assignment, rejects stale/duplicate replies, and requeues the same Assignment on its existing provider-context lineage;
- the principal reply is likewise private, creates no normal agent delivery, and is injected only into the resumed C Assignment;
- a pending consultation survives process restart because the wait is durable transaction state; Pause may retain the wait, while Stop/cancel terminates it with the surrounding transaction lifecycle;
- private consultation does **not** silently become shared organizational knowledge. If A or B later need a consequence of the private exchange, C must deliberately communicate only the necessary shared consequence through normal transaction work;
- the first implementation does not add a nonblocking private notification action. If ordinary use later demonstrates a need for “tell the principal without waiting,” that should be a distinct semantic rather than overloading consultation.

This extends D-030/D-037 without changing the fixed three-agent organization or C's epistemic status. The human principal remains outside the A/B/C production-agent set; C controls coordination, not judgment, and consultation exists to obtain human authority rather than replace it.

**Principle:** **Ask the principal privately when human judgment is needed; preserve the same work context, involve no peer implicitly, and promote only necessary consequences back to shared state.**

### D-039 — C controls dynamic cognition within an ordinary ceiling; exceptional C cognition requires Task-scoped principal approval
**Date:** 2026-09-19
**Status:** ACTIVE

The principal authorized Agent C to allocate its own execution cognition dynamically rather than remaining fixed at Terra/high, while preserving a human approval boundary for exceptional spend.

Settled boundary:

- the ordinary autonomous execution set is Low, Medium, and High reasoning on each admitted current-generation model: Luna, Terra, and Sol;
- C may select among those nine ordinary configurations for its own subsequent executions and for bounded peer Assignments, using the cheapest configuration it reasonably expects to be sufficient;
- C's self-selection is explicit and auditable transaction state, not an automatic CORE model router. CORE enforces the allowed set and executes C's declared next configuration;
- the existing Terra/high compatibility fallback remains the initial/default execution when no explicit Assignment configuration has yet been selected;
- Sol/XHigh and Sol/Max are exceptional **C-only** cognition levels. A/B may not receive them through ordinary delegation;
- exceptional cognition requires C to use the private principal channel and request a specific Task cognition ceiling, with a concise reason it would materially help;
- approval is bound to the exact current bounded Task. It raises C's available ceiling for that Task but does not force every C execution to use the ceiling; C may continue to choose cheaper configurations and may downgrade at any time;
- approval for Sol/XHigh does not authorize Sol/Max. C must request a higher Task ceiling separately if later evidence warrants Max;
- approval expires automatically when the Task settles, fails, or is cancelled. A successor Task begins again with the ordinary Sol/high ceiling;
- a declined request resumes the same C Assignment without raising the Task ceiling;
- Sol/Ultra is excluded because the provider-defined mode includes automatic task delegation, which conflicts with Codex Room's explicit inspectable A/B/C delegation architecture;
- Astra remains prohibited by D-028 at every effort level; GPT-5.5 remains excluded as a retiring previous-generation model;
- service-tier/priority speed remains outside this cognition policy.

This decision narrows the previously deferred “dynamic model routing” question: **automatic CORE routing remains unauthorized**, while deliberate C-controlled self-allocation is authorized as part of C's coordination responsibility. C controls coordination and cognition spend, not truth or peer judgment.

**Principle:** **C may spend ordinary cognition autonomously; exceptional C cognition requires explicit human authority for the bounded Task that needs it.**

### D-040 — Human-facing Codex command inventory follows the exact running runtime and fails closed on mismatch
**Date:** 2026-09-19
**Status:** SUPERSEDED BY D-041

The principal authorized a trustworthy command-surface foundation before any Codex Room command-selection UI is built.

Settled boundary:

- the authoritative built-in command inventory must be bound to the **actual running Codex App Server version**, not merely Codex Room's Python dependency declaration;
- when App Server exposes no native host-command catalog API, Codex Room may derive the built-in inventory from the exact matching official `openai/codex` release source and cache it with runtime version plus upstream source provenance;
- a cached catalog from another runtime version must never be silently displayed as current;
- if exact-version authority cannot be established, the command catalog must fail closed as unavailable rather than presenting stale commands;
- dynamic command families such as model service-tier commands remain live runtime/model-catalog overlays and must not be falsely frozen into the static built-in manifest;
- if App Server later exposes a native authoritative command-catalog API, prefer that capability over maintaining a parallel source parser;
- **current in Codex** and **appropriate/executable in Codex Room** are separate questions. Future UI/dispatch work must preserve Room governance rather than assume every Codex host command should execute unchanged;
- this decision does not authorize blanket Codex Desktop host-command parity. It establishes freshness/provenance for whatever command surface Codex Room deliberately exposes.

The first CORE slice implementing this rule was exact-head verified at `466fdb39cc60dd99fd3cd690061ab2feaea67c8d`; see E-150. UI and dispatch remain separate unfinished work.

**Principle:** **Never present a command catalog from a different Codex runtime as though it describes the one actually running.**

### D-041 — Codex host-command catalog is not a Codex Room product surface
**Date:** 2026-09-19
**Status:** ACTIVE

After reviewing the official Codex host-command inventory against Codex Room's product model, the principal reversed the earlier command-catalog direction.

Settled boundary:

- Codex Room does not expose an exact-runtime Codex host-command catalog in Status & Tools or through a dedicated public API;
- the source parser, runtime cache, catalog endpoint, Status & Tools catalog card/payload, and dedicated catalog tests are removed rather than hidden behind a flag;
- Codex Desktop/TUI command parity is not a Codex Room objective. Host-specific controls should not be surfaced merely because they exist in Codex;
- App Server runtime identity may remain available where it serves generally useful runtime provenance independent of any command catalog;
- inherited Codex capabilities may still be inspected or used through their underlying App Server/runtime facilities when they are genuinely useful and compatible with Room governance;
- further work on Codex skills is deferred for later evaluation rather than coupled to this cleanup.

D-040 remains historical provenance for the earlier experiment but no longer governs current product behavior.

**Principle:** **Expose useful underlying capability, not another host's command surface.**


### D-042 — Native Codex skills are the first-line reusable workflow layer; D-022 remains the stronger governed capability tier
**Date:** 2026-09-20
**Status:** ACTIVE

I-020 established the practical boundary between Codex's native skill ecosystem and Codex Room's registered deterministic-capability system.

Settled direction:

- when an existing enabled Codex skill materially fits the work, A/B/C should prefer that native skill before inventing a new reusable workflow or Codex Room capability, while still considering whether the skill's workflow/tool cost earns its value unless the principal explicitly requests that skill;
- when a reusable workflow is genuinely missing, agents should prefer native Skill Creator and keep agent-created skills Room-local under `.agents/skills/` by default;
- a Room-local skill may contain bounded deterministic helper scripts when they improve reliability or avoid repeatedly spending model cognition on the same mechanical step;
- valid Room-local skill packages are lineage-local Room assets: they survive Room rollover at exact inherited bytes with deterministic tree-hash provenance, but they are not silently promoted into user-global, administrator, Personal, or CORE scope;
- native skills, Skill Creator outputs, and skill-local scripts are not equivalent to registered Codex Room deterministic capabilities. Registration remains the stronger tier for mechanisms that materially require typed contracts, declared permissions/side effects, exact implementation identity, deterministic verification evidence, durable execution/provenance semantics, independent reusable invocation, or stronger institutional promotion/lineage guarantees;
- therefore agents should promote/register skill machinery as a Codex Room deterministic capability only when those stronger guarantees materially earn the additional governance cost;
- Codex Room does not maintain a parallel skill catalog, copied Desktop/TUI skill picker, or Room-specific `SkillInput` invocation bridge while native discovery/selection/invocation remains adequate;
- creating or modifying user-global or administrator-scope skills requires explicit principal authorization;
- Codex built-in subagents remain disabled; skill workflows that call for independent cognition use the existing A/B/C organization when independent review is warranted.

D-042 **clarifies rather than supersedes D-022**. D-022 remains active for the registered deterministic-capability substrate and its stronger governance/continuity contract. Its direction that agents may create and register deterministic software when useful is now applied after the native skill layer has been considered. I-020 E-153 through E-155 provide the implementation and behavioral evidence for this boundary.

The resulting default hierarchy is:

**existing suitable Codex skill → Skill Creator for a missing reusable workflow → bounded skill-local deterministic helper when sufficient → registered Codex Room capability when stronger institutional guarantees are justified.**

**Principle:** **Reuse native Codex capability first; add Codex Room governance only when the stronger guarantees earn their cost.**

### D-043 — Plugin administration remains a native Codex/ChatGPT host responsibility
**Date:** 2026-09-20
**Status:** ACTIVE

After I-021 Stage A established the native Codex 0.154 plugin contracts and showed that Codex Room localhost is reachable from an A/B/C-equivalent workspace sandbox, Stage B resolved the product boundary without adding a Room mutation bridge.

Settled direction:

- the principal manages plugin discovery, installation, removal, enablement/disablement, marketplace administration, and required app/account authorization through native Codex/ChatGPT plugin surfaces when those surfaces are available for the account/workspace;
- Codex Room remains a consumer and visibility surface for the resulting native state: it may inspect installed/enabled/availability/auth status, expose that state through Status & Tools, and let A/B/C use inherited plugin-derived skills/MCP/apps under existing Room policy;
- Codex Room does not create a principal-only plugin mutation endpoint, copied plugin manager, parallel marketplace/registry, generic Codex configuration editor, credential store, OAuth proxy, or new authentication/security subsystem solely to reproduce controls already provided by the native host;
- A/B/C may recommend that the principal install, enable, disable, or authenticate a plugin, but plugin-state administration remains an external principal action and is not an autonomous Room-agent capability;
- Codex/App Server remains authoritative for plugin/catalog/configuration state. Room should re-read authoritative inventory after native changes rather than mirror or predict plugin state;
- plugin installation/enablement does not relax the separate boundary that Codex built-in subagents remain disabled and that use of plugin-contributed cognition/tools remains subject to existing Room governance and economics;
- I-021 may be reopened only if ordinary use demonstrates a concrete material capability, reliability, or workflow-cost gap caused by native-host administration. Any future Room-side mutation design would still require a mechanical principal-proof boundary because E-158 disproved localhost as sufficient authority.

This decision deliberately accepts a host transition for infrequent administrative actions in exchange for avoiding duplicated product surface and a security mechanism whose only current purpose would be to reproduce native plugin controls.

**Principle:** **Administer plugins where Codex already owns them; let the Room inherit, inspect, and use the resulting capability state.**

### D-044 — Canonical GPT Project runtime instructions live in the repository
**Date:** 2026-09-20
**Status:** ACTIVE

The principal moved Codex Room's maintained ChatGPT Project operating instructions from the size-constrained GPT Project UI field into the canonical repository.

Settled boundary:

- `docs/project/01_GPT_PROJECT_RUNTIME_INSTRUCTIONS.md` on canonical `main` is the maintained authority for Codex Room's project-specific ChatGPT runtime guidance;
- the GPT Project UI custom-instructions field becomes a compact bootstrap/fail-safe whose primary duty is to retrieve and follow `01` at the first substantive Codex Room turn in each new chat;
- the UI bootstrap preserves only enough invariant guidance to fail safely if repository retrieval is unavailable; it is not a second independently maintained full instruction set;
- `01` owns stable operating rules such as source loading, A/B/C identity, evidence discipline, development governance, token economics, repository workflow, and principal command procedures;
- volatile priority/status remains in Development Control and must not migrate into `01`;
- stale attachments, memories, exports, handoffs, summaries, and prior-chat copies do not replace canonical repo instructions when repository access exists;
- changes to Project runtime guidance are made in the repository first, reviewed/versioned there, and then reflected in the UI bootstrap only when the bootstrap itself must change.

This removes the recurring need to compress or reconstruct the full instruction set in every chat and makes instruction changes reviewable through ordinary Git/GitHub provenance.

**Principle:** **Bootstrap from the UI; maintain the real instructions once, in the canonical repository.**

### D-045 — PBM is the canonical performance benchmark and “Run PBM” is its standard invocation
**Date:** 2026-09-20
**Status:** ACTIVE

The standardized Codex Room versus Codex Desktop performance benchmark is named **PBM**, short for **Performance Benchmark**.

Settled invocation contract:

- **PBM** is the canonical name of the benchmark;
- the principal phrase **“Run PBM”** means to initiate the current canonical PBM procedure rather than invent a new benchmark design;
- PBM is versioned. A material change to tasks, fixtures, controls, scoring, or measurement semantics requires a new benchmark version rather than silently changing the historical yardstick;
- the canonical PBM definition and harness must live in the repository so a new chat can determine exactly what “Run PBM” means without relying on memory or prior-chat text;
- PBM should use deterministic setup, usage capture, aggregation, acceptance checks, and reporting wherever practical; paid model cognition should be reserved for the benchmark tasks themselves;
- PBM execution is split by product surface: a dedicated Desktop script prepares/captures the native Codex Desktop arm, a dedicated Room script prepares/drives/captures the Codex Room arm, and shared deterministic code may handle only common manifest/fixture/grading/accounting/reporting mechanics; the Desktop arm must not be replaced by CLI execution and the Room arm must not be impersonated by Desktop;
- PBM compares Codex Room and ordinary Codex Desktop under standardized paired conditions and must preserve quality/correctness alongside usage, rather than declaring a cheaper failed result more efficient;
- implementation/verification status for each PBM version belongs in Development Control and Evidence; the naming/invocation contract remains stable across versions.

**Principle:** **“Run PBM” invokes a versioned standard; it does not redesign the test.**

### D-046 — PBM v2 adds contextual baseline snapshots while preserving v1 task assets and primary accounting
**Date:** 2026-09-20
**Status:** ACTIVE

Before the first live PBM run, the principal required standardized baseline information that would make final performance results easier to interpret.

PBM v2 therefore changes the **measurement/context protocol**, not the task workload:

- PBM v1 remains frozen and reproducible as an explicit historical version;
- PBM v2 inherits the exact eight v1 prompts, fixtures, graders, paired order, and naturalistic Desktop-versus-Room comparison;
- the v2 fingerprint binds both the v2 protocol bytes and the referenced frozen v1 asset bytes;
- v2 captures read-only **run-start**, **task-pair pre**, **task-pair post**, and **run-end** context snapshots;
- snapshots record repository/environment provenance, safe Codex runtime/config/capability state, native `account/rateLimits/read`, and native `account/usage/read` when available;
- sensitive account identity and credential fields are removed before snapshot persistence;
- unavailable native context reads are recorded as unavailable with an error type rather than fabricated;
- rollout-derived Desktop usage and durable Room execution-economics remain the **primary performance accounting**; account/rate-limit snapshots are contextual/corroborating evidence only;
- PBM's naturalistic Room arm must preserve D-039 dynamic cognition: the benchmark may record Room defaults and actual execution choices but must not pin C/A/B to one model/effort merely for symmetry with Desktop; ordinary D-039 model/effort switching remains part of the product behavior being measured;
- snapshot collection must not purchase model cognition;
- the unqualified **“Run PBM”** invocation resolves `benchmarks/pbm/CURRENT`; once v2 is verified and promoted, that invocation uses v2.

**Principle:** **Measure the work directly; snapshot the surrounding account and environment state so the direct measurement can be interpreted.**

### D-047 — PBM v3 uses one initial principal instruction per platform while preserving fresh task contexts
**Date:** 2026-09-20
**Status:** ACTIVE

The principal selected a lower-friction PBM operating model: one initial instruction in Codex Desktop and one initial instruction in a dedicated Codex Room controller, rather than repeated prompt/PowerShell choreography for all sixteen benchmark arms.

Settled PBM v3 boundary:

- PBM v1 and v2 remain frozen and explicitly reproducible;
- PBM v3 inherits the exact frozen v1 eight-task workload and v2 contextual snapshot/accounting semantics;
- the principal opens Codex Desktop on the dedicated `pbm_desktop_controller` folder and gives one instruction to read/execute `DRIVER.md`;
- Desktop's controller conversation is coordination-only and must create a **fresh separate native Codex task** for every Desktop benchmark arm;
- exact Codex 0.154 task creation inherits the controller working directory, so only one current task fixture/instruction is staged in that dedicated controller folder at a time;
- the Desktop controller must use native task management. PBM v3 has **no Codex CLI fallback** and fails closed before paid task execution if native fresh-task creation/wait functionality is unavailable;
- native approval dialogs remain ordinary platform controls and may require human approval without counting as new benchmark prompts;
- PBM creates one dedicated controller Room, stages its driver files, and starts its Round with C explicitly instructed to enter a private `CONSULT_PRINCIPAL` wait without benchmark work;
- the principal's one Room paste is the private consultation reply instructing C to read/execute `PBM_ROOM_DRIVER.md`;
- that Room is coordination-only. After the reply, C launches deterministic background orchestration which creates a **fresh ordinary Room** for every Room benchmark arm;
- each benchmark Room retains D-039 naturalistic dynamic cognition; PBM records rather than pins C/A/B model/reasoning choices;
- the v1/v2 alternating Desktop-first/Room-first task order is preserved exactly;
- controller cognition is reported separately from task execution usage, and an all-in usage view is also retained;
- v3's benchmark fingerprint binds both the inherited task assets and the v3 orchestration implementation so controller-mechanics changes cannot silently change historical v3 semantics.

**Principle:** **One human instruction per platform; fresh measured task context per arm; controller overhead visible, never hidden.**

### D-048 — PBM v4 uses two independent complementary one-paste harnesses
**Date:** 2026-09-20
**Status:** ACTIVE

The principal superseded PBM v3's cross-platform alternating controller after the first substantial live run exposed protocol and benchmark-integrity failures. The next canonical PBM version must use **two independent complementary one-paste harnesses**: one native Codex Desktop benchmark and one ordinary Codex Room benchmark.

Settled boundary:

- PBM v1, v2, and v3 remain frozen historical versions; v3 is not approved for another live performance run;
- Desktop and Room do **not** coordinate with, wait for, wake, or control one another during measurement;
- each platform receives exactly **one principal benchmark instruction** in one fresh measured execution context;
- Desktop uses one fresh top-level native Codex Desktop task rooted at its prepared benchmark workspace;
- Room uses one fresh ordinary production Room with C as coordinator and the normal Personal A/B/C architecture;
- both platforms receive the same frozen integrated mission, equivalent starting fixture, and the same external deterministic grader;
- the integrated mission must exercise a representative mix of repository investigation, bug diagnosis/repair, feature implementation, specification/constraint handling, evidence-backed design judgment, verification, and final synthesis without depending on an internally contradictory requirement;
- Room retains ordinary naturalistic coordination and D-039 cognition behavior; C may delegate to A/B as normal, but the measured Room must not consult the principal for substantive benchmark guidance;
- no follow-up human guidance is permitted during either measured execution. Native approval dialogs may remain ordinary platform controls when they do not supply benchmark substance;
- deterministic preparation, capture, grading, validity classification, status, abort, evidence bundling, and comparison happen outside the measured cognition sessions;
- each platform result is classified explicitly as **VALID**, **INVALID**, or **FAILED**. Human benchmark intervention, substantive principal consultation, protocol deviation, or disallowed terminal state must not silently enter comparative aggregates;
- Desktop and Room results are compared only after both independent runs are complete and share the exact benchmark fingerprint;
- before any full paid v4 comparison, the mission/specification and grader must be audited together for satisfiability and coverage, and a real end-to-end delayed canary must exercise the actual native execution boundaries rather than only unit-testing the state machine.

**Principle:** **One frozen mission; one paste into Desktop; one paste into Room; no live cross-platform orchestration; deterministic comparison afterward.**

### D-049 — PBM v4 has one common protocol with thin platform adapters
**Date:** 2026-09-21
**Status:** ACTIVE
**Supersedes:** D-048 only where D-048 described the principal directly pasting into each measured execution

The principal clarified the PBM operator requirement after the first v4 canary attempt: the human should point Desktop or Room at a named process once and the platform should perform the rest of its own procedure. Desktop and Room may require different native initiation mechanics, but those differences must be thin adapters around one common benchmark protocol rather than separate substantive procedures.

Settled boundary:

- PBM v4 has one normative common protocol governing version/fingerprint binding, mission/fixture equivalence, fresh measured execution, no substantive follow-up guidance, grading, validity classification, evidence capture, bundling, pairing, and deterministic comparison;
- the principal gives exactly one **controller initiation** per platform; the controller is outside measured benchmark cognition;
- Desktop's adapter uses native fresh-task creation, then hands the exact child thread id to a detached deterministic monitor; the controller model does not remain alive as a polling loop, and the monitor waits only for its own measured child evidence;
- Room's adapter may launch a detached deterministic worker that creates and waits only for its own fresh measured Room;
- neither adapter may wait for, wake, control, or coordinate with the other platform;
- the deterministic protocol layer automatically binds independent arms to the same active pair and fingerprint, so the principal does not shuttle run ids or intermediate commands between products;
- preparation, capture, grading, validity checks, evidence bundling, and pair finalization are normal protocol responsibilities, not principal chores;
- `status`, `abort`, and explicit `bundle` remain recovery/diagnostic operations, not the ordinary operator workflow;
- the canary must use the same controller/adapters and native boundaries as production benchmark mode, substituting only the bounded canary mission;
- controller cognition is not charged as measured task cognition; if reported for economics, it must remain visibly separate;
- Desktop prompt/provenance validation must tolerate supported Codex rollout-schema versions rather than treating one legacy record representation as the protocol itself.

**Principle:** **One common protocol; one principal initiation per platform; only native platform entry mechanics differ; the platform performs the procedure.**



### D-050 — PBM compares platform outcomes, not prescribed internal orchestration
**Date:** 2026-09-21
**Status:** ACTIVE
**Supersedes:** D-049 where D-049 prescribed Desktop controller → one child → detached-monitor choreography; preserves D-049's common mission, deterministic evidence, no-substantive-principal-guidance, and automatic comparison principles

The principal clarified the intended PBM abstraction boundary after the first paid v4 attempt exposed a managed-worktree failure in the prescribed Desktop child-task path.

Settled boundary:

- the comparison unit is the **platform**, not a harness-selected internal agent topology;
- Desktop and Room receive the same frozen mission, equivalent starting fixtures, the same success criteria, and the same graders;
- after measured work begins, the principal supplies no substantive guidance;
- each platform is free to sequence, parallelize, delegate, create subagents/peers, or work directly using its native capabilities;
- PBM must not prescribe the number of internal agents, their identities, their working directories, their delegation topology, or the order in which they work;
- Desktop measurement includes the fresh top-level measured task plus all native descendant tasks attributable through rollout parent lineage;
- Room measurement includes the complete measured Round across all participating A/B/C executions;
- validity depends on the prepared starting boundary, final required outputs, prompt/intervention integrity, complete usage evidence, and deterministic grading—not on whether either platform used a particular internal workflow;
- internal orchestration remains observable provenance and measured cost;
- because this materially changes benchmark control semantics after v4 promotion evidence was recorded, the corrected protocol is versioned as **PBM v5** while reusing the frozen v4 seven-task battery and graders;
- PBM v4 remains frozen and reproducible as the promoted predecessor; no paid seven-task v4 comparison was completed.

**Principle:** **Give each platform the same job and judge the result; let the platform decide how to do the work.**

### D-051 — Astra is default-denied but may be authorized by the opening Room prompt
**Date:** 2026-09-24
**Status:** ACTIVE
**Supersedes:** D-028

The principal replaced D-028's blanket Astra prohibition with an explicit opening-prompt opt-in.

Settled rule:

- Astra remains unavailable by default for Codex Room execution;
- the **opening Room prompt** may explicitly request Astra, including a participant/model direction such as `Agent A — Astra, Medium` or an instruction to use Astra;
- when that opening prompt explicitly authorizes Astra, the authorization is durable for the **entire conversation lineage**, including later turns, later bounded Tasks/Rounds, retries, and normal Room rollover successors;
- subsequent observer messages, agent messages, coordination policy, or autonomous routing may not grant Astra to a conversation lineage whose opening prompt did not authorize it;
- authorization makes Astra Low/Medium/High selectable through the ordinary C-controlled model-allocation surface; C must use Astra only where the principal's opening model directions call for it and must not expand Astra use to other participants merely because the Room is authorized;
- CORE must persist the authorization deterministically and fail closed at both coordination validation and provider-turn execution if Astra is attempted without it;
- Luna, Terra, and Sol retain their existing ordinary availability and D-039 economics/coordination rules;
- Sol/Ultra remains unavailable for its separate automatic-delegation reason, and Sol/XHigh / Sol/Max retain their existing C-only Task-scoped approval rules.

This makes the principal's opening Room prompt the authorization boundary. A new prompt later in the same unauthorized Room cannot unlock Astra; creating a new Room with an explicit Astra direction can.

**Principle:** **Astra requires explicit principal opt-in at conversation creation, and that opt-in persists with the conversation lineage.**

### D-052 — Same-Task worker continuity is the default and public Room conversation is supplied incrementally
**Date:** 2026-09-25
**Status:** ACTIVE
**Amends:** D-033 and D-037

Ordinary use exposed that D-033/D-037 had made worker context isolation too conservative for conversational multi-agent work. In a natural adversarial debate, later A/B Assignments repeatedly lacked already-public statements from the other participant and spent additional cognition requesting or reconstructing material that the Room had already recorded.

Settled boundary:

- for A/B work inside one active Task under production `assignment_thread` mode, CORE should automatically continue the worker's latest completed same-Task provider context when one exists;
- the durable `context_parent_assignment_id` continues to record the exact lineage source, and stale/forking provider-context reuse remains prohibited;
- a delegation may set `fresh_context=true` when independence, deliberate reset, or lower accumulated private/provider context is materially more valuable than continuity;
- `fresh_context=true` and an explicit `context_from_assignment_id` are mutually exclusive;
- explicit `context_from_assignment_id` remains available when an exact source must be named and remains required for bounded cross-Task worker-grace continuation;
- the first execution of each new A/B Assignment receives a bounded **public Room delta** covering public, agent-readable conversational messages published since the inherited worker context last settled, or since the Task began when the worker starts fresh;
- the public delta must exclude private principal content, private participant content, mechanical/lifecycle events, status telemetry, tool chatter, and other non-conversational runtime records;
- provider-context independence does not mean ignorance of shared public Room facts: even a deliberately fresh worker Assignment may receive the bounded public Room delta;
- the delta is injected only on the first execution of the new logical Assignment, so EVIDENCE/HISTORY/retry continuations on that same provider thread do not replay it;
- bounded `HISTORY` may select completed Assignment results from earlier work in the **current Task** as well as earlier settled Tasks in the same Round and earlier Rounds;
- C's coordinator-context rules, REFRESH economics, Task boundaries, and cross-Task worker-grace rules otherwise remain unchanged;
- a new unrelated Task still starts fresh worker context by default unless the existing explicit grace mechanism is deliberately used.

This retains assignment-thread isolation at real objective boundaries while restoring the basic conversational expectation that a participant can respond to public statements already made in the Room.

**Principle:** **Keep context bounded at objective boundaries, not at every conversational turn; preserve private/provider independence without making peers forget the public Room.**

### D-053 — Room creation may explicitly enable unrestricted native model access
**Date:** 2026-09-26
**Status:** ACTIVE
**Amends:** D-039 and D-051 only when the principal selects unrestricted model access; default Room behavior remains unchanged

The principal selected an explicit Room-creation control that preserves the existing bounded model policy by default while allowing a deliberately unrestricted Room when needed.

Settled boundary:

- New Room setup exposes an **Unrestricted model access** toggle, default **off**.
- With the toggle off, the existing model policy remains authoritative: ordinary bounded configurations, opening-prompt Astra authorization under D-051, and Task-scoped exceptional C cognition approval under D-039 continue unchanged.
- With the toggle on, the human principal grants advance authorization for Agent C to allocate any model/reasoning-effort combination that the current native Codex runtime exposes as available to agents, for A, B, or C.
- CORE must discover that catalog through native Codex model discovery rather than maintaining a separate unrestricted allowlist. The native model/effort catalog is snapshotted at Room creation, persisted with the Room, and used as the exact execution-validation boundary for that conversation lineage.
- Unrestricted mode removes Room-side Astra gates, peer-versus-C configuration restrictions, and Task cognition-ceiling approval requirements. It does not force expensive cognition: C retains coordination responsibility and should still choose configurations economically according to expected value.
- Native Codex availability remains the hard boundary. CORE requests the complete native `model/list` catalog, including entries Codex marks hidden; configurations absent from that native catalog or rejected by the provider are not emulated or inferred.
- Unrestricted creation fails closed if CORE cannot obtain a complete usable native catalog. A partial catalog must not silently masquerade as unrestricted access.
- The policy is creation-time lineage state rather than prompt interpretation. Later messages cannot switch a default Room into unrestricted mode.
- Normal rollover successors inherit the predecessor's model policy and exact snapshotted catalog so authorization/provenance remain deterministic.
- Room UI and exports must expose whether the lineage uses the default or unrestricted model policy.

**Principle:** **Keep economical restrictions as the default; when the principal explicitly opens the gate, let native Codex availability—not duplicated Room policy—define the model menu.**


### D-054 — Ordinary Rooms automatically capture account-level provider usage at measured work-cycle boundaries
**Date:** 2026-09-26
**Status:** ACTIVE
**Related:** D-005, D-019, D-046

Codex Room Personal should automatically record the native provider usage/rate-limit meter around ordinary Room work, using the same normalized semantics already employed by PBM.

Settled boundary:

- Measurement is read-only and applies to ordinary production Rooms independently of PBM.
- A measured cycle begins when Round work becomes active and ends when that work settles or is explicitly stopped/replaced; reopening/resuming previously completed work starts another cycle rather than overwriting the earlier one.
- Native `account/rateLimits/read` and `account/usage/read` are the source of truth when available. Room token totals are not substituted for provider allowance readings.
- Usage snapshots are durable mechanical state, not conversational events, and must not alter transcript sequence, agent readability, routing, or model choice.
- Exports expose the recorded before/after readings and derived deltas.
- A provider-window reset invalidates a simple percentage-point subtraction across that boundary; the reset must be represented explicitly instead of reporting a false negative delta.
- Provider meters are account-level. Concurrent Codex activity outside a Room can contribute to its observed before/after delta; therefore the value is an observed account-meter change over the Room interval, not guaranteed exclusive billing attribution.
- This decision does **not** activate D-019 pacing. No work is blocked or throttled from these readings until the separate mixed allowance/credit semantics required by D-019 are deliberately resolved.

**Principle:** **Measure every Room automatically, preserve the provider's meter semantics, and keep observation separate from enforcement.**

### D-055 — Agent C receives compact advisory model-selection guidance
**Date:** 2026-09-26
**Status:** ACTIVE
**Related:** D-039, D-051, D-053

The principal selected a compact descriptive guide so Agent C can understand the general character of available model families and reasoning-effort levels without turning that information into a routing policy.

Settled boundary:

- CORE may append a compact **advisory model-selection guide** to Agent C's model-policy prompt.
- The guide describes only model families and reasoning-effort levels that are already selectable under the current Room policy. It does not make an otherwise unavailable configuration available.
- The maintained known-family descriptions are intentionally short: Luna is fast/economical for focused bounded work; Terra balances capability, speed, and cost for general professional work; Sol is a high-capability model for complex professional work; Astra is the highest-capability model for especially difficult, ambiguous, or demanding end-to-end work.
- The maintained reasoning-effort descriptions are likewise compact: Low for efficient straightforward reasoning, Medium for balanced substantive reasoning, High for deeper difficult reasoning, and XHigh/Max for progressively greater reasoning investment where those efforts are actually selectable.
- The guide explicitly states that it is background information rather than a routing rule, ranking, threshold, or required escalation path. C retains independent cognition-allocation judgment and the existing economic expected-value duty.
- The guide is supplied to C only. A and B do not receive it because they do not own Room cognition allocation.
- In unrestricted Rooms, native `model/list` plus the persisted Room snapshot remain authoritative. A native configuration without maintained advisory text remains selectable; CORE must not invent capabilities or infer a ranking from an unknown model identifier.
- The advisory layer must not change model discovery, availability, Astra authorization, Task cognition ceilings, execution validation, persistence, rollover lineage, or provider execution.
- The guide deliberately omits quantitative prices, model scores, task-specific triggers, and escalation recipes that could turn descriptive context into an implicit router.

**Principle:** **Inform C's model judgment without replacing it.**
