# Architecture Decision Record: Default Workflow Template Architecture

**Created**: 2026-10-29T16:19:40+05:30
**Status**: Accepted

## Context

Users arriving at the Swarm platform need a production-grade, out-of-the-box workflow that illustrates what multi-agent workflows are capable of, rather than encountering an empty workflow library. The workflow must showcase the full breadth of block types (`agent`, `condition`, `python_code`, `loop`, `artifact`) and agents.

## Decisions

### 1. Default Workflow Topic: Competitive Product Research & Technical Report
- **Rationale**: This is a universally applicable workflow archetype that demonstrates realistic real-world agent collaboration:
  1. `researcher` queries live web data via Perplexity Sonar.
  2. `python_code` programmatic script computes quantitative metrics and depth scores without consuming LLM tokens.
  3. `condition` gate evaluates quality metrics to determine if research satisfies quality criteria.
  4. `loop` controller retries research if quality is insufficient.
  5. `data_analyst` processes statistical comparisons.
  6. `coder` generates practical implementation scripts.
  7. `reviewer` performs security and best-practice audit.
  8. `artifact` compiles a structured markdown deliverable for download.

### 2. In-Memory Store Seeding at Application Startup
- **Rationale**: Seeding at FastAPI initialization guarantees the template is always available immediately upon backend startup, both in test environments and in production serverless runtimes.
- **Idempotency**: Checked against `memory_store.workflows` using the fixed ID `default-wf-research-pipeline`.

### 3. Visibility and Public Discovery
- **Visibility**: Set to `public`, allowing it to naturally appear in every user's `GET /api/workflows` list via the existing `visibility.in.(shared,public)` filter.
- **Dedicated Endpoint**: Added `GET /api/workflows/defaults` so frontend clients can query templates independently of user-created workflows for a dedicated "Templates" tab or starter modal.

## Consequences

- All users immediately have access to a rich 8-step workflow on launch.
- Users can fork the workflow using `POST /api/workflows/{id}/fork` to customize their own copy.
- Zero extra database migration required as it reuses the standard workflow schema.
