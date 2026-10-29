# Swarm Project Base

A modern, full-stack monorepo featuring a **FastAPI** backend powered by **Google Gemini API** (`google-genai`) and a **Next.js 14** (App Router) frontend. Built to deploy, manage, and orchestrate an autonomous swarm of specialized AI agents with a rich, interactive chat experience.

---

## 🚀 Key Features

### Frontend (Next.js 14 + Tailwind CSS + Framer Motion)
- **Interactive Chat Interface**:
  - **Inline Message Editing**: Edit previous prompts in place with "Cancel" and "Save & Submit".
  - **Conversation Tree Branching (`< 1 / 2 >`)**: Seamlessly navigate alternative branches and responses without losing conversation history.
  - **Rating & Feedback**: Quick Thumbs Up 👍 / Thumbs Down 👎 toggles with visual accent states.
  - **Response Regeneration**: Re-query the swarm for alternative agent turns.
  - **One-Click Copy**: Copy message contents to clipboard with animated confirmation.
  - **Swarm Tool Calls Disclosure**: Collapsible monospace accordion inspecting tool names, arguments, and execution outputs.
  - **Ergonomic Multi-line Input**: Auto-resizing textarea with `Enter` (send) and `Shift+Enter` (newline) support.
  - **Chat Management**: Real-time agent status badge, target agent routing selector, Markdown transcript export, and session reset.

### Backend (FastAPI + Google Gemini API)
- **Google Gemini Integration**: Uses the official `google-genai` SDK for multi-turn conversational intelligence, agent-specific system instructions, and token usage tracking.
- **Pre-populated Swarm Agents**:
  - `researcher` (**Research Agent**): In-depth analytical investigation, structured syntheses, and factual reporting.
  - `coder` (**Coder Agent**): Expert software engineering, clean code generation, debugging, and type safety.
- **Dynamic Swarm Routing**: Automatically routes queries based on prompt intent (e.g. coding queries route to `coder`, analytical inquiries to `researcher`), or honors explicit target agent selection from the frontend.
- **Graceful Demonstration Fallback**: Operates out-of-the-box with simulated tool calls and setup guidance if `GEMINI_API_KEY` is not yet configured.
- **Agent Instructions Guide**: Dedicated architectural blueprint in [`agent-instructions/backend-review.md`](agent-instructions/backend-review.md).

---

## 📁 Repository Structure

```plaintext
swarm-backend/
├── agent-instructions/
│   └── backend-review.md     # Architecture & compatibility guide for backend agents
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── main.py           # FastAPI routes, Gemini client, routing, and swarm models
│   │   └── supabase.py       # Supabase client configuration
│   ├── requirements.txt      # Python dependencies (fastapi, google-genai, etc.)
│   ├── test_endpoints.py     # Automated endpoint integration tests
│   ├── .env.example          # Environment variables template
│   └── vercel.json           # Vercel deployment configuration
└── frontend/                 # Next.js 14 Application
    ├── src/
    │   ├── app/
    │   │   ├── chat/         # Rich chat interface & page orchestrator
    │   │   │   ├── components/
    │   │   │   │   ├── MessageItem.tsx  # Message bubble, actions, tools & branch switcher
    │   │   │   │   ├── ChatInput.tsx    # Ergonomic auto-resizing input
    │   │   │   │   └── ChatHeader.tsx   # Swarm indicator, agent selector & controls
    │   │   │   ├── types.ts             # Conversation tree data structures & utilities
    │   │   │   └── page.tsx             # Interactive chat page
    │   │   ├── login/page.tsx           # Supabase Auth UI page
    │   │   └── page.tsx                 # Landing page
    └── package.json          # Node dependencies (pnpm / npm)
```

---

## 🛠️ Getting Started Locally

### 1. Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables (`backend/.env`):
   ```env
   # Add your Google Gemini API key (from https://aistudio.google.com/)
   GEMINI_API_KEY="your-gemini-api-key"
   GEMINI_MODEL="gemini-3.8-flash"
   ```

5. Run endpoint integration tests:
   ```bash
   python test_endpoints.py
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *Health check:* `http://localhost:8000/api/health`  
   *API documentation:* `http://localhost:8000/docs`

---

### 2. Frontend (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   pnpm install
   # or
   npm install
   ```

3. Configure environment variables (`frontend/.env.local`):
   ```env
   NEXT_PUBLIC_API_URL="http://localhost:8000"
   ```

4. Run the development server:
   ```bash
   pnpm dev
   # or
   npm run dev
   ```
   Open **`http://localhost:3000/chat`** in your browser.

---

## 🧪 Testing

- **Backend Integration Tests:**
  ```bash
  cd backend
  python test_endpoints.py
  ```
- **Frontend Type Checking:**
  ```bash
  cd frontend
  npx tsc --noEmit
  ```
- **Frontend Production Build:**
  ```bash
  cd frontend
  pnpm build
  ```

---

## 🚢 Deployment to Vercel

Configured for serverless deployment on Vercel:
- **Backend:** `backend/vercel.json` deploys `backend/app/main.py` via `@vercel/python`.
- **Frontend:** Standard Next.js serverless build.
- **State Note:** Persistent swarm state, conversation trees, and usage telemetry are stored in Supabase tables (`chat_sessions`, `chat_messages`, `user_usage`) protected with Row Level Security (RLS). Apply the migration script in `supabase/migrations/20261028_chat_sessions_history_usage.sql`.

---

## 📝 Changelog

### [2026-10-28] Supabase Chat Sessions, History, and Usage Telemetry
- **Database**: Created SQL migration `supabase/migrations/20261028_chat_sessions_history_usage.sql` establishing `chat_sessions`, `chat_messages` (with adjacency-list tree branching), and `user_usage` tables with complete RLS policies and performance indexes.
- **Backend API**: Added FastAPI endpoints for session CRUD (`GET`, `POST`, `PATCH`, `DELETE /api/sessions`) and usage aggregation (`GET /api/usage`).
- **Auth Integration**: Created `backend/app/auth.py` verifying Supabase access tokens via `Authorization: Bearer <token>` while retaining guest mode demo fallback.
- **Frontend UI**: Integrated conversation sidebar with session switching, title editing, session deletion, token telemetry modal (`UsageModal`), user profile footer, and dynamic tree state hydration (`reconstructTreeFromMessages`).
- **Automated Verification**: Added 13-stage test suite in `backend/test_endpoints.py` verifying all endpoints, sessions, message persistence, and token telemetry. Full pass on frontend linter and production build.
