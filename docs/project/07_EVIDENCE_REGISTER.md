# Codex Room — Evidence Register

**Initialized:** 2026-09-08  
**Last updated:** 2026-09-18  
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


### E-030 — P4.1 deterministic file assertions
**Date:** 2026-09-12  
**Kind:** Current-source implementation + exact-diff review + GitHub PR/CI

P4.1 begins the deterministic product-capability phase with one bounded vertical slice rather than a general tool framework.

Implemented capability:

- `codex_room.capabilities.assert_file` performs read-only exact checks for regular-file existence, SHA-256 equality, JSON validity, and required top-level JSON keys;
- paths are required to be workspace-relative and path resolution rejects traversal outside the invocation workspace;
- one compact JSON result carries a stable capability marker, overall `ok`, subject metadata, and per-assertion results;
- false assertions return a normal result; malformed requests return a structured invalid-request result;
- a Windows `codex-room-cap.cmd` wrapper invokes the repository-owned implementation through the Codex Room virtual environment;
- `Start-Codex-Room.cmd` exposes the wrapper to inherited agent command execution through PATH;
- normal agent delivery prompts advertise the capability and explicitly preserve the cognition boundary: agents choose assertions and interpret significance;
- the adapter promotes only recognized structured output from a direct, non-chained `codex-room-cap assert-file` command into `deterministic_capability` activity metadata;
- arbitrary command output remains hidden from Room telemetry.

Review tightened two boundaries before verification: an existence assertion now requires a regular file rather than merely an existing path, and capability telemetry rejects commands that only mention the capability or chain additional shell operations.

Exact PR head:

`ae5a57b6d5ae4a046e36bf81064875375fec4cc6`

GitHub Actions run `34709164489`: **149 passed, 2 warnings**.

PR #5 squash-merged to canonical `main` as:

`40afe50b97bf7333a397f1b06dd7a4e3492bdb4b` — `P4.1: Add deterministic file assertions`

Post-merge GitHub Actions run `34709284545`: **149 passed, 2 warnings**.

**Status:** CORE capability IMPLEMENTED / VERIFIED deterministically.

A first live Room smoke attempt was then run on the merged build. The Room created three persistent participants, designated C as starter, invoked only C, and closed after one C turn with exactly `P4.1-CAPABILITY-OK`. A/B did not consume context or record outcomes. However, the export contained no `tool_activity` or `deterministic_capability` event. The agent's final claim therefore did not independently prove the exact capability invocation/result.

Inspection of the exact pinned SDK release source (`openai-codex==0.147.0`, release source commit `025a88adbd7ae4d448fc938b28d0446eb1753317`) identified the cause: completed Python SDK ThreadItems use camelCase discriminators including `commandExecution` and `fileChange`, while Codex Room's `_safe_activity()` accepted only snake_case names. This mismatch also meant ordinary real command/file/tool activity had been silently omitted from Room telemetry.

PR #6 repaired the adapter boundary by normalizing the pinned SDK's camelCase activity types to Codex Room's stable snake_case telemetry vocabulary while retaining compatibility with existing snake_case test/legacy shapes.

Exact PR #6 head:

`92a9fcefbbcb9228a98cc8074415e32af6ffe116`

GitHub Actions run `34709739325`: **150 passed, 2 warnings**.

PR #6 squash-merged to canonical `main` as:

`d54565afc459b251fa084910086e74123810dce0` — `P4.1: Normalize SDK activity item types`

Post-merge GitHub Actions run `34709822193`: **150 passed, 2 warnings**.

A second live Room smoke on the activity-type repair then showed:

- C was again the only invoked/consuming participant;
- the Round closed after one C FINISH with exactly `P4.1-CAPABILITY-OK`;
- a `file_change` tool-activity event was exported;
- a `command_execution` tool-activity event was exported;
- no `deterministic_capability` event was exported.

This proves the camelCase activity-type normalization repaired the broader telemetry loss, while isolating the remaining issue to capability provenance recognition. The pinned Codex command presentation is shell-wrapped on Windows; its parsed `command_actions` preserve the inner PowerShell script. PR #7 therefore authenticates capability invocations against those parsed inner commands, still requiring a direct `codex-room-cap assert-file` call and rejecting pipes, semicolons, `&&`, and forged `echo` forms.

Exact PR #7 head:

`0cdf2293f4f036c5557dd8bae800de2cb88c112c`

GitHub Actions run `34711798262`: **152 passed, 2 warnings**.

PR #7 squash-merged to canonical `main` as:

`9909d1525a4ddef495a783c340cfd6bddf54c90d` — `P4.1: Recognize shell-wrapped capability calls`

Post-merge GitHub Actions run `34711878505`: **152 passed, 2 warnings**.

A third fresh live Room smoke on the PR #7 build closed the remaining verification gap.

Observed export evidence:

- Room `room_a28f1dc7eb2d450bb081f6cddc7bddb0`, Round `round_fef49b49d92f46bd8d8d1170db31400d`;
- C was the designated starter and sole invoked/consuming participant; A/B had `context_consumed_at = null` and `last_outcome = null`;
- the Round executed exactly **one** agent turn;
- a completed `file_change` tool-activity event recorded creation work;
- the next tool-activity event recorded:
  - `type: deterministic_capability`;
  - `status: completed`;
  - `capability: assert_file`;
  - `ok: true`;
- the structured capability result recorded `p4_probe.json` with `exists: true`, `is_file: true`, and all four requested checks true: regular-file existence, JSON validity, required key `probe`, and required key `status`;
- C FINISHed exactly `P4.1-CAPABILITY-OK`;
- the Round closed normally with reason `mutual_finish`.

This independently proves agent discovery/invocation, inherited launcher/wrapper execution, exact deterministic result capture, safe promotion into durable Room telemetry, and C-only settlement on the merged implementation.

**Status:** P4.1 COMPLETE — IMPLEMENTED / VERIFIED end to end on 2026-09-12.


### E-031 — P4.2 capability registry and discovery
**Date:** 2026-09-12  
**Kind:** Current-source implementation + exact-diff review + GitHub PR/CI

P4.2 makes deterministic capabilities first-class discoverable CORE objects rather than hard-coded prompt knowledge.

Implemented:

- `CapabilitySpec` manifest model with stable ID, description, origin/scope, version, implementation SHA-256, input/output schemas, permission/side-effect declaration, verification metadata, and invocation guidance;
- static `CORE_CAPABILITIES` registry, initially containing the already verified `assert_file`;
- compact `codex-room-cap list` output so inventory growth does not automatically inject every full schema into model context;
- detailed `codex-room-cap inspect CAPABILITY_ID`;
- generic `codex-room-cap invoke CAPABILITY_ID --input-json JSON_OBJECT`;
- backward-compatible P4.1 `assert-file` alias routed through the registered implementation;
- invocation results carry capability version and implementation SHA-256;
- safe telemetry distinguishes `deterministic_capability_registry` discovery from `deterministic_capability` execution;
- agent prompt guidance now expresses the judgment boundary for deterministic software, tells agents to discover the current registry rather than hard-coding a known tool, and—after live verification exposed an ad hoc-command preference—requires checking the registry before ad hoc mechanical execution and using an adequate registered capability when one exists.

D-022 separately settles the future direction: a small default CORE library plus agent-created registered capabilities, lineage rollover continuity, and possible Personal/CORE promotion. Those later lifecycle/persistence features are not claimed as P4.2 implementation.

PR #8 squash-merged to canonical `main` as:

`aeed9d93d16e4933730b1bbea04b54581dbe62d7` — `P4.2: Add capability registry and discovery`

The first post-merge GitHub Actions run `34713909186` failed one newly added regression assertion with `KeyError: 'permissions'`. The list response had intentionally been made compact immediately before merge, but the new test still expected detailed permission fields there. Inspection showed the detail remained available through `inspect`; no production runtime source change was required.

PR #9 changed only `tests/test_capabilities.py` to require that detailed fields are absent from the compact list and present in the inspected manifest.

Exact PR #9 head:

`d4e04e190eac2c594dcd2c8745135f61484c4367`

GitHub Actions run `34714005661`: **161 passed, 2 warnings**.

PR #9 squash-merged as:

`78dd8da418f2c29c37b94324d66bbe8c99da39b3` — `P4.2: Fix compact-list regression test`

Post-merge canonical-`main` GitHub Actions run `34714080693`: **161 passed, 2 warnings**.

A subsequent fresh live Room used the exact P4.2 discovery probe without naming `assert_file`. C alone created the file and FINISHed `P4.2-DISCOVERY-OK`, but the durable tool evidence contained `file_change` plus ordinary `command_execution` and no `deterministic_capability_registry` or `deterministic_capability` event. This did not satisfy the end-to-end stop condition and demonstrated that the then-current guidance still allowed ad hoc mechanical execution to bypass an adequate registered capability.

PR #10 changed only `codex_room/orchestrator.py` deterministic-capability guidance and the existing prompt regression test. It requires the agent to check the registered inventory before implementing or running an ad hoc mechanical command, use an adequate registered capability when one exists, and reserve ad hoc deterministic execution for cases where no registered capability is adequate or registry use is materially less suitable.

Exact PR #10 head:

`c4b3f5cf03a7684be1414ddd051a49b6d9a1cc69`

GitHub Actions run `34718435578`: pytest step passed.

PR #10 squash-merged as:

`745e76b305cab38607e6035f4fb670c3ea8f2fd4` — `P4.2: prefer registered capabilities before ad hoc mechanics`

Post-merge canonical-`main` GitHub Actions run `34718498032`: pytest step passed.

The live evidence therefore supports **OBSERVED ISSUE → IMPLEMENTED / VERIFIED deterministic repair**, while live registry-first behavior still requires one rerun.

A post-PR-#10 fresh live Room then changed its execution pattern: C alone created the probe file, executed **two** commands, FINISHed exactly `P4.2-DISCOVERY-OK`, and closed normally. Both command tool events were still exported only as generic `command_execution`. Because arbitrary command text is intentionally excluded from exports, this evidence does not prove what those commands were; it does establish that the P4.2 end-to-end telemetry stop condition still was not met and is consistent with capability commands arriving only in an outer Windows shell representation.

Inspection of the exact pinned `openai-codex==0.147.0` SDK source confirmed all parsed `CommandAction` variants carry a `command` string, which the adapter already inspects. The remaining unhandled safe fallback was therefore a completed command item whose useful provenance is present only in the outer PowerShell command string.

PR #11 preserved the existing direct capability executable restriction and added a narrow fallback: if direct parsing fails, Codex Room may unwrap a known `powershell` / `powershell.exe` / `pwsh` / `pwsh.exe` `-Command` or `-c` wrapper and then re-apply the same direct, non-chained capability parser to the entire inner script. Chained `;`, `|`, or `&&` forms remain unpromoted. Regression tests cover registry list, registered invoke, and forged/chained rejection with empty `command_actions`.

Exact PR #11 head:

`8304d0a46cab644cb5069a03730af1de057ff1ad`

GitHub Actions run `34719562400`: **164 passed, 2 warnings**.

PR #11 squash-merged as:

`80654078567cbdc997c09586994f1d67a1cc784c` — `P4.2: recognize direct capability calls through PowerShell wrappers`

The first canonical-main run `34719622155` failed only the pre-existing `tests/test_orchestrator.py::test_stop_before_lease_expiry_cancels_without_false_error_or_retry` timing test after 163 other tests passed; no P4.2 parser/provenance regression test failed. A rerun of the exact same merged commit passed **164 tests, 2 warnings**. This is recorded as a hosted test flake, not as evidence that the failed attempt itself was green.

The PR #11 provenance repair is therefore **IMPLEMENTED / VERIFIED deterministically**.

A final fresh live Room on the post-PR-#11 runtime satisfied the P4.2 end-to-end stop condition.

Observed export evidence:

- Room `room_db9f70efd99d4307a4410e22a8908ea5`, Round `round_cf33e6b2894e4b309b2071aa565e3aee`;
- the user prompt required exact file/JSON/key verification but did **not** name `assert_file` or any registry command;
- C was the designated starter and sole invoked/consuming participant; A/B both had `context_consumed_at = null` and `last_outcome = null`;
- the Round executed exactly one agent turn;
- telemetry recorded completed `deterministic_capability_registry` `list`, returning `assert_file` with origin/scope `core`, version `1`, and implementation SHA-256 `6f34376f64110d61d18f278597196b69c1214bba1a8c048c951c3332f049f7b3`;
- telemetry then recorded completed registry `inspect` for `assert_file`, including its description, read-only/no-network/no-external-process permissions, no side effects, version/hash identity, and verified evidence `E-030`;
- C created `p4_discovery_probe.json`;
- the first registered invocation was safely surfaced as a failed `deterministic_capability` event with structured `invalid_request` because its input JSON was malformed;
- C corrected the request within the same turn and retried through the registry path;
- the successful `deterministic_capability` event recorded `capability: assert_file`, `capability_version: "1"`, the same implementation SHA-256, and `ok: true`;
- the structured result independently recorded the subject as an existing regular file and all requested checks true: existence, JSON validity, required key `probe`, and required key `status`;
- C FINISHed exactly `P4.2-DISCOVERY-OK`;
- the Round closed normally with reason `mutual_finish`.

The malformed first invocation is a recoverable call-construction error, not a failure of the capability or discovery path: the error was explicit and structured, no unsupported fallback was used, and the corrected registered invocation produced the required exact result.

This final Room independently proves agent recognition of a deterministic subproblem, registry discovery without user-supplied capability identity, manifest inspection, registered invocation, exact version/hash continuity across discovery and execution, structured error observability, successful retry, durable result telemetry, and C-only settlement.

**Status:** P4.2 COMPLETE — IMPLEMENTED / VERIFIED end to end on 2026-09-12.

Because PR #9 changed tests only, the original P4.2 registry/runtime implementation source bytes were introduced by PR #8; PR #10 later changed only the institutional selection guidance in `orchestrator.py` plus its regression test.

### E-032 — P4.3 minimal CORE standard library
**Date:** 2026-09-12  
**Kind:** Current-source implementation + GitHub PR/CI + planned bounded live verification

P4.3 is implementing the smallest broadly useful CORE deterministic standard library under D-022. The initial admitted sequence is substrate generalization, then `find_files`, `search_text`, `compare_files`, followed by bounded live evaluation before any further CORE promotion.

#### P4.3a — Generic bounded capability-result telemetry

Before adding capabilities whose useful results are not shaped like `assert_file`, current source review showed that `CodexAgentAdapter._safe_capability_activity()` durably whitelisted only the common capability envelope plus `subject`, `checks`, and `error`. A future capability could execute successfully yet lose its capability-specific structured evidence in Room telemetry.

PR #12 added a generic bounded declaration path:

- `CapabilitySpec` now declares `durable_result_fields`;
- the declaration is included in the capability manifest and exact implementation SHA-256 calculation;
- generic registered invocation results carry the declaration;
- the adapter persists only the common identity/status envelope plus explicitly declared result fields;
- results without a declaration retain the P4.1/P4.2 legacy `subject` / `checks` path;
- malformed declarations are not promoted to deterministic-capability telemetry;
- arbitrary shell stdout/stderr remains excluded;
- declared durable evidence above **64 KiB** is replaced by explicit truncation metadata rather than persisted unbounded;
- registry inspect telemetry includes the declaration.

Exact PR #12 head:

`e35d835d54a7af72e4040d5ef86dc0dcaae918b8`

GitHub Actions PR run `34721307863`: **167 passed, 2 warnings**.

PR #12 squash-merged as:

`2b697de8597bc06cfe21044854869273fb0cceee` — `P4.3a: generalize bounded capability telemetry`

Canonical-main GitHub Actions run `34721368173`: **167 passed, 2 warnings**.

**P4.3a status:** IMPLEMENTED / VERIFIED.

#### P4.3b — `find_files`

PR #13 added registered CORE `find_files` version `1` as the first new standard-library primitive.

Implemented/verified properties:

- scan roots are resolved inside the Room workspace; escapes are rejected;
- only regular files are returned;
- file and directory symlinks are never followed;
- directory traversal errors fail visibly instead of silently dropping subtrees;
- include/exclude glob filters use host-independent POSIX-style matching with zero-depth `**/` support and normalize Windows backslashes at the registered-input boundary;
- hidden files/directories are excluded unless explicitly requested;
- optional minimum/maximum size filters are exact byte comparisons;
- results use deterministic sorted depth-first traversal;
- one invocation returns 100 matches by default and at most 200;
- match payload is capped at **48 KiB** with explicit `result_bytes` truncation;
- traversal is capped at **100,000 entries** with explicit `scan_limit` truncation;
- exceeding the requested result count reports explicit `max_results` truncation;
- the result carries only structured path/size evidence and declares `evidence` as its durable result field;
- JSON byte accounting uses escaped JSON representation so POSIX surrogate-escaped filenames cannot break telemetry sizing;
- permissions are workspace-read only, with no workspace write, network, or external process.

Exact PR #13 head:

`4f5c244437c99130362f3e86e9f618198acb18c9`

GitHub Actions PR run `34721808859`: **186 passed, 2 warnings**.

PR #13 squash-merged as:

`56d08cd733fdc4598fc878b3778bce664e193aca` — `P4.3b: add bounded find_files capability`

Canonical-main GitHub Actions run `34721893200`: **186 passed, 2 warnings**.

**P4.3b status:** IMPLEMENTED / VERIFIED.

#### P4.3c — `search_text`

PR #14 added registered CORE `search_text` version `1` as a bounded literal text-search primitive.

Implemented/verified properties:

- candidate discovery composes the already verified `find_files` path and propagates any candidate truncation;
- queries are single-line literal UTF-8 strings rather than regex programs;
- case sensitivity is explicit and defaults to true;
- search roots remain workspace-confined, with the inherited file-glob/hidden/symlink protections from `find_files`;
- only UTF-8, NUL-free text is searched; non-text candidates are counted and skipped;
- oversized candidates are explicitly reported as incomplete rather than silently excluded;
- candidate files are 100 by default / 200 maximum;
- matches are 50 by default / 100 maximum;
- per-file search size is 2 MiB by default / 10 MiB maximum;
- aggregate reads are capped at 20 MiB;
- runtime match excerpts are capped to 240 characters each and total transient match evidence to 32 KiB;
- durable match locations are independently capped at 16 KiB;
- the raw query is not persisted in durable Room telemetry; durable evidence carries its SHA-256, length, exact locations, counts, limits, and truncation status;
- runtime excerpts are deliberately outside `durable_result_fields`, and adapter regression coverage proves excerpt content is dropped from durable telemetry;
- permissions are workspace-read only, with no workspace write, network, or external process.

Exact PR #14 head:

`0afb3b7a4b2dc52e451543ba1a25d51cf015155b`

GitHub Actions PR run `34722267899`: **216 passed, 2 warnings**.

PR #14 squash-merged as:

`eb6c29f346081affa61eb412006f460426bafc40` — `P4.3c: add bounded search_text capability`

Canonical-main GitHub Actions run `34722497151`: **216 passed, 2 warnings**.

**P4.3c status:** IMPLEMENTED / VERIFIED.

#### P4.3d — `compare_files`

PR #16 added registered CORE `compare_files` version `1` as the fourth initial standard-library primitive.

Implemented/verified properties:

- both inputs are Room-workspace-relative regular files;
- exact byte equality is computed independently of the text-diff path;
- SHA-256 and exact byte size are reported for both files;
- each comparable file is capped at **50 MiB**;
- equal files avoid unnecessary text-diff work;
- unequal files up to **2 MiB** each may receive a UTF-8 text comparison;
- UTF-8 text comparison is capped at **20,000 lines per file**;
- runtime unified diff output is capped at **200 lines** and **32 KiB**;
- diff context is configurable from 0 through 10 lines, defaulting to 3;
- binary/NUL or invalid UTF-8 inputs retain exact byte comparison and report text status `non_text`;
- oversized text-diff candidates retain exact byte comparison and report `size_limit`;
- line-heavy text retains exact byte comparison and reports `line_limit`;
- line-ending-only differences are explicitly distinguishable as `byte_equal: false` with `text_lines_equal: true`;
- transient unified-diff content is deliberately outside `durable_result_fields`; durable Room evidence retains only paths, sizes, SHA-256 values, byte equality, and bounded text-diff status/count metadata;
- adapter regression coverage proves diff content is dropped from durable telemetry;
- permissions are workspace-read only, with no workspace write, network, or external process.

Exact PR #16 head:

`6e5b7161dd2d75c33e1527db5d51ce552d0e4888`

GitHub Actions PR run `34722624669`: **235 passed, 2 warnings**.

PR #16 squash-merged as:

`260431ad7ca64ed0c9f1f3b3bf0122ca98e4de6c` — `P4.3d: add bounded compare_files capability`

Canonical-main GitHub Actions run `34722758182`: **235 passed, 2 warnings**.

**P4.3d status:** IMPLEMENTED / VERIFIED.

**Remaining P4.3 limit:** the initial four-capability CORE library is code-complete but still requires one bounded fresh-Room live evaluation before P4.3 can close.

#### P4.3e — First bounded live evaluation and auditable-call repair

Fresh Room `room_0b855adf7e3f49ef870b6a6f6b60bc24`, Round `round_5efc6d7bb14d46c8b4727ac0077db083`, ran the prescribed four-capability probe without naming any capability or registry command.

Observed durable export evidence:

- C was the designated starter and sole consuming participant;
- A and B retained `context_consumed_at: null` and no outcome;
- registry `list` completed and durably identified `assert_file`, `compare_files`, `find_files`, and `search_text`, all CORE scope/version `1`, with implementation SHA-256 values;
- after registry discovery, telemetry recorded two completed generic `command_execution` events, one completed `file_change`, one failed generic `command_execution`, and one completed generic `command_execution`;
- there were **no** `deterministic_capability` invocation events and no structured durable invocation results for any of the four capabilities;
- C FINISHed exactly `P4.3-LIBRARY-OK`;
- the one-turn Round closed normally with `mutual_finish`.

The attempt therefore did **not** satisfy the P4.3e stop condition. Because generic command text/output is intentionally omitted from Room exports, the evidence does not prove whether C replaced the registered capabilities with ad hoc shell verification or issued capability operations in a batched/chained command shape that safe telemetry deliberately refuses to promote. The existing adapter already promotes registered invocation IDs generically, including regression coverage for the newer result shapes, so no capability-specific telemetry defect was demonstrated.

PR #17 made the narrow behavioral/provenance repair:

- each registry list/inspect operation and each capability invocation must run as its own command execution;
- capability operations must not be chained with other shell commands or another capability call;
- when a task has multiple independent mechanical subproblems, agents should compose adequate registered capabilities by invoking the relevant capabilities separately rather than replacing them with one ad hoc script;
- capability implementations, registry contents, command parser, and arbitrary-shell-output safety boundaries are unchanged.

Exact PR #17 head:

`ab578295ae9da339983d8f59079a0683a795e9f8`

GitHub Actions PR run `34723435009`: **235 passed, 2 warnings**.

PR #17 squash-merged as:

`d65da0bd1399b0cd5511cf0653162e48af7ae546` — `P4.3e: keep capability invocations auditable`

Canonical-main GitHub Actions run `34723499027`: **235 passed, 2 warnings**.

**PR #17 repair status:** IMPLEMENTED / VERIFIED deterministically.

**P4.3e final live verification**

Fresh post-PR-#17 Room `room_2077937c86524ac3aaced1918dbe6050`, Round `round_a65e1ca8eb3d48248c06e1730e21923e`, repeated the unchanged prescribed probe.

Observed durable export evidence:

- the user prompt named no capability or registry command;
- C was the designated starter and sole consuming participant;
- A and B retained `context_consumed_at: null` and no outcome;
- registry `list` durably identified all four CORE capabilities as version `1` with implementation SHA-256 identities:
  - `assert_file` — `c79294869ae9b3d31b0e307dea5cc67d1f23d00f7ac0ff8385f3273206fde5cd`;
  - `compare_files` — `d5dba06167ef60cdb037792a6c329bc59cb5a46668173fd54ec0b88d4cedee1b`;
  - `find_files` — `8e377fef5c9a31d3e9183cddfa3c27bab9a6c1aae0b35949b6570f7250b60f31`;
  - `search_text` — `d04df21b054865016ab726646ef5f1fdfedc6adef8a1aade79bfa0b75499c4d9`;
- C separately inspected all four manifests, preserving CORE scope, read-only/no-network/no-external-process permissions, side effects `none`, and the same version/hash identities;
- fixture creation recorded one completed `file_change`;
- the first `find_files` invocation had malformed JSON and returned a structured `invalid_request`; C corrected the call without ad hoc fallback;
- successful `find_files` invocation returned exactly three sorted matches:
  - `p4_core_probe/alpha.txt`;
  - `p4_core_probe/beta.txt`;
  - `p4_core_probe/nested/gamma.txt`;
  with `returned_count: 3`, no truncation, and the expected implementation identity;
- successful `search_text` invocation returned exactly two matches for the probe literal:
  - `p4_core_probe/alpha.txt`, line 2, column 1;
  - `p4_core_probe/beta.txt`, line 2, column 1;
  with `match_count: 2`, no truncation, and the expected implementation identity;
- successful `compare_files` invocation reported `byte_equal: false`, exact per-file SHA-256/size evidence, bounded text-diff status `available`, and the expected implementation identity;
- successful `assert_file` invocation reported `p4_core_probe/data.json` as an existing regular file, valid JSON, with required top-level keys `probe` and `status` all true, plus the expected implementation identity;
- C FINISHed exactly `P4.3-LIBRARY-OK`;
- the one-turn Round closed normally with `mutual_finish`.

The malformed first `find_files` call is a recoverable call-construction error, analogous to the accepted P4.2 malformed-input proof: it was durably observable, corrected within the same turn, and followed by the required successful registered invocation. It does not weaken the successful end-to-end result.

**P4.3e status:** COMPLETE / VERIFIED end to end — 2026-09-12.

**P4.3 status:** COMPLETE / IMPLEMENTED / VERIFIED end to end — 2026-09-12.

### E-033 — P4.4a custom capability package and exact identity
**Date:** 2026-09-13  
**Scope:** P4.4a package/identity substrate only; no custom registration, publication, discovery, inheritance, or invocation.

PR #19 introduced a deliberately narrow custom-capability draft model before implementing trusted registration.

Implemented evidence boundary:

- fixed Room draft location: `.codex-room/capability-drafts/<id>/`;
- portable lowercase capability-ID namespace with Windows-reserved names rejected;
- package schema v1 is lineage-scoped and contains exactly `manifest.json` plus one `capability.py`;
- runtime declaration is fixed to Python / `stdio-json-v1`;
- input/output contracts must describe JSON objects; output must require boolean `ok`;
- `durable_result_fields` must be unique, non-reserved, and declared in the output contract;
- permissions must declare exactly `workspace_read`, `workspace_write`, `network`, and `external_process` as booleans;
- side effects require an explicit bounded declaration;
- draft path components reject symlinks and non-directories; manifest/entrypoint must be bounded regular non-symlink files; extra package entries are rejected;
- the Python entrypoint must be UTF-8, NUL-free, and syntax-valid without being executed during package validation;
- exact identity records manifest SHA-256, implementation SHA-256, and a domain-separated combined package SHA-256 over the exact manifest and executable bytes;
- package inspection explicitly records permission enforcement as `ambient_room_sandbox` with `per_capability_enforcement: false`, preserving the distinction between declared permissions and actual per-capability OS enforcement.

The first PR-head CI run `34760645153` failed one newly added parametrized test because the implementation rejected a malformed output contract one validation stage earlier than the test's expected error text. The implementation behavior was correct: required field `ok` referenced a removed property. Only the expected error-message pattern changed.

Exact repaired PR #19 head:

`39ead0212319774b987b00bc661b773e6b99c807`

GitHub Actions PR run `34760718140`: **261 passed, 2 warnings**.

PR #19 squash-merged as:

`574edbfeaf5c5ae9053eae1825a0fe8f6fb728aa` — `P4.4a: define custom capability package identity`

Canonical-main GitHub Actions run `34760790346`: **261 passed, 2 warnings**.

**P4.4a status:** COMPLETE / IMPLEMENTED / VERIFIED.

**Remaining P4.4 boundary:** a structurally valid draft is still ordinary unregistered Room code. P4.4b must define adequate deterministic verification evidence and immutable content-addressed publication before any custom package becomes a registered capability.

### E-034 — P4.4b custom capability verification and immutable publication
**Date:** 2026-09-13  
**Scope:** P4.4b verification/publication substrate only; ordinary capability discovery/invocation remains CORE-only.

PR #20 added the trust transition between a structurally valid P4.4a draft and immutable published registration evidence.

Verification boundary:

- 1–16 exact deterministic cases per verification run;
- each case supplies a JSON-object input, exact JSON-object expected output, and optional bounded UTF-8 workspace fixture files;
- expected outputs must include boolean `ok` and every declared durable-result field;
- case JSON is bounded to 64 KiB each; fixture inventory is capped at 32 files, 64 KiB per file, and 256 KiB total;
- exact copied `capability.py` bytes run through the current Python interpreter in isolated mode with a fresh case workspace;
- default per-case wall time is 5 seconds;
- stdout/stderr use temporary-file capture with live size monitoring; a process crossing the 64 KiB output bound is killed rather than allowed to accumulate unbounded captured output;
- success requires zero exit, empty stderr, one UTF-8 JSON object with boolean `ok`, and exact equality to the expected output;
- verification re-loads/re-hashes the draft after execution and fails if package identity changed during the test run;
- the durable receipt records package/manifest/implementation identity, case-plan SHA-256, case names, and input/expected/observed/fixture SHA-256 values without retaining raw test content;
- the receipt itself has an exact verification SHA-256 and reparses with self-hash validation.

Publication boundary:

- host-side publication never executes candidate code;
- exact verified package bytes publish under `data/custom-capabilities/packages/<package_sha256>/`;
- verification receipts publish under content-addressed verification SHA-256 filenames;
- registration records publish under content-addressed registration SHA-256 filenames;
- registration identity binds Room ID, capability ID/version, package SHA-256, manifest SHA-256, implementation SHA-256, and verification SHA-256;
- existing content-addressed objects are re-verified byte-for-byte; corruption/conflict fails visibly;
- repeating the same exact publication is idempotent;
- publication does not yet bind the custom capability into normal Room `list` / `inspect` / `invoke`.

Exact reviewed PR #20 head:

`617c41e95cdbb775b065a8bb47c4ced5c71f0f4c`

GitHub Actions PR run `34761184584`: **277 passed, 2 warnings**.

PR #20 squash-merged as:

`7ecf05f206043116cf77a9f6a8581b6eb85136be` — `P4.4b: verify and publish custom capabilities`

Canonical-main GitHub Actions run `34761250928`: **277 passed, 2 warnings**.

**P4.4b status:** COMPLETE / IMPLEMENTED / VERIFIED.

**Remaining P4.4 boundary:** published registrations are durable provenance objects but are not yet active Room registry bindings. P4.4c must resolve verified immutable custom registrations through the same normal discovery/invocation vocabulary as CORE while rejecting collisions/ambiguity and preserving safe telemetry.

### E-035 — P4.4c lifecycle-safe Room binding and dynamic custom registry
**Date:** 2026-09-13  
**Scope:** P4.4c Room binding / unified CORE + custom discovery and invocation. Rollover inheritance and live agent authoring behavior are outside this evidence item.

PR #21 completed the activation boundary from a verified custom draft to one Room's ordinary capability registry.

Authority-boundary result:

- the sandboxed `codex-room-cap register <id> --cases-file <path>` command verifies exact draft bytes using the P4.4b gate and emits a bounded self-hashed registration request;
- the command does not publish or bind protected `data/custom-capabilities/` state itself;
- exact-diff review caught and removed an earlier pre-CI implementation that attempted protected publication directly from the agent's `workspace_write` sandbox;
- after the agent turn passes lifecycle/staleness checks and delivery settlement, `RoomRuntime` host settlement reparses the receipt, requires the current draft/package hashes to match, publishes immutable package / verification / registration objects, and writes the protected Room binding;
- host settlement first recognizes an already-bound exact receipt/package identity, making recovered-result replay idempotent even if mutable draft files later change;
- a draft changed between sandbox verification and first host settlement fails registration rather than publishing different bytes.

Registry/invocation result:

- binding schema v1 is single-assignment per Room/capability ID;
- same exact binding is idempotent; a different registration for an already-bound ID fails visibly;
- CORE/custom ID collisions fail visibly;
- only canonical `data/rooms/<room_id>/shared` workspaces receive the custom overlay;
- bound custom capabilities appear in the same sorted `codex-room-cap list` inventory and expose normal `inspect` / `invoke` operations;
- custom inspection reports lineage scope, exact implementation/package/registration identity, verification receipt identity/case-plan metadata, declared permissions/side effects, and the explicit no-per-capability-enforcement boundary;
- custom invocation executes immutable published `capability.py` bytes rather than mutable draft bytes;
- published package/registration/verification records are revalidated before use;
- custom invocation returns the normal capability envelope with capability version, implementation SHA-256, package SHA-256, registration SHA-256, verification SHA-256, and declared durable-result fields;
- safe Room telemetry preserves those bounded provenance fields and only manifest-declared durable result fields, dropping undeclared transient output;
- registration-request telemetry preserves only the bounded receipt identity/hash evidence required for host settlement, not raw verification fixture/input/output bodies.

Exact reviewed PR #21 head:

`8ebfad68e1210d7191f7274a450ed76d29ae2e8e`

GitHub Actions PR run `34762414175`: **291 passed, 2 warnings**.

PR #21 squash-merged as:

`5e2d90b92197ce58866af0ddaceff922d2b16c9e` — `P4.4c: bind verified custom capabilities into Room registry`

Canonical-main GitHub Actions run `34762490876`: **291 passed, 2 warnings**.

**P4.4c status:** COMPLETE / IMPLEMENTED / VERIFIED deterministically.

**Remaining P4.4 boundary:** A/B/C do not yet receive explicit package-authoring / verification / host-pending guidance, and no fresh Room has yet demonstrated autonomous custom-capability creation, later rediscovery, and registered invocation. Those are P4.4d / P4.4e.

### E-036 — P4.4d token-efficient agent custom-capability authoring behavior
**Date:** 2026-09-13  
**Scope:** P4.4d deterministic authoring reference and runtime guidance. No live Room creation/invocation proof is claimed here.

PR #22 added the agent behavior needed to use the P4.4a–c custom-capability substrate without hard-wiring task-specific software or injecting the full package schema into every model turn.

Implemented behavior:

- existing guidance still requires agents to check registered capability inventory before ad hoc mechanical work;
- custom capability creation is selective: it is suggested only when no adequate registered capability exists and reusable deterministic software is justified by reuse, reliability, provenance, or mechanical-complexity value;
- the always-loaded instruction points to standalone `codex-room-cap authoring` instead of repeating the full authoring contract on every turn;
- `authoring` returns registry operation/schema identity plus:
  - draft root `.codex-room/capability-drafts/<id>`;
  - package files `manifest.json` and `capability.py`;
  - portable lowercase ID pattern plus Windows-reserved-name warning;
  - manifest/code byte limits derived from `MAX_MANIFEST_BYTES` / `MAX_ENTRYPOINT_BYTES`;
  - all required manifest fields and fixed lineage/Python/`stdio-json-v1` values;
  - object input/output contract rules, required boolean `ok`, reserved registry-envelope output names, durable-result-field rules, exact permission declaration keys, and side-effect declaration requirement;
  - verification case count/JSON/fixture bounds derived from P4.4b implementation constants;
  - exact registration command shape;
  - explicit host-pending settlement semantics;
  - explicit statement that permission declarations are not per-capability OS enforcement;
- safe Room telemetry promotes an authoring lookup only as compact registry evidence with `authoring_schema_version: 1`, omitting the detailed reference payload;
- runtime guidance requires `authoring` and `register` to run as standalone auditable commands;
- after successful `register`, the agent is told not to treat the capability as active until the turn settles;
- a later turn must rediscover the custom capability through normal `list` / `inspect` before invoking it.

Exact reviewed PR #22 head:

`167cb4361ac8d1c36d858fb9d6dbd5fb18d65747`

GitHub Actions PR run `34762737011`: **294 passed, 2 warnings**.

PR #22 squash-merged as:

`8afa54e23850441690a6071cb7fff01e32a2ab46` — `P4.4d: teach agents bounded custom capability authoring`

Canonical-main GitHub Actions run `34762827607`: **294 passed, 2 warnings**.

**P4.4d status:** COMPLETE / IMPLEMENTED / VERIFIED deterministically.

**Remaining P4.4 boundary:** P4.4e must provide fresh-Room evidence that an agent independently chooses this path, produces a valid custom package/test suite, reaches host-bound registration after settlement, then later rediscovers and invokes the immutable registered capability correctly.

