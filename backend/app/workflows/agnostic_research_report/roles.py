"""
Multi-Provider LLM Worker & Role Router with Granular Token Accounting.
Supports Azure AI Foundry (Anthropic Messages API / Entra ID), Groq LPUs, Google Gemini, and IteraCompute.
Every role execution returns (parsed_result, token_usage, duration_ms, model_used).
"""

import os
import re
import json
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv

load_dotenv()

# Active provider & fallback model configuration
ACTIVE_PROVIDER = os.environ.get("LLM_PROVIDER", "azure").lower()
ACTIVE_FALLBACK_MODEL = os.environ.get("AZURE_FALLBACK_MODEL", "claude-opus-4-8")

PROVIDER_MODELS: Dict[str, Dict[str, str]] = {
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
    "groq": {
        "fast": "llama-3.3-70b-versatile",
        "medium": "llama-3.3-70b-versatile",
        "reasoning": "openai/gpt-oss-120b",
    },
    "gemini": {
        "fast": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "medium": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "reasoning": os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"),
    },
    "iteracompute": {
        "fast": os.environ.get("ITERACOMPUTE_MODEL", "qwen/qwen3.8-27b"),
        "medium": os.environ.get("ITERACOMPUTE_MODEL", "qwen/qwen3.8-27b"),
        "reasoning": os.environ.get("ITERACOMPUTE_REASONING_MODEL", "qwen/qwen3.8-27b"),
    },
}

ROLE_TIER_MAPPING: Dict[str, str] = {
    "plan": "medium",
    "extract": "fast",
    "gap": "fast",
    "draft": "medium",
    "synthesize": "reasoning",
    "verify": "reasoning",
}

# Role System Prompts (Domain-Agnostic)
PLAN_SYSTEM = """You are the Plan role in an analytical research pipeline.
Given a subject and a section specification, formulate 4 to 6 highly targeted, distinct web search queries
to systematically discover empirical data, verified developments, benchmarks, key players, or regulatory context covering the required checklist.
Do not repeat generic search queries.
Output format: JSON object with key "queries": [{"text": "query string", "domains": ["example.com"], "recency": "year"}]"""

EXTRACT_SYSTEM = """You are the Extract role in an analytical research pipeline.
Task: Turn compacted search results into atomic facts adhering to the Evidence Ledger schema.
CRITICAL RULES:
1. SUBJECT GUARD: Reject any result about an unrelated entity or topic with a similar name.
2. NO INFERENCE: Extract only what is explicitly stated in the source text. Never guess or extrapolate.
3. CITATIONS: Each extracted fact must include the source URL, publication date, and a verbatim quote.
4. "NOT FOUND": If a search result contains no relevant facts addressing the section, return an empty items list.
Output format: JSON object with key "items": list of Evidence objects with fields:
[{"claim": "...", "value": "...", "as_of": "YYYY-MM-DD", "source_url": "...", "source_type": "official|academic|news|filing|other", "published": "YYYY-MM-DD", "confidence": "high|med|low", "quote": "verbatim text"}]"""

GAP_SYSTEM = """You are the Gap role in an analytical research pipeline.
Task: Compare section evidence claims against the required section field checklist.
If the section requirements are sufficiently covered, return an empty queries list.
If critical fields are missing, unverified, or ambiguous, generate at most 2 highly targeted follow-up search queries to close the specific evidence gaps.
Do not repeat broad or generic queries.
Output format: JSON object with key "queries": [{"text": "follow up query string", "domains": [], "recency": "year"}]"""

DRAFT_SYSTEM = """You are the Section Drafter in an institutional research pipeline.
Task: Draft the comprehensive, highly analytical narrative for the requested section.
RULES:
1. Follow the section's formatting rules, bullet requirements, and subheadings strictly.
2. CITE EVIDENCE: Cite facts strictly using [E###] citation tokens from the supplied evidence ledger rows.
3. ZERO INVENTIONS: If a requested field is not present in the evidence ledger, state that data is unavailable.
4. Output format: JSON object with key "section_text": "### SECTION TITLE\\n- Narrative..." """

SYNTHESIZE_SYSTEM = """You are the Synthesizer in an institutional research pipeline.
Task: Synthesize the drafted sections into an overarching executive summary and verdict.
RULES:
1. NO NEW FACTS: Every claim must be traceable to preceding drafted sections.
2. Provide strategic classification, bottom-line assessment, and identify any critical information gaps.
Output format: JSON object with keys:
{"executive_summary": "...", "verdict_text": "...", "classification": "...", "unknowns": ["..."]}"""

