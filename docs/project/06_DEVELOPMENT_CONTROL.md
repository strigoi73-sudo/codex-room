# Codex Room — Development Control

**Last updated:** 2026-09-26
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** I-034 — **interaction-aware C sequencing** — is the selected immediate refinement and is implemented on a feature branch pending exact-head verification. The underlying roadmap priority remains I-030's concurrent public-delta continuity race.
- **What just happened?** A natural God Button debate showed that C's existing dependency-only sequencing rule could parallelize work that was mechanically independent but conversationally better treated as responsive. The same run also naturally reproduced I-030 recovery waste: B spent two HISTORY continuations recovering A's already-public steelman. See E-188.
- **What is next?** Verify and merge I-034, then resume I-030's CORE public-delta visibility repair before returning to I-028 utility benchmarking.
- **What remains behind it?** I-028 utility benchmarking remains behind I-030.
- **What is blocked?** Nothing conceptual is blocked.
- **What are we deliberately not doing?** We are not globally deleting default model safeguards, hard-coding a second unrestricted model list, or treating unrestricted authorization as a mandate to use maximum cognition.

## Current development state

### I-034 — Interaction-aware C sequencing

**Scope:** [C protected structural coordination / parallel-vs-sequential judgment / responsive peer work]

**Work state:** IN PROGRESS

**Reality / evidence:** DECIDED / IMPLEMENTED ON FEATURE BRANCH / NEEDS EXACT-HEAD VERIFICATION

**Decision:** D-035 (amended 2026-09-26)

**Evidence:** E-188

The principal selected a domain-general refinement to C's existing dependency-aware sequencing responsibility after the natural God Button debate exposed a coordination-topology gap.

The protected C instructions now require C to:

- consider both **dependency** and **interaction value** before concurrent peer delegation;
- parallelize independent cognition when neither assignment materially benefits from receiving the other's contribution first;
- serialize work when a prerequisite artifact/evidence/result is required **or** when one participant's contribution should become substantive input to another participant's reasoning;
- treat rebuttal, critique, cross-examination responses, negotiation, iterative refinement, and responsive dialogue as examples where interaction value may justify sequencing;
- obey explicit principal ordering when supplied;
- otherwise choose order from the objective, relevant context continuity, and execution economy without permanent A/B precedence;
- preserve concurrency as a first-class behavior and never serialize independent work merely to conceal or work around context-visibility defects.

The implementation remains instruction-level. It does **not** add a debate mode, deterministic scheduler, new transaction primitive, persistent role specialization, or workaround for I-030. The existing structural-coordination regression is extended so these requirements appear in C's protected instructions and not in A/B's.

Adoption remains consistent with D-035: freshly composed Rooms receive the refined instructions; existing Room snapshots are not retroactively rewritten. I-030 remains separately responsible for making concurrent public-context delivery mechanically safe.

After exact-head verification and merge, I-034 should close and active development should return directly to I-030.

### I-033 — Compact advisory model-selection guidance for C

**Scope:** [C cognition allocation / model-policy prompt / native-catalog interpretation]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / PRINCIPAL EXACT-HEAD VERIFIED / MERGED / CONTROLLED ROOM ACCEPTANCE

**Decision:** D-055

The principal selected a deliberately compact descriptive guide rather than a richer task-routing catalog:

- C receives short general descriptions for known model families and reasoning efforts that are already selectable in the current Room;
- the guide is explicitly advisory only and does not define routing rules, rankings, thresholds, escalation triggers, or quantitative cost policy;
- A/B do not receive the guide;
- default Rooms show guidance only for configurations actually available under D-039/D-051, so default-denied Astra is not described as an available choice;
- unrestricted Rooms derive the guide from the snapshotted native catalog, but an unknown native model/effort remains selectable even when Codex Room has no maintained description for it;
- native discovery, authorization, validation, persistence, rollover inheritance, and provider execution remain unchanged.

PR #219 was principal-verified at exact head `055afd4b0789b3137efa90ee4396aefaf4f458e2`. The focused gate passed the exact-head check, detached clean-worktree check, `git diff --check`, Python compilation, import smoke, the dedicated model-guidance tests, unrestricted native-config regression, default-policy native-config rejection, and default-policy Astra denial regression. GitHub merged that exact expected head as `774a6e3caa6dd83c556e23fe6ffebca992c12961`; comparison from the verified feature head to the merge commit reported zero changed files. No hosted CI/status run was attached to the verified head. See E-186.

Post-merge controlled acceptance then reran Project Helix in a fresh unrestricted Room. The Room finished in 17 counted turns. C assigned A/B work across `luna-low`, `luna-medium`, `terra-high`, and `sol-high`, with no Astra assignment despite Astra authorization and native-catalog availability. In particular, C used `sol-high` for B's final decision analysis and then returned A's independent final decision to `terra-high` rather than preserving Sol merely for consistency. B's `terra-high` adversarial failure analysis was subsequently audited by A at `terra-high` with no reported arithmetic, dependency, probability, nominal-capacity, assumption, or evidentiary errors. The runtime record did not state reasons for individual model changes, so none are inferred. This supports the intended advisory-not-router boundary without establishing a universal routing rule or Astra threshold. See E-187.

### I-032 — Automatic per-Round provider usage-meter capture

