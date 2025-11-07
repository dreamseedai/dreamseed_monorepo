# 🎓 DreamSeedAI 통합 설계서 레팩토링 요약

**최종 업데이트**: 2025-11-06  
**버전**: v2.0 Refactored  
**목적**: 중복 제거 및 누락 사항 보완

---

## 📋 레팩토링 결과

### ✅ 제거된 중복 사항

1. **인증/권한** (섹션 3, 5, 9 통합 → 섹션 3)
2. **리스크 규칙** (섹션 4, 10 통합 → 섹션 4)
3. **API 스펙** (섹션 5, 부록 통합 → 섹션 5)
4. **환경 변수** (섹션 7, 9 통합 → 섹션 9)
5. **배포/보안** (섹션 9, 12 통합 → 섹션 9)

---

### 🆕 추가된 누락 사항

#### 1. 에러 처리 전략
```python
# 재시도 전략
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(TransientError)
)
def call_assignment_api(payload):
    ...

# 서킷 브레이커
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=APIError
)

# 데드레터 큐
if retry_count >= MAX_RETRIES:
    send_to_dead_letter_queue(message)
```

#### 2. 데이터 마이그레이션 전략
```sql
-- 무중단 배포: 컬럼 추가 (nullable)
ALTER TABLE student ADD COLUMN country VARCHAR(3);

-- 데이터 백필
UPDATE student SET country = 'USA' WHERE country IS NULL;

-- NOT NULL 제약 추가
ALTER TABLE student ALTER COLUMN country SET NOT NULL;

-- 롤백 계획
-- 1. 제약 제거
-- 2. 컬럼 삭제
```

#### 3. 캐싱 전략
```python
# Redis 레이어
@cache(ttl=300, key_prefix="class_snapshot")
def get_class_snapshot(class_id: str, from_date: date, to_date: date):
    ...

# 무효화
def invalidate_class_cache(class_id: str):
    redis.delete_pattern(f"class_snapshot:{class_id}:*")
```

#### 4. 이벤트 소싱
```python
# 감사 로그
class AuditLog(BaseModel):
    event_id: str
    event_type: str  # assignment_created, risk_calculated
    user_id: str
    org_id: str
    timestamp: datetime
    payload: dict
    result: dict

# Kafka 이벤트
producer.send('audit_log', audit_log.dict())
```

#### 5. API 버저닝
```python
# URL 버저닝
@app.post("/api/v1/assignments")
@app.post("/api/v2/assignments")  # 새 버전

# 헤더 버저닝
@app.post("/api/assignments")
def create_assignment(
    request: Request,
    api_version: str = Header("1.0", alias="X-API-Version")
):
    if api_version == "2.0":
        return create_assignment_v2(request)
    return create_assignment_v1(request)
```

#### 6. 성능 SLA
```yaml
SLA:
  API 응답 시간:
    - GET /api/classes/{id}/snapshot: < 1초 (p95)
    - GET /api/classes/{id}/students: < 2초 (p95)
    - POST /api/assignments: < 3초 (p95)
  
  대시보드 로딩:
    - Class Monitor 초기 로드: < 3초
    - 학생 테이블 렌더링: < 2초
    - 히스토그램 렌더링: < 1초
  
  배치 처리:
    - 주간 리스크 산출 (1000명): < 5분
    - 일일 통계 갱신 (10000명): < 10분
  
  데이터 처리:
    - Arrow 데이터 로드 (10GB): < 5초
    - PostgreSQL 쿼리 (100만 행): < 3초
```

#### 7. 재해 복구 (DR)
```yaml
DR 정책:
  RTO (Recovery Time Objective): 4시간
  RPO (Recovery Point Objective): 1시간
  
  백업 전략:
    - PostgreSQL: 매일 전체 백업 + 5분 WAL 아카이빙
    - S3/MinIO: 교차 리전 복제
    - Redis: RDB 스냅샷 (1시간 간격)
  
  복구 절차:
    1. 최신 백업 복원
    2. WAL 재생 (RPO까지)
    3. 서비스 헬스 체크
    4. 트래픽 전환
```

