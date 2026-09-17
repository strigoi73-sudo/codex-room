# Codex Room — Development Control

**Last updated:** 2026-09-17
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** Engineering Foundation, A2, P4, A3 remediation, and I-015 are complete. Work-model v2 with `provider_context_mode="assignment_thread"` is the public production path. Legacy Rooms were deliberately cleared rather than migrated.
- **What just changed?** Common Cause ordinary use exposed an expensive coordination topology. PR #109 added dependency-aware sequencing plus an initial context-aware fallback rule. Naturalistic reruns then showed the sequencing rule working but exposed a fallback loophole. PR #110 tightened that loophole and merged to canonical `main` as `ad9e46310068c07facea34ef0de76456881cd271`.
- **Verification state:** PR #110 exact head `da4e47efb8d6e350503325f7521a2e9e56735bc1` passed the focused C-structural regression, `verify-fast.cmd`, exact-head/blob rechecks, and tracked-tree cleanliness. Canonical `main` carries verified `personalities.py` blob `6fbe105abc8684173bd05878eac5f46c2c6ece25`.
- **Naturalistic state:** dependency-aware sequencing has behavioral support. Post-PR-#110 fallback allocation does not yet have behavioral verification.
- **What is blocked?** D-019 daily usage pacing remains blocked on unresolved mixed subscription-allowance / purchased-credit semantics. No other high-priority blocker is known.
- **What is next?** Run a fresh **implementation/fallback-only Common Cause benchmark** after PR #110. Do not repeat Stage 1. Use the controlled historical implementation specification and a modestly higher turn ceiling than 16 so a real defect/correction cycle does not terminate the experiment prematurely.
- **What are we deliberately not doing?** No retroactive rewrite of existing Room snapshots; no fourth persistent agent; no broad v2 redesign; no new memory/index architecture; no personality calibration; no automatic model router; no adjacent maintenance investigation unless the next rerun or ordinary use demonstrates a concrete problem.

## Current Focus

### Common Cause coordination-economics follow-up

**Work state:** IN PROGRESS — PR #110 merged; post-#110 fallback rerun next

**Reality:** dependency sequencing IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED; tightened fallback allocation IMPLEMENTED / EXACT-HEAD VERIFIED / BEHAVIORALLY UNVERIFIED

**Decision:** D-035

**Evidence:** E-124 plus the 2026-09-17 Common Cause rerun records summarized below

**Scope:** [ROOM naturalistic evaluation of current CORE instructions]

### Historical successful implementation baseline

The historical successful Common Cause implementation Round `round_f2075476746b4263a394203a2a2e7f3` produced the game implementation and passed 9/9 unit tests, but its coordination/economic shape was poor:

- 16 Room executions;
- 33 underlying provider responses;
- 17 native tool calls;
- **1,511,456 raw execution tokens**;
- C: **1,041,653**;
- A: **405,252**;
- B: **64,551**.

The principal failure topology was:

1. implementation and artifact-dependent verification were delegated concurrently;
2. the verifier therefore could only produce a plan before the artifact existed;
3. later corrective assignments failed to produce the needed substantive correction/audit;
4. C then absorbed large tool-heavy fallback on accumulated coordinator context.

The desired domain-general topology is:

`produce prerequisite -> verify exact result -> integrate`

If correction is needed:

`identify bounded defect -> fresh capable worker corrects -> verifier checks exact corrected bytes -> integrate`

Independent work should still run in parallel. The policy does not permanently specialize A or B cognitively.

### Structural rerun Stage 1 — complete

Fresh Room:

`room_e910bab728bb4b518bb54ecfea9c67e9`

Round:

`round_62c0413093d54ed99a552d2524785f7b`

Observed result:

- C deliberately assigned A an original complete rules concept and B an independent mechanics/failure-mode analysis;
- both assignments were genuinely independent and ran concurrently;
- no native tools, retries, or failures occurred;
- total raw execution tokens: **93,939**;
- historical Stage-1 baseline: **98,996**;
- difference: **5,057 fewer / 5.1% lower**.

Interpretation: **PASS for “do not over-serialize.”** The dependency-aware rule preserved useful independent parallelism. Stage 1 did not test implementation→verification dependency or fallback behavior and does not need to be repeated for the next benchmark.

