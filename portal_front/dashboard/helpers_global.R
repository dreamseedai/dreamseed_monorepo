# ============================================================================
# DreamseedAI 글로벌 헬퍼 함수
# 파일명: helpers_global.R
# 버전: 2.0
# 작성일: 2025-11-06
# 목적: 다국가, 다과목, 다학년 지원을 위한 유틸리티 함수
# ============================================================================

# ============================================================================
# 1. 템플릿 검색 함수 (계층적 검색)
# ============================================================================

#' 국가/과목/학년/레벨에 맞는 과제 템플릿 검색
#' 
#' 계층적 검색 순서:
#' 1. country.subject.grade.level.bucket
#' 2. country.subject.grade.bucket (level 없이)
#' 3. country.subject.bucket (grade 무시)
#' 4. USA.math.G9.bucket (기본 fallback)
#' 
#' @param config YAML 설정 객체 (load_config() 결과)
#' @param country 국가 코드 (USA, CAN, KOR, GBR 등)
#' @param subject 과목명 (math, physics, chemistry, biology 등)
#' @param grade 학년 (G9, G10, G11, G12, Year10 등)
#' @param level 난이도/레벨 (algebra2, mechanics, honors, AP, NULL)
#' @param bucket 능력치 버킷 (very_low, low, mid, high, very_high)
#' @return 템플릿 리스트 (template_id, catalog_ids, difficulty 등)
get_template <- function(config, country, subject, grade, level = NULL, bucket) {
  templates <- config$templates
  
  # 입력 검증
  if (is.null(country) || is.na(country)) country <- "USA"
  if (is.null(subject) || is.na(subject)) subject <- "math"
  if (is.null(grade) || is.na(grade)) grade <- "G9"
  if (is.null(bucket) || is.na(bucket)) bucket <- "mid"
  
  # 1차 시도: country.subject.grade.level.bucket
  if (!is.null(level) && !is.na(level)) {
    template <- try({
      templates[[country]][[subject]][[grade]][[level]][[bucket]]
    }, silent = TRUE)
    
    if (!inherits(template, "try-error") && !is.null(template)) {
      message("[get_template] ✓ Found: ", country, ".", subject, ".", grade, ".", level, ".", bucket)
      return(template)
    }
  }
  
  # 2차 시도: country.subject.grade.bucket (level 없이)
  template <- try({
    templates[[country]][[subject]][[grade]][[bucket]]
  }, silent = TRUE)
  
  if (!inherits(template, "try-error") && !is.null(template)) {
    message("[get_template] ✓ Found: ", country, ".", subject, ".", grade, ".", bucket)
    return(template)
  }
  
  # 3차 시도: country.subject.bucket (grade 무시, 범용 템플릿)
  template <- try({
    # 해당 과목의 첫 번째 학년 찾기
    first_grade <- names(templates[[country]][[subject]])[1]
    if (!is.null(first_grade)) {
      templates[[country]][[subject]][[first_grade]][[bucket]]
    }
  }, silent = TRUE)
  
  if (!inherits(template, "try-error") && !is.null(template)) {
    warning("[get_template] ⚠ Using fallback (grade ignored): ", country, ".", subject, ".", bucket)
    return(template)
  }
  
  # 4차 시도: USA.math.G9.bucket (최종 기본값)
  template <- try({
    templates$USA$math$G9[[bucket]]
  }, silent = TRUE)
  
  if (!inherits(template, "try-error") && !is.null(template)) {
    warning("[get_template] ⚠ Using default fallback: USA.math.G9.", bucket)
    return(template)
  }
  
  # 모든 시도 실패 시 하드코딩된 기본값
  warning("[get_template] ✗ No template found. Using hardcoded default.")
  return(list(
    template_id = "DEFAULT_CORE",
    catalog_ids = list("DEFAULT_CORE_001"),
    difficulty = 3,
    estimated_minutes = 30,
    language = "en-US",
    tags = list("default")
  ))
}

# ============================================================================
# 2. 다국어 메시지 함수
# ============================================================================

