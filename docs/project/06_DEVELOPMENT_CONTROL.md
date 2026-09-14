# Codex Room — Development Control

**Last updated:** 2026-09-14  
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.  
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** The minimum Engineering Foundation, GPT Project review, D-020 permanent Personal triad / C-integration migration, **A2 — Assurance Pass 2**, and **P4 — Deterministic Room and agent capabilities** are complete. The repository baseline is canonical `main`; verify exact HEAD, applicable CI, and local Git state directly when consequential rather than maintaining those mechanically changing facts here.
- **What just changed?** The D-020 delegation-cohort timing issue is now **LIVE VERIFIED / COMPLETE**. E-055 confirms that the first peer return stays passive to C, the full cohort settles, and C receives one coalesced integration turn before normal closure.
- **What is blocked?** Nothing. The delegation-cohort timing repair is live verified.
- **Where is P4?** **COMPLETE.** E-030 through E-040 contain the implementation/live-verification evidence across P4.1–P4.5.
- **What is next?** The timing issue is complete. Reassess the roadmap before starting another implementation slice.
- **What are we deliberately not doing?** **No further personality calibration or personality behavioral testing unless the principal explicitly revisits it.** No broader fan-out/join framework, archive/retrieval, capability-promotion, provider-subagent-routing, provider-neutral, broader productization, or Enterprise work during this timing slice.

## Current Focus

### C delegation-cohort timing
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / LIVE VERIFIED  
**Decision:** D-020  
**Observed Room evidence:** E-052  
**Instruction repair:** E-053  
**Deterministic timing implementation:** E-054  
**Live verification:** E-055

E-055 verifies the exact timing mechanism end to end. A returned first and remained passive to C. B returned later. CORE then created one delegation-cohort-settled trigger, and C consumed both peer returns plus that trigger in one integration turn. The same C FINISH settled both peer MESSAGE boundaries and the Round closed normally.

The demonstrated timing issue is complete. No further timing retest is currently warranted.

### Personality calibration
**Work state:** DEFERRED  
**Reality:** Historical evidence retained through E-051; no current behavioral-testing priority  
**Decision:** D-023

The principal explicitly stopped further personality testing on 2026-09-14 in order to focus on the coordination timing defect exposed by CG1. Existing V7 defaults remain the current implemented defaults; this status does not claim that the personality calibration target was achieved. Resume only on explicit principal direction.

## Recently completed work

### Live C delegation-cohort timing verification
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / LIVE VERIFIED — 2026-09-14  
**Decision:** D-020  
**Evidence:** E-055

The fresh timing-only Room verified the E-054 mechanism without any personality scoring. One C message invoked A and B together; A returned first and did not wake C; B returned later; one cohort-settled trigger then made C runnable; C consumed both peer returns in one integration batch; causal settlement and normal closure succeeded.

### Deterministic C delegation-cohort batching
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED deterministically — 2026-09-14  
**Decision:** D-020  
**Evidence:** E-054

PR #43 changes C wake timing for one multi-peer delegation cohort. Partial peer returns to C become passive/readable until the cohort settles, then one durable cohort trigger makes C runnable and existing delivery coalescing provides the accumulated returns in one integration turn. Single-peer delegation is unchanged.

Exact PR head `7ee029e9ee8678eb6e7645b130311e866e24f87c` passed **317 tests, 2 warnings**. Squash merge `167ef0cc609ae5635909ae11b722a7842252e570` has the exact same tree `25defbb94723c90a6698d1acb311e7eff71e17cf`; canonical-main run `34889163939` also passed **317 tests, 2 warnings**.

### CG1 coordination gate and C delegated-input settlement repair
**Work state:** COMPLETE for diagnosis/repair; behavioral verification pending  
**Reality / evidence:** CG1 PARTIAL PASS / OBSERVED ISSUE; repair IMPLEMENTED / VERIFIED deterministically — 2026-09-14  
**Decisions:** D-020, D-023  
**Evidence:** E-052, E-053

CG1 established that coordination-level task allocation can produce non-redundant peer cognition where identical same-task prompting did not. C's delegation itself succeeded and A/B adhered to the bounded assignments.

The remaining issue was premature semantic finalization: C responded substantively after only the first peer return. The existing runtime later reopened C on the second return, so no mechanical closure leak occurred.

PR #41 adds a narrow protected C rule requiring explicitly necessary multi-peer inputs to settle before final recommendation/FINISH. Exact PR head `04fdca71911330a0a4c8607738e89c0e1279311c` passed GitHub Actions run `34887902144` with **315 passed, 2 warnings**. Squash merge `2ce2e7c40fbca09ac31e843b7d06dabf13cc387d` has the exact same Git tree `9af8be81e7cbc1fc7f94c73aafdf295e360e43bd`; canonical-main run `34888053548` also passed **315 passed, 2 warnings**.

### V7 same-task work-product admission gate
**Work state:** COMPLETE  
**Reality / evidence:** OBSERVED ISSUE — admission gate failed — 2026-09-14  
**Decision:** D-023  
**Evidence:** E-051

The V7 AI tutoring rerun was mechanically clean under the established independent controls. B produced a recognizable evidence audit, but A and C still organized around the same causal-inference objection and randomized/phased evaluation plan. The explicit primary-work-product language therefore did not prevent same-task convergence.

The experiment changes the active mechanism under test: stop asking three identical models to solve the same broad task independently and expecting static personality text to create sufficient cognitive division. Move complementarity to C-first decomposition and bounded peer task allocation.

### V7 complementary work-product contracts
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED deterministically — 2026-09-14  
**Decision:** D-023  
**Evidence:** E-050

PR #38 replaced the V6.2 "persistent cognitive center while still solving the full problem" mechanism with explicit primary deliverables: A possibility brief, B evidence audit, and C decision map. Each default now rejects comprehensive balanced coverage merely for completeness. A/B recommendations are subordinate to their primary work products; C is explicitly told to use peer cognition in ordinary collaborative operation rather than silently absorb every missing job.

The D-023 protected-layer boundary is unchanged: institutional identity/peer rules, C's structural organizer responsibilities, and Room protocol remain outside the replaceable personality body.

Startup migration recognizes the exact V6.2 built-in personality bodies and updates only those defaults to V7. Non-matching/custom default text remains preserved, and existing Room snapshots/effective instructions are not silently rewritten.

Exact PR head `739ab2562ef38212ce0e4f4c9ef2fe1808ee4cee` passed GitHub Actions run `34873161338` with **315 tests, 2 warnings**. PR #38 squash-merged as `1c427954c7471a9d8007bd2ac29bac7d2d3f1655`; merge tree `0fc53385d726084bbc7f13a5cce551cdde302aff` exactly matches the tested PR-head tree. Canonical-main run `34873373728` also passed **315 tests, 2 warnings**.

This establishes V7 implementation, not live behavioral complementarity.

