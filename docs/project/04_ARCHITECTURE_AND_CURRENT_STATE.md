# Codex Room — Architecture & Current State

**Last synthesized:** 2026-09-14  
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

`pyproject.toml` declares setuptools packaging for `codex_room` and its static assets, requires Python 3.11+, and exposes test dependencies through the `test` extra. `constraints-test.txt` records the known-good application/test dependency set used by routine development and CI while `pyproject.toml` retains broader supported dependency ranges. A disposable clean environment successfully installed the project with:

`python -m pip install -c constraints-test.txt ".[test]"`

The canonical routine full-test command is:

`python -m pytest -q`

Clean-environment verification collected **129 tests** and completed successfully. The browser transcript check `test-transcript-stability.ps1` remains separate from the canonical Python command because it requires Node.js plus Chrome or Edge; I-011 now runs it automatically in the hosted Windows lane with pinned `@playwright/test@1.63.0`. `uv` was not adopted because the existing pip/venv path was sufficient.

### Local deterministic verification and historical hosted assurance

**IMPLEMENTED / HISTORICALLY VERIFIED — local verifier introduced 2026-09-16**

Routine repository verification now uses `verify-fast.cmd` and `verify-full.cmd`, backed by `verify-local.ps1`. Fast mode exercises the focused Linux/Python 3.12 core set, Windows dependency/portability checks, and browser transcript stability. Full mode runs complete Linux/Python 3.12 and 3.11 pytest, complete Windows pytest, browser transcript stability, and the pinned dependency audit. Cached verification environments and dependency synchronization keep the routine fast path materially cheaper than the earlier exhaustive Windows-first process.

The previous GitHub Actions verification/dependency workflows were removed from `main` on 2026-09-16 after repeated pre-runner startup failures made them unreliable as the routine path. Earlier hosted runs remain historical exact-version evidence, including the I-011 portability finding and E-088 verification. GitHub continues to provide canonical history/review; routine mechanical verification is local and deliberate under amended D-018. See E-109.

### SDK-pinned Codex runtime selection

**IMPLEMENTED / VERIFIED — 2026-09-12**

`Start-Codex-Room.cmd` no longer supplies a desktop-app or version-directory Codex executable by default. When `CODEX_ROOM_CODEX_BIN` is unset, `CodexAgentAdapter` leaves `codex_bin` unset and the pinned `openai-codex==0.147.0` SDK selects its matching packaged `openai-codex-cli-bin==0.147.0` runtime. An explicit operator override remains supported and is validated for path existence by the launcher.

This boundary was repaired after a live smoke attempt using the desktop-app binary produced a completed turn without a usable final response followed by a persistent-thread `system-error`. The corrected launcher commit was hosted-verified with **137 passed, 2 warnings**. See E-029.

## 4. Core execution path

**IMPLEMENTED**

The working execution model remains approximately:

**event → delivery → per-agent worker → coalesced readable/runnable batch or transaction Assignment → selected provider context → model decision → routing/settlement**

Provider context is now policy-selected. `persistent_agent_thread` remains the ordinary/default transport, preserving the established per-agent SDK thread. Opt-in work-model-v2 Rounds may instead use `assignment_thread`, where one logical Assignment owns one durable provider thread across its continuations and different Assignments do not inherit provider history merely because they share the same persistent A/B/C identity. Invocation frequency and active-provider-context size therefore remain distinct operating-economics concerns.

## 5. Deterministic Room capability substrate

**IMPLEMENTED / VERIFIED end to end through P4.5 — 2026-09-13**

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

D-029/I-012 introduced the static CORE `inspect_source` capability so a running Personal Room can retrieve relevant evidence without receiving cross-boundary mutation authority. Its confinement remains unchanged: an explicit maintained-CORE allowlist plus another canonical Room's `shared` workspace; `data/`, environment-private files, Git internals, credentials/secrets, arbitrary host paths, traversal, and symlink/reparse escapes remain outside the readable surface, and no cross-boundary write mechanism exists. E-078/E-079 verify the original boundary and live deployed behavior.

I-014 advances `inspect_source` to version `2` to address demonstrated tool-loop/context amplification without broadening authority. It adds bounded `search_many` (up to 16 known literal queries in one source scan) and `read_many` (up to 16 bounded text ranges under one shared 128-KiB output ceiling), plus a JSON-free `codex-room-cap source ...` CLI that translates into the same registered handler. The adapter recognizes this direct CLI as ordinary deterministic-capability telemetry, including structured failures, while raw search excerpts/read content remain transient. Protected participant instructions use the direct source surface for normal `inspect_source` work and make one `search-many` followed by one `read-many` the normal pattern when several lookups are already known, with further retrieval reserved for a specific unresolved dependency. PR #77 additionally lets search/search-many target an explicit regular file as well as a directory while preserving the original CORE/cross-Room confinement, link/reparse rejection, output bounds, and no-write boundary.

