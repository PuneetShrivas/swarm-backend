# Feature: PDF Attachment & Artifact Template Report Generation

**Datetime**: 2026-11-02T14:35:00+05:30  
**Status**: Draft (Awaiting User Approval)

## Goal

Enable users to attach a PDF document in chat, trigger an attached `/artifact` template picker popup directly from the input box to select an artifact template (e.g., Executive Summary, Research Report, Technical Audit, Financial Analysis), and receive the generated report both as a rich markdown response in chat and as a ready-to-download file artifact (.pdf / .md).

## Scope

- In scope:
  - **Chat Input Attached `/artifact` Template Popup (`ChatInput.tsx`)**:
    - Add `/artifact` (and `/artifacts`) to slash commands with an interactive popover docked directly above the input box.
    - Provide a built-in library of artifact report templates:
      1. **Executive Summary Report** (High-level overview, key findings, strategic recommendations, risk matrix).
      2. **Research & Deep-Dive Synthesis** (Abstract, methodology, comprehensive findings, comparative evidence, citations).
      3. **Technical Specification & Architecture Audit** (System architecture, component analysis, security review, implementation roadmap).
      4. **Financial & Quantitative Data Analysis** (Financial performance, KPI metrics, tabular comparisons, forward projections).
      5. **Compliance & Policy Review** (Regulatory evaluation, policy gap analysis, compliance checklist, remediation plan).
      6. **Actionable Meeting & Transcript Minutes** (Discussion summary, decisions adopted, action item matrix with owners/deadlines).
    - Allow selecting previously created/saved user artifacts as custom templates.
    - On selection, populate/update the input box (e.g., `prepare a report according to /artifact [Executive Summary Report]`) and attach template specifications to the message payload.
  - **PDF Attachment Ingestion & Grounding**:
    - Verify and enhance PDF upload handling in `ChatInput.tsx` / `page.tsx` (drag-and-drop or paperclip file picker) ensuring binary PDFs are base64-encoded and sent in `attached_artifacts`.
    - Ensure `build_artifact_context_block` in `backend/app/main.py` extracts human-readable text from attached PDFs using `pypdf.PdfReader` without leaking raw base64 into prompt context.
  - **On-The-Fly Multi-Agent Workflow Routing (`ai_generator.py`)**:
    - Add specialized workflow decomposition pattern for PDF + Artifact Template requests:
      - **Step 1: Document Parsing & Evidence Extraction (`file_parser`)**: Extracts text, structural sections, tables, and metrics from the attached PDF.
      - **Step 2: Template Analysis & Structured Report Drafting (`writer` / `data_analyst`)**: Analyzes PDF data against the selected artifact template schema.
      - **Step 3: Executive Publication & File Artifact Generation (`file_creator` / `synthesizer`)**: Compiles the comprehensive Markdown report and triggers ReportLab PDF generation.
  - **Dual Output Rendering (`backend/app/main.py` & `MessageItem.tsx`)**:
    - Ensure `extract_file_artifact_from_turn` generates a styled PDF document (`generate_pdf_document`) and registers it in `file_artifact` metadata.
    - Render the full markdown report in the chat message bubble and display the downloadable file card with a one-click `Download File` button.
- Out of scope:
  - OCR for scanned image-only PDFs without text layers (focus on standard text-encoded PDFs).

## Current behavior

1. When a user uploads a PDF in chat, it is base64-encoded and attached as context, but typing `/artifact` does not open a template picker popup; slash commands only show `/workflows`, `/agents`, `/clear`.
2. There is no attached popup on the input box specifically designed to browse, preview, and select artifact report templates.
3. When asking for a report from an attached PDF, the system falls back to generic text completion without a dedicated document parsing and template generation pipeline, occasionally omitting the downloadable file card.

## Proposed behavior

1. **Attached `/artifact` Template Popup**:
   - Typing `/artifact` or `/template` (or clicking the `/artifact` command) displays an attached popover docked directly to the top edge of the chat input box.
   - Users browse labelled artifact templates with badges, descriptions, and structural outline tags.
   - Selecting a template updates the input prompt to `prepare a report according to /artifact [Template Name]` and stores the template definition in `attached_template`.
2. **Contextual PDF Attachment**:
   - The user attaches a PDF file via drag-and-drop or the attachment paperclip. The PDF appears as an attached context pill above the input box.
3. **End-to-End Orchestration**:
   - When the user sends the prompt with the attached PDF and `/artifact` template, the backend synthesizes a dedicated 3-step pipeline (`file_parser` -> `writer` -> `file_creator` / `synthesizer`).
   - The PDF's text is cleanly extracted, analyzed against the template's required sections, and synthesized.
