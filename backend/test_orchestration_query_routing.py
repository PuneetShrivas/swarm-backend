"""
Test Suite: Orchestration Query Routing & Markdown Document Artifact Extraction
Ensures non-market queries containing 'download' do not falsely trigger market searches,
and verifies correct multi-agent synthesis and downloadable markdown artifact extraction.
"""

import sys
import os
import base64

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.ai_generator import synthesize_on_the_fly_workflow
from app.main import extract_file_artifact_from_turn


def test_poem_markdown_workflow_synthesis():
    query = "generate a markdown md file instructing how a good poem should be written and make it available for download"
    wf = synthesize_on_the_fly_workflow(prompt=query)
    
    print("[TEST 1] Poem workflow title:", wf.get("title"))
    assert wf.get("is_multi_step") is True, "Workflow should be multi-step"
    steps = wf.get("steps", [])
    assert len(steps) == 3, f"Expected 3 steps, got {len(steps)}"
    
    # Verify agents and steps
    assert steps[0]["agent_id"] == "writer", f"Step 1 should be writer, got {steps[0]['agent_id']}"
    assert steps[1]["agent_id"] == "file_creator", f"Step 2 should be file_creator, got {steps[1]['agent_id']}"
    assert steps[2]["agent_id"] == "synthesizer", f"Step 3 should be synthesizer, got {steps[2]['agent_id']}"
    
    # Verify no financial/market artifacts in title or step names
    title = wf.get("title", "").lower()
    step_names = [s.get("name", "").lower() for s in steps]
    assert "market" not in title, f"Title should not contain 'market': {title}"
    assert "stock" not in title, f"Title should not contain 'stock': {title}"
    for name in step_names:
        assert "market" not in name, f"Step name should not contain 'market': {name}"
        assert "stock" not in name, f"Step name should not contain 'stock': {name}"
    print("[PASS] test_poem_markdown_workflow_synthesis")


def test_download_keyword_does_not_trigger_market_search():
    queries = [
        "can you make this summary available for download",
        "please download this guide for future reading",
        "stockpile of creative ideas for our next meeting",
    ]
    for q in queries:
        wf = synthesize_on_the_fly_workflow(prompt=q)
        title = wf.get("title", "").lower()
        step_names = [s.get("name", "").lower() for s in wf.get("steps", [])]
        assert "market" not in title, f"Query '{q}' triggered market title: {title}"
        assert "stock discovery" not in title, f"Query '{q}' triggered stock discovery: {title}"
        for name in step_names:
            assert "market data" not in name, f"Query '{q}' triggered market data step: {name}"
            assert "stock discovery" not in name, f"Query '{q}' triggered stock discovery step: {name}"
    print("[PASS] test_download_keyword_does_not_trigger_market_search")


def test_legitimate_market_search_still_routes_correctly():
    query = "search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet"
    wf = synthesize_on_the_fly_workflow(prompt=query)
    
    print("[TEST 3] Market query title:", wf.get("title"))
    assert wf.get("is_multi_step") is True
    steps = wf.get("steps", [])
    assert len(steps) >= 2
    assert steps[0]["agent_id"] == "researcher"
    assert steps[0].get("model") == "sonar", f"Expected sonar model for live researcher, got {steps[0].get('model')}"
    print("[PASS] test_legitimate_market_search_still_routes_correctly")


def test_extract_markdown_artifact_without_fences():
    content = """# How to Write a Good Poem

A truly resonant poem captures an emotional truth through imagery, rhythm, and economy of language.

## 1. Finding the Core Emotion
Start with an image or feeling rather than an abstract concept.

## 2. Choosing Meter and Form
Free verse or structured meter? Listen to the cadence of the words.

## 3. Revision and Polish
Prune every unnecessary syllable until each word carries weight.
"""
    prompt = "generate a markdown md file instructing how a good poem should be written and make it available for download"
    artifact = extract_file_artifact_from_turn(content, agent_id="orchestrator", prompt=prompt)
    
    assert artifact is not None, "Expected an artifact to be extracted"
    assert artifact["type"] == "md", f"Expected type 'md', got {artifact['type']}"
    assert artifact["mime_type"] == "text/markdown", f"Expected text/markdown, got {artifact['mime_type']}"
    assert artifact["downloadable"] is True, "Artifact should be downloadable"
    assert artifact["filename"].endswith(".md"), f"Filename should end with .md: {artifact['filename']}"
    assert "how_to_write_a_good_poem" in artifact["filename"], f"Filename should slugify header: {artifact['filename']}"
    assert artifact.get("content_base64"), "Artifact should include content_base64"
    decoded = base64.b64decode(artifact["content_base64"]).decode("utf-8")
    assert decoded == content.strip()
    print("[PASS] test_extract_markdown_artifact_without_fences")


def test_extract_markdown_artifact_with_fences():
    content = """Here is the complete instructional guide on writing poetry:

```markdown
# The Craft of Poetic Composition

Poetry is distilled human feeling captured in structured cadence.

### Stanzas and Rhyme
Use meter with intention.
```

Enjoy reading this guide!"""

    prompt = "generate a markdown md file instructing how a good poem should be written and make it available for download"
    artifact = extract_file_artifact_from_turn(content, agent_id="orchestrator", prompt=prompt)
    
    assert artifact is not None, "Expected an artifact to be extracted"
    assert artifact["type"] == "md", f"Expected type 'md', got {artifact['type']}"
    assert artifact["mime_type"] == "text/markdown"
    assert artifact["downloadable"] is True
    assert artifact["filename"].endswith(".md")
    assert "the_craft_of_poetic" in artifact["filename"]
    print("[PASS] test_extract_markdown_artifact_with_fences")


if __name__ == "__main__":
    test_poem_markdown_workflow_synthesis()
    test_download_keyword_does_not_trigger_market_search()
    test_legitimate_market_search_still_routes_correctly()
    test_extract_markdown_artifact_without_fences()
    test_extract_markdown_artifact_with_fences()
    print("\nALL ORCHESTRATION QUERY ROUTING TESTS PASSED SUCCESSFULLY!")
