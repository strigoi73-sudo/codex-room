from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, AsyncIterator

from .agent import (
    ROOM_MODEL,
    ROOM_REASONING_EFFORT,
    AgentAdapter,
    AgentDecisionValidationError,
    AgentRunResult,
    AgentTurnTerminalError,
    AgentTurnStateUnknownError,
    InterruptOutcome,
)
from .capabilities import CORE_CAPABILITIES
from .custom_capabilities import CustomCapabilityPackageError
from .custom_capability_registration import (
    CustomCapabilityPublicationError,
    CustomCapabilityVerificationError,
    VerificationReceipt,
    publish_verified_custom_capability,
)
from .custom_registry import (
    CustomCapabilityRegistryError,
    bind_custom_registration,
    discard_rollover_custom_capabilities,
    inherit_room_custom_capabilities,
    load_room_custom_capabilities,
)
from .db import Database, utc_now
from .institutional import (
    InstitutionalRelease,
    institutional_release_root,
    resolve_institutional_release,
    stage_institutional_release,
    verify_materialized_release,
)
from .models import (
    AddAgentRequest,
    AgentDecision,
    AgentStatus,
    BindInstitutionalReleaseRequest,
    CreateRoomRequest,
    EXECUTION_CONFIGS,
    NewTopicRequest,
    ObserverMessageRequest,
    Outcome,
    TransactionAction,
    TransactionDecision,
    PrepareRoundRequest,
    RolloverRoomRequest,
    RoomStatus,
    HistoryRequest,
    SourceEvidenceRequest,
    UpdateRoomRequest,
)
from .runtime_info import collect_runtime_provenance
from .transaction_evidence import execute_source_evidence


@dataclass(slots=True)
class WorkerSlot:
    generation: int
    task: asyncio.Task[None] | None
    wakeup: asyncio.Event
    phase: str = "idle"
    batch_id: str | None = None
    phase_started_at: str | None = None
    last_progress_at: str | None = None
    quarantined: bool = False
    reason: str = "Worker is idle."


class AgentTurnTimeoutError(TimeoutError):
    """A persistent agent turn exceeded the Room's bounded execution lease."""


class LiveHub:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)

    @asynccontextmanager
    async def subscribe(self, room_id: str) -> AsyncIterator[asyncio.Queue[dict[str, Any]]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        self._subscribers[room_id].add(queue)
        try:
            yield queue
        finally:
            self._subscribers[room_id].discard(queue)

    def publish(self, room_id: str, payload: dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(room_id, set())):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(payload)


class RoomRuntime:
    CONTEXT_COMPACTION_RATIO = 0.30
    CONTEXT_COMPACTION_MIN_GROWTH_TOKENS = 25_000
    STOP_RETIRE_TIMEOUT_SECONDS = 2.0
    LONG_RUNNING_SECONDS = 60.0
    AGENT_TURN_TIMEOUT_SECONDS = 600.0
    USAGE_WALL_ERROR_CODES = frozenset(
        {"usageLimitExceeded", "usage_limit_exceeded"}
    )
    USAGE_CONTINUATION_GRACE_SECONDS = 60
    USAGE_CONTINUATION_INSTRUCTION = (
        "Your previous work was interrupted because Codex reached a usage limit. "
        "The reported retry period has passed. Continue the interrupted work from "
        "where you left off, using the existing Room/thread context. Do not redo "
        "completed work solely because this is a continuation wake."
    )
    DETERMINISTIC_CAPABILITY_INSTRUCTION = (
        "<deterministic_capabilities>\n"
        "Minimize model/tool continuations. For ordinary one-off workspace reads, searches, "
        "inspection, and simple commands, use native workspace tools directly; do not inspect "
        "the capability registry merely because a step is mechanical. Batch related independent "
        "reads/searches when their need is already known, do not batch speculative dependent "
        "follow-ups, and stop retrieving once evidence is sufficient. "
        "Use registered capabilities when they materially add exact semantics, reuse, provenance, "
        "or useful mechanical complexity. Use 'codex-room-cap list' only when a needed capability "
        "identity is unknown, and 'codex-room-cap inspect CAPABILITY_ID' only when its current "
        "contract is needed. For source inspection use the direct 'codex-room-cap source' "
        "surface rather than generic inline-JSON 'invoke inspect_source' when the direct surface "
        "can express the operation. Search and search-many paths may identify either a file or "
        "directory; keep "
        "max-matches within 1-100 and max-files within 1-200. When heterogeneous find/search/read "
        "requests and their bounds are already known, prefer one declarative 'codex-room-cap source "
        "bundle' plan so CORE executes them and returns one normalized evidence bundle. Use "
        "search-many/read-many directly when one homogeneous batch is sufficient. Do not place "
        "speculative dependent follow-ups in a bundle; retrieve again only for a specific unresolved "
        "dependency. Do not inspect CORE or another Room "
        "unless the current task requires it; an explicit workspace-only instruction forbids it. "
        "Invoke known capabilities with 'codex-room-cap invoke CAPABILITY_ID --input-json JSON_OBJECT'; "
        "if shell quoting is fragile, use '--input-file WORKSPACE_RELATIVE_JSON'. Avoid redundant "
        "list/inspect calls and ceremony-only continuations. Create/register custom deterministic "
        "software only when reuse, reliability, provenance, or mechanical complexity earns that "
        "cost; use 'codex-room-cap authoring' and "
        "'codex-room-cap register CAPABILITY_ID --cases-file WORKSPACE_RELATIVE_JSON'. Registration "
        "is not active until the agent turn settles. Deterministic software supports judgment; it "
        "does not replace it.\n"
        "</deterministic_capabilities>"
    )
    TRANSACTION_EVIDENCE_INSTRUCTION = (
        "<deterministic_evidence>\n"
        "For read-only source evidence from your workspace, CORE, or another Room shared "
        "workspace, declare the bounded evidence you need with transaction action EVIDENCE. "
        "Use atomic READ, SEARCH, or FIND requests and include only the source, path/query, "
        "Room ID when applicable, and useful bounds. Every request path must be non-empty. "
        "For source='core', select a maintained top-level entry: use 'codex_room' for CORE "
        "implementation source, 'tests' for tests, or 'docs' for documentation; do not use "
        "an empty path or '.' as the CORE root. CORE validates authority, chooses any "
        "single/batched/bundled inspect_source execution mechanically, and returns normalized "
        "evidence to this same assignment. Do not use shell commands, codex-room-cap, registry "
        "discovery, bundle/read-many/search-many selection, or JSON transport mechanics for "
        "source retrieval when EVIDENCE can express the need. Ask for another EVIDENCE action "
        "only when returned evidence exposes a specific unresolved dependency. Other shell and "
        "registered-capability work remains available when the task genuinely requires it.\n"
        "</deterministic_evidence>"
    )
    TRANSACTION_HISTORY_INSTRUCTION = (
        "<room_history>\n"
        "When this assignment needs a specific fact or result from an earlier Round in this "
        "same Room and that history is not already supplied, declare the bounded need with "
        "transaction action HISTORY. Use RECENT for a temporal dependency or SEARCH with one "
        "specific lexical query when you know the relevant concept; optionally restrict the "
        "request to one agent and request only as many results as are likely necessary. CORE "
        "selects only durable completed Assignment results from earlier Rounds and returns the "
        "exact bounded result events to this same assignment. Do not use HISTORY to recover "
        "current Task/Join/Evidence state already supplied in the assignment envelope, to read "
        "source files, or for broad catch-up. Ask again only when the returned history leaves a "
        "specific unresolved dependency.\n"
        "</room_history>"
    )
    TRANSACTION_HISTORY_CONTEXT_MAX_CHARS = 24_000
    TRANSACTION_CAPABILITY_INSTRUCTION = (
        "<deterministic_capabilities>\n"
        "Registered deterministic capabilities remain available for non-source work when they "
        "materially add exact semantics, reuse, provenance, or useful mechanical complexity. "
        "If the capability identity is already known, invoke it directly; use 'codex-room-cap "
        "list' only when identity is unknown and 'codex-room-cap inspect CAPABILITY_ID' only "
        "when its current contract is needed. Invoke a known capability with 'codex-room-cap "
        "invoke CAPABILITY_ID --input-json JSON_OBJECT', using a workspace-relative input file "
        "only when structured shell transport requires it. Create/register custom deterministic "
        "software only when reuse, reliability, provenance, or mechanical complexity earns the "
        "cost; use the existing authoring/registration contract. Registration becomes active "
        "only after the agent turn settles. Source retrieval belongs to EVIDENCE, not this CLI "
        "surface. Deterministic software supports judgment; it does not replace it.\n"
        "</deterministic_capabilities>"
    )


    def __init__(self, db: Database, adapter: AgentAdapter, data_root: Path) -> None:
        self.db = db
        self.adapter = adapter
        self.data_root = data_root
        self.hub = LiveHub()
        self.auth_info: dict[str, Any] = {"authenticated": False}
        self.provenance = collect_runtime_provenance(
            model=ROOM_MODEL,
            reasoning_effort=ROOM_REASONING_EFFORT,
        )
        self._watchdog_last_started_at: str | None = None
        self._watchdog_last_success_at: str | None = None
        self._watchdog_last_error_at: str | None = None
        self._watchdog_last_error: str | None = None
        self._watchdog_failure_count = 0
        self._watchdog_consecutive_failures = 0
        self._workers: dict[tuple[str, str], asyncio.Task[None]] = {}
        self._wakeups: dict[tuple[str, str], asyncio.Event] = {}
        self._worker_slots: dict[tuple[str, str], WorkerSlot] = {}
        self._worker_generations: dict[tuple[str, str], int] = defaultdict(int)
        self._shutdown = asyncio.Event()
        self._watchdog: asyncio.Task[None] | None = None
        self._lifecycle_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._background_tasks: set[asyncio.Task[Any]] = set()

    def health_status(self) -> dict[str, Any]:
        watchdog_status = (
            "degraded"
            if self._watchdog_consecutive_failures
            else "healthy"
            if self._watchdog_last_success_at is not None
            else "starting"
        )
        return {
            "ok": watchdog_status != "degraded",
            "codex": self.auth_info,
            "provenance": self.provenance,
            "maintenance": {
                "watchdog": {
                    "status": watchdog_status,
                    "last_started_at": self._watchdog_last_started_at,
                    "last_success_at": self._watchdog_last_success_at,
                    "last_error_at": self._watchdog_last_error_at,
                    "last_error": self._watchdog_last_error,
                    "failure_count": self._watchdog_failure_count,
                    "consecutive_failures": self._watchdog_consecutive_failures,
                }
            },
        }

    async def initialize(self) -> None:
        await self.db.initialize()
        await self.db.recover_interrupted_work()
        self.auth_info = await self.adapter.initialize()
        await self._recover_rollovers()
        await self._recover_transaction_evidence()
        rooms = await self.db.list_rooms(include_archived=False)
        for room in rooms:
            if room["status"] == RoomStatus.RUNNING:
                agents = await self.db.get_agents(room["id"])
                if all(agent.get("thread_id") for agent in agents):
                    await self.ensure_workers(room["id"])
        self._watchdog = asyncio.create_task(self._watchdog_loop(), name="room-watchdog")

    async def close(self) -> None:
        self._shutdown.set()
        for wakeup in self._wakeups.values():
            wakeup.set()
        if self._watchdog is not None:
            self._watchdog.cancel()
            await asyncio.gather(self._watchdog, return_exceptions=True)
        tasks = [task for task in self._workers.values() if not task.done()]
        if tasks:
            _, pending = await asyncio.wait(tasks, timeout=2)
        else:
            pending = set()
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        # Worker done-callbacks publish one final observer-visible retirement
        # snapshot. Let the callbacks register those tasks, then drain them before
        # the test/application event loop closes.
        await asyncio.sleep(0)
        background = [task for task in self._background_tasks if not task.done()]
        if background:
            await asyncio.gather(*background, return_exceptions=True)
        await self.adapter.close()

    async def create_room(self, request: CreateRoomRequest) -> dict[str, Any]:
        room_id = await self.db.create_room(request)
        workspace = self.workspace(room_id)
        workspace.mkdir(parents=True, exist_ok=True)
        agents = await self.db.get_agents(room_id)

        starts = await asyncio.gather(
            *(self.adapter.start_agent(agent, workspace) for agent in agents),
            return_exceptions=True,
        )
        errors: list[str] = []
        thread_ids: dict[str, str] = {}
        for agent, result in zip(agents, starts, strict=True):
            if isinstance(result, BaseException):
                message = f"{agent['name']} thread creation failed: {result}"
                errors.append(message)
                await self.db.set_agent_status(agent["id"], AgentStatus.ERROR, str(result))
            else:
                thread_ids[agent["agent_key"]] = result
                await self.db.set_agent_thread(agent["id"], result)

        if len(set(thread_ids.values())) != len(thread_ids):
            errors.append("Codex returned duplicate thread IDs; Room refused to start")
        if errors or len(thread_ids) != len(agents):
            await self.db.set_room_status(room_id, RoomStatus.ERROR)
            event = await self.db.create_event(
                room_id,
                "error",
                "room",
                "observer",
                "\n".join(errors) or "Agent initialization was incomplete",
                status="error",
            )
            self._publish_event(event)
            raise RuntimeError(f"Room {room_id} could not initialize: {'; '.join(errors)}")

        await self.db.set_room_status(room_id, RoomStatus.PREPARING)
        created = await self.db.create_event(
            room_id,
            "room_created",
            "room",
            "observer",
            f"Room created with {len(agents)} independent persistent Codex threads.",
            metadata={"thread_ids": thread_ids},
        )
        self._publish_event(created)
        room = await self._required_room(room_id)
        round_item = await self.db.get_round(room["active_round_id"])
        assert round_item is not None
        await self._record_round_preparation(room_id, round_item)
        if request.auto_start:
            await self._activate_round(room_id, round_item["id"])
        else:
            await self.publish_state(room_id)
        return await self._required_snapshot(room_id)

    async def rollover(
        self, source_room_id: str, request: RolloverRoomRequest
    ) -> dict[str, Any]:
        """Create a fresh-thread successor from one reviewed visible checkpoint."""
        async with self._lifecycle_locks[source_room_id]:
            source = await self._required_room(source_room_id)
            committed = source.get("metadata", {}).get("rollover_successor")
            checkpoint_hash = hashlib.sha256(request.checkpoint.encode("utf-8")).hexdigest()
            if committed:
                if committed.get("checkpoint_sha256") != checkpoint_hash:
                    raise ValueError("This Room has already rolled over with another checkpoint")
                committed_release = (committed.get("institutional_release") or {}).get(
                    "manifest_sha256"
                )
                if (
                    request.institutional_release_sha256 is not None
                    and request.institutional_release_sha256 != committed_release
                ):
                    raise ValueError("This Room has already rolled over with another release")
                return await self._required_snapshot(committed["room_id"])
            slots = [
                slot
                for (room_id, _), slot in self._worker_slots.items()
                if room_id == source_room_id and slot.phase not in {"idle", "stopped"}
            ]
            agents = await self.db.get_agents(source_room_id)
            active = [
                agent["agent_key"]
                for agent in agents
                if await self._adapter_has_active_run(agent["id"])
            ]
            if slots or active:
                raise ValueError("Room rollover requires no active worker, compaction, or SDK turn")
            carried_release = (source.get("metadata", {}).get("institutional_release") or {}).get(
                "manifest_sha256"
            )
            selected_release = request.institutional_release_sha256 or carried_release
            release = (
                resolve_institutional_release(self.data_root, selected_release)
                if selected_release is not None
                else None
            )
            reservation = await self.db.reserve_rollover(
                source_room_id,
                request,
                release.metadata() if release is not None else None,
            )
            if reservation.get("already_committed"):
                return await self._required_snapshot(reservation["successor_room_id"])
            successor_id = reservation["successor_room_id"]
            operation_id = reservation["operation_id"]
            local_thread_ids: list[str] = []
            suspicious_thread_ids: list[str] = []
            predecessor_thread_ids = {
                item["thread_id"] for item in agents if item.get("thread_id")
            }
            try:
                self._materialize_rollover_workspace(operation_id, successor_id, release)
                inherit_room_custom_capabilities(
                    self.data_root,
                    source_room_id,
                    successor_id,
                    operation_id,
                    reserved_capability_ids=frozenset(CORE_CAPABILITIES),
                )
                successor_agents = await self.db.get_agents(successor_id)
                known_ids: set[str] = set()
                for agent in successor_agents:
                    thread_id = await self.adapter.start_agent(agent, self.workspace(successor_id))
                    if thread_id in predecessor_thread_ids:
                        suspicious_thread_ids.append(thread_id)
                        raise RuntimeError("Codex returned a duplicate or predecessor thread ID")
                    if thread_id in known_ids:
                        raise RuntimeError("Codex returned a duplicate or predecessor thread ID")
                    local_thread_ids.append(thread_id)
                    await self.db.record_rollover_thread(
                        source_room_id,
                        operation_id,
                        successor_id,
                        agent["agent_key"],
                        thread_id,
                    )
                    known_ids.add(thread_id)
                await self.db.finalize_rollover(source_room_id, operation_id, successor_id)
            except BaseException as exc:
                orphaned = await self.db.abort_rollover(
                    source_room_id,
                    operation_id,
                    successor_id,
                    str(exc),
                    local_thread_ids,
                    suspicious_thread_ids,
                )
                cleanup_error = self._discard_rollover_workspace(operation_id, successor_id)
                capability_cleanup_error = discard_rollover_custom_capabilities(
                    self.data_root, operation_id, successor_id
                )
                await asyncio.gather(
                    *(self.adapter.archive_thread(thread_id) for thread_id in orphaned),
                    return_exceptions=True,
                )
                aborted = await self.db.create_event(
                    source_room_id,
                    "rollover_aborted",
                    "room",
                    "observer",
                    f"Room rollover aborted safely: {str(exc)[:500]}",
                    metadata={
                        "operation_id": operation_id,
                        "orphaned_thread_ids": orphaned,
                        "checkpoint_sha256": reservation["checkpoint_sha256"],
                        "workspace_cleanup_error": cleanup_error,
                        "custom_capability_cleanup_error": capability_cleanup_error,
                    },
                )
                self._publish_event(aborted)
                raise
            completed, inherited = await self._record_rollover_events(
                source_room_id, successor_id, operation_id, reservation["checkpoint_sha256"]
            )
            self._publish_event(completed)
            self._publish_event(inherited)
            await self.publish_state(source_room_id)
            await self.publish_state(successor_id)
            return await self._required_snapshot(successor_id)

    async def bind_institutional_release(
        self, room_id: str, request: BindInstitutionalReleaseRequest
    ) -> dict[str, Any]:
        """Bind one validated immutable release to an existing Room lineage."""
        release = resolve_institutional_release(
            self.data_root, request.institutional_release_sha256
        )
        async with self._lifecycle_locks[room_id]:
            event = await self.db.bind_institutional_release(room_id, release.metadata())
            if event is not None:
                self._publish_event(event)
            await self.publish_state(room_id)
            return await self._required_snapshot(room_id)

    async def rebind_agent_profile(self, room_id: str, agent_key: str) -> dict[str, Any]:
        """Refresh one idle adapter thread without changing its persistent identity."""
        async with self._lifecycle_locks[room_id]:
            room = await self._required_room(room_id)
            if room["status"] != RoomStatus.RUNNING or room.get("metadata", {}).get("sealed"):
                raise ValueError("Profile rebind requires an active, unsealed Room")
            agent = await self.db.get_agent(room_id, agent_key)
            if agent is None:
                raise KeyError(f"Agent {agent_key} not found")
            key = (room_id, agent_key)
            slot = self._worker_slots.get(key)
            evidence = (await self.db.get_delivery_execution(room_id)).get(agent_key, {})
            execution = evidence.get("execution") or {}
            if (
                slot is None
                or slot.phase != "idle"
                or agent["status"] != AgentStatus.IDLE
                or evidence.get("pending_count")
                or evidence.get("processing_count")
                or await self.db.has_open_transaction_assignment(
                    room_id, agent_key, room["active_round_id"]
                )
                or execution.get("state")
                in {"claimed", "active", "recovering", "result_ready", "quarantined"}
                or await self._adapter_has_active_run(agent["id"])
            ):
                raise ValueError("Profile rebind requires the selected agent to be fully idle")

            slot.quarantined = True
            slot.phase = "stopping"
            slot.reason = "Selected worker is retiring for a profile-only SDK rebind."
            slot.phase_started_at = utc_now()
            if slot.task is not None and not slot.task.done():
                slot.task.cancel()
                await asyncio.gather(slot.task, return_exceptions=True)
            instruction_sha256 = hashlib.sha256(
                agent["developer_instructions"].encode("utf-8")
            ).hexdigest()
            resume_attempted = False
            try:
                settled = (await self.db.get_delivery_execution(room_id)).get(
                    agent_key, {}
                )
                settled_execution = settled.get("execution") or {}
                if (
                    settled.get("pending_count")
                    or settled.get("processing_count")
                    or await self.db.has_open_transaction_assignment(
                        room_id, agent_key, room["active_round_id"]
                    )
                    or settled_execution.get("state")
                    in {"claimed", "active", "recovering", "result_ready", "quarantined"}
                    or await self._adapter_has_active_run(agent["id"])
                ):
                    raise ValueError(
                        "Profile rebind raced with new work; no SDK rebind was attempted"
                    )
                resume_attempted = True
                rebound_id = await self.adapter.rebind_agent_profile(
                    agent, self.workspace(room_id)
                )
                if rebound_id != agent["thread_id"]:
                    raise RuntimeError("Profile rebind changed the persistent thread ID")
            except BaseException:
                if resume_attempted:
                    self._worker_generations[key] += 1
                    quarantined = WorkerSlot(
                        generation=self._worker_generations[key],
                        task=None,
                        wakeup=asyncio.Event(),
                        phase="quarantined",
                        phase_started_at=utc_now(),
                        last_progress_at=utc_now(),
                        quarantined=True,
                        reason=(
                            "SDK profile resume failed; the selected worker remains "
                            "quarantined pending operator review."
                        ),
                    )
                    self._worker_slots[key] = quarantined
                    self._wakeups[key] = quarantined.wakeup
                    event = await self.db.create_event(
                        room_id,
                        "agent_profile_rebind",
                        "room",
                        "observer",
                        (
                            f"{agent['name']} SDK profile resume failed; durable identity "
                            "is unchanged and its worker is quarantined."
                        ),
                        status="error",
                        metadata={
                            "agent_key": agent_key,
                            "thread_id": agent["thread_id"],
                            "developer_instructions_sha256": instruction_sha256,
                            "cache_entry_evicted": True,
                            "result": "failed",
                        },
                    )
                    self._publish_event(event)
                    await self.publish_state(room_id)
                else:
                    await self.ensure_workers(room_id)
                raise
            else:
                await self.ensure_workers(room_id)

            event = await self.db.create_event(
                room_id,
                "agent_profile_rebind",
                "room",
                "observer",
                (
                    f"{agent['name']} SDK profile resume completed with its unchanged "
                    "thread ID; instruction application awaits participant verification."
                ),
                metadata={
                    "agent_key": agent_key,
                    "thread_id": rebound_id,
                    "developer_instructions_sha256": instruction_sha256,
                    "cache_entry_evicted": True,
                    "result": "completed",
                },
            )
            self._publish_event(event)
            await self.publish_state(room_id)
            return await self._required_snapshot(room_id)

    async def _recover_rollovers(self) -> None:
        """Finalize fully provisioned sagas; abort incomplete ones without replay."""
        for pending in await self.db.get_pending_rollovers():
            source_id = pending["source"]["id"]
            successor_id = pending["successor_room_id"]
            operation_id = pending["operation_id"]
            agents = await self.db.get_agents(successor_id)
            thread_ids = [agent.get("thread_id") for agent in agents]
            if (
                agents
                and all(thread_ids)
                and len(set(thread_ids)) == len(thread_ids)
                and self.workspace(successor_id).is_dir()
            ):
                try:
                    release_metadata = pending.get("institutional_release")
                    release = (
                        resolve_institutional_release(
                            self.data_root, release_metadata["manifest_sha256"]
                        )
                        if release_metadata is not None
                        else None
                    )
                    if release is not None and release.metadata() != release_metadata:
                        raise ValueError("Pending rollover release metadata changed")
                    verify_materialized_release(
                        release,
                        self.workspace(successor_id),
                        require_exact_inventory=True,
                    )
                    inherit_room_custom_capabilities(
                        self.data_root,
                        source_id,
                        successor_id,
                        operation_id,
                        reserved_capability_ids=frozenset(CORE_CAPABILITIES),
                    )
                    await self.db.finalize_rollover(source_id, operation_id, successor_id)
                    await self._record_rollover_events(
                        source_id,
                        successor_id,
                        operation_id,
                        pending["checkpoint_sha256"],
                    )
                    continue
                except (KeyError, ValueError):
                    pass
            orphaned = await self.db.abort_rollover(
                source_id,
                operation_id,
                successor_id,
                "Startup aborted an incompletely provisioned rollover",
            )
            self._discard_rollover_workspace(operation_id, successor_id)
            discard_rollover_custom_capabilities(
                self.data_root, operation_id, successor_id
            )
            await asyncio.gather(
                *(self.adapter.archive_thread(thread_id) for thread_id in orphaned),
                return_exceptions=True,
            )
        for committed in await self.db.get_committed_rollovers():
            await self._record_rollover_events(
                committed["source"]["id"],
                committed["room_id"],
                committed["operation_id"],
                committed["checkpoint_sha256"],
            )

    async def _record_rollover_events(
        self,
        source_room_id: str,
        successor_room_id: str,
        operation_id: str,
        checkpoint_hash: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        successor = await self._required_room(successor_room_id)
        institutional_release = successor.get("metadata", {}).get("institutional_release")
        completed = await self.db.create_event(
            source_room_id,
            "rollover_completed",
            "room",
            "observer",
            "Room sealed after a fresh-thread successor was created.",
            metadata={
                "operation_id": operation_id,
                "successor_room_id": successor_room_id,
                "checkpoint_sha256": checkpoint_hash,
                "institutional_release": institutional_release,
            },
            event_id=f"event_{operation_id}_source",
        )
        inherited = await self.db.create_event(
            successor_room_id,
            "rollover_checkpoint",
            "room",
            "observer",
            successor["topic"],
            metadata={
                "operation_id": operation_id,
                "predecessor_room_id": source_room_id,
                "checkpoint_sha256": checkpoint_hash,
                "stored_only": True,
                "institutional_release": institutional_release,
            },
            event_id=f"event_{operation_id}_successor",
        )
        return completed, inherited

    def _materialize_rollover_workspace(
        self,
        operation_id: str,
        successor_room_id: str,
        release: InstitutionalRelease | None,
    ) -> None:
        """Stage a complete allowlisted workspace, then expose it with one rename."""
        stage_root = self.data_root / ".rollover-staging" / operation_id
        staging_workspace = stage_root / "shared"
        successor_workspace = self.workspace(successor_room_id)
        if stage_root.exists() or successor_workspace.exists():
            raise RuntimeError("Rollover workspace staging path already exists")
        stage_root.parent.mkdir(parents=True, exist_ok=True)
        successor_workspace.parent.mkdir(parents=True, exist_ok=False)
        try:
            stage_institutional_release(
                release,
                institutional_release_root(self.data_root, release.manifest_sha256)
                if release is not None
                else self.data_root,
                staging_workspace,
            )
            verify_materialized_release(
                release, staging_workspace, require_exact_inventory=True
            )
            os.replace(staging_workspace, successor_workspace)
            stage_root.rmdir()
        except BaseException:
            self._discard_rollover_workspace(operation_id, successor_room_id)
            raise

    def _discard_rollover_workspace(
        self, operation_id: str, successor_room_id: str
    ) -> str | None:
        """Remove only paths allocated to one failed staged successor."""
        errors: list[str] = []
        for target in (
            self.data_root / ".rollover-staging" / operation_id,
            self.workspace(successor_room_id).parent,
        ):
            try:
                if target.exists():
                    shutil.rmtree(target)
            except OSError as exc:
                errors.append(f"{target.name}: {exc}")
        return "; ".join(errors) or None

    async def prepare_round(
        self, room_id: str, request: PrepareRoundRequest
    ) -> dict[str, Any]:
        async with self._lifecycle_locks[room_id]:
            room = await self._required_room(room_id)
            agents = await self.db.get_agents(room_id)
            await asyncio.gather(
                *(self.adapter.interrupt(agent["id"]) for agent in agents),
                return_exceptions=True,
            )
            await self.db.cancel_pending_deliveries(room_id, room["discussion_id"])
            await self.db.cancel_transaction_work(room_id, room["discussion_id"])
            round_item = await self.db.prepare_round(room_id, request)
            await self._record_round_preparation(room_id, round_item)
            await self.publish_state(room_id)
            return await self._required_snapshot(room_id)

    async def add_agent(self, room_id: str, request: AddAgentRequest) -> dict[str, Any]:
        """Add a genuinely new participant without replaying any pre-join context."""
        async with self._lifecycle_locks[room_id]:
            await self._required_room(room_id)
            agent = await self.db.reserve_agent_c(room_id)
            thread_id: str | None = None
            try:
                thread_id = await self.adapter.start_agent(agent, self.workspace(room_id))
                other_ids = {
                    item["thread_id"]
                    for item in await self.db.get_agents(room_id)
                    if item["agent_key"] != request.agent_key and item.get("thread_id")
                }
                if thread_id in other_ids:
                    raise RuntimeError("Codex returned a duplicate thread ID")
                await self.db.set_agent_thread(agent["id"], thread_id)
            except BaseException:
                await self.db.remove_agent(room_id, request.agent_key)
                if thread_id:
                    await self.adapter.archive_thread(thread_id)
                raise
            joined = await self.db.create_event(
                room_id,
                "agent_added",
                "room",
                "observer",
                "Agent C joined with a fresh persistent thread and no prior Room delivery.",
                metadata={"agent_key": request.agent_key, "thread_id": thread_id},
            )
            self._publish_event(joined)
            await self.ensure_workers(room_id)
            await self.publish_state(room_id)
            return await self._required_snapshot(room_id)

    async def start_round(self, room_id: str, round_id: str) -> dict[str, Any]:
        async with self._lifecycle_locks[room_id]:
            room = await self._required_room(room_id)
            if room["status"] != RoomStatus.PREPARING:
                raise ValueError(f"Cannot start a round while room is {room['status']}")
            await self._activate_round(room_id, round_id)
            return await self._required_snapshot(room_id)

    async def _record_round_preparation(
        self, room_id: str, round_item: dict[str, Any]
    ) -> None:
        prepared = await self.db.create_event(
            room_id,
            "round_prepared",
            "observer",
            "room",
            round_item["title"] or "Prepared round",
            metadata={
                "starting_agent": round_item["starting_agent"],
                "private_participants": sorted(round_item.get("participant_private", {})),
                "has_task_overlay": bool(round_item.get("task_overlay")),
                "required_contributors": round_item.get("required_contributors", []),
                "work_model_version": round_item.get("work_model_version", 1),
                "provider_context_mode": round_item.get(
                    "provider_context_mode", "persistent_agent_thread"
                ),
            },
            round_id=round_item["id"],
            discussion_id=round_item["id"],
        )
        self._publish_event(prepared)
        context = await self.db.create_event(
            room_id,
            "round_context_stored",
            "observer",
            "all",
            round_item["prompt"],
            metadata={"stored_only": True, "does_not_run_agent": True},
            round_id=round_item["id"],
            discussion_id=round_item["id"],
        )
        self._publish_event(context)
        for agent_key, private in round_item.get("participant_private", {}).items():
            if private:
                event = await self.db.create_event(
                    room_id,
                    "private_initialization",
                    "observer",
                    agent_key,
                    private,
                    metadata={
                        "private": True,
                        "stored_only": True,
                        "does_not_run_agent": True,
                    },
                    round_id=round_item["id"],
                    discussion_id=round_item["id"],
                )
                self._publish_event(event)

    async def _activate_round(self, room_id: str, round_id: str) -> None:
        round_item = await self.db.start_round(room_id, round_id)
        started = await self.db.create_event(
            room_id,
            "round_started",
            "room",
            "observer",
            f"Round started with {round_item['starting_agent']} designated to begin.",
            metadata={"starting_agent": round_item["starting_agent"]},
            round_id=round_id,
            discussion_id=round_id,
        )
        self._publish_event(started)
        members = [agent["agent_key"] for agent in await self.db.get_agents(room_id)]
        targets = tuple(members) if round_item["starting_agent"] == "either" else (round_item["starting_agent"],)
        if any(target not in members for target in targets):
            raise ValueError("Round starting agent is not a Room participant")
        activation = await self.db.create_event(
            room_id,
            "round_start_turn",
            "room",
            round_item["starting_agent"],
            "Begin the prepared round now.",
            metadata={
                "starting_agent": round_item["starting_agent"],
                "work_model_version": round_item.get("work_model_version", 1),
                "provider_context_mode": round_item.get(
                    "provider_context_mode", "persistent_agent_thread"
                ),
            },
            deliver_to=(
                ()
                if round_item.get("work_model_version", 1) == 2
                else targets
            ),
            runnable_to=(
                ()
                if round_item.get("work_model_version", 1) == 2
                else None
            ),
            round_id=round_id,
            discussion_id=round_id,
        )
        self._publish_event(activation)
        if round_item.get("work_model_version", 1) == 2:
            transaction = await self.db.create_transaction_task(
                room_id,
                round_id,
                activation["id"],
                round_item["starting_agent"],
                round_item.get("required_contributors", []),
            )
            targets = tuple(transaction["agent_keys"])
        await self.ensure_workers(room_id)
        for target in targets:
            self.wake(room_id, target)
        await self.publish_state(room_id)

    async def observer_message(
        self, room_id: str, request: ObserverMessageRequest
    ) -> dict[str, Any]:
        reopen_events: list[dict[str, Any]] = []
        async with self._lifecycle_locks[room_id]:
            room = await self._required_room(room_id)
            if room["status"] == RoomStatus.FINISHED:
                await self.db.reopen_finished_room(room_id)
                await self._system_event(
                    room_id,
                    "discussion_reopened",
                    "Discussion reopened by a new observer message; agent thread identities were retained.",
                )
            elif room["status"] not in {RoomStatus.RUNNING, RoomStatus.PAUSED}:
                raise ValueError(f"Cannot send messages while room is {room['status']}")
            members = [agent["agent_key"] for agent in await self.db.get_agents(room_id)]
            target = "all" if request.target in {"all", "both"} else request.target
            targets = tuple(members) if target == "all" else (target,)
            if any(item not in members for item in targets):
                raise ValueError(f"Target {request.target} is not a Room participant")
            round_item = await self.db.get_round(room["active_round_id"])
            transactional = bool(
                round_item and round_item.get("work_model_version", 1) == 2
            )
            event = await self.db.create_event(
                room_id,
                "observer_message",
                "observer",
                target,
                request.content,
                metadata={
                    "private": target != "all",
                    "work_model_version": 2 if transactional else 1,
                },
                deliver_to=() if transactional else targets,
                runnable_to=() if transactional else None,
            )
            if transactional:
                transaction = await self.db.create_observer_transaction_work(
                    room_id,
                    room["active_round_id"],
                    event["id"],
                    targets,
                    request.content,
                )
                targets = tuple(transaction["agent_keys"])
            else:
                for target in targets:
                    if await self.db.reopen_ready_agent(room_id, target):
                        reopened = await self.db.create_event(
                            room_id,
                            "agent_reopened",
                            "room",
                            "observer",
                            f"{target.replace('_', ' ').title()} received new substantive observer input after FINISH and may respond.",
                            related_event_id=event["id"],
                            metadata={"reopened_agent": target, "message_source": "observer"},
                        )
                        reopen_events.append(reopened)
        self._publish_event(event)
        for reopened in reopen_events:
            self._publish_event(reopened)
        await self.ensure_workers(room_id)
        for target in targets:
            self.wake(room_id, target)
        return event

    async def pause(self, room_id: str) -> None:
        room = await self._required_room(room_id)
        if room["status"] != RoomStatus.RUNNING:
            raise ValueError(f"Room is {room['status']}, not running")
        await self.db.set_room_status(room_id, RoomStatus.PAUSED)
        await self._system_event(
            room_id, "room_paused", "Room paused. Active turns may finish; queued turns will wait."
        )
        await self.publish_state(room_id)

    async def resume(self, room_id: str) -> None:
        closed_without_work = False
        async with self._lifecycle_locks[room_id]:
            room = await self._required_room(room_id)
            if room["status"] not in {RoomStatus.PAUSED, RoomStatus.STOPPED, RoomStatus.FINISHED}:
                raise ValueError(f"Room cannot resume from {room['status']}")
            blocking: list[str] = []
            agents_by_key = {
                agent["agent_key"]: agent for agent in await self.db.get_agents(room_id)
            }
            for key, slot in self._worker_slots.items():
                if key[0] != room_id or not slot.quarantined:
                    continue
                agent = agents_by_key.get(key[1])
                active = bool(agent and await self._adapter_has_active_run(agent["id"]))
                task_alive = slot.task is not None and not slot.task.done()
                if task_alive or active:
                    blocking.append(key[1])
                else:
                    slot.quarantined = False
            if blocking:
                raise ValueError(
                    "Cannot resume while prior worker execution is still retiring: "
                    + ", ".join(sorted(blocking))
                )
            if room["status"] == RoomStatus.FINISHED:
                await self.db.reopen_finished_room(room_id)
            else:
                await self.db.set_room_status(room_id, RoomStatus.RUNNING)
                await self.db.resume_active_round(room_id)
            await self._system_event(room_id, "room_resumed", "Room resumed.")
            round_item = await self.db.get_round(room["active_round_id"])
            transactional = bool(
                round_item and round_item.get("work_model_version", 1) == 2
            )
            if transactional:
                if not await self.db.has_active_transaction_task(
                    room_id, room["active_round_id"]
                ):
                    await self._close_discussion(
                        room_id,
                        room["active_round_id"],
                        "resume_without_work",
                        "Round closed immediately after Resume because no active "
                        "transaction task remained. Send a new observer message to "
                        "continue with fresh work.",
                    )
                    closed_without_work = True
            else:
                closed_without_work = await self._reconcile_quiescent_room(
                    room_id,
                    room["active_round_id"],
                    fallback_reason="resume_without_work",
                    fallback_content=(
                        "Round closed immediately after Resume because Stop left no runnable "
                        "deliveries. Send a new observer message to continue with fresh work."
                    ),
                )
        if closed_without_work:
            await self.publish_state(room_id)
            return
        await self.ensure_workers(room_id)
        for agent in await self.db.get_agents(room_id):
            self.wake(room_id, agent["agent_key"])
        await self.publish_state(room_id)

    async def stop(self, room_id: str, reason: str = "Stopped by observer") -> None:
        # First make every result from the old generation unroutable. Then let an
        # interrupted SDK turn retire without holding the lifecycle lock it needs
        # to record a stale result. A still-live turn is quarantined, never replaced.
        async with self._lifecycle_locks[room_id]:
            room = await self._required_room(room_id)
            if room["status"] in {RoomStatus.CREATING, RoomStatus.ROLLING_OVER}:
                raise ValueError("Room is frozen while creation or rollover is pending")
            if room["status"] == RoomStatus.ARCHIVED:
                return
            await self.db.invalidate_inflight(room_id)
            await self.db.set_room_status(room_id, RoomStatus.STOPPED)
            agents = await self.db.get_agents(room_id)
        interruption_results = await asyncio.gather(
            *(self.adapter.interrupt(agent["id"]) for agent in agents),
            return_exceptions=True,
        )
        interruption_outcomes = {
            agent["agent_key"]: (
                result if isinstance(result, InterruptOutcome) else InterruptOutcome.UNKNOWN
            )
            for agent, result in zip(agents, interruption_results, strict=True)
        }
        await self._retire_room_workers(room_id, interruption_outcomes)
        async with self._lifecycle_locks[room_id]:
            await self.db.cancel_pending_deliveries(room_id, room["discussion_id"])
            await self.db.cancel_transaction_work(room_id, room["discussion_id"])
            await self.db.stop_active_round(room_id, reason)
            for agent in agents:
                slot = self._worker_slots.get((room_id, agent["agent_key"]))
                retired = (
                    slot is None
                    or slot.task is None
                    or (slot.task.done() and not slot.quarantined)
                )
                if agent["status"] != AgentStatus.FINISHED and retired:
                    await self.db.set_agent_status(agent["id"], AgentStatus.IDLE)
            await self._system_event(room_id, "room_stopped", reason)
            await self.publish_state(room_id)

    async def new_topic(self, room_id: str, request: NewTopicRequest) -> dict[str, Any]:
        prepared = await self.prepare_round(
            room_id,
            PrepareRoundRequest(title="New topic", prompt=request.topic),
        )
        round_id = prepared["active_round_id"]
        return await self.start_round(room_id, round_id)

    async def update_room(self, room_id: str, request: UpdateRoomRequest) -> None:
        room = await self._required_room(room_id)
        if room["status"] in {
            RoomStatus.CREATING,
            RoomStatus.ROLLING_OVER,
            RoomStatus.ARCHIVED,
        }:
            raise ValueError(f"Cannot update a room while it is {room['status']}")
        await self.db.update_room(room_id, request.model_dump(exclude_none=True))
        await self.publish_state(room_id)

    async def archive(self, room_id: str) -> None:
        await self.stop(room_id, "Room archived by observer.")
        agents = await self.db.get_agents(room_id)
        await asyncio.gather(
            *(
                self.adapter.archive_thread(agent["thread_id"])
                for agent in agents
                if agent.get("thread_id")
            ),
            return_exceptions=True,
        )
        await self.db.set_room_status(room_id, RoomStatus.ARCHIVED)
        await self.publish_state(room_id)

    async def unarchive(self, room_id: str) -> None:
        room = await self._required_room(room_id)
        if room["status"] != RoomStatus.ARCHIVED:
            raise ValueError("Room is not archived")
        if room.get("metadata", {}).get("sealed"):
            raise ValueError("A rollover predecessor is sealed and cannot be unarchived")
        agents = await self.db.get_agents(room_id)
        failures = await asyncio.gather(
            *(
                self.adapter.unarchive_thread(agent["thread_id"])
                for agent in agents
                if agent.get("thread_id")
            ),
            return_exceptions=True,
        )
        errors = [str(item) for item in failures if isinstance(item, BaseException)]
        if errors:
            raise RuntimeError("Could not unarchive Codex threads: " + "; ".join(errors))
        await self.db.set_room_status(room_id, RoomStatus.STOPPED)
        await self._system_event(room_id, "room_unarchived", "Room restored from archive.")
        await self.publish_state(room_id)

    async def reset(self, room_id: str) -> dict[str, Any]:
        """Deliberately replace all participant identities, retaining an audit event."""
        await self.stop(room_id, "Room reset requested; replacing all participant threads.")
        async with self._lifecycle_locks[room_id]:
            room = await self._required_room(room_id)
            if room["status"] == RoomStatus.ARCHIVED:
                raise ValueError("Unarchive the room before resetting it")
            agents = await self.db.get_agents(room_id)
            old_ids = [agent["thread_id"] for agent in agents if agent.get("thread_id")]
            await asyncio.gather(
                *(self.adapter.archive_thread(thread_id) for thread_id in old_ids),
                return_exceptions=True,
            )
            await self.db.reset_room_threads(room_id)
            agents = await self.db.get_agents(room_id)
            starts = await asyncio.gather(
                *(self.adapter.start_agent(agent, self.workspace(room_id)) for agent in agents),
                return_exceptions=True,
            )
            if any(isinstance(item, BaseException) for item in starts):
                await self.db.set_room_status(room_id, RoomStatus.ERROR)
                raise RuntimeError("Reset failed while creating replacement Codex threads")
            new_ids = {
                agent["agent_key"]: str(thread_id)
                for agent, thread_id in zip(agents, starts, strict=True)
            }
            if len(set(new_ids.values())) != len(agents):
                await self.db.set_room_status(room_id, RoomStatus.ERROR)
                raise RuntimeError("Reset returned duplicate Codex thread IDs")
            await self.db.replace_agent_threads(room_id, new_ids)
            _, discussion_id = await self.db.begin_new_topic(room_id, room["topic"])
            reset_event = await self.db.create_event(
                room_id,
                "room_reset",
                "room",
                "observer",
                "Agent identities were deliberately reset.",
                metadata={"old_thread_ids": old_ids, "new_thread_ids": new_ids},
                discussion_id=discussion_id,
            )
            topic_event = await self.db.create_event(
                room_id,
                "topic",
                "observer",
                "all",
                room["topic"],
                metadata={"after_reset": True, "independent_delivery": True},
                deliver_to=tuple(agent["agent_key"] for agent in agents),
                discussion_id=discussion_id,
            )
            self._publish_event(reset_event)
            self._publish_event(topic_event)
            await self.ensure_workers(room_id)
            for agent in agents:
                self.wake(room_id, agent["agent_key"])
            return await self._required_snapshot(room_id)

    async def ensure_workers(self, room_id: str) -> None:
        room = await self._required_room(room_id)
        if room["status"] != RoomStatus.RUNNING:
            return
        durable = await self.db.get_delivery_execution(room_id)
        for agent in await self.db.get_agents(room_id):
            agent_key = agent["agent_key"]
            key = (room_id, agent_key)
            slot = self._worker_slots.get(key)
            if slot and slot.task is not None and not slot.task.done():
                continue
            active_handle = await self._adapter_has_active_run(agent["id"])
            evidence = durable.get(agent_key, {})
            durable_execution = evidence.get("execution") or {}
            if durable_execution.get("state") == "quarantined":
                if slot is None:
                    slot = WorkerSlot(
                        generation=self._worker_generations[key],
                        task=None,
                        wakeup=asyncio.Event(),
                    )
                    self._worker_slots[key] = slot
                slot.quarantined = True
                slot.phase = "quarantined"
                slot.batch_id = durable_execution.get("batch_id")
                slot.reason = durable_execution.get("error") or (
                    "Exact Codex turn state is unknown; replacement is blocked."
                )
                continue
            if active_handle:
                # A detached SDK handle is proof that replacement could overlap the
                # same persistent thread. Quarantine it until the handle disappears.
                if slot is None:
                    slot = WorkerSlot(
                        generation=self._worker_generations[key],
                        task=None,
                        wakeup=asyncio.Event(),
                    )
                    self._worker_slots[key] = slot
                slot.quarantined = True
                slot.phase = "stopping"
                slot.phase_started_at = slot.phase_started_at or utc_now()
                slot.reason = (
                    "An active SDK handle has no live worker task; replacement is "
                    "quarantined to prevent overlapping persistent-thread turns."
                )
                continue
            if (
                agent["status"] == AgentStatus.RUNNING
                and not evidence.get("processing_count")
                and not active_handle
            ):
                await self.db.set_agent_status(agent["id"], AgentStatus.IDLE)
            self._worker_generations[key] += 1
            generation = self._worker_generations[key]
            wakeup = asyncio.Event()
            slot = WorkerSlot(
                generation=generation,
                task=None,
                wakeup=wakeup,
                phase_started_at=utc_now(),
                last_progress_at=utc_now(),
            )
            self._worker_slots[key] = slot
            self._wakeups[key] = wakeup
            task = asyncio.create_task(
                    self._worker_loop(room_id, agent_key, generation),
                    name=f"worker:{room_id}:{agent_key}",
            )
            slot.task = task
            self._workers[key] = task
            task.add_done_callback(
                lambda completed, *, worker_key=key, worker_generation=generation: (
                    self._worker_task_finished(worker_key, worker_generation, completed)
                )
            )

    def wake(self, room_id: str, agent_key: str) -> None:
        wakeup = self._wakeups.get((room_id, agent_key))
        if wakeup is not None:
            wakeup.set()

    async def publish_state(self, room_id: str) -> None:
        room = await self.db.get_room(room_id)
        if room is None:
            return
        room["agents"] = await self.db.get_agents(room_id)
        await self._attach_execution(room)
        self.hub.publish(room_id, {"kind": "state", "room": room})

    async def snapshot(self, room_id: str) -> dict[str, Any] | None:
        room = await self.db.snapshot(room_id)
        if room is not None:
            await self._attach_execution(room)
        return room

    def workspace(self, room_id: str) -> Path:
        return self.data_root / "rooms" / room_id / "shared"

    async def _worker_loop(self, room_id: str, agent_key: str, generation: int) -> None:
        key = (room_id, agent_key)
        slot = self._worker_slots[key]
        wakeup = slot.wakeup
        while not self._shutdown.is_set() and self._slot_is_current(key, generation):
            try:
                # Clear before checking SQLite so an event arriving between the
                # query and the wait leaves the wake flag set. Clearing after an
                # empty claim would lose that notification and delay a valid turn.
                wakeup.clear()
                room = await self.db.get_room(room_id)
                round_item = (
                    await self.db.get_round(room["active_round_id"])
                    if room and room.get("active_round_id")
                    else None
                )
                transactional = bool(
                    round_item and round_item.get("work_model_version", 1) == 2
                )
                delivery = (
                    await self.db.claim_next_assignment(
                        room_id,
                        agent_key,
                        generation,
                        model=ROOM_MODEL,
                        reasoning_effort=ROOM_REASONING_EFFORT,
                    )
                    if transactional
                    else await self.db.claim_next_delivery(
                        room_id,
                        agent_key,
                        generation,
                        model=ROOM_MODEL,
                        reasoning_effort=ROOM_REASONING_EFFORT,
                    )
                )
                if delivery is None:
                    self._set_worker_phase(key, generation, "idle", None, "Worker is waiting for work.")
                    if self._shutdown.is_set():
                        break
                    try:
                        await asyncio.wait_for(wakeup.wait(), timeout=5)
                    except TimeoutError:
                        pass
                    continue
                self._set_worker_phase(
                    key,
                    generation,
                    "recovering" if delivery.get("recovered") else "invoking",
                    delivery["batch_id"],
                    (
                        "The Room is reconciling the exact persisted Codex turn."
                        if delivery.get("recovered")
                        else "The transaction assignment is running under exact-turn reconciliation."
                        if transactional
                        else
                        f"Retry attempt {max(item['attempts'] for item in delivery['events']) + 1} "
                        "is running under exact-turn reconciliation."
                        if max(item["attempts"] for item in delivery["events"]) + 1 > 1
                        else "The persistent agent turn is running under exact-turn reconciliation."
                    ),
                )
                if transactional:
                    await self._process_assignment(delivery, generation)
                else:
                    await self._process_delivery(delivery, generation)
                self._set_worker_phase(key, generation, "idle", None, "Worker completed its batch.")
                # Decision routing publishes while the worker is still settling.
                # Publish the terminal transition as well so connected clients do
                # not retain a stale execution phase until unrelated activity.
                await self.publish_state(room_id)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                await self._system_event(
                    room_id,
                    "worker_error",
                    f"{agent_key} worker recovered from an error: {exc}",
                    status="error",
                )
                await asyncio.sleep(1)

    def _worker_task_finished(
        self,
        key: tuple[str, str],
        generation: int,
        task: asyncio.Task[None],
    ) -> None:
        """Publish the post-task state, after ``task.done()`` becomes observable."""
        slot = self._worker_slots.get(key)
        if (
            slot is None
            or slot.generation != generation
            or slot.task is not task
            or not slot.quarantined
        ):
            return
        try:
            publication = asyncio.get_running_loop().create_task(
                self._publish_worker_retirement(key, generation, task)
            )
            self._background_tasks.add(publication)
            publication.add_done_callback(self._background_tasks.discard)
        except RuntimeError:
            # The event loop is already closing; there can be no connected observer.
            return

    async def _publish_worker_retirement(
        self,
        key: tuple[str, str],
        generation: int,
        task: asyncio.Task[None],
    ) -> None:
        slot = self._worker_slots.get(key)
        if slot is None or slot.generation != generation or slot.task is not task:
            return
        if slot.quarantined:
            agent = await self.db.get_agent(key[0], key[1])
            active = bool(agent and await self._adapter_has_active_run(agent["id"]))
            durable = await self.db.get_delivery_execution(key[0])
            durable_execution = (durable.get(key[1], {}).get("execution") or {})
            slot.phase_started_at = utc_now()
            slot.last_progress_at = slot.phase_started_at
            if durable_execution.get("state") == "quarantined":
                slot.phase = "quarantined"
                slot.reason = durable_execution.get("error") or (
                    "Exact Codex turn state is unknown; replacement is blocked."
                )
            elif active:
                slot.phase = "stopping"
                slot.reason = (
                    "The worker retired, but SDK interruption remains unconfirmed; "
                    "replacement is quarantined to prevent an overlapping turn."
                )
            else:
                slot.quarantined = False
                slot.phase = "stopped"
                slot.batch_id = None
                slot.reason = "Worker generation finished retiring after Stop."
        await self.publish_state(key[0])

    async def _retire_room_workers(
        self,
        room_id: str,
        interruption_outcomes: dict[str, InterruptOutcome] | None = None,
    ) -> None:
        slots = [
            (agent_key, slot)
            for (candidate, agent_key), slot in self._worker_slots.items()
            if candidate == room_id and slot.task is not None and not slot.task.done()
        ]
        for agent_key, slot in slots:
            active_phase = slot.phase
            slot.quarantined = True
            slot.phase = "stopping"
            slot.reason = "Stop requested; waiting for the current worker generation to retire."
            slot.phase_started_at = utc_now()
            outcome = (interruption_outcomes or {}).get(agent_key, InterruptOutcome.UNKNOWN)
            if (
                active_phase not in {"invoking", "settling"}
                or outcome in {InterruptOutcome.INTERRUPTED, InterruptOutcome.ALREADY_INACTIVE}
            ):
                slot.task.cancel()
        if not slots:
            return
        _, pending = await asyncio.wait(
            [slot.task for _, slot in slots if slot.task is not None],
            timeout=self.STOP_RETIRE_TIMEOUT_SECONDS,
        )
        for agent_key, slot in slots:
            if slot.task is not None and slot.task.done():
                agent = await self.db.get_agent(room_id, agent_key)
                active = bool(agent and await self._adapter_has_active_run(agent["id"]))
                if active:
                    slot.phase = "stopping"
                    slot.reason = (
                        "The worker retired, but SDK interruption remains unconfirmed; "
                        "replacement is quarantined to prevent an overlapping turn."
                    )
                else:
                    slot.quarantined = False
                    slot.phase = "stopped"
                    slot.reason = "Worker generation retired after Stop."
                slot.last_progress_at = utc_now()
            elif slot.task in pending:
                slot.reason = (
                    "Worker retirement is unconfirmed; Resume is blocked to prevent "
                    "overlapping turns on the persistent thread."
                )

    def _slot_is_current(self, key: tuple[str, str], generation: int) -> bool:
        slot = self._worker_slots.get(key)
        return slot is not None and slot.generation == generation and not slot.quarantined

    def _set_worker_phase(
        self,
        key: tuple[str, str],
        generation: int,
        phase: str,
        batch_id: str | None,
        reason: str,
    ) -> None:
        slot = self._worker_slots.get(key)
        if slot is None or slot.generation != generation or slot.quarantined:
            return
        now = utc_now()
        slot.phase = phase
        slot.batch_id = batch_id
        slot.phase_started_at = now
        slot.last_progress_at = now
        slot.reason = reason

    async def _adapter_has_active_run(self, agent_id: str) -> bool:
        checker = getattr(self.adapter, "has_active_run", None)
        if checker is None:
            return False
        try:
            return bool(await checker(agent_id))
        except Exception:
            return False

    async def _await_with_inactivity_lease(
        self,
        awaitable: Any,
        key: tuple[str, str],
        generation: int,
    ) -> AgentRunResult:
        """Expire only after no verified exact-turn progress, not total runtime."""
        task = asyncio.create_task(awaitable)
        try:
            while True:
                slot = self._worker_slots.get(key)
                if slot is None or slot.generation != generation:
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
                    raise asyncio.CancelledError
                try:
                    last_progress = datetime.fromisoformat(
                        slot.last_progress_at or slot.phase_started_at or utc_now()
                    )
                except ValueError:
                    last_progress = datetime.now(UTC)
                inactive_for = (datetime.now(UTC) - last_progress).total_seconds()
                remaining = self.AGENT_TURN_TIMEOUT_SECONDS - inactive_for
                if remaining <= 0:
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
                    raise TimeoutError
                done, _ = await asyncio.wait({task}, timeout=min(remaining, 5.0))
                if task in done:
                    return task.result()
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

    async def _record_verified_progress(
        self, key: tuple[str, str], generation: int, batch_id: str
    ) -> None:
        slot = self._worker_slots.get(key)
        if slot is None or slot.generation != generation or slot.quarantined:
            return
        slot.last_progress_at = utc_now()
        slot.reason = "Authoritative exact-turn history showed new progress."
        await self.db.touch_execution_progress(batch_id)

    async def _attach_execution(self, room: dict[str, Any]) -> None:
        room_id = room["id"]
        durable = await self.db.get_delivery_execution(room_id)
        now = datetime.now(UTC)
        for agent in room.get("agents", []):
            key = (room_id, agent["agent_key"])
            slot = self._worker_slots.get(key)
            evidence = durable.get(agent["agent_key"], {})
            durable_execution = evidence.get("execution") or {}
            last_execution = evidence.get("last_execution") or {}
            displayed_execution = (
                durable_execution if durable_execution.get("model") else last_execution
            )
            model_recency = (
                "current"
                if durable_execution.get("model")
                else ("last" if last_execution.get("model") else None)
            )
            alive = bool(slot and slot.task is not None and not slot.task.done())
            active = await self._adapter_has_active_run(agent["id"])
            pending = int(evidence.get("pending_count", 0))
            processing = int(evidence.get("processing_count", 0))
            usage_continuation = evidence.get("usage_continuation") or {}
            phase = slot.phase if slot and alive else ("queued" if pending else "idle")
            reason = slot.reason if slot else "No live worker is registered in this process."
            health = "healthy"
            if durable_execution.get("state") == "quarantined":
                phase = "quarantined"
                health = "state_unknown"
                reason = durable_execution.get("error") or (
                    "Exact Codex turn state is unknown; replacement is blocked."
                )
            elif durable_execution.get("state") == "usage_suspended":
                phase = "usage_suspended"
                health = "waiting"
                reason = (
                    "Usage limit reached; continuation is scheduled for "
                    f"{usage_continuation.get('wake_at', 'the reported reset time')}."
                )
            elif slot and slot.quarantined and alive:
                phase = "stopping"
                health = "progress_unobservable"
                reason = slot.reason
            elif processing and not alive and not active:
                phase = "stalled"
                health = "invariant_mismatch"
                reason = "Durable processing work has no matching live worker or active SDK handle."
            elif active and not alive:
                phase = "stopping"
                health = "invariant_mismatch"
                reason = "An active SDK handle has no matching live worker task; replacement is quarantined."
            elif agent["status"] == AgentStatus.RUNNING and not processing and not active:
                health = "invariant_mismatch"
                reason = "Agent is marked running without a processing batch or active SDK handle."
            elif phase == "invoking" and slot and slot.phase_started_at:
                try:
                    started = datetime.fromisoformat(slot.phase_started_at)
                    if (now - started).total_seconds() >= self.LONG_RUNNING_SECONDS:
                        health = "progress_unobservable"
                        reason = "Invocation is long-running; exact-turn progress is being reconciled."
                except ValueError:
                    pass
            elif pending and not alive:
                health = "invariant_mismatch"
                reason = "Queued work has no live current-generation worker."
            agent["execution"] = {
                "phase": phase,
                "health": health,
                "reason": reason,
                "batch_id": (slot.batch_id if slot else None) or evidence.get("batch_id"),
                "phase_started_at": slot.phase_started_at if slot else evidence.get("started_at"),
                "last_progress_at": slot.last_progress_at if slot else None,
                "pending_count": pending,
                "processing_count": processing,
                "worker_generation": slot.generation if slot else None,
                "worker_alive": alive,
                "active_handle": active,
                "durable_execution_state": durable_execution.get("state"),
                "sdk_thread_id": durable_execution.get("sdk_thread_id"),
                "sdk_turn_id": durable_execution.get("sdk_turn_id"),
                "completion_source": durable_execution.get("completion_source"),
                "model": displayed_execution.get("model"),
                "reasoning_effort": displayed_execution.get("reasoning_effort"),
                "model_recency": model_recency,
                "usage_continuation": usage_continuation or None,
            }

    async def _recover_transaction_evidence(self) -> None:
        for item in await self.db.list_pending_transaction_evidence():
            await self._execute_transaction_evidence(
                item["room_id"],
                item["round_id"],
                item["assignment_id"],
                item["id"],
                item["request"],
                related_event_id=None,
                recovery=True,
            )

    async def _execute_transaction_evidence(
        self,
        room_id: str,
        round_id: str,
        assignment_id: str,
        evidence_id: str,
        raw_requests: list[dict[str, Any]],
        *,
        related_event_id: str | None,
        recovery: bool = False,
    ) -> None:
        requests = [SourceEvidenceRequest.model_validate(item) for item in raw_requests]
        execution = await asyncio.to_thread(
            execute_source_evidence,
            self.workspace(room_id),
            requests,
        )
        completed = await self.db.complete_transaction_evidence(
            evidence_id,
            execution.plan,
            execution.durable_result,
            execution.result,
        )
        if completed["completed"]:
            event = await self.db.create_event(
                room_id,
                "tool_activity",
                "room",
                "observer",
                (
                    "CORE executed structured source evidence"
                    + (" during restart recovery." if recovery else ".")
                ),
                related_event_id=related_event_id,
                status="recorded" if execution.result.get("ok") else "error",
                metadata={
                    "type": "deterministic_source_evidence",
                    "status": "completed" if execution.result.get("ok") else "error",
                    "assignment_id": assignment_id,
                    "evidence_id": evidence_id,
                    "plan_operation": execution.plan.get("operation"),
                    "result": execution.durable_result,
                    "work_model_version": 2,
                },
                discussion_id=round_id,
                round_id=round_id,
            )
            self._publish_event(event)
        if completed.get("wake_agent"):
            await self.ensure_workers(room_id)
            self.wake(room_id, completed["agent_key"])

    async def _assignment_prompt(
        self, batch: dict[str, Any], agent: dict[str, Any]
    ) -> str:
        round_item = await self.db.get_round(batch["round_id"])
        if round_item is None:
            raise RuntimeError(f"Round {batch['round_id']} is missing")
        assignment = batch["assignment"]
        dependencies = await self.db.get_assignment_dependency_results(
            assignment["id"]
        )
        siblings = await self.db.get_assignment_sibling_context(
            assignment["id"]
        )
        evidence_results = await self.db.get_assignment_evidence_results(
            assignment["id"]
        )
        raw_context_event_ids = assignment.get("context_event_ids_json") or "[]"
        context_event_ids = (
            json.loads(raw_context_event_ids)
            if isinstance(raw_context_event_ids, str)
            else list(raw_context_event_ids)
        )
        history_events = await self.db.get_events_by_ids(
            batch["room_id"], context_event_ids
        )
        history_resume = False
        if assignment.get("result_event_id"):
            prior_result = await self.db.get_event(assignment["result_event_id"])
            history_resume = bool(
                prior_result
                and prior_result.get("metadata", {}).get("transaction_action") == "HISTORY"
            )
        context_parts = [
            "<transaction_assignment>",
            f"Room ID: {batch['room_id']}",
            f"Round ID: {batch['round_id']}",
            f"Task ID: {batch['task_id']}",
            f"Assignment ID: {assignment['id']}",
            f"Round objective:\n{round_item['prompt']}",
            f"Current assignment:\n{assignment['instruction']}",
        ]
        retry_feedback = batch.get("retry_feedback")
        if retry_feedback:
            context_parts.extend(
                [
                    "<retry_feedback>",
                    (
                        "CORE rejected the immediately preceding execution of this same "
                        "Assignment. Correct the reported validation/runtime issue rather than "
                        "repeating the invalid structured decision. Failure detail:\n"
                        + str(retry_feedback)
                    ),
                    "</retry_feedback>",
                ]
            )
        private = round_item.get("participant_private", {}).get(agent["agent_key"])
        if private:
            context_parts.append(f"Private initialization for you:\n{private}")
        overlay = round_item.get("participant_overlays", {}).get(agent["agent_key"])
        if overlay:
            context_parts.append(f"Temporary overlay for you:\n{overlay}")
        if round_item.get("task_overlay"):
            context_parts.append(f"Round task overlay:\n{round_item['task_overlay']}")
        if siblings:
            context_parts.append("<declared_sibling_assignments>")
            for item in siblings:
                context_parts.extend(
                    [
                        (
                            f"<sibling assignment_id=\"{item['assignment_id']}\" "
                            f"agent=\"{item['agent_key']}\" state=\"{item['state']}\">"
                        ),
                        item["instruction"],
                        "</sibling>",
                    ]
                )
            context_parts.append("</declared_sibling_assignments>")
            context_parts.append(
                "These sibling assignments are already declared work under your current "
                "dependency join. Use them as bounded coordination awareness. Avoid "
                "delegating substantially duplicate work unless a specific dependency "
                "makes another peer turn materially necessary; sibling results remain "
                "independent until the join resolves."
            )
        if dependencies:
            context_parts.append("<resolved_dependencies>")
            for item in dependencies:
                context_parts.extend(
                    [
                        (
                            f"<dependency join_id=\"{item['join_id']}\" "
                            f"assignment_id=\"{item['assignment_id']}\" "
                            f"agent=\"{item['agent_key']}\" "
                            f"state=\"{item['state']}\">"
                        ),
                        item.get("result_content")
                        or item.get("resolution_reason")
                        or "(no substantive result text)",
                        "</dependency>",
                    ]
                )
            context_parts.append("</resolved_dependencies>")
        if history_events or history_resume:
            context_parts.append("<retrieved_room_history>")
            if history_events:
                remaining_chars = self.TRANSACTION_HISTORY_CONTEXT_MAX_CHARS
                for event in history_events:
                    if remaining_chars <= 0:
                        context_parts.append(
                            "[Additional selected Room-history results omitted by CORE context bound.]"
                        )
                        break
                    raw_content = event.get("content") or ""
                    content = raw_content[:remaining_chars]
                    remaining_chars -= len(content)
                    context_parts.extend(
                        [
                            (
                                f"<history_result event_id=\"{event['id']}\" "
                                f"round_id=\"{event.get('round_id') or ''}\" "
                                f"agent=\"{event.get('source') or ''}\">"
                            ),
                            content,
                            "</history_result>",
                        ]
                    )
                    if len(content) < len(raw_content):
                        context_parts.append(
                            "[This selected historical result was truncated by CORE context bound.]"
                        )
                        remaining_chars = 0
            else:
                context_parts.append(
                    "CORE found no matching prior completed Assignment results for the "
                    "most recent HISTORY request."
                )
            context_parts.append("</retrieved_room_history>")
            context_parts.append(
                "The Room history above is bounded historical context, not current work state. "
                "Use it only for the dependency that justified retrieval; the current Assignment "
                "and durable Task/Join/Evidence state remain authoritative."
            )
        if evidence_results:
            context_parts.append("<resolved_source_evidence>")
            for item in evidence_results:
                context_parts.extend(
                    [
                        (
                            f"<evidence evidence_id=\"{item['id']}\">"
                        ),
                        json.dumps(item["result"], ensure_ascii=False, indent=2),
                        "</evidence>",
                    ]
                )
            context_parts.append("</resolved_source_evidence>")
            context_parts.append(
                "The source evidence above was executed deterministically by CORE for this "
                "assignment. Interpret it directly; request more evidence only for a specific "
                "unresolved dependency."
            )
        provider_context_mode = round_item.get(
            "provider_context_mode", "persistent_agent_thread"
        )
        context_boundary = (
            "This provider context is bounded to the current logical Assignment. Durable Room, "
            "Task, dependency, and evidence state supplied above is authoritative continuity; "
            "do not assume unsupplied history from another Assignment or earlier Round."
            if provider_context_mode == "assignment_thread"
            else
            "Earlier persistent-thread history is background only; do not treat an older "
            "request as the current assignment."
        )
        context_parts.extend(
            [
                "</transaction_assignment>",
                (
                    "The transaction assignment above is the only current actionable Room work. "
                    + context_boundary
                ),
                self.TRANSACTION_EVIDENCE_INSTRUCTION,
                self.TRANSACTION_HISTORY_INSTRUCTION,
                self.TRANSACTION_CAPABILITY_INSTRUCTION,
                (
                    "Return the transaction structured decision only. action must be COMPLETE, "
                    "DELEGATE, EVIDENCE, HISTORY, or PASS. COMPLETE ends this assignment with a "
                    "substantive message. DELEGATE pauses this assignment and must include one or "
                    "more distinct peer delegations, each with target, bounded instruction, and "
                    "optional config. EVIDENCE pauses this same assignment and must include 1-16 "
                    "bounded READ, SEARCH, or FIND source-evidence requests. HISTORY immediately "
                    "selects bounded completed results from earlier Rounds in this Room and resumes "
                    "this same assignment with those exact events supplied as historical context. "
                    "PASS ends this assignment without substantive output. Do not announce that you "
                    "are waiting for a peer unless you actually use DELEGATE to create that work. "
                    "delegations must be null outside DELEGATE, evidence_requests must be null "
                    "outside EVIDENCE, and history_requests must be null outside HISTORY."
                ),
                self._transaction_execution_config_prompt(agent["agent_key"]),
            ]
        )
        return "\n\n".join(context_parts)

    async def _record_invalid_decision_telemetry(
        self,
        batch: dict[str, Any],
        agent: dict[str, Any],
        exc: AgentDecisionValidationError,
    ) -> None:
        """Preserve completed-turn economics/activity before decision-validation failure."""
        recorded = await self.db.record_execution_failure_telemetry(
            batch["batch_id"],
            exc.usage,
            exc.activity,
            exc.completion_source,
        )
        if not recorded:
            return

        usage_baseline = await self.db.get_execution_usage_baseline(batch["batch_id"])
        economics = self._execution_economics(
            exc,
            [],
            previous_usage=usage_baseline["usage"],
            has_prior_execution=usage_baseline["has_prior_execution"],
        )
        execution_tokens = economics["usage_delta"].get("total_tokens")
        event = await self.db.create_event(
            batch["room_id"],
            "execution_economics",
            agent["agent_key"],
            "observer",
            (
                f"{agent['name']}: execution economics before decision-validation "
                "failure — "
                + (
                    f"{execution_tokens} execution token(s)"
                    if execution_tokens is not None
                    else "execution token delta unavailable"
                )
            ),
            related_event_id=batch["assignment"].get("origin_event_id"),
            status="error",
            metadata={
                **economics,
                "decision_validation_failed": True,
                "assignment_id": batch["assignment_id"],
                "task_id": batch["task_id"],
                "batch_id": batch["batch_id"],
                "work_model_version": 2,
            },
            discussion_id=batch["round_id"],
            round_id=batch["round_id"],
        )
        self._publish_event(event)
        for item in exc.activity:
            tool_event = await self.db.create_event(
                batch["room_id"],
                "tool_activity",
                agent["agent_key"],
                "observer",
                (
                    f"{agent['name']}: {item['type'].replace('_', ' ')} "
                    f"({item.get('status') or 'observed'})"
                ),
                related_event_id=batch["assignment"].get("origin_event_id"),
                status="error" if item.get("status") not in {None, "completed"} else "recorded",
                metadata={
                    **item,
                    "decision_validation_failed": True,
                    "assignment_id": batch["assignment_id"],
                    "task_id": batch["task_id"],
                    "batch_id": batch["batch_id"],
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
            )
            self._publish_event(tool_event)

    async def _handle_assignment_failure(
        self,
        batch: dict[str, Any],
        agent: dict[str, Any],
        exc: Exception,
        generation: int,
        *,
        retryable: bool = True,
    ) -> None:
        diagnostic = " ".join(str(exc).split()) or type(exc).__name__
        if len(diagnostic) > 500:
            diagnostic = diagnostic[:497] + "..."
        async with self._lifecycle_locks[batch["room_id"]]:
            outcome = await self.db.fail_transaction_assignment(
                batch["room_id"],
                batch["round_id"],
                batch["batch_id"],
                diagnostic,
                retryable=retryable,
            )
            if batch.get("usage_continuation"):
                await self.db.finish_usage_continuation(
                    batch["usage_continuation"]["id"],
                    batch["batch_id"],
                    "ready" if outcome["retried"] else "failed",
                    diagnostic,
                )
            event = await self.db.create_event(
                batch["room_id"],
                "agent_error",
                agent["agent_key"],
                "observer",
                f"{agent['name']} transaction assignment failed: {diagnostic}",
                related_event_id=batch["assignment"].get("origin_event_id"),
                status="error",
                metadata={
                    "assignment_id": batch["assignment_id"],
                    "task_id": batch["task_id"],
                    "batch_id": batch["batch_id"],
                    "will_retry": outcome["retried"],
                    "work_model_version": 2,
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
            )
            self._publish_event(event)
            await self.ensure_workers(batch["room_id"])
            for target in outcome["wake_agent_keys"]:
                self.wake(batch["room_id"], target)
            if outcome["task_failed"]:
                current = await self.db.get_room(batch["room_id"])
                if current and current["status"] == RoomStatus.RUNNING:
                    await self._close_discussion(
                        batch["room_id"],
                        batch["round_id"],
                        "transaction_failed",
                        "Transaction task closed after a terminal coordinator assignment failure.",
                    )
        await self.publish_state(batch["room_id"])

    async def _handle_transaction_usage_wall(
        self,
        batch: dict[str, Any],
        agent: dict[str, Any],
        exc: AgentTurnTerminalError,
        generation: int,
        reported_retry_at: str,
        wake_at: str,
    ) -> None:
        diagnostic = " ".join(str(exc).split())[:4000]
        suspension_failed = False
        async with self._lifecycle_locks[batch["room_id"]]:
            current = await self._required_room(batch["room_id"])
            slot = self._worker_slots.get((batch["room_id"], agent["agent_key"]))
            claim_is_current = (
                current["discussion_id"] == batch["round_id"]
                and current["lifecycle_version"] == batch["lifecycle_version"]
                and current["status"] == RoomStatus.RUNNING
                and slot is not None
                and slot.generation == generation
                and not slot.quarantined
            )
            if not claim_is_current:
                await self.db.set_execution_state(
                    batch["batch_id"], "stale", diagnostic
                )
                if batch.get("usage_continuation"):
                    await self.db.finish_usage_continuation(
                        batch["usage_continuation"]["id"],
                        batch["batch_id"],
                        "cancelled",
                        diagnostic,
                    )
                return
            continuation = await self.db.suspend_transaction_usage_continuation(
                batch,
                agent,
                reported_retry_at=reported_retry_at,
                wake_at=wake_at,
                diagnostic=diagnostic,
                worker_generation=generation,
            )
            if continuation is None:
                suspension_failed = True
            else:
                self._set_worker_phase(
                    (batch["room_id"], agent["agent_key"]),
                    generation,
                    "usage_suspended",
                    batch["batch_id"],
                    f"Usage limit reached; transaction continuation is scheduled for {wake_at}.",
                )
                event = await self.db.create_event(
                    batch["room_id"],
                    "usage_limit_suspended",
                    agent["agent_key"],
                    "observer",
                    f"{agent['name']} paused — usage limit reached. Transaction continuation scheduled for {wake_at}.",
                    related_event_id=batch["assignment"].get("origin_event_id"),
                    status="warning",
                    metadata={
                        "classification": exc.codex_error_info,
                        "reported_retry_at": reported_retry_at,
                        "wake_at": wake_at,
                        "agent": agent["agent_key"],
                        "thread_id": (
                            batch["assignment"].get("context_thread_id")
                            if batch.get("provider_context_mode") == "assignment_thread"
                            else agent["thread_id"]
                        ),
                        "provider_context_mode": batch.get(
                            "provider_context_mode", "persistent_agent_thread"
                        ),
                        "source_batch_id": batch["batch_id"],
                        "assignment_id": batch["assignment_id"],
                        "task_id": batch["task_id"],
                        "usage_continuation_id": continuation["id"],
                        "reschedule_count": continuation["reschedule_count"],
                        "work_model_version": 2,
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(event)
        if suspension_failed:
            await self._handle_assignment_failure(
                batch,
                agent,
                RuntimeError(
                    "Transaction usage suspension lost its durable assignment claim"
                ),
                generation,
                retryable=False,
            )
            return
        await self.publish_state(batch["room_id"])

    async def _process_assignment(
        self, batch: dict[str, Any], generation: int
    ) -> None:
        room_id = batch["room_id"]
        agent_key = batch["agent_key"]
        agent = await self.db.get_agent(room_id, agent_key)
        if agent is None:
            return
        execution = batch.get("execution") or {}
        if execution.get("state") == "quarantined":
            slot = self._worker_slots.get((room_id, agent_key))
            if slot is not None and slot.generation == generation:
                slot.quarantined = True
                slot.phase = "quarantined"
                slot.reason = execution.get("error") or (
                    "The transaction claim has no exact Codex turn identity; replay is blocked."
                )
            await self.publish_state(room_id)
            return
        await self.publish_state(room_id)
        activity = await self.db.create_event(
            room_id,
            "agent_activity",
            agent_key,
            "observer",
            f"{agent['name']} is running transaction assignment {batch['assignment_id']}.",
            related_event_id=batch["assignment"].get("origin_event_id"),
            metadata={
                "state": "running",
                "assignment_id": batch["assignment_id"],
                "task_id": batch["task_id"],
                "batch_id": batch["batch_id"],
                "work_model_version": 2,
            },
            discussion_id=batch["round_id"],
            round_id=batch["round_id"],
        )
        self._publish_event(activity)

        try:
            progress = lambda: self._record_verified_progress(  # noqa: E731
                (room_id, agent_key), generation, batch["batch_id"]
            )
            if execution.get("state") == "result_ready":
                result = AgentRunResult(
                    decision=TransactionDecision.model_validate(execution["result"]),
                    usage=execution.get("usage"),
                    activity=execution.get("activity") or [],
                    thread_id=execution.get("sdk_thread_id"),
                    turn_id=execution.get("sdk_turn_id"),
                    completion_source=execution.get("completion_source") or "recovery",
                )
            elif execution.get("sdk_turn_id"):
                result = await self._await_with_inactivity_lease(
                    self.adapter.resume_agent(
                        agent,
                        self.workspace(room_id),
                        execution["sdk_thread_id"],
                        execution["sdk_turn_id"],
                        on_progress=progress,
                        transactional=True,
                    ),
                    (room_id, agent_key),
                    generation,
                )
            else:
                prompt = await self._assignment_prompt(batch, agent)
                provider_context_mode = batch.get(
                    "provider_context_mode", "persistent_agent_thread"
                )
                context_thread_id = batch["assignment"].get("context_thread_id")
                if provider_context_mode == "assignment_thread":
                    if context_thread_id is None:
                        context_thread_id = await self.adapter.start_context_thread(
                            agent,
                            self.workspace(room_id),
                            label=f"assignment {batch['assignment_id']}",
                        )
                        bound_context = await self.db.bind_assignment_context_thread(
                            batch["assignment_id"], context_thread_id
                        )
                        if not bound_context:
                            try:
                                await self.adapter.archive_thread(context_thread_id)
                            except Exception:
                                pass
                            raise RuntimeError(
                                "Assignment provider context thread could not be bound"
                            )
                        batch["assignment"]["context_thread_id"] = context_thread_id
                else:
                    context_thread_id = agent["thread_id"]

                if batch.get("usage_continuation"):
                    await self.adapter.prepare_usage_continuation(
                        agent,
                        self.workspace(room_id),
                        context_thread_id,
                    )
                    prompt = (
                        f"<usage_limit_continuation>\n"
                        f"{self.USAGE_CONTINUATION_INSTRUCTION}\n"
                        f"</usage_limit_continuation>\n\n{prompt}"
                    )

                async def bind_turn(thread_id: str, turn_id: str) -> None:
                    if (
                        provider_context_mode == "assignment_thread"
                        and thread_id != context_thread_id
                    ):
                        raise RuntimeError(
                            "Codex turn used the wrong assignment provider context"
                        )
                    bound = await self.db.bind_execution_turn(
                        batch["batch_id"], thread_id, turn_id, generation
                    )
                    if not bound:
                        raise RuntimeError(
                            "Codex turn could not be bound to its transaction assignment"
                        )

                run = (
                    self.adapter.run_agent_on_thread(
                        agent,
                        self.workspace(room_id),
                        prompt,
                        context_thread_id,
                        on_started=bind_turn,
                        on_progress=progress,
                        model=execution.get("model") or ROOM_MODEL,
                        reasoning_effort=(
                            execution.get("reasoning_effort")
                            or ROOM_REASONING_EFFORT
                        ),
                        transactional=True,
                    )
                    if provider_context_mode == "assignment_thread"
                    else self.adapter.run_agent(
                        agent,
                        self.workspace(room_id),
                        prompt,
                        on_started=bind_turn,
                        on_progress=progress,
                        model=execution.get("model") or ROOM_MODEL,
                        reasoning_effort=(
                            execution.get("reasoning_effort")
                            or ROOM_REASONING_EFFORT
                        ),
                        transactional=True,
                    )
                )
                result = await self._await_with_inactivity_lease(
                    run,
                    (room_id, agent_key),
                    generation,
                )
        except asyncio.CancelledError:
            raise
        except AgentTurnStateUnknownError as exc:
            await self.db.set_execution_state(
                batch["batch_id"], "quarantined", str(exc)
            )
            slot = self._worker_slots.get((room_id, agent_key))
            if slot is not None and slot.generation == generation:
                slot.quarantined = True
                slot.phase = "quarantined"
                slot.reason = str(exc)
            await self.publish_state(room_id)
            return
        except AgentTurnTerminalError as exc:
            if exc.codex_error_info in self.USAGE_WALL_ERROR_CODES:
                schedule = self._usage_wall_schedule(exc)
                if schedule is None:
                    await self._handle_assignment_failure(
                        batch,
                        agent,
                        RuntimeError(
                            "Codex reported usage exhaustion without a valid try-again time: "
                            + str(exc)
                        ),
                        generation,
                        retryable=False,
                    )
                else:
                    await self._handle_transaction_usage_wall(
                        batch, agent, exc, generation, *schedule
                    )
                return
            await self._handle_assignment_failure(
                batch, agent, exc, generation, retryable=False
            )
            return
        except TimeoutError:
            await self.adapter.interrupt(agent["id"])
            await self._handle_assignment_failure(
                batch,
                agent,
                AgentTurnTimeoutError(
                    "Transaction assignment exceeded its inactivity execution lease"
                ),
                generation,
                retryable=False,
            )
            return
        except AgentDecisionValidationError as exc:
            await self._record_invalid_decision_telemetry(batch, agent, exc)
            await self._handle_assignment_failure(batch, agent, exc, generation)
            return
        except Exception as exc:
            await self._handle_assignment_failure(batch, agent, exc, generation)
            return

        if not isinstance(result.decision, TransactionDecision):
            await self._handle_assignment_failure(
                batch,
                agent,
                RuntimeError("Transaction turn returned a legacy Room decision"),
                generation,
                retryable=False,
            )
            return
        decision = result.decision
        try:
            participants = {
                item["agent_key"]: item for item in await self.db.get_agents(room_id)
            }
            delegations = [
                item.model_dump(mode="json") for item in (decision.delegations or [])
            ]
            evidence_requests = [
                item.model_dump(mode="json")
                for item in (decision.evidence_requests or [])
            ]
            history_requests = [
                item.model_dump(mode="json")
                for item in (decision.history_requests or [])
            ]
            for item in delegations:
                if item["target"] == agent_key or item["target"] not in participants:
                    raise ValueError("Transaction delegation must target an available peer")
                if item.get("config") is not None and agent_key != "agent_c":
                    raise ValueError(
                        "Only Agent C may select a peer execution configuration"
                    )
            runnable_targets = [item["target"] for item in delegations]
        except ValueError as exc:
            await self._handle_assignment_failure(
                batch, agent, exc, generation, retryable=False
            )
            return

        recorded = await self.db.record_execution_result(
            batch["batch_id"],
            decision.model_dump(mode="json"),
            result.usage,
            result.activity,
            result.completion_source,
        )
        if not recorded:
            await self._handle_assignment_failure(
                batch,
                agent,
                RuntimeError("Transaction execution result lost its durable claim"),
                generation,
                retryable=False,
            )
            return

        self._set_worker_phase(
            (room_id, agent_key),
            generation,
            "settling",
            batch["batch_id"],
            "The Room is atomically settling the transaction assignment decision.",
        )

        async with self._lifecycle_locks[room_id]:
            current = await self._required_room(room_id)
            if (
                current["discussion_id"] != batch["round_id"]
                or current["lifecycle_version"] != batch["lifecycle_version"]
                or current["status"] in {
                    RoomStatus.STOPPED,
                    RoomStatus.FINISHED,
                    RoomStatus.PREPARING,
                    RoomStatus.ARCHIVED,
                    RoomStatus.ERROR,
                }
            ):
                await self.db.set_agent_status(agent["id"], AgentStatus.IDLE)
                await self.db.set_execution_state(batch["batch_id"], "stale")
                await self.publish_state(room_id)
                return

            registration_outcomes = self._settle_custom_capability_registration_requests(
                room_id, result.activity
            )
            usage_baseline = await self.db.get_execution_usage_baseline(
                batch["batch_id"]
            )
            economics = self._execution_economics(
                result,
                runnable_targets,
                previous_usage=usage_baseline["usage"],
                has_prior_execution=usage_baseline["has_prior_execution"],
            )
            execution_tokens = economics["usage_delta"].get("total_tokens")
            economics_event = await self.db.create_event(
                room_id,
                "execution_economics",
                agent_key,
                "observer",
                (
                    f"{agent['name']}: execution economics — "
                    f"{economics['tool_calls']} tool call(s), "
                    + (
                        f"{execution_tokens} execution token(s)"
                        if execution_tokens is not None
                        else "execution token delta unavailable"
                    )
                ),
                related_event_id=batch["assignment"].get("origin_event_id"),
                metadata={
                    **economics,
                    "assignment_id": batch["assignment_id"],
                    "task_id": batch["task_id"],
                    "batch_id": batch["batch_id"],
                    "work_model_version": 2,
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
            )
            self._publish_event(economics_event)
            for outcome in registration_outcomes:
                host_event = await self.db.create_event(
                    room_id,
                    "tool_activity",
                    agent_key,
                    "observer",
                    (
                        f"{agent['name']}: custom capability registration "
                        f"({outcome['status']}) — {outcome.get('capability') or 'unknown'}"
                    ),
                    related_event_id=batch["assignment"].get("origin_event_id"),
                    status=(
                        "recorded" if outcome["status"] == "completed" else "error"
                    ),
                    metadata={
                        **outcome,
                        "assignment_id": batch["assignment_id"],
                        "task_id": batch["task_id"],
                        "batch_id": batch["batch_id"],
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(host_event)
            for item in result.activity:
                tool_event = await self.db.create_event(
                    room_id,
                    "tool_activity",
                    agent_key,
                    "observer",
                    f"{agent['name']}: {item['type'].replace('_', ' ')} ({item['status']})",
                    related_event_id=batch["assignment"].get("origin_event_id"),
                    metadata={
                        **item,
                        "assignment_id": batch["assignment_id"],
                        "task_id": batch["task_id"],
                        "batch_id": batch["batch_id"],
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(tool_event)

            event_type = (
                "agent_pass"
                if decision.action == TransactionAction.PASS
                else "agent_message"
            )
            content = decision.message
            if decision.action == TransactionAction.DELEGATE and not content:
                content = "Delegated explicit transaction assignments to: " + ", ".join(
                    runnable_targets
                )
            if decision.action == TransactionAction.EVIDENCE and not content:
                content = (
                    f"Requested {len(evidence_requests)} bounded source evidence "
                    "operation(s) from CORE."
                )
            if decision.action == TransactionAction.HISTORY and not content:
                content = (
                    f"Requested {len(history_requests)} bounded prior-Room history "
                    "lookup(s) from CORE."
                )
            result_event = await self.db.create_event(
                room_id,
                event_type,
                agent_key,
                "all" if decision.action != TransactionAction.PASS else "room",
                content,
                related_event_id=batch["assignment"].get("origin_event_id"),
                metadata={
                    "task_id": batch["task_id"],
                    "assignment_id": batch["assignment_id"],
                    "batch_id": batch["batch_id"],
                    "transaction_action": decision.action,
                    "delegations": delegations or None,
                    "evidence_requests": evidence_requests or None,
                    "history_requests": history_requests or None,
                    "work_model_version": 2,
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
                execution_id=batch["batch_id"],
            )
            if result_event.pop("_created", True):
                self._publish_event(result_event)

            settlement = await self.db.settle_transaction_decision(
                room_id,
                batch["round_id"],
                batch["batch_id"],
                batch["assignment_id"],
                decision.action,
                result_event["id"],
                delegations,
                evidence_requests,
                history_requests,
            )
            if decision.action == TransactionAction.HISTORY:
                history_event = await self.db.create_event(
                    room_id,
                    "tool_activity",
                    "room",
                    "observer",
                    (
                        "CORE selected "
                        f"{len(settlement['history_event_ids'])} prior durable Room result(s) "
                        "for Assignment context."
                    ),
                    related_event_id=result_event["id"],
                    metadata={
                        "type": "deterministic_room_history",
                        "assignment_id": batch["assignment_id"],
                        "request_batch_id": batch["batch_id"],
                        "selected_event_ids": settlement["history_event_ids"],
                        "history_requests": history_requests,
                        "work_model_version": 2,
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(history_event)
            await self.db.set_agent_status(agent["id"], AgentStatus.IDLE)
            await self.db.set_execution_state(batch["batch_id"], "settled")
            continuation = batch.get("usage_continuation")
            if continuation:
                await self.db.finish_usage_continuation(
                    continuation["id"], batch["batch_id"], "completed"
                )
                continued = await self.db.create_event(
                    room_id,
                    "usage_continuation_completed",
                    agent_key,
                    "observer",
                    f"{agent['name']} completed its scheduled transaction usage-limit continuation.",
                    related_event_id=result_event["id"],
                    metadata={
                        "usage_continuation_id": continuation["id"],
                        "source_batch_id": continuation["source_batch_id"],
                        "continuation_batch_id": batch["batch_id"],
                        "assignment_id": batch["assignment_id"],
                        "thread_id": agent["thread_id"],
                        "work_model_version": 2,
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(continued)

            if settlement["turn_limit_hit"]:
                await self.db.cancel_transaction_work(room_id, batch["round_id"])
                await self.db.set_room_status(room_id, RoomStatus.STOPPED)
                await self.db.stop_active_round(room_id, "turn_limit")
                await self.db.set_all_agent_statuses(room_id, AgentStatus.IDLE)
                await self._system_event(
                    room_id,
                    "turn_limit",
                    "The configured Round turn limit was reached during transaction work.",
                )
                await self.publish_state(room_id)
                return

            if settlement["missing_required_contributors"]:
                required_event = await self.db.create_event(
                    room_id,
                    "required_contributors_pending",
                    "room",
                    "observer",
                    "Task settlement is blocked until the explicitly required "
                    "participant contribution(s) are recorded: "
                    + ", ".join(settlement["missing_required_contributors"]),
                    related_event_id=result_event["id"],
                    metadata={
                        "task_id": batch["task_id"],
                        "missing_required_contributors": settlement[
                            "missing_required_contributors"
                        ],
                        "work_model_version": 2,
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(required_event)

            if settlement["released_join_id"]:
                released = await self.db.create_event(
                    room_id,
                    "assignment_join_released",
                    "room",
                    "observer",
                    "All assignments in the dependency join reached terminal state; "
                    "the dependent assignment was released exactly once.",
                    related_event_id=result_event["id"],
                    metadata={
                        "join_id": settlement["released_join_id"],
                        "task_id": batch["task_id"],
                        "work_model_version": 2,
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(released)

            await self.ensure_workers(room_id)
            for target in settlement["wake_agent_keys"]:
                self.wake(room_id, target)
            if settlement["task_settled"] and current["status"] == RoomStatus.RUNNING:
                await self._close_discussion(
                    room_id,
                    batch["round_id"],
                    "transaction_settled",
                    "Transaction task closed after all explicit assignments and joins settled.",
                )

        if settlement.get("evidence_request_id") and not settlement["turn_limit_hit"]:
            await self._execute_transaction_evidence(
                room_id,
                batch["round_id"],
                batch["assignment_id"],
                settlement["evidence_request_id"],
                evidence_requests,
                related_event_id=result_event["id"],
            )

        await self._maybe_compact_context(batch, agent, result)
        await self.publish_state(room_id)

    async def _process_delivery(self, batch: dict[str, Any], generation: int) -> None:
        room_id = batch["room_id"]
        agent_key = batch["agent_key"]
        agent = await self.db.get_agent(room_id, agent_key)
        events = batch["events"]
        first_event = events[0]
        input_ids = [event["id"] for event in events]
        if agent is None:
            await self.db.fail_deliveries(
                batch["delivery_ids"],
                "Agent missing",
                retry=False,
                batch_id=batch["batch_id"],
            )
            return
        execution = batch.get("execution") or {}
        if execution.get("state") == "quarantined":
            slot = self._worker_slots.get((room_id, agent_key))
            if slot is not None and slot.generation == generation:
                slot.quarantined = True
                slot.phase = "quarantined"
                slot.reason = execution.get("error") or (
                    "The processing claim has no exact Codex turn identity; replay is blocked."
                )
            await self.publish_state(room_id)
            return
        if batch.get("status") == AgentStatus.READY_TO_FINISH and not batch.get("recovered"):
            source_keys = {
                event["source"] for event in events if event["source"].startswith("agent_")
            }
            for source_key in source_keys:
                source_agent = await self.db.get_agent(room_id, source_key)
                if source_agent and source_agent["status"] == AgentStatus.IDLE:
                    await self.db.set_agent_status(source_agent["id"], AgentStatus.READY_TO_FINISH)
            reopened = await self.db.create_event(
                room_id,
                "agent_reopened",
                "room",
                "observer",
                f"{agent['name']} received substantive unread input after its FINISH boundary and reopened.",
                related_event_id=first_event["id"],
                metadata={
                    "reopened_agent": agent_key,
                    "input_event_ids": input_ids,
                    "batch_id": batch["batch_id"],
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
            )
            self._publish_event(reopened)
        await self.publish_state(room_id)
        activity = await self.db.create_event(
            room_id,
            "agent_activity",
            agent_key,
            "observer",
            (
                f"{agent['name']} is continuing work interrupted by a usage limit."
                if batch.get("usage_continuation")
                else f"{agent['name']} is running on {len(events)} unread event(s)."
            ),
            related_event_id=first_event["id"],
            metadata={
                "state": "running",
                "input_event_ids": input_ids,
                "triggering_event_ids": batch["triggering_event_ids"],
                "passive_event_ids": batch["passive_event_ids"],
                "batch_id": batch["batch_id"],
                "usage_continuation_id": (
                    batch["usage_continuation"]["id"]
                    if batch.get("usage_continuation") else None
                ),
            },
            discussion_id=batch["round_id"],
            round_id=batch["round_id"],
        )
        self._publish_event(activity)

        try:
            progress = lambda: self._record_verified_progress(  # noqa: E731
                (room_id, agent_key), generation, batch["batch_id"]
            )
            if execution.get("state") == "result_ready":
                result = AgentRunResult(
                    decision=AgentDecision.model_validate(execution["result"]),
                    usage=execution.get("usage"),
                    activity=execution.get("activity") or [],
                    thread_id=execution.get("sdk_thread_id"),
                    turn_id=execution.get("sdk_turn_id"),
                    completion_source=execution.get("completion_source") or "recovery",
                )
            elif execution.get("sdk_turn_id"):
                result = await self._await_with_inactivity_lease(
                    self.adapter.resume_agent(
                        agent,
                        self.workspace(room_id),
                        execution["sdk_thread_id"],
                        execution["sdk_turn_id"],
                        on_progress=progress,
                    ),
                    (room_id, agent_key),
                    generation,
                )
            else:
                prompt = await self._delivery_prompt(events, agent, batch["round_id"])
                if batch.get("usage_continuation"):
                    await self.adapter.prepare_usage_continuation(
                        agent, self.workspace(room_id)
                    )
                    prompt = (
                        f"<usage_limit_continuation>\n"
                        f"{self.USAGE_CONTINUATION_INSTRUCTION}\n"
                        f"</usage_limit_continuation>\n\n{prompt}"
                    )

                async def bind_turn(thread_id: str, turn_id: str) -> None:
                    bound = await self.db.bind_execution_turn(
                        batch["batch_id"], thread_id, turn_id, generation
                    )
                    if not bound:
                        raise RuntimeError(
                            "Codex turn could not be bound to its durable Room execution"
                        )

                result = await self._await_with_inactivity_lease(
                    self.adapter.run_agent(
                        agent,
                        self.workspace(room_id),
                        prompt,
                        on_started=bind_turn,
                        on_progress=progress,
                        model=execution.get("model") or ROOM_MODEL,
                        reasoning_effort=(
                            execution.get("reasoning_effort")
                            or ROOM_REASONING_EFFORT
                        ),
                    ),
                    (room_id, agent_key),
                    generation,
                )
        except asyncio.CancelledError:
            raise
        except AgentTurnStateUnknownError as exc:
            await self.db.set_execution_state(
                batch["batch_id"], "quarantined", str(exc)
            )
            slot = self._worker_slots.get((room_id, agent_key))
            if slot is not None and slot.generation == generation:
                slot.quarantined = True
                slot.phase = "quarantined"
                slot.reason = str(exc)
            await self.publish_state(room_id)
            return
        except AgentTurnTerminalError as exc:
            if exc.codex_error_info in self.USAGE_WALL_ERROR_CODES:
                schedule = self._usage_wall_schedule(exc)
                if schedule is None:
                    await self._handle_turn_failure(
                        batch,
                        agent,
                        RuntimeError(
                            "Codex reported usage exhaustion without a valid try-again time: "
                            + str(exc)
                        ),
                        generation,
                        retryable=False,
                    )
                else:
                    await self._handle_usage_wall(
                        batch, agent, exc, generation, *schedule
                    )
                return
            await self._handle_turn_failure(batch, agent, exc, generation)
            return
        except TimeoutError:
            interrupt_outcome = await self.adapter.interrupt(agent["id"])
            if interrupt_outcome == InterruptOutcome.UNKNOWN:
                slot = self._worker_slots.get((room_id, agent_key))
                if slot is not None and slot.generation == generation:
                    slot.quarantined = True
                    slot.phase = "stopping"
                    slot.reason = (
                        "The execution lease expired, but SDK interruption remains "
                        "unconfirmed; replacement is quarantined."
                    )
            await self._handle_turn_failure(
                batch,
                agent,
                AgentTurnTimeoutError(
                    "Agent turn exceeded its inactivity execution lease after no "
                    f"verifiable progress for {self.AGENT_TURN_TIMEOUT_SECONDS:g} seconds"
                ),
                generation,
                retryable=False,
            )
            return
        except Exception as exc:
            await self._handle_turn_failure(batch, agent, exc, generation)
            return

        try:
            participants = await self.db.get_agents(room_id)
            runnable_targets = self._resolve_invoke_targets(
                result.decision,
                agent["agent_key"],
                participants,
            )
            self._resolve_execution_configs(
                result.decision,
                agent["agent_key"],
                runnable_targets,
            )
        except ValueError as exc:
            await self._handle_turn_failure(
                batch, agent, exc, generation, retryable=False
            )
            return

        recorded = await self.db.record_execution_result(
            batch["batch_id"],
            result.decision.model_dump(mode="json"),
            result.usage,
            result.activity,
            result.completion_source,
        )
        if not recorded:
            if batch.get("usage_continuation"):
                await self.db.finish_usage_continuation(
                    batch["usage_continuation"]["id"],
                    batch["batch_id"],
                    "cancelled",
                    "Execution result no longer matches the durable claim",
                )
            await self._record_stale_failure(
                batch,
                agent,
                "Completed Codex result no longer matches the durable execution claim",
                "execution_result_compare_and_set_failed",
            )
            return

        self._set_worker_phase(
            (room_id, agent_key),
            generation,
            "settling",
            batch["batch_id"],
            (
                "The exact Codex turn was recovered from authoritative history; "
                "the Room is recording its decision."
                if result.completion_source == "history"
                else "The SDK turn completed; the Room is recording and routing its decision."
            ),
        )

        async with self._lifecycle_locks[room_id]:
            current = await self._required_room(room_id)
            if (
                current["discussion_id"] != batch["round_id"]
                or current["lifecycle_version"] != batch["lifecycle_version"]
                or current["status"] in {
                RoomStatus.STOPPED,
                RoomStatus.FINISHED,
                RoomStatus.PREPARING,
                RoomStatus.ARCHIVED,
                RoomStatus.ERROR,
                }
            ):
                await self.db.set_agent_status(agent["id"], AgentStatus.IDLE)
                await self.db.set_execution_state(batch["batch_id"], "stale")
                if batch.get("usage_continuation"):
                    await self.db.finish_usage_continuation(
                        batch["usage_continuation"]["id"],
                        batch["batch_id"],
                        "cancelled",
                        "Room lifecycle changed before continuation settlement",
                    )
                stale = await self.db.create_event(
                    room_id,
                    "stale_result",
                    "room",
                    "observer",
                    f"A completed {agent['name']} turn was not routed because its round was stopped, closed, or replaced.",
                    related_event_id=first_event["id"],
                    metadata={
                        "outcome": result.decision.outcome,
                        "usage": result.usage,
                        "input_event_ids": input_ids,
                        "batch_id": batch["batch_id"],
                        "invocation_lifecycle_version": batch["lifecycle_version"],
                        "current_lifecycle_version": current["lifecycle_version"],
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(stale)
                await self.publish_state(room_id)
                return

            completed = await self.db.complete_deliveries(
                batch["delivery_ids"], batch_id=batch["batch_id"]
            )
            if not completed:
                await self.db.set_execution_state(
                    batch["batch_id"], "quarantined", "Delivery settlement compare-and-set failed"
                )
                return
            await self.db.mark_round_context_consumed(batch["round_id"], agent["id"])
            registration_outcomes = self._settle_custom_capability_registration_requests(
                room_id, result.activity
            )
            for outcome in registration_outcomes:
                capability_name = outcome.get("capability") or "unknown"
                host_event = await self.db.create_event(
                    room_id,
                    "tool_activity",
                    agent_key,
                    "observer",
                    (
                        f"{agent['name']}: custom capability registration "
                        f"({outcome['status']}) — {capability_name}"
                    ),
                    related_event_id=first_event["id"],
                    status=(
                        "recorded" if outcome["status"] == "completed" else "error"
                    ),
                    metadata={
                        **outcome,
                        "input_event_ids": input_ids,
                        "batch_id": batch["batch_id"],
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                    event_id=(
                        f"event_{batch['batch_id']}_customreg_{outcome['index']}"
                    ),
                )
                self._publish_event(host_event)
            usage_baseline = await self.db.get_execution_usage_baseline(
                batch["batch_id"]
            )
            economics = self._execution_economics(
                result,
                runnable_targets,
                previous_usage=usage_baseline["usage"],
                has_prior_execution=usage_baseline["has_prior_execution"],
            )
            execution_tokens = economics["usage_delta"].get("total_tokens")
            economics_event = await self.db.create_event(
                room_id,
                "execution_economics",
                agent_key,
                "observer",
                (
                    f"{agent['name']}: execution economics — "
                    f"{economics['tool_calls']} tool call(s), "
                    + (
                        f"{execution_tokens} execution token(s)"
                        if execution_tokens is not None
                        else "execution token delta unavailable"
                    )
                ),
                related_event_id=first_event["id"],
                metadata={
                    **economics,
                    "input_event_ids": input_ids,
                    "batch_id": batch["batch_id"],
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
            )
            self._publish_event(economics_event)
            for item in result.activity:
                tool_event = await self.db.create_event(
                    room_id,
                    "tool_activity",
                    agent_key,
                    "observer",
                    f"{agent['name']}: {item['type'].replace('_', ' ')} ({item['status']})",
                    related_event_id=first_event["id"],
                    metadata={**item, "input_event_ids": input_ids, "batch_id": batch["batch_id"]},
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(tool_event)
            await self._apply_decision(batch, agent, result)
            await self.db.set_execution_state(batch["batch_id"], "settled")
            continuation = batch.get("usage_continuation")
            if continuation:
                await self.db.finish_usage_continuation(
                    continuation["id"], batch["batch_id"], "completed"
                )
                continued = await self.db.create_event(
                    room_id,
                    "usage_continuation_completed",
                    agent_key,
                    "observer",
                    f"{agent['name']} completed its scheduled usage-limit continuation.",
                    related_event_id=first_event["id"],
                    metadata={
                        "usage_continuation_id": continuation["id"],
                        "source_batch_id": continuation["source_batch_id"],
                        "continuation_batch_id": batch["batch_id"],
                        "thread_id": agent["thread_id"],
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(continued)

        await self._maybe_compact_context(batch, agent, result)

    @staticmethod
    def _usage_token_fields(usage: dict[str, Any] | None) -> dict[str, int | float]:
        raw = usage if isinstance(usage, dict) else {}
        usage_total = raw.get("total") if isinstance(raw.get("total"), dict) else raw
        return {
            key: usage_total.get(key)
            for key in (
                "input_tokens",
                "cached_input_tokens",
                "cache_write_input_tokens",
                "output_tokens",
                "reasoning_output_tokens",
                "total_tokens",
            )
            if isinstance(usage_total.get(key), (int, float))
            and not isinstance(usage_total.get(key), bool)
        }

    @classmethod
    def _execution_economics(
        cls,
        result: AgentRunResult | AgentDecisionValidationError,
        runnable_targets: list[str],
        *,
        previous_usage: dict[str, Any] | None = None,
        has_prior_execution: bool = False,
    ) -> dict[str, Any]:
        activity_counts: dict[str, int] = {}
        failed_tool_calls = 0
        for item in result.activity:
            item_type = str(item.get("type", "unknown"))
            activity_counts[item_type] = activity_counts.get(item_type, 0) + 1
            if item.get("status") not in {None, "completed"} or item.get("ok") is False:
                failed_tool_calls += 1

        tool_calls = len(result.activity)
        capability_invocations = activity_counts.get("deterministic_capability", 0)
        capability_failures = sum(
            1
            for item in result.activity
            if item.get("type") == "deterministic_capability"
            and (
                item.get("status") not in {None, "completed"}
                or item.get("ok") is False
            )
        )
        token_fields = cls._usage_token_fields(result.usage)
        previous_fields = cls._usage_token_fields(previous_usage)
        usage_delta: dict[str, int | float] = {}
        if not token_fields:
            usage_delta_status = "unavailable"
        elif not has_prior_execution:
            usage_delta = dict(token_fields)
            usage_delta_status = "first_execution"
        elif not previous_fields:
            usage_delta_status = "unavailable"
        else:
            comparable = set(token_fields).intersection(previous_fields)
            if not comparable or "total_tokens" not in comparable:
                usage_delta_status = "unavailable"
            elif any(token_fields[key] < previous_fields[key] for key in comparable):
                usage_delta_status = "non_monotonic"
            else:
                usage_delta = {
                    key: token_fields[key] - previous_fields[key]
                    for key in comparable
                }
                usage_delta_status = "computed"

        execution_total = usage_delta.get("total_tokens")
        return {
            "type": "execution_economics",
            "tool_calls": tool_calls,
            "activity_counts": dict(sorted(activity_counts.items())),
            "failed_tool_calls": failed_tool_calls,
            "failed_tool_fraction": (
                round(failed_tool_calls / tool_calls, 4) if tool_calls else 0.0
            ),
            "capability_invocations": capability_invocations,
            "capability_failures": capability_failures,
            "file_changes": activity_counts.get("file_change", 0),
            "context_compactions": activity_counts.get("context_compaction", 0),
            "sub_agent_activity": activity_counts.get("sub_agent_activity", 0),
            "peer_invocations": len(runnable_targets),
            "usage": token_fields,
            "usage_delta": usage_delta,
            "usage_delta_status": usage_delta_status,
            "tokens_per_tool_call": (
                round(float(execution_total) / tool_calls, 1)
                if tool_calls and execution_total is not None
                else None
            ),
        }

    def _settle_custom_capability_registration_requests(
        self,
        room_id: str,
        activity: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Publish/bind verified registration requests outside the agent sandbox."""
        outcomes: list[dict[str, Any]] = []
        for index, item in enumerate(activity):
            if (
                item.get("type") != "deterministic_capability_registry"
                or item.get("operation") != "register"
                or item.get("status") != "completed"
            ):
                continue
            capability_id = item.get("capability")
            request = item.get("registration_request")
            try:
                if (
                    not isinstance(capability_id, str)
                    or not isinstance(request, dict)
                    or request.get("capability_id") != capability_id
                ):
                    raise CustomCapabilityRegistryError(
                        "Custom capability registration request is malformed"
                    )
                receipt = VerificationReceipt.from_dict(request.get("receipt"))
                existing = load_room_custom_capabilities(
                    self.data_root,
                    room_id,
                    reserved_capability_ids=frozenset(CORE_CAPABILITIES),
                ).get(capability_id)
                if (
                    existing is not None
                    and existing.receipt.verification_sha256
                    == receipt.verification_sha256
                    and existing.package.package_sha256 == receipt.package_sha256
                    and existing.package.manifest_sha256 == receipt.manifest_sha256
                    and existing.package.implementation_sha256
                    == receipt.implementation_sha256
                ):
                    registration = existing.registration
                    binding = existing
                else:
                    registration = publish_verified_custom_capability(
                        self.workspace(room_id),
                        self.data_root,
                        room_id,
                        capability_id,
                        receipt,
                    )
                    binding = bind_custom_registration(
                        self.data_root,
                        room_id,
                        registration.registration_sha256,
                        reserved_capability_ids=frozenset(CORE_CAPABILITIES),
                    )
                outcomes.append(
                    {
                        "index": index,
                        "type": "custom_capability_registration",
                        "status": "completed",
                        "capability": capability_id,
                        "registration_sha256": registration.registration_sha256,
                        "verification_sha256": receipt.verification_sha256,
                        "package_sha256": binding.package.package_sha256,
                        "implementation_sha256": binding.package.implementation_sha256,
                        "binding_sha256": binding.binding_sha256,
                    }
                )
            except (
                CustomCapabilityPackageError,
                CustomCapabilityVerificationError,
                CustomCapabilityPublicationError,
                CustomCapabilityRegistryError,
                ValueError,
                OSError,
            ) as exc:
                diagnostic = " ".join(str(exc).split()) or type(exc).__name__
                if len(diagnostic) > 500:
                    diagnostic = diagnostic[:497] + "..."
                outcomes.append(
                    {
                        "index": index,
                        "type": "custom_capability_registration",
                        "status": "error",
                        "capability": capability_id if isinstance(capability_id, str) else None,
                        "error": diagnostic,
                    }
                )
        return outcomes

    async def _maybe_compact_context(
        self, batch: dict[str, Any], agent: dict[str, Any], result: AgentRunResult
    ) -> None:
        if batch.get("provider_context_mode") == "assignment_thread":
            return
        usage = result.usage or {}
        last_usage = usage.get("last") or {}
        input_tokens = last_usage.get("input_tokens")
        context_window = usage.get("model_context_window")
        if not isinstance(input_tokens, int) or not isinstance(context_window, int):
            return
        if any(item.get("type") == "context_compaction" for item in result.activity):
            return
        previous, baseline_established = (
            await self.db.establish_context_checkpoint_growth_baseline(
                batch["room_id"],
                agent["agent_key"],
                input_tokens,
                batch["batch_id"],
            )
        )
        # The first successful turn after compaction supplies the first authoritative
        # model-input measurement. It establishes the baseline but cannot compact.
        # Growth before this turn is deliberately not credited to the 25k allowance.
        if baseline_established:
            return
        if context_window <= 0 or input_tokens / context_window < self.CONTEXT_COMPACTION_RATIO:
            return
        if previous is not None:
            previous_tokens = previous["metadata"].get("growth_baseline_input_tokens")
            if (
                isinstance(previous_tokens, int)
                and input_tokens
                < previous_tokens + self.CONTEXT_COMPACTION_MIN_GROWTH_TOKENS
            ):
                return

        metadata = {
            "agent": agent["agent_key"],
            "input_tokens": input_tokens,
            "model_context_window": context_window,
            "threshold_ratio": self.CONTEXT_COMPACTION_RATIO,
            "batch_id": batch["batch_id"],
        }
        try:
            await self.adapter.compact_agent(agent, self.workspace(batch["room_id"]))
            event = await self.db.create_event(
                batch["room_id"],
                "context_checkpoint",
                "room",
                "observer",
                f"{agent['name']} context compacted after {input_tokens} input tokens "
                f"({input_tokens / context_window:.0%} of the model window).",
                metadata={
                    **metadata,
                    "result": "compacted",
                    "growth_baseline_state": "pending",
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
            )
        except Exception as exc:
            diagnostic = " ".join(str(exc).split()) or type(exc).__name__
            if len(diagnostic) > 500:
                diagnostic = diagnostic[:497] + "..."
            event = await self.db.create_event(
                batch["room_id"],
                "context_checkpoint",
                "room",
                "observer",
                f"{agent['name']} context compaction failed nonfatally: {diagnostic}",
                status="error",
                metadata={**metadata, "result": "failed", "error": diagnostic},
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
            )
        self._publish_event(event)

    async def _apply_decision(
        self, batch: dict[str, Any], agent: dict[str, Any], result: AgentRunResult
    ) -> None:
        room_id = batch["room_id"]
        agent_key = agent["agent_key"]
        decision = result.decision
        first_event = batch["events"][0]
        input_ids = [event["id"] for event in batch["events"]]
        retry_failures = await self.db.get_retryable_attempt_failures(
            room_id, batch["round_id"], agent_key, input_ids
        )
        recovery_metadata = self._recovery_metadata(retry_failures, "recovered")
        room_config = await self._required_room(room_id)
        round_item = await self.db.register_decision(
            room_id,
            batch["round_id"],
            agent["id"],
            decision.outcome,
            batch["max_event_sequence"],
            execution_id=batch["batch_id"],
        )
        limit_hit = round_item["turn_count"] >= room_config["max_turns"]
        participants = await self.db.get_agents(room_id)
        peers = [item for item in participants if item["agent_key"] != agent_key]
        if not peers:
            raise RuntimeError("A Room requires at least one peer")
        requested_runnable_targets = self._resolve_invoke_targets(
            decision, agent_key, participants
        )
        delegation_parent = self._multi_peer_c_delegation_parent(batch, agent_key)
        defer_c_return = (
            decision.outcome == Outcome.MESSAGE
            and delegation_parent is not None
            and "agent_c" in requested_runnable_targets
        )
        runnable_targets = tuple(
            target
            for target in requested_runnable_targets
            if not (defer_c_return and target == "agent_c")
        )
        resolved_execution_configs = self._resolve_execution_configs(
            decision,
            agent_key,
            requested_runnable_targets,
        )
        peer_keys = tuple(item["agent_key"] for item in peers)
        ready_peers = {
            item["agent_key"] for item in peers if item["status"] == AgentStatus.READY_TO_FINISH
        }

        if decision.outcome == Outcome.MESSAGE:
            event = await self.db.create_event(
                room_id,
                "agent_message",
                agent_key,
                "all",
                decision.message,
                related_event_id=first_event["id"],
                metadata={
                    "usage": result.usage,
                    "input_event_ids": input_ids,
                    "triggering_event_ids": batch["triggering_event_ids"],
                    "passive_event_ids": batch["passive_event_ids"],
                    "batch_id": batch["batch_id"],
                    "invoke_targets": decision.invoke_targets,
                    "execution_configs": (
                        [
                            selection.model_dump(mode="json")
                            for selection in decision.execution_configs
                        ]
                        if decision.execution_configs is not None
                        else None
                    ),
                    "resolved_execution_configs": resolved_execution_configs,
                    "readable_recipients": list(peer_keys),
                    "requested_runnable_recipients": list(requested_runnable_targets),
                    "runnable_recipients": list(runnable_targets),
                    "deferred_runnable_recipients": (
                        ["agent_c"] if defer_c_return else []
                    ),
                    **(
                        {
                            "delegation_cohort_parent_event_id": delegation_parent["id"]
                        }
                        if defer_c_return and delegation_parent is not None
                        else {}
                    ),
                    "legacy_fanout_invocations_avoided": (
                        len(peer_keys) - len(requested_runnable_targets)
                    ),
                    **recovery_metadata,
                },
                deliver_to=() if limit_hit else peer_keys,
                runnable_to=() if limit_hit else runnable_targets,
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
                execution_id=batch["batch_id"],
            )
            ready_targets = ready_peers.intersection(runnable_targets)
            if ready_targets and not limit_hit:
                # The sender has supplied the content that interrupted closure and is now
                # waiting for the peer's final reaction. A substantive reply can reopen
                # the sender in the same way.
                await self.db.set_agent_status(agent["id"], AgentStatus.READY_TO_FINISH)
                for peer_key in ready_targets:
                    await self.db.reopen_ready_agent(room_id, peer_key)
            else:
                await self.db.set_agent_status(agent["id"], AgentStatus.IDLE)
            if event.pop("_created", True):
                self._publish_event(event)
            if not limit_hit:
                for peer in peers:
                    peer_key = peer["agent_key"]
                    if peer_key not in runnable_targets:
                        continue
                    if peer_key not in ready_targets:
                        self.wake(room_id, peer_key)
                        continue
                    reopened = await self.db.create_event(
                        room_id,
                        "agent_reopened",
                        "room",
                        "observer",
                        f"{peer['name']} was ready to finish but received new substantive content from {agent['name']} and may respond.",
                        related_event_id=event["id"],
                        metadata={"reopened_agent": peer_key, "message_source": agent_key},
                        discussion_id=batch["round_id"],
                        round_id=batch["round_id"],
                    )
                    self._publish_event(reopened)
                    self.wake(room_id, peer_key)
        elif decision.outcome == Outcome.PASS:
            event = await self.db.create_event(
                room_id,
                "agent_pass",
                agent_key,
                "room",
                decision.message,
                related_event_id=first_event["id"],
                metadata={
                    "usage": result.usage,
                    "input_event_ids": input_ids,
                    "batch_id": batch["batch_id"],
                    **recovery_metadata,
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
                execution_id=batch["batch_id"],
            )
            await self.db.set_agent_status(agent["id"], AgentStatus.IDLE)
            if event.pop("_created", True):
                self._publish_event(event)
        else:
            event = await self.db.create_event(
                room_id,
                "agent_finish",
                agent_key,
                "room",
                decision.message,
                related_event_id=first_event["id"],
                metadata={
                    "usage": result.usage,
                    "input_event_ids": input_ids,
                    "batch_id": batch["batch_id"],
                    "finish_boundary_sequence": batch["max_event_sequence"],
                    **recovery_metadata,
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
                execution_id=batch["batch_id"],
            )
            await self.db.set_agent_status(agent["id"], AgentStatus.READY_TO_FINISH)
            if event.pop("_created", True):
                self._publish_event(event)

        if delegation_parent is not None and not limit_hit:
            await self._release_c_delegation_cohort_if_settled(
                room_id, batch["round_id"], delegation_parent["id"]
            )

        if limit_hit:
            await self.db.set_room_status(room_id, RoomStatus.STOPPED)
            await self.db.cancel_pending_deliveries(room_id, batch["round_id"])
            await self.db.stop_active_round(room_id, "turn_limit")
            await self.db.set_all_agent_statuses(room_id, AgentStatus.IDLE)
            await self._system_event(
                room_id,
                "turn_limit",
                f"Round stopped after reaching the {room_config['max_turns']}-turn limit.",
            )
        elif decision.outcome in {Outcome.FINISH, Outcome.PASS}:
            settled, open_keys, pending_keys, all_finished, causal = (
                await self._settlement_state(room_id, batch["round_id"])
            )
            if settled:
                integration_scheduled = await self._schedule_c_integration_if_needed(
                    room_id, batch["round_id"]
                )
                if not integration_scheduled:
                    if causal:
                        reaction_event = await self.db.create_event(
                            room_id,
                            "reactions_settled",
                            "room",
                            "observer",
                            "Every recipient settled the listed message boundary with PASS or FINISH; "
                            "no synthetic sender turn was required.",
                            related_event_id=causal[0]["message_event_id"],
                            metadata={"boundaries": causal},
                            discussion_id=batch["round_id"],
                            round_id=batch["round_id"],
                        )
                        self._publish_event(reaction_event)
                    await self._close_discussion(
                        room_id,
                        batch["round_id"],
                        "mutual_finish" if all_finished else (
                            "reactions_settled" if causal else "finish_and_pass"
                        ),
                        "Discussion closed after every engaged participant independently or "
                        "causally settled with FINISH or PASS.",
                    )
            elif decision.outcome == Outcome.FINISH:
                blockers = sorted(set(open_keys) | set(pending_keys))
                waiting_text = (
                    f"{agent['name']} is ready to finish. The Room is waiting for: "
                    + ", ".join(blockers)
                    + "."
                )
                waiting = await self.db.create_event(
                    room_id,
                    "finish_waiting",
                    "room",
                    "observer",
                    waiting_text,
                    related_event_id=event["id"],
                    metadata={
                        "ready_agent": agent_key,
                        "waiting_for": blockers,
                        "open_turns": open_keys,
                        **(
                            {
                                "peer": peers[0]["agent_key"],
                                "peer_status": peers[0]["status"],
                                "peer_has_open_turn": peers[0]["agent_key"] in open_keys,
                            }
                            if len(peers) == 1
                            else {}
                        ),
                    },
                    discussion_id=batch["round_id"],
                    round_id=batch["round_id"],
                )
                self._publish_event(waiting)
            elif round_item["consecutive_passes"] >= room_config["max_consecutive_passes"]:
                integration_scheduled = await self._schedule_c_integration_if_needed(
                    room_id, batch["round_id"]
                )
                if not integration_scheduled:
                    await self._system_event(
                        room_id,
                        "pass_limit",
                        "The configured consecutive PASS limit was reached.",
                    )
                    await self._close_discussion(
                        room_id,
                        batch["round_id"],
                        "pass_limit",
                        "Discussion closed after the configured consecutive PASS limit.",
                    )
        await self.publish_state(room_id)

    @staticmethod
    def _recovery_metadata(
        failures: list[dict[str, Any]], status: str
    ) -> dict[str, Any]:
        if not failures:
            return {}
        return {
            "retry_recovery": {
                "status": status,
                "attempt_failure_count": len(failures),
                "attempt_failure_event_ids": [item["id"] for item in failures],
                "attempt_batch_ids": [
                    item["metadata"].get("batch_id") for item in failures
                    if item["metadata"].get("batch_id")
                ],
            }
        }

    @staticmethod
    def _multi_peer_c_delegation_parent(
        batch: dict[str, Any], agent_key: str
    ) -> dict[str, Any] | None:
        """Return the C delegation event when this turn belongs to a multi-peer cohort."""
        triggering = set(batch.get("triggering_event_ids") or [])
        for event in batch.get("events", []):
            if event.get("id") not in triggering:
                continue
            if event.get("event_type") != "agent_message" or event.get("source") != "agent_c":
                continue
            targets = (event.get("metadata") or {}).get("runnable_recipients") or []
            if (
                isinstance(targets, list)
                and len(targets) > 1
                and agent_key in targets
            ):
                return event
        return None

    async def _release_c_delegation_cohort_if_settled(
        self, room_id: str, round_id: str, delegation_event_id: str
    ) -> bool:
        """Wake C once after every peer in one multi-target C delegation has settled."""
        events = await self.db.get_round_decision_events(room_id, round_id)
        delegation = next(
            (
                event
                for event in events
                if event["id"] == delegation_event_id
                and event["event_type"] == "agent_message"
                and event["source"] == "agent_c"
            ),
            None,
        )
        if delegation is None:
            return False

        cohort_deliveries = [
            item for item in delegation.get("deliveries", []) if item.get("runnable")
        ]
        if len(cohort_deliveries) < 2:
            return False

        settlement_signals: dict[str, str] = {}
        response_event_ids: dict[str, str] = {}
        returned_message_event_ids: list[str] = []
        terminal_delivery_states = {"failed", "cancelled"}

        for delivery in sorted(cohort_deliveries, key=lambda item: item["agent_key"]):
            peer_key = delivery["agent_key"]
            responses = [
                event
                for event in events
                if event["source"] == peer_key
                and delegation_event_id
                in (event.get("metadata") or {}).get("input_event_ids", [])
            ]
            if responses:
                response = responses[-1]
                signal = response["event_type"].removeprefix("agent_").upper()
                settlement_signals[peer_key] = signal
                response_event_ids[peer_key] = response["id"]
                if response["event_type"] == "agent_message":
                    returned_message_event_ids.append(response["id"])
                continue
            if delivery.get("status") in terminal_delivery_states:
                settlement_signals[peer_key] = str(delivery["status"]).upper()
                continue
            # A delivery may already be marked delivered a few instructions before
            # its decision event is persisted. Do not release the cohort in that race.
            return False

        trigger_id = (
            f"event_{delegation_event_id.removeprefix('event_')}"
            "_delegation_cohort_settled_agent_c"
        )
        trigger = await self.db.create_event(
            room_id,
            "delegation_cohort_settled",
            "room",
            "agent_c",
            (
                "All peers invoked by the same delegation have now settled. "
                "Integrate the accumulated returns before the next substantive "
                "recommendation or follow-up. "
                + ", ".join(
                    f"{key}: {settlement_signals[key]}"
                    for key in sorted(settlement_signals)
                )
                + "."
            ),
            related_event_id=delegation_event_id,
            metadata={
                "delegation_event_id": delegation_event_id,
                "delegation_cohort": [
                    item["agent_key"]
                    for item in sorted(
                        cohort_deliveries, key=lambda item: item["agent_key"]
                    )
                ],
                "settlement_signals": settlement_signals,
                "response_event_ids": response_event_ids,
                "returned_message_event_ids": returned_message_event_ids,
            },
            deliver_to=("agent_c",),
            runnable_to=("agent_c",),
            discussion_id=round_id,
            round_id=round_id,
            event_class="conversation",
            conversational=True,
            counts_as_turn=False,
            counts_toward_pass=False,
            visibility="mechanical",
            agent_readable=True,
            turn_triggering=True,
            event_id=trigger_id,
        )
        if trigger.pop("_created", True):
            self._publish_event(trigger)
        if await self.db.reopen_ready_agent(room_id, "agent_c"):
            reopened = await self.db.create_event(
                room_id,
                "agent_reopened",
                "room",
                "observer",
                "Agent C received the completed peer delegation cohort and reopened for integration.",
                related_event_id=trigger["id"],
                metadata={
                    "reopened_agent": "agent_c",
                    "message_source": "room",
                    "reason": "delegation_cohort_settled",
                    "delegation_event_id": delegation_event_id,
                },
                discussion_id=round_id,
                round_id=round_id,
            )
            self._publish_event(reopened)
        await self.ensure_workers(room_id)
        self.wake(room_id, "agent_c")
        return True

    @staticmethod
    def _resolve_invoke_targets(
        decision: AgentDecision,
        sender_key: str,
        participants: list[dict[str, Any]],
    ) -> tuple[str, ...]:
        if decision.outcome != Outcome.MESSAGE:
            return ()
        peer_keys = tuple(
            item["agent_key"]
            for item in participants
            if item["agent_key"] != sender_key
        )
        requested = decision.invoke_targets
        if requested is None or requested == ["all"]:
            return peer_keys
        unknown = set(requested) - set(peer_keys)
        if unknown:
            raise ValueError(
                "invoke_targets contains unavailable or unauthorized peers: "
                + ", ".join(sorted(unknown))
            )
        requested_set = set(requested)
        return tuple(key for key in peer_keys if key in requested_set)

    @staticmethod
    def _resolve_execution_configs(
        decision: AgentDecision,
        sender_key: str,
        runnable_targets: tuple[str, ...],
    ) -> dict[str, dict[str, str]]:
        """Resolve C's bounded per-invocation cognition choices to exact SDK settings."""
        if (
            decision.outcome != Outcome.MESSAGE
            or sender_key != "agent_c"
            or not decision.execution_configs
        ):
            return {}
        requested = {
            selection.target: selection.config
            for selection in decision.execution_configs
        }
        unauthorized = set(requested) - set(runnable_targets)
        if unauthorized:
            raise ValueError(
                "execution_configs may name only peers C is invoking now: "
                + ", ".join(sorted(unauthorized))
            )
        resolved: dict[str, dict[str, str]] = {}
        for target, config_id in requested.items():
            model, effort = EXECUTION_CONFIGS[config_id]
            resolved[target] = {
                "config_id": config_id,
                "model": model,
                "reasoning_effort": effort,
            }
        return resolved

    async def _schedule_c_integration_if_needed(
        self, room_id: str, round_id: str
    ) -> bool:
        """Wake C once when unread passive peer work would otherwise cross closure."""
        integrator = await self.db.get_agent(room_id, "agent_c")
        if integrator is None:
            return False
        pending = await self.db.get_pending_integration_material(
            room_id, round_id, "agent_c"
        )
        if not pending:
            return False

        # Existing runnable or active C work is already an integration opportunity.
        # If some passive material is newer than that trigger, it will remain pending
        # and this method will schedule one later trigger at the next quiescent edge.
        if await self.db.has_open_delivery(room_id, "agent_c", round_id):
            return True
        if integrator["status"] in {
            AgentStatus.RUNNING,
            AgentStatus.USAGE_SUSPENDED,
        }:
            return True

        states = {
            item["agent_key"]: item
            for item in await self.db.get_round_agent_states(round_id)
        }
        peer_signals = []
        for key in sorted(states):
            if key == "agent_c":
                continue
            outcome = states[key].get("last_outcome") or "no terminal signal"
            peer_signals.append(f"{key}: {outcome}")
        pending_ids = [item["id"] for item in pending]
        trigger = await self.db.create_event(
            room_id,
            "integration_required",
            "room",
            "agent_c",
            (
                "Integrate the unread peer work in this batch before final Round closure. "
                "Decide whether the overall objective is satisfied, whether contradictions "
                "or dependencies remain, and whether follow-up delegation is useful. "
                + (
                    "Current peer settlement signals: " + ", ".join(peer_signals) + "."
                    if peer_signals else ""
                )
            ),
            related_event_id=pending_ids[-1],
            metadata={
                "integrator": "agent_c",
                "pending_peer_message_event_ids": pending_ids,
                "pending_peer_sources": sorted({item["source"] for item in pending}),
                "peer_settlement_signals": {
                    key: states[key].get("last_outcome")
                    for key in sorted(states)
                    if key != "agent_c"
                },
            },
            deliver_to=("agent_c",),
            runnable_to=("agent_c",),
            discussion_id=round_id,
            round_id=round_id,
            event_class="conversation",
            conversational=True,
            counts_as_turn=False,
            counts_toward_pass=False,
            visibility="mechanical",
            agent_readable=True,
            turn_triggering=True,
        )
        if trigger.pop("_created", True):
            self._publish_event(trigger)
        if await self.db.reopen_ready_agent(room_id, "agent_c"):
            reopened = await self.db.create_event(
                room_id,
                "agent_reopened",
                "room",
                "observer",
                "Agent C was ready to finish but must integrate unread peer work before closure.",
                related_event_id=trigger["id"],
                metadata={
                    "reopened_agent": "agent_c",
                    "message_source": "room",
                    "reason": "integration_before_closure",
                },
                discussion_id=round_id,
                round_id=round_id,
            )
            self._publish_event(reopened)
        await self.ensure_workers(room_id)
        self.wake(room_id, "agent_c")
        return True

    async def _settlement_state(
        self, room_id: str, round_id: str
    ) -> tuple[bool, list[str], list[str], bool, list[dict[str, Any]]]:
        agents = await self.db.get_agents(room_id)
        states = {
            state["agent_id"]: state for state in await self.db.get_round_agent_states(round_id)
        }
        causal = await self._causally_settled_messages(room_id, round_id, agents, states)
        causal_keys = {item["sender"] for item in causal}
        open_keys = [
            item["agent_key"]
            for item in agents
            if await self.db.has_open_delivery(room_id, item["agent_key"], round_id)
        ]
        participation = {
            agent["agent_key"]: counts
            for agent, counts in zip(
                agents,
                await asyncio.gather(
                    *(
                        self.db.get_delivery_participation(
                            room_id, agent["agent_key"], round_id
                        )
                        for agent in agents
                    )
                ),
                strict=True,
            )
        }
        pending_keys: list[str] = []
        all_finished = True
        engaged_count = 0
        triad_room = any(item["agent_key"] == "agent_c" for item in agents)
        for item in agents:
            state = states.get(item["id"], {})
            finished = item["status"] == AgentStatus.READY_TO_FINISH
            passed = state.get("last_outcome") == Outcome.PASS
            late_unengaged_member = (
                int(state.get("delivery_start_sequence") or 0) > 0
                and not state.get("last_outcome")
                and item["agent_key"] not in open_keys
                and item["status"] != AgentStatus.RUNNING
            )
            counts = participation[item["agent_key"]]
            never_engaged_member = (
                triad_room
                and counts["readable_count"] == 0
                and not state.get("last_outcome")
                and item["agent_key"] not in open_keys
                and item["status"] != AgentStatus.RUNNING
            )
            passive_only_unengaged_member = (
                counts["readable_count"] > 0
                and counts["runnable_count"] == 0
                and not state.get("last_outcome")
                and item["agent_key"] not in open_keys
                and item["status"] != AgentStatus.RUNNING
            )
            if (
                late_unengaged_member
                or never_engaged_member
                or passive_only_unengaged_member
            ):
                # Settlement follows actual engagement rather than membership alone.
                # This lets C deliberately solve work without waking unnecessary peers,
                # preserves the newcomer sequence boundary, and keeps passive readers
                # from becoming mandatory model calls. Unread passive peer MESSAGE
                # material for C is handled separately by the integration barrier.
                continue
            engaged_count += 1
            if not finished:
                all_finished = False
            if not (finished or passed or item["agent_key"] in causal_keys):
                pending_keys.append(item["agent_key"])
        return (
            engaged_count > 0 and not open_keys and not pending_keys,
            open_keys,
            pending_keys,
            engaged_count > 0 and all_finished,
            causal,
        )

    async def _reconcile_quiescent_room(
        self,
        room_id: str,
        round_id: str,
        *,
        fallback_reason: str = "quiescent_without_work",
        fallback_content: str = (
            "Round closed because no participant was running and no runnable deliveries remained."
        ),
    ) -> bool:
        """Close a RUNNING round that has no possible next state transition."""
        room = await self.db.get_room(room_id)
        if room is None or room["status"] != RoomStatus.RUNNING:
            return False
        agents = await self.db.get_agents(room_id)
        if any(
            agent["status"] in {AgentStatus.RUNNING, AgentStatus.USAGE_SUSPENDED}
            for agent in agents
        ):
            return False
        round_item = await self.db.get_round(round_id)
        if round_item and round_item.get("work_model_version", 1) == 2:
            if await self.db.has_active_transaction_task(room_id, round_id):
                return False
            await self._close_discussion(
                room_id,
                round_id,
                fallback_reason,
                fallback_content,
            )
            return True
        open_deliveries = await asyncio.gather(
            *(
                self.db.has_open_delivery(room_id, agent["agent_key"], round_id)
                for agent in agents
            )
        )
        if any(open_deliveries):
            return False
        if await self._schedule_c_integration_if_needed(room_id, round_id):
            return False
        settled, _, _, all_finished, causal = await self._settlement_state(room_id, round_id)
        if settled:
            reason = "mutual_finish" if all_finished else (
                "reactions_settled" if causal else "finish_and_pass"
            )
            content = "Discussion closed after every engaged participant settled."
        else:
            reason = fallback_reason
            content = fallback_content
        await self._close_discussion(room_id, round_id, reason, content)
        return True

    async def _causally_settled_messages(
        self,
        room_id: str,
        round_id: str,
        agents: list[dict[str, Any]],
        states: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Find exact MESSAGE boundaries fully answered by terminal peer reactions."""
        events = await self.db.get_round_decision_events(room_id, round_id)
        boundaries: list[dict[str, Any]] = []
        for sender in agents:
            state = states.get(sender["id"], {})
            if state.get("last_outcome") != Outcome.MESSAGE:
                continue
            message = next(
                (
                    event for event in reversed(events)
                    if event["event_type"] == "agent_message"
                    and event["source"] == sender["agent_key"]
                ),
                None,
            )
            if message is None:
                continue
            deferred_runnable = set(
                (message.get("metadata") or {}).get(
                    "deferred_runnable_recipients", []
                )
            )
            cohort = {
                delivery["agent_key"]
                for delivery in message.get("deliveries", [])
                if delivery.get("runnable")
                or delivery["agent_key"] in deferred_runnable
            }
            if not cohort or any(
                delivery["status"] != "delivered"
                for delivery in message.get("deliveries", [])
                if delivery.get("runnable")
                or delivery["agent_key"] in deferred_runnable
            ):
                continue
            terminal_ids: dict[str, str] = {}
            defeated = False
            for recipient in cohort:
                relevant = [
                    event for event in events
                    if event["source"] == recipient
                    and message["id"] in event.get("metadata", {}).get("input_event_ids", [])
                ]
                if any(event["event_type"] == "agent_message" for event in relevant):
                    defeated = True
                    break
                terminal = next(
                    (
                        event for event in reversed(relevant)
                        if event["event_type"] in {"agent_pass", "agent_finish"}
                    ),
                    None,
                )
                if terminal is None:
                    defeated = True
                    break
                terminal_ids[recipient] = terminal["id"]
            if not defeated:
                boundaries.append(
                    {
                        "sender": sender["agent_key"],
                        "message_event_id": message["id"],
                        "delivery_cohort": sorted(cohort),
                        "terminal_decision_event_ids": {
                            key: terminal_ids[key] for key in sorted(terminal_ids)
                        },
                    }
                )
        return boundaries

    async def _close_discussion(
        self, room_id: str, discussion_id: str, reason: str, content: str
    ) -> None:
        event = await self.db.close_discussion(room_id, discussion_id, reason, content)
        self._publish_event(event)

    async def _handle_turn_failure(
        self,
        batch: dict[str, Any],
        agent: dict[str, Any],
        exc: Exception,
        generation: int,
        *,
        retryable: bool = True,
    ) -> None:
        attempts = max(event["attempts"] for event in batch["events"])
        retry = retryable and attempts < 2
        first_event = batch["events"][0]
        diagnostic = " ".join(str(exc).split()) or type(exc).__name__
        if len(diagnostic) > 500:
            diagnostic = diagnostic[:497] + "..."
        async with self._lifecycle_locks[batch["room_id"]]:
            current = await self._required_room(batch["room_id"])
            slot = self._worker_slots.get((batch["room_id"], agent["agent_key"]))
            claim_is_current = (
                current["discussion_id"] == batch["round_id"]
                and current["lifecycle_version"] == batch["lifecycle_version"]
                and current["status"] == RoomStatus.RUNNING
                and slot is not None
                and slot.generation == generation
            )
            if not claim_is_current:
                await self.db.set_execution_state(batch["batch_id"], "stale", diagnostic)
                if batch.get("usage_continuation"):
                    await self.db.finish_usage_continuation(
                        batch["usage_continuation"]["id"],
                        batch["batch_id"],
                        "cancelled",
                        diagnostic,
                    )
                await self._record_stale_failure(
                    batch, agent, diagnostic, "lifecycle_or_generation_changed"
                )
                return
            changed = await self.db.fail_deliveries(
                batch["delivery_ids"],
                diagnostic,
                retry=retry,
                batch_id=batch["batch_id"],
            )
            if changed != len(batch["delivery_ids"]):
                await self.db.set_execution_state(batch["batch_id"], "stale", diagnostic)
                await self._record_stale_failure(
                    batch, agent, diagnostic, "delivery_claim_changed"
                )
                return
            await self.db.set_execution_state(batch["batch_id"], "failed", diagnostic)
            if batch.get("usage_continuation"):
                await self.db.finish_usage_continuation(
                    batch["usage_continuation"]["id"],
                    batch["batch_id"],
                    "ready" if retry else "failed",
                    diagnostic,
                )
            await self.db.set_agent_status(agent["id"], AgentStatus.ERROR, diagnostic)
            prior_failures = (
                await self.db.get_retryable_attempt_failures(
                    batch["room_id"],
                    batch["round_id"],
                    agent["agent_key"],
                    [item["id"] for item in batch["events"]],
                )
                if not retry
                else []
            )
            event = await self.db.create_event(
                batch["room_id"],
                "agent_error",
                agent["agent_key"],
                "observer",
                (
                    f"{agent['name']} attempt interrupted — retrying: {diagnostic}"
                    if retry
                    else f"{agent['name']} agent error — recovery failed: {diagnostic}"
                ),
                related_event_id=first_event["id"],
                status="warning" if retry else "error",
                metadata={
                    "attempt": attempts,
                    "will_retry": retry,
                    "operator_state": "retrying" if retry else "terminal_failure",
                    "diagnostic": diagnostic,
                    "input_event_ids": [item["id"] for item in batch["events"]],
                    "batch_id": batch["batch_id"],
                    "worker_generation": generation,
                    **self._recovery_metadata(prior_failures, "failed"),
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
            )
            self._publish_event(event)
            if not retry:
                await self.db.set_room_status(batch["room_id"], RoomStatus.ERROR)
                await self.db.stop_active_round(batch["room_id"], "agent_error")
        if retry:
            await asyncio.sleep(1)
            async with self._lifecycle_locks[batch["room_id"]]:
                current = await self._required_room(batch["room_id"])
                slot = self._worker_slots.get((batch["room_id"], agent["agent_key"]))
                if (
                    current["discussion_id"] == batch["round_id"]
                    and current["lifecycle_version"] == batch["lifecycle_version"]
                    and current["status"] == RoomStatus.RUNNING
                    and slot is not None
                    and slot.generation == generation
                    and not slot.quarantined
                ):
                    await self.db.set_agent_status(agent["id"], AgentStatus.IDLE)
                    self.wake(batch["room_id"], agent["agent_key"])
        await self.publish_state(batch["room_id"])

    @classmethod
    def _usage_wall_schedule(
        cls,
        exc: AgentTurnTerminalError,
        *,
        now: datetime | None = None,
    ) -> tuple[str, str] | None:
        """Parse only the retry forms emitted with Codex usageLimitExceeded."""
        match = re.search(r"try again at\s+(.+?)\.?$", str(exc), re.IGNORECASE)
        if match is None:
            return None
        reported = match.group(1).strip()
        reference = now if now is not None else datetime.now().astimezone()
        local_tz = reference.tzinfo
        if local_tz is None:
            return None
        parsed: datetime | None = None
        try:
            parsed_time = datetime.strptime(reported, "%I:%M %p").time()
            parsed = datetime.combine(reference.date(), parsed_time, tzinfo=local_tz)
        except ValueError:
            dated = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", reported, flags=re.IGNORECASE)
            try:
                parsed = datetime.strptime(dated, "%b %d, %Y %I:%M %p").replace(
                    tzinfo=local_tz
                )
            except ValueError:
                return None
        reported_utc = parsed.astimezone(UTC)
        wake_utc = reported_utc + timedelta(
            seconds=cls.USAGE_CONTINUATION_GRACE_SECONDS
        )
        return (
            reported_utc.isoformat(timespec="milliseconds"),
            wake_utc.isoformat(timespec="milliseconds"),
        )

    async def _handle_usage_wall(
        self,
        batch: dict[str, Any],
        agent: dict[str, Any],
        exc: AgentTurnTerminalError,
        generation: int,
        reported_retry_at: str,
        wake_at: str,
    ) -> None:
        diagnostic = " ".join(str(exc).split())[:4000]
        async with self._lifecycle_locks[batch["room_id"]]:
            current = await self._required_room(batch["room_id"])
            slot = self._worker_slots.get((batch["room_id"], agent["agent_key"]))
            claim_is_current = (
                current["discussion_id"] == batch["round_id"]
                and current["lifecycle_version"] == batch["lifecycle_version"]
                and current["status"] == RoomStatus.RUNNING
                and slot is not None
                and slot.generation == generation
                and not slot.quarantined
            )
            if not claim_is_current:
                await self.db.set_execution_state(batch["batch_id"], "stale", diagnostic)
                if batch.get("usage_continuation"):
                    await self.db.finish_usage_continuation(
                        batch["usage_continuation"]["id"],
                        batch["batch_id"],
                        "cancelled",
                        diagnostic,
                    )
                await self._record_stale_failure(
                    batch, agent, diagnostic, "lifecycle_or_generation_changed"
                )
                return
            continuation = await self.db.suspend_usage_continuation(
                batch,
                agent,
                reported_retry_at=reported_retry_at,
                wake_at=wake_at,
                diagnostic=diagnostic,
                worker_generation=generation,
            )
            if continuation is None:
                await self._record_stale_failure(
                    batch, agent, diagnostic, "usage_suspension_compare_and_set_failed"
                )
                return
            self._set_worker_phase(
                (batch["room_id"], agent["agent_key"]),
                generation,
                "usage_suspended",
                batch["batch_id"],
                f"Usage limit reached; continuation is scheduled for {wake_at}.",
            )
            event = await self.db.create_event(
                batch["room_id"],
                "usage_limit_suspended",
                agent["agent_key"],
                "observer",
                f"{agent['name']} paused — usage limit reached. Continuation scheduled for {wake_at}.",
                related_event_id=batch["events"][0]["id"],
                status="warning",
                metadata={
                    "classification": exc.codex_error_info,
                    "reported_retry_at": reported_retry_at,
                    "wake_at": wake_at,
                    "agent": agent["agent_key"],
                    "thread_id": agent["thread_id"],
                    "source_batch_id": batch["batch_id"],
                    "input_event_ids": continuation["input_event_ids"],
                    "triggering_event_ids": continuation["triggering_event_ids"],
                    "usage_continuation_id": continuation["id"],
                    "reschedule_count": continuation["reschedule_count"],
                },
                discussion_id=batch["round_id"],
                round_id=batch["round_id"],
            )
            self._publish_event(event)
        await self.publish_state(batch["room_id"])

    async def _record_stale_failure(
        self,
        batch: dict[str, Any],
        agent: dict[str, Any],
        diagnostic: str,
        reason: str,
    ) -> None:
        event = await self.db.create_event(
            batch["room_id"],
            "stale_failure",
            "room",
            "observer",
            (
                f"A late {agent['name']} failure was ignored because its work claim "
                f"is no longer current: {diagnostic}"
            ),
            related_event_id=batch["events"][0]["id"],
            metadata={
                "reason": reason,
                "input_event_ids": [item["id"] for item in batch["events"]],
                "batch_id": batch["batch_id"],
            },
            discussion_id=batch["round_id"],
            round_id=batch["round_id"],
        )
        self._publish_event(event)

    async def _delivery_prompt(
        self, events: list[dict[str, Any]], agent: dict[str, Any], round_id: str
    ) -> str:
        source_labels: dict[str, str] = {
            "observer": "the human Observer",
            "room": "the Room lifecycle system",
        }
        participants = await self.db.get_agents(agent["room_id"])
        for participant in participants:
            source_labels[participant["agent_key"]] = (
                f"{participant['name']}, an independent peer thread"
            )
        available_peer_targets = [
            participant["agent_key"]
            for participant in participants
            if participant["agent_key"] != agent["agent_key"]
        ]
        round_item = await self.db.get_round(round_id)
        if round_item is None:
            raise RuntimeError(f"Round {round_id} is missing")
        state = await self.db.get_round_agent_state(round_id, agent["id"])
        context_parts: list[str] = []
        if state and not state["context_consumed_at"]:
            context_parts.extend(
                [
                    "<stored_round_context>",
                    f"Round title: {round_item['title'] or '(untitled)'}",
                    f"Public prompt:\n{round_item['prompt']}",
                ]
            )
            if round_item.get("task_overlay"):
                context_parts.append(f"Round task overlay:\n{round_item['task_overlay']}")
            private = round_item.get("participant_private", {}).get(agent["agent_key"])
            if private:
                context_parts.append(
                    "Private initialization for you only (other participants did not receive it):\n"
                    + private
                )
            overlay = round_item.get("participant_overlays", {}).get(agent["agent_key"])
            if overlay:
                context_parts.append(f"Temporary overlay for you in this round:\n{overlay}")
            context_parts.append("</stored_round_context>")
        has_passive_context = any(
            not bool(event.get("delivery_runnable")) for event in events
        )
        event_parts = ["<unread_room_events>"]
        for event in events:
            privacy = " private-to-you" if (
                event["event_type"] == "observer_message"
                and event["destination"] not in {"all", "both"}
            ) else ""
            delivery_role = (
                "triggering" if bool(event.get("delivery_runnable")) else "passive_context"
            )
            event_parts.extend(
                [
                    f"<event id=\"{event['id']}\" type=\"{event['event_type']}\" "
                    f"role=\"{delivery_role}\" "
                    f"source=\"{source_labels.get(event['source'], event['source'])}\"{privacy}>",
                    event["content"],
                    "</event>",
                ]
            )
        event_parts.append("</unread_room_events>")
        event_role_instruction = (
            "<room_event_roles>\n"
            "Events with role=\"triggering\" caused this execution and define the current work "
            "that requires your response. Events with role=\"passive_context\" are earlier "
            "readable context coalesced for continuity; consider them when relevant, but do not "
            "mistake them for a new request.\n"
            "</room_event_roles>\n\n"
            if has_passive_context
            else ""
        )
        heading = "NEW TOPIC / ROUND TURN" if any(
            event["event_type"] == "round_start_turn" for event in events
        ) else "COALESCED ROOM EVENTS"
        return f"""{heading}
Round ID: {round_id}
Unread event count: {len(events)}

{chr(10).join(context_parts)}

{event_role_instruction}{chr(10).join(event_parts)}

{self.DETERMINISTIC_CAPABILITY_INSTRUCTION}

Respond to this event according to your own judgment. Your final response must satisfy the Room's structured schema: outcome MESSAGE, PASS, or FINISH; message text; invoke_targets; and execution_configs. For MESSAGE, invoke_targets may be {available_peer_targets}, ["all"] for every peer, or [] for a public/readable message that should make no peer runnable. The message remains public/readable to every authorized peer, but only named invoke_targets become runnable. Use null to retain legacy all-peer invocation.

{self._execution_config_prompt(agent["agent_key"])}

For MESSAGE, execution_configs is null or an array of target/config records, for example a record selecting agent_a with luna-medium. For PASS or FINISH, set invoke_targets and execution_configs to null. PASS creates no follow-up delivery. FINISH marks you ready to close; the Room preserves any peer turns already in progress and waits for every engaged participant to settle. Do not place JSON in markdown fences."""

    @staticmethod
    def _transaction_execution_config_prompt(agent_key: str) -> str:
        if agent_key != "agent_c":
            return (
                "Only Agent C may select a peer execution config in this P1 trial. "
                "If you DELEGATE, set each delegation record's config to null. "
                "If stronger cognition appears necessary, say so in your substantive "
                "result or delegation instruction so C can decide whether to escalate."
            )
        choices = ", ".join(EXECUTION_CONFIGS)
        return (
            "As Agent C, each DELEGATE record may optionally select that peer's "
            f"execution config from: {choices}. Prefer luna-medium for routine, "
            "bounded work and spend more only for affirmative complexity, uncertainty, "
            "risk, or verification reasons. A null config uses the Terra/high "
            "compatibility fallback. COMPLETE and PASS contain no delegation records."
        )

    @staticmethod
    def _execution_config_prompt(agent_key: str) -> str:
        if agent_key != "agent_c":
            return (
                "Only Agent C may select peer execution_configs in this P1 trial. "
                "Set execution_configs to null. If the assigned work appears to need "
                "stronger cognition, report that to C in a MESSAGE and request escalation."
            )
        choices = ", ".join(EXECUTION_CONFIGS)
        return (
            "As Agent C, you may set execution_configs only for peers you are invoking "
            "in this MESSAGE. Allowed bounded P1 configs are: "
            f"{choices}. Prefer luna-medium for routine, bounded delegated work. "
            "Choose a more expensive config only when complexity, uncertainty, risk, "
            "or prior verification trouble gives an affirmative reason to spend more. "
            "A peer may ask you to escalate later; you can redelegate with a stronger "
            "config. If an invoked peer has no explicit execution_configs entry, the "
            "compatibility fallback remains the current Terra/high policy. "
            "Set execution_configs to null when no peer cognition is invoked."
        )

    async def _system_event(
        self, room_id: str, event_type: str, content: str, status: str = "recorded"
    ) -> dict[str, Any]:
        event = await self.db.create_event(
            room_id, event_type, "room", "observer", content, status=status
        )
        self._publish_event(event)
        return event

    def _publish_event(self, event: dict[str, Any]) -> None:
        self.hub.publish(event["room_id"], {"kind": "event", "event": event})

    async def _watchdog_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(10)
                await self._watchdog_cycle()
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)

    async def _watchdog_cycle(self) -> None:
        self._watchdog_last_started_at = utc_now()
        try:
            await self._watchdog_tick()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._watchdog_failure_count += 1
            self._watchdog_consecutive_failures += 1
            self._watchdog_last_error_at = utc_now()
            message = f"{type(exc).__name__}: {exc}"
            self._watchdog_last_error = message[:1000]
            raise
        else:
            self._watchdog_last_success_at = utc_now()
            self._watchdog_consecutive_failures = 0

    async def _watchdog_tick(self) -> None:
        now = datetime.now(UTC)
        for room in await self.db.list_rooms(include_archived=False):
            if room["status"] != RoomStatus.RUNNING:
                continue
            # Reconcile only from structural proof: a completed/missing worker
            # cannot still own an SDK await. Age by itself never replaces work.
            await self.ensure_workers(room["id"])
            due_agent_keys: list[str] = []
            async with self._lifecycle_locks[room["id"]]:
                outcomes = await self.db.release_due_usage_continuations(
                    room["id"], now.isoformat(timespec="milliseconds")
                )
                for continuation in outcomes:
                    fired = continuation["outcome"] == "fired"
                    event = await self.db.create_event(
                        room["id"],
                        (
                            "usage_continuation_wake"
                            if fired else "usage_continuation_cancelled"
                        ),
                        continuation["agent_key"] if fired else "room",
                        "observer",
                        (
                            f"{continuation['agent_key']} usage-limit continuation is now due."
                            if fired
                            else "A scheduled usage-limit continuation was suppressed as stale."
                        ),
                        related_event_id=(continuation["input_event_ids"] or [None])[0],
                        status="recorded" if fired else "warning",
                        metadata={
                            "usage_continuation_id": continuation["id"],
                            "source_batch_id": continuation["source_batch_id"],
                            "reported_retry_at": continuation["reported_retry_at"],
                            "wake_at": continuation["wake_at"],
                            "thread_id": continuation["thread_id"],
                            "assignment_id": continuation.get("assignment_id"),
                            "outcome": continuation["outcome"],
                            "reason": continuation.get("last_error"),
                        },
                        discussion_id=continuation["round_id"],
                        round_id=continuation["round_id"],
                    )
                    self._publish_event(event)
                    if fired:
                        due_agent_keys.append(continuation["agent_key"])
            for agent_key in due_agent_keys:
                self.wake(room["id"], agent_key)
            # Execution health is derived from process-local evidence and elapsed
            # time, so refresh subscribers even when no conversational event occurs.
            await self.publish_state(room["id"])
            async with self._lifecycle_locks[room["id"]]:
                current = await self.db.get_room(room["id"])
                if current is None or current["status"] != RoomStatus.RUNNING:
                    continue
                if await self._reconcile_quiescent_room(
                    room["id"], current["active_round_id"]
                ):
                    await self.publish_state(room["id"])
                    continue
            round_item = await self.db.get_round(room["active_round_id"])
            activity_at = (
                round_item.get("last_activity_at") or round_item.get("started_at")
                if round_item
                else room["updated_at"]
            )
            updated = datetime.fromisoformat(activity_at)
            if (now - updated).total_seconds() < room["inactivity_seconds"]:
                continue
            agents = await self.db.get_agents(room["id"])
            if any(
                agent["status"] in {
                    AgentStatus.RUNNING,
                    AgentStatus.USAGE_SUSPENDED,
                }
                for agent in agents
            ):
                continue
            if (
                round_item
                and round_item.get("work_model_version", 1) == 2
                and await self.db.has_active_transaction_task(
                    room["id"], room["active_round_id"]
                )
            ):
                continue
            if any(
                await asyncio.gather(
                    *(
                        self.db.has_open_delivery(
                            room["id"], agent["agent_key"], room["active_round_id"]
                        )
                        for agent in agents
                    )
                )
            ):
                continue
            await self._close_discussion(
                room["id"],
                room["discussion_id"],
                "inactivity_timeout",
                f"Round closed after {room['inactivity_seconds']} seconds of inactivity.",
            )
            await self.publish_state(room["id"])

    async def _required_room(self, room_id: str) -> dict[str, Any]:
        room = await self.db.get_room(room_id)
        if room is None:
            raise KeyError(room_id)
        return room

    async def _required_snapshot(self, room_id: str) -> dict[str, Any]:
        snapshot = await self.snapshot(room_id)
        if snapshot is None:
            raise KeyError(room_id)
        return snapshot
