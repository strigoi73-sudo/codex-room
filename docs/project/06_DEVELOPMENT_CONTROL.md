# Codex Room — Development Control

**Last updated:** 2026-09-11  
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.  
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** Pre-refresh hold. The minimum Engineering Foundation and the GPT Project review are complete. The repository baseline is canonical `main`; verify exact HEAD, applicable CI, and local Git state directly when consequential rather than maintaining those mechanically changing facts here.
- **What just changed?** The human principal promoted the permanent Personal triad / C-integration migration under D-020 and placed it ahead of A2. I-001 remains fixed and verified, the Project-source review remains complete, and the Personal daily usage pacing limit remains approved planned development under D-019.
- **What is blocked?** Nothing is blocking the planned path.
- **What is next?** The **permanent Personal triad / C-integration migration** is the first major post-refresh task. After it is implemented and adequately verified, **A2 — Assurance Pass 2** follows immediately.
- **What are we deliberately not doing?** No triad-migration implementation before the 2026-09-15 refresh unless explicitly started early by the human principal; no Assurance Pass 2 before that migration is verified; no new in-Room A/B/C exercises; no P4 implementation; no archive/retrieval work; no adjacent refactoring.

## Current Focus

### Pre-refresh hold with triad migration queued ahead of A2
**Work state:** MONITOR

The minimum Engineering Foundation is complete and the targeted GPT Project review is complete. D-020 now makes the permanent Personal triad / C-integration migration the first major post-refresh implementation task. No implementation needs to start before the weekly model-usage refresh unless the human principal explicitly starts it early.

Repository baseline: canonical `main`. Exact current HEAD, hosted CI state, remote-ref agreement, and local working-tree state are intentionally **not maintained in this document**; inspect GitHub and local Git directly when those facts are consequential.

I-001 is closed: bounded live snapshots now expose the newest 2,000-event window and explicit truncation metadata, while Room exports request complete event history. See E-025 for the exact implementation commit and verification evidence.

Until **2026-09-15**, prefer no-op/monitoring over manufacturing work unless the human principal explicitly starts the triad migration early. On or after the refresh, implement and verify the D-020 migration before beginning A2. The default external development workflow remains D-018: reason where relevant context exists, execute through the cheapest capable authorized layer, exchange exact evidence through Git/GitHub, and use deterministic verification where model cognition is unnecessary.

## Recently completed operating-economics work

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
**Reality / evidence:** IMPLEMENTED / HISTORICALLY VERIFIED — 2026-09-09

A positively identified usage wall schedules durable continuation for the same agent/thread at the provider retry time + 60 seconds, with restart survival, serialized release, lifecycle cancellation, and repeated-wall rescheduling.

Historical verification: **10 focused tests passed; 127 full-suite tests passed**; production and fresh-migration database integrity checks were OK.

**Non-blocking review gap:** exact-byte independent review of the P3 implementation was not completed.

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

### Permanent Personal triad / C-integration migration
**Scope:** [CORE + ROOM migration]  
**Work state:** DEFERRED — until 2026-09-15 unless explicitly started early by the human principal  
**Reality:** DECIDED / NOT IMPLEMENTED  
**Decision:** D-020  
**Priority:** first major post-refresh implementation task; complete before A2

Align the runtime with the settled Personal production triad and the new C-first coordination contract:

- create A/B/C in every new Personal Room;
- remove optional-C behavior from ordinary new-Room creation while preserving an explicit migration path for historical A/B Rooms;
- make C the default initial contact / ordinary Round starter;
- preserve direct A↔B communication without routing through C;
- preserve passive readability so C stays durably informed without unnecessary invocation;
- add a mechanical integration-before-closure barrier so material A/B work cannot settle globally without a subsequent C integration opportunity when needed;
- preserve peer judgment, selective invocation, serialized execution, restart recovery, stale-result protection, and token-efficiency guarantees.

Verification should include targeted triad-routing/settlement/restart tests, the canonical full Python suite, the specialized browser transcript/UI check because creation controls change, and hosted CI. Do not call the migration implemented or verified until exact-version evidence supports those claims.

### A2 — Assurance Pass 2
**Work state:** DEFERRED — until the D-020 triad migration is implemented and adequately verified; not before 2026-09-15 unless explicitly changed by the human principal  
**Dependencies:** Engineering Foundation — SATISFIED; D-020 triad migration — PENDING

Use deterministic repository/config inspection first, then existing tests/reproducible checks, runtime/database evidence where needed, and model reasoning only for interpretation. Use adversarial review only where the risk justifies it.

Assessment ratings remain:

- GOOD
- PARTIAL
- GAP
- NEEDS VERIFICATION
- NOT RELEVANT YET

Do not launch a half-audit if available model budget cannot support a coherent bounded pass.

### P4 — Deterministic operational tooling
**Work state:** PLANNED — after Assurance Pass 2

High-value candidates include deployment/restart/activation choreography, diagnostics, health checks, manifests/provenance, profile consistency, rollover inspection, deterministic extraction/validation/deduplication/normalization/statistics, and review-hash checks.

## Approved planned development

### Personal daily usage pacing limit
**Work state:** PLANNED  
**Reality:** DECIDED / NOT IMPLEMENTED  
**Decision:** D-019  
**Feasibility evidence:** E-026  
**Scheduling:** approved for development but not yet sequenced relative to P4; it does not displace the D-020 triad migration or A2.

Core approved behavior:

- user-configurable daily limit expressed as a percentage of the weekly Codex usage allowance;
- default daily limit: **1/7 of the weekly allowance (~14.3%)**;
- use Codex's structured account rate-limit/usage meter as the pacing source;
- stop initiating new model work after the configured daily allowance has been reached according to the latest available reading;
- allow already-running work to finish, accepting possible small overshoot;
- provider enforcement remains authoritative.

Implementation details such as warning thresholds, UI presentation, carry-forward semantics, daily-period/time-zone semantics, polling cadence, and exact SDK/app-server integration remain open until implementation design.

## Maintenance issues

### I-003 — B SDK-thread/profile continuity residue
**Evidence qualifier:** NEEDS VERIFICATION  
**Priority:** LOW  
**Last known evidence:** 2026-09-08

An older B thread appeared to retain pair-era developer-header residue. Do not assume this is current. Recheck only when profile/thread continuity work makes it relevant.

## Deferred work

Keep these behind Assurance Pass 2 unless the human principal changes priorities. The D-020 triad migration is the explicit pre-A2 exception:

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

No high-priority open question is currently blocking the pre-refresh hold. I-003 remains low priority and should be revisited only when profile/thread continuity work makes it relevant.
