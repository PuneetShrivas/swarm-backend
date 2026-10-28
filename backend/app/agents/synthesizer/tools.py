from typing import Dict, Any, List

def generate_executive_summary(notes: List[str]) -> Dict[str, Any]:
    """
    Transforms raw notes into an executive summary structure.
    """
    return {
        "summary": "Executive summary generated from provided input points.",
        "key_takeaways": [f"Takeaway: {n[:40]}" for n in notes[:3]],
        "points_analyzed": len(notes)
    }

def format_readme(title: str, sections: Dict[str, str]) -> str:
    """
    Formats a structured README in GitHub Flavored Markdown.
    """
    lines = [f"# {title}\n"]
    for header, content in sections.items():
        lines.append(f"## {header}\n{content}\n")
    return "\n".join(lines)

TOOLS = [
    {
        "name": "generate_executive_summary",
        "description": "Synthesizes bulleted notes or agent outputs into an executive summary.",
        "parameters": {
            "type": "object",
            "properties": {
                "notes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of observations, findings, or notes"
                }
            },
            "required": ["notes"]
        },
        "handler_name": "generate_executive_summary"
    }
]

TOOL_HANDLERS = {
    "generate_executive_summary": generate_executive_summary,
    "format_readme": format_readme,
}
