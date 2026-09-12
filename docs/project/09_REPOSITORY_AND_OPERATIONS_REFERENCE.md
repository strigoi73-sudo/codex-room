# Codex Room — Repository & Operations Reference

**Last synthesized:** 2026-09-12  
**Scope:** Compact technical reference for source/runtime layout, maintenance boundaries, source-control workflow, recovery, and verification practices.  
**Freshness:** Repository details are time-bounded. Prefer current live source and Git state when available.

## 1. Canonical repository and live workspace

Canonical source-control arrangement:

- primary development workspace: `C:\Codex Room`
- GitHub repository: `strigoi73-sudo/codex-room` (private)
- remote: `https://github.com/strigoi73-sudo/codex-room.git`
- branch: `main`
- upstream: `origin/main`

The earlier September 8 state with an unborn/untracked Git repository is historical and superseded. Milestone commit identities belong in Git history/Evidence Register. Exact current HEAD, ref agreement, CI state, and working-tree state are mechanically changing repository facts and should be inspected directly from GitHub or local Git when consequential rather than maintained in Project sources.

**Canonical Project-source home:** maintained Project sources live under `docs/project/` in this repository. Those repository files are authoritative for Charter, Constitution, Architecture & Current State, Decision Register, Development Control, Evidence Register, Product Vision, Repository & Operations, and the identifier index. The GPT Project should not maintain duplicate authoritative source attachments after cutover.

**Boundary:** the repository Project sources track durable meaning, architecture, decisions, evidence, and work state; Git/GitHub also track their exact bytes/history plus mechanically changing repository state and provenance.

## 2. Official cognition-allocation and development workflow

Decision D-018 governs the default external development workflow. The objective is to spend cognition only where cognition is useful, execute work at the cheapest authorized capable layer, and preserve exact evidence across handoffs.

- **ChatGPT Codex Room Project — reasoning, coordination, and connected execution:** use the live GPT Project instructions as a bootstrap, then retrieve the relevant canonical files from `docs/project/` for scoping, sequencing, tradeoffs, and review. Do not rely on stale uploaded copies when repository freshness matters. When connected tools can safely perform repository inspection, bounded edits, GitHub operations, or other deterministic work, perform that work directly instead of delegating it merely for execution.
- **Deterministic local tools — local execution without model cognition:** use Git, shell commands, tests, filesystem searches, and other deterministic tools when the task depends on local state but does not require model reasoning.
- **Local Codex — local development cognition and execution:** use Codex when local-only access, substantial implementation work, scattered or ambiguous evidence, failure-prone investigation, or valuable independent cognition makes it useful. When the task is already understood, use explicit phase-titled prompts with narrow scope, verification requirements, and stop conditions.
- **Git — exact change and provenance machinery:** use status, diff, blob IDs, commits, and history as the preferred representation of what actually changed.
- **GitHub — shared canonical history and review boundary:** use pushed commits and pull requests to make exact versions available across Project and local development workflows.
- **GitHub Actions and deterministic tooling — routine mechanical verification:** automate stable checks such as clean installation and the canonical test suite without model reasoning.

Normal [CORE] path:

**known commit → reasoning/scope where needed → cheapest capable execution layer → deterministic checks → exact-diff review where warranted → commit/push → GitHub-hosted verification as applicable**

Do not delegate an operation to Codex when the Project can safely and adequately perform it directly. Do not deprive Codex of cognition when local ambiguity, implementation complexity, failure-prone investigation, or independent challenge makes that cognition materially useful.

Prefer exact diffs/status/test outputs over model narration of mechanically available facts.

Do not create ZIP/Drive transfer copies as routine development checkpoints. The temporary `Codex Git Transfer` process was a one-time bridge used to establish the baseline; it is not the normal maintenance workflow.

A review attaches to the exact reviewed commit/bytes. Any later mutation makes the prior review stale for the new version.

### GPT Project bootstrap/retrieval workflow

Use the repository sources selectively rather than loading the full package by default:

1. use `docs/project/00_PACKAGE_INDEX_AND_MAINTENANCE_GUIDE.md` when document ownership or source authority is unclear;
2. use `docs/project/06_DEVELOPMENT_CONTROL.md` for current priority, active work, blockers, and open questions;
3. retrieve Charter/Constitution/Decision Register when governing intent is relevant;
4. retrieve Architecture & Current State for implementation synthesis, Evidence Register for rationale/evidence, Product Vision for future direction, and this file for repository/operations mechanics;
5. verify consequential current repository facts directly from Git/GitHub instead of treating maintained prose as a live ref/status feed;
6. if repository access is unavailable and current Project-source content is consequential, state that freshness cannot be verified rather than silently falling back to stale memory or historical attachments.

## 3. Reproducible development/test baseline and CI

Current clean-development procedure:

1. create a Python virtual environment;
2. install with `python -m pip install -c constraints-test.txt ".[test]"`;
3. run the canonical routine suite with `python -m pytest -q`.

`constraints-test.txt` records the known-good application/test dependency set for routine development and CI while `pyproject.toml` retains broader supported ranges. Clean-environment verification collected and passed **129 tests**. `test-transcript-stability.ps1` remains a separate specialized browser check because it requires Node.js plus Chrome or Edge.

Minimal CI lives at `.github/workflows/python-tests.yml`. It runs on pushes to `main` and pull requests targeting `main`, uses Python 3.12 on Ubuntu, grants `contents: read`, installs through `constraints-test.txt`, and runs the canonical pytest command. Commits or pull requests whose changed paths are entirely under `docs/project/**` are ignored by this Python-test workflow; mixed code + Project-document changes still run CI. Dependency upgrades should be deliberate changes to the constraint set rather than incidental resolver drift.

