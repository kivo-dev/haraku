from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Message:
    """One conversation message. role: user | assistant | tool."""

    role: str
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)  # assistant messages only
    tool_call_id: Optional[str] = None  # tool messages only


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema (object)


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall]
    usage: Usage = field(default_factory=Usage)
    model: str = ""
