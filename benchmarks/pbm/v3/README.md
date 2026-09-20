# PBM v3 — one paste per platform

PBM v3 preserves the PBM v2 benchmark workload, graders, quality semantics, contextual snapshots, naturalistic Room cognition, and alternating product order. It changes the **operator protocol** so the principal supplies one initial instruction to Codex Desktop and one initial instruction to a dedicated Codex Room controller.

## Human workflow

Desktop is opened on:

`C:\Codex Room\pbm_desktop_controller`

The single Desktop instruction is:

`Read DRIVER.md and execute it exactly.`

PBM then creates a dedicated controller Room named **PBM v3 Controller — ACTIVE**. The single Room instruction is:

`Read PBM_ROOM_DRIVER.md and execute it exactly.`

Native approval dialogs may still require principal approval. Those approvals are ordinary platform controls and are not additional benchmark prompts.

## Desktop isolation

The Desktop controller is coordination-only and must never solve a benchmark task itself.

For each Desktop arm it:

1. waits until the alternating PBM schedule says Desktop is next;
2. asks deterministic PBM tooling to stage exactly one active fixture and instruction file;
3. uses native Codex task management to create a **fresh separate child task**;
4. omits any model override so the child uses ordinary Desktop behavior;
5. waits for that child task to finish;
6. supplies the exact returned child thread id to deterministic PBM capture/grading;
7. removes the active staged workspace before proceeding.

PBM v3 requires native Desktop task creation/wait/read functionality. If those native tools are unavailable, PBM fails closed before benchmark task execution. **There is no Codex CLI fallback.**

The native task-creation primitive inherits the controller task's working directory. For that reason the controller is opened in a dedicated PBM controller folder, not the repository root. Only the current active task is staged there. Child-task instructions forbid inspection of parent/sibling benchmark state, graders/oracles, prior results, and the Room arm.

## Room isolation

The special PBM controller Room is coordination-only. It launches a deterministic background PBM worker and then does no benchmark reasoning.

The worker follows the same alternating PBM schedule and, when Room is next, creates a **fresh ordinary production Room** for that task, stages the fixture, starts the Round, waits for terminal state, exports it, captures execution economics/model-effort provenance, grades externally, and advances.

Each benchmark Room retains normal D-039 behavior: C may dynamically choose ordinary Luna/Terra/Sol × Low/Medium/High cognition for itself and peer Assignments. PBM records those choices and does not pin them.

## Measurement

PBM v3 retains v2's run-start/run-end and task-pair pre/post contextual snapshots.

Task execution usage remains the primary Desktop-versus-Room comparison. Because v3 adds one controller cognition turn on each platform, the final one-paste report also exposes:

- Desktop task usage;
- Room task usage;
- Desktop controller overhead;
- Room controller overhead;
- all-in Desktop usage;
- all-in Room usage.

Controller overhead is never silently charged to an individual benchmark task.

## Version integrity

PBM v3 inherits the exact frozen v1 task assets. Its benchmark fingerprint also binds the v3 orchestration implementation files listed by the manifest, so changes to one-paste mechanics invalidate the v3 fingerprint rather than silently changing the procedure.

PBM v1 and v2 remain frozen and explicitly reproducible.
