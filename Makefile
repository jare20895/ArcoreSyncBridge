FRONTEND_DIR := frontend
BACKEND_DIR := backend
BACKEND_PYTHON := $(shell if [ -x "$(BACKEND_DIR)/venv/bin/python" ]; then echo "venv/bin/python"; else echo "python3"; fi)

.PHONY: frontend-lint frontend-typecheck frontend-build backend-test ci

frontend-lint:
	cd $(FRONTEND_DIR) && npm run lint

frontend-typecheck:
	cd $(FRONTEND_DIR) && npm run typecheck

frontend-build:
	cd $(FRONTEND_DIR) && npm run build

backend-test:
	cd $(BACKEND_DIR) && PYTHONPATH=$(PWD)/$(BACKEND_DIR) $(BACKEND_PYTHON) -m pytest tests

ci: frontend-lint frontend-typecheck frontend-build backend-test
