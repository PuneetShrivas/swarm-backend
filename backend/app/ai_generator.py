import os
import re
import json
import uuid
from typing import Dict, Any, List, Optional, Literal, Tuple
from pydantic import BaseModel, Field

try:
    from app.groq_client import get_groq_client, is_groq_configured, execute_groq_chat
except ImportError:
    from groq_client import get_groq_client, is_groq_configured, execute_groq_chat


# -------------------------------------------------------------
# 0. Intent Classification Models & Caching
# -------------------------------------------------------------

class QueryIntentClassification(BaseModel):
    primary_intent: Literal[
        "spreadsheet_operations",
        "document_authoring",
        "artifact_report",
        "code_engineering",
        "strategic_planning",
        "market_intelligence",
        "live_web_research",
        "data_analytics",
        "document_parsing",
        "conversational_greeting",
        "general_inquiry",
    ] = "general_inquiry"
    requires_live_web_search: bool = False
    file_export_requested: bool = False
    export_format: Optional[Literal["md", "xlsx", "csv", "pdf", "pptx", "py", "json", "txt"]] = None
    is_multi_step: bool = True
    workflow_title: str = "Coordinated Multi-Agent Pipeline"
    workflow_description: str = "Collaborative multi-agent execution pipeline."
    recommended_agent_ids: List[str] = Field(default_factory=lambda: ["general_assistant", "synthesizer"])
    reasoning: str = ""


_INTENT_CACHE: Dict[str, QueryIntentClassification] = {}

INTENT_CLASSIFIER_PROMPT = """You are the Swarm Autonomous Orchestrator Intent Analyzer.
Your task is to analyze the user prompt and context to produce a structured JSON classification that decides which specialist agent pipeline should execute the request.

Analyze the prompt holistically into exactly ONE primary_intent:
- "spreadsheet_operations": Natural language queries on Excel/spreadsheets, cell coordinate operations, format-preserving edits, multi-sheet relational joins, pivot tables, complex formulas, or statistical computing on sheets.
- "document_authoring": Creative or instructional document composition: poems, poetry guides, essays, creative stories, editorial articles, manuals, blog posts, newsletters.
- "artifact_report": Formal structured report synthesis (e.g. Executive Summary, Technical Specification, Compliance Review, Research Synthesis, Financial Analysis, Meeting Minutes) based on /artifact command or attached documents/PDFs.
- "code_engineering": Writing software code, scripts, algorithms, debugging, code refactoring, security audits, unit tests.
- "strategic_planning": Project roadmaps, milestone phasing, sprint plans, task decomposition, timelines.
- "market_intelligence": Real-time stock prices, tickers, equity valuations, market performance, crypto quotes, financial metrics.
- "live_web_research": Current events, breaking news, live web facts, verified citations, or time-sensitive lookups requiring up-to-date internet research.
- "data_analytics": Statistical computations, numerical dataset analysis, math calculations, data modeling (without specific spreadsheet coordinate editing).
- "document_parsing": Document extraction, indexing, RAG, text schemas from PDFs or unstructured files.
- "conversational_greeting": Casual greetings, pleasantries, trivial single-turn questions (e.g. "hi", "hello", "who are you").
- "general_inquiry": General knowledge questions, conceptual explanations, multi-domain exploration.

Also determine:
- requires_live_web_search (boolean): True ONLY if answering requires fresh real-time web search / current internet information (e.g. current stock prices, recent news, live facts, weather).
- file_export_requested (boolean): True if the user asks for a file to be generated, saved, created, or made available for download.
- export_format: "md", "xlsx", "csv", "pdf", "pptx", "py", "json", "txt", or null.
- is_multi_step (boolean): False ONLY for trivial conversational greetings. True for all reasoning/content/research/spreadsheet/coding tasks.
- recommended_agent_ids: Ordered sequence of specialist agents to execute the workflow (e.g. ["writer", "file_creator", "synthesizer"]).
- workflow_title: A concise, descriptive title (e.g. "Document Authoring & Downloadable Markdown Synthesis Pipeline").
- workflow_description: A 1-sentence description.
- reasoning: A 1-sentence explanation of why this intent and pipeline were chosen.

Return ONLY a raw JSON object matching the exact structure without markdown commentary:
{
  "primary_intent": "...",
  "requires_live_web_search": false,
  "file_export_requested": false,
  "export_format": null,
  "is_multi_step": true,
  "workflow_title": "...",
  "workflow_description": "...",
  "recommended_agent_ids": ["..."],
  "reasoning": "..."
}"""