### Windows local launch and shutdown

Normal Personal local operation uses the root launch scripts:

- double-click `Start-Codex-Room.cmd` to start the foreground local server; the dedicated launcher console is titled `Codex Room Server`;
- use `Kill-Codex-Room.bat` to stop Codex Room;
- `Kill-Codex-Room.bat --dry-run` previews the repository-specific process targets without stopping them.

Current shutdown targeting identifies both the repository venv Python process running `-m codex_room` and a dedicated launcher `cmd.exe` identified by the canonical start-script path or the `Codex Room Server` window title. It then includes descendants of those seeds, stops the target set, and verifies the targeted process IDs are gone. Successful shutdown does not pause, so a temporary Kill console can exit immediately; the script pauses only on shutdown failure so diagnostics remain visible.

The kill script deliberately does **not** terminate browser processes. Codex Room opens the UI through the system browser and that process may also own unrelated tabs/windows, so browser teardown is outside the safe repository-specific process boundary.

PR #18 introduced this behavior. Exact PR-head and merged canonical-main Python CI both passed **238 tests, 2 warnings**. Local Windows runtime verification on 2026-09-12 then confirmed that the normal Kill path closed both the Codex Room server console and the Kill console with no manual cleanup required. The shutdown behavior is therefore IMPLEMENTED / VERIFIED for the intended Personal Windows path.

## 4. Source/runtime/generated boundaries

The canonical repository tracks application source, tests, root scripts/configuration, and static assets.

The established `.gitignore` excludes major runtime/generated material, including:

- `.venv/`, `venv/`
- `__pycache__/`, `.pytest_cache/`
- `.playwright-cli/`, `node_modules/`
- `output/`
- Python bytecode
- runtime database files under `data/`
- `data/rooms/`
- `data/backups/`
- identity-recovery directories
- rollover staging/result files
- institutional publishing/generated release registry
- `Codex Git Transfer/`

No filesystem reorganization was required to establish this boundary.

Important runtime locations still include:

- `data/codex-room.db`
- `data/rooms/`
- `data/institutional/`

Generated/runtime data is not evidence of canonical source history merely because it exists under the project root.

## 5. Functional source landmarks

Current canonical source includes these useful areas/symbols:

- `codex_room/models.py` — `AgentDecision`, MESSAGE/PASS/FINISH schema, `invoke_targets`;
- `codex_room/orchestrator.py` — routing/settlement, selective invocation, compaction policy, retry observability, usage-wall scheduling/watchdog;
- `codex_room/db.py` — durable events/deliveries, compaction baseline persistence, `usage_continuations`, execution state;
- `codex_room/agent.py` — persistent SDK-thread interaction, compaction completion checks, same-thread usage-continuation preparation;
- `tests/` — regression coverage including selective routing, compaction baseline, usage-wall continuation, three-agent behavior, rollover, API, and institutional behavior.

Locate and inspect current definitions before consequential edits; this list is a navigation aid, not a substitute for source inspection.

## 6. Maintenance boundary

Classify planned changes as:

- **[CORE]**
- **[ROOM]**
- **[CORE + ROOM migration]**

Do not have a running A/B/C Room hot-patch the protected Core runtime hosting itself.

Perform [CORE] implementation outside the protected running Room through the cheapest authorized execution layer capable of safely completing the work and producing adequate evidence. Use local Codex when its local access or cognition is materially useful. Prefer one controlled writer; independent review may follow where it adds value. Bring the Room to a safe/quiescent state before changes capable of affecting active execution when practical.

## 7. Verification discipline

For consequential [CORE] changes:

1. identify the relevant invariant/failure mode;
2. inspect the current source before editing;
3. make the smallest sufficient change;
4. add/update focused regression tests where behavior changes;
5. run focused tests during development;
6. run the canonical broader/full suite before completion when warranted;
7. inspect `git diff` so review covers the actual changed bytes;
8. record important verification in the Evidence Register;
9. update Architecture & Current State only after implementation is evidenced.

Historical test counts prove the tree/version that produced them. They do not substitute for a fresh run after later code changes.

## 8. Source-control safety rules

- Do not use `git clean`, destructive reset, or checkout as a casual repair mechanism around runtime data.
- Preserve ignored runtime material unless a task explicitly authorizes changing it.
- Before destructive or broad Git operations, verify branch, target commit, and affected paths.
- Prefer deterministic Git evidence (`status`, `diff`, blob/commit IDs) over timestamp/size heuristics.
- For exact-byte comparison, compare Git blob IDs with Git blob IDs; ordinary SHA-256 file hashes are not directly comparable to Git blob object IDs.

## 9. Usage-limit recovery

The old manual workaround (**stop Room → restart service → Resume → send a continuation**) is superseded for positively identified usage walls by the implemented delayed-continuation mechanism.

Current implementation behavior, historically verified 2026-09-09:

- recognize authoritative usage-limit error + parseable terminal retry time;
- schedule wake at provider retry time + 60 seconds;
- persist continuation state across restart;
- prepare/rebind the same persistent thread where safely supported;
- release due work through the normal serialized queue;
- repeated usage walls replace the schedule;
- stop/lifecycle changes cancel stale continuation work;
- unrecognized retry formats fail closed.

Exact-byte independent review of this P3 implementation remains pending but non-blocking.

## 10. Historical external artifacts

Older repository ZIP snapshots, Room exports, handoff bundles, raw archives, prior GPT Project source attachments, and database/recovery backups remain historical evidence only after the repository-source cutover. Inspect them narrowly when a question requires them.

Do not infer present behavior solely from an old artifact. Prefer the canonical current Git commit/source and dated current evidence.
