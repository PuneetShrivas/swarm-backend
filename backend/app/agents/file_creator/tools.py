import json
from typing import Dict, Any

def generate_file_artifact(filename: str, content: str, file_type: str = "text/plain", description: str = "") -> Dict[str, Any]:
    """
    Constructs a structured downloadable file artifact record.
    
    Args:
        filename: Target name for the file (e.g. 'report.md', 'script.py', 'dataset.csv').
        content: Raw content string of the file.
        file_type: MIME type or extension identifier.
        description: Human-readable description of the file purpose.
    """
    size_bytes = len(content.encode("utf-8"))
    return {
        "status": "created",
        "filename": filename,
        "file_type": file_type,
        "size_bytes": size_bytes,
        "description": description or f"Generated {filename}",
        "downloadable": True,
        "content": content
    }
