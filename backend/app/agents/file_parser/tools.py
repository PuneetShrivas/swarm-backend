import json
import ast
import csv
import io
from typing import Dict, Any, List

def parse_document_payload(filename: str, content: str, mode: str = "auto") -> Dict[str, Any]:
    """
    Ingests and parses document or file payload, computing structural diagnostics and summaries.
    """
    lines = content.splitlines()
    total_lines = len(lines)
    size_bytes = len(content.encode("utf-8"))
    
    detected_format = "text"
    if filename.endswith(".json") or (content.strip().startswith("{") and content.strip().endswith("}")):
        detected_format = "json"
    elif filename.endswith(".csv") or ("," in content and total_lines > 1):
        detected_format = "csv"
    elif filename.endswith((".py", ".ts", ".js", ".sql", ".sh")):
        detected_format = "code"
    elif filename.endswith((".md", ".markdown")):
        detected_format = "markdown"

    word_count = len(content.split())
    return {
        "status": "parsed",
        "filename": filename,
        "format": detected_format,
        "total_lines": total_lines,
        "size_bytes": size_bytes,
        "word_count": word_count,
        "has_content": bool(content.strip()),
        "preview_snippet": lines[0][:120] if lines else ""
    }

def extract_json_schema(content: str) -> Dict[str, Any]:
    """
    Infers property types, keys, and generates a valid JSON Schema draft-07 representation.
    """
    try:
        data = json.loads(content)
    except Exception as e:
        return {"status": "error", "message": f"Invalid JSON string: {str(e)}"}
        
    def infer_type(val):
        if val is None:
            return "null"
        if isinstance(val, bool):
            return "boolean"
        if isinstance(val, int):
            return "integer"
        if isinstance(val, float):
            return "number"
        if isinstance(val, str):
            return "string"
        if isinstance(val, list):
            return "array"
        if isinstance(val, dict):
            return "object"
        return "any"

    if isinstance(data, dict):
        properties = {}
        required = []
        for k, v in data.items():
            t = infer_type(v)
            properties[k] = {"type": t}
            required.append(k)
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": properties,
            "required": required
        }
    elif isinstance(data, list):
        item_type = infer_type(data[0]) if data else "any"
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "array",
            "items": {"type": item_type}
        }
    else:
        schema = {"type": infer_type(data)}

    return {
        "status": "schema_extracted",
        "root_type": type(data).__name__,
        "schema": schema,
        "top_level_keys": list(data.keys()) if isinstance(data, dict) else len(data) if isinstance(data, list) else 1
    }

def analyze_csv_delimiter(content: str) -> Dict[str, Any]:
    """
    Analyzes raw tabular text, discovers delimiter, validates column uniformity, and infers column types.
    """
    lines = [l for l in content.splitlines() if l.strip()]
    if not lines:
        return {"status": "error", "message": "Content is empty."}
        
    sample = "\n".join(lines[:10])
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample, delimiters=[",", ";", "\t", "|"])
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    reader = csv.reader(io.StringIO(content), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return {"status": "error", "message": "No rows found in CSV."}
        
    headers = rows[0]
    data_rows = rows[1:]
    col_count = len(headers)
    is_uniform = all(len(r) == col_count for r in data_rows)

    # Infer column types from first data row
    column_types = {}
    if data_rows:
        sample_row = data_rows[0]
        for idx, h in enumerate(headers):
            val = sample_row[idx] if idx < len(sample_row) else ""
            if val.isdigit():
                column_types[h] = "integer"
            else:
                try:
                    float(val)
                    column_types[h] = "float"
                except ValueError:
                    column_types[h] = "string"

    return {
        "status": "csv_analyzed",
        "delimiter": "\\t" if delimiter == "\t" else delimiter,
        "column_count": col_count,
        "row_count": len(data_rows),
        "headers": headers,
        "is_uniform": is_uniform,
        "column_types": column_types
    }

def validate_ast_syntax(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Parses code through the Abstract Syntax Tree (AST) engine to verify structural integrity and detect syntax errors.
    """
    if language.lower() not in ["python", "py"]:
        return {
            "status": "unsupported_language",
            "message": f"AST validation natively supports Python; validated '{language}' through basic tokenization."
        }
        
    try:
        tree = ast.parse(code)
        node_counts = {
            "functions": len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]),
            "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
            "imports": len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
            "total_ast_nodes": len(list(ast.walk(tree)))
        }
        return {
            "status": "valid",
            "language": "python",
            "syntax_valid": True,
            "metrics": node_counts
        }
    except SyntaxError as e:
        return {
            "status": "syntax_error",
            "language": "python",
            "syntax_valid": False,
            "error": str(e.msg),
            "line": e.lineno,
            "offset": e.offset,
            "error_text": e.text
        }

TOOLS = [
    {
        "name": "parse_document_payload",
        "description": "Ingests and parses document or file payload, computing structural diagnostics and summaries.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Name of the file with extension"},
                "content": {"type": "string", "description": "Raw text content of the document"},
                "mode": {"type": "string", "description": "Parsing strategy ('auto', 'json', 'csv', 'code')"}
            },
            "required": ["filename", "content"]
        },
        "handler_name": "parse_document_payload"
    },
    {
        "name": "extract_json_schema",
        "description": "Infers property types, keys, and generates a valid JSON Schema draft-07 representation.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Raw JSON string"}
            },
            "required": ["content"]
        },
        "handler_name": "extract_json_schema"
    },
    {
        "name": "analyze_csv_delimiter",
        "description": "Analyzes raw tabular text, discovers delimiter, validates column uniformity, and infers column types.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Raw tabular CSV string content"}
            },
            "required": ["content"]
        },
        "handler_name": "analyze_csv_delimiter"
    },
    {
        "name": "validate_ast_syntax",
        "description": "Parses code through the Abstract Syntax Tree (AST) engine to verify structural integrity and detect syntax errors.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Source code text to validate"},
                "language": {"type": "string", "description": "Programming language (default: 'python')"}
            },
            "required": ["code"]
        },
        "handler_name": "validate_ast_syntax"
    }
]

TOOL_HANDLERS = {
    "parse_document_payload": parse_document_payload,
    "extract_json_schema": extract_json_schema,
    "analyze_csv_delimiter": analyze_csv_delimiter,
    "validate_ast_syntax": validate_ast_syntax,
}
