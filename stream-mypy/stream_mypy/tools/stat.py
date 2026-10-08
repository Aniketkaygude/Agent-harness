"""Stat tool for file information"""
import os
from datetime import datetime
from typing import Dict, Any
from stream_mypy.types import Tool


def format_bytes(bytes_num: int) -> str:
    """Format bytes as human-readable string"""
    if bytes_num < 1024:
        return f"{bytes_num} B"
    
    units = ["KB", "MB", "GB", "TB"]
    value = float(bytes_num)
    unit_idx = -1
    
    while value >= 1024 and unit_idx < len(units) - 1:
        value /= 1024
        unit_idx += 1
    
    return f"{value:.2f} {units[unit_idx]}"


class StatTool(Tool):
    """Tool for getting file/directory metadata"""
    
    def __init__(self):
        super().__init__(
            name="stat",
            description="Get metadata for a file or directory: size, type, created/modified times, permissions.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file or directory, relative to the current folder",
                    },
                },
                "required": ["path"],
            },
        )
    
    async def execute(self, args: Dict[str, Any]) -> str:
        target = os.path.join(os.getcwd(), str(args["path"]))
        stat_info = os.stat(target)
        
        if os.path.isdir(target):
            file_type = "directory"
        elif os.path.islink(target):
            file_type = "symlink"
        elif os.path.isfile(target):
            file_type = "file"
        else:
            file_type = "other"
        
        # Get timestamps
        created = datetime.fromtimestamp(stat_info.st_birthtime if hasattr(stat_info, 'st_birthtime') else stat_info.st_ctime).isoformat()
        modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        accessed = datetime.fromtimestamp(stat_info.st_atime).isoformat()
        
        # Get permissions (Unix-style)
        mode = stat_info.st_mode & 0o777
        
        lines = [
            f"path: {target}",
            f"type: {file_type}",
            f"size: {stat_info.st_size} bytes ({format_bytes(stat_info.st_size)})",
            f"created: {created}",
            f"modified: {modified}",
            f"accessed: {accessed}",
            f"mode: {oct(mode)[2:]}",
        ]
        
        return "\n".join(lines)


stat_tool = StatTool()
