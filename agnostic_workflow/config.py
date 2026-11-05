"""Configuration loader for the standalone agnostic workflow.

Automatically locates and loads environment variables from:
1. Current working directory .env
2. Package directory .env (agnostic_workflow/.env)
3. Parent directory .env (../.env)
"""

import os
from pathlib import Path

# Try loading dotenv if installed
try:
    from dotenv import load_dotenv

    # Search candidates
    search_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent / "backend" / ".env",
    ]
    for p in search_paths:
        if p.exists() and p.is_file():
            load_dotenv(dotenv_path=str(p), override=False)
            break
except ImportError:
    pass


class WorkflowConfig:
    """Standalone configuration options."""

    # Perplexity API
    PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
    PERPLEXITY_BASE_URL = os.environ.get("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
    PERPLEXITY_SEARCH_TYPE = os.environ.get("PERPLEXITY_SEARCH_TYPE", "fast")

    # Azure AI Foundry / OpenAI
    AZURE_FOUNDRY_ENDPOINT = os.environ.get(
        "AZURE_FOUNDRY_ENDPOINT",
        os.environ.get("AZURE_OPENAI_ENDPOINT", "https://puneetshrivas32-0871-resource.services.ai.azure.com")
    ).rstrip("/")
    AZURE_API_KEY = os.environ.get("AZURE_API_KEY", os.environ.get("AZURE_OPENAI_API_KEY", ""))

    # Groq API
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    # Google Gemini API
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

    # IteraCompute / Custom OpenAI-compatible
    ITERACT_API_KEY = os.environ.get("ITERACT_API_KEY", "")
    ITERACT_BASE_URL = os.environ.get("ITERACT_BASE_URL", "https://api.iteract.ai/v1")

    # Caching and Artifact Directories
    DEFAULT_ARTIFACTS_DIR = os.environ.get("ARTIFACTS_DIR", str(Path.cwd() / "artifacts"))
    DEFAULT_CACHE_DIR = os.environ.get("CACHE_DIR", str(Path.cwd() / ".cache_agnostic_retrieval"))


config = WorkflowConfig()