### Controlled implementation rerun — complete as evidence, incomplete as product readiness

Fresh Room:

`room_5c3fd157970f4f54ba391a7b009e3b8a`

Round:

`round_65eac0c64bb347eaa9fa5977f0fd08c0`

This run used the approved historical Common Cause implementation specification directly so the coordination topology could be tested without requiring Stage-1 design compatibility.

Observed sequence:

1. C split work into A implementation and B **artifact-independent verification-matrix design** in parallel.
2. B completed useful pre-artifact verification work rather than pretending to audit nonexistent code.
3. A implemented and tested the game.
4. Only after artifacts existed did C audit the actual engine/tests against B's matrix.
5. C found a real final-round offer-lifecycle defect and delegated a bounded correction to A.
6. A inadvertently settled that correction assignment before applying the patch and explicitly asked for reassignment.
7. Fallback then reached C through a child assignment; C performed substantial tool-heavy correction itself.
8. A later identified still-missing coverage and delegated more work back to C.
9. The Room hit `turn_limit` before the remaining coverage/readiness work completed.

Interpretation:

- **Dependency sequencing: PASS.** C distinguished artifact-independent pre-work from artifact-dependent verification and did not recreate the historical implementation+verification concurrency mistake.
- **Initial correction delegation: PASS.** C sent the bounded defect correction to a peer.
- **Fallback allocation under failed/empty delegated work: PARTIAL FAIL for PR #109 wording.** Substantial fallback still landed on C through a peer-created child assignment.
- **Full readiness: NOT COMPLETE.** The Room stopped at the turn limit; the game was not declared ready for competitive play.

Economics through the turn-limit stop:

- total raw execution tokens: **863,799**;
- C: **354,530**;
- A: **485,893**;
- B: **23,376**;
- native model tool calls: **13**;
- cached-input share: approximately **80.8%**.

The observed total is **647,657 raw tokens / 42.85% below** the historical successful implementation baseline, but this is **directional evidence only** because the rerun did not finish the requested regression/readiness work. Do not record it as a completed 42.9% benchmark improvement.

### PR #110 — fallback tightening

The controlled rerun exposed two wording loopholes in PR #109:

- “consider” another bounded peer assignment was too weak;
- “C's own coordination assignment” was too narrow because substantial fallback could reach C inside a child assignment.

PR #110 tightened the protected C rule so that when delegated implementation/correction/investigation fails to produce needed work, **or fallback reaches C because another assignment failed or settled without producing it**, C should normally place substantial tool-heavy execution in a fresh bounded peer assignment rather than perform it itself. The rule applies whether C is in the root coordination assignment or a peer-created child assignment.

Direct C execution remains allowed when work is demonstrably small in expected execution/context cost, urgent, inseparable from integration, or no fresh peer is likely to perform it reliably at lower total cost. A small-looking code/file diff is not itself evidence that model execution will be cheap.

Reviewed PR #110 head:

`da4e47efb8d6e350503325f7521a2e9e56735bc1`

Verified blobs:

- `codex_room/personalities.py`: `6fbe105abc8684173bd05878eac5f46c2c6ece25`;
- `tests/test_c_structural_coordination.py`: `590a11e2616c7ac69d17c12a756b8b3dee094285`.

PR #110 merged as:

`ad9e46310068c07facea34ef0de76456881cd271`

The deterministic regression proves instruction composition and preservation of surrounding coordination policy. It does **not** prove that a fresh C will obey the tightened fallback rule in a real failure path.

### Next benchmark

Run **only the controlled implementation/fallback benchmark** in a new Room created after PR #110. Do not repeat the design-only Stage 1.

Controls:

- work-model version 2;
- `provider_context_mode="assignment_thread"`;
- starter C;
- required contributors empty;
- ordinary current default profiles / protected instructions;
- empty fresh workspace;
- no historical Common Cause files preloaded;
- use the same controlled Common Cause implementation specification used in the prior implementation rerun;
- do not tell agents the historical failure topology, token totals, or desired remedy;
- use a modestly higher turn ceiling than 16 (target **20** unless a concrete setup constraint justifies another bounded value);
- retain `max_consecutive_passes=3` and `inactivity_seconds=1800` unless current runtime constraints require a documented deviation.

Primary questions:

1. When delegated correction fails or settles empty, does substantial fallback move to a fresh capable low-context peer rather than C?
2. Does artifact-dependent verification occur only after the exact artifact/correction exists?
3. Does the run complete the requested regression/readiness work rather than stopping at the ceiling?
4. Is quality preserved?
5. What are the completed execution count, provider-response count, tool calls, per-agent usage, and total raw execution tokens?

Stop after this bounded rerun unless its evidence demonstrates another concrete defect. Do not reopen Stage 1 or broad work-model-v2 design merely because the benchmark exists.

## Completed major program state

### I-015 — Task-transaction stabilization redesign

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / VERIFIED / PUBLIC DEFAULT / LIVE SMOKE PASSED

**Decisions:** D-030 through D-034

**Evidence:** E-092 through E-123

The production path is work-model v2 with Assignment-scoped provider context. Stage A established Task/Assignment/Join mechanics; Stage B added structured `EVIDENCE`; Stage C added assignment-scoped context plus bounded `HISTORY`; Stage D passed the ten-task viability gate at 9/10 quality with all coordination/robustness/economic thresholds satisfied; D-034 activated v2 publicly; legacy Rooms were deliberately cleared rather than migrated.

PR #108 is a bounded post-close ordinary-use repair for transaction contract/retry bounds. It does not reopen I-015.

### P4 — Deterministic Room/agent capabilities

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / VERIFIED end to end

**Decision:** D-022

**Evidence:** E-030 through E-040

CORE capability registry/discovery, standard library, custom authoring/verification/registration, safe invocation, and lineage rollover inheritance are implemented and verified. Personal/CORE promotion remains later work only if demonstrated useful.

### A3 remediation

**Work state:** COMPLETE

**Evidence:** E-065 through E-091

Environment/document truth, repository hygiene, runtime provenance, maintenance health, model-economy investigation, authorized source inspection, SDK-subagent bypass, deterministic retrieval economy, persistent-data maintenance, verification-platform cleanup, and Windows restart QOL were addressed in bounded slices. Continue naturalistic monitoring rather than reopening broad audits.

## Approved planned development

### D-019 — Personal daily usage pacing

**Work state:** DEFERRED

**Reality:** DECIDED / NOT IMPLEMENTED

**Evidence:** E-026

The intended default remains one-seventh of the weekly allowance (~14.3%), using structured provider usage/rate-limit data rather than Room token estimates. Implementation remains blocked until mixed subscription allowance versus purchased-credit semantics are understood well enough to define which pool is paced and how multiple pools interact.

## Maintenance / monitor items

### I-003 — Provider-side instruction adoption after same-thread profile rebind

**Work state:** MONITOR

**Reality:** NEEDS VERIFICATION / current recurrence not demonstrated

Current deterministic evidence verifies the local rebind mechanism and fail-closed identity behavior, but not independent provider-side proof that replacement developer instructions took effect on the resumed same thread. Do not spend a dedicated paid test unless ordinary use makes the uncertainty consequential.

### Naturalistic continuation economy

**Work state:** MONITOR

E-086 demonstrated that the continuation-economy repair can radically reduce tool-loop replay on a controlled fixture. E-090 showed broader source work can still become expensive. The current `EVIDENCE` interface and assignment-scoped production context further change that cost surface. Continue to record concrete expensive recurrences; do not launch synthetic benchmark matrices.

## Deferred work

Keep these deferred unless new evidence or explicit principal direction reprioritizes them:

- archive indexing/embeddings/broad summarization beyond bounded `HISTORY`;
- automatic/dynamic model routing;
- broader deterministic-tooling promotion without demonstrated reuse;
- stronger per-capability OS isolation;
- shareable/redacted exports;
- large-module refactors/storage optimization;
- broader productization/packaging/funding;
- Enterprise workforce features;
- provider-neutral implementation work;
- nonessential UI refinement.

## Open questions

No high-priority conceptual question blocks the next Common Cause run. The immediate empirical question is narrower: **does the post-PR-#110 fallback rule actually keep substantial failed-delegation fallback off C's accumulated context while preserving quality and exact verification?**

After the bounded implementation/fallback rerun, resume ordinary Codex Room development/use unless its evidence demonstrates another concrete defect or the principal explicitly reprioritizes work.
