#!/usr/bin/env Rscript
# ============================================================================
# 교사용 대시보드 샘플 데이터 생성 스크립트
# ============================================================================
# 최근 90일 학생 θ, 출석, 스킬 취약점, 문항 반응 통계를 Parquet로 생성
# org_id/class_id 파티션으로 저장하여 푸시다운 필터링 지원

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(lubridate)
  library(tibble)
  library(tidyr)
})

# 설정
DATASET_ROOT <- Sys.getenv("DATASET_ROOT", "data/datasets")
N_ORGS <- 3
N_CLASSES_PER_ORG <- 5
N_STUDENTS_PER_CLASS <- 30
N_DAYS <- 90
SKILLS <- c("인수분해", "지수법칙", "이차방정식", "함수그래프", "확률통계", 
            "삼각함수", "미분기초", "적분기초", "벡터연산", "행렬계산")

set.seed(42)

cat("📊 교사용 대시보드 샘플 데이터 생성 시작\n")
cat("   - 조직 수:", N_ORGS, "\n")
cat("   - 클래스/조직:", N_CLASSES_PER_ORG, "\n")
cat("   - 학생/클래스:", N_STUDENTS_PER_CLASS, "\n")
cat("   - 기간:", N_DAYS, "일\n\n")

# ============================================================================
# 1. 조직 및 클래스 메타데이터
# ============================================================================
cat("1️⃣  조직 및 클래스 생성...\n")

orgs <- tibble(
  org_id = sprintf("org_%03d", 1:N_ORGS),
  org_name = sprintf("학교_%d", 1:N_ORGS)
)

classes <- expand_grid(
  org_id = orgs$org_id,
  class_num = 1:N_CLASSES_PER_ORG
) %>%
  mutate(
    class_id = sprintf("%s_class_%02d", org_id, class_num),
    class_name = sprintf("%d학년 %d반", (class_num - 1) %/% 5 + 1, (class_num - 1) %% 5 + 1),
    teacher_id = sprintf("teacher_%s_%02d", org_id, class_num),
    teacher_name = sprintf("교사%02d", class_num)
  ) %>%
  select(-class_num)

write_parquet(classes, file.path(DATASET_ROOT, "classes.parquet"))
cat("   ✓ classes.parquet 저장 (", nrow(classes), "건)\n")

# ============================================================================
# 2. 학생 메타데이터
# ============================================================================
cat("2️⃣  학생 메타데이터 생성...\n")

students <- classes %>%
  select(org_id, class_id) %>%
  crossing(student_num = 1:N_STUDENTS_PER_CLASS) %>%
  mutate(
    student_id = sprintf("%s_s%03d", class_id, student_num),
    student_name = sprintf("학생%03d", student_num),
    grade = as.integer(substr(class_id, nchar(class_id) - 4, nchar(class_id) - 4)),
    enrollment_date = today() - days(sample(180:720, n(), replace = TRUE))
  ) %>%
  select(-student_num)

write_parquet(students, file.path(DATASET_ROOT, "students.parquet"))
cat("   ✓ students.parquet 저장 (", nrow(students), "건)\n")

# ============================================================================
# 3. 학생별 일별 θ (최근 90일)
# ============================================================================
cat("3️⃣  학생별 θ 시계열 생성 (90일)...\n")

dates <- seq(today() - days(N_DAYS - 1), today(), by = "day")

# 학생별 초기 θ와 성장률 설정
student_params <- students %>%
  mutate(
    theta_init = rnorm(n(), mean = 0, sd = 1),
    growth_rate = rnorm(n(), mean = 0.01, sd = 0.005)  # 일평균 성장률
  )

student_theta <- expand_grid(
  student_id = students$student_id,
  date = dates
) %>%
  left_join(student_params %>% select(student_id, org_id, class_id, theta_init, growth_rate), 
            by = "student_id") %>%
  arrange(student_id, date) %>%
  group_by(student_id) %>%
  mutate(
    day_index = row_number() - 1,
    theta = theta_init + growth_rate * day_index + rnorm(n(), 0, 0.05),  # 노이즈 추가
    theta = pmax(-3, pmin(3, theta))  # -3 ~ 3 범위로 제한
  ) %>%
  ungroup() %>%
  select(org_id, class_id, student_id, date, theta)

