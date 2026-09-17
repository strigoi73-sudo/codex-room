# Codex Room — Development Control

**Last updated:** 2026-09-17  
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.  
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** Engineering Foundation, A2, P4, A3 remediation, and I-015 are complete. Work-model v2 with `provider_context_mode="assignment_thread"` is the public production path. Legacy Rooms were deliberately cleared rather than migrated.
- **What just changed?** Ordinary Common Cause use first exposed a bounded transaction-contract/retry defect, repaired by PR #108. The subsequent Common Cause implementation baseline then exposed expensive coordination topology: dependent implementation/verification was run concurrently, corrective assignments failed to produce substantive work, and large fallback execution accumulated on C. PR #109 added dependency-aware sequencing plus context-aware fallback allocation; PR #110 tightened the fallback rule so substantial tool-heavy fallback normally moves to a fresh bounded peer even when C is operating in a child assignment.
- **Verification state:** PR #110 exact head `da4e47efb8d6e350503325f7521a2e9e56735bc1` passed `git diff --check`, the focused C-structural regression, `verify-fast.cmd`, exact-head recheck, blob-identity recheck, and tracked-tree cleanliness. PR #110 merged to canonical `main` as `ad9e46310068c07facea34ef0de76456881cd271`; canonical `main` carries the verified `personalities.py` blob `6fbe105abc8684173bd05878eac5f46c2c6ece25`.
- **What is blocked?** D-019 daily usage pacing remains blocked on unresolved mixed subscription-allowance / purchased-credit semantics. No other high-priority blocker is known.
- **What is next?** Run the bounded **fresh-Room Common Cause rerun** under the original staged protocol. Stage 1 should establish benchmark continuity/design compatibility; the implementation Round is the primary naturalistic test of PR #109/#110 sequencing and fallback behavior.
- **What are we deliberately not doing?** No retroactive rewrite of existing Room snapshots; no fourth persistent agent; no broad v2 redesign; no new memory/index architecture; no personality calibration; no automatic model router; no adjacent maintenance investigation unless the rerun or ordinary use demonstrates a concrete problem.

## Current Focus

### Common Cause coordination-economics rerun
**Work state:** IN PROGRESS — structural remediation merged; fresh-Room rerun next  
**Reality:** PR #109/#110 IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED; behavioral compliance NOT YET VERIFIED  
**Decision:** D-035  
**Evidence:** E-124  
**Scope:** [ROOM naturalistic evaluation of current CORE instructions]

#### Why this rerun exists

The original Common Cause implementation succeeded functionally and passed its 9/9 unit tests, but the coordination/economic shape was poor:

- 16 Room executions;
- 33 underlying provider responses;
- 17 native tool calls;
- **1,511,456 raw execution tokens** in the successful implementation Round;
- C alone accounted for **1,041,653** tokens;
- the failed A2/B2 corrective assignments cost about **100,683** tokens;
- C's subsequent fallback consumed about **889,673** tokens;
- the conservative avoidable total from those two paths is about **990,356 tokens / 65.5%** of the implementation-Round total.

The causal coordination concern was not simply “C used too many tokens.” The observed topology was:

1. C delegated implementation to A and verification to B concurrently even though useful verification required the artifact A had not yet produced.
2. B could only return a verification plan.
3. C later issued A2/B2 corrective work concurrently; both settled without producing the needed correction/audit.
4. C then absorbed substantial editing/testing itself on an already large coordinator context.

The desired general topology is dependency-driven rather than Common-Cause-specific:

`produce prerequisite artifact/result -> verify exact result -> integrate`

If correction is needed:

`identify bounded defect -> fresh capable worker corrects -> verifier checks exact corrected bytes -> integrate`

Independent work should still run in parallel. The policy does not hard-code A as implementation or B as verification.

#### Implemented structural repair

PR #109 added two C-only protected structural rules:

1. determine whether concurrent assignments can each produce useful work without another assignment's result; parallelize genuinely independent work and sequence dependent work;
2. after failed delegated implementation/correction/investigation, consider moving substantial fallback to a fresh bounded peer with less accumulated context instead of loading it onto C.

