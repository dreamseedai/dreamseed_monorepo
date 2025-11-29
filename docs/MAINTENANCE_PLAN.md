# DreamSeed AI - 유지보수 계획 (MegaCity 연계)

> **현재 규모**: 389,119 라인 (100K의 3.9배)  
> **MegaCity Phase**: Phase 0 (90%) → Phase 1 진행 중  
> **목표**: Phase 4 (100만 유저, 60만+ 라인)까지 확장 가능한 유지보수 체계

---

## 🏙️ MegaCity 컨텍스트

**MegaCity란?**
- 9개 Zone (UnivPrepAI, CollegePrepAI, SkillPrepAI, MediPrepAI, MajorPrepAI, My-Ktube 등)
- 2025-2030 장기 계획 (Phase 0~4)
- 100만 유저 목표 AI 교육 플랫폼 생태계

**관련 문서:**
- [PHASE_OVERVIEW.md](/docs/project-status/PHASE_OVERVIEW.md) - Phase 전체 개요
- [MEGACITY_EXECUTION_CHECKLIST.md](/ops/architecture/MEGACITY_EXECUTION_CHECKLIST.md) - 실행 체크리스트
- [MEGACITY_MASTER_BOOK.md](/ops/architecture/MEGACITY_MASTER_BOOK.md) - 통합 백과사전

---

## 📊 현재 상태 (2025-11-25)

### Phase 진행 상황
- ✅ **Phase 0 (Foundation)**: 90% 완료
  - 인증/모니터링/백업/Rate Limiting 완료
  - 도메인 8/9 이전 완료
- 🔄 **Phase 0.5 (Core Backend)**: 40% 진행
  - DB Schema 미완료
  - CAT/IRT 엔진 설계 진행 중
- 🔄 **Phase 1 (Core MVP)**: 60% 진행
  - Backend API 100% 완료
  - Frontend 진행 중

### 코드베이스 강점
- ✅ **문서화**: 1,051개 .md 파일 (MegaCity 문서 포함)
- ✅ **테스트**: 116개 테스트 파일 (pytest + Playwright)
- ✅ **코드 품질**: black, mypy, ESLint, Prettier, Pyright
- ✅ **모노레포**: pnpm workspace 구조
- ✅ **CI/CD**: GitHub Actions (fast/full 프로필)

### 개선 필요 (Phase 1 이전)
- ⚠️ **기술 부채**: 50+ TODO 마커 (JWT, CAT, IRT 통합 등)
- ⚠️ **버전 관리**: CHANGELOG 없음
- ⚠️ **의존성**: 대규모 node_modules/venv 관리
- ⚠️ **모니터링**: Phase 0에서 설치했지만 대시보드 미완성
- 🔴 **메신저 시스템**: Phase 2 핵심, 40K LOC 추가 예정 (현재 미구현)

---

## 🎯 Phase 1: 기술 부채 관리 (1주) - **MegaCity Phase 1 Gate**

> **타이밍**: Phase 0.5 완료 직후, Phase 1 본격 시작 전  
> **목적**: Phase 1 (첫 1,000명 사용자) 출시 전 코드 안정성 확보

### 1.1 TODO 추적 시스템
```bash
# TODO 리스트 자동 생성
rg "TODO|FIXME|XXX|HACK" --json > .todos.json

# GitHub Issues로 변환 (MegaCity 레이블 추가)
python scripts/create_issues_from_todos.py --label "megacity-blocker"
```

**우선순위 (MegaCity Phase 1 기준):**
1. 🔴 **P0 - Phase 1 Blocker**: 
   - JWT 인증 완성 (현재 mock)
   - User 모델 relationship 활성화
   - DB Schema 생성 완료
2. 🟡 **P1 - Phase 1 High**: 
   - CAT 알고리즘 통합 (R Plumber)
   - IRT 점수 계산 엔진
3. 🟢 **P2 - Phase 2**: 
   - 캐싱 전략 구현
   - 부모-자녀 관계 검증
   - Exposure tracking

### 1.2 버전 관리 자동화
```bash
# Changesets 초기화
pnpm changeset init

# 변경사항 기록
pnpm changeset add

## 🎯 Phase 2: 모니터링 강화 (1주) - **이미 Phase 0에서 구축됨!**

> **상태**: ✅ Phase 0에서 Prometheus + Grafana 설치 완료  
> **남은 작업**: 대시보드 7개 완성 + 알림 규칙 추가

### 2.1 구조화된 로깅 (추가 작업)
```python
# backend/app/core/logging.py
import structlog

logger = structlog.get_logger()

