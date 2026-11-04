"""
Executive PDF Document Compiler for Azure AI Foundry Pipeline using ReportLab.
"""

import os
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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


class NumberedCanvas(canvas.Canvas):
    """Custom canvas that performs two passes to dynamically compute total pages."""
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

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "CONFIDENTIAL // D&O RISK UNDERWRITING ASSESSMENT")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 750, 558, 750)

        # Running footer
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, "Generated via Azure AI Foundry Multi-Agent Pipeline (Researcher → Validator → Generator)")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)
        self.restoreState()


class ReportPdfCompiler:
    """Renders formatted executive D&O Risk Reports into publication-grade PDF documents."""

    def __init__(self, output_path: str):
        self.output_path = output_path
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    def compile(
        self,
        report_text: str,
        title: str = "D&O Risk Underwriting Assessment",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compiles the markdown/text report into a formatted PDF document.
        Returns metadata containing output path, file size, and checksum.
        """
        metadata = metadata or {}
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()

        # Custom typography
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#2563eb"),
            spaceAfter=14,
        )
        h1_style = ParagraphStyle(
            "Heading1_Custom",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True,
        )
        h2_style = ParagraphStyle(
            "Heading2_Custom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        )
        body_style = ParagraphStyle(
            "Body_Custom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )
        bullet_style = ParagraphStyle(
            "Bullet_Custom",
            parent=body_style,
            leftIndent=14,
            firstLineIndent=-10,
            spaceAfter=4,
        )
        meta_label_style = ParagraphStyle(
            "MetaLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#475569"),
        )
        meta_val_style = ParagraphStyle(
            "MetaValue",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0f172a"),
        )

        story = []

        # Document Header Banner
        story.append(Paragraph(title.upper(), title_style))
        gen_time = metadata.get("completed_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"AUTONOMOUS PIPELINE REPORT &bull; GENERATED: {gen_time}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceAfter=10))

        # Metadata Summary Card
        total_tokens = metadata.get("total_tokens", {}).get("total", 0) if isinstance(metadata.get("total_tokens"), dict) else 0
        duration_sec = metadata.get("total_duration_seconds", 0.0)
        user_input = metadata.get("user_prompt", "Standard Evaluation")

        meta_data = [
            [
                Paragraph("Target / Prompt:", meta_label_style),
                Paragraph(str(user_input)[:60], meta_val_style),
                Paragraph("Execution Duration:", meta_label_style),
                Paragraph(f"{duration_sec:.2f}s", meta_val_style),
            ],
            [
                Paragraph("Agents Chained:", meta_label_style),
                Paragraph("Researcher &rarr; Validator &rarr; Generator", meta_val_style),
                Paragraph("Total Tokens Consumed:", meta_label_style),
                Paragraph(f"{total_tokens:,}", meta_val_style),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[110, 190, 110, 94])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # Parse and append report body
        lines = (report_text or "").split("\n")
        in_code_block = False

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 4))
                continue

            if line.startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                story.append(Paragraph(self._escape_xml(line), body_style))
                continue

            if line.startswith("# "):
                story.append(Spacer(1, 8))
                story.append(Paragraph(self._escape_xml(line.lstrip("# ").strip()), h1_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=6))
            elif line.startswith("## "):
                story.append(Spacer(1, 6))
                story.append(Paragraph(self._escape_xml(line.lstrip("# ").strip()), h1_style))
            elif line.startswith("### "):
                story.append(Spacer(1, 4))
                story.append(Paragraph(self._escape_xml(line.lstrip("# ").strip()), h2_style))
            elif line.startswith(("- ", "* ", "• ")):
                bullet_text = line[2:].strip()
                story.append(Paragraph(f"&bull; {self._format_inline_markdown(bullet_text)}", bullet_style))
            else:
                story.append(Paragraph(self._format_inline_markdown(line), body_style))

        # Build document
        doc.build(story, canvasmaker=NumberedCanvas)

        file_size = os.path.getsize(self.output_path)
        with open(self.output_path, "rb") as f:
            checksum = hashlib.sha256(f.read()).hexdigest()

        return {
            "output_pdf_path": os.path.abspath(self.output_path),
            "file_size_bytes": file_size,
            "sha256_checksum": checksum,
        }

    @staticmethod
    def _escape_xml(text: str) -> str:
        """Escapes raw text for safe inclusion in ReportLab XML-like paragraphs."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    @classmethod
    def _format_inline_markdown(cls, text: str) -> str:
        """Translates basic markdown bold/italic tags into ReportLab XML markup."""
        escaped = cls._escape_xml(text)
        # Bold **text** -> <b>text</b>
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
        # Italic *text* -> <i>text</i>
        escaped = re.sub(r"\*(.+?)\*", r"<i>\1</i>", escaped)
        # Inline code `code` -> <font name="Courier">\1</font>
        escaped = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', escaped)
        return escaped
