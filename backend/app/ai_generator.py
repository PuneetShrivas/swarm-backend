import os
import re
import json
import uuid
from typing import Dict, Any, List, Optional


def get_gemini_client():
    """Initializes and returns the google-genai Client if API key is configured."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key or api_key.strip() == "" or api_key.strip().startswith("your-"):
        return None, None
    try:
        from google import genai
        client = genai.Client(api_key=api_key.strip())
        return client, api_key.strip()
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini client for AI generation: {e}")
        return None, None


def _clean_json_markdown(text: str) -> str:
    """Strips markdown code fences (```json ... ```) from LLM output."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


# -------------------------------------------------------------
# 1. AI Workflow Generator
# -------------------------------------------------------------

def generate_workflow_spec(
    prompt: str,
    available_agents: Optional[List[Dict[str, Any]]] = None,
    available_tools: Optional[List[Dict[str, Any]]] = None,
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Generates a structured multi-step autonomous workflow specification
    using Google Gemini 2.5 (with an intelligent fallback if offline).
    """
    if client is None:
        client, _ = get_gemini_client()
    agent_roster_summary = ""
    if available_agents:
        agent_roster_summary = "\n".join(
            f"- ID: {a.get('id')}, Name: {a.get('name')}, Role: {a.get('role', 'Specialist')}"
            for a in available_agents
        )
    else:
        agent_roster_summary = (
            "- ID: researcher, Role: Deep investigative research & evidence gathering\n"
            "- ID: coder, Role: Production software development & system engineering\n"
            "- ID: reviewer, Role: Security audits & code review\n"
            "- ID: data_analyst, Role: Numerical calculations & statistics\n"
            "- ID: synthesizer, Role: Technical briefings & executive documentation\n"
            "- ID: orchestrator, Role: Swarm routing & goal decomposition"
        )

    tools_summary = ""
    if available_tools:
        tools_summary = "\n".join(
            f"- Tool ID: {t.get('id')}, Name: {t.get('name')}, Description: {t.get('description')}"
            for t in available_tools
        )
    else:
        tools_summary = "No custom script tools currently attached."

    system_instruction = (
        "You are an expert AI Autonomous Workflow Architect. Your mission is to take user requirements "
        "and generate a complete, valid multi-step directed acyclic graph (DAG) workflow pipeline.\n"
        "Supported Step Types:\n"
        "- 'agent': General reasoning step delegated to a specialist agent.\n"
        "- 'condition': Branching decision block with 'condition_expr', 'true_target_step_id', and 'false_target_step_id'.\n"
        "- 'python_code': Sandboxed Python script execution block with 'code'.\n"
        "- 'loop': Iteration block with 'loop_target_step_id' and 'max_loop_iterations'.\n"
        "- 'artifact': Structured deliverable generator with 'artifact_title' and 'artifact_type' ('report', 'markdown', 'code', 'json').\n\n"
        "Return ONLY a raw JSON object matching the following structure without markdown explanation:\n"
        "{\n"
        '  "title": "Concise, professional workflow title (max 50 chars)",\n'
        '  "description": "1-2 sentence overview of what the workflow accomplishes",\n'
        '  "goal": "Clear, specific high-level objective of the workflow",\n'
        '  "steps": [\n'
        "    {\n"
        '      "id": "step_1",\n'
        '      "name": "Human-readable step name",\n'
        '      "step_type": "agent",\n'
        '      "agent_id": "Must match one of the available agent IDs (if step_type is agent)",\n'
        '      "model": "Use \'sonar\' for websearch, finding stock prices, live data, news, and market quotes; otherwise \'gemini-3.8-flash\'",\n'
        '      "instructions": "Detailed prompt template using {{goal}}, {{inputs.query}}, or {{steps.<prev_step_id>.output.text}}",\n'
        '      "tool_ids": [],\n'
        '      "knowledge_file_ids": [],\n'
        '      "depends_on": []\n'
        "    }\n"
        "  ],\n"
        '  "edges": [\n'
        '    {"source": "step_1", "target": "step_2"}\n'
        "  ]\n"
        "}\n\n"
        "CRITICAL MODEL DIRECTIVE: When creating workflow steps that involve web search, real-time data, breaking news, or live web discovery, ALWAYS assign agent_id 'researcher' or specify model 'sonar' (Perplexity Sonar). Perplexity is the mandatory model for all live information and web search tasks.\n\n"
        "CRITICAL ORCHESTRATION DIRECTIVE: For all multi-step workflows, the final step MUST ALWAYS be a synthesis step assigned to agent 'synthesizer' to consolidate previous step outputs and deliver a cohesive final output directly in line with the high-level workflow goal.\n\n"
        "GENERAL DATA ANALYST DIRECTIVE: The data_analyst agent is a general-purpose numerical, statistical, and tabular analysis agent across all domains. Do NOT inject scenario-specific or finance-specific constraints (e.g. price-to-earnings, stock quotes) into data analyst steps unless explicitly requested by the user.\n\n"
        f"Available Agents to assign:\n{agent_roster_summary}\n\n"
        f"Available Script Tools:\n{tools_summary}\n"
    )

    if client:
        try:
            from google.genai import types
            response = client.models.generate_content(
                model=os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
                contents=[types.Part.from_text(text=f"User workflow requirements: {prompt}")],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                ),
            )
            raw_text = response.text or ""
            cleaned_json = _clean_json_markdown(raw_text)
            data = json.loads(cleaned_json)
            if "title" in data and "steps" in data and isinstance(data["steps"], list):
                # Ensure all required defaults exist
                for idx, s in enumerate(data["steps"]):
                    if not s.get("id"):
                        s["id"] = f"step_{idx+1}"
                    if not s.get("name"):
                        s["name"] = f"Step {idx+1}"
                    if not s.get("step_type"):
                        s["step_type"] = "agent"
                    if s["step_type"] == "agent" and not s.get("agent_id"):
                        s["agent_id"] = "orchestrator"
                    if not s.get("instructions"):
                        s["instructions"] = f"Execute action for: {{{{goal}}}}"
                    if "tool_ids" not in s:
                        s["tool_ids"] = []
                    if "knowledge_file_ids" not in s:
                        s["knowledge_file_ids"] = []
                    if "depends_on" not in s:
                        s["depends_on"] = [data["steps"][idx-1]["id"]] if idx > 0 else []

                    # Enforce Perplexity ('sonar') on websearch, stock prices, and live information tasks
                    combined_step_text = f"{s.get('name', '')} {s.get('instructions', '')}".lower()
                    if any(k in combined_step_text for k in ["stock", "price", "market", "ticker", "web search", "websearch", "search", "live info", "news", "quote", "crypto", "btc", "current"]):
                        if s.get("step_type") == "agent":
                            s["agent_id"] = "researcher"
                        s["model"] = "sonar"
                    elif s.get("agent_id") == "researcher":
                        s["model"] = "sonar"

                # Ensure multi-step workflows conclude with a goal-aligned synthesis step
                if len(data["steps"]) >= 2 and data["steps"][-1].get("agent_id") != "synthesizer":
                    last_step_id = data["steps"][-1].get("id", f"step_{len(data['steps'])}")
                    synth_id = f"step_{len(data['steps']) + 1}"
                    data["steps"].append({
                        "id": synth_id,
                        "name": "Goal-Aligned Final Synthesis",
                        "step_type": "agent",
                        "agent_id": "synthesizer",
                        "instructions": f"Synthesize all preceding step outputs into a cohesive, structured final response directly fulfilling the user's goal: '{prompt}'. Ensure actionable takeaways and thorough satisfaction of the initial objective: {{{{steps.{last_step_id}.output.text}}}}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "depends_on": [last_step_id],
                    })

                if "edges" not in data or not isinstance(data["edges"], list) or not data["edges"]:
                    edges = []
                    for s in data["steps"]:
                        for dep in s.get("depends_on", []):
                            edges.append({"source": dep, "target": s["id"]})
                    data["edges"] = edges
                return data
        except Exception as e:
            print(f"Gemini workflow generation error: {e}, falling back to deterministic generator.")

    # ----------------- Deterministic Fallback Generator -----------------
    prompt_lower = prompt.lower()
    slug_id = uuid.uuid4().hex[:6]

    if any(k in prompt_lower for k in ["stock", "price", "ticker", "market quote", "share price", "equity", "crypto", "btc", "websearch", "live info"]):
        return {
            "title": f"Live Market & Stock Intelligence Pipeline ({slug_id})",
            "description": "Extracts real-time market data, quotes, and financial indicators using Perplexity Sonar live search.",
            "goal": prompt or "Retrieve real-time market data, ticker prices, and synthesize financial trends.",
            "steps": [
                {
                    "id": "step_1",
                    "name": "Live Stock Price & Market Discovery",
                    "step_type": "agent",
                    "agent_id": "researcher",
                    "model": "sonar",
                    "instructions": "Search live financial sources and market quotes for current stock prices, volume, and valuation metrics: {{inputs.query}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Quantitative Valuation Analysis",
                    "step_type": "agent",
                    "agent_id": "data_analyst",
                    "instructions": "Analyze numerical market data, calculate percentage changes, ratios, and variance based on live quotes: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Market Intelligence Briefing",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize all verified quotes and numerical metrics into an executive briefing in direct alignment with the goal '{prompt}': {{{{steps.step_2.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": ["step_2"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ],
        }

    if any(k in prompt_lower for k in ["audit", "security", "vulnerability", "cve", "owasp", "pen test"]):
        return {
            "title": f"Security & Vulnerability Audit Pipeline ({slug_id})",
            "description": "Scans codebases and configurations for security risks, validates vulnerabilities, and produces a compliance remediation plan.",
            "goal": prompt or "Conduct comprehensive vulnerability audit and security remediation.",
            "steps": [
                {
                    "id": "step_1",
                    "name": "Static Vulnerability Scan",
                    "step_type": "agent",
                    "agent_id": "coder",
                    "instructions": "Analyze code assets for potential security flaws, injection vectors, and hardcoded secrets: {{inputs.query}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "OWASP Security Compliance Audit",
                    "step_type": "agent",
                    "agent_id": "reviewer",
                    "instructions": "Evaluate findings from previous step against OWASP standards and calculate risk severity: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Remediation & Executive Briefing",
                    "step_type": "artifact",
                    "artifact_title": "Security Remediation Plan & Audit Report",
                    "artifact_type": "report",
                    "instructions": "Synthesize security findings into an executive report with actionable remediation steps: {{steps.step_2.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": ["step_2"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ],
        }

    if any(k in prompt_lower for k in ["refactor", "code review", "git", "clean code", "lint", "pr review"]):
        return {
            "title": f"Automated Code Quality & Refactor Pipeline ({slug_id})",
            "description": "Audits codebase syntax, complexity, and maintainability, branching conditionally on quality thresholds.",
            "goal": prompt or "Audit code quality and produce automated refactor suggestions.",
            "steps": [
                {
                    "id": "step_1",
                    "name": "Static Analysis & Complexity Audit",
                    "step_type": "agent",
                    "agent_id": "coder",
                    "instructions": "Audit codebase syntax, cyclomatic complexity, and test coverage: {{inputs.query}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Quality Threshold Evaluation",
                    "step_type": "condition",
                    "instructions": "Verify if code maintainability score satisfies production quality gate: {{steps.step_1.output.score}} >= 80",
                    "condition_expr": "{{steps.step_1.output.score}} >= 80",
                    "true_target_step_id": "step_3",
                    "false_target_step_id": "step_3",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Refactor Delivery & Executive Report",
                    "step_type": "artifact",
                    "artifact_title": "Automated Code Review & Refactor Specifications",
                    "artifact_type": "markdown",
                    "instructions": "Synthesize verified code diffs and documentation: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": ["step_2"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ],
        }

    if any(k in prompt_lower for k in ["data", "stats", "financial", "csv", "table", "metrics", "analytics"]):
        return {
            "title": f"Data Analytics & Insights Engine ({slug_id})",
            "description": "Performs statistical analysis, computes distribution trends, and outputs an executive briefing.",
            "goal": prompt or "Process tabular metrics and generate statistical summary report.",
            "steps": [
                {
                    "id": "step_1",
                    "name": "Quantitative Metrics Extraction",
                    "step_type": "agent",
                    "agent_id": "data_analyst",
                    "instructions": "Extract key numerical indicators, distributions, and variance metrics for: {{inputs.query}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Strategic Findings Synthesis",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": "Transform quantitative metrics into executive insights with trend graphs: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "depends_on": ["step_1"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
            ],
        }

    # Default General Research & Delivery Pipeline
    return {
        "title": f"Investigation & Synthesis Pipeline ({slug_id})",
        "description": "Conducts deep multi-agent research on user objectives and delivers a structured executive briefing.",
        "goal": prompt or "Investigate target domain and synthesize structured deliverable.",
        "steps": [
            {
                "id": "step_1",
                "name": "Investigative Research & Evidence Gathering",
                "step_type": "agent",
                "agent_id": "researcher",
                "model": "sonar",
                "instructions": "Conduct deep investigative discovery regarding: {{goal}} with input query: {{inputs.query}}",
                "tool_ids": [],
                "knowledge_file_ids": [],
                "depends_on": [],
            },
            {
                "id": "step_2",
                "name": "Technical Verification & Solution Design",
                "step_type": "agent",
                "agent_id": "coder",
                "instructions": "Verify technical feasibility and formulate solution specifications based on: {{steps.step_1.output.text}}",
                "tool_ids": [],
                "knowledge_file_ids": [],
                "depends_on": ["step_1"],
            },
            {
                "id": "step_3",
                "name": "Executive Synthesis & Delivery",
                "step_type": "artifact",
                "artifact_title": "Executive Strategic Briefing",
                "artifact_type": "report",
                "instructions": "Compile research and technical specs into a final verified executive deliverable: {{steps.step_2.output.text}}",
                "tool_ids": [],
                "knowledge_file_ids": [],
                "depends_on": ["step_2"],
            },
        ],
        "edges": [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_3"},
        ],
    }


# -------------------------------------------------------------
# 2. AI Agent Generator
# -------------------------------------------------------------

def generate_agent_spec(
    prompt: str,
    available_tools: Optional[List[Dict[str, Any]]] = None,
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Generates a complete user agent profile (persona, role, system prompt,
    temperature, model, and recommended tool linkages) from user requirements.
    """
    if client is None:
        client, _ = get_gemini_client()
    tools_summary = ""
    if available_tools:
        tools_summary = "\n".join(
            f"- Tool ID: {t.get('id')}, Name: {t.get('name')}, Description: {t.get('description')}"
            for t in available_tools
        )
    else:
        tools_summary = "No custom script tools currently attached."

    system_instruction = (
        "You are an expert AI Persona & Agent System Architect. Given a user request for an AI agent, "
        "you construct a complete, professional, highly capable agent definition.\n"
        "Return ONLY a raw JSON object matching the following structure without markdown explanations:\n"
        "{\n"
        '  "id": "slugified-unique-id (e.g. agent-sql-optimizer)",\n'
        '  "name": "Professional display name (e.g. SQL Database Optimizer)",\n'
        '  "role": "Concise 3-5 word role description",\n'
        '  "description": "2-3 sentence overview of this agent\'s specialization and scope",\n'
        '  "system_prompt": "Comprehensive markdown system prompt defining persona, core tasks, operational guidelines, constraints, and structured output expectations",\n'
        '  "model": "gemini-3.8-flash",\n'
        '  "temperature": 0.2,\n'
        '  "icon": "Lucide icon name (e.g. Database, ShieldCheck, Search, Code2, Bot, Sparkles, Terminal)",\n'
        '  "skills": [{"id": "skill_1", "name": "Core Domain Expertise"}]\n'
        "}\n\n"
        f"Available script tools to consider:\n{tools_summary}\n"
    )

    if client:
        try:
            from google.genai import types
            response = client.models.generate_content(
                model=os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
                contents=[types.Part.from_text(text=f"User desired agent: {prompt}")],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                ),
            )
            raw_text = response.text or ""
            cleaned_json = _clean_json_markdown(raw_text)
            data = json.loads(cleaned_json)
            if "name" in data and "system_prompt" in data:
                if not data.get("id"):
                    data["id"] = f"agent-{uuid.uuid4().hex[:8]}"
                return data
        except Exception as e:
            print(f"Gemini agent generation error: {e}, falling back to deterministic generator.")

    # ----------------- Deterministic Fallback Generator -----------------
    prompt_clean = prompt.strip()
    slug_name = re.sub(r"[^a-z0-9]+", "-", prompt_clean.lower())[:24].strip("-") or "custom"
    agent_id = f"agent-{slug_name}-{uuid.uuid4().hex[:4]}"

    # Choose persona archetype based on keywords
    p_lower = prompt_clean.lower()
    if any(k in p_lower for k in ["sql", "database", "query", "postgres"]):
        return {
            "id": agent_id,
            "name": "Database & Query Optimizer Specialist",
            "role": "SQL Query Tuning & Schema Architect",
            "description": "Specializes in relational database performance tuning, index strategy, and query plan optimization.",
            "system_prompt": (
                f"# Identity: Database & Query Optimizer Specialist\n\n"
                f"You are a principal database engineer tasked with: {prompt_clean}\n\n"
                f"## Core Directives:\n"
                f"1. Analyze query execution plans, identify sequential scans, and recommend selective indexing.\n"
                f"2. Audit schema constraints, normalization levels, and connection pooling configurations.\n"
                f"3. Produce optimized SQL statements with before-and-after complexity estimates.\n"
                f"4. Format all SQL code with proper indentation and capitalized keywords."
            ),
            "model": "gemini-3.8-flash",
            "temperature": 0.2,
            "icon": "Database",
            "skills": [
                {"id": "query_optimization", "name": "SQL Plan Optimization"},
                {"id": "index_tuning", "name": "B-Tree Index Tuning"},
            ],
        }

    if any(k in p_lower for k in ["security", "audit", "cve", "auth", "crypto"]):
        return {
            "id": agent_id,
            "name": "Security & Vulnerability Auditor",
            "role": "Application Security & Threat Analyst",
            "description": "Audits application architectures, APIs, and dependencies for security flaws and zero-trust compliance.",
            "system_prompt": (
                f"# Identity: Security & Vulnerability Auditor\n\n"
                f"You are a senior security researcher tasked with: {prompt_clean}\n\n"
                f"## Core Directives:\n"
                f"1. Identify potential OWASP Top 10 vulnerabilities (SQLi, XSS, SSRF, broken auth).\n"
                f"2. Calculate CVSS severity scores for identified issues.\n"
                f"3. Formulate zero-trust architectural remediations.\n"
                f"4. Ensure sensitive data is encrypted at rest and in transit."
            ),
            "model": "gemini-3.8-flash",
            "temperature": 0.1,
            "icon": "ShieldCheck",
            "skills": [
                {"id": "vulnerability_audit", "name": "Vulnerability Assessment"},
                {"id": "threat_modeling", "name": "Threat Modeling"},
            ],
        }

    # Default General Specialist
    words = [w.capitalize() for w in prompt_clean.split()[:4]]
    display_name = " ".join(words) + " Specialist" if words else "Domain Specialist"

    return {
        "id": agent_id,
        "name": display_name,
        "role": f"{prompt_clean[:32]} Expert",
        "description": f"Specialized AI agent configured to execute: {prompt_clean}",
        "system_prompt": (
            f"# Identity: {display_name}\n\n"
            f"You are a highly capable AI agent built for: {prompt_clean}\n\n"
            f"## Operational Guidelines:\n"
            f"1. Deliver accurate, verified, and direct answers.\n"
            f"2. Cite evidence, reference specific methodologies, and explain assumptions clearly.\n"
            f"3. Use structured Markdown with bold headers and concise bullet points."
        ),
        "model": "gemini-3.8-flash",
        "temperature": 0.3,
        "icon": "Bot",
        "skills": [
            {"id": "domain_expertise", "name": "Domain Expertise"},
            {"id": "structured_synthesis", "name": "Structured Synthesis"},
        ],
    }


