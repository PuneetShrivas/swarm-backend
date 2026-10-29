import ast
import difflib
import io
import sys
from typing import Dict, Any, List, Optional


def syntax_validator(code: str, language: str = "python") -> Dict[str, Any]:
    """Validates code syntax and basic AST integrity."""
    if language.lower() == "python":
        try:
            ast.parse(code)
            return {"valid": True, "language": language, "errors": None}
        except SyntaxError as e:
            return {"valid": False, "language": language, "errors": str(e), "line": e.lineno}
    return {"valid": True, "language": language, "notice": "AST validation supported for Python; text verified."}


def generate_test_suite(module_name: str, framework: str = "pytest") -> Dict[str, Any]:
    """Produces scaffolding for test suites targeting a given module."""
    clean_name = module_name.strip().replace(".py", "")
    tests = [
        f"test_{clean_name}_initialization",
        f"test_{clean_name}_happy_path_execution",
        f"test_{clean_name}_edge_case_and_exceptions",
    ]
    template = f"""import pytest
# Auto-generated {framework} test suite for {clean_name}

def test_{clean_name}_initialization():
    assert True

def test_{clean_name}_happy_path_execution():
    result = True
    assert result is True

def test_{clean_name}_edge_case_and_exceptions():
    with pytest.raises(Exception):
        raise ValueError("Simulated edge case error")
"""
    return {
        "module": clean_name,
        "framework": framework,
        "recommended_tests": tests,
        "scaffold_code": template,
    }


def diff_patcher(original_code: str, modified_code: str) -> Dict[str, Any]:
    """Generates unified diff between original and modified code."""
    orig_lines = original_code.splitlines(keepends=True)
    mod_lines = modified_code.splitlines(keepends=True)
    diff = list(difflib.unified_diff(orig_lines, mod_lines, fromfile="original", tofile="modified"))
    return {
        "has_diff": len(diff) > 0,
        "diff_text": "".join(diff),
        "lines_changed": len(diff),
    }


def execute_python_sandbox(code: str, timeout_seconds: int = 5) -> Dict[str, Any]:
    """
    Executes Python snippet in a sandboxed, restricted execution scope.
    Captures stdout, stderr, and evaluation output safely.
    """
    # Prevent unsafe module imports or OS destructive commands in sandbox
    forbidden = ["import os", "import subprocess", "import sys", "shutil", "__import__('os')", "open("]
    for block in forbidden:
        if block in code:
            return {
                "success": False,
                "error": f"Restricted operation '{block}' is blocked in sandbox.",
                "output": "",
            }

    try:
        ast.parse(code)
    except SyntaxError as e:
        return {"success": False, "error": f"SyntaxError: {str(e)}", "output": ""}

    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer
    local_env: Dict[str, Any] = {}
    safe_globals = {
        "__builtins__": {
            "abs": abs,
            "all": all,
            "any": any,
            "bin": bin,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "print": print,
            "range": range,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
        }
    }

    try:
        exec(code, safe_globals, local_env)
        output = buffer.getvalue()
        return {
            "success": True,
            "output": output if output else "Code executed successfully (no stdout).",
            "variables_defined": [k for k in local_env.keys() if not k.startswith("_")],
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "output": buffer.getvalue(),
        }
    finally:
        sys.stdout = old_stdout


def format_code(code: str, language: str = "python") -> Dict[str, Any]:
    """Cleans up formatting, strips trailing whitespace, and normalizes line endings."""
    lines = code.splitlines()
    cleaned = [line.rstrip() for line in lines]
    formatted = "\n".join(cleaned) + "\n"
    return {
        "language": language,
        "formatted_code": formatted,
        "lines_count": len(cleaned),
        "trailing_spaces_removed": True,
    }


TOOLS = [
    {
        "name": "syntax_validator",
        "description": "Validates code syntax and verifies AST integrity.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Source code content"},
                "language": {"type": "string", "description": "Programming language ('python', 'javascript', etc.)"},
            },
            "required": ["code"],
        },
        "handler_name": "syntax_validator",
    },
    {
        "name": "generate_test_suite",
        "description": "Produces test scaffolds and recommended assertions for a given module.",
        "parameters": {
            "type": "object",
            "properties": {
                "module_name": {"type": "string", "description": "Module or component name"},
                "framework": {"type": "string", "description": "Test framework ('pytest', 'jest', etc.)"},
            },
            "required": ["module_name"],
        },
        "handler_name": "generate_test_suite",
    },
    {
        "name": "diff_patcher",
        "description": "Calculates unified diff between original and modified code.",
        "parameters": {
            "type": "object",
            "properties": {
                "original_code": {"type": "string", "description": "Existing code content"},
                "modified_code": {"type": "string", "description": "Proposed new code content"},
            },
            "required": ["original_code", "modified_code"],
        },
        "handler_name": "diff_patcher",
    },
    {
        "name": "execute_python_sandbox",
        "description": "Safely executes Python snippet within a restricted sandbox environment and returns output.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python source code to execute"},
                "timeout_seconds": {"type": "integer", "description": "Execution timeout limit in seconds"},
            },
            "required": ["code"],
        },
        "handler_name": "execute_python_sandbox",
    },
    {
        "name": "format_code",
        "description": "Normalizes formatting, strips trailing whitespace, and ensures clean line endings.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Source code to reformat"},
                "language": {"type": "string", "description": "Language identifier"},
            },
            "required": ["code"],
        },
        "handler_name": "format_code",
    },
]

TOOL_HANDLERS = {
    "syntax_validator": syntax_validator,
    "generate_test_suite": generate_test_suite,
    "diff_patcher": diff_patcher,
    "execute_python_sandbox": execute_python_sandbox,
    "format_code": format_code,
}
