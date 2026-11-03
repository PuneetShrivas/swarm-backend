"""
Publication Document Renderers.
Converts [E###] citations to styled footnotes, and exports publication-grade
Markdown, DOCX (python-docx), and PDF (reportlab) reports with an automated
Limitations & Low-Confidence Appendix, two-pass NumberedCanvas, running headers/footers,
and styled markdown tables.
"""

import os
import re
import time
from typing import Dict, Any, List, Tuple, Optional
from app.workflows.do_risk_report.models import EntityCard, Evidence
from app.workflows.do_risk_report.ledger import EvidenceLedger


def format_inline_markdown(text: str) -> str:
    """Escapes XML entities and translates markdown bold/italic/code to ReportLab tags."""
    if not text:
        return ""
    # Escape ampersands not already part of an entity
    t = re.sub(r"&(?!(?:amp|lt|gt|quot|apos|bull);)", "&amp;", text)
    # Convert bold **text** or __text__
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"__(.+?)__", r"<b>\1</b>", t)
    # Convert italic *text* (not preceded or followed by *)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", t)
    # Convert backticks `code`
    t = re.sub(r"`(.+?)`", r"<font face='Courier' color='#0284c7'>\1</font>", t)
    return t


class FootnoteTransformer:
    """Transforms [E###] citations into sequential superscript footnote numbers and footnote tables."""

    @staticmethod
    def transform_citations(text: str, ledger: EvidenceLedger) -> Tuple[str, List[Dict[str, Any]]]:
        citation_tokens = re.findall(r"\[(E\d{3,4})\]", text, re.IGNORECASE)
        unique_tokens = []
        for t in citation_tokens:
            t_upper = t.upper()
            if t_upper not in unique_tokens:
                unique_tokens.append(t_upper)

        token_to_num: Dict[str, int] = {tok: i + 1 for i, tok in enumerate(unique_tokens)}
        footnotes: List[Dict[str, Any]] = []

        for tok, num in token_to_num.items():
            ev = ledger.resolve_citation(tok)
            if ev:
                footnotes.append({
                    "num": num,
                    "id": tok,
                    "claim": ev.claim,
                    "source_url": ev.source_url,
                    "source_type": ev.source_type,
                    "published": ev.published or ev.as_of or "N/A",
                    "confidence": ev.confidence,
                    "quote": ev.quote or "",
                })
            else:
                footnotes.append({
                    "num": num,
                    "id": tok,
                    "claim": "Source claim unverified in ledger",
                    "source_url": "N/A",
                    "source_type": "other",
                    "published": "N/A",
                    "confidence": "low",
                    "quote": "",
                })

        def _replace_token(match):
            tok = match.group(1).upper()
            num = token_to_num.get(tok, "")
            return f"[{num}]" if num else match.group(0)

        transformed_text = re.sub(r"\[(E\d{3,4})\]", _replace_token, text, flags=re.IGNORECASE)
        return transformed_text, footnotes


class MarkdownRenderer:
    """Renders complete D&O Risk Underwriting report in GitHub Flavored Markdown."""

    @staticmethod
    def render(
        entity: EntityCard,
        risk_tier: str,
        validated_text: str,
        footnotes: List[Dict[str, Any]],
        ledger: EvidenceLedger,
        report_date: Optional[str] = None,
    ) -> str:
        date_str = report_date or time.strftime("%B %d, %Y")
        lines: List[str] = []

        # Master title: exactly ONE title line containing only company name
        lines.append(f"# {entity.legal_name.upper()}\n")

        # Risk tier badge banner
        lines.append(f"**Overall D&O Risk Tier:** `{risk_tier.upper()}` | **Ticker:** `{entity.ticker}` | **CIK:** `{entity.cik}` | **Date:** `{date_str}`\n")
        lines.append("---\n")

        # Report body
        lines.append(validated_text.strip())
        lines.append("\n\n---\n")

        # Footnote citations section
        lines.append("## FOOTNOTE CITATIONS & SOURCES\n")
        for fn in footnotes:
            quote_snip = f' — *"{fn["quote"]}"*' if fn["quote"] else ""
            lines.append(f"[{fn['num']}] **{fn['id']}** ({fn['source_type'].title()}, Conf: {fn['confidence'].upper()}): [{fn['claim']}]({fn['source_url']}) (Published: {fn['published']}){quote_snip}")

        lines.append("\n\n---\n")

        # Automated Limitations Appendix
        lines.append("## APPENDIX: LIMITATIONS, SINGLE-SOURCE & UNRESOLVED ITEMS\n")
        low_conf = ledger.get_low_confidence_or_unresolved()
        single_src = ledger.get_single_source_high_stakes()

        if not low_conf and not single_src:
            lines.append("- No unresolved, paywalled, or low-confidence items identified. All critical fields verified with primary filing or corroborating sources.\n")
        else:
            if low_conf:
                lines.append("### Unresolved or Low-Confidence Disclosures\n")
                for item in low_conf:
                    lines.append(f"- **{item.section}**: {item.claim} (Status: {item.status}, Source: {item.source_url})")
            if single_src:
                lines.append("\n### Single-Source High-Stakes Litigation / Regulatory Matters\n")
                for item in single_src:
                    lines.append(f"- **{item.section}**: [{item.id}] {item.claim} (Source: {item.source_url})")

        lines.append("\n*Assessment based solely on public information and filing records contained in this report.*")
        return "\n".join(lines)