**Scope:** [ordinary Room lifecycle / native provider usage meter / durable measurement / exports]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / PRINCIPAL EXACT-HEAD VERIFIED / MERGED

**Decision:** D-054

The principal selected read-only automatic usage measurement for all ordinary production Rooms without reactivating D-019 pacing:

- when a Round begins measured work, CORE reads native Codex `account/rateLimits/read` and `account/usage/read` through the existing production adapter;
- when that measured work cycle naturally settles, is stopped/replaced, or later begins another reopened/resumed cycle, CORE records the corresponding end/start boundaries;
- snapshots live in a dedicated durable `usage_meter_snapshots` table rather than the conversational event stream, so measurement does not alter agent-visible transcript sequence or wake behavior;
- completed cycles expose normalized provider-meter before/after values and deltas in Room snapshots and JSON exports; Markdown exports surface the recorded usage-cycle summary;
- the shared normalization/delta implementation is also used by PBM, avoiding two incompatible interpretations of the native provider meter;
- if a provider window resets between snapshots, CORE records the reset and does not report a misleading negative percentage-point delta;
- natural Room completion persists the closing usage snapshot atomically with the `FINISHED` transition, preventing observers/exports from seeing a finished Room with an open measurement cycle;
- this is measurement only. It does not stop work, impose a budget, choose models, or change D-019's deferred pacing policy.

The provider readings are account-level, not exclusive per-Room billing telemetry. Concurrent Codex activity outside the measured Room can contribute to an observed delta, so isolated benchmark runs remain the strongest attribution case.

PR #217 was verified locally by the principal at exact head `ba5de09a0bc441691db318d16611bf8fc0ca6d57`. The focused gate passed `git diff --check`, Python compilation/import smoke, and **4/4** targeted tests in **6.71 s**. GitHub then merged that exact expected head as merge commit `0874b630c1f62505b552b1c9220d40a471214864`. See E-185.

### I-031 — Principal-selectable unrestricted Room model access

**Scope:** [Room setup UI / native model discovery / C model allocation / durable lineage policy]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / PRINCIPAL EXACT-HEAD ACCEPTED / MERGED

**Decision:** D-053

The principal selected a creation-time toggle rather than a global policy change:

- unchecked/default Rooms retain D-039/D-051 behavior unchanged;
- checked Rooms ask native Codex model discovery for the native model catalog and supported reasoning efforts, then snapshot that exact catalog into Room metadata;
- C may allocate any snapshotted native model/effort configuration to A, B, or C;
- unrestricted mode bypasses Room-side Astra gates, peer-versus-C config restrictions, and exceptional C Task cognition ceilings, while preserving C's responsibility to allocate cognition economically;
- creation fails closed if native discovery is unavailable, empty, or demonstrably partial;
- the setting is immutable after Room creation, survives restart through persisted metadata, and normal rollover successors inherit the exact policy/catalog;
- Room UI and exports expose the active model policy.

The implementation deliberately reuses native Codex `model/list` rather than creating a second Room-owned unrestricted catalog. Source review verified the pinned 0.154 native pagination contract and repaired the adapter integration before the verification freeze. PR #215 merged after principal acceptance of exact head `a189a9b9b0c03e118f5c5d9a862739a5d47f33fc`. The focused run produced 127 passes and one unchanged rollover timing failure; that test then passed five consecutive isolated reruns. `verify-fast.cmd` was not run after the focused-suite failure, and the evidence does not represent the full suite as clean. GitHub comparison from the accepted feature head to merge commit `0ddfc5d6411c4da749dd16a5a903f7b028bc1f09` reported zero file differences. See E-184.

### I-030 — Same-Task conversational continuity repair

**Scope:** [worker provider-context continuity / public Room delta / same-Task HISTORY / token economy]

**Work state:** IN PROGRESS

**Reality / evidence:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED / NATURAL RUNTIME ACCEPTANCE PARTIAL — CONCURRENT PUBLIC-DELTA RACE REMAINS

**Decision:** D-052

A natural multi-agent AI debate exposed a product-level continuity defect in the production assignment-thread model: later A/B Assignments sometimes lacked public statements already made by their peers, then spent additional model executions requesting, reconstructing, or unsuccessfully searching for that same Room context. The principal judged the existing rule too conservative for token efficiency and directed a repair before further utility benchmarking.

D-052 changes the worker boundary without returning to permanent transcript replay:

- same A/B worker + same active Task automatically continues the latest completed worker provider context;
- `fresh_context=true` explicitly requests a new provider context when independence/reset/low-context execution is the real goal;
- exact `context_from_assignment_id` remains available and is still required for bounded cross-Task grace continuation;
- each new A/B Assignment receives a bounded public conversational delta on its first execution only;
- the delta contains only public, agent-readable conversational Room messages and excludes private/mechanical/status/tool/economics material;
- `HISTORY` may retrieve completed Assignment results from the current Task as well as prior Tasks/Rounds;
- C coordinator continuity/REFRESH and Task-boundary semantics remain unchanged.

PR #213 merged the implementation after principal exact-head verification of `03fb490d6b924f6268a29ceeda62a8f7bab6300a`. The focused D-052 continuity regression block passed and `verify-fast.cmd` passed. GitHub comparison from that exact verified head to merge commit `2985b714dce70e0fe7540e8b2e8b3eb3fc7a4c17` reported zero file differences. See E-183.

