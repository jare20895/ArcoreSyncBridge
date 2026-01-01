# Contributing to Arcore SyncBridge

Thank you for your interest in contributing. This project is in active design and early implementation.

## Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

## Local setup (planned)
1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in credentials.
3. Create a virtualenv and install API dependencies.
4. Install UI dependencies in the frontend workspace.
5. Run API, worker, and UI in separate terminals.

## Development workflow
- Create a feature branch from `main`.
- Add or update tests for new behavior.
- Run linters and formatters before opening a PR.
- Keep PRs focused and describe any breaking changes.

## Coding standards
- Python: ruff + black
- TypeScript: eslint + prettier
- Docs: update relevant Markdown when behavior changes

## Pull requests
- Link to the issue or design decision.
- Include screenshots for UI changes.
- Note any schema or migration impact.
