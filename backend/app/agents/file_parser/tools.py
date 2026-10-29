import json
from typing import Dict, Any

def parse_document_payload(filename: str, content: str, mode: str = "auto") -> Dict[str, Any]:
    """
    Ingests and parses document or file payload, computing structural diagnostics.
    
    Args:
        filename: Name of the file (e.g. 'data.csv', 'logs.txt', 'config.json').
        content: String content of the document.
        mode: Parsing strategy ('auto', 'json', 'csv', 'lines', 'code').
    """
    lines = content.splitlines()
    total_lines = len(lines)
    size_bytes = len(content.encode("utf-8"))
    
    # Simple delimiter / format detection
    detected_format = "text"
    if filename.endswith(".json") or (content.strip().startswith("{") and content.strip().endswith("}")):
        detected_format = "json"
    elif filename.endswith(".csv") or ("," in content and total_lines > 1):
        detected_format = "csv"
    elif filename.endswith((".py", ".ts", ".js", ".sql")):
        detected_format = "code"

    return {
        "status": "parsed",
        "filename": filename,
        "format": detected_format,
        "total_lines": total_lines,
        "size_bytes": size_bytes,
        "has_content": bool(content.strip()),
        "preview_snippet": lines[0][:120] if lines else ""
    }
