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
    print(f"      Response snippet: {msg['content'][:80]}...")
    print(f"      Tool calls returned: {len(msg['metadata'].get('tool_calls', []))}")

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
    print(f"      Response snippet: {msg['content'][:80]}...")

    print("\n========================================")
    print("ALL ENDPOINT TESTS PASSED SUCCESSFULLY!")
    print("========================================")

if __name__ == "__main__":
    run_tests()
