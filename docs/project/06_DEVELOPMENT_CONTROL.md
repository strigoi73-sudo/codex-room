# Codex Room — Development Control

**Last updated:** 2026-09-20
**Scope:** Volatile current focus, ordered priorities, known issues, planned work, and unresolved questions.
**Freshness:** High volatility. Replace dated state promptly when newer evidence or user direction exists.

## Operator summary

- **Where are we?** I-020 Stages A, B, and D are **COMPLETE / VERIFIED**. Native Codex skills work inside Rooms, the protected policy governs economical skill use, and Room-local skills now survive Room rollover with exact-byte/tree-hash provenance.
- **What just changed?** A natural three-agent Room demonstrated runtime discovery of `skill-creator`, `spreadsheets`, and `documents`; autonomous spreadsheet-skill selection; explicit document-skill use; Room-local Skill Creator authoring with a deterministic helper; runtime discovery of the created skill; and cross-agent reuse. See E-153.
- **Verification state:** Stage A natural Room evidence is **VERIFIED** (E-153). Stage B is **VERIFIED / MERGED** (E-154). Stage D exact implementation head `e4391ec18daca81038bf2d8d3e50c78ca3b22ddf` is **VERIFIED** and merged through PR #159 as canonical squash commit `7740067fcecf31c0cf7b417365a47a0814a6bef5` (E-155). The Stage A Room also exposed severe execution cost: about 5.28M recorded execution tokens total.
- **What is blocked?** Nothing blocks ordinary Codex Room use. Skill use is functionally available natively; the current work is policy and persistence discipline, not a missing invocation mechanism.
- **What is next?** Proceed to I-020 Stage E: reconcile D-022 against the now-verified native-skill + Skill Creator + lineage-persistence boundary, changing the settled decision only if the evidence requires an additive or superseding clarification.
- **What are we deliberately not doing?** No Codex Desktop/TUI command palette, no parallel Room skill registry, no automatic global/user-scope skill writes, no SkillInput bridge without evidence, no immediate rewrite of D-022, no fourth persistent agent, and no Codex built-in subagents.

## Current focus

### I-020 — Codex skill integration and Skill Creator adoption

**Scope:** [CORE + ROOM behavior, only where native Codex support proves insufficient]

**Work state:** IN PROGRESS

**Reality / evidence:** Stages A-B-D IMPLEMENTED / VERIFIED; Stage C NOT WARRANTED; Stage E PLANNED

**Origin:** principal selection after I-019 / D-041 cleanup

**Objective:** make Codex's existing skill ecosystem the first-line reusable workflow layer for A/B/C. Agents should be able to use relevant predefined skills on their own initiative, the principal should be able to direct use of a named skill, and agents should be able to use Skill Creator for reusable Room-local workflows. Codex Room's deterministic capability registry remains the stronger promotion tier for mechanisms that require typed contracts, exact provenance, declared side effects, durable telemetry, or lineage guarantees.

**Current verified design facts:**

- Codex Room already calls App Server `skills/list` for the active Room workspace and exposes sanitized enabled-skill inventory through Status & Tools.
- Current Room turns use the official Python SDK `thread.turn(...)` path with plain-text input.
- The current Python SDK also supports structured `SkillInput(name, path)`, and App Server recommends a structured `skill` input for explicit invocation; plain `$skill-name` text remains a supported fallback.
- Skill Creator can create a skill containing `SKILL.md`, optional references/assets, and deterministic helper scripts. Its packaging/structural validation is not equivalent to Codex Room's registered-capability verification/provenance contract.
- A Room agent runs with `workspace_write`, so Room-local skill creation should be bounded to the Room workspace (for example `.agents/skills/...`) unless the principal separately authorizes broader user/global scope.
- Room rollover preserves valid Room-local Codex skill packages under `.agents/skills/<name>/SKILL.md` through the existing atomic staging path. Inheritance is lineage-local, exact-byte/tree-hash verified, bounded, and excludes unrelated workspace or `.agents` state; no automatic user/global promotion occurs.
- Codex built-in subagents remain disabled. Any Skill Creator recommendation for independent agent review must map to the existing A/B/C organization rather than re-enabling Codex subagents.

**Implementation sequence:**

**Stage A — Native capability proof, no CORE changes. COMPLETE / VERIFIED (E-153).** The natural Room demonstrated representative predefined-skill discovery, autonomous `spreadsheets` selection, explicit `documents` use, Skill Creator authoring of Room-local `.agents/skills/i020-line-normalizer/` with a deterministic helper, resumed-runtime discovery of that skill, and cross-agent reuse by a different peer. No CORE bridge was needed. Native invocation provenance remains weaker than Codex Room deterministic-capability provenance, but that did not block successful use. The exercise was operationally expensive: about 5.28M recorded execution tokens total, dominated by a 4.33M-token Sol/Medium Skill Creator/document assignment.

**Stage B — Agent policy. COMPLETE / IMPLEMENTED / VERIFIED (E-154).** The protected guidance now tells agents to use an existing enabled Codex skill when it materially fits, check existing skills before inventing reusable workflow/software, use native Skill Creator for genuinely missing reusable workflows, keep agent-created skills Room-local by default, allow bounded skill-local deterministic helpers, require explicit principal authorization for user-global/administrator-scope skill changes, preserve the ban on Codex built-in subagents, and promote machinery into the Codex Room deterministic registry only when its stronger guarantees earn the added governance cost. A cost guard explicitly says a heavyweight skill workflow must earn its cost unless the principal requests it. No parallel skill catalog or SkillInput bridge was added.

**Stage C — Explicit invocation bridge. NOT WARRANTED BY CURRENT EVIDENCE.** Stage A showed successful autonomous selection, explicit named-skill use, Skill Creator authoring, runtime discovery, and cross-agent reuse without a Room-specific bridge. Keep the official Python SDK `SkillInput(name, path)` path as a future fallback only if later evidence exposes a real reliability or latency gap. Do not build a slash-command parser or copy the Desktop/TUI popup.

**Stage D — Skill persistence. COMPLETE / IMPLEMENTED / VERIFIED (E-155).** Valid direct packages under `.agents/skills/<name>/SKILL.md` are now lineage-local Room skills carried through the existing atomic rollover staging path. Only package files are copied; unrelated workspace files, unrelated `.agents` state, and directories under `.agents/skills` without a direct regular `SKILL.md` remain excluded. Source and destination skill trees reject symlinks/special entries, inheritance is bounded to 1,024 files / 64 MiB, copied bytes are rehashed before exposure, and rollover events record skill names/counts plus a deterministic tree SHA-256. Skills remain Room-lineage scope; no global promotion occurs automatically.

