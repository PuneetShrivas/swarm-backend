# Feature Plan: Gemini 3.8 Upgrade, Perplexity Citations Display, Theme Dark Prose Fix & Chat Input Scrollbar Removal

- **Created Date/Time**: 2026-10-29T08:03:30+05:30
- **Status**: Complete
- **Feature Slug**: `gemini-3.8-upgrade-citations-theme-fix`

---

## 1. Goal
Address four core issues across the frontend and backend:
1. **Gemini Model Upgrade**: Resolve Google Gemini 404 NOT_FOUND error (`models/gemini-2.5-flash is no longer available to new users`) by migrating all backend and frontend model references from `gemini-2.5-flash` to `gemini-3.8-flash` (and Pro models to `gemini-4-argon`), adding automatic normalization for legacy requests so deprecated models are mapped automatically.
2. **Theme Prose Readability Fix**: Fix dark unreadable text in dark theme caused by `@tailwindcss/typography` default `--tw-prose-bold` / `--tw-prose-headings` values (`#111827` black on `#010102` black canvas), ensuring high-contrast readable styling across all themes and palettes.
3. **Perplexity Citations Display**: Gracefully surface search citations returned by Perplexity Sonar models as an interactive, accessible "Sources & Citations" section in the frontend rather than dumping raw JSON into the collapsed tool executions block.
4. **Chat Input Scrollbar Removal**: Eliminate the persistent vertical scrollbar visible in the chat input `<textarea>` across all browsers and operating systems.

---

## 2. Scope

### In Scope
- **Backend Model Updates**:
  - Update `general_assistant` agent config from `gemini-2.5-flash` to `gemini-3.8-flash`.
  - Update base agent model default in `backend/app/agents/base.py` to `gemini-3.8-flash`.
  - Update AI generator model fallback in `backend/app/ai_generator.py` to `gemini-3.8-flash`.
  - Update workflow models schema in `backend/app/workflows/models.py` to `gemini-3.8-flash`.
  - Add robust model normalization in `backend/app/main.py` (`normalize_model_name`) to map deprecated models (`gemini-2.5-flash` -> `gemini-3.8-flash`, `gemini-2.5-pro` -> `gemini-4-argon`) gracefully.
  - Update `.env.example` and `README.md`.
  - Update test fixtures and assertions in `backend/test_endpoints.py`.
- **Frontend Model Updates**:
  - Update `ChatHeader.tsx` model selector options to latest models (`gemini-3.8-flash`, `gemini-4-argon`, `sonar`, `sonar-pro`).
  - Update `AgentEditorModal.tsx` and `AIAgentGeneratorModal.tsx` dropdowns and defaults.
  - Update `AgentCard.tsx` model label badges.
  - Update `StepCardEditor.tsx` and `VisualGraphEditor.tsx` workflow step model dropdowns.
- **Theme Prose Fix**:
  - Configure `typography` in `frontend/tailwind.config.ts` mapping `--tw-prose-bold`, `--tw-prose-headings`, `--tw-prose-body`, etc. to `hsl(var(--foreground))` and high-contrast text.
  - Add explicit global CSS overrides in `frontend/src/app/globals.css` ensuring `--tw-prose-bold` and related properties remain high-contrast in dark mode and across custom palettes.
  - Update `MessageItem.tsx` markdown container with `dark:prose-invert`.
- **Perplexity Citations Display**:
  - Update `backend/app/main.py` Perplexity handler to ensure citations are stored in message metadata and clean up `perplexity_live_search` tool output.
  - Update `frontend/src/app/chat/types.ts` to include `citations?: string[]` in `MessageMetadata`.
  - Create a dedicated, accessible Citations component inside `MessageItem.tsx` displaying domain badges, link cards, favicon/domain indicators, index numbers `[1]`, `[2]`, and external link opening.
- **Chat Input Scrollbar Removal**:
  - In `frontend/src/app/chat/components/ChatInput.tsx`, add cross-browser scrollbar-hiding utility classes (`[scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden`).
  - Add `.no-scrollbar` styling in `frontend/src/app/globals.css`.

### Out of Scope
- Modifying authentication or Supabase database schema tables.
- Changing third-party LLM providers or adding non-Google/non-Perplexity APIs.

---

## 3. Files to Change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/agents/general_assistant/config.json` | Change model to `gemini-3.8-flash` | Migrate general assistant to latest active model |
| `backend/app/agents/base.py` | Change model default to `gemini-3.8-flash` | Ensure base agent schemas default to latest model |
| `backend/app/ai_generator.py` | Change model defaults to `gemini-3.8-flash` | Ensure workflow/agent generators use latest model |
| `backend/app/workflows/models.py` | Change model default to `gemini-3.8-flash` | Step schema default update |
| `backend/app/main.py` | Add `normalize_model_name`, update default models and Perplexity metadata | Support automatic model migration and clean citations |
| `backend/.env.example` | Update default model to `gemini-3.8-flash` | Keep configuration templates accurate |
| `README.md` | Update model references | Accurate onboarding docs |
| `backend/test_endpoints.py` | Update model assertions & add legacy normalization test | Validate model mapping & agent execution |
| `frontend/src/app/chat/components/ChatHeader.tsx` | Replace 2.5 models with 3.8 Flash & 4 Argon | Frontend model override selector update |
| `frontend/src/app/agents/components/AgentEditorModal.tsx` | Update model select options & defaults | Custom agent creation & edit |
| `frontend/src/app/agents/components/AIAgentGeneratorModal.tsx` | Update model select options & defaults | AI agent generation preview |
| `frontend/src/app/agents/components/AgentCard.tsx` | Update model display mapping | Human-readable model badge |
| `frontend/src/app/workflows/components/StepCardEditor.tsx` | Update step model options & defaults | Workflow step configuration |
| `frontend/src/app/workflows/components/VisualGraphEditor.tsx` | Update graph node model options & defaults | DAG visual step editor |
| `frontend/tailwind.config.ts` | Configure typography plugin for dark theme | Fix `--tw-prose-bold` and prose colors |
| `frontend/src/app/globals.css` | Add prose CSS variables & `.no-scrollbar` | System-wide high-contrast prose & scrollbar removal |
| `frontend/src/app/chat/components/ChatInput.tsx` | Add scrollbar-hiding classes to textarea | Remove vertical scrollbar |
| `frontend/src/app/chat/types.ts` | Add `citations?: string[]` to `MessageMetadata` | Strong TypeScript typing for citations |
| `frontend/src/app/chat/components/MessageItem.tsx` | Add Citations section & prose-invert | Gracefully display sources and render high-contrast markdown |
| `CHANGELOG.md` | Document changes | Maintain changelog integrity |

---

## 4. Verification Plan
- Unit & regression tests: Execute `backend/venv/Scripts/python backend/test_endpoints.py` ensuring all 33+ test suites pass.
- Frontend build & typecheck: Execute `npm --prefix frontend run build` verifying zero TypeScript or Tailwind compilation errors.
- Visual & manual verification of prose styles, citations component rendering, and input box scrollbar elimination.
