# SeedTest API – Local Run Guide

This guide helps you run the SeedTest FastAPI service locally for manual testing and development.

## Prerequisites

- Python 3.11+ (virtualenv recommended)
- PostgreSQL (local server or container)
- Optional: Make, Docker (only if you prefer containers)

## 1) Environment setup

Create a virtual environment and install dependencies. If your repo uses a shared `requirements.txt`, install from it; otherwise install the core packages listed below.

```bash
# Create & activate venv (Linux/macOS)
python3 -m venv .venv
source .venv/bin/activate

# Option A: shared requirements (recommended if present at repo root)
pip install -r requirements.txt

# Option B: minimal direct install for SeedTest API
pip install \
  fastapi uvicorn[standard] \
  sqlalchemy psycopg2-binary alembic \
  pydantic pydantic-settings python-dotenv \
  httpx python-jose
```

Create a local env file specifically for SeedTest API. The settings loader automatically reads `.env` from this package directory.

```bash
# From repo root
cp apps/seedtest_api/.env.example apps/seedtest_api/.env 2>/dev/null || true
# Or create a minimal one:
cat > apps/seedtest_api/.env << 'EOF'
# Loosen auth and allow no Authorization header for local experiments
LOCAL_DEV=true

# Postgres URL (adjust host/port/user/password/db)
DATABASE_URL=postgresql+psycopg2://user:pass@127.0.0.1:5432/dreamseed_db

# JWT verification settings (ignored when LOCAL_DEV=true)
JWKS_URL=https://auth.dreamseedai.com/.well-known/jwks.json
JWT_ISS=https://auth.dreamseedai.com/
JWT_AUD=seedtest-api
# JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----...-----END PUBLIC KEY-----
EOF
```

Notes
- The settings file is `apps/seedtest_api/settings.py`. It reads `.env` from the same folder.
- With `LOCAL_DEV=true`, the service accepts requests without Authorization on most endpoints and automatically injects a `dev-user` identity for ease of testing.

## 2) Database and migrations

Ensure a local Postgres instance is running and that your `DATABASE_URL` points to a created database.

Apply Alembic migrations for SeedTest API:

```bash
# From repo root, add apps/ to PYTHONPATH so alembic can import modules
PYTHONPATH=apps alembic -c apps/seedtest_api/alembic.ini upgrade head
```

If you run into an Alembic version length issue (VARCHAR(32)), see repo README section “Alembic version length” for details. The above command uses the project’s Alembic config which already sets a longer version column type.

Optional: You can also use the DB test harness script which ensures migrations are applied before running tests:

```bash
DB_PORT=5433 bash apps/seedtest_api/scripts/dev_db_test.sh --help
```

## 3) Start the API server

Run the FastAPI app with Uvicorn (from the repo root):

```bash
PYTHONPATH=apps uvicorn seedtest_api.main:app --reload --port 8002
```

- OpenAPI docs: http://127.0.0.1:8002/docs
- Healthcheck: GET http://127.0.0.1:8002/api/seedtest/health

## 4) Try the exam flow locally

With `LOCAL_DEV=true`, you can create a session and submit answers without a token.

```bash
# Create a session
curl -s -X POST http://127.0.0.1:8002/api/seedtest/exams \
  -H 'Content-Type: application/json' \
  -d '{"exam_id":"math_adaptive"}'
# → { "exam_session_id": "<UUID>", ... }

# Submit a few answers; when finished, the server computes the result best-effort
SESSION_ID=<UUID_FROM_CREATE>
for i in 1 2 3 4 5; do
  curl -s -X POST http://127.0.0.1:8002/api/seedtest/exams/$SESSION_ID/response \
    -H 'Content-Type: application/json' \
    -d '{"question_id":"1","answer":"C","elapsed_time":3}' | jq .
done

# Explicitly compute/refresh result (idempotent)
curl -s -X POST http://127.0.0.1:8002/api/seedtest/exams/$SESSION_ID/result | jq .

# Retrieve cached result (404 if missing or not ready)
curl -s http://127.0.0.1:8002/api/seedtest/exams/$SESSION_ID/result | jq .

# Force recompute via GET refresh
curl -s "http://127.0.0.1:8002/api/seedtest/exams/$SESSION_ID/result?refresh=true" | jq .

# PDF endpoint (stub)
curl -i http://127.0.0.1:8002/api/seedtest/exams/$SESSION_ID/result/pdf
# → 501 Not Implemented
```

