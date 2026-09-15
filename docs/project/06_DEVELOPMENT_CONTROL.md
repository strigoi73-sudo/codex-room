# Codex Room — Development Control

**Last updated:** 2026-09-15  
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.  
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** The minimum Engineering Foundation, GPT Project review, D-020 permanent Personal triad / C-integration migration, **A2 — Assurance Pass 2**, **P4 — Deterministic Room and agent capabilities**, and the **A3 — Whole-system housekeeping, efficiency, and operational assurance audit plus its bounded remediation sequence** are complete. The repository baseline is canonical `main`; verify exact HEAD, applicable CI, and local Git state directly when consequential rather than maintaining those mechanically changing facts here.
- **What just changed?** Ordinary-use product evaluation exposed a broader coordination/economics recurrence after the I-014 repairs: one serious assessment spent 544,416 execution tokens before peer cognition and then announced it was waiting for A/B while emitting no runnable peer targets. A follow-up Room deliberately avoided rediscovery, correctly differentiated and invoked A/B, integrated both through the existing cohort barrier, and completed in 138,522 execution tokens total. The agents independently converged on the same architectural thesis: intellectual allocation should remain cognitive, but mechanical work state should be explicit and deterministic rather than inferred from conversational backlog. I-015 is now the active **design-only** stabilization investigation; no redesign implementation is yet authorized. See E-092 and E-093. The restart correction remains locally confirmed under E-091.
- **What is blocked?** D-019 daily usage pacing remains blocked on unresolved mixed subscription-allowance / purchased-credit semantics. The A3 remediation sequence is complete.
- **Where is P4?** **COMPLETE.** E-030 through E-040 contain the implementation/live-verification evidence across P4.1–P4.5.
- **What is next?** **I-015 — Task-transaction stabilization redesign** is IN PROGRESS as a design investigation prompted by demonstrated ordinary-use failures. Feature development is frozen for this investigation. The immediate deliverable is a concrete migration design and viability gate, not another prompt patch. I-003 remains a low-priority provider-side verification candidate, D-019 remains blocked, and no automatic model router is authorized.
- **What are we deliberately not doing?** No further personality calibration, blind recognizability testing, stronger personality prose, or attempts to force cognitive specialization through persistent identity unless ordinary usage demonstrates a concrete product problem.

## Current Focus

### I-015 — Task-transaction stabilization redesign
**Work state:** IN PROGRESS  
**Reality:** OBSERVED ISSUE / EXPLORATORY redesign  
**Evidence:** E-092, E-093  
**Scope:** [CORE], with later [CORE + ROOM migration] only if a redesign is approved.

Ordinary-use testing has now demonstrated that the remaining failure class is not adequately described as one bad prompt, one stale event, or one source-inspection footgun. The current runtime mixes intellectual coordination with mechanical work-state bookkeeping by using conversational events plus readable/runnable deliveries as both history and the scheduling substrate. That design has produced recurring variants of prose/action divergence, stale passive context, settlement ambiguity, and continuation amplification.

**Design objective:** preserve the permanent A/B/C organization and agent judgment while replacing implicit conversational work state with an explicit, inspectable transaction model.

Proposed state model:

1. **Task** — one bounded objective being advanced inside a Room/Round. A task owns its current work state, completion condition, and optional budget/context policy. A Round remains the user-visible conversational/lifecycle container; tasks become the work units inside it.
2. **Assignment** — one explicit unit of cognition assigned to one agent. It carries a task ID, target agent, bounded instruction, causal parent, execution configuration when applicable, selected context references, and a durable state such as queued / claimed / running / completed / passed / failed / cancelled / waived.
3. **Join** — an explicit dependency set over assignments. A join records which contributions are required before integration or settlement can proceed. CORE, not prose, determines whether the join is satisfied. Timeouts, failures, cancellation, and explicit visible waivers must be represented mechanically.
4. **Result** — the immutable outcome of an assignment, linked to the exact assignment and execution. Existing decision events and `agent_executions` can remain the durable result/provenance layer; a new standalone result table is not required unless implementation evidence shows one is necessary.
5. **Integration** — ordinarily another explicit assignment, usually to C, created deterministically when a required join becomes ready. Integration is therefore work, not a heuristic inferred from unread passive peer messages.
6. **Settlement** — a task-level terminal transition. A task may settle only when its explicit dependencies are resolved and the current integrating/owning assignment chooses a valid terminal action. Agent `READY_TO_FINISH` state should no longer carry task-completion semantics by itself.

**Important boundary:** C/A/B continue to decide intellectual questions: whether peers add value, whom to delegate to, how to frame work, what evidence matters, how to interpret disagreement, whether a waiver is justified, and what conclusion to reach. CORE owns only declared mechanics: assignment creation, causal delivery, joins, queue ordering, retries/budgets, context assembly, and whether a requested terminal transition is mechanically valid. CORE must not infer hidden intent from prose such as “I am waiting for A.”

**Structured-output direction:** the present `invoke_targets` field is a routing primitive, not a sufficient work contract. A transaction design should evaluate replacing or superseding it with explicit delegation records that atomically contain target + assignment + dependency semantics. Public/readable messages may remain events, but readable history should not itself become runnable work. This is a proposal, not a settled replacement of D-015/D-027.

