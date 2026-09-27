from __future__ import annotations

from enum import StrEnum
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


from .observer_attachments import (
    MAX_OBSERVER_IMAGES,
    MAX_OBSERVER_IMAGE_DATA_URL_CHARS,
)
from .personalities import (
    AGENT_A_DEFAULT_INSTRUCTIONS,
    AGENT_B_DEFAULT_INSTRUCTIONS,
    AGENT_C_DEFAULT_INSTRUCTIONS,
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


class TransactionAction(StrEnum):
    COMPLETE = "COMPLETE"
    DELEGATE = "DELEGATE"
    EVIDENCE = "EVIDENCE"
    HISTORY = "HISTORY"
    REFRESH = "REFRESH"
    CONSULT_PRINCIPAL = "CONSULT_PRINCIPAL"
    PASS = "PASS"


class RoundStatus(StrEnum):
    PREPARING = "preparing"
    ACTIVE = "active"
    FINISHED = "finished"
    STOPPED = "stopped"


OrdinaryExecutionConfigId = Literal[
    "luna-low",
    "luna-medium",
    "luna-high",
    "terra-low",
    "terra-medium",
    "terra-high",
    "sol-low",
    "sol-medium",
    "sol-high",
]
AstraExecutionConfigId = Literal[
    "astra-low",
    "astra-medium",
    "astra-high",
]
SelectableExecutionConfigId = OrdinaryExecutionConfigId | AstraExecutionConfigId
ExceptionalCExecutionConfigId = Literal[
    "sol-xhigh",
    "sol-max",
]
ExecutionConfigId = SelectableExecutionConfigId | ExceptionalCExecutionConfigId
ModelPolicy = Literal["default", "unrestricted"]

ORDINARY_EXECUTION_CONFIGS: tuple[str, ...] = (
    "luna-low",
    "luna-medium",
    "luna-high",
    "terra-low",
    "terra-medium",
    "terra-high",
    "sol-low",
    "sol-medium",
    "sol-high",
)
ASTRA_EXECUTION_CONFIGS: tuple[str, ...] = (
    "astra-low",
    "astra-medium",
    "astra-high",
)
EXCEPTIONAL_C_EXECUTION_CONFIGS: tuple[str, ...] = (
    "sol-xhigh",
    "sol-max",
)
EXECUTION_CONFIGS: dict[str, tuple[str, str]] = {
    "luna-low": ("gpt-5.6-luna", "low"),
    "luna-medium": ("gpt-5.6-luna", "medium"),
    "luna-high": ("gpt-5.6-luna", "high"),
    "terra-low": ("gpt-5.6-terra", "low"),
    "terra-medium": ("gpt-5.6-terra", "medium"),
    "terra-high": ("gpt-5.6-terra", "high"),
    "sol-low": ("gpt-5.6-sol", "low"),
    "sol-medium": ("gpt-5.6-sol", "medium"),
    "sol-high": ("gpt-5.6-sol", "high"),
    "astra-low": ("gpt-6-astra", "low"),
    "astra-medium": ("gpt-6-astra", "medium"),
    "astra-high": ("gpt-6-astra", "high"),
    "sol-xhigh": ("gpt-5.6-sol", "xhigh"),
    "sol-max": ("gpt-5.6-sol", "max"),
}
C_COGNITION_CEILING_RANK: dict[str, int] = {
    "sol-high": 0,
    "sol-xhigh": 1,
    "sol-max": 2,
}


def room_unrestricted_model_access(metadata: dict[str, Any] | None) -> bool:
    return bool(metadata and metadata.get("model_policy") == "unrestricted")


def execution_config_catalog(
    metadata: dict[str, Any] | None,
) -> dict[str, tuple[str, str]]:
    if not room_unrestricted_model_access(metadata):
        return dict(EXECUTION_CONFIGS)
    raw = (metadata or {}).get("unrestricted_execution_configs") or {}
    if not isinstance(raw, dict):
        return {}
    catalog: dict[str, tuple[str, str]] = {}
    for config_id, item in raw.items():
        if not isinstance(config_id, str) or not isinstance(item, dict):
            continue
        model = item.get("model")
        effort = item.get("reasoning_effort")
        if isinstance(model, str) and model and isinstance(effort, str) and effort:
            catalog[config_id] = (model, effort)
    return catalog


def initial_prompt_authorizes_astra(prompt: str) -> bool:
    """Return whether the opening Room prompt explicitly authorizes Astra execution."""
    negative = re.compile(
        r"\b(?:do\s+not|don't|never|prohibit(?:ed)?|forbid(?:den)?|without)\b"
        r"[^\n]{0,80}\bastra\b",
        re.IGNORECASE,
    )
    explicit = (
        re.compile(
            r"\b(?:use|uses|using|run|runs|running|execute|executes|executing|"
            r"assign|assigns|assigning|select|selects|selecting)\b"
            r"[^\n]{0,120}\bastra\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bagent\s+[abc]\b[^\n]{0,80}"
            r"\b(?:participant|model|config|configuration)\b"
            r"[^\n]{0,80}\bastra\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:agent\s+)?[abc]\b\s*(?:[:=]|[-–—]{1,2})"
            r"[^\n]{0,60}\bastra\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bastra\b[^\n]{0,120}\b(?:for|on)\s+(?:agent\s+)?[abc]\b",
            re.IGNORECASE,
        ),
    )
    for line in prompt.splitlines():
        if "astra" not in line.lower() or negative.search(line):
            continue
        if any(pattern.search(line) for pattern in explicit):
            return True
    return False


class ExecutionSelection(BaseModel):
    target: Literal["agent_a", "agent_b", "agent_c"]
    config: SelectableExecutionConfigId


class DelegationRequest(BaseModel):
    target: Literal["agent_a", "agent_b", "agent_c"]
    instruction: str = Field(min_length=1, max_length=50_000)
    config: str | None = Field(default=None, min_length=1, max_length=200)
    context_from_assignment_id: str | None = Field(
        default=None, min_length=1, max_length=200
    )
    fresh_context: bool = False

    @model_validator(mode="after")
    def validate_context_policy(self) -> "DelegationRequest":
        if self.fresh_context and self.context_from_assignment_id is not None:
            raise ValueError(
                "fresh_context cannot be combined with context_from_assignment_id"
            )
        if self.config in EXCEPTIONAL_C_EXECUTION_CONFIGS:
            raise ValueError(
                "Exceptional C execution configs cannot be assigned directly to peers"
            )
        return self


class SourceEvidenceRequest(BaseModel):
    operation: Literal["READ", "SEARCH", "FIND"]
    source: Literal["workspace", "core", "room"] = "workspace"
    room_id: str | None = None
    path: str = Field(min_length=1, max_length=4096)
    query: str | None = Field(default=None, max_length=4096)
    start_line: int = Field(default=1, ge=1)
    max_lines: int = Field(default=400, ge=1, le=1000)
    max_bytes: int = Field(default=32 * 1024, ge=1, le=128 * 1024)
    include_globs: list[str] = Field(default_factory=list)
    exclude_globs: list[str] = Field(default_factory=list)
    include_hidden: bool = False
    case_sensitive: bool = True
    max_results: int = Field(default=100, ge=1, le=200)
    max_files: int = Field(default=100, ge=1, le=200)
    max_matches: int = Field(default=50, ge=1, le=100)

    @model_validator(mode="after")
    def validate_source_evidence_request(self) -> "SourceEvidenceRequest":
        if self.source == "room":
            if not self.room_id:
                raise ValueError("room source evidence requires room_id")
        elif self.room_id is not None:
            raise ValueError("room_id is valid only for room source evidence")
        if self.operation == "SEARCH":
            if not self.query or "\n" in self.query or "\r" in self.query:
                raise ValueError("SEARCH source evidence requires one non-empty query line")
        elif self.query is not None:
            raise ValueError("query is valid only for SEARCH source evidence")
        return self


class HistoryRequest(BaseModel):
    operation: Literal["RECENT", "SEARCH"]
    query: str | None = Field(default=None, max_length=4096)
    agent: Literal["agent_a", "agent_b", "agent_c"] | None = None
    max_results: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def validate_history_request(self) -> "HistoryRequest":
        if self.operation == "SEARCH":
            if not self.query or "\n" in self.query or "\r" in self.query:
                raise ValueError("SEARCH history retrieval requires one non-empty query line")
        elif self.query is not None:
            raise ValueError("query is valid only for SEARCH history retrieval")
        return self


class TransactionDecision(BaseModel):
    action: TransactionAction
    message: str = ""
    checkpoint: str | None = Field(default=None, max_length=12_000)
    delegations: list[DelegationRequest] | None = None
    delegation_return_mode: Literal["parent", "coordinator"] | None = None
    retire_worker_context_task_ids: list[str] | None = None
    evidence_requests: list[SourceEvidenceRequest] | None = None
    history_requests: list[HistoryRequest] | None = None
    next_self_config: str | None = Field(default=None, min_length=1, max_length=200)
    requested_task_cognition_ceiling: ExceptionalCExecutionConfigId | None = None

    @model_validator(mode="after")
    def validate_transaction_decision(self) -> "TransactionDecision":
        self.message = self.message.strip()
        if self.action in {
            TransactionAction.COMPLETE,
            TransactionAction.CONSULT_PRINCIPAL,
        } and not self.message:
            raise ValueError(f"{self.action} requires non-empty message text")
        if self.action == TransactionAction.REFRESH:
            if self.checkpoint is None or not self.checkpoint.strip():
                raise ValueError("REFRESH requires a non-empty coordinator checkpoint")
            self.checkpoint = self.checkpoint.strip()
        elif self.checkpoint is not None:
            raise ValueError("checkpoint is valid only for REFRESH")
        if self.action == TransactionAction.DELEGATE:
            if not self.delegations:
                raise ValueError("DELEGATE requires at least one delegation")
            targets = [item.target for item in self.delegations]
            if len(targets) != len(set(targets)):
                raise ValueError("delegations cannot contain duplicate targets")
            if (
                self.delegation_return_mode == "coordinator"
                and len(self.delegations) != 1
            ):
                raise ValueError(
                    "coordinator delegation return requires exactly one child assignment"
                )
        elif self.delegations is not None:
            raise ValueError("delegations is valid only for DELEGATE")
        if self.action != TransactionAction.DELEGATE and self.delegation_return_mode is not None:
            raise ValueError("delegation_return_mode is valid only for DELEGATE")
        if self.retire_worker_context_task_ids is not None:
            cleaned = [item.strip() for item in self.retire_worker_context_task_ids]
            if any(not item for item in cleaned):
                raise ValueError("retire_worker_context_task_ids cannot contain empty IDs")
            if any(len(item) > 200 for item in cleaned):
                raise ValueError(
                    "retire_worker_context_task_ids entries are limited to 200 characters"
                )
            if len(cleaned) > 8:
                raise ValueError(
                    "retire_worker_context_task_ids accepts at most 8 Task IDs"
                )
            if len(cleaned) != len(set(cleaned)):
                raise ValueError(
                    "retire_worker_context_task_ids cannot contain duplicates"
                )
            self.retire_worker_context_task_ids = cleaned
        if self.action == TransactionAction.EVIDENCE:
            if not self.evidence_requests:
                raise ValueError("EVIDENCE requires at least one source evidence request")
            if len(self.evidence_requests) > 16:
                raise ValueError("EVIDENCE accepts at most 16 source evidence requests")
        elif self.evidence_requests is not None:
            raise ValueError("evidence_requests is valid only for EVIDENCE")
        if self.action == TransactionAction.HISTORY:
            if not self.history_requests:
                raise ValueError("HISTORY requires at least one Room-history request")
            if len(self.history_requests) > 4:
                raise ValueError("HISTORY accepts at most 4 Room-history requests")
        elif self.history_requests is not None:
            raise ValueError("history_requests is valid only for HISTORY")
        if self.action in {TransactionAction.COMPLETE, TransactionAction.PASS}:
            if self.next_self_config is not None:
                raise ValueError("next_self_config is valid only for nonterminal actions")
        if self.requested_task_cognition_ceiling is not None:
            if self.action != TransactionAction.CONSULT_PRINCIPAL:
                raise ValueError(
                    "requested_task_cognition_ceiling is valid only for CONSULT_PRINCIPAL"
                )
            if self.next_self_config is not None:
                raise ValueError(
                    "cognition-ceiling consultation cannot also set next_self_config"
                )
        return self


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
                                    "luna-low",
                                    "luna-medium",
                                    "luna-high",
                                    "terra-low",
                                    "terra-medium",
                                    "terra-high",
                                    "sol-low",
                                    "sol-medium",
                                    "sol-high",
                                    "astra-low",
                                    "astra-medium",
                                    "astra-high",
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



TRANSACTION_DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "COMPLETE",
                "DELEGATE",
                "EVIDENCE",
                "HISTORY",
                "REFRESH",
                "CONSULT_PRINCIPAL",
                "PASS",
            ],
        },
        "message": {"type": "string"},
        "checkpoint": {
            "anyOf": [
                {"type": "string", "minLength": 1, "maxLength": 12000},
                {"type": "null"},
            ]
        },
        "delegations": {
            "anyOf": [
                {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "enum": ["agent_a", "agent_b", "agent_c"],
                            },
                            "instruction": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 50_000,
                            },
                            "config": {
                                "anyOf": [
                                    {
                                        "type": "string",
                                        "minLength": 1,
                                        "maxLength": 200,
                                    },
                                    {"type": "null"},
                                ]
                            },
                            "context_from_assignment_id": {
                                "anyOf": [
                                    {"type": "string", "minLength": 1, "maxLength": 200},
                                    {"type": "null"},
                                ]
                            },
                            "fresh_context": {"type": "boolean"},
                        },
                        "required": [
                            "target",
                            "instruction",
                            "config",
                            "context_from_assignment_id",
                            "fresh_context",
                        ],
                        "additionalProperties": False,
                    },
                },
                {"type": "null"},
            ]
        },
        "delegation_return_mode": {
            "anyOf": [
                {"type": "string", "enum": ["parent", "coordinator"]},
                {"type": "null"},
            ]
        },
        "retire_worker_context_task_ids": {
            "anyOf": [
                {
                    "type": "array",
                    "maxItems": 8,
                    "items": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200,
                    },
                },
                {"type": "null"},
            ]
        },
        "evidence_requests": {
            "anyOf": [
                {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 16,
                    "items": {
                        "anyOf": [
                            {
                                "type": "object",
                                "properties": {
                                    "operation": {"type": "string", "enum": ["READ"]},
                                    "source": {
                                        "type": "string",
                                        "enum": ["workspace", "core", "room"],
                                    },
                                    "room_id": {
                                        "anyOf": [{"type": "string"}, {"type": "null"}]
                                    },
                                    "path": {
                                        "type": "string",
                                        "minLength": 1,
                                        "maxLength": 4096,
                                    },
                                    "start_line": {
                                        "type": "integer",
                                        "minimum": 1,
                                    },
                                    "max_lines": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 1000,
                                    },
                                    "max_bytes": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 128 * 1024,
                                    },
                                },
                                "required": [
                                    "operation",
                                    "source",
                                    "room_id",
                                    "path",
                                    "start_line",
                                    "max_lines",
                                    "max_bytes",
                                ],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "operation": {"type": "string", "enum": ["SEARCH"]},
                                    "source": {
                                        "type": "string",
                                        "enum": ["workspace", "core", "room"],
                                    },
                                    "room_id": {
                                        "anyOf": [{"type": "string"}, {"type": "null"}]
                                    },
                                    "path": {
                                        "type": "string",
                                        "minLength": 1,
                                        "maxLength": 4096,
                                    },
                                    "query": {
                                        "type": "string",
                                        "minLength": 1,
                                        "maxLength": 4096,
                                    },
                                    "include_globs": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "exclude_globs": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "include_hidden": {"type": "boolean"},
                                    "case_sensitive": {"type": "boolean"},
                                    "max_files": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 200,
                                    },
                                    "max_matches": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 100,
                                    },
                                },
                                "required": [
                                    "operation",
                                    "source",
                                    "room_id",
                                    "path",
                                    "query",
                                    "include_globs",
                                    "exclude_globs",
                                    "include_hidden",
                                    "case_sensitive",
                                    "max_files",
                                    "max_matches",
                                ],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "operation": {"type": "string", "enum": ["FIND"]},
                                    "source": {
                                        "type": "string",
                                        "enum": ["workspace", "core", "room"],
                                    },
                                    "room_id": {
                                        "anyOf": [{"type": "string"}, {"type": "null"}]
                                    },
                                    "path": {
                                        "type": "string",
                                        "minLength": 1,
                                        "maxLength": 4096,
                                    },
                                    "include_globs": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "exclude_globs": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "include_hidden": {"type": "boolean"},
                                    "max_results": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 200,
                                    },
                                },
                                "required": [
                                    "operation",
                                    "source",
                                    "room_id",
                                    "path",
                                    "include_globs",
                                    "exclude_globs",
                                    "include_hidden",
                                    "max_results",
                                ],
                                "additionalProperties": False,
                            },
                        ]
                    },
                },
                {"type": "null"},
            ]
        },
        "next_self_config": {
            "anyOf": [
                {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 200,
                },
                {"type": "null"},
            ]
        },
        "requested_task_cognition_ceiling": {
            "anyOf": [
                {"type": "string", "enum": ["sol-xhigh", "sol-max"]},
                {"type": "null"},
            ]
        },
        "history_requests": {
            "anyOf": [
                {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {
                        "anyOf": [
                            {
                                "type": "object",
                                "properties": {
                                    "operation": {"type": "string", "enum": ["RECENT"]},
                                    "query": {"type": "null"},
                                    "agent": {
                                        "anyOf": [
                                            {
                                                "type": "string",
                                                "enum": ["agent_a", "agent_b", "agent_c"],
                                            },
                                            {"type": "null"},
                                        ]
                                    },
                                    "max_results": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 10,
                                    },
                                },
                                "required": [
                                    "operation",
                                    "query",
                                    "agent",
                                    "max_results",
                                ],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "operation": {"type": "string", "enum": ["SEARCH"]},
                                    "query": {
                                        "type": "string",
                                        "minLength": 1,
                                        "maxLength": 4096,
                                    },
                                    "agent": {
                                        "anyOf": [
                                            {
                                                "type": "string",
                                                "enum": ["agent_a", "agent_b", "agent_c"],
                                            },
                                            {"type": "null"},
                                        ]
                                    },
                                    "max_results": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 10,
                                    },
                                },
                                "required": [
                                    "operation",
                                    "query",
                                    "agent",
                                    "max_results",
                                ],
                                "additionalProperties": False,
                            },
                        ]
                    },
                },
                {"type": "null"},
            ]
        },
    },
    "required": [
        "action",
        "message",
        "checkpoint",
        "delegations",
        "delegation_return_mode",
        "retire_worker_context_task_ids",
        "evidence_requests",
        "history_requests",
        "next_self_config",
        "requested_task_cognition_ceiling",
    ],
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
    work_model_version: Literal[1, 2] = 1
    provider_context_mode: Literal["persistent_agent_thread", "assignment_thread"] = (
        "persistent_agent_thread"
    )
    completion_policy: Literal["auto_settle", "continuous"] = "auto_settle"
    model_policy: ModelPolicy = "default"
    required_contributors: list[
        Literal["agent_a", "agent_b", "agent_c"]
    ] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_required_contributors(self) -> "CreateRoomRequest":
        if len(self.required_contributors) != len(set(self.required_contributors)):
            raise ValueError("required_contributors cannot contain duplicates")
        if (
            self.provider_context_mode == "assignment_thread"
            and self.work_model_version != 2
        ):
            raise ValueError(
                "assignment_thread provider context requires work_model_version=2"
            )
        return self


