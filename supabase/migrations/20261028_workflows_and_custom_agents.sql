-- ====================================================================
-- Migration: 20261028_workflows_and_custom_agents.sql
-- Description: Creates user_agents, workflow_tools, workflows,
--              workflow_knowledge_files, workflow_runs, and
--              workflow_step_runs tables with RLS policies tied to auth.users.
-- ====================================================================

-- 1. USER CUSTOM AGENTS TABLE
CREATE TABLE IF NOT EXISTS public.user_agents (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Specialist',
    description TEXT NOT NULL DEFAULT '',
    system_prompt TEXT NOT NULL,
    model TEXT NOT NULL DEFAULT 'gemini-2.5-flash',
    temperature NUMERIC(3, 2) NOT NULL DEFAULT 0.3,
    icon TEXT NOT NULL DEFAULT 'Bot',
    tools JSONB NOT NULL DEFAULT '[]'::jsonb,
    skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_public BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. WORKFLOW SCRIPT TOOLS TABLE
CREATE TABLE IF NOT EXISTS public.workflow_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    code TEXT NOT NULL,
    input_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_public BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. WORKFLOWS TABLE
CREATE TABLE IF NOT EXISTS public.workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    goal TEXT NOT NULL,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    edges JSONB NOT NULL DEFAULT '[]'::jsonb,
    visibility TEXT NOT NULL DEFAULT 'private' CHECK (visibility IN ('private', 'shared', 'public')),
    share_slug TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 4. WORKFLOW KNOWLEDGE FILES TABLE
CREATE TABLE IF NOT EXISTS public.workflow_knowledge_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES public.workflows(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL DEFAULT 'text/plain',
    file_size INTEGER NOT NULL DEFAULT 0,
    content_text TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 5. WORKFLOW RUNS TABLE
CREATE TABLE IF NOT EXISTS public.workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES public.workflows(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES public.chat_sessions(id) ON DELETE SET NULL,
    trigger_type TEXT NOT NULL DEFAULT 'manual' CHECK (trigger_type IN ('manual', 'unit_test', 'system_test', 'chat')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    input_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    duration_ms NUMERIC(10, 2),
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ
);

-- 6. WORKFLOW STEP RUNS TABLE
CREATE TABLE IF NOT EXISTS public.workflow_step_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES public.workflow_runs(id) ON DELETE CASCADE,
    step_id TEXT NOT NULL,
    step_index INTEGER NOT NULL DEFAULT 0,
    agent_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    prompt_rendered TEXT,
    input_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    tool_calls JSONB NOT NULL DEFAULT '[]'::jsonb,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    duration_ms NUMERIC(10, 2),
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ
);

-- ====================================================================
-- INDEXES
-- ====================================================================

CREATE INDEX IF NOT EXISTS idx_user_agents_user
    ON public.user_agents(user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_workflow_tools_user
    ON public.workflow_tools(user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_workflows_user_updated
    ON public.workflows(user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_workflows_share_slug
    ON public.workflows(share_slug);

CREATE INDEX IF NOT EXISTS idx_workflow_knowledge_workflow
    ON public.workflow_knowledge_files(workflow_id);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow
    ON public.workflow_runs(workflow_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_user
    ON public.workflow_runs(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_session
    ON public.workflow_runs(session_id);

CREATE INDEX IF NOT EXISTS idx_workflow_step_runs_run
    ON public.workflow_step_runs(run_id, step_index ASC);

-- ====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ====================================================================

ALTER TABLE public.user_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_knowledge_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_step_runs ENABLE ROW LEVEL SECURITY;

-- 1. USER AGENTS POLICIES
CREATE POLICY user_agents_owner_all ON public.user_agents
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY user_agents_public_select ON public.user_agents
    FOR SELECT USING (is_public = true);

-- 2. WORKFLOW TOOLS POLICIES
CREATE POLICY workflow_tools_owner_all ON public.workflow_tools
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY workflow_tools_public_select ON public.workflow_tools
    FOR SELECT USING (is_public = true);

-- 3. WORKFLOWS POLICIES
CREATE POLICY workflows_owner_all ON public.workflows
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY workflows_shared_select ON public.workflows
    FOR SELECT USING (visibility IN ('shared', 'public'));

-- 4. KNOWLEDGE FILES POLICIES
CREATE POLICY workflow_knowledge_owner_all ON public.workflow_knowledge_files
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY workflow_knowledge_shared_select ON public.workflow_knowledge_files
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.workflows w
            WHERE w.id = workflow_id AND w.visibility IN ('shared', 'public')
        )
    );

-- 5. WORKFLOW RUNS POLICIES
CREATE POLICY workflow_runs_owner_all ON public.workflow_runs
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 6. WORKFLOW STEP RUNS POLICIES
CREATE POLICY workflow_step_runs_owner_all ON public.workflow_step_runs
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.workflow_runs r
            WHERE r.id = run_id AND r.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.workflow_runs r
            WHERE r.id = run_id AND r.user_id = auth.uid()
        )
    );