Each settled execution emits one mechanical/status `execution_economics` record from existing usage/activity facts. Provider usage counters are cumulative on a persistent SDK thread, so PR #77 retains those cumulative fields as metadata but computes the visible execution-token count and tokens-per-tool-call from the immediately prior durable usage snapshot on that same SDK thread. If a prior snapshot is missing or comparable counters decrease, the delta is explicitly unavailable/non-monotonic rather than inferred. E-081 records the original motivating evidence; E-090 records the ordinary-use recurrence and the verified PR #77 follow-up. Exact PR #77 head `2d898aacecd274962a57cf39b32c983538d403fb` and squash merge `7d930127212b94580c6309032b83d654d032570e` share Git tree `e3a5e382712ac64e23f7abe9e5bc25cf2dfa3a10`; both PR and canonical-main hosted verification passed **376 tests, 2 warnings** on all three Python lanes plus **3 browser tests** on Windows.

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

P4.5 is **COMPLETE / IMPLEMENTED / VERIFIED end to end**. E-040 records the fresh live rollover proof: a newly registered lineage capability survived an actual Room rollover, remained discoverable/inspectable/invokable in the successor at the exact inherited version and provenance, and left the predecessor binding unchanged. Personal/CORE promotion remains later work under D-022.

PRs #8–#11 established the registry/discovery path and then repaired two live-only integration gaps: agents initially preferred ad hoc mechanical execution, and later safe telemetry could miss capability commands exposed only through an outer PowerShell wrapper. Exact PR-head and merged-byte verification is recorded in E-031; the final code-bearing merged bytes passed **164 tests, 2 warnings** on rerun after one unrelated pre-existing timing flake.

Final live verification used a fresh Room whose prompt did not name any capability. C alone recorded registry `list` and `inspect`, created the file, surfaced one malformed-input invocation as a structured `invalid_request`, corrected it, then successfully invoked `assert_file` version `1` with matching implementation SHA-256 and all requested checks true before FINISHing exactly `P4.2-DISCOVERY-OK`. P4.2 is therefore verified end to end; see E-031.

## 6. Selective invocation and routing

**IMPLEMENTED / VERIFIED — delegation-cohort timing updated 2026-09-14**

`AgentDecision` supports optional `invoke_targets` for MESSAGE outcomes.

Current semantics:

- explicit named targets make only those peers runnable;
- `["all"]` deliberately invokes all peers;
- omitted/null targets preserve legacy all-peer fan-out for compatibility;
- a targeted public message remains readable to authorized non-target peers;
- passive readable deliveries do not initiate turns; ordinary passive delivery remains non-runnable, while unread passive A/B MESSAGE material delivered to C participates in D-020's integration-before-closure barrier;
- a later legitimate trigger consumes earlier passive readable information in sequence order; the delivery prompt preserves that coalescing but labels the runnable event(s) as `triggering` and earlier non-runnable material as `passive_context`, so historical cross-reading is not presented as the current assignment;
- passive information newer than the trigger remains pending;
- running agents retain serialized backlog behavior rather than receiving concurrent turns;
- private-message authorization remains unchanged.

D-020 now also has a narrow **C delegation-cohort timing rule**. When one C MESSAGE invokes multiple peers, a peer MESSAGE return addressed to C remains readable but temporarily non-runnable until every peer invoked by that same C event has settled its delegated turn. CORE then creates one durable `delegation_cohort_settled` trigger. C's next claim coalesces the accumulated passive returns plus that trigger. Single-peer delegation remains immediate. Deferred C deliveries remain part of causal MESSAGE settlement, so C's later terminal reaction can settle those peer boundaries normally.

This is not a general join primitive: the cohort is the exact runnable-recipient set of one C delegation event, unrelated work is not globally blocked, and the observer can still see each public peer return as it arrives.

Routing telemetry records readable recipients, requested/immediate/deferred runnable recipients where applicable, triggering/passive event IDs, delegation-cohort identity, batch IDs, usage, and avoided legacy fan-out.

Historical verification after the original selective-invocation change: **111 passed, 2 warnings**, with SQLite `quick_check` OK. The 2026-09-14 cohort-timing repair is verified by E-054: PR-head and canonical-main exact-tree runs both passed **317 tests, 2 warnings**.

**Live verification:** E-055 confirmed the delegation-cohort timing behavior in a fresh Room: the first peer return remained passive to C, the second peer return completed the cohort, one cohort-settled trigger made C runnable, and C integrated both returns in one batch before normal causal closure. Multi-peer cohort batching intentionally trades first-return responsiveness for one coherent C integration turn.

## 7. Delivery coalescing

**IMPLEMENTED and worth preserving**

`claim_next_batch()` continues to coalesce multiple pending conversational deliveries into one invocation when appropriate. The C delegation-cohort barrier deliberately uses this existing behavior: peer returns stay passive until the cohort-settled trigger makes C runnable, allowing the complete return set to be consumed in one batch rather than one model call per completion.

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

**IMPLEMENTED / VERIFIED**

The observer blanking/rescrolling repair used keyed reconciliation, stable IDs, status-only chrome, reconnect merge behavior, and reader anchoring/follow behavior. Practical user testing succeeded at the time.