**Current-to-proposed mapping:**

- preserve `rooms`, `rounds`, persistent A/B/C identities, profiles/overlays, workspaces, custom capability bindings, exports, observer event history, model policy, durable `agent_executions`, recovery/usage-wall machinery, and WebSocket/UI transport;
- preserve `events` primarily as audit/conversation history and exact provenance;
- stop using coalesced unread `deliveries` as the authoritative work queue for redesigned tasks; existing deliveries may remain for readable notification/history and legacy Rooms;
- replace `claim_next_batch()`'s “all pending conversational events through newest runnable trigger” semantics with assignment claiming for transaction-enabled work;
- replace passive-backlog prompt construction with an assignment envelope plus explicitly selected prerequisite context;
- replace event-derived multi-peer cohort detection with explicit joins;
- replace settlement heuristics based on agent status, FINISH boundaries, passive participation, and causal-message reconstruction with task/assignment/join state;
- retain existing execution durability: an assignment claim should still bind to one exact `agent_execution` and one exact SDK turn before side effects settle.

**Migration judgment:** this is **not a whole-product rewrite**. The durable product shell and much of the execution/provenance machinery are reusable. It is, however, a deliberate replacement of the scheduling/work-state kernel centered in `db.py` and `orchestrator.py`. Treating it as “just another patch” would understate the change. Legacy Rooms should remain readable/replayable under existing semantics; new transaction semantics should be introduced behind an explicit Room/task version or deliberate migration path rather than silently reinterpret old event history.

**Staged design path — do not collapse these into one implementation:**

- **Stage A — coordination transaction kernel:** Task/Assignment/Join state, assignment envelopes, deterministic join release, terminal-state validity, and removal of passive backlog as actionable work. Keep current persistent SDK thread behavior initially so coordination reliability can be isolated from context-economy changes.
- **Stage B — bounded evidence execution:** add a declarative evidence-plan path where a model states already-known searches/reads/bounds once, CORE executes the plan deterministically, and one normalized evidence bundle returns for cognition. Native exploratory tools remain available for genuinely adaptive investigation; planned retrieval should not require a model continuation per mechanical step.
- **Stage C — durable memory vs active context experiment:** test whether application-level persistent agent identity can be preserved with a compact versioned Room/task ledger plus targeted history/evidence instead of resuming an ever-growing full SDK thread for every execution. This may require short-lived or task-bounded SDK threads and therefore requires an explicit later design decision if adopted. D-009 already supports targeted retrieval; D-020/D-023 require persistent organizational identity, not necessarily one forever-growing provider thread.
- **Stage D — viability gate:** only after the bounded design is implemented and deterministically verified, run a preregistered set of ordinary useful tasks. Do not resume feature development until the gate passes.

**Provisional viability gate to validate before implementation:**

- coordination: zero unsatisfied explicit joins may settle; zero stale-history preemption; zero unauthorized fanout; every assignment/result causally attributable;
- economics: target median total execution tokens <=100k/task, p90 <=200k, cached replay <=25%, median post-framing model/tool continuations <=4, and no >300k task without explicit justified escalation;
- quality: >=90% of preregistered ordinary tasks meet a human rubric without material omission and expose provenance/partial-result state;
- robustness: include tool failure, truncation, stale-history pressure, and interruption/resume cases;
- stop condition: any deterministic coordination invariant failure after implementation, two independent ordinary tasks exceeding the economic ceiling without justified escalation, or quality below the agreed threshold while meeting budget ends incremental patching. At that point either the runtime is redesigned more fundamentally or the present architecture is declared non-viable.

**Open design questions before any code authorization:**

- exact minimal tables/columns for tasks, assignments, and joins;
- whether redesigned `deliveries` remain only a readability/audit projection or are retired for transaction-enabled tasks;
- how observer follow-ups amend, supersede, or create tasks;
- the smallest structured decision schema that makes delegation and settlement atomic without moving intellectual judgment into CORE;
- how explicit user-required peer work is represented without brittle natural-language parsing;
- whether Stage C can use bounded provider threads while preserving D-013 recovery guarantees and D-023 identity/history semantics;
- exact gate corpus and thresholds, including whether the agents' proposed numerical ceilings are realistic rather than merely aspirational.

No implementation should begin until the principal accepts or revises this design boundary.


### A3 audit remediation program
**Audit work state:** COMPLETE  
**Remediation work state:** COMPLETE  
**Evidence:** E-065

A3 found the core execution/coordination architecture structurally healthy enough to preserve while identifying maintenance debt that ordinary production work can miss.

Ordered remediation:

