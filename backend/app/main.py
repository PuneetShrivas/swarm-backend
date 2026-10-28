import os
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize FastAPI application
app = FastAPI(
    title="Swarm Backend API",
    version="1.1.0",
    description="FastAPI service for running an autonomous AI agent swarm powered by Google Gemini.",
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
# API Endpoints
# ---------------------------------------------------------

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Swarm Backend API",
        "version": "1.1.0",
        "docs_url": "/docs",
    }

@app.get("/api/health")
def health_check():
    """Health check endpoint with swarm status."""
    _, api_key = get_gemini_client()
    return {
        "status": "ok",
        "agents_online": len(agents_db),
        "gemini_configured": bool(api_key),
        "active_agents": [agent.id for agent in agents_db],
    }

@app.get("/api/agents", response_model=List[Agent])
def get_agents():
    """Returns the roster of all active agents in the swarm."""
    return agents_db

@app.post("/api/agents", response_model=Agent)
def create_agent(agent: Agent):
    """Registers a new specialized agent into the swarm."""
    # Check if agent ID already exists
    for existing in agents_db:
        if existing.id == agent.id:
            raise HTTPException(status_code=400, detail=f"Agent with id '{agent.id}' already exists.")
    agents_db.append(agent)
    return agent

@app.post("/api/chat", response_model=Message)
def chat(request: ChatRequest):
    """
    Main swarm chat endpoint.
    Routes prompt to the appropriate swarm agent and executes via Gemini API.
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

    # 1. LIVE GEMINI API GENERATION
    if client:
        try:
            from google.genai import types

            # Format conversation history for Gemini
            gemini_contents = []
            for msg in request.messages:
                # Map roles: 'user' -> 'user', 'agent' -> 'model'
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
            tokens_used = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens_used = getattr(response.usage_metadata, "total_token_count", None)

            # Detect if agent simulated a tool call or action
            tool_calls = [
                {
                    "tool": "swarm_router",
                    "args": {"target_agent": selected_agent.id, "model": model_name},
                    "result": {"status": "routed", "agent_name": selected_agent.name}
                }
            ]

            return Message(
                role="agent",
                content=response.text or "Completed without output text.",
                metadata={
                    "agent_state": "completed",
                    "agent_id": selected_agent.id,
                    "agent_name": selected_agent.name,
                    "tool_calls": tool_calls,
                    "tokens_used": tokens_used,
                    "latency_ms": latency_ms,
                    "model": model_name,
                }
            )

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            latency_ms = round((time.time() - start_time) * 1000, 2)
            # Return graceful error metadata so frontend displays it cleanly
            return Message(
                role="agent",
                content=(
                    f"⚠️ **Gemini API Execution Notice:**\n\n"
                    f"Encountered an issue communicating with Gemini (`{str(e)}`).\n\n"
                    f"Please check your `GEMINI_API_KEY` and internet connectivity."
                ),
                metadata={
                    "agent_state": "error",
                    "agent_id": selected_agent.id,
                    "latency_ms": latency_ms,
                    "error_detail": str(e),
                }
            )

    # 2. DEMO / SIMULATION MODE (When GEMINI_API_KEY is not yet configured)
    latency_ms = round((time.time() - start_time) * 1000, 2)
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
        f"The frontend interactive features (edit, branch, rate, regenerate, copy, and tool calls) are fully active and connected to this endpoint."
    )

    return Message(
        role="agent",
        content=fallback_content,
        metadata={
            "agent_state": "completed",
            "agent_id": selected_agent.id,
            "agent_name": selected_agent.name,
            "tool_calls": demo_tools,
            "latency_ms": latency_ms,
            "mode": "demo_fallback",
        }
    )
