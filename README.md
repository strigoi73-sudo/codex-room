# Codex Room

Codex Room is a local browser application for a persistent, inspectable AI organization. Its settled Personal production architecture is a fixed triad of three persistent Codex threads: A — Implementer, B — Verifier, and C — Integrator, communicating through a durable mechanical router while a human observes and intervenes. The current runtime retains two-agent Room compatibility, including adding C to an existing A/B Room.

The application uses the official `openai-codex` Python SDK and its local app-server transport. It reuses the Codex authentication already available on the machine. Normal Room turns are explicitly pinned at the adapter boundary to `gpt-5.6-terra` with `high` reasoning; this Room-local policy does not depend on the user's global Codex model default.

## Install for development and testing

Codex Room requires Python 3.10 or later. From this directory, create an environment and install the application with its test dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints-test.txt ".[test]"
```

`constraints-test.txt` records the known-good application and test dependency versions used by routine development and CI. Dependency upgrades should be deliberate changes to that constraint set rather than incidental resolver drift.

## Start

From this directory, double-click `Start-Codex-Room.cmd`. It starts the local server and opens:

<http://127.0.0.1:8765>

The first start can take several seconds while the Codex app-server initializes. The application stores its SQLite database and per-room shared workspaces under `data/`.

`Start-Codex-Room.cmd` sets `CODEX_ROOM_CODEX_BIN` to the current desktop Codex runtime. Set that environment variable explicitly when a different supported `codex.exe` is required. The adapter otherwise falls back to the runtime pinned by the installed `openai-codex` Python package.

Model choice and reasoning effort are intentionally static Room policy. Codex Room does not route between models or provide automatic model fallback.

For development, the equivalent entry point is:

```powershell
$env:CODEX_ROOM_CODEX_BIN = "C:\path\to\current\codex.exe"
.\.venv\Scripts\python.exe -m codex_room
```

## First run

1. Select **New room**.
2. Enter an opening topic.
3. Optionally edit Agent A/B names, reciprocal developer instructions, safety limits, and whether the new Room should include a fresh Agent C.
4. Create the room. Distinct persistent Codex threads are created for the selected participants and the opening Round remains in `preparing`.
5. Review the staged Round and select **Start Round**. Only the designated starter is invoked.
6. Watch the transcript. Observer messages can target all agents or be delivered privately to one.

Use **New Round** to stage a public prompt, per-participant private initialization, temporary overlays, and a designated starter. Preparation performs no model invocation. **Start Round** schedules only the chosen starter, or every participant independently when that option is selected; waiting participants receive their stored context with their first legitimate conversational turn.

Pause stops new queue claims after active turns finish. Stop interrupts active turns best-effort and cancels queued deliveries. Resume never leaves an empty queue falsely marked as running: if Stop left no runnable work, the Round closes immediately and the next observer message reopens it with fresh work on the same threads. The legacy New Topic API now prepares and immediately starts a Round for compatibility. Reset Agents is deliberately destructive to identity: it archives every participant's old Codex thread, records the IDs in the transcript, and creates replacements.

### Adding Agent C

Every new Personal Room is created as the permanent A/B/C triad. Agent C — the Integrator — is the ordinary default Round starter and human entry point. C may selectively invoke A, B, both, or neither; A and B may communicate directly without routing through C. Public peer messages remain readable to the whole triad while `invoke_targets` controls which peers become runnable.

C is not invoked after every A/B exchange. Passive readable deliveries let C stay durably informed without spending a model turn. If material A/B MESSAGE work remains unread by C when the Round would otherwise settle, the runtime creates one integration opportunity for C before final closure. C then consumes the pending peer material through the normal coalesced delivery path and may synthesize, report, redelegate, or finish.

Historical two-agent Rooms remain valid and are not silently mutated. Their **Upgrade legacy Room to triad** action adds a fresh C thread while preserving the exact A/B identities and histories. The upgrade does not deliver pre-join Room history, private prompts, overlays, or a synopsis to C. New rollover successor Rooms use the permanent triad even when the predecessor was a historical A/B Room.

## Architecture

```text
Browser UI ──HTTP/WebSocket── FastAPI
                              │
                    RoomRuntime (mechanical only)
                     │        │        │
               agent A queue  │  agent B queue  [agent C queue]
                     │        │        │
                     └──────── Codex SDK ────────┘
                              │
                    persistent participant threads

