from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from pathlib import Path
from collections.abc import Awaitable, Callable
from typing import Any

from codex_room.agent import AgentRunResult, InterruptOutcome
from codex_room.models import AgentDecision, Outcome


class FakeAgentAdapter:
    def __init__(
        self,
        decisions: dict[str, list[tuple[Outcome, str]]] | None = None,
        *,
        synchronize_first_topic: bool = False,
        delay: float = 0.01,
        delays: dict[str, list[float]] | None = None,
        blocked_calls: dict[str, set[int]] | None = None,
        usages: dict[str, list[dict[str, Any]]] | None = None,
        activities: dict[str, list[list[dict[str, Any]]]] | None = None,
        compact_failures: set[str] | None = None,
        compact_error_messages: dict[str, str] | None = None,
        interrupt_outcomes: dict[str, InterruptOutcome] | None = None,
        failures: dict[str, list[Exception]] | None = None,
        profile_rebind_error: Exception | None = None,
    ) -> None:
        self.decisions = {
            key: deque(AgentDecision(outcome=outcome, message=message) for outcome, message in values)
            for key, values in (decisions or {}).items()
        }
        self.synchronize_first_topic = synchronize_first_topic
        self.delay = delay
        self.delays = {key: deque(values) for key, values in (delays or {}).items()}
        self.blocked_calls = blocked_calls or {}
        self.usages = {key: deque(values) for key, values in (usages or {}).items()}
        self.activities = {key: deque(values) for key, values in (activities or {}).items()}
        self.compact_failures = compact_failures or set()
        self.compact_error_messages = compact_error_messages or {}
        self.interrupt_outcomes = interrupt_outcomes or {}
        self.failures = {key: deque(values) for key, values in (failures or {}).items()}
        self.profile_rebind_error = profile_rebind_error
        self._call_gates: dict[tuple[str, int], asyncio.Event] = {}
        self._inactive_agents: set[str] = set()
        self.starts: list[tuple[str, str]] = []
        self.calls: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.completed_calls: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.archived: list[str] = []
        self.unarchived: list[str] = []
        self.interrupted: list[str] = []
        self.compacted: list[str] = []
        self.profile_rebinds: list[dict[str, Any]] = []
        self.usage_continuation_prepares: list[dict[str, Any]] = []
        self._topic_started = 0
        self._topic_barrier = asyncio.Event()

    async def initialize(self) -> dict[str, Any]:
        return {"authenticated": True, "provider": "fake"}

    async def close(self) -> None:
        return None

    async def start_agent(self, agent: dict[str, Any], cwd: Path) -> str:
        thread_id = f"thr_fake_{agent['agent_key']}_{len(self.starts) + 1}"
        self.starts.append((agent["agent_key"], thread_id))
        return thread_id

    async def run_agent(
        self,
        agent: dict[str, Any],
        cwd: Path,
        prompt: str,
        on_started: Callable[[str, str], Awaitable[None]] | None = None,
        on_progress: Callable[[], Awaitable[None]] | None = None,
    ) -> AgentRunResult:
        self._inactive_agents.discard(agent["agent_key"])
        self.calls[agent["agent_key"]].append(
            {"thread_id": agent["thread_id"], "prompt": prompt, "cwd": str(cwd)}
        )
        if self.synchronize_first_topic and "NEW TOPIC" in prompt and len(self.calls[agent["agent_key"]]) == 1:
            self._topic_started += 1
            if self._topic_started == 2:
                self._topic_barrier.set()
            await asyncio.wait_for(self._topic_barrier.wait(), timeout=2)
        call_number = len(self.calls[agent["agent_key"]])
        turn_id = f"turn_fake_{agent['agent_key']}_{call_number}"
        if on_started is not None:
            await on_started(agent["thread_id"], turn_id)
        if on_progress is not None:
            await on_progress()
        if call_number in self.blocked_calls.get(agent["agent_key"], set()):
            gate = self._call_gates.setdefault((agent["agent_key"], call_number), asyncio.Event())
            await gate.wait()
        delays = self.delays.get(agent["agent_key"])
        await asyncio.sleep(delays.popleft() if delays else self.delay)
        failures = self.failures.get(agent["agent_key"])
        if failures:
            self.completed_calls[agent["agent_key"]].append(
                self.calls[agent["agent_key"]][-1]
            )
            raise failures.popleft()
        queue = self.decisions.get(agent["agent_key"])
        decision = queue.popleft() if queue else AgentDecision(outcome=Outcome.PASS, message="")
        self.completed_calls[agent["agent_key"]].append(self.calls[agent["agent_key"]][-1])
        usages = self.usages.get(agent["agent_key"])
        usage = usages.popleft() if usages else {"total_tokens": 10}
        activities = self.activities.get(agent["agent_key"])
        activity = activities.popleft() if activities else []
        return AgentRunResult(
            decision=decision,
            usage=usage,
            activity=activity,
            thread_id=agent["thread_id"],
            turn_id=turn_id,
        )

    async def resume_agent(
        self,
        agent: dict[str, Any],
        cwd: Path,
        thread_id: str,
        turn_id: str,
        on_progress: Callable[[], Awaitable[None]] | None = None,
    ) -> AgentRunResult:
        """Tests may provide a durable turn result using the normal decision queue."""
        self.calls[agent["agent_key"]].append(
            {
                "thread_id": thread_id,
                "turn_id": turn_id,
                "prompt": "[recovered exact turn]",
                "cwd": str(cwd),
                "recovered": True,
            }
        )
        queue = self.decisions.get(agent["agent_key"])
        decision = queue.popleft() if queue else AgentDecision(outcome=Outcome.PASS, message="")
        self.completed_calls[agent["agent_key"]].append(self.calls[agent["agent_key"]][-1])
        if on_progress is not None:
            await on_progress()
        return AgentRunResult(
            decision=decision,
            usage={"total_tokens": 10},
            thread_id=thread_id,
            turn_id=turn_id,
            completion_source="history",
        )

    async def compact_agent(self, agent: dict[str, Any], cwd: Path) -> None:
        self.compacted.append(agent["agent_key"])
        if agent["agent_key"] in self.compact_failures:
            raise RuntimeError(
                self.compact_error_messages.get(
                    agent["agent_key"], "simulated compaction failure"
                )
            )

    async def prepare_usage_continuation(
        self, agent: dict[str, Any], cwd: Path
    ) -> None:
        self.usage_continuation_prepares.append(
            {
                "agent_key": agent["agent_key"],
                "thread_id": agent["thread_id"],
                "cwd": str(cwd),
            }
        )

    def release_call(self, agent_key: str, call_number: int) -> None:
        self._call_gates.setdefault((agent_key, call_number), asyncio.Event()).set()

    async def interrupt(self, agent_id: str) -> InterruptOutcome:
        self.interrupted.append(agent_id)
        agent_key = agent_id.rsplit(":", 1)[-1]
        outcome = self.interrupt_outcomes.get(agent_key, InterruptOutcome.UNKNOWN)
        if outcome != InterruptOutcome.UNKNOWN:
            self._inactive_agents.add(agent_key)
        return outcome

    async def has_active_run(self, agent_id: str) -> bool:
        agent_key = agent_id.rsplit(":", 1)[-1]
        if agent_key in self._inactive_agents:
            return False
        call_number = len(self.calls[agent_key])
        return (
            call_number > len(self.completed_calls[agent_key])
            and call_number in self.blocked_calls.get(agent_key, set())
        )

    async def archive_thread(self, thread_id: str) -> None:
        self.archived.append(thread_id)

    async def unarchive_thread(self, thread_id: str) -> None:
        self.unarchived.append(thread_id)

    async def rebind_agent_profile(self, agent: dict[str, Any], cwd: Path) -> str:
        self.profile_rebinds.append(
            {
                "agent_key": agent["agent_key"],
                "thread_id": agent["thread_id"],
                "developer_instructions": agent["developer_instructions"],
                "cwd": str(cwd),
            }
        )
        if self.profile_rebind_error is not None:
            raise self.profile_rebind_error
        return agent["thread_id"]


async def wait_until(predicate, timeout: float = 30.0) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        value = predicate()
        if asyncio.iscoroutine(value):
            value = await value
        if value:
            return
        await asyncio.sleep(0.02)
    raise AssertionError("condition was not met before timeout")
