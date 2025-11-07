# 🤝 Copilot → Windsurf 인수인계 문서

**작업 일시**: 2025-11-06  
**작업자**: GitHub Copilot  
**인수자**: Windsurf  
**브랜치**: `staging/attempt-view-lock-v1`

---

## ✅ 완료된 작업 (4가지 개선사항)

### 1️⃣ 버킷→과제ID 매핑의 설정 파일화 (YAML 기반)

**구현 위치**: `app_teacher.R` + `config/assignment_templates.yaml`

**핵심 내용**:
- 하드코딩된 과제 템플릿을 YAML 설정 파일로 외부화
- 30초마다 파일 변경 자동 감지 → **핫리로드** (재시작 불필요)
- 템플릿/권한/IdP 매핑 통합 관리

**설정 파일 구조** (`config/assignment_templates.yaml`):
```yaml
templates:
  very_low:
    template_id: remedial_basics
    catalog_ids: [MATH-1A, MATH-1B]
    tags: [remedial, foundational]
    difficulty: 1
    estimated_minutes: 30
  low:
    template_id: supplementary_review
    catalog_ids: [MATH-2A, MATH-2B]
  # ... mid, high, very_high 동일 구조

permissions:
  admin:    { can_assign: true, can_view_all_classes: true,  can_modify_thresholds: true }
  teacher:  { can_assign: true, can_view_all_classes: false, can_modify_thresholds: false }
  counselor:{ can_assign: false, can_view_all_classes: true, can_modify_thresholds: false }
  viewer:   { can_assign: false, can_view_all_classes: false, can_modify_thresholds: false }

idp_header_mappings:
  keycloak:
    user_header: X-Auth-Request-User
    org_header: X-Auth-Request-Groups
    roles_header: X-Auth-Request-Roles
```

**코드 변경**:
```r
# 글로벌 설정 로드
CONFIG <- load_config()  # config/assignment_templates.yaml 읽기
ASSIGNMENT_TEMPLATES <- CONFIG$templates %||% list()
ROLE_PERMISSIONS <- CONFIG$permissions %||% list()

# 서버에서 30초마다 핫리로드
config_reload_timer <- reactiveTimer(30000)
observe({
  if (check_config_reload()) {
    CONFIG <<- load_config()
    ASSIGNMENT_TEMPLATES <<- CONFIG$templates
    showNotification("⚡ 설정 파일이 업데이트되었습니다")
  }
})
```

**테스트 방법**:
```bash
# 1. 설정 수정
vim config/assignment_templates.yaml
# very_low.template_id 를 "new_template" 으로 변경

# 2. 30초 이내 알림 확인
# "⚡ 설정 파일이 업데이트되었습니다 (템플릿/권한 재로드 완료)"

# 3. "매우낮음" CTA 클릭 → new_template 사용 확인
```

---

### 2️⃣ 학생 테이블 "즉시 배정" 액션 컬럼

**구현 위치**: `app_teacher.R` (UI + 서버)

**핵심 내용**:
- 학생 테이블 각 행에 **"과제 배정" 버튼** 추가
- 클릭 시 학생의 θ 버킷 자동 판단 → 적절한 템플릿 선택 → API 호출
- 권한 체크: `teacher` 또는 `admin`만 허용
- 성공/실패 알림 (학생 이름 포함)

**UI 변경**:
```r
# students_tbl에 theta_bucket 컬럼 추가
theta_bucket = case_when(
  theta <= -1.5 ~ "very_low",
  theta > -1.5 & theta <= -0.5 ~ "low",
  theta > -0.5 & theta <= 0.5 ~ "mid",
  theta > 0.5 & theta <= 1.5 ~ "high",
  theta > 1.5 ~ "very_high",
  TRUE ~ "mid"
)

# 테이블에 액션 버튼 컬럼 추가
df$action <- sprintf(
  '<button class="btn btn-primary btn-sm assign-btn" data-student-id="%s" data-theta-bucket="%s">과제 배정</button>',
  students_tbl()$student_id,
  students_tbl()$theta_bucket
)
```

**JavaScript 이벤트 핸들러**:
```javascript
$(document).on('click', '.assign-btn', function() {
  var studentId = $(this).data('student-id');
  var thetaBucket = $(this).data('theta-bucket');
  Shiny.setInputValue('assign_single_student', {
    student_id: studentId, 
    theta_bucket: thetaBucket, 
    timestamp: Date.now()
  }, {priority: 'event'});
});
```