Behavior summary
- POST /exams/{session_id}/result
  - 200 on success, idempotent upsert; 400 if session exists but not completed; 404 if session not found; 409 on rare conflict; 500 on compute error (also marks status=failed).
- GET /exams/{session_id}/result
  - Returns 200 only for cached, ready results by default; 404 otherwise. Pass `refresh=true` to recompute and upsert.

## 5) Authorization notes

- Local dev mode: `LOCAL_DEV=true` allows calling endpoints without passing Authorization.
- Strict mode: set `LOCAL_DEV=false` and use valid JWTs:
  - Students can access their own sessions/results.
  - Teachers can access sessions/results for their org when the service can resolve org from in-memory state. If your schema includes `exam_sessions.org_id`, the service will verify teacher org from the DB as well. Otherwise, it denies ambiguous teacher access by default.
  - Admins bypass both checks.

## 6) Troubleshooting

- “No data was collected” during tests: ensure pytest runs in the configured test path and coverage targets are set; repo `pyproject.toml` already aligns these for SeedTest API.
- Alembic errors about version length: use the provided Alembic config (above) or see repo README appendix.
- DB connection refused: confirm `DATABASE_URL` points to a reachable Postgres and that the DB exists.
- Import errors when running Uvicorn: ensure `PYTHONPATH=apps` so `seedtest_api` is importable.

## 7) Run tests locally (optional)

The DB harness will apply migrations, run tests, and write coverage artifacts:

```bash
DB_PORT=5433 bash apps/seedtest_api/scripts/dev_db_test.sh apps/seedtest_api/tests
```

This repo includes both unit tests (no DB) and DB-backed tests for results and listing endpoints. All should pass green after setup.

### Minimal Docker run with Postgres healthcheck (alternative)

아래 스니펫은 docker run으로 Postgres를 기동하고, healthcheck로 준비성을 보장한 뒤 Alembic과 전체 테스트를 실행하는 최소 절차입니다. venv 경로와 PYTHONPATH를 명시적으로 설정해 경로 문제를 방지합니다.

```bash
# 1) Postgres (로컬 5432) + readiness 대기
docker run --rm -d --name pg-seedtest -p 5432:5432 \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=seedtest_ci \
  --health-cmd="pg_isready -U postgres" --health-interval=2s --health-timeout=2s --health-retries=15 \
  postgres:15
echo "Waiting for Postgres..."; until [ "$(docker inspect -f '{{.State.Health.Status}}' pg-seedtest)" = "healthy" ]; do sleep 1; done

# 2) Alembic 마이그레이션
cd apps/seedtest_api
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/seedtest_ci
# venv 경로가 이 패키지 내부라면:
. .venv/bin/activate
alembic upgrade head

# 3) 전체 테스트 (DB 사용)
cd ../..
PYTHONPATH=apps DATABASE_URL=$DATABASE_URL pytest -q

# 4) (선택) 컨테이너 정리
docker stop pg-seedtest >/dev/null 2>&1 || true
```

참고
- venv가 레포 루트에 있다면 `. ../.venv/bin/activate`로 바꾸면 됩니다.
- 로컬 개발 편의를 원하면 `export LOCAL_DEV=true`를 추가해 토큰 검증을 우회할 수 있습니다.
- 포트 충돌 시: 예를 들어 호스트 5433을 쓰려면 `-p 5433:5432`로 바꾸고 `DATABASE_URL`도 포트 5433으로 맞추세요.

  예시(5433 사용):

  ```bash
  # 컨테이너 기동 (5433로 포워딩)
  docker run --rm -d --name pg-seedtest -p 5433:5432 \
    -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=seedtest_ci \
    --health-cmd="pg_isready -U postgres" --health-interval=2s --health-timeout=2s --health-retries=15 \
    postgres:15
  echo "Waiting for Postgres..."; until [ "$(docker inspect -f '{{.State.Health.Status}}' pg-seedtest)" = "healthy" ]; do sleep 1; done

  # DB URL도 5433으로 설정
  export DATABASE_URL=postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/seedtest_ci
  ```

