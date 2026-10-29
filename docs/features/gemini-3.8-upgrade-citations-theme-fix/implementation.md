# Implementation: Gemini 3.8 Upgrade, Perplexity Citations Display, Theme Dark Prose Fix & Chat Input Scrollbar Removal

- **Completed Date/Time**: 2026-10-29T08:15:00+05:30
- **Status**: Complete
- **Feature Slug**: `gemini-3.8-upgrade-citations-theme-fix`

---

## 1. Summary of Changes

### Gemini Model Upgrade
- **Root Cause**: Google Gemini API returned 404 NOT_FOUND because `models/gemini-2.5-flash` was deprecated and retired for users.
- **Backend Changes**:
  - `backend/app/agents/general_assistant/config.json`: Updated model to `gemini-3.8-flash`.
  - `backend/app/agents/base.py`: Updated `AgentConfig` and `AgentProfile` model defaults to `gemini-3.8-flash`.
  - `backend/app/workflows/models.py`: Updated `UserAgentProfile` model default to `gemini-3.8-flash`.
  - `backend/app/ai_generator.py`: Updated all Gemini model calls, fallback configurations, and prompts from `gemini-2.5-flash` to `gemini-3.8-flash`.
  - `backend/app/main.py`:
    - Added `normalize_model_name()` function to intercept deprecated models (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash` -> `gemini-3.8-flash`; `gemini-2.5-pro` -> `gemini-4-argon`).
    - Updated `ChatRequest` and `AgentTestRequest` schemas.
    - Updated chat routing, agent execution, and testing endpoints with normalization.
  - `backend/.env.example` and `README.md`: Updated default model to `gemini-3.8-flash`.
  - `backend/test_endpoints.py`: Updated tests to `gemini-3.8-flash` and added explicit verification for legacy `gemini-2.5-flash` auto-normalization.
- **Frontend Changes**:
  - `frontend/src/app/chat/components/ChatHeader.tsx`: Replaced 2.5 options with `gemini-3.8-flash` and `gemini-4-argon`.
  - `frontend/src/app/agents/components/AgentEditorModal.tsx`: Updated default and selection options to `gemini-3.8-flash` and `gemini-4-argon`.
  - `frontend/src/app/agents/components/AIAgentGeneratorModal.tsx`: Updated AI agent generator defaults and model dropdown.
  - `frontend/src/app/agents/components/AgentCard.tsx`: Updated badge label mapping for `gemini-3.8-flash` and `gemini-4-argon`.
  - `frontend/src/app/workflows/components/StepCardEditor.tsx`: Updated workflow step editor default and options.
  - `frontend/src/app/workflows/components/VisualGraphEditor.tsx`: Updated visual graph step editor default and options.
  - `frontend/src/app/agents/components/AgentPlaygroundModal.tsx` & `AgentDetailsModal.tsx`: Updated fallback model text.

### Theme Prose & Unreadable Dark Text Fix
- **Root Cause**: `@tailwindcss/typography` default styling sets `--tw-prose-bold`, `--tw-prose-headings`, `--tw-prose-quotes` to `#111827` (near-black), which renders unreadable on dark backgrounds (`#010102` canvas).
- **Frontend Changes**:
  - `frontend/tailwind.config.ts`: Configured `typography` theme extension with high-contrast variable bindings (`--tw-prose-bold: hsl(var(--foreground))`, `strong: { color: 'inherit', fontWeight: '600' }`).
  - `frontend/src/app/globals.css`: Added explicit system-wide root and palette definitions for `--tw-prose-bold: #f7f8f8`, `--tw-prose-headings: #f7f8f8`, with explicit `.prose strong`, `.prose b`, `.prose h1`...`h6` rules.
  - `frontend/src/app/chat/components/MessageItem.tsx`: Added `dark:prose-invert` and custom ReactMarkdown renderers for `strong`, `b`, `h1`, `h2`, `h3`, and `a` elements with crisp contrast.

### Perplexity Citations Display & Tool Result Cleanup
- **Root Cause**: Perplexity Sonar search citations were dumped as raw JSON string arrays inside the collapsed `tool_calls` accordion (`perplexity_live_search`), with no direct viewing or clickable access.
- **Backend Changes**:
  - `backend/app/main.py`: Attached `citations` to `agent_metadata["citations"]`, and updated `perplexity_live_search` tool call result to provide clean summary statistics (`sources_found`, `provider`, `status`) rather than duplicating the raw URL dump.
- **Frontend Changes**:
  - `frontend/src/app/chat/types.ts`: Added `citations?: string[]` to `MessageMetadata`.
  - `frontend/src/app/chat/components/MessageItem.tsx`:
    - Extracted citations from metadata (or tool call fallbacks).
    - Added dedicated "Sources & Citations" section above the tool calls accordion.
    - Each source card displays an index indicator `[1]`, `[2]`, clean host domain, truncated URL path, external link icon, full URL tooltip, and clickable external navigation (`target="_blank"`).
    - Cleaned up tool execution JSON view to note that citations are displayed in the Sources section.

### Chat Input Scrollbar Elimination
- **Root Cause**: Default browser `<textarea>` on Windows shows a vertical scrollbar track when `rows={1}` without explicit scrollbar-hiding utilities.
- **Frontend Changes**:
  - `frontend/src/app/globals.css`: Added cross-browser `.no-scrollbar` utility classes (`::-webkit-scrollbar { display: none }`, `-ms-overflow-style: none`, `scrollbar-width: none`).
  - `frontend/src/app/chat/components/ChatInput.tsx`: Added `overflow-y-auto no-scrollbar [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden` and inline styles to ensure the scrollbar is never visible while preserving smooth multi-line scrolling.

---

## 2. Changed Files

1. `backend/app/agents/general_assistant/config.json`
2. `backend/app/agents/base.py`
3. `backend/app/workflows/models.py`
4. `backend/app/ai_generator.py`
5. `backend/app/main.py`
6. `backend/.env.example`
7. `README.md`
8. `backend/test_endpoints.py`
9. `frontend/tailwind.config.ts`
10. `frontend/src/app/globals.css`
11. `frontend/src/app/chat/types.ts`
12. `frontend/src/app/chat/components/ChatInput.tsx`
13. `frontend/src/app/chat/components/ChatHeader.tsx`
14. `frontend/src/app/chat/components/MessageItem.tsx`
15. `frontend/src/app/chat/components/AgentDetailsModal.tsx`
16. `frontend/src/app/agents/components/AgentCard.tsx`
17. `frontend/src/app/agents/components/AgentEditorModal.tsx`
18. `frontend/src/app/agents/components/AgentPlaygroundModal.tsx`
19. `frontend/src/app/agents/components/AIAgentGeneratorModal.tsx`
20. `frontend/src/app/workflows/components/StepCardEditor.tsx`
21. `frontend/src/app/workflows/components/VisualGraphEditor.tsx`
