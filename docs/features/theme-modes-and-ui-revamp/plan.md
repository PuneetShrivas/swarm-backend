# Feature: Modern Theming, Theme Switching, and Polished UI Revamp

## Status

Completed (2026-10-28T16:47:00+05:30)

## Goal

Transform the application's visual design into a cohesive, modern AI SaaS interface (inspired by Linear, Vercel, and Raycast) with comprehensive theme switching supporting Light, Dark, and System modes, alongside 5 curated aesthetic color palettes (Modern Slate, Violet Nebula, Emerald Matrix, Amber Luxe, and Nordic Frost) applied consistently across the Landing Page, Login Page, and Chat Swarm Workspace.

## Scope

- In scope:
  - Modern token-based CSS variable theme architecture in `frontend/src/app/globals.css` and `frontend/tailwind.config.ts`.
  - Dark mode (`light`, `dark`, `system`) and palette theme switching (`slate`, `nebula`, `emerald`, `amber`, `frost`) with zero-FOUC persistence in `localStorage`.
  - Interactive, accessible `ThemeSwitcher` component with live palette swatches and smooth Framer Motion animations.
  - Complete UI revamp of the Landing Page (`/`) with modern glassmorphism navbar, hero mesh background, theme switcher, and feature cards.
  - Revamp of Login Page (`/login`) with themed glass card and Supabase Auth UI synchronization.
  - Full Chat Workspace polish (`/chat`):
    - `SessionSidebar`: Modern dark/light sidebar with crisp session items, active pill indicators, rename/delete actions, and collapsible agent roster.
    - `ChatHeader`: Sticky glassmorphic navbar with active agent badge, theme selector, token usage counter, and action controls.
    - `MessageItem`: Refined chat bubbles with agent badge, tool call disclosure with syntax-styled code view, branching `< 1 / 2 >` navigator, and feedback actions.
    - `ChatInput`: Floating modern input capsule with auto-resize, keyboard shortcut hints, and responsive send/stop button.
    - `UsageModal`: Polished telemetry dialog with metric counters, agent breakdown bars, and execution history.
- Out of scope:
  - Backend API changes (FastAPI endpoints and data models are fully functional and remain untouched).
  - Database schema changes (Supabase tables for sessions, messages, and usage remain intact).

## Current behavior

- Theming is fragmented and mostly hardcoded:
  - Landing page has hardcoded `bg-slate-950 text-white`.
  - Login page has hardcoded `bg-gray-50`.
  - Chat interface has hardcoded `bg-slate-50`, `bg-white`, `border-slate-200`.
- No theme switcher exists in the user interface.
- No dark mode support on the chat workspace.
- Basic component styling with default Tailwind utility classes and minimal design consistency.

## Proposed behavior

1. **Theme System & State**:
   - `ThemeProvider` manages mode (`light` | `dark` | `system`) and theme palette (`slate` | `nebula` | `emerald` | `amber` | `frost`).
   - Persists user preferences to `localStorage` and applies classes (`dark`, `theme-nebula`, etc.) to `<html>` with anti-flash script.
   - Design tokens mapped via CSS variables: `--background`, `--foreground`, `--card`, `--card-foreground`, `--border`, `--input`, `--primary`, `--primary-foreground`, `--accent`, `--muted`.
2. **Interactive Theme Switcher**:
   - Easily accessible from the Landing Page header, Login Page, and Chat Header.
   - Allows one-click switching between Light, Dark, System, and 5 curated color palettes with real-time preview dots.
3. **Consistent Component Design System**:
   - Polished typography, glassmorphism backdrops (`backdrop-blur-md`), subtle borders (`border-border`), and micro-interactions powered by Framer Motion.
   - Refined code blocks and tool disclosures in chat messages.

## Implementation steps

