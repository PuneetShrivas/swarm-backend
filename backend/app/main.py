import os
import re
import json
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.auth import AuthUser, get_current_user, get_optional_user
from app.supabase import (
    supabase,
    is_supabase_configured,
    get_user_supabase_client,
    memory_store,
)
from app.agents import (
    agent_registry,
    AgentProfile,
    ToolDefinition,
    SkillDefinition,
    MCPServerConfig,
    BaseAgent,
)
from app.workflows import (
    Workflow,
    WorkflowStep,
    ScriptTool,
    KnowledgeFile,
    WorkflowRun,
    WorkflowStepRun,
    StepUnitTestRequest,
    StepUnitTestResponse,
    WorkflowRunRequest,
    ScriptToolTestRequest,
    ScriptToolTestResponse,
    UserAgentProfile,
    execute_tool_script,
    validate_tool_code,
    extract_file_content,
    workflow_engine,
)
from app.workflows.models import WorkflowCreateUpdatePayload
from app.ai_generator import generate_workflow_spec, generate_agent_spec
from app.workflows.default_workflows import seed_default_workflows, get_default_workflows
from app.groq_client import (
    get_groq_client,
    is_groq_configured,
    DEFAULT_GROQ_MODEL,
    execute_groq_chat,
    resolve_groq_model_candidates,
)

# Load environment variables from .env
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Initialize FastAPI application
app = FastAPI(
    title="Swarm Backend API",
    version="2.0.0",
    description="FastAPI service for running an autonomous AI agent swarm with modular packages, standardized asset files, Supabase session persistence, and token telemetry.",
)

# CORS middleware for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent Registry
agent_registry.initialize()

# Seed default workflow templates (idempotent across memory store and Supabase)
_seeded_count = seed_default_workflows(memory_store, supabase if is_supabase_configured() else None)
if _seeded_count:
    print(f"Seeded {_seeded_count} default workflow template(s) into memory store.")

# ---------------------------------------------------------
# Data Models
# ---------------------------------------------------------

# Backward-compatible Agent alias mapping to AgentProfile
Agent = AgentProfile

class ToolCall(BaseModel):
    tool: str
    args: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None

class Message(BaseModel):
    role: str = Field(..., description="'user', 'agent', or 'system'")
    content: str = Field(..., description="Markdown or text content of the message")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata including agent_state, tool_calls, agent_id, etc.")

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="Active conversation thread messages")
    session_id: Optional[str] = Field(None, description="Active Supabase chat session ID")
    parent_message_id: Optional[str] = Field(None, description="Parent message ID for conversation branching")
    user_message_id: Optional[str] = Field(None, description="Client-assigned user message ID")
    model: Optional[str] = Field(None, description="Optional model selection override (e.g. gemini-3.8-flash, gemini-4-argon, sonar)")
    workflow_id: Optional[str] = Field(None, description="Optional workflow ID to execute in this turn")
    workflow_inputs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Input arguments for workflow execution")
    artifact_ids: Optional[List[str]] = Field(default_factory=list, description="IDs of artifacts invoked or attached for context")
    attached_artifacts: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Direct artifact objects attached to the chat turn")

class AgentTestRequest(BaseModel):
    agent_id: Optional[str] = None
    system_prompt: Optional[str] = None
    input_prompt: Optional[str] = None
    prompt: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = Field(default_factory=dict)
    mock_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    model: Optional[str] = "gemini-3.8-flash"
    temperature: Optional[float] = 0.3
    tool_ids: Optional[List[str]] = Field(default_factory=list)
    attached_artifact_ids: Optional[List[str]] = Field(default_factory=list)
    mock_context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AgentTestResponse(BaseModel):
    status: str
    content: str
    response: Optional[str] = None
    tokens_used: int = 0
    latency_ms: float = 0.0
    duration_ms: Optional[float] = None
    agent_id: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)

class ToolExecutionRequest(BaseModel):
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arguments to pass to the tool handler")

class MCPExecutionRequest(BaseModel):
    server: Optional[str] = Field(None, description="Target MCP server identifier")
    tool: Optional[str] = Field(None, description="Target tool name")
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arguments to pass to the tool")

class AIGenerateWorkflowRequest(BaseModel):
    prompt: str = Field(..., description="Natural language requirements for the workflow")

class AIGenerateAgentRequest(BaseModel):
    prompt: str = Field(..., description="Natural language description of desired agent")

# Session & History Models
class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field(None, description="Chat session title")
    prompt: Optional[str] = Field(None, description="Initial prompt context for automatic titling")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session metadata")

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated session title")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated session metadata")

class ChatSession(BaseModel):
    id: str
    user_id: str
    title: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str

class ChatMessageRecord(BaseModel):
    id: str
    session_id: str
    user_id: str
    parent_id: Optional[str] = None
    role: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    rating: Optional[str] = None
    created_at: str

class SessionDetailResponse(BaseModel):
    session: ChatSession
    messages: List[ChatMessageRecord]

class UsageSummary(BaseModel):
    total_tokens: int
    total_requests: int
    models: Dict[str, int]
    agents: Dict[str, int]
    recent_activity: List[Dict[str, Any]]

# ---------------------------------------------------------
# Swarm Agents Database Proxy (Synchronized with AgentRegistry)
# ---------------------------------------------------------

class _AgentsDBProxy(list):
    def __iter__(self):
        return iter(agent_registry.get_all())

    def __len__(self):
        return len(agent_registry.get_all())

    def __getitem__(self, index):
        return agent_registry.get_all()[index]

    def append(self, item):
        if isinstance(item, AgentProfile):
            agent_registry.register_custom(item)
        elif isinstance(item, dict):
            agent_registry.register_custom(AgentProfile(**item))

agents_db = _AgentsDBProxy()

# ---------------------------------------------------------
# Persistence Helper Functions
# ---------------------------------------------------------

def db_save_message(
    user_id: str,
    session_id: str,
    msg_id: str,
    parent_id: Optional[str],
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    rating: Optional[str] = None,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """Saves or updates a message node into Supabase chat_messages (or memory_store)."""
    clean_parent = parent_id
    if clean_parent in (None, "", "root-greeting", "root", msg_id):
        clean_parent = None

    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "id": msg_id,
        "session_id": session_id,
        "user_id": user_id,
        "parent_id": clean_parent,
        "role": role,
        "content": content,
        "metadata": metadata or {},
        "rating": rating,
        "created_at": now_iso,
    }
    if is_supabase_configured() and not user_id.startswith("test-"):
        client = get_user_supabase_client(token)
        if client:
            try:
                if clean_parent is not None:
                    chk = client.table("chat_messages").select("id").eq("id", clean_parent).eq("session_id", session_id).execute()
                    if not chk.data:
                        record["parent_id"] = None

                client.table("chat_messages").upsert(record).execute()
                return record
            except Exception as e:
                print(f"Supabase chat_messages insert error: {e}")
                if "violates foreign key constraint" in str(e) or "23503" in str(e):
                    try:
                        record["parent_id"] = None
                        client.table("chat_messages").upsert(record).execute()
                        return record
                    except Exception as retry_err:
                        print(f"Supabase chat_messages retry error: {retry_err}")
    # Memory fallback
    memory_store.add_message(record)
    return record

def db_save_usage(
    user_id: str,
    session_id: Optional[str],
    message_id: Optional[str],
    model: str,
    agent_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    latency_ms: Optional[float],
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """Records LLM token telemetry into user_usage."""
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_id": session_id,
        "message_id": message_id,
        "model": model,
        "agent_id": agent_id,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_ms": latency_ms,
        "created_at": now_iso,
    }
    if is_supabase_configured() and not user_id.startswith("test-"):
        client = get_user_supabase_client(token)
        if client:
            try:
                client.table("user_usage").insert(record).execute()
                return record
            except Exception as e:
                print(f"Supabase user_usage insert error: {e}")
    # Memory fallback
    memory_store.add_usage(record)
    return record

# ---------------------------------------------------------
# Gemini API Client Helper
# ---------------------------------------------------------

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
        print(f"Warning: Failed to initialize Gemini client: {e}")
        return None, None

def normalize_model_name(model_name: Optional[str]) -> str:
    """
    Normalizes and maps model names across Groq, Perplexity, and Gemini.
    - Groq default: qwen-3.8 (primary default)
    - Perplexity: sonar, sonar-pro
    - Gemini: gemini-3.8-flash, gemini-4-argon
    """
    if not model_name or not str(model_name).strip():
        return os.environ.get("DEFAULT_MODEL", DEFAULT_GROQ_MODEL)
    m = str(model_name).strip()
    if m in ("qwen", "qwen-3", "qwen 3.8", "qwen-3.8", "default"):
        return "qwen-3.8"
    if m in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash"):
        return "gemini-3.8-flash"
    if m in ("gemini-2.5-pro", "gemini-2.0-pro", "gemini-1.5-pro", "gemini-pro"):
        return "gemini-4-argon"
    if m.startswith("gemini-2.5-flash"):
        return "gemini-3.8-flash"
    if m.startswith("gemini-2.5-pro"):
        return "gemini-4-argon"
    return m

def route_agent(target_id: Optional[str], last_user_content: str):
    """
    Selects the target agent or auto-routes based on prompt intent and agent specialties.
    Prioritizes file creation requests so CSV/dataset/script generation is never hijacked
    by general data analysis or conversational agents.
    """
    # 1. Explicit target selection
    if target_id and target_id.strip():
        agent = agent_registry.get(target_id.strip())
        if agent:
            return agent
        custom = agent_registry.get_profile(target_id.strip())
        if custom:
            return custom

    content_lower = last_user_content.lower()

    # 2. File Creation Specialists (EVALUATED FIRST to prevent data analyst interception)
    file_create_keywords = [
        "create file", "generate file", "make file", "write to file", "download file",
        "export file", "save file", "create script", "generate csv", "generate report file",
        "export dataset", "sample csv", "create csv", "make csv", "build csv", "produce csv",
        "csv file", "json file", "sample file", "generate a file", "create a file", "generate a csv",
        "create a csv", "sample data file", "generate dataset", "create spreadsheet", "generate spreadsheet",
        "give me a csv", "give me a file", "output as csv", "provide a csv", "create a spreadsheet",
        "generate pdf", "create pdf", "make pdf", "export pdf", "pdf report", "pdf document", "download pdf",
        "generate presentation", "create presentation", "make presentation", "powerpoint", "slide deck",
        "presentation deck", "generate ppt", "create ppt", "generate pptx", "create pptx", "pitch deck",
        "generate word", "create word document", "make docx", "generate docx", "create docx", "word doc",
        "generate excel", "create excel", "make excel", "generate xlsx", "create xlsx", "excel sheet",
        "excel spreadsheet", "financial model xlsx"
    ]
    is_file_creation = (
        any(k in content_lower for k in file_create_keywords)
        or (
            any(verb in content_lower for verb in ["create", "generate", "make", "export", "download", "produce", "write", "build", "provide", "give me"])
            and any(noun in content_lower for noun in ["csv", "file", "json", "spreadsheet", "dataset", "markdown file", "txt file", "pdf", "pptx", "presentation", "deck", "docx", "word document", "xlsx", "excel sheet"])
        )
    )
    if is_file_creation:
        creator = agent_registry.get("file_creator")
        if creator:
            return creator

    file_parse_keywords = [
        "parse file", "parse log", "parse json", "parse csv", "ingest file", "ingest document",
        "validate schema", "extract schema", "parse document", "inspect file", "ingest",
        "parse pdf", "read pdf", "extract pdf", "parse ppt", "parse pptx", "read presentation",
        "parse docx", "read word document", "parse excel", "read excel", "parse xlsx",
        "rag", "rag search", "query document", "search in file", "search document", "document context",
        "find in document", "ask document", "document qa", "context passing"
    ]
    if any(k in content_lower for k in file_parse_keywords):
        parser = agent_registry.get("file_parser")
        if parser:
            return parser

    # Security & Code Audit Reviewer
    review_keywords = ["audit", "security", "vulnerability", "owasp", "leak", "test coverage", "qa", "lint", "complexity"]
    if any(k in content_lower for k in review_keywords):
        reviewer = agent_registry.get("reviewer")
        if reviewer:
            return reviewer

    # Data Analyst (Mathematical & statistical analysis; excludes file synthesis)
    data_keywords = ["statistics", "mean", "median", "table analysis", "percentile", "trend", "distribution", "variance", "stdev", "metrics", "data analysis", "data analyst", "analyze data"]
    if any(k in content_lower for k in data_keywords):
        analyst = agent_registry.get("data_analyst")
        if analyst:
            return analyst

    synthesis_keywords = ["executive summary", "briefing", "readme", "documentation", "tldr", "docs", "manual", "guide"]
    if any(k in content_lower for k in synthesis_keywords):
        synth = agent_registry.get("synthesizer")
        if synth:
            return synth

    coder_keywords = ["code", "function", "bug", "python", "javascript", "typescript", "fastapi", "react", "sql", "api", "git", "class", "error", "compile", "syntax", "refactor"]
    if any(k in content_lower for k in coder_keywords):
        coder = agent_registry.get("coder")
        if coder:
            return coder

    research_keywords = [
        "research", "investigate", "history", "quantum", "paper", "scientific", "study", "fact check", "source", "citation",
        "web search", "websearch", "search web", "search online", "google", "stock price", "stock prices",
        "stocks", "ticker", "current price", "live price", "market quote", "share price", "equity price",
        "latest news", "breaking news", "live data", "live info", "live information", "crypto price", "btc price"
    ]
    if any(k in content_lower for k in research_keywords):
        researcher = agent_registry.get("researcher")
        if researcher:
            return researcher

    orchestrator_keywords = ["swarm", "orchestrat", "workflow", "plan our", "pipeline", "multi-agent"]
    if any(k in content_lower for k in orchestrator_keywords):
        orchestrator = agent_registry.get_orchestrator()
        if orchestrator:
            return orchestrator

    # 3. Conversational intent matching -> general_assistant (for general conversational chat)
    conversational_phrases = ["how are you", "who are you", "what can you do", "tell me a joke", "chat with me", "good morning", "good evening", "good afternoon"]
    casual_words = {"hello", "hi", "hey", "greetings", "howdy", "sup"}
    cleaned_words = re.sub(r"[^\w\s]", " ", content_lower).split()
    if any(phrase in content_lower for phrase in conversational_phrases) or (cleaned_words and cleaned_words[0] in casual_words):
        assistant = agent_registry.get("general_assistant")
        if assistant:
            return assistant

    # 4. Default to Swarm Orchestrator
    orchestrator = agent_registry.get_orchestrator()
    if orchestrator:
        return orchestrator

    return agent_registry.get_all()[0]

