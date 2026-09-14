# Codex Room — Architecture & Current State

**Last synthesized:** 2026-09-12  
**Scope:** Best current technical synthesis from the canonical source baseline, dated implementation/test evidence, and current repository state.  
**Freshness:** Moderate to high volatility. Verify consequential current-state claims against newer source, tests, or runtime evidence when available.

## 1. Status legend

- **IMPLEMENTED** — present in the inspected implementation as of the cited evidence date/version.
- **HISTORICALLY VERIFIED** — passed stated verification at the time; later changes may require re-verification.
- **DECIDED / NOT IMPLEMENTED** — intended behavior has been decided but current implementation has not been shown to contain it.
- **OBSERVED ISSUE** — evidence supports the problem; no completed fix is established here.
- **EXPLORATORY** — hypothesis or design direction still requiring investigation or decision.
- **SUPERSEDED** — older state retained only for history; newer evidence or a later decision governs.

## 2. Source-control foundation

**IMPLEMENTED — 2026-09-10**

The primary development workspace is `C:\Codex Room`, attached to the private GitHub repository `strigoi73-sudo/codex-room` on `main` with upstream `origin/main`. The canonical GitHub baseline was populated from known source bytes and mechanically matched against the local tree with Git blob hashes. Normal development uses the live repository, Git diffs/commits, and GitHub history rather than ZIP/Drive transfer snapshots.

Exact current HEAD, working-tree state, and active repository work are intentionally not maintained here; inspect Git/GitHub directly and use `06_DEVELOPMENT_CONTROL.md` for volatile coordination state.


## 3. Engineering-foundation tooling

### Reproducible development/test install

**IMPLEMENTED / VERIFIED — 2026-09-10**

`pyproject.toml` declares setuptools packaging for `codex_room` and its static assets, with test dependencies available through the `test` extra. `constraints-test.txt` records the known-good application/test dependency set used by routine development and CI while `pyproject.toml` retains broader supported ranges. A disposable clean environment successfully installed the project with:

`python -m pip install -c constraints-test.txt ".[test]"`

The canonical routine full-test command is:

`python -m pytest -q`

Clean-environment verification collected **129 tests** and completed successfully. The browser transcript check `test-transcript-stability.ps1` remains a specialized check rather than part of the routine Python suite because it requires Node.js plus Chrome or Edge. `uv` was not adopted because the existing pip/venv path was sufficient.

### Minimal GitHub CI

**IMPLEMENTED / VERIFIED — 2026-09-10**

`.github/workflows/python-tests.yml` runs on pushes to `main` and pull requests targeting `main`. It uses a single Ubuntu job with Python 3.12, read-only repository contents permission, installs through `constraints-test.txt`, and runs the canonical pytest command.

The dependency-constraint repair was hosted-verified on 2026-09-10: the merged `main` workflow installed the known-good `openai-codex==0.147.0` set and passed **129 tests, 2 warnings**. Exact run/commit evidence belongs in the Evidence Register or GitHub rather than this architecture summary.

### SDK-pinned Codex runtime selection

**IMPLEMENTED / VERIFIED — 2026-09-12**

`Start-Codex-Room.cmd` no longer supplies a desktop-app or version-directory Codex executable by default. When `CODEX_ROOM_CODEX_BIN` is unset, `CodexAgentAdapter` leaves `codex_bin` unset and the pinned `openai-codex==0.147.0` SDK selects its matching packaged `openai-codex-cli-bin==0.147.0` runtime. An explicit operator override remains supported and is validated for path existence by the launcher.

This boundary was repaired after a live smoke attempt using the desktop-app binary produced a completed turn without a usable final response followed by a persistent-thread `system-error`. The corrected launcher commit was hosted-verified with **137 passed, 2 warnings**. See E-029.

## 4. Core execution path

**IMPLEMENTED**

The working execution model remains approximately:

**event → delivery → per-agent worker → coalesced readable/runnable batch → persistent SDK thread → MESSAGE/PASS/FINISH decision → routing/settlement**

Persistent SDK threads remain a major context-cost driver; invocation frequency and persistent-context size are distinct operating-economics concerns.

## 5. Deterministic Room capability substrate

**IMPLEMENTED / VERIFIED end to end — 2026-09-12; P4.1 live invocation VERIFIED; P4.2 live registry discovery/invocation VERIFIED**

Codex Room owns a deterministic capability substrate without relying on the provider's experimental dynamic-tool API.

### Capability execution and safety

The first CORE capability remains `assert_file`, which performs read-only assertions against a Room-workspace-relative file: regular-file existence, SHA-256 equality, JSON validity, and required top-level JSON keys. Workspace resolution rejects absolute paths and traversal outside the Room workspace. Assertion failure is a normal factual result rather than an execution failure.

The agent chooses what should be asserted and interprets significance. Deterministic software computes exact facts; it does not replace agent judgment.

P4.1 live verification established the end-to-end execution path, including safe Windows shell-wrapper recognition and durable `deterministic_capability` telemetry. See E-030.

### Capability registry and discovery

P4.2 adds a static CORE registry and a common manifest model.

Each registered capability currently exposes:

- stable capability ID;
- description;
- origin and scope;
- explicit version;
- SHA-256 over the registered implementation components;
- typed input/output contracts;
- declared workspace/network/external-process permissions;
- side-effect declaration;
- verification metadata;
- inspect/invoke guidance.

Current command surface:

- `codex-room-cap list` — compact summaries only, intentionally avoiding full schemas to control model context cost;
- `codex-room-cap inspect CAPABILITY_ID` — detailed manifest;
- `codex-room-cap invoke CAPABILITY_ID --input-json JSON_OBJECT` — registered invocation;
- `codex-room-cap assert-file ...` — retained P4.1 compatibility alias.

The ordinary agent delivery instruction no longer names `assert_file`. It tells agents to consider deterministic software when inputs are explicit, outputs are objectively checkable, and fresh judgment is unnecessary for each execution; before ad hoc mechanical execution, agents check the registry and use an adequate registered capability when one exists, while retaining justified ad hoc fallback when the registry is inadequate or materially less suitable.

Adapter telemetry recognizes direct registry commands plus bounded Windows PowerShell/pwsh wrapper forms, while rejecting chained command forms. Registry list/inspect activity is recorded as `deterministic_capability_registry`; registered execution remains `deterministic_capability` and includes capability version and implementation hash when emitted by the registry. Structured invocation errors are also safely surfaced without exposing arbitrary command stdout/stderr.

P4.3a generalized durable invocation evidence for capabilities whose results are not shaped like `assert_file`. Each `CapabilitySpec` may declare `durable_result_fields`; registered invocation propagates that declaration, registry inspection exposes it, and the adapter persists only the common identity/status envelope plus those named result fields. Older capability results without a declaration retain the P4.1/P4.2 `subject` / `checks` compatibility path. Invalid declarations are not promoted, and declared evidence above **64 KiB** is replaced by explicit truncation metadata. PR #12 / E-032 verified this path with **167 tests, 2 warnings** on both the exact PR head and the merged canonical-main bytes.

P4.3b added registered CORE `find_files` version `1`. It scans only within the Room workspace, returns regular files only, never follows symlinks, fails visibly on traversal errors, supports deterministic include/exclude glob filtering plus hidden-file and exact size controls, and reports explicit truncation. One invocation returns 100 matches by default / 200 maximum, limits match evidence to 48 KiB, and stops after 100,000 scanned entries. Results are stable sorted depth-first path/size evidence with no write, network, or external-process permission. PR #13 / E-032 verified the exact PR head and merged canonical-main bytes with **186 tests, 2 warnings**.

