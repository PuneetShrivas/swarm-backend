"""Comprehensive Standalone Unit Test Suite for Agnostic Workflow Package.

Can be run independently in any environment:
    python test_standalone_workflow.py
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Add package parent and package directory to sys.path
package_dir = Path(__file__).resolve().parent
if str(package_dir.parent) not in sys.path:
    sys.path.insert(0, str(package_dir.parent))
if str(package_dir) not in sys.path:
    sys.path.insert(0, str(package_dir))

from agnostic_workflow.models import SectionSpec, ReportPromptSpec, AgnosticEvidence, AgnosticReportResult
from agnostic_workflow.spec_parser import MarkdownSpecParser
from agnostic_workflow.ledger import AgnosticEvidenceLedger
from agnostic_workflow.retrieval import ResultCompactor, PerplexitySearchQueue
from agnostic_workflow.roles import (
    _extract_json,
    ROLES_CONFIG,
    set_active_provider,
    get_active_provider,
    parse_retry_delay,
    run_role,
    resolve_foundry_endpoint,
    is_openai_foundry_model,
)
from agnostic_workflow.renderer import (
    format_inline_markdown,
    FootnoteTransformer,
    AgnosticMarkdownRenderer,
    AgnosticPdfRenderer,
)
from agnostic_workflow.telemetry import render_tree, render_table


class TestStandaloneAgnosticWorkflow(unittest.TestCase):
    """Verifies complete standalone functionality of the agnostic workflow."""

    def test_01_zero_app_imports(self):
        """CRITICAL: Verifies zero imports from backend app.* anywhere in agnostic_workflow/ production modules."""
        py_files = [p for p in package_dir.glob("*.py") if not p.name.startswith("test_")]
        self.assertGreater(len(py_files), 5, "Expected multiple python modules in package")

        violations = []
        for pf in py_files:
            content = pf.read_text(encoding="utf-8")
            for line_no, line in enumerate(content.splitlines(), start=1):
                clean_line = line.strip()
                if clean_line.startswith("#"):
                    continue
                if "from app." in clean_line or "import app." in clean_line:
                    violations.append(f"{pf.name}:{line_no}: {clean_line}")

        self.assertEqual(violations, [], f"Found forbidden app.* imports in standalone package: {violations}")

    def test_02_spec_parser_standard_markdown(self):
        """Verifies parsing of standard ## Markdown templates."""
        template_path = package_dir / "templates" / "standard_research_report.md"
        self.assertTrue(template_path.is_file(), "Default template must exist")

        spec = MarkdownSpecParser.parse_file(str(template_path))
        self.assertEqual(spec.title_format, "# {SUBJECT}")
        self.assertEqual(len(spec.sections), 8)
        self.assertEqual(spec.closing_statement, "Assessment based solely on information contained in this report.")

        # Check section types
        sec_names = [s.name for s in spec.sections]
        self.assertIn("executive_summary", sec_names)
        self.assertIn("overall_synthesis_verdict", sec_names)
        self.assertTrue(spec.get_section("executive_summary").is_synthesis)
        self.assertTrue(spec.get_section("overall_synthesis_verdict").is_synthesis)
        self.assertFalse(spec.get_section("background_context").is_synthesis)

    def test_03_spec_parser_unstructured_prompt(self):
        """Verifies parsing of prompt files without ## markdown headings (e.g. web-search-prompt.md)."""
        prompt_path = package_dir.parent / "agent-instructions" / "web-search-prompt.md"
        if prompt_path.is_file():
            spec = MarkdownSpecParser.parse_file(str(prompt_path))
            self.assertEqual(spec.title_format, "# {SUBJECT}")
            self.assertGreaterEqual(len(spec.sections), 10)
            self.assertEqual(spec.closing_statement, "Assessment based solely on information contained in this report.")

            sec_names = [s.name for s in spec.sections]
            self.assertIn("company_snapshot", sec_names)
            self.assertIn("financial_overview", sec_names)
            self.assertIn("overall_do_underwriter_verdict", sec_names)
            self.assertTrue(spec.get_section("overall_do_underwriter_verdict").is_synthesis)

    def test_04_evidence_ledger_sequential_citations(self):
        """Verifies thread-safe sequential citation ID tracking [E001], [E002] and stats."""
        ledger = AgnosticEvidenceLedger()
        items = [
            AgnosticEvidence(
                id="",
                section_slug="financial_overview",
                claim="Annual revenue reached $60.9B in fiscal 2024.",
                value="$60.9B",
                as_of="2024-01-31",
                source_url="https://sec.gov/edgar/10k",
                source_domain="sec.gov",
                source_title="SEC 10-K Filing",
                published="2024-02-15",
                confidence="high",
                quote="revenue totaled $60.9B",
            ),
            AgnosticEvidence(
                id="",
                section_slug="financial_overview",
                claim="Gross margin expanded by 450 bps YoY.",
                value="74.5%",
                source_url="https://bloomberg.com/news/tech-margins",
                source_domain="bloomberg.com",
                confidence="high",
            ),
            AgnosticEvidence(
                id="",
                section_slug="governance",
                claim="Board approved new lead independent director charter.",
                source_url="https://reuters.com/business/governance",
                source_domain="reuters.com",
                confidence="med",
            )
        ]
        added = ledger.add(items)
        self.assertEqual(added[0].id, "E001")
        self.assertEqual(added[1].id, "E002")
        self.assertEqual(added[2].id, "E003")

        # Resolve
        ev1 = ledger.resolve_citation("E001")
        self.assertIsNotNone(ev1)
        self.assertEqual(ev1.value, "$60.9B")

        # Section filtering
        fin_items = ledger.for_section("financial_overview")
        self.assertEqual(len(fin_items), 2)

        # Stats
        stats = ledger.stats()
        self.assertEqual(stats["total_evidence_count"], 3)
        self.assertEqual(stats["sections_covered"], 2)
        self.assertEqual(stats["high_confidence_count"], 2)

    def test_05_retrieval_compactor_and_dedup(self):
        """Verifies snippet cleaning, length capping, and wire news deduplication."""
        # Snippet cleaning
        dirty = "Check out ![logo](https://img.com/a.png) this **great** research [link](https://test.com)   with   lots of    spaces."
        cleaned = ResultCompactor.clean_snippet(dirty, max_chars=100)
        self.assertNotIn("![logo]", cleaned)
        self.assertNotIn("https://img.com", cleaned)
        self.assertIn("research link", cleaned)

        # Deduplication
        raw_results = [
            {
                "title": "PR Newswire: NVIDIA announces next-gen architecture",
                "url": "https://prnewswire.com/news/nvidia",
                "snippet": "SANTA CLARA, Calif. -- NVIDIA today announced next-gen compute platform.",
            },
            {
                "title": "Business Wire: NVIDIA announces next-gen architecture",
                "url": "https://businesswire.com/news/nvidia",
                "snippet": "SANTA CLARA, Calif. -- NVIDIA today announced next-gen compute platform.",
            },
            {
                "title": "Reuters: Tech market rallies on chip earnings",
                "url": "https://reuters.com/markets/chips",
                "snippet": "Semiconductor stocks rallied strongly on Friday led by major earnings beats.",
            }
        ]
        deduped = ResultCompactor.deduplicate_results(raw_results)
        self.assertEqual(len(deduped), 2)
        domains = [d["url"] for d in deduped]
        self.assertIn("https://prnewswire.com/news/nvidia", domains)
        self.assertIn("https://reuters.com/markets/chips", domains)

    def test_05b_perplexity_fast_search_payload(self):
        """Verifies that Perplexity Search API requests in standalone retrieval transmit search_type: 'fast'."""
        import asyncio
        from unittest.mock import patch, MagicMock
        from agnostic_workflow.retrieval import async_search_via_perplexity_search_api

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"title": "Fast Search Test", "url": "https://example.com/fast", "snippet": "Fast mode verified", "date": "2026-11-05"}
            ]
        }

        async def run_check():
            with patch("httpx.AsyncClient.post", return_value=mock_resp) as mock_post:
                res = await async_search_via_perplexity_search_api("Quantum photonics", api_key="test-key-fast")
                self.assertIsNotNone(res)
                call_kwargs = mock_post.call_args[1]
                payload = call_kwargs["json"]
                self.assertEqual(payload.get("search_type"), "fast")
                self.assertEqual(payload.get("search_context_size"), "high")

        asyncio.run(run_check())

    def test_06_roles_json_extraction(self):
        """Verifies JSON parsing across fences, thinking blocks, and loose formats."""
        # Thinking blocks
        text1 = "<thinking>Analyzing user input and formatting JSON</thinking>\n{\"queries\": [{\"text\": \"NVIDIA revenue\"}]}"
        res1 = _extract_json(text1)
        self.assertEqual(len(res1.get("queries", [])), 1)

        # Fenced ```json
        text2 = "Here is the plan:\n```json\n{\n  \"queries\": [{\"text\": \"AMD GPU benchmarks\"}]\n}\n```"
        res2 = _extract_json(text2)
        self.assertEqual(res2["queries"][0]["text"], "AMD GPU benchmarks")

        # Provider setting
        set_active_provider("groq")
        self.assertEqual(get_active_provider(), "groq")
        set_active_provider("azure")
        self.assertEqual(get_active_provider(), "azure")

    def test_07_footnote_transformation_and_rendering(self):
        """Verifies [E###] to [1] superscript footnote transformation and PDF rendering."""
        ledger = AgnosticEvidenceLedger()
        ledger.add([
            AgnosticEvidence(
                id="E001",
                section_slug="tech",
                claim="Quantum volume surpassed 2^20 in lab trials.",
                source_url="https://nature.com/articles/qv20",
                source_domain="nature.com",
                published="2026-03-01",
                confidence="high",
                quote="surpassed 2^20 milestone",
            ),
            AgnosticEvidence(
                id="E002",
                section_slug="tech",
                claim="Operating temperature reached 4 Kelvin.",
                source_url="https://science.org/temp4k",
                source_domain="science.org",
                published="2026-03-10",
                confidence="high",
            )
        ])

        raw_text = "Trial results demonstrated that quantum volume surpassed 2^20 [E001] at 4 Kelvin [E002]."
        transformed, footnotes = FootnoteTransformer.transform_citations(raw_text, ledger)

        self.assertIn("[1]", transformed)
        self.assertIn("[2]", transformed)
        self.assertNotIn("[E001]", transformed)
        self.assertNotIn("[E002]", transformed)
        self.assertEqual(len(footnotes), 2)
        self.assertEqual(footnotes[0]["source_domain"], "nature.com")

        # Markdown render
        md = AgnosticMarkdownRenderer.render(
            subject="Quantum Computing",
            sections_text=[transformed],
            footnotes=footnotes,
            closing_statement="Assessment based solely on report.",
            metadata={"date": "2026-11-05", "model": "claude-sonnet-4-6", "provider": "azure"},
        )
        self.assertIn("# QUANTUM COMPUTING", md)
        self.assertIn("## SOURCES & FOOTNOTES", md)
        self.assertIn("[nature.com]", md)

        # PDF render
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test_output.pdf")
            AgnosticPdfRenderer.render(
                subject="Quantum Computing",
                sections_text=[transformed],
                footnotes=footnotes,
                output_path=pdf_path,
                closing_statement="Assessment based solely on report.",
                metadata={"date": "2026-11-05", "model": "claude-sonnet-4-6", "provider": "azure", "evidence_count": 2, "total_tokens": 1000, "duration_seconds": 2.5},
            )
            self.assertTrue(os.path.isfile(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 1000)

    def test_08_telemetry_renderers(self):
        """Verifies ASCII hierarchical tree and table rendering."""
        mock_telemetry = {
            "total_wall_clock_ms": 3200.0,
            "total_compute_ms": 7800.0,
            "concurrency_speedup": "2.44x",
            "tokens": {"input_tokens": 4000, "output_tokens": 1200, "total_tokens": 5200},
            "stages": {
                "stage_1_spec_parse": {"sections_count": 8},
                "stage_2_research_and_draft": {
                    "wall_clock_ms": 2800.0,
                    "sections": {
                        "executive_summary": {
                            "total_ms": 1400.0,
                            "tokens": {"input_tokens": 2000, "output_tokens": 600, "total_tokens": 2600},
                            "subsections": {
                                "planning_ms": 250.0,
                                "retrieval_ms": 400.0,
                                "extract_ms": 350.0,
                                "gap_ms": 0.0,
                                "draft_narrative_ms": 400.0,
                                "queries_count": 2,
                                "claims_extracted": 3,
                                "evidence_cited_count": 3,
                                "rounds": [],
                            }
                        }
                    }
                },
                "stage_3_synthesis": {"wall_clock_ms": 300.0, "sections": {}},
                "stage_5_rendering": {"wall_clock_ms": 100.0, "footnotes_count": 3},
            }
        }
        tree = render_tree(mock_telemetry, "Solid State Batteries")
        self.assertIn("AGNOSTIC RESEARCH PIPELINE: GRANULAR TIMINGS TREE", tree)
        self.assertIn("SOLID STATE BATTERIES", tree)
        self.assertIn("Concurrency: 2.44x", tree)

        table = render_table(mock_telemetry, "Solid State Batteries")
        self.assertIn("AGNOSTIC RESEARCH PIPELINE: TIMINGS & TOKENS TABLE", table)
        self.assertIn("TOTAL WALL-CLOCK DURATION", table)
        self.assertIn("5,200", table)

    def test_09_end_to_end_orchestrator_execution(self):
        """Verifies end-to-end AgnosticResearchOrchestrator execution producing md, pdf, and telemetry."""
        import asyncio
        from agnostic_workflow.orchestrator import AgnosticResearchOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"TESTING": "true", "ALLOW_MOCK_DATA": "true", "MOCK_PERPLEXITY": "true"}):
                orchestrator = AgnosticResearchOrchestrator(artifacts_dir=tmpdir)
                test_prompt = """# {SUBJECT}

## 1. TECHNICAL ANALYSIS
- Key architecture and metrics

## 2. SYNTHESIS VERDICT
- Final bottom-line assessment

### Closing Statement
"Assessment based solely on information contained in this report."
"""
                progress_events = []
                def on_progress(stage, msg):
                    progress_events.append((stage, msg))

                result = asyncio.run(orchestrator.run(
                    subject="Silicon Anode Batteries",
                    prompt_markdown=test_prompt,
                    mode="fast",
                    output_dir=tmpdir,
                    on_progress=on_progress,
                ))

                self.assertIsInstance(result, AgnosticReportResult)
                self.assertTrue(os.path.isfile(result.markdown_path))
                self.assertTrue(os.path.isfile(result.pdf_path))
                self.assertTrue(os.path.isfile(result.telemetry_path))
                self.assertGreater(result.evidence_count, 0)
                self.assertGreater(result.total_tokens, 0)

                # Verify granular stage 2 & stage 3 progress milestones
                event_stages = [ev[0] for ev in progress_events]
                self.assertIn("stage_1", event_stages)
                self.assertIn("stage_2", event_stages)
                self.assertIn("plan", event_stages)
                self.assertIn("plan_done", event_stages)
                self.assertIn("search", event_stages)
                self.assertIn("search_done", event_stages)
                self.assertIn("extract", event_stages)
                self.assertIn("extract_done", event_stages)
                self.assertIn("draft", event_stages)
                self.assertIn("draft_done", event_stages)
                self.assertIn("section_done", event_stages)
                self.assertIn("stage_2_done", event_stages)
                self.assertIn("stage_3", event_stages)
                self.assertIn("synth", event_stages)
                self.assertIn("synth_done", event_stages)
                self.assertIn("stage_5", event_stages)
                self.assertIn("stage_5_footnotes", event_stages)

                # Verify visual ASCII progress bar presence
                section_done_msgs = [ev[1] for ev in progress_events if ev[0] == "section_done"]
                self.assertTrue(any("█" in msg for msg in section_done_msgs))
                self.assertTrue(any("%" in msg for msg in section_done_msgs))


    def test_10_rate_limit_delay_parsing(self):
        """Verifies parsing of recommended retry wait seconds from 429 errors."""
        msg_1s = "Rate limit of 8000 per 60s exceeded for UserByModelByMinuteOutputTokens. Please wait 1 seconds before retrying."
        self.assertEqual(parse_retry_delay(msg_1s), 3.0)  # 1.0 + 2.0 buffer

        msg_8s = "Please wait 8 seconds before retrying."
        self.assertEqual(parse_retry_delay(msg_8s), 10.0)  # 8.0 + 2.0 buffer

        msg_alt = "retry after 12.5 seconds"
        self.assertEqual(parse_retry_delay(msg_alt), 14.5)  # 12.5 + 2.0 buffer

        # Fallback when no seconds regex match
        msg_none = "Generic rate limit reached"
        self.assertEqual(parse_retry_delay(msg_none, default_wait=5.0, attempt=2), 15.0)

    def test_11_run_role_429_retry_recovery(self):
        """Simulates an Azure 429 rate limit error followed by success."""
        call_count = 0
        async def fake_azure_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError('Azure Foundry HTTP 429: {"error":{"code":"RateLimitReached","message":"Please wait 0.01 seconds before retrying."}}')
            return '{"section_text": "## SECTION\\n- Valid drafted bullet [E001]."}', {"input_tokens": 50, "output_tokens": 20, "total_tokens": 70}

        orig_env = os.environ.copy()
        os.environ.pop("ALLOW_MOCK_DATA", None)
        os.environ.pop("MOCK_ROLES", None)
        os.environ["AZURE_MAX_RETRY_ROUNDS"] = "2"
        try:
            with patch("agnostic_workflow.roles._execute_azure_chat_with_tokens", side_effect=fake_azure_call):
                import asyncio
                res, usage, dur, model = asyncio.run(run_role(
                    "draft",
                    "Draft test section",
                    provider_override="azure",
                    model_override="claude-opus-4-8",
                ))
                self.assertEqual(call_count, 2)
                self.assertIn("Valid drafted bullet", res.get("section_text", ""))
        finally:
            os.environ.clear()
            os.environ.update(orig_env)

    def test_12_orchestrator_section_draft_retry_recovers(self):
        """Verifies that orchestrator _process_section retries on transient draft failure and succeeds."""
        from agnostic_workflow.orchestrator import AgnosticResearchOrchestrator
        from agnostic_workflow.ledger import AgnosticEvidenceLedger
        from agnostic_workflow.models import SectionSpec

        orch = AgnosticResearchOrchestrator()
        sec = SectionSpec(name="test_sec", title="Test Section", required_fields=["Field 1"])
        ledger = AgnosticEvidenceLedger()

        draft_call_count = 0
        async def mock_run_role(role, user_input, **kwargs):
            nonlocal draft_call_count
            if role == "plan":
                return {"queries": []}, {"input_tokens": 10, "output_tokens": 10, "total_tokens": 20}, 5.0, "mock-model"
            elif role == "draft":
                draft_call_count += 1
                if draft_call_count == 1:
                    raise RuntimeError("Azure Foundry HTTP 429: Rate limit exceeded")
                return {"section_text": "## Test Section\n- Successful recovered draft."}, {"input_tokens": 15, "output_tokens": 15, "total_tokens": 30}, 5.0, "mock-model"
            return {}, {}, 5.0, "mock-model"

        orig_env = os.environ.copy()
        os.environ["TESTING"] = "false"
        os.environ["DRAFT_MAX_RETRIES"] = "3"
        try:
            with patch("agnostic_workflow.orchestrator.run_role", side_effect=mock_run_role):
                with patch("asyncio.sleep", return_value=None):
                    import asyncio
                    text, timing = asyncio.run(orch._process_section(
                        subject="NVIDIA",
                        section=sec,
                        ledger=ledger,
                        global_rules="Rules",
                        mode="fast",
                        model="claude-opus-4-8",
                        provider="azure",
                    ))
                    self.assertEqual(draft_call_count, 2)
                    self.assertIn("Successful recovered draft", text)
                    self.assertNotIn("unavailable due to upstream error", text)
        finally:
            os.environ.clear()
            os.environ.update(orig_env)


    def test_13_resolve_foundry_endpoint_routing(self):
        """Verifies endpoint changes to /openai/v1/messages for gpt-5.4 and gpt-5-mini and /anthropic/ for Claude."""
        default_anthropic = "https://puneetshrivas32-0871-resource.services.ai.azure.com/anthropic/v1/messages"
        default_openai = "https://puneetshrivas32-0871-resource.services.ai.azure.com/openai/v1/responses"

        # Model detection
        self.assertTrue(is_openai_foundry_model("gpt-5.4"))
        self.assertTrue(is_openai_foundry_model("gpt-5-mini"))
        self.assertFalse(is_openai_foundry_model("claude-opus-4-8"))
        self.assertFalse(is_openai_foundry_model("claude-sonnet-4-6"))

        # Default resolution
        self.assertEqual(resolve_foundry_endpoint("gpt-5.4"), default_openai)
        self.assertEqual(resolve_foundry_endpoint("gpt-5-mini"), default_openai)
        self.assertEqual(resolve_foundry_endpoint("claude-opus-4-8"), default_anthropic)
        self.assertEqual(resolve_foundry_endpoint("claude-sonnet-4-6"), default_anthropic)

        # When AZURE_FOUNDRY_ENDPOINT is set to anthropic in env
        orig_env = os.environ.get("AZURE_FOUNDRY_ENDPOINT")
        try:
            os.environ["AZURE_FOUNDRY_ENDPOINT"] = default_anthropic
            self.assertEqual(resolve_foundry_endpoint("gpt-5.4"), default_openai)
            self.assertEqual(resolve_foundry_endpoint("gpt-5-mini"), default_openai)
            self.assertEqual(resolve_foundry_endpoint("claude-opus-4-8"), default_anthropic)
        finally:
            if orig_env is not None:
                os.environ["AZURE_FOUNDRY_ENDPOINT"] = orig_env
            else:
                os.environ.pop("AZURE_FOUNDRY_ENDPOINT", None)

        # When bare host is passed
        base_host = "https://puneetshrivas32-0871-resource.services.ai.azure.com"
        self.assertEqual(resolve_foundry_endpoint("gpt-5.4", base_host), default_openai)
        self.assertEqual(resolve_foundry_endpoint("claude-opus-4-8", base_host), default_anthropic)


if __name__ == "__main__":
    unittest.main()
