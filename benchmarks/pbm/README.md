# PBM — Performance Benchmark

PBM is the canonical versioned Codex Room versus Codex Desktop performance benchmark.

**PBM v4 is the canonical live benchmark.** `benchmarks/pbm/CURRENT` resolves to `v4`.

The principal phrase **Run PBM** means: load this file, resolve the version named by `CURRENT`, and follow that version's canonical protocol without redesigning the benchmark.

PBM v4 uses one common protocol with thin platform-native adapters:

- one principal controller initiation on Codex Desktop and one on Codex Room;
- one fresh measured execution per platform over the same frozen seven-task cross-domain battery;
- equivalent starting fixtures, task prompts, and deterministic task-specific graders;
- native platform organization is allowed, so Desktop and Room may coordinate the work differently;
- automatic pairing, capture, grading, comparison, and evidence bundling;
- explicit **VALID / INVALID / FAILED** execution classification;
- whole-battery token and duration measurement plus per-task correctness;
- no fabricated per-task token attribution from a continuous execution;
- no Codex CLI substitution for the measured Desktop arm;
- no principal choreography between the two measured platform executions.

The retained v4 task battery covers:

1. mechanical change;
2. bounded investigation;
3. localized bug repair;
4. small feature work;
5. state-mutation repair;
6. constrained design;
7. integrated CLI work.

The known-inconsistent historical `t07-spec-repair` task is excluded from v4. Historical PBM v1-v3 assets remain frozen and explicitly reproducible by version where their historical procedures support it; PBM v3 must not be used for another live performance comparison.

Before promotion, v4 passed deterministic battery/reference and repository verification plus a real merged-bytes common-protocol canary in which both Desktop and Room completed **VALID / 100**, fingerprints matched, the pair was comparable, automatic finalization completed, and the active pair cleared.

For v4 operating instructions, read:

- `benchmarks/pbm/v4/README.md`
- `benchmarks/pbm/v4/PROTOCOL.md`
- Desktop adapter: `pbm_desktop_controller/V4_PROTOCOL.md`
- Room adapter: persistent `PBM v4 Room Runner` with staged `PBM_ROOM_PROTOCOL.md`

`codex_room/pbm.py` remains the shared deterministic manifest, fixture, grading, usage, context-snapshot, and report layer.

Do not change an existing version's tasks, prompts, fixtures, graders, controls, or scoring semantics after benchmark results have been recorded. Material benchmark changes require a new version.
