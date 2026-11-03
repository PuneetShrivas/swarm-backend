"""
Single-Instruction CLI Runner for D&O Public Risk Report System.
Provides granular hierarchical timing trees, table formatting, and end-to-end execution.
"""

import os
import sys
import json
import time
import asyncio
import argparse
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Ensure backend root directory is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.workflows.do_risk_report.orchestrator import DORiskReportOrchestrator
from app.workflows.do_risk_report.models import ReportResult


def format_ms(ms: float) -> str:
    """Formats millisecond durations cleanly."""
    if ms >= 1000:
        return f"{ms / 1000:.2f}s ({ms:,.1f} ms)"
    return f"{ms:,.1f} ms"


def render_tree(telemetry: Dict[str, Any], entity_ticker: str) -> str:
    """Renders hierarchical granular timings as an indented ASCII tree."""
    stages = telemetry.get("stages", {})
    wall_ms = telemetry.get("total_wall_clock_ms", 0.0)
    compute_ms = telemetry.get("total_compute_ms", 0.0)
    speedup = telemetry.get("concurrency_speedup", "1.00x")

    lines = []
    lines.append("-" * 80)
    lines.append("                           GRANULAR TIMINGS TREE")
    lines.append("-" * 80)
    lines.append(f"Pipeline Execution [{entity_ticker}] (Wall-Clock: {format_ms(wall_ms)} | Compute: {format_ms(compute_ms)} | Concurrency: {speedup})")

    # Stage 1: EDGAR
    s1 = stages.get("stage_1_edgar_resolution", {})
    s1_subs = s1.get("subsections", {})
    lines.append(f"├── Stage 1: SEC EDGAR & Entity Resolution [{format_ms(s1.get('wall_clock_ms', 0.0))}]")
    lines.append(f"│   ├── Ticker-to-CIK Resolution: {format_ms(s1_subs.get('ticker_to_cik_lookup_ms', 0.0))}")
    lines.append(f"│   ├── Submissions Metadata Fetch: {format_ms(s1_subs.get('submissions_metadata_fetch_ms', 0.0))}")
    lines.append(f"│   ├── US-GAAP Company Facts Parse: {format_ms(s1_subs.get('company_facts_xbrl_fetch_ms', 0.0))}")
    lines.append(f"│   └── Evidence Ledger Population: {format_ms(s1_subs.get('fact_extraction_and_ledger_ms', 0.0))} ({s1_subs.get('facts_found_count', 0)} facts found)")

    # Stage 2: Research & Drafting
    s2 = stages.get("stage_2_research_and_draft", {})
    s2_secs = s2.get("sections", {})
    sec_names = list(s2_secs.keys())
    lines.append(f"├── Stage 2: Research & Drafting ({s2.get('parallel_workers_count', len(sec_names))} Parallel Sections) [{format_ms(s2.get('wall_clock_ms', 0.0))}]")

    prov_label = telemetry.get("llm_provider", "Groq").capitalize()

    for i, name in enumerate(sec_names):
        is_last_sec = (i == len(sec_names) - 1)
        prefix_sec = "│   └──" if is_last_sec else "│   ├──"
        branch_child = "│       " if not is_last_sec else "        "

        s_info = s2_secs[name]
        s_subs = s_info.get("subsections", {})
        rounds = s_subs.get("rounds", [])

        lines.append(f"{prefix_sec} [{i+1:02d}] {name} [{format_ms(s_info.get('total_ms', 0.0))}]")
        if rounds and len(rounds) > 1:
            for r in rounds:
                r_num = r.get("round", 1)
                lines.append(f"{branch_child}├── Round {r_num} Search (Pplx Batch): {format_ms(r.get('retrieval_ms', 0.0))} ({r.get('queries_count', 0)} queries)")
                lines.append(f"{branch_child}├── Round {r_num} Claim Extraction ({prov_label}): {format_ms(r.get('extract_ms', 0.0))} ({r.get('claims_extracted', 0)} claims)")
                lines.append(f"{branch_child}├── Round {r_num} Gap Analysis ({prov_label}): {format_ms(r.get('gap_ms', 0.0))}")
            lines.append(f"{branch_child}└── {prov_label} Narrative Draft: {format_ms(s_subs.get('groq_draft_narrative_ms', 0.0))} ({s_subs.get('char_length', 0):,} chars, {s_subs.get('evidence_cited_count', 0)} citations)")
        else:
            lines.append(f"{branch_child}├── Perplexity Batch Search: {format_ms(s_subs.get('retrieval_ms', 0.0))} ({s_subs.get('queries_count', 0)} queries)")
            lines.append(f"{branch_child}├── {prov_label} Claim Extraction: {format_ms(s_subs.get('groq_extract_ms', 0.0))} ({s_subs.get('claims_extracted', 0)} claims)")
            lines.append(f"{branch_child}├── {prov_label} Gap Analysis: {format_ms(s_subs.get('groq_gap_check_ms', 0.0))}")
            lines.append(f"{branch_child}└── {prov_label} Narrative Draft: {format_ms(s_subs.get('groq_draft_narrative_ms', 0.0))} ({s_subs.get('char_length', 0):,} chars, {s_subs.get('evidence_cited_count', 0)} citations)")

    # Stage 3: Synthesis
    s3 = stages.get("stage_3_synthesis_and_verdict", {})
    s3_subs = s3.get("subsections", {})
    s3_model = s3_subs.get("model_used", "reasoning")
    s3_prov = s3_subs.get("provider", telemetry.get("llm_provider", "llm")).upper()
    lines.append(f"├── Stage 3: Executive Synthesis & D&O Verdict [{format_ms(s3.get('wall_clock_ms', 0.0))}]")
    lines.append(f"│   └── Synthesis ({s3_prov} - {s3_model}): {format_ms(s3_subs.get('synthesis_ms', s3_subs.get('groq_synthesis_ms', 0.0)))} (Verdict: {s3_subs.get('risk_tier', 'Contained')})")

    # Stage 4: Validation
    s4 = stages.get("stage_4_validation_agent", {})
    s4_subs = s4.get("subsections", {})
    s4_model = s4_subs.get("model_used", "reasoning")
    s4_prov = s4_subs.get("provider", telemetry.get("llm_provider", "llm")).upper()
    lines.append(f"├── Stage 4: Post-Generation Validation Agent (Zero Web Access) [{format_ms(s4.get('wall_clock_ms', 0.0))}]")
    lines.append(f"│   ├── Layer 1 Deterministic Verification: {format_ms(s4_subs.get('deterministic_validator_ms', 0.0))} ({s4_subs.get('deterministic_issues_count', 0)} issues)")
    lines.append(f"│   └── Layer 2 Validation Agent Pass ({s4_prov} - {s4_model}): {format_ms(s4_subs.get('validation_agent_pass_ms', 0.0))}")

    # Stage 5: Rendering
    s5 = stages.get("stage_5_artifact_rendering", {})
    s5_subs = s5.get("subsections", {})
    lines.append(f"└── Stage 5: Publication Artifact Rendering [{format_ms(s5.get('wall_clock_ms', 0.0))}]")
    lines.append(f"    ├── Footnote Citation Transformation: {format_ms(s5_subs.get('footnote_transformation_ms', 0.0))} ({s5_subs.get('footnotes_count', 0)} footnotes)")
    lines.append(f"    ├── Markdown Document Build: {format_ms(s5_subs.get('render_markdown_ms', 0.0))}")
    lines.append(f"    ├── Word (.docx) Document Build: {format_ms(s5_subs.get('render_docx_ms', 0.0))}")
    lines.append(f"    └── PDF Document Build (ReportLab): {format_ms(s5_subs.get('render_pdf_ms', 0.0))}")

    lines.append("-" * 80)
    return "\n".join(lines)


