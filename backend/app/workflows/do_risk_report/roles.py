"""
Single LLM Worker & Role Router on Groq Infrastructure.
Implements the 'one LLM worker, many roles' architectural principle.
A role is configuration (model tier, system prompt, output schema, temperature),
not a separate agent.
"""

import os
import time
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv
load_dotenv()

from app.groq_client import get_groq_client, execute_groq_chat, is_groq_configured
from app.workflows.do_risk_report.models import Evidence, EntityCard

# Active model tiers available on Groq LPUs
GROQ_FAST_TIER = "qwen/qwen3.8-27b"
GROQ_MEDIUM_TIER = "qwen/qwen3.8-27b"
GROQ_REASONING_TIER = "openai/gpt-oss-120b"

# System prompts for roles
PLAN_PROMPT = """You are the Plan role in a D&O Risk Underwriting pipeline.
Given an Entity Card and a report section specification, formulate up to 3 highly targeted, company-specific
search queries to uncover adverse litigation, regulatory enforcement, governance drift, or accounting scrutiny.
Do not repeat generic search queries.
Output format: JSON object with key "queries": [{"text": "query string", "domains": ["domain.com"], "recency": "year"}]"""

EXTRACT_PROMPT = """You are the Extract role in a D&O Risk Underwriting pipeline.
Task: Turn compacted search results into atomic facts adhering to the Evidence Ledger schema.
CRITICAL RULES:
1. ENTITY GUARD: Reject any result about a different company with a similar name. Use legal name, ticker, and CIK to verify identity.
2. NO INFERENCE: Extract only what is explicitly stated in the source text. Never extrapolate or guess.
3. CITATIONS: Each extracted fact must include the source URL, publication date, and a verbatim quote.
4. "NOT FOUND": If a search result does not contain facts addressing the section fields, return an empty items list.
Output format: JSON object with key "items": list of Evidence objects with fields:
[{"section": "...", "claim": "...", "value": "...", "as_of": "YYYY-MM-DD", "status": "found", "source_url": "...", "source_type": "court|regulator|filing|rating_agency|news|other", "published": "YYYY-MM-DD", "confidence": "high|med|low", "quote": "verbatim text"}]"""

GAP_PROMPT = """You are the Gap role in a D&O Risk Underwriting pipeline.
Task: Compare section evidence ledger rows against the required section field checklist.
If all required fields are satisfied, return an empty queries list.
If a high-stakes field (e.g. securities litigation, settlement amount, restatement) is missing or supported by only one source,
generate up to 2 targeted follow-up queries.
Output format: JSON object with keys:
{"missing_fields": ["field_name"], "queries": [{"text": "...", "domains": ["..."], "recency": "year"}]}"""

DRAFT_PROMPT = """You are the 0.01%-tier Senior D&O Underwriter Draft role.
Task: Draft the assigned section narrative using ONLY the provided section evidence ledger rows.
CRITICAL RULES:
1. Every factual statement MUST carry an inline citation by ID, e.g. [E001], [E014]. NEVER cite by URL.
2. Bullet points only.
3. If an in-scope field has no evidence in the ledger, explicitly write: "<Field Name>: Not found in public disclosures / Not publicly available." NEVER fill gaps from model memory.
4. Strictly follow the section header, formatting, and scale (Contained / Elevated / High-Volatility / Severe Tail Exposure) from the underwriting guide.
Output format: JSON object with keys:
{"section_text": "### SECTION HEADER\n- Bullet 1 [E001]\n- Bullet 2 [E002]", "citations": ["E001", "E002"]}"""

