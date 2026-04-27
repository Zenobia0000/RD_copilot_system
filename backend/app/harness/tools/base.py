"""Tool base class — anything an agent can call."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class ToolResult:
    """The string sent back to the model as `tool_result.content`."""

    content: str
    is_error: bool = False


class Tool(ABC):
    """Subclass and override the three class vars + run()."""

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    input_schema: ClassVar[dict[str, Any]] = {}

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult: ...

    def to_anthropic_schema(self) -> dict[str, Any]:
        """Shape that the Anthropic Messages API expects in `tools=[...]`."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }
