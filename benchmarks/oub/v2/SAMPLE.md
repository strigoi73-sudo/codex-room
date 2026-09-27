# OUB v2 — Frozen external task sample

**I-028 phase:** 2 — External Task Sample  
**Status:** FROZEN FOR PHASE 3 VALIDATION  
**Phase-1 contract:** `e608f08bf0ab24e33f3d67293913e1dcaf4223df`

## Source

The initial OUB v2 sample is drawn from the published CooperBench `flash` subset at exact upstream repository revision:

`cooperbench/CooperBench@63b9d44d9f39a02fccf5bf0052db48a917a011fd`

The frozen subset file is `dataset/subsets/flash.json`, which declares 50 feature pairs across 20 tasks and 11 repositories. CooperBench and its dataset identify the benchmark as MIT-licensed.

No candidate was excluded before selection.

## Selection rule

To avoid hand-selecting tasks that look favorable to Codex Room, Phase 2 uses a deterministic draw over all 50 frozen flash pairs.

For every pair, form this exact UTF-8 string:

`<phase1_contract_commit>|<repo>|<task_id>|<feature1>,<feature2>`

Compute SHA-256, sort all 50 pairs by the lowercase hexadecimal digest in ascending lexicographic order, and select the first three.

The selection seed is therefore the already-canonical Phase-1 contract merge commit, not a task characteristic observed after inspecting candidate behavior.

## Frozen sample

### O2-1 — LlamaIndex task 18813, features 2 + 5

- selection digest: `08df8e29812980335c86738471d40ec7e3b77d80db388356de7dede11b91bd64`
- upstream project: `run-llama/llama_index`
- base commit: `5eca4973cef04eca5d817d3e1515c8cbe7d1cf9e`
- feature 2: **Add `max_bytes` limit to resolve methods for content blocks**
- feature 5: **Add Progress Callback Hook to Audio Resolution for Byte Tracking**
- upstream task path: `dataset/llama_index_task/task18813`

Both selected feature specifications modify the task's LlamaIndex content-block resolution surface. This description is recorded only to identify the upstream task; it was not used as a selection criterion.

### O2-2 — Typst task 6554, features 4 + 9

- selection digest: `0e4ecde99af0eb3a68046c3a7c9c16162ab3656918e5ea28895b694c8ee2abdb`
- upstream project: `typst/typst`
- base commit: `b8034a343831e8609aec2ec81eb7eeda57aa5d81`
- feature 4: **Add `repeat` parameter to `str.first` and `str.last`**
- feature 9: **Add `strip` parameter to `str.first` and `str.last`**
- upstream task path: `dataset/typst_task/task6554`

The upstream task provides a Rust-based Docker environment and executable test harness. That environment is not yet accepted as locally usable for OUB v2; Phase 3 owns that validation.

### O2-3 — dirty-equals task 43, features 3 + 7

- selection digest: `27765789b34219244172387cb103979b1a065b61a63b5b195e07334d6ee98c30`
- upstream project: `samuelcolvin/dirty-equals`
- base commit: `593bcccf738ab8b724d7cb860881d74344171f5f`
- feature 3: **Add IsEmail validator class for email address validation with optional domain filtering**
- feature 7: **Add IsHash validator for cryptographic hash value validation**
- upstream task path: `dataset/samuelcolvin_dirty_equals_task/task43`

The upstream task provides a Python-based Docker environment and executable test harness. Phase 3 owns local reproducibility and oracle validation.

## Phase-2 boundary

This file freezes task identity only.

Phase 2 does **not**:

- adapt the tasks into the OUB harness;
- execute CooperBench gold/oracle patches locally;
- prove that Docker/build/test dependencies work on the principal's machine;
- run Desktop or Codex Room models;
- replace a selected task because it looks easy, difficult, low-contrast, or unfavorable.

Phase 3 performs the deterministic sanity check against this frozen sample. If a selected task is genuinely unusable because of a benchmark-invalidating defect or an environment requirement that cannot reasonably be satisfied, replacement must be recorded explicitly under the Phase-1 contract rather than silently resampling.
