# Codex Room — Evidence Register, Continuation

**Continues:** `07_EVIDENCE_REGISTER.md`  
**Initialized:** 2026-09-17  
**Last updated:** 2026-09-19  
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

---

### E-132 — BCTX-1 Task-bounded continuous lifecycle implemented, exact-head locally verified, and merged
**Date:** 2026-09-18
**Kind:** [CORE implementation + focused deterministic verification + repository-standard fast verification + canonical merge]
**Decision:** D-037
**Work item:** BCTX-1

BCTX-1 changes the continuous-Round settlement boundary without adding a new persistent Objective entity. Existing v2 Task is now the bounded objective/activity unit for continuous work.

Exact implementation head verified locally by the principal:

`6871f8e45e76c783e9709b2a7feead561939a779`

Implementation behavior on that head:

- coordinator `COMPLETE`/`PASS` at an ordinary continuous settlement boundary settles the current Task;
- when the Round remains active and the hard turn limit has not fired, CORE creates one successor Task in the same Round linked through `parent_task_id`;
- the successor Task preserves `required_contributors_json`;
- CORE creates a new successor C Assignment and explicitly carries the predecessor C Assignment's exact `context_thread_id` in `assignment_thread` mode;
- assignment-thread successor creation fails closed if the coordinator context lineage is unexpectedly missing;
- `continuous_round_resumed` records predecessor Task/Assignment plus successor Task/Assignment IDs;
- hard turn-limit settlement creates no successor;
- child Assignments remain bounded normally;
- A/B context remains Task-local in this slice; cross-Task worker context is deliberately fresh;
- `auto_settle` semantics are unchanged.

The principal verified the exact head from a clean tracked working tree. Focused BCTX-1 transaction selection:

`python -m pytest -q tests/test_transactions.py -k "continuous"`

Result:

- **4 passed**
- **13 deselected**
- runtime approximately **24.12 s**

Repository-standard `verify-fast.cmd` on the same exact head:

- Linux Python 3.12 focused core: **49 passed**, 2 warnings;
- Windows focused portability: **118 passed**;
- browser transcript stability: **3 passed**;
- dependency check: synchronized;
- total verifier time: approximately **79.4 s**;
- overall result: **PASS**.

Post-verification state:

- final HEAD remained exactly `6871f8e45e76c783e9709b2a7feead561939a779`;
- tracked tree remained clean;
- one untracked local `data/` path was present and was explicitly outside tracked source verification.

PR #117 merged that exact verified head to canonical `main` as merge commit:

`46ee194f791cd6e2cf2a823c98e1e74a98814c7c`

Post-merge inspection confirmed canonical `main` at that merge commit and confirmed the verified implementation head as its second parent.

**Assessment:** BCTX-1 is **IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**. This evidence does not claim BCTX-2 worker-context reuse/direct-result routing/status, BCTX-3 grace/same-Round HISTORY, or BCTX-4 coordinator checkpoint/refresh are implemented.

**Namespace note:** canonical Development Control/Architecture already reserve and cite E-125 through E-131, while the current Evidence Register body ends at E-124 before this entry. E-132 is used deliberately to avoid colliding with those pre-existing reserved references. Repair of that older documentation gap is separate maintenance.

### E-133 — BCTX-2 objective-local worker continuity, direct result return, and compact coordinator status implemented, exact-head locally verified, and merged
**Date:** 2026-09-18
**Kind:** [CORE implementation + focused deterministic verification + repository-standard fast verification + canonical merge]
**Decision:** D-037
**Work item:** BCTX-2

BCTX-2 extends the assignment-thread transaction model without adding a new persistent Objective/context entity.

Exact implementation head verified locally by the principal:

`3a1a7f240ed43ebd4c7ea7149a5855732a23838d`

Implementation behavior on that head:

- a later A/B Assignment may deliberately continue a prior same-worker provider context only through explicit same-Task causal Assignment lineage;
- ordinary later work by the same worker remains fresh by default when no lineage is requested;
- CORE validates that a requested context source belongs to the same Task and worker, has a bound provider context, is an eligible terminal source, and is the latest owner of that provider thread; settlement rechecks lineage under the Room lifecycle lock to prevent stale/forking reuse;
- context continuation is a generic objective-local iterative-collaboration mechanism rather than a workflow classifier. The tested A→B→A→B verification/repair sequence is one regression example, not a restriction on when deliberate continuity may be used;
- `DELEGATE` may explicitly request a single-child `coordinator` return mode when that child will hold the finished required result and the parent has no material intellectual work left;
- successful child `COMPLETE` may mechanically waive relay-only intermediate Assignments and route the exact result toward the Task coordinator;
- `PASS`, terminal failure, and degraded child paths do not bypass the parent; ordinary parent judgment/integration remains available;
- direct return preserves exact child result source, forwarded Assignment provenance, waived relay Assignment IDs, and released Join IDs;
- C receives bounded status-only Task/Assignment/Join state without automatic worker result text, provider transcript, or tool chatter;
- durable state additions are limited to `assignments.context_parent_assignment_id` and `assignment_joins.return_mode`;
- restart recovery preserves exact active worker context lineage where applicable.

The first local verification attempt on predecessor head `6ac98fbfade26658649ed9be57316cf395a4fe3a` exposed one stale prompt-wording assertion in `tests/test_assignment_context.py`: the old test expected the pre-BCTX-2 phrase `bounded to the current logical Assignment` after the prompt contract had intentionally changed to explicit Assignment-context lineage. That run otherwise showed 33 focused passes with one failure, and the fast verifier showed the same single assertion failure. The correction changed only that stale test assertion; CORE implementation bytes were unchanged.

The principal then verified exact head `3a1a7f240ed43ebd4c7ea7149a5855732a23838d` from a clean tracked working tree.

Focused BCTX-2 verification:

`python -m pytest -q tests/test_transactions.py tests/test_assignment_context.py`

Result:

- **34 passed**
- runtime approximately **183.76 s**

Repository-standard `verify-fast.cmd` on the same exact head:

- Linux Python 3.12 focused core: **51 passed**, 2 warnings;
- Windows focused portability: **118 passed**;
- browser transcript stability: **3 passed**;
- dependency check: synchronized;
- total verifier time: approximately **82 s**;
- overall result: **PASS**.

Post-verification state:

- final HEAD remained exactly `3a1a7f240ed43ebd4c7ea7149a5855732a23838d`;
- tracked tree remained clean;
- one untracked local `data/` path was present and explicitly outside tracked source verification.

PR #119 merged that exact verified head to canonical `main` as merge commit:

`112b433dcc04520322da1e3048679137b3aa9f91`

Post-merge inspection confirmed canonical `main` at that merge commit.

**Assessment:** BCTX-2 is **IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**. This evidence does not claim BCTX-3 worker-context grace/retirement or same-Round HISTORY, or BCTX-4 coordinator checkpoint/refresh, are implemented.

**Namespace note:** E-133 follows E-132. The older canonical Evidence Register body gap for reserved/cited E-125 through E-131 remains separate maintenance and is not repaired by this closeout.


### E-134 — BCTX-3 worker-context grace/retirement and same-Round bounded HISTORY implemented, exact-head locally verified, and merged
**Date:** 2026-09-18
**Kind:** [CORE implementation + focused deterministic verification + repository-standard fast verification + canonical merge]
**Decision:** D-037
**Work item:** BCTX-3

BCTX-3 extends the assignment-thread bounded-context lifecycle without introducing embeddings, broad transcript summaries, a new memory database, or BCTX-4 coordinator refresh mechanics.

Exact implementation head verified locally by the principal:

`ed44f87f7648f88aca8096109a221cd00339d563`

Implementation behavior on that head:

- when a bounded Task settles inside an active continuous Round, CORE stages the latest worker-owned provider contexts from that Task as grace-eligible for deliberate continuation;
- grace is bounded to the next **two successful C executions** after Task settlement and is represented durably on Assignment state so restart does not reset the window;
- C receives bounded status-only grace metadata identifying the settled Task, source Assignment, worker, and remaining C executions; worker transcript/result text is not injected by grace eligibility;
- cross-Task worker continuation remains explicit: C must supply the eligible source Assignment ID through `context_from_assignment_id`, the source must be the same worker's latest owner of that provider thread, the source Task must be settled in the same Round, and the source Task must lie in the current Task's lineage;
- successful cross-Task continuation consumes the predecessor grace source and records the successor Assignment as its continuation provenance;
- C may explicitly retire grace early by naming settled prior Task IDs when it deliberately moves past/closes those objectives;
- automatic grace expiry and explicit closure move the provider context to durable retirement-pending state; CORE archives the provider thread and records retirement after successful archive acknowledgement;
- pending retirement survives restart: initialization drains durable retirement-pending contexts and completes provider archival before ordinary Room recovery;
- terminal Round boundaries retire any remaining eligible worker contexts, while Pause preserves them;
- bounded `HISTORY` now selects durable completed Assignment results from earlier settled Tasks in the same Round as well as earlier Rounds in the same Room;
- same-Round HISTORY excludes the current Task and retains the existing global context/result bounds, exact selected-event provenance, and the rule that current Task/Assignment/Join/Evidence state remains authoritative rather than historical.

