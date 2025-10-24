# SeedTest API: DB-backed CI job (Postgres + Alembic + tests), lint/mypy fixes, and workflow cleanup

## Summary

This PR integrates a dedicated SeedTest API job into the main CI pipeline that provisions Postgres, runs Alembic migrations, and executes the DB-backed test suite. It also includes small lint/typecheck fixes and removes a standalone example workflow to keep CI configuration clean.

## Changes

- CI: Add "SeedTest API - DB Tests" job to `.github/workflows/ci.yml`:
  - Postgres service with healthchecks
  - Python setup and dependency install (with fallback if root requirements are missing)
  - Alembic upgrade using `apps/seedtest_api/alembic.ini`
  - Run pytest for `apps/seedtest_api/tests` with `DATABASE_URL` and `LOCAL_DEV=true`

- Lint/Typecheck: Fix minor flake8 issues and keep mypy clean in SeedTest API:
  - Wrap long condition in `apps/seedtest_api/deps.py` (E501)
  - Correct logger placement/blank lines in `apps/seedtest_api/services/result_service.py` (E303)

- Cleanup: Remove `.github/workflows/seedtest-api-migration-example.yml` to avoid duplication with the integrated CI job.

## Motivation

Make DB-backed tests a first-class part of CI to catch migration/runtime issues early and ensure the SeedTest API remains deployable with consistent database schema. Reduce maintenance overhead by consolidating workflows.

## Verification

- Local: Full SeedTest API suite passes with the Postgres + Alembic harness (52 passed, 2 skipped).
- Lint: flake8 is clean for `apps/seedtest_api` after minor fixes.
- Typecheck: mypy reports no issues for configured SeedTest API files.

## Risks and impact

- Minimal. New CI job is gated to run only when SeedTest API paths change (using the existing "changes" job output) and uses isolated Postgres service.
- Removal of the example workflow eliminates duplication; the new job in `ci.yml` supersedes it.

## Rollout and backout

- Rollout: Merging this PR will start running DB-backed SeedTest tests in the main pipeline when changes are detected in `apps/seedtest_api/**`.
- Backout: Revert this PR to restore the previous CI state; optionally re-introduce the example workflow if needed.

## Notes for reviewers

- The CI job installs dependencies with a best-effort fallback in case `requirements.txt` isn’t present at repo root.
- Alembic is executed with `PYTHONPATH=apps` and config at `apps/seedtest_api/alembic.ini` to match local/dev harness.
