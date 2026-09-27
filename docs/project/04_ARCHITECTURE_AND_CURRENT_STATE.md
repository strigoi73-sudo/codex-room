# Codex Room — Architecture & Current State

**Last synthesized:** 2026-09-26
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

Routine mechanical verification is local. `verify-fast.cmd` is the normal PR gate and `verify-full.cmd` is the exhaustive/manual tier, both backed by `verify-local.ps1`. GitHub Actions is no longer the routine verification path after repeated pre-runner startup failures. GitHub remains the canonical history/review bridge. See D-018 and E-109. Repeated exact-head feature verification is now codified in repository-root `verify-feature.ps1`, which owns shutdown through `Kill-Codex-Room.bat`, exact base/head checks, optional focused pytest, canonical broad verification, final exact-head confirmation, and restoration of the caller's checkout without terminating the interactive PowerShell shell. Its first merged-main self-verification passed on 2026-09-27. See E-192.

Exact review validity attaches to the reviewed bytes. A push or merge is not itself verification; applicable deterministic checks must pass on the version being described as verified. Verification depth should be proportional to the demonstrated risk and changed behavior rather than repeating broad pytest coverage after sufficient focused evidence already exists.

The repeatable functional acceptance campaign completed **T0–T14 with every test recorded PASS** on 2026-09-19. The campaign exercised baseline verification, transaction/delegation behavior, EVIDENCE/HISTORY, explicit worker continuity, hard-restart recovery, C REFRESH, custom capabilities, rollover, offline maintenance, explicit model allocation, and an integrated implementation/verification mission. T8 found one genuine hard-restart recovery defect; PR #130 repaired it and the natural hard-restart rerun passed. See E-140, E-141, and `docs/CODEX_ROOM_FUNCTIONAL_ACCEPTANCE_TEST_PLAN.md`.

## 3. Personal organization and protected instruction composition

**IMPLEMENTED / VERIFIED**

Personal production contains exactly three persistent agents: **Agent A, Agent B, and Agent C**. A and B are operationally equivalent epistemic peers with the same neutral default profile and no protected occupational or cognitive specialization. C is also an epistemic peer, with protected coordination responsibilities rather than superior judgment: **C controls coordination, not judgment.**

Fresh standard Rooms use neutral/empty default profile bodies. Shared institutional/peer rules and Room protocol remain protected; C additionally receives protected structural coordination instructions. Optional saved-profile text and Room overrides remain replaceable profile content rather than protected structure. See D-002 through D-004, D-020, D-023, D-024, and E-058.

C's protected coordination policy currently includes:

- use the fewest peer invocations expected to add sufficient value;
- if both A and B are invoked, give them meaningfully differentiated cognitive responsibilities;
- treat invocation as a purchase of cognition, not as message visibility;
- before concurrent delegation, consider both dependency and interaction value: determine whether each assignment can produce useful work independently and whether seeing another participant's contribution first would materially improve the reasoning;
- parallelize independent cognition when neither assignment materially benefits from receiving the other's contribution first;
- sequence work whose useful completion depends on a prerequisite artifact, evidence, or result, or when one participant's contribution should become substantive input to another participant's reasoning, including rebuttal, critique, cross-examination responses, negotiation, iterative refinement, and dialogue where responsiveness is part of the objective;
- follow explicit principal ordering when supplied; otherwise choose order from the objective, relevant context continuity, and execution economy without permanent A/B precedence;
- do not serialize independent work merely to work around context-visibility defects; concurrency remains a supported behavior that CORE must make mechanically safe;
- do not treat verification of an artifact as concurrent with creation/modification of that same artifact unless the peer assigned verification has meaningful independent pre-artifact work;
- when delegated implementation, correction, or investigation fails to produce needed work, or fallback work reaches C because another assignment failed or settled without producing it, substantial tool-heavy fallback should normally move to a fresh bounded peer assignment rather than remain on C's accumulated coordinator context;
- that fallback rule applies whether C is in its root coordination assignment or a child assignment created by a peer;
- prefer the capable assignment with the least unnecessary accumulated context, while correctness, safety, continuity, and reliability remain controlling constraints;
- C may still execute directly when work is demonstrably small in expected execution/context cost, urgent, inseparable from integration, or no fresh peer is likely to perform it reliably at lower total cost;
- do not infer that model execution will be cheap merely because a code/file change appears small.

