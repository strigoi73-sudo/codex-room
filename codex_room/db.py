from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, AsyncIterator, Iterable

import aiosqlite

from .personalities import (
    AGENT_A_IMPLEMENTER_INSTRUCTIONS,
    AGENT_B_VERIFIER_INSTRUCTIONS,
    AGENT_C_INTEGRATOR_INSTRUCTIONS,
    DEFAULT_PERSONALITY_BY_AGENT,
    compose_agent_instructions,
)

from .models import (
    AgentStatus,
    CreateRoomRequest,
    PrepareRoundRequest,
    RolloverRoomRequest,
    RoomStatus,
    RoundStatus,
    EXECUTION_CONFIGS,
)


_LEGACY_PAIR_PROFILE_SHA256 = {
    "agent_a": "4a70ed77bc61a6e4c81c6bc9c013b9cd86dab4d158c7ec3fe5d8b9b7e2b06399",
    "agent_b": "f32fc62a1a86c392c53d2d21313fa74491fd282094a1dbebea245966e7a1ca61",
}
_TRIAD_PROFILE_TEXT = {
    "agent_a": AGENT_A_IMPLEMENTER_INSTRUCTIONS,
    "agent_b": AGENT_B_VERIFIER_INSTRUCTIONS,
    "agent_c": AGENT_C_INTEGRATOR_INSTRUCTIONS,
}
_TRIAD_PROFILE_MIGRATION_ID = "triad_profiles_v1"
_EARLY_TRIAD_PROFILE_SHA256 = {
    "agent_a": "cfad300ba057c99c9839765615bd8851cd1c4960a2f0714cae57c70f810b0480",
    "agent_b": "97c822fcd38b6e408158b6d040d1a517c8030530af1f80033fdbd9d8b22c4bac",
    "agent_c": "7bfe1e10d35c084e1eb8aac8013459fdc3ac48d3824ebd9d728a9ea9ceb0c6cb",
}
_EARLY_TRIAD_PROFILE_MIGRATION_ID = "triad_profiles_v2"
_PRE_PERSONALITY_LAYER_PROFILE_SHA256 = {
    "agent_a": "5d12def051f832aa83ef2bb929d6d3aa9301b7f9eb387dc8eaece1c30b494493",
    "agent_b": "aa769b9385fa8ab277769abf45963de732f16a1443d5ff6514f599f5f4def6de",
    "agent_c": "b07be1545126c2061f82c2128195a091f991ab38a9b0ebbeb92b1d22e7614e62",
}
_ROLE_DERIVED_PERSONALITY_SHA256 = {
    "agent_a": "a4a8566f549a95661f1d043936558ec9e2e7165bd859dfabedb7bd030586c323",
    "agent_b": "06b9e49ab589092bca16e9c93bee35c6222f7eec3dd144fc206314a90a9e2351",
    "agent_c": "2978adfbc475d74927d29699c5828a2ed4bc515fe673362b4ffeb580acaf49f5",
}
_V3_DEFAULT_PERSONALITY_SHA256 = {
    "agent_a": "678d7c48cd652e9237fcfeadd8da20d3595aa708a79deb35cd531263d96e2477",
    "agent_b": "a0df11ad77c5849cfa39cadfc6efe0d4b302cac587fa5e2f60ab13db6327bd17",
    "agent_c": "5f7452ee2a40a9ed432d1cacbd404ff836a9539260d1ea1ac01035acd99f0fa9",
}
_V4_DEFAULT_PERSONALITY_SHA256 = {
    "agent_a": "ebe03e6456df6eb2ccbf4e82bdeedaf756a4075712266ba16b99201400583d11",
    "agent_b": "e52156bc3d24a9e39c2a04458edc15cd7fd71ad3164ef7de1d17fa0959488776",
    "agent_c": "cbea4f0090d33aa22079f9c6692569dac0193bd633e6ed61839f9019020d8706",
}
_V5_DEFAULT_PERSONALITY_SHA256 = {
    "agent_a": "49225250cd1fa14c1bb58e654cf4ede6e55dd7ff969013341552db5ee45a705d",
    "agent_b": "c1449f7edbb9f0e509a10ca4c5f4ff6146f285de242ea7a9fb195c527c810dd1",
    "agent_c": "59a9113aa443a7c0dbda65444c1e61039e79f27652b8be1ac53d9aad57fa3722",
}
_V6_2_DEFAULT_PERSONALITY_SHA256 = {
    "agent_a": "75719cad8fcfe3ea0cbc7c7f6fd903769aad1202732b0fae6f42b818b2616c42",
    "agent_b": "9b136b537a9c8d2dab39fed3f4aef5f68b33c7a3cdca22e9f961c227bd23cdf3",
    "agent_c": "78dda32bf9ffbf27818ea858f1c4395891b5357aa85c6ba11edd15c7ac60935d",
}
_V7_DEFAULT_PERSONALITY_SHA256 = {
    "agent_a": "5462686efba369af926bee543fdb27b53145fce9c02ad581eefca26057acc503",
    "agent_b": "ca4f58aee7040dccdbfecae94088d2ae88e1eb0366b7a20f234f7a27e0039c34",
    "agent_c": "1c19a8d4d39a7d148c29725f55ee0f8239c45503090f2eb77a143c3df88b1afa",
}
_E056_DEFAULT_PERSONALITY_SHA256 = {
    "agent_a": "5b11450825c124cd423bc99ad8ff8cffd94a89eec0309750b5aa3cba392db8d5",
    "agent_b": "9532a31035d3c230d44e709d8e0c3ad4ebc94fc6454bfa3eff3c487500ca4ded",
    "agent_c": "8b689f1894125f106023958d16385c7656287cdfb57b6d3f476406ed164e3993",
}
_INSTITUTIONAL_RELEASE_BINDABLE_ROOM_STATUSES = frozenset(
    {
        RoomStatus.PREPARING,
        RoomStatus.RUNNING,
        RoomStatus.PAUSED,
        RoomStatus.STOPPED,
        RoomStatus.FINISHED,
    }
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[aiosqlite.Connection]:
        db = await aiosqlite.connect(self.path, timeout=30)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA busy_timeout = 30000")
        try:
            yield db
        finally:
            close_task = asyncio.create_task(db.close())
            try:
                await asyncio.shield(close_task)
            except asyncio.CancelledError:
                await close_task
                raise

    async def initialize(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        async with self.connect() as db:
            await db.executescript(
                """
                PRAGMA journal_mode = WAL;

                CREATE TABLE IF NOT EXISTS rooms (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    discussion_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    max_turns INTEGER NOT NULL,
                    max_consecutive_passes INTEGER NOT NULL,
                    inactivity_seconds INTEGER NOT NULL,
                    turn_count INTEGER NOT NULL DEFAULT 0,
                    consecutive_passes INTEGER NOT NULL DEFAULT 0,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                    agent_key TEXT NOT NULL,
                    name TEXT NOT NULL,
                    thread_id TEXT,
                    developer_instructions TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(room_id, agent_key),
                    UNIQUE(thread_id)
                );

                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                    discussion_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    content TEXT NOT NULL,
                    related_event_id TEXT REFERENCES events(id),
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS deliveries (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    runnable INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    queued_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    error TEXT,
                    UNIQUE(event_id, agent_id)
                );

                CREATE INDEX IF NOT EXISTS idx_events_room_time
                    ON events(room_id, created_at, id);
                CREATE INDEX IF NOT EXISTS idx_deliveries_agent_status
                    ON deliveries(agent_id, status, queued_at);

                CREATE TABLE IF NOT EXISTS agent_profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    developer_instructions TEXT NOT NULL,
                    default_slot TEXT UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rounds (
                    id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                    title TEXT,
                    prompt TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    ended_at TEXT,
                    status TEXT NOT NULL,
                    starting_agent TEXT,
                    turn_count INTEGER NOT NULL DEFAULT 0,
                    consecutive_passes INTEGER NOT NULL DEFAULT 0,
                    agent_a_private TEXT,
                    agent_b_private TEXT,
                    task_overlay TEXT,
                    agent_a_overlay TEXT,
                    agent_b_overlay TEXT,
                    close_reason TEXT,
                    last_activity_at TEXT,
                    work_model_version INTEGER NOT NULL DEFAULT 1,
                    required_contributors_json TEXT NOT NULL DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS round_agent_state (
                    round_id TEXT NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
                    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    context_stored_at TEXT NOT NULL,
                    context_consumed_at TEXT,
                    finish_boundary_sequence INTEGER,
                    last_outcome TEXT,
                    PRIMARY KEY(round_id, agent_id)
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                    round_id TEXT NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
                    parent_task_id TEXT REFERENCES tasks(id),
                    origin_event_id TEXT REFERENCES events(id),
                    coordinator_agent_id TEXT NOT NULL REFERENCES agents(id),
                    state TEXT NOT NULL,
                    required_contributors_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    settled_at TEXT,
                    settlement_event_id TEXT REFERENCES events(id),
                    settlement_reason TEXT
                );

                CREATE TABLE IF NOT EXISTS assignment_joins (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    parent_assignment_id TEXT REFERENCES assignments(id),
                    continuation_agent_id TEXT REFERENCES agents(id),
                    state TEXT NOT NULL,
                    released_assignment_id TEXT REFERENCES assignments(id),
                    created_at TEXT NOT NULL,
                    ready_at TEXT,
                    released_at TEXT
                );

                CREATE TABLE IF NOT EXISTS assignments (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    parent_assignment_id TEXT REFERENCES assignments(id),
                    contribution_join_id TEXT REFERENCES assignment_joins(id),
                    origin_event_id TEXT REFERENCES events(id),
                    instruction TEXT NOT NULL,
                    context_event_ids_json TEXT NOT NULL DEFAULT '[]',
                    execution_config_id TEXT,
                    state TEXT NOT NULL,
                    result_event_id TEXT REFERENCES events(id),
                    resolution_reason TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_round_state
                    ON tasks(round_id, state);
                CREATE INDEX IF NOT EXISTS idx_tasks_room_time
                    ON tasks(room_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_assignments_agent_state
                    ON assignments(agent_id, state, created_at);
                CREATE INDEX IF NOT EXISTS idx_assignments_task_state
                    ON assignments(task_id, state);
                CREATE INDEX IF NOT EXISTS idx_assignments_join_state
                    ON assignments(contribution_join_id, state);
                CREATE INDEX IF NOT EXISTS idx_assignment_joins_task_state
                    ON assignment_joins(task_id, state);

                CREATE TABLE IF NOT EXISTS agent_executions (
                    batch_id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    round_id TEXT NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
                    assignment_id TEXT REFERENCES assignments(id),
                    lifecycle_version INTEGER NOT NULL,
                    worker_generation INTEGER NOT NULL,
                    model TEXT,
                    reasoning_effort TEXT,
                    sdk_thread_id TEXT,
                    sdk_turn_id TEXT,
                    state TEXT NOT NULL,
                    result_json TEXT,
                    usage_json TEXT,
                    activity_json TEXT,
                    completion_source TEXT,
                    created_at TEXT NOT NULL,
                    turn_started_at TEXT,
                    result_recorded_at TEXT,
                    decision_recorded_at TEXT,
                    settled_at TEXT,
                    last_reconciled_at TEXT,
                    last_verified_progress_at TEXT,
                    error TEXT,
                    UNIQUE(sdk_thread_id, sdk_turn_id)
                );

                CREATE INDEX IF NOT EXISTS idx_agent_executions_open
                    ON agent_executions(room_id, agent_id, state, created_at);

                CREATE TABLE IF NOT EXISTS assignment_evidence (
                    id TEXT PRIMARY KEY,
                    assignment_id TEXT NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
                    source_batch_id TEXT NOT NULL UNIQUE
                        REFERENCES agent_executions(batch_id) ON DELETE CASCADE,
                    request_json TEXT,
                    durable_request_json TEXT NOT NULL,
                    durable_evidence_json TEXT NOT NULL,
                    transient_payload_json TEXT,
                    strategy TEXT NOT NULL,
                    state TEXT NOT NULL,
                    provenance_event_id TEXT REFERENCES events(id),
                    created_at TEXT NOT NULL,
                    consumed_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_assignment_evidence_pending
                    ON assignment_evidence(assignment_id, state, created_at);

                CREATE TABLE IF NOT EXISTS usage_continuations (
                    id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    thread_id TEXT NOT NULL,
                    source_batch_id TEXT NOT NULL,
                    assignment_id TEXT REFERENCES assignments(id),
                    round_id TEXT NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
                    lifecycle_version INTEGER NOT NULL,
                    worker_generation INTEGER NOT NULL,
                    input_event_ids_json TEXT NOT NULL,
                    triggering_event_ids_json TEXT NOT NULL,
                    reported_retry_at TEXT NOT NULL,
                    wake_at TEXT NOT NULL,
                    state TEXT NOT NULL,
                    continuation_batch_id TEXT,
                    reschedule_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    fired_at TEXT,
                    completed_at TEXT,
                    last_error TEXT,
                    UNIQUE(agent_id)
                );

                CREATE INDEX IF NOT EXISTS idx_usage_continuations_due
                    ON usage_continuations(state, wake_at);
                """
            )
            await self._ensure_column(db, "rooms", "active_round_id", "TEXT")
            await self._ensure_column(db, "rooms", "agent_a_profile_id", "TEXT")
            await self._ensure_column(db, "rooms", "agent_b_profile_id", "TEXT")
            await self._ensure_column(db, "rooms", "agent_a_override", "TEXT")
            await self._ensure_column(db, "rooms", "agent_b_override", "TEXT")
            await self._ensure_column(db, "rooms", "lifecycle_version", "INTEGER NOT NULL DEFAULT 0")
            await self._ensure_column(db, "agents", "profile_id", "TEXT")
            await self._ensure_column(db, "agents", "profile_snapshot", "TEXT")
            await self._ensure_column(db, "agents", "room_override", "TEXT")
            await self._ensure_column(db, "events", "round_id", "TEXT")
            await self._ensure_column(db, "events", "sequence_no", "INTEGER")
            await self._ensure_column(db, "events", "event_class", "TEXT NOT NULL DEFAULT 'mechanical'")
            await self._ensure_column(db, "events", "conversational", "INTEGER NOT NULL DEFAULT 0")
            await self._ensure_column(db, "events", "counts_as_turn", "INTEGER NOT NULL DEFAULT 0")
            await self._ensure_column(db, "events", "counts_toward_pass", "INTEGER NOT NULL DEFAULT 0")
            await self._ensure_column(db, "events", "visibility", "TEXT NOT NULL DEFAULT 'mechanical'")
            await self._ensure_column(db, "events", "agent_readable", "INTEGER NOT NULL DEFAULT 0")
            await self._ensure_column(db, "events", "turn_triggering", "INTEGER NOT NULL DEFAULT 0")
            await self._ensure_column(db, "deliveries", "batch_id", "TEXT")
            await self._ensure_column(db, "deliveries", "consumed_at", "TEXT")
            await self._ensure_column(db, "deliveries", "runnable", "INTEGER NOT NULL DEFAULT 1")
            await self._ensure_column(db, "events", "execution_id", "TEXT")
            await self._ensure_column(
                db, "agent_executions", "last_verified_progress_at", "TEXT"
            )
            await self._ensure_column(db, "agent_executions", "model", "TEXT")
            await self._ensure_column(
                db, "agent_executions", "reasoning_effort", "TEXT"
            )
            await self._ensure_column(db, "rounds", "last_activity_at", "TEXT")
            await self._ensure_column(db, "rounds", "participant_private_json", "TEXT NOT NULL DEFAULT '{}'")
            await self._ensure_column(db, "rounds", "participant_overlays_json", "TEXT NOT NULL DEFAULT '{}'")
            await self._ensure_column(db, "rounds", "work_model_version", "INTEGER NOT NULL DEFAULT 1")
            await self._ensure_column(db, "rounds", "required_contributors_json", "TEXT NOT NULL DEFAULT '[]'")
            await self._ensure_column(db, "round_agent_state", "delivery_start_sequence", "INTEGER NOT NULL DEFAULT 0")
            await self._ensure_column(
                db,
                "agent_executions",
                "assignment_id",
                "TEXT REFERENCES assignments(id)",
            )
            await self._ensure_column(
                db,
                "usage_continuations",
                "assignment_id",
                "TEXT REFERENCES assignments(id)",
            )

            now = utc_now()
            await db.executemany(
                """INSERT OR IGNORE INTO agent_profiles
                   (id, name, developer_instructions, default_slot, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (
                        "profile_default_a",
                        "Agent A default",
                        DEFAULT_PERSONALITY_BY_AGENT["agent_a"],
                        "agent_a",
                        now,
                        now,
                    ),
                    (
                        "profile_default_b",
                        "Agent B default",
                        DEFAULT_PERSONALITY_BY_AGENT["agent_b"],
                        "agent_b",
                        now,
                        now,
                    ),
                    (
                        "profile_default_c",
                        "Agent C default",
                        DEFAULT_PERSONALITY_BY_AGENT["agent_c"],
                        "agent_c",
                        now,
                        now,
                    ),
                ],
            )
            await db.execute("UPDATE events SET round_id=discussion_id WHERE round_id IS NULL")
            await db.execute("UPDATE events SET sequence_no=rowid WHERE sequence_no IS NULL")
            await db.execute(
                """UPDATE events SET
                   event_class=CASE
                     WHEN event_type IN ('observer_message','agent_message','agent_pass','agent_finish','topic') THEN 'conversation'
                     WHEN event_type IN ('agent_activity','tool_activity') THEN 'status'
                     ELSE 'lifecycle' END,
                   conversational=CASE WHEN event_type IN
                     ('observer_message','agent_message','agent_pass','agent_finish','topic') THEN 1 ELSE 0 END,
                   counts_as_turn=CASE WHEN event_type IN
                     ('agent_message','agent_pass','agent_finish') THEN 1 ELSE 0 END,
                   counts_toward_pass=CASE WHEN event_type='agent_pass' THEN 1 ELSE 0 END,
                   visibility=CASE
                     WHEN event_type='observer_message' AND destination NOT IN ('both','all') THEN 'private'
                     WHEN source='room' THEN 'mechanical' ELSE 'public' END,
                   agent_readable=CASE WHEN event_type IN
                     ('observer_message','agent_message','topic') THEN 1 ELSE 0 END,
                   turn_triggering=CASE WHEN event_type IN
                     ('observer_message','agent_message','topic') THEN 1 ELSE 0 END
                   WHERE event_class='mechanical'"""
            )
            await db.execute(
                """UPDATE deliveries SET consumed_at=completed_at
                   WHERE status='delivered' AND consumed_at IS NULL"""
            )
            legacy_rooms = await db.execute_fetchall("SELECT * FROM rooms")
            for room in legacy_rooms:
                round_id = room["active_round_id"] or room["discussion_id"]
                round_status = self._round_status_for_room(room["status"])
                started_at = room["created_at"] if round_status != RoundStatus.PREPARING else None
                ended_at = room["updated_at"] if round_status in {
                    RoundStatus.FINISHED,
                    RoundStatus.STOPPED,
                } else None
                await db.execute(
                    """INSERT OR IGNORE INTO rounds
                       (id, room_id, title, prompt, created_at, started_at, ended_at,
                        status, starting_agent, turn_count, consecutive_passes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'either', ?, ?)""",
                    (
                        round_id,
                        room["id"],
                        "Migrated initial round",
                        room["topic"],
                        room["created_at"],
                        started_at,
                        ended_at,
                        round_status,
                        room["turn_count"],
                        room["consecutive_passes"],
                    ),
                )
                await db.execute(
                    "UPDATE rooms SET active_round_id=? WHERE id=? AND active_round_id IS NULL",
                    (round_id, room["id"]),
                )
                agents = await db.execute_fetchall(
                    "SELECT * FROM agents WHERE room_id=?", (room["id"],)
                )
                for agent in agents:
                    snapshot = agent["profile_snapshot"] or agent["developer_instructions"]
                    await db.execute(
                        """UPDATE agents SET profile_snapshot=?
                           WHERE id=? AND profile_snapshot IS NULL""",
                        (snapshot, agent["id"]),
                    )
                    await db.execute(
                        """INSERT OR IGNORE INTO round_agent_state
                           (round_id, agent_id, context_stored_at, context_consumed_at)
                           VALUES (?, ?, ?, ?)""",
                        (round_id, agent["id"], room["created_at"], room["created_at"]),
                    )
            await self._migrate_known_pair_profiles(db, now)
            await self._migrate_known_early_triad_profiles(db, now)
            await self._migrate_builtin_profiles_to_personality_layers(db, now)
            await db.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS idx_events_room_sequence
                   ON events(room_id, sequence_no)"""
            )
            await db.execute(
                """CREATE INDEX IF NOT EXISTS idx_rounds_room_created
                   ON rounds(room_id, created_at)"""
            )
            await db.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS idx_events_execution_result
                   ON events(execution_id) WHERE execution_id IS NOT NULL"""
            )
            await db.commit()

    async def _migrate_known_pair_profiles(
        self, db: aiosqlite.Connection, now: str
    ) -> None:
        """Replace only the known stale pair defaults and matching live snapshots.

        Existing custom profiles, Room overrides, and archived predecessor snapshots
        are deliberately outside this one-time migration.
        """
        defaults = await db.execute_fetchall(
            """SELECT id, default_slot, developer_instructions FROM agent_profiles
               WHERE default_slot IN ('agent_a', 'agent_b')"""
        )
        for row in defaults:
            slot = row["default_slot"]
            digest = hashlib.sha256(row["developer_instructions"].encode("utf-8")).hexdigest()
            if digest == _LEGACY_PAIR_PROFILE_SHA256[slot]:
                await db.execute(
                    """UPDATE agent_profiles SET developer_instructions=?, updated_at=?
                       WHERE id=? AND developer_instructions=?""",
                    (_TRIAD_PROFILE_TEXT[slot], now, row["id"], row["developer_instructions"]),
                )

        candidates = await db.execute_fetchall(
            """SELECT a.id, a.room_id, a.agent_key, a.profile_id, a.profile_snapshot,
                      a.developer_instructions, a.room_override, r.status, r.metadata_json
               FROM agents a JOIN rooms r ON r.id=a.room_id
               WHERE a.agent_key IN ('agent_a', 'agent_b') AND r.status != ?""",
            (RoomStatus.ARCHIVED,),
        )
        changed_rooms: dict[str, tuple[dict[str, Any], set[str]]] = {}
        for row in candidates:
            slot = row["agent_key"]
            snapshot = row["profile_snapshot"] or ""
            effective = row["developer_instructions"] or ""
            room_metadata = json.loads(row["metadata_json"] or "{}")
            if (
                room_metadata.get("sealed") is True
                or row["profile_id"] != f"profile_default_{slot[-1]}"
                or row["room_override"] is not None
                or hashlib.sha256(snapshot.encode("utf-8")).hexdigest()
                != _LEGACY_PAIR_PROFILE_SHA256[slot]
                or hashlib.sha256(effective.encode("utf-8")).hexdigest()
                != _LEGACY_PAIR_PROFILE_SHA256[slot]
            ):
                continue
            replacement = _TRIAD_PROFILE_TEXT[slot]
            cursor = await db.execute(
                """UPDATE agents SET profile_snapshot=?, developer_instructions=?, updated_at=?
                   WHERE id=? AND profile_snapshot=? AND developer_instructions=?
                         AND room_override IS NULL""",
                (replacement, replacement, now, row["id"], snapshot, effective),
            )
            if cursor.rowcount == 1:
                _, changed_agents = changed_rooms.setdefault(
                    row["room_id"], (room_metadata, set())
                )
                changed_agents.add(slot)

        for room_id, (metadata, changed_agents) in changed_rooms.items():
            migrations = metadata.setdefault("profile_migrations", [])
            if not any(item.get("id") == _TRIAD_PROFILE_MIGRATION_ID for item in migrations):
                migrations.append(
                    {
                        "id": _TRIAD_PROFILE_MIGRATION_ID,
                        "applied_at": now,
                        "agents": sorted(changed_agents),
                        "previous_sha256": {
                            slot: _LEGACY_PAIR_PROFILE_SHA256[slot]
                            for slot in sorted(changed_agents)
                        },
                        "replacement_sha256": {
                            slot: hashlib.sha256(text.encode("utf-8")).hexdigest()
                            for slot, text in _TRIAD_PROFILE_TEXT.items()
                            if slot in changed_agents
                        },
                    }
                )
                await db.execute(
                    "UPDATE rooms SET metadata_json=?, updated_at=? WHERE id=?",
                    (json.dumps(metadata, ensure_ascii=False), now, room_id),
                )

    async def _migrate_known_early_triad_profiles(
        self, db: aiosqlite.Connection, now: str
    ) -> None:
        """Replace the exact observed early-triad built-ins with current profiles.

        This migration is deliberately hash-gated. Custom defaults, Room overrides,
        archived Rooms, and sealed predecessor snapshots are not modified.
        """
        defaults = await db.execute_fetchall(
            """SELECT id, default_slot, developer_instructions FROM agent_profiles
               WHERE default_slot IN ('agent_a', 'agent_b', 'agent_c')"""
        )
        for row in defaults:
            slot = row["default_slot"]
            digest = hashlib.sha256(row["developer_instructions"].encode("utf-8")).hexdigest()
            if digest == _EARLY_TRIAD_PROFILE_SHA256[slot]:
                await db.execute(
                    """UPDATE agent_profiles SET developer_instructions=?, updated_at=?
                       WHERE id=? AND developer_instructions=?""",
                    (_TRIAD_PROFILE_TEXT[slot], now, row["id"], row["developer_instructions"]),
                )

        candidates = await db.execute_fetchall(
            """SELECT a.id, a.room_id, a.agent_key, a.profile_id, a.profile_snapshot,
                      a.developer_instructions, a.room_override, r.status, r.metadata_json
               FROM agents a JOIN rooms r ON r.id=a.room_id
               WHERE a.agent_key IN ('agent_a', 'agent_b', 'agent_c') AND r.status != ?""",
            (RoomStatus.ARCHIVED,),
        )
        changed_rooms: dict[str, tuple[dict[str, Any], set[str]]] = {}
        for row in candidates:
            slot = row["agent_key"]
            snapshot = row["profile_snapshot"] or ""
            effective = row["developer_instructions"] or ""
            room_metadata = json.loads(row["metadata_json"] or "{}")
            stale_sha256 = _EARLY_TRIAD_PROFILE_SHA256[slot]
            if (
                room_metadata.get("sealed") is True
                or row["profile_id"] != f"profile_default_{slot[-1]}"
                or row["room_override"] is not None
                or hashlib.sha256(snapshot.encode("utf-8")).hexdigest() != stale_sha256
                or hashlib.sha256(effective.encode("utf-8")).hexdigest() != stale_sha256
            ):
                continue
            replacement = _TRIAD_PROFILE_TEXT[slot]
            cursor = await db.execute(
                """UPDATE agents SET profile_snapshot=?, developer_instructions=?, updated_at=?
                   WHERE id=? AND profile_snapshot=? AND developer_instructions=?
                         AND room_override IS NULL""",
                (replacement, replacement, now, row["id"], snapshot, effective),
            )
            if cursor.rowcount == 1:
                _, changed_agents = changed_rooms.setdefault(
                    row["room_id"], (room_metadata, set())
                )
                changed_agents.add(slot)

        for room_id, (metadata, changed_agents) in changed_rooms.items():
            migrations = metadata.setdefault("profile_migrations", [])
            if not any(
                item.get("id") == _EARLY_TRIAD_PROFILE_MIGRATION_ID
                for item in migrations
            ):
                migrations.append(
                    {
                        "id": _EARLY_TRIAD_PROFILE_MIGRATION_ID,
                        "applied_at": now,
                        "agents": sorted(changed_agents),
                        "previous_sha256": {
                            slot: _EARLY_TRIAD_PROFILE_SHA256[slot]
                            for slot in sorted(changed_agents)
                        },
                        "replacement_sha256": {
                            slot: hashlib.sha256(
                                _TRIAD_PROFILE_TEXT[slot].encode("utf-8")
                            ).hexdigest()
                            for slot in sorted(changed_agents)
                        },
                    }
                )
                await db.execute(
                    "UPDATE rooms SET metadata_json=?, updated_at=? WHERE id=?",
                    (json.dumps(metadata, ensure_ascii=False), now, room_id),
                )

    async def recover_interrupted_work(self) -> None:
        """Preserve in-flight claims for exact-turn reconciliation after restart."""
        async with self.connect() as db:
            await db.execute(
                """UPDATE agent_executions
                   SET state='recovering', last_reconciled_at=NULL
                   WHERE state IN ('active', 'recovering')"""
            )
            await db.execute(
                """UPDATE agent_executions
                   SET state='quarantined',
                       error='Process exited before the exact Codex turn identity was persisted'
                   WHERE state='claimed'"""
            )
            await db.commit()

    async def _migrate_builtin_profiles_to_personality_layers(
        self, db: aiosqlite.Connection, now: str
    ) -> None:
        """Convert exact built-in defaults to the current optional profile bodies.

        Existing Room snapshots and any non-matching custom default profile text are
        deliberately preserved. New Rooms compose protected institutional, structural,
        and protocol layers around the selected optional profile body. The standard
        default body is intentionally empty.
        """
        defaults = await db.execute_fetchall(
            """SELECT id, name, default_slot, developer_instructions FROM agent_profiles
               WHERE default_slot IN ('agent_a', 'agent_b', 'agent_c')"""
        )
        for row in defaults:
            slot = row["default_slot"]
            text = row["developer_instructions"]
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if (
                digest == _PRE_PERSONALITY_LAYER_PROFILE_SHA256[slot]
                or digest == _ROLE_DERIVED_PERSONALITY_SHA256[slot]
                or digest == _V3_DEFAULT_PERSONALITY_SHA256[slot]
                or digest == _V4_DEFAULT_PERSONALITY_SHA256[slot]
                or digest == _V5_DEFAULT_PERSONALITY_SHA256[slot]
                or digest == _V6_2_DEFAULT_PERSONALITY_SHA256[slot]
                or digest == _V7_DEFAULT_PERSONALITY_SHA256[slot]
                or digest == _E056_DEFAULT_PERSONALITY_SHA256[slot]
                or text == _TRIAD_PROFILE_TEXT[slot]
            ):
                profile_name = row["name"]
                if (
                    slot == "agent_c"
                    and profile_name == "Agent C · The Integrator"
                ):
                    profile_name = "Agent C default"
                await db.execute(
                    """UPDATE agent_profiles
                       SET name=?, developer_instructions=?, updated_at=?
                       WHERE id=? AND developer_instructions=?""",
                    (
                        profile_name,
                        DEFAULT_PERSONALITY_BY_AGENT[slot],
                        now,
                        row["id"],
                        text,
                    ),
                )

    async def create_room(self, request: CreateRoomRequest) -> str:
        room_id = new_id("room")
        round_id = new_id("round")
        now = utc_now()
        a_id = f"{room_id}:agent_a"
        b_id = f"{room_id}:agent_b"
        c_id = f"{room_id}:agent_c"
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            profile_a = await self._fetchone(
                db, "SELECT * FROM agent_profiles WHERE default_slot='agent_a'", ()
            )
            profile_b = await self._fetchone(
                db, "SELECT * FROM agent_profiles WHERE default_slot='agent_b'", ()
            )
            profile_c = await self._fetchone(
                db, "SELECT * FROM agent_profiles WHERE default_slot='agent_c'", ()
            )
            if profile_a is None or profile_b is None or profile_c is None:
                raise RuntimeError("Default agent profiles are missing")
            a_profile_text = profile_a["developer_instructions"]
            b_profile_text = profile_b["developer_instructions"]
            c_profile_text = profile_c["developer_instructions"]
            a_instructions = self._effective_instructions(
                "agent_a", request.agent_a_name, a_profile_text, request.agent_a_instructions
            )
            b_instructions = self._effective_instructions(
                "agent_b", request.agent_b_name, b_profile_text, request.agent_b_instructions
            )
            c_instructions = self._effective_instructions(
                "agent_c", "Agent C", c_profile_text, request.agent_c_instructions
            )
            await db.execute(
                """INSERT INTO rooms
                (id, title, status, topic, discussion_id, created_at, updated_at,
                 max_turns, max_consecutive_passes, inactivity_seconds, metadata_json,
                 active_round_id, agent_a_profile_id, agent_b_profile_id,
                 agent_a_override, agent_b_override)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    room_id,
                    request.title,
                    RoomStatus.CREATING,
                    request.topic,
                    round_id,
                    now,
                    now,
                    request.max_turns,
                    request.max_consecutive_passes,
                    request.inactivity_seconds,
                    json.dumps({"schema_version": 2, "created_by": "local_observer"}),
                    round_id,
                    profile_a["id"],
                    profile_b["id"],
                    request.agent_a_instructions,
                    request.agent_b_instructions,
                ),
            )
            agent_rows = [
                (
                    a_id,
                    room_id,
                    "agent_a",
                    request.agent_a_name,
                    a_instructions,
                    AgentStatus.INITIALIZING,
                    now,
                    now,
                    profile_a["id"],
                    a_profile_text,
                    request.agent_a_instructions,
                ),
                (
                    b_id,
                    room_id,
                    "agent_b",
                    request.agent_b_name,
                    b_instructions,
                    AgentStatus.INITIALIZING,
                    now,
                    now,
                    profile_b["id"],
                    b_profile_text,
                    request.agent_b_instructions,
                ),
                (
                    c_id,
                    room_id,
                    "agent_c",
                    "Agent C",
                    c_instructions,
                    AgentStatus.INITIALIZING,
                    now,
                    now,
                    profile_c["id"],
                    c_profile_text,
                    request.agent_c_instructions,
                ),
            ]
            await db.executemany(
                """INSERT INTO agents
                (id, room_id, agent_key, name, thread_id, developer_instructions,
                 status, created_at, updated_at, profile_id, profile_snapshot, room_override)
                VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)""",
                agent_rows,
            )
            await db.execute(
                """INSERT INTO rounds
                   (id, room_id, title, prompt, created_at, status, starting_agent,
                    work_model_version, required_contributors_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    round_id,
                    room_id,
                    "Opening round",
                    request.topic,
                    now,
                    RoundStatus.PREPARING,
                    request.starting_agent,
                    request.work_model_version,
                    json.dumps(request.required_contributors),
                ),
            )
            await db.executemany(
                """INSERT INTO round_agent_state
                   (round_id, agent_id, context_stored_at)
                   VALUES (?, ?, ?)""",
                [(round_id, row[0], now) for row in agent_rows],
            )
            await db.commit()
        return room_id

    async def reserve_rollover(
        self,
        source_room_id: str,
        request: RolloverRoomRequest,
        institutional_release: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Freeze a quiescent predecessor and create one unroutable staged successor."""
        operation_id = new_id("rollover")
        successor_id = new_id("room")
        round_id = new_id("round")
        now = utc_now()
        checkpoint_hash = hashlib.sha256(request.checkpoint.encode("utf-8")).hexdigest()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            source = await self._fetchone(db, "SELECT * FROM rooms WHERE id=?", (source_room_id,))
            if source is None:
                raise KeyError(source_room_id)
            source_metadata = json.loads(source["metadata_json"] or "{}")
            committed = source_metadata.get("rollover_successor")
            if committed:
                if committed.get("checkpoint_sha256") == checkpoint_hash:
                    if committed.get("institutional_release") != institutional_release:
                        await db.rollback()
                        raise ValueError(
                            "This Room has already rolled over with another institutional release"
                        )
                    await db.rollback()
                    return {
                        "operation_id": committed["operation_id"],
                        "source_room_id": source_room_id,
                        "successor_room_id": committed["room_id"],
                        "checkpoint_sha256": checkpoint_hash,
                        "already_committed": True,
                    }
                await db.rollback()
                raise ValueError("This Room has already rolled over with another checkpoint")
            if source["status"] != RoomStatus.FINISHED:
                raise ValueError("Only a naturally finished Room can roll over")
            active_round = await self._fetchone(
                db, "SELECT status FROM rounds WHERE id=?", (source["active_round_id"],)
            )
            if active_round is None or active_round["status"] != RoundStatus.FINISHED:
                raise ValueError("Room rollover requires a naturally finished active round")
            open_deliveries = await self._fetchone(
                db,
                """SELECT COUNT(*) AS count FROM deliveries d
                   JOIN events e ON e.id=d.event_id
                   WHERE e.room_id=? AND d.status IN ('pending','processing')""",
                (source_room_id,),
            )
            open_executions = await self._fetchone(
                db,
                """SELECT COUNT(*) AS count FROM agent_executions
                   WHERE room_id=? AND state IN
                   ('claimed','active','recovering','result_ready','quarantined')""",
                (source_room_id,),
            )
            if (open_deliveries and open_deliveries["count"]) or (
                open_executions and open_executions["count"]
            ):
                raise ValueError("Room rollover requires fully quiescent delivery and execution state")
            agents = await db.execute_fetchall(
                "SELECT * FROM agents WHERE room_id=? ORDER BY agent_key", (source_room_id,)
            )
            if not agents or any(not agent["thread_id"] for agent in agents):
                raise ValueError("Every predecessor participant must have a persistent thread")
            predecessor_has_c = any(agent["agent_key"] == "agent_c" for agent in agents)
            profile_c = None
            if not predecessor_has_c:
                profile_c = await self._fetchone(
                    db, "SELECT * FROM agent_profiles WHERE default_slot='agent_c'", ()
                )
                if profile_c is None:
                    raise RuntimeError("Agent C default profile is missing")

            active = {
                "operation_id": operation_id,
                "successor_room_id": successor_id,
                "checkpoint_sha256": checkpoint_hash,
                "checkpoint_character_count": len(request.checkpoint),
                "provisioned_threads": {},
                "started_at": now,
            }
            if institutional_release is not None:
                active["institutional_release"] = institutional_release
            source_metadata["rollover_pending"] = active
            cursor = await db.execute(
                """UPDATE rooms SET status=?, metadata_json=?, updated_at=?
                   WHERE id=? AND status=?""",
                (
                    RoomStatus.ROLLING_OVER,
                    json.dumps(source_metadata, ensure_ascii=False),
                    now,
                    source_room_id,
                    RoomStatus.FINISHED,
                ),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                raise ValueError("Room rollover reservation lost its state comparison")

            successor_metadata = {
                "schema_version": 2,
                "created_by": "room_rollover",
                "rollover_state": "staging",
                "lineage": {
                    "operation_id": operation_id,
                    "predecessor_room_id": source_room_id,
                    "checkpoint_sha256": checkpoint_hash,
                    "checkpoint_character_count": len(request.checkpoint),
                    "participants": {
                        agent["agent_key"]: agent["id"] for agent in agents
                    },
                },
            }
            if not predecessor_has_c:
                successor_metadata["lineage"]["successor_added_participants"] = ["agent_c"]
            if institutional_release is not None:
                successor_metadata["institutional_release"] = institutional_release
                successor_metadata["lineage"]["institutional_release"] = institutional_release
            await db.execute(
                """INSERT INTO rooms
                   (id, title, status, topic, discussion_id, created_at, updated_at,
                    max_turns, max_consecutive_passes, inactivity_seconds, metadata_json,
                    active_round_id, agent_a_profile_id, agent_b_profile_id,
                    agent_a_override, agent_b_override)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    successor_id,
                    request.title or f"{source['title']} (continued)"[:120],
                    RoomStatus.CREATING,
                    request.checkpoint,
                    round_id,
                    now,
                    now,
                    source["max_turns"],
                    source["max_consecutive_passes"],
                    source["inactivity_seconds"],
                    json.dumps(successor_metadata, ensure_ascii=False),
                    round_id,
                    source["agent_a_profile_id"],
                    source["agent_b_profile_id"],
                    source["agent_a_override"],
                    source["agent_b_override"],
                ),
            )
            successor_agents: list[tuple[Any, ...]] = []
            for agent in agents:
                successor_agents.append(
                    (
                        f"{successor_id}:{agent['agent_key']}",
                        successor_id,
                        agent["agent_key"],
                        agent["name"],
                        agent["developer_instructions"],
                        AgentStatus.INITIALIZING,
                        now,
                        now,
                        agent["profile_id"],
                        agent["profile_snapshot"],
                        agent["room_override"],
                    )
                )
            if not predecessor_has_c:
                assert profile_c is not None
                successor_agents.append(
                    (
                        f"{successor_id}:agent_c",
                        successor_id,
                        "agent_c",
                        "Agent C",
                        self._effective_instructions(
                            "agent_c", "Agent C", profile_c["developer_instructions"], None
                        ),
                        AgentStatus.INITIALIZING,
                        now,
                        now,
                        profile_c["id"],
                        profile_c["developer_instructions"],
                        None,
                    )
                )
                successor_agents.sort(key=lambda row: row[2])
            await db.executemany(
                """INSERT INTO agents
                   (id, room_id, agent_key, name, thread_id, developer_instructions,
                    status, created_at, updated_at, profile_id, profile_snapshot, room_override)
                   VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)""",
                successor_agents,
            )
            await db.execute(
                """INSERT INTO rounds
                   (id, room_id, title, prompt, created_at, status, starting_agent,
                    participant_private_json, participant_overlays_json)
                   VALUES (?, ?, ?, ?, ?, ?, 'agent_c', '{}', '{}')""",
                (round_id, successor_id, "Inherited checkpoint", request.checkpoint, now, RoundStatus.PREPARING),
            )
            await db.executemany(
                """INSERT INTO round_agent_state (round_id, agent_id, context_stored_at)
                   VALUES (?, ?, ?)""",
                [(round_id, row[0], now) for row in successor_agents],
            )
            await db.commit()
        return {
            "operation_id": operation_id,
            "source_room_id": source_room_id,
            "successor_room_id": successor_id,
            "checkpoint_sha256": checkpoint_hash,
            "already_committed": False,
        }

    async def record_rollover_thread(
        self,
        source_room_id: str,
        operation_id: str,
        successor_room_id: str,
        agent_key: str,
        thread_id: str,
    ) -> None:
        """Bind one externally provisioned thread to the reserved successor."""
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            source = await self._fetchone(db, "SELECT * FROM rooms WHERE id=?", (source_room_id,))
            if source is None:
                raise KeyError(source_room_id)
            metadata = json.loads(source["metadata_json"] or "{}")
            pending = metadata.get("rollover_pending") or {}
            if (
                source["status"] != RoomStatus.ROLLING_OVER
                or pending.get("operation_id") != operation_id
                or pending.get("successor_room_id") != successor_room_id
            ):
                raise ValueError("Rollover reservation is no longer current")
            predecessor_ids = {
                row["thread_id"]
                for row in await db.execute_fetchall(
                    "SELECT thread_id FROM agents WHERE room_id=? AND thread_id IS NOT NULL",
                    (source_room_id,),
                )
            }
            successor_ids = {
                row["thread_id"]
                for row in await db.execute_fetchall(
                    "SELECT thread_id FROM agents WHERE room_id=? AND thread_id IS NOT NULL",
                    (successor_room_id,),
                )
            }
            if thread_id in predecessor_ids or thread_id in successor_ids:
                await db.rollback()
                raise ValueError("Rollover thread ID must be fresh and unique")
            cursor = await db.execute(
                """UPDATE agents SET thread_id=?, status=?, updated_at=?
                   WHERE room_id=? AND agent_key=? AND thread_id IS NULL""",
                (thread_id, AgentStatus.IDLE, utc_now(), successor_room_id, agent_key),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                raise ValueError(f"Rollover participant {agent_key} was already provisioned")
            pending.setdefault("provisioned_threads", {})[agent_key] = thread_id
            metadata["rollover_pending"] = pending
            await db.execute(
                "UPDATE rooms SET metadata_json=?, updated_at=? WHERE id=?",
                (json.dumps(metadata, ensure_ascii=False), utc_now(), source_room_id),
            )
            await db.commit()

    async def finalize_rollover(
        self, source_room_id: str, operation_id: str, successor_room_id: str
    ) -> dict[str, Any]:
        """Atomically link/seal the predecessor and expose a fully provisioned successor."""
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            source = await self._fetchone(db, "SELECT * FROM rooms WHERE id=?", (source_room_id,))
            successor = await self._fetchone(db, "SELECT * FROM rooms WHERE id=?", (successor_room_id,))
            if source is None or successor is None:
                raise ValueError("Rollover source or staged successor is missing")
            source_metadata = json.loads(source["metadata_json"] or "{}")
            pending = source_metadata.get("rollover_pending") or {}
            if (
                source["status"] != RoomStatus.ROLLING_OVER
                or pending.get("operation_id") != operation_id
                or pending.get("successor_room_id") != successor_room_id
                or successor["status"] != RoomStatus.CREATING
            ):
                raise ValueError("Rollover finalization no longer matches its reservation")
            open_deliveries = await self._fetchone(
                db,
                """SELECT COUNT(*) AS count FROM deliveries d JOIN events e ON e.id=d.event_id
                   WHERE e.room_id=? AND d.status IN ('pending','processing')""",
                (source_room_id,),
            )
            active_round = await self._fetchone(
                db, "SELECT status FROM rounds WHERE id=?", (source["active_round_id"],)
            )
            open_executions = await self._fetchone(
                db,
                """SELECT COUNT(*) AS count FROM agent_executions WHERE room_id=? AND state IN
                   ('claimed','active','recovering','result_ready','quarantined')""",
                (source_room_id,),
            )
            agents = await db.execute_fetchall(
                "SELECT agent_key, thread_id FROM agents WHERE room_id=? ORDER BY agent_key",
                (successor_room_id,),
            )
            predecessor_ids = {
                row["thread_id"]
                for row in await db.execute_fetchall(
                    "SELECT thread_id FROM agents WHERE room_id=? AND thread_id IS NOT NULL",
                    (source_room_id,),
                )
            }
            ids = [agent["thread_id"] for agent in agents]
            if (
                (open_deliveries and open_deliveries["count"])
                or (open_executions and open_executions["count"])
                or active_round is None
                or active_round["status"] != RoundStatus.FINISHED
                or not agents
                or any(not item for item in ids)
                or len(set(ids)) != len(ids)
                or not set(ids).isdisjoint(predecessor_ids)
            ):
                raise ValueError("Rollover cannot finalize without quiescence and unique fresh threads")
            history = source_metadata.setdefault("rollover_history", [])
            history.append({**pending, "state": "committed", "completed_at": now})
            source_metadata.pop("rollover_pending", None)
            source_metadata["rollover_successor"] = {
                "operation_id": operation_id,
                "room_id": successor_room_id,
                "checkpoint_sha256": pending["checkpoint_sha256"],
                "checkpoint_character_count": pending["checkpoint_character_count"],
            }
            if pending.get("institutional_release") is not None:
                source_metadata["rollover_successor"]["institutional_release"] = pending[
                    "institutional_release"
                ]
            source_metadata["sealed"] = True
            successor_metadata = json.loads(successor["metadata_json"] or "{}")
            successor_metadata["rollover_state"] = "ready"
            await db.execute(
                "UPDATE rooms SET status=?, metadata_json=?, updated_at=? WHERE id=?",
                (RoomStatus.ARCHIVED, json.dumps(source_metadata, ensure_ascii=False), now, source_room_id),
            )
            await db.execute(
                "UPDATE rooms SET status=?, metadata_json=?, updated_at=? WHERE id=?",
                (RoomStatus.PREPARING, json.dumps(successor_metadata, ensure_ascii=False), now, successor_room_id),
            )
            await db.commit()
        room = await self.get_room(successor_room_id)
        assert room is not None
        return room

    async def abort_rollover(
        self,
        source_room_id: str,
        operation_id: str,
        successor_room_id: str,
        error: str,
        extra_orphaned_thread_ids: Iterable[str] = (),
        suspicious_thread_ids: Iterable[str] = (),
    ) -> list[str]:
        """Restore the predecessor and retain an audit of provisioned orphan threads."""
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            source = await self._fetchone(db, "SELECT * FROM rooms WHERE id=?", (source_room_id,))
            if source is None:
                raise KeyError(source_room_id)
            metadata = json.loads(source["metadata_json"] or "{}")
            pending = metadata.get("rollover_pending") or {}
            if pending.get("operation_id") != operation_id:
                await db.rollback()
                return []
            rows = await db.execute_fetchall(
                "SELECT thread_id FROM agents WHERE room_id=? AND thread_id IS NOT NULL",
                (successor_room_id,),
            )
            predecessor_ids = {
                row["thread_id"]
                for row in await db.execute_fetchall(
                    "SELECT thread_id FROM agents WHERE room_id=? AND thread_id IS NOT NULL",
                    (source_room_id,),
                )
            }
            candidates = list(
                dict.fromkeys([row["thread_id"] for row in rows] + list(extra_orphaned_thread_ids))
            )
            suspicious = list(
                dict.fromkeys(
                    list(suspicious_thread_ids)
                    + [thread_id for thread_id in candidates if thread_id in predecessor_ids]
                )
            )
            orphaned = [
                thread_id for thread_id in candidates if thread_id not in predecessor_ids
            ]
            metadata.setdefault("rollover_history", []).append(
                {
                    **pending,
                    "state": "aborted",
                    "completed_at": now,
                    "error": error[:1000],
                    "orphaned_thread_ids": orphaned,
                    "suspicious_thread_ids": suspicious,
                }
            )
            metadata.pop("rollover_pending", None)
            await db.execute("DELETE FROM rooms WHERE id=?", (successor_room_id,))
            await db.execute(
                "UPDATE rooms SET status=?, metadata_json=?, updated_at=? WHERE id=?",
                (RoomStatus.FINISHED, json.dumps(metadata, ensure_ascii=False), now, source_room_id),
            )
            await db.commit()
        return orphaned

    async def get_pending_rollovers(self) -> list[dict[str, Any]]:
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                "SELECT * FROM rooms WHERE status=?", (RoomStatus.ROLLING_OVER,)
            )
        result: list[dict[str, Any]] = []
        for row in rows:
            source = self._decode_row(row)
            pending = source.get("metadata", {}).get("rollover_pending")
            if pending:
                result.append({"source": source, **pending})
        return result

    async def get_committed_rollovers(self) -> list[dict[str, Any]]:
        """Return committed lineage records so missing audit events can be repaired idempotently."""
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                "SELECT * FROM rooms WHERE status=?", (RoomStatus.ARCHIVED,)
            )
        result: list[dict[str, Any]] = []
        for row in rows:
            source = self._decode_row(row)
            committed = source.get("metadata", {}).get("rollover_successor")
            if committed:
                result.append({"source": source, **committed})
        return result

    async def list_rooms(self, include_archived: bool = False) -> list[dict[str, Any]]:
        where = "" if include_archived else "WHERE status != 'archived'"
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                f"SELECT * FROM rooms {where} ORDER BY updated_at DESC"  # noqa: S608
            )
        decoded = [self._decode_row(row) for row in rows]
        return [
            room
            for room in decoded
            if room.get("metadata", {}).get("rollover_state") != "staging"
        ]

    async def get_room(self, room_id: str) -> dict[str, Any] | None:
        async with self.connect() as db:
            row = await self._fetchone(db, "SELECT * FROM rooms WHERE id=?", (room_id,))
        return self._decode_row(row) if row else None

    async def get_agents(self, room_id: str) -> list[dict[str, Any]]:
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                "SELECT * FROM agents WHERE room_id=? ORDER BY agent_key", (room_id,)
            )
        return [self._decode_row(row) for row in rows]

    async def get_agent(self, room_id: str, agent_key: str) -> dict[str, Any] | None:
        async with self.connect() as db:
            row = await self._fetchone(
                db,
                "SELECT * FROM agents WHERE room_id=? AND agent_key=?",
                (room_id, agent_key),
            )
        return self._decode_row(row) if row else None

    async def set_agent_thread(self, agent_id: str, thread_id: str) -> None:
        now = utc_now()
        async with self.connect() as db:
            await db.execute(
                "UPDATE agents SET thread_id=?, status=?, last_error=NULL, updated_at=? WHERE id=?",
                (thread_id, AgentStatus.IDLE, now, agent_id),
            )
            await db.commit()

    async def reserve_agent_c(self, room_id: str) -> dict[str, Any]:
        """Add C without delivering any pre-join event or round initialization."""
        now = utc_now()
        agent_id = f"{room_id}:agent_c"
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            room = await self._fetchone(db, "SELECT * FROM rooms WHERE id=?", (room_id,))
            if room is None:
                raise KeyError(room_id)
            if room["status"] in {
                RoomStatus.ARCHIVED,
                RoomStatus.CREATING,
                RoomStatus.ROLLING_OVER,
                RoomStatus.ERROR,
            }:
                raise ValueError(f"Cannot add an agent while room is {room['status']}")
            existing = await self._fetchone(
                db, "SELECT 1 FROM agents WHERE room_id=? AND agent_key='agent_c'", (room_id,)
            )
            if existing is not None:
                raise ValueError("Agent C is already a participant")
            profile = await self._fetchone(
                db, "SELECT * FROM agent_profiles WHERE default_slot='agent_c'", ()
            )
            if profile is None:
                raise RuntimeError("Agent C default profile is missing")
            maximum = await self._fetchone(
                db, "SELECT COALESCE(MAX(sequence_no), 0) AS value FROM events WHERE room_id=?",
                (room_id,),
            )
            watermark = maximum["value"] if maximum else 0
            await db.execute(
                """INSERT INTO agents
                   (id, room_id, agent_key, name, thread_id, developer_instructions,
                    status, created_at, updated_at, profile_id, profile_snapshot, room_override)
                   VALUES (?, ?, 'agent_c', 'Agent C', NULL, ?, ?, ?, ?, ?, ?, NULL)""",
                (
                    agent_id,
                    room_id,
                    self._effective_instructions(
                        "agent_c", "Agent C", profile["developer_instructions"], None
                    ),
                    AgentStatus.INITIALIZING,
                    now,
                    now,
                    profile["id"],
                    profile["developer_instructions"],
                ),
            )
            await db.execute(
                """INSERT INTO round_agent_state
                   (round_id, agent_id, context_stored_at, context_consumed_at,
                    delivery_start_sequence)
                   VALUES (?, ?, ?, ?, ?)""",
                (room["active_round_id"], agent_id, now, now, watermark),
            )
            await db.commit()
        agent = await self.get_agent(room_id, "agent_c")
        assert agent is not None
        return agent

    async def remove_agent(self, room_id: str, agent_key: str) -> None:
        async with self.connect() as db:
            await db.execute("DELETE FROM agents WHERE room_id=? AND agent_key=?", (room_id, agent_key))
            await db.commit()

    async def set_agent_status(
        self, agent_id: str, status: AgentStatus | str, error: str | None = None
    ) -> None:
        async with self.connect() as db:
            await db.execute(
                "UPDATE agents SET status=?, last_error=?, updated_at=? WHERE id=?",
                (str(status), error, utc_now(), agent_id),
            )
            await db.commit()

    async def set_all_agent_statuses(
        self, room_id: str, status: AgentStatus | str, error: str | None = None
    ) -> None:
        async with self.connect() as db:
            await db.execute(
                "UPDATE agents SET status=?, last_error=?, updated_at=? WHERE room_id=?",
                (str(status), error, utc_now(), room_id),
            )
            await db.commit()

    async def reopen_ready_agent(self, room_id: str, agent_key: str) -> bool:
        async with self.connect() as db:
            cursor = await db.execute(
                """UPDATE agents SET status=?, last_error=NULL, updated_at=?
                   WHERE room_id=? AND agent_key=? AND status=?""",
                (
                    AgentStatus.IDLE,
                    utc_now(),
                    room_id,
                    agent_key,
                    AgentStatus.READY_TO_FINISH,
                ),
            )
            await db.commit()
        return cursor.rowcount == 1

    async def set_room_status(self, room_id: str, status: RoomStatus | str) -> None:
        async with self.connect() as db:
            await db.execute(
                "UPDATE rooms SET status=?, updated_at=? WHERE id=?",
                (str(status), utc_now(), room_id),
            )
            await db.commit()

    async def reopen_finished_room(self, room_id: str) -> None:
        """Reopen the current discussion without changing either thread identity."""
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute(
                """UPDATE rooms SET status=?, consecutive_passes=0, updated_at=?
                   WHERE id=? AND status=?""",
                (RoomStatus.RUNNING, now, room_id, RoomStatus.FINISHED),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                raise ValueError("Only a naturally finished room can be reopened by a message")
            await db.execute(
                """UPDATE agents SET status=?, last_error=NULL, updated_at=?
                   WHERE room_id=? AND status IN (?, ?)""",
                (
                    AgentStatus.IDLE,
                    now,
                    room_id,
                    AgentStatus.FINISHED,
                    AgentStatus.READY_TO_FINISH,
                ),
            )
            await db.execute(
                """UPDATE rounds SET status=?, ended_at=NULL, close_reason=NULL,
                   consecutive_passes=0 WHERE id=(SELECT active_round_id FROM rooms WHERE id=?)""",
                (RoundStatus.ACTIVE, room_id),
            )
            await db.commit()

    async def update_room(self, room_id: str, changes: dict[str, Any]) -> None:
        allowed = {"title", "max_turns", "max_consecutive_passes", "inactivity_seconds"}
        filtered = {key: value for key, value in changes.items() if key in allowed and value is not None}
        if not filtered:
            return
        assignments = ", ".join(f"{key}=?" for key in filtered)
        values = [*filtered.values(), utc_now(), room_id]
        async with self.connect() as db:
            room = await self._fetchone(db, "SELECT status FROM rooms WHERE id=?", (room_id,))
            if room is None:
                raise KeyError(room_id)
            if room["status"] in {
                RoomStatus.CREATING,
                RoomStatus.ROLLING_OVER,
                RoomStatus.ARCHIVED,
            }:
                raise ValueError(f"Cannot update a room while it is {room['status']}")
            await db.execute(
                f"UPDATE rooms SET {assignments}, updated_at=? WHERE id=?",  # noqa: S608
                values,
            )
            await db.commit()

    async def bind_institutional_release(
        self, room_id: str, institutional_release: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Atomically bind one immutable release and its audit event to a live Room."""
        now = utc_now()
        event_id = new_id("event")
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            room = await self._fetchone(db, "SELECT * FROM rooms WHERE id=?", (room_id,))
            if room is None:
                raise KeyError(room_id)
            metadata = json.loads(room["metadata_json"] or "{}")
            if metadata.get("sealed") is True:
                raise ValueError("Cannot bind an institutional release to a sealed Room")
            if room["status"] not in _INSTITUTIONAL_RELEASE_BINDABLE_ROOM_STATUSES:
                raise ValueError(
                    f"Cannot bind an institutional release while Room is {room['status']}"
                )
            lineage = metadata.get("lineage")
            if lineage is None:
                lineage = {}
            if not isinstance(lineage, dict):
                raise ValueError("Room lineage metadata is malformed")
            current = metadata.get("institutional_release")
            lineage_current = lineage.get("institutional_release")
            if current is not None or lineage_current is not None:
                if current == institutional_release and lineage_current == institutional_release:
                    await db.rollback()
                    return None
                raise ValueError("Room is already bound to another institutional release")

            metadata["institutional_release"] = institutional_release
            lineage["institutional_release"] = institutional_release
            metadata["lineage"] = lineage
            sequence_row = await self._fetchone(
                db,
                "SELECT COALESCE(MAX(sequence_no), 0) + 1 AS next_sequence FROM events WHERE room_id=?",
                (room_id,),
            )
            sequence_no = sequence_row["next_sequence"] if sequence_row else 1
            round_id = room["active_round_id"] or room["discussion_id"]
            await db.execute(
                "UPDATE rooms SET metadata_json=?, updated_at=? WHERE id=?",
                (json.dumps(metadata, ensure_ascii=False), now, room_id),
            )
            await db.execute(
                """INSERT INTO events
                (id, room_id, discussion_id, created_at, event_type, source,
                 destination, content, status, metadata_json, round_id, sequence_no,
                 event_class, conversational, counts_as_turn, counts_toward_pass,
                 visibility, agent_readable, turn_triggering)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, 0, 0)""",
                (
                    event_id,
                    room_id,
                    room["discussion_id"],
                    now,
                    "institutional_release_bound",
                    "room",
                    "observer",
                    "Institutional release bound to Room continuity.",
                    "recorded",
                    json.dumps(
                        {"institutional_release": institutional_release},
                        ensure_ascii=False,
                    ),
                    round_id,
                    sequence_no,
                    "lifecycle",
                    "mechanical",
                ),
            )
            await db.commit()
        event = await self.get_event(event_id)
        assert event is not None
        event["_created"] = True
        return event

    async def get_default_profiles(self) -> dict[str, dict[str, Any]]:
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                "SELECT * FROM agent_profiles WHERE default_slot IS NOT NULL ORDER BY default_slot"
            )
        return {row["default_slot"]: dict(row) for row in rows}

    async def update_default_profiles(
        self,
        agent_a_name: str,
        agent_a_instructions: str,
        agent_b_name: str,
        agent_b_instructions: str,
        agent_c_name: str | None = None,
        agent_c_instructions: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        now = utc_now()
        updates = [
            (agent_a_name, agent_a_instructions, now, "agent_a"),
            (agent_b_name, agent_b_instructions, now, "agent_b"),
        ]
        if agent_c_name is not None and agent_c_instructions is not None:
            updates.append((agent_c_name, agent_c_instructions, now, "agent_c"))
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            await db.executemany(
                """UPDATE agent_profiles SET name=?, developer_instructions=?, updated_at=?
                   WHERE default_slot=?""",
                updates,
            )
            await db.commit()
        return await self.get_default_profiles()

    async def get_rounds(self, room_id: str) -> list[dict[str, Any]]:
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                "SELECT * FROM rounds WHERE room_id=? ORDER BY created_at, id", (room_id,)
            )
        return [self._decode_round(row) for row in rows]

    async def get_round(self, round_id: str) -> dict[str, Any] | None:
        async with self.connect() as db:
            row = await self._fetchone(db, "SELECT * FROM rounds WHERE id=?", (round_id,))
        return self._decode_round(row) if row else None

    async def get_round_agent_states(self, round_id: str) -> list[dict[str, Any]]:
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                """SELECT ras.*, a.agent_key, a.name
                   FROM round_agent_state ras JOIN agents a ON a.id=ras.agent_id
                   WHERE ras.round_id=? ORDER BY a.agent_key""",
                (round_id,),
            )
        return [dict(row) for row in rows]

    async def get_round_agent_state(
        self, round_id: str, agent_id: str
    ) -> dict[str, Any] | None:
        async with self.connect() as db:
            row = await self._fetchone(
                db,
                "SELECT * FROM round_agent_state WHERE round_id=? AND agent_id=?",
                (round_id, agent_id),
            )
        return dict(row) if row else None

    async def prepare_round(self, room_id: str, request: PrepareRoundRequest) -> dict[str, Any]:
        round_id = new_id("round")
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            room = await self._fetchone(db, "SELECT * FROM rooms WHERE id=?", (room_id,))
            if room is None:
                raise KeyError(room_id)
            if room["status"] in {
                RoomStatus.ARCHIVED,
                RoomStatus.CREATING,
                RoomStatus.ROLLING_OVER,
                RoomStatus.ERROR,
            }:
                raise ValueError(f"Cannot prepare a round while room is {room['status']}")
            agents = await db.execute_fetchall(
                "SELECT id, agent_key FROM agents WHERE room_id=? ORDER BY agent_key", (room_id,)
            )
            member_keys = {agent["agent_key"] for agent in agents}
            starting_agent = request.starting_agent or (
                "agent_c" if "agent_c" in member_keys else "either"
            )
            if starting_agent != "either" and starting_agent not in member_keys:
                raise ValueError(f"Starting agent {starting_agent} is not a Room participant")
            configured_keys = set(request.participant_private) | set(request.participant_overlays)
            if not configured_keys <= member_keys:
                missing = sorted(configured_keys - member_keys)
                raise ValueError(f"Round configuration targets non-participants: {missing}")
            required_keys = set(request.required_contributors)
            if not required_keys <= member_keys:
                missing = sorted(required_keys - member_keys)
                raise ValueError(
                    f"Required contributors are not Room participants: {missing}"
                )
            if room["active_round_id"]:
                await db.execute(
                    """UPDATE rounds SET status=?, ended_at=COALESCE(ended_at, ?),
                       close_reason=COALESCE(close_reason, 'replaced_by_new_round')
                       WHERE id=? AND status IN (?, ?)""",
                    (
                        RoundStatus.STOPPED,
                        now,
                        room["active_round_id"],
                        RoundStatus.ACTIVE,
                        RoundStatus.PREPARING,
                    ),
                )
            await db.execute(
                """INSERT INTO rounds
                   (id, room_id, title, prompt, created_at, status, starting_agent,
                    agent_a_private, agent_b_private, task_overlay,
                    agent_a_overlay, agent_b_overlay,
                    participant_private_json, participant_overlays_json,
                    work_model_version, required_contributors_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    round_id,
                    room_id,
                    request.title,
                    request.prompt,
                    now,
                    RoundStatus.PREPARING,
                    starting_agent,
                    request.agent_a_private,
                    request.agent_b_private,
                    request.task_overlay,
                    request.agent_a_overlay,
                    request.agent_b_overlay,
                    json.dumps(request.participant_private, ensure_ascii=False),
                    json.dumps(request.participant_overlays, ensure_ascii=False),
                    request.work_model_version,
                    json.dumps(request.required_contributors),
                ),
            )
            await db.executemany(
                """INSERT INTO round_agent_state
                   (round_id, agent_id, context_stored_at) VALUES (?, ?, ?)""",
                [(round_id, agent["id"], now) for agent in agents],
            )
            await db.execute(
                """UPDATE rooms SET status=?, discussion_id=?, active_round_id=?,
                   turn_count=0, consecutive_passes=0, updated_at=? WHERE id=?""",
                (RoomStatus.PREPARING, round_id, round_id, now, room_id),
            )
            await db.execute(
                """UPDATE agents SET status=?, last_error=NULL, updated_at=? WHERE room_id=?""",
                (AgentStatus.IDLE, now, room_id),
            )
            await db.commit()
        result = await self.get_round(round_id)
        assert result is not None
        return result

    async def start_round(self, room_id: str, round_id: str) -> dict[str, Any]:
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute(
                """UPDATE rounds SET status=?, started_at=?, turn_count=0,
                   consecutive_passes=0, last_activity_at=?
                   WHERE id=? AND room_id=? AND status=?""",
                (
                    RoundStatus.ACTIVE,
                    now,
                    now,
                    round_id,
                    room_id,
                    RoundStatus.PREPARING,
                ),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                raise ValueError("Only the currently prepared round can be started")
            await db.execute(
                """UPDATE rooms SET status=?, discussion_id=?, active_round_id=?,
                   turn_count=0, consecutive_passes=0, updated_at=?
                   WHERE id=? AND active_round_id=?""",
                (RoomStatus.RUNNING, round_id, round_id, now, room_id, round_id),
            )
            await db.execute(
                """UPDATE agents SET status=?, last_error=NULL, updated_at=? WHERE room_id=?""",
                (AgentStatus.IDLE, now, room_id),
            )
            await db.commit()
        result = await self.get_round(round_id)
        assert result is not None
        return result

    async def mark_round_context_consumed(self, round_id: str, agent_id: str) -> None:
        async with self.connect() as db:
            await db.execute(
                """UPDATE round_agent_state SET context_consumed_at=COALESCE(context_consumed_at, ?)
                   WHERE round_id=? AND agent_id=?""",
                (utc_now(), round_id, agent_id),
            )
            await db.commit()

    async def create_event(
        self,
        room_id: str,
        event_type: str,
        source: str,
        destination: str,
        content: str,
        *,
        related_event_id: str | None = None,
        status: str = "recorded",
        metadata: dict[str, Any] | None = None,
        deliver_to: Iterable[str] = (),
        runnable_to: Iterable[str] | None = None,
        discussion_id: str | None = None,
        round_id: str | None = None,
        event_class: str | None = None,
        conversational: bool | None = None,
        counts_as_turn: bool | None = None,
        counts_toward_pass: bool | None = None,
        visibility: str | None = None,
        agent_readable: bool | None = None,
        turn_triggering: bool | None = None,
        execution_id: str | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        event_id = event_id or new_id("event")
        now = utc_now()
        traits = self._event_traits(event_type)
        event_class = event_class or traits[0]
        conversational = traits[1] if conversational is None else conversational
        counts_as_turn = traits[2] if counts_as_turn is None else counts_as_turn
        counts_toward_pass = traits[3] if counts_toward_pass is None else counts_toward_pass
        agent_readable = traits[4] if agent_readable is None else agent_readable
        turn_triggering = traits[5] if turn_triggering is None else turn_triggering
        if visibility is None:
            visibility = "private" if (metadata or {}).get("private") else traits[6]
        readable_recipients = tuple(dict.fromkeys(deliver_to))
        runnable_recipients = (
            readable_recipients
            if runnable_to is None
            else tuple(dict.fromkeys(runnable_to))
        )
        if not set(runnable_recipients).issubset(readable_recipients):
            raise ValueError("Runnable recipients must also be readable recipients")
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            existing_event = await self._fetchone(
                db, "SELECT * FROM events WHERE id=?", (event_id,)
            )
            if existing_event is not None:
                await db.rollback()
                result = self._decode_row(existing_event)
                result["_created"] = False
                return result
            if execution_id is not None:
                existing = await self._fetchone(
                    db, "SELECT * FROM events WHERE execution_id=?", (execution_id,)
                )
                if existing is not None:
                    await db.rollback()
                    result = self._decode_row(existing)
                    result["_created"] = False
                    return result
            if discussion_id is None:
                room_row = await self._fetchone(
                    db, "SELECT discussion_id, active_round_id FROM rooms WHERE id=?", (room_id,)
                )
                if room_row is None:
                    raise KeyError(room_id)
                discussion_id = room_row["discussion_id"]
                round_id = round_id or room_row["active_round_id"] or discussion_id
            else:
                round_id = round_id or discussion_id
            sequence_row = await self._fetchone(
                db,
                "SELECT COALESCE(MAX(sequence_no), 0) + 1 AS next_sequence FROM events WHERE room_id=?",
                (room_id,),
            )
            sequence_no = sequence_row["next_sequence"] if sequence_row else 1
            await db.execute(
                """INSERT INTO events
                (id, room_id, discussion_id, created_at, event_type, source,
                 destination, content, related_event_id, status, metadata_json,
                 round_id, sequence_no, event_class, conversational, counts_as_turn,
                 counts_toward_pass, visibility, agent_readable, turn_triggering,
                 execution_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event_id,
                    room_id,
                    discussion_id,
                    now,
                    event_type,
                    source,
                    destination,
                    content,
                    related_event_id,
                    status,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    round_id,
                    sequence_no,
                    event_class,
                    1 if conversational else 0,
                    1 if counts_as_turn else 0,
                    1 if counts_toward_pass else 0,
                    visibility,
                    1 if agent_readable else 0,
                    1 if turn_triggering else 0,
                    execution_id,
                ),
            )
            for agent_key in readable_recipients:
                agent = await self._fetchone(
                    db,
                    "SELECT id FROM agents WHERE room_id=? AND agent_key=?",
                    (room_id, agent_key),
                )
                if agent is None:
                    raise KeyError(f"Agent {agent_key} not found")
                await db.execute(
                    """INSERT OR IGNORE INTO deliveries
                    (id, event_id, agent_id, runnable, status, attempts, queued_at)
                    VALUES (?, ?, ?, ?, 'pending', 0, ?)""",
                    (
                        new_id("delivery"),
                        event_id,
                        agent["id"],
                        1 if agent_key in runnable_recipients else 0,
                        now,
                    ),
                )
            await db.execute("UPDATE rooms SET updated_at=? WHERE id=?", (now, room_id))
            if conversational:
                await db.execute(
                    "UPDATE rounds SET last_activity_at=? WHERE id=?",
                    (now, round_id),
                )
            await db.commit()
        event = await self.get_event(event_id)
        assert event is not None
        event["_created"] = True
        return event

    async def get_event(self, event_id: str) -> dict[str, Any] | None:
        async with self.connect() as db:
            row = await self._fetchone(db, "SELECT * FROM events WHERE id=?", (event_id,))
        return self._decode_row(row) if row else None

    async def get_events(
        self, room_id: str, limit: int | None = 2000
    ) -> list[dict[str, Any]]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative or None")
        async with self.connect() as db:
            if limit is None:
                rows = await db.execute_fetchall(
                    """SELECT * FROM events WHERE room_id=?
                    ORDER BY sequence_no ASC""",
                    (room_id,),
                )
            else:
                rows = await db.execute_fetchall(
                    """SELECT * FROM (
                           SELECT * FROM events WHERE room_id=?
                           ORDER BY sequence_no DESC LIMIT ?
                       )
                       ORDER BY sequence_no ASC""",
                    (room_id, limit),
                )
            delivery_rows = await db.execute_fetchall(
                """SELECT d.event_id, a.agent_key, d.runnable, d.status, d.batch_id, d.attempts,
                          d.queued_at, d.started_at, d.completed_at, d.consumed_at
                   FROM deliveries d JOIN agents a ON a.id=d.agent_id
                   JOIN events e ON e.id=d.event_id WHERE e.room_id=?""",
                (room_id,),
            )
        deliveries: dict[str, list[dict[str, Any]]] = {}
        for row in delivery_rows:
            item = dict(row)
            item["runnable"] = bool(item["runnable"])
            deliveries.setdefault(item.pop("event_id"), []).append(item)
        events = [self._decode_row(row) for row in rows]
        for event in events:
            event["deliveries"] = deliveries.get(event["id"], [])
        self._annotate_retry_observer_state(events)
        return events

    async def get_event_count(self, room_id: str) -> int:
        async with self.connect() as db:
            row = await self._fetchone(
                db,
                "SELECT COUNT(*) AS event_count FROM events WHERE room_id=?",
                (room_id,),
            )
        return int(row["event_count"]) if row else 0

    async def get_retryable_attempt_failures(
        self,
        room_id: str,
        round_id: str,
        agent_key: str,
        input_event_ids: Iterable[str],
    ) -> list[dict[str, Any]]:
        """Find retry warnings causally included in a successful or terminal batch."""
        successful_inputs = set(input_event_ids)
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                """SELECT * FROM events
                   WHERE room_id=? AND round_id=? AND source=?
                     AND event_type='agent_error'
                     AND json_extract(metadata_json, '$.will_retry')=1
                   ORDER BY sequence_no""",
                (room_id, round_id, agent_key),
            )
        failures = []
        for row in rows:
            event = self._decode_row(row)
            failed_inputs = set(event["metadata"].get("input_event_ids") or ())
            if failed_inputs and failed_inputs.issubset(successful_inputs):
                failures.append(event)
        return failures

    @staticmethod
    def _annotate_retry_observer_state(events: list[dict[str, Any]]) -> None:
        """Project retry outcomes for both current and legacy observer history."""
        pending: dict[tuple[str | None, str], list[dict[str, Any]]] = {}
        for event in events:
            metadata = event["metadata"]
            key = (event.get("round_id"), event["source"])
            if event["event_type"] == "agent_error":
                if metadata.get("will_retry") is True:
                    metadata.setdefault("operator_state", "retrying")
                    pending.setdefault(key, []).append(event)
                else:
                    metadata.setdefault("operator_state", "terminal_failure")
                    failed_inputs = set(metadata.get("input_event_ids") or ())
                    matched = [
                        warning
                        for warning in pending.get(key, [])
                        if set(warning["metadata"].get("input_event_ids") or ())
                        and set(warning["metadata"].get("input_event_ids") or ()).issubset(
                            failed_inputs
                        )
                    ]
                    for warning in matched:
                        warning["metadata"]["operator_state"] = "recovery_failed"
                        warning["metadata"]["terminal_error_event_id"] = event["id"]
                    if matched:
                        metadata.setdefault(
                            "retry_recovery",
                            {
                                "status": "failed",
                                "attempt_failure_count": len(matched),
                                "attempt_failure_event_ids": [item["id"] for item in matched],
                                "attempt_batch_ids": [
                                    item["metadata"].get("batch_id") for item in matched
                                    if item["metadata"].get("batch_id")
                                ],
                            },
                        )
                        pending[key] = [item for item in pending[key] if item not in matched]
                continue
            if event["event_type"] not in {"agent_message", "agent_pass", "agent_finish"}:
                continue
            successful_inputs = set(metadata.get("input_event_ids") or ())
            matched = [
                warning
                for warning in pending.get(key, [])
                if set(warning["metadata"].get("input_event_ids") or ())
                and set(warning["metadata"].get("input_event_ids") or ()).issubset(
                    successful_inputs
                )
            ]
            if not matched:
                continue
            recovery = metadata.setdefault(
                "retry_recovery",
                {
                    "status": "recovered",
                    "attempt_failure_count": len(matched),
                    "attempt_failure_event_ids": [item["id"] for item in matched],
                    "attempt_batch_ids": [
                        item["metadata"].get("batch_id") for item in matched
                        if item["metadata"].get("batch_id")
                    ],
                },
            )
            for warning in matched:
                warning["metadata"]["operator_state"] = "recovered"
                warning["metadata"]["recovered_by_event_id"] = event["id"]
                warning["metadata"]["recovered_outcome"] = event["event_type"]
            if recovery.get("status") == "recovered":
                pending[key] = [item for item in pending[key] if item not in matched]

    async def get_latest_successful_context_checkpoint(
        self, room_id: str, agent_key: str
    ) -> dict[str, Any] | None:
        async with self.connect() as db:
            row = await self._fetchone(
                db,
                """SELECT * FROM events
                   WHERE room_id=? AND event_type='context_checkpoint'
                     AND json_extract(metadata_json, '$.agent')=?
                     AND json_extract(metadata_json, '$.result')='compacted'
                   ORDER BY sequence_no DESC LIMIT 1""",
                (room_id, agent_key),
            )
        return self._decode_row(row) if row else None

    async def establish_context_checkpoint_growth_baseline(
        self,
        room_id: str,
        agent_key: str,
        input_tokens: int,
        batch_id: str,
    ) -> tuple[dict[str, Any] | None, bool]:
        """Persist the first authoritative input count after the latest compaction.

        A checkpoint without the new fields is legacy state and is treated as pending.
        The transaction makes establishment durable before later turns can use it.
        """
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            row = await self._fetchone(
                db,
                """SELECT * FROM events
                   WHERE room_id=? AND event_type='context_checkpoint'
                     AND json_extract(metadata_json, '$.agent')=?
                     AND json_extract(metadata_json, '$.result')='compacted'
                   ORDER BY sequence_no DESC LIMIT 1""",
                (room_id, agent_key),
            )
            if row is None:
                await db.rollback()
                return None, False

            metadata = json.loads(row["metadata_json"] or "{}")
            baseline = metadata.get("growth_baseline_input_tokens")
            if metadata.get("growth_baseline_state") == "established" and isinstance(
                baseline, int
            ):
                await db.rollback()
                return self._decode_row(row), False

            metadata.update(
                {
                    "growth_baseline_state": "established",
                    "growth_baseline_input_tokens": input_tokens,
                    "growth_baseline_batch_id": batch_id,
                }
            )
            await db.execute(
                "UPDATE events SET metadata_json=? WHERE id=?",
                (json.dumps(metadata, ensure_ascii=False), row["id"]),
            )
            await db.commit()
            updated = await self._fetchone(db, "SELECT * FROM events WHERE id=?", (row["id"],))
        return self._decode_row(updated), True

    async def get_round_decision_events(
        self, room_id: str, round_id: str
    ) -> list[dict[str, Any]]:
        """Return the untruncated causal record needed for settlement."""
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                """SELECT * FROM events
                   WHERE room_id=? AND round_id=?
                     AND event_type IN ('agent_message','agent_pass','agent_finish')
                   ORDER BY sequence_no""",
                (room_id, round_id),
            )
            delivery_rows = await db.execute_fetchall(
                """SELECT d.event_id, a.agent_key, d.runnable, d.status, d.batch_id, d.attempts,
                          d.queued_at, d.started_at, d.completed_at, d.consumed_at
                   FROM deliveries d JOIN agents a ON a.id=d.agent_id
                   JOIN events e ON e.id=d.event_id
                   WHERE e.room_id=? AND e.round_id=? AND e.event_type='agent_message'""",
                (room_id, round_id),
            )
        deliveries: dict[str, list[dict[str, Any]]] = {}
        for row in delivery_rows:
            item = dict(row)
            item["runnable"] = bool(item["runnable"])
            deliveries.setdefault(item.pop("event_id"), []).append(item)
        events = [self._decode_row(row) for row in rows]
        for event in events:
            event["deliveries"] = deliveries.get(event["id"], [])
        return events

    async def get_round_transaction_state(
        self, round_id: str
    ) -> dict[str, Any]:
        """Return explicit version-2 work state for inspection/export."""
        async with self.connect() as db:
            task_rows = await db.execute_fetchall(
                "SELECT * FROM tasks WHERE round_id=? ORDER BY created_at, id",
                (round_id,),
            )
            assignment_rows = await db.execute_fetchall(
                """SELECT x.*, a.agent_key
                   FROM assignments x
                   JOIN tasks t ON t.id=x.task_id
                   JOIN agents a ON a.id=x.agent_id
                   WHERE t.round_id=?
                   ORDER BY x.created_at, x.id""",
                (round_id,),
            )
            join_rows = await db.execute_fetchall(
                """SELECT j.*
                   FROM assignment_joins j
                   JOIN tasks t ON t.id=j.task_id
                   WHERE t.round_id=?
                   ORDER BY j.created_at, j.id""",
                (round_id,),
            )
        tasks: list[dict[str, Any]] = []
        assignments_by_task: dict[str, list[dict[str, Any]]] = {}
        joins_by_task: dict[str, list[dict[str, Any]]] = {}
        for row in assignment_rows:
            item = dict(row)
            item["context_event_ids"] = json.loads(
                item.pop("context_event_ids_json", "[]") or "[]"
            )
            assignments_by_task.setdefault(item["task_id"], []).append(item)
        for row in join_rows:
            item = dict(row)
            joins_by_task.setdefault(item["task_id"], []).append(item)
        for row in task_rows:
            item = dict(row)
            item["required_contributors"] = json.loads(
                item.pop("required_contributors_json", "[]") or "[]"
            )
            item["assignments"] = assignments_by_task.get(item["id"], [])
            item["joins"] = joins_by_task.get(item["id"], [])
            tasks.append(item)
        return {"tasks": tasks}

    async def snapshot(
        self, room_id: str, *, event_limit: int | None = 2000
    ) -> dict[str, Any] | None:
        room = await self.get_room(room_id)
        if room is None:
            return None
        room["agents"] = await self.get_agents(room_id)
        event_count = await self.get_event_count(room_id)
        room["events"] = await self.get_events(room_id, limit=event_limit)
        room["event_window"] = {
            "limit": event_limit,
            "total": event_count,
            "returned": len(room["events"]),
            "truncated": len(room["events"]) < event_count,
            "first_sequence_no": (
                room["events"][0].get("sequence_no") if room["events"] else None
            ),
            "last_sequence_no": (
                room["events"][-1].get("sequence_no") if room["events"] else None
            ),
        }
        rounds = await self.get_rounds(room_id)
        for round_item in rounds:
            round_item["events"] = [
                event for event in room["events"] if event.get("round_id") == round_item["id"]
            ]
            round_item["agent_state"] = await self.get_round_agent_states(round_item["id"])
            if round_item.get("work_model_version", 1) == 2:
                round_item["transaction_state"] = await self.get_round_transaction_state(
                    round_item["id"]
                )
            configured_members = {
                state["agent_key"]
                for state in round_item["agent_state"]
                if not state.get("delivery_start_sequence")
            }
            private_by_agent = round_item.get("participant_private", {})
            overlays_by_agent = round_item.get("participant_overlays", {})
            round_item["private_initialization"] = {
                key: {
                    "present": bool(content),
                    "visibility": f"observer_and_{key}",
                    "content": content,
                }
                for key, content in private_by_agent.items()
            }
            for key in ("agent_a", "agent_b"):
                round_item["private_initialization"].setdefault(
                    key,
                    {"present": False, "visibility": f"observer_and_{key}", "content": None},
                )
            round_item["effective_agent_configuration"] = {
                agent["agent_key"]: {
                    "profile_id": agent.get("profile_id"),
                    "profile_snapshot": agent.get("profile_snapshot"),
                    "room_override": agent.get("room_override"),
                    "task_overlay": round_item.get("task_overlay"),
                    "round_overlay": overlays_by_agent.get(agent["agent_key"]),
                }
                for agent in room["agents"]
                if agent["agent_key"] in configured_members
            }
        room["rounds"] = rounds
        room["active_round"] = next(
            (item for item in rounds if item["id"] == room.get("active_round_id")), None
        )
        return room

    async def create_transaction_task(
        self,
        room_id: str,
        round_id: str,
        origin_event_id: str,
        starting_agent: str,
        required_contributors: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create the first explicit task/assignment graph for a version-2 Round."""
        now = utc_now()
        task_id = new_id("task")
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            round_row = await self._fetchone(
                db,
                """SELECT * FROM rounds
                   WHERE id=? AND room_id=? AND status=? AND work_model_version=2""",
                (round_id, room_id, RoundStatus.ACTIVE),
            )
            if round_row is None:
                await db.rollback()
                raise ValueError("Transaction task requires an active work-model-v2 Round")
            existing = await self._fetchone(
                db, "SELECT * FROM tasks WHERE round_id=? ORDER BY created_at LIMIT 1",
                (round_id,),
            )
            if existing is not None:
                await db.commit()
                return {
                    "task_id": existing["id"],
                    "assignment_ids": [],
                    "agent_keys": [],
                    "created": False,
                }
            agents = await db.execute_fetchall(
                "SELECT id, agent_key FROM agents WHERE room_id=? ORDER BY agent_key",
                (room_id,),
            )
            by_key = {row["agent_key"]: row for row in agents}
            coordinator = by_key.get("agent_c")
            if coordinator is None:
                if starting_agent == "either":
                    coordinator = agents[0] if agents else None
                else:
                    coordinator = by_key.get(starting_agent)
            if coordinator is None:
                await db.rollback()
                raise ValueError("Transaction task has no valid coordinator")
            await db.execute(
                """INSERT INTO tasks
                   (id, room_id, round_id, origin_event_id, coordinator_agent_id,
                    state, required_contributors_json, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)""",
                (
                    task_id,
                    room_id,
                    round_id,
                    origin_event_id,
                    coordinator["id"],
                    json.dumps(required_contributors or []),
                    now,
                    now,
                ),
            )

            if starting_agent == "either":
                target_keys = tuple(by_key)
            else:
                if starting_agent not in by_key:
                    await db.rollback()
                    raise ValueError("Round starting agent is not a Room participant")
                target_keys = (starting_agent,)

            assignment_ids: list[str] = []
            join_id: str | None = None
            use_external_join = target_keys != (coordinator["agent_key"],)
            if use_external_join:
                join_id = new_id("join")
                await db.execute(
                    """INSERT INTO assignment_joins
                       (id, task_id, continuation_agent_id, state, created_at)
                       VALUES (?, ?, ?, 'pending', ?)""",
                    (join_id, task_id, coordinator["id"], now),
                )
            for target_key in target_keys:
                assignment_id = new_id("assignment")
                assignment_ids.append(assignment_id)
                await db.execute(
                    """INSERT INTO assignments
                       (id, task_id, agent_id, contribution_join_id, origin_event_id,
                        instruction, state, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?)""",
                    (
                        assignment_id,
                        task_id,
                        by_key[target_key]["id"],
                        join_id,
                        origin_event_id,
                        (
                            "Independently advance the prepared Round objective."
                            if starting_agent == "either"
                            else "Advance the prepared Round objective."
                        ),
                        now,
                        now,
                    ),
                )
            await db.commit()
        return {
            "task_id": task_id,
            "assignment_ids": assignment_ids,
            "agent_keys": list(target_keys),
            "created": True,
        }

    async def create_observer_transaction_work(
        self,
        room_id: str,
        round_id: str,
        origin_event_id: str,
        target_keys: tuple[str, ...],
        instruction: str,
    ) -> dict[str, Any]:
        """Turn observer input into explicit assignments instead of runnable history."""
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            round_row = await self._fetchone(
                db,
                """SELECT * FROM rounds
                   WHERE id=? AND room_id=? AND status=? AND work_model_version=2""",
                (round_id, room_id, RoundStatus.ACTIVE),
            )
            if round_row is None:
                await db.rollback()
                raise ValueError("Observer transaction work requires an active version-2 Round")
            agents = await db.execute_fetchall(
                "SELECT id, agent_key FROM agents WHERE room_id=? ORDER BY agent_key",
                (room_id,),
            )
            by_key = {row["agent_key"]: row for row in agents}
            if not target_keys or any(key not in by_key for key in target_keys):
                await db.rollback()
                raise ValueError("Observer transaction target is not a Room participant")
            coordinator = by_key.get("agent_c") or by_key[target_keys[0]]
            task = await self._fetchone(
                db,
                """SELECT * FROM tasks
                   WHERE room_id=? AND round_id=? AND state='active'
                   ORDER BY created_at DESC LIMIT 1""",
                (room_id, round_id),
            )
            if task is None:
                previous = await self._fetchone(
                    db,
                    """SELECT * FROM tasks
                       WHERE room_id=? AND round_id=?
                       ORDER BY created_at DESC LIMIT 1""",
                    (room_id, round_id),
                )
                task_id = new_id("task")
                await db.execute(
                    """INSERT INTO tasks
                       (id, room_id, round_id, parent_task_id, origin_event_id,
                        coordinator_agent_id, state, required_contributors_json,
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)""",
                    (
                        task_id,
                        room_id,
                        round_id,
                        previous["id"] if previous else None,
                        origin_event_id,
                        coordinator["id"],
                        round_row["required_contributors_json"] or "[]",
                        now,
                        now,
                    ),
                )
            else:
                task_id = task["id"]

            join_id: str | None = None
            if target_keys != (coordinator["agent_key"],):
                join_id = new_id("join")
                await db.execute(
                    """INSERT INTO assignment_joins
                       (id, task_id, continuation_agent_id, state, created_at)
                       VALUES (?, ?, ?, 'pending', ?)""",
                    (join_id, task_id, coordinator["id"], now),
                )
            assignment_ids: list[str] = []
            for target_key in target_keys:
                assignment_id = new_id("assignment")
                assignment_ids.append(assignment_id)
                await db.execute(
                    """INSERT INTO assignments
                       (id, task_id, agent_id, contribution_join_id, origin_event_id,
                        instruction, state, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?)""",
                    (
                        assignment_id,
                        task_id,
                        by_key[target_key]["id"],
                        join_id,
                        origin_event_id,
                        instruction,
                        now,
                        now,
                    ),
                )
            await db.commit()
        return {
            "task_id": task_id,
            "assignment_ids": assignment_ids,
            "agent_keys": list(target_keys),
        }

    async def claim_next_assignment(
        self,
        room_id: str,
        agent_key: str,
        worker_generation: int = 0,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any] | None:
        """Claim one explicit version-2 logical assignment for one serialized agent."""
        now = utc_now()
        batch_id = new_id("batch")
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            agent = await self._fetchone(
                db,
                """SELECT a.*, r.status AS room_status, r.active_round_id,
                          r.max_turns, r.lifecycle_version,
                          ro.turn_count AS round_turn_count, ro.work_model_version
                   FROM agents a JOIN rooms r ON r.id=a.room_id
                   JOIN rounds ro ON ro.id=r.active_round_id
                   WHERE a.room_id=? AND a.agent_key=? AND r.status='running'
                     AND ro.status='active' AND ro.work_model_version=2""",
                (room_id, agent_key),
            )
            if agent is None:
                await db.rollback()
                return None
            execution = await self._fetchone(
                db,
                """SELECT * FROM agent_executions
                   WHERE room_id=? AND agent_id=? AND round_id=? AND assignment_id IS NOT NULL
                     AND state IN ('claimed','active','recovering','result_ready','usage_suspended','quarantined')
                   ORDER BY created_at LIMIT 1""",
                (room_id, agent["id"], agent["active_round_id"]),
            )
            if execution is not None:
                if execution["state"] == "usage_suspended":
                    await db.commit()
                    return None
                assignment = await self._fetchone(
                    db, "SELECT * FROM assignments WHERE id=?", (execution["assignment_id"],)
                )
                if assignment is None:
                    await db.rollback()
                    raise RuntimeError("Transaction execution references a missing assignment")
                continuation_row = await self._fetchone(
                    db,
                    """SELECT * FROM usage_continuations
                       WHERE continuation_batch_id=? AND assignment_id=?
                         AND state='running'""",
                    (execution["batch_id"], assignment["id"]),
                )
                await db.commit()
                result = dict(agent)
                result.update(
                    {
                        "batch_id": execution["batch_id"],
                        "round_id": agent["active_round_id"],
                        "discussion_id": agent["active_round_id"],
                        "assignment": dict(assignment),
                        "assignment_id": assignment["id"],
                        "task_id": assignment["task_id"],
                        "recovered": True,
                        "execution": self._decode_execution(execution),
                        "usage_continuation": (
                            self._decode_usage_continuation(continuation_row)
                            if continuation_row else None
                        ),
                        "work_model_version": 2,
                    }
                )
                return result

            active_executions = await self._fetchone(
                db,
                """SELECT COUNT(*) AS count FROM agent_executions
                   WHERE room_id=? AND round_id=? AND state IN
                     ('claimed','active','recovering','result_ready','usage_suspended')""",
                (room_id, agent["active_round_id"]),
            )
            if (
                agent["round_turn_count"]
                + int(active_executions["count"] if active_executions else 0)
                >= agent["max_turns"]
            ):
                await db.commit()
                return None

            assignment = await self._fetchone(
                db,
                """SELECT x.*
                   FROM assignments x JOIN tasks t ON t.id=x.task_id
                   WHERE x.agent_id=? AND x.state='queued' AND t.state='active'
                     AND t.room_id=? AND t.round_id=?
                   ORDER BY x.created_at, x.id LIMIT 1""",
                (agent["id"], room_id, agent["active_round_id"]),
            )
            if assignment is None:
                await db.commit()
                return None

            continuation_row = await self._fetchone(
                db,
                """SELECT * FROM usage_continuations
                   WHERE agent_id=? AND room_id=? AND round_id=?
                     AND lifecycle_version=? AND thread_id=?
                     AND assignment_id=? AND state='ready'""",
                (
                    agent["id"],
                    room_id,
                    agent["active_round_id"],
                    agent["lifecycle_version"],
                    agent["thread_id"],
                    assignment["id"],
                ),
            )

            selected_model = model
            selected_effort = reasoning_effort
            config_id = assignment["execution_config_id"]
            if config_id:
                resolved = EXECUTION_CONFIGS.get(config_id)
                if resolved is None:
                    await db.rollback()
                    raise RuntimeError("Assignment contains an unsupported execution config")
                selected_model, selected_effort = resolved

            cursor = await db.execute(
                """UPDATE assignments
                   SET state='running', started_at=COALESCE(started_at, ?), updated_at=?
                   WHERE id=? AND state='queued'""",
                (now, now, assignment["id"]),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                return None
            await db.execute(
                "UPDATE agents SET status=?, last_error=NULL, updated_at=? WHERE id=?",
                (AgentStatus.RUNNING, now, agent["id"]),
            )
            await db.execute(
                """INSERT INTO agent_executions
                   (batch_id, room_id, agent_id, round_id, assignment_id,
                    lifecycle_version, worker_generation, model, reasoning_effort,
                    state, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'claimed', ?)""",
                (
                    batch_id,
                    room_id,
                    agent["id"],
                    agent["active_round_id"],
                    assignment["id"],
                    agent["lifecycle_version"],
                    worker_generation,
                    selected_model,
                    selected_effort,
                    now,
                ),
            )
            if continuation_row is not None:
                cursor = await db.execute(
                    """UPDATE usage_continuations
                       SET state='running', continuation_batch_id=?, updated_at=?
                       WHERE id=? AND state='ready'""",
                    (batch_id, now, continuation_row["id"]),
                )
                if cursor.rowcount != 1:
                    await db.rollback()
                    return None
            await db.commit()
            execution = await self._fetchone(
                db, "SELECT * FROM agent_executions WHERE batch_id=?", (batch_id,)
            )
        result = dict(agent)
        result.update(
            {
                "batch_id": batch_id,
                "round_id": agent["active_round_id"],
                "discussion_id": agent["active_round_id"],
                "assignment": dict(assignment),
                "assignment_id": assignment["id"],
                "task_id": assignment["task_id"],
                "recovered": False,
                "execution": self._decode_execution(execution),
                "usage_continuation": (
                    self._decode_usage_continuation(continuation_row)
                    if continuation_row else None
                ),
                "work_model_version": 2,
            }
        )
        return result

    async def get_assignment_dependency_results(
        self, assignment_id: str
    ) -> list[dict[str, Any]]:
        """Return exact released child results that caused this assignment to resume."""
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                """SELECT j.id AS join_id, x.id AS assignment_id, a.agent_key,
                          x.state, x.result_event_id, x.resolution_reason,
                          e.content AS result_content
                   FROM assignment_joins j
                   JOIN assignments x ON x.contribution_join_id=j.id
                   JOIN agents a ON a.id=x.agent_id
                   LEFT JOIN events e ON e.id=x.result_event_id
                   WHERE j.released_assignment_id=? AND j.state='released'
                   ORDER BY j.created_at, x.created_at, x.id""",
                (assignment_id,),
            )
        return [dict(row) for row in rows]

    async def get_assignment_sibling_context(
        self, assignment_id: str
    ) -> list[dict[str, Any]]:
        """Return bounded declared sibling work for one assignment's current join."""
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                """SELECT sibling.id AS assignment_id, a.agent_key,
                          sibling.state, sibling.instruction
                   FROM assignments current
                   JOIN assignments sibling
                     ON sibling.contribution_join_id=current.contribution_join_id
                    AND sibling.id<>current.id
                   JOIN agents a ON a.id=sibling.agent_id
                   WHERE current.id=?
                     AND current.contribution_join_id IS NOT NULL
                   ORDER BY sibling.created_at, sibling.id""",
                (assignment_id,),
            )
        return [dict(row) for row in rows]

    async def get_pending_assignment_evidence(
        self, assignment_id: str
    ) -> list[dict[str, Any]]:
        """Return bounded evidence payloads awaiting one successful assignment continuation."""
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                """SELECT * FROM assignment_evidence
                   WHERE assignment_id=? AND state='pending'
                   ORDER BY created_at, id""",
                (assignment_id,),
            )
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            raw_request = item.pop("request_json")
            item["request"] = json.loads(raw_request) if raw_request else None
            item["durable_request"] = json.loads(item.pop("durable_request_json"))
            item["durable_evidence"] = json.loads(item.pop("durable_evidence_json"))
            payload = item.pop("transient_payload_json")
            item["payload"] = json.loads(payload) if payload else None
            result.append(item)
        return result

    async def get_assignment_evidence_by_batch(
        self, batch_id: str
    ) -> dict[str, Any] | None:
        """Return the exact structured-evidence record created by one model execution."""
        async with self.connect() as db:
            row = await self._fetchone(
                db,
                "SELECT * FROM assignment_evidence WHERE source_batch_id=?",
                (batch_id,),
            )
        if row is None:
            return None
        item = dict(row)
        raw_request = item.pop("request_json")
        item["request"] = json.loads(raw_request) if raw_request else None
        item["durable_request"] = json.loads(item.pop("durable_request_json"))
        item["durable_evidence"] = json.loads(item.pop("durable_evidence_json"))
        payload = item.pop("transient_payload_json")
        item["payload"] = json.loads(payload) if payload else None
        return item

    async def prepare_transaction_evidence(
        self,
        room_id: str,
        batch_id: str,
        assignment_id: str,
        requests: list[dict[str, Any]],
        *,
        durable_requests: list[dict[str, Any]],
        strategy: str,
        durable_evidence: dict[str, Any],
        transient_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Durably stage exact bounded evidence before any provenance/queue side effects."""
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            execution = await self._fetchone(
                db, "SELECT * FROM agent_executions WHERE batch_id=?", (batch_id,)
            )
            if (
                execution is None
                or execution["assignment_id"] != assignment_id
                or execution["state"] not in {"result_ready", "settled"}
            ):
                await db.rollback()
                raise RuntimeError("Transaction execution is not ready for evidence preparation")
            assignment = await self._fetchone(
                db,
                """SELECT x.*, a.room_id
                   FROM assignments x JOIN agents a ON a.id=x.agent_id
                   WHERE x.id=?""",
                (assignment_id,),
            )
            if assignment is None or assignment["room_id"] != room_id:
                await db.rollback()
                raise RuntimeError("Transaction assignment is missing or belongs elsewhere")

            existing = await self._fetchone(
                db,
                "SELECT * FROM assignment_evidence WHERE source_batch_id=?",
                (batch_id,),
            )
            if existing is None:
                if execution["decision_recorded_at"] is not None:
                    await db.rollback()
                    raise RuntimeError(
                        "Recorded evidence decision is missing its prepared result"
                    )
                if assignment["state"] != "running":
                    await db.rollback()
                    raise RuntimeError(
                        "Only a running assignment can prepare transaction evidence"
                    )
                evidence_id = new_id("evidence")
                await db.execute(
                    """INSERT INTO assignment_evidence
                       (id, assignment_id, source_batch_id, request_json,
                        durable_request_json, durable_evidence_json,
                        transient_payload_json, strategy, state,
                        provenance_event_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'prepared', NULL, ?)""",
                    (
                        evidence_id,
                        assignment_id,
                        batch_id,
                        json.dumps(
                            requests,
                            ensure_ascii=True,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        json.dumps(
                            durable_requests,
                            ensure_ascii=True,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        json.dumps(
                            durable_evidence,
                            ensure_ascii=True,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        json.dumps(
                            transient_payload,
                            ensure_ascii=True,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        strategy,
                        now,
                    ),
                )
                existing = await self._fetchone(
                    db,
                    "SELECT * FROM assignment_evidence WHERE id=?",
                    (evidence_id,),
                )
            await db.commit()

        if existing is None:
            raise RuntimeError("Prepared evidence could not be reloaded")
        item = dict(existing)
        raw_request = item.pop("request_json")
        item["request"] = json.loads(raw_request) if raw_request else None
        item["durable_request"] = json.loads(item.pop("durable_request_json"))
        item["durable_evidence"] = json.loads(item.pop("durable_evidence_json"))
        payload = item.pop("transient_payload_json")
        item["payload"] = json.loads(payload) if payload else None
        return item

    async def settle_transaction_evidence(
        self,
        room_id: str,
        round_id: str,
        batch_id: str,
        assignment_id: str,
        *,
        provenance_event_id: str,
    ) -> dict[str, Any]:
        """Atomically promote prepared evidence and requeue the same assignment."""
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            execution = await self._fetchone(
                db, "SELECT * FROM agent_executions WHERE batch_id=?", (batch_id,)
            )
            if (
                execution is None
                or execution["assignment_id"] != assignment_id
                or execution["state"] not in {"result_ready", "settled"}
            ):
                await db.rollback()
                raise RuntimeError("Transaction execution is not ready for evidence settlement")
            assignment = await self._fetchone(
                db,
                """SELECT x.*, a.agent_key, a.room_id
                   FROM assignments x JOIN agents a ON a.id=x.agent_id
                   WHERE x.id=?""",
                (assignment_id,),
            )
            if assignment is None or assignment["room_id"] != room_id:
                await db.rollback()
                raise RuntimeError("Transaction assignment is missing or belongs elsewhere")

            existing = await self._fetchone(
                db,
                "SELECT * FROM assignment_evidence WHERE source_batch_id=?",
                (batch_id,),
            )
            if existing is None:
                await db.rollback()
                raise RuntimeError("Transaction evidence was not prepared before settlement")
            if execution["decision_recorded_at"] is not None:
                round_budget = await self._fetchone(
                    db,
                    """SELECT ro.turn_count, r.max_turns
                       FROM rounds ro JOIN rooms r ON r.id=ro.room_id
                       WHERE ro.id=? AND ro.room_id=?""",
                    (round_id, room_id),
                )
                turn_limit_hit = bool(
                    round_budget
                    and int(round_budget["turn_count"]) >= int(round_budget["max_turns"])
                )
                await db.commit()
                return {
                    "wake_agent_keys": (
                        [assignment["agent_key"]]
                        if assignment["state"] == "queued" and not turn_limit_hit
                        else []
                    ),
                    "turn_limit_hit": turn_limit_hit,
                    "decision_applied": False,
                    "evidence_id": existing["id"],
                }
            if assignment["state"] != "running":
                await db.rollback()
                raise RuntimeError("Only a running assignment can request evidence")
            if existing["state"] != "prepared":
                await db.rollback()
                raise RuntimeError("Transaction evidence is not in prepared state")

            await db.execute(
                "UPDATE rooms SET turn_count=turn_count+1, updated_at=? WHERE id=?",
                (now, room_id),
            )
            await db.execute(
                """UPDATE rounds SET turn_count=turn_count+1
                   WHERE id=? AND room_id=? AND status=? AND work_model_version=2""",
                (round_id, room_id, RoundStatus.ACTIVE),
            )
            round_budget = await self._fetchone(
                db,
                """SELECT ro.turn_count, r.max_turns
                   FROM rounds ro JOIN rooms r ON r.id=ro.room_id
                   WHERE ro.id=? AND ro.room_id=?""",
                (round_id, room_id),
            )
            turn_limit_hit = bool(
                round_budget
                and int(round_budget["turn_count"]) >= int(round_budget["max_turns"])
            )

            await db.execute(
                """UPDATE assignment_evidence
                   SET state='consumed', consumed_at=?,
                       request_json=NULL, transient_payload_json=NULL
                   WHERE assignment_id=? AND state='pending'""",
                (now, assignment_id),
            )
            cursor = await db.execute(
                """UPDATE assignment_evidence
                   SET state='pending', provenance_event_id=?
                   WHERE id=? AND state='prepared'""",
                (provenance_event_id, existing["id"]),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                raise RuntimeError("Evidence settlement lost its prepared result")
            cursor = await db.execute(
                """UPDATE assignments
                   SET state='queued', updated_at=?, resolution_reason=NULL
                   WHERE id=? AND state='running'""",
                (now, assignment_id),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                raise RuntimeError("Evidence settlement lost the running assignment")
            cursor = await db.execute(
                """UPDATE agent_executions SET decision_recorded_at=?
                   WHERE batch_id=? AND decision_recorded_at IS NULL""",
                (now, batch_id),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                raise RuntimeError("Evidence settlement lost its compare-and-set")
            await db.commit()
        return {
            "wake_agent_keys": [assignment["agent_key"]],
            "turn_limit_hit": turn_limit_hit,
            "decision_applied": True,
            "evidence_id": existing["id"],
        }

    async def settle_transaction_decision(
        self,
        room_id: str,
        round_id: str,
        batch_id: str,
        assignment_id: str,
        action: str,
        result_event_id: str,
        delegations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Atomically settle one assignment decision and release any satisfied join."""
        now = utc_now()
        terminal_states = ("completed", "passed", "failed", "cancelled", "waived")
        wake_agent_keys: list[str] = []
        released_join_id: str | None = None
        task_settled = False
        missing_required_contributors: list[str] = []
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            execution = await self._fetchone(
                db, "SELECT * FROM agent_executions WHERE batch_id=?", (batch_id,)
            )
            if (
                execution is None
                or execution["assignment_id"] != assignment_id
                or execution["state"] not in {"result_ready", "settled"}
            ):
                await db.rollback()
                raise RuntimeError("Transaction execution is not ready for settlement")
            assignment = await self._fetchone(
                db,
                """SELECT x.*, a.agent_key, a.room_id
                   FROM assignments x JOIN agents a ON a.id=x.agent_id
                   WHERE x.id=?""",
                (assignment_id,),
            )
            if assignment is None or assignment["room_id"] != room_id:
                await db.rollback()
                raise RuntimeError("Transaction assignment is missing or belongs elsewhere")
            if execution["decision_recorded_at"] is not None:
                await db.commit()
                return {
                    "wake_agent_keys": [],
                    "released_join_id": None,
                    "task_settled": False,
                    "turn_limit_hit": False,
                    "decision_applied": False,
                }
            if assignment["state"] != "running":
                await db.rollback()
                raise RuntimeError("Only a running assignment can settle a new decision")

            await db.execute(
                """UPDATE rooms SET turn_count=turn_count+1, updated_at=? WHERE id=?""",
                (now, room_id),
            )
            await db.execute(
                """UPDATE rounds SET turn_count=turn_count+1
                   WHERE id=? AND room_id=? AND status=? AND work_model_version=2""",
                (round_id, room_id, RoundStatus.ACTIVE),
            )

            round_budget = await self._fetchone(
                db,
                """SELECT ro.turn_count, r.max_turns
                   FROM rounds ro JOIN rooms r ON r.id=ro.room_id
                   WHERE ro.id=? AND ro.room_id=?""",
                (round_id, room_id),
            )
            turn_limit_hit = bool(
                round_budget
                and int(round_budget["turn_count"]) >= int(round_budget["max_turns"])
            )

            await db.execute(
                """UPDATE assignment_evidence
                   SET state='consumed', consumed_at=?,
                       request_json=NULL, transient_payload_json=NULL
                   WHERE assignment_id=? AND state='pending'""",
                (now, assignment_id),
            )

            if action == "DELEGATE":
                if not delegations:
                    await db.rollback()
                    raise ValueError("DELEGATE requires child assignments")
                join_id = new_id("join")
                await db.execute(
                    """INSERT INTO assignment_joins
                       (id, task_id, parent_assignment_id, state, created_at)
                       VALUES (?, ?, ?, 'pending', ?)""",
                    (join_id, assignment["task_id"], assignment_id, now),
                )
                await db.execute(
                    """UPDATE assignments
                       SET state='waiting_join', result_event_id=?, updated_at=?
                       WHERE id=? AND state='running'""",
                    (result_event_id, now, assignment_id),
                )
                seen: set[str] = set()
                for item in delegations:
                    target_key = item["target"]
                    if target_key == assignment["agent_key"] or target_key in seen:
                        await db.rollback()
                        raise ValueError("Delegation targets must be distinct peers")
                    seen.add(target_key)
                    target = await self._fetchone(
                        db,
                        "SELECT * FROM agents WHERE room_id=? AND agent_key=?",
                        (room_id, target_key),
                    )
                    if target is None:
                        await db.rollback()
                        raise ValueError(f"Delegation target {target_key} is unavailable")
                    config_id = item.get("config")
                    if config_id is not None and config_id not in EXECUTION_CONFIGS:
                        await db.rollback()
                        raise ValueError("Delegation execution config is unsupported")
                    child_id = new_id("assignment")
                    await db.execute(
                        """INSERT INTO assignments
                           (id, task_id, agent_id, parent_assignment_id,
                            contribution_join_id, origin_event_id, instruction,
                            execution_config_id, state, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)""",
                        (
                            child_id,
                            assignment["task_id"],
                            target["id"],
                            assignment_id,
                            join_id,
                            result_event_id,
                            item["instruction"],
                            config_id,
                            now,
                            now,
                        ),
                    )
                    wake_agent_keys.append(target_key)
            else:
                state = "completed" if action == "COMPLETE" else "passed"
                await db.execute(
                    """UPDATE assignments
                       SET state=?, result_event_id=?, completed_at=?, updated_at=?
                       WHERE id=? AND state='running'""",
                    (state, result_event_id, now, now, assignment_id),
                )

            cursor = await db.execute(
                """UPDATE agent_executions SET decision_recorded_at=?
                   WHERE batch_id=? AND decision_recorded_at IS NULL""",
                (now, batch_id),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                raise RuntimeError("Transaction decision settlement lost its compare-and-set")

            contribution_join_id = assignment["contribution_join_id"]
            if action != "DELEGATE" and contribution_join_id:
                open_member = await self._fetchone(
                    db,
                    """SELECT 1 FROM assignments
                       WHERE contribution_join_id=? AND state NOT IN
                         ('completed','passed','failed','cancelled','waived')
                       LIMIT 1""",
                    (contribution_join_id,),
                )
                if open_member is None:
                    join = await self._fetchone(
                        db,
                        "SELECT * FROM assignment_joins WHERE id=?",
                        (contribution_join_id,),
                    )
                    if join is not None and join["state"] == "pending":
                        await db.execute(
                            """UPDATE assignment_joins SET state='ready', ready_at=?
                               WHERE id=? AND state='pending'""",
                            (now, contribution_join_id),
                        )
                        released_assignment_id: str | None = None
                        if join["parent_assignment_id"]:
                            parent = await self._fetchone(
                                db,
                                """SELECT x.*, a.agent_key
                                   FROM assignments x JOIN agents a ON a.id=x.agent_id
                                   WHERE x.id=?""",
                                (join["parent_assignment_id"],),
                            )
                            if parent is None or parent["state"] != "waiting_join":
                                await db.rollback()
                                raise RuntimeError("Ready join has no waiting parent assignment")
                            await db.execute(
                                """UPDATE assignments
                                   SET state='queued', updated_at=?
                                   WHERE id=? AND state='waiting_join'""",
                                (now, parent["id"]),
                            )
                            released_assignment_id = parent["id"]
                            wake_agent_keys.append(parent["agent_key"])
                        else:
                            continuation = await self._fetchone(
                                db,
                                """SELECT a.* FROM agents a
                                   WHERE a.id=? AND a.room_id=?""",
                                (join["continuation_agent_id"], room_id),
                            )
                            if continuation is None:
                                await db.rollback()
                                raise RuntimeError("Ready join has no continuation agent")
                            released_assignment_id = new_id("assignment")
                            await db.execute(
                                """INSERT INTO assignments
                                   (id, task_id, agent_id, origin_event_id, instruction,
                                    state, created_at, updated_at)
                                   VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)""",
                                (
                                    released_assignment_id,
                                    assignment["task_id"],
                                    continuation["id"],
                                    result_event_id,
                                    "Integrate the completed dependent assignments and advance the task.",
                                    now,
                                    now,
                                ),
                            )
                            wake_agent_keys.append(continuation["agent_key"])
                        await db.execute(
                            """UPDATE assignment_joins
                               SET state='released', released_assignment_id=?, released_at=?
                               WHERE id=? AND state='ready'""",
                            (
                                released_assignment_id,
                                now,
                                contribution_join_id,
                            ),
                        )
                        released_join_id = contribution_join_id

            if action != "DELEGATE":
                open_assignment = await self._fetchone(
                    db,
                    """SELECT 1 FROM assignments
                       WHERE task_id=? AND state IN ('queued','running','waiting_join')
                       LIMIT 1""",
                    (assignment["task_id"],),
                )
                open_join = await self._fetchone(
                    db,
                    """SELECT 1 FROM assignment_joins
                       WHERE task_id=? AND state IN ('pending','ready')
                       LIMIT 1""",
                    (assignment["task_id"],),
                )
                task = await self._fetchone(
                    db, "SELECT * FROM tasks WHERE id=?", (assignment["task_id"],)
                )
                if (
                    open_assignment is None
                    and open_join is None
                    and task is not None
                    and task["coordinator_agent_id"] == assignment["agent_id"]
                    and task["state"] == "active"
                ):
                    required = json.loads(
                        task["required_contributors_json"] or "[]"
                    )
                    terminal_rows = await db.execute_fetchall(
                        """SELECT DISTINCT a.agent_key
                           FROM assignments x JOIN agents a ON a.id=x.agent_id
                           WHERE x.task_id=? AND x.state IN
                             ('completed','passed','failed','cancelled','waived')""",
                        (assignment["task_id"],),
                    )
                    contributed = {row["agent_key"] for row in terminal_rows}
                    missing_required_contributors = [
                        key for key in required if key not in contributed
                    ]
                    if missing_required_contributors and not turn_limit_hit:
                        coordinator = await self._fetchone(
                            db,
                            "SELECT agent_key FROM agents WHERE id=?",
                            (task["coordinator_agent_id"],),
                        )
                        if coordinator is None:
                            await db.rollback()
                            raise RuntimeError(
                                "Active transaction task has no coordinator agent"
                            )
                        followup_id = new_id("assignment")
                        await db.execute(
                            """INSERT INTO assignments
                               (id, task_id, agent_id, origin_event_id, instruction,
                                state, created_at, updated_at)
                               VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)""",
                            (
                                followup_id,
                                assignment["task_id"],
                                task["coordinator_agent_id"],
                                result_event_id,
                                (
                                    "The human explicitly requires contribution from: "
                                    + ", ".join(missing_required_contributors)
                                    + ". The task cannot settle until each named participant "
                                      "has a causally linked terminal assignment. Delegate "
                                      "bounded work to the missing participant(s), then integrate "
                                      "their results."
                                ),
                                now,
                                now,
                            ),
                        )
                        wake_agent_keys.append(coordinator["agent_key"])
                    elif not missing_required_contributors:
                        await db.execute(
                            """UPDATE tasks
                               SET state='settled', settled_at=?, updated_at=?,
                                   settlement_event_id=?, settlement_reason=?
                               WHERE id=? AND state='active'""",
                            (
                                now,
                                now,
                                result_event_id,
                                action.lower(),
                                assignment["task_id"],
                            ),
                        )
                        task_settled = True

            await db.commit()
        return {
            "wake_agent_keys": list(dict.fromkeys(wake_agent_keys)),
            "released_join_id": released_join_id,
            "task_settled": task_settled,
            "missing_required_contributors": missing_required_contributors,
            "turn_limit_hit": turn_limit_hit,
            "decision_applied": True,
        }

    async def fail_transaction_assignment(
        self,
        room_id: str,
        round_id: str,
        batch_id: str,
        error: str,
        *,
        retryable: bool = True,
    ) -> dict[str, Any]:
        """Fail or requeue one exact transaction execution without stranding joins."""
        now = utc_now()
        wake_agent_keys: list[str] = []
        task_failed = False
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            execution = await self._fetchone(
                db, "SELECT * FROM agent_executions WHERE batch_id=?", (batch_id,)
            )
            if execution is None or not execution["assignment_id"]:
                await db.rollback()
                raise RuntimeError("Transaction failure has no assignment execution")
            assignment = await self._fetchone(
                db,
                """SELECT x.*, a.agent_key, a.room_id
                   FROM assignments x JOIN agents a ON a.id=x.agent_id
                   WHERE x.id=?""",
                (execution["assignment_id"],),
            )
            if assignment is None or assignment["room_id"] != room_id:
                await db.rollback()
                raise RuntimeError("Transaction failure assignment is unavailable")
            attempts = await self._fetchone(
                db,
                "SELECT COUNT(*) AS count FROM agent_executions WHERE assignment_id=?",
                (assignment["id"],),
            )
            should_retry = (
                retryable
                and int(attempts["count"] if attempts else 0) < 2
                and assignment["state"] == "running"
            )
            await db.execute(
                """UPDATE agent_executions
                   SET state='failed', settled_at=?, error=?
                   WHERE batch_id=? AND state IN
                     ('claimed','active','recovering','result_ready')""",
                (now, error[:4000], batch_id),
            )
            await db.execute(
                "UPDATE agents SET status=?, last_error=?, updated_at=? WHERE id=?",
                (AgentStatus.IDLE, error[:4000], now, assignment["agent_id"]),
            )
            if should_retry:
                await db.execute(
                    """UPDATE assignments
                       SET state='queued', updated_at=?, resolution_reason=?
                       WHERE id=? AND state='running'""",
                    (now, error[:4000], assignment["id"]),
                )
                wake_agent_keys.append(assignment["agent_key"])
                await db.commit()
                return {
                    "retried": True,
                    "wake_agent_keys": wake_agent_keys,
                    "task_failed": False,
                }

            await db.execute(
                """UPDATE assignments
                   SET state='failed', completed_at=?, updated_at=?, resolution_reason=?
                   WHERE id=? AND state IN ('running','queued')""",
                (now, now, error[:4000], assignment["id"]),
            )
            contribution_join_id = assignment["contribution_join_id"]
            if contribution_join_id:
                open_member = await self._fetchone(
                    db,
                    """SELECT 1 FROM assignments
                       WHERE contribution_join_id=? AND state NOT IN
                         ('completed','passed','failed','cancelled','waived')
                       LIMIT 1""",
                    (contribution_join_id,),
                )
                join = await self._fetchone(
                    db, "SELECT * FROM assignment_joins WHERE id=?",
                    (contribution_join_id,),
                )
                if open_member is None and join is not None and join["state"] == "pending":
                    await db.execute(
                        """UPDATE assignment_joins
                           SET state='ready', ready_at=?
                           WHERE id=? AND state='pending'""",
                        (now, contribution_join_id),
                    )
                    if join["parent_assignment_id"]:
                        parent = await self._fetchone(
                            db,
                            """SELECT x.*, a.agent_key
                               FROM assignments x JOIN agents a ON a.id=x.agent_id
                               WHERE x.id=?""",
                            (join["parent_assignment_id"],),
                        )
                        if parent is None or parent["state"] != "waiting_join":
                            await db.rollback()
                            raise RuntimeError("Failed child has no waiting parent assignment")
                        released_assignment_id = parent["id"]
                        await db.execute(
                            """UPDATE assignments SET state='queued', updated_at=?
                               WHERE id=? AND state='waiting_join'""",
                            (now, parent["id"]),
                        )
                        wake_agent_keys.append(parent["agent_key"])
                    else:
                        continuation = await self._fetchone(
                            db,
                            "SELECT * FROM agents WHERE id=? AND room_id=?",
                            (join["continuation_agent_id"], room_id),
                        )
                        if continuation is None:
                            await db.rollback()
                            raise RuntimeError("Failed child join has no continuation agent")
                        released_assignment_id = new_id("assignment")
                        await db.execute(
                            """INSERT INTO assignments
                               (id, task_id, agent_id, instruction, state, created_at, updated_at)
                               VALUES (?, ?, ?, ?, 'queued', ?, ?)""",
                            (
                                released_assignment_id,
                                assignment["task_id"],
                                continuation["id"],
                                "Integrate the completed dependent assignments, including failures, and advance the task.",
                                now,
                                now,
                            ),
                        )
                        wake_agent_keys.append(continuation["agent_key"])
                    await db.execute(
                        """UPDATE assignment_joins
                           SET state='released', released_assignment_id=?, released_at=?
                           WHERE id=? AND state='ready'""",
                        (released_assignment_id, now, contribution_join_id),
                    )
            else:
                task = await self._fetchone(
                    db, "SELECT * FROM tasks WHERE id=?", (assignment["task_id"],)
                )
                if (
                    task is not None
                    and task["coordinator_agent_id"] == assignment["agent_id"]
                    and task["state"] == "active"
                ):
                    await db.execute(
                        """UPDATE tasks
                           SET state='failed', updated_at=?, settled_at=?,
                               settlement_reason=?
                           WHERE id=? AND state='active'""",
                        (now, now, error[:4000], assignment["task_id"]),
                    )
                    task_failed = True
            await db.commit()
        return {
            "retried": False,
            "wake_agent_keys": list(dict.fromkeys(wake_agent_keys)),
            "task_failed": task_failed,
        }

    async def has_open_transaction_assignment(
        self,
        room_id: str,
        agent_key: str,
        round_id: str | None = None,
    ) -> bool:
        async with self.connect() as db:
            params: list[Any] = [room_id, agent_key]
            round_clause = ""
            if round_id is not None:
                round_clause = " AND t.round_id=?"
                params.append(round_id)
            row = await self._fetchone(
                db,
                f"""SELECT 1
                    FROM assignments x
                    JOIN tasks t ON t.id=x.task_id
                    JOIN agents a ON a.id=x.agent_id
                    WHERE t.room_id=? AND a.agent_key=?
                      AND t.state='active'
                      AND x.state IN ('queued','running','waiting_join')
                      {round_clause}
                    LIMIT 1""",
                tuple(params),
            )
        return row is not None

    async def has_active_transaction_task(
        self, room_id: str, round_id: str
    ) -> bool:
        async with self.connect() as db:
            row = await self._fetchone(
                db,
                """SELECT 1 FROM tasks
                   WHERE room_id=? AND round_id=? AND state='active' LIMIT 1""",
                (room_id, round_id),
            )
        return row is not None

    async def cancel_transaction_work(
        self, room_id: str, round_id: str | None = None
    ) -> None:
        """Cancel unfinished transaction state under the same Room lifecycle boundary."""
        now = utc_now()
        async with self.connect() as db:
            task_clause = " AND round_id=?" if round_id is not None else ""
            task_params: list[Any] = [now, now, room_id]
            if round_id is not None:
                task_params.append(round_id)
            await db.execute(
                f"""UPDATE tasks
                    SET state='cancelled', updated_at=?, settled_at=?,
                        settlement_reason='room_lifecycle_change'
                    WHERE room_id=? AND state='active'{task_clause}""",
                task_params,
            )
            assignment_clause = (
                " AND task_id IN (SELECT id FROM tasks WHERE room_id=? AND round_id=?)"
                if round_id is not None
                else " AND task_id IN (SELECT id FROM tasks WHERE room_id=?)"
            )
            assignment_params: list[Any] = [now, now, room_id]
            if round_id is not None:
                assignment_params.append(round_id)
            await db.execute(
                f"""UPDATE assignments
                    SET state='cancelled', updated_at=?, completed_at=?,
                        resolution_reason='room_lifecycle_change'
                    WHERE state IN ('queued','running','waiting_join'){assignment_clause}""",
                assignment_params,
            )
            join_clause = (
                " AND task_id IN (SELECT id FROM tasks WHERE room_id=? AND round_id=?)"
                if round_id is not None
                else " AND task_id IN (SELECT id FROM tasks WHERE room_id=?)"
            )
            join_params: list[Any] = [now, room_id]
            if round_id is not None:
                join_params.append(round_id)
            await db.execute(
                f"""UPDATE assignment_joins
                    SET state='cancelled', released_at=?
                    WHERE state IN ('pending','ready'){join_clause}""",
                join_params,
            )
            evidence_clause = (
                " AND assignment_id IN (SELECT x.id FROM assignments x "
                "JOIN tasks t ON t.id=x.task_id WHERE t.room_id=? AND t.round_id=?)"
                if round_id is not None
                else " AND assignment_id IN (SELECT x.id FROM assignments x "
                "JOIN tasks t ON t.id=x.task_id WHERE t.room_id=?)"
            )
            evidence_params: list[Any] = [now, room_id]
            if round_id is not None:
                evidence_params.append(round_id)
            await db.execute(
                f"""UPDATE assignment_evidence
                    SET state='discarded', consumed_at=?,
                        request_json=NULL, transient_payload_json=NULL
                    WHERE state IN ('prepared','pending'){evidence_clause}""",
                evidence_params,
            )
            await db.commit()

    async def claim_next_batch(
        self,
        room_id: str,
        agent_key: str,
        worker_generation: int = 0,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any] | None:
        now = utc_now()
        batch_id = new_id("batch")
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            agent = await self._fetchone(
                db,
                """SELECT a.*, r.status AS room_status, r.active_round_id,
                          r.max_turns, r.lifecycle_version, ro.turn_count AS round_turn_count,
                          ras.finish_boundary_sequence, ras.context_consumed_at,
                          ras.delivery_start_sequence
                   FROM agents a JOIN rooms r ON r.id=a.room_id
                   JOIN rounds ro ON ro.id=r.active_round_id
                   JOIN round_agent_state ras ON ras.round_id=ro.id AND ras.agent_id=a.id
                   WHERE a.room_id=? AND a.agent_key=? AND r.status='running'
                     AND ro.status='active'""",
                (room_id, agent_key),
            )
            if agent is None:
                await db.rollback()
                return None
            execution = await self._fetchone(
                db,
                """SELECT * FROM agent_executions
                   WHERE room_id=? AND agent_id=? AND round_id=?
                     AND state IN ('claimed','active','recovering','result_ready','usage_suspended')
                   ORDER BY created_at LIMIT 1""",
                (room_id, agent["id"], agent["active_round_id"]),
            )
            if execution is not None:
                if (
                    (execution["model"] is None and model is not None)
                    or (
                        execution["reasoning_effort"] is None
                        and reasoning_effort is not None
                    )
                ):
                    await db.execute(
                        """UPDATE agent_executions
                           SET model=COALESCE(model, ?),
                               reasoning_effort=COALESCE(reasoning_effort, ?)
                           WHERE batch_id=?""",
                        (model, reasoning_effort, execution["batch_id"]),
                    )
                    execution = await self._fetchone(
                        db,
                        "SELECT * FROM agent_executions WHERE batch_id=?",
                        (execution["batch_id"],),
                    )
                    assert execution is not None
                if execution["state"] == "usage_suspended":
                    await db.commit()
                    return None
                rows = await db.execute_fetchall(
                    """SELECT d.id AS delivery_id, d.attempts,
                              d.runnable AS delivery_runnable, e.*
                       FROM deliveries d JOIN events e ON e.id=d.event_id
                       WHERE d.agent_id=? AND d.batch_id=?
                       ORDER BY e.sequence_no""",
                    (agent["id"], execution["batch_id"]),
                )
                continuation_row = await self._fetchone(
                    db,
                    """SELECT * FROM usage_continuations
                       WHERE continuation_batch_id=? AND state='running'""",
                    (execution["batch_id"],),
                )
                await db.commit()
                if not rows:
                    return None
                return self._claimed_batch(
                    agent,
                    rows,
                    execution["batch_id"],
                    recovered=True,
                    execution=self._decode_execution(execution),
                    usage_continuation=(
                        self._decode_usage_continuation(continuation_row)
                        if continuation_row else None
                    ),
                )

            # Legacy or crash-window processing with no execution identity is not
            # safe to replay. Give it a durable quarantined record so the worker
            # can surface the ambiguity instead of starting duplicate work.
            legacy = await self._fetchone(
                db,
                """SELECT d.batch_id
                   FROM deliveries d JOIN events e ON e.id=d.event_id
                   WHERE d.agent_id=? AND d.status='processing'
                     AND e.room_id=? AND e.round_id=?
                   LIMIT 1""",
                (agent["id"], room_id, agent["active_round_id"]),
            )
            if legacy is not None:
                legacy_batch_id = legacy["batch_id"] or batch_id
                if legacy["batch_id"] is None:
                    await db.execute(
                        """UPDATE deliveries SET batch_id=?
                           WHERE agent_id=? AND status='processing' AND event_id IN (
                             SELECT id FROM events WHERE room_id=? AND round_id=?
                           )""",
                        (legacy_batch_id, agent["id"], room_id, agent["active_round_id"]),
                    )
                await db.execute(
                    """INSERT INTO agent_executions
                       (batch_id, room_id, agent_id, round_id, lifecycle_version,
                        worker_generation, model, reasoning_effort,
                        state, created_at, error)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'quarantined', ?, ?)""",
                    (
                        legacy_batch_id,
                        room_id,
                        agent["id"],
                        agent["active_round_id"],
                        agent["lifecycle_version"],
                        worker_generation,
                        model,
                        reasoning_effort,
                        now,
                        "Processing claim has no persisted Codex turn identity",
                    ),
                )
                rows = await db.execute_fetchall(
                    """SELECT d.id AS delivery_id, d.attempts,
                              d.runnable AS delivery_runnable, e.*
                       FROM deliveries d JOIN events e ON e.id=d.event_id
                       WHERE d.agent_id=? AND d.batch_id=? ORDER BY e.sequence_no""",
                    (agent["id"], legacy_batch_id),
                )
                execution = await self._fetchone(
                    db, "SELECT * FROM agent_executions WHERE batch_id=?", (legacy_batch_id,)
                )
                await db.commit()
                return self._claimed_batch(
                    agent,
                    rows,
                    legacy_batch_id,
                    recovered=True,
                    execution=self._decode_execution(execution),
                )
            active_batches = await self._fetchone(
                db,
                """SELECT COUNT(DISTINCT d.batch_id) AS count
                   FROM deliveries d JOIN events e ON e.id=d.event_id
                   WHERE e.room_id=? AND e.round_id=? AND d.status='processing'""",
                (room_id, agent["active_round_id"]),
            )
            if agent["round_turn_count"] + (active_batches["count"] or 0) >= agent["max_turns"]:
                await db.rollback()
                return None
            boundary = agent["finish_boundary_sequence"]
            delivery_start = agent["delivery_start_sequence"] or 0
            if boundary is not None:
                await db.execute(
                    """UPDATE deliveries SET status='cancelled', completed_at=?,
                       error='At or before FINISH consumption boundary'
                       WHERE agent_id=? AND status='pending' AND event_id IN (
                         SELECT id FROM events WHERE room_id=? AND round_id=?
                           AND sequence_no<=?
                       )""",
                    (now, agent["id"], room_id, agent["active_round_id"], boundary),
                )
            trigger = await self._fetchone(
                db,
                """SELECT MAX(e.sequence_no) AS max_sequence
                   FROM deliveries d JOIN events e ON e.id=d.event_id
                   WHERE d.agent_id=? AND d.status='pending' AND d.runnable=1
                     AND e.room_id=? AND e.round_id=? AND e.conversational=1
                     AND e.sequence_no>?
                     AND (? IS NULL OR e.sequence_no>?)""",
                (
                    agent["id"],
                    room_id,
                    agent["active_round_id"],
                    delivery_start,
                    boundary,
                    boundary,
                ),
            )
            if trigger is None or trigger["max_sequence"] is None:
                await db.commit()
                return None
            rows = await db.execute_fetchall(
                """SELECT d.id AS delivery_id, d.attempts,
                          d.runnable AS delivery_runnable, e.*
                   FROM deliveries d JOIN events e ON e.id=d.event_id
                   WHERE d.agent_id=? AND d.status='pending' AND e.room_id=?
                     AND e.round_id=? AND e.conversational=1
                     AND e.sequence_no>?
                     AND (? IS NULL OR e.sequence_no>?)
                     AND e.sequence_no<=?
                   ORDER BY e.sequence_no""",
                (
                    agent["id"],
                    room_id,
                    agent["active_round_id"],
                    delivery_start,
                    boundary,
                    boundary,
                    trigger["max_sequence"],
                ),
            )
            if not rows:
                await db.commit()
                return None
            selected_model, selected_effort = self._batch_execution_config(
                rows,
                agent_key,
                default_model=model,
                default_reasoning_effort=reasoning_effort,
            )
            continuation_row = await self._fetchone(
                db,
                """SELECT * FROM usage_continuations
                   WHERE agent_id=? AND room_id=? AND round_id=?
                     AND lifecycle_version=? AND thread_id=? AND state='ready'""",
                (
                    agent["id"],
                    room_id,
                    agent["active_round_id"],
                    agent["lifecycle_version"],
                    agent["thread_id"],
                ),
            )
            delivery_ids = [row["delivery_id"] for row in rows]
            placeholders = ",".join("?" for _ in delivery_ids)
            cursor = await db.execute(
                f"""UPDATE deliveries SET status='processing', attempts=attempts+1,
                   started_at=?, error=NULL, batch_id=?
                   WHERE id IN ({placeholders}) AND status='pending'""",  # noqa: S608
                (now, batch_id, *delivery_ids),
            )
            if cursor.rowcount != len(delivery_ids):
                await db.rollback()
                return None
            await db.execute(
                "UPDATE agents SET status=?, last_error=NULL, updated_at=? WHERE id=?",
                (AgentStatus.RUNNING, now, agent["id"]),
            )
            await db.execute(
                """INSERT INTO agent_executions
                   (batch_id, room_id, agent_id, round_id, lifecycle_version,
                    worker_generation, model, reasoning_effort, state, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'claimed', ?)""",
                (
                    batch_id,
                    room_id,
                    agent["id"],
                    agent["active_round_id"],
                    agent["lifecycle_version"],
                    worker_generation,
                    selected_model,
                    selected_effort,
                    now,
                ),
            )
            if continuation_row is not None:
                cursor = await db.execute(
                    """UPDATE usage_continuations
                       SET state='running', continuation_batch_id=?, updated_at=?
                       WHERE id=? AND state='ready'""",
                    (batch_id, now, continuation_row["id"]),
                )
                if cursor.rowcount != 1:
                    await db.rollback()
                    return None
            await db.commit()
            execution = await self._fetchone(
                db, "SELECT * FROM agent_executions WHERE batch_id=?", (batch_id,)
            )
        return self._claimed_batch(
            agent,
            rows,
            batch_id,
            recovered=False,
            execution=self._decode_execution(execution),
            usage_continuation=(
                self._decode_usage_continuation(continuation_row)
                if continuation_row else None
            ),
        )

    async def claim_next_delivery(
        self,
        room_id: str,
        agent_key: str,
        worker_generation: int = 0,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any] | None:
        """Compatibility alias; the returned unit is now a coalesced batch."""
        return await self.claim_next_batch(
            room_id,
            agent_key,
            worker_generation,
            model=model,
            reasoning_effort=reasoning_effort,
        )

    def _claimed_batch(
        self,
        agent: aiosqlite.Row,
        rows: Iterable[aiosqlite.Row],
        batch_id: str,
        *,
        recovered: bool,
        execution: dict[str, Any],
        usage_continuation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        events = [self._decode_row(row) for row in rows]
        result = dict(agent)
        result.update(
            {
                "batch_id": batch_id,
                "delivery_ids": [event["delivery_id"] for event in events],
                "events": events,
                "discussion_id": agent["active_round_id"],
                "round_id": agent["active_round_id"],
                "max_event_sequence": max(event["sequence_no"] for event in events),
                "triggering_delivery_ids": [
                    event["delivery_id"] for event in events
                    if event.get("delivery_runnable")
                ],
                "triggering_event_ids": [
                    event["id"] for event in events if event.get("delivery_runnable")
                ],
                "passive_event_ids": [
                    event["id"] for event in events if not event.get("delivery_runnable")
                ],
                "recovered": recovered,
                "execution": execution,
                "usage_continuation": usage_continuation,
            }
        )
        return result

    @staticmethod
    def _batch_execution_config(
        rows: Iterable[aiosqlite.Row],
        agent_key: str,
        *,
        default_model: str | None,
        default_reasoning_effort: str | None,
    ) -> tuple[str | None, str | None]:
        """Use only the newest runnable event's explicit C-selected execution config."""
        for row in reversed(list(rows)):
            if not bool(row["delivery_runnable"]):
                continue
            metadata = json.loads(row["metadata_json"] or "{}")
            resolved = metadata.get("resolved_execution_configs")
            selected = resolved.get(agent_key) if isinstance(resolved, dict) else None
            if isinstance(selected, dict):
                model = selected.get("model")
                effort = selected.get("reasoning_effort")
                if isinstance(model, str) and isinstance(effort, str):
                    return model, effort
            break
        return default_model, default_reasoning_effort

    async def has_open_delivery(
        self, room_id: str, agent_key: str, discussion_id: str
    ) -> bool:
        async with self.connect() as db:
            row = await self._fetchone(
                db,
                """SELECT 1
                   FROM deliveries d
                   JOIN events e ON e.id=d.event_id
                   JOIN agents a ON a.id=d.agent_id
                   WHERE e.room_id=? AND e.discussion_id=? AND a.agent_key=?
                     AND d.status IN ('pending', 'processing') AND d.runnable=1
                     AND e.conversational=1
                   LIMIT 1""",
                (room_id, discussion_id, agent_key),
            )
        return row is not None

    async def get_delivery_execution(self, room_id: str) -> dict[str, dict[str, Any]]:
        """Return durable queue/claim evidence keyed by participant."""
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                """SELECT a.agent_key,
                          SUM(CASE WHEN e.id IS NOT NULL AND d.status='pending'
                                    AND d.runnable=1 THEN 1 ELSE 0 END)
                            AS pending_count,
                          SUM(CASE WHEN e.id IS NOT NULL AND d.status='pending'
                                    AND d.runnable=0 THEN 1 ELSE 0 END)
                            AS passive_pending_count,
                          SUM(CASE WHEN e.id IS NOT NULL AND d.status='processing' THEN 1 ELSE 0 END)
                            AS processing_count,
                          MAX(CASE WHEN e.id IS NOT NULL AND d.status='processing'
                                   THEN d.batch_id END) AS batch_id,
                          MIN(CASE WHEN e.id IS NOT NULL AND d.status='processing'
                                   THEN d.started_at END) AS started_at
                   FROM agents a
                   LEFT JOIN deliveries d ON d.agent_id=a.id
                   LEFT JOIN events e ON e.id=d.event_id
                     AND e.room_id=? AND e.round_id=(SELECT active_round_id FROM rooms WHERE id=?)
                   WHERE a.room_id=?
                   GROUP BY a.id, a.agent_key
                   ORDER BY a.agent_key""",
                (room_id, room_id, room_id),
            )
            execution_rows = await db.execute_fetchall(
                """SELECT x.*, a.agent_key FROM agent_executions x
                   JOIN agents a ON a.id=x.agent_id
                   WHERE x.room_id=? AND x.state IN
                     ('claimed','active','recovering','result_ready','usage_suspended','quarantined')
                   ORDER BY x.created_at""",
                (room_id,),
            )
            latest_execution_rows = await db.execute_fetchall(
                """SELECT x.*, a.agent_key
                   FROM agents a
                   JOIN agent_executions x ON x.batch_id=(
                       SELECT x2.batch_id
                       FROM agent_executions x2
                       WHERE x2.room_id=? AND x2.agent_id=a.id AND x2.model IS NOT NULL
                       ORDER BY x2.created_at DESC, x2.batch_id DESC
                       LIMIT 1
                   )
                   WHERE a.room_id=?
                   ORDER BY a.agent_key""",
                (room_id, room_id),
            )
            continuation_rows = await db.execute_fetchall(
                """SELECT u.*, a.agent_key FROM usage_continuations u
                   JOIN agents a ON a.id=u.agent_id
                   WHERE u.room_id=? AND u.state IN ('scheduled','ready','running')""",
                (room_id,),
            )
        executions = {
            row["agent_key"]: self._decode_execution(row) for row in execution_rows
        }
        latest_executions = {
            row["agent_key"]: self._decode_execution(row)
            for row in latest_execution_rows
        }
        continuations = {
            row["agent_key"]: self._decode_usage_continuation(row)
            for row in continuation_rows
        }
        result = {
            row["agent_key"]: {
                "pending_count": int(row["pending_count"] or 0),
                "passive_pending_count": int(row["passive_pending_count"] or 0),
                "processing_count": int(row["processing_count"] or 0),
                "batch_id": row["batch_id"],
                "started_at": row["started_at"],
                "execution": executions.get(row["agent_key"]),
                "last_execution": latest_executions.get(row["agent_key"]),
                "usage_continuation": continuations.get(row["agent_key"]),
            }
            for row in rows
        }
        return result

    async def get_pending_integration_material(
        self, room_id: str, round_id: str, integrator_key: str = "agent_c"
    ) -> list[dict[str, Any]]:
        """Return unread passive peer MESSAGE deliveries awaiting integration."""
        async with self.connect() as db:
            rows = await db.execute_fetchall(
                """SELECT e.id, e.source, e.sequence_no
                   FROM deliveries d
                   JOIN events e ON e.id=d.event_id
                   JOIN agents a ON a.id=d.agent_id
                   WHERE e.room_id=? AND e.round_id=? AND a.agent_key=?
                     AND d.status='pending' AND d.runnable=0
                     AND e.event_type='agent_message' AND e.source<>?
                   ORDER BY e.sequence_no""",
                (room_id, round_id, integrator_key, integrator_key),
            )
        return [dict(row) for row in rows]

    async def get_delivery_participation(
        self, room_id: str, agent_key: str, round_id: str
    ) -> dict[str, int]:
        """Count durable readable and runnable deliveries for settlement membership."""
        async with self.connect() as db:
            row = await self._fetchone(
                db,
                """SELECT COUNT(*) AS readable_count,
                          SUM(CASE WHEN d.runnable=1 THEN 1 ELSE 0 END) AS runnable_count
                   FROM deliveries d
                   JOIN events e ON e.id=d.event_id
                   JOIN agents a ON a.id=d.agent_id
                   WHERE e.room_id=? AND e.round_id=? AND a.agent_key=?
                     AND e.conversational=1""",
                (room_id, round_id, agent_key),
            )
        return {
            "readable_count": int(row["readable_count"] or 0) if row else 0,
            "runnable_count": int(row["runnable_count"] or 0) if row else 0,
        }

    async def bind_execution_turn(
        self,
        batch_id: str,
        thread_id: str,
        turn_id: str,
        worker_generation: int,
    ) -> bool:
        """Durably bind a claimed Room batch to its one exact Codex turn."""
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            row = await self._fetchone(
                db, "SELECT * FROM agent_executions WHERE batch_id=?", (batch_id,)
            )
            if row is None:
                await db.rollback()
                return False
            if row["sdk_thread_id"] == thread_id and row["sdk_turn_id"] == turn_id:
                await db.commit()
                return True
            if row["state"] != "claimed" or row["worker_generation"] != worker_generation:
                await db.rollback()
                return False
            processing = await self._fetchone(
                db,
                "SELECT COUNT(*) AS count FROM deliveries WHERE batch_id=? AND status='processing'",
                (batch_id,),
            )
            assignment_live = False
            if row["assignment_id"] is not None:
                assignment = await self._fetchone(
                    db,
                    """SELECT 1 FROM assignments
                       WHERE id=? AND agent_id=? AND state='running'""",
                    (row["assignment_id"], row["agent_id"]),
                )
                assignment_live = assignment is not None
            if (processing is None or not processing["count"]) and not assignment_live:
                await db.rollback()
                return False
            try:
                cursor = await db.execute(
                    """UPDATE agent_executions
                       SET sdk_thread_id=?, sdk_turn_id=?, state='active',
                           turn_started_at=?, last_reconciled_at=?,
                           last_verified_progress_at=?
                       WHERE batch_id=? AND state='claimed' AND worker_generation=?""",
                    (thread_id, turn_id, now, now, now, batch_id, worker_generation),
                )
            except aiosqlite.IntegrityError:
                await db.rollback()
                return False
            if cursor.rowcount != 1:
                await db.rollback()
                return False
            await db.commit()
        return True

    async def touch_execution_progress(self, batch_id: str) -> None:
        now = utc_now()
        async with self.connect() as db:
            await db.execute(
                """UPDATE agent_executions
                   SET last_reconciled_at=?, last_verified_progress_at=?
                   WHERE batch_id=? AND state IN ('active','recovering')""",
                (now, now, batch_id),
            )
            await db.commit()

    async def record_execution_result(
        self,
        batch_id: str,
        result: dict[str, Any],
        usage: dict[str, Any] | None,
        activity: list[dict[str, Any]],
        completion_source: str,
    ) -> bool:
        """Persist a terminal result before any Room-side settlement effects."""
        now = utc_now()
        result_json = json.dumps(result, ensure_ascii=False)
        usage_json = json.dumps(usage, ensure_ascii=False) if usage is not None else None
        activity_json = json.dumps(activity, ensure_ascii=False)
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            row = await self._fetchone(
                db, "SELECT * FROM agent_executions WHERE batch_id=?", (batch_id,)
            )
            if row is None:
                await db.rollback()
                return False
            if row["state"] in {"result_ready", "settled"}:
                matches = row["result_json"] == result_json
                if matches:
                    await db.commit()
                else:
                    await db.rollback()
                return matches
            if row["state"] not in {"active", "recovering", "cancelled", "stale"}:
                await db.rollback()
                return False
            cursor = await db.execute(
                """UPDATE agent_executions SET state='result_ready', result_json=?,
                   usage_json=?, activity_json=?, completion_source=?,
                   result_recorded_at=?, last_reconciled_at=?, error=NULL
                   WHERE batch_id=? AND state IN ('active','recovering','cancelled','stale')""",
                (
                    result_json,
                    usage_json,
                    activity_json,
                    completion_source,
                    now,
                    now,
                    batch_id,
                ),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                return False
            await db.commit()
        return True

    async def set_execution_state(
        self, batch_id: str, state: str, error: str | None = None
    ) -> None:
        now = utc_now()
        terminal = now if state in {"settled", "failed", "cancelled", "stale"} else None
        async with self.connect() as db:
            await db.execute(
                """UPDATE agent_executions SET state=?, error=?,
                   last_reconciled_at=?, settled_at=COALESCE(?, settled_at)
                   WHERE batch_id=?""",
                (state, error, now, terminal, batch_id),
            )
            await db.commit()

    async def get_execution(self, batch_id: str) -> dict[str, Any] | None:
        async with self.connect() as db:
            row = await self._fetchone(
                db, "SELECT * FROM agent_executions WHERE batch_id=?", (batch_id,)
            )
        return self._decode_execution(row) if row else None

    async def get_execution_usage_baseline(self, batch_id: str) -> dict[str, Any]:
        """Return the nearest prior usage snapshot on this exact persistent SDK thread."""
        async with self.connect() as db:
            current = await self._fetchone(
                db,
                """SELECT rowid AS execution_rowid, agent_id, sdk_thread_id
                   FROM agent_executions WHERE batch_id=?""",
                (batch_id,),
            )
            if current is None or not current["sdk_thread_id"]:
                return {"has_prior_execution": False, "usage": None}
            prior = await self._fetchone(
                db,
                """SELECT usage_json FROM agent_executions
                   WHERE agent_id=? AND sdk_thread_id=? AND rowid<?
                   ORDER BY rowid DESC LIMIT 1""",
                (
                    current["agent_id"],
                    current["sdk_thread_id"],
                    current["execution_rowid"],
                ),
            )
        if prior is None:
            return {"has_prior_execution": False, "usage": None}
        return {
            "has_prior_execution": True,
            "usage": (
                json.loads(prior["usage_json"])
                if prior["usage_json"] is not None
                else None
            ),
        }

    async def get_usage_continuation(
        self, room_id: str, agent_key: str
    ) -> dict[str, Any] | None:
        async with self.connect() as db:
            row = await self._fetchone(
                db,
                """SELECT u.* FROM usage_continuations u
                   JOIN agents a ON a.id=u.agent_id
                   WHERE u.room_id=? AND a.agent_key=?""",
                (room_id, agent_key),
            )
        return self._decode_usage_continuation(row) if row else None

    async def suspend_usage_continuation(
        self,
        batch: dict[str, Any],
        agent: dict[str, Any],
        *,
        reported_retry_at: str,
        wake_at: str,
        diagnostic: str,
        worker_generation: int,
    ) -> dict[str, Any] | None:
        """Atomically park one exact failed execution until its reported reset."""
        now = utc_now()
        continuation_id = new_id("usage")
        input_ids = [event["id"] for event in batch["events"]]
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            current = await self._fetchone(
                db,
                """SELECT r.status, r.active_round_id, r.lifecycle_version,
                          a.thread_id
                   FROM rooms r JOIN agents a ON a.room_id=r.id
                   WHERE r.id=? AND a.id=?""",
                (batch["room_id"], agent["id"]),
            )
            execution = await self._fetchone(
                db,
                "SELECT state FROM agent_executions WHERE batch_id=?",
                (batch["batch_id"],),
            )
            if (
                current is None
                or execution is None
                or current["status"] != RoomStatus.RUNNING
                or current["active_round_id"] != batch["round_id"]
                or current["lifecycle_version"] != batch["lifecycle_version"]
                or current["thread_id"] != agent["thread_id"]
                or execution["state"] not in {"active", "recovering"}
            ):
                await db.rollback()
                return None
            cursor = await db.execute(
                """UPDATE agent_executions
                   SET state='usage_suspended', error=?, last_reconciled_at=?
                   WHERE batch_id=? AND state IN ('active','recovering')""",
                (diagnostic[:4000], now, batch["batch_id"]),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                return None
            await db.execute(
                """INSERT INTO usage_continuations
                   (id, room_id, agent_id, thread_id, source_batch_id, round_id,
                    lifecycle_version, worker_generation, input_event_ids_json,
                    triggering_event_ids_json, reported_retry_at, wake_at, state,
                    created_at, updated_at, last_error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?, ?)
                   ON CONFLICT(agent_id) DO UPDATE SET
                     thread_id=excluded.thread_id,
                     source_batch_id=excluded.source_batch_id,
                     round_id=excluded.round_id,
                     lifecycle_version=excluded.lifecycle_version,
                     worker_generation=excluded.worker_generation,
                     input_event_ids_json=excluded.input_event_ids_json,
                     triggering_event_ids_json=excluded.triggering_event_ids_json,
                     reported_retry_at=excluded.reported_retry_at,
                     wake_at=excluded.wake_at,
                     state='scheduled', continuation_batch_id=NULL,
                     reschedule_count=usage_continuations.reschedule_count+1,
                     updated_at=excluded.updated_at, fired_at=NULL,
                     completed_at=NULL, last_error=excluded.last_error""",
                (
                    continuation_id,
                    batch["room_id"],
                    agent["id"],
                    agent["thread_id"],
                    batch["batch_id"],
                    batch["round_id"],
                    batch["lifecycle_version"],
                    worker_generation,
                    json.dumps(input_ids),
                    json.dumps(batch["triggering_event_ids"]),
                    reported_retry_at,
                    wake_at,
                    now,
                    now,
                    diagnostic[:4000],
                ),
            )
            await db.execute(
                "UPDATE agents SET status=?, last_error=NULL, updated_at=? WHERE id=?",
                (AgentStatus.USAGE_SUSPENDED, now, agent["id"]),
            )
            row = await self._fetchone(
                db, "SELECT * FROM usage_continuations WHERE agent_id=?", (agent["id"],)
            )
            await db.commit()
        assert row is not None
        return self._decode_usage_continuation(row)

    async def suspend_transaction_usage_continuation(
        self,
        batch: dict[str, Any],
        agent: dict[str, Any],
        *,
        reported_retry_at: str,
        wake_at: str,
        diagnostic: str,
        worker_generation: int,
    ) -> dict[str, Any] | None:
        """Park one exact version-2 assignment execution until the provider reset."""
        now = utc_now()
        continuation_id = new_id("usage")
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            current = await self._fetchone(
                db,
                """SELECT r.status, r.active_round_id, r.lifecycle_version,
                          a.thread_id, x.state AS assignment_state
                   FROM rooms r
                   JOIN agents a ON a.room_id=r.id
                   JOIN assignments x ON x.id=?
                   WHERE r.id=? AND a.id=? AND x.agent_id=a.id""",
                (batch["assignment_id"], batch["room_id"], agent["id"]),
            )
            execution = await self._fetchone(
                db,
                "SELECT state, assignment_id FROM agent_executions WHERE batch_id=?",
                (batch["batch_id"],),
            )
            if (
                current is None
                or execution is None
                or current["status"] != RoomStatus.RUNNING
                or current["active_round_id"] != batch["round_id"]
                or current["lifecycle_version"] != batch["lifecycle_version"]
                or current["thread_id"] != agent["thread_id"]
                or current["assignment_state"] != "running"
                or execution["assignment_id"] != batch["assignment_id"]
                or execution["state"] not in {"active", "recovering"}
            ):
                await db.rollback()
                return None
            cursor = await db.execute(
                """UPDATE agent_executions
                   SET state='usage_suspended', error=?, last_reconciled_at=?
                   WHERE batch_id=? AND state IN ('active','recovering')""",
                (diagnostic[:4000], now, batch["batch_id"]),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                return None
            await db.execute(
                """INSERT INTO usage_continuations
                   (id, room_id, agent_id, thread_id, source_batch_id,
                    assignment_id, round_id, lifecycle_version, worker_generation,
                    input_event_ids_json, triggering_event_ids_json,
                    reported_retry_at, wake_at, state, created_at, updated_at, last_error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', '[]', ?, ?,
                           'scheduled', ?, ?, ?)
                   ON CONFLICT(agent_id) DO UPDATE SET
                     thread_id=excluded.thread_id,
                     source_batch_id=excluded.source_batch_id,
                     assignment_id=excluded.assignment_id,
                     round_id=excluded.round_id,
                     lifecycle_version=excluded.lifecycle_version,
                     worker_generation=excluded.worker_generation,
                     input_event_ids_json='[]',
                     triggering_event_ids_json='[]',
                     reported_retry_at=excluded.reported_retry_at,
                     wake_at=excluded.wake_at,
                     state='scheduled', continuation_batch_id=NULL,
                     reschedule_count=usage_continuations.reschedule_count+1,
                     updated_at=excluded.updated_at, fired_at=NULL,
                     completed_at=NULL, last_error=excluded.last_error""",
                (
                    continuation_id,
                    batch["room_id"],
                    agent["id"],
                    agent["thread_id"],
                    batch["batch_id"],
                    batch["assignment_id"],
                    batch["round_id"],
                    batch["lifecycle_version"],
                    worker_generation,
                    reported_retry_at,
                    wake_at,
                    now,
                    now,
                    diagnostic[:4000],
                ),
            )
            await db.execute(
                "UPDATE agents SET status=?, last_error=NULL, updated_at=? WHERE id=?",
                (AgentStatus.USAGE_SUSPENDED, now, agent["id"]),
            )
            row = await self._fetchone(
                db, "SELECT * FROM usage_continuations WHERE agent_id=?", (agent["id"],)
            )
            await db.commit()
        assert row is not None
        return self._decode_usage_continuation(row)

    async def release_due_usage_continuations(
        self, room_id: str, now: str
    ) -> list[dict[str, Any]]:
        """Make due legacy deliveries or version-2 assignments claimable again."""
        outcomes: list[dict[str, Any]] = []
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            rows = await db.execute_fetchall(
                """SELECT u.*, a.agent_key, a.status AS agent_status,
                          a.thread_id AS current_thread_id,
                          r.status AS room_status, r.active_round_id,
                          r.lifecycle_version AS current_lifecycle_version,
                          ro.status AS round_status, x.state AS execution_state,
                          tx.state AS assignment_state
                   FROM usage_continuations u
                   JOIN agents a ON a.id=u.agent_id
                   JOIN rooms r ON r.id=u.room_id
                   LEFT JOIN rounds ro ON ro.id=u.round_id
                   LEFT JOIN agent_executions x ON x.batch_id=u.source_batch_id
                   LEFT JOIN assignments tx ON tx.id=u.assignment_id
                   WHERE u.room_id=? AND u.state='scheduled' AND u.wake_at<=?
                   ORDER BY u.wake_at""",
                (room_id, now),
            )
            for row in rows:
                base_valid = (
                    row["room_status"] == RoomStatus.RUNNING
                    and row["active_round_id"] == row["round_id"]
                    and row["current_lifecycle_version"] == row["lifecycle_version"]
                    and row["round_status"] == RoundStatus.ACTIVE
                    and row["current_thread_id"] == row["thread_id"]
                    and row["agent_status"] == AgentStatus.USAGE_SUSPENDED
                    and row["execution_state"] == "usage_suspended"
                )
                if row["assignment_id"] is not None:
                    valid = base_valid and row["assignment_state"] == "running"
                    if valid:
                        cursor = await db.execute(
                            """UPDATE assignments SET state='queued', updated_at=?
                               WHERE id=? AND agent_id=? AND state='running'""",
                            (now, row["assignment_id"], row["agent_id"]),
                        )
                        if cursor.rowcount != 1:
                            valid = False
                    if valid:
                        await db.execute(
                            """UPDATE agent_executions
                               SET state='usage_released', settled_at=?,
                                   last_reconciled_at=?
                               WHERE batch_id=? AND state='usage_suspended'""",
                            (now, now, row["source_batch_id"]),
                        )
                        await db.execute(
                            """UPDATE usage_continuations
                               SET state='ready', fired_at=?, updated_at=?
                               WHERE id=? AND state='scheduled'""",
                            (now, now, row["id"]),
                        )
                        await db.execute(
                            "UPDATE agents SET status=?, updated_at=? WHERE id=?",
                            (AgentStatus.IDLE, now, row["agent_id"]),
                        )
                        state = "fired"
                        reason = None
                    else:
                        reason = (
                            "Scheduled transaction usage continuation is stale under "
                            "current lifecycle or assignment state"
                        )
                        await db.execute(
                            """UPDATE assignments
                               SET state='cancelled', updated_at=?, completed_at=?,
                                   resolution_reason=?
                               WHERE id=? AND state='running'""",
                            (now, now, reason, row["assignment_id"]),
                        )
                        await db.execute(
                            """UPDATE agent_executions
                               SET state='cancelled', settled_at=?, error=?
                               WHERE batch_id=? AND state='usage_suspended'""",
                            (now, reason, row["source_batch_id"]),
                        )
                        await db.execute(
                            """UPDATE usage_continuations SET state='cancelled',
                               completed_at=?, updated_at=?, last_error=? WHERE id=?""",
                            (now, now, reason, row["id"]),
                        )
                        await db.execute(
                            """UPDATE agents SET status=?, updated_at=?
                               WHERE id=? AND status=?""",
                            (
                                AgentStatus.IDLE,
                                now,
                                row["agent_id"],
                                AgentStatus.USAGE_SUSPENDED,
                            ),
                        )
                        state = "cancelled"
                else:
                    expected = json.loads(row["input_event_ids_json"] or "[]")
                    delivery = await self._fetchone(
                        db,
                        """SELECT COUNT(*) AS count FROM deliveries
                           WHERE agent_id=? AND batch_id=? AND status='processing'""",
                        (row["agent_id"], row["source_batch_id"]),
                    )
                    valid = (
                        base_valid
                        and delivery is not None
                        and delivery["count"] == len(expected)
                        and bool(expected)
                    )
                    if valid:
                        await db.execute(
                            """UPDATE deliveries SET status='pending', attempts=CASE
                                 WHEN attempts>0 THEN attempts-1 ELSE 0 END,
                               started_at=NULL, completed_at=NULL, error=NULL, batch_id=NULL
                               WHERE agent_id=? AND batch_id=? AND status='processing'""",
                            (row["agent_id"], row["source_batch_id"]),
                        )
                        await db.execute(
                            """UPDATE agent_executions
                               SET state='usage_released', settled_at=?,
                                   last_reconciled_at=?
                               WHERE batch_id=? AND state='usage_suspended'""",
                            (now, now, row["source_batch_id"]),
                        )
                        await db.execute(
                            """UPDATE usage_continuations SET state='ready', fired_at=?,
                               updated_at=? WHERE id=? AND state='scheduled'""",
                            (now, now, row["id"]),
                        )
                        await db.execute(
                            "UPDATE agents SET status=?, updated_at=? WHERE id=?",
                            (AgentStatus.IDLE, now, row["agent_id"]),
                        )
                        state = "fired"
                        reason = None
                    else:
                        reason = (
                            "Scheduled usage continuation is stale under current "
                            "lifecycle state"
                        )
                        await db.execute(
                            """UPDATE deliveries SET status='cancelled',
                               completed_at=?, error=?
                               WHERE agent_id=? AND batch_id=?
                                 AND status='processing'""",
                            (now, reason, row["agent_id"], row["source_batch_id"]),
                        )
                        await db.execute(
                            """UPDATE agent_executions SET state='cancelled',
                               settled_at=?, error=?
                               WHERE batch_id=? AND state='usage_suspended'""",
                            (now, reason, row["source_batch_id"]),
                        )
                        await db.execute(
                            """UPDATE usage_continuations SET state='cancelled',
                               completed_at=?, updated_at=?, last_error=? WHERE id=?""",
                            (now, now, reason, row["id"]),
                        )
                        await db.execute(
                            """UPDATE agents SET status=?, updated_at=?
                               WHERE id=? AND status=?""",
                            (
                                AgentStatus.IDLE,
                                now,
                                row["agent_id"],
                                AgentStatus.USAGE_SUSPENDED,
                            ),
                        )
                        state = "cancelled"
                item = self._decode_usage_continuation(row)
                item.update({"agent_key": row["agent_key"], "outcome": state})
                item["last_error"] = reason
                outcomes.append(item)
            await db.commit()
        return outcomes

    async def finish_usage_continuation(
        self,
        continuation_id: str,
        batch_id: str,
        state: str,
        error: str | None = None,
    ) -> bool:
        if state not in {"completed", "failed", "cancelled", "ready"}:
            raise ValueError("Invalid usage continuation terminal state")
        now = utc_now()
        async with self.connect() as db:
            cursor = await db.execute(
                """UPDATE usage_continuations SET state=?, updated_at=?,
                   completed_at=CASE WHEN ?='ready' THEN NULL ELSE ? END,
                   continuation_batch_id=CASE WHEN ?='ready' THEN NULL
                     ELSE continuation_batch_id END, last_error=?
                   WHERE id=? AND continuation_batch_id=? AND state='running'""",
                (state, now, state, now, state, error, continuation_id, batch_id),
            )
            await db.commit()
        return cursor.rowcount == 1

    async def recover_agent_processing(self, room_id: str, agent_id: str) -> int:
        """Requeue an orphaned claim only after the runtime proves execution absent."""
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute(
                """UPDATE deliveries SET status='pending', started_at=NULL, batch_id=NULL,
                          completed_at=NULL, error='Recovered orphaned in-process worker'
                   WHERE agent_id=? AND status='processing' AND event_id IN (
                     SELECT id FROM events WHERE room_id=?
                       AND round_id=(SELECT active_round_id FROM rooms WHERE id=?)
                   )""",
                (agent_id, room_id, room_id),
            )
            if cursor.rowcount:
                await db.execute(
                    "UPDATE agents SET status=?, updated_at=? WHERE id=? AND status=?",
                    (AgentStatus.IDLE, now, agent_id, AgentStatus.RUNNING),
                )
            await db.commit()
        return cursor.rowcount

    async def complete_deliveries(
        self, delivery_ids: list[str], *, batch_id: str | None = None
    ) -> bool:
        if not delivery_ids:
            return True
        placeholders = ",".join("?" for _ in delivery_ids)
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute(
                f"""UPDATE deliveries SET status='delivered', completed_at=?, consumed_at=?
                   WHERE id IN ({placeholders}) AND status='processing'
                     {"AND batch_id=?" if batch_id is not None else ""}""",  # noqa: S608
                (utc_now(), utc_now(), *delivery_ids, *((batch_id,) if batch_id is not None else ())),
            )
            if cursor.rowcount != len(delivery_ids):
                delivered = await self._fetchone(
                    db,
                    f"""SELECT COUNT(*) AS count FROM deliveries
                        WHERE id IN ({placeholders}) AND status='delivered'
                          {"AND batch_id=?" if batch_id is not None else ""}""",  # noqa: S608
                    (*delivery_ids, *((batch_id,) if batch_id is not None else ())),
                )
                if delivered is None or delivered["count"] != len(delivery_ids):
                    await db.rollback()
                    return False
            await db.commit()
        return True

    async def complete_delivery(self, delivery_id: str) -> None:
        await self.complete_deliveries([delivery_id])

    async def fail_delivery(
        self,
        delivery_id: str,
        error: str,
        retry: bool,
        *,
        batch_id: str | None = None,
    ) -> bool:
        return bool(
            await self.fail_deliveries(
                [delivery_id], error, retry, batch_id=batch_id
            )
        )

    async def fail_deliveries(
        self,
        delivery_ids: list[str],
        error: str,
        retry: bool,
        *,
        batch_id: str | None = None,
    ) -> int:
        if not delivery_ids:
            return 0
        placeholders = ",".join("?" for _ in delivery_ids)
        batch_clause = " AND batch_id=?" if batch_id is not None else ""
        params: list[Any] = [
            "pending" if retry else "failed",
            utc_now(),
            error[:4000],
            *delivery_ids,
        ]
        if batch_id is not None:
            params.append(batch_id)
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute(
                f"""UPDATE deliveries SET status=?, completed_at=?, error=?
                    WHERE id IN ({placeholders}) AND status='processing'{batch_clause}""",  # noqa: S608
                params,
            )
            if cursor.rowcount != len(delivery_ids):
                await db.rollback()
                return 0
            await db.commit()
        return cursor.rowcount

    async def cancel_pending_deliveries(self, room_id: str, discussion_id: str | None = None) -> None:
        params: list[Any] = [utc_now(), room_id]
        extra = ""
        if discussion_id is not None:
            extra = " AND e.discussion_id=?"
            params.append(discussion_id)
        async with self.connect() as db:
            await db.execute(
                f"""UPDATE deliveries SET status='cancelled', completed_at=?
                    WHERE id IN (
                      SELECT d.id FROM deliveries d JOIN events e ON e.id=d.event_id
                      WHERE e.room_id=? AND d.status IN ('pending','processing'){extra}
                    )""",  # noqa: S608
                params,
            )
            execution_params: list[Any] = [utc_now(), room_id]
            execution_extra = ""
            if discussion_id is not None:
                execution_extra = " AND round_id=?"
                execution_params.append(discussion_id)
            await db.execute(
                f"""UPDATE agent_executions
                    SET state='cancelled', settled_at=?, error='Cancelled by Room lifecycle change'
                    WHERE room_id=? AND state IN
                      ('claimed','active','recovering','result_ready','usage_suspended')
                    {execution_extra}""",  # noqa: S608
                execution_params,
            )
            continuation_params: list[Any] = [utc_now(), utc_now(), room_id]
            continuation_extra = ""
            if discussion_id is not None:
                continuation_extra = " AND round_id=?"
                continuation_params.append(discussion_id)
            await db.execute(
                f"""UPDATE usage_continuations
                    SET state='cancelled', completed_at=?, updated_at=?,
                        last_error='Cancelled by Room lifecycle change'
                    WHERE room_id=? AND state IN ('scheduled','ready','running')
                    {continuation_extra}""",  # noqa: S608
                continuation_params,
            )
            await db.commit()

    async def register_decision(
        self,
        room_id: str,
        round_id: str,
        agent_id: str,
        outcome: str,
        finish_boundary_sequence: int,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        passed = outcome == "PASS"
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            if execution_id is not None:
                execution = await self._fetchone(
                    db,
                    "SELECT state, decision_recorded_at FROM agent_executions WHERE batch_id=?",
                    (execution_id,),
                )
                if execution is None or execution["state"] not in {"result_ready", "settled"}:
                    await db.rollback()
                    raise RuntimeError("Execution is not ready for decision settlement")
                if execution["decision_recorded_at"] is not None:
                    row = await self._fetchone(db, "SELECT * FROM rounds WHERE id=?", (round_id,))
                    await db.commit()
                    assert row is not None
                    result = dict(row)
                    result["_decision_applied"] = False
                    return result
            await db.execute(
                """UPDATE rooms SET turn_count=turn_count+1,
                   consecutive_passes=CASE WHEN ? THEN consecutive_passes+1 ELSE 0 END,
                   updated_at=? WHERE id=?""",
                (1 if passed else 0, now, room_id),
            )
            await db.execute(
                """UPDATE rounds SET turn_count=turn_count+1,
                   consecutive_passes=CASE WHEN ? THEN consecutive_passes+1 ELSE 0 END
                   WHERE id=? AND room_id=? AND status=?""",
                (1 if passed else 0, round_id, room_id, RoundStatus.ACTIVE),
            )
            await db.execute(
                """UPDATE round_agent_state SET last_outcome=?,
                   finish_boundary_sequence=CASE WHEN ?='FINISH' THEN ?
                     ELSE finish_boundary_sequence END
                   WHERE round_id=? AND agent_id=?""",
                (
                    outcome,
                    outcome,
                    finish_boundary_sequence,
                    round_id,
                    agent_id,
                ),
            )
            if execution_id is not None:
                cursor = await db.execute(
                    """UPDATE agent_executions SET decision_recorded_at=?
                       WHERE batch_id=? AND decision_recorded_at IS NULL""",
                    (now, execution_id),
                )
                if cursor.rowcount != 1:
                    await db.rollback()
                    raise RuntimeError("Execution decision settlement lost its compare-and-set")
            row = await self._fetchone(db, "SELECT * FROM rounds WHERE id=?", (round_id,))
            await db.commit()
        assert row is not None
        result = dict(row)
        result["_decision_applied"] = True
        return result

    async def close_discussion(
        self, room_id: str, discussion_id: str, reason: str, content: str
    ) -> dict[str, Any]:
        """Atomically close a live discussion and write its audit event."""
        event_id = new_id("event")
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute(
                """UPDATE rooms SET status=?, updated_at=?
                   WHERE id=? AND discussion_id=? AND status=?""",
                (
                    RoomStatus.FINISHED,
                    now,
                    room_id,
                    discussion_id,
                    RoomStatus.RUNNING,
                ),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                raise ValueError("Discussion is no longer live and cannot be closed")
            await db.execute(
                """UPDATE rounds SET status=?, ended_at=?, close_reason=?
                   WHERE id=? AND room_id=?""",
                (RoundStatus.FINISHED, now, reason, discussion_id, room_id),
            )
            await db.execute(
                """UPDATE deliveries SET status='cancelled', completed_at=?
                   WHERE id IN (
                     SELECT d.id FROM deliveries d JOIN events e ON e.id=d.event_id
                     WHERE e.room_id=? AND e.discussion_id=?
                       AND d.status IN ('pending','processing') AND d.runnable=1
                   )""",
                (now, room_id, discussion_id),
            )
            await db.execute(
                """UPDATE agents SET status=?, last_error=NULL, updated_at=?
                   WHERE room_id=?""",
                (AgentStatus.FINISHED, now, room_id),
            )
            sequence_cursor = await db.execute(
                """SELECT COALESCE(MAX(sequence_no), 0) + 1 AS next_sequence
                   FROM events WHERE room_id=?""",
                (room_id,),
            )
            sequence_no = (await sequence_cursor.fetchone())["next_sequence"]
            await db.execute(
                """INSERT INTO events
                (id, room_id, discussion_id, created_at, event_type, source,
                 destination, content, related_event_id, status, metadata_json,
                 round_id, sequence_no, event_class, conversational,
                 counts_as_turn, counts_toward_pass)
                VALUES (?, ?, ?, ?, 'discussion_closed', 'room', 'observer',
                        ?, NULL, 'recorded', ?, ?, ?, 'lifecycle', 0, 0, 0)""",
                (
                    event_id,
                    room_id,
                    discussion_id,
                    now,
                    content,
                    json.dumps({"reason": reason}, ensure_ascii=False),
                    discussion_id,
                    sequence_no,
                ),
            )
            await db.commit()
        event = await self.get_event(event_id)
        assert event is not None
        return event

    async def begin_new_topic(self, room_id: str, topic: str) -> tuple[str, str]:
        room = await self.get_room(room_id)
        if room is None:
            raise KeyError(room_id)
        old_id = room["discussion_id"]
        prepared = await self.prepare_round(
            room_id, PrepareRoundRequest(title="Legacy new topic", prompt=topic)
        )
        await self.start_round(room_id, prepared["id"])
        return old_id, prepared["id"]

    async def stop_active_round(self, room_id: str, reason: str) -> None:
        now = utc_now()
        async with self.connect() as db:
            await db.execute(
                """UPDATE rounds SET status=?, ended_at=COALESCE(ended_at, ?),
                   close_reason=? WHERE id=(SELECT active_round_id FROM rooms WHERE id=?)
                   AND status IN (?, ?)""",
                (
                    RoundStatus.STOPPED,
                    now,
                    reason,
                    room_id,
                    RoundStatus.ACTIVE,
                    RoundStatus.PREPARING,
                ),
            )
            await db.commit()

    async def invalidate_inflight(self, room_id: str) -> None:
        async with self.connect() as db:
            await db.execute(
                "UPDATE rooms SET lifecycle_version=lifecycle_version+1, updated_at=? WHERE id=?",
                (utc_now(), room_id),
            )
            await db.commit()

    async def resume_active_round(self, room_id: str) -> None:
        now = utc_now()
        async with self.connect() as db:
            await db.execute(
                """UPDATE rounds SET status=?, ended_at=NULL, close_reason=NULL,
                   last_activity_at=?
                   WHERE id=(SELECT active_round_id FROM rooms WHERE id=?)""",
                (RoundStatus.ACTIVE, now, room_id),
            )
            await db.commit()

    async def reset_room_threads(self, room_id: str) -> list[str]:
        agents = await self.get_agents(room_id)
        old_ids = [a["thread_id"] for a in agents if a.get("thread_id")]
        async with self.connect() as db:
            await db.execute(
                """UPDATE agents SET thread_id=NULL, status=?, last_error=NULL, updated_at=?
                   WHERE room_id=?""",
                (AgentStatus.INITIALIZING, utc_now(), room_id),
            )
            await db.commit()
        return old_ids

    async def replace_agent_threads(self, room_id: str, thread_ids: dict[str, str]) -> None:
        now = utc_now()
        async with self.connect() as db:
            await db.execute("BEGIN IMMEDIATE")
            for key, thread_id in thread_ids.items():
                await db.execute(
                    """UPDATE agents SET thread_id=?, status=?, last_error=NULL, updated_at=?
                       WHERE room_id=? AND agent_key=?""",
                    (thread_id, AgentStatus.IDLE, now, room_id, key),
                )
            await db.commit()

    async def _fetchone(
        self, db: aiosqlite.Connection, query: str, params: tuple[Any, ...]
    ) -> aiosqlite.Row | None:
        cursor = await db.execute(query, params)
        return await cursor.fetchone()

    @staticmethod
    async def _ensure_column(
        db: aiosqlite.Connection, table: str, column: str, definition: str
    ) -> None:
        rows = await db.execute_fetchall(f"PRAGMA table_info({table})")
        if column not in {row[1] for row in rows}:
            await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    @staticmethod
    def _round_status_for_room(status: str) -> RoundStatus:
        if status in {RoomStatus.CREATING, RoomStatus.PREPARING}:
            return RoundStatus.PREPARING
        if status == RoomStatus.FINISHED:
            return RoundStatus.FINISHED
        if status in {
            RoomStatus.STOPPED,
            RoomStatus.ROLLING_OVER,
            RoomStatus.ARCHIVED,
            RoomStatus.ERROR,
        }:
            return RoundStatus.STOPPED
        return RoundStatus.ACTIVE

    @staticmethod
    def _decode_row(row: aiosqlite.Row) -> dict[str, Any]:
        result = dict(row)
        if "metadata_json" in result:
            result["metadata"] = json.loads(result.pop("metadata_json") or "{}")
        for key in (
            "conversational",
            "counts_as_turn",
            "counts_toward_pass",
            "agent_readable",
            "turn_triggering",
            "delivery_runnable",
        ):
            if key in result:
                result[key] = bool(result[key])
        return result

    @staticmethod
    def _decode_execution(row: aiosqlite.Row) -> dict[str, Any]:
        result = dict(row)
        for source, target, fallback in (
            ("result_json", "result", None),
            ("usage_json", "usage", None),
            ("activity_json", "activity", []),
        ):
            raw = result.pop(source, None)
            result[target] = json.loads(raw) if raw is not None else fallback
        return result

    @staticmethod
    def _decode_usage_continuation(row: aiosqlite.Row) -> dict[str, Any]:
        result = dict(row)
        result["input_event_ids"] = json.loads(
            result.pop("input_event_ids_json") or "[]"
        )
        result["triggering_event_ids"] = json.loads(
            result.pop("triggering_event_ids_json") or "[]"
        )
        return result

    @staticmethod
    def _decode_round(row: aiosqlite.Row) -> dict[str, Any]:
        result = dict(row)
        private = json.loads(result.pop("participant_private_json", "{}") or "{}")
        overlays = json.loads(result.pop("participant_overlays_json", "{}") or "{}")
        required_contributors = json.loads(
            result.pop("required_contributors_json", "[]") or "[]"
        )
        # Preserve legacy A/B rows without synthesizing absent C configuration.
        for key in ("agent_a", "agent_b"):
            old_private = result.get(f"{key}_private")
            old_overlay = result.get(f"{key}_overlay")
            if old_private is not None and key not in private:
                private[key] = old_private
            if old_overlay is not None and key not in overlays:
                overlays[key] = old_overlay
        result["participant_private"] = private
        result["participant_overlays"] = overlays
        result["required_contributors"] = required_contributors
        return result

    @staticmethod
    def _effective_instructions(
        agent_key: str,
        name: str,
        profile: str,
        override: str | None,
    ) -> str:
        personality = override.strip() if override and override.strip() else profile.strip()
        return compose_agent_instructions(agent_key, name, personality)

    @staticmethod
    def _event_traits(event_type: str) -> tuple[str, bool, bool, bool, bool, bool, str]:
        if event_type in {"observer_message", "round_start_turn", "topic"}:
            return "conversation", True, False, False, True, True, "public"
        if event_type == "agent_message":
            return "conversation", True, True, False, True, True, "public"
        if event_type == "agent_pass":
            return "conversation", True, True, True, False, False, "public"
        if event_type in {"agent_finish", "agent_reopened"}:
            return (
                "conversation",
                True,
                event_type == "agent_finish",
                False,
                False,
                False,
                "public",
            )
        if event_type in {"private_initialization", "round_context_stored"}:
            return "initialization", False, False, False, True, False, (
                "private" if event_type == "private_initialization" else "public"
            )
        if event_type in {"agent_activity", "tool_activity", "execution_economics"}:
            return "status", False, False, False, False, False, "mechanical"
        return "lifecycle", False, False, False, False, False, "mechanical"