class DocxRenderer:
    """Generates styled publication DOCX report using python-docx."""

    @staticmethod
    def render(
        filepath: str,
        entity: EntityCard,
        risk_tier: str,
        validated_text: str,
        footnotes: List[Dict[str, Any]],
        ledger: EvidenceLedger,
        report_date: Optional[str] = None,
    ) -> str:
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        date_str = report_date or time.strftime("%B %d, %Y")
        doc = Document()

        # Document margins
        for section in doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)

        # Title
        title_p = doc.add_paragraph()
        run_title = title_p.add_run(entity.legal_name.upper())
        run_title.font.size = Pt(22)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(15, 23, 42)

        # Subtitle banner
        sub_p = doc.add_paragraph()
        run_sub = sub_p.add_run(f"D&O PUBLIC RISK UNDERWRITING REPORT  |  TICKER: {entity.ticker}  |  CIK: {entity.cik}  |  DATE: {date_str}")
        run_sub.font.size = Pt(9.5)
        run_sub.font.color.rgb = RGBColor(100, 116, 139)

        # Risk tier callout
        tier_table = doc.add_table(rows=1, cols=1)
        tier_table.autofit = True
        cell = tier_table.cell(0, 0)
        p_cell = cell.paragraphs[0]
        r1 = p_cell.add_run("OVERALL D&O RISK TIER: ")
        r1.font.bold = True
        r1.font.size = Pt(11)
        r2 = p_cell.add_run(f"{risk_tier.upper()}")
        r2.font.bold = True
        r2.font.size = Pt(13)
        if "severe" in risk_tier.lower() or "high" in risk_tier.lower():
            r2.font.color.rgb = RGBColor(220, 38, 38)
        else:
            r2.font.color.rgb = RGBColor(16, 185, 129)

        doc.add_paragraph()

        # Body parsing
        lines = validated_text.splitlines()
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("#"):
                clean_h = line_str.lstrip("#").strip()
                h_p = doc.add_paragraph()
                h_p.paragraph_format.space_before = Pt(12)
                h_p.paragraph_format.space_after = Pt(4)
                h_run = h_p.add_run(clean_h)
                h_run.font.bold = True
                h_run.font.size = Pt(12)
                h_run.font.color.rgb = RGBColor(30, 41, 59)
            elif line_str.startswith("- ") or line_str.startswith("* "):
                b_p = doc.add_paragraph(style="List Bullet")
                b_p.paragraph_format.space_after = Pt(2)
                b_run = b_p.add_run(line_str[2:].strip())
                b_run.font.size = Pt(9.5)
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(3)
                p_run = p.add_run(line_str)
                p_run.font.size = Pt(9.5)

        # Footnotes Table
        doc.add_paragraph()
        fn_header = doc.add_paragraph()
        fn_header.add_run("FOOTNOTE CITATIONS & EVIDENCE LEDGER").font.bold = True

        fn_table = doc.add_table(rows=1, cols=4)
        hdr_cells = fn_table.rows[0].cells
        hdr_cells[0].text = "#"
        hdr_cells[1].text = "ID"
        hdr_cells[2].text = "Fact / Claim"
        hdr_cells[3].text = "Source & Date"

        for fn in footnotes:
            row_cells = fn_table.add_row().cells
            row_cells[0].text = str(fn["num"])
            row_cells[1].text = fn["id"]
            row_cells[2].text = fn["claim"][:80] + ("..." if len(fn["claim"]) > 80 else "")
            row_cells[3].text = f"{fn['source_type'].title()} ({fn['published']})\n{fn['source_url'][:40]}"

        # Save document
        doc.save(filepath)
        return filepath