### V6.2 behavioral evaluation
**Work state:** COMPLETE  
**Reality / evidence:** OBSERVED ISSUE — pre-set criterion not met — 2026-09-14  
**Decision:** D-023  
**Evidence:** E-049

Three controlled V6.2 scenarios were run under clean independent controls. Café showed meaningful complementary work and passed its qualitative gate, but AI tutoring and manuscript revision both converged strongly on the same dominant reasoning method and operational plan.

The agreed practical target was at least 3 of 4 complete trios. After two failures in the first three scenarios, the maximum possible score was 2 of 4, so the disaster-relief scenario and blind classification were intentionally not run.

The result is stronger than the V4/V5 calibration evidence: V6.2 could produce genuine differentiation when the task left room for several useful approaches, but a salient high-quality reasoning path still overwhelmed the personality contracts. This motivated V7's primary-work-product mechanism.

### V6.2 persistent complementary cognitive contracts
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED deterministically — 2026-09-14  
**Decision:** D-023  
**Evidence:** E-048

PR #36 replaced V5's stronger opening priors with persistent cognitive centers of gravity that remain active through narrowing, recommendation, and peer follow-up. A owns option-space expansion, B epistemic justification, and C consequential relationships/system structure. Anti-duplication behavior now explicitly moves each agent toward the frontier of work already performed.

The D-023 protected-layer boundary is unchanged: institutional identity/peer rules, C's structural organizer responsibilities, and Room protocol remain outside the replaceable personality body.

Startup migration now recognizes the exact V5 built-in personality bodies and updates only those defaults to V6.2. Non-matching/custom default text remains preserved, and existing Room snapshots/effective instructions are not silently rewritten.

Exact PR head `8ecfd73104638b49975a6bf134cc3dde16f35468` passed GitHub Actions run `34870235815` with **313 tests, 2 warnings**. PR #36 squash-merged as `6d89465de2bf581a8bce2e44ce569beea224f3df`; merge tree `bc2590ddc11682d51ecf3cb79221259f7acd59ea` exactly matches the tested PR-head tree. Canonical-main run `34870432154` also passed **313 tests, 2 warnings**.

This establishes V6.2 implementation, not behavioral differentiation.

### V5 café calibration gate
**Work state:** COMPLETE  
**Reality / evidence:** OBSERVED ISSUE — 2026-09-14  
**Decision:** D-023  
**Evidence:** E-047

The V5 café rerun was mechanically clean under the same independent controls. All three participants nevertheless entered through substantially the same diagnosis: margin compression / margin rather than demand. A, B, and C showed some later texture differences, but V5's explicit first-move prohibitions did not overcome the shared model's common diagnostic entrance strongly enough.

The principal stopped the remaining V5 scenarios and selected a different mechanism for V6.2: persistent asymmetric cognitive contracts rather than further adjective-level strengthening of opening temperament.

### V5 strong personality calibration
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED deterministically — 2026-09-14  
**Decision:** D-023  
**Evidence:** E-046

PR #34 deliberately strengthened the A/B/C cognitive priors rather than continuing small V4-style increments. Each personality now names a dominant first move and a starting posture to resist, while retaining self-correction and the ability to use other reasoning modes later. Protected institutional, structural, and Room-protocol layers were unchanged.

Startup migration now recognizes the exact V4 built-in personality bodies and updates only those defaults to V5. Non-matching/custom default text remains preserved, and existing Room snapshots/effective instructions are not silently rewritten.

The first PR run passed **310 tests** and failed one stale UI assertion that still required the V4 C phrase; no production defect was demonstrated. After changing only that obsolete expectation, exact final PR head `1b38c76b5cf1cbc606fc2b9df2bf3f1e2b4d66be` passed run `34863827367` with **311 tests, 2 warnings**. PR #34 squash-merged as `ed8b73fb9f1437a894e926f65e1ca558e0005973`; merge tree `c5955136274252f77e065d3a5b54825ba2cae5e2` exactly matches the tested PR-head tree. Canonical-main run `34864015525` also passed **311 tests, 2 warnings**.

This establishes V5 implementation, not behavioral differentiation.

### V4 café first-move calibration observation
**Work state:** COMPLETE  
**Reality / evidence:** OBSERVED ISSUE — 2026-09-14  
**Decision:** D-023  
**Evidence:** E-045

The first V4 controlled rerun used the same café scenario and independent controls as the V3 evaluation. Mechanics were clean: exact V4 defaults, no overrides/private initialization/participant-specific overlays, `starting_agent: "either"`, one shared start event, one FINISH from each participant, no MESSAGE, and normal `mutual_finish` closure.

Despite that control, A, B, and C all opened by diagnosing essentially the same margin-versus-demand problem. Later differences existed, but V4's principal intervention was supposed to produce distinct first attentional moves. The principal treated this as a strong enough calibration signal to stop the V4 series and move directly to a more extreme V5. The remaining V4 scenarios and blind packet were intentionally not run.

### V4 default personality distinctiveness revision
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED deterministically — 2026-09-14  
**Decision:** D-023  
**Evidence:** E-044

PR #32 sharpened the standard defaults around distinct first attentional moves without changing protected institutional, structural, or protocol layers. A now first widens the possibility space; B first establishes the epistemic picture; C first locates the question in consequential context and explicitly treats framing as interpretation rather than ruling.

Startup migration now recognizes the exact V3 built-in personality bodies and updates only those defaults to V4. Non-matching/custom default text remains preserved, and existing Room snapshots/effective instructions are not silently rewritten.

Exact PR head `b588e27011b0c1be13f8ada9b1cb254133d2329c` passed GitHub Actions run `34856031735` with **309 tests, 2 warnings**. PR #32 squash-merged as `7567e2a40c6a3745d829f119397cc6525f9f512a`; its Git tree `741448ed0a9d023f012778c679dd5d692ec6f9fe` exactly matches the tested PR-head tree. Canonical-main run `34856479809` also passed **309 tests, 2 warnings**.

This establishes V4 implementation, not V4 behavioral differentiation.

### V3 controlled personality evaluation
**Work state:** COMPLETE  
**Reality / evidence:** HISTORICALLY VERIFIED — criterion not met — 2026-09-14  
**Decision:** D-023  
**Evidence:** E-043

Four fresh Rooms tested the V3 defaults independently across café, AI-tutoring, manuscript, and disaster-relief decisions. All four trials were mechanically clean and showed useful convergence without manufactured disagreement or caricature failure.

The blind reviewer recovered **3/12** individual identities and **0/4** complete A/B/C trios against the established **3/4 complete-trio** target. The sample is too small to support a statistical claim of worse-than-chance performance; the practical result is simply that V3 did not meet the required blind recognizability criterion. V3 remains historical evidence and has been superseded as the active default by V4.

### V3 standard default personality implementation
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED deterministically — 2026-09-13  
**Decision:** D-023  
**Evidence:** E-042

PR #30 replaced the role-derived standard default personality bodies with the approved general-purpose temperaments for A/B/C, kept C's organizer responsibility exclusively in the protected structural layer, migrated only exact known prior built-in personality defaults, preserved non-matching custom profile text, and removed the remaining built-in C profile display label `The Integrator`.

The first PR run exposed one stale UI regression assertion that still required the retired C label; all other tests passed. After updating only that obsolete expectation, the exact final PR head and canonical-main merge both passed **307 tests, 2 warnings**, and the squash-merge Git tree exactly matches the tested PR-head tree.

Behavioral quality is intentionally not claimed by this deterministic evidence. Controlled live Room evaluation is the active next step.


### Protected identity / replaceable personality composition
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED deterministically — 2026-09-13  
**Decision:** D-023  
**Evidence:** E-041

PR #28 separated protected institutional/structural/protocol instructions from the replaceable personality layer. Room personality overrides now replace the selected default personality instead of being appended to it; A, B, and C all support overrides; C's organizer responsibilities remain protected; exact known built-in defaults migrate conservatively while existing Room snapshots and non-matching custom defaults are preserved.

Exact PR-head and canonical-main hosted verification both passed **305 tests, 2 warnings**, and the squash-merge tree exactly matches the tested PR-head tree. The existing standard personality prose still contains the old role-derived labels and is the current active design target, not a completed part of D-023.


### P4 — Deterministic Room and agent capabilities
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED end to end — 2026-09-13  
**Decision:** D-022  
**Evidence:** E-030 through E-040

P4 is product/runtime work: hard-wire deterministic capabilities that Codex Room or its agents can use during normal operation to replace mechanical model cognition. Development/production automation remains supporting engineering work unless it is deliberately exposed as product functionality.

Admission rule: given the same explicit inputs and underlying state, a correct deterministic capability should return substantially the same factual result without requiring judgment. Agents remain responsible for choosing what to test and interpreting significance.

**P4 closure:** P4.1 through P4.5 are complete and verified end to end. Personal/CORE promotion remains a future deliberately selected capability-lifecycle extension under D-022; it is not required to keep P4 open.

#### P4.1 — Deterministic assertions
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-12  
**Evidence:** E-030

The first deterministic-capability vertical slice is complete. Codex Room now provides a read-only, Room-workspace-confined `assert_file` capability for exact regular-file existence, SHA-256, JSON-validity, and required-key assertions. It returns typed JSON; recognized direct capability results are persisted as `deterministic_capability` telemetry while arbitrary command output remains hidden. The current transport uses the agent's existing command tool rather than the provider's experimental dynamic-tool API.

Deterministic verification progressed through PRs #5–#7. The final code-bearing canonical-`main` run passed **152 tests, 2 warnings**. Three bounded live attempts then established the full path: the first exposed dropped SDK tool activity because pinned Codex emits camelCase ThreadItem types; the second verified activity normalization but exposed Windows shell-wrapper provenance handling; the third exported the exact structured capability result.

Final live export evidence:

- C was the sole invoked/consuming participant; A/B remained unengaged;
- C created `p4_probe.json`;
- Room telemetry recorded `type: deterministic_capability`, `capability: assert_file`, `status: completed`, and `ok: true`;
- the structured result independently recorded regular-file existence, valid JSON, and presence of both required keys (`probe`, `status`) as true;
- C FINISHed exactly `P4.1-CAPABILITY-OK`;
- the Round closed normally after exactly one agent turn.

P4.1 is closed. Do not broaden this slice merely because the substrate now exists; select the next capability only from demonstrated product value.

#### P4.2 — Capability registry and discovery
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED end to end — 2026-09-12  
**Decision:** D-022  
**Evidence:** E-031

P4.2 makes deterministic capabilities first-class discoverable objects before custom registration or rollover inheritance is implemented.

Implemented behavior:

- each registered capability has a stable ID, description, origin/scope, version, implementation SHA-256, typed input/output contracts, permissions/side effects, verification metadata, and invocation guidance;
- `codex-room-cap list` returns a compact inventory to control context cost;
- `codex-room-cap inspect CAPABILITY_ID` returns the detailed manifest;
- `codex-room-cap invoke CAPABILITY_ID --input-json JSON_OBJECT` invokes by registered ID;
- the already live-verified `assert_file` capability is registered as the first CORE capability; its P4.1 `assert-file` command remains as a compatibility alias;
- normal agent prompts no longer hard-code `assert_file`; they teach the decision boundary for deterministic software, require checking the registry before ad hoc mechanical execution, prefer an adequate registered capability when one exists, and retain ad hoc deterministic execution as a justified fallback;
- registry list/inspect and capability invocation produce bounded structured telemetry, while arbitrary shell output remains excluded;
- this slice implements only a static CORE registry. Custom registration, lineage persistence, rollover inheritance, Personal promotion, and the broader default library remain **DECIDED / NOT IMPLEMENTED** under D-022.

Verification history:

- the substantive P4.2 branch passed **161 tests, 2 warnings** before the final compact-list refinement;
- PR #8 squash-merged as `aeed9d93d16e4933730b1bbea04b54581dbe62d7`;
- the first post-merge run exposed one stale new-test assertion that still expected detailed fields in the intentionally compact list response; runtime source was not implicated;
- PR #9 changed only `tests/test_capabilities.py` to assert the compact-list boundary and obtain details through inspect; exact PR-head run `34714005661` passed **161 tests, 2 warnings**;
- PR #9 squash-merged as `78dd8da418f2c29c37b94324d66bbe8c99da39b3`; canonical-`main` run `34714080693` passed **161 tests, 2 warnings**.
- the first fresh live P4.2 discovery attempt after local adoption of current code created the probe and finished correctly with C only, but telemetry recorded ordinary `command_execution` rather than `deterministic_capability_registry` / `deterministic_capability`; this demonstrated a capability-selection gap rather than a registry implementation failure;
- PR #10 strengthened only the deterministic-capability guidance plus its prompt regression test. Exact PR head `c4b3f5cf03a7684be1414ddd051a49b6d9a1cc69`; GitHub Actions run `34718435578` passed. It squash-merged as `745e76b305cab38607e6035f4fb670c3ea8f2fd4`; canonical-`main` run `34718498032` also passed.
- the next fresh live probe after PR #10 again used only C and FINISHed correctly, but emitted one `file_change` followed by **two** completed generic `command_execution` events. Because the export deliberately hides arbitrary command text, this did not prove the commands were registry operations; it did prove the live stop condition still lacked durable registry/invocation telemetry and was consistent with an unrecognized outer-shell provenance shape;
- PR #11 added only a narrow PowerShell/pwsh wrapper fallback in capability provenance recognition plus regression tests for registry list, registered invoke, and chained-command rejection when `command_actions` are absent. Exact PR head `8304d0a46cab644cb5069a03730af1de057ff1ad`; run `34719562400` passed **164 tests, 2 warnings**. It squash-merged as `80654078567cbdc997c09586994f1d67a1cc784c`. Main run `34719622155` first failed only the pre-existing `test_stop_before_lease_expiry_cancels_without_false_error_or_retry` timing test; rerunning the same merged bytes passed **164 tests, 2 warnings**.

