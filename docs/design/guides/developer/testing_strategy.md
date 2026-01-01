# Testing Strategy

## Unit tests
- Mapping rules, sharding logic, ledger hash generation
- Framework: pytest

## Integration tests
- Postgres + Redis via docker-compose
- Graph API mocked or using a sandbox tenant

## End-to-end tests
- Provision a list, push sync, verify list contents
- Optional UI flows with Playwright once UI is available

## Coverage targets
- Core sync engine: 85 percent line coverage
- API endpoints: 70 percent line coverage
