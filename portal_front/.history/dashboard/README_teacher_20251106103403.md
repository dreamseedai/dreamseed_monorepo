# 교사용 클래스 모니터 대시보드

## 목표
**교사가 1분 이내에 介入(개입) 대상을 결정**할 수 있도록 클래스 상태를 시각화하고 리스크를 자동 탐지합니다.

## 핵심 화면 구성

### 1. 클래스 스냅샷 (6개 KPI)
- **평균 θ**: 클래스 전체 능력 수준
- **중앙값 θ**: 중심 경향성
- **상·하위 10% 구간**: P10 ~ P90 범위 (분산도)
- **주간 성장률 Δθ**: 최근 7일 vs 이전 7일 평균 변화
- **출석 안정도**: 평균 결석률 · 지각률
- **리스크 카운트**: 개선 저조 / 출석 불규칙 / 문항 반응 이상 학생 수

### 2. 리스크 카드 (3종)
| 리스크 유형 | 기준 (환경변수로 조정 가능) | 색상 |
|------------|---------------------------|------|
| **개선 저조** | Δ7d < 0.02 (RISK_THETA_DELTA) | 30% 이상: 빨강, 1명 이상: 노랑 |
| **출석 불규칙** | 결석+지각 > 25% (RISK_ATTENDANCE) | 20% 이상: 빨강, 1명 이상: 노랑 |
| **문항 반응 이상** | guess_rate > 15% OR omit_rate > 12% | 15% 이상: 빨강, 1명 이상: 노랑 |

