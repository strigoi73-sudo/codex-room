# Codex Room — Evidence Register, Continuation

**Continues:** `07_EVIDENCE_REGISTER.md`  
**Initialized:** 2026-09-17  
**Last updated:** 2026-09-20  
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

## E-143 — First naturalistic I-016 Room exposed C consultation-selection failure

**Date:** 2026-09-19
**Kind:** [ROOM naturalistic behavioral acceptance / observed issue]
**Related decision:** D-038
**Related work:** I-016
**Room:** `room_3c414df808d943b6994f55be191b914d`

After I-016's deterministic implementation/verification closeout, the principal ran a fresh Room specifically to exercise the private principal channel. The prepared objective explicitly required C to complete the work itself, make no A/B delegation, ask the principal privately to choose FORMAL or PLAYFUL, wait for the private reply, and only then continue.

The first C execution did not select `CONSULT_PRINCIPAL`. Instead it returned terminal `COMPLETE` with the question “Which announcement style should I use for Lantern: FORMAL or PLAYFUL?”. CORE therefore recorded an ordinary public `agent_message` to `all` and settled the original Task normally. No `principal_message`, `principal_reply`, or `waiting_principal` state occurred.

The principal then replied “Playful” through the ordinary observer composer. Because the original Task had already settled, that message was correctly processed as a new public observer message. It reopened the discussion and created new transaction work for C, A, and B. A and B both executed and produced public launch-announcement outputs, exactly the involvement the acceptance scenario was designed to avoid.

The exported Room also contains the I-016 schema/state additions such as `principal_reply_event_id`, demonstrating that this was not an old-runtime/restart mismatch. The demonstrated failure is therefore a **C action-selection / instruction-contract defect**, not a failure of the private wait/resume state machine and not an operator routing error.

The repair scope is deliberately bounded:

- strengthen C's protected structural instructions so a required principal response maps to `CONSULT_PRINCIPAL`;
- state explicitly that `COMPLETE` is terminal and must not be used merely to ask the principal a question or request a response;
- strengthen the transaction decision prompt with the same negative/positive mapping;
- add deterministic regressions asserting those instructions remain present;
- then rerun the naturalistic acceptance Room after exact-head verification.

**Assessment:** I-016 remains mechanically implemented, but the first naturalistic acceptance attempt is a **FAIL** for end-to-end behavioral usability. I-016 is reopened until the bounded repair is verified and a fresh Room demonstrates the intended private consultation path.

## E-144 — I-016 post-repair naturalistic re-acceptance passed

**Date:** 2026-09-19
**Kind:** [ROOM naturalistic behavioral acceptance / closeout]
**Related decision:** D-038
**Related work:** I-016
**Room:** `room_2613bdfdff0e4ddca15fe3ba6930029b`

After PR #139 repaired the C action-selection contract, the principal restarted on merged `main` and ran a fresh Room using the same acceptance objective that had previously failed.

The repaired Room produced the intended sequence:

- C's first substantive outcome was a `principal_message` with transaction action `CONSULT_PRINCIPAL`, destination `observer`, private visibility, `agent_readable=false`, `turn_triggering=false`, `awaiting_principal_reply=true`, and zero delivery rows;
- the consultation asked only whether Lantern should use FORMAL or PLAYFUL;
- the principal replied `Formal` through the dedicated private reply path;
- the reply was recorded as `principal_reply`, destination `agent_c`, private, non-agent-readable, non-turn-triggering, bound to the exact consultation event and the same C Assignment;
- CORE then ran that same Assignment again;
- C completed with the requested formal Lantern announcement;
- A and B did not execute: their Round agent state retained `context_consumed_at=null` and `last_outcome=null`;
- the Room finished after exactly two counted turns.

The exact Assignment throughout the consultation and completion was:

`assignment_a7c15bf5c63a48b081d9946375a46a0b`

Its durable provider context thread was:

`01a0ba61-07fb-7822-a4f5-93d5ae220e61`

The completed Task settled normally after C's final `COMPLETE` result.

**Assessment:** I-016 is **IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY ACCEPTED / MERGED**. The demonstrated first-run defect from E-143 is repaired. The current evidence supports the intended C-only private consultation flow without A/B invocation or leakage. No widening to A/B and no nonblocking private-notification primitive is implied by this acceptance.

## E-145 — C self-cognition was fixed at Terra/high; current catalog supports a wider bounded set

**Date:** 2026-09-19
**Kind:** [P1 / CORE diagnosis / zero-turn catalog verification]
**Related decision:** D-039
**Related work:** I-017

Before changing model-allocation policy, the principal ran two deterministic/local inspections.

First, a direct SQLite query over the 200 most recent Agent C `agent_executions` rows found exactly one model/effort combination:

- **200 / 200:** `gpt-5.6-terra` / `high`;
- **0 observed transitions** between model/effort combinations.

The inspected history included routine functional-acceptance work, transaction/EVIDENCE/HISTORY/REFRESH work, restart recovery, the explicit peer model-allocation test, the T14 integrated mission, and both I-016 principal-channel Rooms. The successful I-016 re-acceptance itself contained two executions of the same C Assignment and both remained Terra/high.

Source inspection explains the fixed behavior: peer child Assignments may carry `execution_config_id`, but ordinary root C Assignments were created without a selection and therefore used the Room compatibility fallback `gpt-5.6-terra` / high at claim time. The historical evidence therefore establishes a missing self-allocation surface rather than mere model reluctance.

Second, the principal reran the authenticated **zero-turn** SDK model-catalog probe against local `openai-codex==0.154.0` / `openai-codex-cli-bin==0.154.0`. The visible catalog was:

- Luna: low, medium, high, xhigh, max;
- Terra: low, medium, high, xhigh, max, ultra;
- Sol: low, medium, high, xhigh, max, ultra;
- Astra: low through ultra, still prohibited by D-028;
- GPT-5.5: low through xhigh, marked for retirement on 2026-10-14 in favor of Sol.

The principal then settled D-039: ordinary autonomous Room cognition is limited to Low/Medium/High across Luna/Terra/Sol; Sol/XHigh and Sol/Max are exceptional C-only settings requiring private Task-scoped approval; Sol/Ultra remains excluded because its provider description includes automatic task delegation; Astra remains prohibited; GPT-5.5 remains excluded.

**Assessment:** the need for I-017 is empirically demonstrated. The catalog supports the authorized bounded configuration surface, while the preceding production behavior did not let C dynamically allocate its own cognition.

## E-146 — I-017 dynamic C cognition exact-head verification and merge

**Date:** 2026-09-19
**Kind:** [CORE + ROOM UI implementation verification / restart regression / merge closeout]
**Related decision:** D-039
**Related work:** I-017

The final I-017 feature head was:

`b498709ed30541d7a673b245f19a9021eca98ee5`

The principal ran the complete exact-head verification procedure against that commit. Results:

- `git diff --check origin/main...HEAD`: PASS;
- restart-recovery regressions: **2 passed**;
- focused I-017 suite (`tests/test_transactions.py`, `tests/test_three_agents.py`, `tests/test_three_agent_ui.py`): **85 passed, 2 warnings**;
- repository-standard `verify-fast.cmd`:
  - Linux Python 3.12 focused core — **63 passed, 2 warnings**;
  - Windows focused portability — **118 passed**;
  - browser transcript stability / interaction — **8 passed**;
  - overall result — **PASS**;
- post-verification HEAD remained exactly `b498709ed30541d7a673b245f19a9021eca98ee5`;
- tracked repository state remained clean after verification; one untracked local file was reported and explicitly excluded from tracked-source verification.

The final commit on the verified head, `b498709` (`Scope fake turn namespace to principal restart test`), made only the intended test-harness correction: it removed the special fake turn-ID namespace from an unrelated restart test and applied it to the principal-wait restart test where adapter restart would otherwise recreate the same fake `(sdk_thread_id, sdk_turn_id)`.

The restart investigation established two distinct facts:

1. CORE recovery must treat durable transaction state as authoritative: a lagging active/recovering/result-ready execution is settled rather than replayed when its decision was already recorded or its bound Assignment has advanced out of `running`.
2. The remaining two-call artifact after that repair came from the fake provider resetting its turn counter after restart and colliding with CORE's deliberate unique exact-turn identity constraint; giving only the restarted principal-wait fake adapter a distinct namespace removed that harness artifact.

GitHub confirmed PR #142 was open, mergeable, and still pointed to the exact verified head before merge. Neither the exact feature head nor the squash merge had an attached GitHub Actions workflow run; the applicable implementation evidence is therefore the exact-head local deterministic gate above.

PR #142 squash-merged the verified implementation bytes to canonical `main` as:

`1806a7a16e1477f9dbe88515100f787c0389c709`

**Assessment:** I-017 is **IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**. Deterministic evidence supports ordinary C self-selection, Task-scoped exceptional approval mechanics, peer exclusion from exceptional configurations, Task-boundary ceiling expiry, and the restart-recovery repair at the exact verified version. A bounded naturalistic Room exercise remains required before I-017 is closed as end-to-end accepted.

## E-147 — I-017 ordinary C self-switch naturalistic acceptance

**Date:** 2026-09-19
**Kind:** [ROOM naturalistic behavioral acceptance / execution provenance]
**Related decision:** D-039
**Related work:** I-017
**Room:** `room_b91f31f8cccc4d6c8eb26c4c008854dd`

The principal ran a fresh bounded acceptance Room on canonical source revision `cc68344a948b4585f556be8d26c6be23b16e9fc2`. The objective required C to work alone, avoid exceptional cognition, use bounded source evidence, and deliberately select a different ordinary configuration for its next execution.

Observed durable execution provenance:

- Agent A executions: **0**;
- Agent B executions: **0**;
- Agent C executions: **2**;
- both C executions belonged to the same Assignment, `assignment_8e5c4898bfbb4af4b8da8e0e0a731042`;
- C execution 1: `gpt-5.6-terra` / high;
- C execution 2: `gpt-5.6-luna` / low;
- observed transition: **Terra/High → Luna/Low**;
- Room terminal status: `finished`;
- Room turn count: **2**;
- Task `task_fcb78782d6184b8a938dcb5c174ffe93` settled with `c_cognition_ceiling=sol-high`.

**Assessment:** the ordinary self-allocation half of I-017 is **NATURALISTICALLY ACCEPTED**. C demonstrably changed its own model/reasoning configuration between executions on the same root Assignment while A/B remained uninvolved and no exceptional Task ceiling was requested. Task-scoped exceptional approval remains a separate acceptance gate.

## E-148 — I-017 exceptional cognition naturalistic acceptance

**Date:** 2026-09-19
**Kind:** [ROOM naturalistic behavioral acceptance / execution provenance / Task-boundary scope]
**Related decision:** D-039
**Related work:** I-017
**Room:** `room_c5c830d0cf5443608c09e476e89f41dc`

The principal ran the second bounded I-017 acceptance Room to exercise exceptional C-only cognition and its Task scope. The continuous Round required C to work alone, request Sol/XHigh through the private principal channel for the first Task, use that approved configuration if authorized, then complete one successor Task without carrying the exceptional approval forward.

The exported Room showed the intended control flow:

- C emitted a private `CONSULT_PRINCIPAL` request for `requested_task_cognition_ceiling=sol-xhigh`;
- the principal replied through the dedicated private channel with `cognition_approval=approve`;
- the reply remained bound to the same first Task and root C Assignment;
- C completed the first Task with the required acceptance result;
- CORE created one successor Task in the same continuous Round;
- the first Task settled with `c_cognition_ceiling=sol-xhigh` and its C Assignment recorded `execution_config_id=sol-xhigh`;
- the successor Task settled with `c_cognition_ceiling=sol-high` and no inherited exceptional `execution_config_id`;
- A and B remained uninvolved;
- the Round then stopped at the deliberately configured three-turn limit after both bounded Tasks had completed.

The principal then queried the local durable `agent_executions` provenance for that exact Room. Results:

- Agent A executions: **0**;
- Agent B executions: **0**;
- Agent C executions: **3**;
- C execution 1: `gpt-5.6-terra` / high on `assignment_c2d504cdad10491fba41131d6bb53c36`;
- C execution 2: `gpt-5.6-sol` / xhigh on the **same Assignment** after approval;
- C execution 3: `gpt-5.6-terra` / high on successor `assignment_f59136b17cb1441b8c8de73adf228da2`;
- first Task `task_d3c3c1a51737438a83caf4625ec740e7`: settled, ceiling `sol-xhigh`;
- successor Task `task_4a4b05d25d6446dc9fea18bced2f83c3`: settled, parent first Task, ceiling `sol-high`;
- the bounded acceptance checker returned **RESULT: PASS**.

**Assessment:** the exceptional-cognition half of I-017 is **NATURALISTICALLY ACCEPTED**. The evidence demonstrates private Task-scoped approval, actual Sol/XHigh execution after approval, no peer authorization or execution leakage, and expiry of the exceptional ceiling at the Task boundary. Combined with E-146 exact-head verification and E-147 ordinary self-switch acceptance, I-017 is **COMPLETE / IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED / NATURALISTICALLY ACCEPTED**.

## E-149 — Codex Desktop ↔ Codex Room capability audit

**Date:** 2026-09-19
**Kind:** [product capability audit / CORE source inspection / current official Codex documentation]
**Related work:** I-018
**Canonical Room source inspected:** `9d875ffe71d84aa862e664d23f1aae08ac0ab65b`

### Question

What useful work can current Codex Desktop do that current Codex Room cannot, and which apparent differences are only host/UI differences over capabilities already present in the embedded Codex runtime?

### Evidence basis

Canonical Room source established that:

- `codex_room/agent.py` creates real persistent local Codex SDK/App Server threads, `ephemeral=False`, rooted in the Room workspace with `Sandbox.workspace_write`;
- turns run through the official SDK with explicit model/effort and Room decision output schema;
- Room session overrides set the model/reasoning defaults and explicitly disable `agents.enabled` and `features.multi_agent_v2.enabled`; no blanket override disables ordinary file/shell, web-search, skill, MCP, or app facilities;
- the adapter recognizes native Codex activity including command execution, file change, MCP tool calls, dynamic tool calls, web search, image view/generation, and context compaction;
- `codex_room/orchestrator.py` explicitly instructs agents to use native workspace tools for ordinary one-off reads/searches/inspection/simple commands and adds Room deterministic capabilities/EVIDENCE/HISTORY for bounded organizational use;
- `codex_room/static/app.js` sends the observer composer through the Room message API and contains no host-command parser; `codex_room/main.py` accepts those ordinary observer messages through `/api/rooms/{room_id}/messages`.

Current official OpenAI Codex documentation established that:

- Codex App Server exposes persistent thread start/resume/fork, turn execution, command/file-change items, MCP calls, web search, image viewing, review-mode items, context compaction, skills APIs, installed-app APIs, and MCP status/tool APIs;
- Codex configuration is layered: session/`--config` overrides take precedence while user `~/.codex/config.toml` and trusted project `.codex/config.toml` remain part of the effective configuration;
- web search defaults to cached mode unless disabled or changed by configuration;
- MCP configuration is shared by local Codex clients through the normal Codex configuration files;
- the ChatGPT desktop app's command palette is a host/composer interface for product actions such as plan, goal, review, status, compact, fork, and worktree-related flows;
- the Desktop built-in browser, integrated terminal, worktree manager, diff/review surface, attachment/editor surfaces, and authentication UI are host features rather than properties automatically supplied to every App Server embedding.

No model-driven acceptance Room was run because source plus current official protocol/configuration documentation resolved the product-level mechanism without buying additional cognition. Account-specific configured MCP servers, installed apps/plugins, enabled skills, OAuth state, and admin policy remain environment-dependent and are not claimed as universally present.

### Capability matrix

| Capability / Desktop surface | I-018 classification | Current Room assessment |
|---|---|---|
| Workspace reads/writes and file changes | **INHERITED** | A/B/C run in `workspace_write`; native file-change activity is supported. |
| Shell / command execution / local Git | **INHERITED** | Native command execution is part of the embedded Codex substrate and explicitly allowed for ordinary work. |
| Persistent Codex threads | **INHERITED** | Core Room execution mechanism; transaction Assignments bind durable provider context. |
| Hosted web search | **INHERITED / CONFIG-DEPENDENT** | App Server supports web search; Codex default is cached unless effective config changes/disables it; Room does not override it. |
| Configured MCP tools | **INHERITED / CONFIG-DEPENDENT** | Normal Codex config is retained and the adapter supports `mcp_tool_call`; interactive auth/elicitation is a host-surface limitation. |
| Skills | **AVAILABLE BUT HIDDEN / CONFIG-DEPENDENT** | App Server has skill discovery/invocation and normal config/search paths remain; Room has no observer skill picker or explicit structured skill input. |
| Installed apps/plugins/connectors | **AVAILABLE BUT HIDDEN / CONFIG-DEPENDENT** | App Server exposes installed-app/plugin and tool surfaces; Room does not provide browse/install/auth/manage UI. Do not assume any specific app is installed. |
| Tool/MCP OAuth, approvals, elicitation | **GENUINELY INCOMPLETE HOST SURFACE** | Room lacks a general observer interaction bridge for arbitrary tool authorization/authentication/elicitation. |
| `/status` | **AVAILABLE BUT HIDDEN** | Room already stores health/provenance, Task/Assignment state, agent status, model/effort, context/economics, and limits, but no consolidated human status surface exists. |
| `/compact` | **ROOM EQUIVALENT** | Room calls the underlying thread compaction API and also has deliberate C `REFRESH`. |
| `/model`, `/reasoning` | **ROOM EQUIVALENT / GOVERNED DIFFERENTLY** | D-039 gives C bounded cognition allocation and requires principal approval for exceptional C cognition; direct Desktop parity would bypass settled governance. |
| `/goal` | **ROOM EQUIVALENT** | Round standing objectives plus bounded Task state own organizational objective continuity; duplicating App Server goal state would create competing authority. |
| `/personality` | **ROOM EQUIVALENT** | Persistent A/B/C profiles and Room overrides own personality configuration. |
| Built-in Codex subagents / multi-agent tools | **INCOMPATIBLE BY DESIGN** | Explicitly disabled; the A/B/C organization and transaction substrate replace this layer. |
| `/review` reasoning | **ROOM EQUIVALENT** | Independent verifier work can be delegated to B or another peer; current Room does not provide Desktop's dedicated diff/review UI or a first-class read-only review mode. |
| Dedicated review diff / inline comment UI | **GENUINELY MISSING / CODING-SPECIFIC** | No Desktop-style changed-file pane, inline review comments, stage/revert/commit/push surface. |
| `/plan` plan-only mode | **PARTLY INHERITED / GENUINELY MISSING AS ENFORCED ROOM MODE** | Agents can plan on request, but Room has no first-class mechanical “plan but do not execute” mode. |
| `/fork` | **UNDERLYING API AVAILABLE; DIRECT ROOM PARITY INCOMPATIBLE** | App Server can fork one thread, but a Room is three agents plus durable transaction state; a correct Room fork is not equivalent to exposing thread/fork. |
| `/side` side chat | **GENUINELY MISSING / NO DEMONSTRATED NEED** | Room has no ephemeral human side-chat tied to a main Room; adding one would require clear state/authority semantics. |
| Desktop built-in visual browser / computer-use | **GENUINELY MISSING HOST CAPABILITY** | Web search is distinct from the shared visual browser. Room has no equivalent interactive browser host. |
| Rich user file/image attachment UX | **GENUINELY MISSING HOST SURFACE** | Underlying Codex protocol supports richer input types, but the Room observer composer/API is text-centric and does not provide a first-class attachment path. |
| Integrated human terminal | **GENUINELY MISSING UI / CODING-SPECIFIC** | Agents can execute commands; the principal has no embedded project-scoped terminal whose output is jointly visible to the Room. |
| Desktop-managed Git worktrees | **GENUINELY MISSING / CODING-SPECIFIC** | Room uses its shared workspace model and does not create/manage Desktop-style isolated worktrees for parallel chats. |
| `/init` | **INHERITED AS ORDINARY WORK** | Creating an `AGENTS.md` or equivalent file needs no special Room command; an agent can create it through normal file work if requested. |
| `/feedback`, `/pet`, other host utilities | **OUT OF SCOPE** | Product-host conveniences do not add organizational capability. |
| Host-command syntax itself | **OUT OF SCOPE / NOT A CAPABILITY** | The Room has no Codex host-command parser. Copying command syntax without a demonstrated product need would add UI ceremony, not agent power. |

### Findings

1. **The largest misconception corrected by the audit is that Codex Room agents lack Codex tools.** They already run on the Codex execution substrate. The deliberate exception is Codex's own built-in multi-agent layer.
2. **The largest actual gap is the observer host layer.** Desktop gives the human rich control/inspection surfaces around the same class of agent runtime; Room currently exposes mostly its transcript and Room lifecycle controls.
3. **Web search and visual browser are different capabilities.** The former belongs to the Codex runtime/configuration and is available subject to effective config; the latter is a Desktop host feature and is absent from Room.
4. **MCP/skills/apps are not best treated as a new Room tool architecture.** The underlying App Server already exposes these ecosystems. If ordinary use needs them, the economical direction is to expose/configure/interact with the inherited surface rather than build a competing registry. Room's own deterministic capability registry remains appropriate for Room-owned repeatable local procedures.
5. **Host-command parity is the wrong target.** Several commands duplicate settled Room semantics; others are shortcuts to Desktop-host functions. Product work should expose useful underlying capability or state, not copy syntax.
6. **No synthetic capability benchmark was warranted.** The audit is about available mechanisms and host surfaces, and the decisive facts were mechanically available from source/protocol/config documentation.

### Candidate gaps worth principal consideration

**Highest expected value / smallest conceptual change:** a consolidated **Room Status + Tools** surface showing current objective/Task/Assignment state, A/B/C status, active model/effort, recent execution economics/context indicators, and available configured skills/MCP/apps. This would make inherited capability inspectable without changing organizational authority.

**Potentially high value if external tools become normal:** a bounded **tool interaction bridge** for authentication/approval/elicitation when inherited MCP/apps require human action.

**Broad general-purpose value:** first-class **attachments/rich input** for files and images.

**Potentially very high general-purpose value but materially larger scope:** a **browser/computer-use host** integrated with Room authority and provenance.

**Lower priority absent demonstrated use:** enforced plan-only mode, Desktop-style code-review UI, human terminal, worktree orchestration, Room forks, or side chats.

**Assessment:** I-018 is **COMPLETE** as an exploratory product audit. It establishes no new implementation authorization. The next action is a principal product choice, not automatic development.

## E-150 — I-019 exact-runtime command catalog foundation exact-head verification

**Current status:** HISTORICAL / SUPERSEDED BY D-041. The verified catalog implementation below is retained as provenance but is being removed from the current Codex Room product surface.

**Date:** 2026-09-19  
**Kind:** [CORE implementation / deterministic verification / source provenance]  
**Related work:** I-019 / D-040  
**Exact implementation head verified:** `466fdb39cc60dd99fd3cd690061ab2feaea67c8d`

The first bounded I-019 implementation slice established a read-only authority layer for the Codex host-command inventory before any command dropdown or dispatcher is built.

Implemented behavior on the exact verified head:

- `CodexAgentAdapter.initialize()` records the actual running App Server identity from official SDK initialization metadata after the client is initialized;
- `CodexCommandCatalog` requires a safe nonempty runtime version and resolves built-in command source against the exact official `openai/codex` release ref `rust-v<runtime-version>`;
- synchronized manifests record runtime version, official source repository/path/ref, upstream blob SHA, synchronization timestamp, command order/names/aliases/descriptions, and dynamic-overlay metadata;
- cached manifests are accepted only when schema, runtime version, source ref/repository/path, blob-SHA shape, and command count are internally consistent;
- a newer/different runtime cannot fall back to an older cached catalog; failure to establish an exact catalog returns `status=unavailable` and an empty command list;
- `GET /api/codex/commands` binds resolution to the runtime identity captured from the active adapter and is served with `Cache-Control: no-store`;
- model service-tier commands are marked as a live model-catalog overlay and are not claimed to be present in the static manifest;
- the runtime cache is excluded from Git through `data/cache/`.

