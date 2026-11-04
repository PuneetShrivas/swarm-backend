"""
D&O Public Risk Report Asyncio Pipeline Orchestrator.
Coordinates the end-to-end DAG execution:
1. Entity Resolution & EDGAR Structured Pull (XBRL + filings, code, no LLM)
2. Parallel Per-Section Retrieval & Fact Extraction into Evidence Ledger
3. Pipelined Section Drafting
4. Executive Synthesis & Overall D&O Underwriter Verdict
5. Dedicated Validation Agent Pass (zero web access, validation-prompt.txt rules)
6. Publication Artifact Rendering (MD, DOCX, PDF)
"""

import os
import time
import uuid
import inspect
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Callable
from app.workflows.do_risk_report.models import EntityCard, Evidence, ReportResult
from app.workflows.do_risk_report.ledger import EvidenceLedger
from app.workflows.do_risk_report.edgar import EdgarFetcher
from app.workflows.do_risk_report.retrieval import PerplexitySearchQueue, ResultCompactor
from app.workflows.do_risk_report.template_spec import TemplateCompiler, SECTION_DEFINITIONS
from app.workflows.do_risk_report.roles import (
    run_role,
    set_active_provider,
    get_active_provider,
    set_fallback_model,
    get_fallback_model,
    PROVIDER_MODELS,
    ROLE_TIER_MAPPING,
)
from app.workflows.do_risk_report.validator import DeterministicValidator, ValidationAgent, RepairCoordinator
from app.workflows.do_risk_report.renderer import FootnoteTransformer, MarkdownRenderer, DocxRenderer, PdfRenderer

DEFAULT_ARTIFACTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "artifacts"
)


