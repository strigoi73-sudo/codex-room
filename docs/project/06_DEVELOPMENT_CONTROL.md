# Codex Room — Development Control

**Last updated:** 2026-09-19
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** I-016 — Private Principal Channel is the current authorized product objective under D-038. Its C-only private consultation/wait/resume implementation is present on a feature branch and awaits exact-head deterministic verification before merge. Earlier Engineering Foundation, A2, P4, A3 remediation, I-015, D-037/BCTX, and T0-T14 acceptance remain complete.
- **What just changed?** The principal authorized an explicit private C↔principal consultation path that must not invoke or deliver to A/B. The implementation adds `CONSULT_PRINCIPAL`, durable `waiting_principal` Assignment state, exact-event principal reply binding, same-Assignment/provider-context resume, restart persistence, Stop cancellation, and an observer reply UI.
- **Verification state:** I-016 is **IMPLEMENTED ON FEATURE BRANCH / VERIFICATION PENDING / NOT MERGED**. Added deterministic transaction tests cover privacy/no-delivery, same-context continuation, duplicate/stale reply rejection, restart persistence, Stop cancellation, and C-only authority; browser tests cover the private reply surface. Repository-standard `verify-fast.cmd` on the exact PR head is required before merge.
- **What is blocked?** I-016 has no known design blocker; it is waiting on exact-head verification. D-019 daily usage pacing remains separately deferred on unresolved mixed subscription-allowance / purchased-credit semantics. Common Cause competitive play still awaits separate principal authorization.
- **What is next?** Finish exact-diff review, run `verify-fast.cmd` on the exact I-016 feature head, and merge only if that version passes. Do not widen I-016 to A/B or add a nonblocking notification primitive without separate evidence/authorization.
- **What are we deliberately not doing?** No new Objective entity; no broad transaction rewrite; no automatic transcript replay; no fourth persistent agent; no new embedding/memory-index architecture; no automatic model router; no CORE-enforced refresh threshold; no adjacent maintenance investigation without a demonstrated problem.

## Current focus

### I-016 — Private Principal Channel

**Scope:** [CORE + ROOM UI]

**Decision:** D-038

**Work state:** IN PROGRESS

**Reality:** IMPLEMENTED ON FEATURE BRANCH / VERIFICATION PENDING / NOT MERGED

**Authorized first release:** Agent C's root coordinator Assignment may emit structured `CONSULT_PRINCIPAL` when human judgment, authorization, or material clarification is needed. CORE records a private `principal_message` visible to the observer, creates no A/B deliveries, and moves the same Assignment to durable `waiting_principal`. The observer replies to that exact consultation event; CORE atomically rejects stale/duplicate replies, records a private `principal_reply`, and requeues the same C Assignment on its existing provider-context lineage. Private exchange is not automatically shared with A/B.

**Lifecycle:** waiting survives runtime restart; Pause preserves the wait and may accept the reply without executing until Resume; Stop/cancel terminates it with the surrounding Task. No fourth agent or human-as-agent entity is introduced.

**UI:** principal consultations render distinctly in the transcript with an inline private reply form. Existing ordinary observer messaging remains separate.

**Verification gate:** exact PR-head `verify-fast.cmd`, including the new transaction and browser regressions. Merge only the verified bytes. After merge, update Architecture/Development Control from verification-pending to the exact verified state and record evidence in the Evidence Register if the result warrants a durable evidence entry.

### Functional acceptance campaign T0-T14

**Scope:** [CORE + ROOM operational acceptance]

**Work state:** COMPLETE

**Authoritative operational procedure:** `docs/CODEX_ROOM_FUNCTIONAL_ACCEPTANCE_TEST_PLAN.md`

**Current state:** T0 through T14 are PASS and the campaign is closed. T8's initial failure was a genuine runtime-invariant failure, not permitted model variation: hard restart preserved the durable Assignment but the exact provider turn became `interrupted` and was terminally failed. PR #130 repaired and revalidated that path; E-140 owns the detailed repair evidence. T9-T14 then exercised coordinator refresh, the custom-capability lifecycle, rollover continuity, offline export/backup/verify, explicit peer model allocation, and an integrated naturalistic implementation/verification mission. E-141 records the campaign-level outcome and retained behavioral observations.

**Next:** none automatically. Preserve the acceptance plan as the repeatable regression/acceptance specification and stop here unless new evidence or explicit principal direction justifies further work.

