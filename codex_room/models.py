from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


from .personalities import (
    AGENT_A_IMPLEMENTER_INSTRUCTIONS,
    AGENT_B_VERIFIER_INSTRUCTIONS,
    AGENT_C_INTEGRATOR_INSTRUCTIONS,
    default_agent_instructions,
)

class RoomStatus(StrEnum):
    CREATING = "creating"
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FINISHED = "finished"
    ROLLING_OVER = "rolling_over"
    ERROR = "error"
    ARCHIVED = "archived"


class AgentStatus(StrEnum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    RUNNING = "running"
    USAGE_SUSPENDED = "usage_suspended"
    READY_TO_FINISH = "ready_to_finish"
    FINISHED = "finished"
    ERROR = "error"


class Outcome(StrEnum):
    MESSAGE = "MESSAGE"
    PASS = "PASS"
    FINISH = "FINISH"


class RoundStatus(StrEnum):
    PREPARING = "preparing"
    ACTIVE = "active"
    FINISHED = "finished"
    STOPPED = "stopped"


ExecutionConfigId = Literal[
    "luna-medium",
    "terra-medium",
    "terra-high",
    "sol-medium",
]

EXECUTION_CONFIGS: dict[str, tuple[str, str]] = {
    "luna-medium": ("gpt-5.6-luna", "medium"),
    "terra-medium": ("gpt-5.6-terra", "medium"),
    "terra-high": ("gpt-5.6-terra", "high"),
    "sol-medium": ("gpt-5.6-sol", "medium"),
}


class ExecutionSelection(BaseModel):
    target: Literal["agent_a", "agent_b", "agent_c"]
    config: ExecutionConfigId


class AgentDecision(BaseModel):
    outcome: Outcome
    message: str = ""
    invoke_targets: list[
        Literal["all", "agent_a", "agent_b", "agent_c"]
    ] | None = None
    execution_configs: list[ExecutionSelection] | None = None

    @model_validator(mode="after")
    def message_required_for_message(self) -> "AgentDecision":
        self.message = self.message.strip()
        if self.outcome == Outcome.MESSAGE and not self.message:
            raise ValueError("MESSAGE requires non-empty message text")
        if self.outcome != Outcome.MESSAGE and self.invoke_targets is not None:
            raise ValueError("invoke_targets is valid only for MESSAGE")
        if self.outcome != Outcome.MESSAGE and self.execution_configs is not None:
            raise ValueError("execution_configs is valid only for MESSAGE")
        if self.invoke_targets is not None:
            if len(self.invoke_targets) != len(set(self.invoke_targets)):
                raise ValueError("invoke_targets cannot contain duplicates")
            if "all" in self.invoke_targets and len(self.invoke_targets) != 1:
                raise ValueError("invoke_targets 'all' cannot be combined with participants")
        if self.execution_configs is not None:
            targets = [selection.target for selection in self.execution_configs]
            if len(targets) != len(set(targets)):
                raise ValueError("execution_configs cannot contain duplicate targets")
        return self


DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["MESSAGE", "PASS", "FINISH"]},
        "message": {"type": "string"},
        "invoke_targets": {
            "anyOf": [
                {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["all", "agent_a", "agent_b", "agent_c"],
                    },
                },
                {"type": "null"},
            ]
        },
        "execution_configs": {
            "anyOf": [
                {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "enum": ["agent_a", "agent_b", "agent_c"],
                            },
                            "config": {
                                "type": "string",
                                "enum": [
                                    "luna-medium",
                                    "terra-medium",
                                    "terra-high",
                                    "sol-medium",
                                ],
                            },
                        },
                        "required": ["target", "config"],
                        "additionalProperties": False,
                    },
                },
                {"type": "null"},
            ]
        },
    },
    "required": ["outcome", "message", "invoke_targets", "execution_configs"],
    "additionalProperties": False,
}


