# Codex Room — Evidence Register, Continuation

**Continues:** `07_EVIDENCE_REGISTER.md`  
**Initialized:** 2026-09-17  
**Scope:** Continuation of the canonical Evidence Register. Evidence identifiers continue the existing `E-###` sequence without a new namespace.  
**Freshness:** Evidence proves what was observed at a stated time/version. It does not automatically prove every later version behaves identically.

## Continuation rule

This file is the second physical volume of the single Codex Room Evidence Register. `07_EVIDENCE_REGISTER.md` retains E-001 through E-124 and their historical record. New evidence entries continue here beginning with E-125. Cross-references may cite `E-###` without encoding the physical volume in the identifier.

---

### E-125 — Post-PR-#110 Common Cause controlled replication
**Date:** 2026-09-17  
**Kind:** [ROOM controlled replication / coordination behavior / execution economics]  
**Decision:** D-035

A fresh controlled implementation replication was run after PR #110 using:

- Room `room_01f030b67b0a44f08922391836a6fdd8`;
- Round `round_6409c600e2414a32a73a5f6f8e94bf51`;
- work-model version 2;
- `provider_context_mode="assignment_thread"`;
- starter C;
- required contributors empty;
- fresh empty workspace;
- the same controlled Common Cause implementation specification used in the prior implementation rerun;
- `max_turns=20`;
- `max_consecutive_passes=3`;
- `inactivity_seconds=1800`.

Observed sequence:

1. C confirmed the shared workspace was empty.
2. C delegated A implementation and B artifact-independent rules-audit/test-design work concurrently.
3. A implemented and tested the artifact while B returned an independent acceptance matrix.
4. After the artifact existed, C inspected the exact engine, tests, and documentation.
5. C then delegated B to black-box verify the existing artifact against the earlier audit.
6. B completed the artifact audit and found a reproducible deadlock in the approved game specification: a legal state can leave a player with one required action remaining while every enumerated action is illegal or unaffordable and no Pass/turn-completion rule exists.
7. The dependency join released; C resumed normally, integrated B's result, did not invent an unapproved rule, and requested human clarification.
8. The Room closed normally with `close_reason="transaction_settled"` after **12 of 20 turns**.

Replication result:

- the earlier terminal `Codex turn was interrupted` immediately after the verifier's artifact audit **did not reproduce**;
- artifact-dependent verification occurred only after the artifact existed: **PASS**;
- the run completed below its turn ceiling: **PASS**;
- quality was preserved: black-box verification exercised atomic rejection, final-round offer timing, Work 3 handling/action resumption, scoring/tie-break behavior, and identified the reproducible turn-completion contradiction;
- C stopped at the correct human-decision boundary instead of silently changing the approved game rules;
- PR #110's failed-delegation fallback condition **was not exercised** because no delegated implementation, correction, or investigation failed or settled empty. The tightened fallback rule therefore remains behaviorally unverified.

Execution economics:

- Room executions: **12**;
- total raw execution tokens: **953,892**;
- C: **161,672**;
- A: **309,159**;
- B: **483,061**;
- native model tool calls: **14**;
- failed tool calls: **4**;
- cached-input share: approximately **80.8%**.

The Room export does not directly expose underlying provider-response records for this run, so a provider-response count is not inferred from execution/tool-call counts.

Relative to the historical successful implementation baseline of **1,511,456 raw execution tokens**, the completed replication used **557,564 fewer tokens / 36.9% less**. This comparison is directional because the endpoints differed: the replication correctly stopped on an unresolved game-specification contradiction, whereas the historical baseline reached a competitive-play-ready implementation.

The replication used more raw tokens than the interrupted partial rerun because it continued through the complete black-box audit and coordinator integration. Do not treat completed-versus-interrupted totals as a savings comparison.

**Assessment:** D-035's dependency-aware sequencing is behaviorally supported, and the previously observed coordinator interruption was **NOT REPRODUCED** in this controlled replication. PR #110's tightened fallback allocation remains **IMPLEMENTED / EXACT-HEAD VERIFIED / BEHAVIORALLY UNVERIFIED** because its trigger condition did not occur. Stop the dedicated Common Cause synthetic benchmark series unless ordinary use demonstrates another concrete recurrence or defect. Observe the fallback rule naturally if a real failed/empty delegation occurs.

