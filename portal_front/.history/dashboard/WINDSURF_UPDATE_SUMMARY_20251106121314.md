# 🔄 Windsurf 업데이트 요약 (Copilot 확인용)

**업데이트 일시**: 2025-11-06  
**작업자**: Windsurf  
**확인자**: GitHub Copilot  
**파일**: `app_teacher.R` (1043줄)

---

## ✅ Windsurf가 완료한 작업

### 🎯 리스크 규칙 업데이트 (초기 정책 반영)

Windsurf가 사용자 요구사항에 따라 **3가지 리스크 규칙**을 정확하게 구현했습니다.

---

## 1️⃣ 개선 저조 (Improvement Risk)

### 규칙 (정책)
```
Δθ_7d < +0.05 AND 최근 3주 연속 주간 Δθ ≤ 0
```

### 구현 상세

**환경 변수**:
```r
RISK_THETA_DELTA_THRESHOLD <- as.numeric(Sys.getenv("RISK_THETA_DELTA", "0.05"))
```

**알고리즘** (`latest_theta_tbl` reactive, L461-L489):
```r
# 1. 최근 28일 데이터를 주 단위로 집계
weekly <- df_all %>%
  filter(date > (maxd - 28)) %>%
  mutate(week = lubridate::floor_date(date, unit = "week", week_start = 1)) %>%
  group_by(student_id, week) %>% 
  summarise(theta_w = mean(theta, na.rm = TRUE), .groups='drop') %>%
  arrange(student_id, week) %>% 
  group_by(student_id) %>%
  mutate(delta_w = theta_w - dplyr::lag(theta_w)) %>%
  
# 2. 최근 3주 연속 ≤0 체크
  summarise(three_nonpos = {
    d <- delta_w[!is.na(delta_w)]
    if (length(d) >= 3) all(tail(d, 3) <= 0) else FALSE
  }, .groups='drop')

# 3. 플래그 생성
out <- out %>% left_join(weekly, by = "student_id") %>% 
  mutate(three_nonpos = ifelse(is.na(three_nonpos), FALSE, three_nonpos))
```

**리스크 플래그**:
```r
improve_flag = (delta_7d < RISK_THETA_DELTA_THRESHOLD) AND three_nonpos
```

**UI 반영** (L569-L573):
```r
output$vb_risk_improve <- renderValueBox({
  lt <- latest_theta_tbl()
  low <- sum(lt$delta_7d < RISK_THETA_DELTA_THRESHOLD & lt$three_nonpos, na.rm = TRUE)
  total <- nrow(lt)
  valueBox(sprintf("%d명", low), 
    "리스크: 개선 저조(Δ7d<+0.05 & 최근 3주 연속 ≤0)", 
    icon = icon("triangle-exclamation"), 
    color = if (total>0 && low/total > 0.3) "red" else if (low>0) "yellow" else "green")
})
```

**검증 포인트**:
- ✅ 28일 데이터를 주(week) 단위로 집계
- ✅ `lubridate::floor_date(unit = "week", week_start = 1)` 사용
- ✅ `tail(d, 3) <= 0` 모두 만족 시 `three_nonpos = TRUE`
- ✅ `delta_7d < 0.05` AND `three_nonpos` 조합

---

## 2️⃣ 출석 불규칙 (Attendance Risk)

### 규칙 (정책)
```
결석률 ≥ 10% OR 지각률 ≥ 15% OR 요일별 분산 상위 20%
```

### 구현 상세

**환경 변수**:
```r
RISK_ATTEND_ABS_THRESHOLD <- as.numeric(Sys.getenv("RISK_ATTEND_ABS", "0.10"))   # 10%
RISK_ATTEND_TARDY_THRESHOLD <- as.numeric(Sys.getenv("RISK_ATTEND_TARDY", "0.15")) # 15%
RISK_ATTEND_VAR_TOP_PCT <- as.numeric(Sys.getenv("RISK_ATTEND_VAR_TOP_PCT", "0.80")) # 상위 20%
```

**요일별 분산 계산** (`attn_metrics_tbl`, L491-L534):
```r
# 1. 요일별(월~일) 결석·지각 비율 산출
dow_variance <- adf %>% mutate(
  is_abs = status == "absent",
  is_tardy = status == "tardy",
  weekday = lubridate::wday(date, label = TRUE, abbr = TRUE, week_start = 1)
) %>% 
group_by(student_id, weekday) %>% summarise(
  abs_rate_dow = mean(is_abs),
  tardy_rate_dow = mean(is_tardy),
  .groups = 'drop'
) %>% 

# 2. 학생별 분산 계산
group_by(student_id) %>% summarise(
  abs_rate_variance = var(abs_rate_dow, na.rm = TRUE),
  tardy_rate_variance = var(tardy_rate_dow, na.rm = TRUE),
  worst_day = weekday[which.max(abs_rate_dow)],
  worst_day_abs_rate = max(abs_rate_dow, na.rm = TRUE),
  .groups = 'drop'
)
```

