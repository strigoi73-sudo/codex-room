# Codex Room

Codex Room is a local browser application for a persistent, inspectable AI organization. Personal production uses a fixed triad of **Agent A, Agent B, and Agent C**. They are persistent organizational identities and epistemic peers; standard profile bodies are neutral. Agent C has protected coordination responsibility, serves as the ordinary human entry point, and controls coordination without gaining superior judgment.

The current public production path is **work-model version 2** with `provider_context_mode="assignment_thread"`. Durable Room/Task/Assignment/Join state is authoritative. Provider context is bounded to declared work and explicit continuity rather than serving as the definition of agent identity.

Codex Room uses the official `openai-codex` Python SDK and its local app-server transport, reusing Codex authentication already available on the machine.

## Install for development and testing

Codex Room requires Python 3.11 or later. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints-test.txt ".[test]"
```

`constraints-test.txt` records the known-good application/test dependency set. Dependency upgrades are deliberate changes rather than incidental resolver drift.

## Start

Double-click `Start-Codex-Room.cmd`. It starts the local server and opens:

<http://127.0.0.1:8765>

The application stores its SQLite database and per-Room shared workspaces under `data/`.

`Start-Codex-Room.cmd` normally uses the Codex runtime pinned by the installed `openai-codex` package. Set `CODEX_ROOM_CODEX_BIN` only when deliberately testing another supported `codex.exe`.

For development, the equivalent entry point is:

```powershell
$env:CODEX_ROOM_CODEX_BIN = "C:\path\to\current\codex.exe"
.\.venv\Scripts\python.exe -m codex_room
```

Use `Kill-Codex-Room.bat` to stop the local runtime and `Restart-Codex-Room.bat` for the normal server-only restart path that preserves the existing browser window/tab.

## First run

1. Select **New room**.
2. Enter the opening objective/topic.
3. Optionally edit participant names/profile overrides and safety limits.
4. Create the Room. New Personal Rooms contain A/B/C and stage the opening Round in `preparing`.
5. Review the staged Round and select **Start Round**. C is the ordinary default starter.
6. Observe the transcript and intervene when useful.

Round preparation itself performs no model invocation. A Round can also be started with all participants independently when deliberate independent first-pass cognition is desired.

## Current work model

The production scheduler is transaction-based:

```text
Room
└─ Round
   └─ Task
      ├─ Assignment
      ├─ Assignment
      └─ Join / integration / settlement state
```

A **Task** is the bounded objective/activity. An **Assignment** is declared agent work. A **Join** records dependency/return state. CORE owns the mechanical lifecycle and provenance; agents retain judgment about decomposition, evidence, conclusions, and whether further cognition is worthwhile.

Transaction-enabled agent actions include:

- `COMPLETE` — finish the current Assignment with a substantive result;
- `DELEGATE` — create explicit peer Assignment work;
- `EVIDENCE` — request bounded deterministic source reads/searches;
- `HISTORY` — retrieve bounded prior completed Room results;
- `REFRESH` — C-only bounded coordinator context checkpoint/refresh;
- `PASS` — finish without a substantive result where permitted.

Provider context normally belongs to an Assignment. Explicit causal lineage may preserve useful A/B context for continued work, including the bounded post-Task grace mechanism. C may carry continuity across successor Tasks in a continuous Round and can deliberately `REFRESH` to a fresh provider context with a bounded checkpoint. Durable transaction state remains authoritative throughout.

Legacy work-model-v1 code/tests may remain internally for historical compatibility, but v1 is not a selectable public production mode.

## Model allocation

New Rooms use the **Default** model policy unless the principal explicitly selects **Unrestricted model access** during Room setup.

Under the default policy, the compatibility execution boundary remains **Terra/high** and C allocates among the admitted bounded configurations. Stronger cognition is available when complexity, uncertainty, risk, or verification trouble justifies it. Astra remains default-denied; an explicit Astra model direction in the opening Room prompt authorizes Astra Low/Medium/High for that conversation lineage, including normal rollover successors. Exceptional C-only cognition retains its Task-scoped principal-approval rules.

When **Unrestricted model access** is selected, CORE snapshots the native Codex model catalog and every reasoning effort exposed for those models at Room creation. C may then allocate any snapshotted native model/effort configuration to A, B, or C without the default Room model-family, peer-role, Astra, or exceptional-cognition restrictions. C still allocates cognition economically; unrestricted authorization does not mean strongest-by-default. The policy and exact catalog persist with normal rollover successors, and Room creation fails closed if a complete usable native catalog cannot be established.

There is no automatic model router: C remains the model-allocation decision maker.

## Deterministic capabilities

Codex Room includes a registered deterministic capability substrate for mechanical work that should not repeatedly consume model cognition. The CORE library includes capabilities such as exact file assertions, file discovery/comparison, text search, and bounded source inspection.

Rooms can also author and register verified custom capabilities. Registered custom capability versions are immutable/provenance-bearing, and lineage-scoped capabilities can be inherited by rollover successors at the exact registered version.

The governing principle is to use model judgment for interpretation and decisions while moving stable exact procedures into deterministic software when the expected value justifies it.

## Persistence, recovery, and inspection

SQLite stores Room/Round/Task/Assignment/Join state, events, exact execution provenance, provider-context identities, usage/recovery state, capability bindings, and related metadata. The runtime serializes execution per agent, protects against stale results, and reconciles exact provider turns after restart.

Positive usage walls schedule durable delayed continuation instead of immediate retry storms. Hard-restart recovery for an exact active transaction turn is covered by the repaired startup-recovery path validated during Functional Acceptance T8.

Live snapshots are bounded for observer efficiency while exports request complete Room history. Offline maintenance supports integrity checking, verified backup, independent backup verification, and guarded restore.

## Verification

The normal repository PR/change gate is:

```powershell
.\verify-fast.cmd
```

The exhaustive/manual tier is:

```powershell
.\verify-full.cmd
```

Both are implemented by `verify-local.ps1`. Fast verification includes focused Linux/Python checks, Windows portability coverage, and browser transcript stability. Full verification expands to complete supported Python suites plus dependency audit where the local prerequisites are available.

The raw Python suite remains available for focused development:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

GitHub remains the canonical history/review bridge. Routine verification is local because the prior GitHub Actions workflows were removed after repeated pre-runner startup failures made them unreliable as the normal gate.

The repeatable operational acceptance specification is `docs/CODEX_ROOM_FUNCTIONAL_ACCEPTANCE_TEST_PLAN.md`. The 2026-09-19 T0–T14 campaign completed with every test recorded PASS; its exact evidence is retained in the acceptance plan and Evidence Register.

## Project documentation

Canonical maintained Project sources live in `docs/project/`. The key ownership split is:

- `04_ARCHITECTURE_AND_CURRENT_STATE.md` — implemented/current technical synthesis;
- `05_DECISION_REGISTER.md` — settled decisions;
- `06_DEVELOPMENT_CONTROL.md` — current priority, issues, blockers, and next work;
- `07_EVIDENCE_REGISTER.md` plus `07a_EVIDENCE_REGISTER_CONTINUATION.md` — empirical evidence;
- `08_PRODUCT_VISION.md` — longer-range direction;
- `09_REPOSITORY_AND_OPERATIONS_REFERENCE.md` — repository/operations mechanics.

For current sequencing, read `docs/project/06_DEVELOPMENT_CONTROL.md` rather than inferring a roadmap from this README.
