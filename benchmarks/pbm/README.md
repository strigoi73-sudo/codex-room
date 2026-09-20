# PBM — Performance Benchmark

PBM is the canonical versioned Codex Room versus Codex Desktop performance benchmark.

The current canonical version is resolved from `CURRENT`. PBM v2 adds standardized run/task-pair context snapshots while preserving v1's eight task assets and primary performance accounting.

The principal phrase **Run PBM** means: load this file, resolve the version named by `CURRENT`, and follow that version's protocol without redesigning the benchmark.

Execution is deliberately separated:

- `pbm-desktop.ps1` owns Desktop-arm setup and Desktop rollout capture. The actual model work must occur in a fresh native Codex Desktop chat opened on the prepared workspace.
- `pbm-room.ps1` owns Room-arm setup, fixture staging, Room start/wait/export, and Room result capture.
- `codex_room/pbm.py` is shared deterministic machinery for manifests, fixture materialization, grading, usage normalization, context checkpoints, and reports. It does not replace either product arm.
- PBM v2 context snapshots capture read-only provider rate-limit/account-usage state and environment/capability provenance before/after the run and each task pair; those snapshots are corroborating context, not a replacement for rollout/Room execution accounting.

Do not change an existing version's tasks, prompts, fixtures, graders, controls, or scoring semantics after benchmark results have been recorded. Material benchmark changes require a new version.
