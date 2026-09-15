# Codex Room — Development Control

**Last updated:** 2026-09-15  
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.  
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** The minimum Engineering Foundation, GPT Project review, D-020 permanent Personal triad / C-integration migration, **A2 — Assurance Pass 2**, **P4 — Deterministic Room and agent capabilities**, and **A3 — Whole-system housekeeping, efficiency, and operational assurance audit** are complete. The repository baseline is canonical `main`; verify exact HEAD, applicable CI, and local Git state directly when consequential rather than maintaining those mechanically changing facts here.
- **What just changed?** P1 advanced the canonical Codex SDK/runtime standard from 0.147.0 to the matched 0.154.0 pair under PR #59 / E-071. Production Room policy remains Terra/high; local reinstall/restart and an unfiltered zero-turn catalog check are next.
- **What is blocked?** D-019 daily usage pacing remains blocked on unresolved mixed subscription-allowance / purchased-credit semantics. The A3 remediation sequence itself has no known blocker.
- **Where is P4?** **COMPLETE.** E-030 through E-040 contain the implementation/live-verification evidence across P4.1–P4.5.
- **What is next?** P1 remains in progress. E-075 implements verified C-selected peer cognition for representative real work; the next evidence should come from ordinary Rooms, with C allocating cheaper or stronger peer cognition as warranted and A/B requesting escalation when needed. No automatic router is authorized. I-010 and I-011 remain after P1.
- **What are we deliberately not doing?** No further personality calibration, blind recognizability testing, stronger personality prose, or attempts to force cognitive specialization through persistent identity unless ordinary usage demonstrates a concrete product problem.

## Current Focus

### A3 audit remediation program
**Audit work state:** COMPLETE  
**Remediation work state:** IN PROGRESS / ordered  
**Evidence:** E-065

A3 found the core execution/coordination architecture structurally healthy enough to preserve while identifying maintenance debt that ordinary production work can miss.

Ordered remediation:

1. **I-007 — Environment and documentation truth drift (COMPLETE):** Python support-floor, README/Architecture/Operations truth, and Development Control context hygiene repaired; see E-066.
2. **I-008 — Repository branch hygiene (COMPLETE):** merged-branch residue removed and automatic deletion of future merged PR heads enabled; see E-067.
3. **I-009 — Runtime provenance and maintenance health (COMPLETE):** deterministic runtime/source/model-policy provenance, watchdog degradation/recovery health, and durable execution-level model/effort/usage facts implemented and canonically verified; see E-068.
4. **P1 follow-up — Model/reasoning-effort economy:** measure representative work before deciding whether universal Terra/high, participant-specific defaults, delegation-selected effort, or another policy is economically justified.
5. **I-010 — Persistent-data operational maintenance:** add the smallest deterministic integrity/backup/restore path warranted for durable Personal state.
6. **I-011 — Verification-platform and dependency assurance:** remove known test nondeterminism where practical, improve Windows assurance, pin specialized browser tooling, and add deliberate dependency/advisory review mechanics.

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
**Work state:** PLANNED  
**Evidence:** E-065

Current order:

1. I-007 — environment/document truth and context hygiene;
2. I-008 — merged-branch/repository hygiene;
3. I-009 — runtime provenance, maintenance-health visibility, and usage instrumentation;
4. P1 follow-up — empirical model/reasoning-effort economy investigation;
5. I-010 — deterministic persistent-data integrity/backup/restore maintenance;
6. I-011 — verification-platform and dependency assurance cleanup.

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

GitHub Actions runs the canonical Python suite on pushes to `main` and pull requests targeting `main`, installing through `constraints-test.txt`. The latest hosted verification on canonical `main` (`34abd391ecbb861d7661541e4a716a5152a2049d`) completed successfully with **130 passed, 2 warnings**.

### P4 — Deterministic Room and agent capabilities
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED end to end — 2026-09-13

P4.1 through P4.5 are complete: deterministic assertions, registry/discovery, the minimal CORE library, agent-created custom capability registration/verification, and lineage rollover inheritance have all been verified end to end. P4 is closed. Personal/CORE promotion remains later work under D-022 and requires separate explicit prioritization.

### P1 follow-up — Model/reasoning-effort economy
**Work state:** IN PROGRESS  
**Reality:** EXPLORATORY  
**Evidence:** E-065, E-068, E-069, E-070, E-071, E-072, E-073, E-074, E-075, E-076, E-077  
**Current gate:** deploy/use the verified C-selected peer-execution capability in representative real work; no further dedicated paid synthetic benchmarks.

The compatibility/default policy remains `gpt-5.6-terra` with `high` reasoning, including C's own turns and any peer invocation for which C supplies no experimental override. E-075 adds a bounded P1 capability: when C explicitly invokes A/B, C may select one of four admitted model/effort configurations for that peer execution. D-028 hard-prohibits Astra execution. A/B cannot directly change their own execution configuration; they may request escalation from C. No automatic router exists. I-009 continues to provide the durable per-execution model, reasoning-effort, and usage evidence.

