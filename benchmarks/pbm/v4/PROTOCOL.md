# PBM v4 common execution protocol

This document is the shared PBM v4 protocol. Desktop and Room use the same benchmark contract. Their adapter documents may differ only where their native platform mechanics require it.

## Principal contract

The principal initiates each platform exactly once by pointing its controller at that platform's PBM v4 adapter protocol.

Normal benchmark operation requires no principal-run preparation, capture, grading, comparison, status, or bundle commands. Those are deterministic protocol responsibilities.

The two platform controllers are outside measured benchmark cognition. Each controller performs only the minimum native initiation required to launch one fresh measured execution.

## Shared measured contract

For both Desktop and Room:

1. Bind the exact current PBM v4 benchmark fingerprint and canonical repository HEAD before measured work starts.
2. Join the same active PBM v4 pair automatically. The principal does not relay a run id between platforms.
3. Prepare the platform workspace from the same versioned seven-task battery. Canary mode substitutes the same tiny canary fixture on both platforms while retaining the production v4 fingerprint binding.
4. Launch one fresh measured execution with the frozen battery instruction:
   `Read BENCHMARK.md and execute it exactly. Do not ask me questions. When complete, stop.`
5. Supply no substantive principal guidance after launch. Native approval controls are permitted only when they add no benchmark substance.
6. Do not coordinate with, wait for, wake, or control the other platform.
7. Capture execution evidence deterministically, grade with the applicable deterministic grader, and classify the arm as `VALID`, `INVALID`, or `FAILED`.
8. Preserve exact provenance and create an evidence bundle automatically.
9. When both independent arms exist for the same fingerprint, compare them deterministically and close the active pair automatically.

A measured arm cannot become `VALID` merely because a result file exists. Protocol intervention, prompt deviation, incomplete provider usage, missing completion evidence, or disallowed terminal state must fail closed.

## Controller boundary

The controller is not the measured benchmark task.

A controller must not solve, inspect, critique, repair, or summarize the benchmark mission. It may read this protocol and its own platform adapter, invoke deterministic PBM commands, launch the measured execution through native platform mechanics, and report protocol status.

Desktop must hand its native measured child thread id to the detached deterministic Desktop monitor and return. The controller model must not act as a durable polling loop. The monitor waits only for that Desktop child's completion evidence and must never wait for Room.

Room must hand its own measured Room execution to the detached deterministic Room worker and return. Agent C must not act as a durable polling loop.

## Modes

**Benchmark mode** is the production seven-task cross-domain battery and is allowed only after `benchmarks/pbm/CURRENT` is deliberately promoted to `v4`.

**Canary mode** uses the same controller/adapters and the same measured launch boundaries with a tiny marker mission. It exists to verify the protocol before full paid execution.

Recovery commands such as status, abort, and bundle remain available, but they are exception paths rather than normal principal choreography.
