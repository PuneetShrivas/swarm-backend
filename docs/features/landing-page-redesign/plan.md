# Feature: Comprehensive Landing Page Redesign with Reference UI Components

- **Date/Time**: 2026-10-29T12:41:00+05:30
- **Feature Slug**: `landing-page-redesign`

## Status

Complete (Implemented & Verified 2026-10-29T12:55:50+05:30)

## Goal

Redesign the Swarm platform landing page (`frontend/src/app/page.tsx`) from scratch by porting and adapting the majority of components from `PuneetShrivas/generative-engine-optimization` (`src/app/page.tsx` and `src/components`), transforming the landing page into a modern, high-craft, interactive showcase for the Swarm multi-agent orchestration platform, Visual DAG Studio, and live execution telemetry.

## Scope

- In scope:
  - Utility setup:
    - Create `frontend/src/lib/utils.ts` with standard `cn()` helper (`clsx` + `tailwind-merge`).
  - Port and tailor core UI component primitives in `frontend/src/components/ui/`:
    - `resizable-navbar.tsx`: Scroll-aware dynamic floating navbar with desktop links and mobile drawer.
    - `background-boxes.tsx`: Interactive 3D perspective grid with hover color lighting.
    - `container-text-flip.tsx`: Animated text flip cycling through AI models (Gemini 3.8, Sonar, Claude, GPT-4o) with SVG icons.
    - `hero-highlight.tsx`: Gradient highlighter sweep effects for headline emphasis.
    - `card-spotlight.tsx`: Mouse-tracking radial spotlight glow cards.
    - `bento-grid.tsx`: Multi-tier layout grid with hover translations and responsive sizing.
    - `glare-card.tsx`: 3D tilt and holographic glare reflection cards for specialized agents.
    - `animated-testimonials.tsx`: Smooth stacked 3D rotation carousel for developer & architect testimonials.
    - `timeline.tsx`: Scroll-driven vertical progress bar illustrating swarm execution lifecycle.
    - `background-beams.tsx`: Luminous SVG ray animation canvas for the final CTA section.
    - `button.tsx`, `card.tsx`, `separator.tsx`, `switch.tsx`: Native Tailwind/Framer Motion primitives.
  - Port and tailor high-level section components in `frontend/src/components/landing/`:
    - `CompareResponse.tsx`: Interactive typewriter comparison demonstrating single-agent bottleneck vs multi-agent swarm orchestration.
    - `IntegrationsBento.tsx`: Bento grid showcasing Swarm's 5 core pillars.
    - `MetricsSection.tsx`: North star metrics (4 Core Specialists, Sub-second AST routing, 100% Deterministic Fallback) and supported stack.
    - `WhoWeServe.tsx`: 3D Glare Cards highlighting the 4 specialized agent roles (Orchestrator, Researcher, Python Specialist, Auditor).
    - `TestimonialsSection.tsx`: Testimonials from AI systems engineers.
    - `TimelineSection.tsx`: 4-stage execution sequence from objective to verified synthesis.
    - `PricingSection.tsx`: Flexible tiers (Community / Cloud / Enterprise).
    - `FinalCTA.tsx`: Animated beam backdrop inviting users to launch chat or studio.
    - `FooterSection.tsx`: Comprehensive footer with live status indicators and navigation links.
  - Complete rewrite of `frontend/src/app/page.tsx` assembling all sections seamlessly with dark theme coherence, responsive mobile layout, and zero TypeScript/lint errors.
- Out of scope:
  - Changes to backend FastAPI endpoints (this is a frontend visual and architectural redesign).
  - Heavy 3D WebGL runtimes (`@react-three/fiber` / `three.js`) to keep bundle sizes lean and load times instant.

## Current behavior

The existing landing page (`frontend/src/app/page.tsx`, 317 lines) is a standard static layout with basic text cards, a single code mockup terminal, and standard links. It lacks interactive 3D physics, scroll-aware navigation, model text-flipping, side-by-side execution comparison, bento grids, and interactive showcases.

## Proposed behavior

A completely redesigned, state-of-the-art landing page powered by the majority of components from the reference repository, featuring:
1. **Dynamic Floating Navbar**: Shrinks and blurs into a pill on scroll with instant navigation to Chat, Workflows, Agents, and Docs.
2. **Interactive 3D Grid Hero**: Background box grid with cursor lighting, model flipper ("Gemini 3.8", "Sonar", "Claude", "GPT-4o"), and high-contrast highlighter strokes.
3. **Interactive Side-by-Side Swarm Terminal**: Real-time typewriter comparison highlighting the speed and reliability of multi-agent decomposition over single-agent bottlenecks.
4. **Spotlight Feature Engines**: Dual mouse-tracking cards detailing Swarm Orchestration and Visual DAG Workflow Studio.
5. **Interactive Bento Grid**: Multi-card display of branching dialogue memory, Python sandboxes, and Supabase RLS telemetry.
6. **Execution Timeline**: Scroll-linked 4-step sequence showing how Swarm breaks down goals into verified solutions.
7. **3D Glare Agent Cards**: Holographic cards showcasing the 4 core specialized agent roles.
8. **Interactive Testimonials**: 3D stacked card carousel with smooth framer-motion transitions.
9. **Transparent Pricing & Plans**: Switchable monthly/yearly pricing cards.
10. **Luminous Beam Call to Action & Comprehensive Footer**: High-impact closing section with Background Beams and rich multi-column footer.