The principal verified the exact head from a clean tracked working tree. Focused transaction/context verification:

`python -m pytest -q tests/test_transactions.py tests/test_assignment_context.py`

Result:

- **38 passed** in 219.81 seconds.

Repository-standard fast verification on the same exact head:

- Linux Python 3.12 focused core: **54 passed**, 2 warnings;
- Windows focused portability: **118 passed**;
- browser transcript stability: **3 passed**;
- total verifier result: **PASS** in 106.5 seconds;
- final HEAD remained exactly `ed44f87f7648f88aca8096109a221cd00339d563`;
- tracked tree remained clean;
- one untracked local `data/` path was present and explicitly outside tracked source verification.

PR #122 merged that exact verified head to canonical `main` as merge commit:

`25fcf4db370aa81e2cc0aa05bf1bd143c1bc8d1e`

Post-merge inspection confirmed canonical `main` at that merge commit. No GitHub-hosted workflow run was attached to the merge commit, so this entry relies on the exact-head local verification above rather than claiming hosted CI verification.

**Assessment:** BCTX-3 is **IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**. This evidence does not claim BCTX-4 coordinator checkpoint/refresh is implemented.

### E-135 — BCTX-4 coordinator checkpoint/refresh implemented, exact-head locally verified, and merged
**Date:** 2026-09-18
**Kind:** [CORE implementation + focused deterministic verification + repository-standard fast verification + canonical merge]
**Decision:** D-037
**Work item:** BCTX-4

BCTX-4 completes the four-slice bounded-context program by adding a deliberate fail-closed coordinator context refresh without introducing automatic refresh heuristics, broad transcript replay, embeddings, or a new memory database.

Exact implementation head verified locally by the principal:

`fdb21c60dd9f03c82111014a3987f0f783124e7c`

Canonical pre-merge base:

`e92c825cac083d871d577195a67f07d316783095`

Exact reviewed change surface:

- `codex_room/db.py`
- `codex_room/models.py`
- `codex_room/orchestrator.py`
- `tests/test_assignment_context.py`

Implemented behavior on that head:

- adds explicit C-only `REFRESH` for the root Task-coordinator Assignment in production `assignment_thread` mode;
- C supplies a bounded free-form continuity checkpoint;
- CORE creates a distinct fresh C provider context and durably records checkpoint source, old/new context identities, source execution/event, activation/completion state, and first-turn checkpoint consumption;
- the refreshed Assignment remains non-runnable until old-context archival completes;
- current Task/Assignment/Join/Evidence/grace state is reconstructed separately from SQLite, and the old coordinator transcript is not wholesale replayed;
- fresh-context creation/activation failure before handoff falls back to the exact old context;
- old-context archival failure after activation leaves both sides non-runnable and durable recovery retries the pending handoff on initialization/watchdog;
- human Stop cancels unresolved refresh work with the transaction;
- refreshed C continuity persists across ordinary BCTX-1 successor Tasks;
- transaction snapshot/export exposes exact refresh provenance;
- no automatic refresh threshold or trigger is implemented.

The principal verified the exact head from a clean tracked working tree. Focused transaction/context verification:

`python -m pytest -q tests/test_assignment_context.py tests/test_transactions.py`

Result:

- **44 passed** in **262.40 seconds**.

Repository-standard fast verification on the same exact head:

- Linux Python 3.12 focused core: **60 passed**, 2 warnings;
- Windows focused portability: **118 passed**;
- browser transcript stability: **3 passed**;
- dependency checks remained synchronized;
- total verifier result: **PASS** in **99.3 seconds**;
- final HEAD remained exactly `fdb21c60dd9f03c82111014a3987f0f783124e7c`;
- tracked tree remained clean;
- one untracked local `data/` path was present and explicitly outside tracked-source verification.

