"""
Unit and Integration Test Suite for D&O Public Risk Report System.
"""

import os
import tempfile
import unittest
from app.workflows.do_risk_report.models import (
    Evidence,
    EntityCard,
    SectionSpec,
    TemplateSpec,
    ValidationIssue,
    ReportResult,
)
from app.workflows.do_risk_report.ledger import EvidenceLedger


class TestDORiskReportModels(unittest.TestCase):
    def test_evidence_model_validation(self):
        ev = Evidence(
            id="E001",
            section="company_snapshot",
            claim="Annual revenue reported at $383.29B for FY2023",
            value="$383.29B",
            as_of="2023-09-30",
            status="found",
            source_url="https://www.sec.gov/edgar/data/320193/000032019323000106/aapl-20230930.htm",
            source_type="filing",
            confidence="high",
            quote="Total net sales: $383,285 million"
        )
        self.assertEqual(ev.id, "E001")
        self.assertEqual(ev.status, "found")
        self.assertEqual(ev.confidence, "high")
        self.assertEqual(ev.source_type, "filing")

    def test_entity_card_model(self):
        card = EntityCard(
            ticker="AAPL",
            legal_name="Apple Inc.",
            cik="0000320193",
            former_names=["Apple Computer, Inc."],
            exchange="NASDAQ",
            country_of_domicile="United States",
            cpi_score="69/100, rank 24, CPI 2023"
        )
        self.assertEqual(card.ticker, "AAPL")
        self.assertEqual(card.cik, "0000320193")
        self.assertIn("Apple Computer, Inc.", card.former_names)

    def test_prompt_templates_exist(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_dir = os.path.join(base_dir, "app", "workflows", "do_risk_report", "prompts")
        web_search_path = os.path.join(prompts_dir, "web_search_prompt.txt")
        validation_path = os.path.join(prompts_dir, "validation_prompt.txt")

        self.assertTrue(os.path.isfile(web_search_path), f"Missing {web_search_path}")
        self.assertTrue(os.path.isfile(validation_path), f"Missing {validation_path}")

        with open(web_search_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("0.01%-tier senior D&O underwriter", content)
            self.assertIn("COMPANY SNAPSHOT", content)
            self.assertIn("OVERALL D&O UNDERWRITER VERDICT", content)

        with open(validation_path, "r", encoding="utf-8") as f:
            v_content = f.read()
            self.assertIn("validation-and-correction pass", v_content)
            self.assertIn("{{currentDate}}", v_content)


class TestEvidenceLedger(unittest.TestCase):
    def setUp(self):
        self.ledger = EvidenceLedger()

    def test_add_and_deduplicate(self):
        e1 = Evidence(
            id="E001",
            section="securities_litigation",
            claim="Class action filed alleging misleading guidance",
            source_url="https://courtlistener.com/docket/123",
            source_type="court",
            confidence="high"
        )
        e2 = Evidence(
            id="E002",
            section="securities_litigation",
            claim="Class action filed alleging misleading guidance",
            source_url="https://courtlistener.com/docket/123",  # duplicate
            source_type="court",
            confidence="high"
        )
        e3 = Evidence(
            id="E003",
            section="securities_litigation",
            claim="Class action filed alleging misleading guidance",
            source_url="https://law360.com/articles/456",  # different source
            source_type="news",
            confidence="med"
        )

        added = self.ledger.add([e1, e2, e3])
        self.assertEqual(added, 2)
        self.assertEqual(len(self.ledger.all_rows()), 2)

    def test_section_filtering_and_citation_resolution(self):
        e1 = Evidence(
            id="E010",
            section="governance_culture",
            claim="Audit Committee Chair resigned after 1 year",
            source_url="https://sec.gov/edgar/1",
            source_type="filing",
            confidence="high"
        )
        e2 = Evidence(
            id="E011",
            section="financial_overview",
            claim="Gross debt totaled $105B",
            source_url="https://sec.gov/edgar/2",
            source_type="filing",
            confidence="high"
        )
        self.ledger.add([e1, e2])

        gov_rows = self.ledger.for_section("governance_culture")
        self.assertEqual(len(gov_rows), 1)
        self.assertEqual(gov_rows[0].id, "E010")

        # Citation lookup
        resolved = self.ledger.resolve_citation("E010")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.claim, "Audit Committee Chair resigned after 1 year")

        # Citation lookup with brackets
        resolved_bracket = self.ledger.resolve_citation("[E011]")
        self.assertIsNotNone(resolved_bracket)
        self.assertEqual(resolved_bracket.claim, "Gross debt totaled $105B")

        # Missing lookup
        self.assertIsNone(self.ledger.resolve_citation("[E999]"))

    def test_two_source_rule_check(self):
        e1 = Evidence(
            id="E001",
            section="securities_litigation",
            claim="Settled class action for $25 million",
            source_url="https://sec.gov/edgar/1",
            source_type="filing",
            confidence="high"
        )
        self.ledger.add([e1])
        self.assertFalse(self.ledger.check_two_source_rule("Settled class action for $25 million"))

        e2 = Evidence(
            id="E002",
            section="securities_litigation",
            claim="Settled class action for $25 million",
            source_url="https://reuters.com/article/settlement",
            source_type="news",
            confidence="high"
        )
        self.ledger.add([e2])
        self.assertTrue(self.ledger.check_two_source_rule("Settled class action for $25 million"))

    def test_jsonl_checkpoint_and_restore(self):
        e1 = Evidence(
            id="E001",
            section="financial_overview",
            claim="Current cash and equivalents $29.96B",
            value="$29.96B",
            source_url="https://sec.gov/edgar/10k",
            source_type="filing",
            confidence="high"
        )
        self.ledger.add([e1])

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            saved_count = self.ledger.to_jsonl(tmp_path)
            self.assertEqual(saved_count, 1)

            new_ledger = EvidenceLedger()
            restored_count = new_ledger.from_jsonl(tmp_path)
            self.assertEqual(restored_count, 1)
            self.assertEqual(new_ledger.resolve_citation("E001").value, "$29.96B")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


from app.workflows.do_risk_report.edgar import EdgarFetcher


class TestEdgarFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = EdgarFetcher()

    def test_cik_resolution_and_entity_card(self):
        cik = self.fetcher.resolve_cik("AAPL")
        self.assertEqual(cik, "0000320193")

        card = self.fetcher.build_entity_card("AAPL")
        self.assertEqual(card.ticker, "AAPL")
        self.assertEqual(card.cik, "0000320193")
        self.assertTrue(len(card.legal_name) > 0)
        self.assertEqual(card.country_of_domicile, "United States")
        self.assertIn("Transparency International", card.cpi_score)

    def test_xbrl_parsing_and_ledger_population(self):
        card = self.fetcher.build_entity_card("AAPL")
        ledger = EvidenceLedger()
        added = self.fetcher.populate_edgar_ledger(card, ledger)
        self.assertGreater(added, 3)

        fin_rows = ledger.for_section("financial_overview")
        self.assertGreater(len(fin_rows), 0)

        # Confirm revenue trend was extracted in descending order
        rev_row = next((r for r in fin_rows if "Revenue trend" in r.claim), None)
        self.assertIsNotNone(rev_row)
        self.assertIn("CY2023", rev_row.claim) if "CY2023" in rev_row.claim else self.assertIn("2023", rev_row.claim)

        # Confirm total assets is populated in company snapshot
        snapshot_rows = ledger.for_section("company_snapshot")
        assets_row = next((r for r in snapshot_rows if "Total assets" in r.claim), None)
        self.assertIsNotNone(assets_row)
        self.assertIn("$", assets_row.value)


import asyncio
from app.workflows.do_risk_report.retrieval import ResultCompactor, PerplexitySearchQueue


class TestRetrievalSubsystem(unittest.TestCase):
    def test_clean_snippet_length_and_formatting(self):
        long_text = "This is a factual claim about securities litigation. " * 30
        cleaned = ResultCompactor.clean_snippet(long_text, max_chars=100)
        self.assertLessEqual(len(cleaned), 105)
        self.assertTrue(cleaned.endswith("..."))

    def test_deduplicate_syndicated_results(self):
        results = [
            {"title": "Apple Faces Lawsuit Over Cloud Storage", "snippet": "Plaintiffs allege antitrust violations in iCloud pricing model.", "url": "https://reuters.com/1"},
            {"title": "Apple Faces Lawsuit Over Cloud Storage", "snippet": "Plaintiffs allege antitrust violations in iCloud pricing model.", "url": "https://yahoo.com/finance/1"},
            {"title": "Unique Article About Board Governance", "snippet": "Board elected new lead independent director.", "url": "https://wsj.com/2"}
        ]
        deduped = ResultCompactor.deduplicate_results(results)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["title"], "Apple Faces Lawsuit Over Cloud Storage")
        self.assertEqual(deduped[1]["title"], "Unique Article About Board Governance")

    def test_perplexity_queue_search_and_batch(self):
        queue = PerplexitySearchQueue()
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(queue.search("Apple securities class action lawsuit", domains=["courtlistener.com"]))
            self.assertGreater(len(res), 0)
            self.assertIn("snippet", res[0])
            self.assertIn("url", res[0])

            batch_queries = [
                {"text": "Apple SEC investigation formal order", "domains": ["sec.gov"]},
                {"text": "Apple credit rating Fitch Moody's", "domains": ["fitchratings.com"]}
            ]
            batch_res = loop.run_until_complete(queue.batch_search(batch_queries))
            self.assertGreaterEqual(len(batch_res), 2)
        finally:
            loop.close()


