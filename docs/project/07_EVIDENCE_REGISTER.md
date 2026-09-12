# Codex Room — Evidence Register

**Initialized:** 2026-09-08  
**Last updated:** 2026-09-12  
**Scope:** Compact empirical record supporting important project claims.  
**Freshness:** Evidence proves what was observed at a stated time/version. It does not automatically prove every later version behaves identically.

## Evidence conventions

Each entry records the observation, its significance, and important limits. Large raw artifacts remain external to this maintained package.

---

### E-001 — Measured Room invocation usage
**Date:** 2026-09-08 analysis of `Codex-Room-Continuation (11).json`  
**Kind:** Runtime/export measurement

142 measured model invocations contained usage metadata:

- input: **10,978,902**
- cached input: **10,386,048**
- output: **50,364**
- reasoning output: **24,594**

Outcome breakdown:

- MESSAGE: 83 invocations; **6,405,576** input; ~77,176 average
- PASS: 53 invocations; **4,308,241** input; ~81,288 average
- FINISH: 6 invocations; **265,085** input; ~44,181 average

PASS input by agent:

- B: 27 PASS; **2,753,191** input
- C: 18 PASS; **1,091,395** input
- A: 8 PASS; **463,655** input

Approximately 94.6% of raw input was cached input.

**Significance:** PASS is computationally expensive in a persistent-thread architecture; concise output does not imply cheap cognition.

**Limit:** Raw input tokens are useful comparatively; cached-input pricing/weighting may differ from uncached input.

### E-002 — Tiny-question invocation cascade
**Date:** 2026-09-08 analysis  
**Kind:** Runtime/export measurement

A direct user question to C caused:

- C answer: **55,291 input**
- A wake → PASS: **47,826 input**
- B wake → PASS: **138,764 input**

Total: ~**241,881 input**. A+B PASS expenditure was ~**186,590 input**, or **77.1%** of the chain.

**Significance:** A small task can trigger much larger peer cognition under all-peer fan-out.

### E-003 — Persistent context growth
**Date:** 2026-09-08 analysis  
**Kind:** Runtime/export measurement

Early successor invocations were roughly ~21k input tokens. Later examples included B PASS turns up to ~145k, A substantive turns ~175k–180k+, and C after compaction often ~55k–61k.

**Significance:** Persistent-thread context growth can increase the cost of otherwise similar decisions.

### E-004 — Broad MESSAGE fan-out was explicit in the 2026-09-08 implementation
**Date:** 2026-09-08 repository inspection  
**Kind:** Source/test inspection

The inspected `AgentDecision` protocol exposed MESSAGE/PASS/FINISH without a recipient field, and `_apply_decision()` routed MESSAGE to all peers.

**Status:** SUPERSEDED by E-017 for current implementation behavior.

### E-005 — Existing event schema contained selective-routing building blocks
**Date:** 2026-09-08 repository inspection  
**Kind:** Source inspection

Observed fields/concepts included `agent_readable`, `turn_triggering`, and `visibility`.

**Significance:** The persistence/event model already contained part of the distinction later used by selective invocation.

### E-006 — Delivery coalescing
**Date:** 2026-09-08 repository inspection  
**Kind:** Source/test inspection

`claim_next_batch()` coalesced multiple pending conversational deliveries into a single invocation when appropriate, with explicit test coverage.

**Significance:** Existing batching is an efficiency feature worth preserving.

### E-007 — Observer blanking/rescrolling repair
**Date:** Prior to 2026-09-08 handoff  
**Kind:** Implementation + practical user verification

Keyed reconciliation, stable IDs, status-only chrome, reconnect merge behavior, and reader anchoring/follow behavior were implemented. Practical user testing succeeded.

**Status:** HISTORICALLY VERIFIED.

### E-008 — Exact-turn completion + inactivity lease repair
**Date:** Prior to 2026-09-08 handoff  
**Kind:** Test verification

Historical final full-suite result: **69 passed, 0 failed, 0 skipped**.

**Status:** HISTORICALLY VERIFIED.

### E-009 — Proactive context-compaction race repair
**Date:** Prior to 2026-09-08 handoff  
**Kind:** Test verification

Historical final result: **70 passed, 0 failed**. Repair behavior included positive `contextCompaction` completion evidence, idle-state preflight, and repeat-compaction suppression.

