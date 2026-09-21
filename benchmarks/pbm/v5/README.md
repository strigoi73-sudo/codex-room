# PBM v5 — platform outcomes, native internal workflow

PBM v5 preserves the PBM v4 seven-task cross-domain battery and graders while correcting the benchmark control boundary.

PBM measures **Desktop versus Room**, not a prescribed subagent choreography.

Preparation creates equivalent platform workspaces, starts the measured Room through the normal Room runtime, and starts deterministic monitors. Desktop is then launched as one fresh top-level native task in the prepared Desktop workspace with the frozen battery instruction. Desktop may use any native internal organization it chooses. PBM aggregates the root Desktop rollout and all native descendants into the Desktop platform usage total.

The Room remains free to use normal A/B/C coordination under the same mission.

Run preparation with:

`pbm-v5.ps1 prepare`

Then open one fresh top-level Codex Desktop task rooted at the returned `desktop_workspace` and give it exactly the returned `desktop_instruction`.

Do not provide substantive follow-up guidance to either platform.

Use `pbm-v5.ps1 status` for deterministic inspection and `pbm-v5.ps1 abort` only for recovery.

PBM v4 remains frozen as the promoted predecessor whose Desktop adapter prescribed one child-task launch. No paid seven-task v4 comparison was completed.