from app.workflows.do_risk_report.template_spec import TemplateCompiler


class TestTemplateCompiler(unittest.TestCase):
    def test_get_template_spec_compilation(self):
        spec = TemplateCompiler.get_template_spec()
        self.assertEqual(spec.id, "do_underwriting_lens_v1")
        self.assertGreaterEqual(len(spec.sections), 12)
        section_names = [s.name for s in spec.sections]
        self.assertIn("company_snapshot", section_names)
        self.assertIn("news_updates", section_names)
        self.assertIn("financial_overview", section_names)
        self.assertIn("securities_class_action_risk", section_names)
        self.assertIn("overall_verdict", section_names)

        self.assertIn("0.01%-tier senior D&O underwriter", spec.system_prompt_template)
        self.assertIn("validation-and-correction pass", spec.validation_rules_template)

    def test_generate_static_queries(self):
        card = EntityCard(
            ticker="AAPL",
            legal_name="Apple Inc.",
            cik="0000320193",
            exchange="NASDAQ"
        )
        queries = TemplateCompiler.generate_static_queries(card)
        self.assertIn("company_snapshot", queries)
        self.assertIn("securities_class_action_risk", queries)

        sca_queries = queries["securities_class_action_risk"]
        self.assertGreater(len(sca_queries), 0)
        self.assertTrue(any("Apple Inc." in q["text"] for q in sca_queries))
        self.assertIn("courtlistener.com", sca_queries[0]["domains"])


from app.workflows.do_risk_report.roles import run_role, _extract_json_from_llm_response