### E-037 — P4.4e first live custom-capability exercise and robust input-transport repair
**Date:** 2026-09-13  
**Scope:** First live P4.4e Room plus the bounded CORE repair exposed by its second Round. P4.4e is not closed by this evidence item.

Live Room:

- Room `room_857d95aa75c14dd0b939f43baf9a9e17`
- creation Round `round_9136a696201c4d0b89a99e2059beb543`
- reuse Round `round_8993b4baccc140f48de28bd51bcaea7e`
- both Rounds used one C turn; A/B never consumed context.

**Round 1 — PASSED**

C independently followed the custom-capability path from a prompt that named no capability ID, package filename, authoring command, registration command, or implementation language.

Durable evidence shows:

- initial registry `list`: only `assert_file`, `compare_files`, `find_files`, and `search_text`;
- on-demand `authoring` schema version 1 lookup;
- custom capability ID `ascii_text_slug`;
- four verification cases with matching expected/observed output hashes and `passed: true`;
- package SHA-256 `af1ed4105a432ff0f1b0faab7bcb63c90e1bb86eeaf0a7e2463babd35b9d53d5`;
- manifest SHA-256 `d23225a3be144d6fbc41f69b4a94971ee22377459f0490e2eda9eb039017fcaa`;
- implementation SHA-256 `3333ecd6e0af62de3a87a679acbc320e57e6cf82cc9561a189871712aca6add5`;
- verification SHA-256 `8eca83c2e7d9fa439d8e60e9fe3f97598af0d575015120d99c4555ae83c1b023`;
- host registration SHA-256 `abfbeb96bee8d24621f2c1666d9bf9b11c5ce9f952cfe3ba5ec5eb750c614d2e`;
- Room binding SHA-256 `0988e7efccb235a7106dc438cf4074f6d1ddf95b31cc6995d3d9f7d24c40c81c`;
- exact C FINISH `P4.4-CUSTOM-REGISTERED`;
- normal `mutual_finish` closure.

**Round 2 — FAILED THE LIVE STOP CONDITION**

C correctly rediscovered `ascii_text_slug` in normal registry `list` as `origin: custom`, `scope: lineage`, version `1`, with implementation/package/registration identity matching Round 1. `inspect` also showed the same verification SHA, four-case plan, durable fields `slug` / `length`, no declared permissions, and no side effects.

The first durable custom invocation then failed:

`invalid_request: input JSON is invalid: Expecting property name enclosed in double quotes`

The Round subsequently recorded six generic failed command executions and two generic completed command executions. By design those events retain no arbitrary command text/output. Crucially, the export contains **no later successful `deterministic_capability` event**, no durable `ok:true`, and no durable `slug` / `length` result. C's exact `P4.4-CUSTOM-OK` FINISH therefore does not satisfy the stop condition.

This evidence does not claim what the generic later commands contained. It does establish that the live product path taught and exposed only inline `--input-json JSON_OBJECT`, and the one auditable registered invocation failed because JSON was not preserved across command-line quoting.

**PR #23 repair**

The smallest demonstrated repair preserved inline compatibility and added a second normal invocation transport:

`codex-room-cap invoke CAPABILITY_ID --input-file WORKSPACE_RELATIVE_JSON`

Properties:

- mutually exclusive with `--input-json`;
- path must remain inside the Room workspace;
- input file is bounded to 1 MiB;
- content must be UTF-8 JSON and one object;
- both CORE and custom manifests advertise the file-input form;
- persistent agent guidance tells agents to use file input when shell quoting is fragile or when an inline attempt fails to preserve valid JSON;
- the command remains a standalone ordinary `invoke`, so existing safe durable capability telemetry applies unchanged.

Exact reviewed PR #23 head:

`2a32cd3ef915ff1c064bda49a0303e2a72cbbc04`

GitHub Actions PR run `34763827289`: **297 passed, 2 warnings**.

PR #23 squash-merged as:

`4c10b60c4ef290fc690d39a33c2d5e43d5eece7d` — `P4.4e: make capability invocation input shell-robust`

Canonical-main GitHub Actions run `34763920318`: **297 passed, 2 warnings**.

**Status:** Round 1 IMPLEMENTED / VERIFIED live. PR #23 IMPLEMENTED / VERIFIED deterministically. P4.4e as a whole remains **IN PROGRESS / NEEDS LIVE VERIFICATION** until a later Round in the same preserved Room produces a successful durable registered invocation on new input.

### E-038 — P4.4e repaired live reuse proof closes custom capability registration
**Date:** 2026-09-13  
**Scope:** Same-Room post-PR-#23 reuse proof for the already-host-bound custom capability. Closes P4.4e and P4.4 end to end.

Live Room:

- Room `room_857d95aa75c14dd0b939f43baf9a9e17`
- repaired reuse Round `round_3f88ad9c33fa4079aec29364681749ae`
- one C turn; A/B remained unconsumed
- normal `mutual_finish` closure.

The user prompt named neither the custom capability nor any registry/invocation command. It asked only to reuse the deterministic facility already available in the Room for the new input:

`  Alpha / Beta__99  `

Durable evidence establishes the full registered reuse path:

- registry `list` rediscovered `ascii_text_slug` as `origin: custom`, `scope: lineage`, version `1`;
- listed identities matched the original host binding:
  - implementation SHA-256 `3333ecd6e0af62de3a87a679acbc320e57e6cf82cc9561a189871712aca6add5`;
  - package SHA-256 `af1ed4105a432ff0f1b0faab7bcb63c90e1bb86eeaf0a7e2463babd35b9d53d5`;
  - registration SHA-256 `abfbeb96bee8d24621f2c1666d9bf9b11c5ce9f952cfe3ba5ec5eb750c614d2e`;
- registry `inspect` returned the same implementation/package/registration identities, verification status `verified`, verification SHA-256 `8eca83c2e7d9fa439d8e60e9fe3f97598af0d575015120d99c4555ae83c1b023`, the original four-case plan, and durable result fields `slug` / `length`;
- one workspace file change occurred before invocation, consistent with the repaired bounded file-input transport introduced by PR #23;
- the subsequent normal deterministic capability invocation completed with:
  - `capability: ascii_text_slug`;
  - version `1`;
  - the same implementation/package/registration/verification identities;
  - `ok: true`;
  - `slug: "alpha-beta-99"`;
  - `length: 13`;
- C FINISHed exactly `P4.4-CUSTOM-OK`.

This satisfies the outstanding P4.4e stop condition that the already-bound immutable custom capability be rediscovered and successfully invoked on a new input without relying on the mutable draft or re-registration.

**P4.4e status:** COMPLETE / IMPLEMENTED / VERIFIED live.

**P4.4 status:** COMPLETE / IMPLEMENTED / VERIFIED end to end.

**Next boundary:** P4.5 must preserve registered lineage-scoped custom capabilities across Room rollover at the exact inherited version. Personal/CORE promotion remains later work under D-022.


### E-039 — P4.5a exact lineage binding inheritance across rollover
**Date:** 2026-09-13  
**Scope:** Deterministic P4.5a implementation and hosted verification. Fresh live Room rollover evidence is not claimed here.

PR #24 implemented inherited custom-capability bindings without changing the identity of the registration being inherited.

Binding/provenance result:

- original custom registrations remain content-addressed records tied to the Room that actually registered them;
- existing direct Room bindings remain schema v1 and are not rewritten;
- a rollover successor receives schema-v2 bindings that commit to:
  - the successor Room ID;
  - capability ID;
  - exact original registration SHA-256;
  - truthful original registration Room ID;
  - immediate predecessor Room ID;
  - exact predecessor binding SHA-256;
- inherited binding loading re-resolves and revalidates the original immutable registration, verification receipt, and published package;
- the predecessor binding chain must match the claimed immediate predecessor hash and the same exact registration/origin identity;
- no successor registration or verification record is fabricated, and inheritance never performs a newest-version lookup;
- predecessor binding bytes remain unchanged.

Rollover-saga result:

- the predecessor's complete current custom-binding set is inherited deterministically;
- protected operation-scoped staging is used before publishing the successor binding directory;
- replay of the same rollover validates/reuses the already-published exact successor bindings;
- normal rollover abort removes the operation staging area and successor binding directory;
- startup recovery for a fully provisioned pending successor validates/reconstructs the same inherited binding set before database finalization;
- startup recovery for an incomplete successor aborts it and removes inherited successor binding state;
- a predecessor with no custom binding continues through the existing no-capability rollover path.

Regression coverage additionally proves:

- normal successor registry `list`, `inspect`, and `invoke` use the inherited capability successfully;
- implementation/package/registration/verification/version identity matches the predecessor exactly;
- multiple custom capabilities inherit together;
- multi-generation rollover keeps the original registration Room while each generation records its immediate predecessor binding;
- a rehashed schema-v2 record with a false predecessor-binding link is rejected;
- existing CORE/custom collision enforcement remains in the inherited load path.

Exact reviewed PR #24 head:

`888585749cbfe702080005d7211fbc79e758a7a7`

GitHub Actions PR run `34766802808`: **301 passed, 2 warnings**.

PR #24 squash-merged as:

`f1f83357b78399718ed8910f2849763c6c2dbbbb` — `P4.5a: inherit lineage custom capability bindings`

The merge Git tree `c6884247cfc5cdf59126121fb50776140c84ed73` exactly matches the reviewed/tested PR-head tree.

Canonical-main GitHub Actions run `34766882490`: **301 passed, 2 warnings**.

**P4.5a status:** COMPLETE / IMPLEMENTED / VERIFIED deterministically.

**P4.5a deterministic boundary:** satisfied. E-040 records the fresh live Room rollover proof required for end-to-end P4.5 closeout. Personal/CORE promotion remains outside this slice.

### E-040 — P4.5 live lineage-capability rollover proof
**Date:** 2026-09-13  
**Scope:** Fresh live source→successor Room rollover verification plus direct predecessor/successor binding inspection. Complements E-039 deterministic/hosted verification.

Source Room:

- Room ID: `room_8b85b75a868f4077bc44f465ee2d9439`;
- capability: `normalize_ascii_label`, version `1`, scope `lineage`;
- implementation SHA-256: `25142f348f9532321a9547a15d6253bfdf5e858ed5126e93b7bdd12bb3c6ed7a`;
- package SHA-256: `92c6e493f278f21680ddb7fcde20c4c49fe327381fcf4d63e6de215e9abf90ca`;
- registration SHA-256: `1adfeb4be3095104402f4cc5b1fd8f1331253dd1712e5eafb5b025afb5ec8a39`;
- verification SHA-256: `7a016e4aa8e6ad5d79333a5c38f398a02e56cf1a2320b38518a7d2d8a281c1cb`;
- manifest SHA-256: `d2b07a93ca8b8ccec295cdc27ae7bb403df02462836fd505e9cfed17a64b50df`;
- direct schema-v1 binding SHA-256: `e6386581c2bd1ebe63d8e427b90c7ea51474350b44d6bf1f8776e0d9dd3f9bc8`.

The source completed its baseline registry/list/inspect/invoke proof before rollover. A malformed inline JSON invocation was rejected visibly and then corrected through the existing file-input path; final source invocation succeeded without capability mutation or re-registration.

Rollover:

- operation ID: `rollover_5cc48f0927fe469cbfc52f9f9e6767cc`;
- successor Room ID: `room_d5d2462daff04c62bcf00468bf90606a`;
- successor was created in `preparing` state with fresh A/B/C persistent thread IDs and lineage metadata naming the exact predecessor;
- no successor capability registration/republication operation occurred.

Direct successor binding inspection before the live Round showed:

- binding schema version `2`;
- current Room `room_d5d2462daff04c62bcf00468bf90606a`;
- successor binding SHA-256 `4a5e91e2c8c4fe47f24cf919fba9fee28597cd8535290b130b74c49bfc6632b9`;
- original registration Room `room_8b85b75a868f4077bc44f465ee2d9439`;
- immediate predecessor Room `room_8b85b75a868f4077bc44f465ee2d9439`;
- inherited predecessor binding SHA-256 `e6386581c2bd1ebe63d8e427b90c7ea51474350b44d6bf1f8776e0d9dd3f9bc8`;
- exact implementation/package/registration/verification/manifest identities matching the source.

Successor live Round evidence:

- C alone consumed the Round; A/B remained unconsumed;
- normal registry `list` rediscovered `normalize_ascii_label` as custom / lineage / version `1` with exact implementation/package/registration identity;
- registry `inspect` returned the same implementation/package/registration identities, verification status `verified`, verification SHA-256 `7a016e4a...`, five verified cases, and the same case-plan identity;
- the first inline registered invocation returned structured `invalid_request` because the JSON transport was malformed;
- C then used the existing workspace file-input transport and the normal registered invocation completed successfully;
- durable invocation evidence reported the exact source version/implementation/package/registration/verification identities with `ok:true`, `normalized:"p4_5_live_lineage_verification"`, and `length:30`;
- C FINISHed after one turn and the Round closed normally;
- the export contains no authoring, verification, publication, or registration event for a replacement capability.

Post-rollover predecessor stability check:

- the source Room reports `status: archived`, `sealed: true`, and a committed rollover record naming the successor;
- direct inspection from the predecessor workspace still returns schema-v1 binding SHA-256 `e6386581c2bd1ebe63d8e427b90c7ea51474350b44d6bf1f8776e0d9dd3f9bc8`;
- original registration Room and all immutable capability identities remain unchanged.

**P4.5 status:** COMPLETE / IMPLEMENTED / VERIFIED end to end.

This live proof satisfies the remaining E-039 boundary: a fresh registered lineage-scoped custom capability survived an actual Room rollover, remained discoverable/inspectable/invokable at the exact inherited identity in the successor, and left the historical predecessor's original binding unchanged.

### E-041 — Protected instruction layers and replaceable A/B/C personalities
**Date:** 2026-09-13  
**Scope:** [CORE] personality-composition refactor; deterministic/hosted verification. This record does not claim that the next default personality texts have been behaviorally validated.

PR #28 changed effective agent-instruction composition from an editable whole-prompt / additive-override model to explicit protected and replaceable layers.

Verified behavior:

- A, B, and C effective developer instructions are composed from protected shared institutional/peer rules, agent-specific structural instructions where applicable, one replaceable personality body, and protected Room protocol;
- C's organizer/coordination responsibilities are carried in the protected structural layer and remain present when C receives a personality override;
- A/B/C Room personality overrides use the override as the effective personality rather than retaining the saved default personality alongside it;
- the old `ROOM-SPECIFIC OVERRIDE` additive composition is absent from new effective prompts;
- all three agents support Room personality overrides, including C;
- saved default profile rows hold the personality body used for new composition;
- exact known built-in full-prompt defaults migrate to personality-only default rows;
- non-matching custom default text and existing Room snapshots are deliberately preserved rather than silently rewritten;
- normal rollover preserves exact selected profile snapshot, Room override, and effective instructions; the legacy add-C path composes C's protected structure around its selected personality;
- the previous A/B-only default-profile update API remains compatible and preserves C's saved default when C fields are omitted.

Focused regression tests exercise default composition, all-three override replacement, C structural protection, migration, rollover continuity, UI/API support, and A/B-only update compatibility.

Exact reviewed PR head:

`1265d93e3850b62e03109ef3f6aa5db331ae8e54`

GitHub Actions PR run `34793148740`: **305 passed, 2 warnings**.

PR #28 squash-merged as:

`247aee5f3d6869e0435cadba415ed168b163b345` — `Core: separate protected instructions from replaceable personalities`

The merge Git tree `817c498f21d6ab93cc5523636189a972d054c132` exactly matches the reviewed/tested PR-head tree.

Canonical-main GitHub Actions run `34793231052`: **305 passed, 2 warnings**.

One earlier pre-final PR head produced **303 passed, 1 failed, 2 warnings** because a newly expanded test expected Agent C inside the intentionally two-agent `LegacyPairDatabase` compatibility fixture. The correction kept that fixture pair-scoped and moved triad/C assertions to triad-specific coverage; the failure did not demonstrate a runtime composition defect.

**Evidence boundary:** E-041 verifies instruction composition, persistence, migration, API/UI wiring, and hosted regression behavior. It does not establish that the eventual replacement default personalities are sufficiently differentiated in live model cognition. That remains the current behavioral-design task under D-023.

### E-042 — Standard default personality redesign implementation
**Date:** 2026-09-13  
**Scope:** [CORE] replacement of the standard A/B/C personality bodies under D-023; conservative built-in migration; deterministic/hosted verification. This record does not claim live behavioral differentiation.

PR #30 replaced the role-derived standard default personality bodies with the approved general-purpose cognitive temperaments:

- **Agent A:** exploratory and constructive — tends to generate worthwhile possibilities, make uncertainty concrete, use bounded reversible probes, and guard against both premature attachment and option flooding;
- **Agent B:** skeptical and discriminating — tends to separate observation from inference, inspect premises and evidence, distinguish fatal/material/minor flaws, and identify what would actually resolve uncertainty;
- **Agent C:** contextual and relational — tends to examine surrounding purpose, relationships, relevance, and consequences while explicitly treating its own synthesis or pattern as a hypothesis rather than closure.

The active default personality bodies no longer contain the former **Implementer / Verifier / Integrator** occupational labels. C's organizer/coordination responsibility remains in the protected structural layer established by PR #28/E-041 and was not moved into the new personality text.

Upgrade behavior was also tightened conservatively:

- exact SHA-256 identities for the immediately prior role-derived personality-only defaults are recognized and migrated to the redesigned defaults;
- non-matching custom default profile text is preserved;
- the exact built-in C profile display name `Agent C · The Integrator` migrates to `Agent C default` only when the associated profile text is one of the recognized built-ins;
- existing Room snapshots/effective instructions are not silently rewritten by this default-profile migration.

Regression coverage verifies the three new temperament anchors, absence of the retired labels from active defaults, exact old-built-in migration, preservation of modified/custom text, default composition, and the UI contract.

Verification history:

- initial PR head `eea0d4af907135ab767fb303ce95d9ab2ef0d323`, GitHub Actions run `34794891870`: **306 passed, 1 failed, 2 warnings**;
- the sole failure was `tests/test_three_agent_ui.py::test_http_new_room_snapshot_and_ui_contract_are_permanent_triad`, whose stale assertion still required the retired string `The Integrator` in C's default personality; no runtime/personality implementation failure was demonstrated;
- the stale assertion alone was updated to the new C default contract;
- exact final PR head: `b65a8aedac9f0212e19e9535070cbaf798f0816d`;
- GitHub Actions PR run `34795003630`: **307 passed, 2 warnings**;
- PR #30 squash-merged as `412b0f68eca5150a99042f7ced2038eaf75bcf8c` — `Replace role-derived default personalities`;
- the final PR-head Git tree and merge Git tree are both `7f14b70e98cf297576d0dc337d34571fa29d8c9c`;
- canonical-main GitHub Actions run `34795121428`: **307 passed, 2 warnings**.

**Evidence boundary:** E-042 establishes that the approved default personality texts are implemented, selected for fresh/default-profile use, conservatively migrated from exact prior built-ins, and hosted-regression verified. It does **not** establish that A/B/C are behaviorally distinguishable enough in live model cognition, that the observed A/B or B/C overlap seams are harmless in practice, or that C's greater prompt length has no behavioral weighting effect. Those are the next controlled live-evaluation questions.

### E-043 — V3 controlled default-personality behavioral evaluation
**Date:** 2026-09-14  
**Scope:** [ROOM] controlled live behavioral evaluation under D-023. This record evaluates the V3 defaults implemented by E-042; it does not establish V4 behavior.

Four fresh Personal Rooms were run across four different decision domains:

1. family-owned café profitability;
2. optional AI tutoring and causal inference;
3. manuscript revision under a deadline;
4. disaster-relief ordering governance.

Each trial used the same control structure: standard V3 defaults only, no Room personality overrides, no private initialization or participant-specific overlays, the same shared independent-reasoning overlay, and `starting_agent: "either"` so A/B/C began independently from the same Round-start event. The staging opening Round was never executed. No participant used MESSAGE or consumed a peer response before its own answer; each participant produced one FINISH and each Round closed normally. The four trials are therefore mechanically clean for the intended independent comparison.

The live responses supplied positive behavioral evidence as well:

- all three agents remained generally competent across business, evidentiary, creative, and organizational problems;
- none manufactured disagreement merely to express identity;
- A did not exhibit option flooding or obvious novelty fixation;
- B did not exhibit skeptical paralysis;
- C did not treat synthesis as epistemic authority or premature closure;
- convergence occurred naturally when the problem strongly supported a common recommendation.

The blind-distinctiveness stage then removed agent identities, independently randomized the three responses within each scenario, and asked an external evaluator to map each response to A/B/C based on reasoning trajectory rather than tone. The established success criterion was at least **3 of 4 complete trios** correctly mapped.

Actual blind score:

- **3 of 12** individual identities correctly mapped;
- **0 of 4** complete A/B/C trios correctly mapped;
- A, B, and C were each correctly identified in only **1 of 4** scenarios.

The sample is too small to support a statistical claim that performance was worse than chance. The decision-relevant result is that V3 failed the previously established practical distinguishability criterion. Pairwise confusions occurred across all three pairings, showing that the issue was not confined to one weak personality. The responses did show differences in emphasis, but those differences were too subtle for reliable blind recovery.

**Conclusion:** V3 demonstrated that the D-023 personality architecture can influence attention without creating caricature or forced disagreement, but the personality strengths were under-calibrated for the required blind recognizability. This is a calibration failure, not evidence that protected identity / replaceable personality composition itself is unsound.

**Status:** HISTORICALLY VERIFIED / DID NOT MEET CRITERION. V3 is superseded as the active default by the V4 revision recorded in E-044.

### E-044 — V4 standard default personality distinctiveness revision implementation
**Date:** 2026-09-14  
**Scope:** [CORE] targeted D-023 revision responding to E-043; conservative V3 built-in migration; deterministic/hosted verification. This record does not claim V4 behavioral differentiation.

PR #32 replaced the active V3 personality bodies with a targeted V4 revision that strengthens each participant's characteristic first attentional move:

- **Agent A — exploratory / generative:** first widens the possibility space before narrowing, looking for untried options, combinations, mechanisms, or reframings that may change the shape of the problem;
- **Agent B — skeptical / discriminating:** first establishes the epistemic picture, separating observations from inferences or assumptions, identifying what remains unknown, and comparing competing explanations;
- **Agent C — contextual / relational:** first locates the immediate question within the objective, dependencies, tradeoffs, and consequences that materially affect it, while explicitly treating framing or synthesis as an interpretation to test rather than a ruling.

The revision preserves the D-023 layer boundary: C's organizer/coordination responsibilities remain in the protected structural layer and are not embedded in the replaceable personality body. The former Implementer / Verifier / Integrator occupational labels remain absent from the active defaults.

Upgrade behavior recognizes the exact V3 default personality bodies by SHA-256:

- A: `678d7c48cd652e9237fcfeadd8da20d3595aa708a79deb35cd531263d96e2477`;
- B: `a0df11ad77c5849cfa39cadfc6efe0d4b302cac587fa5e2f60ab13db6327bd17`;
- C: `5f7452ee2a40a9ed432d1cacbd404ff836a9539260d1ea1ac01035acd99f0fa9`.

Only recognized exact built-in default profile text migrates to V4. Non-matching/custom profile content remains preserved, and existing Room snapshots/effective instructions are not silently rewritten. Regression coverage verifies V4 first-move anchors, the exact V3 migration identities, recognized-default migration, and preservation of customized text.

Verification:

- exact reviewed PR head: `b588e27011b0c1be13f8ada9b1cb254133d2329c`;
- PR-head Git tree: `741448ed0a9d023f012778c679dd5d692ec6f9fe`;
- GitHub Actions PR run `34856031735`: **309 passed, 2 warnings**;
- PR #32 squash merge: `7567e2a40c6a3745d829f119397cc6525f9f512a` — `Sharpen default personality trajectories`;
- merge Git tree: `741448ed0a9d023f012778c679dd5d692ec6f9fe`, exactly matching the reviewed/tested PR-head tree;
- canonical-main GitHub Actions run `34856479809`: **309 passed, 2 warnings**.

**Evidence boundary:** E-044 establishes that the reviewed V4 personality texts are implemented, selected for fresh/default-profile use, conservatively migrated from exact V3 built-ins, and deterministically/hosted verified. It does **not** establish that V4 meets the blind-distinctiveness criterion. The next evidence step is to rerun the same four controlled independent scenarios in fresh Rooms and repeat blind classification against the same **3-of-4 complete-trio** target.

**Status:** IMPLEMENTED / VERIFIED deterministically.

### E-045 — V4 café first-move calibration observation
**Date:** 2026-09-14  
**Scope:** [ROOM] one controlled V4 live rerun under D-023, used as a calibration gate rather than as a completed four-scenario blind evaluation.

A fresh Room titled `D023-V4-S1-Cafe` reran the same family-owned café scenario used in the V3 evaluation.

Mechanical controls were clean:

- the staging opening Round was prepared but never started and closed only as `replaced_by_new_round`;
- the evaluation Round was `D023-V4-S1-Independent` with `starting_agent: "either"`;
- A/B/C used the exact V4 standard personality snapshots with no Room personality overrides;
- there was no private initialization and no participant-specific overlay;
- all three agents were delivered the same start event and began independently;
- no agent used MESSAGE or consumed peer conversational output before finishing;
- each participant produced exactly one substantive FINISH;
- the Round closed normally with `mutual_finish`.

The principal V4 intervention was stronger first-attentional differentiation. On that target, the live result showed direct convergence:

- A opened by framing the immediate problem as margin rather than demand;
- B opened by framing the evidence as margin erosion rather than demand collapse;
- C opened by framing the immediate problem as margin compression rather than demand.

Later reasoning contained some differentiation: A became more generative in menu/operating possibilities, B more explicitly discriminated what the evidence established, and C showed contextual/daypart relationships. But those differences emerged after all three had already entered through substantially the same diagnosis.

**Interpretation:** this is a strong observed calibration failure at the exact first-move seam V4 was designed to strengthen. It does not establish a full V4 blind-evaluation score because the other three scenarios and blind packet were intentionally not run. The human principal explicitly chose to treat this clean Scenario 1 result as sufficient to stop the incremental V4 path and move to a more extreme V5 calibration.

**Status:** OBSERVED ISSUE / V4 first-move calibration insufficient. V4 is superseded as the active default by V5; no completed four-scenario V4 blind verdict is claimed.

### E-046 — V5 strong default-personality calibration implementation
**Date:** 2026-09-14  
**Scope:** [CORE] deliberately stronger D-023 personality calibration responding to E-045; conservative V4 built-in migration; deterministic/hosted verification. This record does not claim V5 behavioral differentiation.

PR #34 replaced the active V4 personality bodies with a stronger calibration intended to counter the repeated tendency of a shared capable model to converge on the same generic problem-solving entry point.

The V5 default cognitive priors are:

- **Agent A — strongly exploratory / generative:** natural first move is to expand the possibility space; it explicitly resists beginning with diagnosis unless missing facts make exploration meaningless;
- **Agent B — strongly skeptical / discriminating:** natural first move is to challenge the epistemic foundation; it explicitly resists leading with solutions before the factual structure has survived examination;
- **Agent C — strongly contextual / relational:** natural first move is to step outside the immediate question into objectives, dependencies, constraints, and consequences; it explicitly resists leading with local-option generation or fact-by-fact litigation.

The stronger starting priors retain anti-caricature self-correction:

- A distrusts the attractiveness of its possibilities;
- B distrusts the importance of its objections;
- C distrusts the completeness of its synthesis.

The D-023 layer boundary remains intact. C's organizer/coordination responsibility is unchanged in the protected structural layer and is not embedded in the replaceable personality body. Protected institutional identity, peer rules, and Room protocol were unchanged.

Upgrade behavior now recognizes the exact V4 default personality bodies by SHA-256:

- A: `ebe03e6456df6eb2ccbf4e82bdeedaf756a4075712266ba16b99201400583d11`;
- B: `e52156bc3d24a9e39c2a04458edc15cd7fd71ad3164ef7de1d17fa0959488776`;
- C: `cbea4f0090d33aa22079f9c6692569dac0193bd633e6ed61839f9019020d8706`.

Only recognized exact built-in default profile text migrates to V5. Non-matching/custom profile content remains preserved, and existing Room snapshots/effective instructions are not silently rewritten. Regression coverage verifies V5 first-move and negative-starting constraints, the exact V4 migration identities, recognized-default migration, custom-profile preservation, fresh Room composition, and the UI default-profile contract.

Verification history:

- initial PR head `7e36c63f7cbba684dc0f8233ff65f38646a03cdf`, GitHub Actions run `34863634983`: **310 passed, 1 failed, 2 warnings**;
- the sole failure was a stale UI assertion expecting the V4 phrase `contextual, relational temperament`; production V5 behavior was not implicated;
- only that obsolete assertion was changed;
- exact final PR head: `1b38c76b5cf1cbc606fc2b9df2bf3f1e2b4d66be`;
- final PR-head Git tree: `c5955136274252f77e065d3a5b54825ba2cae5e2`;
- GitHub Actions final PR run `34863827367`: **311 passed, 2 warnings**;
- PR #34 squash merge: `ed8b73fb9f1437a894e926f65e1ca558e0005973` — `Strengthen default personality calibration`;
- merge Git tree: `c5955136274252f77e065d3a5b54825ba2cae5e2`, exactly matching the tested final PR-head tree;
- canonical-main GitHub Actions run `34864015525`: **311 passed, 2 warnings**.

**Evidence boundary:** E-046 establishes that the V5 personality texts are implemented, selected for fresh/default-profile use, conservatively migrated from exact V4 built-ins, and deterministically/hosted verified. It does **not** establish that V5 produces the intended strong behavioral differentiation without excessive rigidity or pathology.

**Next evidence gate:** rerun the café scenario in a fresh V5 Room using the same independent controls. Only if the opening trajectories visibly separate should the remaining scenarios and full blind evaluation resume.

**Status:** IMPLEMENTED / VERIFIED deterministically.

### E-047 — V5 café calibration gate failed cleanly
**Date:** 2026-09-14  
**Scope:** [ROOM] one controlled V5 live rerun under D-023, used as a calibration gate before spending the remaining scenarios.

A fresh Room titled `D023-V5-S1-Cafe` reran the same family-owned café scenario and independent controls used for the prior calibration work.

Mechanical controls were clean:

- the staging opening Round was prepared but never started and closed only as `replaced_by_new_round`;
- the evaluation Round was `D023-V5-S1-Independent` with `starting_agent: "either"`;
- A/B/C used the exact V5 standard personality snapshots with no Room personality overrides;
- there was no private initialization and no participant-specific overlay;
- all three agents received the same start event and began independently;
- no agent used MESSAGE or consumed peer conversational output before finishing;
- each participant produced exactly one substantive FINISH;
- the Round closed normally with `mutual_finish`.

V5 had been deliberately strengthened to force different first cognitive entrances. The live result still converged at that exact seam:

- B opened: the facts support a **margin problem more clearly than a demand problem**;
- C opened: the immediate problem is **margin compression, not demand collapse**;
- A opened: the immediate problem is **margin compression**.

Later texture showed some differentiation. A became the most generative around catering, pickup/preorder, and alternative use of quiet capacity; B most explicitly discriminated what the evidence did and did not establish; C organized options into a sequenced margin-recovery program. Those differences emerged only after all three had already entered through substantially the same diagnosis.

**Interpretation:** V5 did not pass its deliberately cheap café admission gate. Stronger temperament prose and explicit first-move prohibitions influenced later emphasis but did not reliably overcome the shared model's tendency to begin with the same competent diagnostic framing. The remaining V5 scenarios were intentionally not run. This result motivated a different V6.2 mechanism: persistent asymmetric cognitive contracts across the full reasoning cycle, rather than a stronger opening temperament alone.

**Status:** OBSERVED ISSUE / V5 first-move calibration insufficient. V5 is superseded as the active default by V6.2; no completed four-scenario V5 blind verdict is claimed.

### E-048 — V6.2 complementary cognitive-contract implementation
**Date:** 2026-09-14  
**Scope:** [CORE] D-023 personality revision responding to E-047; conservative V5 built-in migration; exact-diff and hosted verification. This record does not claim live behavioral differentiation.

PR #36 replaced the V5 default personality bodies with V6.2 persistent cognitive contracts. The change preserves the protected D-023 composition boundary: institutional identity/peer rules, C's structural organizer responsibilities, and Room protocol were unchanged.

The active V6.2 cognitive centers of gravity are:

- **Agent A — "What else could we do?"** A must actively expand the option space on a fresh problem and keep the exploratory orientation active through narrowing and recommendation. Its later convergence favors leverage, reversibility, optionality, useful learning, combinations, and removal of unnecessary tradeoffs.
- **Agent B — "What are we justified in believing?"** B must establish what is actually supported before accepting diagnosis, causal story, prediction, or solution, and keeps epistemic justification as its center through evaluation and recommendation.
- **Agent C — "How do the consequential parts fit together and behave?"** C must identify load-bearing objectives, dependencies, constraints, bottlenecks, interactions, sequencing, and consequences before local diagnosis, and keeps relational/system structure as its center through recommendation.

V6.2 also makes the B/C seam explicit:

- B's primary concern is whether a proposition, inference, diagnosis, or prediction deserves belief;
- C's primary concern is how elements relate and what those relationships cause or constrain, assuming relevant claims are provisionally usable.

All three profiles include characteristic anti-duplication "move the frontier" behavior and stopping rules against their expected failure modes. C is explicitly required to surface genuine unresolved conflict rather than hide it inside a compromise.

Upgrade behavior adds exact V5 personality-body SHA-256 anchors:

- A: `49225250cd1fa14c1bb58e654cf4ede6e55dd7ff969013341552db5ee45a705d`;
- B: `c1449f7edbb9f0e509a10ca4c5f4ff6146f285de242ea7a9fb195c527c810dd1`;
- C: `59a9113aa443a7c0dbda65444c1e61039e79f27652b8be1ac53d9aad57fa3722`.

Only exact recognized built-in defaults migrate to V6.2. Non-matching/custom default text remains preserved, and existing Room snapshots/effective instructions are not silently rewritten.

Verification:

- exact final PR head: `8ecfd73104638b49975a6bf134cc3dde16f35468`;
- PR-head Git tree: `bc2590ddc11682d51ecf3cb79221259f7acd59ea`;
- GitHub Actions PR run `34870235815`: **313 passed, 2 warnings**;
- PR #36 squash merge: `6d89465de2bf581a8bce2e44ce569beea224f3df` — `D-023: implement V6.2 complementary cognitive contracts`;
- merge Git tree: `bc2590ddc11682d51ecf3cb79221259f7acd59ea`, exactly matching the tested PR-head tree;
- canonical-main GitHub Actions run `34870432154`: **313 passed, 2 warnings**.

**Evidence boundary:** E-048 establishes that V6.2 is implemented as the current default, conservatively migrates exact V5 defaults, preserves custom/default and existing Room-state boundaries, and is deterministically/hosted verified. It does **not** establish that the shared model will honor the intended complementary trajectories in live cognition.

**Next evidence gate:** rerun the same café scenario once in a fresh V6.2 Room under the established independent controls. Only if A, B, and C visibly perform complementary cognitive work without obvious pathology should the remaining controlled scenarios and blind evaluation resume.

**Status:** IMPLEMENTED / VERIFIED deterministically.

### E-049 — V6.2 behavioral evaluation failed the pre-set complementarity criterion
**Date:** 2026-09-14  
**Scope:** [ROOM] controlled D-023 behavioral evaluation of the V6.2 default personalities across the first three established scenarios. The fourth scenario and blind classification were stopped once the agreed 3-of-4 criterion became mathematically unreachable.

All three V6.2 Rooms used the established independent-control pattern: fresh Room, unstarted staging Round replaced by a dedicated evaluation Round, `starting_agent: "either"`, no private initialization, no participant-specific overlays, one common start event, no peer MESSAGE traffic before FINISH, and normal `mutual_finish` closure.

Scenario outcomes:

- **S1 — Café:** qualitative gate **PASS**. A materially changed the option space, B made the evidence structure legible, and C organized the consequential relationships and sequencing. Final recommendations overlapped, but the cognitive work products were visibly more complementary than V4/V5. C still opened with the familiar margin-compression diagnosis, so the pass carried a watch item rather than establishing full verification.
- **S2 — AI tutoring:** **FAIL**. The prompt contained an obvious selection-bias / causal-inference flaw, and the shared model pulled all three participants into substantially the same organizing frame. B behaved strongly as intended, but A and C also centered their answers on the association-versus-causation objection and converged on essentially the same randomized/phased evaluation plan. Later texture differed, but the complete trio was not reliably distinguishable by cognitive work.
- **S3 — Manuscript revision:** **FAIL**. All three independently converged on nearly the same intermediate method and recommendation: scene-level diagnosis/map, structural rebuild of the middle, selective cuts, targeted character additions, protection of the strong opening, and a final continuity/pacing pass. A/B/C openings retained some characteristic language, but the reasoning architecture and operational work product were substantially the same.

