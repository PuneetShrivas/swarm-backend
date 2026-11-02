"""
Tests for Workflow Step Artifact & Resource Judicious Assignment and Persistence
Verifies:
1. Artifact classification (template, source, reference).
2. Judicious distribution of artifacts to workflow steps according to roles/goals.
3. Explicit user prompt instructions overriding default step bindings.
4. Execution engine resource context injection into agent prompts.
5. Pydantic schema validation for step resources in WorkflowStep.
"""

import unittest
from unittest.mock import MagicMock
from app.ai_generator import classify_artifact_purpose, assign_artifacts_to_steps
from app.workflows.models import WorkflowStep, WorkflowCreateUpdatePayload
from app.workflows.engine import WorkflowExecutionEngine


class TestWorkflowStepResourceAssignment(unittest.TestCase):

    def test_classify_artifact_purpose(self):
        # Template classifications
        art_tpl = {"filename": "executive_report_template.md", "content": "# Section 1: Summary\n# Section 2: Financials"}
        self.assertEqual(classify_artifact_purpose(art_tpl, "write a report"), "template")

        art_format = {"filename": "audit_format.json", "content": '{"header": "Audit", "fields": []}'}
        self.assertEqual(classify_artifact_purpose(art_format, "audit report"), "template")

        # Source dataset classifications
        art_data = {"filename": "q3_revenue_breakdown.xlsx", "content": "base64content..."}
        self.assertEqual(classify_artifact_purpose(art_data, "analyze q3 revenue"), "source")

        art_csv = {"filename": "customer_churn.csv", "content": "customer_id,churned\n1,0"}
        self.assertEqual(classify_artifact_purpose(art_csv, "analyze churn"), "source")

        # Reference document classifications
        art_pdf = {"filename": "market_trends_2026.pdf", "content": "base64content..."}
        self.assertEqual(classify_artifact_purpose(art_pdf, "research 2026 market trends"), "reference")

        art_brief = {"filename": "project_brief.txt", "content": "Background details about the company."}
        self.assertEqual(classify_artifact_purpose(art_brief, "write proposal"), "reference")

    def test_judicious_artifact_distribution(self):
        """
        Given a multi-agent pipeline:
        Step 1: researcher (gathers facts)
        Step 2: data_analyst (computes numbers)
        Step 3: writer (drafts final report)
        Verify that each artifact is assigned to the appropriate step.
        """
        steps = [
            {
                "id": "step_1_research",
                "name": "Research Market Background",
                "agent_id": "researcher",
                "instructions": "Research latest trends and background.",
            },
            {
                "id": "step_2_analysis",
                "name": "Financial Data Analysis",
                "agent_id": "data_analyst",
                "instructions": "Compute quarterly metrics and KPIs.",
            },
            {
                "id": "step_3_synthesis",
                "name": "Draft Executive Report",
                "agent_id": "writer",
                "instructions": "Synthesize findings into an executive report.",
            },
        ]

        artifacts = [
            {
                "id": "art_1",
                "filename": "industry_background.pdf",
                "content": "Industry background details",
                "mime_type": "application/pdf",
            },
            {
                "id": "art_2",
                "filename": "q3_financials.xlsx",
                "content": "Revenue: 1.2M",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
            {
                "id": "art_3",
                "filename": "board_presentation_template.md",
                "content": "# Executive Summary\n## Findings\n## Recommendations",
                "mime_type": "text/markdown",
            },
        ]

        prompt = "Conduct a market research study using industry_background.pdf, analyze q3_financials.xlsx, and write the final document using board_presentation_template.md"

        assigned_steps = assign_artifacts_to_steps(steps, artifacts, prompt)

        # Step 1 should have industry_background.pdf (reference)
        step1_res = assigned_steps[0].get("resources", [])
        self.assertTrue(any(r["filename"] == "industry_background.pdf" for r in step1_res), "Step 1 missing industry_background.pdf")
        self.assertTrue(any(r["role"] == "reference" for r in step1_res))

        # Step 2 should have q3_financials.xlsx (source)
        step2_res = assigned_steps[1].get("resources", [])
        self.assertTrue(any(r["filename"] == "q3_financials.xlsx" for r in step2_res), "Step 2 missing q3_financials.xlsx")
        self.assertTrue(any(r["role"] == "source" for r in step2_res))

        # Step 3 should have board_presentation_template.md (template)
        step3_res = assigned_steps[2].get("resources", [])
        self.assertTrue(any(r["filename"] == "board_presentation_template.md" for r in step3_res), "Step 3 missing template")
        self.assertTrue(any(r["role"] == "template" for r in step3_res))

        # Step 3 instructions should be enriched with template adherence note
        self.assertIn("board_presentation_template.md", assigned_steps[2]["instructions"])

    def test_explicit_user_prompt_binding(self):
        """
        If user prompt explicitly specifies:
        'In step 1, analyze data_sample.csv and write raw summary',
        the CSV should bind to step 1.
        """
        steps = [
            {
                "id": "step_1_ingest",
                "name": "Ingest and Summarize Data",
                "agent_id": "file_parser",
                "instructions": "Parse input data.",
            },
            {
                "id": "step_2_conclude",
                "name": "Final Conclusion",
                "agent_id": "writer",
                "instructions": "Write conclusions.",
            },
        ]

        artifacts = [
            {
                "id": "art_csv",
                "filename": "data_sample.csv",
                "content": "id,val\n1,100",
                "mime_type": "text/csv",
            }
        ]

        prompt = "Please use data_sample.csv in step 1 to extract stats."
        assigned_steps = assign_artifacts_to_steps(steps, artifacts, prompt)

        step1_res = assigned_steps[0].get("resources", [])
        self.assertEqual(len(step1_res), 1)
        self.assertEqual(step1_res[0]["filename"], "data_sample.csv")

    def test_step_resources_injected_at_execution(self):
        """
        Verify that WorkflowExecutionEngine extracts step.get('resources')
        and provides it to relevant_files / format_knowledge_context.
        """
        engine = WorkflowExecutionEngine()

        captured = {}

        def mock_execute_agent_turn(agent, prompt, system_instructions, model_name=None, temperature=0.3):
            captured["prompt"] = prompt
            captured["system_instructions"] = system_instructions
            return "Execution complete according to template.", 150

        engine._execute_agent_turn = mock_execute_agent_turn

        step_with_resources = {
            "id": "step_draft",
            "name": "Draft Document",
            "agent_id": "writer",
            "instructions": "Draft the final report.",
            "resources": [
                {
                    "id": "res_tpl",
                    "filename": "brand_template.md",
                    "role": "template",
                    "content": "# Brand Header\nStandardized branding format",
                }
            ],
        }

        step_run = engine.execute_single_step(
            step=step_with_resources,
            inputs={"query": "test query"},
            previous_outputs={},
            goal="Test Goal",
            knowledge_files=[],
            tools_map={},
            user_id="test_user",
        )

        self.assertEqual(step_run.get("status"), "completed")
        # System instructions should have injected knowledge context containing the resource
        sys_inst = captured.get("system_instructions", "")
        self.assertIn("brand_template.md (template)", sys_inst)
        self.assertIn("Standardized branding format", sys_inst)

    def test_workflow_models_resource_schema(self):
        """
        Verify that WorkflowStep and WorkflowCreateUpdatePayload correctly
        serialize and validate step resources.
        """
        step = WorkflowStep(
            id="s1",
            name="Step 1",
            agent_id="researcher",
            resources=[
                {
                    "id": "art_123",
                    "filename": "reference_doc.pdf",
                    "role": "reference",
                    "source_title": "Market Study",
                }
            ],
        )

        dumped = step.model_dump()
        self.assertIn("resources", dumped)
        self.assertEqual(len(dumped["resources"]), 1)
        self.assertEqual(dumped["resources"][0]["filename"], "reference_doc.pdf")
        self.assertEqual(dumped["resources"][0]["role"], "reference")

        payload = WorkflowCreateUpdatePayload(
            title="Pipeline with Resources",
            goal="Test Goal",
            steps=[step],
        )
        payload_dump = payload.model_dump()
        self.assertEqual(len(payload_dump["steps"][0]["resources"]), 1)
        self.assertEqual(payload_dump["steps"][0]["resources"][0]["id"], "art_123")


if __name__ == "__main__":
    unittest.main()