def _deterministic_intent_fallback(
    prompt: str,
    attached_artifacts: Optional[List[Dict[str, Any]]] = None,
) -> QueryIntentClassification:
    """
    High-accuracy deterministic fallback classifier used when LLM providers are unreachable.
    Uses regex word boundaries to avoid substring collision errors.
    """
    p_lower = (prompt or "").lower().strip()
    has_attached = bool(attached_artifacts)
    
    # 1. Artifact report
    if "/artifact" in p_lower or (has_attached and any(k in p_lower for k in ["report", "summary", "analyze", "review"])):
        return QueryIntentClassification(
            primary_intent="artifact_report",
            requires_live_web_search=False,
            file_export_requested=True,
            export_format="pdf",
            is_multi_step=True,
            workflow_title="Artifact Report Synthesis Pipeline",
            workflow_description="Multi-agent document extraction, structured template drafting, and downloadable report compilation.",
            recommended_agent_ids=["file_parser", "writer", "synthesizer"] if has_attached else ["researcher", "writer", "synthesizer"],
            reasoning="Fallback: Detected template report request with attached document/context."
        )

    # 2. Market intelligence
    market_terms = [r"\bstocks?\b", r"\btickers?\b", r"\bmarket quotes?\b", r"\bshare prices?\b", r"\bcrypto\b", r"\bbtc\b", r"\bnasdaq\b", r"\bdow jones\b", r"\bs&p\b", r"\bstock performances?\b"]
    if any(re.search(t, p_lower) for t in market_terms):
        has_file = bool(re.search(r"\b(excel|xlsx|spreadsheet|csv|sheet|download|file)\b", p_lower))
        return QueryIntentClassification(
            primary_intent="market_intelligence",
            requires_live_web_search=True,
            file_export_requested=has_file,
            export_format="xlsx" if has_file else None,
            is_multi_step=True,
            workflow_title="Live Market Data & Spreadsheet Generation Pipeline" if has_file else "Live Market & Valuation Intelligence Pipeline",
            workflow_description="Multi-agent live market research with Perplexity Sonar and financial analysis.",
            recommended_agent_ids=["researcher", "data_analyst", "file_creator"] if has_file else ["researcher", "data_analyst", "synthesizer"],
            reasoning="Fallback: Detected financial market intelligence inquiry requiring live Sonar discovery."
        )

    # 3. Spreadsheet operations (Excel Specialist)
    if bool(re.search(r"\b(excel|spreadsheet|xlsx|xlsm|pivot table|relational join|merge sheets|join sheets|join sheet|cell coordinate|cell [a-z]+\d+|vba macro|sheet\d+)\b", p_lower)):
        req_search = bool(re.search(r"\b(stock|price|market|ticker|latest|current|real-time)\b", p_lower))
        return QueryIntentClassification(
            primary_intent="spreadsheet_operations",
            requires_live_web_search=req_search,
            file_export_requested=True,
            export_format="xlsx",
            is_multi_step=True,
            workflow_title="Enterprise Excel & Computational Intelligence Pipeline",
            workflow_description="Format-preserving spreadsheet mutations, cell coordinate resolution, and analytical joins.",
            recommended_agent_ids=["researcher", "excel_specialist", "synthesizer"] if req_search else ["excel_specialist", "synthesizer"],
            reasoning="Fallback: Detected spreadsheet manipulation and computational cell operations."
        )

    # 4. Document authoring & creative writing
    writing_terms = [r"\bpoems?\b", r"\bpoetry\b", r"\bessays?\b", r"\barticles?\b", r"\bblog posts?\b", r"\bwriting guide\b", r"\bcreative story\b"]
    if any(re.search(t, p_lower) for t in writing_terms) or (bool(re.search(r"\b(write|draft|author|compose)\b", p_lower)) and bool(re.search(r"\b(guide|manual|story|speech|post|poem)\b", p_lower))):
        has_download = bool(re.search(r"\b(download|available for download|markdown|md file|\.md|save as file)\b", p_lower))
        return QueryIntentClassification(
            primary_intent="document_authoring",
            requires_live_web_search=False,
            file_export_requested=has_download,
            export_format="md" if has_download else None,
            is_multi_step=True,
            workflow_title="Document Authoring & Downloadable Markdown Synthesis Pipeline" if has_download else "Editorial Content & Polish Pipeline",
            workflow_description="Creative and instructional document authoring and markdown file delivery.",
            recommended_agent_ids=["writer", "file_creator", "synthesizer"] if has_download else ["writer", "synthesizer"],
            reasoning="Fallback: Detected creative or instructional document authoring intent."
        )

    # 5. Code engineering
    if bool(re.search(r"\b(code|coding|function|python|javascript|typescript|sql|bug|refactor|script|program|class|api|unit test)\b", p_lower)):
        return QueryIntentClassification(
            primary_intent="code_engineering",
            requires_live_web_search=False,
            file_export_requested=bool(re.search(r"\b(file|download|save|script)\b", p_lower)),
            export_format="py",
            is_multi_step=True,
            workflow_title="Software Engineering & Quality Review Pipeline",
            workflow_description="Production code implementation, security review, and technical documentation.",
            recommended_agent_ids=["coder", "reviewer", "synthesizer"],
            reasoning="Fallback: Detected software implementation and engineering request."
        )

    # 6. Strategic planning
    if bool(re.search(r"\b(roadmap|milestone plan|sprint plan|project plan|timeline plan|task decomposition)\b", p_lower)):
        return QueryIntentClassification(
            primary_intent="strategic_planning",
            requires_live_web_search=False,
            file_export_requested=False,
            is_multi_step=True,
            workflow_title="Strategic Roadmap & Phasing Pipeline",
            workflow_description="Multi-agent roadmap design, task decomposition, and milestone synthesis.",
            recommended_agent_ids=["planner", "synthesizer"],
            reasoning="Fallback: Detected strategic planning and milestone decomposition."
        )

    # 7. Conversational greeting
    if p_lower.strip("!.? ") in ["hi", "hello", "hey", "greetings", "good morning", "good evening", "howdy", "sup", "yo", "who are you"] or len(prompt.split()) <= 2:
        return QueryIntentClassification(
            primary_intent="conversational_greeting",
            requires_live_web_search=False,
            file_export_requested=False,
            is_multi_step=False,
            workflow_title="General Assistant Turn",
            workflow_description="Direct single-agent response for conversational greeting.",
            recommended_agent_ids=["general_assistant"],
            reasoning="Fallback: Detected casual greeting or pleasantry."
        )

    # 8. Live web research
    if bool(re.search(r"\b(search|websearch|look up|find out|latest|news|current|recent|today|weather)\b", p_lower)):
        return QueryIntentClassification(
            primary_intent="live_web_research",
            requires_live_web_search=True,
            file_export_requested=False,
            is_multi_step=True,
            workflow_title="Live Web Discovery & Synthesis Pipeline",
            workflow_description="Real-time web search with Perplexity Sonar and verified fact synthesis.",
            recommended_agent_ids=["researcher", "synthesizer"],
            reasoning="Fallback: Detected time-sensitive live research query."
        )

    # Default general inquiry
    return QueryIntentClassification(
        primary_intent="general_inquiry",
        requires_live_web_search=False,
        file_export_requested=False,
        is_multi_step=True,
        workflow_title="Coordinated Knowledge & Synthesis Pipeline",
        workflow_description="Multi-agent exploratory research and comprehensive synthesis pipeline.",
        recommended_agent_ids=["general_assistant", "synthesizer"],
        reasoning="Fallback: General knowledge and conceptual analysis request."
    )