class TestRolesSubsystem(unittest.TestCase):
    def test_json_extractor_helpers(self):
        # Raw json
        d1 = _extract_json_from_llm_response('{"status": "ok", "value": 42}')
        self.assertEqual(d1.get("status"), "ok")

        # Fenced markdown json
        fenced = "Here is the result:\n```json\n{\"risk_tier\": \"Elevated\", \"score\": 85}\n```\nDone."
        d2 = _extract_json_from_llm_response(fenced)
        self.assertEqual(d2.get("risk_tier"), "Elevated")

    def test_run_role_execution(self):
        loop = asyncio.new_event_loop()
        try:
            # Plan role
            plan_out = loop.run_until_complete(run_role("plan", "Entity: Apple Inc."))
            self.assertIn("queries", plan_out)

            # Extract role with realistic search snippet
            sample_search = (
                "Company: Apple Inc. (AAPL). On 2024-01-10, Apple Inc. settled a shareholder securities class action "
                "lawsuit for $25 million in federal court. Source: https://courtlistener.com/docket/123"
            )
            extract_out = loop.run_until_complete(run_role("extract", sample_search))
            self.assertIn("items", extract_out)

            # Draft role with realistic ledger row
            sample_ledger_input = (
                "Section: Securities Class Action Risk. Evidence Rows:\n"
                "[E001] Apple Inc. settled shareholder securities class action for $25 million in federal court on 2024-01-10. "
                "Status: found. Source: https://courtlistener.com/docket/123"
            )
            draft_out = loop.run_until_complete(run_role("draft", sample_ledger_input))
            self.assertIn("section_text", draft_out)
            self.assertTrue(len(draft_out.get("section_text", "")) > 0)

            # Synthesize role
            synth_out = loop.run_until_complete(run_role("synthesize", "Drafted sections summary"))
            self.assertIn("risk_tier", synth_out)
            self.assertIn("band_register", synth_out)
            self.assertEqual(synth_out["risk_tier"], "Contained")
        finally:
            loop.close()


from app.workflows.do_risk_report.validator import DeterministicValidator, ValidationAgent


class TestValidationSubsystem(unittest.TestCase):
    def test_deterministic_citation_validation(self):
        ledger = EvidenceLedger()
        ledger.add([
            Evidence(
                id="E001",
                section="company_snapshot",
                claim="Valid claim",
                source_url="https://sec.gov",
                confidence="high"
            )
        ])

        valid_text = "This report cites [E001] properly."
        issues = DeterministicValidator.validate_citations(valid_text, ledger)
        self.assertEqual(len(issues), 0)

        invalid_text = "This report cites [E001] and fake [E999]."
        issues = DeterministicValidator.validate_citations(invalid_text, ledger)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, "E999")

    def test_validation_agent_news_cutoff_and_ordering(self):
        val_agent = ValidationAgent(current_date="2026-11-03")
        report = (
            "### UPDATES / PRESS RELEASES / NEWS\n"
            "- 15-Jan-2026 - Major product launch - [news] - revenue impact - reuters\n"
            "- 10-Oct-2024 - Old event outside 12-month window - [litigation] - old matter - courtlistener\n"
            "- 20-Aug-2026 - Leadership change CFO departure - [leadership] - governance - 8-K\n"
            "- No resolvable date news item - [other] - gap - none\n"
        )
        corrected = val_agent.apply_deterministic_corrections(report)
        self.assertIn("15-Jan-2026", corrected)
        self.assertIn("20-Aug-2026", corrected)
        # 10-Oct-2024 is >12 months before 2026-11-03, should be removed
        self.assertNotIn("10-Oct-2024", corrected)
        # Unresolvable date line should be removed
        self.assertNotIn("No resolvable date news item", corrected)

    def test_validation_agent_share_price_date_relabeling(self):
        val_agent = ValidationAgent(current_date="2026-11-03")
        report = "Share price: current (2026-10-28) $180.50 vs $160.00"
        corrected = val_agent.apply_deterministic_corrections(report)
        self.assertIn("Share price: last close (2026-10-28)", corrected)

    def test_validation_agent_empty_heading_handling(self):
        val_agent = ValidationAgent(current_date="2026-11-03")
        report = "### FORWARD-LOOKING STRATEGIC RISK\n\n### NEXT SECTION\n- Content"
        corrected = val_agent.apply_deterministic_corrections(report)
        self.assertIn("Data unavailable.", corrected)


from app.workflows.do_risk_report.renderer import FootnoteTransformer, MarkdownRenderer, DocxRenderer, PdfRenderer