**Stage E — Reconcile D-022 after evidence.** Only after Stages A-D establish the real boundary, decide whether D-022 needs an additive/superseding decision. The likely hierarchy to evaluate is: **use existing Codex skill → create skill with Skill Creator → use skill-local deterministic script when sufficient → promote to registered Codex Room capability only for stronger institutional guarantees**. Do not alter D-022 merely from architectural analogy.

**Stage F — Acceptance and closeout.** Verify the chosen exact implementation bytes with the repository-standard local gate plus one bounded naturalistic Room acceptance. Record which predefined skill was used, whether invocation was autonomous or principal-directed, whether Skill Creator produced a usable Room-local skill, whether another agent could use it, whether any deterministic helper executed, and whether continuity/promotion behavior matched the selected policy.

**Acceptance target:**

- A/B/C can use a relevant predefined Codex skill without user micromanagement when the task naturally calls for it.
- The principal can direct a specific skill without requiring a copied Desktop/TUI command palette.
- Skill Creator can produce a bounded Room-local skill and, when appropriate, a deterministic helper that another Room agent can actually use.
- Skill creation does not silently escape Room scope or enable Codex built-in subagents.
- Existing deterministic capabilities remain available and are used as the stronger governed tier rather than duplicated by default.
- Any implemented rollover continuity preserves the exact intended skill bytes/provenance.

**Stop discipline:** stop after each stage if native Codex behavior already satisfies the need. CORE work is justified only by an observed gap. Do not manufacture a generic skill manager, new persistent agent, or parallel plugin/tool ecosystem.
### Post-I-019 cleanup — remove Codex host-command catalog exposure

**Scope:** [CORE + ROOM UI]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / VERIFIED

**Decision:** D-041

The principal reviewed the official Codex command inventory and concluded that it is primarily specific to Codex Desktop/TUI and coding/session management rather than a useful Codex Room product surface. The completed cleanup removes the exact-runtime command-catalog parser/cache, its dedicated API endpoint, its Status & Tools payload/card, and catalog-specific tests. The broader Status & Tools surface remains: current work, A/B/C state/economics/context guidance, Room-native deterministic capabilities, inherited workspace/command execution, and safely inspectable web-search, skills, MCP, apps/connectors, and plugins.

App Server runtime identity normalization remains because runtime provenance is useful independently of any command catalog. Skills evaluation is explicitly back-burnered and is not part of this cleanup.

**Verification closeout:** exact implementation head `d77e020588cf548580937a146877a15e7a76f5f4` passed the repository-standard fast gate and exact-diff review. See E-152.

**Stop condition:** met. The catalog product surface is removed and no replacement command surface or dispatcher was introduced.

### I-019 — Human-facing capability visibility

**Scope:** [CORE + ROOM UI]

**Work state:** COMPLETE

**Reality / evidence:** IMPLEMENTED / VERIFIED

**Origin:** I-018 / E-149

**Goal achieved:** Codex Room exposes a compact, read-only **Status & Tools** view that lets the principal understand current Room work and major Room-native/inherited Codex capability classes without requiring knowledge of internal database tables, transaction actions, SDK configuration, or Codex Desktop host controls.

**Implemented first-release surface:**

- current Round / Task / Assignment state and active objective;
- A/B/C lifecycle state, work ownership, current-or-most-recent model/reasoning evidence, bounded queue/processing state, and recent execution economics where recorded;
- C coordinator-context guidance derived from existing context economics;
- Room-native deterministic capability inventory;
- inherited workspace-file and command-execution classes;
- safely inspectable Codex web-search, skills, MCP, installed apps/connectors, and plugins inventory from the active App Server;
- explicit **available / interaction required / unavailable / unknown** truth classifications rather than assuming configured features are usable;

**Safety / architecture boundaries preserved:**

- first release is read-only and reuses authoritative Room state plus existing App Server/configuration APIs;
- secrets, tokens, private account identifiers, arbitrary MCP schemas/payloads, filesystem paths, and hidden reasoning are not exposed;
- direct model/reasoning overrides that bypass D-039 remain absent;
- Codex built-in subagents remain disabled;
- OAuth/approval/elicitation bridges, attachments, browser/computer use, worktrees, terminal, diff/review UI, and blanket Desktop host parity remain outside I-019.

**Verification closeout (E-151):** the pre-cleanup I-019 implementation passed the repository fast verifier and natural rendered-UI acceptance for Current work, A/B/C and economics, Room-native capabilities, inherited capability classifications, sanitization, read-only Refresh behavior, and the then-present host-command catalog. D-041 now supersedes only that catalog portion; the cleanup requires fresh exact-byte verification before it can be called verified.

**Stop condition:** met. I-019 ends here. Completing it does not automatically authorize or start the next roadmap stage.

### Post-I-018 human-facing capability roadmap

**Status:** principal-approved sequence; later implementation stages remain gated by evidence.

The governing product rule for this sequence is:

> **Do not build a new Codex Room mechanism when the underlying Codex/App Server capability already exists and can be safely exposed or reused.**

Proceed in this order:

1. **Expose what already exists — I-019 Status & Tools. COMPLETE.** Current organizational state, model/economics data, Room deterministic capabilities, and inherited/configured Codex tool availability are now visible through the verified read-only surface.
2. **Empirically verify inherited tools through ordinary work.** After I-019, run a small practical Room exercise that lets C use tools naturally. Verify local file work, command execution, web search, and any actually configured skill/MCP/app capability without manufacturing expensive benchmark traffic. Treat a capability as naturally usable only when runtime evidence supports it.
3. **Add a bounded tool-interaction bridge only when demonstrated necessary.** If an inherited MCP/app/plugin is blocked because it needs human OAuth, approval, account selection, or elicitation, implement the smallest safe principal interaction path required by that demonstrated case. Do not prebuild a generic orchestration subsystem in anticipation.
4. **Add first-class rich attachments.** Provide a principal-facing path to attach files/images directly to Room work with clear Room/workspace provenance and availability to agents selected by C. This is the next generally useful input expansion after visibility/tool access is understood.
5. **Run a real-use campaign before larger host work.** Use Codex Room for several actual objectives across research/decision support, attached-material work, multi-stage noncoding work, and software work. Judge value by whether the Room materially reduces principal effort or improves outcomes versus an ordinary single-agent conversation. Record recurring friction; do not manufacture feature demand.
6. **Evaluate browser/computer use only if real-use evidence justifies it.** A shared visual browser/computer-use host may materially expand general-purpose value, but it is a larger authority, safety, provenance, and UI integration. Begin that work only if prior practical use demonstrates that search/tool access is insufficient.

**Explicitly deferred pending demonstrated need:** blanket Desktop host-control parity, integrated human terminal, Desktop-style worktrees, Desktop diff/review UI, side chats, Room/thread forks, and a mechanically enforced Plan mode.

