"""List directory tool"""
import os
from typing import Dict, Any
from stream_mypy.types import Tool
from stream_mypy.tools.fsutil import walk


class LsTool(Tool):
    """Tool for listing directory contents"""
    
    def __init__(self):
        super().__init__(
            name="ls",
            description="List files and directories recursively under a path. Skips common noise dirs (.git, node_modules, dist, build) and hidden files by default.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory to list, relative to the current folder (default '.')",
                    },
                    "maxDepth": {
                        "type": "number",
                        "description": "How many levels deep to recurse (default: unlimited)",
                    },
                    "includeHidden": {
                        "type": "boolean",
                        "description": "Include dotfiles/dot-directories (default false)",
                    },
                    "dirsOnly": {
                        "type": "boolean",
                        "description": "Only list directories (default false)",
                    },
                },
            },
        )
    
    async def execute(self, args: Dict[str, Any]) -> str:
        root = os.path.join(os.getcwd(), str(args.get("path", ".")))
        max_depth = args.get("maxDepth")
        if max_depth is None:
            max_depth = float("inf")
        include_hidden = bool(args.get("includeHidden", False))
        dirs_only = bool(args.get("dirsOnly", False))
        
        lines = []
        count = 0
        limit = 5000
        
        async for entry in walk(root, max_depth=max_depth, include_hidden=include_hidden):
            if dirs_only and not entry.is_directory:
                continue
            
            if entry.is_directory:
                lines.append(f"{entry.rel_path}/")
            else:
                lines.append(entry.rel_path)
            
            count += 1
            if count >= limit:
                lines.append(f"[truncated at {limit} entries]")
                break
        
        if not lines:
            return "(empty)"
        
        return "\n".join(lines)


ls_tool = LsTool()
