# 30 / 60 / 90 Day Roadmap

## 30 Days

### Objectives
- Establish baseline safety and developer workflow
- Remove the highest-risk security gaps
- Make the repo buildable and testable in CI

### Deliverables
- Auth/RBAC skeleton
- CORS allowlist
- ESLint and backend test tooling
- CI quality gates
- Shared toast/dialog/skeleton primitives
- Navigation cleanup

### Dependencies
- Azure AD application configuration
- Agreement on role model

### Risks
- Auth integration touches both apps and the API surface

### Expected Impact
- Significant reduction in operational and security risk

## 60 Days

### Objectives
- Improve operational maturity and user workflows
- Tighten data integrity and auditability

### Deliverables
- Async manual sync orchestration
- Run retry/requeue center
- Audit log
- First schema integrity migration pack
- Runs and drift UX refresh
- Saved views and filter persistence

### Dependencies
- Stable job orchestration contract
- Migration backfill plan

### Risks
- Data migration sequencing

### Expected Impact
- Lower MTTR and better operational confidence

## 90 Days

### Objectives
- Reach enterprise-ready governance and scale posture

### Deliverables
- Approval workflows
- Teams alerts
- Data quality rules
- Feature flags
- Organization/tenant boundary support
- Observability dashboards and SLOs

### Dependencies
- Stable audit/event model
- Role and organization schema

### Risks
- Cross-cutting scope across UI, API, and data model

### Expected Impact
- Stronger governance, safer rollout control, better scale readiness
