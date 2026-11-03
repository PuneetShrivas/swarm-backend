"""
Template Specifications & Static Query Library.
Compiles the master D&O Underwriter structure from `web-search-prompt.txt` and
validation rules from `validation-prompt.txt` into structured section specifications
and pre-written static query templates.
"""

import os
from typing import List, Dict, Any, Optional
from app.workflows.do_risk_report.models import SectionSpec, TemplateSpec, EntityCard
from app.workflows.do_risk_report.retrieval import WORKSTREAM_DOMAINS

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")


def load_prompt_text(filename: str) -> str:
    path = os.path.join(PROMPTS_DIR, filename)
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# Section Definitions matching agent-instructions/web-search-prompt.txt
SECTION_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "company_snapshot",
        "title": "COMPANY SNAPSHOT",
        "required_fields": [
            "legal_name", "business_description", "hq_footprint", "us_exposure",
            "country_of_domicile", "cpi_score", "listing_ticker", "market_cap",
            "share_price", "total_assets", "revenue", "capital_structure",
            "trading_liquidity", "analyst_sentiment", "governance_snapshot",
            "crypto_cannabis_coal", "ai_exposure", "conclusion_band"
        ],
        "static_query_templates": [
            "{company} {ticker} market cap share price 52 week range current month",
            "{company} business description headquarters US exposure country of domicile",
            "{company} capital structure debt to equity trading liquidity analyst rating",
            "{company} AI exposure material to revenue valuation governance",
            "{company} exposure crypto cannabis coal",
        ],
        "workstream": "news",
    },
    {
        "name": "news_updates",
        "title": "UPDATES / PRESS RELEASES / NEWS",
        "required_fields": [
            "items_within_12_months", "newest_first", "claim_triggers_only"
        ],
        "static_query_templates": [
            "{company} litigation securities class action regulatory enforcement last 12 months",
            "{company} CEO CFO leadership departure auditor change resignation",
            "{company} guidance withdrawal earnings miss accounting restatement",
            "{company} M&A financing debt offering credit downgrade",
            "{company} SEC DOJ investigation whistleblower short seller report",
        ],
        "workstream": "news",
    },
    {
        "name": "financial_overview",
        "title": "FINANCIAL OVERVIEW",
        "required_fields": [
            "snapshot_metrics", "revenue_trend_descending", "profitability_durability",
            "cash_liquidity", "leverage_refinancing", "earnings_quality",
            "balance_sheet_flexibility", "credit_rating", "macro_resilience",
            "auditor_assessment", "debt_refinancing_profile", "conclusion_band"
        ],
        "static_query_templates": [
            "{company} annual report 10-K revenue trend balance sheet cash liquidity",
            "{company} credit rating S&P Moody's Fitch senior debt outlook",
            "{company} debt maturity profile credit facilities revolving commercial paper",
            "{company} auditor assessment material weakness going concern internal controls",
        ],
        "workstream": "credit_ratings",
    },
    {
        "name": "analysts",
        "title": "ANALYSTS",
        "required_fields": [
            "analyst_coverage", "bullish_neutral_bearish_breakdown", "positives_concerns",
            "peer_benchmarking_volatility", "conclusion_bullets"
        ],
        "static_query_templates": [
            "{company} Wall Street analyst consensus price target ratings bullish bearish",
            "{company} stock beta volatility peer comparison 52 week range",
            "{company} latest analyst upgrades downgrades key concerns",
        ],
        "workstream": "news",
    },
    {
        "name": "governance_culture",
        "title": "GOVERNANCE & CULTURE",
        "required_fields": [
            "board_independence", "governance_drift_5yr", "turnover_ceo_cfo",
            "audit_committee_strength", "related_party_complexity", "disclosure_discipline",
            "conclusion_band"
        ],
        "static_query_templates": [
            "{company} board independence CEO chair duality proxy statement DEF 14A",
            "{company} 5-year governance drift board turnover executive changes",
            "{company} audit committee financial experts related party transactions",
            "{company} disclosure controls culture scrutiny compliance failures",
        ],
        "workstream": "regulatory",
    },
    {
        "name": "director_officer_history",
        "title": "DIRECTOR & OFFICER HISTORY",
        "required_fields": [
            "mandatory_officers_reviewed", "scope_10_years", "identity_match_confirming",
            "per_individual_outcome"
        ],
        "static_query_templates": [
            "{company} CEO CFO prior litigation regulatory enforcement sanctions",
            "{company} Board Chair Audit Committee Chair history securities violations",
            "{company} executive officer director bar disqualification restatement",
        ],
        "workstream": "litigation",
    },
    {
        "name": "strategic_operational_profile",
        "title": "STRATEGIC & OPERATIONAL PROFILE",
        "required_fields": [
            "sector_position", "execution_capability", "concentration_risk",
            "regulatory_exposure", "key_man_dependency", "cyber_operational_risk",
            "conclusion_bullets"
        ],
        "static_query_templates": [
            "{company} competitive market share sector position customer concentration",
            "{company} key man dependencies operational execution risks supply chain",
            "{company} cyber operational resilience ransomware disaster recovery",
        ],
        "workstream": "news",
    },
    {
        "name": "securities_class_action_risk",
        "title": "SECURITIES CLASS ACTION RISK",
        "required_fields": [
            "scale_assessment", "jurisdiction", "likelihood_drivers_band",
            "most_likely_allegation_type", "severity_band", "side_a_side_c_bands",
            "tower_interaction", "scenario_max_2_lines", "conclusion_final_band"
        ],
        "static_query_templates": [
            "{company} securities class action lawsuit Stanford clearinghouse",
            "{company} shareholder derivative lawsuit Delaware chancery court",
            "{company} stock drop restatement disclosure event litigation risk",
        ],
        "workstream": "litigation",
    },
    {
        "name": "legal_regulatory_claims",
        "title": "LEGAL, REGULATORY & CLAIMS CONTEXT",
        "required_fields": [
            "lawsuits_ongoing_and_1yr", "nature_of_claim", "parties_jurisdiction_outcome",
            "regulatory_heat", "whistleblower_signals", "sector_clustering",
            "venue_risk", "us_exposure", "sanctions_exposure", "conclusion_bullets"
        ],
        "static_query_templates": [
            "{company} federal court docket litigation ongoing settlement courtlistener",
            "{company} SEC DOJ FTC formal investigation enforcement action order",
            "{company} whistleblower allegations sanctions Russia high risk territories",
        ],
        "workstream": "litigation",
    },
    {
        "name": "esg_cyber_operational",
        "title": "ESG, CYBER & OPERATIONAL EXPOSURE",
        "required_fields": [
            "esg_controversy_velocity", "cyber_disclosure_quality", "product_safety_exposure",
            "supply_chain_fragility", "conclusion_bullets"
        ],
        "static_query_templates": [
            "{company} ESG controversy environmental safety OSHA regulatory fine",
            "{company} cyber incident data breach SEC 8-K cyber disclosure",
            "{company} product recall safety investigation supply chain disruption",
        ],
        "workstream": "news",
    },
    {
        "name": "forward_looking_risk",
        "title": "FORWARD-LOOKING STRATEGIC RISK",
        "required_fields": [
            "near_term_catalysts", "macro_sector_pressure", "execution_vulnerabilities",
            "regulatory_shifts", "conclusion_bullets"
        ],
        "static_query_templates": [
            "{company} near term catalysts regulatory headwinds tariff exposure",
            "{company} macro headwinds interest rate margin pressure earnings risk",
            "{company} strategic execution vulnerabilities upcoming product pipeline",
        ],
        "workstream": "news",
    },
    {
        "name": "overall_verdict",
        "title": "OVERALL D&O UNDERWRITER VERDICT",
        "required_fields": [
            "headline_max_20_words", "final_band_confidence", "dominant_driver_cited",
            "tensions_mismatches", "unknowns_gaps", "band_register_verbatim",
            "closing_disclaimer"
        ],
        "static_query_templates": [],
        "workstream": "news",
    },
]


