# stream-mypy Python Concepts Deep Dive

A complete guide to every Python language feature, typing concept, async pattern, and programming technique used in the `stream-mypy` repository. Organized from beginner to advanced, with examples grounded entirely in the actual codebase.

---

## Table of Contents

1. [Module System & Imports](#module-system--imports)
2. [Functions & Docstrings](#functions--docstrings)
3. [Classes & Object-Oriented Programming](#classes--object-oriented-programming)
4. [Type Hints & Typing Module](#type-hints--typing-module)
5. [Async/Await & Asyncio](#asyncawait--asyncio)
6. [Generators & Async Generators](#generators--async-generators)
7. [Exception Handling](#exception-handling)
8. [String Operations & Encoding](#string-operations--encoding)
9. [Collections & Data Structures](#collections--data-structures)
10. [Standard Library APIs](#standard-library-apis)
11. [Advanced Python Patterns](#advanced-python-patterns)
12. [Design Patterns in stream-mypy](#design-patterns-in-stream-mypy)

---

## Module System & Imports

### 1. What It Is

Python code is organized into **modules** (`.py` files) and **packages** (directories with `__init__.py`). You import code from modules to use it in other files.

### 2. Syntax

There are several ways to import:

```python
import module                      # Import entire module
from module import name            # Import specific name
from module import name as alias   # Import with alias
from package.submodule import x    # Import from nested package
from . import name                 # Relative import (from current package)
from .. import name                # Relative import (from parent package)
```

### 3. Simple Example

```python
# constants.py
MAX_SIZE = 100

# main.py
from constants import MAX_SIZE
print(MAX_SIZE)  # Output: 100
```

### 4. stream-mypy Examples

#### Basic Imports in [stream_mypy/main.py](stream_mypy/main.py)

```python
import sys               # Standard library module
import os               # Standard library module
import asyncio          # Standard library module
import argparse         # Standard library module
from pathlib import Path        # Import class from standard library
from typing import List         # Import type from typing
from dotenv import load_dotenv  # Third-party library
```

Each import brings in a module or specific names from it. `sys`, `os`, `asyncio`, and `argparse` are standard library modules. `pathlib.Path` is a class for path operations. `typing.List` is a type hint used for annotations.

#### Module-Level Code Execution

```python
# stream_mypy/main.py
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, verbose=False)
```

This code **runs when the module is imported or executed**. It finds the `.env` file relative to this file and loads environment variables. `Path(__file__)` gets the path to the current file.

#### Conditional Module Execution

```python
# stream_mypy/main.py
if __name__ == "__main__":
    main()
```

**What it means:** This code only runs if the file is executed directly, **not** if it's imported into another module.

**Why it matters:** Allows the same file to be used as a reusable module or as an executable script.

#### Nested Package Imports

```python
# stream_mypy/main.py
from stream_mypy.providers import get_provider
from stream_mypy.agent import run_agent, TextEvent, ToolStartEvent, ToolEndEvent, TurnEndEvent
from stream_mypy.tools import tools
from stream_mypy.types import Message
```

These import from nested packages:
- `stream_mypy.providers` is the `providers/__init__.py` file
- `stream_mypy.agent` accesses `agent/__init__.py`
- `stream_mypy.types` is the `types.py` file

Python resolves these paths automatically.

### 5. Runtime Behavior

When you write `from X import Y`, Python:
1. Finds the module `X` (searches `sys.path`)
2. Executes the entire module file (if not already loaded)
3. Extracts the name `Y` from the module's namespace
4. Binds `Y` to the current namespace

If the module was already imported, Python uses the cached version (modules are only executed once per Python session).

### 6. Common Mistakes & Best Practices

**❌ Circular Imports:**
```python
# a.py
from b import func_b

# b.py
from a import func_a  # Error: circular dependency
```

**✅ Break circular imports by moving imports into functions:**
```python
# b.py
def use_func_a():
    from a import func_a  # Import when needed
    return func_a()
```

**✅ Use relative imports within packages:**
```python
# stream_mypy/providers/anthropic.py
from stream_mypy.types import Provider  # ✓ Clear absolute import
from ..types import Provider            # ✓ Or relative import (same meaning)
```

### 7. Related Concepts

- **`__all__`**: Defines what names are exported when someone does `from module import *`
- **`sys.path`**: List of directories Python searches for modules
- **Lazy imports**: Importing inside functions to avoid circular dependencies or reduce startup time

---

## Functions & Docstrings

### 1. What It Is

**Functions** are reusable blocks of code. **Docstrings** are documentation strings that describe what a function does.

### 2. Syntax

```python
def function_name(param1, param2, param3=default_value):
    """Docstring describing the function"""
    # Code here
    return result

async def async_function(param):
    """Async function for concurrent operations"""
    await some_async_call()
```

### 3. Simple Example

```python
def greet(name):
    """Return a greeting message."""
    return f"Hello, {name}!"

print(greet("Alice"))  # Output: Hello, Alice!
```

### 4. stream-mypy Examples

#### Basic Function

```python
# stream_mypy/tools/bash.py
def find_bash() -> str:
    """Find bash executable, preferring Git Bash on Windows"""
    if platform.system() != "Windows":
        return "bash"
    # ...
    return "bash"
```

**Components:**
- `def find_bash() -> str:` — Function name and return type (`str`)
- Docstring explains what it does
- Returns a string

**Runtime:** Calling `find_bash()` executes the function body and returns a string.

#### Functions with Parameters and Type Hints

```python
# stream_mypy/tools/bash.py
def truncate_tail(text: str, max_lines: int = MAX_LINES, max_bytes: int = MAX_BYTES) -> str:
    """Keep the end of output and indicate what was truncated"""
    lines = text.split("\n")
    kept = lines[-max_lines:] if len(lines) > max_lines else lines
    # ...
    return result
```

**Type hints:**
- `text: str` — Parameter `text` must be a string
- `max_lines: int = MAX_LINES` — Integer parameter with default value
- `-> str` — Returns a string

**Runtime:** Python doesn't enforce these hints (they're checked by tools like mypy), but they document expectations.

#### Async Functions

```python
# stream_mypy/tools/bash.py
async def run_bash(command: str, timeout_ms: int) -> str:
    """Run a bash command and return output"""
    try:
        result = subprocess.run(...)
        out = result.stdout + result.stderr
        return f"{out}\n[exit code: {result.returncode}]"
    except subprocess.TimeoutExpired:
        return f"\n[timed out after {timeout_ms / 1000}s]"
```

**`async def` vs `def`:**
- `async def` defines a coroutine (async function)
- Can use `await` keyword inside
- Must be called with `await` or `asyncio.run()` from sync code

**Runtime:** When called, returns a coroutine object (not executing the body yet). The body executes when awaited.

### 5. Nested Functions

```python
# stream_mypy/agent/__init__.py
async def run_agent(...):
    """Run the agent loop"""
    
    def push(message: Message):
        messages.append(message)
        on_event(MessageEvent(message))
    
    # Later: call push()
    push(assistant)
```

**What it is:** A function defined inside another function. It has access to the outer function's variables (closure).

**Runtime:** `push` is created each time `run_agent` is called. It captures `messages` and `on_event` from the enclosing scope.

### 6. Docstrings

```python
def example():
    """Single-line docstring."""
    pass

def another():
    """
    Multi-line docstring.
    
    Explains the function's purpose, parameters, and return value.
    Tools like Sphinx extract these for documentation.
    """
    pass
```

### 7. Common Mistakes & Best Practices

**❌ Mutable default arguments:**
```python
def bad_function(items=[]):  # ❌ Empty list is created ONCE
    items.append(1)
    return items

print(bad_function())  # [1]
print(bad_function())  # [1, 1]  ← Unexpected!
```

**✅ Use `None` as default:**
```python
def good_function(items=None):
    if items is None:
        items = []
    items.append(1)
    return items
```

---

## Classes & Object-Oriented Programming

### 1. What It Is

**Classes** define blueprints for objects. An **object** is an instance of a class with data (attributes) and behavior (methods).

### 2. Syntax

```python
class ClassName:
    """Class docstring"""
    
    def __init__(self, param1):
        """Constructor: called when creating an object"""
        self.param1 = param1
    
    def method(self):
        """Instance method"""
        return self.param1
    
    @classmethod
    def class_method(cls):
        """Class method: operates on the class itself"""
        pass
    
    @staticmethod
    def static_method():
        """Static method: no access to self or cls"""
        pass
```

### 3. Simple Example

```python
class Dog:
    def __init__(self, name):
        self.name = name
    
    def bark(self):
        return f"{self.name} barks!"

dog = Dog("Buddy")
print(dog.bark())  # Output: Buddy barks!
```

### 4. stream-mypy Examples

#### Base Classes (Abstract Interfaces)

```python
# stream_mypy/types.py
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

**Pattern: Base classes define interfaces**
- `Tool` defines what all tools must have: `name`, `description`, `parameters`, and an `execute` method
- Subclasses **implement** these
- The base class raises `NotImplementedError` if a method isn't overridden

**Runtime:** If you try to call `Tool.execute()` directly, it raises `NotImplementedError`. Subclasses override this method.

#### Inheritance & super()

```python
# stream_mypy/tools/bash.py
class BashTool(Tool):
    """Tool for running bash commands"""
    
    def __init__(self):
        super().__init__(
            name="bash",
            description="Run a bash command in the current folder...",
            parameters={...}
        )
    
    async def execute(self, args: Dict[str, Any]) -> str:
        # Implementation
        return result
```

**What it does:**
- `BashTool(Tool)` — inherits from `Tool`
- `super().__init__(...)` — calls the parent class's `__init__` method
- `BashTool` overrides the abstract `execute` method with actual behavior

**Running sequence:**
1. `BashTool()` is called
2. Python calls `BashTool.__init__(self)`
3. Inside, `super().__init__(...)` calls `Tool.__init__`, setting attributes
4. Now the object has `name`, `description`, `parameters`

#### Multiple Inheritance

```python
# stream_mypy/types.py
class StreamEvent(TypedDict, total=False):
    type: str
    delta: str
    message: AssistantMessage
```

**`TypedDict, total=False`:**
- Inherits from `TypedDict` (a typing construct)
- `total=False` means all keys are optional
- This is a type hint, not a regular class — it doesn't create runtime objects

### 5. Important Methods

#### `__init__` (Constructor)

```python
# stream_mypy/agent/__init__.py
class TextEvent:
    def __init__(self, delta: str):
        self.type = "text"
        self.delta = delta
```

Called automatically when creating an object: `TextEvent("hello")`.

#### `__str__` (String Representation)

```python
class Example:
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return f"Example({self.name})"

obj = Example("test")
print(obj)  # Output: Example(test)
```

#### `__repr__` (Debugging Representation)

Same as `__str__` but used in interactive debuggers.

### 6. Common Mistakes & Best Practices

**❌ Mutating shared mutable defaults:**
```python
class Bad:
    items = []  # ❌ Shared between ALL instances
    
    def add(self, item):
        self.items.append(item)

b1 = Bad()
b2 = Bad()
b1.add(1)
print(b2.items)  # [1]  ← b2's items affected!
```

**✅ Initialize in `__init__`:**
```python
class Good:
    def __init__(self):
        self.items = []  # ✓ Each instance has its own
```

---

## Type Hints & Typing Module

### 1. What It Is

**Type hints** are annotations that tell you (and type-checking tools) what types variables and functions expect. They're **not enforced at runtime** but help catch bugs and improve IDE support.

### 2. Syntax

```python
from typing import List, Dict, Optional, Union, Any, Callable, TypedDict, Literal, AsyncGenerator

name: str = "Alice"
age: int = 25
items: List[str] = ["a", "b"]
mapping: Dict[str, int] = {"a": 1}
maybe_name: Optional[str] = None  # or name: str | None (Python 3.10+)
value: Union[int, str] = 5
any_value: Any = "anything goes"
func: Callable[[int, str], bool] = lambda x, y: True
```

### 3. Simple Example

```python
def add(x: int, y: int) -> int:
    """Add two numbers and return the sum"""
    return x + y

result: int = add(5, 3)
```

### 4. stream-mypy Examples

#### Basic Type Hints

```python
# stream_mypy/main.py
def main():
    """Main entry point"""
    try:
        asyncio.run(main_async())
    # ...
```

#### TypedDict (Typed Dictionaries)

```python
# stream_mypy/types.py
class Usage(TypedDict):
    input: int
    output: int

class TextBlock(TypedDict):
    type: Literal["text"]
    text: str
```

**What it is:** A way to annotate dictionary structure. `TextBlock` defines a dict that **must** have:
- Key `"type"` with value `Literal["text"]` (only the string `"text"`)
- Key `"text"` with value `str`

**Runtime behavior:** `TypedDict` doesn't create a real class — it's only for type checking. At runtime, values are still regular dicts:

```python
block: TextBlock = {"type": "text", "text": "hello"}
# ✓ Type checker sees this as TextBlock
# At runtime, it's just a dict
```

#### Union Types

```python
# stream_mypy/types.py
ContentBlock = Union[TextBlock, ToolCallBlock]
Message = Union[UserMessage, AssistantMessage, ToolResultMessage]
```

**Meaning:** `ContentBlock` can be **either** `TextBlock` or `ToolCallBlock`. Type checkers know this and offer narrowing:

```python
def handle_block(block: ContentBlock):
    if block["type"] == "text":
        # Type checker now knows block is TextBlock
        text: str = block["text"]
    elif block["type"] == "toolCall":
        # Type checker now knows block is ToolCallBlock
        name: str = block["name"]
```

#### Literal Types

```python
# stream_mypy/types.py
StopReason = Literal["stop", "length", "toolUse"]
```

**Meaning:** `StopReason` can **only** be one of these exact strings. This prevents typos:

```python
reason: StopReason = "stop"       # ✓ OK
reason: StopReason = "stop me"    # ✗ Type error
```

#### Optional Types

```python
# stream_mypy/agent/__init__.py
assistant: Optional[AssistantMessage] = None

async def walk(
    root: str,
    max_depth: Optional[int] = None,
    # ...
):
```

**Meaning:** `Optional[X]` = `Union[X, None]` — the value can be `X` or `None`.

**Runtime:** `None` is the absence of a value. You must check before using:

```python
if assistant is None:
    raise RuntimeError("No assistant message")
name = assistant["role"]  # ✓ Now safe
```

#### List, Dict, and Generic Types

```python
# stream_mypy/types.py
class AssistantMessage(TypedDict):
    content: List[ContentBlock]
    usage: Usage
```

**Meaning:**
- `List[ContentBlock]` — a list of `ContentBlock` items
- `Dict[str, Any]` — a dict with string keys and any values

**Runtime:** These are still regular Python lists and dicts:

```python
content: List[ContentBlock] = [{"type": "text", "text": "hi"}]
# At runtime: regular list
# Type checker: each item must be ContentBlock
```

#### Callable Types

```python
# stream_mypy/agent/__init__.py
async def run_agent(
    # ...
    on_event: Callable[[Any], None],
    # ...
):
```

**Meaning:** `Callable[[Any], None]` is a function that:
- Takes one argument of type `Any`
- Returns `None` (no meaningful return value)

**Runtime:**

```python
def my_event_handler(event: Any) -> None:
    print(event)

run_agent(..., on_event=my_event_handler)  # ✓ Matches
```

#### AsyncGenerator

```python
# stream_mypy/tools/fsutil.py
async def walk(
    root: str,
    # ...
) -> AsyncGenerator[WalkEntry, None]:
```

**Meaning:** An async generator that:
- **Yields** items of type `WalkEntry`
- Doesn't return anything (`None`)

**Runtime:** You iterate with `async for`:

```python
async for entry in walk(root):
    # entry has type WalkEntry
    print(entry.abs_path)
```

### 5. NamedTuple

```python
# stream_mypy/tools/fsutil.py
from typing import NamedTuple

class WalkEntry(NamedTuple):
    abs_path: str
    rel_path: str
    is_directory: bool
```

**What it is:** A lightweight class for structured data. Like a tuple but with named fields.

**Runtime:**

```python
entry = WalkEntry("/home/user/file.txt", "file.txt", False)
print(entry.abs_path)  # "/home/user/file.txt"
print(entry[0])        # Also "/home/user/file.txt" (tuple indexing)

# Can unpack like a tuple
path, rel, is_dir = entry
```

**Why:** Cleaner than `(path, rel, is_dir)` tuple. Type hints document the structure. Immutable (can't modify).

### 6. Common Mistakes & Best Practices

**❌ Forgetting that type hints aren't enforced:**
```python
def get_number() -> int:
    return "not a number"  # ✗ Type checker catches this, but Python allows it

result = get_number()  # At runtime, result is a string, not int!
print(result + 5)      # TypeError: can only concatenate str with str
```

**✅ Use tools like mypy to catch these:**
```bash
mypy stream_mypy/  # Checks all files
```

**✅ Use type narrowing:**
```python
def handle(value: Union[int, str]):
    if isinstance(value, int):
        # Type checker now knows value is int
        print(value + 5)  # ✓ Type safe
    else:
        # Type checker knows value is str
        print(value.upper())  # ✓ Type safe
```

---

## Async/Await & Asyncio

### 1. What It Is

**Async/await** let you write code that can **pause and resume**, enabling **concurrent** operations. Think of it as "cooperative multitasking" — tasks voluntarily pause to let others run.

### 2. Why It Matters

Imagine fetching data from 3 APIs sequentially (one after another):

```python
# Sequential (slow)
data1 = fetch_api("url1")  # Wait 1 second
data2 = fetch_api("url2")  # Wait 1 second
data3 = fetch_api("url3")  # Wait 1 second
# Total: 3 seconds
```

With async, they can run concurrently:

```python
# Concurrent (fast)
async def fetch_all():
    data1, data2, data3 = await asyncio.gather(
        fetch_api("url1"),
        fetch_api("url2"),
        fetch_api("url3"),
    )
# Total: 1 second (they overlap)
```

### 3. Syntax

```python
async def async_function():
    """Define an async function with async def"""
    result = await other_async_function()
    return result

# Call from synchronous code
import asyncio
asyncio.run(async_function())

# Call from async code
await async_function()
```

### 4. Simple Example

```python
import asyncio

async def say_hello():
    print("Starting")
    await asyncio.sleep(1)  # Pause for 1 second
    print("Done!")

asyncio.run(say_hello())
# Output:
# Starting
# (1 second passes)
# Done!
```

### 5. stream-mypy Examples

#### Main Async Wrapper

```python
# stream_mypy/main.py
async def main_async():
    """Main async function"""
    parser = argparse.ArgumentParser(...)
    # ... parse arguments ...
    
    await run_agent(
        provider=provider,
        model=model,
        tools=tools,
        messages=messages,
        on_event=on_event,
    )

def main():
    """Main entry point"""
    try:
        asyncio.run(main_async())  # Run async code from sync context
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Flow:**
1. `main()` is called (synchronous)
2. `asyncio.run(main_async())` starts the event loop
3. `main_async()` runs asynchronously
4. When `main_async()` finishes, the event loop stops

#### Async Functions Calling Each Other

```python
# stream_mypy/agent/__init__.py
async def run_agent(...):
    for turn in range(1, max_turns + 1):
        async for event in provider.stream({...}):
            if event.get("type") == "text_delta":
                on_event(TextEvent(event.get("delta", "")))
            elif event.get("type") == "done":
                assistant = event.get("message")
        
        # Execute tools
        for call in assistant["content"]:
            result = await tool.execute(call["arguments"])
```

**Structure:**
- `run_agent` is async
- It calls `provider.stream()` which returns an async generator
- It awaits `tool.execute()` which is an async function
- Each `await` pauses until that operation completes

#### Async with Context Manager

```python
# stream_mypy/providers/anthropic.py
async with self.client.messages.stream(
    model=model,
    max_tokens=4096,
    system=system,
    messages=messages,
    tools=anthropic_tools if anthropic_tools else None,
) as stream:
    async for event in stream:
        # Process events
        pass
    
    final_message = await stream.get_final_message()
```

**What it does:**
- `async with` — enters a context (stream starts)
- Code inside runs while the stream is active
- When exiting, cleanup happens (stream closes)
- Type: `as stream` gives you the context manager object

**Runtime behavior:**
1. `__aenter__` method is called (async version of `__enter__`)
2. Code inside the `with` block runs
3. `__aexit__` is called when exiting (even if an exception occurs)

### 6. Event Loop

Behind the scenes, asyncio runs an **event loop**:

```python
# Conceptual (not real code)
event_loop = asyncio.get_event_loop()
while True:
    # Check all coroutines
    for coroutine in pending_coroutines:
        if coroutine.is_ready():
            # Run it until next await
            result = coroutine.run_until_await()
            
            if coroutine.is_done():
                # Remove from pending
                pending_coroutines.remove(coroutine)
```

Key insight: **Only one coroutine runs at a time**. They take turns at `await` points. This is **concurrency** (not true parallelism), but it works great for I/O operations (network, files).

### 7. Common Mistakes & Best Practices

**❌ Forgetting `await`:**
```python
async def bad():
    result = some_async_function()  # ✗ Creates coroutine, doesn't run it
    print(result)  # <coroutine object> — not the actual result!

async def good():
    result = await some_async_function()  # ✓ Runs and gets result
    print(result)  # Actual result
```

**❌ Mixing async and sync:**
```python
async def bad():
    # ✗ Can't await sync functions
    result = await os.path.exists("file.txt")  # Error!

async def good():
    # ✓ Call sync functions normally
    result = os.path.exists("file.txt")  # OK
```

**✅ Use `asyncio.gather()` to run multiple async operations concurrently:**

```python
async def fetch_data():
    # These three run concurrently
    results = await asyncio.gather(
        fetch_url("url1"),
        fetch_url("url2"),
        fetch_url("url3"),
    )
    return results
```

### 8. Relationship to Threading

| Aspect | Async | Threading |
|--------|-------|-----------|
| **Concurrency model** | Cooperative (via `await`) | Preemptive (OS interrupts) |
| **Number of threads** | Single thread | Multiple threads |
| **GIL* impact** | No GIL issues | GIL limits parallelism |
| **Best for** | I/O operations | CPU-bound work (with workarounds) |
| **Complexity** | Moderate | Complex (race conditions) |

*GIL = Global Interpreter Lock

---

## Generators & Async Generators

### 1. What It Is

**Generators** are functions that **yield** values one at a time, pausing between yields. **Async generators** are generators that can `await`.

### 2. Syntax

```python
# Regular generator
def regular_generator():
    yield 1
    yield 2
    yield 3

# Async generator
async def async_gen():
    yield 1
    await asyncio.sleep(0.1)
    yield 2
```

### 3. Simple Example

```python
def count_up(n):
    for i in range(n):
        yield i

for value in count_up(3):
    print(value)
# Output: 0, 1, 2
```

### 4. stream-mypy Examples

#### Async Generators in File Walking

```python
# stream_mypy/tools/fsutil.py
async def walk(
    root: str,
    max_depth: Optional[int] = None,
    include_hidden: bool = False,
    ignores: Optional[set] = None,
) -> AsyncGenerator[WalkEntry, None]:
    """Recursively walk directory tree, yielding files and directories"""
    
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
            
            # ... filtering logic ...
            
            yield WalkEntry(abs_path, rel_path, is_directory)
            
            if is_directory and depth < max_depth:
                async for entry in recurse(abs_path, depth + 1):
                    yield entry
    
    async for entry in recurse(root, 1):
        yield entry
```

**What it does:**
1. `async def walk()` makes it an async generator
2. `async def recurse()` — nested async function
3. `yield WalkEntry(...)` — produces one entry
4. `async for entry in recurse(...)` — iterates over nested generator's yields
5. Recursively yields from all subdirectories

**Runtime flow:**

```python
# Usage
async for entry in walk("/home/user"):
    print(entry.rel_path)
    # After each iteration, walk() pauses at a yield
    # Control returns to you
    # Next iteration resumes after the yield
```

**Key insight:** The function pauses at `yield`, allowing you to process one result before it computes the next. This saves memory (doesn't load all files at once).

#### Streaming API Responses

```python
# stream_mypy/providers/anthropic.py
async def stream(self, opts: StreamOptions) -> AsyncGenerator[StreamEvent, None]:
    """Stream responses from Claude"""
    async with self.client.messages.stream(...) as stream:
        content: List[ContentBlock] = []
        
        async for event in stream:
            if event.type == "content_block_start":
                # Handle event
                pass
            elif event.type == "content_block_delta":
                # Process delta
                yield {"type": "text_delta", "delta": event.delta.text}
            elif event.type == "content_block_stop":
                # Handle stop
                pass
        
        final_message = await stream.get_final_message()
        yield {
            "type": "done",
            "message": {
                "role": "assistant",
                "content": content,
                "usage": {...},
                "stopReason": stop_reason,
            }
        }
```

**Pattern:**
- Iterates over incoming events from the API
- `yield` sends each delta to the caller
- Accumulates final state
- At the end, yields the complete message

**Runtime:**
```python
async for event in provider.stream(options):
    if event["type"] == "text_delta":
        print(event["delta"], end="")  # Print streaming text
    elif event["type"] == "done":
        print("\n[Finished]")
        message = event["message"]
```

### 5. Why Generators Matter

**Memory efficiency:**
```python
# Without generator (loads everything)
def get_all_files():
    files = []
    for file in list_all_files():
        files.append(file)
    return files  # Huge list in memory

# With generator (lazy evaluation)
async def get_all_files():
    for file in list_all_files():
        yield file  # One at a time
```

If you're walking a directory with 1 million files, the generator approach uses constant memory. The non-generator approach needs memory for all 1 million entries.

### 6. Common Mistakes & Best Practices

**❌ Forgetting that generators must be iterated:**
```python
def bad():
    gen = my_generator()  # ✗ Creates generator, doesn't execute it
    print(gen)  # <generator object>

def good():
    for item in my_generator():  # ✓ Iterates and executes
        print(item)
```

**✅ Use list comprehensions for small datasets:**
```python
# Small data: OK to load all
small_list = [x for x in fetch_small_data()]

# Large data: Use generator
for item in fetch_large_data():
    process(item)
```

---

## Exception Handling

### 1. What It Is

**Exceptions** are errors that occur during execution. **Exception handling** lets you catch them and respond gracefully instead of crashing.

### 2. Syntax

```python
try:
    # Code that might raise an exception
    result = risky_operation()
except SpecificException as e:
    # Handle specific exception
    print(f"Error: {e}")
except (OtherException, AnotherException) as e:
    # Handle multiple exception types
    print(f"Another error: {e}")
except Exception as e:
    # Catch any exception (too broad, avoid this)
    print(f"Unknown error: {e}")
else:
    # Runs if no exception occurred
    print("Success!")
finally:
    # Runs regardless (use for cleanup)
    cleanup()
```

### 3. Simple Example

```python
try:
    age = int("not a number")
except ValueError:
    print("Invalid age input")
```

### 4. stream-mypy Examples

#### Basic Try-Except in Main

```python
# stream_mypy/main.py
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

**Handles:**
- `KeyboardInterrupt` — user pressed Ctrl+C
- `Exception` — any other error
- Exits with non-zero code (signals failure to OS)

#### Try-Except in Providers

```python
# stream_mypy/tools/bash.py
async def run_bash(command: str, timeout_ms: int) -> str:
    """Run a bash command and return output"""
    try:
        bash_exe = find_bash()
        result = subprocess.run(...)
        out = result.stdout + result.stderr
        return f"{out}\n[exit code: {result.returncode}]"
    except subprocess.TimeoutExpired:
        return f"\n[timed out after {timeout_ms / 1000}s]"
    except Exception as e:
        return f"failed to start bash: {str(e)}"
```

**Handles:**
- `subprocess.TimeoutExpired` — command took too long
- `Exception` — any other error (file not found, permission denied, etc.)
- Returns error messages instead of raising (graceful degradation)

#### Try-Except in Agent Loop

```python
# stream_mypy/agent/__init__.py
try:
    tool = next((t for t in tools if t.name == call["name"]), None)
    if not tool:
        raise RuntimeError(f"Unknown tool: {call['name']}")
    
    result = await tool.execute(call["arguments"])
except Exception as e:
    result = f"Error: {str(e)}"
    is_error = True

on_event(ToolEndEvent(call, result, is_error))
```

**Pattern:**
- Tries to execute a tool
- If it fails, catches the exception
- Converts it to an error message
- Still sends a result (instead of crashing)

#### Try-Except in Provider Initialization

```python
# stream_mypy/main.py
try:
    provider = get_provider(args.provider)
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
```

#### Try-Except in File Operations

```python
# stream_mypy/tools/grep.py
try:
    with open(entry.abs_path, "rb") as f:
        file_content = f.read()
    
    if len(file_content) > MAX_FILE_BYTES:
        continue
    
    if b"\x00" in file_content:
        continue  # Skip binary files
    
    content = file_content.decode("utf-8", errors="ignore")
except Exception:
    continue  # Skip this file and continue
```

**Pattern:**
- Opens a file
- If any error occurs (file deleted, permission denied, etc.), skip it
- Continues with the next file

### 5. Common Mistakes & Best Practices

**❌ Too broad exception handling:**
```python
try:
    result = parse_json(data)
except Exception:  # ✗ Catches everything (even bugs you should see)
    print("Parse error")
```

**✅ Catch specific exceptions:**
```python
try:
    result = parse_json(data)
except json.JSONDecodeError as e:  # ✓ Specific exception
    print(f"Invalid JSON: {e}")
except UnicodeDecodeError as e:  # ✓ Different error
    print(f"Invalid encoding: {e}")
```

**❌ Silently swallowing errors:**
```python
try:
    important_operation()
except:  # ✗ No exception type, no message
    pass  # What went wrong? No idea!
```

**✅ Log or handle meaningfully:**
```python
try:
    important_operation()
except RuntimeError as e:  # ✓ Specific
    logger.error(f"Operation failed: {e}")  # ✓ Log it
    raise  # ✓ Or re-raise if it's critical
```

---

## String Operations & Encoding

### 1. What It Is

**Strings** are sequences of characters. **Encoding** is converting between text and bytes.

### 2. Syntax

```python
# String literals
s = "Hello"
s = 'Hello'
s = """Multi-line
string"""

# f-strings (formatted strings)
name = "Alice"
s = f"Hello, {name}!"

# Raw strings (backslashes aren't special)
path = r"C:\Users\name"  # No need to escape backslashes

# Encoding
text = "Hello"
bytes_data = text.encode("utf-8")  # str -> bytes
text = bytes_data.decode("utf-8")  # bytes -> str
```

### 3. Simple Example

```python
name = "World"
greeting = f"Hello, {name}!"
print(greeting)  # Output: Hello, World!

data = greeting.encode("utf-8")
print(data)  # b'Hello, World!'
```

### 4. stream-mypy Examples

#### F-strings

```python
# stream_mypy/main.py
print(f"\n  {provider.name} ... {model} ... {usage['input']} ... {usage['output']} ... {stop_reason}")

# stream_mypy/tools/bash.py
return f"[truncated: showing the last {len(kept)} of {len(lines)} lines]\n{result}"

# stream_mypy/tools/grep.py
results.append(f"{entry.rel_path}:{line_num}:{line}")
```

**Format:** `f"text {variable} more text"`

**Runtime:** Python evaluates expressions inside `{}` and formats them as strings.

#### String Methods

```python
# stream_mypy/tools/fsutil.py
normalized = pattern.replace("\\", "/")  # Replace backslashes with forward slashes
c in ".+^${}()|[]\\"  # Check if character is in string

# stream_mypy/tools/bash.py
lines = text.split("\n")  # Split by newline
kept_text = "\n".join(kept)  # Join list with newlines

# stream_mypy/tools/grep.py
if pattern_re.search(line):  # Check if regex matches
return "\n".join(results)  # Join results with newlines

# stream_mypy/agent/__init__.py
result = f"Error: {str(e)}"
```

**Common string methods:**
- `.split(sep)` — split by separator, returns list
- `.join(list)` — join list items with separator
- `.replace(old, new)` — replace all occurrences
- `.startswith(prefix)` / `.endswith(suffix)` — check start/end
- `.strip()` / `.lstrip()` / `.rstrip()` — remove whitespace
- `.lower()` / `.upper()` — change case
- `.find(sub)` — find substring index (returns -1 if not found)

#### Encoding & Decoding

```python
# stream_mypy/tools/bash.py
out = result.stdout + result.stderr  # Strings (already decoded by subprocess.run with text=True)
return f"{out}\n[exit code: {result.returncode}]"

# stream_mypy/tools/grep.py
with open(entry.abs_path, "rb") as f:  # Open in binary mode
    file_content = f.read()  # Returns bytes

if b"\x00" in file_content:  # Check for null byte (binary file indicator)
    continue

content = file_content.decode("utf-8", errors="ignore")  # Decode bytes to string
```

**Flow:**
1. `open(..., "rb")` opens file in binary mode (returns bytes)
2. `.read()` returns bytes
3. `.decode("utf-8", ...)` converts bytes to string
4. `errors="ignore"` drops non-UTF-8 bytes (graceful degradation)

**Key difference:**
- `str` — text (what humans read)
- `bytes` — data (what files store)

### 5. Common Mistakes & Best Practices

**❌ Mixing str and bytes:**
```python
text = "Hello"
data = b"World"
result = text + data  # ✗ TypeError: can't concat str and bytes
```

**✅ Convert explicitly:**
```python
text = "Hello"
data = b"World"
result = text + data.decode("utf-8")  # ✓ Convert bytes to str
```

**❌ Assuming UTF-8:**
```python
with open("file.txt", "rb") as f:
    content = f.read().decode("utf-8")  # ✗ Fails on non-UTF-8 files
```

**✅ Handle encoding errors gracefully:**
```python
with open("file.txt", "rb") as f:
    content = f.read().decode("utf-8", errors="replace")  # ✓ Replaces bad bytes with U+FFFD
    # or
    content = f.read().decode("utf-8", errors="ignore")  # ✓ Drops bad bytes
```

**✅ Use f-strings for modern code:**
```python
# Old style
name = "Alice"
age = 30
greeting = "Hello, %s. You are %d years old." % (name, age)

# Better
greeting = f"Hello, {name}. You are {age} years old."
```

---

## Collections & Data Structures

### 1. What It Is

Python provides built-in data structures: **lists**, **tuples**, **sets**, and **dicts**.

### 2. Syntax

```python
# List (mutable, ordered)
items = [1, 2, 3]
items.append(4)
items[0] = 10

# Tuple (immutable, ordered)
point = (1, 2, 3)
x, y, z = point  # Unpacking

# Set (unordered, unique)
colors = {"red", "blue", "green"}
colors.add("yellow")
colors.discard("red")

# Dict (key-value, unordered in old Python, ordered in 3.7+)
user = {"name": "Alice", "age": 30}
user["email"] = "alice@example.com"
value = user.get("phone", "Not set")  # Get with default
```

### 3. Simple Example

```python
fruits = ["apple", "banana"]
fruits.append("orange")
print(fruits)  # ['apple', 'banana', 'orange']

person = {"name": "Bob", "age": 25}
print(person["name"])  # Bob
```

### 4. stream-mypy Examples

#### Lists

```python
# stream_mypy/types.py
class AssistantMessage(TypedDict):
    content: List[ContentBlock]  # List of content blocks

# stream_mypy/agent/__init__.py
messages: List[Message] = [{"role": "user", "content": args.prompt}]
# Add to list
messages.append(message)

# stream_mypy/tools/grep.py
results = []
results.append(f"{entry.rel_path}:{line_num}:{line}")
return "\n".join(results)
```

**Operations:**
- Create: `[]` or `list()`
- Add: `.append(item)` or `.extend(list)`
- Access: `items[index]` or `items[start:end:step]`
- Remove: `.remove(item)` or `.pop(index)`
- Iterate: `for item in items`

#### Tuples

```python
# stream_mypy/tools/fsutil.py
class WalkEntry(NamedTuple):
    abs_path: str
    rel_path: str
    is_directory: bool

# Used as
entry = WalkEntry("/home/user", "file.txt", False)
abs_path, rel_path, is_dir = entry  # Unpacking
```

#### Sets

```python
# stream_mypy/tools/fsutil.py
DEFAULT_IGNORES = {".git", "node_modules", "dist", "build", ".next", "coverage"}

def should_ignore(name: str, ignores: set) -> bool:
    return name in ignores  # O(1) lookup (fast)
```

**Set advantages:**
- Membership testing is O(1) (very fast)
- No duplicates
- Unordered

#### Dicts

```python
# stream_mypy/types.py
class TextBlock(TypedDict):
    type: Literal["text"]
    text: str

# Used as
block: TextBlock = {"type": "text", "text": "hello"}

# stream_mypy/agent/__init__.py
push({
    "role": "toolResult",
    "toolCallId": call["id"],
    "toolName": call["name"],
    "content": result,
    "isError": is_error,
})

# stream_mypy/tools/bash.py
parameters={
    "type": "object",
    "properties": {
        "command": {"type": "string", "description": "..."},
        "timeout": {"type": "number", "description": "..."},
    },
    "required": ["command"],
}

# DictOperations
value = dict.get("key", default)  # Safe access
for key, value in dict.items():  # Iterate key-value pairs
if "key" in dict:  # Check existence
del dict["key"]  # Delete
```

### 5. Common Mistakes & Best Practices

**❌ Modifying list while iterating:**
```python
items = [1, 2, 3, 4, 5]
for item in items:
    if item % 2 == 0:
        items.remove(item)  # ✗ Skips items, unpredictable behavior
```

**✅ Iterate over a copy or collect mutations:**
```python
items = [1, 2, 3, 4, 5]
for item in items[:]:  # ✓ Iterate over copy
    if item % 2 == 0:
        items.remove(item)

# Or better
items = [item for item in items if item % 2 != 0]  # ✓ List comprehension
```

**❌ Dict key order (in old Python):**
```python
# In Python 3.7+, dicts maintain insertion order
# But older code might not rely on this!
dict = {"z": 1, "a": 2}
print(list(dict.keys()))  # ['z', 'a'] in 3.7+
```

**✅ Use OrderedDict if you need guaranteed order:**
```python
from collections import OrderedDict
d = OrderedDict([("z", 1), ("a", 2)])
```

---

## Standard Library APIs

### 1. What It Is

Python includes "batteries included" — powerful built-in modules for common tasks. Key modules in stream-mypy:

- `os` — operating system operations
- `sys` — system-specific parameters
- `subprocess` — run external processes
- `asyncio` — async I/O
- `argparse` — command-line parsing
- `json` — JSON encoding/decoding
- `re` — regular expressions
- `pathlib` — object-oriented file paths
- `platform` — platform detection
- `shutil` — file operations

### 2. os Module

```python
# stream_mypy/main.py
os.getcwd()  # Current working directory
os.path.exists(path)  # Check if path exists
os.path.join(dir, file)  # Join path components

# stream_mypy/tools/bash.py
os.path.expandvars(r"%ProgramFiles%\Git\bin\bash.exe")  # Expand env vars

# stream_mypy/tools/fsutil.py
os.listdir(dir)  # List files in directory
os.path.isdir(path)  # Check if directory
os.path.relpath(path, start)  # Get relative path
```

### 3. subprocess Module

```python
# stream_mypy/tools/bash.py
result = subprocess.run(
    [bash_exe, "-c", command],  # Command to run
    capture_output=True,  # Capture stdout/stderr
    text=True,  # Return as strings (not bytes)
    timeout=timeout_ms / 1000,  # Timeout in seconds
    cwd=os.getcwd(),  # Working directory
)

# Access results
result.stdout  # Standard output
result.stderr  # Standard error
result.returncode  # Exit code (0 = success)
```

**Why:** Run shell commands from Python and capture output.

### 4. argparse Module

```python
# stream_mypy/main.py
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

args = parser.parse_args()

# Access parsed arguments
print(args.prompt)  # From -p or --prompt
print(args.provider)  # From --provider (or default)
```

**Flow:**
1. Create `ArgumentParser`
2. Add arguments with `.add_argument()`
3. Call `.parse_args()` to parse command-line
4. Access parsed values as attributes

### 5. json Module

```python
# stream_mypy/providers/openai_compat.py
import json

# Serialize Python object to JSON string
json_string = json.dumps({"name": "Alice", "age": 30})

# Deserialize JSON string to Python object
obj = json.loads(json_string)

# In Anthropic provider
tool_calls = [
    {
        "id": b["id"],
        "function": {
            "name": b["name"],
            "arguments": json.dumps(b["arguments"]),  # Convert dict to JSON string
        },
    }
]

# Later
arguments = json.loads(call["args"])  # Convert JSON string back to dict
```

### 6. re Module (Regular Expressions)

```python
# stream_mypy/tools/fsutil.py
import re

pattern = re.compile(r"\.py$")  # Match files ending in .py
if pattern.search("script.py"):  #  ✓ Match found
    pass

# stream_mypy/tools/grep.py
try:
    flags = re.IGNORECASE if ignore_case else 0
    pattern_re = re.compile(pattern_str, flags)
except re.error as e:
    return f"invalid regex: {str(e)}"

# Search in text
if pattern_re.search(line):  # Find pattern in line
    pass

pattern_re.match(text)  # Match at start of string
pattern_re.findall(text)  # Find all matches
pattern_re.sub(replacement, text)  # Replace matches
```

### 7. pathlib Module

```python
# stream_mypy/main.py
from pathlib import Path

env_path = Path(__file__).parent.parent.parent / ".env"
# Path(__file__) — path to current file
# .parent — parent directory
# ... / ".env" — join paths (more readable than os.path.join)

load_dotenv(env_path, verbose=False)
```

**Why:** OOP-style path handling (cleaner than `os.path`).

### 8. platform Module

```python
# stream_mypy/tools/bash.py
import platform

if platform.system() != "Windows":
    return "bash"
```

**`platform.system()`** — returns OS: "Windows", "Linux", "Darwin" (macOS), etc.

### 9. shutil Module

```python
# stream_mypy/tools/bash.py
import shutil

bash_path = shutil.which("bash")  # Find executable in PATH
if bash_path and "system32" not in bash_path.lower():
    return bash_path
```

**`shutil.which()`** — finds an executable command in `PATH`.

---

## Advanced Python Patterns

### 1. List Comprehensions

#### What It Is

Concise syntax for creating lists by filtering/transforming.

#### Syntax

```python
[expression for item in iterable if condition]
```

#### Simple Example

```python
numbers = [1, 2, 3, 4, 5]
squares = [n ** 2 for n in numbers if n % 2 == 0]
print(squares)  # [4, 16]
```

#### stream-mypy Examples

```python
# stream_mypy/providers/openai_compat.py
text_blocks = [b for b in msg["content"] if b["type"] == "text"]
tool_blocks = [b for b in msg["content"] if b["type"] == "toolCall"]

text = "".join(b["text"] for b in text_blocks)

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

# stream_mypy/agent/__init__.py
"tools": [
    {
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
    }
    for tool in tools
] if tools else []
```

### 2. Generator Expressions

Like list comprehensions but returns generator (memory-efficient):

```python
(expression for item in iterable if condition)
```

#### stream-mypy Example

```python
# stream_mypy/agent/__init__.py
tool = next((t for t in tools if t.name == call["name"]), None)
```

**`next(generator, default)`:**
- Runs the generator until first item
- Returns first item matching `t.name == call["name"]`
- If no match, returns `None`

### 3. Dictionary Comprehensions

Create dicts concisely:

```python
{key: value for item in iterable if condition}
```

### 4. Unpacking

#### Tuple Unpacking

```python
# stream_mypy/tools/fsutil.py
x, y, z = point  # Unpack tuple

# stream_mypy/agent/__init__.py
for call in assistant["content"]:  # Each iteration unpacks
    pass
```

#### Dictionary Unpacking (Python 3.5+)

```python
dict1 = {"a": 1}
dict2 = {"b": 2}
merged = {**dict1, **dict2}  # {"a": 1, "b": 2}
```

### 5. Default Arguments & Keyword Arguments

#### Default Arguments

```python
# stream_mypy/agent/__init__.py
async def run_agent(
    provider: Provider,
    model: str,
    tools: List[Tool],
    messages: List[Message],
    on_event: Callable[[Any], None],
    system: Optional[str] = None,
    max_turns: int = 20,
) -> None:
```

- `system=None` — default value if not provided
- `max_turns=20` — default value
- **Called as:** `run_agent(provider, model, tools, messages, on_event)` (uses defaults)
- **Or:** `run_agent(..., system="Be helpful", max_turns=10)` (override)

#### Keyword-Only Arguments

```python
# stream_mypy/tools/fsutil.py
async def walk(
    root: str,
    max_depth: Optional[int] = None,
    include_hidden: bool = False,
    ignores: Optional[set] = None,
) -> AsyncGenerator[WalkEntry, None]:
```

All parameters after the first one are keyword-only in practice (can be called by name):

```python
walk("/home", include_hidden=True)
walk("/home", ignores={"node_modules"})
```

### 6. Context Managers (with statement)

Ensure cleanup code runs:

```python
with open_resource() as resource:
    # Use resource
    # Cleanup runs automatically when exiting
    pass
```

#### Async Context Managers

```python
# stream_mypy/providers/anthropic.py
async with self.client.messages.stream(...) as stream:
    async for event in stream:
        # Process events
        pass
    # Cleanup runs when exiting (stream closes)
```

### 7. isinstance() Type Checking

```python
# stream_mypy/main.py
def on_event(event):
    if isinstance(event, TextEvent):
        sys.stdout.write(event.delta)
    elif isinstance(event, ToolStartEvent):
        print(f"\n {event.call['name']}")
    elif isinstance(event, ToolEndEvent):
        # ...
    elif isinstance(event, TurnEndEvent):
        # ...
```

**What it does:** Checks the runtime type of an object. Enables **type narrowing** — once you know the type, you can access type-specific attributes.

### 8. Dict.get() with Default

```python
# stream_mypy/agent/__init__.py
if event.get("type") == "text_delta":
    on_event(TextEvent(event.get("delta", "")))
```

**`dict.get(key, default)`:**
- Returns `dict[key]` if it exists
- Returns `default` if key doesn't exist
- No `KeyError` exception

### 9. Callable Types & Callbacks

```python
# stream_mypy/agent/__init__.py
async def run_agent(
    # ...
    on_event: Callable[[Any], None],
    # ...
) -> None:
    def on_event(event):  # Called for each event
        # Process event
        pass
    
    on_event(TextEvent("hello"))  # Call the callback
```

**Pattern:** Pass a function to another function. The recipient calls it at certain points.

### 10. Enums (Type-Safe Constants)

Not directly used in stream-mypy, but good to know:

```python
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

color = Color.RED
if color == Color.RED:
    pass
```

Better than magic strings for fixed sets of values.

---

## Design Patterns in stream-mypy

### 1. Strategy Pattern (Provider)

**What it is:** Multiple implementations of the same interface.

```python
# stream_mypy/types.py
class Provider:
    async def stream(self, opts: StreamOptions):
        raise NotImplementedError

# stream_mypy/providers/anthropic.py
class AnthropicProvider(Provider):
    async def stream(self, opts):
        # Anthropic-specific implementation

# stream_mypy/providers/openai_compat.py
class OpenAICompatibleProvider(Provider):
    async def stream(self, opts):
        # OpenAI-specific implementation

# stream_mypy/providers/__init__.py
PROVIDERS = {
    "anthropic": create_anthropic,
    "groq": lambda: create_openai_compat("groq", ...),
}

def get_provider(name: str) -> Provider:
    create_func = PROVIDERS.get(name)
    if not create_func:
        raise RuntimeError(f"Unknown provider: {name}")
    return create_func()
```

**Usage:**
```python
provider = get_provider("anthropic")  # Returns AnthropicProvider
# vs
provider = get_provider("groq")       # Returns OpenAICompatibleProvider
# Same interface, different implementations
```

### 2. Factory Pattern

```python
# stream_mypy/providers/anthropic.py
def create_anthropic() -> Provider:
    return AnthropicProvider()

# stream_mypy/providers/openai_compat.py
def create_openai_compat(name, base_url, api_key, default_model) -> Provider:
    return OpenAICompatibleProvider(name, base_url, api_key, default_model)
```

**What it is:** Functions that create objects, hiding complex initialization.

### 3. Adapter Pattern (Message Conversion)

```python
# stream_mypy/providers/anthropic.py
def to_anthropic_messages(messages: List[Message]) -> List[Dict[str, Any]]:
    """Convert our message format to Anthropic's format"""
    result = []
    for msg in messages:
        # Convert each message
        pass
    return result

# stream_mypy/providers/openai_compat.py
def to_openai_messages(messages: List[Message]) -> List[Dict[str, Any]]:
    """Convert our message format to OpenAI's format"""
    result = []
    for msg in messages:
        # Different conversion logic
        pass
    return result
```

**What it is:** Convert between different formats/interfaces.

### 4. Observer Pattern (Events & Callbacks)

```python
# stream_mypy/agent/__init__.py
async def run_agent(
    # ...
    on_event: Callable[[Any], None],  # Observer function
):
    # When something happens, call the observer
    on_event(TextEvent(event.delta))
    on_event(ToolStartEvent(call))
    on_event(ToolEndEvent(call, result, is_error))
    on_event(TurnEndEvent(message))
    on_event(MessageEvent(message))

# stream_mypy/main.py
def on_event(event):
    if isinstance(event, TextEvent):
        sys.stdout.write(event.delta)  # Observer reacts
    elif isinstance(event, ToolStartEvent):
        print(f"\n {event.call['name']}")
```

**What it is:** Objects notify other objects of state changes without tight coupling.

### 5. Dependency Injection

```python
# stream_mypy/agent/__init__.py
async def run_agent(
    provider: Provider,  # Injected dependency
    model: str,
    tools: List[Tool],  # Injected dependency
    messages: List[Message],
    on_event: Callable[[Any], None],  # Injected callback
    # ...
):
    # Function receives dependencies, doesn't create them
    async for event in provider.stream({...}):  # Use provider
        # ...
        result = await tool.execute(...)  # Use tool
```

**What it is:** Pass dependencies as arguments instead of creating them inside.

**Benefits:**
- Easy to test (inject mocks)
- Easy to extend (inject different implementations)
- Decoupled (function doesn't depend on concrete classes)

---

## Python Internals & Runtime Behavior

### 1. Attribute Resolution

When you access `obj.name`, Python searches:

1. Instance `__dict__`
2. Class `__dict__`
3. Parent class `__dict__` (MRO—Method Resolution Order)
4. Raises `AttributeError`

**Example in stream-mypy:**

```python
# stream_mypy/tools/bash.py
class BashTool(Tool):
    def __init__(self):
        super().__init__(
            name="bash",
            description="...",
            parameters={...}
        )

# Later
tool = BashTool()
print(tool.name)  # Searches: instance → BashTool → Tool → AttributeError
# Found in Tool.__init__ as self.name = name
```

### 2. Method Binding

When you call `obj.method()`, Python:
1. Finds the method in the class
2. Binds `self` to the object
3. Calls the method

```python
# stream_mypy/tools/bash.py
class BashTool(Tool):
    async def execute(self, args):
        # self is automatically bound to the BashTool instance
        return await run_bash(...)

tool = BashTool()
result = await tool.execute({"command": "echo hello"})
# Behind the scenes: BashTool.execute(tool, {"command": "echo hello"})
```

### 3. Module Caching

```python
# module.py
import expensive_module

# First import: module code executes
import module  # Loads expensive_module once

# Second import: uses cached version
import module  # Doesn't reload, returns cached module
```

### 4. Global & Local Scope

```python
# stream_mypy/tools/fsutil.py
DEFAULT_IGNORES = {".git", ...}  # Global (module-level)

async def walk(root, ...):
    ignores = opts.ignores or DEFAULT_IGNORES  # Local variable
    
    async def recurse(dir, depth):
        # Has access to walk's variables (closure)
        entries = os.listdir(dir)
```

### 5. Garbage Collection

Python automatically deletes objects when no references exist:

```python
async def run_bash(...):
    try:
        result = subprocess.run(...)
        # ...
    except subprocess.TimeoutExpired:
        # result object might be garbage collected here if error
        return error_message
    # If no exception, result is garbage collected when function exits
```

---

## Summary & Best Practices

### Key Python Concepts Used in stream-mypy

| Concept | Where Used | Purpose |
|---------|-----------|---------|
| **Async/await** | `main.py`, `agent/__init__.py`, `providers/*.py` | Concurrent execution |
| **Async generators** | `tools/fsutil.py`, `providers/anthropic.py` | Lazy stream of data |
| **TypedDict** | `types.py` | Type-safe dict structures |
| **Union types** | `types.py` | Allow multiple types |
| **Literal types** | `types.py` | Restrict to specific values |
| **Generator expressions** | `agent/__init__.py` | Memory-efficient `next()` search |
| **List comprehensions** | `providers/openai_compat.py` | Transform/filter lists |
| **isinstance() checking** | `main.py`, `agent/__init__.py` | Runtime type dispatch |
| **Context managers** | `providers/anthropic.py` | Resource cleanup (async with) |
| **Exception handling** | `tools/bash.py`, `agent/__init__.py` | Graceful error handling |
| **String encoding** | `tools/grep.py` | Handle binary/text files |
| **Regex** | `tools/grep.py`, `tools/find.py` | Pattern matching |
| **subprocess** | `tools/bash.py` | Run external commands |
| **argparse** | `main.py` | CLI argument parsing |
| **asyncio.run()** | `main.py` | Bridge sync to async |
| **Callback functions** | `agent/__init__.py` | Observer pattern |
| **Mutable vs immutable** | `types.py`, `tools/fsutil.py` | NamedTuple, TypedDict |

### Best Practices Applied

✅ **Type hints everywhere** — Improves IDE support and catches bugs early  
✅ **Meaningful variable names** — Code is self-documenting  
✅ **Docstrings for public functions/classes** — Explains purpose  
✅ **Context managers for resources** — Ensures cleanup  
✅ **Specific exception handling** — Catches expected errors  
✅ **Validation in __init__** — Fail fast with clear errors  
✅ **Dependency injection** — Makes code testable and flexible  
✅ **Async all the way** — Consistent async patterns  
✅ **Generator for large datasets** — Memory-efficient streaming  
✅ **Encoding handling** — Robustly handles different text encodings  

---

## Recommended Reading Order

1. **Module System & Imports** — Foundation for understanding code organization
2. **Functions & Docstrings** — How to write reusable code
3. **Classes & OOP** — Object design patterns
4. **Type Hints** — Essential for understanding stream-mypy's types
5. **Async/Await** — Critical for understanding main execution flow
6. **Generators & Async Generators** — Understand streaming behavior
7. **Standard Library APIs** — See how Python's built-ins are used
8. **Advanced Python Patterns** — Understand actual code patterns
9. **Design Patterns** — Architectural understanding
10. **Python Internals** — Deep understanding of runtime behavior

---

## What You Should Remember

After studying this guide:

1. **stream-mypy is all about async streaming** — Everything uses async/await and generators for concurrent I/O
2. **Types guide the codebase** — TypedDict, Union, Literal, and Callable types define the contracts
3. **Providers implement the same interface** — Strategy pattern lets you swap LLM backends
4. **Events flow through callbacks** — Agent publishes events, main subscribes and prints
5. **Generators are memory-efficient** — Directory walking and message streaming use generators to avoid loading everything
6. **Exception handling is graceful** — Errors become messages, not crashes
7. **Standard library is powerful** — subprocess, argparse, json, regex all save code
8. **Python's simplicity is powerful** — Duck typing + type hints = readable + flexible code

The codebase demonstrates **professional Python** — async patterns, type safety, error handling, and clean design working together.