PR #109 introduced dependency-aware sequencing plus the first context-aware fallback rule. I-034 later extended that same protected C-side policy from mechanical prerequisite dependency to **interaction-aware sequencing**: technically independent tasks may still warrant serialization when one participant's contribution is valuable reasoning input to the other. The change remains instruction-level; it adds no debate mode, scheduler, persistent A/B order, or substitute for I-030's CORE visibility repair. PR #220 was principal exact-head verified at `72ea8a50001862ed7de08d8f8f6eb61fa692358c` and merged as `a63df21ccd910885df1dbf59b06c89ea012e4b58`; GitHub comparison reported zero changed files between the verified head and merge commit. See E-188 and E-189.

A fresh design-only Common Cause rerun then supplied useful naturalistic evidence for the sequencing side: C deliberately ran two genuinely independent design assignments in parallel, with no tools/retries, using **93,939 raw execution tokens** versus the historical **98,996** Stage-1 baseline. This is a behavioral **PASS for avoiding over-serialization**; it is not an implementation/fallback test.

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

**IMPLEMENTED / VERIFIED / PRODUCTION DEFAULT through D-052 / I-030**

Each logical v2 Assignment stores a durable provider `context_thread_id`. D-037/BCTX-1 deliberately carries C's provider thread across causally linked successor Tasks in one continuing Round. D-052 now makes **A/B same-Task continuity the ordinary default**: when a worker is delegated later work inside the same active Task, CORE automatically continues that worker's latest completed provider context when one exists and records the exact source in `context_parent_assignment_id`. Stale/forking lineage remains prohibited. C may set `fresh_context=true` when independent re-analysis, deliberate reset, or lower accumulated private/provider context is materially more valuable; explicit `context_from_assignment_id` remains available for exact-source selection and cannot be combined with `fresh_context=true`.

D-052 also adds a bounded public-conversation bridge. On the first execution of each new A/B Assignment, CORE supplies public, agent-readable conversational messages that the inherited provider thread has not actually been supplied, or messages since Task origin for a fresh/new worker context. Each bound provider execution may persist `public_context_through_sequence` as the exact visibility watermark supplied when that provider turn starts. Prompt composition alone does not advance the watermark, and later Assignment/result chronology is not used as a surrogate for provider visibility. This matters under concurrency: a peer message published while another provider turn is already in flight remains unseen by that provider and is therefore eligible for the worker's next Assignment delta.

The delta drains unseen eligible public events oldest-first as one contiguous prefix. The event cap and character bound carry newer unseen messages forward rather than silently skipping them; whole events are supplied, so an oversized first unseen event is not truncated and then incorrectly marked fully visible. When the bounded delta is exhausted, the watermark may advance through the Assignment-origin upper bound because all eligible public conversation through that point has been considered. Private content, mechanical events, status/economics telemetry, and tool chatter remain excluded. The public delta is injected only on the first execution of the new logical Assignment and is not replayed on EVIDENCE/HISTORY/retry continuations of that same Assignment. This preserves provider-context independence without making a worker artificially ignorant of public Room statements.

Bounded `HISTORY` now also permits exact completed Assignment results from earlier work in the current Task, in addition to earlier settled Tasks in the same Round and earlier Rounds. This is a fallback for specific dependencies, not a substitute for the automatic public delta or same-worker continuation.

BCTX-3 extends worker continuity across bounded Task boundaries without making it automatic. When a Task settles in an active continuous Round, the latest worker-owned provider contexts from that Task become grace-eligible for the next **two successful C executions**. C receives only bounded grace metadata—source Task, source Assignment, worker, and remaining executions—not the worker transcript or result text. To continue a worker context into a successor Task, C must explicitly name the eligible source Assignment through `context_from_assignment_id`; CORE requires the source to be the same worker's latest thread owner, a terminal Assignment in a settled Task from the same Round, and an ancestor in the current Task lineage. Successful continuation consumes the predecessor grace source and records the successor Assignment as continuation provenance.