**Roadmap stop discipline:** each stage is independently bounded. Completing one stage does not automatically authorize the next implementation. Preserve working systems and stop whenever sufficient evidence says a proposed addition does not earn its complexity.

### I-018 — Codex Desktop ↔ Codex Room capability audit

**Scope:** [CORE / ROOM product capability audit]

**Work state:** COMPLETE

**Reality:** EXPLORATORY AUDIT COMPLETE / NO IMPLEMENTATION AUTHORIZED

**Objective:** determine what useful work current Codex Desktop can do that current Codex Room cannot, with special attention to whether Codex Room is failing to expose capabilities already present in the embedded Codex SDK/runtime.

**Questions to answer:**

- Which practical Codex Desktop capabilities are properties of the underlying Codex agent/runtime and are therefore already usable by A/B/C?
- Which capabilities exist underneath Codex Room but are hidden, discouraged, or lack a convenient human-facing surface?
- Which Desktop host commands are UI shortcuts for behavior Codex Room already provides through a different mechanism?
- Which Desktop capabilities are genuinely absent from Codex Room and would materially expand ordinary non-test use?
- Which Desktop features are intentionally incompatible with Room architecture or primarily coding-specific and therefore should not be copied?

**Method:**

1. establish the current Codex Desktop capability/host-command surface from current official OpenAI documentation;
2. inspect canonical Codex Room source and runtime configuration to establish what A/B/C can actually access and what the observer UI/API exposes;
3. prefer deterministic source/docs evidence; use at most bounded empirical probes only where material capability status remains ambiguous;
4. classify each relevant capability as **INHERITED / AVAILABLE BUT HIDDEN / ROOM EQUIVALENT / GENUINELY MISSING / INCOMPATIBLE OR OUT OF SCOPE**;
5. distinguish agent capability from observer/UI convenience so a missing host command is not mistaken for a missing underlying capability;
6. identify only demonstrated product gaps whose benefit could plausibly exceed their implementation/maintenance cost.

**Result:** E-149 records the completed matrix. The principal finding is that **Codex Room is not a reduced text-only Codex engine**: A/B/C run on persistent official Codex SDK/App Server threads with `workspace_write`, native command/file tooling, normal Codex configuration inheritance, and Room-specific deterministic capabilities. Codex built-in subagents are deliberately disabled because A/B/C and Room transactions own multi-agent organization.

The missing Desktop command palette is primarily a **host/UI gap**, not proof that the underlying agent capability is absent. Current Room composer/API sends observer text as ordinary Room messages and has no host-command parser.

**Important classifications:**

- **INHERITED / config-dependent:** workspace file work, shell/command execution, persistent Codex threads, hosted web search unless disabled by Codex configuration, and configured MCP/App Server tool availability where authentication/interaction requirements are already satisfied.
- **AVAILABLE BUT HIDDEN / incomplete host surface:** Room status/economics/model/context data; configured MCP/tool inventory; skills/apps/plugin inventory and explicit selection; some App Server thread controls. Interactive OAuth, elicitation, and generic tool-approval UX are not currently provided by the Room observer surface.
- **ROOM EQUIVALENT:** model/reasoning control through D-039; context compaction/refresh; Round/Task objective state; persistent agent profiles; A/B/C organization in place of built-in Codex subagents; bounded Room history; independent verifier delegation in place of a Desktop review shortcut.
- **GENUINELY MISSING HOST CAPABILITIES:** the Desktop built-in visual browser/computer-use surface, rich observer attachments/input UX, integrated human terminal, Desktop diff/review UI, and Desktop-managed worktrees. Some are coding-specific; browser/attachments have broader general-purpose implications.
- **DO NOT COPY FOR PARITY ALONE:** host command syntax itself, direct `/model` or `/reasoning` overrides that bypass D-039, built-in Codex subagents, or host utilities such as product feedback/pet commands.

**Candidate product work, pending principal choice:**

1. **Room status + tools visibility** — expose current Round/Task/Assignment state, agent/model/economics data, and configured skill/MCP/app availability in one human-facing surface. Prefer reusing App Server APIs rather than reproducing tool registries.
2. **Tool interaction bridge** — only if MCP/plugins become important in ordinary use, add the missing human authorization/authentication/elicitation path needed for tools that cannot run unattended.
3. **Rich attachments** — give the principal a first-class way to attach files/images to Room work instead of relying on filesystem placement or text-only instructions.
4. **Browser/computer-use host** — potentially high general-purpose value, but a materially larger product/authority/safety integration than exposing inherited tools.
5. **Plan-only or review-specific modes** — consider only if ordinary use demonstrates that natural-language constraints plus existing verifier/transaction mechanics are insufficient.

**Stop condition satisfied:** I-018 made no runtime change and authorizes none. Do not implement blanket host-command parity or any candidate above until the principal explicitly selects it.

### I-017 — Dynamic C cognition and Task-scoped exceptional approval

**Scope:** [CORE + ROOM UI]

**Decision:** D-039

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED / NATURALISTICALLY ACCEPTED

**Observed gap:** local execution-history inspection of the most recent 200 Agent C execution records found zero model/effort transitions; every execution used `gpt-5.6-terra` / high. Source inspection showed why: C-selected execution configuration existed only for delegated peer Assignments while C's own root work used the Terra/high compatibility fallback.

**Authorized behavior:** C may dynamically choose Low/Medium/High across Luna, Terra, and Sol for its own subsequent root-Assignment executions. Peer delegation receives the same ordinary nine-configuration set. C-only Sol/XHigh or Sol/Max requires private principal approval that raises the exact current Task's cognition ceiling; approval expires at the Task boundary and does not authorize peers. Sol/Ultra, Astra, and GPT-5.5 remain unavailable.

**Implemented and verified:** canonical `main` now persists `tasks.c_cognition_ceiling` with ordinary default `sol-high`; adds structured `next_self_config` and `requested_task_cognition_ceiling`; reuses `CONSULT_PRINCIPAL` for a private structured approval/decline exchange; records approval in durable private events; resumes the same C Assignment at the approved configuration when authorized; resets successor Tasks to the ordinary ceiling; and reconciles restart recovery against durable Assignment state so an old provider execution is resumable only while its Assignment remains `running`. Exact feature head `b498709ed30541d7a673b245f19a9021eca98ee5` passed the repository-standard local gate and squash-merged as `1806a7a16e1477f9dbe88515100f787c0389c709`.

**Naturalistic acceptance:** PASS for both required gates. Ordinary self-switching passed in Room `room_b91f31f8cccc4d6c8eb26c4c008854dd`: C moved from Terra/High to Luna/Low on the same Assignment while A/B remained unused and the Task retained the ordinary `sol-high` ceiling (E-147). Exceptional cognition passed in Room `room_c5c830d0cf5443608c09e476e89f41dc`: private Task-scoped approval raised the first Task to `sol-xhigh`; durable execution provenance showed Terra/High → Sol/XHigh on the same Assignment; A/B remained unused; and the successor Task reset to `sol-high` with C back on Terra/High (E-148).

