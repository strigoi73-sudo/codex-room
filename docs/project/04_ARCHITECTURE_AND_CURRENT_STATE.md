# Codex Room — Architecture & Current State

**Last synthesized:** 2026-09-17  
**Scope:** Best current technical synthesis from canonical source, dated implementation/test evidence, and current repository state.  
**Freshness:** Moderate to high volatility. Verify consequential current-state claims against newer source, tests, runtime evidence, and `06_DEVELOPMENT_CONTROL.md`.

## 1. Status legend

- **IMPLEMENTED** — present in the inspected implementation as of the cited evidence/version.
- **HISTORICALLY VERIFIED** — passed stated verification at the time; later changes may require re-verification.
- **DECIDED / NOT IMPLEMENTED** — intended behavior is settled but not shown in current implementation.
- **OBSERVED ISSUE** — evidence supports the problem; no completed repair is established here.
- **EXPLORATORY** — hypothesis or direction still requiring investigation or decision.
- **SUPERSEDED** — older state retained only for history; newer evidence or a later decision governs.

## 2. Canonical repository and verification

**IMPLEMENTED / VERIFIED**

The canonical repository is the private GitHub repo `strigoi73-sudo/codex-room`; maintained Project sources live under `docs/project/` on canonical `main`. Exact current HEAD, local working-tree state, and active branch state are intentionally not duplicated here; inspect Git/GitHub directly when consequential.

Routine mechanical verification is local. `verify-fast.cmd` is the normal PR gate and `verify-full.cmd` is the exhaustive/manual tier, both backed by `verify-local.ps1`. GitHub Actions is no longer the routine verification path after repeated pre-runner startup failures. GitHub remains the canonical history/review bridge. See D-018 and E-109.

Exact review validity attaches to the reviewed bytes. A push or merge is not itself verification; applicable deterministic checks must pass on the version being described as verified. Verification depth should be proportional to the demonstrated risk and changed behavior rather than repeating broad pytest coverage after sufficient focused evidence already exists.

## 3. Personal organization and protected instruction composition

**IMPLEMENTED / VERIFIED**

Personal production contains exactly three persistent agents: **A — Implementer, B — Verifier, C — Integrator**. They are epistemic peers. C coordinates but has no superior judgment: **C controls coordination, not judgment.**

Fresh standard Rooms use neutral/empty default profile bodies. Shared institutional/peer rules and Room protocol remain protected; C additionally receives protected structural coordination instructions. Optional saved-profile text and Room overrides remain replaceable profile content rather than protected structure. See D-002 through D-004, D-020, D-023, D-024, and E-058.

C's protected coordination policy currently includes:

- use the fewest peer invocations expected to add sufficient value;
- if both A and B are invoked, give them meaningfully differentiated cognitive responsibilities;
- treat invocation as a purchase of cognition, not as message visibility;
- before concurrent delegation, determine whether each assignment can produce useful work independently; parallelize genuinely independent work and sequence work whose useful completion depends on a prerequisite artifact, evidence, or result;
- do not treat verification of an artifact as concurrent with creation/modification of that same artifact unless the verifier has meaningful independent pre-artifact work;
- when delegated implementation, correction, or investigation fails to produce needed work, or fallback work reaches C because another assignment failed or settled without producing it, substantial tool-heavy fallback should normally move to a fresh bounded peer assignment rather than remain on C's accumulated coordinator context;
- that fallback rule applies whether C is in its root coordination assignment or a child assignment created by a peer;
- prefer the capable assignment with the least unnecessary accumulated context, while correctness, safety, continuity, and reliability remain controlling constraints;
- C may still execute directly when work is demonstrably small in expected execution/context cost, urgent, inseparable from integration, or no fresh peer is likely to perform it reliably at lower total cost;
- do not infer that model execution will be cheap merely because a code/file change appears small.

PR #109 introduced dependency-aware sequencing plus the first context-aware fallback rule. A fresh design-only Common Cause rerun then supplied useful naturalistic evidence for the sequencing side: C deliberately ran two genuinely independent design assignments in parallel, with no tools/retries, using **93,939 raw execution tokens** versus the historical **98,996** Stage-1 baseline. This is a behavioral **PASS for avoiding over-serialization**; it is not an implementation/fallback test.

A controlled implementation rerun then exercised the dependency boundary directly. C ran A's implementation concurrently with B's artifact-independent verification-matrix design, waited for the implementation artifact before auditing actual code, found a genuine defect, and delegated a bounded correction. That sequence supports the dependency-aware rule. The same run exposed a remaining fallback loophole: after the correction assignment settled without applying its patch, substantial tool-heavy work reached C in a peer-created child assignment and C executed the fallback itself. PR #110 tightened the fallback wording specifically for that failure mode.

