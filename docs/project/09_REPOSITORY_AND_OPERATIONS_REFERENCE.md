# Codex Room — Repository & Operations Reference

**Last synthesized:** 2026-09-27  
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
- **Deterministic local verification — routine mechanical verification:** use the repository-root local verifier for stable checks without model reasoning; keep GitHub focused on canonical source history/review unless hosted automation is deliberately reintroduced for a demonstrated need.

Normal [CORE] path:

**known commit → reasoning/scope where needed → cheapest capable execution layer → deterministic checks → exact-diff review where warranted → commit/push → local exact-tree verification as applicable**

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
3. use `python -m pytest -q` for the raw Python suite when that scope is specifically needed;
4. use `verify-fast.cmd` as the normal repository change/PR gate and `verify-full.cmd` for exhaustive/manual verification.

`constraints-test.txt` records the known-good application/test dependency set while `pyproject.toml` retains broader supported dependency ranges. The supported Python floor is 3.11+. As of E-071, the standard Codex pair is `openai-codex==0.154.0` with `openai-codex-cli-bin==0.154.0`, and the package floor is `openai-codex>=0.154,<1`; production Room model policy remains separately pinned in source. The exact code-bearing verification for that upgrade passed **327 tests, 2 warnings**. `test-transcript-stability.ps1` remains separate from the raw Python suite because it requires Node.js plus Chrome or Edge, but it is included by the repository verification wrappers.

Routine cross-platform verification uses the repository-root wrappers `verify-fast.cmd` and `verify-full.cmd`, both implemented by `verify-local.ps1`. Fast mode runs the focused Linux/Python 3.12 core set, synchronizes/checks pinned Windows dependencies, runs the focused Windows portability set, and runs browser transcript stability. Full mode runs the complete Python suite under Linux/Python 3.12 and 3.11, the complete Windows Python suite, browser transcript stability, and pinned `pip-audit==2.10.1`. The verifier caches its local environments, synchronizes dependencies only when needed, reports the exact commit, distinguishes tracked-source modifications from untracked local artifacts, and fails on any failing phase.

For repeated exact-head PR/feature verification, use repository-root `verify-feature.ps1` instead of regenerating checkout/restore guardrails in chat. It accepts an exact canonical `-Base` SHA, exact `-Head` SHA, optional `-FocusedTests`, and `-Mode Fast|Full`. The script requires a clean tracked tree, stops a running Room through `Kill-Codex-Room.bat`, fetches/prunes `origin`, requires `origin/main` to equal the requested base, verifies that the base is an ancestor of the exact head (or its direct parent when `-RequireDirectParent` is selected), runs `git diff --check`, verifies the detached exact head, runs focused Windows pytest targets when supplied, invokes the canonical broad verifier, confirms the final exact head/tree, and restores the caller's original branch or detached HEAD. If the cached Windows verification environment does not yet exist and focused tests were requested, the broad gate runs first to provision it. The script never uses `exit`, so direct invocation from the principal's interactive PowerShell session does not terminate that shell. It leaves a Room stopped after verification rather than silently restarting production.

Typical invocation:

```powershell
.\verify-feature.ps1 -Base <canonical-main-sha> -Head <feature-head-sha> -RequireDirectParent -FocusedTests @(
    "tests/test_example.py::test_changed_behavior"
)
```

### Human-operated PowerShell procedure standard

For copy/paste procedures issued to the human principal, PowerShell is treated as an operator interface rather than disposable prose. The standard below governs generated one-off procedures unless a specific task requires an explicitly documented exception.

