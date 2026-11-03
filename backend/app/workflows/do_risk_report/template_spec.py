"""
Dynamic Template Specifications & Query Compiler.
Treats `web-search-prompt.txt` as the dynamic single source of truth.
Parses sections, verbatim instructions, field requirements, and search queries dynamically at runtime.
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from app.workflows.do_risk_report.models import SectionSpec, TemplateSpec, EntityCard
from app.workflows.do_risk_report.retrieval import WORKSTREAM_DOMAINS

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

HEADER_EXCLUDES = {
    "IN SCOPE", "OUT OF SCOPE", "SOURCING", "RULES", "CONCLUSION", "OUTPUT",
    "WHO TO REVIEW", "LOOK FOR", "TIME HORIZON", "IDENTITY DISCIPLINE", "PER-INDIVIDUAL OUTCOME",
    "DISCIPLINE", "CLOSE WITH", "BAND REGISTER", "SUMMARY", "TITLE", "TARGET COMPANY",
    "DATA SOURCE", "LIKELIHOOD", "SEVERITY IF BROUGHT", "SIDE A / SIDE C EXPOSURE",
    "TOWER INTERACTION", "MOST LIKELY ALLEGATION TYPE", "Debt & Refinancing Profile",
}

# Domain keyword mappings for workstream selection
WORKSTREAM_KEYWORDS = {
    "litigation": ["litigation", "lawsuit", "court", "derivative", "docket", "sec investigation", "settlement", "class action"],
    "credit_ratings": ["credit rating", "debt", "refinancing", "bond", "maturities", "commercial paper", "fitch", "moodys", "s&p"],
    "regulatory": ["sec", "doj", "ftc", "regulator", "governance", "board", "insider", "audit", "compliance", "whistleblower"],
}


def load_prompt_text(filename: str = "web_search_prompt.txt") -> str:
    """Loads prompt text from file or parent agent-instructions directory."""
    path = os.path.join(PROMPTS_DIR, filename)
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # Fallback to root agent-instructions
    root_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "agent-instructions",
        filename.replace("_", "-")
    )
    if os.path.isfile(root_path):
        with open(root_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def slugify_header(title: str) -> str:
    """Converts display section title into a clean slug."""
    clean = re.sub(r"[^\w\s]", "", title.lower())
    words = clean.split()
    if not words:
        return "section"
    # Canonical mappings for common titles
    if "snapshot" in words:
        return "company_snapshot"
    if "news" in words or "updates" in words or "press" in words:
        return "news_updates"
    if "financial" in words:
        return "financial_overview"
    if "analysts" in words:
        return "analysts"
    if "governance" in words:
        return "governance_culture"
    if "director" in words or "officer" in words:
        return "director_officer_history"
    if any(w.startswith("forward") for w in words):
        return "forward_looking_risk"
    if "strategic" in words:
        return "strategic_operational_profile"
    if "securities" in words or "sca" in words:
        return "securities_class_action_risk"
    if "legal" in words or "claims" in words:
        return "legal_regulatory_claims"
    if "esg" in words or "cyber" in words:
        return "esg_cyber_operational"
    if "verdict" in words or "overall" in words:
        return "overall_verdict"
    return "_".join(words[:3])


def determine_workstream(text: str) -> str:
    """Determines domain filter workstream based on section instruction content."""
    t_lower = text.lower()
    for ws, kws in WORKSTREAM_KEYWORDS.items():
        if any(kw in t_lower for kw in kws):
            return ws
    return "news"


def extract_section_queries(title: str, text: str) -> List[str]:
    """
    Extracts targeted search query concepts dynamically from the prompt instructions.
    """
    slug = slugify_header(title)
    queries: List[str] = []

    if slug == "company_snapshot":
        queries = [
            "{company} {ticker} market cap share price 52 week range current month",
            "{company} business description headquarters US operations country of domicile",
            "{company} capital structure debt to equity trading liquidity analyst rating",
            "{company} AI exposure material to revenue valuation margins concentration risk",
            "{company} exposure crypto cannabis coal",
        ]
    elif slug == "news_updates":
        queries = [
            "{company} litigation securities class action regulatory enforcement last 12 months",
            "{company} CEO CFO leadership departure auditor change resignation",
            "{company} guidance withdrawal earnings miss accounting restatement",
            "{company} M&A financing debt offering credit rating downgrade",
            "{company} SEC DOJ investigation whistleblower short seller report",
        ]
    elif slug == "financial_overview":
        queries = [
            "{company} annual report 10-K revenue trend balance sheet cash liquidity operating cash flow",
            "{company} credit rating S&P Moody's Fitch senior debt outlook",
            "{company} debt maturity profile credit facilities revolving commercial paper covenants",
            "{company} auditor assessment material weakness going concern internal controls",
        ]
    elif slug == "analysts":
        queries = [
            "{company} Wall Street analyst consensus price target ratings bullish bearish breakdown",
            "{company} stock beta volatility peer comparison 52 week trading range",
            "{company} latest analyst upgrades downgrades key concerns",
            "{company} short interest short interest ratio days to cover stock loan fee",
        ]
    elif slug == "governance_culture":
        queries = [
            "{company} board independence Lead Independent Director chair CEO duality DEF 14A",
            "{company} 5-year governance drift board turnover executive changes refresh",
            "{company} audit committee financial experts auditor tenure fees related party transactions",
            "{company} insider selling Rule 10b5-1 trading plans executive compensation clawback",
        ]
    elif slug == "director_officer_history":
        queries = [
            "{company} CEO CFO President prior litigation regulatory enforcement sanctions",
            "{company} Board Chair Audit Committee Chair history securities violations dockets",
            "{company} executive officer director bar disqualification restatement accounting fraud",
        ]
    elif slug == "strategic_operational_profile":
        queries = [
            "{company} competitive market share sector position customer concentration top customers",
            "{company} single-source supplier dependencies manufacturing TSMC operational risk",
            "{company} key man dependencies operational execution risks supply chain choke points",
            "{company} geopolitical export restrictions BIS licenses trade compliance",
        ]
    elif slug == "securities_class_action_risk":
        queries = [
            "{company} securities class action lawsuit Stanford clearinghouse certified class",
            "{company} shareholder derivative lawsuit Delaware chancery court",
            "{company} stock drop restatement disclosure event litigation Side A Side C exposure",
        ]
    elif slug == "legal_regulatory_claims":
        queries = [
            "{company} federal court docket litigation ongoing settlement courtlistener",
            "{company} SEC DOJ FTC formal investigation enforcement action order subpoenas",
            "{company} whistleblower allegations sanctions Russia high risk export controls",
        ]
    elif slug == "esg_cyber_operational":
        queries = [
            "{company} ESG controversy environmental safety OSHA regulatory fine power consumption",
            "{company} cyber incident data breach ransomware SEC 8-K cyber disclosure",
            "{company} product recall safety investigation AI training copyright lawsuit",
        ]
    elif slug == "forward_looking_risk":
        queries = [
            "{company} near term catalysts regulatory headwinds tariff exposure margin trajectory",
            "{company} macro headwinds interest rate margin pressure earnings guidance risk",
            "{company} strategic execution vulnerabilities upcoming product pipeline",
        ]
    elif slug == "overall_verdict":
        queries = []
    else:
        # Generic query generation from lines in the custom section
        cleaned_lines = [
            re.sub(r"[^\w\s]", "", l).strip()
            for l in text.splitlines()
            if l.strip() and len(l.strip()) > 3 and not l.strip().startswith("-")
        ]
        for l in cleaned_lines[:4]:
            queries.append(f"{{company}} {l[:50]}")

    return queries


def parse_prompt_sections(prompt_text: str) -> Tuple[str, List[SectionSpec]]:
    """
    Dynamically segments `web-search-prompt.txt` into master rules and SectionSpec objects.
    Finds section headers by detecting uppercase section lines.
    """
    lines = prompt_text.splitlines()
    section_spans: List[Dict[str, Any]] = []
    curr_title = None
    curr_start = 0

    for idx, line in enumerate(lines):
        clean = re.sub(r"[\*#_]", "", line).strip()
        clean_no_colon = clean[:-1].strip() if clean.endswith(":") else clean

        # Detect section headings
        is_hdr = (
            clean.isupper()
            and len(clean) >= 4
            and clean_no_colon not in HEADER_EXCLUDES
            and not clean.startswith("NOTE")
            and not clean.startswith("HTTP")
            and not clean.startswith("END OF")
            and not clean.endswith(":")
            and not clean.startswith("---")
        )

        if is_hdr:
            if any(s["title"] == clean for s in section_spans):
                continue
            if curr_title is not None:
                section_spans.append({"title": curr_title, "start": curr_start, "end": idx})
            curr_title = clean
            curr_start = idx

    if curr_title is not None:
        section_spans.append({"title": curr_title, "start": curr_start, "end": len(lines)})

    if not section_spans:
        # Fallback if no uppercase headers detected
        return prompt_text, []

    # Master prompt is everything before the first section
    first_start = section_spans[0]["start"]
    master_prompt = "\n".join(lines[:first_start]).strip()

    section_specs: List[SectionSpec] = []
    for span in section_spans:
        sec_title = span["title"]
        sec_body = "\n".join(lines[span["start"]:span["end"]]).strip()
        sec_name = slugify_header(sec_title)
        workstream = determine_workstream(sec_body)
        queries = extract_section_queries(sec_title, sec_body)

        # Extract field lines
        req_fields = [
            line.strip().lstrip("-*• ")
            for line in sec_body.splitlines()
            if line.strip() and not line.strip().isupper() and len(line.strip()) < 80
        ][:15]

        section_specs.append(SectionSpec(
            name=sec_name,
            title=sec_title,
            section_prompt=sec_body,
            required_fields=req_fields,
            static_queries=queries,
            workstream=workstream,
            stop_threshold=2,
        ))

    return master_prompt, section_specs


class TemplateCompiler:
    """
    Dynamic Template Specification Compiler.
    Loads and compiles `web-search-prompt.txt` dynamically at runtime.
    """

    @staticmethod
    def get_template_spec(prompt_filename: str = "web_search_prompt.txt") -> TemplateSpec:
        raw_web_prompt = load_prompt_text(prompt_filename)
        raw_val_prompt = load_prompt_text("validation_prompt.txt")

        master_rules, section_specs = parse_prompt_sections(raw_web_prompt)

        return TemplateSpec(
            id="do_underwriting_lens_v1",
            title="D&O Public Risk Underwriting Lens (Dynamic from web-search-prompt.txt)",
            sections=section_specs,
            system_prompt_template=master_rules or raw_web_prompt,
            validation_rules_template=raw_val_prompt,
        )

    @staticmethod
    def generate_static_queries(
        entity: EntityCard,
        template_spec: Optional[TemplateSpec] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Dynamically generates search queries for each parsed section using entity details.
        """
        spec = template_spec or TemplateCompiler.get_template_spec()
        queries_by_section: Dict[str, List[Dict[str, Any]]] = {}

        for sec in spec.sections:
            sec_name = sec.name
            domains = WORKSTREAM_DOMAINS.get(sec.workstream, [])

            sec_queries: List[Dict[str, Any]] = []
            for tmpl in sec.static_queries:
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


# Dynamic module-level definitions for backward compatibility
def _get_dynamic_definitions() -> List[Dict[str, Any]]:
    spec = TemplateCompiler.get_template_spec()
    return [
        {
            "name": s.name,
            "title": s.title,
            "section_prompt": s.section_prompt,
            "required_fields": s.required_fields,
            "static_query_templates": s.static_queries,
            "workstream": s.workstream,
        }
        for s in spec.sections
    ]


SECTION_DEFINITIONS = _get_dynamic_definitions()