PR #124 squash-merged those exact verified implementation bytes to canonical `main` as:

`e9669a05255beb3cce73f80cc491601f99db5219`

No GitHub-hosted workflow run was attached to the merge commit at closeout time, so this entry relies on the exact-head local verification above rather than claiming hosted CI verification.

**Assessment:** BCTX-4 is **IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**. **BCTX-1 through BCTX-4 are complete; the D-037 bounded-context program is COMPLETE.**



### E-136 — Transaction output-schema provider compatibility defect reproduced, repaired, exact-head verified, and merged
**Date:** 2026-09-18
**Kind:** [CORE provider-boundary defect / exact-head repair verification / canonical merge]
**Decision:** D-037
**Related work:** BCTX-4 post-close ordinary-use repair

A fresh post-BCTX recreation of the historical continuous `Stay busy.` exercise failed before C completed any transaction turn. The Room was configured correctly for work-model v2, `provider_context_mode="assignment_thread"`, C starter, and continuous completion, but the provider rejected the transaction response schema with HTTP 400 / `invalid_json_schema` because `retire_worker_context_task_ids` contained JSON-Schema keyword `uniqueItems`, which that response-format boundary did not permit.

The failure was a real CORE/provider-contract defect rather than a Room configuration error. CORE's Pydantic/runtime validator already enforced retirement-ID uniqueness independently, so removing the unsupported provider-schema keyword did not weaken accepted transaction semantics.

Repair PR #126 changed exactly:

- `codex_room/models.py` — removed provider-facing `"uniqueItems": True`;
- `tests/test_assignment_context.py` — added a regression asserting that the provider transaction schema contains no `uniqueItems`.

Exact repair head verified locally by the principal:

`9ccdbbef1faf6961c2bf51f16e9c9a47dd0f87ce`

Canonical base:

`c5612c9b4630e198e3eae66d02b01154c5422ec9`

Verification on the exact head:

- direct transaction-schema compatibility check — PASS;
- focused repair tests — **2 passed** in approximately **0.45 s**;
- repository-standard `verify-fast.cmd`:
  - Linux Python 3.12 focused core — **61 passed**, 2 warnings;
  - Windows focused portability — **118 passed**;
  - browser transcript stability — **3 passed**;
  - overall result — **PASS** in approximately **88 s**;
- final HEAD remained exact;
- tracked tree remained clean;
- one untracked local `data/` path remained outside tracked-source verification.

PR #126 squash-merged the exact verified implementation bytes as:

`2295d749c98e70bfe0ce490d23aba7a52b506067`

Post-merge blob comparison confirmed byte identity for both changed files between the verified head and canonical merge. No GitHub-hosted workflow run was attached.

**Assessment:** the provider-schema compatibility defect is **RESOLVED / IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**. Live provider-boundary revalidation was then supplied by E-137's successful 59-turn Room execution.

### E-137 — Post-BCTX naturalistic run exposed missing coordinator refresh adoption/economics signal
**Date:** 2026-09-18
**Kind:** [ROOM naturalistic observation / coordinator context economics / BCTX-4 adoption evidence]
**Decision:** D-037

After E-136 repaired the provider response-schema boundary, a fresh replacement Room reran the standing objective under the assembled BCTX stack:

- Room: `room_a7012ca175104f9aa52c1a640d262cca`;
- Round: `round_b6cce4d1c0874ce2bbbc7a0d853d63f0`;
- prompt: exactly `Stay busy.`;
- starter: C;
- work model: v2;
- provider context: `assignment_thread`;
- completion policy: `continuous`;
- hard turn ceiling: 500;
- shared workspace: 17 files copied from the failed predecessor Room and SHA-256 verified file-for-file before start.

The human paused the run after **59 turns** and approximately **10 minutes 36 seconds**. The Room remained operational: approximately **15 bounded Tasks** had settled and a successor activity had already begun. BCTX-1 through BCTX-3 behavior was exercised naturally, including repeated bounded Task progression, explicit worker-context continuation where useful, and worker-context retirement.

The important BCTX-4 observation was negative adoption evidence:

- C issued **zero `REFRESH` actions**;
- the export contained **zero coordinator context-refresh records**;
- C remained on the same coordinator provider-context lineage across the observed successor Tasks;
- C's completed-execution input load climbed from roughly **20,923** on the first execution to roughly **117,832** on the final observed execution;
- total raw execution-token deltas were approximately **3.605 million**;
- C accounted for approximately **2.663 million**, about **74%** of the total;
- A accounted for approximately **153K** and B approximately **790K**.

Relative to the earlier E-131 continuous acceptance, this run used approximately 92% more raw execution-token deltas for 59 versus 42 turns, with substantially higher tokens per turn. The principal's subscription meter moved from **100% to 86%** on the 5-hour allowance and **47% to 45%** on the 7-day allowance during the run; the ChatGPT session context meter itself remained unchanged during that comparison.

This evidence does **not** show that BCTX-4's fail-closed refresh mechanism is broken. It shows that merely exposing `REFRESH` with qualitative wording such as “when materially useful” did not give C enough actionable self-knowledge to recognize escalating coordinator-context cost.

**Assessment:** BCTX-1 through BCTX-3 receive further naturalistic support. BCTX-4 remains mechanically verified, but this run demonstrated an **OBSERVED ISSUE** in refresh adoption/economics information: C did not naturally choose refresh despite sharply increasing exact-thread execution load. The bounded response was to expose deterministic self-telemetry and advisory judgment guidance, not to add an automatic refresh trigger. See E-138.

### E-138 — Coordinator exact-thread economics and advisory refresh guidance implemented, exact-head verified, and merged
**Date:** 2026-09-18
**Kind:** [CORE evidence-driven refinement / exact-head deterministic verification / canonical merge]
**Decision:** D-037
**Related evidence:** E-137

PR #127 addresses E-137's demonstrated information/adoption gap while preserving the BCTX-4 authority boundary: C still decides whether to refresh; CORE supplies facts and performs the safe handoff.

Implemented behavior:

- eligible C root-coordinator turns in production `assignment_thread` mode receive deterministic telemetry for the exact provider context thread;
- telemetry includes executions carried, Tasks seen/settled on that thread, first-execution input baseline, last completed execution input/cached-input load, provider-reported cumulative input tokens, and input-load growth from baseline;
- telemetry is explicitly labeled as completed-execution load, **not** as a context-window occupancy percentage;
- approximately **64,000 last-completed-execution input tokens** is an advisory point to actively consider `REFRESH` at the next clean bounded Task boundary;
- approximately **96,000** is an advisory point to strongly prefer `REFRESH` unless a concrete continuity or integration reason makes immediate refresh materially unsafe or lossy;
- the ranges are judgment guides only. CORE does not auto-refresh because either number is crossed;
- prompt construction now occurs after initial assignment-thread binding so the very first eligible C turn can truthfully report `baseline_pending` for the exact provider thread;
- after a successful BCTX-4 refresh, the distinct new provider thread naturally establishes a fresh telemetry baseline.

Exact implementation head verified locally by the principal:

`03bb1a898e8d2f0e5d69f6cf28cbef0a9ddb828d`

Canonical base:

`2295d749c98e70bfe0ce490d23aba7a52b506067`

Exact change surface:

- `codex_room/db.py`;
- `codex_room/orchestrator.py`;
- `tests/test_assignment_context.py`.

Verification history was deliberately fail-fast and evidence-preserving:

1. The first predecessor head exposed that the economics block was absent from C's first prompt because prompt composition preceded initial assignment-thread binding. That ordering was corrected.
2. A later Linux fast-verifier run exposed an existing nondeterministic test assumption in the worker-lineage restart regression: two Assignments can share millisecond-resolution `created_at`, while random UUID IDs do not encode causal order. The test was hardened to identify the continued Assignment by identity rather than row position; no production lineage behavior changed for that correction.
3. Final exact-head verification then passed completely.

Final verification on exact head `03bb1a898e8d2f0e5d69f6cf28cbef0a9ddb828d`:

- focused correction/economics selection — **4 passed** in approximately **19.59 s**;
- complete transaction/context suites — **47 passed** in approximately **337.05 s**;
- repository-standard `verify-fast.cmd`:
  - Linux Python 3.12 focused core — **63 passed**, 2 warnings;
  - Windows focused portability — **118 passed**;
  - browser transcript stability — **3 passed**;
  - total verifier result — **PASS** in approximately **85 s**;