Independent source-parser check against official Codex `rust-v0.154.0` found **60 enum variants, 60 descriptions, zero missing descriptions**.

The principal then ran deterministic verification on Windows/WSL against exact head `466fdb39cc60dd99fd3cd690061ab2feaea67c8d` with a clean tracked tree. Results:

- dedicated I-019 command-catalog tests: **6 passed**;
- Linux Python 3.12 focused core: **63 passed**;
- Windows focused portability tests: **118 passed**;
- browser transcript stability: **8 passed**;
- repository fast verifier: **RESULT: PASS**;
- the only reported warnings were existing FastAPI/Starlette deprecation warnings; no test failed.

**Assessment:** the command-catalog synchronization/freshness foundation is **IMPLEMENTED / VERIFIED on the exact head above**. This does **not** verify or complete I-019 as a whole: Status & Tools UI, live service-tier overlay, Room applicability classification, command dropdown, and command dispatch remain outside this verified slice unless separately implemented and verified.

## E-151 — I-019 Status & Tools exact-head and natural rendered-UI acceptance

**Current status:** HISTORICAL FOR THE REMOVED CATALOG PORTION. The broader Status & Tools acceptance remains relevant; D-041 supersedes the catalog-specific product behavior described below.

**Date:** 2026-09-19  
**Kind:** [CORE + ROOM UI implementation / deterministic verification / live runtime check / natural rendered-UI acceptance]  
**Related work:** I-019 / D-040  
**Exact implementation head verified:** `cc785e34d9332e479e4e8b62af7ca465f5d01cc8`

The I-019 Status & Tools candidate was evaluated in two natural browser passes around one acceptance-blocking defect, with deterministic verification attached to the exact repaired implementation bytes.

### First natural acceptance pass

The initial rendered UI check used existing Room `room_a7012ca175104f9aa52c1a640d262cca` (“Stay Busy - BCTX Full Stack”) without starting new Room work. It established that:

- Current work accurately showed the active continuous Round/objective, active Task, and C/B assignment ownership/state;
- A/B/C lifecycle, model provenance, reasoning effort, queue/processing state, recent tokens/tool counts, and C context-refresh guidance were understandable;
- all five Room-native deterministic capabilities appeared Available;
- inherited workspace files, command execution, web search, skills, and plugins were classified Available while MCP and Apps/connectors were honestly shown Unknown/not inspectable;
- no secrets, absolute filesystem paths, MCP schemas/payloads, private identifiers, or hidden reasoning were exposed;
- Refresh was read-only: the Room remained paused at 59 turns / 249 events with the same active Round, Task, assignments, and idle A/B/C state;
- the browser console reported zero errors.

That run correctly **failed** acceptance because the rendered Exact Codex host-command catalog showed Unknown / 0 built-ins. The underlying endpoint returned `runtime_version_unavailable`: the running runtime identity could be displayed, but the strict catalog validator rejected the SDK-supplied version string as an unsafe release identifier.

### Defect diagnosis and repair

Source inspection against official Codex `rust-v0.154.0` showed that the App Server initialize response exposes its build version in the authoritative `userAgent`, while the Python SDK's legacy metadata normalization can backfill `serverInfo.version` with the remaining OS/user-agent suffix attached. Codex Room had passed that expanded string into the intentionally strict D-040 release validator.

The repair preserves fail-closed catalog semantics. At the SDK metadata boundary, Codex Room now accepts an already-safe `serverInfo.version` unchanged; otherwise it extracts only the leading App Server product/version token from the authoritative user-agent and requires it to agree with any SDK-backfilled server-info fields. Metadata disagreement still returns no runtime identity. Regression coverage includes both the real expanded 0.154.0 shape and a mismatch that must fail closed.

### Exact-head deterministic and live verification

The principal synchronized to exact repaired head `cc785e34d9332e479e4e8b62af7ca465f5d01cc8` with a clean tracked tree. Results:

- focused `tests/test_codex_commands.py` + `tests/test_status_tools.py`: **13 passed**;
- Linux Python 3.12 focused core: **63 passed**;
- Windows focused portability tests: **118 passed**;
- browser transcript stability: **9 passed**;
- repository fast verifier: **RESULT: PASS**;
- only existing FastAPI/Starlette deprecation warnings were reported;
- live `/api/health`: healthy;
- live runtime identity: `codex_python_sdk` / `0.154.0`;
- live `/api/codex/commands`: `status=current`, `runtime_version=0.154.0`, `source_ref=rust-v0.154.0`, `command_count=60`.

### Final rendered-UI recheck

A deliberately bounded second browser check did not repeat the already-passed wider acceptance campaign. On the same exact repaired head, the actual Status & Tools dialog visibly showed:

- runtime `0.154.0`;
- Exact Codex host-command catalog **Available**;
- **60** built-in commands;
- source `rust-v0.154.0`.

After one Refresh, those values remained visible. The Room remained paused at 59 turns / 249 events with the same active Round; A, B, and C remained idle; no new Room activity appeared; and the browser console reported zero errors and zero warnings. The surrounding Current work, Agents & economics, Room-native capabilities, and inherited Codex sections appeared normal.

The first natural browser campaign consumed roughly **6% of the principal's five-hour Codex allowance**. That cost is process evidence, not a product defect: future verification should keep deterministic Git/test/API checks mechanical and use Codex for browser/UI or multi-step local work where that interactive capability earns its model cost.

**Assessment:** I-019 is **COMPLETE / IMPLEMENTED / VERIFIED** on exact implementation bytes `cc785e34d9332e479e4e8b62af7ca465f5d01cc8`. The intended first-release Status & Tools surface satisfies its deterministic and natural rendered-UI acceptance target. This closeout does not authorize host-command dispatch, OAuth/elicitation bridges, attachments, browser/computer-use integration, or any later roadmap stage.

## E-152 — Post-I-019 Codex host-command catalog removal exact-head verification

**Date:** 2026-09-19
**Kind:** [CORE + ROOM UI cleanup / deterministic verification / exact-diff review]
**Related work:** D-041 / post-I-019 cleanup
**Exact implementation head verified:** `d77e020588cf548580937a146877a15e7a76f5f4`

The principal synchronized the local `i019-remove-slash-command-surface` branch to the exact candidate head above with a clean tracked tree and ran the repository-standard fast verification gate after `git diff --check`.

Results:

- `git diff --check origin/main...HEAD`: **PASS**;
- Linux Python 3.12 focused core: **63 passed, 2 existing deprecation warnings**;
- Windows focused portability tests: **118 passed**;
- browser transcript stability: **9 passed**;
- repository fast verifier: **RESULT: PASS**;
- tracked worktree after verification: **clean**.

Exact-diff review confirmed that the cleanup removes the Codex host-command catalog parser/cache module, dedicated catalog API endpoint, Status & Tools catalog payload/card, browser fixture content, and catalog-specific tests. General App Server runtime identity provenance is preserved by retaining `sdk_server_identity()` in `codex_room/agent.py`, with its normalization/fail-closed regression coverage moved into the remaining Status & Tools test module.

The reviewed cleanup also updates current Project documentation so D-040 and the catalog-specific portions of E-150/E-151 remain historical provenance while D-041 governs current product behavior. Skills remain deferred and no replacement command surface or dispatch mechanism is introduced.

**Assessment:** the D-041 cleanup implementation is **IMPLEMENTED / VERIFIED** on exact source/test bytes `d77e020588cf548580937a146877a15e7a76f5f4`. A later documentation-only closeout commit may record this result without changing the verified source/test bytes.


## E-153 — I-020 Stage A native Codex skills and Skill Creator proof

**Date:** 2026-09-20
**Kind:** [ROOM naturalistic capability evidence / execution economics]
**Related work:** I-020
**CORE changes during exercise:** none

A fresh production work-model-v2 Room ran the bounded I-020 Stage A exercise with C coordinating A and B. C assigned A `terra-medium` for the autonomous spreadsheet leg and B `sol-medium` for the explicit document-skill + Skill Creator leg.

### Capability results

The active runtime exposed the relevant predefined skills, including:

- `skill-creator`;
- `spreadsheets:Spreadsheets`;
- `documents:documents`.

Agent A received a workbook assignment that deliberately did not name or suggest a skill. A reported independently selecting the predefined spreadsheet workflow and created `i020-stage-a/autonomous-skill-test.xlsx`. Direct artifact inspection confirmed the required Data and Summary sheets, formula-derived row totals, formula-derived grand total 15.5, and no formula errors. No separate durable native skill-invocation event was exposed, so autonomous skill choice is agent self-report corroborated by the observed workflow/artifact rather than independently provable from the artifact alone.

Agent B explicitly used `documents:documents` to create and render/inspect `i020-stage-a/explicit-skill-test/tiny-workspace-note.docx`. The workflow loaded the skill instructions, performed render/visual QA, corrected a presentation defect, and re-rendered the result. Again, no separate durable `SkillInput`/dispatch audit event was exposed.

Agent B explicitly used `skill-creator` to create exactly one Room-local skill at `.agents/skills/i020-line-normalizer/` with:

- `SKILL.md`;
- `agents/openai.yaml`;
- `scripts/normalize_lines.py`.

Skill Creator's structural validator returned `Skill is valid!`. The deterministic helper accepts input/output paths, removes blank lines, trims surrounding whitespace, sorts case-insensitively, uses no network access, and emits `I020_LINE_NORMALIZER_V1`. A direct helper test succeeded.

After creation, the resumed runtime listed `i020-line-normalizer` from the Room-local skill root. C then delegated the required cross-agent reuse to A. A read the created skill instructions, invoked the supplied helper rather than reimplementing it, and produced the expected normalized output:

`Apple`
`apple`
`banana`
`Cherry`
`zebra`

The adjacent evidence file recorded `I020_LINE_NORMALIZER_V1`. No CORE, global-skill, or Codex Room deterministic-capability registration change occurred during the exercise.

### Boundary result

Stage A demonstrates that Codex Room agents can already:

- discover relevant native/predefined Codex skills;
- select a relevant skill autonomously;
- follow a principal/coordinator request to use a named skill;
- use Skill Creator to create a Room-local skill with a deterministic helper;
- have a different agent discover and reuse that new skill.

Therefore a Room-specific native `SkillInput` invocation bridge is **not currently justified**. The missing property is stronger durable, independently auditable skill-invocation provenance; that is a provenance limitation, not a functional blocker.

### Execution economics

The exercise was far more expensive than the small artifacts imply.

Recorded execution-token deltas sum to approximately **5,278,785** across the Room:

- C: approximately **92,599**;
- A: approximately **764,011**;
- B: approximately **4,422,175**.

The dominant event was B's first `sol-medium` assignment for explicit document-skill use plus Skill Creator:

- **61 tool calls**;
- **4,326,764 execution tokens**;
- **11 failed tool calls**;
- about **70,931 tokens/tool call**.

A's main `terra-medium` spreadsheet execution used:

- **13 tool calls**;
- **534,421 execution tokens**;
- **1 failed tool call**.

The principal independently observed that this Room consumed roughly **30% of the five-hour Codex allowance** before the approaching refresh. The provider meter is aggregate and should not be treated as exact per-Room attribution; it is retained as corroborating operational evidence.

**Assessment:** Stage A is **COMPLETE / VERIFIED** for functional native-skill use. It simultaneously establishes a serious economics warning: skill workflows can trigger very large model/tool execution costs even for tiny artifacts. I-020 Stage B should therefore add a policy hierarchy and an explicit cost guard, while Stage C remains unwarranted absent a demonstrated native-invocation reliability gap.


## E-154 — I-020 Stage B native-skill policy exact-head verification and merge

**Date:** 2026-09-20
**Kind:** [CORE protected-instruction implementation / exact-head deterministic verification]
**Related work:** I-020 Stage B
**Exact implementation head verified:** `5b97c584ef30bcfa167e2337f59c09ee55ed7ebd`
**Canonical squash merge:** `70cb80ee25281f5217213953e40b7657e68148f2`

Following E-153's natural Room proof, Stage B made the smallest CORE change justified by the evidence. It added protected guidance for both ordinary and transaction-assignment prompts so A/B/C:

- prefer an existing enabled Codex skill when it materially fits;
- do not run heavyweight skill workflows merely because a skill exists; expected workflow/tool cost must earn its value unless the principal explicitly requests the skill;
- check existing Codex skills before inventing a new reusable workflow or custom deterministic mechanism;
- prefer native Skill Creator for genuinely missing reusable workflows;
- keep agent-created skills Room-local under `.agents/skills/` by default;
- may use bounded deterministic helpers inside a skill when they improve reliability or avoid repeated model work;
- may not create or modify user-global or administrator-scope skills without explicit principal authorization;
- may not enable Codex built-in subagents through a skill;
- promote/register skill machinery as a Codex Room deterministic capability only when stronger exact semantics, independent reuse, provenance, declared side effects, verification, or lineage continuity materially earns the added governance cost.

No skill catalog, slash-command surface, or Room-specific `SkillInput` bridge was added.

The first verification attempt exposed a test-only case-normalization bug: the transaction prompt was lowercased but compared against an assertion containing uppercase `Codex`. Runtime prompt inspection showed the Stage B policy was already present. The regression assertion alone was corrected, producing the exact candidate above.

The principal then verified exact head `5b97c584ef30bcfa167e2337f59c09ee55ed7ebd` with a clean tracked tree:

- `git diff --check origin/main...HEAD`: **PASS**;
- focused I-020 regressions: **2 passed**;
- Linux Python 3.12 focused core: **63 passed, 2 existing deprecation warnings**;
- Windows focused portability: **118 passed**;
- browser transcript stability: **9 passed**;
- repository fast verifier: **RESULT: PASS**;
- final HEAD remained exactly `5b97c584ef30bcfa167e2337f59c09ee55ed7ebd`;
- tracked tree remained clean.

PR #157 then merged that exact reviewed candidate by squash to canonical `main` as `70cb80ee25281f5217213953e40b7657e68148f2`.

**Assessment:** I-020 Stage B is **COMPLETE / IMPLEMENTED / VERIFIED / MERGED**. Current evidence does not justify Stage C's explicit skill-invocation bridge. The next bounded work is Stage D: persistence of selected Room-local skills across Room rollover.


## E-155 — I-020 Stage D Room-local skill rollover exact-head verification and merge

**Date:** 2026-09-20
**Kind:** [CORE rollover persistence / exact-head deterministic verification]
**Related work:** I-020 Stage D
**Exact implementation head verified:** `e4391ec18daca81038bf2d8d3e50c78ca3b22ddf`
**Canonical squash merge:** `7740067fcecf31c0cf7b417365a47a0814a6bef5`

Stage D implements lineage-local persistence for native Codex skills created inside a Room. Direct valid packages under `.agents/skills/<name>/SKILL.md` are copied into the successor Room through the existing atomic rollover staging path. The implementation does not copy arbitrary predecessor workspace state and does not promote Room-created skills into user/global scope.

The inherited skill path is deliberately bounded and fail-closed:

- only direct skill-package directories with a regular `SKILL.md` are treated as lineage skills;
- unrelated workspace files and unrelated `.agents` state remain excluded;
- directories under `.agents/skills` without a direct regular `SKILL.md` are not inherited;
- source and destination skill trees reject symlinks and unsupported filesystem entries;
- inheritance is bounded to 1,024 files and 64 MiB total;
- copied files are rehashed before the staged workspace is exposed;
- rollover events record inherited skill names/counts, file/byte counts, and a deterministic tree SHA-256;
- no automatic user/global skill promotion occurs.

The principal verified exact head `e4391ec18daca81038bf2d8d3e50c78ca3b22ddf` with a clean tracked tree:

- `git diff --check origin/main...HEAD`: **PASS**;
- focused I-020 Stage D rollover tests: **4 passed, 2 existing deprecation warnings**;
- Linux Python 3.12 focused core: **63 passed, 2 existing deprecation warnings**;
- Windows focused portability: **118 passed**;
- browser transcript stability: **9 passed**;
- repository fast verifier: **RESULT: PASS**;
- final HEAD remained exactly `e4391ec18daca81038bf2d8d3e50c78ca3b22ddf`;
- tracked tree remained clean.

The focused rollover cases covered exact Room-local skill inheritance plus exclusion of unrelated state, exact registered custom-capability inheritance, verified institutional-release materialization, and stable configuration/checkpoint rollover behavior. PR #159 then squash-merged the exact verified Stage D candidate to canonical `main` as `7740067fcecf31c0cf7b417365a47a0814a6bef5`.

**Assessment:** I-020 Stage D is **COMPLETE / IMPLEMENTED / VERIFIED / MERGED**. Stage C remains unwarranted by current evidence. The next bounded work is Stage E: reconcile D-022 with the now-demonstrated native-skill / Skill Creator / lineage-persistence hierarchy.


## E-156 — I-020 Stage F consolidated acceptance and closeout

**Date:** 2026-09-20
**Kind:** [acceptance synthesis / closeout]
**Related work:** I-020
**New model-heavy Room run:** none

Stage F reviewed the I-020 acceptance target against the already-recorded exact evidence rather than purchasing another naturalistic skill exercise. No acceptance requirement remained materially unproven.

Acceptance mapping:

1. **A/B/C can use a relevant predefined Codex skill without user micromanagement when the task naturally calls for it — VERIFIED.** E-153 records A receiving a workbook task whose assignment deliberately did not name or suggest a skill; A independently selected the predefined spreadsheet workflow and produced the required workbook. Native invocation provenance is weaker than Codex Room capability provenance, but the behavior itself was demonstrated.

2. **The principal can direct a specific skill without a copied Desktop/TUI command palette — VERIFIED TO THE I-020 PRODUCT REQUIREMENT.** The Stage A Room was launched from a principal-authored directive requiring explicit use of an exact discovered predefined skill; C then explicitly assigned the exact `documents:documents` skill to B and the task completed through ordinary Room/Codex prompting. This establishes that named-skill direction works without a copied host command surface or Room-specific `SkillInput` bridge. It does not create a separate durable native-skill invocation audit event.

3. **Skill Creator can produce a bounded Room-local skill with a deterministic helper that another Room agent can use — VERIFIED.** E-153 records `.agents/skills/i020-line-normalizer/` with `SKILL.md`, `agents/openai.yaml`, and `scripts/normalize_lines.py`; Skill Creator validation passed, the deterministic helper emitted `I020_LINE_NORMALIZER_V1`, and a different peer later discovered and used the skill/helper to produce the exact expected normalized output.

4. **Skill creation does not silently escape Room scope or enable Codex built-in subagents — VERIFIED TO THE IMPLEMENTED POLICY/BOUNDARY.** E-153 created the skill only in the Room workspace and made no global-skill or CORE registration change. E-154's protected policy requires explicit principal authorization for user-global/administrator-scope skill changes and forbids enabling Codex built-in subagents through skills. E-155 preserves the skill only within Room lineage during rollover rather than promoting it globally.

5. **Existing deterministic capabilities remain the stronger governed tier rather than being duplicated by default — VERIFIED / DECIDED.** E-154 implements the policy boundary and D-042 settles it: existing suitable native skill first, Skill Creator for a missing reusable workflow, bounded skill-local deterministic helper when sufficient, then Codex Room capability registration only when stronger typed contracts, permissions/side effects, exact identity, verification/provenance, independent reusable invocation, or institutional continuity justify the added governance cost. No parallel skill catalog or invocation subsystem was built.

6. **Implemented rollover continuity preserves exact intended skill bytes/provenance — VERIFIED.** E-155 records exact-head deterministic tests proving Room-local skill packages survive rollover through the atomic staging path, copied bytes are rehashed, a deterministic tree SHA-256 is recorded in rollover events, unsafe filesystem structures fail closed, and unrelated workspace/.agents state remains excluded.

Stage C's structured `SkillInput` bridge remains **NOT WARRANTED BY CURRENT EVIDENCE**. It remains a future fallback if native invocation later demonstrates a concrete reliability or latency gap.

The Stage A economics warning remains material: the bounded naturalistic exercise recorded about **5.28 million execution-token deltas**, dominated by the Sol/Medium document + Skill Creator assignment. Repeating that exercise solely for closeout would add cost without materially improving confidence.

**Assessment:** I-020 is **COMPLETE / IMPLEMENTED / VERIFIED**. The acceptance target is satisfied by E-153 through E-156 plus D-042. No further I-020 implementation or dedicated naturalistic testing is authorized absent new evidence of a specific skill-integration defect or gap.


## E-157 — I-021 Stage A exact 0.154 plugin-contract audit; Windows loopback boundary pending

**Date:** 2026-09-20
**Kind:** [CORE/App Server source audit / plugin-management authority boundary]
**Related work:** I-021
**Plugin state changed:** none
**Evidence state:** VERIFIED for source-level native contracts and install refresh semantics; NEEDS VERIFICATION for exact Windows sandbox loopback reachability

I-021 Stage A audited the exact OpenAI Codex Python SDK/App Server release admitted by Codex Room's dependency floor/current package line: `openai-codex` 0.154, corresponding to upstream Codex source commit `9fd29dfd8c583e93855aeb2a51e1725346765162`. No plugin install, enable, disable, uninstall, marketplace mutation, authentication flow, or Codex configuration write was performed.

### Native plugin contracts

The generated Python SDK types in the 0.154 release expose the plugin/configuration contracts required for a bounded Room bridge, including:

- `PluginListParams`, `PluginInstalledParams`, `PluginInstallParams`, `PluginInstallResponse`, and `PluginReconcileParams/Response`;
- `ConfigValueWriteParams` and `ConfigWriteResponse`;
- plugin summary state including stable plugin ID, installed/enabled state, local/remote version, install policy and its source, auth policy, availability, disabled reason, eligible plan types, and interface metadata;
- availability values `AVAILABLE` / `DISABLED_BY_ADMIN`, install-policy values `NOT_AVAILABLE` / `AVAILABLE` / `INSTALLED_BY_DEFAULT`, and auth-policy values `ON_INSTALL` / `ON_USE`;
- marketplace kinds for local, vertical, workspace-directory, shared-with-me, and created-by-me-remote catalogs.

The exact App Server protocol routes include `plugin/list`, `plugin/installed`, `plugin/reconcile`, `plugin/read`, `plugin/install`, `plugin/uninstall`, `config/read`, `config/value/write`, and `config/batchWrite`.

### Installation and enablement behavior

The exact 0.154 install processor requires exactly one native marketplace locator: local `marketplacePath` or `remoteMarketplaceName`. The Room bridge therefore does not need and should not invent a package installer.

After a successful local plugin install, App Server:

- reloads current user configuration;
- clears plugin and skill caches;
- refreshes configuration for existing threads;
- invalidates MCP runtimes;
- refreshes hook runtimes;
- starts native MCP OAuth handling when declared by the plugin;
- evaluates plugin apps that still need authentication;
- returns `authPolicy` plus `appsNeedingAuth`.

Remote install similarly uses the native remote catalog/install path and distinguishes policy/admin-disabled and not-available failures. This is evidence that a successful install does not require a Codex Room process restart merely to refresh existing App Server threads.

Codex TUI's own plugin toggle path writes `plugins.<plugin_id>` with value `{"enabled": <bool>}` through `config/value/write` with merge strategy `Upsert`. The config processor clears plugin/skill caches and emits toggle telemetry. `plugin/reconcile` explicitly reports plugin changes including enablement changes; it is a change/reconciliation report, not by itself a runtime-readiness guarantee. Stage B should therefore follow a mutation with authoritative reinspection of installed plugin plus skill/MCP/app state rather than infer contributed capability readiness from the write response alone.

### Principal-only authority boundary

Current Codex Room binds its browser/API host to `127.0.0.1:8765` by default and does not currently place an authentication middleware boundary around its ordinary localhost API. Therefore a future state-changing plugin endpoint cannot be called “principal-only” merely because it is a POST request or because it is local.

A/B/C threads are started with the SDK's `Sandbox.workspace_write` preset. In 0.154 that preset maps to workspace-write with direct network disabled. macOS sandbox source explicitly gates loopback access, and Windows source applies the no-network environment treatment for the default workspace-write permission profile. However, source inspection did **not** establish with sufficient confidence that a direct Windows process in the actual Codex Room sandbox cannot connect to `127.0.0.1:8765`; the Windows filtering rules inspected are not sufficient evidence for that exact negative claim.