P4.3c added registered CORE `search_text` version `1`. It performs literal single-line search over bounded UTF-8, NUL-free workspace text selected through the existing `find_files` path. Candidate count, match count, per-file bytes, aggregate bytes, transient excerpt bytes, and durable location bytes are all explicitly bounded. Runtime excerpts are available to the acting agent but deliberately excluded from durable Room telemetry; persistent evidence contains query SHA-256/length, exact locations, counts, limits, and truncation status. PR #14 / E-032 verified the exact PR head and merged canonical-main bytes with **216 tests, 2 warnings**.

P4.3d added registered CORE `compare_files` version `1`. It computes exact byte equality plus SHA-256 and sizes for two bounded workspace files. Small unequal UTF-8 text can additionally produce a bounded unified diff; binary, oversized, or line-heavy inputs still retain exact byte comparison with an explicit text-diff status. Diff content is transient and durable telemetry retains only identities, hashes, sizes, equality, and bounded diff metadata. PR #16 / E-032 verified the exact PR head and merged canonical-main bytes with **235 tests, 2 warnings**.

The initial P4.3 CORE library is complete and live-verified end to end: `assert_file`, `find_files`, `search_text`, and `compare_files`. A fresh post-PR-#17 Room whose prompt named no capability discovered and inspected all four manifests, then durably invoked all four through the registered path with matching version/implementation identities and correct structured evidence. C alone handled the mechanical work; A/B remained unconsumed; one malformed `find_files` input was surfaced as a structured error and corrected; C then FINISHed exactly `P4.3-LIBRARY-OK` and the one-turn Round closed normally. P4.3 is therefore **IMPLEMENTED / VERIFIED end to end — 2026-09-12**; see E-032.

The invocation registry remains static, but P4.4a now provides the first implemented custom-capability substrate. Room-local drafts are structurally validated from `.codex-room/capability-drafts/<id>/` using a deliberately narrow package-v1 shape: one exact JSON manifest plus one UTF-8 syntax-valid Python `capability.py` entrypoint. Custom IDs use a portable lowercase namespace; draft directory components and files reject symlinks; manifest/code sizes are bounded; unsupported extra package entries are rejected. The manifest binds lineage scope, Python/`stdio-json-v1` runtime, object input/output contracts with required boolean `ok`, durable-result fields, permission declarations, and side effects. Exact identity exposes manifest SHA-256, implementation SHA-256, and a domain-separated combined package SHA-256 over the exact bytes.

P4.4a deliberately does **not** make draft code registered or trusted for invocation. Permission declarations are represented separately from enforcement: package inspection reports `ambient_room_sandbox` and `per_capability_enforcement: false`. Registered custom code must never gain authority merely by becoming reusable, and Codex Room does not claim a per-capability OS sandbox that current source does not implement. PR #19 / E-033 verified the exact repaired PR head and merged canonical-main bytes with **261 tests, 2 warnings**.

P4.4b now adds deterministic verification and immutable publication without yet changing ordinary capability discovery. Exact draft code is copied into fresh bounded test workspaces and executed through Python isolated mode against 1–16 exact input/output cases under the caller's existing Room execution boundary. Fixtures, JSON inputs/expected outputs, runtime, and subprocess output are bounded; output floods are killed at the limit; stderr must remain quiet; results must exactly match expected JSON and exercise declared durable fields. The original draft is re-loaded/re-hashed after verification to detect mutation during the run. Verification receipts store only test identities/hashes, not raw fixture/input/output content.

Host-side P4.4b publication does not execute candidate code. It publishes only the verified exact `manifest.json` / `capability.py` bytes plus content-addressed verification and registration records beneath protected `data/custom-capabilities/`. Registration records bind Room ID, custom ID/version, package, manifest, implementation, and verification hashes. Same-exact publication is idempotent; conflicting/corrupt content-addressed material is rejected. PR #20 / E-034 verified the exact reviewed PR head and merged canonical-main bytes with **277 tests, 2 warnings**.

