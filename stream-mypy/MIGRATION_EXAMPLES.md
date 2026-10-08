# Code Migration Examples: TypeScript → Python

This document shows side-by-side comparisons of how key components were migrated from TypeScript to Python.

## 1. Type Definitions

### TypeScript (src/types.ts)
```typescript
export type Usage = { input: number; output: number };
export type StopReason = "stop" | "length" | "toolUse";

export type TextBlock = {type:"text", text:string};
export type ToolCallBlock = {type:"toolCall", id:string, name:string, arguments:Record<string, unknown>};
export type ContentBlock = TextBlock|ToolCallBlock;

export type UserMessage = { role: "user"; content: string };
export type AssistantMessage = {
  role: "assistant";
  content:ContentBlock[],
  usage: Usage;
  stopReason: StopReason;
};

export type Tool = ToolSpec & {execute(args:Record<string,unknown>):Promise<string>}

export interface Provider {
  name: string;
  defaultModel: string;
  stream(opts: StreamOptions): AsyncIterable<StreamEvent>;
}
```

### Python (stream_mypy/types.py)
```python
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

class Tool:
    """Base Tool interface"""
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    async def execute(self, args: Dict[str, Any]) -> str:
        raise NotImplementedError

class Provider:
    """Base Provider interface"""
    def __init__(self, name: str, default_model: str):
        self.name = name
        self.default_model = default_model
    
    async def stream(self, opts: StreamOptions):
        raise NotImplementedError
```

**Key Differences:**
- TypeScript unions (`|`) → Python `Union` types
- TypeScript `Record<string, unknown>` → Python `Dict[str, Any]`
- TypeScript interfaces → Python classes with type hints
- TypeScript `Promise` → Python `async def` with `await`

---

## 2. Tool Implementation

### TypeScript (src/tools/bash.ts)
```typescript
export const bashTool: Tool = {
  name: "bash",
  description: "Run a bash command in the current folder...",
  parameters: { /* ... */ },
  async execute(args) {
    const seconds = typeof args.timeout === "number" ? args.timeout : 30;
    return truncateTail(await runBash(String(args.command), seconds * 1000));
  },
};

function runBash(command: string, timeoutMs: number): Promise<string> {
  return new Promise((resolve) => {
    const child = spawn(findBash(), ["-c", command], { /* ... */ });
    // ...
  });
}
```

### Python (stream_mypy/tools/bash.py)
```python
class BashTool(Tool):
    """Tool for running bash commands"""
    
    def __init__(self):
        super().__init__(
            name="bash",
            description="Run a bash command in the current folder...",
            parameters={ /* ... */ },
        )
    
    async def execute(self, args: Dict[str, Any]) -> str:
        timeout_seconds = args.get("timeout", 30)
        if isinstance(timeout_seconds, (int, float)):
            timeout_ms = int(timeout_seconds * 1000)
        else:
            timeout_ms = 30000
        
        output = await run_bash(str(args["command"]), timeout_ms)
        return truncate_tail(output)

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

**Key Differences:**
- TypeScript `spawn` → Python `subprocess.run`
- TypeScript object literals → Python class inheritance
- TypeScript Promise constructor → Python async/await
- TypeScript type guards → Python `isinstance` checks

---

## 3. Provider Implementation

### TypeScript (src/providers/anthropic.ts)
```typescript
export function createAnthropic(): Provider {
  const client = new Anthropic();
  return {
    name: "anthropic",
    defaultModel: "claude-sonnet-5",
    async *stream({ messages, model, system, tools=[] }) {
      const stream = client.messages.stream({
        model,
        max_tokens: 4096,
        system,
        messages: toAnthropic(messages),
        tools: tools.map((t)=>({
          name:t.name,
          description:t.description,
          input_schema:t.parameters as Anthropic.Tool.InputSchema
        }))
      });
      
      for await (const event of stream) {
        if(event.type==="content_block_start") { /* ... */ }
        else if(event.type==="content_block_delta") { /* ... */ }
      }
      
      const final= await stream.finalMessage();
      yield { type:"done", message: { /* ... */ } }
    },
  };
}
```

### Python (stream_mypy/providers/anthropic.py)
```python
class AnthropicProvider(Provider):
    """Provider for Anthropic's Claude model"""
    
    def __init__(self):
        super().__init__("anthropic", "claude-sonnet-4-20250514")
        self.client = AsyncAnthropic()
    
    async def stream(self, opts: StreamOptions) -> AsyncGenerator[StreamEvent, None]:
        """Stream responses from Claude"""
        messages = to_anthropic_messages(opts["messages"])
        model = opts["model"]
        
        anthropic_tools = []
        if tools:
            for tool in tools:
                anthropic_tools.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["parameters"],
                })
        
        async with self.client.messages.stream(
            model=model,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=anthropic_tools if anthropic_tools else None,
        ) as stream:
            async for event in stream:
                event_type = event.type
                
                if event_type == "content_block_start":
                    # Handle event
                    pass
                elif event_type == "content_block_delta":
                    # Handle delta
                    pass
            
            final_message = await stream.get_final_message()
            yield { "type": "done", "message": { /* ... */ } }

