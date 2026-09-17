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