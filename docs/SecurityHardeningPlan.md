# Security Hardening Plan

## Current Risks
- No inbound authentication or authorization layer
- Open CORS policy
- Plaintext secret storage in database records
- Unsafe SQL composition against source databases
- Development defaults for credentials in runtime code
- No audit trail for sensitive admin actions

## Phase 1: Baseline Hardening
- Add application auth using Azure AD JWT validation
- Define RBAC roles: viewer, operator, editor, admin, platform_admin
- Replace wildcard CORS with an environment-driven allowlist
- Remove fallback default credentials from runtime services
- Mask secrets in UI and never return them in API responses
- Introduce request validation and centralized exception handling

## Phase 2: Secret Management
- Move DB passwords and Graph client secrets to encrypted storage
- Preferred target: external vault/KMS
- Interim fallback: envelope encryption with key rotation support
- Add secret rotation flow and audit entries

## Phase 3: Governance
- Add audit log for create/update/delete/run/failover/secret actions
- Add approval workflow for destructive or high-risk changes
- Add feature flags for staged rollout of new sync behaviors

## API Hardening Standards
- Standard response envelope
- Standard error envelope with machine-readable code
- Rate limiting for expensive operations
- Idempotency keys for retries and task-triggering endpoints
- Optimistic concurrency for config edits
- Pagination, filtering, and sorting standards

## Threat Model Focus Areas
- Unauthorized admin access
- Secret leakage
- SQL injection via dynamic identifier composition
- Duplicate or replayed background jobs
- Excessive Graph throttling and external dependency failure
- CDC lag causing replication slot/WAL growth

## Verification Checklist
- [ ] All admin routes require auth
- [ ] Role checks exist for mutating actions
- [ ] Unknown origins are rejected
- [ ] Secrets are encrypted or externalized
- [ ] No secret values appear in logs
- [ ] Dynamic SQL uses safe identifier handling
- [ ] Audit entries exist for high-risk actions
- [ ] Readiness checks include DB and Redis
- [ ] Alerting exists for CDC lag and repeated failures