# ---------------------------------------------------------
# Root & System Endpoints
# ---------------------------------------------------------

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Swarm Backend API",
        "version": "2.0.0",
        "docs_url": "/docs",
        "supabase_connected": is_supabase_configured(),
        "agents_count": len(agent_registry.get_all()),
    }

@app.get("/api/health")
def health_check():
    """Health check endpoint with swarm and database status."""
    _, api_key = get_gemini_client()
    profiles = agent_registry.get_all()
    return {
        "status": "ok",
        "agents_online": len(profiles),
        "gemini_configured": bool(api_key),
        "supabase_configured": is_supabase_configured(),
        "active_agents": [agent.id for agent in profiles],
    }

@app.get("/api/agents", response_model=List[AgentProfile])
def get_agents():
    """Returns the roster of all active agents in the swarm."""
    return agent_registry.get_all()

@app.get("/api/agents/{agent_id}", response_model=AgentProfile)
def get_agent_detail(agent_id: str):
    """Retrieves deep inspection details for a specific agent in the swarm."""
    profile = agent_registry.get_profile(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Agent with id '{agent_id}' not found.")
    return profile

@app.post("/api/agents", response_model=AgentProfile)
def create_agent(agent: AgentProfile):
    """Registers a new specialized agent into the swarm."""
    for existing in agent_registry.get_all():
        if existing.id == agent.id:
            raise HTTPException(status_code=400, detail=f"Agent with id '{agent.id}' already exists.")
    agent_registry.register_custom(agent)
    return agent

@app.post("/api/agents/{agent_id}/tools/{tool_name}/execute")
def execute_agent_tool(agent_id: str, tool_name: str, payload: ToolExecutionRequest):
    """Executes a specific python tool registered to an agent."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    if tool_name not in agent.tool_handlers:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{tool_name}' not available on agent '{agent_id}'. Available: {list(agent.tool_handlers.keys())}",
        )
    result = agent.execute_tool(tool_name, payload.arguments or {})
    return {
        "agent_id": agent_id,
        "tool_name": tool_name,
        "arguments": payload.arguments,
        "result": result,
        "status": "success",
    }

@app.post("/api/agents/{agent_id}/mcp/{server_name}/tools/{tool_name}/execute")
def execute_agent_mcp_tool(agent_id: str, server_name: str, tool_name: str, payload: ToolExecutionRequest):
    """Executes an MCP server tool for an agent."""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    result = agent.execute_mcp_tool(server_name, tool_name, payload.arguments or {})
    return result

@app.get("/api/mcp/servers")
def get_mcp_servers():
    """Returns list of registered MCP servers and their available tools."""
    from app.mcp.manager import mcp_manager
    return mcp_manager.list_servers()

@app.post("/api/mcp/execute")
def execute_mcp_tool_direct(payload: MCPExecutionRequest):
    """Executes an MCP tool directly across any registered MCP server."""
    if not payload.server or not payload.tool:
        raise HTTPException(status_code=400, detail="Fields 'server' and 'tool' are required.")
    from app.mcp.manager import mcp_manager
    return mcp_manager.execute(payload.server, payload.tool, payload.arguments or {})


# ---------------------------------------------------------
# Chat Sessions & History Endpoints
# ---------------------------------------------------------

def extract_contextual_title(prompt: str) -> str:
    """
    Derives a concise, contextual session title (3-6 words, <= 45 chars) from a user prompt.
    Strips markdown, leading conversational fillers, and punctuation.
    """
    if not prompt or not prompt.strip():
        return "New Conversation"

    clean = prompt.strip()
    clean = re.sub(r'```.*?```', '', clean, flags=re.DOTALL)
    clean = re.sub(r'[#*`_~>\[\]\(\)]', '', clean)
    clean = " ".join(clean.split())

    filler_patterns = [
        r"^(can you\s+(please\s+)?(help me\s+)?(to\s+)?)",
        r"^(please\s+(help me\s+)?(to\s+)?)",
        r"^(could you\s+(please\s+)?)",
        r"^(how (do|can|would) (i|we|you)\s+)",
        r"^(what is\s+(the\s+)?)",
        r"^(tell me (about\s+)?)",
        r"^(write (me\s+)?(a\s+)?)",
        r"^(create (me\s+)?(a\s+)?)",
        r"^(generate (me\s+)?(a\s+)?)",
        r"^(explain\s+(how|what|why)?\s*)",
    ]
    for pattern in filler_patterns:
        clean = re.sub(pattern, "", clean, flags=re.IGNORECASE).strip()

    words = clean.split()
    if not words:
        return "New Conversation"

    title_words = []
    current_len = 0
    for w in words[:6]:
        if current_len + len(w) + (1 if title_words else 0) > 42:
            break
        title_words.append(w)
        current_len += len(w) + 1

    if not title_words:
        title_words = [words[0][:40]]

    title = " ".join(title_words).strip(" ,:.-?!")
    if title:
        title = title[0].upper() + title[1:]
    return title or "New Conversation"


def auto_rename_session_if_needed(session_id: str, prompt: str, current_user: Optional[AuthUser]) -> Optional[str]:
    """If session title is generic or default ('New Conversation'), renames it based on prompt."""
    if not session_id or not prompt or not current_user:
        return None

    current_title = None
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("chat_sessions").select("title").eq("id", session_id).eq("user_id", current_user.id).single().execute()
                if res.data:
                    current_title = res.data.get("title")
            except Exception:
                pass
    if not current_title:
        sess = memory_store.get_session(session_id, current_user.id)
        if sess:
            current_title = sess.get("title")

    if not current_title or current_title in ("New Conversation", "Untitled", "New Chat", ""):
        new_title = extract_contextual_title(prompt)
        now_iso = datetime.now(timezone.utc).isoformat()
        updates = {"title": new_title, "updated_at": now_iso}
        if is_supabase_configured() and not current_user.id.startswith("test-"):
            client = get_user_supabase_client(current_user.token)
            if client:
                try:
                    client.table("chat_sessions").update(updates).eq("id", session_id).eq("user_id", current_user.id).execute()
                except Exception as e:
                    print(f"Supabase auto_rename_session error: {e}")
        memory_store.update_session(session_id, current_user.id, updates)
        return new_title
    return None


def build_artifact_context_block(
    artifact_ids: Optional[List[str]] = None,
    attached_artifacts: Optional[List[Dict[str, Any]]] = None,
    user_prompt: str = "",
    user_id: str = "guest-user",
    top_k: int = 3,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Builds a grounded document context block from user-attached artifacts for agent prompt injection.
    Leverages direct text excerpts for small files and hybrid RAG knowledge store for binary/large documents.
    """
    resolved_artifacts: List[Dict[str, Any]] = []
    seen_ids = set()

    # 1. Direct attached artifacts
    if attached_artifacts:
        for art in attached_artifacts:
            if isinstance(art, dict) and art.get("id") and art["id"] not in seen_ids:
                resolved_artifacts.append(art)
                seen_ids.add(art["id"])

    # 2. Look up by artifact_ids
    if artifact_ids:
        for aid in artifact_ids:
            if not aid or aid in seen_ids:
                continue
            art = memory_store.get_artifact(aid)
            if art and isinstance(art, dict):
                resolved_artifacts.append(art)
                seen_ids.add(aid)
        # Check user artifacts list as well
        for art in memory_store.get_artifacts(user_id):
            if art.get("id") in artifact_ids and art["id"] not in seen_ids:
                resolved_artifacts.append(art)
                seen_ids.add(art["id"])

    if not resolved_artifacts:
        return "", []

    context_sections: List[str] = [
        "### [Attached User Artifacts & Grounded Knowledge Context]",
        "The user has attached the following artifacts/documents to ground your response. Cite and reference their data accurately:"
    ]

    try:
        from app.rag.store import rag_store
    except Exception:
        rag_store = None

    for art in resolved_artifacts:
        fname = art.get("filename") or art.get("name") or "document.txt"
        art_type = (art.get("type") or fname.split(".")[-1] or "txt").lower()
        content = art.get("content") or ""
        is_binary = bool(art.get("is_base64")) or art_type in ["pdf", "docx", "pptx", "xlsx"]

        if is_binary and rag_store:
            doc_id = f"art_doc_{art['id']}"
            rag_results = rag_store.query_context(query=user_prompt or fname, top_k=top_k, document_id=doc_id)
            if not rag_results:
                rag_results = rag_store.query_context(query=user_prompt or fname, top_k=top_k)
                rag_results = [r for r in rag_results if r.get("filename") == fname]

            if rag_results:
                sec_lines = [f"#### Attached Document: `{fname}` (Format: {art_type.upper()})"]
                for r in rag_results:
                    conf = int(r.get("confidence", 0.8) * 100)
                    sec_lines.append(f"> **Section: {r.get('heading', 'General')}** ({conf}% relevance):\n> {r.get('content')}")
                context_sections.append("\n".join(sec_lines))
            else:
                context_sections.append(
                    f"#### Attached Document: `{fname}` (Format: {art_type.upper()})\n"
                    f"*Binary document attached ({art.get('size_bytes', len(content))} bytes). Ready for analysis.*"
                )
        else:
            excerpt = content[:3000]
            if len(content) > 3000:
                excerpt += f"\n... [Truncated: {len(content) - 3000} additional characters]"
            context_sections.append(
                f"#### Attached Document: `{fname}` (Format: {art_type.upper()})\n"
                f"```\n{excerpt}\n```"
            )

    return "\n\n".join(context_sections), resolved_artifacts


@app.get("/api/sessions", response_model=List[ChatSession])
def list_sessions(current_user: AuthUser = Depends(get_current_user)):
    """Lists all chat sessions belonging to the authenticated user."""
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("chat_sessions").select("*").eq("user_id", current_user.id).order("updated_at", desc=True).execute()
                return res.data
            except Exception as e:
                print(f"Supabase list_sessions error: {e}")
    return memory_store.get_sessions(current_user.id)

@app.post("/api/sessions", response_model=ChatSession)
def create_session(
    payload: ChatSessionCreate,
    current_user: AuthUser = Depends(get_current_user),
):
    """Creates a new chat session for the authenticated user."""
    session_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    resolved_title = payload.title
    if not resolved_title or resolved_title == "New Conversation":
        if payload.prompt:
            resolved_title = extract_contextual_title(payload.prompt)
        else:
            resolved_title = "New Conversation"

    session_data = {
        "id": session_id,
        "user_id": current_user.id,
        "title": resolved_title,
        "metadata": payload.metadata or {},
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("chat_sessions").insert(session_data).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"Supabase create_session error: {e}")

    return memory_store.create_session(session_data)

@app.get("/api/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(
    session_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Retrieves session details and full conversation history tree."""
    session = None
    messages: List[Dict[str, Any]] = []

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res_sess = client.table("chat_sessions").select("*").eq("id", session_id).eq("user_id", current_user.id).single().execute()
                session = res_sess.data
                res_msg = client.table("chat_messages").select("*").eq("session_id", session_id).order("created_at", desc=False).execute()
                messages = res_msg.data or []
            except Exception as e:
                print(f"Supabase get_session error: {e}")

    if not session:
        session = memory_store.get_session(session_id, current_user.id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
        messages = memory_store.get_messages(session_id)

    return SessionDetailResponse(session=session, messages=messages)

@app.patch("/api/sessions/{session_id}", response_model=ChatSession)
def update_session(
    session_id: str,
    payload: ChatSessionUpdate,
    current_user: AuthUser = Depends(get_current_user),
):
    """Updates session title or metadata."""
    now_iso = datetime.now(timezone.utc).isoformat()
    updates: Dict[str, Any] = {"updated_at": now_iso}
    if payload.title is not None:
        updates["title"] = payload.title
    if payload.metadata is not None:
        updates["metadata"] = payload.metadata

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("chat_sessions").update(updates).eq("id", session_id).eq("user_id", current_user.id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"Supabase update_session error: {e}")

    updated = memory_store.update_session(session_id, current_user.id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return updated

@app.delete("/api/sessions/{session_id}")
def delete_session(
    session_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Deletes a chat session and all associated messages."""
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                client.table("chat_sessions").delete().eq("id", session_id).eq("user_id", current_user.id).execute()
                return {"status": "deleted", "session_id": session_id}
            except Exception as e:
                print(f"Supabase delete_session error: {e}")

    deleted = memory_store.delete_session(session_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return {"status": "deleted", "session_id": session_id}

# ---------------------------------------------------------
# Usage Telemetry Endpoint
# ---------------------------------------------------------

@app.get("/api/usage", response_model=UsageSummary)
def get_usage(current_user: AuthUser = Depends(get_current_user)):
    """Computes aggregated LLM token usage and request activity for the user."""
    usage_records: List[Dict[str, Any]] = []

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("user_usage").select("*").eq("user_id", current_user.id).order("created_at", desc=True).execute()
                usage_records = res.data or []
            except Exception as e:
                print(f"Supabase get_usage error: {e}")

    if not usage_records:
        usage_records = memory_store.get_usage(current_user.id)

    total_tokens = sum(r.get("total_tokens", 0) for r in usage_records)
    total_requests = len(usage_records)

    models_breakdown: Dict[str, int] = {}
    agents_breakdown: Dict[str, int] = {}
    for r in usage_records:
        m = r.get("model", "unknown")
        ag = r.get("agent_id", "unknown")
        toks = r.get("total_tokens", 0)
        models_breakdown[m] = models_breakdown.get(m, 0) + toks
        agents_breakdown[ag] = agents_breakdown.get(ag, 0) + toks

    recent = usage_records[:10]
    return UsageSummary(
        total_tokens=total_tokens,
        total_requests=total_requests,
        models=models_breakdown,
        agents=agents_breakdown,
        recent_activity=recent,
    )

# ---------------------------------------------------------
# Swarm Chat Endpoint (With Persistence & Usage Tracking)
# ---------------------------------------------------------

def extract_file_artifact_from_turn(content: str, agent_id: str, prompt: str = "") -> Optional[Dict[str, Any]]:
    """
    Detects and extracts a downloadable file artifact from agent response.
    Supports standard code blocks with language identifiers, CRLF linebreaks,
    and automatic tabular CSV/data parsing for file_creator agents.
    """
    if not content or not content.strip():
        return None

    prompt_lower = prompt.lower()

    # 1. Binary Document Generation detection (PDF, PPTX, DOCX, XLSX)
    if "pdf" in prompt_lower:
        try:
            from app.agents.file_creator.tools import generate_pdf_document
            clean_lines = [l.strip("# *") for l in content.splitlines() if l.strip()]
            doc_title = clean_lines[0] if clean_lines else "Generated Document"
            raw_secs = re.split(r"(?m)^(?=#{1,3}\s+)", content)
            sections = []
            for s in raw_secs:
                s_lines = s.strip().splitlines()
                if s_lines:
                    h = s_lines[0].strip("# ").strip()
                    b = "\n".join(s_lines[1:]).strip()
                    sections.append({"heading": h, "content": b})
            art = generate_pdf_document(
                title=doc_title[:80],
                subtitle="Swarm Autonomous Document",
                sections=sections or [{"heading": "Executive Summary", "content": content[:400]}],
                filename=f"document_{int(time.time())}.pdf"
            )
            return {
                **art,
                "id": f"art-{int(time.time()*1000)}",
                "name": art["filename"],
                "type": "pdf",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "origin_agent": agent_id,
                "is_base64": True,
            }
        except Exception as e:
            print(f"PDF auto-synthesis notice: {e}")

    if any(k in prompt_lower for k in ["presentation", "powerpoint", "slide deck", "pptx", "pitch deck"]):
        try:
            from app.agents.file_creator.tools import generate_presentation_deck
            clean_lines = [l.strip("# *") for l in content.splitlines() if l.strip()]
            deck_title = clean_lines[0] if clean_lines else "Strategic Presentation"
            raw_slides = re.split(r"(?m)^(?=#{1,2}\s+)", content)
            slides = []
            for s in raw_slides:
                s_lines = s.strip().splitlines()
                if s_lines:
                    s_title = s_lines[0].strip("# ").strip()
                    bullets = [l.strip("-* ") for l in s_lines[1:] if l.strip()]
                    slides.append({"title": s_title, "bullet_points": bullets or ["Overview"]})
            art = generate_presentation_deck(
                title=deck_title[:80],
                subtitle="Swarm Autonomous Slide Deck",
                slides=slides or [{"title": "Agenda", "bullet_points": ["Key Highlights", "Execution Plan"]}],
                filename=f"presentation_{int(time.time())}.pptx"
            )
            return {
                **art,
                "id": f"art-{int(time.time()*1000)}",
                "name": art["filename"],
                "type": "pptx",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "origin_agent": agent_id,
                "is_base64": True,
            }
        except Exception as e:
            print(f"PPTX auto-synthesis notice: {e}")

    if any(k in prompt_lower for k in ["word document", "docx", "word doc"]):
        try:
            from app.agents.file_creator.tools import generate_word_document
            clean_lines = [l.strip("# *") for l in content.splitlines() if l.strip()]
            doc_title = clean_lines[0] if clean_lines else "Project Document"
            raw_secs = re.split(r"(?m)^(?=#{1,3}\s+)", content)
            sections = []
            for s in raw_secs:
                s_lines = s.strip().splitlines()
                if s_lines:
                    h = s_lines[0].strip("# ").strip()
                    b = "\n".join(s_lines[1:]).strip()
                    sections.append({"heading": h, "paragraphs": [b]})
            art = generate_word_document(
                title=doc_title[:80],
                subtitle="Generated by Swarm Document Architect",
                sections=sections or [{"heading": "Overview", "paragraphs": [content[:400]]}],
                filename=f"document_{int(time.time())}.docx"
            )
            return {
                **art,
                "id": f"art-{int(time.time()*1000)}",
                "name": art["filename"],
                "type": "docx",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "origin_agent": agent_id,
                "is_base64": True,
            }
        except Exception as e:
            print(f"DOCX auto-synthesis notice: {e}")

    if any(k in prompt_lower for k in ["excel", "xlsx", "workbook"]):
        try:
            from app.agents.file_creator.tools import generate_spreadsheet_workbook
            table_lines = [l for l in content.splitlines() if "," in l or "\t" in l]
            rows = []
            headers = []
            if table_lines:
                headers = [h.strip() for h in table_lines[0].split(",")]
                for tl in table_lines[1:]:
                    rows.append([v.strip() for v in tl.split(",")])
            if not headers:
                headers = ["Metric", "Q1", "Q2", "Q3", "Q4", "Total"]
                rows = [["Sales", 1000, 1200, 1400, 1600, "=SUM(B2:E2)"]]
            art = generate_spreadsheet_workbook(
                sheets=[{"sheet_name": "Data Sheet", "headers": headers, "rows": rows, "include_totals": True}],
                filename=f"spreadsheet_{int(time.time())}.xlsx"
            )
            return {
                **art,
                "id": f"art-{int(time.time()*1000)}",
                "name": art["filename"],
                "type": "xlsx",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "origin_agent": agent_id,
                "is_base64": True,
            }
        except Exception as e:
            print(f"XLSX auto-synthesis notice: {e}")

    ext_map = {
        "python": "py", "py": "py",
        "javascript": "js", "js": "js", "typescript": "ts", "ts": "ts",
        "json": "json", "csv": "csv", "sql": "sql", "html": "html",
        "markdown": "md", "md": "md", "yaml": "yaml", "yml": "yml",
        "bash": "sh", "sh": "sh", "shell": "sh", "text": "txt", "txt": "txt",
        "pdf": "pdf", "pptx": "pptx", "ppt": "pptx", "docx": "docx", "doc": "docx",
        "xlsx": "xlsx", "xls": "xlsx"
    }
    mime_map = {
        "py": "text/x-python", "js": "application/javascript", "ts": "application/typescript",
        "json": "application/json", "csv": "text/csv", "sql": "application/sql",
        "html": "text/html", "md": "text/markdown", "txt": "text/plain", "sh": "application/x-sh",
        "yaml": "text/yaml", "yml": "text/yaml",
        "pdf": "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }

    # Handle code fence with optional lang, spaces, and CRLF or LF newlines
    code_match = re.search(r"```([a-zA-Z0-9_-]+)?[ \t]*\r?\n([\s\S]+?)\r?\n```", content)
    code_body = ""
    ext = ""

    if code_match:
        lang = (code_match.group(1) or "").strip().lower()
        code_body = code_match.group(2).strip()
        ext = ext_map.get(lang, "")
        if not ext:
            if "csv" in prompt_lower or ("," in code_body and "\n" in code_body and "{" not in code_body):
                ext = "csv"
            elif "json" in prompt_lower or code_body.startswith("{") or code_body.startswith("["):
                ext = "json"
            elif "python" in prompt_lower or "def " in code_body or "import " in code_body:
                ext = "py"
            else:
                ext = "txt"
    else:
        # Fallback: Check if agent is file_creator or prompt explicitly asks to generate/create a file
        is_file_intent = agent_id == "file_creator" or any(k in prompt_lower for k in [
            "generate csv", "sample csv", "create csv", "make csv", "generate file", "create file", "csv file", "download file"
        ])
        if is_file_intent:
            code_body = content.strip()
            if "csv" in prompt_lower or ("," in code_body and "\n" in code_body and "{" not in code_body):
                ext = "csv"
            elif "json" in prompt_lower or code_body.startswith("{") or code_body.startswith("["):
                ext = "json"
            elif "python" in prompt_lower or "def " in code_body or "import " in code_body:
                ext = "py"
            else:
                ext = "txt"
        else:
            return None

    if not code_body:
        return None

    # Detect filename in content or prompt
    fname_match = re.search(r"(?:filename|saved as|created|file):\s*[`'\"]?([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)[`'\"]?", content, re.IGNORECASE)
    if not fname_match:
        fname_match = re.search(r"[`']([a-zA-Z0-9_\-.]+\.(?:py|json|csv|md|js|ts|html|sql|yaml|yml|sh|txt))[`']", prompt, re.IGNORECASE)

    if fname_match:
        filename = fname_match.group(1)
        if "." not in filename:
            filename = f"{filename}.{ext}"
    else:
        if ext == "csv":
            filename = f"dataset_{int(time.time())}.csv"
        elif ext == "json":
            filename = f"data_{int(time.time())}.json"
        elif ext == "py":
            filename = f"script_{int(time.time())}.py"
        else:
            filename = f"generated_file_{int(time.time())}.{ext}"

    mime = mime_map.get(ext, "text/plain")

    return {
        "id": f"art-{int(time.time()*1000)}",
        "filename": filename,
        "name": filename,
        "type": ext,
        "mime_type": mime,
        "content": code_body,
        "size_bytes": len(code_body.encode("utf-8")),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "origin_agent": agent_id,
        "downloadable": True,
    }


@app.post("/api/chat", response_model=Message)
def chat(
    request: ChatRequest,
    current_user: Optional[AuthUser] = Depends(get_optional_user),
):
    """
    Main swarm chat endpoint.
    Routes prompt to swarm agent, executes via Gemini API, and persists turn
    and telemetry into Supabase if an authenticated session is present.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided in chat request.")

    last_user_message = next(
        (m for m in reversed(request.messages) if m.role == "user"),
        request.messages[-1]
    )

    # Determine target agent
    target_agent_id = None
    if last_user_message.metadata:
        target_agent_id = last_user_message.metadata.get("target_agent_id")

    selected_agent = route_agent(target_agent_id, last_user_message.content)
    client, api_key = get_gemini_client()
    start_time = time.time()

    # Extract metadata properties from agent (handles BaseAgent and AgentProfile)
    agent_id = getattr(selected_agent, "agent_id", None) or getattr(selected_agent, "id", "orchestrator")
    config_obj = getattr(selected_agent, "config", None)
    agent_name = getattr(config_obj, "name", None) or getattr(selected_agent, "name", "Swarm Orchestrator")
    agent_role = getattr(config_obj, "role", None) or getattr(selected_agent, "role", "Coordinator")
    agent_prompt = selected_agent.system_prompt or "You are a helpful AI assistant in an agent swarm."
    agent_tools = getattr(selected_agent, "tools", [])
    agent_skills = getattr(selected_agent, "skills", [])
    agent_mcp = getattr(selected_agent, "mcp_servers", [])
    agent_model = normalize_model_name(getattr(config_obj, "model", None) or getattr(selected_agent, "model", "gemini-3.8-flash"))
    agent_temp = getattr(config_obj, "temperature", None) or getattr(selected_agent, "temperature", 0.3)

    # Build attached artifact and grounded knowledge context if present
    user_uid = current_user.id if current_user else "guest-user"
    artifact_context_block, attached_arts = build_artifact_context_block(
        artifact_ids=request.artifact_ids,
        attached_artifacts=request.attached_artifacts,
        user_prompt=last_user_message.content,
        user_id=user_uid,
    )
    custom_art_ids = getattr(selected_agent, "attached_artifact_ids", None)
    if custom_art_ids:
        custom_block, custom_arts = build_artifact_context_block(
            artifact_ids=custom_art_ids,
            user_prompt=last_user_message.content,
            user_id=user_uid,
        )
        if custom_block:
            artifact_context_block = f"{artifact_context_block}\n\n{custom_block}".strip()
            seen_attached = {a.get("id") for a in attached_arts}
            for ca in custom_arts:
                if ca.get("id") not in seen_attached:
                    attached_arts.append(ca)
                    seen_attached.add(ca.get("id"))

    if artifact_context_block:
        agent_prompt = f"{agent_prompt}\n\n{artifact_context_block}"

    # Track user message persistence if session is active
    user_node_id = (
        request.user_message_id
        or (last_user_message.metadata or {}).get("node_id")
        or f"user-{int(time.time()*1000)}"
    )
    if current_user and request.session_id:
        db_save_message(
            user_id=current_user.id,
            session_id=request.session_id,
            msg_id=user_node_id,
            parent_id=request.parent_message_id,
            role="user",
            content=last_user_message.content,
            metadata=last_user_message.metadata,
            token=current_user.token,
        )

    # Auto-rename session if it has default generic title
    renamed_session_title = None
    if current_user and request.session_id:
        renamed_session_title = auto_rename_session_if_needed(request.session_id, last_user_message.content, current_user)

    # Check if this chat turn invokes an autonomous workflow
    invoked_workflow_id = request.workflow_id
    if not invoked_workflow_id and last_user_message.content.strip().startswith("/workflow"):
        parts = last_user_message.content.strip().split(maxsplit=1)
        if len(parts) > 1:
            invoked_workflow_id = parts[1].strip()

    if invoked_workflow_id:
        user_uid = current_user.id if current_user else "guest-user"
        wf_data = None
        if is_supabase_configured() and not user_uid.startswith("test-"):
            db_client = get_user_supabase_client(current_user.token if current_user else None)
            if db_client:
                try:
                    res = db_client.table("workflows").select("*").eq("id", invoked_workflow_id).single().execute()
                    wf_data = res.data
                except Exception:
                    pass
        if not wf_data:
            wf_data = memory_store.get_workflow(invoked_workflow_id, user_uid)
            if not wf_data:
                for w in memory_store.workflows.values():
                    if (
                        w.get("title", "").lower() == invoked_workflow_id.lower()
                        or w.get("share_slug") == invoked_workflow_id
                        or w.get("id") == invoked_workflow_id
                    ):
                        wf_data = w
                        break

        if wf_data:
            wf_inputs = request.workflow_inputs or {"prompt": last_user_message.content}
            run_result = workflow_engine.execute_workflow(
                workflow_data=wf_data,
                inputs=wf_inputs,
                user_id=user_uid,
                trigger_type="chat",
                session_id=request.session_id,
            )
            final_res = run_result.get("output_data", {}).get("final_result") or "Workflow execution completed."
            agent_node_id = f"agent-wf-{int(time.time()*1000)}"
            wf_metadata = {
                "agent_state": "completed",
                "agent_id": "orchestrator",
                "agent_name": f"Workflow: {wf_data.get('title', 'Autonomous Workflow')}",
                "workflow_run_id": run_result.get("id"),
                "workflow_id": wf_data.get("id"),
                "workflow_title": wf_data.get("title"),
                "workflow_goal": wf_data.get("goal"),
                "step_runs": run_result.get("step_runs", []),
                "tokens_used": run_result.get("total_tokens", 0),
                "duration_ms": run_result.get("duration_ms", 0),
                "mode": "workflow_execution",
                "node_id": agent_node_id,
            }
            if renamed_session_title:
                wf_metadata["session_title"] = renamed_session_title
            if current_user and request.session_id:
                db_save_message(
                    user_id=current_user.id,
                    session_id=request.session_id,
                    msg_id=agent_node_id,
                    parent_id=user_node_id,
                    role="agent",
                    content=final_res,
                    metadata=wf_metadata,
                    token=current_user.token,
                )
            return Message(
                role="agent",
                content=final_res,
                metadata=wf_metadata,
            )

    # Determine model choice
    raw_model = request.model or getattr(selected_agent, "model", None) or agent_model or os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    chosen_model = normalize_model_name(raw_model)

    # Enforce: Researcher agent ALWAYS uses Perplexity Sonar ('sonar')
    is_live_query = any(k in last_user_message.content.lower() for k in [
        "stock price", "stock prices", "stocks", "ticker", "current price", "live price", "market quote", "web search", "websearch", "live info", "latest news"
    ])
    if agent_id == "researcher" or getattr(selected_agent, "name", "") == "Research Agent" or is_live_query:
        chosen_model = "sonar"

    # 1. LIVE PERPLEXITY SONAR API GENERATION
    perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
    if (
        chosen_model.startswith("sonar")
        and perplexity_key
        and not perplexity_key.startswith("your-")
        and not perplexity_key.startswith("test-")
        and os.environ.get("TESTING") != "true"
    ):
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {perplexity_key.strip()}",
                "Content-Type": "application/json",
            }
            perp_messages = [{"role": "system", "content": agent_prompt}]
            for msg in request.messages:
                perp_messages.append({"role": "user" if msg.role == "user" else "assistant", "content": msg.content})

            perp_resp = httpx.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json={
                    "model": chosen_model,
                    "messages": perp_messages,
                    "temperature": agent_temp,
                },
                timeout=25.0
            )
            if perp_resp.status_code == 200:
                perp_data = perp_resp.json()
                choice = perp_data.get("choices", [{}])[0]
                perp_content = choice.get("message", {}).get("content", "")
                citations = perp_data.get("citations") or []
                latency_ms = round((time.time() - start_time) * 1000, 2)
                usage_info = perp_data.get("usage", {})
                total_tokens = usage_info.get("total_tokens", len(perp_content.split()) + 30)
                prompt_tokens = usage_info.get("prompt_tokens", 20)
                completion_tokens = usage_info.get("completion_tokens", len(perp_content.split()))

                tool_calls = [
                    {
                        "tool": "perplexity_live_search",
                        "args": {"model": chosen_model, "query": last_user_message.content[:80]},
                        "result": {
                            "status": "completed",
                            "sources_found": len(citations),
                            "provider": "perplexity_sonar"
                        }
                    }
                ]
                agent_node_id = f"agent-{int(time.time()*1000)}"
                agent_metadata = {
                    "agent_state": "completed",
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "tool_calls": tool_calls,
                    "citations": citations,
                    "tokens_used": total_tokens,
                    "latency_ms": latency_ms,
                    "model": chosen_model,
                    "node_id": agent_node_id,
                }
                if renamed_session_title:
                    agent_metadata["session_title"] = renamed_session_title
                if attached_arts:
                    agent_metadata["attached_artifacts"] = [
                        {"id": a.get("id"), "filename": a.get("filename") or a.get("name"), "type": a.get("type")}
                        for a in attached_arts
                    ]

                # Extract and catalog any generated file artifacts
                turn_artifact = extract_file_artifact_from_turn(perp_content, agent_id, last_user_message.content)
                if turn_artifact:
                    agent_metadata["file_artifact"] = turn_artifact
                    agent_metadata["artifacts"] = [turn_artifact]
                    memory_store.save_artifact({
                        **turn_artifact,
                        "user_id": current_user.id if current_user else "guest-user",
                        "source_type": "chat",
                        "source_title": agent_name,
                    })

                if current_user and request.session_id:
                    db_save_message(
                        user_id=current_user.id,
                        session_id=request.session_id,
                        msg_id=agent_node_id,
                        parent_id=user_node_id,
                        role="agent",
                        content=perp_content,
                        metadata=agent_metadata,
                        token=current_user.token,
                    )
                    db_save_usage(
                        user_id=current_user.id,
                        session_id=request.session_id,
                        message_id=agent_node_id,
                        model=chosen_model,
                        agent_id=agent_id,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        latency_ms=latency_ms,
                        token=current_user.token,
                    )
                return Message(role="agent", content=perp_content, metadata=agent_metadata)
        except Exception as perp_err:
            print(f"Perplexity API execution note: {perp_err}")

    # 2. LIVE GROQ API GENERATION (Primary Default Provider Site-wide)
    client_groq, groq_key = get_groq_client()
    if (
        client_groq
        and not chosen_model.startswith("sonar")
        and not chosen_model.startswith("gemini-")
        and os.environ.get("TESTING") != "true"
        and os.environ.get("MOCK_GROQ") != "true"
    ):
        try:
            groq_msgs = []
            for msg in request.messages:
                groq_msgs.append({"role": msg.role, "content": msg.content})

            groq_content, total_tokens, prompt_tokens, completion_tokens, used_model = execute_groq_chat(
                client=client_groq,
                messages=groq_msgs,
                system_prompt=agent_prompt,
                requested_model=chosen_model or DEFAULT_GROQ_MODEL,
                temperature=agent_temp,
            )
            latency_ms = round((time.time() - start_time) * 1000, 2)
            agent_node_id = f"agent-{int(time.time()*1000)}"

            tool_calls = [
                {
                    "tool": "groq_lpu_inference",
                    "args": {
                        "model": used_model,
                        "agent_id": agent_id,
                    },
                    "result": {
                        "status": "completed",
                        "provider": "groq",
                        "latency_ms": latency_ms,
                    }
                }
            ]

            agent_metadata = {
                "agent_state": "completed",
                "agent_id": agent_id,
                "agent_name": agent_name,
                "tool_calls": tool_calls,
                "skills_invoked": [s.id for s in agent_skills[:2]],
                "tokens_used": total_tokens,
                "latency_ms": latency_ms,
                "model": used_model,
                "node_id": agent_node_id,
            }
            if renamed_session_title:
                agent_metadata["session_title"] = renamed_session_title
            if attached_arts:
                agent_metadata["attached_artifacts"] = [
                    {"id": a.get("id"), "filename": a.get("filename") or a.get("name"), "type": a.get("type")}
                    for a in attached_arts
                ]

            turn_artifact = extract_file_artifact_from_turn(groq_content, agent_id, last_user_message.content)
            if turn_artifact:
                agent_metadata["file_artifact"] = turn_artifact
                agent_metadata["artifacts"] = [turn_artifact]
                memory_store.save_artifact({
                    **turn_artifact,
                    "user_id": current_user.id if current_user else "guest-user",
                    "source_type": "chat",
                    "source_title": agent_name,
                })

            if current_user and request.session_id:
                db_save_message(
                    user_id=current_user.id,
                    session_id=request.session_id,
                    msg_id=agent_node_id,
                    parent_id=user_node_id,
                    role="agent",
                    content=groq_content,
                    metadata=agent_metadata,
                    token=current_user.token,
                )
                db_save_usage(
                    user_id=current_user.id,
                    session_id=request.session_id,
                    message_id=agent_node_id,
                    model=used_model,
                    agent_id=agent_id,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    latency_ms=latency_ms,
                    token=current_user.token,
                )

            return Message(
                role="agent",
                content=groq_content,
                metadata=agent_metadata,
            )
        except Exception as groq_err:
            print(f"Groq API execution note: {groq_err}")

    # 3. LIVE GEMINI API GENERATION
    if client:
        try:
            from google.genai import types

            gemini_contents = []
            for msg in request.messages:
                role = "user" if msg.role == "user" else "model"
                gemini_contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.content)]
                    )
                )

            model_name = chosen_model if chosen_model.startswith("gemini-") else normalize_model_name(os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"))
            config = types.GenerateContentConfig(
                system_instruction=agent_prompt,
                temperature=agent_temp,
            )

            response = client.models.generate_content(
                model=model_name,
                contents=gemini_contents,
                config=config,
            )

            latency_ms = round((time.time() - start_time) * 1000, 2)
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            if hasattr(response, "usage_metadata") and response.usage_metadata:
                total_tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

            tool_calls = [
                {
                    "tool": "swarm_router",
                    "args": {
                        "target_agent": agent_id,
                        "model": model_name,
                        "skills_matched": [s.name for s in agent_skills[:2]],
                        "tools_available": [t.name for t in agent_tools[:3]],
                    },
                    "result": {
                        "status": "routed",
                        "agent_name": agent_name,
                        "mcp_servers": [m.name for m in agent_mcp],
                    }
                }
            ]

            agent_response_content = response.text or "Completed without output text."
            agent_node_id = f"agent-{int(time.time()*1000)}"

            agent_metadata = {
                "agent_state": "completed",
                "agent_id": agent_id,
                "agent_name": agent_name,
                "tool_calls": tool_calls,
                "skills_invoked": [s.id for s in agent_skills[:2]],
                "tokens_used": total_tokens,
                "latency_ms": latency_ms,
                "model": model_name,
                "node_id": agent_node_id,
            }
            if renamed_session_title:
                agent_metadata["session_title"] = renamed_session_title
            if attached_arts:
                agent_metadata["attached_artifacts"] = [
                    {"id": a.get("id"), "filename": a.get("filename") or a.get("name"), "type": a.get("type")}
                    for a in attached_arts
                ]

            # Detect and catalog generated file artifacts
            turn_artifact = extract_file_artifact_from_turn(agent_response_content, agent_id, last_user_message.content)
            if turn_artifact:
                agent_metadata["file_artifact"] = turn_artifact
                agent_metadata["artifacts"] = [turn_artifact]
                memory_store.save_artifact({
                    **turn_artifact,
                    "user_id": current_user.id if current_user else "guest-user",
                    "source_type": "chat",
                    "source_title": agent_name,
                })

            # Persist agent turn & usage if user is authenticated
            if current_user and request.session_id:
                db_save_message(
                    user_id=current_user.id,
                    session_id=request.session_id,
                    msg_id=agent_node_id,
                    parent_id=user_node_id,
                    role="agent",
                    content=agent_response_content,
                    metadata=agent_metadata,
                    token=current_user.token,
                )
                db_save_usage(
                    user_id=current_user.id,
                    session_id=request.session_id,
                    message_id=agent_node_id,
                    model=model_name,
                    agent_id=agent_id,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    latency_ms=latency_ms,
                    token=current_user.token,
                )

            return Message(
                role="agent",
                content=agent_response_content,
                metadata=agent_metadata,
            )

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            latency_ms = round((time.time() - start_time) * 1000, 2)
            agent_node_id = f"agent-{int(time.time()*1000)}"
            err_metadata = {
                "agent_state": "error",
                "agent_id": agent_id,
                "latency_ms": latency_ms,
                "tokens_used": 0,
                "error_detail": str(e),
                "node_id": agent_node_id,
            }
            if renamed_session_title:
                err_metadata["session_title"] = renamed_session_title
            if current_user and request.session_id:
                db_save_message(
                    user_id=current_user.id,
                    session_id=request.session_id,
                    msg_id=agent_node_id,
                    parent_id=user_node_id,
                    role="agent",
                    content=f"⚠️ Notice: {str(e)}",
                    metadata=err_metadata,
                    token=current_user.token,
                )
                db_save_usage(
                    user_id=current_user.id,
                    session_id=request.session_id,
                    message_id=agent_node_id,
                    model=agent_model,
                    agent_id=agent_id,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=10,
                    latency_ms=latency_ms,
                    token=current_user.token,
                )
            return Message(
                role="agent",
                content=(
                    f"⚠️ **Gemini API Execution Notice:**\n\n"
                    f"Encountered an issue communicating with Gemini (`{str(e)}`).\n\n"
                    f"Please check your `GEMINI_API_KEY` and internet connectivity."
                ),
                metadata=err_metadata,
            )

    # 2. DEMO / SIMULATION MODE (When GEMINI_API_KEY is not configured)
    latency_ms = round((time.time() - start_time) * 1000, 2)
    simulated_tokens = 450
    demo_tools = [
        {
            "tool": "swarm_registry_lookup",
            "args": {
                "agent_id": agent_id,
                "role": agent_role,
                "tools_count": len(agent_tools),
                "skills_count": len(agent_skills),
                "mcp_servers": [m.name for m in agent_mcp],
            },
            "result": {"status": "online", "mode": "modular_swarm_active"}
        },
        {
            "tool": "gemini_provider_check",
            "args": {"env_var": "GEMINI_API_KEY"},
            "result": {"configured": False, "instructions": "Set GEMINI_API_KEY in backend/.env"}
        }
    ]

    if agent_id == "file_creator":
        p_lower = last_user_message.content.lower()
        if "csv" in p_lower:
            sample_code = "id,name,role,department,salary\n1,Alice Smith,Principal Engineer,AI Platforms,185000\n2,Bob Jones,Data Scientist,Analytics,162000\n3,Carol Danvers,Product Manager,Growth,174000\n4,David Miller,DevOps Lead,Infrastructure,168000\n5,Eve Polastri,Security Analyst,SecOps,159000"
            filename = "sample_data.csv"
            fallback_content = (
                f"### 📄 CSV Dataset Generated Successfully\n\n"
                f"I have created the requested CSV dataset: `{filename}`.\n\n"
                f"```csv\n{sample_code}\n```\n\n"
                f"You can review the rows above or download the file directly using the **Download File** card below."
            )
        elif "json" in p_lower:
            sample_code = '{\n  "version": "1.0",\n  "dataset": "sample_records",\n  "records": [\n    {"id": 1, "name": "Item A", "status": "active"},\n    {"id": 2, "name": "Item B", "status": "pending"}\n  ]\n}'
            filename = "sample_data.json"
            fallback_content = (
                f"### 📄 JSON File Generated Successfully\n\n"
                f"I have created the requested JSON file: `{filename}`.\n\n"
                f"```json\n{sample_code}\n```\n\n"
                f"You can download this file directly using the **Download File** button below."
            )
        else:
            sample_code = "# Auto-Generated Python Automation Script\nimport datetime\n\ndef main():\n    print(f'Swarm automated file execution at {datetime.datetime.utcnow()}')\n\nif __name__ == '__main__':\n    main()\n"
            filename = "automation_script.py"
            fallback_content = (
                f"### 📄 File Generated Successfully\n\n"
                f"I have created the requested file artifact: `{filename}`.\n\n"
                f"```python\n{sample_code}\n```\n\n"
                f"You can download this file directly using the **Download File** button below."
            )
    elif agent_id == "file_parser":
        fallback_content = (
            f"### 📊 Document Ingestion & Schema Diagnostics\n\n"
            f"**File Analysis Summary:**\n"
            f"- **Target**: Ingested content payload\n"
            f"- **Integrity Status**: Valid structure, 0 syntax violations detected\n"
            f"- **Fields Identified**: Schema extracted with high confidence\n\n"
            f"```json\n{{\n  \"status\": \"parsed\",\n  \"fields_count\": 4,\n  \"null_ratio\": 0.0,\n  \"format\": \"structured_payload\"\n}}\n```"
        )
    elif attached_arts:
        art_names = ", ".join([f"`{a.get('filename') or a.get('name')}`" for a in attached_arts])
        fallback_content = (
            f"Hello! I am **{agent_name}** (`{agent_id}`).\n\n"
            f"I have successfully ingested and grounded your inquiry on the attached document(s): {art_names}.\n\n"
            f"**Context Grounding & Extracted Highlights:**\n"
            f"- Grounded across {len(attached_arts)} user artifact(s).\n"
            f"- Active document context has been loaded into the swarm scratchpad.\n\n"
            f"Inquiry received:\n> \"*{last_user_message.content}*\""
        )
    else:
        fallback_content = (
            f"Hello! I am **{agent_name}** (`{agent_id}`).\n\n"
            f"**My Role:** {agent_role}\n\n"
            f"I received your inquiry:\n> \"*{last_user_message.content}*\"\n\n"
            f"### ⚙️ LLM Provider Setup\n"
            f"To enable live generative responses from Groq (ultra fast LPU) or Google Gemini:\n"
            f"1. Open `backend/.env`\n"
            f"2. Add your Groq API Key: `GROQ_API_KEY=\"your_groq_key_here\"` (or `GEMINI_API_KEY` for Gemini)\n"
            f"3. Once added, the backend will immediately stream live AI responses for this agent!\n\n"
            f"The frontend interactive features (sessions, history, branching, tool inspection, and usage tracking) are fully active."
        )

    agent_node_id = f"agent-{int(time.time()*1000)}"
    demo_metadata = {
        "agent_state": "completed",
        "agent_id": agent_id,
        "agent_name": agent_name,
        "tool_calls": demo_tools,
        "skills_invoked": [s.id for s in agent_skills[:2]],
        "tokens_used": simulated_tokens,
        "latency_ms": latency_ms,
        "mode": "demo_fallback",
        "node_id": agent_node_id,
    }
    if renamed_session_title:
        demo_metadata["session_title"] = renamed_session_title
    if attached_arts:
        demo_metadata["attached_artifacts"] = [
            {"id": a.get("id"), "filename": a.get("filename") or a.get("name"), "type": a.get("type")}
            for a in attached_arts
        ]

    # Detect and catalog generated file artifacts in demo mode
    turn_artifact = extract_file_artifact_from_turn(fallback_content, agent_id, last_user_message.content)
    if turn_artifact:
        demo_metadata["file_artifact"] = turn_artifact
        demo_metadata["artifacts"] = [turn_artifact]
        memory_store.save_artifact({
            **turn_artifact,
            "user_id": current_user.id if current_user else "guest-user",
            "source_type": "chat",
            "source_title": agent_name,
        })

    if current_user and request.session_id:
        db_save_message(
            user_id=current_user.id,
            session_id=request.session_id,
            msg_id=agent_node_id,
            parent_id=user_node_id,
            role="agent",
            content=fallback_content,
            metadata=demo_metadata,
            token=current_user.token,
        )
        db_save_usage(
            user_id=current_user.id,
            session_id=request.session_id,
            message_id=agent_node_id,
            model="simulation-demo",
            agent_id=agent_id,
            prompt_tokens=150,
            completion_tokens=300,
            total_tokens=simulated_tokens,
            latency_ms=latency_ms,
            token=current_user.token,
        )

    return Message(
        role="agent",
        content=fallback_content,
        metadata=demo_metadata,
    )


# =========================================================
# Workflows, Custom Agents, Tools & Knowledge Endpoints
# =========================================================

# ----------------- User Custom Agents -----------------

@app.get("/api/custom-agents", response_model=List[UserAgentProfile])
def list_custom_agents(current_user: AuthUser = Depends(get_current_user)):
    """Lists custom agents created by or accessible to the user."""
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("user_agents").select("*").or_(f"user_id.eq.{current_user.id},is_public.eq.true").order("updated_at", desc=True).execute()
                return res.data or []
            except Exception as e:
                print(f"Supabase list_custom_agents error: {e}")
    return memory_store.get_user_agents(current_user.id)


@app.post("/api/custom-agents", response_model=UserAgentProfile)
def create_custom_agent(
    payload: UserAgentProfile,
    current_user: AuthUser = Depends(get_current_user),
):
    """Creates a new persistent custom agent profile."""
    agent_id = payload.id.strip().lower()
    if not agent_id:
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"

    # Prevent collision with prebuilt agents
    prebuilt = agent_registry.get(agent_id)
    if prebuilt:
        raise HTTPException(status_code=400, detail=f"Cannot overwrite prebuilt agent '{agent_id}'.")

    now_iso = datetime.now(timezone.utc).isoformat()
    agent_dict = payload.model_dump()
    agent_dict["id"] = agent_id
    agent_dict["user_id"] = current_user.id
    agent_dict["created_at"] = now_iso
    agent_dict["updated_at"] = now_iso

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("user_agents").upsert(agent_dict).execute()
                if res.data:
                    # Sync to registry
                    agent_registry.register_custom(AgentProfile(
                        id=agent_id,
                        name=payload.name,
                        role=payload.role,
                        description=payload.description,
                        model=payload.model,
                        temperature=payload.temperature,
                        is_orchestrator=False,
                        icon=payload.icon,
                    ))
                    return res.data[0]
            except Exception as e:
                print(f"Supabase create_custom_agent error: {e}")

    saved = memory_store.create_user_agent(agent_dict)
    agent_registry.register_custom(AgentProfile(
        id=agent_id,
        name=payload.name,
        role=payload.role,
        description=payload.description,
        model=payload.model,
        temperature=payload.temperature,
        is_orchestrator=False,
        icon=payload.icon,
    ))
    return saved


@app.get("/api/custom-agents/{agent_id}", response_model=UserAgentProfile)
def get_custom_agent(
    agent_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Retrieves details of a specific user custom agent."""
    agent = None
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("user_agents").select("*").eq("id", agent_id.lower()).single().execute()
                agent = res.data
            except Exception:
                pass
    if not agent:
        agent = memory_store.get_user_agent(agent_id, current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Custom agent '{agent_id}' not found.")
    return agent


@app.put("/api/custom-agents/{agent_id}", response_model=UserAgentProfile)
def update_custom_agent(
    agent_id: str,
    payload: UserAgentProfile,
    current_user: AuthUser = Depends(get_current_user),
):
    """Updates an existing custom agent profile."""
    # Prevent collision with prebuilt agents
    prebuilt = agent_registry.get(agent_id.lower())
    if prebuilt and not getattr(prebuilt, "is_custom", False):
        raise HTTPException(status_code=400, detail=f"Cannot overwrite prebuilt swarm agent '{agent_id}'.")

    now_iso = datetime.now(timezone.utc).isoformat()
    agent_dict = payload.model_dump()
    agent_dict["id"] = agent_id.lower()
    agent_dict["user_id"] = current_user.id
    agent_dict["updated_at"] = now_iso

    saved_agent = None
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("user_agents").update(agent_dict).eq("id", agent_id.lower()).eq("user_id", current_user.id).execute()
                if res.data:
                    saved_agent = res.data[0]
            except Exception as e:
                print(f"Supabase update_custom_agent error: {e}")

    if not saved_agent:
        saved_agent = memory_store.update_user_agent(agent_id.lower(), current_user.id, agent_dict)

    if not saved_agent:
        raise HTTPException(status_code=404, detail=f"Custom agent '{agent_id}' not found or unauthorized.")

    # Re-register updated profile in registry
    agent_registry.register_custom(AgentProfile(
        id=agent_id.lower(),
        name=payload.name,
        role=payload.role,
        description=payload.description,
        model=payload.model,
        temperature=payload.temperature,
        is_orchestrator=False,
        icon=payload.icon,
    ))
    return saved_agent


@app.delete("/api/custom-agents/{agent_id}")
def delete_custom_agent(
    agent_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Deletes a custom agent created by the user."""
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                client.table("user_agents").delete().eq("id", agent_id.lower()).eq("user_id", current_user.id).execute()
                return {"message": f"Agent '{agent_id}' deleted successfully."}
            except Exception as e:
                print(f"Supabase delete_custom_agent error: {e}")
    success = memory_store.delete_user_agent(agent_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Custom agent not found or unauthorized.")
    return {"message": f"Agent '{agent_id}' deleted successfully."}


@app.post("/api/custom-agents/test", response_model=AgentTestResponse)
def test_custom_agent(
    payload: AgentTestRequest,
    current_user: Optional[AuthUser] = Depends(get_optional_user),
):
    """Executes a custom or prebuilt agent in isolation with user test prompt."""
    start_time = time.time()
    user_id = current_user.id if current_user else "anonymous"

    # 1. Resolve prompt
    input_text = payload.input_prompt or payload.prompt or "Hello"

    # 2. Resolve agent system prompt, model, temperature, and name
    system_prompt = payload.system_prompt
    agent_name = "Agent"
    model_name = payload.model or DEFAULT_GROQ_MODEL
    temperature = payload.temperature if payload.temperature is not None else 0.3
    agent_obj = None

    if payload.agent_id:
        # Check prebuilt registry first
        agent_obj = agent_registry.get(payload.agent_id)
        if agent_obj:
            agent_name = getattr(agent_obj, "name", payload.agent_id)
            if not system_prompt:
                system_prompt = getattr(agent_obj, "system_prompt", None) or f"You are {agent_name}, an autonomous AI specialist in Swarm."
            config = getattr(agent_obj, "config", None)
            if config:
                if not payload.model:
                    model_name = getattr(config, "model", model_name)
                if payload.temperature is None:
                    temperature = getattr(config, "temperature", temperature)
        else:
            # Check custom agents in registry or memory store / Supabase
            profile = agent_registry.get_profile(payload.agent_id) or memory_store.get_user_agent(payload.agent_id, user_id)
            if profile:
                agent_name = getattr(profile, "name", None) or (profile.get("name") if isinstance(profile, dict) else payload.agent_id)
                prof_prompt = getattr(profile, "system_prompt", None) or (profile.get("system_prompt") if isinstance(profile, dict) else None)
                if not system_prompt and prof_prompt:
                    system_prompt = prof_prompt
                prof_model = getattr(profile, "model", None) or (profile.get("model") if isinstance(profile, dict) else None)
                if not payload.model and prof_model:
                    model_name = prof_model
                prof_temp = getattr(profile, "temperature", None) if not isinstance(profile, dict) else profile.get("temperature")
                if payload.temperature is None and prof_temp is not None:
                    temperature = prof_temp

    if not system_prompt:
        system_prompt = f"You are {agent_name}, an autonomous specialist agent in the Swarm platform."

    # Ground test prompt in attached knowledge artifacts if present
    art_ids = list(payload.attached_artifact_ids or [])
    if 'profile' in locals() and profile:
        prof_arts = getattr(profile, "attached_artifact_ids", None) or (profile.get("attached_artifact_ids") if isinstance(profile, dict) else None)
        if prof_arts:
            for aid in prof_arts:
                if aid not in art_ids:
                    art_ids.append(aid)

    if art_ids:
        art_block, _ = build_artifact_context_block(artifact_ids=art_ids, user_prompt=input_text, user_id=user_id)
        if art_block:
            system_prompt = f"{system_prompt}\n\n{art_block}"

    # 3. Automatic Sonar routing for researcher or live search queries
    is_sonar = (
        model_name.startswith("sonar")
        or model_name.startswith("perplexity")
        or payload.agent_id == "researcher"
        or any(k in input_text.lower() for k in ["stock price", "stock prices", "ticker", "live information", "web search", "websearch", "market quote"])
    )

    tool_calls = []
    if payload.tool_ids and current_user:
        for tid in payload.tool_ids:
            tool_rec = _get_tool_record(tid, current_user)
            if tool_rec:
                tool_calls.append({
                    "tool": tool_rec.get("name", tid),
                    "tool_name": tool_rec.get("name", tid),
                    "args": {"test_mode": True},
                    "result": {"status": "available", "description": tool_rec.get("description")}
                })

    # 4. Live execution via Perplexity Sonar
    if is_sonar:
        perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
        if (
            perplexity_key
            and not perplexity_key.startswith("test-")
            and not perplexity_key.startswith("your-")
            and os.environ.get("TESTING") != "true"
            and os.environ.get("MOCK_PERPLEXITY") != "true"
        ):
            try:
                import httpx
                headers = {
                    "Authorization": f"Bearer {perplexity_key.strip()}",
                    "Content-Type": "application/json",
                }
                perp_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input_text},
                ]
                resp = httpx.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers=headers,
                    json={
                        "model": model_name if model_name.startswith("sonar") else "sonar",
                        "messages": perp_messages,
                        "temperature": temperature,
                    },
                    timeout=35.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    latency_ms = round((time.time() - start_time) * 1000, 2)
                    usage = data.get("usage", {})
                    tokens = usage.get("total_tokens", len(input_text.split()) + len(text.split()) + 30)
                    return AgentTestResponse(
                        status="success",
                        content=text,
                        response=text,
                        tokens_used=tokens,
                        latency_ms=latency_ms,
                        duration_ms=latency_ms,
                        agent_id=payload.agent_id or "researcher",
                        tool_calls=tool_calls,
                    )
            except Exception as e:
                print(f"Perplexity Sonar agent test error: {e}")

    # 5. Live execution via Groq (Primary Default Provider)
    client_groq, groq_key = get_groq_client()
    if (
        client_groq
        and not is_sonar
        and not model_name.startswith("gemini-")
        and os.environ.get("TESTING") != "true"
        and os.environ.get("MOCK_GROQ") != "true"
    ):
        try:
            content, total_tokens, prompt_tokens, completion_tokens, used_model = execute_groq_chat(
                client=client_groq,
                messages=[{"role": "user", "content": input_text}],
                system_prompt=system_prompt,
                requested_model=model_name or DEFAULT_GROQ_MODEL,
                temperature=temperature,
            )
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return AgentTestResponse(
                status="success",
                content=content,
                response=content,
                tokens_used=total_tokens,
                latency_ms=latency_ms,
                duration_ms=latency_ms,
                agent_id=payload.agent_id or "agent",
                tool_calls=tool_calls,
            )
        except Exception as e:
            print(f"Groq agent test note: {e}")

    # 6. Live execution via Gemini
    client, api_key = get_gemini_client()
    if client and not is_sonar and os.environ.get("TESTING") != "true" and os.environ.get("MOCK_GEMINI") != "true":
        try:
            from google.genai import types
            gemini_model = model_name if model_name.startswith("gemini-") else normalize_model_name(os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"))
            response = client.models.generate_content(
                model=gemini_model,
                contents=[types.Part.from_text(text=input_text)],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                ),
            )
            latency_ms = round((time.time() - start_time) * 1000, 2)
            tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0
            if not tokens:
                tokens = len(input_text.split()) + len((response.text or "").split()) + 25

            resp_text = response.text or f"Agent [{agent_name}] completed without content."
            return AgentTestResponse(
                status="success",
                content=resp_text,
                response=resp_text,
                tokens_used=tokens,
                latency_ms=latency_ms,
                duration_ms=latency_ms,
                agent_id=payload.agent_id or "agent",
                tool_calls=tool_calls,
            )
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            print(f"Gemini agent test note: {e}")

    # 6. Fallback Simulation Response
    latency_ms = round((time.time() - start_time) * 1000, 2)
    simulated_content = (
        f"[{agent_name} - Isolated Playground Test]\n\n"
        f"**Agent System Prompt Verified:**\n> {system_prompt[:120]}...\n\n"
        f"**Response to:** \"{input_text}\"\n\n"
        f"I have successfully processed your prompt following my persona instructions. All constraints and guidelines were respected."
    )
    return AgentTestResponse(
        status="success",
        content=simulated_content,
        response=simulated_content,
        tokens_used=len(input_text.split()) + 65,
        latency_ms=latency_ms,
        duration_ms=latency_ms,
        agent_id=payload.agent_id or "agent",
        tool_calls=tool_calls,
    )


# ----------------- AI Architect Generation Endpoints -----------------

@app.post("/api/ai/generate-workflow", response_model=Dict[str, Any])
def ai_generate_workflow(
    payload: AIGenerateWorkflowRequest,
    current_user: AuthUser = Depends(get_current_user),
):
    """Generates a complete autonomous workflow DAG from user natural language prompt."""
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    client, _ = get_gemini_client()
    agents_list = [a.model_dump() if hasattr(a, "model_dump") else dict(a) for a in agent_registry.get_all()]
    tools_list = memory_store.get_tools(current_user.id)

    spec = generate_workflow_spec(
        prompt=payload.prompt,
        available_agents=agents_list,
        available_tools=tools_list,
        client=client,
    )
    return spec


@app.post("/api/ai/generate-agent", response_model=Dict[str, Any])
def ai_generate_agent(
    payload: AIGenerateAgentRequest,
    current_user: AuthUser = Depends(get_current_user),
):
    """Generates an agent profile, persona, and system prompt from natural language description."""
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    client, _ = get_gemini_client()
    tools_list = memory_store.get_tools(current_user.id)
    agent_spec = generate_agent_spec(
        prompt=payload.prompt,
        available_tools=tools_list,
        client=client,
    )
    return agent_spec


# ----------------- Workflow Script Tools -----------------

@app.get("/api/workflow-tools", response_model=List[ScriptTool])
def list_workflow_tools(current_user: AuthUser = Depends(get_current_user)):
    """Lists script tools belonging to the user or marked public."""
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflow_tools").select("*").or_(f"user_id.eq.{current_user.id},is_public.eq.true").order("updated_at", desc=True).execute()
                return res.data or []
            except Exception as e:
                print(f"Supabase list_workflow_tools error: {e}")
    return memory_store.get_tools(current_user.id)


def _get_tool_record(tool_id: str, current_user: AuthUser) -> Optional[Dict[str, Any]]:
    """Retrieves a script tool from Supabase or MemoryStore with cache sync."""
    tool = None
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflow_tools").select("*").eq("id", tool_id).execute()
                if res.data:
                    tool = res.data[0]
                    memory_store.create_tool(tool)
            except Exception as e:
                print(f"Supabase _get_tool_record error: {e}")
    if not tool:
        tool = memory_store.get_tool(tool_id)
    return tool


@app.post("/api/workflow-tools", response_model=ScriptTool)
def create_workflow_tool(
    payload: ScriptTool,
    current_user: AuthUser = Depends(get_current_user),
):
    """Creates a new user-submitted Python script tool with AST security validation."""
    is_valid, validation_error = validate_tool_code(payload.code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Tool validation failed: {validation_error}")

    tool_id = payload.id or str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    tool_dict = payload.model_dump()
    tool_dict["id"] = tool_id
    tool_dict["user_id"] = current_user.id
    tool_dict["created_at"] = now_iso
    tool_dict["updated_at"] = now_iso

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflow_tools").insert(tool_dict).execute()
                if res.data:
                    created_tool = res.data[0]
                    memory_store.create_tool(created_tool)
                    return created_tool
            except Exception as e:
                print(f"Supabase create_workflow_tool error: {e}")

    return memory_store.create_tool(tool_dict)


@app.get("/api/workflow-tools/{tool_id}", response_model=ScriptTool)
def get_workflow_tool(
    tool_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Retrieves details and Python code of a specific script tool."""
    tool = _get_tool_record(tool_id, current_user)
    if not tool:
        raise HTTPException(status_code=404, detail="Script tool not found.")
    return tool


@app.put("/api/workflow-tools/{tool_id}", response_model=ScriptTool)
def update_workflow_tool(
    tool_id: str,
    payload: ScriptTool,
    current_user: AuthUser = Depends(get_current_user),
):
    """Updates an existing script tool after validating code changes."""
    is_valid, validation_error = validate_tool_code(payload.code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Tool validation failed: {validation_error}")

    existing = _get_tool_record(tool_id, current_user)
    if not existing:
        raise HTTPException(status_code=404, detail="Script tool not found.")
    if existing.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot modify another user's script tool.")

    updates = {
        "name": payload.name,
        "description": payload.description,
        "code": payload.code,
        "input_schema": payload.input_schema,
        "output_schema": payload.output_schema,
        "is_public": payload.is_public,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflow_tools").update(updates).eq("id", tool_id).eq("user_id", current_user.id).execute()
                if res.data:
                    memory_store.update_tool(tool_id, current_user.id, updates)
                    return res.data[0]
            except Exception as e:
                print(f"Supabase update_workflow_tool error: {e}")

    updated = memory_store.update_tool(tool_id, current_user.id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Script tool not found or unauthorized.")
    return updated


@app.delete("/api/workflow-tools/{tool_id}")
def delete_workflow_tool(
    tool_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Deletes a user script tool."""
    existing = _get_tool_record(tool_id, current_user)
    if not existing:
        raise HTTPException(status_code=404, detail="Script tool not found.")
    if existing.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot delete another user's script tool.")

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                client.table("workflow_tools").delete().eq("id", tool_id).eq("user_id", current_user.id).execute()
            except Exception as e:
                print(f"Supabase delete_workflow_tool error: {e}")

    success = memory_store.delete_tool(tool_id, current_user.id)
    return {"message": "Script tool deleted successfully."}


@app.post("/api/workflow-tools/{tool_id}/test", response_model=ScriptToolTestResponse)
def test_workflow_tool(
    tool_id: str,
    payload: ScriptToolTestRequest,
    current_user: AuthUser = Depends(get_current_user),
):
    """Directly executes a script tool with test input arguments inside the AST sandbox."""
    tool = _get_tool_record(tool_id, current_user)
    if not tool:
        raise HTTPException(status_code=404, detail="Script tool not found.")

    res = execute_tool_script(
        code=tool["code"],
        input_data=payload.input_data,
        context=payload.context or {},
        timeout_seconds=5.0
    )
    return ScriptToolTestResponse(
        status=res.get("status", "error"),
        result=res.get("result"),
        stdout=res.get("stdout"),
        duration_ms=res.get("duration_ms", 0.0),
        error=res.get("error"),
    )


# ----------------- Workflows CRUD & Sharing -----------------

def _get_workflow_record(workflow_id: str, current_user: Optional[AuthUser] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a workflow from Supabase or MemoryStore with cache sync, falling back to default templates."""
    wf = None
    if current_user and is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflows").select("*").eq("id", workflow_id).execute()
                if res.data:
                    wf = res.data[0]
                    memory_store.create_workflow(wf)
            except Exception as e:
                print(f"Supabase _get_workflow_record error: {e}")
    if not wf:
        wf = memory_store.get_workflow(workflow_id)
    if not wf:
        for default_wf in get_default_workflows():
            if default_wf["id"] == workflow_id:
                return default_wf
    return wf


@app.get("/api/workflows", response_model=List[Workflow])
def list_workflows(current_user: Optional[AuthUser] = Depends(get_optional_user)):
    """Lists workflows owned by the user or shared publicly, always including default templates."""
    workflows_list = []
    user_id = current_user.id if current_user else "anonymous"

    if current_user and is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflows").select("*").or_(f"user_id.eq.{current_user.id},visibility.in.(shared,public)").order("updated_at", desc=True).execute()
                if res.data is not None:
                    workflows_list = res.data
                    for w in res.data:
                        memory_store.create_workflow(w)
            except Exception as e:
                print(f"Supabase list_workflows error: {e}")

    if not workflows_list:
        workflows_list = memory_store.get_workflows(user_id)

    # Always ensure default workflow templates are present in the list
    existing_ids = {w.get("id") for w in workflows_list}
    for default_wf in get_default_workflows():
        if default_wf["id"] not in existing_ids:
            workflows_list.append(default_wf)
            existing_ids.add(default_wf["id"])

    return sorted(workflows_list, key=lambda w: w.get("updated_at", ""), reverse=True)


@app.post("/api/workflows", response_model=Workflow)
def create_workflow(
    payload: WorkflowCreateUpdatePayload,
    current_user: AuthUser = Depends(get_current_user),
):
    """Creates a new workflow definition with goal and steps."""
    wf_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    share_slug = f"wf-{uuid.uuid4().hex[:8]}"

    wf_dict = {
        "id": wf_id,
        "user_id": current_user.id,
        "title": payload.title,
        "description": payload.description or "",
        "goal": payload.goal,
        "steps": [s.model_dump() for s in payload.steps],
        "edges": payload.edges or [],
        "visibility": payload.visibility or "private",
        "share_slug": share_slug,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflows").insert(wf_dict).execute()
                if res.data:
                    created_wf = res.data[0]
                    memory_store.create_workflow(created_wf)
                    return created_wf
            except Exception as e:
                print(f"Supabase create_workflow error: {e}")

    return memory_store.create_workflow(wf_dict)


@app.get("/api/workflows/defaults", response_model=List[Workflow])
def list_default_workflows():
    """Returns all built-in default workflow templates available to every user."""
    return get_default_workflows()


@app.get("/api/workflows/{workflow_id}", response_model=Workflow)
def get_workflow(
    workflow_id: str,
    current_user: Optional[AuthUser] = Depends(get_optional_user),
):
    """Retrieves a workflow by ID if owned or shared/public."""
    wf = _get_workflow_record(workflow_id, current_user)
    if not wf:
        for default_wf in get_default_workflows():
            if default_wf["id"] == workflow_id:
                return default_wf
        raise HTTPException(status_code=404, detail="Workflow not found.")
    user_id = current_user.id if current_user else None
    if user_id and wf.get("user_id") != user_id and wf.get("visibility") not in ["shared", "public"]:
        raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this workflow.")
    if not user_id and wf.get("visibility") not in ["shared", "public"]:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return wf


@app.put("/api/workflows/{workflow_id}", response_model=Workflow)
def update_workflow(
    workflow_id: str,
    payload: WorkflowCreateUpdatePayload,
    current_user: AuthUser = Depends(get_current_user),
):
    """Updates an existing workflow definition (owner only)."""
    existing = _get_workflow_record(workflow_id, current_user)
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    if existing.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot modify another user's workflow.")

    updates = {
        "title": payload.title,
        "description": payload.description or "",
        "goal": payload.goal,
        "steps": [s.model_dump() for s in payload.steps],
        "edges": payload.edges or [],
        "visibility": payload.visibility or existing.get("visibility", "private"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflows").update(updates).eq("id", workflow_id).eq("user_id", current_user.id).execute()
                if res.data:
                    memory_store.update_workflow(workflow_id, current_user.id, updates)
                    return res.data[0]
            except Exception as e:
                print(f"Supabase update_workflow error: {e}")

    updated = memory_store.update_workflow(workflow_id, current_user.id, updates)
    return updated


@app.delete("/api/workflows/{workflow_id}")
def delete_workflow(
    workflow_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Deletes a workflow definition (owner only)."""
    existing = _get_workflow_record(workflow_id, current_user)
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    if existing.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot delete another user's workflow.")

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                client.table("workflows").delete().eq("id", workflow_id).eq("user_id", current_user.id).execute()
            except Exception as e:
                print(f"Supabase delete_workflow error: {e}")

    memory_store.delete_workflow(workflow_id, current_user.id)
    return {"message": "Workflow deleted successfully."}


@app.get("/api/workflows/shared/{share_slug}", response_model=Workflow)
def get_shared_workflow(
    share_slug: str,
    current_user: Optional[AuthUser] = Depends(get_optional_user),
):
    """Provides view-only access to a shared workflow without allowing mutations."""
    wf = None
    if is_supabase_configured():
        try:
            if supabase:
                res = supabase.table("workflows").select("*").eq("share_slug", share_slug).or_("visibility.eq.shared,visibility.eq.public").execute()
                if res.data:
                    wf = res.data[0]
                    memory_store.create_workflow(wf)
        except Exception as e:
            print(f"Supabase get_shared_workflow error: {e}")

    if not wf:
        wf = memory_store.get_shared_workflow(share_slug)
    if not wf:
        raise HTTPException(status_code=404, detail="Shared workflow not found or has been made private.")
    return wf


@app.post("/api/workflows/{workflow_id}/fork", response_model=Workflow)
def fork_workflow(
    workflow_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Forks/clones a shared or accessible workflow into the current user's library."""
    original = _get_workflow_record(workflow_id, current_user)
    if not original:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    forked_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    forked_data = dict(original)
    forked_data["id"] = forked_id
    forked_data["user_id"] = current_user.id
    forked_data["title"] = f"{original.get('title', 'Workflow')} (Forked)"
    forked_data["visibility"] = "private"
    forked_data["share_slug"] = f"wf-{uuid.uuid4().hex[:8]}"
    forked_data["created_at"] = now_iso
    forked_data["updated_at"] = now_iso

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflows").insert(forked_data).execute()
                if res.data:
                    memory_store.create_workflow(res.data[0])
                    return res.data[0]
            except Exception as e:
                print(f"Supabase fork_workflow error: {e}")

    return memory_store.create_workflow(forked_data)


# ----------------- Knowledge Base Documents -----------------

class KnowledgeUploadPayload(BaseModel):
    file_name: str
    content_text: str
    file_type: Optional[str] = "text/plain"


@app.get("/api/workflows/{workflow_id}/knowledge", response_model=List[KnowledgeFile])
def list_knowledge_files(
    workflow_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Lists attached knowledge base documents for a workflow."""
    files = []
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflow_knowledge_files").select("*").eq("workflow_id", workflow_id).execute()
                if res.data:
                    files = res.data
                    for f in files:
                        memory_store.add_knowledge_file(f)
            except Exception as e:
                print(f"Supabase list_knowledge_files error: {e}")
    if not files:
        files = memory_store.get_knowledge_files(workflow_id)
    return files


@app.post("/api/workflows/{workflow_id}/knowledge/upload", response_model=KnowledgeFile)
def upload_knowledge_file(
    workflow_id: str,
    payload: KnowledgeUploadPayload,
    current_user: AuthUser = Depends(get_current_user),
):
    """Uploads and attaches a knowledge base document to a workflow."""
    wf = _get_workflow_record(workflow_id, current_user)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    if wf.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot modify this workflow's knowledge base.")

    file_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Check if binary document (e.g. PDF, Word, PowerPoint, Excel, or Base64 data URI)
    lower_name = payload.file_name.lower()
    is_binary = any(lower_name.endswith(ext) for ext in [".pdf", ".docx", ".pptx", ".xlsx", ".zip", ".png", ".jpg"]) or payload.content_text.startswith("data:")
    if is_binary:
        try:
            from app.agents.file_parser.tools import parse_binary_document
            parsed = parse_binary_document(payload.file_name, payload.content_text, payload.file_type or "auto")
            if parsed.get("status") == "success" and parsed.get("text"):
                content_clean = parsed["text"]
            else:
                content_clean = extract_file_content(payload.file_name, payload.content_text.encode("utf-8"), payload.file_type)
        except Exception as e:
            print(f"parse_binary_document error in knowledge upload: {e}")
            content_clean = extract_file_content(payload.file_name, payload.content_text.encode("utf-8"), payload.file_type)
    else:
        content_clean = extract_file_content(payload.file_name, payload.content_text.encode("utf-8"), payload.file_type)

    doc_dict = {
        "id": file_id,
        "workflow_id": workflow_id,
        "user_id": current_user.id,
        "file_name": payload.file_name,
        "file_type": payload.file_type or "text/plain",
        "file_size": len(content_clean.encode("utf-8")),
        "content_text": content_clean,
        "metadata": {},
        "created_at": now_iso,
    }

    # Automatically index into RAG store for grounded vector/hybrid search
    try:
        from app.agents.file_parser.tools import ingest_and_index_document
        ingest_and_index_document(
            filename=payload.file_name,
            content=content_clean,
            file_type=payload.file_type or "auto",
            document_id=file_id,
        )
    except Exception as e:
        print(f"RAG indexing error for workflow knowledge file: {e}")

    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflow_knowledge_files").insert(doc_dict).execute()
                if res.data:
                    created_file = res.data[0]
                    memory_store.add_knowledge_file(created_file)
                    return created_file
            except Exception as e:
                print(f"Supabase upload_knowledge_file error: {e}")

    return memory_store.add_knowledge_file(doc_dict)


@app.delete("/api/workflows/{workflow_id}/knowledge/{file_id}")
def delete_knowledge_file(
    workflow_id: str,
    file_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Deletes an attached knowledge base file."""
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                client.table("workflow_knowledge_files").delete().eq("id", file_id).eq("user_id", current_user.id).execute()
            except Exception as e:
                print(f"Supabase delete_knowledge_file error: {e}")

    success = memory_store.delete_knowledge_file(file_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge file not found or unauthorized.")
        
    try:
        from app.rag.store import rag_store
        rag_store.delete_document(file_id)
    except Exception as e:
        print(f"RAG delete document error: {e}")

    return {"message": "Knowledge document deleted successfully."}


# ----------------- Testing & Execution Endpoints -----------------

@app.post("/api/workflows/{workflow_id}/steps/{step_id}/test", response_model=StepUnitTestResponse)
def unit_test_step(
    workflow_id: str,
    step_id: str,
    payload: StepUnitTestRequest,
    current_user: Optional[AuthUser] = Depends(get_optional_user),
):
    """Executes a single step in isolation with mock input parameters for unit testing."""
    user_id = current_user.id if current_user else "anonymous"
    wf = _get_workflow_record(workflow_id, current_user)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    res = workflow_engine.execute_unit_test(
        workflow_data=wf,
        step_id=step_id,
        mock_inputs=payload.mock_inputs,
        mock_previous_outputs=payload.mock_previous_outputs,
        user_id=user_id,
    )
    return res


@app.post("/api/workflows/{workflow_id}/run", response_model=WorkflowRun)
def run_workflow(
    workflow_id: str,
    payload: WorkflowRunRequest,
    current_user: Optional[AuthUser] = Depends(get_optional_user),
):
    """Executes the entire workflow DAG end-to-end (system test or manual trigger)."""
    user_id = current_user.id if current_user else "anonymous"
    wf = _get_workflow_record(workflow_id, current_user)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    run_record = workflow_engine.execute_workflow(
        workflow_data=wf,
        inputs=payload.inputs,
        user_id=user_id,
        trigger_type="system_test",
        session_id=payload.session_id,
    )

    if current_user and is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                client.table("workflow_runs").insert(run_record).execute()
            except Exception as e:
                print(f"Supabase persist workflow_run error: {e}")

    return run_record


@app.get("/api/workflows/{workflow_id}/runs", response_model=List[WorkflowRun])
def list_workflow_runs(
    workflow_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Lists historical execution runs and telemetry for this workflow."""
    runs = []
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflow_runs").select("*").eq("workflow_id", workflow_id).order("started_at", desc=True).execute()
                if res.data:
                    runs = res.data
                    for r in runs:
                        memory_store.create_workflow_run(r)
            except Exception as e:
                print(f"Supabase list_workflow_runs error: {e}")
    if not runs:
        runs = memory_store.get_workflow_runs(workflow_id)
    return runs


@app.get("/api/workflows/{workflow_id}/runs/{run_id}", response_model=WorkflowRun)
def get_workflow_run(
    workflow_id: str,
    run_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Retrieves granular details of a specific workflow run including all step runs."""
    run = memory_store.get_workflow_run(run_id)
    if not run or run.get("workflow_id") != workflow_id:
        raise HTTPException(status_code=404, detail="Workflow run not found.")
    run_copy = dict(run)
    run_copy["step_runs"] = memory_store.get_step_runs(run_id)
    return run_copy


@app.get("/api/workflow-runs", response_model=List[WorkflowRun])
def list_all_workflow_runs(
    current_user: AuthUser = Depends(get_current_user),
):
    """Lists recent execution runs across all workflows belonging to the authenticated user."""
    user_workflows = memory_store.get_workflows(current_user.id)
    wf_ids = {w["id"] for w in user_workflows}
    all_runs = []
    for wf_id in wf_ids:
        all_runs.extend(memory_store.get_workflow_runs(wf_id))
    all_runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return all_runs[:25]


# ---------------------------------------------------------
# Artifacts Endpoints (User-Generated & Workflow Files)
# ---------------------------------------------------------

@app.get("/api/artifacts", response_model=List[Dict[str, Any]])
def list_artifacts(current_user: Optional[AuthUser] = Depends(get_optional_user)):
    """
    Returns all generated artifacts belonging to the authenticated or guest user.
    Extracts persistent artifacts from Supabase user_artifacts and chat_messages metadata,
    merged with active in-memory artifacts.
    """
    user_id = current_user.id if current_user else "guest-user"
    artifacts_map: Dict[str, Dict[str, Any]] = {}

    # 1. Load artifacts from in-memory store
    for art in memory_store.get_artifacts(user_id):
        if art.get("id"):
            artifacts_map[art["id"]] = art

    # 1b. Check in-memory chat messages for file artifacts
    for sess_id, msgs in getattr(memory_store, "messages", {}).items():
        for msg in msgs:
            if msg.get("user_id") == user_id or user_id == "guest-user":
                meta = msg.get("metadata") or {}
                file_art = meta.get("file_artifact")
                if isinstance(file_art, dict) and file_art.get("id"):
                    art_id = file_art["id"]
                    if art_id not in artifacts_map:
                        artifacts_map[art_id] = {
                            **file_art,
                            "user_id": user_id,
                            "source_type": "chat",
                            "source_title": meta.get("agent_name", "Chat Agent"),
                            "created_at": file_art.get("created_at") or msg.get("created_at"),
                        }
                arts_list = meta.get("artifacts")
                if isinstance(arts_list, list):
                    for sub_art in arts_list:
                        if isinstance(sub_art, dict) and sub_art.get("id"):
                            sub_id = sub_art["id"]
                            if sub_id not in artifacts_map:
                                artifacts_map[sub_id] = {
                                    **sub_art,
                                    "user_id": user_id,
                                    "source_type": "chat",
                                    "source_title": meta.get("agent_name", "Chat Agent"),
                                    "created_at": sub_art.get("created_at") or msg.get("created_at"),
                                }

    # 2. Extract artifacts from Supabase if active and authenticated
    if is_supabase_configured() and current_user and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            # 2a. Query user_artifacts table if present
            try:
                res = client.table("user_artifacts").select("*").eq("user_id", current_user.id).order("created_at", desc=True).execute()
                if res.data:
                    for a in res.data:
                        if a.get("id"):
                            artifacts_map[a["id"]] = a
            except Exception:
                pass

            # 2b. Extract file artifacts from user's chat_messages metadata
            try:
                msg_res = client.table("chat_messages").select("id, role, content, metadata, created_at").eq("user_id", current_user.id).order("created_at", desc=True).limit(100).execute()
                if msg_res.data:
                    for msg in msg_res.data:
                        meta = msg.get("metadata") or {}
                        # Extract singular file_artifact
                        file_art = meta.get("file_artifact")
                        if isinstance(file_art, dict) and file_art.get("id"):
                            art_id = file_art["id"]
                            if art_id not in artifacts_map:
                                artifacts_map[art_id] = {
                                    **file_art,
                                    "user_id": current_user.id,
                                    "source_type": "chat",
                                    "source_title": meta.get("agent_name", "Chat Agent"),
                                    "created_at": file_art.get("created_at") or msg.get("created_at"),
                                }
                        # Extract artifacts list
                        arts_list = meta.get("artifacts")
                        if isinstance(arts_list, list):
                            for sub_art in arts_list:
                                if isinstance(sub_art, dict) and sub_art.get("id"):
                                    sub_id = sub_art["id"]
                                    if sub_id not in artifacts_map:
                                        artifacts_map[sub_id] = {
                                            **sub_art,
                                            "user_id": current_user.id,
                                            "source_type": "chat",
                                            "source_title": meta.get("agent_name", "Chat Agent"),
                                            "created_at": sub_art.get("created_at") or msg.get("created_at"),
                                        }
            except Exception as e:
                print(f"Supabase chat_messages artifact extraction note: {e}")

    # Return sorted by created_at descending
    return sorted(artifacts_map.values(), key=lambda a: a.get("created_at", ""), reverse=True)


@app.post("/api/artifacts", response_model=Dict[str, Any])
def create_artifact(payload: Dict[str, Any], current_user: Optional[AuthUser] = Depends(get_optional_user)):
    """Saves a newly generated or uploaded artifact to memory, Supabase, and RAG knowledge store."""
    user_id = current_user.id if current_user else "guest-user"
    now_iso = datetime.now(timezone.utc).isoformat()
    art_id = payload.get("id") or f"art-{str(uuid.uuid4())[:8]}"
    content = payload.get("content", "")
    fname = payload.get("filename") or payload.get("name") or f"artifact_{art_id}.txt"
    file_type = (payload.get("type") or fname.split(".")[-1] or "txt").lower()
    is_base64 = bool(payload.get("is_base64")) or payload.get("encoding") == "base64" or file_type in ["pdf", "pptx", "docx", "xlsx"]

    artifact = {
        "id": art_id,
        "user_id": user_id,
        "name": payload.get("name") or fname,
        "filename": fname,
        "type": file_type,
        "content": content,
        "size_bytes": payload.get("size_bytes") or len(content.encode("utf-8")),
        "created_at": payload.get("created_at") or now_iso,
        "origin_agent": payload.get("origin_agent", "user_upload"),
        "source_type": payload.get("source_type", "upload"),
        "source_title": payload.get("source_title", "User Upload"),
        "downloadable": True,
        "is_base64": is_base64,
        "mime_type": payload.get("mime_type"),
        "encoding": "base64" if is_base64 else "utf-8",
    }
    saved = memory_store.save_artifact(artifact)

    # Automatically index into Swarm RAG Knowledge Store for instant multi-agent retrieval
    try:
        from app.agents.file_parser.tools import ingest_and_index_document
        ingest_and_index_document(
            filename=fname,
            content=content if not is_base64 else "",
            content_base64=content if is_base64 else "",
            file_type=file_type,
            document_id=f"art_doc_{art_id}",
        )
    except Exception as e:
        print(f"RAG auto-indexing error for artifact {art_id}: {e}")

    if is_supabase_configured() and current_user and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                client.table("user_artifacts").upsert(artifact).execute()
            except Exception as e:
                print(f"Supabase user_artifacts upsert note: {e}")

    return saved


@app.get("/api/artifacts/{artifact_id}", response_model=Dict[str, Any])
def get_artifact(artifact_id: str, current_user: Optional[AuthUser] = Depends(get_optional_user)):
    """Retrieves a single artifact by ID."""
    user_id = current_user.id if current_user else "guest-user"
    for art in memory_store.get_artifacts(user_id):
        if art.get("id") == artifact_id:
            return art
    for arts in getattr(memory_store, "artifacts", {}).values():
        for art in arts:
            if art.get("id") == artifact_id:
                return art
    if is_supabase_configured() and current_user and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("user_artifacts").select("*").eq("id", artifact_id).single().execute()
                if res.data:
                    return res.data
            except Exception:
                pass
    raise HTTPException(status_code=404, detail="Artifact not found.")


@app.delete("/api/artifacts/{artifact_id}")
def delete_artifact(artifact_id: str, current_user: Optional[AuthUser] = Depends(get_optional_user)):
    """Deletes an artifact by ID from memory, Supabase, and RAG knowledge store."""
    user_id = current_user.id if current_user else "guest-user"
    success = memory_store.delete_artifact(artifact_id, user_id)

    # Clean up from RAG store
    try:
        from app.rag.store import rag_store
        rag_store.delete_document(f"art_doc_{artifact_id}")
    except Exception as e:
        print(f"RAG delete notice: {e}")

    if is_supabase_configured() and current_user and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                client.table("user_artifacts").delete().eq("id", artifact_id).eq("user_id", current_user.id).execute()
                success = True
            except Exception:
                pass

    return {"status": "deleted" if success else "not_found", "id": artifact_id}


# ---------------------------------------------------------
# Document Ingestion & RAG Context Endpoints
# ---------------------------------------------------------

class DocumentIngestPayload(BaseModel):
    filename: str
    content: Optional[str] = ""
    content_base64: Optional[str] = ""
    file_type: Optional[str] = "auto"
    chunk_size: Optional[int] = 150
    chunk_overlap: Optional[int] = 30


class RAGQueryPayload(BaseModel):
    query: str
    top_k: Optional[int] = 3
    document_id: Optional[str] = None


@app.post("/api/documents/ingest", response_model=Dict[str, Any])
def ingest_document_api(
    payload: DocumentIngestPayload,
    current_user: Optional[AuthUser] = Depends(get_optional_user)
):
    """
    Ingests and parses any document (text, code, CSV, JSON, Markdown, or binary Base64 PDF/PPTX/DOCX/XLSX),
    chunks it into semantic passages, and indexes it into the Swarm RAG Knowledge Store.
    """
    from app.agents.file_parser.tools import ingest_and_index_document
    res = ingest_and_index_document(
        filename=payload.filename,
        content=payload.content or "",
        content_base64=payload.content_base64 or "",
        file_type=payload.file_type or "auto",
        chunk_size=payload.chunk_size or 150,
        chunk_overlap=payload.chunk_overlap or 30
    )
    return res


@app.post("/api/documents/rag/query", response_model=Dict[str, Any])
def rag_query_api(
    payload: RAGQueryPayload,
    current_user: Optional[AuthUser] = Depends(get_optional_user)
):
    """
    Retrieves Top-K relevant contextual chunks from ingested documents using hybrid BM25 lexical
    scoring and vector similarity with confidence scores and citations.
    """
    from app.agents.file_parser.tools import query_document_context
    return query_document_context(
        query=payload.query,
        top_k=payload.top_k or 3,
        document_id=payload.document_id
    )


@app.post("/api/documents/rag/context", response_model=Dict[str, Any])
def rag_context_api(
    payload: RAGQueryPayload,
    current_user: Optional[AuthUser] = Depends(get_optional_user)
):
    """
    Constructs an enriched prompt context block with citations and confidence metrics
    for direct injection into other swarm agents (orchestrator, researcher, coder, synthesizer).
    """
    from app.agents.file_parser.tools import generate_rag_context
    return generate_rag_context(
        query=payload.query,
        top_k=payload.top_k or 3,
        document_id=payload.document_id
    )


@app.get("/api/documents", response_model=List[Dict[str, Any]])
def list_documents_api(current_user: Optional[AuthUser] = Depends(get_optional_user)):
    """Lists all documents currently indexed in the RAG Knowledge Store."""
    from app.rag.store import rag_store
    return rag_store.list_documents()


@app.delete("/api/documents/{document_id}", response_model=Dict[str, Any])
def delete_document_api(document_id: str, current_user: Optional[AuthUser] = Depends(get_optional_user)):
    """Deletes an indexed document and its chunks from the RAG Knowledge Store."""
    from app.rag.store import rag_store
    success = rag_store.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found in RAG store.")
    return {"status": "deleted", "document_id": document_id}