Unused grace retires deterministically. C may explicitly close grace early by listing settled prior Task IDs in `retire_worker_context_task_ids` when it deliberately moves past/closes those objectives. Otherwise each later successful C execution consumes one grace count. Expired or explicitly closed contexts enter durable retirement-pending state, their provider threads are archived, and successful archival is recorded. Pending archival is restart-safe: initialization drains durable retirement-pending contexts. Terminal Round boundaries retire residual grace; Pause preserves it.

BCTX-2 also adds explicit single-child result routing through Join `return_mode`. When a child successfully `COMPLETE`s with the finished required result and the intermediate parent has no material intellectual work left, the parent may request coordinator return explicitly; CORE then waives relay-only intermediate work mechanically and preserves exact child-result and Join provenance. Failure/degraded paths and ordinary parent-required integration continue to resume the parent instead of bypassing judgment.

C receives a bounded status-only `<task_coordination_status>` block containing current Task/Assignment/Join ownership, state, dependency, context-lineage, and return-routing metadata, plus a separate bounded worker-grace status view when grace is available. These blocks intentionally exclude worker result text, provider transcript, and tool chatter; substantive results still cross through explicit dependency/result/history paths.

PR #119 implemented BCTX-2 on exact locally verified head `3a1a7f240ed43ebd4c7ea7149a5855732a23838d`; see E-133. PR #122 implemented BCTX-3 on exact locally verified head `ed44f87f7648f88aca8096109a221cd00339d563`; see E-134. PR #124 implemented BCTX-4 on exact locally verified head `fdb21c60dd9f03c82111014a3987f0f783124e7c`. BCTX-4 focused transaction/context verification passed **44/44**; the repository fast verifier passed **60 Linux focused tests, 118 Windows focused tests, and 3 browser transcript tests** with the tracked tree clean and HEAD unchanged. PR #124 squash-merged those verified implementation bytes to canonical `main` as `e9669a05255beb3cce73f80cc491601f99db5219`. No hosted workflow run was attached at closeout time. See D-037 and E-135.

BCTX-4 adds an explicit C-only `REFRESH` action for deliberate coordinator context reset. C supplies a bounded free-form continuity checkpoint; CORE creates a distinct fresh C provider context, records old/new context identities and checkpoint provenance durably, and injects the checkpoint only into the first turn on the fresh context. Current Round/Task/Assignment/Join/Evidence/grace state is rebuilt separately from SQLite instead of replaying the old coordinator transcript. The handoff is fail-closed: the refreshed Assignment remains non-runnable until the old C context is archived, pre-activation failure falls back to the exact old context, archive-pending handoff survives restart and is retried, and human Stop cancels unresolved refresh work with the transaction. Refreshed C context continues normally across later BCTX-1 successor Tasks.

Post-BCTX naturalistic use showed that merely making `REFRESH` available was insufficient: C carried one coordinator context across many bounded Tasks and never refreshed while its completed-execution input load rose into the 100K+ range. PR #127 therefore adds **coordinator context economics** to eligible C root turns. CORE reports deterministic telemetry for the exact provider thread—executions and settled Tasks carried, first-execution input baseline, last completed execution input/cached-input load, provider-reported cumulative input tokens, and growth from baseline. The prompt labels these figures as execution-load telemetry rather than context-window occupancy. C retains judgment: approximately **64K last-execution input tokens** is an advisory point to actively consider refresh at the next clean bounded Task boundary, and approximately **96K** is an advisory point to strongly prefer refresh unless a concrete continuity/integration reason justifies deferral. CORE does not auto-refresh on either range. A successful `REFRESH` creates a distinct provider thread and therefore a fresh economics baseline. See E-137 and E-138.

A bounded naturalistic revalidation after PR #127 supplied the previously pending behavioral evidence. With the same literal `Stay busy.` objective and an authoritative 17-file source fixture, C crossed the consider range at **65,796** completed-execution input tokens, then deliberately issued `REFRESH` on the next C execution at **67,960** input tokens. CORE completed the checkpoint handoff to a distinct provider thread, whose first completed execution established a fresh **21,421-token** baseline; work then continued normally until the deliberately configured 40-turn limit. The run used approximately **1.963 million** raw execution-token deltas, about **49.1K per turn**, versus approximately **61.1K per turn** in E-137. This is naturalistic support that the advisory telemetry changes coordinator refresh adoption and can reduce observed execution cost; it is not a guaranteed savings rate or an automatic-refresh mandate. See E-139.


