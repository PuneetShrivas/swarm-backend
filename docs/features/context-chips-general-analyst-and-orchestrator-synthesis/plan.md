# Feature: Attached Context Chips, General Data Analyst & Orchestrator Goal Synthesis

**Datetime:** 2026-10-29T22:25:00+05:30  
**Status:** Complete  

## Goal
1. Ensure context artifacts attached to a chat prompt (via upload or Artifacts Studio) are visibly rendered on the user message bubble in the chat view.
2. Remove scenario-specific directives (e.g. finance/stock metrics) from agent prompts, specifically establishing `data_analyst` as a general-purpose numerical and tabular analysis agent across all domains.
3. Ensure that when the orchestrator generates workflows on the fly, every multi-agent pipeline concludes with a final `synthesizer` step that consolidates all prior step outputs in direct alignment with the high-level user goal.

## Scope
- In scope:
  - `frontend/src/app/chat/page.tsx`: Fix `ChatInput.onSend` forwarding and ensure `attached_artifacts` is always retained in user node metadata.
  - `frontend/src/app/chat/types.ts`: Parse `metadata` in `reconstructTreeFromMessages` if returned as a JSON string from PostgreSQL/Supabase.
  - `frontend/src/app/chat/components/MessageItem.tsx`: Robust resolution of `attachedArtifacts` for user messages with format badges, icons, filenames, and download actions.
  - `backend/app/main.py`: Persist `attached_artifacts` in `db_save_message` when provided in `request.attached_artifacts`.
  - `backend/app/agents/data_analyst/prompt.md`: Generalize Data Analyst system prompt across scientific, operational, business, and ML domains, avoiding scenario-specific finance mandates.
  - `backend/app/ai_generator.py`: Remove finance-specific instructions for `data_analyst`, and ensure every multi-agent on-the-fly workflow terminates with a `synthesizer` step aligned with the high-level user goal.
  - Automated tests in `backend/test_endpoints.py` and Next.js production build verification.
- Out of scope:
  - Redesigning the entire database schema for chat messages.
  - Modifying third-party MCP servers.

## Current behavior
- `ChatInput.tsx:167` called `onSend(trimmed, attachedArtifacts)`, but `page.tsx:1016` passed `onSend={(content) => handleSend(content)}`, dropping `attachedArtifacts`.
- In `reconstructTreeFromMessages`, `m.metadata` was not parsed if it was a JSON string, causing attachments to vanish upon session reload.
- `ai_generator.py` hardcoded stock valuation metrics ("price-to-earnings, momentum indicators, financial variance") into `data_analyst` instructions regardless of query intent.
- Several on-the-fly workflows (e.g. security audits, document parsing) lacked a final synthesis step, returning unformatted raw intermediate step outputs.

## Proposed behavior
- User message bubbles consistently display attached context documents with format-colored badges, icons, file names, sizes, and download actions, both live in session and upon session reload.
- `data_analyst` functions as a domain-agnostic numerical, statistical, and tabular analysis agent.
- Every multi-agent on-the-fly workflow concludes with a `synthesizer` step that evaluates all prior steps against the initial user goal and produces a cohesive executive output.

## Implementation steps
1. Update `frontend/src/app/chat/page.tsx`, `frontend/src/app/chat/types.ts`, `frontend/src/app/chat/components/MessageItem.tsx`, and `backend/app/main.py` for context chips binding and persistence.
2. Update `backend/app/agents/data_analyst/prompt.md` and `backend/app/ai_generator.py` to generalize Data Analyst directives.
3. Update `backend/app/ai_generator.py` workflow decomposition patterns and `generate_workflow_spec` to ensure all multi-step pipelines conclude with a goal-aligned `synthesizer` step.
4. Add automated tests covering the new behavior, run full test suites, verify frontend build, and deploy to production.

## Files to change
| File | Change | Reason |
| ---- | ------ | ------ |
| `frontend/src/app/chat/page.tsx` | Pass `arts` in `onSend`, retain in user message metadata | Fix context chips not appearing on user message bubble |
| `frontend/src/app/chat/types.ts` | Parse string metadata in `reconstructTreeFromMessages` | Ensure reloaded sessions display context chips |
| `frontend/src/app/chat/components/MessageItem.tsx` | Normalize metadata retrieval and format styling | Safe, prominent rendering of attached context |
| `backend/app/main.py` | Merge `request.attached_artifacts` into user message persistence | Guarantee context metadata is stored in DB |
| `backend/app/agents/data_analyst/prompt.md` | Domain-agnostic mathematical and tabular instructions | Remove scenario-specific finance mandates |
| `backend/app/ai_generator.py` | Update data analyst directives and add goal-aligned synthesizer step to all multi-agent workflows | Fulfill user request for domain-agnostic analyst and final goal synthesis |
| `backend/test_endpoints.py` | Add Tests 75-77 | Verify new behavior and regression safety |

## Risks and mitigations
| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Extra step increases latency for multi-agent workflows | Minor token usage and execution time increase | Synthesizer runs with fast Groq Qwen 3.8 and directly unifies prior step outputs |
| Large Base64 artifacts in message metadata could inflate DB payload | Supabase storage pressure | Store sanitized artifact descriptor (id, name, filename, type, size_bytes) if content exceeds 64KB |
