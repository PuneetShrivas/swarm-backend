import re
from typing import Dict, Any, List, Optional


def analyze_readability(text: str) -> Dict[str, Any]:
    """Analyzes text metrics including word count, sentence count, and reading ease."""
    if not text or not text.strip():
        return {"error": "Empty text provided."}

    words = re.findall(r"\b\w+\b", text)
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    word_count = len(words)
    sentence_count = max(1, len(sentences))
    avg_sentence_len = round(word_count / sentence_count, 1)

    # Simple reading speed: 200 words per minute
    reading_time_min = max(1, round(word_count / 200, 1))

    # Flesch-Kincaid style heuristic
    if avg_sentence_len <= 14:
        reading_ease = "Easy / Conversational"
    elif avg_sentence_len <= 22:
        reading_ease = "Standard / Accessible"
    else:
        reading_ease = "Complex / Formal"

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "paragraph_count": len(paragraphs),
        "avg_words_per_sentence": avg_sentence_len,
        "estimated_reading_minutes": reading_time_min,
        "reading_ease": reading_ease,
        "status": "completed",
    }


def generate_article_outline(
    topic: str,
    target_audience: str = "General",
    key_points: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generates a structured outline for an article or long-form essay."""
    points = key_points or ["Core concept overview", "Key mechanisms and evidence", "Practical implications"]
    sections = [
        {"section": "Introduction", "focus": f"Hook reader, introduce {topic}, state thesis for {target_audience}."},
    ]
    for idx, pt in enumerate(points, 1):
        sections.append({
            "section": f"Body Section {idx}: {pt}",
            "focus": f"In-depth exploration of {pt} with examples and evidence.",
        })
    sections.append({
        "section": "Conclusion & Takeaways",
        "focus": "Synthesize key arguments and leave reader with actionable insight.",
    })

    return {
        "topic": topic,
        "target_audience": target_audience,
        "section_count": len(sections),
        "outline": sections,
        "status": "completed",
    }


def format_editorial_copy(
    title: str,
    body: str,
    subtitle: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Formats an editorial piece with clean markdown headers and metadata."""
    header = f"# {title.strip()}\n"
    if subtitle:
        header += f"\n*{subtitle.strip()}*\n"
    header += "\n---\n\n"

    formatted_tags = " ".join([f"`#{t.lstrip('#')}`" for t in (tags or [])])
    footer = f"\n\n---\n{formatted_tags}\n" if formatted_tags else ""

    markdown = f"{header}{body.strip()}{footer}"
    return {
        "title": title,
        "markdown": markdown,
        "word_count": len(markdown.split()),
        "status": "completed",
    }


TOOLS = [
    {
        "name": "analyze_readability",
        "description": "Calculates word count, sentence length, reading ease, and reading time for text.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"},
            },
            "required": ["text"],
        },
        "handler_name": "analyze_readability",
    },
    {
        "name": "generate_article_outline",
        "description": "Generates a structured section-by-section outline for an article or essay.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Subject or theme of the article"},
                "target_audience": {"type": "string", "description": "Intended readership"},
                "key_points": {"type": "array", "items": {"type": "string"}, "description": "Key themes to cover"},
            },
            "required": ["topic"],
        },
        "handler_name": "generate_article_outline",
    },
    {
        "name": "format_editorial_copy",
        "description": "Formats an editorial piece with titles, subtitles, divider, and tag metadata.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Main title"},
                "body": {"type": "string", "description": "Main editorial body text"},
                "subtitle": {"type": "string", "description": "Optional subtitle"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional topic tags"},
            },
            "required": ["title", "body"],
        },
        "handler_name": "format_editorial_copy",
    },
]

TOOL_HANDLERS = {
    "analyze_readability": analyze_readability,
    "generate_article_outline": generate_article_outline,
    "format_editorial_copy": format_editorial_copy,
}