Final live verification on the post-PR-#11 runtime satisfied the stop condition:

- the user prompt did not name `assert_file`;
- C was the sole invoked/consuming participant; A/B remained unengaged;
- telemetry recorded completed registry `list` and `inspect` operations, both identifying `assert_file` version `1` with implementation SHA-256 `6f34376f64110d61d18f278597196b69c1214bba1a8c048c951c3332f049f7b3`;
- after creating `p4_discovery_probe.json`, C made one malformed registered invocation that returned a structured `invalid_request` error, corrected the input, and retried through the registry path;
- the successful `deterministic_capability` event recorded `capability: assert_file`, `capability_version: "1"`, the same implementation hash, `ok: true`, regular-file existence, valid JSON, and required keys `probe` and `status` all true;
- C FINISHed exactly `P4.2-DISCOVERY-OK`; the one-turn Round closed normally.

P4.2 is closed.

#### P4.3 — Minimal CORE standard library
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED end to end — 2026-09-12  
**Decision:** D-022  
**Evidence:** E-032

Select the smallest set of broadly useful deterministic primitives that should exist in every new Personal Room. Add only capabilities with clear recurring value, compact contracts, bounded permissions/side effects, and deterministic verification. Built-in capabilities must use the same registry/discovery/invocation surface proven by P4.2.

Current sequence:

- **P4.3a — Generic bounded capability-result telemetry: COMPLETE / IMPLEMENTED / VERIFIED.** Each capability may declare `durable_result_fields`; safe invocation telemetry persists only common identity/status fields plus those declared result fields. Invalid declarations are not promoted, arbitrary shell output remains excluded, legacy `assert_file` results remain compatible, and durable evidence above 64 KiB is replaced by explicit truncation metadata. PR #12 exact head `e35d835d54a7af72e4040d5ef86dc0dcaae918b8` passed **167 tests, 2 warnings**; squash merge `2b697de8597bc06cfe21044854869273fb0cceee` passed canonical-main run `34721368173` with **167 tests, 2 warnings**.
- **P4.3b — `find_files`: COMPLETE / IMPLEMENTED / VERIFIED.** Registered CORE version `1`; read-only/workspace-confined; regular files only; symlinks never followed; traversal errors fail visibly; POSIX-style include/exclude globs with Windows backslash normalization; hidden files opt in; optional size bounds; 100 results by default / 200 maximum; 48 KiB match-evidence ceiling; 100,000-entry scan ceiling; explicit truncation reason; stable sorted depth-first ordering. PR #13 exact head `4f5c244437c99130362f3e86e9f618198acb18c9` and squash merge `56d08cd733fdc4598fc878b3778bce664e193aca` both passed **186 tests, 2 warnings**.
- **P4.3c — `search_text`: COMPLETE / IMPLEMENTED / VERIFIED.** Registered CORE version `1`; literal single-line search only; composes bounded `find_files` discovery; UTF-8/NUL-free text only; case and file-glob controls; 100 candidate files default / 200 maximum; 50 matches default / 100 maximum; 2 MiB default / 10 MiB maximum per file; 20 MiB aggregate byte ceiling; bounded excerpts returned only transiently; durable evidence retains query SHA-256/length, exact locations, counts, and truncation metadata. PR #14 exact head `0afb3b7a4b2dc52e451543ba1a25d51cf015155b` and squash merge `eb6c29f346081affa61eb412006f460426bafc40` both passed **216 tests, 2 warnings**.
- **P4.3d — `compare_files`: COMPLETE / IMPLEMENTED / VERIFIED.** Registered CORE version `1`; exact byte comparison plus SHA-256/size evidence; 50 MiB per-file ceiling; small unequal UTF-8 text may produce a bounded unified diff with 2 MiB / 20,000-line eligibility limits and 200-line / 32 KiB diff ceilings; binary/oversized/line-heavy cases retain exact byte comparison and report explicit text-diff status; diff content is transient while durable evidence retains only paths, hashes, sizes, equality, and diff status/count metadata. PR #16 exact head `6e5b7161dd2d75c33e1527db5d51ce552d0e4888` and squash merge `260431ad7ca64ed0c9f1f3b3bf0122ca98e4de6c` both passed **235 tests, 2 warnings**.
- **P4.3e — bounded live evaluation of the four-capability CORE library: COMPLETE / VERIFIED end to end.**

Live stop condition: one fresh post-P4.3d Room must receive a probe that names no capability or registry command, keep C as the sole consuming participant unless peer judgment is genuinely needed, durably record registry discovery, and invoke all four initial CORE capabilities (`find_files`, `search_text`, `compare_files`, `assert_file`) for naturally corresponding mechanical subproblems. Each invocation must carry version/implementation identity and a successful structured result; the evidence must match the known probe fixtures; C must FINISH exactly `P4.3-LIBRARY-OK`; and the Round should close normally.

First live attempt (Room `room_0b855adf7e3f49ef870b6a6f6b60bc24`) **did not satisfy this stop condition**. The user prompt named no capability. C was the sole consuming participant; A/B remained unconsumed. Durable telemetry recorded a successful registry `list` containing all four CORE version-1 capabilities and their implementation hashes, then two completed generic command executions, one file change, one failed generic command execution, and one completed generic command execution. It recorded **no** `deterministic_capability` invocation events. C still FINISHed exactly `P4.3-LIBRARY-OK` and the one-turn Round closed normally. Because exports intentionally omit arbitrary generic command text/output, this evidence cannot establish whether C used ad hoc verification or batched/chained registered operations that were not safely promotable.

PR #17 repaired the behavioral/provenance guidance rather than weakening telemetry safety. Agents are now instructed to run each registry list/inspect and each capability invocation as its own command execution, not chain capability operations with shell commands or each other, and compose multiple adequate registered capabilities separately for multiple independent mechanical subproblems. Exact PR head `ab578295ae9da339983d8f59079a0683a795e9f8`, run `34723435009`: **235 passed, 2 warnings**. Squash merge `d65da0bd1399b0cd5511cf0653162e48af7ae546`; canonical-main run `34723499027`: **235 passed, 2 warnings**.