PR #76 adds two bounded observer-information improvements without changing Room semantics: the Room header displays the persistent Room ID beside the title context, and each participant card displays the model/reasoning effort from the currently open durable execution or, when idle, the most recent durable execution that recorded a model. This reuses `agent_executions`; no second model-state store or schema migration was introduced. A focused regression verifies the card payload transitions from `model_recency="current"` during a blocked turn to `model_recency="last"` after settlement. See E-089.

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

**IMPLEMENTED / VERIFIED — through 2026-09-14**

D-020 aligned Personal runtime behavior with the settled three-agent production architecture; later D-024 through D-027 refine startup cognition, temporary framing, differentiated peer allocation, and invocation economy without changing the permanent triad.

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

A and B currently have no special protected structural role beyond the shared peer/institutional layer. C's protected structural layer carries the ordinary Personal organizer/coordination responsibility: initial organizational contact, selective allocation of peer cognition, integration of substantive delegated work, preservation of material disagreement, and no superior judgment over A/B. Under D-025, that coordination discretion includes temporary cognitive framing: C may assign A/B task-specific postures, perspectives, scopes, constraints, evidence standards, expected deliverables, or temporary roles/personas. Under D-026, peer allocation is explicitly economic: C should use the fewest peers that can add sufficient value, and if both A and B are invoked in the same delegation their cognitive responsibilities must be meaningfully differentiated along a substantive dimension expected to create complementary value. Cosmetic labels and substantially duplicate analyses do not satisfy the rule; even independent verification should differentiate method or responsibility. D-027 generalizes invocation economy to every participant through the protected Room protocol: `invoke_targets` requests immediate cognition rather than visibility, public readability does not require runnable delivery, and `invoke_targets: []` explicitly publishes a MESSAGE with no runnable peers while `null` retains legacy all-peer fanout. A peer completing bounded work for C should normally return to C without waking the other delegated peer unless that peer's additional cognition is materially needed. These frames and routing choices do not change persistent identities or peer standing, and A/B remain free to challenge the frame or reach any conclusion supported by their own judgment. After CG1 exposed premature semantic finalization, the protected C layer also requires explicitly necessary multi-peer delegation to remain provisional until all requested contributions have returned, declined, failed, or been judged unnecessary; only then should C present the final recommendation or FINISH. These are coordination-instruction rules, not a deterministic join or posture registry.

Default profile rows now store the personality body for each slot. When a new Room is created, the runtime composes the protected layers around either the saved default personality or a Room-specific personality override. An override **replaces** the selected default personality; the old additive `profile + ROOM-SPECIFIC OVERRIDE` composition is no longer used for new Rooms. A/B/C all support Room personality overrides, including C.

The migration converts only exact known built-in defaults to the current default profile rows. This includes the earlier full-prompt built-ins, the exact role-derived defaults, and the exact V3, V4, V5, V6.2, V7, and E-056 personality bodies. Those known built-ins now migrate to the empty neutral default. Non-matching custom default content is preserved deliberately, and existing Room snapshots/effective instructions are not silently rewritten. Normal triad rollover continues to carry the exact predecessor agent configuration forward; the legacy add-C path composes C's protected structural/protocol layers around the selected optional profile body.

The active standard startup profile is now **neutral** under D-024. A/B/C receive no distinguishing default personality, temperament, occupational role, intellectual specialty, or stylistic posture. Their standard default profile bodies are empty, so fresh Rooms compose no `PERSONALITY` section unless explicit profile text or a Room-specific override is supplied.

All participants still receive the protected shared institutional identity/peer layer and Room protocol. C additionally receives its protected organizer/coordination structural layer; that structural responsibility is not personality and grants no superior judgment over A/B. A and B have no special protected structural role beyond the shared institutional layer.

Optional profile content remains replaceable and Room-specific overrides still replace the selected saved profile body. Thus the composition model survives, but neutral startup is the standard: persistent identity supplies continuity, protected structure supplies institutional behavior, and task/Room context supplies any specialization actually needed.

The migration recognizes exact known built-in defaults through E-056 and converts those standard built-ins to the empty neutral profile while preserving non-matching custom profile text and existing Room snapshots/effective instructions. Normal triad rollover continues to carry the exact predecessor agent configuration forward.

E-057 established that task/fictional role dominated blind personality recognition. D-024 resolves the resulting product question by removing startup differentiation rather than continuing calibration. E-058 records the neutral-default implementation and verification: PR #49 tested head `2627fbd35b14214988a1828f788adb02163b03f8` and squash merge `833d3498c75fe4d7e2a3e76efda362b421341431` share Git tree `be52f9a92655ce28f6c3655fc39f1b72922d7d39`; PR run `34901569309` and canonical-main run `34901711440` both passed **321 tests, 2 warnings**. D-025 then makes task-specific differentiation an explicit part of C's protected coordination discretion through natural-language delegation rather than persistent startup profiles. E-059 verifies that protected-instruction implementation on PR #51 / merge `36eafaadd7b7a162ca7d4e8195e90f9498da0b21`, with exact tested/merged tree `dfcc00c242acedb7c0ce5b52276a1784bc103e76`; the PR suite passed **322 tests, 2 warnings**, and canonical main passed the same suite on rerun after one recorded intermittent pre-existing timing-test failure on the first attempt. E-060 then records the first live D-025 allocation test: C correctly coordinated a dual-peer cohort but gave A and B substantially the same analysis, producing strongly convergent recommendations. D-026 responds by making dual-peer differentiation mandatory and peer-count economy explicit. E-061 verifies the implementation on PR #53 / merge `057d5e2ca67356c6dfa642fb1c6bad6e5b71634e`; tested and merged tree `c8e635761d4d7aaf5fe619a90e8e86da86dd85cb` matched exactly, and both PR-head and canonical-main suites passed **322 tests, 2 warnings**. E-062 then live-verifies D-026 in a clean household-move Room: C assigned A the operating-workflow/tooling problem and B the AI-judgment/risk problem, and both produced complementary work. The same trace exposed a separate peer-routing inefficiency when B made A runnable after posting an already-public return, causing an extra A review and C reopen; D-027 addresses that broader invocation-economy gap. E-063 verifies D-027 on PR #55 / merge `18337b2c678bdf258f84591b6f9443e969c65d1c`: corrected tested and merged tree `da51b39fb0f18d66f062470e50652a76572243a7` matched exactly, and corrected PR-head plus canonical-main suites both passed **324 tests, 2 warnings**.

