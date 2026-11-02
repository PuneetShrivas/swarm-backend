# Swarm Project Base

A modern, full-stack monorepo featuring a **FastAPI** backend powered by **Google Gemini API** (`google-genai`) and a **Next.js 14** (App Router) frontend. Built to deploy, manage, and orchestrate an autonomous swarm of specialized AI agents with a rich, interactive chat experience.

---

## 🚀 Key Features

### Frontend (Next.js 14 + Tailwind CSS + Framer Motion)
- **Workflow Studio & Visual Editor**:
  - **Live System Test Debugger & File Attachments**: Attach test files (PDF, XLSX, CSV, DOCX, TXT, MD, JSON) via local upload or from the workspace Artifact Studio directly into the system test modal. Watch live animated progress bars with active step tickers, stream real-time execution logs in the Debug Console, and deeply inspect rendered prompts, tool invocations, injected knowledge, and step outputs.
- **Interactive Chat Interface**:
  - **Judicious Step Resource Inspection**: Displays assigned step resources with role chips (`template`, `source`, `reference`) under individual execution step cards in collapsed and expanded views.
  - **Save Workflow Resource Persistence**: Seamlessly includes step-level resources and artifact references when persisting synthesized pipelines to the permanent workflow library via `SaveWorkflowModal.tsx`.
  - **Mid-Sentence `/workflow` Autocomplete & Pointing**: Type `/workflow` or `/wf` anywhere mid-sentence (e.g. `"follow the /workflow ABC and execute it for all attached files"`) to trigger a floating suggestions popover, insert `/workflow [Title]`, and render a persistent workflow pill badge.
  - **Batch Workflow Trace Carousel (`< File X of N >`)**: Interactively cycle through per-file runtime execution traces, tool calls, status pills, and outputs when executing a batch workflow across attached files.
  - **1-Click ZIP Artifact Download**: Instantly download compiled `.zip` archives bundling per-file outputs, JSON execution logs, and markdown summaries.
  - **Inline Message Editing**: Edit previous prompts in place with "Cancel" and "Save & Submit".
  - **Conversation Tree Branching (`< 1 / 2 >`)**: Seamlessly navigate alternative branches and responses without losing conversation history.
  - **Rating & Feedback**: Quick Thumbs Up 👍 / Thumbs Down 👎 toggles with visual accent states.
  - **Response Regeneration**: Re-query the swarm for alternative agent turns.
  - **One-Click Copy**: Copy message contents to clipboard with animated confirmation.
  - **Swarm Tool Calls Disclosure**: Collapsible monospace accordion inspecting tool names, arguments, and execution outputs.
  - **Ergonomic Multi-line Input**: Auto-resizing textarea with `Enter` (send) and `Shift+Enter` (newline) support.
  - **Chat Management**: Real-time agent status badge, target agent routing selector, Markdown transcript export, and session reset.

### Backend (FastAPI + Google Gemini API)
- **Real-Time Workflow Streaming Engine (`/run-stream`)**: Streams real-time Server-Sent Events (`text/event-stream`) during workflow DAG execution, emitting step lifecycle events (`pipeline_start`, `step_start`, `step_progress`, `step_completed`, `step_failed`, `pipeline_complete`), and ingesting test file attachments directly into step knowledge contexts.
- **Judicious Workflow Step Artifact Assignment**: Automatically classifies attached files (from device uploads or Artifact Studio) into `template`, `source`, and `reference`, maps them to matching steps (`writer` for templates, `data_analyst` for spreadsheets, `researcher` for reference docs), enriches step instructions with compliance rules, and injects step resources into `kb_text` at runtime.
- **Batch Multi-File Workflow Execution**: Automatically isolates and executes workflows $n$ times across all attached files upon detecting batch queries (e.g. `"execute it for all attached files"`).
- **In-Memory ZIP Package Compilation**: Bundles individual file outputs (`outputs/`), execution traces (`logs/`), and an aggregate summary table (`batch_execution_summary.md`) into a downloadable `.zip` artifact.
- **Mid-Sentence Workflow Resolution**: Resolves workflow references mid-sentence using bracketed (`/workflow [Title]`) and unbracketed syntax across Supabase, memory store, and preloaded defaults.
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