A later ordinary continuation in the post-PR-#110 Room supplied the missing natural evidence. A requested follow-up settled with `PASS` without producing the needed strengthening work; C responded by creating a fresh bounded B assignment rather than absorbing the substantial fallback onto its accumulated coordinator context. B completed the requested regressions/documentation successfully. Therefore both sides of the coordination refinement now have naturalistic support: **dependency-aware sequencing is behaviorally supported, and post-PR-#110 fallback allocation is NATURALISTICALLY SUPPORTED**. Continue monitoring ordinary work rather than manufacturing another benchmark. See D-035 / E-124 through E-126 and current Development Control.

These rules affect freshly composed Rooms from their implementation point forward; existing Room snapshots are not retroactively rewritten.

## 4. Production work model: explicit transaction state

**IMPLEMENTED / VERIFIED / PRODUCTION DEFAULT**

The public production path is **work-model version 2** with `provider_context_mode="assignment_thread"`. D-034 activated that configuration after the Stage-D viability gate passed. Legacy Rooms were deliberately deleted rather than migrated; no public v1 migration layer is required. Historical v1 compatibility code/tests may remain internally where deletion provides no demonstrated product value.

The authoritative work model is explicit transaction state rather than unread conversational backlog:

**Round → Task → Assignment → Join → Result / continuation → Task settlement**

Current transaction actions are:

- `COMPLETE`
- `DELEGATE`
- `EVIDENCE`
- `HISTORY`
- `PASS`

CORE owns declared mechanics: assignment creation/claiming, joins, deterministic evidence/history execution, queueing, retry/recovery, context assembly, exact execution provenance, and settlement validity. Agents retain intellectual judgment: whether peers add value, how to frame work, what evidence matters, how to interpret results, and what conclusion to reach.

A parent Assignment that delegates remains nonterminal until child work settles and the parent resumes. Nested A↔B delegation remains allowed. Joins release mechanically only when members are terminal and release at most once. A Task cannot settle with unresolved transaction work. Readable/audit events do not become runnable work without an explicit Assignment.

I-015 is complete. Stage A established the transaction kernel; Stage B moved bounded source retrieval behind `EVIDENCE`; Stage C introduced assignment-scoped provider context and bounded `HISTORY`; Stage D passed the preregistered viability gate; D-034 then activated v2 + assignment-thread publicly. Post-close ordinary-use repair PR #108 corrected remaining transaction contract/retry bounds without reopening I-015. See E-094 through E-123.


### Round completion policy

**IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED**

Rounds now carry an explicit `completion_policy`. `auto_settle` remains the default and preserves ordinary transaction settlement. `continuous` is an opt-in standing-objective mode for instructions whose lifecycle should remain active after one bounded coordinator activity completes.

In continuous mode, child Assignments still settle normally. When the task coordinator reaches the ordinary settlement boundary with no open Assignments/Joins, required contributors satisfied, and no hard turn-limit stop, CORE requeues the **same coordinator Assignment** instead of settling the Task. That preserves the Assignment's existing `context_thread_id` under the production `assignment_thread` provider-context model. The next coordinator execution receives the Round objective again plus explicit continuous-mode lifecycle guidance. `COMPLETE` or `PASS` ends the current bounded coordinator activity but does not by itself close the standing Round objective.

Manual human stop, the Round hard turn limit, and genuine runtime boundaries remain termination mechanisms. Continuous mode is explicit per Round and does not weaken child-assignment scope or make perpetual execution the default.

PR #113 implemented and exact-head verified this behavior; canonical merge commit is `aa3c98dd81303bfd2cb5798c73dec1be2f13dcda`. A subsequent naturalistic `Stay busy.` Room crossed the ordinary coordinator settlement boundary four times, each time resuming the same root C Assignment and its assignment-scoped provider context, then continued into a fifth bounded activity until the human paused the Room at 42/500 turns. Child Assignments continued to settle normally. See D-036, E-130, and E-131. Continuous Round mechanics are therefore naturally supported; further dedicated acceptance testing is unnecessary absent a demonstrated failure.


## 5. Assignment-scoped provider context and continuity

**IMPLEMENTED / VERIFIED / PRODUCTION DEFAULT**

Each logical v2 Assignment owns a durable provider `context_thread_id`. Continuations of that same Assignment reuse its exact provider thread; different Assignments receive different provider contexts even when owned by the same persistent A/B/C identity.

This separates durable organizational identity from provider-context transport. C-N1 measured a 24.0% input reduction for assignment-scoped context on a self-contained warmed-history task. C-N2 demonstrated the expected continuity gap: a fresh Assignment could not recall an arbitrary fact available on C's permanent thread. D-033/C.3 therefore added explicit bounded `HISTORY` retrieval rather than restoring wholesale provider-thread inheritance. C-N3 verified recovery of the needed prior result on the same Assignment thread with exact event provenance. See E-103 through E-106.

