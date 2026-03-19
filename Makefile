FRONTEND_DIR := frontend
BACKEND_DIR := backend

.PHONY: frontend-lint frontend-typecheck frontend-build backend-test ci

frontend-lint:
	cd $(FRONTEND_DIR) && npm run lint

frontend-typecheck:
	cd $(FRONTEND_DIR) && npm run typecheck

frontend-build:
	cd $(FRONTEND_DIR) && npm run build

backend-test:
	cd $(BACKEND_DIR) && python -m pytest

ci: frontend-lint frontend-typecheck frontend-build backend-test
