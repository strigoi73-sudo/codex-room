# Codex Room GPT Project — Package Index & Maintenance Guide

**Package initialized:** 2026-09-08  
**Purpose:** Maintain a compact, durable knowledge base for future ChatGPT work on Codex Room.  
**Freshness principle:** Every file is a maintained synthesis with a defined scope. Newer direct evidence or later explicit decisions may supersede dated material.

## 1. Package contents

| File | Role | Expected volatility |
|---|---|---|
| `02_CODEX_ROOM_CHARTER.md` | System identity, purpose, human authority, Personal architecture, and high-level design philosophy. | Very low |
| `03_CONSTITUTION_AND_INSTITUTIONAL_RULES.md` | Ratified agent Constitution and durable cross-Room governance rules. | Very low |
| `04_ARCHITECTURE_AND_CURRENT_STATE.md` | Best current synthesis of implemented behavior and system structure. | Moderate |
| `05_DECISION_REGISTER.md` | Settled design/product decisions and later supersessions. | Moderate |
| `06_DEVELOPMENT_CONTROL.md` | Current focus, priorities, known issues, planned work, and open questions. | High |
| `07_EVIDENCE_REGISTER.md` | Compact record of measurements, tests, observations, and their limits. | Moderate |
| `08_PRODUCT_VISION.md` | Longer-range direction and deliberately deferred capabilities. | Low |
| `09_REPOSITORY_AND_OPERATIONS_REFERENCE.md` | Dated repository map, maintenance boundaries, recovery notes, and verification conventions. | Moderate |
| `10_WORK_PROGRAM_AND_IDENTIFIER_INDEX.md` | Stable human-facing legend and cross-reference for phase, issue, decision, evidence, assurance, and scope identifiers. It does not own current status. | Low |

**Project instructions:** the live Codex Room GPT Project custom-instructions configuration is authoritative and is intentionally **not duplicated as a maintained Project source**. If a handoff/export ever needs a copy, capture it as a dated snapshot rather than maintaining a second authoritative version.

**Manifest policy:** `MANIFEST.md` is **not a live maintained Project source**. Generate a manifest only for a deliberate export, handoff, or archival package where exact package inventory and hashes are useful.

**Filename convention:** preserve the leading canonical document number (for example `06_` or `10_`). Automatic trailing download/upload suffixes such as ` (1)` or ` (3)` before the extension are incidental and do not change logical document identity. Keep only one active Project source for each logical document.

## 2. How to resolve disagreements

Do not assign one universal authority order to all project material. Resolve conflicts according to the kind of claim being made and its freshness.

- **What the software currently does:** prefer the freshest relevant source code, current tests, runtime evidence, and current repository inspection.
- **What Codex Room is intended or permitted to do:** prefer the current ratified Constitution, Charter where applicable, and later explicit decisions recorded in the Decision Register.
- **Best current implementation summary:** use `04_ARCHITECTURE_AND_CURRENT_STATE.md`, then verify volatile or consequential claims against fresher technical evidence when available.
- **What should be worked on now:** use the latest `06_DEVELOPMENT_CONTROL.md`.
- **Why an important claim is believed:** use `07_EVIDENCE_REGISTER.md` and, when needed, the external artifact it cites.
- **Longer-range direction:** use `08_PRODUCT_VISION.md`; do not infer that vision items are implemented or committed.
- **What a shorthand identifier such as `P3`, `EF-2`, `I-004`, `D-018`, or `E-023` means:** use `10_WORK_PROGRAM_AND_IDENTIFIER_INDEX.md`, then follow its pointer to the owning source for current detail/status.

When implementation and institutional intent disagree, record the discrepancy. Do not silently rewrite one to match the other.

## 3. Status vocabulary

Keep **work state**, **reality status**, and **evidence qualification** separate. Do not collapse unlike concepts into one generic `Type` or `Status` field.

### 3.1 Work state

Use primarily in **Development Control**:

- **PLANNED** — identified/authorized work that has not started.
- **IN PROGRESS** — active work is underway.
- **COMPLETE** — the bounded work is finished. Monitoring or later follow-up may still be noted separately.
- **DEFERRED** — intentionally postponed until a later condition, date, or decision.
- **MONITOR** — no active implementation is required; watch behavior/evidence before deciding whether more work is needed.

