#!/usr/bin/env Rscript
# 리스크 메트릭 계산: Δθ, omit rate, attendance, c_hat

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
  library(yaml)
  library(lubridate)
})

# 인자 파싱
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 4) {
  stop("Usage: Rscript 10_compute_metrics.R <input_csv> <tenants_yaml> <thresholds_yaml> <output_csv>")
}

input_csv    <- args[1]
tenants_yaml <- args[2]
thr_yaml     <- args[3]
output_csv   <- args[4]

# 설정 로드
tenants <- yaml::read_yaml(tenants_yaml)
thr     <- yaml::read_yaml(thr_yaml)

# 데이터 로드
df <- readr::read_csv(input_csv, show_col_types = FALSE)

# 메트릭 계산
metrics <- df %>%
  group_by(org_id, user_id) %>%
  arrange(record_date) %>%
  summarise(
    # 최신 θ 값
    theta_current = last(na.omit(coalesce(theta_estimate, irt_theta))),
    se_current    = last(na.omit(coalesce(se_estimate, irt_se))),
    
    # 7일 전 θ 값
    theta_7d_ago  = nth(na.omit(coalesce(theta_estimate, irt_theta)), 
                        max(1, n() - 7)),
    
    # 14일 전 θ 값
    theta_14d_ago = first(na.omit(coalesce(theta_estimate, irt_theta))),
    
    # Δθ 계산
    delta_theta_7d  = theta_current - theta_7d_ago,
    delta_theta_14d = theta_current - theta_14d_ago,
    
    # 무응답률 (omit rate)
    omit_rate = mean(coalesce(omitted_count, 0) / 
                     coalesce(total_items, 1), na.rm = TRUE),
    
    # 추측률 (c_hat)
    c_hat_avg = mean(coalesce(c_hat_estimate, irt_c_hat), na.rm = TRUE),
    
    # 출석률
    attendance_rate_7d  = mean(tail(attended, 7), na.rm = TRUE),
    attendance_rate_14d = mean(attended, na.rm = TRUE),
    
    # 연속 결석일
    consecutive_absences = {
      att_vec <- tail(attended, 14)
      if (all(is.na(att_vec))) {
        0
      } else {
        rle_result <- rle(att_vec == 0)
        max(rle_result$lengths[rle_result$values], 0)
      }
    },
    
    # 연속 θ 하락 주차
    consecutive_decline_weeks = {
      theta_vec <- na.omit(coalesce(irt_delta_theta, delta_theta_7d))
      if (length(theta_vec) < 2) {
        0
      } else {
        rle_result <- rle(theta_vec < 0)
        max(rle_result$lengths[rle_result$values], 0)
      }
    },
    
    # 데이터 포인트 수
    n_assessments = sum(!is.na(test_id)),
    n_attendance  = sum(!is.na(attended)),
    
    .groups = "drop"
  ) %>%
  
  # 리스크 플래그 계산
  mutate(
    # θ 하락 리스크
    risk_theta = case_when(
      delta_theta_7d <= thr$theta$delta_7d_crit ~ "CRIT",
      delta_theta_7d <= thr$theta$delta_7d_warn ~ "WARN",
      delta_theta_14d <= thr$theta$delta_14d_crit ~ "CRIT",
      delta_theta_14d <= thr$theta$delta_14d_warn ~ "WARN",
      consecutive_decline_weeks >= thr$consecutive$theta_decline_weeks ~ "WARN",
      TRUE ~ "OK"
    ),
    
    # 무응답 리스크
    risk_omit = case_when(
      omit_rate >= thr$omit$rate_crit ~ "CRIT",
      omit_rate >= thr$omit$rate_warn ~ "WARN",
      TRUE ~ "OK"
    ),
    
    # 추측 리스크
    risk_guess = case_when(
      c_hat_avg >= thr$guess$c_hat_crit ~ "CRIT",
      c_hat_avg >= thr$guess$c_hat_warn ~ "WARN",
      TRUE ~ "OK"
    ),
    
    # 출석 리스크
    risk_attendance = case_when(
      (1 - attendance_rate_7d) >= thr$attendance$miss_rate_week_crit ~ "CRIT",
      (1 - attendance_rate_7d) >= thr$attendance$miss_rate_week_warn ~ "WARN",
      (1 - attendance_rate_14d) >= thr$attendance$miss_rate_2week_crit ~ "CRIT",
      (1 - attendance_rate_14d) >= thr$attendance$miss_rate_2week_warn ~ "WARN",
      consecutive_absences >= thr$consecutive$absence_days ~ "CRIT",
      TRUE ~ "OK"
    ),
    
    # 종합 리스크 레벨
    risk_overall = case_when(
      "CRIT" %in% c(risk_theta, risk_omit, risk_guess, risk_attendance) ~ "CRIT",
      "WARN" %in% c(risk_theta, risk_omit, risk_guess, risk_attendance) ~ "WARN",
      TRUE ~ "OK"
    )
  )

# 결과 저장
readr::write_csv(metrics, output_csv)

# 요약 출력
cat(sprintf("\n=== Risk Metrics Computed ===\n"))
cat(sprintf("Total students: %d\n", nrow(metrics)))
cat(sprintf("CRIT: %d (%.1f%%)\n", 
            sum(metrics$risk_overall == "CRIT"),
            100 * mean(metrics$risk_overall == "CRIT")))
cat(sprintf("WARN: %d (%.1f%%)\n", 
            sum(metrics$risk_overall == "WARN"),
            100 * mean(metrics$risk_overall == "WARN")))
cat(sprintf("OK:   %d (%.1f%%)\n", 
            sum(metrics$risk_overall == "OK"),
            100 * mean(metrics$risk_overall == "OK")))