**Status:** HISTORICALLY VERIFIED.

### E-010 — Rollover reduced initial successor context
**Date:** 2026-09-08 handoff evidence  
**Kind:** Runtime measurement

Predecessor → successor first-invocation reductions:

- A: 109,892 → 21,318 (**−80.6%**)
- B: 92,820 → 20,907 (**−77.5%**)
- C: 83,519 → 21,338 (**−74.5%**)

**Significance:** Clean rollover can materially reduce inherited active context while preserving continuity through other mechanisms.

### E-011 — Institutional release binding
**Date:** 2026-09-08 reviewed evidence  
**Kind:** Runtime/metadata observation

Release `continuity-toolkit-v1` with manifest `d0a193ec20118d146ec910cde1ff85aa14564d275972571e88cb58f7dddec82a` was observed bound identically in top-level and lineage metadata.

### E-012 — Deployment/restart choreography cost
**Date:** 2026-09-08 analysis  
**Kind:** Runtime/export measurement

One deployment/restart/activation sequence consumed approximately **1.31 million raw input tokens**, including roughly **800k PASS input**.

**Significance:** Stable operational choreography is a strong candidate for deterministic local tooling.

### E-013 — Compaction-baseline ratchet hypothesis
**Date:** 2026-09-08 repository/runtime analysis  
**Kind:** Source + usage-pattern hypothesis

Observed A compaction points were approximately 82k, 112k, 151k, and 181k input. Inspection suggested the anti-repeat baseline could be using pre-compaction context size.

**Status:** SUPERSEDED by E-019; the defect was later confirmed and repaired.

### E-014 — 2,000-event retrieval concern
**Date:** 2026-09-08 repository inspection  
**Kind:** Source inspection

`Database.get_events()` appeared to use ascending order with `LIMIT 2000`, and snapshots/initial WebSocket state/exports used this path.

**Significance:** A Room above 2,000 events could expose/export the first 2,000 while omitting newer events.

**Status:** SUPERSEDED by E-025. The issue was later re-confirmed in canonical source, repaired, regression-tested, merged, and hosted-verified.

### E-015 — Repository lacked a Git baseline
**Date:** 2026-09-08 repository snapshot inspection  
**Kind:** Repository-state observation

The included `.git` state had no commits or refs and the source tree was untracked.

**Status:** SUPERSEDED by E-021.

### E-016 — Historical usage-limit failure state
**Date:** 2026-09-08 handoff  
**Kind:** Runtime/export observation

A hit a usage limit, immediate retries followed, A entered persistent `systemError`, and the Room became `error`.

**Significance:** This failure motivated later retry/recovery work.

**Limit:** Historical only; do not treat this as current runtime state.

### E-017 — Selective invocation implemented and exercised
**Date:** 2026-09-09  
**Kind:** Current-source inspection + historical test/runtime evidence

Current canonical source exposes optional `AgentDecision.invoke_targets`. `_resolve_invoke_targets()` treats null or `["all"]` as all peers and validates named peer targets. Agent MESSAGE creation records readable recipients, runnable recipients, triggering/passive event IDs, usage, and `legacy_fanout_invocations_avoided`; delivery uses separate readable and runnable recipient sets.

Historical verification after implementation: **111 passed, 2 warnings**, SQLite `quick_check` OK.

A real Room exercise used **5 purposeful invocations** and recorded **4 legacy fan-out invocations avoided**.

**Status:** IMPLEMENTED / HISTORICALLY VERIFIED.

### E-018 — Retry / Agent Error observability repair
**Date:** 2026-09-09  
**Kind:** Current-source inspection + historical test evidence

Current source records retrying operator state and exposes interrupted retry attempts before terminal failure. Later correlated success can record recovery; stale/stop/quarantine paths are guarded against false recovery.

Historical verification: focused tests, one historical reconciliation test, and browser/UI checks passed; full suite **116 passed, 2 warnings**, SQLite `quick_check` OK.

**Status:** IMPLEMENTED / HISTORICALLY VERIFIED.

### E-019 — Deferred post-compaction growth baseline
**Date:** 2026-09-09  
**Kind:** Current-source inspection + historical test evidence

Current source writes `growth_baseline_state = "pending"` after successful compaction. `establish_context_checkpoint_growth_baseline()` then atomically records the first later authoritative input-token count and batch ID as the established baseline. The establishment turn is excluded from compaction, and later turns apply the 25,000-token growth requirement from that post-compaction baseline.