`HISTORY` supports bounded `RECENT` and lexical `SEARCH` retrieval over completed Assignment results in earlier Rounds of the same Room. Selected exact event IDs become durable Assignment context provenance. Current Task/Assignment/Join/Evidence state remains authoritative and separate from historical retrieval.

## 6. Structured source evidence

**IMPLEMENTED / VERIFIED**

For v2 work, bounded read-only source needs are normally declared through `EVIDENCE` using semantic `READ`, `SEARCH`, and `FIND` requests. Agents decide what evidence is needed; CORE owns source authorization, bounds, batching/execution choice, restart-safe evidence state, provenance, and normalized return to the same Assignment.

This removes normal CLI discovery, shell quoting, and batching mechanics from model cognition. Underlying `inspect_source` operations remain implementation/operator primitives. E-101's naturalistic validation completed the source task with zero agent tool/command calls and 72,271 execution tokens, compared with the much more expensive earlier direct-CLI pattern.

PR #108 aligned provider/runtime transaction bounds and retry accounting after ordinary Common Cause use exposed two remaining contract mismatches. Successful `EVIDENCE`/`HISTORY` continuations no longer consume the one corrective retry budget; provider schema/guidance mirrors relevant runtime bounds and source-relative path semantics. See E-123.

## 7. Deterministic capability substrate

**IMPLEMENTED / VERIFIED end to end through P4.5**

Codex Room provides a registered deterministic capability system so stable mechanical procedures can be executed as software rather than repeatedly regenerated as model cognition.

The default CORE library includes `assert_file`, `find_files`, `search_text`, `compare_files`, and `inspect_source`, with stable identity, typed contracts, permissions/side-effect declarations, implementation hashes, verification metadata, bounded outputs, and safe telemetry.

Custom capabilities use a bounded draft/package model, deterministic verification cases, immutable content-addressed publication, protected Room binding, normal registry discovery/invocation, and lineage-scoped rollover inheritance. Rollover preserves the exact registered version/provenance rather than selecting a newest capability implicitly. See D-022 and E-030 through E-040.

Agents decide when deterministic software is warranted. Registered capabilities are preferred when they are adequate; custom software is justified by demonstrated reuse, reliability, provenance, or mechanical-complexity value rather than by a desire to create tooling for its own sake.

## 8. Model allocation and execution constraints

**IMPLEMENTED / MONITOR**

Production supports bounded C-selected peer configurations across admitted Luna, Terra, and Sol settings. C should prefer lower-cost cognition for routine bounded delegated work and spend stronger cognition only when complexity, uncertainty, risk, or prior trouble provides an affirmative reason. A/B may request escalation from C but do not self-route execution configuration.

Astra execution is prohibited by D-028; the runtime fails closed if the currently identified Astra model is attempted.

No automatic model router is authorized. The dedicated synthetic P1 benchmark phase is closed because the experiments were expensive and did not establish a trustworthy general ranking. Naturalistic useful work is the evidence source. See E-073 through E-077.

## 9. Execution economics and continuation control

**IMPLEMENTED / MONITOR**

A recurring economic failure mode was model→tool→model continuation amplification: many small tool calls inside one SDK turn repeatedly replayed large cached contexts. I-014 introduced bounded/batched source retrieval, direct source commands, explicit triggering-vs-passive context labels, and execution-level usage deltas. PR #70 further reduced always-loaded capability ceremony and emphasized batching/sufficient-evidence stopping.

The controlled LAB-2C post-fix run used 3 tool calls / 4 provider responses / 92,765 total tokens, versus 38 tool calls / 39 provider responses / 1,805,314 tokens in the pre-fix Room run on the same fixture. This is evidence for the repaired mechanism, not a universal savings claim. See E-081 through E-090.

The historical Common Cause implementation later demonstrated another expensive pattern at the coordination level: dependent implementation/verification scheduled concurrently, followed by failed corrective delegations and large fallback execution on accumulated C context. The successful historical implementation Round consumed **1,511,456 raw execution tokens**, including **1,041,653 on C**. PRs #109/#110 target that demonstrated pattern without creating a new scheduler, fourth agent, or hard-coded cognitive specialty.

The controlled post-#109 implementation rerun consumed **863,799 raw execution tokens through its turn-limit stop**, with C at **354,530**, A at **485,893**, and B at **23,376**. It showed materially less C accumulation and correct artifact-dependent sequencing, but it did not finish the requested regression/readiness work. The 42.9% raw-token difference from the historical successful implementation is therefore **directional evidence only, not a completed savings benchmark**. It also exposed the fallback loophole that PR #110 subsequently tightened.

