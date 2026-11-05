"""
Agnostic Research & Report Orchestrator.
Coordinates the end-to-end prompt-driven research workflow:
1. Dynamic Prompt Specification Parsing
2. Parallel Per-Section Planning, Web Search (Perplexity), & Atomic Evidence Extraction
3. Automated Gap Analysis & Research Reruns
4. Concurrent Section Drafting with [E###] Citation Ingestion
5. Cross-Section Synthesis & Executive Verdict Pass
6. Publication Document Rendering (Markdown & ReportLab PDF with Footnotes)
7. Granular Timing Trees & Token Accounting
"""

import os
import re
import time
import uuid
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable

from app.workflows.agnostic_research_report.models import (
    SectionSpec,
    ReportPromptSpec,
    AgnosticEvidence,
    AgnosticReportResult,
)
from app.workflows.agnostic_research_report.spec_parser import MarkdownSpecParser
from app.workflows.agnostic_research_report.ledger import AgnosticEvidenceLedger
from app.workflows.agnostic_research_report.retrieval import PerplexitySearchQueue
from app.workflows.agnostic_research_report.roles import (
    run_role,
    set_active_provider,
    get_active_provider,
    set_fallback_model,
    get_fallback_model,
    PROVIDER_MODELS,
    ROLE_TIER_MAPPING,
)
from app.workflows.agnostic_research_report.renderer import (
    FootnoteTransformer,
    AgnosticMarkdownRenderer,
    AgnosticPdfRenderer,
)

DEFAULT_ARTIFACTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "artifacts"
)


