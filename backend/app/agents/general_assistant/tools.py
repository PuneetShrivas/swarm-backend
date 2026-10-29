from typing import Dict, Any


def general_lookup(topic: str) -> Dict[str, Any]:
    """Provides general knowledge lookups."""
    return {"topic": topic, "status": "resolved"}


TOOLS = [
    {
        "name": "general_lookup",
        "description": "Performs general concept inquiries.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The concept or topic to lookup"},
            },
            "required": ["topic"],
        },
        "handler_name": "general_lookup",
    }
]

TOOL_HANDLERS = {
    "general_lookup": general_lookup,
}
