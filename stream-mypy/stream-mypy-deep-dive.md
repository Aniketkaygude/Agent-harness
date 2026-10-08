# stream-mypy: A Deep Dive into Agentic AI Architecture

**Table of Contents**
1. [What is stream-mypy?](#what-is-stream-mypy)
2. [Agentic/AI Concepts](#agentiCai-concepts)
3. [Repository Architecture](#repository-architecture)
4. [Code Walkthrough](#code-walkthrough)
5. [Python Concepts](#python-concepts)
6. [Streaming Deep Dive](#streaming-deep-dive)
7. [Type System](#type-system)
8. [Design & Engineering](#design--engineering)
9. [Tests, Errors & Debugging](#tests-errors--debugging)
10. [How to Extend It](#how-to-extend-it)
11. [Final Mental Model](#final-mental-model)

---

## What is stream-mypy?

### Problem Statement

**The Problem:** Suppose you want to build an AI agent that:
- Talks to a large language model (LLM) like Claude or GPT
- Can use tools (like running bash commands or reading files)
- Gets real-time responses (streaming)
- Can handle multi-turn conversations where the model requests tools and you execute them

**Naïve Approach:** You might write:
```python
response = claude.ask("What files are in this directory?")
# Claude says: "I should use the bash command to list files"
# Then you manually execute `/bin/ls`, get results, and ask Claude again
# This is error-prone and doesn't scale
```

**Better Approach:** Build an autonomous agent that:
1. Sends a prompt to the LLM
2. **Streams** responses in real-time (text piece-by-piece)
3. Detects when the LLM wants to use a tool
4. Automatically executes that tool
5. Feeds the results back to the LLM
6. Repeats until the LLM says it's done (or max turns exceeded)

All while streaming text output to the user in real-time.

### What stream-mypy Does

**stream-mypy** is a Python framework that implements this autonomous agent pattern. It:

1. **Abstracts multiple LLM providers** — supports Anthropic Claude, OpenAI, Groq, etc.
2. **Provides streaming responses** — real-time text output using async generators
3. **Implements an agent loop** — automatically executes tools and continues the conversation
4. **Includes built-in tools** — bash, file read, directory listing, grep, find, stat
5. **Provides a CLI interface** — run agents from the command line: `python -m stream_mypy.main -p "Your prompt"`

### Why It Exists

Before stream-mypy, you'd need to:
- Write provider-specific code for each LLM (Anthropic, OpenAI, etc.)
- Handle streaming yourself with complex event loops
- Manually parse tool calls and execute them
- Manage conversation state across multiple turns
- Deal with timeouts, truncation, and error handling

**stream-mypy eliminates all of this** by providing a unified, battle-tested abstraction.

### High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│           User (CLI or Python code)             │
└──────────────────┬──────────────────────────────┘
                   │
                   │ Prompt: "What files are here?"
                   ▼
        ┌──────────────────────┐
        │   Main (main.py)      │
        │ - Parse arguments     │
        │ - Load .env           │
        │ - Get provider & model│
        └──────────┬────────────┘
                   │
                   │ Create Provider + Tools
                   ▼
        ┌──────────────────────┐
        │   Agent Loop (agent) │
        │ - Get response from  │
        │   LLM provider       │
        │ - Extract tool calls │
        │ - Execute tools      │
        │ - Feed results back  │
        │ - Emit events        │
        └──────────┬────────────┘
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
   ┌────────────────┐  ┌──────────────────┐
   │  Providers     │  │  Tools           │
   │ ┌────────────┐ │  │ ┌──────────────┐ │
   │ │ Anthropic  │ │  │ │ bash         │ │
   │ │ OpenAI     │ │  │ │ read         │ │
   │ │ Groq       │ │  │ │ ls (walk)    │ │
   │ └────────────┘ │  │ │ grep         │ │
   │ Stream Claude  │  │ │ find         │ │
   │ responses &    │  │ │ stat         │ │
   │ tool calls     │  │ └──────────────┘ │
   └────────────────┘  │ Execute & return │
                       │ results as text  │
                       └──────────────────┘
```

### End-to-End Execution Flow

1. **Initialization:** User runs `python -m stream_mypy.main -p "What's in this folder?" --provider anthropic`
2. **Setup:** main.py loads env vars, creates an Anthropic provider, initializes tools list
3. **First Turn:**
   - Agent sends prompt + tools to Claude via streaming API
   - Claude responds with: "I'll use the `ls` tool to list files"
   - Agent detects tool call, emits `TextEvent` for each text chunk
4. **Tool Execution:**
   - Agent calls `ls_tool.execute({"path": "."})`
   - Tool walks the filesystem, returns results
   - Agent emits `ToolStartEvent`, `ToolEndEvent`
5. **Second Turn:**
   - Agent adds tool result to conversation
   - Sends full conversation (prompt + assistant response + tool result) back to Claude
   - Claude provides a natural language summary
   - Claude's `stopReason` is "stop" (not "toolUse"), so agent exits
6. **Exit:** All events and final response streamed to stdout

### Simple Mental Model

**Think of stream-mypy as a "bridge" between you and the LLM:**

```python
You: "What files are here?"
  ↓
stream-mypy (Agent)
  ├─ Calls Claude API (streaming)
  ├─ Claude says: "Use ls tool"
  ├─ Executes ls tool → gets file list
  ├─ Tells Claude the results
  ├─ Claude provides summary
  └─ Returns final answer to you
```

The agent is **autonomous** — it doesn't wait for you to manually execute tools. It sees what the LLM wants and does it automatically.

---

## Agentic/AI Concepts

### What is an Agent?

An **agent** is a program that:
1. **Observes** the current state (conversation history)
2. **Decides** what to do (call LLM, execute tool, exit)
3. **Acts** (calls LLM or tool)
4. **Repeats** until it reaches a goal or max attempts

Unlike simple LLM chatbots (which just return text), agents take **actions in the world** (execute tools) and respond to **feedback** (tool results).

### Where It's Implemented in stream-mypy

**File:** `stream_mypy/agent/__init__.py`, function `run_agent()`

```python
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
    
    for turn in range(1, max_turns + 1):
        # Observe: Get LLM response
        assistant: Optional[AssistantMessage] = None
        
        async for event in provider.stream({...}):
            if event.get("type") == "text_delta":
                on_event(TextEvent(event.get("delta", "")))  # Stream text to user
            elif event.get("type") == "done":
                assistant = event.get("message")  # Final response
        
        if not assistant:
            raise RuntimeError("Assistant message is empty")
        
        push(assistant)
        on_event(TurnEndEvent(assistant))
        
        # Decide: Should we continue?
        if assistant["stopReason"] != "toolUse":
            return  # Agent decides: "I'm done"
        
        # Act: Execute tools
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
                
                result = await tool.execute(call["arguments"])  # Act: Execute tool
            except Exception as e:
                result = f"Error: {str(e)}"
                is_error = True
            
            on_event(ToolEndEvent(call, result, is_error))
            
            # Observe: Add tool result to conversation
            push({
                "role": "toolResult",
                "toolCallId": call["id"],
                "toolName": call["name"],
                "content": result,
                "isError": is_error,
            })
    
    raise RuntimeError(f"Agent stopped after {max_turns} turns")
```

**Key Points:**
- **Observe-Decide-Act loop:** Get response → check if done → execute tools → loop
- **Turn-based:** Each iteration is one "turn"
- **Max turns:** Prevent infinite loops (default 20)
- **Event-driven:** Emits events for UI/logging

### Tool Use / Function Calling

**Concept:** An LLM can request tools instead of just returning text.

Example response from Claude:
```json
{
  "role": "assistant",
  "content": [
    {"type": "text", "text": "Let me check the files in this directory."},
    {
      "type": "toolCall",
      "id": "call_123",
      "name": "ls",
      "arguments": {"path": "src"}
    }
  ]
}
```

The LLM is essentially saying: "Here's some text, and by the way, I want to call the `ls` tool with these arguments."

### Where Tool Use is Detected

**File:** `stream_mypy/providers/anthropic.py`

The Anthropic provider's `stream()` method processes streaming events:

```python
async for event in stream:
    event_type = event.type
    
    if event_type == "content_block_start":
        block = event.content_block
        if block.type == "tool_use":
            # Detect: LLM is about to call a tool
            current_tool_id = block.id
            current_tool_name = block.name
            current_tool_input_json = ""
            content.append({
                "type": "toolCall",
                "id": block.id,
                "name": block.name,
                "arguments": {},  # Will be filled in as JSON arrives
            })
    
    elif event_type == "content_block_delta":
        delta = event.delta
        if hasattr(delta, "partial_json"):
            # Accumulate JSON arguments as they stream
            current_tool_input_json += delta.partial_json
    
    elif event_type == "content_block_stop":
        # Parse final JSON into Python dict
        if current_tool_id and current_tool_input_json:
            block = content[-1] if content else None
            if block and block["type"] == "toolCall":
                try:
                    block["arguments"] = json.loads(current_tool_input_json)
                except json.JSONDecodeError:
                    block["arguments"] = {}
```

**Important:** Tool arguments stream as JSON, one chunk at a time. The provider buffers them and parses at the end.

### Message Formats & Adaptation

**Concept:** Different LLM APIs have different message formats:
- **Anthropic:** Uses `tool_use` for tool calls, `tool_result` in user messages
- **OpenAI:** Uses `function` calls, separate `tool` role for results

**Where It's Implemented:** 
- `stream_mypy/providers/anthropic.py` → `to_anthropic_messages()`
- `stream_mypy/providers/openai_compat.py` → `to_openai_messages()`

These **adapters** translate our unified message format into each provider's native format.

### Concept: Streaming

**Why streaming?** If the LLM takes 5 seconds to respond, without streaming the user waits 5 seconds then sees the full response. With streaming, they see text appear in real-time.

**Benefits:**
- User perceives faster response
- Can cancel long responses
- Text appears while model is still thinking

---

## Repository Architecture

### Directory Structure

```
stream-mypy/
├── stream_mypy/                 # Main package
│   ├── __init__.py              # Package marker
│   ├── main.py                  # CLI entry point (103 lines)
│   ├── types.py                 # Type definitions (88 lines)
│   │
│   ├── agent/
│   │   └── __init__.py          # Agent loop (120 lines)
│   │
│   ├── providers/
│   │   ├── __init__.py          # Provider factory (30 lines)
│   │   ├── anthropic.py         # Anthropic Claude (171 lines)
│   │   └── openai_compat.py     # OpenAI/Groq (191 lines)
│   │
│   └── tools/
│       ├── __init__.py          # Tool registry (11 lines)
│       ├── fsutil.py            # Async filesystem walk (98 lines)
│       ├── bash.py              # Bash execution (110 lines)
│       ├── read.py              # File reading (32 lines)
│       ├── ls.py                # Directory listing (70 lines)
│       ├── grep.py              # Pattern search (108 lines)
│       ├── find.py              # File finding (112 lines)
│       └── stat.py              # File metadata (77 lines)
│
├── mypi.py                      # CLI wrapper
├── pyproject.toml               # Poetry config
├── requirements.txt             # Pip dependencies
├── .env                         # Environment variables
├── README.md                    # User guide
├── MIGRATION.md                 # Migration notes
├── test_structure.py            # Structure verification
└── test_migration.py            # Functionality tests
```

### Key Files & Responsibilities

| File | Responsibility | Key Classes/Functions |
|------|-----------------|----------------------|
| `types.py` | Type definitions, contracts | `Message`, `Tool`, `Provider`, `StreamEvent`, `ToolCallBlock` |
| `main.py` | CLI interface, setup | `main()`, `main_async()` |
| `agent/__init__.py` | Agent loop orchestration | `run_agent()`, `TextEvent`, `ToolStartEvent`, `ToolEndEvent` |
| `providers/anthropic.py` | Anthropic API integration | `AnthropicProvider`, `to_anthropic_messages()` |
| `providers/openai_compat.py` | OpenAI/Groq API integration | `OpenAICompatibleProvider`, `to_openai_messages()` |
| `providers/__init__.py` | Provider factory | `get_provider()`, `PROVIDERS` dict |
| `tools/fsutil.py` | Async filesystem utilities | `walk()`, `glob_to_regex()` |
| `tools/bash.py` | Shell command execution | `BashTool`, `run_bash()`, `find_bash()` |
| `tools/read.py` | File reading | `ReadTool` |
| `tools/ls.py` | Directory listing | `LsTool` |
| `tools/grep.py` | Pattern searching | `GrepTool` |
| `tools/find.py` | File finding | `FindTool` |
| `tools/stat.py` | File metadata | `StatTool` |

### Component Interactions

```
┌──────────────────────┐
│   main.py            │ ← User runs CLI
└──────────┬───────────┘
           │
           ├─ Parse arguments
           ├─ Load .env
           ├─ get_provider("anthropic")
           │   └─ returns AnthropicProvider instance
           │
           ├─ import tools (6 tools)
           │
           └─ run_agent()
              ├─ Loop: provider.stream({messages, model, tools})
              │  ├─ AnthropicProvider
              │  │  ├─ Convert messages via to_anthropic_messages()
              │  │  ├─ Stream from Claude API
              │  │  ├─ Parse text_delta events
              │  │  ├─ Parse tool_use events
              │  │  └─ Yield StreamEvent
              │  │
              │  └─ Detect tool calls in assistant response
              │     ├─ Find tool by name in tools list
              │     └─ tool.execute(arguments)
              │
              └─ Emit events (TextEvent, ToolStartEvent, etc.)
                 └─ main.py displays to user
```

### Data Flow: Prompt to Response

```
User Input: "What's in src/?"
┌─────────────────────────────────────────┐
│ main.py                                   │
│ - Parse args                              │
│ - messages = [UserMessage("What's in?")] │
└──────────────────┬──────────────────────┘
                   │
                   │ Call: run_agent(provider, model, tools, messages, ...)
                   ▼
┌─────────────────────────────────────────────┐
│ agent.run_agent() - Turn 1                   │
│ - Call: provider.stream({messages, ...})    │
└──────────────────┬──────────────────────────┘
                   │
                   ├─ AnthropicProvider.stream()
                   │  ├─ POST to Claude API with messages
                   │  ├─ Stream response
                   │  └─ Yield StreamEvent("text_delta", "Let me")
                   │  └─ Yield StreamEvent("text_delta", " check...")
                   │  └─ Yield StreamEvent("done", AssistantMessage)
                   │
                   └─ Detect: assistant["content"][0] is ToolCallBlock
                      - toolCall(id="123", name="ls", args={"path": "src"})
                      - stopReason = "toolUse" → continue loop
┌─────────────────────────────────────────────┐
│ Execute Tool                                 │
│ - tool = find tool by name "ls"              │
│ - result = await tool.execute({"path": "src"})
│   - LsTool walks src/ via walk() async gen   │
│   - Returns "src/main.py\nsrc/types.py\n..." │
└──────────────────┬──────────────────────────┘
                   │
                   └─ Add to messages:
                      ToolResultMessage(
                        role="toolResult",
                        toolCallId="123",
                        content="src/main.py\n..."
                      )
┌─────────────────────────────────────────────┐
│ agent.run_agent() - Turn 2                   │
│ - messages now has user prompt + assistant  │
│   response + tool result                     │
│ - Call: provider.stream({messages, ...})    │
│   (same full conversation sent to Claude)   │
└──────────────────┬──────────────────────────┘
                   │
                   └─ Claude responds:
                      "The src directory contains main.py and types.py"
                      stopReason = "stop" → exit loop

Final: Text streamed to stdout via TextEvent callbacks
```

---

## Code Walkthrough

### 1. Entry Point: main.py

**File:** `stream_mypy/main.py`

```python
def main():
    """Main entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
```

**What it does:**
- Wraps `main_async()` in `asyncio.run()` to start the async event loop
- Handles Ctrl+C gracefully
- Exits on error

**Why this pattern?**
- stream-mypy is async-first (streaming, tool execution)
- `asyncio.run()` is the Python standard way to enter async context from sync code

```python
async def main_async():
    """Main async function"""
    parser = argparse.ArgumentParser(description="Stream MyPI agent")
    parser.add_argument("-p", "--prompt", type=str, required=True)
    parser.add_argument("--provider", type=str, default="anthropic")
    parser.add_argument("--model", type=str)
    
    args = parser.parse_args()
```

**What it does:**
- Creates argument parser (standard Python)
- `-p/--prompt`: User's question (required)
- `--provider`: Which LLM to use (default: anthropic)
- `--model`: Specific model (optional, uses provider default)

```python
    # Load .env from the same directory as this file
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path, verbose=False)
```

**What it does:**
- Constructs path to `.env` file (up 3 levels from main.py)
- Loads environment variables (API keys, etc.)
- This happens BEFORE parsing args, so env vars are available to providers

```python
    provider = get_provider(args.provider)
    model = args.model or provider.default_model
```

**What it does:**
- Calls provider factory to get the right provider instance (Anthropic, Groq, etc.)
- If user didn't specify model, use provider's default

```python
    messages: List[Message] = [
        {"role": "user", "content": args.prompt}
    ]
    
    def on_event(event):
        if isinstance(event, TextEvent):
            sys.stdout.write(event.delta)
            sys.stdout.flush()
        elif isinstance(event, ToolStartEvent):
            print(f"\n {event.call['name']}")
        elif isinstance(event, ToolEndEvent):
            if event.is_error:
                print(f"\n {event.result}")
            else:
                lines = event.result.split("\n")
                print(f"\n {len(lines)}")
        elif isinstance(event, TurnEndEvent):
            msg = event.message
            usage = msg["usage"]
            stop_reason = msg["stopReason"]
            print(f"\n\n  {provider.name} ... {model} ... {usage['input']} ... {usage['output']} ... {stop_reason}")
```

**What it does:**
- Creates initial message list with user's prompt
- Defines event callback that displays to user:
  - `TextEvent`: Write text chunks to stdout (streaming)
  - `ToolStartEvent`: Print tool name starting
  - `ToolEndEvent`: Print number of output lines (or error)
  - `TurnEndEvent`: Print stats (provider, model, token usage, stop reason)

**Why this design?**
- Decouples event emission (agent) from display (main)
- Agent doesn't know HOW events are displayed
- Easy to swap displays (stdout, file, web, etc.)

```python
    await run_agent(
        provider=provider,
        model=model,
        tools=tools,
        messages=messages,
        on_event=on_event,
    )
```

**What it does:**
- Calls agent loop with provider, model, tools, conversation state, and callback
- `run_agent` is where the autonomous agent executes

### 2. Type System: types.py

**File:** `stream_mypy/types.py`

```python
class Usage(TypedDict):
    input: int
    output: int

StopReason = Literal["stop", "length", "toolUse"]
```

**Why TypedDict?**
- Runtime-checkable type hints
- Can validate at runtime: `if isinstance(msg, dict) and "usage" in msg`
- Tells type checkers: "This dict always has these keys with these types"

```python
class TextBlock(TypedDict):
    type: Literal["text"]
    text: str

class ToolCallBlock(TypedDict):
    type: Literal["toolCall"]
    id: str
    name: str
    arguments: Dict[str, Any]

ContentBlock = Union[TextBlock, ToolCallBlock]
```

**What it represents:**
- Any piece of content from the assistant is either text or a tool call
- `Literal["text"]` ensures type checkers understand `type` must be exactly "text"
- `Union` means "one of these types"

```python
class UserMessage(TypedDict):
    role: Literal["user"]
    content: str

class AssistantMessage(TypedDict):
    role: Literal["assistant"]
    content: List[ContentBlock]
    usage: Usage
    stopReason: StopReason

Message = Union[UserMessage, AssistantMessage, ToolResultMessage]
```

**Why this structure?**
- Conversation is a list of messages
- Each message has a role (who said it) and content
- User messages are simple: just text
- Assistant messages are complex: text + tool calls + stats
- This structure maps to every LLM API (OpenAI, Anthropic, etc.)

```python
class Tool:
    """Base Tool interface"""
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    async def execute(self, args: Dict[str, Any]) -> str:
        raise NotImplementedError
```

**Design Pattern:** Abstract base class
- All tools inherit from this and implement `execute()`
- `name` and `description` are sent to LLM so it knows what tools exist
- `parameters` is a JSON schema (what arguments the tool accepts)

```python
class Provider:
    """Base Provider interface"""
    def __init__(self, name: str, default_model: str):
        self.name = name
        self.default_model = default_model
    
    async def stream(self, opts: StreamOptions):
        raise NotImplementedError
```

**Design Pattern:** Abstract provider
- All providers (Anthropic, OpenAI) inherit from this
- `stream()` is an async generator that yields `StreamEvent` objects
- This is the protocol that agent expects

### 3. Agent Loop: agent/__init__.py

**File:** `stream_mypy/agent/__init__.py`

```python
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
```

**Parameters:**
- `provider`: Instantiated provider (Anthropic, OpenAI, etc.)
- `model`: Model name ("claude-sonnet-4-20250514", "gpt-4", etc.)
- `tools`: List of available tools
- `messages`: Mutable conversation history
- `on_event`: Callback for events (streamed to user)
- `system`: Optional system prompt
- `max_turns`: Prevent infinite loops

```python
    def push(message: Message):
        messages.append(message)
        on_event(MessageEvent(message))
```

**What it does:**
- Helper function to add a message to conversation state
- Also emits event so UI knows a message was added

```python
    for turn in range(1, max_turns + 1):
        # Get response from provider
        assistant: Optional[AssistantMessage] = None
        
        async for event in provider.stream({...}):
            if event.get("type") == "text_delta":
                on_event(TextEvent(event.get("delta", "")))
            elif event.get("type") == "done":
                assistant = event.get("message")
```

**What it does (Observe):**
- Call provider to stream response (or responses in multi-turn)
- Provider yields `StreamEvent` objects as it receives chunks
- Two types of events:
  - `text_delta`: A chunk of text (stream to user immediately)
  - `done`: Full response is ready (contains tool calls, tokens, etc.)
- Accumulate final response in `assistant` variable

**Key insight:** Events flow through while streaming. User sees text in real-time.

```python
        if not assistant:
            raise RuntimeError("Assistant message is empty")
        
        push(assistant)
        on_event(TurnEndEvent(assistant))
        
        # Check if we should continue
        if assistant["stopReason"] != "toolUse":
            return
```

**What it does (Decide):**
- Verify response was complete
- Add assistant's response to message history
- Emit event (so UI knows turn is done)
- **Key decision:** `stopReason` tells us why the LLM stopped
  - `"stop"`: Normal completion, no tools needed → exit
  - `"length"`: Hit token limit → exit (error condition)
  - `"toolUse"`: LLM wants to use tools → continue loop

```python
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
```

**What it does (Act):**
1. Find all tool calls in assistant's response
2. For each tool call:
   - Emit `ToolStartEvent` (for UI feedback)
   - Find the tool in the available tools list
   - Call `tool.execute(arguments)` asynchronously
   - Emit `ToolEndEvent` with result
   - Add tool result to message history
3. Loop continues with new context (conversation + tool results)

**Error handling:** If tool not found or execution fails, result is error message sent back to LLM. This continues the conversation.

```python
    raise RuntimeError(f"Agent stopped after {max_turns} turns")
```

**What it does:**
- If loop completes without returning, it means max_turns was reached
- This is an error condition (should have exited earlier)

### 4. Anthropic Provider: providers/anthropic.py

**File:** `stream_mypy/providers/anthropic.py`

**Design Goal:** Translate our unified message format ↔ Anthropic's format, stream responses.

```python
def to_anthropic_messages(messages: List[Message]) -> List[Dict[str, Any]]:
    """Convert our message format to Anthropic's format"""
    result = []
    
    for msg in messages:
        if msg["role"] == "user":
            result.append({
                "role": "user",
                "content": msg["content"],
            })
```

**Pattern matching:** Check message type and convert

```python
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
                        "type": "tool_use",  # Anthropic calls it "tool_use"
                        "id": block["id"],
                        "name": block["name"],
                        "input": block["arguments"],  # Anthropic calls it "input"
                    })
            result.append({
                "role": "assistant",
                "content": content,
            })
```

**Key difference:** Anthropic calls tool calls `"tool_use"` and arguments `"input"`.

```python
        elif msg["role"] == "toolResult":
            # Tool results go in a user message for Anthropic
            result.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg["toolCallId"],  # Match the call ID
                        "content": msg["content"],
                        "is_error": msg["isError"],
                    }
                ],
            })
```

**Anthropic quirk:** Tool results are user messages with `tool_result` blocks. This is why the API design is flexible.

```python
class AnthropicProvider(Provider):
    """Provider for Anthropic's Claude model"""
    
    def __init__(self):
        super().__init__("anthropic", "claude-sonnet-4-20250514")
        self.client = AsyncAnthropic()
```

**Initialization:**
- Calls parent constructor with provider name and default model
- Creates async client (handles thread pool for streaming)

```python
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
```

**Preparation:**
- Convert messages to Anthropic format
- Convert tool specs to Anthropic format (name/description/input_schema)
- Extract system prompt if provided

```python
        async with self.client.messages.stream(
            model=model,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=anthropic_tools if anthropic_tools else None,
        ) as stream:
```

**Streaming setup:**
- Call Anthropic API with streaming
- Context manager ensures cleanup
- `max_tokens=4096`: Limit response length
- Pass tools so Claude knows what it can call

```python
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
```

**Event: Content block starts**
- Anthropic informs us a text block or tool_use block is starting
- Initialize structures to accumulate it
- For text: empty string (will be filled with deltas)
- For tool: empty dict (will be filled with JSON)

```python
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
```

**Event: Content block delta**
- Text streaming: Add chunk to current text block, yield immediately to stream to user
- Tool input streaming: Accumulate JSON (arguments come as JSON fragments)

```python
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
```

**Event: Content block stops**
- Tool input complete: Parse accumulated JSON into Python dict
- Clear state for next block

```python
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
```

**Final event:**
- After stream ends, get final message (contains tokens, stop reason)
- Convert stop reason to our format
- Yield `done` event with complete AssistantMessage
- This is when agent loop updates `assistant` variable

### 5. Tools: bash.py Example

**File:** `stream_mypy/tools/bash.py`

```python
def find_bash() -> str:
    """Find bash executable, preferring Git Bash on Windows"""
    if platform.system() != "Windows":
        return "bash"
    
    candidates = [
        os.path.expandvars(r"%ProgramFiles%\Git\bin\bash.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Git\bin\bash.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin\bash.exe"),
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
```

**Cross-platform handling:**
- On Unix: Just use "bash" from PATH
- On Windows: Multiple Git Bash locations, prefer explicit paths
- Why? Windows PATH can have WSL bash (different filesystem), Git Bash has proper Windows integration

```python
def truncate_tail(text: str, max_lines: int = MAX_LINES, max_bytes: int = MAX_BYTES) -> str:
    """Keep the end of output and indicate what was truncated"""
    lines = text.split("\n")
    kept = lines[-max_lines:] if len(lines) > max_lines else lines
    
    kept_text = "\n".join(kept)
    while len(kept) > 1 and len(kept_text.encode()) > max_bytes:
        kept = kept[1:]
        kept_text = "\n".join(kept)
    
    result = kept_text
    if len(result.encode()) > max_bytes:
        result = result.encode()[-max_bytes:].decode(errors="ignore")
    
    if len(kept) == len(lines) and len(result) == len(text):
        return text
    
    return f"[truncated: showing the last {len(kept)} of {len(lines)} lines]\n{result}"
```

**Truncation strategy:**
- Keep last N lines (errors usually at end)
- Truncate by bytes (avoid huge responses to LLM)
- Indicate truncation to user/LLM with message

```python
async def run_bash(command: str, timeout_ms: int) -> str:
    """Run a bash command and return output"""
    try:
        bash_exe = find_bash()
        result = subprocess.run(
            [bash_exe, "-c", command],
            capture_output=True,
            text=True,
            timeout=timeout_ms / 1000,
            cwd=os.getcwd(),
        )
        out = result.stdout + result.stderr
        return f"{out}\n[exit code: {result.returncode}]"
    except subprocess.TimeoutExpired:
        return f"\n[timed out after {timeout_ms / 1000}s]"
    except Exception as e:
        return f"failed to start bash: {str(e)}"
```

**Execution:**
- Use `subprocess.run()` with timeout
- Combine stdout + stderr (both go back to LLM)
- Return exit code (LLM can see if command succeeded)
- Catch timeout and other errors, return as string

**Design choice:** Return errors as strings, not raise exceptions
- Agent catches exception higher up
- Entire error message is sent back to LLM
- LLM can reason about what went wrong

```python
class BashTool(Tool):
    """Tool for running bash commands"""
    
    def __init__(self):
        super().__init__(
            name="bash",
            description="Run a bash command in the current folder. Returns stdout, stderr and the exit code.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to run",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds (default 30)",
                    },
                },
                "required": ["command"],
            },
        )
    
    async def execute(self, args: Dict[str, Any]) -> str:
        timeout_seconds = args.get("timeout", 30)
        if isinstance(timeout_seconds, (int, float)):
            timeout_ms = int(timeout_seconds * 1000)
        else:
            timeout_ms = 30000
        
        output = await run_bash(str(args["command"]), timeout_ms)
        return truncate_tail(output)
```

**Tool contract:**
- `parameters` is JSON schema that describes what arguments the LLM should provide
- `execute()` receives parsed arguments as dict
- Returns string (result sent back to LLM)

### 6. Filesystem Walking: tools/fsutil.py

**File:** `stream_mypy/tools/fsutil.py`

```python
async def walk(
    root: str,
    max_depth: Optional[int] = None,
    include_hidden: bool = False,
    ignores: Optional[set] = None,
) -> AsyncGenerator[WalkEntry, None]:
    """Recursively walk directory tree, yielding files and directories (depth-first)"""
    if ignores is None:
        ignores = DEFAULT_IGNORES
    
    if max_depth is None:
        max_depth = float("inf")
    
    async def recurse(dir_path: str, depth: int):
        try:
            entries = os.listdir(dir_path)
        except OSError:
            return
        
        entries.sort()
        
        for entry_name in entries:
            abs_path = os.path.join(dir_path, entry_name)
            rel_path = os.path.relpath(abs_path, root).replace("\\", "/")
            is_directory = os.path.isdir(abs_path)
            
            # Skip hidden files unless requested
            if entry_name.startswith(".") and not include_hidden:
                if should_ignore(entry_name, ignores):
                    continue
                if entry_name not in ignores:
                    continue
            
            if should_ignore(entry_name, ignores):
                continue
            
            yield WalkEntry(abs_path, rel_path, is_directory)
            
            if is_directory and depth < max_depth:
                async for entry in recurse(abs_path, depth + 1):
                    yield entry
    
    async for entry in recurse(root, 1):
        yield entry
```

**Key patterns:**

1. **Async generator:** Returns `AsyncGenerator[WalkEntry, None]`
   - `yield` suspends the function
   - Can be resumed with `async for`
   - Allows lazy evaluation (don't load everything into memory)

2. **Nested async generator:** `recurse()` is defined inside
   - Has access to `ignores`, `max_depth` from outer scope
   - Simplifies parameter passing

3. **Cross-platform paths:** `.replace("\\", "/")`
   - Relative paths use `/` for consistency
   - Works on Windows, Linux, macOS

4. **Depth-first traversal:** Yield entry, then recurse into subdirectory
   - Contrast: breadth-first queues all items first

5. **Error handling:** `try/except OSError` for permission denied
   - Doesn't crash, just skips inaccessible directories

```python
def glob_to_regex(pattern: str) -> re.Pattern:
    """Convert glob pattern (supports *, ?, **) to regex that matches relative paths"""
    normalized = pattern.replace("\\", "/")
    out = ""
    i = 0
    while i < len(normalized):
        c = normalized[i]
        if c == "*":
            if i + 1 < len(normalized) and normalized[i + 1] == "*":
                # "**" matches across path segments (including none)
                i += 1
                if i + 1 < len(normalized) and normalized[i + 1] == "/":
                    i += 1
                out += "(?:.*/)?"
            else:
                out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        elif c in ".+^${}()|[]\\":
            out += "\\" + c
        else:
            out += c
        i += 1
    
    return re.compile(f"^{out}$")
```

**Glob → Regex translation:**
- `*` → `[^/]*` (any chars except /, one segment)
- `**` → `(?:.*/)?` (any chars including /, multiple segments)
- `?` → `[^/]` (any single char except /)
- Special chars → escaped for regex

**Example:**
- Input: `**/*.py`
- Output: regex `^(?:.*/)?[^/]*\.py$`
- Matches: `main.py`, `src/main.py`, `src/dir/main.py`, etc.

---

## Python Concepts

### Async/Await & Async Generators

**Concept:** Asynchronous programming allows multiple tasks to interleave without threads.

**Syntax:**
```python
async def some_func():  # Async function
    result = await other_async_func()  # Wait for result
    return result

async def main():
    result = await some_func()
```

**Where used:** Every time stream-mypy calls an API or tool:
- `provider.stream()` is async generator
- `tool.execute()` is async coroutine
- `run_agent()` is async, calls await on both

**Why async?**
- API calls can take seconds
- Without async, program blocks
- With async, can handle multiple streams simultaneously
- Cleaner than threads for I/O-bound tasks

**Stream-mypy example:**
```python
async for event in provider.stream({...}):
    if event.get("type") == "text_delta":
        on_event(TextEvent(event.get("delta", "")))
```

**Async generator specifics:**
- `async def walk(...)` with `yield` creates async generator
- Caller uses `async for entry in walk(...)`
- Each yield suspends; next iteration resumes
- Memory efficient: doesn't load all files at once

### Type Hints & TypedDict

**TypedDict:** Typed dictionary for structured data

```python
class User(TypedDict):
    name: str
    age: int
    email: str
```

**Benefits:**
1. **IDE autocomplete:** Know available keys
2. **Type checking:** Mypy catches {`"age": "thirty"`} (string, not int)
3. **Self-documentation:** Code shows structure
4. **Runtime flexibility:** Still just a dict at runtime

**Literal types:**
```python
StopReason = Literal["stop", "length", "toolUse"]
```

**Benefits:**
- Type checker knows these are only valid values
- `stop_reason = "done"` → type error
- `stop_reason = "stop"` → OK

**Union types:**
```python
ContentBlock = Union[TextBlock, ToolCallBlock]
```

**Benefits:**
- Can be one of multiple types
- Type checker validates type-specific operations

### Protocols & Abstract Base Classes

**Protocol (structural typing):**
```python
class Provider:
    async def stream(self, opts: StreamOptions):
        raise NotImplementedError
```

**Pattern:** Base class defines interface, subclasses implement

**Benefits:**
- `run_agent()` doesn't know specifics of each provider
- Just calls `provider.stream()`
- Any provider implementing this method works
- Similar to interface in Java/TypeScript, but Python uses inheritance

### Callbacks & Higher-Order Functions

**Callback:** Pass function to be called later

```python
def on_event(event):
    if isinstance(event, TextEvent):
        sys.stdout.write(event.delta)

await run_agent(..., on_event=on_event)
```

**Inside run_agent:**
```python
on_event(TextEvent(event.get("delta", "")))
```

**Benefits:**
- Agent doesn't know how events are displayed
- Can swap callbacks for testing, logging, web APIs, etc.
- Inversion of control: agent calls your function

**Type annotation:**
```python
on_event: Callable[[Any], None]
```

Means: takes any argument, returns None

### Context Managers

**Pattern:**
```python
async with self.client.messages.stream(...) as stream:
    async for event in stream:
        # process event
    # Automatically cleanup when exiting block
```

**Benefits:**
- Ensures cleanup (close connections, release resources)
- Even if exception raised
- `__aenter__` and `__aexit__` are called automatically

---

## Streaming Deep Dive

### What is Streamed?

**Raw data from LLM API:**

Anthropic streaming example:
```json
{"type":"content_block_start","content_block":{"type":"text"}}
{"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}
{"type":"content_block_delta","delta":{"type":"text_delta","text":" "}}
{"type":"content_block_delta","delta":{"type":"text_delta","text":"world"}}
{"type":"content_block_stop"}
{"type":"message_stop"}
```

### Streaming Pipeline

```
Anthropic API (binary stream)
  │
  ├─ AsyncAnthropic receives raw bytes
  │
  ├─ Parses JSON events
  │
  └─ Yields Python objects
       │
       └─ AnthropicProvider.stream()
          │
          ├─ For each "text_delta" event:
          │  │
          │  └─ yield StreamEvent("text_delta", delta=chunk)
          │
          ├─ For each "tool_use" event:
          │  │
          │  └─ Accumulate JSON arguments
          │
          └─ On "message_stop":
             │
             └─ yield StreamEvent("done", message=complete_response)
                  │
                  └─ Agent receives, updates assistant variable
                       │
                       └─ Main receives, displays via callback
```

### Streaming Text

**Situation:** LLM says "Let me check the files in this directory"

**Flow:**
1. Provider yields `StreamEvent("text_delta", delta="Let")`
2. Main calls `on_event()` → prints "Let"
3. Provider yields `StreamEvent("text_delta", delta=" ")`
4. Main calls `on_event()` → prints " " (no line break, text appears per-chunk)
5. Provider yields `StreamEvent("text_delta", delta="me")`
6. Main calls `on_event()` → prints "me"

**Result:** Text appears word-by-word in real-time

**Why not just buffer and send all at once?**
- User sees text appearing (feels faster)
- Can cancel long responses
- Streaming is how modern APIs work (efficiency, reduce latency)

### Streaming Tool Calls

**Situation:** LLM says use bash tool with command "ls src"

**What Anthropic sends (simplified):**
```json
{"type":"content_block_start","content_block":{"type":"tool_use","id":"123","name":"bash"}}
{"type":"content_block_delta","delta":{"type":"input_json_delta","partial_json":"{\"comm"}}
{"type":"content_block_delta","delta":{"type":"input_json_delta","partial_json":"and\": \"ls"}}
{"type":"content_block_delta","delta":{"type":"input_json_delta","partial_json":" src\"}"}}
{"type":"content_block_stop"}
```

**Provider behavior:**
1. On `content_block_start`: Initialize tool call with empty arguments
2. On `input_json_delta`: Append to JSON buffer
3. On `content_block_stop`: Parse complete JSON → populate arguments

**Code in anthropic.py:**
```python
elif event_type == "content_block_delta":
    delta = event.delta
    if hasattr(delta, "partial_json"):
        # Tool input streaming: Accumulate JSON
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
```

### State Management During Streaming

**Variables in provider.stream():**

```python
content: List[ContentBlock] = []  # All text + tool blocks
current_tool_id = None             # Which tool are we parsing
current_tool_name = None
current_tool_input_json = ""       # Accumulating JSON
```

**Invariant:** At any point, `content[-1]` is either:
- A text block (being appended with text_delta)
- A tool call block (being filled with input_json_delta)

**State transitions:**

```
Start
  │
  ├─ content_block_start(text) →
  │  └─ Append {"type": "text", "text": ""}
  │
  ├─ content_block_delta(text) →
  │  └─ Modify content[-1]["text"] += chunk
  │
  ├─ content_block_start(tool) →
  │  └─ Append {"type": "toolCall", "arguments": {}}
  │     Set current_tool_id, current_tool_input_json = ""
  │
  ├─ content_block_delta(json) →
  │  └─ current_tool_input_json += chunk
  │
  ├─ content_block_stop →
  │  └─ Parse current_tool_input_json into dict
  │     content[-1]["arguments"] = parsed_dict
  │
  └─ message_stop →
     └─ Stream ends
```

### Error Scenarios

**Scenario 1: JSON parse error in tool arguments**

```python
try:
    block["arguments"] = json.loads(current_tool_input_json)
except json.JSONDecodeError:
    block["arguments"] = {}
```

**Behavior:** Silently use empty dict. Agent will later catch missing required arguments.

**Scenario 2: Incomplete stream**

```python
if not assistant:
    raise RuntimeError("Assistant message is empty")
```

**Behavior:** Detect in agent, raise error, propagate to main, exit.

**Scenario 3: Tool doesn't exist**

```python
tool = next((t for t in tools if t.name == call["name"]), None)
if not tool:
    raise RuntimeError(f"Unknown tool: {call['name']}")
```

**Behavior:** Caught in try/except, error message sent back to LLM. If LLM is smart, it learns and corrects.

### Memory & Performance

**Streaming benefits:**
- Text appears immediately (perceived latency lower)
- No need to buffer entire response in memory upfront
- Events processed as they arrive

**Memory usage:**
- `content: List[ContentBlock]` grows as response builds
- With `max_tokens=4096`, response is bounded
- No memory leaks (stream ends, objects freed)

**Latency:**
- First text chunk can arrive in 100-500ms
- User sees progress immediately
- vs. buffering everything (5+ seconds typically)

---

## Type System

### How Types Help

**1. IDE autocompletion:**

```python
msg: AssistantMessage

msg.  # IDE knows keys: role, content, usage, stopReason
msg["usage"].  # IDE knows: input, output
```

**2. Type checking (mypy):**

```python
def bad_function(msg: UserMessage) -> str:
    return msg["content"]  # OK, UserMessage has content

msg: Message = {...}
return msg["content"]  # Error: Message type has no guaranteed content
```

**3. Documentation:**

```python
async def stream(self, opts: StreamOptions) -> AsyncGenerator[StreamEvent, None]:
```

Tells reader: "Takes these options, yields these events, returns nothing"

### Key Type Definitions

**Message hierarchy:**

```python
Message = Union[UserMessage, AssistantMessage, ToolResultMessage]

# When you write:
msg: Message

# Type checker knows:
# - It has a "role" field (all have it)
# - To use type-specific fields, must check role first

if msg["role"] == "user":
    # Type narrowing: here msg is UserMessage
    text = msg["content"]  # Type checker knows content is str
elif msg["role"] == "assistant":
    # Type narrowing: here msg is AssistantMessage
    blocks = msg["content"]  # Type checker knows it's List[ContentBlock]
```

**ContentBlock hierarchy:**

```python
ContentBlock = Union[TextBlock, ToolCallBlock]

block: ContentBlock

if block["type"] == "text":
    # Type narrowed to TextBlock
    text_value = block["text"]  # str
else:
    # Type narrowed to ToolCallBlock
    call_id = block["id"]  # str
```

**Generic types:**

```python
async def stream(self, opts: StreamOptions) -> AsyncGenerator[StreamEvent, None]:
    # AsyncGenerator[Yield, Send]
    #   Yield: type of values from yield
    #   Send: type of arguments to send()
    # Most generators don't use send, so None
```

### Type-Driven Design

**Provider protocol:**

```python
class Provider:
    async def stream(self, opts: StreamOptions):
        raise NotImplementedError
```

**Type contract:** Any provider must return `AsyncGenerator[StreamEvent, None]`

**Consequence:** Agent can call any `provider.stream()` without knowing specifics

**Tool protocol:**

```python
class Tool:
    async def execute(self, args: Dict[str, Any]) -> str:
        raise NotImplementedError
```

**Type contract:** Any tool receives dict of arguments, returns string

**Consequence:** Agent can call any `tool.execute()` without knowing specifics

### What Type Hints Don't Catch

**Runtime type safety:**

```python
result = json.loads(current_tool_input_json)
# Type: Dict[str, Any]
# But could be invalid JSON
```

**Mitigated by:** try/except around json.loads()

**Dict key access:**

```python
model = args.get("model")
# Type: Any (could be None, wrong type, etc.)

# Better:
model = str(args.get("model", "default-model"))
```

**Mitigated by:** Defensive programming, type guards

---

## Design & Engineering

### Architectural Principles

#### 1. Adapter Pattern: Multiple Providers

**Problem:** Different LLM APIs have different formats

**Solution:** Each provider implements the same interface (`stream()` method)

```python
class AnthropicProvider(Provider):
    async def stream(self, opts: StreamOptions) -> AsyncGenerator[StreamEvent, None]:
        # Convert to Anthropic format, call API, convert back

class OpenAICompatibleProvider(Provider):
    async def stream(self, opts: StreamOptions) -> AsyncGenerator[StreamEvent, None]:
        # Convert to OpenAI format, call API, convert back
```

**Benefit:** \`agent.run_agent()\` works with any provider without knowing specifics

#### 2. Factory Pattern: Provider Instantiation

```python
PROVIDERS = {
    "anthropic": create_anthropic,
    "anthropic-openai": lambda: create_openai_compat(...),
    "groq": lambda: create_openai_compat(...),
}

def get_provider(name: str) -> Provider:
    create_func = PROVIDERS.get(name)
    if not create_func:
        raise RuntimeError(f"Unknown provider: {name}")
    return create_func()
```

**Benefit:** Easy to add new providers without modifying agent logic

#### 3. Template Method Pattern: Agent Loop

```python
for turn in range(1, max_turns + 1):
    # Step 1: Get response (provider-specific)
    assistant = await provider.stream(...)
    
    # Step 2: Check decision (common logic)
    if assistant["stopReason"] != "toolUse":
        return
    
    # Step 3: Execute tools (tool-specific)
    for call in assistant["content"]:
        result = await tool.execute(call["arguments"])
    
    # Step 4: Continue (common logic)
    # Loop back to step 1
```

**Invariant:** Same loop structure regardless of provider or tools

#### 4. Event-Driven Architecture

**Pattern:** Agent doesn't know who consumes events

```python
on_event(TextEvent(...))
on_event(ToolStartEvent(...))
on_event(TurnEndEvent(...))
```

**Benefit:** Can swap event consumers (stdout, logging, web servers, etc.)

**Hierarchy:**
- Agent emits events
- Main (or any client) passes callback
- Decoupled: agent ≠ display

### Error Handling Strategy

**Errors at different levels:**

| Level | Error | Handling |
|-------|-------|----------|
| CLI args | Invalid args | Argparse raises, main catches, exits |
| Env vars | Missing API key | Provider initialization fails, main catches, exits |
| API call | Network error | Provider propagates, agent propagates, main catches, exits |
| Tool execution | Tool not found | Try/except, error string returned to LLM, continue |
| Tool execution | Timeout | Caught by subprocess, error string returned to LLM, continue |
| Agent loop | Max turns | Raise after loop, main catches, exits |

**Philosophy:**
- Errors that prevent continuation → raise and exit
- Errors LLM can handle → return as string, let LLM reason

**Example:**

```python
try:
    result = await tool.execute(call["arguments"])
except Exception as e:
    result = f"Error: {str(e)}"  # Return error to LLM
    is_error = True
    
push({
    "role": "toolResult",
    "toolCallId": call["id"],
    "toolName": call["name"],
    "content": result,
    "isError": is_error,  # Flag error
})
```

LLM receives: "Error: /tmp doesn't exist" and can reason about it.

### Design Decisions & Trade-offs

#### Decision 1: Streaming Text vs. Buffering

**Choice:** Stream text immediately (yield text_delta events)

**Alternative:** Buffer until final message, then return all text

**Trade-off:**
- **Streaming:** User sees progress, higher complexity
- **Buffering:** Simpler, but user waits for full response

**Why streaming?** Modern UX expectation, better perceived latency

#### Decision 2: Tool Result as String

**Choice:** All tool results are strings

**Alternative:** Structured objects, preserve types

**Trade-off:**
- **String:** Simple, LLM-friendly (LLM works with text), loses some structure
- **Structured:** Richer info, more complex

**Why string?** LLM only understands text input. Easier for user to see what tool returns.

#### Decision 3: Message History Mutable

**Choice:** messages list is passed in, modified in-place

**Alternative:** Immutable, return new list each turn

**Trade-off:**
- **Mutable:** Efficient, caller tracks state
- **Immutable:** Functional programming style, easier to reason about

**Why mutable?** Agent needs to maintain conversation state across turns

#### Decision 4: Async Throughout

**Choice:** Everything is async (providers, tools, agent, main)

**Alternative:** Sync with thread pool for I/O

**Trade-off:**
- **Async:** Cleaner code, but requires `async/await` everywhere
- **Sync:** Traditional, but requires threading/threading pools

**Why async?** Better for I/O-bound tasks (API calls, file I/O), cleaner error handling than threads

### Extensibility

**To add a new provider:**
1. Subclass Provider
2. Implement `stream()` method
3. Add to PROVIDERS dict in `providers/__init__.py`
4. No changes needed to agent or tools

**To add a new tool:**
1. Subclass Tool
2. Implement `execute()` method
3. Add instance to tools list in `tools/__init__.py`
4. Agent automatically picks it up

**To change event display:**
1. Define new `on_event()` callback
2. Pass to `run_agent()`
3. Callback receives event objects
4. Choose how to display

---

## Tests, Errors & Debugging

### Testing Strategy

**File:** `test_structure.py` (validation test)
```python
def check_syntax(filepath):
    """Check if a Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)
```

**Purpose:** Verify all files are syntactically valid Python

**Run:** `python test_structure.py`

**File:** `test_migration.py` (functional test)
```python
print("Testing imports...")
try:
    from stream_mypy.types import Message, Tool, Provider
    print("✓ Types imported successfully")
except Exception as e:
    print(f"✗ Failed to import types: {e}")
```

**Purpose:** Verify imports work, tools exist, basic functionality

**Run:** `python test_migration.py` (requires dependencies)

### Common Errors & Debugging

#### Error: "No module named 'anthropic'"

**Cause:** Dependencies not installed

**Debug:**
```bash
pip install -r requirements.txt
```

#### Error: "ANTHROPIC_API_KEY not set"

**Cause:** .env file missing or API key not set

**Debug:**
```bash
cat .env  # Check what's there
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

#### Error: Agent stops after max_turns

**Cause:** LLM keeps requesting same tool or tool always says it needs tool

**Debug:**
- Check tool output: Is LLM getting useful results?
- Check LLM prompt: Is system prompt clear?
- Increase max_turns temporarily to see if agent completes

#### Error: Tool not found

**Cause:** LLM requested tool name not in tools list

**Debug:**
```python
# In main.py, add debug:
print(f"Available tools: {[t.name for t in tools]}")

# LLM tries to call tool not in list
```

**Fix:**
- Check tool implements Tool interface
- Check tool is added to tools list in `tools/__init__.py`

#### Error: Tool returns incomplete results

**Cause:** Output truncated by truncate_tail()

**Debug:**
```python
# In bash.py:
result = await run_bash(command, timeout_ms)
return truncate_tail(result)

# truncate_tail keeps last 2000 lines or 50KB
# If LLM needs full output, it's lost
```

**Fix:**
- Adjust MAX_BYTES/MAX_LINES constants
- Or have tool filter output server before truncate

### Debugging Streaming

**Problem:** Text appearing in chunks, hard to trace

**Debug strategy:**
```python
class DebugEvent:
    def __init__(self, event):
        self.event = event
        print(f"[EVENT] {event.get('type')}: {event.get('delta', '')[:20]}")

# In main.py:
on_event = lambda e: DebugEvent(e) if isinstance(e, dict) else on_event(e)
```

**Alternative:** Add logging to provider
```python
# In anthropic.py stream() method:
async for event in stream:
    print(f"[Anthropic] {event.type}")
    if event_type == "content_block_delta":
        print(f"  Delta: {delta}")
```

### Debugging Agent Loop

**Add debug prints:**
```python
# In run_agent():
for turn in range(1, max_turns + 1):
    print(f"[Agent] Turn {turn}")
    print(f"[Agent] Messages: {len(messages)}")
    
    async for event in provider.stream(...):
        pass
    
    if not assistant:
        raise RuntimeError("Assistant message is empty")
    
    print(f"[Agent] Stop reason: {assistant['stopReason']}")
    
    if assistant["stopReason"] != "toolUse":
        print(f"[Agent] Agent decides to exit (stop reason: {assistant['stopReason']})")
        return
```

### Memory Debugging

**Check for leaks:**
```python
import tracemalloc
tracemalloc.start()

# Run agent
...

current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.2f}MB")
print(f"Peak: {peak / 1024 / 1024:.2f}MB")
```

**Typical usage:** Few MB (messages, tools) to ~100MB (if max_tokens is high)

---

## How to Extend It

### Adding a New Tool

**Step 1: Create the tool file**

Example: `tools/count_lines.py`

```python
"""Count lines in a file"""
from typing import Dict, Any
from stream_mypy.types import Tool


class CountLinesTool(Tool):
    """Tool for counting lines in a file"""
    
    def __init__(self):
        super().__init__(
            name="count_lines",
            description="Count the number of lines in a file",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file, relative to current folder",
                    },
                },
                "required": ["path"],
            },
        )
    
    async def execute(self, args: Dict[str, Any]) -> str:
        import os
        file_path = os.path.join(os.getcwd(), str(args["path"]))
        with open(file_path, "r", encoding="utf-8") as f:
            lines = len(f.readlines())
        return f"File has {lines} lines"


count_lines_tool = CountLinesTool()
```

**Step 2: Export from tools/__init__.py**

```python
from stream_mypy.tools.count_lines import count_lines_tool

tools = [bash_tool, read_tool, ls_tool, grep_tool, stat_tool, find_tool, count_lines_tool]
```

**Step 3: Test**

```bash
python -m stream_mypy.main -p "How many lines in pyproject.toml?" --provider anthropic
```

LLM will detect count_lines tool exists and can use it.

### Adding a New Provider

**Step 1: Create provider file**

Example: `providers/llama.py`

```python
"""Llama provider via Ollama"""
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx  # or whatever HTTP library
from stream_mypy.types import Provider, StreamOptions, StreamEvent, Message


def to_llama_messages(messages: List[Message]) -> List[Dict[str, Any]]:
    """Convert to Llama format"""
    # Similar to to_anthropic_messages()
    pass


class LlamaProvider(Provider):
    """Provider for Llama models via Ollama"""
    
    def __init__(self):
        super().__init__("llama", "llama2")
        self.base_url = "http://localhost:11434"
    
    async def stream(self, opts: StreamOptions) -> AsyncGenerator[StreamEvent, None]:
        """Stream from Llama"""
        messages = to_llama_messages(opts["messages"])
        model = opts["model"]
        
        # Call Ollama API with streaming
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={"model": model, "messages": messages, "stream": True},
            ) as response:
                async for line in response.aiter_lines():
                    # Parse line, extract text and tool calls
                    # Yield StreamEvent
                    pass

def create_llama() -> Provider:
    return LlamaProvider()
```

**Step 2: Register in providers/__init__.py**

```python
from stream_mypy.providers.llama import create_llama

PROVIDERS = {
    ...existing...,
    "llama": create_llama,
}
```

**Step 3: Test**

```bash
python -m stream_mypy.main -p "Hello" --provider llama
```

### Changing Event Display

**Default:** Print to stderr/stdout

**Alternative: Write to file**

```python
async def main_async():
    ...
    
    # Open log file
    log_file = open("agent.log", "w")
    
    def on_event(event):
        if isinstance(event, TextEvent):
            log_file.write(event.delta)
            log_file.flush()
        elif isinstance(event, ToolStartEvent):
            log_file.write(f"\n[TOOL] {event.call['name']}\n")
        ...
    
    try:
        await run_agent(..., on_event=on_event)
    finally:
        log_file.close()
```

**Alternative: Web dashboard**

```python
# In event callback:
# websocket.send(json.dumps({"type": "text_delta", "delta": event.delta}))
```

### Customizing Tool Behavior

**Make tools stateful:**

```python
class CountingBashTool(BashTool):
    """Bash tool that counts execution"""
    
    def __init__(self):
        super().__init__()
        self.execution_count = 0
    
    async def execute(self, args: Dict[str, Any]) -> str:
        self.execution_count += 1
        result = await super().execute(args)
        return f"[Execution #{self.execution_count}] {result}"
```

**Add validation:**

```python
class SafeBashTool(BashTool):
    """Bash tool that blocks dangerous commands"""
    
    BLOCKED = ["rm", "dd", ">"]  # Dangerous commands
    
    async def execute(self, args: Dict[str, Any]) -> str:
        command = str(args["command"])
        for blocked in self.BLOCKED:
            if blocked in command:
                return f"Command '{command}' is blocked (contains '{blocked}')"
        
        return await super().execute(args)
```

---

## Final Mental Model

### The 10,000-Foot View

**stream-mypy is a bridge.**

```
You ←→ stream-mypy Agent ←→ LLM ←→ Tools
  │         Loop        Provider  (bash, grep, etc.)
  │                        │
  └────────────────────────┘
      Conversation history
```

**What happens:**

1. **You ask:** "What files changed in the last 5 minutes?"
2. **Agent sends to LLM:** Prompt + tools available + conversation history
3. **LLM responds via streaming:** "I'll use bash to check... [tool call]"
4. **Agent sees tool call:** Execute it (e.g., `find . -mmin -5`)
5. **Tool returns results:** File list
6. **Agent adds to conversation:** LLM, here's what bash returned
7. **LLM responds:** Natural language answer + final response
8. **You receive:** Streamed answer, real-time

### Key Architectural Insights

| Component | Responsibility | Why It Matters |
|-----------|-----------------|----------------|
| **Types (types.py)** | Define message format | Contracts between parts |
| **Provider** | Abstract LLM API | Swap GPT ↔ Claude without changing agent |
| **Agent Loop** | Orchestrate turns | Autonomous decision-making (Observe-Decide-Act) |
| **Tools** | Execute actions | Agent's interface to the world |
| **Events** | Report progress | Decouple display from logic |
| **Async/await** | Enable concurrency | Streaming feels responsive |

### Data Flow Summary

```
CLI Argument (-p "prompt")
    ↓
main.py
    ├─ Load env, create provider
    ├─ Initialize tools
    └─ Call run_agent()
        ↓
    run_agent() Loop:
        ├─ Call provider.stream()
        │   ↓
        │   Provider async generator
        │   ├─ Call LLM API (Anthropic/OpenAI/Groq)
        │   ├─ Stream response events
        │   ├─ Convert tool calls to standard format
        │   └─ Yield StreamEvent
        │
        ├─ For each text_delta event:
        │   └─ Emit TextEvent → displayed to user immediately
        │
        ├─ When done event arrives:
        │   ├─ Check stopReason
        │   ├─ If "toolUse":
        │   │   └─ For each tool call:
        │   │       ├─ Find tool by name
        │   │       ├─ Call tool.execute()
        │   │       └─ Add result to message history
        │   │       └─ Loop continues with updated history
        │   └─ If "stop":
        │       └─ Exit loop
        │
        └─ Return from run_agent()
            ↓
    Callback in main.py displays final stats
```

### Most Important Classes/Functions

**To understand stream-mypy, study these (in order):**

1. **`types.py`:** Type definitions (Message, Tool, Provider, StreamEvent)
2. **`run_agent()` in agent/__init__.py:** The core loop (page-by-page walk it)
3. **`AnthropicProvider.stream()` in providers/anthropic.py:** Concrete provider example
4. **`BashTool.execute()` in tools/bash.py:** Concrete tool example
5. **`walk()` in tools/fsutil.py:** Async generator pattern
6. **`main.py`:** How CLI wires everything together

### Execution Checklist

When adding a feature or debugging, ask:

- [ ] How does my feature fit in the message flow?
- [ ] Which provider(s) need changes?
- [ ] Which tool(s) need changes?
- [ ] Do I need new types?
- [ ] How do agents discover my tool/provider?
- [ ] How do events flow for my feature?
- [ ] Does it work with async/await?
- [ ] Did I test with both providers?
- [ ] Can agent still exit gracefully?

### Python Patterns Most Used

1. **Async generators:** `async def func() -> AsyncGenerator`
2. **TypedDict:** Structured typing for dicts
3. **Union types:** Tagged union (discriminated by "type"/"role" field)
4. **Abstract base class:** `class Provider` with abstract methods
5. **Callbacks:** `on_event: Callable[[Any], None]`
6. **Factory pattern:** `get_provider(name: str) -> Provider`
7. **Context managers:** `async with stream as ...`
8. **Type narrowing:** `if msg["role"] == "user": ...`

### AI/Agentic Patterns Most Used

1. **Autonomous agent:** Observe-Decide-Act loop
2. **Tool use / function calling:** LLM requests execution
3. **Message format adaptation:** Translate between APIs
4. **Streaming:** Real-time response, better UX
5. **Turn-based conversation:** Multi-turn with context
6. **Event-driven UI:** Decouple computation from display

### What Should Always Be True

**Invariants:**

1. **Agent exit condition:** Always exit on stopReason != "toolUse" OR max_turns exceeded
2. **Message history:** Every assistant response and tool result is added (messages list grows)
3. **Tool results:** Always returned as strings (even errors)
4. **Events:** Always emitted for text, tool start/end, turn end
5. **Async:** No synchronous API calls (everything awaited)
6. **Provider:** Can be instantiated once, stream multiple times
7. **Tools:** Idempotent (run twice = same result)

### When Something Goes Wrong, Check

| Symptom | Check |
|---------|-------|
| Agent loops infinitely | Does stopReason ever != "toolUse"? Max turns? |
| LLM doesn't see tool | Is tool added to tools list? Name matches? |
| Text not streaming | Is TextEvent emitted? Is on_event callback called? |
| Tool returns wrong result | Check tool.execute() implementation, parameters parsing |
| Provider crashes | Check API key, message format conversion, stream parsing |
| Memory grows unbounded | Are event listeners holding old messages? Check for cycles. |

---

## Conclusion

**stream-mypy is production-ready code** that demonstrates:

- Modern async/await patterns in Python
- Type safety with TypedDict and Literals
- Clean separation of concerns (providers, agents, tools, types)
- Streaming and real-time UX
- Autonomous agent design (Observe-Decide-Act)
- Multi-provider LLM abstraction
- Extensible architecture

**After reading this document, you should be able to:**

- Explain how stream-mypy works end-to-end
- Add a new tool, provider, or event handler
- Debug streaming responses and async issues
- Understand the type system and why it matters
- Reason about agent behavior and edge cases
- Modify existing code confidently
- Write async Python more effectively

**The most important insight:** stream-mypy separates concerns cleanly. The agent loop doesn't care about provider details. Providers don't care about tool details. Tools don't care about display. This separation makes the code elegant, testable, and extensible.

**Start with:** `types.py` (understand contracts), then `run_agent()` (understand orchestration), then any provider/tool (understand implementations).