- 빠른 DB 연결 점검(선택):

  ```bash
  # 5432를 쓰는 경우
  PGPASSWORD=postgres psql -h 127.0.0.1 -p 5432 -U postgres -d seedtest_ci -c 'SELECT 1;' -P pager=off
  # 5433을 썼다면 -p 5433 으로 변경
  ```

### Make targets for convenience

From the repo root, a few helpful targets are available:

```bash
# Full SeedTest API suite (unit + DB-backed) via harness
make test-seedtest-api-all

# Lint only SeedTest API (flake8)
make lint-seedtest-api

# Type-check only SeedTest API (mypy)
make typecheck-seedtest-api
```

### Pre-commit hooks (optional)

Enable pre-commit to auto-run flake8 and mypy on changed SeedTest files before each commit:

```bash
pip install pre-commit
pre-commit install
```

## 8) CI/CD and deployment considerations

- Migrations in deploy:
  - Ensure your deploy pipeline runs Alembic before starting new app versions:
    - `PYTHONPATH=apps alembic -c apps/seedtest_api/alembic.ini upgrade head`
  - The included Alembic config sets a longer version column width so long revision IDs won’t fail.

- Monorepo CI test selection:
  - Pytest discovery and coverage are scoped to `apps/seedtest_api` via `pyproject.toml`.
  - In a matrix/filtered CI, run the SeedTest API tests whenever files under `apps/seedtest_api/**` or shared infra (settings, test helpers) change.
  - Example (GitHub Actions job steps):

    ```yaml
    - name: Install deps
      run: |
        python -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
    - name: Start Postgres (service or compose)
      # Use services: in Actions or a docker compose with ports
      run: echo "start db"
    - name: Alembic upgrade
      env:
        DATABASE_URL: postgresql+psycopg2://user:pass@127.0.0.1:5432/dreamseed_db
      run: |
        source .venv/bin/activate
        PYTHONPATH=apps alembic -c apps/seedtest_api/alembic.ini upgrade head
    - name: Tests (SeedTest API)
      env:
        DATABASE_URL: postgresql+psycopg2://user:pass@127.0.0.1:5432/dreamseed_db
      run: |
        source .venv/bin/activate
        pytest -q apps/seedtest_api/tests
    ```

- Fixtures and auth in CI:
  - Tests already support a strict/loose mode via `LOCAL_DEV` and dependency overrides (`get_current_user`).
  - For unit tests, we monkeypatch `get_session_state`, DB layer, and JWT decoder as needed.
  - For DB-backed tests, the harness script `apps/seedtest_api/scripts/dev_db_test.sh` ensures migrations and connectivity.

- Performance: JSONB and indexes
  - Current pattern stores a JSONB result and parallel summary columns (score_raw, score_scaled, percentile…) with btree indexes on `session_id`, `user_id`, `org_id`, `updated_at` used by list endpoints.
  - If you later need to query inside `result_json` (e.g., topics), consider a GIN index:
    - `CREATE INDEX IF NOT EXISTS exam_results_result_gin ON exam_results USING GIN (result_json);`
  - Monitor query plans periodically (`EXPLAIN ANALYZE`) and add partial indexes if specific filters emerge.

- Logging and monitoring
  - Result computation (`result_service.compute_result`) logs exceptions and, when configured, reports to Sentry.
  - Failures are persisted by marking `exam_results.status='failed'`.
  - You can alert on failures by periodically checking:

    ```sql
    SELECT count(*) AS failed_count
    FROM exam_results
    WHERE status = 'failed'
      AND updated_at > NOW() - INTERVAL '15 minutes';
    ```

  - Add this as a scheduled monitor (Cloud SQL job, CronJob, or observability query) and page when count > 0.
  - See also: `ops/monitoring/README.md` for ready-to-use cron and Cloud Run Job snippets.