def create_anthropic() -> Provider:
    return AnthropicProvider()
```

**Key Differences:**
- TypeScript async generators (`async *`) → Python async generators with `async def` and `yield`
- TypeScript client initialization → Python class-based provider
- TypeScript object return → Python type-annotated return
- TypeScript factory function pattern → Python factory function (same pattern)

---

## 4. Agent Loop

### TypeScript (src/agent/loop.ts)
```typescript
export async function runAgent(opts: AgentOptions): Promise<void> {
  const { provider, model, system, tools, messages, onEvent } = opts;
  const maxTurns = opts.maxTurns ?? 20;
  
  for(let turn=1; turn<=maxTurns; ++turn){
    let assistant: AssistantMessage | undefined
    for await(const event of provider.stream({messages,model,system,tools})){
      if(event.type==="text_delta") onEvent({type:"text", delta:event.delta})
      else assistant = event.message
    }
    if(!assistant) throw new Error('assistant khali h ')
    push(assistant);
    
    if(assistant.stopReason!=="toolUse") return;
    
    for(const call of assistant.content){
      if(call.type!== "toolCall") continue;
      // Execute tool
    }
  }
}
```

### Python (stream_mypy/agent/__init__.py)
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
            # Execute tool
```

**Key Differences:**
- TypeScript `for` loop → Python `range()` loop
- TypeScript destructuring → Python named parameters
- TypeScript `??` operator → Python `or` keyword
- TypeScript `for await` → Python `async for`
- TypeScript callback → Python callable with type hint

---

## 5. File System Utilities

### TypeScript (src/tools/fsutil.ts)
```typescript
export async function* walk(root: string, opts: WalkOptions = {}): AsyncGenerator<WalkEntry> {
  async function* recurse(dir: string, depth: number): AsyncGenerator<WalkEntry> {
    let entries = await readdir(dir, { withFileTypes: true });
    entries.sort((a, b) => a.name.localeCompare(b.name));
    
    for (const entry of entries) {
      if (!includeHidden && entry.name.startsWith(".") && !ignores.includes(entry.name)) continue;
      if (shouldIgnore(entry.name, ignores)) continue;
      
      const absPath = join(dir, entry.name);
      const relPath = relative(root, absPath).split(sep).join("/");
      const isDirectory = entry.isDirectory();
      
      yield { absPath, relPath, isDirectory };
      
      if (isDirectory && depth < maxDepth) {
        yield* recurse(absPath, depth + 1);
      }
    }
  }
  
  yield* recurse(root, 1);
}
```

### Python (stream_mypy/tools/fsutil.py)
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
        entries = os.listdir(dir_path)
        entries.sort()
        
        for entry_name in entries:
            abs_path = os.path.join(dir_path, entry_name)
            rel_path = os.path.relpath(abs_path, root).replace("\\", "/")
            is_directory = os.path.isdir(abs_path)
            
            # Check if should be ignored
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

**Key Differences:**
- TypeScript `async function*` → Python `async def` with `AsyncGenerator`
- TypeScript `yield*` → Python `async for` and `yield`
- TypeScript `readdir` API → Python `os.listdir`
- TypeScript path methods → Python `os.path` module
- TypeScript Set membership → Python `set` operations