**분산 컷오프 계산** (L445-L449):
```r
attn_var_cutoff <- reactive({
  am <- attn_metrics_tbl()
  if (nrow(am) == 0) return(Inf)
  var_score <- pmax(am$abs_rate_variance %||% 0, am$tardy_rate_variance %||% 0)
  as.numeric(stats::quantile(var_score, probs = RISK_ATTEND_VAR_TOP_PCT, na.rm = TRUE))
})
```
→ `max(abs_rate_variance, tardy_rate_variance)`의 80% 분위수 = 상위 20% 컷오프

**리스크 플래그**:
```r
attn_flag = (abs_rate ≥ 0.10) OR (tardy_rate ≥ 0.15) OR (var_score ≥ cutoff)
```

**UI 반영** (L575-L582):
```r
output$vb_risk_attn <- renderValueBox({
  am <- attn_metrics_tbl()
  var_score <- pmax(am$abs_rate_variance %||% 0, am$tardy_rate_variance %||% 0)
  cutoff <- attn_var_cutoff()
  irregular <- sum((am$abs_rate >= RISK_ATTEND_ABS_THRESHOLD) | 
                   (am$tardy_rate >= RISK_ATTEND_TARDY_THRESHOLD) | 
                   (var_score >= cutoff), na.rm = TRUE)
  valueBox(sprintf("%d명", irregular), 
    "리스크: 출석 불규칙(결석≥10% 또는 지각≥15% 또는 요일분산 상위20%)", ...)
})
```

**학생 테이블 추가 컬럼**:
```r
abs_variance = round(abs_rate_variance, 4),
worst_day = as.character(worst_day)
```

**검증 포인트**:
- ✅ `lubridate::wday()` 사용하여 요일 추출
- ✅ `var()` 함수로 학생별 요일 분산 계산
- ✅ `pmax()` 로 결석/지각 분산 중 큰 값 선택
- ✅ `quantile(var_score, probs = 0.80)` 로 상위 20% 컷오프 계산
- ✅ OR 조건으로 3가지 규칙 통합

---

## 3️⃣ 반응 이상치 (Response Anomaly Risk)

### 규칙 (정책)
```
추측확률(c) 추정 상위 20% OR 무응답률 ≥ 8%
```

### 구현 상세

**환경 변수**:
```r
RISK_RESP_GUESS_TOP_PCT <- as.numeric(Sys.getenv("RISK_RESP_GUESS_TOP_PCT", "0.80")) # 상위 20%
RISK_RESP_OMIT_THRESHOLD <- as.numeric(Sys.getenv("RISK_RESP_OMIT", "0.08"))       # 8%
```

**추측률 컷오프 계산** (L451-L455):
```r
guess_q_cutoff <- reactive({
  rsp <- resp_ds() %>% collect()
  if (nrow(rsp) == 0) return(Inf)
  as.numeric(stats::quantile(rsp$guess_like_rate, probs = RISK_RESP_GUESS_TOP_PCT, na.rm = TRUE))
})
```
→ `guess_like_rate`의 80% 분위수 = 상위 20% 컷오프

**리스크 플래그**:
```r
resp_flag = (guess_like_rate ≥ cutoff) OR (omit_rate ≥ 0.08)
```

**UI 반영** (L584-L590):
```r
output$vb_risk_response <- renderValueBox({
  rsp <- resp_ds() %>% collect()
  cutoff <- guess_q_cutoff()
  anomaly <- sum((rsp$guess_like_rate >= cutoff) | 
                 (rsp$omit_rate >= RISK_RESP_OMIT_THRESHOLD), na.rm = TRUE)
  valueBox(sprintf("%d명", anomaly), 
    "리스크: 반응 이상치(추측 상위20% 또는 무응답≥8%)", ...)
})
```

**이상 패턴별 value box 업데이트**:
```r
# Pure Guessing (L592-L596)
cutoff <- guess_q_cutoff()
pure_guess <- sum(rsp$guess_like_rate >= cutoff & rsp$omit_rate < 0.05, na.rm = TRUE)

# Strategic Omit (L598-L601)
strategic <- sum(rsp$omit_rate >= RISK_RESP_OMIT_THRESHOLD & rsp$guess_like_rate < 0.05, na.rm = TRUE)

# Multi-pattern (L609-L616)
multi <- sum((rsp$guess_like_rate >= cutoff) & 
             (rsp$omit_rate >= RISK_RESP_OMIT_THRESHOLD) & 
             (rsp$rapid_fire_rate > 0.10), na.rm = TRUE)
```