- Snapshot-friendly responses
  - Set `RESULT_EXCLUDE_TIMESTAMPS=true` (env) to omit `created_at` and `updated_at` from result responses, stabilizing contract snapshots. Default is `false`.
  - Per-request override: pass `stable=true|false` on POST/GET single-result endpoints and on the list endpoint.

- Keyset pagination cursors
  - The list endpoint now returns an opaque cursor token at `next_cursor_opaque` (base64url `v1:` JSON). This avoids exposing raw timestamps/ids in responses.
  - Requests can pass this token using the `cursor` query parameter. Backwards-compatible params `cursor_ts` and `cursor_id` are still accepted.

- Security review checklist
  - JWT verification: RS256 via JWKS or PEM (`JWT_PUBLIC_KEY`), with issuer and audience from settings.
  - Authorization: `require_session_access` gate checks admin/teacher/student with in-memory state; if schema includes `exam_sessions.org_id`, it also validates teacher org in DB; otherwise it conservatively denies ambiguous teacher access.
  - Endpoints use strict GET-vs-POST semantics: GET returns cached-only unless `refresh=true`.
  - Snapshots exclude certain fields (`score_detail`, `updated_at`) to keep the response contract stable while internal mappers remain rich.

## AI 알고리즘 및 분석 (피드백 생성) 요약

성적 리포트는 다음 요소를 종합해 개인화 피드백을 제공합니다.

- 혼합효과 모델: 충분한 응답 데이터가 누적되면 학생 능력과 문항 난이도를 동시에 추정하여 편향을 줄입니다. 설정 `ANALYSIS_ENGINE=mixed_effects`로 연결(스텁 포함).
- 성장 예측: 현재 점수/능력을 바탕으로 선형-감쇠 궤적을 추정하고, 표준오차(SE)가 있으면 목표 점수 도달 확률(예: 5회 내 150점)을 계산하여 `forecast.goals`에 포함합니다.
- 추천 엔진: 약점 토픽을 기준으로 학습 리소스를 추천합니다. 기본은 규칙 기반이며, 협업필터링/콘텐츠 기반으로 확장 가능합니다.
- 벤치마크: 개인 성적과 집단 통계(백분위 등)를 연결합니다. 전체 분포는 배치로 갱신 가능하며 조회 시 최신 값을 사용합니다.

구현 위치: `services/analysis_service.py` (`compute_analysis`) / 라우터 `routers/analysis.py`. 엔진 플러그인: `services/score_analysis.get_engine`, 추천: `services/recommendation.get_recommender`.
# SeedTest API — Exam Results

This package exposes result endpoints to compute and fetch exam session results with FastAPI + PostgreSQL (JSONB cache).

## Endpoints & Contract

- POST `/api/seedtest/exams/{session_id}/result`
  - Create or refresh the result (idempotent). Can persist to DB if configured.
  - Body (optional): `{ "force": true }` — when provided, overrides any `force` query param.
  - Query: `exam_id` (optional) — persisted when recomputing.
  - Response: 200 OK with contract below.

- GET `/api/seedtest/exams/{session_id}/result`
  - Strict fetch of cached result. Does NOT compute if missing.
  - Query: `refresh=true` — recomputes (and persists if DB configured) and returns the contract.
  - Errors: 404 when not cached and `refresh` not provided.

- GET `/api/seedtest/exams/{session_id}/result/pdf`
  - Stub: returns 501 Not Implemented.

- GET `/api/seedtest/exams/{session_id}/analysis`
  - Detailed analysis and AI feedback for a result (ability, topic insights, recommendations, forecast, benchmark).
  - Guarded by `ENABLE_ANALYSIS`; returns 501 when disabled.
  - Response: `AnalysisReport` (see `schemas/analysis.py`).

### Admin / debug

- POST `/api/seedtest/exams/{session_id}/finish`
  - Finalize a session and compute (or refresh) the result idempotently.
  - Requires `exam:write` scope (LOCAL_DEV=true bypasses auth during local development).
  - Useful for manual re-computation or when driving flows from admin tools.

Exam flow note: the exams routes automatically finalize and compute a result when a session finishes (best-effort). The admin/debug endpoint is provided for manual control or retries.

### Authentication & Authorization