P4.4c now activates verified custom capabilities through a protected per-Room binding while preserving the existing registry vocabulary. Agent-side `codex-room-cap register` runs only the deterministic verifier inside the agent's existing `workspace_write` sandbox and emits a bounded self-hashed registration request. It does not write protected registry state. During lifecycle-valid turn settlement, `RoomRuntime` reparses that request on the host, re-checks the current exact draft against the receipt, publishes the immutable package / verification / registration objects, and writes one protected Room binding. Recovery recognizes an already-bound exact request before consulting mutable draft state, so replay remains idempotent.

Canonical Room workspaces now resolve CORE plus explicitly bound custom registrations through the same `list`, `inspect`, and `invoke` interface. Schema-v1 custom bindings are single-assignment per Room/capability ID; same-exact rebinding is idempotent, while conflicting versions and CORE/custom ID collisions fail visibly. Invocation loads and re-verifies the immutable published package, executes `capability.py` under the ambient caller/sandbox boundary, returns the standard capability envelope, and preserves implementation, package, registration, and verification SHA-256 identities. Durable telemetry retains only common provenance plus manifest-declared durable result fields. The earlier draft that attempted protected publication directly from the sandboxed command was rejected during exact-diff review before CI. PR #21 / E-035 verified the corrected exact PR head and merged canonical-main bytes with **291 tests, 2 warnings**.

P4.4d now supplies the agent behavior layer without making every turn pay for the full package schema. The always-loaded deterministic-capability instruction tells A/B/C to consider custom software only when the current registry is inadequate and reusable deterministic software is justified by reuse, reliability, provenance, or mechanical-complexity value. When that condition is met, agents load the detailed package/test-vector contract on demand with standalone `codex-room-cap authoring`. That reference is machine-readable and derives its numeric package/test limits from implementation constants; safe telemetry retains only its operation/schema identity. Agents are explicitly told that successful `register` means verification passed and host registration is pending until turn settlement, and that a later turn must rediscover the capability with `list` / `inspect` before invocation. PR #22 / E-036 verified the exact reviewed PR head and merged canonical-main bytes with **294 tests, 2 warnings**.

P4.4 is now **IMPLEMENTED / VERIFIED end to end**. In Room `room_857d95aa75c14dd0b939f43baf9a9e17`, C alone first discovered that no CORE capability covered the requested slug transformation, loaded the bounded authoring contract, created and verified `ascii_text_slug` against four exact cases, requested registration, and host settlement durably bound the exact package. The first reuse Round exposed a Windows inline-JSON quoting failure, which PR #23 repaired by adding bounded workspace-file invocation input while preserving inline compatibility. Exact PR head `2a32cd3e...` and merged canonical-main `4c10b60c...` both passed **297 tests, 2 warnings**.

A later repaired Round in the same Room then rediscovered the already-bound custom capability through normal `list` / `inspect`, with implementation/package/registration/verification identities matching the original registration, created one workspace input file, and invoked the normal registered capability successfully. Durable evidence recorded `ok:true`, `slug:"alpha-beta-99"`, and `length:13` under the same immutable implementation/package/registration/verification identities. A/B remained unconsumed, C FINISHed exactly `P4.4-CUSTOM-OK`, and the one-turn Round closed normally. P4.4 therefore demonstrates the full path from agent judgment through bounded custom authoring, verification, host binding, later rediscovery, and registered deterministic reuse.

P4.5a lineage binding inheritance is now **IMPLEMENTED / VERIFIED deterministically — 2026-09-13**. Original Room registrations and schema-v1 direct bindings remain immutable historical provenance. Rollover successors use schema-v2 inherited bindings containing the successor Room identity, the exact original registration SHA-256 and registration Room, plus the immediate predecessor Room and predecessor binding SHA-256. The loader resolves the original content-addressed registration/package/verification objects and validates the predecessor-binding chain, so a later generation continues to use the original registration while recording its immediate inheritance source.