- final HEAD remained exact;
- tracked tree remained clean;
- one untracked local `data/` path remained outside tracked-source verification.

PR #127 squash-merged the exact verified bytes to canonical `main` as:

`3db7442ee8181f3aca23626d98d77e996fe2bb9e`

Post-merge GitHub inspection confirmed canonical `main` at that commit and exact blob identity between the verified head and merged bytes for all three changed files. No GitHub-hosted status checks or workflow runs were attached, so the executable evidence is the exact-head local verification above.

**Assessment at implementation close:** the coordinator economics/guidance refinement was **IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**. Live naturalistic effectiveness was still unverified at that point; E-139 subsequently supplies the bounded behavioral revalidation. The refinement does not reopen the completed BCTX program or authorize an automatic refresh controller.

### E-139 — Coordinator refresh-economics guidance succeeded in bounded naturalistic revalidation
**Date:** 2026-09-18  
**Kind:** [ROOM naturalistic revalidation / coordinator refresh adoption / execution-economics observation]  
**Decision:** D-037  
**Related evidence:** E-137, E-138

After PR #127 was merged and the local runtime was updated to canonical `main`, the principal staged a fresh continuous Room from the authoritative source fixture `codex-room-spontaneous-work-test.zip`. The ZIP contained exactly **17 files**; extraction into the new Room workspace was verified file-for-file with SHA-256 before the Round began.

Revalidation configuration:

- Room: `room_a441e14d5e00487ca006a2a20c35534c`;
- Round: `round_6e4c309bd94c49778022149129984297`;
- prompt: exactly `Stay busy.`;
- starter: C;
- work model: v2;
- provider context: `assignment_thread`;
- completion policy: `continuous`;
- hard turn ceiling: **40**.

The Round ran from approximately 00:37:26.793Z to 00:44:59.476Z on 2026-09-19 UTC, approximately **7 minutes 33 seconds**, and stopped normally at the configured **40-turn** limit.

The previously pending refresh-adoption question was answered positively:

- C's completed-execution input load first crossed the ~64K advisory consider range at **65,796 input tokens**;
- on the next C execution, at **67,960 input tokens**, C issued the structured `REFRESH` action with a **1,016-character** checkpoint;
- CORE recorded a completed coordinator-context handoff from provider thread `01a0b718-bea9-7dd1-8475-51a6bfc85096` to distinct fresh thread `01a0b71c-5a0a-7542-b3b4-155b067eb9b6`;
- the first completed C execution on the fresh thread established a new baseline of **21,421 input tokens**;
- ordinary continuous work then continued successfully; C's final observed completed-execution input load was **58,701**, still below the 64K consider band when the 40-turn limit stopped the Round.

Execution-economics comparison with E-137:

- total raw execution-token deltas: **1,962,660** versus approximately **3.605 million** in E-137;
- C: **1,149,451** raw tokens, approximately **58.6%** of the total, versus approximately **2.663 million / 74%** in E-137;
- A: **508,512**;
- B: **304,697**;
- normalized total: approximately **49.1K raw execution tokens per turn**, versus approximately **61.1K per turn** in E-137, about **20% lower**.

This was not a controlled identical-work benchmark: naturalistic delegated work differed between the two runs, and A performed materially more implementation work in E-139. The comparison therefore supports an observed economics improvement associated with bounded coordinator refresh; it does not establish a guaranteed percentage savings rate or causal estimate.

The pre-run subscription meter showed **86% remaining** on the 5-hour allowance and **45% remaining** on the 7-day allowance. The 5-hour window reset before a post-run reading could be captured, so no post-run 5-hour consumption delta is claimed or back-calculated.

**Assessment:** PR #127's coordinator economics/guidance refinement is **IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED / NATURALISTICALLY SUPPORTED**. The demonstrated E-137 adoption gap is supported as resolved for this bounded live exercise: C received the advisory economics, chose `REFRESH` shortly after crossing the consider range, CORE completed the fail-closed handoff, and useful work continued on the fresh context. No further patch-specific benchmark or threshold tuning is warranted absent new contrary evidence.

### E-140 — Functional Acceptance T8 exposed and verified repair of hard-restart interrupted-turn recovery
**Date:** 2026-09-19  
**Kind:** [ROOM functional acceptance / CORE restart-recovery defect / exact-head deterministic verification / natural hard-restart revalidation / canonical merge]

