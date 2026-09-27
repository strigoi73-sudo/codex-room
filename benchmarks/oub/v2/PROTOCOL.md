# OUB v2 — External-task platform utility protocol

OUB v2 evaluates whether Codex Room's persistent A/B/C organization creates practical utility on externally authored work without prescribing that either platform use multiple agents.

This protocol is the Phase-1 comparison contract for I-028. Task selection, task adaptation, harness changes, and measured model runs occur only in later phases.

## 1. Comparison unit

The comparison unit is the **platform**.

For each frozen task:

- Codex Desktop receives one fresh top-level task rooted at the prepared workspace.
- Codex Room receives one fresh ordinary A/B/C Room rooted at an equivalent prepared workspace.
- Both platforms receive the same task mission, starting repository/workspace content, and completion target.
- Each platform may use its native capabilities and internal organization however it chooses.

The benchmark does not prescribe agent count, role division, speaking order, delegation, review structure, or model-selection sequence.

Desktop may remain one thread or create native descendants. Room may remain C-only or invoke A/B. Those choices are measured product behavior, not validity requirements.

## 2. Initial sample

The initial OUB v2 sample contains **three externally authored tasks**.

All three tasks are selected and frozen before the first measured OUB v2 run. A task is not selected or rejected because it is expected to favor Codex Room, expected to induce peer use, expected to create a particular coordination pattern, or belongs to a preferred difficulty band.

Phase 2 may exclude a candidate only for practical benchmark suitability, such as:

- unavailable or unreasonable local infrastructure;
- missing or unusable upstream grading/tests;
- irreproducible setup;
- licensing/reuse incompatibility;
- execution cost clearly outside the principal's reasonable benchmark budget.

Task diversity is desirable, but the sample is not engineered to guarantee organizational contrast.

Once measured work begins, a frozen task is not replaced because of an unfavorable, uninteresting, or no-peer result. Replacement is allowed only for a demonstrated benchmark-invalidating defect or environment requirement that makes the task unusable as specified.

## 3. Shared mission and task assets

Each platform receives the same frozen mission derived from the external task and equivalent starting assets.

Where an upstream benchmark provides executable tests or an objective grader, OUB v2 uses that upstream outcome contract rather than inventing hidden semantic labels.

Any Codex Room adapter may package, copy, invoke, or normalize the upstream task mechanically, but it must not:

- add Room-specific hints;
- tell either platform how to decompose the work;
- expose hidden answers or gold patches;
- weaken or strengthen the task differently by platform;
- rewrite grading rules after observing a measured outcome.

Exact upstream revision/task identity and the locally frozen task fingerprint are recorded before measurement.

## 4. Principal intervention

After a measured arm starts, the principal provides no substantive guidance, debugging help, task clarification, correction, or organizational direction.

Read-only status inspection is allowed.

A run requiring substantive principal intervention is invalid for platform comparison and is recorded as such rather than silently repaired during measurement.

## 5. Outcome dimensions

OUB v2 reports outcome dimensions separately. It does not compute a composite platform score or overall winner.

For each task and platform, record at least:

### Task outcome

- official/upstream test or grader result;
- completion validity;
- required-artifact presence where applicable.

### Execution cost

- measured provider tokens;
- elapsed measured duration.

### Organization

- Desktop measured root/descendant count;
- Room measured execution count;
- Room A/B peer invocations;
- observed model/reasoning configurations where available.

### Human involvement

- substantive principal intervention count/status;
- invalidation reason, if any.

Additional task-native metrics may be retained when supplied by the upstream benchmark, but they do not replace the shared OUB dimensions.

## 6. Validity

A valid platform arm requires:

- the frozen starting task/workspace;
- the exact shared mission;
- no benchmark-prohibited mutation of supplied task evidence or hidden evaluation assets;
- no substantive principal intervention after launch;
- complete enough usage/provenance data for the shared OUB measurements;
- execution of the frozen official grader/test contract.

A mechanical launcher, harness, fixture-installation, or grading failure that occurs independently of the measured model's substantive work is an infrastructure failure, not a model/platform outcome. Repair the infrastructure before a valid measured comparison.

A substantive model failure, timeout within the declared benchmark boundary, poor result, failure to delegate, excessive delegation, or integration failure is an outcome and must not be relabeled as infrastructure failure.

## 7. Interpretation

The primary I-028 evidence is the **pattern across the three-task sample**, not a single task's result.

More agents, more messages, more executions, more provenance, or greater token spend are not evidence of utility by themselves.

Room utility may be supported when its ordinary organization produces material practical benefit, such as:

- higher objective task correctness;
- avoidance or detection of a consequential defect;
- successful integration where the comparison platform fails;
- comparable task quality with a meaningful reduction in human coordination burden.

Negative utility evidence includes cases where Room's additional organization/cost produces no material benefit or harms the final outcome.

Mixed results are retained as mixed evidence. They may identify task classes where organization helps, hurts, or is irrelevant.

A task on which both platforms solve the work easily, neither platform organizes beyond one primary agent/thread, or the final outcomes are indistinguishable is still a valid observation. It is not automatically discarded as "insufficient organizational pressure."

No result is rerun merely to obtain a more favorable organizational pattern.

## 8. Cost and quality

Correctness and cost remain separate.

A more expensive platform may still demonstrate practical utility if the additional expenditure yields material outcome value. Conversely, equal correctness at materially higher cost is evidence against utility for that observed task.

OUB v2 does not define an arbitrary exchange rate between tokens, time, correctness, and organization.

## 9. Phase boundary

Phase 1 ends when this comparison contract is canonical.

Phase 2 selects the three-task external sample under this contract. Phase 2 does not modify the fairness rules in response to candidate-task characteristics.

No paid OUB v2 model comparison is authorized by Phase 1.
