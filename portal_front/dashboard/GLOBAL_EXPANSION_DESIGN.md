# 글로벌 확장 가능한 Teacher Dashboard 설계안

**작성일**: 2025-11-06  
**대상**: DreamseedAI 글로벌 확장 로드맵  
**목적**: 다국가, 다과목, 다학년, 다교육 형태 지원

---

## 🎯 요구사항 요약

### 초기 범위 (현재 ~ 6개월)
- **지역**: 미국, 캐나다
- **학년**: G9-G12 (고등학교)
- **과목**: Math, Physics, Chemistry, Biology
- **교육 형태**: 1:1 개인지도, 소수 그룹 과외, 학원 (Private), 공교육

### 확장 계획 (6개월 ~ 2년)
- **과목 확장**: English, Social Science, Computer Science/Coding
- **지역 확장**: 영국, 호주, 한국
- **언어 확장**: 한국어, 중국어, 일본어

### 궁극 비전 (2년+)
- **글로벌**: 전 세계 영어권 + 아시아권
- **전 과목**: K-12 모든 과목
- **다양한 교육 형태**: 개인지도, 소그룹, 학원, 공교육, 온라인

---

## 📊 데이터 스키마 설계

### 1. 학생 메타데이터 (`students` 테이블)

```sql
-- 확장 가능한 학생 테이블
CREATE TABLE students (
  student_id VARCHAR(50) PRIMARY KEY,
  student_name VARCHAR(100),
  org_id VARCHAR(50),  -- 조직 (학교/학원/개인교습)
  class_id VARCHAR(50),
  
  -- 학년/학제 (국제 표준)
  grade VARCHAR(10),   -- "G9", "G10", "G11", "G12"
  grade_system VARCHAR(20),  -- "US", "UK", "KR", "AU", "CN"
  
  -- 지역/언어
  region VARCHAR(10),  -- "US-CA", "US-NY", "CA-ON", "UK-LON", "KR-SEL"
  country VARCHAR(3),  -- ISO 3166-1 alpha-3: "USA", "CAN", "GBR", "AUS", "KOR", "CHN"
  language VARCHAR(10), -- "en-US", "en-GB", "ko-KR", "zh-CN"
  timezone VARCHAR(50), -- "America/Los_Angeles", "Asia/Seoul"
  
  -- 교육 형태
  education_type VARCHAR(20),  -- "tutoring", "small_group", "academy", "public_school"
  group_size INT,              -- 1 (개인), 2-5 (소그룹), 6-20 (학원), 21+ (학교)
  
  -- 활성 상태
  is_active BOOLEAN,
  enrollment_date DATE,
  updated_at TIMESTAMP
);

CREATE INDEX idx_students_grade_country ON students(grade, country);
CREATE INDEX idx_students_org_type ON students(org_id, education_type);
```

### 2. 클래스/과목 메타데이터 (`classes` 테이블)

```sql
CREATE TABLE classes (
  class_id VARCHAR(50) PRIMARY KEY,
  class_name VARCHAR(100),
  org_id VARCHAR(50),
  
  -- 과목 (국제 표준화)
  subject VARCHAR(50),         -- "math", "physics", "chemistry", "biology"
  subject_code VARCHAR(20),    -- "MATH-ALG2", "PHYS-MECH", "CHEM-ORG"
  subject_level VARCHAR(20),   -- "honors", "AP", "IB", "regular", "remedial"
  
  -- 학년/국가
  grade VARCHAR(10),           -- "G9", "G10", "G11", "G12"
  country VARCHAR(3),          -- "USA", "CAN", "GBR", "AUS", "KOR", "CHN"
  curriculum VARCHAR(20),      -- "US-Common-Core", "AP", "IB", "UK-GCSE", "KR-National"
  
  -- 교육 형태
  education_type VARCHAR(20),
  teacher_id VARCHAR(50),
  
  -- 기간
  start_date DATE,
  end_date DATE,
  is_active BOOLEAN
);

CREATE INDEX idx_classes_subject_grade ON classes(subject, grade, country);
```

### 3. 과목 마스터 테이블 (`subjects_master`)

