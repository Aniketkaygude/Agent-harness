#!/usr/bin/env python3
"""Test script to verify the Python migration works"""
import asyncio
import sys
import os

# Test imports
print("Testing imports...")
try:
    from stream_mypy.types import (
        Message, Tool, Provider, StreamEvent, StopReason, 
        UserMessage, AssistantMessage, ToolCallBlock, TextBlock
    )
    print("✓ Types imported successfully")
except Exception as e:
    print(f"✗ Failed to import types: {e}")
    sys.exit(1)

try:
    from stream_mypy.providers import get_provider
    print("✓ Providers module imported")
except Exception as e:
    print(f"✗ Failed to import providers: {e}")
    sys.exit(1)

try:
    from stream_mypy.tools import tools
    print(f"✓ Tools imported ({len(tools)} tools available)")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")
except Exception as e:
    print(f"✗ Failed to import tools: {e}")
    sys.exit(1)

try:
    from stream_mypy.agent import run_agent
    print("✓ Agent loop imported")
except Exception as e:
    print(f"✗ Failed to import agent: {e}")
    sys.exit(1)

# Test tools
print("\nTesting tools...")
async def test_tools():
    try:
        # Test read tool
        from stream_mypy.tools.read import read_tool
        print(f"✓ Read tool: {read_tool.name}")
        
        # Test bash tool
        from stream_mypy.tools.bash import bash_tool
        result = await bash_tool.execute({"command": "echo 'Hello from Python!'"})
        print(f"✓ Bash tool works: {result[:50]}...")
        
        # Test ls tool
        from stream_mypy.tools.ls import ls_tool
        result = await ls_tool.execute({"path": "."})
        print(f"✓ List tool works: Found files/directories")
        
        # Test find tool
        from stream_mypy.tools.find import find_tool
        result = await find_tool.execute({"name": "README"})
        print(f"✓ Find tool works")
        
        # Test stat tool
        from stream_mypy.tools.stat import stat_tool
        if os.path.exists("pyproject.toml"):
            result = await stat_tool.execute({"path": "pyproject.toml"})
            print(f"✓ Stat tool works")
        
    except Exception as e:
        print(f"✗ Tool test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

asyncio.run(test_tools())

# Test provider factory
print("\nTesting provider factory...")
try:
    provider = get_provider("anthropic")
    print(f"✓ Created provider: {provider.name}")
    print(f"  Default model: {provider.default_model}")
except Exception as e:
    print(f"✗ Provider factory failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✓ All tests passed! Python migration is working!")
print("="*50)
print("\nYou can now run the agent with:")
print('  python -m stream_mypy.main -p "Your prompt here" --provider anthropic')
print("\nMake sure to set your API keys in the .env file first!")
