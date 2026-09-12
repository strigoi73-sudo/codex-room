# Codex Room — Development Control

**Last updated:** 2026-09-12  
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.  
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** The minimum Engineering Foundation, GPT Project review, D-020 permanent Personal triad / C-integration migration, and **A2 — Assurance Pass 2** are complete. The repository baseline is canonical `main`; verify exact HEAD, applicable CI, and local Git state directly when consequential rather than maintaining those mechanically changing facts here.
- **What just changed?** **P4.2 — Capability registry and discovery** is COMPLETE. A fresh post-PR-#11 Room, without being given the capability name, recorded registry `list` and `inspect`, created the probe file, recovered from one malformed invocation request, then successfully invoked registered `assert_file` with version/hash identity and all requested checks true. C alone FINISHed exactly `P4.2-DISCOVERY-OK` and the Round closed normally.
- **What is blocked?** Nothing currently blocks continued P4 work.
- **What is next?** **P4.3 — Minimal CORE standard library**: choose and implement the smallest broadly useful default capability set that earns its permanent cost, using the P4.2 registry/discovery path rather than hard-coding tool knowledge into agents.
- **What are we deliberately not doing?** No archive/retrieval work, collaboration-quality experiments, provider-neutral implementation, broader productization, or Enterprise expansion unless reprioritized.

## Current Focus

### P4 — Deterministic Room and agent capabilities
**Work state:** IN PROGRESS

P4 is product/runtime work: hard-wire deterministic capabilities that Codex Room or its agents can use during normal operation to replace mechanical model cognition. Development/production automation remains supporting engineering work unless it is deliberately exposed as product functionality.

Admission rule: given the same explicit inputs and underlying state, a correct deterministic capability should return substantially the same factual result without requiring judgment. Agents remain responsible for choosing what to test and interpreting significance.

#### P4.1 — Deterministic assertions
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-12  
**Evidence:** E-030

The first deterministic-capability vertical slice is complete. Codex Room now provides a read-only, Room-workspace-confined `assert_file` capability for exact regular-file existence, SHA-256, JSON-validity, and required-key assertions. It returns typed JSON; recognized direct capability results are persisted as `deterministic_capability` telemetry while arbitrary command output remains hidden. The current transport uses the agent's existing command tool rather than the provider's experimental dynamic-tool API.

Deterministic verification progressed through PRs #5–#7. The final code-bearing canonical-`main` run passed **152 tests, 2 warnings**. Three bounded live attempts then established the full path: the first exposed dropped SDK tool activity because pinned Codex emits camelCase ThreadItem types; the second verified activity normalization but exposed Windows shell-wrapper provenance handling; the third exported the exact structured capability result.

Final live export evidence:

- C was the sole invoked/consuming participant; A/B remained unengaged;
- C created `p4_probe.json`;
- Room telemetry recorded `type: deterministic_capability`, `capability: assert_file`, `status: completed`, and `ok: true`;
- the structured result independently recorded regular-file existence, valid JSON, and presence of both required keys (`probe`, `status`) as true;
- C FINISHed exactly `P4.1-CAPABILITY-OK`;
- the Round closed normally after exactly one agent turn.

P4.1 is closed. Do not broaden this slice merely because the substrate now exists; select the next capability only from demonstrated product value.

#### P4.2 — Capability registry and discovery
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED end to end — 2026-09-12  
**Decision:** D-022  
**Evidence:** E-031

P4.2 makes deterministic capabilities first-class discoverable objects before custom registration or rollover inheritance is implemented.

Implemented behavior:

- each registered capability has a stable ID, description, origin/scope, version, implementation SHA-256, typed input/output contracts, permissions/side effects, verification metadata, and invocation guidance;
- `codex-room-cap list` returns a compact inventory to control context cost;
- `codex-room-cap inspect CAPABILITY_ID` returns the detailed manifest;
- `codex-room-cap invoke CAPABILITY_ID --input-json JSON_OBJECT` invokes by registered ID;
- the already live-verified `assert_file` capability is registered as the first CORE capability; its P4.1 `assert-file` command remains as a compatibility alias;
- normal agent prompts no longer hard-code `assert_file`; they teach the decision boundary for deterministic software, require checking the registry before ad hoc mechanical execution, prefer an adequate registered capability when one exists, and retain ad hoc deterministic execution as a justified fallback;
- registry list/inspect and capability invocation produce bounded structured telemetry, while arbitrary shell output remains excluded;
- this slice implements only a static CORE registry. Custom registration, lineage persistence, rollover inheritance, Personal promotion, and the broader default library remain **DECIDED / NOT IMPLEMENTED** under D-022.

Verification history:

- the substantive P4.2 branch passed **161 tests, 2 warnings** before the final compact-list refinement;
- PR #8 squash-merged as `aeed9d93d16e4933730b1bbea04b54581dbe62d7`;
- the first post-merge run exposed one stale new-test assertion that still expected detailed fields in the intentionally compact list response; runtime source was not implicated;
- PR #9 changed only `tests/test_capabilities.py` to assert the compact-list boundary and obtain details through inspect; exact PR-head run `34714005661` passed **161 tests, 2 warnings**;
- PR #9 squash-merged as `78dd8da418f2c29c37b94324d66bbe8c99da39b3`; canonical-`main` run `34714080693` passed **161 tests, 2 warnings**.
- the first fresh live P4.2 discovery attempt after local adoption of current code created the probe and finished correctly with C only, but telemetry recorded ordinary `command_execution` rather than `deterministic_capability_registry` / `deterministic_capability`; this demonstrated a capability-selection gap rather than a registry implementation failure;
- PR #10 strengthened only the deterministic-capability guidance plus its prompt regression test. Exact PR head `c4b3f5cf03a7684be1414ddd051a49b6d9a1cc69`; GitHub Actions run `34718435578` passed. It squash-merged as `745e76b305cab38607e6035f4fb670c3ea8f2fd4`; canonical-`main` run `34718498032` also passed.
- the next fresh live probe after PR #10 again used only C and FINISHed correctly, but emitted one `file_change` followed by **two** completed generic `command_execution` events. Because the export deliberately hides arbitrary command text, this did not prove the commands were registry operations; it did prove the live stop condition still lacked durable registry/invocation telemetry and was consistent with an unrecognized outer-shell provenance shape;
- PR #11 added only a narrow PowerShell/pwsh wrapper fallback in capability provenance recognition plus regression tests for registry list, registered invoke, and chained-command rejection when `command_actions` are absent. Exact PR head `8304d0a46cab644cb5069a03730af1de057ff1ad`; run `34719562400` passed **164 tests, 2 warnings**. It squash-merged as `80654078567cbdc997c09586994f1d67a1cc784c`. Main run `34719622155` first failed only the pre-existing `test_stop_before_lease_expiry_cancels_without_false_error_or_retry` timing test; rerunning the same merged bytes passed **164 tests, 2 warnings**.

Final live verification on the post-PR-#11 runtime satisfied the stop condition:

- the user prompt did not name `assert_file`;
- C was the sole invoked/consuming participant; A/B remained unengaged;
- telemetry recorded completed registry `list` and `inspect` operations, both identifying `assert_file` version `1` with implementation SHA-256 `6f34376f64110d61d18f278597196b69c1214bba1a8c048c951c3332f049f7b3`;
- after creating `p4_discovery_probe.json`, C made one malformed registered invocation that returned a structured `invalid_request` error, corrected the input, and retried through the registry path;
- the successful `deterministic_capability` event recorded `capability: assert_file`, `capability_version: "1"`, the same implementation hash, `ok: true`, regular-file existence, valid JSON, and required keys `probe` and `status` all true;
- C FINISHed exactly `P4.2-DISCOVERY-OK`; the one-turn Round closed normally.

P4.2 is closed.

#### P4.3 — Minimal CORE standard library
**Work state:** PLANNED  
**Reality / evidence:** DECIDED / NOT IMPLEMENTED  
**Decision:** D-022

Select the smallest set of broadly useful deterministic primitives that should exist in every new Personal Room. Add only capabilities with clear recurring value, compact contracts, bounded permissions/side effects, and deterministic verification. Built-in capabilities must use the same registry/discovery/invocation surface proven by P4.2.


Repository baseline: canonical `main`. Exact current HEAD, hosted CI state, remote-ref agreement, and local working-tree state are intentionally **not maintained in this document**; inspect GitHub and local Git directly when those facts are consequential.

## Recently completed work

### I-006 — Early-triad default profiles missed D-020 migration
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-12  
**Evidence:** E-029

A live post-D-020 smoke Room exposed that the local database still held an older exact built-in A/B/C profile generation. PR #4 added the conservative `triad_profiles_v2` exact-hash migration while preserving non-matching custom content, Room overrides, archived Rooms, and sealed predecessors.

Post-repair local verification used a newly created Room. Its A/B/C `profile_snapshot` values contained the current D-020 instruction text, C was the sole starter, only C consumed Round context or recorded an outcome, C FINISHed with `C-ONLY-OK`, and the Round closed after exactly one agent turn. This verifies both local profile migration and C-only engaged-participant settlement.

I-006 is closed.


### A2 — Assurance Pass 2
**Work state:** COMPLETE  
**Evidence:** E-028  
**Result:** No material runtime GAP demonstrated

