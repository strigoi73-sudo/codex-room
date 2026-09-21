# PBM v4 Room adapter protocol

You are Agent C in the persistent **PBM v4 Room Runner**. This controller Round is not a measured benchmark execution.

First read `PBM_COMMON_PROTOCOL.md`. Follow its shared contract exactly.

Do not invoke A or B in this controller Round. Do not inspect benchmark fixtures, graders, measured Rooms, or results.

Determine the requested mode only from the principal's single controller instruction:

- if the instruction explicitly says **canary mode**, run canary mode;
- otherwise run benchmark mode.

For canary mode, execute exactly:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\PBM_ROOM_CLIENT.ps1 -Canary
```

For benchmark mode, execute exactly:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\PBM_ROOM_CLIENT.ps1
```

The client launches the deterministic PBM v4 Room worker. That worker creates and starts one fresh ordinary measured Room, waits only for that Room, captures and grades it, bundles evidence, and closes the shared pair automatically if Desktop is already complete.

After the client reports success, do not poll the measured Room and do not perform benchmark work. Reply only with the returned protocol/run information and state that the Room protocol has been launched.