- All results endpoints require JWT auth.
- Roles and access rules:
  - student: can only access their own sessions and results.
  - teacher: by default, listing is limited to their organization (org_id from token); direct session access requires same-org check.
  - admin: full access.
- LOCAL_DEV=true allows headerless local development and bypasses strict checks.
- Endpoint-level guards:
  - Per-session endpoints use a `require_session_access(session_id)` dependency to enforce ownership/org checks early.
  - Listing auto-limits students to `user_id=current_user.user_id` and teachers to `org_id=current_user.org_id` by default (non-LOCAL_DEV).

Note: To support teacher org filtering, the `exam_results` table includes `org_id` and is populated during result upsert from session state.

### Response contract (example)

```
{
  "exam_session_id": "d1f67...89",
  "user_id": "42",
  "exam_id": 5,
  "score": 128,
  "ability_estimate": 0.55,
  "standard_error": 0.32,
  "percentile": 85,
  "topic_breakdown": [
    { "topic": "대수", "correct": 5, "total": 7, "accuracy": 0.714 }
  ],
  "questions": [
    { "question_id": 101, "is_correct": true, "user_answer": "C", "correct_answer": "C", "explanation": "...", "topic": "기하" }
  ],
  "recommendations": [
    "확률통계 영역의 정답률이 25%로 낮습니다..."
  ],
  "created_at": "2025-10-18T09:45:00Z",
  "status": "ready"
}
```

### Listing (/results) filters and role rules

The listing endpoint supports keyset pagination and rich filters. Common query params:

- Pagination/sort: `limit`, `cursor_ts`, `cursor_id`, `sort_by` (created_at|updated_at), `order` (asc|desc)
- Time windows: `last_n_hours|days|weeks`, `created_last_n_hours|days|weeks`, or explicit `created_from|to`, `updated_from|to` (ISO)
- Status: `status` (multi) and/or `status_csv`
- Scores: `min_score_scaled|max_score_scaled|min_score_raw|max_score_raw|score_scaled_eq|score_raw_eq`
- Identity: `user_id`, `exam_id`
- Organization: `org_id` (teacher/admin only)

Role behavior (non-LOCAL_DEV):

- student
  - Auto-limited to `user_id=current_user.user_id`. Passing `org_id` is forbidden (403).
- teacher
  - Defaults to their `org_id` (from token) if none provided; cannot override to a different org (403).
  - Other filters (time, scores, status, exam_id) are allowed but applied within their org.
- admin
  - Unrestricted; can optionally pass `org_id` to scope by org and combine with other filters.

Examples:

- Admin: list org 20 only, last 7 days, scaled score >= 120
  - `/api/seedtest/results?org_id=20&last_n_days=7&min_score_scaled=120`
- Admin: org 10 + a specific user
  - `/api/seedtest/results?org_id=10&user_id=stu1`
- Teacher (org 10): list within own org, last 24 hours, status=ready
  - `/api/seedtest/results?last_n_hours=24&status_csv=ready`
- Student: see only own results (no extra params needed)
  - `/api/seedtest/results`

## Quick start (local)

1) **Configure environment**

Copy `env.example` to `.env` and adjust values:

```bash
cp env.example .env
# Edit .env with your editor
```

For quick local dev without DB, keep:
```env
LOCAL_DEV=true
```

For full setup with PostgreSQL:
```env
DATABASE_URL=postgresql+psycopg2://user:pass@127.0.0.1:5432/dreamseed_db
LOCAL_DEV=true
```

2) **Install dependencies**

```bash
cd apps/seedtest_api
pip install -r requirements.txt
```

3) **Run Alembic migrations** (optional, for DB persistence)

```bash
# Skip this if running without DATABASE_URL
alembic upgrade head
```

4) **Start the server**

```bash
uvicorn app.main:app --reload --port 8002
```

Or from repo root:
```bash
cd apps/seedtest_api
uvicorn app.main:app --reload --port 8002
```

5) **Try it** (with LOCAL_DEV bypass)

