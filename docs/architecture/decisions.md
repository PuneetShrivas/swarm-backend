# Architecture Decision Records (ADRs)

*Last Updated: 2026-10-28T11:20:00+05:30*

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