VERIFY_SYSTEM = """You are the Verification Agent in an institutional research pipeline.
Task: Audit drafted section narrative against evidence ledger rows.
Verify that every [E###] token matches its supporting quote and that no unsupported claims exist.
Output format: JSON object with keys:
{"issues": [{"section": "...", "problem": "...", "severity": "warning|critical"}], "is_valid": true|false}"""

ROLES_CONFIG: Dict[str, Dict[str, Any]] = {
    "plan": {"system": PLAN_SYSTEM, "temp": 0.1, "max_tokens": 4000},
    "extract": {"system": EXTRACT_SYSTEM, "temp": 0.0, "max_tokens": 4000},
    "gap": {"system": GAP_SYSTEM, "temp": 0.0, "max_tokens": 1000},
    "draft": {"system": DRAFT_SYSTEM, "temp": 0.1, "max_tokens": 4000},
    "synthesize": {"system": SYNTHESIZE_SYSTEM, "temp": 0.1, "max_tokens": 3500},
    "verify": {"system": VERIFY_SYSTEM, "temp": 0.0, "max_tokens": 2000},
}

AZURE_SEMAPHORE = asyncio.Semaphore(int(os.environ.get("AZURE_MAX_CONCURRENCY", "3")))


def set_active_provider(provider: str) -> None:
    global ACTIVE_PROVIDER
    p = provider.lower().strip()
    if p in ["azure", "azure-foundry", "foundry", "groq", "gemini", "iteracompute"]:
        ACTIVE_PROVIDER = "azure" if p in ["azure-foundry", "foundry"] else p
    else:
        raise ValueError(f"Unknown provider '{provider}'. Valid choices: 'azure', 'groq', 'gemini', 'iteracompute'")


def get_active_provider() -> str:
    return ACTIVE_PROVIDER


def set_fallback_model(model: str) -> None:
    global ACTIVE_FALLBACK_MODEL
    ACTIVE_FALLBACK_MODEL = model.strip()


def get_fallback_model() -> Optional[str]:
    return ACTIVE_FALLBACK_MODEL


# Active per-task model overrides
ACTIVE_TASK_MODELS: Dict[str, str] = {
    "plan": os.environ.get("MODEL_PLAN", os.environ.get("AZURE_PLAN_MODEL", "")).strip(),
    "extract": os.environ.get("MODEL_EXTRACT", os.environ.get("AZURE_EXTRACT_MODEL", "")).strip(),
    "gap": os.environ.get("MODEL_GAP", os.environ.get("AZURE_GAP_MODEL", "")).strip(),
    "draft": os.environ.get("MODEL_DRAFT", os.environ.get("AZURE_DRAFT_MODEL", "")).strip(),
    "synthesize": os.environ.get("MODEL_SYNTHESIZE", os.environ.get("MODEL_SYNTH", os.environ.get("AZURE_SYNTHESIZE_MODEL", ""))).strip(),
    "verify": os.environ.get("MODEL_VERIFY", "").strip(),
}


def set_task_model(role: str, model: str) -> None:
    """Sets a model override for a specific task role."""
    norm_role = "synthesize" if role.lower().strip() in ["synth", "synthesize"] else role.lower().strip()
    ACTIVE_TASK_MODELS[norm_role] = model.strip()


def set_task_models(mapping: Dict[str, str]) -> None:
    """Sets multiple model overrides from a dictionary."""
    for role, model in mapping.items():
        if model:
            set_task_model(role, model)


def get_task_models() -> Dict[str, str]:
    """Returns a dictionary of all active non-empty task model overrides."""
    return {k: v for k, v in ACTIVE_TASK_MODELS.items() if v}


def resolve_task_model(
    role: str,
    task_models: Optional[Dict[str, str]] = None,
    model_override: Optional[str] = None,
    provider: Optional[str] = None,
) -> str:
    """
    Resolves the exact model to use for a given role based on:
    1. Explicit task override from passed task_models dict
    2. Global ACTIVE_TASK_MODELS override (from env or set_task_model)
    3. Direct model_override (e.g. global CLI --model flag)
    4. Provider default for the role's tier
    """
    norm_role = "synthesize" if role.lower().strip() in ["synth", "synthesize"] else role.lower().strip()
    if task_models:
        cand = task_models.get(norm_role) or task_models.get(role)
        if cand and cand.strip():
            return cand.strip()

    if ACTIVE_TASK_MODELS.get(norm_role):
        return ACTIVE_TASK_MODELS[norm_role].strip()

    if model_override and model_override.strip():
        return model_override.strip()

    prov = (provider or ACTIVE_PROVIDER).lower()
    prov_models = PROVIDER_MODELS.get(prov, PROVIDER_MODELS.get("azure", {}))
    role_tier = ROLE_TIER_MAPPING.get(norm_role, "medium")
    return prov_models.get(role_tier, "claude-sonnet-4-6")