PBM v5 C-only evidence later exposed a distinct economy defect in the same assignment-thread substrate: before a 518,708-token tool-bearing C execution, the exact coordinator thread had already accumulated about 124K provider-reported input tokens across four evidence/inspection executions, but the refresh advisory still looked only at the latest execution delta (~41K) and therefore stayed below the 64K consideration threshold. The same provider-context lineage also received the full immutable transaction/evidence/history/capability contract again on each continuation even though that static contract already existed on the exact provider thread.

PR #200 repairs both mechanisms without changing Assignment semantics or making refresh automatic. Coordinator refresh pressure now uses the stronger of **cumulative provider-thread input spend** or **latest-execution input spend**. Established provider-context lineages receive a compact continuation delta instead of replaying the full immutable protocol; fresh assignment threads and post-`REFRESH` threads still receive the full contract. The compact continuation preserves explicit bounded `HISTORY` availability across continuous-mode successor Tasks that intentionally inherit the same provider thread. C retains refresh judgment and CORE continues to rebuild current dynamic Task/Assignment/Join/Evidence state authoritatively. Exact feature head `4434ac711bf3d8a90e7dba2c183ca7e11dc8a75d` passed the targeted regression gate, focused context/transaction suite, PBM-v5 fingerprint invariant, and repository fast verifier, then merged byte-identically as `f09a575881915256c0f7311f4bcce152bd18aeed`. See E-176.

This separates durable organizational identity from provider-context transport. C-N1 measured a 24.0% input reduction for assignment-scoped context on a self-contained warmed-history task. C-N2 demonstrated the expected continuity gap: a fresh Assignment could not recall an arbitrary fact available on C's permanent thread. D-033/C.3 originally answered that gap with explicit bounded `HISTORY` alone; D-052 later amended the worker side after ordinary conversational use showed that making same-Task continuity and already-public peer statements opt-in was too aggressive an economy rule. C-N3 verified recovery of the needed prior result on the same Assignment thread with exact event provenance. See E-103 through E-106.

I-030 closes the remaining D-052 concurrency race. Regression coverage reproduces a peer message published while another worker's provider turn is already in flight and verifies that the next same-thread Assignment receives that message. A second regression queues 60 eligible public messages and verifies oldest-first delivery across the 50-event cap with no skipped or duplicated markers. Exact feature head `08baf90e8836964ebdb7bc6fd9e50df313f1ddc7` passed the repository-standard fast verifier in the normal `C:\Codex Room` checkout: **72 Linux focused tests, 2 warnings; 119 Windows focused tests; 9 browser transcript tests**. PR #222 merged that exact verified content as `fed7538eaaccf65bb769bc360127a028027afbef`; GitHub comparison reported zero changed files between feature head and merge commit. See E-188 and E-190.

Under D-052, `HISTORY` supports bounded `RECENT` and lexical `SEARCH` retrieval over completed Assignment results from earlier work in the **current Task**, earlier settled Tasks in the same Round, and earlier Rounds of the same Room. Selected exact event IDs become durable Assignment context provenance, existing result/count/context bounds remain in force, and current Task/Assignment/Join/Evidence state remains authoritative and separate from historical retrieval. HISTORY is therefore a bounded fallback for specific substantive dependencies rather than a substitute for automatic same-worker continuity or public-delta delivery.

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

Codex's native skill layer is also available inside Rooms. I-020 verified discovery and autonomous/explicit use of predefined skills, Skill Creator authoring of a Room-local skill with a deterministic helper, and cross-agent reuse without a Room-specific `SkillInput` bridge. Protected guidance now prefers a materially suitable existing Codex skill before inventing reusable workflow/software, uses native Skill Creator for genuinely missing reusable workflows, keeps agent-created skills Room-local by default, and reserves Codex Room capability registration for cases that need stronger exact semantics, provenance, declared side effects, verification, independent reuse, or lineage guarantees. Room-local skill packages under `.agents/skills/<name>/SKILL.md` now survive Room rollover through exact-byte, bounded, fail-closed lineage inheritance with deterministic tree-hash provenance; unrelated workspace and `.agents` state remain excluded. I-020 final acceptance is complete: the combined E-153 through E-156 evidence establishes autonomous and explicit named-skill use, Skill Creator authoring, deterministic helper execution, cross-agent reuse, scope/subagent guardrails, and rollover continuity without a parallel skill subsystem or Room-specific SkillInput bridge.