class CreateRoomApiRequest(CreateRoomRequest):
    """Production API contract after the work-model-v2 default cutover."""

    work_model_version: Literal[2] = 2
    provider_context_mode: Literal["assignment_thread"] = "assignment_thread"


class AddAgentRequest(BaseModel):
    agent_key: Literal["agent_c"] = "agent_c"


class RolloverRoomRequest(BaseModel):
    checkpoint: str = Field(min_length=1, max_length=50_000)
    title: str | None = Field(default=None, min_length=1, max_length=120)
    institutional_release_sha256: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )


class RolloverRoomApiRequest(RolloverRoomRequest):
    """Production rollover contract after the work-model-v2 default cutover."""

    work_model_version: Literal[2] = 2
    provider_context_mode: Literal["assignment_thread"] = "assignment_thread"


class BindInstitutionalReleaseRequest(BaseModel):
    institutional_release_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ObserverImageAttachmentInput(BaseModel):
    filename: str = Field(min_length=1, max_length=240)
    media_type: Literal["image/png", "image/jpeg", "image/webp"]
    data_url: str = Field(min_length=1, max_length=MAX_OBSERVER_IMAGE_DATA_URL_CHARS)


class ObserverMessageRequest(BaseModel):
    target: Literal["all", "both", "agent_a", "agent_b", "agent_c"]
    content: str = Field(default="", max_length=50_000)
    images: list[ObserverImageAttachmentInput] = Field(
        default_factory=list,
        max_length=MAX_OBSERVER_IMAGES,
    )

    @model_validator(mode="after")
    def validate_observer_message_payload(self) -> "ObserverMessageRequest":
        if not self.content.strip() and not self.images:
            raise ValueError("Observer message requires text or at least one image")
        return self


class PrincipalReplyRequest(BaseModel):
    consultation_event_id: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50_000)
    cognition_approval: Literal["approve", "decline"] | None = None


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
    work_model_version: Literal[1, 2] = 1
    provider_context_mode: Literal["persistent_agent_thread", "assignment_thread"] = (
        "persistent_agent_thread"
    )
    completion_policy: Literal["auto_settle", "continuous"] = "auto_settle"
    required_contributors: list[
        Literal["agent_a", "agent_b", "agent_c"]
    ] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_participant_maps(self) -> "PrepareRoundRequest":
        allowed = {"agent_a", "agent_b", "agent_c"}
        if len(self.required_contributors) != len(set(self.required_contributors)):
            raise ValueError("required_contributors cannot contain duplicates")
        if (
            self.provider_context_mode == "assignment_thread"
            and self.work_model_version != 2
        ):
            raise ValueError(
                "assignment_thread provider context requires work_model_version=2"
            )
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


class PrepareRoundApiRequest(PrepareRoundRequest):
    """Production API contract after the work-model-v2 default cutover."""

    work_model_version: Literal[2] = 2
    provider_context_mode: Literal["assignment_thread"] = "assignment_thread"


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