def _extract_json(text: str) -> Dict[str, Any]:
    """Robust parser extracting JSON from thinking blocks, fences, or bare dictionaries."""
    if not text:
        return {}
    # Strip thinking blocks
    cleaned = re.sub(r"<(?:thinking|thought)>[\s\S]*?</(?:thinking|thought)>", "", text).strip()
    if not cleaned:
        cleaned = text.strip()

    # Direct JSON parse
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        elif isinstance(parsed, list):
            return {"items": parsed}
    except Exception:
        pass

    # Fenced ```json ... ```
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

    # Outermost curly braces
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        cand = cleaned[start:end + 1]
        try:
            parsed = json.loads(cand)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            try:
                cand_fixed = re.sub(r",\s*([\}\]])", r"\1", cand)
                parsed = json.loads(cand_fixed)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

    return {}


def is_openai_foundry_model(model_name: str) -> bool:
    """Checks if the requested Azure Foundry model is an OpenAI model (e.g., gpt-5.4, gpt-5-mini)."""
    m = (model_name or "").lower().strip()
    return (
        m in ["gpt-5.4", "gpt-5-mini"]
        or m.startswith("gpt-5.4")
        or m.startswith("gpt-5-mini")
        or m.startswith("gpt-")
        or m.startswith("o1")
        or m.startswith("o3")
    )


def resolve_foundry_endpoint(model: str, base_endpoint: Optional[str] = None) -> str:
    """Resolves Azure Foundry endpoint according to model family.
    When gpt-5.4 or gpt-5-mini is used:
        routes to Azure Foundry OpenAI Responses API (.../openai/v1/responses)
    When Claude or other Anthropic models are used:
        routes to Azure Foundry Anthropic Messages API (.../anthropic/v1/messages)
    """
    m = (model or "").lower().strip()
    is_openai = is_openai_foundry_model(m)
    default_host = "https://puneetshrivas32-0871-resource.services.ai.azure.com"
    raw = (base_endpoint or os.environ.get("AZURE_FOUNDRY_ENDPOINT", "")).strip()

    if not raw:
        return f"{default_host}/openai/v1/responses" if is_openai else f"{default_host}/anthropic/v1/messages"

    if is_openai:
        if "/anthropic/" in raw:
            raw = raw.replace("/anthropic/", "/openai/")
        if raw.endswith("/v1/messages"):
            raw = raw[:-len("/v1/messages")] + "/v1/responses"
        elif raw.endswith("/v1"):
            raw = raw + "/responses"
        elif not raw.endswith("/v1/responses"):
            raw = f"{raw.rstrip('/')}/openai/v1/responses" if "/openai" not in raw else f"{raw.rstrip('/')}/v1/responses"
        return raw
    else:
        if "/openai/" in raw:
            raw = raw.replace("/openai/", "/anthropic/")
        if raw.endswith("/v1/responses"):
            raw = raw[:-len("/v1/responses")] + "/v1/messages"
        elif raw.endswith("/v1"):
            raw = raw + "/messages"
        elif not raw.endswith("/v1/messages"):
            raw = f"{raw.rstrip('/')}/anthropic/v1/messages" if "/anthropic" not in raw else f"{raw.rstrip('/')}/v1/messages"
        return raw


