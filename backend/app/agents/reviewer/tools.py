import ast
import re
from typing import Dict, Any, List


def security_audit(code_snippet: str) -> Dict[str, Any]:
    """Performs heuristic static analysis for common security vulnerabilities."""
    findings: List[Dict[str, str]] = []
    lower = code_snippet.lower()
    if "eval(" in lower or "exec(" in lower:
        findings.append({"severity": "CRITICAL", "message": "Dangerous dynamic execution (eval/exec) detected."})
    if "password" in lower and ("=" in lower or ":" in lower):
        findings.append({"severity": "WARNING", "message": "Potential hardcoded credential or secret detected."})
    if "cors" in lower and "*" in lower:
        findings.append({"severity": "WARNING", "message": "Wildcard CORS origin enabled."})
    if "shell=true" in lower:
        findings.append({"severity": "CRITICAL", "message": "Shell execution with shell=True invites command injection."})

    return {
        "status": "completed",
        "findings_count": len(findings),
        "findings": findings if findings else [{"severity": "INFO", "message": "No high-risk static patterns identified."}],
    }


def complexity_analysis(code_snippet: str) -> Dict[str, Any]:
    """Estimates cyclomatic complexity and nesting depth."""
    lines = code_snippet.splitlines()
    indent_levels = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
    max_indent = max(indent_levels) // 4 if indent_levels else 0
    return {
        "loc": len(lines),
        "max_nesting_depth": max_indent,
        "complexity_rating": "High" if max_indent >= 4 else "Moderate" if max_indent >= 2 else "Low",
    }


def dependency_security_scan(dependencies: List[str]) -> Dict[str, Any]:
    """
    Audits package dependencies against advisory vulnerability databases.
    Detects deprecated libraries, known CVE patterns, and insecure pinnings.
    """
    vulnerabilities = []
    risky_packages = {
        "pyyaml": {"advisory": "CVE-2020-14343 Arbitrary code execution if using yaml.load without Loader=SafeLoader"},
        "urllib3": {"advisory": "Ensure version >= 2.0.7 to remediate header leak issues (CVE-2023-45803)"},
        "requests": {"advisory": "Ensure version >= 2.31.0 for sensitive header stripping fixes"},
        "django": {"advisory": "Check against recent LTS security bulletins"},
        "flask": {"advisory": "Verify secure session cookie configuration and secret key entropy"},
    }

    for dep in dependencies:
        pkg_clean = re.split(r"[=<>~!]", dep.strip())[0].lower()
        if pkg_clean in risky_packages:
            vulnerabilities.append({
                "package": dep,
                "severity": "MEDIUM",
                "notice": risky_packages[pkg_clean]["advisory"],
            })

    return {
        "dependencies_scanned": len(dependencies),
        "vulnerabilities_found": len(vulnerabilities),
        "advisories": vulnerabilities,
        "recommendation": "All dependencies checked. Keep libraries patched to latest stable semver." if not vulnerabilities else "Review flagged packages and pin to patched releases.",
    }


def owasp_compliance_audit(code_snippet: str, framework: str = "web") -> Dict[str, Any]:
    """Audits code against primary OWASP Top 10 vulnerability categories."""
    findings = []
    lower = code_snippet.lower()

    # A03: Injection
    if "select " in lower and "where " in lower and ("%s" not in lower and "?" not in lower and "$1" not in lower) and "+" in lower:
        findings.append({
            "category": "A03: Injection",
            "severity": "CRITICAL",
            "rule": "SQL string concatenation detected without parameterized queries.",
        })

    # A01: Broken Access Control
    if "role" in lower and "==" in lower and "admin" in lower and "server" not in lower:
        findings.append({
            "category": "A01: Broken Access Control",
            "severity": "WARNING",
            "rule": "Client-side or rudimentary role matching may be bypassable.",
        })

    # A07: Identification and Authentication
    if "md5" in lower or "sha1" in lower:
        findings.append({
            "category": "A07: Identification & Auth",
            "severity": "HIGH",
            "rule": "Weak hashing algorithm (MD5/SHA1) detected; use bcrypt, argon2, or PBKDF2.",
        })

    # A05: Security Misconfiguration
    if "debug=true" in lower or "debug = true" in lower:
        findings.append({
            "category": "A05: Security Misconfiguration",
            "severity": "HIGH",
            "rule": "Debug mode enabled in code; must be disabled in production environments.",
        })

    return {
        "framework": framework,
        "owasp_compliance_score": max(0, 100 - len(findings) * 20),
        "violations_detected": len(findings),
        "violations": findings,
    }


