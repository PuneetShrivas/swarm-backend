#!/usr/bin/env python
"""Standalone CLI Entrypoint for Agnostic Research & Report Generation Swarm.

Can be run directly from within the agnostic_workflow folder:
    python run_workflow.py "NVIDIA Corporation" --prompt-file web-search-prompt.md --provider azure --model claude-sonnet-4-6
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path

# Ensure package directory is on sys.path
package_dir = Path(__file__).resolve().parent
if str(package_dir) not in sys.path:
    sys.path.insert(0, str(package_dir))
parent_dir = package_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from agnostic_workflow.orchestrator import AgnosticResearchOrchestrator
from agnostic_workflow.telemetry import render_tree, render_table


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Standalone Prompt-Driven Agnostic Research & Report Generation Swarm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_workflow.py "Solid State Battery Commercialization"
  python run_workflow.py "Quantum Computing in Drug Discovery" --prompt-file path/to/prompt.md --mode standard
  python run_workflow.py "NVIDIA Corporation" --prompt-file prompt.md --provider azure --model claude-sonnet-4-6 --fallback-model claude-opus-4-8
  python run_workflow.py "AMD AI Roadmaps" --provider groq --model llama-3.3-70b-versatile --format table
        """,
    )
    parser.add_argument(
        "subject",
        help="Target subject or topic to research and generate report for.",
    )
    parser.add_argument(
        "--prompt-file", "-p",
        default=None,
        help="Path to Markdown or text prompt specification file defining desired report structure and format. If omitted, uses standard template.",
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
        help="Directory to save generated Markdown, PDF, and telemetry files. (Default: ./artifacts)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["tree", "table", "json"],
        default="tree",
        help="Terminal telemetry format to render upon completion. (Default: tree)",
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
            print(f"[*] {msg}", flush=True)

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

        print("\n" + "=" * 86, flush=True)
        if fmt == "tree":
            print(render_tree(telemetry, subject), flush=True)
        elif fmt == "table":
            print(render_table(telemetry, subject), flush=True)
        else:
            print(json.dumps(telemetry, indent=2), flush=True)

        print("\nGENERATION COMPLETE:", flush=True)
        print(f"  - Markdown Report: {result.markdown_path}", flush=True)
        print(f"  - PDF Report:      {result.pdf_path}", flush=True)
        print(f"  - Telemetry Data:  {result.telemetry_path}", flush=True)
        print(f"  - Facts Collected: {result.evidence_count} items", flush=True)
        print(f"  - Total Tokens:    {result.total_tokens:,}", flush=True)
        print(f"  - Duration:        {result.total_duration_seconds:.2f}s\n", flush=True)
        return 0

    except Exception as e:
        print(f"\n[ERROR] Pipeline execution terminated: {e}", file=sys.stderr, flush=True)
        return 1


def main() -> int:
    args = parse_args()
    return asyncio.run(execute_cli(args))


if __name__ == "__main__":
    sys.exit(main())
