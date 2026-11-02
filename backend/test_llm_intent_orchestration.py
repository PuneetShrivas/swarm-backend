"""
Test Suite: LLM-Driven Intent Analysis & Semantic Orchestration
Validates single-pass LLM intent classification, declarative pipeline dispatching,
offline fallback resilience, and zero substring-collision false positives.
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.ai_generator import (
    analyze_query_intent,
    synthesize_on_the_fly_workflow,
    _deterministic_intent_fallback,
    QueryIntentClassification,
)


def test_poem_with_download_intent():
    query = "generate a markdown md file instructing how a good poem should be written and make it available for download"
    intent = analyze_query_intent(query)
    print(f"\n[TEST 1] Poem Query Intent: {intent.primary_intent} (Reasoning: {intent.reasoning})")
    
    assert intent.primary_intent == "document_authoring", f"Expected document_authoring, got {intent.primary_intent}"
    assert intent.file_export_requested is True, "Expected file_export_requested=True"
    assert intent.export_format == "md", f"Expected export_format=md, got {intent.export_format}"
    
    wf = synthesize_on_the_fly_workflow(prompt=query)
    assert wf["is_multi_step"] is True
    steps = wf["steps"]
    assert len(steps) == 3
    assert steps[0]["agent_id"] == "writer", f"Expected writer, got {steps[0]['agent_id']}"
    assert steps[1]["agent_id"] == "file_creator", f"Expected file_creator, got {steps[1]['agent_id']}"
    assert steps[2]["agent_id"] == "synthesizer", f"Expected synthesizer, got {steps[2]['agent_id']}"
    assert "Live Market" not in wf["title"]
    print("[PASS] test_poem_with_download_intent")


def test_stock_research_with_excel_intent():
    query = "search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet"
    intent = analyze_query_intent(query)
    print(f"\n[TEST 2] Stock Query Intent: {intent.primary_intent} (Reasoning: {intent.reasoning})")
    
    assert intent.primary_intent == "market_intelligence", f"Expected market_intelligence, got {intent.primary_intent}"
    assert intent.requires_live_web_search is True, "Expected requires_live_web_search=True"
    assert intent.file_export_requested is True, "Expected file_export_requested=True"
    
    wf = synthesize_on_the_fly_workflow(prompt=query)
    steps = wf["steps"]
    assert len(steps) == 3
    assert steps[0]["agent_id"] == "researcher"
    assert steps[0].get("model") == "sonar"
    assert steps[1]["agent_id"] == "data_analyst"
    assert steps[2]["agent_id"] == "file_creator"
    print("[PASS] test_stock_research_with_excel_intent")


def test_excel_specialist_operations_intent():
    query = "join Sheet1 and Sheet2 on customer_id and calculate the sum in cell C10"
    intent = analyze_query_intent(query)
    print(f"\n[TEST 3] Excel Specialist Query Intent: {intent.primary_intent} (Reasoning: {intent.reasoning})")
    
    assert intent.primary_intent == "spreadsheet_operations", f"Expected spreadsheet_operations, got {intent.primary_intent}"
    
    wf = synthesize_on_the_fly_workflow(prompt=query)
    steps = wf["steps"]
    assert steps[0]["agent_id"] == "excel_specialist"
    assert len(steps[0]["tool_ids"]) == 8, f"Expected 8 tools, got {len(steps[0]['tool_ids'])}"
    assert "relational_join_sheets" in steps[0]["tool_ids"]
    assert "rollback_spreadsheet_transactions" in steps[0]["tool_ids"]
    print("[PASS] test_excel_specialist_operations_intent")


def test_conversational_greeting_intent():
    query = "hello there, who are you?"
    intent = analyze_query_intent(query)
    print(f"\n[TEST 4] Greeting Query Intent: {intent.primary_intent}")
    
    assert intent.primary_intent == "conversational_greeting"
    assert intent.is_multi_step is False
    
    wf = synthesize_on_the_fly_workflow(prompt=query)
    assert wf["is_multi_step"] is False
    assert len(wf["steps"]) == 1
    assert wf["steps"][0]["agent_id"] == "general_assistant"
    print("[PASS] test_conversational_greeting_intent")


def test_code_engineering_intent():
    query = "write a python script to parse a json file and handle errors with unit tests"
    intent = analyze_query_intent(query)
    print(f"\n[TEST 5] Code Query Intent: {intent.primary_intent}")
    
    assert intent.primary_intent == "code_engineering"
    
    wf = synthesize_on_the_fly_workflow(prompt=query)
    steps = wf["steps"]
    assert steps[0]["agent_id"] == "coder"
    assert steps[1]["agent_id"] == "reviewer"
    assert steps[2]["agent_id"] == "synthesizer"
    print("[PASS] test_code_engineering_intent")


def test_strategic_planning_intent():
    query = "create a 3-month sprint roadmap with phased milestones for our product launch"
    intent = analyze_query_intent(query)
    print(f"\n[TEST 6] Planning Query Intent: {intent.primary_intent}")
    
    assert intent.primary_intent == "strategic_planning"
    
    wf = synthesize_on_the_fly_workflow(prompt=query)
    steps = wf["steps"]
    assert steps[0]["agent_id"] == "planner"
    assert steps[1]["agent_id"] == "synthesizer"
    print("[PASS] test_strategic_planning_intent")


def test_offline_fallback_resilience():
    test_cases = [
        ("generate a poem about the sunrise and make it available for download", "document_authoring"),
        ("what are current stock prices for AAPL and NVDA", "market_intelligence"),
        ("edit cell B4 in Sheet1 to 5000", "spreadsheet_operations"),
        ("implement a REST API in Python using FastAPI", "code_engineering"),
        ("quarterly sprint roadmap", "strategic_planning"),
        ("good morning", "conversational_greeting"),
    ]
    print("\n[TEST 7] Testing deterministic fallback classifier resilience...")
    for q, expected in test_cases:
        fb = _deterministic_intent_fallback(q)
        assert fb.primary_intent == expected, f"Fallback for '{q}' failed: expected {expected}, got {fb.primary_intent}"
    print("[PASS] test_offline_fallback_resilience")


if __name__ == "__main__":
    test_poem_with_download_intent()
    test_stock_research_with_excel_intent()
    test_excel_specialist_operations_intent()
    test_conversational_greeting_intent()
    test_code_engineering_intent()
    test_strategic_planning_intent()
    test_offline_fallback_resilience()
    print("\nALL LLM INTENT ORCHESTRATION TESTS PASSED SUCCESSFULLY!")
