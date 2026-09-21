# Codex Room — Development Control

**Last updated:** 2026-09-21
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** I-027 — **PBM v5 platform-outcome benchmark** — is **COMPLETE / IMPLEMENTED / EXACT-HEAD VERIFIED / PROMOTED / FIRST LIVE COMPARISON COMPLETE** under D-050.
- **What just happened?** The first real PBM v5 run, `pbm-v5-benchmark-20260921T130735334526Z`, completed with Desktop **VALID / 100** and Room **VALID / 100**, every retained task scoring 100 on both platforms, matching benchmark fingerprints, `comparable: true`, and no finalization error.
- **Measured result on the frozen seven-task battery:** Desktop used **371,378 tokens in 292.069 s** with one measured top-level thread and zero descendants. Room used **1,473,150 tokens in 628.984 s** across 32 measured executions with 6 peer invocations. Room/Desktop measured-token ratio was **3.9667**.
- **Interpretation boundary:** This is a result for the frozen PBM v5 workload, not a universal product ranking. It demonstrates equal full-credit correctness under the benchmark while Desktop was materially more token- and time-efficient on this run.
- **What is next?** No PBM repair or rerun is required. Preserve this run as the first v5 performance baseline and return to ordinary roadmap selection unless the principal explicitly requests additional benchmark analysis.
- **What is blocked?** Nothing is blocked in I-027.
- **What are we deliberately not doing?** We are not adding another benchmark run merely to manufacture confidence, prescribing either platform's internal topology, or treating the account-level usage meter as the primary token measurement.

## Current development state

### I-027 — PBM v5 platform-outcome benchmark

**Scope:** [platform-level benchmark / equivalent mission and fixtures / native internal orchestration / aggregate platform measurement]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / EXACT-HEAD VERIFIED / PROMOTED / FIRST LIVE COMPARISON COMPLETE

**Decision:** D-050

**Evidence:** E-173, E-174

PBM v5 corrects the benchmark abstraction boundary while preserving the frozen seven-task battery and graders.

Current architecture:

- the comparison unit is **Desktop versus Codex Room as platforms**;
- both platforms receive the same frozen seven-task mission, equivalent prepared fixtures, the same completion criteria, and the same deterministic graders;
- after measured work begins, substantive principal guidance is prohibited;
- Desktop receives one fresh top-level native task rooted at its prepared benchmark workspace and may sequence, parallelize, delegate, create native descendants, or work directly as it chooses;
- Desktop cost/evidence aggregates the measured top-level rollout plus every native descendant attributable through rollout parent lineage;
- Room receives one fresh ordinary measured Room and retains normal A/B/C coordination and D-039 cognition; PBM does not prescribe which peers C invokes or how the Room sequences work;
- Room cost/evidence covers the complete measured Round across all participating executions;
- internal agent topology is provenance and measured cost, not a validity requirement;
- validity remains tied to equivalent starting boundary, frozen mission/prompt integrity, absence of substantive principal intervention, complete provider usage, completion evidence, and deterministic correctness grading;
- automatic evidence capture, comparison, bundling, provider/account usage-meter context, and recovery operations remain deterministic harness responsibilities;
- `benchmarks/pbm/CURRENT` resolves to **v5**;
- PBM v4 is frozen as the promoted predecessor and is superseded for new live comparisons; no paid seven-task v4 comparison completed.

The first paid seven-task v5 comparison completed successfully as `pbm-v5-benchmark-20260921T130735334526Z`: Desktop VALID/100 at 371,378 measured tokens and 292.069 seconds; Room VALID/100 at 1,473,150 measured tokens and 628.984 seconds; Room/Desktop token ratio 3.9667. See E-174.


### I-026 — PBM v4 common protocol with thin platform adapters

**Scope:** [common benchmark protocol / native Desktop adapter / ordinary Room adapter / deterministic pairing and comparison]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / EXACT-HEAD VERIFIED / LIVE CANARY VERIFIED / PROMOTED

