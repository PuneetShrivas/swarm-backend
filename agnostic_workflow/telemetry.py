"""Granular Hierarchical Timings & Token Accounting Subsystem.

Renders indented ASCII trees and columnar tables displaying stage latencies,
token consumption per step, compute vs wall-clock time, and concurrency speedups.
Completely standalone.
"""

from typing import Dict, Any, List


def format_ms(ms: float) -> str:
    """Formats millisecond durations cleanly as seconds or milliseconds."""
    if ms >= 1000:
        return f"{ms / 1000:.2f}s ({ms:,.1f} ms)"
    return f"{ms:,.1f} ms"


def render_tree(telemetry: Dict[str, Any], subject: str) -> str:
    """Renders hierarchical granular timings and token accounting as an indented ASCII tree."""
    stages = telemetry.get("stages", {})
    wall_ms = telemetry.get("total_wall_clock_ms", 0.0)
    compute_ms = telemetry.get("total_compute_ms", 0.0)
    speedup = telemetry.get("concurrency_speedup", "1.00x")
    tokens = telemetry.get("tokens", {})

    lines = []
    lines.append("=" * 86)
    lines.append("                     AGNOSTIC RESEARCH PIPELINE: GRANULAR TIMINGS TREE")
    lines.append("=" * 86)
    lines.append(f" Subject:            {subject.upper()}")
    lines.append(f" Total Wall-Clock:   {format_ms(wall_ms)} | Compute Time: {format_ms(compute_ms)} | Concurrency: {speedup}")
    lines.append(f" Total Tokens:       {tokens.get('total_tokens', 0):,} (Input: {tokens.get('input_tokens', 0):,} | Output: {tokens.get('output_tokens', 0):,})")
    lines.append("-" * 86)

    # Stage 1: Prompt Spec Parsing
    s1 = stages.get("stage_1_spec_parse", {})
    lines.append(f"├── Stage 1: Dynamic Prompt Specification Parse")
    lines.append(f"│   └── Parsed Sections: {s1.get('sections_count', 0)} sections extracted from markdown prompt")

    # Stage 2: Research & Drafting
    s2 = stages.get("stage_2_research_and_draft", {})
    s2_secs = s2.get("sections", {})
    sec_names = list(s2_secs.keys())
    lines.append(f"├── Stage 2: Concurrent Research & Section Drafting ({len(sec_names)} Parallel Sections) [{format_ms(s2.get('wall_clock_ms', 0.0))}]")

    for i, name in enumerate(sec_names):
        is_last = (i == len(sec_names) - 1)
        prefix_sec = "│   └──" if is_last else "│   ├──"
        branch_child = "        " if is_last else "│       "

        s_info = s2_secs[name]
        s_subs = s_info.get("subsections", {})
        s_tok = s_info.get("tokens", {})
        rounds = s_subs.get("rounds", [])

        lines.append(f"{prefix_sec} [{i+1:02d}] {name} [{format_ms(s_info.get('total_ms', 0.0))} | {s_tok.get('total_tokens', 0):,} tokens]")
        lines.append(f"{branch_child}├── Plan Search Queries: {format_ms(s_subs.get('planning_ms', 0.0))}")
        if rounds and len(rounds) > 1:
            for r in rounds:
                r_num = r.get("round", 1)
                lines.append(f"{branch_child}├── Round {r_num} Web Search (Perplexity): {format_ms(r.get('retrieval_ms', 0.0))} ({r.get('queries_count', 0)} queries)")
                lines.append(f"{branch_child}├── Round {r_num} Atomic Extraction: {format_ms(r.get('extract_ms', 0.0))} ({r.get('claims_extracted', 0)} claims)")
                if r.get("gap_ms", 0) > 0:
                    lines.append(f"{branch_child}├── Round {r_num} Gap Analysis: {format_ms(r.get('gap_ms', 0.0))}")
        else:
            lines.append(f"{branch_child}├── Perplexity Web Search: {format_ms(s_subs.get('retrieval_ms', 0.0))} ({s_subs.get('queries_count', 0)} queries)")
            lines.append(f"{branch_child}├── Atomic Extraction: {format_ms(s_subs.get('extract_ms', 0.0))} ({s_subs.get('claims_extracted', 0)} claims)")
            if s_subs.get("gap_ms", 0) > 0:
                lines.append(f"{branch_child}├── Gap Analysis: {format_ms(s_subs.get('gap_ms', 0.0))}")

        lines.append(f"{branch_child}└── Section Narrative Drafting: {format_ms(s_subs.get('draft_narrative_ms', 0.0))} ({s_subs.get('evidence_cited_count', 0)} evidence citations)")

    # Stage 3: Synthesis
    s3 = stages.get("stage_3_synthesis", {})
    s3_secs = s3.get("sections", {})
    lines.append(f"├── Stage 3: Cross-Section Executive Synthesis [{format_ms(s3.get('wall_clock_ms', 0.0))}]")
    if s3_secs:
        for s_name, s_data in s3_secs.items():
            tok_count = s_data.get("tokens", {}).get("total_tokens", 0)
            lines.append(f"│   └── Synthesis ({s_name}): {format_ms(s_data.get('duration_ms', 0.0))} [{tok_count:,} tokens]")
    else:
        lines.append(f"│   └── (No separate synthesis sections defined in prompt)")

    # Stage 5: File Generation
    s5 = stages.get("stage_5_rendering", {})
    lines.append(f"└── Stage 4: Publication File Generation Agent [{format_ms(s5.get('wall_clock_ms', 0.0))}]")
    lines.append(f"    ├── Footnote Citations Transformed: {s5.get('footnotes_count', 0)} footnotes")
    lines.append(f"    ├── Publication Markdown Document Built")
    lines.append(f"    └── Publication ReportLab PDF Built (NumberedCanvas 'Page X of Y')")

    lines.append("=" * 86)
    return "\n".join(lines)