1. **I-007 — Environment and documentation truth drift (COMPLETE):** Python support-floor, README/Architecture/Operations truth, and Development Control context hygiene repaired; see E-066.
2. **I-008 — Repository branch hygiene (COMPLETE):** merged-branch residue removed and automatic deletion of future merged PR heads enabled; see E-067.
3. **I-009 — Runtime provenance and maintenance health (COMPLETE):** deterministic runtime/source/model-policy provenance, watchdog degradation/recovery health, and durable execution-level model/effort/usage facts implemented and canonically verified; see E-068.
4. **P1 follow-up — Model/reasoning-effort and continuation economy (COMPLETE / LIVE VERIFIED / MONITOR):** same-thread selection is live verified; hidden SDK subagents are disabled; E-083–E-086 establish the continuation mechanism and first repair; E-090 records an ordinary-use recurrence in broader source work and the verified PR #77 follow-up. No further dedicated paid benchmarking is planned.
5. **I-012 — Authorized CORE and cross-Room read inspection (COMPLETE):** the I-010 evidence boundary was repaired and live verified under D-029 / E-078 / E-079.
6. **I-013 — SDK-internal subagent bypass (COMPLETE):** Codex's ambient multi-agent surface is disabled so production cognition routes through persistent Room A/B/C and its execution-accounting path; see E-080.
7. **I-014 — Deterministic retrieval economy (COMPLETE):** E-081's original direct/batched retrieval repair remains, and E-090 closes an ordinary-use recurrence by distinguishing triggering versus passive context, hardening direct source retrieval, and correcting execution-level token telemetry.
8. **I-010 — Persistent-data operational maintenance (COMPLETE):** offline local check/backup/verify/restore implemented and verified; see E-087.
9. **I-011 — Verification-platform and dependency assurance (COMPLETE):** cross-platform hosted verification, pinned browser tooling, deterministic test synchronization, dependency/advisory review, and the Windows newline portability repair are implemented and canonically verified; see E-088.

Lower-value audit findings remain MONITOR/DEFERRED until evidence shows they are expensive: shareable/redacted exports, explicit non-loopback safeguards, WebSocket overflow resync, formal numbered schema migrations, large-module refactoring, storage optimization, and stronger per-capability isolation.

The remediation program does **not** authorize automatic model routing, large refactors, or broader productization by implication.

### Room-wide invocation economy
**Work state:** COMPLETE  
**Follow-up:** MONITOR through ordinary use  
**Reality:** IMPLEMENTED / LIVE VERIFIED  
**Decision:** D-027  
**Evidence:** E-062, E-063, E-064

D-027 generalizes the token-economy rule to every use of `invoke_targets`:

- invocation requests immediate cognition, not visibility;
- public messages remain readable without waking a peer;
- use `all` only when every peer genuinely needs to run;
- if no additional cognition is needed, use `invoke_targets: []` for a public/readable MESSAGE with no runnable peer;
- a peer completing bounded work for C should normally return to C without waking the other delegated peer;
- direct A/B collaboration remains allowed when that peer's additional cognition is materially necessary.

PR #55 / E-063 verify the shared protocol and explicit no-wake routing primitive. `invoke_targets: []` publishes a public/readable MESSAGE with no runnable peers; `null` remains the legacy all-peer fanout. No scheduler or UI redesign was required.

E-064 provides the fresh-Room live pass. C differentiated A/B work; A returned with no runnable peer; B targeted only C; neither peer woke the other; one cohort trigger caused one C integration turn; and the earlier E-062 review/reopen cascade did not recur. No further dedicated D-027 test is warranted. Monitor ordinary use for regressions or cases where direct A/B invocation is genuinely useful.

### C peer-allocation economy and temporary cognitive framing
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / LIVE VERIFIED  
**Decisions:** D-025, D-026  
**Evidence:** E-059, E-060, E-061, E-062

C retains D-025 authority to assign temporary task-specific working postures, perspectives, scopes, constraints, evidence standards, expected deliverables, or temporary roles/personas to A/B.

E-060 showed that optional differentiation was too permissive: in the first live test C invoked both peers for substantially the same analysis, and A/B produced strongly convergent recommendations.

D-026 therefore adds two protected allocation rules:

- use the fewest peers that can add sufficient value; if one peer is enough, invoke one;
- if both A and B are invoked in the same delegation, their cognitive responsibilities **must be meaningfully differentiated** along a substantive dimension expected to create complementary value.

Cosmetic role labels and substantially duplicate analyses do not satisfy the rule. Even when independent verification is valuable, C should differentiate the verification method or responsibility rather than duplicating the same assignment.

D-025's identity and judgment guardrails remain: frames are temporary delegation instructions; C cannot dictate conclusions; A/B may challenge the frame or premise and remain epistemic peers.

PR #53 / E-061 verify the protected D-026 rule. No posture registry, new database object, profile mutation, or UI is warranted without evidence that natural-language delegation is insufficient.

E-062 provides that live verification: on a clean household-move objective C invoked both peers with substantively different responsibilities and integrated complementary returns. D-026 is therefore complete.

### C delegation-cohort timing
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / LIVE VERIFIED  
**Decision:** D-020  
**Observed Room evidence:** E-052  
**Instruction repair:** E-053  
**Deterministic timing implementation:** E-054  
**Live verification:** E-055

E-055 verifies the exact timing mechanism end to end. A returned first and remained passive to C. B returned later. CORE then created one delegation-cohort-settled trigger, and C consumed both peer returns plus that trigger in one integration turn. The same C FINISH settled both peer MESSAGE boundaries and the Round closed normally.

The demonstrated timing issue is complete. No further timing retest is currently warranted.

