# PBM v4 bounded common-protocol canary

This canary verifies the same PBM v4 controller/adapters used by production benchmark mode without spending a full integrated mission.

The canary keeps the production v4 fingerprint binding and the exact measured instruction:

`Read BENCHMARK.md and execute it exactly. Do not ask me questions. When complete, stop.`

Its tiny fixture only requires an exact completion marker. It does not measure comparative task performance.

## Desktop

Point a fresh Desktop controller at the normal adapter in canary mode:

`Read V4_PROTOCOL.md and execute it exactly in canary mode.`

The controller performs preparation, native fresh-task launch, capture, classification, and bundling itself. The principal does not run intermediate commands.

## Room

Use the persistent `PBM v4 Room Runner` and point C at the normal adapter in canary mode:

`Read PBM_ROOM_PROTOCOL.md and execute it exactly in canary mode.`

C launches the detached deterministic worker and returns. The worker creates the fresh measured canary Room and performs capture/classification/bundling without principal choreography.

A canary pair passes only when both independent platform results are VALID and share the exact same production v4 fingerprint.

The older `pbm-v4-canary.ps1` commands remain diagnostic/recovery tooling for historical canary evidence. They are not the canonical operator path after D-049.