```sql
CREATE TABLE subjects_master (
  subject_code VARCHAR(20) PRIMARY KEY,
  subject_name_en VARCHAR(100),  -- "Algebra 2", "Organic Chemistry"
  subject_name_ko VARCHAR(100),  -- "대수학 2", "유기화학"
  subject_name_zh VARCHAR(100),  -- "代数2", "有机化学"
  
  category VARCHAR(50),          -- "math", "science", "language", "social", "cs"
  subcategory VARCHAR(50),       -- "algebra", "mechanics", "organic", "molecular"
  
  -- 난이도/레벨
  min_grade VARCHAR(10),         -- "G9"
  max_grade VARCHAR(10),         -- "G12"
  difficulty_level INT,          -- 1-5
  
  -- 지원 국가/커리큘럼
  supported_countries TEXT[],    -- ["USA", "CAN", "GBR", "AUS"]
  supported_curricula TEXT[],    -- ["US-Common-Core", "AP", "IB"]
  
  is_active BOOLEAN,
  launch_date DATE
);

-- 초기 데이터 예시
INSERT INTO subjects_master VALUES
('MATH-ALG2', 'Algebra 2', '대수학 2', '代数2', 'math', 'algebra', 'G9', 'G11', 3, 
 ARRAY['USA','CAN','GBR','AUS'], ARRAY['US-Common-Core','AP'], true, '2025-01-01'),
('PHYS-MECH', 'Mechanics', '역학', '力学', 'science', 'mechanics', 'G10', 'G12', 4,
 ARRAY['USA','CAN','GBR','AUS'], ARRAY['AP','IB'], true, '2025-01-01'),
('CHEM-ORG', 'Organic Chemistry', '유기화학', '有机化学', 'science', 'organic', 'G11', 'G12', 5,
 ARRAY['USA','CAN','GBR','AUS'], ARRAY['AP','IB'], true, '2025-03-01');
```

### 4. 조직 메타데이터 (`organizations` 테이블)

```sql
CREATE TABLE organizations (
  org_id VARCHAR(50) PRIMARY KEY,
  org_name VARCHAR(200),
  
  -- 조직 유형
  org_type VARCHAR(20),          -- "tutoring_center", "private_academy", "public_school", "individual_tutor"
  education_type VARCHAR(20),    -- "tutoring", "small_group", "academy", "public_school"
  
  -- 지역
  country VARCHAR(3),
  region VARCHAR(10),
  city VARCHAR(100),
  timezone VARCHAR(50),
  
  -- 규모
  student_capacity INT,
  teacher_count INT,
  
  -- 언어/커리큘럼
  primary_language VARCHAR(10),
  supported_languages TEXT[],
  curricula TEXT[],
  
  is_active BOOLEAN
);
```

---

## 🔧 YAML 설정 확장 설계

### `config/assignment_templates.yaml` (다국가/다과목 지원)

