#!/usr/bin/env Rscript
#' Bayesian IRT Calibration with brms
#' ====================================
#' Monthly calibration using hierarchical 2PL model with anchor item priors
#' 
#' Features:
#' - Hierarchical Bayesian 2PL model (brms + cmdstanr)
#' - Anchor item stability via informative priors
#' - Automatic window creation for previous month
#' - Drift detection (Δb, Δa)
#' - PostgreSQL integration
#' 
#' Usage:
#'   Rscript calibrate_monthly_brms.R \
#'     --dbname dreamseed \
#'     --host 127.0.0.1 \
#'     --user postgres \
#'     --password *** \
#'     --min-responses 200 \
#'     --window-label "2025-10 monthly"
#' 
#' Dependencies:
#'   install.packages(c("dplyr", "DBI", "RPostgres", "brms", "cmdstanr", "optparse", "jsonlite"))

suppressPackageStartupMessages({
  library(dplyr)
  library(DBI)
  library(RPostgres)
  library(brms)
  library(jsonlite)
  library(optparse)
})

# ==============================================================================
# CLI Options
# ==============================================================================
option_list <- list(
  make_option(c("--dbname"), type="character", default="dreamseed",
              help="PostgreSQL database name [default: %default]"),
  make_option(c("--host"), type="character", default="127.0.0.1",
              help="PostgreSQL host [default: %default]"),
  make_option(c("--user"), type="character", default="postgres",
              help="PostgreSQL user [default: %default]"),
  make_option(c("--password"), type="character", default=NULL,
              help="PostgreSQL password [required]", metavar="PASSWORD"),
  make_option(c("--port"), type="integer", default=5432,
              help="PostgreSQL port [default: %default]"),
  make_option(c("--window-label"), type="character", default=NULL,
              help="Window label (default: auto-generate for previous month)"),
  make_option(c("--min-responses"), type="integer", default=200,
              help="Minimum responses per item [default: %default]"),
  make_option(c("--drift-threshold-b"), type="numeric", default=0.25,
              help="Difficulty drift threshold |Δb| [default: %default]"),
  make_option(c("--drift-threshold-a"), type="numeric", default=0.2,
              help="Discrimination drift threshold |Δa| [default: %default]"),
  make_option(c("--iter"), type="integer", default=2000,
              help="MCMC iterations [default: %default]"),
  make_option(c("--warmup"), type="integer", default=1000,
              help="MCMC warmup [default: %default]"),
  make_option(c("--chains"), type="integer", default=4,
              help="MCMC chains [default: %default]"),
  make_option(c("--cores"), type="integer", default=4,
              help="Parallel cores [default: %default]")
)

parser <- OptionParser(
  usage="%prog [options]",
  option_list=option_list,
  description="Bayesian IRT calibration with brms"
)

args <- parse_args(parser)

# Validate
if (is.null(args$password)) {
  stop("Error: --password is required")
}

cat(sprintf("[INFO] Connecting to PostgreSQL: %s@%s/%s\n", 
            args$user, args$host, args$dbname))

# ==============================================================================
# Database Connection
# ==============================================================================
pg <- tryCatch({
  dbConnect(
    RPostgres::Postgres(),
    dbname = args$dbname,
    host = args$host,
    port = args$port,
    user = args$user,
    password = args$password
  )
}, error = function(e) {
  stop(paste("Failed to connect to database:", e$message))
})

cat("[INFO] Database connected\n")