**서버 핸들러**:
```r
observeEvent(input$assign_single_student, {
  data <- input$assign_single_student
  student_id <- data$student_id
  theta_bucket <- data$theta_bucket
  
  # 권한 체크
  if (!(has_role(claims, "teacher") || has_role(claims, "admin"))) {
    showNotification("과제 배정 권한이 없습니다.", type = "error")
    return()
  }
  
  # 템플릿 선택
  template_id <- ASSIGNMENT_TEMPLATES[[theta_bucket]]$template_id %||% "core_practice"
  
  # API 호출
  ok <- call_assignment_api(c(student_id), template_id, claims, assignment_auth)
  
  # 알림
  showNotification(
    sprintf("✓ %s 학생에게 '%s' 과제를 배정했습니다.", student_name, template_id),
    type = if (ok) "message" else "error"
  )
})
```

**테스트 방법**:
```r
# 1. 학생 테이블에서 임의 학생 선택
# 2. "과제 배정" 버튼 클릭
# 3. 알림 확인: "✓ [학생명] 학생에게 '[template_id]' 과제를 배정했습니다."
# 4. API 로그 확인: [assignment API] success: 1 students, template=remedial_basics
```

---

### 3️⃣ 출석 리스크에 요일 편차 반영

**구현 위치**: `app_teacher.R` (`attn_metrics_tbl` reactive)

**핵심 내용**:
- 요일별(월~일) 결석률/지각률 분산 계산
- 학생별 `abs_rate_variance`, `tardy_rate_variance` 산출
- 학생 테이블에 `abs_variance`, `worst_day` 컬럼 추가
- 어느 요일이 특히 취약한지 식별 (예: 매주 금요일 결석)

**알고리즘**:
```r
dow_variance <- adf %>% mutate(
  is_abs = status == "absent",
  is_tardy = status == "tardy",
  weekday = lubridate::wday(date, label = TRUE, abbr = TRUE, week_start = 1)  # Mon=1
) %>% 
# 1. 학생×요일별 결석률 계산
group_by(student_id, weekday) %>% summarise(
  abs_rate_dow = mean(is_abs),
  tardy_rate_dow = mean(is_tardy)
) %>% 
# 2. 학생별 분산 계산
group_by(student_id) %>% summarise(
  abs_rate_variance = var(abs_rate_dow, na.rm = TRUE),
  tardy_rate_variance = var(tardy_rate_dow, na.rm = TRUE),
  worst_day = weekday[which.max(abs_rate_dow)],  # 결석 최다 요일
  worst_day_abs_rate = max(abs_rate_dow, na.rm = TRUE)
)
```

**학생 테이블 출력**:
```r
transmute(
  student_id, student_name, theta, delta_7d,
  absences_14d, tardies_14d,
  abs_variance = round(abs_rate_variance, 4),  # 추가
  worst_day = as.character(worst_day),         # 추가
  guess_rate, omit_rate, weak_tags, risk_score, theta_bucket
)
```

**해석 가이드**:
- **abs_variance < 0.01**: 규칙적인 출석 패턴
- **abs_variance 0.01~0.05**: 특정 요일 문제
- **abs_variance > 0.05**: 매우 불규칙 (예: 매주 금요일만 결석)

**예시**:
```
학생: 이영희
abs_variance: 0.08
worst_day: "Fri"
worst_day_abs_rate: 0.40 (40%)

→ 매주 금요일 40% 결석 → 학부모 상담 필요
```

**테스트 방법**:
```r
# 1. 학생 테이블에서 abs_variance 컬럼 확인
# 2. 높은 값(>0.05) 학생 찾기
# 3. worst_day 확인 (예: "Mon", "Fri")
# 4. 드릴다운 모달에서 "출석 타임라인" 차트로 패턴 시각화
```

---

### 4️⃣ 문항 반응 이상치 카드 → 바로가기(모달)

**구현 위치**: `app_teacher.R` (UI + 서버)

**핵심 내용**:
- 4가지 이상 패턴별 **빠른 접근 버튼** 추가
- 클릭 시 해당 조건 만족 학생 목록 모달 표시
- 정렬 가능한 DT 테이블로 상세 정보 제공

**UI 추가**:
```r
fluidRow(
  column(3, actionButton("show_pure_guess_modal", "Pure Guessing 학생 보기", ...)),
  column(3, actionButton("show_strategic_omit_modal", "Strategic Omit 학생 보기", ...)),
  column(3, actionButton("show_rapid_fire_modal", "Rapid-Fire 학생 보기", ...)),
  column(3, actionButton("show_multi_pattern_modal", "복합 패턴 학생 보기", ...))
)
```

**조건 정의**:
| 패턴 | 조건 |
|------|------|
| Pure Guessing | `guess_like_rate > RISK_GUESS_THRESHOLD` AND `omit_rate < 0.05` |
| Strategic Omit | `omit_rate > RISK_OMIT_THRESHOLD` AND `guess_like_rate < 0.05` |
| Rapid-Fire | `rapid_fire_rate > 0.10` AND `avg_response_time < 20` |
| 복합 이상 패턴 | 위 3가지 모두 초과 |