The rollover saga creates inherited binding state from the predecessor's exact bound set under protected operation-scoped staging before successor finalization. Repeating the same operation validates and reuses the same binding bytes. Failure/abort removes staged and successor binding state; startup recovery revalidates/reconstructs inheritance for a fully provisioned pending successor before finalizing it and removes inherited state when an incomplete successor is aborted. A successor therefore receives all eligible lineage-scoped custom bindings deterministically without a newest-version lookup, republishing, re-verification, or synthetic registration.

Focused regression coverage proves exact registration/package/implementation/verification continuity, unchanged predecessor binding bytes, normal successor `list` / `inspect` / `invoke`, replay/idempotence, abort cleanup, restart finalization/cleanup, multiple inherited capabilities, false-predecessor rejection, and multi-generation origin/immediate-predecessor coherence. PR #24 exact head `888585749cbfe702080005d7211fbc79e758a7a7` and canonical-main merge `f1f83357b78399718ed8910f2849763c6c2dbbbb` both passed **301 tests, 2 warnings**; the squash-merge tree exactly matches the reviewed/tested PR-head tree. See E-039.

P4.5 remains **IN PROGRESS** pending a fresh live rollover proof. Personal/CORE promotion remains later work under D-022.

PRs #8–#11 established the registry/discovery path and then repaired two live-only integration gaps: agents initially preferred ad hoc mechanical execution, and later safe telemetry could miss capability commands exposed only through an outer PowerShell wrapper. Exact PR-head and merged-byte verification is recorded in E-031; the final code-bearing merged bytes passed **164 tests, 2 warnings** on rerun after one unrelated pre-existing timing flake.

Final live verification used a fresh Room whose prompt did not name any capability. C alone recorded registry `list` and `inspect`, created the file, surfaced one malformed-input invocation as a structured `invalid_request`, corrected it, then successfully invoked `assert_file` version `1` with matching implementation SHA-256 and all requested checks true before FINISHing exactly `P4.2-DISCOVERY-OK`. P4.2 is therefore verified end to end; see E-031.

## 6. Selective invocation and routing

**IMPLEMENTED / HISTORICALLY VERIFIED — 2026-09-09**

`AgentDecision` supports optional `invoke_targets` for MESSAGE outcomes.

Current semantics:

- explicit named targets make only those peers runnable;
- `["all"]` deliberately invokes all peers;
- omitted/null targets preserve legacy all-peer fan-out for compatibility;
- a targeted public message remains readable to authorized non-target peers;
- passive readable deliveries do not initiate turns; ordinary passive delivery remains non-runnable, while unread passive A/B MESSAGE material delivered to C participates in D-020's integration-before-closure barrier;
- a later legitimate trigger consumes earlier passive readable information in sequence order;
- passive information newer than the trigger remains pending;
- running agents retain serialized backlog behavior rather than receiving concurrent turns;
- private-message authorization remains unchanged.

Routing telemetry records readable recipients, runnable recipients, triggering/passive event IDs, batch IDs, usage, and avoided legacy fan-out.

Historical verification after the selective-invocation change: **111 passed, 2 warnings**, with SQLite `quick_check` OK. A real Room exercise used **5 purposeful invocations** while avoiding **4 legacy fan-out invocations**.

**Monitor:** selective targeting may reduce spontaneous peer challenge if agents under-invoke useful reviewers.

## 7. Delivery coalescing

**IMPLEMENTED and worth preserving**

`claim_next_batch()` continues to coalesce multiple pending conversational deliveries into one invocation when appropriate. Selective invocation was designed to preserve this behavior rather than convert delivery into one-event/one-model-call execution.

## 8. Persistent threads and context management

**IMPLEMENTED**

Agents use persistent SDK threads. Context growth can make later invocations much more expensive than early ones.

### Proactive compaction race repair

