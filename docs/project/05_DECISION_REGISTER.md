# Codex Room — Decision Register

**Initialized:** 2026-09-08  
**Last updated:** 2026-09-19  
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

This decision supersedes D-020 only where D-020 names **Implementer / Verifier / Integrator** as permanent agent-role descriptors. D-020's permanent-triad, C-first coordination, direct peer communication, selective invocation, and integration-before-closure requirements remain active.

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
**Status:** ACTIVE

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
- verification of an artifact should not be treated as concurrent with creation or modification of that same artifact unless the verifier has meaningful independent work it can complete before the artifact exists;
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