**서버 핸들러 예시** (Pure Guessing):
```r
observeEvent(input$show_pure_guess_modal, {
  rsp <- resp_ds() %>% collect()
  students <- students_ds() %>% select(student_id, student_name) %>% collect()
  
  anomaly_students <- rsp %>%
    filter(guess_like_rate > RISK_GUESS_THRESHOLD & omit_rate < 0.05) %>%
    left_join(students, by = "student_id") %>%
    select(student_id, student_name, guess_like_rate, omit_rate, rapid_fire_rate, avg_response_time) %>%
    arrange(desc(guess_like_rate))
  
  showModal(modalDialog(
    size = "l",
    title = sprintf("Pure Guessing 패턴 학생 목록 (%d명)", nrow(anomaly_students)),
    renderDT({ datatable(anomaly_students, rownames = FALSE, ...) }),
    footer = modalButton("닫기")
  ))
})
```

**테스트 방법**:
```r
# 1. "문항 반응 이상 패턴 세부 분석" 박스 펼치기
# 2. "Pure Guessing 학생 보기" 클릭
# 3. 모달에서 guess_rate 컬럼 클릭 → 내림차순 정렬
# 4. 최상위 학생 ID 확인
# 5. 학생 테이블에서 해당 학생 검색
```

---

## 🔧 환경 변수 / 설정

### IdP/프록시 헤더 매핑
```bash
# 헤더 이름 커스터마이징
export AUTH_HEADER_USER="X-User"           # 기본값
export AUTH_HEADER_ORG="X-Org-Id"          # 기본값
export AUTH_HEADER_ROLES="X-Roles"         # 기본값
export AUTH_HEADER_GROUPS="X-Groups"       # 선택

# 구분자
export AUTH_ROLES_SEPARATOR=","            # 기본값
```

### 임계값
```bash
export RISK_THETA_DELTA="0.02"      # 7일 θ 변화 임계값
export RISK_ATTENDANCE="0.25"       # 출석률 임계값 (25%)
export RISK_GUESS="0.15"            # 추측 비율 임계값 (15%)
export RISK_OMIT="0.12"             # 무응답 비율 임계값 (12%)
```

### 과제 API
```bash
export ASSIGNMENT_API_URL="http://localhost:8000/api/assignments"
export ASSIGNMENT_API_BEARER="Bearer eyJ..."  # 선택 (JWT 토큰)
```

### 로컬 개발
```bash
export DEV_USER="test_teacher"
export DEV_ORG_ID="org_test"
export DEV_ROLES="teacher,admin"
```

---

## 📁 수정/생성 파일 목록

### 수정된 파일
- **`app_teacher.R`** (973줄)
  - `library(yaml)` 추가
  - `load_config()`, `check_config_reload()` 함수 추가
  - 핫리로드 타이머 (30초)
  - 개별 학생 배정 핸들러
  - 요일별 분산 계산
  - 4개 이상 패턴 모달 핸들러

### 생성된 파일
- **`config/assignment_templates.yaml`** - 과제 템플릿 설정
- **`ENHANCEMENTS_v2.md`** - 상세 기술 문서 (17개 섹션)
- **`QUICKSTART_v2.md`** - 빠른 시작 가이드
- **`INTEGRATION_GUIDE.md`** - YAML 통합 가이드
- **`HANDOFF_TO_WINDSURF.md`** - 본 인수인계 문서

---

## 🚀 실행 방법

```bash
# 1. 디렉토리 이동
cd /home/won/projects/dreamseed_monorepo/portal_front/dashboard

# 2. 실행 (방법 1: 직접)
Rscript app_teacher.R --port 8081

# 3. 실행 (방법 2: shiny::runApp)
Rscript -e 'shiny::runApp("app_teacher.R", host="0.0.0.0", port=8081)'

# 4. 실행 (방법 3: systemd)
sudo systemctl start portal-teacher-dashboard

# 5. 브라우저 접속
http://localhost:8081
```

---

## ⚠️ 남은 작업 (귀사 정책 반영 필요)

### 1. assignment_templates.yaml 실제 값 채우기
**현재**: 예시 값 (MATH-1A, MATH-2A 등)  
**필요**: 귀사 실제 과제 카탈로그 ID, 난이도, 소요시간  
**예시**:
```yaml
templates:
  very_low:
    template_id: "your_actual_template_id"
    catalog_ids: ["YOUR-CATALOG-1", "YOUR-CATALOG-2"]
```

### 2. AUTH_HEADER_* 및 역할명 정규화
**현재**: Keycloak/Auth0 예시  
**필요**: 귀사 IdP 헤더 스키마  
**예시**:
```yaml
idp_header_mappings:
  your_idp:
    user_header: "X-Custom-User"
    org_header: "X-Custom-Org"
    roles_header: "X-Custom-Roles"
```

