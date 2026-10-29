# Architecture Decisions: AI Mode Workflow Generation

- **Slug**: `ai-mode-workflow-generation`
- **Date/Time**: 2026-10-29T12:35:50+05:30
- **Status**: Accepted

---

## Context
Users needed a natural-language AI mode for generating multi-agent DAG pipelines on the `/workflows` dashboard and studio canvas, similar to the existing AI mode for creating agents on `/agents`.

## Decisions

1. **Leveraged existing `POST /api/ai/generate-workflow` endpoint**:
   - The backend already had a base generation endpoint utilizing Gemini 3.8 Flash with structured JSON schema outputs.
   - We enhanced the system instruction to explicitly support all 5 step types (`agent`, `condition`, `python_code`, `loop`, `artifact`) and reinforced robust default fallbacks.

2. **Linear-style Modal UX with Editable Review Deck**:
   - Rather than directly persisting an uninspected workflow, the user is presented with a rich inspection modal (`AIWorkflowGeneratorModal.tsx`).
   - The user can preview the visual execution sequence strip, expand each step card, edit Title, Goal, and Description, and then persist with "Create & Open Studio".

3. **Dual Entrypoints**:
   - Added entrypoints on `/workflows` (top toolbar, empty state, manual modal shortcut) and `/workflows/[id]` (studio canvas header), ensuring frictionless discoverability.

## Consequences
- Faster workflow onboarding for non-technical and power users alike.
- Guaranteed fallback responsiveness when API keys are unconfigured or rate limited.
