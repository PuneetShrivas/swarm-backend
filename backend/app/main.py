import os
import re
import json
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
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

class AgentTestRequest(BaseModel):
    agent_id: Optional[str] = None
    system_prompt: str
    input_prompt: str
    model: Optional[str] = "gemini-3.8-flash"
    temperature: Optional[float] = 0.3
    tool_ids: Optional[List[str]] = Field(default_factory=list)
    mock_context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AgentTestResponse(BaseModel):
    status: str
    content: str
    tokens_used: int
    latency_ms: float
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)

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
    Normalizes and maps legacy/deprecated models to latest active models.
    Maps gemini-2.5-flash / gemini-2.0-flash / gemini-1.5-flash -> gemini-3.8-flash
    Maps gemini-2.5-pro / gemini-2.0-pro / gemini-1.5-pro -> gemini-4-argon
    """
    if not model_name or not str(model_name).strip():
        return os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    m = str(model_name).strip()
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

    # 2. Heuristic Intent Matching (Domain specialists evaluated first)
    review_keywords = ["audit", "security", "vulnerability", "owasp", "leak", "test coverage", "qa", "lint", "complexity"]
    if any(k in content_lower for k in review_keywords):
        reviewer = agent_registry.get("reviewer")
        if reviewer:
            return reviewer

    data_keywords = ["statistics", "mean", "median", "table", "csv", "percentile", "trend", "distribution", "variance", "stdev", "metrics"]
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

    research_keywords = ["research", "investigate", "history", "quantum", "paper", "scientific", "study", "fact check", "source", "citation"]
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

    # 2. LIVE GEMINI API GENERATION
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

            model_name = chosen_model if not chosen_model.startswith("sonar") else normalize_model_name(os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"))
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

    fallback_content = (
        f"Hello! I am **{agent_name}** (`{agent_id}`).\n\n"
        f"**My Role:** {agent_role}\n\n"
        f"I received your inquiry:\n> \"*{last_user_message.content}*\"\n\n"
        f"### ⚙️ Gemini API Setup Required\n"
        f"To enable live generative responses from Google Gemini:\n"
        f"1. Open `backend/.env`\n"
        f"2. Add your Gemini API Key: `GEMINI_API_KEY=\"your_key_here\"` (get one free at [Google AI Studio](https://aistudio.google.com/))\n"
        f"3. Once added, the backend will immediately stream live AI responses for this agent!\n\n"
        f"The frontend interactive features (sessions, history, branching, tool inspection, and usage tracking) are fully active and connected to this endpoint."
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
    current_user: AuthUser = Depends(get_current_user),
):
    """Executes a custom or prebuilt agent in isolation with user test prompt."""
    start_time = time.time()
    client, api_key = get_gemini_client()

    tool_calls = []
    if payload.tool_ids:
        for tid in payload.tool_ids:
            tool_rec = _get_tool_record(tid, current_user)
            if tool_rec:
                tool_calls.append({
                    "tool": tool_rec.get("name", tid),
                    "args": {"test_mode": True},
                    "result": {"status": "available", "description": tool_rec.get("description")}
                })

    if client:
        try:
            from google.genai import types
            model_name = normalize_model_name(payload.model or os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"))
            response = client.models.generate_content(
                model=model_name,
                contents=[types.Part.from_text(text=payload.input_prompt)],
                config=types.GenerateContentConfig(
                    system_instruction=payload.system_prompt,
                    temperature=payload.temperature or 0.3,
                ),
            )
            latency_ms = round((time.time() - start_time) * 1000, 2)
            tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0

            return AgentTestResponse(
                status="success",
                content=response.text or "Agent completed without content.",
                tokens_used=tokens,
                latency_ms=latency_ms,
                tool_calls=tool_calls,
            )
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return AgentTestResponse(
                status="error",
                content=f"Agent test execution error: {str(e)}",
                tokens_used=0,
                latency_ms=latency_ms,
                tool_calls=tool_calls,
            )

    # Simulation / Offline Fallback Mode
    latency_ms = round((time.time() - start_time) * 1000, 2)
    simulated_content = (
        f"[Test Simulation Mode]\n\n"
        f"**Agent System Prompt Verified:**\n> {payload.system_prompt[:120]}...\n\n"
        f"**Response to:** \"{payload.input_prompt}\"\n\n"
        f"I have processed your prompt following my persona instructions. All constraints and guidelines were respected."
    )
    return AgentTestResponse(
        status="success",
        content=simulated_content,
        tokens_used=120,
        latency_ms=latency_ms,
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

def _get_workflow_record(workflow_id: str, current_user: AuthUser) -> Optional[Dict[str, Any]]:
    """Retrieves a workflow from Supabase or MemoryStore with cache sync."""
    wf = None
    if is_supabase_configured() and not current_user.id.startswith("test-"):
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
    return wf


@app.get("/api/workflows", response_model=List[Workflow])
def list_workflows(current_user: AuthUser = Depends(get_current_user)):
    """Lists workflows owned by the user or shared publicly."""
    if is_supabase_configured() and not current_user.id.startswith("test-"):
        client = get_user_supabase_client(current_user.token)
        if client:
            try:
                res = client.table("workflows").select("*").or_(f"user_id.eq.{current_user.id},visibility.in.(shared,public)").order("updated_at", desc=True).execute()
                if res.data is not None:
                    for w in res.data:
                        memory_store.create_workflow(w)
                    return res.data
            except Exception as e:
                print(f"Supabase list_workflows error: {e}")
    return memory_store.get_workflows(current_user.id)


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


@app.get("/api/workflows/{workflow_id}", response_model=Workflow)
def get_workflow(
    workflow_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Retrieves a workflow by ID if owned or shared."""
    wf = _get_workflow_record(workflow_id, current_user)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    if wf.get("user_id") != current_user.id and wf.get("visibility") not in ["shared", "public"]:
        raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this workflow.")
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
    return {"message": "Knowledge document deleted successfully."}


# ----------------- Testing & Execution Endpoints -----------------

@app.post("/api/workflows/{workflow_id}/steps/{step_id}/test", response_model=StepUnitTestResponse)
def unit_test_step(
    workflow_id: str,
    step_id: str,
    payload: StepUnitTestRequest,
    current_user: AuthUser = Depends(get_current_user),
):
    """Executes a single step in isolation with mock input parameters for unit testing."""
    wf = _get_workflow_record(workflow_id, current_user)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    res = workflow_engine.execute_unit_test(
        workflow_data=wf,
        step_id=step_id,
        mock_inputs=payload.mock_inputs,
        mock_previous_outputs=payload.mock_previous_outputs,
        user_id=current_user.id,
    )
    return res


@app.post("/api/workflows/{workflow_id}/run", response_model=WorkflowRun)
def run_workflow(
    workflow_id: str,
    payload: WorkflowRunRequest,
    current_user: AuthUser = Depends(get_current_user),
):
    """Executes the entire workflow DAG end-to-end (system test or manual trigger)."""
    wf = _get_workflow_record(workflow_id, current_user)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    run_record = workflow_engine.execute_workflow(
        workflow_data=wf,
        inputs=payload.inputs,
        user_id=current_user.id,
        trigger_type="system_test",
        session_id=payload.session_id,
    )

    if is_supabase_configured() and not current_user.id.startswith("test-"):
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
    run_copy["step_runs"] = memory_store.get_step_runs(run_id)
    return run_copy

