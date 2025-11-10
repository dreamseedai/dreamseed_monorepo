# ------------------------------------------------------------
# irt_drift_pipeline.R
#  - 3PL (unidim) + MIRT (multidim 2PL/3PL) + Bayesian drift
#  - Weekly/daily moving-window recalibration + flags
#  - Outputs to Postgres tables
#
# 파일 위치: /portal_front/r-irt-plumber/irt_drift_pipeline.R
# 사용법: source("irt_drift_pipeline.R"); run_drift()
# ------------------------------------------------------------

suppressPackageStartupMessages({
  library(DBI)
  library(RPostgres)
  library(dplyr)
  library(tidyr)
  library(mirt)
  library(purrr)
  library(stringr)
  library(lubridate)
  library(jsonlite)
  library(rstan)       # Bayesian
})

# ---- Config ------------------------------------------------
DRIFT_CONF <- list(
  window_days     = 56,          # 최근 8주
  min_resp_per_it = 200,         # 문항당 최소 응답수
  tau_b           = 0.20,        # |Δb| 임계
  tau_a           = 0.15,        # |Δa| 임계 (상대폭)
  tau_c           = 0.05,        # |Δc| 임계
  prob_thresh     = 0.95,        # P(|Δ|>τ) >= 0.95
  use_multidim    = TRUE,        # 다차원 추정 실행 여부
  multidim_K      = 2,           # 잠재차원 수
  use_3pl         = TRUE         # 3PL 사용
)

# ---- DB helpers --------------------------------------------
pg_conn <- function() {
  dbConnect(
    RPostgres::Postgres(),
    host     = Sys.getenv("PGHOST", "localhost"),
    port     = as.integer(Sys.getenv("PGPORT", "5432")),
    user     = Sys.getenv("PGUSER", "postgres"),
    password = Sys.getenv("PGPASSWORD", ""),
    dbname   = Sys.getenv("PGDATABASE", "dreamseed")
  )
}

# 표준 스키마/테이블명
T_RESP_VIEW   <- "view_item_responses_recent"
T_BASE_PARAMS <- "irt_item_params_baseline"
T_OUT_LOG     <- "item_drift_log"
T_OUT_PARAMS  <- "irt_item_params_latest"

