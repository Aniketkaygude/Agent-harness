"""Read file tool"""
import os
from typing import Dict, Any
from stream_mypy.types import Tool


class ReadTool(Tool):
    """Tool for reading files"""
    
    def __init__(self):
        super().__init__(
            name="read",
            description="Read a text file and returns its contents",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, relative to the current folder",
                    },
                },
                "required": ["path"],
            },
        )
    
    async def execute(self, args: Dict[str, Any]) -> str:
        file_path = os.path.join(os.getcwd(), str(args["path"]))
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


read_tool = ReadTool()