# Parquet 파티션 저장 (org_id/class_id)
student_theta %>%
  group_by(org_id, class_id) %>%
  write_dataset(
    path = file.path(DATASET_ROOT, "student_theta"),
    format = "parquet",
    partitioning = c("org_id", "class_id")
  )

cat("   ✓ student_theta 파티션 저장 (", nrow(student_theta), "건)\n")

# ============================================================================
# 4. 출석 데이터 (최근 90일)
# ============================================================================
cat("4️⃣  출석 데이터 생성 (90일)...\n")

# 학생별 출석 패턴 설정
student_attendance_pattern <- students %>%
  mutate(
    absence_prob = rbeta(n(), 1, 20),      # 결석 확률 (평균 5%)
    late_prob = rbeta(n(), 1, 10),         # 지각 확률 (평균 9%)
    irregular = sample(c(TRUE, FALSE), n(), replace = TRUE, prob = c(0.15, 0.85))
  )

attendance <- expand_grid(
  student_id = students$student_id,
  date = dates[wday(dates) %in% 2:6]  # 평일만
) %>%
  left_join(student_attendance_pattern %>% 
              select(student_id, org_id, class_id, absence_prob, late_prob, irregular),
            by = "student_id") %>%
  mutate(
    # 불규칙 학생은 특정 요일에 결석 확률 증가
    day_of_week = wday(date),
    adjusted_absence_prob = if_else(irregular & day_of_week == 2, 
                                     absence_prob * 3, absence_prob),
    
    status = case_when(
      runif(n()) < adjusted_absence_prob ~ "absent",
      runif(n()) < late_prob ~ "late",
      TRUE ~ "present"
    )
  ) %>%
  select(org_id, class_id, student_id, date, status)

# Parquet 파티션 저장
attendance %>%
  group_by(org_id, class_id) %>%
  write_dataset(
    path = file.path(DATASET_ROOT, "attendance"),
    format = "parquet",
    partitioning = c("org_id", "class_id")
  )

cat("   ✓ attendance 파티션 저장 (", nrow(attendance), "건)\n")

# ============================================================================
# 5. 스킬 취약점 (학생별 TOP3)
# ============================================================================
cat("5️⃣  스킬 취약점 데이터 생성...\n")

skill_weakness <- students %>%
  crossing(skill_rank = 1:3) %>%
  group_by(student_id) %>%
  mutate(
    skill = sample(SKILLS, 3, replace = FALSE)[skill_rank],
    weakness_score = runif(3, 0.3, 0.8)[skill_rank],  # 취약도 점수
    last_updated = today() - days(sample(0:30, 1))
  ) %>%
  ungroup() %>%
  select(org_id, class_id, student_id, skill, weakness_score, skill_rank, last_updated)

write_parquet(skill_weakness, file.path(DATASET_ROOT, "skill_weakness.parquet"))
cat("   ✓ skill_weakness.parquet 저장 (", nrow(skill_weakness), "건)\n")

# ============================================================================
# 6. 문항 반응 통계 (추측/무응답 비율)
# ============================================================================
cat("6️⃣  문항 반응 통계 생성...\n")

response_stats <- students %>%
  mutate(
    total_responses = sample(50:200, n(), replace = TRUE),
    guess_like_rate = rbeta(n(), 2, 10),   # 추측 패턴 비율 (평균 ~17%)
    omit_rate = rbeta(n(), 1, 20),         # 무응답 비율 (평균 ~5%)
    last_updated = today() - days(sample(0:7, n(), replace = TRUE))
  ) %>%
  select(org_id, class_id, student_id, total_responses, 
         guess_like_rate, omit_rate, last_updated)

write_parquet(response_stats, file.path(DATASET_ROOT, "response_stats.parquet"))
cat("   ✓ response_stats.parquet 저장 (", nrow(response_stats), "건)\n")

# ============================================================================
# 완료 메시지
# ============================================================================
cat("\n✅ 샘플 데이터 생성 완료!\n")
cat("   저장 위치:", normalizePath(DATASET_ROOT), "\n")
cat("\n생성된 데이터셋:\n")
cat("   - classes.parquet\n")
cat("   - students.parquet\n")
cat("   - student_theta/ (파티션: org_id/class_id)\n")
cat("   - attendance/ (파티션: org_id/class_id)\n")
cat("   - skill_weakness.parquet\n")
cat("   - response_stats.parquet\n")
