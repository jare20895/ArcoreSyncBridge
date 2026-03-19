# UI/UX Modernization Plan

## Current-State Summary
- The UI is implemented as page-level React views with direct `useState`/`useEffect` fetching.
- A design direction exists in `frontend/tailwind.config.ts`, but shared UI primitives are minimal.
- Layout is handled globally in `frontend/src/components/Layout.tsx`.
- Several routes referenced in navigation do not exist yet, including governance and docs views.
- Feedback patterns rely heavily on `alert()` and `confirm()`.

## Information Architecture

### Primary Navigation
- Overview
- Inventory
- Syncs
- Operations
- Governance
- Docs

### Secondary Navigation
- Inventory: Applications, Databases, Instances, SharePoint Connections, Sites, Lists
- Syncs: Definitions, Mappings, Targets, Schedules, CDC
- Operations: Runs, Drift, Ledger, Replication Health, Alerts
- Governance: Roles, Audit Log, Approvals, Feature Flags

### Global Elements
- Global search in header for sync definitions, databases, lists, and runs
- Command palette for quick navigation and actions
- Settings/profile/admin utilities grouped in header menu
- Breadcrumbs on all detail pages

## Design System Baseline

### Typography
- Keep IBM Plex Sans, Space Grotesk, IBM Plex Mono already defined in `frontend/tailwind.config.ts`
- Standardize sizes: 12, 14, 16, 20, 24, 30, 36

### Spacing
- Standardize on 4, 8, 12, 16, 24, 32, 48

### Color Tokens
- Promote existing light/dark tokens into semantic tokens:
  - surface
  - surface-muted
  - text-primary
  - text-secondary
  - border-subtle
  - primary
  - success
  - warning
  - danger

### Interaction
- Replace native browser alerts with toast and modal primitives
- Standardize loading with skeletons and inline status banners
- Use drawers for entity inspection and modals for destructive confirmation

## Standard Interaction Patterns
- Forms use sectioned layouts, inline validation, and sticky footers
- Tables use sticky headers, filter bars, row actions, and bulk actions
- Detail views use split-pane or tabbed detail patterns
- Long-running operations show non-blocking progress and final status
- Empty states always explain why the page is empty and what to do next

## High-Friction Screens

### Dashboard
- Problem: mixed concerns, high density, expensive visuals, weak information hierarchy
- Fix: split into health overview, recent runs, drift, and quick actions

### Sync Definition Detail
- Problem: too many responsibilities on one screen
- Fix: convert to tabbed split-view with sticky action bar and right-side detail panes

### Settings
- Problem: overloaded with integrations, secrets, and profile concerns
- Fix: move integrations into Inventory/Admin and keep Settings user-centric

### Database Instances
- Problem: operational and inventory concerns are blended
- Fix: table-based management view with health, failover, and verification flows

### Runs
- Problem: list-only history without rich drill-down or recovery flow
- Fix: add filters, run detail drawer, grouped failures, retry actions

## Accessibility Upgrade Priorities
- Add semantic landmarks and a skip link
- Ensure visible focus states on all controls
- Add accessible dialog and drawer patterns
- Add table captions and proper headers
- Add error summaries and live regions for async feedback
- Support reduced motion preferences

## 40-Item Consistency Checklist
- [ ] Page title matches route intent
- [ ] Breadcrumbs present on detail pages
- [ ] One primary CTA per view
- [ ] Secondary actions are visually secondary
- [ ] Filters sit above data views
- [ ] Search placeholders are task-specific
- [ ] Empty state includes next action
- [ ] Error state includes retry path
- [ ] Loading state uses skeletons
- [ ] Cards use consistent padding
- [ ] Sections use consistent vertical rhythm
- [ ] Labels align consistently
- [ ] Required fields marked consistently
- [ ] Help text placement consistent
- [ ] Inline validation placement consistent
- [ ] Destructive controls styled consistently
- [ ] Status chips use semantic colors
- [ ] Dates formatted consistently
- [ ] Durations formatted consistently
- [ ] IDs use monospace
- [ ] Row actions align consistently
- [ ] Overflow menus placed consistently
- [ ] Toast location is consistent
- [ ] Success copy is concise
- [ ] Error copy is actionable
- [ ] Focus order is logical
- [ ] Keyboard-only operation is possible
- [ ] Icon buttons have labels
- [ ] Dialogs trap and restore focus
- [ ] Tables have captions/labels
- [ ] Responsive collapse rules are defined
- [ ] Mobile CTAs remain visible
- [ ] Active nav state matches route
- [ ] Child routes inherit correct nav state
- [ ] Information density matches task complexity
- [ ] Advanced options are progressively disclosed
- [ ] Filters are discoverable
- [ ] Action placement is predictable
- [ ] No dead links in visible navigation
- [ ] Visual language is consistent across pages

## Delivery Order
1. Shared feedback and dialog primitives
2. Navigation and route cleanup
3. Table/filter/search primitives
4. Sync detail redesign
5. Runs and operations workspace redesign