The pre-established practical criterion for this evaluation family was at least **3 of 4 complete A/B/C trios** showing distinguishable reasoning trajectories. After S2 and S3 both failed, the maximum possible result was only 2 of 4 even if S4 passed. The principal therefore stopped the V6.2 series before the disaster-relief scenario and blind classification.

**Interpretation:** V6.2 was behaviorally better than V5, especially in the café gate, but persistent cognitive-center instructions were still not strong enough to overcome a shared model's attraction to a salient best reasoning path. When the task strongly suggested one high-quality method, the agents could preserve different wording and emphasis while still producing substantially redundant cognition.

This evidence supports moving away from asking three copies of the same model to each produce a complete balanced solution. The next mechanism should make the agents' default contributions intrinsically non-redundant through different required primary work products.

**Status:** OBSERVED ISSUE / V6.2 behavioral criterion NOT MET. V6.2 is superseded as the active default by V7; S4 and blind classification were intentionally not run.

### E-050 — V7 complementary work-product implementation
**Date:** 2026-09-14  
**Scope:** [CORE] D-023 revision responding to E-049; exact V6.2 built-in migration; deterministic and hosted verification. This record does not claim live V7 complementarity.

PR #38 changed the standard default personalities from persistent cognitive centers alone to distinct **primary work products**:

- **Agent A — possibility brief.** Broad requests to analyze, advise, or decide do not erase the exploratory scope. A is expected to spend most of its contribution changing the option space, including materially different approaches, at least one option outside the presented framing, combinations/sequences/reversible experiments, leverage/optionality, and kill conditions. Any recommendation is subordinate to that option-space work.
- **Agent B — evidence audit.** Broad requests do not erase the epistemic scope. B is expected to spend most of its contribution on what is supported, what important conclusion is not supported, competing explanations/premises, discriminating evidence, decision thresholds, and what action is already justified. Any recommendation is concise and tied directly to the evidence threshold.
- **Agent C — decision map.** C is expected to identify the governing objective, load-bearing constraints/dependencies, interactions, sequencing, downstream effects, and unresolved tensions without silently reproducing a complete option search and evidence audit. In ordinary collaboration it should use peer cognition rather than absorb every missing cognitive job itself.

All three defaults explicitly reject comprehensive balanced coverage merely for completeness. This is the key V7 mechanism: the shared model is not merely asked to think differently while still solving the entire problem in the same way; each default contribution has a different primary deliverable and scope boundary.

The D-023 protected-layer boundary remains unchanged. Shared institutional identity/peer rules, C's structural coordination responsibilities, and Room protocol were not modified. The V7 work-product contracts live only in the replaceable personality layer.

Upgrade behavior adds exact V6.2 personality-body SHA-256 anchors:

- A: `75719cad8fcfe3ea0cbc7c7f6fd903769aad1202732b0fae6f42b818b2616c42`;
- B: `9b136b537a9c8d2dab39fed3f4aef5f68b33c7a3cdca22e9f961c227bd23cdf3`;
- C: `78dda32bf9ffbf27818ea858f1c4395891b5357aa85c6ba11edd15c7ac60935d`.

Only exact recognized built-in V6.2 defaults migrate to V7. Non-matching/custom defaults remain preserved, and existing Room snapshots/effective instructions are not silently rewritten.

Verification:

- exact PR head: `739ab2562ef38212ce0e4f4c9ef2fe1808ee4cee`;
- PR-head Git tree: `0fc53385d726084bbc7f13a5cce551cdde302aff`;
- GitHub Actions PR run `34873161338`: **315 passed, 2 warnings**;
- PR #38 squash merge: `1c427954c7471a9d8007bd2ac29bac7d2d3f1655` — `D-023: implement V7 complementary work products`;
- merge Git tree: `0fc53385d726084bbc7f13a5cce551cdde302aff`, exactly matching the tested PR-head tree;
- canonical-main GitHub Actions run `34873373728`: **315 passed, 2 warnings**.

**Evidence boundary:** E-050 establishes that V7 is implemented as the active standard default, exact V6.2 built-ins migrate conservatively, custom/default and existing Room-state boundaries remain intact, and the exact merged tree is hosted-verified. It does **not** establish that the shared model will honor the work-product separation in live cognition.

**Next evidence gate:** rerun the known-hard AI tutoring scenario in a fresh V7 Room under the same independent controls. Success requires the complete contributions to be organized around different primary products — A possibility brief, B evidence audit, C decision map — even if all three ultimately oppose an immediate mandate. If that admission gate passes, proceed to a collaborative C-first Room to test complementarity under normal coordination rather than returning immediately to a four-scenario independent blind series.

**Status:** IMPLEMENTED / VERIFIED deterministically.

### E-051 — V7 same-task work-product admission gate failed cleanly
**Date:** 2026-09-14  
**Scope:** [ROOM] controlled D-023 admission gate for the V7 primary-work-product personalities using the known-hard AI tutoring scenario.

A fresh Room titled `D023-V7-S2-AI-Tutoring` reran the AI tutoring scenario under the established independent controls.

Mechanical controls were clean:

- the staging opening Round was prepared but never started and closed only as `replaced_by_new_round`;
- the evaluation Round was `D023-V7-S2-Independent` with `starting_agent: "either"`;
- A/B/C used the exact V7 standard personality snapshots with no Room personality overrides;
- there was no private initialization and no participant-specific overlay;
- all three participants received the same single `round_start_turn` and began independently;
- every delivery succeeded on the first attempt;
- no participant consumed peer conversational output before finishing;
- no participant used MESSAGE;
- each participant produced exactly one substantive FINISH;
- the Round closed normally with `mutual_finish`.

The V7 admission criterion was stricter than agreement or wording difference. The complete responses needed to remain organized around different primary work products: A possibility brief, B evidence audit, C decision map.

That separation did not occur.

- **B** behaved strongly as intended. Its response was primarily an evidence audit: the nine-point gap did not establish causation; voluntary participation and pre-existing attendance differences implied selection; randomized or delayed-access evaluation was stronger than matched observational analysis; the mandate threshold depended on causal benefit, subgroup generalization, and implementation burden.
- **A** did not produce a materially distinct possibility brief. It opened with the same causal-inference objection as B, then centered its answer on essentially the same randomized/phased rollout, measurement plan, and later decision threshold. It did not spend most of the contribution expanding the option space, relaxing assumptions, or developing several genuinely different approaches.
- **C** did not produce a materially distinct decision map. It likewise opened with selection bias, then centered the response on a randomized pilot/rollout and evidence collection. Equity, workload, privacy, implementation burden, and subgroup effects appeared, but they did not become the governing objective/dependency/sequencing structure of the contribution.

All three therefore followed substantially the same reasoning architecture:

`observed gain is not causal -> voluntary users differ -> do not mandate -> randomized/phased evaluation -> measure baselines/outcomes -> reassess later`.

**Interpretation:** V7's stronger static developer-personality text did not reliably override the shared model's attraction to the same salient high-quality solution when all three participants received the same broad problem-solving assignment. This is now observed after progressively stronger mechanisms: temperament, first-move constraints, persistent cognitive centers, and explicit primary work products/scope boundaries.

The result does **not** show that complementary cognition is unattainable in Codex Room. It shows that same-task independent prompting is an inefficient place to demand that complementarity. The next experiment should move the differentiation mechanism to **coordination and task allocation**: C receives the human objective first, decomposes the problem, and assigns genuinely different bounded work to A and B before integrating returned work.

**Status:** OBSERVED ISSUE / V7 same-task admission gate FAILED. Do not continue same-task personality wording escalation or run the previously planned collaborative test unchanged.

### E-052 — CG1 coordination gate: bounded task allocation worked; C finalized before all requested inputs returned
**Date:** 2026-09-14  
**Scope:** [ROOM] controlled coordination-level complementarity gate using the known-hard AI tutoring problem after E-051.

Room `D023-CG1-AI-Tutoring` used Agent C as the sole starting participant, no public/task overlay, no private initialization, and no Room personality overrides. The public prompt required C to use both A and B, choose distinct bounded work for each, and integrate their work before final recommendation.

The coordination mechanism materially changed the behavior relative to E-051.

C decomposed the decision into two distinct dependencies and publicly stated the assignments:

- **Agent A:** causal-evidence assessment;
- **Agent B:** practical/equitable implementation path.

Both peers honored the bounded assignment rather than returning redundant complete consultant answers.

- **A** focused on the evidentiary question: association versus causal effect, voluntary-selection bias, randomized rollout, pre-specified outcomes, baseline adjustment, and conditions under which a mandate would lose support.
- **B** focused on implementation: optional supported access, scheduled in-school/advisory availability, devices/connectivity, accessibility/ELL support, teacher training, consent, privacy/academic-integrity rules, and operational/equity thresholds for later expansion.

This is strong evidence that **task allocation, not static personality wording alone, can produce non-redundant peer cognition from the same underlying model**. Notably, C assigned the epistemic job to A and the implementation job to B despite their V7 default centers. The peers followed the bounded task objective, showing that allocation can dominate personality when needed without changing persistent identity.

The gate did not fully pass, however, because C issued its substantive final recommendation after B's implementation return while A's delegated causal-evidence turn was still running. Runtime evidence is exact:

- B's MESSAGE triggered a C turn first;
- C's substantive FINISH used only B's MESSAGE as its triggering/input event;
- A's substantive MESSAGE arrived later;
- because A's unread result crossed C's previous FINISH boundary, the runtime mechanically reopened C before closure;
- C then consumed A's message and emitted an empty FINISH, after which the Room closed by `reactions_settled`.

Therefore D-020's **mechanical integration-before-closure barrier worked as implemented**: A's late substantive work could not silently cross closure. But C's semantic coordination timing was insufficient. It treated the first of two explicitly requested necessary peer returns as enough to present the final recommendation, then judged the later A result to require no textual revision.

**Interpretation:** CG1 validates the allocation hypothesis but exposes a narrower C-coordination defect. The next change should not add a runtime join barrier yet, because the runtime already provided the required late-input integration opportunity and a global join could unnecessarily reduce responsiveness. The cheapest safe repair is to strengthen C's protected structural coordination instructions: when C explicitly requests multiple peer contributions because each is needed for the decision, treat early returns as provisional and do not present the final recommendation or FINISH until all requested contributions have returned, declined, failed, or been explicitly judged unnecessary.

**Status:** PARTIAL PASS / OBSERVED ISSUE. Bounded task decomposition and peer adherence succeeded; full integration timing failed.

### E-053 — C delegated-input settlement instruction
**Date:** 2026-09-14  
**Scope:** [CORE] narrow D-020 protected structural-instruction repair responding to E-052. No personality, scheduler, routing, or Room-protocol change.

PR #41 added one protected C structural coordination rule:

> When C has explicitly requested multiple peer contributions because each is needed for the decision, the first return is only a partial result. C must not present the final recommendation or FINISH merely because one requested contribution arrived first. It should wait until every requested contribution has returned, declined, failed, or been explicitly judged no longer necessary, then integrate the available set. Interim reactions may remain provisional.

This instruction lives in `AGENT_C_STRUCTURAL_INSTRUCTIONS`, not in the replaceable personality layer. A/B protected instructions and all V7 personality bodies are unchanged. The change preserves C's peer status and does not add superior judgment.

The repair deliberately does **not** add a deterministic fan-out/join barrier. E-052 showed that the existing D-020 integration-before-closure mechanism already reopened C when later A work arrived. The demonstrated defect was that C semantically finalized too early, not that the runtime allowed the Room to close without an integration opportunity.

Verification:

- exact PR head: `04fdca71911330a0a4c8607738e89c0e1279311c`;
- PR-head Git tree: `9af8be81e7cbc1fc7f94c73aafdf295e360e43bd`;
- GitHub Actions PR run `34887902144`: **315 passed, 2 warnings**;
- PR #41 squash merge: `2ce2e7c40fbca09ac31e843b7d06dabf13cc387d`;
- merge Git tree: `9af8be81e7cbc1fc7f94c73aafdf295e360e43bd`, exactly matching the tested PR-head tree;
- canonical-main GitHub Actions run `34888053548`: **315 passed, 2 warnings**.

**Evidence boundary:** E-053 establishes correct composition and deterministic regression coverage for the protected C settlement rule. It does not establish that C will obey the rule behaviorally.

**Next evidence gate:** rerun CG1 with the same AI tutoring scenario and C-first coordination after pulling/restarting the updated runtime. Success now requires the already-demonstrated distinct A/B task allocation plus C withholding its final recommendation until both explicitly requested peer inputs have settled and then integrating both.

**Status:** IMPLEMENTED / VERIFIED deterministically.

### E-054 — Deterministic C delegation-cohort timing
**Date:** 2026-09-14  
**Scope:** [CORE] D-020 coordination-timing repair derived from CG1 / E-052. This work intentionally stops the personality-calibration thread and addresses the demonstrated runtime ordering seam directly.

CG1 showed that C can issue one multi-peer delegation, receive one peer return first, and be awakened immediately by that first return while another peer from the same delegation is still running. The existing integration-before-closure barrier prevented the later peer result from being silently lost, but it did not prevent an unnecessary premature C turn.

PR #43 adds a narrow deterministic **delegation-cohort wake barrier**:

- a C MESSAGE that invokes more than one peer defines one delegation cohort using that exact event and its runnable recipients;
- when a cohort peer returns a MESSAGE that requests C, C's copy remains public/readable but is temporarily **non-runnable** while sibling cohort members remain unsettled;
- other explicitly requested recipients of that peer message remain runnable normally;
- each cohort member is considered settled when its turn caused by the original C delegation produces MESSAGE, PASS, or FINISH;
- after the complete cohort settles, the runtime emits one durable `delegation_cohort_settled` trigger to C;
- C's normal delivery coalescing then claims the accumulated passive peer returns plus the one cohort-settled trigger in a single model invocation;
- single-peer C delegation remains immediate and unchanged;
- deferred C recipients remain part of causal MESSAGE settlement, so C's later terminal reaction can settle those peer MESSAGE boundaries and allow normal Room closure.

This is deliberately **not** a global fan-out/join primitive. The barrier applies only to peers invoked together by one C delegation event. It changes when C is awakened by that cohort; it does not hide peer messages from the observer, prevent unrelated observer work, or change the protected peer relationship.

Focused regression coverage proves two timing cases:

1. B returns a MESSAGE to C while A is still running. C is not awakened by B alone. After A returns, C receives both A and B returns plus the cohort-settled trigger in one invocation, then the Room closes normally.
2. One delegated peer returns MESSAGE while the other PASSes. C remains unwoken until both settle, then receives the available return plus the PASS settlement signal.

Verification:

- exact PR head: `7ee029e9ee8678eb6e7645b130311e866e24f87c`;
- PR-head Git tree: `25defbb94723c90a6698d1acb311e7eff71e17cf`;
- GitHub Actions PR run `34889003409`: **317 passed, 2 warnings** in 46.14s;
- PR #43 squash merge: `167ef0cc609ae5635909ae11b722a7842252e570`;
- merge Git tree: `25defbb94723c90a6698d1acb311e7eff71e17cf`, exactly matching the tested PR-head tree;
- canonical-main GitHub Actions run `34889163939`: **317 passed, 2 warnings** in 107.79s.

The slower canonical-main pytest duration is recorded as an observation, not a failure: both exact-tree hosted runs passed. No evidence currently attributes the duration difference to the cohort logic.

**Evidence boundary:** E-054 establishes deterministic cohort batching and causal-settlement behavior. It does not yet establish the live hosted/local timing behavior in a real Room.

**Status:** IMPLEMENTED / VERIFIED deterministically. Personality behavioral evaluation is not the active workstream.

### E-055 — Live C delegation-cohort timing verification
**Date:** 2026-09-14  
**Scope:** [ROOM] live verification of the deterministic D-020 delegation-cohort timing repair from E-054. Personality behavior was explicitly out of scope.

Fresh Room:

- Room: `D020-Timing-1-Delegation-Cohort`;
- Room id: `room_ed26d1ca3c154fc6bc99799d09ccf070`;
- active Round: `round_808c359ce90c4e44a3bc03e2328125af`;
- starting participant: Agent C;
- no task/public overlay, private initialization, participant overlays, or Room personality overrides;
- opening staging Round was prepared but never started and closed only as `replaced_by_new_round`.

The timing-only prompt required C to send one MESSAGE invoking A and B together on two bounded tasks and then integrate only after the delegated work settled.

Observed event chain:

1. **One exact C delegation cohort formed.** C's event `event_3c1c707059724c80a0b804b9a1461d58` invoked both `agent_a` and `agent_b`; both deliveries were runnable from that same event.
2. **A returned first while B was still running.** A's MESSAGE `event_93b8476be7cb49a0a6329d706a6a2fd1` was recorded at 20:01:38.556Z. Its C delivery was readable but `runnable: false`; metadata recorded `requested_runnable_recipients: ["agent_c"]`, `runnable_recipients: []`, `deferred_runnable_recipients: ["agent_c"]`, and the original C delegation event as `delegation_cohort_parent_event_id`.
3. **No premature C turn occurred.** There is no C `agent_activity` or decision event between A's first return and B's later return.
4. **B returned second.** B's MESSAGE `event_20148188455346eeb506bb1ea93f4071` was recorded at 20:01:43.526Z with the same deferred-to-C cohort metadata.
5. **Exactly one cohort-settled trigger fired.** `event_3c1c707059724c80a0b804b9a1461d58_delegation_cohort_settled_agent_c` was created at 20:01:43.731Z. Its metadata identified cohort `["agent_a", "agent_b"]` with settlement signals `MESSAGE/MESSAGE` and both response event ids.
6. **C received one coalesced integration turn.** C's next activity reported **3 unread events**. Its input set was exactly A's return, B's return, and the cohort-settled trigger. The cohort trigger was the only triggering event; both peer returns were passive inputs.
7. **C integrated once and closed normally.** C emitted one FINISH using all three input event ids. `reactions_settled` then showed the same C FINISH as the terminal decision settling both A and B MESSAGE boundaries, and the Round closed by `reactions_settled`.

The active Round had only four substantive turns: C delegation, A return, B return, C integration. There was no extra intermediate C model invocation between peer completions.

**Interpretation:** the E-052 timing defect is resolved for the demonstrated case. C's integration wake now follows the settlement of its exact multi-peer delegation cohort rather than first-peer completion order. The implementation preserves public visibility of early peer returns, uses existing delivery coalescing, and preserves causal settlement/normal closure.

This evidence verifies the narrow mechanism implemented in E-054. It does not establish a general fan-out/join abstraction and should not be generalized beyond one C MESSAGE's runnable peer cohort without further evidence.

**Status:** IMPLEMENTED / LIVE VERIFIED. The D-020 delegation-cohort timing issue is COMPLETE.

### E-056 — Temperament-only default personalities
**Date:** 2026-09-14  
**Scope:** [CORE] D-023 refinement after the principal accepted that shared model competence outweighs personality in same-task reasoning. No change to persistent identity, peer status, C's protected coordination responsibilities, routing, timing, or Room protocol.

PR #46 removes V7's mandatory cognitive work products and redefines the standard personalities as general-purpose character/temperament priors:

- **Agent A — exploratory / imaginative / forward-moving.** Naturally notices openings, alternatives, reframings, experiments, optionality, and tractable change. Conversational style is energetic about possibilities without requiring novelty or disagreement.
- **Agent B — measured / discriminating / precise.** Naturally notices overclaiming, ambiguity, hidden assumptions, confidence calibration, and distinctions between what is known and inferred. Conversational style is exacting without requiring opposition or excessive caution.
- **Agent C — contextual / connective / organizational.** Naturally notices relationships, dependencies, sequencing, people, and downstream consequences. Conversational style connects pieces and preserves tensions without requiring universal synthesis.

All three defaults now state explicitly that:

- each participant remains a **fully capable generalist**;
- the **assigned task governs the work**;
- personality should show through attention, emphasis, questions, interaction, and expression;
- personality must not force a different conclusion merely for distinctiveness;
- the former V7 `possibility brief`, `evidence audit`, and `decision map` obligations are removed.

C's protected organizer/coordination responsibilities remain outside the personality layer exactly as required by D-023. The new C personality explicitly distinguishes those protected responsibilities from temperament.

Upgrade behavior adds exact V7 personality-body SHA-256 anchors so existing installations using exact built-in V7 defaults migrate to the new temperament-only defaults while non-matching/custom default text remains preserved:

- A: `5462686efba369af926bee543fdb27b53145fce9c02ad581eefca26057acc503`;
- B: `ca4f58aee7040dccdbfecae94088d2ae88e1eb0366b7a20f234f7a27e0039c34`;
- C: `1c19a8d4d39a7d148c29725f55ee0f8239c45503090f2eb77a143c3df88b1afa`.

Verification:

- an initial PR-head run correctly exposed one stale UI assertion tied to the old C temperament phrase; that assertion was updated in the same PR;
- exact corrected PR head: `20fa1b135426842bba1c65483cbb587b5db5c6fb`;
- PR-head Git tree: `343c68687675825e69f9c9d3300db6b044e7d9a5`;
- GitHub Actions corrected PR run `34892520515`: **319 passed, 2 warnings** in 52.30s;
- PR #46 squash merge: `d83e2b6eca09477e255ea0033843c5834e64e4e1`;
- merge Git tree: `343c68687675825e69f9c9d3300db6b044e7d9a5`, exactly matching the tested corrected PR-head tree;
- canonical-main GitHub Actions run `34892673292`: **319 passed, 2 warnings** in 56.40s.

**Evidence boundary:** E-056 establishes the temperament-only implementation and conservative V7 migration. It does not establish live personality recognizability.

**Next evidence gate:** use interactive role-play conversations with rotating fictional responsibilities, then blind/anonymize the transcripts independently and ask an external evaluator to map conversational behavior to the three temperament descriptions. Solution divergence is not a success criterion.

**Status:** IMPLEMENTED / VERIFIED deterministically; behavioral character-recognizability evaluation NOT YET VERIFIED.

### E-057 — Blind role-play personality recognizability evaluation
**Date:** 2026-09-14  
**Scope:** [ROOM] qualitative blind evaluation of the E-056 temperament-only defaults. This evidence tests recognizability, not implementation correctness.

Three fresh role-play Rooms were run with current temperament-only defaults. The first Museum attempt exposed a deterministic C multi-peer delegation-cohort choreography confound and was discarded. A corrected Museum run, a Remote Film Shoot run, and a Community Festival run were then retained under a stricter control: every substantive MESSAGE invoked exactly one peer, mechanical FINISH/PASS material was excluded from the evaluation packet, and each conversation used an independently permuted anonymous speaker mapping.

The fictional responsibilities were deliberately rotated across conversations. The evaluator received only:

- scenario context;
- fictional role labels;
- substantive MESSAGE dialogue;
- the three temperament descriptions from E-056;
- instructions to classify stable conversational behavior rather than substantive position, professional role, or correctness.

The evaluator did **not** receive the raw Room exports, developer instructions, agent ids, profile snapshots, routing metadata, or the answer key.

Observed classification result:

- Conversation 1 — Museum: **0/3** individual identities correct; **0/1** complete trio.
- Conversation 2 — Remote Film Shoot: **0/3** individual identities correct; **0/1** complete trio.
- Conversation 3 — Community Festival: **1/3** individual identities correct; **0/1** complete trio.
- Aggregate: **1/9** individual identities correct; **0/3** complete trios.

The evaluator's own qualitative conclusion was that the apparent behavioral signal was dominated by the **fictional occupational role** rather than the underlying persistent personality. Its classifications repeatedly mapped creative/purpose roles to exploratory Personality A, operations/sequencing roles to contextual Personality C, and expectation/risk/precision roles to measured Personality B. In the third scenario, the Site/Safety and Vendor/Community roles produced a B/C ambiguity, again reflecting role demands more strongly than persistent identity.

**Interpretation:** this result does not demonstrate that the E-056 personality implementation is defective. It demonstrates that, under a realistic role-play task with differentiated responsibilities, **task/role demands can dominate the observable temperament signal**. Combined with E-043, E-045, E-047, E-049, and E-051, the accumulated evidence supports a broader working conclusion:

- shared-model competence dominates same-task reasoning;
- assigned cognitive responsibility reliably shapes work product;
- explicit occupational/fictional role strongly shapes observable conversational behavior;
- persistent personality text is a comparatively weak signal and has not earned further active calibration effort.

No additional personality wording change is justified by this evaluation. The current E-056 temperament-only defaults remain implemented and may continue as light social/interaction priors.

**Status:** OBSERVED ISSUE for behavioral recognizability; calibration objective NOT ESTABLISHED. Active personality calibration should move to **MONITOR / DEFERRED** unless ordinary Codex Room usage later demonstrates a concrete product problem attributable to insufficient personality distinction.

### E-058 — Neutral default agent profiles
**Date:** 2026-09-14  
**Scope:** [CORE] D-024 removal of distinguishing startup personality/temperament while preserving persistent identity, protected institutional context, Room protocol, optional profile overrides, and C's protected coordination structure.

PR #49 implements neutral startup profiles:

- `AGENT_A_DEFAULT_PERSONALITY`, `AGENT_B_DEFAULT_PERSONALITY`, and `AGENT_C_DEFAULT_PERSONALITY` now resolve to the same empty default body;
- fresh Rooms therefore compose no default `PERSONALITY` section;
- the shared institutional identity/peer layer and Room protocol remain present for A/B/C;
- C still receives its protected organizer/coordination structural instructions, while A/B receive no special protected structural role;
- explicit custom profile text and Room-specific overrides remain supported and still compose through the optional profile layer;
- startup migration adds exact SHA-256 anchors for the E-056 built-in temperament bodies and migrates only those known built-ins to the empty neutral default;
- non-matching custom default profile text is preserved;
- existing Room snapshots/effective instructions are deliberately not rewritten, so the neutral default applies to fresh composition rather than retroactively changing historical Rooms.

Exact E-056 migration anchors were derived from the canonical source bytes before replacement:

- A: `5b11450825c124cd423bc99ad8ff8cffd94a89eec0309750b5aa3cba392db8d5`;
- B: `9532a31035d3c230d44e709d8e0c3ad4ebc94fc6454bfa3eff3c487500ca4ded`;
- C: `8b689f1894125f106023958d16385c7656287cdfb57b6d3f476406ed164e3993`.

Verification:

- PR #49 exact head: `2627fbd35b14214988a1828f788adb02163b03f8`;
- tested PR-head Git tree: `be52f9a92655ce28f6c3655fc39f1b72922d7d39`;
- PR Actions run `34901569309`: **321 passed, 2 warnings** in 54.08s;
- squash merge: `833d3498c75fe4d7e2a3e76efda362b421341431`;
- merge Git tree: `be52f9a92655ce28f6c3655fc39f1b72922d7d39`, exactly matching the tested PR-head tree;
- canonical-main Actions run `34901711440`: **321 passed, 2 warnings** in 53.59s;
- direct canonical-main source inspection confirmed the neutral default constant is empty, the retired E-056 temperament prose is absent from the active default source, and the E-056 migration anchor remains present.

**Evidence boundary:** E-058 verifies neutral default profile composition and conservative built-in migration deterministically. It does not retroactively rewrite existing Room snapshots and does not implement the proposed dynamic cognitive-posture capability.

**Status:** IMPLEMENTED / VERIFIED deterministically. D-024 neutral startup profiles are COMPLETE.

### E-059 — C temporary cognitive framing
**Date:** 2026-09-14  
**Scope:** [CORE] D-025 protected-coordination instruction allowing C to assign temporary task-specific cognitive frames to A/B through ordinary natural-language delegation.

PR #51 changes only C's protected structural coordination instructions plus regression coverage and governing documentation. The new instruction explicitly allows C, when useful, to assign A and/or B:

- temporary working postures or perspectives;
- scopes and constraints;
- evidence standards;
- expected deliverables;
- temporary roles or personas.

The same protected instruction also states that:

- frames are chosen from the objective rather than fixed A/B specialties;
- differentiation is optional; identical, overlapping, or independent work may be better;
- frames are delegation instructions only and do not alter persistent identity, saved profile, or peer standing;
- C may not dictate conclusions;
- A/B may challenge the framing, reject a mistaken premise, expand scope when necessary, or return any conclusion supported by their own judgment and evidence.

No posture registry, database object, profile mutation, or UI mechanism was added. The capability uses the existing Room MESSAGE/delegation path.

Verification:

- PR #51 exact head: `547ee44f5fe3215841d22ee26cfc098c2f1299ab`;
- tested PR-head Git tree: `dfcc00c242acedb7c0ce5b52276a1784bc103e76`;
- PR Actions run `34902792601`: **322 passed, 2 warnings** in 54.35s;
- squash merge: `36eafaadd7b7a162ca7d4e8195e90f9498da0b21`;
- merge Git tree: `dfcc00c242acedb7c0ce5b52276a1784bc103e76`, exactly matching the tested PR-head tree;
- the first canonical-main Actions attempt on run `34902936137` produced one failure in pre-existing timing-sensitive test `test_finish_preserves_peer_turn_that_is_already_running` (expected peer status `running`, observed `idle`), with **321 passed, 1 failed, 2 warnings**. No D-025 code changed after that attempt;
- rerunning that exact workflow job on the same canonical-main commit succeeded with **322 passed, 2 warnings** in 53.27s.

**Interpretation:** D-025's implementation is verified on the exact tested bytes and on canonical main. The transient first-attempt orchestrator timing failure was not caused by an intervening D-025 code change and is not claimed fixed here; it is recorded as verification context rather than expanded into a separate repair effort.

**Evidence boundary:** E-059 verifies that C is explicitly instructed and structurally authorized to use temporary cognitive framing through existing natural-language delegation. It does not establish how well C will choose frames in live ordinary use, and it does not implement persistent posture state or deterministic profile rewriting.

**Status:** IMPLEMENTED / VERIFIED deterministically. Live usefulness of C-selected cognitive frames remains to be observed in ordinary Room use.

### E-060 — First live D-025 allocation test exposed redundant dual-peer cognition
**Date:** 2026-09-14  
**Scope:** [ROOM] first ordinary-use test of neutral startup plus D-025 temporary cognitive framing.

Fresh Room `room_c9d24cf2010d465482ae47aaf362e341` used neutral default profiles for A/B/C with no Room overrides, task overlay, or participant overlays. C received a real product-architecture question and was explicitly told to use the Room as it judged useful without assuming every participant needed to be involved.

Observed behavior:

- C correctly exercised its coordinator role and chose to invoke both A and B;
- C described the choice as gathering "two independent assessments";
- both peers received substantially the same assignment: evaluate the tradeoff between C-led ad hoc delegation and formal temporary-specialization machinery, focusing on the smallest worthwhile increment, operational failure modes, and evidence that would justify more structure;
- A and B returned highly convergent recommendations: keep C-led delegation, add only a lightweight delegation/task brief, avoid formal role machinery, and wait for observed recurrence before adding structure;
- the delegation-cohort barrier behaved correctly: A's return did not wake C early, B returned, the cohort settled, and C consumed both returns plus the settlement trigger in one integration turn;
- C integrated the returns into a coherent final recommendation rather than merely concatenating them.

Interpretation:

- D-025's coordination authority and live delegation mechanics worked;
- differentiated cognitive framing was **not** demonstrated in this run;
- the two peer calls bought materially overlapping cognition, consistent with the accumulated evidence that neutral same-model agents tend to converge when given the same task;
- the run therefore exposed an allocation-economics problem: if C does not need distinct cognitive work from both peers, invoking both is usually not worth the extra token and coordination cost.

This observation motivates D-026: use the fewest peers that add sufficient value, and require meaningfully differentiated cognitive responsibilities whenever C invokes both A and B.

**Status:** OBSERVED ISSUE for dual-peer allocation efficiency; coordination mechanics PASS; differentiated framing NOT DEMONSTRATED.

### E-061 — D-026 peer-allocation economy and mandatory dual-peer differentiation
**Date:** 2026-09-14  
**Scope:** [CORE] protected C coordination rule implementing D-026.

PR #53 updates C's protected structural instructions so that:

- every additional peer invocation must be expected to earn its cognitive and token cost;
- C should use the fewest peers that can add sufficient value;
- if one peer is enough, C should invoke one rather than both;
- if C invokes both A and B in the same delegation, their cognitive responsibilities must be meaningfully differentiated;
- the differentiation must concern a substantive dimension expected to create complementary value, such as perspective, method, evidence source, scope, constraint, deliverable, or verification responsibility;
- cosmetic labels and substantially duplicate analyses do not satisfy the rule;
- independent verification must still differentiate method or responsibility rather than duplicating the same assignment;
- D-025's temporary-frame, persistent-identity, peer-status, and no-dictated-conclusion guardrails remain intact.

Regression coverage verifies that these requirements appear only in C's protected structural instructions and not in A/B's default instructions.

Verification:

- PR #53 exact head: `280c04b69418cefcd2c2a91ea003ada7872f7717`;
- tested PR-head Git tree: `c8e635761d4d7aaf5fe619a90e8e86da86dd85cb`;
- PR Actions run `34905911537`: **322 passed, 2 warnings** in 50.14s;
- squash merge: `057d5e2ca67356c6dfa642fb1c6bad6e5b71634e`;
- merge Git tree: `c8e635761d4d7aaf5fe619a90e8e86da86dd85cb`, exactly matching the tested PR-head tree;
- canonical-main Actions run `34906039452`: **322 passed, 2 warnings** in 53.51s.

**Evidence boundary:** E-061 verifies the protected coordination rule and exact merged bytes. It does not yet establish live compliance by C in a fresh Room.

**Status:** IMPLEMENTED / VERIFIED deterministically. Live behavioral verification remains next.

### E-062 — D-026 live pass exposed unnecessary peer-to-peer runnable invocation
**Date:** 2026-09-14  
**Scope:** [ROOM] clean live test of D-026, followed by observation of invocation-economy leakage outside C's initial delegation.

Fresh Room `room_19a4fcb993294de2a2becae5961307df` used the full household-move objective as the opening Round prompt, with C as starter, neutral empty A/B/C profiles, and no Room/task/participant overlays.

Primary D-026 behavior:

- C invoked both A and B from the opening objective;
- C assigned meaningfully different cognitive responsibilities:
  - A: propose the end-to-end operating workflow and smallest useful structured tracker/tooling layer;
  - B: assess where multi-agent AI judgment adds value, especially research/decisions/risk, and identify failure modes/overengineering traps;
- A returned an operating-plan / workflow / structured-tooling recommendation;
- B returned an evidence-sensitive judgment / risk / failure-mode recommendation;
- the delegation cohort settled only after both primary returns;
- C integrated the complementary outputs into one practical recommendation.

**D-026 result:** LIVE PASS. The dual-peer assignments were substantively differentiated and produced complementary value.

A separate coordination-economy issue then appeared:

- B's return requested runnable delivery to both A and C even though B's substantive answer was already publicly readable to A;
- C's runnable delivery was correctly deferred by the delegation-cohort mechanism, but A was awakened immediately;
- A then spent an additional turn reviewing B's answer and sent a refinement to C;
- C had already integrated the primary cohort and issued FINISH, so A's refinement reopened C for another turn;
- the extra A review turn reported **23,249** tokens and the resulting C reopen reported **25,459** tokens, about **48,708 reported call-tokens** beyond the primary cohort, without being required by C's original bounded delegation.

Interpretation:

- D-026 is live verified for C's peer-count/differentiation behavior;
- public readability and runnable invocation are mechanically distinct, but the participant instructions did not yet make the economic meaning of that distinction explicit;
- direct A/B collaboration remains valuable when additional cognition is actually needed, but invoking a peer merely to expose an already-public message creates avoidable model work and can cascade into unnecessary follow-up/reopen turns.

This observation motivates D-027: invocation should request immediate cognition, not visibility; a peer completing bounded work for C should normally return to C without waking the other delegated peer unless that peer's additional cognition is materially needed.

**Status:** D-026 LIVE VERIFIED. Peer-to-peer invocation economy OBSERVED ISSUE motivating D-027.

### E-063 — D-027 room-wide invocation economy and explicit no-wake MESSAGE
**Date:** 2026-09-14  
**Scope:** [CORE] shared Room protocol and routing-schema support implementing D-027.

PR #55 implements invocation economy for all participants:

- the protected Room protocol tells A/B/C that invocation requests immediate cognition, not visibility;
- messages remain public/readable without making every reader runnable;
- peers should invoke only participants whose immediate cognition is expected to add material value;
- a peer completing bounded work for C should normally return to C without waking the other delegated peer unless that peer's cognition is materially needed;
- direct A/B collaboration remains permitted when additional peer cognition is useful;
- `invoke_targets: []` is now a valid MESSAGE value meaning public/readable delivery with no runnable peers;
- `invoke_targets: null` retains legacy all-peer fanout compatibility;
- the runtime's existing target resolver already maps an explicit empty target list to no runnable peers, so the implementation required removing the model-level empty-list rejection and exposing the semantics in the runtime prompt/protected protocol rather than changing scheduler behavior.

Regression coverage verifies:

- all three effective default instruction sets include the invocation-economy rule;
- empty `invoke_targets` is accepted for MESSAGE;
- a public MESSAGE with `invoke_targets: []` remains readable by both peers while waking neither;
- metadata records empty requested/runnable recipients and counts both legacy fanout invocations as avoided;
- existing selective routing, C delegation-cohort timing, integration, and other Room behavior remain under the full regression suite.

Verification:

- first PR-head run `34911744037` on head `b76c7463c0d1d88e94e7fa57da4e8c8b1537bc51`: **323 passed, 1 failed, 2 warnings**. The sole failure was an obsolete test that still expected empty `invoke_targets` to raise `ValidationError`; the new no-wake runtime test itself passed;
- corrected PR #55 exact head: `493b917108a78e8e6a5778a1734e02ce71c92778`;
- corrected tested PR-head Git tree: `da51b39fb0f18d66f062470e50652a76572243a7`;
- corrected PR Actions run `34911927151`: **324 passed, 2 warnings** in 64.09s;
- squash merge: `18337b2c678bdf258f84591b6f9443e969c65d1c`;
- merge Git tree: `da51b39fb0f18d66f062470e50652a76572243a7`, exactly matching the corrected tested PR-head tree;
- canonical-main Actions run `34912081457`: **324 passed, 2 warnings** in 63.70s.

**Evidence boundary:** E-063 verifies the exact implementation, protected instruction composition, and no-wake routing primitive. It does not yet establish that live A/B/C behavior will consistently choose economical `invoke_targets` in ordinary Rooms.

**Status:** IMPLEMENTED / VERIFIED deterministically. Live behavioral compliance remains to be observed.

### E-064 — D-027 live invocation-economy compliance
**Date:** 2026-09-14  
**Scope:** [ROOM] clean fresh-Room live verification of D-027.

Fresh Room `room_b49a10be02e340a6bb8fa6f8e76eba0f` used a two-day community science-fair planning objective with C as starter, neutral empty A/B/C profiles, and no Room/task/participant overlays.

Observed routing:

- C invoked both peers once and gave them substantively differentiated responsibilities: A owned minimum viable format, workstreams, owners, and the six-week critical path; B owned early decisions, budget allocation, risks/contingencies, and anti-overengineering guardrails.
- A returned its bounded result with `invoke_targets: []`. The MESSAGE remained readable to B and C, requested no runnable recipients, made neither peer runnable, and recorded **2 legacy fanout invocations avoided**.
- B returned its bounded result with `invoke_targets: ["agent_c"]`. The MESSAGE remained readable to A and C; A was not runnable, while C's requested invocation was deferred by the existing delegation-cohort rule until the cohort settled. This recorded **1 legacy fanout invocation avoided**.
- No A↔B peer-review wake occurred, no extra peer cognition was purchased merely for visibility, and no post-integration reopen cascade occurred.
- Once both peer returns had settled, CORE emitted one `delegation_cohort_settled` trigger. C consumed both peer returns as passive inputs plus that trigger in one integration batch and issued the final recommendation.
- The Room used exactly four model turns: C delegation, A return, B return, and C integration/FINISH.

This is the live behavior D-027 was intended to produce. Compared with E-062, the unnecessary A review and C reopen were absent.

**Settlement note:** A's explicit no-wake `invoke_targets: []` return reached C passively through the cohort path rather than as a runnable/deferred causal edge. After C FINISH, the observer therefore briefly emitted `finish_waiting` for A before quiescent reconciliation closed the Room with no runnable work. No extra model invocation resulted and C had already consumed and integrated A's return. This trace is retained as a settlement/observer limitation of the exact run; it does not undermine the D-027 invocation-economy result.

**Status:** D-027 LIVE VERIFIED. No further dedicated D-027 live test is currently warranted; monitor ordinary Rooms for regression.

### E-065 — A3 whole-system housekeeping, efficiency, and operational assurance audit
**Date:** 2026-09-14  
**Scope:** Read-only whole-system audit of canonical repository baseline `9465863b7a86b7081af38c7d87bcabb5964dcc79`, maintained Project sources, current GitHub repository/CI state, current source/tests, and the latest D-027 live Room evidence.

The audit looked specifically for housekeeping debt, avoidable operating cost, assurance gaps, observability weaknesses, persistence/recovery risks, stale documentation, and complexity that ordinary feature production can overlook.

Material findings:

- **Core execution and coordination remained structurally strong.** Source inspection did not demonstrate a new material defect in exact-turn recovery, per-agent serialization, stale-result protection, selective readable/runnable routing, delegation-cohort integration, rollover provenance, or deterministic custom-capability registration/inheritance. D-027's latest live evidence remained a clean four-turn invocation-economy pass under E-064.
- **Model/effort economy is unresolved.** `codex_room/agent.py` pins every Room thread/turn to `gpt-5.6-terra` with `high` reasoning. This is an implemented static policy, but the audit found no settled decision or empirical evidence establishing that universal Terra/high is the economically correct policy for all work. This creates an explicit P1 follow-up: measure before changing model/effort allocation.
- **Supported-Python metadata is inconsistent with source.** `pyproject.toml` declares `requires-python = ">=3.10"` and README says Python 3.10+, while current source imports `enum.StrEnum` and otherwise relies on the current 3.11-era runtime surface. CI tests only Python 3.12. The support-floor claim therefore needs correction or deliberate compatibility work.
- **Maintained/user-facing documentation has drift.** README still says the launcher sets `CODEX_ROOM_CODEX_BIN` to the desktop runtime even though the launcher defaults to the SDK-pinned runtime, and README still describes C as using a fixed read-only Integrator template despite current neutral replaceable profiles plus protected C coordination structure. `04_ARCHITECTURE_AND_CURRENT_STATE.md` is dated 2026-09-12 and still says P4.5 is IN PROGRESS while current Development Control/E-040 close P4.5/P4. Register freshness headers also lag later entries. Development Control itself contains substantial completed experimental history that duplicates durable evidence and increases routine context cost.
- **Repository branch hygiene is stale but mechanically clear.** GitHub exposed 55 non-`main` branches; all 55 are heads of already-merged PRs, there are zero open PRs, `delete_branch_on_merge` is false, and no branch is currently protected. This is cleanup debt, not active work.
- **Runtime provenance is weak.** `/api/health` exposes authentication health but not the exact Codex Room source/build identity, SDK/runtime version, or configured Room model/effort. The application package/API version remains `0.1.0`. Exact-live-version questions therefore require external repository/process reasoning rather than one deterministic status surface.
- **Unexpected watchdog failures can be silent.** The watchdog loop catches arbitrary exceptions and retries after sleep without persisting/logging the unexpected exception through an operator-visible health signal.
- **Persistent-data maintenance is mostly release/manual rather than routine.** The SQLite design uses WAL, foreign keys, busy timeout, atomic transaction patterns, durable execution records, and restart recovery. The active runtime does not expose a routine `quick_check`/integrity health path or an automatic verified backup/restore workflow.
- **Assurance is broad but platform-asymmetric.** The last code-bearing canonical suite under E-063 passed 324 tests with 2 warnings; source inspection counted 269 test functions before parametrization. Hosted CI runs only Ubuntu/Python 3.12 even though ordinary operation relies heavily on Windows launcher/PowerShell/shell behavior. One previously recorded timing-sensitive test flake remains documented. The specialized Playwright browser script is manual and resolves an unpinned `@playwright/test` package at execution time.
- **Dependency policy is reproducible but freshness/security review is not routine.** `constraints-test.txt` deliberately pins the known-good stack, including `openai-codex==0.147.0`; no routine dependency-advisory/freshness check is part of normal CI.
- **Custom capability trust boundaries remain explicit.** Registered custom capabilities retain exact package/verification/registration provenance and bounded execution checks. Their permission declarations are intentionally not per-capability OS enforcement; they rely on the ambient Room sandbox. The audit found no evidence warranting immediate redesign of this settled boundary.
- **Passive no-wake deliveries are Round-scoped.** Pending passive deliveries such as those visible in E-064 are filtered by active Round, sequence/watermark, runnable trigger, and FINISH boundary before any future claim. The audit did not find evidence that old passive deliveries silently bleed into later Round cognition.
- **Some hardening ideas remain low-priority rather than demonstrated defects:** shareable/redacted exports, explicit non-loopback-host safeguards, WebSocket overflow-triggered resync, formal numbered schema migrations, large-module refactoring, and stronger per-capability isolation.

Resulting work allocation:

1. record and perform low-risk environment/document truth cleanup and context-hygiene work;
2. clean merged-branch residue and adopt cheap repository hygiene;
3. establish deterministic runtime provenance/maintenance health and usage instrumentation;
4. reopen P1 only as an empirical model/reasoning-effort economy investigation, with no automatic routing policy assumed in advance;
5. add bounded persistent-data integrity/backup operations;
6. repair verification-platform debt and add deliberate dependency-review mechanics;
7. leave lower-value hardening and large refactors deferred/monitor unless later evidence demonstrates a costly problem.

**Evidence boundary:** This audit did not inspect the principal's current local `C:\\Codex Room` working tree, running process tree, local database size/integrity, or untracked/generated files. It therefore establishes the canonical repository/system findings above, not a clean bill of health for the current local machine state.

**Assessment:** A3 COMPLETE. Core runtime/coordination: GOOD. Housekeeping, operational observability, and model/effort economy: PARTIAL with bounded remediation work identified.

### E-066 — I-007 environment/document truth and context-hygiene repair
**Date:** 2026-09-14  
**Scope:** [CORE metadata + documentation] first A3 remediation item.

PR #57 repairs the concrete I-007 drift identified by E-065 without changing Room routing, model policy, agent cognition, or persistent runtime behavior.

Changed contracts/synthesis:

- `pyproject.toml` now declares Python **3.11+**, matching the current source runtime surface instead of advertising unsupported Python 3.10;
- README now describes the SDK-pinned Codex runtime as the default, treats the current Terra/high configuration as implementation state rather than settled final economics, describes A/B/C replaceable profile bodies plus C's protected coordination structure, and delegates roadmap ownership to Development Control/Product Vision instead of maintaining a stale duplicate feature list;
- Architecture & Current State is resynthesized through 2026-09-14, closes P4.5 using E-040, preserves the neutral-profile/protected-structure model, and points to E-064 as the latest D-027 live behavior;
- Decision Register and Repository & Operations freshness/landmarks are updated to current maintained state, including the Python 3.11 floor, P4/custom-capability source landmarks, and the A2-retired P3 review caveat;
- Development Control removes roughly **58.6 KB** of duplicated completed implementation/experiment narration, replacing it with a compact current-result table that points to the existing Decision/Evidence owners. Historical personality experiments remain preserved in E-042 through E-057 rather than being duplicated in the volatile control document.

Exact PR-head verification before closeout documentation:

- PR #57 head: `ab70c6dec2fb650fc32797ac3ce9ab45d0b7a7eb`;
- GitHub Actions run `34916314320`;
- constrained installation completed successfully under the corrected package metadata;
- the canonical `python -m pytest -q` step completed successfully.

**Evidence boundary:** the Python support-floor repair declares 3.11+ based on the current source/runtime contract; CI continues to execute Python 3.12 only. Cross-version/cross-platform matrix expansion belongs to I-011, not I-007.

Merge/canonical-main confirmation:

- PR #57 squash-merged as `d6882ff0d650242dfafdbdc707315df7d459b6ae`;
- canonical-main GitHub Actions run `34916627006` completed successfully;
- constrained installation and the full `python -m pytest -q` step both passed on the exact merged commit.

**Status:** I-007 COMPLETE / IMPLEMENTED / VERIFIED on canonical `main`.

### E-067 — I-008 repository branch-hygiene preflight
**Date:** 2026-09-14  
**Scope:** Read-only GitHub repository-state verification for the second A3 remediation item.

Fresh canonical GitHub inspection after I-007 established:

- canonical `main` at audit time: `03eef56b8836a96ba1e34169399d6f8c53abdc37`;
- **56** non-`main` branches exist;
- **all 56** names are heads of pull requests with non-null `merged_at`;
- **zero** pull requests are open;
- no non-`main` branch is the head of an open pull request;
- repository setting `delete_branch_on_merge` remains `false`;
- a ruleset read returned HTTP 403 with GitHub's message that this private repository requires GitHub Pro (or public visibility) for that feature.

Verified safe-delete branch set:

- `core/default-personality-redesign`
- `core/personality-layer-composition`
- `d020-c-delegation-settlement`
- `d020-delegation-cohort-timing`
- `d020-triad-migration`
- `d023-temperament-only-defaults`
- `d023-v6-2-personality-contracts`
- `d023-v7-complementary-work-products`
- `d024-neutral-default-agents`
- `d025-c-temporary-cognitive-framing`
- `d026-peer-economy-differentiation`
- `d027-invocation-economy`
- `docs-cg1-settlement-state`
- `docs-d020-delegation-timing`
- `docs-d020-timing-live-verified`
- `docs-d023-calibration-monitor`
- `docs-d023-coordination-gate`
- `docs-d023-roleplay-personality-eval`
- `docs-d023-v6-2-state`
- `docs-d023-v7-state`
- `docs-d024-neutral-default-verification`
- `docs-d025-cognitive-framing-verification`
- `docs-d026-peer-economy-verification`
- `docs-d027-invocation-economy-verification`
- `docs/default-personality-implementation`
- `docs/personality-layer-governance`
- `docs/personality-v4-evidence`
- `docs/personality-v5-evidence`
- `fix/early-triad-profile-migration`
- `fix/i-001-complete-event-history`
- `fix/p4-1-capability-shell-wrapper`
- `fix/p4-1-sdk-activity-types`
- `fix/p4-2-compact-list-test`
- `fix/reproducible-test-deps`
- `i-004-readme-triad-cleanup`
- `i007-truth-context-hygiene`
- `p4-1-deterministic-assertions`
- `p4-2-capability-registry`
- `p4-2-powershell-provenance`
- `p4-2-registry-preference`
- `p4-3a-capability-telemetry`
- `p4-3b-find-files`
- `p4-3c-search-text`
- `p4-3d-compare-files`
- `p4-3e-standalone-capability-invocations`
- `p4-4a-custom-capability-package`
- `p4-4b-verify-register-custom-capabilities`
- `p4-4c-dynamic-custom-registry`
- `p4-4d-agent-custom-capability-authoring`
- `p4-4e-robust-capability-input-transport`
- `p4-5-live-proof-closeout`
- `p4-5a-lineage-binding-inheritance`
- `p4-umbrella-closeout`
- `personality-v4`
- `personality-v5`
- `support-kill-full-room-tree`

The connected GitHub tool surface available to this Project exposes no branch-ref deletion action and no repository-settings write action. Therefore E-067 proves the safe deletion set and configuration gap but does not claim those mutations were performed.

Post-delete verification:

- the operator executed the bounded deletion script against the exact 56-branch set recorded above;
- fresh GitHub inspection then returned exactly one branch: `main`;
- non-`main` branch count is **0**;
- open pull-request count remains **0**;
- canonical `main` remains at `22a6f98e50805f47ad774b6f6c929f7719ba54c6`;
- `delete_branch_on_merge` is still `false`.

Final closeout verification:

- repository setting `delete_branch_on_merge` is now `true`;
- branch count is **1**, consisting only of canonical `main`;
- non-`main` branch count is **0**;
- open pull-request count is **0**;
- default branch remains `main`.

Minimal `main` protection remains unavailable through the checked ruleset path on this private-repository plan; no heavyweight workaround was introduced.

**Status:** I-008 COMPLETE / IMPLEMENTED / VERIFIED. Historical merged-branch residue is removed and future merged PR head branches are configured for automatic deletion.

### E-068 — I-009 runtime provenance and maintenance-health implementation
**Date:** 2026-09-14  
**Scope:** [CORE] bounded A3 remediation for deterministic runtime identity, maintenance-loop health, and P1 execution facts.

Implemented behavior:

- `/api/health` now exposes process-start Codex Room provenance: application version, Git source revision when available, source-dirty state when available, and a SHA-256 fingerprint over the runtime package/source surface;
- the same health response exposes Python version, installed `openai-codex` version, and the configured Room model/reasoning-effort policy;
- the watchdog now records cycle start/success, cumulative and consecutive unexpected-failure counts, last unexpected error/time, and an explicit `starting` / `healthy` / `degraded` state. A later successful cycle clears the consecutive-failure degradation but deliberately retains the last error and cumulative failure count for the lifetime of the process;
- `agent_executions` now persists `model` and `reasoning_effort` beside the already-durable `usage_json`. Existing open execution rows are backfilled with the current policy when reclaimed, so P1 can analyze completed execution usage together with the policy that launched the execution;
- the change remains intentionally narrow: no dashboard, general metrics/logging platform, or automatic model-routing policy was introduced.

Verification:

- PR #58 tested head: `0d030fc938d2edb4fdcff4d6cb985de9f816ffd6`;
- PR-head GitHub Actions run `34929088157`: constrained installation succeeded; full `python -m pytest -q` passed **327 tests, 2 warnings**;
- PR #58 squash-merged as canonical code commit `05f2dc4eb9e998122685d28e9383f2f54e419238`;
- canonical-`main` Actions run `34929208446` on that exact merge commit: constrained installation succeeded; full `python -m pytest -q` passed **327 tests, 2 warnings**;
- automatic merged-branch cleanup removed the PR branch after merge, leaving canonical `main`.

Evidence boundary:

- this proves the canonical implementation and deterministic test behavior, not that the principal's currently running local process has already pulled/restarted onto the new commit;
- watchdog error history is process-scoped rather than a cross-restart incident log. Within one process, a transient failure remains visible after recovery through the retained last-error and cumulative-failure fields;
- the source fingerprint identifies the package/source bytes visible at process-start provenance capture; Git revision/dirty fields are supplemental and may be null outside a Git checkout.

**Status:** I-009 IMPLEMENTED / VERIFIED on canonical `main`. Local live-runtime verification remains a deployment/operator step after pulling and restarting the Room.

### E-069 — I-009 local live-runtime provenance verification
**Date:** 2026-09-15  
**Scope:** [CORE live deployment] Principal-operated Windows Codex Room after pulling and restarting canonical `main`.

The principal queried `http://127.0.0.1:8765/api/health` from the local Codex Room installation. The running process reported:

- `application.version`: `0.1.0`;
- `application.source_revision`: `6168c80938c7e9172a86651d3a9953fb66c2e219`, matching canonical `main` at verification time;
- `application.source_dirty`: `false`;
- `application.source_fingerprint_sha256`: `f115abeb99ecfccb9b6f9a90608ed8d3c4fa2480c6729231a4ab18e52b586cf4`;
- Python: `3.12.10`;
- installed `openai-codex`: `0.147.0`;
- configured Room policy: `gpt-5.6-terra` with `high` reasoning effort;
- Codex authentication: authenticated ChatGPT Plus account;
- watchdog status: `healthy`;
- watchdog failure count: `0`;
- watchdog consecutive failures: `0`;
- watchdog last error: none.

This closes the deployment-evidence boundary left open by E-068: the new I-009 provenance/health surface is not only implemented and CI-verified on canonical source, but is also running successfully in the principal's local Personal Codex Room environment on the exact canonical revision.

**Status:** I-009 IMPLEMENTED / VERIFIED / LIVE VERIFIED.

### E-070 — P1 authenticated local model-catalog probe
**Date:** 2026-09-15  
**Scope:** [P1 exploratory / zero-turn] Principal's authenticated local `openai-codex==0.147.0` runtime on ChatGPT Plus.

An initial targeted SDK `codex.models()` probe confirmed Sol, Terra, and Luna but was later recognized as incomplete because the probe filtered to those IDs. A corrected unfiltered zero-turn probe then returned the complete visible local catalog:

- `gpt-5.6-sol` — visible; catalog default; default reasoning effort `low`; supports `low`, `medium`, `high`, `xhigh`, `max`, `ultra`;
- `gpt-5.6-terra` — visible; default reasoning effort `medium`; supports `low`, `medium`, `high`, `xhigh`, `max`, `ultra`;
- `gpt-5.6-luna` — visible; default reasoning effort `medium`; supports `low`, `medium`, `high`, `xhigh`, `max`;
- `gpt-5.5` — visible previous-generation model; default reasoning effort `medium`; supports `low`, `medium`, `high`, `xhigh`.

The local catalog returned no Astra model. This evidence establishes only the capabilities of the principal's currently deployed authenticated SDK/runtime; it does not by itself establish whether Astra would become available after a supported runtime upgrade or under different account/workspace conditions.

The optional `fast`/priority service tier is visible for all returned models but remains outside the P1 admission test because changing speed tier would confound model/effort economy with a separate increased-usage choice.

First admission matrix remains:

1. Luna / medium — low-cost current-generation reference;
2. Terra / medium — current-generation balanced model at default effort;
3. Terra / high — current production baseline;
4. Sol / medium — current-generation higher-capability comparison at moderate effort.

GPT-5.5 is retained as an available legacy comparator but is not admitted to the first benchmark unless later evidence makes it economically relevant. Higher reasoning levels (`xhigh`, `max`, `ultra`) are likewise deferred until the first comparison shows a reason to spend on them.

**Status:** P1 catalog gate PASSED after corrected unfiltered probe. No production model-selection policy changed.

### E-071 — P1 Codex SDK/runtime standard advanced to 0.154.0
**Date:** 2026-09-15  
**Scope:** [CORE] dependency/runtime upgrade supporting the P1 model-economy investigation.

Motivation:

- the principal's Codex desktop UI visibly exposed Astra while Codex Room's pinned `openai-codex==0.147.0` runtime did not return Astra from an unfiltered `codex.models()` probe;
- the published Codex runtime line after the Astra client floor provides a matched `openai-codex==0.154.0` / `openai-codex-cli-bin==0.154.0` pair;
- production Room cognition remains explicitly pinned in Codex Room source to `gpt-5.6-terra` with `high` reasoning, so advancing the SDK/runtime does not itself change the Room model-selection policy.

Implementation:

- `pyproject.toml` now requires `openai-codex>=0.154,<1`;
- `constraints-test.txt` pins both `openai-codex==0.154.0` and `openai-codex-cli-bin==0.154.0`;
- one restart/reconciliation test fixture was updated for the 0.154 `AsyncTurnHandle` constructor contract, which now subscribes to turn notifications during construction. No production recovery logic changed.

Verification history:

- PR #59 initial dependency-only head installed the 0.154.0 pair successfully but full CI found one fixture incompatibility: **326 passed, 1 failed, 2 warnings** in run `34943186987`. The failure occurred because the test substituted bare `object()` for the SDK client while the new handle constructor requires the client's notification-subscription surface;
- after the narrow fixture correction, PR-head run `34943392571` passed **327 tests, 2 warnings**;
- final exact PR head `27c4dab1809f576ee4fadeaaa06c906b387f8842`, including refreshed dependency-provenance comments, passed **327 tests, 2 warnings** in run `34943555791`;
- PR #59 squash-merged as `e08f06c483b2040aa857bc43aa637d870281f5a9`;
- canonical-`main` run `34943692719` on that exact merge commit passed **327 tests, 2 warnings**;
- automatic merged-branch cleanup removed the feature branch.

Evidence boundary:

- canonical CORE now standardizes on the matched 0.154.0 SDK/runtime pair;
- the principal's local installation has not yet been reinstalled/restarted onto that dependency pair in this evidence record;
- Astra exposure through the upgraded local SDK/runtime remains to be verified directly with the zero-turn model-catalog probe before P1 spends model usage on comparison turns.

**Status:** Codex SDK/runtime 0.154.0 IMPLEMENTED / VERIFIED on canonical `main`; local live deployment verification pending.

### E-072 — P1 local 0.154 deployment and Astra SDK exposure
**Date:** 2026-09-15  
**Scope:** [P1 exploratory / live local verification] Principal's Windows Codex Room after pulling/reinstalling/restarting canonical CORE.

Live `/api/health` reported:

- application source revision `3cfae1d7c730f38b85f2968fc07a2679f76b67ea`, matching canonical `main` at verification time;
- `source_dirty=false`;
- source fingerprint `41602ee1959273e0fe12cc39e564cc5fa8e7047435a1451735a50ef4bb3ccfd3`;
- Python `3.12.10`;
- `openai-codex==0.154.0`;
- production Room policy unchanged at `gpt-5.6-terra` / `high`;
- authenticated ChatGPT Plus account;
- watchdog state `starting` immediately after restart with zero cumulative/consecutive failures and no recorded error. This capture occurred before the first watchdog cycle and therefore is not evidence of the later `healthy` state.

The principal then ran the corrected **unfiltered** zero-turn `codex.models()` probe through the same local virtual environment. The complete visible catalog was:

- `gpt-6-astra` — visible, SDK default, default effort `low`, supports `low`, `medium`, `high`, `xhigh`, `max`, `ultra`; `multi_agent_version=v2`;
- `gpt-5.6-sol` — visible, default effort `low`, same six reasoning levels; `multi_agent_version=v2`;
- `gpt-5.6-terra` — visible, default effort `medium`, same six reasoning levels; `multi_agent_version=v2`;
- `gpt-5.6-luna` — visible, default effort `medium`, supports through `max` but not `ultra`; `multi_agent_version=v1`;
- `gpt-5.5` — visible previous-generation comparator, default effort `medium`, supports `low` through `xhigh`.

This resolves the earlier UI/SDK discrepancy: Astra access was present on the account, but the former 0.147 SDK/runtime did not expose it. The verified 0.154.0 standard does.

First paid P1 admission matrix is therefore:

1. Luna / medium;
2. Terra / medium;
3. Terra / high — current production baseline;
4. Sol / medium;
5. Astra / medium.

Using `medium` across Luna/Terra/Sol/Astra isolates model-tier effects at one common effort; Terra `medium → high` separately measures the marginal value of the current extra reasoning spend. Astra `low` is intentionally deferred until Astra first demonstrates enough quality/economic value to justify a second-stage effort comparison.

**Status:** P1 local runtime/catalog gate PASSED. Astra is admitted to the first paid comparison. No production model-selection policy changed.

### E-073 — P1 first paid model/effort admission benchmark
**Date:** 2026-09-15  
**Scope:** [P1 exploratory] 15 isolated SDK turns on `openai-codex==0.154.0`, three objectively scored task families, five model/effort configurations.

Benchmark design:

- fresh ephemeral thread per turn;
- service tier unchanged;
- read-only sandbox with developer instruction prohibiting tools/files/network/external sources;
- three self-contained task families: evidence grounding, constraint planning, and code review;
- 10 objectively scored labels per task;
- configurations: Luna/medium, Terra/medium, Terra/high (production baseline), Sol/medium, Astra/medium;
- deterministic shuffled execution order.

Observed quality / duration:

| Configuration | Score | SDK failures | Aggregate duration |
|---|---:|---:|---:|
| Luna / medium | 30/30 | 0 | 21.650 s |
| Terra / medium | 30/30 | 0 | 21.053 s |
| Terra / high | 30/30 | 0 | 26.293 s |
| Sol / medium | 28/30 | 0 | 25.333 s |
| Astra / medium | 30/30 | 0 | 20.907 s |

Sol's two misses occurred in the evidence-grounding task: claims whose facts were explicitly unreported were labeled contradicted rather than unknown even though the accompanying rationale itself said training completion and staffing additions were not reported. This single-run miss is evidence about this benchmark instance, not sufficient evidence that Sol is generally inferior.

The generated JSON's top-level summary incorrectly printed all token totals as zero. This is a benchmark-reporting defect, not missing provider usage: the record-level SDK results contain usage under nested `usage.total`, while the summarizer read token fields from the outer usage object. Re-aggregation from the preserved raw records gives:

| Configuration | Input | Output | Reasoning-output | Total |
|---|---:|---:|---:|---:|
| Luna / medium | 53,230 | 761 | 468 | 53,991 |
| Terra / medium | 57,925 | 648 | 353 | 58,573 |
| Terra / high | 56,391 | 733 | 469 | 57,124 |
| Sol / medium | 57,925 | 725 | 395 | 58,650 |
| Astra / medium | 53,512 | 390 | 65 | 53,902 |

Reasoning-output tokens are a subset/detail of reported output usage, not additive to `total_tokens`.

Interpretation:

- this admission set has a substantial ceiling effect: Luna/medium, Terra/medium, Terra/high, and Astra/medium all achieved perfect objective quality;
- on this routine structured task class, Terra/high showed **no measured quality advantage** over Terra/medium and was materially slower;
- Luna/medium matched the production Terra/high baseline on quality while completing faster in aggregate;
- Astra/medium also matched rather than exceeded the ceiling, so this gate does not justify spending Astra on routine work;
- raw token counts are useful execution facts but are not themselves a complete measure of Plus included-allowance consumption because model, reasoning, context, and provider metering all affect allowance usage;
- therefore the first gate supports a strong hypothesis that universal Terra/high overspends cognition on routine bounded work, but it does **not** yet establish the boundary at which Terra/high, Sol, or Astra earn their higher usage.

Provider economic context captured 2026-09-15 (volatile; recheck before relying on exact rates):

- OpenAI's current Plus local-message estimates per five-hour period are approximately Luna 250–2,000, Terra 25–200, Sol 10–100, and Astra 5–45; actual consumption varies by task, context, reasoning, tools, and other factors.
- Current token-based Work/Codex flexible-credit rates are listed as Luna 5 input / 30 output credits per 1M tokens; Terra 50 / 300; Sol 100 / 500; Astra 250 / 1,250. Applying those rates only as a **credit-equivalent comparison** to the raw E-073 benchmark records yields roughly Luna 0.29 credits, Terra/medium 3.09, Terra/high 3.04, Sol 6.16, and Astra 13.87 for the three-turn batch.
- These credit-equivalent values do not claim exact debit behavior of the principal's included Plus allowance. Their significance is relative: a quality tie across these models is economically material, so higher-cost tiers need affirmative quality evidence to justify selection.

Provider references at capture time: OpenAI Help Center, “Managing usage with GPT-6 Astra in Work and Codex”; “Using Credits for Flexible Usage in ChatGPT (Personal plans)”; and the current ChatGPT Work/Codex token rate card.

**Next gate:** a deliberately harder, more Codex-Room-representative threshold benchmark should test the same five configurations on subtle evidence/state reasoning, multi-constraint coordination, and concurrent/runtime code reasoning. If that also ceilings, stop synthetic expansion and move to representative real-work evaluation rather than manufacturing ever harder puzzles.

**Status:** first paid P1 admission gate COMPLETE; no production model-selection policy changed.

### E-074 — P1 threshold benchmark and synthetic-test cost limit
**Date:** 2026-09-15  
**Scope:** [P1 exploratory] second 15-turn synthetic comparison plus principal-observed Plus allowance cost.

The harder threshold benchmark ran the same five configurations across three 12-label task families: state/evidence reasoning, coordination constraints, and concurrent/runtime code review.

Observed aggregate results:

| Configuration | Score | SDK failures | Aggregate duration | Total tokens |
|---|---:|---:|---:|---:|
| Luna / medium | 35/36 | 0 | 27.719 s | 54,698 |
| Terra / medium | 33/36 | 0 | 28.340 s | 58,068 |
| Terra / high | 35/36 | 0 | 29.931 s | 59,577 |
| Sol / medium | 34/36 | 0 | 22.528 s | 59,242 |
| Astra / medium | 34/36 | 0 | 24.548 s | 54,622 |

All five configurations scored 12/12 on both coordination constraints and concurrent/runtime review. All score differences came from the state/evidence task.

Post-run inspection found that the state/evidence answer key was not sufficiently epistemically clean to rank models reliably. In particular, several claims mixed two different questions: whether an underlying fact is false versus whether supplied evidence establishes that fact. Models split between `C` and `U` on those cases while their rationales often expressed the same underlying uncertainty. The resulting 35/36 versus 34/36 versus 33/36 ordering should therefore **not** be interpreted as a reliable capability ranking.

The economically important observation is independent of that scoring ambiguity: the principal reported that the two 15-turn benchmark runs together consumed nearly **20% of the five-hour Plus usage allowance**. Thirty dedicated synthetic turns for this amount of evidence is disproportionate to P1's goal. This is direct evidence that continuing to manufacture synthetic comparisons is itself an expensive failure mode.

P1 consequence:

- stop dedicated paid synthetic benchmark expansion now;
- do not run Astra effort sweeps or additional puzzle matrices;
- preserve the useful conclusion from E-073/E-074 that routine bounded work did not show a quality advantage for universal Terra/high;
- gather further model-economy evidence opportunistically from representative work the principal actually wants completed, avoiding duplicate model calls solely for experimentation;
- prefer deterministic verification and already-required review evidence over model-against-model duplication;
- do not change production model-selection policy solely from these synthetic runs.

**Status:** synthetic P1 benchmark phase COMPLETE / STOPPED FOR COST. Next evidence should come from representative real work, not additional dedicated benchmark turns.

### E-075 — P1 bounded C-selected execution configuration
**Date:** 2026-09-15  
**Scope:** [CORE / P1 experimental capability] Representative-real-work model/effort economy without automatic routing.

PR #60 implemented the smallest adaptive cognition mechanism needed for P1 real-work evidence while preserving the existing triad and C's coordination-only authority.

Implemented behavior:

- C may attach a bounded execution selection to a peer it explicitly invokes in the same MESSAGE;
- allowed P1 selections are `luna-medium`, `terra-medium`, `terra-high`, `sol-medium`, and `astra-medium`;
- each selection resolves deterministically to the exact SDK model + reasoning effort at delivery claim time;
- the selected model/effort is persisted in the existing durable `agent_executions` row before invocation, so recovery and I-009 usage evidence remain tied to the exact execution;
- C is instructed to prefer `luna-medium` for routine bounded delegated work and spend stronger cognition only for an affirmative reason such as complexity, uncertainty, risk, or prior verification trouble;
- A/B cannot directly cause a model change. Their structured selections are not resolved into executable settings; they are instructed to return an escalation request to C when stronger cognition appears warranted;
- C may redelegate the same peer with a stronger allowed configuration after considering that request;
- if C does not specify a peer configuration, the compatibility fallback remains the existing `gpt-5.6-terra` / `high` policy;
- C's own turns remain on the existing Terra/high fallback;
- no automatic task classifier, deterministic model router, new persistent agent, UI control, or separate metrics system was introduced.

Structured-output implementation uses a strict-schema-safe nullable array of required `{target, config}` records. Event metadata stores the plain JSON form plus the resolved exact model/effort map for inspection.

Verification history:

- initial PR-head CI exposed one pre-existing timing assumption in the multi-peer test after additional metadata/validation work; the test was corrected to wait for the intended durable event rather than a fixed sleep;
- later diagnostic runs exposed a prompt-formatting bug in a JSON example embedded in an f-string. The worker error was `Invalid format specifier '"agent_a","config":"luna-medium"' for object of type 'str'`; the example was replaced with non-braced prose and all temporary diagnostic workflow/test changes were removed before final verification;
- final exact PR head `f0736b3f79f5274781a2d7dda3e26d942775e153` passed **329 tests, 2 warnings** in GitHub Actions run `34951904535`;
- PR #60 squash-merged as `ebbacb212b8d6c26b69a8fd2acb0959dcff26b42`;
- canonical-`main` run `34952133541` on that exact merge commit passed **329 tests, 2 warnings**;
- automatic merged-branch cleanup left only `main`.

Evidence boundary:

- the capability is IMPLEMENTED / VERIFIED on canonical `main`;
- it is still an **experimental P1 allocation mechanism**, not a settled recommendation for automatic/dynamic routing;
- no local live Room using C-selected peer cognition has yet been recorded under this evidence item;
- P1's next evidence should come from ordinary work the principal wants done, without duplicate benchmark turns solely for comparison.

**Status:** bounded adaptive execution selection IMPLEMENTED / VERIFIED; representative live-use evaluation remains IN PROGRESS.



### E-076 — Astra hard execution prohibition
**Date:** 2026-09-15  
**Scope:** [CORE / P1 policy enforcement] D-028 hard prohibition on Astra Room cognition.

PR #61 removed `astra-medium` from the bounded C-selectable execution configuration type, mapping, and Structured Output schema. The runtime adapter also now fails closed before starting a Room thread or turn when the currently identified Astra model `gpt-6-astra` is supplied. Regression coverage verifies both schema-level rejection of `astra-medium` and adapter-level rejection of direct Astra execution.

Verification:

- exact PR head `281f70c52ace0c9812d2f7a85b75016c8b0cfa02` passed GitHub Actions run `34953937701`;
- PR #61 squash-merged as `537e87c1fc2302aab9874bd7f5394e5d17550baf`;
- the merge commit carries the same Git tree as the verified PR head (`d4f71e006a015804bdd325959093f92d96209c89`);
- canonical-main GitHub Actions run `34954156484` passed on that exact merge commit.

The governing decision is D-028: Astra is prohibited for Codex Room execution and prompts or later allocation/routing logic may not override the rule. Luna, Terra, and Sol remain admitted to the bounded P1 real-work trial.

**Status:** D-028 IMPLEMENTED / VERIFIED on canonical `main`.

### E-077 — Live same-thread adaptive peer execution and Room evidence-boundary observation
**Date:** 2026-09-15  
**Scope:** [ROOM / P1 live evidence] representative I-010 work using the bounded C-selected execution mechanism.

Fresh Room `room_56bbfe947f5d4d169de29a563c450253` ran the I-010 maintenance-design task as a real-work P1 trial. C selected Agent A for a bounded initial inventory on `luna-medium`, then deliberately redelegated the same persistent peer for a harder recovery-safety design pass on `terra-high`. B was not invoked because the absent implementation surface meant a second peer could not add independent implementation evidence.

Room-export evidence records:

- first Agent A execution request: `batch_1f3f5b37a32d4b3d97355d49dd76d1ca`, resolved as `gpt-5.6-luna` / `medium`;
- second Agent A execution request: `batch_b8fcf19c6fde4051af5c56695446af44`, resolved as `gpt-5.6-terra` / `high`;
- the second assignment was substantively harder: recovery invariants, backup consistency, destructive restore safeguards, crash/interruption behavior, and verification design rather than duplicate comparison work;
- A did not request escalation in the first pass; C proactively spent stronger cognition for the harder follow-up;
- Astra was not available or selected.

The principal then queried the durable local `agent_executions` rows for those exact batch IDs. The database returned:

- `batch_1f3f5b37a32d4b3d97355d49dd76d1ca` → Agent A, `gpt-5.6-luna`, `medium`, SDK thread `01a0a478-09b1-7821-8a55-8db5e596abe9`, state `settled`;
- `batch_b8fcf19c6fde4051af5c56695446af44` → the same Agent A, `gpt-5.6-terra`, `high`, the same SDK thread `01a0a478-09b1-7821-8a55-8db5e596abe9`, state `settled`.

This directly verifies that one persistent Room peer can continue on the same SDK thread across different C-selected model/reasoning configurations. The trial therefore closes the live-mechanics question for same-thread adaptive peer execution. It does **not** establish precise automatic-routing thresholds or authorize an automatic router.

The same Room also exposed an architectural evidence boundary relevant to I-012: Agent A's current shared workspace contained no CORE implementation, database, migrations, configuration, tests, or Project evidence, so it correctly refused to make implementation-specific I-010 claims and produced only a conditional SQLite design. This observation motivated D-029/I-012 bounded read access to authorized CORE source and other Room shared workspaces.

**Status:** same-thread C-selected peer switching LIVE VERIFIED; automatic routing remains unauthorized; cross-boundary evidence access gap OBSERVED and routed to I-012.

### E-078 — Bounded CORE and cross-Room read inspection
**Date:** 2026-09-15  
**Scope:** [CORE] D-029 / I-012 deterministic read-boundary implementation.

PR #62 adds registered CORE capability `inspect_source` version `1` for targeted read-only inspection beyond the current Room workspace.

Implemented surface:

- source discovery identifies the current canonical Room, the maintained CORE read surface, and canonical Personal Room shared workspaces;
- `source="core"` is confined to an explicit allowlist of maintained repository/source entries such as `codex_room/`, `tests/`, `docs/`, launcher/configuration files, and repository metadata files needed for implementation reasoning;
- CORE runtime data and arbitrary host paths are outside that allowlist, including `data/`, `.env`, `.git/`, virtual environments, credentials/secrets, and provider/account state;
- `source="room"` resolves only `data/rooms/<room_id>/shared`; private participant state, Room-private files outside `shared`, and host database internals are not exposed;
- operations are bounded `sources`, `find`, literal `search`, and UTF-8 text `read`;
- absolute/traversal paths, backslash path tricks, NUL paths, symlink/reparse traversal, and wholesale CORE-root scans are rejected;
- reads are size/line bounded; find/search have explicit file, match, byte, and scan ceilings;
- read content and search excerpts remain transient. Durable Room telemetry persists only the capability identity plus declared bounded `evidence`, reusing the generic durable-result filtering verified in the existing capability substrate;
- the capability grants no workspace write, network, or external-process authority and adds no cross-boundary write mechanism;
- shared protected agent instructions tell A/B/C to use authorized read-only inspection when relevant while preserving the CORE/Room mutation boundary.

Verification history:

- an initial PR run exposed only two stale registry-list test expectations after the fifth CORE capability was registered; all new capability tests themselves passed in that run;
- those exact expectations were updated to include `inspect_source`;
- repaired code-bearing PR head `b70d67f0d743b8a1228b29fd942f2aae666302cc` passed **341 tests, 2 warnings** in GitHub Actions run `34956587939`;
- regression coverage includes CORE-source allowlisting, `data/` and `.env` rejection, cross-Room shared-only confinement, traversal rejection, symlink/reparse escape rejection, bounded reads, source discovery, and find/search behavior.

Canonical verification:

- final exact PR head `a64acf828cd32202038529d180311934ac1c26f5` passed **341 tests, 2 warnings** in GitHub Actions run `34956844117`;
- PR #62 squash-merged as `e60ad2b1d4a3339c30ef1837f3bca53366929acd`;
- the merge commit carries the exact same Git tree as the verified PR head: `c24f31635065252fd4e9d2bd0d2460549f5243e0`;
- canonical-`main` GitHub Actions run `34957034618` passed **341 tests, 2 warnings** on that exact merge commit.

Evidence boundary: deterministic implementation and hosted verification are complete on canonical `main`. A fresh local live Room smoke remains necessary to prove that the deployed Windows/Codex sandbox can exercise the new cross-boundary read path end to end.

**Status:** IMPLEMENTED / VERIFIED on canonical `main`; fresh local live-Room verification pending.

### E-079 — Live bounded CORE and cross-Room read verification
**Date:** 2026-09-15  
**Scope:** [ROOM / CORE live verification] D-029 / I-012 deployed read-boundary smoke.

Fresh Room `room_38590e397cf94542b92fe76278924a65` ran the dedicated I-012 live smoke after the canonical implementation was pulled and the runtime restarted.

Observed Room-export evidence:

- only Agent C ran; A and B never consumed the round context and were not invoked;
- registry discovery exposed `inspect_source` version `1` with implementation SHA-256 `49338a3be7e57dad643bf2924fb9a017c4bfaa421ad8e0a235a87a2a55799f9b`;
- manifest inspection reported `core_source_read: true`, `cross_room_read: true`, `workspace_write: false`, no network/external-process permission, `side_effects: none`, and verification evidence `E-078`;
- source discovery succeeded;
- a bounded CORE read succeeded against `core:codex_room/db.py`, returning lines 1–12 / 271 bytes;
- a literal CORE search succeeded under `core:codex_room` for `CREATE TABLE IF NOT EXISTS agent_executions`, locating one match at `codex_room/db.py:238`;
- a bounded cross-Room find succeeded against `room:room_066696deaefd414bab84c00fa3f536dc`, path `.`, returning 10 shared-workspace file matches;
- C reported no protected-surface access and no file creation, modification, or deletion;
- C FINISHed exactly `I-012-LIVE-OK` and the one-turn round closed normally.

The live turn also exposed invocation ergonomics/telemetry behavior worth preserving without overclaiming. Two malformed inline-JSON attempts were correctly surfaced and durably classified as failed `deterministic_capability` invocations. After C changed invocation form to work around the Windows command-line JSON quoting problem, the successful source-discovery/read/search/find operations appeared in the export only as generic `command_execution` activity rather than promoted `deterministic_capability` evidence. The export does not preserve the raw generic command text, so the exact wrapper form cannot be established from this artifact alone. C's final response reports the exact successful results, and the capability's functional live path is therefore demonstrated, but this export does not independently prove durable structured promotion of those successful wrapper-form invocations.

Interpretation:

- D-029's functional objective is live verified: a running Personal Room can inspect authorized CORE source and another Room's shared workspace without peer invocation or cross-boundary write authority;
- the no-write smoke intentionally prevented use of the already-supported `--input-file` fallback for fragile command-line JSON, making the test stricter than ordinary workspace operation;
- the generic activity classification did not expose raw read/search payloads, so no data-leak regression is shown;
- do not expand I-012 solely to redesign capability invocation or telemetry from this one constrained smoke. Monitor ordinary Room use; reopen only if wrapper-form invocation or missing structured telemetry recurs as a practical product problem.

**Status:** I-012 functional read boundary LIVE VERIFIED; bounded telemetry/quoting observation retained as MONITOR, not a completion blocker.

### E-080 — I-010 grounded maintenance investigation exposed SDK-internal subagent bypass
**Date:** 2026-09-15  
**Scope:** [ROOM / P1 / CORE] I-010 representative work and hidden-cognition-path observation.

Fresh Room `room_6a9dd827148f40739ce3f3a4c7601bac` ran the repository-grounded I-010 investigation after I-012 live verification.

Useful I-010 evidence:

- C successfully used registered `inspect_source` to inspect current CORE rather than relying on the earlier empty-workspace inference;
- source evidence confirmed the default Personal root at `data/`, SQLite at `data/codex-room.db`, Room shared workspaces under `data/rooms/<room-id>/shared`, durable institutional/custom-capability registry material under the data root, WAL/foreign-key/busy-timeout and restart/recovery safeguards, and the absence of a current backup/integrity/restore maintenance command or explicit SQLite `user_version` contract;
- C produced a bounded candidate I-010 direction: one local operator-only maintenance CLI covering integrity check, backup, backup verification, and guarded restore while explicitly excluding cloud sync, scheduling, retention, dashboards, and an agent-callable backup service.

The execution-allocation record in C's final response was not valid Room evidence. It claimed that persistent Agent A ran at `luna-medium` and persistent Agent B at `terra-medium`, but the complete export shows:

- Room `turn_count = 1`;
- every model/tool activity event belongs to Agent C;
- A and B have no conversational/source events and did not consume the Round context;
- no C MESSAGE with `invoke_targets` / `execution_configs` delegated Room work to A or B;
- C's single turn contains four `sub_agent_activity` tool events instead.

Therefore the additional cognition came from Codex SDK-internal subagents inside C's turn, not the persistent Room peers. The Room's claimed Luna/Terra peer allocation must not be counted as P1 evidence.

Pinned Codex 0.154 source confirms the mechanism:

- `[agents].enabled` defaults to true;
- enabled `features.multi_agent_v2` takes precedence over that switch;
- the multi-agent spawn surface states that spawned agents inherit the parent model by default.

Codex Room's adapter previously supplied only model and reasoning-effort app-server overrides, so the internal multi-agent surface remained available. This creates an untracked/poorly attributed cognition path outside `invoke_targets`, Room peer execution rows, and P1's C-selected peer configuration mechanism.

Bounded remediation PR #63 adds `agents.enabled=false` plus `features.multi_agent_v2.enabled=false` to the Codex Room app-server config overrides and updates the existing adapter-initialization regression assertion.

Verification:

- exact code-bearing head `571bc2effe75b7b63df3f4094ed1b56099a3264d` passed **341 tests, 2 warnings** in GitHub Actions run `34981186463`;
- final exact PR head `830bbfec06d3f90463a4e07c214e780bb7ca3c23` passed **341 tests, 2 warnings** in run `34981545707`;
- PR #63 squash-merged as `8ed3df777ed24a8192b48e43f652f4736921fe2c`;
- the merge commit and final PR head carry the exact same Git tree `b7436a3a3e12616b81f84e59c5650f599776ebf9`;
- canonical-`main` run `34981774647` passed **341 tests, 2 warnings** on that exact merge commit.

Interpretation:

- the I-010 investigation produced useful repository-grounded design evidence, but its peer-allocation narrative is false and does not satisfy the P1 naturalistic-allocation gate;
- internal SDK subagents are not needed for Personal production because deliberate production cognition already has the persistent A/B/C Room path;
- I-013 closes this deterministic bypass on canonical `main`; no dedicated paid model smoke is warranted, and the next useful Room should simply be inspected for absence of `sub_agent_activity`;
- the I-010 design remains a candidate specification for Project-level review; recommendations such as installation identity, explicit SQLite `user_version`, and a particular restore-lock protocol are proposals, not existing implementation facts.

**Status:** I-010 repository investigation useful; claimed A/B allocation INVALID; I-013 IMPLEMENTED / VERIFIED on canonical `main`; next useful Room should monitor for recurrence.

### E-081 — I-010 tool-loop amplification and deterministic retrieval economy
**Date:** 2026-09-15  
**Scope:** [ROOM / CORE / P1] Operating-economics evidence and I-014 bounded remediation.

The principal observed roughly **19% of the five-hour Codex allowance** consumed during the recent hour that included I-012 live verification and the repository-grounded I-010 investigation. That allowance reading is an aggregate provider meter and does not by itself attribute exact percentages to individual turns.

The I-010 Room export and C's same-thread retrospective establish a concrete amplification mechanism:

- the initial I-010 C turn reported **2,549,213 total tokens**: 2,534,360 input, 2,391,296 cached input, 14,853 output, and 6,165 reasoning-output tokens;
- no context-compaction activity occurred during that turn;
- C deliberately spawned two temporary SDK workers with full-history forks, explicitly selecting Luna/medium for the bounded persistence audit and Terra/medium for the lifecycle/restore audit; both returned materially useful results, so this evidence does not establish that temporary helpers themselves were wasteful;
- C then performed 27 direct `inspect_source` invocations: 3 source-discovery attempts, 2 find attempts, 11 search attempts, and 11 reads;
- 22 inspection invocations succeeded and 5 failed on avoidable request/contract mistakes;
- because Windows command-line JSON was fragile, C also performed **27 `apply_patch` operations** against four temporary JSON request files solely to feed those 27 inspections; the files were not I-010 work product;
- C's retrospective therefore identifies 58 direct actions across two worker spawns, registry list/inspect, 27 request-file edits, and 27 source invocations, before counting provider-internal continuation boundaries not separately exposed;
- after receiving useful delegated research, C independently inspected substantial overlapping persistence/lifecycle evidence rather than limiting itself to consequential spot checks.

Interpretation: the demonstrated expensive problem is **tool-loop/context amplification**. A mechanical evidence lookup could require a request-file write plus a capability invocation, and repeated small reads/searches repeatedly returned control to the model while prior tool context accumulated. This is a more concrete P1/P2 operating-economics problem than further synthetic model-ranking work.

I-014 implements the bounded remediation:

- `inspect_source` advances to version 2 and adds `search_many` (up to 16 known literal queries in one bounded source scan) plus `read_many` (up to 16 bounded ranges with a shared 128-KiB output ceiling);
- `codex-room-cap source ...` provides a JSON-free scalar CLI for sources/find/search/search-many/read/read-many while translating into the same registered `inspect_source` handler and preserving its path confinement, symlink/reparse rejection, source allowlists, output bounds, no-write permissions, and transient raw-content contract;
- adapter telemetry recognizes the direct source CLI as `deterministic_capability`, including structured failure attribution, without persisting transient search excerpts/read content;
- protected agent instructions tell participants to prefer bounded batching/direct source retrieval when related lookups are already known, while avoiding speculative batches whose need depends on prior results;
- C's structural instructions now require evidence-backed delegated research to be integrated normally, with independent re-inspection limited to consequential uncertainty, contradiction, risk, or verification needs rather than broad reassurance-driven repetition;
- each settled execution now emits one mechanical/status `execution_economics` event derived from already-available usage/activity data: tool/activity counts, failed-tool and capability-failure counts, file changes, context compactions, subagent-activity count, peer-invocation count, available token fields, failed-tool fraction, and tokens-per-tool-call. No new metrics database or quota/enforcement mechanism is introduced.

Verification history:

- the first PR #64 run exposed one stale test that still expected `inspect_source` version 1; all other tests passed (**348 passed, 1 failed, 2 warnings**);
- after updating that exact assertion, head `7a7d0b5f724e280db9dc3f2a595dd33501ce3722` passed **350 tests, 2 warnings** in run `34986727410`;
- the later exact implementation head `0f075bd5ea5fa408a1c0e94606d74e85513e44c4`, including explicit status classification for execution-economics telemetry, passed **350 tests, 2 warnings** in run `34986799530`.

Final canonical verification:

- final exact PR #64 head `6bea22469f0195831dfb09037f551380fde76a07` passed **350 tests, 2 warnings** in GitHub Actions run `34987373764`;
- PR #64 squash-merged as `02c026ab29dd4bd573b8945de0e6adca9c4b27b4`;
- the final PR head and merge commit carry the exact same Git tree `9b7e163a7d685add368d7208f5010d8294f3b9e3`;
- canonical-`main` run `34987638410` passed **350 tests, 2 warnings** on that exact merge commit.

Evidence boundary: deterministic implementation and canonical verification are complete. No dedicated paid Room smoke is warranted; the next useful Room can provide naturalistic evidence on whether direct/batched retrieval reduces file-change/tool-loop amplification.

**Status:** I-014 IMPLEMENTED / VERIFIED on canonical `main`; naturalistic ordinary-use monitoring remains.

### E-082 — Read-only Codex rollout usage extraction for Desktop/Room comparison
**Date:** 2026-09-15  
**Scope:** [P1 / deterministic local tooling] Comparable Codex task-level usage evidence without model introspection.

Current Codex 0.154 source records local session rollouts beneath `CODEX_HOME/sessions/YYYY/MM/DD/rollout-...jsonl`. `token_count` events carry both cumulative `total_token_usage` and `last_token_usage`, with input, cached-input, cache-write-input, output, reasoning-output, and total-token fields. This is materially closer to Codex Room's persisted SDK usage than the account/credit meter and permits deterministic local extraction without asking Codex to analyze itself.

PR #65 adds a stdlib-only, read-only extractor:

- `codex_room/codex_usage.py` reads rollout JSONL only; it does not invoke Codex, write Codex state, or read the Codex SQLite state database;
- default selection uses the latest active **top-level** rollout rather than silently selecting a newer child/subagent rollout; exact rollout paths and thread IDs can also be selected;
- the report includes thread/session metadata, final cumulative usage, final last-response usage, token-count update progression, and event-type counts relevant to context compaction/subagent activity;
- task-level usage is reconstructed for each user turn as the element-wise delta in cumulative token counters between that user message and the next user message/end of rollout;
- prompt/response content is not retained in the generated report;
- `codex-usage.cmd` provides the normal Windows wrapper through the repository virtual environment;
- machine-readable `--json` and human `--timeline` output are supported.

The implementation deliberately treats cumulative usage as authoritative for a completed task/thread comparison; `last_token_usage` is reported separately and must not be substituted for total task work. A fresh Desktop thread remains the cleanest comparison case, but per-user-turn deltas permit bounded analysis of reused threads when cumulative counters remain monotonic.

Exact implementation head `5a4473b6718ac2cec6e0396d8a7ad02ef22f6b40` passed **356 tests, 3 warnings** in GitHub Actions run `34991882483`. The extra warning did not fail the suite and belongs to the already-known test-platform warning/nondeterminism surface rather than an extractor assertion failure.

Final canonical verification:

- final exact PR #65 head `5ce7c769561ebf303b52a7ef59c660a96e992375` passed **356 tests, 2 warnings** in GitHub Actions run `34992234417`;
- PR #65 squash-merged as `8d1851ca74c2e69dd5085e8ac47134011653ba70`;
- final PR head and merge commit carry the exact same Git tree `7b5a8f3af71588bb1f6545ad0deed6409a7bc8b4`;
- canonical-`main` run `34992448459` passed **356 tests, 2 warnings** on that exact merge commit.

Evidence boundary: deterministic extraction behavior is verified on canonical `main`. A real local Desktop rollout should be sampled only when useful comparison work is ready; no paid/model smoke is necessary merely to prove the parser.

**Status:** IMPLEMENTED / VERIFIED on canonical `main`; useful-work comparison evidence pending.

### E-083 — Controlled Desktop-vs-Room Stage 1 and pre-bind crash-window ground truth
**Date:** 2026-09-15  
**Scope:** [P1 / operating economics / correctness] First matched C-only Room versus standalone Codex Desktop repository investigation, followed by deterministic ground-truth verification.

The principal ran the same shutdown/persistence investigation back-to-back against the same Codex Room source state with fresh contexts and intended Terra/high cognition on both sides. Stage 1 deliberately disabled Room peer invocation so the comparison was one standalone Desktop participant versus C alone. The Room export and native rollouts establish that no persistent A/B peer or SDK subagent participated.

Observed execution economics:

| Metric | Desktop Stage 1 | Room C-only Stage 1 |
|---|---:|---:|
| Tool calls | 11 | 32 |
| Provider-response usage records / nonzero usage increments | 12 | 33 |
| Failed tool calls | not surfaced as failures in the extractor output | 6 |
| Total reported tokens | 809,750 | 1,558,227 |
| Input tokens | 804,410 | 1,549,446 |
| Cached input tokens | 708,608 | 1,445,888 |
| Uncached input tokens | 95,802 | 103,558 |
| Output tokens | 5,340 | 8,781 |
| Reasoning-output tokens | 3,034 | 3,297 |
| Context compactions | 0 | 0 |
| Subagent activity | 0 | 0 |
| Room peer invocations | n/a | 0 |

The Room therefore used about 2.91x as many tool calls and 1.92x as many reported total tokens, while uncached input was only about 8.1% higher and reasoning-output tokens only about 8.7% higher. The excess raw-token volume was dominated by repeated cached-context replay across additional model/tool continuations rather than by materially more new input or explicit reasoning. This strengthens E-081's conclusion that continuation count and tool-loop shape are first-order operating-economics variables even after I-014 batching is available.

The two participants also disagreed on correctness. Desktop concluded that a pre-bind claim is deliberately quarantined on restart and not replayed. C instead inferred a duplicate-execution failure because `recover_interrupted_work()` changes `claimed` to `quarantined` while `claim_next_batch()` does not include `quarantined` in its existing-execution lookup.

Direct source inspection identified an outer control-flow guard C had missed: startup calls `ensure_workers()`, whose durable-execution view *does* include `quarantined`; it marks that worker slot quarantined and does not create a worker. Thus the startup path does not reach `claim_next_batch()` for that quarantined execution.

PR #67 converted that dispute into a deterministic regression test. The test forces a delivery to remain durably `claimed` before SDK turn binding, simulates process loss without Room settlement, restarts the runtime, and verifies all of the following:

- the same batch becomes `quarantined`;
- its processing delivery remains durably quarantined rather than replayed;
- no replacement Agent A worker task is created;
- the replacement adapter receives no Agent A call;
- exactly one execution row remains for the batch, so no duplicate insert occurs;
- no `worker_error` event is emitted.

Exact PR #67 head `297bada6fd89ba095e0fe64076e9cf9fde66e3d8` passed **358 tests, 2 warnings** in GitHub Actions run `34997699874`. PR #67 squash-merged as `66ac4355551609bcca34b78166687bd252c8539e`; canonical-`main` run `34997919791` then passed **358 tests, 2 warnings** on that exact merge commit.

Ground-truth conclusion: Desktop was correct on the disputed pre-bind restart mechanism; C's proposed duplicate-insert corruption path was a false positive caused by local reasoning that did not prove reachability through the complete startup control flow. No production persistence repair was justified by that claim.

Important limitations:

- this is one matched investigation, not evidence that Desktop is globally better than Codex Room;
- the task used the real repository rather than a frozen synthetic fixture;
- Desktop reported CLI `0.154.0-alpha.6.2` while Room used SDK/runtime `0.154.0`, so exact client-build equivalence was not achieved;
- intended same-model/same-effort selection was operator-controlled; the rollout extractor does not independently expose the selected model/effort for the Desktop run;
- Desktop failed-tool count is not reconstructed by the current extractor, so only the Room's six explicit failures are directly measured.

**Status:** P1 evidence established. Stage 1 favors Desktop on both continuation economy and this specific correctness question; broader system-level conclusions remain exploratory.

### E-084 — Blind Stage 2 Desktop-vs-Room fixture exposed scope and coordination failure
**Date:** 2026-09-15  
**Scope:** [P1 / operating economics / coordination correctness] Fresh blind standalone fixture comparison after Stage 1.

A fresh standalone 28-file Python fixture (`relay_app`) was created outside the Codex Room repository specifically to avoid Stage 1 answer leakage. The bug report asked whether graceful shutdown could acknowledge an update before durable persistence and required a reachable causal mechanism, source evidence, rejected false leads, and the smallest safe correction.

The Desktop run used the extracted fixture as its working directory and correctly identified the intended defect: `UpdateAPI.update()` acknowledges after scheduling asynchronous delivery; `RelayApplication.shutdown()` closes the journal before stopping/draining the subscription pump; a delayed accepted delivery can therefore wake after journal closure, fail with `RuntimeError("journal is closed")`, and never reach SQLite. Desktop correctly rejected WAL and already-enqueued journal items as false leads and recommended the minimal shutdown-order repair: stop/drain subscriptions before closing the journal.

Desktop blind-run economics:

| Metric | Desktop Stage 2A |
|---|---:|
| Tool calls | 8 |
| Provider-response usage records | 9 |
| Total reported tokens | 279,098 |
| Input tokens | 275,125 |
| Cached input tokens | 251,648 |
| Uncached input tokens | 23,477 |
| Output tokens | 3,973 |
| Reasoning-output tokens | 1,867 |
| Context compactions | 0 |
| Subagent activity | 0 |

The Room run used fresh Room `room_26494a49df3749fd99f84df5c45f5727`. The fixture bytes were copied into that Room's shared workspace before the LAB-2B prompt. A neutral setup topic caused one initial no-op C turn before the real lab prompt; that setup turn is excluded from the task-cost comparison below.

The LAB-2B Room run failed procedurally rather than merely reaching the wrong technical conclusion:

- C made 38 tool calls, including 29 deterministic-capability invocations and 7 command-execution activities; 6 tool calls failed;
- persistent A/B peer invocations remained zero and SDK subagent activity remained zero;
- C spent substantial retrieval effort against Codex Room CORE (`codex_room/` and CORE `tests/`) despite the prompt explicitly limiting work to the supplied Room shared workspace;
- C did not return the requested conclusion, mechanism, source evidence, false leads, or correction;
- C's only substantive message said it was "awaiting the two complementary peer audits before concluding", but the exact message metadata recorded `invoke_targets: []`, `peer_invocations: 0`, no requested runnable recipients, and no runnable recipients;
- with no runnable work remaining, the Room closed mechanically as `quiescent_without_work`.

Native rollout extraction permits exact separation of the neutral setup turn. The full C thread reported 1,825,861 total tokens across 40 provider-response usage records. The first setup turn accounted for 20,547 total tokens (20,489 input, 58 output, 28 reasoning; no cached input). Therefore the actual LAB-2B attempt consumed:

| Metric | Room Stage 2B task only | Desktop Stage 2A | Room / Desktop |
|---|---:|---:|---:|
| Tool calls | 38 | 8 | 4.75x |
| Provider responses | 39 | 9 | 4.33x |
| Total reported tokens | 1,805,314 | 279,098 | 6.47x |
| Input tokens | 1,797,842 | 275,125 | 6.53x |
| Cached input tokens | 1,719,552 | 251,648 | 6.83x |
| Uncached input tokens | 78,290 | 23,477 | 3.33x |
| Output tokens | 7,472 | 3,973 | 1.88x |
| Reasoning-output tokens | 3,125 | 1,867 | 1.67x |

Interpretation:

- Stage 2 independently reinforces E-081/E-083: continuation count and repeated cached-context replay remain a first-order Room cost driver even on a small bounded fixture;
- unlike Stage 1, the Room also consumed materially more *uncached* input, consistent with investigating the wrong source boundary rather than merely replaying the same relevant context;
- normal Room coordination did not get a chance to demonstrate value because C never actually invoked A or B despite believing or stating that it was awaiting two peer audits;
- the closure mechanism behaved consistently with the structured routing state: because C emitted no runnable peer targets, the Room had no work to execute. The contradiction is between C's stated coordination plan and its structured action, not evidence that the router silently dropped requested peer work;
- the Room's explicit scope failure and coordination-action inconsistency are demonstrated product-quality issues worthy of deterministic source/test diagnosis before paying for another comparative Room run.

Experimental limitations:

- the Room incurred one excluded neutral setup turn because the Room creation flow required a topic before the later observer LAB prompt;
- Desktop used CLI `0.154.0-alpha.6.2`; Room used SDK/runtime `0.154.0`; exact client-build equivalence was not achieved;
- intended Terra/high selection remained operator-controlled and is not independently emitted by the Desktop rollout extractor;
- this is one blind fixture and does not establish universal Desktop superiority.

**Status:** P1 Stage 2 evidence established. No rerun is justified before deterministic diagnosis of the demonstrated scope-selection and stated-vs-structured peer-invocation failures.

### E-085 — Provider-continuation trace and bounded continuation-economy repair
**Date:** 2026-09-15  
**Scope:** [P1 / CORE / operating economics] Source-level diagnosis of E-084's context-replay amplification.

The E-084 LAB-2B C thread provides a clean continuation trace once its neutral setup turn is excluded:

- one actual Room/C SDK turn contained **38 tool calls** and **39 provider-response usage records**;
- the 38 recorded activities were 29 deterministic-capability calls, 2 capability-registry calls, and 7 other command executions; 6 failed;
- the deterministic source activity included **15 single reads**, only **1 read_many**, 4 search_many calls, 2 single searches, 2 finds, and source discovery;
- the task accumulated **1,719,552 cached input tokens** out of 1,797,842 total input tokens.

Source inspection establishes the execution boundary precisely. `RoomRuntime._process_delivery()` submits one `adapter.run_agent(...)` call and waits for that SDK turn to finish. `CodexAgentAdapter._consume_handle()` receives the completed turn result and only then derives safe activity summaries from the returned SDK items. Back in `_process_delivery()`, execution-economics and `tool_activity` Room events are created **after** `record_execution_result()` and after the SDK turn has completed. Therefore those Room ledger/status events did not wake C between the 38 LAB tool calls and did not create the 39 provider responses.

The expensive loop was inside the single Codex turn: model response → tool execution/result → another provider continuation with the active thread context. The observed arithmetic is consistent with 38 tool-producing continuations plus the final structured response. Codex Room cannot merge those provider continuations after the fact; its practical levers are to reduce tool-call count, batch known deterministic work, avoid failures/redundant retrieval, and keep active context smaller.

The existing Room compaction mechanism is not a repair for this specific pathology. `_maybe_compact_context()` runs only after a Room agent turn has settled, so it cannot intervene between tool calls inside one SDK turn. Lowering the Room compaction threshold would therefore not have changed the 38-call LAB-2B loop.

A concrete Room-owned contributor was also identified. Before PR #70, every delivery prompt instructed agents to check the capability registry before ordinary ad hoc mechanical work, inspect candidates, run registry/capability actions as separate commands, and compose independent mechanical subproblems through separate capability invocations. That policy preserved auditability but imposed a continuation tax and conflicted with the demonstrated operating-economics objective.

PR #70 makes the bounded repair without changing D-022's capability architecture:

- ordinary one-off workspace reads/searches/inspection/simple commands may use native workspace tools directly;
- agents are explicitly told to minimize model/tool continuations, batch already-known related reads/searches, avoid speculative batching, and stop once evidence is sufficient;
- registry `list` is needed only when a required capability identity is unknown, and `inspect` only when the current contract is needed;
- direct source `search-many` / `read-many` remains preferred for known related source lookups;
- explicit workspace-only instructions now explicitly forbid CORE/cross-Room source inspection;
- redundant registry ceremony and one-lookup-per-continuation behavior are discouraged;
- the repeated deterministic-capability guidance block was reduced from 2,793 to 1,869 characters (**33.1% smaller**).

Verification:

- exact PR #70 head `328bf127cc898babea45c410462ff8d83a43db3c` passed **358 tests, 2 warnings** in GitHub Actions run `35005923649`;
- PR #70 squash-merged as `037aa23bdf2e53082d5f089415319de7daa2b356`;
- canonical-main push run `35006163737` passed **358 tests, 2 warnings** in 67.55 seconds.

Evidence boundary: the continuation mechanism and CORE instruction repair are deterministically established. **No token-savings claim is made yet.** The next evidence should come from ordinary useful Room work, not another paid synthetic comparison.

**Status:** continuation mechanism DIAGNOSED; bounded CORE repair IMPLEMENTED / VERIFIED; dedicated paid P1 benchmarking CLOSED, ordinary-use monitoring remains.

### E-086 — LAB-2C post-fix continuation-economy regression
**Date:** 2026-09-15  
**Scope:** [P1 / CORE / operating economics] Controlled post-PR-#70 regression against the same blind shutdown fixture used by E-084.

A fresh Room `room_50eadb78672740cba17bb5e486b9a6b9` was created after PR #70 was deployed. The LAB-2C task reused the same standalone `relay_app` fixture and explicitly constrained C to the Room shared workspace, prohibited A/B invocation, prohibited modification, and asked C to minimize unnecessary tool/model continuations while batching known related lookups.

Observed result:

- C completed the task correctly in one Room turn;
- C identified the same intended shutdown-order defect as the clean Desktop Stage 2A run and recommended the same minimal correction: stop/drain subscriptions before closing the journal;
- A/B peer invocations remained zero;
- SDK subagent activity remained zero;
- no context compaction occurred;
- Room execution economics reported **3 tool calls**, **0 failures**, and **92,765 total tokens**;
- all 3 recorded activities were ordinary command executions; there were no deterministic-capability or capability-registry invocations;
- the C rollout thread was `01a0a650-e951-7df1-9e51-4026fea95482`, top-level, SDK originator, CLI 0.154.0, cwd set to the Room shared workspace.

Native rollout extraction reported exactly **4 provider-response usage records** and **3 tool calls**, with no zero-delta updates:

| Metric | Desktop Stage 2A | Pre-fix Room LAB-2B | Post-fix Room LAB-2C |
|---|---:|---:|---:|
| Tool calls | 8 | 38 | **3** |
| Provider responses | 9 | 39 | **4** |
| Total reported tokens | 279,098 | 1,805,314 | **92,765** |
| Input tokens | 275,125 | 1,797,842 | **90,578** |
| Cached input tokens | 251,648 | 1,719,552 | **79,872** |
| Uncached input tokens | 23,477 | 78,290 | **10,706** |
| Output tokens | 3,973 | 7,472 | **2,187** |
| Reasoning-output tokens | 1,867 | 3,125 | **1,045** |
| Correct completed answer | yes | no | **yes** |

Relative to the pre-fix Room run, LAB-2C reduced:

- tool calls by **92.1%**;
- provider responses by **89.7%**;
- total reported tokens by **94.9%**;
- cached input by **95.4%**;
- uncached input by **86.3%**.

Relative to the frozen Desktop Stage 2A baseline, LAB-2C used:

- 62.5% fewer tool calls;
- 55.6% fewer provider responses;
- 66.8% fewer total reported tokens;
- 54.4% fewer uncached input tokens.

The provider-response timeline was compact and monotonic: 20,813 → 42,133 → 65,740 → 92,765 cumulative total tokens. The final provider request was 27,025 tokens.

Interpretation: PR #70's continuation-economy change is not merely syntactically present; on this controlled regression it materially changed tool-loop behavior and eliminated the previously demonstrated registry/retrieval amplification. The post-fix Room also completed correctly and economically enough to outperform the frozen Desktop baseline on this bounded task.

Limitations:

- this is one controlled fixture and must not be generalized into universal Room superiority;
- the Desktop baseline used CLI 0.154.0-alpha.6.2 while the Room used 0.154.0;
- the LAB-2C prompt explicitly emphasized continuation minimization and workspace-only scope, so part of the improvement reflects the repaired policy plus an explicit regression instruction rather than a measurement of unconstrained ordinary use;
- the compact Room export records command-execution categories, not raw command bodies. The rollout cwd was the Room shared workspace and the final answer cited only fixture-local paths; there is no observed evidence of CORE or cross-Room inspection, but the current telemetry does not independently reconstruct every shell read path.

**Status:** PR #70 continuation-economy repair LIVE VERIFIED on a controlled regression. Dedicated P1 benchmarking remains closed; ordinary-use monitoring is now sufficient.

### E-087 — I-010 persistent-data operational maintenance implemented and verified
**Date:** 2026-09-15  
**Scope:** [CORE / operations] Offline local integrity, backup, verification, and guarded restore for Codex Room persistent data.

