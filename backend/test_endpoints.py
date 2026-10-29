import sys
import json
from fastapi.testclient import TestClient
from app.main import app, agents_db

client = TestClient(app)

def run_tests():
    print("========================================")
    print("Testing Modular Swarm Backend Endpoints")
    print("========================================\n")

    # 1. Test Root
    res = client.get("/")
    assert res.status_code == 200, f"Root failed: {res.status_code}"
    root_data = res.json()
    assert root_data["version"] == "2.0.0"
    assert root_data["agents_count"] >= 6
    print("PASS: GET / ->", root_data)

    # 2. Test Health with 6 Agents
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    health_data = res.json()
    assert health_data["status"] == "ok"
    assert health_data["agents_online"] >= 6
    assert "supabase_configured" in health_data
    expected_agents = ["orchestrator", "researcher", "coder", "reviewer", "data_analyst", "synthesizer"]
    for expected in expected_agents:
        assert expected in health_data["active_agents"], f"Missing agent '{expected}' in health check"
    print("PASS: GET /api/health ->", health_data)

    # 3. Test Agents Roster
    res = client.get("/api/agents")
    assert res.status_code == 200, f"Get agents failed: {res.status_code}"
    agents = res.json()
    assert len(agents) >= 6
    agent_ids = [a["id"] for a in agents]
    for expected in expected_agents:
        assert expected in agent_ids, f"Agent '{expected}' missing from roster"
    print(f"PASS: GET /api/agents -> Found {len(agents)} agents: {agent_ids}")

    # 4. Test Deep Agent Inspection (/api/agents/{agent_id})
    res = client.get("/api/agents/orchestrator")
    assert res.status_code == 200, f"Failed getting orchestrator: {res.status_code}"
    orch = res.json()
    assert orch["id"] == "orchestrator"
    assert orch["is_orchestrator"] is True
    assert len(orch["tools"]) >= 2
    assert len(orch["skills"]) >= 3
    assert len(orch["mcp_servers"]) >= 1
    print(f"PASS: GET /api/agents/orchestrator -> {orch['name']} (tools: {len(orch['tools'])}, skills: {len(orch['skills'])}, mcp: {len(orch['mcp_servers'])})")

    res = client.get("/api/agents/reviewer")
    assert res.status_code == 200
    rev = res.json()
    assert rev["id"] == "reviewer"
    assert len(rev["skills"]) >= 3
    print(f"PASS: GET /api/agents/reviewer -> {rev['name']} (skills: {len(rev['skills'])})")

    res = client.get("/api/agents/nonexistent-agent-id")
    assert res.status_code == 404
    print("PASS: GET /api/agents/nonexistent-agent-id -> 404 Not Found")

    # 5. Test Create Custom Agent
    new_agent = {
        "id": "qa-tester",
        "name": "QA Specialist",
        "role": "Performs integration and automated regression testing",
        "status": "active",
        "model": "gemini-3.8-flash",
        "temperature": 0.1,
        "is_orchestrator": False,
        "system_prompt": "You are a test engineer validating swarm APIs.",
        "tools": [],
        "skills": [],
        "mcp_servers": [],
    }
    res = client.post("/api/agents", json=new_agent)
    assert res.status_code == 200, f"Create agent failed: {res.status_code}"
    created = res.json()
    assert created["id"] == "qa-tester"
    print("PASS: POST /api/agents -> Created custom agent:", created["name"])

    # 6. Test Chat with Auto Routing (Coding query)
    coding_chat = {
        "messages": [
            {
                "role": "user",
                "content": "Can you write a python function to compute factorial?",
                "metadata": {}
            }
        ]
    }
    res = client.post("/api/chat", json=coding_chat)
    assert res.status_code == 200, f"Chat failed: {res.status_code}"
    msg = res.json()
    assert msg["role"] == "agent"
    assert "content" in msg
    assert msg["metadata"]["agent_id"] == "coder"
    print(f"PASS: POST /api/chat (coding intent) -> Routed to {msg['metadata']['agent_id']}")

    # 7. Test Chat with Auto Routing to Reviewer (Security audit query)
    security_chat = {
        "messages": [
            {
                "role": "user",
                "content": "Can you perform a security audit on this code for vulnerabilities?",
                "metadata": {}
            }
        ]
    }
    res = client.post("/api/chat", json=security_chat)
    assert res.status_code == 200
    msg = res.json()
    assert msg["metadata"]["agent_id"] == "reviewer"
    print(f"PASS: POST /api/chat (security audit intent) -> Routed to {msg['metadata']['agent_id']}")

    # 8. Test Chat with Auto Routing to Data Analyst (Statistics query)
    data_chat = {
        "messages": [
            {
                "role": "user",
                "content": "Please calculate the mean, median, and stdev for these statistics",
                "metadata": {}
            }
        ]
    }
    res = client.post("/api/chat", json=data_chat)
    assert res.status_code == 200
    msg = res.json()
    assert msg["metadata"]["agent_id"] == "data_analyst"
    print(f"PASS: POST /api/chat (statistics intent) -> Routed to {msg['metadata']['agent_id']}")

    # 9. Test Chat with Auto Routing to Swarm Orchestrator (Generic inquiry)
    orch_chat = {
        "messages": [
            {
                "role": "user",
                "content": "Hello! Can you help plan our swarm workflow today?",
                "metadata": {}
            }
        ]
    }
    res = client.post("/api/chat", json=orch_chat)
    assert res.status_code == 200
    msg = res.json()
    assert msg["metadata"]["agent_id"] == "orchestrator"
    print(f"PASS: POST /api/chat (generic intent) -> Routed to {msg['metadata']['agent_id']}")

    # 10. Test Chat with Explicit Target Agent ("researcher")
    research_chat = {
        "messages": [
            {
                "role": "user",
                "content": "What is the history of quantum computing?",
                "metadata": {"target_agent_id": "researcher"}
            }
        ]
    }
    res = client.post("/api/chat", json=research_chat)
    assert res.status_code == 200, f"Chat failed: {res.status_code}"
    msg = res.json()
    assert msg["role"] == "agent"
    assert msg["metadata"]["agent_id"] == "researcher"
    print(f"PASS: POST /api/chat (targeted 'researcher') -> Routed to {msg['metadata']['agent_id']}")

    # 11. Test Auth Enforcement on Protected Endpoints
    res = client.get("/api/sessions")
    assert res.status_code == 401, f"Expected 401 unauthorized on /api/sessions without auth, got {res.status_code}"
    print("PASS: GET /api/sessions without auth header returned 401 Unauthorized")

    # 12. Test Session Creation with Authenticated User
    auth_headers = {"Authorization": "Bearer test-user-uuid-1"}
    res = client.get("/api/sessions", headers=auth_headers)
    assert res.status_code == 200, f"Failed listing sessions: {res.status_code}"
    initial_sessions = res.json()
    print(f"PASS: GET /api/sessions (authenticated) -> Initial session count: {len(initial_sessions)}")

    res = client.post("/api/sessions", json={"title": "Test AI Chat Session"}, headers=auth_headers)
    assert res.status_code == 200, f"Failed creating session: {res.status_code}"
    session = res.json()
    assert session["title"] == "Test AI Chat Session"
    assert session["user_id"] == "test-user-uuid-1"
    session_id = session["id"]
    print(f"PASS: POST /api/sessions -> Created session '{session['title']}' (id: {session_id})")

    # 13. Test Session Retrieval
    res = client.get(f"/api/sessions/{session_id}", headers=auth_headers)
    assert res.status_code == 200, f"Failed getting session detail: {res.status_code}"
    detail = res.json()
    assert detail["session"]["id"] == session_id
    assert isinstance(detail["messages"], list)
    print(f"PASS: GET /api/sessions/{session_id} -> Retrieved session with {len(detail['messages'])} messages")

    # 14. Test Session Update (Rename)
    res = client.patch(f"/api/sessions/{session_id}", json={"title": "Renamed AI Session"}, headers=auth_headers)
    assert res.status_code == 200, f"Failed renaming session: {res.status_code}"
    updated_session = res.json()
    assert updated_session["title"] == "Renamed AI Session"
    print("PASS: PATCH /api/sessions/{session_id} -> Successfully updated title to 'Renamed AI Session'")

    # 15. Test Chat Turn Linked to Session (Persisting messages & recording usage)
    session_chat = {
        "session_id": session_id,
        "messages": [
            {
                "role": "user",
                "content": "Can you design a test case for user authentication in Python?",
                "metadata": {"node_id": "user-node-test-1"}
            }
        ]
    }
    res = client.post("/api/chat", json=session_chat, headers=auth_headers)
    assert res.status_code == 200, f"Session chat failed: {res.status_code}"
    agent_msg = res.json()
    assert agent_msg["role"] == "agent"
    assert "tokens_used" in agent_msg["metadata"]
    print(f"PASS: POST /api/chat (with session_id) -> Response returned: tokens={agent_msg['metadata']['tokens_used']}")

    # Verify session detail now contains persisted messages
    res = client.get(f"/api/sessions/{session_id}", headers=auth_headers)
    assert res.status_code == 200
    detail = res.json()
    assert len(detail["messages"]) >= 2
    roles = [m["role"] for m in detail["messages"]]
    assert "user" in roles
    assert "agent" in roles
    print(f"PASS: Session history verified: {len(detail['messages'])} messages stored (user + agent turns)")

    # 16. Test Usage Telemetry Aggregation
    res = client.get("/api/usage", headers=auth_headers)
    assert res.status_code == 200, f"Usage retrieval failed: {res.status_code}"
    usage = res.json()
    assert usage["total_requests"] >= 1
    assert usage["total_tokens"] >= 0
    assert len(usage["recent_activity"]) >= 1
    print(f"PASS: GET /api/usage -> Total tokens: {usage['total_tokens']}, Requests: {usage['total_requests']}")

    # 17. Test Session Deletion
    res = client.delete(f"/api/sessions/{session_id}", headers=auth_headers)
    assert res.status_code == 200, f"Delete session failed: {res.status_code}"
    print(f"PASS: DELETE /api/sessions/{session_id} -> Deleted successfully")

    # Confirm deleted
    res = client.get(f"/api/sessions/{session_id}", headers=auth_headers)
    assert res.status_code == 404, f"Expected 404 for deleted session, got {res.status_code}"
    print("PASS: Verified session is no longer accessible (404)")

    # 18. Test Custom Agent CRUD
    custom_agent_payload = {
        "id": "agent-financial-auditor",
        "name": "Financial Auditor Agent",
        "role": "Financial Forensic Analyst",
        "description": "Reviews financial records and balance sheets for anomalies.",
        "system_prompt": "You are a specialized financial forensic analyst.",
        "model": "gemini-3.8-flash",
        "temperature": 0.2,
        "icon": "ShieldCheck",
        "tools": [{"name": "balance_sheet_evaluator"}],
        "skills": [{"id": "audit_anomaly_detection"}],
        "is_public": False
    }
    res = client.post("/api/custom-agents", json=custom_agent_payload, headers=auth_headers)
    assert res.status_code == 200, f"Create custom agent failed: {res.text}"
    c_agent = res.json()
    assert c_agent["id"] == "agent-financial-auditor"
    print(f"PASS: POST /api/custom-agents -> Created '{c_agent['name']}' (id: {c_agent['id']})")

    res = client.get("/api/custom-agents", headers=auth_headers)
    assert res.status_code == 200
    custom_list = res.json()
    assert any(a["id"] == "agent-financial-auditor" for a in custom_list)
    print(f"PASS: GET /api/custom-agents -> Listed {len(custom_list)} custom agents")

    # 19. Test Script Tool Creation & AST Security Sandbox
    safe_script_code = """
def execute(input_data: dict, context: dict) -> dict:
    text = input_data.get("text", "")
    words = text.split()
    return {
        "word_count": len(words),
        "status": "processed"
    }
"""
    tool_payload = {
        "name": "word_counter_tool",
        "description": "Counts words in input text.",
        "code": safe_script_code,
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}},
        "output_schema": {"type": "object", "properties": {"word_count": {"type": "integer"}}},
        "is_public": False
    }
    res = client.post("/api/workflow-tools", json=tool_payload, headers=auth_headers)
    assert res.status_code == 200, f"Create tool failed: {res.text}"
    created_tool = res.json()
    tool_id = created_tool["id"]
    print(f"PASS: POST /api/workflow-tools -> Created tool '{created_tool['name']}' (id: {tool_id})")

    # Test AST Security sandbox rejection on unsafe code
    unsafe_script_code = """
import os
def execute(input_data: dict, context: dict) -> dict:
    return {"files": os.listdir(".")}
"""
    res = client.post("/api/workflow-tools", json={"name": "unsafe", "code": unsafe_script_code}, headers=auth_headers)
    assert res.status_code == 400, "Expected 400 rejection for unsafe import 'os'"
    print(f"PASS: AST Sandbox accurately rejected unsafe script with 400: {res.json()['detail'][:60]}...")

    # Test tool execution endpoint
    res = client.post(f"/api/workflow-tools/{tool_id}/test", json={"input_data": {"text": "hello swarm autonomous workflow"}, "context": {}}, headers=auth_headers)
    assert res.status_code == 200, f"Tool test failed: {res.text}"
    tool_run_res = res.json()
    assert tool_run_res["status"] == "success"
    assert tool_run_res["result"]["word_count"] == 4
    print(f"PASS: POST /api/workflow-tools/{tool_id}/test -> Output: {tool_run_res['result']} (duration: {tool_run_res['duration_ms']}ms)")

    # 20. Test Workflow Creation with Steps & Edges
    workflow_payload = {
        "title": "Competitor Analysis & Synthesis Pipeline",
        "description": "Gathers competitor intelligence, runs statistical metrics, and synthesizes report.",
        "goal": "Analyze market competitors and produce an executive summary.",
        "visibility": "shared",
        "steps": [
            {
                "id": "step_research",
                "name": "Research Competitors",
                "agent_id": "researcher",
                "instructions": "Investigate key competitors in the domain: {{inputs.domain}}. Goal: {{goal}}",
                "tool_ids": [tool_id],
                "depends_on": []
            },
            {
                "id": "step_synthesize",
                "name": "Synthesize Findings",
                "agent_id": "synthesizer",
                "instructions": "Synthesize the findings from research: {{steps.step_research.output.text}}",
                "tool_ids": [],
                "depends_on": ["step_research"]
            }
        ],
        "edges": [
            {"source": "step_research", "target": "step_synthesize"}
        ]
    }
    res = client.post("/api/workflows", json=workflow_payload, headers=auth_headers)
    assert res.status_code == 200, f"Create workflow failed: {res.text}"
    wf = res.json()
    wf_id = wf["id"]
    share_slug = wf["share_slug"]
    assert len(wf["steps"]) == 2
    assert wf["visibility"] == "shared"
    print(f"PASS: POST /api/workflows -> Created '{wf['title']}' (id: {wf_id}, slug: {share_slug})")

    # Verify immediate retrieval by ID (matches studio loading)
    res_get = client.get(f"/api/workflows/{wf_id}", headers=auth_headers)
    assert res_get.status_code == 200, f"Expected 200 when loading created workflow, got {res_get.status_code}: {res_get.text}"
    assert res_get.json()["id"] == wf_id
    print(f"PASS: GET /api/workflows/{wf_id} -> Successfully loaded newly created workflow")

    # Verify update/save workflow with modified steps
    updated_payload = dict(workflow_payload)
    updated_payload["title"] = "Competitor Analysis & Synthesis Pipeline (Updated)"
    res_put = client.put(f"/api/workflows/{wf_id}", json=updated_payload, headers=auth_headers)
    assert res_put.status_code == 200, f"Expected 200 on workflow save/update, got {res_put.status_code}: {res_put.text}"
    assert res_put.json()["title"] == "Competitor Analysis & Synthesis Pipeline (Updated)"
    print(f"PASS: PUT /api/workflows/{wf_id} -> Successfully updated workflow steps and title")

    # 21. Test Knowledge File Attachment
    knowledge_payload = {
        "file_name": "market_context.md",
        "content_text": "# Market Context\nKey competitor A has 34% market share. Competitor B has 22%.",
        "file_type": "text/markdown"
    }
    res = client.post(f"/api/workflows/{wf_id}/knowledge/upload", json=knowledge_payload, headers=auth_headers)
    assert res.status_code == 200, f"Upload knowledge failed: {res.text}"
    k_doc = res.json()
    assert k_doc["file_name"] == "market_context.md"
    print(f"PASS: POST /api/workflows/{wf_id}/knowledge/upload -> Attached document '{k_doc['file_name']}' ({k_doc['file_size']} bytes)")

    # 22. Test Step Unit Testing in Isolation
    unit_test_payload = {
        "step_id": "step_research",
        "mock_inputs": {"domain": "Autonomous Cloud Agents", "text": "Sample text for word counter"},
        "mock_previous_outputs": {}
    }
    res = client.post(f"/api/workflows/{wf_id}/steps/step_research/test", json=unit_test_payload, headers=auth_headers)
    assert res.status_code == 200, f"Unit test failed: {res.text}"
    unit_res = res.json()
    assert unit_res["status"] == "completed"
    assert unit_res["step_id"] == "step_research"
    assert unit_res["tokens_used"] > 0
    print(f"PASS: POST /api/workflows/{wf_id}/steps/step_research/test -> Unit test passed (tokens: {unit_res['tokens_used']}, latency: {unit_res['duration_ms']}ms)")

    # 23. Test Full Workflow System Execution
    run_payload = {
        "inputs": {"domain": "Cloud Infrastructure AI", "text": "Testing word count string"}
    }
    res = client.post(f"/api/workflows/{wf_id}/run", json=run_payload, headers=auth_headers)
    assert res.status_code == 200, f"Run workflow failed: {res.text}"
    run_res = res.json()
    run_id = run_res["id"]
    assert run_res["status"] == "completed"
    assert len(run_res["step_runs"]) == 2
    assert run_res["total_tokens"] > 0
    print(f"PASS: POST /api/workflows/{wf_id}/run -> System test completed! (run_id: {run_id}, duration: {run_res['duration_ms']}ms, tokens: {run_res['total_tokens']})")

    # Inspect runs endpoint
    res = client.get(f"/api/workflows/{wf_id}/runs", headers=auth_headers)
    assert res.status_code == 200
    runs_list = res.json()
    assert len(runs_list) >= 1
    print(f"PASS: GET /api/workflows/{wf_id}/runs -> Verified {len(runs_list)} historical execution runs")

    # 24. Test Shared Workflow Access & Forking
    # Unauthenticated / different user access to shared slug
    res = client.get(f"/api/workflows/shared/{share_slug}")
    assert res.status_code == 200, f"Shared workflow access failed: {res.text}"
    shared_wf = res.json()
    assert shared_wf["id"] == wf_id
    assert shared_wf["visibility"] in ("shared", "public")
    print(f"PASS: GET /api/workflows/shared/{share_slug} -> View-only shared access confirmed")

    # Unauthorized edit rejection
    other_headers = {"Authorization": "Bearer test-other-user"}
    res = client.put(f"/api/workflows/{wf_id}", json=workflow_payload, headers=other_headers)
    assert res.status_code == 403, f"Expected 403 forbidden for non-owner edit, got {res.status_code}"
    print("PASS: Unauthorized edit on shared workflow rejected with 403 Forbidden")

    # Fork workflow
    res = client.post(f"/api/workflows/{wf_id}/fork", headers=other_headers)
    assert res.status_code == 200, f"Fork failed: {res.text}"
    forked = res.json()
    assert "(Forked)" in forked["title"]
    assert forked["user_id"] == "test-other-user" or "other" in forked["user_id"] or forked["visibility"] == "private"
    print(f"PASS: POST /api/workflows/{wf_id}/fork -> Forked as '{forked['title']}' (id: {forked['id']})")

    # 25. Test Chat Invocation of Autonomous Workflow
    chat_wf_payload = {
        "messages": [{"role": "user", "content": f"/workflow {wf_id}"}],
        "workflow_id": wf_id,
        "workflow_inputs": {"domain": "Enterprise Kubernetes Swarms"}
    }
    res = client.post("/api/chat", json=chat_wf_payload, headers=auth_headers)
    assert res.status_code == 200, f"Chat workflow invocation failed: {res.text}"
    chat_msg = res.json()
    assert chat_msg["metadata"]["mode"] == "workflow_execution"
    assert chat_msg["metadata"]["workflow_id"] == wf_id
    assert len(chat_msg["metadata"]["step_runs"]) == 2
    print(f"PASS: POST /api/chat (workflow invocation) -> Executed workflow, generated progress metadata: {chat_msg['metadata']['agent_name']}")

    # 26. Test Custom Agent Isolated Execution & Testing Playground
    test_agent_payload = {
        "system_prompt": "You are a financial risk analyst specializing in fraud detection.",
        "input_prompt": "Analyze transaction pattern for potential structuring violation.",
        "model": "gemini-3.8-flash",
        "temperature": 0.2,
        "tool_ids": [tool_id]
    }
    res = client.post("/api/custom-agents/test", json=test_agent_payload, headers=auth_headers)
    assert res.status_code == 200, f"Agent test failed: {res.text}"
    agent_test_res = res.json()
    assert agent_test_res["status"] == "success"
    assert len(agent_test_res["content"]) > 0
    assert len(agent_test_res["tool_calls"]) == 1
    print(f"PASS: POST /api/custom-agents/test -> Verified agent isolated test: tokens={agent_test_res['tokens_used']}, latency={agent_test_res['latency_ms']}ms")

    # 27. Test AI Workflow Generator
    ai_wf_payload = {
        "prompt": "Create an automated threat intelligence workflow to audit python packages and generate executive briefing"
    }
    res = client.post("/api/ai/generate-workflow", json=ai_wf_payload, headers=auth_headers)
    assert res.status_code == 200, f"AI workflow generation failed: {res.text}"
    gen_wf = res.json()
    assert "title" in gen_wf and "steps" in gen_wf
    assert len(gen_wf["steps"]) >= 2
    assert len(gen_wf["edges"]) >= 1
    print(f"PASS: POST /api/ai/generate-workflow -> Generated workflow: '{gen_wf['title']}' with {len(gen_wf['steps'])} steps and {len(gen_wf['edges'])} edges")

    # 28. Test AI Agent Generator
    ai_agent_payload = {
        "prompt": "Create a database query optimization expert that inspects EXPLAIN ANALYZE execution plans"
    }
    res = client.post("/api/ai/generate-agent", json=ai_agent_payload, headers=auth_headers)
    assert res.status_code == 200, f"AI agent generation failed: {res.text}"
    gen_agent = res.json()
    assert "name" in gen_agent and "system_prompt" in gen_agent
    assert "optimizer" in gen_agent["name"].lower() or "database" in gen_agent["name"].lower() or "specialist" in gen_agent["name"].lower()
    print(f"PASS: POST /api/ai/generate-agent -> Generated agent: '{gen_agent['name']}' ({gen_agent['id']})")

    # 29. Test Multi-Block Step Unit Tests (Condition, Python Code, Loop, Artifact)
    multi_block_wf_payload = {
        "title": "Autonomous Multi-Block Logic Pipeline",
        "description": "Pipeline verifying Condition, Python Code, Loop, and Artifact blocks",
        "goal": "Process data, branch on threshold, and produce artifact report",
        "steps": [
            {
                "id": "step_code",
                "name": "Data Transform Script",
                "step_type": "python_code",
                "code": "def execute(inputs, previous_outputs, context):\n    v = inputs.get('count', 10)\n    return {'score': v * 5, 'status': 'computed'}",
                "depends_on": [],
            },
            {
                "id": "step_cond",
                "name": "Score Threshold Check",
                "step_type": "condition",
                "condition_expr": "{{steps.step_code.output.score}} >= 50",
                "true_target_step_id": "step_artifact",
                "false_target_step_id": "step_code",
                "depends_on": ["step_code"],
            },
            {
                "id": "step_loop",
                "name": "Quality Retry Loop",
                "step_type": "loop",
                "condition_expr": "{{inputs.retry_needed}} == true",
                "loop_target_step_id": "step_code",
                "max_loop_iterations": 2,
                "depends_on": ["step_cond"],
            },
            {
                "id": "step_artifact",
                "name": "Executive Summary Artifact",
                "step_type": "artifact",
                "artifact_title": "Pipeline Execution Briefing",
                "artifact_type": "markdown",
                "instructions": "# Executive Report\nGoal: {{goal}}\nComputed Score: {{steps.step_code.output.score}}\nResult: Approved",
                "depends_on": ["step_cond"],
            }
        ],
        "edges": [
            {"id": "e1", "source": "step_code", "target": "step_cond"},
            {"id": "e2", "source": "step_cond", "target": "step_artifact"},
        ]
    }
    res = client.post("/api/workflows", json=multi_block_wf_payload, headers=auth_headers)
    assert res.status_code == 200, f"Failed to create multi-block workflow: {res.text}"
    mb_wf = res.json()
    mb_wf_id = mb_wf["id"]

    # 29a. Unit test Python Code step
    res_code = client.post(
        f"/api/workflows/{mb_wf_id}/steps/step_code/test",
        json={"step_id": "step_code", "mock_inputs": {"count": 12}, "mock_previous_outputs": {}},
        headers=auth_headers,
    )
    assert res_code.status_code == 200, f"Python code step test failed: {res_code.text}"
    res_code_data = res_code.json()
    assert res_code_data["status"] == "completed"
    assert res_code_data["output_data"]["score"] == 60

    # 29b. Unit test Condition step
    res_cond = client.post(
        f"/api/workflows/{mb_wf_id}/steps/step_cond/test",
        json={"step_id": "step_cond", "mock_inputs": {}, "mock_previous_outputs": {"step_code": {"score": 60}}},
        headers=auth_headers,
    )
    assert res_cond.status_code == 200, f"Condition step test failed: {res_cond.text}"
    res_cond_data = res_cond.json()
    assert res_cond_data["status"] == "completed"
    assert res_cond_data["output_data"]["condition"] is True
    assert res_cond_data["output_data"]["branch"] == "true"

    # 29c. Unit test Artifact step
    res_art = client.post(
        f"/api/workflows/{mb_wf_id}/steps/step_artifact/test",
        json={"step_id": "step_artifact", "mock_inputs": {}, "mock_previous_outputs": {"step_code": {"score": 60}}},
        headers=auth_headers,
    )
    assert res_art.status_code == 200, f"Artifact step test failed: {res_art.text}"
    res_art_data = res_art.json()
    assert res_art_data["status"] == "completed"
    assert "artifact" in res_art_data["output_data"]
    assert "Computed Score: 60" in res_art_data["output_data"]["artifact"]["content"]
    print(f"PASS: Multi-block unit tests verified (Python Code, Condition True branch, Artifact generation)")

    # 30. Test Multi-Block End-to-End Workflow Execution
    res_run = client.post(
        f"/api/workflows/{mb_wf_id}/run",
        json={"inputs": {"count": 14, "retry_needed": False}},
        headers=auth_headers,
    )
    assert res_run.status_code == 200, f"Multi-block workflow run failed: {res_run.text}"
    run_data = res_run.json()
    assert run_data["status"] == "completed"
    assert "artifacts" in run_data and len(run_data["artifacts"]) == 1
    assert run_data["artifacts"][0]["title"] == "Pipeline Execution Briefing"
    assert len(run_data["step_runs"]) >= 3
    print(f"PASS: POST /api/workflows/{mb_wf_id}/run -> Successfully executed multi-block pipeline end-to-end with 1 persistent artifact generated")

    # 31. Test Real Web Search Tool Execution
    from app.agents.researcher.tools import web_search_query, extract_citations
    search_res = web_search_query("FastAPI Python web framework", max_results=3)
    assert search_res["status"] == "completed"
    assert search_res["results_count"] > 0
    assert len(search_res["sources"]) > 0
    cited = extract_citations("According to https://fastapi.tiangolo.com and https://docs.python.org, performance is high.")
    assert len(cited) == 2
    assert "https://fastapi.tiangolo.com" in cited
    print(f"PASS: Real web search query executed successfully with {search_res['results_count']} live sources and URL citations")

    # 32. Test Base Conversational Agent & Latest Model Selection (Gemini 3.8 Flash & Normalization)
    res_conv = client.post(
        "/api/chat",
        json={
            "messages": [{"role": "user", "content": "Hello! How are you doing today?"}],
            "model": "gemini-3.8-flash",
        },
        headers=auth_headers,
    )
    assert res_conv.status_code == 200, f"Conversational chat turn failed: {res_conv.text}"
    conv_data = res_conv.json()
    assert conv_data["metadata"]["agent_id"] == "general_assistant"
    assert conv_data["metadata"]["model"] == "gemini-3.8-flash"
    print(f"PASS: Conversational routing routed to 'general_assistant' with custom model selection: {conv_data['metadata']['model']}")

    # 32b. Test Legacy Deprecated Model Auto-Normalization (gemini-2.5-flash -> gemini-3.8-flash)
    res_legacy = client.post(
        "/api/chat",
        json={
            "messages": [{"role": "user", "content": "Tell me a joke."}],
            "model": "gemini-2.5-flash",
        },
        headers=auth_headers,
    )
    assert res_legacy.status_code == 200, f"Legacy model chat failed: {res_legacy.text}"
    legacy_data = res_legacy.json()
    assert legacy_data["metadata"]["model"] == "gemini-3.8-flash"
    print(f"PASS: Legacy model 'gemini-2.5-flash' normalized gracefully to '{legacy_data['metadata']['model']}'")

    # 33. Test Custom Agent Update (PUT /api/custom-agents/{id})
    res_update = client.put(
        "/api/custom-agents/agent-financial-auditor",
        json={
            "id": "agent-financial-auditor",
            "name": "Senior Financial Auditor Agent",
            "role": "Lead Audit & Risk Specialist",
            "description": "Performs institutional compliance and risk audits.",
            "system_prompt": "You are a Senior Risk Auditor. Provide strict quantitative rigor.",
            "model": "sonar-pro",
            "temperature": 0.1,
            "icon": "ShieldCheck",
        },
        headers=auth_headers,
    )
    assert res_update.status_code == 200, f"Custom agent update failed: {res_update.text}"
    updated_data = res_update.json()
    assert updated_data["name"] == "Senior Financial Auditor Agent"
    assert updated_data["model"] == "sonar-pro"
    assert updated_data["temperature"] == 0.1
    print(f"PASS: PUT /api/custom-agents/agent-financial-auditor updated model to {updated_data['model']} and name to '{updated_data['name']}'")

    # 34. Test AI Workflow Generator with Multi-Block Archetype (Code Review & Condition)
    refactor_wf_payload = {
        "prompt": "Create an automated code review and refactor pipeline that checks code quality and produces a pull request report"
    }
    res_ai_wf = client.post("/api/ai/generate-workflow", json=refactor_wf_payload, headers=auth_headers)
    assert res_ai_wf.status_code == 200, f"AI multi-block workflow generation failed: {res_ai_wf.text}"
    refactor_wf = res_ai_wf.json()
    assert "title" in refactor_wf and "steps" in refactor_wf
    assert any(s.get("step_type") in ("condition", "artifact") for s in refactor_wf["steps"]), "Expected condition or artifact step in generated DAG"
    print(f"PASS: POST /api/ai/generate-workflow (multi-block) -> Generated '{refactor_wf['title']}' with {len(refactor_wf['steps'])} steps including specialized block types")

    # 35. Test Researcher Agent Default Model is Sonar (Perplexity)
    res_researcher = client.get("/api/agents/researcher")
    assert res_researcher.status_code == 200, f"Failed to get researcher agent: {res_researcher.text}"
    researcher_data = res_researcher.json()
    assert researcher_data["model"] == "sonar", f"Expected model 'sonar', got '{researcher_data.get('model')}'"
    print(f"PASS: GET /api/agents/researcher confirmed default model is '{researcher_data['model']}' (Perplexity)")

    # 36. Test Contextual Auto-Titling on POST /api/sessions with prompt
    res_context_sess = client.post(
        "/api/sessions",
        json={"prompt": "Can you please help me write a Python script for PostgreSQL index tuning?"},
        headers=auth_headers,
    )
    assert res_context_sess.status_code == 200, f"Context session creation failed: {res_context_sess.text}"
    ctx_sess_data = res_context_sess.json()
    assert "PostgreSQL" in ctx_sess_data["title"] or "Index Tuning" in ctx_sess_data["title"], f"Unexpected title: {ctx_sess_data['title']}"
    assert ctx_sess_data["title"] != "New Conversation", f"Title should not be generic: {ctx_sess_data['title']}"
    print(f"PASS: POST /api/sessions with prompt automatically derived contextual title: '{ctx_sess_data['title']}'")

    # 37. Test Automatic Session Renaming during First Chat Turn on Generic Session
    res_generic_sess = client.post("/api/sessions", json={"title": "New Conversation"}, headers=auth_headers)
    assert res_generic_sess.status_code == 200
    gen_sess_id = res_generic_sess.json()["id"]

    chat_turn_payload = {
        "session_id": gen_sess_id,
        "messages": [
            {"role": "user", "content": "Explain quantum entanglement and photon polarization in simple terms"}
        ]
    }
    res_chat_turn = client.post("/api/chat", json=chat_turn_payload, headers=auth_headers)
    assert res_chat_turn.status_code == 200, f"Chat turn failed: {res_chat_turn.text}"
    msg_metadata = res_chat_turn.json().get("metadata", {})
    assert "session_title" in msg_metadata, f"Expected session_title in metadata: {msg_metadata}"
    assert "Quantum" in msg_metadata["session_title"], f"Expected 'Quantum' in title: {msg_metadata['session_title']}"

    # Verify session detail reflects the updated title
    res_detail = client.get(f"/api/sessions/{gen_sess_id}", headers=auth_headers)
    assert res_detail.status_code == 200
    saved_title = res_detail.json()["session"]["title"]
    assert "Quantum" in saved_title, f"Saved session title was not updated: {saved_title}"
    print(f"PASS: POST /api/chat automatically renamed generic session to: '{saved_title}'")

    # 38. Test File Creator Agent Routing and Artifact Generation
    res_file_create = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "Generate file for customer data pipeline in python"}]},
        headers=auth_headers
    )
    assert res_file_create.status_code == 200, f"File creation chat failed: {res_file_create.text}"
    fc_meta = res_file_create.json().get("metadata", {})
    assert fc_meta.get("agent_id") == "file_creator", f"Expected routing to file_creator, got {fc_meta.get('agent_id')}"
    assert "file_artifact" in fc_meta or "artifacts" in fc_meta, f"Expected file artifact in metadata: {fc_meta}"
    print(f"PASS: POST /api/chat routed to file_creator and generated downloadable file artifact: '{fc_meta.get('file_artifact', {}).get('filename')}'")

    # 39. Test File Parser Agent Routing
    res_file_parse = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "Parse file logs and extract schema diagnostics"}]},
        headers=auth_headers
    )
    assert res_file_parse.status_code == 200, f"File parser chat failed: {res_file_parse.text}"
    fp_meta = res_file_parse.json().get("metadata", {})
    assert fp_meta.get("agent_id") == "file_parser", f"Expected routing to file_parser, got {fp_meta.get('agent_id')}"
    print(f"PASS: POST /api/chat routed to file_parser for schema and document inspection")

    # 40. Test Artifacts API (POST, GET, DELETE /api/artifacts)
    art_payload = {
        "name": "sales_projection_q4.csv",
        "type": "csv",
        "content": "month,revenue,profit\nOct,12000,3400\nNov,15000,4200\nDec,22000,7100\n",
        "origin_agent": "file_creator",
        "source_type": "chat"
    }
    res_post_art = client.post("/api/artifacts", json=art_payload, headers=auth_headers)
    assert res_post_art.status_code == 200, f"Failed to create artifact: {res_post_art.text}"
    created_art = res_post_art.json()
    assert created_art["name"] == "sales_projection_q4.csv"
    art_id = created_art["id"]

    res_list_art = client.get("/api/artifacts", headers=auth_headers)
    assert res_list_art.status_code == 200
    all_arts = res_list_art.json()
    assert any(a["id"] == art_id for a in all_arts), "Created artifact not found in artifacts list"

    res_del_art = client.delete(f"/api/artifacts/{art_id}", headers=auth_headers)
    assert res_del_art.status_code == 200
    print(f"PASS: /api/artifacts endpoints verified: created, listed ({len(all_arts)} items), and deleted artifact '{art_id}'")

    # 41. Test Routing for Live Stock Prices & Web Search -> researcher with 'sonar'
    res_stock = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "What is the current stock price and ticker quote for AAPL?"}]},
        headers=auth_headers
    )
    assert res_stock.status_code == 200, f"Stock price chat failed: {res_stock.text}"
    stock_meta = res_stock.json().get("metadata", {})
    assert stock_meta.get("agent_id") == "researcher", f"Expected routing to researcher, got {stock_meta.get('agent_id')}"
    print(f"PASS: Live stock price query correctly routed to researcher with Perplexity Sonar")

    # 42. Test Workflow Step Execution with Perplexity Sonar for Web Search & Live Info
    stock_wf_payload = {
        "title": "Real-Time Stock Market Intelligence DAG",
        "description": "Scrapes and evaluates live equity prices using Perplexity Sonar",
        "goal": "Retrieve live stock quotes and market telemetry",
        "steps": [
            {
                "id": "step_live_stock",
                "name": "Live Stock Price Discovery",
                "step_type": "agent",
                "agent_id": "researcher",
                "model": "sonar",
                "instructions": "Extract live market prices and volume for {{inputs.query}}",
                "depends_on": []
            }
        ],
        "edges": []
    }
    res_stock_wf = client.post("/api/workflows", json=stock_wf_payload, headers=auth_headers)
    assert res_stock_wf.status_code == 200
    s_wf_id = res_stock_wf.json()["id"]

    res_step_test = client.post(
        f"/api/workflows/{s_wf_id}/steps/step_live_stock/test",
        json={"step_id": "step_live_stock", "mock_inputs": {"query": "NVDA stock price"}},
        headers=auth_headers
    )
    assert res_step_test.status_code == 200, f"Workflow Perplexity step test failed: {res_step_test.text}"
    step_out = res_step_test.json()
    assert step_out["status"] == "completed"
    assert "Perplexity Sonar Web Search" in step_out["output_data"]["text"], "Expected Perplexity Sonar execution in step output"
    print(f"PASS: Workflow execution engine executed live information step using Perplexity Sonar")

    # 43. Test Direct Agent Tool Execution Across Multiple Agents
    res_coder_tool = client.post(
        "/api/agents/coder/tools/syntax_validator/execute",
        json={"arguments": {"code": "def hello():\n    return 'world'\n", "language": "python"}},
    )
    assert res_coder_tool.status_code == 200, f"Coder tool execution failed: {res_coder_tool.text}"
    coder_out = res_coder_tool.json()
    assert coder_out["status"] == "success"
    assert coder_out["result"]["valid"] is True

    res_sandbox = client.post(
        "/api/agents/coder/tools/execute_python_sandbox/execute",
        json={"arguments": {"code": "x = [1, 2, 3]\nprint(sum(x))"}},
    )
    assert res_sandbox.status_code == 200
    assert "6" in res_sandbox.json()["result"]["output"]

    res_analyst_tool = client.post(
        "/api/agents/data_analyst/tools/calculate_statistics/execute",
        json={"arguments": {"numbers": [10.0, 20.0, 30.0, 40.0, 50.0]}},
    )
    assert res_analyst_tool.status_code == 200
    assert res_analyst_tool.json()["result"]["mean"] == 30.0

    res_synth_tool = client.post(
        "/api/agents/synthesizer/tools/create_table_of_contents/execute",
        json={"arguments": {"markdown_content": "# Intro\nText\n## Setup\nText\n### Verification\nText"}},
    )
    assert res_synth_tool.status_code == 200
    assert res_synth_tool.json()["result"]["headers_found"] == 3

    res_creator_tool = client.post(
        "/api/agents/file_creator/tools/generate_file_artifact/execute",
        json={"arguments": {"filename": "test_output.json", "content": '{"test": 123}', "mime_type": "application/json"}},
    )
    assert res_creator_tool.status_code == 200
    assert res_creator_tool.json()["result"]["status"] == "created"
    print("PASS: POST /api/agents/{agent_id}/tools/{tool_name}/execute verified across coder, data_analyst, synthesizer, and file_creator")

    # 44. Test Agent MCP Tool Execution
    res_mcp_fs = client.post(
        "/api/agents/coder/mcp/filesystem/tools/list_directory/execute",
        json={"arguments": {"path": "."}},
    )
    assert res_mcp_fs.status_code == 200, f"MCP filesystem execution failed: {res_mcp_fs.text}"
    mcp_fs_data = res_mcp_fs.json()
    assert mcp_fs_data["server"] == "filesystem"
    assert mcp_fs_data["isError"] is False
    assert mcp_fs_data["data"]["count"] > 0

    res_mcp_gateway = client.post(
        "/api/agents/orchestrator/mcp/swarm-gateway/tools/list_agents/execute",
        json={"arguments": {}},
    )
    assert res_mcp_gateway.status_code == 200
    assert res_mcp_gateway.json()["data"]["active_agents_count"] >= 9

    res_mcp_kb = client.post(
        "/api/agents/general_assistant/mcp/knowledge-base/tools/list_topics/execute",
        json={"arguments": {}},
    )
    assert res_mcp_kb.status_code == 200
    assert res_mcp_kb.json()["data"]["count"] >= 2
    print("PASS: POST /api/agents/{agent_id}/mcp/{server_name}/tools/{tool_name}/execute verified across filesystem, swarm-gateway, and knowledge-base")

    # 45. Test Global MCP Server Listing and Direct Dispatcher
    res_mcp_servers = client.get("/api/mcp/servers")
    assert res_mcp_servers.status_code == 200
    servers_list = res_mcp_servers.json()
    assert len(servers_list) >= 12
    server_names = [s["name"] for s in servers_list]
    assert "filesystem" in server_names
    assert "sqlite-analytics" in server_names
    assert "knowledge-base" in server_names
    assert "swarm-gateway" in server_names

    res_direct_mcp = client.post(
        "/api/mcp/execute",
        json={
            "server": "sqlite-analytics",
            "tool": "read_query",
            "arguments": {"query": "SELECT metric_name, value FROM metrics WHERE id = 1"},
        },
    )
    assert res_direct_mcp.status_code == 200
    direct_data = res_direct_mcp.json()
    assert direct_data["isError"] is False
    assert len(direct_data["data"]["rows"]) == 1
    assert direct_data["data"]["rows"][0][0] == "api_latency_ms"
    print(f"PASS: GET /api/mcp/servers listed {len(servers_list)} servers and POST /api/mcp/execute executed sqlite-analytics query directly")

    # 46. Test Agent Tool & MCP Error Handling
    res_bad_tool = client.post(
        "/api/agents/coder/tools/non_existent_tool/execute",
        json={"arguments": {}},
    )
    assert res_bad_tool.status_code == 400

    res_unauth_mcp = client.post(
        "/api/agents/coder/mcp/postgres/tools/query/execute",
        json={"arguments": {"sql": "SELECT 1"}},
    )
    assert res_unauth_mcp.status_code == 200
    assert res_unauth_mcp.json()["isError"] is True
    print("PASS: Agent Tool & MCP security boundaries accurately reject invalid tools and unconfigured servers")

    # 47. Test Default Workflow Templates Endpoint
    res_defaults = client.get("/api/workflows/defaults")
    assert res_defaults.status_code == 200, f"Default workflows endpoint failed: {res_defaults.text}"
    default_wfs = res_defaults.json()
    assert len(default_wfs) >= 1, f"Expected at least 1 default workflow, got {len(default_wfs)}"
    research_wf = default_wfs[0]
    assert research_wf["id"] in ("0193e182-5af1-5bf1-bfe2-970663d16eb8", "default-wf-research-pipeline")
    assert research_wf["visibility"] == "public"
    assert research_wf["share_slug"] == "default-research-pipeline"
    assert len(research_wf["steps"]) == 8
    assert len(research_wf["edges"]) == 8
    step_types = {s["step_type"] for s in research_wf["steps"]}
    assert step_types == {"agent", "python_code", "condition", "loop", "artifact"}, f"Expected all 5 step types, got {step_types}"
    agent_ids = {s["agent_id"] for s in research_wf["steps"] if s["step_type"] == "agent"}
    assert len(agent_ids) >= 4, f"Expected 4+ unique agents, got {agent_ids}"
    print(f"PASS: GET /api/workflows/defaults -> {len(default_wfs)} template(s), '{research_wf['title']}' with {len(research_wf['steps'])} steps, all 5 block types present")

    # 48. Test Default Workflow Is Seeded and Accessible via Regular Workflow List
    res_wf_list = client.get("/api/workflows", headers=auth_headers)
    assert res_wf_list.status_code == 200
    wf_list = res_wf_list.json()
    default_in_list = [w for w in wf_list if w.get("share_slug") == "default-research-pipeline" or w.get("id") in ("0193e182-5af1-5bf1-bfe2-970663d16eb8", "default-wf-research-pipeline")]
    assert len(default_in_list) >= 1, "Default workflow not found in regular workflow list"
    assert default_in_list[0]["visibility"] == "public"
    print("PASS: Default workflow is seeded at startup and visible in GET /api/workflows list")

    # 49. Test Default Workflow Individual Step Unit Tests
    default_wf_id = research_wf["id"]

    # 49a. Unit test Python Code scoring step
    res_ut_score = client.post(
        f"/api/workflows/{default_wf_id}/steps/step_score/test",
        json={
            "step_id": "step_score",
            "mock_inputs": {"topic": "Cloud Computing"},
            "mock_previous_outputs": {
                "step_research": {"text": "Cloud computing market reached $500B in 2025. Sources: https://gartner.com and https://aws.amazon.com provide comprehensive analysis of IaaS, PaaS, SaaS segments."}
            }
        },
        headers=auth_headers,
    )
    assert res_ut_score.status_code == 200, f"Scoring step test failed: {res_ut_score.text}"
    score_data = res_ut_score.json()
    assert score_data["status"] == "completed"
    assert score_data["output_data"]["score"] >= 40, f"Score too low: {score_data['output_data']['score']}"
    assert score_data["output_data"]["has_sources"] is True
    assert score_data["output_data"]["has_data_points"] is True
    print(f"PASS: Default workflow step_score unit test -> score={score_data['output_data']['score']}, quality={score_data['output_data']['quality']}")

    # 49b. Unit test Condition gate step (should pass with score >= 40)
    res_ut_gate = client.post(
        f"/api/workflows/{default_wf_id}/steps/step_quality_gate/test",
        json={
            "step_id": "step_quality_gate",
            "mock_inputs": {},
            "mock_previous_outputs": {"step_score": {"score": 75, "quality": "high"}}
        },
        headers=auth_headers,
    )
    assert res_ut_gate.status_code == 200, f"Condition gate test failed: {res_ut_gate.text}"
    gate_data = res_ut_gate.json()
    assert gate_data["status"] == "completed"
    assert gate_data["output_data"]["condition"] is True
    assert gate_data["output_data"]["branch"] == "true"
    assert gate_data["output_data"]["target_step"] == "step_analysis"
    print("PASS: Default workflow step_quality_gate unit test -> condition=True, target=step_analysis")

    # 49c. Unit test Artifact report step
    res_ut_art = client.post(
        f"/api/workflows/{default_wf_id}/steps/step_report/test",
        json={
            "step_id": "step_report",
            "mock_inputs": {"topic": "Edge Computing"},
            "mock_previous_outputs": {
                "step_research": {"text": "Edge computing enables low-latency processing."},
                "step_score": {"score": 82, "quality": "high", "word_count": 50},
                "step_analysis": {"text": "Market growing at 22% CAGR."},
                "step_implementation": {"text": "Deploy via Kubernetes edge nodes."},
                "step_review": {"text": "No critical vulnerabilities found."},
            }
        },
        headers=auth_headers,
    )
    assert res_ut_art.status_code == 200, f"Artifact step test failed: {res_ut_art.text}"
    art_data = res_ut_art.json()
    assert art_data["status"] == "completed"
    assert "artifact" in art_data["output_data"]
    assert art_data["output_data"]["artifact"]["title"] == "Competitive Research Report"
    assert "Edge Computing" in art_data["output_data"]["artifact"]["content"]
    assert "Score: 82/100" in art_data["output_data"]["artifact"]["content"]
    print("PASS: Default workflow step_report artifact unit test -> generated report with interpolated content")

    # 50. Test Default Workflow End-to-End Execution
    res_e2e = client.post(
        f"/api/workflows/{default_wf_id}/run",
        json={"inputs": {"topic": "Kubernetes Autoscaling Strategies"}},
        headers=auth_headers,
    )
    assert res_e2e.status_code == 200, f"Default workflow E2E run failed: {res_e2e.text}"
    e2e_data = res_e2e.json()
    assert e2e_data["status"] == "completed", f"Workflow did not complete: {e2e_data.get('error')}"
    assert len(e2e_data["step_runs"]) >= 6, f"Expected 6+ step runs, got {len(e2e_data['step_runs'])}"
    assert len(e2e_data["artifacts"]) == 1, f"Expected 1 artifact, got {len(e2e_data.get('artifacts', []))}"
    assert e2e_data["artifacts"][0]["title"] == "Competitive Research Report"
    assert e2e_data["total_tokens"] > 0
    step_ids_executed = [sr["step_id"] for sr in e2e_data["step_runs"]]
    assert "step_research" in step_ids_executed
    assert "step_score" in step_ids_executed
    assert "step_quality_gate" in step_ids_executed
    assert "step_report" in step_ids_executed
    print(f"PASS: Default workflow E2E execution completed with {len(e2e_data['step_runs'])} step runs, {len(e2e_data['artifacts'])} artifact(s), {e2e_data['total_tokens']} tokens")

    # 51. Test Agent Playground Execution With Minimal Payload (agent_id + prompt)
    playground_payload = {
        "agent_id": "file_creator",
        "prompt": "generate a sample csv file",
        "inputs": {},
        "mock_variables": {}
    }
    res_pg = client.post("/api/custom-agents/test", json=playground_payload, headers=auth_headers)
    assert res_pg.status_code == 200, f"Agent playground test failed: {res_pg.text}"
    pg_data = res_pg.json()
    assert pg_data["status"] == "success"
    assert "response" in pg_data and len(pg_data["response"]) > 0
    assert "content" in pg_data and len(pg_data["content"]) > 0
    assert "duration_ms" in pg_data
    assert pg_data["agent_id"] == "file_creator"
    print(f"PASS: POST /api/custom-agents/test -> Executed playground test with agent_id & prompt successfully: tokens={pg_data['tokens_used']}")

    # 52. Test Public / Guest Access to GET /api/workflows Returns Default Workflows
    res_guest_wf = client.get("/api/workflows")
    assert res_guest_wf.status_code == 200, f"Guest workflows access failed: {res_guest_wf.text}"
    guest_wfs = res_guest_wf.json()
    assert any(w.get("share_slug") == "default-research-pipeline" or w.get("id") in ("0193e182-5af1-5bf1-bfe2-970663d16eb8", "default-wf-research-pipeline") for w in guest_wfs), "Default workflow missing in guest list"
    print(f"PASS: GET /api/workflows without auth header returned {len(guest_wfs)} public workflow(s) including default template")

    # 53. Test File Creator Agent Routing and CSV Artifact Emission
    res_chat_csv = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "generate a sample csv file"}]},
        headers=auth_headers,
    )
    assert res_chat_csv.status_code == 200, f"Chat CSV generation failed: {res_chat_csv.text}"
    chat_csv_data = res_chat_csv.json()
    meta = chat_csv_data.get("metadata", {})
    assert meta.get("agent_id") == "file_creator", f"Expected routing to 'file_creator', got '{meta.get('agent_id')}'"
    assert "file_artifact" in meta and meta["file_artifact"] is not None, "Expected 'file_artifact' in chat metadata"
    artifact = meta["file_artifact"]
    assert artifact.get("type") == "csv", f"Expected artifact type 'csv', got '{artifact.get('type')}'"
    assert artifact.get("downloadable") is True
    assert artifact.get("filename", "").endswith(".csv")
    assert "content" in artifact and len(artifact["content"]) > 0
    assert "artifacts" in meta and len(meta["artifacts"]) > 0
    print(f"PASS: POST /api/chat 'generate a sample csv file' routed to file_creator with downloadable CSV artifact: '{artifact.get('filename')}' ({artifact.get('size_bytes')} bytes)")

    # 54. Test extract_file_artifact_from_turn Robustness (CRLF, trailing whitespace, plain CSV)
    from app.main import extract_file_artifact_from_turn
    # CRLF with language
    crlf_sample = "### Generated File\r\n```csv\r\nid,metric,value\r\n1,latency,12ms\r\n2,throughput,4500\r\n```\r\n"
    art_crlf = extract_file_artifact_from_turn(crlf_sample, "file_creator", "generate a sample csv file")
    assert art_crlf is not None and art_crlf["type"] == "csv", f"CRLF extraction failed: {art_crlf}"
    # Trailing whitespace on language fence
    space_sample = "Here is the dataset:\n```csv   \nname,score\nalice,98\nbob,92\n```"
    art_space = extract_file_artifact_from_turn(space_sample, "data_analyst", "export dataset csv")
    assert art_space is not None and art_space["type"] == "csv", f"Trailing space extraction failed: {art_space}"
    # Plain CSV without code block for file_creator
    plain_sample = "id,name,role\n1,Alex,Architect\n2,Jordan,Lead\n"
    art_plain = extract_file_artifact_from_turn(plain_sample, "file_creator", "generate csv file")
    assert art_plain is not None and art_plain["type"] == "csv", f"Plain text CSV extraction failed: {art_plain}"
    print("PASS: extract_file_artifact_from_turn verified robust across CRLF, trailing whitespace, and tabular plain text")

    # 55. Test Groq Model Normalizer & Model Candidates
    from app.main import normalize_model_name
    from app.groq_client import resolve_groq_model_candidates, DEFAULT_GROQ_MODEL
    assert normalize_model_name("qwen-3.8") == "qwen-3.8"
    assert normalize_model_name("qwen") == "qwen-3.8"
    assert normalize_model_name(None) == "qwen-3.8"
    assert normalize_model_name("") == "qwen-3.8"
    assert normalize_model_name("sonar") == "sonar"
    assert normalize_model_name("gemini-2.5-flash") == "gemini-3.8-flash"
    assert normalize_model_name("gemini-2.5-pro") == "gemini-4-argon"

    groq_candidates = resolve_groq_model_candidates("qwen-3.8")
    assert len(groq_candidates) > 0
    assert any("qwen" in c.lower() for c in groq_candidates)
    assert DEFAULT_GROQ_MODEL == "qwen-3.8"
    print(f"PASS: Groq model normalization verified: default={DEFAULT_GROQ_MODEL}, candidates count={len(groq_candidates)}")

    # 56. Test Site-wide Prebuilt Agent Models & Default Workflow Perplexity Research Step
    res_fc = client.get("/api/agents/file_creator")
    assert res_fc.status_code == 200
    assert res_fc.json()["model"] == "qwen-3.8", f"Expected file_creator model 'qwen-3.8', got '{res_fc.json().get('model')}'"

    res_orch = client.get("/api/agents/orchestrator")
    assert res_orch.status_code == 200
    assert res_orch.json()["model"] == "qwen-3.8", f"Expected orchestrator model 'qwen-3.8', got '{res_orch.json().get('model')}'"

    res_res = client.get("/api/agents/researcher")
    assert res_res.status_code == 200
    assert res_res.json()["model"] == "sonar", f"Expected researcher model 'sonar', got '{res_res.json().get('model')}'"

    res_defaults = client.get("/api/workflows/defaults")
    assert res_defaults.status_code == 200
    wf_tmpl = res_defaults.json()[0]
    step_research = next((s for s in wf_tmpl["steps"] if s["id"] == "step_research"), None)
    assert step_research is not None, "Missing step_research in default workflow template"
    assert step_research["model"] == "sonar", f"Expected step_research model 'sonar', got '{step_research.get('model')}'"
    assert step_research["agent_id"] == "researcher"
    print(f"PASS: Site-wide models verified: Groq Qwen 3.8 default across agents, Perplexity Sonar on researcher and default workflow step")

    # 57. Test Artifacts Persistence, Extraction & Studio Listing
    test_art_payload = {
        "id": "art-test-studio-01",
        "name": "system_metrics.json",
        "filename": "system_metrics.json",
        "type": "json",
        "content": '{"uptime_pct": 99.98, "rps": 4200}',
        "origin_agent": "file_creator",
    }
    res_create_art = client.post("/api/artifacts", json=test_art_payload, headers=auth_headers)
    assert res_create_art.status_code == 200, f"Artifact create failed: {res_create_art.text}"
    created_art = res_create_art.json()
    assert created_art["id"] == "art-test-studio-01"
    assert created_art["downloadable"] is True

    res_get_arts = client.get("/api/artifacts", headers=auth_headers)
    assert res_get_arts.status_code == 200
    arts_list = res_get_arts.json()
    art_ids = [a["id"] for a in arts_list]
    assert "art-test-studio-01" in art_ids, f"Created artifact not found in listing: {art_ids}"

    # Verify deletion
    res_del_art = client.delete("/api/artifacts/art-test-studio-01", headers=auth_headers)
    assert res_del_art.status_code == 200
    res_get_after = client.get("/api/artifacts", headers=auth_headers)
    assert "art-test-studio-01" not in [a["id"] for a in res_get_after.json()]
    print("PASS: /api/artifacts POST, GET, and DELETE lifecycle verified for Artifacts Studio")

    # 58. Test Binary Document Generation Tooling (PDF, PPTX, DOCX, XLSX)
    from app.agents.file_creator.tools import (
        generate_pdf_document,
        generate_presentation_deck,
        generate_word_document,
        generate_spreadsheet_workbook,
    )
    # PDF
    pdf_out = generate_pdf_document(
        title="Autonomous Swarm Research Report",
        subtitle="Quarterly Multi-Agent Intelligence Briefing",
        sections=[
            {"heading": "Executive Summary", "content": "Autonomous agent swarms demonstrate 4x throughput."},
            {"heading": "Performance Metrics", "bullets": ["Latency: 12ms", "Accuracy: 99.4%"]}
        ],
        tables=[{"headers": ["Agent", "Status"], "rows": [["Coder", "Active"], ["Researcher", "Active"]]}],
        filename="swarm_briefing.pdf"
    )
    assert pdf_out["status"] == "created"
    assert pdf_out["file_type"] == "pdf"
    assert pdf_out["is_base64"] is True
    assert len(pdf_out["content"]) > 500

    # PPTX
    pptx_out = generate_presentation_deck(
        title="Q3 Strategy Presentation",
        subtitle="Swarm Architecture & Scaling",
        slides=[
            {"title": "Core Milestones", "bullet_points": ["Milestone A", "Milestone B"]},
            {"title": "System Architecture", "layout": "two_column", "left_points": ["FastAPI", "Vercel"], "right_points": ["Supabase", "Groq"]}
        ],
        filename="strategy_deck.pptx"
    )
    assert pptx_out["status"] == "created"
    assert pptx_out["file_type"] == "pptx"
    assert pptx_out["slide_count"] >= 3
    assert len(pptx_out["content"]) > 1000

    # DOCX
    docx_out = generate_word_document(
        title="Project Implementation Specification",
        subtitle="Technical Design Document",
        sections=[
            {"heading": "System Architecture", "paragraphs": ["The platform coordinates modular agents via DAG workflows."]},
            {"heading": "Action Items", "bullets": ["Deploy endpoints", "Validate tests"]}
        ],
        filename="project_spec.docx"
    )
    assert docx_out["status"] == "created"
    assert docx_out["file_type"] == "docx"
    assert docx_out["section_count"] == 2
    assert len(docx_out["content"]) > 1000

    # XLSX
    xlsx_out = generate_spreadsheet_workbook(
        sheets=[{
            "sheet_name": "Revenue Forecast",
            "headers": ["Product", "Q1", "Q2", "Q3", "Total"],
            "rows": [["Agent Swarm", 50000, 75000, 110000, "=SUM(B2:D2)"]],
            "include_totals": True
        }],
        filename="financial_model.xlsx"
    )
    assert xlsx_out["status"] == "created"
    assert xlsx_out["file_type"] == "xlsx"
    assert xlsx_out["sheet_count"] == 1
    assert len(xlsx_out["content"]) > 500

    # Direct tool execution endpoint probe
    res_direct_gen = client.post(
        "/api/agents/file_creator/tools/generate_pdf_document/execute",
        json={"arguments": {"title": "API Test PDF", "filename": "api_test.pdf"}},
    )
    assert res_direct_gen.status_code == 200, f"Direct tool execution failed: {res_direct_gen.text}"
    assert res_direct_gen.json()["result"]["file_type"] == "pdf"
    print("PASS: Binary Document Generation Tools verified: PDF, PPTX, DOCX, XLSX with Base64 encoding")

    # 59. Test Binary Document Ingestion & Parsing Tooling (PDF, PPTX, DOCX, XLSX)
    from app.agents.file_parser.tools import parse_binary_document
    # Parse generated PDF
    parsed_pdf = parse_binary_document("swarm_briefing.pdf", pdf_out["content"], file_type="pdf")
    assert parsed_pdf["status"] == "parsed"
    assert parsed_pdf["format"] == "pdf"
    assert parsed_pdf["page_count"] >= 1
    assert "Autonomous Swarm Research Report" in parsed_pdf["extracted_text"]

    # Parse generated PPTX
    parsed_pptx = parse_binary_document("strategy_deck.pptx", pptx_out["content"], file_type="pptx")
    assert parsed_pptx["status"] == "parsed"
    assert parsed_pptx["format"] == "pptx"
    assert parsed_pptx["slide_count"] >= 3
    assert "Q3 Strategy Presentation" in parsed_pptx["extracted_text"]

    # Parse generated DOCX
    parsed_docx = parse_binary_document("project_spec.docx", docx_out["content"], file_type="docx")
    assert parsed_docx["status"] == "parsed"
    assert parsed_docx["format"] == "docx"
    assert "Project Implementation Specification" in parsed_docx["extracted_text"]

    # Parse generated XLSX
    parsed_xlsx = parse_binary_document("financial_model.xlsx", xlsx_out["content"], file_type="xlsx")
    assert parsed_xlsx["status"] == "parsed"
    assert parsed_xlsx["format"] == "xlsx"
    assert parsed_xlsx["sheet_count"] >= 1
    assert "Agent Swarm" in parsed_xlsx["extracted_text"]
    print("PASS: Binary Document Ingestion Tools verified: PDF, PPTX, DOCX, XLSX extraction")

    # 60. Test RAG Document Ingestion, Indexing, and Context Retrieval Endpoints
    rag_payload = {
        "filename": "swarm_security_architecture.md",
        "content": (
            "# Swarm Security Architecture\n"
            "All multi-agent communication routes through secure JWT authentication.\n"
            "Each worker agent operates inside an isolated sandbox with memory boundaries.\n\n"
            "# RAG Data Isolation\n"
            "Document chunks are indexed using hybrid BM25 and vector similarity.\n"
            "Cross-tenant data leakage is strictly blocked by user RLS policies.\n"
        ),
        "chunk_size": 100,
        "chunk_overlap": 20
    }
    res_ingest = client.post("/api/documents/ingest", json=rag_payload, headers=auth_headers)
    assert res_ingest.status_code == 200, f"RAG Ingest failed: {res_ingest.text}"
    ingest_data = res_ingest.json()
    assert ingest_data["status"] == "indexed"
    assert ingest_data["chunk_count"] >= 2
    doc_id = ingest_data["document_id"]

    # Query RAG Context
    query_payload = {"query": "How is multi-agent communication secured?", "top_k": 2}
    res_query = client.post("/api/documents/rag/query", json=query_payload, headers=auth_headers)
    assert res_query.status_code == 200, f"RAG Query failed: {res_query.text}"
    query_data = res_query.json()
    assert query_data["status"] == "success"
    assert query_data["results_count"] > 0
    top_chunk = query_data["chunks"][0]
    assert "JWT authentication" in top_chunk["content"]
    assert top_chunk["confidence"] > 0.0

    # Generate RAG Context Block for Agent Prompts
    res_context = client.post("/api/documents/rag/context", json=query_payload, headers=auth_headers)
    assert res_context.status_code == 200
    context_data = res_context.json()
    assert context_data["status"] == "context_generated"
    assert "### [Retrieved Document Context via RAG]" in context_data["formatted_context_block"]
    assert "swarm_security_architecture.md" in context_data["sources"]

    # List & Delete Document
    res_list_docs = client.get("/api/documents", headers=auth_headers)
    assert res_list_docs.status_code == 200
    assert any(d["document_id"] == doc_id for d in res_list_docs.json())

    res_del_doc = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert res_del_doc.status_code == 200
    assert res_del_doc.json()["status"] == "deleted"
    print("PASS: RAG Ingest, BM25/Vector retrieval, prompt context generation, and index lifecycle verified")

    # ---------------------------------------------------------
    # Test 61: User Artifact Upload & Automatic RAG Indexing
    # ---------------------------------------------------------
    upload_art_payload = {
        "id": "art-user-audit-doc",
        "name": "Audit_Policy_2026.txt",
        "filename": "Audit_Policy_2026.txt",
        "type": "txt",
        "content": "Swarm Platform Security Policy: All financial operations require dual-key multi-sig authorization and cryptographic hash verification.",
        "size_bytes": 115,
        "source_type": "upload",
        "source_title": "Compliance Manual",
    }
    res_up = client.post("/api/artifacts", json=upload_art_payload, headers=auth_headers)
    assert res_up.status_code == 200
    up_data = res_up.json()
    assert up_data["id"] == "art-user-audit-doc"
    assert up_data["downloadable"] is True

    # Verify automatically indexed into RAG store
    from app.rag.store import rag_store
    rag_matches = rag_store.query_context("cryptographic hash verification dual-key")
    assert len(rag_matches) > 0
    assert "Audit_Policy_2026.txt" in [m["filename"] for m in rag_matches]
    print("PASS: User artifact upload and automatic RAG indexing verified")

    # ---------------------------------------------------------
    # Test 62: Chat Turn with Attached Artifacts & Grounded Context
    # ---------------------------------------------------------
    chat_with_art_payload = {
        "messages": [
            {"role": "user", "content": "What are the security authorization rules for financial operations?"}
        ],
        "artifact_ids": ["art-user-audit-doc"],
        "model": "qwen-3.8",
    }
    res_chat_art = client.post("/api/chat", json=chat_with_art_payload, headers=auth_headers)
    assert res_chat_art.status_code == 200
    chat_art_data = res_chat_art.json()
    assert chat_art_data["role"] == "agent"
    meta = chat_art_data.get("metadata", {})
    assert "attached_artifacts" in meta
    assert any(a["id"] == "art-user-audit-doc" for a in meta["attached_artifacts"])
    print("PASS: Chat turn with attached artifacts and grounded context injection verified")

    # ---------------------------------------------------------
    # Test 63: Custom Agent with Attached Knowledge Artifacts
    # ---------------------------------------------------------
    custom_agent_with_art = {
        "id": "agent-compliance-officer",
        "name": "Chief Compliance Officer",
        "role": "Regulatory Specialist",
        "description": "Enforces company compliance rules based on uploaded manuals",
        "system_prompt": "You are the Chief Compliance Officer. Answer strictly based on company audit policies.",
        "model": "qwen-3.8",
        "temperature": 0.2,
        "icon": "ShieldCheck",
        "attached_artifact_ids": ["art-user-audit-doc"],
    }
    res_ca_art = client.post("/api/custom-agents", json=custom_agent_with_art, headers=auth_headers)
    assert res_ca_art.status_code == 200
    ca_saved = res_ca_art.json()
    assert "art-user-audit-doc" in ca_saved.get("attached_artifact_ids", [])

    # Test custom agent playground with attached artifact grounding
    res_ca_test = client.post(
        "/api/custom-agents/test",
        json={
            "agent_id": "agent-compliance-officer",
            "prompt": "Verify policy regarding financial transactions.",
            "attached_artifact_ids": ["art-user-audit-doc"],
        },
        headers=auth_headers
    )
    assert res_ca_test.status_code == 200
    print("PASS: Custom agent creation with attached knowledge artifacts and playground test verified")

    # ---------------------------------------------------------
    # Test 64: Workflow Step Execution with Attached Knowledge Artifacts
    # ---------------------------------------------------------
    res_step_art_test = client.post(
        f"/api/workflows/{wf_id}/steps/step_research/test",
        json={
            "step_id": "step_research",
            "mock_inputs": {"topic": "AI Market Trends 2026"},
            "mock_previous_outputs": {},
        },
        headers=auth_headers,
    )
    assert res_step_art_test.status_code == 200
    assert res_step_art_test.json()["status"] == "completed"
    print("PASS: Workflow step execution with attached knowledge and artifacts verified")

    # Clean up test artifact
    res_del_art = client.delete("/api/artifacts/art-user-audit-doc", headers=auth_headers)
    assert res_del_art.status_code == 200

    # ---------------------------------------------------------
    # Test 65: Orchestrator On-The-Fly Multi-Agent Workflow Synthesis & Execution
    # ---------------------------------------------------------
    from app.supabase import memory_store
    otf_composite_payload = {
        "messages": [
            {
                "role": "user",
                "content": "Find the current market price of Apple stock and synthesize an executive valuation analysis with key financial ratios."
            }
        ],
        "model": "qwen-3.8",
    }
    res_otf = client.post("/api/chat", json=otf_composite_payload, headers=auth_headers)
    assert res_otf.status_code == 200
    otf_data = res_otf.json()
    assert otf_data["role"] == "agent"
    otf_meta = otf_data.get("metadata", {})
    assert otf_meta.get("mode") == "on_the_fly_workflow"
    assert otf_meta.get("is_ephemeral_workflow") is True
    assert otf_meta.get("is_multi_step") is True
    assert "workflow_spec" in otf_meta
    assert len(otf_meta["workflow_spec"]["steps"]) >= 2
    assert len(otf_meta.get("step_runs", [])) >= 2
    assert len(otf_meta.get("granular_trace", [])) >= 2
    # Verify ephemeral workflow was NOT added as a saved workflow in memory_store.workflows
    assert otf_meta["workflow_spec"]["id"] not in memory_store.workflows
    print("PASS: On-the-fly multi-agent workflow synthesis and ephemeral execution verified")

    # ---------------------------------------------------------
    # Test 66: Orchestrator On-The-Fly Single-Agent Workflow Execution
    # ---------------------------------------------------------
    otf_single_payload = {
        "messages": [
            {
                "role": "user",
                "content": "Write a python function to binary search a sorted array recursively."
            }
        ],
        "model": "qwen-3.8",
    }
    res_single = client.post("/api/chat", json=otf_single_payload, headers=auth_headers)
    assert res_single.status_code == 200
    single_data = res_single.json()
    assert single_data["role"] == "agent"
    single_meta = single_data.get("metadata", {})
    assert single_meta.get("is_ephemeral_workflow") is True
    assert single_meta.get("is_multi_step") is False
    assert len(single_meta.get("step_runs", [])) == 1
    assert any(t.get("phase") == "intent_analysis" for t in single_meta.get("granular_trace", []))
    assert any(t.get("phase") == "model_inference" for t in single_meta.get("granular_trace", []))
    print("PASS: On-the-fly single-agent workflow execution and granular trace verified")

    # ---------------------------------------------------------
    # Test 67: Granular Server-Sent Events (SSE) Progress Streaming
    # ---------------------------------------------------------
    stream_payload = {
        "messages": [
            {
                "role": "user",
                "content": "Find the current market price of Tesla stock and prepare an investor valuation briefing."
            }
        ],
        "model": "qwen-3.8",
    }
    res_stream = client.post("/api/chat/stream", json=stream_payload, headers=auth_headers)
    assert res_stream.status_code == 200, f"Chat stream failed: {res_stream.text}"
    assert "text/event-stream" in res_stream.headers.get("content-type", "")

    # Parse SSE chunks
    sse_events = []
    for line in res_stream.text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            data_part = line[5:].strip()
            try:
                sse_events.append(json.loads(data_part))
            except Exception:
                pass

    event_types = [evt.get("type") for evt in sse_events]
    assert "phase" in event_types, f"Phase event missing in SSE: {event_types}"
    assert "workflow_planned" in event_types, f"workflow_planned missing in SSE: {event_types}"
    assert "step_start" in event_types, f"step_start missing in SSE: {event_types}"
    assert "step_complete" in event_types, f"step_complete missing in SSE: {event_types}"
    assert "complete" in event_types, f"complete event missing in SSE: {event_types}"

    # Verify complete event payload structure
    complete_evt = next((e for e in sse_events if e.get("type") == "complete"), None)
    assert complete_evt is not None
    assert "message" in complete_evt
    assert complete_evt["message"]["role"] == "agent"
    assert "metadata" in complete_evt["message"]
    assert complete_evt["message"]["metadata"].get("is_ephemeral_workflow") is True
    print(f"PASS: POST /api/chat/stream granular progress streaming verified ({len(sse_events)} event chunks emitted)")

    # ---------------------------------------------------------
    # Test 68: Save Ephemeral On-The-Fly Workflow to Permanent Library
    # ---------------------------------------------------------
    save_otf_payload = {
        "title": "Saved Market Research & Valuation Pipeline",
        "description": otf_meta["workflow_spec"].get("description", "Synthesized by Swarm Orchestrator."),
        "goal": otf_meta["workflow_spec"].get("goal", "Analyze market price and executive valuation."),
        "steps": otf_meta["workflow_spec"].get("steps", []),
        "edges": otf_meta["workflow_spec"].get("edges", []),
        "is_published": True,
    }
    res_save_wf = client.post("/api/workflows", json=save_otf_payload, headers=auth_headers)
    assert res_save_wf.status_code == 200, f"Saving ephemeral workflow failed: {res_save_wf.text}"
    saved_wf_data = res_save_wf.json()
    assert saved_wf_data["title"] == "Saved Market Research & Valuation Pipeline"
    saved_wf_id = saved_wf_data["id"]
    assert saved_wf_id in memory_store.workflows

    # Verify retrieved by GET /api/workflows/{id}
    res_get_saved = client.get(f"/api/workflows/{saved_wf_id}", headers=auth_headers)
    assert res_get_saved.status_code == 200
    assert res_get_saved.json()["id"] == saved_wf_id
    assert len(res_get_saved.json()["steps"]) >= 2

    # Verify the saved workflow executes end-to-end via /api/workflows/{id}/run
    res_run_saved = client.post(
        f"/api/workflows/{saved_wf_id}/run",
        json={"inputs": {"query": "Apple stock valuation"}},
        headers=auth_headers,
    )
    assert res_run_saved.status_code == 200
    run_output = res_run_saved.json()
    assert run_output["status"] == "completed"
    assert len(run_output["step_runs"]) >= 2
    print(f"PASS: Ephemeral on-the-fly workflow saved to permanent library and executed ({saved_wf_id})")

    # ---------------------------------------------------------
    # Test 69: openpyxl Native Table & Typed Spreadsheet Generation
    # ---------------------------------------------------------
    from app.agents.file_creator.tools import generate_spreadsheet_workbook, extract_tabular_data
    from openpyxl import load_workbook
    import io
    import base64

    test_sheet_spec = [{
        "sheet_name": "FinancialMetrics",
        "headers": ["Metric", "Q1", "Q2", "Target", "Achieved"],
        "rows": [
            ["Revenue", 100000, 125000, 120000, True],
            ["COGS", 40000, 48000, 45000, True],
            ["Gross Profit", "=B2-B3", "=C2-C3", 75000, True],
        ],
        "include_totals": True
    }]
    xlsx_res = generate_spreadsheet_workbook(
        sheets=test_sheet_spec,
        filename="financial_metrics.xlsx",
        title="Q1-Q2 Financial Model"
    )
    assert xlsx_res["status"] == "created"
    assert xlsx_res["file_type"] == "xlsx"
    assert xlsx_res["downloadable"] is True
    assert xlsx_res["size_bytes"] > 0
    assert "FinancialMetrics" in xlsx_res["sheets"]

    # Verify openpyxl native Table object and freeze panes
    loaded_wb = load_workbook(io.BytesIO(base64.b64decode(xlsx_res["content"])))
    metrics_ws = loaded_wb["FinancialMetrics"]
    assert len(metrics_ws.tables) >= 1, "Native openpyxl Table missing from worksheet"
    tbl_name = list(metrics_ws.tables.keys())[0]
    assert metrics_ws.tables[tbl_name].tableStyleInfo.showRowStripes is True
    assert metrics_ws.freeze_panes == "A2", f"Header row must be frozen, got: {metrics_ws.freeze_panes}"
    # Verify typing
    assert metrics_ws.cell(row=2, column=2).value == 100000
    assert isinstance(metrics_ws.cell(row=2, column=2).value, int)
    assert metrics_ws.cell(row=4, column=2).value == "=B2-B3"
    print("PASS: openpyxl native Table, TableStyleInfo, typed cells, and frozen pane verified in generate_spreadsheet_workbook")

    # ---------------------------------------------------------
    # Test 70: Aggressive Multi-Agent Workflow Decomposition
    # ---------------------------------------------------------
    from app.ai_generator import synthesize_on_the_fly_workflow

    # 1. File creation query -> 3-step DAG
    wf_file = synthesize_on_the_fly_workflow("generate a sales spreadsheet for Q1 with revenue metrics")
    assert wf_file["is_multi_step"] is True
    assert len(wf_file["steps"]) == 3
    assert [s["agent_id"] for s in wf_file["steps"]] == ["data_analyst", "file_creator", "synthesizer"]

    # 2. Coding query -> 3-step DAG
    wf_code = synthesize_on_the_fly_workflow("write python code for binary search algorithm")
    assert wf_code["is_multi_step"] is True
    assert len(wf_code["steps"]) == 3
    assert [s["agent_id"] for s in wf_code["steps"]] == ["coder", "reviewer", "synthesizer"]

    # 3. Live search query -> 3-step DAG
    wf_search = synthesize_on_the_fly_workflow("latest news and price of gold")
    assert wf_search["is_multi_step"] is True
    assert len(wf_search["steps"]) == 3
    assert [s["agent_id"] for s in wf_search["steps"]] == ["researcher", "data_analyst", "synthesizer"]

    # 4. Math query -> 2-step DAG
    wf_math = synthesize_on_the_fly_workflow("calculate compound interest for 10000 at 5 percent")
    assert wf_math["is_multi_step"] is True
    assert len(wf_math["steps"]) == 2
    assert [s["agent_id"] for s in wf_math["steps"]] == ["data_analyst", "synthesizer"]

    # 5. Trivial greeting -> 1-agent step
    wf_greeting = synthesize_on_the_fly_workflow("hello")
    assert wf_greeting["is_multi_step"] is False
    assert len(wf_greeting["steps"]) == 1

    # 6. Targeted agent selection -> 1-agent step
    wf_targeted = synthesize_on_the_fly_workflow("generate report", target_agent_id="file_creator")
    assert wf_targeted["is_multi_step"] is False
    assert len(wf_targeted["steps"]) == 1
    assert wf_targeted["steps"][0]["agent_id"] == "file_creator"
    print("PASS: Orchestrator multi-agent workflow decomposition verified across file creation, coding, search, math, and single-agent fallbacks")

    # ---------------------------------------------------------
    # Test 71: Tabular Data Extraction & Markdown Table Conversion
    # ---------------------------------------------------------
    from app.main import extract_file_artifact_from_turn

    sample_md_table = """
Here is the performance report:

| Employee | Department | Score | Bonus |
|---|---|---|---|
| Alice | Engineering | 95 | 5000 |
| Bob | Marketing | 88 | 3500 |
| Charlie | Product | 92 | 4200 |

All targets achieved.
"""
    headers, rows = extract_tabular_data(sample_md_table)
    assert headers == ["Employee", "Department", "Score", "Bonus"]
    assert len(rows) == 3
    assert rows[0] == ["Alice", "Engineering", 95, 5000]
    assert isinstance(rows[0][2], int)
    assert isinstance(rows[0][3], int)

    # Test auto-extraction of xlsx artifact from markdown table in chat response
    art_extracted = extract_file_artifact_from_turn(
        content=sample_md_table,
        agent_id="file_creator",
        prompt="export an excel spreadsheet with employee scores"
    )
    assert art_extracted is not None
    assert art_extracted["type"] == "xlsx"
    assert art_extracted["is_base64"] is True
    assert art_extracted["downloadable"] is True
    wb_extracted = load_workbook(io.BytesIO(base64.b64decode(art_extracted["content"])))
    assert "Data Sheet" in wb_extracted.sheetnames
    ds = wb_extracted["Data Sheet"]
    assert len(ds.tables) >= 1
    assert ds.cell(row=2, column=1).value == "Alice"
    assert ds.cell(row=2, column=3).value == 95
    print("PASS: Tabular data extraction and markdown table to Excel artifact verified")

    print("\n========================================")
    print("ALL 71 MODULAR ENDPOINT & WORKFLOW TESTS PASSED SUCCESSFULLY!")
    print("========================================")

if __name__ == "__main__":
    import os
    os.environ["TESTING"] = "true"
    os.environ["MOCK_GEMINI"] = "true"
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.text = "Here is the verified swarm agent response."
    mock_resp.usage_metadata = MagicMock()
    mock_resp.usage_metadata.total_token_count = 145
    mock_resp.usage_metadata.prompt_token_count = 45
    mock_resp.usage_metadata.candidates_token_count = 100

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    with patch("app.main.get_gemini_client", return_value=(mock_client, "test-api-key")):
        run_tests()
