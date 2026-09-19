# Codex Room — Architecture & Current State

**Last synthesized:** 2026-09-19  
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

The repeatable functional acceptance campaign completed **T0–T14 with every test recorded PASS** on 2026-09-19. The campaign exercised baseline verification, transaction/delegation behavior, EVIDENCE/HISTORY, explicit worker continuity, hard-restart recovery, C REFRESH, custom capabilities, rollover, offline maintenance, explicit model allocation, and an integrated implementation/verification mission. T8 found one genuine hard-restart recovery defect; PR #130 repaired it and the natural hard-restart rerun passed. See E-140, E-141, and `docs/CODEX_ROOM_FUNCTIONAL_ACCEPTANCE_TEST_PLAN.md`.

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
- `REFRESH`
- `CONSULT_PRINCIPAL`
- `PASS`

CORE owns declared mechanics: assignment creation/claiming, joins, deterministic evidence/history execution, queueing, retry/recovery, context assembly, exact execution provenance, and settlement validity. Agents retain intellectual judgment: whether peers add value, how to frame work, what evidence matters, how to interpret results, and what conclusion to reach.

A parent Assignment that delegates remains nonterminal until child work settles and the parent resumes. Nested A↔B delegation remains allowed. Joins release mechanically only when members are terminal and release at most once. A Task cannot settle with unresolved transaction work. Readable/audit events do not become runnable work without an explicit Assignment.

I-015 is complete. Stage A established the transaction kernel; Stage B moved bounded source retrieval behind `EVIDENCE`; Stage C introduced assignment-scoped provider context and bounded `HISTORY`; Stage D passed the preregistered viability gate; D-034 then activated v2 + assignment-thread publicly. Post-close ordinary-use repair PR #108 corrected remaining transaction contract/retry bounds without reopening I-015. See E-094 through E-123.

### Private principal consultation

**IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**

D-038 adds a C-only `CONSULT_PRINCIPAL` action for the root coordinator Assignment. The action is explicitly nonterminal: CORE records C's consultation as a private observer event, creates no A/B delivery or wakeup, and moves the exact Assignment to durable `waiting_principal` state. The human principal is not modeled as a fourth production agent.

The principal's reply is bound to the exact consultation event and waiting Assignment. CORE rejects stale or duplicate replies, records the reply as a private non-agent-readable/non-turn-triggering event, and requeues the same Assignment. Under the production assignment-thread model, the same durable `context_thread_id` is therefore retained. The reply is injected only into that C continuation rather than entering normal Room delivery or bounded `HISTORY`.

The wait is transaction state, so an ordinary runtime restart does not erase it. Pause may preserve the wait and accept a reply without executing until Resume; Stop/cancel marks `waiting_principal` work cancelled with the rest of the Task. Private consultation does not become shared organizational knowledge automatically. C must explicitly communicate only the necessary consequence if A/B later need it.

The initial I-016 release deliberately excludes A/B→principal consultation and a nonblocking private notification action. Those are separate product choices, not implicit extensions of this primitive.

PR #137 exact feature head `e58c758527ae6a3954be9525b1411324e12ec7de` passed the repository-standard fast gate: 63 Linux focused tests, 118 Windows portability tests, and 7 browser interaction/stability tests, with a clean tracked tree and clean `git diff --check`. It squash-merged to canonical `main` as `d57d25769a8be215cc01af354983fd9c44b10825`. See E-142.

The first naturalistic Room exposed a C action-selection defect: C used terminal `COMPLETE` to ask the principal instead of entering the private wait state. PR #139 hardened C's protected structural instructions and transaction decision contract; exact repair head `d964af1d8fdd9c49dfcdf18f3e6104aa5b21eed9` passed the same 63 Linux / 118 Windows / 7 browser gate and squash-merged as `26c7fb8035f15752929cfc27bd4295f0f8035ec7`. A fresh post-repair Room then passed end-to-end naturalistic acceptance: private C→principal consultation, private exact-event reply, same-Assignment continuation, no A/B execution, and successful completion. See E-143 and E-144.


### Round completion policy

**IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED**