Functional Acceptance T8 deliberately restarted Codex Room while a live work-model-v2 transaction execution was active. The initial run at canonical commit `9a313df86db5596416b8a2135b107a33f7eeb635` caught an active C execution before restart and the Room returned as `running`, but exact-turn reconciliation then observed the persisted provider turn as `interrupted`. CORE treated that recovered interruption as a non-retryable terminal failure, so the root C Assignment and Task failed with `Codex turn was interrupted`, the Round closed `transaction_failed`, and A/B were never delegated.

The same run also exposed an acceptance-harness observability gap: top-level Room status became `finished` after the failed transaction, so checking only Room status could falsely print a successful-looking completion. The authoritative export preserved the failed transaction state.

PR #130 implemented the bounded repair:

- a provider `AgentTurnInterruptedError` is handled separately only in the transaction Assignment path;
- only an execution marked `recovering` by startup recovery may spend the Assignment's existing one-retry budget after the exact persisted provider turn is authoritatively interrupted;
- the retry remains the same durable Assignment and retains its bound assignment provider context;
- ordinary runtime interruptions remain terminal;
- exact-turn identity uncertainty remains quarantined/fail-closed;
- other terminal provider failures retain existing semantics;
- T8's PowerShell harness now checks `active_round.close_reason` and failed Task state so `transaction_failed` cannot masquerade as success.

Exact PR head verified by the principal:

`17da2833f24e9ab84416e1585bb4d00bfd0cb86f`

Verification on that exact head:

- targeted restart-recovery tests: **2 passed**, 22 deselected;
- repository-standard `verify-fast.cmd`:
  - Linux Python 3.12 focused core — **63 passed**, 2 warnings;
  - Windows focused portability — **118 passed**;
  - browser transcript stability — **3 passed**;
  - overall result — **PASS** in approximately **89.7 s**;
- tracked tree remained clean; one pre-existing untracked local file remained outside tracked-source verification.

Natural hard-restart revalidation on the same exact head:

- Room: `room_0397719906ec48e6a90515b71556cc3f`;
- evidence: `output\functional-acceptance\T8-RERUN-20260919-015831`;
- C's first exact provider turn became `interrupted` after restart;
- CORE recorded `will_retry=true` and retried the **same root C Assignment** under a new execution batch;
- the retry then delegated A and B together with differentiated independent work;
- A and B both completed;
- the dependency Join released exactly once;
- C integrated and completed the root Assignment;
- the Task settled `complete`;
- the Round closed `transaction_settled`;
- top-level Room status was `finished` with no failed Task.

PR #130 squash-merged the exact verified implementation bytes to canonical `main` as:

`f11b1d5bc02b8f8a7f9d2bcc84e3991b8c767877`

No GitHub-hosted workflow run was attached; verification is the exact-head local deterministic gate plus the natural hard-restart exercise above.

**Assessment:** the T8 hard-restart defect is **RESOLVED / IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED / NATURALISTICALLY VERIFIED**. The original failing run remains preserved as evidence of the pre-repair behavior.

### E-141 — Functional acceptance campaign T0–T14 completed with all tests PASS
**Date:** 2026-09-19  
**Kind:** [CORE + ROOM functional acceptance / integrated operational verification]  
**Related evidence:** E-140

The repeatable functional acceptance campaign in `docs/CODEX_ROOM_FUNCTIONAL_ACCEPTANCE_TEST_PLAN.md` completed T0 through T14 with every test recorded **PASS** against preserved exact-HEAD and Room/export evidence.

The campaign exercised, in sequence:

- baseline health and repository-standard fast verification;
- C-only trivial work and selective invocation;
- parallel differentiated A/B delegation;
- dependency-ordered implementation then verification;
- nested A→B delegation with direct coordinator return;
- bounded CORE source evidence;
- explicit same-worker Assignment context continuation;
- bounded same-Round HISTORY retrieval;
- hard-restart recovery during active transaction work;
- deliberate C-only coordinator `REFRESH`;
- custom-capability author/register/rediscover/invoke lifecycle;
- Room rollover continuity;
- offline export / maintenance integrity / backup / verify;
- explicit per-peer execution configuration;
- an integrated naturalistic implementation-and-verification mission.