def synthesize_on_the_fly_workflow(
    prompt: str,
    target_agent_id: Optional[str] = None,
    available_agents: Optional[List[Dict[str, Any]]] = None,
    available_tools: Optional[List[Dict[str, Any]]] = None,
    attached_artifacts: Optional[List[Dict[str, Any]]] = None,
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Synthesizes an on-the-fly workflow specification for user chat queries.
    - If a specific agent is targeted or the query is simple, generates a 1-agent workflow.
    - If the query is composite, decomposes it into a multi-agent DAG (e.g. Researcher -> Data Analyst -> Synthesizer).
    - Preserves specialized model configs (e.g. Researcher uses Perplexity Sonar 'sonar').
    - Returns an ephemeral workflow dictionary ready for in-memory execution by WorkflowExecutionEngine.
    """
    prompt_clean = prompt.strip()
    prompt_lower = prompt_clean.lower()
    slug_id = uuid.uuid4().hex[:6]
    art_ids = [a.get("id") for a in (attached_artifacts or []) if a and a.get("id")]

    # 1. Targeted Specific Agent Execution (1-Step Workflow)
    if target_agent_id and target_agent_id != "orchestrator":
        model_override = "sonar" if target_agent_id == "researcher" else None
        agent_name = target_agent_id.replace("_", " ").title()
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"{agent_name} Execution Plan ({slug_id})",
            "description": f"Direct single-agent workflow for {agent_name}.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": False,
            "steps": [
                {
                    "id": "step_1",
                    "name": f"{agent_name} Task",
                    "step_type": "agent",
                    "agent_id": target_agent_id,
                    "model": model_override,
                    "instructions": prompt_clean,
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                }
            ],
            "edges": [],
        }

    # 2. Composite Multi-Agent Workflows Decomposition
    # A) Live Market & Financial Intelligence
    has_market_kw = any(k in prompt_lower for k in [
        "stock", "ticker", "market quote", "share price", "equity", "crypto", "btc",
        "financial metric", "p/e ratio", "valuation", "nasdaq", "dow", "s&p"
    ])
    has_analysis_kw = any(k in prompt_lower for k in [
        "analysis", "analyze", "compare", "valuation", "ratio", "briefing", "summary",
        "financial", "trend", "forecast", "insight"
    ])
    if has_market_kw and (has_analysis_kw or len(prompt_clean.split()) > 6):
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Live Market & Valuation Intelligence Pipeline ({slug_id})",
            "description": "Multi-agent research and valuation analysis using Perplexity Sonar and Groq Qwen.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Live Market Data & Stock Discovery",
                    "step_type": "agent",
                    "agent_id": "researcher",
                    "model": "sonar",
                    "instructions": f"Search live financial sources and market quotes for current stock prices, volume, and valuation metrics: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Quantitative Valuation Analysis",
                    "step_type": "agent",
                    "agent_id": "data_analyst",
                    "instructions": f"Perform quantitative analysis on the discovered data, calculate key metrics, identify trends and anomalies, and structure findings: {{{{steps.step_1.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Market Intelligence Briefing",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize all verified discoveries and quantitative evaluations into a cohesive final briefing directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_2.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_2"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ],
        }

    # B) Research + Production Code + Quality Review + Goal Synthesis
    has_research_kw = any(k in prompt_lower for k in ["research", "investigate", "find out", "learn about", "look up", "documentation", "spec"])
    has_code_kw = any(k in prompt_lower for k in ["code", "implement", "python", "script", "program", "build", "develop", "function", "api"])
    if has_research_kw and has_code_kw:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Technical Research, Engineering & Code Review Pipeline ({slug_id})",
            "description": "Collaborative research, production implementation, security review, and goal-aligned synthesis.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Technical Specifications & Documentation Discovery",
                    "step_type": "agent",
                    "agent_id": "researcher",
                    "model": "sonar",
                    "instructions": f"Gather official documentation, API specifications, and architecture requirements for: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Production Software Implementation",
                    "step_type": "agent",
                    "agent_id": "coder",
                    "instructions": "Implement robust, complete production code based on technical specifications: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Code Review & Security Verification",
                    "step_type": "agent",
                    "agent_id": "reviewer",
                    "instructions": "Perform code review, security audit, and edge-case validation for the implementation: {{steps.step_2.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_2"],
                },
                {
                    "id": "step_4",
                    "name": "Technical Synthesis & Usage Guide",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize technical implementation details, architecture overview, security review results, and execution instructions into a cohesive final response directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_3.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_3"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
                {"source": "step_3", "target": "step_4"},
            ],
        }

    # C) Security Vulnerability Audit & Hardened Refactor + Synthesis
    has_sec_kw = any(k in prompt_lower for k in ["security", "vulnerability", "audit", "cve", "owasp", "pen test", "penetration", "exploit"])
    if has_sec_kw:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Security Audit, Remediation & Briefing Pipeline ({slug_id})",
            "description": "Comprehensive security audit, hardened implementation, and executive synthesis.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Vulnerability & Threat Assessment",
                    "step_type": "agent",
                    "agent_id": "reviewer",
                    "instructions": f"Conduct thorough vulnerability analysis and security audit: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Hardened Remediation Implementation",
                    "step_type": "agent",
                    "agent_id": "coder",
                    "instructions": "Implement secure code remediating all identified audit findings: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Security Remediation & Executive Briefing",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize security audit findings, vulnerability remediations, and defensive best practices into a cohesive final response directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_2.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_2"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ],
        }

    # D) Data Analysis & Document / Dataset Export
    has_data_kw = any(k in prompt_lower for k in ["data", "dataset", "statistics", "numbers", "sales", "metrics", "calculate"])
    has_file_kw = any(k in prompt_lower for k in ["csv", "excel", "xlsx", "pdf", "report", "spreadsheet", "file", "download"])
    if has_data_kw and has_file_kw:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Data Analysis & File Export Pipeline ({slug_id})",
            "description": "Calculates statistics and exports formatted downloadable datasets or documents.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Statistical & Numerical Analysis",
                    "step_type": "agent",
                    "agent_id": "data_analyst",
                    "instructions": f"Analyze data and numerical parameters, calculate descriptive metrics, identify patterns, and structure clean data: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Formatted File & Report Generation",
                    "step_type": "agent",
                    "agent_id": "file_creator",
                    "instructions": "Generate formatted downloadable file incorporating numerical analysis: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Dataset Summary & Verification",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize all analytical metrics and generated file artifact details into a cohesive final response directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_2.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_2"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ],
        }

    # E) In-Depth Research & Executive Synthesis
    has_deep_kw = any(k in prompt_lower for k in [
        "deep dive", "in-depth", "comprehensive", "comparative", "compare",
        "executive summary", "detailed briefing", "investigate", "explain in detail"
    ])
    if has_deep_kw or len(prompt_clean.split()) > 14:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Deep Investigation & Executive Synthesis Pipeline ({slug_id})",
            "description": "Multi-agent deep research and executive briefing synthesis.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Domain Discovery & Evidence Gathering",
                    "step_type": "agent",
                    "agent_id": "researcher",
                    "model": "sonar",
                    "instructions": f"Gather evidence, background context, and current developments: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Executive Synthesis & Strategic Briefing",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Consolidate research findings and evidence into a comprehensive, cohesive final response directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_1.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
            ],
        }

    # 3. Aggressive Multi-Agent Workflow Decompositions
    # F) Structured File Generation & Tabular Data Architecture Workflow (3 Steps)
    has_file_gen = any(k in prompt_lower for k in [
        "create file", "generate csv", "make csv", "generate pdf", "generate pptx", "excel",
        "xlsx", "spreadsheet", "table", "dataset", "generate file", "make file", "csv file",
        "word document", "presentation", "export file"
    ])
    if has_file_gen:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Tabular Architecture & File Generation Pipeline ({slug_id})",
            "description": "Collaborative pipeline to structure normalized tabular data, generate formatted file artifacts, and synthesize takeaways.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Data Schema & Tabular Normalization",
                    "step_type": "agent",
                    "agent_id": "data_analyst",
                    "instructions": f"Analyze query requirements, design clean column schemas, calculate metrics, and structure normalized tabular data with typed columns and headers: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Production File & Spreadsheet Synthesis",
                    "step_type": "agent",
                    "agent_id": "file_creator",
                    "instructions": "Generate formatted production file artifact (native Excel spreadsheet table with openpyxl, CSV, PDF, or presentation) incorporating structured tabular data: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Artifact Quality & Executive Summary",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Review generated file artifact, summarize column structure, row counts, key insights, and file access instructions into a cohesive final response directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_2.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_2"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ],
        }

    # G) Software Engineering, Implementation & Quality Review Workflow (3 Steps)
    has_coding = bool(re.search(
        r"\b(code|coding|function|python|javascript|typescript|sql|bug|refactor|algorithm|script|program|class|method|api|backend|frontend|unit test|write code|fix code)\b",
        prompt_lower
    ))
    if has_coding:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Software Implementation & Quality Review Pipeline ({slug_id})",
            "description": "Multi-agent engineering workflow implementing robust code, auditing security and edge-cases, and generating usage guides.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Production Code Implementation",
                    "step_type": "agent",
                    "agent_id": "coder",
                    "instructions": f"Design and implement production-ready code with complete algorithms, typing, and error handling for: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Code Review & Security Audit",
                    "step_type": "agent",
                    "agent_id": "reviewer",
                    "instructions": "Conduct code review, security audit, edge-case analysis, and verification: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Technical Documentation & Instructions",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize technical implementation details, architecture notes, security review results, and execution instructions into a cohesive final response directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_2.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_2"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ],
        }

    # H) Real-Time Research, Fact Verification & Synthesis Workflow (3 Steps)
    has_search = any(k in prompt_lower for k in [
        "web search", "websearch", "search", "latest", "news", "price", "who is", "when did",
        "current", "recent", "lookup", "find", "trends", "what happened"
    ])
    if has_search:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Live Web Research & Fact Synthesis Pipeline ({slug_id})",
            "description": "Multi-agent research gathering verified live web evidence and synthesizing comprehensive briefings.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Live Web Discovery & Evidence Gathering",
                    "step_type": "agent",
                    "agent_id": "researcher",
                    "model": "sonar",
                    "instructions": f"Execute live web search to gather authoritative citations, verified facts, and recent developments: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Comparative Analysis & Fact Verification",
                    "step_type": "agent",
                    "agent_id": "data_analyst",
                    "instructions": "Analyze research findings, extract key metrics, structure comparative facts, and check data consistency: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Executive Synthesis & Strategic Briefing",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize verified findings, citations, and analytical comparisons into a cohesive, comprehensive final response directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_2.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_2"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ],
        }

    # I) Quantitative Analytics & Statistical Evaluation Workflow (2 Steps)
    has_math = bool(re.search(
        r"\b(math|calculate|average|median|statistics|analytics|percentage|variance|forecast|sum|formula|computation)\b",
        prompt_lower
    ))
    if has_math:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Quantitative Analytics & Statistical Pipeline ({slug_id})",
            "description": "Evaluates numerical metrics, executes computations, and formats structured findings.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Numerical Computation & Statistical Analysis",
                    "step_type": "agent",
                    "agent_id": "data_analyst",
                    "instructions": f"Extract numerical parameters, execute statistical calculations, and structure data: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Executive Analytics Briefing",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Translate numerical results, statistical analyses, and structured data into a cohesive, comprehensive final briefing directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_1.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
            ],
        }

    # J) Document Ingestion, Schema Extraction & RAG Pipeline (3 Steps)
    has_parse = any(k in prompt_lower for k in [
        "parse", "inspect", "extract schema", "rag", "ingest", "read file", "unstructured"
    ])
    if has_parse:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Document Ingestion & Schema Extraction Pipeline ({slug_id})",
            "description": "Extracts structured tables and metadata from documents, analyzing semantic patterns.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Document Parsing & Schema Extraction",
                    "step_type": "agent",
                    "agent_id": "file_parser",
                    "instructions": f"Parse context files, extract text schemas, tabular data, and key entities: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Structured Data Synthesis",
                    "step_type": "agent",
                    "agent_id": "data_analyst",
                    "instructions": "Analyze parsed document contents, organize schema, and summarize key data: {{steps.step_1.output.text}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Document Insights Synthesis",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize all parsed document contents, structured schemas, and analytical findings into a cohesive, comprehensive final response directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_2.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_2"],
                },
            ],
            "edges": [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ],
        }

    # K) Conversational Greetings Check (Single Agent Step only for trivial greetings)
    is_trivial_greeting = prompt_lower.strip("!.? ") in [
        "hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening",
        "howdy", "sup", "yo", "who are you", "what can you do", "help"
    ] or len(prompt_clean.split()) <= 2

    if is_trivial_greeting:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"General Assistant Turn ({slug_id})",
            "description": "Direct response for conversational greeting.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": False,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Conversational Response",
                    "step_type": "agent",
                    "agent_id": "general_assistant",
                    "instructions": prompt_clean,
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                }
            ],
            "edges": [],
        }

    # L) General Knowledge Exploration & Synthesis Workflow (2 Steps for all other queries)
    return {
        "id": f"ephemeral_wf_{slug_id}",
        "title": f"Coordinated Knowledge & Synthesis Pipeline ({slug_id})",
        "description": "Multi-agent exploratory research and comprehensive synthesis pipeline.",
        "goal": prompt_clean,
        "is_ephemeral": True,
        "is_multi_step": True,
        "steps": [
            {
                "id": "step_1",
                "name": "Domain Exploration & Concept Analysis",
                "step_type": "agent",
                "agent_id": "general_assistant",
                "instructions": f"Analyze core principles, background context, and nuanced perspectives for: {prompt_clean}",
                "tool_ids": [],
                "knowledge_file_ids": [],
                "attached_artifact_ids": art_ids,
                "depends_on": [],
            },
            {
                "id": "step_2",
                "name": "Cohesive Synthesis & Executive Response",
                "step_type": "agent",
                "agent_id": "synthesizer",
                "instructions": f"Synthesize a comprehensive, polished response with structured headings, bullet points, and actionable takeaways directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_1.output.text}}}}",
                "tool_ids": [],
                "knowledge_file_ids": [],
                "attached_artifact_ids": [],
                "depends_on": ["step_1"],
            },
        ],
        "edges": [
            {"source": "step_1", "target": "step_2"},
        ],
    }
