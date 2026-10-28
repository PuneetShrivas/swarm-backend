# Agent instructions

Read `docs/development-process.md` for strict instructions on the development process and follow it. Mention Datetime in documentation files.

## Mandatory workflow

For any feature, bug fix, refactor, or architectural change:

1. Run `/plan` first unless the change is a one-line typo or comment fix.
2. Create and maintain documentation under `docs/features/<feature-slug>/`. Check `docs/templates/feature-plan.md` for the template.
3. Never mark a task complete unless tests, lint, and build checks pass.
4. Update documentation in the same change as the code.
5. If implementation reveals a changed assumption, update `plan.md` and
   `decisions.md` before continuing.

## Required feature documentation

For every feature, create:

- `docs/features/<feature-slug>/plan.md`
- `docs/features/<feature-slug>/implementation.md`
- `docs/features/<feature-slug>/verification.md`
- `docs/features/<feature-slug>/qa-checklist.md`

## Definition of done

A task is complete only when:

- [ ] Code follows repository conventions.
- [ ] Tests cover new behavior and relevant regressions.
- [ ] Feature documentation is created or updated.
- [ ] Architecture documentation is updated if interfaces or data flow changed.
- [ ] A concise changelog entry exists.
- [ ] The final summary lists changed files, tests, docs, and residual risks.

## Document decisions

Maintain key decisions in `docs/decisions/<architecture-slug>/decisions.md`.