#### 8. 글로벌 확장 연동
```python
# 이미 구현된 helpers_global.R 통합
from rpy2 import robjects as ro

ro.r.source('portal_front/dashboard/helpers_global.R')

def get_global_template(country, subject, grade, level, bucket):
    """
    R 헬퍼 함수 호출
    """
    config = ro.r['load_config']()
    template = ro.r['get_template'](
        config=config,
        country=country,
        subject=subject,
        grade=grade,
        level=level,
        bucket=bucket
    )
    return dict(template)

# 다국어 메시지
def get_i18n_message(language, message_key, **kwargs):
    config = ro.r['load_config']()
    message = ro.r['get_i18n_message'](
        config=config,
        language=language,
        message_key=message_key
    )
    return message.format(**kwargs)
```

---

## 📚 최적화된 문서 구조

### 8권 분할 (각 ≤ 128K 토큰)

```
docs/
├── DREAMSEED_REFACTORED_SUMMARY.md (본 문서)
├── Doc01_Requirements_Domain_ERD.md
│   ├── 1. 교육 철학 (4계층)
│   ├── 2. MVP 범위
│   ├── 3. 도메인 모델
│   ├── 4. ERD
│   └── 5. 최소 스키마 + 확장 필드
│
├── Doc02_Auth_Permissions_MultiTenancy.md
│   ├── 1. 헤더 계약
│   ├── 2. 역할 정규화
│   ├── 3. 데이터 스코프
│   ├── 4. Bearer 인증
│   ├── 5. 보안 체크리스트
│   └── 6. 테스트 시나리오
│
├── Doc03_Data_Schema_Migrations.md
│   ├── 1. PostgreSQL DDL
│   ├── 2. 인덱스 전략
│   ├── 3. Arrow 파티셔닝
│   ├── 4. CDC/동기화
│   ├── 5. 마이그레이션 전략
│   └── 6. 롤백 계획
│
├── Doc04_IRT_Risk_Engine.md
│   ├── 1. 개선 저조 (알고리즘 + 코드)
│   ├── 2. 출석 불규칙 (알고리즘 + 코드)
│   ├── 3. 응답 이상 (알고리즘 + 코드)
│   ├── 4. 서브그룹 분위수 (Fallback)
│   ├── 5. 배치 설계
│   └── 6. 테스트 케이스
│
├── Doc05_Assignment_Service_API.md
│   ├── 1. API 스펙 (POST /api/assignments)
│   ├── 2. 템플릿 매핑 (YAML)
│   ├── 3. 권한 가드
│   ├── 4. 에러 처리 (재시도, 서킷 브레이커)
│   ├── 5. 감사 로그
│   ├── 6. 글로벌 확장 연동
│   └── 7. 테스트 시나리오
│
├── Doc06_Teacher_Dashboard_Design.md
│   ├── 1. KPI 카드
│   ├── 2. θ 히스토그램
│   ├── 3. 학생 테이블
│   ├── 4. 모달 (반응 이상 4유형)
│   ├── 5. API 연동
│   ├── 6. 성능 튜닝 (Arrow pushdown, DT server)
│   └── 7. 접근 제어
│
├── Doc07_Admin_Dashboard_Design.md
│   ├── 1. Cohort Overview
│   ├── 2. IRT Calibration
│   ├── 3. A/B Lab
│   ├── 4. Churn Monitor
│   ├── 5. Content Bank
│   ├── 6. 데이터 소스
│   └── 7. 성능/권한
│
└── Doc08_Operations_Deployment_Observability.md
    ├── 1. 환경 변수 (전체 목록)
    ├── 2. Docker/Kubernetes (Helm)
    ├── 3. CI/CD (GitHub Actions)
    ├── 4. 로깅/모니터링 (OpenTelemetry, Prometheus)
    ├── 5. 백업/DR (RTO/RPO)
    ├── 6. 보안 체크리스트
    ├── 7. 성능 SLA
    └── 8. 트러블슈팅
```

---

## 🔧 즉시 코딩 체크리스트 (보완)

### Phase 1: 백엔드 스캐폴딩 (Week 1)
- [ ] FastAPI 프로젝트 구조 생성
- [ ] Pydantic 모델 정의 (student, session, attendance, irt_snapshot, skill_mastery, risk_flag)
- [ ] Alembic 마이그레이션 초기화
- [ ] 인증 미들웨어 (헤더 파싱, 역할 정규화)
- [ ] 권한 가드 데코레이터 (`@require_role("teacher")`)

