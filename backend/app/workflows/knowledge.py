import io
import csv
import json
from typing import List, Dict, Any, Optional


def extract_file_content(file_name: str, file_bytes: bytes, content_type: Optional[str] = None) -> str:
    """
    Extracts plain text content from uploaded knowledge documents (.txt, .md, .csv, .json, .py, etc.).
    """
    if not file_bytes:
        return ""

    # Attempt standard encodings
    text = ""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if not text:
        text = str(file_bytes, errors="replace")

    # Clean up carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # If CSV file, format as readable table or sample
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        try:
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
            if rows:
                header = rows[0]
                lines = [" | ".join(header), " | ".join(["---"] * len(header))]
                for row in rows[1:101]:  # limit to first 100 rows
                    lines.append(" | ".join(row))
                if len(rows) > 101:
                    lines.append(f"... [{len(rows) - 101} more rows omitted]")
                return "\n".join(lines)
        except Exception:
            pass

    # If JSON file, format with indentation
    if lower_name.endswith(".json"):
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, indent=2)
        except Exception:
            pass

    return text.strip()


def format_knowledge_context(knowledge_files: List[Dict[str, Any]], max_chars_per_doc: int = 4000) -> str:
    """
    Formats attached knowledge files into an LLM context injection block.
    """
    if not knowledge_files:
        return ""

    blocks = ["\n\n<KNOWLEDGE_BASE>\n### Attached Workflow Knowledge Documents\n"]
    for file_info in knowledge_files:
        fname = file_info.get("file_name", "Document")
        content = file_info.get("content_text", "")
        if not content:
            continue

        if len(content) > max_chars_per_doc:
            content = content[:max_chars_per_doc] + f"\n... [Truncated remaining {len(content) - max_chars_per_doc} characters]"

        blocks.append(f"#### [Document: {fname}]\n```\n{content}\n```\n")

    blocks.append("</KNOWLEDGE_BASE>\n")
    return "\n".join(blocks)
