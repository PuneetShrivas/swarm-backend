-- ====================================================================
-- Migration: 20261028_chat_sessions_history_usage.sql
-- Description: Creates chat_sessions, chat_messages, and user_usage
--              tables with Row Level Security (RLS) tied to auth.users.
-- ====================================================================

-- 1. CHAT SESSIONS TABLE
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. CHAT MESSAGES TABLE (Supports tree branching via parent_id)
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id TEXT PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    parent_id TEXT REFERENCES public.chat_messages(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'agent', 'system')),
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    rating TEXT CHECK (rating IN ('up', 'down')),
    rating_comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. USER USAGE TELEMETRY TABLE
CREATE TABLE IF NOT EXISTS public.user_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES public.chat_sessions(id) ON DELETE SET NULL,
    message_id TEXT,
    model TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms NUMERIC(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ====================================================================
-- INDEXES
-- ====================================================================

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_updated
    ON public.chat_sessions(user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created
    ON public.chat_messages(session_id, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_user
    ON public.chat_messages(user_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_parent
    ON public.chat_messages(parent_id);

CREATE INDEX IF NOT EXISTS idx_user_usage_user_created
    ON public.user_usage(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_usage_session
    ON public.user_usage(session_id);

-- ====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ====================================================================

ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_usage ENABLE ROW LEVEL SECURITY;

-- chat_sessions policies
DROP POLICY IF EXISTS "Users can view their own sessions" ON public.chat_sessions;
CREATE POLICY "Users can view their own sessions"
    ON public.chat_sessions FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own sessions" ON public.chat_sessions;
CREATE POLICY "Users can insert their own sessions"
    ON public.chat_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own sessions" ON public.chat_sessions;
CREATE POLICY "Users can update their own sessions"
    ON public.chat_sessions FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own sessions" ON public.chat_sessions;
CREATE POLICY "Users can delete their own sessions"
    ON public.chat_sessions FOR DELETE
    USING (auth.uid() = user_id);

-- chat_messages policies
DROP POLICY IF EXISTS "Users can view their own messages" ON public.chat_messages;
CREATE POLICY "Users can view their own messages"
    ON public.chat_messages FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own messages" ON public.chat_messages;
CREATE POLICY "Users can insert their own messages"
    ON public.chat_messages FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own messages" ON public.chat_messages;
CREATE POLICY "Users can update their own messages"
    ON public.chat_messages FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own messages" ON public.chat_messages;
CREATE POLICY "Users can delete their own messages"
    ON public.chat_messages FOR DELETE
    USING (auth.uid() = user_id);

-- user_usage policies
DROP POLICY IF EXISTS "Users can view their own usage" ON public.user_usage;
CREATE POLICY "Users can view their own usage"
    ON public.user_usage FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own usage" ON public.user_usage;
CREATE POLICY "Users can insert their own usage"
    ON public.user_usage FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ====================================================================
-- TRIGGERS & FUNCTIONS
-- ====================================================================

-- Auto-update updated_at on chat_sessions updates
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_chat_sessions_updated_at ON public.chat_sessions;
CREATE TRIGGER set_chat_sessions_updated_at
    BEFORE UPDATE ON public.chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Bump session updated_at when a new message is inserted
CREATE OR REPLACE FUNCTION public.touch_session_on_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.chat_sessions
    SET updated_at = timezone('utc'::text, now())
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS bump_session_updated_at ON public.chat_messages;
CREATE TRIGGER bump_session_updated_at
    AFTER INSERT ON public.chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION public.touch_session_on_message();