### Neutral startup profiles
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / VERIFIED deterministically  
**Decisions:** D-023, D-024  
**Evidence:** E-058

The active product direction no longer requires persistent startup personalities.

D-024 requires:

- standard A/B/C default profile bodies are empty and identical;
- fresh Rooms compose no default `PERSONALITY` section;
- A/B/C retain persistent identity and shared institutional/peer context;
- C retains protected organizer/coordination responsibilities as structure, not personality;
- custom saved profile text and Room-specific overrides remain supported;
- existing Room snapshots are not rewritten;
- exact known built-in defaults migrate conservatively to the empty neutral default while non-matching custom text is preserved.

The former personality-calibration effort remains closed. Behavioral recognizability is not an acceptance criterion.

PR #49 and E-058 verify the implementation: fresh standard composition has no default `PERSONALITY` section; E-056 built-ins migrate conservatively to empty defaults; custom profile text remains preserved; and C's protected structural layer remains intact.

D-025 now authorizes an initial semantic form of dynamic cognitive framing through C's protected coordination instructions. A heavier posture registry/data model/UI remains **NOT IMPLEMENTED** and should not be added unless ordinary use demonstrates a need.

## Recently completed work

This section is intentionally compact. Detailed implementation narratives and exact verification belong in the Decision/Evidence registers and Architecture, not in volatile Development Control.

| Work | Current result | Durable pointer |
|---|---|---|
| A3 — whole-system housekeeping, efficiency, and operational assurance audit | COMPLETE; core runtime/coordination GOOD, bounded remediation identified | E-065 |
| D-027 — invocation is cognition, not visibility | COMPLETE / IMPLEMENTED / LIVE VERIFIED; ordinary-use MONITOR | D-027, E-062–E-064 |
| D-026 — economical differentiated dual-peer delegation | COMPLETE / IMPLEMENTED / LIVE VERIFIED | D-026, E-061–E-062 |
| D-025 — temporary cognitive framing through C delegation | COMPLETE / IMPLEMENTED | D-025, E-059–E-060 |
| D-024 — neutral startup cognition | COMPLETE / IMPLEMENTED | D-024, E-058 |
| D-023 personality-layer program | SUPERSEDED in default-personality objective by D-024; protected replaceable-layer architecture retained | D-023–D-024, E-041–E-057 |
| D-020 permanent triad / C integration | COMPLETE / IMPLEMENTED / VERIFIED | D-020, E-027, E-029, E-052–E-055 |
| P4 deterministic Room/agent capabilities | COMPLETE / IMPLEMENTED / VERIFIED end to end, including custom registration/reuse and rollover inheritance | D-022, E-030–E-040 |
| A2 — Assurance Pass 2 | COMPLETE; no material runtime GAP demonstrated at its baseline | E-028 |
| P0 selective invocation | COMPLETE / MONITOR | E-017 |
| Retry / Agent Error observability | COMPLETE | E-018 |
| P1 operating-efficiency doctrine | COMPLETE as doctrine / MONITOR; new empirical model-effort follow-up is separately PLANNED below | D-005, D-006, D-018, E-065 |
| P2 persistent-context / compaction economics | COMPLETE / MONITOR | E-019 |
| P3 usage-wall delayed continuation | COMPLETE / MONITOR | D-017, E-020, E-028 |
| I-004 README permanent-triad drift | COMPLETE | historical Development Control/Git history; D-020 |
| I-006 early-triad profile migration | COMPLETE | E-029 |

Personality experiments V3/V4/V5/V6.2/V7 and CG1 remain historical evidence, not current work. Their implementation/evaluation records are E-042 through E-057. The current governing state is neutral startup profiles plus temporary task framing and economical differentiated delegation under D-024 through D-027.

## Ordered next work

### A3 audit-remediation sequence
**Work state:** COMPLETE  
**Evidence:** E-065

Current order:

1. I-007 — environment/document truth and context hygiene;
2. I-008 — merged-branch/repository hygiene;
3. I-009 — runtime provenance, maintenance-health visibility, and usage instrumentation;
4. P1 follow-up — COMPLETE / MONITOR through ordinary useful work;
5. I-010 — COMPLETE / IMPLEMENTED / VERIFIED; see E-087;
6. I-011 — verification-platform and dependency assurance cleanup — **COMPLETE / IMPLEMENTED / VERIFIED**; see E-088.

Do not collapse this into one large refactor. Each item should close on bounded evidence, and later items should reuse instrumentation established earlier.

### EF-1 — Reproducible dependency/environment setup
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-10

Clean pip/venv installation is now constrained by `constraints-test.txt`, which records the known-good application/test dependency set while `pyproject.toml` retains broader supported ranges. The merged repair restored green hosted CI with **129 passed, 2 warnings**. No `uv` migration was needed.

### EF-2 — Canonical full-test command
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-10

Canonical routine command: `python -m pytest -q`. Clean-environment verification collected and passed **129 tests**. `test-transcript-stability.ps1` remains a separate specialized browser check.

### EF-3 — Minimal CI
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-10