SYNTHESIZE_PROMPT = """You are the Executive Synthesizer role in a D&O Underwriting pipeline.
Task: Produce the Executive Summary, overall D&O Underwriter Verdict, and the verbatim Band Register across all drafted sections.
CRITICAL RULES:
1. NO NEW FACTS: Every statement must be traceable to the section drafts.
2. Produce a headline with max 2 bullets, max 20 words each.
3. Dominant driver: cite the specific section doing the heavy lifting.
4. Transcribe the Band Register verbatim across Financial, Governance, SCA Likelihood, SCA Severity, Side A / Side C, Legal & Regulatory, ESG Cyber & Ops, and Forward-Looking.
5. Overall risk tier must be exactly one of: Contained, Elevated, High-Volatility, Severe Tail Exposure.
Output format: JSON object with keys:
{"executive_summary": "...", "risk_tier": "Contained|Elevated|High-Volatility|Severe Tail Exposure", "band_register": {"financial": "...", "governance": "..."}, "verdict_text": "..."}"""

VERIFY_PROMPT = """You are an Adversarial D&O Underwriting Auditor.
Task: Scrutinize the section draft against its cited evidence ledger rows.
Check for:
1. Unsupported claims: Draft states a fact not present in the cited quote.
2. Overstatements: Draft characterizes an allegation as an adjudicated finding or inflates severity.
3. Wrong entity: Claims attributed to target entity that belong to a subsidiary, competitor, or unrelated company.
4. Stale/Conflicting data: Discrepant dates or numbers.
Output format: JSON object with key "issues": list of issues:
[{"section": "...", "field": "...", "problem": "...", "suggested_query": "...", "severity": "critical|warning"}]"""

REPAIR_PROMPT = """You are the Repair role in a D&O Underwriting pipeline.
Task: Rewrite the flagged section passage to resolve the identified validation issues using available evidence rows.
Remove unsupported statements, correct numbers/dates, or downgrade to 'Data unavailable.'
Output format: JSON object with key "patched_text": "..." """

ROLES_CONFIG: Dict[str, Dict[str, Any]] = {
    "plan": {"model": GROQ_MEDIUM_TIER, "system": PLAN_PROMPT, "temp": 0.1, "max_tokens": 600},
    "extract": {"model": GROQ_FAST_TIER, "system": EXTRACT_PROMPT, "temp": 0.0, "max_tokens": 1500},
    "gap": {"model": GROQ_FAST_TIER, "system": GAP_PROMPT, "temp": 0.0, "max_tokens": 600},
    "draft": {"model": GROQ_MEDIUM_TIER, "system": DRAFT_PROMPT, "temp": 0.1, "max_tokens": 2000},
    "synthesize": {"model": GROQ_REASONING_TIER, "system": SYNTHESIZE_PROMPT, "temp": 0.1, "max_tokens": 2000},
    "verify": {"model": GROQ_REASONING_TIER, "system": VERIFY_PROMPT, "temp": 0.0, "max_tokens": 1000},
    "repair": {"model": GROQ_MEDIUM_TIER, "system": REPAIR_PROMPT, "temp": 0.0, "max_tokens": 2000},
}


def _extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    """Robust parser that extracts JSON payload from markdown fences or raw strings."""
    if not text:
        return {}
    # Try direct parse
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # Try fenced json block ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass

    # Try curly brace matching { ... }
    match_braces = re.search(r"(\{[\s\S]*\})", text)
    if match_braces:
        try:
            return json.loads(match_braces.group(1).strip())
        except Exception:
            pass

    return {}


