# AGENTS.md — Agent Developer & Contributor Guide

Welcome! This document provides operational guidelines, architecture context, and coding conventions for autonomous AI agents and engineers working in this repository.

---

## 1. Project Overview

**Swarm Backend & Frontend** is a full-stack monorepo designed to build, manage, and orchestrate a swarm of specialized AI agents.

- **Backend:** A [FastAPI](https://fastapi.tiangolo.com/) application exposing RESTful APIs for agent registration, swarm orchestration, and conversational interactions with rich metadata (agent state, tool calls, token usage). Powered by the official [Google Gemini API](https://github.com/google-gemini/generative-ai-python) (`google-genai`).
- **Frontend:** A [Next.js](https://nextjs.org/) (v14, App Router) application providing a modern, responsive UI with tree-based branching, inline message editing, rating, regeneration, tool call disclosure, and swarm status dashboards.
- **Persistence & Auth:** Powered by [Supabase](https://supabase.com/) for authentication and database services.
- **Deployment Target:** Optimized for deployment on [Vercel](https://vercel.com/) (using `@vercel/python` for backend serverless functions and standard Next.js deployment for frontend).

---

## 2. Repository Layout

```plaintext
swarm-backend/
├── AGENTS.md                 # Agent instructions and repository manual (this file)
├── README.md                 # Project overview and quickstart guide
├── .gitignore                # Git ignore patterns for OS, Python, and Node
├── agent-instructions/
│   └── backend-review.md     # Backend specifications, schemas & persistence instructions
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── __init__.py       # Package marker
│   │   ├── main.py           # FastAPI routes, Gemini client, routing, and swarm models
│   │   └── supabase.py       # Supabase Python client configuration
│   ├── requirements.txt      # Python dependencies (fastapi, uvicorn, pydantic, supabase, google-genai)
│   ├── test_endpoints.py     # Automated endpoint integration tests
│   ├── .env.example          # Template for GEMINI_API_KEY and Supabase config
│   └── vercel.json           # Vercel deployment config for Python runtime
└── frontend/                 # Next.js Application
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx    # Root layout & global fonts
    │   │   ├── page.tsx      # Landing page with swarm introduction & CTA
    │   │   ├── chat/         # Swarm interactive chat interface
    │   │   │   ├── components/
    │   │   │   │   ├── MessageItem.tsx  # Message bubble, actions, tool calls & branch navigation
    │   │   │   │   ├── ChatInput.tsx    # Auto-resizing multi-line textarea
    │   │   │   │   └── ChatHeader.tsx   # Swarm indicator, agent selector & controls
    │   │   │   ├── types.ts             # Conversation tree structures and helper functions
    │   │   │   └── page.tsx             # Main chat page orchestrator
    │   │   ├── login/page.tsx# Authentication page powered by Supabase Auth UI
    │   │   └── globals.css   # Global Tailwind styles
    │   └── lib/
    │       └── supabase.ts   # Supabase JavaScript client initialization
    ├── package.json          # Node dependencies & run scripts
    ├── tsconfig.json         # TypeScript compiler configuration
    └── tailwind.config.ts    # Tailwind CSS configuration
```

---

## 3. Environment Setup & Local Development

### 3.1 Backend (FastAPI)

1. **Working Directory:** `cd backend`
2. **Virtual Environment:**
   - Linux/macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables (`backend/.env`):**
   ```env
   GEMINI_API_KEY="your-gemini-api-key"
   GEMINI_MODEL="gemini-2.5-flash"
   SUPABASE_URL="https://your-project.supabase.co"
   SUPABASE_KEY="your-anon-or-service-key"
   ```
5. **Run Integration Tests:**
   ```bash
   python test_endpoints.py
   ```
6. **Run Development Server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *Health endpoint:* `http://localhost:8000/api/health`  
   *Interactive Docs:* `http://localhost:8000/docs`

### 3.2 Frontend (Next.js)

1. **Working Directory:** `cd frontend`
2. **Install Dependencies:**
   ```bash
   pnpm install
   # or
   npm install
   ```
3. **Environment Variables (`frontend/.env.local`):**
   ```env
   NEXT_PUBLIC_API_URL="http://localhost:8000"
   NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
   NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"
   ```
4. **Run Development Server:**
   ```bash
   pnpm dev
   # or
   npm run dev
   ```
   *Frontend UI:* `http://localhost:3000/chat`

---

## 4. Architecture & Key Data Models

### 4.1 Backend Models (`backend/app/main.py`)

- **`Agent`**:
  - `id: str`: Unique identifier for the agent (e.g., `"researcher"`, `"coder"`).
  - `name: str`: Display name (e.g., `"Research Agent"`, `"Coder Agent"`).
  - `role: str`: Specialty or system purpose.
  - `status: str`: Operational state (`active`, `idle`, `busy`, `offline`).
  - `system_prompt: Optional[str]`: Agent persona and instructions passed to Gemini.

- **`ToolCall`**:
  - `tool: str`: Name of the executed tool.
  - `args: Optional[Dict[str, Any]]`: Input arguments.
  - `result: Optional[Any]`: Output payload.

- **`Message`**:
  - `role: str`: Sender role (`user`, `agent`, or `system`).
  - `content: str`: Markdown or text payload.
  - `metadata: Optional[Dict[str, Any]]`: Extensible metadata supporting `agent_state`, `agent_id`, `tool_calls`, `tokens_used`, `latency_ms`, etc.

- **`ChatRequest`**:
  - `messages: List[Message]`: Conversation history sent for swarm processing.

### 4.2 Frontend Architecture (`frontend/src/app/chat/`)

- **Tree-based State Management (`types.ts`)**:
  - Stores messages as an adjacency tree (`nodes: Record<string, ChatNode>`), where nodes have `parentId` and `childrenIds`.
  - Supports non-destructive branching (`< 1 / 2 >`), message version toggling, and rating state.
- **Message Feed (`MessageItem.tsx`)**:
  - Inline message editing for user turns.
  - Sibling branch switcher controls.
  - Thumbs up/down rating toggles.
  - Response regeneration and copy-to-clipboard.
  - Expandable swarm tool call disclosure.
- **Ergonomic Input (`ChatInput.tsx`)**:
  - Auto-resizing textarea up to 180px with `Enter` (send) and `Shift+Enter` (newline).
- **Controls & Header (`ChatHeader.tsx`)**:
  - Swarm status badge, target agent routing selector, Markdown transcript export, and chat clear dialog.

---

## 5. Agent Instructions & Development Guidelines

When modifying, extending, or fixing code in this repository, all AI agents MUST adhere to these conventions:

### 5.1 General Rules

1. **Minimal Disturbance:** Modify only relevant files. Do not rewrite unaffected modules or change code formatting arbitrarily.
2. **Preserve Documentation:** Retain existing comments, type definitions, and docstrings unless updating stale information.
3. **Security First:**
   - NEVER commit API keys, service role tokens, or sensitive credentials.
   - Use environment variables via `os.environ` (Python) and `process.env` (Next.js).
   - In production, restrict FastAPI CORS `allow_origins` instead of `["*"]`.
4. **Cross-Platform Compatibility:** Write path references and commands compatible with Windows, macOS, and Linux where feasible.

### 5.2 Backend Guidelines (Python / FastAPI)

1. **Type Annotations:** Annotate all function signatures, parameters, and return types explicitly.
2. **Pydantic Validation:** Always use Pydantic `BaseModel` for request payloads and response serialization.
3. **Gemini SDK Best Practices:** Use `google-genai` (>= 2.30.0). Re-specify system instructions and tool declarations per request when configuring content generation.
4. **Modularity:** Refer to [`agent-instructions/backend-review.md`](agent-instructions/backend-review.md) when extending the backend into routers, agent execution graphs, and database persistence.
5. **Error Handling:** Use `fastapi.HTTPException` with appropriate status codes (e.g., 400 for bad requests, 404 for missing agents, 500 for internal errors).

### 5.3 Frontend Guidelines (TypeScript / Next.js)

1. **Strict TypeScript:** Define types and interfaces for all state, props, and API responses. Avoid `any`.
2. **Client vs Server Components:** Keep pages server-rendered where feasible; isolate client state (`'use client'`) to interactive controls and chat feeds.
3. **Error & Loading States:** Always handle fetch failure gracefully with fallback UI states or error banners, and show loading spinners/indicators (`Loader2`) during async tasks.
4. **Environment Fallbacks:** Provide sensible local defaults when `process.env.NEXT_PUBLIC_*` variables are not defined.

---

## 6. Testing & Quality Verification

Before proposing or committing changes:

- **Frontend Build Check:**
  ```bash
  cd frontend
  pnpm build
  ```
- **Frontend Type Checking:**
  ```bash
  cd frontend
  npx tsc --noEmit
  ```
- **Backend Import & Syntax Verification:**
  ```bash
  cd backend
  python -m py_compile app/main.py app/supabase.py
  ```
- **Backend Integration Test:**
  ```bash
  cd backend
  python test_endpoints.py
  ```

---

## 7. Deployment Considerations (Vercel)

- `backend/vercel.json` configures `@vercel/python` routing. The entrypoint is `app/main.py`.
- In serverless environments, in-memory state (such as `agents_db = []`) resets between lambda cold starts. Persistent swarm state and conversation logs must be stored in Supabase or an external database as outlined in [`agent-instructions/backend-review.md`](agent-instructions/backend-review.md).
- Keep dependencies lean in `backend/requirements.txt` to minimize serverless cold starts.
