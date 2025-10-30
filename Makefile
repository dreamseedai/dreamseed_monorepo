# Convenience targets for SeedTest Question Bank and Admin Front E2E

.PHONY: questions-db-migrate questions-db-test questions-db-all \
	test-admin-e2e test-admin-e2e-setup

# Ensure DATABASE_URL is set in your environment before running
questions-db-migrate:
	alembic upgrade head

questions-db-test:
	pytest -q apps/seedtest_api/tests/test_questions_db_integration.py
	pytest -q apps/seedtest_api/tests/test_questions_db_keyset_filters.py
	pytest -q apps/seedtest_api/tests/test_questions_jwt_roles.py

questions-db-all: questions-db-migrate questions-db-test
	@echo "Migrations applied and Question Bank DB tests executed."

# --- Admin Front (Next.js) E2E ---
# Quick setup for Playwright (installs node modules and browsers)
test-admin-e2e-setup:
	cd admin_front && npm ci && npx playwright install --with-deps

# Run Playwright E2E against admin_front using its own config and build/start flow
# Optional: pass extra Playwright args via ARGS, e.g.,
#   make test-admin-e2e ARGS="--grep @smoke"
test-admin-e2e:
	cd admin_front && npm run test:e2e -- $(ARGS)

# --- Smoke tests (backend + frontend) ---
.PHONY: smoke smoke-legacy smoke-backend smoke-frontend

# Defaults (can be overridden via CLI like `make smoke-backend BACKEND_URL=http://...`)
BACKEND_URL ?= http://127.0.0.1:8012
API_PATH ?= /api/seedtest/questions?page_size=1
TIMEOUT ?= 5
SMOKE_STRICT ?= 1
EXPECT_DATA_SOURCE ?=
FRONTEND_URL ?= http://127.0.0.1:3030

smoke:
	BACKEND_URL=$(BACKEND_URL) API_PATH=$(API_PATH) TIMEOUT=$(TIMEOUT) SMOKE_STRICT=$(SMOKE_STRICT) EXPECT_DATA_SOURCE=$(EXPECT_DATA_SOURCE) FRONTEND_URL=$(FRONTEND_URL) bash scripts/smoke-local.sh

smoke-legacy:
	BACKEND_URL=$(BACKEND_URL) API_PATH=$(API_PATH) TIMEOUT=$(TIMEOUT) SMOKE_STRICT=1 EXPECT_DATA_SOURCE=legacy FRONTEND_URL=$(FRONTEND_URL) bash scripts/smoke-local.sh

smoke-backend:
	BACKEND_URL=$(BACKEND_URL) API_PATH=$(API_PATH) TIMEOUT=$(TIMEOUT) SMOKE_STRICT=$(SMOKE_STRICT) SKIP_FRONTEND=1 EXPECT_DATA_SOURCE= bash scripts/smoke-local.sh

smoke-frontend:
	bash -c 'FE_STATUS=$$(curl -sS --max-time $(TIMEOUT) -o /dev/null -w "%{http_code}" "$(FRONTEND_URL)" || true); \
	if [ "$$FE_STATUS" = "200" ]; then echo "Frontend OK ($$FRONTEND_URL)"; else echo "Frontend FAIL (HTTP $$FE_STATUS)"; exit 1; fi'
