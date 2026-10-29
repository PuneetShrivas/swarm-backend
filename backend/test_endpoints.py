import sys
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
        "model": "gemini-2.5-flash",
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
        "model": "gemini-2.5-flash",
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
        "model": "gemini-2.5-flash",
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

    # 32. Test Base Conversational Agent & Model Selection Override
    res_conv = client.post(
        "/api/chat",
        json={
            "messages": [{"role": "user", "content": "Hello! How are you doing today?"}],
            "model": "gemini-2.5-pro",
        },
        headers=auth_headers,
    )
    assert res_conv.status_code == 200, f"Conversational chat turn failed: {res_conv.text}"
    conv_data = res_conv.json()
    assert conv_data["metadata"]["agent_id"] == "general_assistant"
    assert conv_data["metadata"]["model"] == "gemini-2.5-pro"
    print(f"PASS: Conversational routing routed to 'general_assistant' with custom model selection: {conv_data['metadata']['model']}")

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

    print("\n========================================")
    print("ALL 33 MODULAR ENDPOINT & WORKFLOW TESTS PASSED SUCCESSFULLY!")
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
