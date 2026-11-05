"""
Data models for the prompt-driven, domain-agnostic research and report workflow.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SectionSpec:
    """Specification of a single report section parsed dynamically from a prompt Markdown file."""
    name: str                           # Normalized slug identifier (e.g. "executive_summary")
    title: str                          # Display title (e.g. "1. EXECUTIVE SUMMARY")
    level: int = 2                      # Header level (2 for ##, 3 for ###)
    instructions: str = ""              # Specific section prompt guidelines & constraints
    required_fields: List[str] = field(default_factory=list)  # Extracted field checklist
    format_rules: str = ""              # Bullet points, tables, limits, ordering rules
    is_synthesis: bool = False          # True if section synthesizes cross-section findings (e.g. Executive Summary or Verdict)


@dataclass
class ReportPromptSpec:
    """Complete specification of report structure parsed from a user's prompt Markdown file."""
    title_format: str = "# {SUBJECT}"
    global_rules: str = ""
    sections: List[SectionSpec] = field(default_factory=list)
    closing_statement: str = ""
    raw_markdown: str = ""

    def get_section(self, name_or_slug: str) -> Optional[SectionSpec]:
        """Finds section by slug or title."""
        target = name_or_slug.lower().strip()
        for s in self.sections:
            if s.name == target or s.title.lower() == target:
                return s
        return None


@dataclass
class AgnosticEvidence:
    """Atomic verifiable evidence unit captured by research extraction."""
    id: str                             # E.g. "E001"
    section_slug: str                   # Target section
    claim: str                          # Core factual finding
    value: Optional[str] = None         # Specific numeric or scalar datum if applicable
    as_of: Optional[str] = None         # Date of observation/report
    source_url: str = ""                # Origin URL
    source_title: str = ""              # Origin title/publication
    source_domain: str = ""             # Domain (e.g. reuters.com)
    published: Optional[str] = None     # Publication timestamp
    confidence: str = "med"             # "high", "med", "low"
    quote: Optional[str] = None         # Verbatim textual excerpt supporting claim

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "section_slug": self.section_slug,
            "claim": self.claim,
            "value": self.value,
            "as_of": self.as_of,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "source_domain": self.source_domain,
            "published": self.published,
            "confidence": self.confidence,
            "quote": self.quote,
        }


@dataclass
class AgnosticReportResult:
    """Final output bundle produced by workflow execution."""
    report_id: str
    subject: str
    markdown_path: str
    pdf_path: str
    telemetry_path: str
    telemetry_data: Dict[str, Any] = field(default_factory=dict)
    evidence_count: int = 0
    total_duration_seconds: float = 0.0
    total_tokens: int = 0