Natural provider-backed debate acceptance confirmed same-worker continuity but exposed a remaining concurrency race: a peer message published while another worker's provider execution is in flight can predate that worker's own result without ever having been supplied to its provider context, then be skipped by the next delta boundary and require HISTORY recovery. I-030 therefore remains open. The next repair should track what external public transcript was actually supplied to each worker context rather than inferring visibility from the worker's result sequence, with bounded-backlog semantics that cannot silently skip capped events.

### I-029 — Opening-prompt Astra opt-in

**Scope:** [CORE model allocation / explicit principal authorization / conversation-lineage persistence]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED / PRINCIPAL-VERIFIED NATURAL PROVIDER ACCEPTANCE

**Decision:** D-051

The principal explicitly authorized a narrow replacement for D-028:

- Astra remains denied unless the opening Room prompt explicitly requests it;
- authorization is captured once at Room creation and persists for the whole conversation lineage, including later turns, Tasks/Rounds, retries, and normal rollover successors;
- later observer or agent messages cannot grant Astra to an unauthorized lineage;
- authorized Rooms expose Astra Low/Medium/High through C's existing bounded model-allocation surface, while C must honor the participant/model directions in the opening prompt rather than expanding Astra use merely because it is available;
- the implementation must fail closed both when C attempts an unauthorized Astra allocation and immediately before provider execution.

PR #210 merged the implementation after exact-head verification of `b923e1654bae39291ff7f3211c1062b1005615b4`. Coverage includes opening-prompt recognition, repeated Astra peer turns in both legacy and production transaction paths, default-denied behavior, adapter fail-closed behavior, and rollover inheritance. The focused Astra suite passed 7/7 and the repository fast verifier passed 64 Linux focused tests, 119 Windows portability tests, and 9 browser transcript tests. GitHub comparison from the exact verified feature head to merge commit `8132fac9df2d4fc06fcb59a0d015400fdab4f5d6` reported zero file differences. See E-181. On 2026-09-24 the principal then reported that a fresh natural provider-backed Room using the intended Astra opening authorization worked as designed. This is recorded as principal-verified acceptance rather than independent transcript inspection. See E-182. I-029 is complete.

### I-028 — Codex Room utility gate

**Scope:** [product-value validation / Room-specific organizational utility / Desktop comparison without handicapping either platform]

**Work state:** IN PROGRESS

**Reality / evidence:** OUB v1/O1 FIRST MEASURED COMPARISON COMPLETE; COST/ORCHESTRATION EVIDENCE VALID; NUMERIC QUALITY SCORE NOT AUTHORITATIVE DUE GRADER-CONTRACT DEFECT

**Evidence basis:** E-174, E-175, E-176, E-177, E-178, E-179, E-180

Purpose: determine whether Codex Room's persistent A/B/C organization creates enough practical value to justify its additional complexity and execution cost.

The gate must test situations where Room's architecture should matter intrinsically rather than merely giving both products another generic coding battery. Candidate dimensions are:

- independent epistemic analysis where premature convergence or correlated error is a meaningful risk;
- durable organizational continuity across separate principal interactions or evolving objectives;
- implementation plus genuinely independent skeptical review where the second perspective can catch consequential defects or alternatives;
- standing objectives where persistent coordination materially reduces principal re-briefing or manual task management.

Desktop must remain free to use its own native capabilities, including subagents, whenever it chooses. Room must likewise use normal A/B/C behavior. The test must not handicap Desktop or prescribe Room choreography.

A positive result requires demonstrated practical benefit such as materially better answer/output quality, materially better consequential-error detection, materially better continuity, materially less human coordination burden, or a workflow/capability that Desktop cannot reproduce with comparable convenience. More agents, more messages, more provenance, or greater token spend are not success criteria.

If fair utility testing fails to establish a meaningful advantage, the project should explicitly consider simplifying, repurposing, or stopping rather than continuing orchestration work by inertia.


Current implementation slice: **OUB v1 / O1 — Competing root causes**.

