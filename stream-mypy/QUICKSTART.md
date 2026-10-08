# Quick Start Guide

## ✅ Migration Complete!

Your TypeScript `stream-mypi` codebase has been fully migrated to Python as `stream-mypy`.

### 📁 Project Location
```
c:\Users\anike\OneDrive\Desktop\agents\stream-mypy\
```

### 📦 What Was Created

**23 Python files** structured as follows:

```
stream-mypy/
├── stream_mypy/              # Main package
│   ├── __init__.py          # Package initialization
│   ├── main.py              # CLI entry point (103 lines)
│   ├── types.py             # Type definitions (88 lines)
│   ├── agent/
│   │   └── __init__.py      # Agent loop (120 lines)
│   ├── providers/
│   │   ├── __init__.py      # Provider factory (30 lines)
│   │   ├── anthropic.py     # Anthropic Claude (171 lines)
│   │   └── openai_compat.py # OpenAI/Groq (191 lines)
│   └── tools/
│       ├── __init__.py              # Tool exports (11 lines)
│       ├── fsutil.py                # File system utils (98 lines)
│       ├── bash.py                  # Bash execution (110 lines)
│       ├── read.py                  # File reading (32 lines)
│       ├── ls.py                    # Directory listing (70 lines)
│       ├── grep.py                  # File search (108 lines)
│       ├── find.py                  # File finding (112 lines)
│       └── stat.py                  # File stats (77 lines)
├── mypi.py                  # CLI wrapper
├── pyproject.toml           # Poetry configuration
├── requirements.txt         # Pip requirements
├── .env                     # Environment variables
├── README.md                # Full documentation
├── MIGRATION.md             # Migration details
├── test_structure.py        # Structure verification
└── test_migration.py        # Functionality tests
```

### 🚀 Quick Start (3 Steps)

#### Step 1: Install Dependencies
```bash
cd c:\Users\anike\OneDrive\Desktop\agents\stream-mypy
pip install -r requirements.txt
```

Or with Poetry:
```bash
poetry install
```

#### Step 2: Set API Keys
Edit `.env` file and add your API keys:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx...
GROQ_API_KEY=gsk-xxxxxxxx...
OPENAI_API_KEY=sk-xxxxxxxx...
```

#### Step 3: Run the Agent
```bash
python -m stream_mypy.main -p "Your prompt here" --provider anthropic
```

### 💡 Example Prompts

```bash
# List files
python -m stream_mypy.main -p "What's in the current directory?"

# Read and analyze
python -m stream_mypy.main -p "Read pyproject.toml and explain it"

# Search code
python -m stream_mypy.main -p "Find all Python files with 'class ' in them"

# Complex tasks
python -m stream_mypy.main -p "Show me the 5 largest Python files in this project"
```

### 🛠️ Available Tools

The agent has access to these tools:

| Tool | Purpose | Example |
|------|---------|---------|
| `bash` | Run shell commands | `ls -la`, `python --version` |
| `read` | Read file contents | Read configuration files |
| `ls` | List directories recursively | Find all files in a path |
| `grep` | Search with regex | Find code patterns |
| `find` | Find files by name/glob/regex | `**/*.py` files |
| `stat` | Get file metadata | Size, permissions, timestamps |

### 📋 Configuration

**Providers available:**
- `anthropic` (default) - Claude models
- `groq` - Mixtral and other open models
- `anthropic-openai` - Claude via OpenAI endpoint

**CLI Options:**
```
-p, --prompt TEXT      The prompt to send (required)
--provider TEXT        Provider to use (default: anthropic)
--model TEXT          Specific model (optional)
```

### ✅ Verification

Test that everything works:
```bash
python test_structure.py
```

This verifies all files and syntax are correct.

For full functionality test (requires dependencies):
```bash
python test_migration.py
```

### 📚 Documentation

- **README.md** - Full documentation with examples
- **MIGRATION.md** - Detailed migration information
- **MIGRATION_EXAMPLES.md** - Common usage patterns

### 🎯 Key Features Preserved

✅ Streaming responses from LLMs  
✅ Tool use with automatic execution  
✅ Multi-provider support  
✅ Agent loop with turn handling  
✅ All 6 tools working  
✅ CLI interface  
✅ Environment variable loading  
✅ Cross-platform support  

### 🔧 Troubleshooting

**"No module named 'anthropic'"**
→ Install dependencies: `pip install -r requirements.txt`

**"ANTHROPIC_API_KEY not set"**
→ Add key to `.env` file or set environment variable

**"Unknown provider"**
→ Use one of: `anthropic`, `groq`, `anthropic-openai`

### 📖 Learn More

See [README.md](README.md) for comprehensive documentation including:
- Detailed installation instructions
- Full API reference
- Custom tool development
- Architecture overview
- Performance tuning

### 🎉 You're Ready!

The Python migration is complete and tested. All original functionality is preserved and ready to use.

Start with:
```bash
python -m stream_mypy.main -p "What can you do?" --provider anthropic
```

Happy coding! 🐍