class TestRendererSubsystem(unittest.TestCase):
    def setUp(self):
        self.entity = EntityCard(
            ticker="AAPL",
            legal_name="Apple Inc.",
            cik="0000320193",
            exchange="NASDAQ"
        )
        self.ledger = EvidenceLedger()
        self.ledger.add([
            Evidence(
                id="E001",
                section="financial_overview",
                claim="Gross debt totaled $95.28B",
                source_url="https://sec.gov/10k",
                source_type="filing",
                published="2023-11-03",
                confidence="high",
                quote="Long-term debt was $95,281M"
            ),
            Evidence(
                id="E002",
                section="securities_litigation",
                claim="Securities lawsuit dismissed in federal court",
                source_url="https://courtlistener.com/1",
                source_type="court",
                published="2024-02-15",
                confidence="high",
                quote="Court granted motion to dismiss without prejudice."
            )
        ])

    def test_footnote_transformer(self):
        text = "Company debt was reported [E001]. Prior class action was dismissed [E002]."
        transformed, footnotes = FootnoteTransformer.transform_citations(text, self.ledger)

        self.assertIn("[1]", transformed)
        self.assertIn("[2]", transformed)
        self.assertEqual(len(footnotes), 2)
        self.assertEqual(footnotes[0]["id"], "E001")
        self.assertEqual(footnotes[1]["id"], "E002")

    def test_markdown_rendering(self):
        text = "### COMPANY SNAPSHOT\n- Legal name: Apple Inc. [E001]"
        transformed, footnotes = FootnoteTransformer.transform_citations(text, self.ledger)
        md = MarkdownRenderer.render(self.entity, "Contained", transformed, footnotes, self.ledger)

        self.assertIn("# APPLE INC.", md)
        self.assertIn("FOOTNOTE CITATIONS", md)
        self.assertIn("APPENDIX: LIMITATIONS", md)

    def test_docx_and_pdf_rendering(self):
        text = "### COMPANY SNAPSHOT\n- Legal name: Apple Inc. [E001]\n### FINANCIAL OVERVIEW\n- Total debt: $95B [E001]"
        transformed, footnotes = FootnoteTransformer.transform_citations(text, self.ledger)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            docx_path = tmp_docx.name
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            pdf_path = tmp_pdf.name

        try:
            DocxRenderer.render(docx_path, self.entity, "Contained", transformed, footnotes, self.ledger)
            self.assertTrue(os.path.isfile(docx_path))
            self.assertGreater(os.path.getsize(docx_path), 500)

            PdfRenderer.render(pdf_path, self.entity, "Contained", transformed, footnotes, self.ledger)
            self.assertTrue(os.path.isfile(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 500)
        finally:
            if os.path.exists(docx_path):
                os.remove(docx_path)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)


from app.workflows.do_risk_report.orchestrator import DORiskReportOrchestrator


class TestDORiskReportOrchestrator(unittest.TestCase):
    def test_pipeline_e2e_fast_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orch = DORiskReportOrchestrator(artifacts_dir=tmpdir)
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(
                    orch.run(ticker="AAPL", mode="fast", current_date="2026-11-03")
                )
                self.assertIsNotNone(result)
                self.assertEqual(result.ticker, "AAPL")
                self.assertIn("Apple", result.entity.legal_name)
                self.assertGreater(result.evidence_count, 0)
                self.assertEqual(len(result.artifacts), 3)

                # Confirm file artifacts were written to disk
                for art in result.artifacts:
                    self.assertTrue(os.path.isfile(art["path"]))
                    self.assertGreater(art["size"], 0)

                # Check telemetry
                self.assertIn("stages", result.telemetry)
                self.assertIn("edgar_resolution_ms", result.telemetry["stages"])
                self.assertIn("research_and_draft_ms", result.telemetry["stages"])
                self.assertIn("synthesis_ms", result.telemetry["stages"])
                self.assertIn("validation_agent_ms", result.telemetry["stages"])
                self.assertIn("rendering_ms", result.telemetry["stages"])
            finally:
                loop.close()


from app.agents.registry import agent_registry


class TestSpecializedAgentsDiscovery(unittest.TestCase):
    def test_agent_registry_discovers_specialist_and_validator(self):
        agent_registry.reload()
        specialist = agent_registry.get("do_risk_specialist")
        self.assertIsNotNone(specialist, "do_risk_specialist should be discovered by registry")
        self.assertEqual(specialist.config.id, "do_risk_specialist")
        self.assertIn("underwriting", specialist.config.role.lower())

        validator = agent_registry.get("do_risk_validator")
        self.assertIsNotNone(validator, "do_risk_validator should be discovered by registry")
        self.assertEqual(validator.config.id, "do_risk_validator")
        self.assertIn("validation", validator.config.role.lower())


from fastapi.testclient import TestClient
from app.main import app
from app.workflows.default_workflows import get_default_workflows, DEFAULT_DO_RISK_REPORT_WORKFLOW_ID


class TestWorkflowSeedingAndEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_default_workflow_seeding(self):
        defaults = get_default_workflows()
        self.assertEqual(len(defaults), 2)
        wf_ids = [w["id"] for w in defaults]
        self.assertIn(DEFAULT_DO_RISK_REPORT_WORKFLOW_ID, wf_ids)

        do_wf = next(w for w in defaults if w["id"] == DEFAULT_DO_RISK_REPORT_WORKFLOW_ID)
        self.assertIn("D&O Public Risk Report", do_wf["title"])
        step_ids = [s["id"] for s in do_wf["steps"]]
        self.assertIn("step_entity_edgar", step_ids)
        self.assertIn("step_validation_agent", step_ids)
        self.assertIn("step_report_artifacts", step_ids)

    def test_get_templates_api(self):
        resp = self.client.get("/api/do-risk-report/templates")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["id"], "do_underwriting_lens_v1")
        self.assertGreaterEqual(len(data["sections"]), 12)

    def test_validate_api_endpoint(self):
        report_payload = {
            "report_text": "### UPDATES / PRESS RELEASES / NEWS\n- 10-Oct-2024 - Old news - [litigation] - out - courtlistener\n- 15-Jan-2026 - Valid news - [news] - in - reuters\n\n### FINANCIAL OVERVIEW\n- Revenue: $383B",
            "current_date": "2026-11-03"
        }
        resp = self.client.post("/api/do-risk-report/validate", json=report_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "validated")
        self.assertIn("15-Jan-2026", data["validated_report"])
        self.assertNotIn("10-Oct-2024", data["validated_report"])


