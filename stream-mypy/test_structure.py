#!/usr/bin/env python3
"""Test script to verify the Python migration structure without external dependencies"""
import sys
import os
import ast

def check_syntax(filepath):
    """Check if a Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)

print("Migration Test Report")
print("=" * 60)

# List all Python files to check
python_files = {
    "Core": [
        "stream_mypy/__init__.py",
        "stream_mypy/types.py",
        "stream_mypy/main.py",
    ],
    "Agent": [
        "stream_mypy/agent/__init__.py",
    ],
    "Providers": [
        "stream_mypy/providers/__init__.py",
        "stream_mypy/providers/anthropic.py",
        "stream_mypy/providers/openai_compat.py",
    ],
    "Tools": [
        "stream_mypy/tools/__init__.py",
        "stream_mypy/tools/fsutil.py",
        "stream_mypy/tools/bash.py",
        "stream_mypy/tools/read.py",
        "stream_mypy/tools/ls.py",
        "stream_mypy/tools/grep.py",
        "stream_mypy/tools/find.py",
        "stream_mypy/tools/stat.py",
    ],
}

# Check all files
all_ok = True
for category, files in python_files.items():
    print(f"\n{category}:")
    for filepath in files:
        if os.path.exists(filepath):
            ok, error = check_syntax(filepath)
            if ok:
                # Count lines
                with open(filepath, 'r') as f:
                    lines = len(f.readlines())
                print(f"  ✓ {filepath} ({lines} lines)")
            else:
                print(f"  ✗ {filepath}: {error}")
                all_ok = False
        else:
            print(f"  ✗ {filepath}: File not found")
            all_ok = False

# Check project files
print(f"\nProject Files:")
project_files = {
    "pyproject.toml": "Poetry configuration",
    "requirements.txt": "Pip requirements",
    ".env": "Environment variables",
    "README.md": "Documentation",
    "mypi.py": "CLI entry point",
    "test_migration.py": "Test script",
}

for filename, description in project_files.items():
    if os.path.exists(filename):
        print(f"  ✓ {filename} - {description}")
    else:
        print(f"  ✗ {filename} - {description}")

print("\n" + "=" * 60)

if all_ok:
    print("✓ Migration Complete!")
    print("\nProject structure verified. All Python files have valid syntax.")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Set API keys in .env file")
    print("3. Run: python -m stream_mypy.main -p 'Your prompt' --provider anthropic")
    print("\nAvailable tools:")
    print("  - bash: Run shell commands")
    print("  - read: Read files")
    print("  - ls: List directory contents")
    print("  - grep: Search files")
    print("  - find: Find files/directories")
    print("  - stat: Get file metadata")
else:
    print("✗ Some files have issues. See above.")
    sys.exit(1)
