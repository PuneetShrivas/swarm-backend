"""
D&O Report Validation Agent Tool Call Handlers.
"""

import re
import datetime
from typing import Dict, Any, List, Optional
from app.workflows.do_risk_report.validator import ValidationAgent, DeterministicValidator
from app.workflows.do_risk_report.ledger import EvidenceLedger


def evaluate_date_cutoffs(report_text: str, current_date: str = "") -> str:
    """Applies the 12-month calendar cutoff to news updates and sorts newest-first."""
    agent = ValidationAgent(current_date=current_date or datetime.date.today().isoformat())
    return agent.apply_deterministic_corrections(report_text)


def verify_share_price_labeling(report_text: str, current_date: str = "") -> str:
    """Verifies that older share prices are labeled as 'last close (<date>)'."""
    agent = ValidationAgent(current_date=current_date or datetime.date.today().isoformat())
    return agent.apply_deterministic_corrections(report_text)