**Next:** none automatically. Preserve the verified behavior and use Codex Room normally; reopen or create work only from demonstrated problems or explicit principal direction.

### I-016 — Private Principal Channel

**Scope:** [CORE + ROOM UI]

**Decision:** D-038

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY ACCEPTED / MERGED

**Authorized first release:** Agent C's root coordinator Assignment may emit structured `CONSULT_PRINCIPAL` when human judgment, authorization, or material clarification is needed. CORE records a private `principal_message` visible to the observer, creates no A/B deliveries, and moves the same Assignment to durable `waiting_principal`. The observer replies to that exact consultation event; CORE atomically rejects stale/duplicate replies, records a private `principal_reply`, and requeues the same C Assignment on its existing provider-context lineage. Private exchange is not automatically shared with A/B.

**Lifecycle:** waiting survives runtime restart; Pause preserves the wait and may accept the reply without executing until Resume; Stop/cancel terminates it with the surrounding Task. No fourth agent or human-as-agent entity is introduced.

**UI:** principal consultations render distinctly in the transcript with an inline private reply form. Existing ordinary observer messaging remains separate.

**Verification:** PR #137 exact feature head `e58c758527ae6a3954be9525b1411324e12ec7de` passed `git diff --check` and `verify-fast.cmd`: 63 Linux focused tests, 118 Windows portability tests, and 7 browser interaction/stability tests. The tracked tree was clean. Squash-merged as `d57d25769a8be215cc01af354983fd9c44b10825`. E-142 records the closeout evidence.

**Observed issue:** The first naturalistic acceptance Room did not exercise that machinery because C returned `COMPLETE` with the principal question, which publicly settled the original Task. The later observer reply was therefore a normal Room message and created new A/B/C work. E-143 records the exact observed sequence. A bounded prompt/instruction repair is now required before I-016 can return to COMPLETE.

**Repair state:** PR #139 exact repair head `d964af1d8fdd9c49dfcdf18f3e6104aa5b21eed9` passed `git diff --check`, 63 Linux focused tests, 118 Windows portability tests, and 7 browser tests with a clean tracked tree. It squash-merged as `26c7fb8035f15752929cfc27bd4295f0f8035ec7`.

**Naturalistic re-acceptance:** PASS in Room `room_2613bdfdff0e4ddca15fe3ba6930029b`. C emitted `CONSULT_PRINCIPAL` privately to the observer, the principal reply remained private and bound to the same Assignment, C resumed that Assignment and completed, and A/B remained unexecuted. E-144 records the exact sequence.

### Functional acceptance campaign T0-T14

**Scope:** [CORE + ROOM operational acceptance]

**Work state:** COMPLETE

**Authoritative operational procedure:** `docs/CODEX_ROOM_FUNCTIONAL_ACCEPTANCE_TEST_PLAN.md`

**Current state:** T0 through T14 are PASS and the campaign is closed. T8's initial failure was a genuine runtime-invariant failure, not permitted model variation: hard restart preserved the durable Assignment but the exact provider turn became `interrupted` and was terminally failed. PR #130 repaired and revalidated that path; E-140 owns the detailed repair evidence. T9-T14 then exercised coordinator refresh, the custom-capability lifecycle, rollover continuity, offline export/backup/verify, explicit peer model allocation, and an integrated naturalistic implementation/verification mission. E-141 records the campaign-level outcome and retained behavioral observations.

**Next:** none automatically. Preserve the acceptance plan as the repeatable regression/acceptance specification and stop here unless new evidence or explicit principal direction justifies further work.

### BCTX — bounded-context architecture program

**Scope:** [CORE]

**Decision:** D-037

**Overall work state:** COMPLETE — BCTX-1 through BCTX-4 complete

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED — BCTX-1 through BCTX-4

**Current production state:** D-037 is implemented through BCTX-4 plus the evidence-driven refresh-economics refinement. Continuous mode settles bounded Tasks and preserves deliberate C continuity across successor Tasks. A/B continuity is explicit rather than identity-based: inside a Task it follows causal Assignment lineage, and across a bounded Task boundary it requires an eligible predecessor grace source. Grace lasts through the next two successful C executions unless C closes it earlier, expires into durable provider-thread retirement, survives restart, and is retired at terminal Round boundaries while Pause preserves it. Bounded HISTORY can recover earlier settled same-Round results without replacing current transaction authority. C receives compact authoritative Task/Assignment/Join/grace state without automatic worker transcript replay and may deliberately issue `REFRESH` with a bounded checkpoint to move to a distinct fresh provider context through a fail-closed, restart-safe handoff. Eligible root-coordinator turns also receive exact-thread economics. Approximately 64K/96K last-completed-execution input-token ranges are advisory judgment guides; CORE does not auto-refresh when either range is crossed.

The program reuses the existing work-model-v2 transaction substrate. **Task is the bounded objective/activity. Assignment remains declared agent work. Join remains dependency/return state. Round remains the human-facing lifecycle/standing objective.** No new maintained Objective entity or broad v2 redesign is authorized.

The approved memory/context horizons are:

1. **Worker active context** — A/B context may be deliberately retained across explicitly causally continuous work inside the current bounded Task and, through BCTX-3's explicit grace-qualified lineage, briefly across a causally linked successor-Task boundary. This is a generic objective-local iterative-collaboration mechanism; implementation/verification/repair/re-verification is one example, not a deterministic workflow category or restriction.
2. **Coordinator continuity context** — C may carry materially longer context across successor Tasks in one continuing Round, with a later deliberate checkpoint/refresh boundary.
3. **Durable deterministic state** — Round/Task/Assignment/Join/Evidence/history/provenance remains authoritative outside provider transcript state.

Implementation order and stop boundaries follow.

#### BCTX-1 — Task-bounded continuous lifecycle and coordinator continuity

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED

**Evidence:** E-132

**Implementation:** PR #117; exact locally verified head `6871f8e45e76c783e9709b2a7feead561939a779`; canonical merge `46ee194f791cd6e2cf2a823c98e1e74a98814c7c`.

**Goal:** make each bounded coordinator activity in a continuous Round settle as its own Task while preserving the standing Round and C's useful continuity.

Required behavior:

- when the coordinator reaches the ordinary Task settlement boundary in a `continuous` Round with no open Assignments/Joins and no missing required contributor, settle the current Task instead of requeueing its terminal coordinator Assignment;
- if the hard turn limit or another terminal runtime boundary has fired, do not create successor work;
- otherwise create one successor Task in the same Round, linked through existing Task lineage (`parent_task_id` or the smallest equivalent existing mechanism);
- create the successor coordinator Assignment as fresh durable work while explicitly carrying the prior coordinator provider-context lineage forward;
- preserve the same standing Round objective and required-contributor contract;
- child Assignments remain bounded and settle normally;
- `auto_settle` Round behavior remains unchanged;
- human Stop/Pause/Resume, usage-wall continuation, exact-turn recovery, serialized execution, stale-result protection, and transaction settlement invariants remain intact;
- record enough event/provenance state to inspect each bounded Task transition deterministically.

BCTX-1 explicitly does **not** add worker context reuse, relay bypass, worker grace, same-Round HISTORY expansion, or C checkpointing.

Verification:

- focused transaction tests proving multiple settled successor Tasks inside one active continuous Round;
- exact C context-thread continuity across successor Tasks;
- no successor Task after hard turn limit/terminal stop;
- child Assignment scope remains bounded;
- existing `auto_settle` behavior unchanged;
- restart/recovery coverage at the Task-transition boundary where warranted;
- repository-standard `verify-fast.cmd` / `verify-local.ps1` verification on the exact implementation bytes;
- inspect exact diff before merge.

**Stop condition:** BCTX-1 ends when Task-bounded continuous lifecycle is exact-version verified. Do not absorb BCTX-2 mechanics merely because adjacent code is convenient to edit.

#### BCTX-2 — objective-local worker context, direct result return, and compact coordinator status

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED

**Evidence:** E-133

**Implementation:** PR #119; exact locally verified head `3a1a7f240ed43ebd4c7ea7149a5855732a23838d`; canonical merge `112b433dcc04520322da1e3048679137b3aa9f91`.

**Goal:** preserve useful A/B local cognition inside one bounded Task while removing unnecessary relay cognition and keeping C informed through compact authoritative state.

Required behavior:

- allow a later Assignment to reuse a worker provider context only through an **explicit causal context lineage** inside the same Task; common agent identity or common Task membership alone is insufficient when branches could be independent;
- preserve useful worker context across any deliberately continuous same-objective iterative collaboration inside the Task; implementation → verification → repair → re-verification is a tested example, not a special-case workflow rule;
- unrelated/new Tasks start A/B context fresh by default;
- add an explicit structured transaction mechanism allowing a child that holds the finished required result to return directly to the Task coordinator when the intermediate parent has no material intellectual work left;
- CORE must close/waive/resolve obsolete intermediate relay work mechanically and preserve exact provenance; relay bypass must never be inferred from prose;
- keep ordinary nested parent-resume behavior available when the parent genuinely has integration/correction work;
- provide C a compact deterministic Task/Assignment/Join status view sufficient to understand active ownership, dependency state, and completed/failed work without replaying worker transcript/tool chatter.

Verification should include ordinary nested delegation, direct-return delegation, parent-required integration, failure/degraded paths, parallel independent branches, restart/recovery, and exact provider-thread lineage checks.

**Stop condition:** BCTX-2 ends when objective-local continuity and direct return are verified without weakening transaction settlement or purchasing redundant model turns.

#### BCTX-3 — worker-context grace/retirement and same-Round bounded HISTORY

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED

**Evidence:** E-134

**Implementation:** PR #122; exact locally verified head `ed44f87f7648f88aca8096109a221cd00339d563`; canonical merge `25fcf4db370aa81e2cc0aa05bf1bd143c1bc8d1e`.

**Goal:** keep just-completed worker context briefly available for legitimate follow-up while preventing unrelated future work from inheriting it.

Implemented behavior:

- after a Task completes in an active continuous Round, the latest worker-owned provider contexts from that Task remain eligible for deliberate continuation through the next **two successful C executions**;
- grace ends earlier when C explicitly moves past/closes the completed objective by naming its settled Task ID;
- grace eligibility does not automatically invoke a worker or inject its transcript/result text into another Assignment;
- cross-Task continuation is explicit through `context_from_assignment_id` and is accepted only for the same worker's latest provider-thread owner from a settled ancestor Task in the same Round with remaining grace;
- successful continuation consumes the predecessor grace source and records the successor Assignment as continuation provenance;
- grace counters/state are durable on Assignment rows; expiry/explicit closure moves the context to retirement-pending, provider archival is acknowledged durably, and initialization retries pending archival after restart;
- terminal Round boundaries retire residual eligible grace; Pause preserves it;
- bounded `HISTORY` selection now retrieves completed result events from earlier settled Tasks in the **same Round** as well as earlier Rounds;
- existing same-Room authority, result-count/context bounds, exact selected-event provenance, and the rule that current transaction state comes from Task/Assignment/Join/Evidence state rather than HISTORY remain intact.

Verification on the exact implementation head: complete transaction/context suites **38/38 passed**; repository-standard fast verifier passed **54 Linux focused + 118 Windows focused + 3 browser tests** with tracked tree clean and HEAD unchanged. No GitHub-hosted workflow run was attached to the merge commit.

**Stop condition:** satisfied. Do not extend BCTX-3 into embeddings, broad summaries, a new memory database, or BCTX-4 checkpointing.

#### BCTX-4 — coordinator checkpoint and refresh

**Work state:** COMPLETE

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / MERGED

**Evidence:** E-135 through E-139

**Implementation:** PR #124 established the fail-closed refresh mechanism; exact locally verified head `fdb21c60dd9f03c82111014a3987f0f783124e7c`; canonical merge `e9669a05255beb3cce73f80cc491601f99db5219`. PR #127 adds exact-thread coordinator economics and advisory refresh guidance; exact locally verified head `03bb1a898e8d2f0e5d69f6cf28cbef0a9ddb828d`; canonical squash merge `3db7442ee8181f3aca23626d98d77e996fe2bb9e`.

**Goal:** give long-lived C coordination a deliberate context-reset mechanism without losing organizational continuity or replaying the full old transcript.

Implemented behavior:

- C may issue the explicit C-only `REFRESH` action from the root Task-coordinator Assignment in production `assignment_thread` mode and provide a bounded free-form continuity checkpoint;
- CORE creates a distinct fresh C provider context, durably records the checkpoint source plus old/new context identities and execution/event provenance, and atomically switches Assignment context ownership while keeping the refreshed Assignment non-runnable;
- the checkpoint is injected only on the first turn of the fresh context; current Round/Task/Assignment/Join/Evidence/grace state is reconstructed separately from SQLite;
- the old C context must be archived before the refreshed Assignment becomes runnable;
- failure before fresh-context activation falls back to the exact old C context;
- archival failure after activation leaves the handoff non-runnable and durable; initialization/watchdog recovery retries the pending archival;
- human Stop cancels unresolved refresh handoffs with the rest of transaction work;
- refreshed C context remains the coordinator continuity source across later BCTX-1 successor Tasks;
- transaction snapshot/export exposes exact refresh provenance;
- no automatic refresh threshold or trigger is implemented. C deliberately requests refresh when fresh context is materially useful.