Historical verification: focused/restart checks passed; full suite **119 passed**, SQLite `quick_check` OK.

**Status:** IMPLEMENTED / HISTORICALLY VERIFIED.

### E-020 — Usage-wall delayed continuation
**Date:** 2026-09-09  
**Kind:** Current-source inspection + historical test/database evidence

Current source contains durable `usage_continuations`, a 60-second grace constant, retry-time parsing restricted to positively identified usage walls, same-thread continuation preparation, watchdog release through the normal queue, repeated-wall rescheduling, and stale lifecycle cancellation.

Historical verification: **10 focused tests passed**; full suite **127 passed**; production and fresh-migration database integrity checks were OK with zero foreign-key failures.

**Status:** IMPLEMENTED / VERIFIED — current A2 review 2026-09-12.

A2 re-inspected the current usage-wall source path, including positive `usageLimitExceeded` classification, retry-time parsing with a 60-second grace, transactional suspension, lifecycle/thread-bound release, same-thread continuation, restart survival, repeated-wall rescheduling, stale lifecycle cancellation, and fail-closed behavior for unparseable retry times. Current deterministic coverage exercises suspension/release, restart, repeated-wall reschedule, non-usage fallback, invalid retry time, and stop cancellation. The current runtime/test bytes are covered by canonical `main` run `34703409739`: **136 passed, 2 warnings**.

**Limit:** No new live provider usage-wall event was induced during A2; verification is based on current source plus exact-version deterministic adapter/runtime tests.

### E-021 — Canonical Git/GitHub baseline and live working-copy alignment
**Date:** 2026-09-10  
**Kind:** Repository-state + mechanical hash verification

A private canonical repository exists at `strigoi73-sudo/codex-room` with `main` at:

`7b4f7aaa47e23ea117806199d38fe1fc396f4fc9`

The live `C:\Codex Room` repository was attached to `origin/main` at that exact commit. All tracked files were mechanically compared with Git blob hashes before attachment. A representative three-way check for `codex_room/agent.py` produced the same blob ID for live file, transfer copy, and `origin/main`:

`d26babff71c83ae89c624b877cd9b1d23de4bb2d`

with live and transfer copies both **24,780 bytes**.

After branch/upstream attachment and removal of leftover archival ZIPs, `git status --short` returned no output.

**Status:** IMPLEMENTED / VERIFIED for repository alignment as of 2026-09-10.

**Significance:** Later [CORE] work can now be tied to immutable commits/diffs instead of reconstructed ZIP snapshots.

### E-022 — Reproducible install and canonical routine test suite
**Date:** 2026-09-10  
**Kind:** Clean-environment package/test verification

EF-1/EF-2 added explicit setuptools package/static-asset configuration to `pyproject.toml` and documented the development/test setup. In a disposable clean Python environment, the project installed successfully from its declared configuration with `python -m pip install ".[test]"`.

The canonical routine test command is `python -m pytest -q`. Clean-environment verification collected **129 tests** and the full routine suite exited successfully.

The approved changes were committed and pushed as:

`a021656f6cd928683c8e77ff9e5dd2d51a965419` — `Establish reproducible development and test setup`

`test-transcript-stability.ps1` was deliberately kept outside the routine Python suite because it requires Node.js plus an installed Chrome or Edge browser. `uv` was not adopted because the existing pip/venv workflow satisfied the reproducibility objective.

**Status:** IMPLEMENTED / VERIFIED.

### E-023 — Minimal GitHub CI completed successfully
**Date:** 2026-09-10  
**Kind:** GitHub-hosted clean install/test execution

Commit:

`d714fb08910613e99e7e9ab2168b7c3ea52bb05b` — `Add minimal Python test CI`

added `.github/workflows/python-tests.yml`. The workflow runs on pushes to `main` and pull requests targeting `main`, uses Python 3.12 on Ubuntu with `contents: read`, installs `.[test]`, and executes `python -m pytest -q`.

GitHub Actions run `34522039398` completed with conclusion **success**. Checkout, Python setup, package installation, pytest, and post-job steps all completed successfully.

**Status:** IMPLEMENTED / VERIFIED.

**Significance:** Routine clean-install/test verification can now be performed by deterministic hosted automation rather than consuming model cognition.

