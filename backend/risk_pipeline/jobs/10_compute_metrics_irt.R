#!/usr/bin/env Rscript
# Δθ IRT 확장: 앵커/아이템 파라미터 연결
# 조건부 사용: fact_assessment_item 테이블 존재 시

suppressPackageStartupMessages({
  library(DBI)
  library(RPostgres)
  library(dplyr)
  library(readr)
  library(yaml)
  library(tidyr)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript 10_compute_metrics_irt.R <thresholds_yaml> <output_csv>")
}

thr_yaml <- args[1]
out_csv  <- args[2]

# 설정 로드
thr <- yaml::read_yaml(thr_yaml)

# DB 연결 (DSN 환경 변수 사용)
dsn <- Sys.getenv("DSN")
if (dsn == "") {
  stop("DSN environment variable not set")
}

# DSN 파싱 (postgresql://user:pass@host:port/dbname)
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

# 최근 14일 아이템 로그 로드
qry <- "
SELECT org_id, user_id, test_id, 
       (taken_at AT TIME ZONE 'UTC')::date AS d,
       item_id, a, b, c, anchor_group, 
       correct::int AS y
FROM fact_assessment_item
WHERE taken_at >= now() - interval '14 days'
ORDER BY org_id, user_id, d
"

items <- tryCatch(
  dbGetQuery(con, qry),
  error = function(e) {
    message("Error fetching item data: ", e$message)
    return(data.frame())
  }
)

if (nrow(items) == 0) {
  stop('No item-level rows in last 14 days; use 10_compute_metrics.R instead.')
}

# 사용자별 θ 추정 함수
compute_user <- function(g) {
  g <- arrange(g, d)
  
  # 주간 분할
  last_day <- max(g$d, na.rm = TRUE)
  prev_cut <- last_day - 7
  
  g_prev <- g %>% filter(d <= prev_cut)
  g_curr <- g %>% filter(d > prev_cut)
  
  # 최소 데이터 요구사항
  if (nrow(g_curr) < 5 || nrow(g_prev) < 5) {
    return(NULL)
  }
  
  # Wide format 변환
  to_wide <- function(df) {
    df %>%
      select(user_id, item_id, y) %>%
      pivot_wider(
        id_cols = user_id,
        names_from = item_id,
        values_from = y,
        values_fn = mean  # 중복 응답 처리
      )
  }
  
  X_prev <- to_wide(g_prev)
  X_curr <- to_wide(g_curr)
  
  # 아이템 파라미터 추출
  ip <- g %>%
    distinct(item_id, a, b, c) %>%
    filter(!is.na(a), !is.na(b), !is.na(c))
  
  if (nrow(ip) == 0) {
    return(NULL)
  }
  
  # EAP θ 추정 (간단한 근사)
  eap_theta <- function(X, ip) {
    th <- seq(-4, 4, length.out = 161)
    prior <- dnorm(th)
    
    post_theta <- function(row) {
      like <- rep(1, length(th))
      answered <- names(row)[!is.na(row) & names(row) != "user_id"]
      
      for (it in answered) {
        resp <- as.numeric(row[[it]])
        par <- ip[ip$item_id == it, c("a", "b", "c")]
        
        if (nrow(par) == 0) next
        
        a <- par$a[1]
        b <- par$b[1]
        c <- par$c[1]
        
        # 3PL 모델
        p <- c + (1 - c) * (1 / (1 + exp(-1.7 * a * (th - b))))
        like <- like * ifelse(resp == 1, p, (1 - p))
      }
      
      post <- like * prior
      post <- post / sum(post)
      sum(th * post)
    }
    
    apply(X, 1, post_theta)
  }
  
  theta_prev <- tryCatch(
    mean(eap_theta(X_prev, ip), na.rm = TRUE),
    error = function(e) NA_real_
  )
  
  theta_curr <- tryCatch(
    mean(eap_theta(X_curr, ip), na.rm = TRUE),
    error = function(e) NA_real_
  )
  
  data.frame(
    org_id = g$org_id[1],
    user_id = g$user_id[1],
    theta_t = theta_curr,
    theta_t_1 = theta_prev,
    n_obs = nrow(g)
  )
}

# 모든 사용자에 대해 계산
cat("Computing IRT-based metrics for", length(unique(items$user_id)), "users...\n")

res <- items %>%
  group_by(org_id, user_id) %>%
  group_split() %>%
  lapply(compute_user) %>%
  bind_rows()

# 리스크 플래그 계산
metrics <- res %>%
  mutate(
    delta_7d = theta_t - theta_t_1,
    omit_rate = NA_real_,  # 아이템 레벨에서는 별도 계산 필요
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
readr::write_csv(metrics, out_csv)

cat(sprintf("\n✓ IRT metrics computed: %s\n", out_csv))
cat(sprintf("  - Total users: %d\n", nrow(metrics)))
cat(sprintf("  - CRIT: %d\n", sum(metrics$risk_theta == "CRIT")))
cat(sprintf("  - WARN: %d\n", sum(metrics$risk_theta == "WARN")))