#' 다국어 메시지 가져오기
#' 
#' @param config YAML 설정 객체
#' @param language 언어 코드 (en-US, ko-KR, zh-CN 등)
#' @param key 메시지 키 (risk_improve, assign_success 등)
#' @param replacements Named list of {placeholder: value} (예: list(count = 5))
#' @return 번역된 메시지 문자열
get_i18n_message <- function(config, language, key, replacements = list()) {
  messages <- config$messages
  
  # 기본값 설정
  if (is.null(language) || is.na(language)) language <- "en-US"
  
  # 메시지 조회
  msg <- try({
    messages[[language]][[key]]
  }, silent = TRUE)
  
  # 언어별 메시지 없으면 en-US로 fallback
  if (inherits(msg, "try-error") || is.null(msg)) {
    msg <- try({
      messages[["en-US"]][[key]]
    }, silent = TRUE)
  }
  
  # 여전히 없으면 키 자체 반환
  if (inherits(msg, "try-error") || is.null(msg)) {
    warning("[get_i18n_message] Message not found: ", language, ".", key)
    return(key)
  }
  
  # 플레이스홀더 치환 ({count} → 5)
  if (length(replacements) > 0) {
    for (placeholder in names(replacements)) {
      pattern <- paste0("\\{", placeholder, "\\}")
      msg <- gsub(pattern, replacements[[placeholder]], msg)
    }
  }
  
  return(msg)
}

#' 요일명 번역
#' 
#' @param config YAML 설정 객체
#' @param language 언어 코드
#' @param day_abbr 요일 약어 (Mon, Tue, Wed 등)
#' @return 번역된 요일명
get_day_name <- function(config, language, day_abbr) {
  messages <- config$messages
  
  if (is.null(language) || is.na(language)) language <- "en-US"
  
  day_name <- try({
    messages[[language]]$day_names[[day_abbr]]
  }, silent = TRUE)
  
  if (inherits(day_name, "try-error") || is.null(day_name)) {
    return(day_abbr)  # Fallback to abbreviation
  }
  
  return(day_name)
}

# ============================================================================
# 3. 서브그룹 필터링 함수
# ============================================================================

#' 동일 서브그룹 (국가/과목/학년) 데이터 필터링
#' 
#' @param dataset Arrow dataset
#' @param country 국가 코드
#' @param subject 과목명
#' @param grade 학년
#' @return 필터링된 Arrow dataset
filter_by_subgroup <- function(dataset, country, subject, grade) {
  # 초기 필터링
  filtered <- dataset
  
  # country 필터
  if (!is.null(country) && !is.na(country)) {
    filtered <- filtered %>% dplyr::filter(country == !!country)
  }
  
  # subject 필터
  if (!is.null(subject) && !is.na(subject)) {
    filtered <- filtered %>% dplyr::filter(subject == !!subject)
  }
  
  # grade 필터
  if (!is.null(grade) && !is.na(grade)) {
    filtered <- filtered %>% dplyr::filter(grade == !!grade)
  }
  
  return(filtered)
}

#' 서브그룹 데이터 수집 후 검증
#' 
#' @param dataset Arrow dataset
#' @param country 국가 코드
#' @param subject 과목명
#' @param grade 학년
#' @param min_rows 최소 행 수 (기본값 10)
#' @param fallback_levels 데이터 부족 시 확장 단계 (c("subject", "country", "all"))
#' @return collected data.frame
collect_subgroup_data <- function(dataset, country, subject, grade, 
                                   min_rows = 10, 
                                   fallback_levels = c("subject", "country", "all")) {
  # 1차 시도: country + subject + grade
  data <- filter_by_subgroup(dataset, country, subject, grade) %>% dplyr::collect()
  
  if (nrow(data) >= min_rows) {
    message("[collect_subgroup] ✓ Found ", nrow(data), " rows: ", country, ".", subject, ".", grade)
    return(data)
  }
  
  # 데이터 부족 시 순차적 확장
  for (level in fallback_levels) {
    if (level == "subject") {
      # country + subject (grade 무시)
      data <- filter_by_subgroup(dataset, country, subject, NULL) %>% dplyr::collect()
      if (nrow(data) >= min_rows) {
        warning("[collect_subgroup] ⚠ Expanded to ", country, ".", subject, " (", nrow(data), " rows)")
        return(data)
      }
    } else if (level == "country") {
      # country only
      data <- filter_by_subgroup(dataset, country, NULL, NULL) %>% dplyr::collect()
      if (nrow(data) >= min_rows) {
        warning("[collect_subgroup] ⚠ Expanded to ", country, " (", nrow(data), " rows)")
        return(data)
      }
    } else if (level == "all") {
      # 전체 데이터
      data <- dataset %>% dplyr::collect()
      warning("[collect_subgroup] ⚠ Using all data (", nrow(data), " rows)")
      return(data)
    }
  }
  
  # 그래도 부족하면 빈 데이터프레임 반환
  warning("[collect_subgroup] ✗ Insufficient data even after fallback")
  return(data.frame())
}

