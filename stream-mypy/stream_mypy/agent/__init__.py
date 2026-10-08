"""Agent loop implementation"""
from typing import Callable, Dict, Any, Optional, List
from stream_mypy.types import Provider, Tool, Message, AssistantMessage, ToolCallBlock


class AgentEvent:
    """Base class for agent events"""
    pass


class TextEvent:
    def __init__(self, delta: str):
        self.type = "text"
        self.delta = delta


class ToolStartEvent:
    def __init__(self, call: ToolCallBlock):
        self.type = "tool_start"
        self.call = call


class ToolEndEvent:
    def __init__(self, call: ToolCallBlock, result: str, is_error: bool):
        self.type = "tool_end"
        self.call = call
        self.result = result
        self.is_error = is_error


class TurnEndEvent:
    def __init__(self, message: AssistantMessage):
        self.type = "turn_end"
        self.message = message


class MessageEvent:
    def __init__(self, message: Message):
        self.type = "message"
        self.message = message


async def run_agent(
    provider: Provider,
    model: str,
    tools: List[Tool],
    messages: List[Message],
    on_event: Callable[[Any], None],
    system: Optional[str] = None,
    max_turns: int = 20,
) -> None:
    """Run the agent loop"""
    
    def push(message: Message):
        messages.append(message)
        on_event(MessageEvent(message))
    
    for turn in range(1, max_turns + 1):
        # Get response from provider
        assistant: Optional[AssistantMessage] = None
        
        async for event in provider.stream({
            "messages": messages,
            "model": model,
            "system": system,
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
                for tool in tools
            ] if tools else [],
        }):
            if event.get("type") == "text_delta":
                on_event(TextEvent(event.get("delta", "")))
            elif event.get("type") == "done":
                assistant = event.get("message")
        
        if not assistant:
            raise RuntimeError("Assistant message is empty")
        
        push(assistant)
        on_event(TurnEndEvent(assistant))
        
        # Check if we should continue
        if assistant["stopReason"] != "toolUse":
            return
        
        # Execute tools
        for call in assistant["content"]:
            if call["type"] != "toolCall":
                continue
            
            on_event(ToolStartEvent(call))
            
            result = ""
            is_error = False
            
            try:
                tool = next((t for t in tools if t.name == call["name"]), None)
                if not tool:
                    raise RuntimeError(f"Unknown tool: {call['name']}")
                
                result = await tool.execute(call["arguments"])
            except Exception as e:
                result = f"Error: {str(e)}"
                is_error = True
            
            on_event(ToolEndEvent(call, result, is_error))
            
            push({
                "role": "toolResult",
                "toolCallId": call["id"],
                "toolName": call["name"],
                "content": result,
                "isError": is_error,
            })
    
    raise RuntimeError(f"Agent stopped after {max_turns} turns")
