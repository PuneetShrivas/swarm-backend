"""Dynamic Markdown Prompt Specification Parser.

Parses arbitrary Markdown or text specifications into a structured ReportPromptSpec.
Completely domain-agnostic; extracts sections, guidelines, required fields, and rules.
Supports:
1. Standard Markdown headings (## Section Title)
2. Numbered headings (## 1. Section Title, 1. SECTION TITLE)
3. Uppercase plaintext section headers (COMPANY SNAPSHOT, FINANCIAL OVERVIEW)
4. Bold plaintext section headers (** UPDATES / PRESS RELEASES / NEWS**)
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

from app.workflows.agnostic_research_report.models import SectionSpec, ReportPromptSpec


RAW_EXCLUDES = [
    "TARGET COMPANY",
    "TITLE",
    "GLOBAL FORMATTING RULES",
    "GLOBAL RULES",
    "INSTRUCTIONS",
    "RULES",
    "IN SCOPE",
    "OUT OF SCOPE",
    "SOURCING",
    "TIME HORIZON",
    "IDENTITY DISCIPLINE",
    "DATA SOURCE",
    "DISCIPLINE",
    "LOOK FOR",
    "OUTPUT",
    "SCALE",
    "JURISDICTION",
    "LIKELIHOOD",
    "SEVERITY IF BROUGHT",
    "SIDE A SIDE C EXPOSURE",
    "SIDE A / SIDE C EXPOSURE",
    "TOWER INTERACTION",
    "SCENARIO",
    "CONCLUSION",
    "DOMINANT DRIVER",
    "HEADLINE",
    "TENSIONS",
    "UNKNOWNS",
    "BAND REGISTER",
    "CLOSE WITH",
    "WHO TO REVIEW",
    "PURPOSE",
    "FORMAT EXAMPLE",
    "WINDOW",
    "PER INDIVIDUAL OUTCOME",
    "PER-INDIVIDUAL OUTCOME",
    "ORDERING WITHIN AN INDIVIDUAL",
    "MOST LIKELY ALLEGATION TYPE",
]


def _normalize_key(text: str) -> str:
    """Collapses non-alphanumeric characters and whitespace for fuzzy key comparison."""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9\s]", " ", text.upper())).strip()


HEADER_EXCLUDES: Set[str] = {_normalize_key(x) for x in RAW_EXCLUDES}


class MarkdownSpecParser:
    """Parses a report specification document dynamically at runtime."""

    @classmethod
    def parse_file(cls, file_path: str) -> ReportPromptSpec:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Prompt Markdown file not found: {file_path}")
        content = path.read_text(encoding="utf-8")
        return cls.parse(content)

    @classmethod
    def parse(cls, markdown_text: str) -> ReportPromptSpec:
        """Parses the raw Markdown or plain text prompt into a ReportPromptSpec."""
        spec = ReportPromptSpec(raw_markdown=markdown_text)

        # 1. Normalize line endings
        text = markdown_text.replace("\r\n", "\n")

        # 2. Extract Title format rule if present
        title_match = re.search(
            r"(?:^|\n)(?:##\s+)?TITLE[\s\S]*?(?:Format:\s*\n#\s*([^\n]+)|#\s*([^\n\.\"]+)|containing only the company's name[^\n]*?\"#\s*([^\"]+)\")",
            text,
            re.IGNORECASE,
        )
        if title_match:
            spec.title_format = "# {SUBJECT}"
        else:
            first_h1 = re.search(r"^#\s+([^\n]+)", text, re.MULTILINE)
            if first_h1 and "instruction" not in first_h1.group(1).lower():
                spec.title_format = f"# {first_h1.group(1).strip()}"

        # 3. Extract Closing Statement if present (find the last match in the prompt)
        closing_pattern = re.compile(
            r'(?:###?\s*Closing\s*Statement|CLOSE WITH|End the report with exactly)[\s\S]*?(?:"([^"\n]+)"|`([^`\n]+)`)',
            re.IGNORECASE,
        )
        closing_matches = list(closing_pattern.finditer(text))
        if closing_matches:
            last_match = closing_matches[-1]
            spec.closing_statement = (last_match.group(1) or last_match.group(2) or "").strip()

        # 4. Check if standard H2 headings exist (## ...)
        lines = text.split("\n")
        h2_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
        h2_matches = list(h2_pattern.finditer(text))
        valid_h2 = [
            m for m in h2_matches
            if not any(k in m.group(1).upper() for k in ["GLOBAL FORMATTING RULES", "GLOBAL RULES", "TITLE", "INSTRUCTIONS"])
        ]

        if len(valid_h2) >= 2:
            spec.sections = cls._parse_h2_sections(text, valid_h2)
            first_pos = valid_h2[0].start()
            spec.global_rules = text[:first_pos].strip()
        else:
            spec.sections, preamble_end_idx = cls._parse_plain_or_bold_sections(lines)
            spec.global_rules = "\n".join(lines[:preamble_end_idx]).strip()

        return spec

    @classmethod
    def _parse_h2_sections(cls, text: str, matches: List[re.Match]) -> List[SectionSpec]:
        """Extracts sections from standard ## Markdown headings."""
        sections: List[SectionSpec] = []
        for idx, match in enumerate(matches):
            raw_title = match.group(1).strip()
            start_pos = match.end()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            section_content = text[start_pos:end_pos].strip()

            slug = cls._slugify(raw_title)
            is_synth = any(term in raw_title.lower() for term in [
                "executive summary", "verdict", "synthesis", "conclusion", "overall", "summary"
            ])
            fields = cls._extract_fields(section_content)

            sections.append(SectionSpec(
                name=slug,
                title=raw_title,
                level=2,
                instructions=section_content,
                required_fields=fields,
                is_synthesis=is_synth,
            ))
        return sections

    @classmethod
    def _parse_plain_or_bold_sections(cls, lines: List[str]) -> Tuple[List[SectionSpec], int]:
        """Extracts sections from uppercase, bold, or numbered plaintext lines."""
        raw_candidates: List[Tuple[int, str]] = []

        for idx, line in enumerate(lines):
            line_s = line.strip()
            if not line_s:
                continue

            # Check bold heading e.g. ** UPDATES / PRESS RELEASES / NEWS** or **COMPANY SNAPSHOT**
            m_bold = re.match(r"^\*{2,}\s*([A-Za-z0-9\s/&,-]+?)\s*\*{2,}$", line_s)
            if m_bold:
                h = m_bold.group(1).strip()
                if not cls._is_excluded_header(h):
                    raw_candidates.append((idx, h))
                    continue

            # Check numbered headers e.g. "1. COMPANY SNAPSHOT" or "01) FINANCIAL OVERVIEW"
            m_num = re.match(r"^\d{1,2}[\.\)]\s+([A-Za-z0-9\s/&,-]+)$", line_s)
            if m_num:
                h = m_num.group(1).strip()
                if not cls._is_excluded_header(h):
                    raw_candidates.append((idx, h))
                    continue

            # Check all-caps lines e.g. "COMPANY SNAPSHOT", "FINANCIAL OVERVIEW"
            if re.match(r"^[A-Z0-9\s/&,-]{3,50}$", line_s) and any(c.isalpha() for c in line_s):
                if line_s.endswith(":") or line_s.endswith("."):
                    continue
                if not cls._is_excluded_header(line_s):
                    raw_candidates.append((idx, line_s))
                    continue

            # Check Markdown # or ### if present
            if line_s.startswith("# ") or line_s.startswith("### "):
                h = line_s.lstrip("#").strip()
                if not cls._is_excluded_header(h):
                    raw_candidates.append((idx, h))
                    continue

        # Deduplicate consecutive identical headings (e.g. repeated DIRECTOR & OFFICER HISTORY)
        deduped_candidates: List[Tuple[int, str]] = []
        for c in raw_candidates:
            if not deduped_candidates or deduped_candidates[-1][1] != c[1]:
                deduped_candidates.append(c)

        if not deduped_candidates:
            return [SectionSpec(
                name="full_report",
                title="Full Report",
                instructions="\n".join(lines).strip(),
                is_synthesis=False,
            )], 0

        first_section_line = deduped_candidates[0][0]
        sections: List[SectionSpec] = []

        for i, (line_idx, title) in enumerate(deduped_candidates):
            next_line_idx = deduped_candidates[i + 1][0] if i + 1 < len(deduped_candidates) else len(lines)
            slice_lines = lines[line_idx + 1:next_line_idx]
            cleaned_slice = [
                l for l in slice_lines
                if l.strip() != title and not l.strip().startswith(f"**{title}")
            ]
            content = "\n".join(cleaned_slice).strip()

            slug = cls._slugify(title)
            is_synth = any(term in title.lower() for term in [
                "executive summary", "verdict", "synthesis", "overall", "summary"
            ])
            fields = cls._extract_fields(content)

            sections.append(SectionSpec(
                name=slug,
                title=title,
                level=2,
                instructions=content,
                required_fields=fields,
                is_synthesis=is_synth,
            ))

        return sections, first_section_line

    @staticmethod
    def _is_excluded_header(header: str) -> bool:
        """Determines if a candidate heading is a rule/metadata label rather than a report section."""
        norm_h = _normalize_key(header)
        if not norm_h:
            return True
        if norm_h in HEADER_EXCLUDES:
            return True
        for ex in HEADER_EXCLUDES:
            if norm_h == ex or norm_h.startswith(f"{ex} "):
                return True
        if any(marker in norm_h for marker in [
            "GLOBAL", "INSTRUCTION", "TARGET COMPANY", "TIME HORIZON", "FORMATTING", "SOURCING"
        ]):
            return True
        return False

    @staticmethod
    def _slugify(title: str) -> str:
        """Converts section title into a clean underscore-separated slug."""
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", title.strip())
        cleaned = re.sub(r"[^\w\s-]", "", cleaned).lower()
        slug = re.sub(r"[\s-]+", "_", cleaned).strip("_")
        return slug or "section"

    @staticmethod
    def _extract_fields(section_content: str) -> List[str]:
        """Extracts bulleted fields, checklist items, or subsection titles from section text."""
        fields: List[str] = []
        for line in section_content.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                bullet_text = line[2:].strip()
                if ":" in bullet_text and not bullet_text.startswith("http"):
                    field_name = bullet_text.split(":", 1)[0].strip()
                    if len(field_name) < 40 and not any(k in field_name.lower() for k in ["format", "e.g.", "note", "example"]):
                        fields.append(field_name)
                elif len(bullet_text) < 40 and not bullet_text.endswith("."):
                    fields.append(bullet_text)
            elif line.startswith("### "):
                fields.append(line[4:].strip())
            elif line and not line.startswith("http") and len(line) < 35 and not line.endswith(".") and not line.endswith(":"):
                if not any(k in line.lower() for k in ["rule", "guidance", "scope", "must", "note", "format"]):
                    fields.append(line)
        return fields[:15]