# ============================================================================
# 4. 프라이버시 필터 함수
# ============================================================================

#' 프라이버시 규정에 따른 데이터 필터링/마스킹
#' 
#' GDPR (유럽): 이름 익명화, ID 마스킹
#' COPPA (미국 13세 미만): 학부모 동의 확인
#' FERPA (미국 공교육): 외부 기록 제한
#' PIPA (한국): ID 마스킹
#' 
#' @param data 학생 데이터프레임
#' @param country 국가 코드
#' @param education_type 교육 형태
#' @param user_role 사용자 역할 (teacher, admin 등)
#' @param config YAML 설정 객체
#' @return 필터링/마스킹된 데이터프레임
privacy_filter <- function(data, country, education_type, user_role, config) {
  if (nrow(data) == 0) return(data)
  
  privacy_config <- config$privacy
  
  # GDPR 적용 (유럽)
  gdpr_countries <- privacy_config$GDPR$applicable_countries
  if (!is.null(gdpr_countries) && country %in% gdpr_countries) {
    if (user_role != "admin" && privacy_config$GDPR$anonymize_names) {
      # 이름 익명화: "Kim Sujin" → "K***"
      data$student_name <- sapply(data$student_name, function(name) {
        if (is.na(name) || nchar(name) == 0) return(name)
        paste0(substr(name, 1, 1), "***")
      })
    }
    
    if (privacy_config$GDPR$mask_identifiers) {
      # ID 마스킹: "STU-12345" → "STU-***45"
      data$student_id <- sapply(data$student_id, mask_identifier)
    }
    
    message("[privacy_filter] GDPR applied: ", country)
  }
  
  # COPPA 적용 (미국 13세 미만)
  if (country == "USA" && !is.null(privacy_config$COPPA)) {
    age_threshold <- privacy_config$COPPA$age_threshold
    
    if ("date_of_birth" %in% names(data) && user_role != "admin") {
      # 나이 계산
      data$age <- as.numeric(difftime(Sys.Date(), data$date_of_birth, units = "days")) / 365.25
      
      # 13세 미만 + 동의 없음 → 제외
      if (privacy_config$COPPA$require_parental_consent && "parental_consent" %in% names(data)) {
        data <- data %>%
          dplyr::filter(is.na(age) | age >= age_threshold | parental_consent == TRUE)
        
        message("[privacy_filter] COPPA applied: filtered ", sum(data$age < age_threshold & !data$parental_consent, na.rm=TRUE), " rows")
      }
    }
  }
  
  # FERPA 적용 (미국 공교육)
  if (country == "USA" && education_type == "public_school" && !is.null(privacy_config$FERPA)) {
    if (user_role == "public_school_teacher") {
      # 외부 기록 컬럼 제거
      external_cols <- c("external_test_scores", "private_tutor_history", "family_income")
      data <- data %>% dplyr::select(-any_of(external_cols))
      
      # 이름 익명화
      if (privacy_config$FERPA$anonymize_for_teachers) {
        data$student_name <- sapply(data$student_name, function(name) {
          if (is.na(name) || nchar(name) == 0) return(name)
          paste0(substr(name, 1, 1), "***")
        })
      }
      
      message("[privacy_filter] FERPA applied: public school teacher")
    }
  }
  
  # PIPA 적용 (한국)
  if (country == "KOR" && !is.null(privacy_config$PIPA)) {
    if (user_role != "admin" && privacy_config$PIPA$mask_identifiers) {
      data$student_id <- sapply(data$student_id, mask_identifier)
      message("[privacy_filter] PIPA applied: Korea")
    }
  }
  
  return(data)
}

#' ID 마스킹 헬퍼 함수
#' 
#' @param id ID 문자열 (예: "STU-12345")
#' @return 마스킹된 ID (예: "STU-***45")
mask_identifier <- function(id) {
  if (is.na(id) || nchar(id) < 5) return(id)
  
  # 앞 3자 + *** + 뒤 2자
  prefix <- substr(id, 1, min(3, nchar(id) - 2))
  suffix <- substr(id, nchar(id) - 1, nchar(id))
  
  return(paste0(prefix, "***", suffix))
}