from app.workflows.do_risk_report.models import (
    EdgarSubstageTiming,
    SectionSubsectionTiming,
    SectionTiming,
    ValidationSubsectionTiming,
    RenderingSubsectionTiming,
    ReportTelemetry,
)
from app.workflows.do_risk_report.edgar import EdgarFetcher
from app.workflows.do_risk_report.retrieval import PerplexitySearchQueue
from app.workflows.do_risk_report.roles import run_role_with_timings
from app.workflows.do_risk_report.cli import build_parser, render_tree, render_table


class TestGranularTimingTelemetry(unittest.TestCase):
    def test_timing_telemetry_models_serialization(self):
        edgar_t = EdgarSubstageTiming(
            ticker_to_cik_lookup_ms=120.5,
            submissions_metadata_fetch_ms=250.0,
            company_facts_xbrl_fetch_ms=450.0,
            fact_extraction_and_ledger_ms=180.0,
            facts_found_count=24
        )
        self.assertEqual(edgar_t.facts_found_count, 24)
        self.assertEqual(edgar_t.ticker_to_cik_lookup_ms, 120.5)

        sec_sub = SectionSubsectionTiming(
            retrieval_ms=1100.0,
            groq_extract_ms=1400.0,
            groq_gap_check_ms=600.0,
            groq_draft_narrative_ms=900.0,
            queries_count=3,
            claims_extracted=5,
            evidence_cited_count=8,
            char_length=1500
        )
        sec_t = SectionTiming(total_ms=4000.0, subsections=sec_sub)
        self.assertEqual(sec_t.total_ms, 4000.0)
        self.assertEqual(sec_t.subsections.queries_count, 3)

        rep_t = ReportTelemetry(
            mode="fast",
            total_wall_clock_ms=25000.0,
            total_compute_ms=75000.0,
            concurrency_speedup="3.00x",
            edgar_facts_count=24,
            evidence_count=45,
            stages={
                "stage_1_edgar_resolution": {"wall_clock_ms": 1000.0, "subsections": edgar_t.model_dump()},
                "stage_2_research_and_draft": {"wall_clock_ms": 20000.0, "sections": {"company_snapshot": sec_t.model_dump()}}
            }
        )
        data = rep_t.model_dump()
        self.assertEqual(data["concurrency_speedup"], "3.00x")
        self.assertIn("stage_1_edgar_resolution", data["stages"])

    def test_edgar_fetcher_with_timings(self):
        edgar = EdgarFetcher()
        card, card_timings = edgar.build_entity_card_with_timings("AAPL")
        self.assertEqual(card.ticker, "AAPL")
        self.assertIn("ticker_to_cik_lookup_ms", card_timings)
        self.assertIn("submissions_metadata_fetch_ms", card_timings)

        ledger = EvidenceLedger()
        count, ledger_timings = edgar.populate_edgar_ledger_with_timings(card, ledger)
        self.assertGreaterEqual(count, 1)
        self.assertIn("company_facts_xbrl_fetch_ms", ledger_timings)
        self.assertIn("fact_extraction_and_ledger_ms", ledger_timings)
        self.assertEqual(ledger_timings["facts_found_count"], count)

    def test_roles_with_timings(self):
        res, meta = asyncio.run(run_role_with_timings(
            "extract",
            "TARGET COMPANY: Apple Inc.\nSECTION: company_snapshot\n\nSEARCH RESULTS: Apple reported $383B revenue.",
            mock_response={"items": [{"claim": "Revenue $383B", "status": "found"}]}
        ))
        self.assertIn("items", res)
        self.assertIn("duration_ms", meta)
        self.assertEqual(meta["role"], "extract")


