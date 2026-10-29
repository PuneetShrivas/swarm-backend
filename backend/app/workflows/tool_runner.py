import ast
import io
import time
import math
import json
import re
import datetime
import collections
import itertools
import statistics
import random
from contextlib import redirect_stdout, redirect_stderr
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Dict, Any, Tuple, Optional

# Disallowed module names and dangerous operations
DISALLOWED_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "urllib", "requests",
    "http", "pty", "commands", "builtin", "builtins", "posix", "nt",
    "signal", "multiprocessing", "ctypes", "pickle", "shelve", "webbrowser"
}

DISALLOWED_CALLS = {
    "eval", "exec", "__import__", "compile", "breakpoint"
}


class SecurityValidator(ast.NodeVisitor):
    def __init__(self):
        self.errors = []
        self.has_execute_function = False

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_module = alias.name.split(".")[0].lower()
            if base_module in DISALLOWED_MODULES:
                self.errors.append(f"Security violation: Import of '{alias.name}' is strictly prohibited.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_module = node.module.split(".")[0].lower()
            if base_module in DISALLOWED_MODULES:
                self.errors.append(f"Security violation: Import from '{node.module}' is strictly prohibited.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in DISALLOWED_CALLS:
                self.errors.append(f"Security violation: Call to '{node.func.id}()' is strictly prohibited.")
            if node.func.id == "open":
                self.errors.append("Security violation: Direct file filesystem access via open() is prohibited.")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name == "execute":
            self.has_execute_function = True
            # Check argument count: should accept at least 1 arg (e.g. input_data)
            total_args = len(node.args.args)
            if total_args < 1 and not node.args.vararg:
                self.errors.append("Function 'execute' must accept at least 1 argument: (input_data, ...).")
        self.generic_visit(node)


def validate_tool_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    Parses Python code and verifies security rules and the standard execution contract.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Python syntax error at line {e.lineno}: {e.msg}"

    validator = SecurityValidator()
    validator.visit(tree)

    if validator.errors:
        return False, " | ".join(validator.errors)

    if not validator.has_execute_function:
        return False, "Tool code must define an entry point function: def execute(input_data: dict, context: dict) -> dict"

    return True, None


def _build_safe_globals() -> Dict[str, Any]:
    """Builds a restricted execution environment with safe builtins and standard libraries."""
    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
        "dict": dict, "enumerate": enumerate, "filter": filter, "float": float,
        "format": format, "frozenset": frozenset, "hash": hash, "hex": hex,
        "int": int, "isinstance": isinstance, "issubclass": issubclass,
        "iter": iter, "len": len, "list": list, "map": map, "max": max,
        "min": min, "next": next, "oct": oct, "ord": ord, "pow": pow,
        "print": print, "range": range, "repr": repr, "reversed": reversed,
        "round": round, "set": set, "sorted": sorted, "str": str, "sum": sum,
        "tuple": tuple, "type": type, "zip": zip,
        "True": True, "False": False, "None": None,
        "Exception": Exception, "ValueError": ValueError, "TypeError": TypeError,
        "KeyError": KeyError, "IndexError": IndexError
    }

    return {
        "__builtins__": safe_builtins,
        "math": math,
        "json": json,
        "re": re,
        "datetime": datetime,
        "collections": collections,
        "itertools": itertools,
        "statistics": statistics,
        "random": random,
    }


def execute_tool_script(
    code: str,
    input_data: Dict[str, Any],
    context: Dict[str, Any],
    timeout_seconds: float = 5.0
) -> Dict[str, Any]:
    """
    Executes a user-submitted Python script tool in a restricted, sandboxed thread.
    Enforces a strict timeout and captures standard output.
    """
    is_valid, validation_error = validate_tool_code(code)
    if not is_valid:
        return {
            "status": "error",
            "error": f"Validation failed: {validation_error}",
            "result": None,
            "stdout": "",
            "duration_ms": 0.0,
        }

    start_time = time.time()
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    def _target_runner():
        exec_globals = _build_safe_globals()
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(code, exec_globals)
            execute_fn = exec_globals.get("execute")
            if not callable(execute_fn):
                raise ValueError("Entry point 'execute' is not callable.")
            
            # Introspect execute signature to support 1, 2, or 3 arguments dynamically
            import inspect
            sig = inspect.signature(execute_fn)
            param_count = len(sig.parameters)
            if param_count == 1:
                result = execute_fn(dict(input_data or {}))
            elif param_count == 2:
                result = execute_fn(dict(input_data or {}), dict(context or {}))
            else:
                prev_outs = (context or {}).get("previous_outputs", {})
                result = execute_fn(dict(input_data or {}), dict(prev_outs or {}), dict(context or {}))

            if not isinstance(result, dict):
                # Auto-wrap non-dict returns into standard dictionary
                result = {"result": result}
            return result

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_target_runner)
        try:
            result = future.result(timeout=timeout_seconds)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "success",
                "result": result,
                "stdout": stdout_buf.getvalue(),
                "duration_ms": duration_ms,
                "error": None,
            }
        except TimeoutError:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "error",
                "error": f"Script execution timed out after {timeout_seconds} seconds.",
                "result": None,
                "stdout": stdout_buf.getvalue(),
                "duration_ms": duration_ms,
            }
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "error",
                "error": f"Execution error: {str(e)}",
                "result": None,
                "stdout": stdout_buf.getvalue() + "\n" + stderr_buf.getvalue(),
                "duration_ms": duration_ms,
            }