PR #110 tightened the second rule after review found the first wording too permissive. Current C structure now says that when delegated implementation/correction/investigation fails to produce needed work, **or when fallback reaches C because another assignment failed or settled without producing it**, C should normally place substantial tool-heavy execution in a fresh bounded peer assignment rather than execute it itself. This applies whether C is in the root coordination assignment or a peer-created child assignment. Direct C execution remains allowed for demonstrably small expected execution/context cost, urgency, integration-inseparable work, or when no fresh peer is likely to do it reliably at lower total cost. Small-looking code/file changes are not assumed to be cheap model executions.

These rules are forward-looking for freshly composed Rooms. Existing Room snapshots are not retroactively rewritten. Rollover successors continue to inherit predecessor instructions unless later changed deliberately.

#### Exact PR #110 verification

Reviewed head:

`da4e47efb8d6e350503325f7521a2e9e56735bc1`

Base:

`b708f31faf7ee5c292c2e49efb632500e5f1a83b`

Verified file set:

- `codex_room/personalities.py`
- `tests/test_c_structural_coordination.py`

Verified blobs:

- `personalities.py`: `6fbe105abc8684173bd05878eac5f46c2c6ece25`
- structural test: `590a11e2616c7ac69d17c12a756b8b3dee094285`

Local exact-head verification passed:

- expected head == final head;
- expected base ancestry;
- exact two-file change set;
- `git diff --check`;
- focused C structural regression;
- `verify-fast.cmd`;
- post-verification head/blob identity;
- tracked tree clean.

`verify-fast.cmd` reported Linux focused core PASS, Windows dependency synchronization PASS, **118 Windows portability tests PASS**, and **3 browser transcript tests PASS**. PR #110 then merged as `ad9e46310068c07facea34ef0de76456881cd271`; canonical `main` retains the exact verified `personalities.py` blob.

#### Rerun controls

Use a **fresh Room** created after PR #110. Do not reuse the historical Common Cause Room.

Hold constant where current CORE permits:

- title/topic may identify the rerun, but agents must not be told the baseline failure, token totals, or desired topology;
- work-model version 2;
- `provider_context_mode="assignment_thread"`;
- `max_turns=16`;
- `max_consecutive_passes=3`;
- `inactivity_seconds=1800`;
- starter C;
- required contributors empty;
- ordinary current default profiles / protected instructions;
- empty fresh workspace before implementation;
- no old Common Cause files preloaded.

Use the original staged prompts rather than rewriting the task to force the new behavior. Record any necessary deviations explicitly.

#### Stage 1 benchmark boundary

Stage 1 is design-only. The historical baseline used four model executions and **98,996 raw execution tokens**. The new Stage 1 is primarily a continuity/compatibility check: confirm that the rerun still produces a materially compatible Common Cause design and that no unrelated behavior change makes the historical Stage-2 follow-up nonsensical.

Do **not** over-interpret Stage 1 as the causal test of PR #109/#110; dependency sequencing and fallback allocation may not be meaningfully exercised in design-only work.

If the fresh Stage-1 design remains materially compatible, continue with the exact historical Stage-2 follow-up. If it diverges enough that the historical Stage-2 prompt no longer fits, stop and make an explicit benchmark choice rather than silently editing the protocol.

#### Primary implementation-round hypotheses

1. **Dependency-aware sequencing:** verification of an artifact should normally wait for artifact existence unless the verifier has useful independent pre-artifact work.
2. **Fallback allocation:** failed delegated work should not automatically cause substantial tool-heavy execution to accumulate on C's coordinator context; a fresh bounded capable assignment should be preferred when it is reliably cheaper in total context/execution cost.
3. **Quality preservation:** lower usage is not a success if implementation/test quality degrades.
4. **Economics:** collect exact execution count, provider-response count, tools, per-agent usage, and task topology. The ~521k counterfactual from the earlier analysis is a reference, not a hard acceptance threshold.