def render_table(telemetry: Dict[str, Any], entity_ticker: str) -> str:
    """Renders hierarchical granular timings as an ASCII column table."""
    stages = telemetry.get("stages", {})
    lines = []
    lines.append("-" * 80)
    lines.append("                           GRANULAR TIMINGS TABLE")
    lines.append("-" * 80)
    lines.append(f"{'STAGE / SECTION / SUBSECTION':<58} {'DURATION':>20}")
    lines.append("-" * 80)

    # Stage 1
    s1 = stages.get("stage_1_edgar_resolution", {})
    s1_subs = s1.get("subsections", {})
    lines.append(f"{'Stage 1: SEC EDGAR & Entity Resolution':<58} {format_ms(s1.get('wall_clock_ms', 0.0)):>20}")
    lines.append(f"{'  ├── Ticker-to-CIK Resolution':<58} {format_ms(s1_subs.get('ticker_to_cik_lookup_ms', 0.0)):>20}")
    lines.append(f"{'  ├── Submissions Metadata Fetch':<58} {format_ms(s1_subs.get('submissions_metadata_fetch_ms', 0.0)):>20}")
    lines.append(f"{'  ├── US-GAAP Company Facts Parse':<58} {format_ms(s1_subs.get('company_facts_xbrl_fetch_ms', 0.0)):>20}")
    lines.append(f"{'  └── Evidence Ledger Population':<58} {format_ms(s1_subs.get('fact_extraction_and_ledger_ms', 0.0)):>20}")

    # Stage 2
    s2 = stages.get("stage_2_research_and_draft", {})
    s2_secs = s2.get("sections", {})
    lines.append(f"{'Stage 2: Research & Drafting (Parallel)':<58} {format_ms(s2.get('wall_clock_ms', 0.0)):>20}")
    for name, s_info in s2_secs.items():
        lines.append(f"{'  ├── ' + name:<58} {format_ms(s_info.get('total_ms', 0.0)):>20}")

    # Stage 3
    s3 = stages.get("stage_3_synthesis_and_verdict", {})
    lines.append(f"{'Stage 3: Executive Synthesis & Verdict':<58} {format_ms(s3.get('wall_clock_ms', 0.0)):>20}")

    # Stage 4
    s4 = stages.get("stage_4_validation_agent", {})
    lines.append(f"{'Stage 4: Post-Generation Validation Agent':<58} {format_ms(s4.get('wall_clock_ms', 0.0)):>20}")

    # Stage 5
    s5 = stages.get("stage_5_artifact_rendering", {})
    lines.append(f"{'Stage 5: Publication Artifact Rendering':<58} {format_ms(s5.get('wall_clock_ms', 0.0)):>20}")

    lines.append("-" * 80)
    wall_ms = telemetry.get("total_wall_clock_ms", 0.0)
    compute_ms = telemetry.get("total_compute_ms", 0.0)
    speedup = telemetry.get("concurrency_speedup", "1.00x")
    lines.append(f"{'Total Wall-Clock Time:':<58} {format_ms(wall_ms):>20}")
    lines.append(f"{'Total Cumulative Processing Time:':<58} {format_ms(compute_ms):>20}")
    lines.append(f"{'Concurrency Speedup Multiplier:':<58} {speedup:>20}")
    lines.append("-" * 80)
    return "\n".join(lines)