Verification on the exact implementation head: complete transaction/context suites **44/44 passed**; repository-standard fast verifier passed **60 Linux focused + 118 Windows focused + 3 browser tests** with tracked source clean and HEAD unchanged. One untracked local `data/` path remained outside tracked-source verification. No GitHub-hosted workflow run was attached at closeout time.

**Post-completion refinement:** E-137 demonstrated a concrete adoption/economics issue rather than a broken refresh handoff: C never invoked `REFRESH` during a 59-turn continuous run while its exact-thread execution load grew sharply. PR #127 adds deterministic self-telemetry and advisory guidance while preserving C's judgment. The initial ranges are approximately 64K to actively consider refresh and 96K to strongly prefer it at the next clean Task boundary unless continuity/integration warrants deferral. They are not context-window occupancy claims and are not automatic triggers. E-139 completed the one bounded live revalidation: C crossed the consider range at 65,796 completed-execution input tokens, chose `REFRESH` on the next C execution at 67,960, and the fresh provider thread restarted at a 21,421-token first-execution baseline before ordinary work continued to the 40-turn limit. **Live naturalistic effectiveness is therefore supported; no further patch-specific benchmark is planned.**

**Stop condition:** the four-slice BCTX program remains complete. The PR #127 refinement fixes the demonstrated information/adoption gap without reopening BCTX or authorizing broader memory/index work, automatic refresh control, or adjacent transaction redesign.

#### Program-wide constraints and verification policy

- Preserve A/B/C as epistemic peers; C coordinates without superior judgment.
- Preserve work-model-v2 Task/Assignment/Join authority, selective cognition, exact execution provenance, serialized per-agent execution, restart recovery, stale-result protection, usage-wall safety, and human stop authority.
- Prefer schema reuse. Add state only where an existing owner cannot represent the required lifecycle safely.
- Review validity attaches to exact bytes/version.
- Use focused deterministic tests during each slice and the repository-standard fast verifier before completion. Escalate to broader/manual verification when the changed risk surface warrants it.
- One bounded naturalistic exercise after the assembled behavior is available may be useful. Do not buy a large synthetic `Stay busy.` benchmark after every slice.
- Record implementation/test evidence in the Evidence Register only after it exists. Update Architecture & Current State only after implementation is evidenced.
- If implementation reveals that a settled D-037 semantic cannot be achieved safely with the planned mechanism, stop and update the decision/plan deliberately before substituting a different architecture.

### Continuous Round naturalistic acceptance

**Work state:** COMPLETE

**Decision:** D-036

**Evidence:** E-130, E-131

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED

The dedicated acceptance is complete. In Room `room_579eb5236cd246d6a1000ea3fea781d0`, prompt exactly `Stay busy.` ran under `completion_policy="continuous"`, work-model v2, and `assignment_thread` with a 500-turn ceiling. C completed four distinct bounded activities; after each coordinator `COMPLETE`, CORE emitted `continuous_round_resumed` for the same root Assignment `assignment_df0eb6faf079484682e18e21beec5dcc`. C then began a fifth bounded activity.

The human paused the Room at 42 turns. The Round and root Task remained active, with six child Assignments completed, one child still running, six released Joins, and one pending Join. This is the intended behavior: the standing objective remained active, bounded child work retained ordinary lifecycle semantics, and human pause suspended further queued work without falsely settling the transaction.

The run consumed 1,882,148 raw execution-token deltas in approximately 506 seconds. That is useful stress-test economics evidence, but the prompt was deliberately literal and open-ended with a high turn ceiling. The later E-137 run is a separate post-BCTX observation: it exposed a coordinator-refresh adoption/economics issue because C had the refresh mechanism available but lacked actionable exact-thread self-telemetry.

No further dedicated **lifecycle** acceptance run is required. The one planned post-PR-#127 naturalistic revalidation is specifically about refresh adoption/economics, not whether continuous Round lifecycle works.

### Common Cause competitive-play authorization and ordinary-use monitoring

**Work state:** PLANNED

**Dependency:** explicit human authorization for competitive play.

**Evidence:** E-125 through E-129

The Common Cause implementation/repair/verification sequence is complete. The artifact in the existing shared workspace is verified play-ready. No further implementation or verification work is currently required.

When competitive play is authorized, use the same Room, persistent A/B/C identities/threads, and existing shared workspace. Freeze the verified game rules/engine except for a genuine defect. The first match is an ordinary competitive exercise, not another CORE benchmark.

Continue to monitor the repaired reconciliation boundary and coordination-allocation rules naturally rather than manufacturing dedicated tests.

### Ordinary continuation after the controlled replication

**Evidence:** E-126 through E-129

The principal chose to continue the existing Common Cause Room rather than discard already-spent work. A implemented an explicit zero-cost `pass` action to resolve the game-specification deadlock. When a requested A follow-up later returned `PASS` without performing the needed strengthening work, C placed the substantial fallback with a fresh bounded B assignment. B added the requested regressions/documentation and reported 11 passing tests without changing the engine mechanic.

That sequence naturally exercised the PR #110 fallback condition and supports the intended topology:

`identify bounded defect -> fresh capable worker corrects/strengthens -> verifier checks exact result -> integrate`

C then attempted to delegate one final independent exact-artifact verification. The local SDK rollout completed that exact turn with a valid `DELEGATE` decision and `task_complete`, but CORE recorded the same exact execution as `Codex turn was interrupted` and failed the transaction. Forensics identified a reconciliation race rather than a provider/model interruption. Repair commit `6b810f0e327da4055ced97f38a60977f4eba9c46` gives only the authoritative interrupted case a 0.05-second bounded opportunity for the already-started notification stream to settle; real `failed` history remains authoritative. See E-127.

After restart, a separate local environment regression temporarily blocked shell execution: redirected user `TEMP`/`TMP` pointed to `F:\Users\strig\AppData\Local\Temp`, where the Codex Windows sandbox helper could not apply its required write ACE. Restoring both variables to the Windows-profile temp directory on `C:` and restarting resolved the helper failure; a one-command SDK probe returned `CODEX_SANDBOX_OK` and sandbox setup logged `errors=[]`. See E-128.

The final continuation Round `round_557922a63c8c463ba7c40d185ddd0d58` then completed the missing nonmodifying verification. B performed the substantive independent checks; both Python files compiled, the existing unit suite passed 11 tests, CLI rejection atomicity was demonstrated for the exercised illegal action, and 48 deterministic pass actions completed all eight rounds with no unresolved offer or defense state and a final winner. C integrated the result and the Round closed normally by `transaction_settled`. See E-129.

The game is therefore verified play-ready. Competitive play remains a separate human authorization.