async def _execute_azure_chat_with_tokens(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temp: float,
    max_tokens: int,
) -> Tuple[str, Dict[str, int]]:
    """Executes Azure Foundry REST call and returns (content_text, token_usage)."""
    api_key = os.environ.get("AZURE_API_KEY", "").strip()
    auth_header = ""
    if api_key and not api_key.startswith("your-") and not api_key.startswith("test-"):
        auth_header = f"Bearer {api_key}"
    else:
        # Fallback to dynamic Entra ID Bearer token
        try:
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
            cred = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(cred, "https://ai.azure.com/.default")
            tok = token_provider()
            if tok:
                auth_header = f"Bearer {tok}"
        except Exception:
            pass

    if not auth_header:
        raise RuntimeError("Neither AZURE_API_KEY nor valid Azure Entra ID credentials available.")

    endpoint = resolve_foundry_endpoint(model, os.environ.get("AZURE_FOUNDRY_ENDPOINT"))
    is_openai = is_openai_foundry_model(model)

    if is_openai:
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_header,
        }
        if api_key:
            headers["api-key"] = api_key
        payload = {
            "model": model,
            "instructions": system_prompt + "\n\nCRITICAL: Respond ONLY with a valid JSON object matching the requested schema. Do not wrap in markdown fences.",
            "input": user_prompt,
            "max_output_tokens": max_tokens,
        }
    else:
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_header,
            "anthropic-version": "2023-06-01",
        }
        if api_key:
            headers["api-key"] = api_key
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_prompt + "\n\nCRITICAL: Respond ONLY with a valid JSON object matching the requested schema. Do not wrap in markdown fences.",
            "messages": [{"role": "user", "content": user_prompt}],
        }

    import httpx
    async with AZURE_SEMAPHORE:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(endpoint, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Azure Foundry HTTP {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            if not isinstance(data, dict):
                raise RuntimeError(f"Azure Foundry non-dict response: {data}")

            if data.get("error"):
                err_msg = data["error"].get("message", str(data["error"])) if isinstance(data["error"], dict) else str(data["error"])
                raise RuntimeError(f"Azure Foundry API error: {err_msg}")

            # 1. Parse OpenAI Responses API format
            full_text = ""
            if "output" in data and isinstance(data["output"], list):
                for item in data["output"]:
                    if isinstance(item, dict) and "content" in item and isinstance(item["content"], list):
                        for c in item["content"]:
                            if isinstance(c, dict) and "text" in c:
                                full_text += c["text"]
            if not full_text and data.get("output_text"):
                full_text = data.get("output_text", "")

            # 2. Parse Anthropic Messages API format
            if not full_text:
                content_items = data.get("content", [])
                text_blocks = []
                if isinstance(content_items, list):
                    for item in content_items:
                        if isinstance(item, dict) and (item.get("type") == "text" or "text" in item):
                            text_blocks.append(item.get("text", ""))
                full_text = "".join(text_blocks).strip()

            # 3. Parse OpenAI Chat Completions fallback
            if not full_text and "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                first_choice = data["choices"][0]
                if isinstance(first_choice, dict) and "message" in first_choice:
                    full_text = first_choice["message"].get("content", "").strip()

            raw_usage = data.get("usage", {})
            in_tok = raw_usage.get("input_tokens") or raw_usage.get("prompt_tokens") or (len(user_prompt) // 4)
            out_tok = raw_usage.get("output_tokens") or raw_usage.get("completion_tokens") or (len(full_text) // 4)
            usage = {
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "total_tokens": in_tok + out_tok,
            }
            return full_text, usage


async def _execute_groq_chat_with_tokens(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temp: float,
    max_tokens: int,
) -> Tuple[str, Dict[str, int]]:
    """Executes Groq chat and captures token usage."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    from groq import AsyncGroq
    client = AsyncGroq(api_key=api_key)
    res = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temp,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    content = res.choices[0].message.content or ""
    usage_info = getattr(res, "usage", None)
    in_tok = getattr(usage_info, "prompt_tokens", len(user_prompt) // 4) if usage_info else len(user_prompt) // 4
    out_tok = getattr(usage_info, "completion_tokens", len(content) // 4) if usage_info else len(content) // 4
    return content, {
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "total_tokens": in_tok + out_tok,
    }


async def _execute_gemini_chat_with_tokens(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temp: float,
    max_tokens: int,
) -> Tuple[str, Dict[str, int]]:
    """Executes Google Gemini chat and captures token usage metadata."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key or api_key.startswith("your-"):
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key.strip())
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=temp,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
    )

    def _call():
        return client.models.generate_content(model=model, contents=user_prompt, config=config)

    res = await asyncio.to_thread(_call)
    content = res.text or ""
    meta = getattr(res, "usage_metadata", None)
    in_tok = getattr(meta, "prompt_token_count", len(user_prompt) // 4) if meta else len(user_prompt) // 4
    out_tok = getattr(meta, "candidates_token_count", len(content) // 4) if meta else len(content) // 4
    return content, {
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "total_tokens": in_tok + out_tok,
    }


def _generate_mock_role_output(role: str, user_prompt: str) -> Tuple[Dict[str, Any], Dict[str, int], float, str]:
    """Synthetic role output strictly for unit testing."""
    in_tok = len(user_prompt) // 4
    if role == "plan":
        data = {"queries": [{"text": "Quantum computing commercial roadmap", "domains": ["nature.com"], "recency": "year"}]}
    elif role == "extract":
        data = {
            "items": [
                {
                    "claim": "Major breakthrough in qubit coherence time achieved.",
                    "value": "100 microseconds",
                    "as_of": "2026-04-12",
                    "source_url": "https://nature.com/articles/quantum-qubit",
                    "source_type": "academic",
                    "published": "2026-04-12",
                    "confidence": "high",
                    "quote": "achieved record 100 microseconds coherence",
                }
            ]
        }
    elif role == "gap":
        data = {"queries": []}
    elif role == "draft":
        data = {"section_text": "### SECTION\n- Finding [E001] confirmed 100x efficiency gain."}
    elif role == "synthesize":
        data = {
            "executive_summary": "- Quantum advances show verifiable progress [E001].",
            "verdict_text": "## OVERALL VERDICT\n- Momentum: Rapid Acceleration.",
            "classification": "Rapid Acceleration",
            "unknowns": ["Long-term cooling infrastructure costs remain undisclosed."],
        }
    elif role == "verify":
        data = {"issues": [], "is_valid": True}
    else:
        data = {}

    out_tok = 80
    return data, {"input_tokens": in_tok, "output_tokens": out_tok, "total_tokens": in_tok + out_tok}, 5.0, "mock-model"



def parse_retry_delay(error_text: str, default_wait: float = 10.0, attempt: int = 0) -> float:
    """Extracts recommended wait seconds from Azure Foundry 429 error messages.
    Example matches:
    - 'Please wait 8 seconds before retrying.'
    - 'Please wait 1 seconds before retrying.'
    - 'retry after 12 seconds'
    """
    match = re.search(r"(?:please wait|retry after|wait)\s+(\d+(?:\.\d+)?)\s*(?:seconds|s)", error_text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1)) + 2.0  # +2s safety buffer
        except Exception:
            pass
    return default_wait + (attempt * 5.0)

async def run_role(
    role: str,
    user_input: str,
    *,
    model_override: Optional[str] = None,
    provider_override: Optional[str] = None,
    fallback_model_override: Optional[str] = None,
    task_models: Optional[Dict[str, str]] = None,
    mock_response: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, int], float, str]:
    """
    Executes an LLM role returning (parsed_dict, token_usage, duration_ms, model_used).
    Supports automatic 429 rate limit backoff and fallback model failover.
    """
    if role not in ROLES_CONFIG:
        raise ValueError(f"Unknown role '{role}'. Valid roles: {list(ROLES_CONFIG.keys())}")

    if mock_response is not None:
        return mock_response, {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}, 1.0, "mock"

    is_testing = os.environ.get("TESTING") == "true" or os.environ.get("MOCK_ROLES") == "true"
    allow_mock = is_testing and os.environ.get("ALLOW_MOCK_DATA") == "true"
    if allow_mock:
        return _generate_mock_role_output(role, user_input)

    cfg = ROLES_CONFIG[role]
    active_prov = (provider_override or ACTIVE_PROVIDER).lower()
    selected_model = resolve_task_model(
        role=role,
        task_models=task_models,
        model_override=model_override,
        provider=active_prov,
    )
    active_fallback = fallback_model_override or ACTIVE_FALLBACK_MODEL

    models_sequence = [selected_model]
    if active_fallback and active_fallback != selected_model:
        models_sequence.append(active_fallback)

    t0 = time.perf_counter()
    last_error = ""
    max_outer_rounds = 1 if is_testing else int(os.environ.get("AZURE_MAX_RETRY_ROUNDS", "5"))
    base_cooldown_seconds = int(os.environ.get("AZURE_RETRY_WAIT_SECONDS", "20"))

    for round_idx in range(max_outer_rounds):
        for m_idx, current_model in enumerate(models_sequence):
            is_fallback = (m_idx > 0)
            max_attempts = 3 if len(models_sequence) == 1 else 2

            for attempt in range(max_attempts):
                try:
                    if active_prov in ["azure", "azure-foundry", "foundry"]:
                        content, usage = await _execute_azure_chat_with_tokens(
                            model=current_model,
                            system_prompt=cfg["system"],
                            user_prompt=user_input,
                            temp=cfg["temp"],
                            max_tokens=cfg["max_tokens"],
                        )
                    elif active_prov == "groq":
                        content, usage = await _execute_groq_chat_with_tokens(
                            model=current_model,
                            system_prompt=cfg["system"],
                            user_prompt=user_input,
                            temp=cfg["temp"],
                            max_tokens=cfg["max_tokens"],
                        )
                    elif active_prov == "gemini":
                        content, usage = await _execute_gemini_chat_with_tokens(
                            model=current_model,
                            system_prompt=cfg["system"],
                            user_prompt=user_input,
                            temp=cfg["temp"],
                            max_tokens=cfg["max_tokens"],
                        )
                    else:
                        raise ValueError(f"Unsupported provider '{active_prov}'")

                    parsed = _extract_json(content)
                    if parsed:
                        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                        if is_fallback or round_idx > 0:
                            print(f"[AZURE SUCCESS] Role '{role}' succeeded with model '{current_model}' (round {round_idx + 1}/{max_outer_rounds})", flush=True)
                        return parsed, usage, duration_ms, current_model

                    last_error = f"Model '{current_model}' returned unparseable JSON (length={len(content)})"
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue

                except Exception as e:
                    last_error = str(e)
                    err_lower = str(e).lower()
                    is_429 = any(k in err_lower for k in ["rate limit", "429", "tpm", "quota", "tokens per 60s"])

                    if is_429 and not is_fallback and len(models_sequence) > 1:
                        print(f"[RATE LIMIT 429] Role '{role}' hit rate limit on '{current_model}'. Failing over to fallback model '{models_sequence[1]}'...", flush=True)
                        break

                    if (is_429 or "timeout" in err_lower) and attempt < max_attempts - 1:
                        delay = parse_retry_delay(last_error, default_wait=4.0, attempt=attempt)
                        print(f"  ⏳ [AZURE 429 BACKOFF] Role '{role}' ({current_model}): Rate limit detected. Pausing {delay:.1f}s before retry (attempt {attempt + 2}/{max_attempts})...", flush=True)
                        await asyncio.sleep(delay)
                        continue

                    break

        # If all models in sequence failed in this round, check if retryable before outer cooldown
        if round_idx < max_outer_rounds - 1:
            is_retryable = any(kw in last_error.lower() for kw in [
                "rate limit", "429", "token", "tpm", "quota", "overloaded", "capacity",
                "500", "502", "503", "504", "timeout", "connection", "temporarily",
                "service unavailable", "gateway", "call failed", "unparseable", "empty json"
            ])
            if not is_retryable:
                break

            parsed_wait = parse_retry_delay(last_error, default_wait=0.0)
            cooldown_wait = max(parsed_wait, float(base_cooldown_seconds + round_idx * 10))
            print(f"\n[AZURE RATE LIMIT COOLDOWN] Role '{role}' exhausted model sequence for round {round_idx + 1}/{max_outer_rounds}.\n[AZURE RATE LIMIT COOLDOWN] Pausing {int(cooldown_wait)}s for token quota replenishment before round {round_idx + 2}/{max_outer_rounds}...", flush=True)

            elapsed = 0.0
            step = 5.0
            while elapsed < cooldown_wait:
                sleep_time = min(step, cooldown_wait - elapsed)
                await asyncio.sleep(sleep_time)
                elapsed += sleep_time
                remaining = cooldown_wait - elapsed
                pct = int((elapsed / cooldown_wait) * 100)
                bar_filled = "#" * (pct // 5)
                bar_empty = "-" * (20 - (pct // 5))
                if remaining > 0:
                    print(f"  ⏳ [AZURE COOLDOWN] Role '{role}': [{bar_filled}{bar_empty}] {int(elapsed)}s/{int(cooldown_wait)}s ({pct}%) — retrying in {int(remaining)}s...", flush=True)
                else:
                    print(f"  ✅ [AZURE COOLDOWN COMPLETE] Role '{role}': Cooldown finished ({int(cooldown_wait)}s elapsed). Retrying request with model '{models_sequence[0]}'...\n", flush=True)

    raise RuntimeError(f"Role '{role}' execution failed across models {models_sequence} after {max_outer_rounds} retry rounds: {last_error}")
