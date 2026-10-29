# Architecture Decision Records (ADRs)

*Last Updated: 2026-10-28T17:20:00+05:30*

## ADR 001: Supabase Schema for Chat Sessions, History, and Usage Tracking

### Status
Accepted (2026-10-28T11:20:00+05:30)

### Context
The application supports multi-agent conversations with advanced features such as inline editing, conversation branching (`< 1 / 2 >`), agent routing, tool call inspection, and ratings. Previously, conversations were purely in-memory in the React frontend, and no sessions or token usage were persisted. Supabase Auth is already implemented on `/login` and provides user sessions via `@supabase/supabase-js`.

We needed to persist chat sessions, conversation history, and usage metrics per authenticated user using Supabase tables, while maintaining full compatibility with the existing auth session and tree branching data model.

### Decisions

1. **Relational Database Design with Foreign Keys to `auth.users`**:
   - Created three dedicated tables: `chat_sessions`, `chat_messages`, and `user_usage`.
   - Each table has foreign key constraints referencing `auth.users(id) ON DELETE CASCADE`.
   - Applied PostgreSQL Row Level Security (RLS) on all three tables restricting access to `auth.uid() = user_id`.
   - *Parent Foreign Key Sanitization (Updated 2026-10-28T16:03:00+05:30)*: Root message nodes have `parent_id = NULL`. Client-side placeholders such as `'root-greeting'` or self-references are sanitized to `NULL`, and the backend queries existence before inserting to prevent `23503` foreign key violations. All inserts use `upsert` for idempotent delivery.

2. **Graph/Tree Structure in `chat_messages`**:
   - To natively support conversation tree branching and inline editing without data loss, `chat_messages` stores `parent_id TEXT NULL REFERENCES chat_messages(id)`.
   - Message IDs are stored as `TEXT PRIMARY KEY` to seamlessly accommodate client-side IDs (`root-greeting`, `msg-<timestamp>-<hash>`) or UUIDs.
   - Reconstructing the active path and sibling lists is performed mathematically from the adjacency list model via `reconstructTreeFromMessages`, ensuring full parity with the frontend's `ConversationState` and `ChatNode`.

3. **Decoupled Usage Tracking**:
   - Usage is recorded in an append-only `user_usage` table containing `prompt_tokens`, `completion_tokens`, `total_tokens`, `model`, `agent_id`, and `latency_ms`.
   - This keeps telemetry auditable and independent of message content or deletion, allowing accurate cumulative usage analytics over time.

4. **Dual Auth Layer (Frontend & Backend)**:
   - Frontend passes the existing Supabase session access token (`session.access_token`) via `Authorization: Bearer <token>` to FastAPI.
   - FastAPI verifies the token via Supabase Auth API (`supabase.auth.get_user(token)`).
   - If unauthenticated, the chat operates in a guest demo mode in local memory, preventing disruption for visitors while securing database operations for authenticated users.

### Consequences
- **Positive**: Clean data isolation per user with RLS; exact support for branching conversation trees; scalable telemetry; unified authentication.
- **Negative / Considerations**: Requires executing the migration script `supabase/migrations/20261028_chat_sessions_history_usage.sql` in the Supabase project dashboard SQL editor.

---

## ADR 002: Token-Based Theming System and Multi-Palette Architecture

### Status
Accepted (2026-10-28T16:47:00+05:30)

### Context
The application had fragmented, hardcoded color schemes (e.g. hardcoded `bg-slate-950` on landing, `bg-gray-50` on login, `bg-slate-50` on chat) with no theme toggle or dark mode support on the main workspace. A cohesive modern design system is required supporting light/dark/system mode alongside curated aesthetic themes.

### Decisions

1. **CSS Variable Design Tokens with Semantic Tailwind Mapping**:
   - Instead of hardcoding palette hex codes in utility classes, define CSS variables (`--background`, `--foreground`, `--card`, `--border`, `--primary`, `--accent`, `--muted`) in `globals.css` and map them in `tailwind.config.ts`.
   - Allows instant theme switches by updating attributes or classes on `<html>` or `<body>` without re-rendering component trees.

2. **Hierarchical Theming: Mode + Palette**:
   - **Mode (Light / Dark / System)**: Controls luminosity and contrast base.
   - **Palette (Slate / Nebula / Emerald / Amber / Frost)**: Controls the accent, glow, and tone tints.
   - Managed via a unified `ThemeProvider` integrating `next-themes` with palette persistence in `localStorage`.

3. **Zero-FOUC (Flash of Unstyled Content)**:
   - Next-themes executes an inline head script before initial paint to apply saved theme classes immediately upon page load.

4. **Supabase Auth UI Dynamic Theming**:
   - The login page synchronizes its `ThemeSupa` appearance config dynamically based on the active theme mode (`dark` vs `light`).

### Consequences
- **Positive**: Complete visual consistency across all views; rich user personalization; clean separation of styling concerns via design tokens; zero flash on page reload.
- **Negative / Considerations**: Refactored hardcoded color classes across existing components to use semantic token classes (`bg-background`, `border-border`, `text-foreground`, etc.).

---

