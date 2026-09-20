# Codex Room — Development Control

**Last updated:** 2026-09-20
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** No feature implementation is currently selected. I-021 — Principal-controlled Codex plugin management — is **COMPLETE** after Stage B selected the native Codex/ChatGPT administration path; no Room-side mutation bridge is required under current evidence. I-022 remains **COMPLETE / VERIFIED AS AN AUDIT** through E-159/E-160.
- **What just changed?** D-043 / E-162 resolve I-021: the principal will manage plugin install/enable/disable through native Codex/ChatGPT plugin surfaces, while Codex Room continues to inherit, inspect, and use the resulting plugin/skill/MCP/app state. No runtime code or plugin state changed in this closeout.
- **Verification state:** E-157/E-158 establish the exact Codex 0.154 plugin contracts and the localhost authority limitation; E-162 verifies the native human-controlled plugin surface and current Room inheritance/visibility boundary. Current implementation claims remain owned by Architecture & Current State plus their exact evidence.
- **What is next?** Principal selection or ordinary use. A future development item should arise from demonstrated friction or explicit principal choice rather than from I-021/I-022 automatically advancing a queue.
- **What is blocked?** No high-priority conceptual blocker prevents ordinary use or further development. Individual deferred items retain their own gates.
- **What are we deliberately not doing?** No Room-local plugin mutation endpoint, principal-proof security subsystem solely for plugin administration, generic config editor, copied marketplace/plugin manager, built-in Codex subagents, autonomous fan-out, automatic model router, or speculative host-parity project.

## Current development state

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
- routine change verification uses `verify-fast.cmd`; `verify-full.cmd` is the exhaustive/manual path;
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

Until the principal selects a direction, **there is no default next feature**.
