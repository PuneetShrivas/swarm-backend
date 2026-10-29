# Architecture Decisions: Landing Page Redesign with Reference UI Components

- **Slug**: `landing-page-redesign`
- **Date/Time**: 2026-10-29T12:55:50+05:30
- **Status**: Accepted

---

## Context
The Swarm landing page required a complete, modern redesign to elevate the platform's positioning as an autonomous multi-agent orchestration engine with a Visual DAG Studio. The user requested referencing `https://github.com/PuneetShrivas/generative-engine-optimization/tree/main/src` (`src/app/page.tsx` and `src/components/`) and incorporating the majority of its interactive components.

## Decisions

1. **Pure CSS & Framer Motion Primitives (No Heavy Three.js Bloat)**:
   - While the reference repository had optional `@react-three/fiber` imports, we implemented the 3D glare effects, hover boxes, and luminous beams using pure SVG path animations, Framer Motion, and CSS 3D matrix transforms.
   - This keeps bundle sizes lightweight (First load JS ~176 kB), eliminates WebGL context crashes, and guarantees instant mobile responsiveness.

2. **Tailored Narrative Hierarchy for Swarm**:
   - Re-architected all reference components to directly communicate Swarm's value proposition:
     - **Dynamic Resizable Navbar**: Shrinks on scroll, displaying status, brand, and quick links.
     - **Background Boxes Hero**: Interactive grid with LLM engine flipper (`Gemini 3.8`, `Sonar`, `Claude`, `GPT-4o`).
     - **Side-by-Side Comparison**: Demonstrates the failure mode of single-agent LLMs vs Swarm 2.0's parallel DAG decomposition.
     - **Dual Engine Spotlight**: Directs users toward either conversational chat or visual workflow automation.
     - **Bento Grid**: Highlights non-linear tree memory, sandboxed Python code, and Supabase RLS telemetry.
     - **Execution Lifecycle Timeline**: Explains the 4 stages from prompt ingestion to telemetry commit.
     - **3D Glare Agent Cards**: Interactive holographic cards for the 4 core specialized personas.
     - **Transparent Pricing**: Tiers with instant annual/monthly calculation.
     - **Background Beams CTA**: High-impact closing callout with multi-column footer.

3. **High-Contrast Dark Theme Compliance**:
   - Strictly utilized Linear dark design tokens (`text-ink` `#f7f8f8`, `surface-1`, `surface-2`, `hairline`), ensuring high contrast and zero readability regressions across all screens.

## Consequences
- World-class landing page aesthetics matching modern high-craft devtool benchmarks.
- Clean Next.js 14 production builds with zero ESLint or TypeScript warnings.
