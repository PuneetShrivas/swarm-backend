# QA Checklist: Sidebar Sessions Across Pages and Artifacts Tab Visibility

**Datetime:** 2026-10-29T18:27:40+05:30  
**Feature Slug:** `sidebar-sessions-and-artifacts-visibility`  

- [x] Unified sidebar displays conversations list when user is on `/workflows`
- [x] Unified sidebar displays conversations list when user is on `/agents`
- [x] Unified sidebar displays conversations list when user is on `/artifacts`
- [x] Clicking a conversation from any non-chat page navigates to `/chat?session=<id>`
- [x] The targeted session's complete message history and branching tree loads into view
- [x] Generating a file in chat (e.g., CSV, Python script, JSON) immediately populates into `/artifacts`
- [x] Visiting `/artifacts` tab displays all generated files with filename, size, agent origin, and preview snippet
- [x] Downloading file artifact from `/artifacts` produces valid file with correct MIME type
- [x] Deleting artifact removes it from `/artifacts` and local cache
- [x] Backend test suite passes all 57 tests
- [x] Frontend production build compiles with zero errors