**HISTORICALLY VERIFIED**

The earlier repair requires positive persisted `contextCompaction` evidence plus idle thread state before treating compaction as complete, with idle-state preflight before a new turn.

### Post-compaction growth baseline

**IMPLEMENTED / HISTORICALLY VERIFIED — 2026-09-09**

The former baseline-ratchet hypothesis was confirmed and repaired.

Current behavior:

1. successful compaction persists `growth_baseline_state = "pending"`;
2. the first later successful authoritative `usage.last.input_tokens` measurement establishes the growth baseline and its batch ID;
3. that establishment turn cannot itself trigger another compaction;
4. later eligibility requires both the context-ratio threshold and at least 25,000 tokens of growth from the established post-compaction baseline;
5. a later successful compaction resets the state to pending;
6. legacy checkpoints without the new fields are treated as pending rather than reusing a pre-compaction baseline.

Historical verification: **119 passed**, with SQLite `quick_check` OK.

## 9. Retry / Agent Error observability

**IMPLEMENTED / HISTORICALLY VERIFIED — 2026-09-09**

Retryable agent failures are exposed as interrupted attempts rather than immediately as terminal Agent Errors. A later correlated success records recovery; terminal Agent Error is reserved for exhausted or non-recoverable failure. Reconciliation avoids false recovery under stop, stale-generation, or quarantine conditions.

Historical verification: focused and browser/UI checks passed; full suite **116 passed, 2 warnings**, SQLite `quick_check` OK.

## 10. Usage-wall delayed continuation

**IMPLEMENTED / VERIFIED — 2026-09-12**

A positively identified Codex usage wall with a parseable terminal “try again at” time schedules durable continuation work for the same agent/thread at:

**reported retry time + 60 seconds**

The implementation persists continuation state, survives restart, releases due work through the normal serialized queue, supports one-use same-thread rebind for usage-induced `systemError`, replaces the schedule on repeated usage walls, and cancels stale continuations under stop/lifecycle changes.

Historical implementation verification included **10 focused tests**, a **127-test** full suite, and database-integrity checks. A2 then re-reviewed the current exact source and mapped the current usage-wall continuation tests to the lifecycle/thread-bound transactional implementation. The current runtime/test bytes are also covered by the later canonical `main` full-suite result of **136 passed, 2 warnings**. The former exact-byte review caveat is therefore retired.

## 11. Exact-turn completion, observer stability, and rollover

### Exact-turn completion + inactivity lease

**HISTORICALLY VERIFIED**

Durable `agent_executions`, exact turn identifiers, reconciliation, restart safety, quarantine behavior, idempotent settlement/routing, and a progress-sensitive inactivity lease were historically verified. Historical full-suite result: **69 passed, 0 failed, 0 skipped**.

### Observer stability

**HISTORICALLY VERIFIED / practically tested**

The observer blanking/rescrolling repair used keyed reconciliation, stable IDs, status-only chrome, reconnect merge behavior, and reader anchoring/follow behavior. Practical user testing succeeded at the time.

### Rollover and institutional continuity

**IMPLEMENTED as of the reviewed successor rollover**

Reviewed rollover behavior created a sealed predecessor, reciprocal lineage, and fresh successor SDK threads without carrying predecessor transcript/private prompts/hidden context/deliveries/executions/compaction state into the successor. Explicitly promoted institutional material remained separately bindable through the institutional release mechanism.

## 12. Bounded live snapshots and complete Room exports

**IMPLEMENTED / VERIFIED — 2026-09-11**

Room state reads now distinguish bounded live-history views from complete exports. `Database.get_events()` keeps a default limit of 2,000 but returns the **newest** events while preserving ascending sequence order in the returned window. `Database.snapshot()` exposes `event_window` metadata with the configured limit, total event count, returned count, truncation flag, and first/last returned sequence numbers.

