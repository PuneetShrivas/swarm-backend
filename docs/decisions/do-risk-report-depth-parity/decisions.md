# Architectural Decisions: D&O Public Risk Report Depth Parity & Claude-Quality Deliverables

**Created Datetime**: 2026-11-03T15:02:00+05:30  
**Last Updated Datetime**: 2026-11-03T15:35:00+05:30  

## Decision 1: `web_search_prompt.txt` as Dynamic Single Source of Truth (No Hardcoding)
- **Context**: The user may modify `web_search_prompt.txt` at any time to alter section order, add new analytical fields, change date cutoffs, or adjust risk band guidelines. Hardcoding section schemas, query templates, or prompt text in Python violates flexibility and prevents user-driven prompt iteration.
- **Decision**: Treat `web_search_prompt.txt` as the dynamic single source of truth. At runtime, `TemplateCompiler` dynamically parses `web_search_prompt.txt`, discovers section headers, extracts verbatim instruction blocks for each section, and derives search query concepts directly from the prompt text.
- **Consequence**: The system adheres strongly to `web_search_prompt.txt`. Any prompt edit by the user immediately propagates through the entire research, drafting, validation, and rendering pipeline without modifying Python source code.

## Decision 2: ReportLab `NumberedCanvas` for Two-Pass Multi-Page Typography
- **Context**: `Claude_NVIDIA_DO_Risk_Report.pdf` features a subtle running top header on pages 2–8 (`COMPANY — D&O Underwriting Analysis — DATE`) and running footers with total page counts (`Page X of Y`). Default ReportLab `SimpleDocTemplate` cannot calculate total page counts on a single pass.
- **Decision**: Subclass `canvas.Canvas` into `NumberedCanvas` which overrides `showPage` and `save` to record page states in memory and draw running headers and footers with total page counts in a second pass.
- **Consequence**: The PDF deliverable achieves visual and structural parity with Claude's layout without requiring external LaTeX, Node.js, or headless browser dependencies.

## Decision 3: Section-Aware Dynamic Fallback Generation
- **Context**: During testing with `MOCK_GROQ=true` or when Groq is unreachable, a single static stub caused all 11 sections to repeat `SECURITIES CLASS ACTION RISK`.
- **Decision**: Provide dynamic, section-aware fallback generation in `roles.py` that inspects each dynamic section's title and required fields to generate realistic, multi-paragraph, domain-specific text with citations.
- **Consequence**: Test runs and offline evaluations produce realistic multi-page reports reflecting the true report structure.
