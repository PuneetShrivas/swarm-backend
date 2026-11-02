# QA Checklist: PDF Attachment Report Generation & Attached /artifact Picker

**Datetime**: 2026-11-02T15:03:30+05:30  
**Feature**: `pdf-artifact-report-generation`  
**Status**: Ready for Production / Completed

## Visual Inspection Checklist

- [x] **Attached Template Popover Framing**:
  - [x] Attached `#artifact-template-container` popover docks directly above the chat input box.
  - [x] Conforms to Linear dark theme styling (`bg-card`, hairline border `border-border/80`, backdrop blur, SF-proportional typography).
  - [x] Popover does not clip or overflow viewport on desktop or mobile screens.
- [x] **Template Directory Display**:
  - [x] Renders 6 distinct report templates with title, category badge, description, and hashtag section pills.
  - [x] Includes search input at top with immediate live filtering.
  - [x] Active template displays [`Check`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/frontend/src/app/chat/components/ChatInput.tsx) icon indicator.
- [x] **Input Box Context Chips**:
  - [x] Attached PDF file renders with red `PDF` badge and file size.
  - [x] Selected template renders with purple `TEMPLATE` badge, title, and quick dismiss `X` button.
  - [x] Textarea expands smoothly without jumping when chips are present.

---

## Functional Interaction Checklist

- [x] **Invoking the Template Picker**:
  - [x] Typing `/artifact` inside the prompt automatically triggers the attached template popover.
  - [x] Clicking the Paperclip attachment menu displays "Report Template (/artifact)" option.
- [x] **Keyboard & Navigation**:
  - [x] `ArrowUp` and `ArrowDown` navigate through the template list.
  - [x] `Enter` selects the highlighted template, populates `"prepare a report according to /artifact [Template Title]"`, and closes popover.
  - [x] `Escape` or clicking outside dismisses the popover.
- [x] **End-to-End Orchestration**:
  - [x] Sending prompt with attached PDF and `/artifact` triggers the 3-step ephemeral workflow:
    - `step_1`: [`file_parser`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/agents/file_parser/) extracts text schemas, tables, and entities.
    - `step_2`: [`writer`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/agents/writer/) formats and drafts the report sections.
    - `step_3`: [`synthesizer`](file:///C:/Users/punee/OneDrive/Documents/GitHub/swarm-backend/backend/app/agents/synthesizer/) finalizes executive markdown and compiles PDF sections.
- [x] **Dual Response Presentation**:
  - [x] Chat message displays the complete, formatted Markdown document with headings, bullets, and tables.
  - [x] Message bubble includes a downloadable file artifact card showing PDF icon, filename, and file size.
  - [x] Clicking "Download PDF" initiates a clean browser download of the base64 PDF.

---

## Regression & System Health

- [x] Production build passes with 0 errors (`npm --prefix frontend run build`).
- [x] Backend automated test suite passes (`backend/test_pdf_report_artifact.py`).
- [x] ReportLab Paragraph rendering handles `<, >, &` without XML parsing errors.
- [x] Existing slash commands (`/workflows`, `/clear`) continue to function without regression.
- [x] Artifacts Studio reflects newly generated PDF reports in the persistent artifact memory store.
