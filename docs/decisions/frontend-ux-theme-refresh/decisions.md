# Architecture Decisions: Frontend UX, Theme & Brand Refresh

- **Slug**: `frontend-ux-theme-refresh`
- **Date/Time**: 2026-10-29T13:49:50+05:30
- **Status**: Accepted

---

## Context
1. The frontend had divergent navigation structures: `/chat` and `/agents` used `AppNavigationRail` with the 3-pillar segmented switcher, but `/workflows` had an isolated custom header, preventing intuitive switching between core platform pillars.
2. The theming system was previously restricted to dark mode because design tokens like `canvas`, `surface-1`, `hairline`, and `ink` were hardcoded static hex values in `tailwind.config.ts`. Switching to light mode resulted in unreadable white-on-white text and dark backgrounds.
3. User-facing copy contained typical AI cliches ("holographic neural persona", "linear intelligence", "seamlessly transition") rather than clear, engineering-focused technical English.
4. The project logo was a placeholder generic Lucide bot icon.

---

## Decisions

### 1. Unified Navigation Switcher Standard (`AppNavigationRail`)
- **Decision**: Standardize on `AppNavigationRail` as the singular top navigation bar for all three main application views (`/chat`, `/agents`, `/workflows`).
- **Implementation**:
  - Mounted `<AppNavigationRail currentTab="workflows" />` on `/workflows`.
  - Moved pipeline search, visibility filters, "AI Architect", and "New Workflow" into a clean secondary toolbar, establishing parity with `/agents`.
  - Added a compact 3-pillar switcher to `/workflows/[id]` so users editing a canvas can navigate back to Chat or Agents without losing context.

### 2. Dynamic CSS Variable Theming for Complete Light Mode
- **Decision**: Refactor all surface, border, and ink design tokens in `tailwind.config.ts` from static hex colors to dynamic HSL CSS variables with alpha channel support (`hsl(var(--...) / <alpha-value>)`).
- **Implementation**:
  - Defined high-contrast zinc/white light tokens under `:root` and `.light` in `globals.css`.
  - Maintained pure dark tokens under `.dark`.
  - Configured typography prose variables to dynamically adapt bold and heading tags (`#09090b` in light mode, `#f7f8f8` in dark mode).
  - Integrated `ThemeSwitcher` into `AppNavigationRail` and `ResizableNavbar` for instant user access.

### 3. Engineering-Grade Copy Standards
- **Decision**: Eradicate AI buzzwords and marketing filler across all pages, modals, and tooltips.
- **Implementation**:
  - Replaced vague statements with precise technical descriptions (e.g. "Orchestrate Multi-Agent Production Systems", "Inspect built-in agent specialists, system prompt roles, and execution models", "Stateless FastAPI orchestration, visual DAG workflow execution, and dialogue branching").
  - Updated default initial chat greeting to `"Swarm orchestrator ready. Select an agent or submit a query to begin."`.

### 4. Internet Brand Asset Integration
- **Decision**: Incorporate an authentic open-source Swarm brand asset sourced from the GitHub multi-agent ecosystem (`The-Swarm-Corporation`).
- **Implementation**:
  - Saved asset to `frontend/public/swarm-logo.png`.
  - Built `BrandLogo.tsx` with Next.js image optimization, responsive sizing, and vector SVG fallback.
  - Replaced placeholder robot icons across navbars, headers, and footers.

---

## Consequences

- **Positive**:
  - Consistent navigation across all 3 pillars with zero friction switching between Chat, Agents, and Workflows.
  - Seamless, fully accessible Light and Dark mode rendering.
  - Professional, developer-first communication tone matching leading developer platforms (Linear, Stripe, Vercel).
  - Cohesive visual branding across the product.
- **Considerations**:
  - Future components must use semantic tokens (`bg-canvas`, `bg-surface-1`, `border-hairline`, `text-ink`) rather than hardcoded hex values to maintain automatic Light/Dark adaptability.
