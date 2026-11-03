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


if __name__ == "__main__":
    unittest.main()


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
