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
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv
load_dotenv()

from app.groq_client import get_groq_client, execute_groq_chat, is_groq_configured
from app.workflows.do_risk_report.models import Evidence, EntityCard

# Active model tiers available per provider
ACTIVE_PROVIDER = os.environ.get("LLM_PROVIDER", "gpt-oss").lower()

PROVIDER_MODELS: Dict[str, Dict[str, str]] = {
    "gpt-oss": {
        "fast": "openai/gpt-oss-20b",
        "medium": "openai/gpt-oss-20b",
        "reasoning": "openai/gpt-oss-120b",
    },
    "qwen": {
        "fast": "qwen/qwen3.8-27b",
        "medium": "qwen/qwen3.8-27b",
        "reasoning": "qwen/qwen3.8-27b",
    },
    "gemini": {
        "fast": os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
        "medium": os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
        "reasoning": os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
    },
    "iteracompute": {
        "fast": os.environ.get("ITERACOMPUTE_MODEL", "qwen/qwen3.8-27b"),
        "medium": os.environ.get("ITERACOMPUTE_MODEL", "qwen/qwen3.8-27b"),
        "reasoning": os.environ.get("ITERACOMPUTE_REASONING_MODEL", os.environ.get("ITERACOMPUTE_MODEL", "qwen/qwen3.8-27b")),
    },
    "itera": {
        "fast": os.environ.get("ITERACOMPUTE_MODEL", "qwen/qwen3.8-27b"),
        "medium": os.environ.get("ITERACOMPUTE_MODEL", "qwen/qwen3.8-27b"),
        "reasoning": os.environ.get("ITERACOMPUTE_REASONING_MODEL", os.environ.get("ITERACOMPUTE_MODEL", "qwen/qwen3.8-27b")),
    },
    "azure": {
        "fast": os.environ.get("AZURE_FAST_MODEL", "claude-sonnet-4-6"),
        "medium": os.environ.get("AZURE_MEDIUM_MODEL", "claude-sonnet-4-6"),
        "reasoning": os.environ.get("AZURE_MODEL", "claude-opus-4-8"),
    },
    "azure-foundry": {
        "fast": os.environ.get("AZURE_FAST_MODEL", "claude-sonnet-4-6"),
        "medium": os.environ.get("AZURE_MEDIUM_MODEL", "claude-sonnet-4-6"),
        "reasoning": os.environ.get("AZURE_MODEL", "claude-opus-4-8"),
    },
    "foundry": {
        "fast": os.environ.get("AZURE_FAST_MODEL", "claude-sonnet-4-6"),
        "medium": os.environ.get("AZURE_MEDIUM_MODEL", "claude-sonnet-4-6"),
        "reasoning": os.environ.get("AZURE_MODEL", "claude-opus-4-8"),
    },
}

ROLE_TIER_MAPPING: Dict[str, str] = {
    "plan": "medium",
    "extract": "fast",
    "gap": "fast",
    "draft": "medium",
    "synthesize": "reasoning",
    "verify": "reasoning",
    "repair": "reasoning",
}


def set_active_provider(provider: str) -> None:
    """Sets the active LLM provider for all non-Perplexity workflow tasks."""
    global ACTIVE_PROVIDER
    p = provider.lower().strip()
    if p in ["gpt-oss", "qwen", "gemini", "iteracompute", "itera", "azure", "azure-foundry", "foundry"]:
        if p == "itera":
            ACTIVE_PROVIDER = "iteracompute"
        elif p in ["azure-foundry", "foundry"]:
            ACTIVE_PROVIDER = "azure"
        else:
            ACTIVE_PROVIDER = p
    else:
        raise ValueError(f"Unknown LLM provider '{provider}'. Valid choices: 'gpt-oss', 'qwen', 'gemini', 'iteracompute', 'azure'")


def get_active_provider() -> str:
    """Returns the currently active LLM provider name."""
    return ACTIVE_PROVIDER


# Fallback/Secondary model to fail over to upon encountering 429 rate limits
ACTIVE_FALLBACK_MODEL: Optional[str] = (
    os.environ.get("AZURE_FALLBACK_MODEL")
    or os.environ.get("LLM_FALLBACK_MODEL")
)


def set_fallback_model(model: Optional[str]) -> None:
    """Sets the secondary/fallback model to use when primary model encounters 429 rate limits."""
    global ACTIVE_FALLBACK_MODEL
    ACTIVE_FALLBACK_MODEL = model.strip() if (model and model.strip()) else None


def get_fallback_model() -> Optional[str]:
    """Returns the currently active fallback model name, if configured."""
    return ACTIVE_FALLBACK_MODEL


# Global concurrency semaphore for Azure Foundry to prevent TPM exhaustion
AZURE_SEMAPHORE = asyncio.Semaphore(int(os.environ.get("AZURE_MAX_CONCURRENCY", "2")))


async def _execute_azure_chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temp: float,
    max_tokens: int,
) -> str:
    """Executes a chat generation with Azure Foundry Anthropic endpoint with bounded concurrency."""
    api_key = os.environ.get("AZURE_API_KEY")
    if not api_key:
        raise RuntimeError("AZURE_API_KEY is not configured.")

    endpoint = os.environ.get(
        "AZURE_FOUNDRY_ENDPOINT",
        "https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages"
    ).strip()
    if not endpoint.endswith("/v1/messages"):
        endpoint = f"{endpoint.rstrip('/')}/v1/messages"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key.strip()}",
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_prompt + "\n\nCRITICAL: Respond ONLY with a valid JSON object matching the requested schema. Do not wrap in backticks or markdown fences.",
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
    }

    import httpx
    async with AZURE_SEMAPHORE:
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post(endpoint, headers=headers, json=payload)
            if r.status_code != 200:
                raise RuntimeError(f"Azure Foundry error {r.status_code}: {r.text}")
            data = r.json()
            if not isinstance(data, dict):
                raise RuntimeError(f"Azure Foundry returned non-dict response: {data}")

            # Check for error payload even if HTTP status was 200
            if "error" in data:
                err_obj = data["error"]
                msg = err_obj.get("message", str(err_obj)) if isinstance(err_obj, dict) else str(err_obj)
                raise RuntimeError(f"Azure Foundry API error: {msg}")

            content_items = data.get("content", [])
            text_blocks: List[str] = []
            if isinstance(content_items, list):
                for item in content_items:
                    if isinstance(item, dict):
                        if item.get("type") == "text" or "text" in item:
                            text_blocks.append(item.get("text", ""))
            elif isinstance(content_items, str):
                text_blocks.append(content_items)

            full_text = "".join(text_blocks).strip()
            if not full_text:
                if "message" in data and isinstance(data["message"], dict):
                    full_text = str(data["message"].get("content", "")).strip()
                elif "choices" in data and isinstance(data["choices"], list) and data["choices"]:
                    first_choice = data["choices"][0]
                    if isinstance(first_choice, dict) and "message" in first_choice:
                        full_text = str(first_choice["message"].get("content", "")).strip()

            if not full_text:
                raise RuntimeError(f"Azure Foundry returned empty content payload (keys: {list(data.keys())})")

            return full_text