#' 연령 계산 함수
#' 
#' @param date_of_birth Date 객체
#' @return 만 나이 (숫자)
calculate_age <- function(date_of_birth) {
  if (is.na(date_of_birth)) return(NA)
  as.numeric(difftime(Sys.Date(), date_of_birth, units = "days")) / 365.25
}

# ============================================================================
# 5. 요일별 보정 추천 함수
# ============================================================================

#' 요일별 출석 패턴에 기반한 보충 지도 추천 메시지 생성
#' 
#' @param student_id 학생 ID
#' @param worst_day 최악의 요일 (Mon, Tue, Wed 등)
#' @param worst_day_abs_rate 해당 요일 결석률 (0-1)
#' @param country 국가 코드
#' @param language 언어 코드
#' @param config YAML 설정 객체
#' @return 추천 메시지 문자열
generate_dow_recommendation <- function(student_id, worst_day, worst_day_abs_rate, 
                                       country, language, config) {
  # 입력 검증
  if (is.null(worst_day) || is.na(worst_day) || is.null(worst_day_abs_rate) || is.na(worst_day_abs_rate)) {
    return("")
  }
  
  # 리스크 임계값 (20% 이상일 때만 추천)
  if (worst_day_abs_rate < 0.20) {
    return("")
  }
  
  # 국가별 보충 가능 요일
  defaults <- config$defaults
  tutoring_days <- try({
    defaults[[country]]$tutoring_days
  }, silent = TRUE)
  
  if (inherits(tutoring_days, "try-error") || is.null(tutoring_days)) {
    # Fallback: 수요일, 금요일
    tutoring_days <- c("Wed", "Fri")
  }
  
  # 요일명 번역
  worst_day_name <- get_day_name(config, language, worst_day)
  tutoring_day_names <- sapply(tutoring_days, function(d) get_day_name(config, language, d))
  tutoring_days_str <- paste(tutoring_day_names, collapse = if (language == "ko-KR") " 또는 " else if (language == "zh-CN") "或" else " or ")
  
  # 템플릿 메시지 가져오기
  template <- get_i18n_message(config, language, "dow_rec_template")
  
  # 플레이스홀더 치환
  msg <- gsub("\\{day\\}", worst_day_name, template)
  msg <- gsub("\\{rate\\}", sprintf("%.0f", worst_day_abs_rate * 100), msg)
  msg <- gsub("\\{tutoring_days\\}", tutoring_days_str, msg)
  
  return(msg)
}

# ============================================================================
# 6. 리스크 임계값 조회 함수
# ============================================================================

#' 국가/과목에 맞는 리스크 임계값 조회
#' 
#' 우선순위: 과목별 > 국가별 > 기본값
#' 
#' @param config YAML 설정 객체
#' @param country 국가 코드
#' @param subject 과목명
#' @param threshold_key 임계값 키 (theta_delta, attendance_abs 등)
#' @return 임계값 (숫자)
get_risk_threshold <- function(config, country, subject, threshold_key) {
  thresholds <- config$risk_thresholds
  
  # 1차: 과목별 임계값
  subject_threshold <- try({
    thresholds[[subject]][[threshold_key]]
  }, silent = TRUE)
  
  if (!inherits(subject_threshold, "try-error") && !is.null(subject_threshold)) {
    return(subject_threshold)
  }
  
  # 2차: 국가별 임계값
  country_threshold <- try({
    thresholds[[country]][[threshold_key]]
  }, silent = TRUE)
  
  if (!inherits(country_threshold, "try-error") && !is.null(country_threshold)) {
    return(country_threshold)
  }
  
  # 3차: 기본값
  default_threshold <- try({
    thresholds$default[[threshold_key]]
  }, silent = TRUE)
  
  if (!inherits(default_threshold, "try-error") && !is.null(default_threshold)) {
    return(default_threshold)
  }
  
  # 하드코딩된 최종 기본값
  default_values <- list(
    theta_delta = 0.05,
    attendance_abs = 0.10,
    attendance_tardy = 0.15,
    attendance_var_top_pct = 0.80,
    guess_top_pct = 0.80,
    omit = 0.08
  )
  
  return(default_values[[threshold_key]] %||% 0.05)
}

# ============================================================================
# 7. 권한 체크 함수
# ============================================================================

