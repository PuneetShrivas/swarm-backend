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
            "- ID: researcher, Role: Live web search, cited factual evidence & current data (uses Perplexity Sonar)\n"
            "- ID: coder, Role: Production software development & system engineering\n"
            "- ID: reviewer, Role: Security audits & code review\n"
            "- ID: data_analyst, Role: Universal numerical calculations & statistical analysis across all domains\n"
            "- ID: synthesizer, Role: Goal-aligned briefings & deliverable consolidation\n"
            "- ID: file_creator, Role: Document & downloadable file synthesis (PDF, PPTX, DOCX, XLSX, CSV)\n"
            "- ID: file_parser, Role: Document extraction, indexing & RAG retrieval\n"
            "- ID: writer, Role: Content, editorial & copywriting specialist for articles, essays, and communication\n"
            "- ID: planner, Role: Strategic project roadmaps, milestone planning, and task decomposition\n"
            "- ID: general_assistant, Role: Conversational inquiry & direct conceptual explanations\n"
            "- ID: excel_specialist, Role: Enterprise Excel & computational intelligence specialist for coordinate resolution, cell-level edits, multi-sheet joins, pivots, statistical formulas, and format-preserving mutations\n"
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
        "CRITICAL MODEL & RESEARCH DIRECTIVE: When creating workflow steps that involve web search, real-time data, breaking news, today's weather, live stock quotes, sports results, or fresh internet discovery, ALWAYS assign agent_id 'researcher' with model 'sonar' (Perplexity Sonar). Perplexity Sonar is the mandatory model for all live information and web search tasks.\n\n"
        "CRITICAL BLOCK OPTIMIZATION DIRECTIVE: Whenever a workflow task involves deterministic computation, mathematical calculations, string parsing, or data formatting, ALWAYS prefer a 'python_code' non-agent block instead of an LLM agent block. Python scripts execute with zero tokens and 100% precision. Reserve 'agent' blocks for tasks requiring reasoning, language generation, web search, or code creation.\n\n"
        "CRITICAL ORCHESTRATION DIRECTIVE: For all multi-step workflows, the final step MUST ALWAYS be a synthesis step assigned to agent 'synthesizer' to consolidate previous step outputs and deliver a cohesive final output directly in line with the high-level workflow goal.\n\n"
        "GENERAL DATA ANALYST DIRECTIVE: The data_analyst agent is a general-purpose numerical, statistical, and tabular analysis agent across all domains. Do NOT inject scenario-specific or finance-specific constraints (e.g. price-to-earnings, stock quotes) into data analyst steps unless explicitly requested by the user.\n\n"
        "CRITICAL ENTERPRISE EXCEL DIRECTIVE: For tasks requiring spreadsheet coordinate resolution, cell-level edits, Excel formulas, multi-sheet relational joins, multi-dimensional pivot tables, VBA macro preservation, or format-preserving spreadsheet mutations, ALWAYS assign agent 'excel_specialist'.\n\n"
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

    market_terms_fb = [
        r"\bstocks?\b", r"\btickers?\b", r"\bmarket quotes?\b", r"\bshare prices?\b",
        r"\bequity\b", r"\bequities\b", r"\bcrypto\b", r"\bbtc\b", r"\bbitcoin\b",
        r"\bwebsearch\b", r"\blive search\b", r"\blive info\b"
    ]
    if any(re.search(term, prompt_lower) for term in market_terms_fb):
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


