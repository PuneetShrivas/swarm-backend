import json
import ast
import csv
import io
import base64
import re
from typing import Dict, Any, List, Optional

# Binary document ingestion libraries
from pypdf import PdfReader
from pptx import Presentation
from docx import Document
from openpyxl import load_workbook

# RAG Knowledge Store
from app.rag.store import rag_store, chunk_text, tokenize


def decode_content_to_bytes(content: Any) -> Optional[bytes]:
    """
    Decodes content that may be raw bytes, a base64 string, a data URI, or utf-8 text.
    Handles padding errors, whitespace, and URL-encoding safely.
    """
    if content is None:
        return None
    if isinstance(content, bytes):
        return content
    if not isinstance(content, str) or not content.strip():
        return b""

    clean_str = content.strip()

    # 1. Strip data URI prefix if present (e.g. data:application/pdf;base64,...)
    if clean_str.startswith("data:"):
        parts = clean_str.split(",", 1)
        if len(parts) == 2:
            clean_str = parts[1].strip()

    # 2. Normalize whitespace, newlines, and space characters (+ encoded as space in URLs)
    clean_str = clean_str.replace("\r", "").replace("\n", "").replace(" ", "+")

    # 3. Fix base64 padding if needed
    missing_padding = len(clean_str) % 4
    if missing_padding:
        clean_str += "=" * (4 - missing_padding)

    # 4. Attempt base64 decode
    try:
        return base64.b64decode(clean_str)
    except Exception:
        # If not valid base64, fall back to utf-8 bytes
        return content.encode("utf-8", errors="replace")