The Implementer / Verifier / Integrator names remain persistent organizational labels, but their former use as startup occupational/cognitive personality contracts is retired.

Composition verification is recorded in E-041. V3 implementation/evaluation is recorded in E-042/E-043; V4 implementation and its failed café calibration gate in E-044/E-045; V5 implementation and its failed café calibration gate in E-046/E-047. V6.2 implementation is recorded in E-048 and its behavioral failure against the pre-set complementarity criterion in E-049. V6.2 showed real improvement in the café scenario but converged too strongly in AI tutoring and manuscript revision, making the 3-of-4 target unreachable after S3.

V7 deterministic implementation is recorded in E-050, and its same-task AI-tutoring admission failure in E-051 established that explicit work-product prose did not reliably override shared-model convergence. CG1 / E-052 then showed that bounded task allocation can create genuinely different cognitive work even when the underlying model is shared. E-056 records the resulting D-023 refinement: the V7 work-product burden is removed, exact V7 built-ins migrate conservatively, and the active defaults are temperament-only generalists. PR #46 corrected head `20fa1b135426842bba1c65483cbb587b5db5c6fb` and squash merge `d83e2b6eca09477e255ea0033843c5834e64e4e1` share Git tree `343c68687675825e69f9c9d3300db6b044e7d9a5`; corrected PR run `34892520515` and canonical-main run `34892673292` both passed **319 tests, 2 warnings**. E-057 then tested live character recognizability through independently blinded role-play transcripts and found the observable signal dominated by fictional/task roles: **1/9** individual identities correct and **0/3** complete trios. The personality implementation remains active, but further calibration is MONITOR / DEFERRED; recognizability is not an established acceptance criterion.

## 14. Runtime provenance and maintenance health

**IMPLEMENTED / VERIFIED / LIVE VERIFIED — 2026-09-15**

The runtime now exposes a bounded deterministic health/provenance surface rather than requiring repository/process inference for ordinary live-version questions. `/api/health` reports application/source provenance captured for the running process, including the package version, Git revision and source-dirty state when available, a SHA-256 fingerprint over the relevant source/package bytes, Python version, installed `openai-codex` version, and the configured Room model/reasoning-effort policy.

Maintenance watchdog cycles retain process-local health facts: last cycle start/success, last unexpected error/time, cumulative failure count, consecutive failures, and an explicit `starting` / `healthy` / `degraded` state. A successful later cycle clears current degradation while preserving the prior error and cumulative count for the lifetime of the process.

Durable `agent_executions` rows now persist the model and reasoning effort at execution claim time beside the existing SDK usage JSON. Existing open pre-I-009 executions are filled when reclaimed. This provides execution-level policy/usage evidence for the subsequent P1 model-economy investigation without introducing a general metrics platform or automatic model routing.

E-068 records PR #58 and canonical-main verification. The exact code-bearing canonical commit passed **327 tests, 2 warnings**. E-069 then verified the principal's local Windows runtime after pull/restart: it reported exact canonical revision `6168c80938c7e9172a86651d3a9953fb66c2e219`, clean source, Python 3.12.10, `openai-codex` 0.147.0, Terra/high policy, and a healthy watchdog with zero failures. Git provenance fields may be unavailable outside a Git checkout; the source fingerprint remains the deterministic byte-level fallback. Watchdog error history is intentionally process-scoped rather than a cross-restart incident log.

P1 now also has a bounded adaptive execution mechanism, verified in E-075. The Room's compatibility/default policy remains Terra/high, including C's own turns. When C explicitly invokes A or B, C may attach one admitted execution configuration — Luna/medium, Terra/medium, Terra/high, or Sol/medium — for that peer's claimed execution. The claim persists the resolved exact model and reasoning effort in the existing `agent_executions` row before the SDK turn runs, so recovery and usage evidence remain exact-execution scoped. A/B do not directly control model selection; they may return an escalation request to C, which can redelegate with stronger cognition. Unspecified selections fall back to Terra/high. Under D-028, Astra is a hard-prohibited Room execution model: it is absent from the selectable configuration schema and the runtime fails closed if an execution path attempts to start a `gpt-6-astra` turn. E-076 records exact-head and canonical-main GitHub verification of that enforcement through PR #61. This is an implemented P1 experimental coordination capability, **not** an automatic model router or a settled production model-selection policy. PR #60 exact head `f0736b3f79f5274781a2d7dda3e26d942775e153` and canonical merge `ebbacb212b8d6c26b69a8fd2acb0959dcff26b42` both passed **329 tests, 2 warnings**.