- OUB is a separate organizational-utility benchmark family rather than a harder PBM battery.
- O1 is a compact fictional duplicate-charge forensic investigation with one real retry/idempotency causal chain and three plausible competing explanations.
- Both platforms receive the same ten-file investigation workspace and the same mission; native internal orchestration is unconstrained.
- No implementation work or outside research is required. The intended model workload is evidence partitioning, competing-hypothesis analysis, causal synthesis, falsification, and control selection.
- O1's design budget is **10–15 minutes per platform**, with a manifest target of 12 minutes, at most ten fixture files, and at most 30 KB of starting fixture content.
- The deterministic 100-point grader separately scores root cause, trigger, exact causal ordering, source/operational evidence, rejection of duplicate-ingress / concurrent-claim / database-pool alternatives, and recurrence controls.
- Reference artifacts and an asset audit are included so satisfiability and grading can be verified before any measured platform run.
- O1 asset head `266481fa1d66571e250d588c3eba2c2b0f430348` passed exact-head verification: reference score 100, 10 fixture files / 9,840 bytes, focused OUB tests 3/3, unchanged PBM v5 fingerprint, repository fast verifier 64 Linux / 118 Windows / 9 browser, clean scope/head checks. PR #202 merged byte-identically as `7d7d3342432908a553c6456d358d819ab8548079`.
- The frozen O1 fingerprint is `d6ec60fca42c6dd436b15d4f8621bb711056b1da5aa93f5a6ecaee2188ba4835`.
- The thin measurement harness creates equivalent Desktop/Room workspaces, starts the ordinary Room arm plus detached monitors, discovers exactly one fresh Desktop root by workspace, aggregates Desktop native descendants and all Room executions, enforces no-substantive-principal-intervention plus frozen-fixture integrity, grades both final workspaces, and reports quality/cost/duration/orchestration separately without declaring a winner.
- Harness implementation uses a 30-minute safety ceiling while retaining the 10–15 minute / 12-minute target as the intended task budget.
- Exact harness head `9790c736ba695b8cc127b19ea45b480eb0713867` passed the frozen-asset invariant, harness audit, 14 focused OUB/PBM tests, unchanged PBM v5 fingerprint, repository fast verifier (64 Linux / 118 Windows / 9 browser), and exact scope/head checks. PR #203 merged byte-identically as `21b427a68a582ce3f717f4c64759bebd0c710edc`; see E-177.
- First measured O1 comparison completed as `oub-v1-o01-20260921T164303033477Z`. Both arms were VALID and used the same frozen fingerprint. Desktop: 167,898 tokens / 56.223 s / 1 thread / 0 descendants. Room: 191,793 tokens / 109.143 s / 5 executions / 0 peer invocations. The observed Room/Desktop token ratio was 1.1423 and duration ratio 1.9413.
- The reported quality scores (Desktop 45, Room 35) are **not authoritative measures of diagnosis quality**. `BENCHMARK.md` permitted arbitrary descriptive `UPPER_SNAKE_CASE` codes, while the hidden grader required exact canonical strings and one exact four-step chain. Manual inspection shows both platforms identified the unstable per-attempt idempotency identity, ambiguous timeout-after-commit mechanism, the three rejected alternatives, and the two intended controls. Preserve the numeric outputs as historical grader results, but do not use them to infer a 10-point reasoning gap.
- O1 did not create the intended organizational pressure: both platforms finished far below the 10–15 minute design budget, Desktop used no descendants, and Room used no A/B peer invocation. O1 therefore provides a valid negative signal about spontaneous Room organizational activation plus valid cost/time evidence, but is insufficient as the decisive I-028 utility gate. Do not rerun O1 merely for another stochastic sample; design the next OUB version/task around stronger intrinsic need for independent analysis and a grader contract that cannot penalize unspecified hidden labels.
- The first O1 launch attempt exposed a launcher race before any measured arm was created: `Restart-Codex-Room.bat` returned after process launch but before the API accepted connections, causing `oub-v1.ps1 prepare` to fail at `/api/health`. PR #205 adds a post-launch readiness gate that polls `/api/health` for up to 30 seconds and cleans up on failure. Exact head `6ef357f512b1ff8b5f485212485c40249dd7fb7a` passed 9 launcher tests, frozen OUB/PBM fingerprint checks, a live restart-readiness probe, no-active-OUB confirmation, and exact scope/head checks; it merged byte-identically as `e0897b692aa985c6aa676a63a55df4cfe247ca17`. See E-178.
- The second O1 launch attempt reached Room creation but still failed before any measured turn began: OUB tried to delete the newly created live Room `shared` workspace before copying the fixture, but the persistent Codex threads already used that directory as their working directory, producing Windows `WinError 32`. PR #207 aligns OUB with PBM's proven pattern by populating the existing empty Room workspace in place, rejects unexpected pre-existing files, and archives a newly created Room automatically if preparation fails before measurement. Exact head `0eb91145f5eb75237b9dcc4fba1a03620fb971cb` passed 17 focused OUB/PBM tests, a Windows live-workspace lock regression, frozen OUB/PBM fingerprint checks, and exact scope/head checks; it merged byte-identically as `4b8d9a4335fd3abddd02b7ba36a90b20c685a13e`. See E-179.

### I-027 — PBM v5 platform-outcome benchmark


**Scope:** [platform-level benchmark / equivalent mission and fixtures / native internal orchestration / aggregate platform measurement]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / EXACT-HEAD VERIFIED / PROMOTED / FIRST LIVE COMPARISON COMPLETE

**Decision:** D-050

**Evidence:** E-173, E-174, E-175

PBM v5 corrects the benchmark abstraction boundary while preserving the frozen seven-task battery and graders.

Current architecture:

- the comparison unit is **Desktop versus Codex Room as platforms**;
- both platforms receive the same frozen seven-task mission, equivalent prepared fixtures, the same completion criteria, and the same deterministic graders;
- after measured work begins, substantive principal guidance is prohibited;
- Desktop receives one fresh top-level native task rooted at its prepared benchmark workspace and may sequence, parallelize, delegate, create native descendants, or work directly as it chooses;
- Desktop cost/evidence aggregates the measured top-level rollout plus every native descendant attributable through rollout parent lineage;
- Room receives one fresh ordinary measured Room and retains normal A/B/C coordination and D-039 cognition; PBM does not prescribe which peers C invokes or how the Room sequences work;
- Room cost/evidence covers the complete measured Round across all participating executions;
- internal agent topology is provenance and measured cost, not a validity requirement;
- validity remains tied to equivalent starting boundary, frozen mission/prompt integrity, absence of substantive principal intervention, complete provider usage, completion evidence, and deterministic correctness grading;
- automatic evidence capture, comparison, bundling, provider/account usage-meter context, and recovery operations remain deterministic harness responsibilities;
- `benchmarks/pbm/CURRENT` resolves to **v5**;
- PBM v4 is frozen as the promoted predecessor and is superseded for new live comparisons; no paid seven-task v4 comparison completed.