```yaml
# 글로벌 템플릿 구조: {country}.{subject}.{grade}.{level}.{bucket}
templates:
  # 미국 수학
  USA:
    math:
      G9:
        algebra2:
          very_low:
            template_id: "US-MATH-ALG2-G9-REMEDIAL"
            catalog_ids: ["MATH-ALG2-BASICS-001", "MATH-ALG2-BASICS-002"]
            difficulty: 1
            estimated_minutes: 30
            language: "en-US"
            tags: ["remedial", "foundational", "algebra"]
          low:
            template_id: "US-MATH-ALG2-G9-SUPPLEMENT"
            catalog_ids: ["MATH-ALG2-REVIEW-001", "MATH-ALG2-REVIEW-002"]
            difficulty: 2
            estimated_minutes: 25
          mid:
            template_id: "US-MATH-ALG2-G9-CORE"
            catalog_ids: ["MATH-ALG2-PRACTICE-001", "MATH-ALG2-PRACTICE-002"]
            difficulty: 3
            estimated_minutes: 35
          high:
            template_id: "US-MATH-ALG2-G9-CHALLENGE"
            catalog_ids: ["MATH-ALG2-ADVANCED-001", "MATH-ALG2-ADVANCED-002"]
            difficulty: 4
            estimated_minutes: 40
          very_high:
            template_id: "US-MATH-ALG2-G9-ENRICHMENT"
            catalog_ids: ["MATH-ALG2-HONORS-001", "MATH-ALG2-HONORS-002"]
            difficulty: 5
            estimated_minutes: 45
      G10:
        # ... G10 templates
      G11:
        # ... G11 templates
      G12:
        # ... G12 templates
    
    physics:
      G10:
        mechanics:
          very_low:
            template_id: "US-PHYS-MECH-G10-REMEDIAL"
            catalog_ids: ["PHYS-MECH-BASICS-001"]
            difficulty: 1
            estimated_minutes: 35
          # ... other buckets
      G11:
        # ... G11 physics
      G12:
        electromagnetism:
          # ... EM templates
    
    chemistry:
      G11:
        organic:
          very_low:
            template_id: "US-CHEM-ORG-G11-REMEDIAL"
            catalog_ids: ["CHEM-ORG-BASICS-001"]
            difficulty: 1
            estimated_minutes: 30
          # ... other buckets
    
    biology:
      G9:
        cell_bio:
          # ... cell biology templates
      G10:
        genetics:
          # ... genetics templates

  # 캐나다 (대부분 미국과 동일하지만 지역 차이 반영)
  CAN:
    math:
      G9:
        algebra2:
          # USA와 유사하지만 Ontario 커리큘럼 반영
          very_low:
            template_id: "CAN-MATH-ALG2-G9-REMEDIAL"
            catalog_ids: ["CAN-MATH-ALG2-BASICS-001"]
            language: "en-CA"
    # ... 기타 과목

  # 한국 (향후 확장)
  KOR:
    math:
      G9:
        algebra:
          very_low:
            template_id: "KR-MATH-ALG-G9-REMEDIAL"
            catalog_ids: ["KR-MATH-ALG-BASICS-001"]
            language: "ko-KR"
            tags: ["보충", "기초", "대수"]
          # ... other buckets
    # ... 기타 과목

  # 영국 (향후 확장)
  GBR:
    math:
      Year10:  # UK uses Year system
        gcse_math:
          # ... GCSE templates
    # ... 기타 과목

  # 중국 (향후 확장)
  CHN:
    math:
      G9:
        algebra:
          very_low:
            template_id: "CN-MATH-ALG-G9-REMEDIAL"
            catalog_ids: ["CN-MATH-ALG-BASICS-001"]
            language: "zh-CN"
            tags: ["补习", "基础", "代数"]
          # ... other buckets

# 국가별 기본 설정
defaults:
  USA:
    grade_system: "US"
    language: "en-US"
    timezone: "America/Los_Angeles"
    curriculum: "US-Common-Core"
    working_days: ["Mon", "Tue", "Wed", "Thu", "Fri"]
    
  CAN:
    grade_system: "US"  # Similar to US
    language: "en-CA"
    timezone: "America/Toronto"
    curriculum: "CAN-Provincial"
    working_days: ["Mon", "Tue", "Wed", "Thu", "Fri"]
  
  KOR:
    grade_system: "KR"
    language: "ko-KR"
    timezone: "Asia/Seoul"
    curriculum: "KR-National"
    working_days: ["Mon", "Tue", "Wed", "Thu", "Fri"]
  
  GBR:
    grade_system: "UK"
    language: "en-GB"
    timezone: "Europe/London"
    curriculum: "UK-National"
    working_days: ["Mon", "Tue", "Wed", "Thu", "Fri"]
  
  CHN:
    grade_system: "CN"
    language: "zh-CN"
    timezone: "Asia/Shanghai"
    curriculum: "CN-National"
    working_days: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

# 교육 형태별 권한
permissions:
  # 개인 과외 (1:1)
  individual_tutor:
    can_assign: true
    can_view_all_classes: false
    can_view_student_history: true
    can_modify_thresholds: false
    max_students: 10
  
  # 소그룹 과외
  small_group_tutor:
    can_assign: true
    can_view_all_classes: false
    can_view_student_history: true
    can_modify_thresholds: false
    max_students: 30
  
  # 학원 강사
  academy_teacher:
    can_assign: true
    can_view_all_classes: true
    can_view_student_history: true
    can_modify_thresholds: false
    max_students: 100
  
  # 공교육 교사
  public_school_teacher:
    can_assign: true
    can_view_all_classes: true
    can_view_student_history: false  # Privacy
    can_modify_thresholds: false
    max_students: 200
  
  # 학원장/교감
  admin:
    can_assign: true
    can_view_all_classes: true
    can_view_student_history: true
    can_modify_thresholds: true
    max_students: 999999

# 리스크 임계값 (국가/과목별 조정 가능)
risk_thresholds:
  default:
    theta_delta: 0.05
    attendance_abs: 0.10
    attendance_tardy: 0.15
    attendance_var_top_pct: 0.80
    guess_top_pct: 0.80
    omit: 0.08
  
  # 국가별 오버라이드 (예: 한국은 출석 기준 더 엄격)
  KOR:
    attendance_abs: 0.05  # 5% 이상이면 리스크
    attendance_tardy: 0.10
  
  # 과목별 오버라이드 (예: Physics는 추측률 기준 다름)
  physics:
    guess_top_pct: 0.85  # 상위 15%만 리스크
    omit: 0.10

# i18n 메시지
messages:
  en-US:
    risk_improve: "Risk: Low Improvement (Δ7d<+0.05 & 3 weeks ≤0)"
    risk_attendance: "Risk: Irregular Attendance (Absent≥10% or Tardy≥15% or Variance Top 20%)"
    risk_response: "Risk: Response Anomaly (Guessing Top 20% or Omit≥8%)"
    assign_success: "Assignment successful: {count} students"
    assign_fail: "Assignment failed"
  
  ko-KR:
    risk_improve: "리스크: 개선 저조 (Δ7d<+0.05 & 최근 3주 연속 ≤0)"
    risk_attendance: "리스크: 출석 불규칙 (결석≥10% 또는 지각≥15% 또는 요일분산 상위20%)"
    risk_response: "리스크: 반응 이상치 (추측 상위20% 또는 무응답≥8%)"
    assign_success: "과제 배정 성공: {count}명"
    assign_fail: "과제 배정 실패"
  
  zh-CN:
    risk_improve: "风险: 改进缓慢 (Δ7d<+0.05 & 最近3周 ≤0)"
    risk_attendance: "风险: 出勤不规律 (缺勤≥10% 或迟到≥15% 或方差前20%)"
    risk_response: "风险: 响应异常 (猜测前20% 或空白≥8%)"
    assign_success: "分配成功: {count}名学生"
    assign_fail: "分配失败"
```