def parse_binary_document(
    filename: str,
    content_base64: str,
    file_type: str = "auto"
) -> Dict[str, Any]:
    """
    Ingests and extracts text, metadata, and structural sections from binary files
    such as PDFs, PowerPoint decks (.pptx), Word documents (.docx), and Excel spreadsheets (.xlsx).
    """
    raw_bytes = decode_content_to_bytes(content_base64)
    if raw_bytes is None or len(raw_bytes) == 0:
        return {"status": "error", "message": "Content is empty or unreadable."}

    fname_lower = filename.lower()
    fmt = file_type.lower()
    if fmt == "auto":
        if fname_lower.endswith(".pdf"):
            fmt = "pdf"
        elif fname_lower.endswith(".pptx") or fname_lower.endswith(".ppt"):
            fmt = "pptx"
        elif fname_lower.endswith(".docx") or fname_lower.endswith(".doc"):
            fmt = "docx"
        elif fname_lower.endswith(".xlsx") or fname_lower.endswith(".xls"):
            fmt = "xlsx"
        elif any(fname_lower.endswith(ext) for ext in [".csv", ".tsv", ".json", ".txt", ".md", ".py", ".sql", ".html", ".xml", ".yaml", ".yml", ".log"]):
            fmt = fname_lower.split(".")[-1]
        else:
            fmt = "binary"

    extracted_text = ""
    sections: List[Dict[str, Any]] = []

    try:
        if fmt == "pdf":
            reader = PdfReader(io.BytesIO(raw_bytes))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    pass
            page_count = len(reader.pages)
            meta = reader.metadata or {}
            page_texts = []
            for p_idx, page in enumerate(reader.pages):
                try:
                    txt = (page.extract_text() or "").strip()
                except Exception as p_err:
                    txt = f"[Page {p_idx + 1} extraction note: {p_err}]"
                if txt:
                    page_texts.append(f"--- Page {p_idx + 1} ---\n{txt}")
                    sections.append({
                        "section_type": "page",
                        "index": p_idx + 1,
                        "title": f"Page {p_idx + 1}",
                        "content": txt
                    })
            extracted_text = "\n\n".join(page_texts)
            if not extracted_text.strip():
                extracted_text = f"[PDF Document: {filename} ({page_count} pages) - Contains no selectable text or is scanned]"
            return {
                "status": "parsed",
                "filename": filename,
                "format": "pdf",
                "page_count": page_count,
                "word_count": len(extracted_text.split()),
                "extracted_text": extracted_text,
                "metadata": {
                    "author": str(meta.get("/Author", "Unknown")),
                    "title": str(meta.get("/Title", filename)),
                    "creator": str(meta.get("/Creator", "PDF Engine")),
                },
                "sections": sections[:10]
            }

        elif fmt == "pptx":
            prs = Presentation(io.BytesIO(raw_bytes))
            slide_count = len(prs.slides)
            slide_texts = []
            for s_idx, slide in enumerate(prs.slides):
                s_title = slide.shapes.title.text if slide.shapes.title else f"Slide {s_idx + 1}"
                body_parts = []
                for shape in slide.shapes:
                    if shape.has_text_frame and shape != slide.shapes.title:
                        for p in shape.text_frame.paragraphs:
                            if p.text.strip():
                                body_parts.append(p.text.strip())
                    elif shape.has_table:
                        for row in shape.table.rows:
                            row_txt = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                            if row_txt:
                                body_parts.append(f"[Table Row]: {row_txt}")
                combined = f"--- Slide {s_idx + 1}: {s_title} ---\n" + "\n".join(f"- {b}" for b in body_parts)
                slide_texts.append(combined)
                sections.append({
                    "section_type": "slide",
                    "index": s_idx + 1,
                    "title": s_title,
                    "bullet_points": body_parts
                })
            extracted_text = "\n\n".join(slide_texts)
            return {
                "status": "parsed",
                "filename": filename,
                "format": "pptx",
                "slide_count": slide_count,
                "word_count": len(extracted_text.split()),
                "extracted_text": extracted_text,
                "sections": sections
            }

        elif fmt == "docx":
            doc = Document(io.BytesIO(raw_bytes))
            doc_lines = []
            for p in doc.paragraphs:
                txt = p.text.strip()
                if txt:
                    doc_lines.append(txt)
                    if p.style.name.startswith("Heading"):
                        sections.append({"section_type": "heading", "title": txt, "style": p.style.name})

            # Extract table contents as clean markdown tables
            table_count = len(doc.tables)
            for t_idx, table in enumerate(doc.tables):
                t_rows = []
                for row in table.rows:
                    t_rows.append([cell.text.strip() for cell in row.cells])
                if t_rows:
                    sections.append({
                        "section_type": "table",
                        "index": t_idx + 1,
                        "rows": t_rows
                    })
                    doc_lines.append(f"\n--- Table {t_idx + 1} ---")
                    doc_lines.append("| " + " | ".join(t_rows[0]) + " |")
                    doc_lines.append("| " + " | ".join(["---"] * len(t_rows[0])) + " |")
                    for row_cells in t_rows[1:]:
                        doc_lines.append("| " + " | ".join(row_cells) + " |")

            extracted_text = "\n\n".join(doc_lines)
            return {
                "status": "parsed",
                "filename": filename,
                "format": "docx",
                "paragraph_count": len(doc.paragraphs),
                "table_count": table_count,
                "word_count": len(extracted_text.split()),
                "extracted_text": extracted_text,
                "sections": sections[:10]
            }

        elif fmt == "xlsx":
            wb = load_workbook(io.BytesIO(raw_bytes), data_only=True)
            sheet_summaries = []
            all_sheets_text = []

            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                rows = list(ws.iter_rows(values_only=True))
                row_count = len(rows)
                col_count = len(rows[0]) if rows else 0

                sheet_lines = [f"=== Sheet: {sheet_name} ({row_count} rows, {col_count} columns) ==="]
                if rows:
                    headers = [str(c) if c is not None else "" for c in rows[0]]
                    sheet_lines.append("| " + " | ".join(headers) + " |")
                    sheet_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                    for r in rows[1:50]:  # preview up to 50 rows per sheet
                        row_vals = [str(v) if v is not None else "" for v in r]
                        if any(row_vals):
                            sheet_lines.append("| " + " | ".join(row_vals) + " |")
                    if len(rows) > 50:
                        sheet_lines.append(f"... [{len(rows) - 50} additional rows in {sheet_name}]")

                sheet_text = "\n".join(sheet_lines)
                all_sheets_text.append(sheet_text)
                sheet_summaries.append({
                    "sheet_name": sheet_name,
                    "row_count": row_count,
                    "col_count": col_count,
                    "headers": [str(c) for c in (rows[0] if rows else []) if c is not None]
                })

            extracted_text = "\n\n".join(all_sheets_text)
            return {
                "status": "parsed",
                "filename": filename,
                "format": "xlsx",
                "sheet_count": len(wb.sheetnames),
                "sheets": sheet_summaries,
                "word_count": len(extracted_text.split()),
                "extracted_text": extracted_text
            }

        elif fmt in ["csv", "tsv", "json", "txt", "md", "py", "sql", "html", "xml", "yaml", "yml", "log"]:
            for enc in ["utf-8", "latin-1", "cp1252"]:
                try:
                    extracted_text = raw_bytes.decode(enc)
                    break
                except Exception:
                    pass
            return {
                "status": "parsed",
                "filename": filename,
                "format": fmt,
                "word_count": len(extracted_text.split()),
                "extracted_text": extracted_text,
                "sections": []
            }

        else:
            # Fallback text decoder
            for enc in ["utf-8", "latin-1", "cp1252"]:
                try:
                    extracted_text = raw_bytes.decode(enc)
                    break
                except Exception:
                    pass
            if extracted_text:
                return {
                    "status": "parsed",
                    "filename": filename,
                    "format": fmt,
                    "word_count": len(extracted_text.split()),
                    "extracted_text": extracted_text,
                    "sections": []
                }
            return {"status": "unsupported_format", "format": fmt, "message": f"Unsupported binary format '{fmt}'."}

    except Exception as e:
        return {"status": "error", "format": fmt, "message": f"Parsing exception: {str(e)}"}


