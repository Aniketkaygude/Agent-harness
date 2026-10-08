"""Grep tool for searching files"""
import os
import re
from typing import Dict, Any, Optional
from stream_mypy.types import Tool
from stream_mypy.tools.fsutil import walk, glob_to_regex


MAX_MATCHES = 500
MAX_FILE_BYTES = 5 * 1024 * 1024


class GrepTool(Tool):
    """Tool for searching files with regex"""
    
    def __init__(self):
        super().__init__(
            name="grep",
            description="Search for a regex pattern inside files under a directory (recursively). Returns matching file:line:text, like grep -rn.",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory or file to search in, relative to the current folder (default '.')",
                    },
                    "glob": {
                        "type": "string",
                        "description": "Only search files whose relative path matches this glob, e.g. '**/*.ts'",
                    },
                    "ignoreCase": {
                        "type": "boolean",
                        "description": "Case-insensitive search (default false)",
                    },
                    "maxMatches": {
                        "type": "number",
                        "description": f"Max number of matches to return (default {MAX_MATCHES})",
                    },
                },
                "required": ["pattern"],
            },
        )
    
    async def execute(self, args: Dict[str, Any]) -> str:
        root = os.path.join(os.getcwd(), str(args.get("path", ".")))
        pattern_str = str(args["pattern"])
        ignore_case = bool(args.get("ignoreCase", False))
        max_matches = args.get("maxMatches", MAX_MATCHES)
        if not isinstance(max_matches, int):
            max_matches = MAX_MATCHES
        
        glob_pattern = args.get("glob")
        glob_re: Optional[re.Pattern] = None
        if glob_pattern:
            glob_re = glob_to_regex(str(glob_pattern))
        
        # Compile the search regex
        try:
            flags = re.IGNORECASE if ignore_case else 0
            pattern_re = re.compile(pattern_str, flags)
        except re.error as e:
            return f"invalid regex: {str(e)}"
        
        results = []
        match_count = 0
        
        async for entry in walk(root):
            if entry.is_directory:
                continue
            
            if glob_re and not glob_re.match(entry.rel_path):
                continue
            
            try:
                with open(entry.abs_path, "rb") as f:
                    file_content = f.read()
                
                if len(file_content) > MAX_FILE_BYTES:
                    continue
                
                # Skip binary files
                if b"\x00" in file_content:
                    continue
                
                content = file_content.decode("utf-8", errors="ignore")
            except Exception:
                continue
            
            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                if pattern_re.search(line):
                    results.append(f"{entry.rel_path}:{line_num}:{line}")
                    match_count += 1
                    if match_count >= max_matches:
                        results.append(f"[truncated at {max_matches} matches]")
                        return "\n".join(results)
        
        if not results:
            return "(no matches)"
        
        return "\n".join(results)


grep_tool = GrepTool()
