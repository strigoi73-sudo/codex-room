# PBM v4 — independent complementary one-paste benchmarks

PBM v4 replaces v3's live cross-platform controller with two independent measured executions over one frozen integrated mission.

## Operator contract

The benchmark prompt is exactly:

`Read BENCHMARK.md and execute it exactly. Do not ask me questions. When complete, stop.`

That exact text is pasted once into a fresh Codex Desktop task and once as the public prompt of a fresh Codex Room Round. No substantive follow-up benchmark guidance is permitted.

Desktop and Room never wait for, wake, or control one another. Deterministic PBM tooling prepares equivalent workspaces, captures execution evidence, grades the finished workspaces, classifies each arm as VALID / INVALID / FAILED, and compares them only after both independent results exist.

## Preparation

Run from the repository root:

```powershell
.\pbm-v4.ps1 prepare-pair
```

The command:

- audits the frozen mission and grader against the hidden reference solution;
- requires a clean tracked working tree;
- creates one PBM v4 pair run;
- prepares the Desktop workspace;
- creates one fresh ordinary production Room in PREPARING state without starting cognition;
- stages the same fixture into that Room workspace;
- prints the Desktop workspace, Room id/title, and exact one-paste prompt.

## Desktop arm

Open a fresh top-level native Codex Desktop task rooted exactly at the printed Desktop workspace. Paste the exact benchmark prompt once. Do not send follow-up guidance.

After the task stops, capture deterministically:

```powershell
.\pbm-v4.ps1 complete-desktop --run-id '<run-id>'
```

If more than one matching fresh rollout exists, rerun that command with `--thread-id '<thread-id>'`.

## Room arm

Open the prepared Room. Its initial staging Round is deliberately not started.

1. Click **New round**.
2. Paste the exact benchmark prompt once into **Public prompt**.
3. Keep **Agent C** as the starting agent, with ordinary production work-model-v2 / assignment-thread behavior.
4. Prepare and start the Round.
5. Do not send observer messages, pause/resume, stop, or answer a substantive principal consultation during measured work.

After the Room settles, capture deterministically:

```powershell
.\pbm-v4.ps1 complete-room --run-id '<run-id>'
```

A substantive `CONSULT_PRINCIPAL`, observer intervention, or protocol deviation makes the Room arm INVALID. Runtime/terminal failure without protocol contamination is FAILED.

## Comparison

After both independent captures:

```powershell
.\pbm-v4.ps1 compare --run-id '<run-id>'
```

Comparison is marked comparable only when both arms are VALID and share the exact v4 fingerprint. Quality failure is still valid benchmark evidence; protocol validity is separate from task correctness.

## Operations

Read-only status:

```powershell
.\pbm-v4.ps1 status --run-id '<run-id>'
```

Abort a pair without improvising PID/API surgery:

```powershell
.\pbm-v4.ps1 abort --run-id '<run-id>'
```

Create an evidence bundle:

```powershell
.\pbm-v4.ps1 bundle --run-id '<run-id>'
```

## Promotion

PBM v4 is not canonical merely because these assets exist. `benchmarks/pbm/CURRENT` remains unchanged until the I-026 promotion gate is satisfied: mission/grader audit, focused and routine verification, one-paste Desktop canary, one-paste Room canary, and verified status/abort/bundle paths.
