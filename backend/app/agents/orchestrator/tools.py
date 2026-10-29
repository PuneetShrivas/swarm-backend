import uuid
from typing import Dict, Any, List, Optional


def swarm_router(query: str, target_agent: str = "orchestrator") -> Dict[str, Any]:
    """Evaluates prompt intent and recommends optimal specialist routing."""
    lower_q = query.lower()
    recommended = target_agent

    if any(k in lower_q for k in ["code", "bug", "python", "function", "javascript", "typescript", "implement"]):
        recommended = "coder"
    elif any(k in lower_q for k in ["data", "csv", "statistic", "correlat", "forecast", "metric"]):
        recommended = "data_analyst"
    elif any(k in lower_q for k in ["search", "find out", "research", "market", "stock", "price", "cite"]):
        recommended = "researcher"
    elif any(k in lower_q for k in ["review", "security", "audit", "owasp", "vulnerability"]):
        recommended = "reviewer"
    elif any(k in lower_q for k in ["summarize", "readme", "document", "toc", "changelog"]):
        recommended = "synthesizer"
    elif any(k in lower_q for k in ["create file", "export", "download file", "generate json", "artifact"]):
        recommended = "file_creator"
    elif any(k in lower_q for k in ["parse file", "read pdf", "extract text", "ingest file", "inspect csv"]):
        recommended = "file_parser"

    return {
        "status": "routed",
        "recommended_agent": recommended,
        "query_preview": query[:64] + ("..." if len(query) > 64 else ""),
    }


def swarm_delegate(agent_id: str, subtask: str) -> Dict[str, Any]:
    """Delegates a specific subtask to a specialized agent in the swarm."""
    task_id = str(uuid.uuid4())[:8]
    return {
        "status": "delegated",
        "task_id": f"task_{task_id}",
        "delegate_agent": agent_id,
        "subtask": subtask,
        "execution_state": "queued",
    }


def generate_workflow_dag(goal: str, agents_available: Optional[List[str]] = None) -> Dict[str, Any]:
    """Generates structured multi-step DAG with nodes, edges, dependencies, and agent assignments."""
    available = agents_available or ["researcher", "coder", "reviewer", "synthesizer"]
    
    # Heuristic workflow construction
    nodes = [
        {
            "id": "step_1_research",
            "name": "Empirical Research & Scope",
            "agent": "researcher" if "researcher" in available else available[0],
            "description": f"Gather prerequisites and market references for: {goal[:50]}",
        },
        {
            "id": "step_2_implementation",
            "name": "Core Logic Implementation",
            "agent": "coder" if "coder" in available else available[0],
            "description": "Construct code and operational scaffolding.",
        },
        {
            "id": "step_3_verification",
            "name": "Quality & Security Review",
            "agent": "reviewer" if "reviewer" in available else available[0],
            "description": "Audit security vulnerabilities and edge case test coverage.",
        },
        {
            "id": "step_4_synthesis",
            "name": "Executive Synthesis & Packaging",
            "agent": "synthesizer" if "synthesizer" in available else available[0],
            "description": "Produce structured documentation and user-facing delivery summary.",
        },
    ]

    edges = [
        {"from": "step_1_research", "to": "step_2_implementation"},
        {"from": "step_2_implementation", "to": "step_3_verification"},
        {"from": "step_3_verification", "to": "step_4_synthesis"},
    ]

    return {
        "workflow_goal": goal,
        "steps_count": len(nodes),
        "nodes": nodes,
        "edges": edges,
        "status": "generated",
    }


def evaluate_consensus(proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Weighs multi-agent recommendations, computes agreement score, and resolves conflicting decisions."""
    if not proposals:
        return {"error": "Empty proposals list provided."}

    total = len(proposals)
    agent_votes: Dict[str, int] = {}
    for p in proposals:
        decision = str(p.get("decision", p.get("verdict", "approve"))).lower()
        agent_votes[decision] = agent_votes.get(decision, 0) + 1

    top_decision = max(agent_votes.items(), key=lambda x: x[1])
    agreement_score = round(top_decision[1] / total, 2)

    return {
        "total_proposals": total,
        "majority_verdict": top_decision[0],
        "vote_distribution": agent_votes,
        "consensus_agreement_ratio": agreement_score,
        "unanimous": agreement_score == 1.0,
    }


TOOLS = [
    {
        "name": "swarm_router",
        "description": "Evaluates prompt intent and recommends the best agent to handle the request.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The user inquiry to route"},
                "target_agent": {"type": "string", "description": "Default recommended agent ID"},
            },
            "required": ["query"],
        },
        "handler_name": "swarm_router",
    },
    {
        "name": "swarm_delegate",
        "description": "Delegates a specific subtask to a specialized agent in the swarm.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "ID of the agent to delegate to"},
                "subtask": {"type": "string", "description": "Specific subtask instructions"},
            },
            "required": ["agent_id", "subtask"],
        },
        "handler_name": "swarm_delegate",
    },
    {
        "name": "generate_workflow_dag",
        "description": "Constructs a directed acyclic graph workflow allocating specialist subtasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "High-level user objective"},
                "agents_available": {"type": "array", "items": {"type": "string"}, "description": "List of available agent IDs"},
            },
            "required": ["goal"],
        },
        "handler_name": "generate_workflow_dag",
    },
    {
        "name": "evaluate_consensus",
        "description": "Aggregates multi-agent recommendations and resolves conflicting decisions.",
        "parameters": {
            "type": "object",
            "properties": {
                "proposals": {"type": "array", "items": {"type": "object"}, "description": "Proposals submitted by agents"},
            },
            "required": ["proposals"],
        },
        "handler_name": "evaluate_consensus",
    },
]

TOOL_HANDLERS = {
    "swarm_router": swarm_router,
    "swarm_delegate": swarm_delegate,
    "generate_workflow_dag": generate_workflow_dag,
    "evaluate_consensus": evaluate_consensus,
}
