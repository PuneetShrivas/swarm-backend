# QA Checklist: Modern Theming, Theme Switching, and Polished UI Revamp

*Created: 2026-10-28T16:30:00+05:30*  
*Completed: 2026-10-28T16:47:00+05:30*

## Pre-flight
- [x] Dependencies installed cleanly without audit flags (`next-themes`).
- [x] CSS design tokens mapped in `frontend/tailwind.config.ts` and `frontend/src/app/globals.css`.

## Theme Modes & Switching
- [x] Open Landing Page (`/`):
  - [x] Theme switcher is visible in top navigation.
  - [x] Switch to **Light Mode**: background turns clean light/off-white; text is crisp dark slate.
  - [x] Switch to **Dark Mode**: background turns deep dark; text is clean light.
  - [x] Switch to **System**: honors OS dark/light mode preference.
- [x] Palette Selection:
  - [x] Select **Slate**: neutral obsidian/white with indigo accent.
  - [x] Select **Nebula**: deep violet/indigo with neon purple accent.
  - [x] Select **Emerald**: carbon obsidian with emerald green accent.
  - [x] Select **Amber**: warm espresso charcoal with amber gold accent.
  - [x] Select **Frost**: arctic navy with ice cyan accent.
- [x] Persistence:
  - [x] Select a theme, close the tab, reopen `http://localhost:3000`: the selected mode and palette persist without flashing.

## Landing Page (`/`)
- [x] Modern navigation header with brand icon, status pill, GitHub link, and theme selector.
- [x] Hero section has glowing gradient background, bold typography, and interactive CTA buttons.
- [x] Feature cards have subtle borders, hover elevation, and responsive grid layout.

## Login Page (`/login`)
- [x] Card uses backdrop blur and responsive padding.
- [x] Supabase Auth UI adapts to light / dark theme cleanly with readable form labels, inputs, and OAuth buttons.
- [x] "Back to Home" button functions smoothly.

## Chat Workspace (`/chat`)
- [x] **Sidebar (`SessionSidebar`)**:
  - [x] "+ New Chat" button features modern accent styling.
  - [x] Conversation items display active selection pill and hover quick-actions.
  - [x] Collapsible "Active Swarm" list expands and collapses cleanly.
  - [x] User profile footer displays email, usage button, and sign out button in themed card.
- [x] **Header (`ChatHeader`)**:
  - [x] Theme switcher dropdown operates smoothly.
  - [x] Active agent pill displays pulse dot.
  - [x] Usage counter badge opens telemetry modal.
  - [x] Export and Clear buttons have clear hover and disabled states.
- [x] **Message Feed (`MessageItem`)**:
  - [x] User messages render in modern themed pill/bubble.
  - [x] Agent messages render in clean card with agent avatar, badge, and formatted markdown.
  - [x] Code blocks render with monospace font, dark/light contrast, and copy action.
  - [x] Tool call accordion opens and closes smoothly with formatted JSON.
  - [x] Branch switcher `< 1 / 2 >` renders cleanly and navigates alternatives.
  - [x] Thumbs up / down rating buttons toggle with visual accent feedback.
- [x] **Input Dock (`ChatInput`)**:
  - [x] Auto-resizes smoothly up to max height.
  - [x] Sends on `Enter`, inserts newline on `Shift+Enter`.
  - [x] Send / Stop button features polished transition and icon states.
- [x] **Usage Modal (`UsageModal`)**:
  - [x] Backdrop blur covers screen.
  - [x] Token count cards, agent consumption breakdown, and recent history table display clearly.