**Decision:** D-049 (supersedes D-048 operator-initiation mechanics)

**Evidence:** E-167, E-168, E-169, E-170, E-171, E-172

The principal required two complementary benchmark executions under one common PBM protocol, with exactly one controller initiation per platform and no intermediate principal choreography. That bounded work is complete.

Final production architecture:

- one frozen seven-task cross-domain benchmark battery with equivalent prepared starting fixtures for both products;
- **common protocol:** one normative procedure owns fingerprint binding, fixture equivalence, validity, grading, capture, bundling, automatic pairing, and comparison;
- **Desktop adapter:** one principal instruction to a non-measured Desktop controller; native fresh-task creation launches one fresh measured child and a detached deterministic monitor handles completion;
- provisional Desktop `client-new-thread:<uuid>` identities are resolved fail-closed to the unique persisted rollout created after PBM preparation with the exact controller cwd, then rebound to the durable rollout thread id;
- **Room adapter:** one principal instruction to C in the persistent non-measured PBM v4 Room Runner; C launches a detached deterministic worker that creates and waits only for one fresh measured ordinary Room;
- measured Room work retains normal A/B/C coordination and D-039 cognition, with substantive principal consultation treated as invalid intervention;
- no cross-platform model controller, alternating-arm schedule, platform wait loop, wake-up dependency, or principal run-id relay;
- deterministic state supports status, abort, evidence bundling, and idempotent recovery/finalization when both platform results exist;
- explicit result classification remains **VALID / INVALID / FAILED**;
- token/duration efficiency is reported across the full battery, with task-specific correctness reported separately;
- historical `t07-spec-repair` remains excluded because its frozen contract is internally inconsistent.

Promotion gate:

1. seven-task satisfiability/reference audit — **PASS**;
2. task-specific grader coverage audit — **PASS**;
3. focused deterministic tests — **PASS**;
4. repository routine verification — **PASS**;
5. repaired one-initiation Desktop canary — **PASS / VALID / 100**;
6. one-initiation Room canary — **PASS / VALID / 100**;
7. automatic comparison/fingerprint/finalization and recovery/evidence paths — **PASS**;
8. `benchmarks/pbm/CURRENT` promoted to **v4** — **COMPLETE**.

Final live promotion canary:

- run: `pbm-v4-canary-protocol-20260921T085358797378Z`;
- Desktop: **VALID**, score 100, 126,873 tokens, 20.859 seconds;
- Room: **VALID**, score 100, 144,863 tokens, 44.911 seconds, 1 peer invocation;
- matching benchmark fingerprint: **true**;
- matching canary fingerprint: **true**;
- comparable: **true**;
- finalization error: **none**;
- active pair after completion: **false**.

These canary usage values validate protocol execution only. They are not a performance benchmark result and must not be used to claim relative product efficiency. A paid seven-task comparison remains a separate principal invocation of **Run PBM**.

### I-025 — PBM v3 one-paste workflow

**Scope:** [benchmark operator workflow / native Desktop task controller / deterministic Room controller]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / HISTORICALLY VERIFIED / LIVE-END-TO-END FAILED / SUPERSEDED FOR CURRENT BENCHMARK WORK

**Decision:** D-047

**Evidence:** E-165, E-166

**Postmortem disposition:** E-167 supersedes the earlier readiness inference. The first substantial live run exposed controller-liveness, validity-enforcement, and workload/grader defects. Preserve v3 for historical reproduction only; do not use it for another live performance comparison.


PBM v3 preserves the frozen PBM workload and measurement semantics while removing repeated human prompt/command choreography.

Implemented behavior:

- `benchmarks/pbm/CURRENT` resolves to v3 on canonical `main`;
- the principal opens Desktop on `pbm_desktop_controller` and supplies one instruction: read/execute `DRIVER.md`;
- the Desktop controller performs coordination only and uses native fresh-task management for each Desktop arm; there is no Codex CLI fallback;
- exactly one current Desktop task is staged at a time under the controller folder, while graders/oracles and historical results remain outside the intended child workspace;
- PBM creates one controller Room, stages its files, starts its Round, and has C enter a private principal-consultation wait before any benchmark work;
- the principal's one Room paste is the private reply instructing C to read/execute `PBM_ROOM_DRIVER.md`;
- that controller Room then launches a detached deterministic worker, which creates a fresh ordinary Room for every Room benchmark arm;
- the original sixteen-arm alternating sequence remains authoritative;
- v2 run/task-pair contextual snapshots remain in force;
- D-039 dynamic Room model/reasoning allocation remains part of the measured product behavior;
- Desktop-controller and Room-controller usage are recorded separately from task execution usage, with an all-in view also produced;
- native approval dialogs may still require principal action and are not treated as new benchmark prompts;
- the v3 fingerprint binds orchestration code and driver files in addition to the inherited task assets.

**Verification:** E-165 and E-166. The original final implementation head passed exact-head deterministic verification plus bounded Desktop- and Room-controller preflights. The first live invocation then exposed a controller-directory Python import-path defect before initialization; PR #181 repaired that path with a tracked repo-root wrapper. The exact repair head passed a controller-directory import smoke test, 9 focused PBM tests, and the repository fast verifier. No benchmark task executed during the failed live attempt or the repair verification.

### I-024 — PBM v2 contextual baseline

**Scope:** [benchmark measurement protocol / read-only native account + environment context]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / EXACT-HEAD VERIFIED / READ-ONLY PREFLIGHT VERIFIED / LIVE PAID PBM NOT YET EXECUTED

**Decision:** D-046

**Evidence:** E-164

PBM v2 keeps the PBM v1 workload unchanged while adding interpretive context before and after benchmark work.

Implemented behavior:

- PBM v2 remains explicitly reproducible; canonical `benchmarks/pbm/CURRENT` now resolves to v3;
- the v2 manifest inherits v1 task assets and fingerprints both version trees;
- v1 can still be explicitly reproduced through `--version v1`;
- each v2 run captures `run-start` and `run-end` snapshots;
- each task pair captures one pre-pair and one post-pair snapshot;
- snapshots attempt read-only native `account/rateLimits/read` and `account/usage/read` plus safe runtime/config/tool inventory and local repository/environment provenance;
- snapshot sanitation removes account identity/credential fields while retaining usage/credit/rate-limit semantics;
- native snapshot failures are recorded as unavailable and do not fabricate values;
- primary Desktop/Room usage accounting and deterministic quality graders remain unchanged from v1.
- the Room arm remains naturalistic under D-039: C may dynamically allocate ordinary model/reasoning configurations for itself and peers, and PBM records rather than suppresses those choices.

**Implementation boundary:** satisfied for v2. Snapshot reads are non-cognitive and read-only; the preflight produced no Codex rollout traffic and no task-execution state. They provide interpretive context only and do not replace rollout/Room execution accounting.

### I-023 — PBM (Performance Benchmark)

**Scope:** [benchmark tooling + paired Codex Desktop / Codex Room execution]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / EXACT-HEAD VERIFIED / LIVE PBM RUN NOT YET EXECUTED

**Decision:** D-045

PBM is the canonical standardized performance benchmark for comparing ordinary Codex Desktop with Codex Room across a fixed, versioned suite of paired tasks. The principal invocation **“Run PBM”** must resolve to the current canonical PBM procedure rather than triggering ad hoc benchmark design.

PBM v1 establishes:

- a frozen versioned task suite spanning trivial mechanical work through larger ambiguous/verification-heavy work;
- exact paired starting fixtures and prompts;
- fresh isolated Desktop and Room executions without cross-arm contamination;
- a primary naturalistic comparison in which each product operates as designed, plus a controlled mode where useful for isolating coordination/model effects;
- provider usage accounting using existing rollout instrumentation, with Room A/B/C usage aggregated;
- elapsed-time, tool-call, failure/retry, model/effort, agent-invocation, and coordination-waste measurements;
- deterministic task-specific acceptance checks and explicit quality/correctness outcomes;
- machine-readable run records and a standard human-readable comparison report;
- a low-cost pilot before broader replication, so the benchmark itself does not recreate previously observed high-cost synthetic testing.

