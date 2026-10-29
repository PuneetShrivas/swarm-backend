# Feature: AI Mode for Autonomous Workflow Construction

- **Date/Time**: 2026-10-29T12:22:00+05:30
- **Feature Slug**: `ai-mode-workflow-generation`

## Status

Complete (Implemented & Verified 2026-10-29T12:35:50+05:30)

## Goal

Provide a first-class AI mode for automatically constructing, reviewing, refining, and launching autonomous multi-agent workflows and DAG pipelines from natural language prompts, establishing complete feature parity with the AI Agent Architect on the `/agents` page.

## Scope

- In scope:
  - Frontend `AIWorkflowGeneratorModal` component (`frontend/src/app/workflows/components/AIWorkflowGeneratorModal.tsx`) matching the high-craft Linear design of `AIAgentGeneratorModal.tsx`.
  - Integration on the Workflows Dashboard (`frontend/src/app/workflows/page.tsx`):
    - "AI Workflow Architect" action button in the top navigation header with `Sparkles` icon.
    - AI mode shortcut inside the existing manual Create Workflow modal.
    - AI architect callout in empty and zero-search states.
  - Integration within the Workflow Studio Canvas (`frontend/src/app/workflows/[id]/page.tsx`):
    - "AI Architect" header action enabling users to synthesize or expand DAG pipelines from natural language directly from within an existing workflow canvas.
  - Interactive Review & Refinement Deck:
    - Editable pipeline metadata: Title, Goal, Description.
    - Step-by-step DAG breakdown displaying step types (`agent`, `condition`, `python_code`, `loop`, `artifact`), assigned agents, prompt instructions, and dependencies.
    - Visual DAG sequence flow preview chips.
    - One-click "Create & Open Studio" that persists the workflow via `POST /api/workflows` and redirects directly to the interactive DAG canvas.
  - Backend AI generation enhancements (`backend/app/ai_generator.py`):
    - Upgrade workflow generation system prompt to support multi-block types (`condition`, `python_code`, `loop`, `artifact`) and dynamic model assignment (`gemini-3.8-flash`).
    - Expand deterministic fallback generator with diverse domain archetypes (Security Audit, Data Analytics, Code Review & Refactor, Document Synthesis).
  - Automated testing:
    - Backend test suite coverage for AI workflow generation with specialized block types and DAG integrity.
- Out of scope:
  - Database schema changes (the existing `workflows` table and JSON structures in Supabase natively support arbitrary step types and DAG edges).
  - External non-Gemini workflow synthesizer services.

## Current behavior

1. On the Workflows page (`frontend/src/app/workflows/page.tsx`), users can only click a manual "New Workflow" button, which opens a minimal modal requiring manual entry of Title and Goal, and creates a static 2-step stub (`step_1: researcher`, `step_2: synthesizer`).
2. Although a backend endpoint `POST /api/ai/generate-workflow` exists in `backend/app/main.py`, there is zero frontend UI connecting users to this capability.
3. In contrast, the `/agents` page provides a dedicated `AIAgentGeneratorModal` (`<Sparkles /> AI Agent Generator`) that takes natural language, calls `POST /api/ai/generate-agent`, renders an interactive "Review & Refine" preview, allows testing in the playground, and saves directly to the user's roster.
4. Users cannot auto-construct rich workflows, pipelines with condition/loop blocks, or multi-agent orchestrations with AI.

## Proposed behavior

1. **AI Workflow Architect Entry Points**:
   - On `/workflows`, a prominent `AI Workflow Architect` button (`<Sparkles />`) is available in the top header next to `New Workflow`.
   - The manual Create Modal contains a quick switch: "✨ Or generate entire pipeline with AI mode".
   - On `/workflows/[id]` (the Studio canvas), an `AI Architect` toolbar button allows users to generate or replace workflow DAGs with AI prompts.
2. **Interactive AI Generation Experience (`AIWorkflowGeneratorModal`)**:
   - Curated inspiration presets (Security Audit Pipeline, Competitor Market Research DAG, FinTech Analytics Engine, Code Quality & Refactor).
   - Natural language prompt textarea.
   - Live generation state with spinning indicator ("Architecting Workflow DAG...").
   - Review & Refine Deck displaying:
     - Editable Title, Description, and Goal.
     - Visual flow sequence (`Step 1 [researcher] ──► Step 2 [coder] ──► Step 3 [artifact]`).
     - Interactive step cards showing step type badges (`agent`, `condition`, `python_code`, `loop`, `artifact`), assigned agent avatar, prompt template, and dependencies.
     - Inline editability for step titles and instructions before saving.
   - "Create & Open Studio" button:
     - Saves the constructed DAG via `POST /api/workflows`.
     - Immediately redirects to `/workflows/[id]` with the full visual graph rendered on the React Flow canvas.
