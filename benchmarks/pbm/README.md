# PBM — Performance Benchmark

PBM is the canonical versioned Codex Room versus Codex Desktop performance benchmark.

The current canonical version is resolved from `CURRENT`. PBM v3 preserves the frozen eight-task workload and v2 contextual snapshots while changing the operator workflow to one initial instruction in Codex Desktop and one in a dedicated Codex Room controller.

The principal phrase **Run PBM** means: load this file, resolve the version named by `CURRENT`, and follow that version's protocol without redesigning the benchmark.

Execution is deliberately separated:

- PBM v1/v2 retain the original arm-by-arm scripts for explicit historical reproduction.
- PBM v3 uses `pbm_desktop_controller/DRIVER.md` plus deterministic `codex_room/pbm_onepaste*.py` orchestration. Desktop benchmark work still occurs in fresh native Codex Desktop child tasks; Room benchmark work still occurs in fresh ordinary Codex Rooms.
- There is no Codex CLI substitution for the Desktop arm. If native separate-task management is unavailable, v3 fails closed.
- `codex_room/pbm.py` remains the shared deterministic manifest, fixture, grading, usage, context-snapshot, and report layer.
- PBM v2/v3 context snapshots capture read-only provider rate-limit/account-usage state and environment/capability provenance before/after the run and each task pair; those snapshots are corroborating context, not a replacement for rollout/Room execution accounting.

Do not change an existing version's tasks, prompts, fixtures, graders, controls, or scoring semantics after benchmark results have been recorded. Material benchmark changes require a new version.
