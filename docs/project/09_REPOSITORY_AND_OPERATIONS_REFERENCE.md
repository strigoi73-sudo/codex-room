# Codex Room — Repository & Operations Reference

**Last synthesized:** 2026-09-15  
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

1. use Python 3.11 or later and create a virtual environment;
2. install with `python -m pip install -c constraints-test.txt ".[test]"`;
3. run the canonical routine suite with `python -m pytest -q`.

`constraints-test.txt` records the known-good application/test dependency set for routine development and CI while `pyproject.toml` retains broader supported dependency ranges. The supported Python floor is 3.11+. As of E-071, the standard Codex pair is `openai-codex==0.154.0` with `openai-codex-cli-bin==0.154.0`, and the package floor is `openai-codex>=0.154,<1`; production Room model policy remains separately pinned in source. The exact code-bearing canonical-main verification for that upgrade passed **327 tests, 2 warnings**. `test-transcript-stability.ps1` remains separate from the canonical Python command because it requires Node.js plus Chrome or Edge; hosted Windows CI now runs it automatically using pinned `@playwright/test@1.63.0`.

Hosted verification lives at `.github/workflows/python-tests.yml`. It runs on pushes to `main` and pull requests targeting `main`, grants `contents: read`, installs through `constraints-test.txt`, and runs the canonical pytest command on Ubuntu/Python 3.11, Ubuntu/Python 3.12, and Windows/Python 3.12. The Windows lane also runs `test-transcript-stability.ps1`. Commits or pull requests whose changed paths are entirely under `docs/project/**` are ignored by this Python-test workflow; mixed code + Project-document changes still run CI.

Dependency assurance lives at `.github/workflows/dependency-review.yml`. It runs when `pyproject.toml`, `constraints-test.txt`, or the workflow itself changes on a PR/push to `main`, on monthly schedule, and on manual dispatch. The workflow installs pinned `pip-audit==2.10.1`, audits the fully pinned constraint set with `--strict --no-deps`, then installs the normal test environment and reports `python -m pip list --outdated`. The audit can fail on a known vulnerability; the outdated report is informational. Package upgrades remain deliberate reviewed changes to the constraint set rather than automatic resolver or bot churn. See E-088.

### Read-only Codex rollout usage reporting

For P1 operating-economics comparisons, `codex-usage.cmd` reads local Codex rollout JSONL token counters without invoking Codex or modifying its state. The underlying module is `codex_room/codex_usage.py` and uses only the Python standard library.

Normal commands from the repository root:

```powershell
.\codex-usage.cmd
.\codex-usage.cmd --timeline
.\codex-usage.cmd --json
.\codex-usage.cmd --thread-id <thread-id> --json
.\codex-usage.cmd --path "C:\path\to\rollout-....jsonl" --json
```

Default lookup uses `CODEX_HOME` when set, otherwise `~/.codex`, and selects the most recently modified active **top-level** rollout so a child/subagent rollout is not silently substituted for the requested Desktop task. `--include-subagents-latest` is an explicit opt-in; `--include-archived` extends discovery to archived rollouts.

The report contains no prompt/response text. It retains session metadata, event-type counts, cumulative and last-response token counters, token-update progression, and per-user-turn usage deltas derived from cumulative counters. For a fresh one-task Desktop thread, final cumulative usage is the cleanest task total. For a reused thread, use the relevant `user_turns[].usage` delta and confirm that cumulative counters did not decrease. Never use `last_token_usage` as a substitute for cumulative task work when tool/model continuations occurred.

See E-082 for verification and evidence limits.

### Windows local launch and shutdown

Normal Personal local operation uses the root launch scripts:

- double-click `Start-Codex-Room.cmd` to start the foreground local server; the dedicated launcher console is titled `Codex Room Server`;
- use `Kill-Codex-Room.bat` to stop Codex Room;
- `Kill-Codex-Room.bat --dry-run` previews the repository-specific process targets without stopping them.

Current shutdown targeting identifies both the repository venv Python process running `-m codex_room` and a dedicated launcher `cmd.exe` identified by the canonical start-script path or the `Codex Room Server` window title. It then includes descendants of those seeds, stops the target set, and verifies the targeted process IDs are gone. Successful shutdown does not pause, so a temporary Kill console can exit immediately; the script pauses only on shutdown failure so diagnostics remain visible.

