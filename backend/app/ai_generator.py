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
