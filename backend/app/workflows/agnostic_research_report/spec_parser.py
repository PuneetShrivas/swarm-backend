"""
Dynamic Markdown Prompt Specification Parser.
Parses any arbitrary Markdown specification into a structured ReportPromptSpec.
Completely domain-agnostic; extracts sections, guidelines, required fields, and rules.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from app.workflows.agnostic_research_report.models import SectionSpec, ReportPromptSpec


class MarkdownSpecParser:
    """Parses a report specification Markdown document dynamically at runtime."""

    @classmethod
    def parse_file(cls, file_path: str) -> ReportPromptSpec:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Prompt Markdown file not found: {file_path}")
        content = path.read_text(encoding="utf-8")
        return cls.parse(content)

    @classmethod
    def parse(cls, markdown_text: str) -> ReportPromptSpec:
        """Parses the raw Markdown prompt text into a ReportPromptSpec."""
        spec = ReportPromptSpec(raw_markdown=markdown_text)

        # 1. Normalize line endings
        text = markdown_text.replace("\r\n", "\n")

        # 2. Extract Title format rule if present
        title_match = re.search(r"(?:^|\n)##\s+TITLE[\s\S]*?(?:Format:\s*\n#\s*([^\n]+)|#\s*([^\n]+))", text, re.IGNORECASE)
        if title_match:
            spec.title_format = f"# {title_match.group(1) or title_match.group(2) or '{SUBJECT}'}"
        else:
            first_h1 = re.search(r"^#\s+([^\n]+)", text, re.MULTILINE)
            if first_h1 and "instruction" not in first_h1.group(1).lower():
                spec.title_format = f"# {first_h1.group(1).strip()}"

        # 3. Extract Closing Statement if present
        closing_match = re.search(r"(?:###?\s*Closing\s*Statement[\s\S]*?)(?:\"([^\"]+)\"|`([^`]+)`)", text, re.IGNORECASE)
        if closing_match:
            spec.closing_statement = (closing_match.group(1) or closing_match.group(2) or "").strip()
        else:
            simple_closing = re.search(r"End the report with exactly:?\s*\n+\"([^\"]+)\"", text, re.IGNORECASE)
            if simple_closing:
                spec.closing_statement = simple_closing.group(1).strip()

        # 4. Extract Global Instructions / Preamble
        # Everything before the first numbered section or first ## section after TITLE/RULES
        lines = text.split("\n")
        preamble_lines = []
        section_start_idx = len(lines)

        for i, line in enumerate(lines):
            line_s = line.strip()
            # Match sections like "## 1. EXECUTIVE SUMMARY" or "## SECTION NAME"
            if re.match(r"^##\s+\d+[\.\)]\s+", line_s) or (line_s.startswith("## ") and not any(k in line_s.upper() for k in ["GLOBAL", "FORMATTING", "TITLE", "RULES", "INSTRUCTION", "OVERVIEW"])):
                section_start_idx = i
                break
            preamble_lines.append(line)

        spec.global_rules = "\n".join(preamble_lines).strip()

        # 5. Extract Section Specifications
        # Find all H2 headers that represent report sections
        section_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
        matches = list(section_pattern.finditer(text))

        sections: List[SectionSpec] = []
        for idx, match in enumerate(matches):
            raw_title = match.group(1).strip()
            # Skip metadata/global sections
            if any(k in raw_title.upper() for k in ["GLOBAL FORMATTING RULES", "GLOBAL RULES", "TITLE", "INSTRUCTIONS"]):
                continue

            start_pos = match.end()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            section_content = text[start_pos:end_pos].strip()

            # Generate clean slug
            slug = cls._slugify(raw_title)

            # Check if this section is a synthesis/verdict section
            is_synth = any(term in raw_title.lower() for term in [
                "executive summary", "verdict", "synthesis", "conclusion", "overall", "summary"
            ])

            # Extract required fields (look for bullet lists, fields:, keywords)
            fields = cls._extract_fields(section_content)

            sections.append(SectionSpec(
                name=slug,
                title=raw_title,
                level=2,
                instructions=section_content,
                required_fields=fields,
                is_synthesis=is_synth,
            ))

        # If no H2 sections matched (e.g., author used H1 or H3), fallback to general heading scan
        if not sections:
            sections = cls._fallback_scan_sections(text)

        spec.sections = sections
        return spec

    @staticmethod
    def _slugify(title: str) -> str:
        """Converts section title into a clean underscore-separated slug."""
        # Strip leading numbers like "1. ", "02) "
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", title.strip())
        # Strip non-alphanumeric
        cleaned = re.sub(r"[^\w\s-]", "", cleaned).lower()
        slug = re.sub(r"[\s-]+", "_", cleaned).strip("_")
        return slug or "section"

    @staticmethod
    def _extract_fields(section_content: str) -> List[str]:
        """Extracts bulleted fields, checklist items, or subsection titles from section text."""
        fields: List[str] = []
        for line in section_content.split("\n"):
            line = line.strip()
            # Match "- Field Name:" or "- Field Name"
            if line.startswith("- ") or line.startswith("* "):
                bullet_text = line[2:].strip()
                # Split at colon if present
                if ":" in bullet_text and not bullet_text.startswith("http"):
                    field_name = bullet_text.split(":", 1)[0].strip()
                    if len(field_name) < 40 and not any(k in field_name.lower() for k in ["format", "e.g.", "note", "example"]):
                        fields.append(field_name)
                elif len(bullet_text) < 40 and not bullet_text.endswith("."):
                    fields.append(bullet_text)
            elif line.startswith("### "):
                fields.append(line[4:].strip())
        return fields[:15]

    @classmethod
    def _fallback_scan_sections(cls, text: str) -> List[SectionSpec]:
        """Fallback scanner if user formatted with H1 or H3 instead of H2."""
        sections: List[SectionSpec] = []
        lines = text.split("\n")
        current_title = ""
        current_content: List[str] = []

        for line in lines:
            line_s = line.strip()
            if line_s.startswith("# ") or line_s.startswith("### "):
                if current_title and current_content:
                    sections.append(SectionSpec(
                        name=cls._slugify(current_title),
                        title=current_title,
                        instructions="\n".join(current_content).strip(),
                    ))
                current_title = line_s.lstrip("#").strip()
                current_content = []
            else:
                current_content.append(line)

        if current_title and current_content:
            sections.append(SectionSpec(
                name=cls._slugify(current_title),
                title=current_title,
                instructions="\n".join(current_content).strip(),
            ))
        return sections