The kill script deliberately does **not** terminate browser processes. Codex Room opens the UI through the system browser and that process may also own unrelated tabs/windows, so browser teardown is outside the safe repository-specific process boundary.

PR #18 introduced this behavior. Exact PR-head and merged canonical-main Python CI both passed **238 tests, 2 warnings**. Local Windows runtime verification on 2026-09-12 then confirmed that the normal Kill path closed both the Codex Room server console and the Kill console with no manual cleanup required. The shutdown behavior is therefore IMPLEMENTED / VERIFIED for the intended Personal Windows path.

### Offline persistent-data maintenance

I-010 adds a local operator maintenance wrapper:

```powershell
.\codex-room-maint.cmd check --offline-confirmed
.\codex-room-maint.cmd backup --offline-confirmed
.\codex-room-maint.cmd verify "C:\Codex Room\data\backups\<backup-id>"
.\codex-room-maint.cmd restore "C:\Codex Room\data\backups\<backup-id>" --offline-confirmed --confirm-replace-data
```

For `check`, `backup`, or `restore`, first stop Codex Room with the normal Kill path. The `--offline-confirmed` switch is an explicit operator assertion; the maintenance command does not independently detect running server processes. `restore` is destructive and additionally requires `--confirm-replace-data`.

By default the data root is `C:\Codex Room\data`. A different root may be supplied as a global option before the subcommand:

```powershell
.\codex-room-maint.cmd --data-root "D:\CodexRoomData" check --offline-confirmed
```

`backup` writes beneath `data\backups\` unless an external `--backup-root` is supplied. It uses SQLite's native backup API, then hashes/verifies the remaining durable payload before publishing the backup directory. `verify` checks the archive manifest, exact payload set, hashes/sizes, safe paths, and SQLite health. `restore` verifies and stages the selected archive before replacing current data and preserves the existing backup collection through the swap. See E-087 for exact verification and limitations.

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
- `data/custom-capabilities/`

Generated/runtime data is not evidence of canonical source history merely because it exists under the project root.

## 5. Functional source landmarks

Current canonical source includes these useful areas/symbols:

- `codex_room/models.py` — `AgentDecision`, MESSAGE/PASS/FINISH schema, `invoke_targets`;
- `codex_room/personalities.py` — protected institutional/structural/protocol instruction composition and neutral default profile bodies;
- `codex_room/orchestrator.py` — routing/settlement, D-026/D-027 invocation economy, delegation-cohort timing, compaction, retry/usage-wall recovery, maintenance watchdog;
- `codex_room/db.py` — durable events/deliveries, profiles/Rounds, exact execution state, migrations, usage continuations, rollover state;
- `codex_room/agent.py` — persistent SDK-thread interaction, fixed current model/effort boundary, exact-turn reconciliation, compaction and continuation preparation;
- `codex_room/capabilities.py` — CORE deterministic registry, list/inspect/invoke surface, and minimal built-in library;
- `codex_room/custom_capabilities.py`, `custom_capability_registration.py`, `custom_registry.py` — custom package validation, deterministic verification/publication, protected Room binding, unified custom discovery/invocation;
- `codex_room/rollover.py` / rollover paths in runtime/database code — lineage continuation and exact inherited custom-capability bindings;
- `Start-Codex-Room.cmd`, `Kill-Codex-Room.bat`, `codex-room-cap.cmd`, `codex-room-maint.cmd` — normal Windows launch/shutdown, agent capability, and offline maintenance wrappers;
- `codex_room/maintenance.py` — I-010 persistent-data check/backup/verify/guarded-restore implementation;
- `tests/` — regression coverage including routing/settlement, persistent execution recovery, profiles, capabilities, rollover, Windows launcher contracts, API, and UI behavior.

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

Current A2 source/test review retired the earlier exact-byte-review caveat for P3; see E-028. Later changes still require version-appropriate verification rather than inheriting that historical result automatically.

## 10. Historical external artifacts

Older repository ZIP snapshots, Room exports, handoff bundles, raw archives, prior GPT Project source attachments, and database/recovery backups remain historical evidence only after the repository-source cutover. Inspect them narrowly when a question requires them.

Do not infer present behavior solely from an old artifact. Prefer the canonical current Git commit/source and dated current evidence.
