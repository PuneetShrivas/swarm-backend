# Backend Review & Agent Compatibility Guide

> **Target Audience:** Autonomous AI agents and backend engineers implementing or updating the FastAPI backend in `backend/app/`.
> **Scope:** Defines API contracts, data models, swarm routing, metadata specifications, tool execution protocols, and database persistence required for seamless interoperability with the Next.js frontend chat interface.

---

## 1. Architecture Overview & Role of FastAPI

The backend is an asynchronous [FastAPI](https://fastapi.tiangolo.com/) service designed to orchestrate specialized AI agents in a swarm architecture.

- **Source Code Entrypoint:** `backend/app/main.py`
- **Supabase Client:** `backend/app/supabase.py`
- **Serverless Configuration:** `backend/vercel.json` (configured via `@vercel/python`)
- **Interactive OpenAPI Documentation:** Available locally at `http://localhost:8000/docs`

---

## 2. API Contracts & Compatibility Specifications

The frontend (`frontend/src/app/chat/`) interacts directly with the following FastAPI endpoints:

### 2.1 Agent Roster Endpoint
- **Method & Path:** `GET /api/agents`
- **Response Format:** `List[Agent]`
- **Model Definition:**
  ```python
  class Agent(BaseModel):
      id: str               # e.g., "coder-01", "researcher-02"
      name: str             # e.g., "Code Specialist", "Research Analyst"
      role: str             # e.g., "Writes and refactors code", "Web research"
      status: str           # "active" | "busy" | "idle" | "offline"
  ```
- **Frontend Usage:** Populates the "Active Swarm" sidebar roster and target agent dropdown selector in the chat header.

### 2.2 Agent Creation Endpoint
- **Method & Path:** `POST /api/agents`
- **Request Body:** `Agent`
- **Response Format:** `Agent`
- **Behavior:** Registers a new specialized agent into the swarm.

### 2.3 Swarm Chat Endpoint
- **Method & Path:** `POST /api/chat`
- **Request Body:** `ChatRequest`
  ```python
  class Message(BaseModel):
      role: str                                    # "user" | "agent" | "system"
      content: str                                 # Markdown or plain text
      metadata: Optional[Dict[str, Any]] = None    # Extensible metadata dictionary

  class ChatRequest(BaseModel):
      messages: List[Message]
  ```
- **Response Format:** `Message` (representing the agent's turn).

---

## 3. Rich Metadata Specification (`metadata` dictionary)

The frontend chat interface is built to render rich execution state from the backend. The FastAPI service should populate the `metadata` dictionary with the following standard keys:

### 3.1 `agent_state` (string)
- **Allowed Values:** `"active"`, `"reasoning"`, `"executing"`, `"completed"`, `"idle"`, `"error"`
- **Frontend Behavior:** Renders an animated status indicator with the state label beneath the message bubble.

### 3.2 `tool_calls` (list of objects)
When an agent invokes tools (e.g., search, shell, Python sandbox, API queries), return them in `metadata["tool_calls"]`:
```python
"tool_calls": [
    {
        "tool": "web_search",
        "args": {
            "query": "FastAPI agents with Supabase"
        },
        "result": {
            "status": "success",
            "matches": 5
        }
    },
    {
        "tool": "python_eval",
        "args": {
            "code": "sum([1, 2, 3, 4, 5])"
        },
        "result": 15
    }
]
```
- **Frontend Behavior:** Automatically renders an interactive, collapsible disclosure ("Swarm Tools Executed (N)") showing the tool name, arguments, and result formatted in clean monospace.

### 3.3 `agent_id` (string)
- **Example:** `"coder-agent"`, `"orchestrator"`
- **Frontend Behavior:** Displays which agent in the swarm formulated the response (`"via coder-agent"`).

### 3.4 Target Agent Routing (`target_agent_id`)
- When the user selects a specific agent in the frontend dropdown, the user's message will contain:
  ```python
  metadata: {
      "target_agent_id": "agent-id-selected-by-user"
  }
  ```
- **Backend Implementation Guideline:** Check `request.messages[-1].metadata.get("target_agent_id")` and dispatch the task to that specific agent rather than default swarm broadcast.

---

## 4. Conversation Tree & Branching Mechanics

The frontend uses an **Adjacency Tree model** (`ChatNode` with `id`, `parentId`, and `childrenIds`).
- When a user **edits** a prompt or **regenerates** a response, a new branch is formed.
- The frontend extracts the active path (from the chosen leaf back to root) and sends the clean, linear `messages: Message[]` history to `POST /api/chat`.
- **Backend Benefit:** The backend never needs to worry about managing tree branches unless you persist full tree state in Supabase.

---

## 5. Supabase Database Persistence Guidelines

In serverless Vercel environments, in-memory storage (`agents_db = []`) resets on cold starts. When implementing database persistence with Supabase (`backend/app/supabase.py`), use the following schema design:

### 5.1 Tables Schema Recommendation

```sql
-- 1. Agents Table
CREATE TABLE public.agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    system_prompt TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Conversations Table
CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Messages Table (Adjacency Tree Structure)
CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES public.messages(id) ON DELETE SET NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'agent', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    rating TEXT CHECK (rating IN ('up', 'down', NULL)),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.2 Ratings & Feedback Persistence
- When adding a route for rating:
  ```python
  @app.post("/api/messages/{message_id}/rate")
  async def rate_message(message_id: str, payload: RateRequest):
      # Update rating ('up', 'down', null) in Supabase public.messages
      ...
  ```

---

## 6. Recommended Streaming Architecture (SSE)

For real-time token streaming and progressive tool call updates:
1. **Endpoint:** `POST /api/chat/stream`
2. **Response:** `StreamingResponse(event_generator(), media_type="text/event-stream")`
3. **Event Payloads:**
   - `event: token` -> `data: {"delta": "..."}`
   - `event: tool_call` -> `data: {"tool": "...", "status": "running"}`
   - `event: metadata` -> `data: {"agent_state": "completed", ...}`
   - `event: done` -> `data: "[DONE]"`

---

## 7. Security & Production Checklist

1. **CORS:** In `backend/app/main.py`, replace `allow_origins=["*"]` with explicit domain names in production (e.g., `["https://your-domain.vercel.app"]`).
2. **Authentication:** Extract JWT from incoming `Authorization: Bearer <token>` and verify with `supabase.auth.get_user(token)`.
3. **Validation & Errors:** Raise standard `fastapi.HTTPException` with status codes (`400` for invalid schemas, `404` for missing agent, `500` for orchestration failures).
4. **Environment Variables:** Keep `SUPABASE_URL` and `SUPABASE_KEY` configured in `backend/.env` and Vercel project settings.
