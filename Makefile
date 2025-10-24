SHELL := /bin/bash

.PHONY: db-test-listing-auth db-test-listing-all db-test

# Host DB port for local Postgres started by docker-compose.db.yml (default 5432)
DB_PORT ?= 5432

# Run listing auth smoke tests with local Postgres (compose + Alembic + pytest)
db-test-listing-auth:
	DB_PORT=$(DB_PORT) apps/seedtest_api/scripts/dev_db_test.sh apps/seedtest_api/tests/test_results_list_auth.py

# Run all listing-related DB tests
db-test-listing-all:
	DB_PORT=$(DB_PORT) apps/seedtest_api/scripts/dev_db_test.sh apps/seedtest_api/tests/test_results_list_*.py

# Generic pass-through; use: make db-test PYTEST_ARGS="apps/seedtest_api/tests/test_results_list_filters.py"
db-test:
	DB_PORT=$(DB_PORT) apps/seedtest_api/scripts/dev_db_test.sh $(PYTEST_ARGS)

.PHONY: test-seedtest-api-all
# Run the full seedtest_api test suite (unit + DB-backed)
test-seedtest-api-all:
	DB_PORT=$(DB_PORT) apps/seedtest_api/scripts/dev_db_test.sh apps/seedtest_api/tests

.PHONY: lint-seedtest-api
# Run flake8 lint scoped to seedtest_api using its virtualenv if available
lint-seedtest-api:
	@if [ -x apps/seedtest_api/.venv/bin/flake8 ]; then \
		apps/seedtest_api/.venv/bin/flake8 apps/seedtest_api ; \
	else \
		flake8 apps/seedtest_api ; \
	fi

.PHONY: typecheck-seedtest-api
# Run mypy type checks for seedtest_api using its mypy.ini; prefer local venv if present
typecheck-seedtest-api:
	@if [ -x apps/seedtest_api/.venv/bin/mypy ]; then \
		apps/seedtest_api/.venv/bin/mypy --config-file apps/seedtest_api/mypy.ini ; \
	else \
		mypy --config-file apps/seedtest_api/mypy.ini ; \
	fi
