"""Find tool for searching files/directories"""
import os
import re
from typing import Dict, Any, Optional
from stream_mypy.types import Tool
from stream_mypy.tools.fsutil import walk, glob_to_regex


LIMIT = 2000


class FindTool(Tool):
    """Tool for finding files and directories"""
    
    def __init__(self):
        super().__init__(
            name="find",
            description="Find files/directories by name, matching a substring, glob pattern (e.g. '**/*.test.ts') or regex, recursively under a path.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Substring to match against file/directory names",
                    },
                    "glob": {
                        "type": "string",
                        "description": "Glob pattern to match against the relative path, e.g. '**/*.ts'",
                    },
                    "regex": {
                        "type": "string",
                        "description": "Regex to match against the relative path",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search under, relative to the current folder (default '.')",
                    },
                    "type": {
                        "type": "string",
                        "description": "Filter by 'file' or 'dir' (default: both)",
                    },
                    "includeHidden": {
                        "type": "boolean",
                        "description": "Include dotfiles/dot-directories (default false)",
                    },
                },
            },
        )
    
    async def execute(self, args: Dict[str, Any]) -> str:
        root = os.path.join(os.getcwd(), str(args.get("path", ".")))
        name = args.get("name")
        if name:
            name = str(name)
        glob_pattern = args.get("glob")
        if glob_pattern:
            glob_pattern = str(glob_pattern)
        regex_pattern = args.get("regex")
        if regex_pattern:
            regex_pattern = str(regex_pattern)
        type_filter = args.get("type")
        if type_filter:
            type_filter = str(type_filter)
        include_hidden = bool(args.get("includeHidden", False))
        
        if not name and not glob_pattern and not regex_pattern:
            return "error: provide at least one of 'name', 'glob', or 'regex'"
        
        glob_re: Optional[re.Pattern] = None
        if glob_pattern:
            glob_re = glob_to_regex(glob_pattern)
        
        regex_re: Optional[re.Pattern] = None
        if regex_pattern:
            try:
                regex_re = re.compile(regex_pattern)
            except re.error as e:
                return f"invalid regex: {str(e)}"
        
        results = []
        
        async for entry in walk(root, include_hidden=include_hidden):
            if type_filter == "file" and entry.is_directory:
                continue
            if type_filter == "dir" and not entry.is_directory:
                continue
            
            base_name = entry.rel_path.split("/")[-1] if "/" in entry.rel_path else entry.rel_path
            
            if name and name.lower() not in base_name.lower():
                continue
            if glob_re and not glob_re.match(entry.rel_path):
                continue
            if regex_re and not regex_re.search(entry.rel_path):
                continue
            
            if entry.is_directory:
                results.append(f"{entry.rel_path}/")
            else:
                results.append(entry.rel_path)
            
            if len(results) >= LIMIT:
                results.append(f"[truncated at {LIMIT} results]")
                break
        
        if not results:
            return "(no matches)"
        
        return "\n".join(results)


find_tool = FindTool()
