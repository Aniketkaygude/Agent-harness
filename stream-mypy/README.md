# Stream MyPI - Python Migration

Python implementation of the TypeScript stream-mypi agent system. This is an agentic system that works with LLM providers (Anthropic, OpenAI, Groq) to execute tool calls and process responses with streaming support.

## Features

- **Multi-provider support**: Anthropic Claude, OpenAI-compatible APIs (including Groq)
- **Streaming responses**: Real-time text streaming from LLMs
- **Tool execution**: Built-in tools for:
  - `bash`: Run shell commands
  - `read`: Read files
  - `ls`: List directory contents
  - `grep`: Search files with regex
  - `find`: Find files and directories
  - `stat`: Get file metadata
- **Agent loop**: Autonomous agent that streams from provider and executes tools
- **Cross-platform**: Works on Windows (with Git Bash), Linux, and macOS

## Installation

### Prerequisites
- Python 3.9 or higher
- Poetry (recommended) or pip

### Setup with Poetry

```bash
cd stream-mypy
poetry install
```

### Setup with pip

```bash
cd stream-mypy
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env` and add your API keys:

```bash
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk-...
OPENAI_API_KEY=sk-...
```

2. You can also set these as environment variables.

## Usage

### Command Line

```bash
# Using Poetry
poetry run python -m stream_mypy.main -p "What files are in the current directory?" --provider anthropic

# Using Python directly
python -m stream_mypy.main -p "List all Python files" --provider anthropic

# With a different model
python -m stream_mypy.main -p "Your prompt here" --provider anthropic --model claude-opus-4-1-20250805

# With other providers
python -m stream_mypy.main -p "Your prompt" --provider groq
python -m stream_mypy.main -p "Your prompt" --provider anthropic-openai
```

### Options

- `-p, --prompt TEXT`: The prompt to send to the agent (required)
- `--provider TEXT`: Provider to use: `anthropic`, `anthropic-openai`, `groq` (default: anthropic)
- `--model TEXT`: Model to use (optional, uses provider default if not specified)

### Examples

```bash
# Read a file and analyze it
python -m stream_mypy.main -p "Read pyproject.toml and explain its contents"

# Search for patterns
python -m stream_mypy.main -p "Find all Python files and grep for 'class ' in them"

# Run commands
python -m stream_mypy.main -p "What is the current directory and list all files?"

# Complex tasks
python -m stream_mypy.main -p "Find all .py files modified in the last day and show their sizes"
```

## Project Structure

```
stream-mypy/
├── stream_mypy/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── types.py             # Type definitions
│   ├── agent/
│   │   └── __init__.py      # Agent loop implementation
│   ├── providers/
│   │   ├── __init__.py      # Provider factory
│   │   ├── anthropic.py     # Anthropic provider
│   │   └── openai_compat.py # OpenAI-compatible provider
│   └── tools/
│       ├── __init__.py      # Tool exports
│       ├── fsutil.py        # File system utilities
│       ├── bash.py          # Bash tool
│       ├── read.py          # Read tool
│       ├── ls.py            # List directory tool
│       ├── grep.py          # Grep tool
│       ├── find.py          # Find tool
│       └── stat.py          # Stat tool
├── mypi.py                  # CLI entry point
├── pyproject.toml           # Poetry config
├── .env                     # Environment variables
└── README.md                # This file
```

## How It Works

1. **User Input**: Sends a prompt via CLI
2. **Agent Loop**: 
   - Streams response from LLM provider
   - Parses tool calls from response
   - Executes requested tools
   - Feeds tool results back to LLM
   - Repeats until LLM stops requesting tools
3. **Output**: Streams text output in real-time

## Differences from TypeScript Version

- Async/await pattern instead of async generators (where applicable)
- Python-specific imports and patterns
- No npm dependencies, uses pip/poetry
- Better cross-platform bash detection
- Python type hints instead of TypeScript types

## Requirements

- Python 3.9+
- anthropic >= 0.31.0
- openai >= 1.50.0
- python-dotenv >= 1.0.0

## License

ISC

## Migration Notes

This is a complete port of the TypeScript `stream-mypi` project to Python. All functionality has been preserved:

- ✅ Multiple provider support (Anthropic, OpenAI-compatible)
- ✅ Streaming responses
- ✅ All 6 tools (bash, read, ls, grep, find, stat)
- ✅ Agent loop with tool execution
- ✅ CLI argument parsing
- ✅ Environment variable loading
- ✅ Error handling
- ✅ Cross-platform support