### 3. 그룹 θ 히스토그램
- **24 bins**, 5개 버킷으로 색상 구분:
  - 매우낮음 (≤-1.5): 빨강 (#d32f2f)
  - 낮음 (-1.5~-0.5): 주황 (#f57c00)
  - 중간 (-0.5~0.5): 노랑 (#fbc02d)
  - 높음 (0.5~1.5): 연두 (#689f38)
  - 매우높음 (>1.5): 초록 (#388e3c)

### 4. 버킷별 추천 액션 (CTA 버튼)
각 버킷별 학생 수와 추천 액션을 클릭형 버튼으로 제공:
- **매우낮음 → 보정 과제 배정**
- **낮음 → 보충수업 추천**
- **중간 → 핵심 연습 강화**
- **높음 → 상향 도전**
- **매우높음 → 심화/확장**

*(현재 버전: 클릭 시 알림 표시. 추후 과제 배정 API 연동 가능)*

### 5. 학생 목록 (드릴다운)
- **다중 정렬**: `risk_score DESC, theta ASC, delta_7d ASC`
  - **risk_score**: 개선 저조(3점) + 출석 불규칙(2점) + 반응 이상(1점)
- **컬럼**:
  - student_id, student_name, theta, delta_7d, absences_14d, tardies_14d, guess_rate, omit_rate, weak_tags
- **행 클릭 → 모달 상세**:
  - 최근 4주 θ 스파크라인 (plotly)
  - 출석 타임라인 (present/tardy/absent 색상 구분)
  - 취약 스킬태그 TOP3

## 권한/필터

프록시가 주입한 헤더 기반:
- `X-User`: 사용자 ID
- `X-Org-Id`: 조직 ID (org 스코프 필터)
- `X-Roles`: 역할 (teacher, admin 등)

로컬 테스트 시 환경변수 사용:
```bash
export DEV_USER=teacher01
export DEV_ORG_ID=org_001
export DEV_ROLES=teacher
```

## 성능 최적화

- **Arrow dataset**: Parquet 파티션 (org_id, class_id)으로 푸시다운/프루닝 적용
- **지연 수집**: 요약 통계 먼저 계산 후 필요 시점에 `collect()`
- **스레드 활성화**: `options(arrow.use_threads = TRUE)`

## 실행

### 종속 패키지
```r
install.packages(c("shiny", "shinydashboard", "DT", "arrow", "dplyr", "plotly", "lubridate", "stringr", "tidyr", "tibble"))
```

### 로컬 실행
```bash
# 기본 포트 8081
Rscript -e 'shiny::runApp("portal_front/dashboard/app_teacher.R", host="0.0.0.0", port=8081)'

# 리스크 임계값 커스터마이징
export RISK_THETA_DELTA=0.03
export RISK_ATTENDANCE=0.30
export RISK_GUESS=0.20
export RISK_OMIT=0.15
Rscript -e 'shiny::runApp("portal_front/dashboard/app_teacher.R", host="0.0.0.0", port=8081)'
```

### 프로덕션 배포
nginx 리버스 프록시 + JWT 헤더 주입 패턴:
```nginx
location /dashboard/teacher/ {
    proxy_pass http://localhost:8081/;
    proxy_set_header X-User $jwt_claim_sub;
    proxy_set_header X-Org-Id $jwt_claim_org_id;
    proxy_set_header X-Roles $jwt_claim_roles;
}
```

참고: `infra/nginx/dashboard.dreamseedai.com.conf` 예제

## 임의 데이터 부트스트랩

`DATASET_ROOT` 미지정 시 자동으로 `data/datasets/`에 demo 데이터 생성:
- **classes**: org_id, class_id, class_name (10개 조직 × 10개 클래스)
- **students**: 클래스당 30명
- **student_theta**: 최근 90일 일별 θ 시계열
- **attendance**: 최근 90일 일별 출결 (present/tardy/absent)
- **skill_weakness**: 학생별 취약 스킬태그 TOP3
- **response_stats**: 학생별 guess_like_rate, omit_rate

Parquet 포맷 + org_id/class_id 파티션으로 저장

## 튜닝 포인트 (1분 의사결정 최적화)

### 1. 리스크 임계값 조정
환경변수로 학교 정책 반영:
```bash
export RISK_THETA_DELTA=0.02      # 주간 성장 임계
export RISK_ATTENDANCE=0.25       # 결석+지각 비율
export RISK_GUESS=0.15            # guess_like_rate
export RISK_OMIT=0.12             # omit_rate
```

### 2. 학생 테이블 기본 정렬
현재: **리스크 우선 → 낮은 θ → 낮은 Δ7d** 순
- risk_score: 다중 리스크 가중합 (개선 저조 3점, 출석 2점, 반응 이상 1점)
- 필요 시 컬럼 헤더 클릭으로 재정렬 가능

### 3. 버킷별 CTA → 과제 배정 API 연동 ✅ **구현완료**
각 버킷 CTA 버튼 클릭 시:
1. **학생 테이블 필터링**: 해당 θ 범위로 자동 필터
2. **과제 배정 API 호출**: FastAPI `/api/assignments` 엔드포인트로 POST 요청
3. **시각적 피드백**: 활성 필터는 파란색 강조, "필터 초기화" 버튼 표시

#### 과제 템플릿 매핑:
- **매우낮음** → `remedial_basics` (기본 개념 보정)
- **낮음** → `supplementary_review` (보충 복습)
- **중간** → `core_practice` (핵심 연습)
- **높음** → `challenge_advanced` (상향 도전)
- **매우높음** → `enrichment_extension` (심화 확장)

#### API 설정:
```bash
export ASSIGNMENT_API_URL=http://localhost:8000/api/assignments
export ETL_API_TOKEN=your_jwt_token_here  # 선택적
```

FastAPI 서버 실행:
```bash
cd portal_api
uvicorn assignment_api:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 문항 반응 이상 패턴 세부 분석 ✅ **구현완료**
Collapsible 섹션에 4개 패턴 카드 + 히트맵 제공:

#### 패턴 분류:
- **Pure Guessing**: guess_rate > 15% & omit_rate < 5%
- **Strategic Omit**: omit_rate > 12% & guess_rate < 5%
- **Rapid-Fire**: rapid_fire_rate > 10% & avg_response_time < 20초
- **복합 이상 패턴**: 위 3가지 모두 충족

#### 문항별 이상치 히트맵:
- 이상률 상위 20개 문항 자동 선택
- X축: 문항 ID, Y축: 패턴 유형 (guess/omit/rapid)
- 색상: 빨강(높음) ~ 흰색(낮음) 히트맵
- Plotly 인터랙티브 차트 (줌/팬 가능)

### 5. 실시간 데이터 ETL 파이프라인 ✅ **구현완료**
백그라운드 동기화 스크립트 제공:

#### 기능:
- **학사 출결 시스템** → `attendance` 데이터셋 자동 동기화
- **평가 시스템** → `response_stats` 데이터셋 자동 업데이트
- 증분 업데이트 (마지막 동기 이후 변경분만)
- 중복 제거 및 Parquet 파티션 유지

#### 실행:
```bash
# 환경변수 설정
export DATASET_ROOT=data/datasets
export ATTENDANCE_API=http://localhost:8000/api/attendance
export RESPONSE_API=http://localhost:8000/api/response_stats
export ETL_INTERVAL=300  # 5분마다 동기화
export ETL_API_TOKEN=your_token_here

# ETL 파이프라인 시작
Rscript portal_front/dashboard/etl_realtime.R
```

#### Systemd 서비스 등록 (프로덕션):
```ini
# /etc/systemd/system/dashboard-etl.service
[Unit]
Description=Teacher Dashboard ETL Pipeline
After=network.target

[Service]
Type=simple
User=shiny
WorkingDirectory=/opt/dashboard
Environment="DATASET_ROOT=/opt/dashboard/data/datasets"
Environment="ATTENDANCE_API=http://internal-api:8000/api/attendance"
Environment="RESPONSE_API=http://internal-api:8000/api/response_stats"
Environment="ETL_INTERVAL=300"
Environment="ETL_API_TOKEN=production_token"
ExecStart=/usr/bin/Rscript /opt/dashboard/etl_realtime.R
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable dashboard-etl
sudo systemctl start dashboard-etl
sudo journalctl -u dashboard-etl -f  # 로그 확인
```

#### API 응답 형식:
```json
{
  "records": [
    {
      "org_id": "org_001",
      "class_id": "CLS0001",
      "student_id": "STD123456",
      "date": "2025-11-06",
      "status": "present"
    }
  ]
}
```

## 연동 가능한 시스템

- **학사 출결 시스템**: attendance 데이터 실시간 ETL
- **평가 시스템**: response_stats 연계 (문항 반응 시간, 정답률)
- **과제 관리 API**: 버킷별 CTA → 자동 배정
- **IdP (Keycloak/Auth0)**: JWT 역할 매핑 (teacher, admin, principal)

## 참고 문서

- `infra/nginx/README.md`: JWT 검증 및 헤더 주입 패턴
- `infra/systemd/README.md`: Shiny 앱 서비스 등록
- `portal_front/dashboard/app.R`: 관리자용 대시보드 (org/role 필터 예제)

## 라이선스
DreamSeed AI 내부용