The campaign exposed one demonstrated product/runtime invariant defect: T8's initial hard-restart run showed that an exact provider turn recovered as `interrupted` was treated as terminal. That defect was repaired and exact-head verified in PR #130, then naturally revalidated by the T8 rerun. E-140 owns the detailed defect/repair evidence.

The campaign also preserved non-blocking behavioral or operational observations rather than converting them into CORE defects:

- T6 recovered from one invalid delegation decision and one failed command while still exercising explicit A continuation lineage correctly;
- T10 required recovery from two malformed custom-capability invocations before successful invocation;
- T11 performed one unnecessary HISTORY lookup before completing rollover validation;
- T14's A implementation path included one failed command after successful artifact creation/execution, and the delegated B verification assignment returned `PASS` without a substantive audit. C compensated by using bounded CORE `read_many` evidence over the exact fixture, implementation, and generated JSON before final integration.

T14 exact tested state:

- repository HEAD: `b2ba255b19f2ad47326e9da9457a03b3edad564d`;
- Room: `room_2f804e5f1c78414f811e82fc6d30f249`;
- evidence: `output\functional-acceptance\T14-20260919-022415`;
- generated script SHA-256: `351c72f109dc981e5dbf510dc89e3baf06b7a9e0534c17252d8d4eb1113cc3ad`;
- generated summary SHA-256: `098cad458c5396be3a7ef98efc043c09086da37bf6a753001b8b9f13a5fdd3cf`;
- exact output: 5 orders, total amount 150.0, North 62.5, South 70.0, West 17.5;
- Round terminal state: `transaction_settled`.

**Assessment:** the functional acceptance campaign is **COMPLETE**. The exercised production paths are empirically supported at the recorded exact versions. No additional repair or adjacent acceptance work is warranted solely from this campaign. The preserved behavioral observations remain evidence for future comparison if they recur or become expensive; they do not currently establish a new CORE defect.

## E-142 — I-016 private principal channel exact-head verification and merge closeout

**Date:** 2026-09-19  
**Kind:** [CORE + ROOM UI implementation verification / closeout]  
**Related decision:** D-038  
**Related work:** I-016

I-016 implemented the first-release private principal consultation channel for Agent C's root coordinator Assignment.

The implemented path adds structured `CONSULT_PRINCIPAL`, durable `waiting_principal` Assignment state, exact consultation-event reply binding, same-Assignment/provider-context continuation, restart persistence, Pause preservation, Stop/cancel termination, and an observer-only private reply surface. C's consultation and the principal's reply create no normal A/B delivery or peer wakeup, and private content is not automatically promoted into shared organizational state.

Verification history preserved one useful pre-closeout correction:

- exact head `53aec1c3d317ebafeb1b2c554c7ea462e9f62b70` passed `git diff --check` but the focused Linux suite exposed a pre-existing ordering-sensitive assertion in `tests/test_transaction_evidence.py`;
- the failing test's behavioral prompt assertions already showed the intended evidence → invalid decision → retry sequence, while its final execution-state query ordered rows by millisecond `created_at` before `rowid`;
- the two affected retry assertions were changed to deterministic SQLite insertion order (`ORDER BY rowid`), matching CORE's existing use of execution row order when resolving exact prior execution history;
- no I-016 runtime semantics were changed by that correction.

Final exact feature head:

`e58c758527ae6a3954be9525b1411324e12ec7de`

The principal then ran the repository-standard exact-head verification procedure against that commit:

- `git diff --check origin/main...HEAD`: PASS;
- Linux Python 3.12 focused core: **63 passed** with 2 deprecation warnings;
- Windows focused portability: **118 passed**;
- browser transcript stability / interaction: **7 passed**;
- tracked tree: clean;
- only local untracked `data/` remained, explicitly outside tracked source.

PR #137 was re-checked as open, mergeable, and still pointing to the exact verified head before merge. No hosted commit statuses were attached, so the exact local deterministic verification above is the applicable merge evidence.

PR #137 then squash-merged to canonical `main` as:

`d57d25769a8be215cc01af354983fd9c44b10825`

**Assessment:** I-016 is **IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**. The first-release C-only private principal channel is supported by deterministic transaction and browser regression coverage at the recorded exact version. No widening to A/B and no nonblocking private-notification primitive is implied by this closeout.