**Implementation boundary:** satisfied for v1. The procedure, fixtures, measurement semantics, and reporting contract are now frozen and mechanically inspectable. Future material changes require a new benchmark version rather than silent mutation of v1.

PBM v1 separates the product arms mechanically:

- `pbm-desktop.ps1` prepares a fresh Desktop workspace/prompt and captures the matching native Desktop rollout only after the principal runs the task in a fresh Codex Desktop chat;
- `pbm-room.ps1` prepares a fresh Room without starting cognition, stages the same fixture, then separately starts/waits/exports/captures the Room arm;
- `codex_room/pbm.py` owns only shared deterministic manifest, fixture, grader, accounting, and report logic;
- PBM v1 and v2 remain frozen and explicitly reproducible; `benchmarks/pbm/CURRENT` now resolves the canonical live-use version, PBM v3, which preserves those exact eight v1 task assets, v2 contextual snapshots, and the verified one-paste orchestration protocol.

**Verification:** E-163. The tested PR head and canonical merge commit have the same Git tree. No live PBM task execution is claimed by this verification.

### I-022 — Native Codex capability exposure and execution-economics audit

**Scope:** [CORE + ROOM UI audit; native Codex/App Server first]

**Work state:** COMPLETE

**Reality / evidence:** EXPLORATORY AUDIT COMPLETE / VERIFIED / NO IMPLEMENTATION AUTHORIZED

**Evidence:** E-159, E-160

I-022 separated three questions that must not be collapsed:

1. does exact Codex 0.154 expose a primitive;
2. can Codex Room's SDK/runtime call or inherit it;
3. should Codex Room expose/adapt it as a product feature.

The exact-source audit verified native support for active-turn steering/interruption, model discovery, provider-thread lifecycle controls, native review, rate-limit/usage reads, permission profiles, command/file/permission approvals, tool user-input requests, structured image/local-image inputs, managed-worktree machinery, browser/computer-use feature/configuration surfaces, remote-environment contracts, and other host/runtime facilities.

E-160 then compared those families by current Room status, principal value, inherent cognition cost, continuation/context implications, overlap with Room mechanisms, authority burden, and implementation complexity.

**Selection boundary:** I-022 is not an implementation queue. Any feature-specific runtime probe, implementation slice, revival of a deferred feature such as D-019, or host-integration project requires separate principal selection. Built-in Codex subagents remain disabled.

### I-021 — Principal-controlled Codex plugin management

**Scope:** [native Codex/ChatGPT administration + existing Room visibility/use]

**Work state:** COMPLETE

**Reality / evidence:** NATIVE-HOST PATH SELECTED / VERIFIED AS A PRODUCT BOUNDARY

**Decision / evidence:** D-043; E-157, E-158, E-162

Stage A verified the exact Codex 0.154 plugin/configuration contracts and proved that an A/B/C-equivalent Windows `:workspace` sandbox can reach Codex Room's loopback API, so a Room-local unauthenticated mutation route cannot establish principal-only authority.

Stage B resolved the remaining product choice in favor of native administration. Exact Codex 0.154 already provides human-facing plugin discovery, install/uninstall, enable/disable, marketplace, and app-auth handoff surfaces; current official OpenAI product guidance also exposes plugin installation and management through ChatGPT/Codex surfaces. Codex Room does not override ordinary plugin configuration, already inspects native plugin/skill/MCP/app state for Status & Tools, and can use inherited capabilities through the underlying Codex runtime.

Therefore I-021 closes without a Room-side mutation bridge, copied plugin manager, credential/auth proxy, or new principal-proof security subsystem. Reopen only if ordinary use demonstrates a concrete material cost or capability gap from managing plugin state through the native host.

## Approved or deferred work

