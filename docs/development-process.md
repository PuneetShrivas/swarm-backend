# Development cycle

Every non-trivial change must follow these stages:

1. **Understand**
   - Identify affected modules, APIs, data models, and tests.
   - Record assumptions and open questions.

2. **Plan**
   - Create `docs/features/<feature-slug>/plan.md`.
   - Include goal, scope, non-goals, file-level changes, interfaces,
     risks, rollout notes, and verification commands.

3. **Implement**
   - Work in small commits.
   - Follow existing architecture and conventions.
   - Do not expand scope without updating the plan.

4. **Verify**
   - Add/update tests.
   - Run all required checks.
   - Record actual commands and outcomes in `verification.md`.

5. **Document**
   - Update `docs/features/<feature-slug>/`.
   - Update architecture docs if behavior, interfaces, or data flow changed.
   - Add a concise changelog entry.

6. **Review**
   - Produce a final diff summary and manual QA checklist.
   - Do not declare completion until all checks and docs are updated.
