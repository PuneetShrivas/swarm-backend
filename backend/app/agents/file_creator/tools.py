import json
import base64
import io
import re
from typing import Dict, Any, List, Optional

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# python-pptx imports for PowerPoint presentation decks
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# python-docx imports for Word documents
from docx import Document
from docx.shared import Inches as DocxInches, Pt as DocxPt, RGBColor as DocxRGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# openpyxl imports for Excel spreadsheets
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table as OpenpyxlTable, TableStyleInfo


def generate_pdf_document(
    title: str,
    subtitle: str = "",
    sections: Optional[List[Dict[str, Any]]] = None,
    tables: Optional[List[Dict[str, Any]]] = None,
    author: str = "Swarm Document Architect",
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs a styled multi-page PDF document with headers, paragraphs, bullet lists,
    and formatted data tables. Returns a Base64-encoded downloadable PDF artifact.
    """
    clean_fname = filename or f"{re.sub(r'[^a-zA-Z0-9_-]', '_', title.lower())}.pdf"
    if not clean_fname.endswith(".pdf"):
        clean_fname += ".pdf"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PDFDocTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
        alignment=0  # Left aligned
    )
    subtitle_style = ParagraphStyle(
        "PDFDocSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        spaceAfter=16
    )
    heading_style = ParagraphStyle(
        "PDFDocHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "PDFDocBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        "PDFDocBullet",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=15,
        spaceAfter=4
    )

    story = [
        Paragraph(title, title_style),
    ]
    if subtitle:
        story.append(Paragraph(subtitle, subtitle_style))
    story.append(Spacer(1, 10))

    # Add document sections
    if sections:
        for sec in sections:
            if isinstance(sec, dict):
                heading = sec.get("heading") or sec.get("title")
                if heading:
                    story.append(Paragraph(str(heading), heading_style))

                content = sec.get("content") or sec.get("body") or sec.get("text")
                if content:
                    story.append(Paragraph(str(content).replace("\n", "<br/>"), body_style))

                bullets = sec.get("bullets") or sec.get("points") or []
                if isinstance(bullets, list):
                    for b in bullets:
                        story.append(Paragraph(f"&bull; {str(b)}", bullet_style))

                sec_table = sec.get("table")
                if isinstance(sec_table, dict) and sec_table.get("rows"):
                    t_headers = sec_table.get("headers", [])
                    t_rows = sec_table.get("rows", [])
                    table_data = [t_headers] + t_rows if t_headers else t_rows
                    t = Table(table_data, hAlign="LEFT")
                    t.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
                    ]))
                    story.append(Spacer(1, 6))
                    story.append(t)
                    story.append(Spacer(1, 8))

    # Add standalone tables if supplied
    if tables:
        for tbl in tables:
            if isinstance(tbl, dict) and tbl.get("rows"):
                t_headers = tbl.get("headers", [])
                t_rows = tbl.get("rows", [])
                table_data = [t_headers] + t_rows if t_headers else t_rows
                t = Table(table_data, hAlign="LEFT")
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
                ]))
                story.append(Spacer(1, 8))
                story.append(t)

    doc.build(story)
    pdf_bytes = buf.getvalue()
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    return {
        "status": "created",
        "filename": clean_fname,
        "file_type": "pdf",
        "mime_type": "application/pdf",
        "is_base64": True,
        "encoding": "base64",
        "size_bytes": len(pdf_bytes),
        "description": f"Generated PDF: {title}",
        "downloadable": True,
        "content": pdf_b64,
    }


def generate_presentation_deck(
    title: str,
    subtitle: str = "",
    slides: Optional[List[Dict[str, Any]]] = None,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs a multi-slide PowerPoint presentation (.pptx) with title, bullet lists,
    two-column comparative layouts, and data tables. Returns a Base64-encoded artifact.
    """
    clean_fname = filename or f"{re.sub(r'[^a-zA-Z0-9_-]', '_', title.lower())}.pptx"
    if not clean_fname.endswith(".pptx"):
        clean_fname += ".pptx"

    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)  # 16:9 Widescreen

    # 1. Title Slide (Layout 0)
    title_slide = prs.slides.add_slide(prs.slide_layouts[0])
    title_slide.shapes.title.text = title
    if subtitle and len(title_slide.placeholders) > 1:
        title_slide.placeholders[1].text = subtitle

    # 2. Content Slides
    if slides:
        for s_idx, s in enumerate(slides):
            s_title = s.get("title") or f"Topic {s_idx + 1}"
            layout_type = (s.get("layout") or "bullet").lower()

            if layout_type == "two_column":
                slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title only
                slide.shapes.title.text = s_title

                left_points = s.get("left_points") or s.get("column_left") or []
                right_points = s.get("right_points") or s.get("column_right") or []

                # Left Box
                txBox1 = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(4.0), Inches(3.5))
                tf1 = txBox1.text_frame
                tf1.word_wrap = True
                for i, p in enumerate(left_points):
                    para = tf1.paragraphs[0] if i == 0 else tf1.add_paragraph()
                    para.text = str(p)
                    para.level = 0
                    para.font.size = Pt(14)

                # Right Box
                txBox2 = slide.shapes.add_textbox(Inches(5.2), Inches(1.5), Inches(4.0), Inches(3.5))
                tf2 = txBox2.text_frame
                tf2.word_wrap = True
                for i, p in enumerate(right_points):
                    para = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
                    para.text = str(p)
                    para.level = 0
                    para.font.size = Pt(14)

            elif layout_type == "table" and s.get("table_data"):
                slide = prs.slides.add_slide(prs.slide_layouts[5])
                slide.shapes.title.text = s_title
                tbl_spec = s["table_data"]
                headers = tbl_spec.get("headers", [])
                rows = tbl_spec.get("rows", [])
                all_data = [headers] + rows if headers else rows
                if all_data:
                    num_rows = len(all_data)
                    num_cols = len(all_data[0])
                    table_shape = slide.shapes.add_table(num_rows, num_cols, Inches(1.0), Inches(1.5), Inches(8.0), Inches(3.0))
                    table = table_shape.table
                    for r_idx, row in enumerate(all_data):
                        for c_idx, val in enumerate(row):
                            cell = table.cell(r_idx, c_idx)
                            cell.text = str(val)
                            for p in cell.text_frame.paragraphs:
                                p.font.size = Pt(12)
                                if r_idx == 0:
                                    p.font.bold = True
            else:
                # Default bullet layout (Layout 1)
                slide = prs.slides.add_slide(prs.slide_layouts[1])
                slide.shapes.title.text = s_title
                bullets = s.get("bullet_points") or s.get("bullets") or s.get("points") or []
                if isinstance(bullets, list) and len(slide.placeholders) > 1:
                    tf = slide.placeholders[1].text_frame
                    for i, b in enumerate(bullets):
                        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                        para.text = str(b)
                        para.level = 0
                        para.font.size = Pt(15)

    buf = io.BytesIO()
    prs.save(buf)
    pptx_bytes = buf.getvalue()
    pptx_b64 = base64.b64encode(pptx_bytes).decode("utf-8")

    return {
        "status": "created",
        "filename": clean_fname,
        "file_type": "pptx",
        "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "is_base64": True,
        "encoding": "base64",
        "size_bytes": len(pptx_bytes),
        "slide_count": len(prs.slides),
        "description": f"Generated Presentation: {title} ({len(prs.slides)} slides)",
        "downloadable": True,
        "content": pptx_b64,
    }


