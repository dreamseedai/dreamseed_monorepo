# DreamSeedAI Analytics - 실시간 드리프트 탐지 시스템

서사형 모니터링으로 IRT 파라미터 변화, 행동 패턴, 지역/언어별 드리프트를 실시간 감지합니다.

## 📁 디렉토리 구조

```
shared/analytics/
├── grafana/
│   ├── dashboards/
│   │   └── assessment_drift_watch.json    # Grafana 대시보드
│   └── provisioning/
│       └── datasources/
│           └── postgres.yaml               # Postgres 데이터소스 설정
├── sql/
│   └── metrics_views.sql                   # Materialized Views
├── shiny/
│   └── assessment_drift_watch/
│       └── app.R                           # R Shiny 대시보드
└── README.md                               # 이 문서
```

## 🚀 빠른 시작

### 1. 환경 변수 설정

```bash
export DSA_PG_HOST=localhost
export DSA_PG_PORT=5432
export DSA_PG_USER=dreamseed_user
export DSA_PG_PASSWORD=your_password
export DSA_PG_DB=dreamseed
export DSA_PG_SCHEMA=analytics
```

### 2. Postgres 뷰 생성

```bash
psql -h $DSA_PG_HOST -U $DSA_PG_USER -d $DSA_PG_DB -f shared/analytics/sql/metrics_views.sql
```

### 3. Grafana 대시보드 임포트

1. Grafana → Dashboards → Import
2. `shared/analytics/grafana/dashboards/assessment_drift_watch.json` 내용 붙여넣기
3. Postgres 데이터소스 선택
4. Import 클릭

### 4. Shiny 대시보드 실행

```bash
cd shared/analytics/shiny/assessment_drift_watch
Rscript -e "shiny::runApp('app.R', host='0.0.0.0', port=8012)"
```

브라우저에서 `http://localhost:8012` 접속

---

## 📊 드리프트 유형

### 1. Anchor Erosion (앵커 침식)
- **감지**: 앵커 문항의 난이도(b) 변화 > 0.35 SD
- **원인**: 문항 노출, 커리큘럼 변화
- **조치**: 재보정 큐에 편성

### 2. Guessing Instability (추측 불안정)
- **감지**: 추측도(c) 변화 > 0.06
- **원인**: 보기 난이도 변화, 시험 전략 변화
- **조치**: 보기 난이도/길이 점검

### 3. Difficulty Migration (난이도 이동)
- **감지**: 난이도 분포 KL divergence > 0.5
- **원인**: 문항 풀 불균형
- **조치**: 문항 풀 재균형

### 4. Curriculum Shift (커리큘럼 변화)
- **감지**: 지식 요소(KC) 출현 빈도 급변
- **원인**: 교육 과정 변경
- **조치**: 문항 분포 조정

### 5. Latency Creep (응답 시간 증가)
- **감지**: P95 응답 시간 > 120초
- **원인**: UI 지연, 피로
- **조치**: 성능 프로파일링

### 6. Region-Language Drift (지역/언어 드리프트)
- **감지**: 지역별 정답률 격차 > 15%
- **원인**: 번역 품질, 문화적 차이
- **조치**: 언어별 문항 재검토

---

## 🔄 Materialized View 리프레시

### 수동 리프레시
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.behavior_metrics;
REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.latency_metrics;
REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.daily_metrics;
REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.irt_anchor_deltas;
```

### Celery 자동 리프레시 (권장)

```python
# backend/tasks.py
from celery import Celery
from sqlalchemy import create_engine

app = Celery('analytics')

@app.task
def refresh_analytics_views():
    engine = create_engine(os.getenv('DSN'))
    with engine.connect() as conn:
        conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.behavior_metrics;")
        conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.latency_metrics;")
        conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.daily_metrics;")
        conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.irt_anchor_deltas;")

# Celery Beat 스케줄
app.conf.beat_schedule = {
    'refresh-analytics-every-15-min': {
        'task': 'tasks.refresh_analytics_views',
        'schedule': 900.0,  # 15분
    },
}
```

---

## 📈 데이터 요구사항

### 필수 테이블

#### 1. responses
```sql
CREATE TABLE responses (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    choice_idx INTEGER,        -- 선택한 보기 인덱스
    max_idx INTEGER,           -- 마지막 보기 인덱스
    open_ts TIMESTAMPTZ,       -- 문항 열람 시간
    submit_ts TIMESTAMPTZ      -- 제출 시간
);
```

#### 2. users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    language TEXT,             -- 'ko', 'en', 'zh-Hans', etc.
    region TEXT                -- 'KR', 'US', 'CN', etc.
);
```