E-080 exposed a separate provider-runtime cognition path that is not part of this Room allocation mechanism: Codex 0.154's ambient internal multi-agent tools can spawn SDK subagents inside a participant turn. In the I-010 Room, C used that path while later describing the work as persistent A/B allocations; the Room export contained no A/B turns or peer execution configs. I-013 therefore disables both `agents.enabled` and `features.multi_agent_v2.enabled` in Codex Room's app-server configuration so production cognition remains attributable to persistent Room A/B/C and the existing execution-accounting path. PR #63 final head `830bbfec06d3f90463a4e07c214e780bb7ca3c23` and canonical merge `8ed3df777ed24a8192b48e43f652f4736921fe2c` carry the same Git tree; both hosted runs passed **341 tests, 2 warnings**. I-013 is therefore verified on canonical `main`; recurrence is monitored through ordinary useful Rooms rather than a dedicated paid smoke.

E-082 adds a separate read-only local operating-economics instrument for ordinary Codex Desktop/CLI sessions. `codex_room/codex_usage.py` reads the provider runtime's persisted rollout `token_count` events, reports cumulative/last usage and per-user-turn cumulative deltas, and intentionally excludes prompt/response text. The root `codex-usage.cmd` wrapper makes this available through the normal Windows repository environment. This creates a deterministic bridge for future useful Codex-vs-Room comparisons without adding model calls or changing Room execution policy.

## 15. Persistent-data operational maintenance

**IMPLEMENTED / VERIFIED — 2026-09-15**

Codex Room now has a bounded offline operator maintenance path for its persistent data root. `codex_room/maintenance.py` and the Windows wrapper `codex-room-maint.cmd` provide four operations: current-state integrity `check`, coherent `backup`, backup `verify`, and guarded `restore`.

Current-data operations are deliberately offline in v1. The operator must stop Codex Room and explicitly supply `--offline-confirmed` for `check`, `backup`, and `restore`. This is an operator assertion rather than process detection or a runtime lock protocol. Backup-archive verification is read-only with respect to live Room state and does not require the offline flag.

Backups use SQLite's native backup API for `data/codex-room.db` rather than raw file copying, then copy the remaining durable data-root payload while excluding recursive backup archives and SQLite WAL/SHM sidecars. A root `manifest.json` records every payload path, size, and SHA-256. Verification requires exact manifest/payload agreement, safe relative paths, regular non-reparse files/directories, valid hashes/sizes, and healthy SQLite `quick_check` / foreign-key checks.

Restore is deliberately destructive and therefore requires both `--offline-confirmed` and `--confirm-replace-data`. It verifies the selected archive before touching current data, stages a complete candidate tree, preserves the existing backup collection, checks the candidate, moves the old data root to a sibling rollback path, and only then swaps the candidate into place. A failed final swap restores the prior root through the rollback path. No cloud backup, scheduler, retention service, dashboard, agent-callable restore, installation UUID, or formal SQLite schema-version contract is implied.

PR #73 / E-087 provide exact implementation and verification evidence. Final PR head `136eeec8755922023618c8a13c644155d01ae63b` and canonical merge `e22dd9a51c8f803bda1cce0ae658c30b2f383056` share the tested tree; both hosted suites passed **369 tests, 2 warnings**.

## 16. I-015 Stage A transaction coordination kernel

**IMPLEMENTED / VERIFIED — 2026-09-15 — opt-in only**

D-030's first coordination-state migration is implemented behind explicit Round `work_model_version=2`; legacy and ordinary operation continue to use version 1 unless version 2 is deliberately selected. Historical event streams are therefore not reinterpreted.

Version-2 work uses durable `tasks`, `assignments`, and `assignment_joins` as the authoritative scheduling and settlement state. The **current** structured decision set is `COMPLETE | DELEGATE | EVIDENCE | HISTORY | PASS`: Stage A introduced `COMPLETE | DELEGATE | PASS`, D-031 later added bounded source `EVIDENCE`, and D-033 added bounded prior-Room `HISTORY`. Delegation atomically creates bounded child assignments plus their dependency join, so conversational prose cannot claim delegation without creating runnable work. `EVIDENCE` keeps the same Assignment nonterminal while CORE obtains bounded source material; `HISTORY` atomically selects bounded prior completed results and requeues the same Assignment. A parent assignment remains nonterminal while delegated children are outstanding and resumes exactly once after the join resolves. Nested direct peer collaboration is supported through the same mechanism.

After V2-N1 exposed avoidable duplicate peer cognition, version-2 child assignment envelopes now also expose the other assignments already declared under the same dependency join as bounded sibling-work metadata: sibling agent, current assignment state, and bounded instruction. Sibling result content is withheld until the join resolves. This gives peers explicit mechanical awareness of work already in flight while preserving independent cognition and legitimate nested A↔B delegation.