# ==============================================================================
# Create or Get Calibration Window
# ==============================================================================
create_window <- function(pg, label = NULL) {
  if (is.null(label)) {
    # Auto-generate label for previous month
    label <- dbGetQuery(pg, "
      SELECT to_char(date_trunc('month', now() - interval '1 month'), 'YYYY-MM') || ' monthly' AS label
    ")$label[1]
  }
  
  # Check if window exists
  existing <- dbGetQuery(pg, 
    "SELECT id, start_at, end_at FROM shared_irt.windows WHERE label = $1",
    params = list(label)
  )
  
  if (nrow(existing) > 0) {
    cat(sprintf("[INFO] Using existing window: %s (id=%d)\n", label, existing$id[1]))
    return(existing)
  }
  
  # Create new window
  win <- dbGetQuery(pg, "
    INSERT INTO shared_irt.windows (label, start_at, end_at, population_tags)
    VALUES (
      $1,
      date_trunc('month', now() - interval '1 month'),
      date_trunc('month', now()),
      ARRAY['global']
    )
    RETURNING id, start_at, end_at, label
  ", params = list(label))
  
  cat(sprintf("[INFO] Created window: %s (id=%d)\n", win$label[1], win$id[1]))
  cat(sprintf("[INFO] Date range: %s to %s\n", win$start_at[1], win$end_at[1]))
  
  return(win)
}

win <- create_window(pg, args$window_label)
win_id <- win$id[1]

# ==============================================================================
# Load Response Data
# ==============================================================================
cat(sprintf("[INFO] Loading responses for window %d...\n", win_id))

resp <- dbGetQuery(pg, sprintf("
  SELECT 
    r.item_id, 
    r.user_id_hash, 
    r.is_correct::int AS y
  FROM shared_irt.item_responses r
  WHERE r.answered_at >= (SELECT start_at FROM shared_irt.windows WHERE id = %d)
    AND r.answered_at <  (SELECT end_at   FROM shared_irt.windows WHERE id = %d)
", win_id, win_id))

if (nrow(resp) == 0) {
  stop("Error: No responses found for this window")
}

cat(sprintf("[INFO] Loaded %d total responses\n", nrow(resp)))

# Filter items with sufficient responses
resp_counts <- resp %>% 
  count(item_id, name = "n_responses") %>%
  arrange(desc(n_responses))

eligible_items <- resp_counts %>%
  filter(n_responses >= args$min_responses) %>%
  pull(item_id)

if (length(eligible_items) == 0) {
  stop(sprintf("Error: No items with >= %d responses", args$min_responses))
}

cat(sprintf("[INFO] Eligible items: %d (>= %d responses)\n", 
            length(eligible_items), args$min_responses))

dat <- resp %>% 
  filter(item_id %in% eligible_items) %>%
  mutate(
    user = factor(user_id_hash),
    item = factor(item_id)
  )

cat(sprintf("[INFO] Final dataset: %d responses, %d users, %d items\n",
            nrow(dat), n_distinct(dat$user), n_distinct(dat$item)))

# ==============================================================================
# Load Anchor Item Parameters
# ==============================================================================
cat("[INFO] Loading anchor items...\n")

anchors <- dbGetQuery(pg, "
  SELECT 
    i.id, 
    c.model, 
    c.a, 
    c.b, 
    c.c 
  FROM shared_irt.items i
  JOIN shared_irt.item_parameters_current c ON c.item_id = i.id
  WHERE i.is_anchor = TRUE
    AND i.id = ANY($1)
", params = list(eligible_items))

if (nrow(anchors) > 0) {
  cat(sprintf("[INFO] Found %d anchor items with current parameters\n", nrow(anchors)))
} else {
  cat("[WARN] No anchor items found - all items will use default priors\n")
}

# ==============================================================================
# Specify Bayesian 2PL Model
# ==============================================================================
cat("[INFO] Specifying brms 2PL model...\n")

# Hierarchical 2PL formula
# y ~ inv_logit(discrimination * (ability - difficulty))
# Random effects:
#   (1|u|user) : user ability (theta)
#   (1|i|item) : item difficulty (b)
#   (1|a|item) : item discrimination (a) - varying intercept approximation

bf_formula <- bf(
  y ~ 1 + (1|u|user) + (1|i|item) + (1|a|item), 
  family = bernoulli(link = "logit")
)

# Default priors
priors <- c(
  # User ability: theta ~ N(0, 1)
  set_prior("normal(0, 1)", class = "sd", group = "u"),
  
  # Item discrimination: log(a) ~ N(0, 0.2)
  set_prior("normal(0, 0.2)", class = "sd", group = "a"),
  
  # Item difficulty: b ~ N(0, 1)
  set_prior("normal(0, 1)", class = "sd", group = "i")
)

# Anchor item priors (informative to stabilize parameters)
if (nrow(anchors) > 0) {
  cat("[INFO] Setting informative priors for anchor items...\n")
  
  for (i in seq_len(nrow(anchors))) {
    anchor_id <- anchors$id[i]
    anchor_a <- anchors$a[i]
    anchor_b <- anchors$b[i]
    
    # Tight priors around previous parameters (SD = 0.05)
    if (!is.na(anchor_a)) {
      priors <- c(priors,
        set_prior(
          sprintf("normal(%f, 0.05)", log(anchor_a)), 
          class = "sd", 
          group = "a", 
          coef = sprintf("item%d", anchor_id)
        )
      )
    }
    
    if (!is.na(anchor_b)) {
      priors <- c(priors,
        set_prior(
          sprintf("normal(%f, 0.05)", anchor_b), 
          class = "sd", 
          group = "i", 
          coef = sprintf("item%d", anchor_id)
        )
      )
    }
  }
}

# ==============================================================================
# Fit Model
# ==============================================================================
cat(sprintf("[INFO] Fitting brms model (iter=%d, warmup=%d, chains=%d)...\n",
            args$iter, args$warmup, args$chains))
cat("[INFO] This may take 10-30 minutes depending on data size...\n")

fit <- tryCatch({
  brm(
    formula = bf_formula,
    data = dat,
    prior = priors,
    iter = args$iter,
    warmup = args$warmup,
    chains = args$chains,
    cores = args$cores,
    backend = "cmdstanr",
    seed = 42,
    file = sprintf("brms_fit_window_%d", win_id),  # Cache results
    file_refit = "on_change"
  )
}, error = function(e) {
  stop(paste("Model fitting failed:", e$message))
})

cat("[INFO] Model fitting complete\n")

# ==============================================================================
# Extract Item Parameters
# ==============================================================================
cat("[INFO] Extracting item parameters...\n")

# Get random effects
re <- ranef(fit)

# Extract discrimination (a) and difficulty (b) for each item
item_params <- data.frame(
  item_id = as.integer(gsub("item", "", rownames(re$item))),
  stringsAsFactors = FALSE
)

# Difficulty (b) - from random effect "i"
if ("i" %in% colnames(re$item)) {
  item_params$b_hat <- re$item[, "i", "Estimate"]
  item_params$b_ci_low <- re$item[, "i", "Q2.5"]
  item_params$b_ci_high <- re$item[, "i", "Q97.5"]
} else {
  item_params$b_hat <- 0
  item_params$b_ci_low <- NA
  item_params$b_ci_high <- NA
}

# Discrimination (a) - from random effect "a" (on log scale)
if ("a" %in% colnames(re$item)) {
  item_params$a_hat <- exp(re$item[, "a", "Estimate"])  # Back-transform from log
  item_params$a_ci_low <- exp(re$item[, "a", "Q2.5"])
  item_params$a_ci_high <- exp(re$item[, "a", "Q97.5"])
} else {
  item_params$a_hat <- 1.0
  item_params$a_ci_low <- NA
  item_params$a_ci_high <- NA
}

# Guessing (c) - not estimated in 2PL, set to NULL
item_params$c_hat <- NA_real_
item_params$c_ci_low <- NA_real_
item_params$c_ci_high <- NA_real_

# Add response counts
item_params <- item_params %>%
  left_join(resp_counts, by = "item_id")

# Model log-likelihood
loglik_total <- sum(log_lik(fit))

cat(sprintf("[INFO] Extracted parameters for %d items\n", nrow(item_params)))
cat(sprintf("[INFO] Model log-likelihood: %.2f\n", loglik_total))

# ==============================================================================
# Load Baseline Parameters for Drift Detection
# ==============================================================================
cat("[INFO] Loading baseline parameters for drift detection...\n")

baseline <- dbGetQuery(pg, "
  SELECT item_id, model, a, b, c 
  FROM shared_irt.item_parameters_current
  WHERE item_id = ANY($1)
", params = list(item_params$item_id))

if (nrow(baseline) == 0) {
  cat("[WARN] No baseline parameters found - skipping drift detection\n")
  baseline <- data.frame(item_id = integer(), a = numeric(), b = numeric())
}

# Merge with current estimates
item_params <- item_params %>%
  left_join(
    baseline %>% select(item_id, a_prev = a, b_prev = b),
    by = "item_id"
  ) %>%
  mutate(
    delta_b = ifelse(!is.na(b_prev), b_hat - b_prev, NA_real_),
    delta_a = ifelse(!is.na(a_prev), a_hat - a_prev, NA_real_)
  )

# ==============================================================================
# Store Calibration Results
# ==============================================================================
cat("[INFO] Storing calibration results...\n")

dbBegin(pg)

tryCatch({
  for (i in seq_len(nrow(item_params))) {
    row <- item_params[i, ]
    
    dbExecute(pg, "
      INSERT INTO shared_irt.item_calibration (
        item_id, window_id, model, 
        a_hat, b_hat, c_hat,
        a_ci_low, a_ci_high, b_ci_low, b_ci_high,
        n_responses, loglik
      )
      VALUES ($1, $2, '2PL', $3, $4, $5, $6, $7, $8, $9, $10, $11)
      ON CONFLICT (item_id, window_id) DO UPDATE SET
        a_hat = EXCLUDED.a_hat,
        b_hat = EXCLUDED.b_hat,
        a_ci_low = EXCLUDED.a_ci_low,
        a_ci_high = EXCLUDED.a_ci_high,
        b_ci_low = EXCLUDED.b_ci_low,
        b_ci_high = EXCLUDED.b_ci_high,
        n_responses = EXCLUDED.n_responses,
        loglik = EXCLUDED.loglik,
        created_at = now()
    ", params = list(
      row$item_id, win_id,
      row$a_hat, row$b_hat, row$c_hat,
      row$a_ci_low, row$a_ci_high, row$b_ci_low, row$b_ci_high,
      row$n_responses, loglik_total
    ))
  }
  
  dbCommit(pg)
  cat(sprintf("[INFO] Stored %d calibration results\n", nrow(item_params)))
  
}, error = function(e) {
  dbRollback(pg)
  stop(paste("Failed to store results:", e$message))
})

# ==============================================================================
# Drift Detection and Alerts
# ==============================================================================
cat("[INFO] Detecting parameter drift...\n")

drift_count <- 0

dbBegin(pg)

tryCatch({
  for (i in seq_len(nrow(item_params))) {
    row <- item_params[i, ]
    
    # Check difficulty drift (Δb)
    if (!is.na(row$delta_b) && abs(row$delta_b) > args$drift_threshold_b) {
      severity <- ifelse(abs(row$delta_b) > 0.5, "high", "medium")
      message <- sprintf("Item %d: Δb = %+.3f (current: %.3f, previous: %.3f)",
                        row$item_id, row$delta_b, row$b_hat, row$b_prev)
      
      dbExecute(pg, "
        INSERT INTO shared_irt.drift_alerts (
          item_id, window_id, metric, value, threshold, severity, message
        )
        VALUES ($1, $2, 'Δb', $3, $4, $5, $6)
      ", params = list(
        row$item_id, win_id, row$delta_b, args$drift_threshold_b, severity, message
      ))
      
      drift_count <- drift_count + 1
    }
    
    # Check discrimination drift (Δa)
    if (!is.na(row$delta_a) && abs(row$delta_a) > args$drift_threshold_a) {
      severity <- ifelse(abs(row$delta_a) > 0.4, "high", "medium")
      message <- sprintf("Item %d: Δa = %+.3f (current: %.3f, previous: %.3f)",
                        row$item_id, row$delta_a, row$a_hat, row$a_prev)
      
      dbExecute(pg, "
        INSERT INTO shared_irt.drift_alerts (
          item_id, window_id, metric, value, threshold, severity, message
        )
        VALUES ($1, $2, 'Δa', $3, $4, $5, $6)
      ", params = list(
        row$item_id, win_id, row$delta_a, args$drift_threshold_a, severity, message
      ))
      
      drift_count <- drift_count + 1
    }
  }
  
  dbCommit(pg)
  
  if (drift_count > 0) {
    cat(sprintf("[WARN] Detected %d drift alerts\n", drift_count))
  } else {
    cat("[INFO] No significant drift detected ✓\n")
  }
  
}, error = function(e) {
  dbRollback(pg)
  stop(paste("Failed to create drift alerts:", e$message))
})

# ==============================================================================
# Update Current Parameters (non-drifted items)
# ==============================================================================
cat("[INFO] Updating current parameters for stable items...\n")

stable_items <- item_params %>%
  filter(
    (is.na(delta_b) | abs(delta_b) <= args$drift_threshold_b) &
    (is.na(delta_a) | abs(delta_a) <= args$drift_threshold_a)
  )

dbBegin(pg)

tryCatch({
  for (i in seq_len(nrow(stable_items))) {
    row <- stable_items[i, ]
    
    dbExecute(pg, "
      INSERT INTO shared_irt.item_parameters_current (
        item_id, model, a, b, c, 
        a_se, b_se,
        version, effective_from
      )
      VALUES ($1, '2PL', $2, $3, $4, $5, $6, 
              COALESCE((SELECT version FROM shared_irt.item_parameters_current WHERE item_id = $1), 0) + 1,
              now())
      ON CONFLICT (item_id) DO UPDATE SET
        a = EXCLUDED.a,
        b = EXCLUDED.b,
        a_se = EXCLUDED.a_se,
        b_se = EXCLUDED.b_se,
        version = EXCLUDED.version,
        effective_from = EXCLUDED.effective_from,
        updated_at = now()
    ", params = list(
      row$item_id,
      row$a_hat, row$b_hat, row$c_hat,
      (row$a_ci_high - row$a_ci_low) / 3.92,  # Approximate SE from 95% CI
      (row$b_ci_high - row$b_ci_low) / 3.92
    ))
  }
  
  dbCommit(pg)
  cat(sprintf("[INFO] Updated parameters for %d stable items\n", nrow(stable_items)))
  
}, error = function(e) {
  dbRollback(pg)
  stop(paste("Failed to update current parameters:", e$message))
})

# ==============================================================================
# Cleanup
# ==============================================================================
dbDisconnect(pg)

cat("[INFO] Calibration complete ✓\n")
cat(sprintf("[INFO] Window: %d\n", win_id))
cat(sprintf("[INFO] Items calibrated: %d\n", nrow(item_params)))
cat(sprintf("[INFO] Drift alerts: %d\n", drift_count))
cat(sprintf("[INFO] Stable items updated: %d\n", nrow(stable_items)))