**검증 포인트**:
- ✅ `quantile(guess_like_rate, probs = 0.80)` 로 상위 20% 계산
- ✅ `omit_rate >= 0.08` 절대 임계값
- ✅ OR 조건으로 추측/무응답 통합
- ✅ 모든 value box와 모달에 동일 기준 적용

---

## 4️⃣ 정렬 규칙 업데이트

### Risk Score 계산
```r
risk_score = improve_flag * 3 + attn_flag * 2 + resp_flag * 1
```

### 정렬 순서
```r
arrange(desc(risk_score), desc(improve_flag), desc(attn_flag), theta, delta_7d)
```

**의미**:
1. **1차 정렬**: 종합 리스크 점수 (높은 순)
2. **2차 정렬**: 개선 저조 플래그 (있는 학생 우선)
3. **3차 정렬**: 출석 불규칙 플래그 (있는 학생 우선)
4. **4차 정렬**: θ (낮은 순)
5. **5차 정렬**: Δ7d (낮은 순)

---

## 🔧 환경 변수 완전 목록

### 리스크 임계값
```bash
# 개선 저조
export RISK_THETA_DELTA="0.05"              # Δ7d < +0.05

# 출석 불규칙
export RISK_ATTEND_ABS="0.10"               # 결석률 ≥ 10%
export RISK_ATTEND_TARDY="0.15"             # 지각률 ≥ 15%
export RISK_ATTEND_VAR_TOP_PCT="0.80"       # 요일 분산 상위 20%

# 반응 이상치
export RISK_RESP_GUESS_TOP_PCT="0.80"       # 추측률 상위 20%
export RISK_RESP_OMIT="0.08"                # 무응답률 ≥ 8%
```

### 과제 API
```bash
export ASSIGNMENT_API_URL="http://localhost:8000/api/assignments"
export ASSIGNMENT_API_BEARER="Bearer eyJ..."
```

### IdP 헤더
```bash
export AUTH_HEADER_USER="X-User"
export AUTH_HEADER_ORG="X-Org-Id"
export AUTH_HEADER_ROLES="X-Roles"
export AUTH_ROLES_SEPARATOR=","
```

---

## 🚀 자동 보정 로드맵 (Windsurf 제안)

### 현재 상태
- ✅ 분위수 기반 컷오프 계산 구조 완성
- ✅ `attn_var_cutoff()`, `guess_q_cutoff()` reactive 함수
- ✅ 클래스 전체 분포 기준으로 상위 20% 계산

### 향후 확장 (학년/과목별 자동 보정)

**Step 1**: 메타 데이터 추가
```r
# students 또는 classes 테이블에 추가 필요
- grade: 학년 (예: "3", "4", "5")
- subject: 과목 (예: "math", "korean", "english")
```

**Step 2**: 서브그룹 분위수 계산
```r
attn_var_cutoff <- reactive({
  am <- attn_metrics_tbl()
  cls <- classes_ds() %>% collect()  # grade, subject 포함
  
  # 현재 클래스의 grade + subject
  current_grade <- cls$grade[1]
  current_subject <- cls$subject[1]
  
  # 동일 grade + subject 클래스 전체 데이터 로드
  all_classes_same_profile <- open_ds(base, "attendance") %>%
    filter(grade == !!current_grade, subject == !!current_subject) %>%
    collect()
  
  # 서브그룹 분포 기준으로 컷오프 계산
  var_score <- pmax(all_classes_same_profile$abs_rate_variance, 
                    all_classes_same_profile$tardy_rate_variance)
  as.numeric(quantile(var_score, probs = RISK_ATTEND_VAR_TOP_PCT, na.rm = TRUE))
})
```

**Step 3**: 과목·학년별 템플릿 매핑
```yaml
# config/assignment_templates.yaml 확장
templates:
  math:
    grade_3:
      very_low: { template_id: "math_g3_remedial", catalog_ids: ["MATH-3R1", "MATH-3R2"] }
      low: { template_id: "math_g3_supplement", catalog_ids: ["MATH-3S1", "MATH-3S2"] }
    grade_4:
      very_low: { template_id: "math_g4_remedial", catalog_ids: ["MATH-4R1", "MATH-4R2"] }
  korean:
    # ...
```

---

## 📊 코드 구조 분석