E-070 established that the former 0.147 runtime exposed Sol, Terra, Luna, and GPT-5.5 through its SDK catalog while the principal's desktop Codex UI visibly exposed Astra. E-071 advanced the canonical SDK/runtime standard to the matched published 0.154.0 pair, verified with 327 tests on exact PR and canonical-main commits. E-072 then live-verified the local 0.154.0 runtime and confirmed the same SDK now exposes `gpt-6-astra`. This dependency upgrade does **not** change production model selection.

The two paid synthetic matrices are complete under E-073/E-074. Routine structured work showed no measured quality advantage for universal Terra/high, but the harder threshold run's only score differences came from an epistemically ambiguous state/evidence answer key and therefore do not support a trustworthy model ranking. More importantly, the principal reported that the 30 dedicated benchmark turns consumed nearly 20% of the five-hour Plus allowance. Continuing synthetic expansion would violate P1's own efficiency objective.

P1 now proceeds by representative real work only:

- deploy/use the E-075 capability in normal Rooms rather than creating more paid benchmark Rooms;
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
**Work state:** IN PROGRESS  
**Reality:** IMPLEMENTED / VERIFIED on canonical `main`; live-Room verification pending  
**Decision:** D-029  
**Evidence:** E-077, E-078  
**Priority:** ACTIVE / raised directly by the I-010/P1 live trial

The I-010 adaptive-cognition Room demonstrated a real evidence boundary: the agents could inspect only their current shared workspace and therefore could not ground implementation-specific maintenance conclusions in CORE source or prior Room artifacts. E-077 records that live observation while also verifying same-thread Luna→Terra peer execution.

PR #62 implements the bounded remediation through registered CORE capability `inspect_source`:

- discover authorized sources, find files, search literal text, and read bounded UTF-8 source text;
- expose an allowlisted maintained CORE repository/source surface while excluding `data/`, environment-private files, credentials/secrets, virtual environments, Git internals, and arbitrary host paths;
- expose other Personal Rooms only through `data/rooms/<room_id>/shared`, not private participant state or host database internals;
- reject traversal plus symlink/reparse escapes and keep read/search payload content transient while durable telemetry records only bounded provenance/evidence;
- preserve all existing cross-boundary write restrictions.

Final PR head `a64acf828cd32202038529d180311934ac1c26f5` and squash merge `e60ad2b1d4a3339c30ef1837f3bca53366929acd` share exact Git tree `c24f31635065252fd4e9d2bd0d2460549f5243e0`; both hosted runs passed **341 tests, 2 warnings**. The remaining gate is one fresh local Room smoke proving the deployed Windows/Codex sandbox can use `inspect_source` against CORE and another Room shared workspace. Do not close I-012 until that live gate passes.

### I-010 — Persistent-data operational maintenance
**Work state:** PLANNED  
**Reality:** OBSERVED ISSUE / maintenance gap  
**Priority:** MEDIUM  
**Evidence:** E-065

SQLite transactional/recovery design is strong, but routine Personal operation lacks a small deterministic integrity/backup/restore maintenance path.

Target the minimum useful operations:

- database integrity/quick check;
- consistent backup creation;
- deterministic verification that the backup is readable/internally sound;
- concise tested restore instructions or equivalent bounded recovery proof;
- storage-size/accounting diagnostics only if they materially aid maintenance.

Do not add a large backup subsystem without evidence.

### I-011 — Verification-platform and dependency assurance
**Work state:** PLANNED  
**Reality:** OBSERVED ISSUE / assurance gap  
**Priority:** MEDIUM  
**Evidence:** E-065

A3 found broad automated coverage but several assurance edges:

- routine hosted CI runs only Ubuntu/Python 3.12 despite Windows-centric normal operation;
- one timing-sensitive test has a documented hosted flake;
- specialized Playwright coverage resolves an unpinned package at run time;
- the known-good Python dependency set is intentionally pinned, but routine advisory/freshness review is not automated.

Bounded remediation should remove avoidable test nondeterminism, add the cheapest useful Windows-hosted verification, pin specialized browser-test tooling, and add a deliberate dependency/advisory review path. Dependency upgrades remain controlled changes requiring exact-version verification; this item does not authorize automatic upgrading.

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

No high-priority conceptual question blocks I-007/I-008. I-009 should establish the provenance/usage evidence needed before the P1 model/reasoning-effort follow-up makes any policy recommendation. I-003 remains low priority and needs provider-side participant verification only if the value justifies a live model check. D-019 remains specifically blocked on understanding and defining mixed subscription-allowance / purchased-credit pacing semantics.
