"""
Unit test suite for Agnostic Research & Report Generation Flow.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.workflows.agnostic_research_report.models import (
    SectionSpec,
    ReportPromptSpec,
    AgnosticEvidence,
    AgnosticReportResult,
)
from app.workflows.agnostic_research_report.spec_parser import MarkdownSpecParser
from app.workflows.agnostic_research_report.ledger import AgnosticEvidenceLedger
from app.workflows.agnostic_research_report.retrieval import PerplexitySearchQueue, ResultCompactor
from app.workflows.agnostic_research_report.roles import (
    run_role,
    set_active_provider,
    get_active_provider,
    set_fallback_model,
    get_fallback_model,
    _extract_json,
    _execute_azure_chat_with_tokens,
    parse_retry_delay,
    resolve_foundry_endpoint,
    is_openai_foundry_model,
)
from app.workflows.agnostic_research_report.renderer import (
    FootnoteTransformer,
    AgnosticMarkdownRenderer,
    AgnosticPdfRenderer,
)
from app.workflows.agnostic_research_report.orchestrator import AgnosticResearchOrchestrator
from app.workflows.agnostic_research_report.telemetry import render_tree, render_table
from app.workflows.agnostic_research_report.cli import parse_args, execute_cli


class TestAgnosticResearchReportStep1(unittest.TestCase):
    """Tests for Step 1: Data Models and Markdown Prompt Parser."""

    def test_models_instantiation(self):
        """Verifies dataclass creation and serialization."""
        sec = SectionSpec(name="test_sec", title="Test Section", required_fields=["Field A", "Field B"])
        self.assertEqual(sec.name, "test_sec")
        self.assertEqual(len(sec.required_fields), 2)

        ev = AgnosticEvidence(
            id="E001",
            section_slug="test_sec",
            claim="Quantum computing reduces simulation time.",
            source_url="https://nature.com/articles/123",
            source_title="Nature Journal",
            source_domain="nature.com",
            published="2026-05-10",
            confidence="high",
            quote="simulations demonstrated 100x speedup",
        )
        self.assertEqual(ev.id, "E001")
        d = ev.to_dict()
        self.assertEqual(d["claim"], "Quantum computing reduces simulation time.")
        self.assertEqual(d["source_domain"], "nature.com")

    def test_spec_parser_standard_template(self):
        """Verifies MarkdownSpecParser parses the standard research template accurately."""
        template_path = Path(backend_dir) / "app" / "workflows" / "agnostic_research_report" / "templates" / "standard_research_report.md"
        self.assertTrue(template_path.is_file(), f"Template not found at {template_path}")

        spec = MarkdownSpecParser.parse_file(str(template_path))
        self.assertIsInstance(spec, ReportPromptSpec)

        # Check sections count (8 sections expected)
        self.assertGreaterEqual(len(spec.sections), 8)

        # Check section names
        sec_names = [s.name for s in spec.sections]
        self.assertIn("executive_summary", sec_names)
        self.assertIn("background_context", sec_names)
        self.assertIn("technical_core_analysis", sec_names)
        self.assertIn("overall_synthesis_verdict", sec_names)

        # Check section details
        exec_sec = spec.get_section("executive_summary")
        self.assertIsNotNone(exec_sec)
        self.assertTrue(exec_sec.is_synthesis)

        # Check closing statement
        self.assertIn("Assessment based solely on information contained in this report.", spec.closing_statement)

    def test_spec_parser_custom_markdown(self):
        """Verifies MarkdownSpecParser on arbitrary custom markdown structure."""
        custom_md = """# CUSTOM EVALUATION SPECIFICATION

Global Instructions:
- Maintain an objective perspective.
- Avoid promotional language.

## TITLE
Format:
# SUBJECT REPORT

## 1. MARKET OVERVIEW
- Market size
- Key participants
- Growth rate

## 2. CRITICAL BOTTLENECKS
- Regulatory friction
- Supply constraints