def analyze_query_intent(
    prompt: str,
    attached_artifacts: Optional[List[Dict[str, Any]]] = None,
) -> QueryIntentClassification:
    """
    Evaluates user prompt semantics and context in a single pass using LLM analysis.
    Classifies intent, determines real-time search necessity, detects file export intent,
    and returns a structured QueryIntentClassification.
    """
    clean_p = (prompt or "").strip()
    if not clean_p:
        return QueryIntentClassification(
            primary_intent="conversational_greeting",
            is_multi_step=False,
            recommended_agent_ids=["general_assistant"],
            workflow_title="General Assistant Turn",
            reasoning="Empty prompt"
        )

    # Check in-memory cache
    cache_key = f"{clean_p.lower()}__art_{bool(attached_artifacts)}"
    if cache_key in _INTENT_CACHE:
        return _INTENT_CACHE[cache_key]

    context_note = ""
    if attached_artifacts:
        fnames = [a.get("filename") or a.get("name") or "file" for a in attached_artifacts]
        context_note = f"\nAttached context files: {', '.join(fnames)}"

    user_eval_prompt = f"User Request:\n{clean_p}{context_note}"

    # 1. Attempt Groq LPU inference (ultra-low latency)
    if is_groq_configured():
        groq_client, _ = get_groq_client()
        if groq_client:
            try:
                res_text, _, _, _, _ = execute_groq_chat(
                    client=groq_client,
                    messages=[{"role": "user", "content": user_eval_prompt}],
                    system_prompt=INTENT_CLASSIFIER_PROMPT,
                    requested_model="qwen-3.8",
                    temperature=0.1,
                    max_completion_tokens=600,
                )
                cleaned = _clean_json_markdown(res_text)
                data = json.loads(cleaned)
                classification = QueryIntentClassification(**data)
                if len(_INTENT_CACHE) > 500:
                    _INTENT_CACHE.clear()
                _INTENT_CACHE[cache_key] = classification
                return classification
            except Exception as e:
                print(f"Groq intent classification warning: {e}, attempting Gemini fallback.")

    # 2. Attempt Google Gemini Flash inference
    gemini_client, _ = get_gemini_client()
    if gemini_client:
        try:
            full_prompt = f"{INTENT_CLASSIFIER_PROMPT}\n\n{user_eval_prompt}"
            response = gemini_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=full_prompt,
            )
            raw_text = response.text or ""
            cleaned = _clean_json_markdown(raw_text)
            data = json.loads(cleaned)
            classification = QueryIntentClassification(**data)
            if len(_INTENT_CACHE) > 500:
                _INTENT_CACHE.clear()
            _INTENT_CACHE[cache_key] = classification
            return classification
        except Exception as e:
            print(f"Gemini intent classification warning: {e}, using deterministic fallback.")

    # 3. Fallback to deterministic token-boundary classifier
    fallback = _deterministic_intent_fallback(clean_p, attached_artifacts)
    if len(_INTENT_CACHE) > 500:
        _INTENT_CACHE.clear()
    _INTENT_CACHE[cache_key] = fallback
    return fallback


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


