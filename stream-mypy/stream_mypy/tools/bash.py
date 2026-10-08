"""Bash tool for running shell commands"""
import os
import subprocess
import platform
import shutil
from typing import Dict, Any
from stream_mypy.types import Tool


MAX_LINES = 2000
MAX_BYTES = 50 * 1024


def find_bash() -> str:
    """Find bash executable, preferring Git Bash on Windows"""
    if platform.system() != "Windows":
        return "bash"
    
    candidates = [
        os.path.expandvars(r"%ProgramFiles%\Git\bin\bash.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Git\bin\bash.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin\bash.exe"),
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    
    # Look in PATH, skipping System32
    bash_path = shutil.which("bash")
    if bash_path and "system32" not in bash_path.lower():
        return bash_path
    
    return "bash"


def truncate_tail(text: str, max_lines: int = MAX_LINES, max_bytes: int = MAX_BYTES) -> str:
    """Keep the end of output and indicate what was truncated"""
    lines = text.split("\n")
    kept = lines[-max_lines:] if len(lines) > max_lines else lines
    
    kept_text = "\n".join(kept)
    while len(kept) > 1 and len(kept_text.encode()) > max_bytes:
        kept = kept[1:]
        kept_text = "\n".join(kept)
    
    result = kept_text
    if len(result.encode()) > max_bytes:
        result = result.encode()[-max_bytes:].decode(errors="ignore")
    
    if len(kept) == len(lines) and len(result) == len(text):
        return text
    
    return f"[truncated: showing the last {len(kept)} of {len(lines)} lines]\n{result}"


async def run_bash(command: str, timeout_ms: int) -> str:
    """Run a bash command and return output"""
    try:
        bash_exe = find_bash()
        result = subprocess.run(
            [bash_exe, "-c", command],
            capture_output=True,
            text=True,
            timeout=timeout_ms / 1000,
            cwd=os.getcwd(),
        )
        out = result.stdout + result.stderr
        return f"{out}\n[exit code: {result.returncode}]"
    except subprocess.TimeoutExpired:
        return f"\n[timed out after {timeout_ms / 1000}s]"
    except Exception as e:
        return f"failed to start bash: {str(e)}"


class BashTool(Tool):
    """Tool for running bash commands"""
    
    def __init__(self):
        super().__init__(
            name="bash",
            description="Run a bash command in the current folder. Returns stdout, stderr and the exit code.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to run",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds (default 30)",
                    },
                },
                "required": ["command"],
            },
        )
    
    async def execute(self, args: Dict[str, Any]) -> str:
        timeout_seconds = args.get("timeout", 30)
        if isinstance(timeout_seconds, (int, float)):
            timeout_ms = int(timeout_seconds * 1000)
        else:
            timeout_ms = 30000
        
        output = await run_bash(str(args["command"]), timeout_ms)
        return truncate_tail(output)


bash_tool = BashTool()
