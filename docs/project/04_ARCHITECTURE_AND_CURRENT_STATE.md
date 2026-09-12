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

The initial P4.3 CORE library is now code-complete: `assert_file`, `find_files`, `search_text`, and `compare_files`. The registry remains static. D-022 settles the future unified CORE/lineage/Personal model and rollover-continuity requirement, but custom capability registration, persistence, inheritance, and promotion are not implemented yet. One bounded fresh-Room live evaluation remains before P4.3 can close.

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

## 14. Runtime-state and work-queue caution

Current priorities, maintenance issues, blockers, and open questions are owned by `06_DEVELOPMENT_CONTROL.md` and are intentionally not duplicated in this architecture synthesis.

Fresh live Personal Room exports were captured on 2026-09-12 and are recorded in E-029. They provide current runtime evidence for D-020 selective coordination, integration-before-closure, C-only engaged-participant settlement, SDK-pinned runtime operation, and successful local adoption of the repaired A/B/C built-in profiles. Older Room-error snapshots remain historical evidence only.