The implementation also covers explicit required-contributor settlement gates, exact assignment-to-`agent_executions` provenance, transaction-aware turn limits and pause/resume behavior, stop/new-Round cancellation, exact-turn restart recovery, same-assignment usage-wall continuation, transaction quiescence, profile-rebind protection while work is open, and Task/Assignment/Join visibility in snapshots and JSON/Markdown exports. Readable Room events remain audit/conversation history; unread passive history is not an implicit version-2 runnable queue.

Stage A deliberately retained the existing persistent SDK-thread/context model so coordination reliability could be measured independently. Stage C later added the opt-in `assignment_thread` transport under D-032 while leaving `persistent_agent_thread` as the ordinary/default mode; the current provider-context behavior is summarized in Section 19.

PR #81 established the foundation and merged as `3043a3789d03013e4c3618eb3f6aff2861cb60df`. PR #82 completed the remaining Stage A invariants and merged as canonical `main` `a4f53a7c4f62a5d03a0907365f5024d266801e1c`. GitHub Actions run `35036898229` completed successfully on Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12 + browser. E-094 records the closeout evidence. V2-N1 then exposed the sibling-work visibility gap; PR #85 repaired it and merged as `19e5100508e4401f45cd27c11684c438171aa5c5`. Its tested PR head and merge share Git tree `1763d24377718e32606239e13ccd3343242e869e`; hosted run `35038949753` passed the same three-job matrix. E-095 records the naturalistic finding and remediation evidence.

**Activation status:** version 2 has passed the bounded V2-N1/V2-N2 Stage-A naturalistic checkpoint after the sibling-work remediation. This is evidence for the coordination kernel, not the full Stage-D viability gate. Version 1 remains the ordinary default; default version-2 activation has not been approved.

## 17. I-015 Stage B bounded evidence execution — declarative source bundles

**IMPLEMENTED / VERIFIED — 2026-09-15 — first bounded slice**

Stage B's first slice reuses the existing deterministic `inspect_source` engine rather than creating a second retrieval system. Capability version 3 adds a `bundle` operation for **already-known, independently bounded** source-inspection work. One bundle may contain labeled `find`, `search`, `search_many`, `read`, and `read_many` requests across authorized workspace, CORE, and Room-shared sources. CORE executes the declared requests in order and returns one normalized transient evidence bundle plus durable per-item provenance.

The bundle is intentionally not an adaptive research language. Nested bundles and source-inventory discovery are rejected, labels must be unique and bounded, the number of requests is capped, and the aggregate transient result has a bundle-wide byte ceiling. A retrieval whose necessity or bounds depend on an earlier result remains a later cognitive/tool step. Existing exploratory source operations therefore remain available and unchanged.

The direct CLI surface exposes `codex-room-cap source bundle` through either compact `--plan-json` or a workspace-relative `--plan-file`. At the Stage-B1 checkpoint, agent guidance preferred a bundle when heterogeneous retrieval operations and their bounds were known before execution, while retaining `search-many` and `read-many` for homogeneous batches. D-031/B2 later superseded that ordinary v2 agent-facing choice with structured `EVIDENCE`; the direct bundle remains an implementation/compatibility/operator primitive.

PR #88 implemented this slice and merged as `6158461bfee94eba375e99baec110e707c30499d`. Its final tested PR head `b7e3ce3ddf9652e21ef4e66f4a5a988a0855b93d` and the squash merge share Git tree `e9b7b1d633ecee9b7fb050df794384795f377a6e`. GitHub Actions run `35041711940` passed Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12 + browser. E-097 records implementation and verification evidence.

**Validation status:** this direct CLI/bundle slice remains implemented and verified as a compatibility/operator primitive. The later D-031 structured broker removed batching selection from ordinary version-2 agent cognition, and Stage B3 / E-101 supplied the naturalistic closeout evidence for the consolidated Stage-B interface. Stage B is complete. Stage C subsequently completed under D-032/D-033 with implementation and naturalistic evidence E-102 through E-106; those later context findings do not change the Stage-B bundle's compatibility/operator role.

## 18. I-015 Stage B2 structured deterministic source evidence execution

**IMPLEMENTED / VERIFIED — 2026-09-16 — opt-in work-model v2**

D-031 moves bounded read-only source retrieval behind the version-2 transaction contract. A transaction assignment may now return `EVIDENCE` with 1–16 semantic `READ`, `SEARCH`, or `FIND` requests naming the logical source, path/query, Room ID when applicable, and useful bounds. The assignment remains nonterminal while CORE obtains the evidence and then resumes the same logical assignment with the normalized result.

CORE owns the invocation mechanics for this path. It validates the structured request through the existing source-inspection contract and mechanically chooses an existing `inspect_source` execution form. One request executes directly; a bounded homogeneous read set may execute through `read_many`; other independent multi-request sets use the existing `bundle` primitive when that preserves the declared atomic semantics. In particular, independent SEARCH requests currently remain bundled because `search_many` has one aggregate match bound rather than independent per-request match bounds. Agents therefore do not need to choose `bundle`, `read_many`, `search_many`, executable paths, shell quoting, JSON transport, or plan files for source retrieval.

A new durable `assignment_evidence` record binds each evidence request to the exact assignment and originating execution batch. Pending requests survive process restart; successful deterministic execution records the selected plan plus bounded durable evidence/provenance, requeues the same assignment, and makes bulk result content available to that resumed assignment. After the resumed assignment settles its next decision, the transient bulk result is cleared while durable request/plan/result provenance remains visible in transaction state and exports. Stop/new-Round cancellation covers waiting evidence and prevents stale evidence completion from reviving cancelled work.

The existing CLI and deterministic capability substrate remain available as operator/debug/compatibility surfaces and for non-source registered/custom capabilities. Version-2 source retrieval guidance now points agents to `EVIDENCE` while retaining a compact non-source capability contract. Work-model v1 keeps its existing capability path. Direct `codex-room-cap source bundle` telemetry recognition was also repaired so the compatibility surface promotes the same bounded deterministic provenance as the other direct source verbs.

PR #92 code-bearing head `9b4e352e490a4cdeda9a8242396cabd981f3b19d` (Git tree `2b27d2ea509f279416eb65a8c2a6161414096501`) passed GitHub Actions run `35066558470`: **401 tests, 2 warnings** on Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12; the Windows browser transcript-stability check additionally passed **3 tests**. E-100 records the exact implementation and verification evidence.

**Naturalistic closeout:** Stage B3 / E-101 passed on 2026-09-16 in a fresh C-only version-2 Room. C declared the three known source needs as one structured FIND + SEARCH + READ evidence request; CORE mechanically selected a heterogeneous bundle; the same assignment resumed and made one evidence-dependent follow-up READ after SEARCH supplied the declaration's line location; then C completed the task correctly. The run used **72,271 total execution tokens**, with zero agent CLI/tool calls, zero failures, zero file changes, and preserved request/plan/result provenance. This closes Stage B as **IMPLEMENTED / VERIFIED / NATURALISTIC CHECKPOINT PASSED**.

**Scope limit:** the broker handles read-only source evidence. Arbitrary custom-capability brokerage remains outside this slice because preserving its Room/sandbox execution authority needs a separate design. Stage C is now complete separately under D-032/D-033 and E-102 through E-106.

**Stage-D D-N4 remediation status — IMPLEMENTED / VERIFIED / MERGED (2026-09-16):** PR #104 merged the structured-EVIDENCE contract/telemetry repair, and the repository-standard `verify-fast.cmd` then passed on exact code-bearing canonical-main commit `668ef98253c5bd1387eefb1b71f99ed38fd8b53c`: Linux/Python 3.12 focused core **45 passed, 2 warnings**; Windows focused portability **118 passed**; browser transcript stability **3 passed**; total verifier time **74.7 seconds** with all phases exit code 0 and a clean tracked tree. The repair aligns provider/runtime path validation, states CORE path semantics, preserves invalid-decision usage/activity/economics, and supplies one-shot retry feedback without stale leakage. E-108 records implementation/focused evidence; E-110 records merged-tree verification.

## 19. I-015 Stage C assignment-scoped provider context and bounded continuity

**IMPLEMENTED / VERIFIED / NATURALISTIC CHECKPOINTS PASSED — 2026-09-16 — opt-in work-model v2**

D-032 treats provider context as execution transport rather than the definition of persistent agent identity. Persistent A/B/C identity, transaction state, evidence state, joins, and assignment provenance remain durable application-level state. The existing `persistent_agent_thread` mode remains the ordinary default.

An opt-in version-2 Round may set `provider_context_mode="assignment_thread"`. Each logical Assignment then owns a durable `context_thread_id`. CORE creates and binds that provider thread for the Assignment's first model execution, reuses the same thread for evidence and dependency/join continuations, carries it through usage-wall continuation, and resumes an exact recorded non-agent thread/turn after process interruption. A later independent Assignment receives a different provider thread even when the same persistent agent owns both Assignments.

The adapter can therefore start and resume provider threads that are not the agent's permanent cached thread without replacing that permanent cache. Public execution entry points still enforce the existing model-policy boundary before thread acquisition. Assignment-scoped mode also avoids permanent-thread compaction because its context is already bounded to the logical Assignment.

Hosted deterministic coverage verifies same-Assignment reuse, same-agent distinct-Assignment isolation, evidence resume, usage-wall restart, exact active-turn recovery, permanent-mode compatibility, and preservation of the permanent agent thread. E-102 records the exact PR/main commits, shared tree, CI runs, and test counts.

**Naturalistic economics:** C-N1 / E-103 compared one self-contained C-only task in the already-warmed B3 Room. The assignment-scoped arm used **20,810 input tokens** versus **27,389** for the persistent-thread arm, a **24.0% reduction**, with one execution each, identical correctness, and no tool/peer/evidence activity. The assignment arm had zero cached input; the persistent arm replayed **17,152 cached input tokens**. This passes the preregistered material-improvement threshold and demonstrates that provider-history inheritance can impose measurable cost without adding value on self-contained work.