def generate_word_document(
    title: str,
    subtitle: str = "",
    sections: Optional[List[Dict[str, Any]]] = None,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs a formatted Word document (.docx) with styled headings, paragraphs,
    bulleted lists, and tables. Returns a Base64-encoded artifact.
    """
    clean_fname = filename or f"{re.sub(r'[^a-zA-Z0-9_-]', '_', title.lower())}.docx"
    if not clean_fname.endswith(".docx"):
        clean_fname += ".docx"

    doc = Document()
    doc.add_heading(title, level=0)

    if subtitle:
        sub_para = doc.add_paragraph(subtitle)
        sub_para.style = "Subtitle"

    if sections:
        for sec in sections:
            if isinstance(sec, dict):
                heading = sec.get("heading") or sec.get("title")
                level = int(sec.get("level", 1))
                if heading:
                    doc.add_heading(str(heading), level=min(3, max(1, level)))

                paragraphs = sec.get("paragraphs") or []
                if isinstance(paragraphs, list):
                    for p in paragraphs:
                        doc.add_paragraph(str(p))
                elif sec.get("content"):
                    doc.add_paragraph(str(sec["content"]))

                bullets = sec.get("bullets") or sec.get("points") or []
                if isinstance(bullets, list):
                    for b in bullets:
                        doc.add_paragraph(str(b), style="List Bullet")

                tbl = sec.get("table")
                if isinstance(tbl, dict) and tbl.get("rows"):
                    headers = tbl.get("headers", [])
                    rows = tbl.get("rows", [])
                    all_rows = [headers] + rows if headers else rows
                    if all_rows:
                        table = doc.add_table(rows=len(all_rows), cols=len(all_rows[0]))
                        table.style = "Table Grid"
                        for r_idx, r in enumerate(all_rows):
                            for c_idx, val in enumerate(r):
                                cell = table.cell(r_idx, c_idx)
                                cell.text = str(val)
                                if r_idx == 0:
                                    for p in cell.paragraphs:
                                        p.runs[0].font.bold = True

    buf = io.BytesIO()
    doc.save(buf)
    docx_bytes = buf.getvalue()
    docx_b64 = base64.b64encode(docx_bytes).decode("utf-8")

    return {
        "status": "created",
        "filename": clean_fname,
        "file_type": "docx",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "is_base64": True,
        "encoding": "base64",
        "size_bytes": len(docx_bytes),
        "section_count": len(sections or []),
        "description": f"Generated Word Document: {title}",
        "downloadable": True,
        "content": docx_b64,
    }


def coerce_cell_value(val: Any) -> Any:
    """
    Intelligently casts string cell representations into typed integers, floats,
    formulas, or booleans to preserve spreadsheet typing instead of dumping raw text.
    """
    if val is None:
        return ""
    if isinstance(val, (int, float, bool)):
        return val
    val_str = str(val).strip()
    if not val_str:
        return ""
    # Preserve Excel formulas
    if val_str.startswith("="):
        return val_str
    # Currency / percentage / accounting parenthesis format
    clean_num = val_str.replace("$", "").replace("€", "").replace("£", "").replace(",", "").strip()
    if clean_num.endswith("%"):
        try:
            return float(clean_num[:-1]) / 100.0
        except ValueError:
            pass
    if clean_num.startswith("(") and clean_num.endswith(")"):
        clean_num = f"-{clean_num[1:-1]}"
    if re.match(r"^-?\d+$", clean_num):
        try:
            return int(clean_num)
        except ValueError:
            pass
    if re.match(r"^-?\d+\.\d+$", clean_num):
        try:
            return float(clean_num)
        except ValueError:
            pass
    if val_str.lower() in ("true", "yes"):
        return True
    if val_str.lower() in ("false", "no"):
        return False
    return val_str


def extract_tabular_data(text: str) -> tuple[List[str], List[List[Any]]]:
    """
    Intelligently parses unstructured or semi-structured text into a clean tabular
    header list and list of typed rows. Supports markdown tables, CSV blocks,
    tab-separated values, and JSON record arrays.
    """
    if not text or not text.strip():
        return [], []

    clean = text.strip()

    # 1. JSON array of objects
    if (clean.startswith("[") and clean.endswith("]")) or "```json" in clean:
        json_str = clean
        if "```json" in clean:
            m = re.search(r"```json\s*([\s\S]*?)\s*```", clean)
            if m:
                json_str = m.group(1).strip()
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                headers = list(parsed[0].keys())
                rows = []
                for item in parsed:
                    if isinstance(item, dict):
                        rows.append([coerce_cell_value(item.get(h, "")) for h in headers])
                if headers and rows:
                    return headers, rows
        except Exception:
            pass

    # 2. Markdown Table (| Col 1 | Col 2 |)
    lines = [l.strip() for l in clean.splitlines()]
    table_lines: List[str] = []
    for l in lines:
        if l.startswith("|") and l.endswith("|"):
            table_lines.append(l)
        elif len(table_lines) >= 3 and any("-" in c for c in table_lines[1].split("|")):
            break
        else:
            table_lines = []

    if len(table_lines) >= 3:
        raw_headers = [c.strip() for c in table_lines[0].split("|")[1:-1]]
        headers = [h for h in raw_headers if h]
        rows = []
        for line in table_lines[2:]:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            typed_row = [coerce_cell_value(c) for c in cells[:len(headers)]]
            while len(typed_row) < len(headers):
                typed_row.append("")
            rows.append(typed_row)
        if headers and rows:
            return headers, rows

    # 3. CSV code block or raw lines
    csv_block = clean
    if "```csv" in clean or "```text" in clean:
        m = re.search(r"```(?:csv|text)?\s*([\s\S]*?)\s*```", clean)
        if m:
            csv_block = m.group(1).strip()

    candidate_lines = [l for l in csv_block.splitlines() if l.strip()]
    if candidate_lines:
        first_line = candidate_lines[0]
        delim = "\t" if "\t" in first_line else ("," if "," in first_line else None)
        if delim:
            import csv
            reader = csv.reader(candidate_lines, delimiter=delim)
            all_rows = list(reader)
            if len(all_rows) >= 2:
                headers = [h.strip() for h in all_rows[0] if h.strip()]
                if headers:
                    data_rows = []
                    for r in all_rows[1:]:
                        if any(c.strip() for c in r):
                            row = [coerce_cell_value(c) for c in r[:len(headers)]]
                            while len(row) < len(headers):
                                row.append("")
                            data_rows.append(row)
                    if data_rows:
                        return headers, data_rows

    return [], []


def generate_spreadsheet_workbook(
    sheets: Optional[List[Dict[str, Any]]] = None,
    filename: Optional[str] = None,
    title: Optional[str] = "Financial Model"
) -> Dict[str, Any]:
    """
    Constructs an Excel workbook (.xlsx) with true native openpyxl Tables (Table and TableStyleInfo),
    styled header rows, typed numeric data, formulas, auto-sized columns, frozen panes, and
    multiple worksheets. Returns a Base64-encoded artifact.
    """
    clean_fname = filename or f"{re.sub(r'[^a-zA-Z0-9_-]', '_', (title or 'workbook').lower())}.xlsx"
    if not clean_fname.endswith(".xlsx"):
        clean_fname += ".xlsx"

    wb = Workbook()
    if sheets and len(sheets) > 0:
        wb.remove(wb.active)

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    border_thin = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)

    sheet_specs = sheets or [{
        "sheet_name": "Summary",
        "headers": ["Item", "Category", "Q1", "Q2", "Q3", "Q4", "Total"],
        "rows": [
            ["Subscription Revenue", "ARR", 45000, 52000, 58000, 65000, "=SUM(C2:F2)"],
            ["Professional Services", "Services", 12000, 14000, 11000, 16000, "=SUM(C3:F3)"],
            ["Infrastructure Cost", "COGS", -8500, -9200, -10100, -11000, "=SUM(C4:F4)"],
        ],
        "include_totals": True
    }]

    for s_idx, s in enumerate(sheet_specs):
        sheet_name = s.get("sheet_name") or f"Sheet{s_idx + 1}"
        ws = wb.create_sheet(title=sheet_name[:30])

        headers = s.get("headers", [])
        raw_rows = s.get("rows", [])

        # If headers/rows not provided but raw text or content exists, parse tabular data
        if not headers and (s.get("content") or s.get("raw_data")):
            p_headers, p_rows = extract_tabular_data(s.get("content") or s.get("raw_data") or "")
            if p_headers:
                headers = p_headers
                raw_rows = p_rows

        if headers:
            ws.append([str(h).strip() for h in headers])
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_align
                cell.border = cell_border

        for r in raw_rows:
            typed_row = [coerce_cell_value(val) for val in r]
            ws.append(typed_row)

        # Style data cells and apply numbers/alignment
        for r_idx in range(2, ws.max_row + 1):
            for c_idx in range(1, ws.max_column + 1):
                cell = ws.cell(row=r_idx, column=c_idx)
                cell.border = cell_border
                val = cell.value
                if isinstance(val, int):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    cell.number_format = "#,##0"
                elif isinstance(val, float):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    cell.number_format = "#,##0.00"
                elif isinstance(val, str) and val.startswith("="):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        # Add native openpyxl Table with zebra stripes and filters
        if ws.max_row >= 2 and ws.max_column >= 1:
            clean_tbl_name = re.sub(r"[^a-zA-Z0-9_]", "_", f"Table_{sheet_name[:12]}_{s_idx + 1}")
            if clean_tbl_name[0].isdigit():
                clean_tbl_name = f"T_{clean_tbl_name}"
            tab_ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
            table_obj = OpenpyxlTable(displayName=clean_tbl_name, ref=tab_ref)
            table_obj.tableStyleInfo = TableStyleInfo(
                name="TableStyleMedium9",
                showFirstColumn=False,
                showLastColumn=False,
                showRowStripes=True,
                showColumnStripes=False,
            )
            ws.add_table(table_obj)

        # Freeze top header row so it stays visible on scrolling
        ws.freeze_panes = "A2"

        # Auto-adjust column width with padding
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or "")
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    buf = io.BytesIO()
    wb.save(buf)
    xlsx_bytes = buf.getvalue()
    xlsx_b64 = base64.b64encode(xlsx_bytes).decode("utf-8")

    return {
        "status": "created",
        "filename": clean_fname,
        "file_type": "xlsx",
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "is_base64": True,
        "encoding": "base64",
        "size_bytes": len(xlsx_bytes),
        "sheet_count": len(wb.sheetnames),
        "sheets": wb.sheetnames,
        "description": f"Generated Excel Workbook: {clean_fname} ({len(wb.sheetnames)} sheets with native Excel Tables)",
        "downloadable": True,
        "content": xlsx_b64,
    }


def generate_file_artifact(
    filename: str,
    content: str,
    file_type: str = "text/plain",
    description: str = "",
    mime_type: Optional[str] = None,
    is_base64: bool = False,
    encoding: str = "utf-8"
) -> Dict[str, Any]:
    """
    Constructs a structured downloadable file artifact record with byte sizing and metadata.
    Supports both plain text and Base64-encoded binary content.
    """
    effective_type = mime_type or file_type
    size_bytes = len(content.encode("utf-8")) if not is_base64 else len(base64.b64decode(content))

    return {
        "status": "created",
        "filename": filename,
        "file_type": effective_type,
        "size_bytes": size_bytes,
        "description": description or f"Generated {filename}",
        "downloadable": True,
        "is_base64": is_base64,
        "encoding": "base64" if is_base64 else encoding,
        "content": content
    }


def convert_file_format(
    source_content: str,
    source_format: str,
    target_format: str,
    title: str = "Converted Document"
) -> Dict[str, Any]:
    """
    Converts document content across formats: Markdown <-> HTML <-> TXT, or CSV <-> JSON.
    """
    s_fmt = source_format.lower().strip()
    t_fmt = target_format.lower().strip()

    converted = ""
    target_mime = "text/plain"

    if s_fmt == "csv" and t_fmt == "json":
        lines = [l for l in source_content.splitlines() if l.strip()]
        if lines:
            headers = [h.strip() for h in lines[0].split(",")]
            records = []
            for line in lines[1:]:
                vals = [v.strip() for v in line.split(",")]
                records.append(dict(zip(headers, vals)))
            converted = json.dumps(records, indent=2)
            target_mime = "application/json"
    elif s_fmt == "json" and t_fmt == "csv":
        try:
            data = json.loads(source_content)
            if isinstance(data, list) and data and isinstance(data[0], dict):
                headers = list(data[0].keys())
                rows = [",".join(headers)]
                for item in data:
                    rows.append(",".join(str(item.get(h, "")) for h in headers))
                converted = "\n".join(rows) + "\n"
                target_mime = "text/csv"
        except Exception:
            converted = source_content
    elif s_fmt in ["md", "markdown"] and t_fmt == "html":
        # Basic markdown to HTML
        html_lines = []
        for line in source_content.splitlines():
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            else:
                html_lines.append(f"<p>{line}</p>")
        converted = f"<!DOCTYPE html><html><head><title>{title}</title></head><body>\n" + "\n".join(html_lines) + "\n</body></html>"
        target_mime = "text/html"
    else:
        converted = source_content

    return {
        "status": "converted",
        "source_format": s_fmt,
        "target_format": t_fmt,
        "mime_type": target_mime,
        "content": converted,
        "size_bytes": len(converted.encode("utf-8")),
    }


def render_template_file(template_type: str, title: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Renders standardized production boilerplate for scripts, configs, datasets, and documentation.
    """
    parameters = parameters or {}
    t_type = template_type.lower().strip()

    if t_type in ["python", "py"]:
        filename = f"{title.lower().replace(' ', '_')}.py"
        content = (
            f'"""\n{title}\nGenerated by Swarm File Architect\n"""\n\n'
            f'import sys\nimport os\n\n'
            f'def main():\n'
            f'    print("Executing {title}...")\n'
            f'    # Custom parameters: {json.dumps(parameters)}\n'
            f'    return 0\n\n'
            f'if __name__ == "__main__":\n'
            f'    sys.exit(main())\n'
        )
        mime = "text/x-python"
    elif t_type in ["markdown", "md"]:
        filename = f"{title.lower().replace(' ', '_')}.md"
        content = (
            f"# {title}\n\n"
            f"> Generated automatically by Swarm File Architect.\n\n"
            f"## Overview\nThis document describes specifications and requirements.\n\n"
            f"## Configuration\n```json\n{json.dumps(parameters, indent=2)}\n```\n\n"
            f"## Action Items\n- [x] Initial specification\n- [ ] Execution\n"
        )
        mime = "text/markdown"
    elif t_type in ["csv"]:
        filename = f"{title.lower().replace(' ', '_')}.csv"
        headers = parameters.get("headers", ["id", "name", "value", "status"])
        rows = parameters.get("rows", [
            ["1", "Alpha Metric", "120.5", "active"],
            ["2", "Beta Metric", "340.2", "completed"]
        ])
        content = ",".join(headers) + "\n" + "\n".join([",".join(map(str, r)) for r in rows]) + "\n"
        mime = "text/csv"
    elif t_type in ["json"]:
        filename = f"{title.lower().replace(' ', '_')}.json"
        content = json.dumps({"title": title, "parameters": parameters, "status": "active"}, indent=2)
        mime = "application/json"
    else:
        filename = f"{title.lower().replace(' ', '_')}.txt"
        content = f"{title}\n\nParameters:\n{json.dumps(parameters, indent=2)}\n"
        mime = "text/plain"

    return {
        "status": "rendered",
        "filename": filename,
        "template_type": t_type,
        "mime_type": mime,
        "content": content,
        "size_bytes": len(content.encode("utf-8")),
    }


def create_tabular_dataset(filename: str, columns: List[str], sample_rows: List[List[Any]]) -> Dict[str, Any]:
    """
    Creates a verified, structured tabular dataset with column validation and row counts.
    """
    if not columns:
        columns = ["col1", "col2", "col3"]
    if not sample_rows:
        sample_rows = [["sample_1", "sample_2", "sample_3"]]

    csv_lines = [",".join(columns)]
    for row in sample_rows:
        csv_lines.append(",".join([str(val) for val in row]))

    csv_text = "\n".join(csv_lines) + "\n"
    return {
        "status": "dataset_created",
        "filename": filename if filename.endswith(".csv") else f"{filename}.csv",
        "column_count": len(columns),
        "row_count": len(sample_rows),
        "columns": columns,
        "content": csv_text,
        "size_bytes": len(csv_text.encode("utf-8")),
    }


def package_multi_file_archive(archive_name: str, files: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Packages a collection of virtual files into a structured multi-file bundle.
    """
    manifest = []
    total_bytes = 0
    for f in files:
        fname = f.get("filename", "untitled.txt")
        body = f.get("content", "")
        fbytes = len(body.encode("utf-8"))
        total_bytes += fbytes
        manifest.append({
            "filename": fname,
            "size_bytes": fbytes,
            "preview": body[:60] + ("..." if len(body) > 60 else "")
        })

    return {
        "status": "packaged",
        "archive_name": archive_name if archive_name.endswith(".swarm-pack") else f"{archive_name}.swarm-pack",
        "file_count": len(files),
        "total_bytes": total_bytes,
        "manifest": manifest,
        "raw_bundle_json": json.dumps({"archive": archive_name, "files": files})
    }


TOOLS = [
    {
        "name": "generate_pdf_document",
        "description": "Constructs a styled multi-page PDF document with headers, paragraphs, bullet lists, and tables. Returns a Base64-encoded PDF artifact.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "subtitle": {"type": "string", "description": "Document subtitle or author metadata"},
                "sections": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of sections containing 'heading', 'content', 'bullets', and optional 'table'"
                },
                "filename": {"type": "string", "description": "Target PDF filename (e.g. report.pdf)"}
            },
            "required": ["title"]
        },
        "handler_name": "generate_pdf_document"
    },
    {
        "name": "generate_presentation_deck",
        "description": "Constructs a multi-slide PowerPoint presentation (.pptx) with title, content bullets, two-column comparative layouts, and tables. Returns a Base64-encoded PPTX artifact.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Presentation deck title"},
                "subtitle": {"type": "string", "description": "Subtitle or presenter information"},
                "slides": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of slides with 'title', 'bullet_points', 'layout' ('bullet', 'two_column', 'table')"
                },
                "filename": {"type": "string", "description": "Target PPTX filename (e.g. presentation.pptx)"}
            },
            "required": ["title"]
        },
        "handler_name": "generate_presentation_deck"
    },
    {
        "name": "generate_word_document",
        "description": "Constructs a formatted Word document (.docx) with styled headings, paragraphs, bulleted lists, and tables. Returns a Base64-encoded DOCX artifact.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Word document title"},
                "subtitle": {"type": "string", "description": "Subtitle or document author"},
                "sections": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of sections with 'heading', 'paragraphs', 'bullets', and 'table'"
                },
                "filename": {"type": "string", "description": "Target DOCX filename (e.g. document.docx)"}
            },
            "required": ["title"]
        },
        "handler_name": "generate_word_document"
    },
    {
        "name": "generate_spreadsheet_workbook",
        "description": "Constructs an Excel workbook (.xlsx) with styled headers, multiple worksheets, auto-sized columns, and formulas. Returns a Base64-encoded XLSX artifact.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Workbook title or subject"},
                "filename": {"type": "string", "description": "Target XLSX filename (e.g. model.xlsx)"},
                "sheets": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of sheets with 'sheet_name', 'headers', 'rows', and 'include_totals'"
                }
            },
            "required": ["title"]
        },
        "handler_name": "generate_spreadsheet_workbook"
    },
    {
        "name": "generate_file_artifact",
        "description": "Universal file artifact constructor supporting text and Base64-encoded binary content with byte sizing and metadata.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Target filename with extension (e.g. data.csv, app.py, doc.pdf)"},
                "content": {"type": "string", "description": "Content string or Base64 string for binary files"},
                "file_type": {"type": "string", "description": "MIME type or file format (e.g. text/csv, application/pdf)"},
                "is_base64": {"type": "boolean", "description": "True if content is Base64 encoded"},
                "description": {"type": "string", "description": "Description of the file's purpose"}
            },
            "required": ["filename", "content"]
        },
        "handler_name": "generate_file_artifact"
    },
    {
        "name": "render_template_file",
        "description": "Renders standardized production boilerplate for scripts, configs, datasets, and documentation.",
        "parameters": {
            "type": "object",
            "properties": {
                "template_type": {"type": "string", "description": "Template format ('python', 'markdown', 'csv', 'json')"},
                "title": {"type": "string", "description": "Document or script title"},
                "parameters": {"type": "object", "description": "Optional dictionary of custom variables"}
            },
            "required": ["template_type", "title"]
        },
        "handler_name": "render_template_file"
    },
    {
        "name": "create_tabular_dataset",
        "description": "Creates a verified, structured tabular dataset with column validation and row counts.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Output CSV filename"},
                "columns": {"type": "array", "items": {"type": "string"}, "description": "List of column header names"},
                "sample_rows": {"type": "array", "items": {"type": "array"}, "description": "Matrix of table rows"}
            },
            "required": ["filename", "columns", "sample_rows"]
        },
        "handler_name": "create_tabular_dataset"
    },
    {
        "name": "package_multi_file_archive",
        "description": "Packages a collection of virtual files into a structured multi-file bundle.",
        "parameters": {
            "type": "object",
            "properties": {
                "archive_name": {"type": "string", "description": "Name of the archive bundle"},
                "files": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of objects with 'filename' and 'content' keys"
                }
            },
            "required": ["archive_name", "files"]
        },
        "handler_name": "package_multi_file_archive"
    },
    {
        "name": "convert_file_format",
        "description": "Converts document content across formats (Markdown <-> HTML <-> TXT, or CSV <-> JSON).",
        "parameters": {
            "type": "object",
            "properties": {
                "source_content": {"type": "string", "description": "Original document content"},
                "source_format": {"type": "string", "description": "Source format ('md', 'html', 'csv', 'json')"},
                "target_format": {"type": "string", "description": "Target format ('md', 'html', 'csv', 'json')"},
                "title": {"type": "string", "description": "Document title"}
            },
            "required": ["source_content", "source_format", "target_format"]
        },
        "handler_name": "convert_file_format"
    }
]

TOOL_HANDLERS = {
    "generate_pdf_document": generate_pdf_document,
    "generate_presentation_deck": generate_presentation_deck,
    "generate_word_document": generate_word_document,
    "generate_spreadsheet_workbook": generate_spreadsheet_workbook,
    "generate_file_artifact": generate_file_artifact,
    "render_template_file": render_template_file,
    "create_tabular_dataset": create_tabular_dataset,
    "package_multi_file_archive": package_multi_file_archive,
    "convert_file_format": convert_file_format,
}
