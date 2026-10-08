"""Type definitions for stream-mypy"""
from typing import TypedDict, Union, List, Dict, Any, Literal, Optional


class Usage(TypedDict):
    input: int
    output: int


StopReason = Literal["stop", "length", "toolUse"]


class TextBlock(TypedDict):
    type: Literal["text"]
    text: str


class ToolCallBlock(TypedDict):
    type: Literal["toolCall"]
    id: str
    name: str
    arguments: Dict[str, Any]


ContentBlock = Union[TextBlock, ToolCallBlock]


class UserMessage(TypedDict):
    role: Literal["user"]
    content: str


class AssistantMessage(TypedDict):
    role: Literal["assistant"]
    content: List[ContentBlock]
    usage: Usage
    stopReason: StopReason


class ToolResultMessage(TypedDict):
    role: Literal["toolResult"]
    toolCallId: str
    toolName: str
    content: str
    isError: bool


Message = Union[UserMessage, AssistantMessage, ToolResultMessage]


class ToolSpec(TypedDict):
    name: str
    description: str
    parameters: Dict[str, Any]


class Tool:
    """Base Tool interface"""
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    async def execute(self, args: Dict[str, Any]) -> str:
        raise NotImplementedError


class StreamEvent(TypedDict, total=False):
    type: str
    delta: str
    message: AssistantMessage


class StreamOptions(TypedDict, total=False):
    messages: List[Message]
    model: str
    system: str
    tools: List[ToolSpec]


class Provider:
    """Base Provider interface"""
    def __init__(self, name: str, default_model: str):
        self.name = name
        self.default_model = default_model
    
    async def stream(self, opts: StreamOptions):
        raise NotImplementedError