The release provides a deterministic `codex sandbox` CLI that can run an arbitrary command directly under the same built-in `:workspace` permission profile without a model turn. This permits a cheap exact-runtime loopback probe against read-only `GET /api/health` before Stage B.

### Stage A disposition

Stage A remains **IN PROGRESS** solely on the principal-authority boundary. The native plugin/configuration contract itself is sufficient for a narrow Stage B bridge and does not justify direct config-file editing, a parallel plugin registry, a copied marketplace, or a new plugin runtime.

**Required closeout evidence:** on the principal's actual Windows Codex runtime, run one deterministic `codex sandbox --permission-profile :workspace` command that attempts only a short-timeout connection to the Room health endpoint. Record whether the sandboxed command can reach loopback. No plugin state or configuration is to be changed by that probe.

## E-158 — I-021 exact Windows workspace-write loopback probe

**Date:** 2026-09-20
**Kind:** [exact-runtime deterministic Windows sandbox probe / authority-boundary evidence]
**Related work:** I-021 Stage A
**Plugin/configuration state changed:** none
**Evidence state:** VERIFIED

The principal ran the bounded Stage A probe against the live Codex Room service on Windows. The principal host first confirmed `GET http://127.0.0.1:8765/api/health` was reachable and healthy.

The probe then resolved the exact runtime used by Codex Room:

- `openai-codex` SDK: **0.154.0**;
- runtime source: **SDK-pinned runtime**;
- executable: `C:\\Codex Room\\.venv\\Lib\\site-packages\\codex_cli_bin\\bin\\codex.exe`;
- CLI version: **codex-cli 0.154.0**.

Using that exact executable, the probe ran an arbitrary PowerShell command through:

`codex sandbox --permission-profile :workspace --cd "C:\\Codex Room" ...`

The sandboxed command attempted only a short-timeout GET to the Room health endpoint and returned:

`LOOPBACK_REACHABLE HTTP_STATUS=200`

with sandbox command exit code **0**.

**Assessment:** on the principal's actual Windows Codex Room runtime, an A/B/C-equivalent workspace-write sandbox can directly reach the localhost FastAPI service. Localhost binding, HTTP method choice, and the current workspace-write sandbox therefore do not provide a principal-only authority boundary for plugin mutation. Stage B must introduce a separate mechanical principal-proof mechanism before any state-changing plugin route is exposed.

This result closes the sole pending Stage A runtime fact identified by E-157. Stage A is **COMPLETE / VERIFIED** for the bounded contract-and-authority audit. I-021 remains **DECIDED-NOT IMPLEMENTED** until later stages implement and verify the mutation path.

## E-159 — I-022 exact Codex 0.154 native-capability source audit

**Date:** 2026-09-20
**Kind:** [exact upstream source/SDK audit / capability exposure economics]
**Related work:** I-022 Stage A
**Runtime version audited:** Codex / openai-codex **0.154.0**, upstream tag `rust-v0.154.0`
**Room runtime behavior changed:** none
**Evidence state:** VERIFIED for source-level contracts and current Room host/source gaps; NEEDS VERIFICATION for any future principal-facing exposure

The audit compared the exact upstream Codex 0.154 App Server protocol and Python SDK against current Codex Room source. It deliberately distinguishes three facts: a native primitive exists in 0.154; Codex Room's SDK/runtime can call it; Codex Room currently exposes it to the principal. The first two do not imply the third.

### Exact 0.154 native primitives verified

The App Server protocol registers these relevant routes:

- `turn/steer`;
- `turn/interrupt`;
- `review/start`;
- `model/list`;
- `thread/list`, `thread/read`, `thread/fork`, `thread/archive`, and `thread/unarchive`;
- `account/rateLimits/read`;
- `account/usage/read`;
- `permissionProfile/list`;
- server requests `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/permissions/requestApproval`, and `item/tool/requestUserInput`.

The 0.154 turn protocol accepts structured `UserInput` variants including remote image and local-image input in addition to text, skill, mention, audio, and local-audio forms.

The exact 0.154 Python SDK directly exposes high-level client methods for:

- `turn_interrupt(...)`;
- `turn_steer(...)`;
- `model_list(...)`;
- thread start/resume/list/read/fork/archive/unarchive/name/compact and goal operations.

The generated 0.154 Python types also include typed response models for `ReviewStartResponse`, `GetAccountRateLimitsResponse`, `GetAccountTokenUsageResponse`, `PermissionProfileListResponse`, `ModelListResponse`, `TurnSteerResponse`, and `TurnInterruptResponse`. Codex Room already uses the SDK's lower-level request path for exact App Server calls in Status & Tools, so absence of a convenience wrapper is not itself a substrate blocker.

### Current Room-side observations

Current Codex Room source already uses active-turn interruption internally through the SDK turn handle for lifecycle cancellation/Stop and recovery. Therefore a future principal-facing interrupt control would primarily be a host/authority/product-surface decision rather than a new Codex substrate integration.

The current observer message model remains text-only (`content: str`) and the observer message endpoint accepts that text model. Thus image/file input is currently a genuine Room host/input gap even though the pinned Codex turn protocol already accepts image/local-image input.

Current Room architecture deliberately substitutes its own mechanisms for native multi-agent orchestration: A/B/C transactions, assignment-scoped contexts, D-039 model allocation, Round/Task state, and REFRESH remain authoritative. This audit does not justify enabling Codex built-in subagents or autonomous fan-out.

### 0.154 release evidence relevant to the audit

The upstream 0.154 release notes additionally identify release-level work for inline user questions while Codex continues, usage-capability reads, experimental managed worktrees, durable reasoning configuration updates, managed Windows App Server lifecycle, and plugin refresh across existing sessions. Release-note presence is useful orientation but does not by itself establish a Codex Room product surface.

### Economics interpretation

The highest-value candidates are native **primitives** that add control or information without independently purchasing additional model cognition. Read-only usage/model/thread metadata and interruption are especially cheap. Steering may save tokens when it redirects an already-running turn instead of requiring cancellation plus replacement work. Image input can reduce textual transcription but still participates in model context. Native review and approval/elicitation paths may be valuable, but they require Room-semantic and authority analysis before use because they can introduce additional cognition or human-interaction state.

Native orchestration remains categorically different. Built-in subagents, autonomous fan-out, and provider-controlled delegation can add model executions/context duplication outside Room's explicit economics and provenance controls. They remain disabled.

**Assessment:** I-022 Stage A is **COMPLETE / VERIFIED** as an exact-source contract audit. The evidence establishes a larger immediately available native primitive surface than the older Desktop↔Room audit captured. It does not authorize implementation or select a preferred feature. Stage B should compare the candidate families neutrally by principal value, Room-semantic fit, implementation/authority cost, overlap, and expected model-token impact. Feature-specific runtime probes or implementation follow only when a material comparison fact cannot otherwise be established or after explicit principal selection.

## E-160 — I-022 Stage B native-capability / execution-economics comparison

**Date:** 2026-09-20
**Kind:** [exact-source comparative audit / execution-economics classification]
**Related work:** I-022 Stage B
**Runtime behavior changed:** none
**Evidence state:** VERIFIED for the compared exact-source/current-Room facts; NEEDS VERIFICATION for any future feature-specific runtime exposure

Stage B compared the exact Codex 0.154 source/SDK surface from E-159 with current Codex Room source and settled Room semantics. It did not run model-heavy empirical probes and did not select an implementation feature.

| Capability family | Exact 0.154 substrate | Current Codex Room state | Inherent model-cognition cost | Room semantic / integration consequence |
|---|---|---|---|---|
| Workspace files and command execution | Normal Codex thread/runtime capability | Already inherited and used; Status & Tools reports both classes | Tool continuations can trigger large context replay even though the command itself is deterministic | Existing I-014 batching and deterministic-capability policy already address the main economics risk |
| Web search / MCP / apps / skills / plugins | Native/config-dependent runtime capabilities; Room already inspects inventory for these families | Web/skills/MCP/apps/plugins inventory is surfaced; I-020 completed native skill integration; I-021 separately tracks plugin mutation | Depends on use; repeated tool loops can be expensive | Preserve native substrate; do not create parallel catalogs or tool systems |
| Account rate limits / usage | `account/rateLimits/read`, `account/usage/read`; typed responses include multi-bucket limits, ordinary-usage permission, credits/spend-control state, account/daily/thread usage | Not currently surfaced as a principal Room feature | None for the read itself | Read-only adapter is mechanically small, but any pacing/policy feature such as D-019 remains a separate decision requiring semantics from actual supported payloads |
| Model discovery | `model/list`; Python SDK direct wrapper | D-039 currently governs an admitted model/configuration set; raw discovery is not a principal picker | None for discovery | Native discovery could reduce stale model metadata, but raw provider selection must not bypass D-039 or prohibited-model policy |
| Provider thread list/read/archive/unarchive/name/compact/fork | Native App Server / Python SDK thread lifecycle controls | Room already owns durable provider-context identity, Assignment lineage, archival/retirement and REFRESH semantics | None for metadata/lifecycle calls; fork/continuation may lead to later cognition | Raw provider-thread controls overlap Room authority. Use, if any, should support maintenance/context machinery rather than create a second human-visible work model |
| Active-turn steering | `turn/steer`; exact active-turn id precondition; SDK direct wrapper | No principal-facing Room steering path | No separate turn is inherently required, but the existing model turn continues with added input/context | Potentially avoids cancel-and-restart waste, but requires exact binding to active Assignment/turn, durable provenance, and rules for how steering affects the transaction decision contract |
| Active-turn interruption | `turn/interrupt`; SDK direct wrapper; Room already invokes interruption internally through active turn handles | Room Stop/lifecycle uses interruption internally; no granular principal-facing per-assignment interrupt | Stops ongoing spend; partial turn work may be lost | Not merely a UI button: ordinary interrupted transaction turns are terminal except narrow recovery rules, so principal interruption needs deliberate settlement/retry/cancel semantics |
| Structured principal input: images/audio/path mentions | `UserInput` includes Image, LocalImage, Audio, LocalAudio, Skill and Mention(path) in addition to Text | Observer messages are currently text-only; agents can already read files placed in shared workspace | No separate model invocation, but image/audio/context processing consumes model context | Image/local-path delivery can reuse native input; generic upload/import UX, file staging, provenance and safe path handling remain Room host work |
| Native code review | `review/start` over uncommitted changes, base branch, commit or custom instructions; inline review starts a Turn; detached delivery exists but is deprecated | Room currently obtains independent review through task-specific peer Assignments when warranted | Yes: review is model cognition/a model turn | Strong overlap with peer verification. Native review may be a useful bounded primitive, but it is neither free nor automatically independent and must not silently become a fourth reviewer/organization |
| Command/file/permission approvals and tool user input | App Server server requests for command approval, file-change approval, additional permissions and tool user input; permission-profile enumeration exists | Room lacks a generic principal interaction bridge; C-only durable CONSULT_PRINCIPAL exists for organizational consultation | Approval/input handling itself need not buy a separate model turn; it resumes/unblocks current cognition | High authority value and high security/interaction burden. A principal-proof boundary is necessary because E-158 proved agent-equivalent workspace-write execution can reach Room localhost |
| Managed worktrees | Exact 0.154 `codex-worktree` manager plus CLI `--worktree`; feature is Experimental and disabled by default | No Room managed-worktree integration; Room intentionally uses a shared workspace for A/B/C collaboration | No model cognition inherent in worktree creation | Useful isolation primitive for selected coding workflows, but indiscriminate per-agent worktrees would fragment shared state and add merge/provenance/cleanup machinery |
| Browser Use / Computer Use | Exact 0.154 feature registry marks Browser Use, full-CDP Browser Use, external Browser Use, and Computer Use Stable/default-enabled; config/requirements types govern origins/apps | Current Room host has no verified visual browser/computer-use execution surface | Usually model + iterative UI/tool interaction; continuation amplification can be substantial | App Server/config presence does not prove Room execution availability. This is a host/security/runtime integration question and needs exact runtime proof only if selected |
| Remote execution environments | Experimental `environment/add`, `environment/info`, `environment/status` contracts point to an exec-server URL and runtime workspace roots | No Room remote-environment integration | Environment control itself is non-cognitive; work run there still incurs normal cognition/tool cost | Potential execution-substrate primitive, but not evidence of full Desktop cloud-task parity; workspace authority, provenance, failure/recovery and secrets/network boundaries would need design |
| Remote control / pairing | Exact 0.154 protocol, transport and processor code includes enable/disable/status, pairing, client list/revoke; the compatibility `remote_control` feature flag is marked Removed | No Room integration | Transport/control is not inherently cognitive | Substantial authentication/pairing/security surface, and exact product availability is ambiguous enough that no Room adoption should be inferred from protocol code alone |
| Desktop local automation / scheduled tasks | 0.154 feature registry marks in-app local automation Stable/default-enabled, but no ordinary automation/schedule App Server request was found in the audited protocol request surface | Room has no scheduler/local-automation host | Each scheduled execution would incur whatever cognition/tools its task requires | Primarily a Desktop host capability rather than a ready Room primitive; adopting scheduling would require a host scheduler and durable authority/lifecycle semantics |
| Dictation / in-app browser panes / integrated terminal / Git/editor surfaces | Desktop host/UI features; some have stable feature flags but are not equivalent to agent App Server methods | Not provided by Room observer host as equivalent UI | UI itself is non-cognitive | These are host-experience gaps, not evidence that agent filesystem/command/Git capabilities are missing |
| Built-in subagents / collaboration orchestration | Codex contains native multi-agent/collaboration machinery | Explicitly disabled by Room config; A/B/C transactions are authoritative | Can multiply model executions/context fan-out | Deliberately superseded under current architecture; native orchestration should remain disabled absent new evidence that it can preserve Room semantics and economics |

