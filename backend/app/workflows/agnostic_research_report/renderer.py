"""
Publication File Generation Agent for Agnostic Research Reports.
Converts [E###] citations into sequential superscript footnotes, and exports publication-grade
Markdown and ReportLab PDF documents with two-pass NumberedCanvas (Page X of Y), running headers/footers,
styled metadata cards, and footnotes tables.
"""

import os
import re
import time
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.pdfgen import canvas

from app.workflows.agnostic_research_report.ledger import AgnosticEvidenceLedger


def format_inline_markdown(text: str) -> str:
    """Escapes XML entities and translates markdown bold/italic/code to ReportLab tags."""
    if not text:
        return ""
    # Escape ampersands not already part of an entity
    t = re.sub(r"&(?!(?:amp|lt|gt|quot|apos|bull);)", "&amp;", text)
    # Convert bold **text** or __text__
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"__(.+?)__", r"<b>\1</b>", t)
    # Convert italic *text*
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", t)
    # Convert backticks `code`
    t = re.sub(r"`(.+?)`", r"<font face='Courier' color='#0284c7'>\1</font>", t)
    return t


class FootnoteTransformer:
    """Transforms [E###] tokens into sequential footnote numbers and footnote dictionaries."""

    @staticmethod
    def transform_citations(text: str, ledger: AgnosticEvidenceLedger) -> Tuple[str, List[Dict[str, Any]]]:
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
                    "source_domain": ev.source_domain or (ev.source_url.split("/")[2] if "://" in ev.source_url else "web"),
                    "source_title": ev.source_title or ev.source_domain,
                    "published": ev.published or ev.as_of or "N/A",
                    "confidence": ev.confidence,
                    "quote": ev.quote or "",
                })
            else:
                footnotes.append({
                    "num": num,
                    "id": tok,
                    "claim": "Claim unverified in evidence ledger",
                    "source_url": "N/A",
                    "source_domain": "N/A",
                    "source_title": "N/A",
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


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas recording total page count and rendering running headers/footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

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
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            header_title = getattr(self, "header_title", "RESEARCH & INTELLIGENCE REPORT")
            self.drawString(54, 750, header_title)
            self.drawRightString(612 - 54, 750, getattr(self, "report_date", time.strftime("%Y-%m-%d")))
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        self.drawString(54, 34, "CONFIDENTIAL & PROPRIETARY — PREPARED VIA AGNOSTIC RESEARCH SWARM")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 34, page_str)
        self.restoreState()


class AgnosticMarkdownRenderer:
    """Builds clean Markdown report files."""

    @staticmethod
    def render(
        subject: str,
        sections_text: List[str],
        footnotes: List[Dict[str, Any]],
        closing_statement: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        lines = []
        lines.append(f"# {subject.upper()}")
        lines.append("")
        if metadata:
            lines.append(f"> **Date**: {metadata.get('date', time.strftime('%Y-%m-%d'))} | **Model**: {metadata.get('model', 'N/A')} | **Provider**: {metadata.get('provider', 'N/A').upper()} | **Evidence Count**: {metadata.get('evidence_count', len(footnotes))}")
            lines.append("")

        for sec in sections_text:
            lines.append(sec.strip())
            lines.append("")

        if footnotes:
            lines.append("## SOURCES & FOOTNOTES")
            lines.append("")
            for fn in footnotes:
                url_display = f"[{fn['source_domain']}]({fn['source_url']})" if fn['source_url'] != "N/A" else "N/A"
                quote_str = f' — *"{fn["quote"]}"*' if fn.get("quote") else ""
                lines.append(f"[{fn['num']}] {fn['claim']} (Source: {url_display}, Date: {fn['published']}){quote_str}")
            lines.append("")

        if closing_statement:
            lines.append(f"*{closing_statement}*")
            lines.append("")

        return "\n".join(lines)


class AgnosticPdfRenderer:
    """Builds publication-grade PDF documents using ReportLab."""

    @staticmethod
    def render(
        subject: str,
        sections_text: List[str],
        footnotes: List[Dict[str, Any]],
        output_path: str,
        closing_statement: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()
        normal = styles["Normal"]
        body_style = ParagraphStyle(
            "AgBody",
            parent=normal,
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=4,
        )
        bullet_style = ParagraphStyle(
            "AgBullet",
            parent=normal,
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#1e293b"),
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=3,
        )
        h1_style = ParagraphStyle(
            "AgH1",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=10,
        )
        h2_style = ParagraphStyle(
            "AgH2",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0369a1"),
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
        )
        h3_style = ParagraphStyle(
            "AgH3",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14.5,
            textColor=colors.HexColor("#334155"),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        )
        meta_label_style = ParagraphStyle("MetaLabel", parent=normal, fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#475569"))
        meta_val_style = ParagraphStyle("MetaVal", parent=normal, fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#0f172a"))

        story = []

        # Title
        story.append(Paragraph(format_inline_markdown(subject.upper()), h1_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10))

        # Metadata table
        if metadata:
            meta_data = [
                [
                    Paragraph("TARGET SUBJECT", meta_label_style), Paragraph(subject, meta_val_style),
                    Paragraph("DATE", meta_label_style), Paragraph(metadata.get("date", time.strftime("%Y-%m-%d")), meta_val_style),
                ],
                [
                    Paragraph("MODEL / PROVIDER", meta_label_style), Paragraph(f"{metadata.get('model', 'N/A')} ({metadata.get('provider', 'N/A').upper()})", meta_val_style),
                    Paragraph("EVIDENCE COLLECTED", meta_label_style), Paragraph(f"{metadata.get('evidence_count', len(footnotes))} facts ({len(footnotes)} cited)", meta_val_style),
                ],
                [
                    Paragraph("TOTAL TOKENS", meta_label_style), Paragraph(f"{metadata.get('total_tokens', 0):,}", meta_val_style),
                    Paragraph("WALL-CLOCK TIME", meta_label_style), Paragraph(f"{metadata.get('duration_seconds', 0.0):.2f}s (Speedup: {metadata.get('concurrency_speedup', '1.0x')})", meta_val_style),
                ]
            ]
            t = Table(meta_data, colWidths=[100, 152, 100, 152])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 14))

        # Sections content
        for sec in sections_text:
            lines = sec.strip().split("\n")
            for line in lines:
                l_strip = line.strip()
                if not l_strip:
                    continue
                if l_strip.startswith("## "):
                    story.append(Paragraph(format_inline_markdown(l_strip[3:].strip()), h2_style))
                elif l_strip.startswith("### "):
                    story.append(Paragraph(format_inline_markdown(l_strip[4:].strip()), h3_style))
                elif l_strip.startswith("- ") or l_strip.startswith("* "):
                    story.append(Paragraph(f"&bull; {format_inline_markdown(l_strip[2:].strip())}", bullet_style))
                else:
                    story.append(Paragraph(format_inline_markdown(l_strip), body_style))
            story.append(Spacer(1, 6))

        # Footnotes / Sources Table
        if footnotes:
            story.append(Spacer(1, 10))
            story.append(Paragraph("SOURCES & CITATIONS", h2_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

            fn_rows = [[
                Paragraph("<b>#</b>", meta_label_style),
                Paragraph("<b>FACT / CLAIM</b>", meta_label_style),
                Paragraph("<b>DOMAIN / URL</b>", meta_label_style),
                Paragraph("<b>DATE</b>", meta_label_style),
                Paragraph("<b>CONF</b>", meta_label_style),
            ]]
            for fn in footnotes:
                domain_val = fn.get("source_domain", "web")
                url_val = fn.get("source_url", "")
                link_html = f'<a href="{url_val}" color="#0284c7"><u>{domain_val}</u></a>' if url_val and url_val != "N/A" else domain_val
                fn_rows.append([
                    Paragraph(f"[{fn['num']}]", meta_val_style),
                    Paragraph(format_inline_markdown(fn["claim"]), meta_val_style),
                    Paragraph(link_html, meta_val_style),
                    Paragraph(str(fn.get("published", "N/A")), meta_val_style),
                    Paragraph(str(fn.get("confidence", "med")).upper(), meta_val_style),
                ])

            fn_table = Table(fn_rows, colWidths=[24, 250, 120, 60, 50])
            fn_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(fn_table)

        # Closing Statement
        if closing_statement:
            story.append(Spacer(1, 14))
            story.append(Paragraph(f"<i>{format_inline_markdown(closing_statement)}</i>", body_style))

        # Build with NumberedCanvas
        def _canvas_factory(*args, **kwargs):
            canv = NumberedCanvas(*args, **kwargs)
            canv.header_title = f"RESEARCH REPORT: {subject.upper()}"
            canv.report_date = metadata.get("date", time.strftime("%Y-%m-%d")) if metadata else time.strftime("%Y-%m-%d")
            return canv

        doc.build(story, canvasmaker=_canvas_factory)
        return output_path