Rounds carry an explicit `completion_policy`. `auto_settle` remains the default and preserves ordinary transaction settlement. `continuous` is an opt-in standing-objective mode for instructions whose lifecycle should remain active after one bounded coordinator activity completes.

Under D-037/BCTX-1, **Task is the bounded objective/activity unit**. In continuous mode, child Assignments still settle normally. When the task coordinator reaches the ordinary settlement boundary with no open Assignments/Joins, required contributors satisfied, and no hard turn-limit stop, CORE settles the current Task and atomically creates a successor Task in the same Round. The successor Task is linked through `parent_task_id`, preserves the required-contributor contract, and receives a fresh coordinator Assignment. In production `assignment_thread` mode that successor C Assignment explicitly inherits the predecessor C Assignment's exact `context_thread_id`; if that context lineage is unexpectedly missing, settlement fails closed rather than silently starting a new coordinator context. The `continuous_round_resumed` event records predecessor and successor Task/Assignment IDs.

A hard turn-limit settlement creates no successor Task. Manual human stop and genuine runtime boundaries remain termination mechanisms. Continuous mode is explicit per Round and does not weaken child-assignment scope or make perpetual execution the default.

PR #113 originally established and naturalistically supported the standing-objective behavior by requeueing one coordinator Assignment. D-037 intentionally superseded that mechanism while preserving the standing-Round semantics. PR #117 implemented BCTX-1 on exact verified head `6871f8e45e76c783e9709b2a7feead561939a779`; focused continuous transaction tests passed **4/4**, and the repository fast verifier passed **49 Linux focused tests, 118 Windows focused tests, and 3 browser transcript tests** with a clean tracked tree. Canonical merge commit is `46ee194f791cd6e2cf2a823c98e1e74a98814c7c`. See D-037 and E-132.

The earlier naturalistic `Stay busy.` acceptance remains evidence that the standing objective survives repeated bounded activity boundaries and that child work settles normally; its exact same-Assignment mechanism is historical evidence for D-036, not the current BCTX-1 implementation.


## 5. Assignment-scoped provider context and continuity

**IMPLEMENTED / VERIFIED / PRODUCTION DEFAULT through BCTX-4**

Each logical v2 Assignment stores a durable provider `context_thread_id`. Ordinary unrelated Assignments receive different provider contexts even when owned by the same persistent A/B/C identity. D-037/BCTX-1 deliberately carries C's provider thread across causally linked successor Tasks in one continuing Round. D-037/BCTX-2 allows a later **A/B Assignment inside the same Task** to continue a prior same-worker provider context through explicit `context_from_assignment_id` / durable `context_parent_assignment_id` lineage. Common worker identity alone does not imply continuity: fresh context remains the default unless deliberate causal continuation is requested, and CORE rejects stale/forking lineage. This mechanism is generic objective-local iterative collaboration, not a deterministic repair/testing workflow.

BCTX-3 extends that deliberate worker continuity across bounded Task boundaries without making it automatic. When a Task settles in an active continuous Round, the latest worker-owned provider contexts from that Task become grace-eligible for the next **two successful C executions**. C receives only bounded grace metadata—source Task, source Assignment, worker, and remaining executions—not the worker transcript or result text. To continue a worker context into a successor Task, C must explicitly name the eligible source Assignment through `context_from_assignment_id`; CORE requires the source to be the same worker's latest thread owner, a terminal Assignment in a settled Task from the same Round, and an ancestor in the current Task lineage. Successful continuation consumes the predecessor grace source and records the successor Assignment as continuation provenance.

Unused grace retires deterministically. C may explicitly close grace early by listing settled prior Task IDs in `retire_worker_context_task_ids` when it deliberately moves past/closes those objectives. Otherwise each later successful C execution consumes one grace count. Expired or explicitly closed contexts enter durable retirement-pending state, their provider threads are archived, and successful archival is recorded. Pending archival is restart-safe: initialization drains durable retirement-pending contexts. Terminal Round boundaries retire residual grace; Pause preserves it.

