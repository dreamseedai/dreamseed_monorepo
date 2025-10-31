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

# Apply Alembic migrations to the configured DATABASE_URL
alembic-upgrade:
	cd $(CURDIR) && \
	if [ -f apps/seedtest_api/alembic.ini ]; then \
		PYTHONPATH=apps alembic -c apps/seedtest_api/alembic.ini upgrade head; \
	else \
		cd apps/seedtest_api && alembic upgrade head; \
	fi

# Run the IRT calibration job once (requires R_IRT_BASE_URL configured)
job-mirt-calibrate:
	. .venv/bin/activate && PYTHONPATH=../..:.. python -m seedtest_api.jobs.mirt_calibrate

# Backfill topic-level theta from general ability across observed topics
job-backfill-topic-theta:
	. .venv/bin/activate && PYTHONPATH=../..:.. python -m seedtest_api.jobs.backfill_topic_theta

# Recompute weekly KPIs for users (week_start defaults to current ISO Monday)
job-recompute-weekly-kpi:
	. .venv/bin/activate && PYTHONPATH=../..:.. python -m seedtest_api.jobs.recompute_weekly_kpi

# One-shot: Calibrate -> Backfill topic theta -> Recompute KPIs
pipeline-calibrate-and-kpi:
	$(MAKE) job-mirt-calibrate
	$(MAKE) job-backfill-topic-theta
	$(MAKE) job-recompute-weekly-kpi

# Verify table counts for IRT and metrics
verify:
	. .venv/bin/activate && PYTHONPATH=../..:.. python -m seedtest_api.jobs.verify_counts

# Combined ops verification: table counts + key API calls with LOCAL_DEV=true
ops-verify:
	$(MAKE) verify
	. .venv/bin/activate && PYTHONPATH=../..:.. LOCAL_DEV=true python -m seedtest_api.jobs.ops_verify

# Run FastAPI locally on port 8002
run:
	. .venv/bin/activate && PYTHONPATH=../..:.. uvicorn seedtest_api.main:app --reload --port 8002