# 사용 예시 (MegaCity 필수 로그)
logger.info("user.login", user_id=user_id, zone_id=zone_id, ip=request.client.host)
logger.error("exam.failed", exam_id=exam_id, zone_id=zone_id, error=str(e))
logger.warn("ai.quota_exceeded", user_id=user_id, zone_id=zone_id)
```

### 2.2 성능 모니터링 (Phase 0 완료, 대시보드 추가)

**Phase 0에서 이미 설치됨:**
- ✅ Prometheus (메트릭 수집)
- ✅ Grafana (시각화)
- ✅ Node/PostgreSQL/Redis Exporter
- ✅ 기본 알림 규칙

**추가 작업 (Phase 1 전):**
```bash
# Grafana 대시보드 7개 구성
1. API Health (응답 시간, 에러율)
2. Database Performance (쿼리 시간, 연결 수)
3. AI Infrastructure (GPU 사용률, vLLM 레이턴시)
4. User Activity (활성 사용자, Zone별 분포)
5. CAT Engine (난이도 조정 시간, 종료 조건)
6. Security (실패한 로그인, Rate Limit 초과)
7. Zone Overview (9개 Zone 상태)
```

**핵심 지표 (MegaCity 맞춤):**
- API 응답 시간 (p50, p95, p99) - **목표: <200ms**
- 에러율 (4xx, 5xx) - **목표: <1%**
- 데이터베이스 쿼리 시간 - **목표: <50ms**
- CAT 알고리즘 수행 시간 - **목표: <500ms**
- AI 응답 시간 (vLLM) - **목표: <2s**
- Zone별 동시 접속자 수na/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**핵심 지표:**
- API 응답 시간 (p50, p95, p99)
- 에러율 (4xx, 5xx)
- 데이터베이스 쿼리 시간
- CAT 알고리즘 수행 시간

### 2.3 알림 시스템
```yaml
# monitoring/alertmanager.yml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: $SLACK_WEBHOOK_URL
        channel: '#alerts'
        title: '🚨 DreamSeed Alert'

  - name: 'email'
    email_configs:
      - to: 'team@dreamseed.com'
```

**알림 규칙:**
- API 에러율 > 5% (5분간)
- 응답 시간 > 1초 (10분간)
- DB 연결 실패
- 메모리 사용량 > 80%

---

## 🎯 Phase 3: 의존성 최적화 (2주)

### 3.1 Python 의존성
```bash
# 사용되지 않는 패키지 찾기
pip-autoremove -L | tee unused_packages.txt

# 보안 취약점 스캔
pip-audit --desc

# 의존성 업데이트
pip list --outdated
```

**정책:**
- 월 1회 의존성 업데이트
- 보안 취약점 즉시 패치
- Major 버전 업그레이드는 별도 브랜치

### 3.2 Node 의존성
```bash
# 중복 의존성 제거
pnpm dedupe

# 사용되지 않는 패키지
npx depcheck

# 번들 크기 분석
pnpm -r exec -- npx vite-bundle-visualizer
```

### 3.3 Docker 이미지 최적화
```dockerfile
# multi-stage build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
```

---

## 🎯 Phase 4: 코드 품질 자동화 (2주)

### 4.1 Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.0.0
    hooks:
      - id: eslint
        files: \.(js|jsx|ts|tsx)$
```

### 4.2 자동화된 코드 리뷰
```yaml
# .github/workflows/code-review.yml
name: Automated Code Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Code Review
        uses: microsoft/action-python@v1
        with:
          command: |
            black --check .
            mypy .
            pytest --cov=backend --cov-report=xml
            
      - name: Comment Coverage
        uses: codecov/codecov-action@v3
```

### 4.3 복잡도 모니터링
```bash
# 순환 복잡도 체크
radon cc backend/ -a -nb

# 유지보수 지수
radon mi backend/ -nb

# 코드 중복 검사
pylint --disable=all --enable=duplicate-code backend/
```

**임계값:**
- Cyclomatic Complexity: < 10 (권장), < 15 (최대)
- Maintainability Index: > 70 (양호), > 50 (수용)
- 중복 코드: < 5%

---

## 🎯 Phase 5: 문서 자동화 (1주)

### 5.1 API 문서 자동 생성
```python
# backend/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="DreamSeed AI API",
    description="AI-powered education platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# OpenAPI 스펙 내보내기
with open("openapi.json", "w") as f:
    json.dump(get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    ), f)
```

### 5.2 타입 문서화
```typescript
// apps/shared/types/api.ts
/**
 * 사용자 인증 요청
 * @example
 * ```ts
 * const req: LoginRequest = {
 *   username: "student@example.com",
 *   password: "secure123"
 * };
 * ```
 */
export interface LoginRequest {
  username: string;
  password: string;
}
```

### 5.3 아키텍처 다이어그램 자동화
```bash
# PlantUML로 다이어그램 생성
docker run -v $(pwd):/data plantuml/plantuml:latest \
  docs/architecture/*.puml
```