### D-019 — Personal daily usage pacing

**Work state:** DEFERRED

**Reality:** DECIDED / NOT IMPLEMENTED

**Evidence:** E-026

The approved baseline remains a configurable daily pacing limit defaulting to one-seventh of the weekly allowance (~14.3%), using structured provider usage/rate-limit data rather than Room token estimates.

Implementation remains deferred until the mixed subscription-allowance versus purchased-credit semantics are understood well enough to define which pool is paced and how multiple pools interact. I-022 verified that exact 0.154 exposes richer account rate-limit/usage structures, but that source-level fact does not by itself resolve the product semantics or reactivate D-019.

### QoL wishlist

Wishlist entries are idea capture, not a work queue. Selection requires an explicit principal choice.

**Implemented / verified:**
- observer composer Enter-to-send / Shift+Enter newline — PR #133;
- composer focus retention — PR #135;
- auto-growing observer composer — PR #135;
- per-Room unsent drafts — PR #135.

**Unselected ideas:**
- new-activity / jump-to-latest control;
- one-click operational-ID copying / Copy diagnostics;
- Room search and filtering;
- transcript detail/noise controls;
- clear immediate action feedback;
- local persistence for harmless presentation preferences;
- conservative navigation/focus keyboard shortcuts;
- copy action on individual agent responses.

## Maintenance / monitor

### PR #110 failed-delegation fallback behavior

**Work state:** MONITOR

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED

E-126 shows the tightened fallback path operating as intended: a nonproductive delegated follow-up was followed by substantial fallback work on a fresh capable peer rather than C's accumulated coordinator context. Continue ordinary-use observation; do not purchase a dedicated synthetic benchmark.

### Exact-turn interruption reconciliation

**Work state:** MONITOR

**Reality:** IMPLEMENTED / REVIEWED / VERIFIED TO SUFFICIENT EVIDENCE

E-127 records the reproduced false interruption, diagnosis, and bounded repair. E-129 adds a normal post-repair continuation that closed by `transaction_settled`. Do not widen the interrupted-only grace or redesign reconciliation absent recurrence.

### I-003 — Provider-side instruction adoption after same-thread profile rebind

**Work state:** MONITOR

**Reality:** NEEDS VERIFICATION / current recurrence not demonstrated

Local rebind mechanics and fail-closed identity behavior are verified. Independent provider-side proof that replacement developer instructions took effect on the resumed same thread remains unproven. Do not spend a dedicated paid test unless ordinary use makes this uncertainty consequential.

### Naturalistic continuation economy

**Work state:** MONITOR

E-086 showed that continuation-economy repair can radically reduce tool-loop replay on a controlled fixture; E-090 showed broader source work can still become expensive; E-129 records a smaller zero-tool relay recurrence. Continue ordinary-use monitoring. Optimize demonstrated expensive patterns rather than purchasing synthetic tests without a concrete recurrence.

## Recently completed programs

Detailed rationale, exact commits, tests, benchmarks, and historical narrative belong in the Decision/Evidence registers and Architecture, not in this volatile work-control file.

