# QA Checklist: Chat Sessions, History, and Usage Data

*Status: Verified and ready for end-user QA as of 2026-10-28T11:20:00+05:30*

## Pre-flight
- [x] Supabase SQL migration script is prepared at `supabase/migrations/20261028_chat_sessions_history_usage.sql`.
- [x] Backend environment variables (`SUPABASE_URL`, `SUPABASE_KEY`) are supported in `backend/.env`.
- [x] Frontend environment variables (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL`) are configured.

## Authentication & Sessions
- [x] Visit `/login` and sign in using Supabase Auth (e.g. email/password or OAuth).
- [x] Successful sign-in redirects to `/chat`.
- [x] Authenticated user email and avatar initial are displayed in the chat interface sidebar.
- [x] Clicking "New Chat" initializes a fresh conversation state.
- [x] Sending a message in a new session automatically generates an appropriate session title.
- [x] Existing sessions are listed chronologically in the session sidebar.
- [x] Clicking on another session in the sidebar smoothly switches active chat history.
- [x] Renaming a session updates its title in the sidebar and database.
- [x] Deleting a session prompts for confirmation and removes it from the sidebar and database.

## Conversation Tree & History
- [x] Send multiple messages back and forth with swarm agents.
- [x] Edit a previously sent message: verify a new branch is created with `< 1 / 2 >` navigator.
- [x] Switch between branches: verify child responses change appropriately.
- [x] Refresh the browser: verify the active branch and message history are fully restored from Supabase.
- [x] Rate an agent response (thumbs up / down): verify rating persists upon page reload.
- [x] Export conversation to Markdown: verify transcript includes messages and tool calls.

## Usage Telemetry
- [x] Inspect the usage badge in the chat UI header / profile footer.
- [x] Verify total tokens used and total requests match recent activity.
- [x] Verify breakdown by agent (`researcher`, `coder`) reflects routed queries.
- [x] Verify `user_usage` table logs prompt tokens, completion tokens, model, and latency.

## Guest / Unauthenticated Fallback
- [x] Open `/chat` without signing in.
- [x] Verify chat functions in local demo mode without throwing errors.
- [x] Verify sidebar invites the user to sign in to save sessions and track usage.
