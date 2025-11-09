#!/usr/bin/env Rscript
# mirt 앵커 고정 다집단 IRT 파이프라인 (프로덕션용)
# 이전 7일 vs 최근 7일을 group으로 두고 앵커 아이템 파라미터 불변 제약

suppressPackageStartupMessages({
  library(DBI)
  library(RPostgres)
  library(dplyr)
  library(tidyr)
  library(purrr)
  library(mirt)
  library(readr)
  library(yaml)
  library(lubridate)
})

# 인자 파싱
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript 10_compute_metrics_mg_anchor.R <thresholds_yaml> <output_csv>")
}

thr_yaml <- args[1]
out_csv  <- args[2]

# 설정 로드
thr <- yaml::read_yaml(thr_yaml)

# DB 연결
dsn <- Sys.getenv("DSN")
if (dsn == "") {
  stop("DSN environment variable not set")
}

# DSN 파싱
dsn_parts <- regmatches(dsn, regexec("postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)", dsn))[[1]]
if (length(dsn_parts) != 6) {
  stop("Invalid DSN format")
}

con <- dbConnect(
  RPostgres::Postgres(),
  user = dsn_parts[2],
  password = dsn_parts[3],
  host = dsn_parts[4],
  port = as.integer(dsn_parts[5]),
  dbname = dsn_parts[6]
)
on.exit(dbDisconnect(con), add = TRUE)

cat("=== mirt Multi-Group Anchor IRT Pipeline ===\n")

# 최근 14일 아이템 반응 로드
qry <- "
SELECT org_id, user_id, item_id, 
       (taken_at AT TIME ZONE 'UTC')::date AS d,
       u_resp::int AS y, 
       anchor_group, 
       a, b, c
FROM fact_assessment_item
WHERE taken_at >= now() - interval '14 days'
ORDER BY org_id, user_id, d
"

X <- tryCatch(
  dbGetQuery(con, qry),
  error = function(e) {
    message("Error fetching item data: ", e$message)
    return(data.frame())
  }
)

if (nrow(X) == 0) {
  stop('No item-level rows in last 14 days; use 10_compute_metrics.R instead.')
}

cat(sprintf("Loaded %d item responses\n", nrow(X)))

# 그룹 분할: prev (≤ last-7d), curr (> last-7d)
last_d <- max(X$d)
cutoff <- last_d - 7
X$grp <- ifelse(X$d <= cutoff, "prev", "curr")

cat(sprintf("Cutoff date: %s\n", cutoff))
cat(sprintf("  prev group: %d responses\n", sum(X$grp == "prev")))
cat(sprintf("  curr group: %d responses\n", sum(X$grp == "curr")))

# 사용자별 θ 추정 함수
estimate_user <- function(df) {
  # 두 그룹 모두 있는지 확인
  if (length(unique(df$grp)) < 2) {
    return(NULL)
  }
  
  # Wide format 변환
  wid <- df %>%
    mutate(item = paste0("I", item_id)) %>%
    select(user_id, grp, item, y) %>%
    group_by(grp, user_id, item) %>%
    summarise(y = as.integer(round(mean(y, na.rm = TRUE))), .groups = "drop") %>%
    pivot_wider(names_from = item, values_from = y)
  
  # 그룹별 데이터 분리
  split_d <- split(wid %>% select(-user_id), wid$grp)
  
  if (!all(c("prev", "curr") %in% names(split_d))) {
    return(NULL)
  }
  
  # 공통 아이템 교집합
  common_items <- intersect(colnames(split_d$prev), colnames(split_d$curr))
  common_items <- setdiff(common_items, "grp")
  
  if (length(common_items) < 10) {
    return(NULL)
  }
  
  dat_prev <- as.data.frame(split_d$prev[, common_items, drop = FALSE])
  dat_curr <- as.data.frame(split_d$curr[, common_items, drop = FALSE])
  
  # multipleGroup 데이터 구성
  dat <- rbind(dat_prev, dat_curr)
  group <- c(rep("prev", nrow(dat_prev)), rep("curr", nrow(dat_curr)))
  
  # 앵커 아이템 선택 (anchor_group != null)
  anchor_items <- df %>%
    filter(!is.na(anchor_group)) %>%
    transmute(item = paste0("I", item_id)) %>%
    distinct() %>%
    pull(item)
  
  anchor_items <- intersect(anchor_items, common_items)
  
  # 아이템 타입 (3PL)
  itemtype <- rep("3PL", length(common_items))
  names(itemtype) <- common_items
  
  # 앵커 제약: slopes(a), intercepts(b), guessing(c) 불변
  invariance <- list()
  if (length(anchor_items) > 0) {
    invariance <- list(
      free_means = TRUE,
      free_var = TRUE,
      slopes = anchor_items,
      intercepts = anchor_items,
      guessing = anchor_items
    )
  }
  
  # mirt multipleGroup 적합
  fit <- try(
    multipleGroup(
      dat, 1,
      group = group,
      itemtype = itemtype,
      invariance = invariance,
      SE = FALSE,
      verbose = FALSE
    ),
    silent = TRUE
  )
  
  if (inherits(fit, "try-error")) {
    return(NULL)
  }
  
  # θ EAP 추정
  fs <- fscores(fit, method = "EAP", full.scores = TRUE)
  nm <- rownames(fs)
  
  th_prev <- mean(fs[grepl("^prev", nm), 1], na.rm = TRUE)
  th_curr <- mean(fs[grepl("^curr", nm), 1], na.rm = TRUE)
  
  tibble(
    org_id = df$org_id[1],
    user_id = df$user_id[1],
    theta_t = th_curr,
    theta_t_1 = th_prev,
    n_obs = nrow(df),
    n_anchor = length(anchor_items)
  )
}

# 모든 사용자에 대해 계산
cat("\nEstimating θ for users...\n")

res <- X %>%
  group_by(org_id, user_id) %>%
  group_split() %>%
  map_dfr(estimate_user, .progress = TRUE)

if (nrow(res) == 0) {
  stop("No users could be estimated")
}

# 리스크 플래그 계산
metrics <- res %>%
  mutate(
    delta_7d = theta_t - theta_t_1,
    omit_rate = NA_real_,
    attend_rate = NA_real_
  ) %>%
  mutate(
    risk_theta = case_when(
      !is.na(delta_7d) & delta_7d <= thr$theta$delta_14d_crit ~ "CRIT",
      !is.na(delta_7d) & delta_7d <= thr$theta$delta_7d_warn ~ "WARN",
      TRUE ~ "OK"
    ),
    risk_omit = "OK",
    risk_attend = "OK"
  )

# 결과 저장
write_csv(metrics, out_csv)

cat(sprintf("\n✓ mirt multi-group metrics computed: %s\n", out_csv))
cat(sprintf("  - Total users: %d\n", nrow(metrics)))
cat(sprintf("  - CRIT: %d (%.1f%%)\n", 
            sum(metrics$risk_theta == "CRIT"),
            100 * mean(metrics$risk_theta == "CRIT")))
cat(sprintf("  - WARN: %d (%.1f%%)\n", 
            sum(metrics$risk_theta == "WARN"),
            100 * mean(metrics$risk_theta == "WARN")))
cat(sprintf("  - OK: %d (%.1f%%)\n", 
            sum(metrics$risk_theta == "OK"),
            100 * mean(metrics$risk_theta == "OK")))
cat(sprintf("  - Avg anchor items: %.1f\n", mean(metrics$n_anchor, na.rm = TRUE)))