#' 사용자 권한 체크
#' 
#' @param config YAML 설정 객체
#' @param user_role 사용자 역할 (individual_tutor, academy_teacher 등)
#' @param permission 권한 키 (can_assign, can_view_pii 등)
#' @return TRUE/FALSE
has_permission <- function(config, user_role, permission) {
  permissions <- config$permissions
  
  role_perms <- try({
    permissions[[user_role]]
  }, silent = TRUE)
  
  if (inherits(role_perms, "try-error") || is.null(role_perms)) {
    warning("[has_permission] Unknown role: ", user_role)
    return(FALSE)
  }
  
  perm_value <- role_perms[[permission]]
  
  if (is.null(perm_value)) {
    warning("[has_permission] Unknown permission: ", permission)
    return(FALSE)
  }
  
  return(as.logical(perm_value))
}

#' 최대 학생 수 조회
#' 
#' @param config YAML 설정 객체
#' @param user_role 사용자 역할
#' @return 최대 학생 수 (숫자)
get_max_students <- function(config, user_role) {
  permissions <- config$permissions
  
  max_students <- try({
    permissions[[user_role]]$max_students
  }, silent = TRUE)
  
  if (inherits(max_students, "try-error") || is.null(max_students)) {
    return(10)  # 기본값
  }
  
  return(as.numeric(max_students))
}

# ============================================================================
# 8. 데이터 서버 URL 조회 (성능 최적화)
# ============================================================================

#' 국가별 데이터 서버 URL 조회
#' 
#' @param config YAML 설정 객체
#' @param country 국가 코드
#' @return 데이터 서버 URL
get_data_server <- function(config, country) {
  servers <- config$performance$data_servers
  
  server_url <- try({
    servers[[country]]
  }, silent = TRUE)
  
  if (inherits(server_url, "try-error") || is.null(server_url)) {
    # Fallback to USA server
    return(servers$USA %||% "https://data.dreamseedai.com")
  }
  
  return(server_url)
}

# ============================================================================
# 9. 유틸리티 함수
# ============================================================================

#' NULL 체크 연산자 (%||%)
#' 
#' @param x 값
#' @param y 기본값
#' @return x가 NULL이면 y, 아니면 x
`%||%` <- function(x, y) {
  if (is.null(x)) y else x
}

#' 안전한 평균 계산 (NA 제거)
#' 
#' @param x 숫자 벡터
#' @return 평균값
safe_mean <- function(x) {
  if (length(x) == 0) return(NA)
  mean(x, na.rm = TRUE)
}

#' 안전한 분위수 계산
#' 
#' @param x 숫자 벡터
#' @param probs 분위수 (0-1)
#' @return 분위수 값
safe_quantile <- function(x, probs = 0.5) {
  if (length(x) == 0) return(Inf)
  as.numeric(stats::quantile(x, probs = probs, na.rm = TRUE))
}

#' 로그 메시지 출력 (타임스탬프 포함)
#' 
#' @param msg 메시지
#' @param level 로그 레벨 (INFO, WARNING, ERROR)
log_message <- function(msg, level = "INFO") {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  cat(sprintf("[%s] [%s] %s\n", timestamp, level, msg))
}

# ============================================================================
# 예제 사용법 (주석)
# ============================================================================

# # 1. 템플릿 검색
# config <- yaml::yaml.load_file("config/assignment_templates_global.yaml")
# template <- get_template(config, "USA", "math", "G9", "algebra2", "very_low")
# print(template$template_id)  # "US-MATH-ALG2-G9-REMEDIAL"
# 
# # 2. 다국어 메시지
# msg <- get_i18n_message(config, "ko-KR", "assign_success", list(count = 5))
# print(msg)  # "과제 배정 성공: 5명"
# 
# # 3. 서브그룹 데이터 수집
# data <- collect_subgroup_data(attendance_ds, "USA", "math", "G9", min_rows = 10)
# 
# # 4. 프라이버시 필터
# filtered_data <- privacy_filter(data, "USA", "public_school", "teacher", config)
# 
# # 5. 요일별 추천
# rec <- generate_dow_recommendation("STU-001", "Mon", 0.25, "USA", "en-US", config)
# print(rec)  # "Weekly Monday absence rate 25% → Recommend Wednesday or Friday tutoring"
# 
# # 6. 리스크 임계값
# threshold <- get_risk_threshold(config, "KOR", "math", "attendance_abs")
# print(threshold)  # 0.05 (한국은 더 엄격)
# 
# # 7. 권한 체크
# can_assign <- has_permission(config, "individual_tutor", "can_assign")
# print(can_assign)  # TRUE

message("[helpers_global.R] ✓ Loaded successfully")
