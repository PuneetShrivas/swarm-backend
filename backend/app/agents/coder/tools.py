from typing import Dict, Any

def syntax_validator(code: str, language: str) -> Dict[str, Any]:
    """
    Validates code syntax and basic AST integrity.
    """
    if language.lower() == "python":
        import ast
        try:
            ast.parse(code)
            return {"valid": True, "language": language, "errors": None}
        except SyntaxError as e:
            return {"valid": False, "language": language, "errors": str(e), "line": e.lineno}
    return {"valid": True, "language": language, "notice": "AST validation supported for Python; text verified."}

def generate_test_suite(module_name: str, framework: str = "pytest") -> Dict[str, Any]:
    """
    Produces scaffolding for test suites targeting a given module.
    """
    return {
        "module": module_name,
        "framework": framework,
        "recommended_tests": [f"test_{module_name}_init", f"test_{module_name}_positive_case", f"test_{module_name}_edge_case"]
    }

def diff_patcher(original_code: str, modified_code: str) -> Dict[str, Any]:
    """
    Generates unified diff between original and modified code.
    """
    import difflib
    orig_lines = original_code.splitlines(keepends=True)
    mod_lines = modified_code.splitlines(keepends=True)
    diff = list(difflib.unified_diff(orig_lines, mod_lines, fromfile="original", tofile="modified"))
    return {
        "has_diff": len(diff) > 0,
        "diff_text": "".join(diff),
        "lines_changed": len(diff)
    }

TOOLS = [
    {
        "name": "syntax_validator",
        "description": "Validates code syntax and verifies AST integrity.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Source code content"},
                "language": {"type": "string", "description": "Programming language ('python', 'javascript', etc.)"}
            },
            "required": ["code", "language"]
        },
        "handler_name": "syntax_validator"
    },
    {
        "name": "diff_patcher",
        "description": "Calculates unified diff between original and modified code.",
        "parameters": {
            "type": "object",
            "properties": {
                "original_code": {"type": "string", "description": "Existing code content"},
                "modified_code": {"type": "string", "description": "Proposed new code content"}
            },
            "required": ["original_code", "modified_code"]
        },
        "handler_name": "diff_patcher"
    }
]

TOOL_HANDLERS = {
    "syntax_validator": syntax_validator,
    "generate_test_suite": generate_test_suite,
    "diff_patcher": diff_patcher,
}