Final post-repair live verification used fresh Room `room_2077937c86524ac3aaced1918dbe6050`, Round `round_a65e1ca8eb3d48248c06e1730e21923e`. The prompt named no capability or registry command. C alone consumed context; A/B remained unconsumed. C durably recorded registry `list`, inspected all four capability manifests, created the fixtures, surfaced one malformed `find_files` invocation as structured `invalid_request`, corrected it, and then successfully invoked all four capabilities with version `1` and implementation identities matching registry discovery. `find_files` returned exactly the three expected sorted text files; `search_text` returned exactly the two expected line-2/column-1 locations; `compare_files` reported the two files byte-unequal with exact hashes/sizes; and `assert_file` verified regular-file existence, valid JSON, and required keys `probe` / `status`. C FINISHed exactly `P4.3-LIBRARY-OK`; the one-turn Round closed normally.

P4.3 is closed.

`query_data` remains a post-evaluation candidate, not part of the initial P4.3 implementation commitment.

#### P4.4 — Agent-created capability registration and verification
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED end to end — 2026-09-13  
**Decision:** D-022
**Evidence:** E-033 through E-038

P4.4 is implementing the bounded path for A/B/C to turn newly warranted deterministic procedures into registered first-class capabilities when the CORE library is inadequate. Registered status must remain stronger than ordinary ad hoc code: stable identity, exact implementation bytes, typed contracts, declared permissions/side effects, provenance, and adequate verification evidence are required.

##### P4.4a — Custom capability package and identity
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-13

Implemented package-v1 boundary:

- Room drafts live only at `.codex-room/capability-drafts/<id>/`;
- custom IDs use a portable lowercase `[a-z][a-z0-9_]*` namespace with Windows-reserved names rejected;
- v1 packages are lineage-scoped and contain exactly `manifest.json` plus one `capability.py` entrypoint;
- runtime is fixed to Python with protocol `stdio-json-v1`; multi-file packages and other runtimes are intentionally outside this slice;
- manifest validation requires object-shaped input/output schemas, a required boolean `ok` output, explicit durable-result fields, the four CORE-style permission declarations, and a side-effect declaration;
- the draft directory chain and package files must be real non-symlink directories/regular files; unsupported extra entries are rejected;
- manifest and implementation sizes are bounded; the Python entrypoint must be UTF-8, NUL-free, and syntax-valid;
- exact identity includes manifest SHA-256, executable SHA-256, and a domain-separated combined package SHA-256 over the exact manifest and executable bytes;
- permission declarations are explicitly **not** represented as per-capability OS enforcement. The package manifest records `ambient_room_sandbox` with `per_capability_enforcement: false`; registration must not grant authority beyond the Room's ambient execution boundary.

PR #19 exact repaired head `39ead0212319774b987b00bc661b773e6b99c807` and squash merge `574edbfeaf5c5ae9053eae1825a0fe8f6fb728aa` both passed **261 tests, 2 warnings**. The first PR-head run failed only one new expected-error-message assertion; the implementation correctly rejected the malformed schema and the test expectation was aligned before the green reviewed head.

P4.4a does **not** register, publish, discover, inherit, or invoke custom capabilities.

##### P4.4b — Verification and immutable registration
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-13  
**Evidence:** E-034

Implemented verification/publication boundary:

- verification accepts 1–16 exact JSON-object input / exact JSON-object expected-output cases plus optional bounded UTF-8 workspace fixture files;
- each case runs exact copied `capability.py` bytes through Python isolated mode under the caller's existing ambient Room execution boundary;
- case execution has a 5-second default timeout, bounded fixture/input/expected sizes, and a live stdout/stderr size cutoff that kills output floods rather than buffering them without bound;
- successful cases require zero exit, quiet stderr, one UTF-8 JSON object with boolean `ok`, exact expected output, and expected coverage of every declared durable-result field;
- the verifier re-loads and re-hashes the original draft after execution and fails if exact package bytes changed during verification;
- durable verification receipts retain case names plus input/expected/observed/fixture hashes and case-plan identity, not raw test contents;
- host-side publication **never executes candidate code**;
- accepted exact bytes publish under content-addressed package, verification, and registration identities below protected `data/custom-capabilities/`;
- repeated publication of the same exact registration is idempotent; corrupt/conflicting content-addressed bytes fail visibly;
- the registration record binds Room ID, custom ID/version, package SHA-256, manifest SHA-256, implementation SHA-256, and verification SHA-256.

PR #20 exact reviewed head `617c41e95cdbb775b065a8bb47c4ced5c71f0f4c` and squash merge `7ecf05f206043116cf77a9f6a8581b6eb85136be` both passed **277 tests, 2 warnings**.

P4.4b publication is still **not a Room registry binding**. Ordinary `codex-room-cap list / inspect / invoke` remains CORE-only.

##### P4.4c — Room binding and dynamic registry overlay
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-13  
**Evidence:** E-035

Implemented Room activation boundary:

- `codex-room-cap register <id> --cases-file <path>` runs inside the existing agent `workspace_write` sandbox, verifies the exact draft through the P4.4b deterministic test gate, and emits a bounded self-hashed registration request;
- the sandboxed command does **not** write protected `data/custom-capabilities/` state;
- after the exact agent turn is lifecycle-valid and delivery settlement succeeds, `RoomRuntime` host settlement reparses the verification receipt, re-checks exact draft/package identity, publishes the protected immutable package / verification / registration objects, and creates one protected Room binding;
- replay first recognizes an already-bound exact registration, so a recovered result does not depend on later mutable draft state and does not duplicate registration;
- schema-v1 Room binding is single-assignment per capability ID: same exact binding is idempotent; a different registration for the same ID fails visibly rather than silently replacing it;
- CORE/custom ID collisions fail visibly;
- canonical Room workspaces overlay explicitly bound custom capabilities onto the same `list` / `inspect` / `invoke` vocabulary as CORE;
- custom invocation executes immutable published package bytes, not the mutable draft;
- successful custom results preserve implementation, package, registration, and verification identities plus only declared durable result fields through the existing safe capability telemetry path;
- registration requests and host-settlement results are durably observable without persisting raw verification fixture/input/output content.

The original pre-CI implementation briefly attempted protected publication directly from the sandboxed `register` command. Exact-diff review caught that authority-boundary error before verification; PR #21 was corrected so publication/binding occurs only in host settlement.

PR #21 exact reviewed head `8ebfad68e1210d7191f7274a450ed76d29ae2e8e` passed **291 tests, 2 warnings** in GitHub Actions run `34762414175`. It squash-merged as `5e2d90b92197ce58866af0ddaceff922d2b16c9e`; canonical-main run `34762490876` also passed **291 tests, 2 warnings**.

P4.4c does **not** implement rollover inheritance; that remains P4.5.

##### P4.4d — Agent authoring and selection behavior
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-13  
**Evidence:** E-036

Implemented token-efficient agent guidance:

- the always-loaded deterministic-capability instruction still requires registry discovery before ad hoc mechanical execution;
- agents are told to create custom software only when no adequate registered capability exists and reuse, reliability, provenance, or mechanical-complexity value justifies reusable software;
- the full package/test-vector procedure is not injected into every turn. Agents load it only when needed using standalone `codex-room-cap authoring`;
- the on-demand authoring reference derives numeric package/test limits from implementation constants and exposes package-v1 file shape, portable ID rule, fixed lineage/Python/`stdio-json-v1` values, required manifest fields, contract/durable-field/permission/side-effect requirements, exact verification-case shape and limits, registration command, host-pending settlement rule, and the explicit permission-enforcement caveat;
- authoring-reference telemetry persists only operation/schema identity, not the full reference payload;
- agents are told that a successful `register` command proves sandbox verification and requests host registration, but the capability is not active until that turn settles;
- on a later turn they must rediscover with `list` / `inspect` before invocation rather than relying on memory of the draft.

PR #22 exact reviewed head `167cb4361ac8d1c36d858fb9d6dbd5fb18d65747` passed **294 tests, 2 warnings** in GitHub Actions run `34762737011`. It squash-merged as `8afa54e23850441690a6071cb7fff01e32a2ab46`; canonical-main run `34762827607` also passed **294 tests, 2 warnings**.

##### P4.4e — Bounded live custom-capability proof
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED live — 2026-09-13

Use one fresh post-P4.4d Room and **two deliberate rounds** because protected registration becomes active only after the creating turn settles.

**Round 1 stop condition — autonomous creation and host registration**

The user prompt must name no capability ID, package filename, authoring command, registration command, or implementation language. It should present one mechanical transformation that is not covered by the initial CORE library and is sufficiently reusable to justify deterministic software. C should remain the sole consuming participant unless peer judgment is genuinely needed.

Successful evidence requires:

- registry `list` showing the initial CORE inventory without an adequate capability;
- optional but expected on-demand registry `authoring` discovery after C independently decides reusable deterministic software is warranted;
- workspace creation of one bounded custom package and verification-case file consistent with package schema v1;
- a standalone `register` operation yielding durable `verification_passed_host_pending` request evidence with exact package / manifest / implementation / verification identities;
- host-settlement `custom_capability_registration` evidence with `status: completed` and exact registration / verification / package / implementation / binding identities;
- no custom invocation in Round 1, because activation occurs only after settlement;
- C FINISH exactly `P4.4-CUSTOM-REGISTERED`;
- normal Round closure.

**Round 2 stop condition — rediscovery and immutable registered invocation**

Start a new Round in the **same Room**. The prompt should ask C to solve a new input of the same mechanical transformation and to independently verify the result using the Room's available deterministic facilities; it must not name the custom capability or registry commands.

Successful evidence requires:

- C separately runs registry `list` and sees the custom lineage-scoped capability alongside CORE with exact implementation / package / registration identity;
- C inspects that custom capability before use;
- C invokes it through normal `codex-room-cap invoke`;
- durable capability evidence reports matching version, implementation SHA-256, package SHA-256, registration SHA-256, verification SHA-256, `ok: true`, and the correct declared durable result for the new input;
- the invocation is served from immutable published bytes; the proof must not depend on the mutable draft;
- A/B remain unconsumed unless genuine judgment is needed;
- C FINISH exactly `P4.4-CUSTOM-OK`;
- normal Round closure.

A recoverable malformed call may be acceptable if it is durably visible, corrected without ad hoc fallback, and all required final registered operations succeed. If the live probe exposes a new integration defect, preserve the first-export evidence and repair only the demonstrated gap before rerunning.

**First live attempt — partial pass plus demonstrated input-transport gap**

Room `room_857d95aa75c14dd0b939f43baf9a9e17` provided two one-turn C-only rounds.

Round 1 **passed its stop condition**:

- C first listed only the four CORE capabilities, then loaded the on-demand authoring reference;
- C authored the custom lineage capability `ascii_text_slug` and four exact verification cases;
- standalone registration produced `verification_passed_host_pending` evidence with package SHA `af1ed410...`, manifest SHA `d23225a3...`, implementation SHA `3333ecd6...`, and verification SHA `8eca83c2...`;
- host settlement completed registration `abfbeb96...` and binding `0988e7ef...`;
- C alone FINISHed exactly `P4.4-CUSTOM-REGISTERED`; the Round closed normally.

Round 2 **did not pass** despite the exact final marker:

- C durably rediscovered `ascii_text_slug` via `list` and `inspect`, with matching package/implementation/registration/verification identity;
- the first direct registered invocation was promoted correctly but failed `invalid_request` because the inline JSON reached the CLI malformed;
- six later command executions failed generically and two completed generically, but the export contains **no successful `deterministic_capability` event** and therefore no durable `ok:true`, `slug`, or `length` result;
- C nevertheless FINISHed `P4.4-CUSTOM-OK`, so the marker alone is insufficient evidence.

Because arbitrary generic command contents/outputs are intentionally excluded from durable telemetry, the export cannot establish what each later command attempted. Current source did establish a narrow product defect relevant to the observed failure: normal invocation offered only `--input-json JSON_OBJECT` and persistent guidance taught that quote-fragile command-line transport.

PR #23 added `--input-file WORKSPACE_RELATIVE_JSON` as a mutually exclusive, workspace-confined, <=1 MiB UTF-8 JSON-object transport while preserving `--input-json`. CORE and custom manifests now advertise the file form, and agent guidance explicitly switches to it when shell quoting is fragile or an inline attempt fails. Safe standalone invocation telemetry remains unchanged. Exact PR head `2a32cd3ef915ff1c064bda49a0303e2a72cbbc04` passed **297 tests, 2 warnings** in run `34763827289`; squash merge `4c10b60c4ef290fc690d39a33c2d5e43d5eece7d` passed **297 tests, 2 warnings** on canonical-main run `34763920318`.

**Repaired rerun — PASSED**

The same preserved Room then ran Round `round_3f88ad9c33fa4079aec29364681749ae` against new input `  Alpha / Beta__99  ` after the PR #23 runtime repair.

Durable evidence shows:

- C alone consumed the Round; A/B remained unconsumed;
- registry `list` rediscovered `ascii_text_slug` as custom / lineage / version `1` with implementation SHA `3333ecd6...`, package SHA `af1ed410...`, and registration SHA `abfbeb96...`;
- `inspect` returned the same exact implementation/package/registration identities plus verification SHA `8eca83c2...`, four verified cases, and durable result fields `slug` / `length`;
- C created one workspace file for robust input transport, then the normal registered invocation completed successfully;
- durable capability evidence reported matching version and exact implementation/package/registration/verification identities, `ok:true`, `slug:"alpha-beta-99"`, and `length:13`;
- C FINISHed exactly `P4.4-CUSTOM-OK`;
- the one-turn Round closed normally with `mutual_finish`.

This closes the demonstrated live gap and P4.4 as a whole. The successful reuse proof depended on the already-host-bound immutable capability, not on recreating or reregistering the draft.

#### P4.5 — Rollover persistence / lineage inheritance
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED end to end — 2026-09-13  
**Decision:** D-022  
**Evidence:** E-039, E-040

