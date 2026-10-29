from typing import Dict, Any, List, Optional


def general_lookup(topic: str) -> Dict[str, Any]:
    """Provides general knowledge lookups across technical and conversational concepts."""
    return {
        "topic": topic,
        "status": "resolved",
        "reference_summary": f"General reference analysis for: '{topic.strip()}'",
    }


def clarify_intent(user_prompt: str) -> Dict[str, Any]:
    """Analyzes an inquiry and recommends targeted clarifying questions to eliminate ambiguity."""
    clean = user_prompt.strip()
    words = clean.split()
    is_brief = len(words) < 5

    questions = []
    if is_brief:
        questions.append("Could you clarify the specific programming language or operational environment?")
        questions.append("What is your desired final output format (code snippet, step-by-step tutorial, or architecture)?")
    else:
        questions.append(f"Are there any specific constraints or frameworks to keep in mind regarding '{words[0]}... '?")
        questions.append("Would you like a high-level overview or an in-depth implementation walkthrough?")

    return {
        "original_prompt": clean,
        "is_ambiguous": is_brief,
        "recommended_clarifications": questions,
        "inferred_domain": "general_inquiry" if is_brief else "specialized_task",
    }


def summarize_dialogue(messages: List[Dict[str, str]], max_bullets: int = 4) -> Dict[str, Any]:
    """Distills conversation turns into a succinct set of context points."""
    if not messages:
        return {"summary": "No dialogue messages provided.", "points": []}

    bullets = []
    for m in messages[-max_bullets:]:
        role = m.get("role", "user").capitalize()
        preview = m.get("content", "")[:70]
        bullets.append(f"{role}: {preview}...")

    return {
        "turns_analyzed": len(messages),
        "key_points": bullets,
        "active_context": "Dialogue active and focused on task completion.",
    }


def format_response_structure(content: str, style: str = "bulleted") -> Dict[str, Any]:
    """Transforms raw stream or unstructured response into structured markdown."""
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    if style == "numbered":
        formatted = "\n".join(f"{idx + 1}. {line}" for idx, line in enumerate(lines))
    elif style == "executive":
        formatted = f"### Summary\n\n{lines[0] if lines else ''}\n\n### Details\n\n" + "\n".join(f"- {l}" for l in lines[1:])
    else:
        formatted = "\n".join(f"- {line}" for line in lines)

    return {
        "style": style,
        "lines_processed": len(lines),
        "formatted_content": formatted,
    }


TOOLS = [
    {
        "name": "general_lookup",
        "description": "Performs general concept inquiries and synthesizes technical foundations.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The concept or topic to lookup"},
            },
            "required": ["topic"],
        },
        "handler_name": "general_lookup",
    },
    {
        "name": "clarify_intent",
        "description": "Formulates clarifying questions and resolves ambiguity in user prompts.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_prompt": {"type": "string", "description": "User's initial inquiry"},
            },
            "required": ["user_prompt"],
        },
        "handler_name": "clarify_intent",
    },
    {
        "name": "summarize_dialogue",
        "description": "Summarizes recent conversation turns into concise contextual memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "messages": {"type": "array", "items": {"type": "object"}, "description": "List of message dicts with role and content"},
                "max_bullets": {"type": "integer", "description": "Maximum bullet items to produce"},
            },
            "required": ["messages"],
        },
        "handler_name": "summarize_dialogue",
    },
    {
        "name": "format_response_structure",
        "description": "Restructures text content into bulleted, numbered, or executive format.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Raw text content"},
                "style": {"type": "string", "description": "Formatting style ('bulleted', 'numbered', 'executive')"},
            },
            "required": ["content"],
        },
        "handler_name": "format_response_structure",
    },
]

TOOL_HANDLERS = {
    "general_lookup": general_lookup,
    "clarify_intent": clarify_intent,
    "summarize_dialogue": summarize_dialogue,
    "format_response_structure": format_response_structure,
}