def extract_text_from_artifact(artifact: Dict[str, Any], max_chars: int = 12000) -> str:
    """
    Universally extracts clean, human-readable text from any artifact dictionary
    (PDF, DOCX, PPTX, XLSX, CSV, JSON, code, or plain text).
    Guarantees no raw Base64 or binary gibberish is returned.
    """
    if not artifact or not isinstance(artifact, dict):
        return ""

    # If already parsed and cached, return it directly
    if artifact.get("extracted_text") and str(artifact["extracted_text"]).strip():
        txt = str(artifact["extracted_text"]).strip()
        return txt[:max_chars]

    fname = artifact.get("filename") or artifact.get("name") or "document.txt"
    art_type = (artifact.get("type") or fname.split(".")[-1] or "txt").lower()
    raw_content = artifact.get("content") or ""
    is_binary = bool(artifact.get("is_base64")) or art_type in ["pdf", "pptx", "docx", "xlsx"]

    # If plain text file and not data URI
    if not is_binary and art_type not in ["pdf", "pptx", "docx", "xlsx"] and not raw_content.startswith("data:"):
        # Check if content looks like base64
        if len(raw_content) > 100 and re.match(r"^[A-Za-z0-9+/=\r\n]+$", raw_content) and len(raw_content) % 4 == 0:
            try:
                decoded = base64.b64decode(raw_content.replace("\n", "").replace(" ", "+"))
                if decoded.startswith(b"%PDF") or decoded.startswith(b"PK\x03\x04"):
                    is_binary = True
                else:
                    try:
                        return decoded.decode("utf-8")[:max_chars]
                    except UnicodeDecodeError:
                        is_binary = True
            except Exception:
                pass

        if not is_binary:
            return raw_content[:max_chars]

    # For binary documents (PDF, DOCX, PPTX, XLSX), parse with our engine
    parsed = parse_binary_document(filename=fname, content_base64=raw_content, file_type=art_type)
    if parsed.get("status") == "parsed" and parsed.get("extracted_text"):
        extracted = parsed.get("extracted_text", "").strip()
        if extracted:
            artifact["extracted_text"] = extracted
            return extracted[:max_chars]

    # If parsing returned error or unsupported format, try text decode fallback
    raw_bytes = decode_content_to_bytes(raw_content)
    if raw_bytes:
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                dec = raw_bytes.decode(enc)
                printable_count = sum(1 for c in dec[:500] if c.isprintable() or c in "\r\n\t")
                if printable_count / max(1, len(dec[:500])) > 0.85:
                    return dec[:max_chars]
            except Exception:
                pass

    return f"[Attached Document: {fname} (Format: {art_type.upper()}) - Unable to extract readable text]"


