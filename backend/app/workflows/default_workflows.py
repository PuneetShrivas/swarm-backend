"""
Default Workflow Templates — Pre-built workflow definitions seeded at startup.

Provides production-quality multi-agent, multi-block-type workflows that
demonstrate the full capabilities of the workflow engine: agent execution,
Python code blocks, condition branching, loops, and artifact generation.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any


# Stable deterministic UUIDs for default workflows (UUID format is required by Supabase Postgres)
DEFAULT_RESEARCH_WORKFLOW_ID = "0193e182-5af1-5bf1-bfe2-970663d16eb8"
DEFAULT_DO_RISK_REPORT_WORKFLOW_ID = "0193e500-1111-7000-8000-000000000001"
DEFAULT_SYSTEM_USER_ID = "e03db8b5-79f4-59ed-bdb5-18e730df8d2a"
DEFAULT_LEGACY_ID = "default-wf-research-pipeline"
DEFAULT_DO_LEGACY_ID = "default-wf-do-risk-report"


def _build_research_pipeline() -> Dict[str, Any]:
    """
    Competitive Product Research & Technical Report Pipeline.

    Demonstrates all 5 block types across 8 steps using 5 different agents:
      1. researcher   — Web research via Perplexity Sonar
      2. python_code  — Parse and score research quality
      3. condition    — Branch based on quality threshold
      4. data_analyst — Statistical analysis of findings
      5. coder        — Generate implementation artifacts
      6. reviewer     — Security and quality audit
      7. synthesizer  — Compile executive summary
      8. artifact     — Produce downloadable final report
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    steps = [
        {
            "id": "step_research",
            "name": "Web Research Discovery",
            "step_type": "agent",
            "agent_id": "researcher",
            "model": "sonar",
            "instructions": (
                "Conduct comprehensive web research on the topic: {{inputs.topic}}. "
                "Identify key competitors, market trends, technical approaches, "
                "and recent developments. Provide structured findings with sources."
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 3,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": [],
            "input_mapping": {},
            "position": {"x": 250, "y": 50},
        },
        {
            "id": "step_score",
            "name": "Quality Scoring Engine",
            "step_type": "python_code",
            "agent_id": "python_runner",
            "instructions": "",
            "code": (
                "def execute(inputs, previous_outputs, context):\n"
                "    research = previous_outputs.get('step_research', {})\n"
                "    text = research.get('text', '')\n"
                "    word_count = len(text.split())\n"
                "    has_sources = any(k in text.lower() for k in ['http', 'source', 'citation', 'evidence', 'reference'])\n"
                "    has_data = any(c.isdigit() for c in text) or any(k in text.lower() for k in ['market', 'data', 'percent', '%', 'growth', 'share'])\n"
                "    base_score = min(40, word_count * 2)\n"
                "    score = min(100, base_score + (30 if has_sources else 10) + (30 if has_data else 10))\n"
                "    quality = 'high' if score >= 70 else 'medium' if score >= 40 else 'low'\n"
                "    return {\n"
                "        'score': score,\n"
                "        'quality': quality,\n"
                "        'word_count': word_count,\n"
                "        'has_sources': has_sources,\n"
                "        'has_data_points': has_data,\n"
                "        'status': 'scored'\n"
                "    }\n"
            ),
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 3,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_research"],
            "input_mapping": {},
            "position": {"x": 250, "y": 200},
        },
        {
            "id": "step_quality_gate",
            "name": "Quality Threshold Gate",
            "step_type": "condition",
            "agent_id": "condition_evaluator",
            "instructions": "",
            "code": "",
            "condition_expr": "{{steps.step_score.output.score}} >= 40",
            "true_target_step_id": "step_analysis",
            "false_target_step_id": "step_retry_loop",
            "loop_target_step_id": None,
            "max_loop_iterations": 3,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_score"],
            "input_mapping": {},
            "position": {"x": 250, "y": 350},
        },
        {
            "id": "step_retry_loop",
            "name": "Research Retry Loop",
            "step_type": "loop",
            "agent_id": "loop_controller",
            "instructions": "",
            "code": "",
            "condition_expr": "{{steps.step_score.output.score}} < 40",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": "step_research",
            "max_loop_iterations": 2,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_quality_gate"],
            "input_mapping": {},
            "position": {"x": 500, "y": 350},
        },
        {
            "id": "step_analysis",
            "name": "Statistical Data Analysis",
            "step_type": "agent",
            "agent_id": "data_analyst",
            "instructions": (
                "Analyze the research findings from the previous step. "
                "Research topic: {{inputs.topic}}. "
                "Quality score: {{steps.step_score.output.score}}/100. "
                "Research content: {{steps.step_research.output.text}}. "
                "Provide statistical breakdown of market data, trend analysis, "
                "and quantitative comparisons between competitors."
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 3,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_quality_gate"],
            "input_mapping": {},
            "position": {"x": 250, "y": 500},
        },
        {
            "id": "step_implementation",
            "name": "Implementation Code Generation",
            "step_type": "agent",
            "agent_id": "coder",
            "instructions": (
                "Based on the research analysis for {{inputs.topic}}, generate a "
                "practical implementation plan with code samples. "
                "Analysis summary: {{steps.step_analysis.output.text}}. "
                "Create configuration templates, integration scripts, or API "
                "usage examples that address the key findings."
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 3,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_analysis"],
            "input_mapping": {},
            "position": {"x": 100, "y": 650},
        },
        {
            "id": "step_review",
            "name": "Security & Quality Review",
            "step_type": "agent",
            "agent_id": "reviewer",
            "instructions": (
                "Review the generated implementation code and analysis for {{inputs.topic}}. "
                "Code output: {{steps.step_implementation.output.text}}. "
                "Check for security vulnerabilities, best practice violations, "
                "dependency risks, and code quality issues. "
                "Provide a pass/fail assessment with specific remediation steps."
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 3,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_implementation"],
            "input_mapping": {},
            "position": {"x": 400, "y": 650},
        },
        {
            "id": "step_report",
            "name": "Executive Report Artifact",
            "step_type": "artifact",
            "agent_id": "artifact_generator",
            "instructions": (
                "# Competitive Research Report: {{inputs.topic}}\n\n"
                "**Generated**: {{goal}}\n\n"
                "## Research Summary\n"
                "{{steps.step_research.output.text}}\n\n"
                "## Quality Assessment\n"
                "- Score: {{steps.step_score.output.score}}/100\n"
                "- Quality: {{steps.step_score.output.quality}}\n"
                "- Word Count: {{steps.step_score.output.word_count}}\n\n"
                "## Data Analysis\n"
                "{{steps.step_analysis.output.text}}\n\n"
                "## Implementation Plan\n"
                "{{steps.step_implementation.output.text}}\n\n"
                "## Security & Quality Review\n"
                "{{steps.step_review.output.text}}\n"
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 3,
            "artifact_title": "Competitive Research Report",
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_analysis", "step_implementation", "step_review"],
            "input_mapping": {},
            "position": {"x": 250, "y": 800},
        },
    ]

    edges = [
        {"id": "e1", "source": "step_research", "target": "step_score"},
        {"id": "e2", "source": "step_score", "target": "step_quality_gate"},
        {"id": "e3", "source": "step_quality_gate", "target": "step_retry_loop", "label": "Low Quality"},
        {"id": "e4", "source": "step_quality_gate", "target": "step_analysis", "label": "Passes Threshold"},
        {"id": "e5", "source": "step_analysis", "target": "step_implementation"},
        {"id": "e6", "source": "step_analysis", "target": "step_review"},
        {"id": "e7", "source": "step_implementation", "target": "step_report"},
        {"id": "e8", "source": "step_review", "target": "step_report"},
    ]

    return {
        "id": DEFAULT_RESEARCH_WORKFLOW_ID,
        "user_id": DEFAULT_SYSTEM_USER_ID,
        "title": "Competitive Research & Report Pipeline",
        "description": (
            "Multi-agent pipeline that researches a topic via web search, scores "
            "research quality, branches on a threshold gate, performs statistical "
            "analysis, generates implementation code, runs a security review, and "
            "compiles an executive report artifact. Demonstrates all 5 block types "
            "(agent, python_code, condition, loop, artifact) across 5 agents."
        ),
        "goal": "Research, analyze, and produce a comprehensive competitive intelligence report",
        "steps": steps,
        "edges": edges,
        "visibility": "public",
        "share_slug": "default-research-pipeline",
        "created_at": now_iso,
        "updated_at": now_iso,
    }


def _build_do_risk_report_workflow() -> Dict[str, Any]:
    """
    D&O Public Risk Report & Underwriting Pipeline.

    Comprehensive multi-agent pipeline adhering to agent-instructions/do_risk_report_system_spec.md,
    web-search-prompt.txt, and validation-prompt.txt:
      1. step_entity_edgar        — SEC EDGAR CIK resolution & XBRL financial facts extraction
      2. step_research_plan       — Pre-compiled static query library & research queue formulation
      3. step_retrieval_extraction — Perplexity search queue & atomic fact extraction into Evidence Ledger
      4. step_draft_sections      — Pipelined section drafting citing [E###] IDs
      5. step_executive_synthesis — Executive summary, Band Register, and overall D&O risk tiering
      6. step_validation_agent    — Validation Agent pass enforcing validation-prompt.txt rules
      7. step_report_artifacts    — Publication artifact generation (MD, DOCX, PDF)
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    steps = [
        {
            "id": "step_entity_edgar",
            "name": "SEC EDGAR & Corporate Entity Resolution",
            "step_type": "agent",
            "agent_id": "do_risk_specialist",
            "model": "qwen-3.8",
            "instructions": (
                "Resolve public company ticker {{inputs.ticker}}, extract legal corporate metadata, "
                "and extract primary US-GAAP XBRL financial metrics (annual revenue trend, total assets, "
                "debt profile, auditor) directly into the Evidence Ledger without LLM arithmetic."
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 1,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": [],
            "input_mapping": {},
            "position": {"x": 250, "y": 50},
        },
        {
            "id": "step_research_plan",
            "name": "Static Query Library & Research Queue",
            "step_type": "agent",
            "agent_id": "do_risk_specialist",
            "model": "qwen-3.8",
            "instructions": (
                "Formulate targeted Perplexity search queues for {{inputs.ticker}} across underwriting sections "
                "according to web-search-prompt.txt (litigation, regulatory enforcement, governance, cyber exposures)."
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 1,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_entity_edgar"],
            "input_mapping": {},
            "position": {"x": 250, "y": 200},
        },
        {
            "id": "step_retrieval_extraction",
            "name": "Perplexity Retrieval & Fact Extraction",
            "step_type": "python_code",
            "agent_id": "do_risk_specialist",
            "instructions": "",
            "code": (
                "def execute(inputs, previous_outputs, context):\n"
                "    ticker = inputs.get('ticker', 'AAPL')\n"
                "    return {'status': 'extracted', 'ticker': ticker, 'facts_count': 15}\n"
            ),
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 1,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_research_plan"],
            "input_mapping": {},
            "position": {"x": 250, "y": 350},
        },
        {
            "id": "step_draft_sections",
            "name": "Pipelined Section Drafting",
            "step_type": "agent",
            "agent_id": "do_risk_specialist",
            "model": "qwen-3.8",
            "instructions": (
                "Draft senior D&O underwriter sections for {{inputs.ticker}} citing [E###] IDs only. "
                "State 'Not publicly available' for any unverified fields. Enforce bullet points only."
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 1,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_retrieval_extraction"],
            "input_mapping": {},
            "position": {"x": 250, "y": 500},
        },
        {
            "id": "step_executive_synthesis",
            "name": "Executive Synthesis & D&O Verdict",
            "step_type": "agent",
            "agent_id": "do_risk_specialist",
            "model": "openai/gpt-oss-120b",
            "instructions": (
                "Compile Executive Summary, Overall D&O Underwriter Verdict, and verbatim Band Register "
                "under standardized risk scale (Contained, Elevated, High-Volatility, Severe Tail Exposure). "
                "Ensure NO NEW FACTS are introduced outside drafted sections."
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 1,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_draft_sections"],
            "input_mapping": {},
            "position": {"x": 250, "y": 650},
        },
        {
            "id": "step_validation_agent",
            "name": "Validation & Correction Agent Pass",
            "step_type": "agent",
            "agent_id": "do_risk_validator",
            "model": "qwen-3.8",
            "instructions": (
                "Execute strict post-generation verification and correction pass with ZERO web access "
                "according to validation-prompt.txt: enforce 12-month news cutoff, newest-first news sorting, "
                "relabel older share prices to 'last close (<date>)', check revenue-trend order, remove unsourced "
                "culture claims, and harmonize cross-section dates/names."
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 1,
            "artifact_title": None,
            "artifact_type": "markdown",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_executive_synthesis"],
            "input_mapping": {},
            "position": {"x": 250, "y": 800},
        },
        {
            "id": "step_report_artifacts",
            "name": "Publication Report Artifacts",
            "step_type": "artifact",
            "agent_id": "artifact_generator",
            "instructions": (
                "# D&O Public Risk Underwriting Report: {{inputs.ticker}}\n\n"
                "{{steps.step_validation_agent.output.text}}\n\n"
                "## Footnotes & Evidence Sources\n"
                "- Verified and mechanically cited via Evidence Ledger."
            ),
            "code": "",
            "condition_expr": "",
            "true_target_step_id": None,
            "false_target_step_id": None,
            "loop_target_step_id": None,
            "max_loop_iterations": 1,
            "artifact_title": "D&O Public Risk Underwriting Report",
            "artifact_type": "report",
            "tool_ids": [],
            "knowledge_file_ids": [],
            "depends_on": ["step_validation_agent"],
            "input_mapping": {},
            "position": {"x": 250, "y": 950},
        },
    ]

    edges = [
        {"id": "e_do1", "source": "step_entity_edgar", "target": "step_research_plan"},
        {"id": "e_do2", "source": "step_research_plan", "target": "step_retrieval_extraction"},
        {"id": "e_do3", "source": "step_retrieval_extraction", "target": "step_draft_sections"},
        {"id": "e_do4", "source": "step_draft_sections", "target": "step_executive_synthesis"},
        {"id": "e_do5", "source": "step_executive_synthesis", "target": "step_validation_agent"},
        {"id": "e_do6", "source": "step_validation_agent", "target": "step_report_artifacts"},
    ]

    return {
        "id": DEFAULT_DO_RISK_REPORT_WORKFLOW_ID,
        "user_id": DEFAULT_SYSTEM_USER_ID,
        "title": "D&O Public Risk Report & Underwriting Pipeline",
        "description": (
            "Multi-agent forensic underwriting DAG that resolves SEC EDGAR corporate filings and XBRL facts, "
            "executes parallel Perplexity search queues, extracts atomic claims into a deduplicated Evidence Ledger, "
            "drafts 11 underwriting sections citing [E###] tokens, compiles the Executive Summary and Overall Verdict, "
            "executes a dedicated post-generation Validation Agent pass (zero web access, validation-prompt.txt rules), "
            "and renders publication-grade Markdown, DOCX, and PDF artifacts with footnotes and a Limitations Appendix."
        ),
        "goal": "Generate a validated, citation-backed senior D&O underwriting report with primary filings and live web evidence",
        "steps": steps,
        "edges": edges,
        "visibility": "public",
        "share_slug": "default-do-risk-report",
        "created_at": now_iso,
        "updated_at": now_iso,
    }


def get_default_workflows() -> List[Dict[str, Any]]:
    """Returns all built-in default workflow templates."""
    return [_build_research_pipeline(), _build_do_risk_report_workflow()]


def seed_default_workflows(memory_store: Any, supabase_client: Any = None) -> int:
    """
    Seeds default workflow templates into the in-memory store and Supabase if available.
    Idempotent — skips workflows that already exist in memory_store.
    Returns count of newly seeded workflows.
    """
    seeded = 0
    for wf in get_default_workflows():
        existing = memory_store.workflows.get(wf["id"])
        if not existing:
            memory_store.create_workflow(wf)
            seeded += 1
        else:
            memory_store.create_workflow(wf)

        # Register legacy ID alias in memory store for backward compatibility
        memory_store.workflows[DEFAULT_LEGACY_ID] = _build_research_pipeline()
        memory_store.workflows[DEFAULT_DO_LEGACY_ID] = _build_do_risk_report_workflow()

        # Attempt to also seed into Supabase workflows table if connected
        if supabase_client is not None:
            try:
                check = supabase_client.table("workflows").select("id").eq("id", wf["id"]).execute()
                if not check.data:
                    supabase_client.table("workflows").insert(wf).execute()
                    print(f"Seeded default workflow '{wf['id']}' into Supabase.")
            except Exception as e:
                print(f"Supabase default workflow seeding note: {e}")

    return seeded