The deterministic structural regression proves the instruction is composed correctly. It does **not** prove model behavioral compliance. The rerun is required before calling the coordination-economics problem behaviorally resolved.

## Completed major program state

### I-015 — Task-transaction stabilization redesign
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / VERIFIED / PUBLIC DEFAULT / LIVE SMOKE PASSED  
**Decisions:** D-030 through D-034  
**Evidence:** E-092 through E-123

The production path is work-model v2 with Assignment-scoped provider context. Stage A established Task/Assignment/Join mechanics; Stage B added structured `EVIDENCE`; Stage C added assignment-scoped context plus bounded `HISTORY`; Stage D passed the ten-task viability gate at 9/10 quality with all coordination/robustness/economic thresholds satisfied; D-034 activated v2 publicly; legacy Rooms were deliberately cleared rather than migrated.

PR #108 is a bounded post-close ordinary-use repair for transaction contract/retry bounds. It does not reopen I-015.

### P4 — Deterministic Room/agent capabilities
**Work state:** COMPLETE  
**Reality:** IMPLEMENTED / VERIFIED end to end  
**Decision:** D-022  
**Evidence:** E-030 through E-040

CORE capability registry/discovery, standard library, custom authoring/verification/registration, safe invocation, and lineage rollover inheritance are implemented and verified. Personal/CORE promotion remains later work only if demonstrated useful.

### A3 remediation
**Work state:** COMPLETE  
**Evidence:** E-065 through E-091

Environment/document truth, repository hygiene, runtime provenance, maintenance health, model-economy investigation, authorized source inspection, SDK-subagent bypass, deterministic retrieval economy, persistent-data maintenance, verification-platform cleanup, and Windows restart QOL were addressed in bounded slices. Continue naturalistic monitoring rather than reopening broad audits.

## Approved planned development

### D-019 — Personal daily usage pacing
**Work state:** DEFERRED  
**Reality:** DECIDED / NOT IMPLEMENTED  
**Evidence:** E-026

The intended default remains one-seventh of the weekly allowance (~14.3%), using structured provider usage/rate-limit data rather than Room token estimates. Implementation remains blocked until mixed subscription allowance versus purchased-credit semantics are understood well enough to define which pool is paced and how multiple pools interact.

## Maintenance / monitor items

### I-003 — Provider-side instruction adoption after same-thread profile rebind
**Work state:** MONITOR  
**Reality:** NEEDS VERIFICATION / current recurrence not demonstrated

Current deterministic evidence verifies the local rebind mechanism and fail-closed identity behavior, but not independent provider-side proof that replacement developer instructions took effect on the resumed same thread. Do not spend a dedicated paid test unless ordinary use makes the uncertainty consequential.

### Naturalistic continuation economy
**Work state:** MONITOR

E-086 demonstrated that the continuation-economy repair can radically reduce tool-loop replay on a controlled fixture. E-090 showed broader source work can still become expensive. The current `EVIDENCE` interface and assignment-scoped production context further change that cost surface. Continue to record concrete expensive recurrences; do not launch synthetic benchmark matrices.

## Deferred work

Keep these deferred unless new evidence or explicit principal direction reprioritizes them:

- archive indexing/embeddings/broad summarization beyond bounded `HISTORY`;
- automatic/dynamic model routing;
- broader deterministic-tooling promotion without demonstrated reuse;
- stronger per-capability OS isolation;
- shareable/redacted exports;
- large-module refactors/storage optimization;
- broader productization/packaging/funding;
- Enterprise workforce features;
- provider-neutral implementation work;
- nonessential UI refinement.

## Open questions

No high-priority conceptual question blocks the current Common Cause rerun. The immediate question is empirical: **do the merged PR #109/#110 C structural rules actually change fresh-Room dependency sequencing and fallback allocation enough to avoid the previously observed coordination/context-cost failure while preserving implementation quality?**

After the bounded rerun, resume ordinary Codex Room development/use unless its evidence demonstrates another concrete defect or the principal explicitly reprioritizes work.