#### 3. ability_daily
```sql
CREATE TABLE ability_daily (
    user_id INTEGER NOT NULL,
    ts DATE NOT NULL,
    theta REAL NOT NULL,
    PRIMARY KEY (user_id, ts)
);
```

#### 4. item_params_weekly
```sql
CREATE TABLE item_params_weekly (
    item_id TEXT NOT NULL,
    ts DATE NOT NULL,
    a REAL NOT NULL,           -- 변별도
    b REAL NOT NULL,           -- 난이도
    c REAL NOT NULL,           -- 추측도
    is_anchor BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (item_id, ts)
);
```

---

## 🎨 Grafana 대시보드 구성

### 패널 구성
1. **Today's Narrative** - 자동 요약 (HTML)
2. **KPI Cards** - Δθ, Last Option Rate, Omit Rate, Active Alerts
3. **Time Series** - Last Option Rate, Median Latency
4. **Table** - Anchor Item Δa/Δb/Δc
5. **Bar Gauge** - Alerts by Type
6. **Workflow** - 조치 버튼

### 템플릿 변수
- `$ds`: Postgres 데이터소스
- `$schema`: 스키마 (기본: analytics)
- `$lang`: 언어 필터 (all, ko, en, zh-Hans, zh-Hant)
- `$region`: 지역 필터 (all, KR, US, CN, etc.)

---

## 🔧 Shiny 대시보드 기능

### 주요 기능
1. **서사형 진단 카드** - 오늘의 드리프트 요약
2. **KPI 지표** - 색상 코드로 경보 레벨 표시
3. **시계열 차트** - Last Option Rate, Median Latency
4. **앵커 테이블** - 파라미터 변화 Top 50

### 필터
- Schema 선택
- Language 필터
- Region 필터
- 날짜 범위

---

## 🚨 경보 레벨

| 레벨 | 색상 | 조건 | 조치 |
|------|------|------|------|
| **높음** 🔴 | 빨강 | 임계값 2배 초과 | 즉시 조치 필요 |
| **중간** 🟠 | 주황 | 임계값 초과 | 모니터링 강화 |
| **낮음** 🟢 | 초록 | 정상 범위 | 정상 운영 |

---

## 📝 운영 가이드

### 일일 체크리스트
- [ ] Grafana 대시보드 확인
- [ ] Active Alerts 검토
- [ ] Anchor Erosion 항목 확인
- [ ] 지역/언어별 정답률 격차 모니터링

### 주간 체크리스트
- [ ] Materialized View 리프레시 상태 확인
- [ ] 드리프트 트렌드 분석
- [ ] 조치 이력 검토
- [ ] 문항 풀 재균형 필요성 평가

### 월간 체크리스트
- [ ] IRT 파라미터 재보정
- [ ] 앵커 문항 갱신
- [ ] 언어별 문항 품질 검토
- [ ] 시스템 성능 최적화

---

## 🔗 통합 가이드

### DreamSeedAI 교사용 대시보드 연동
```r
# portal_front/dashboard/app_teacher.R에 추가
observeEvent(input$view_drift_dashboard, {
  showModal(modalDialog(
    title = "Drift Monitoring",
    tags$iframe(
      src = "http://localhost:8012",
      width = "100%",
      height = "600px",
      frameborder = "0"
    ),
    size = "l"
  ))
})
```

### FastAPI 백엔드 연동
```python
# backend/app/routers/analytics.py
from fastapi import APIRouter
from shared.analytics.models.drift_detector import BayesianDriftDetector

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/drift/alerts")
async def get_drift_alerts():
    detector = BayesianDriftDetector()
    # ... 드리프트 탐지 로직
    return alerts
```

---

## 📚 참고 자료

- [Grafana 대시보드 문서](https://grafana.com/docs/grafana/latest/dashboards/)
- [R Shiny 가이드](https://shiny.rstudio.com/)
- [PostgreSQL Materialized Views](https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
- [IRT 파라미터 드리프트 탐지](https://en.wikipedia.org/wiki/Item_response_theory)

---

**DreamSeedAI Analytics Team**