---

## 💻 R 코드 확장 구조

### 1. 템플릿 로딩 함수 (계층적 검색)

```r
# config/assignment_templates.yaml 로드 (글로벌 지원)
load_config <- function(config_path = "config/assignment_templates.yaml") {
  # ... 기존 로직 ...
  
  config <- yaml::yaml.load_file(config_path)
  
  # 템플릿 계층 구조 파싱
  config$template_hierarchy <- parse_template_hierarchy(config$templates)
  config$`_last_modified` <- file.info(config_path)$mtime
  
  message("[load_config] Loaded templates for countries: ", 
          paste(names(config$templates), collapse = ", "))
  
  config
}

# 템플릿 검색 함수 (국가 > 과목 > 학년 > 레벨 > 버킷)
get_template <- function(country, subject, grade, level = NULL, bucket) {
  # 1차: country.subject.grade.level.bucket
  if (!is.null(level)) {
    template <- ASSIGNMENT_TEMPLATES[[country]][[subject]][[grade]][[level]][[bucket]]
    if (!is.null(template)) return(template)
  }
  
  # 2차: country.subject.grade.bucket (level 없이)
  template <- ASSIGNMENT_TEMPLATES[[country]][[subject]][[grade]][[bucket]]
  if (!is.null(template)) return(template)
  
  # 3차: country.subject.bucket (grade 무시, 범용)
  template <- ASSIGNMENT_TEMPLATES[[country]][[subject]][[bucket]]
  if (!is.null(template)) return(template)
  
  # 4차: default fallback (USA.math.G9.bucket)
  template <- ASSIGNMENT_TEMPLATES$USA$math$G9[[bucket]]
  
  warning("[get_template] No template found for ", country, ".", subject, ".", grade, 
          ". Using fallback.")
  
  return(template %||% list(template_id = "default_core", catalog_ids = list()))
}
```

### 2. 서브그룹 분위수 계산 (국가/과목/학년별)

