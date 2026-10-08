"""OpenAI-compatible provider implementation"""
import json
from typing import AsyncGenerator, Dict, Any, List, Optional
from openai import AsyncOpenAI
from stream_mypy.types import (
    Provider,
    StreamOptions,
    StreamEvent,
    Message,
    ContentBlock,
    TextBlock,
    ToolCallBlock,
    StopReason,
    Usage,
    ToolSpec,
)


def to_openai_messages(messages: List[Message]) -> List[Dict[str, Any]]:
    """Convert our message format to OpenAI's format"""
    result = []
    
    for msg in messages:
        if msg["role"] == "user":
            result.append({
                "role": "user",
                "content": msg["content"],
            })
        elif msg["role"] == "assistant":
            # Separate text and tool calls
            text_blocks = [b for b in msg["content"] if b["type"] == "text"]
            tool_blocks = [b for b in msg["content"] if b["type"] == "toolCall"]
            
            text = "".join(b["text"] for b in text_blocks)
            
            tool_calls = None
            if tool_blocks:
                tool_calls = [
                    {
                        "id": b["id"],
                        "type": "function",
                        "function": {
                            "name": b["name"],
                            "arguments": json.dumps(b["arguments"]),
                        },
                    }
                    for b in tool_blocks
                ]
            
            result.append({
                "role": "assistant",
                "content": text if text else None,
                "tool_calls": tool_calls,
            })
        elif msg["role"] == "toolResult":
            result.append({
                "role": "tool",
                "tool_call_id": msg["toolCallId"],
                "content": msg["content"],
            })
    
    return result


class OpenAICompatibleProvider(Provider):
    """Provider for OpenAI-compatible APIs"""
    
    def __init__(self, name: str, base_url: str, api_key: Optional[str], default_model: str):
        super().__init__(name, default_model)
        self.base_url = base_url
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    
    async def stream(self, opts: StreamOptions) -> AsyncGenerator[StreamEvent, None]:
        """Stream responses from OpenAI-compatible API"""
        messages = to_openai_messages(opts["messages"])
        model = opts["model"]
        system = opts.get("system")
        tools = opts.get("tools", [])
        
        # Prepend system message if provided
        if system:
            messages.insert(0, {"role": "system", "content": system})
        
        # Convert tools to OpenAI format
        openai_tools = None
        if tools:
            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    },
                }
                for tool in tools
            ]
        
        # Create the stream
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
            tools=openai_tools if openai_tools else None,
        )
        
        text = ""
        calls: Dict[int, Dict[str, str]] = {}  # index -> {id, name, args}
        usage: Usage = {"input": 0, "output": 0}
        stop_reason: StopReason = "stop"
        
        async for chunk in stream:
            if not chunk.choices:
                continue
            
            choice = chunk.choices[0]
            
            # Handle text content
            if choice.delta.content:
                text += choice.delta.content
                yield {"type": "text_delta", "delta": choice.delta.content}
            
            # Handle tool calls
            if choice.delta.tool_calls:
                for tc in choice.delta.tool_calls:
                    idx = tc.index
                    if idx not in calls:
                        calls[idx] = {
                            "id": tc.id or f"call_{idx}",
                            "name": tc.function.name or "",
                            "args": "",
                        }
                    if tc.function.arguments:
                        calls[idx]["args"] += tc.function.arguments
            
            # Check finish reason
            if choice.finish_reason == "tool_calls":
                stop_reason = "toolUse"
            elif choice.finish_reason == "length":
                stop_reason = "length"
            
            # Update usage if available
            if chunk.usage:
                usage["input"] = chunk.usage.prompt_tokens
                usage["output"] = chunk.usage.completion_tokens
        
        # Build final content
        content: List[ContentBlock] = []
        
        if text:
            content.append({"type": "text", "text": text})
        
        # Add tool calls
        for idx in sorted(calls.keys()):
            call = calls[idx]
            try:
                arguments = json.loads(call["args"]) if call["args"] else {}
            except json.JSONDecodeError:
                arguments = {}
            
            content.append({
                "type": "toolCall",
                "id": call["id"],
                "name": call["name"],
                "arguments": arguments,
            })
        
        # If we have tool calls, update stop reason
        if any(b["type"] == "toolCall" for b in content):
            stop_reason = "toolUse"
        
        yield {
            "type": "done",
            "message": {
                "role": "assistant",
                "content": content,
                "usage": usage,
                "stopReason": stop_reason,
            },
        }


def create_openai_compat(
    name: str,
    base_url: str,
    api_key: Optional[str],
    default_model: str,
) -> Provider:
    """Factory function to create OpenAI-compatible provider"""
    return OpenAICompatibleProvider(name, base_url, api_key, default_model)
