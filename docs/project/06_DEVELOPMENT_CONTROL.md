# Codex Room — Development Control

**Last updated:** 2026-09-17
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** Engineering Foundation, A2, P4, A3 remediation, and I-015 are complete. Work-model v2 with `provider_context_mode="assignment_thread"` is the public production path. Legacy Rooms were deliberately cleared rather than migrated.
- **What just changed?** The bounded Common Cause coordination-economics follow-up is complete. A post-PR-#110 controlled replication preserved dependency-aware sequencing, completed artifact-dependent verification only after the implementation existed, resumed C normally after the verifier returned, and closed by `transaction_settled` after 12 of 20 allowed turns. The earlier terminal C interruption did not reproduce.
- **Verification state:** PR #110 remains IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED. Dependency-aware sequencing is additionally NATURALISTICALLY SUPPORTED. The tightened failed-delegation fallback rule remains BEHAVIORALLY UNVERIFIED because the replication did not contain a failed or empty delegated correction/investigation path.
- **What is blocked?** D-019 daily usage pacing remains blocked on unresolved mixed subscription-allowance / purchased-credit semantics. No other high-priority blocker is known.
- **What is next?** Resume ordinary Codex Room use/development. Treat PR #110 fallback behavior as a monitor item and evaluate it if ordinary work naturally produces a failed/empty delegation. Do not run another dedicated Common Cause benchmark merely to force that branch.
- **What are we deliberately not doing?** No further synthetic Common Cause series; no retroactive rewrite of existing Room snapshots; no fourth persistent agent; no broad v2 redesign; no new memory/index architecture; no personality calibration; no automatic model router; no adjacent maintenance investigation without a demonstrated problem.

## Current focus

### Ordinary-use development and naturalistic monitoring

**Work state:** IN PROGRESS

**Scope:** Use Codex Room for real objectives, preserve settled architecture, and turn concrete ordinary-use failures or expensive recurrences into bounded work only when evidence warrants it.

The latest dedicated benchmark series is closed. No current synthetic validation gate blocks ordinary use.

## Common Cause coordination-economics follow-up — complete

**Work state:** COMPLETE

**Decision:** D-035

**Evidence:** E-124, E-125

**Reality:**

- dependency-aware sequencing — **IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED**;
- post-PR-#110 failed-delegation fallback allocation — **IMPLEMENTED / EXACT-HEAD VERIFIED / BEHAVIORALLY UNVERIFIED / MONITOR**;
- earlier coordinator-interruption recurrence — **NOT REPRODUCED** in the controlled replication.

### Historical successful implementation baseline

The historical successful Common Cause implementation Round `round_f2075476746b4263a394203a2a2e7f3` produced the game implementation and passed 9/9 unit tests, but its coordination/economic shape was poor:

- 16 Room executions;
- 33 underlying provider responses;
- 17 native tool calls;
- **1,511,456 raw execution tokens**;
- C: **1,041,653**;
- A: **405,252**;
- B: **64,551**.

The demonstrated expensive topology was implementation and artifact-dependent verification running concurrently, followed by failed corrective work and large tool-heavy fallback on C's accumulated coordinator context.

The intended domain-general topology remains:

`produce prerequisite -> verify exact result -> integrate`

When correction is required:

`identify bounded defect -> fresh capable worker corrects -> verifier checks exact corrected bytes -> integrate`

Independent work remains eligible for parallel execution.

### Stage-1 structural rerun

Room `room_e910bab728bb4b518bb54ecfea9c67e9`, Round `round_62c0413093d54ed99a552d2524785f7b`, showed that the sequencing rule did not over-serialize independent work. C assigned A and B genuinely independent responsibilities concurrently. The run used **93,939 raw execution tokens**, 5.1% below the historical Stage-1 baseline of 98,996.

**Assessment:** PASS for preserving useful independent parallelism.

### Controlled implementation rerun before PR #110

Room `room_5c3fd157970f4f54ba391a7b009e3b8a`, Round `round_65eac0c64bb347eaa9fa5977f0fd08c0`, showed correct prerequisite sequencing and initial correction delegation, then exposed the PR #109 fallback loophole: substantial fallback reached C through a peer-created child assignment after delegated correction failed to produce the needed work.

The run stopped at the turn limit before full readiness. Economics through that stop were **863,799 raw execution tokens**, with C 354,530, A 485,893, B 23,376, 13 native tool calls, and approximately 80.8% cached-input share.