## Common Cause coordination-economics follow-up — complete

**Work state:** COMPLETE

**Decision:** D-035

**Evidence:** E-124 through E-129

**Reality:**

- dependency-aware sequencing — **IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED**;
- post-PR-#110 failed-delegation fallback allocation — **IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED / MONITOR**;
- coordinator-interruption issue — **REPRODUCED IN ORDINARY CONTINUATION / CORE REPAIR IMPLEMENTED AND VERIFIED TO SUFFICIENT EVIDENCE / MONITOR**;
- Common Cause artifact — **VERIFIED PLAY-READY / AWAITING HUMAN MATCH AUTHORIZATION**.

### Historical successful implementation baseline

The historical successful Common Cause implementation Round `round_f2075476746b4263a394203a2a2e7f3` produced the game implementation and passed 9/9 unit tests, but its coordination/economic shape was poor:

- 16 Room executions;
- 33 underlying provider responses;
- 17 native tool calls;
- **1,511,456 raw execution tokens**;
- C: **1,041,653**;
- A: **405,252**;
- B: **64,551**.

The demonstrated expensive topology was implementation and artifact-dependent verification running concurrently, followed by failed corrective work and large tool-heavy fallback on C's accumulated coordinator context.

The intended domain-general topology remains:

`produce prerequisite -> verify exact result -> integrate`

When correction is required:

`identify bounded defect -> fresh capable worker corrects -> verifier checks exact corrected bytes -> integrate`

Independent work remains eligible for parallel execution.

### Stage-1 structural rerun

Room `room_e910bab728bb4b518bb54ecfea9c67e9`, Round `round_62c0413093d54ed99a552d2524785f7b`, showed that the sequencing rule did not over-serialize independent work. C assigned A and B genuinely independent responsibilities concurrently. The run used **93,939 raw execution tokens**, 5.1% below the historical Stage-1 baseline of 98,996.

**Assessment:** PASS for preserving useful independent parallelism.

### Controlled implementation rerun before PR #110

Room `room_5c3fd157970f4f54ba391a7b009e3b8a`, Round `round_65eac0c64bb347eaa9fa5977f0fd08c0`, showed correct prerequisite sequencing and initial correction delegation, then exposed the PR #109 fallback loophole: substantial fallback reached C through a peer-created child assignment after delegated correction failed to produce the needed work.

The run stopped at the turn limit before full readiness. Economics through that stop were **863,799 raw execution tokens**, with C 354,530, A 485,893, B 23,376, 13 native tool calls, and approximately 80.8% cached-input share.

That evidence motivated PR #110's tightened fallback rule.

### PR #110 fallback tightening

Reviewed head:

`da4e47efb8d6e350503325f7521a2e9e56735bc1`

Merged as:

`ad9e46310068c07facea34ef0de76456881cd271`

Verified blobs:

- `codex_room/personalities.py`: `6fbe105abc8684173bd05878eac5f46c2c6ece25`;
- `tests/test_c_structural_coordination.py`: `590a11e2616c7ac69d17c12a756b8b3dee094285`.

The protected C rule says that when delegated implementation, correction, or investigation fails to produce needed work, or fallback reaches C because another assignment failed or settled without producing it, C should normally place substantial tool-heavy execution in a fresh bounded capable peer assignment. This applies in the root coordination assignment and in peer-created child assignments. Direct C execution remains available for demonstrably small, urgent, integration-inseparable work or when no fresh peer is likely to perform it reliably at lower total cost.

E-126 later supplied the first natural ordinary-use support for this exact tightened branch: A's follow-up settled with `PASS` without producing the requested strengthening work, and C moved the substantial fallback to fresh B rather than doing it on C's accumulated context. B completed the work successfully.

### Post-PR-#110 controlled replication

Fresh Room:

`room_01f030b67b0a44f08922391836a6fdd8`

Round:

`round_6409c600e2414a32a73a5f6f8e94bf51`

Controls included work-model v2, `provider_context_mode="assignment_thread"`, starter C, required contributors empty, a fresh empty workspace, the same controlled Common Cause implementation specification, `max_turns=20`, `max_consecutive_passes=3`, and `inactivity_seconds=1800`.

Observed sequence:

1. C confirmed the workspace was empty.
2. C delegated A implementation and B artifact-independent rules-audit/test-design work in parallel.
3. A implemented and tested the artifact while B produced a useful independent acceptance matrix.
4. After the artifact existed, C inspected the exact engine/tests/documentation.
5. C then delegated B to black-box verify that existing artifact.
6. B completed the artifact audit and found a reproducible gameplay deadlock in the approved specification: a legal state can require a second action when every enumerated action is illegal or unaffordable and no Pass/turn-completion rule exists.
7. The dependency join released and C resumed normally, integrated B's result, declined to invent an unapproved rule, and requested human clarification.
8. The Room closed normally by `transaction_settled` after **12 of 20 turns**.

Replication conclusions at that historical checkpoint:

- the earlier terminal `Codex turn was interrupted` after the verifier's artifact audit **did not reproduce in that controlled replication**;
- artifact-dependent verification sequencing **PASSed**;
- the Room completed below its turn ceiling;
- quality was preserved: the verifier exercised important state transitions and found a real specification contradiction, and C stopped at the correct human-decision boundary;
- PR #110's failed-delegation fallback condition **was not exercised in that Round**.

E-126/E-127 supersede the earlier monitor conclusions for later ordinary continuation: the fallback branch was subsequently exercised successfully, and the coordinator-interruption problem subsequently recurred and was diagnosed as a CORE reconciliation race.

Execution economics for the controlled replication:

- total raw execution tokens: **953,892**;
- C: **161,672**;
- A: **309,159**;
- B: **483,061**;
- Room executions: **12**;
- native model tool calls: **14**;
- failed tool calls: **4**;
- cached-input share: approximately **80.8%**.

The completed replication was **557,564 raw tokens / 36.9% below** the historical 1,511,456-token successful implementation baseline. Treat that comparison as directional because the endpoints differed: the replication correctly stopped on an unresolved game-specification contradiction rather than reaching a competitive-play-ready declaration.

### Common Cause stop condition

The dedicated synthetic coordination benchmark series remains stopped. Ordinary continuation provided the missing fallback evidence naturally and exposed a real CORE reconciliation defect, which received a bounded repair. The game's turn-completion contradiction was addressed by the explicit zero-cost pass mechanic, and E-129 completed the final independent exact-artifact verification.

Common Cause is now **VERIFIED PLAY-READY**. Do not add another verification gate before competitive play unless the artifact changes or a genuine defect appears. Competitive play starts only after explicit principal authorization.

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

## QoL Wishlist

**Purpose:** Retain useful quality-of-life ideas without silently promoting them into authorized implementation work.