The post-#110 controlled replication then used **953,892 raw execution tokens** and completed the artifact-dependent audit correctly, while later ordinary continuation supplied direct naturalistic support for the tightened fresh-peer fallback. Do not treat these different endpoints as a single comparable benchmark series. See E-125 and E-126.

## 10. Recovery, usage walls, and lifecycle safety

**IMPLEMENTED / VERIFIED / MONITOR**

Codex Room retains durable exact execution binding, serialized per-agent execution, lifecycle generations, stale-result protection, restart reconciliation, and fail-closed recovery. Usage-limit walls create delayed continuation work tied to the exact relevant provider context; repeated walls reschedule rather than storm immediate retries. Transaction-mode restart/recovery preserves Assignment identity and exact Assignment provider context where applicable.

A later ordinary Common Cause continuation exposed a narrow exact-turn reconciliation race. The provider SDK rollout recorded a valid final decision and `task_complete`, while CORE's concurrent exact-history reconciliation observed `interrupted` and failed the execution before the usable notification completion was preserved. This produced a false terminal `Codex turn was interrupted` and a `transaction_failed` Round even though the model/provider turn had actually completed.

Commit `6b810f0e327da4055ced97f38a60977f4eba9c46` repairs that boundary narrowly. `interrupted` history now raises an interruption-specific terminal subtype and receives a **0.05-second** bounded opportunity for the already-started notification stream to settle. If a usable notification completion arrives in that window, it is accepted; if not, the genuine interruption remains terminal. Other terminal failures remain authoritative and do not receive the grace, including usage-limit/error-code history. No replacement work, broad retry loop, or overlapping turn is introduced.

Focused reconciliation coverage passed 46/46, and the canonical fast verifier passed its Linux, Windows, and browser phases on the reviewed working tree. An additional exhaustive exact-commit attempt passed 426 Linux/Python-3.12 tests before stopping because Python 3.11 was unavailable inside WSL; that incomplete run is not represented as a full-verifier PASS. See E-127.

Maintenance watchdog health is operator-visible through `/api/health`, including runtime/source provenance and failure/recovery state. See E-068, E-069, E-100, E-102, E-105, and E-127.

## 11. Data, exports, and operator maintenance

**IMPLEMENTED / VERIFIED**

SQLite uses WAL/foreign-key/transactional safeguards and durable execution/work-state provenance. Live Room snapshots use bounded recent event windows while exports request complete Room history. The offline maintenance CLI provides integrity check, verified backup, backup verification, and guarded restore. See E-025 and E-087.

The Room UI exposes the persistent Room ID and current/last execution model/effort. `Restart-Codex-Room.bat` preserves the existing browser tab/window and restarts the server with `--no-browser`; the retained tab reconnects through the existing WebSocket retry path. See E-089 and E-091.

## 12. Current known limits / deferred items

- D-019 Personal daily usage pacing remains **DECIDED / NOT IMPLEMENTED** because mixed subscription-allowance versus purchased-credit semantics are unresolved.
- I-003 provider-side adoption of replacement developer instructions on same-thread profile rebind remains low-priority **NEEDS VERIFICATION**; no current product failure justifies a dedicated paid test.
- broader archive indexing/embeddings/summarization is not justified by current evidence; bounded `HISTORY` remains the implemented continuity mechanism.
- no automatic model router is authorized.
- stronger custom-capability per-capability OS isolation, shareable/redacted exports, broader productization, Enterprise features, and large refactors remain deferred until demonstrated need.

## 13. Current development posture

The major foundation, A2, P4, A3 remediation, and I-015 transaction redesign/cutover are complete. PR #108 closed the ordinary-use transaction contract/retry defect; PRs #109 and #110 implemented the Common Cause coordination-economics structural refinement. Subsequent ordinary continuation supplied naturalistic support for both dependency-aware sequencing and PR #110's tightened failed-delegation fallback.

That same continuation exposed a real CORE lifecycle defect at the exact-turn reconciliation boundary. The defect is now repaired and sufficiently verified at E-127. No further synthetic Common Cause coordination benchmark is required.

The existing Common Cause game workspace should be preserved; its final exact-artifact verification is complete and the artifact is play-ready. PR #113's continuous Round completion semantics under D-036 are now naturally supported by E-131. No dedicated continuous-Round follow-up is required. Competitive Common Cause play remains a separate human authorization. Volatile sequencing and monitor state live in `06_DEVELOPMENT_CONTROL.md` rather than here.

Do not launch adjacent broad v2 redesign, personality calibration, new memory architecture, automatic model routing, or unrelated maintenance merely because this checkpoint exists.