A2 assessed the intended post-D-020 architecture using fresh source/config inspection, exact-version/current deterministic test evidence, existing evidence records, and targeted reasoning. It did not launch new in-Room A/B/C exercises or opportunistic remediation.

Material results:

- repository/reproducibility/provenance — **GOOD**;
- agent identity and continuity — **GOOD**, with provider-side profile application remaining **NEEDS VERIFICATION** under I-003;
- execution serialization, stale-result protection, exact-turn recovery, and bounded execution lease — **GOOD**;
- permanent-triad coordination and settlement — **GOOD**;
- retry/usage-wall recovery — **GOOD**; the prior P3 exact-byte review caveat is retired by the A2 current-source review plus current exact-version deterministic tests;
- data integrity, event/delivery provenance, export completeness, and execution observability — **GOOD**;
- current Personal local privacy/exposure boundary — **GOOD**;
- structural operating-economics mechanisms — **GOOD**, but empirical post-D-020 usage efficiency remains **PARTIAL** because no new real-Room usage benchmark was run;
- intent/implementation alignment — **PARTIAL** because of I-004 README drift and because editable A/B profiles currently replace full developer instructions rather than being composed beneath a protected institutional layer. The latter remains a deferred design concern, not an A2 implementation task.

No finding requires repair before P4. See E-028 for evidence and limitations.



### D-020 — Permanent Personal triad / C-integration migration
**Scope:** [CORE + ROOM migration]  
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-12  
**Decision:** D-020  
**Evidence:** E-027

Implemented mandatory A/B/C creation for new Personal Rooms, C-first default Round initiation, direct A↔B selective communication with passive C readability, explicit legacy A/B upgrade behavior, triad rollover successors, engaged-participant settlement, and a mechanical integration-before-closure barrier for unread passive A/B MESSAGE material awaiting C integration.

Verification on the exact reviewed PR head passed **136 Python tests, 2 warnings** in GitHub Actions and **3 Playwright browser tests** locally. PR #3 squash-merged to canonical `main`; the merge tree exactly matched the reviewed/tested head tree. A post-merge push run exposed one race-prone legacy-upgrade test assertion; stabilization changed only that test assertion/comment plus documentation, and the subsequent canonical-`main` run passed **136 tests, 2 warnings**.

### P0 — Selective invocation
**Work state:** COMPLETE  
**Follow-up:** MONITOR  
**Reality / evidence:** IMPLEMENTED / HISTORICALLY VERIFIED — 2026-09-09

Implemented recipient-aware `invoke_targets`, durable readable-vs-runnable delivery semantics, passive backlog behavior, settlement compatibility, and routing telemetry while preserving serialized execution and private authorization.

Historical verification: **111 passed, 2 warnings**, SQLite `quick_check` OK. A real Room exercise used **5 purposeful invocations** and avoided **4 legacy fan-out invocations**.

Monitor for under-invocation of useful peer challenge; do not optimize invocation count at the expense of correctness or collaboration.

### Supporting repair — Retry / Agent Error observability
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / HISTORICALLY VERIFIED — 2026-09-09

Retryable failures are shown as interrupted attempts and reconciled to recovery when later success is correlated. Terminal Agent Error is reserved for exhausted/non-recoverable failure.

Historical full-suite verification: **116 passed, 2 warnings**, SQLite `quick_check` OK.

### P1 — Operational token/usage-efficiency doctrine
**Work state:** COMPLETE  
**Follow-up:** MONITOR — wording may still be deliberately refined

Current work uses the settled practical hierarchy of avoiding unnecessary model calls, invoking only useful cognition, loading only relevant context, preferring deterministic procedures for stable work, scaling reasoning to consequence, and treating output verbosity as a lower-order optimization.

The exact wording of the operational definition remains subject to deliberate refinement and must not be silently hardened into constitutional interpretation.

### P2 — Persistent-context / compaction economics
**Work state:** COMPLETE  
**Follow-up:** MONITOR  
**Reality / evidence:** IMPLEMENTED / HISTORICALLY VERIFIED — 2026-09-09

The pre-compaction baseline ratchet was confirmed and repaired with a deferred post-compaction growth baseline. Historical full-suite verification: **119 passed**, SQLite `quick_check` OK.

### P3 — Usage-wall delayed continuation
**Work state:** COMPLETE  
**Follow-up:** MONITOR  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-12

A positively identified usage wall schedules durable continuation for the same agent/thread at the provider retry time + 60 seconds, with restart survival, serialized release, lifecycle cancellation, and repeated-wall rescheduling.

Historical verification: **10 focused tests passed; 127 full-suite tests passed**; production and fresh-migration database integrity checks were OK.