class AgnosticResearchOrchestrator:
    """Cognitive orchestrator managing the prompt-driven research and report pipeline."""

    def __init__(self, artifacts_dir: Optional[str] = None):
        self.artifacts_dir = artifacts_dir or DEFAULT_ARTIFACTS_DIR
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self.search_queue = PerplexitySearchQueue()

    async def _process_section(
        self,
        subject: str,
        section: SectionSpec,
        ledger: AgnosticEvidenceLedger,
        global_rules: str,
        mode: str = "standard",
        model: Optional[str] = None,
        provider: Optional[str] = None,
        fallback_model: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Executes planning, search, extraction, gap checking, and drafting for a single section
        while capturing granular subsection timings and token usage.
        """
        sec_start = time.perf_counter()
        total_retrieval_ms = 0.0
        total_extract_ms = 0.0
        total_gap_ms = 0.0
        total_plan_ms = 0.0
        queries_count = 0
        claims_extracted = 0
        round_substeps: List[Dict[str, Any]] = []

        tokens_in = 0
        tokens_out = 0

        # 1. Planner generates initial targeted queries
        plan_input = (
            f"TARGET SUBJECT: {subject}\n\n"
            f"SECTION: {section.title} ({section.name})\n"
            f"REQUIRED FIELDS / CHECKLIST:\n" + "\n".join(f"- {f}" for f in section.required_fields) + "\n\n"
            f"SECTION INSTRUCTIONS:\n{section.instructions}\n\n"
            f"Formulate up to 3 highly targeted search queries."
        )
        try:
            plan_res, plan_tok, plan_dur, plan_mod = await run_role(
                "plan",
                plan_input,
                model_override=model,
                provider_override=provider,
                fallback_model_override=fallback_model,
            )
            current_queries = plan_res.get("queries", [])
            total_plan_ms = plan_dur
            tokens_in += plan_tok.get("input_tokens", 0)
            tokens_out += plan_tok.get("output_tokens", 0)
        except Exception as e:
            current_queries = [{"text": f"{subject} {section.title}", "domains": []}]
            total_plan_ms = 1.0

        max_rounds = 1 if mode == "fast" else (3 if mode == "deep" else 2)

        for rnd in range(max_rounds):
            if not current_queries:
                break

            # 2. Web search queue via Perplexity
            search_batches, search_meta = await self.search_queue.batch_search_with_timings(current_queries)
            rnd_retrieval_ms = search_meta.get("duration_ms", 0.0)
            total_retrieval_ms += rnd_retrieval_ms
            rnd_queries_count = len(current_queries)
            queries_count += rnd_queries_count

            rnd_extract_ms = 0.0
            rnd_claims = 0

            if search_batches:
                # 3. Extract atomic claims into Evidence Ledger
                compacted_text = "\n".join(
                    f"Title: {r['title']}\nURL: {r['url']}\nDate: {r.get('date')}\nSnippet: {r['snippet']}"
                    for r in search_batches[:10]
                )
                extract_prompt = (
                    f"TARGET SUBJECT: {subject}\n"
                    f"SECTION: {section.title}\n\n"
                    f"SEARCH RESULTS:\n{compacted_text}"
                )
                try:
                    extract_res, ext_tok, ext_dur, ext_mod = await run_role(
                        "extract",
                        extract_prompt,
                        model_override=model,
                        provider_override=provider,
                        fallback_model_override=fallback_model,
                    )
                    rnd_extract_ms = ext_dur
                    total_extract_ms += rnd_extract_ms
                    tokens_in += ext_tok.get("input_tokens", 0)
                    tokens_out += ext_tok.get("output_tokens", 0)
                except Exception:
                    extract_res = {"items": []}

                new_items: List[AgnosticEvidence] = []
                for item_dict in extract_res.get("items", []):
                    try:
                        new_items.append(AgnosticEvidence(
                            id="",
                            section_slug=section.name,
                            claim=item_dict.get("claim", ""),
                            value=item_dict.get("value"),
                            as_of=item_dict.get("as_of"),
                            source_url=item_dict.get("source_url", "https://api.perplexity.ai"),
                            source_domain=item_dict.get("source_url", "").split("/")[2] if "://" in item_dict.get("source_url", "") else "web",
                            source_title=item_dict.get("source_title", "Web Source"),
                            published=item_dict.get("published"),
                            confidence=item_dict.get("confidence", "med"),
                            quote=item_dict.get("quote"),
                        ))
                    except Exception:
                        pass

                if new_items:
                    rnd_claims = len(new_items)
                    claims_extracted += rnd_claims
                    ledger.add(new_items)

            # 4. Gap check if more rounds remain
            rnd_gap_ms = 0.0
            next_queries: List[Dict[str, Any]] = []
            if rnd < max_rounds - 1:
                sec_rows = ledger.for_section(section.name)
                gap_prompt = (
                    f"TARGET SUBJECT: {subject}\n"
                    f"SECTION: {section.title}\n"
                    f"REQUIRED FIELDS:\n" + "\n".join(f"- {f}" for f in section.required_fields) + "\n\n"
                    f"EXTRACTED EVIDENCE CLAIMS ({len(sec_rows)} items):\n"
                    + "\n".join(f"[{r.id}] {r.claim}" for r in sec_rows[:12])
                )
                try:
                    gap_res, gap_tok, gap_dur, gap_mod = await run_role(
                        "gap",
                        gap_prompt,
                        model_override=model,
                        provider_override=provider,
                        fallback_model_override=fallback_model,
                    )
                    rnd_gap_ms = gap_dur
                    total_gap_ms += rnd_gap_ms
                    tokens_in += gap_tok.get("input_tokens", 0)
                    tokens_out += gap_tok.get("output_tokens", 0)
                    next_queries = gap_res.get("queries", [])
                except Exception:
                    next_queries = []

            round_substeps.append({
                "round": rnd + 1,
                "retrieval_ms": round(rnd_retrieval_ms, 2),
                "queries_count": rnd_queries_count,
                "extract_ms": round(rnd_extract_ms, 2),
                "claims_extracted": rnd_claims,
                "gap_ms": round(rnd_gap_ms, 2),
            })

            current_queries = next_queries

        # 5. Draft section narrative citing [E###] tokens
        sec_rows = ledger.for_section(section.name)
        ledger_text = "\n".join(
            f"[{r.id}] ({r.published or 'N/A'}, {r.source_domain}): {r.claim} (Quote: '{r.quote or r.claim}')"
            for r in sec_rows
        ) if sec_rows else "No specific public disclosures found in ledger."

        draft_prompt = (
            f"TARGET SUBJECT: {subject}\n\n"
            f"SECTION HEADER: ## {section.title}\n\n"
            f"GLOBAL INSTRUCTIONS & RULES:\n{global_rules}\n\n"
            f"SECTION SPECIFICATION & DETAILED GUIDELINES:\n{section.instructions}\n\n"
            f"AVAILABLE EVIDENCE LEDGER ROWS:\n{ledger_text}\n\n"
            f"Draft the complete analytical section narrative. Follow all format and bullet rules. Cite facts with [E###] tokens."
        )
        t_d0 = time.perf_counter()
        is_testing = os.environ.get("TESTING") == "true" or os.environ.get("MOCK_ROLES") == "true"
        max_draft_retries = 1 if is_testing else int(os.environ.get("DRAFT_MAX_RETRIES", "4"))
        section_text = ""
        draft_dur = 0.0

        for draft_attempt in range(max_draft_retries):
            try:
                draft_res, draft_tok, draft_dur, draft_mod = await run_role(
                    "draft",
                    draft_prompt,
                    model_override=model,
                    provider_override=provider,
                    fallback_model_override=fallback_model,
                )
                raw_text = draft_res.get("section_text", "")
                if raw_text and not raw_text.strip().endswith("Data unavailable."):
                    section_text = raw_text
                    tokens_in += draft_tok.get("input_tokens", 0)
                    tokens_out += draft_tok.get("output_tokens", 0)
                    break
                elif raw_text:
                    section_text = raw_text
                    tokens_in += draft_tok.get("input_tokens", 0)
                    tokens_out += draft_tok.get("output_tokens", 0)
                    break

                if draft_attempt < max_draft_retries - 1:
                    wait_sec = 10.0 * (draft_attempt + 1)
                    print(f"[*] Section '{section.title}' drafting returned empty. Retrying in {wait_sec:.0f}s (attempt {draft_attempt + 2}/{max_draft_retries})...", flush=True)
                    await asyncio.sleep(wait_sec)
            except Exception as e:
                if draft_attempt < max_draft_retries - 1:
                    wait_sec = 15.0 * (draft_attempt + 1)
                    print(f"[*] [SECTION DRAFT RETRY] Section '{section.title}' drafting encountered error ({e}). Waiting {wait_sec:.0f}s before retry (attempt {draft_attempt + 2}/{max_draft_retries})...", flush=True)
                    await asyncio.sleep(wait_sec)
                else:
                    section_text = f"## {section.title}\n- Section drafting unavailable after {max_draft_retries} attempts: {e}"
                    draft_dur = (time.perf_counter() - t_d0) * 1000

        sec_total_ms = (time.perf_counter() - sec_start) * 1000

        sec_timing = {
            "total_ms": round(sec_total_ms, 2),
            "tokens": {
                "input_tokens": tokens_in,
                "output_tokens": tokens_out,
                "total_tokens": tokens_in + tokens_out,
            },
            "subsections": {
                "planning_ms": round(total_plan_ms, 2),
                "retrieval_ms": round(total_retrieval_ms, 2),
                "extract_ms": round(total_extract_ms, 2),
                "gap_ms": round(total_gap_ms, 2),
                "draft_narrative_ms": round(draft_dur, 2),
                "queries_count": queries_count,
                "claims_extracted": claims_extracted,
                "evidence_cited_count": len(sec_rows),
                "rounds": round_substeps,
            }
        }
        return section_text, sec_timing

    async def run(
        self,
        subject: str,
        prompt_file: Optional[str] = None,
        prompt_markdown: Optional[str] = None,
        mode: str = "standard",
        provider: str = "azure",
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        output_dir: Optional[str] = None,
        on_progress: Optional[Callable[[str, str], None]] = None,
    ) -> AgnosticReportResult:
        """
        Executes the entire prompt-driven research pipeline end-to-end.
        """
        out_dir = Path(output_dir or self.artifacts_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        set_active_provider(provider)
        if fallback_model:
            set_fallback_model(fallback_model)

        def _notify(stage: str, msg: str):
            if on_progress:
                try:
                    on_progress(stage, msg)
                except Exception:
                    pass

        t_global_start = time.perf_counter()
        report_id = str(uuid.uuid4())
        date_str = datetime.now().strftime("%Y-%m-%d")

        # -------------------------------------------------------------
        # Stage 1: Parse Prompt Specification
        # -------------------------------------------------------------
        _notify("stage_1", f"Parsing Markdown Prompt Specification for '{subject}'...")
        if prompt_file:
            spec = MarkdownSpecParser.parse_file(prompt_file)
        elif prompt_markdown:
            spec = MarkdownSpecParser.parse(prompt_markdown)
        else:
            default_template = Path(__file__).parent / "templates" / "standard_research_report.md"
            spec = MarkdownSpecParser.parse_file(str(default_template))

        ledger = AgnosticEvidenceLedger()

        # Differentiate body sections from overarching synthesis sections
        body_sections = [s for s in spec.sections if not s.is_synthesis]
        synth_sections = [s for s in spec.sections if s.is_synthesis]

        # -------------------------------------------------------------
        # Stage 2: Parallel Per-Section Planning, Web Search & Extraction
        # -------------------------------------------------------------
        _notify("stage_2", f"Concurrent Perplexity retrieval & fact extraction across {len(body_sections)} sections...")
        t_s2_start = time.perf_counter()

        async def _run_section_worker(sec_spec: SectionSpec):
            return await self._process_section(
                subject=subject,
                section=sec_spec,
                ledger=ledger,
                global_rules=spec.global_rules,
                mode=mode,
                model=model,
                provider=provider,
                fallback_model=fallback_model,
            )

        section_results = await asyncio.gather(*[_run_section_worker(s) for s in body_sections])
        s2_wall_ms = round((time.perf_counter() - t_s2_start) * 1000, 2)

        drafted_sections_map = {body_sections[i].name: section_results[i][0] for i in range(len(body_sections))}
        sections_timings = {body_sections[i].name: section_results[i][1] for i in range(len(body_sections))}
        _notify("stage_2_done", f"{len(body_sections)} sections researched in {s2_wall_ms / 1000:.2f}s | {len(ledger.all())} atomic facts collected")

        # -------------------------------------------------------------
        # Stage 3: Cross-Section Synthesis Pass
        # -------------------------------------------------------------
        _notify("stage_3", "Synthesizing cross-section executive insights and final verdict...")
        t_s3_start = time.perf_counter()
        synth_timings: Dict[str, Any] = {}
        synth_tokens_in = 0
        synth_tokens_out = 0

        is_testing = os.environ.get("TESTING") == "true" or os.environ.get("MOCK_ROLES") == "true"
        max_synth_retries = 1 if is_testing else int(os.environ.get("SYNTH_MAX_RETRIES", "4"))
        for s_spec in synth_sections:
            synth_input = (
                f"TARGET SUBJECT: {subject}\n\n"
                f"SYNTHESIS SECTION: {s_spec.title}\n"
                f"SECTION INSTRUCTIONS:\n{s_spec.instructions}\n\n"
                f"DRAFTED SECTIONS EVIDENCE BASE:\n"
                + "\n\n".join(drafted_sections_map.values())
            )
            for synth_attempt in range(max_synth_retries):
                try:
                    synth_res, synth_tok, synth_dur, synth_mod = await run_role(
                        "synthesize",
                        synth_input,
                        model_override=model,
                        provider_override=provider,
                        fallback_model_override=fallback_model,
                    )
                    drafted_sections_map[s_spec.name] = synth_res.get("executive_summary") or synth_res.get("verdict_text") or f"## {s_spec.title}\n- Synthesis complete."
                    synth_tokens_in += synth_tok.get("input_tokens", 0)
                    synth_tokens_out += synth_tok.get("output_tokens", 0)
                    synth_timings[s_spec.name] = {
                        "duration_ms": synth_dur,
                        "model": synth_mod,
                        "tokens": synth_tok,
                    }
                    break
                except Exception as e:
                    if synth_attempt < max_synth_retries - 1:
                        wait_sec = 15.0 * (synth_attempt + 1)
                        print(f"[*] [SYNTHESIS RETRY] Section '{s_spec.title}' synthesis encountered error ({e}). Waiting {wait_sec:.0f}s before retry (attempt {synth_attempt + 2}/{max_synth_retries})...", flush=True)
                        await asyncio.sleep(wait_sec)
                    else:
                        drafted_sections_map[s_spec.name] = f"## {s_spec.title}\n- Synthesis unavailable after {max_synth_retries} attempts: {e}"

        s3_wall_ms = round((time.perf_counter() - t_s3_start) * 1000, 2)

        # -------------------------------------------------------------
        # Stage 4: Order All Sections According to Prompt Spec
        # -------------------------------------------------------------
        ordered_sections_text = []
        for s in spec.sections:
            if s.name in drafted_sections_map:
                ordered_sections_text.append(drafted_sections_map[s.name])

        consolidated_raw_text = "\n\n".join(ordered_sections_text)

        # -------------------------------------------------------------
        # Stage 5: File Generation Agent (Markdown & ReportLab PDF)
        # -------------------------------------------------------------
        _notify("stage_5", "Transforming citations and compiling publication Markdown and PDF artifacts...")
        t_s5_start = time.perf_counter()

        transformed_text, footnotes = FootnoteTransformer.transform_citations(consolidated_raw_text, ledger)

        # Compute total token usage
        total_tokens_in = sum(s["tokens"]["input_tokens"] for s in sections_timings.values()) + synth_tokens_in
        total_tokens_out = sum(s["tokens"]["output_tokens"] for s in sections_timings.values()) + synth_tokens_out
        total_tokens = total_tokens_in + total_tokens_out

        # Compute compute vs wall-clock
        t_global_end = time.perf_counter()
        total_wall_ms = round((t_global_end - t_global_start) * 1000, 2)
        total_compute_ms = round(
            sum(s["total_ms"] for s in sections_timings.values()) + s3_wall_ms, 2
        )
        speedup_factor = round(total_compute_ms / total_wall_ms, 2) if total_wall_ms > 0 else 1.0

        slug = re.sub(r"[^\w-]", "_", subject.lower())[:30].strip("_")
        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"Research_Report_{slug}_{timestamp_slug}"

        meta_dict = {
            "date": date_str,
            "subject": subject,
            "model": model or PROVIDER_MODELS.get(provider, {}).get("medium", "default"),
            "provider": provider,
            "evidence_count": len(ledger.all()),
            "citations_count": len(footnotes),
            "total_tokens": total_tokens,
            "duration_seconds": round(total_wall_ms / 1000, 2),
            "concurrency_speedup": f"{speedup_factor:.2f}x",
        }

        # 1. Render Markdown
        md_content = AgnosticMarkdownRenderer.render(
            subject=subject,
            sections_text=[transformed_text],
            footnotes=footnotes,
            closing_statement=spec.closing_statement,
            metadata=meta_dict,
        )
        md_path = out_dir / f"{base_name}.md"
        md_path.write_text(md_content, encoding="utf-8")

        # 2. Render ReportLab PDF
        pdf_path = out_dir / f"{base_name}.pdf"
        AgnosticPdfRenderer.render(
            subject=subject,
            sections_text=[transformed_text],
            footnotes=footnotes,
            output_path=str(pdf_path),
            closing_statement=spec.closing_statement,
            metadata=meta_dict,
        )

        s5_wall_ms = round((time.perf_counter() - t_s5_start) * 1000, 2)

        # 3. Assemble Telemetry Data
        telemetry = {
            "report_id": report_id,
            "subject": subject,
            "started_at": datetime.fromtimestamp(t_global_start).isoformat(),
            "completed_at": datetime.now().isoformat(),
            "total_wall_clock_ms": total_wall_ms,
            "total_compute_ms": total_compute_ms,
            "concurrency_speedup": f"{speedup_factor:.2f}x",
            "tokens": {
                "input_tokens": total_tokens_in,
                "output_tokens": total_tokens_out,
                "total_tokens": total_tokens,
            },
            "stages": {
                "stage_1_spec_parse": {"sections_count": len(spec.sections)},
                "stage_2_research_and_draft": {
                    "wall_clock_ms": s2_wall_ms,
                    "sections": sections_timings,
                },
                "stage_3_synthesis": {
                    "wall_clock_ms": s3_wall_ms,
                    "sections": synth_timings,
                },
                "stage_5_rendering": {
                    "wall_clock_ms": s5_wall_ms,
                    "footnotes_count": len(footnotes),
                },
            },
            "artifacts": {
                "markdown": str(md_path.resolve()),
                "pdf": str(pdf_path.resolve()),
            }
        }

        json_path = out_dir / f"{base_name}_telemetry.json"
        import json
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(telemetry, f, indent=2)

        telemetry["artifacts"]["telemetry_json"] = str(json_path.resolve())

        _notify("stage_5_done", f"Report successfully generated at {pdf_path}")

        return AgnosticReportResult(
            report_id=report_id,
            subject=subject,
            markdown_path=str(md_path.resolve()),
            pdf_path=str(pdf_path.resolve()),
            telemetry_path=str(json_path.resolve()),
            telemetry_data=telemetry,
            evidence_count=len(ledger.all()),
            total_duration_seconds=round(total_wall_ms / 1000, 2),
            total_tokens=total_tokens,
        )