Goal: when a Personal Room rolls over within the same continuing body of work, registered lineage-scoped custom capabilities remain discoverable and invokable at the exact inherited version unless deliberately retired or excluded. Historical Rooms continue to preserve the exact capability versions they used.

**P4.5a — lineage binding inheritance: COMPLETE / IMPLEMENTED / VERIFIED deterministically.**

Implemented behavior:

- direct registrations keep the existing schema-v1 Room binding and truthful original registration Room;
- a successor receives a schema-v2 inherited binding that retains the exact original registration SHA-256 and registration Room while naming the immediate predecessor Room and predecessor binding SHA-256;
- inherited bindings resolve the same immutable package, manifest, implementation, and verification identities; rollover does not republish, reverify, or manufacture a successor registration;
- predecessor binding bytes remain untouched;
- inherited bindings remain first-class through normal successor `list` / `inspect` / `invoke`;
- the rollover saga creates the exact successor binding set under protected operation-scoped staging and validates replay idempotently;
- failed/incomplete rollover removes successor/staged binding state along with the staged successor; fully provisioned restart recovery validates/reconstructs the same exact inherited binding set before finalization;
- multiple capabilities inherit deterministically, and later generations keep the original registration provenance while linking each successor to its immediate predecessor binding;
- CORE/custom collision checks remain enforced.

Verification: PR #24 exact reviewed head `888585749cbfe702080005d7211fbc79e758a7a7`; GitHub Actions run `34766802808`: **301 passed, 2 warnings**. Squash merge `f1f83357b78399718ed8910f2849763c6c2dbbbb` has the same Git tree as the reviewed/tested head; canonical-main run `34766882490`: **301 passed, 2 warnings**.

**Live rollover proof: COMPLETE / VERIFIED.**

Fresh source Room `room_8b85b75a868f4077bc44f465ee2d9439` registered lineage capability `normalize_ascii_label` version `1`, then rolled over to successor `room_d5d2462daff04c62bcf00468bf90606a`.

Live evidence established:

- the successor received schema-v2 binding `4a5e91e2c8c4fe47f24cf919fba9fee28597cd8535290b130b74c49bfc6632b9`, naming the original registration Room and immediate predecessor plus predecessor binding `e6386581c2bd1ebe63d8e427b90c7ea51474350b44d6bf1f8776e0d9dd3f9bc8`;
- successor registry `list` rediscovered the custom lineage capability, `inspect` preserved its verified identity, and normal registered invocation succeeded with the same version/implementation/package/registration/verification identities;
- the successful successor result was `normalized: "p4_5_live_lineage_verification"`, `length: 30`;
- no successor registration/republication event occurred;
- the predecessor is archived and sealed with a committed rollover record, and direct post-rollover inspection still shows the original schema-v1 binding SHA `e6386581...` and original registration identity unchanged.

One inline invocation attempt in the successor was rejected as malformed JSON and then retried successfully through the existing file-input transport; this did not alter capability identity or require ad hoc fallback.

P4.5 is closed. Personal/CORE promotion remains later work under D-022.


Repository baseline: canonical `main`. Exact current HEAD, hosted CI state, remote-ref agreement, and local working-tree state are intentionally **not maintained in this document**; inspect GitHub and local Git directly when those facts are consequential.

### I-006 — Early-triad default profiles missed D-020 migration
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-12  
**Evidence:** E-029

A live post-D-020 smoke Room exposed that the local database still held an older exact built-in A/B/C profile generation. PR #4 added the conservative `triad_profiles_v2` exact-hash migration while preserving non-matching custom content, Room overrides, archived Rooms, and sealed predecessors.

Post-repair local verification used a newly created Room. Its A/B/C `profile_snapshot` values contained the current D-020 instruction text, C was the sole starter, only C consumed Round context or recorded an outcome, C FINISHed with `C-ONLY-OK`, and the Round closed after exactly one agent turn. This verifies both local profile migration and C-only engaged-participant settlement.

I-006 is closed.


### I-004 — README permanent-triad documentation drift
**Work state:** COMPLETE  
**Reality / evidence:** OBSERVED ISSUE / VERIFIED — 2026-09-12; documentation repaired — 2026-09-13  
**Decision:** D-020

A2 found that the README's **First run** instructions still treated Agent C as optional for new Rooms even though D-020 and current runtime require every new Personal Room to start as the permanent A/B/C triad. The same legacy implication also appeared as `[agent C queue]` in the architecture diagram.

The README now states that C is included in every new Personal Room, that creation provisions distinct persistent A/B/C threads, retitles the C section to distinguish legacy two-agent upgrades from normal new-Room behavior, and removes the optional-C diagram notation. This was documentation-only cleanup; runtime behavior did not change.

I-004 is closed.


### A2 — Assurance Pass 2
**Work state:** COMPLETE  
**Evidence:** E-028  
**Result:** No material runtime GAP demonstrated

A2 assessed the intended post-D-020 architecture using fresh source/config inspection, exact-version/current deterministic test evidence, existing evidence records, and targeted reasoning. It did not launch new in-Room A/B/C exercises or opportunistic remediation.

Material results:

- repository/reproducibility/provenance — **GOOD**;
- agent identity and continuity — **GOOD**, with provider-side profile application remaining **NEEDS VERIFICATION** under I-003;
- execution serialization, stale-result protection, exact-turn recovery, and bounded execution lease — **GOOD**;
- permanent-triad coordination and settlement — **GOOD**;
- retry/usage-wall recovery — **GOOD**; the prior P3 exact-byte review caveat is retired by the A2 current-source review plus current exact-version deterministic tests;
- data integrity, event/delivery provenance, export completeness, and execution observability — **GOOD**;
- current Personal local privacy/exposure boundary — **GOOD**;
- structural operating-economics mechanisms — **GOOD**, but empirical post-D-020 usage efficiency remains **PARTIAL** because no new real-Room usage benchmark was run;
- intent/implementation alignment — **PARTIAL** because of I-004 README drift and because editable A/B profiles currently replace full developer instructions rather than being composed beneath a protected institutional layer. The latter remains a deferred design concern, not an A2 implementation task.

No finding requires repair before P4. See E-028 for evidence and limitations.



### D-020 — Permanent Personal triad / C-integration migration
**Scope:** [CORE + ROOM migration]  
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-12  
**Decision:** D-020  
**Evidence:** E-027

Implemented mandatory A/B/C creation for new Personal Rooms, C-first default Round initiation, direct A↔B selective communication with passive C readability, explicit legacy A/B upgrade behavior, triad rollover successors, engaged-participant settlement, and a mechanical integration-before-closure barrier for unread passive A/B MESSAGE material awaiting C integration.

