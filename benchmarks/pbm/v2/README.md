# PBM v2

PBM v2 preserves the **same eight task prompts, fixtures, graders, task order, and naturalistic product comparison as PBM v1**. It changes the measurement protocol by adding standardized contextual baseline snapshots.

## Asset inheritance

PBM v2 references the frozen PBM v1 task assets rather than copying them. The v2 benchmark fingerprint covers both:

- the PBM v2 protocol/manifest bytes; and
- every file under the referenced frozen v1 asset version.

A material change to either source changes the v2 fingerprint.

## Context snapshot protocol

PBM v2 captures deterministic, non-model context snapshots at these boundaries:

1. **run-start** — before the first benchmark task executes;
2. **task-pair pre** — before either Desktop or Room executes that task pair;
3. **task-pair post** — after both Desktop and Room results for that pair exist;
4. **run-end** — after all eight task pairs are complete.

The first arm prepared for a task pair creates the pre-pair snapshot. The second completed arm creates the post-pair snapshot. Snapshot creation does not invoke a model turn.

Snapshots are stored under:

`output/pbm/runs/<run-id>/context/`

## Snapshot contents

When available, each snapshot records:

- timestamp and benchmark version/fingerprint;
- canonical repository HEAD, branch/detached state, and working-tree cleanliness;
- OS/platform, Python version, CPU count, free disk space, and installed `openai-codex` package version;
- pinned native Codex/App Server runtime identity and authenticated account-type metadata after sensitive identity fields are removed;
- native `account/rateLimits/read` response;
- native `account/usage/read` response;
- native base model/reasoning/sandbox/approval/web-search configuration without Room overrides;
- Room-effective model/reasoning/sandbox/approval/web-search configuration with the actual Room overrides applied;
- safe inherited Room tool inventory for web search, skills, MCP servers, apps, and plugins;
- Codex Room's configured default model and reasoning effort.

Sensitive account identity/credential fields are stripped before persistence. If a native context read is unavailable, PBM records that fact and the error type rather than failing or fabricating a value.

## Accounting semantics

PBM v2 preserves PBM v1's primary performance accounting:

- native Desktop rollout usage;
- Codex Room durable execution-economics usage;
- deterministic task quality graders;
- elapsed time and tool/execution provenance.

Provider account/rate-limit snapshots are **contextual/corroborating evidence only**. They help interpret allowance consumption, resets, spend-control/credit state, or provider-side anomalies, but they do not replace per-arm rollout/execution accounting.

## Interpretation

The standard report includes snapshot availability and labels. The complete sanitized snapshot JSON remains available beside the run for deeper interpretation.

PBM v1 remains immutable and may still be reproduced explicitly as v1. The unqualified **Run PBM** invocation resolves `benchmarks/pbm/CURRENT`, which points to the currently canonical version.