---

### E-126 — Common Cause ordinary continuation naturally exercised PR #110 fallback
**Date:** 2026-09-17  
**Kind:** [ROOM ordinary-use continuation / coordination behavior / fallback allocation]  
**Decision:** D-035

The principal chose to continue the existing Common Cause Room and workspace rather than discard already-spent work. In Round `round_f82ce430abd74a058982df25f8b4d087` of Room `room_01f030b67b0a44f08922391836a6fdd8`, the agents were given bounded authority to bring the game to a playable state before any separately authorized competitive match.

Observed sequence relevant to PR #110:

1. C delegated A to repair the turn-completion deadlock and B to perform independent audit work.
2. A implemented an explicit zero-cost `pass` action, documented it, and reported passing focused tests plus a dry full-game completion run.
3. C requested stronger tests/documentation before final integration.
4. A's follow-up returned `PASS` without performing the requested strengthening.
5. C did **not** absorb the substantial fallback work onto its accumulated coordinator context. It created a fresh bounded B assignment instead.
6. B added the requested targeted regressions and documentation clarifications, including unaffordable-offer expiry/pass behavior, Round-8 offer timing and rejection nonmutation, Work-3 defense interruption/resumption, and deterministic eight-round completion; B reported 11 passing tests and no engine-mechanic change.
7. C then prepared one final independent exact-artifact verification delegation before the Round later failed for a separate CORE lifecycle reason recorded in E-127.

**Assessment:** the exact PR #110 trigger condition occurred naturally: delegated follow-up work settled without producing the needed work, and C moved the substantial fallback to a fresh capable peer assignment. The fallback then produced the needed result. This supplies **NATURALISTIC SUPPORT** for post-PR-#110 fallback allocation. It does not prove every future failure mode or allocation choice; continued ordinary-use monitoring remains appropriate.

---

### E-127 — False coordinator interruption forensics and exact-turn reconciliation repair
**Date:** 2026-09-17  
**Kind:** [CORE observed issue / forensic diagnosis / bounded repair / verification]

The Common Cause continuation in E-126 ended with `close_reason="transaction_failed"` after CORE recorded C's final exact execution as failed with `Codex turn was interrupted`. Forensic comparison of the Room database and the local Codex SDK rollout for the same thread/turn showed the apparent interruption was false:

- coordinator thread: `01a0b0c3-a8fd-7182-9490-a550c440bc67`;
- exact final SDK turn: `01a0b0c8-c178-7f61-a6f8-a422d457c306`;
- execution batch: `batch_01137c97d0bd498cb419c59eb45cc4b1`.

The SDK rollout recorded a valid final structured C decision at approximately 19:12:30Z: C chose `DELEGATE` to `agent_a` for final independent nonmodifying verification. The rollout then recorded the response item, usage, and `task_complete`. No later SDK interruption record appeared in the inspected session tail.

The Room database nevertheless recorded that exact execution as failed, with no result or usage recorded, then failed the root assignment/task and closed the Round as `transaction_failed`. The timing was extremely tight: SDK task completion and CORE reconciliation/settlement occurred within a few hundred milliseconds.

Source inspection identified the vulnerable boundary in `codex_room/agent.py`: exact-turn history classified `status == "interrupted"` as immediately terminal while `_run_with_reconciliation` independently awaited the already-started notification stream. A transient terminal history observation could therefore win the race and cause cleanup to cancel/discard a usable notification completion that was already settling.

Repair commit:

`6b810f0e327da4055ced97f38a60977f4eba9c46` — `Fix interrupted turn reconciliation race`

The repair is deliberately narrow:

- introduces interruption-specific `AgentTurnInterruptedError` rather than treating every terminal state alike;
- gives only an authoritative `interrupted` observation a **0.05 second** bounded chance for the already-started notification stream to finish;
- accepts the usable notification completion if it settles in that narrow window;
- preserves fail-closed behavior when a genuine interruption has no usable completion;
- preserves authoritative `failed` history, including `codex_error_info` such as `usageLimitExceeded`, so a contradictory apparent notification success cannot override a real failure;
- does not create replacement work, retries, or overlapping exact turns.

Verification on the reviewed working tree before commit:

- `tests/test_agent.py`: **46 passed**;
- canonical `verify-fast.cmd`: Linux Python 3.12 focused core **49 passed, 2 warnings**; Windows focused portability **116 passed, 2 skipped**; browser transcript stability **3 passed**; overall **PASS**;
- `git diff --check`: PASS.

After commit, an additional exhaustive attempt on the exact commit produced **426 passed, 2 warnings** under Linux Python 3.12, then stopped because Python 3.11 was unavailable inside WSL. That run is therefore **incomplete**, not a full-verifier PASS, and no broader claim is made from it.

The commit was pushed to canonical `main`, and local `HEAD` and `origin/main` were confirmed equal at `6b810f0e327da4055ced97f38a60977f4eba9c46` immediately after push.

**Assessment:** the false coordinator interruption is a demonstrated **CORE lifecycle/reconciliation race**, not evidence that C's provider turn actually failed. The bounded exact-turn reconciliation repair is **IMPLEMENTED / REVIEWED / VERIFIED TO SUFFICIENT EVIDENCE / PUSHED** at the stated commit. Further synthetic reproduction is not required; monitor ordinary execution for recurrence. The interrupted Common Cause Round itself remains historically failed in durable Room state and should not be rewritten retroactively.

---

### E-128 — Windows Codex sandbox helper failure from redirected TEMP/TMP and deterministic recovery
**Date:** 2026-09-17  
**Kind:** [LOCAL environment issue / Codex sandbox provisioning / operational recovery]

After the CORE repair was restarted, the next Common Cause continuation could not execute shell commands. A, B, and C encountered the same pre-command failure: `helper_unknown_error: setup refresh had errors`. No game runtime verification actually began in that Round.

Local sandbox logs isolated the failure to the Windows sandbox setup helper attempting to grant its write ACE on the user's redirected temporary directory:

`F:\Users\strig\AppData\Local\Temp`

The helper repeatedly recorded:

`write ACE grant failed ... SetNamedSecurityInfoW failed: 5`

followed by `setup refresh had errors`. The redirect had been introduced during an earlier pytest-temp workaround by changing user-level `TEMP` and `TMP` from the Windows-profile location on `C:` to the parallel `F:` tree. ACL inspection showed the ordinary `C:\Users\strig\AppData\Local\Temp` path was owned by the user and already carried Codex sandbox-specific permissions, while the `F:` temp path was owned by `BUILTIN\Administrators` and lacked the same Codex-specific ACL arrangement.

Recovery deliberately avoided changing the F: ACL. User-level and process-level `TEMP`/`TMP` were restored to:

`C:\Users\strig\AppData\Local\Temp`

Codex Room was restarted. A one-command SDK sandbox probe using the same `openai-codex` workspace-write boundary then returned `CODEX_SANDBOX_OK`, and the newest sandbox setup log recorded:

`setup refresh: processed 2 write roots (read roots delegated); errors=[]`

No repository code change was required.

**Assessment:** the helper failure was a local environment regression caused by redirecting TEMP/TMP to a path on which Codex sandbox setup could not apply the required write ACE. It is **RESOLVED** by restoring TEMP/TMP to the Windows-profile temp directory. Do not globally redirect TEMP/TMP again merely to work around pytest cleanup without first accounting for Codex sandbox ACL/provisioning requirements.

---

### E-129 — Common Cause final exact-artifact verification and play-readiness closeout
**Date:** 2026-09-17  
**Kind:** [ROOM final verification / game artifact / ordinary-use post-repair evidence]

After E-128 restored shell execution, the existing Common Cause Room and workspace were continued without rebuilding or redesigning the game:

- Room: `room_01f030b67b0a44f08922391836a6fdd8`;
- Round: `round_557922a63c8c463ba7c40d185ddd0d58`;
- Task: `task_0649d48012f3411694bc19a0c640f94a`.

The bounded objective was the previously missing nonmodifying exact-artifact verification. B performed the substantive independent verification against the current `common_cause.py`, `test_common_cause.py`, and `README.md`; the Round recorded no persistent game-file modification.

Verification evidence reported by B and then integrated by A and C:

- `python -m py_compile common_cause.py test_common_cause.py` exited **0**;
- `python -m unittest -v test_common_cause` exited **0** with **11 passing tests**;
- a fresh temporary state rejected illegal `claim B AB` with exit **1** and `RuleError: it is not that player's turn`;
- SHA-256 of that temporary state was identical before and after the rejected command: `e97cf31b089c486f389bf9f51613839071d70b69be9058f8fbf1b5c57effe996`, demonstrating CLI rejection atomicity for the exercised case;
- from that temporary state, **48 deterministic pass actions** completed all eight rounds;
- final state reported `finished=True`, round 8, no pending offer, zero unresolved defense choices, and a final winner (`WINNER: A` under the deterministic smoke sequence);
- source review found no genuine blocker to competitive play; remaining work was characterized as optional polish.

The Round closed normally by `transaction_settled`. This is also one natural ordinary-use completion after the E-127 reconciliation repair without recurrence of the false `Codex turn was interrupted` failure; one successful continuation is supporting evidence, not proof against all future races.

Execution economics for this final verification Round:

- Room executions: **7**;
- total raw execution tokens: **280,433**;
- C: **46,646**;
- A: **45,338**;
- B: **188,449**;
- native model tool calls: **2**;
- failed tool calls: **0**.

Coordination note: C announced one independent verifier, but the actual path was C -> A -> B, with A acting as a zero-tool relay before and after B's substantive verification. B remained the independent executor, so this does not undermine the artifact result, but A's relay consumed **45,338** raw execution tokens and did not materially add verification evidence. Treat that as concrete token-economy evidence for future ordinary-use coordination; it does not justify reopening the closed synthetic benchmark series by itself.

**Assessment:** the existing Common Cause artifact is **VERIFIED PLAY-READY** for the intended three-agent competitive exercise. Competitive play remains a separate human authorization; this evidence does not itself start a match.

---

### E-130 — Continuous Round completion policy exact-head verification and merge
**Date:** 2026-09-18  
**Kind:** [CORE lifecycle feature / exact-head review / local verification / merge]  
**Decision:** D-036

PR #113 implemented explicit Round-level `completion_policy` values:

- `auto_settle` — existing/default behavior;
- `continuous` — keep a standing coordinator objective active across bounded coordinator completions.

Reviewed implementation head:

`24063623160bb7e4eff44e0932fbf1d0be00eb35`

The implementation persists the policy on the Round, exposes the choice in Room creation/New Round UI, requeues the same completed/passed coordinator Assignment at the ordinary settlement boundary in continuous mode, preserves its assignment-scoped provider context, and emits `continuous_round_resumed`. Child Assignments still complete normally.

Exact-diff review found and corrected one pre-merge prompt defect: the first continuous-mode prompt wording told every Assignment that CORE would return control to “this same coordinator Assignment,” which was false for delegated A/B child Assignments. The corrected wording explicitly states that child Assignments complete normally and must stay within their own scope. Because review validity attaches to exact bytes, the earlier four-test pass on predecessor head `e3548759ffecdef123d8cd9aee51573d16b9f125` was not used as verification of the corrected head.

Focused verification on the corrected head:

- continuous coordinator requeue through hard turn limit — PASS;
- continuous PASS does not settle the Task — PASS;
- continuous delegated child completes normally and preserves scope — PASS;
- dual-delegation regression — PASS;
- assignment-thread evidence-resume continuity regression — PASS;
- aggregate: **5 passed**.

Broader local verification on the same exact head produced:

- `git diff --check` — PASS;
- full Python suite — **428 passed, 1 failed**;
- the one failure was `test_rollover_http_endpoint_leaves_successor_preparing`, a rollover quiescence timing test unchanged from canonical `main` and outside the PR #113 diff;
- specialized browser/transcript stability — **3 passed**;
- exact local/remote feature-head agreement remained intact and the tracked working tree was clean.

The single rollover failure was investigated rather than treated as a continuous-Round regression. The test decides apparent quiescence from persisted execution state, while `rollover()` separately rejects still-active in-memory worker-slot/adapter state, creating a narrow scheduling window. The same unchanged rollover test then passed **3 consecutive focused reruns** on the exact feature head (6.04s, 5.46s, 8.33s). No product code was changed for that unrelated transient.

GitHub attached no status checks or PR-triggered workflow runs to the exact head. PR #113 was marked ready and merged with the head SHA pinned. Canonical merge commit:

`aa3c98dd81303bfd2cb5798c73dec1be2f13dcda`

Canonical `main` was then confirmed to point to that merge commit.

**Assessment:** D-036 is **IMPLEMENTED / EXACT-HEAD REVIEWED / VERIFIED TO SUFFICIENT LOCAL EVIDENCE / MERGED**. The remaining acceptance step is naturalistic runtime validation after the local installation is updated/restarted: run a Round with prompt exactly `Stay busy.`, select **Keep objective active**, use a deliberately high turn ceiling, and observe repeated coordinator return to the same standing objective until human stop or a hard boundary. That naturalistic run remains pending and is not implied by this entry.

---

### E-131 — Naturalistic continuous-Round `Stay busy.` acceptance
**Date:** 2026-09-18  
**Kind:** [ROOM naturalistic acceptance / CORE lifecycle / execution economics]  
**Decision:** D-036

A fresh Room exercised the merged continuous Round policy under ordinary runtime conditions rather than a synthetic fixture:

- Room: `room_579eb5236cd246d6a1000ea3fea781d0`;
- Round: `round_4273968a4dd54ffb8b99d5e721a0e93f`;
- Task: `task_6de7a02ca8ea483e8b852b0bb3b99795`;
- public objective: exactly `Stay busy.`;
- starter: C;
- work model: v2;
- provider context: `assignment_thread`;
- completion policy: `continuous`;
- hard turn ceiling: 500.

The human allowed the Room to run for 42 counted turns, then paused it manually after approximately 8 minutes 26 seconds.

Observed lifecycle sequence:

1. C's root Assignment was `assignment_df0eb6faf079484682e18e21beec5dcc`, with durable Assignment context thread `01a0b4f6-c404-7222-809e-521df84c8320`.
2. C completed a bounded shipment-SLA correction/integration activity. CORE emitted `continuous_round_resumed` at sequence 52 for that same root Assignment.
3. C then completed a separate Q3 service-review-note activity. CORE emitted another resume at sequence 81 for the same Assignment.
4. C completed a transaction-reconciliation-note activity. CORE emitted another resume at sequence 113 for the same Assignment.
5. C completed a billing-export incident-note activity. CORE emitted another resume at sequence 141 for the same Assignment.
6. C immediately began a fifth bounded activity concerning shipment priority parsing rather than treating the standing Round objective as satisfied.
7. The human paused the Room at sequence 181 while that fifth activity still had active transaction work.

Across the observed run, CORE therefore crossed the ordinary coordinator settlement boundary **four times** and each time returned control to the **same root coordinator Assignment** rather than settling the Task or creating a replacement coordinator Assignment. The Round objective stayed active throughout.

Child work also preserved ordinary bounded semantics. The transaction snapshot at pause contained seven child Assignments: six were completed and one was still running. Six Joins were released and one Join remained pending for the active child path. The root Task remained `active`, the Round remained `active`, and neither had a settlement/close reason. The Room itself was `paused`, demonstrating that human lifecycle control suspended further queued work without falsely settling outstanding transaction state.

The manual **stop** path was not separately exercised in this run; the human used **pause**. That does not weaken the feature-specific acceptance result because the newly introduced behavior under test was repeated coordinator requeue across ordinary settlement boundaries. Existing hard-stop semantics remain separately covered by deterministic tests and prior lifecycle evidence.

Execution economics were intentionally extreme and should be interpreted as stress-test evidence, not as an efficiency baseline:

- 42 execution-economics records;
- **1,882,148 raw execution-token deltas** in total;
- C: **919,131**;
- A: **488,906**;
- B: **474,111**;
- 13 native model tool calls;
- 0 failed tool calls;
- elapsed started-to-pause time: approximately **506 seconds**.

This cost is an expected consequence of a literal standing instruction with a very high turn ceiling: the Room kept finding useful or plausibly useful work instead of deciding that enough had been done. Busywork, diminishing-value work, or escalating token spend are legitimate future product/economic questions, but this run does not by itself establish a lifecycle defect or authorize a new optimization project.

**Assessment:** D-036 continuous Round behavior is **IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED**. The intended standing-objective lifecycle worked across four completed coordinator cycles and continued into a fifth until the human paused the Room. No further dedicated continuous-Round acceptance test is required absent a concrete recurrence or new failure mode.

