# Feature Spec: Audit Explorer

## Goal
- Provide immutable visibility into administrative and configuration changes.

## Scope
- Entity change history
- Actor and timestamp attribution
- Before/after diff payloads
- Filtering and export

## Acceptance Criteria
- User can filter audit events by entity, action, actor, and date range
- User can open event detail with before/after diff
- Sensitive fields are masked in audit payloads
- Export supports CSV for filtered results
- High-risk actions are prominently tagged

## API Changes
- Audit log list endpoint
- Audit event detail endpoint

## Data Changes
- `audit_log`