```r
# 출석 분산 컷오프 (서브그룹 기준)
attn_var_cutoff <- reactive({
  am <- attn_metrics_tbl()
  if (nrow(am) == 0) return(Inf)
  
  # 현재 클래스 메타
  cls <- classes_ds() %>% collect()
  current_country <- cls$country[1] %||% "USA"
  current_subject <- cls$subject[1] %||% "math"
  current_grade <- cls$grade[1] %||% "G9"
  
  # 동일 서브그룹 전체 데이터 로드
  all_same_subgroup <- open_ds(base, "attendance") %>%
    filter(
      country == !!current_country,
      subject == !!current_subject,
      grade == !!current_grade
    ) %>%
    collect()
  
  if (nrow(all_same_subgroup) < 10) {
    # 데이터 부족 시 국가 레벨로 확장
    all_same_subgroup <- open_ds(base, "attendance") %>%
      filter(country == !!current_country) %>%
      collect()
  }
  
  if (nrow(all_same_subgroup) < 10) {
    # 여전히 부족하면 글로벌 기본값
    return(Inf)
  }
  
  var_score <- pmax(all_same_subgroup$abs_rate_variance %||% 0, 
                    all_same_subgroup$tardy_rate_variance %||% 0)
  
  # 국가별 임계값 오버라이드
  pct <- CONFIG$risk_thresholds[[current_country]]$attendance_var_top_pct %||%
         CONFIG$risk_thresholds$default$attendance_var_top_pct %||%
         0.80
  
  as.numeric(stats::quantile(var_score, probs = pct, na.rm = TRUE))
})

# 추측률 컷오프 (서브그룹 기준)
guess_q_cutoff <- reactive({
  rsp <- resp_ds() %>% collect()
  if (nrow(rsp) == 0) return(Inf)
  
  cls <- classes_ds() %>% collect()
  current_country <- cls$country[1] %||% "USA"
  current_subject <- cls$subject[1] %||% "math"
  
  # 과목별 임계값 오버라이드
  pct <- CONFIG$risk_thresholds[[current_subject]]$guess_top_pct %||%
         CONFIG$risk_thresholds[[current_country]]$guess_top_pct %||%
         CONFIG$risk_thresholds$default$guess_top_pct %||%
         0.80
  
  as.numeric(stats::quantile(rsp$guess_like_rate, probs = pct, na.rm = TRUE))
})
```

### 3. 개별 학생 배정 (국가/과목/학년 자동 감지)

```r
observeEvent(input$assign_single_student, {
  req(input$assign_single_student)
  data <- input$assign_single_student
  student_id <- data$student_id
  theta_bucket <- data$theta_bucket
  
  if (!(has_role(claims, "teacher") || has_role(claims, "admin"))) {
    showNotification("과제 배정 권한이 없습니다.", type = "error", duration = 4)
    return()
  }
  
  # 학생 메타 조회
  student_meta <- students_ds() %>% 
    filter(student_id == !!student_id) %>% 
    collect()
  
  if (nrow(student_meta) == 0) {
    showNotification("학생 정보를 찾을 수 없습니다.", type = "error", duration = 4)
    return()
  }
  
  # 클래스 메타 조회
  class_meta <- classes_ds() %>% 
    filter(class_id == !!student_meta$class_id[1]) %>% 
    collect()
  
  country <- student_meta$country[1] %||% "USA"
  subject <- class_meta$subject[1] %||% "math"
  grade <- student_meta$grade[1] %||% "G9"
  level <- class_meta$subject_level[1]  # "honors", "AP", NULL
  
  # 템플릿 검색 (계층적)
  template <- get_template(country, subject, grade, level, theta_bucket)
  template_id <- template$template_id %||% "default_core"
  
  # 학생 이름 (다국어 지원)
  student_name <- if (nrow(student_row) > 0) student_row$student_name[1] else student_id
  
  # API 호출
  ok <- call_assignment_api(c(student_id), template_id, claims, assignment_auth)
  
  # 메시지 i18n
  language <- student_meta$language[1] %||% "en-US"
  msg_success <- CONFIG$messages[[language]]$assign_success %||% 
                 "Assignment successful: {count} students"
  msg_fail <- CONFIG$messages[[language]]$assign_fail %||% "Assignment failed"
  
  if (ok) {
    msg <- gsub("\\{count\\}", "1", msg_success)
    msg <- sprintf("%s - %s (%s)", msg, student_name, template_id)
    showNotification(msg, type = "message", duration = 5)
  } else {
    showNotification(msg_fail, type = "error", duration = 5)
  }
})
```

