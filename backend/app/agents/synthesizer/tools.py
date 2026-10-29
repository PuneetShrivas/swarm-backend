import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


def generate_executive_summary(notes: List[str]) -> Dict[str, Any]:
    """Transforms raw notes into an executive summary structure."""
    if not notes:
        return {"error": "Empty notes list provided."}

    takeaways = [f"Key Takeaway: {n[:80]}" for n in notes[:4]]
    return {
        "summary": "Executive synthesis distilled from active findings.",
        "key_takeaways": takeaways,
        "points_analyzed": len(notes),
        "status": "completed",
    }


def format_readme(title: str, sections: Dict[str, str]) -> Dict[str, Any]:
    """Formats a structured README in GitHub Flavored Markdown."""
    lines = [f"# {title}\n"]
    for header, content in sections.items():
        lines.append(f"## {header}\n\n{content}\n")
    doc = "\n".join(lines)
    return {
        "title": title,
        "markdown": doc,
        "section_count": len(sections),
    }


def create_table_of_contents(markdown_content: str) -> Dict[str, Any]:
    """Parses markdown headers and generates an anchor-linked Table of Contents."""
    lines = markdown_content.splitlines()
    header_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
    toc_items = []

    for line in lines:
        match = header_pattern.match(line.strip())
        if match:
            hashes, title = match.groups()
            level = len(hashes)
            slug = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
            indent = "  " * (level - 1)
            toc_items.append(f"{indent}- [{title}](#{slug})")

    toc_text = "## Table of Contents\n\n" + "\n".join(toc_items) if toc_items else "No headers found."
    return {
        "headers_found": len(toc_items),
        "table_of_contents": toc_text,
    }


def lint_and_format_markdown(markdown_content: str) -> Dict[str, Any]:
    """Lints markdown for broken code blocks, trailing spaces, and standardizes spacing."""
    issues = []
    lines = markdown_content.splitlines()

    # Check unclosed code fences
    fence_count = sum(1 for l in lines if l.strip().startswith("```"))
    if fence_count % 2 != 0:
        issues.append("Unclosed markdown code fence (```) detected.")

    cleaned_lines = [l.rstrip() for l in lines]
    formatted = "\n".join(cleaned_lines).strip() + "\n"

    return {
        "issues_found": len(issues),
        "issues": issues if issues else ["No markdown syntax violations."],
        "formatted_markdown": formatted,
        "line_count": len(cleaned_lines),
    }


def extract_action_items(text: str) -> Dict[str, Any]:
    """Extracts TODO items, task checkboxes, and actionable next steps from text."""
    action_items = []
    lines = text.splitlines()

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("- [ ]") or stripped.startswith("- [x]"):
            action_items.append({"task": stripped[5:].strip(), "completed": stripped.startswith("- [x]")})
        elif "todo:" in lower or "action item:" in lower or "next step:" in lower:
            action_items.append({"task": stripped, "completed": False})

    return {
        "items_count": len(action_items),
        "action_items": action_items if action_items else [{"task": "Review document findings", "completed": False}],
    }


def generate_changelog_entry(
    version: str,
    added: Optional[List[str]] = None,
    fixed: Optional[List[str]] = None,
    changed: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Formats Keep-a-Changelog standard release notes block."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"## [{version}] - {date_str}"]

    if added:
        lines.append("\n### Added")
        for item in added:
            lines.append(f"- {item}")
    if changed:
        lines.append("\n### Changed")
        for item in changed:
            lines.append(f"- {item}")
    if fixed:
        lines.append("\n### Fixed")
        for item in fixed:
            lines.append(f"- {item}")

    changelog_text = "\n".join(lines)
    return {
        "version": version,
        "date": date_str,
        "changelog_markdown": changelog_text,
    }


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
                    "description": "List of observations, findings, or notes",
                }
            },
            "required": ["notes"],
        },
        "handler_name": "generate_executive_summary",
    },
    {
        "name": "format_readme",
        "description": "Formats a structured project or module README in GitHub Flavored Markdown.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "sections": {"type": "object", "description": "Key-value mapping of section title to markdown content"},
            },
            "required": ["title", "sections"],
        },
        "handler_name": "format_readme",
    },
    {
        "name": "create_table_of_contents",
        "description": "Parses markdown headers and generates an anchor-linked Table of Contents.",
        "parameters": {
            "type": "object",
            "properties": {
                "markdown_content": {"type": "string", "description": "Markdown document to parse"},
            },
            "required": ["markdown_content"],
        },
        "handler_name": "create_table_of_contents",
    },
    {
        "name": "lint_and_format_markdown",
        "description": "Standardizes markdown formatting, strips trailing whitespace, and verifies code fences.",
        "parameters": {
            "type": "object",
            "properties": {
                "markdown_content": {"type": "string", "description": "Markdown text to lint"},
            },
            "required": ["markdown_content"],
        },
        "handler_name": "lint_and_format_markdown",
    },
    {
        "name": "extract_action_items",
        "description": "Extracts actionable checklist tasks and TODOs from text.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Input text to extract tasks from"},
            },
            "required": ["text"],
        },
        "handler_name": "extract_action_items",
    },
    {
        "name": "generate_changelog_entry",
        "description": "Generates a Keep-a-Changelog standard release entry.",
        "parameters": {
            "type": "object",
            "properties": {
                "version": {"type": "string", "description": "Release semver (e.g. 1.2.0)"},
                "added": {"type": "array", "items": {"type": "string"}, "description": "New features"},
                "fixed": {"type": "array", "items": {"type": "string"}, "description": "Bug fixes"},
                "changed": {"type": "array", "items": {"type": "string"}, "description": "Modified behavior"},
            },
            "required": ["version"],
        },
        "handler_name": "generate_changelog_entry",
    },
]

TOOL_HANDLERS = {
    "generate_executive_summary": generate_executive_summary,
    "format_readme": format_readme,
    "create_table_of_contents": create_table_of_contents,
    "lint_and_format_markdown": lint_and_format_markdown,
    "extract_action_items": extract_action_items,
    "generate_changelog_entry": generate_changelog_entry,
}
