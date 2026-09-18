# Codex Room — Development Control

**Last updated:** 2026-09-18
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** Engineering Foundation, A2, P4, A3 remediation, and I-015 are complete. Work-model v2 with `provider_context_mode="assignment_thread"` remains the public production path. PR #113 is merged on canonical `main` and adds explicit Round-level `completion_policy` values: default `auto_settle` and opt-in `continuous`.
- **What just changed?** The naturalistic `Stay busy.` acceptance run completed. At 42/500 turns, the Room had crossed four coordinator settlement boundaries and CORE had resumed the same root C Assignment after each one; C had already entered a fifth bounded activity when the human paused the Room. Child Assignments continued to complete normally. See D-036 / E-130 / E-131.
- **Verification state:** D-036 continuous Round behavior is **IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED**. E-130 records deterministic verification/merge evidence; E-131 records four successful same-Assignment naturalistic resumptions under the literal `Stay busy.` objective. The run was intentionally expensive—1,882,148 raw execution-token deltas across 42 executions in about 8.4 minutes—so treat cost as stress-test evidence rather than a normal baseline.
- **What is blocked?** No high-priority CORE blocker is known. D-019 daily usage pacing remains deferred on unresolved mixed subscription-allowance / purchased-credit semantics. Common Cause competitive play still awaits separate principal authorization.
- **What is next?** No further dedicated continuous-Round work is required absent a demonstrated failure. Common Cause competitive play remains available when the principal explicitly authorizes it; otherwise continue ordinary-use monitoring and wait for a concrete next objective.
- **What are we deliberately not doing?** No further implementation or dedicated testing of continuous mode absent a demonstrated failure; no new optimization project solely because the literal stress test was expensive; no further synthetic Common Cause benchmark; no retroactive rewrite of failed historical Room transactions; no fourth persistent agent; no broad v2 redesign; no new memory/index architecture; no personality calibration; no automatic model router; no adjacent maintenance investigation without a demonstrated problem.

## Current focus

### Continuous Round naturalistic acceptance

**Work state:** COMPLETE

**Decision:** D-036

**Evidence:** E-130, E-131

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED

The dedicated acceptance is complete. In Room `room_579eb5236cd246d6a1000ea3fea781d0`, prompt exactly `Stay busy.` ran under `completion_policy="continuous"`, work-model v2, and `assignment_thread` with a 500-turn ceiling. C completed four distinct bounded activities; after each coordinator `COMPLETE`, CORE emitted `continuous_round_resumed` for the same root Assignment `assignment_df0eb6faf079484682e18e21beec5dcc`. C then began a fifth bounded activity.

The human paused the Room at 42 turns. The Round and root Task remained active, with six child Assignments completed, one child still running, six released Joins, and one pending Join. This is the intended behavior: the standing objective remained active, bounded child work retained ordinary lifecycle semantics, and human pause suspended further queued work without falsely settling the transaction.

The run consumed 1,882,148 raw execution-token deltas in approximately 506 seconds. That is useful stress-test economics evidence, but the prompt was deliberately literal and open-ended with a high turn ceiling. Do not infer a new CORE defect or launch an optimization phase from this cost alone.

No further dedicated continuous-Round acceptance run is required unless ordinary use exposes a concrete recurrence or new failure mode.

### Common Cause competitive-play authorization and ordinary-use monitoring

**Work state:** PLANNED

**Dependency:** explicit human authorization for competitive play.

**Evidence:** E-125 through E-129

The Common Cause implementation/repair/verification sequence is complete. The artifact in the existing shared workspace is verified play-ready. No further implementation or verification work is currently required.

When competitive play is authorized, use the same Room, persistent A/B/C identities/threads, and existing shared workspace. Freeze the verified game rules/engine except for a genuine defect. The first match is an ordinary competitive exercise, not another CORE benchmark.

Continue to monitor the repaired reconciliation boundary and coordination-allocation rules naturally rather than manufacturing dedicated tests.

### Ordinary continuation after the controlled replication

**Evidence:** E-126 through E-129

The principal chose to continue the existing Common Cause Room rather than discard already-spent work. A implemented an explicit zero-cost `pass` action to resolve the game-specification deadlock. When a requested A follow-up later returned `PASS` without performing the needed strengthening work, C placed the substantial fallback with a fresh bounded B assignment. B added the requested regressions/documentation and reported 11 passing tests without changing the engine mechanic.

That sequence naturally exercised the PR #110 fallback condition and supports the intended topology:

`identify bounded defect -> fresh capable worker corrects/strengthens -> verifier checks exact result -> integrate`

C then attempted to delegate one final independent exact-artifact verification. The local SDK rollout completed that exact turn with a valid `DELEGATE` decision and `task_complete`, but CORE recorded the same exact execution as `Codex turn was interrupted` and failed the transaction. Forensics identified a reconciliation race rather than a provider/model interruption. Repair commit `6b810f0e327da4055ced97f38a60977f4eba9c46` gives only the authoritative interrupted case a 0.05-second bounded opportunity for the already-started notification stream to settle; real `failed` history remains authoritative. See E-127.

After restart, a separate local environment regression temporarily blocked shell execution: redirected user `TEMP`/`TMP` pointed to `F:\Users\strig\AppData\Local\Temp`, where the Codex Windows sandbox helper could not apply its required write ACE. Restoring both variables to the Windows-profile temp directory on `C:` and restarting resolved the helper failure; a one-command SDK probe returned `CODEX_SANDBOX_OK` and sandbox setup logged `errors=[]`. See E-128.