### E-024 — Git-mediated ChatGPT ↔ Codex development handoff demonstrated
**Date:** 2026-09-10  
**Kind:** Process observation / operating-economics evidence

The Git-baseline, EF-1/EF-2, and EF-3 work demonstrated a repeatable external maintenance pattern:

1. project-level reasoning and scope control occurred in the ChatGPT Codex Room Project;
2. local Codex received explicit bounded prompts for filesystem/repository execution;
3. Git diffs and commit identities carried exact change evidence back for review;
4. GitHub exposed the canonical pushed version to both sides;
5. GitHub Actions performed routine clean-install/test verification without model reasoning.

This removed the need for routine ZIP/Drive source handoffs and avoided requiring Codex to independently rediscover analysis already settled in the Project when a mechanical execution prompt was sufficient.

**Significance:** This process directly supports the token-efficiency objective by separating reasoning, local execution, exact evidence transport, and deterministic verification.

**Limit:** No controlled before/after token-cost benchmark has yet quantified the savings. Treat the efficiency benefit as strongly motivated by mechanism and observed workflow simplification, not as a measured percentage reduction.

### E-025 — I-001 long-Room history repair
**Date:** 2026-09-11  
**Kind:** Current-source inspection + regression test + GitHub PR/CI + local Git alignment

The confirmed I-001 defect was repaired through GitHub PR #2 and squash-merged to canonical `main` as commit `34abd391ecbb861d7661541e4a716a5152a2049d` (`Fix complete event history for long Room exports`).

Implemented behavior at that commit:

- `Database.get_events(room_id, limit=2000)` retains a bounded default but selects the newest events and returns the selected window in ascending `sequence_no` order;
- `Database.snapshot(..., event_limit=2000)` reports `event_window` metadata: configured limit, total count, returned count, truncation flag, and first/last returned sequence numbers;
- the Room export route calls `db.snapshot(room_id, event_limit=None)`, so JSON and Markdown exports include complete event history rather than inheriting the live snapshot limit;
- regression coverage inserts more than 2,000 events and verifies that the live Room state exposes the latest 2,000 while JSON export includes the entire history, including events outside that live window.

Verification:

- PR-head GitHub Actions: **130 passed, 2 warnings**;
- post-merge `main` GitHub Actions: **130 passed, 2 warnings**;
- the local `C:\Codex Room` `main` branch was fast-forwarded from `8cc0b378...` to `34abd391...` on 2026-09-11.

**Status:** IMPLEMENTED / VERIFIED. I-001 is closed.

**Limit:** complete export currently materializes the full Room snapshot/history in memory. This fixes correctness; it does not establish that arbitrarily large exports are optimally scalable.
### E-026 — Codex 0.147.0 exposes structured account rate-limit usage data
**Date:** 2026-09-11  
**Kind:** Exact-version upstream source/protocol inspection + current Codex Room dependency/source inspection

Inspection of OpenAI's `openai/codex` source at tag `rust-v0.147.0` established that the pinned Codex generation used by Codex Room already exposes structured account rate-limit data through the app-server JSON-RPC method:

`account/rateLimits/read`

Relevant exact-version protocol/source evidence includes:

- `RateLimitWindow` carries `usedPercent`, `windowDurationMins`, and `resetsAt`;
- `RateLimitSnapshot` carries primary and secondary windows and optional multi-bucket usage metadata;
- the generated client request schema includes `account/rateLimits/read`;
- app-server tests exercise authenticated reads backed by `/api/codex/usage` and map backend usage windows into structured rate-limit snapshots.

Current Codex Room dependency constraints pin `openai-codex==0.147.0` and `openai-codex-cli-bin==0.147.0`. Current Room source uses `AsyncCodex`.

At 0.147.0, the high-level public `AsyncCodex` convenience API exposes account/login/thread/turn/model operations but does not expose a dedicated first-class rate-limit convenience method. The underlying SDK client does provide a generic typed JSON-RPC `request()` path, so a bounded Codex Room integration appears technically feasible without scraping UI output. The exact integration boundary should be chosen during implementation; relying on private SDK attributes should not be treated as settled design.

**Evidence qualification:** VERIFIED for existence and shape of the 0.147.0 app-server rate-limit protocol; NEEDS VERIFICATION for the eventual Codex Room integration implementation and runtime behavior.

