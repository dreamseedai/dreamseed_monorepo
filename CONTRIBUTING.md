# Contributing to DreamSeed

Thanks for contributing! This guide covers basic dev setup and our preferred workflows.

## Pre-commit hooks (recommended)

We use pre-commit to catch common issues locally before you push. Enable it once per clone:

```bash
pip install pre-commit
pre-commit install
```

This repo config runs hygiene checks plus flake8 and mypy for the SeedTest API package (`apps/seedtest_api`). You can run all hooks on demand:

```bash
pre-commit run --all-files
```

## SeedTest API quick dev

- Lint: `make lint-seedtest-api`
- Typecheck: `make typecheck-seedtest-api`
- Full test suite (applies Alembic, runs DB-backed tests):
  
  ```bash
  make test-seedtest-api-all
  ```

## Branching and commits

- Use short, descriptive branches: `feature/*`, `fix/*`, `chore/*`
- Prefer Conventional Commits in messages, e.g.:
  - `feat(seedtest): add ability percentile`
  - `fix(results): handle IntegrityError race`
  - `chore(ci): add Postgres service job`

## Pull Requests

- Include a brief summary (what/why)
- If schema or migration changes: call it out in the PR and ensure Alembic included
- For SeedTest API: link to `docs/PR_SEEDTEST_CI_UPDATE.md` format as a reference for structure

## Code style

- Python: Black + isort, flake8, mypy
- Keep functions small, add docstrings for service entrypoints
- Prefer tests: include a happy path and 1–2 edge cases

## Questions

Open a discussion or file an issue if you’re unsure about any of the above.