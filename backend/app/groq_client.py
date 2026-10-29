"""
Groq Client Integration — High-speed inference provider.

Supports Qwen 3.8 (primary default), Llama 3.3, and DeepSeek distilled models
via Groq's low-latency LPU infrastructure.
"""

import os
import time
from typing import Optional, Tuple, List, Dict, Any

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    Groq = None  # type: ignore
    GROQ_AVAILABLE = False


DEFAULT_GROQ_MODEL = "qwen-3.8"

# Model candidate priority list for Qwen models on Groq
QWEN_MODEL_CANDIDATES = [
    "qwen/qwen3.8-27b",
    "qwen-2.5-32b",
    "qwen/qwen3-32b",
    "qwen-2.5-coder-32b",
    "deepseek-r1-distill-qwen-32b",
    "llama-3.3-70b-versatile",
]


def is_groq_configured() -> bool:
    """Returns True if GROQ_API_KEY is configured in the environment."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    return bool(key and not key.startswith("your-") and not key.startswith("test-placeholder"))


def get_groq_client() -> Tuple[Optional[Any], Optional[str]]:
    """
    Returns an initialized Groq client and the active API key, or (None, None).
    """
    if not GROQ_AVAILABLE:
        return None, None

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key or api_key.startswith("your-") or api_key.startswith("test-placeholder"):
        return None, None

    try:
        client = Groq(api_key=api_key)
        return client, api_key
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return None, None


def resolve_groq_model_candidates(requested_model: Optional[str]) -> List[str]:
    """
    Resolves requested model name to prioritized candidate IDs on Groq.
    """
    if not requested_model:
        return list(QWEN_MODEL_CANDIDATES)

    m = requested_model.strip().lower()

    if "qwen-3.8" in m or "qwen 3.8" in m or m == "qwen" or m == "default" or m == "qwen-3":
        return list(QWEN_MODEL_CANDIDATES)
    elif "coder" in m and "qwen" in m:
        return ["qwen-2.5-coder-32b", "qwen-2.5-32b", "qwen/qwen3.8-27b"]
    elif "llama" in m:
        return ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    elif "deepseek" in m:
        return ["deepseek-r1-distill-qwen-32b", "deepseek-r1-distill-llama-70b"]
    elif "/" in requested_model or "-" in requested_model:
        # User passed a specific model ID like 'qwen-2.5-32b'
        return [requested_model.strip()] + [c for c in QWEN_MODEL_CANDIDATES if c != requested_model.strip()]

    return list(QWEN_MODEL_CANDIDATES)


def execute_groq_chat(
    client: Any,
    messages: List[Dict[str, str]],
    system_prompt: str = "",
    requested_model: str = DEFAULT_GROQ_MODEL,
    temperature: float = 0.3,
    max_completion_tokens: int = 4096,
) -> Tuple[str, int, int, int, str]:
    """
    Executes a chat completion against Groq API with automatic model candidate fallback.

    Returns:
        (content, total_tokens, prompt_tokens, completion_tokens, resolved_model_name)
    """
    candidates = resolve_groq_model_candidates(requested_model)

    payload_messages: List[Dict[str, str]] = []
    if system_prompt:
        payload_messages.append({"role": "system", "content": system_prompt})

    for msg in messages:
        role = "user" if msg.get("role") == "user" else "assistant"
        payload_messages.append({"role": role, "content": msg.get("content", "")})

    last_error = None
    for model_id in candidates:
        try:
            completion = client.chat.completions.create(
                model=model_id,
                messages=payload_messages,
                temperature=temperature,
                max_completion_tokens=max_completion_tokens,
            )

            choice = completion.choices[0] if completion.choices else None
            content = choice.message.content if choice and choice.message else ""

            usage = getattr(completion, "usage", None)
            total_tokens = getattr(usage, "total_tokens", 0) or (len(content.split()) + 50)
            prompt_tokens = getattr(usage, "prompt_tokens", 0) or 20
            completion_tokens = getattr(usage, "completion_tokens", 0) or len(content.split())

            return content, total_tokens, prompt_tokens, completion_tokens, model_id
        except Exception as e:
            err_str = str(e).lower()
            last_error = e
            # If model is not found or deprecated, try next candidate
            if "model" in err_str and ("not found" in err_str or "decommissioned" in err_str or "does not exist" in err_str):
                continue
            # For rate limits or auth errors, re-raise or break
            raise e

    if last_error:
        raise last_error

    raise RuntimeError("No suitable Groq model candidates could be executed.")