def classify_artifact_purpose(art: Dict[str, Any], prompt: str = "") -> str:
    """
    Classifies an attached artifact into its semantic operational role:
    - 'template': Formatting templates, report format specifications, markdown layouts, style guides
    - 'source': Tabular data, computational metrics, spreadsheets, structured figures
    - 'reference': Research briefings, background documents, PDFs, contextual references
    """
    if not isinstance(art, dict):
        return "reference"

    fname = str(art.get("filename") or art.get("name") or "").lower()
    ftype = str(art.get("type") or (fname.split(".")[-1] if "." in fname else "")).lower()
    source_type = str(art.get("source_type") or "").lower()
    content = str(art.get("content") or "")[:2000].lower()
    p_lower = prompt.lower()

    # 1. Template Classification
    template_cues = ["template", "format", "specification", "spec", "style_guide", "guideline", "outline", "layout", "executive_summary"]
    if art.get("type") == "template" or source_type == "template":
        return "template"
    if any(cue in fname for cue in template_cues):
        return "template"
    if ftype in ["md", "markdown"]:
        if any(cue in p_lower for cue in ["template", "format", "according to", "following the"]):
            return "template"
        if any(h in content for h in ["# template", "## executive summary", "## section", "## overview", "# format"]):
            return "template"

    # 2. Source Data Classification (Spreadsheets & Calculations)
    if ftype in ["xlsx", "xls", "csv", "tsv", "json", "parquet"]:
        return "source"
    source_cues = ["data", "metrics", "financials", "sales", "revenue", "calculation", "balance", "ledger", "dataset"]
    if any(cue in fname for cue in source_cues):
        return "source"

    # 3. Reference Classification (PDFs, Research, Contextual Docs)
    if ftype in ["pdf", "docx", "doc", "txt", "pptx", "ppt", "html"]:
        return "reference"

    # Default based on extension
    if ftype in ["md", "markdown"]:
        return "template"
    return "reference"