## ADR 003: Filesystem-Based Modular Agent Architecture and Standardized Asset Structure

### Status
Accepted (2026-10-28T17:36:00+05:30)

### Context
Previously, agents were hardcoded Python dictionaries within `backend/app/main.py`. As the swarm expands to include specialized agents (orchestrator, researcher, coder, reviewer, data analyst, synthesizer) along with tools, skills, and Model Context Protocol (MCP) server configurations, maintaining monolithic lists in `main.py` causes tight coupling, hampers extensibility, and makes prompt engineering difficult to review.

### Decisions

1. **Standardized Directory Layout per Agent**:
   - Each agent resides in its own isolated subfolder under `backend/app/agents/<agent_id>/`.
   - Each agent folder contains 5 standardized asset files:
     - `config.json`: Metadata, model designation, temperature, icon, and operational status.
     - `prompt.md`: Isolated Markdown system prompt containing personas, formatting guidelines, and operational guardrails.
     - `tools.py`: Python callable functions and Gemini-compatible tool schema definitions.
     - `skills.json`: Declarative capability descriptions, triggers, and execution workflows.
     - `mcp.json`: Model Context Protocol server specifications (`stdio`/`sse`, commands, and exposed tool mappings).

2. **Autonomous Orchestrator as a First-Class Agent**:
   - The Orchestrator is refactored from a procedural if-else keyword branch into a dedicated agent package (`backend/app/agents/orchestrator/`).
   - The Orchestrator is equipped with swarm dispatch tools (`swarm_router`, `swarm_delegate`) and system prompt tuning enabling it to act as the cognitive hub of the swarm.

3. **Auto-Discovery via `AgentRegistry`**:
   - An `AgentRegistry` singleton scans `backend/app/agents/*/` at startup, dynamically parses asset files, instantiates `BaseAgent` objects, and exposes querying and reloading APIs.
   - External custom agents registered via `POST /api/agents` are stored in registry memory without overwriting filesystem assets.

4. **Backward-Compatible API Interface**:
   - `/api/agents` returns the established fields (`id`, `name`, `role`, `status`, `system_prompt`) ensuring existing clients do not break, while augmenting with optional fields (`tools`, `skills`, `mcp_servers`, `is_orchestrator`, `model`).
   - Added `/api/agents/{agent_id}` for granular inspection.

### Consequences
- **Positive**: Complete encapsulation; prompts can be version-controlled in plain Markdown; clear separation of tools and skills; native MCP readiness; zero breaking changes to existing endpoints.
- **Negative / Considerations**: Introduces file I/O on startup (cached in memory); requires synchronizing frontend types in a planned follow-up phase.

---

## ADR 006: Gemini 3.8 Model Migration, Perplexity Citations Architecture & Dark Theme Typography

### Status
Accepted (2026-10-29T08:15:00+05:30)

### Context
1. Google Gemini retired `gemini-2.5-flash` for new users, resulting in 404 NOT_FOUND errors during live API execution.
2. In dark mode, `@tailwindcss/typography` defaulted `--tw-prose-bold` and `--tw-prose-headings` to near-black (`#111827`), rendering bold text and headers unreadable on dark backgrounds.
3. Live Perplexity Sonar search citations were previously dumped into a raw JSON string array inside the tool executions accordion, making it hard to read and click sources.
4. Chat input box displayed an unwanted vertical scrollbar on Windows browsers.

### Decisions
1. **Model Upgrades & Backward-Compatible Normalization**:
   - Upgraded all backend agents, generators, schemas, and frontend selectors from `gemini-2.5-flash` to `gemini-3.8-flash`, and from `gemini-2.5-pro` to `gemini-4-argon`.
   - Introduced `normalize_model_name()` in FastAPI to transparently map legacy client requests or stored sessions from deprecated 2.5 models to active models.
2. **First-Class Citations Interface**:
   - Surfaced search citations directly through `agent_metadata["citations"]` in the backend.
   - Cleaned up `perplexity_live_search` tool execution output so raw URL string arrays do not clutter the tool debugging view.
   - Built a dedicated, accessible "Sources & Citations" section in the frontend displaying source index markers (`[1]`, `[2]`), clean domain hostnames, paths, external link icons, and secure tab openers.
3. **High-Contrast Dark Theme Typography**:
   - Extended Tailwind Typography theme configuration to bind `--tw-prose-bold` and prose colors to `hsl(var(--foreground))` and `#f7f8f8`.
   - Injected global CSS and ReactMarkdown component overrides guaranteeing crisp white bold styling across all theme palettes.
4. **Scrollbar-Free Auto-Expanding Textarea**:
   - Implemented `.no-scrollbar` utility classes and arbitrary Tailwind selectors (`[scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden`) on the chat input box.

### Consequences
- **Positive**: Eradicates Gemini 404 API errors; ensures zero breakage for existing conversations via auto-normalization; delivers high-contrast readability across all themes; transforms raw Perplexity citation dumps into an interactive sources UI; removes unsightly scrollbars.
- **Negative / Considerations**: Deprecated models will be automatically upgraded to 3.8 Flash, which exhibits superior speed and capabilities.