class CreateRoomRequest(BaseModel):
    title: str = Field(default="Untitled Room", min_length=1, max_length=120)
    topic: str = Field(min_length=1, max_length=50_000)
    agent_a_name: str = Field(default="Agent A", min_length=1, max_length=80)
    agent_b_name: str = Field(default="Agent B", min_length=1, max_length=80)
    agent_a_instructions: str | None = Field(default=None, max_length=50_000)
    agent_b_instructions: str | None = Field(default=None, max_length=50_000)
    agent_c_instructions: str | None = Field(default=None, max_length=50_000)
    max_turns: int = Field(default=40, ge=2, le=500)
    max_consecutive_passes: int = Field(default=3, ge=1, le=20)
    inactivity_seconds: int = Field(default=900, ge=30, le=86_400)
    starting_agent: Literal["agent_a", "agent_b", "agent_c", "either"] = "agent_c"
    auto_start: bool = True


class AddAgentRequest(BaseModel):
    agent_key: Literal["agent_c"] = "agent_c"


class RolloverRoomRequest(BaseModel):
    checkpoint: str = Field(min_length=1, max_length=50_000)
    title: str | None = Field(default=None, min_length=1, max_length=120)
    institutional_release_sha256: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )


class BindInstitutionalReleaseRequest(BaseModel):
    institutional_release_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ObserverMessageRequest(BaseModel):
    target: Literal["all", "both", "agent_a", "agent_b", "agent_c"]
    content: str = Field(min_length=1, max_length=50_000)


class NewTopicRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=50_000)


class PrepareRoundRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    prompt: str = Field(min_length=1, max_length=50_000)
    agent_a_private: str | None = Field(default=None, max_length=50_000)
    agent_b_private: str | None = Field(default=None, max_length=50_000)
    participant_private: dict[str, str] = Field(default_factory=dict)
    participant_overlays: dict[str, str] = Field(default_factory=dict)
    starting_agent: Literal["agent_a", "agent_b", "agent_c", "either"] | None = None
    task_overlay: str | None = Field(default=None, max_length=50_000)
    agent_a_overlay: str | None = Field(default=None, max_length=50_000)
    agent_b_overlay: str | None = Field(default=None, max_length=50_000)

    @model_validator(mode="after")
    def validate_participant_maps(self) -> "PrepareRoundRequest":
        allowed = {"agent_a", "agent_b", "agent_c"}
        for label, values in (
            ("participant_private", self.participant_private),
            ("participant_overlays", self.participant_overlays),
        ):
            unknown = set(values) - allowed
            if unknown:
                raise ValueError(f"{label} contains unsupported participants: {sorted(unknown)}")
            for key, value in values.items():
                if not isinstance(value, str) or len(value) > 50_000:
                    raise ValueError(f"{label}.{key} must be a string of at most 50000 characters")
        legacy_private = {"agent_a": self.agent_a_private, "agent_b": self.agent_b_private}
        legacy_overlays = {"agent_a": self.agent_a_overlay, "agent_b": self.agent_b_overlay}
        for key, value in legacy_private.items():
            if value is not None:
                if key in self.participant_private and self.participant_private[key] != value:
                    raise ValueError(f"Conflicting private initialization for {key}")
                self.participant_private[key] = value
        for key, value in legacy_overlays.items():
            if value is not None:
                if key in self.participant_overlays and self.participant_overlays[key] != value:
                    raise ValueError(f"Conflicting overlay for {key}")
                self.participant_overlays[key] = value
        return self


class DefaultProfilesUpdate(BaseModel):
    agent_a_name: str = Field(default="Agent A default", min_length=1, max_length=120)
    agent_a_instructions: str = Field(min_length=1, max_length=50_000)
    agent_b_name: str = Field(default="Agent B default", min_length=1, max_length=120)
    agent_b_instructions: str = Field(min_length=1, max_length=50_000)
    agent_c_name: str | None = Field(default=None, min_length=1, max_length=120)
    agent_c_instructions: str | None = Field(default=None, min_length=1, max_length=50_000)

    @model_validator(mode="after")
    def validate_agent_c_profile_pair(self) -> "DefaultProfilesUpdate":
        if (self.agent_c_name is None) != (self.agent_c_instructions is None):
            raise ValueError("agent_c_name and agent_c_instructions must be supplied together")
        return self


class UpdateRoomRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    max_turns: int | None = Field(default=None, ge=2, le=500)
    max_consecutive_passes: int | None = Field(default=None, ge=1, le=20)
    inactivity_seconds: int | None = Field(default=None, ge=30, le=86_400)