**역할명 정규화**:
```r
canonicalize_roles <- function(raw_roles) {
  # 현재: "admin|관리자|principal|교장" → "admin"
  # 추가 필요: "담임교사" → "teacher", "부장교사" → "admin" 등
}
```

### 3. 과제 배정 API 스펙 확정
**현재**: 가정한 JSON 구조  
**필요**: 실제 API 엔드포인트, 필드명, 에러 코드  
**예시**:
```javascript
// 현재 payload
{
  "student_ids": ["S001"],
  "template": "remedial_basics",
  "assigned_by": "teacher123",
  "org_id": "org_001",
  "timestamp": "2025-11-06T10:30:00Z"
}

// 실제 API가 다른 필드명을 요구하면 수정 필요
```

### 4. 출석 요일 편차 임계값 도입 여부
**현재**: 계산만 수행 (리스크 플래그 미반영)  
**옵션**: `abs_rate_variance > 0.01` 이면 리스크 카드에 반영  
**코드 예시**:
```r
# 리스크 점수에 요일 편차 추가
risk_score = improve_flag * 3 + 
             attn_flag * 2 + 
             resp_flag * 1 +
             dow_variance_flag * 1.5  # 추가
```

---

## 📖 추천 문서 읽기 순서 (Windsurf용)

### 빠르게 파악 (5분):
```bash
cat QUICKSTART_v2.md
```

### 상세 이해 (15분):
```bash
cat ENHANCEMENTS_v2.md
```

### 설정 변경:
```bash
cat INTEGRATION_GUIDE.md
vim config/assignment_templates.yaml
```

---

## 🧪 테스트 체크리스트

- [ ] **핫리로드**: `assignment_templates.yaml` 수정 → 30초 내 알림 확인
- [ ] **개별 배정**: 학생 테이블 "과제 배정" 클릭 → 알림 확인
- [ ] **요일 분산**: `abs_variance` 컬럼 확인 → 높은 값 학생 파악
- [ ] **이상 모달**: "Pure Guessing 학생 보기" 클릭 → 모달 정렬 테스트
- [ ] **권한 체크**: viewer 역할로 과제 배정 시도 → 거부 확인

---

## 📞 질문/이슈

### Windsurf가 확인해야 할 사항:
1. **설정 파일 경로**: `config/assignment_templates.yaml` 정상 로드되는지
2. **핫리로드 타이머**: 30초마다 `check_config_reload()` 호출 확인
3. **JavaScript 이벤트**: `.assign-btn` 클릭 시 `input$assign_single_student` 전달 확인
4. **요일 컬럼**: `lubridate::wday()` 결과가 "Mon", "Tue" 형식인지
5. **모달 렌더링**: `renderDT()` 함수가 모달 내부에서 정상 작동하는지

### 알려진 제약사항:
- 핫리로드는 30초 간격 (즉시 반영 아님, 파일 시스템 watcher 미사용)
- 모달 DT는 reactive 컨텍스트 외부에서 렌더링 (일부 IDE에서 경고 가능)
- 요일 분산은 최소 2개 이상 요일 데이터 필요 (주말만 있으면 분산 계산 불가)

---

## ✅ 인수인계 완료 확인

- [x] 4가지 개선사항 모두 구현 완료
- [x] 코드에 주석 추가 (핵심 로직)
- [x] 문서 5개 작성 (QUICKSTART, ENHANCEMENTS, INTEGRATION, README, HANDOFF)
- [x] 테스트 체크리스트 제공
- [x] 남은 작업 명시 (귀사 정책 반영)
- [x] 환경 변수 가이드 제공

---

**인계자**: GitHub Copilot  
**인수자**: Windsurf  
**인계 일시**: 2025-11-06  
**상태**: ✅ 인수인계 준비 완료

---

## 📝 Windsurf 액션 아이템

### 즉시 수행:
1. `QUICKSTART_v2.md` 읽기 (5분)
2. `app_teacher.R` 실행 테스트
3. 핫리로드 테스트 (YAML 수정 후 30초 대기)

### 단기 작업:
1. `assignment_templates.yaml` 실제 값 채우기
2. IdP 헤더 매핑 확정
3. 과제 API 스펙 맞추기

### 장기 고려:
1. 요일 편차 임계값 도입 여부 결정
2. 핫리로드 간격 조정 (30초 → 10초?)
3. 모달에 bulk assignment 기능 추가

---

**Happy Coding! 🚀**

GitHub Copilot이 작업한 모든 내용이 위 문서와 코드에 정리되어 있습니다.  
궁금한 점은 `QUICKSTART_v2.md` 또는 `ENHANCEMENTS_v2.md`를 참고하세요!