def assign_artifacts_to_steps(
    steps: List[Dict[str, Any]],
    attached_artifacts: Optional[List[Dict[str, Any]]],
    prompt: str = ""
) -> List[Dict[str, Any]]:
    """
    Judiciously assigns attached artifacts to specific workflow steps according to:
    1. Explicit prompt references (e.g. 'follow report_template.md', 'analyze data.xlsx')
    2. Semantic purpose matching (templates -> writer/synthesizer; sources -> analyst/excel; references -> researcher/parser)
    """
    if not attached_artifacts or not steps:
        for s in steps:
            if "resources" not in s:
                s["resources"] = []
        return steps

    p_lower = prompt.lower()

    # Prepared resource items with classified roles
    resources_by_role: Dict[str, List[Dict[str, Any]]] = {
        "template": [],
        "source": [],
        "reference": [],
    }
    all_prepared_resources: List[Dict[str, Any]] = []

    for art in attached_artifacts:
        if not isinstance(art, dict):
            continue
        role = classify_artifact_purpose(art, prompt)
        res_item = {
            "id": art.get("id"),
            "name": art.get("name") or art.get("filename"),
            "filename": art.get("filename") or art.get("name"),
            "type": art.get("type") or (art.get("filename", "").split(".")[-1] if "." in art.get("filename", "") else "file"),
            "content": art.get("content", ""),
            "size_bytes": art.get("size_bytes") or len(str(art.get("content", ""))),
            "is_base64": bool(art.get("is_base64")),
            "mime_type": art.get("mime_type"),
            "role": role,
            "source_title": art.get("source_title"),
        }
        resources_by_role[role].append(res_item)
        all_prepared_resources.append(res_item)

    # Initialize each step
    for s in steps:
        s["resources"] = []
        s["attached_artifact_ids"] = []

    assigned_resource_ids = set()

    # Phase 1: Explicit Prompt Mentions
    for res in all_prepared_resources:
        fname = (res.get("filename") or "").lower()
        if fname and fname in p_lower:
            best_step = None
            if res["role"] == "template":
                best_step = next(
                    (s for s in steps if s.get("agent_id") in ["writer", "synthesizer", "file_creator"] or "report" in s.get("name", "").lower()),
                    steps[-1]
                )
            elif res["role"] == "source":
                best_step = next(
                    (s for s in steps if s.get("agent_id") in ["data_analyst", "excel_specialist", "file_parser"] or "data" in s.get("name", "").lower() or "calculat" in s.get("name", "").lower()),
                    steps[0]
                )
            else:
                best_step = next(
                    (s for s in steps if s.get("agent_id") in ["researcher", "file_parser", "general_assistant"] or "research" in s.get("name", "").lower()),
                    steps[0]
                )

            if best_step:
                best_step["resources"].append(res)
                if res.get("id"):
                    best_step["attached_artifact_ids"].append(res["id"])
                assigned_resource_ids.add(res["id"] or res["filename"])

    # Phase 2: Role-Based Semantic Assignment for unassigned files
    for role, items in resources_by_role.items():
        unassigned = [i for i in items if (i["id"] or i["filename"]) not in assigned_resource_ids]
        if not unassigned:
            continue

        if role == "template":
            # Assign templates to writing/synthesis/delivery steps
            target_step = next(
                (s for s in reversed(steps) if s.get("agent_id") in ["writer", "synthesizer", "file_creator"] or any(k in s.get("name", "").lower() for k in ["synthesis", "briefing", "report", "authoring"])),
                steps[-1]
            )
            for itm in unassigned:
                target_step["resources"].append(itm)
                if itm.get("id"):
                    target_step["attached_artifact_ids"].append(itm["id"])
                assigned_resource_ids.add(itm["id"] or itm["filename"])

        elif role == "source":
            # Assign source data to analysis/computation/excel steps
            target_step = next(
                (s for s in steps if s.get("agent_id") in ["data_analyst", "excel_specialist", "file_parser"] or any(k in s.get("name", "").lower() for k in ["data", "computation", "statistical", "analytics", "cell"])),
                steps[0]
            )
            for itm in unassigned:
                target_step["resources"].append(itm)
                if itm.get("id"):
                    target_step["attached_artifact_ids"].append(itm["id"])
                assigned_resource_ids.add(itm["id"] or itm["filename"])

        elif role == "reference":
            # Assign research/reference documents to research/parsing/discovery steps
            target_step = next(
                (s for s in steps if s.get("agent_id") in ["researcher", "file_parser", "general_assistant"] or any(k in s.get("name", "").lower() for k in ["research", "discovery", "parsing", "extraction", "evidence"])),
                steps[0]
            )
            for itm in unassigned:
                target_step["resources"].append(itm)
                if itm.get("id"):
                    target_step["attached_artifact_ids"].append(itm["id"])
                assigned_resource_ids.add(itm["id"] or itm["filename"])

    # Phase 3: Fallback safety - if any item is still unassigned, attach to step 1
    for itm in all_prepared_resources:
        if (itm["id"] or itm["filename"]) not in assigned_resource_ids:
            steps[0]["resources"].append(itm)
            if itm.get("id"):
                steps[0]["attached_artifact_ids"].append(itm["id"])

    # Phase 4: Enrich step instructions with references to assigned resources
    for s in steps:
        if s.get("resources"):
            res_names = ", ".join([f"'{r.get('filename')}' ({r.get('role')})" for r in s["resources"]])
            s["instructions"] = f"{s.get('instructions', '').rstrip()}\n\n[Assigned Step Resources: {res_names}]\nCarefully utilize the provided resource contents attached to this step to fulfill your assigned operational objective."

    return steps


