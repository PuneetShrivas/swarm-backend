#!/usr/bin/env python
"""
Executable Entrypoint for Azure AI Foundry Three-Agent Pipeline.
Usage:
    python azure_agents_pipeline/run_pipeline.py [TICKER] [OPTIONS]

Examples:
    python azure_agents_pipeline/run_pipeline.py NVDA
    python azure_agents_pipeline/run_pipeline.py MSFT --output-dir ./reports
    python azure_agents_pipeline/run_pipeline.py --input "Investigate cyber governance and securities litigation for Tesla Inc."
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to sys.path so package imports resolve seamlessly
_current_dir = Path(__file__).resolve().parent
_root_dir = _current_dir.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from azure_agents_pipeline.config import (
    DEFAULT_ENDPOINT,
    DEFAULT_RESEARCHER_AGENT,
    DEFAULT_VALIDATOR_AGENT,
    DEFAULT_GENERATOR_AGENT,
    DEFAULT_OUTPUT_DIR,
    check_azure_credentials_available,
)
from azure_agents_pipeline.pipeline import AzureFoundryAgentTrioPipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="Azure AI Foundry Three-Agent Workflow: DO-researcher → DO-validator → DO-report-generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python azure_agents_pipeline/run_pipeline.py NVDA
  python azure_agents_pipeline/run_pipeline.py AAPL --output-dir ./reports
  python azure_agents_pipeline/run_pipeline.py --input "Analyze board turnover and restatement risk for target company." --interactive
        """
    )
    parser.add_argument(
        "ticker",
        nargs="?",
        default=None,
        help="Target company stock ticker symbol (e.g. NVDA, AAPL, MSFT)",
    )
    parser.add_argument(
        "--input", "-i",
        dest="user_input",
        default=None,
        help="Custom user instruction or prompt for the researcher agent.",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"Azure AI Foundry project endpoint URL. (Default: {DEFAULT_ENDPOINT})",
    )
    parser.add_argument(
        "--researcher",
        default=DEFAULT_RESEARCHER_AGENT,
        help=f"Researcher agent name. (Default: {DEFAULT_RESEARCHER_AGENT})",
    )
    parser.add_argument(
        "--validator",
        default=DEFAULT_VALIDATOR_AGENT,
        help=f"Validator agent name. (Default: {DEFAULT_VALIDATOR_AGENT})",
    )
    parser.add_argument(
        "--generator",
        default=DEFAULT_GENERATOR_AGENT,
        help=f"Report generator agent name. (Default: {DEFAULT_GENERATOR_AGENT})",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to save generated markdown, PDF, and telemetry JSON. (Default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive browser login if no active Azure Entra ID token or Service Principal is found.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    ticker = args.ticker.strip().upper() if args.ticker else None
    user_input = args.user_input

    if not user_input and not ticker:
        user_input = "Conduct an executive D&O Risk Underwriting assessment and evaluate key exposures."
    elif not user_input and ticker:
        user_input = f"Evaluate comprehensive D&O risk posture, litigation exposures, and underwriter tier for {ticker}."

    # Validate Azure credentials availability
    has_creds, diag_msg = check_azure_credentials_available()
    if not has_creds and not args.interactive:
        print("\n" + "=" * 80)
        print(" [!] AZURE ENTRA ID AUTHENTICATION REQUIRED")
        print("=" * 80)
        print(diag_msg)
        print("=" * 80 + "\n")

    pipeline = AzureFoundryAgentTrioPipeline(
        endpoint=args.endpoint,
        researcher_agent=args.researcher,
        validator_agent=args.validator,
        generator_agent=args.generator,
        output_dir=args.output_dir,
        interactive=args.interactive,
    )

    try:
        telemetry = pipeline.run(user_input=user_input, ticker=ticker)
        summary_text = telemetry.format_console_summary()
        print(summary_text, flush=True)

        pdf_path = telemetry.output_files.get("pdf")
        if pdf_path and os.path.isfile(pdf_path):
            print(f"[SUCCESS] Official PDF Report generated successfully:\n  → {pdf_path}\n", flush=True)

    except Exception as e:
        print(f"\n[PIPELINE ERROR] Execution failed: {e}", file=sys.stderr, flush=True)
        # Check if error is related to authentication
        err_lower = str(e).lower()
        if "credential" in err_lower or "token" in err_lower or "unauthorized" in err_lower or "401" in err_lower:
            print("\n[AUTHENTICATION DIAGNOSTIC]")
            print("Azure AI Foundry requires an Entra ID token.")
            print("Please configure one of:")
            print("  1. In .env: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET")
            print("  2. In terminal: az login")
            print("  3. Run script with --interactive to open browser authentication.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
