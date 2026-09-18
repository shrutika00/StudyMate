"""
Safe Python code executor for StudyMate Practice Agent exercises.
Executes code in an isolated subprocess with strict timeouts, output limits, and syntax checks.
"""
import sys
import subprocess
import tempfile
import os
from typing import Dict, Any


def execute_code_safely(code: str, timeout_seconds: int = 5) -> Dict[str, Any]:
    """
    Safely executes student submitted Python code in an isolated subprocess.
    Returns:
        {
            "success": bool,
            "stdout": str,
            "stderr": str,
            "exit_code": int,
            "error": str | None
        }
    """
    if not code or not code.strip():
        return {
            "success": False,
            "stdout": "",
            "stderr": "No code provided to execute.",
            "exit_code": -1,
            "error": "Empty code"
        }

    # Deterministic syntax pre-check
    try:
        compile(code, "<student_solution>", "exec")
    except SyntaxError as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"SyntaxError at line {e.lineno}: {e.msg}",
            "exit_code": 1,
            "error": f"SyntaxError: {e.msg}"
        }

    # Write code to a temporary file
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_file = f.name

        # Execute using the current python executable in an isolated process
        proc = subprocess.run(
            [sys.executable, "-I", temp_file],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        stdout = proc.stdout[:10000] if proc.stdout else ""
        stderr = proc.stderr[:10000] if proc.stderr else ""

        return {
            "success": proc.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode,
            "error": stderr if proc.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout_seconds} seconds (possible infinite loop).",
            "exit_code": -2,
            "error": "Execution timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution failed: {str(e)}",
            "exit_code": -3,
            "error": str(e)
        }
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