The final continuation Round `round_557922a63c8c463ba7c40d185ddd0d58` then completed the missing nonmodifying verification. B performed the substantive independent checks; both Python files compiled, the existing unit suite passed 11 tests, CLI rejection atomicity was demonstrated for the exercised illegal action, and 48 deterministic pass actions completed all eight rounds with no unresolved offer or defense state and a final winner. C integrated the result and the Round closed normally by `transaction_settled`. See E-129.

The game is therefore verified play-ready. Competitive play remains a separate human authorization.

## Common Cause coordination-economics follow-up — complete

**Work state:** COMPLETE

**Decision:** D-035

**Evidence:** E-124 through E-129

**Reality:**

- dependency-aware sequencing — **IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED**;
- post-PR-#110 failed-delegation fallback allocation — **IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED / MONITOR**;
- coordinator-interruption issue — **REPRODUCED IN ORDINARY CONTINUATION / CORE REPAIR IMPLEMENTED AND VERIFIED TO SUFFICIENT EVIDENCE / MONITOR**;
- Common Cause artifact — **VERIFIED PLAY-READY / AWAITING HUMAN MATCH AUTHORIZATION**.

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

The protected C rule says that when delegated implementation, correction, or investigation fails to produce needed work, or fallback reaches C because another assignment failed or settled without producing it, C should normally place substantial tool-heavy execution in a fresh bounded capable peer assignment. This applies in the root coordination assignment and in peer-created child assignments. Direct C execution remains available for demonstrably small, urgent, integration-inseparable work or when no fresh peer is likely to perform it reliably at lower total cost.

E-126 later supplied the first natural ordinary-use support for this exact tightened branch: A's follow-up settled with `PASS` without producing the requested strengthening work, and C moved the substantial fallback to fresh B rather than doing it on C's accumulated context. B completed the work successfully.

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

Replication conclusions at that historical checkpoint:

- the earlier terminal `Codex turn was interrupted` after the verifier's artifact audit **did not reproduce in that controlled replication**;
- artifact-dependent verification sequencing **PASSed**;
- the Room completed below its turn ceiling;
- quality was preserved: the verifier exercised important state transitions and found a real specification contradiction, and C stopped at the correct human-decision boundary;
- PR #110's failed-delegation fallback condition **was not exercised in that Round**.

E-126/E-127 supersede the earlier monitor conclusions for later ordinary continuation: the fallback branch was subsequently exercised successfully, and the coordinator-interruption problem subsequently recurred and was diagnosed as a CORE reconciliation race.

Execution economics for the controlled replication:

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

The dedicated synthetic coordination benchmark series remains stopped. Ordinary continuation provided the missing fallback evidence naturally and exposed a real CORE reconciliation defect, which received a bounded repair. The game's turn-completion contradiction was addressed by the explicit zero-cost pass mechanic, and E-129 completed the final independent exact-artifact verification.

Common Cause is now **VERIFIED PLAY-READY**. Do not add another verification gate before competitive play unless the artifact changes or a genuine defect appears. Competitive play starts only after explicit principal authorization.

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

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED

E-126 shows the tightened branch operating as intended in ordinary continuation: an empty/nonproductive delegated follow-up was followed by substantial fallback work on a fresh capable peer rather than C's accumulated coordinator context. Continue to observe natural recurrences for generalization and cost/quality effects; do not purchase a dedicated synthetic test.

### Exact-turn interruption reconciliation

**Work state:** MONITOR

**Reality:** IMPLEMENTED / REVIEWED / VERIFIED TO SUFFICIENT EVIDENCE

E-127 records the reproduced false interruption, forensic diagnosis, and bounded repair at commit `6b810f0e327da4055ced97f38a60977f4eba9c46`. E-129 adds one normal post-repair continuation that closed by `transaction_settled` without recurrence. Continue ordinary-use monitoring. Do not widen the 0.05-second interrupted-only grace or redesign reconciliation absent new evidence.

### I-003 — Provider-side instruction adoption after same-thread profile rebind

**Work state:** MONITOR

**Reality:** NEEDS VERIFICATION / current recurrence not demonstrated

Current deterministic evidence verifies the local rebind mechanism and fail-closed identity behavior, but not independent provider-side proof that replacement developer instructions took effect on the resumed same thread. Do not spend a dedicated paid test unless ordinary use makes the uncertainty consequential.

### Naturalistic continuation economy

**Work state:** MONITOR

E-086 demonstrated that the continuation-economy repair can radically reduce tool-loop replay on a controlled fixture. E-090 showed broader source work can still become expensive. E-129 adds a concrete smaller recurrence: a requested single-verifier closeout took the path C -> A -> B, with A acting as a zero-tool relay and consuming 45,338 raw execution tokens without adding independent verification evidence. Treat this as ordinary-use cost evidence; avoid purchasing another synthetic benchmark solely to investigate it unless similar relay patterns recur or become materially expensive.

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

The Common Cause coordination questions that motivated PRs #109/#110 now have naturalistic support for both dependency-aware sequencing and the tightened failed-delegation fallback. The game artifact is verified play-ready. The only remaining Common Cause gate is the principal's separate authorization to begin competitive play.

The repaired exact-turn interruption boundary is monitor-only unless it recurs. The TEMP/TMP sandbox-helper regression is resolved and recorded in E-128; do not reopen it absent recurrence.

D-019 remains blocked on provider allowance/credit-pool semantics. Other deferred work should remain deferred until new evidence or explicit principal direction gives it priority.