---

## 🎯 Phase 6: 테스트 커버리지 향상 (진행 중)

### 6.1 현재 상태
```bash
# Backend 커버리지
pytest --cov=backend --cov-report=html

# 목표: 70% → 85%
```

### 6.2 테스트 전략
| 레이어 | 현재 | 목표 | 전략 |
|--------|------|------|------|
| Unit | 65% | 85% | 각 함수별 테스트 |
| Integration | 50% | 75% | API 엔드포인트 테스트 |
| E2E | 30% | 60% | Playwright로 주요 플로우 |
| Performance | 10% | 40% | Locust 부하 테스트 |

### 6.3 테스트 자동화
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
        node-version: [20, 22]
    
    steps:
      - name: Backend Tests
        run: |
          pytest --cov=backend \
                 --cov-report=xml \
                 --cov-report=html
      
      - name: Frontend Tests
        run: |
          pnpm test --coverage
      
      - name: E2E Tests
        run: |
          pnpm playwright test
```

---

## 📊 주간 체크리스트

### 월요일: 계획
- [ ] TODO 리스트 업데이트
- [ ] 이번 주 목표 설정
- [ ] 의존성 업데이트 확인

### 화-목: 개발
- [ ] Pre-commit hooks 통과
- [ ] 테스트 작성
- [ ] 문서 업데이트
- [ ] Code review 완료

### 금요일: 점검
- [ ] 커버리지 확인 (≥70%)
- [ ] 성능 지표 확인
- [ ] 기술 부채 정리
- [ ] 다음 주 계획

---

## 🚨 경고 신호

### 즉시 대응 필요
- 🔴 **에러율 > 5%**: 긴급 핫픽스
- 🔴 **응답 시간 > 2초**: 성능 최적화
- 🔴 **보안 취약점**: 즉시 패치

### 주의 필요
- 🟡 **테스트 실패**: 1시간 내 수정
- 🟡 **커버리지 감소**: PR block
- 🟡 **빌드 시간 > 5분**: 최적화 필요

### 개선 필요
- 🟢 **TODO > 100개**: 매주 10개씩 해결
- 🟢 **문서 오래됨**: 월 1회 업데이트
- 🟢 **의존성 오래됨**: 분기 1회 업데이트

---

## 🎓 학습 리소스

### 대규모 프로젝트 관리
- [Google Engineering Practices](https://google.github.io/eng-practices/)
- [The Twelve-Factor App](https://12factor.net/)
- [Awesome Monorepo](https://github.com/korfuri/awesome-monorepo)

### 코드 품질
- [Clean Code in Python](https://testdriven.io/blog/clean-code-python/)
- [TypeScript Best Practices](https://typescript-best-practices.netlify.app/)
## 📝 다음 단계 (MegaCity Phase별 연계)

### 🚨 즉시 (이번 주) - **Phase 0.5 완료 + Phase 1 Gate**

**1. TODO 추적 시스템 구축**
```bash
# P0 블로커만 추출
rg "TODO.*JWT|TODO.*User.*relationship|TODO.*CAT|TODO.*IRT" \
  --json > megacity_p0_blockers.json

# GitHub Issues 생성 (megacity-p0 레이블)
python scripts/create_issues_from_todos.py \
  --label "megacity-p0" \
  --milestone "Phase 1 - Core MVP"
```

**2. Grafana 대시보드 7개 완성**
```bash
# Phase 0에서 Prometheus는 이미 실행 중
# Grafana 대시보드 JSON 가져오기
cd monitoring/grafana/dashboards
# 각 대시보드 구성 완료 확인
ls -l api_health.json db_performance.json ai_infra.json \
      user_activity.json cat_engine.json security.json zone_overview.json
