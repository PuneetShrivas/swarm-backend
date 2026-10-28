# Architecture Decision Records (ADRs)

*Last Updated: 2026-10-28T16:30:00+05:30*

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
Proposed (Pending Approval: 2026-10-28T16:30:00+05:30)

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
- **Negative / Considerations**: Requires refactoring hardcoded color classes across existing components to use semantic token classes (`bg-background`, `border-border`, `text-foreground`, etc.).