The first paid seven-task v5 comparison completed successfully as `pbm-v5-benchmark-20260921T130735334526Z`: Desktop VALID/100 at 371,378 measured tokens and 292.069 seconds; Room VALID/100 at 1,473,150 measured tokens and 628.984 seconds; Room/Desktop token ratio 3.9667. See E-174.

A controlled C-only follow-up, `pbm-v5-c-only-20260921T134611828882Z`, then reused the verified Desktop baseline while mechanically prohibiting A/B delegation or execution. C-only finished VALID/100 at 644,255 measured tokens and 327.556 seconds across 5 Agent-C executions with zero peer invocations. This reduced tokens 56.27% and time 47.92% versus the ordinary three-agent Room run, but remained 1.7348× Desktop tokens and 1.1215× Desktop duration. The fifth C execution alone consumed 518,708 tokens, showing a residual single-agent context/tool-loop economy problem after peer overhead is removed. See E-175.


### I-026 — PBM v4 common protocol with thin platform adapters

**Scope:** [common benchmark protocol / native Desktop adapter / ordinary Room adapter / deterministic pairing and comparison]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / EXACT-HEAD VERIFIED / LIVE CANARY VERIFIED / PROMOTED

**Decision:** D-049 (supersedes D-048 operator-initiation mechanics)

**Evidence:** E-167, E-168, E-169, E-170, E-171, E-172

The principal required two complementary benchmark executions under one common PBM protocol, with exactly one controller initiation per platform and no intermediate principal choreography. That bounded work is complete.

Final production architecture:

- one frozen seven-task cross-domain benchmark battery with equivalent prepared starting fixtures for both products;
- **common protocol:** one normative procedure owns fingerprint binding, fixture equivalence, validity, grading, capture, bundling, automatic pairing, and comparison;
- **Desktop adapter:** one principal instruction to a non-measured Desktop controller; native fresh-task creation launches one fresh measured child and a detached deterministic monitor handles completion;
- provisional Desktop `client-new-thread:<uuid>` identities are resolved fail-closed to the unique persisted rollout created after PBM preparation with the exact controller cwd, then rebound to the durable rollout thread id;
- **Room adapter:** one principal instruction to C in the persistent non-measured PBM v4 Room Runner; C launches a detached deterministic worker that creates and waits only for one fresh measured ordinary Room;
- measured Room work retains normal A/B/C coordination and D-039 cognition, with substantive principal consultation treated as invalid intervention;
- no cross-platform model controller, alternating-arm schedule, platform wait loop, wake-up dependency, or principal run-id relay;
- deterministic state supports status, abort, evidence bundling, and idempotent recovery/finalization when both platform results exist;
- explicit result classification remains **VALID / INVALID / FAILED**;
- token/duration efficiency is reported across the full battery, with task-specific correctness reported separately;
- historical `t07-spec-repair` remains excluded because its frozen contract is internally inconsistent.

Promotion gate:

1. seven-task satisfiability/reference audit — **PASS**;
2. task-specific grader coverage audit — **PASS**;
3. focused deterministic tests — **PASS**;
4. repository routine verification — **PASS**;
5. repaired one-initiation Desktop canary — **PASS / VALID / 100**;
6. one-initiation Room canary — **PASS / VALID / 100**;
7. automatic comparison/fingerprint/finalization and recovery/evidence paths — **PASS**;
8. `benchmarks/pbm/CURRENT` promoted to **v4** — **COMPLETE**.

Final live promotion canary:

- run: `pbm-v4-canary-protocol-20260921T085358797378Z`;
- Desktop: **VALID**, score 100, 126,873 tokens, 20.859 seconds;
- Room: **VALID**, score 100, 144,863 tokens, 44.911 seconds, 1 peer invocation;
- matching benchmark fingerprint: **true**;
- matching canary fingerprint: **true**;
- comparable: **true**;
- finalization error: **none**;
- active pair after completion: **false**.

These canary usage values validate protocol execution only. They are not a performance benchmark result and must not be used to claim relative product efficiency. A paid seven-task comparison remains a separate principal invocation of **Run PBM**.

### I-025 — PBM v3 one-paste workflow

**Scope:** [benchmark operator workflow / native Desktop task controller / deterministic Room controller]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / HISTORICALLY VERIFIED / LIVE-END-TO-END FAILED / SUPERSEDED FOR CURRENT BENCHMARK WORK

**Decision:** D-047

**Evidence:** E-165, E-166

**Postmortem disposition:** E-167 supersedes the earlier readiness inference. The first substantial live run exposed controller-liveness, validity-enforcement, and workload/grader defects. Preserve v3 for historical reproduction only; do not use it for another live performance comparison.


PBM v3 preserves the frozen PBM workload and measurement semantics while removing repeated human prompt/command choreography.

Implemented behavior:

- `benchmarks/pbm/CURRENT` resolves to v3 on canonical `main`;
- the principal opens Desktop on `pbm_desktop_controller` and supplies one instruction: read/execute `DRIVER.md`;
- the Desktop controller performs coordination only and uses native fresh-task management for each Desktop arm; there is no Codex CLI fallback;
- exactly one current Desktop task is staged at a time under the controller folder, while graders/oracles and historical results remain outside the intended child workspace;
- PBM creates one controller Room, stages its files, starts its Round, and has C enter a private principal-consultation wait before any benchmark work;
- the principal's one Room paste is the private reply instructing C to read/execute `PBM_ROOM_DRIVER.md`;
- that controller Room then launches a detached deterministic worker, which creates a fresh ordinary Room for every Room benchmark arm;
- the original sixteen-arm alternating sequence remains authoritative;
- v2 run/task-pair contextual snapshots remain in force;
- D-039 dynamic Room model/reasoning allocation remains part of the measured product behavior;
- Desktop-controller and Room-controller usage are recorded separately from task execution usage, with an all-in view also produced;
- native approval dialogs may still require principal action and are not treated as new benchmark prompts;
- the v3 fingerprint binds orchestration code and driver files in addition to the inherited task assets.

**Verification:** E-165 and E-166. The original final implementation head passed exact-head deterministic verification plus bounded Desktop- and Room-controller preflights. The first live invocation then exposed a controller-directory Python import-path defect before initialization; PR #181 repaired that path with a tracked repo-root wrapper. The exact repair head passed a controller-directory import smoke test, 9 focused PBM tests, and the repository fast verifier. No benchmark task executed during the failed live attempt or the repair verification.

### I-024 — PBM v2 contextual baseline

**Scope:** [benchmark measurement protocol / read-only native account + environment context]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / EXACT-HEAD VERIFIED / READ-ONLY PREFLIGHT VERIFIED / LIVE PAID PBM NOT YET EXECUTED

**Decision:** D-046

**Evidence:** E-164

PBM v2 keeps the PBM v1 workload unchanged while adding interpretive context before and after benchmark work.

Implemented behavior:

- PBM v2 remains explicitly reproducible; canonical `benchmarks/pbm/CURRENT` now resolves to v3;
- the v2 manifest inherits v1 task assets and fingerprints both version trees;
- v1 can still be explicitly reproduced through `--version v1`;
- each v2 run captures `run-start` and `run-end` snapshots;
- each task pair captures one pre-pair and one post-pair snapshot;
- snapshots attempt read-only native `account/rateLimits/read` and `account/usage/read` plus safe runtime/config/tool inventory and local repository/environment provenance;
- snapshot sanitation removes account identity/credential fields while retaining usage/credit/rate-limit semantics;
- native snapshot failures are recorded as unavailable and do not fabricate values;
- primary Desktop/Room usage accounting and deterministic quality graders remain unchanged from v1.
- the Room arm remains naturalistic under D-039: C may dynamically allocate ordinary model/reasoning configurations for itself and peers, and PBM records rather than suppresses those choices.

**Implementation boundary:** satisfied for v2. Snapshot reads are non-cognitive and read-only; the preflight produced no Codex rollout traffic and no task-execution state. They provide interpretive context only and do not replace rollout/Room execution accounting.

### I-023 — PBM (Performance Benchmark)

**Scope:** [benchmark tooling + paired Codex Desktop / Codex Room execution]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / EXACT-HEAD VERIFIED / LIVE PBM RUN NOT YET EXECUTED

**Decision:** D-045

PBM is the canonical standardized performance benchmark for comparing ordinary Codex Desktop with Codex Room across a fixed, versioned suite of paired tasks. The principal invocation **“Run PBM”** must resolve to the current canonical PBM procedure rather than triggering ad hoc benchmark design.

PBM v1 establishes:

- a frozen versioned task suite spanning trivial mechanical work through larger ambiguous/verification-heavy work;
- exact paired starting fixtures and prompts;
- fresh isolated Desktop and Room executions without cross-arm contamination;
- a primary naturalistic comparison in which each product operates as designed, plus a controlled mode where useful for isolating coordination/model effects;
- provider usage accounting using existing rollout instrumentation, with Room A/B/C usage aggregated;
- elapsed-time, tool-call, failure/retry, model/effort, agent-invocation, and coordination-waste measurements;
- deterministic task-specific acceptance checks and explicit quality/correctness outcomes;
- machine-readable run records and a standard human-readable comparison report;
- a low-cost pilot before broader replication, so the benchmark itself does not recreate previously observed high-cost synthetic testing.

**Implementation boundary:** satisfied for v1. The procedure, fixtures, measurement semantics, and reporting contract are now frozen and mechanically inspectable. Future material changes require a new benchmark version rather than silent mutation of v1.

PBM v1 separates the product arms mechanically:

- `pbm-desktop.ps1` prepares a fresh Desktop workspace/prompt and captures the matching native Desktop rollout only after the principal runs the task in a fresh Codex Desktop chat;
- `pbm-room.ps1` prepares a fresh Room without starting cognition, stages the same fixture, then separately starts/waits/exports/captures the Room arm;
- `codex_room/pbm.py` owns only shared deterministic manifest, fixture, grader, accounting, and report logic;
- PBM v1 and v2 remain frozen and explicitly reproducible; `benchmarks/pbm/CURRENT` now resolves the canonical live-use version, PBM v3, which preserves those exact eight v1 task assets, v2 contextual snapshots, and the verified one-paste orchestration protocol.