The export route explicitly requests `event_limit=None`, so JSON and Markdown exports materialize the complete Room event history rather than inheriting the live 2,000-event window. Regression coverage exercises a Room above the window size and verifies both the latest-event live snapshot and full-history export.

Hosted verification for the merged repair passed **130 tests, 2 warnings** on canonical `main`. Exact commit/run evidence is recorded in the Evidence Register.

**Operational note:** complete exports intentionally scale with total Room history; later scalability work may revisit streaming/pagination if demonstrated Room sizes make full materialization expensive.

## 13. Permanent Personal triad and integration-before-closure

**IMPLEMENTED / VERIFIED — 2026-09-12**

D-020 aligned Personal runtime behavior with the settled three-agent production architecture.

Current behavior:

- every new Personal Room is created with A — Implementer, B — Verifier, and C — Integrator, each on a distinct persistent SDK thread;
- C is the default starter for new Rooms, prepared Rounds without an explicit starter, new-topic compatibility flow, and rollover successor Rooms; explicit A, B, C, or `either` starts remain available where deliberately requested;
- historical A/B Rooms remain valid and are not silently upgraded; the explicit legacy upgrade path adds a fresh C while preserving A/B identities and pre-join history boundaries;
- rollover from a historical A/B predecessor creates a new triad successor and records that C was added in successor lineage metadata;
- A and B may route MESSAGE outcomes directly to each other. Public peer messages remain readable to authorized non-target peers, so C can accumulate passive A/B context without a model invocation;
- settlement follows actual engagement in triad Rooms, allowing C to solve a task without forcing unused A/B turns;
- if C has unread passive A/B `agent_message` deliveries when a Round would otherwise close, the runtime creates one durable runnable `integration_required` event for C. C consumes that trigger together with the pending passive peer material through normal ordered batch coalescing;
- an already-open or running C turn counts as an integration opportunity; the barrier does not create a second simultaneous C invocation;
- the integration trigger survives restart through ordinary durable deliveries, and inactivity closure now respects any open delivery so it cannot race a pending integration turn;
- after integration, C may finish, synthesize, or redelegate. Coordination responsibility does not give C superior judgment over A or B.

Verification evidence is recorded in E-027. On the exact reviewed PR head, GitHub Actions passed **136 tests, 2 warnings** and the specialized local Playwright suite passed **3 tests**. The squash-merge commit on `main` has the same Git tree as the reviewed/tested PR head.

A fresh live Personal Room exercise on 2026-09-12 subsequently demonstrated the intended C→A→C→A→B→C coordination path, including selective invocation, passive readability, one mechanical `integration_required` wake, and final engaged-participant settlement. That exercise also exposed an older exact built-in A/B/C profile generation still persisted in the local database.

Current startup migration therefore includes a separate `triad_profiles_v2` exact-hash migration for the observed early-triad A/B/C built-ins. Only matching default rows and matching non-archived, unsealed, default-profile Room snapshots with no Room override are replaced with current profile text. Non-matching custom content, Room overrides, archived Rooms, and sealed predecessors are preserved. PR #4 and canonical `main` both passed **138 tests, 2 warnings**. A fresh post-repair local Room export then verified that all three participants inherited the current D-020 profiles. The same Room also verified C-only settlement: C was the sole invoked/consuming participant and the Round closed after one C FINISH. See E-029.

### Agent identity, protected structure, and replaceable personality

**IMPLEMENTED / VERIFIED deterministically — through 2026-09-14**

Agent developer instructions are now composed from separate layers rather than treating the editable profile as the entire developer prompt:

1. protected shared institutional identity and peer rules;
2. protected agent-specific structural responsibilities;
3. one replaceable personality layer;
4. protected Room protocol.

A and B currently have no special protected structural role beyond the shared peer/institutional layer. C's protected structural layer carries the ordinary Personal organizer/coordination responsibility: initial organizational contact, selective allocation of peer cognition, integration of substantive delegated work, preservation of material disagreement, and no superior judgment over A/B.

