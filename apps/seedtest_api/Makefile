SHELL := /bin/bash

# Convenience targets for local DB-backed tests

# Spin up Postgres (docker compose), run alembic, then run listing auth smoke tests
db-test-listing-auth:
	./scripts/dev_db_test.sh apps/seedtest_api/tests/test_results_list_auth.py

# Run all DB-backed result listing tests (filters, auth, etc.)
db-test-listing-all:
	./scripts/dev_db_test.sh apps/seedtest_api/tests/test_results_list_*.py

# Generic: pass-through to dev_db_test with custom pytest args
db-test:
	./scripts/dev_db_test.sh $(args)

# Run the full test suite for this package
test-all:
	./scripts/dev_db_test.sh apps/seedtest_api/tests

# --- Questions-specific helpers ---
.PHONY: questions-db-migrate questions-db-tests

# Apply Alembic migrations only (no tests), using DATABASE_URL or default localhost DSN
questions-db-migrate:
	cd apps/seedtest_api && alembic upgrade head

# Run questions org/global authorization tests against a DB (uses Postgres if DATABASE_URL is provided; otherwise will spin up a local DB and run Alembic via helper)
questions-db-tests:
	./scripts/dev_db_test.sh apps/seedtest_api/tests/test_questions_org_authorization.py
