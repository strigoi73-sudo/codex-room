# PBM v1

PBM v1 is the first standardized naturalistic comparison of Codex Desktop and Codex Room.

## Standard suite

PBM v1 contains eight paired tasks, ordered from small mechanical work through multi-file implementation and repair. Each arm receives the same task prompt and fixture bytes. Task-specific graders are outside the task workspace and run only after the product arm finishes.

The eight task categories are:

1. trivial mechanical change;
2. bounded repository investigation;
3. localized bug repair;
4. small feature implementation;
5. ambiguous state-mutation bug diagnosis and repair;
6. evidence-backed constrained design choice;
7. specification audit and repair;
8. integrated multi-file CLI feature.

## Naturalistic comparison

PBM v1's canonical mode is **naturalistic**.

- Codex Desktop runs as native Codex Desktop in a fresh local chat opened on the prepared Desktop workspace.
- Codex Room runs as a fresh production Room with C as the starter and no required contributors. C may invoke A/B only when its normal coordination policy judges that worthwhile.
- Do not force Desktop and Room into identical internal orchestration. PBM v1 measures the products as designed.
- Do not provide substantive human hints, corrections, or implementation guidance after a task starts. Ordinary permission/safety confirmations are allowed when the product requires them.
- Do not retry a failed benchmark task inside the same run merely to improve its score. A later replication is a separate run.

## Isolation and oracle rule

Both prompts receive the same benchmark rule: work only from the task workspace and task prompt. Neither arm may inspect PBM manifests, graders/oracles, the other arm's workspace/results, or earlier PBM results.

The benchmark harness and graders are intentionally not copied into either task workspace.

## Paired order

A PBM run alternates which product executes first:

- odd-numbered tasks: Desktop first;
- even-numbered tasks: Room first.

Both arms may be prepared before either arm executes. Preparation itself must not purchase model cognition.

## Quality and usage

Every task receives a deterministic 0–100 quality score plus pass/fail checks. Usage is reported independently; a cheaper failed result is not treated as equivalent to a correct result.

Desktop usage comes from the fresh top-level Codex rollout whose exact working directory matches the prepared Desktop workspace. Room usage is aggregated from durable `execution_economics` events and Room execution provenance.

PBM reports preserve at least:

- raw input, cached-input, output, reasoning-output, and total-token usage when available;
- provider-response/tool-call counts when available;
- Room execution count, per-agent execution distribution, failed tool calls, and model/effort provenance;
- elapsed execution time where mechanically recoverable;
- deterministic quality score and pass/fail;
- Room/Desktop raw-token ratio for paired tasks.

The subscription/weekly usage meter is corroborating evidence only and is not PBM's primary accounting source.

## Running PBM

Prepare/run each arm with the dedicated scripts at repository root:

`pbm-desktop.ps1`
`pbm-room.ps1`

The scripts refresh the partial PBM report after completed arms. Run metadata and results are written under ignored `output/pbm/runs/<run-id>/`.

A run is not a historical PBM v1 result until all eight task pairs are complete and the exact benchmark fingerprint is preserved in the run records.
