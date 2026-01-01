# Arcore SyncBridge UI/UX Design Specification

This document defines the frontend experience for Arcore SyncBridge. The UI is a modern, confident admin console with a top tabbed navigation, left sidebar sub-sections, and a right-aligned utility cluster (dark mode, settings, profile).

## 1. Experience goals
- Clear separation between configuration, operations, and governance.
- Reduce cognitive load for complex sync setups.
- Operational trust: status, auditability, and drift visibility are always accessible.
- Fast onboarding through guided provisioning and sensible defaults.

## 2. Information architecture

### 2.1 Primary tabs (top banner)
- Dashboard
- Connections
- Sync Definitions
- Runs and Ledger
- Governance
- Docs

Each primary tab owns a left sidebar with sub-sections, filters, and quick actions.

### 2.2 Sidebar sections by tab

Dashboard
- Overview
- Throughput
- Alerts
- Drift Summary

Connections
- Postgres
- SharePoint
- Secrets
- Verification Logs

Sync Definitions
- Definitions List
- Targets
- Field Mappings
- Sharding Rules
- Provisioning

Runs and Ledger
- Run History
- Ledger Browser
- Errors
- Replays

Governance
- RBAC
- Audit Logs
- Risk Controls

Docs
- Getting Started
- API Reference
- Runbooks

## 3. Layout and navigation

### 3.1 Top banner (fixed)
- Left: product logo and name
- Center: primary tabs (horizontal, pill-style)
- Right: utility cluster
  - Dark mode toggle
  - Settings icon
  - User profile avatar (dropdown)

### 3.2 Left sidebar (contextual)
- Persistent within each primary tab
- Collapsible sections for filters and advanced tools
- Supports nested sub-sections with clear visual hierarchy

### 3.3 Main workspace
- Header: page title, breadcrumbs, primary action button
- Content: cards, tables, and diagrams
- Right panel (optional): inspector drawer for details

## 4. Design system

### 4.1 Color palette
Light mode
- Background: #F5F4F2
- Surface: #FFFFFF
- Primary: #1B4F72
- Accent: #D97706
- Success: #2F855A
- Warning: #B45309
- Danger: #B91C1C
- Text primary: #1F2933
- Text secondary: #52606D

Dark mode
- Background: #0F1720
- Surface: #141E2A
- Primary: #7FB3D5
- Accent: #F4B266
- Success: #6EE7B7
- Warning: #FBBF24
- Danger: #F87171
- Text primary: #E2E8F0
- Text secondary: #94A3B8

### 4.2 Typography
- Primary: IBM Plex Sans
- Secondary: Space Grotesk (for headings and tab labels)
- Mono: IBM Plex Mono (schema names, SQL, and payload previews)

### 4.3 Spacing and layout
- Base unit: 8 px
- Sidebar width: 260 px (collapsed 72 px)
- Top banner height: 64 px
- Content max width: 1200 px
- Table row height: 48 px

### 4.4 Elevation and borders
- Subtle layered depth: 1px borders + soft shadows
- Cards: 1px solid #E5E7EB (light) or #1F2A37 (dark)

## 5. Component guidelines

### 5.1 Tabs and sidebar
- Tabs show current state with bold label and accent underline.
- Sidebar active item uses a left bar accent and background tint.

### 5.2 Data tables
- Compact view for high-density lists
- Inline status chips (Success, Warning, Error)
- Sticky header with filter controls

### 5.3 Forms
- Multi-step wizards for provisioning and sharding rules
- Inline validation with descriptive error text
- Preview panel for mapping results

### 5.4 Cards and charts
- Dashboard tiles: trend, last run, error count, queue depth
- Consistent chart palette across tabs

### 5.5 Modals and drawers
- Confirmation modals for destructive actions
- Right-side drawer for ledger detail inspection

## 6. Component inventory (frontend)

### 6.1 Navigation and layout
- Top banner tabs: default, active, hover, disabled, overflow state
- Left sidebar: section headers, nested items, collapsed mode, pin/favorite
- Breadcrumbs: clickable hierarchy with truncation

### 6.2 Actions and controls
- Buttons: primary, secondary, ghost, danger, icon-only
- Button states: default, hover, focus, disabled, loading
- Icon buttons: settings, theme toggle, refresh, filters

### 6.3 Inputs and forms
- Text input, textarea, numeric, select, multiselect
- Date picker, time range, cron editor
- Toggle, checkbox, radio group
- Inline validation: error, warning, success states