E-080 established the maintenance gap and bounded solution shape: the default persistent root is `data/`, with SQLite at `data/codex-room.db`, Room shared workspaces under `data/rooms/`, and institutional/custom-capability material under the same root. Raw SQLite copying is not an adequate WAL-era backup strategy, and no bounded operator check/backup/verify/restore path previously existed.

PR #73 implements that bounded local operator path without adding a service, scheduler, cloud sync, retention policy, dashboard, installation identity, SQLite `user_version` contract, or agent-callable restore.

Implemented behavior:

- `codex_room/maintenance.py` provides `check`, `backup`, `verify`, and `restore`;
- `codex-room-maint.cmd` exposes the module through the repository virtual environment on Windows;
- v1 is explicitly offline for current-data operations: `check`, `backup`, and `restore` require the operator to assert `--offline-confirmed`; backup-archive `verify` does not;
- `check` validates a real/non-reparse data tree, runs SQLite `PRAGMA quick_check` and `foreign_key_check`, and reports bounded health facts;
- `backup` uses SQLite's native backup API rather than copying `codex-room.db` directly, copies the remaining durable data tree while excluding recursive backup archives and SQLite WAL/SHM sidecars, and publishes only after staged verification succeeds;
- every backup contains a schema-v1 root manifest with relative path, byte size, and SHA-256 for every payload file;
- `verify` requires exact manifest/payload agreement, rejects unsafe paths/symlinks/reparse points, verifies every size/hash, and rechecks SQLite health;
- `restore` verifies the selected backup before current-state mutation, builds and checks a complete candidate tree, preserves the existing backup collection, requires both `--offline-confirmed` and `--confirm-replace-data`, then performs a same-parent candidate/rollback directory swap;
- if the final candidate-to-data swap fails after the old root was moved aside, the rollback path restores the prior data root; focused fault-injection coverage verifies that behavior.

During PR verification, the first hosted run exposed a real boundary bug: the verifier initially treated every nested file named `manifest.json` as reserved, which rejected legitimate durable custom-capability manifests. The fix restricts the reserved name to the backup archive's root `manifest.json`, while retaining traversal and reserved-`backups/` rejection.

Verification:

- final exact PR #73 head `136eeec8755922023618c8a13c644155d01ae63b` passed **369 tests, 2 warnings** in GitHub Actions run `35009406047`;
- PR #73 squash-merged as `e22dd9a51c8f803bda1cce0ae658c30b2f383056`;
- the merge carries the same tested Git tree `a708a1dfa2a3a570425b435318144d8e9a7d4c35`;
- canonical-`main` run `35009644053` passed **369 tests, 2 warnings** in 74.07 seconds.

Evidence boundary: the implementation and deterministic hosted verification are complete. The offline flag is an explicit operator assertion, not automatic process-state detection. No destructive restore was run against the principal's live Personal data as part of verification.

**Status:** I-010 COMPLETE / IMPLEMENTED / VERIFIED on canonical `main`.

### E-088 — I-011 verification-platform and dependency assurance implemented and canonically verified
**Date:** 2026-09-15  
**Scope:** [CORE / engineering assurance] Cross-platform hosted verification, flaky-test repair, pinned browser tooling, dependency/advisory review, and a portability defect exposed by Windows CI.

A3/E-065 identified four bounded assurance gaps: routine hosted CI covered only Ubuntu/Python 3.12 despite Windows-centric Personal operation; recorded orchestration tests contained timing-sensitive sleep/delay assumptions; the specialized browser transcript script resolved the latest Playwright package at execution time; and the intentionally pinned Python dependency set had no routine advisory/freshness review.

PR #75 closes those gaps without adding automatic dependency upgrading, a broad QA framework, runtime model changes, or unrelated refactoring.

Implemented assurance surface:

- `.github/workflows/python-tests.yml` now runs the canonical `python -m pytest -q` suite on Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12 with `fail-fast: false`;
- the Windows lane additionally runs `test-transcript-stability.ps1`;
- that browser script now resolves pinned `@playwright/test@1.63.0` rather than an unversioned latest package;
- `test_finish_preserves_peer_turn_that_is_already_running` uses an explicitly blocked/released peer call rather than a 150 ms delay;
- `test_stop_before_lease_expiry_cancels_without_false_error_or_retry` waits for worker completion rather than manufacturing a 200 ms timeout race and then sleeping 250 ms;
- `.github/workflows/dependency-review.yml` installs pinned `pip-audit==2.10.1`, audits `constraints-test.txt` with `--strict --no-deps`, and emits an informational `pip list --outdated` report. It runs on relevant dependency/workflow changes, monthly, and on manual dispatch. It does not update packages.

The first substantive Windows run demonstrated the value of the new lane. Exact PR head `ad8b5eebd1d36ed4860b4f5579a19d92494d0de3` failed with **6 failed, 363 passed, 2 warnings** because `inspect_source` returned CRLF text on Windows while the same deterministic retrieval contract returned LF on Linux. All six failures were the same platform-newline defect across source-inspection/CLI assertions.

The bounded repair normalizes transient UTF-8 read content from CRLF or CR to LF before line slicing/return, while the durable `size_bytes` and SHA-256 continue to describe the original raw file bytes. A mixed-newline regression verifies both properties. Because the input/output schema and registered interface did not change, `inspect_source` remains interface version 2; its implementation hash changes with the repaired bytes.

Final PR verification:

- exact PR #75 head `77cb237e9d86551f0f314d6d538963742d62e14e` passed **370 tests, 2 warnings** on Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12 in GitHub Actions run `35012714775`;
- the Windows lane also passed **3 browser tests** in that run;
- dependency-review run `35012714808` reported **No known vulnerabilities found** and completed the informational outdated-package report successfully;
- PR #75 squash-merged as `ed2e5f1ea636eacc585bf89168d222f017a4b75d`;
- the final PR head and squash merge carry the exact same Git tree `4ac1f3069363639e1d1275bbff3f64bf2e16a770`.

Canonical-main verification:

- push run `35014379476` on merge `ed2e5f1ea636eacc585bf89168d222f017a4b75d` passed **370 tests, 2 warnings** on Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12;
- its Windows lane passed **3 browser tests**;
- dependency-review run `35014379312` again reported **No known vulnerabilities found** and completed the freshness report successfully.

Evidence boundary: this establishes deterministic hosted coverage for the supported Python floor/current primary Python and the Windows operating platform, plus the specialized browser path and pinned-dependency advisory scan. The monthly outdated-package report creates review visibility; it does not establish that every newer package should be adopted. No claim is made that these lanes exhaust all platform/browser/runtime combinations.

**Status:** I-011 COMPLETE / IMPLEMENTED / VERIFIED on canonical `main`; the ordered A3 remediation sequence is complete.

### E-089 — Room identity/model visibility and Windows restart QOL
**Date:** 2026-09-15  
**Scope:** [ROOM / CORE / operator QOL] Three principal-requested usability improvements.

PR #76 implements a bounded QOL batch:

- the active Room header now displays the persistent `room.id` directly beneath the Room title;
- each agent information card displays `Model <model> · <reasoning effort>`. The snapshot uses an open durable execution when one exists and otherwise the most recent durable `agent_executions` row with a recorded model, so an idle card retains the last model actually used;
- new `Restart-Codex-Room.bat` requests closure of visible supported-browser windows whose title contains `Codex Room`, calls the existing `Kill-Codex-Room.bat`, aborts if shutdown fails, waits five seconds, then launches the existing `Start-Codex-Room.cmd`. The ordinary Kill script remains unchanged and does not close browsers.

Implementation deliberately reuses durable execution records rather than adding a second model-state field or schema migration. The focused runtime regression blocks an Agent A turn and verifies `gpt-5.6-terra` / `high` is exposed as `current`; after release and settlement, the same values remain exposed as `last`.

Verification:

- exact PR #76 head `7312482cabfccdf9d7c65511479ae389aa5e626a` passed **372 tests, 2 warnings** on Ubuntu/Python 3.11 and Ubuntu/Python 3.12, and **372 tests, 2 warnings** plus **3 browser tests** on Windows/Python 3.12 in run `35015874588`;
- PR #76 squash-merged as `fe446d0f8ae68761ca8394a33008f48cc2c4c91d`;
- PR head and merge share exact Git tree `b1ad864d7061775df13862b2e84a155cb24e8f2c`;
- canonical-main run `35016556197` passed **372 tests, 2 warnings** on all three Python lanes and **3 browser tests** on Windows.

Evidence boundary: hosted verification covers the UI contract, current→last model-state transition, restart-script sequencing, and the browser UI suite. The restart wrapper's actual closure of the principal's local browser window is not simulated in CI; title-based browser closure is intentionally best-effort and avoids force-killing unrelated browser state.

**Status:** requested QOL batch IMPLEMENTED / VERIFIED on canonical `main`.


### E-090 — Ordinary-use continuation-economy recurrence and I-014 follow-up
**Date:** 2026-09-15  
**Scope:** [ROOM / CORE / P1] Naturalistic feature testing exposed passive-context orientation, source-retrieval continuation amplification, and cumulative-vs-execution telemetry semantics.

After the controlled E-086 regression, the principal deliberately remained in one ordinary Room and exercised C-only reasoning, single-peer delegation, differentiated dual-peer delegation, source inspection, and C-selected peer model configuration while observing the already-free mechanical `execution_economics` events.

The conversational/coordination path was mostly healthy. A C-only product-design turn required no peer cognition, and a two-peer task used differentiated A/B responsibilities at Luna/medium and returned through the delegation-cohort integration path. Two ordinary-use defects nevertheless emerged.

**Passive backlog orientation.** In the single-peer task, C invoked only A for a new agent-card question. A's coalesced unread batch also contained older passive public material. CORE already persisted which delivery was runnable through `triggering_event_ids` / `passive_event_ids`, but the generated prompt rendered every item identically inside one `<unread_room_events>` list. A answered the older title-editing topic instead of the triggering assignment; C detected the mismatch and re-delegated. The two recovery turns represented roughly 49.6k additional reported tokens in that Room. Source inspection confirmed this was a prompt-assembly information loss, not a routing failure.

**Source-investigation continuation amplification.** Two useful source tasks reproduced the mechanism from E-081/E-085 outside the small E-086 fixture:

- C's source-inspection task recorded **22 tool/activity calls**, **5 failures**, and about **1,046,402 incremental reported tokens**, including about **989,440 incremental cached-input tokens**;
- the delegated source trace used A at Luna/medium and recorded **31 tool/activity calls**, **10 failures**, and about **790,515 incremental reported tokens** for A's investigation; the overall C/A/C task was about **926.5k incremental reported tokens**;
- the activity traces show that `search_many` / `read_many` existed and were used, but the agents still performed repeated successful follow-ups plus avoidable contract/quoting failures. C on Terra/high and A on Luna/medium both showed the pattern, so the evidence does not support treating model tier as the primary cause;
- late provider requests carried tens of thousands of mostly cached input tokens. Repeated model→tool→model continuations therefore replayed substantial persistent-thread context even when newly uncached evidence remained much smaller;
- the active thread sizes were still below the normal proactive-compaction threshold. Compaction runs only after a Room turn settles and therefore cannot repair continuation amplification inside one SDK turn.

The same Room also exposed a telemetry semantics defect. `execution_economics` counted tools from the current execution but displayed the SDK's cumulative persistent-thread token total as though it were that execution's cost. The first turn was unaffected because cumulative and per-execution totals coincide, but later status lines required manual subtraction.

PR #77 implements the bounded follow-up:

- coalesced delivery prompts preserve passive cross-reading but mark runnable events `role="triggering"` and older non-runnable material `role="passive_context"`, with an explicit instruction that triggering events define the current work;
- normal source inspection is directed through the JSON-free `codex-room-cap source` surface rather than generic inline-JSON invocation when the direct surface can express the operation;
- source `search` / `search-many` now accept an explicit regular file as well as a directory while preserving the existing CORE/cross-Room allowlist, traversal, symlink/reparse, output-bound, and no-write protections;
- the always-loaded retrieval guidance states the relevant search limits and makes one `search-many` followed by one `read-many` the normal pattern when several related lookups are already known, with further retrieval reserved for a specific unresolved dependency;
- the mechanical economics event keeps cumulative provider counters in metadata but derives `usage_delta` and tokens-per-tool-call from the immediately prior durable usage snapshot on the same SDK thread. A first execution uses its own cumulative value; missing prior usage or non-monotonic counters yield explicit unavailable/non-monotonic status rather than a fabricated delta;
- no schema migration, hard tool quota, research planner, automatic model router, new metrics subsystem, or expansion of source-read authority was introduced.

Verification history:

- a superseded PR run exposed one stale regression that still expected the literal old phrase `search-many/read-many`; that lane otherwise reported **375 passed, 1 failed, 2 warnings**. The regression was updated to assert the stronger direct-source/file-or-directory/one-search-many→one-read-many contract;
- final exact PR #77 head `2d898aacecd274962a57cf39b32c983538d403fb` passed **376 tests, 2 warnings** on Ubuntu/Python 3.11 (60.98s), Ubuntu/Python 3.12 (66.21s), and Windows/Python 3.12 (218.96s), plus **3 browser tests** (16.4s) in run `35023873652`;
- PR #77 squash-merged as `7d930127212b94580c6309032b83d654d032570e`;
- final PR head and squash merge share exact Git tree `e3a5e382712ac64e23f7abe9e5bc25cf2dfa3a10`;
- canonical-main push run `35024443078` passed **376 tests, 2 warnings** on Ubuntu/Python 3.11 (63.63s), Ubuntu/Python 3.12 (158.29s), and Windows/Python 3.12 (240.39s), plus **3 browser tests** (17.6s).

Evidence boundary: the ordinary-use Room demonstrates recurrence of the continuation mechanism and the stale-passive orientation error; hosted verification establishes the bounded CORE repair. It does **not** yet establish a universal post-fix token-savings percentage for arbitrary source investigations, and no paid synthetic rerun is warranted. Continue naturalistic monitoring through work the principal actually wants done.

**Status:** I-014 follow-up IMPLEMENTED / VERIFIED on canonical `main`; continuation economy returns to ordinary-use MONITOR.

### E-091 — Restart preserves the existing browser tab instead of closing the browser window
**Date:** 2026-09-15  
**Scope:** [CORE / operator QOL] Principal runtime observation and bounded Windows launcher correction.

After E-089, principal runtime testing showed that the original `Restart-Codex-Room.bat` browser-close step did not close only the Codex Room tab in Chrome. The script selected a browser process by `MainWindowTitle` and called `CloseMainWindow()`; on Chrome that closes the entire top-level browser window and therefore can close unrelated tabs in the same window.

PR #78 replaces that unsafe approximation rather than adding browser-specific tab automation:

- Restart no longer enumerates or closes browser windows/processes;
- the normal `Kill-Codex-Room.bat` server/process-tree shutdown remains unchanged;
- `Start-Codex-Room.cmd` forwards optional server CLI arguments;
- Restart waits the existing five seconds and launches `Start-Codex-Room.cmd --no-browser`, leaving the already-open Codex Room tab in place and avoiding a duplicate browser tab;
- the existing UI WebSocket reconnect path retries every 1.5 seconds after disconnect, so the retained tab can reconnect after the server returns;
- ordinary Start without arguments retains its existing browser-opening behavior.

Verification:

- exact PR #78 head `92620c9b27db2eec8657c890bf85b2ad8758e929` passed **377 tests, 2 warnings** on Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12, plus **3 browser tests** on Windows in run `35025843774`;
- PR #78 squash-merged as `a1bedcc1bd0ca7037b4c79d5dc41e5aae7812559`;
- final PR head and squash merge share exact Git tree `f1f803a54b0efe229e4690c005ec86cccf12e463`;
- canonical-main run `35026399189` passed **377 tests, 2 warnings** on Ubuntu/Python 3.11 (67.92s), Ubuntu/Python 3.12 (69.54s), and Windows/Python 3.12 (360.67s), plus **3 browser tests** (18.1s).

Evidence boundary: CI verifies launcher contents/sequencing and the existing browser UI suite; it does not physically exercise the principal's exact installed Chrome window/tab topology. The previous E-089 claim that Restart intentionally requests browser-window closure is **SUPERSEDED** by this correction. Local principal confirmation of the new retained-tab restart behavior remains useful naturalistic verification.

**Local principal confirmation:** after pulling the correction, the principal ran `Restart-Codex-Room.bat` on the Personal Windows installation and confirmed that the existing Chrome window/tab remained open and Codex Room recovered successfully after restart.

**Status:** browser-preserving restart correction IMPLEMENTED / VERIFIED on canonical `main` / LOCALLY CONFIRMED.

### E-092 — Ordinary-use stabilization discussion isolates coordination mechanics from cognition
**Date:** 2026-09-15  
**Scope:** [ROOM observation] Room `room_9d8df997c8ff47419252e5877eb9f23c` (“Wits End”), prompted with the demonstrated coordination/economics failures and instructed to use both peers without repository modification.

Observed execution:

- C accepted the supplied incidents as evidence rather than rediscovering them and performed no source/tool inspection before delegation;
- C explicitly gave A a coordination-architecture assignment and B an execution-economics/simplification assignment, selected `terra-medium` for both, emitted `invoke_targets=[agent_a, agent_b]`, and both deliveries became runnable;
- A completed its coordination analysis with 0 tools and **22,399 execution tokens**;
- B completed its economics/simplification analysis with 2 command activities (1 failed, 1 completed) and **66,245 execution tokens**;
- CORE emitted the existing deterministic `delegation_cohort_settled` trigger only after both peer MESSAGE returns existed;
- C consumed both peer returns plus the cohort trigger and produced an integrated FINISH with 0 tools and **27,838 execution tokens**;
- C's initial delegation turn cost **22,040 execution tokens**, making the four execution deltas total **138,522 tokens**.

This run demonstrates that the triad can perform differentiated parallel cognition and deterministic cohort integration economically enough to be materially different from the prior 544,416-token pre-peer evidence loop when the work does not require repeated source/tool continuations.

The run also exposed a remaining settlement-model anomaly: after C FINISHed following the settled cohort, observer telemetry said “Agent C is ready to finish. The Room is waiting for: agent_b,” even though B had already returned its MESSAGE, the cohort-settled event recorded both A and B as settled, and no runnable work remained; the Room then closed as `quiescent_without_work`. This is evidence that peer-contribution settlement, agent FINISH state, and Room closure are not represented by one clean work-state model.

A and B independently converged on the same architectural boundary: keep intellectual allocation/judgment cognitive; move declared assignments, causal delivery, dependency joins, queue ordering, resource budgets, and terminal-state validity into deterministic CORE state. Both rejected brittle prose matching as the primary fix.

**Evidence limit:** this Room did not inspect current CORE source. Its architectural proposals are reasoned from the supplied incidents and observed Room behavior, not proof of implementation feasibility. E-093 separately records the source-level feasibility inspection.

**Status:** OBSERVED ISSUE plus naturalistic architectural evidence; no redesign implementation claim.

### E-093 — Current CORE contains reusable transaction primitives but uses conversational delivery as the work-state kernel
**Date:** 2026-09-15  
**Scope:** [CORE source inspection] Canonical `main` at `6247db876d0c118b88e3f486a36fae702adf01f8`.

Fresh source inspection establishes:

- persistent product/state objects already exist for Rooms, Agents, Rounds, Events, Deliveries, Round-Agent state, exact Agent Executions, and usage continuations;
- `create_event()` creates readable and runnable delivery rows separately, making event visibility and scheduling durable;
- `claim_next_batch()` finds the newest pending runnable conversational delivery for an agent, then claims **every pending conversational delivery in sequence from the agent's delivery boundary through that trigger**, including passive-readable events; `_claimed_batch()` labels the resulting event IDs as triggering vs passive;
- `_delivery_prompt()` therefore still composes work from unread Room events, now with `role="triggering"` / `role="passive_context"` labels added by PR #77;
- the structured agent decision schema carries MESSAGE/PASS/FINISH plus `invoke_targets` and optional peer execution configurations, but it has no first-class task, assignment, dependency, join, or terminal-task action;
- C multi-peer coordination is reconstructed from an `agent_message` event's runnable deliveries; `_release_c_delegation_cohort_if_settled()` searches later decision events for peer responses to that delegation and then synthesizes one `delegation_cohort_settled` trigger for C;
- Round settlement is reconstructed from agent READY_TO_FINISH/PASS state, delivery participation, open runnable deliveries, causal-message boundaries, and a separate integration-before-closure check;
- agent executions already provide the exact durable execution primitive needed by a future assignment queue: each claimed batch receives one `agent_executions` row and is bound to one exact SDK thread/turn before Room-side settlement;
- the adapter resumes one long-lived SDK `thread_id` per application-level agent and starts each Room execution as another turn on that thread.

Feasibility conclusion: a Task/Assignment/Join redesign does **not** require rewriting the whole product. Rooms/Rounds/Agents, events as audit history, execution durability/recovery, workspaces/capabilities, model policy, exports, and UI transport are reusable. The concentrated replacement area is the scheduling/work-state kernel: runnable-delivery batching, passive unread events as prompt work, event-derived cohort reconstruction, and heuristic settlement.

A staged implementation can therefore introduce transaction tables/state alongside legacy delivery semantics, preserve historical Rooms under their existing interpretation, and migrate new work deliberately. The later proposal to split durable organizational identity from full provider-thread context is a deeper runtime experiment and should remain separate from the first coordination-state migration.

**Status:** source-level architecture finding supporting I-015; redesign remains EXPLORATORY / NOT IMPLEMENTED.

### E-094 — I-015 Stage A transaction kernel implemented and hosted-verified
**Date:** 2026-09-15  
**Kind:** [CORE] implementation + deterministic hosted verification

D-030 Stage A was implemented in two bounded pull requests while preserving legacy work-model-v1 behavior by default.

**PR #81 — foundation**

Merged to canonical `main` as:

`3043a3789d03013e4c3618eb3f6aff2861cb60df` — `Implement I-015 Stage A transaction kernel foundation`

This slice introduced the version-2 structured decision contract (`COMPLETE | DELEGATE | PASS`), durable Task/Assignment/Join state, exact assignment-to-execution binding, explicit assignment claiming, atomic delegation/join creation, nested delegation, task-level settlement, transaction failure release, stop cancellation, turn-budget enforcement, pause/resume support, transaction quiescence, and protection against profile rebind while transaction work is open.

**PR #82 — remaining Stage A invariants**

Merged to canonical `main` as:

`a4f53a7c4f62a5d03a0907365f5024d266801e1c` — `Complete I-015 Stage A transaction invariants`

This slice added explicit required-contributor controls and settlement enforcement, transaction state in snapshots and exports, transaction-aware usage-wall suspension/release on the same logical assignment, exact restart recovery for active transaction turns, new-Round cancellation/stale-result protection, participant validation, and follow-up inheritance of Round contributor requirements.

**Hosted verification**

Post-merge GitHub Actions run `35036898229` for canonical `main` completed successfully. All three matrix jobs concluded **success**:

- Ubuntu / Python 3.11;
- Ubuntu / Python 3.12;
- Windows / Python 3.12 + browser.

**Status:** IMPLEMENTED / VERIFIED for the opt-in Stage A coordination kernel at `a4f53a7c4f62a5d03a0907365f5024d266801e1c`.

**Activation limit:** this evidence does not establish ordinary-use quality or economics. Work-model v1 remains the default; work-model v2 is ready for bounded paid naturalistic validation before any default-activation decision.

### E-095 — V2-N1 validates transaction settlement but exposes sibling-work visibility waste
**Date:** 2026-09-15  
**Kind:** [ROOM naturalistic validation + current-source diagnosis]  
**Room:** `room_7d645b883f7348f780decd555187473a` (“V2-N1 - First Naturalistic Validation”)

The preregistered first paid naturalistic Stage-A validation ran under `work_model_version=2` with C as starter and A/B as required contributors.

**Mechanical result**

- the Room finished with `close_reason=transaction_settled`;
- one task settled successfully;
- all four created assignments reached `completed`;
- both created joins reached `released`;
- C's root assignment resumed only after its outer join resolved;
- no tool calls, failed tool calls, retries, usage-wall events, stale results, or repository/source inspection occurred;
- the final C answer was coherent, usable, and incorporated the peer work.

This is positive naturalistic evidence for the Stage-A Task/Assignment/Join settlement kernel.

**Economics and coordination result**

The Room used six model executions and **131,976 execution tokens**:

- C initial delegation: 20,649;
- A initial child turn: 20,074;
- B initial child turn: 20,646;
- B nested child turn created by A: 25,508;
- A resume after the nested join: 21,843;
- C final integration: 23,256.

Cached-input deltas totaled 49,408 against 129,003 input-token deltas, about **38.3%**, above the provisional <=25% cached-replay target. The run also used five post-framing model continuations rather than the target <=4.