### 3.2 Reality status

Use for claims about implementation, intended behavior, or demonstrated problems:

- **IMPLEMENTED** — the capability/change is shown to exist in the relevant version/system.
- **DECIDED / NOT IMPLEMENTED** — settled intent that has not yet been shown implemented.
- **EXPLORATORY** — proposed, hypothetical, or under investigation.
- **OBSERVED ISSUE** — problematic behavior supported by evidence and not yet shown fixed.
- **SUPERSEDED** — retained only for historical explanation because later state/intent governs.

### 3.3 Evidence qualification

Use as a qualifier on a reality claim when useful:

- **VERIFIED** — supported by current or exact-version evidence appropriate to the claim.
- **HISTORICALLY VERIFIED** — passed verification at a stated earlier time/version; later change may require re-verification.
- **NEEDS VERIFICATION** — current applicability or correctness has not been adequately established.

### 3.4 Domain-specific vocabularies

Some registers have their own local labels. Do not mix them into the general axes above:

- Decision Register: **ACTIVE / SUPERSEDED** describes whether a decision currently governs.
- Assurance assessment: **GOOD / PARTIAL / GAP / NEEDS VERIFICATION / NOT RELEVANT YET** are assessment ratings, not general work states.
- Dependency/readiness notes such as **SATISFIED** are descriptive fields, not statuses.

Where multiple concepts apply, label them explicitly, for example: `Work state: COMPLETE`, `Follow-up: MONITOR`, `Reality / evidence: IMPLEMENTED / HISTORICALLY VERIFIED`.

## 4. Maintenance discipline

After substantial work, update only the files materially affected.

- Implementation changed → update **Architecture & Current State**.
- A design/product decision became settled or was superseded → update **Decision Register**.
- A test, benchmark, measurement, or important observation changed the evidentiary picture → update **Evidence Register**.
- Priority, blocker, issue, planned work, or open question changed → update **Development Control**.
- A foundational purpose or durable governance rule changed → deliberately update the **Charter** or **Constitution & Institutional Rules** and record the decision.
- Long-range product direction changed → update **Product Vision**.
- Repository layout, operational recovery, or maintenance workflow changed → update **Repository & Operations Reference**.
- Work-program identifier added, renamed, retired, or materially re-scoped → update **Work Program & Identifier Index** after updating the owning source.

Use explicit dates for volatile claims. Remove resolved questions from Development Control after their resolution is recorded elsewhere as appropriate.

**Repository-state boundary:** maintained Project sources track the **meaning** of repository changes, not mechanically changing repository state. Git/GitHub are authoritative for current HEAD, refs, diffs, commit history, pull requests, CI runs, and hosted verification; local Git is authoritative for the local working tree and local ref state. Do not update Project sources merely because a commit SHA or CI run changed. Preserve exact commits, test counts, or run IDs in the Evidence Register only when they materially support a durable claim, closeout, decision, or assurance result.

**Volatile-state ownership:** `06_DEVELOPMENT_CONTROL.md` is the sole maintained owner of current priority, active work/issue status, blockers, open questions, and temporary budget timing. `04`, `09`, and `10` may retain dated historical evidence or stable structural references, but should not mirror the live work queue, current-status tables, or exact current repository HEAD.

## 5. Context economy

The Project package is designed to preserve continuity without turning active context into an archive.

Keep large or episodic material outside the maintained core, including:

- Room JSON exports;
- full repository ZIP snapshots;
- raw chat transcripts;
- historical prompt collections;
- large benchmark dumps;
- one-off implementation reports;
- backups, caches, `.venv`, `.git` objects, and generated runtime debris.

Reference those artifacts by name and date when they matter. Inspect them narrowly for the question at hand.

## 6. External reference baseline used to initialize this package

The initial package was synthesized from the working handoff bundle dated 2026-09-08. The large repository snapshots `Codex Room 1.zip` and `Codex Room 2.zip` remain separate reference artifacts and were intentionally excluded.

Any newer live source, runtime export, test result, explicit user decision, or later maintained package revision should be preferred within its relevant domain.