async def _execute_iteracompute_chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temp: float,
    max_tokens: int,
) -> str:
    """Executes a chat generation with IteraCompute OpenAI-compatible API."""
    api_key = os.environ.get("ITERACOMPUTE_API_KEY")
    if not api_key:
        raise RuntimeError("ITERACOMPUTE_API_KEY is not configured.")

    base_url = os.environ.get("ITERACOMPUTE_BASE_URL", "https://api.iteracompute.com/v1").rstrip("/")
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }

    import httpx
    async with httpx.AsyncClient(timeout=130.0) as client:
        r = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"IteraCompute error {r.status_code}: {r.text}")
        data = r.json()
        return data["choices"][0]["message"]["content"] or ""


def _get_gemini_client():
    """Initializes Google GenAI Client from environment variables."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key or api_key.strip().startswith("your-") or api_key.strip().startswith("test-"):
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key.strip())
    except Exception as e:
        print(f"Failed to initialize Gemini client: {e}")
        return None


async def _execute_gemini_chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temp: float,
    max_tokens: int,
) -> str:
    """Executes a chat generation with Google Gemini using response_mime_type='application/json'."""
    client = _get_gemini_client()
    if not client:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    from google.genai import types

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=temp,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
    )

    def _call():
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=config,
        )
        return response.text or ""

    return await asyncio.to_thread(_call)


GROQ_FAST_TIER = "openai/gpt-oss-20b"
GROQ_MEDIUM_TIER = "openai/gpt-oss-20b"
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
    "plan": {"model": GROQ_MEDIUM_TIER, "system": PLAN_PROMPT, "temp": 0.1, "max_tokens": 800},
    "extract": {"model": GROQ_FAST_TIER, "system": EXTRACT_PROMPT, "temp": 0.0, "max_tokens": 4000},
    "gap": {"model": GROQ_FAST_TIER, "system": GAP_PROMPT, "temp": 0.0, "max_tokens": 800},
    "draft": {"model": GROQ_MEDIUM_TIER, "system": DRAFT_PROMPT, "temp": 0.1, "max_tokens": 3000},
    "synthesize": {"model": GROQ_REASONING_TIER, "system": SYNTHESIZE_PROMPT, "temp": 0.1, "max_tokens": 3000},
    "verify": {"model": GROQ_REASONING_TIER, "system": VERIFY_PROMPT, "temp": 0.0, "max_tokens": 1500},
    "repair": {"model": GROQ_MEDIUM_TIER, "system": REPAIR_PROMPT, "temp": 0.0, "max_tokens": 3500},
}


def _extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    """Robust parser that extracts JSON payload from markdown fences, raw strings, thinking blocks, or bare lists."""
    if not text:
        return {}

    # 1. Strip thinking blocks <thinking>...</thinking> or <thought>...</thought>
    cleaned = re.sub(r"<(?:thinking|thought)>[\s\S]*?</(?:thinking|thought)>", "", text).strip()
    if not cleaned:
        cleaned = text.strip()

    # 2. Try direct parse on cleaned text
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        elif isinstance(parsed, list):
            return {"items": parsed}
    except Exception:
        pass

    # 3. Try fenced json block ```json ... ```
    matches = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    for block in matches:
        try:
            parsed = json.loads(block.strip())
            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, list):
                return {"items": parsed}
        except Exception:
            pass

    # 4. Try outermost curly braces { ... }
    brace_start = cleaned.find("{")
    brace_end = cleaned.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        candidate = cleaned[brace_start:brace_end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            try:
                repaired = re.sub(r",\s*([\}\]])", r"\1", candidate)
                parsed = json.loads(repaired)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

    # 5. Try outermost brackets [ ... ] (bare list output)
    bracket_start = cleaned.find("[")
    bracket_end = cleaned.rfind("]")
    if bracket_start != -1 and bracket_end > bracket_start:
        candidate_arr = cleaned[bracket_start:bracket_end + 1]
        try:
            parsed = json.loads(candidate_arr)
            if isinstance(parsed, list):
                return {"items": parsed}
        except Exception:
            try:
                repaired = re.sub(r",\s*([\}\]])", r"\1", candidate_arr)
                parsed = json.loads(repaired)
                if isinstance(parsed, list):
                    return {"items": parsed}
            except Exception:
                pass

    return {}


async def run_role(
    role: str,
    user_input: str,
    *,
    model_override: Optional[str] = None,
    provider_override: Optional[str] = None,
    fallback_model_override: Optional[str] = None,
    mock_response: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes a role using the active LLM provider (gpt-oss, qwen, gemini, iteracompute, or azure) with strict JSON schema outputs.
    Falls back gracefully to mock payloads for tests or offline execution.
    Supports automatic 429 TPM rate-limit failover to secondary/fallback models (e.g. claude-sonnet-4-6).
    """
    if role not in ROLES_CONFIG:
        raise ValueError(f"Unknown role '{role}'. Valid roles: {list(ROLES_CONFIG.keys())}")

    cfg = ROLES_CONFIG[role]
    active_prov = (provider_override or ACTIVE_PROVIDER).lower()
    prov_models = PROVIDER_MODELS.get(active_prov, PROVIDER_MODELS["gpt-oss"])
    role_tier = ROLE_TIER_MAPPING.get(role, "medium")
    selected_model = model_override or prov_models.get(role_tier, "openai/gpt-oss-20b")
    active_fallback = fallback_model_override or ACTIVE_FALLBACK_MODEL or (
        os.environ.get("AZURE_FALLBACK_MODEL", "claude-sonnet-4-6") if active_prov in ["azure", "azure-foundry", "foundry"] else None
    )

    # If mock_response is provided explicitly
    if mock_response is not None:
        return mock_response

    is_testing = os.environ.get("TESTING") == "true" or os.environ.get("MOCK_GROQ") == "true"
    if is_testing:
        return _generate_mock_role_output(role, user_input)

    # Dispatch to Google Gemini
    if active_prov == "gemini":
        gemini_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not gemini_api_key or gemini_api_key.startswith("your-") or gemini_api_key.startswith("test-"):
            if is_testing and os.environ.get("ALLOW_MOCK_DATA") == "true":
                return _generate_mock_role_output(role, user_input)
            raise RuntimeError("GEMINI_API_KEY is not configured or invalid.")

        models_sequence = [selected_model]
        if active_fallback and active_fallback != selected_model:
            models_sequence.append(active_fallback)

        system_p = cfg["system"] + "\n\nRespond ONLY with a valid JSON object matching the required schema."
        last_gemini_error = ""
        for m_idx, current_model in enumerate(models_sequence):
            is_fallback = (m_idx > 0)
            max_attempts = 2 if len(models_sequence) > 1 else 3
            for attempt in range(max_attempts):
                try:
                    content = await _execute_gemini_chat(
                        model=current_model,
                        system_prompt=system_p,
                        user_prompt=user_input,
                        temp=cfg["temp"],
                        max_tokens=cfg["max_tokens"],
                    )
                    parsed = _extract_json_from_llm_response(content)
                    if parsed:
                        if is_fallback:
                            print(f"[FALLBACK SUCCESS] Role '{role}' succeeded with fallback model '{current_model}'")
                        return parsed
                    last_gemini_error = f"Model '{current_model}' returned unparseable or empty JSON response (length={len(content)})."
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    break
                except Exception as e:
                    last_gemini_error = str(e)
                    err_msg = str(e).lower()
                    if ("rate limit" in err_msg or "429" in err_msg) and not is_fallback and len(models_sequence) > 1:
                        print(f"[RATE LIMIT 429] Role '{role}' hit rate limit on '{current_model}'. Failing over to fallback model '{models_sequence[1]}'...")
                        break
                    if ("rate limit" in err_msg or "429" in err_msg or "503" in err_msg or "unavailable" in err_msg) and attempt < max_attempts - 1:
                        await asyncio.sleep(2.0 * (attempt + 1))
                        continue
                    print(f"Role '{role}' Gemini execution note ({current_model}): {e}")
                    break
        if is_testing and os.environ.get("ALLOW_MOCK_DATA") == "true":
            return _generate_mock_role_output(role, user_input)
        raise RuntimeError(f"Role '{role}' Gemini execution failed across models {models_sequence}: {last_gemini_error}")

    # Dispatch to IteraCompute (OpenAI-compatible)
    if active_prov in ["iteracompute", "itera"]:
        itera_key = os.environ.get("ITERACOMPUTE_API_KEY")
        if not itera_key or itera_key.startswith("your-") or itera_key.startswith("test-"):
            if is_testing and os.environ.get("ALLOW_MOCK_DATA") == "true":
                return _generate_mock_role_output(role, user_input)
            raise RuntimeError("ITERACOMPUTE_API_KEY is not configured or invalid.")

        models_sequence = [selected_model]
        if active_fallback and active_fallback != selected_model:
            models_sequence.append(active_fallback)

        system_p = cfg["system"] + "\n\nRespond ONLY with a valid JSON object matching the required schema."
        last_itera_error = ""
        for m_idx, current_model in enumerate(models_sequence):
            is_fallback = (m_idx > 0)
            max_attempts = 2 if len(models_sequence) > 1 else 3
            for attempt in range(max_attempts):
                try:
                    content = await _execute_iteracompute_chat(
                        model=current_model,
                        system_prompt=system_p,
                        user_prompt=user_input,
                        temp=cfg["temp"],
                        max_tokens=cfg["max_tokens"],
                    )
                    parsed = _extract_json_from_llm_response(content)
                    if parsed:
                        if is_fallback:
                            print(f"[FALLBACK SUCCESS] Role '{role}' succeeded with fallback model '{current_model}'")
                        return parsed
                    last_itera_error = f"Model '{current_model}' returned unparseable or empty JSON response (length={len(content)})."
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    break
                except Exception as e:
                    last_itera_error = str(e)
                    err_msg = str(e).lower()
                    if ("rate limit" in err_msg or "429" in err_msg) and not is_fallback and len(models_sequence) > 1:
                        print(f"[RATE LIMIT 429] Role '{role}' hit rate limit on '{current_model}'. Failing over to fallback model '{models_sequence[1]}'...")
                        break
                    if ("rate limit" in err_msg or "429" in err_msg or "503" in err_msg or "timeout" in err_msg) and attempt < max_attempts - 1:
                        await asyncio.sleep(2.0 * (attempt + 1))
                        continue
                    print(f"Role '{role}' IteraCompute execution note ({current_model}): {e}")
                    break
        if is_testing and os.environ.get("ALLOW_MOCK_DATA") == "true":
            return _generate_mock_role_output(role, user_input)
        raise RuntimeError(f"Role '{role}' IteraCompute execution failed across models {models_sequence}: {last_itera_error}")

    # Dispatch to Azure Foundry (Anthropic claude-opus-4-8 / claude-sonnet-4-6 fallback)
    if active_prov in ["azure", "azure-foundry", "foundry"]:
        azure_key = os.environ.get("AZURE_API_KEY")
        if not azure_key or azure_key.startswith("your-") or azure_key.startswith("test-"):
            if is_testing and os.environ.get("ALLOW_MOCK_DATA") == "true":
                return _generate_mock_role_output(role, user_input)
            raise RuntimeError("AZURE_API_KEY is not configured or invalid.")

        models_sequence = [selected_model]
        if active_fallback and active_fallback != selected_model:
            models_sequence.append(active_fallback)

        system_p = cfg["system"] + "\n\nRespond ONLY with a valid JSON object matching the required schema."
        last_azure_error = ""
        max_outer_rounds = 1 if is_testing else int(os.environ.get("AZURE_MAX_RETRY_ROUNDS", "5"))
        base_wait_seconds = int(os.environ.get("AZURE_RETRY_WAIT_SECONDS", "25"))

        for round_idx in range(max_outer_rounds):
            for m_idx, current_model in enumerate(models_sequence):
                is_fallback = (m_idx > 0)
                max_attempts = 2 if len(models_sequence) > 1 else 3
                for attempt in range(max_attempts):
                    try:
                        content = await _execute_azure_chat(
                            model=current_model,
                            system_prompt=system_p,
                            user_prompt=user_input,
                            temp=cfg["temp"],
                            max_tokens=cfg["max_tokens"],
                        )
                        parsed = _extract_json_from_llm_response(content)
                        if parsed:
                            if is_fallback or round_idx > 0:
                                print(f"[AZURE SUCCESS] Role '{role}' succeeded with model '{current_model}' (round {round_idx + 1}/{max_outer_rounds})", flush=True)
                            return parsed

                        # Response could not be parsed into a valid JSON object
                        last_azure_error = f"Model '{current_model}' returned unparseable or empty JSON response (length={len(content)}). Content preview: {repr(content[:250])}"
                        print(f"[AZURE PARSE RETRY] Role '{role}' ({current_model}) attempt {attempt + 1}/{max_attempts}: {last_azure_error}", flush=True)
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(1.5 * (attempt + 1))
                            continue
                        break
                    except Exception as e:
                        last_azure_error = str(e)
                        err_msg = str(e).lower()
                        if ("rate limit" in err_msg or "429" in err_msg or "token" in err_msg) and not is_fallback and len(models_sequence) > 1:
                            print(f"[RATE LIMIT 429] Role '{role}' hit TPM rate limit on '{current_model}'. Failing over to fallback model '{models_sequence[1]}'...", flush=True)
                            break
                        if ("rate limit" in err_msg or "429" in err_msg or "503" in err_msg or "timeout" in err_msg) and attempt < max_attempts - 1:
                            await asyncio.sleep(2.0 * (attempt + 1))
                            continue
                        print(f"Role '{role}' Azure Foundry execution note ({current_model}): {e}", flush=True)
                        break

            # If all models in sequence failed in this round, check if retryable before waiting
            if round_idx < max_outer_rounds - 1:
                is_retryable = any(
                    kw in last_azure_error.lower()
                    for kw in [
                        "rate limit", "429", "token", "tpm", "quota", "overloaded",
                        "capacity", "500", "502", "503", "504", "timeout",
                        "connection", "temporarily", "service unavailable", "gateway",
                        "call failed", "unparseable", "empty json", "parse", "empty content",
                        "json response"
                    ]
                )
                if not is_retryable:
                    print(f"[AZURE NON-RETRYABLE] Non-transient error for role '{role}': {last_azure_error}. Aborting retry loop.", flush=True)
                    break

                wait_seconds = base_wait_seconds + (round_idx * 10)
                print(
                    f"\n[AZURE RATE LIMIT COOLDOWN] Role '{role}' exhausted model sequence ({last_azure_error}).\n"
                    f"[AZURE RATE LIMIT COOLDOWN] Pausing {wait_seconds}s for token quota reset before round {round_idx + 2}/{max_outer_rounds}...",
                    flush=True,
                )

                elapsed = 0
                step = 5
                while elapsed < wait_seconds:
                    sleep_time = min(step, wait_seconds - elapsed)
                    await asyncio.sleep(sleep_time)
                    elapsed += sleep_time
                    remaining = wait_seconds - elapsed
                    pct = int((elapsed / wait_seconds) * 100)
                    bar_filled = "#" * (pct // 5)
                    bar_empty = "-" * (20 - (pct // 5))
                    if remaining > 0:
                        print(
                            f"  ⏳ [AZURE COOLDOWN] Role '{role}': [{bar_filled}{bar_empty}] {elapsed}s/{wait_seconds}s ({pct}%) — retrying in {remaining}s...",
                            flush=True,
                        )
                    else:
                        print(
                            f"  ✅ [AZURE COOLDOWN COMPLETE] Role '{role}': Cooldown finished ({wait_seconds}s elapsed). Retrying request with model '{models_sequence[0]}'...\n",
                            flush=True,
                        )

        if is_testing and os.environ.get("ALLOW_MOCK_DATA") == "true":
            return _generate_mock_role_output(role, user_input)
        raise RuntimeError(f"Role '{role}' Azure Foundry execution failed across models {models_sequence} after {max_outer_rounds} retry rounds: {last_azure_error}")

    # Dispatch to Groq LPUs (gpt-oss or qwen)
    groq_client, _ = get_groq_client()
    if not groq_client or not is_groq_configured():
        if is_testing and os.environ.get("ALLOW_MOCK_DATA") == "true":
            return _generate_mock_role_output(role, user_input)
        raise RuntimeError("Groq client is not configured.")

    models_sequence = [selected_model]
    if active_fallback and active_fallback != selected_model:
        models_sequence.append(active_fallback)

    # Live Groq API Execution with retry for transient rate limits and fallback failover
    last_groq_error = ""
    for m_idx, current_model in enumerate(models_sequence):
        is_fallback = (m_idx > 0)
        max_attempts = 2 if len(models_sequence) > 1 else 3
        for attempt in range(max_attempts):
            try:
                content, _, _, _, _ = execute_groq_chat(
                    client=groq_client,
                    messages=[{"role": "user", "content": user_input}],
                    system_prompt=cfg["system"] + "\n\nRespond ONLY with a valid JSON object matching the required schema.",
                    requested_model=current_model,
                    temperature=cfg["temp"],
                    max_completion_tokens=cfg["max_tokens"],
                )
                parsed = _extract_json_from_llm_response(content)
                if parsed:
                    if is_fallback:
                        print(f"[FALLBACK SUCCESS] Role '{role}' succeeded on Groq with fallback model '{current_model}'")
                    return parsed
                last_groq_error = f"Model '{current_model}' returned unparseable or empty JSON response (length={len(content)})."
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                break
            except Exception as e:
                last_groq_error = str(e)
                err_msg = str(e).lower()
                if ("rate limit" in err_msg or "429" in err_msg) and not is_fallback and len(models_sequence) > 1:
                    print(f"[RATE LIMIT 429] Role '{role}' hit Groq rate limit on '{current_model}'. Failing over to fallback model '{models_sequence[1]}'...")
                    break
                if ("rate limit" in err_msg or "429" in err_msg) and attempt < max_attempts - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                print(f"Role '{role}' Groq execution note ({current_model}): {e}")
                break

    # Fallback to deterministic mock in test mode only when explicitly allowed
    if is_testing and os.environ.get("ALLOW_MOCK_DATA") == "true":
        return _generate_mock_role_output(role, user_input)
    raise RuntimeError(f"Role '{role}' Groq execution failed across models {models_sequence}: {last_groq_error}")


async def run_role_with_timings(
    role: str,
    user_input: str,
    *,
    model_override: Optional[str] = None,
    provider_override: Optional[str] = None,
    fallback_model_override: Optional[str] = None,
    mock_response: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Executes a role using the active LLM provider and captures exact execution latency.
    """
    active_prov = (provider_override or ACTIVE_PROVIDER).lower()
    prov_models = PROVIDER_MODELS.get(active_prov, PROVIDER_MODELS["gpt-oss"])
    role_tier = ROLE_TIER_MAPPING.get(role, "medium")
    model_used = model_override or prov_models.get(role_tier, "unknown")
    active_fallback = fallback_model_override or ACTIVE_FALLBACK_MODEL or (
        os.environ.get("AZURE_FALLBACK_MODEL", "claude-sonnet-4-6") if active_prov in ["azure", "azure-foundry", "foundry"] else None
    )

    t0 = time.perf_counter()
    result = await run_role(
        role,
        user_input,
        model_override=model_override,
        provider_override=provider_override,
        fallback_model_override=fallback_model_override,
        mock_response=mock_response
    )
    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    meta = {
        "duration_ms": duration_ms,
        "role": role,
        "model": model_used,
        "provider": active_prov,
        "fallback_model": active_fallback,
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
        return _generate_mock_draft(user_input)
    elif role == "synthesize":
        return {
            "executive_summary": (
                "This Public Risk Underwriting Report evaluates the comprehensive risk profile of the target enterprise "
                "through an institutional D&O underwriter lens. The analysis indicates a fortress balance sheet featuring "
                "over $60B in total liquidity, stellar AAA/AA+ credit ratings, exceptional free cash flow generation, "
                "and an exemplary corporate governance framework characterized by 88.9% independent board oversight. "
                "Historical securities class action frequency is negligible, with zero active class actions and zero "
                "financial statement restatements in the trailing seven years. Primary underwriting attention is focused on "
                "ongoing Department of Justice and European antitrust regulatory inquiries, as well as operational "
                "dependency on Taiwanese semiconductor foundries (TSMC)."
            ),
            "risk_tier": "Contained",
            "band_register": {
                "financial": "Contained",
                "governance": "Contained",
                "sca_likelihood": "Contained",
                "sca_severity": "Contained",
                "side_a_side_c": "Contained / Contained",
                "legal_regulatory": "Elevated",
                "esg_cyber_ops": "Contained",
                "forward_looking": "Contained"
            },
            "verdict_text": (
                "## OVERALL D&O UNDERWRITER VERDICT\n\n"
                "### Underwriter Headline\n"
                "- Well-capitalized enterprise with fortress balance sheet liquidity, mature internal governance controls, and minimal securities litigation history.\n"
                "- Primary underwriting exposure concentrated in ongoing global antitrust regulatory scrutiny and single-source advanced semiconductor foundry dependencies.\n\n"
                "### Dominant Risk Driver\n"
                "- Primary underwriting risk is driven by **Strategic & Operational Profile** and **Legal & Regulatory Claims**, specifically geopolitical foundry concentration and antitrust litigation.\n\n"
                "### D&O Exposure Band Register\n"
                "| Risk Dimension | Assigned Band | Primary Evidence Driver |\n"
                "| :--- | :--- | :--- |\n"
                "| **Financial Overview** | **Contained** | $61.5B total liquidity; AA+ credit ratings; positive operating cash flow [E003] |\n"
                "| **Governance & Culture** | **Contained** | 88.9% independent board; separate Chair/CEO; robust clawbacks [E002] |\n"
                "| **SCA Likelihood** | **Contained** | Zero active class actions; no restatements in 7 years [E001] |\n"
                "| **SCA Severity** | **Contained** | Low historical loss frequency; robust disclosure controls [E004] |\n"
                "| **Side A / Side C Exposure** | **Contained / Contained** | Corporate indemnification robust; excess tower untouched [E005] |\n"
                "| **Legal & Regulatory Claims** | **Elevated** | Ongoing DOJ and EU antitrust inquiries into ecosystem practices [E002] |\n"
                "| **ESG, Cyber & Operational** | **Contained** | Zero Item 1.05 cyber breaches; negligible environmental risk [E001] |\n"
                "| **Forward-Looking Strategic Risk** | **Contained** | Managed product roadmap; gross margins sustained at 44% [E005] |\n\n"
                "### Final D&O Underwriting Verdict\n"
                "- **Overall Underwriting Risk Tier:** `CONTAINED` (Data Confidence: Strong)\n"
                "- **Tensions:** High operational dependency on TSMC vs. fortress balance sheet liquidity mitigating business interruption losses.\n"
                "- **Unknowns:** Long-term remedies or structural modifications resulting from multi-jurisdiction antitrust proceedings.\n"
                "- *Assessment based solely on public information and regulatory filings contained in this report.*"
            )
        }
    elif role == "verify":
        return {"issues": []}
    elif role == "repair":
        return {"patched_text": user_input}

    return {}


def _generate_mock_draft(user_input: str) -> Dict[str, Any]:
    co_match = re.search(r"TARGET COMPANY:\s*([^(\n]+)", user_input)
    co_name = co_match.group(1).strip() if co_match else "Target Enterprise"
    tk_match = re.search(r"Ticker:\s*([^,\)\n]+)", user_input)
    ticker = tk_match.group(1).strip() if tk_match else "TKR"
    cik_match = re.search(r"CIK:\s*([^,\)\n]+)", user_input)
    cik = cik_match.group(1).strip() if cik_match else "0000000000"
    dom_match = re.search(r"Domicile:\s*([^,\)\n]+)", user_input)
    domicile = dom_match.group(1).strip() if dom_match else "United States"
    ex_match = re.search(r"Exchange:\s*([^,\)\n]+)", user_input)
    exchange = ex_match.group(1).strip() if ex_match else "NASDAQ"

    slug_match = re.search(r"SECTION SLUG:\s*([a-z0-9_]+)", user_input, re.IGNORECASE)
    slug = slug_match.group(1).lower().strip() if slug_match else ""

    header_match = re.search(r"SECTION HEADER:\s*###\s*(.+)", user_input, re.IGNORECASE)
    header = header_match.group(1).strip().lower() if header_match else ""

    u_lower = user_input.lower()

    if slug == "company_snapshot" or "company snapshot" in header or ("snapshot" in u_lower and "section name: company_snapshot" in u_lower):
        citations = [f"E{i:03d}" for i in range(1, 15)]
        text = (
            f"### COMPANY SNAPSHOT\n"
            f"- Legal name: {co_name} [E001]; incorporated under the laws of the State of Delaware; SEC CIK: {cik}; primary trading exchange: {exchange} [E001]\n"
            f"- Business description: {co_name} operates across core technology, infrastructure, enterprise computing platforms, and advanced software ecosystems [E001]\n"
            f"- HQ + footprint: Corporate headquarters located in {domicile}; supported by global administrative hubs, technical design facilities, and regional commercial operations [E002]\n"
            f"- U.S. Exposure: Domiciled and organized under United States jurisdiction; primary executive management, core intellectual property, and SEC reporting framework reside in the U.S. [E002]\n"
            f"- Country of domicile: {domicile} — single sovereign legal registration and regulatory domicile [E002]\n"
            f"- Corruption Perception Index (CPI) Score: United States — 69/100, rank 24, CPI 2023 (source: Transparency International) [E003]\n"
            f"- Listing(s) + ticker(s): Common stock registered under Section 12(b) of the Securities Exchange Act of 1934, traded on {exchange} under ticker symbol {ticker} [E001]\n"
            f"- Market cap: $2.50 trillion as of November 02, 2026 based on official exchange closing price [E004]\n"
            f"- Share price: $185.50 at market close on November 02, 2026 vs $142.10 one year prior (+30.5% 52-week change) [E004]\n"
            f"- Total Assets: $150.00 billion as reported in the most recent consolidated regulatory balance sheet filing [E005]\n"
            f"- Revenue: Latest reported fiscal year consolidated revenue of $120.00 billion reflecting robust annual operating expansion [E006]\n"
            f"- Capital structure: Conservative capital structure comprising $15.0B in senior unsecured notes and extensive stockholders' equity cushion [E006]\n"
            f"- Trading liquidity: High average daily trading volume with deep institutional market liquidity on {exchange} [E004]\n"
            f"- Analyst sentiment (most recent 3–6 months): Overwhelmingly constructive consensus across major institutional brokerages [E007]\n"
            f"- Governance snapshot: Large accelerated filer governed by an independent board of directors with standing oversight committees [E008]\n"
            f"- Exposure to crypto, cannabis, or coal: Not found in public disclosures / Not publicly available [E009]\n"
            f"- AI Exposure to revenue and valuations: Material to enterprise platform architecture, accelerated computing systems, and developer software ecosystems [E010]\n"
            f"- Conclusion:\n"
            f"  - Core corporate standing, listing integrity, and public regulatory disclosures fully verified across SEC EDGAR filings [E001]\n"
            f"  - Contained"
        )
    elif slug == "news_updates" or "updates" in header or "news & recent developments" in header or "updates / press releases / news" in header:
        citations = [f"E{i:03d}" for i in range(1, 12)]
        text = (
            f"### UPDATES / PRESS RELEASES / NEWS\n"
            f"- 15-Aug-2026 - {co_name} reported quarterly earnings meeting consensus expectations with top-line growth across core enterprise platforms - [Guidance/Earnings] - Confirms operating execution and revenue trajectory - SEC Form 8-K [E001]\n"
            f"- 10-May-2026 - Board of directors authorized expanded share repurchase program and declared regular quarterly cash dividend - [Capital Allocation] - Demonstrates capital return discipline and strong liquidity buffer - Company Press Release [E002]\n"
            f"- 28-Feb-2026 - Filed Annual Report on Form 10-K confirming zero accounting restatements and robust internal controls over financial reporting - [Periodic Filing] - Confirms financial reporting integrity and clean audit opinion - SEC Form 10-K [E003]\n"
            f"- 14-Jan-2026 - Announced next-generation enterprise hardware and software architecture roadmap at industry symposium - [Product Innovation] - Reaffirms technological leadership and competitive moat - Press Release [E004]\n"
            f"- Adverse Securities Litigation Filings: None filed during trailing 12 months; historical legacy dockets remain inactive or dismissed [E005]\n"
            f"- Independent Auditor Changes: Checked: Unchanged. Independent registered public accounting firm continues with unqualified audit opinion [E006]\n"
            f"- Executive Departures & Governance Shakes: Checked: Stable C-suite tenure with zero unplanned or involuntary executive officer departures [E007]\n"
            f"- Final Section Risk Band: Contained (Data Confidence: Strong)"
        )
    elif slug == "financial_overview" or "financial" in header:
        citations = [f"E{i:03d}" for i in range(1, 15)]
        text = (
            f"### FINANCIAL OVERVIEW\n"
            f"Snapshot (Reporting Period: FY2026, Currency: USD): Revenue $120.00B [E001] | Cash Flow from Operations $35.00B (prior year: $28.00B) [E002] | Total assets $150.00B [E003] | Total liabilities $45.00B [E004] | Current assets $60.00B [E005] | Current liabilities $20.00B [E006] | Cash & equivalents $25.00B [E007] | Net worth $105.00B [E008] | Working capital $40.00B [E009]\n"
            f"\n"
            f"- Revenue trend: FY2026 $120.00B | FY2025 $95.00B | FY2024 $75.00B | FY2023 $60.00B representing sustained multi-year top-line momentum [E001]\n"
            f"- Profitability durability: Operating margins sustained above 50% across trailing fiscal periods with exceptional cash conversion efficiency [E002]\n"
            f"- Cash & liquidity: Total enterprise cash and marketable securities of $25.00B provide exceptional balance sheet fortress liquidity [E007]\n"
            f"- Leverage + refinancing: Total debt $15.0B; staggered maturity schedule with interest coverage ratio exceeding 25x operating earnings [E004]\n"
            f"- Earnings quality: Free cash flow conversion exceeding 90% supports reported net earnings with zero aggressive revenue recognition signs [E002]\n"
            f"- Balance sheet flexibility: Total stockholders' equity of $105.00B and positive working capital of $40.00B ensure substantial underwriting buffer [E008][E009]\n"
            f"- Credit rating: Investment grade senior unsecured ratings: S&P: AA (Stable); Moody's: Aa2 (Stable) [E007]\n"
            f"- Macro resilience: Diversified enterprise end-markets and global customer base provide durability against cyclical macroeconomic headwinds [E001]\n"
            f"- Auditor assessment: Independent registered public accounting firm rendered an unqualified audit opinion with zero material weaknesses in internal control [E003]\n"
            f"- Debt & Refinancing Profile (Reporting Period: FY2026, Currency: USD)\n"
            f"  * Total debt (gross): $15.0B | Maturities: <12m $1.5B | Year 2 $2.0B | Year 3 $2.5B | Thereafter $9.0B\n"
            f"  * Revolving credit facilities: $5.0B undrawn committed facility | Commercial paper: active tier-1 access | Interest structure: 90% fixed, 10% floating | Coupon range: 1.50% - 3.85% | Covenants: standard non-restrictive negative pledges\n"
            f"- Conclusion:\n"
            f"  * Exceptionally strong balance sheet fundamentals and cash generation profile support underwriting stability [E001]\n"
            f"  * Contained"
        )
    elif slug == "analysts" or "analyst" in header:
        citations = [f"E{i:03d}" for i in range(1, 10)]
        text = (
            f"### ANALYSTS\n"
            f"- Wall Street Analyst Ratings Breakdown: 45 covering research analysts; 38 Buy (84.4%), 6 Hold (13.3%), 1 Sell (2.2%) [E001]\n"
            f"- Consensus Mean Price Target: $220.00 (range: $175.00 – $280.00), representing implied 12-month upside of +18.6% [E002]\n"
            f"- Stock Beta & Relative Volatility: 5-year monthly Beta of 1.25; 52-week trading range $135.00 – $210.00 reflecting normal sector beta [E003]\n"
            f"- Short Interest: 1.1% of public float with days-to-cover ratio of 1.8 days, indicating low short seller scrutiny [E004]\n"
            f"- Recent Upgrades / Downgrades: Major Wall Street brokerages reiterate overweight/buy stances citing multi-year enterprise demand visibility [E005]\n"
            f"- Valuation Multiples: Forward P/E of 28.5x and EV/EBITDA of 22.0x reflect premium technology sector valuation grounded in fundamental cash flow [E006]\n"
            f"- Conclusion:\n"
            f"  * Overwhelmingly constructive institutional consensus conviction with negligible short pressure and healthy price discovery [E001]\n"
            f"  * Contained"
        )
    elif slug == "governance_culture" or "governance" in header:
        citations = [f"E{i:03d}" for i in range(1, 12)]
        text = (
            f"### GOVERNANCE & CULTURE\n"
            f"- Board Independence: 11 active directors; 10 independent directors (90.9% independence level) under exchange listing standards [E001]\n"
            f"- Board Leadership Structure: Lead Independent Director model ensures robust oversight independent of executive management [E002]\n"
            f"- 5-Year Governance Drift: Fully declassified board with annual elections for all directors, majority voting standard, and active refreshment [E003]\n"
            f"- Audit Committee Strength: All audit committee members designated as financial experts under SEC regulations; meets regularly in executive session [E004]\n"
            f"- CEO/CFO Turnover: Stable executive stewardship with long-tenured leadership and zero unplanned executive officer turnover [E005]\n"
            f"- Related-Party/Complexity: Zero material related-party transactions reported in recent annual proxy filings [E006]\n"
            f"- Disclosure Discipline: Transparent corporate disclosures with active board-level risk management and formal clawback policies [E007]\n"
            f"- Committee Composition: Standing Compensation, Nominating, and Audit Committees composed 100% of independent directors [E008]\n"
            f"- Conclusion:\n"
            f"  * Mature governance infrastructure, high board independence, and conservative structural oversight safeguards [E001]\n"
            f"  * Contained"
        )
    elif slug == "director_officer_history" or "director" in header or "officer" in header:
        citations = [f"E{i:03d}" for i in range(1, 10)]
        text = (
            f"### DIRECTOR & OFFICER HISTORY\n"
            f"- Chief Executive Officer (CEO): Active executive tenure; exemplary corporate background with zero civil fraud findings or regulatory reprimands [E001]\n"
            f"- Chief Financial Officer (CFO): Active financial stewardship; clean regulatory record with zero historical restatements or disclosure inquiries [E002]\n"
            f"- Lead Independent Director: Experienced public company governance leader; clean litigation and regulatory background [E003]\n"
            f"- Audit Committee Chair: Former partner at a major public accounting firm; clean regulatory and professional record [E004]\n"
            f"- SEC Officer/Director Disqualification Verification: Systematic search returned zero disqualifications under Rule 506(d) or SEC enforcement dockets [E005]\n"
            f"- Professional Backgrounds: All executive officers and directors demonstrate extensive industry tenure and high reputational standing [E006]\n"
            f"- No matters identified within scope for any individual reviewed [E001]\n"
            f"- Conclusion:\n"
            f"  * Executive leadership record is clean with zero adverse regulatory orders, civil judgments, or disqualifying events [E001]\n"
            f"  * Contained"
        )
    elif slug == "strategic_operational_profile" or "strategic" in header:
        citations = [f"E{i:03d}" for i in range(1, 10)]
        text = (
            f"### STRATEGIC & OPERATIONAL PROFILE\n"
            f"- Sector Position: Leading global market position in core enterprise technology and infrastructure platforms supported by proprietary moats [E001]\n"
            f"- Execution Capability: Proven manufacturing scale, disciplined capital expenditure allocation, and rigorous operational control [E002]\n"
            f"- Concentration Risk: Broad enterprise customer base with top commercial accounts diversified across industries and geographic regions [E003]\n"
            f"- Regulatory Exposure: Fully compliant with international trade regulations, export licensing frameworks, and global standards [E004]\n"
            f"- Key-Man Dependency: Experienced management bench supported by formal board-supervised executive succession planning frameworks [E005]\n"
            f"- Cyber/Operational Risk: Robust enterprise cybersecurity architecture, ISO-certified protocols, and continuous disaster recovery planning [E006]\n"
            f"- R&D Investment: Material multi-billion annual reinvestment into proprietary software, silicon development, and intellectual property [E007]\n"
            f"- Conclusion:\n"
            f"  * Resilient competitive positioning, deep technological moats, and diversified operational relationships [E001]\n"
            f"  * Contained"
        )
    elif slug == "securities_class_action_risk" or "securities" in header or "class action" in header:
        citations = [f"E{i:03d}" for i in range(1, 12)]
        text = (
            f"### SECURITIES CLASS ACTION RISK\n"
            f"JURISDICTION - ONE LINE. Primary listing on {exchange} with deep US domestic investor base; US federal securities jurisdiction applies directly. [E001]\n"
            f"LIKELIHOOD\n"
            f"- Stable financial reporting history and consistent quarterly guidance framing mitigate event-driven stock drop vulnerability across market cycles. [E002]\n"
            f"- Zero accounting restatements, formal SEC inquiries, or auditor disagreements in trailing 36 months constrain plaintiff bar traction. [E003]\n"
            f"- Band: Contained\n"
            f"MOST LIKELY ALLEGATION TYPE. If a claim were brought, the most likely theory would be event-driven disclosure around supply chain delivery timelines or customer milestone dependencies. [E004]\n"
            f"SEVERITY IF BROUGHT\n"
            f"- Substantial public market capitalization provides deep free float, but absence of historical multi-day share price collapse bounds theoretical aggregate damages. [E005]\n"
            f"- Band: Contained\n"
            f"SIDE A / SIDE C EXPOSURE\n"
            f"- Side C: Substantial US institutional investor base and high market liquidity — Band: Contained [E006]\n"
            f"- Side A: Robust corporate balance sheet liquidity, broad indemnification bylaws, and negligible insolvency risk — Band: Contained [E007]\n"
            f"TOWER INTERACTION. Where a realistic claim attaches and how far it burns: primary layer attachment remote; Side A breach: Remote given fortress liquidity reserves and clean governance history. [E008]\n"
            f"SCENARIO, MAX 2 LINES. Severe operational delivery disruption triggers unexpected quarterly revenue miss > plaintiffs allege disclosure lag > commercial resolution contained below excess tower. [E009]\n"
            f"CONCLUSION: Core disclosure disciplines, conservative guidance, and fortress balance sheet strength insulate target from systemic securities class action claims. Final band: Contained (data confidence: Strong)."
        )
    elif slug == "legal_regulatory_claims" or "legal" in header or "claims" in header:
        citations = [f"E{i:03d}" for i in range(1, 10)]
        text = (
            f"### LEGAL, REGULATORY & CLAIMS CONTEXT\n"
            f"- Federal Civil Docket Review (CourtListener / PACER): Trailing 24 months discloses ordinary-course commercial contract and intellectual property litigation; zero default judgments or contempt orders [E001]\n"
            f"- Regulatory Enforcement & Orders: Form 10-K Item 3 disclosures confirm zero active SEC formal investigation orders, Wells Notices, or accounting subpoenas [E002]\n"
            f"- Antitrust & Competition Inquiries: No formal adverse adjudications or blocking injunctions issued by domestic or international antitrust authorities [E003]\n"
            f"- Whistleblower Claims & Sanctions Enforcement: Zero reported OSHA/SEC whistleblower retaliation claims; zero Office of Foreign Assets Control (OFAC) penalties or sanctions violations [E004]\n"
            f"- US Exposure: Primary corporate and operational activities centered in US federal jurisdiction; governed by federal judicial standards [E005]\n"
            f"- Sanctions: Zero operational exposure to sanctioned territories, blocked persons, or restricted foreign entities [E006]\n"
            f"- Intellectual Property Litigation: Defense of core proprietary patents handled as normal-course operational overhead without material financial exposure [E007]\n"
            f"- Conclusion:\n"
            f"  * Legal and regulatory claims remain within normal commercial bounds with no systemic D&O loss vector identified [E001]\n"
            f"  * Contained"
        )
    elif slug == "esg_cyber_operational" or "esg" in header or "cyber" in header:
        citations = [f"E{i:03d}" for i in range(1, 10)]
        text = (
            f"### ESG, CYBER & OPERATIONAL EXPOSURE\n"
            f"- ESG Controversy Velocity: Zero material toxic release violations or hazardous substance enforcement actions exceeding SEC disclosure thresholds [E001]\n"
            f"- Cyber Disclosure Quality: Item 1C compliant cybersecurity risk disclosures with board-level oversight; zero material 8-K Item 1.05 breach notifications [E002]\n"
            f"- Product/Safety Exposure: Negligible product liability or safety hazard recall history in public regulatory databases [E003]\n"
            f"- Supply Chain Fragility: Multi-vendor sourcing strategy reduces single-point manufacturing bottlenecks and operational exposure [E004]\n"
            f"- Data Privacy & Compliance: Full adherence to global data privacy regulations and security certifications [E005]\n"
            f"- Operational Continuity: Redundant enterprise infrastructure and multi-zone data center configurations maintain operational resilience [E006]\n"
            f"- Conclusion:\n"
            f"  * Manageable ESG profile, mature cybersecurity governance structure, and reliable business continuity architecture [E001]\n"
            f"  * Contained"
        )
    elif slug == "forward_looking_risk" or "forward" in header:
        citations = [f"E{i:03d}" for i in range(1, 10)]
        text = (
            f"### FORWARD-LOOKING STRATEGIC RISK\n"
            f"- Near-Term Catalysts: Upcoming product cycle introductions, architecture refreshes, and enterprise platform expansion [E001]\n"
            f"- Macro/Sector Pressure: Global hardware and enterprise infrastructure demand cycles managed through disciplined supply chain planning [E002]\n"
            f"- Execution Vulnerabilities: Complex multi-tier supply chain execution remains primary operational dependency [E003]\n"
            f"- Regulatory Shifts: Continual monitoring of global trade policies, export licensing frameworks, and international tariff developments [E004]\n"
            f"- Capital Allocation: Disciplined capital expenditure deployment balancing growth investments with programmatic shareholder returns [E005]\n"
            f"- Technological Moat: Substantial ongoing investments in proprietary software layers and architectures sustain competitive barriers [E006]\n"
            f"- Conclusion:\n"
            f"  * Strategic execution capabilities and diversified enterprise end-markets provide durable forward resilience [E001]\n"
            f"  * Contained"
        )
    else:
        citations = ["E001", "E002"]
        text = f"### {user_input[:40].strip()}\n- Core disclosures verified in primary SEC filings [E001].\n- Operational performance aligns with standard corporate parameters [E002].\n- Final Section Risk Band: Contained (Data Confidence: Strong)"

    return {"section_text": text, "citations": citations}

    return {"section_text": text, "citations": citations}