### Phase 2: 리스크 엔진 (Week 2)
- [ ] 개선 저조 알고리즘 구현
- [ ] 출석 불규칙 알고리즘 구현
- [ ] 응답 이상 알고리즘 구현
- [ ] 서브그룹 분위수 계산 (Fallback)
- [ ] Celery 태스크 (주간/일일 배치)
- [ ] 단위 테스트 (pytest)

### Phase 3: Assignment API (Week 3)
- [ ] POST /api/v1/assignments 구현
- [ ] GET /api/v1/assignment-templates 구현
- [ ] YAML 설정 로드 (핫리로드)
- [ ] Bearer 인증 검증
- [ ] 권한 가드 (teacher/admin)
- [ ] 에러 처리 (재시도, 서킷 브레이커, 데드레터)
- [ ] 감사 로그 (Kafka/PostgreSQL)

### Phase 4: 조회 API (Week 4)
- [ ] GET /api/v1/classes/{id}/snapshot
- [ ] GET /api/v1/classes/{id}/students
- [ ] GET /api/v1/students/{id}/timeline
- [ ] GET /api/v1/classes/{id}/risk/summary
- [ ] 캐싱 (Redis)
- [ ] 성능 최적화 (쿼리, 인덱스)

### Phase 5: 대시보드 연동 (Week 5)
- [ ] Shiny 앱 AUTH_HEADER_* 반영
- [ ] API 클라이언트 (httr, Bearer 전달)
- [ ] YAML 핫리로드 (30초)
- [ ] 에러 핸들링 (알림)
- [ ] 성능 튜닝 (Arrow pushdown, DT server)

### Phase 6: 배치/워크플로 (Week 6)
- [ ] Celery Beat 스케줄 설정
- [ ] 주간 리스크 산출 태스크
- [ ] 일일 통계 갱신 태스크
- [ ] 재처리/감사 로그
- [ ] 모니터링 (Celery Flower)

### Phase 7: 배포/운영 (Week 7)
- [ ] Dockerfile (api, worker, dashboard)
- [ ] Helm 차트 (ingress, hpa, secrets)
- [ ] GitHub Actions CI/CD
- [ ] 로깅 (OpenTelemetry)
- [ ] 모니터링 (Prometheus/Grafana)
- [ ] 백업/DR 스크립트

### Phase 8: 테스트/검증 (Week 8)
- [ ] 단위 테스트 (pytest, 커버리지 ≥ 80%)
- [ ] 통합 테스트 (API 엔드포인트)
- [ ] 성능 테스트 (Locust, SLA 검증)
- [ ] 보안 테스트 (헤더 삽입 차단, org 교차 접근)
- [ ] 대시보드 시나리오 테스트

---

## 🎯 핵심 개선 사항 요약

### 1. 중복 제거
- 인증/권한: 3개 섹션 → 1개 섹션
- 리스크 규칙: 2개 섹션 → 1개 섹션
- API 스펙: 2개 섹션 → 1개 섹션
- 환경 변수: 2개 섹션 → 1개 섹션

### 2. 누락 사항 추가
- 에러 처리 (재시도, 서킷 브레이커, 데드레터)
- 데이터 마이그레이션 (무중단, 롤백)
- 캐싱 (Redis, TTL, 무효화)
- 이벤트 소싱 (감사 로그, Kafka)
- API 버저닝 (v1/v2)
- 성능 SLA (구체적 수치)
- 재해 복구 (RTO/RPO)
- 글로벌 확장 연동 (helpers_global.R)

### 3. 문서 구조 최적화
- 8권 분할 (각 ≤ 128K 토큰)
- 명확한 섹션 구분
- 코드 예시 포함
- 테스트 시나리오 포함

---

## 📞 다음 단계

1. **Doc01-08 상세 작성** (각 문서 별도 파일)
2. **FastAPI 스캐폴딩 시작**
3. **리스크 엔진 구현**
4. **Assignment API 구현**
5. **대시보드 연동**

---

**작성자**: DreamSeedAI Architecture Team  
**최종 업데이트**: 2025-11-06  
**버전**: v2.0 Refactored  
**상태**: ✅ 레팩토링 완료, 코딩 준비 완료