| Work | Current disposition | Durable references |
|---|---|---|
| I-025 — PBM v3 one-paste workflow | COMPLETE / IMPLEMENTED / EXACT-HEAD + CONTROLLER-PREFLIGHT VERIFIED / first benchmark-task execution pending after launch-path repair | D-047; E-165–E-166 |
| I-024 — PBM v2 contextual baseline | COMPLETE / IMPLEMENTED / EXACT-HEAD + READ-ONLY PREFLIGHT VERIFIED / first live PBM pending | D-046; E-164 |
| I-023 — PBM (Performance Benchmark) | COMPLETE / IMPLEMENTED / EXACT-HEAD VERIFIED / first live run pending | D-045; E-163 |
| I-021 — Principal-controlled Codex plugin management | COMPLETE / native-host administration selected / no Room bridge | D-043; E-157–E-158; E-162 |
| I-020 — Codex skill integration / Skill Creator | COMPLETE / IMPLEMENTED / VERIFIED | D-042; E-153–E-156 |
| Post-I-019 host-command catalog cleanup | COMPLETE / IMPLEMENTED / VERIFIED | D-041; E-152 |
| I-019 — Status & Tools | COMPLETE / IMPLEMENTED / VERIFIED | E-149–E-152 |
| I-018 — Desktop ↔ Room capability audit | COMPLETE / audit only | E-149 |
| I-017 — dynamic C cognition / exceptional approval | COMPLETE / IMPLEMENTED / VERIFIED | D-039; E-145–E-148 |
| I-016 — Private Principal Channel | COMPLETE / IMPLEMENTED / VERIFIED | D-038; E-143–E-144 |
| Functional acceptance T0–T14 | COMPLETE / all recorded PASS after T8 repair | E-140–E-141 |
| BCTX-1 through BCTX-4 | COMPLETE / IMPLEMENTED / VERIFIED | D-037; E-132–E-139 |
| Continuous-Round naturalistic acceptance | COMPLETE | E-136–E-139 |
| I-015 — task-transaction stabilization | COMPLETE | D-030–D-034; E-092 onward |
| P4 — deterministic Room/agent capabilities | COMPLETE / IMPLEMENTED / VERIFIED | D-022; E-030–E-040 |
| A3 remediation | COMPLETE | E-065–E-088 |

### Common Cause disposition

The Common Cause implementation/repair/verification work is complete and the artifact is verified play-ready (E-125–E-129). Competitive play is **not development work** and is not an active/planned roadmap item. It may begin only if the principal separately authorizes that activity. Continue to use any future ordinary play only as incidental evidence for monitored coordination behavior; do not manufacture benchmark traffic.

## Repository-development hygiene

- canonical source is private GitHub repo `strigoi73-sudo/codex-room`, branch `main`;
- verification should match the changed risk surface: use focused deterministic tests for localized changes; use `verify-fast.cmd` for materially integration-sensitive changes, repository-wide gates, or when focused evidence is insufficient; `verify-full.cmd` remains the exhaustive/manual path;
- GitHub Actions are not the routine verification gate after the documented pre-runner failures;
- exact current refs/working-tree state are live Git/GitHub facts, not maintained prose;
- the complete `data/` tree is runtime/generated state and is ignored by Git;
- superseded open PRs #91 and #121 were closed during the 2026-09-20 roadmap audit;
- old unmerged/superseded remote feature branches may remain as Git history residue; they are not active roadmap work. Remove them only after verifying they are obsolete, and do not treat branch existence as work-state authority.

## Deferred work

Keep these deferred unless new evidence or explicit principal direction reprioritizes them:

- archive indexing/embeddings/broad summarization beyond bounded `HISTORY`;
- automatic CORE model routing (C-controlled D-039 allocation is separate);
- broader deterministic-tooling promotion without demonstrated reuse;
- stronger per-capability OS isolation;
- shareable/redacted exports;
- large-module refactors/storage optimization;
- broader productization/packaging/funding;
- Enterprise workforce features;
- provider-neutral implementation work;
- setup/onboarding wizard;
- blanket Desktop host parity or broad browser/computer-use integration without demonstrated need;
- nonessential UI refinement.

## Open questions

No high-priority conceptual question currently blocks ordinary Codex Room use or development.

Current unresolved questions are feature-local rather than roadmap-global:

- if ordinary use later demonstrates material friction from native-host plugin administration, what exact gap justifies reopening I-021;
- if D-019 is selected again, how should mixed subscription allowance and purchased credits interact;
- if browser/computer use, worktrees, remote execution, attachments, native review, steering, approvals, or other I-022 families are selected, what is the smallest native reuse that preserves Room semantics and execution economics.

I-027 is the current benchmark implementation. Unqualified **Run PBM** resolves to canonical PBM v5. PBM v1–v4 remain available only for historical/reproducibility purposes unless the principal explicitly selects an older version.
