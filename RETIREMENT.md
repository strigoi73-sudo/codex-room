# Codex Room — Retirement Note

**Retired:** 2026-09-27  
**Status:** Final / archival

Codex Room began as an experiment in whether a persistent, inspectable multi-agent organization could provide practical advantages over using Codex directly.

The project progressed far beyond a prototype. It implemented a durable A/B/C organization, transaction-based work state, persistent provenance, recovery behavior, dynamic model allocation, deterministic capabilities, file/image handoff, usage accounting, benchmark harnesses, and a substantial local verification discipline.

The final product question remained:

> Does Codex Room's persistent organization create enough measurable practical value to justify its additional complexity and execution cost?

## What the project learned

The answer from the completed benchmark program was no.

That conclusion was reached in stages rather than assumed.

### PBM v5

PBM compared Codex Desktop and Codex Room as platforms across the same seven-task battery while allowing each platform to use its native organization.

The first paid comparison completed with both platforms VALID and perfect on deterministic correctness:

| Platform | Correctness | Measured tokens | Duration |
|---|---:|---:|---:|
| Desktop | 100 | 371,378 | 292.069 s |
| Room | 100 | 1,473,150 | 628.984 s |

Room used about 3.97× the provider tokens.

A controlled C-only follow-up materially reduced Room overhead, but still used 1.7348× Desktop tokens and took 1.1215× Desktop duration. That showed that peer fan-out was not the only source of the economic gap.

### OUB v1

The first organizational-utility task did not create enough organizational pressure. Both platforms solved the substantive diagnosis, but neither Desktop descendants nor Room peers activated meaningfully. The result was preserved as valid negative evidence, not rerun until a preferred pattern appeared.

### OUB v2

OUB v2 froze three externally authored CooperBench task pairs before measured execution and gave both platforms equivalent starting repositories, the same mission, the same hidden evaluation, and freedom to organize naturally.

The measured Phase 6 results were:

| Task | Desktop features | Room features | Desktop tokens | Room tokens | Room/Desktop tokens | Desktop s | Room s |
|---|---:|---:|---:|---:|---:|---:|---:|
| o2-1 | 1/2 | 0/2 | 759,563 | 967,610 | 1.2739 | 327.708 | 279.727 |
| o2-2 | 2/2 | 2/2 | 863,424 | 922,496 | 1.0684 | 235.405 | 210.307 |
| o2-3 | 1/2 | 0/2 | 517,202 | 607,866 | 1.1753 | 174.594 | 232.315 |

Aggregate:

- Desktop: **4/6** features, **2,140,189** tokens, **737.707 s**
- Room: **2/6** features, **2,497,972** tokens, **722.349 s**
- Room/Desktop token ratio: **1.1672**
- Room/Desktop aggregate measured-duration ratio: **0.9792**
- Desktop native descendants: **0**
- Room peer invocations: **3**
- substantive principal intervention: **0** for both platforms

The important point was not that Room failed to invoke its architecture. It invoked peers on all three tasks. Even with that organization active, the frozen sample did not show a correctness, cost, speed, or human-coordination advantage sufficient to justify the extra system.

## What the conclusion does and does not mean

The retirement decision is intentionally narrow.

It means:

- this implementation did not establish a practical advantage over Codex Desktop in the measurements that mattered to the project;
- additional orchestration complexity was not justified by the demonstrated outcomes;
- continuing development in hope that another feature would eventually reveal the missing advantage would be development by inertia rather than evidence.

It does not mean:

- every multi-agent architecture is inferior;
- no future model/runtime could benefit from persistent organization;
- every Room task will always underperform every Desktop task;
- the engineering work was without value.

The project produced reusable lessons in benchmark design, provenance, deterministic orchestration, context economics, Windows/WSL reliability, provider usage measurement, and the importance of testing whether architectural complexity actually pays for itself.

## Final disposition

Codex Room is retired as an active product.

The repository is preserved as an experimental and educational artifact so others may inspect it, run it, fork it, or reuse ideas from it. Historical benchmark code and maintained project records remain part of the archive.

There is no active roadmap and no promise of compatibility with future Codex releases.

The experiment succeeded in the most important sense: it generated enough evidence to know when to stop.