3. **Backend Multi-Block Synthesis**:
   - `backend/app/ai_generator.py` instructs Gemini 3.8 Flash to emit valid multi-block types (`condition`, `python_code`, `loop`, `artifact`) when described in user prompts, and provides fallback templates with rich blocks.

## Implementation steps

1. **Backend Generator Enhancement (`backend/app/ai_generator.py`)**:
   - Enhance `generate_workflow_spec` system instruction to support advanced step types (`agent`, `condition`, `python_code`, `loop`, `artifact`).
   - Add rich archetype fallbacks with conditions and artifacts.
2. **Frontend AI Modal Component (`AIWorkflowGeneratorModal.tsx`)**:
   - Create `frontend/src/app/workflows/components/AIWorkflowGeneratorModal.tsx` following `AIAgentGeneratorModal.tsx` design patterns.
   - Include prompt presets, generation spinner, step inspection cards, visual DAG flow pills, and save/open logic.
3. **Workflows Dashboard Integration (`frontend/src/app/workflows/page.tsx`)**:
   - Add `AI Workflow Architect` button to header.
   - Add AI toggle to manual Create Modal.
   - Render `AIWorkflowGeneratorModal` with router navigation on save.
4. **Workflow Studio Integration (`frontend/src/app/workflows/[id]/page.tsx`)**:
   - Add `AI Architect` button to studio header to allow AI-assisted DAG updates.
5. **Testing & Verification**:
   - Update `backend/test_endpoints.py` to verify workflow generation with complex prompts.
   - Run full backend test suite (`python test_endpoints.py`).
   - Run Next.js production build (`npm run build`).

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `backend/app/ai_generator.py` | Enhance `generate_workflow_spec` prompt & fallbacks | Support rich multi-block DAG generation with Gemini 3.8 |
| `backend/test_endpoints.py` | Add test cases for AI workflow generation with block types | Automated regression verification |
| `frontend/src/app/workflows/components/AIWorkflowGeneratorModal.tsx` | New component | Core AI workflow generation modal with review/refine UI |
| `frontend/src/app/workflows/page.tsx` | Add AI mode trigger buttons & modal integration | Dashboard entry points for AI mode |
| `frontend/src/app/workflows/[id]/page.tsx` | Add AI Architect trigger button to studio toolbar | Studio canvas AI mode entry point |

## Interfaces

### 1. `POST /api/ai/generate-workflow` Request & Response
```typescript
// Request
interface AIGenerateWorkflowRequest {
  prompt: string;
}

// Response
interface GeneratedWorkflowSpec {
  title: string;
  description: string;
  goal: string;
  steps: Array<{
    id: string;
    name: string;
    step_type?: "agent" | "condition" | "python_code" | "loop" | "artifact";
    agent_id?: string;
    instructions?: string;
    code?: string;
    condition_expr?: string;
    true_target_step_id?: string;
    false_target_step_id?: string;
    loop_target_step_id?: string;
    max_loop_iterations?: number;
    artifact_title?: string;
    artifact_type?: string;
    tool_ids?: string[];
    knowledge_file_ids?: string[];
    depends_on?: string[];
  }>;
  edges: Array<{
    source: string;
    target: string;
  }>;
}
```

### 2. `AIWorkflowGeneratorModalProps`
```typescript
interface AIWorkflowGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (workflow: Workflow) => void;
  availableAgents?: Array<{ id: string; name: string; role?: string; icon?: string }>;
}
```

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| LLM returns malformed JSON or markdown fences | Parsing failure | Use `_clean_json_markdown` and robust deterministic fallback templates |
| Generated step references non-existent agent | Step runtime failure | System instruction explicitly supplies available agent IDs; fallback maps to `orchestrator` / `researcher` |
| Generated DAG has disconnected or cyclical edges | DAG layout issues | Edge sanitization validates dependencies and auto-links sequential steps if edges missing |

## Verification

- Unit tests: Add Test 34 to `backend/test_endpoints.py` verifying `POST /api/ai/generate-workflow` outputs valid DAG steps and edges.
- Integration tests: Run `backend/venv/Scripts/python backend/test_endpoints.py` ensuring all 34 tests pass.
- Manual checks: Open `/workflows`, click "AI Workflow Architect", generate a workflow, inspect the review deck, edit title/instructions, click "Create & Open Studio", verify redirection to `/workflows/[id]` and inspect visual DAG layout.
- Commands:
  - `backend/venv/Scripts/python backend/test_endpoints.py`
  - `npm --prefix frontend run build`
