"""File system utilities"""
import os
import re
import asyncio
from pathlib import Path
from typing import AsyncGenerator, List, Optional, NamedTuple


DEFAULT_IGNORES = {".git", "node_modules", "dist", "build", ".next", "coverage"}


class WalkEntry(NamedTuple):
    abs_path: str
    rel_path: str
    is_directory: bool


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


def should_ignore(name: str, ignores: set) -> bool:
    """Check if a name should be ignored"""
    return name in ignores


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


async def path_exists(path: str) -> bool:
    """Check if a path exists"""
    return os.path.exists(path)
