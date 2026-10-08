"""Anthropic provider implementation"""
import json
from typing import AsyncGenerator, Dict, Any, List, Optional
from anthropic import Anthropic, AsyncAnthropic
from stream_mypy.types import (
    Provider,
    StreamOptions,
    StreamEvent,
    Message,
    ContentBlock,
    TextBlock,
    ToolCallBlock,
    StopReason,
    ToolSpec,
)


def to_anthropic_messages(messages: List[Message]) -> List[Dict[str, Any]]:
    """Convert our message format to Anthropic's format"""
    result = []
    
    for msg in messages:
        if msg["role"] == "user":
            result.append({
                "role": "user",
                "content": msg["content"],
            })
        elif msg["role"] == "assistant":
            content = []
            for block in msg["content"]:
                if block["type"] == "text":
                    content.append({
                        "type": "text",
                        "text": block["text"],
                    })
                elif block["type"] == "toolCall":
                    content.append({
                        "type": "tool_use",
                        "id": block["id"],
                        "name": block["name"],
                        "input": block["arguments"],
                    })
            result.append({
                "role": "assistant",
                "content": content,
            })
        elif msg["role"] == "toolResult":
            # Tool results go in a user message for Anthropic
            result.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg["toolCallId"],
                        "content": msg["content"],
                        "is_error": msg["isError"],
                    }
                ],
            })
    
    return result


class AnthropicProvider(Provider):
    """Provider for Anthropic's Claude model"""
    
    def __init__(self):
        super().__init__("anthropic", "claude-sonnet-4-20250514")
        self.client = AsyncAnthropic()
    
    async def stream(self, opts: StreamOptions) -> AsyncGenerator[StreamEvent, None]:
        """Stream responses from Claude"""
        messages = to_anthropic_messages(opts["messages"])
        model = opts["model"]
        system = opts.get("system")
        tools = opts.get("tools", [])
        
        # Convert tools to Anthropic format
        anthropic_tools = []
        if tools:
            for tool in tools:
                anthropic_tools.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["parameters"],
                })
        
        # Create the stream
        async with self.client.messages.stream(
            model=model,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=anthropic_tools if anthropic_tools else None,
        ) as stream:
            content: List[ContentBlock] = []
            current_tool_id = None
            current_tool_name = None
            current_tool_input_json = ""
            
            async for event in stream:
                event_type = event.type
                
                if event_type == "content_block_start":
                    block = event.content_block
                    if block.type == "text":
                        content.append({"type": "text", "text": ""})
                    elif block.type == "tool_use":
                        current_tool_id = block.id
                        current_tool_name = block.name
                        current_tool_input_json = ""
                        content.append({
                            "type": "toolCall",
                            "id": block.id,
                            "name": block.name,
                            "arguments": {},
                        })
                
                elif event_type == "content_block_delta":
                    delta = event.delta
                    if hasattr(delta, "text"):
                        # Text delta
                        block = content[-1] if content else None
                        if block and block["type"] == "text":
                            block["text"] += delta.text
                            yield {"type": "text_delta", "delta": delta.text}
                    elif hasattr(delta, "partial_json"):
                        # Tool input JSON delta
                        current_tool_input_json += delta.partial_json
                
                elif event_type == "content_block_stop":
                    # Finalize tool input if present
                    if current_tool_id and current_tool_input_json:
                        block = content[-1] if content else None
                        if block and block["type"] == "toolCall":
                            try:
                                block["arguments"] = json.loads(current_tool_input_json)
                            except json.JSONDecodeError:
                                block["arguments"] = {}
                        current_tool_id = None
                        current_tool_name = None
                        current_tool_input_json = ""
            
            # Get final message for usage and stop reason
            final_message = await stream.get_final_message()
            
            stop_reason: StopReason = "stop"
            if final_message.stop_reason == "tool_use":
                stop_reason = "toolUse"
            elif final_message.stop_reason == "max_tokens":
                stop_reason = "length"
            
            usage = {
                "input": final_message.usage.input_tokens,
                "output": final_message.usage.output_tokens,
            }
            
            yield {
                "type": "done",
                "message": {
                    "role": "assistant",
                    "content": content,
                    "usage": usage,
                    "stopReason": stop_reason,
                },
            }


def create_anthropic() -> Provider:
    """Factory function to create Anthropic provider"""
    return AnthropicProvider()
