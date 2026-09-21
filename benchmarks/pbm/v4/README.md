# PBM v4 — common protocol with thin platform adapters

PBM v4 compares one fresh native Codex Desktop measured execution with one fresh ordinary Codex Room measured execution over the same frozen seven-task cross-domain battery.

The principal does not orchestrate preparation, capture, grading, bundling, or comparison. Each platform is pointed once at its adapter protocol and carries its own procedure through to completion.

## Common protocol

The normative shared procedure is `PROTOCOL.md`.

Both platforms bind the same v4 fingerprint, prepare equivalent copies of the seven-task battery, launch the same frozen measured instruction, forbid substantive follow-up principal guidance, classify results as VALID / INVALID / FAILED, capture evidence deterministically, and auto-bundle. The protocol also captures the read-only Codex provider usage/rate-limit meter at protocol start and protocol completion; the final comparison surfaces before/after values and deltas alongside the primary rollout/Room token accounting. The independent arms never wait for or control one another. When both results exist for the active fingerprint, deterministic comparison closes the pair automatically.

The measured battery instruction remains exactly:

`Read BENCHMARK.md and execute it exactly. Do not ask me questions. When complete, stop.`

The platform controller is outside measured benchmark cognition.

## Desktop initiation

Open a fresh top-level native Codex Desktop controller task rooted at:

`C:\Codex Room\pbm_desktop_controller`

Give it exactly one controller instruction:

`Read V4_PROTOCOL.md and execute it exactly.`

The Desktop adapter prepares the measured workspace and creates one fresh native child task with the deterministic delegated prompt. It immediately hands the returned child thread id to a detached deterministic Desktop monitor and stops. The monitor waits only for that child's completion evidence, captures and grades it, bundles evidence, and closes the pair if Room is already complete. Neither the controller nor the monitor waits for Room.

For bounded protocol validation before promotion, use:

`Read V4_PROTOCOL.md and execute it exactly in canary mode.`

## Room initiation

PBM v4 uses one persistent non-measured Room controller titled:

`PBM v4 Room Runner`

It is installed deterministically with:

`pbm-v4-protocol.ps1 install-room-runner`

That installation is setup, not a per-run benchmark step.

For an ordinary benchmark run, create a controller Round in that Room and give C exactly one instruction:

`Read PBM_ROOM_PROTOCOL.md and execute it exactly.`

C invokes the Room adapter once and returns. The deterministic detached Room worker creates one fresh ordinary measured Room, starts it, waits only for that Room, captures and grades it, bundles evidence, and stops. C does not poll the measured Room and does not act as a durable event loop.

For bounded protocol validation before promotion, use:

`Read PBM_ROOM_PROTOCOL.md and execute it exactly in canary mode.`

## Recovery

Recovery is exceptional, not normal principal choreography. Deterministic status, abort, and bundle operations remain available through `pbm-v4-protocol.ps1`.

## Promotion

PBM v4 is not canonical merely because these assets exist. `benchmarks/pbm/CURRENT` remains unchanged until I-026's promotion gate is satisfied using the common protocol path: battery/grader audit, focused verification, one-instruction Desktop canary, one-instruction Room canary, and verified recovery/evidence paths. The canary validates protocol mechanics only; comparative token-efficiency measurement comes from the seven-task benchmark battery.