BCTX-2 also adds explicit single-child result routing through Join `return_mode`. When a child successfully `COMPLETE`s with the finished required result and the intermediate parent has no material intellectual work left, the parent may request coordinator return explicitly; CORE then waives relay-only intermediate work mechanically and preserves exact child-result and Join provenance. Failure/degraded paths and ordinary parent-required integration continue to resume the parent instead of bypassing judgment.

C receives a bounded status-only `<task_coordination_status>` block containing current Task/Assignment/Join ownership, state, dependency, context-lineage, and return-routing metadata, plus a separate bounded worker-grace status view when grace is available. These blocks intentionally exclude worker result text, provider transcript, and tool chatter; substantive results still cross through explicit dependency/result/history paths.

PR #119 implemented BCTX-2 on exact locally verified head `3a1a7f240ed43ebd4c7ea7149a5855732a23838d`; see E-133. PR #122 implemented BCTX-3 on exact locally verified head `ed44f87f7648f88aca8096109a221cd00339d563`; see E-134. PR #124 implemented BCTX-4 on exact locally verified head `fdb21c60dd9f03c82111014a3987f0f783124e7c`. BCTX-4 focused transaction/context verification passed **44/44**; the repository fast verifier passed **60 Linux focused tests, 118 Windows focused tests, and 3 browser transcript tests** with the tracked tree clean and HEAD unchanged. PR #124 squash-merged those verified implementation bytes to canonical `main` as `e9669a05255beb3cce73f80cc491601f99db5219`. No hosted workflow run was attached at closeout time. See D-037 and E-135.

BCTX-4 adds an explicit C-only `REFRESH` action for deliberate coordinator context reset. C supplies a bounded free-form continuity checkpoint; CORE creates a distinct fresh C provider context, records old/new context identities and checkpoint provenance durably, and injects the checkpoint only into the first turn on the fresh context. Current Round/Task/Assignment/Join/Evidence/grace state is rebuilt separately from SQLite instead of replaying the old coordinator transcript. The handoff is fail-closed: the refreshed Assignment remains non-runnable until the old C context is archived, pre-activation failure falls back to the exact old context, archive-pending handoff survives restart and is retried, and human Stop cancels unresolved refresh work with the transaction. Refreshed C context continues normally across later BCTX-1 successor Tasks.

Post-BCTX naturalistic use showed that merely making `REFRESH` available was insufficient: C carried one coordinator context across many bounded Tasks and never refreshed while its completed-execution input load rose into the 100K+ range. PR #127 therefore adds **coordinator context economics** to eligible C root turns. CORE reports deterministic telemetry for the exact provider thread—executions and settled Tasks carried, first-execution input baseline, last completed execution input/cached-input load, provider-reported cumulative input tokens, and growth from baseline. The prompt labels these figures as execution-load telemetry rather than context-window occupancy. C retains judgment: approximately **64K last-execution input tokens** is an advisory point to actively consider refresh at the next clean bounded Task boundary, and approximately **96K** is an advisory point to strongly prefer refresh unless a concrete continuity/integration reason justifies deferral. CORE does not auto-refresh on either range. A successful `REFRESH` creates a distinct provider thread and therefore a fresh economics baseline. See E-137 and E-138.

A bounded naturalistic revalidation after PR #127 supplied the previously pending behavioral evidence. With the same literal `Stay busy.` objective and an authoritative 17-file source fixture, C crossed the consider range at **65,796** completed-execution input tokens, then deliberately issued `REFRESH` on the next C execution at **67,960** input tokens. CORE completed the checkpoint handoff to a distinct provider thread, whose first completed execution established a fresh **21,421-token** baseline; work then continued normally until the deliberately configured 40-turn limit. The run used approximately **1.963 million** raw execution-token deltas, about **49.1K per turn**, versus approximately **61.1K per turn** in E-137. This is naturalistic support that the advisory telemetry changes coordinator refresh adoption and can reduce observed execution cost; it is not a guaranteed savings rate or an automatic-refresh mandate. See E-139.

