from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from .models import AgentDecision, DECISION_SCHEMA


ROOM_MODEL = "gpt-5.6-terra"
ROOM_REASONING_EFFORT = "high"
ROOM_CODEX_CONFIG_OVERRIDES = (
    f'model="{ROOM_MODEL}"',
    f'model_reasoning_effort="{ROOM_REASONING_EFFORT}"',
)


@dataclass(slots=True)
class AgentRunResult:
    decision: AgentDecision
    usage: dict[str, Any] | None = None
    activity: list[dict[str, Any]] = field(default_factory=list)
    thread_id: str | None = None
    turn_id: str | None = None
    completion_source: str = "notification"


class InterruptOutcome(StrEnum):
    """Evidence returned by an attempt to retire an SDK turn."""

    INTERRUPTED = "interrupted"
    ALREADY_INACTIVE = "already_inactive"
    UNKNOWN = "unknown"


class AgentTurnStateUnknownError(RuntimeError):
    """The authoritative thread history cannot prove the expected turn exists."""


class AgentTurnTerminalError(RuntimeError):
    """The exact recovered Codex turn ended without a usable completion."""

    def __init__(self, message: str, *, codex_error_info: str | None = None) -> None:
        super().__init__(message)
        self.codex_error_info = codex_error_info


class AgentAdapter(Protocol):
    async def initialize(self) -> dict[str, Any]: ...

    async def close(self) -> None: ...

    async def start_agent(self, agent: dict[str, Any], cwd: Path) -> str: ...

    async def run_agent(
        self,
        agent: dict[str, Any],
        cwd: Path,
        prompt: str,
        on_started: Callable[[str, str], Awaitable[None]] | None = None,
        on_progress: Callable[[], Awaitable[None]] | None = None,
    ) -> AgentRunResult: ...

    async def resume_agent(
        self,
        agent: dict[str, Any],
        cwd: Path,
        thread_id: str,
        turn_id: str,
        on_progress: Callable[[], Awaitable[None]] | None = None,
    ) -> AgentRunResult: ...

    async def compact_agent(self, agent: dict[str, Any], cwd: Path) -> None: ...

    async def prepare_usage_continuation(
        self, agent: dict[str, Any], cwd: Path
    ) -> None: ...

    async def interrupt(self, agent_id: str) -> InterruptOutcome: ...

    async def has_active_run(self, agent_id: str) -> bool: ...

    async def archive_thread(self, thread_id: str) -> None: ...

    async def unarchive_thread(self, thread_id: str) -> None: ...

    async def rebind_agent_profile(self, agent: dict[str, Any], cwd: Path) -> str: ...


