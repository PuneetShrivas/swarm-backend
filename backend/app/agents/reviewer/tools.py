from typing import Dict, Any, List

def security_audit(code_snippet: str) -> Dict[str, Any]:
    """
    Performs heuristic static analysis for common security vulnerabilities.
    """
    findings: List[Dict[str, str]] = []
    lower = code_snippet.lower()
    if "eval(" in lower or "exec(" in lower:
        findings.append({"severity": "CRITICAL", "message": "Dangerous dynamic execution (eval/exec) detected."})
    if "password" in lower and ("=" in lower or ":" in lower):
        findings.append({"severity": "WARNING", "message": "Potential hardcoded credential or secret detected."})
    if "cors" in lower and "*" in lower:
        findings.append({"severity": "WARNING", "message": "Wildcard CORS origin enabled."})

    return {
        "status": "completed",
        "findings_count": len(findings),
        "findings": findings if findings else [{"severity": "INFO", "message": "No high-risk static patterns identified."}]
    }

def complexity_analysis(code_snippet: str) -> Dict[str, Any]:
    """
    Estimates cyclomatic complexity and nesting depth.
    """
    lines = code_snippet.splitlines()
    indent_levels = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
    max_indent = max(indent_levels) // 4 if indent_levels else 0
    return {
        "loc": len(lines),
        "max_nesting_depth": max_indent,
        "complexity_rating": "High" if max_indent >= 4 else "Moderate" if max_indent >= 2 else "Low"
    }

TOOLS = [
    {
        "name": "security_audit",
        "description": "Performs static vulnerability scanning on code snippets.",
        "parameters": {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "Source code to audit"}
            },
            "required": ["code_snippet"]
        },
        "handler_name": "security_audit"
    },
    {
        "name": "complexity_analysis",
        "description": "Calculates lines of code, nesting depth, and structural complexity.",
        "parameters": {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "Source code to evaluate"}
            },
            "required": ["code_snippet"]
        },
        "handler_name": "complexity_analysis"
    }
]

TOOL_HANDLERS = {
    "security_audit": security_audit,
    "complexity_analysis": complexity_analysis,
}
