# Implementation Checklist

## Architecture
- [ ] Establish module boundaries for inventory, sync, operations, and security
- [ ] Normalize dependency injection to a single `get_db` source
- [ ] Standardize API envelopes and exception handling
- [ ] Move manual sync execution to async job orchestration

## UI/UX
- [ ] Add dialog, toast, and skeleton primitives
- [ ] Remove native browser `alert` and `confirm` usage
- [ ] Fix dead navigation routes
- [ ] Add breadcrumbs and command palette
- [ ] Standardize tables, filters, and form patterns

## Security
- [ ] Add Azure AD-backed authentication
- [ ] Add RBAC and route guards
- [ ] Restrict CORS by environment
- [ ] Encrypt or externalize secrets
- [ ] Remove runtime default credentials
- [ ] Add audit log for sensitive actions

## Data Model
- [ ] Add missing foreign keys
- [ ] Add missing unique constraints
- [ ] Add operational indexes
- [ ] Add audit and governance tables

## Observability
- [ ] Introduce structured logs
- [ ] Propagate request/run/task correlation IDs
- [ ] Define key metrics and dashboards
- [ ] Add liveness and readiness checks

## Testing
- [ ] Add frontend lint/type/build checks
- [ ] Add backend lint/type/test checks
- [ ] Add migration validation in CI
- [ ] Add API contract tests
- [ ] Add accessibility smoke tests

## DevOps
- [ ] Create production-oriented Dockerfiles
- [ ] Add CI workflow with quality gates
- [ ] Add dependency and security scanning
- [ ] Add release checklist and rollback validation

## Feature Delivery
- [ ] Build sync definition wizard
- [ ] Add run retry/requeue center
- [ ] Add analytics dashboard
- [ ] Add audit explorer
- [ ] Add approval workflow
- [ ] Add Teams alert integration