def render_table(telemetry: Dict[str, Any], subject: str) -> str:
    """Renders hierarchical timings and tokens as an ASCII column table."""
    stages = telemetry.get("stages", {})
    wall_ms = telemetry.get("total_wall_clock_ms", 0.0)
    compute_ms = telemetry.get("total_compute_ms", 0.0)
    speedup = telemetry.get("concurrency_speedup", "1.00x")
    tokens = telemetry.get("tokens", {})

    lines = []
    lines.append("=" * 86)
    lines.append("                    AGNOSTIC RESEARCH PIPELINE: TIMINGS & TOKENS TABLE")
    lines.append("=" * 86)
    lines.append(f"{'STAGE / SECTION / TASK':<52} | {'DURATION':<16} | {'TOKENS'}")
    lines.append("-" * 86)

    # Stage 1
    lines.append(f"{'Stage 1: Prompt Specification Parse':<52} | {'N/A':<16} | 0")

    # Stage 2
    s2 = stages.get("stage_2_research_and_draft", {})
    s2_secs = s2.get("sections", {})
    lines.append(f"{'Stage 2: Concurrent Research & Section Drafting':<52} | {format_ms(s2.get('wall_clock_ms', 0.0)):<16} | -")
    for name, s_info in s2_secs.items():
        s_tok = s_info.get("tokens", {}).get("total_tokens", 0)
        lines.append(f"{'  ├── ' + name:<52} | {format_ms(s_info.get('total_ms', 0.0)):<16} | {s_tok:,}")

    # Stage 3
    s3 = stages.get("stage_3_synthesis", {})
    s3_secs = s3.get("sections", {})
    lines.append(f"{'Stage 3: Executive Cross-Section Synthesis':<52} | {format_ms(s3.get('wall_clock_ms', 0.0)):<16} | -")
    for name, s_data in s3_secs.items():
        tok = s_data.get("tokens", {}).get("total_tokens", 0)
        lines.append(f"{'  └── ' + name:<52} | {format_ms(s_data.get('duration_ms', 0.0)):<16} | {tok:,}")

    # Stage 5
    s5 = stages.get("stage_5_rendering", {})
    lines.append(f"{'Stage 4: Publication Artifact Rendering (MD & PDF)':<52} | {format_ms(s5.get('wall_clock_ms', 0.0)):<16} | 0")

    lines.append("-" * 86)
    lines.append(f"{'TOTAL WALL-CLOCK DURATION:':<52} | {format_ms(wall_ms):<16} | -")
    lines.append(f"{'CUMULATIVE PROCESSING TIME:':<52} | {format_ms(compute_ms):<16} | -")
    lines.append(f"{'CONCURRENCY SPEEDUP FACTOR:':<52} | {speedup:<16} | -")
    lines.append(f"{'TOTAL TOKENS CONSUMED:':<52} | -                | {tokens.get('total_tokens', 0):,}")
    lines.append("=" * 86)
    return "\n".join(lines)