def build_workflow_from_intent(
    intent: QueryIntentClassification,
    prompt_clean: str,
    slug_id: str,
    art_ids: List[str],
    attached_artifacts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Declarative workflow factory mapping an evaluated QueryIntentClassification
    directly to a multi-agent DAG specification.
    """
    pri = intent.primary_intent
    steps: List[Dict[str, Any]] = []
    edges: List[Dict[str, str]] = []
    wf_title = intent.workflow_title
    wf_desc = intent.workflow_description

    # 1. Spreadsheet Operations (Excel Specialist)
    if pri == "spreadsheet_operations":
        excel_tools = [
            "introspect_spreadsheet",
            "resolve_coordinates",
            "edit_spreadsheet_cells",
            "execute_statistical_analysis",
            "relational_join_sheets",
            "create_pivot_table",
            "rollback_spreadsheet_transactions",
            "validate_workbook_integrity"
        ]
        if intent.requires_live_web_search:
            steps = [
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
                    "tool_ids": excel_tools,
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
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ]
        else:
            steps = [
                {
                    "id": "step_1",
                    "name": "Enterprise Spreadsheet & Cell Resolution Operations",
                    "step_type": "agent",
                    "agent_id": "excel_specialist",
                    "instructions": f"Translate natural language requests into exact cell coordinates, perform targeted mutations while strictly preserving all cell styling, formulas, number formats, and VBA macros, execute calculations, and validate schema integrity for: {prompt_clean}",
                    "tool_ids": excel_tools,
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": art_ids,
                    "depends_on": [],
                },
                {
                    "id": "step_2",
                    "name": "Computational Audit & Delivery Briefing",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Consolidate cell modifications, structural operations, and calculation audit summary into a cohesive final briefing directly fulfilling the user's goal: {{{{steps.step_1.output.text}}}} Goal: {prompt_clean}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_1"],
                },
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
            ]

    # 2. Document Authoring & Writing
    elif pri == "document_authoring":
        if intent.file_export_requested:
            steps = [
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
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ]
        elif intent.requires_live_web_search:
            steps = [
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
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ]
        else:
            steps = [
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
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
            ]

    # 3. Artifact Report (/artifact or PDF document context)
    elif pri == "artifact_report":
        if art_ids:
            step_1 = {
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
        elif intent.requires_live_web_search:
            step_1 = {
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
        else:
            step_1 = {
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
        steps = [
            step_1,
            {
                "id": "step_2",
                "name": "Template-Guided Report Drafting",
                "step_type": "agent",
                "agent_id": "writer",
                "instructions": f"Using the extracted context, draft a thorough, comprehensive report structured into clear sections directly adhering to the requested artifact template for: {prompt_clean}\n\nContext:\n{{{{steps.step_1.output.text}}}}",
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
        ]
        edges = [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_3"},
        ]

    # 4. Code Engineering
    elif pri == "code_engineering":
        steps = [
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
        ]
        edges = [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_3"},
        ]

    # 5. Strategic Planning
    elif pri == "strategic_planning":
        steps = [
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
        ]
        edges = [
            {"source": "step_1", "target": "step_2"},
        ]

    # 6. Market Intelligence (Stocks, Crypto, Equities)
    elif pri == "market_intelligence":
        if intent.file_export_requested:
            steps = [
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
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ]
        else:
            steps = [
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
                    "name": "Executive Market Briefing & Valuation Delivery",
                    "step_type": "agent",
                    "agent_id": "synthesizer",
                    "instructions": f"Deliver a cohesive financial briefing synthesizing all discovered market data, valuation ratios, and analytical insights directly fulfilling the user's goal '{prompt_clean}': {{{{steps.step_2.output.text}}}}",
                    "tool_ids": [],
                    "knowledge_file_ids": [],
                    "attached_artifact_ids": [],
                    "depends_on": ["step_2"],
                },
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ]

    # 7. Live Web Research
    elif pri == "live_web_research":
        if intent.file_export_requested:
            steps = [
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
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ]
        else:
            steps = [
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
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
            ]

    # 8. Data Analytics & Calculations
    elif pri == "data_analytics":
        if intent.file_export_requested:
            steps = [
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
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
                {"source": "step_2", "target": "step_3"},
            ]
        else:
            steps = [
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
            ]
            edges = [
                {"source": "step_1", "target": "step_2"},
            ]

    # 9. Document Parsing & Ingestion
    elif pri == "document_parsing":
        steps = [
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
        ]
        edges = [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_3"},
        ]

    # 10. Conversational Greeting (Single Step)
    elif pri == "conversational_greeting":
        steps = [
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
        ]
        edges = []

    # 11. General Inquiry (Default Coordinated 2-Step)
    else:
        steps = [
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
        ]
        edges = [
            {"source": "step_1", "target": "step_2"},
        ]

    steps = assign_artifacts_to_steps(steps, attached_artifacts, prompt_clean)

    return {
        "id": f"ephemeral_wf_{slug_id}",
        "title": f"{wf_title} ({slug_id})",
        "description": wf_desc,
        "goal": prompt_clean,
        "is_ephemeral": True,
        "is_multi_step": intent.is_multi_step,
        "intent_analysis": {
            "primary_intent": intent.primary_intent,
            "requires_live_web_search": intent.requires_live_web_search,
            "file_export_requested": intent.file_export_requested,
            "export_format": intent.export_format,
            "reasoning": intent.reasoning,
        },
        "steps": steps,
        "edges": edges,
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
        single_step = {
            "id": "step_1",
            "name": f"{agent_name} Task",
            "step_type": "agent",
            "agent_id": target_agent_id,
            "model": model_override,
            "instructions": prompt_clean,
            "tool_ids": [],
            "knowledge_file_ids": [],
            "attached_artifact_ids": art_ids,
            "resources": [],
            "depends_on": [],
        }
        steps = assign_artifacts_to_steps([single_step], attached_artifacts, prompt_clean)
        return {
            "id": f"ephemeral_wf_{slug_id}",
            "title": f"{agent_name} Execution Plan ({slug_id})",
            "description": f"Direct single-agent workflow for {agent_name}.",
            "goal": prompt_clean,
            "is_ephemeral": True,
            "is_multi_step": False,
            "steps": steps,
            "edges": [],
        }

    # 2. LLM-Driven Intent Analysis (Single-Pass Semantic Evaluation)
    intent = analyze_query_intent(prompt_clean, attached_artifacts)
    return build_workflow_from_intent(intent, prompt_clean, slug_id, art_ids, attached_artifacts=attached_artifacts)
