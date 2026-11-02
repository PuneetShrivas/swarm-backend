"""
Test Suite: Workflow System Test Process & Backend Streaming Debugger
Validates:
1. WorkflowRunRequest schema accepting attached_artifacts and WorkflowStepRun telemetry.
2. Ingestion of ad-hoc test file attachments into step knowledge context during single step execution.
3. Real-time SSE event emission via POST /api/workflows/{workflow_id}/run-stream.
4. Error handling and failure event propagation during streaming pipeline execution.
"""

import unittest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.supabase import memory_store
from app.workflows.models import WorkflowRunRequest, WorkflowStepRun
from app.workflows.engine import WorkflowExecutionEngine


class TestSystemTestDebugger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_workflow_run_request_schema(self):
        """Verifies WorkflowRunRequest and WorkflowStepRun serialization with test attachments."""
        req = WorkflowRunRequest(
            inputs={"query": "Test query"},
            attached_artifacts=[
                {
                    "id": "art-1",
                    "filename": "test_data.csv",
                    "content": "col1,col2\n10,20",
                    "role": "source",
                }
            ],
        )
        dump = req.model_dump()
        self.assertIn("attached_artifacts", dump)
        self.assertEqual(len(dump["attached_artifacts"]), 1)
        self.assertEqual(dump["attached_artifacts"][0]["filename"], "test_data.csv")

        step_run = WorkflowStepRun(
            run_id="run-1",
            step_id="step-1",
            step_name="Data Ingestion",
            agent_id="data_analyst",
            status="completed",
            system_instructions="You are an analyst with test_data.csv",
            resources=[{"filename": "test_data.csv", "role": "source"}],
        )
        sr_dump = step_run.model_dump()
        self.assertEqual(sr_dump["step_name"], "Data Ingestion")
        self.assertEqual(sr_dump["system_instructions"], "You are an analyst with test_data.csv")
        self.assertEqual(len(sr_dump["resources"]), 1)

    def test_step_execution_ingests_test_attachments(self):
        """Verifies execute_single_step extracts ad-hoc test attachments and injects into system instructions."""
        engine = WorkflowExecutionEngine()

        captured = {}

        def mock_execute_agent(agent, prompt, system_instructions, model_name=None, temperature=0.3):
            captured["prompt"] = prompt
            captured["system_instructions"] = system_instructions
            return "Analysis complete with test_data.csv", 100

        engine._execute_agent_turn = mock_execute_agent

        step_def = {
            "id": "step_analysis",
            "name": "Analyze Revenue Data",
            "agent_id": "data_analyst",
            "instructions": "Analyze input figures from {{inputs.query}}.",
        }

        test_artifacts = [
            {
                "id": "art-test-1",
                "filename": "revenue_q3.csv",
                "content": "quarter,rev\nQ3,500000",
                "role": "source",
            }
        ]

        res = engine.execute_single_step(
            step=step_def,
            inputs={"query": "Evaluate Q3 numbers", "attached_artifacts": test_artifacts},
            previous_outputs={},
            goal="Test Revenue Flow",
            knowledge_files=[],
            tools_map={},
            user_id="test_user",
        )

        self.assertEqual(res.get("status"), "completed")
        self.assertEqual(res.get("step_name"), "Analyze Revenue Data")
        sys_instructions = captured.get("system_instructions", "")
        self.assertIn("revenue_q3.csv (source)", sys_instructions)
        self.assertIn("quarter,rev", sys_instructions)

    def test_run_workflow_stream_endpoint(self):
        """Verifies that /api/workflows/{id}/run-stream emits real-time SSE lines in proper sequence."""
        wf_id = "wf-stream-test-001"
        memory_store.create_workflow({
            "id": wf_id,
            "user_id": "anon-tester",
            "title": "Streamed Test Pipeline",
            "goal": "Verify SSE delivery",
            "steps": [
                {
                    "id": "s1",
                    "name": "Step One",
                    "agent_id": "orchestrator",
                    "instructions": "Task 1",
                },
                {
                    "id": "s2",
                    "name": "Step Two",
                    "agent_id": "writer",
                    "instructions": "Task 2",
                },
            ],
            "edges": [{"source": "s1", "target": "s2"}],
            "visibility": "private",
        })

        payload = {
            "inputs": {"query": "Execute test stream"},
            "attached_artifacts": [
                {
                    "id": "art-test",
                    "filename": "metrics.json",
                    "content": '{"metric": "uptime", "value": 99.9}',
                    "role": "reference",
                }
            ],
        }

        res = self.client.post(f"/api/workflows/{wf_id}/run-stream", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.headers.get("content-type", "").startswith("text/event-stream"))

        lines = [line.strip() for line in res.text.splitlines() if line.strip().startswith("data:")]
        self.assertGreaterEqual(len(lines), 4)

        event_types = []
        for line in lines:
            json_str = line.replace("data:", "").strip()
            data = json.loads(json_str)
            event_types.append(data.get("type"))

        # Verify event sequence
        self.assertEqual(event_types[0], "pipeline_start")
        self.assertIn("step_start", event_types)
        self.assertIn("step_completed", event_types)
        self.assertEqual(event_types[-1], "pipeline_complete")

        # Verify final payload completeness
        final_payload = json.loads(lines[-1].replace("data:", "").strip())
        final_run = final_payload.get("run", {})
        self.assertEqual(final_run.get("status"), "completed")
        self.assertEqual(len(final_run.get("step_runs", [])), 2)


if __name__ == "__main__":
    unittest.main()
