# OUB v1 harness

The OUB v1 harness measures one naturalistic Desktop arm and one naturalistic Codex Room arm against the frozen O1 asset.

## Operator flow

1. Start Codex Room normally.
2. Run `./oub-v1.ps1 prepare`.
3. Open exactly one fresh top-level Codex Desktop task rooted at the printed `desktop_workspace`.
4. Send the printed `desktop_instruction` exactly once.
5. Do not provide substantive guidance to either measured arm.
6. Use `./oub-v1.ps1 status` for read-only progress inspection.
7. When both arms finish, the harness writes comparison JSON/Markdown and an evidence ZIP.

The Room arm starts automatically after preparation. Desktop remains native: the harness discovers the fresh top-level rollout by prepared workspace and includes all native descendants in measured usage.

## Measurement

OUB records quality, measured tokens, duration, and orchestration separately.

It does not compute an overall winner.

Desktop measurement includes the root task plus native descendants. Room measurement includes every measured execution in the Room round.

## Safety ceiling

O1 targets roughly 10–15 minutes of capable-model work per platform. The detached harness workers use a 30-minute safety ceiling so an unexpectedly pathological arm does not remain monitored indefinitely. This is a harness protection boundary, not a claim that 30 minutes is the intended task duration.

## Commands

- `./oub-v1.ps1 audit`
- `./oub-v1.ps1 prepare`
- `./oub-v1.ps1 status [--run-id RUN_ID]`
- `./oub-v1.ps1 abort [--run-id RUN_ID]`
- `./oub-v1.ps1 bundle --run-id RUN_ID`

The asset fingerprint is frozen independently from harness implementation.
