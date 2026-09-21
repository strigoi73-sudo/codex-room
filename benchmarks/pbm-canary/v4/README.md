# PBM v4 bounded one-paste canary

This canary verifies the live native one-paste protocol without spending a full PBM mission.

The canary uses the exact production v4 paste:

`Read BENCHMARK.md and execute it exactly. Do not ask me questions. When complete, stop.`

It gives Desktop and Room the same tiny workspace instruction: create and verify one exact JSON marker, then stop. It does not measure comparative task performance.

## Deterministic operations probe

Before paid cognition:

```powershell
.\pbm-v4-canary.ps1 probe-operations
```

This creates a prepared Room without starting cognition, checks live status, aborts it through the canonical Room stop endpoint, rechecks status, and creates an evidence bundle.

## Live pair canary

Prepare:

```powershell
.\pbm-v4-canary.ps1 prepare-pair
```

Then follow the printed Desktop and Room steps. Each platform receives exactly one substantive paste.

Capture:

```powershell
.\pbm-v4-canary.ps1 complete-desktop --run-id '<run-id>'
.\pbm-v4-canary.ps1 complete-room --run-id '<run-id>'
.\pbm-v4-canary.ps1 verify-pair --run-id '<run-id>'
.\pbm-v4-canary.ps1 bundle --run-id '<run-id>'
```

A canary passes only if both platform classifications are `VALID` and both are bound to the same already-verified PBM v4 production fingerprint.

The canary assets live outside `benchmarks/pbm/v4` and the canary implementation is not a v4 `implementation_file`; therefore adding or changing canary-only scaffolding does not silently alter the verified production benchmark fingerprint.