**Significance:** D-019 can be developed against provider-reported structured usage data rather than an internally estimated weekly allowance.


### E-027 — D-020 permanent-triad and C-integration migration
**Date:** 2026-09-12  
**Kind:** Current-source inspection + targeted regression coverage + GitHub PR/CI + local browser verification + exact-tree identity

D-020 was implemented through GitHub PR #3. The exact reviewed/tested PR head was:

`2748e2900024d99463eacf2b9e9398a0718c5f74`

Implemented behavior at that version includes:

- new Personal Rooms always create A/B/C with distinct persistent threads;
- C is the ordinary default starter, while explicit participant or `either` starts remain available;
- historical A/B Rooms remain unchanged unless explicitly upgraded; rollover successors become triads even when the predecessor is a historical pair;
- direct A↔B selective routing remains supported while public peer work is passively readable by C;
- triad settlement excludes genuinely unengaged participants rather than forcing unnecessary model calls;
- unread passive A/B MESSAGE material for C is detected mechanically before closure and produces one durable runnable `integration_required` trigger when no existing C opportunity is already open;
- C receives pending peer material and the integration trigger through normal ordered delivery coalescing and may finish or redelegate;
- restart/idempotence, direct peer return to C, symmetric A↔B routing, legacy upgrade, rollover, API, and static UI behavior have targeted regression coverage;
- inactivity closure respects open deliveries so a pending C integration trigger cannot be closed out by the watchdog.

Verification on the exact PR head:

- GitHub Actions run `34701476286`: **136 passed, 2 warnings** using the canonical Python suite;
- local `C:\Codex Room\test-transcript-stability.ps1` on the detached exact PR head: **3 passed (11.5s)**;
- the local workspace was then returned to a clean `main` state before the PR merge.

PR #3 was squash-merged to canonical `main` as:

`12b156853c9c8b053eaae63aec44f44fc83618af` — `D-020: Permanent Personal triad and C integration barrier`

The reviewed PR head and the squash-merge commit both resolve to Git tree:

`8f3348fd5688361a0a516ea88d76cf394d5c7944`

so the merged production source bytes are exactly the bytes covered by the PR-head Python and browser verification.

The first push-triggered `main` run after merge, `34703228720`, passed **135 tests** and failed one legacy-upgrade regression assertion because the test required `delivery_start_sequence == max_before`. Source inspection showed that `reserve_agent_c()` correctly captures the actual pre-join watermark inside its `BEGIN IMMEDIATE` transaction, while an active legacy worker can append another legitimate pre-join event after the test's earlier unsynchronized `max_before` observation. The production behavior was therefore unchanged; the test assertion was too strict for the documented concurrency boundary.

Commit:

`749b31ba73bb9e7f64e41ac4f4bf81519fc4ba97` — `Stabilize legacy C-upgrade regression`

changed only `tests/test_three_agents.py` and `docs/project/06_DEVELOPMENT_CONTROL.md`: the test now requires the actual join watermark to be **at or after** the last sequence observed before the join request, while retaining the stronger behavioral checks that no pre-join public/private/overlay content reaches C. No production runtime file changed.

GitHub Actions run `34703409739` on that canonical-`main` stabilization commit completed successfully with **136 passed, 2 warnings**.

**Status:** IMPLEMENTED / VERIFIED.

**Limit:** this verification establishes the deterministic runtime/UI contract and exact merged bytes. It is not a new live multi-agent production exercise against a long-running real Room; A2 should evaluate the post-D-020 architecture using the evidence appropriate to each assurance claim.


### E-028 — Assurance Pass 2
**Date:** 2026-09-12  
**Kind:** Bounded current-source/config assurance review + exact-version deterministic evidence mapping

A2 assessed the intended post-D-020 Personal architecture. The pass began after the Engineering Foundation and D-020 were complete and deliberately avoided new in-Room A/B/C exercises, broad refactoring, P4 implementation, and opportunistic repairs.

Assessed runtime/test baseline:

- canonical runtime/test commit `749b31ba73bb9e7f64e41ac4f4bf81519fc4ba97` passed GitHub Actions run `34703409739` with **136 passed, 2 warnings**;
- later commits through the A2 review changed only `docs/project/**`; a direct compare from that green runtime/test commit to the review-time `main` showed no non-Project-document changes;
- D-020 exact-tree/browser evidence remains E-027.

Assurance matrix:

| Area | Rating | Basis | Important limitation |
|---|---|---|---|
| Repository, reproducibility, provenance | **GOOD** | canonical Git/GitHub history; explicit package metadata; constrained known-good dependency set; canonical pytest command; GitHub CI; generated/runtime paths excluded from source | `main` is currently unprotected, but no demonstrated Personal single-principal failure makes branch protection a present assurance requirement |
| Agent identity and continuity | **GOOD** | unique persistent thread IDs; restart resumes stored identities; compaction preserves thread IDs; reset explicitly archives/replaces identities; rollover requires fresh non-predecessor IDs; legacy C upgrade preserves A/B IDs | provider-side adoption of replacement developer instructions on an existing resumed thread remains **NEEDS VERIFICATION** under I-003 |
| Execution safety | **GOOD** | one serialized worker per participant; worker generations; durable exact-turn binding; active-handle quarantine; lifecycle/version stale-result rejection; restart reconciliation; bounded inactivity execution lease | deterministic/fake-adapter tests establish mechanical guarantees; no new live long-running provider stress exercise was run |
| Permanent triad coordination and settlement | **GOOD** | D-020 / E-027 exact reviewed tree; targeted A↔B routing, passive C readability, integration barrier, restart/idempotence, direct return, redelegation, legacy upgrade and rollover tests | no new real long-running Room exercise was needed or run in A2 |
| Retry and usage-wall recovery | **GOOD** | current-source review; retry warning/terminal distinction; transactional usage suspension/release; lifecycle/thread checks; same-thread restart continuation; reschedule/cancel/fail-closed tests | no new live provider usage-wall event was induced |
| Data integrity and observability | **GOOD** | WAL + foreign keys; transactional event+delivery creation; unique thread/event-recipient/exact-turn identities; atomic batch compare-and-set paths; monotonic Room event sequence; bounded live snapshots plus complete exports; execution health telemetry | complete export still materializes all Room history in memory; scalability remains a later concern rather than a correctness gap |
| Personal privacy/exposure boundary | **GOOD** | default server bind is `127.0.0.1`; private observer messages deliver only to the named participant; private status is labeled; exports expose private content to the authorized human operator intentionally | this does not assess Enterprise/multi-user authorization, which is not the current Personal scope |
| Operating-economics mechanisms | **PARTIAL** | selective invocation, passive readability, batching, compaction growth controls, and C integration coalescing structurally reduce unnecessary cognition | no post-D-020 real-Room usage benchmark was collected, so current end-to-end savings are not empirically quantified |
| Intent ↔ implementation alignment | **PARTIAL** | D-020 runtime aligns with permanent triad and peer coordination; mechanical peerhood is preserved | I-004 README text still describes optional C in places; A/B saved profiles and Room overrides replace full developer instructions, so constitutional/peer protocol text is not independently protected beneath customization |

A2 did **not** demonstrate a material runtime **GAP** requiring repair before the next planned phase.

Follow-ups preserved after A2:

- **I-003** remains low-priority **NEEDS VERIFICATION**: current deterministic evidence proves same-thread rebind is attempted with current instructions and fails closed on identity mismatch, but provider-side instruction adoption has not been independently demonstrated.
- **I-004** is a verified low-priority documentation inconsistency: the README's First run/selected-participant wording and optional-C visual residue conflict with the permanent-triad implementation.
- A/B role/personality/institutional-layer separation remains a future design concern. Current editable A/B instructions can replace the whole developer prompt; mechanical peer authority is unaffected, but institutional prompt composition is only partially assured. The human principal previously deferred that redesign.
- P3's former exact-byte review caveat is retired by this A2 current-source review plus exact-version deterministic coverage.
- No new live model exercise was justified solely to turn already-strong deterministic assurance into ceremony.

**Overall A2 result:** current Personal Codex Room has **GOOD** mechanical assurance across the core execution architecture, with no demonstrated material runtime gap. Remaining weaknesses are bounded and mostly concern provider-side profile verification, documentation alignment, empirical post-D-020 usage measurement, and future protected composition of institutional versus customizable agent instructions.

**Status:** A2 COMPLETE.


### E-029 — Live post-D-020 smoke exercise and early-triad profile repair
**Date:** 2026-09-12  
**Kind:** Live Personal Room export + current-source diagnosis + GitHub PR/CI