def requires_fresh_internet_information(prompt: str) -> bool:
    """
    Detects whether a user prompt requires real-time, current, live, or time-sensitive
    information from the web that warrants aggressively using the Research Agent with Perplexity Sonar.
    """
    p = prompt.lower().strip()

    # Explicit web search verbs & live discovery intents
    search_intents = [
        "search out", "search for", "search up", "search the web", "search the internet",
        "search online", "look up", "find out", "find me", "find online", "google",
        "web search", "websearch", "search web", "browse the web", "browse online",
        "crawl", "scrape", "live search", "online search", "check online", "check the web",
        "check latest", "who is the current", "what is the current", "when did",
        "fact check", "fact-check", "citations for", "sources for", "verify claims",
        "verify if", "is it true that"
    ]
    if any(intent in p for intent in search_intents):
        return True

    # Search keyword boundaries (e.g. standalone "search", "lookup")
    if re.search(r"\b(search|websearch|google|lookup)\b", p):
        return True

    # Temporal recency cues
    temporal_cues = [
        "today", "yesterday", "tonight", "this morning", "this afternoon", "this week",
        "this month", "this quarter", "this year", "right now", "currently", "current",
        "latest", "recent", "recently", "newest", "upcoming", "breaking", "as of now",
        "as of today", "real-time", "real time", "live data", "live info", "live information",
        "live update", "2025", "2026", "2027", "updated"
    ]
    if any(re.search(rf"\b{re.escape(cue)}\b", p) for cue in temporal_cues):
        return True

    # Real-time entities & topics (stocks, financial performance, sports, weather, events)
    realtime_topics = [
        "weather", "forecast", "temperature", "climate today",
        "stock performance", "stock performances", "stock movement", "stock movements",
        "stock price", "stock prices", "ticker", "tickers", "market quote", "market quotes",
        "stock quote", "stock quotes", "share price", "share prices", "equity price", "equity prices",
        "crypto price", "crypto prices", "btc price", "bitcoin price", "eth price", "nasdaq",
        "s&p", "dow jones", "market cap", "p/e ratio", "quarterly earnings", "earnings report",
        "earnings call", "dividend yield", "trading volume", "52-week", "financial performance",
        "financial metrics",
        "sports score", "sports scores", "game score", "match score", "who won",
        "game result", "match result", "tournament", "championship", "standings",
        "election", "poll results", "who won the election", "vote count",
        "did spacex", "spacex launch", "starship", "nasa launch",
        "what happened to", "what happened with", "what is happening",
        "breaking news", "headlines", "top stories", "press release",
        "flight status", "delay status", "traffic today"
    ]
    if any(topic in p for topic in realtime_topics):
        return True

    return False


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

    # 2. PDF Attachment & /artifact Report Generation Pipeline
    has_artifact_command = "/artifact" in prompt_lower
    has_pdf_or_doc = bool(attached_artifacts) or "pdf" in prompt_lower or ".pdf" in prompt_lower
    has_report_request = any(k in prompt_lower for k in [
        "prepare a report", "prepare report", "generate a report", "generate report",
        "create a report", "create report", "executive summary", "research synthesis",
        "technical specification", "tech spec", "financial analysis", "compliance review",
        "meeting minutes", "artifact report", "synthesize report", "draft report"
    ])

    if has_artifact_command or (has_report_request and has_pdf_or_doc):
        if has_pdf_or_doc and attached_artifacts:
            step_1_def = {
                "id": "step_1",
                "name": "PDF Document Extraction & Analysis",
                "step_type": "agent",
                "agent_id": "file_parser",
                "instructions": f"Extract all critical text schemas, tabular data, metrics, key findings, and structure from the attached PDF document(s) relevant to: {prompt_clean}",
                "tool_ids": [],
                "knowledge_file_ids": [],
                "attached_artifact_ids": art_ids,
                "depends_on": [],
            }
            step_2_input = "{{steps.step_1.output.text}}"
        elif requires_fresh_internet_information(prompt_clean):
            step_1_def = {
                "id": "step_1",
                "name": "Live Grounded Fact & Market Research",
                "step_type": "agent",
                "agent_id": "researcher",
                "model": "sonar",
                "instructions": f"Gather verified facts, recent developments, metrics, and citations for: {prompt_clean}",
                "tool_ids": [],
                "knowledge_file_ids": [],
                "attached_artifact_ids": art_ids,
                "depends_on": [],
            }
            step_2_input = "{{steps.step_1.output.text}}"
        else:
            step_1_def = {
                "id": "step_1",
                "name": "Topic Research & Strategic Structuring",
                "step_type": "agent",
                "agent_id": "planner",
                "instructions": f"Analyze core principles, outline section requirements, and establish evidence points for: {prompt_clean}",
                "tool_ids": [],
                "knowledge_file_ids": [],
                "attached_artifact_ids": art_ids,
                "depends_on": [],
            }
            step_2_input = "{{steps.step_1.output.text}}"

        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Artifact Report Synthesis Pipeline ({slug_id})",
            "description": "Multi-agent PDF extraction, structured template drafting, and dual markdown/downloadable PDF compilation.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                step_1_def,
                {
                    "id": "step_2",
                    "name": "Template-Guided Report Drafting",
                    "step_type": "agent",
                    "agent_id": "writer",
                    "instructions": f"Using the extracted context, draft a thorough, comprehensive report structured into clear sections (Executive Summary, Key Findings, In-Depth Analysis, Data/Metrics Table, and Recommendations) directly adhering to the requested artifact template for: {prompt_clean}\n\nContext:\n{step_2_input}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
                {
                    "id": "step_3",
                    "name": "Final Report & PDF Artifact Compilation",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Finalize the report into a polished, professional markdown document with clean headings, formatted tables, bullet points, and an executive sign-off ready for dual display and automated PDF generation: {{{{steps.step_2.output.text}}}} Goal: {prompt_clean}",
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

    # 3. Enterprise Excel & Computational Intelligence Pipeline (Excel Specialist Agent)
    has_excel_specialist = any(k in prompt_lower for k in [
        "excel specialist", "spreadsheet coordinate", "cell coordinate", "cell coordinates",
        "excel formula", "spreadsheet formula", "pivot table", "relational join",
        "join sheets", "merge sheets", "excel macro", "update cell", "format-preserving",
        "format preserving", "multi-sheet", "coordinate resolution", "edit spreadsheet",
        "excel edit", "modify cell", "targeted edit"
    ]) or (
        any(k in prompt_lower for k in ["excel", "xlsx", "xlsm", "spreadsheet"]) and
        any(k in prompt_lower for k in ["cell", "row", "column", "formula", "join", "merge", "pivot", "preserve", "edit", "update", "coordinate", "schema", "validation", "rollback"])
    )
    if has_excel_specialist:
        if requires_fresh_internet_information(prompt_clean):
            return {
                "id": f"ephemeral_wf_{slug_id}",
                "title": f"Live Research & Enterprise Excel Mutation Pipeline ({slug_id})",
                "description": "Multi-agent live market discovery with Perplexity Sonar followed by surgical format-preserving spreadsheet edits and synthesis.",
                "goal": prompt_clean,
                "is_ephemeral": True,
                "is_multi_step": True,
                "steps": [
                    {
                        "id": "step_1",
                        "name": "Live Grounded Market Discovery",
                        "step_type": "agent",
                        "agent_id": "researcher",
                        "model": "sonar",
                        "instructions": f"Search live sources using Perplexity Sonar for verified facts, figures, and metrics required for: {prompt_clean}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": art_ids,
                        "depends_on": [],
                    },
                    {
                        "id": "step_2",
                        "name": "Enterprise Spreadsheet & Cell Resolution Operations",
                        "step_type": "agent",
                        "agent_id": "excel_specialist",
                        "instructions": f"Translate natural language requests into exact cell coordinates, perform targeted mutations while strictly preserving all cell styling, formulas, number formats, and VBA macros, validate pre-save schema integrity, and apply results: {{{{steps.step_1.output.text}}}} Goal: {prompt_clean}",
                        "tool_ids": [
                            "introspect_spreadsheet",
                            "resolve_coordinates",
                            "edit_spreadsheet_cells",
                            "execute_statistical_analysis",
                            "relational_join_sheets",
                            "create_pivot_table",
                            "rollback_spreadsheet_transactions",
                            "validate_workbook_integrity"
                        ],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": art_ids,
                        "depends_on": ["step_1"],
                    },
                    {
                        "id": "step_3",
                        "name": "Computational Audit & Delivery Briefing",
                        "step_type": "agent",
                        "agent_id": "synthesizer",
                        "instructions": f"Consolidate verified research findings, cell modifications, and transaction audit summary into a cohesive delivery directly fulfilling the user's goal: {{{{steps.step_2.output.text}}}} Goal: {prompt_clean}",
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

        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Enterprise Computational Spreadsheet Intelligence Pipeline ({slug_id})",
            "description": "Targeted format-preserving spreadsheet mutations, multi-sheet joins, pivot tables, and pre-save schema validation.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Surgical Spreadsheet Operations & Validation",
                    "step_type": "agent",
                    "agent_id": "excel_specialist",
                    "instructions": f"Resolve natural language coordinates, execute targeted cell mutations/formulas, perform relational joins or multi-axis pivot tables, preserve original styling and VBA macros, and guarantee pre-save workbook integrity for: {prompt_clean}",
                    "tool_ids": [
                        "introspect_spreadsheet",
                        "resolve_coordinates",
                        "edit_spreadsheet_cells",
                        "execute_statistical_analysis",
                        "relational_join_sheets",
                        "create_pivot_table",
                        "rollback_spreadsheet_transactions",
                        "validate_workbook_integrity"
                    ],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Audit Log & Executive Spreadsheet Summary",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize cell mutation diffs, statistical outputs, and transaction audit verification into a clear, executive-ready summary directly fulfilling the user's goal: {{{{steps.step_1.output.text}}}} Goal: {prompt_clean}",
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

    # 4. Optimized Deterministic Non-Agent Blocks (Python Code / Math Execution)
    has_code_calc = any(k in prompt_lower for k in [
        "python code block", "non agent", "non-agent", "compute with python",
        "calculate with python", "deterministic code", "python runner", "python script block"
    ])
    if has_code_calc:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Deterministic Computational Pipeline ({slug_id})",
            "description": "Optimized execution using a sandboxed Python code block for zero-token deterministic calculation.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Deterministic Sandboxed Calculation",
                    "step_type": "python_code",
                    "agent_id": "python_runner",
                    "code": (
                        "def execute(inputs, previous_outputs, context):\n"
                        "    prompt = str(inputs.get('prompt') or inputs.get('query') or '')\n"
                        "    # Execute verified formula computation\n"
                        "    res = {'status': 'success', 'calculation': 'Completed deterministic computation', 'goal': prompt}\n"
                        "    if 'interest' in prompt.lower() or 'compound' in prompt.lower():\n"
                        "        p, r, t = 10000.0, 0.05, 10.0\n"
                        "        total = p * ((1.0 + r) ** t)\n"
                        "        res.update({'principal': p, 'rate': r, 'years': t, 'total_amount': round(total, 2), 'interest_earned': round(total - p, 2)})\n"
                        "    return res\n"
                    ),
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Goal-Aligned Output Synthesis",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Format and summarize the verified computation results into a cohesive final response directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_1.output.text}}}}",
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

    # 3. Content Writing & Editorial Drafting (Writer Agent)
    has_writing = any(k in prompt_lower for k in [
        "write an article", "write article", "blog post", "draft essay", "write an essay",
        "write essay", "newsletter", "copywriting", "write a speech", "write a story", "draft email",
        "poem", "poetry", "write a poem", "how a good poem", "how to write a poem",
        "how a poem should be written", "instructing how", "instruction on", "instructions on",
        "writing guide", "guide to writing", "tutorial on writing", "how to write"
    ]) or (
        any(k in prompt_lower for k in ["write", "draft", "author", "compose", "instruct", "instructing"]) and
        any(k in prompt_lower for k in ["poem", "poetry", "guide", "manual", "handbook", "article", "essay", "story", "post", "document"])
    )
    has_doc_file_export = any(k in prompt_lower for k in [
        "markdown file", "md file", ".md file", "generate a markdown", "create a markdown",
        "download", "downloadable", "available for download", "make it available for download",
        "save as file", "export file", "file format", "text file", "txt file"
    ])
    if has_writing:
        if has_doc_file_export:
            return {
                "id": f"ephemeral_wf_{slug_id}",
                "title": f"Document Authoring & Downloadable Markdown Synthesis Pipeline ({slug_id})",
                "description": "Multi-agent creative and instructional document authoring, markdown file compilation, and deliverable handoff.",
                "goal": prompt_clean,
                "is_ephemeral": True,
                "is_multi_step": True,
                "steps": [
                    {
                        "id": "step_1",
                        "name": "Creative & Instructional Content Authoring",
                        "step_type": "agent",
                        "agent_id": "writer",
                        "instructions": f"Author complete, high-quality, comprehensive written content directly satisfying the user's goal '{prompt_clean}'. Organize into clear structured sections with evocative prose, deep insight, and practical guidance. Avoid conversational filler.",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": art_ids,
                        "depends_on": [],
                    },
                    {
                        "id": "step_2",
                        "name": "Downloadable Markdown File Compilation",
                        "step_type": "agent",
                        "agent_id": "file_creator",
                        "instructions": f"Compile the authored document into a polished, downloadable markdown (.md) document with an appropriate main header (# Title), clean subheadings, bullet points, and formatting ready for direct file export: {{{{steps.step_1.output.text}}}} User Request: {prompt_clean}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": [],
                        "depends_on": ["step_1"],
                    },
                    {
                        "id": "step_3",
                        "name": "Executive Overview & File Delivery",
                        "step_type": "agent",
                        "agent_id": "synthesizer",
                        "instructions": f"Deliver the final markdown document to the user along with a concise executive overview directly fulfilling the goal '{prompt_clean}': {{{{steps.step_2.output.text}}}}",
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
        if requires_fresh_internet_information(prompt_clean):
            return {
                "id": f"ephemeral_wf_{slug_id}",
                "title": f"Live Research & Editorial Writing Pipeline ({slug_id})",
                "description": "Multi-agent live research and structured editorial content drafting.",
                "goal": prompt_clean,
                "is_ephemeral": True,
                "is_multi_step": True,
                "steps": [
                    {
                        "id": "step_1",
                        "name": "Live Topic Research & Evidence Discovery",
                        "step_type": "agent",
                        "agent_id": "researcher",
                        "model": "sonar",
                        "instructions": f"Gather live background context, verified citations, and recent developments: {prompt_clean}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": art_ids,
                        "depends_on": [],
                    },
                    {
                        "id": "step_2",
                        "name": "Editorial Content Drafting",
                        "step_type": "agent",
                        "agent_id": "writer",
                        "instructions": f"Draft engaging, high quality editorial content adhering strictly to the user's goal '{prompt_clean}' incorporating research findings: {{{{steps.step_1.output.text}}}}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": [],
                        "depends_on": ["step_1"],
                    },
                    {
                        "id": "step_3",
                        "name": "Editorial Review & Delivery Synthesis",
                        "step_type": "agent",
                        "agent_id": "synthesizer",
                        "instructions": f"Consolidate editorial copy and citations into a polished final deliverable directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_2.output.text}}}}",
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
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Editorial Content & Polish Pipeline ({slug_id})",
            "description": "Content drafting and stylistic synthesis.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Targeted Content Drafting",
                    "step_type": "agent",
                    "agent_id": "writer",
                    "instructions": f"Draft complete, polished written content directly satisfying the user's goal '{prompt_clean}'. Avoid unnecessary boilerplate.",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Editorial Polish & Delivery",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Ensure cohesive formatting, headings, and seamless presentation directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_1.output.text}}}}",
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

    # 4. Strategic Planning & Roadmaps (Planner Agent)
    has_planning = any(k in prompt_lower for k in [
        "roadmap", "milestone plan", "sprint plan", "project plan", "timeline plan",
        "task decomposition", "launch plan", "implementation plan"
    ])
    if has_planning:
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Strategic Roadmap & Phasing Pipeline ({slug_id})",
            "description": "Multi-agent roadmap design, task decomposition, and milestone synthesis.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Roadmap Architecture & Task Decomposition",
                    "step_type": "agent",
                    "agent_id": "planner",
                    "instructions": f"Decompose project requirements into structured phases, milestones, dependencies, and completion criteria for: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Executive Roadmap Synthesis",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize milestones, timelines, and execution recommendations into a cohesive final briefing directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_1.output.text}}}}",
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

    # 5. Composite Multi-Agent Workflows Decomposition
    # A) Live Market & Financial Intelligence
    market_terms = [
        r"\bstocks?\b", r"\btickers?\b", r"\bmarket quotes?\b", r"\bshare prices?\b",
        r"\bequity\b", r"\bequities\b", r"\bcrypto\b", r"\bbtc\b", r"\bbitcoin\b", r"\beth\b",
        r"\bfinancial metrics?\b", r"\bp/e ratios?\b", r"\bvaluations?\b",
        r"\bnasdaq\b", r"\bdow jones\b", r"\bdow\b", r"\bs&p\b", r"\bs&p 500\b",
        r"\bmarket performances?\b", r"\bstock performances?\b"
    ]
    has_market_kw = any(re.search(term, prompt_lower) for term in market_terms)
    has_analysis_kw = any(k in prompt_lower for k in [
        "analysis", "analyze", "compare", "valuation", "ratio", "briefing", "summary",
        "financial", "trend", "forecast", "insight"
    ])
    has_file_export = any(k in prompt_lower for k in [
        "excel", "xlsx", "spreadsheet", "csv", "sheet", "workbook", "create file", "export file", "download file", "generate file"
    ])
    if has_market_kw and (has_analysis_kw or has_file_export or len(prompt_clean.split()) > 6):
        if has_file_export:
            return {
                "id": f"ephemeral_wf_{slug_id}",
                "title": f"Live Market Data & Spreadsheet Generation Pipeline ({slug_id})",
                "description": "Multi-agent live market research with Perplexity Sonar, quantitative tabular normalization, and production Excel spreadsheet synthesis.",
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
                        "instructions": f"Search live financial sources and market quotes using Perplexity Sonar for real-time stock prices, trading volume, daily/historical performance, and valuation metrics: {prompt_clean}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": art_ids,
                        "depends_on": [],
                    },
                    {
                        "id": "step_2",
                        "name": "Financial Data Normalization & Tabular Structuring",
                        "step_type": "agent",
                        "agent_id": "data_analyst",
                        "instructions": f"Analyze discovered market data, calculate performance deltas and ratios, and format clean structured tabular rows with typed headers (Ticker, Company, Current Price, Change %, Market Cap, P/E Ratio, 52-Week Range): {{{{steps.step_1.output.text}}}}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": [],
                        "depends_on": ["step_1"],
                    },
                    {
                        "id": "step_3",
                        "name": "Production Spreadsheet & File Synthesis",
                        "step_type": "agent",
                        "agent_id": "file_creator",
                        "instructions": f"Generate a formatted production Excel spreadsheet (.xlsx/CSV) with styled tables, column widths, and summary rows from the tabular data, and provide an executive summary of market performance: {{{{steps.step_2.output.text}}}} Goal: {prompt_clean}",
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
        if requires_fresh_internet_information(prompt_clean):
            return {
                "id": f"ephemeral_wf_{slug_id}",
                "title": f"Live Research, Analysis & File Export Pipeline ({slug_id})",
                "description": "Multi-agent live research with Perplexity Sonar, quantitative analysis, and formatted file artifact generation.",
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
                        "instructions": f"Conduct live web search using Perplexity Sonar to gather authoritative citations, verified facts, and recent metrics: {prompt_clean}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": art_ids,
                        "depends_on": [],
                    },
                    {
                        "id": "step_2",
                        "name": "Statistical & Numerical Analysis",
                        "step_type": "agent",
                        "agent_id": "data_analyst",
                        "instructions": f"Analyze discovered data and parameters, calculate descriptive metrics, identify patterns, and structure clean data: {{{{steps.step_1.output.text}}}}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": [],
                        "depends_on": ["step_1"],
                    },
                    {
                        "id": "step_3",
                        "name": "Formatted File & Report Generation",
                        "step_type": "agent",
                        "agent_id": "file_creator",
                        "instructions": "Generate formatted downloadable file incorporating numerical analysis: {{steps.step_2.output.text}}",
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
    if (has_deep_kw or len(prompt_clean.split()) > 14) and not has_file_export:
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
        if requires_fresh_internet_information(prompt_clean):
            return {
                "id": f"ephemeral_wf_{slug_id}",
                "title": f"Live Discovery & File Generation Pipeline ({slug_id})",
                "description": "Multi-agent live web research with Perplexity Sonar, tabular normalization, and production file artifact synthesis.",
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
                        "instructions": f"Conduct live web search using Perplexity Sonar to gather authoritative citations, real-time facts, and current metrics for: {prompt_clean}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": art_ids,
                        "depends_on": [],
                    },
                    {
                        "id": "step_2",
                        "name": "Data Schema & Tabular Normalization",
                        "step_type": "agent",
                        "agent_id": "data_analyst",
                        "instructions": f"Analyze discovered web findings, design clean column schemas, calculate metrics, and structure normalized tabular data with typed columns and headers: {{{{steps.step_1.output.text}}}}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": [],
                        "depends_on": ["step_1"],
                    },
                    {
                        "id": "step_3",
                        "name": "Production File & Spreadsheet Synthesis",
                        "step_type": "agent",
                        "agent_id": "file_creator",
                        "instructions": f"Generate formatted production file artifact (native Excel spreadsheet table with openpyxl, CSV, PDF, or presentation) incorporating structured tabular data: {{{{steps.step_2.output.text}}}}",
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

    # H) Real-Time Research, Fact Verification & Synthesis Workflow (2 or 3 Steps)
    is_fresh = requires_fresh_internet_information(prompt_clean)
    has_search = any(k in prompt_lower for k in [
        "web search", "websearch", "search", "search out", "search for", "latest", "news",
        "price", "prices", "who is", "when did", "current", "recent", "lookup", "look up",
        "find", "find out", "trends", "what happened"
    ])
    if has_search or is_fresh:
        if has_file_export:
            return {
                "id": f"ephemeral_wf_{slug_id}",
                "title": f"Live Web Research & File Generation Pipeline ({slug_id})",
                "description": "Multi-agent live research with Perplexity Sonar, quantitative tabular normalization, and production file synthesis.",
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
                        "instructions": f"Execute live web search using Perplexity Sonar to gather authoritative citations, real-time facts, and current developments: {prompt_clean}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": art_ids,
                        "depends_on": [],
                    },
                    {
                        "id": "step_2",
                        "name": "Comparative Analysis & Tabular Structuring",
                        "step_type": "agent",
                        "agent_id": "data_analyst",
                        "instructions": f"Analyze research findings, extract key metrics, structure comparative facts, and format clean structured tabular data: {{{{steps.step_1.output.text}}}}",
                        "tool_ids": [],
                        "knowledge_file_ids": [],
                        "attached_artifact_ids": [],
                        "depends_on": ["step_1"],
                    },
                    {
                        "id": "step_3",
                        "name": "Production File & Spreadsheet Synthesis",
                        "step_type": "agent",
                        "agent_id": "file_creator",
                        "instructions": f"Generate formatted production file artifact (.xlsx, CSV, or document) incorporating structured tabular data: {{{{steps.step_2.output.text}}}} Goal: {prompt_clean}",
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

        has_metrics_or_price = any(k in prompt_lower for k in [
            "price", "gold", "market", "rate", "cost", "quote", "metrics", "data", "compare", "valuation", "p/e"
        ])
        if has_metrics_or_price:
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
        # Direct live web query (weather, sports scores, recent news, live facts)
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"Live Web Discovery & Synthesis Pipeline ({slug_id})",
            "description": "Multi-agent live internet research with Perplexity Sonar and verified synthesis.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": True,
            "steps": [
                {
                    "id": "step_1",
                    "name": "Live Web Discovery & Citation Gathering",
                    "step_type": "agent",
                    "agent_id": "researcher",
                    "model": "sonar",
                    "instructions": f"Execute live web search using Perplexity Sonar to gather authoritative citations, real-time facts, and current developments: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Goal-Aligned Fact Synthesis",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Synthesize verified findings, citations, and live evidence into a cohesive final response directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_1.output.text}}}}",
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