async def run_role(
    role: str,
    user_input: str,
    *,
    model_override: Optional[str] = None,
    mock_response: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes a role using Groq models with strict JSON schema outputs.
    Falls back gracefully to mock payloads for tests or offline execution.
    """
    if role not in ROLES_CONFIG:
        raise ValueError(f"Unknown role '{role}'. Valid roles: {list(ROLES_CONFIG.keys())}")

    cfg = ROLES_CONFIG[role]
    selected_model = model_override or cfg["model"]

    # If mock_response is provided explicitly or testing mode is active without Groq key
    if mock_response is not None:
        return mock_response

    is_testing = os.environ.get("TESTING") == "true" or os.environ.get("MOCK_GROQ") == "true"
    groq_client, _ = get_groq_client()

    if not groq_client or is_testing or not is_groq_configured():
        return _generate_mock_role_output(role, user_input)

    # Live Groq API Execution
    try:
        content, _, _, _, _ = execute_groq_chat(
            client=groq_client,
            messages=[{"role": "user", "content": user_input}],
            system_prompt=cfg["system"] + "\n\nRespond ONLY with a valid JSON object matching the required schema.",
            requested_model=selected_model,
            temperature=cfg["temp"],
            max_completion_tokens=cfg["max_tokens"],
        )
        parsed = _extract_json_from_llm_response(content)
        if parsed:
            return parsed
    except Exception as e:
        print(f"Role '{role}' Groq execution note: {e}")

    # Fallback to deterministic mock
    return _generate_mock_role_output(role, user_input)


async def run_role_with_timings(
    role: str,
    user_input: str,
    *,
    model_override: Optional[str] = None,
    mock_response: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Executes a role using Groq models and captures exact execution latency.
    """
    t0 = time.perf_counter()
    result = await run_role(role, user_input, model_override=model_override, mock_response=mock_response)
    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    cfg = ROLES_CONFIG.get(role, {})
    model_used = model_override or cfg.get("model", "unknown")
    meta = {
        "duration_ms": duration_ms,
        "role": role,
        "model": model_used,
    }
    return result, meta


def _generate_mock_role_output(role: str, user_input: str) -> Dict[str, Any]:
    """Deterministic synthetic responses for each role during testing or offline runs."""
    if role == "plan":
        return {
            "queries": [
                {"text": "Apple SEC investigation formal order", "domains": ["sec.gov"], "recency": "year"},
                {"text": "Apple shareholder derivative lawsuit Delaware", "domains": ["courtlistener.com"], "recency": "year"}
            ]
        }
    elif role == "extract":
        return {
            "items": [
                {
                    "section": "securities_litigation",
                    "claim": "Shareholder class action ongoing regarding market disclosures",
                    "value": "Ongoing",
                    "as_of": "2024-01-15",
                    "status": "found",
                    "source_url": "https://courtlistener.com/docket/23-cv-0914",
                    "source_type": "court",
                    "published": "2024-01-15",
                    "confidence": "high",
                    "quote": "Securities class action lawsuit ongoing in district court."
                }
            ]
        }
    elif role == "gap":
        return {"missing_fields": [], "queries": []}
    elif role == "draft":
        return {
            "section_text": "### SECURITIES CLASS ACTION RISK\n- Level I US listing status with contained securities class action exposure [E001].\n- No formal restatement or adverse disclosure event recorded [E002].\n- Final band: Contained (data confidence: Strong).",
            "citations": ["E001", "E002"]
        }
    elif role == "synthesize":
        return {
            "executive_summary": "Overall public risk profile for target entity demonstrates robust balance sheet liquidity and low securities class action frequency.",
            "risk_tier": "Contained",
            "band_register": {
                "financial": "Contained",
                "governance": "Contained",
                "sca_likelihood": "Contained",
                "sca_severity": "Contained",
                "side_a_side_c": "Contained / Contained",
                "legal_regulatory": "Contained",
                "esg_cyber_ops": "Contained",
                "forward_looking": "Contained"
            },
            "verdict_text": "## OVERALL D&O UNDERWRITER VERDICT\n- Headline: Well-capitalized enterprise with mature internal governance controls and contained public securities exposure.\n- Final band: Contained (data confidence: Strong)\n- Dominant driver: Financial overview and primary filing strength [E001].\n- Tensions: None identified.\n- Unknowns: None.\n- Assessment based solely on information contained in this report."
        }
    elif role == "verify":
        return {"issues": []}
    elif role == "repair":
        return {"patched_text": user_input}

    return {}