FastAPI / RoomRuntime ── SQLite rooms, agents, events, deliveries
```

- `codex_room/agent.py` — official SDK adapter, structured `MESSAGE` / `PASS` / `FINISH` decisions, interruption, and safe activity summaries.
- `codex_room/orchestrator.py` — serialized per-agent workers, explicit peer delivery, concurrency, lifecycle controls, retry handling, and limits. It never chooses an intellectual position.
- `codex_room/db.py` — additive SQLite migrations, Rooms/Rounds/profiles, atomic batch claims, and durable event consumption. Interrupted `processing` rows return to `pending` at startup.
- `codex_room/main.py` — HTTP, exports, and live WebSocket API.
- `codex_room/static/` — dependency-free observer interface.
- `tests/` — fake-agent routing, persistence, lifecycle, limit, and API coverage without model calls.

### Durable event flow

Every visible event contains an event ID and monotonic room sequence, Room/Round IDs, timestamp, type/class, visibility, source, destination, content, status, related event, conversational/turn/PASS flags, and metadata. A separate delivery row is inserted in the same transaction for each authorized reader, with a per-recipient `runnable` bit recording whether that delivery may initiate cognition. `UNIQUE(event_id, agent_id)` prevents duplicate delivery records; `BEGIN IMMEDIATE` makes routing and claiming atomic. Each agent has exactly one worker, so its turns never overlap, while different participants can run concurrently.

A worker can claim only when at least one pending runnable delivery exists. That atomic claim includes every earlier pending readable delivery for the same agent, in sequence order, through the newest runnable trigger. Passive information newer than that trigger remains pending for a later legitimate invocation; passive information alone never creates a catch-up turn. The model prompt lists every consumed event ID, and activity metadata distinguishes triggering from passive event IDs. Events arriving during a run remain unread and are handled by the same no-overlap backlog machinery. Delivered rows retain `consumed_at`; a FINISH records the input sequence boundary so old or duplicated deliveries at or before it are cancelled rather than reactivating the agent.

Initial and new topics create all intended delivery rows before any worker runs. A peer knows a statement only because an `agent_message` event is explicitly queued to that peer. `PASS` records an event but creates no ordinary follow-up delivery.

`FINISH` is an agent-level ready-to-close state, not an immediate room shutdown. Already-running peer turns are preserved. The discussion closes only after every engaged participant in the applicable runnable delivery boundary has settled with `FINISH` or `PASS`; passive-only readers do not block closure. An agent `MESSAGE` remains public/readable to every peer while optional validated `invoke_targets` select which peers become runnable. A null or omitted target list retains legacy all-peer invocation, and `["all"]` requests it explicitly. A running Room with no active turn and no runnable delivery is reconciled immediately instead of waiting for the inactivity watchdog. Individual SDK turns also have a bounded ten-minute execution lease; expiry is recorded as an explicit terminal agent error rather than an indefinite `RUNNING` state. Manual Stop, topic replacement, archive, errors, and truly obsolete discussion results still invalidate later output and record it as `stale_result` instead of routing it. Limits, inactivity, pause, stop, and archive remain mechanical lifecycle transitions rather than moderator opinions.

### Persistence and privacy

The database retains room configuration, agent names and developer instructions, thread IDs, timestamps, discussion counters, events, delivery attempts, and metadata. On restart, the SDK resumes the exact stored thread IDs. Existing identities are never silently replaced.

Private observer events are marked in both the UI and exports. The source message is delivered only to its target. The recipient remains intellectually autonomous and may decide whether to mention it in a later peer message. Hidden reasoning is never stored or rendered; only final messages, explicit outcomes, lifecycle states, and coarse tool/activity categories are observable.

Reusable Agent A/B profiles live separately from Room overrides and Round overlays. A new Room snapshots the current persistent profiles into its independent threads. Later A/B profile edits affect future Rooms only; a Room override changes only that Room, and temporary overlays are injected only for their Round. Agent C uses a fixed, read-only Integrator template so joining cannot smuggle prior Room context into its identity prompt.

## API summary

- `POST /api/rooms` and `GET /api/rooms/{id}`
- `POST /api/rooms/{id}/agents` (currently supports the additive `agent_c` join)
- `POST /api/rooms/{id}/messages`
- `POST /api/rooms/{id}/rounds` (prepare without running)
- `POST /api/rooms/{id}/rounds/{round_id}/start`
- `GET|PUT /api/profiles/defaults`
- `POST /api/rooms/{id}/pause|resume|stop|new-topic`
- `POST /api/rooms/{id}/archive|unarchive|reset`
- `GET /api/rooms/{id}/export?format=markdown|json`
- `WS /ws/rooms/{id}`

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The automated suite verifies distinct identities, N-participant routing and settlement, separate histories, PASS behavior, observer targeting, pause/resume, persistence across runtime restarts, runaway limits, compaction continuity, deliberate reset/archive auditing, exports, two-agent compatibility, and Agent C's fresh-context boundary.

`test-transcript-stability.ps1` is a specialized browser transcript check. It is excluded from the routine Python test suite because it requires Node.js plus an installed Chrome or Edge browser; run it separately when that browser-level coverage is needed.

## Roadmap

- Multiple simultaneously selected room dashboards
- Asymmetric evidence experiments and experiment presets
- First-class private A/private B/shared filesystem layouts and controlled external tools
- Editable personalities after creation with versioned instruction history
- Conversation branching, replay, search, and transcript analytics
- Git repository and worktree collaboration modes
- Rich streamed tool progress and aggregate usage/cost views
- Configurable retry/backoff policies and failed-delivery replay controls
