"""
D&O Risk Underwriting Specialist Tool Call Handlers.
"""

from typing import Dict, Any, List, Optional
from app.workflows.do_risk_report.edgar import EdgarFetcher
from app.workflows.do_risk_report.ledger import EvidenceLedger
from app.workflows.do_risk_report.models import EntityCard, Evidence


def resolve_edgar_entity(ticker: str) -> Dict[str, Any]:
    """Resolves corporate entity metadata and CIK via SEC EDGAR."""
    fetcher = EdgarFetcher()
    card = fetcher.build_entity_card(ticker)
    return card.model_dump()


def fetch_edgar_facts(cik: str) -> Dict[str, Any]:
    """Extracts US-GAAP XBRL financial metrics for a CIK."""
    fetcher = EdgarFetcher()
    facts = fetcher.fetch_company_facts(cik)
    metrics = fetcher.extract_xbrl_metrics(facts)
    return metrics


def query_evidence_ledger(section: str, query: str = "") -> List[Dict[str, Any]]:
    """Filters evidence ledger rows for a specific section."""
    ledger = EvidenceLedger()
    rows = ledger.for_section(section)
    if query:
        q_lower = query.lower()
        rows = [r for r in rows if q_lower in r.claim.lower()]
    return [r.model_dump() for r in rows]