class TemplateCompiler:
    """Compiles prompt files and static definitions into runtime specifications."""

    @staticmethod
    def get_template_spec() -> TemplateSpec:
        web_search_prompt = load_prompt_text("web_search_prompt.txt")
        validation_prompt = load_prompt_text("validation_prompt.txt")

        section_specs = [
            SectionSpec(
                name=d["name"],
                title=d["title"],
                required_fields=d["required_fields"],
                static_queries=d["static_query_templates"],
                stop_threshold=2,
            )
            for d in SECTION_DEFINITIONS
        ]

        return TemplateSpec(
            id="do_underwriting_lens_v1",
            title="D&O Public Risk Underwriting Lens (0.01% Tier Senior Underwriter)",
            sections=section_specs,
            system_prompt_template=web_search_prompt,
            validation_rules_template=validation_prompt,
        )

    @staticmethod
    def generate_static_queries(entity: EntityCard) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fills static query templates for each section with entity details and domain filters.
        No LLM required — queries are ready to execute immediately at t=0.
        """
        queries_by_section: Dict[str, List[Dict[str, Any]]] = {}

        for defn in SECTION_DEFINITIONS:
            sec_name = defn["name"]
            templates = defn.get("static_query_templates", [])
            workstream = defn.get("workstream", "news")
            domains = WORKSTREAM_DOMAINS.get(workstream, [])

            sec_queries: List[Dict[str, Any]] = []
            for tmpl in templates:
                q_text = tmpl.format(
                    company=entity.legal_name,
                    ticker=entity.ticker
                )
                sec_queries.append({
                    "text": q_text,
                    "section": sec_name,
                    "domains": domains,
                    "recency": "year" if sec_name == "news_updates" else None,
                })

            queries_by_section[sec_name] = sec_queries

        return queries_by_section
