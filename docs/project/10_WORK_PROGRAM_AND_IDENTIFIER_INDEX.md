# Codex Room — Work Program & Identifier Index

**Initialized:** 2026-09-10  
**Purpose:** Stable human-facing legend and cross-reference for short identifiers used across Codex Room planning, maintenance, decisions, evidence, assurance, and prompts.  
**Authority:** Navigation aid only. It does not own current priority or status. Use `06_DEVELOPMENT_CONTROL.md` for current work/status; `05_DECISION_REGISTER.md` for decisions; the Evidence Register (`07_EVIDENCE_REGISTER.md` + `07a_EVIDENCE_REGISTER_CONTINUATION.md`) for evidence; and `08_PRODUCT_VISION.md` for long-range direction.

## 1. Identifier families

| Form | Meaning | Canonical owner | Example |
|---|---|---|---|
| `P#` | Major development / operating-economics phase or roadmap workstream | `06_DEVELOPMENT_CONTROL.md`; long-range direction may also appear in `08_PRODUCT_VISION.md` | `P3` — usage-wall delayed continuation |
| `EF-#` | Engineering Foundation subphase | `06_DEVELOPMENT_CONTROL.md` | `EF-3` — minimal GitHub CI |
| `BCTX-#` | Bounded-context architecture implementation slice | `06_DEVELOPMENT_CONTROL.md`; governing decision in `05_DECISION_REGISTER.md` | `BCTX-1` — Task-bounded continuous lifecycle and coordinator continuity |
| `A#` | Assurance pass | `06_DEVELOPMENT_CONTROL.md`; evidence in the Evidence Register (`07_EVIDENCE_REGISTER.md` + `07a_EVIDENCE_REGISTER_CONTINUATION.md`) | `A2` — Assurance Pass 2 |
| `I-###` | Maintenance issue, observed gap, or item needing verification | `06_DEVELOPMENT_CONTROL.md` | `I-001` — 2,000-event snapshot/export cutoff |
| `D-###` | Settled decision | `05_DECISION_REGISTER.md` | `D-018` — allocate cognition once; execute at the cheapest capable layer |
| `E-###` | Evidence record | Evidence Register (`07` + `07a` continuation) | `E-023` — first minimal GitHub CI run succeeded |
| `[CORE]` | Runtime/codebase change with cross-Room implications | Constitution / Decision Register / Repository & Operations | `[CORE] Engineering Foundation` |
| `[ROOM]` | Change confined to one Room's state, profiles, artifacts, tools, knowledge, objectives, or operating rules | Constitution / Decision Register / Repository & Operations | `[ROOM]` profile adjustment |
| `[CORE + ROOM migration]` | Core capability implemented centrally, followed by Room-specific adoption | Constitution / Decision Register / Repository & Operations | migration of a new Core capability into a Room |

Identifiers name work or records; they do not imply status. Missing numbers do not imply missing current work.

## 2. Established program identifiers

This table preserves names and navigation only. Read Development Control for current state and ordering.

| ID | Title | Owner |
|---|---|---|
| `P0` | Selective invocation | Decision Register / Evidence Register |
| `P1` | Operational token/usage-efficiency doctrine | Decision Register / Evidence Register |
| `P2` | Persistent-context / compaction economics | Evidence Register |
| `P3` | Usage-wall delayed continuation | Decision Register / Evidence Register / Repository & Operations |
| `EF-1` | Reproducible dependency/environment setup | Evidence Register |
| `EF-2` | Canonical full-test command | Evidence Register / Repository & Operations |
| `EF-3` | Minimal GitHub CI | Evidence Register / Repository & Operations |
| `A1` | Assurance Pass 1 | Evidence Register |
| `A2` | Assurance Pass 2 | Evidence Register |
| `A3` | Whole-system housekeeping, efficiency, and operational assurance audit | Development Control / Evidence Register |
| `P4` | Deterministic Room and agent capabilities | Development Control / Product Vision |
| `BCTX-1` | Task-bounded continuous lifecycle and coordinator continuity | Development Control / D-037 |
| `BCTX-2` | Objective-local worker context, direct result return, and compact coordinator status | Development Control / D-037 |
| `BCTX-3` | Worker-context grace/retirement and same-Round bounded HISTORY | Development Control / D-037 |
| `BCTX-4` | Coordinator checkpoint and refresh | Development Control / D-037 |