### Cross-cutting conclusions

1. **Native primitive availability and Room product exposure are separate facts.** 0.154 contains many useful operations that Room does not expose, while several Desktop features remain host capabilities rather than ordinary App Server methods.
2. **Read-only/control primitives are not automatically feature priorities.** Their low cognition cost makes them economically attractive to expose if the principal wants them, but Stage B does not select them.
3. **Steering and interruption are economically interesting but transaction-sensitive.** They can change or stop ongoing spend without purchasing an entirely new turn, yet Codex Room's durable Assignment/turn/result semantics mean a raw SDK button would be insufficient.
4. **Native review is cognition, not a free deterministic primitive.** Its main question is semantic/economic fit relative to task-specific peer verification, not API availability.
5. **Interaction/approval capabilities are limited primarily by principal authority, not by missing Codex protocol.** E-158 prevents localhost itself from serving as the trust boundary.
6. **Worktrees and remote environments are environment primitives, not organizational primitives.** They may be valuable selectively but should not redefine A/B/C or shared-workspace collaboration by default.
7. **Browser/computer-use parity remains materially larger.** Exact 0.154 has stable feature/configuration support, but Room availability is not established and the iterative tool-loop economics deserve explicit attention if selected.
8. **Desktop host conveniences should not be rebuilt merely for visual parity.** The audit should ask whether the underlying capability is missing for useful work, not whether Room reproduces every Desktop screen.
9. **Native subagent orchestration remains excluded.** The Room's differentiated value is explicit, inspectable, assignment-scoped cognition with controlled context and invocation economics.

**Assessment:** I-022 Stage B is **COMPLETE / VERIFIED** as a comparative audit. No feature, runtime probe, or implementation slice is selected by this evidence. The next action is principal review/selection or closure of I-022 if no capability warrants further work now.

## E-161 — 2026-09-20 roadmap/development truth audit and Development Control consolidation

**Date:** 2026-09-20
**Kind:** [repository/document truth audit / roadmap maintenance]
**Related work:** project-wide roadmap/development control
**Runtime behavior changed:** none
**Evidence state:** VERIFIED for repository/document state inspected in this audit

The audit began from canonical `main` at `bb1d057e698909c2212663181b73cdc72f67bcee` and cross-checked Development Control against Architecture & Current State, the Decision Register, both Evidence Register volumes, Product Vision, Repository & Operations, the identifier index, current GitHub PR state, branch state, and recent canonical work.

### Findings

1. **The implementation/vision baseline was broadly coherent.** Product Vision already reflected neutral A/B peer identities, D-019 remained explicitly deferred, and the Decision Register correctly marked D-003 and D-040 superseded while retaining later active decisions. No new governing decision was required.

2. **Development Control had regrown into a historical archive.** Before cleanup it was approximately 77.7 KB / 803 lines and carried detailed completed narratives for I-018/I-019/I-020, BCTX, Common Cause experiments, acceptance campaigns, and older completed programs. This conflicted with the package guide's ownership rule that Development Control should carry volatile current focus/status while durable implementation/evidence history lives elsewhere.

3. **The older post-I-018 ordered roadmap was stale.** It still described a principal-approved sequence with inherited-tool exercises and rich attachments as ordered follow-ons. I-022 / E-159 / E-160 subsequently established a neutral capability/economics comparison and an explicit feature-selection boundary. The old sequence could incorrectly imply that completion of one item automatically advances to the next.

4. **I-019 contained stale closeout wording.** The current file simultaneously marked the D-041 catalog cleanup COMPLETE / VERIFIED and retained an older sentence saying the cleanup still required fresh exact-byte verification. E-152 had already supplied that verification. The same area also called skills evaluation back-burnered even though I-020 later completed and D-042 settled the native-skill hierarchy.

5. **I-021 remains an open development topic but has no selected Stage-B path.** Stage A plugin-contract/authority evidence remains verified (E-157/E-158). The principal had selected plugin administration before I-022, so the audit does not revoke that choice. However, no state-changing mutation bridge is currently selected as the automatic next implementation; Stage B must first resolve native/Desktop-managed administration versus a Room-side principal mutation surface.

6. **I-022 itself had reached a natural closeout.** Stage A exact-source audit and Stage B comparative matrix are complete. No implementation was authorized. The current roadmap should therefore present principal selection or ordinary use as the next boundary rather than invent a default feature.

7. **Common Cause competitive play was misclassified as planned development.** The game artifact is verified play-ready, but competitive play depends on separate principal authorization and is ordinary product use, not current development work.

8. **The identifier index had stale ownership pointers.** P0-P3, EF-1-EF-3, A1/A2, and several closed I-items still pointed to Development Control even though their durable records now live in the Decision/Evidence registers and Repository & Operations.

9. **Repository PR hygiene had two false active signals.** PR #91 was an older I-015 Stage B2 attempt superseded by merged PR #92 and Stage B3 PR #93. PR #121 was an older BCTX-3 attempt superseded by merged PR #122, followed by PR #123 closeout and PR #124 BCTX-4. Both were commented with their supersession and closed during the audit.

10. **Remote branch residue remains but is not roadmap authority.** Non-`main` branches include old unmerged/superseded attempts such as `a-b-peer-role-normalization`, `bctx-3-grace-history`, `docs-i015-stage-a-verification`, `i015-stage-b2-structured-evidence`, and `i019-status-tools-v2`. Their existence does not mean the work is active. GitHub's connected mutation surface used here does not provide a delete-ref action, so this audit does not rewrite or move those refs merely for cosmetic cleanup.

### Maintenance changes

- Development Control was consolidated to approximately 11.8 KB / 181 lines, retaining only current/deferred/monitor state, compact recent-completion pointers, the QoL wishlist, and open questions.
- I-022 is now COMPLETE / audit-only / no implementation authorized.
- I-021 remains IN PROGRESS at the topic level with Stage A complete; its Stage-B administration path remains unselected pending re-evaluation of native Desktop-managed plugin administration versus a Room mutation bridge.
- The stale ordered post-I-018 roadmap and duplicated historical narratives were removed from volatile work control.
- Common Cause competitive play is explicitly identified as non-development pending principal activity.
- Historical identifier pointers were repaired to their actual durable owners.
- Architecture & Current State and Repository & Operations synthesis dates were refreshed to 2026-09-20; Architecture now records E-160's no-runtime-change/no-selection boundary.

**Assessment:** after these changes, no active implementation feature is selected by default. Ordinary Codex Room use is unblocked. The next development item should arise from explicit principal selection or demonstrated ordinary-use evidence, not from stale roadmap sequence or leftover PR/branch state.

## E-162 — I-021 Stage B native-host plugin administration boundary
**Date:** 2026-09-20
**Kind:** [exact-source/product-surface audit / product-boundary decision evidence]
**Related work:** I-021 Stage B
**Runtime/plugin state changed:** none
**Evidence state:** VERIFIED for the inspected Codex 0.154 source, current Room source, and current official product guidance; no Room mutation implementation performed

Stage B re-evaluated whether Codex Room should implement its originally planned principal-only plugin mutation bridge or rely on native plugin administration while Room inherits the resulting capability state.

### Exact Codex 0.154 host surface

Exact upstream source at tag `rust-v0.154.0` contains a TUI `/plugins` surface that:

- loads native plugin marketplaces and plugin details;
- offers **Install plugin** for installable native plugin identities;
- offers **Uninstall plugin** for removable installed plugins;
- exposes an installed-plugin toggle whose action is explicitly described as enable/disable;
- blocks toggling for administrator-installed or administrator-disabled plugins as appropriate;
- drives the native App Server plugin/configuration operations rather than a separate TUI-side registry;
- after installation, reports any included apps that still require authentication and provides a native handoff to the applicable ChatGPT app-management page instead of collecting provider credentials itself.

This complements E-157, which already verified the exact 0.154 App Server routes, install semantics, cache/runtime refresh behavior, and native configuration-write path for plugin enablement.

### Current official product surface

Current OpenAI plugin guidance on 2026-09-20 states that eligible users can go to **Plugins in ChatGPT or Codex**, review a plugin, select **Install plugin**, and complete any required app connection/authorization through the product's native flows. Workspace plugin policy and disable controls remain native administrative functions. Availability can vary by plan, role, workspace, region, and product surface.

This establishes that principal-controlled plugin administration is already a supported product responsibility of the native host rather than a capability unique to Codex Room.

### Current Codex Room boundary

Current canonical Room source was inspected at the 2026-09-20 `main` baseline:

- `codex_room/agent.py` applies explicit session overrides for model/reasoning defaults and disables Codex built-in agent/multi-agent features; it does not override ordinary plugin configuration;
- the same adapter's native inventory inspection calls `plugin/installed`, `skills/list`, `mcpServerStatus/list`, and `app/installed` against the active App Server;
- `codex_room/status_tools.py` surfaces installed plugin enabled/availability/auth-policy state together with contributed skill/MCP/app inventory;
- therefore Room visibility already follows the authoritative native configuration rather than maintaining a competing plugin registry.

E-158 remains decisive for the alternative design: an A/B/C-equivalent Windows workspace sandbox successfully reached the Room localhost API. Building Room-side plugin mutation would therefore require a separate principal-proof mechanism; localhost binding or HTTP method choice cannot supply that boundary.

### Stage B disposition

The principal selected the native-host path after reviewing this tradeoff.

The native path satisfies the current underlying need with lower complexity and stronger authority placement: plugin state is changed through the product surface that already owns plugin policy, marketplace state, and app authorization, while Codex Room inherits and reports the resulting capabilities. The only sacrificed property is single-surface convenience for an infrequent administrative action.

No runtime probe or real plugin mutation was necessary for this decision because the relevant capability and authority facts were already mechanically available from exact 0.154 source, E-157/E-158, current Room source, and current official product guidance.

**Assessment:** I-021 is **COMPLETE**. No Room-side plugin mutation bridge, generic configuration editor, copied marketplace UI, credential/auth proxy, or principal-proof security subsystem is currently warranted. D-043 records the settled boundary. Reopen only on concrete ordinary-use evidence that native-host administration creates a material capability, reliability, or workflow-cost problem.

---

### E-163 — PBM v1 exact-head verification and canonical merge equivalence
**Date:** 2026-09-20  
**Kind:** [deterministic exact-head verification / benchmark-harness verification / Git provenance]  
**Related work:** I-023 / D-045  
**Runtime/model benchmark traffic changed:** none  
**Evidence state:** VERIFIED for the PBM v1 implementation bytes; no live PBM performance result is claimed

PBM v1 was verified on exact feature head:

`7b7cbfdfcea8617f8885676df2a257ce299e4657`

The principal ran the complete interactive-PowerShell verification block against a clean detached checkout of that exact SHA.

Observed results:

- pre-verification working tree: clean;
- fetched feature ref resolved exactly to the expected SHA;
- detached checkout HEAD matched the expected SHA;
- `git diff --check origin/main...HEAD`: exit 0;
- `pbm-desktop.ps1` PowerShell parser: no errors;
- `pbm-room.ps1` PowerShell parser: no errors;
- focused PBM + usage tests: **11 passed**;
- `verify-fast.cmd`: **PASS**;
- Linux Python 3.12 focused core: **63 passed**;
- Windows focused portability tests: **118 passed**;
- browser transcript stability: **9 passed**;
- final HEAD remained the expected SHA;
- final tracked working tree remained clean.

The verification output included only the pre-existing dependency/deprecation warnings from FastAPI/Starlette test dependencies; no PBM-specific failure or warning was observed.

PR #176 was then merged without modifying the verified feature head, using expected-head protection. Canonical merge commit:

`c0fe5f6600fb12f039b7e3d4bd26e67a64795a23`

Git object verification after merge established:

- tested feature-head tree SHA: `aecd10f535785c27dc690719b650beb29aaed111`;
- canonical merge-commit tree SHA: `aecd10f535785c27dc690719b650beb29aaed111`;
- the canonical merge commit directly lists the tested feature head as one of its parents.

Therefore the canonical merged PBM v1 bytes are exactly the bytes that passed the local verification gate.

PBM v1 now includes:

- canonical version pointer at `benchmarks/pbm/CURRENT`;
- frozen v1 manifest/protocol;
- eight synthetic standard-library-only paired task fixtures/prompts;
- deterministic task graders;
- dedicated native Desktop preparation/capture script;
- dedicated Room preparation/run/capture script;
- shared deterministic PBM manifest/fixture/grading/accounting/report machinery;
- focused automated harness tests;
- the canonical Project-runtime rule that **“Run PBM”** resolves the current PBM version and executes its defined procedure rather than redesigning the benchmark.

**Assessment:** I-023 PBM v1 is **IMPLEMENTED / EXACT-HEAD VERIFIED** and may be used for its first live benchmark run. This evidence does **not** claim that a Desktop-vs-Room PBM run has yet occurred, that the live integration path has been behaviorally exercised end-to-end, or that either product has any measured performance advantage.

---

### E-164 — PBM v2 contextual baseline exact-head verification and non-cognitive native preflight
**Date:** 2026-09-20  
**Kind:** [deterministic exact-head verification / read-only native runtime preflight / benchmark protocol verification / Git provenance]  
**Related work:** I-024 / D-046 / D-039  
**Runtime/model benchmark traffic changed:** none  
**Evidence state:** VERIFIED for PBM v2 implementation bytes and read-only context-snapshot behavior; no live paid PBM result is claimed

PBM v2 was verified on exact feature head:

`b69cf713657d7ad3f742f657f70002a61ea4eecd`

The principal ran the exact-head verification against a clean detached checkout. Deterministic verification observed:

- exact HEAD matched the expected feature SHA;
- tracked working tree was clean;
- `git diff --check origin/main...HEAD`: PASS;
- `pbm-desktop.ps1` PowerShell parser: no errors;
- `pbm-room.ps1` PowerShell parser: no errors;
- focused PBM + usage tests: **16 passed**;
- `verify-fast.cmd`: **PASS**;
- Linux Python 3.12 focused core: **63 passed**;
- Windows focused portability tests: **118 passed**;
- browser transcript stability: **9 passed**;
- only the already-known FastAPI/Starlette dependency deprecation warnings appeared.

A first verification-block attempt stopped before context collection because the helper parameter name `$Home` collided case-insensitively with PowerShell's read-only `$HOME` variable. This was a verification-script defect, not a PBM implementation failure. The principal then reran only the corrected read-only preflight and final exact-head/tree checks; the already-passed deterministic suite was not needlessly repeated.

The corrected PBM v2 context preflight observed:

- PBM version: `v2`;
- `openai-codex` package version: `0.154.0`;
- native runtime version: `0.154.0`;
- Room runtime version: `0.154.0`;
- native `account/rateLimits/read`: **available**;
- native `account/usage/read`: **available**;
- native effective config read: **available**;
- Room-effective config read: **available**;
- no new or modified Codex rollout JSONL appeared during snapshot collection;
- no PBM task execution directory/state was created;
- persisted snapshot passed the sensitive-key scan;
- final HEAD still matched the exact verified feature SHA;
- final tracked working tree remained clean.

The preflight also demonstrated that the contextual data is materially useful. At the snapshot taken on 2026-09-20, the native Codex response reported:

- ordinary usage allowed: true;
- plan type: Plus;
- primary 300-minute window: **0% used**;
- secondary 10,080-minute window: **9% used**;
- purchased-credit balance: **0** / no credits;
- daily account usage and lifetime-token summary were readable through the native account-usage surface.

Those values are evidence about that exact snapshot only; PBM v2 records corresponding start/end and per-task-pair snapshots so later performance results can be interpreted against changing provider/account state.

PBM v2 also preserves naturalistic Room cognition under D-039. The benchmark records the Room defaults and actual execution model/reasoning provenance, but does not pin C/A/B to one model/effort configuration. Ordinary C-controlled dynamic allocation among admitted Luna/Terra/Sol × Low/Medium/High configurations remains part of the Room behavior being measured.

PR #178 was merged with expected-head protection. Canonical merge commit:

`33b0dd7af38c2d84e3cbf2babedc4ac78410d5ce`

Git object verification after merge established:

- tested feature-head tree SHA: `ec90a8344f3dc451b2817c422f0816ce6086520a`;
- canonical merge-commit tree SHA: `ec90a8344f3dc451b2817c422f0816ce6086520a`;
- the canonical merge commit directly lists the tested feature head as one of its parents.

Therefore the canonical merged PBM v2 implementation bytes are exactly the bytes that passed the deterministic verification and read-only context preflight.

**Assessment:** I-024 is **COMPLETE / IMPLEMENTED / EXACT-HEAD VERIFIED / READ-ONLY PREFLIGHT VERIFIED**. `benchmarks/pbm/CURRENT` now selects PBM v2 for the unqualified **“Run PBM”** invocation. PBM v1 remains frozen and explicitly reproducible. No live paid Desktop-versus-Room PBM task has yet been run and no product-performance conclusion is claimed by this evidence.

---

### E-165 — PBM v3 one-paste exact-head verification, controller preflights, launcher repair, and canonical merge equivalence
**Date:** 2026-09-20  
**Kind:** [deterministic exact-head verification / native Desktop controller preflight / Room controller preflight / defect repair / Git provenance]  
**Related work:** I-025 / D-047 / D-039  
**Runtime/model benchmark traffic changed:** controller-only cognition was used for bounded preflights; **zero PBM benchmark tasks were executed**  
**Evidence state:** VERIFIED for PBM v3 implementation bytes and both controller mechanics; no live paid PBM performance result is claimed

PBM v3 preserves the frozen PBM v1 eight-task workload, PBM v2 contextual snapshot/accounting semantics, alternating arm order, and D-039 naturalistic Room cognition while changing the operator workflow to one initial principal instruction per platform.

The first final-candidate controller-preflight head before the launcher repair was:

`19dc9b2427ed82cc5092cc36fb18aee7b36bbf64`

At that head, the native Codex Desktop controller preflight passed. It demonstrated that a coordination-only Desktop controller could use native fresh-task management to create one harmless child task, wait for that exact task, obtain its exact thread id, and complete without Codex CLI fallback, benchmark fixtures, graders, results, or benchmark task execution.

The first Room-controller preflight exposed one implementation defect while also confirming the intended private-controller handshake:

- controller Room creation and file staging occurred before Round start;
- C entered the private `CONSULT_PRINCIPAL` wait;
- the principal's exact private reply was recorded and resumed C;
- C read the staged driver and invoked `PBM_ROOM_CLIENT.ps1`;
- the launcher recorded a detached child PID, but that process exited immediately;
- no worker log or completion marker appeared;
- the failure was isolated to PowerShell `Start-Process -ArgumentList` handling of the worker script path under `C:\Codex Room\...`, where the unquoted path could be split at the space.

The repair changed the launcher to pass an explicitly quoted worker-script argument and added a regression assertion for that construction. Comparing the Desktop-preflight head to the repaired head shows only two changed files:

- `codex_room/pbm_onepaste_room.py`;
- `tests/test_pbm_onepaste.py`.

Therefore the previously passed Desktop-controller implementation bytes were unchanged by the Room-launch repair.

The repaired exact feature head was:

`e655f36141fba9a77b69cc04147a5bd13b728135`

The principal verified that exact head from a clean tracked checkout. Observed deterministic results:

- focused PBM v3 tests: **8 passed**;
- `verify-fast.cmd`: **PASS**;
- Linux Python 3.12 focused core: **63 passed**;
- Windows focused portability tests: **118 passed**;
- browser transcript stability: **9 passed**;
- only the already-known FastAPI/Starlette dependency deprecation warnings appeared.

The bounded repaired Room-controller preflight then passed all intended mechanics:

- exact repaired HEAD: PASS;
- controller Room creation: PASS;
- files staged before Round start: PASS;
- Round start: PASS;
- private `CONSULT_PRINCIPAL` wait: PASS;
- exact private principal reply: PASS;
- repaired PBM v3 launcher execution: PASS;
- detached deterministic worker: PASS;
- worker PID continuity between launcher record and worker marker: PASS;
- completion marker: PASS;
- Agent A/B activity: NONE;
- Agent A/B assignments: NONE;
- PBM benchmark tasks executed: **0**;
- preflight Room archived: PASS.

PR #180 was merged with expected-head protection. Canonical merge commit:

`556e92946d1d6c9f2b10e15b1d303cad0cd05b63`

Git comparison from the exact tested feature head to the canonical merge commit established:

- merge-base is the tested feature head;
- canonical merge is exactly one commit ahead;
- there are **zero file differences** between the tested head and canonical merge commit.

Thus the canonical merged PBM v3 implementation bytes are the exact bytes that passed the repaired deterministic verification and Room-controller preflight. `benchmarks/pbm/CURRENT` now selects v3 for the unqualified **“Run PBM”** invocation. PBM v1 and v2 remain frozen and explicitly reproducible.

**Assessment:** I-025 is **COMPLETE / IMPLEMENTED / EXACT-HEAD VERIFIED / CONTROLLER-PREFLIGHT VERIFIED**. PBM v3 is ready for its first live Desktop-versus-Room benchmark run. No such benchmark run has yet occurred, and this evidence makes no claim about relative product performance.

---

### E-166 — PBM v3 first-live initialization failure and Desktop controller import-path repair
**Date:** 2026-09-20  
**Kind:** [first-live workflow evidence / fail-closed launch defect / deterministic repair / exact-head verification / Git provenance]  
**Related work:** I-025 / D-047  
**Runtime/model benchmark traffic changed:** one Desktop controller conversation was opened for the requested live PBM invocation; **PBM initialization failed before any benchmark task executed**  
**Evidence state:** VERIFIED for the launch-path defect and repair; no Desktop-versus-Room performance result is claimed

The principal invoked the canonical **“Run PBM”** workflow after E-165 closeout. A fresh Codex Desktop controller task was opened at:

`C:\Codex Room\pbm_desktop_controller`

and received the single prescribed instruction:

`Read DRIVER.md and execute it exactly.`

The controller failed closed before PBM initialization and reported that `codex_room.pbm_onepaste` was not installed/importable through `C:\Codex Room\.venv`. No benchmark task was started.

Repository inspection established the cause. `codex-room` is a normal repo-local package defined by `pyproject.toml`. The PBM Desktop controller deliberately runs from the isolated `pbm_desktop_controller` working directory, but the original driver directly invoked:

`C:\Codex Room\.venv\Scripts\python.exe -m codex_room.pbm_onepaste ...`

without either installing the local project into that venv for ordinary runtime use, changing the command working directory to the repository root, or supplying the repository root on `PYTHONPATH`. The repository verifier succeeds under its own controlled environment because it either installs the project into its verification environment or sets `PYTHONPATH` to the repository root. Thus the controller preflight had proven native task-management mechanics but had not behaviorally exercised this exact live initialization command from the controller subdirectory.