async def execute_cli(args: argparse.Namespace) -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    ticker = args.ticker.strip().upper()
    mode = args.mode.lower()
    fmt = args.format.lower()
    date_override = args.date
    output_dir = args.output_dir
    provider = getattr(args, "provider", "gpt-oss").lower()
    fallback_model = getattr(args, "fallback_model", None)

    if not args.quiet:
        print("=" * 80, flush=True)
        print("           D&O PUBLIC RISK REPORT GENERATOR & UNDERWRITING PIPELINE", flush=True)
        print("=" * 80, flush=True)
        print(f"Target Ticker:  {ticker}", flush=True)
        print(f"Execution Mode: {mode} ({'1 search round' if mode == 'fast' else '2 search rounds + gap check'})", flush=True)
        print(f"LLM Provider:   {provider.upper()}", flush=True)
        if fallback_model:
            print(f"Fallback Model: {fallback_model}", flush=True)
        print(f"Display Format: {fmt}", flush=True)
        if date_override:
            print(f"Date Override:  {date_override}", flush=True)
        if output_dir:
            print(f"Artifacts Dir:  {output_dir}", flush=True)
        print("-" * 80, flush=True)

    def on_progress(stage_code: str, detail: str):
        if args.quiet:
            return
        if stage_code == "stage_1":
            print(f"[1/5] {detail}", flush=True)
        elif stage_code == "stage_1_done":
            print(f"      └── {detail}", flush=True)
        elif stage_code == "stage_2":
            print(f"[2/5] {detail}", flush=True)
        elif stage_code == "stage_2_done":
            print(f"      └── {detail}", flush=True)
        elif stage_code == "stage_3":
            print(f"[3/5] {detail}", flush=True)
        elif stage_code == "stage_3_done":
            print(f"      └── {detail}", flush=True)
        elif stage_code == "stage_4":
            print(f"[4/5] {detail}", flush=True)
        elif stage_code == "stage_4_done":
            print(f"      └── {detail}", flush=True)
        elif stage_code == "stage_5":
            print(f"[5/5] {detail}", flush=True)
        elif stage_code == "stage_5_done":
            print(f"      └── {detail}\n", flush=True)

    orchestrator = DORiskReportOrchestrator(artifacts_dir=output_dir)

    try:
        result: ReportResult = await orchestrator.run(
            ticker=ticker,
            mode=mode,
            current_date=date_override,
            provider=provider,
            fallback_model=fallback_model,
            on_progress=on_progress
        )
    except Exception as e:
        print(f"\n[ERROR] Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Format output
    if fmt == "json":
        if args.json_output:
            with open(args.json_output, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2)
            print(f"Full JSON output written to: {args.json_output}")
        else:
            print(json.dumps(result.telemetry, indent=2))
    elif fmt == "table":
        print(render_table(result.telemetry, ticker))
    else:  # default 'tree'
        print(render_tree(result.telemetry, ticker))

    # Summary
    print("=" * 80)
    print("FINAL UNDERWRITING ASSESSMENT")
    print("=" * 80)
    print(f"Entity:              {result.entity.legal_name} ({result.entity.ticker}, CIK: {result.entity.cik})")
    print(f"D&O Risk Verdict:    {result.risk_tier}")
    print(f"Evidence Facts:      {result.evidence_count} verified citations in ledger")
    print("Delivered Artifacts:")
    for a in result.artifacts:
        size_kb = a.get("size", 0) / 1024
        print(f"  • {a['type'].upper():<10} {a['path']} ({size_kb:.1f} KB)")
    print("=" * 80)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="do_risk_report",
        description="D&O Public Risk Report Generator & Underwriting Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Execution Modes:
  fast      Executes 1 retrieval round per section. Ideal for quick evaluations, testing, and debugging.
  standard  Executes 2 retrieval rounds with gap analysis on high-stakes disclosures. Full production depth.

Output Formats:
  tree      (Default) Indented ASCII tree visualizing hierarchical pipeline stages, sections, and subsections.
  table     Tabular column formatting displaying stage and section durations.
  json      Emits full machine-readable JSON telemetry.

Examples:
  python backend/run_do_risk_report.py AAPL
  python backend/run_do_risk_report.py MSFT --mode fast --format tree
  python backend/run_do_risk_report.py NVDA --mode standard --format table --output-dir ./reports
  python backend/run_do_risk_report.py TSLA --mode fast --format json --json-output tsla_result.json
        """
    )
    parser.add_argument(
        "ticker",
        help="Stock ticker symbol of the target public company (e.g. AAPL, MSFT, TSLA)"
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "standard"],
        default="standard",
        help="Pipeline execution mode: 'fast' (1 search round) or 'standard' (2 rounds + gap analysis). Default: standard"
    )
    parser.add_argument(
        "--provider", "--llm-provider", "--model-family",
        dest="provider",
        choices=["gpt-oss", "qwen", "gemini", "iteracompute", "azure"],
        default=os.environ.get("LLM_PROVIDER", "gpt-oss").lower(),
        help="LLM provider family for non-Perplexity tasks: 'gpt-oss', 'qwen', 'gemini', 'iteracompute', or 'azure'. Default: gpt-oss"
    )
    parser.add_argument(
        "--fallback-model", "--secondary-model",
        dest="fallback_model",
        default=os.environ.get("AZURE_FALLBACK_MODEL") or os.environ.get("LLM_FALLBACK_MODEL"),
        help="Secondary/fallback model name to fail over to upon encountering 429 TPM rate limits (e.g. claude-sonnet-4-6)"
    )
    parser.add_argument(
        "--format",
        choices=["tree", "table", "json"],
        default="tree",
        help="Timing display visualization format. Default: tree"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Custom destination directory to save output artifacts (.md, .docx, .pdf). Default: backend/artifacts"
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Reference date override for the validation agent (format: YYYY-MM-DD). Default: today"
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional file path to write complete ReportResult JSON payload"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Mute progress step output, printing only the final timings and deliverables"
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    exit_code = asyncio.run(execute_cli(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