Default profile rows now store the personality body for each slot. When a new Room is created, the runtime composes the protected layers around either the saved default personality or a Room-specific personality override. An override **replaces** the selected default personality; the old additive `profile + ROOM-SPECIFIC OVERRIDE` composition is no longer used for new Rooms. A/B/C all support Room personality overrides, including C.

The migration converts only exact known built-in defaults to the current personality-only default rows. This includes the earlier full-prompt built-ins, the exact role-derived personality-only defaults, and the exact V3, V4, and V5 default personality bodies. Non-matching custom default content is preserved deliberately, and existing Room snapshots/effective instructions are not silently rewritten. Normal triad rollover continues to carry the exact predecessor agent configuration forward; the legacy add-C path composes C's protected structural/protocol layers around the selected C personality.

The active standard default personalities remain general-purpose cognitive temperaments rather than occupational roles. V6.2 uses persistent asymmetric cognitive contracts whose centers of gravity are intended to remain active through exploration, evaluation, narrowing, recommendation, and peer follow-up:

- **Agent A — exploratory / generative:** "**What else could we do?**" A must actively expand and improve the option space before local diagnosis or final recommendation, then narrow in terms of leverage, reversibility, optionality, useful learning, combinations, and changed tradeoffs.
- **Agent B — skeptical / discriminating:** "**What are we justified in believing?**" B must establish what is actually supported before accepting diagnosis, causal story, prediction, or solution, then keep epistemic justification central through evaluation and recommendation.
- **Agent C — contextual / relational:** "**How do the consequential parts fit together and behave?**" C must identify load-bearing objectives, dependencies, constraints, bottlenecks, interactions, sequencing, and consequences before local diagnosis, then keep relational/system structure central through recommendation.

The B/C boundary is explicit in the personality layer: B's primary concern is whether a proposition, inference, diagnosis, or prediction deserves belief; C's primary concern is how provisionally usable elements relate and what those relationships cause or constrain. All three personalities include characteristic anti-duplication behavior that moves the frontier of existing work plus stopping rules against their expected failure modes. C is explicitly instructed to preserve genuine unresolved conflict rather than hide it inside a compromise.

C's organizer/coordination responsibility remains only in the protected structural layer, not in C's personality. The former Implementer / Verifier / Integrator occupational labels remain retired.

Composition verification is recorded in E-041. V3 implementation/evaluation is recorded in E-042/E-043; V4 implementation and its failed café calibration gate in E-044/E-045; V5 implementation and its failed café calibration gate in E-046/E-047. Both V4 and V5 produced materially different later texture while still converging on substantially the same opening margin-versus-demand diagnosis in the controlled café scenario.

V6.2 deterministic implementation is recorded in E-048. PR #36 exact head `8ecfd73104638b49975a6bf134cc3dde16f35468` and canonical-main squash merge `6d89465de2bf581a8bce2e44ce569beea224f3df` share Git tree `bc2590ddc11682d51ecf3cb79221259f7acd59ea`. GitHub Actions PR run `34870235815` and canonical-main run `34870432154` both passed **313 tests, 2 warnings**. V6.2 behavioral differentiation is **not yet verified**; the next evidence step is one fresh café rerun under the established independent controls before deciding whether to resume the remaining scenarios and blind evaluation.

## 14. Runtime-state and work-queue caution

Current priorities, maintenance issues, blockers, and open questions are owned by `06_DEVELOPMENT_CONTROL.md` and are intentionally not duplicated in this architecture synthesis.

Fresh live Personal Room exports were captured on 2026-09-12 and are recorded in E-029. They provide current runtime evidence for D-020 selective coordination, integration-before-closure, C-only engaged-participant settlement, SDK-pinned runtime operation, and successful local adoption of the repaired A/B/C built-in profiles. Older Room-error snapshots remain historical evidence only.