class CodexAgentAdapter:
    """Thin adapter around the official asynchronous Python Codex SDK."""

    INTERRUPT_TIMEOUT_SECONDS = 2.0
    RECONCILIATION_INTERVAL_SECONDS = 2.0
    THREAD_IDLE_TIMEOUT_SECONDS = 120.0

    def __init__(self, *, codex_bin: str | None = None) -> None:
        self._codex_bin = codex_bin or os.environ.get("CODEX_ROOM_CODEX_BIN")
        self._client: Any = None
        self._threads: dict[str, Any] = {}
        self._active_handles: dict[str, Any] = {}
        self._unconfirmed_handles: set[str] = set()
        self._usage_continuation_agents: set[str] = set()
        self._active_lock = asyncio.Lock()

    async def initialize(self) -> dict[str, Any]:
        from openai_codex import AsyncCodex, CodexConfig

        if self._client is None:
            config = CodexConfig(
                codex_bin=self._codex_bin,
                config_overrides=ROOM_CODEX_CONFIG_OVERRIDES,
            )
            self._client = AsyncCodex(config=config)
        account = await self._client.account(refresh_token=False)
        root = getattr(account, "account", None)
        if root is None:
            root = getattr(account, "root", None)
        if root is not None and hasattr(root, "model_dump"):
            raw = root.model_dump(mode="json")
        elif hasattr(account, "model_dump"):
            raw = account.model_dump(mode="json")
        else:
            raw = {"authenticated": True}
        # The browser only needs auth capability/status; do not expose account email.
        raw.pop("email", None)
        raw["authenticated"] = True
        return raw

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
        self._threads.clear()
        self._active_handles.clear()
        self._unconfirmed_handles.clear()
        self._usage_continuation_agents.clear()

    async def start_agent(self, agent: dict[str, Any], cwd: Path) -> str:
        from openai_codex import Sandbox

        self._require_client()
        cwd.mkdir(parents=True, exist_ok=True)
        thread = await self._client.thread_start(
            cwd=str(cwd),
            developer_instructions=agent["developer_instructions"],
            ephemeral=False,
            model=ROOM_MODEL,
            sandbox=Sandbox.workspace_write,
        )
        await thread.set_name(f"Codex Room · {agent['name']}")
        if not thread.id:
            raise RuntimeError("Codex created a thread without a thread ID")
        self._threads[agent["id"]] = thread
        return thread.id

    async def run_agent(
        self,
        agent: dict[str, Any],
        cwd: Path,
        prompt: str,
        on_started: Callable[[str, str], Awaitable[None]] | None = None,
        on_progress: Callable[[], Awaitable[None]] | None = None,
    ) -> AgentRunResult:
        thread = await self._get_thread(agent, cwd)
        usage_continuation = agent["id"] in self._usage_continuation_agents
        self._usage_continuation_agents.discard(agent["id"])
        await self._wait_until_thread_idle(
            thread, allow_usage_system_error=usage_continuation
        )
        handle = await thread.turn(
            prompt,
            effort=ROOM_REASONING_EFFORT,
            model=ROOM_MODEL,
            output_schema=DECISION_SCHEMA,
        )
        return await self._consume_handle(
            agent, thread, handle, on_started=on_started, on_progress=on_progress
        )

    async def resume_agent(
        self,
        agent: dict[str, Any],
        cwd: Path,
        thread_id: str,
        turn_id: str,
        on_progress: Callable[[], Awaitable[None]] | None = None,
    ) -> AgentRunResult:
        """Reattach to one durable turn without starting replacement work."""
        from openai_codex import AsyncTurnHandle

        thread = await self._get_thread(agent, cwd)
        if thread.id != thread_id:
            raise RuntimeError("Persisted execution thread does not match the agent thread")
        handle = AsyncTurnHandle(self._client, thread_id, turn_id)
        return await self._consume_handle(
            agent,
            thread,
            handle,
            require_present=True,
            on_progress=on_progress,
        )

    async def _consume_handle(
        self,
        agent: dict[str, Any],
        thread: Any,
        handle: Any,
        *,
        on_started: Callable[[str, str], Awaitable[None]] | None = None,
        require_present: bool = False,
        on_progress: Callable[[], Awaitable[None]] | None = None,
    ) -> AgentRunResult:
        async with self._active_lock:
            self._active_handles[agent["id"]] = handle
            self._unconfirmed_handles.discard(agent["id"])
        retain_handle = False
        try:
            try:
                if on_started is not None:
                    try:
                        await on_started(thread.id, handle.id)
                    except Exception:
                        # A turn that cannot be bound to its durable Room claim must
                        # not be allowed to continue as untracked work.
                        outcome = await self._interrupt_handle(handle)
                        retain_handle = outcome == InterruptOutcome.UNKNOWN
                        if retain_handle:
                            async with self._active_lock:
                                self._unconfirmed_handles.add(agent["id"])
                        raise
                result, completion_source = await self._run_with_reconciliation(
                    thread,
                    handle,
                    require_present=require_present,
                    on_progress=on_progress,
                )
            except asyncio.CancelledError:
                # A Room execution lease or shutdown cancelled the waiter. Interrupt
                # the SDK turn before releasing the active-handle proof so a future
                # worker cannot overlap the same persistent thread.
                outcome = await self._interrupt_handle(handle)
                retain_handle = outcome == InterruptOutcome.UNKNOWN
                if retain_handle:
                    async with self._active_lock:
                        self._unconfirmed_handles.add(agent["id"])
                raise
        finally:
            if not retain_handle:
                async with self._active_lock:
                    self._active_handles.pop(agent["id"], None)
                    self._unconfirmed_handles.discard(agent["id"])

        if not result.final_response:
            raise RuntimeError("Codex turn completed without a final response")
        try:
            decision = AgentDecision.model_validate(json.loads(result.final_response))
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(
                f"Codex returned invalid Room decision JSON: {result.final_response[:500]}"
            ) from exc

        usage = result.usage.model_dump(mode="json") if result.usage is not None else None
        return AgentRunResult(
            decision=decision,
            usage=usage,
            activity=self._safe_activity(result.items),
            thread_id=thread.id,
            turn_id=handle.id,
            completion_source=completion_source,
        )

    async def _run_with_reconciliation(
        self,
        thread: Any,
        handle: Any,
        *,
        require_present: bool = False,
        on_progress: Callable[[], Awaitable[None]] | None = None,
    ) -> tuple[Any, str]:
        """Race SDK streaming with authoritative lookup of this exact turn."""
        last_fingerprint: tuple[Any, ...] | None = None

        async def observe(fingerprint: tuple[Any, ...]) -> None:
            nonlocal last_fingerprint
            if fingerprint == last_fingerprint:
                return
            last_fingerprint = fingerprint
            if on_progress is not None:
                await on_progress()

        if require_present:
            recovered = await self._read_exact_turn(
                thread, handle.id, require_present=True, on_observed=observe
            )
            if recovered is not None:
                return recovered, "history"
        stream_task = asyncio.create_task(handle.run())
        try:
            while True:
                done, _ = await asyncio.wait(
                    {stream_task}, timeout=self.RECONCILIATION_INTERVAL_SECONDS
                )
                if stream_task in done:
                    try:
                        return stream_task.result(), "notification"
                    except RuntimeError as stream_error:
                        # The SDK notification path reduces a failed turn to its
                        # message. Read the exact persisted turn once so callers can
                        # classify a usage wall from the authoritative error code.
                        try:
                            recovered = await self._read_exact_turn(
                                thread,
                                handle.id,
                                require_present=True,
                                on_observed=observe,
                            )
                        except AgentTurnTerminalError:
                            raise
                        except Exception:
                            raise stream_error
                        if recovered is not None:
                            return recovered, "history"
                        raise stream_error
                try:
                    recovered = await self._read_exact_turn(
                        thread, handle.id, on_observed=observe
                    )
                except (AgentTurnTerminalError, AgentTurnStateUnknownError):
                    raise
                except Exception:
                    # A transient read failure is not evidence that the running turn
                    # failed. The stream remains primary and the next check retries.
                    continue
                if recovered is not None:
                    return recovered, "history"
        finally:
            if not stream_task.done():
                stream_task.cancel()
            await asyncio.gather(stream_task, return_exceptions=True)

    async def _read_exact_turn(
        self,
        thread: Any,
        turn_id: str,
        *,
        require_present: bool = False,
        on_observed: Callable[[tuple[Any, ...]], Awaitable[None]] | None = None,
    ) -> Any | None:
        """Return a TurnResult only when authoritative history proves terminal state."""
        from openai_codex import TurnResult

        response = await thread.read(include_turns=True)
        turns = response.thread.turns
        turn = next((candidate for candidate in turns if candidate.id == turn_id), None)
        if turn is None:
            if require_present:
                raise AgentTurnStateUnknownError(
                    f"Exact Codex turn {turn_id} is absent from complete thread history"
                )
            return None
        status = getattr(turn.status, "value", turn.status)
        item_fingerprint = tuple(
            (
                getattr(getattr(item, "root", item), "id", None),
                getattr(getattr(item, "root", item), "type", None),
                getattr(
                    getattr(getattr(item, "root", item), "status", None),
                    "value",
                    getattr(getattr(item, "root", item), "status", None),
                ),
            )
            for item in turn.items
        )
        if on_observed is not None:
            await on_observed((status, item_fingerprint))
        if status == "inProgress":
            return None
        if status == "failed":
            message = getattr(turn.error, "message", None) if turn.error else None
            error_info = getattr(turn.error, "codex_error_info", None) if turn.error else None
            error_info = getattr(error_info, "root", error_info)
            error_info = getattr(error_info, "value", error_info)
            raise AgentTurnTerminalError(
                message or "Codex turn failed",
                codex_error_info=error_info if isinstance(error_info, str) else None,
            )
        if status == "interrupted":
            raise AgentTurnTerminalError("Codex turn was interrupted")
        if status != "completed":
            raise AgentTurnTerminalError(f"Codex turn has unknown status: {status}")
        items_view = getattr(turn, "items_view", "full")
        items_view = getattr(items_view, "value", items_view)
        if items_view != "full":
            raise AgentTurnStateUnknownError(
                "Authoritative turn history returned incomplete items"
            )
        final_response = None
        for wrapped in reversed(turn.items):
            item = getattr(wrapped, "root", wrapped)
            if getattr(item, "type", None) != "agentMessage":
                continue
            phase = getattr(getattr(item, "phase", None), "value", getattr(item, "phase", None))
            if phase == "final_answer":
                final_response = item.text
                break
        return TurnResult(
            id=turn.id,
            status=turn.status,
            error=turn.error,
            started_at=turn.started_at,
            completed_at=turn.completed_at,
            duration_ms=turn.duration_ms,
            final_response=final_response,
            items=turn.items,
            usage=None,
        )

    async def compact_agent(self, agent: dict[str, Any], cwd: Path) -> None:
        """Compact a persistent thread without changing its identity."""
        thread = await self._get_thread(agent, cwd)
        before = await thread.read(include_turns=True)
        prior_compactions = self._context_compaction_ids(before)
        await thread.compact()
        deadline = (
            asyncio.get_running_loop().time() + self.THREAD_IDLE_TIMEOUT_SECONDS
        )
        while True:
            response = await thread.read(include_turns=True)
            status_type = self._thread_status_type(response)
            completed = self._context_compaction_ids(response) - prior_compactions
            # thread/compact/start is asynchronous. An immediate idle response can
            # be stale, so only a newly persisted compaction turn is proof that the
            # requested operation finished and the thread is safe for another turn.
            if completed and status_type == "idle":
                return
            if status_type == "systemError":
                raise RuntimeError("Codex thread entered a system-error state during compaction")
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError(
                    "Timed out waiting for persisted Codex thread compaction evidence"
                )
            await asyncio.sleep(0.05)

    async def prepare_usage_continuation(
        self, agent: dict[str, Any], cwd: Path
    ) -> None:
        """Rebind the same thread after a positively identified usage wall."""
        await self.rebind_agent_profile(agent, cwd)
        thread = self._threads[agent["id"]]
        response = await thread.read()
        status_type = self._thread_status_type(response)
        if status_type not in {"idle", "systemError"}:
            raise RuntimeError(
                "Usage continuation thread is not in an inactive terminal state"
            )
        self._usage_continuation_agents.add(agent["id"])

    async def _wait_until_thread_idle(
        self, thread: Any, *, allow_usage_system_error: bool = False
    ) -> None:
        """Do not submit a turn while compaction or another SDK turn is active."""
        deadline = (
            asyncio.get_running_loop().time() + self.THREAD_IDLE_TIMEOUT_SECONDS
        )
        while True:
            response = await thread.read()
            status_type = self._thread_status_type(response)
            if status_type == "idle":
                return
            if status_type == "systemError":
                if allow_usage_system_error:
                    return
                raise RuntimeError("Codex thread is in a system-error state")
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError("Timed out waiting for Codex thread to become idle")
            await asyncio.sleep(0.05)

    @staticmethod
    def _thread_status_type(response: Any) -> str | None:
        status = getattr(response.thread.status, "root", response.thread.status)
        return getattr(status, "type", None)

    @staticmethod
    def _context_compaction_ids(response: Any) -> set[str]:
        ids: set[str] = set()
        for turn in getattr(response.thread, "turns", []):
            for wrapped in getattr(turn, "items", []):
                item = getattr(wrapped, "root", wrapped)
                if getattr(item, "type", None) == "contextCompaction":
                    ids.add(item.id)
        return ids

    async def interrupt(self, agent_id: str) -> InterruptOutcome:
        async with self._active_lock:
            handle = self._active_handles.get(agent_id)
        if handle is None:
            return InterruptOutcome.ALREADY_INACTIVE
        outcome = await self._interrupt_handle(handle)
        if outcome != InterruptOutcome.UNKNOWN:
            async with self._active_lock:
                if (
                    agent_id in self._unconfirmed_handles
                    and self._active_handles.get(agent_id) is handle
                ):
                    self._active_handles.pop(agent_id, None)
                    self._unconfirmed_handles.discard(agent_id)
        return outcome

    async def has_active_run(self, agent_id: str) -> bool:
        async with self._active_lock:
            return agent_id in self._active_handles

    @staticmethod
    def _is_already_inactive_error(exc: Exception) -> bool:
        text = str(exc).casefold()
        code = getattr(exc, "code", None)
        return (
            (code == -32600 or "-32600" in text)
            and "no active turn to interrupt" in text
        )

    async def _interrupt_handle(self, handle: Any) -> InterruptOutcome:
        try:
            async with asyncio.timeout(self.INTERRUPT_TIMEOUT_SECONDS):
                await handle.interrupt()
        except Exception as exc:
            if self._is_already_inactive_error(exc):
                return InterruptOutcome.ALREADY_INACTIVE
            return InterruptOutcome.UNKNOWN
        return InterruptOutcome.INTERRUPTED

    async def archive_thread(self, thread_id: str) -> None:
        self._require_client()
        await self._client.thread_archive(thread_id)

    async def unarchive_thread(self, thread_id: str) -> None:
        self._require_client()
        await self._client.thread_unarchive(thread_id)

    async def rebind_agent_profile(self, agent: dict[str, Any], cwd: Path) -> str:
        """Resume one idle persistent thread with its current effective instructions."""
        from openai_codex import Sandbox

        self._require_client()
        async with self._active_lock:
            if (
                agent["id"] in self._active_handles
                or agent["id"] in self._unconfirmed_handles
            ):
                raise RuntimeError("Cannot rebind a profile while its SDK turn is active")
            self._threads.pop(agent["id"], None)
            try:
                thread = await self._client.thread_resume(
                    agent["thread_id"],
                    cwd=str(cwd),
                    developer_instructions=agent["developer_instructions"],
                    model=ROOM_MODEL,
                    sandbox=Sandbox.workspace_write,
                )
            except BaseException:
                raise
            if thread.id != agent["thread_id"]:
                raise RuntimeError("Profile rebind returned a different Codex thread ID")
            self._threads[agent["id"]] = thread
            return thread.id

    async def _get_thread(self, agent: dict[str, Any], cwd: Path) -> Any:
        from openai_codex import Sandbox

        self._require_client()
        cached = self._threads.get(agent["id"])
        if cached is not None and cached.id == agent["thread_id"]:
            return cached
        thread_id = agent.get("thread_id")
        if not thread_id:
            raise RuntimeError(f"{agent['name']} does not have a Codex thread ID")
        thread = await self._client.thread_resume(
            thread_id,
            cwd=str(cwd),
            developer_instructions=agent["developer_instructions"],
            model=ROOM_MODEL,
            sandbox=Sandbox.workspace_write,
        )
        self._threads[agent["id"]] = thread
        return thread

    def _require_client(self) -> None:
        if self._client is None:
            raise RuntimeError("Codex adapter has not been initialized")

    @staticmethod
    def _safe_activity(items: list[Any]) -> list[dict[str, Any]]:
        """Expose tool categories and statuses, never reasoning or hidden text."""
        safe_types = {
            "command_execution",
            "file_change",
            "mcp_tool_call",
            "dynamic_tool_call",
            "collab_agent_tool_call",
            "sub_agent_activity",
            "web_search",
            "image_view",
            "image_generation",
            "context_compaction",
        }
        activities: list[dict[str, Any]] = []
        for wrapped in items:
            item = getattr(wrapped, "root", wrapped)
            item_type = getattr(item, "type", None)
            if item_type not in safe_types:
                continue
            status = getattr(item, "status", None)
            status_value = getattr(status, "value", status) or "completed"
            if item_type == "command_execution":
                capability = CodexAgentAdapter._safe_capability_activity(
                    getattr(item, "command", ""),
                    getattr(item, "aggregated_output", ""),
                    status_value,
                )
                if capability is not None:
                    activities.append(capability)
                    continue
            activities.append({"type": item_type, "status": status_value})
        return activities

    @staticmethod
    def _safe_capability_activity(
        command: str, aggregated_output: str, status: str
    ) -> dict[str, Any] | None:
        """Persist structured capability evidence without arbitrary shell output."""
        if "codex-room-cap" not in str(command).lower():
            return None
        lines = [line.strip() for line in str(aggregated_output).splitlines() if line.strip()]
        if not lines:
            return None
        try:
            payload = json.loads(lines[-1])
        except (json.JSONDecodeError, TypeError):
            return None
        if (
            not isinstance(payload, dict)
            or payload.get("codex_room_capability") != 1
            or payload.get("capability") != "assert_file"
        ):
            return None
        safe_payload = {
            key: payload[key]
            for key in ("codex_room_capability", "capability", "ok", "subject", "checks", "error")
            if key in payload
        }
        return {
            "type": "deterministic_capability",
            "status": status,
            "capability": "assert_file",
            "ok": bool(payload.get("ok")),
            "result": safe_payload,
        }
