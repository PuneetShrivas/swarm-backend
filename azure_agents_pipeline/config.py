"""
Configuration and Credential Resolver for Azure AI Foundry Three-Agent Pipeline.
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv

# Automatically load environment variables from backend/.env or root .env
_root_dir = Path(__file__).resolve().parent.parent
_backend_env = _root_dir / "backend" / ".env"
_root_env = _root_dir / ".env"

if _backend_env.is_file():
    load_dotenv(_backend_env)
if _root_env.is_file():
    load_dotenv(_root_env)

# Azure AI Foundry project configuration
DEFAULT_ENDPOINT = os.environ.get(
    "AZURE_AI_PROJECT_ENDPOINT",
    "https://puneetshrivas32-0871-resource.services.ai.azure.com/api/projects/puneetshrivas32-0871"
).strip()

DEFAULT_RESEARCHER_AGENT = os.environ.get("AZURE_RESEARCHER_AGENT", "DO-researcher")
DEFAULT_VALIDATOR_AGENT = os.environ.get("AZURE_VALIDATOR_AGENT", "DO-validator")
DEFAULT_GENERATOR_AGENT = os.environ.get("AZURE_GENERATOR_AGENT", "DO-report-generator")

# Direct Azure Foundry Model deployment settings
DEFAULT_DIRECT_MODEL_ENDPOINT = os.environ.get(
    "AZURE_FOUNDRY_ENDPOINT",
    "https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages"
).strip()
DEFAULT_DIRECT_MODEL_NAME = os.environ.get("AZURE_FAST_MODEL", "claude-sonnet-4-6").strip()
DEFAULT_FALLBACK_MODEL_NAME = os.environ.get("AZURE_FALLBACK_MODEL", "claude-opus-4-8").strip()
AZURE_API_KEY = os.environ.get("AZURE_API_KEY", "").strip()

DEFAULT_OUTPUT_DIR = os.environ.get(
    "AZURE_PIPELINE_OUTPUT_DIR",
    str(_root_dir / "backend" / "artifacts")
)


def get_azure_credential(interactive: bool = False):
    """
    Initializes and returns an Azure TokenCredential instance.
    Supports Service Principal (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID),
    Azure CLI, VS Code, Managed Identity, and optional Interactive Browser login.
    """
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential(exclude_interactive_browser_credential=not interactive)


def check_azure_credentials_available() -> Tuple[bool, str]:
    """
    Verifies if valid Entra ID credentials can be resolved.
    Returns (is_available, diagnostic_message).
    """
    has_sp = bool(
        os.environ.get("AZURE_CLIENT_ID")
        and os.environ.get("AZURE_CLIENT_SECRET")
        and os.environ.get("AZURE_TENANT_ID")
    )
    if has_sp:
        return True, "Found Service Principal environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)."

    # Test token resolution via DefaultAzureCredential
    try:
        from azure.identity import DefaultAzureCredential
        cred = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        # Attempt to acquire a token for Azure AI Foundry
        token = cred.get_token("https://ai.azure.com/.default")
        if token and token.token:
            return True, "Successfully acquired Azure Entra ID token via DefaultAzureCredential."
    except Exception as e:
        err_msg = str(e)
        return False, (
            "No active Azure Entra ID credential found.\n"
            "To authenticate to Azure AI Foundry, choose one of the following:\n"
            "  1. Add Service Principal credentials to your .env file:\n"
            "     AZURE_TENANT_ID=<your-tenant-id>\n"
            "     AZURE_CLIENT_ID=<your-client-id>\n"
            "     AZURE_CLIENT_SECRET=<your-client-secret>\n"
            "  2. Install and log in via Azure CLI:\n"
            "     az login\n"
            "  3. Run the script with --interactive to open a web browser sign-in."
        )

    return True, "Azure credential verified."