**Cross-Assignment continuity:** C-N2 / E-104 established one arbitrary fact on C's permanent provider thread, then asked a fresh assignment-scoped thread to recall it with guessing prohibited. The assignment-scoped arm returned `UNKNOWN`, while a subsequent persistent-thread control returned the exact nonce. Each arm used one execution and no tools, peers, or evidence requests. This demonstrates that Assignment-bounded provider context does not itself supply episodic continuity from prior Rounds, even though reusable prompt/instruction prefixes may still produce cached-input hits.

**Stage C.3 targeted retrieval — IMPLEMENTED / VERIFIED:** D-033 adds transaction action `HISTORY` for bounded `RECENT` and lexical `SEARCH` retrieval across prior completed Assignment results in the same Room. CORE performs same-Room/prior-Round selection, optional agent filtering, result-count bounds, exact event-ID provenance, and atomic attachment to the requesting Assignment's existing `context_event_ids`. The action is nonterminal and requeues the same Assignment; its assignment-scoped provider thread therefore resumes with selected historical results rather than inheriting another Assignment's provider history. Retrieved historical text is separately marked from authoritative current Task/Join/Evidence state and bounded to 24,000 characters in the prompt. A deterministic audit event records the exact selected result IDs. PR #99 and canonical-main CI verify the implementation; E-105 records the exact commits, trees, runs, and test counts.

**Naturalistic acceptance:** C-N3 / E-106 passed on the existing warmed continuity Room. One C-only assignment-scoped Assignment declared `HISTORY`, CORE selected the exact prior C-N2 establishment result event, the same Assignment context thread resumed, and C completed with the exact nonce. Durable `context_event_ids` and the deterministic Room-history audit both retain the selected event ID. The run used exactly two model executions and no model tools, source evidence, peers, capabilities, retries, file changes, or compactions.

**Economics boundary:** C-N3 consumed **43,398 input / 20,224 cached input / 43,547 total tokens** across two executions. The comparable C-N2 persistent recall control required one **29,211-token** execution. Stage C therefore does not claim explicit retrieval is cheaper for every continuity-dependent task. The validated design trades lower inherited replay on self-contained work (C-N1: 24.0% lower input) for an additional bounded retrieval continuation when prior episodic context is genuinely needed. Stage D owns the whole-system viability judgment across ordinary tasks.

**Stage C closeout:** Stage C is COMPLETE. No separate memory database, embeddings, summarization layer, automatic wholesale history injection, or provider-thread archive is justified by current evidence. Broader D-009 indexing remains future direction only if ordinary use demonstrates the bounded recent/lexical result path is insufficient. A narrow crash window can still create an unused orphan provider thread after provider-thread creation but before durable Assignment binding; no model turn has started in that window, so current evidence does not indicate duplicate cognition.

### Stage D viability closeout

**NATURALISTIC VIABILITY GATE PASSED — 2026-09-16 — PUBLIC V2 DEFAULT ACTIVATED / VERIFIED / MERGED**

The preregistered I-015 Stage-D attempt 2 completed all ten scored tasks in one dedicated Room using `work_model_version=2` with assignment-scoped provider context. Final quality was **9/10 PASS**; all coordination/provenance invariants and robustness requirements passed. Aggregate economics also passed: **74,863.5 median task tokens**, **150,592 nearest-rank p90**, **2 median post-framing continuations**, **182,555 maximum task**, and D-N10 first-C input **21,170** versus D-N1 **21,257** (inside the 125% context-isolation ceiling). See E-111 through E-120.

D-N6 was the sole quality failure and is preserved rather than rerun: history retrieval and Assignment/thread continuity were correct, but C's revised schedule violated the preserved package-drop deadline. The remaining tasks passed their fixed rubrics, including truncation recovery, stale-history discrimination, deterministic evidence failure/recovery, nested delegation, and the final long-Room self-contained isolation check.

This closed the naturalistic viability question for the version-2 task-transaction architecture. The principal subsequently approved D-034, and PR #107 activated **work-model version 2 with `provider_context_mode="assignment_thread"` as the public production path** for new Room work, staged Rounds, New Topic, and rollover successors. Exact PR head `6a9137a47de0da27a0425ab7683ca09b9aa41940` passed the repository fast verifier and merged as `03136c3b11c8c05b8385d0e9f30822dbc014a756`. Public v1 selection is rejected. Legacy Rooms will be deleted rather than converted; no migration/reinterpretation layer is part of the production architecture. See E-121.

## 20. Runtime-state and work-queue caution

Current priorities, maintenance issues, blockers, and open questions are owned by `06_DEVELOPMENT_CONTROL.md` and are intentionally not duplicated in this architecture synthesis.

Live evidence spans the dated records in the Evidence Register rather than one permanent smoke snapshot. E-029 covers the 2026-09-12 post-D-020 smoke/early-triad repair, E-040 closes live P4.5 rollover inheritance, and E-064 provides the latest clean D-027 invocation-economy Room: C differentiated A/B work, A used a public no-wake return, B targeted only C, one cohort integration turn followed, and no visibility-driven peer review/reopen cascade occurred. Older Room-error snapshots remain historical evidence only.