## Implementation steps

1. **Step 1: Utility & Primitives Foundation**:
   - Create `frontend/src/lib/utils.ts` with `cn()` utility.
   - Create native primitives in `frontend/src/components/ui/` (`button.tsx`, `card.tsx`, `separator.tsx`, `switch.tsx`).
   - Verify lint and build.
2. **Step 2: Port Visual Effects & Animation Components**:
   - Port `resizable-navbar.tsx`, `background-boxes.tsx`, `container-text-flip.tsx`, `hero-highlight.tsx`, `card-spotlight.tsx`, `bento-grid.tsx`, `glare-card.tsx`, `animated-testimonials.tsx`, `timeline.tsx`, and `background-beams.tsx` into `frontend/src/components/ui/`.
   - Update imports to use installed `framer-motion` and `@tabler/icons-react` / `lucide-react`.
   - Verify lint and build.
3. **Step 3: Port & Tailor Section Showcase Components**:
   - Create `CompareResponse.tsx` (Single vs Swarm execution).
   - Create `IntegrationsBento.tsx` (Bento Grid of capabilities).
   - Create `MetricsSection.tsx` (System telemetry & stack).
   - Create `WhoWeServe.tsx` (Specialized Agent roles with Glare Cards).
   - Create `TestimonialsSection.tsx` (3D animated testimonials).
   - Create `PricingSection.tsx` (Tiered plans with billing switch).
   - Create `FooterSection.tsx` (Comprehensive footer with live status).
   - Verify lint and build.
4. **Step 4: Redesign `frontend/src/app/page.tsx` from Scratch**:
   - Reconstruct `frontend/src/app/page.tsx` integrating all components in optimal narrative flow.
   - Ensure full dark theme responsiveness, mobile accessibility, and fast client-side hydration.
   - Verify clean production build (`npm --prefix frontend run build`).
5. **Step 5: Verification, Documentation, and Review**:
   - Run complete backend test suite to ensure zero regressions.
   - Run complete frontend build (`next build`) and lint (`next lint`).
   - Create `docs/features/landing-page-redesign/verification.md` and `qa-checklist.md`.
   - Update `CHANGELOG.md` and architecture decisions.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `frontend/src/lib/utils.ts` | New file | Standard `cn()` class merger for Tailwind |
| `frontend/src/components/ui/button.tsx` | New file | Tailwind button component with variants |
| `frontend/src/components/ui/card.tsx` | New file | Clean card component set |
| `frontend/src/components/ui/separator.tsx` | New file | Semantic divider |
| `frontend/src/components/ui/switch.tsx` | New file | Toggle switch for billing/plans |
| `frontend/src/components/ui/resizable-navbar.tsx` | New file | Dynamic floating navbar from reference repo |
| `frontend/src/components/ui/background-boxes.tsx` | New file | Interactive 3D grid hero background |
| `frontend/src/components/ui/container-text-flip.tsx` | New file | Model flipper with built-in SVG icons |
| `frontend/src/components/ui/hero-highlight.tsx` | New file | Gradient highlight text sweep |
| `frontend/src/components/ui/card-spotlight.tsx` | New file | Mouse-tracking spotlight card effect |
| `frontend/src/components/ui/bento-grid.tsx` | New file | Asymmetrical bento grid cards |
| `frontend/src/components/ui/glare-card.tsx` | New file | Holographic 3D glare cards |
| `frontend/src/components/ui/animated-testimonials.tsx` | New file | 3D stacked testimonial card carousel |
| `frontend/src/components/ui/timeline.tsx` | New file | Scroll-linked execution timeline |
| `frontend/src/components/ui/background-beams.tsx` | New file | Ray beam animation canvas |
| `frontend/src/components/landing/*` | New files | Section implementations tailored to Swarm |
| `frontend/src/app/page.tsx` | Complete rewrite | Redesigned landing page integrating all components |

## Interfaces

- Component Props: React 18 compatible props, standard Tailwind CSS classes.
- Navigation targets: `/chat`, `/workflows`, `/agents`, `/login`, `#architecture`, `#workflows`, `#pricing`.
- Zero external runtime API dependencies on initial landing render.

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| SSR / Client Hydration Mismatches with dynamic SVG transforms | Hydration warning in console | Add `"use client"` directive and ensure determinism before mount |
| Heavy WebGL bundle overhead | Slower initial page load | Avoid Three.js; implement pure CSS/Framer Motion shader and glare effects |
| Responsive overflow on small screens | Horizontal scrollbar on mobile | Wrap interactive sections with `max-w-7xl mx-auto px-4 sm:px-6` and `overflow-hidden` |

## Verification

- Lint: `npm --prefix frontend run lint`
- Build: `npm --prefix frontend run build`
- Regression test: `backend/venv/Scripts/python backend/test_endpoints.py`
- Manual checks: Responsive navbar scroll, hover box lighting, text flip transitions, side-by-side typewriter, 3D card glare, testimonials carousel.

## Rollout

Direct drop-in replacement of `frontend/src/app/page.tsx` and addition of reusable UI components in `frontend/src/components/`.