### 6.4 Data display
- Tables: compact and comfortable density, sortable headers, sticky filters
- Status chips: Success, Warning, Error, Paused, Running
- Code blocks: schema and payload previews
- Key-value lists: connection details and run metadata

### 6.5 Feedback and system states
- Toasts: success, warning, error
- Banners: throttling alert, degraded mode, maintenance
- Loaders: skeleton rows, inline spinners, page-level loading
- Empty states: no data, no connections, no runs

### 6.6 Overlays
- Right-side drawer: ledger details, run summary, field mapping preview
- Modal: destructive confirmations, credential entry
- Popover: quick filters, field mapping hints

### 6.7 Visualization
- KPI cards: throughput, error rate, queue depth, last run
- Trend charts: time series for runs and latency
- Diagram viewer: data flow and topology previews

### 6.8 Utilities
- Theme toggle (light/dark)
- Settings panel
- User profile menu: account, roles, sign out

## 7. Page-by-page wireframe specification

### 7.1 Dashboard
- Overview: KPI cards, run status banner, queue depth gauge
- Throughput: time series chart, per-definition breakdown
- Alerts: list with severity filters, acknowledge action
- Drift Summary: table of drifted items with re-run action

### 7.2 Connections
- Postgres list: connection cards, verify button, status chip
- Postgres detail: key-value panel, verification logs table
- SharePoint list: site targets, Graph scope status, verify action
- Secrets: masked values, rotate action, audit trail
- Verification Logs: searchable table with result and duration

### 7.3 Sync Definitions
- Definitions list: table with status, mode, last run, actions
- Definition detail: tabs for Mapping, Targets, Sharding, Schedule, Runs
- Field Mappings: side-by-side mapping table, transform dropdowns
- Targets: multi-select list picker, default target toggle, priority ordering
- Sharding Rules: rule builder with drag-and-drop order, default fallback, coverage indicator
- Provisioning: stepper with schema preview and confirmation

### 7.4 Runs and Ledger
- Run History: timeline table, filters by status and definition
- Run detail: summary cards, step status, error list
- Ledger Browser: searchable table with source_pk and sp_item_id
- Errors: grouped by error type with retry action
- Replays: list of replay jobs with progress

### 7.5 Governance
- RBAC: role list, permissions matrix, assign user action
- Audit Logs: immutable event table with export
- Risk Controls: checklist and policy status cards

### 7.6 Docs
- Getting Started: step checklist with inline links
- API Reference: endpoint list with request/response examples
- Runbooks: operational guides with severity tags

### 7.7 Global pages
- Settings: preferences, notification channels, retention windows
- Profile: account details, roles, session management

## 8. Key user flows

### 8.1 Provisioning a new sync definition
1. Select Postgres connection and source table.
2. Select SharePoint site and add one or more target lists (existing or new).
3. Mark a default target list and order routing rules.
4. Review field mappings and transformations.
5. Configure sharding rules and validate rule order.
6. Run provisioning and save definition.

### 8.2 Monitoring a run
1. Navigate to Runs and Ledger.
2. Filter by sync definition or time range.
3. Inspect run details in drawer.
4. Open ledger entries for drift resolution.

### 8.3 Handling drift
1. View Drift Summary on Dashboard.
2. Open affected definition.
3. Compare source vs destination values.
4. Re-run push or mark as accepted change.

## 9. Interaction and motion
- Page load: subtle fade and staggered card reveal.
- Hover: highlight rows and cards with a slight lift.
- Progress: use deterministic stepper for provisioning.

## 10. Accessibility
- WCAG AA contrast targets for both themes.
- Keyboard navigation for tabs, sidebar, and tables.
- Visible focus rings on all interactive elements.
- Avoid color-only status indicators (use labels and icons).

## 11. Responsive behavior
- Desktop: full layout with top tabs and sidebar.
- Tablet: sidebar collapses by default, tabs remain.
- Mobile: tabs become scrollable with a drawer for sub-sections.

## 12. Content and tone
- Use clear, direct language for operational tasks.
- Avoid jargon in user-facing labels.
- Surface guidance inline where users make decisions.

## 13. Wireframe (layout outline)

```
+---------------------------------------------------------------+
| Logo  Dashboard  Connections  Syncs  Runs  Governance  Docs   |  Dark  Settings  User
+----------------------+----------------------------------------+
| Sidebar              | Page Title       [Primary Action]      |
| - Section A          |----------------------------------------|
|   - Item 1           | Cards / Tables / Diagrams              |
|   - Item 2           |                                        |
| - Section B          |                                        |
+----------------------+----------------------------------------+
```