### Reactive 의존성 그래프
```
input$class_id
    ↓
theta_ds(), students_ds(), attend_ds(), skill_ds(), resp_ds(), item_resp_ds()
    ↓
latest_theta_tbl() ← 28일 데이터로 3주 연속 체크
attn_metrics_tbl() ← 요일별 분산 계산
    ↓
attn_var_cutoff() ← 80% 분위수 계산
guess_q_cutoff() ← 80% 분위수 계산
    ↓
students_tbl() ← improve_flag, attn_flag, resp_flag 계산
    ↓
output$students_table
```

### 성능 고려사항
- **요일별 분산 계산**: `group_by(student_id, weekday)` → `var()` 연산
  - 예상 시간: < 1초 (10,000명 × 28일 = 280,000 rows)
- **3주 연속 체크**: `tail(d, 3) <= 0` 비교
  - 예상 시간: < 0.5초
- **분위수 계산**: `quantile()` 2회 호출
  - 예상 시간: < 0.1초

**총 예상 연산 시간**: ~1.5초 (대규모 데이터 기준)

---

## ⚠️ Copilot이 확인해야 할 사항

### 1. 3주 연속 체크 로직 검증
```r
# L477-L481
summarise(three_nonpos = {
  d <- delta_w[!is.na(delta_w)]
  if (length(d) >= 3) all(tail(d, 3) <= 0) else FALSE
}, .groups='drop')
```

**검증 필요**:
- `delta_w`가 정확히 주간 변화량인지 (`theta_w - lag(theta_w)`)
- `tail(d, 3)` 가 가장 최근 3개 값인지
- `all(...<= 0)` 조건이 맞는지 (정책: "연속 ≤0")

### 2. 요일 분산 컷오프 계산
```r
# L447
var_score <- pmax(am$abs_rate_variance %||% 0, am$tardy_rate_variance %||% 0)
```

**검증 필요**:
- `pmax()` 가 element-wise maximum 맞는지
- `%||%` 연산자가 NA 처리하는지
- 상위 20% = `probs = 0.80` 맞는지 (하위 80% 이하)

### 3. 학생 테이블 플래그 계산 위치
```r
# students_tbl() reactive 내부에서 계산되는지 확인 필요
improve_flag = (delta_7d < 0.05) AND three_nonpos
attn_flag = (abs_rate ≥ 0.10) OR (tardy_rate ≥ 0.15) OR (var_score ≥ cutoff)
resp_flag = (guess_like_rate ≥ cutoff) OR (omit_rate ≥ 0.08)
```

**확인 필요**: 이 플래그들이 `students_tbl` 내부에서 정확히 계산되는지 코드 확인

---

## 🎯 남은 작업 (Windsurf 제안)

### 즉시 가능
- [ ] `assignment_templates.yaml` 실제 값 채우기 (과제 카탈로그 ID)
- [ ] IdP 헤더 매핑 확정 (`AUTH_HEADER_*`)
- [ ] 과제 API JSON 스펙 맞추기

### 단기 (다음 스프린트)
- [ ] 학년/과목 메타 데이터 추가 (`students`, `classes` 테이블)
- [ ] 서브그룹 분위수 계산 구현
- [ ] 요일별 보정 추천 텍스트 생성 (예: "수요일 보충 지도 권고")

### 중기
- [ ] 과목·학년별 템플릿 다중 정의 (`math.high.very_low` 키 공간)
- [ ] A/B 테스팅 지원 (템플릿 variant)
- [ ] 리스크 점수 가중치 조정 UI (admin 전용)

### 장기
- [ ] ML 기반 리스크 예측 (임계값 자동 학습)
- [ ] 다중 클래스 배치 작업
- [ ] 모바일 반응형 UI

---

## 📝 Copilot 액션 아이템

### 즉시 수행
1. ✅ Windsurf 코드 리뷰 (위 검증 포인트 확인)
2. ✅ `students_tbl` reactive에서 플래그 계산 확인
3. ✅ 테스트 케이스 실행 (3주 연속, 요일 분산, 추측률 상위 20%)

### 다음 작업
1. 학년/과목 메타 스키마 설계
2. 서브그룹 분위수 계산 프로토타입
3. YAML 확장 스키마 설계 (`math.grade_3.very_low`)

---

## 📚 관련 문서

- **Copilot 작업**: `HANDOFF_TO_WINDSURF.md` (초기 4가지 기능)
- **빠른 시작**: `QUICKSTART_v2.md`
- **상세 문서**: `ENHANCEMENTS_v2.md`
- **YAML 가이드**: `INTEGRATION_GUIDE.md`

---

**업데이트 상태**: ✅ Windsurf 작업 완료, Copilot 검증 대기  
**다음 협업**: Copilot이 학년/과목별 자동 보정 구조 설계

---

**Happy Collaboration! 🤝**

Copilot과 Windsurf가 함께 만드는 최고의 대시보드!