4. **Dual Output Deliverable**:
   - The chat message bubble displays the complete, formatted Markdown report with all sections, tables, and citations.
   - The message bubble includes an integrated downloadable file card (e.g., `<Report_Title>.pdf` or `<Report_Title>.md`) with a `Download File` button for instant offline access.

## Implementation steps

1. **Step 1: Implement Attached Artifact Template Popover in `ChatInput.tsx`**:
   - Add `/artifact` and `/template` to `SLASH_COMMANDS`.
   - Build an attached popover container (`ArtifactTemplatePicker`) docked right above the input box with Linear Design styling (`bg-surface-1`, hairline border, dark glass backdrop).
   - Define built-in report templates (Executive Summary, Research Deep-Dive, Technical Specification, Financial & Data Analysis, Compliance Review, Meeting Minutes).
   - Support keyboard navigation (`ArrowUp`, `ArrowDown`, `Enter`, `Escape`) and click selection.
   - Update prompt text and callback payload with the selected template.
2. **Step 2: Enhance Backend PDF Ingestion & Ephemeral Report Pipeline in `ai_generator.py` and `main.py`**:
   - In `backend/app/ai_generator.py`: Add dedicated ephemeral workflow pattern for `/artifact` or report requests with attached documents/PDFs (`file_parser` -> `writer` -> `file_creator` / `synthesizer`).
   - In `backend/app/main.py`: Update `extract_file_artifact_from_turn` to ensure that whenever an `/artifact` template report is requested, a downloadable styled PDF (`generate_pdf_document`) and Markdown file are generated and returned in `metadata.file_artifact`.
   - Ensure `build_artifact_context_block` provides the clean extracted PDF text to the workflow steps.
3. **Step 3: Verification, QA Checklist & End-to-End Testing**:
   - Run Next.js production build (`npm --prefix frontend run build`).
   - Verify attaching a PDF file and selecting `/artifact` template from the attached popup.
   - Verify dual output: markdown response in chat message and downloadable file card with functioning download button.
   - Document verification in `verification.md` and complete `qa-checklist.md`.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `frontend/src/app/chat/components/ChatInput.tsx` | Modify | Add `/artifact` command, attached artifact template picker popup, and template selection handling. |
| `frontend/src/app/chat/types.ts` | Modify | Add `ArtifactTemplate` type interface and metadata fields. |
| `frontend/src/app/chat/page.tsx` | Modify | Forward selected artifact template metadata to backend chat stream API. |
| `backend/app/ai_generator.py` | Modify | Add on-the-fly workflow pattern for PDF + Artifact Template report generation. |
| `backend/app/main.py` | Modify | Handle `/artifact` prompt detection and ensure downloadable PDF/MD artifact generation. |
| `docs/features/pdf-artifact-report-generation/plan.md` | New | Feature plan documentation following standard template. |
| `docs/features/pdf-artifact-report-generation/implementation.md` | New | Step-by-step implementation log with dates and diffs. |
| `docs/features/pdf-artifact-report-generation/verification.md` | New | Test results and verification documentation. |
| `docs/features/pdf-artifact-report-generation/qa-checklist.md` | New | Manual QA checklist for verification. |

## Interfaces

```typescript
export interface ArtifactTemplate {
  id: string;
  title: string;
  badge: string;
  description: string;
  sections: string[];
  icon: string;
  defaultFormat: "pdf" | "markdown" | "docx";
}
```

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Large PDF size slowing down prompt or exceeding context | High latency or truncation | `extract_text_from_artifact` limits clean excerpt to 12,000 characters and leverages RAG chunk retrieval for dense documents. |
| Missing ReportLab dependencies for PDF generation | PDF synthesis error | `reportlab` is already installed in `backend/venv` and verified in `file_creator/tools.py`. If generation fails, fallback to downloadable Markdown `.md` is guaranteed. |
| Popover collision or overflow on mobile viewports | Obscured input box | Dock popover with `max-h-80 overflow-y-auto`, responsive widths (`sm:min-w-[400px] max-w-full`), and backdrop blur. |

## Verification

- **Automated / Build**: `npm --prefix frontend run build` (0 errors).
- **Backend Verification**: Execute test script asserting PDF text extraction and ReportLab document generation.
- **Manual Verification**:
  1. Upload a PDF attachment into chat.
  2. Type `/artifact` in input box and verify attached template popup opens.
  3. Select "Executive Summary Report".
  4. Submit query "prepare a report according to /artifact [Executive Summary Report]".
  5. Verify chat displays markdown report and downloadable `.pdf` file card.
  6. Click `Download File` and verify downloaded file opens properly.

## Rollout

Direct rollout to chat frontend and backend. Backward compatible with all existing chat messages and sessions.
