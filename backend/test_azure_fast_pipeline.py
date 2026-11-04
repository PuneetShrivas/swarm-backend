"""
Unit tests for Azure AI Foundry Fast Alternative Pipeline (azure_agents_pipeline/fast_pipeline.py).
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from azure_agents_pipeline.fast_pipeline import FastAzureFoundryPipeline
from azure_agents_pipeline.run_fast_pipeline import parse_args


class TestAzureFastPipeline(unittest.TestCase):

    def test_fast_pipeline_mode_both_execution(self):
        """Verifies mode='both' runs Researcher, Agent Generator, and Direct Model, producing dual PDFs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            pipeline = FastAzureFoundryPipeline(output_dir=tmp_dir)

            # Mock responses
            mock_res_resp = MagicMock()
            mock_res_resp.id = "resp_res_101"
            mock_res_resp.output_text = "### RAW RESEARCH\n- Target company is NVIDIA Corporation"
            mock_res_resp.usage = MagicMock(input_tokens=120, output_tokens=60, total_tokens=180)
            mock_res_resp.model = "claude-sonnet-4-6"
            mock_res_resp.status = "completed"

            mock_gen_resp = MagicMock()
            mock_gen_resp.id = "resp_gen_202"
            mock_gen_resp.output_text = "# FINAL AGENT REPORT\n- Fast agent formatted section"
            mock_gen_resp.usage = MagicMock(input_tokens=200, output_tokens=90, total_tokens=290)
            mock_gen_resp.model = "claude-sonnet-4-6"
            mock_gen_resp.status = "completed"

            mock_openai_client = MagicMock()
            mock_openai_client.conversations.create.side_effect = [
                MagicMock(id="conv_res"),
                MagicMock(id="conv_gen"),
            ]
            mock_openai_client.responses.create.side_effect = [
                mock_res_resp,
                mock_gen_resp,
            ]

            mock_project_client = MagicMock()
            mock_project_client.get_openai_client.return_value = mock_openai_client
            mock_project_client.__enter__.return_value = mock_project_client

            # Mock direct model execution
            mock_direct_text = "### DIRECT SYNTHESIS\n- Executive verdict: Contained"
            mock_direct_usage = SimpleNamespace(input_tokens=210, output_tokens=95, total_tokens=305)

            with patch("azure_agents_pipeline.fast_pipeline.AIProjectClient", return_value=mock_project_client), \
                 patch("azure_agents_pipeline.fast_pipeline.get_azure_credential") as mock_cred, \
                 patch.object(pipeline, "_execute_direct_model", return_value=(mock_direct_text, mock_direct_usage, "claude-sonnet-4-6")):
                mock_cred.return_value = MagicMock()

                telemetry = pipeline.run("NVIDIA Corporation", ticker="NVDA", mode="both")

                # Verify 3 steps recorded
                self.assertEqual(len(telemetry.steps), 3)
                self.assertEqual(telemetry.steps[0].agent_name, "DO-researcher")
                self.assertEqual(telemetry.steps[1].agent_name, "DO-report-generator")
                self.assertIn("claude-sonnet-4-6", telemetry.steps[2].agent_name)

                # Total tokens sum
                self.assertEqual(telemetry.total_tokens, 180 + 290 + 305)

                # Verify dual artifact generation
                self.assertIn("agent_markdown", telemetry.output_files)
                self.assertIn("agent_pdf", telemetry.output_files)
                self.assertIn("direct_markdown", telemetry.output_files)
                self.assertIn("direct_pdf", telemetry.output_files)
                self.assertIn("telemetry_json", telemetry.output_files)

                self.assertTrue(os.path.isfile(telemetry.output_files["agent_pdf"]))
                self.assertTrue(os.path.isfile(telemetry.output_files["direct_pdf"]))

                # Verify comparative summary string
                comp_summary = telemetry.format_fast_comparison_summary()
                self.assertIn("DO-report-generator", comp_summary)
                self.assertIn("AzureFoundry/claude-sonnet-4-6", comp_summary)
                self.assertIn("GENERATION PATHWAY COMPARISON", comp_summary)

    def test_fast_pipeline_mode_agent_only(self):
        """Verifies mode='agent' executes only Researcher and Report Generator agent."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            pipeline = FastAzureFoundryPipeline(output_dir=tmp_dir)

            mock_res_resp = MagicMock()
            mock_res_resp.output_text = "### RESEARCH ONLY"
            mock_res_resp.usage = MagicMock(input_tokens=100, output_tokens=50, total_tokens=150)

            mock_gen_resp = MagicMock()
            mock_gen_resp.output_text = "# AGENT REPORT ONLY"
            mock_gen_resp.usage = MagicMock(input_tokens=150, output_tokens=70, total_tokens=220)

            mock_openai_client = MagicMock()
            mock_openai_client.conversations.create.return_value = MagicMock(id="c1")
            mock_openai_client.responses.create.side_effect = [mock_res_resp, mock_gen_resp]

            mock_project_client = MagicMock()
            mock_project_client.get_openai_client.return_value = mock_openai_client
            mock_project_client.__enter__.return_value = mock_project_client

            with patch("azure_agents_pipeline.fast_pipeline.AIProjectClient", return_value=mock_project_client), \
                 patch("azure_agents_pipeline.fast_pipeline.get_azure_credential"):

                telemetry = pipeline.run("Apple Inc.", ticker="AAPL", mode="agent")

                self.assertEqual(len(telemetry.steps), 2)
                self.assertEqual(telemetry.steps[0].agent_name, "DO-researcher")
                self.assertEqual(telemetry.steps[1].agent_name, "DO-report-generator")
                self.assertIn("agent_pdf", telemetry.output_files)
                self.assertNotIn("direct_pdf", telemetry.output_files)

    def test_fast_pipeline_mode_direct_only(self):
        """Verifies mode='direct' executes only Researcher and Direct Azure Foundry model."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            pipeline = FastAzureFoundryPipeline(output_dir=tmp_dir)

            mock_res_resp = MagicMock()
            mock_res_resp.output_text = "### RESEARCH DATA"
            mock_res_resp.usage = MagicMock(input_tokens=100, output_tokens=50, total_tokens=150)

            mock_openai_client = MagicMock()
            mock_openai_client.conversations.create.return_value = MagicMock(id="c1")
            mock_openai_client.responses.create.return_value = mock_res_resp

            mock_project_client = MagicMock()
            mock_project_client.get_openai_client.return_value = mock_openai_client
            mock_project_client.__enter__.return_value = mock_project_client

            mock_direct_text = "### DIRECT MODEL REPORT"
            mock_direct_usage = SimpleNamespace(input_tokens=180, output_tokens=80, total_tokens=260)

            with patch("azure_agents_pipeline.fast_pipeline.AIProjectClient", return_value=mock_project_client), \
                 patch("azure_agents_pipeline.fast_pipeline.get_azure_credential"), \
                 patch.object(pipeline, "_execute_direct_model", return_value=(mock_direct_text, mock_direct_usage, "claude-sonnet-4-6")):

                telemetry = pipeline.run("Microsoft Corporation", ticker="MSFT", mode="direct")

                self.assertEqual(len(telemetry.steps), 2)
                self.assertEqual(telemetry.steps[0].agent_name, "DO-researcher")
                self.assertIn("claude-sonnet-4-6", telemetry.steps[1].agent_name)
                self.assertIn("direct_pdf", telemetry.output_files)
                self.assertNotIn("agent_pdf", telemetry.output_files)

    def test_execute_direct_model_rest_api_mock(self):
        """Verifies _execute_direct_model properly queries Azure Foundry REST endpoint with API key."""
        pipeline = FastAzureFoundryPipeline()

        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 200
        mock_http_resp.json.return_value = {
            "content": [{"type": "text", "text": "### SYNTHESIZED REPORT\n- Everything verified"}],
            "usage": {"input_tokens": 500, "output_tokens": 120},
        }

        with patch("azure_agents_pipeline.fast_pipeline.AZURE_API_KEY", "sk-valid-key"), \
             patch("httpx.Client.post", return_value=mock_http_resp):
            text, usage, model = pipeline._execute_direct_model(
                research_output="Raw research notes",
                target_company="NVDA",
            )
            self.assertIn("SYNTHESIZED REPORT", text)
            self.assertEqual(usage.input_tokens, 500)
            self.assertEqual(usage.output_tokens, 120)
            self.assertEqual(model, "claude-sonnet-4-6")

    def test_run_fast_pipeline_cli_parsing(self):
        """Verifies argument parser in run_fast_pipeline.py."""
        with patch("sys.argv", ["run_fast_pipeline.py", "TSLA", "--mode", "direct", "--model", "claude-opus-4-8"]):
            args = parse_args()
            self.assertEqual(args.company, "TSLA")
            self.assertEqual(args.mode, "direct")
            self.assertEqual(args.model, "claude-opus-4-8")


if __name__ == "__main__":
    unittest.main()