### BCTX — bounded-context architecture program

**Scope:** [CORE]

**Decision:** D-037

**Overall work state:** COMPLETE — BCTX-1 through BCTX-4 complete

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED — BCTX-1 through BCTX-4

**Current production state:** D-037 is implemented through BCTX-4 plus the evidence-driven refresh-economics refinement. Continuous mode settles bounded Tasks and preserves deliberate C continuity across successor Tasks. A/B continuity is explicit rather than identity-based: inside a Task it follows causal Assignment lineage, and across a bounded Task boundary it requires an eligible predecessor grace source. Grace lasts through the next two successful C executions unless C closes it earlier, expires into durable provider-thread retirement, survives restart, and is retired at terminal Round boundaries while Pause preserves it. Bounded HISTORY can recover earlier settled same-Round results without replacing current transaction authority. C receives compact authoritative Task/Assignment/Join/grace state without automatic worker transcript replay and may deliberately issue `REFRESH` with a bounded checkpoint to move to a distinct fresh provider context through a fail-closed, restart-safe handoff. Eligible root-coordinator turns also receive exact-thread economics. Approximately 64K/96K last-completed-execution input-token ranges are advisory judgment guides; CORE does not auto-refresh when either range is crossed.

The program reuses the existing work-model-v2 transaction substrate. **Task is the bounded objective/activity. Assignment remains declared agent work. Join remains dependency/return state. Round remains the human-facing lifecycle/standing objective.** No new maintained Objective entity or broad v2 redesign is authorized.

The approved memory/context horizons are:

1. **Worker active context** — A/B context may be deliberately retained across explicitly causally continuous work inside the current bounded Task and, through BCTX-3's explicit grace-qualified lineage, briefly across a causally linked successor-Task boundary. This is a generic objective-local iterative-collaboration mechanism; implementation/verification/repair/re-verification is one example, not a deterministic workflow category or restriction.
2. **Coordinator continuity context** — C may carry materially longer context across successor Tasks in one continuing Round, with a later deliberate checkpoint/refresh boundary.
3. **Durable deterministic state** — Round/Task/Assignment/Join/Evidence/history/provenance remains authoritative outside provider transcript state.

Implementation order and stop boundaries follow.

#### BCTX-1 — Task-bounded continuous lifecycle and coordinator continuity

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED

**Evidence:** E-132

**Implementation:** PR #117; exact locally verified head `6871f8e45e76c783e9709b2a7feead561939a779`; canonical merge `46ee194f791cd6e2cf2a823c98e1e74a98814c7c`.

**Goal:** make each bounded coordinator activity in a continuous Round settle as its own Task while preserving the standing Round and C's useful continuity.

Required behavior:

- when the coordinator reaches the ordinary Task settlement boundary in a `continuous` Round with no open Assignments/Joins and no missing required contributor, settle the current Task instead of requeueing its terminal coordinator Assignment;
- if the hard turn limit or another terminal runtime boundary has fired, do not create successor work;
- otherwise create one successor Task in the same Round, linked through existing Task lineage (`parent_task_id` or the smallest equivalent existing mechanism);
- create the successor coordinator Assignment as fresh durable work while explicitly carrying the prior coordinator provider-context lineage forward;
- preserve the same standing Round objective and required-contributor contract;
- child Assignments remain bounded and settle normally;
- `auto_settle` Round behavior remains unchanged;
- human Stop/Pause/Resume, usage-wall continuation, exact-turn recovery, serialized execution, stale-result protection, and transaction settlement invariants remain intact;
- record enough event/provenance state to inspect each bounded Task transition deterministically.

BCTX-1 explicitly does **not** add worker context reuse, relay bypass, worker grace, same-Round HISTORY expansion, or C checkpointing.

Verification:

- focused transaction tests proving multiple settled successor Tasks inside one active continuous Round;
- exact C context-thread continuity across successor Tasks;
- no successor Task after hard turn limit/terminal stop;
- child Assignment scope remains bounded;
- existing `auto_settle` behavior unchanged;
- restart/recovery coverage at the Task-transition boundary where warranted;
- repository-standard `verify-fast.cmd` / `verify-local.ps1` verification on the exact implementation bytes;
- inspect exact diff before merge.

**Stop condition:** BCTX-1 ends when Task-bounded continuous lifecycle is exact-version verified. Do not absorb BCTX-2 mechanics merely because adjacent code is convenient to edit.

