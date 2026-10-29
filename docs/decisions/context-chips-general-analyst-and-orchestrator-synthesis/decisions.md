# Decisions: Attached Context Chips, General Data Analyst & Orchestrator Goal Synthesis

**Datetime:** 2026-10-29T22:15:00+05:30  
**Feature Slug:** `context-chips-general-analyst-and-orchestrator-synthesis`  
**Status:** Approved  

## Decision 1: Safe Multi-Param Callback Contract for ChatInput
- **Context:** `ChatInput` invoked `onSend(trimmed, attachedArtifacts)` with two parameters, but `page.tsx` defined `onSend={(content) => handleSend(content)}`, dropping the artifacts.
- **Decision:** Explicitly type and pass `(content, arts) => handleSend(content, arts)` and let `handleSend` accept `artsToSend?: AttachedArtifact[]`. Additionally, if `artsToSend` is omitted or empty, fall back to current `attachedArtifacts` state, ensuring zero risk of attachment loss.

## Decision 2: Tolerant Metadata Deserialization in Session Tree Reconstruction
- **Context:** In PostgreSQL / Supabase, JSONB columns or raw API responses may return `metadata` as either an already-parsed JSON object or a serialized JSON string.
- **Decision:** In `reconstructTreeFromMessages`, inspect `typeof m.metadata === "string"`. If so, safely execute `JSON.parse` with a fallback to `{}`. In `MessageItem.tsx`, perform the same defense so both newly composed in-memory messages and restored messages reliably access `metadata.attached_artifacts`.

## Decision 3: Decoupling Data Analyst from Finance Scenarios
- **Context:** `data_analyst` had instructions referencing stock tickers, P/E ratios, and momentum indicators by default.
- **Decision:** Strip scenario-specific financial commands from `prompt.md` and `ai_generator.py`. Redefine `data_analyst` as an all-domain statistical, quantitative, and tabular structuring agent. Stock/market queries will continue to use Perplexity Sonar for web retrieval, but analysis will focus on quantitative variance and data normalization rather than assuming finance jargon for non-finance queries.

## Decision 4: Mandatory Synthesis Step for Multi-Agent Workflows
- **Context:** The orchestrator broke queries down into DAG workflows, but some DAGs ended on technical steps (e.g. `coder` or `reviewer` or `file_parser`), leaving intermediate step outputs as the final response without executive consolidation.
- **Decision:** Require that all multi-agent workflows ($\ge 2$ steps) conclude with a `synthesizer` step whose instructions explicitly require consolidating prior outputs in line with the high-level user goal.