Agents decide when deterministic software is warranted. Registered capabilities are preferred when they are adequate; custom software is justified by demonstrated reuse, reliability, provenance, or mechanical-complexity value rather than by a desire to create tooling for its own sake.

### Underlying Codex runtime versus Room host surface

**IMPLEMENTED / AUDITED**

Each Room participant runs through the official local Codex SDK/App Server substrate as a persistent, non-ephemeral Codex thread rooted in that Room's shared workspace with `workspace_write` sandbox authority. Room session overrides select the Room model/reasoning defaults and explicitly disable Codex's built-in multi-agent/subagent layer; they do not replace the normal Codex configuration stack. Consequently, ordinary Codex runtime facilities such as command execution, file changes, and configuration-dependent web/MCP tooling belong to the underlying execution substrate unless separately disabled by effective Codex configuration or unavailable because required host interaction/authentication is missing.

The Room browser is a separate host surface. Observer messages are handled through the Room message API rather than the Codex Desktop command palette. Missing Desktop host controls do not by themselves mean the underlying Codex capability is absent. Conversely, Desktop-host features such as its visual browser, integrated human terminal, worktree UI, attachment/editor affordances, and interactive MCP/authentication surfaces are not conferred merely by using App Server.

Codex Room intentionally substitutes its own organizational mechanisms for several Desktop controls: A/B/C transactions replace built-in Codex subagents; D-039 governs model/reasoning allocation; Round/Task state owns organizational objectives; Room compaction/REFRESH manages long-lived coordinator context; and task-specific peer delegation can provide independent review cognition. See E-149 for the dated Desktop↔Room capability audit and its qualification of config-dependent tool availability.

I-019 adds a verified read-only **Status & Tools** host surface over existing Room and App Server authority. `GET /api/rooms/{room_id}/status-tools` composes current Round/Task/Assignment state, A/B/C lifecycle/model/economics evidence, coordinator-context guidance, Room-native deterministic capabilities, inherited workspace-file/command-execution classes, and safely inspectable web-search, skills, MCP, apps/connectors, and plugins inventory. Major inherited categories are reported as available, interaction-required, unavailable, or unknown rather than guessed. The surface sanitizes secrets, account-like identifiers, filesystem paths, MCP schemas/payloads, and hidden reasoning, and Refresh is read-only with respect to Room work.

I-022 exact-source and comparative audits (E-159, E-160) establish that the pinned Codex 0.154 App Server/SDK surface is broader than the older host-capability audit alone implied. Exact 0.154 contracts include active-turn steering/interruption, model discovery, thread list/read/fork/archive controls, native review start, account rate-limit/usage reads, permission-profile enumeration, command/file/permission approval requests, tool user-input elicitation, and structured image/local-image turn inputs. Codex Room already uses interruption internally for lifecycle control and already has a generic typed App Server request path in Status & Tools; however, these facts do not automatically create principal-facing Room host surfaces. E-160 compared the candidate families by execution economics and Room fit; later I-035 principal selection authorized directed attachment handoff.

I-035 now exposes directed observer **image and generic-file handoff** through the existing Room addressing model. PNG/JPEG/WebP images continue to use Codex 0.154 native `LocalImageInput`. Exact Codex 0.154 inspection found no arbitrary non-image `FileInput` turn item, so generic files reuse the underlying Codex filesystem/command substrate instead of adding a content-ingestion shim: immutable attachment bytes are held under the Room host area outside the shared A/B/C workspace, and the addressed Assignment receives filename, media type, and an absolute provider-local path inside a bounded `<directed_file_attachments>` block on its first provider execution only. Same-Assignment HISTORY/EVIDENCE/retry continuations do not resend attachment delivery data.