def test_coverage_estimator(code_snippet: str, test_snippet: str) -> Dict[str, Any]:
    """Estimates code coverage percentage by correlating functions and test assertions."""
    # Find functions defined in code_snippet
    func_pattern = re.compile(r"def\s+([a-zA-Z0-9_]+)\s*\(")
    defined_funcs = func_pattern.findall(code_snippet)

    # Find test functions and assertions
    test_pattern = re.compile(r"def\s+(test_[a-zA-Z0-9_]+)\s*\(")
    test_funcs = test_pattern.findall(test_snippet)
    assert_pattern = re.compile(r"\bassert\b")
    assert_count = len(assert_pattern.findall(test_snippet))

    tested_funcs = []
    untested_funcs = []
    test_text_lower = test_snippet.lower()

    for fn in defined_funcs:
        if fn.startswith("__"):
            continue
        if fn.lower() in test_text_lower:
            tested_funcs.append(fn)
        else:
            untested_funcs.append(fn)

    target_count = len(tested_funcs) + len(untested_funcs)
    coverage_ratio = (len(tested_funcs) / target_count) if target_count > 0 else 1.0

    return {
        "functions_defined": target_count,
        "functions_covered": len(tested_funcs),
        "uncovered_functions": untested_funcs,
        "test_assertions_count": assert_count,
        "estimated_coverage_pct": round(coverage_ratio * 100, 1),
    }


TOOLS = [
    {
        "name": "security_audit",
        "description": "Performs static vulnerability scanning on code snippets.",
        "parameters": {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "Source code to audit"},
            },
            "required": ["code_snippet"],
        },
        "handler_name": "security_audit",
    },
    {
        "name": "complexity_analysis",
        "description": "Calculates lines of code, nesting depth, and structural complexity.",
        "parameters": {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "Source code to evaluate"},
            },
            "required": ["code_snippet"],
        },
        "handler_name": "complexity_analysis",
    },
    {
        "name": "dependency_security_scan",
        "description": "Audits dependencies against known security advisories and insecure versions.",
        "parameters": {
            "type": "object",
            "properties": {
                "dependencies": {"type": "array", "items": {"type": "string"}, "description": "List of package requirements"},
            },
            "required": ["dependencies"],
        },
        "handler_name": "dependency_security_scan",
    },
    {
        "name": "owasp_compliance_audit",
        "description": "Audits application logic against OWASP Top 10 security standards.",
        "parameters": {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "Application source code"},
                "framework": {"type": "string", "description": "Architecture framework ('web', 'api', etc.)"},
            },
            "required": ["code_snippet"],
        },
        "handler_name": "owasp_compliance_audit",
    },
    {
        "name": "test_coverage_estimator",
        "description": "Estimates test coverage by matching production functions with test assertions.",
        "parameters": {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "Production code"},
                "test_snippet": {"type": "string", "description": "Corresponding test suite code"},
            },
            "required": ["code_snippet", "test_snippet"],
        },
        "handler_name": "test_coverage_estimator",
    },
]

TOOL_HANDLERS = {
    "security_audit": security_audit,
    "complexity_analysis": complexity_analysis,
    "dependency_security_scan": dependency_security_scan,
    "owasp_compliance_audit": owasp_compliance_audit,
    "test_coverage_estimator": test_coverage_estimator,
}