```bash
# Health check
curl http://localhost:8002/healthz

# API docs
open http://localhost:8002/docs

# Example: POST result (stub)
curl -X POST "http://localhost:8002/api/seedtest/exams/SESSION123/result"

# Finish a session now (admin/debug)
curl -X POST "http://localhost:8002/api/seedtest/exams/SESSION123/finish"

# With Authorization (replace TOKEN)
curl -H "Authorization: Bearer TOKEN" -X POST \
  "http://localhost:8002/api/seedtest/exams/SESSION123/finish"
```

## Tests

Install dev dependencies:

```bash
pip install -r dev-requirements.txt
```

**Unit tests** (fast, no external dependencies):

```bash
# From repo root
PYTHONPATH=apps LOCAL_DEV=true pytest -q apps/seedtest_api/tests

# Or from package directory
cd apps/seedtest_api
LOCAL_DEV=true pytest -q
```

**Integration tests** (requires Docker for PostgreSQL):

Integration tests are gated behind the `RUN_INTEGRATION_TESTS` environment variable.

```bash
# Enable integration tests (starts Docker Compose for DB)
RUN_INTEGRATION_TESTS=1 PYTHONPATH=apps LOCAL_DEV=true pytest -q apps/seedtest_api/tests
```

CI automatically brings up a PostgreSQL service and runs DB-backed tests in a dedicated job.

**Notes**:
- Tests use `LOCAL_DEV=true` to bypass JWT verification
- `PYTHONPATH=apps` from repo root ensures `seedtest_api` package is importable
- Integration tests require Docker Desktop/Engine and available port 5432

### One-command local DB test (compose + Alembic + pytest)

For quick local runs of DB-backed tests (e.g., listing auth), use the helper:

```bash
# From repo root
apps/seedtest_api/scripts/dev_db_test.sh apps/seedtest_api/tests/test_results_list_auth.py

# Or via Make targets (from apps/seedtest_api directory)
cd apps/seedtest_api
make db-test-listing-auth

# Run all listing-related DB tests
make db-test-listing-all
```

You can also set `DB_PORT` to avoid host port conflicts (default 5432):

```bash
# Run on an alternate port (e.g., 5433)
DB_PORT=5433 apps/seedtest_api/scripts/dev_db_test.sh apps/seedtest_api/tests/test_results_list_auth.py

# Or with Make (invoke from apps/seedtest_api)
DB_PORT=5433 make db-test-listing-auth
```

The script will:
- Start Postgres with Docker Compose (using `docker-compose.db.yml`)
- Wait for DB readiness on localhost:`$DB_PORT`
- Apply Alembic migrations with `DATABASE_URL=postgresql+psycopg2://user:pass@127.0.0.1:$DB_PORT/dreamseed_db`
- Run pytest for the provided test selection

Run the entire suite (unit + DB-backed) with one command:

```bash
# From repo root
make test-seedtest-api-all

# Or from package directory
cd apps/seedtest_api
make test-all
```

## Internals

- `services/result_service.py` — compute from adaptive session state and upsert JSONB cache (if DB configured)
- `services/scoring.py` — simple rule-based scoring and recommendations
- `services/analysis_service.py` — derive ability/topic insights/forecast/benchmark from result (heuristics now, mixed-effects hook later)
- `routers/results.py` — POST/GET endpoints and a PDF stub
- `routers/analysis.py` — analysis endpoint (feature-flagged)
- `alembic/versions/*_exam_results_table.py` — JSONB cache table and indexes

## 설정 (Configuration)

애플리케이션 설정은 환경변수로부터 로드하며, Pydantic settings를 사용해 관리합니다.

- .env 위치: 프로젝트 루트 또는 `apps/seedtest_api` 경로에 `.env` 파일을 두세요 (배포 환경에서는 각 환경의 설정을 사용).
- 예시:

```
DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/DB_NAME
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqh...IDAQAB\n-----END PUBLIC KEY-----"
# 또는
JWKS_URL=https://auth.example.com/.well-known/jwks.json
APP_ENV=local  # local | staging | production
```

- DATABASE_URL는 SQLAlchemy 연결 문자열이며 Alembic도 이 값을 사용합니다.
- JWT_PUBLIC_KEY 또는 JWKS_URL 중 하나로 토큰 검증에 필요한 키를 제공합니다.
- APP_ENV 등으로 환경별 분기(로깅 레벨 등)를 처리할 수 있습니다.