GitHub Actions runs the canonical Python suite on pushes to `main` and pull requests targeting `main`, installing through `constraints-test.txt`. I-011 expands hosted coverage to Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12; the Windows lane also runs the pinned browser transcript suite. A separate dependency-review workflow performs pinned advisory scanning and informational dependency-freshness reporting without automatic upgrades. Canonical merge `ed2e5f1ea636eacc585bf89168d222f017a4b75d` passed **370 tests, 2 warnings** on each Python lane, **3 browser tests** on Windows, and the dependency audit reported **no known vulnerabilities**; see E-088.

### P4 — Deterministic Room and agent capabilities
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED end to end — 2026-09-13

P4.1 through P4.5 are complete: deterministic assertions, registry/discovery, the minimal CORE library, agent-created custom capability registration/verification, and lineage rollover inheritance have all been verified end to end. P4 is closed. Personal/CORE promotion remains later work under D-022 and requires separate explicit prioritization.

### P1 follow-up — Model/reasoning-effort and continuation economy
**Work state:** COMPLETE / MONITOR  
**Reality:** IMPLEMENTED / VERIFIED mechanisms; ordinary-use savings MONITOR  
**Evidence:** E-065, E-068, E-069, E-070, E-071, E-072, E-073, E-074, E-075, E-076, E-077, E-080, E-081, E-082, E-083, E-084, E-085, E-086, E-090  
**Current gate:** Dedicated paid P1 benchmarking is closed. E-090 demonstrates that ordinary useful work can still expose continuation amplification outside the controlled E-086 fixture; PR #77 closes the demonstrated passive-context, source-retrieval, and telemetry defects deterministically. Continue naturalistic monitoring and reopen only on a concrete recurrence.

The compatibility/default policy remains `gpt-5.6-terra` with `high` reasoning, including C's own turns and any peer invocation for which C supplies no experimental override. E-075 adds a bounded P1 capability: when C explicitly invokes A/B, C may select one of four admitted model/effort configurations for that peer execution. D-028 hard-prohibits Astra execution. A/B cannot directly change their own execution configuration; they may request escalation from C. No automatic router exists. I-009 continues to provide the durable per-execution model, reasoning-effort, and usage evidence.

E-070 established that the former 0.147 runtime exposed Sol, Terra, Luna, and GPT-5.5 through its SDK catalog while the principal's desktop Codex UI visibly exposed Astra. E-071 advanced the canonical SDK/runtime standard to the matched published 0.154.0 pair, verified with 327 tests on exact PR and canonical-main commits. E-072 then live-verified the local 0.154.0 runtime and confirmed the same SDK now exposes `gpt-6-astra`. This dependency upgrade does **not** change production model selection.

The two paid synthetic matrices are complete under E-073/E-074. Routine structured work showed no measured quality advantage for universal Terra/high, but the harder threshold run's only score differences came from an epistemically ambiguous state/evidence answer key and therefore do not support a trustworthy model ranking. More importantly, the principal reported that the 30 dedicated benchmark turns consumed nearly 20% of the five-hour Plus allowance. Continuing synthetic expansion would violate P1's own efficiency objective.

P1's dedicated experimental phase is closed. The retained operating guidance is:

- E-077 already verifies the live same-thread switching mechanics; do not repeat the forced two-configuration commissioning test;
- E-080 shows that Codex SDK-internal subagents can bypass `invoke_targets` and Room execution accounting when the ambient multi-agent surface is available; exclude such work from P1 allocation conclusions and keep I-013 ahead of further evidence gathering;
- E-081 shows that repeated deterministic tool continuations can dominate usage even inside one visible Room turn; prefer reducing tool-loop/context amplification before spending more allowance on model-ranking experiments;
- E-082 provides a read-only local Codex rollout usage extractor, so future useful Desktop-vs-Room comparisons can use cumulative/task-level token counters without asking either system to introspect or commissioning synthetic benchmark turns;
- E-083 shows that the first matched C-only comparison used 32 Room tool calls versus 11 on Desktop and about 1.92x the reported total tokens despite only about 8% more uncached input and reasoning-output tokens; the dominant penalty was cached-context replay across extra continuations. Its deterministic ground-truth test also falsified C's specific duplicate-insert restart claim, so future correctness reviews should require end-to-end reachability rather than local suspicious-code inference;
- E-084's fresh blind fixture strengthens the economics finding: Desktop solved the task correctly with 8 tool calls / 279,098 tokens, while the task-only Room attempt used 38 tool calls / 1,805,314 tokens and returned no answer. The Room used 6.47x total tokens, 6.83x cached input, and 3.33x uncached input. C also violated the explicit shared-workspace-only evidence boundary and claimed it was awaiting two peer audits while structured metadata showed zero peer invocations and `invoke_targets: []`;
- E-085 traces those 39 task provider responses to one C SDK turn with 38 tool calls; Room tool-activity events were post-turn records, not cognition triggers. Fifteen source operations were single reads versus one `read_many`, and the old capability policy imposed registry/separate-command ceremony. PR #70 now prioritizes native one-off workspace work, few/batched tool continuations, sufficient-evidence stopping, and explicit workspace-only boundaries;
- E-086 provides the one justified post-fix regression: on the same fixture C completed correctly with 3 tool calls, 4 provider responses, 0 failures, and 92,765 tokens. Relative to pre-fix Room, tool calls fell 92.1%, provider responses 89.7%, total tokens 94.9%, and cached input 95.4%. This closes the benchmark loop; ordinary useful work is now the evidence source;
- E-090 is the resulting ordinary-use evidence: broader source work again reached 22–31 tool/activity calls with roughly million-token cached-context replay, while a passive backlog caused one peer to answer stale work. PR #77 preserves passive cross-reading but labels triggering versus passive context, requires the direct source CLI for normal `inspect_source` work, supports explicit-file search targets, reinforces one `search-many` → one `read-many` retrieval, and reports execution-token deltas from the prior same-thread cumulative usage snapshot;
- use the E-075 capability naturally in ordinary Rooms rather than creating more paid benchmark Rooms;
- C should prefer `luna-medium` for routine bounded delegated work and deliberately choose a stronger admitted Terra or Sol configuration only when complexity, uncertainty, risk, or prior verification trouble provides an affirmative reason;
- Astra is prohibited by D-028 and is not an admissible execution configuration; the runtime must fail closed if an Astra turn is attempted;
- A/B should request escalation from C when the assigned work appears underpowered rather than silently self-routing;
- collect the already-persisted model/effort/usage facts and normal verification outcomes from work the principal actually wanted completed;
- avoid duplicate model calls solely to compare models; use deterministic checks and already-required independent review where they naturally exist;
- treat E-073/E-074 as evidence that routine bounded tasks do not presently justify universal Terra/high, while preserving uncertainty about the escalation boundary;
- only decide whether to keep C-discretionary selection, compile stable rules, or build any automatic/dynamic router after representative evidence shows which simpler policy actually earns its cost.