A2 re-reviewed the current exact source and mapped the focused continuation/restart/reschedule/cancellation tests to the implementation. The former exact-byte review caveat is retired; see E-028.

## Ordered next work

### EF-1 — Reproducible dependency/environment setup
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-10

Clean pip/venv installation is now constrained by `constraints-test.txt`, which records the known-good application/test dependency set while `pyproject.toml` retains broader supported ranges. The merged repair restored green hosted CI with **129 passed, 2 warnings**. No `uv` migration was needed.

### EF-2 — Canonical full-test command
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-10

Canonical routine command: `python -m pytest -q`. Clean-environment verification collected and passed **129 tests**. `test-transcript-stability.ps1` remains a separate specialized browser check.

### EF-3 — Minimal CI
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-10

GitHub Actions runs the canonical Python suite on pushes to `main` and pull requests targeting `main`, installing through `constraints-test.txt`. The latest hosted verification on canonical `main` (`34abd391ecbb861d7661541e4a716a5152a2049d`) completed successfully with **130 passed, 2 warnings**.

### P4 — Deterministic Room and agent capabilities
**Work state:** IN PROGRESS

P4.1 deterministic assertions is complete. P4.2 capability registry/discovery is now the active bounded slice. After P4.2, build the small default CORE library and then the agent-directed custom-capability lifecycle with rollover inheritance; do not pre-fill a speculative domain-specific tool catalog.

## Approved planned development

### Personal daily usage pacing limit
**Work state:** PLANNED  
**Reality:** DECIDED / NOT IMPLEMENTED  
**Decision:** D-019  
**Feasibility evidence:** E-026  
**Scheduling:** approved for development but not yet sequenced relative to P4; it does not displace A2.

Core approved behavior:

- user-configurable daily limit expressed as a percentage of the weekly Codex usage allowance;
- default daily limit: **1/7 of the weekly allowance (~14.3%)**;
- use Codex's structured account rate-limit/usage meter as the pacing source;
- stop initiating new model work after the configured daily allowance has been reached according to the latest available reading;
- allow already-running work to finish, accepting possible small overshoot;
- provider enforcement remains authoritative.

Implementation details such as warning thresholds, UI presentation, carry-forward semantics, daily-period/time-zone semantics, polling cadence, and exact SDK/app-server integration remain open until implementation design.

## Maintenance issues

### I-004 — README conflicts with permanent-triad behavior
**Reality:** OBSERVED ISSUE  
**Evidence qualifier:** VERIFIED — 2026-09-12 repository inspection  
**Priority:** LOW — record during A2; do not interrupt the audit for repair

The README's **First run** section still says the user may choose whether a new Room includes Agent C. Current source and D-020 instead make every new Personal Room an A/B/C triad. The later README **Adding Agent C** section correctly describes the new architecture, so the document is internally inconsistent. This is documentation/intent drift, not evidence of a runtime defect.

### I-003 — B SDK-thread/profile continuity residue
**Reality:** OBSERVED ISSUE — historical provider-side residue; current recurrence not demonstrated  
**Evidence qualifier:** NEEDS VERIFICATION  
**Priority:** LOW  
**Fresh evidence:** 2026-09-12 A2 source/test inspection

A2 found that the current implementation repairs only the known stale pair-era A/B default/snapshot hashes in live unmodified Rooms, preserves archived/sealed/custom state, and records the migration once. Adapter/runtime tests show that a targeted profile rebind evicts only the selected cache entry, resumes the same persistent SDK thread ID with the current developer instructions, fails closed if the SDK returns another identity, and quarantines the worker on a failed resume without changing the durable thread ID.

The remaining uncertainty is narrower than the original observation: current deterministic evidence does **not** independently prove that the provider-side persistent thread has actually adopted the replacement developer instructions after same-thread resume. The runtime's own audit event therefore says instruction application “awaits participant verification.” Keep I-003 open as low-priority **NEEDS VERIFICATION** unless A2 later determines that a live provider-side check is worth its model cost.

## Deferred work

Keep these behind Assurance Pass 2 unless the human principal changes priorities:

- archive retrieval/indexing;
- broader deterministic-tooling expansion;
- scalability/data-integrity work beyond demonstrated issues;
- collaboration-quality experiments;
- provider-neutral implementation;
- broader productization;
- Enterprise workforce features;
- packaging/funding preparation;
- nonessential UI refinement.

## Open questions

No high-priority open question currently blocks P4. I-003 remains low priority and needs provider-side participant verification only if the value justifies a live model check. I-004 is a verified low-priority README drift issue. The broader A/B protected-institutional-layer question remains a future design concern unless the human principal explicitly promotes it.