#### BCTX-2 — objective-local worker context, direct result return, and compact coordinator status

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED

**Evidence:** E-133

**Implementation:** PR #119; exact locally verified head `3a1a7f240ed43ebd4c7ea7149a5855732a23838d`; canonical merge `112b433dcc04520322da1e3048679137b3aa9f91`.

**Goal:** preserve useful A/B local cognition inside one bounded Task while removing unnecessary relay cognition and keeping C informed through compact authoritative state.

Required behavior:

- allow a later Assignment to reuse a worker provider context only through an **explicit causal context lineage** inside the same Task; common agent identity or common Task membership alone is insufficient when branches could be independent;
- preserve useful worker context across any deliberately continuous same-objective iterative collaboration inside the Task; implementation → verification → repair → re-verification is a tested example, not a special-case workflow rule;
- unrelated/new Tasks start A/B context fresh by default;
- add an explicit structured transaction mechanism allowing a child that holds the finished required result to return directly to the Task coordinator when the intermediate parent has no material intellectual work left;
- CORE must close/waive/resolve obsolete intermediate relay work mechanically and preserve exact provenance; relay bypass must never be inferred from prose;
- keep ordinary nested parent-resume behavior available when the parent genuinely has integration/correction work;
- provide C a compact deterministic Task/Assignment/Join status view sufficient to understand active ownership, dependency state, and completed/failed work without replaying worker transcript/tool chatter.

Verification should include ordinary nested delegation, direct-return delegation, parent-required integration, failure/degraded paths, parallel independent branches, restart/recovery, and exact provider-thread lineage checks.

**Stop condition:** BCTX-2 ends when objective-local continuity and direct return are verified without weakening transaction settlement or purchasing redundant model turns.

#### BCTX-3 — worker-context grace/retirement and same-Round bounded HISTORY

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED

**Evidence:** E-134

**Implementation:** PR #122; exact locally verified head `ed44f87f7648f88aca8096109a221cd00339d563`; canonical merge `25fcf4db370aa81e2cc0aa05bf1bd143c1bc8d1e`.

**Goal:** keep just-completed worker context briefly available for legitimate follow-up while preventing unrelated future work from inheriting it.

Implemented behavior:

- after a Task completes in an active continuous Round, the latest worker-owned provider contexts from that Task remain eligible for deliberate continuation through the next **two successful C executions**;
- grace ends earlier when C explicitly moves past/closes the completed objective by naming its settled Task ID;
- grace eligibility does not automatically invoke a worker or inject its transcript/result text into another Assignment;
- cross-Task continuation is explicit through `context_from_assignment_id` and is accepted only for the same worker's latest provider-thread owner from a settled ancestor Task in the same Round with remaining grace;
- successful continuation consumes the predecessor grace source and records the successor Assignment as continuation provenance;
- grace counters/state are durable on Assignment rows; expiry/explicit closure moves the context to retirement-pending, provider archival is acknowledged durably, and initialization retries pending archival after restart;
- terminal Round boundaries retire residual eligible grace; Pause preserves it;
- bounded `HISTORY` selection now retrieves completed result events from earlier settled Tasks in the **same Round** as well as earlier Rounds;
- existing same-Room authority, result-count/context bounds, exact selected-event provenance, and the rule that current transaction state comes from Task/Assignment/Join/Evidence state rather than HISTORY remain intact.

Verification on the exact implementation head: complete transaction/context suites **38/38 passed**; repository-standard fast verifier passed **54 Linux focused + 118 Windows focused + 3 browser tests** with tracked tree clean and HEAD unchanged. No GitHub-hosted workflow run was attached to the merge commit.

**Stop condition:** satisfied. Do not extend BCTX-3 into embeddings, broad summaries, a new memory database, or BCTX-4 checkpointing.

#### BCTX-4 — coordinator checkpoint and refresh

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED

**Evidence:** E-135 through E-139

**Implementation:** PR #124 established the fail-closed refresh mechanism; exact locally verified head `fdb21c60dd9f03c82111014a3987f0f783124e7c`; canonical merge `e9669a05255beb3cce73f80cc491601f99db5219`. PR #127 adds exact-thread coordinator economics and advisory refresh guidance; exact locally verified head `03bb1a898e8d2f0e5d69f6cf28cbef0a9ddb828d`; canonical squash merge `3db7442ee8181f3aca23626d98d77e996fe2bb9e`.