# ---- Data fetchers -----------------------------------------
fetch_recent_long <- function(con, window_days) {
  sql <- sprintf("
    SELECT user_id, item_id, correct, ts
    FROM %s
    WHERE ts >= now() - interval '%d days'
  ", DBI::dbQuoteIdentifier(con, T_RESP_VIEW), window_days)
  DBI::dbGetQuery(con, sql) %>%
    mutate(correct = as.integer(correct))
}

fetch_baseline_params <- function(con) {
  DBI::dbReadTable(con, T_BASE_PARAMS)
}

# ---- Wide cast (user x item) -------------------------------
to_wide <- function(df_long) {
  df_long %>%
    arrange(ts) %>%
    select(user_id, item_id, correct) %>%
    distinct() %>%
    pivot_wider(names_from = item_id, values_from = correct) %>%
    select(-user_id) %>%
    as.data.frame()
}

# ---- mirt estimation ---------------------------------------
fit_mirt <- function(data_wide, use_3pl=TRUE, multidim=FALSE, K=2) {
  keep <- colSums(!is.na(data_wide)) >= DRIFT_CONF$min_resp_per_it
  data_wide <- data_wide[, keep, drop=FALSE]
  if (ncol(data_wide) < 5) stop("Not enough items after filtering")

  itemtype <- if (use_3pl) "3PL" else "2PL"

  if (!multidim) {
    mod <- mirt(data_wide, model = 1, itemtype = itemtype, SE = TRUE, verbose = FALSE)
    pars <- coef(mod, IRTpars = TRUE, simplify = TRUE)$items %>% as.data.frame()
    pars$item_id <- rownames(pars)
    out <- pars %>%
      transmute(item_id, a=a, b=b, c=ifelse("g" %in% names(pars), g, NA_real_),
                se_a=ifelse("na" %in% names(pars), na, NA_real_),
                se_b=ifelse("nb" %in% names(pars), nb, NA_real_),
                se_c=ifelse("ng" %in% names(pars), ng, NA_real_),
                k=1, a_vec=NA_character_, model=paste0(ifelse(use_3pl,"3PL","2PL"), "-1D"))
    return(list(model=mod, params=out))
  } else {
    spec <- mirt.model(paste0("
      F1 = 1-", ncol(data_wide), "
      F2 = 1-", ncol(data_wide), "
      COV = F1*F2
    "))
    mod <- mirt(data_wide, model = spec, itemtype = itemtype, SE = TRUE, verbose = FALSE, method="EM")
    pars <- coef(mod, IRTpars = TRUE, simplify = TRUE)
    items <- as.data.frame(pars$items)
    items$item_id <- rownames(items)
    a_mat <- as.matrix(items[, grep("^a", colnames(items)) , drop=FALSE])
    a_norm <- sqrt(rowSums(a_mat^2))
    a_vec_json <- apply(a_mat, 1, function(v) jsonlite::toJSON(as.numeric(v)))
    out <- items %>%
      transmute(item_id,
                a = a_norm,
                b = b,
                c = ifelse("g" %in% names(items), g, NA_real_),
                se_a = ifelse("na" %in% names(items), na, NA_real_),
                se_b = ifelse("nb" %in% names(items), nb, NA_real_),
                se_c = ifelse("ng" %in% names(items), ng, NA_real_),
                k = DRIFT_CONF$multidim_K,
                a_vec = a_vec_json,
                model = paste0(ifelse(use_3pl,"3PL","2PL"), "-MD[K=", DRIFT_CONF$multidim_K, "]"))
    return(list(model=mod, params=out))
  }
}

# ---- Bayesian update (Stan) --------------------------------
stan_3pl_unidim <- "
data {
  int<lower=1> N; int<lower=1> I; int<lower=1> P;
  int<lower=1,upper=I> item[N];
  int<lower=1,upper=P> person[N];
  int<lower=0,upper=1> y[N];
  vector[I] a0; vector[I] b0; vector[I] c0;
  vector<lower=0>[I] se_a0; vector<lower=0>[I] se_b0; vector<lower=0>[I] se_c0;
}
parameters {
  vector[I] a_raw; vector[I] b; vector<lower=0,upper=1>[I] c; vector[P] theta;
}
transformed parameters { vector[I] a = exp(a_raw); }
model {
  a_raw ~ normal(log(a0), se_a0 + 1e-6);
  b     ~ normal(b0,      se_b0 + 1e-6);
  c     ~ normal(c0,      se_c0 + 1e-6);
  theta ~ normal(0, 1);
  for (n in 1:N) {
    real z = a[item[n]] * (theta[person[n]] - b[item[n]]);
    real p = c[item[n]] + (1 - c[item[n]]) * inv_logit(z);
    y[n] ~ bernoulli(p);
  }
}
"

stan_2pl_mirt_k2 <- "
data {
  int<lower=1> N; int<lower=1> I; int<lower=1> P;
  int<lower=1,upper=I> item[N];
  int<lower=1,upper=P> person[N];
  int<lower=0,upper=1> y[N];
  vector[I] b0; vector<lower=0>[I] se_b0;
  matrix[I,2] a0; matrix<lower=0>[I,2] se_a0;
}
parameters {
  matrix[I,2] a_raw; vector[I] b; matrix[P,2] theta;
}
model {
  for (i in 1:I) { a_raw[i] ~ normal(log(a0[i]), se_a0[i] + 1e-6); }
  b ~ normal(b0, se_b0 + 1e-6);
  to_vector(theta) ~ normal(0,1);
  for (n in 1:N) {
    real z = exp(a_raw[item[n],1]) * (theta[person[n],1] - b[item[n]]) +
             exp(a_raw[item[n],2]) * (theta[person[n],2] - b[item[n]])/2;
    y[n] ~ bernoulli_logit(z);
  }
}
"

compile_cached <- local({
  cache <- new.env(parent = emptyenv())
  function(model_code, name) {
    if (!exists(name, envir = cache)) {
      cache[[name]] <- rstan::stan_model(model_code = model_code)
    }
    cache[[name]]
  }
})

# ---- Prepare Stan data -------------------------------------
prep_stan_data <- function(df_long, baseline, multidim=FALSE, K=2, use_3pl=TRUE) {
  df <- df_long %>% arrange(user_id, item_id, ts)
  users <- unique(df$user_id)
  items <- unique(df$item_id)
  df$person <- match(df$user_id, users)
  df$item_i <- match(df$item_id, items)
  y <- as.integer(df$correct)

  b0tab <- baseline %>% filter(item_id %in% items)
  b0 <- b0tab$b[match(items, b0tab$item_id)]
  se_b0 <- ifelse(is.na(b0tab$se_b), 0.25, b0tab$se_b)[match(items, b0tab$item_id)]
  a0 <- b0tab$a[match(items, b0tab$item_id)]
  se_a0 <- ifelse(is.na(b0tab$se_a), 0.25, b0tab$se_a)[match(items, b0tab$item_id)]
  c0 <- ifelse(is.na(b0tab$c), 0.15, b0tab$c)[match(items, b0tab$item_id)]
  se_c0 <- ifelse(is.na(b0tab$se_c), 0.05, b0tab$se_c)[match(items, b0tab$item_id)]

  if (!multidim) {
    data <- list(
      N = nrow(df), I = length(items), P = length(users),
      item = df$item_i, person = df$person, y = y,
      a0 = pmax(a0, 0.2), b0 = b0, c0 = pmin(pmax(c0, 0.01), 0.35),
      se_a0 = pmax(se_a0, 0.05), se_b0 = pmax(se_b0, 0.05), se_c0 = pmax(se_c0, 0.02)
    )
    return(list(data=data, items=items))
  } else {
    a_vec_mat <- matrix(NA_real_, nrow=length(items), ncol=K)
    av_json <- b0tab$a_vec[match(items, b0tab$item_id)]
    for (i in seq_along(items)) {
      if (!is.na(av_json[i])) {
        v <- tryCatch(jsonlite::fromJSON(av_json[i]), error=function(e) rep(NA_real_, K))
        if (length(v) >= K) a_vec_mat[i,] <- v[1:K]
      }
    }
    a_vec_mat[is.na(a_vec_mat)] <- a0[is.na(a_vec_mat)]
    data <- list(
      N = nrow(df), I = length(items), P = length(users),
      item = df$item_i, person = df$person, y = y,
      b0 = b0, se_b0 = pmax(se_b0, 0.05),
      a0 = a_vec_mat, se_a0 = matrix(pmax(se_a0, 0.05), nrow=length(items), ncol=K)
    )
    return(list(data=data, items=items))
  }
}

# ---- Posterior summaries -----------------------------------
post_delta_summaries <- function(samples, items, baseline, multidim=FALSE, K=2, use_3pl=TRUE) {
  ex <- rstan::extract(samples, permuted=TRUE)
  b0 <- baseline$b[match(items, baseline$item_id)]
  a0 <- baseline$a[match(items, baseline$item_id)]
  c0 <- baseline$c[match(items, baseline$item_id)]

  if (!multidim) {
    a <- apply(ex$a, 2, mean)
    b <- apply(ex$b, 2, mean)
    c <- apply(ex$c, 2, mean)
    delta_a <- a - a0; delta_b <- b - b0; delta_c <- c - c0
    ci <- function(v) quantile(v, probs=c(0.025, 0.975), na.rm=TRUE)
    ci_a <- t(apply(ex$a, 2, ci))
    ci_b <- t(apply(ex$b, 2, ci))
    ci_c <- t(apply(ex$c, 2, ci))
    p_abs <- function(draws, base, tau) mean(abs(draws - base) > tau)
    p_a <- sapply(1:length(items), function(i) p_abs(ex$a[,i], a0[i], DRIFT_CONF$tau_a))
    p_b <- sapply(1:length(items), function(i) p_abs(ex$b[,i], b0[i], DRIFT_CONF$tau_b))
    p_c <- sapply(1:length(items), function(i) p_abs(ex$c[,i], c0[i], DRIFT_CONF$tau_c))
    tibble(
      item_id = items, k = 1, model = "3PL-1D",
      delta_a, delta_b, delta_c,
      ci_a_low = ci_a[,1], ci_a_high = ci_a[,2],
      ci_b_low = ci_b[,1], ci_b_high = ci_b[,2],
      ci_c_low = ci_c[,1], ci_c_high = ci_c[,2],
      p_abs_a = p_a, p_abs_b = p_b, p_abs_c = p_c,
      flag_a = p_a >= DRIFT_CONF$prob_thresh,
      flag_b = p_b >= DRIFT_CONF$prob_thresh,
      flag_c = p_c >= DRIFT_CONF$prob_thresh
    )
  } else {
    ar <- rstan::extract(samples, pars="a_raw")$a_raw
    I <- length(items)
    a_norm_draws <- array(NA_real_, dim=c(dim(ar)[1], I))
    for (s in 1:dim(ar)[1]) {
      A <- exp(ar[s,,])
      a_norm_draws[s,] <- sqrt(rowSums(A^2))
    }
    a <- apply(a_norm_draws, 2, mean)
    b <- apply(rstan::extract(samples, pars="b")$b, 2, mean)
    delta_a <- a - a0; delta_b <- b - b0
    ci <- function(v) quantile(v, probs=c(0.025, 0.975), na.rm=TRUE)
    ci_a <- t(apply(a_norm_draws, 2, ci))
    b_draws <- rstan::extract(samples, pars="b")$b
    ci_b <- t(apply(b_draws, 2, ci))
    p_abs <- function(draws, base, tau) mean(abs(draws - base) > tau)
    p_a <- sapply(1:I, function(i) p_abs(a_norm_draws[,i], a0[i], DRIFT_CONF$tau_a))
    p_b <- sapply(1:I, function(i) p_abs(b_draws[,i], b0[i], DRIFT_CONF$tau_b))
    tibble(
      item_id = items, k = DRIFT_CONF$multidim_K, model = paste0("2PL-MD[K=", DRIFT_CONF$multidim_K, "]"),
      delta_a = delta_a, delta_b = delta_b, delta_c = NA_real_,
      ci_a_low = ci_a[,1], ci_a_high = ci_a[,2],
      ci_b_low = ci_b[,1], ci_b_high = ci_b[,2],
      ci_c_low = NA_real_, ci_c_high = NA_real_,
      p_abs_a = p_a, p_abs_b = p_b, p_abs_c = NA_real_,
      flag_a = p_a >= DRIFT_CONF$prob_thresh,
      flag_b = p_b >= DRIFT_CONF$prob_thresh,
      flag_c = FALSE
    )
  }
}

# ---- Persist results ---------------------------------------
upsert_latest_params <- function(con, params_df) {
  tmp <- paste0("tmp_params_", as.integer(Sys.time()))
  DBI::dbWriteTable(con, tmp, params_df, temporary=TRUE)
  sql <- sprintf("
    INSERT INTO %s(item_id, model, a, b, c, se_a, se_b, se_c, k, a_vec, updated_at)
    SELECT item_id, model, a, b, c, se_a, se_b, se_c, k, a_vec::jsonb, now()
    FROM %s
    ON CONFLICT (item_id) DO UPDATE SET
      model=EXCLUDED.model, a=EXCLUDED.a, b=EXCLUDED.b, c=EXCLUDED.c,
      se_a=EXCLUDED.se_a, se_b=EXCLUDED.se_b, se_c=EXCLUDED.se_c,
      k=EXCLUDED.k, a_vec=EXCLUDED.a_vec, updated_at=now();
    DROP TABLE %s;
  ", T_OUT_PARAMS, tmp, tmp)
  DBI::dbExecute(con, sql)
}

insert_drift_log <- function(con, drift_df, t_window, n_resp, raw=NULL) {
  drift_df %>%
    mutate(t_window_d = t_window,
           n_resp = n_resp,
           raw = jsonlite::toJSON(raw, auto_unbox = TRUE)) %>%
    DBI::dbWriteTable(con, T_OUT_LOG, ., append=TRUE)
}

# ---- Main entry --------------------------------------------
run_drift <- function(
  use_3pl      = DRIFT_CONF$use_3pl,
  multidim     = DRIFT_CONF$use_multidim,
  K            = DRIFT_CONF$multidim_K,
  iter         = 1000, chains=2, seed=123
) {
  con <- pg_conn(); on.exit(DBI::dbDisconnect(con), add=TRUE)

  recent <- fetch_recent_long(con, DRIFT_CONF$window_days)
  if (nrow(recent) < 1000) stop("Not enough recent responses")

  t_window <- paste0(
    format(min(recent$ts), "%Y-%m-%d"), "..",
    format(max(recent$ts), "%Y-%m-%d")
  )

  baseline <- fetch_baseline_params(con)
  wide <- to_wide(recent)

  mirt_fit <- fit_mirt(wide, use_3pl=use_3pl, multidim=multidim, K=K)
  quick_params <- mirt_fit$params

  stan_dat <- prep_stan_data(recent, baseline, multidim=multidim, K=K, use_3pl=use_3pl)

  if (!multidim) {
    sm <- compile_cached(stan_3pl_unidim, "stan_3pl_unidim")
  } else {
    sm <- compile_cached(stan_2pl_mirt_k2, "stan_2pl_mirt_k2")
  }

  fit <- rstan::sampling(sm, data=stan_dat$data, iter=iter, chains=chains, seed=seed, refresh=0)

  drift <- post_delta_summaries(fit, stan_dat$items, baseline, multidim=multidim, K=K, use_3pl=use_3pl)

  if (!multidim) {
    ex <- rstan::extract(fit)
    a_mean <- apply(ex$a, 2, mean); b_mean <- apply(ex$b, 2, mean); c_mean <- apply(ex$c, 2, mean)
    a_ci <- t(apply(ex$a, 2, function(v) quantile(v, c(0.025,0.975))))
    b_ci <- t(apply(ex$b, 2, function(v) quantile(v, c(0.025,0.975))))
    c_ci <- t(apply(ex$c, 2, function(v) quantile(v, c(0.025,0.975))))
    latest <- tibble(
      item_id = stan_dat$items, model="3PL-1D", k=1,
      a=a_mean, b=b_mean, c=c_mean,
      se_a=(a_ci[,2]-a_ci[,1])/3.92,
      se_b=(b_ci[,2]-b_ci[,1])/3.92,
      se_c=(c_ci[,2]-c_ci[,1])/3.92,
      a_vec = NA_character_
    )
  } else {
    ar <- rstan::extract(fit, pars="a_raw")$a_raw
    I <- length(stan_dat$items)
    a_norm <- apply(ar, 2, function(v) mean(exp(v)))
    b_mean <- apply(rstan::extract(fit, pars="b")$b, 2, mean)
    a_ci <- t(apply(exp(ar), 2, function(v) quantile(v, c(0.025,0.975))))
    b_draws <- rstan::extract(fit, pars="b")$b
    b_ci <- t(apply(b_draws, 2, function(v) quantile(v, c(0.025,0.975))))
    latest <- tibble(
      item_id = stan_dat$items, model=paste0("2PL-MD[K=", K, "]"), k=K,
      a=a_norm, b=b_mean, c=NA_real_,
      se_a=(a_ci[,2]-a_ci[,1])/3.92, se_b=(b_ci[,2]-b_ci[,1])/3.92, se_c=NA_real_,
      a_vec = NA_character_
    )
  }

  upsert_latest_params(con, latest)
  insert_drift_log(con, drift, t_window, n_resp=nrow(recent),
                   raw=list(quick_params=quick_params, conf=DRIFT_CONF))

  list(
    window=t_window,
    n_resp=nrow(recent),
    n_items=length(unique(recent$item_id)),
    flags=sum(drift$flag_a | drift$flag_b | drift$flag_c, na.rm=TRUE),
    drift=drift
  )
}

# ---- Utility functions -------------------------------------
get_latest_params <- function(item_ids=NULL, limit=200) {
  con <- pg_conn(); on.exit(DBI::dbDisconnect(con), add=TRUE)
  if (is.null(item_ids)) {
    sql <- sprintf("SELECT * FROM %s ORDER BY updated_at DESC LIMIT %d", T_OUT_PARAMS, limit)
  } else {
    ids <- paste(sprintf("'%s'", gsub("'", "''", item_ids)), collapse=",")
    sql <- sprintf("SELECT * FROM %s WHERE item_id IN (%s)", T_OUT_PARAMS, ids)
  }
  DBI::dbGetQuery(con, sql)
}

get_drift_items <- function(since_days=30, only_flagged=TRUE, limit=500) {
  con <- pg_conn(); on.exit(DBI::dbDisconnect(con), add=TRUE)
  where <- sprintf("created_at >= now() - interval '%d days'", since_days)
  if (only_flagged) {
    where <- paste0(where, " AND (flag_a OR flag_b OR flag_c)")
  }
  sql <- sprintf("SELECT * FROM %s WHERE %s ORDER BY created_at DESC LIMIT %d", T_OUT_LOG, where, limit)
  DBI::dbGetQuery(con, sql)
}
