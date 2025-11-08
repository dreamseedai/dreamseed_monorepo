# 교사용 클래스 모니터링 대시보드

## 개요

교사가 **1분 안에 개입 대상을 결정**할 수 있도록 설계된 통합 분석 포털입니다.

### 핵심 기능

#### 1. 클래스 스냅샷
- **평균 θ**: 클래스 전체 능력 평균
- **중앙값 θ**: 중간 수준 학생 능력
- **상·하위 10% 구간**: 능력 분포 범위
- **주간 성장률 Δθ**: 지난 7일간 평균 성장
- **출석 안정도**: 결석/지각 비율 요약

#### 2. 리스크 알림 카드
- **개선 저조 학생**: 7일 성장률 < 0.02인 학생 목록
- **출석 불규칙 학생**: 결석+지각 비율 > 25%인 학생 목록
- 실시간 알림으로 즉각 개입 가능

#### 3. 그룹 θ 히스토그램
- 24개 구간으로 능력 분포 시각화
- 각 구간별 추천 액션:
  - **θ < -1**: 보정 과제 필요 (빨강)
  - **-1 ≤ θ < 0**: 보충수업 권장 (주황)
  - **0 ≤ θ < 1**: 정상 진도 (파랑)
  - **θ ≥ 1**: 상향 도전 과제 (초록)

#### 4. 학생 드릴다운
- **최근 4주 θ 추이**: 스파크라인으로 시각화
- **출석 타임라인**: 최근 30일 결석/지각 패턴
- **취약 스킬 TOP3**: 개선이 필요한 스킬 태그
- **정렬 우선순위**: θ 낮음 → 성장 낮음 → 불규칙률 높음

---

## 설치 및 실행

### 1. 필수 R 패키지 설치

```r
install.packages(c(
  "shiny",
  "shinydashboard",
  "DT",
  "arrow",
  "dplyr",
  "plotly",
  "lubridate",
  "stringr",
  "tidyr",
  "tibble"
))
```

### 2. 샘플 데이터 생성 (선택)

데이터셋이 없으면 자동으로 부트스트랩되지만, 수동으로 생성할 수도 있습니다:

```bash
Rscript dashboard/bootstrap_data.R
```

생성되는 데이터:
- `data/datasets/classes.parquet`: 클래스 메타데이터
- `data/datasets/students.parquet`: 학생 메타데이터
- `data/datasets/student_theta/`: 학생별 일별 θ (파티션: org_id/class_id)
- `data/datasets/attendance/`: 출석 기록 (파티션: org_id/class_id)
- `data/datasets/skill_weakness.parquet`: 스킬 취약점
- `data/datasets/response_stats.parquet`: 문항 반응 통계

### 3. 대시보드 실행

#### 방법 1: 실행 스크립트 사용 (권장)

```bash
chmod +x dashboard/run_teacher_dashboard.sh
./dashboard/run_teacher_dashboard.sh
```

#### 방법 2: 직접 실행

```bash
# 개발 모드 (프록시 없이)
DEV_USER=teacher01 DEV_ORG_ID=org_001 DEV_ROLES=teacher \
Rscript -e 'shiny::runApp("dashboard/app_teacher.R", host="0.0.0.0", port=8081)'
```

#### 방법 3: 프로덕션 모드 (프록시 헤더 사용)

프록시가 다음 헤더를 주입하는 경우:
- `X-User`: 사용자 ID
- `X-Org-Id`: 조직 ID
- `X-Roles`: 역할 (쉼표 구분)

```bash
Rscript -e 'shiny::runApp("dashboard/app_teacher.R", host="0.0.0.0", port=8081)'
```

### 4. 브라우저 접속

```
http://localhost:8081
```

---

## 데이터 구조

### Parquet 파티셔닝

성능 최적화를 위해 `student_theta`와 `attendance`는 파티션으로 저장됩니다:

```
data/datasets/
├── student_theta/
│   ├── org_id=org_001/
│   │   ├── class_id=org_001_class_01/
│   │   │   └── part-0.parquet
│   │   └── class_id=org_001_class_02/
│   │       └── part-0.parquet
│   └── org_id=org_002/
│       └── ...
└── attendance/
    └── (동일 구조)
```

이를 통해:
- **푸시다운 필터링**: 필요한 파티션만 읽음
- **프루닝**: 불필요한 데이터 스캔 방지
- **빠른 쿼리**: org/class 스코프 필터링 시 성능 향상

---

## 성능 튜닝

### 1. 리스크 임계값 조정

`app_teacher.R`에서 임계값을 수정:

```r
# 개선 저조 기준 (기본: 0.02)
filter(delta_7d < 0.02)  # → 0.01로 변경하면 더 엄격

# 출석 불규칙 기준 (기본: 25%)
filter(irregular_rate > 0.25)  # → 0.15로 변경하면 더 엄격
```

### 2. 히스토그램 버킷 수 조정

```r
# 기본: 24개 버킷
compute_theta_histogram(class_id, org_id, bins = 24)

# 더 세밀한 분석: 48개 버킷
compute_theta_histogram(class_id, org_id, bins = 48)
```

### 3. 학생 테이블 정렬 규칙

현재 정렬 우선순위:
1. θ 낮음 (오름차순)
2. 7일 성장 낮음 (오름차순)
3. 불규칙률 높음 (내림차순)

`app_teacher.R`에서 수정:

```r
options = list(
  order = list(list(2, 'asc'), list(3, 'asc'), list(6, 'desc'))
)
```

---

## 확장 가능성

### 1. 버킷별 CTA 버튼 추가

히스토그램 각 버킷에 클릭 가능한 액션 버튼 추가:

```r
# 예: "보정 과제 배정" 버튼 클릭 시 API 호출
observeEvent(input$assign_task_btn, {
  # POST /api/tasks/assign
  # body: { student_ids: [...], task_type: "remedial" }
})
```

### 2. 문항 반응 이상치 카드

`response_stats` 데이터를 활용하여 추가 리스크 카드 생성:

```r
# 추측 패턴 과다 학생
high_guess <- response_stats %>%
  filter(guess_like_rate > 0.3) %>%
  arrange(desc(guess_like_rate))

# 무응답 과다 학생
high_omit <- response_stats %>%
  filter(omit_rate > 0.15) %>%
  arrange(desc(omit_rate))
```

### 3. 학사 시스템 연동

기존 IdP/SSO와 통합:

```r
# 프록시 헤더 매핑
get_user_context <- function(session) {
  list(
    user_id = session$request$HTTP_X_SAML_UID,
    org_id = session$request$HTTP_X_SCHOOL_ID,
    roles = strsplit(session$request$HTTP_X_ROLES, ",")[[1]]
  )
}
```

---

## 문제 해결

### Q1. "데이터셋이 없습니다" 오류

**원인**: `data/datasets/` 디렉토리가 비어있음

**해결**:
```bash
Rscript dashboard/bootstrap_data.R
```

### Q2. R 패키지 설치 오류

**원인**: 시스템 라이브러리 누락 (특히 `arrow`)

**해결** (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install -y libcurl4-openssl-dev libssl-dev libxml2-dev
```

**해결** (macOS):
```bash
brew install openssl curl
```

### Q3. 대시보드가 느림

**원인**: 대용량 데이터 로드

**해결**:
1. 파티션 필터링 확인 (org_id/class_id)
2. Arrow 데이터셋 `collect()` 호출 최소화
3. 요약 통계 먼저 계산 후 필요시 상세 데이터 로드

---

## 라이선스

MIT License

---

## 문의

기술 지원: DreamSeed AI 팀