The observer composer accepts up to four total images/files per message, each attachment bounded to 8 MiB. Image MIME types stay on the native image route; generic files retain a safe filename suffix where practical and unknown browser MIME defaults to `application/octet-stream`. Event/export provenance records attachment kind, identity, original filename, MIME type, byte count, and SHA-256 without host paths or binary content. Invalid attachment payloads fail before lifecycle mutation, and materialization is cleaned up on failed event creation. Text-only observer payload compatibility is preserved.

Directed attachment privacy is a **routing and workspace-discoverability boundary, not a per-agent OS ACL**. Attachment bytes are not copied into `shared/`, and unaddressed agents are not given the private attachment path/input; however, the underlying workspace-write sandbox is not a hostile per-agent filesystem isolation mechanism. Rollover deliberately keeps raw attachments with the archived predecessor Room and does not copy or inherit them into the successor; durable cross-Room meaning must travel through the reviewed checkpoint/allowlisted institutional state rather than raw attachment inheritance.

Image handoff was exact-head verified and merged through PR #225; see E-191. Generic-file handoff and rollover semantics were principal exact-head verified at `1a2997dfa5597d9e953b092538d5a0d3ee18ce26`: **8 focused tests passed, 2 warnings; 78 Linux focused tests passed, 2 warnings; 120 Windows focused portability tests passed; 10 browser transcript tests passed**. PR #227 merged as `c19328b8cfe24a69c649c592297f28d9877ff60d`, and GitHub comparison reported zero changed files between the verified feature head and merge commit. I-035 is complete. See E-192 and E-193.

Other newly identified primitives still require separate principal selection plus Room-semantic, authority, economics, and runtime-acceptance decisions before implementation. Built-in Codex subagents remain disabled.

The earlier exact-runtime Codex host-command catalog experiment is **SUPERSEDED by D-041** and is not part of the current Room host surface. The catalog parser/cache, dedicated catalog API, and Status & Tools catalog card are removed. App Server runtime identity normalization remains only as general runtime provenance for Status & Tools. E-150 and the catalog-specific portions of E-151 are retained as historical evidence for the superseded implementation.


## 8. Model allocation and execution constraints

**IMPLEMENTED / MONITOR**

Production supports bounded C-selected peer configurations across admitted Luna, Terra, and Sol settings. C should prefer lower-cost cognition for routine bounded delegated work and spend stronger cognition only when complexity, uncertainty, risk, or prior trouble provides an affirmative reason. A/B may request escalation from C but do not self-route execution configuration.

D-039 / I-017 extends that allocation surface to C's own subsequent root-Assignment executions. C may choose any ordinary Low/Medium/High configuration across Luna, Terra, and Sol. Peer delegation is ordinarily limited to the same nine configurations. C-only Sol/XHigh and Sol/Max require a private principal approval that raises the exact current Task's durable cognition ceiling; approval does not authorize peers and expires at the Task boundary, so successor Tasks return to the ordinary `sol-high` ceiling. Sol/Ultra remains unavailable because its provider behavior includes automatic task delegation. Exact feature head `b498709ed30541d7a673b245f19a9021eca98ee5` passed the local exact-head gate and merged through PR #142 as `1806a7a16e1477f9dbe88515100f787c0389c709`. Naturalistic acceptance then passed both ordinary self-switching and exceptional approval: E-147 records Terra/High → Luna/Low on one C Assignment with no peer execution, while E-148 records private Task-scoped Sol/XHigh approval, actual Terra/High → Sol/XHigh execution, zero A/B execution, and successor-Task reset to `sol-high` / Terra-high. I-017 is complete. See E-145 through E-148.

D-051 supersedes D-028's blanket Astra prohibition. Under the **default Room model policy**, Astra remains default-denied, but an explicit Astra direction in the opening Room prompt authorizes Astra Low/Medium/High for that conversation lineage. The authorization persists across later turns, Tasks/Rounds, retries, and normal rollover successors; later messages cannot create the authorization. C remains responsible for model allocation and must use Astra only where the principal's opening model directions call for it. CORE fails closed if Astra is selected without the persisted opening-prompt authorization.