### 4. 요일별 보정 추천 (국가별 working days 고려)

```r
# 요일별 보정 추천 텍스트 생성
generate_dow_recommendation <- function(student_id, worst_day, worst_day_abs_rate, country = "USA") {
  if (is.na(worst_day) || worst_day_abs_rate < 0.20) {
    return("")  # 리스크 없음
  }
  
  # 국가별 근무일 확인
  working_days <- CONFIG$defaults[[country]]$working_days %||% 
                  c("Mon", "Tue", "Wed", "Thu", "Fri")
  
  # 미국/캐나다: 수요일, 금요일 보충 가능
  # 한국: 수요일, 토요일 보충 가능
  if (country %in% c("USA", "CAN", "GBR", "AUS")) {
    补充_days <- c("Wed", "Fri")
  } else if (country == "KOR") {
    补충_days <- c("Wed", "Sat")
  } else {
    补충_days <- c("Wed")
  }
  
  # 요일명 다국어
  day_names <- list(
    "en-US" = c(Mon="Monday", Tue="Tuesday", Wed="Wednesday", Thu="Thursday", 
                Fri="Friday", Sat="Saturday", Sun="Sunday"),
    "ko-KR" = c(Mon="월요일", Tue="화요일", Wed="수요일", Thu="목요일", 
                Fri="금요일", Sat="토요일", Sun="일요일"),
    "zh-CN" = c(Mon="星期一", Tue="星期二", Wed="星期三", Thu="星期四", 
                Fri="星期五", Sat="星期六", Sun="星期日")
  )
  
  language <- if (country == "KOR") "ko-KR" else if (country == "CHN") "zh-CN" else "en-US"
  worst_day_name <- day_names[[language]][[worst_day]] %||% worst_day
  
  # 추천 메시지
  if (language == "ko-KR") {
    sprintf("매주 %s 결석률 %.0f%% → %s 보충 지도 권장", 
            worst_day_name, worst_day_abs_rate * 100,
            paste(day_names[[language]][补충_days], collapse=" 또는 "))
  } else if (language == "zh-CN") {
    sprintf("每周%s缺勤率%.0f%% → 建议%s补习", 
            worst_day_name, worst_day_abs_rate * 100,
            paste(day_names[[language]][补충_days], collapse="或"))
  } else {
    sprintf("Weekly %s absence rate %.0f%% → Recommend %s tutoring", 
            worst_day_name, worst_day_abs_rate * 100,
            paste(补충_days, collapse=" or "))
  }
}

# 학생 테이블에 추천 컬럼 추가
students_tbl <- reactive({
  # ... 기존 로직 ...
  
  combined <- combined %>% mutate(
    dow_recommendation = mapply(
      generate_dow_recommendation,
      student_id, worst_day, worst_day_abs_rate, country,
      SIMPLIFY = TRUE
    )
  )
  
  # ...
})
```

---

## 🌐 UI 다국어 지원

### `ui.R` 확장 (다국어 value box)

```r
ui <- dashboardPage(
  skin = "purple",
  dashboardHeader(
    title = reactive({
      lang <- session$userData$language %||% "en-US"
      if (lang == "ko-KR") "클래스 모니터"
      else if (lang == "zh-CN") "班级监控"
      else "Class Monitor"
    }),
    tags$li(class = "dropdown", uiOutput("user_badge"))
  ),
  # ...
)

# Value box 다국어
output$vb_risk_improve <- renderValueBox({
  lt <- latest_theta_tbl()
  low <- sum(lt$delta_7d < RISK_THETA_DELTA_THRESHOLD & lt$three_nonpos, na.rm = TRUE)
  total <- nrow(lt)
  
  cls <- classes_ds() %>% collect()
  country <- cls$country[1] %||% "USA"
  language <- if (country == "KOR") "ko-KR" else if (country == "CHN") "zh-CN" else "en-US"
  
  msg <- CONFIG$messages[[language]]$risk_improve %||% 
         "Risk: Low Improvement (Δ7d<+0.05 & 3 weeks ≤0)"
  
  valueBox(sprintf("%d명", low), msg, 
           icon = icon("triangle-exclamation"), 
           color = if (total>0 && low/total > 0.3) "red" else if (low>0) "yellow" else "green")
})
```

