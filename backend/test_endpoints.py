import sys
from fastapi.testclient import TestClient
from app.main import app, agents_db

client = TestClient(app)

def run_tests():
    print("========================================")
    print("Testing Swarm Backend Endpoints")
    print("========================================\n")

    # 1. Test Root
    res = client.get("/")
    assert res.status_code == 200, f"Root failed: {res.status_code}"
    print("PASS: GET / ->", res.json())

    # 2. Test Health
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    health_data = res.json()
    assert health_data["status"] == "ok"
    assert health_data["agents_online"] >= 2
    assert "supabase_configured" in health_data
    print("PASS: GET /api/health ->", health_data)

    # 3. Test Agents Roster
    res = client.get("/api/agents")
    assert res.status_code == 200, f"Get agents failed: {res.status_code}"
    agents = res.json()
    assert len(agents) >= 2
    agent_ids = [a["id"] for a in agents]
    assert "researcher" in agent_ids
    assert "coder" in agent_ids
    print(f"PASS: GET /api/agents -> Found {len(agents)} agents: {agent_ids}")

    # 4. Test Create Agent
    new_agent = {
        "id": "qa-tester",
        "name": "QA Specialist",
        "role": "Performs integration and automated regression testing",
        "status": "active",
        "system_prompt": "You are a test engineer validating swarm APIs.",
    }
    res = client.post("/api/agents", json=new_agent)
    assert res.status_code == 200, f"Create agent failed: {res.status_code}"
    created = res.json()
    assert created["id"] == "qa-tester"
    print("PASS: POST /api/agents -> Created agent:", created["name"])

    # 5. Test Chat with Auto Routing (Coding query)
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

    # 6. Test Chat with Explicit Target Agent ("researcher")
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

    # 7. Test Auth Enforcement on Protected Endpoints
    res = client.get("/api/sessions")
    assert res.status_code == 401, f"Expected 401 unauthorized on /api/sessions without auth, got {res.status_code}"
    print("PASS: GET /api/sessions without auth header returned 401 Unauthorized")

    # 8. Test Session Creation with Authenticated User
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

    # 9. Test Session Retrieval
    res = client.get(f"/api/sessions/{session_id}", headers=auth_headers)
    assert res.status_code == 200, f"Failed getting session detail: {res.status_code}"
    detail = res.json()
    assert detail["session"]["id"] == session_id
    assert isinstance(detail["messages"], list)
    print(f"PASS: GET /api/sessions/{session_id} -> Retrieved session with {len(detail['messages'])} messages")

    # 10. Test Session Update (Rename)
    res = client.patch(f"/api/sessions/{session_id}", json={"title": "Renamed AI Session"}, headers=auth_headers)
    assert res.status_code == 200, f"Failed renaming session: {res.status_code}"
    updated_session = res.json()
    assert updated_session["title"] == "Renamed AI Session"
    print("PASS: PATCH /api/sessions/{session_id} -> Successfully updated title to 'Renamed AI Session'")

    # 11. Test Chat Turn Linked to Session (Persisting messages & recording usage)
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

    # 12. Test Usage Telemetry Aggregation
    res = client.get("/api/usage", headers=auth_headers)
    assert res.status_code == 200, f"Usage retrieval failed: {res.status_code}"
    usage = res.json()
    assert usage["total_requests"] >= 1
    assert usage["total_tokens"] >= 0
    assert len(usage["recent_activity"]) >= 1
    print(f"PASS: GET /api/usage -> Total tokens: {usage['total_tokens']}, Requests: {usage['total_requests']}")

    # 13. Test Session Deletion
    res = client.delete(f"/api/sessions/{session_id}", headers=auth_headers)
    assert res.status_code == 200, f"Delete session failed: {res.status_code}"
    print(f"PASS: DELETE /api/sessions/{session_id} -> Deleted successfully")

    # Confirm deleted
    res = client.get(f"/api/sessions/{session_id}", headers=auth_headers)
    assert res.status_code == 404, f"Expected 404 for deleted session, got {res.status_code}"
    print("PASS: Verified session is no longer accessible (404)")

    print("\n========================================")
    print("ALL 13 ENDPOINT TESTS PASSED SUCCESSFULLY!")
    print("========================================")

if __name__ == "__main__":
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