PR #181 repairs the launch path without weakening Desktop child isolation:

- adds tracked `pbm_desktop_controller/PBM.ps1`;
- the wrapper resolves the repository root from `$PSScriptRoot`;
- it resolves the existing repository `.venv\Scripts\python.exe`;
- it temporarily `Push-Location`s to the repository root only for the deterministic PBM Python invocation;
- it captures `$LASTEXITCODE` immediately after that native command;
- it always `Pop-Location`s in `finally`;
- it throws on nonzero PBM exit rather than terminating the principal/controller shell;
- `DRIVER.md` routes all five PBM deterministic commands through the wrapper;
- the v3 manifest fingerprints `PBM.ps1`, so this orchestration change cannot silently reuse the prior v3 fingerprint;
- focused tests assert the wrapper/driver contract.

Exact repair head:

`e1a047dbe483598a8b800f5293d614fba9cb208b`

The principal verified that exact head from a clean tracked checkout. Observed results:

- PowerShell wrapper parse: PASS;
- controller-directory `PBM.ps1 --help` smoke test: PASS;
- the smoke test displayed the expected `pbm-onepaste` CLI and `desktop-next` command;
- caller working directory preservation: PASS;
- PBM benchmark tasks executed by the smoke test: **0**;
- focused PBM v3 tests: **9 passed**;
- `verify-fast.cmd`: **PASS**;
- Linux Python 3.12 focused core: **63 passed**;
- Windows focused portability tests: **118 passed**;
- browser transcript stability: **9 passed**;
- final HEAD remained the exact expected repair SHA;
- final tracked tree remained clean.

An initial smoke-verification script incorrectly searched the valid argparse output for `pbm_onepaste` with an underscore rather than the actual program name `pbm-onepaste` with a hyphen. That script therefore reported a false FAIL after the module had already imported and printed valid CLI help. The corrected continuation check passed and then ran the focused and routine verification suites. This was a verification-script defect, not an implementation failure.

PR #181 was merged with expected-head protection. Canonical merge commit:

`133ac4d0a2192189756fa8e12acd912b2ffbaca1`

Git comparison from the exact tested feature head to the canonical merge commit established:

- merge-base is the tested feature head;
- canonical merge is exactly one commit ahead;
- there are **zero file differences** between the tested head and canonical merge commit.

**Assessment:** the first live PBM attempt produced useful workflow evidence but **no benchmark result**. PBM v3 remains the canonical workflow, now with the Desktop controller import path repaired and exact-head verified. The correct next action is a fresh live PBM invocation from a new Desktop controller conversation so controller-context measurement starts cleanly.

---

### E-167 — PBM v3 first substantial live run aborted after protocol and benchmark-integrity failures
**Date:** 2026-09-20  
**Kind:** [live benchmark postmortem / orchestration failure / validity failure / workload defect / principal abort]  
**Related work:** I-025 / I-026 / D-047 / D-048  
**Run:** `pbm-v3-20260920T234823Z`  
**Evidence state:** VERIFIED for the observed failure modes; **NO VALID DESKTOP-VERSUS-ROOM PERFORMANCE RESULT**

The first substantial live PBM v3 run initialized successfully after the E-166 import-path repair. The coordinator, controller Room, detached Room worker, native Desktop child-task creation, benchmark fingerprinting, and early task execution all operated far enough to exercise the real end-to-end workflow.

The run then exposed three independent defects.

**1. Desktop controller liveness violated the one-paste protocol.**

After a Desktop arm completed, the v3 Desktop controller used blocking `desktop-next --wait` calls while the alternating schedule belonged to Room. In live native Codex Desktop execution, those waits repeatedly returned at the tool/turn boundary after roughly thirty seconds without a new Desktop action. After several empty waits the controller turn ended. The principal had to send repeated continuation instructions to resume the same controller. The state machine generally avoided repeating completed task arms, but the promised one-instruction Desktop protocol was not preserved.

This was an architectural mismatch: a model conversation was being used as though it were a durable event-loop process capable of sleeping across arbitrarily long asynchronous work on another platform.

**2. Room terminal/validity semantics could advance after human-aborted work.**

The v3 Room helper classified `finished`, `error`, `stopped`, and `paused` as terminal statuses for capture. Room-result validity was primarily tied to usage completeness rather than clean autonomous benchmark completion. During t07 the principal deliberately stopped the measured Room rather than supply privileged substantive guidance. The detached worker subsequently advanced and created the t08 Room.

Thus existence of a captured result was not sufficient evidence that a Room arm completed autonomously under benchmark protocol. Observer stop, pause, error, principal consultation, and other abnormal endpoints require explicit validity semantics in the successor benchmark.

**3. Frozen t07 is internally inconsistent and its grader does not cover that inconsistency.**

The t07 escaped-field codec specification requires empty fields to be preserved and explicitly requires `decode("") == [""]`, while also requiring encoding/decoding to recover the original list. There is no wire-format representation that can distinguish `[]` from `[""]` under those constraints. Agent C correctly identified the contradiction and entered a substantive `CONSULT_PRINCIPAL` wait.

The external t07 grader does not test the empty-list case and can award full credit to an implementation that cannot satisfy the complete written contract. Therefore t07 is not a sound comparative benchmark task as frozen in v1-v3.

The principal aborted the live run. The Room worker and PBM coordinator were stopped, the active run pointer was removed, and run evidence was preserved where available. No completed PBM comparison report is accepted from this run.

Postmortem review also identified an evidence-discipline issue: earlier exact-head and controller-preflight verification correctly established the components it exercised, but those tests did not behaviorally validate the complete native one-paste protocol across real cross-platform delays. The readiness inference was therefore too broad.

**Assessment:** PBM v3 is **HISTORICALLY IMPLEMENTED / LIVE-END-TO-END FAILED / NOT APPROVED FOR ANOTHER PERFORMANCE RUN**. D-048 supersedes its operating architecture for future benchmark work. The successor must use two independent complementary one-paste harnesses, explicit VALID/INVALID/FAILED semantics, audited mission/grader consistency, first-class status/abort/evidence-bundle operations, and a real delayed end-to-end canary before paid full execution.

---

### E-168 — PBM v4 exact-head deterministic implementation verification
**Date:** 2026-09-20  
**Kind:** [benchmark implementation / exact-head verification / mission-grader audit / repository verification / Git provenance]  
**Related work:** I-026 / D-048  
**Runtime/model benchmark traffic changed:** **NONE**; this verification did not execute a Desktop or Room benchmark cognition session  
**Evidence state:** VERIFIED for deterministic implementation and merge provenance; live one-paste canaries remain pending

PBM v4 was implemented on feature branch `i026-pbm-v4-implementation` as the D-048 replacement for v3's live alternating cross-platform controller. The implementation provides:

- one frozen integrated mission shared by Desktop and Room;
- one exact principal paste per platform;
- no live Desktop↔Room coordination, alternating wait loop, controller Room, or persistent benchmark controller model turn;
- equivalent prepared starting fixtures and one external deterministic grader;
- explicit **VALID / INVALID / FAILED** classification separate from quality score;
- exact Desktop user-message verification from rollout evidence;
- fail-closed Room checks for observer intervention, substantive `CONSULT_PRINCIPAL`, clean settlement, usage completeness, and completion marker;
- deterministic `status`, `abort`, evidence `bundle`, and post-run `compare` operations;
- a hidden reference solution used only for preflight satisfiability and grader-coverage audit;
- an explicit resolution of the prior empty-list codec contradiction;
- `benchmarks/pbm/CURRENT` deliberately left at v3 pending promotion gates.

The principal verified exact feature head:

`3074984340777ed906edf643c8deb2358c701827`

from a clean tracked checkout. Observed deterministic verification results:

- exact expected feature HEAD: PASS;
- Python syntax compilation for the v4 harness, grader, and reference implementation: PASS;
- mission/grader satisfiability audit: PASS;
- v4 benchmark fingerprint: `fc505df8c0578308f594e20c27d5a5e0ce68fa078a7c7c5935abc211550bec93`;
- hidden reference solution score: **100**;
- grader coverage requirements present and matched:
  - `public_tests`
  - `codec_contract`
  - `inventory_atomicity`
  - `summary_contract`
  - `payload_integration`
  - `cli_stdout`
  - `cli_output_file`
  - `cli_error_atomicity`
  - `storage_decision`
  - `completion_artifacts`;
- focused PBM v4 tests: **7 passed**;
- `verify-fast.cmd`: **PASS**;
- Linux Python 3.12 focused core: **63 passed**;
- Windows focused portability tests: **118 passed**;
- browser transcript stability: **9 passed**;
- `benchmarks/pbm/CURRENT`: still **v3**;
- final HEAD remained exact;
- final working tree remained clean.

The first focused run exposed one documentation-test wording mismatch: the README said “Open a fresh top-level native Codex Desktop task” while the test asserted the exact substring “one fresh top-level native Codex Desktop task.” No benchmark implementation or asset defect was involved. The repair changed exactly one assertion line in `tests/test_pbm_v4.py`; the continuation verification then passed all checks above.

PR #183 was merged with expected-head protection. Canonical merge commit:

`a1144f27cc2fe196ed0ecd2935a30c76989a3f35`

Git comparison from the exact tested feature head to the canonical merge commit established:

- merge-base is the tested feature head;
- canonical merge is exactly one commit ahead;
- there are **zero file differences** between the tested feature head and canonical merge commit.

**Assessment:** PBM v4 is **IMPLEMENTED / EXACT-HEAD DETERMINISTICALLY VERIFIED / NOT YET PROMOTED**. The next gate is bounded real one-paste canary execution on Desktop and Room plus live-path verification of status/abort/evidence bundling. No full Desktop-versus-Room performance comparison is authorized yet.

---

### E-169 — PBM v4 manual canary exposed operator-choreography and Desktop evidence-parser defects
**Date:** 2026-09-21  
**Kind:** [live canary evidence / operator-workflow defect / evidence-parser defect / no-cognition operations verification]  
**Related work:** I-026 / D-049  
**Evidence state:** VERIFIED for the observed operations-probe and Desktop-capture behavior; no valid Desktop-versus-Room canary pair is claimed

After E-168 deterministic implementation verification, the bounded v4 canary exercised real operating boundaries.

The deterministic no-cognition operations probe initially failed because canary context capture expected `run.json` while the canary runner had created only `state.json`. A localized repair added compatible run metadata before context capture. Focused tests then passed (**7 passed**), the production v4 fingerprint remained unchanged, and a repeated live operations probe passed:

- prepared Room status was `preparing`;
- deterministic `abort` stopped the Room;
- post-abort status reported `stopped` and `aborted: true`;
- a real evidence ZIP was created at the reported bundle path;
- the repository working tree remained clean;
- no model cognition was started by that operations probe.

The subsequent live Desktop canary executed in the correct prepared workspace and produced provider usage, but deterministic capture classified it **INVALID** solely because the v4 prompt parser observed zero principal messages. Captured provenance showed one matching rollout candidate, the exact expected workspace cwd, a concrete Desktop thread id, three tool calls, and nonzero provider usage. Repository inspection then established that the v4 prompt parser recognized only the legacy `event_msg / user_message` record representation even though the usage tooling already encounters newer `response_item` records elsewhere. Therefore the zero-message classification did not provide sufficient evidence that the principal failed the one-paste protocol; the parser itself was too schema-specific.

The principal had also already executed the Room canary by the time the Desktop invalidity was surfaced. No validated Room capture/result from that execution is claimed here.

More importantly, the live canary workflow required the principal to prepare a pair, copy workspace/Room identifiers, launch each product, run separate capture commands, and shuttle outputs back for next-step instructions. The principal rejected that choreography and clarified the desired operator contract: point each platform to its protocol once and let it perform preparation through finalization itself.

**Assessment:** the no-cognition recovery path is behaviorally verified, but the manual v4 operator workflow is superseded before promotion. D-049 governs the replacement: one common protocol, thin Desktop/Room adapters, one principal initiation per platform, automatic pairing/capture/grading/bundling, and schema-tolerant Desktop prompt evidence.