1. Install `next-themes` (or implement dedicated `ThemeProvider` and anti-flash hook).
2. Configure CSS design tokens and theme palettes in `frontend/src/app/globals.css` and `frontend/tailwind.config.ts`.
3. Create reusable UI primitives: `ThemeSwitcher`, `Badge`, `DropdownMenu`.
4. Wrap application in `ThemeProvider` in `frontend/src/app/layout.tsx`.
5. Revamp Landing Page (`frontend/src/app/page.tsx`) with modern navigation, hero, and themed cards.
6. Revamp Login Page (`frontend/src/app/login/page.tsx`) with dynamic Supabase Auth theme integration.
7. Revamp Chat Workspace (`frontend/src/app/chat/`):
   - Polish `SessionSidebar.tsx`
   - Polish `ChatHeader.tsx`
   - Polish `ChatInput.tsx`
   - Polish `MessageItem.tsx`
   - Polish `UsageModal.tsx`
   - Polish `page.tsx`
8. Verify frontend linter (`npm run lint`), build (`npm run build`), and manual theme switching across all views.

## Files to change

| File | Change | Reason |
| ---- | ------ | ------ |
| `frontend/package.json` | [MODIFY] | Add `next-themes` for zero-FOUC theme switching |
| `frontend/tailwind.config.ts` | [MODIFY] | Configure `darkMode: ["class"]` and semantic token mappings |
| `frontend/src/app/globals.css` | [MODIFY] | Define CSS variables for Light, Dark, and all 5 color palettes |
| `frontend/src/components/ThemeProvider.tsx` | [NEW] | Next-themes provider wrapper with palette context |
| `frontend/src/components/ThemeSwitcher.tsx` | [NEW] | Polished dropdown selector for Light/Dark/System and theme palettes |
| `frontend/src/app/layout.tsx` | [MODIFY] | Wrap root in `ThemeProvider` with font classes and smooth transitions |
| `frontend/src/app/page.tsx` | [MODIFY] | Revamp Landing Page with modern navbar, hero, theme toggle, and feature cards |
| `frontend/src/app/login/page.tsx` | [MODIFY] | Revamp Login Page with glassmorphic container and synced Supabase Auth UI styling |
| `frontend/src/app/chat/components/ChatHeader.tsx` | [MODIFY] | Embed ThemeSwitcher, polish agent status, title, and buttons |
| `frontend/src/app/chat/components/SessionSidebar.tsx` | [MODIFY] | Theme-aware styling, sleek conversation list items, and user profile card |
| `frontend/src/app/chat/components/ChatInput.tsx` | [MODIFY] | Modern floating input dock with glowing borders and keyboard hints |
| `frontend/src/app/chat/components/MessageItem.tsx` | [MODIFY] | Polished message bubbles, syntax-highlighted code styling, tool disclosures, and branch controls |
| `frontend/src/app/chat/components/UsageModal.tsx` | [MODIFY] | Themed telemetry dialog with responsive metric cards |
| `frontend/src/app/chat/page.tsx` | [MODIFY] | Coordinate full-height themed workspace layout and mobile responsiveness |

## Interfaces

```typescript
export type ThemeMode = 'light' | 'dark' | 'system';
export type ThemePalette = 'slate' | 'nebula' | 'emerald' | 'amber' | 'frost';

export interface ThemeContextType {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  palette: ThemePalette;
  setPalette: (palette: ThemePalette) => void;
  resolvedTheme: 'light' | 'dark';
}
```

## Risks and mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Flash of Unstyled Content (FOUC) on initial load | Medium | Use `next-themes` which injects a tiny render-blocking inline script into `<head>` to resolve theme before DOM paint |
| Supabase Auth UI styling mismatch | Low | Dynamically compute Supabase Auth `appearance.theme` based on active mode (`ThemeSupa` with dark/light variable overrides) |
| Tooltip or popover clipping in chat feed | Low | Use proper z-index layers and backdrop blur styling |

## Verification

- Linter: `npm --prefix frontend run lint` (0 errors, 0 warnings)
- Production Build: `npm --prefix frontend run build` (Clean compilation)
- Manual checks:
  1. Switch between Light, Dark, and System modes on Landing, Login, and Chat pages.
  2. Switch between all 5 color palettes (Slate, Nebula, Emerald, Amber, Frost) and confirm colors update instantly across all surfaces.
  3. Refresh the page to confirm the selected theme persists from `localStorage`.
  4. Test message sending, branching (`< 1 / 2 >`), editing, tool call inspection, and usage modal in both light and dark themes.