No automatic/dynamic model-routing policy is authorized yet.

## Approved planned development

### Personal daily usage pacing limit
**Work state:** DEFERRED  
**Reality:** DECIDED / NOT IMPLEMENTED  
**Decision:** D-019  
**Feasibility evidence:** E-026  
**Readiness constraint:** mixed subscription-allowance / purchased-credit semantics are unresolved. E-026 proves structured rate-limit data exists, but does not establish how mixed usage pools are represented, prioritized, or consumed well enough to enforce the intended pacing policy correctly.
**Scheduling:** do not begin implementation until this usage-pool model is understood and the pacing semantics are deliberately resolved.

Core approved behavior:

- user-configurable daily limit expressed as a percentage of the weekly Codex usage allowance;
- default daily limit: **1/7 of the weekly allowance (~14.3%)**;
- use Codex's structured account rate-limit/usage meter as the pacing source;
- stop initiating new model work after the configured daily allowance has been reached according to the latest available reading;
- allow already-running work to finish, accepting possible small overshoot;
- provider enforcement remains authoritative.

Implementation details such as warning thresholds, UI presentation, carry-forward semantics, daily-period/time-zone semantics, polling cadence, and exact SDK/app-server integration remain open until implementation design.

Before implementation, resolve at least: whether purchased credits form a distinct consumable pool from the subscription allowance; which pool or combination the daily pacing limit governs; what provider-reported fields can distinguish those pools; and how pacing should behave when one pool is exhausted while another remains available.

## Maintenance issues

### I-007 — Environment and documentation truth drift
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED on canonical `main`  
**Evidence:** E-065, E-066  
**Priority:** CLOSED / first A3 remediation item

A3 found multiple low-risk truth/maintenance defects:

- package/README claim Python 3.10+ while current source relies on a newer runtime surface;
- README incorrectly says the normal launcher sets the desktop Codex runtime and still describes C as a fixed read-only Integrator template;
- Architecture still contains stale P4.5-in-progress text;
- maintained register/synthesis freshness headers lag later content;
- Development Control retains substantial completed experimental narration already owned by durable decision/evidence sources, increasing routine retrieval/context cost;
- Repository & Operations has not yet been refreshed for major later architecture such as P4 and current routing/profile behavior.

Repair completed through PR #57 and canonical-main verification. The owning sources were updated in place rather than adding a new documentation layer; completed experimental detail remains in its Decision/Evidence owners, and Development Control is again a compact volatile control surface.

### I-008 — Repository branch hygiene
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / VERIFIED  
**Priority:** HIGH / second A3 remediation item  
**Evidence:** E-065, E-067

E-067 established and closed the remediation: 56 merged-PR residue branches were verified and deleted, fresh GitHub inspection shows only canonical `main` with zero open PRs, and `delete_branch_on_merge` is enabled. The checked GitHub ruleset path remains unavailable for this private repository on the current account tier; no heavyweight protection workaround was introduced.

Bounded remediation:

- historical cleanup: COMPLETE — the exact 56-branch merged set from E-067 was deleted and fresh GitHub inspection shows only `main`;
- future cleanup: COMPLETE — automatic deletion of merged PR head branches is enabled;
- `main` protection remains a plan/account-capability constraint rather than a reason to invent heavier ceremony.

### I-009 — Runtime provenance and maintenance health
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / VERIFIED / LIVE VERIFIED  
**Priority:** HIGH / prerequisite for P1 empirical follow-up  
**Evidence:** E-065, E-068, E-069

The bounded remediation is complete on canonical CORE:

- `/api/health` exposes process-start application/source provenance, Python and installed Codex SDK version, and configured Room model/reasoning effort;
- the maintenance watchdog exposes `starting` / `healthy` / `degraded` state plus last success/error and cumulative/consecutive unexpected-failure facts instead of silently swallowing arbitrary exceptions;
- durable `agent_executions` rows retain the execution model and reasoning effort beside the existing SDK usage JSON, providing the empirical input needed for P1;
- no dashboard, general observability platform, or automatic model-routing policy was introduced.

PR #58 and the exact canonical merge commit are verified under E-068. Canonical-main CI passed **327 tests, 2 warnings**. E-069 then live-verified the local Personal runtime on exact canonical revision `6168c80938c7e9172a86651d3a9953fb66c2e219`: clean source, Python 3.12.10, `openai-codex` 0.147.0, Terra/high policy, and a healthy zero-failure watchdog.

### I-012 — Authorized CORE and cross-Room read inspection
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / VERIFIED / LIVE VERIFIED  
**Decision:** D-029  
**Evidence:** E-077, E-078, E-079  
**Priority:** CLOSED / dependency discovered by the I-010/P1 live trial

The first I-010 adaptive-cognition Room demonstrated a real evidence boundary: agents confined to their current shared workspace could not ground implementation-specific maintenance conclusions in CORE source or prior Room artifacts. D-029/I-012 repaired that boundary through registered CORE capability `inspect_source`.

Verified behavior:

- discover authorized sources, find files, search literal text, and read bounded UTF-8 source text;
- expose an allowlisted maintained CORE repository/source surface while excluding `data/`, environment-private files, credentials/secrets, virtual environments, Git internals, and arbitrary host paths;
- expose other Personal Rooms only through `data/rooms/<room_id>/shared`, not private participant state or host database internals;
- reject traversal plus symlink/reparse escapes and preserve all existing cross-boundary write restrictions.

PR #62 is canonically verified under E-078. E-079 then live-verified the deployed path in a fresh Room: C alone discovered/inspected `inspect_source`, read and searched CORE, inspected another Room's shared workspace, made no writes, and FINISHed `I-012-LIVE-OK`.

The no-write smoke forced C away from the existing `--input-file` fallback after fragile Windows inline-JSON attempts. Successful workaround invocations were exported as generic `command_execution` rather than promoted structured capability telemetry. This is retained as MONITOR, not a completion blocker: functional access succeeded, no raw payload leaked into durable activity, and ordinary operation already has a file-input fallback. Reopen only if normal Rooms repeatedly need wrapper-form invocation or the missing structured telemetry becomes operationally costly.

### I-013 — SDK-internal subagent bypass
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / VERIFIED on canonical `main`; recurrence MONITOR  
**Priority:** CLOSED / P1 evidence-integrity prerequisite  
**Evidence:** E-080

The repository-grounded I-010 Room contained one counted C turn and no persistent A/B turns, yet C's final report claimed A at `luna-medium` and B at `terra-medium`. The export instead recorded four SDK `sub_agent_activity` events inside C's turn. Pinned Codex 0.154 source confirms that multi-agent tools default enabled and spawned subagents inherit the parent model by default.

PR #63 closes that bypass by adding app-server overrides `agents.enabled=false` and `features.multi_agent_v2.enabled=false`. Final PR head `830bbfec06d3f90463a4e07c214e780bb7ca3c23` and squash merge `8ed3df777ed24a8192b48e43f652f4736921fe2c` share exact Git tree `b7436a3a3e12616b81f84e59c5650f599776ebf9`; both hosted runs passed **341 tests, 2 warnings**.

Do not count Rooms containing SDK-internal subagent activity as C-selected Room-peer allocation evidence. No dedicated paid model smoke is warranted; simply monitor the next useful Room for absence of `sub_agent_activity` and reopen I-013 only on demonstrated recurrence.

### I-014 — Deterministic retrieval economy
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / VERIFIED on canonical `main`; ordinary-use recurrence MONITOR  
**Priority:** CLOSED / demonstrated operating-economics remediation  
**Evidence:** E-081, E-090

E-081 established the original tool-loop/context-amplification defect and PR #64 added direct/batched `inspect_source` retrieval plus execution-economics telemetry. E-086 later showed the broader PR #70 continuation-policy repair could reduce a controlled fixture to 3 tool calls / 4 provider responses / 92,765 tokens.

Ordinary feature testing then demonstrated that the problem was not fully eliminated for broader source work. E-090 records two related defects: a newly invoked peer could receive earlier passive readable messages without the prompt distinguishing them from the runnable trigger, and source investigations could still take 22–31 tool/activity calls with heavy cached-context replay despite `search_many` / `read_many` being available. The same evidence showed the economics status line combined current-execution tool counts with cumulative persistent-thread token totals.

PR #77 closes that bounded recurrence without adding a planner, tool quota, automatic router, schema migration, or broader read authority:

- coalesced prompt events retain passive cross-reading but are explicitly labeled `triggering` versus `passive_context`, with triggering events identified as the current work;
- `inspect_source` search/search-many accepts an explicit regular file as well as a directory while preserving the existing allowlist, traversal, link/reparse, output, and no-write boundaries;
- always-loaded guidance uses the direct `codex-room-cap source` surface for normal source inspection, states the relevant search limits, and makes one `search-many` followed by one `read-many` the normal pattern when several lookups are already known, with further retrieval reserved for a specific unresolved dependency;
- `execution_economics` retains provider-reported cumulative usage in metadata but derives the visible execution token figure and tokens-per-tool-call from the immediately prior durable usage snapshot on the same SDK thread. Missing or non-monotonic counters produce an explicit unavailable/non-monotonic state rather than an invented delta.

Exact PR #77 head `2d898aacecd274962a57cf39b32c983538d403fb` and squash merge `7d930127212b94580c6309032b83d654d032570e` share Git tree `e3a5e382712ac64e23f7abe9e5bc25cf2dfa3a10`. PR run `35023873652` and canonical-main push run `35024443078` both passed **376 tests, 2 warnings** on Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12, plus **3 browser tests** on Windows.

No dedicated paid Room regression is warranted. Continue to use ordinary useful Rooms as the effectiveness monitor.

### I-010 — Persistent-data operational maintenance
**Work state:** IN PROGRESS  
**Reality:** OBSERVED ISSUE / repository-grounded candidate specification  
**Priority:** MEDIUM / ACTIVE after I-014 closure  
**Evidence:** E-065, E-080

E-080 establishes the actual persistence surface and maintenance gap from current CORE: SQLite plus durable Room workspace and institutional/custom-capability material live beneath the Personal data root, while no bounded integrity/backup/verify/restore maintenance command exists.

The Room's candidate direction is intentionally narrow: a local operator-only maintenance CLI with integrity check, staged backup, deterministic backup verification, and guarded restore. Keep cloud sync, scheduling, retention, dashboards, and agent-callable restore outside I-010.

Before coding, Project-level review should simplify any proposal that is not required by current evidence. In particular, installation UUIDs, formal SQLite `user_version` adoption, and a specific PID-marker scheme are candidate mechanisms rather than settled requirements. Preserve the smallest safety properties needed to prevent live-state replacement, partial publication, corrupt restore, path escape, and silent overwrite of newer/existing state.


### I-011 — Verification-platform and dependency assurance
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / VERIFIED  
**Priority:** CLOSED  
**Evidence:** E-065, E-088

PR #75 closes the A3 assurance edges with bounded mechanics:

- hosted Python CI covers Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12;
- the Windows lane also runs the browser transcript suite using pinned `@playwright/test@1.63.0`;
- the two recorded timing-sensitive orchestration tests now synchronize on explicit state rather than short sleep/delay windows;
- `.github/workflows/dependency-review.yml` runs pinned `pip-audit==2.10.1` plus an informational outdated-package report on dependency changes, monthly, and on demand; upgrades remain deliberate;
- the first Windows run exposed `inspect_source` CRLF/LF variance. Returned transient UTF-8 text is now LF-normalized across platforms while raw-file SHA-256 and byte-size evidence continues to describe the original bytes; the version-2 interface/schema remains unchanged.

Final exact PR-head and canonical-main verification passed **370 tests, 2 warnings** on all three Python lanes, **3 browser tests** on Windows, and reported **no known dependency vulnerabilities**. See E-088.

### I-003 — B SDK-thread/profile continuity residue
**Reality:** OBSERVED ISSUE — historical provider-side residue; current recurrence not demonstrated  
**Evidence qualifier:** NEEDS VERIFICATION  
**Priority:** LOW  
**Fresh evidence:** 2026-09-12 A2 source/test inspection

A2 found that the current implementation repairs only the known stale pair-era A/B default/snapshot hashes in live unmodified Rooms, preserves archived/sealed/custom state, and records the migration once. Adapter/runtime tests show that a targeted profile rebind evicts only the selected cache entry, resumes the same persistent SDK thread ID with the current developer instructions, fails closed if the SDK returns another identity, and quarantines the worker on a failed resume without changing the durable thread ID.

The remaining uncertainty is narrower than the original observation: current deterministic evidence does **not** independently prove that the provider-side persistent thread has actually adopted the replacement developer instructions after same-thread resume. The runtime's own audit event therefore says instruction application “awaits participant verification.” Keep I-003 open as low-priority **NEEDS VERIFICATION** unless A2 later determines that a live provider-side check is worth its model cost.

## Deferred work

Keep these behind the active A3 remediation sequence unless the human principal changes priorities:

- archive retrieval/indexing;
- broader deterministic-tooling expansion;
- scalability/data-integrity work beyond demonstrated issues;
- collaboration-quality experiments;
- provider-neutral implementation;
- broader productization;
- Enterprise workforce features;
- packaging/funding preparation;
- nonessential UI refinement.

## Open questions

No high-priority conceptual question blocks current work. The A3 audit-remediation sequence is closed. P1 should gather only naturalistic useful-work evidence and now includes retrieval/tool-loop economics as well as persistent-Room-peer allocation. I-003 remains low priority and needs provider-side participant verification only if the value justifies a live model check. D-019 remains specifically blocked on understanding and defining mixed subscription-allowance / purchased-credit pacing semantics.