## 3. Established maintenance identifiers

Issue titles remain useful after resolution, but status belongs only in Development Control.

| ID | Title | Owner |
|---|---|---|
| `I-001` | 2,000-event snapshot/export cutoff | Evidence Register |
| `I-003` | Provider-side instruction adoption after same-thread profile rebind | Development Control |
| `I-004` | README conflicts with settled architecture | Evidence Register (historical) |
| `I-005` | legacy `Agent Personalities.txt` dependency question | Evidence Register (historical) |
| `I-006` | Early-triad default profiles missed D-020 migration | Evidence Register |
| `I-007` | Environment and documentation truth drift | Evidence Register |
| `I-008` | Repository branch hygiene | Evidence Register / Repository & Operations |
| `I-009` | Runtime provenance and maintenance health | Evidence Register / Architecture & Current State |
| `I-010` | Persistent-data operational maintenance | Evidence Register / Repository & Operations |
| `I-011` | Verification-platform and dependency assurance | Evidence Register / Repository & Operations |
| `I-012` | Authorized CORE and cross-Room read inspection | Decision Register / Evidence Register |
| `I-013` | SDK-internal subagent bypass | Evidence Register / Architecture & Current State |
| `I-014` | Deterministic retrieval economy | Evidence Register / Architecture & Current State |
| `I-015` | Task-transaction stabilization redesign | Development Control |
| `I-016` | Private Principal Channel | Development Control / D-038 |
| `I-017` | Dynamic C cognition and Task-scoped exceptional approval | Development Control / D-039 |
| `I-018` | Codex Desktop ↔ Codex Room capability audit | Development Control |
| `I-019` | Human-facing capability visibility | Development Control / E-149 |
| `I-020` | Codex skill integration and Skill Creator adoption | Development Control |
| `I-021` | Principal-controlled Codex plugin management | Development Control |
| `I-022` | Native Codex capability exposure and execution-economics audit | Development Control / E-159 / E-160 |
| `I-023` | PBM (Performance Benchmark) — standardized Codex Room vs Codex Desktop benchmark | Development Control / D-045 |
| `I-024` | PBM v2 contextual baseline — run/task-pair provider usage and environment snapshots | Development Control / D-046 |
| `I-025` | PBM v3 one-paste workflow — one initial instruction per platform with fresh task contexts | Development Control / D-047 |
| `I-026` | PBM v4 common protocol with thin platform adapters — one shared benchmark procedure, one principal initiation per platform, deterministic pairing/comparison | Development Control / D-049 / E-167–E-169 |
| `I-027` | PBM v5 platform-outcome benchmark — equivalent missions with unconstrained native internal orchestration | Development Control / D-050 |

## 4. Decision and evidence identifiers

`D-###` and `E-###` are record identifiers, not phases.

- `D-###` means a **settled decision**. Read the exact decision and any supersession in `05_DECISION_REGISTER.md`.
- `E-###` means an **evidence record**. Read the exact observation, test, measurement, limitations, and evidence date in the single logical Evidence Register spanning `07_EVIDENCE_REGISTER.md` and `07a_EVIDENCE_REGISTER_CONTINUATION.md`.

Use these IDs to point to durable decisions or evidence without copying their full contents. Do not maintain “latest D/E number” here; the owning register is authoritative.

## 5. Status is separate from identifiers

Use the maintained status vocabulary from `00_PACKAGE_INDEX_AND_MAINTENANCE_GUIDE.md`. Never infer status from an identifier or from this index. For current work state, consult Development Control; for implementation/evidence claims, follow the owning architecture/evidence source.

## 6. Non-canonical roadmap shorthand

`P5`–`P8` have appeared in planning discussions as working shorthand for scalability/data integrity, collaboration quality, archive retrieval/context economy, and runtime/model/provider abstraction. They are **not canonical active work-program identifiers** unless deliberately promoted into Development Control. Avoid using them for new work until then.

## 7. Maintenance rule

Keep this file compact and stable. It should answer **“what does this identifier mean and where do I look?”**, not **“what is the current status?”**

When an identifier is added, renamed, retired, or materially re-scoped:

1. update the owning document first;
2. update this index only enough to preserve navigation;
3. never mirror current priorities, blockers, issue states, temporary budget timing, current repository HEAD, or active sequencing here.