**Goal:** give long-lived C coordination a deliberate context-reset mechanism without losing organizational continuity or replaying the full old transcript.

Implemented behavior:

- C may issue the explicit C-only `REFRESH` action from the root Task-coordinator Assignment in production `assignment_thread` mode and provide a bounded free-form continuity checkpoint;
- CORE creates a distinct fresh C provider context, durably records the checkpoint source plus old/new context identities and execution/event provenance, and atomically switches Assignment context ownership while keeping the refreshed Assignment non-runnable;
- the checkpoint is injected only on the first turn of the fresh context; current Round/Task/Assignment/Join/Evidence/grace state is reconstructed separately from SQLite;
- the old C context must be archived before the refreshed Assignment becomes runnable;
- failure before fresh-context activation falls back to the exact old C context;
- archival failure after activation leaves the handoff non-runnable and durable; initialization/watchdog recovery retries the pending archival;
- human Stop cancels unresolved refresh handoffs with the rest of transaction work;
- refreshed C context remains the coordinator continuity source across later BCTX-1 successor Tasks;
- transaction snapshot/export exposes exact refresh provenance;
- no automatic refresh threshold or trigger is implemented. C deliberately requests refresh when fresh context is materially useful.

Verification on the exact implementation head: complete transaction/context suites **44/44 passed**; repository-standard fast verifier passed **60 Linux focused + 118 Windows focused + 3 browser tests** with tracked source clean and HEAD unchanged. One untracked local `data/` path remained outside tracked-source verification. No GitHub-hosted workflow run was attached at closeout time.

**Post-completion refinement:** E-137 demonstrated a concrete adoption/economics issue rather than a broken refresh handoff: C never invoked `REFRESH` during a 59-turn continuous run while its exact-thread execution load grew sharply. PR #127 adds deterministic self-telemetry and advisory guidance while preserving C's judgment. The initial ranges are approximately 64K to actively consider refresh and 96K to strongly prefer it at the next clean Task boundary unless continuity/integration warrants deferral. They are not context-window occupancy claims and are not automatic triggers. E-139 completed the one bounded live revalidation: C crossed the consider range at 65,796 completed-execution input tokens, chose `REFRESH` on the next C execution at 67,960, and the fresh provider thread restarted at a 21,421-token first-execution baseline before ordinary work continued to the 40-turn limit. **Live naturalistic effectiveness is therefore supported; no further patch-specific benchmark is planned.**

**Stop condition:** the four-slice BCTX program remains complete. The PR #127 refinement fixes the demonstrated information/adoption gap without reopening BCTX or authorizing broader memory/index work, automatic refresh control, or adjacent transaction redesign.

#### Program-wide constraints and verification policy

- Preserve A/B/C as epistemic peers; C coordinates without superior judgment.
- Preserve work-model-v2 Task/Assignment/Join authority, selective cognition, exact execution provenance, serialized per-agent execution, restart recovery, stale-result protection, usage-wall safety, and human stop authority.
- Prefer schema reuse. Add state only where an existing owner cannot represent the required lifecycle safely.
- Review validity attaches to exact bytes/version.
- Use focused deterministic tests during each slice and the repository-standard fast verifier before completion. Escalate to broader/manual verification when the changed risk surface warrants it.
- One bounded naturalistic exercise after the assembled behavior is available may be useful. Do not buy a large synthetic `Stay busy.` benchmark after every slice.
- Record implementation/test evidence in the Evidence Register only after it exists. Update Architecture & Current State only after implementation is evidenced.
- If implementation reveals that a settled D-037 semantic cannot be achieved safely with the planned mechanism, stop and update the decision/plan deliberately before substituting a different architecture.

### Continuous Round naturalistic acceptance

**Work state:** COMPLETE

**Decision:** D-036

**Evidence:** E-130, E-131

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED

The dedicated acceptance is complete. In Room `room_579eb5236cd246d6a1000ea3fea781d0`, prompt exactly `Stay busy.` ran under `completion_policy="continuous"`, work-model v2, and `assignment_thread` with a 500-turn ceiling. C completed four distinct bounded activities; after each coordinator `COMPLETE`, CORE emitted `continuous_round_resumed` for the same root Assignment `assignment_df0eb6faf079484682e18e21beec5dcc`. C then began a fifth bounded activity.