**Verification:** E-163. The tested PR head and canonical merge commit have the same Git tree. No live PBM task execution is claimed by this verification.

### I-022 — Native Codex capability exposure and execution-economics audit

**Scope:** [CORE + ROOM UI audit; native Codex/App Server first]

**Work state:** COMPLETE

**Reality / evidence:** EXPLORATORY AUDIT COMPLETE / VERIFIED / NO IMPLEMENTATION AUTHORIZED

**Evidence:** E-159, E-160

I-022 separated three questions that must not be collapsed:

1. does exact Codex 0.154 expose a primitive;
2. can Codex Room's SDK/runtime call or inherit it;
3. should Codex Room expose/adapt it as a product feature.

The exact-source audit verified native support for active-turn steering/interruption, model discovery, provider-thread lifecycle controls, native review, rate-limit/usage reads, permission profiles, command/file/permission approvals, tool user-input requests, structured image/local-image inputs, managed-worktree machinery, browser/computer-use feature/configuration surfaces, remote-environment contracts, and other host/runtime facilities.

E-160 then compared those families by current Room status, principal value, inherent cognition cost, continuation/context implications, overlap with Room mechanisms, authority burden, and implementation complexity.

**Selection boundary:** I-022 is not an implementation queue. Any feature-specific runtime probe, implementation slice, revival of a deferred feature such as D-019, or host-integration project requires separate principal selection. Built-in Codex subagents remain disabled.

### I-021 — Principal-controlled Codex plugin management

**Scope:** [native Codex/ChatGPT administration + existing Room visibility/use]

**Work state:** COMPLETE

**Reality / evidence:** NATIVE-HOST PATH SELECTED / VERIFIED AS A PRODUCT BOUNDARY

**Decision / evidence:** D-043; E-157, E-158, E-162

Stage A verified the exact Codex 0.154 plugin/configuration contracts and proved that an A/B/C-equivalent Windows `:workspace` sandbox can reach Codex Room's loopback API, so a Room-local unauthenticated mutation route cannot establish principal-only authority.

Stage B resolved the remaining product choice in favor of native administration. Exact Codex 0.154 already provides human-facing plugin discovery, install/uninstall, enable/disable, marketplace, and app-auth handoff surfaces; current official OpenAI product guidance also exposes plugin installation and management through ChatGPT/Codex surfaces. Codex Room does not override ordinary plugin configuration, already inspects native plugin/skill/MCP/app state for Status & Tools, and can use inherited capabilities through the underlying Codex runtime.

Therefore I-021 closes without a Room-side mutation bridge, copied plugin manager, credential/auth proxy, or new principal-proof security subsystem. Reopen only if ordinary use demonstrates a concrete material cost or capability gap from managing plugin state through the native host.

## Approved or deferred work

### D-019 — Personal daily usage pacing

**Work state:** DEFERRED

**Reality:** DECIDED / NOT IMPLEMENTED

**Evidence:** E-026

The approved baseline remains a configurable daily pacing limit defaulting to one-seventh of the weekly allowance (~14.3%), using structured provider usage/rate-limit data rather than Room token estimates.

Implementation remains deferred until the mixed subscription-allowance versus purchased-credit semantics are understood well enough to define which pool is paced and how multiple pools interact. I-022 verified that exact 0.154 exposes richer account rate-limit/usage structures, but that source-level fact does not by itself resolve the product semantics or reactivate D-019.

### QoL wishlist

Wishlist entries are idea capture, not a work queue. Selection requires an explicit principal choice.

**Implemented / verified:**
- observer composer Enter-to-send / Shift+Enter newline — PR #133;
- composer focus retention — PR #135;
- auto-growing observer composer — PR #135;
- per-Room unsent drafts — PR #135.

**Unselected ideas:**
- new-activity / jump-to-latest control;
- one-click operational-ID copying / Copy diagnostics;
- Room search and filtering;
- transcript detail/noise controls;
- clear immediate action feedback;
- local persistence for harmless presentation preferences;
- conservative navigation/focus keyboard shortcuts;
- copy action on individual agent responses.

## Maintenance / monitor

### PR #110 failed-delegation fallback behavior

**Work state:** MONITOR

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED

E-126 shows the tightened fallback path operating as intended: a nonproductive delegated follow-up was followed by substantial fallback work on a fresh capable peer rather than C's accumulated coordinator context. Continue ordinary-use observation; do not purchase a dedicated synthetic benchmark.

### Exact-turn interruption reconciliation

**Work state:** MONITOR

**Reality:** IMPLEMENTED / REVIEWED / VERIFIED TO SUFFICIENT EVIDENCE

E-127 records the reproduced false interruption, diagnosis, and bounded repair. E-129 adds a normal post-repair continuation that closed by `transaction_settled`. Do not widen the interrupted-only grace or redesign reconciliation absent recurrence.

### I-003 — Provider-side instruction adoption after same-thread profile rebind

**Work state:** MONITOR

**Reality:** NEEDS VERIFICATION / current recurrence not demonstrated

Local rebind mechanics and fail-closed identity behavior are verified. Independent provider-side proof that replacement developer instructions took effect on the resumed same thread remains unproven. Do not spend a dedicated paid test unless ordinary use makes this uncertainty consequential.

### Naturalistic continuation economy

**Work state:** MONITOR

