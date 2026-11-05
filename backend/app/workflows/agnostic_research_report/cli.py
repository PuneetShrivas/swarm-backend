"""
CLI Interface for Prompt-Driven Agnostic Research & Report Generation.
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from app.workflows.agnostic_research_report.orchestrator import AgnosticResearchOrchestrator
from app.workflows.agnostic_research_report.telemetry import render_tree, render_table


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prompt-Driven Agnostic Research & Report Generation Swarm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/run_agnostic_research_report.py "Solid State Battery Commercialization"
  python backend/run_agnostic_research_report.py "Quantum Computing in Drug Discovery" --prompt-file path/to/prompt.md --mode standard
  python backend/run_agnostic_research_report.py "CrowdStrike Outage Analysis" --provider azure --model claude-sonnet-4-6 --fallback-model claude-opus-4-8
  python backend/run_agnostic_research_report.py "NVIDIA vs AMD AI Chips" --provider groq --model llama-3.3-70b-versatile --format table
        """
    )
    parser.add_argument(
        "subject",
        help="Target subject or topic to research and generate report for.",
    )
    parser.add_argument(
        "--prompt-file", "-p",
        default=None,
        help="Path to Markdown prompt specification file defining desired report structure and format. If omitted, uses standard research report template.",
    )
    parser.add_argument(
        "--provider",
        choices=["azure", "azure-foundry", "groq", "gemini", "iteracompute"],
        default="azure",
        help="LLM provider for cognitive planning, extraction, gap checking, drafting, and synthesis. (Default: azure)",
    )
    parser.add_argument(
        "--model", "-m",
        default="claude-sonnet-4-6",
        help="Model name for generation (e.g. claude-sonnet-4-6, claude-opus-4-8, llama-3.3-70b-versatile, gemini-2.5-pro). (Default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--fallback-model",
        default="claude-opus-4-8",
        help="Secondary model for 429 TPM rate-limit failover. (Default: claude-opus-4-8)",
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "standard", "deep"],
        default="standard",
        help="Execution mode: 'fast' (1 search round, no gap check), 'standard' (2 rounds + gap check), 'deep' (3 rounds + deep gap). (Default: standard)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Directory to save generated Markdown, PDF, and telemetry files. (Default: backend/artifacts)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["tree", "table", "json"],
        default="tree",
        help="Terminal telemetry format to render upon completion. (Default: tree)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive browser login for Entra ID authentication when using Azure.",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress intermediate progress notifications.",
    )
    return parser.parse_args(args)


async def execute_cli(args: argparse.Namespace) -> int:
    subject = args.subject.strip()
    provider = args.provider.lower()
    model = args.model.strip()
    fallback = args.fallback_model.strip() if args.fallback_model else None
    mode = args.mode.lower()
    fmt = args.format.lower()

    if not args.quiet:
        print("=" * 86, flush=True)
        print("          PROMPT-DRIVEN AGNOSTIC RESEARCH & REPORT GENERATION SWARM", flush=True)
        print("=" * 86, flush=True)
        print(f" Subject:         {subject}", flush=True)
        print(f" Prompt File:     {args.prompt_file or 'Default Standard Research Report Template'}", flush=True)
        print(f" LLM Provider:    {provider.upper()}", flush=True)
        print(f" Model Selected:  {model} (Fallback: {fallback or 'None'})", flush=True)
        print(f" Research Mode:   {mode.upper()}", flush=True)
        print(f" Telemetry Fmt:   {fmt.upper()}", flush=True)
        print("-" * 86, flush=True)

    def on_progress(stage: str, msg: str):
        if not args.quiet:
            prefix = "" if msg.startswith("[*]") else "[*] "
            print(f"{prefix}{msg}", flush=True)

    orchestrator = AgnosticResearchOrchestrator(artifacts_dir=args.output_dir)

    try:
        result = await orchestrator.run(
            subject=subject,
            prompt_file=args.prompt_file,
            mode=mode,
            provider=provider,
            model=model,
            fallback_model=fallback,
            output_dir=args.output_dir,
            on_progress=on_progress,
        )

        telemetry = result.telemetry_data
        if fmt == "tree":
            print("\n" + render_tree(telemetry, subject), flush=True)
        elif fmt == "table":
            print("\n" + render_table(telemetry, subject), flush=True)
        elif fmt == "json":
            print(json.dumps(telemetry, indent=2), flush=True)

        print("\n[SUCCESS] Report Generation Completed! Generated Artifacts:")
        print(f"  * PDF Report:      {result.pdf_path}")
        print(f"  * Markdown Report: {result.markdown_path}")
        print(f"  * Telemetry JSON:  {result.telemetry_path}")
        print("")
        return 0

    except Exception as e:
        print(f"\n[ERROR] Agnostic Research Pipeline failed: {e}", file=sys.stderr, flush=True)
        return 1


def main():
    args = parse_args()
    return asyncio.run(execute_cli(args))


if __name__ == "__main__":
    sys.exit(main())