This separates durable organizational identity from provider-context transport. C-N1 measured a 24.0% input reduction for assignment-scoped context on a self-contained warmed-history task. C-N2 demonstrated the expected continuity gap: a fresh Assignment could not recall an arbitrary fact available on C's permanent thread. D-033/C.3 therefore added explicit bounded `HISTORY` retrieval rather than restoring wholesale provider-thread inheritance. C-N3 verified recovery of the needed prior result on the same Assignment thread with exact event provenance. See E-103 through E-106.

Under BCTX-3, `HISTORY` supports bounded `RECENT` and lexical `SEARCH` retrieval over completed Assignment results from **earlier settled Tasks in the same Round** as well as earlier Rounds of the same Room. Same-Round retrieval excludes the current Task. Selected exact event IDs become durable Assignment context provenance, existing result/count/context bounds remain in force, and current Task/Assignment/Join/Evidence state remains authoritative and separate from historical retrieval.

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

### Underlying Codex runtime versus Room host surface

**IMPLEMENTED / AUDITED**

Each Room participant runs through the official local Codex SDK/App Server substrate as a persistent, non-ephemeral Codex thread rooted in that Room's shared workspace with `workspace_write` sandbox authority. Room session overrides select the Room model/reasoning defaults and explicitly disable Codex's built-in multi-agent/subagent layer; they do not replace the normal Codex configuration stack. Consequently, ordinary Codex runtime facilities such as command execution, file changes, and configuration-dependent web/MCP tooling belong to the underlying execution substrate unless separately disabled by effective Codex configuration or unavailable because required host interaction/authentication is missing.

The Room browser is a separate host surface. Observer messages are submitted through the Room message API and are not parsed as Codex Desktop slash commands. Absence of a Desktop `/` command therefore does not by itself mean the underlying Codex capability is absent. Conversely, Desktop-host features such as its visual browser, integrated human terminal, worktree UI, attachment/editor affordances, and interactive MCP/authentication surfaces are not conferred merely by using App Server.

Codex Room intentionally substitutes its own organizational mechanisms for several Desktop controls: A/B/C transactions replace built-in Codex subagents; D-039 governs model/reasoning allocation; Round/Task state owns organizational objectives; Room compaction/REFRESH manages long-lived coordinator context; and verifier delegation provides independent review cognition. See E-149 for the dated Desktop↔Room capability audit and its qualification of config-dependent tool availability.

I-019 now has a verified CORE command-catalog authority layer. The adapter records the actual running App Server identity from official SDK initialization metadata. `GET /api/codex/commands` resolves the built-in slash-command inventory only against the exact matching official `openai/codex` release source (`rust-v<runtime-version>`), records the upstream source blob SHA, and caches that exact-version manifest under ignored runtime data. A catalog for another runtime version is never accepted as current; missing/unsafe runtime identity or failed exact-version synchronization returns an unavailable catalog with no commands. Browser caching of this endpoint is disabled. Dynamic model service-tier commands are explicitly identified as a live overlay and are not frozen into the built-in manifest. This layer is read-only: it does not yet provide a command dropdown, command dispatch, Room applicability mapping, or live service-tier overlay. See D-040 and E-150.

## 8. Model allocation and execution constraints

**IMPLEMENTED / MONITOR**

Production supports bounded C-selected peer configurations across admitted Luna, Terra, and Sol settings. C should prefer lower-cost cognition for routine bounded delegated work and spend stronger cognition only when complexity, uncertainty, risk, or prior trouble provides an affirmative reason. A/B may request escalation from C but do not self-route execution configuration.

D-039 / I-017 extends that allocation surface to C's own subsequent root-Assignment executions. C may choose any ordinary Low/Medium/High configuration across Luna, Terra, and Sol. Peer delegation is limited to the same nine ordinary configurations. C-only Sol/XHigh and Sol/Max require a private principal approval that raises the exact current Task's durable cognition ceiling; approval does not authorize peers and expires at the Task boundary, so successor Tasks return to the ordinary `sol-high` ceiling. Sol/Ultra remains unavailable because its provider behavior includes automatic task delegation. Exact feature head `b498709ed30541d7a673b245f19a9021eca98ee5` passed the local exact-head gate and merged through PR #142 as `1806a7a16e1477f9dbe88515100f787c0389c709`. Naturalistic acceptance then passed both ordinary self-switching and exceptional approval: E-147 records Terra/High → Luna/Low on one C Assignment with no peer execution, while E-148 records private Task-scoped Sol/XHigh approval, actual Terra/High → Sol/XHigh execution, zero A/B execution, and successor-Task reset to `sol-high` / Terra-high. I-017 is complete. See E-145 through E-148.

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