Verification on the exact reviewed PR head passed **136 Python tests, 2 warnings** in GitHub Actions and **3 Playwright browser tests** locally. PR #3 squash-merged to canonical `main`; the merge tree exactly matched the reviewed/tested head tree. A post-merge push run exposed one race-prone legacy-upgrade test assertion; stabilization changed only that test assertion/comment plus documentation, and the subsequent canonical-`main` run passed **136 tests, 2 warnings**.

### P0 — Selective invocation
**Work state:** COMPLETE  
**Follow-up:** MONITOR  
**Reality / evidence:** IMPLEMENTED / HISTORICALLY VERIFIED — 2026-09-09

Implemented recipient-aware `invoke_targets`, durable readable-vs-runnable delivery semantics, passive backlog behavior, settlement compatibility, and routing telemetry while preserving serialized execution and private authorization.

Historical verification: **111 passed, 2 warnings**, SQLite `quick_check` OK. A real Room exercise used **5 purposeful invocations** and avoided **4 legacy fan-out invocations**.

Monitor for under-invocation of useful peer challenge; do not optimize invocation count at the expense of correctness or collaboration.

### Supporting repair — Retry / Agent Error observability
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / HISTORICALLY VERIFIED — 2026-09-09

Retryable failures are shown as interrupted attempts and reconciled to recovery when later success is correlated. Terminal Agent Error is reserved for exhausted/non-recoverable failure.

Historical full-suite verification: **116 passed, 2 warnings**, SQLite `quick_check` OK.

### P1 — Operational token/usage-efficiency doctrine
**Work state:** COMPLETE  
**Follow-up:** MONITOR — wording may still be deliberately refined

Current work uses the settled practical hierarchy of avoiding unnecessary model calls, invoking only useful cognition, loading only relevant context, preferring deterministic procedures for stable work, scaling reasoning to consequence, and treating output verbosity as a lower-order optimization.

The exact wording of the operational definition remains subject to deliberate refinement and must not be silently hardened into constitutional interpretation.

### P2 — Persistent-context / compaction economics
**Work state:** COMPLETE  
**Follow-up:** MONITOR  
**Reality / evidence:** IMPLEMENTED / HISTORICALLY VERIFIED — 2026-09-09

The pre-compaction baseline ratchet was confirmed and repaired with a deferred post-compaction growth baseline. Historical full-suite verification: **119 passed**, SQLite `quick_check` OK.

### P3 — Usage-wall delayed continuation
**Work state:** COMPLETE  
**Follow-up:** MONITOR  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-12

A positively identified usage wall schedules durable continuation for the same agent/thread at the provider retry time + 60 seconds, with restart survival, serialized release, lifecycle cancellation, and repeated-wall rescheduling.

Historical verification: **10 focused tests passed; 127 full-suite tests passed**; production and fresh-migration database integrity checks were OK.

A2 re-reviewed the current exact source and mapped the focused continuation/restart/reschedule/cancellation tests to the implementation. The former exact-byte review caveat is retired; see E-028.

## Ordered next work

### EF-1 — Reproducible dependency/environment setup
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-10

Clean pip/venv installation is now constrained by `constraints-test.txt`, which records the known-good application/test dependency set while `pyproject.toml` retains broader supported ranges. The merged repair restored green hosted CI with **129 passed, 2 warnings**. No `uv` migration was needed.

### EF-2 — Canonical full-test command
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-10

Canonical routine command: `python -m pytest -q`. Clean-environment verification collected and passed **129 tests**. `test-transcript-stability.ps1` remains a separate specialized browser check.

### EF-3 — Minimal CI
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED — 2026-09-10

GitHub Actions runs the canonical Python suite on pushes to `main` and pull requests targeting `main`, installing through `constraints-test.txt`. The latest hosted verification on canonical `main` (`34abd391ecbb861d7661541e4a716a5152a2049d`) completed successfully with **130 passed, 2 warnings**.

### P4 — Deterministic Room and agent capabilities
**Work state:** COMPLETE  
**Reality / evidence:** IMPLEMENTED / VERIFIED end to end — 2026-09-13

P4.1 through P4.5 are complete: deterministic assertions, registry/discovery, the minimal CORE library, agent-created custom capability registration/verification, and lineage rollover inheritance have all been verified end to end. P4 is closed. Personal/CORE promotion remains later work under D-022 and requires separate explicit prioritization.

## Approved planned development

### Personal daily usage pacing limit
**Work state:** PLANNED  
**Reality:** DECIDED / NOT IMPLEMENTED  
**Decision:** D-019  
**Feasibility evidence:** E-026  
**Scheduling:** approved for development; P4 is complete, but this item has not yet been selected as the next active implementation slice.

Core approved behavior:

- user-configurable daily limit expressed as a percentage of the weekly Codex usage allowance;
- default daily limit: **1/7 of the weekly allowance (~14.3%)**;
- use Codex's structured account rate-limit/usage meter as the pacing source;
- stop initiating new model work after the configured daily allowance has been reached according to the latest available reading;
- allow already-running work to finish, accepting possible small overshoot;
- provider enforcement remains authoritative.

Implementation details such as warning thresholds, UI presentation, carry-forward semantics, daily-period/time-zone semantics, polling cadence, and exact SDK/app-server integration remain open until implementation design.

## Maintenance issues

### I-003 — B SDK-thread/profile continuity residue
**Reality:** OBSERVED ISSUE — historical provider-side residue; current recurrence not demonstrated  
**Evidence qualifier:** NEEDS VERIFICATION  
**Priority:** LOW  
**Fresh evidence:** 2026-09-12 A2 source/test inspection

A2 found that the current implementation repairs only the known stale pair-era A/B default/snapshot hashes in live unmodified Rooms, preserves archived/sealed/custom state, and records the migration once. Adapter/runtime tests show that a targeted profile rebind evicts only the selected cache entry, resumes the same persistent SDK thread ID with the current developer instructions, fails closed if the SDK returns another identity, and quarantines the worker on a failed resume without changing the durable thread ID.

The remaining uncertainty is narrower than the original observation: current deterministic evidence does **not** independently prove that the provider-side persistent thread has actually adopted the replacement developer instructions after same-thread resume. The runtime's own audit event therefore says instruction application “awaits participant verification.” Keep I-003 open as low-priority **NEEDS VERIFICATION** unless A2 later determines that a live provider-side check is worth its model cost.

## Deferred work

Keep these behind Assurance Pass 2 unless the human principal changes priorities:

- archive retrieval/indexing;
- broader deterministic-tooling expansion;
- scalability/data-integrity work beyond demonstrated issues;
- collaboration-quality experiments;
- provider-neutral implementation;
- broader productization;
- Enterprise workforce features;
- packaging/funding preparation;
- nonessential UI refinement.

## Open questions

No high-priority open question blocks the current personality-design work. I-003 remains low priority and needs provider-side participant verification only if the value justifies a live model check. I-004 is closed. The former protected-institutional-layer design concern is resolved by D-023 / E-041; the open question is now the exact content and empirical differentiation quality of the three standard default personalities.
