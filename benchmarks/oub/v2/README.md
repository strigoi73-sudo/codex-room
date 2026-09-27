# OUB v2 — External-task platform utility sample

OUB v2 is the I-028 external-task comparison defined by `PROTOCOL.md`.

The frozen sample is defined by `SAMPLE.md` / `sample.json`. Phase 3 established that all six selected CooperBench feature tests reject their untouched base and pass the frozen combined oracle.

## Phase-4 harness boundary

The v2 harness prepares one selected task pair at a time.

For each platform arm it:

- materializes the exact frozen upstream repository commit;
- writes the same generated `BENCHMARK.md` containing only the two public feature specifications plus a mechanical completion-marker requirement;
- does **not** copy hidden tests, gold patches, combined patches, or the other platform's workspace into the measured workspace;
- records the exact starting repository commit/tree and mission SHA-256;
- lets Desktop or Room organize the task naturally;
- measures provider usage, duration, descendants/peer invocations, and available model-allocation provenance;
- grades the finished implementation only after measured work, using the copied exact upstream CooperBench test patches in an isolated WSL grading clone;
- reports feature-level pass/fail, cost, duration, organization, and intervention separately, with no composite winner score.

The public mission paste remains:

`Read BENCHMARK.md and execute it exactly. Do not ask me questions. When complete, stop.`

The task's `BENCHMARK.md` instructs the platform to create `OUB_COMPLETE.json` with `{"status":"complete"}` after implementation and self-verification. The marker is a harness completion signal, not part of CooperBench grading.

OUB v2 is invoked explicitly through `oub-v2.ps1`. The repository `CURRENT` pointer remains on v1 until the v2 mechanical dry-run gate is complete.
