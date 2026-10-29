# QA Checklist: Gemini 3.8 Upgrade, Citations UI, Theme Dark Prose & Chat Input Scrollbar

- **Reviewed Date/Time**: 2026-10-29T08:15:45+05:30
- **Status**: Complete
- **Feature Slug**: `gemini-3.8-upgrade-citations-theme-fix`

---

## Pre-Release Quality Assurance Checklist

### 1. Model Availability & Normalization
- [x] All default Gemini models configured to `gemini-3.8-flash`.
- [x] All Pro Gemini models updated to `gemini-4-argon`.
- [x] Backend `normalize_model_name` safely converts legacy `gemini-2.5-flash` to `gemini-3.8-flash`.
- [x] Backend `normalize_model_name` safely converts legacy `gemini-2.5-pro` to `gemini-4-argon`.
- [x] General Assistant agent config updated from `gemini-2.5-flash` to `gemini-3.8-flash`.
- [x] AI Workflow & Agent generator prompts and defaults use `gemini-3.8-flash`.
- [x] Frontend `ChatHeader` dropdown lists:
  - Default Model
  - Gemini 3.8 Flash
  - Gemini 4 Argon
  - Perplexity Sonar
  - Perplexity Sonar Pro
- [x] Custom Agent Studio and Workflow block editors offer latest models.

### 2. Dark Theme Readability
- [x] `--tw-prose-bold` configured to `#f7f8f8` / `hsl(var(--foreground))`.
- [x] `--tw-prose-headings` configured to `#f7f8f8` / `hsl(var(--foreground))`.
- [x] Markdown bold terms (`**text**`, `__text__`) clearly readable against `#010102` canvas.
- [x] ReactMarkdown custom renderers enforce `text-ink font-semibold`.
- [x] Links, blockquotes, inline code, and lists maintain high-contrast styling across all theme palettes.

### 3. Citations & Sources Experience
- [x] Perplexity Sonar responses surface citations in `agent_metadata["citations"]`.
- [x] Frontend `MessageItem` displays dedicated "Sources & Citations" section under agent messages.
- [x] Citations render with numeric badge `[1]`, `[2]`, clean domain name, and external link icon.
- [x] Citations open external URLs safely in a new tab (`rel="noopener noreferrer"`).
- [x] If >4 citations exist, an expandable toggle ("+X more") is provided.
- [x] Tool executions accordion does not dump raw URL JSON arrays, keeping output clean.

### 4. Chat Input Box UI
- [x] Vertical scrollbar hidden on `<textarea>` on Windows Chrome, Edge, and Firefox.
- [x] Cross-browser CSS `.no-scrollbar` and Tailwind classes applied.
- [x] Textarea expands smoothly up to max height without flashing a scrollbar track.

### 5. Regressions & Build
- [x] `backend/test_endpoints.py` passes all 33 modular tests.
- [x] Next.js production build (`npm run build`) completes with zero type errors.
