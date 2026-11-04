"""
Unit tests for Azure AI Foundry Three-Agent Pipeline (azure_agents_pipeline).
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from azure_agents_pipeline.config import (
    DEFAULT_ENDPOINT,
    DEFAULT_RESEARCHER_AGENT,
    DEFAULT_VALIDATOR_AGENT,
    DEFAULT_GENERATOR_AGENT,
    check_azure_credentials_available,
)
from azure_agents_pipeline.telemetry import StepTelemetry, PipelineTelemetry
from azure_agents_pipeline.pdf_compiler import ReportPdfCompiler
from azure_agents_pipeline.pipeline import AzureFoundryAgentTrioPipeline
from azure_agents_pipeline.run_pipeline import parse_args


class TestAzureAgentsPipeline(unittest.TestCase):

    def test_config_defaults(self):
        """Verifies default project endpoint and agent naming configurations."""
        self.assertIn("puneetshrivas32-0871", DEFAULT_ENDPOINT)
        self.assertEqual(DEFAULT_RESEARCHER_AGENT, "DO-researcher")
        self.assertEqual(DEFAULT_VALIDATOR_AGENT, "DO-validator")
        self.assertEqual(DEFAULT_GENERATOR_AGENT, "DO-report-generator")

        is_avail, msg = check_azure_credentials_available()
        self.assertIsInstance(is_avail, bool)
        self.assertIsInstance(msg, str)
        self.assertGreater(len(msg), 10)

    def test_telemetry_token_and_duration_aggregation(self):
        """Verifies accurate calculation of total input, output, and aggregate tokens."""
        pipeline_tel = PipelineTelemetry(
            user_prompt="Evaluate NVDA D&O exposure",
            started_at_iso="2026-11-04T12:00:00",
            completed_at_iso="2026-11-04T12:00:30",
            total_duration_seconds=30.0,
        )

        # Mock Step 1
        s1 = StepTelemetry(agent_name="DO-researcher", role_title="Deep Risk Researcher", start_time=100.0)
        usage1 = MagicMock(input_tokens=1500, output_tokens=800, total_tokens=2300)
        s1.complete(
            output_text="### COMPANY SNAPSHOT\n- Legal name: NVIDIA Corporation",
            conversation_id="conv_001",
            response_id="resp_001",
            usage=usage1,
        )
        pipeline_tel.steps.append(s1)

        # Mock Step 2
        s2 = StepTelemetry(agent_name="DO-validator", role_title="Adversarial Audit & Validator", start_time=102.0)
        usage2 = MagicMock(input_tokens=2400, output_tokens=900, total_tokens=3300)
        s2.complete(
            output_text="### AUDITED REPORT\n- Verified legal name: NVIDIA Corporation",
            conversation_id="conv_002",
            response_id="resp_002",
            usage=usage2,
        )
        pipeline_tel.steps.append(s2)

        # Mock Step 3
        s3 = StepTelemetry(agent_name="DO-report-generator", role_title="Executive Report Formatter", start_time=105.0)
        usage3 = MagicMock(input_tokens=3400, output_tokens=1100, total_tokens=4500)
        s3.complete(
            output_text="# FINAL REPORT\n- Executive summary",
            conversation_id="conv_003",
            response_id="resp_003",
            usage=usage3,
        )
        pipeline_tel.steps.append(s3)

        self.assertEqual(pipeline_tel.total_input_tokens, 1500 + 2400 + 3400)
        self.assertEqual(pipeline_tel.total_output_tokens, 800 + 900 + 1100)
        self.assertEqual(pipeline_tel.total_tokens, 2300 + 3300 + 4500)

        # Check console summary formatting
        summary = pipeline_tel.format_console_summary()
        self.assertIn("DO-researcher", summary)
        self.assertIn("DO-validator", summary)
        self.assertIn("DO-report-generator", summary)
        self.assertIn(f"{pipeline_tel.total_tokens:,}", summary)

    def test_pdf_compiler_renders_valid_document(self):
        """Verifies ReportPdfCompiler compiles markdown text into an executive PDF with valid checksum."""
        sample_markdown = (
            "# D&O RISK UNDERWRITING ASSESSMENT\n"
            "## EXECUTIVE SUMMARY\n"
            "- Overall Underwriting Verdict: **Contained**\n"
            "- Primary carrier attachment recommendation: $25M primary tower.\n"
            "### FINANCIAL OVERVIEW\n"
            "- Annual revenues reported at $60.9B for FY2024.\n"
            "- Operating cash flow: $28.09B.\n"
            "### SECURITIES LITIGATION\n"
            "- Zero active class actions pending in U.S. federal court."
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = os.path.join(tmp_dir, "test_assessment.pdf")
            compiler = ReportPdfCompiler(pdf_path)
            res = compiler.compile(
                report_text=sample_markdown,
                title="D&O Risk Underwriting Assessment: NVDA",
                metadata={"user_prompt": "NVDA Underwriting Assessment", "total_duration_seconds": 12.34},
            )

            self.assertTrue(os.path.isfile(pdf_path))
            self.assertGreater(res["file_size_bytes"], 1000)
            self.assertEqual(len(res["sha256_checksum"]), 64)

    def test_pipeline_chaining_and_artifact_generation(self):
        """Verifies end-to-end sequential agent piping: Researcher -> Validator -> Generator -> PDF."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            pipeline = AzureFoundryAgentTrioPipeline(output_dir=tmp_dir)

            # Mock responses for each agent
            mock_res_resp = MagicMock()
            mock_res_resp.id = "resp_res_001"
            mock_res_resp.output_text = "### PRELIMINARY REPORT\n- Research finding for target"
            mock_res_resp.usage = MagicMock(input_tokens=100, output_tokens=50, total_tokens=150)
            mock_res_resp.model = "claude-sonnet-4-6"
            mock_res_resp.status = "completed"

            mock_val_resp = MagicMock()
            mock_val_resp.id = "resp_val_002"
            mock_val_resp.output_text = "### AUDITED REPORT\n- Validated finding for target"
            mock_val_resp.usage = MagicMock(input_tokens=180, output_tokens=60, total_tokens=240)
            mock_val_resp.model = "claude-sonnet-4-6"
            mock_val_resp.status = "completed"

            mock_gen_resp = MagicMock()
            mock_gen_resp.id = "resp_gen_003"
            mock_gen_resp.output_text = "# FINAL EXECUTIVE PUBLICATION\n- Final styled section"
            mock_gen_resp.usage = MagicMock(input_tokens=250, output_tokens=80, total_tokens=330)
            mock_gen_resp.model = "claude-opus-4-8"
            mock_gen_resp.status = "completed"

            # Create mock openai clients for each agent
            mock_openai_client = MagicMock()
            mock_openai_client.conversations.create.side_effect = [
                MagicMock(id="conv_1"),
                MagicMock(id="conv_2"),
                MagicMock(id="conv_3"),
            ]
            mock_openai_client.responses.create.side_effect = [
                mock_res_resp,
                mock_val_resp,
                mock_gen_resp,
            ]

            mock_project_client = MagicMock()
            mock_project_client.get_openai_client.return_value = mock_openai_client
            mock_project_client.__enter__.return_value = mock_project_client

            with patch("azure_agents_pipeline.pipeline.AIProjectClient", return_value=mock_project_client), \
                 patch("azure_agents_pipeline.pipeline.get_azure_credential") as mock_cred:
                mock_cred.return_value = MagicMock()

                telemetry = pipeline.run(user_input="Assess NVIDIA governance risk", ticker="NVDA")

                # Verify 3 steps executed in order
                self.assertEqual(len(telemetry.steps), 3)
                self.assertEqual(telemetry.steps[0].agent_name, "DO-researcher")
                self.assertEqual(telemetry.steps[1].agent_name, "DO-validator")
                self.assertEqual(telemetry.steps[2].agent_name, "DO-report-generator")

                # Verify token sums
                self.assertEqual(telemetry.total_tokens, 150 + 240 + 330)
                self.assertGreater(telemetry.total_duration_seconds, 0.0)

                # Verify files were generated
                self.assertIn("markdown", telemetry.output_files)
                self.assertIn("pdf", telemetry.output_files)
                self.assertIn("telemetry_json", telemetry.output_files)

                self.assertTrue(os.path.isfile(telemetry.output_files["markdown"]))
                self.assertTrue(os.path.isfile(telemetry.output_files["pdf"]))
                self.assertTrue(os.path.isfile(telemetry.output_files["telemetry_json"]))

    def test_cli_argument_parser(self):
        """Verifies CLI argument parsing for positional ticker and optional flags."""
        with patch("sys.argv", ["run_pipeline.py", "NVDA", "--output-dir", "./test_out"]):
            args = parse_args()
            self.assertEqual(args.ticker, "NVDA")
            self.assertEqual(args.output_dir, "./test_out")
            self.assertFalse(args.interactive)


if __name__ == "__main__":
    unittest.main()
