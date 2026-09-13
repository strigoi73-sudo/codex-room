from __future__ import annotations

import asyncio
import json
import os
import shlex
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from .custom_capability_registration import (
    CustomCapabilityVerificationError,
    VerificationReceipt,
)
from .models import AgentDecision, DECISION_SCHEMA


ROOM_MODEL = "gpt-5.6-terra"
ROOM_REASONING_EFFORT = "high"
ROOM_CODEX_CONFIG_OVERRIDES = (
    f'model="{ROOM_MODEL}"',
    f'model_reasoning_effort="{ROOM_REASONING_EFFORT}"',
)
MAX_DURABLE_CAPABILITY_RESULT_BYTES = 64 * 1024


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
        type_aliases = {
            "command_execution": "command_execution",
            "commandExecution": "command_execution",
            "file_change": "file_change",
            "fileChange": "file_change",
            "mcp_tool_call": "mcp_tool_call",
            "mcpToolCall": "mcp_tool_call",
            "dynamic_tool_call": "dynamic_tool_call",
            "dynamicToolCall": "dynamic_tool_call",
            "collab_agent_tool_call": "collab_agent_tool_call",
            "collabAgentToolCall": "collab_agent_tool_call",
            "sub_agent_activity": "sub_agent_activity",
            "subAgentActivity": "sub_agent_activity",
            "web_search": "web_search",
            "webSearch": "web_search",
            "image_view": "image_view",
            "imageView": "image_view",
            "image_generation": "image_generation",
            "imageGeneration": "image_generation",
            "context_compaction": "context_compaction",
            "contextCompaction": "context_compaction",
        }
        activities: list[dict[str, Any]] = []
        for wrapped in items:
            item = getattr(wrapped, "root", wrapped)
            raw_type = getattr(item, "type", None)
            item_type = type_aliases.get(raw_type)
            if item_type is None:
                continue
            status = getattr(item, "status", None)
            status_value = getattr(status, "value", status) or "completed"
            if item_type == "command_execution":
                capability = CodexAgentAdapter._safe_capability_activity(
                    getattr(item, "command", ""),
                    getattr(item, "aggregated_output", ""),
                    status_value,
                    getattr(item, "command_actions", []),
                )
                if capability is not None:
                    activities.append(capability)
                    continue
            activities.append({"type": item_type, "status": status_value})
        return activities

    @staticmethod
    def _safe_capability_activity(
        command: str,
        aggregated_output: str,
        status: str,
        command_actions: list[Any] | None = None,
    ) -> dict[str, Any] | None:
        """Persist recognized registry/capability evidence without arbitrary shell output."""
        candidates = [str(command)]
        for wrapped in command_actions or []:
            action = getattr(wrapped, "root", wrapped)
            action_command = getattr(action, "command", None)
            if isinstance(action_command, str):
                candidates.append(action_command)

        direct = next(
            (
                parsed
                for candidate in candidates
                if (parsed := CodexAgentAdapter._parse_direct_capability_command(candidate))
                is not None
            ),
            None,
        )
        if direct is None:
            return None
        lines = [line.strip() for line in str(aggregated_output).splitlines() if line.strip()]
        if not lines:
            return None
        try:
            payload = json.loads(lines[-1])
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(payload, dict):
            return None

        operation, requested_capability = direct
        if operation in {"list", "authoring", "inspect", "register"}:
            if (
                payload.get("codex_room_registry") != 1
                or payload.get("operation") != operation
            ):
                return None
            if operation == "list":
                manifests = payload.get("capabilities")
                if not isinstance(manifests, list):
                    return None
                summaries = []
                for manifest in manifests:
                    if not isinstance(manifest, dict) or not isinstance(manifest.get("id"), str):
                        return None
                    summaries.append(
                        {
                            key: manifest[key]
                            for key in (
                                "id",
                                "origin",
                                "scope",
                                "version",
                                "implementation_sha256",
                                "package_sha256",
                                "registration_sha256",
                            )
                            if key in manifest
                        }
                    )
                return {
                    "type": "deterministic_capability_registry",
                    "status": status,
                    "operation": "list",
                    "capabilities": summaries,
                }

            if operation == "authoring":
                if payload.get("schema_version") != 1:
                    return None
                return {
                    "type": "deterministic_capability_registry",
                    "status": status,
                    "operation": "authoring",
                    "authoring_schema_version": 1,
                }

            if operation == "register":
                request = payload.get("registration_request")
                if (
                    payload.get("ok") is not True
                    or payload.get("state") != "verification_passed_host_pending"
                    or payload.get("capability_id") != requested_capability
                    or not isinstance(request, dict)
                    or request.get("capability_id") != requested_capability
                ):
                    return None
                try:
                    receipt = VerificationReceipt.from_dict(request.get("receipt"))
                except CustomCapabilityVerificationError:
                    return None
                safe_request = {
                    "capability_id": requested_capability,
                    "receipt": receipt.as_dict(),
                }
                serialized = json.dumps(
                    safe_request,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                if len(serialized) > MAX_DURABLE_CAPABILITY_RESULT_BYTES:
                    return None
                return {
                    "type": "deterministic_capability_registry",
                    "status": status,
                    "operation": "register",
                    "capability": requested_capability,
                    "registration_state": "verification_passed_host_pending",
                    "registration_request": safe_request,
                }

            manifest = payload.get("capability")
            if (
                not isinstance(manifest, dict)
                or manifest.get("id") != requested_capability
            ):
                return None
            safe_manifest = {
                key: manifest[key]
                for key in (
                    "id",
                    "description",
                    "origin",
                    "scope",
                    "version",
                    "implementation_sha256",
                    "package_sha256",
                    "registration_sha256",
                    "durable_result_fields",
                    "permissions",
                    "side_effects",
                    "verification",
                )
                if key in manifest
            }
            return {
                "type": "deterministic_capability_registry",
                "status": status,
                "operation": "inspect",
                "capability": requested_capability,
                "manifest": safe_manifest,
            }

        if (
            payload.get("codex_room_capability") != 1
            or payload.get("capability") != requested_capability
        ):
            return None
        declared_fields = payload.get("durable_result_fields")
        if declared_fields is None:
            # Preserve P4.1/P4.2 telemetry for older capability results.
            durable_fields = ["subject", "checks"]
        elif (
            not isinstance(declared_fields, list)
            or len(declared_fields) > 32
            or any(
                not isinstance(field, str) or not field or len(field) > 128
                for field in declared_fields
            )
        ):
            return None
        else:
            durable_fields = declared_fields

        common_fields = (
            "codex_room_capability",
            "capability",
            "capability_version",
            "implementation_sha256",
            "package_sha256",
            "registration_sha256",
            "verification_sha256",
            "ok",
            "durable_result_fields",
            "error",
        )
        safe_payload = {
            key: payload[key]
            for key in common_fields
            if key in payload
        }
        for field in durable_fields:
            if field in payload and field not in safe_payload:
                safe_payload[field] = payload[field]

        serialized = json.dumps(
            safe_payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(serialized) > MAX_DURABLE_CAPABILITY_RESULT_BYTES:
            safe_payload = {
                key: payload[key]
                for key in common_fields
                if key in payload
            }
            safe_payload["durable_result_truncated"] = True
            safe_payload["durable_result_original_bytes"] = len(serialized)

        return {
            "type": "deterministic_capability",
            "status": status,
            "capability": requested_capability,
            "ok": bool(payload.get("ok")),
            "result": safe_payload,
        }

    @staticmethod
    def _parse_direct_capability_command(command: str) -> tuple[str, str | None] | None:
        normalized = str(command).strip()
        direct = CodexAgentAdapter._parse_capability_script(normalized)
        if direct is not None:
            return direct

        inner = CodexAgentAdapter._unwrap_powershell_command(normalized)
        if inner is None:
            return None
        return CodexAgentAdapter._parse_capability_script(inner)

    @staticmethod
    def _parse_capability_script(command: str) -> tuple[str, str | None] | None:
        normalized = str(command).strip()
        if any(separator in normalized for separator in ("&&", ";", "|")):
            return None
        parts = normalized.split()
        if parts and parts[0] == "&":
            parts = parts[1:]
        if len(parts) < 2:
            return None

        executable = parts[0].strip('"').strip("'").lower()
        if executable not in {"codex-room-cap", "codex-room-cap.cmd"}:
            return None

        operation = parts[1].strip('"').strip("'").lower()
        if operation in {"list", "authoring"}:
            return (operation, None) if len(parts) == 2 else None
        if operation in {"inspect", "invoke", "register"}:
            if len(parts) < 3:
                return None
            return operation, parts[2].strip('"').strip("'")
        if operation == "assert-file":
            return "invoke", "assert_file"
        return None

    @staticmethod
    def _unwrap_powershell_command(command: str) -> str | None:
        try:
            parts = shlex.split(str(command).strip(), posix=False)
        except ValueError:
            return None
        if not parts:
            return None

        executable = parts[0].strip('"').strip("'").replace("\\", "/")
        executable = executable.rsplit("/", 1)[-1].lower()
        if executable not in {"powershell", "powershell.exe", "pwsh", "pwsh.exe"}:
            return None

        command_index = next(
            (
                index
                for index, part in enumerate(parts[1:], start=1)
                if part.strip('"').strip("'").lower() in {"-command", "-c"}
            ),
            None,
        )
        if command_index is None or command_index + 1 >= len(parts):
            return None

        inner = " ".join(parts[command_index + 1 :]).strip()
        if (
            len(inner) >= 2
            and inner[0] == inner[-1]
            and inner[0] in {"'", '"'}
        ):
            inner = inner[1:-1].strip()
        return inner or None
