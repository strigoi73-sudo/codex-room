# OUB harnesses

OUB uses versioned harnesses. Historical OUB v1 remains reproducible; OUB v2 is the active I-028 development path but is not promoted through `benchmarks/oub/CURRENT` until its mechanical dry run passes.

## OUB v1 — historical O1 harness

OUB v1 measures one naturalistic Desktop arm and one naturalistic Codex Room arm against the frozen O1 forensic asset.

Operator entrypoint: `./oub-v1.ps1`.

The Room arm starts automatically after preparation. Desktop remains native: the harness discovers the fresh top-level rollout by prepared workspace and includes all native descendants in measured usage.

## OUB v2 — external coding-task harness

OUB v2 measures one frozen CooperBench feature pair at a time.

Operator entrypoint: `./oub-v2.ps1`.

Supported task IDs are:

- `o2-1` — LlamaIndex task 18813, features 2 + 5;
- `o2-2` — Typst task 6554, features 4 + 9;
- `o2-3` — dirty-equals task 43, features 3 + 7.

For a measured task:

1. start Codex Room normally;
2. run `./oub-v2.ps1 prepare --task-id <TASK_ID>`;
3. open exactly one fresh top-level Codex Desktop task rooted at the printed `desktop_workspace`;
4. send the printed `desktop_instruction` exactly once;
5. do not provide substantive guidance to either measured arm;
6. use `./oub-v2.ps1 status` for read-only progress inspection;
7. after both arms finish, the harness grades each finished implementation against the exact selected upstream CooperBench feature tests and writes comparison JSON/Markdown plus an evidence ZIP.

The Room arm starts automatically in measured mode. Desktop may use native descendants. Room may remain C-only or invoke A/B. Neither behavior is required.

### Mechanical-only preparation

Phase 5 uses:

`./oub-v2.ps1 prepare --task-id <TASK_ID> --no-start`

This creates equivalent Desktop and Room workspaces and a prepared Room round but starts no Desktop task and no Room cognition. The run can then be inspected and aborted mechanically.

### Starting workspace

For both platforms the harness:

- materializes the exact frozen upstream base commit;
- writes the same generated `BENCHMARK.md` containing the two selected public feature specifications;
- excludes only harness files `BENCHMARK.md` and `OUB_COMPLETE.json` from the task repository's Git status;
- records starting HEAD, tree, and mission SHA-256;
- does not place hidden tests, gold patches, combined patches, or prior benchmark results in the measured workspace.

### Completion

After implementation and self-verification, each platform creates:

`OUB_COMPLETE.json`

with exactly:

`{"status":"complete"}`

The marker is only a lifecycle signal. Correctness is determined separately by the upstream test contract.

### Grading

The harness grades only after measured work ends. It:

- captures the candidate change relative to the frozen base;
- constructs an isolated WSL grading clone;
- replays the candidate change;
- applies one exact selected CooperBench test patch at a time;
- runs the frozen task-specific test target;
- reports feature-level pass/fail with no composite score.

The measured workspace itself is not mutated by grading.

### Measurement

OUB v2 reports separately:

- feature-test correctness;
- provider tokens;
- elapsed measured duration;
- Desktop root/descendant count;
- Room execution/peer-invocation count;
- tool calls;
- Room model/reasoning configurations and other model provenance where available;
- principal intervention/validity state.

No overall winner score is computed.

## Common commands

Historical v1:

- `./oub-v1.ps1 audit`
- `./oub-v1.ps1 prepare`
- `./oub-v1.ps1 status [--run-id RUN_ID]`
- `./oub-v1.ps1 abort [--run-id RUN_ID]`
- `./oub-v1.ps1 bundle --run-id RUN_ID`

Explicit v2:

- `./oub-v2.ps1 audit`
- `./oub-v2.ps1 prepare --task-id o2-1 [--no-start]`
- `./oub-v2.ps1 grade --task-id o2-1 --workspace <PATH>`
- `./oub-v2.ps1 status [--run-id RUN_ID]`
- `./oub-v2.ps1 abort [--run-id RUN_ID]`
- `./oub-v2.ps1 bundle --run-id RUN_ID`