The human paused the Room at 42 turns. The Round and root Task remained active, with six child Assignments completed, one child still running, six released Joins, and one pending Join. This is the intended behavior: the standing objective remained active, bounded child work retained ordinary lifecycle semantics, and human pause suspended further queued work without falsely settling the transaction.

The run consumed 1,882,148 raw execution-token deltas in approximately 506 seconds. That is useful stress-test economics evidence, but the prompt was deliberately literal and open-ended with a high turn ceiling. The later E-137 run is a separate post-BCTX observation: it exposed a coordinator-refresh adoption/economics issue because C had the refresh mechanism available but lacked actionable exact-thread self-telemetry.

No further dedicated **lifecycle** acceptance run is required. The one planned post-PR-#127 naturalistic revalidation is specifically about refresh adoption/economics, not whether continuous Round lifecycle works.

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

## QoL Wishlist

**Purpose:** Retain useful quality-of-life ideas without silently promoting them into authorized implementation work.

Wishlist entries are **idea capture, not a work queue**. They have no work state merely by appearing here. When the principal explicitly selects an item for implementation, track that active work through the normal Development Control flow and verify it according to its actual risk. Prefer thin UI/operator improvements that do not disturb transaction semantics, durable state, or agent judgment.

### Initial wishlist — 2026-09-19

- **Observer composer: Enter sends; Shift+Enter inserts a newline — IMPLEMENTED / VERIFIED.** PR #133 implemented the behavior only in the ordinary observer composer, retained Ctrl/Cmd+Enter as an additional send shortcut, ignored Enter during IME composition, and added the `Enter to send · Shift+Enter for newline` hint. Exact feature head `99fb09f0c8273a918cab5ded232accad4fee3ed2` passed `verify-fast.cmd`: 63 Linux focused tests, 118 Windows portability tests, and 4 browser interaction/stability tests. Squash-merged as `74863b688962e80046944d6adda38e3c85dd20d3`.
- **Composer focus retention — IMPLEMENTED / VERIFIED.** PR #135 focuses the observer composer when a Room opens and restores focus after a successful send without forcing transcript scroll movement.
- **Auto-growing observer composer — IMPLEMENTED / VERIFIED.** PR #135 grows the ordinary observer composer from its compact height up to a bounded 180px cap (roughly eight lines at the current typography), then uses internal vertical scrolling.
- **Per-Room unsent drafts — IMPLEMENTED / VERIFIED.** PR #135 stores observer text and selected target per Room in browser-local storage, restores them across Room switches and page refreshes, isolates drafts by Room, and clears only the successfully submitted Room draft.

**PR #135 verification:** Exact feature head `8b1adf77093da1f86753f79665f03bc4ab23a39d` passed `verify-fast.cmd`: 63 Linux focused tests, 118 Windows portability tests, and 5 browser interaction/stability tests. The tracked tree was clean. Squash-merged as `7942d3f43a4871bcfe67a34c2d92efe97377f179`.

- **New-activity / jump-to-latest control.** When the human has scrolled away from the transcript bottom, keep the existing non-forced-scroll behavior but surface a visible `new events` indicator/button that jumps to the latest activity.
- **One-click operational ID copying.** Make the Room ID easy to copy and expose convenient copying for relevant Round, Task, and Assignment IDs. Consider a single `Copy diagnostics` action containing the current Room/Round/Task identifiers, status, turn count, model/effort, and runtime/source provenance.
- **Room search and filtering.** Add quick search plus simple state filters such as Active, Paused, Finished, and Archived so a growing Room list remains manageable.
- **Transcript detail/noise controls.** Allow the human to switch between conversation-focused and full-activity views or collapse low-level activity. Errors, attempt warnings, recoveries, and important lifecycle transitions should remain prominent.
- **Clear immediate action feedback.** Give obvious transient feedback for actions such as sending, copying, preparing/starting, and failures; keep error feedback visually associated with the initiating control where practical.
- **Remember harmless UI preferences locally.** Persist presentation-only choices such as transcript-detail mode, sidebar state/width, last-used observer target, and whether archived Rooms are shown. Do not turn these into CORE/institutional state unless evidence later requires it.
- **Conservative keyboard shortcuts.** Support useful navigation/focus shortcuts such as Escape to close dialogs and a shortcut to focus Room search or the observer composer. Avoid shortcuts for destructive/lifecycle actions such as Stop, Reset Agents, or Archive.
- **Copy individual agent responses.** Provide a small copy action on individual transcript messages so exact agent output can be reused without manual text selection.

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