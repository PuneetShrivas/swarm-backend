"""
Agnostic Research & Report Generation Workflow.
Prompt-driven, domain-agnostic research, gap analysis, and publication document generation.
"""

from app.workflows.agnostic_research_report.models import (
    SectionSpec,
    ReportPromptSpec,
    AgnosticEvidence,
    AgnosticReportResult,
)
from app.workflows.agnostic_research_report.spec_parser import MarkdownSpecParser
from app.workflows.agnostic_research_report.ledger import AgnosticEvidenceLedger
from app.workflows.agnostic_research_report.retrieval import PerplexitySearchQueue, ResultCompactor
from app.workflows.agnostic_research_report.roles import (
    run_role,
    set_active_provider,
    get_active_provider,
    set_fallback_model,
    get_fallback_model,
    PROVIDER_MODELS,
)
from app.workflows.agnostic_research_report.renderer import (
    FootnoteTransformer,
    AgnosticMarkdownRenderer,
    AgnosticPdfRenderer,
)
from app.workflows.agnostic_research_report.orchestrator import AgnosticResearchOrchestrator
from app.workflows.agnostic_research_report.telemetry import render_tree, render_table
from app.workflows.agnostic_research_report.cli import parse_args, execute_cli

__all__ = [
    "SectionSpec",
    "ReportPromptSpec",
    "AgnosticEvidence",
    "AgnosticReportResult",
    "MarkdownSpecParser",
    "AgnosticEvidenceLedger",
    "PerplexitySearchQueue",
    "ResultCompactor",
    "run_role",
    "set_active_provider",
    "get_active_provider",
    "set_fallback_model",
    "get_fallback_model",
    "PROVIDER_MODELS",
    "FootnoteTransformer",
    "AgnosticMarkdownRenderer",
    "AgnosticPdfRenderer",
    "AgnosticResearchOrchestrator",
    "render_tree",
    "render_table",
    "parse_args",
    "execute_cli",
]