### [2026-11-02] System Test Process UI, Real-Time SSE Debugger, and Test File Attachments
- **Test File Attachments**: Added direct file upload (PDF, XLSX, CSV, DOCX, TXT, MD, JSON) and workspace Artifact Studio integration to `WorkflowSystemTestModal.tsx`, mapping test attachments into `WorkflowRunRequest.attached_artifacts` and auto-parsing them into step knowledge contexts.
- **Real-Time SSE Streaming Endpoint**: Implemented `POST /api/workflows/{workflow_id}/run-stream` in `backend/app/main.py` using FastAPI `StreamingResponse` (`text/event-stream`), streaming real-time pipeline events (`pipeline_start`, `step_start`, `step_completed`, `step_failed`, `pipeline_complete`).
- **Live Progress & Dynamic Step Sequence**: Added visual progress percentage bar, active step status ticker, elapsed time stopwatch counter, and dynamic interactive status chips (Pending, Running with spinning loader, Completed with latency/tokens, Failed).
- **Streaming Debug Console**: Added real-time auto-scrolling log terminal tab displaying timestamped execution telemetry, tool invocations, and output previews with quick-copy.
- **Deep Step Inspector**: Tabbed inspector allowing users to deeply audit any step's rendered prompt, injected knowledge/resources, tool calls with arguments/results, outputs, and diagnostic error traces.
- **Verification**: Created automated test suite `backend/test_system_test_debugger.py` (3/3 passed), verified regression test suites, and validated clean Next.js production build (`14/14 static pages generated`).

### [2026-11-02] Judicious Workflow Step Artifact Assignment & Resource Persistence
- **Judicious Artifact Classification**: Implemented `classify_artifact_purpose` in `backend/app/ai_generator.py` to identify whether attached files (from disk or Artifact Studio) serve as `template`, `source` data, or `reference` documentation based on filename heuristics and content cues.
- **Goal & Role-Aware Step Assignment**: Implemented `assign_artifacts_to_steps` to distribute classified artifacts to appropriate workflow steps (templates to writer/synthesizer, tabular datasets to data analyst/excel specialist, reference research to researcher/parser), prioritizing explicit prompt bindings when specific filenames are referenced.
- **Step Resource Schema & Execution Injection**: Extended `WorkflowStep` in `backend/app/workflows/models.py` with `resources: List[Dict[str, Any]]` and updated `WorkflowExecutionEngine.execute_single_step` in `backend/app/workflows/engine.py` to inject step resources into the agent's knowledge context (`kb_text`).
- **UI Trace Badges & Save Persistence**: Updated `GranularStepTrace.tsx` to display step resource counts and badges with role chips (`template`, `source`, `reference`), and updated `SaveWorkflowModal.tsx` to preview assigned step resources and preserve them in `POST /api/workflows` payloads.
- **Verification**: Created test suite `backend/test_workflow_step_resource_assignment.py` (5/5 passed), confirmed regression test pass across batch workflows and intent orchestration, and validated clean Next.js production build.

### [2026-11-02] Batch Workflow Execution, Mid-Sentence Autocomplete, and Zip Output
- **Mid-Sentence Autocomplete & Pointing**: Enhanced `ChatInput.tsx` to detect `/workflow` or `/wf` typed mid-sentence, open an inline floating suggestions popover, insert `/workflow [Title]`, and render a removable target workflow badge pill.
- **Batch Multi-File Execution Engine**: Enhanced `_execute_chat_turn` in `backend/app/main.py` to identify batch execution intent across attached files, isolate inputs per file, and execute the referenced pipeline $n$ times with granular telemetry.
- **In-Memory ZIP Package Compilation**: Automatically compiles per-file outputs (`outputs/`), execution traces (`logs/`), and an aggregate summary table (`batch_execution_summary.md`) into a downloadable base64 `.zip` file artifact.
- **Interactive File Trace Carousel**: Added `<` and `>` carousel controls in `MessageItem.tsx` enabling users to navigate between files (`File X of N`), inspecting per-file execution status, duration, tokens, tool calls, and outputs.
- **Automated Verification**: Created comprehensive test suite in `backend/test_batch_workflow_execution.py` verifying mid-sentence regex extraction, workflow resolution, multi-file batch execution, and ZIP archive validation. 100% test pass and frontend production build pass.

### [2026-10-28] Supabase Chat Sessions, History, and Usage Telemetry
- **Database**: Created SQL migration `supabase/migrations/20261028_chat_sessions_history_usage.sql` establishing `chat_sessions`, `chat_messages` (with adjacency-list tree branching), and `user_usage` tables with complete RLS policies and performance indexes.
- **Backend API**: Added FastAPI endpoints for session CRUD (`GET`, `POST`, `PATCH`, `DELETE /api/sessions`) and usage aggregation (`GET /api/usage`).
- **Auth Integration**: Created `backend/app/auth.py` verifying Supabase access tokens via `Authorization: Bearer <token>` while retaining guest mode demo fallback.
- **Frontend UI**: Integrated conversation sidebar with session switching, title editing, session deletion, token telemetry modal (`UsageModal`), user profile footer, and dynamic tree state hydration (`reconstructTreeFromMessages`).
- **Automated Verification**: Added 13-stage test suite in `backend/test_endpoints.py` verifying all endpoints, sessions, message persistence, and token telemetry. Full pass on frontend linter and production build.