1. **Target PowerShell 7.4+ by default.** The principal's normal interactive shell is PowerShell 7. Maintained repository scripts may deliberately support Windows PowerShell 5.1 or another shell when compatibility requires it, but chat-issued operator blocks should not silently depend on 5.1 behavior.
2. **The complete code block is the unit of execution.** Every procedure must be self-contained, define every variable/function it uses, establish its working directory or derive it safely, and make no dependency on variables or partial state from an earlier pasted block. Corrections are issued as a complete replacement block; never instruct the principal to splice, find/replace, or edit fragments of an earlier procedure.
3. **Use an isolated scope and strict failure policy for nontrivial procedures.** Prefer a script block beginning with `Set-StrictMode -Version Latest`, `$ErrorActionPreference = 'Stop'`, and `$PSNativeCommandUseErrorActionPreference = $true`. If a native command intentionally uses a nonzero exit code as data, isolate and handle that command explicitly rather than weakening the whole procedure.
4. **Do not use the PowerShell backtick as a line-continuation mechanism.** Long command invocations use argument arrays, splatting, parentheses, or natural PowerShell expression continuation. Trailing-space-sensitive backtick continuation is prohibited in operator blocks.
5. **Invoke external programs explicitly and pass complex arguments as arrays.** Prefer `& $executable @arguments` (or `& git @arguments`) over long visually wrapped native-command lines. This keeps tokenization visible and avoids quoting/continuation ambiguity.
6. **Quote conservatively.** Prefer single-quoted strings for literals and double quotes only when interpolation is required. Prefer `Join-Path` for constructed filesystem paths. Avoid complicated expressions inside interpolated strings; use braced variable names, intermediate variables, or format expressions when punctuation could make parsing ambiguous.
7. **Use PowerShell data structures instead of shell-text tricks.** Arrays, hashtables, splatting, and ordinary control flow are preferred to escaped-newline construction, nested command strings, or PowerShell→CMD→PowerShell quoting layers. Cross-shell nesting requires a concrete compatibility reason.
8. **Use here-strings only when embedding another language or a genuinely multiline literal.** Prefer literal single-quoted here-strings (`@' ... '@`) so embedded Python/JSON/etc. is not accidentally interpolated by PowerShell. Here-string delimiters stand alone. Large or recurring embedded programs should become maintained repository files instead of repeatedly pasted payloads.
9. **Preflight before mutation.** Repository-changing procedures should check the relevant working-tree state, fetch/resolve remote refs before relying on them, and verify the intended commit/ref before destructive or verification work. Destructive actions require an explicit guard appropriate to the risk.
10. **Preserve the caller's starting repository state.** Temporary detached-HEAD or branch operations should capture the initial branch/ref and restore that state when practical rather than assuming the caller began on `main`. Do not delete, clean, reset, or overwrite unrelated tracked/untracked work unless that action is explicitly authorized.
11. **Cleanup must not mask the primary failure.** A `finally` block may attempt restoration, but it must not blindly throw and replace an earlier verification/operation error. Preserve the primary failure, capture any restoration failure separately, then report both in priority order after cleanup.
12. **Keep native-command failure handling consistent.** When `$PSNativeCommandUseErrorActionPreference = $true` is active, do not add redundant `$LASTEXITCODE` checks after every native command. Use explicit exit-code inspection only for commands whose nonzero statuses have meaningful non-error semantics or when running under an explicitly broader compatibility mode.
13. **Print phase-level diagnostics, not command chatter.** Use a small number of clear headings such as PRECHECK, VERIFY, RESTORE, and RESULT. Failure messages should identify the failed operation and retain the underlying exception/output needed for diagnosis.
14. **One-off procedures stay pasted; recurring procedures become maintained tooling.** Repeated or operationally important logic should graduate into a versioned `.ps1`/`.cmd`/Python tool with tests rather than being regenerated in chat. The rule is: paste one-off procedures; codify recurring procedures.
15. **Validate generated repository changes before asking the principal to verify them.** Before issuing an exact-head verification block, inspect the complete PR diff for accidental files, trailing whitespace, EOF/newline defects, obvious malformed syntax, and scope drift. Local verification remains authoritative, but trivial formatting defects should be caught before human execution.
16. **Prefer simple, diagnosable PowerShell over terse cleverness.** Avoid aliases, dense one-liners, implicit pipeline-state dependencies, dynamic-scope tricks, and unnecessary metaprogramming. Human pasteability, deterministic behavior, and failure diagnosis take priority over brevity.

The governing interaction convention is therefore: **paste the whole block once; if it fails, return the output; diagnose from evidence; issue a complete corrected block.** Interactive fragment surgery is reserved for explicit forensic/recovery situations, not normal development workflow.

The GitHub Actions workflows previously used for Python and dependency verification were removed from `main` on 2026-09-16 after repeated pre-runner startup failures made them an unreliable routine verification path. Their earlier successful runs remain valid historical evidence for the exact versions they exercised, including E-088. GitHub remains the canonical source-control/history/review bridge. See E-109 for the local-verifier migration and measured reference runs.

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
- use `Restart-Codex-Room.bat` for the QOL restart path: leave the existing browser tab/window untouched, run the normal Kill path, wait five seconds, then start Codex Room with `--no-browser` so the existing UI can reconnect without opening a duplicate tab;
- `Kill-Codex-Room.bat --dry-run` previews the repository-specific process targets without stopping them.

Current shutdown targeting identifies both the repository venv Python process running `-m codex_room` and a dedicated launcher `cmd.exe` identified by the canonical start-script path or the `Codex Room Server` window title. It then includes descendants of those seeds, stops the target set, and verifies the targeted process IDs are gone. Successful shutdown does not pause, so a temporary Kill console can exit immediately; the script pauses only on shutdown failure so diagnostics remain visible.

The kill script deliberately does **not** terminate browser processes. Codex Room opens the UI through the system browser and that process may also own unrelated tabs/windows, so browser teardown remains outside the safe Kill and Restart boundaries. PR #78 removed the earlier Restart `MainWindowTitle` / `CloseMainWindow()` behavior after principal runtime testing showed that closing the title-bearing Chrome process closes the entire top-level Chrome window, including unrelated tabs. `Start-Codex-Room.cmd` now forwards optional server arguments, and Restart launches it with `--no-browser`. The already-loaded UI retries a closed Room WebSocket every 1.5 seconds, so the intended restart path is server-only interruption followed by automatic reconnection of the existing tab. Ordinary Start without arguments still opens the system browser normally.

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

The established `.gitignore` excludes runtime/generated material, including:

- `.venv/`, `venv/`
- `__pycache__/`, `.pytest_cache/`
- `.playwright-cli/`, `node_modules/`
- `output/`
- Python bytecode
- the complete runtime data root `data/`
- `Codex Git Transfer/`

The `data/` boundary is intentionally coarse. Codex Room may add new runtime subdirectories beneath that root without requiring a new Git ignore rule; canonical source, tests, configuration, and maintained documentation do not live there.

No filesystem reorganization was required to establish this boundary.

Important runtime locations still include:

- `data/codex-room.db`
- `data/rooms/`
- `data/institutional/`
- `data/custom-capabilities/`

Generated/runtime data is not evidence of canonical source history merely because it exists under the project root.

## 5. Functional source landmarks

Current canonical source includes these useful areas/symbols:

- `codex_room/models.py` — production v2 API contracts, TransactionDecision actions, Task/Assignment-related request models, and admitted peer execution configurations;
- `codex_room/personalities.py` — protected institutional/structural/protocol instruction composition, neutral standard profile bodies, and C coordination/model-allocation guidance;
- `codex_room/orchestrator.py` — transaction execution/settlement, Task/Assignment/Join orchestration, EVIDENCE/HISTORY/REFRESH handling, provider-context continuity, recovery, usage walls, and coordinator economics telemetry;
- `codex_room/db.py` — durable Rooms/Rounds/Tasks/Assignments/Joins, exact execution state, provider-context lineage, evidence/history/refresh state, migrations, usage continuations, and rollover state;
- `codex_room/agent.py` — Codex SDK/app-server interaction, admitted model enforcement, exact-turn reconciliation, thread creation/resume, compaction, and continuation/recovery preparation;
- `codex_room/capabilities.py` — CORE deterministic registry, discovery/inspection/invocation surface, and standard library;
- `codex_room/custom_capabilities.py`, `custom_capability_registration.py`, `custom_registry.py` — custom package validation, deterministic verification/publication, protected binding, unified custom discovery/invocation;
- `codex_room/transaction_evidence.py` — bounded transaction EVIDENCE execution over authorized sources;
- `codex_room/rollover.py` and rollover paths in runtime/database code — lineage continuation, checkpoint/provenance handling, and exact inherited custom-capability bindings;
- `Start-Codex-Room.cmd`, `Kill-Codex-Room.bat`, `Restart-Codex-Room.bat`, `verify-feature.ps1`, `verify-fast.cmd`, `verify-full.cmd`, `codex-room-cap.cmd`, `codex-room-maint.cmd` — normal Windows launch/shutdown/restart, exact-head and repository verification, capability, and offline-maintenance wrappers;
- `codex_room/maintenance.py` — persistent-data check/backup/verify/guarded-restore implementation;
- `tests/` — regression coverage for transaction settlement, exact execution recovery, provider-context continuity, profiles, capabilities, rollover, Windows launcher contracts, API, and UI behavior.

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

The repeatable operational acceptance specification is `docs/CODEX_ROOM_FUNCTIONAL_ACCEPTANCE_TEST_PLAN.md`. The 2026-09-19 T0–T14 campaign is complete with all tests recorded PASS; E-140 records the T8 hard-restart defect/repair and E-141 records campaign closeout. Preserve that plan as a regression/acceptance specification rather than treating its completed campaign as active work.

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
- preserve or prepare the exact relevant provider context where safely supported, including Assignment-scoped context in production v2;
- release due work through the normal serialized queue;
- repeated usage walls replace the schedule;
- stop/lifecycle changes cancel stale continuation work;
- unrecognized retry formats fail closed.

Current A2 source/test review retired the earlier exact-byte-review caveat for P3; see E-028. Later changes still require version-appropriate verification rather than inheriting that historical result automatically.

## 10. Historical external artifacts

Older repository ZIP snapshots, Room exports, handoff bundles, raw archives, prior GPT Project source attachments, and database/recovery backups remain historical evidence only after the repository-source cutover. Inspect them narrowly when a question requires them.

Do not infer present behavior solely from an old artifact. Prefer the canonical current Git commit/source and dated current evidence.