## 3. FINAL SYNTHESIS & VERDICT
- High-level decision
- Confidence band

End the report with exactly:
"Final evaluation concluded."
"""
        spec = MarkdownSpecParser.parse(custom_md)
        self.assertEqual(len(spec.sections), 3)
        self.assertEqual(spec.sections[0].name, "market_overview")
        self.assertEqual(len(spec.sections[0].required_fields), 3)
        self.assertIn("Final evaluation concluded.", spec.closing_statement)


class TestAgnosticResearchReportStep2(unittest.IsolatedAsyncioTestCase):
    """Tests for Step 2: Evidence Ledger and Perplexity Web Retrieval Subsystem."""

    def test_ledger_sequential_id_and_citation_resolution(self):
        """Verifies ledger adds items with E001, E002, resolves citations, and produces stats."""
        ledger = AgnosticEvidenceLedger()
        items = [
            AgnosticEvidence(id="", section_slug="sec_a", claim="Claim 1", source_url="https://site1.com", source_domain="site1.com", confidence="high"),
            AgnosticEvidence(id="", section_slug="sec_a", claim="Claim 2", source_url="https://site2.com", source_domain="site2.com", confidence="med"),
            AgnosticEvidence(id="", section_slug="sec_b", claim="Claim 3", source_url="https://site1.com", source_domain="site1.com", confidence="high"),
        ]
        added = ledger.add(items)
        self.assertEqual(len(added), 3)
        self.assertEqual(added[0].id, "E001")
        self.assertEqual(added[1].id, "E002")
        self.assertEqual(added[2].id, "E003")

        # Resolve citations
        ev1 = ledger.resolve_citation("E001")
        self.assertIsNotNone(ev1)
        self.assertEqual(ev1.claim, "Claim 1")

        ev2 = ledger.resolve_citation("[E002]")
        self.assertIsNotNone(ev2)
        self.assertEqual(ev2.claim, "Claim 2")

        # Section filtering
        sec_a_items = ledger.for_section("sec_a")
        self.assertEqual(len(sec_a_items), 2)
        sec_b_items = ledger.for_section("sec_b")
        self.assertEqual(len(sec_b_items), 1)

        # Stats
        stats = ledger.stats()
        self.assertEqual(stats["total_evidence_count"], 3)
        self.assertEqual(stats["sections_covered"], 2)
        self.assertEqual(stats["high_confidence_count"], 2)

    def test_result_compactor(self):
        """Verifies cleaning snippets and deduplicating syndicated articles."""
        raw = "![img](https://test.com/pic.jpg) This is [a link](https://test.com)   with    whitespace.   "
        clean = ResultCompactor.clean_snippet(raw)
        self.assertEqual(clean, "This is a link with whitespace.")

        dup_results = [
            {"title": "Breaking News on AI", "snippet": "A major announcement occurred today regarding compute.", "url": "https://wire1.com/a"},
            {"title": "Breaking News on AI", "snippet": "A major announcement occurred today regarding compute.", "url": "https://wire2.com/b"},
            {"title": "Unique Story", "snippet": "Different event happened.", "url": "https://unique.com/c"},
        ]
        deduped = ResultCompactor.deduplicate_results(dup_results)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["url"], "https://wire1.com/a")
        self.assertEqual(deduped[1]["url"], "https://unique.com/c")

    async def test_search_queue_mock_batch(self):
        """Verifies PerplexitySearchQueue batch retrieval under test mock conditions."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            queue = PerplexitySearchQueue(cache_dir=tmp_dir)
            queries = [
                {"text": "Quantum error correction breakthroughs", "domains": ["nature.com"]},
                {"text": "Top quantum computing startups", "domains": ["techcrunch.com"]},
            ]

            orig_env = os.environ.copy()
            os.environ["TESTING"] = "true"
            os.environ["ALLOW_MOCK_DATA"] = "true"
            os.environ["MOCK_PERPLEXITY"] = "true"
            try:
                results, timings = await queue.batch_search_with_timings(queries)
                self.assertGreaterEqual(len(results), 2)
                self.assertEqual(timings["queries_count"], 2)
                self.assertGreater(timings["duration_ms"], 0)
            finally:
                os.environ.clear()
                os.environ.update(orig_env)

    async def test_search_queue_live_strict_credentials_enforcement(self):
        """Verifies that in live mode (no mock flags), missing PERPLEXITY_API_KEY raises RuntimeError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            queue = PerplexitySearchQueue(cache_dir=tmp_dir)

            orig_env = os.environ.copy()
            os.environ["TESTING"] = "false"
            os.environ["ALLOW_MOCK_DATA"] = "false"
            os.environ["MOCK_PERPLEXITY"] = "false"
            os.environ["PERPLEXITY_API_KEY"] = ""

            try:
                with self.assertRaises(RuntimeError) as ctx:
                    await queue.search("Live query test")
                self.assertIn("PERPLEXITY_API_KEY is not configured", str(ctx.exception))
            finally:
                os.environ.clear()
                os.environ.update(orig_env)


class TestAgnosticResearchReportStep3(unittest.IsolatedAsyncioTestCase):
    """Tests for Step 3: Multi-Provider LLM Cognitive Roles and Token Tracking."""

    def test_extract_json_resilience(self):
        """Verifies _extract_json parses thinking blocks, markdown fences, and trailing commas."""
        text_with_thinking = "<thinking>Deep reasoning here</thinking>\n```json\n{\"items\": [\"a\", \"b\"],}\n```"
        parsed = _extract_json(text_with_thinking)
        self.assertEqual(parsed, {"items": ["a", "b"]})

    def test_provider_configuration(self):
        """Verifies setting active provider and fallback model."""
        set_active_provider("groq")
        self.assertEqual(get_active_provider(), "groq")
        set_active_provider("azure")
        self.assertEqual(get_active_provider(), "azure")

        set_fallback_model("claude-opus-4-8")
        self.assertEqual(get_fallback_model(), "claude-opus-4-8")

    async def test_run_role_mock_with_tokens(self):
        """Verifies run_role yields 4-tuple with parsed payload and token usage."""
        orig_env = os.environ.copy()
        os.environ["TESTING"] = "true"
        os.environ["ALLOW_MOCK_DATA"] = "true"
        os.environ["MOCK_ROLES"] = "true"
        try:
            res, usage, dur_ms, model = await run_role("plan", "Subject: Advanced Nuclear SMRs")
            self.assertIn("queries", res)
            self.assertIn("input_tokens", usage)
            self.assertIn("output_tokens", usage)
            self.assertIn("total_tokens", usage)
            self.assertGreater(dur_ms, 0)
            self.assertEqual(model, "mock-model")
        finally:
            os.environ.clear()
            os.environ.update(orig_env)

    async def test_execute_azure_chat_with_tokens_mock(self):
        """Verifies _execute_azure_chat_with_tokens properly parses content and usage."""
        from unittest.mock import patch, MagicMock

        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 200
        mock_http_resp.json.return_value = {
            "content": [{"type": "text", "text": "{\"queries\": [{\"text\": \"q1\"}]}"}],
            "usage": {"input_tokens": 150, "output_tokens": 40},
        }

        with patch.dict(os.environ, {"AZURE_API_KEY": "sk-azure-key"}), \
             patch("httpx.AsyncClient.post", return_value=mock_http_resp):
            text, usage = await _execute_azure_chat_with_tokens(
                model="claude-sonnet-4-6",
                system_prompt="Test sys",
                user_prompt="Test user",
                temp=0.1,
                max_tokens=500,
            )
            self.assertIn("queries", text)
            self.assertEqual(usage["input_tokens"], 150)
            self.assertEqual(usage["output_tokens"], 40)
            self.assertEqual(usage["total_tokens"], 190)


class TestAgnosticResearchReportStep4(unittest.IsolatedAsyncioTestCase):
    """Tests for Step 4: Orchestrator and Publication File Generation Agent."""

    def test_footnote_transformer(self):
        """Verifies [E###] citation replacement and footnote dictionary assembly."""
        ledger = AgnosticEvidenceLedger()
        items = [
            AgnosticEvidence(id="", section_slug="sec", claim="Claim 1", source_url="https://site1.com", source_domain="site1.com", published="2026-01-01", quote="Exact quote"),
            AgnosticEvidence(id="", section_slug="sec", claim="Claim 2", source_url="https://site2.com", source_domain="site2.com", published="2026-02-02", quote="Quote two"),
        ]
        ledger.add(items)

        text = "Key finding stated in literature [E001] and supported by trials [E002]. Another note [E001]."
        transformed, footnotes = FootnoteTransformer.transform_citations(text, ledger)

        self.assertIn("[1]", transformed)
        self.assertIn("[2]", transformed)
        self.assertNotIn("[E001]", transformed)
        self.assertEqual(len(footnotes), 2)
        self.assertEqual(footnotes[0]["num"], 1)
        self.assertEqual(footnotes[0]["claim"], "Claim 1")
        self.assertEqual(footnotes[0]["source_domain"], "site1.com")

    def test_markdown_and_pdf_renderers(self):
        """Verifies Markdown and ReportLab PDF file generation with NumberedCanvas."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = os.path.join(tmp_dir, "test_report.pdf")
            sections = ["## 1. OVERVIEW\n- First bullet finding [1].\n\n## 2. DETAILS\n- Second finding [2]."]
            footnotes = [
                {"num": 1, "claim": "Fact 1", "source_url": "https://example.com/1", "source_domain": "example.com", "published": "2026-03-01", "confidence": "high", "quote": "Q1"},
                {"num": 2, "claim": "Fact 2", "source_url": "https://example.com/2", "source_domain": "example.com", "published": "2026-03-02", "confidence": "med", "quote": "Q2"},
            ]
            meta = {
                "date": "2026-11-05",
                "model": "claude-sonnet-4-6",
                "provider": "azure",
                "evidence_count": 2,
                "total_tokens": 500,
                "duration_seconds": 3.5,
                "concurrency_speedup": "2.1x",
            }

            # Markdown
            md_text = AgnosticMarkdownRenderer.render("Quantum Computing", sections, footnotes, closing_statement="Done.", metadata=meta)
            self.assertIn("# QUANTUM COMPUTING", md_text)
            self.assertIn("## SOURCES & FOOTNOTES", md_text)
            self.assertIn("Done.", md_text)

            # PDF
            res_pdf = AgnosticPdfRenderer.render("Quantum Computing", sections, footnotes, pdf_path, closing_statement="Done.", metadata=meta)
            self.assertTrue(os.path.isfile(res_pdf))
            self.assertGreater(os.path.getsize(res_pdf), 1000)

    async def test_orchestrator_end_to_end_mock(self):
        """Verifies AgnosticResearchOrchestrator runs multi-stage workflow in mock test environment."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            orchestrator = AgnosticResearchOrchestrator(artifacts_dir=tmp_dir)

            custom_prompt = """# AGNOSTIC EVALUATION
## 1. EXECUTIVE SUMMARY
- Summary bullets
## 2. TECHNICAL PROGRESS
- Milestones
## 3. VERDICT
- Bottom line
End the report with exactly:
"Assessment verified."
"""
            orig_env = os.environ.copy()
            os.environ["TESTING"] = "true"
            os.environ["ALLOW_MOCK_DATA"] = "true"
            os.environ["MOCK_ROLES"] = "true"
            os.environ["MOCK_PERPLEXITY"] = "true"

            try:
                progress_events = []
                def on_progress(stage, detail):
                    progress_events.append((stage, detail))

                result = await orchestrator.run(
                    subject="Solid State Batteries",
                    prompt_markdown=custom_prompt,
                    mode="fast",
                    provider="azure",
                    model="claude-sonnet-4-6",
                    output_dir=tmp_dir,
                    on_progress=on_progress,
                )

                self.assertTrue(os.path.isfile(result.markdown_path))
                self.assertTrue(os.path.isfile(result.pdf_path))
                self.assertTrue(os.path.isfile(result.telemetry_path))
                self.assertGreater(result.total_tokens, 0)
                self.assertGreaterEqual(len(progress_events), 3)

                # Check telemetry structure
                telemetry = result.telemetry_data
                self.assertEqual(telemetry["subject"], "Solid State Batteries")
                self.assertIn("stages", telemetry)
                self.assertIn("stage_2_research_and_draft", telemetry["stages"])
                self.assertIn("tokens", telemetry)

            finally:
                os.environ.clear()
                os.environ.update(orig_env)


class TestAgnosticResearchReportStep5(unittest.IsolatedAsyncioTestCase):
    """Tests for Step 5: Hierarchical Timings, Token Accounting, and CLI."""

    def test_render_tree_and_table(self):
        """Verifies render_tree and render_table produce formatted ASCII displays."""
        telemetry = {
            "total_wall_clock_ms": 4200.0,
            "total_compute_ms": 10500.0,
            "concurrency_speedup": "2.50x",
            "tokens": {"input_tokens": 1200, "output_tokens": 400, "total_tokens": 1600},
            "stages": {
                "stage_1_spec_parse": {"sections_count": 3},
                "stage_2_research_and_draft": {
                    "wall_clock_ms": 3500.0,
                    "sections": {
                        "sec_one": {
                            "total_ms": 3500.0,
                            "tokens": {"total_tokens": 800},
                            "subsections": {
                                "planning_ms": 200.0,
                                "retrieval_ms": 1200.0,
                                "extract_ms": 600.0,
                                "gap_ms": 0.0,
                                "draft_narrative_ms": 1500.0,
                                "queries_count": 2,
                                "claims_extracted": 3,
                                "evidence_cited_count": 2,
                                "rounds": [],
                            }
                        }
                    }
                },
                "stage_3_synthesis": {
                    "wall_clock_ms": 500.0,
                    "sections": {"verdict": {"duration_ms": 500.0, "tokens": {"total_tokens": 400}}}
                },
                "stage_5_rendering": {"wall_clock_ms": 200.0, "footnotes_count": 2},
            }
        }

        tree = render_tree(telemetry, "Solid State Batteries")
        self.assertIn("GRANULAR TIMINGS TREE", tree)
        self.assertIn("SOLID STATE BATTERIES", tree)
        self.assertIn("1,600", tree)
        self.assertIn("2.50x", tree)
        self.assertIn("sec_one", tree)

        tbl = render_table(telemetry, "Solid State Batteries")
        self.assertIn("TIMINGS & TOKENS TABLE", tbl)
        self.assertIn("sec_one", tbl)
        self.assertIn("1,600", tbl)

    def test_cli_argument_parsing(self):
        """Verifies CLI argument parser flags."""
        args = parse_args([
            "Quantum Computing in Drug Discovery",
            "--prompt-file", "prompt.md",
            "--model", "claude-sonnet-4-6",
            "--provider", "azure",
            "--fallback-model", "claude-opus-4-8",
            "--mode", "deep",
            "--format", "table",
            "--quiet",
        ])
        self.assertEqual(args.subject, "Quantum Computing in Drug Discovery")
        self.assertEqual(args.prompt_file, "prompt.md")
        self.assertEqual(args.model, "claude-sonnet-4-6")
        self.assertEqual(args.provider, "azure")
        self.assertEqual(args.fallback_model, "claude-opus-4-8")
        self.assertEqual(args.mode, "deep")
        self.assertEqual(args.format, "table")
        self.assertTrue(args.quiet)

    async def test_cli_execution_mock(self):
        """Verifies execute_cli completes cleanly with mock environment."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            orig_env = os.environ.copy()
            os.environ["TESTING"] = "true"
            os.environ["ALLOW_MOCK_DATA"] = "true"
            os.environ["MOCK_ROLES"] = "true"
            os.environ["MOCK_PERPLEXITY"] = "true"

            try:
                args = parse_args([
                    "Solid State Batteries",
                    "--mode", "fast",
                    "--format", "tree",
                    "--output-dir", tmp_dir,
                    "--quiet",
                ])
                ret = await execute_cli(args)
                self.assertEqual(ret, 0)

                # Check artifacts generated
                files = list(Path(tmp_dir).glob("Research_Report_*"))
                self.assertGreaterEqual(len(files), 3)  # .md, .pdf, _telemetry.json
            finally:
                os.environ.clear()
                os.environ.update(orig_env)


class TestAgnosticRateLimitRetry(unittest.IsolatedAsyncioTestCase):
    """Verifies 429 rate limit parsing, dynamic backoff and retry handling."""

    def test_parse_retry_delay(self):
        msg_1s = "Rate limit of 8000 per 60s exceeded for UserByModelByMinuteOutputTokens. Please wait 1 seconds before retrying."
        self.assertEqual(parse_retry_delay(msg_1s), 3.0)  # 1.0 + 2.0 buffer

        msg_8s = "Please wait 8 seconds before retrying."
        self.assertEqual(parse_retry_delay(msg_8s), 10.0)  # 8.0 + 2.0 buffer

        msg_alt = "retry after 12.5 seconds"
        self.assertEqual(parse_retry_delay(msg_alt), 14.5)  # 12.5 + 2.0 buffer

        # Fallback when no seconds regex match
        msg_none = "Generic rate limit reached"
        self.assertEqual(parse_retry_delay(msg_none, default_wait=5.0, attempt=2), 15.0)

    async def test_roles_retry_on_429(self):
        """Simulates a 429 rate limit error followed by success."""
        from unittest.mock import patch

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
            with patch("app.workflows.agnostic_research_report.roles._execute_azure_chat_with_tokens", side_effect=fake_azure_call):
                res, usage, dur, model = await run_role(
                    "draft",
                    "Draft test section",
                    provider_override="azure",
                    model_override="claude-opus-4-8",
                )
                self.assertEqual(call_count, 2)
                self.assertIn("Valid drafted bullet", res.get("section_text", ""))
        finally:
            os.environ.clear()
            os.environ.update(orig_env)

    async def test_orchestrator_section_draft_retry_recovers(self):
        """Verifies that orchestrator _process_section retries on transient draft failure and succeeds."""
        from unittest.mock import patch
        from app.workflows.agnostic_research_report.orchestrator import AgnosticResearchOrchestrator
        from app.workflows.agnostic_research_report.ledger import AgnosticEvidenceLedger
        from app.workflows.agnostic_research_report.models import SectionSpec

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
            with patch("app.workflows.agnostic_research_report.orchestrator.run_role", side_effect=mock_run_role):
                with patch("asyncio.sleep", return_value=None):
                    text, timing = await orch._process_section(
                        subject="NVIDIA",
                        section=sec,
                        ledger=ledger,
                        global_rules="Rules",
                        mode="fast",
                        model="claude-opus-4-8",
                        provider="azure",
                    )
                    self.assertEqual(draft_call_count, 2)
                    self.assertIn("Successful recovered draft", text)
                    self.assertNotIn("unavailable due to upstream error", text)
        finally:
            os.environ.clear()
            os.environ.update(orig_env)


    def test_resolve_foundry_endpoint_routing(self):
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

        # When AZURE_FOUNDRY_ENDPOINT is set to anthropic endpoint in env
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

        # When bare host is provided
        base_host = "https://puneetshrivas32-0871-resource.services.ai.azure.com"
        self.assertEqual(resolve_foundry_endpoint("gpt-5.4", base_host), default_openai)
        self.assertEqual(resolve_foundry_endpoint("claude-opus-4-8", base_host), default_anthropic)


if __name__ == "__main__":
    unittest.main()