class TestCLIRunner(unittest.TestCase):
    def test_cli_parser_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["AAPL"])
        self.assertEqual(args.ticker, "AAPL")
        self.assertEqual(args.mode, "standard")
        self.assertEqual(args.format, "tree")
        self.assertIsNone(args.output_dir)
        self.assertFalse(args.quiet)

    def test_cli_parser_custom_flags(self):
        parser = build_parser()
        args = parser.parse_args(["MSFT", "--mode", "fast", "--format", "table", "--quiet", "--output-dir", "./tmp_rep"])
        self.assertEqual(args.ticker, "MSFT")
        self.assertEqual(args.mode, "fast")
        self.assertEqual(args.format, "table")
        self.assertTrue(args.quiet)
        self.assertEqual(args.output_dir, "./tmp_rep")

    def test_render_tree_output(self):
        sample_telemetry = {
            "total_wall_clock_ms": 30000.0,
            "total_compute_ms": 90000.0,
            "concurrency_speedup": "3.00x",
            "stages": {
                "stage_1_edgar_resolution": {
                    "wall_clock_ms": 1200.0,
                    "subsections": {
                        "ticker_to_cik_lookup_ms": 150.0,
                        "submissions_metadata_fetch_ms": 250.0,
                        "company_facts_xbrl_fetch_ms": 600.0,
                        "fact_extraction_and_ledger_ms": 200.0,
                        "facts_found_count": 24,
                    }
                },
                "stage_2_research_and_draft": {
                    "wall_clock_ms": 22000.0,
                    "parallel_workers_count": 1,
                    "sections": {
                        "company_snapshot": {
                            "total_ms": 4000.0,
                            "subsections": {
                                "retrieval_ms": 1000.0,
                                "groq_extract_ms": 1400.0,
                                "groq_gap_check_ms": 600.0,
                                "groq_draft_narrative_ms": 1000.0,
                                "queries_count": 3,
                                "claims_extracted": 5,
                                "evidence_cited_count": 8,
                                "char_length": 1400,
                            }
                        }
                    }
                },
                "stage_3_synthesis_and_verdict": {
                    "wall_clock_ms": 3000.0,
                    "subsections": {"groq_synthesis_ms": 3000.0, "risk_tier": "Contained"}
                },
                "stage_4_validation_agent": {
                    "wall_clock_ms": 2500.0,
                    "subsections": {"deterministic_validator_ms": 10.0, "validation_agent_pass_ms": 2490.0}
                },
                "stage_5_artifact_rendering": {
                    "wall_clock_ms": 800.0,
                    "subsections": {"footnote_transformation_ms": 40.0, "render_markdown_ms": 10.0, "render_docx_ms": 350.0, "render_pdf_ms": 400.0}
                }
            }
        }
        tree_text = render_tree(sample_telemetry, "AAPL")
        self.assertIn("GRANULAR TIMINGS TREE", tree_text)
        self.assertIn("├── Stage 1: SEC EDGAR & Entity Resolution", tree_text)
        self.assertIn("├── Stage 2: Research & Drafting", tree_text)
        self.assertIn("└── Stage 5: Publication Artifact Rendering", tree_text)
        self.assertIn("Concurrency: 3.00x", tree_text)

    def test_render_table_output(self):
        sample_telemetry = {
            "total_wall_clock_ms": 30000.0,
            "total_compute_ms": 90000.0,
            "concurrency_speedup": "3.00x",
            "stages": {
                "stage_1_edgar_resolution": {"wall_clock_ms": 1200.0, "subsections": {}},
                "stage_2_research_and_draft": {"wall_clock_ms": 22000.0, "sections": {}},
                "stage_3_synthesis_and_verdict": {"wall_clock_ms": 3000.0},
                "stage_4_validation_agent": {"wall_clock_ms": 2500.0},
                "stage_5_artifact_rendering": {"wall_clock_ms": 800.0},
            }
        }
        table_text = render_table(sample_telemetry, "AAPL")
        self.assertIn("GRANULAR TIMINGS TABLE", table_text)
        self.assertIn("Stage 1: SEC EDGAR & Entity Resolution", table_text)
        self.assertIn("Stage 2: Research & Drafting (Parallel)", table_text)