Codex Room retains durable exact execution binding, serialized per-agent execution, lifecycle generations, stale-result protection, restart reconciliation, and fail-closed recovery. Usage-limit walls create delayed continuation work tied to the exact relevant provider context; repeated walls reschedule rather than storm immediate retries. Transaction-mode restart/recovery preserves Assignment identity and exact Assignment provider context where applicable. I-017 tightened startup reconciliation around durable transaction state: an execution whose decision is already recorded, or whose bound Assignment has advanced out of `running`, is settled during recovery rather than replayed. Only a still-`running` transactional Assignment remains eligible for provider-turn recovery. This prevents a process stop between durable decision application and execution-row settlement from causing duplicate coordinator work after restart.

A later ordinary Common Cause continuation exposed a narrow exact-turn reconciliation race. The provider SDK rollout recorded a valid final decision and `task_complete`, while CORE's concurrent exact-history reconciliation observed `interrupted` and failed the execution before the usable notification completion was preserved. This produced a false terminal `Codex turn was interrupted` and a `transaction_failed` Round even though the model/provider turn had actually completed.

Commit `6b810f0e327da4055ced97f38a60977f4eba9c46` repairs that boundary narrowly. `interrupted` history now raises an interruption-specific terminal subtype and receives a **0.05-second** bounded opportunity for the already-started notification stream to settle. If a usable notification completion arrives in that window, it is accepted; if not, the genuine interruption remains terminal. Other terminal failures remain authoritative and do not receive the grace, including usage-limit/error-code history. No replacement work, broad retry loop, or overlapping turn is introduced.

Focused reconciliation coverage passed 46/46, and the canonical fast verifier passed its Linux, Windows, and browser phases on the reviewed working tree. An additional exhaustive exact-commit attempt passed 426 Linux/Python-3.12 tests before stopping because Python 3.11 was unavailable inside WSL; that incomplete run is not represented as a full-verifier PASS. See E-127.

Functional Acceptance T8 later exercised a distinct startup-recovery boundary: after a hard restart, an exact active transaction turn could be authoritatively recovered as `interrupted` and was initially treated as terminal. PR #130 now permits only a startup-marked recovering transaction execution to spend the Assignment's existing one-retry budget after that exact interrupted recovery; ordinary runtime interruptions remain terminal and uncertain identity remains fail-closed. Exact-head focused verification, `verify-fast.cmd`, and a natural hard-restart rerun all passed. The rerun retried the same durable C Assignment, completed A/B delegation and integration, and closed `transaction_settled`. See E-140.

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

Engineering Foundation, A2, P4, A3 remediation, I-015, and the complete D-037/BCTX bounded-context program are finished. Work-model v2 with `provider_context_mode="assignment_thread"` remains the public production path.

The 2026-09-19 repeatable functional acceptance campaign is complete: **T0 through T14 are all recorded PASS**. Its only demonstrated runtime-invariant failure was T8's startup-recovered interrupted-turn handling, which was repaired in PR #130 and revalidated by a natural hard-restart rerun. E-141 owns campaign closeout; E-140 owns the detailed defect/repair evidence.

No follow-on engineering phase is automatically authorized by that closeout. D-019 Personal daily usage pacing remains deferred on unresolved mixed subscription-allowance / purchased-credit semantics. The Common Cause artifact is verified play-ready, but competitive play remains a separate principal authorization. Existing reconciliation/profile-adoption/economy items remain monitor-only unless ordinary use supplies contrary evidence.

Current sequencing, blockers, and monitor state belong in `06_DEVELOPMENT_CONTROL.md`. Do not infer a new project from completion of the acceptance campaign, and do not launch adjacent redesign, automatic model routing, broad memory/index work, or maintenance investigation without demonstrated need or explicit principal direction.
