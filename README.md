# Codex Room

> **Project status: RETIRED — 2026-09-27**
>
> Codex Room was an experiment in persistent multi-agent organization around Codex. It became a substantial working system, but controlled comparisons against Codex Desktop did not establish enough practical benefit to justify the added orchestration complexity and execution cost. Active development has ended.
>
> The repository is preserved so other people can inspect, run, modify, or learn from the experiment. It is not an actively maintained product and should not be treated as a supported replacement for Codex Desktop.

## What Codex Room was

Codex Room is a local browser application for a persistent, inspectable AI organization built around a fixed triad of **Agent A, Agent B, and Agent C**.

- **A and B** are neutral epistemic peers.
- **C** is also an epistemic peer, with protected coordination responsibility.
- C controls coordination, not judgment.
- The human principal retains authority over objectives, intervention, and closure.

The production work model is transaction-based:

```text
Room
└─ Round
   └─ Task
      ├─ Assignment
      ├─ Assignment
      └─ Join / integration / settlement state
```

Codex Room uses the official `openai-codex` Python SDK and local app-server transport, reusing Codex authentication already available on the machine.

## Why development ended

The project ultimately asked a simple product question:

**Does persistent A/B/C organization create enough practical value over ordinary Codex Desktop to justify its additional complexity and execution cost?**

Two benchmark families were built to answer that question.

### PBM

The paid seven-task PBM v5 comparison produced equal deterministic correctness but substantially higher Room cost:

- Desktop: **371,378 measured tokens**, **292.069 s**
- Room: **1,473,150 measured tokens**, **628.984 s**
- Room/Desktop token ratio: **3.9667**

A controlled C-only follow-up reduced Room overhead substantially, but still remained above the Desktop baseline.

### OUB v2

OUB v2 then tested whether Room-specific organization would produce a compensating practical advantage when both platforms were free to organize naturally across a frozen three-task external CooperBench sample.

Across the three measured comparisons:

- Desktop passed **4/6** frozen CooperBench features.
- Room passed **2/6**.
- Desktop used **2,140,189 provider tokens**.
- Room used **2,497,972 provider tokens**.
- Room/Desktop token ratio: **1.1672**.
- Aggregate measured task duration was effectively a wash: **737.707 s Desktop** versus **722.349 s Room**.
- Desktop used **0 native descendants**.
- Room made **3 peer invocations**.

This mattered because Room coordination actually activated. The experiment therefore did not end merely because C failed to use A/B; the architecture was exercised and still did not establish the practical advantage the project was looking for.

These measurements do **not** prove that multi-agent systems in general are inferior, nor do they establish a universal ranking between every possible Room workflow and every future Codex Desktop configuration. They do answer the narrower product question Codex Room was built to investigate.

See [RETIREMENT.md](RETIREMENT.md) for the project closeout and the maintained records under [docs/project/](docs/project/).

## What remains useful

Although the product direction was retired, the repository contains reusable engineering and experimental work around:

- persistent multi-agent coordination;
- transaction-oriented Task / Assignment / Join state;
- exact provider-thread provenance;
- dynamic model and reasoning-effort allocation;
- deterministic capability registration and reuse;
- provider usage accounting;
- restart and continuation semantics;
- Room exports and evidence capture;
- benchmark design for platform-level AI comparisons;
- Windows / PowerShell / WSL operational integration;
- deterministic grading and exact-version verification.

The negative result is part of the value of the repository: it documents a serious attempt to measure whether additional orchestration complexity paid for itself.

## Running the archived project

Codex Room was developed and validated primarily on Windows with PowerShell and WSL. Upstream Codex behavior may change after this repository's retirement, so successful setup is not guaranteed indefinitely.

### Requirements

- Python 3.11 or later
- a supported Codex installation/runtime
- Codex authentication already available on the machine

### Install

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints-test.txt ".[test]"
```

### Start

Double-click:

```text
Start-Codex-Room.cmd
```

The local application normally opens at:

```text
http://127.0.0.1:8765
```

Use `Kill-Codex-Room.bat` to stop the local runtime and `Restart-Codex-Room.bat` for the normal server-only restart path.

Runtime state is stored under `data/`, which is intentionally excluded from version control.

## First run

1. Select **New room**.
2. Enter an opening objective/topic.
3. Optionally adjust participant names/profile overrides and safety limits.
4. Create the Room.
5. Review the staged Round.
6. Select **Start Round**.

New Personal Rooms contain A/B/C. C is the ordinary default starter.

## Verification

The repository's historical local verification entry points remain:

```powershell
.\verify-fast.cmd
```

and:

```powershell
.\verify-full.cmd
```

The raw Python suite is also available:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

These commands describe the project as retired. They are not a promise of future compatibility with later Codex releases.

## Benchmarks and project records

- `benchmarks/pbm/` — platform benchmark family
- `benchmarks/oub/` — organizational utility benchmark family
- `docs/project/05_DECISION_REGISTER.md` — settled design and product decisions
- `docs/project/06_DEVELOPMENT_CONTROL.md` — final development state
- `docs/project/07_EVIDENCE_REGISTER.md` and `07a_EVIDENCE_REGISTER_CONTINUATION.md` — empirical evidence
- `docs/project/08_PRODUCT_VISION.md` — preserved historical product vision

Large runtime outputs, local databases, benchmark workspaces, and generated evidence bundles remain intentionally excluded from the repository.

## Support status

This repository is provided as archived experimental software.

- No active feature development is planned.
- No compatibility commitment is made for future Codex versions.
- No production security support or SLA is provided.
- Use it locally and experimentally at your own risk.

## License and third-party material

Original Codex Room source is released under the [MIT License](LICENSE).

Some benchmark specifications and test patches were copied from external projects for reproducible evaluation. Those materials retain their applicable upstream terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Codex and OpenAI are trademarks or products of OpenAI. Codex Room is an independent experimental project and is not an official OpenAI product.
