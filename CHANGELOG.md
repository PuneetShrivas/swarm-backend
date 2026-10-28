# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-10-28

### Added
- **Dynamic Multi-Palette Theming**: Support for 5 curated aesthetic palettes (`slate`, `nebula`, `emerald`, `amber`, `frost`) with zero-FOUC persistence in `localStorage`.
- **Mode Switching**: Full `light`, `dark`, and `system` mode support via `next-themes` and semantic CSS variables.
- **Interactive Theme Switcher**: Accessible, animated popover component (`ThemeSwitcher.tsx`) with real-time palette swatches, mode toggles, and Framer Motion micro-interactions.
- **Modern Landing Page**: Complete redesign with sticky glassmorphism navbar, hero mesh glow matching the active palette, live status pills, and capability cards.
- **Synced Login Page**: Revamped auth container with glassmorphic backdrop, back-to-home link, and synchronized `@supabase/auth-ui-react` appearance theme.
- **Polished Chat Workspace**:
  - `SessionSidebar`: Modern conversation list items, active selection pills, inline edit controls, deletion confirmations, and collapsible agent roster.
  - `ChatHeader`: Sticky navbar with embedded `ThemeSwitcher`, active agent badge, model dropdown, token usage counter, and action buttons.
  - `MessageItem`: Styled user and agent bubbles, syntax-highlighted code block formatting, tool call disclosure accordion, and sibling branch switcher (`< 1 / 2 >`).
  - `ChatInput`: Floating input dock with auto-resize textarea, focus ring glow, and keyboard shortcut tips.
  - `UsageModal`: Themed telemetry modal with glowing token/query metric cards, breakdown by agent and model, and execution latency logs.

### Changed
- Refactored `frontend/tailwind.config.ts` and `frontend/src/app/globals.css` to use semantic HSL tokens (`background`, `foreground`, `card`, `primary`, `muted`, `accent`, `border`, `ring`).
