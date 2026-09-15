# Codex Room — Work Program & Identifier Index

**Initialized:** 2026-09-10  
**Purpose:** Stable human-facing legend and cross-reference for short identifiers used across Codex Room planning, maintenance, decisions, evidence, assurance, and prompts.  
**Authority:** Navigation aid only. It does not own current priority or status. Use `06_DEVELOPMENT_CONTROL.md` for current work/status; `05_DECISION_REGISTER.md` for decisions; `07_EVIDENCE_REGISTER.md` for evidence; and `08_PRODUCT_VISION.md` for long-range direction.

## 1. Identifier families

| Form | Meaning | Canonical owner | Example |
|---|---|---|---|
| `P#` | Major development / operating-economics phase or roadmap workstream | `06_DEVELOPMENT_CONTROL.md`; long-range direction may also appear in `08_PRODUCT_VISION.md` | `P3` — usage-wall delayed continuation |
| `EF-#` | Engineering Foundation subphase | `06_DEVELOPMENT_CONTROL.md` | `EF-3` — minimal GitHub CI |
| `A#` | Assurance pass | `06_DEVELOPMENT_CONTROL.md`; evidence in `07_EVIDENCE_REGISTER.md` | `A2` — Assurance Pass 2 |
| `I-###` | Maintenance issue, observed gap, or item needing verification | `06_DEVELOPMENT_CONTROL.md` | `I-001` — 2,000-event snapshot/export cutoff |
| `D-###` | Settled decision | `05_DECISION_REGISTER.md` | `D-018` — allocate cognition once; execute at the cheapest capable layer |
| `E-###` | Evidence record | `07_EVIDENCE_REGISTER.md` | `E-023` — first minimal GitHub CI run succeeded |
| `[CORE]` | Runtime/codebase change with cross-Room implications | Constitution / Decision Register / Repository & Operations | `[CORE] Engineering Foundation` |
| `[ROOM]` | Change confined to one Room's state, profiles, artifacts, tools, knowledge, objectives, or operating rules | Constitution / Decision Register / Repository & Operations | `[ROOM]` profile adjustment |
| `[CORE + ROOM migration]` | Core capability implemented centrally, followed by Room-specific adoption | Constitution / Decision Register / Repository & Operations | migration of a new Core capability into a Room |

Identifiers name work or records; they do not imply status. Missing numbers do not imply missing current work.

## 2. Established program identifiers

This table preserves names and navigation only. Read Development Control for current state and ordering.

| ID | Title | Owner |
|---|---|---|
| `P0` | Selective invocation | Development Control |
| `P1` | Operational token/usage-efficiency doctrine | Development Control |
| `P2` | Persistent-context / compaction economics | Development Control |
| `P3` | Usage-wall delayed continuation | Development Control |
| `EF-1` | Reproducible dependency/environment setup | Development Control |
| `EF-2` | Canonical full-test command | Development Control |
| `EF-3` | Minimal GitHub CI | Development Control |
| `A1` | Assurance Pass 1 | Development Control / Evidence Register |
| `A2` | Assurance Pass 2 | Development Control / Evidence Register |
| `A3` | Whole-system housekeeping, efficiency, and operational assurance audit | Development Control / Evidence Register |
| `P4` | Deterministic Room and agent capabilities | Development Control / Product Vision |

## 3. Established maintenance identifiers

Issue titles remain useful after resolution, but status belongs only in Development Control.

| ID | Title | Owner |
|---|---|---|
| `I-001` | 2,000-event snapshot/export cutoff | Development Control |
| `I-003` | B SDK-thread/profile continuity residue | Development Control |
| `I-004` | README conflicts with settled architecture | Development Control / historical evidence after closure |
| `I-005` | legacy `Agent Personalities.txt` dependency question | Development Control / historical evidence after closure |
| `I-006` | Early-triad default profiles missed D-020 migration | Development Control |
| `I-007` | Environment and documentation truth drift | Development Control |
| `I-008` | Repository branch hygiene | Development Control |
| `I-009` | Runtime provenance and maintenance health | Development Control |
| `I-010` | Persistent-data operational maintenance | Development Control |
| `I-011` | Verification-platform and dependency assurance | Development Control |
| `I-012` | Authorized CORE and cross-Room read inspection | Development Control |

## 4. Decision and evidence identifiers

`D-###` and `E-###` are record identifiers, not phases.

- `D-###` means a **settled decision**. Read the exact decision and any supersession in `05_DECISION_REGISTER.md`.
- `E-###` means an **evidence record**. Read the exact observation, test, measurement, limitations, and evidence date in `07_EVIDENCE_REGISTER.md`.

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