That evidence motivated PR #110's tightened fallback rule.

### PR #110 fallback tightening

Reviewed head:

`da4e47efb8d6e350503325f7521a2e9e56735bc1`

Merged as:

`ad9e46310068c07facea34ef0de76456881cd271`

Verified blobs:

- `codex_room/personalities.py`: `6fbe105abc8684173bd05878eac5f46c2c6ece25`;
- `tests/test_c_structural_coordination.py`: `590a11e2616c7ac69d17c12a756b8b3dee094285`.

The protected C rule now says that when delegated implementation, correction, or investigation fails to produce needed work, or fallback reaches C because another assignment failed or settled without producing it, C should normally place substantial tool-heavy execution in a fresh bounded capable peer assignment. This applies in the root coordination assignment and in peer-created child assignments. Direct C execution remains available for demonstrably small, urgent, integration-inseparable work or when no fresh peer is likely to perform the work reliably at lower total cost.

### Post-PR-#110 controlled replication

Fresh Room:

`room_01f030b67b0a44f08922391836a6fdd8`

Round:

`round_6409c600e2414a32a73a5f6f8e94bf51`

Controls included work-model v2, `provider_context_mode="assignment_thread"`, starter C, required contributors empty, a fresh empty workspace, the same controlled Common Cause implementation specification, `max_turns=20`, `max_consecutive_passes=3`, and `inactivity_seconds=1800`.

Observed sequence:

1. C confirmed the workspace was empty.
2. C delegated A implementation and B artifact-independent rules-audit/test-design work in parallel.
3. A implemented and tested the artifact while B produced a useful independent acceptance matrix.
4. After the artifact existed, C inspected the exact engine/tests/documentation.
5. C then delegated B to black-box verify that existing artifact.
6. B completed the artifact audit and found a reproducible gameplay deadlock in the approved specification: a legal state can require a second action when every enumerated action is illegal or unaffordable and no Pass/turn-completion rule exists.
7. The dependency join released and C resumed normally, integrated B's result, declined to invent an unapproved rule, and requested human clarification.
8. The Room closed normally by `transaction_settled` after **12 of 20 turns**.

Replication conclusions:

- the earlier terminal `Codex turn was interrupted` after the verifier's artifact audit **did not reproduce**;
- artifact-dependent verification sequencing **PASSed**;
- the Room completed below its turn ceiling;
- quality was preserved: the verifier exercised important state transitions and found a real specification contradiction, and C stopped at the correct human-decision boundary;
- PR #110's failed-delegation fallback condition **was not exercised**, so no behavioral-verification claim is made for that rule.

Execution economics:

- total raw execution tokens: **953,892**;
- C: **161,672**;
- A: **309,159**;
- B: **483,061**;
- Room executions: **12**;
- native model tool calls: **14**;
- failed tool calls: **4**;
- cached-input share: approximately **80.8%**.

The completed replication was **557,564 raw tokens / 36.9% below** the historical 1,511,456-token successful implementation baseline. Treat that comparison as directional because the endpoints differed: the replication correctly stopped on an unresolved game-specification contradiction rather than reaching a competitive-play-ready declaration.

### Common Cause stop condition

The dedicated synthetic series stops here. The replication found no new Codex Room defect requiring another benchmark or CORE change. Do not manufacture a failed delegation solely to test PR #110. If a real failed/empty delegation occurs in ordinary use, inspect whether substantial fallback moves to a fresh capable low-context peer and record the result then.

The Common Cause game's missing turn-completion rule is a game-specification issue, not a Codex Room architecture defect. Address it only if the principal chooses to continue the game itself.

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

### PR #110 failed-delegation fallback behavior

**Work state:** MONITOR

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / BEHAVIORALLY UNVERIFIED

Observe naturally if ordinary work produces a failed or empty delegated implementation/correction/investigation. Do not purchase another synthetic benchmark solely to force the condition.

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

No high-priority conceptual question currently blocks ordinary Codex Room use or development.

The remaining Common Cause-related empirical question is monitor-only: if ordinary work naturally produces a failed/empty delegation, does PR #110 keep substantial fallback off C's accumulated context while preserving quality and exact verification?

D-019 remains blocked on provider allowance/credit-pool semantics. Other deferred work should remain deferred until new evidence or explicit principal direction gives it priority.
