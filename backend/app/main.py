import os
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
    is_supabase_configured,
    get_user_supabase_client,
    memory_store,
)

# Load environment variables from .env
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Initialize FastAPI application
app = FastAPI(
    title="Swarm Backend API",
    version="1.2.0",
    description="FastAPI service for running an autonomous AI agent swarm powered by Google Gemini, with Supabase session and usage persistence.",
)

# CORS middleware for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Data Models
# ---------------------------------------------------------

class Agent(BaseModel):
    id: str = Field(..., description="Unique agent identifier (e.g. 'researcher', 'coder')")
    name: str = Field(..., description="Display name for the agent")
    role: str = Field(..., description="Specialty and purpose of the agent")
    status: str = Field(default="active", description="Operational state ('active', 'busy', 'idle', 'offline')")
    system_prompt: Optional[str] = Field(None, description="Specialized system instructions defining agent persona")

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

# Session & History Models
class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field("New Conversation", description="Chat session title")
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
# Swarm Database (Pre-populated with 2 Basic Agents)
# ---------------------------------------------------------

DEFAULT_AGENTS: List[Agent] = [
    Agent(
        id="researcher",
        name="Research Agent",
        role="Synthesizes information, conducts analysis and deep research",
        status="active",
        system_prompt=(
            "You are the Research Agent in an autonomous AI agent swarm. "
            "Your specialty is thorough investigation, structured synthesis, and clear factual analysis. "
            "Organize responses with clear markdown headings, bullet points, and actionable takeaways."
        ),
    ),
    Agent(
        id="coder",
        name="Coder Agent",
        role="Expert software engineer specializing in clean code and debugging",
        status="active",
        system_prompt=(
            "You are the Coder Agent in an autonomous AI agent swarm. "
            "Your specialty is writing production-ready, clean, well-tested code across modern stacks. "
            "Provide concise technical explanations, adhere to type safety, and highlight key design decisions."
        ),
    ),
]

agents_db: List[Agent] = list(DEFAULT_AGENTS)

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
    # Sanitize parent_id: cannot be root-greeting, empty string, or self
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
                # If clean_parent is given, verify it exists in DB to avoid FK constraint violation
                if clean_parent is not None:
                    chk = client.table("chat_messages").select("id").eq("id", clean_parent).eq("session_id", session_id).execute()
                    if not chk.data:
                        record["parent_id"] = None

                client.table("chat_messages").upsert(record).execute()
                return record
            except Exception as e:
                print(f"Supabase chat_messages insert error: {e}")
                # Fallback: if parent_id still triggered an FK violation, retry safely with parent_id=None
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

def route_agent(target_id: Optional[str], last_user_content: str) -> Agent:
    """Selects the target agent or auto-routes based on prompt intent."""
    if target_id:
        for agent in agents_db:
            if agent.id.lower() == target_id.lower():
                return agent

    # Automatic Swarm Routing
    content_lower = last_user_content.lower()
    coding_keywords = ["code", "function", "bug", "python", "javascript", "typescript", "fastapi", "react", "sql", "api", "git", "class", "error", "compile"]
    if any(keyword in content_lower for keyword in coding_keywords):
        for agent in agents_db:
            if agent.id == "coder":
                return agent

    # Default to researcher
    for agent in agents_db:
        if agent.id == "researcher":
            return agent

    return agents_db[0]

# ---------------------------------------------------------
# Root & System Endpoints
# ---------------------------------------------------------

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Swarm Backend API",
        "version": "1.2.0",
        "docs_url": "/docs",
        "supabase_connected": is_supabase_configured(),
    }

@app.get("/api/health")
def health_check():
    """Health check endpoint with swarm and database status."""
    _, api_key = get_gemini_client()
    return {
        "status": "ok",
        "agents_online": len(agents_db),
        "gemini_configured": bool(api_key),
        "supabase_configured": is_supabase_configured(),
        "active_agents": [agent.id for agent in agents_db],
    }

@app.get("/api/agents", response_model=List[Agent])
def get_agents():
    """Returns the roster of all active agents in the swarm."""
    return agents_db

@app.post("/api/agents", response_model=Agent)
def create_agent(agent: Agent):
    """Registers a new specialized agent into the swarm."""
    for existing in agents_db:
        if existing.id == agent.id:
            raise HTTPException(status_code=400, detail=f"Agent with id '{agent.id}' already exists.")
    agents_db.append(agent)
    return agent

# ---------------------------------------------------------
# Chat Sessions & History Endpoints
# ---------------------------------------------------------

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
    session_data = {
        "id": session_id,
        "user_id": current_user.id,
        "title": payload.title or "New Conversation",
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

    # 1. LIVE GEMINI API GENERATION
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

            model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            config = types.GenerateContentConfig(
                system_instruction=selected_agent.system_prompt or "You are a helpful AI assistant in an agent swarm.",
                temperature=0.7,
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
                    "args": {"target_agent": selected_agent.id, "model": model_name},
                    "result": {"status": "routed", "agent_name": selected_agent.name}
                }
            ]

            agent_response_content = response.text or "Completed without output text."
            agent_node_id = f"agent-{int(time.time()*1000)}"

            agent_metadata = {
                "agent_state": "completed",
                "agent_id": selected_agent.id,
                "agent_name": selected_agent.name,
                "tool_calls": tool_calls,
                "tokens_used": total_tokens,
                "latency_ms": latency_ms,
                "model": model_name,
                "node_id": agent_node_id,
            }

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
                    agent_id=selected_agent.id,
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
                "agent_id": selected_agent.id,
                "latency_ms": latency_ms,
                "tokens_used": 0,
                "error_detail": str(e),
                "node_id": agent_node_id,
            }
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
                    model=model_name,
                    agent_id=selected_agent.id,
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
            "args": {"agent_id": selected_agent.id, "role": selected_agent.role},
            "result": {"status": "online", "mode": "swarm_active"}
        },
        {
            "tool": "gemini_provider_check",
            "args": {"env_var": "GEMINI_API_KEY"},
            "result": {"configured": False, "instructions": "Set GEMINI_API_KEY in backend/.env"}
        }
    ]

    fallback_content = (
        f"Hello! I am **{selected_agent.name}** (`{selected_agent.id}`).\n\n"
        f"**My Role:** {selected_agent.role}\n\n"
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
        "agent_id": selected_agent.id,
        "agent_name": selected_agent.name,
        "tool_calls": demo_tools,
        "tokens_used": simulated_tokens,
        "latency_ms": latency_ms,
        "mode": "demo_fallback",
        "node_id": agent_node_id,
    }

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
            agent_id=selected_agent.id,
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
