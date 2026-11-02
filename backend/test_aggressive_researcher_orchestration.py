"""
Automated Test Suite for Aggressive Researcher Orchestration and Multi-Agent Routing.
Verifies that:
1. route_agent defaults to Orchestrator in auto-route chat mode and preserves explicit target agents.
2. User query 'search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet'
   properly synthesizes researcher (with Perplexity Sonar) -> data_analyst -> file_creator.
3. requires_fresh_internet_information aggressively captures search verbs, financial/stock performance, and temporal triggers.
4. Non-stock live search requests with spreadsheet/file export invoke researcher with sonar and file_creator.
"""

import sys
import unittest
from app.main import route_agent
from app.ai_generator import (
    synthesize_on_the_fly_workflow,
    requires_fresh_internet_information,
)
from app.agents import agent_registry


class TestAggressiveResearcherOrchestration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        agent_registry.initialize()

    def test_route_agent_defaults_to_orchestrator(self):
        """Auto-route chat queries must return Orchestrator, not be intercepted by single-agent keyword heuristics."""
        queries = [
            "search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet",
            "create an excel spreadsheet for sales data",
            "write python code for a binary search tree",
            "synthesize a report on climate change",
            "what is the latest news today",
        ]
        for q in queries:
            agent = route_agent(None, q)
            agent_id = getattr(agent, "agent_id", getattr(agent, "id", None))
            self.assertEqual(
                agent_id,
                "orchestrator",
                f"Query '{q}' should route to orchestrator, got '{agent_id}'"
            )

        # Empty or explicit 'orchestrator' should also return orchestrator
        agent_empty = route_agent("", "hello")
        self.assertEqual(getattr(agent_empty, "agent_id", getattr(agent_empty, "id", None)), "orchestrator")

        agent_explicit_orch = route_agent("orchestrator", "do something")
        self.assertEqual(getattr(agent_explicit_orch, "agent_id", getattr(agent_explicit_orch, "id", None)), "orchestrator")

    def test_route_agent_honors_explicit_single_target(self):
        """Explicitly targeting a specific agent from UI dropdown must be honored."""
        coder = route_agent("coder", "search out the latest stock performances and create an excel sheet")
        coder_id = getattr(coder, "agent_id", getattr(coder, "id", None))
        self.assertEqual(coder_id, "coder")

        researcher = route_agent("researcher", "hi")
        res_id = getattr(researcher, "agent_id", getattr(researcher, "id", None))
        self.assertEqual(res_id, "researcher")

    def test_user_stock_excel_query_orchestration(self):
        """
        Query: 'search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet'
        Must synthesize:
        Step 1: researcher (model: sonar)
        Step 2: data_analyst
        Step 3: file_creator
        """
        prompt = "search out the latest stock performances of apple, amazon and microsoft and then put them in an excel sheet"
        wf = synthesize_on_the_fly_workflow(prompt)

        self.assertTrue(wf.get("is_multi_step"), "Workflow must be multi-step")
        steps = wf.get("steps", [])
        self.assertEqual(len(steps), 3, f"Expected 3 steps, got {len(steps)}")

        # Step 1: researcher with Perplexity Sonar
        step_1 = steps[0]
        self.assertEqual(step_1.get("agent_id"), "researcher")
        self.assertEqual(step_1.get("model"), "sonar", "Researcher must use Perplexity Sonar 'sonar'")

        # Step 2: data_analyst for tabular normalization
        step_2 = steps[1]
        self.assertEqual(step_2.get("agent_id"), "data_analyst")

        # Step 3: file_creator for Excel spreadsheet synthesis
        step_3 = steps[2]
        self.assertEqual(step_3.get("agent_id"), "file_creator")

    def test_requires_fresh_internet_information_comprehensive(self):
        """Aggressive detection of live web search cues, stock performance, and temporal triggers."""
        fresh_prompts = [
            "search out the latest stock performances of apple, amazon and microsoft",
            "search for current share price of nvidia",
            "look up today's weather in Tokyo",
            "find out who won the match yesterday",
            "check latest earnings report for Tesla",
            "google breaking news on space exploration",
            "what is the current market cap of Microsoft",
            "search the web for 2026 AI benchmarks",
        ]
        for p in fresh_prompts:
            self.assertTrue(
                requires_fresh_internet_information(p),
                f"Prompt should require fresh internet information: '{p}'"
            )

        static_prompts = [
            "explain object oriented programming in python",
            "write a poem about trees",
        ]
        for p in static_prompts:
            self.assertFalse(
                requires_fresh_internet_information(p),
                f"Prompt should not require fresh internet information: '{p}'"
            )

    def test_live_search_file_generation_pipeline(self):
        """Live web query requesting a file export must route to researcher (sonar) -> data_analyst -> file_creator."""
        prompt = "search the internet for latest AI breakthroughs and save to a spreadsheet"
        wf = synthesize_on_the_fly_workflow(prompt)

        steps = wf.get("steps", [])
        self.assertTrue(len(steps) >= 3)
        self.assertEqual(steps[0].get("agent_id"), "researcher")
        self.assertEqual(steps[0].get("model"), "sonar")
        self.assertEqual(steps[1].get("agent_id"), "data_analyst")
        self.assertEqual(steps[2].get("agent_id"), "file_creator")

    def test_market_query_without_file_export(self):
        """Market query without file export should end in synthesizer briefing."""
        prompt = "search out the latest stock performances of apple, amazon and microsoft"
        wf = synthesize_on_the_fly_workflow(prompt)

        steps = wf.get("steps", [])
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0].get("agent_id"), "researcher")
        self.assertEqual(steps[0].get("model"), "sonar")
        self.assertEqual(steps[1].get("agent_id"), "data_analyst")
        self.assertEqual(steps[2].get("agent_id"), "synthesizer")


if __name__ == "__main__":
    unittest.main()