D-053 adds a separate creation-time **unrestricted model access** policy. When selected in New Room setup, CORE calls native Codex model discovery, snapshots every model/reasoning-effort combination it can resolve, persists that exact catalog in Room metadata, and uses the snapshot as the allowed execution-config boundary for A, B, and C. In that lineage, Room-side Astra restrictions, peer-versus-C configuration restrictions, and Task-scoped exceptional cognition ceilings do not apply; C still owns economic allocation judgment. The setting is immutable after Room creation and normal rollover successors inherit both the policy and exact catalog. Creation fails closed if native model discovery is unavailable, empty, or demonstrably partial. Default Rooms preserve D-039/D-051 behavior unchanged.


D-055 adds a compact advisory interpretation layer to C's model-policy prompt. CORE renders short descriptions only for known model families and reasoning-effort levels that are already selectable under the current Room policy. The guide explicitly carries no routing, ranking, threshold, escalation, authorization, or validation authority; A/B do not receive it. In unrestricted Rooms, unknown native configurations remain selectable even when no Codex Room guidance exists for them, preserving native `model/list` as the authority boundary rather than recreating a Room-owned model catalog.

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


### PBM benchmark harness and common-protocol orchestration

**IMPLEMENTED / EXACT-HEAD VERIFIED / LIVE CANARY VERIFIED / PRODUCTION DEFAULT**

PBM is the versioned Codex Desktop-versus-Codex Room performance harness. Historical PBM v1-v3 assets remain frozen for explicit reproduction, but canonical `benchmarks/pbm/CURRENT` now resolves to **v4**.

PBM v4 replaces v3's alternating cross-platform controller with one common deterministic protocol and thin platform-native adapters. The principal initiates one non-measured Desktop controller and one persistent non-measured Room Runner; each adapter independently joins the same active PBM pair, launches one fresh measured execution, and returns. Deterministic protocol code owns fingerprint binding, fixture preparation, validity classification, capture, grading, automatic pairing, comparison, status/abort, and evidence bundling. There is no model conversation acting as a durable cross-platform polling loop and no principal run-id shuttling.

The production v4 workload is a frozen seven-task cross-domain battery covering mechanical change, bounded investigation, localized bug repair, small feature work, state-mutation repair, constrained design, and integrated CLI work. Desktop and Room receive equivalent fixtures/prompts/graders but may organize execution through their native capabilities. The known-inconsistent historical `t07-spec-repair` task is excluded. Every retained task has a deterministic known-good reference that must earn full credit in the v4 audit.

Desktop uses native fresh-task creation from `pbm_desktop_controller`; the adapter accepts either a persisted rollout/session id or a provisional `client-new-thread:<uuid>` identity returned by Desktop. Provisional ids are resolved fail-closed to the unique persisted rollout created after PBM preparation with the exact controller cwd, then rebound to the durable rollout thread id. Child `user.text` records are treated as post-launch substantive intervention; zero is the normal native delegated-child baseline.

Room uses the persistent `PBM v4 Room Runner`. C launches a detached deterministic worker that creates one fresh ordinary measured Room. The measured Room retains ordinary A/B/C coordination and D-039 cognition, while substantive principal consultation or abnormal settlement invalidates/fails the arm rather than being silently accepted.

PR #190 introduced the seven-task battery and corrected Desktop child-message validity semantics. Exact feature head `5e367513e9331a09c768aad377b5924b274b5e16` passed the seven-task reference audit at 100/100 for every task, 55 focused PBM tests, and the routine fast verifier; merge #190 preserved those exact implementation bytes. PR #192 then repaired provisional Desktop task-id resolution and stranded deterministic finalization. Exact feature head `c5efa3ce144b3cbc5b731fb363f1871c2d67e661` passed Python compilation, **26 focused PBM v4 tests**, and the routine fast verifier (**63 Linux / 118 Windows / 9 browser**), then merged as `97da426e8b7cc7f19226299fa6dd19a0dd1d418e` with zero file differences from the verified head.

The final merged-bytes canary `pbm-v4-canary-protocol-20260921T085358797378Z` completed with Desktop **VALID / 100**, Room **VALID / 100**, matching benchmark and canary fingerprints, `comparable: true`, no finalization error, and the active pair cleared. This satisfies the live promotion gate. No paid seven-task Desktop-versus-Room performance comparison has yet been run, so verification of PBM v4 must not be mistaken for a product-performance result.

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
