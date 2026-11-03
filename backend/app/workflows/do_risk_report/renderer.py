"""
Publication Document Renderers.
Converts [E###] citations to styled footnotes, and exports publication-grade
Markdown, DOCX (python-docx), and PDF (reportlab) reports with an automated
Limitations & Low-Confidence Appendix.
"""

import os
import re
from typing import Dict, Any, List, Tuple, Optional
from app.workflows.do_risk_report.models import EntityCard, Evidence
from app.workflows.do_risk_report.ledger import EvidenceLedger


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
    ) -> str:
        lines: List[str] = []

        # Master title: exactly ONE title line containing only company name
        lines.append(f"# {entity.legal_name.upper()}\n")

        # Risk tier badge banner
        lines.append(f"**Overall D&O Risk Tier:** `{risk_tier.upper()}` | **Ticker:** `{entity.ticker}` | **CIK:** `{entity.cik}`\n")
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
    ) -> str:
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

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
        run_sub = sub_p.add_run(f"D&O PUBLIC RISK UNDERWRITING REPORT  |  TICKER: {entity.ticker}  |  CIK: {entity.cik}")
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
        lines = validated_text.split("\n")
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
            elif line_str.startswith("-"):
                b_p = doc.add_paragraph(style="List Bullet")
                b_p.paragraph_format.space_after = Pt(2)
                b_run = b_p.add_run(line_str.lstrip("-").strip())
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


class PdfRenderer:
    """Generates styled publication PDF report using ReportLab."""

    @staticmethod
    def render(
        filepath: str,
        entity: EntityCard,
        risk_tier: str,
        validated_text: str,
        footnotes: List[Dict[str, Any]],
        ledger: EvidenceLedger,
    ) -> str:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
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
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748b"),
        )
        h2_style = ParagraphStyle(
            "ReportH2",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#334155"),
        )
        bullet_style = ParagraphStyle(
            "ReportBullet",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11.5,
            leftIndent=12,
            textColor=colors.HexColor("#334155"),
            spaceAfter=2,
        )

        elements = []

        # Header Title
        elements.append(Paragraph(entity.legal_name.upper(), title_style))
        elements.append(Paragraph(f"D&O PUBLIC RISK UNDERWRITING REPORT  |  TICKER: {entity.ticker}  |  CIK: {entity.cik}", subtitle_style))
        elements.append(Spacer(1, 8))

        # Risk Tier Banner Table
        banner_data = [[
            Paragraph(f"<b>OVERALL D&O RISK TIER:</b> <font size=11 color='#0284c7'><b>{risk_tier.upper()}</b></font>", body_style)
        ]]
        banner_table = Table(banner_data, colWidths=[530])
        banner_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(banner_table)
        elements.append(Spacer(1, 10))

        # Content parsing
        for line in validated_text.split("\n"):
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("#"):
                elements.append(Paragraph(line_str.lstrip("#").strip(), h2_style))
            elif line_str.startswith("-"):
                clean_b = line_str.lstrip("-").strip()
                elements.append(Paragraph(f"&bull; {clean_b}", bullet_style))
            else:
                elements.append(Paragraph(line_str, body_style))

        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        # Footnotes Table
        elements.append(Paragraph("FOOTNOTE CITATIONS & EVIDENCE SOURCES", h2_style))
        elements.append(Spacer(1, 4))

        fn_data = [["#", "ID", "Claim", "Source / Date"]]
        for fn in footnotes[:20]:
            fn_data.append([
                str(fn["num"]),
                fn["id"],
                Paragraph(fn["claim"][:70], body_style),
                Paragraph(f"{fn['source_type'].title()}<br/>{fn['published']}", subtitle_style),
            ])

        fn_table = Table(fn_data, colWidths=[20, 45, 335, 130])
        fn_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#475569")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(fn_table)

        doc.build(elements)
        return filepath