Wishlist entries are **idea capture, not a work queue**. They have no work state merely by appearing here. When the principal explicitly selects an item for implementation, track that active work through the normal Development Control flow and verify it according to its actual risk. Prefer thin UI/operator improvements that do not disturb transaction semantics, durable state, or agent judgment.

### Initial wishlist — 2026-09-19

- **Observer composer: Enter sends; Shift+Enter inserts a newline — IMPLEMENTED / VERIFIED.** PR #133 implemented the behavior only in the ordinary observer composer, retained Ctrl/Cmd+Enter as an additional send shortcut, ignored Enter during IME composition, and added the `Enter to send · Shift+Enter for newline` hint. Exact feature head `99fb09f0c8273a918cab5ded232accad4fee3ed2` passed `verify-fast.cmd`: 63 Linux focused tests, 118 Windows portability tests, and 4 browser interaction/stability tests. Squash-merged as `74863b688962e80046944d6adda38e3c85dd20d3`.
- **Composer focus retention — IMPLEMENTED / VERIFIED.** PR #135 focuses the observer composer when a Room opens and restores focus after a successful send without forcing transcript scroll movement.
- **Auto-growing observer composer — IMPLEMENTED / VERIFIED.** PR #135 grows the ordinary observer composer from its compact height up to a bounded 180px cap (roughly eight lines at the current typography), then uses internal vertical scrolling.
- **Per-Room unsent drafts — IMPLEMENTED / VERIFIED.** PR #135 stores observer text and selected target per Room in browser-local storage, restores them across Room switches and page refreshes, isolates drafts by Room, and clears only the successfully submitted Room draft.

**PR #135 verification:** Exact feature head `8b1adf77093da1f86753f79665f03bc4ab23a39d` passed `verify-fast.cmd`: 63 Linux focused tests, 118 Windows portability tests, and 5 browser interaction/stability tests. The tracked tree was clean. Squash-merged as `7942d3f43a4871bcfe67a34c2d92efe97377f179`.

- **New-activity / jump-to-latest control.** When the human has scrolled away from the transcript bottom, keep the existing non-forced-scroll behavior but surface a visible `new events` indicator/button that jumps to the latest activity.
- **One-click operational ID copying.** Make the Room ID easy to copy and expose convenient copying for relevant Round, Task, and Assignment IDs. Consider a single `Copy diagnostics` action containing the current Room/Round/Task identifiers, status, turn count, model/effort, and runtime/source provenance.
- **Room search and filtering.** Add quick search plus simple state filters such as Active, Paused, Finished, and Archived so a growing Room list remains manageable.
- **Transcript detail/noise controls.** Allow the human to switch between conversation-focused and full-activity views or collapse low-level activity. Errors, attempt warnings, recoveries, and important lifecycle transitions should remain prominent.
- **Clear immediate action feedback.** Give obvious transient feedback for actions such as sending, copying, preparing/starting, and failures; keep error feedback visually associated with the initiating control where practical.
- **Remember harmless UI preferences locally.** Persist presentation-only choices such as transcript-detail mode, sidebar state/width, last-used observer target, and whether archived Rooms are shown. Do not turn these into CORE/institutional state unless evidence later requires it.
- **Conservative keyboard shortcuts.** Support useful navigation/focus shortcuts such as Escape to close dialogs and a shortcut to focus Room search or the observer composer. Avoid shortcuts for destructive/lifecycle actions such as Stop, Reset Agents, or Archive.
- **Copy individual agent responses.** Provide a small copy action on individual transcript messages so exact agent output can be reused without manual text selection.

## Maintenance / monitor items

### PR #110 failed-delegation fallback behavior

**Work state:** MONITOR

**Reality:** IMPLEMENTED / EXACT-HEAD VERIFIED / NATURALISTICALLY SUPPORTED

E-126 shows the tightened branch operating as intended in ordinary continuation: an empty/nonproductive delegated follow-up was followed by substantial fallback work on a fresh capable peer rather than C's accumulated coordinator context. Continue to observe natural recurrences for generalization and cost/quality effects; do not purchase a dedicated synthetic test.

### Exact-turn interruption reconciliation

**Work state:** MONITOR

**Reality:** IMPLEMENTED / REVIEWED / VERIFIED TO SUFFICIENT EVIDENCE

E-127 records the reproduced false interruption, forensic diagnosis, and bounded repair at commit `6b810f0e327da4055ced97f38a60977f4eba9c46`. E-129 adds one normal post-repair continuation that closed by `transaction_settled` without recurrence. Continue ordinary-use monitoring. Do not widen the 0.05-second interrupted-only grace or redesign reconciliation absent new evidence.

### I-003 — Provider-side instruction adoption after same-thread profile rebind

**Work state:** MONITOR

**Reality:** NEEDS VERIFICATION / current recurrence not demonstrated

Current deterministic evidence verifies the local rebind mechanism and fail-closed identity behavior, but not independent provider-side proof that replacement developer instructions took effect on the resumed same thread. Do not spend a dedicated paid test unless ordinary use makes the uncertainty consequential.

### Naturalistic continuation economy

**Work state:** MONITOR

E-086 demonstrated that the continuation-economy repair can radically reduce tool-loop replay on a controlled fixture. E-090 showed broader source work can still become expensive. E-129 adds a concrete smaller recurrence: a requested single-verifier closeout took the path C -> A -> B, with A acting as a zero-tool relay and consuming 45,338 raw execution tokens without adding independent verification evidence. Treat this as ordinary-use cost evidence; avoid purchasing another synthetic benchmark solely to investigate it unless similar relay patterns recur or become materially expensive.

## Deferred work

Keep these deferred unless new evidence or explicit principal direction reprioritizes them:

- archive indexing/embeddings/broad summarization beyond bounded `HISTORY`;
- automatic CORE model routing (C-controlled D-039 self-allocation is separate);
- broader deterministic-tooling promotion without demonstrated reuse;
- stronger per-capability OS isolation;
- shareable/redacted exports;
- large-module refactors/storage optimization;
- broader productization/packaging/funding;
- Enterprise workforce features;
- provider-neutral implementation work;
- nonessential UI refinement.

## Open questions

No high-priority conceptual question currently blocks ordinary Codex Room use or development.

The Common Cause coordination questions that motivated PRs #109/#110 now have naturalistic support for both dependency-aware sequencing and the tightened failed-delegation fallback. The game artifact is verified play-ready. The only remaining Common Cause gate is the principal's separate authorization to begin competitive play.

The repaired exact-turn interruption boundary is monitor-only unless it recurs. The TEMP/TMP sandbox-helper regression is resolved and recorded in E-128; do not reopen it absent recurrence.

D-019 remains blocked on provider allowance/credit-pool semantics. Other deferred work should remain deferred until new evidence or explicit principal direction gives it priority.