### Pydantic BaseSettings

`core/config.py`에 `Config(BaseSettings)`를 정의하여 위 환경변수들을 필드로 선언합니다. FastAPI 앱 기동 시 `app.state.config`에 로드되어 의존성 혹은 전역에서 참조할 수 있습니다.

### 초기화 (앱 기동 시)

- FastAPI startup 훅에서:
  - 설정 로드 후 `app.state.config`에 저장
  - 데이터베이스 연결 확인 (`engine.connect()`로 간단한 쿼리)
  - Alembic 마이그레이션은 일반적으로 CI/CD 또는 운영 절차에서 `alembic upgrade head`로 적용합니다 (개발 환경에서는 수동 실행 권장)
  - JWT 공개키/JWKS 설정을 기반으로 검증 준비 (`security/jwt.py` 참조)

## Analysis engine switch (heuristic | irt | mixed_effects)

분석 엔드포인트(`/api/seedtest/exams/{session_id}/analysis`)는 설정값 `ANALYSIS_ENGINE`에 따라 능력 추정 방식을 선택합니다.

- heuristic (기본): 결과에 포함된 ability_estimate가 있으면 우선 사용하고, 없으면 scaled score에서 간단히 역변환합니다.
- irt: 추후 IRT 기반 구현을 위한 자리표시자(현재는 선형 근사 변환으로 동작).
- mixed_effects: 충분한 응답 데이터가 누적되면 혼합효과 모형을 연결할 계획이며, 현재는 heuristic과 동일한 스텁으로 동작하되 방법명이 `mixed_effects`로 표기됩니다.

활성화 예시:

```bash
# 분석 기능 켜기
export ENABLE_ANALYSIS=true
# 엔진 선택: heuristic | irt | mixed_effects
export ANALYSIS_ENGINE=mixed_effects
```

설정은 `apps/seedtest_api/settings.py`의 `Settings` 클래스로 로드되며, 서비스 로직은 `services/score_analysis.py` 엔진을 통해 추정 값을 계산합니다.

### Recommender engine (rule | content | hybrid)

성적 리포트의 `recommendations`는 설정값 `RECOMMENDER_ENGINE`에 따라 생성됩니다.

- rule (기본): 토픽 정확도가 낮은 영역(예: ≤ 0.6) 위주로 기본 스터디 권고를 제공합니다.
- content: (스텁) 콘텐츠 기반 접근으로 약점 토픽에 맞는 리소스 형태의 권고 문구를 생성합니다. 추후 TF-IDF/임베딩 유사도 기반으로 확장 예정.
- hybrid: content 우선, 부족하면 rule로 보강.

예시:

```bash
export RECOMMENDER_ENGINE=hybrid
export CONTENT_CATALOG_PATH=apps/seedtest_api/data/content_sample.json
```

카탈로그 파일 형식: JSON 또는 YAML. JSON 예시: `apps/seedtest_api/data/content_sample.json`.

### Forecast goals configuration (targets & horizons)

분석 응답의 `forecast.goals`에는 "목표 점수 X를 Y회 내 달성할 확률"이 포함됩니다. 기본값과 요청별 오버라이드는 다음과 같습니다.

- 환경변수(기본값 설정):
  - `ANALYSIS_GOAL_TARGETS` (기본: `130,150`)
  - `ANALYSIS_GOAL_HORIZONS` (기본: `3,5,8`)
- 요청별 오버라이드(쿼리 파라미터):
  - `goal_targets=140,150`
  - `goal_horizons=3,5,10`

예시:

```bash
export ENABLE_ANALYSIS=true
export ANALYSIS_GOAL_TARGETS=130,150
export ANALYSIS_GOAL_HORIZONS=3,5,8

# 요청 시 오버라이드 가능
curl -s "http://127.0.0.1:8002/api/seedtest/exams/S1/analysis?goal_targets=150&goal_horizons=5,10" | jq .
```

확률은 현재 추정된 능력 표준오차(SE)를 스케일 점수로 변환한 정규분포 근사로 계산합니다. SE가 없으면 보수적 기본값을 사용합니다.