C's initial DELEGATE correctly differentiated A and B. A then created a second B assignment asking B to independently identify and compare the same class of candidate trials that A itself had been assigned to identify, even while C's original B assignment was already active. That nested path added **47,351 execution tokens** (the second B turn plus A's resulting resume). Subtracting only those two observed deltas gives an illustrative four-turn remainder of **84,625 tokens**, inside the <=100k run target; this is a diagnostic counterfactual, not a claim that an actual rerun will cost exactly that amount.

**Source diagnosis**

Current `_assignment_prompt()` provides the Round objective, the current assignment, overlays/private initialization, and resolved child dependencies. It does **not** provide a child assignment with bounded awareness of its already-declared sibling assignments under the same join. In V2-N1, A therefore had no transaction-envelope knowledge that B already had separate work in flight. This is a work-state visibility omission, not a join/settlement invariant failure.

**Action:** before another paid run, expose sibling assignment agent/state/instruction metadata in the v2 assignment envelope without exposing sibling result content. Preserve nested delegation authority; the goal is to prevent avoidable duplicate cognition, not prohibit legitimate A↔B collaboration.

**Remediation and verification:** PR #85 added bounded sibling assignment context to the version-2 assignment envelope while intentionally withholding sibling result content and preserving the existing single-child nested-delegation path. The PR head `b8876351100161f157cbb6897a205995cd97d808` passed hosted GitHub Actions run `35038949753` on Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12 + browser. It merged as `19e5100508e4401f45cd27c11684c438171aa5c5`; the tested PR head and squash merge share exact Git tree `1763d24377718e32606239e13ccd3343242e869e`.

**Status:** OBSERVED ISSUE with IMPLEMENTED / VERIFIED targeted remediation. V2-N2 is still required to establish whether the repair removes the naturalistic duplicate-cognition path and returns this task to the intended operating-economics range.

### E-096 — V2-N2 controlled rerun passes Stage-A naturalistic checkpoint
**Date:** 2026-09-15  
**Kind:** [ROOM naturalistic validation]  
**Room:** `room_51eedd657f49497a925aee0f200ae813` (“V2-N2 - Controlled Sibling-Context Rerun”)

V2-N2 repeated the exact V2-N1 task/configuration after the PR #85 sibling-work visibility remediation. It used `work_model_version=2`, C as starting agent, A/B as required contributors, and the same eight-turn ceiling.

**Coordination result**

- one task settled with `close_reason=transaction_settled`;
- exactly three assignments were created: C root, A child, B child;
- exactly one dependency join was created and released once;
- C delegated differentiated work to A and B in one wave;
- neither child created nested peer work;
- after both child assignments completed, the same C root assignment resumed once and completed;
- no assignment or join remained open;
- no tool calls, retries, failures, usage-wall events, stale results, file changes, context compactions, or sub-agent activity were recorded.

This is the intended **C → A+B → C** Stage-A shape.

**Execution economics**

Four model executions consumed **85,228 execution tokens**:

- C initial delegation: 20,675;
- A child assignment: 20,389;
- B child assignment: 20,988;
- C final integration: 23,176.

Input-token deltas totaled 82,866. Cached-input deltas totaled 20,224, for a **24.4% cached-input share**, inside the preregistered <=25% target.

Compared with V2-N1 / E-095:

- executions: **6 → 4**;
- assignments: **4 → 3**;
- joins: **2 → 1**;
- total execution tokens: **131,976 → 85,228**, a reduction of **46,748 / 35.4%**;
- cached-input share: **38.3% → 24.4%**, down about **13.9 percentage points**;
- the redundant nested A→B path disappeared.

The V2-N1 diagnostic counterfactual had estimated an 84,625-token four-turn remainder if the redundant nested path were removed. V2-N2's actual 85,228-token result is within 603 tokens of that estimate, strengthening the causal diagnosis that the missing sibling-work context drove the prior excess.

**Quality result**

The final C answer remained substantively complete: it identified three concrete non-coding trials, selected the household/errand project as the strongest first trial, integrated A's task-selection work with B's testing framework, provided an eight-step execution protocol, and specified observable success and failure criteria. No material omission attributable to the token reduction was observed.

**Interpretation**

The targeted PR #85 repair removed the exact naturalistic duplicate-cognition failure observed in V2-N1 while preserving answer quality and bringing the controlled task inside both Stage-A economic targets. This closes the bounded Stage-A naturalistic checkpoint as **PASS**.

This evidence does **not** establish the later whole-system viability gate: one controlled task cannot establish the required multi-task median/p90 economics, >=90% quality rate, or robustness under tool failure, truncation, stale-history pressure, and interruption/resume.

**Status:** Stage A naturalistic checkpoint PASSED. Default work-model-v2 activation remains unapproved pending the broader viability gate. Stage B bounded evidence execution is the next I-015 work item.

### E-097 — I-015 Stage B declarative source evidence bundles implemented and hosted-verified
**Date:** 2026-09-15  
**Kind:** [CORE] implementation + deterministic hosted verification

The first bounded Stage-B slice is implemented in PR #88.

**Implemented behavior**

- `inspect_source` advances to capability version 3 with a `bundle` operation;
- a bundle accepts 1–16 uniquely labeled, already-known `find`, `search`, `search_many`, `read`, or `read_many` requests;
- each request reuses the existing source-inspection implementation and therefore retains the established workspace / maintained-CORE / Room-shared source confinement and read-only permissions;
- CORE executes the declared requests in order and returns one normalized transient `items` bundle plus durable per-item evidence/provenance;
- aggregate bundle output is capped at 512 KiB and reports deterministic truncation metadata including the next unreturned request index;
- nested `bundle` and `sources` requests are rejected, preventing the bundle from becoming an adaptive plan language or recursive context dump;
- the direct CLI exposes `codex-room-cap source bundle --plan-json ...` and a workspace-relative `--plan-file` alternative;
- agent instructions prefer the bundle only when heterogeneous retrieval operations and their bounds are already known, retain `search-many` / `read-many` for homogeneous batches, and explicitly keep speculative dependent follow-ups outside the bundle.

**Verification**

The final PR head was:

`b7e3ce3ddf9652e21ef4e66f4a5a988a0855b93d`

GitHub Actions run `35041711940` passed all supported jobs:

- Ubuntu / Python 3.11;
- Ubuntu / Python 3.12;
- Windows / Python 3.12 + browser.

PR #88 merged to canonical `main` as:

`6158461bfee94eba375e99baec110e707c30499d`

The final tested PR head and squash merge share exact Git tree:

`e9b7b1d633ecee9b7fb050df794384795f377a6e`

The deterministic tests cover heterogeneous bundled requests, cross-source evidence, transient-vs-durable evidence separation, duplicate/nested/adaptive-plan rejection, aggregate-output truncation, direct JSON/file CLI plans, v3 manifest/version behavior, and the agent prompt boundary.

**Status:** IMPLEMENTED / VERIFIED for the first Stage-B source-evidence-bundle slice. Naturalistic adoption/economics remain unverified; B-N1 is preregistered before another paid run. Stage C remains unimplemented.

### E-098 — B-N1 is inconclusive for bundle adoption and exposes retrieval-overhead signal
**Date:** 2026-09-15  
**Kind:** [ROOM naturalistic validation / test-design correction]  
**Room:** `room_a83ecc1e0287498d8665eedfbc93c620` (“B-N1 - Stage B Evidence Bundle Validation”)

B-N1 ran under `work_model_version=2` with C as the only required worker and a four-turn ceiling. The task asked C to establish three source facts from `codex_room/models.py`, `codex_room/__main__.py`, and `Start-Codex-Room.cmd`.

**Mechanical and quality result**

- one task settled with `close_reason=transaction_settled`;
- exactly one assignment existed, owned by C; no joins were created;
- the Room counted one turn;
- no A/B peer invocation, file change, context compaction, or sub-agent activity occurred;
- the final answer correctly reported:
  - `work_model_version` defaults to `1`;
  - server defaults are `127.0.0.1:8765`;
  - the launcher changes to its own directory and runs `".venv\\Scripts\\python.exe" -m codex_room %*`;
- the final answer cited the requested source paths.

**Why the preregistered bundle criterion is invalid**

The B-N1 preregistration expected one `source bundle` invocation and described the task as heterogeneous. The actual prompt, however, supplied three exact file paths and requested facts obtainable by direct reads. All required retrieval was therefore known homogeneous read work.

Current Stage-B runtime guidance explicitly states that heterogeneous known find/search/read plans should use `bundle`, while `search-many` / `read-many` should be used directly when one homogeneous batch is sufficient. C's eventual use of one `read_many` over the three files was therefore policy-consistent. B-N1 did **not** exercise `bundle`, so it cannot pass or fail naturalistic bundle adoption.

**Efficiency observation**

The single C execution reported:

- **7 tool calls** total;
- 5 command executions;
- 2 deterministic `inspect_source` capability invocations;
- 1 failed command execution;
- 0 capability failures;
- first capability result: `operation=sources`;
- second capability result: `operation=read_many`, with all three requested files returned in one batch;
- `read_many` returned **14,867 bytes**, 3/3 reads, with no truncation;
- **184,143 total execution tokens**;
- 182,922 input tokens;
- 150,784 cached-input tokens;
- 1,221 output tokens;
- 448 reasoning-output tokens.

Cached input was **82.4% of input tokens**. This is far above the earlier provisional 25% whole-task cached-share target, although B-N1 is a different single-agent/tool-heavy shape and should not be mechanically scored as the Stage-A task. The result is nevertheless a strong signal that intra-execution command/tool continuations can repeatedly replay a large persistent context.

The Room export records command success/failure counts but not the exact shell command text. Therefore the aggregate evidence does not establish whether the extra command activity was help discovery, CLI syntax recovery, path probing, or another cause.

**Action**

Before another paid Stage-B Room, inspect the local B-N1 Codex rollout timeline to recover the exact shell-command sequence. Use that evidence to decide whether a small deterministic/CLI discoverability fix is warranted. Do not infer a runtime fix from aggregate counts alone.

After that diagnosis, replace the invalid adoption test with B-N2 using a genuinely heterogeneous, fully predeclared find/search/read evidence plan so `bundle` is the mechanically appropriate operation.

**Status:** B-N1 mechanically successful and answer-correct; **INCONCLUSIVE** for `bundle` adoption due to test-design error; **OBSERVED ISSUE** for command/replay efficiency. Stage B remains IN PROGRESS. Stage C remains separate.

### E-099 — Stage-B consolidation identifies the shell CLI as an agent-facing abstraction leak
**Date:** 2026-09-16  
**Kind:** current-source architecture review + B-N1 consolidation

A consolidation review of B-N1 and canonical `main` at `214fa193d93bbe5cb9a7555c0afe4130469802fc` found that deterministic capability execution is still exposed to Room cognition primarily as a shell/CLI protocol.

Current source evidence:

- the always-loaded deterministic-capability instruction teaches agents when to use registry `list` / `inspect`, generic invocation, direct source commands, `search-many` / `read-many`, `bundle`, inline JSON vs input files, custom-capability authoring/registration, and related operational rules;
- `inspect_source` already contains bounded `find`, `search`, `search_many`, `read`, `read_many`, and `bundle` primitives with source confinement and output limits, so CORE already possesses the deterministic machinery needed to select an execution plan mechanically;
- v2 already has explicit Task / Assignment / Join state and a structured transaction decision contract, providing a natural host for a bounded evidence-request action;
- adapter telemetry still reverse-parses textual capability commands after execution. At this commit, direct source-command recognition covers `sources`, `find`, `search`, `search-many`, `read`, and `read-many`, while `source bundle` is absent from that recognizer even though the CLI and `inspect_source` implement it. This is a source-level interface inconsistency requiring compatibility repair/verification.

B-N1's measured 7 tool calls, failed command, and 184,143-token single execution are consistent with the cost of letting model cognition negotiate this operational interface. The consolidation therefore changes the Stage-B validation target: a model should declare bounded source evidence once, CORE should execute it, and the same assignment should resume with normalized evidence. A second paid test that merely forces the model to remember the word `bundle` would test the old boundary rather than the desired abstraction.

**Status:** source-level diagnosis VERIFIED at the stated commit; the structured evidence path is DECIDED / NOT IMPLEMENTED at this evidence point. B-N1 remains inconclusive for naturalistic `bundle` adoption under E-098.

### E-100 — I-015 Stage B2 structured source evidence execution implemented and hosted-verified
**Date:** 2026-09-16  
**Kind:** [CORE] implementation + exact-diff review + deterministic hosted verification

PR #92 implements D-031's bounded structured source-evidence path for opt-in work-model version 2.

**Implemented behavior**

- `TransactionDecision` adds a fourth action, `EVIDENCE`, carrying 1–16 structured `READ`, `SEARCH`, or `FIND` source requests;
- the request schema carries semantic source/path/query/bound information and excludes agent-facing execution vocabulary such as `bundle`, `read_many`, `search_many`, executable names, shell quoting, or plan-file transport;
- CORE mechanically converts the semantic requests into existing `inspect_source` operations, using direct single operations, `read_many` for bounded homogeneous reads when its aggregate budget can preserve the declared request, and `bundle` for independent multi-request sets whose atomic semantics should be preserved;
- multiple SEARCH requests currently use `bundle` because existing `search_many` has one shared aggregate match cap rather than independent per-request match caps;
- `assignment_evidence` durably binds request identity to the exact assignment and originating execution batch, with pending → ready → consumed state;
- pending evidence is restart-recoverable, successful evidence execution requeues the same assignment, and cancellation/stale-completion guards prevent obsolete evidence from reviving cancelled work;
- bulk evidence content is persisted only while needed to survive and feed the resumed assignment, is omitted from transaction-state/export projection, and is cleared after the resumed assignment settles its next decision; bounded request/plan/result provenance remains durable;
- version-2 prompts use the structured evidence contract for source retrieval while retaining a compact registered/custom capability contract for legitimate non-source deterministic work;
- work-model version 1 retains its existing deterministic-capability instruction/path;
- direct `source bundle` CLI activity is now recognized by the adapter's bounded deterministic-capability telemetry parser, closing the source-level mismatch recorded in E-099.

**Verification**

The exact code-bearing PR head was:

`9b4e352e490a4cdeda9a8242396cabd981f3b19d`

with Git tree:

`2b27d2ea509f279416eb65a8c2a6161414096501`

GitHub Actions run `35066558470` completed successfully on the supported matrix:

- Ubuntu / Python 3.11 — **401 passed, 2 warnings**;
- Ubuntu / Python 3.12 — **401 passed, 2 warnings**;
- Windows / Python 3.12 — **401 passed, 2 warnings**;
- Windows browser transcript-stability check — **3 passed**.

Focused coverage includes mechanical plan selection, homogeneous-read budget fallback, same-assignment evidence resume, transient-vs-durable separation, restart recovery, v2 prompt/legacy-capability compatibility, and direct source-`bundle` telemetry promotion. Exact-diff review also corrected two issues before this final tested head: the restart simulation originally reused a fake SDK turn ID across process instances, and the first v2 prompt revision had removed useful non-source custom-capability guidance.

**Status:** Stage-B2 **IMPLEMENTED / VERIFIED** on the exact tested PR head. Stage-B3 naturalistic consolidated-interface validation remains required before Stage B closes. This evidence does not establish the Stage-C context/memory answer or approve default work-model-v2 activation.

### E-101 — I-015 Stage B3 structured-evidence naturalistic validation passed
**Date:** 2026-09-16  
**Kind:** [ROOM] naturalistic validation / operating-economics evidence

A fresh version-2 Room ran the preregistered Stage-B3 C-only source-evidence task after the Stage-B2 broker reached canonical `main`.

**Configuration**

- Room: `room_5cbd74add7564749862f37696fa4abd4`;
- `work_model_version=2`;
- starting participant: C;
- required contributors: `["agent_c"]`;
- `max_turns=4`;
- no A/B delegation, repository mutation, web use, or external source use requested.

**Observed execution**

1. C's first transaction decision was `EVIDENCE` and declared all three evidence needs together:
   - FIND Python files under `codex_room/`;
   - SEARCH `codex_room/orchestrator.py` for `TRANSACTION_EVIDENCE_INSTRUCTION`;
   - READ `Start-Codex-Room.cmd`.
2. CORE mechanically chose one heterogeneous `bundle` plan and executed all three requests outside model cognition.
3. The SEARCH result established the declaration at lines 157 and 1828 but did not return its text. C therefore issued one additional bounded READ of `codex_room/orchestrator.py` starting at line 150. This was a specific evidence-dependent continuation, consistent with the design boundary that adaptive retrieval remains a later cognitive step.
4. The same logical C assignment resumed after each evidence result and then returned `COMPLETE`.
5. The task settled with one Task, one completed Assignment, no joins, and both evidence records in `consumed` state.

**Economics and mechanical behavior**

- model executions: **3**;
- total execution tokens: **72,271**;
- input tokens: **71,695**;
- cached input tokens: **24,320** (**33.9%** of input);
- agent tool calls: **0**;
- command executions: **0**;
- direct agent capability invocations: **0**;
- failed tool/capability calls: **0**;
- file changes: **0**;
- peer invocations: **0**;
- context compactions: **0**.

This is below the preregistered Stage-B3 target of <=80k total execution tokens. The expected two-execution ideal was missed by one bounded continuation, but the continuation was justified by a concrete returned limitation: SEARCH supplied the location needed to choose the later read range and did not supply the declaration wording required by the prompt.

**Quality / provenance**

The final answer correctly reported:

- `codex_room/transaction_evidence.py` as the Python filename containing “evidence”;
- the version-2 instruction's requirement to declare bounded read-only source needs through `EVIDENCE`, with CORE owning retrieval mechanics and a further request reserved for a specific unresolved dependency;
- the launcher invocation `".venv\\Scripts\\python.exe" -m codex_room %*`.

Both evidence cycles remained bound to the same assignment. The export retained the semantic request, CORE-selected execution plan, normalized durable result, evidence identity, originating request batch, and consumed state.

**Assessment:** **PASS.** The main Stage-B objective is demonstrated in ordinary paid execution: predictable source retrieval moved behind the structured transaction boundary, eliminating CLI discovery, shell transport, batching-choice cognition, retry churn, and direct capability syntax from the agent's work. The one extra retrieval cycle was adaptive evidence work, not interface relearning. Stage B is therefore **COMPLETE / IMPLEMENTED / VERIFIED / NATURALISTIC CHECKPOINT PASSED**.

A preceding accidental run of the same prompt under work-model v1 is excluded from Stage-B3 scoring because it used the wrong work model. It remains useful qualitative contrast only: that run recorded 16 tool calls, 4 failures, and 430,163 execution tokens while ultimately reaching the same factual answer.

Stage C remains a separate decision/experiment. B3's 33.9% aggregate cached-input share does not decide the context architecture, but it supplies fresh motivation to measure durable memory versus active provider-thread replay.

### E-102 — I-015 Stage C.1 assignment-scoped provider context implemented and canonical-main verified
**Date:** 2026-09-16  
**Kind:** [CORE] implementation + exact-diff review + deterministic hosted verification  
**Decision:** D-032

PR #94 implements the first bounded Stage-C provider-context experiment for opt-in work-model version 2.

**Implemented behavior**

- Round configuration adds `provider_context_mode` with values `persistent_agent_thread` and `assignment_thread`; persistent-agent mode remains the default, and assignment-scoped mode requires work-model version 2.
- Each transaction Assignment may durably own a `context_thread_id`. In assignment-scoped mode, CORE starts one provider thread for the logical Assignment and reuses that exact thread for every continuation of that Assignment.
- Evidence resume, dependency/join resume, usage-wall continuation, and exact active-turn restart recovery preserve the Assignment's provider thread rather than falling back to the agent's permanent provider thread.
- Different Assignments receive different provider threads, including successive Assignments owned by the same persistent agent.
- Starting or resuming an assignment-scoped provider thread does not replace the adapter's permanent per-agent thread cache. Existing `persistent_agent_thread` behavior and work-model v1 remain unchanged.
- The adapter can resume an exact recorded non-agent provider thread using the same agent developer instructions, while the existing D-028 model-policy check remains enforced before provider-thread acquisition.
- Assignment-scoped mode skips permanent-thread compaction because active provider history is already bounded by the logical Assignment.
- Round/Assignment state and transaction export preserve the selected context mode and exact Assignment context-thread provenance.

**Review findings corrected before the final tested head**

Exact-diff review and superseded CI caught four material issues before merge:

1. a broad edit accidentally referenced transaction-only `expected_thread_id` in the legacy-v1 usage-continuation insert; v1 was restored unchanged;
2. transaction usage suspension validated the Assignment thread correctly but initially stored the permanent agent thread in the continuation row; storage was corrected to the exact Assignment thread;
3. refactoring moved the D-028 Astra policy check after thread acquisition, causing an adapter initialization error to precede the intended policy error; both public execution entry points now enforce policy before thread access;
4. the first isolation test covered different agents rather than two independent Assignments owned by the same agent; same-agent distinct-Assignment coverage was added.

A small remaining crash window exists after creating an Assignment provider thread but before durably binding it to the Assignment. A process exit in that interval may orphan an unused provider thread. No model turn has started at that point, and existing interrupted-work recovery quarantines claimed work without exact turn identity, so this limitation does not create evidence of duplicate cognition. Provider-thread retention/garbage collection remains outside Stage C.1.

**Exact PR verification**

Final code-bearing PR head:

`c7a8d0d7a4335493d3cb812d755e6df473151ef7`

Git tree:

`aae98a35f543cb1f010ff8deb0270837ed83c720`

GitHub Actions run `35112351716` completed successfully:

- Ubuntu / Python 3.11 — **410 passed, 2 warnings**;
- Ubuntu / Python 3.12 — **410 passed, 2 warnings**;
- Windows / Python 3.12 — **410 passed, 2 warnings**;
- Windows browser transcript-stability check — **3 passed**.

Focused coverage includes the v2-only configuration guard, same-Assignment thread reuse across delegation/join and evidence continuation, same-agent distinct-Assignment isolation, usage-wall restart on the exact Assignment thread, exact active-turn restart recovery, persistent-mode compatibility, and real-adapter non-agent-thread continuation without permanent-cache replacement.

**Canonical-main verification**

PR #94 squash-merged as:

`821fcd9b46925cbbf4905a11846b4b5e1eb18c01`

The merge commit has the exact same Git tree as the tested PR head:

`aae98a35f543cb1f010ff8deb0270837ed83c720`

Canonical-main GitHub Actions run `35113148852` then independently completed successfully:

- Ubuntu / Python 3.11 — **410 passed, 2 warnings**;
- Ubuntu / Python 3.12 — **410 passed, 2 warnings**;
- Windows / Python 3.12 — **410 passed, 2 warnings**;
- Windows browser transcript-stability check — **3 passed**.

**Assessment:** Stage C.1 is **COMPLETE / IMPLEMENTED / VERIFIED** for the opt-in assignment-scoped provider-context mechanism. This evidence establishes deterministic correctness and restart/provenance behavior; it does **not** establish naturalistic token savings, cross-Assignment memory adequacy, provider-thread retention policy, or default activation. Stage C.2 should therefore measure paired context economics before any broader memory architecture is added.

### E-103 — I-015 Stage C.2 C-N1 warmed-history paired context comparison passed
**Date:** 2026-09-16  
**Kind:** [ROOM] paid naturalistic paired diagnostic  
**Decision:** D-032

C-N1 tested whether assignment-scoped provider context materially reduces inherited replay cost on a self-contained Assignment without degrading quality.

**Substrate**

The test reused Stage-B3 Room `room_5cbd74add7564749862f37696fa4abd4`, whose permanent C provider thread `01a0aaa5-ecba-7313-ac8a-ce0afafa610e` already contained the three-execution B3 history. The assignment-scoped arm ran first so its separate context could not mutate the permanent C thread; the identical persistent-thread arm ran second.

Two earlier operator-script attempts created preparation-only Rounds:

- `round_c356baaf9f1a40cc9a2e8509360e1740` — assignment mode;
- `round_b792142e7887427d90a8733a67b4951b` — persistent mode.

Both were stopped as `replaced_by_new_round` before start, with zero Tasks, Assignments, turns, or executions. They are excluded from scoring and did not consume model cognition.

**Valid assignment-scoped arm**

- Round: `round_a6899dc877a04d969c9c3f278424d639`
- Task: `task_3de4bf5015b64bb89057c3c6aea625e8`
- Assignment: `assignment_19045df0c45a41f88b753f20c1a6cff8`
- context mode: `assignment_thread`
- Assignment provider thread: `01a0aae2-6899-7e43-ace4-3b7d986166fb`
- executions: **1**
- input tokens: **20,810**
- cached input: **0**
- output tokens: **239**
- reasoning output tokens: **94**
- total tokens: **21,049**
- tools / capabilities / peers / evidence / file changes / compactions: **0**
- final result: correct **65-minute** optimum, valid worker schedule, valid lower-bound proof.

**Valid persistent-thread arm**

- Round: `round_0096e69b4a1443d1861747aaa4ec78f9`
- Task: `task_ef91b6c0460b4821a92e6be7aebaca9e`
- Assignment: `assignment_2149b43f622b439cb9f838664c238c1e`
- context mode: `persistent_agent_thread`
- provider context: C's permanent thread `01a0aaa5-ecba-7313-ac8a-ce0afafa610e`
- executions: **1**
- per-execution input delta: **27,389**
- per-execution cached-input delta: **17,152** (**62.6%** of input)
- output delta: **184**
- reasoning-output delta: **59**
- total-token delta: **27,573**
- tools / capabilities / peers / evidence / file changes / compactions: **0**
- final result: correct **65-minute** optimum, valid worker schedule, valid lower-bound proof.

The persistent event's top-level `usage` values were cumulative provider-thread usage and are not the paired execution denominator. C-N1 therefore compares the per-execution `usage_delta` values.

**Paired result**

Relative to persistent context, assignment-scoped context reduced:

- input by **6,579 tokens / 24.0%**;
- total execution tokens by **6,524 / 23.7%**.

Both arms required exactly one model execution and preserved answer quality. The assignment arm did not inherit C's permanent provider history and had zero cached input; the persistent arm replayed 17,152 cached tokens.

**Assessment:** **PASS.** C-N1 exceeds the preregistered >=20% input-reduction threshold without extra cognition or quality degradation. It provides naturalistic evidence that an endlessly growing provider thread is not economically neutral and that Assignment-bounded provider context can materially reduce replay on self-contained work.

This result does not establish cross-Assignment memory adequacy. Stage C should proceed only to the preregistered C-N2 boundary test: establish one arbitrary prior fact, compare recall from a fresh assignment-scoped thread against the untouched persistent-thread control, and use that result to decide whether any targeted cross-Assignment retrieval mechanism is warranted.

### E-104 — I-015 Stage C.2 C-N2 demonstrates the cross-Assignment continuity gap
**Date:** 2026-09-16  
**Kind:** [ROOM] paid naturalistic controlled continuity test  
**Decision:** D-032

C-N2 tested whether assignment-scoped provider context can recover one arbitrary fact established in an earlier Round without receiving prior provider-thread history.

The test reused Room `room_5cbd74add7564749862f37696fa4abd4`, C only, work-model version 2, no overlays, no peers, no tools, and no source evidence. The arbitrary nonce was `ORBIT-7429-CEDAR`.

**1. Persistent establishment**

- Round: `round_b0dea5f54c944475898bf230c9ec9bdf`
- Task: `task_a35e3fc9307f498a94bfbd1a5bad57fe`
- Assignment: `assignment_4072e1f399e9460e8b57e892d5c0dc27`
- mode: `persistent_agent_thread`
- provider thread: C permanent thread `01a0aaa5-ecba-7313-ac8a-ce0afafa610e`
- executions: **1**
- per-execution input: **28,336**
- cached input: **26,368** (**93.1%**)
- output: **66**
- reasoning output: **26**
- total: **28,402**
- result: exactly `ORBIT-7429-CEDAR`

**2. Assignment-scoped recall**

- Round: `round_f3b5b0c05f4a4317ab2f8b17888f43cf`
- Task: `task_c1f93341fd964366bc11da0dd5d18ae3`
- Assignment: `assignment_2a862b0c93cf4fe0a9f2355f8c95e1bc`
- mode: `assignment_thread`
- Assignment provider thread: `01a0aae8-16ee-7173-af1c-93ab12f7eb03`
- executions: **1**
- input: **20,750**
- cached input: **17,152** (**82.7%**)
- output: **47**
- reasoning output: **14**
- total: **20,797**
- result: exactly `UNKNOWN`

**3. Persistent recall control**

- Round: `round_90ecc7d2519041ee8f9fbd51d3f9f060`
- Task: `task_4a389d73786d427e9114c3a178a6cb42`
- Assignment: `assignment_74415abaee0f4898ab2889d3ff1dd776`
- mode: `persistent_agent_thread`
- provider thread: C permanent thread `01a0aaa5-ecba-7313-ac8a-ce0afafa610e`
- executions: **1**
- per-execution input: **29,173**
- cached input: **27,392** (**93.9%**)
- output: **38**
- reasoning output: **0**
- total: **29,211**
- result: exactly `ORBIT-7429-CEDAR`

All three Assignments completed normally in one model execution. There were zero tool calls, capability invocations, evidence requests, peer invocations, failures, file changes, context compactions, retries, or extra model turns.

**Interpretation**

The control succeeded: the permanent provider thread retained the establishment nonce. The fresh assignment-scoped provider thread did not receive enough prior-Round context to recover that fact and correctly returned `UNKNOWN` rather than guessing. This is the preregistered outcome that demonstrates a real cross-Assignment continuity gap.

The assignment-scoped recall nevertheless reported 17,152 cached input tokens. That cache hit cannot be treated as evidence of inherited episodic history because the nonce itself was unavailable. It is consistent with reuse of stable system/developer/prompt-prefix material across provider threads.

**Assessment:** **PASS / continuity gap demonstrated.** Combined with E-103, Stage C.2 now establishes both sides of the tradeoff: Assignment-bounded provider context materially reduces inherited replay cost on self-contained work, but continuity-dependent work requires an explicit mechanism to retrieve relevant prior durable history. Stage C.3 should therefore design the smallest bounded targeted retrieval path; this evidence does not justify wholesale history injection, a general summarizer, embeddings, or default activation.

### E-105 — I-015 Stage C.3 bounded Room-history retrieval implemented and hosted-verified
**Date:** 2026-09-16  
**Kind:** [CORE] implementation / deterministic hosted verification  
**Decision:** D-033

PR #99 implemented the first bounded cross-Assignment continuity mechanism without adding a general memory system.

**Implemented boundary**

- transaction action `HISTORY`;
- request operations `RECENT` and lexical `SEARCH`;
- optional `agent_a|agent_b|agent_c` restriction;
- at most 4 requests per action, at most 10 results per request, at most 20 requested/attached results overall;
- selection restricted to non-empty result events from **completed Assignments in earlier Rounds of the same Room**;
- lexical `SEARCH` matches prior Round prompt/title or completed result content;
- selected exact event IDs are attached to the requesting Assignment through the pre-existing durable `context_event_ids` field;
- `HISTORY` is nonterminal and atomically requeues the same Assignment, preserving its logical Assignment identity and assignment-scoped provider thread;
- retrieved history is supplied in a distinct `<retrieved_room_history>` envelope under a 24,000-character bound;
- deterministic audit events retain request and exact selected-event provenance;
- no new memory database, embeddings, summarizer, automatic whole-history injection, or provider-thread archive was introduced.

Focused deterministic coverage verifies request bounds, `RECENT` recovery from a prior Round without provider-thread inheritance, same-Assignment thread reuse across retrieval, durable selected-event provenance, and lexical `SEARCH` by prior Round prompt/title.

**Exact PR verification**

- PR: **#99 — I-015 Stage C3: add bounded cross-Assignment history retrieval**
- final PR head: `78586e96a09f81fb010361604dda3aa4fcd1352b`
- tree: `2d56a4c7631899b66af7d545f571c64209f34f54`
- hosted run: `35119746412`
- Ubuntu Python 3.11: **413 passed, 2 warnings**
- Ubuntu Python 3.12: **413 passed, 2 warnings**
- Windows Python 3.12: **413 passed, 2 warnings**
- Windows browser transcript stability: **3 passed**

**Canonical merge and verification**

- squash-merge commit: `6b88867fc3b22c5e87af0b6d9e9e4281467e0491`
- merge tree: `2d56a4c7631899b66af7d545f571c64209f34f54`
- the merge tree exactly matches the verified PR-head tree;
- canonical-main hosted run: `35120567860`
- Ubuntu Python 3.11: **413 passed, 2 warnings in 86.42s**
- Ubuntu Python 3.12: **413 passed, 2 warnings in 82.31s**
- Windows Python 3.12: **413 passed, 2 warnings in 751.21s**
- Windows browser transcript stability: **3 passed in 27.0s**
- run conclusion: **success**.

**Assessment:** **IMPLEMENTED / VERIFIED.** The deterministic C.3 slice satisfies D-033's bounded explicit-continuity boundary. Naturalistic adequacy is intentionally not inferred from deterministic tests; C-N3 is preregistered as the final Stage-C acceptance check.

### E-106 — I-015 Stage C.3 C-N3 retrieval-enabled continuity acceptance passed
**Date:** 2026-09-16  
**Kind:** [ROOM] paid naturalistic acceptance  
**Decision:** D-032, D-033

C-N3 tested whether a fresh assignment-scoped provider context could recover the exact arbitrary fact that C-N2 showed was unavailable without inherited provider history, using only the bounded D-033 Room-history path.

**Round and work state**

- Room: `room_5cbd74add7564749862f37696fa4abd4`
- Round: `round_05c0fe8a0e3e4cdbae9c6f4909a86959`
- title: `C-N3 Retrieval-Enabled Continuity`
- work model: **2**
- provider context mode: `assignment_thread`
- required contributor: **C only**
- status: **finished / transaction_settled**
- Task: `task_f049e9ecbc17413fbd8da4f6dc4da173`
- one logical Assignment: `assignment_0ccf880bbb54410c83b4c647509d419d`
- Assignment context thread: `01a0ab11-0dfc-7ef2-9f54-45b73197c808`
- C permanent provider thread: `01a0aaa5-ecba-7313-ac8a-ce0afafa610e`

The Assignment context thread is therefore distinct from C's permanent thread. Both execution batches belong to the same logical Assignment, which has one durable `context_thread_id`.

**Execution 1 — HISTORY**

- batch: `batch_052f651eb6b0443c84ca1377dea24cbb`
- action: `HISTORY`
- request: lexical `SEARCH` for `C-N2 Establish Continuity Token`, max 3 results;
- CORE deterministic Room-history audit selected exactly one event:
  - `event_45aff3ef6761486c9783685905c45c24`
- that event is the completed C result from Round `round_b0dea5f54c944475898bf230c9ec9bdf`, titled `C-N2 Establish Continuity Token`, with exact content `ORBIT-7429-CEDAR`;
- per-execution usage: **21,092 input / 0 cached / 106 output / 21,198 total**;
- reasoning output: **28**.

**Execution 2 — COMPLETE**

- batch: `batch_7bd554c57828483eb3620635d1fee6be`
- same Assignment;
- durable `context_event_ids`: [`event_45aff3ef6761486c9783685905c45c24`];
- action: `COMPLETE`;
- result: exactly `ORBIT-7429-CEDAR`;
- per-execution usage: **22,306 input / 20,224 cached / 43 output / 22,349 total**;
- reasoning output: **0**.

**Run totals**

- model executions: **2**
- input: **43,398**
- cached input: **20,224** (**46.6%** of aggregate input)
- output: **149**
- total execution tokens: **43,547**
- model tool calls: **0**
- failed tool calls: **0**
- capability invocations/failures: **0 / 0**
- peer invocations: **0**
- sub-agent activity: **0**
- file changes: **0**
- context compactions: **0**
- source-evidence requests: **0**
- retries/restart anomalies/unexplained executions: **none observed**.

**Acceptance assessment**

All preregistered C-N3 conditions pass:

1. one Task and one logical C Assignment;
2. first relevant decision `HISTORY` with prior result selected;
3. one distinct assignment-scoped `context_thread_id` spans the two execution batches;
4. continuation returns exactly `ORBIT-7429-CEDAR`;
5. both durable Assignment context and audit provenance contain the exact selected C-N2 event ID;
6. no disallowed source evidence, peer, capability/tool activity, retry, restart anomaly, or unexplained extra execution;
7. exact expected execution count: **2**.

**Economics interpretation**

C-N3 is a continuity/architecture acceptance test, not a claim that explicit retrieval always minimizes tokens. The two-execution retrieval path used **43,547 total tokens**, while C-N2's persistent-thread recall control used one **29,211-token** execution. Combined with C-N1, the evidence establishes a tradeoff:

- for self-contained work, assignment-scoped context materially reduced inherited replay (**24.0% lower input** in C-N1);
- when prior episodic context is genuinely needed, explicit bounded retrieval can add a model continuation and additional execution cost.

The preregistered rule said a C-N3 pass closes Stage C and moves the program to Stage D rather than expanding the memory system. Whole-system economics now belong to the Stage-D ordinary-task viability gate.

**Assessment:** **PASS. Stage C COMPLETE.** Assignment-scoped provider context plus explicit bounded Room-history retrieval has deterministic and naturalistic evidence for both isolation and continuity. No current evidence justifies embeddings, broad summarization, automatic whole-history injection, or a general memory index before Stage D.

### E-107 — I-015 Stage D attempt 1 stopped after D-N4 structured-EVIDENCE contract failure
**Date:** 2026-09-16  
**Kind:** [ROOM + CORE diagnosis] paid naturalistic viability-gate checkpoint  
**Decision:** D-031, D-032, D-033

The first preregistered Stage-D viability attempt used fresh Room `room_452465d8fdbf4797b4ac9bbf60723c71`, with every scored Round on work-model v2 and `provider_context_mode="assignment_thread"`.

**Valid scored results before failure**

- **D-N1 PASS** — Round `round_15de552b74c94827b6e516d3a3d1aaa8`; one C Assignment/execution; 21,625 total execution tokens; exact 9:20 AM grocery start; no peers/tools/evidence/history; assignment thread distinct from C's permanent thread.
- **D-N2 PASS** — Round `round_1efd7483b3b1449aa34757a4d43c71a7`; C → B → same C Assignment; three executions; 65,365 total execution tokens; one dependency Join released exactly once; B used a distinct Assignment thread and C resumed its exact original Assignment thread; required B contribution was integrated.
- **D-N3 PASS** — Round `round_644baecca1d54055a8ed38c2bdc26b48`; C → differentiated A+B → same C Assignment; four executions; 89,400 total execution tokens; one outer Join released exactly once; A built the moving plan, B independently audited timing/risk, and C correctly integrated a two-trip plan.

**D-N4 failed run**

- Round: `round_7b38641af8d44d5b9ded3057e418efad`
- Task: `task_7bf3771be9534a47b76acbf3a914a721`
- Assignment: `assignment_5b5c7351aed84a248161b67af4268abf`
- Assignment provider thread: `01a0ab3b-462d-7fe2-ac45-552d7e4f7a37`
- first failed batch: `batch_fd5a8e8c72af41449faecfe89c658de8`
- retry batch: `batch_cfcf8ef44a7e433992b1d3704c3d16d2`
- both executions: `gpt-5.6-terra`, high reasoning
- final Round close reason: `transaction_failed`

Both provider responses attempted transaction action `EVIDENCE` and supplied bounded CORE SEARCH requests with `path: ""`. Runtime `SourceEvidenceRequest.path` has `min_length=1`, so `TransactionDecision.model_validate` rejected the response before `execute_source_evidence` could run. CORE retried the same logical Assignment once; the second provider response again used the invalid empty path and the coordinator Assignment then failed terminally. No D-N4 answer was produced, so D-N4 is a quality FAIL under the preregistered rubric.

**Exact-version CORE diagnosis**

Inspection of canonical Stage-D source at preregistration commit `321fc2b1f74c28e00e1deecc71965952b1ce2e11` established four contributing gaps:

1. `TRANSACTION_DECISION_SCHEMA` exposes EVIDENCE `path` only as `{"type":"string"}`; it does not encode the Pydantic non-empty constraint.
2. `source_inspection.py` requires CORE reads/searches to select an allowed maintained top-level entry; CORE-root `""` is invalid and `"."` is also rejected for CORE. The transaction EVIDENCE prompt does not state this source-specific rule.
3. `fail_transaction_assignment` stores the failed diagnostic in the Assignment's `resolution_reason` before requeue, but `_assignment_prompt` does not surface that reason to the retry. The retry therefore receives no actionable validation feedback.
4. `CodexAgentAdapter._consume_handle` validates the decision before extracting usage/activity into `AgentRunResult`. Both D-N4 durable execution rows consequently ended `failed` with model/effort/thread IDs but no usage/activity payload, preventing normal per-execution economic scoring for the failed turns.

The failure is therefore an **OBSERVED ISSUE** in the integrated structured-EVIDENCE boundary, not an external invalidation of the run. The artifact remains evidence and is not eligible to be silently discarded/reclassified as a clean rerun.

**Assessment:** Stage-D attempt 1 is **STOPPED after D-N4**. D-N1 through D-N3 remain valid historical PASS results; D-N4 remains a FAIL. No D-N5 paid work should begin on the preregistered version because D-N5 exercises the same structured CORE-search boundary and failed-turn economics are currently incomplete. Version 1 remains the production/default work model.

**Required next evidence:** deterministic regression coverage and hosted verification for a bounded [CORE] repair that (a) aligns provider/runtime path validation, (b) states CORE path semantics in the agent contract, (c) exposes exact validation feedback on the single retry without contaminating later continuations, and (d) durably records usage/activity/economics for invalid structured decisions. A later Stage-D attempt must start in a fresh dedicated Room and preserve this attempt as historical evidence.



### E-108 — I-015 D-N4 structured-EVIDENCE remediation implemented, focused locally verified, and merged
**Date:** 2026-09-16  
**Kind:** [CORE] remediation implementation / deterministic local verification / merge closeout  
**Decision:** D-031, D-032, D-033

PR #104 repairs the exact D-N4 boundary exposed in E-107 without discarding or reclassifying the failed naturalistic gate result.

**Implemented repair**

- provider-facing transaction JSON schema now encodes non-empty bounded EVIDENCE paths, matching runtime validation;
- transaction guidance makes the maintained top-level CORE path boundary explicit and rejects root-wide empty/`.` CORE requests;
- invalid structured decisions preserve completed-turn usage/activity and emit execution-economics evidence before retry/failure settlement;
- the exact validation diagnostic is supplied to the one bounded retry on the same logical Assignment;
- retry feedback remains durable through a claimed-but-not-yet-started execution recovery and is cleared only when a valid decision is durably recorded, preventing both restart loss and stale-feedback leakage into later continuations;
- a Windows-invalid test fixture named `nul.txt` was corrected to avoid the reserved Windows `NUL` device name. This was a test-fixture defect, not a product search-text defect.

**Focused local evidence**

Exact code-bearing head: `3c136d250bfd76d189b2c5e0d19921b04a8ee88e`.

On Windows/Python 3.12.10, the exact head passed:

- `test_search_text_skips_non_utf8_and_nul_files`;
- `test_invalid_transaction_decision_retains_completed_turn_telemetry`;
- all tests in `tests/test_transaction_evidence.py`, including the new claimed-execution retry-feedback recovery case.

Combined focused result: **8 passed in 16.33s**. Python compile validation also passed on the immediately preceding code-bearing head before the final restart-safety addition; the final focused pytest import/execution used the exact `3c136d2...` source worktree.

The earlier full local Windows suite on predecessor head `d66b1cbd4a49de310a6302950bc9e7fb5db17b70` produced **409 passed, 5 skipped, 2 failed in 1,197.28s**. Focused investigation established:
- the capability failure came from the Windows-reserved `nul.txt` fixture and was corrected;
- the ordinary v1 new-topic stale-result timeout passed twice in isolation (about 4.7–4.8s call time), so it is recorded as load-sensitive test-suite behavior rather than evidence of a PR #104 product regression.

**Hosted verification limitation**

GitHub Actions run `35133053329` for the exact code-bearing head completed with all three jobs reported failed:
- Ubuntu / Python 3.11;
- Ubuntu / Python 3.12;
- Windows / Python 3.12 + browser.

Each job contains **zero executed steps**. This matches the repeated repository-level Actions startup/runner failure already observed on prior PR #104 attempts and provides no test-result evidence against the code. It also does **not** satisfy the project requirement for applicable hosted verification.

**Process supersession and merge — 2026-09-16:** after this evidence was first recorded, the principal abandoned GitHub Actions as the routine verification path and D-018 was amended accordingly. The Python/dependency workflows were removed from canonical `main`, so the zero-step Actions failure above remains historical infrastructure evidence and no longer blocks the remediation.

PR #104 then merged to canonical `main` as `79bffbfbbdcdbda535d6e69104e2c826208b0451`. Direct comparison showed the changed remediation files `agent.py`, `models.py`, `orchestrator.py`, `tests/test_agent.py`, and `tests/test_transaction_evidence.py` are byte-identical to the focused-tested code-bearing version; `db.py` differs at one unrelated pre-existing Room-ordering line inherited from the newer base, outside the remediation paths.

**Assessment:** **IMPLEMENTED / FOCUSED LOCAL VERIFICATION PASSED / MERGED.** One routine `verify-fast.cmd` run on the merged current `main` remains the exact-tree integration check before restarting Stage D. The next paid viability attempt must use a fresh dedicated Room from D-N1; the failed attempt-1 Room remains historical evidence. Version 1 remains the ordinary default.

### E-109 — Routine verification migrated from GitHub Actions to deterministic local verifier
**Date:** 2026-09-16  
**Kind:** Repository/process inspection + local operator verification measurements  
**Decision:** D-018

Repeated GitHub Actions startup/runner failures consumed substantial maintenance effort without producing test execution. The principal directed that Actions stop being the routine verification path. Canonical `main` then removed `.github/workflows/python-tests.yml` and `.github/workflows/dependency-review.yml` and introduced:

- `verify-fast.cmd`;
- `verify-full.cmd`;
- shared implementation `verify-local.ps1`.

The repository transition is represented by the sequence from `498faca7271623c62afa23776d66370931c328a6` through `f4c39cea9db18be04024750a4d5016eb0cd74903`. The implementation evolved to normalize embedded Bash line endings, avoid multiline Windows→WSL command transport, keep the temporary Bash program under `.git`, distinguish tracked source changes from untracked local artifacts, make Fast mode genuinely focused/cache-aware, and ignore Unix-only `uvloop` in the Windows dependency check.

**Verifier contract**

- **Fast:** Linux/Python 3.12 focused core tests; pinned Windows dependency check/synchronization; focused Windows portability tests; browser transcript stability.
- **Full:** Linux/Python 3.12 full pytest; Linux/Python 3.11 full pytest; pinned Windows dependency check/synchronization; Windows full pytest; browser transcript stability; pinned `pip-audit==2.10.1`.
- the verifier reports the exact commit and tracked-tree cleanliness separately from untracked local files.

**Measured local reference runs**

At `731f25b5e48797e9c7db397a85894ba3ee634bba`, the then-exhaustive local path passed end to end:

- Linux/Python 3.12 full pytest: **413 passed, 2 warnings**;
- Windows focused portability: **118 passed**;
- browser transcript stability: **3 passed**;
- total elapsed: **316.3 seconds**.

At `7ff25ca1f9c8a6f80abd7def1be1ab0f3e1aea9c`, optimized Fast mode passed:

- Linux/Python 3.12 focused core: **42 passed, 2 warnings**;
- Windows focused portability: **118 passed**;
- browser transcript stability: **3 passed**;
- total elapsed: **75.6 seconds**.

The final `f4c39cea...` change only corrected the Windows dependency check to ignore Unix-only `uvloop`; it was intentionally left for the next normal verifier run rather than triggering another special rerun.

**Assessment:** **IMPLEMENTED / VERIFIED through the measured reference runs.** GitHub remains canonical source/history/review machinery. Routine mechanical verification is local and deliberate. Current merged-tree claims still attach to the exact tree actually tested; after later code merges, run the appropriate local verifier before describing that newer tree as verified.

### E-110 — I-015 D-N4 remediation verified on merged canonical main
**Date:** 2026-09-16  
**Kind:** Exact-tree local deterministic verification / remediation closeout  
**Decision:** D-018, D-031, D-032, D-033

After PR #104 and the verification-policy/documentation updates were present on canonical `main`, the local working copy fast-forwarded cleanly from `f4c39cea...` to exact commit:

`668ef98253c5bd1387eefb1b71f99ed38fd8b53c`

The operator then ran the repository-standard `verify-fast.cmd` on that exact commit. The verifier reported:

- mode: **Fast**;
- tracked tree: **clean**;
- 22 untracked local artifacts, explicitly excluded from tracked-source verification;
- Linux/Python 3.12 focused core: **45 passed, 2 warnings** in 39.92s;
- Windows dependency check: pinned dependencies already synchronized;
- Windows focused portability tests: **118 passed** in 21.32s;
- browser transcript stability: **3 passed** in 10.7s;
- verifier summary: every phase exit code **0**;
- total elapsed: **74.7 seconds**;
- final result: **PASS**.

The two Linux warnings were the already-observed Starlette/httpx and anyio deprecation warnings; they did not fail verification.

A final `git status --short` showed only the same class of untracked local runtime/evidence/benchmark artifacts and no tracked-source modifications.

**Assessment:** **PR #104 D-N4 remediation closeout VERIFIED on merged canonical code-bearing main.** The failed Stage-D attempt 1 remains historical evidence and must not be resumed at D-N5. The next paid viability attempt should start in a fresh dedicated Room at D-N1 under the preregistered Stage-D protocol. Version 1 remains the ordinary default during the gate.

### E-111 — Stage-D attempt 2 D-N1 naturalistic pass
**Date:** 2026-09-16  
**Kind:** Paid naturalistic Stage-D viability evidence  
**Decision:** D-031, D-032, D-033

A fresh dedicated Stage-D Room, `room_c47cba973de44f12bde8ef3aaf80bce1`, ran the preregistered D-N1 task under work-model version 2 with `provider_context_mode="assignment_thread"`, starting Agent C, ordinary default profiles/model policy, no private initialization or overlays, `max_turns=8`, and required contributors `["agent_c"]`. The initial opening Round was preparation-only with zero Task/model execution and is excluded under the preregistered rule.

D-N1 settled successfully with one Task, one completed C Assignment, no joins, no peer invocations, no tool/capability calls, no source evidence, and no Room-history retrieval. The Assignment bound its own provider context thread and completed directly.

The returned schedule satisfied every D-N1 quality criterion: pharmacy began at 9:00 AM; grocery shopping began at **9:20 AM** and immediately followed pharmacy; the fixed dentist appointment remained 11:00–11:30; meal prep occurred after grocery shopping; package drop finished by 1:00 PM; lunch and workout were both included without overlap; all scheduled work fit within the 9:00 AM–3:00 PM window.

Execution economics recorded **21,663 total tokens**: 21,257 input, 0 cached input, 406 output, and 275 reasoning-output tokens. There were zero tool calls, zero capability invocations/failures, zero file changes, zero context compactions, zero sub-agent activity, and zero peer invocations.

**Assessment:** **D-N1 PASS** for quality, coordination/provenance, and task-level economics. Stage-D attempt 2 remains IN PROGRESS; continue sequentially with D-N2 in the same Room.

### E-112 — Stage-D attempt 2 D-N2 naturalistic pass
**Date:** 2026-09-16  
**Kind:** Paid naturalistic Stage-D viability evidence  
**Decision:** D-031, D-032, D-033

In the same dedicated Stage-D Room used for D-N1, the preregistered D-N2 task ran under work-model version 2 with assignment-scoped provider context, starting Agent C, required contributor Agent B, ordinary default profiles/model policy, no private initialization or overlays, and max_turns=8.

The transaction followed the expected shape exactly: C framed the decision, delegated one independent check to B using `luna-medium`, B completed on its own Assignment/provider thread, one Join released exactly once, and the same original C Assignment resumed on its exact prior provider thread for integration. Agent A was not invoked. No source evidence, Room-history retrieval, shell/custom capability, or model-tool activity occurred.

Quality passed. B independently recommended Plan North and checked the arithmetic and relocation risk. C's final integrated answer recommended Plan North; correctly computed North at $65/month and $520 over eight months; South at $70/month and $560 over eight months; a 60% × $150 = $90 expected cancellation-fee exposure; and about $650 expected eight-month South cost. It also correctly related the household's 500 GB/month use and low upload demand to North's 1.2 TB cap and 300/20 Mbps service.

Execution telemetry recorded three model executions:
- C framing — `gpt-5.6-terra`, high reasoning effort: **21,410** execution tokens;
- B independent check — `gpt-5.6-luna`, medium reasoning effort: **21,003** execution tokens;
- same-C integration continuation — `gpt-5.6-terra`, high reasoning effort: **23,055** execution-token delta, with 20,224 cached input tokens on the legitimate same-Assignment continuation.

Total D-N2 execution tokens: **65,468**. Post-framing model continuations: **2**.

**Assessment:** **D-N2 PASS** for quality, coordination/provenance, and task-level economics. Stage-D attempt 2 remains IN PROGRESS; continue sequentially with D-N3 in the same Room.

### E-113 — Stage-D attempt 2 D-N3 naturalistic pass
**Date:** 2026-09-16  
**Kind:** Paid naturalistic Stage-D viability evidence  
**Decision:** D-031, D-032, D-033

In the same dedicated Stage-D Room used for D-N1 and D-N2, the preregistered D-N3 task ran under work-model version 2 with assignment-scoped provider context, starting Agent C, required contributors A and B, ordinary default profiles/model policy, no private initialization or overlays, and max_turns=8.

The transaction matched the preregistered shape. C delegated two meaningfully differentiated peer assignments in one action: A was asked to build the logistics plan, while B was asked to audit timing, bottlenecks, contingency risk, and elevator exposure. A and B each ran on their own Assignment/provider thread using `luna-medium`. One outer Join released exactly once after both peers completed, and the same original C Assignment resumed on its original provider thread for integration. No source evidence, Room-history retrieval, shell/custom capability, or model-tool activity occurred.

Quality passed. The final integrated answer correctly identified two trips as both necessary and sufficient, using a capacity-valid 12-box + 2-furniture / 8-box + 1-furniture split. It produced an internally feasible schedule, completed both elevator unloads by 10:25 AM inside the 9:00 AM–noon reservation, left 95 minutes of elevator buffer, scheduled the final old-home walk-through only after the last load had left, and incorporated B's audit warning that starting the walk-through while Trip 2 was in transit would require independent transport for the adult left behind.

Execution telemetry recorded four model executions:
- C framing — `gpt-5.6-terra`, high reasoning effort: **21,493** execution tokens;
- B audit — `gpt-5.6-luna`, medium reasoning effort: **22,418** execution tokens;
- A plan — `gpt-5.6-luna`, medium reasoning effort: **22,914** execution tokens;
- same-C integration continuation — `gpt-5.6-terra`, high reasoning effort: **24,122** execution-token delta.

Total D-N3 execution tokens: **90,947**. Post-framing model continuations: **3**.

**Assessment:** **D-N3 PASS** for quality, differentiated dual-peer coordination/provenance, and task-level economics. Stage-D attempt 2 remains IN PROGRESS; continue sequentially with D-N4 in the same Room.

### E-114 — Stage-D attempt 2 D-N4 structured-evidence pass
**Date:** 2026-09-16  
**Kind:** Paid naturalistic Stage-D viability evidence  
**Decision:** D-031, D-032, D-033

In the same dedicated Stage-D Room used for D-N1 through D-N3, the preregistered D-N4 task ran under work-model version 2 with assignment-scoped provider context, starting and requiring Agent C only, ordinary default profiles/model policy, no private initialization or overlays, and max_turns=8.

The transaction exercised the repaired structured source-evidence path that had failed Stage-D attempt 1. C first issued a structured SEARCH bundle over maintained CORE using the valid non-empty path `codex_room` for `TransactionAction`, `CreateRoomRequest`, and `HISTORY`. After the search located the relevant model definitions, C issued a second structured EVIDENCE action containing targeted READs of `codex_room/models.py`. Both deterministic source-evidence operations completed successfully. No peer Assignments, joins, shell/custom-capability commands, or model-tool activity occurred. The same C Assignment and provider thread were reused across both evidence continuations and final completion.

Quality passed. The final answer reported all five current transaction actions — `COMPLETE`, `DELEGATE`, `EVIDENCE`, `HISTORY`, and `PASS`; the `CreateRoomRequest` defaults `work_model_version=1` and `provider_context_mode="persistent_agent_thread"`; and the HISTORY limits of at most 4 requests per action and at most 20 requested results total. It cited `codex_room/models.py` with the relevant line ranges.

Execution telemetry recorded three C executions, all `gpt-5.6-terra` at high reasoning effort:
- initial framing / first EVIDENCE request: **21,439** execution tokens;
- targeted-source-read continuation: **29,568** execution-token delta;
- final completion continuation: **33,252** execution-token delta.

Total D-N4 execution tokens: **84,259**. Post-framing model continuations: **2**.

**Assessment:** **D-N4 PASS** for quality, structured-evidence provenance, repaired-path behavior, and task-level economics. The attempt-1 empty structured-EVIDENCE path defect did not recur. Stage-D attempt 2 remains IN PROGRESS; continue sequentially with D-N5 in the same Room.

### E-115 — Stage-D attempt 2 D-N5 bounded/truncated evidence-recovery pass
**Date:** 2026-09-16  
**Kind:** Paid naturalistic Stage-D viability evidence  
**Decision:** D-031, D-032, D-033

In the same dedicated Stage-D Room used for D-N1 through D-N4, the preregistered D-N5 task ran under work-model version 2 with assignment-scoped provider context, starting and requiring Agent C only, ordinary default profiles/model policy, no private initialization or overlays, and max_turns=8.

The required bounded partial/truncation condition was exercised exactly. C's first structured evidence request was a maintained-CORE SEARCH for `assignment_thread` at path `codex_room` with `max_matches=3`. The result returned exactly three locations and `truncated=true` with `truncation_reason="max_matches"`. C then treated those results as locators and used targeted structured READ/SEARCH requests to narrow into the validation path and Assignment execution/thread-reuse implementation. Four structured EVIDENCE actions completed successfully before one final COMPLETE action. No peer Assignments, joins, shell/custom-capability commands, or model-tool activity occurred. All five model executions used the same C Assignment and exact same Assignment-scoped provider thread.

Quality passed. The final answer correctly identified:
- `codex_room/models.py:520-539`, where `CreateRoomRequest` permits `assignment_thread` but rejects it unless `work_model_version == 2`;
- `codex_room/db.py` around `claim_next_assignment`, where assignment-scoped mode selects `assignment["context_thread_id"]` rather than the persistent agent thread, checks a ready `usage_continuations` row for the same Assignment/thread, and marks it running when reused;
- the existing-execution recovery branch that returns the already-bound Assignment/execution before claiming new work.

Execution telemetry recorded five C executions, all `gpt-5.6-terra` at high reasoning effort:
- **21,362** execution tokens;
- **23,352** execution-token delta;
- **29,658** execution-token delta;
- **36,389** execution-token delta;
- **39,831** execution-token delta.

Total D-N5 execution tokens: **150,592**. Post-framing model continuations: **4**. This remains below the Stage-D 200k warning threshold and well below the 300k immediate-stop threshold.

**Assessment:** **D-N5 PASS** for quality, bounded/truncated evidence recovery, coordination/provenance, and task-level economics. Stage-D attempt 2 remains IN PROGRESS; continue sequentially with D-N6 in the same Room.



### E-116 — Stage-D attempt 2 D-N6 semantic-continuity quality failure
**Date:** 2026-09-16  
**Kind:** Paid naturalistic Stage-D viability evidence  
**Decision:** D-031, D-032, D-033

In the same dedicated Stage-D Room used for D-N1 through D-N5, the preregistered D-N6 task ran under work-model version 2 with assignment-scoped provider context, starting and requiring Agent C only, ordinary default profiles/model policy, no private initialization or overlays, and max_turns=8.

The structured HISTORY mechanism behaved correctly. C issued one bounded HISTORY search for `D-N1 Solo Saturday Schedule`; deterministic history provenance selected the exact original D-N1 completion event `event_68fda3bbb6264256a5c950653e9a704c`. HISTORY remained nonterminal, and the same logical C Assignment `assignment_2122db71c4984f2aa1cff282e26a84bc` resumed on the same Assignment-scoped provider thread `01a0ac9b-49c2-7b60-8e01-1ef889079958` for final completion. No peers, joins, source evidence, shell/custom capabilities, or model-tool activity occurred.

The final answer correctly reported the original D-N1 grocery-shopping start as **9:20 AM** and moved grocery shopping to **12:00 PM**. However, it moved package drop to **1:45–2:00 PM**. D-N1 explicitly required package drop to finish by **1:00 PM**, and D-N6 explicitly superseded only the original immediate-follow relation between pharmacy and grocery shopping while requiring every other D-N1 constraint to remain satisfied. This is therefore a material explicit-constraint violation.

Execution telemetry recorded two C executions, both `gpt-5.6-terra` at high reasoning effort, on the same Assignment/provider thread:
- first HISTORY request: **21,320** execution tokens;
- final completion continuation: **23,129** execution-token delta.

Total D-N6 execution tokens: **44,449**. Post-framing model continuations: **1**.

**Assessment:** coordination/provenance **PASS**; task-level economics **PASS**; quality **FAIL**. This is the first Stage-D attempt-2 quality failure. Do not rerun D-N6. Because the overall gate requires at least 9/10 quality passes, D-N7 through D-N10 must all pass quality for the gate to remain viable.

### E-117 — Stage-D attempt 2 D-N7 stale-history discrimination pass
**Date:** 2026-09-16  
**Kind:** Paid naturalistic Stage-D viability evidence  
**Decision:** D-031, D-032, D-033

In the same dedicated Stage-D Room after both the original D-N1 result and the later D-N6 revision existed, the preregistered D-N7 task ran under work-model version 2 with assignment-scoped provider context, starting and requiring Agent C only, ordinary default profiles/model policy, no private initialization or overlays, and max_turns=8.

C issued one bounded HISTORY search for `D-N1 Solo Saturday Schedule`. Deterministic history retrieval selected two durable results: the later D-N6 completion event `event_fa579b039a124b9bac267b3e4f20a231` and the intended original D-N1 completion event `event_68fda3bbb6264256a5c950653e9a704c`. The stale-history pressure was therefore real rather than avoided by an exclusive lookup. C correctly discriminated the original result and returned exactly `ORIGINAL: 9:20 AM`, not the D-N6 noon revision.

The transaction used one C Assignment, `assignment_c1fd6a76a112482ba95e00a152dc708f`, and one Assignment-scoped provider thread, `01a0aca6-a970-7ba2-b4b3-a67d5127c0a2`, across both model executions. No peers, joins, EVIDENCE actions, shell/custom capabilities, or model-tool activity occurred. The Task settled cleanly.

Execution telemetry recorded two C executions, both `gpt-5.6-terra` at high reasoning effort:
- first HISTORY request: **21,275** execution tokens;
- final completion continuation: **22,740** execution-token delta.

Total D-N7 execution tokens: **44,015**. Post-framing model continuations: **1**.

**Assessment:** **D-N7 PASS** for stale-history discrimination, quality, coordination/provenance, and task-level economics. Stage-D attempt 2 now stands at **6 quality passes / 1 quality failure** through D-N7. A second quality failure would make the preregistered 9/10 threshold unattainable and end the gate. Continue sequentially with D-N8 in the same Room.


### E-118 — Stage-D attempt 2 D-N8 deterministic evidence-failure recovery pass
**Date:** 2026-09-16  
**Kind:** Paid naturalistic Stage-D viability evidence  
**Decision:** D-031, D-032, D-033

In the same dedicated Stage-D Room used for D-N1 through D-N7, the preregistered D-N8 task ran under work-model version 2 with assignment-scoped provider context, starting and requiring Agent C only, ordinary default profiles/model policy, no private initialization or overlays, and max_turns=8.

The intended stale-path failure occurred first. C issued structured READ evidence against maintained CORE path `codex_room/stage_d_missing_file.py`; the deterministic source-evidence layer returned `ok=false` with `invalid_source_evidence` / `path is unavailable`. The Task and logical Assignment remained intact rather than terminating or corrupting.

C then recovered entirely through later structured source evidence on the same logical Assignment and exact Assignment-scoped provider thread. The recovery sequence used bounded SEARCH/FIND/READ requests only: SEARCH for `TransactionAction.HISTORY`, FIND for transaction/action implementation candidates, READ of `codex_room/transaction_evidence.py`, SEARCH for `TransactionAction` in `codex_room/models.py`, and a final bounded READ of the enum declaration. No peers, joins, HISTORY actions, shell/custom-capability fallback, or model-tool activity occurred.

The final answer correctly stated that the stale-path READ failed, identified the real definition at `codex_room/models.py`, and reported the exact enum value `TransactionAction.HISTORY = "HISTORY"`.

Execution telemetry recorded seven C executions, all `gpt-5.6-terra` at high reasoning effort, all on Assignment `assignment_89a168dba2fd4ad9bbf85d6b78ce3006` and provider thread `01a0acab-6673-78e2-9308-5f1ff655fe58`. Per-execution token deltas were **21,286**, **22,632**, **24,160**, **25,544**, **27,848**, **29,791**, and **31,294**, for **182,555 total execution tokens** and **6 post-framing continuations**.

**Assessment:** **D-N8 PASS** for quality, deterministic evidence-failure recovery, coordination/provenance, and task-level economics. The task remains below the 200k warning threshold and 300k immediate-stop threshold. Stage-D attempt 2 now stands at **7 quality passes / 1 quality failure** through D-N8. Because the overall gate requires at least 9/10 quality passes, D-N9 and D-N10 must both pass quality.


### E-119 — Stage-D attempt 2 D-N9 nested-delegation pass
**Date:** 2026-09-16  
**Kind:** Paid naturalistic Stage-D viability evidence  
**Decision:** D-031, D-032, D-033

In the same dedicated Stage-D Room used for D-N1 through D-N8, the preregistered D-N9 task ran under work-model version 2 with assignment-scoped provider context, starting at Agent C, requiring Agents A and B, ordinary default profiles/model policy, no private initialization or overlays, and max_turns=8.

The required nested dependency shape was preserved exactly: C delegated one planning Assignment to A; A delegated a safety/omission-only audit Assignment to B; B completed; the inner Join released once to the same A Assignment; A resumed on its exact Assignment/provider thread and completed; the outer Join then released once to the same C Assignment; C resumed on its exact Assignment/provider thread and completed. No EVIDENCE, HISTORY, shell/custom-capability, or model-tool activity occurred.

B's contribution remained an audit rather than duplicate plan generation. It identified CO/fire, food-safety, medical-device/medication, temperature, water/sanitation, egress/building, electrical, and communications/local-alert risks. A explicitly incorporated those findings into its finalized contribution, and C's final answer integrated that branch.

The final answer contained **11 checklist items**, separated **First 6 hours** from **Remaining outage (to 48 hours)**, incorporated the material safety/omission findings, and marked local-condition-dependent guidance with `[LOCAL]`.

Execution telemetry recorded five executions:
- C framing: `gpt-5.6-terra` / high, **21,476** tokens;
- A first pass: `gpt-5.6-luna` / medium, **20,753** tokens;
- B audit: `gpt-5.6-terra` / high, **20,985** tokens;
- A continuation on the same Assignment/thread: `gpt-5.6-luna` / medium, **22,742** tokens;
- C integration continuation on the same Assignment/thread: `gpt-5.6-terra` / high, **23,455** tokens.

Total D-N9 execution tokens: **109,411**. Post-framing model continuations: **4**.

**Assessment:** **D-N9 PASS** for quality, nested coordination/provenance, and task-level economics. Stage-D attempt 2 now stands at **8 quality passes / 1 quality failure** through D-N9. D-N10 must pass quality for the 9/10 gate to succeed.


### E-120 — Stage-D attempt 2 final viability-gate pass
**Date:** 2026-09-16  
**Kind:** Paid naturalistic Stage-D viability closeout + aggregate gate assessment  
**Decision:** D-030, D-031, D-032, D-033

The preregistered ten-task Stage-D attempt 2 completed sequentially in one fresh dedicated Room, `room_c47cba973de44f12bde8ef3aaf80bce1`, under work-model version 2 with `provider_context_mode="assignment_thread"`. The preparation-only opening Round had zero model execution and remained excluded exactly as preregistered.

#### D-N10 result

D-N10 ran as one C-only Assignment/execution with no peers, joins, HISTORY, EVIDENCE, tool activity, or other external context. The exact execution used `gpt-5.6-terra` at high reasoning effort, with **21,170 input tokens** and **21,509 total execution tokens**.

The answer correctly enumerated all seven feasible combinations, rejected the all-three combination at **$125.10**, and identified the **$26.25 + $31.40** pair as the highest-spend feasible option at **$105.15** total. D-N10 therefore **PASSed quality**.

The context-isolation baseline from D-N1 was **21,257 first-C input tokens**. The preregistered 125% ceiling was **26,571.25**. D-N10's **21,170** first-C input was about **99.6%** of D-N1 and comfortably inside the ceiling.

#### Ten-task aggregate economics

Per-task total execution tokens:

- D-N1: **21,663**
- D-N2: **65,468**
- D-N3: **90,947**
- D-N4: **84,259**
- D-N5: **150,592**
- D-N6: **44,449**
- D-N7: **44,015**
- D-N8: **182,555**
- D-N9: **109,411**
- D-N10: **21,509**

Sorted totals are **21,509, 21,663, 44,015, 44,449, 65,468, 84,259, 90,947, 109,411, 150,592, 182,555**.

Aggregate thresholds therefore resolve as:
- median total execution tokens: **74,863.5** <= **100,000** — PASS;
- nearest-rank p90: **150,592** <= **200,000** — PASS;
- post-framing continuations by task: **0, 2, 3, 2, 4, 1, 1, 6, 4, 0**; median **2** <= **4** — PASS;
- maximum task total: **182,555** < **300,000** — PASS;
- no task exceeded **200,000**, so the repeated->200k hard-stop condition never arose;
- D-N10 first-C input: **21,170** <= **26,571.25** — context-isolation PASS.

Total paid execution-token use across the ten scored tasks was **814,868**.

#### Quality and robustness

Quality results were **9 PASS / 1 FAIL**. D-N6 was the sole quality failure because its final revised schedule moved package drop past the preserved 1:00 PM deadline. D-N1 through D-N5 and D-N7 through D-N10 passed their preregistered rubrics.

Naturalistic robustness requirements passed:
- D-N5 exercised bounded/truncated evidence and recovered;
- D-N7 exercised stale-history pressure and discriminated the intended original result;
- D-N8 exercised deterministic evidence failure and recovered on the same logical Assignment/thread.

For interruption/restart safety, the post-D-N4-remediation exact code-bearing main commit `668ef98253c5bd1387eefb1b71f99ed38fd8b53c` passed `verify-fast.cmd`. That fast suite includes the exact focused files containing pending-EVIDENCE restart recovery, assignment-thread usage-wall and exact-active-turn recovery, HISTORY continuity coverage, and transaction restart/retry-feedback recovery. A direct comparison from that tested commit to the Stage-D closeout repository state shows only maintained Project-document files changed afterward; no runtime or test code changed. The preregistered unchanged-code condition for relying on E-100, E-102, and E-105 restart evidence is therefore satisfied.

#### Final assessment

All preregistered Stage-D decision conditions are satisfied:

- coordination/provenance invariants: **PASS**;
- robustness coverage: **PASS**;
- economics: **PASS**;
- no task above 300k: **PASS**;
- quality: **9/10 PASS**.

**Stage D attempt 2 therefore PASSES the viability gate.**

This result establishes that the opt-in version-2 task-transaction architecture is viable under the preregistered gate. It does **not** itself change the ordinary default from version 1. Per the protocol, the next step is a separate default-activation / migration decision.


### E-121 — Work-model v2 public-default activation verified and merged
**Date:** 2026-09-16  
**Kind:** Exact-head local verification + production-default activation evidence  
**Decision:** D-034

After the Stage-D viability gate passed, the principal approved a clean production cutover to work-model version 2 with Assignment-scoped provider context. Legacy Rooms are to be deleted rather than converted.

Draft PR #107, `I-015: activate work-model v2 as the public default`, implemented the bounded activation surface:
- public Room creation uses work-model version 2 with `provider_context_mode="assignment_thread"`;
- public staged Round creation uses the same configuration;
- New Topic uses the same configuration;
- rollover successor opening Rounds carry the v2 + assignment-thread public selection;
- explicit public API attempts to select work-model version 1 or the old persistent-agent-thread production mode are rejected;
- dormant internal legacy request paths remain only where useful for deterministic historical tests and are not a supported public production mode.

The exact PR head `6a9137a47de0da27a0425ab7683ca09b9aa41940` was verified locally with the repository-standard `verify-fast.cmd`:
- Linux Python 3.12 focused core: **47 passed, 2 warnings**;
- Windows focused portability: **118 passed**;
- browser transcript stability: **3 passed**;
- tracked working tree: **clean**;
- 42 untracked local artifacts were present but excluded from tracked-source verification.

The PR head remained exactly `6a9137a47de0da27a0425ab7683ca09b9aa41940` at merge time. PR #107 merged successfully to canonical `main` as merge commit `03136c3b11c8c05b8385d0e9f30822dbc014a756`.

**Assessment:** **IMPLEMENTED / VERIFIED / MERGED.** Work-model v2 with Assignment-scoped provider context is now the public production path for new Room work. No legacy-Room migration layer is required under D-034; legacy Rooms are to be deleted deliberately. A bounded live smoke Room remains the next operational verification after the local checkout fast-forwards to the merged main.


### E-122 — Clean v2 cutover and live production smoke
**Date:** 2026-09-16  
**Kind:** Destructive legacy-Room cleanup + live post-activation production verification  
**Decision:** D-034

After PR #107 activated work-model v2 with Assignment-scoped provider context as the public production path, the local checkout was fast-forwarded to canonical `main` and confirmed clean.

Codex Room was then stopped completely before destructive state cleanup. The offline SQLite cleanup enumerated **77 legacy Rooms**, deleted all Room rows with foreign keys enabled, cascaded their Room-scoped relational state, ran a foreign-key integrity check, and reported **Rooms remaining after cleanup: 0**. The legacy `data/rooms` workspace tree and Room-specific custom-capability binding/staging directories were removed. Global agent profiles, institutional releases, and verified custom-capability packages/registrations/verifications were deliberately preserved.

One transcript-only diagnostic in the PowerShell wrapper then printed `Room store was expected to be empty` after the API restart. This was not supported by the authoritative cleanup state and did not prevent the subsequent fresh Room creation. The offline database check immediately beforehand had reported zero Room rows. The fresh smoke Room created afterward was `room_e150b0dce6504d979183609ab0d5d08d`, demonstrating that the post-cleanup store accepted a new Room normally.

The fresh production-default smoke Room used:
- work-model version **2**;
- `provider_context_mode="assignment_thread"`;
- exactly **one transaction Task**;
- exactly **one C Assignment**;
- **zero Joins**;
- exactly one transaction action, **COMPLETE**;
- exactly one model execution;
- **21,172 execution tokens**.

The requested exact final response was `V2 DEFAULT SMOKE PASS`, which the Room returned exactly. The smoke command completed with `=== V2 CLEAN CUTOVER SMOKE PASS ===`, reporting the v2 production work model and Assignment-thread context mode.

**Assessment:** **PASS.** The legacy Room store has been deliberately cleared, and the first retained Room in the clean store successfully executed through the activated v2 production path. I-015 activation follow-through is complete; no further compatibility migration or broad validation is required absent a concrete defect.

### E-123 — Ordinary-use transaction contract/retry repair
**Date:** 2026-09-16
**Kind:** Naturalistic production defect + bounded CORE repair

A Common Cause implementation Round in Room `room_975e0a78e6b040d5bf26d460d577e312` exposed a residual work-model-v2 robustness defect before any game implementation began.

Observed sequence from `Three-Player-Strategy-Game (2).json`:

- C requested workspace `EVIDENCE` with an absolute Windows shared-workspace path; the source inspector correctly rejected it because paths are normalized relative paths.
- On the resumed Assignment, C requested `HISTORY` with `max_results=12`. The provider-facing transaction JSON schema did not advertise the runtime Pydantic maximum of 10, so a provider decision could satisfy the presented schema and still fail internal validation.
- Because the Assignment had already completed one valid EVIDENCE continuation, retry eligibility counted two total Assignment executions and made this malformed decision terminal. The Round closed `transaction_failed`.
- The two C executions consumed **44,496 execution tokens** (21,511 + 22,985) without implementation work beginning.

Repair:

- the transaction provider schema now mirrors the relevant Pydantic bounds for delegation instructions, EVIDENCE READ/SEARCH/FIND limits, and HISTORY `max_results`;
- EVIDENCE agent guidance now states source-relative normalized forward-slash paths, forbids absolute filesystem paths, and states `.` root semantics;
- HISTORY guidance states 1–10 results per request and at most four requests;
- the hidden aggregate requested-result validator was removed while actual retained prior-Round context remains mechanically capped at 20 selected event IDs;
- one corrective Assignment retry now depends on the count of prior failed executions, so successful EVIDENCE/HISTORY continuations do not consume the retry budget;
- regression coverage reproduces successful EVIDENCE → malformed decision → feedback retry → valid completion.

Verification:

- code-bearing repair commit `4c5644fb2273dfe8c9a3d2de809423bb5e988984`;
- exact post-regression-alignment head `9022e4ab4320de96ffa27d1c2ee9fd2673435a47` passed Linux/Python 3.12 full suite **421 passed, 2 warnings** and `git diff --check`;
- Windows focused transaction/source tests passed **43 tests** on `a04edb2a831643f8cfb125a7a87d6e7f61ee1be0`, whose production bytes match `9022e4ab...`; the later difference is the aligned history-validation regression test.

**Assessment:** OBSERVED ISSUE → IMPLEMENTED / VERIFIED bounded repair. This is post-I-015 ordinary-use defect repair, not a reopening of broad v2 validation.

### E-124 — Common Cause coordination-economics structural refinement
**Date:** 2026-09-17
**Kind:** [ROOM baseline economics + CORE protected-instruction implementation + exact-head local verification]
**Decision:** D-035

The Common Cause game exercise supplied a naturalistic coordination-economics baseline after the work-model-v2 production cutover.

The successful historical implementation Round was `round_f2075476746b4263a394203a2a2e7f3`. The produced implementation passed **9/9 unit tests**, but the execution topology was expensive:

- **1,511,456 raw execution tokens**;
- 1,491,330 input tokens;
- 1,292,032 cached-input tokens;
- 199,298 uncached-input tokens;
- 20,126 output tokens;
- **16 Room executions**;
- **33 underlying provider responses**;
- **17 native tool calls**.

Per-agent raw execution totals were:

- C: **1,041,653**;
- A: **405,252**;
- B: **64,551**.

The main A implementation path used 7 tools / 8 provider responses / **281,929 tokens**. C's later correction path used 7 tools / 8 provider responses / **640,347 tokens**, with repeated provider inputs around 77–82K tokens.

The observed coordination topology explains a large part of that cost:

1. C delegated implementation and verification concurrently even though useful verification depended on the implementation artifact existing.
2. The verifier therefore could only produce a verification plan rather than verify exact implementation bytes.
3. C later launched A2/B2 corrective assignments concurrently; both settled without producing the needed substantive correction/audit.
4. C then absorbed substantial editing/testing fallback onto its already accumulated coordination context.

The failed A2/B2 path consumed about **100,683 raw tokens**. C's subsequent fallback consumed about **889,673 raw tokens**. Treating only those two paths as avoidable gives a conservative diagnostic total of about **990,356 tokens**, or **65.5%** of the successful implementation Round.

This is a diagnostic counterfactual, not a claim that a repaired rerun will save exactly that amount. The full historical exercise through implementation consumed about **1,802,046 raw execution tokens**. Its design-only Stage 1 baseline used four model executions and **98,996 raw execution tokens**.

The principal also observed an approximately 11-percentage-point decline in the five-hour Codex allowance meter over the relevant period. That provider meter is aggregate and is not used as exact per-Round token attribution; it is retained only as corroborating evidence that the observed raw execution pattern was operationally expensive.

#### PR #109 — dependency-aware sequencing and initial fallback allocation

PR #109, `Refine C dependency sequencing and fallback allocation`, introduced the first bounded protected-C structural repair.

Base:

`c0d9d2ab3423e40e1cabea9b566694010ee23d09`

Exact reviewed head:

`7dce9a3969528bce60b06fb2518297307599d09f`

Source commit:

`2b245f9b5aecef7346d1008a659f548a98d59bb1`

Verified source/test blobs:

- `codex_room/personalities.py`: `8360919461d97e4bfe62868b00138382345cd618`;
- `tests/test_c_structural_coordination.py`: `7091a83aae56297e4e107335bb3b140cdae001f1`.

The repair added two C-only structural rules:

- determine whether proposed concurrent assignments can each produce useful work without another assignment's output; parallelize genuinely independent work and sequence work that depends on a prerequisite artifact, evidence, or result;
- after failed delegated implementation/correction/investigation, prefer a fresh bounded capable peer when it can perform substantial fallback with materially less accumulated context, subject to correctness, safety, continuity, and reliability.

Exact-head local verification passed:

- expected/actual HEAD identity;
- tracked-tree cleanliness;
- exact two-file / 38-insertion diff;
- `git diff --check`;
- focused C structural regression: **2 passed**;
- `verify-fast.cmd`:
  - Linux/Python 3.12 focused core: **49 passed, 2 warnings**;
  - Windows focused portability: **118 passed**;
  - browser transcript stability: **3 passed**.

PR #109 merged to canonical `main` as:

`b708f31faf7ee5c292c2e49efb632500e5f1a83b`.

#### PR #110 — fallback-allocation tightening

Review of the first repair found that its fallback wording remained too permissive. In particular, substantial fallback could still remain on C if C was already operating in a child assignment or if another assignment had settled without actually producing the needed work.

PR #110 tightened the protected-C rule without adding a scheduler, fourth agent, or persistent A/B cognitive specialty.

Base:

`b708f31faf7ee5c292c2e49efb632500e5f1a83b`

Exact reviewed head:

`da4e47efb8d6e350503325f7521a2e9e56735bc1`

Exact changed files:

- `codex_room/personalities.py`;
- `tests/test_c_structural_coordination.py`.

Diff:

- **2 files changed**;
- **11 insertions**;
- **6 deletions**.

Verified blobs:

- `codex_room/personalities.py`: `6fbe105abc8684173bd05878eac5f46c2c6ece25`;
- `tests/test_c_structural_coordination.py`: `590a11e2616c7ac69d17c12a756b8b3dee094285`.

The tightened rule says that when delegated implementation, correction, or investigation fails to produce needed work, **or when fallback work reaches C because another assignment failed or settled without producing it**, C should normally place substantial tool-heavy execution in a fresh bounded peer assignment rather than execute it itself. The rule applies whether C is operating in the root coordination assignment or in a peer-created child assignment.

Direct C execution remains permitted when the work is demonstrably small in expected execution/context cost, urgent, inseparable from integration, or no fresh peer is likely to perform it reliably at lower total cost. The wording also makes explicit that a code/file change that looks small does not by itself establish that the model execution will be cheap.

The principal's exact-head verification established:

- expected head == final head: `da4e47efb8d6e350503325f7521a2e9e56735bc1`;
- expected base ancestry;
- exact two-file change set;
- `git diff --check`: PASS;
- focused C structural regression: PASS;
- `verify-fast.cmd`: PASS;
- Windows focused portability: **118 passed**;
- browser transcript stability: **3 passed**;
- post-verification head and both blobs unchanged;
- tracked tree clean.

PR #110 merged to canonical `main` as:

`ad9e46310068c07facea34ef0de76456881cd271`.

Post-merge canonical inspection confirmed that `main` carries the exact verified `personalities.py` blob:

`6fbe105abc8684173bd05878eac5f46c2c6ece25`.

#### Evidence boundary and next test

The PR #109/#110 evidence proves that the intended protected C structural rules are present on exact reviewed/verified bytes and merged into canonical `main`. The structural regression proves instruction composition and preservation of surrounding coordination policy.

It does **not** prove that a fresh model execution will behaviorally obey the new sequencing/fallback policy, nor does it establish a realized token-savings percentage.

The next evidence step is therefore a controlled **fresh-Room Common Cause rerun** using the original staged prompts, current production work model, and current protected instructions without telling the agents the historical failure topology, token totals, or expected remedy.

The refinement applies prospectively to freshly composed Rooms. Existing Room snapshots are not retroactively rewritten. Rollover successors continue to inherit predecessor instructions unless later deliberately changed.

**Assessment:** Common Cause exposed a concrete expensive coordination problem; D-035's structural remediation is **IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**. Naturalistic behavioral/economic verification remains **IN PROGRESS** through the fresh-Room rerun.

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

**Assessment:** the coordinator economics/guidance refinement is **IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED**. Its **live naturalistic effectiveness remains unverified** until a bounded ordinary run establishes whether C now chooses `REFRESH` before exact-thread execution load again grows into the previously observed 100K+ range. This pending behavioral check does not reopen the completed BCTX program or authorize an automatic refresh controller.