E-086 showed that continuation-economy repair can radically reduce tool-loop replay on a controlled fixture; E-090 showed broader source work can still become expensive; E-129 records a smaller zero-tool relay recurrence. Continue ordinary-use monitoring. Optimize demonstrated expensive patterns rather than purchasing synthetic tests without a concrete recurrence.

## Recently completed programs

Detailed rationale, exact commits, tests, benchmarks, and historical narrative belong in the Decision/Evidence registers and Architecture, not in this volatile work-control file.

| Work | Current disposition | Durable references |
|---|---|---|
| I-025 — PBM v3 one-paste workflow | COMPLETE / IMPLEMENTED / EXACT-HEAD + CONTROLLER-PREFLIGHT VERIFIED / first benchmark-task execution pending after launch-path repair | D-047; E-165–E-166 |
| I-024 — PBM v2 contextual baseline | COMPLETE / IMPLEMENTED / EXACT-HEAD + READ-ONLY PREFLIGHT VERIFIED / first live PBM pending | D-046; E-164 |
| I-023 — PBM (Performance Benchmark) | COMPLETE / IMPLEMENTED / EXACT-HEAD VERIFIED / first live run pending | D-045; E-163 |
| I-021 — Principal-controlled Codex plugin management | COMPLETE / native-host administration selected / no Room bridge | D-043; E-157–E-158; E-162 |
| I-020 — Codex skill integration / Skill Creator | COMPLETE / IMPLEMENTED / VERIFIED | D-042; E-153–E-156 |
| Post-I-019 host-command catalog cleanup | COMPLETE / IMPLEMENTED / VERIFIED | D-041; E-152 |
| I-019 — Status & Tools | COMPLETE / IMPLEMENTED / VERIFIED | E-149–E-152 |
| I-018 — Desktop ↔ Room capability audit | COMPLETE / audit only | E-149 |
| I-017 — dynamic C cognition / exceptional approval | COMPLETE / IMPLEMENTED / VERIFIED | D-039; E-145–E-148 |
| I-016 — Private Principal Channel | COMPLETE / IMPLEMENTED / VERIFIED | D-038; E-143–E-144 |
| Functional acceptance T0–T14 | COMPLETE / all recorded PASS after T8 repair | E-140–E-141 |
| BCTX-1 through BCTX-4 | COMPLETE / IMPLEMENTED / VERIFIED | D-037; E-132–E-139 |
| Continuous-Round naturalistic acceptance | COMPLETE | E-136–E-139 |
| I-015 — task-transaction stabilization | COMPLETE | D-030–D-034; E-092 onward |
| P4 — deterministic Room/agent capabilities | COMPLETE / IMPLEMENTED / VERIFIED | D-022; E-030–E-040 |
| A3 remediation | COMPLETE | E-065–E-088 |

### Common Cause disposition

The Common Cause implementation/repair/verification work is complete and the artifact is verified play-ready (E-125–E-129). Competitive play is **not development work** and is not an active/planned roadmap item. It may begin only if the principal separately authorizes that activity. Continue to use any future ordinary play only as incidental evidence for monitored coordination behavior; do not manufacture benchmark traffic.

## Repository-development hygiene

- canonical source is private GitHub repo `strigoi73-sudo/codex-room`, branch `main`;
- verification should match the changed risk surface: use focused deterministic tests for localized changes; use `verify-fast.cmd` for materially integration-sensitive changes, repository-wide gates, or when focused evidence is insufficient; `verify-full.cmd` remains the exhaustive/manual path;
- GitHub Actions are not the routine verification gate after the documented pre-runner failures;
- exact current refs/working-tree state are live Git/GitHub facts, not maintained prose;
- the complete `data/` tree is runtime/generated state and is ignored by Git;
- superseded open PRs #91 and #121 were closed during the 2026-09-20 roadmap audit;
- old unmerged/superseded remote feature branches may remain as Git history residue; they are not active roadmap work. Remove them only after verifying they are obsolete, and do not treat branch existence as work-state authority.

## Deferred work

Keep these deferred unless new evidence or explicit principal direction reprioritizes them:

- archive indexing/embeddings/broad summarization beyond bounded `HISTORY`;
- automatic CORE model routing (C-controlled D-039 allocation is separate);
- broader deterministic-tooling promotion without demonstrated reuse;
- stronger per-capability OS isolation;
- shareable/redacted exports;
- large-module refactors/storage optimization;
- broader productization/packaging/funding;
- Enterprise workforce features;
- provider-neutral implementation work;
- setup/onboarding wizard;
- blanket Desktop host parity or broad browser/computer-use integration without demonstrated need;
- nonessential UI refinement.

## Open questions

No high-priority conceptual question currently blocks ordinary Codex Room use or development.

Current unresolved questions are feature-local rather than roadmap-global:

- if ordinary use later demonstrates material friction from native-host plugin administration, what exact gap justifies reopening I-021;
- if D-019 is selected again, how should mixed subscription allowance and purchased credits interact;
- if browser/computer use, worktrees, remote execution, attachments, native review, steering, approvals, or other I-022 families are selected, what is the smallest native reuse that preserves Room semantics and execution economics.

I-027 is the current benchmark implementation. Unqualified **Run PBM** resolves to canonical PBM v5. PBM v1–v4 remain available only for historical/reproducibility purposes unless the principal explicitly selects an older version.
