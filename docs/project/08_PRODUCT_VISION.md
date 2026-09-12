# Codex Room — Product Vision

**Initialized:** 2026-09-08  
**Scope:** Longer-range direction, product philosophy, and deliberately deferred capability space.  
**Freshness:** Vision expresses direction. It does not establish current implementation or a committed delivery schedule.

## 1. Product idea

Codex Room is intended to become a general-purpose persistent AI organization that can help a human principal transform a rudimentary desire, problem, or intention into an organized, evidence-driven, implemented outcome.

A useful conceptual progression is:

**desire/problem → goal → success criteria → investigation → strategy → projects → tasks → execution → evidence → adaptation → outcome**

The system should be capable of helping formalize goals progressively instead of requiring the user to begin with a complete technical specification.

## 2. Personal-first product

The foreseeable Personal architecture centers on the fixed A/B/C triad:

- A — Implementer
- B — Verifier
- C — Integrator

The goal is a capable organization with disciplined operating economics, durable continuity, inspectable work, and adaptable division of labor.

Near-term product value depends heavily on reducing unnecessary model cognition and making long-lived Rooms economically sustainable.

## 3. Adaptive organization within a fixed triad

The three-agent production architecture is intentionally stable. Adaptability should come from task allocation, tools, knowledge, coordination, retrieval, and working procedures rather than routinely expanding the number of persistent agents.

Future experiments may introduce perturbations such as a deliberately difficult/antagonistic participant to study organizational response. Such experiments should preserve broad agent autonomy and do not automatically redefine the production architecture.

## 4. Memory and continuity direction

Long-lived intelligence should separate:

- durable institutional knowledge;
- archived episodic history;
- active working context.

Preferred direction:

**Room archive → local searchable index → targeted retrieval → agent context**

This allows broad retention with narrow active-context loading and reduces the risk of stale history silently becoming current belief.

## 5. Deterministic capability direction

Repeated procedures that become stable and deterministic should migrate from expensive recurring model cognition into Codex Room-owned local capabilities/state machines when doing so improves total operating economics and reliability.

The product boundary is important: these are capabilities Codex Room or its agents can use during normal operation. Git/CI/deployment/restart automation used only to build or maintain Codex Room is supporting engineering work, not itself a product phase.

Preferred principle:

**agents formulate claims and choose actions → deterministic software computes exact facts → agents interpret significance**

Candidate product domains include:

- exact assertions and validation;
- extraction, filtering, sorting, grouping, deduplication, normalization, and statistics;
- artifact hashing, structural comparison, manifests, and version/provenance checks;
- structured work/evidence state;
- Room-state and resource introspection.

Hard-wire functions, not judgment. Goal interpretation, relevance, decomposition, evidence significance, peer invocation, synthesis, and closure remain agent cognition unless later evidence demonstrates a genuinely deterministic procedure.

## 6. Personal usage pacing direction

**Status: DECIDED / NOT IMPLEMENTED — approved planned development (D-019).**

Codex Room Personal should provide a user-configurable daily usage pacing limit expressed as a percentage of the user's weekly Codex usage allowance.

The approved baseline is:

- default daily limit: **1/7 of the weekly allowance (~14.3%)**;
- use Codex's structured account rate-limit/usage meter rather than estimate the weekly allowance from Room token counts;
- once the configured daily allowance has been reached according to the latest available reading, stop initiating new model work under the pacing policy;
- allow work already in progress to finish, accepting possible overshoot;
- treat provider enforcement as authoritative.

This feature is approved for development but is not implemented. Development Control owns scheduling and priority. Warning thresholds, UI presentation, carry-forward behavior, daily-period/time-zone semantics, polling cadence, and exact SDK/app-server integration remain implementation-design questions.

## 7. Setup and onboarding direction

**Status: EXPLORATORY.**

A future Codex Room setup wizard should guide a user through initial setup rather than requiring them to understand the underlying installation and authentication details unaided.

The wizard should help the user:

- initialize and configure their Codex Room;
- identify or verify required local prerequisites;
- connect their OpenAI/Codex account to Codex Room using the supported authentication mechanism available at implementation time;
- confirm that the account connection and required runtime access are working;
- reach a clear ready-to-use state, with actionable guidance when setup cannot complete.

This is a future development idea, not a current implementation claim or committed delivery item.

## 8. Provider direction

OpenAI/Codex is the first implementation target. Provider neutrality remains a design goal so future versions can potentially support other providers or mixed-provider configurations without redesigning the entire organization.

Provider expansion is deferred behind current operating-economics and reliability work.

## 9. Possible Enterprise future

Later Enterprise-scale capabilities may include:

- dynamic workforce management;
- hiring/retiring agents;
- many Rooms and cross-Room coordination;
- role/permission administration;
- integrations;
- larger organizational budgets and controls.

These are future possibility areas, not claims about the Personal architecture or current implementation.

## 10. Product boundaries for now

Current development should avoid allowing the following to displace core Personal viability:

- premature Enterprise administration;
- provider proliferation;
- packaging/funding work ahead of operating economics;
- nonessential UI refinement;
- architectural complexity whose value has not been demonstrated.

The central near-term product question is whether Codex Room can deliver useful, correct organizational cognition with economically disciplined model usage and durable continuity.