---

## 📈 확장 로드맵

### Phase 1: 현재 (2025 Q1-Q2)
- ✅ 미국/캐나다 G9-G12 Math, Physics, Chemistry, Biology
- ✅ 개인지도, 소그룹, 학원, 공교육 지원
- ✅ 영어(en-US, en-CA) UI

### Phase 2: 6개월 후 (2025 Q3-Q4)
- 📝 English, Social Science, Computer Science 추가
- 📝 영국, 호주 지원 (en-GB, en-AU)
- 📝 한국 지원 (ko-KR) + 국내 커리큘럼
- 📝 서브그룹 분위수 실시간 계산

### Phase 3: 1년 후 (2026 Q1-Q2)
- 📝 중국어 지원 (zh-CN) + 중국 커리큘럼
- 📝 일본어 지원 (ja-JP)
- 📝 K-8 학년 확장
- 📝 ML 기반 리스크 예측

### Phase 4: 2년 후 (2026 Q3+)
- 📝 전 세계 주요 국가 지원
- 📝 전 과목 K-12 커버
- 📝 다중 언어 자동 번역
- 📝 글로벌 벤치마크 대시보드

---

## 🔒 보안 및 프라이버시

### 국가별 프라이버시 규정 준수

```r
# GDPR (유럽), COPPA (미국), PIPA (한국) 준수
privacy_filter <- function(data, country, user_role) {
  if (country %in% c("GBR", "DEU", "FRA")) {  # GDPR
    # 개인정보 최소화
    if (user_role != "admin") {
      data$student_name <- anonymize(data$student_name)
    }
  }
  
  if (country == "USA" && any(data$age < 13)) {  # COPPA
    # 13세 미만 학생 데이터 제한
    if (user_role == "public_school_teacher") {
      data <- data %>% filter(age >= 13 | parental_consent == TRUE)
    }
  }
  
  if (country == "KOR") {  # PIPA
    # 한국 개인정보보호법 준수
    data$student_id <- mask_identifier(data$student_id)
  }
  
  return(data)
}
```

---

## 📊 성능 최적화 (글로벌 스케일)

### 데이터 파티셔닝 전략

```python
# Parquet 파티셔닝: country/subject/grade/year/month
data/
  attendance/
    country=USA/
      subject=math/
        grade=G9/
          year=2025/
            month=01/
              part-0000.parquet
    country=CAN/
      subject=physics/
        # ...
    country=KOR/
      subject=math/
        # ...
```

### CDN 및 캐싱

```r
# 국가별 서버 분산
get_data_server <- function(country) {
  servers <- list(
    USA = "https://us-data.dreamseedai.com",
    CAN = "https://ca-data.dreamseedai.com",
    KOR = "https://kr-data.dreamseedai.com",
    GBR = "https://uk-data.dreamseedai.com",
    CHN = "https://cn-data.dreamseedai.com"
  )
  
  servers[[country]] %||% servers$USA
}
```

---

## ✅ 즉시 구현 가능한 최소 변경

### 현재 코드에 추가할 최소 변경사항

1. **`students` 테이블에 컬럼 추가** (DB 마이그레이션)
   ```sql
   ALTER TABLE students ADD COLUMN country VARCHAR(3) DEFAULT 'USA';
   ALTER TABLE students ADD COLUMN grade VARCHAR(10) DEFAULT 'G9';
   ALTER TABLE students ADD COLUMN education_type VARCHAR(20) DEFAULT 'tutoring';
   ```

2. **`classes` 테이블에 컬럼 추가**
   ```sql
   ALTER TABLE classes ADD COLUMN subject VARCHAR(50) DEFAULT 'math';
   ALTER TABLE classes ADD COLUMN country VARCHAR(3) DEFAULT 'USA';
   ALTER TABLE classes ADD COLUMN grade VARCHAR(10) DEFAULT 'G9';
   ```

3. **`assignment_templates.yaml` 구조 변경**
   - 기존: `very_low.template_id`
   - 신규: `USA.math.G9.very_low.template_id`

4. **`get_template()` 함수 추가**
   - 계층적 템플릿 검색 로직

---

**다음 단계**: 위 설계안을 검토하신 후, 우선순위를 정해주시면 즉시 구현을 시작하겠습니다! 🚀
