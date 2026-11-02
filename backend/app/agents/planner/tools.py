from typing import Dict, Any, List, Optional


def generate_milestone_plan(
    goal: str,
    phases_count: int = 3,
    target_duration: str = "3 months",
) -> Dict[str, Any]:
    """Generates a phased milestone roadmap from a high-level goal."""
    if not goal or not goal.strip():
        return {"error": "Empty goal provided."}

    phases = []
    phase_names = [
        "Phase 1: Foundation & Discovery",
        "Phase 2: Core Implementation & Integration",
        "Phase 3: Validation, Polish & Launch",
        "Phase 4: Optimization & Scale",
    ]

    for i in range(min(max(1, phases_count), len(phase_names))):
        p_name = phase_names[i]
        phases.append({
            "phase": p_name,
            "focus": f"Achieve milestones for {goal[:60]} in {p_name.split(':')[1].strip()}",
            "milestones": [
                f"Define requirements and scope for milestone {i+1}.1",
                f"Execute deliverables and verify progress for milestone {i+1}.2",
            ],
            "completion_criteria": f"Deliverables signed off for {p_name.split(':')[1].strip()}",
        })

    return {
        "goal": goal,
        "target_duration": target_duration,
        "phases_count": len(phases),
        "phases": phases,
        "status": "completed",
    }


def calculate_critical_path(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resolves task dependencies and identifies critical sequential path."""
    if not tasks:
        return {"error": "No tasks provided."}

    task_map = {t.get("id", f"task_{idx}"): t for idx, t in enumerate(tasks)}
    sequenced = []
    visited = set()

    # Simple topological dependency ordering
    for tid, task in task_map.items():
        deps = task.get("depends_on") or []
        for d in deps:
            if d in task_map and d not in visited:
                sequenced.append(task_map[d])
                visited.add(d)
        if tid not in visited:
            sequenced.append(task)
            visited.add(tid)

    return {
        "total_tasks": len(tasks),
        "sequenced_order": [t.get("id") or t.get("name") for t in sequenced],
        "has_dependencies": any(bool(t.get("depends_on")) for t in tasks),
        "status": "completed",
    }


def estimate_sprint_allocation(tasks: List[str], sprint_capacity: int = 10) -> Dict[str, Any]:
    """Allocates task items into sequential sprints based on capacity limits."""
    if not tasks:
        return {"error": "No tasks provided."}

    sprints = []
    curr_sprint = []
    sprint_idx = 1

    for t in tasks:
        curr_sprint.append(t)
        if len(curr_sprint) >= sprint_capacity:
            sprints.append({
                "sprint_name": f"Sprint {sprint_idx}",
                "task_count": len(curr_sprint),
                "tasks": list(curr_sprint),
            })
            curr_sprint = []
            sprint_idx += 1

    if curr_sprint:
        sprints.append({
            "sprint_name": f"Sprint {sprint_idx}",
            "task_count": len(curr_sprint),
            "tasks": curr_sprint,
        })

    return {
        "total_tasks": len(tasks),
        "sprint_capacity": sprint_capacity,
        "total_sprints": len(sprints),
        "sprints": sprints,
        "status": "completed",
    }


TOOLS = [
    {
        "name": "generate_milestone_plan",
        "description": "Generates a structured phased roadmap with milestones and completion criteria.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "High-level project objective"},
                "phases_count": {"type": "integer", "description": "Number of sequential phases (default: 3)"},
                "target_duration": {"type": "string", "description": "Expected timeframe (e.g. 3 months)"},
            },
            "required": ["goal"],
        },
        "handler_name": "generate_milestone_plan",
    },
    {
        "name": "calculate_critical_path",
        "description": "Analyzes task dependencies to construct an ordered critical execution path.",
        "parameters": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "depends_on": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "description": "List of tasks with dependency IDs",
                }
            },
            "required": ["tasks"],
        },
        "handler_name": "calculate_critical_path",
    },
    {
        "name": "estimate_sprint_allocation",
        "description": "Groups task lists into sequential sprints respecting capacity limits.",
        "parameters": {
            "type": "object",
            "properties": {
                "tasks": {"type": "array", "items": {"type": "string"}, "description": "List of task descriptions"},
                "sprint_capacity": {"type": "integer", "description": "Max tasks per sprint"},
            },
            "required": ["tasks"],
        },
        "handler_name": "estimate_sprint_allocation",
    },
]

TOOL_HANDLERS = {
    "generate_milestone_plan": generate_milestone_plan,
    "calculate_critical_path": calculate_critical_path,
    "estimate_sprint_allocation": estimate_sprint_allocation,
}
