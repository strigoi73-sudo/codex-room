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