class DORiskReportOrchestrator:
    def __init__(self, artifacts_dir: Optional[str] = None):
        self.artifacts_dir = artifacts_dir or DEFAULT_ARTIFACTS_DIR
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self.edgar = EdgarFetcher()
        self.search_queue = PerplexitySearchQueue()

    async def _process_section(
        self,
        section_name: str,
        section_title: str,
        entity: EntityCard,
        static_queries: List[Dict[str, Any]],
        ledger: EvidenceLedger,
        mode: str = "standard",
        section_prompt_rules: str = "",
        master_rules: str = "",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Executes search, extraction, gap checking, and drafting for a single section
        while tracking granular subsection timings.
        """
        sec_start = time.perf_counter()
        total_retrieval_ms = 0.0
        total_extract_ms = 0.0
        total_gap_ms = 0.0
        queries_count = 0
        claims_extracted = 0
        round_substeps: List[Dict[str, Any]] = []

        max_rounds = 1 if mode == "fast" else 2
        current_queries = list(static_queries)

        for rnd in range(max_rounds):
            if not current_queries:
                break

            # 1. Web search queue via Perplexity
            search_batches, search_meta = await self.search_queue.batch_search_with_timings(current_queries)
            rnd_retrieval_ms = search_meta.get("duration_ms", 0.0)
            total_retrieval_ms += rnd_retrieval_ms
            rnd_queries_count = len(current_queries)
            queries_count += rnd_queries_count

            rnd_extract_ms = 0.0
            rnd_claims = 0

            if search_batches:
                # 2. Extract role on Groq (atomic claims with Entity Guard)
                compacted_text = "\n".join(
                    f"Title: {r['title']}\nURL: {r['url']}\nDate: {r.get('date')}\nSnippet: {r['snippet']}"
                    for r in search_batches[:10]
                )
                user_prompt = (
                    f"TARGET COMPANY: {entity.legal_name} (Ticker: {entity.ticker}, CIK: {entity.cik})\n"
                    f"SECTION: {section_name} ({section_title})\n\n"
                    f"SEARCH RESULTS:\n{compacted_text}"
                )
                t_e0 = time.perf_counter()
                try:
                    extract_res = await run_role("extract", user_prompt)
                except Exception as e:
                    print(f"[ORCHESTRATOR NOTE] Role 'extract' for section '{section_name}' encountered error ({e}). Proceeding with existing ledger evidence.", flush=True)
                    extract_res = {"items": []}
                rnd_extract_ms = (time.perf_counter() - t_e0) * 1000
                total_extract_ms += rnd_extract_ms

                new_items: List[Evidence] = []
                for item_dict in extract_res.get("items", []):
                    try:
                        new_items.append(Evidence(
                            id="",
                            section=section_name,
                            claim=item_dict.get("claim", ""),
                            value=item_dict.get("value"),
                            as_of=item_dict.get("as_of"),
                            status=item_dict.get("status", "found"),
                            source_url=item_dict.get("source_url", "https://api.perplexity.ai"),
                            source_type=item_dict.get("source_type", "other"),
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

            # 3. Gap check
            sec_rows = ledger.for_section(section_name)
            gap_prompt = (
                f"Section: {section_name}\n"
                f"Evidence Count: {len(sec_rows)}\n"
                f"Evidence Claims: " + "; ".join(f"[{r.id}] {r.claim}" for r in sec_rows[:10])
            )
            t_g0 = time.perf_counter()
            try:
                gap_res = await run_role("gap", gap_prompt)
            except Exception as e:
                print(f"[ORCHESTRATOR NOTE] Role 'gap' for section '{section_name}' encountered error ({e}). Continuing.", flush=True)
                gap_res = {"queries": []}
            rnd_gap_ms = (time.perf_counter() - t_g0) * 1000
            total_gap_ms += rnd_gap_ms

            round_substeps.append({
                "round": rnd + 1,
                "retrieval_ms": round(rnd_retrieval_ms, 2),
                "queries_count": rnd_queries_count,
                "extract_ms": round(rnd_extract_ms, 2),
                "claims_extracted": rnd_claims,
                "gap_ms": round(rnd_gap_ms, 2),
            })

            current_queries = gap_res.get("queries", [])
            if not current_queries:
                break

        # 4. Draft section narrative citing [E###] IDs
        sec_rows = ledger.for_section(section_name)
        ledger_text = "\n".join(
            f"[{r.id}] ({r.source_type}, {r.published or 'N/A'}): {r.claim} (Quote: '{r.quote or r.claim}')"
            for r in sec_rows
        ) if sec_rows else "No specific public disclosures found in ledger."

        draft_prompt = (
            f"TARGET COMPANY: {entity.legal_name} (Ticker: {entity.ticker}, CIK: {entity.cik}, Domicile: {entity.country_of_domicile}, Exchange: {entity.exchange})\n\n"
            f"SECTION SLUG: {section_name}\n\n"
            f"SECTION HEADER: ### {section_title}\n\n"
            f"MASTER UNDERWRITING GUIDELINES:\n{master_rules}\n\n"
            f"SECTION SPECIFICATION & DETAILED INSTRUCTIONS:\n{section_prompt_rules}\n\n"
            f"SECTION EVIDENCE LEDGER ROWS:\n{ledger_text}\n\n"
            f"INSTRUCTION: Draft the complete, institutional-grade underwriting narrative for '### {section_title}'. Follow every field and bullet point requirement in the section instructions above. Cite evidence strictly with [E###] tokens. If a required field is not present in the ledger, explicitly state that it is not publicly available or not disclosed."
        )
        t_d0 = time.perf_counter()
        try:
            draft_res = await run_role("draft", draft_prompt)
            section_text = draft_res.get("section_text", f"### {section_title}\n- Data unavailable.")
        except Exception as e:
            print(f"Error drafting section '{section_name}': {e}")
            section_text = f"### {section_title}\n- Section drafting unavailable due to upstream API error: {e}"
        draft_ms = (time.perf_counter() - t_d0) * 1000
        sec_total_ms = (time.perf_counter() - sec_start) * 1000

        sec_timing = {
            "total_ms": round(sec_total_ms, 2),
            "subsections": {
                "retrieval_ms": round(total_retrieval_ms, 2),
                "groq_extract_ms": round(total_extract_ms, 2),
                "groq_gap_check_ms": round(total_gap_ms, 2),
                "groq_draft_narrative_ms": round(draft_ms, 2),
                "queries_count": queries_count,
                "claims_extracted": claims_extracted,
                "evidence_cited_count": len(sec_rows),
                "char_length": len(section_text),
                "rounds": round_substeps,
            }
        }
        return section_text, sec_timing

    async def run(
        self,
        ticker: str,
        mode: str = "standard",
        current_date: Optional[str] = None,
        user_id: Optional[str] = None,
        provider: str = "gpt-oss",
        fallback_model: Optional[str] = None,
        on_progress: Optional[Callable[[str, str], None]] = None,
        on_section_complete: Optional[Callable[[str, str, str], Any]] = None,
    ) -> ReportResult:
        """
        Executes the entire D&O Public Risk Underwriting Report pipeline end-to-end,
        capturing granular stage, section, and subsection timings.
        Supports secondary/fallback models for rate-limit failover.
        """
        set_active_provider(provider)
        if fallback_model:
            set_fallback_model(fallback_model)
        active_prov = get_active_provider()
        active_fallback = get_fallback_model()
        prov_models = PROVIDER_MODELS.get(active_prov, PROVIDER_MODELS["gpt-oss"])
        synth_model = prov_models.get(ROLE_TIER_MAPPING.get("synthesize", "reasoning"), "unknown")
        val_model = prov_models.get(ROLE_TIER_MAPPING.get("repair", "reasoning"), "unknown")
        def _notify(stage_code: str, detail: str = ""):
            if on_progress:
                try:
                    on_progress(stage_code, detail)
                except Exception:
                    pass

        start_time = time.perf_counter()
        report_id = str(uuid.uuid4())

        # Stage 1: Entity Resolution & EDGAR Structured Pull
        _notify("stage_1", f"Resolving Entity Card & SEC EDGAR US-GAAP facts for {ticker.upper()}...")
        t0 = time.perf_counter()
        entity, card_timings = self.edgar.build_entity_card_with_timings(ticker)
        ledger = EvidenceLedger()
        edgar_count, edgar_timings = self.edgar.populate_edgar_ledger_with_timings(entity, ledger)
        stage1_ms = round((time.perf_counter() - t0) * 1000, 2)
        _notify("stage_1_done", f"{entity.legal_name} ({entity.cik}) - {edgar_count} facts collected in {stage1_ms:,.1f} ms")

        stage1_telemetry = {
            "wall_clock_ms": stage1_ms,
            "subsections": {
                "ticker_to_cik_lookup_ms": card_timings["ticker_to_cik_lookup_ms"],
                "submissions_metadata_fetch_ms": card_timings["submissions_metadata_fetch_ms"],
                "company_facts_xbrl_fetch_ms": edgar_timings["company_facts_xbrl_fetch_ms"],
                "fact_extraction_and_ledger_ms": edgar_timings["fact_extraction_and_ledger_ms"],
                "facts_found_count": edgar_count,
            }
        }

        # Stage 2: Parallel Per-Section Research & Drafting
        t1 = time.perf_counter()
        template_spec = TemplateCompiler.get_template_spec()
        static_queries_map = TemplateCompiler.generate_static_queries(entity, template_spec=template_spec)

        # Sections to draft dynamically from prompt (excluding overall_verdict which is handled by Synthesize)
        draft_sections = [s for s in template_spec.sections if s.name != "overall_verdict"]
        _notify("stage_2", f"Concurrent Perplexity retrieval & Groq drafting across {len(draft_sections)} parallel sections...")

        async def _run_section_worker(s_spec):
            sec_name = s_spec.name
            sec_title = s_spec.title
            queries = static_queries_map.get(sec_name, [])
            draft_text, timings = await self._process_section(
                section_name=sec_name,
                section_title=sec_title,
                entity=entity,
                static_queries=queries,
                ledger=ledger,
                mode=mode,
                section_prompt_rules=s_spec.section_prompt,
                master_rules=template_spec.system_prompt_template,
            )
            if on_section_complete:
                try:
                    if inspect.iscoroutinefunction(on_section_complete):
                        await on_section_complete(sec_name, sec_title, draft_text)
                    else:
                        on_section_complete(sec_name, sec_title, draft_text)
                except Exception as e:
                    print(f"on_section_complete callback error: {e}")
            return sec_name, draft_text, timings

        raw_section_results = await asyncio.gather(*[_run_section_worker(s) for s in draft_sections])
        stage2_ms = round((time.perf_counter() - t1) * 1000, 2)

        section_results = [r[1] for r in raw_section_results]
        sections_map = {r[0]: r[1] for r in raw_section_results}
        sections_timings = {r[0]: r[2] for r in raw_section_results}
        _notify("stage_2_done", f"All {len(draft_sections)} sections researched and drafted in {stage2_ms:,.1f} ms")

        stage2_telemetry = {
            "wall_clock_ms": stage2_ms,
            "parallel_workers_count": len(draft_sections),
            "sections": sections_timings,
        }

        # Stage 3: Executive Synthesis & Overall D&O Verdict
        _notify("stage_3", "Synthesizing executive summary and determining D&O underwriter verdict on Groq LPUs...")
        t2 = time.perf_counter()
        verdict_spec = next((s for s in template_spec.sections if s.name == "overall_verdict"), None)
        verdict_instructions = verdict_spec.section_prompt if verdict_spec else ""
        synth_input = (
            f"TARGET COMPANY: {entity.legal_name} (Ticker: {entity.ticker}, CIK: {entity.cik})\n\n"
            f"MASTER UNDERWRITING GUIDELINES:\n{template_spec.system_prompt_template}\n\n"
            f"OVERALL VERDICT SPECIFICATION:\n{verdict_instructions}\n\n"
            f"DRAFTED SECTIONS EVIDENCE & NARRATIVES:\n"
            + "\n\n".join(section_results)
        )
        synth_res = await run_role("synthesize", synth_input)
        stage3_ms = round((time.perf_counter() - t2) * 1000, 2)
        risk_tier = synth_res.get("risk_tier", "Contained")
        exec_summary = synth_res.get("executive_summary", "")
        verdict_text = synth_res.get("verdict_text", "## OVERALL D&O UNDERWRITER VERDICT\n- Assessment complete.")
        sections_map["overall_verdict"] = verdict_text
        _notify("stage_3_done", f"Overall Risk Tier: '{risk_tier}' synthesized in {stage3_ms:,.1f} ms")

        stage3_telemetry = {
            "wall_clock_ms": stage3_ms,
            "subsections": {
                "synthesis_ms": stage3_ms,
                "model_used": synth_model,
                "provider": active_prov,
                "risk_tier": risk_tier,
                "char_length": len(exec_summary) + len(verdict_text),
            }
        }

        # Assemble consolidate raw report text
        consolidated_body = (
            f"Summary\n{exec_summary}\n\n"
            + "\n\n".join(sections_map.values())
        )

        # Stage 4: Dedicated Post-Generation Validation Agent
        _notify("stage_4", "Running zero-web-access Validation Agent audit & repair pass...")
        t3 = time.perf_counter()
        t_det0 = time.perf_counter()
        det_issues = DeterministicValidator.validate(consolidated_body, ledger)
        det_ms = round((time.perf_counter() - t_det0) * 1000, 2)

        t_val0 = time.perf_counter()
        val_agent = ValidationAgent(current_date=current_date, provider=active_prov)
        validated_report_text = await val_agent.run(consolidated_body)
        val_agent_ms = round((time.perf_counter() - t_val0) * 1000, 2)
        stage4_ms = round((time.perf_counter() - t3) * 1000, 2)
        _notify("stage_4_done", f"Validation audit complete ({len(det_issues)} mechanical issues) in {stage4_ms:,.1f} ms")

        stage4_telemetry = {
            "wall_clock_ms": stage4_ms,
            "subsections": {
                "deterministic_validator_ms": det_ms,
                "deterministic_issues_count": len(det_issues),
                "validation_agent_pass_ms": val_agent_ms,
                "repair_coordinator_ms": 0.0,
                "repair_rounds": 0,
                "model_used": val_model,
                "provider": active_prov,
            }
        }

        # Stage 5: Publication Rendering (MD, DOCX, PDF)
        _notify("stage_5", "Transforming citations and compiling publication deliverables (MD, DOCX, PDF)...")
        t4 = time.perf_counter()
        t_fn0 = time.perf_counter()
        transformed_body, footnotes = FootnoteTransformer.transform_citations(validated_report_text, ledger)
        fn_ms = round((time.perf_counter() - t_fn0) * 1000, 2)

        base_filename = f"DO_Risk_Report_{entity.ticker}_{report_id[:8]}"
        md_path = os.path.join(self.artifacts_dir, f"{base_filename}.md")
        docx_path = os.path.join(self.artifacts_dir, f"{base_filename}.docx")
        pdf_path = os.path.join(self.artifacts_dir, f"{base_filename}.pdf")

        report_date = current_date or time.strftime("%B %d, %Y")

        # 1. Render Markdown
        t_md0 = time.perf_counter()
        md_content = MarkdownRenderer.render(entity, risk_tier, transformed_body, footnotes, ledger, report_date=report_date)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        md_ms = round((time.perf_counter() - t_md0) * 1000, 2)

        # 2. Render DOCX
        t_docx0 = time.perf_counter()
        DocxRenderer.render(docx_path, entity, risk_tier, transformed_body, footnotes, ledger, report_date=report_date)
        docx_ms = round((time.perf_counter() - t_docx0) * 1000, 2)

        # 3. Render PDF
        t_pdf0 = time.perf_counter()
        PdfRenderer.render(pdf_path, entity, risk_tier, transformed_body, footnotes, ledger, report_date=report_date)
        pdf_ms = round((time.perf_counter() - t_pdf0) * 1000, 2)

        stage5_ms = round((time.perf_counter() - t4) * 1000, 2)
        _notify("stage_5_done", f"Rendered MD ({os.path.getsize(md_path)/1024:.1f} KB), DOCX ({os.path.getsize(docx_path)/1024:.1f} KB), PDF ({os.path.getsize(pdf_path)/1024:.1f} KB) in {stage5_ms:,.1f} ms")

        stage5_telemetry = {
            "wall_clock_ms": stage5_ms,
            "subsections": {
                "footnote_transformation_ms": fn_ms,
                "footnotes_count": len(footnotes),
                "render_markdown_ms": md_ms,
                "render_docx_ms": docx_ms,
                "render_pdf_ms": pdf_ms,
            }
        }

        # Concurrency & Total Compute calculation
        total_wall_clock_ms = round((time.perf_counter() - start_time) * 1000, 2)
        sec_compute_ms = sum(s["total_ms"] for s in sections_timings.values())
        total_compute_ms = round(stage1_ms + sec_compute_ms + stage3_ms + stage4_ms + stage5_ms, 2)
        speedup_multiplier = f"{total_compute_ms / max(total_wall_clock_ms, 1.0):.2f}x"

        telemetry = {
            "mode": mode,
            "llm_provider": active_prov,
            "fallback_model": active_fallback,
            "total_wall_clock_ms": total_wall_clock_ms,
            "total_compute_ms": total_compute_ms,
            "concurrency_speedup": speedup_multiplier,
            "edgar_facts_count": edgar_count,
            "evidence_count": len(ledger.all_rows()),
            "stages": {
                # Backward-compatible flat keys
                "edgar_resolution_ms": stage1_ms,
                "research_and_draft_ms": stage2_ms,
                "synthesis_ms": stage3_ms,
                "validation_agent_ms": stage4_ms,
                "rendering_ms": stage5_ms,
                # Hierarchical keys
                "stage_1_edgar_resolution": stage1_telemetry,
                "stage_2_research_and_draft": stage2_telemetry,
                "stage_3_synthesis_and_verdict": stage3_telemetry,
                "stage_4_validation_agent": stage4_telemetry,
                "stage_5_artifact_rendering": stage5_telemetry,
            },
            "total_duration_ms": total_wall_clock_ms,
        }

        artifacts = [
            {"filename": f"{base_filename}.md", "path": md_path, "type": "markdown", "size": os.path.getsize(md_path)},
            {"filename": f"{base_filename}.docx", "path": docx_path, "type": "docx", "size": os.path.getsize(docx_path)},
            {"filename": f"{base_filename}.pdf", "path": pdf_path, "type": "pdf", "size": os.path.getsize(pdf_path)},
        ]

        return ReportResult(
            report_id=report_id,
            ticker=entity.ticker,
            entity=entity,
            risk_tier=risk_tier,
            executive_summary=exec_summary,
            sections=sections_map,
            raw_report_text=consolidated_body,
            validated_report_text=validated_report_text,
            artifacts=artifacts,
            evidence_count=len(ledger.all_rows()),
            telemetry=telemetry,
        )