from reportlab.pdfgen import canvas
from reportlab.lib import colors


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass ReportLab canvas for calculating total pages and rendering
    running headers (Page 2+) and running footers (all pages).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []
        self.doc_company: str = getattr(self, "doc_company", "TARGET COMPANY")
        self.doc_date: str = getattr(self, "doc_date", "")

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)

        # Running Header (pages 2+)
        if self._pageNumber > 1:
            header_left = f"{self.doc_company} — D&O Underwriting Analysis — {self.doc_date}"
            self.drawString(40, 755, header_left)
            self.drawRightString(572, 755, f"Page {self._pageNumber} of {page_count}")
            self.line(40, 748, 572, 748)

        # Running Footer (all pages)
        footer_left = "CONFIDENTIAL & PROPRIETARY — STRICTLY FOR D&O UNDERWRITING USE"
        footer_right = f"Page {self._pageNumber} of {page_count}"
        self.drawString(40, 25, footer_left)
        self.drawRightString(572, 25, footer_right)
        self.line(40, 36, 572, 36)
        self.restoreState()


def get_numbered_canvas_class(company: str, report_date: str):
    """Factory creating NumberedCanvas subclass with custom company and date metadata."""
    class CustomNumberedCanvas(NumberedCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.doc_company = company
            self.doc_date = report_date
    return CustomNumberedCanvas


class PdfRenderer:
    """Generates styled publication PDF report using ReportLab with NumberedCanvas."""

    @staticmethod
    def render(
        filepath: str,
        entity: EntityCard,
        risk_tier: str,
        validated_text: str,
        footnotes: List[Dict[str, Any]],
        ledger: EvidenceLedger,
        report_date: Optional[str] = None,
    ) -> str:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )

        date_str = report_date or time.strftime("%B %d, %Y")

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=50,
            bottomMargin=50,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#64748b"),
        )
        h1_style = ParagraphStyle(
            "ReportH1",
            parent=styles["Heading1"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=6,
        )
        h2_style = ParagraphStyle(
            "ReportH2",
            parent=styles["Heading2"],
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=4,
        )
        h3_style = ParagraphStyle(
            "ReportH3",
            parent=styles["Heading3"],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=3,
        )
        h4_style = ParagraphStyle(
            "ReportH4",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#334155"),
            fontName="Helvetica-Bold",
            spaceBefore=6,
            spaceAfter=2,
        )
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#334155"),
            spaceAfter=3,
        )
        bullet_style = ParagraphStyle(
            "ReportBullet",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11.5,
            leftIndent=12,
            textColor=colors.HexColor("#334155"),
            spaceAfter=2.5,
        )
        tbl_hdr_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontSize=8.0,
            leading=10.5,
            textColor=colors.HexColor("#ffffff"),
            fontName="Helvetica-Bold",
        )
        tbl_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=8.0,
            leading=10.5,
            textColor=colors.HexColor("#1e293b"),
        )

        style_dict = {
            "ReportH1": h1_style,
            "ReportH2": h2_style,
            "ReportH3": h3_style,
            "ReportH4": h4_style,
            "ReportBody": body_style,
            "ReportBullet": bullet_style,
            "TableHeader": tbl_hdr_style,
            "TableCell": tbl_cell_style,
        }

        elements = []

        # Document Header Banner
        elements.append(Paragraph(entity.legal_name.upper(), title_style))
        elements.append(Paragraph(
            f"D&O PUBLIC RISK UNDERWRITING REPORT  |  TICKER: {entity.ticker}  |  CIK: {entity.cik}  |  DATE: {date_str}",
            subtitle_style
        ))
        elements.append(Spacer(1, 8))

        # Risk Tier Banner Table
        tier_color = "#16a34a" if "contained" in risk_tier.lower() else "#d97706" if "elevated" in risk_tier.lower() else "#dc2626"
        banner_data = [[
            Paragraph(
                f"<b>OVERALL D&O RISK TIER:</b> <font size=11 color='{tier_color}'><b>{risk_tier.upper()}</b></font>  |  "
                f"<b>ANALYSIS DATE:</b> {date_str}  |  <b>LISTING:</b> {entity.exchange}:{entity.ticker}",
                body_style
            )
        ]]
        banner_table = Table(banner_data, colWidths=[532])
        banner_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#2563eb")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(banner_table)
        elements.append(Spacer(1, 10))

        # Parse markdown body into flowables (including tables and headings)
        lines = validated_text.splitlines()
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Markdown table block
            if line.startswith("|") and line.endswith("|") and "|" in line[1:-1]:
                table_raw_rows = []
                while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    row_str = lines[i].strip()
                    is_separator = all(c in "|:- \t" for c in row_str)
                    if not is_separator:
                        raw_cells = [c.strip() for c in row_str[1:-1].split("|")]
                        table_raw_rows.append(raw_cells)
                    i += 1

                if table_raw_rows:
                    max_cols = max(len(r) for r in table_raw_rows)
                    normalized_rows = []
                    for r_idx, r in enumerate(table_raw_rows):
                        padded = r + [""] * (max_cols - len(r))
                        s_use = tbl_hdr_style if r_idx == 0 else tbl_cell_style
                        row_cells = [Paragraph(format_inline_markdown(c), s_use) for c in padded]
                        normalized_rows.append(row_cells)

                    if max_cols == 3:
                        col_widths = [140, 110, 282]
                    elif max_cols == 4:
                        col_widths = [30, 45, 317, 140]
                    elif max_cols == 2:
                        col_widths = [180, 352]
                    else:
                        col_w = 532.0 / max_cols
                        col_widths = [col_w] * max_cols

                    t_table = Table(normalized_rows, colWidths=col_widths, repeatRows=1)
                    t_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#ffffff")),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                        ("TOPPADDING", (0, 0), (-1, 0), 4),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("TOPPADDING", (0, 1), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ]))
                    elements.append(Spacer(1, 4))
                    elements.append(t_table)
                    elements.append(Spacer(1, 6))
                continue

            # Markdown headings
            if line.startswith("#### "):
                elements.append(Paragraph(format_inline_markdown(line[5:].strip()), h4_style))
            elif line.startswith("### "):
                elements.append(Paragraph(format_inline_markdown(line[4:].strip()), h3_style))
            elif line.startswith("## "):
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(format_inline_markdown(line[3:].strip()), h2_style))
            elif line.startswith("# "):
                elements.append(Spacer(1, 6))
                elements.append(Paragraph(format_inline_markdown(line[2:].strip()), h1_style))
            elif line.startswith("- ") or line.startswith("* "):
                clean_b = format_inline_markdown(line[2:].strip())
                elements.append(Paragraph(f"&bull; {clean_b}", bullet_style))
            elif line == "---":
                elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=6, spaceAfter=6))
            else:
                elements.append(Paragraph(format_inline_markdown(line), body_style))

            i += 1

        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        # Footnotes Table
        elements.append(Paragraph("FOOTNOTE CITATIONS & EVIDENCE SOURCES", h2_style))
        elements.append(Spacer(1, 4))

        fn_data = [["#", "ID", "Claim / Disclosure Finding", "Source & Date"]]
        for fn in footnotes[:60]:
            fn_data.append([
                str(fn["num"]),
                fn["id"],
                Paragraph(format_inline_markdown(fn["claim"][:110]), tbl_cell_style),
                Paragraph(format_inline_markdown(f"{fn['source_type'].title()}<br/>{fn['published']}"), subtitle_style),
            ])

        fn_table = Table(fn_data, colWidths=[24, 46, 332, 130], repeatRows=1)
        fn_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#ffffff")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(fn_table)

        canvas_cls = get_numbered_canvas_class(entity.legal_name, date_str)
        doc.build(elements, canvasmaker=canvas_cls)
        return filepath