def ingest_and_index_document(
    filename: str,
    content: str = "",
    content_base64: str = "",
    file_type: str = "auto",
    chunk_size: int = 150,
    chunk_overlap: int = 30,
    document_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ingests any document (plain text, code, CSV, JSON, Markdown, or binary Base64 PDF/PPTX/DOCX/XLSX),
    extracts structural text, chunks it into semantic passages, and indexes into the RAG Knowledge Store.
    """
    fname_lower = filename.lower()
    text_to_index = content

    # Universally extract readable text across all types (binary or text)
    art_stub = {
        "filename": filename,
        "name": filename,
        "type": file_type,
        "content": content_base64 or content,
        "is_base64": bool(content_base64),
    }
    extracted = extract_text_from_artifact(art_stub)
    if extracted and not extracted.startswith("[Attached Document:"):
        text_to_index = extracted
    elif content:
        text_to_index = content

    if not text_to_index.strip():
        return {
            "status": "error",
            "filename": filename,
            "message": "Document contains no readable text to index."
        }

    # Ingest and index into RAG store
    result = rag_store.ingest_document(
        filename=filename,
        content=text_to_index,
        metadata={"file_type": file_type, "source": "file_parser"},
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        document_id=document_id
    )
    return result


def query_document_context(
    query: str,
    top_k: int = 3,
    document_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves Top-K relevant contextual chunks from ingested documents using hybrid BM25 lexical
    scoring and vector similarity. Returns citations, relevance scores, and text excerpts.
    """
    chunks = rag_store.query_context(query=query, top_k=top_k, document_id=document_id)
    return {
        "status": "success",
        "query": query,
        "results_count": len(chunks),
        "chunks": chunks,
        "has_context": len(chunks) > 0
    }


def generate_rag_context(
    query: str,
    top_k: int = 3,
    document_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs an enriched prompt context block formatted with source file citations and relevance
    confidence scores, designed for passing into other swarm agents (orchestrator, researcher, coder, synthesizer).
    """
    context_block = rag_store.generate_rag_context_block(query=query, top_k=top_k, document_id=document_id)
    chunks = rag_store.query_context(query=query, top_k=top_k, document_id=document_id)
    return {
        "status": "context_generated",
        "query": query,
        "retrieved_chunks_count": len(chunks),
        "sources": list(set(c["filename"] for c in chunks)),
        "formatted_context_block": context_block
    }


def list_indexed_documents() -> Dict[str, Any]:
    """
    Lists all documents currently indexed in the RAG Knowledge Store along with chunk counts.
    """
    docs = rag_store.list_documents()
    return {
        "status": "success",
        "total_documents": len(docs),
        "documents": docs
    }


def clear_indexed_documents() -> Dict[str, Any]:
    """
    Clears all documents and chunk indexes from the RAG Knowledge Store.
    """
    rag_store.clear()
    return {"status": "cleared", "message": "RAG Knowledge Store index has been cleared."}


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
            "message": f"Syntax AST validation is currently optimized for Python, received '{language}'."
        }

    try:
        tree = ast.parse(code)
        func_defs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        class_defs = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        import_modules = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                import_modules.extend([alias.name for alias in n.names])
            elif isinstance(n, ast.ImportFrom):
                if n.module:
                    import_modules.append(n.module)

        return {
            "status": "valid",
            "syntax_valid": True,
            "functions_count": len(func_defs),
            "classes_count": len(class_defs),
            "functions": func_defs,
            "classes": class_defs,
            "imports": import_modules
        }
    except SyntaxError as e:
        return {
            "status": "syntax_error",
            "syntax_valid": False,
            "error": str(e),
            "line": e.lineno,
            "offset": e.offset,
            "text": e.text
        }


TOOLS = [
    {
        "name": "parse_binary_document",
        "description": "Extracts text, metadata, slide/page count, and sections from binary files (PDF, PPTX, DOCX, XLSX).",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename with extension (e.g. document.pdf, deck.pptx, model.xlsx)"},
                "content_base64": {"type": "string", "description": "Base64-encoded binary content string"},
                "file_type": {"type": "string", "description": "Document format ('pdf', 'pptx', 'docx', 'xlsx', or 'auto')"}
            },
            "required": ["filename", "content_base64"]
        },
        "handler_name": "parse_binary_document"
    },
    {
        "name": "ingest_and_index_document",
        "description": "Ingests a document (text, code, CSV, JSON, Markdown, or binary Base64 PDF/PPTX/DOCX/XLSX), chunks it, and indexes it into the RAG Knowledge Store.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename with extension"},
                "content": {"type": "string", "description": "Plain text content if text document"},
                "content_base64": {"type": "string", "description": "Base64 string if binary document (PDF, PPTX, DOCX, XLSX)"},
                "chunk_size": {"type": "integer", "description": "Target word count per chunk (default: 150)"},
                "chunk_overlap": {"type": "integer", "description": "Word overlap between chunks (default: 30)"}
            },
            "required": ["filename"]
        },
        "handler_name": "ingest_and_index_document"
    },
    {
        "name": "query_document_context",
        "description": "Performs hybrid BM25 and vector similarity retrieval over all indexed document chunks. Returns Top-K relevant passages with confidence scores.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query, question, or key concepts"},
                "top_k": {"type": "integer", "description": "Number of top relevant chunks to retrieve (default: 3)"},
                "document_id": {"type": "string", "description": "Optional document ID to scope retrieval"}
            },
            "required": ["query"]
        },
        "handler_name": "query_document_context"
    },
    {
        "name": "generate_rag_context",
        "description": "Constructs an enriched prompt context block from retrieved document chunks with citations for injection into other swarm agents or chat prompts.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Topic or query to retrieve context for"},
                "top_k": {"type": "integer", "description": "Number of passages to format (default: 3)"},
                "document_id": {"type": "string", "description": "Optional document ID filter"}
            },
            "required": ["query"]
        },
        "handler_name": "generate_rag_context"
    },
    {
        "name": "list_indexed_documents",
        "description": "Lists all documents currently indexed in the RAG Knowledge Store.",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "handler_name": "list_indexed_documents"
    },
    {
        "name": "clear_indexed_documents",
        "description": "Clears all indexed documents and chunks from the RAG Knowledge Store.",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "handler_name": "clear_indexed_documents"
    },
    {
        "name": "parse_document_payload",
        "description": "Ingests and parses document or file payload, computing structural diagnostics and summaries.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Original file name"},
                "content": {"type": "string", "description": "Raw string content of the document"},
                "mode": {"type": "string", "description": "Parsing mode ('auto', 'strict', 'tolerant')"}
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
                "content": {"type": "string", "description": "Raw CSV string payload"}
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
                "language": {"type": "string", "description": "Programming language ('python')"}
            },
            "required": ["code"]
        },
        "handler_name": "validate_ast_syntax"
    }
]

TOOL_HANDLERS = {
    "parse_binary_document": parse_binary_document,
    "ingest_and_index_document": ingest_and_index_document,
    "query_document_context": query_document_context,
    "generate_rag_context": generate_rag_context,
    "list_indexed_documents": list_indexed_documents,
    "clear_indexed_documents": clear_indexed_documents,
    "parse_document_payload": parse_document_payload,
    "extract_json_schema": extract_json_schema,
    "analyze_csv_delimiter": analyze_csv_delimiter,
    "validate_ast_syntax": validate_ast_syntax,
}
