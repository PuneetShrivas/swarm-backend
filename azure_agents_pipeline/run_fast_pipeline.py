#!/usr/bin/env python
"""
Executable CLI for Azure AI Foundry Fast Alternative Pipeline.
Usage:
    python azure_agents_pipeline/run_fast_pipeline.py <COMPANY_NAME_OR_TICKER> [OPTIONS]

Examples:
    python azure_agents_pipeline/run_fast_pipeline.py NVDA
    python azure_agents_pipeline/run_fast_pipeline.py "NVIDIA Corporation" --mode both
    python azure_agents_pipeline/run_fast_pipeline.py MSFT --mode direct
    python azure_agents_pipeline/run_fast_pipeline.py AAPL --mode agent --output-dir ./reports
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to sys.path
_current_dir = Path(__file__).resolve().parent
_root_dir = _current_dir.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from azure_agents_pipeline.config import (
    DEFAULT_ENDPOINT,
    DEFAULT_RESEARCHER_AGENT,
    DEFAULT_GENERATOR_AGENT,
    DEFAULT_DIRECT_MODEL_ENDPOINT,
    DEFAULT_DIRECT_MODEL_NAME,
    DEFAULT_FALLBACK_MODEL_NAME,
    DEFAULT_OUTPUT_DIR,
    check_azure_credentials_available,
)
from azure_agents_pipeline.fast_pipeline import FastAzureFoundryPipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fast Alternative Pipeline: Company Name → DO-researcher → (1: DO-report-generator & 2: Direct Azure Foundry Model)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  --mode both    Execute both Pathway 1 (Agent) and Pathway 2 (Direct Model) and print comparison (default).
  --mode agent   Execute only Pathway 1 (DO-researcher → DO-report-generator).
  --mode direct  Execute only Pathway 2 (DO-researcher → Direct Azure Foundry Model).

Examples:
  python azure_agents_pipeline/run_fast_pipeline.py NVDA
  python azure_agents_pipeline/run_fast_pipeline.py "Apple Inc." --mode both
  python azure_agents_pipeline/run_fast_pipeline.py TSLA --mode direct --model claude-sonnet-4-6
        """
    )
    parser.add_argument(
        "company",
        help="Target company name or stock ticker (e.g. NVDA, 'Microsoft Corporation', TSLA)",
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["both", "agent", "direct"],
        default="both",
        help="Fast pipeline execution mode: 'both' (default), 'agent', or 'direct'",
    )
    parser.add_argument(
        "--ticker",
        default=None,
        help="Explicit stock ticker override if company name is a long string.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_DIRECT_MODEL_NAME,
        help=f"Azure Foundry model name for Pathway 2 direct synthesis. (Default: {DEFAULT_DIRECT_MODEL_NAME})",
    )
    parser.add_argument(
        "--fallback-model",
        default=DEFAULT_FALLBACK_MODEL_NAME,
        help=f"Secondary model for Pathway 2 failover. (Default: {DEFAULT_FALLBACK_MODEL_NAME})",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"Azure AI Foundry project endpoint. (Default: {DEFAULT_ENDPOINT})",
    )
    parser.add_argument(
        "--direct-endpoint",
        default=DEFAULT_DIRECT_MODEL_ENDPOINT,
        help=f"Direct model endpoint. (Default: {DEFAULT_DIRECT_MODEL_ENDPOINT})",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to save generated reports. (Default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--prompt-file",
        default=None,
        help="Optional path to markdown prompt file to override standard 13-section underwriter instructions.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive browser login for Entra ID authentication.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    company_input = args.company.strip()
    ticker = (args.ticker.strip().upper() if args.ticker else (company_input.upper() if len(company_input) <= 5 and company_input.isalpha() else None))

    # Check credentials
    has_creds, diag_msg = check_azure_credentials_available()
    if not has_creds and not args.interactive:
        print("\n" + "=" * 80)
        print(" [!] AZURE ENTRA ID AUTHENTICATION NOTICE")
        print("=" * 80)
        print(diag_msg)
        print("=" * 80 + "\n")

    custom_prompt = None
    if args.prompt_file:
        p_path = Path(args.prompt_file)
        if p_path.is_file():
            custom_prompt = p_path.read_text(encoding="utf-8")
        else:
            print(f"[WARNING] Prompt file '{args.prompt_file}' not found. Using standard underwriter prompt.", flush=True)

    pipeline = FastAzureFoundryPipeline(
        endpoint=args.endpoint,
        researcher_agent=DEFAULT_RESEARCHER_AGENT,
        generator_agent=DEFAULT_GENERATOR_AGENT,
        direct_model_endpoint=args.direct_endpoint,
        direct_model_name=args.model,
        fallback_model_name=args.fallback_model,
        direct_model_prompt=custom_prompt,
        output_dir=args.output_dir,
        interactive=args.interactive,
    )

    try:
        telemetry = pipeline.run(
            company_name_or_prompt=company_input,
            ticker=ticker,
            mode=args.mode,
        )
        print(telemetry.format_fast_comparison_summary(), flush=True)

        print("[SUCCESS] Fast pipeline finished. Artifacts created:")
        for kind, path in telemetry.output_files.items():
            print(f"  * {kind.upper()}: {path}")
        print("")

    except Exception as e:
        print(f"\n[FAST PIPELINE ERROR] Execution failed: {e}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