A bounded cognitively-light live Room exercise was run after D-020.

The first attempt was started while `CODEX_ROOM_CODEX_BIN` pointed at the current desktop-app Codex executable rather than the Python SDK's matching packaged runtime. Agent C's first turn completed without a usable final response, then the persistent thread entered `system-error`; the Round stopped with zero agent decisions. The launcher was corrected so that an explicit `CODEX_ROOM_CODEX_BIN` override is still honored, but no override is supplied by default. The pinned `openai-codex==0.147.0` SDK therefore selects its matching `openai-codex-cli-bin==0.147.0` runtime. Commit `41856bbd5f7e2e7c9b4f48df835bd468a02642fd` was hosted-verified by GitHub Actions run `34705380711`: **137 passed, 2 warnings**.

A second fresh Room on the SDK-pinned runtime completed successfully with six agent turns. The observed sequence was:

1. C started the Round and selectively invoked A;
2. A returned `ALPHA` and selectively invoked C;
3. C selectively invoked A for the direct-peer stage;
4. A sent `PING` and selectively invoked B;
5. B FINISHed without invoking C;
6. the Room created `integration_required` for C, coalesced it with A's passive unread message, and C FINISHed with `C-ONLY-OK | ALPHA | INTEGRATION-OK`;
7. the Round closed with reason `reactions_settled`.

This is fresh live evidence for C-first initiation, selective runnable/readable separation, direct A→C and A→B routing, passive C readability, integration-before-closure, and engaged-participant settlement.

The same export showed that the new Room's default A/B/C `profile_snapshot` values were an older early-triad built-in generation. Their exact SHA-256 values were:

- A: `cfad300ba057c99c9839765615bd8851cd1c4960a2f0714cae57c70f810b0480`
- B: `97c822fcd38b6e408158b6d040d1a517c8030530af1f80033fdbd9d8b22c4bac`
- C: `7bfe1e10d35c084e1eb8aac8013459fdc3ac48d3824ebd9d728a9ea9ceb0c6cb`

Those snapshots predated the current selective-invocation wording and D-020 C coordination/integration guidance even though the runtime mechanics themselves were current.

PR #4 implemented a separate `triad_profiles_v2` migration for only those exact observed hashes. The migration:

- updates matching A/B/C default profile rows to the current built-in text;
- updates matching default-profile Room snapshots/effective instructions only when the Room is not archived or sealed and has no Room override;
- preserves all non-matching custom defaults, Room overrides, archived Rooms, and sealed predecessors;
- records the migration in affected Room metadata;
- is idempotent;
- causes newly created Rooms after migration to inherit current A/B/C snapshots.

The first two PR CI attempts each failed only inside the newly added test harness before completing its assertions: one omitted an empty helper parameter tuple, and one omitted the C instruction constant import. Production migration bytes were unchanged. The corrected exact PR head `7ce13c3e8688f9fdd932fa772e165f26dd348008` passed GitHub Actions run `34706196525` with **138 passed, 2 warnings**.

PR #4 squash-merged to canonical `main` as:

`bd4ea0fc21fa5f93db68a8df93a9f12f296c03f5` — `Repair early-triad profile migration`

Post-merge GitHub Actions run `34706293089` passed **138 tests, 2 warnings**.

**Status:** IMPLEMENTED / VERIFIED.

Post-repair local verification was then performed against a newly created Personal Room after pull/restart. The export showed:

- A, B, and C all inherited the current D-020 built-in profile text rather than the observed stale early-triad generation;
- A and B had no Room override;
- C was the designated starter;
- the Round executed exactly **one** agent turn;
- only C consumed Round context and recorded an outcome;
- A and B had `context_consumed_at = null` and `last_outcome = null`;
- C FINISHed with exactly `C-ONLY-OK`;
- the Round closed successfully after the sole engaged participant settled.

Observed post-migration profile SHA-256 values in that fresh Room were:

- A: `5d12def051f832aa83ef2bb929d6d3aa9301b7f9eb387dc8eaece1c30b494493`
- B: `aa769b9385fa8ab277769abf45963de732f16a1443d5ff6514f599f5f4def6de`
- C: `b07be1545126c2061f82c2128195a091f991ab38a9b0ebbeb92b1d22e7614e62`

This closes the remaining local-adoption verification and also supplies fresh live evidence for C-only engaged-participant settlement. I-006 is closed.