class TestDepthParityAndDynamicAdherence(unittest.TestCase):
    def test_dynamic_prompt_parsing(self):
        """Verifies dynamic segmentation of web-search-prompt.txt into sections without hardcoding."""
        from app.workflows.do_risk_report.template_spec import parse_prompt_sections, load_prompt_text
        prompt_text = load_prompt_text("web_search_prompt.txt")
        self.assertTrue(len(prompt_text) > 0, "Prompt text could not be loaded")

        master_rules, sections = parse_prompt_sections(prompt_text)
        self.assertTrue(len(master_rules) > 100, "Master underwriting guidelines should be extracted")
        self.assertGreaterEqual(len(sections), 10, "Should parse at least 10 dynamic sections")

        # Confirm verbatim section prompt contains prompt instructions
        snapshot_sec = next((s for s in sections if s.name == "company_snapshot"), None)
        self.assertIsNotNone(snapshot_sec, "company_snapshot section must be detected")
        self.assertIn("market capitalization", snapshot_sec.section_prompt.lower())
        self.assertIn("company", snapshot_sec.static_queries[0])

    def test_no_prompt_leak_in_validation(self):
        """Verifies that validation wrapper instructions do not leak into the report."""
        from app.workflows.do_risk_report.validator import ValidationAgent
        agent = ValidationAgent()
        sample_report = "### COMPANY SNAPSHOT\n- Legal Name: Apple Inc.\n- Share price as of current month: $180 [E001]"
        loop = asyncio.new_event_loop()
        try:
            validated = loop.run_until_complete(
                agent.run(sample_report)
            )
            self.assertNotIn("REPORT TO VALIDATE AND CORRECT:", validated)
            self.assertNotIn("VALIDATED AND CORRECTED REPORT:", validated)
            self.assertIn("Apple Inc.", validated)
        finally:
            loop.close()

    def test_pdf_multipage_and_headers(self):
        """Verifies ReportLab NumberedCanvas generates running headers, footers, and multi-page layout."""
        import pypdf
        from app.workflows.do_risk_report.renderer import PdfRenderer
        from app.workflows.do_risk_report.models import EntityCard
        from app.workflows.do_risk_report.ledger import EvidenceLedger

        entity = EntityCard(ticker="AAPL", legal_name="Apple Inc.", cik="0000320193", exchange="NASDAQ")
        ledger = EvidenceLedger()

        # Build substantial multi-section content to span multiple pages
        long_body = "\n\n".join([
            f"## SECTION {i}: OPERATIONAL EVALUATION\n" + "\n".join([f"- Underwriting item {j} verified with primary SEC filing [1]." for j in range(1, 15)])
            for i in range(1, 8)
        ])
        long_body += "\n\n### D&O Risk Band Register\n| Dimension | Band | Driver |\n| :--- | :--- | :--- |\n| Financial | Contained | Liquidity |\n| Legal | Elevated | DOJ Inquiry |\n"

        footnotes = [{"num": 1, "id": "E001", "claim": "Fact verified", "source_url": "sec.gov", "source_type": "filing", "published": "2024-01-01", "confidence": "high", "quote": "Fact"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test_parity.pdf")
            PdfRenderer.render(pdf_path, entity, "Contained", long_body, footnotes, ledger, report_date="November 03, 2026")

            self.assertTrue(os.path.isfile(pdf_path))
            reader = pypdf.PdfReader(pdf_path)
            self.assertGreaterEqual(len(reader.pages), 2, "Report should be multi-page")

            # Page 2 should include running header
            page2_text = reader.pages[1].extract_text()
            self.assertIn("Apple Inc. — D&O Underwriting Analysis", page2_text)
            self.assertIn("Page 2 of", page2_text)
            self.assertIn("CONFIDENTIAL & PROPRIETARY", page2_text)

    def test_e2e_depth_parity_metrics(self):
        """Verifies end-to-end report generation generates benchmark-grade depth (>15,000 chars, multi-page PDF)."""
        import pypdf
        from app.workflows.do_risk_report.orchestrator import DORiskReportOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            orch = DORiskReportOrchestrator(artifacts_dir=tmpdir)
            loop = asyncio.new_event_loop()
            try:
                res = loop.run_until_complete(
                    orch.run(ticker="AAPL", mode="fast", current_date="2026-11-03")
                )
                self.assertIsNotNone(res)
                self.assertGreater(len(res.validated_report_text), 15000, "Validated report text should exceed 15,000 characters")

                # Verify PDF size and page count
                pdf_artifact = next((a for a in res.artifacts if a["type"] == "pdf"), None)
                self.assertIsNotNone(pdf_artifact)
                self.assertGreater(pdf_artifact["size"], 20000, "PDF should exceed 20 KB")

                reader = pypdf.PdfReader(pdf_artifact["path"])
                self.assertGreaterEqual(len(reader.pages), 4, "PDF should be at least 4 pages")
            finally:
                loop.close()


class TestPerplexitySearchAPI(unittest.TestCase):
    def test_search_via_perplexity_search_api_empty_key(self):
        from app.agents.researcher.tools import search_via_perplexity_search_api
        res = search_via_perplexity_search_api("NVIDIA board", api_key="")
        self.assertIsNone(res)

    def test_search_via_perplexity_search_api_mock(self):
        from unittest.mock import patch, MagicMock
        from app.agents.researcher.tools import search_via_perplexity_search_api

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "test-uuid-1234",
            "results": [
                {
                    "title": "NVIDIA Governance",
                    "url": "https://investor.nvidia.com/governance",
                    "snippet": "Jensen Huang serves as CEO and Director.",
                    "date": "2026-10-30"
                }
            ]
        }

        with patch("httpx.post", return_value=mock_resp):
            res = search_via_perplexity_search_api("NVIDIA board", api_key="test-key-123")
            self.assertIsNotNone(res)
            self.assertEqual(res["provider"], "perplexity_search_api")
            self.assertEqual(res["results_count"], 1)
            self.assertEqual(res["results"][0]["title"], "NVIDIA Governance")
            self.assertEqual(res["results"][0]["domain"], "investor.nvidia.com")
            self.assertIn("https://investor.nvidia.com/governance", res["sources"])

    def test_async_search_via_perplexity_search_api_mock(self):
        import asyncio
        from unittest.mock import patch, MagicMock
        from app.agents.researcher.tools import async_search_via_perplexity_search_api

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "test-uuid-5678",
            "results": [
                {
                    "title": "NVIDIA SEC Inquiry",
                    "url": "https://sec.gov/filings/nvda-note",
                    "snippet": "Disclosed antitrust inquiry regarding AI software acquisition.",
                    "last_updated": "2026-11-01"
                }
            ]
        }

        async def run_test():
            with patch("httpx.AsyncClient.post", return_value=mock_resp):
                res = await async_search_via_perplexity_search_api("NVIDIA DOJ probe", api_key="test-key-456")
                self.assertIsNotNone(res)
                self.assertEqual(res["provider"], "perplexity_search_api")
                self.assertEqual(res["results_count"], 1)
                self.assertEqual(res["results"][0]["domain"], "sec.gov")
                self.assertEqual(res["results"][0]["date"], "2026-11-01")

        asyncio.run(run_test())

    def test_search_via_perplexity_search_api_batch_query_list(self):
        from unittest.mock import patch, MagicMock
        from app.agents.researcher.tools import search_via_perplexity_search_api

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "batch-uuid-9999",
            "results": [
                {"title": "Jensen Huang Bio", "url": "https://nvidia.com/bio", "snippet": "CEO since 1993", "date": "2026-10-30"},
                {"title": "NVIDIA Market Cap", "url": "https://reuters.com/nvda", "snippet": "Market cap $3.3T", "date": "2026-10-30"}
            ]
        }

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            queries = ["NVIDIA CEO Jensen Huang", "NVIDIA market cap 2026"]
            res = search_via_perplexity_search_api(queries, api_key="test-key-789")
            self.assertIsNotNone(res)
            self.assertEqual(res["results_count"], 2)
            # Verify payload sent to Perplexity Search API contained the list of query strings
            call_kwargs = mock_post.call_args[1]
            payload = call_kwargs["json"]
            self.assertEqual(payload["query"], queries)
            self.assertEqual(payload["search_context_size"], "high")

    def test_async_search_via_perplexity_search_api_batch_query_list(self):
        import asyncio
        from unittest.mock import patch, MagicMock
        from app.agents.researcher.tools import async_search_via_perplexity_search_api

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "async-batch-uuid-8888",
            "results": [
                {"title": "DOJ Inquiry", "url": "https://bloomberg.com/doj", "snippet": "Antitrust probe", "date": "2026-10-31"}
            ]
        }

        async def run_test():
            with patch("httpx.AsyncClient.post", return_value=mock_resp) as mock_post:
                queries = ["NVIDIA antitrust DOJ", "NVIDIA Run:ai acquisition"]
                res = await async_search_via_perplexity_search_api(queries, api_key="test-key-321")
                self.assertIsNotNone(res)
                self.assertEqual(res["results_count"], 1)
                call_kwargs = mock_post.call_args[1]
                payload = call_kwargs["json"]
                self.assertEqual(payload["query"], queries)

        asyncio.run(run_test())

    def test_provider_switching_and_resolution(self):
        from app.workflows.do_risk_report.roles import (
            set_active_provider,
            get_active_provider,
            PROVIDER_MODELS,
            ROLE_TIER_MAPPING,
        )

        orig = get_active_provider()
        try:
            # gpt-oss
            set_active_provider("gpt-oss")
            self.assertEqual(get_active_provider(), "gpt-oss")
            self.assertEqual(PROVIDER_MODELS["gpt-oss"]["fast"], "openai/gpt-oss-20b")
            self.assertEqual(PROVIDER_MODELS["gpt-oss"]["reasoning"], "openai/gpt-oss-120b")

            # qwen
            set_active_provider("qwen")
            self.assertEqual(get_active_provider(), "qwen")
            self.assertEqual(PROVIDER_MODELS["qwen"]["fast"], "qwen/qwen3.8-27b")

            # gemini
            set_active_provider("gemini")
            self.assertEqual(get_active_provider(), "gemini")

            # iteracompute
            set_active_provider("iteracompute")
            self.assertEqual(get_active_provider(), "iteracompute")
            self.assertIn("fast", PROVIDER_MODELS["iteracompute"])

            # itera alias
            set_active_provider("itera")
            self.assertEqual(get_active_provider(), "iteracompute")

            # azure
            set_active_provider("azure")
            self.assertEqual(get_active_provider(), "azure")
            self.assertEqual(PROVIDER_MODELS["azure"]["reasoning"], "claude-opus-4-8")

            # azure-foundry alias
            set_active_provider("azure-foundry")
            self.assertEqual(get_active_provider(), "azure")

            # invalid provider raises ValueError
            with self.assertRaises(ValueError):
                set_active_provider("unsupported-llm")
        finally:
            set_active_provider(orig)

    def test_cli_provider_flag_parsing(self):
        from app.workflows.do_risk_report.cli import build_parser

        parser = build_parser()

        args1 = parser.parse_args(["NVDA", "--provider", "gemini"])
        self.assertEqual(args1.provider, "gemini")

        args2 = parser.parse_args(["NVDA", "--provider", "qwen"])
        self.assertEqual(args2.provider, "qwen")

        args3 = parser.parse_args(["NVDA", "--provider", "iteracompute"])
        self.assertEqual(args3.provider, "iteracompute")

        args4 = parser.parse_args(["NVDA", "--provider", "azure"])
        self.assertEqual(args4.provider, "azure")

        args5 = parser.parse_args(["NVDA", "--llm-provider", "gpt-oss"])
        self.assertEqual(args5.provider, "gpt-oss")

        args6 = parser.parse_args(["NVDA", "--fallback-model", "claude-sonnet-4-6"])
        self.assertEqual(args6.fallback_model, "claude-sonnet-4-6")

    def test_fallback_model_get_set(self):
        from app.workflows.do_risk_report.roles import set_fallback_model, get_fallback_model

        orig = get_fallback_model()
        try:
            set_fallback_model("claude-sonnet-4-6")
            self.assertEqual(get_fallback_model(), "claude-sonnet-4-6")

            set_fallback_model(None)
            self.assertIsNone(get_fallback_model())
        finally:
            set_fallback_model(orig)

    def test_azure_rate_limit_failover_to_fallback(self):
        import asyncio
        from unittest.mock import patch
        from app.workflows.do_risk_report.roles import run_role

        models_called = []

        async def mock_execute(model, system_prompt, user_prompt, temp, max_tokens):
            models_called.append(model)
            if model == "claude-opus-4-8":
                raise RuntimeError("Azure Foundry error 429: Rate limit TPM exceeded")
            return '{"risk_tier": "Contained", "executive_summary": "Fallback success"}'

        async def run_test():
            with patch("app.workflows.do_risk_report.roles._execute_azure_chat", side_effect=mock_execute):
                with patch.dict("os.environ", {"AZURE_API_KEY": "live-test-key", "TESTING": "false"}):
                    res = await run_role(
                        "synthesize",
                        "summary info",
                        model_override="claude-opus-4-8",
                        provider_override="azure",
                        fallback_model_override="claude-sonnet-4-6",
                    )
                    self.assertIsNotNone(res)
                    self.assertEqual(res.get("risk_tier"), "Contained")
                    self.assertIn("claude-opus-4-8", models_called)
                    self.assertIn("claude-sonnet-4-6", models_called)

        asyncio.run(run_test())

    def test_run_role_timings_provider_meta(self):
        import asyncio
        from app.workflows.do_risk_report.roles import run_role_with_timings

        async def run_test():
            res, meta = await run_role_with_timings("extract", "Company info", provider_override="iteracompute")
            self.assertIsNotNone(res)
            self.assertEqual(meta["provider"], "iteracompute")
            self.assertEqual(meta["role"], "extract")

        asyncio.run(run_test())

    def test_validation_agent_provider_attribute(self):
        from app.workflows.do_risk_report.validator import ValidationAgent

        val = ValidationAgent(current_date="2026-11-03", provider="iteracompute")
        self.assertEqual(val.provider, "iteracompute")
        self.assertEqual(val.current_date, "2026-11-03")


if __name__ == "__main__":
    unittest.main()

