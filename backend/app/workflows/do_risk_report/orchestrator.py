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
import asyncio
from typing import Dict, Any, List, Optional
from app.workflows.do_risk_report.models import EntityCard, Evidence, ReportResult
from app.workflows.do_risk_report.ledger import EvidenceLedger
from app.workflows.do_risk_report.edgar import EdgarFetcher
from app.workflows.do_risk_report.retrieval import PerplexitySearchQueue, ResultCompactor
from app.workflows.do_risk_report.template_spec import TemplateCompiler, SECTION_DEFINITIONS
from app.workflows.do_risk_report.roles import run_role
from app.workflows.do_risk_report.validator import DeterministicValidator, ValidationAgent, RepairCoordinator
from app.workflows.do_risk_report.renderer import FootnoteTransformer, MarkdownRenderer, DocxRenderer, PdfRenderer

DEFAULT_ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "artifacts")


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
        mode: str = "standard"
    ) -> str:
        """
        Executes search, extraction, gap checking, and drafting for a single section.
        """
        max_rounds = 1 if mode == "fast" else 2
        current_queries = list(static_queries)

        for rnd in range(max_rounds):
            if not current_queries:
                break

            # 1. Web search queue via Perplexity
            search_batches = await self.search_queue.batch_search(current_queries)

            if search_batches:
                # 2. Extract role on Groq (atomic claims with Entity Guard)
                compacted_text = "\n".join(
                    f"Title: {r['title']}\nURL: {r['url']}\nDate: {r.get('date')}\nSnippet: {r['snippet']}"
                    for r in search_batches[:6]
                )
                user_prompt = (
                    f"TARGET COMPANY: {entity.legal_name} (Ticker: {entity.ticker}, CIK: {entity.cik})\n"
                    f"SECTION: {section_name} ({section_title})\n\n"
                    f"SEARCH RESULTS:\n{compacted_text}"
                )
                extract_res = await run_role("extract", user_prompt)
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
                    ledger.add(new_items)

            # 3. Gap check
            sec_rows = ledger.for_section(section_name)
            gap_prompt = (
                f"Section: {section_name}\n"
                f"Evidence Count: {len(sec_rows)}\n"
                f"Evidence Claims: " + "; ".join(f"[{r.id}] {r.claim}" for r in sec_rows[:10])
            )
            gap_res = await run_role("gap", gap_prompt)
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
            f"TARGET COMPANY: {entity.legal_name} ({entity.ticker})\n"
            f"SECTION HEADER: ### {section_title}\n\n"
            f"SECTION EVIDENCE LEDGER ROWS:\n{ledger_text}"
        )
        draft_res = await run_role("draft", draft_prompt)
        return draft_res.get("section_text", f"### {section_title}\n- Data unavailable.")

    async def run(
        self,
        ticker: str,
        mode: str = "standard",
        current_date: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ReportResult:
        """
        Executes the entire D&O Public Risk Underwriting Report pipeline end-to-end.
        """
        start_time = time.time()
        report_id = str(uuid.uuid4())
        telemetry: Dict[str, Any] = {"mode": mode, "stages": {}}

        # Stage 1: Entity Resolution & EDGAR Structured Pull
        t0 = time.time()
        entity = self.edgar.build_entity_card(ticker)
        ledger = EvidenceLedger()
        edgar_count = self.edgar.populate_edgar_ledger(entity, ledger)
        telemetry["stages"]["edgar_resolution_ms"] = round((time.time() - t0) * 1000, 2)
        telemetry["edgar_facts_count"] = edgar_count

        # Stage 2: Parallel Per-Section Research & Drafting
        t1 = time.time()
        static_queries_map = TemplateCompiler.generate_static_queries(entity)
        section_tasks = []

        # Sections to draft (excluding overall_verdict which is handled by Synthesize)
        draft_sections = [s for s in SECTION_DEFINITIONS if s["name"] != "overall_verdict"]

        for s_def in draft_sections:
            sec_name = s_def["name"]
            sec_title = s_def["title"]
            queries = static_queries_map.get(sec_name, [])
            task = self._process_section(sec_name, sec_title, entity, queries, ledger, mode=mode)
            section_tasks.append((sec_name, task))

        section_results = await asyncio.gather(*[t[1] for t in section_tasks])
        sections_map = {section_tasks[i][0]: section_results[i] for i in range(len(section_tasks))}
        telemetry["stages"]["research_and_draft_ms"] = round((time.time() - t1) * 1000, 2)

        # Stage 3: Executive Synthesis & Overall D&O Verdict
        t2 = time.time()
        synth_input = (
            f"TARGET COMPANY: {entity.legal_name} ({entity.ticker})\n\n"
            + "\n\n".join(section_results)
        )
        synth_res = await run_role("synthesize", synth_input)
        risk_tier = synth_res.get("risk_tier", "Contained")
        exec_summary = synth_res.get("executive_summary", "")
        verdict_text = synth_res.get("verdict_text", "## OVERALL D&O UNDERWRITER VERDICT\n- Assessment complete.")
        sections_map["overall_verdict"] = verdict_text
        telemetry["stages"]["synthesis_ms"] = round((time.time() - t2) * 1000, 2)

        # Assemble consolidate raw report text
        consolidated_body = (
            f"Summary\n{exec_summary}\n\n"
            + "\n\n".join(sections_map.values())
        )

        # Stage 4: Dedicated Post-Generation Validation Agent
        t3 = time.time()
        val_agent = ValidationAgent(current_date=current_date)
        validated_report_text = await val_agent.run(consolidated_body)
        telemetry["stages"]["validation_agent_ms"] = round((time.time() - t3) * 1000, 2)

        # Stage 5: Publication Rendering (MD, DOCX, PDF)
        t4 = time.time()
        transformed_body, footnotes = FootnoteTransformer.transform_citations(validated_report_text, ledger)

        base_filename = f"DO_Risk_Report_{entity.ticker}_{report_id[:8]}"
        md_path = os.path.join(self.artifacts_dir, f"{base_filename}.md")
        docx_path = os.path.join(self.artifacts_dir, f"{base_filename}.docx")
        pdf_path = os.path.join(self.artifacts_dir, f"{base_filename}.pdf")

        # 1. Render Markdown
        md_content = MarkdownRenderer.render(entity, risk_tier, transformed_body, footnotes, ledger)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 2. Render DOCX
        DocxRenderer.render(docx_path, entity, risk_tier, transformed_body, footnotes, ledger)

        # 3. Render PDF
        PdfRenderer.render(pdf_path, entity, risk_tier, transformed_body, footnotes, ledger)

        telemetry["stages"]["rendering_ms"] = round((time.time() - t4) * 1000, 2)
        telemetry["total_duration_ms"] = round((time.time() - start_time) * 1000, 2)
        telemetry["evidence_count"] = len(ledger.all_rows())

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