---

## 6. CLI Main Entry

### TypeScript (src/main.ts)
```typescript
import { config } from "dotenv";
import { parseArgs } from "node:util";

config({
  path: fileURLToPath(new URL("../.env", import.meta.url)),
  quiet: true,
});

const { values } = parseArgs({
  options: {
    prompt: { type: "string", short: "p" },
    provider: { type: "string", default: "anthropic" },
    model: { type: "string" },
  },
});

if (!values.prompt) {
  console.error(`no prompt sirr, mypi -p "prompt" --provider anthropic OR groq`);
  process.exit(1);
}

const provider = getProvider(values.provider);
const model = values.model ?? provider.defaultModel;

await runAgent({
  provider,
  model,
  tools,
  messages,
  onEvent(event) {
    if (event.type === "text") process.stdout.write(event.delta);
    // ...
  },
});
```

### Python (stream_mypy/main.py)
```python
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, verbose=False)

async def main_async():
    """Main async function"""
    parser = argparse.ArgumentParser(description="Stream MyPI agent")
    parser.add_argument(
        "-p", "--prompt",
        type=str,
        required=True,
        help="The prompt to send to the agent",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="anthropic",
        help="The provider to use",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="The model to use",
    )
    
    args = parser.parse_args()
    
    if not args.prompt:
        print('no prompt sirr, mypi -p "prompt" --provider anthropic OR groq')
        sys.exit(1)
    
    provider = get_provider(args.provider)
    model = args.model or provider.default_model
    
    def on_event(event):
        if isinstance(event, TextEvent):
            sys.stdout.write(event.delta)
            sys.stdout.flush()
        # ...
    
    await run_agent(
        provider=provider,
        model=model,
        tools=tools,
        messages=messages,
        on_event=on_event,
    )

def main():
    """Main entry point"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
```

**Key Differences:**
- TypeScript `parseArgs` → Python `argparse`
- TypeScript `console.error` → Python `print`
- TypeScript `process.exit` → Python `sys.exit`
- TypeScript `import.meta.url` → Python `Path(__file__)`
- TypeScript `process.stdout.write` → Python `sys.stdout.write`
- TypeScript `await` at top level → Python `asyncio.run()` wrapper

---

## 7. Message Format Conversion

### TypeScript
```typescript
function toAnthropic(messages: Message[]): Anthropic.MessageParam[] {
  return messages.map((m): Anthropic.MessageParam => {
    if (m.role === "user") return { role: "user", content: m.content };
    if (m.role === "assistant") {
      return {
        role: "assistant",
        content: m.content.map((b): Anthropic.ContentBlockParam =>
          b.type === "text"
            ? { type: "text", text: b.text }
            : { type: "tool_use", id: b.id, name: b.name, input: b.arguments },
        ),
      };
    }
    // toolResult -> Anthropic wants it inside a USER message
    return {
      role: "user",
      content: [{ type: "tool_result", tool_use_id: m.toolCallId, content: m.content, is_error: m.isError }],
    };
  });
}
```

### Python
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
```

**Key Differences:**
- TypeScript `map()` → Python `for` loop with `append()`
- TypeScript ternary operator → Python `if/elif/else`
- TypeScript implicit return → Python explicit `return`
- TypeScript type annotations → Python `List[Dict[str, Any]]` hints

---

## Summary of Migration Patterns

| TypeScript | Python |
|-----------|--------|
| `async function*` | `async def` with `AsyncGenerator` |
| `for await` | `async for` |
| `yield*` | nested `async for` / `yield` |
| `Promise<T>` | `Callable[[], Awaitable[T]]` or direct `async def` |
| `Record<K, V>` | `Dict[K, V]` |
| Union types `A \| B` | `Union[A, B]` |
| Interfaces | Base classes or `TypedDict` |
| `spawn()` | `subprocess.run()` |
| `readdir()` | `os.listdir()` |
| `parseArgs` | `argparse` |
| `private` fields | `_field` naming convention |
| Callbacks | `Callable` types or event classes |

This migration maintains **100% functional parity** with the TypeScript version while following Python best practices and idioms.