```

**3. Phase 0.5 완료 확인**
```bash
# MEGACITY_EXECUTION_CHECKLIST.md Phase 0.5 체크
- [ ] DB Schema 생성 완료
- [ ] CAT/IRT 엔진 R Plumber 연동
- [ ] 시드 데이터 삽입
- [ ] E2E 테스트 통과
```

### ⚡ 단기 (1개월) - **Phase 1 (Core MVP) 완료**

**MegaCity Phase 1 목표:**
- 첫 1,000명 사용자 서비스
- Teacher/Parent/Student Portal 완성
- AI Tutor v1 연동

**유지보수 작업:**
- Pre-commit hooks 설정 (black, mypy, ESLint)
- 테스트 커버리지 75% 달성 (Phase 1 API 위주)
- Slack 알림 시스템 구축 (P1-P4 Incident)
- 성능 벤치마크 기준 설정 (API <200ms, AI <2s)
- CHANGELOG 자동화 (changesets)

### 🚀 중기 (3개월) - **Phase 2 (Zone Expansion + 메신저 시스템)**

**MegaCity Phase 2 목표:**
- 9개 Zone 중 3개 활성화 (UnivPrepAI, CollegePrepAI, SkillPrepAI)
- Zone별 독립 프론트엔드 구축
- Multi-zone 라우팅 구현
- **🗨️ 실시간 메신저 시스템 구축** (40,000~50,000 LOC)

**메신저 시스템 (Phase 2의 핵심!):**
- Week 1-4: MVP (1:1 채팅, 텍스트만) - 15,000 LOC
- Week 5-8: 고급 기능 (그룹, 파일, 알림) - 20,000 LOC
- Week 9-10: 최적화 (성능, 모니터링) - 10,000 LOC
- **총 10주, 단독 프로젝트급 규모**

**유지보수 작업:**
- Phase 3 (의존성 최적화) 실행 (메신저 추가 전!)
  - WebSocket, Socket.IO, Redis Pub/Sub 의존성 추가
  - Firebase (Push), SendGrid (Email) 설정
- Phase 4 (코드 품질 자동화) 강화
- 50+ TODO 중 P1 해결
- Zone별 + 메신저별 모니터링 대시보드 추가

### 🌍 장기 (6개월+) - **Phase 3~4 (Global Scale)**

**MegaCity Phase 3-4 목표:**
- 10만~100만 유저
- 9개 Zone 전체 활성화
- Multi-region 배포 (한국, 일본, 미국)

**유지보수 작업:**
- 테스트 커버리지 85% 달성
- 마이크로서비스 전환 (Zone별 독립 배포)
- 국제화(i18n) 지원 (한/영/일/중)
- 모바일 앱 개발 (React Native)

---

## 📊 MegaCity Phase별 유지보수 맵핑

| MegaCity Phase | 유지보수 Phase | 타이밍 | 우선순위 | 특이사항 |
|----------------|----------------|--------|----------|----------|
| **Phase 0.5 완료** | Phase 1 (기술 부채) | 지금 | 🔴 P0 | - |
| **Phase 1 시작** | Phase 2 (모니터링) | 이번 주 | 🔴 P0 | - |
| **Phase 1 중반** | Phase 4 (코드 품질) | 1개월 후 | 🟡 P1 | - |
| **Phase 2 시작 전** | Phase 3 (의존성) | 3개월 후 | 🔴 P0 | **메신저 의존성 추가!** |
| **Phase 2 중반** | 🗨️ **메신저 구축** | 3~5개월 | 🔴 P0 | **40K LOC, 10주 소요** |
| **Phase 2 후반** | Phase 5 (문서 자동화) | 5개월 후 | 🟢 P2 | 메신저 API 문서 자동화 |
| **Phase 3~4** | Phase 6 (테스트 향상) | 지속 | 🟢 P2 | 메신저 E2E 테스트 추가 |

### 🗨️ 메신저 시스템 세부 일정

| Week | 작업 내용 | LOC | 우선순위 |
|------|----------|-----|----------|
| **Week 1** | Socket.IO + DB Schema + REST API | 2,000 | 🔴 P0 |
| **Week 2** | WebSocket 핸들러 + Redis Pub/Sub | 1,500 | 🔴 P0 |
| **Week 3** | Frontend UI (채팅 목록, 입력창, 리스트) | 3,000 | 🔴 P0 |
| **Week 4** | 테스트 & 배포 (통합, 재연결, 성능) | 2,500 | 🔴 P0 |
| **Week 5-6** | 그룹 채팅 + 파일 업로드 + 썸네일 | 4,000 | 🟡 P1 |
| **Week 7** | 타이핑, 온라인, 읽음 표시 | 2,000 | 🟡 P1 |
| **Week 8** | Push/Email 알림 + 설정 UI | 3,000 | 🟡 P1 |
| **Week 9** | 성능 최적화 (페이징, 캐싱, 인덱스) | 2,000 | 🟢 P2 |
| **Week 10** | 운영 준비 (메트릭, 로깅, 백업, Runbook) | 2,000 | 🟢 P2 |
| **합계** | **10주 (2.5개월)** | **22,000** | - |

**참고 문서:**
- [메신저 시스템 계획](../docs/features/MESSENGER_SYSTEM_PLAN.md)
- [GPT 작업 지시서](../docs/features/MESSENGER_IMPLEMENTATION_TASKS.md)

---

**작성일**: 2025-11-25  
**작성자**: DreamSeed AI Team  
**다음 리뷰**: 2025-12-02 (Phase 1 Gate 통과 확인)  
**MegaCity 연계**: MEGACITY_EXECUTION_CHECKLIST.md와 동기화
- 모바일 앱 개발

---

**작성일**: 2025-11-25  
**작성자**: DreamSeed AI Team  
**다음 리뷰**: 2025-12-02 (주간 체크)
