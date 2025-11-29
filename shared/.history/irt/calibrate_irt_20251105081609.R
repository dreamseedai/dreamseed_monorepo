#!/usr/bin/env Rscript
#' IRT Calibration and Drift Detection
#' =====================================
#' Fits 1PL/2PL/3PL models using mirt/ltm and detects parameter drift
#'
#' Usage:
#'   Rscript calibrate_irt.R \
#'     --input data/window_2025_10.csv \
#'     --model 2PL \
#'     --output results/window_2025_10_params.json \
#'     --previous results/window_2025_09_params.json

suppressPackageStartupMessages({
  library(mirt)
  library(ltm)
  library(jsonlite)
  library(dplyr)
  library(tidyr)
  library(optparse)
})

# ==============================================================================
# CLI Options
# ==============================================================================
option_list <- list(
  make_option(c("--input"), type="character", default=NULL,
              help="Input CSV file (user_id_hash, item_id, is_correct)", metavar="FILE"),
  make_option(c("--model"), type="character", default="2PL",
              help="IRT model: 1PL, 2PL, 3PL [default: %default]", metavar="MODEL"),
  make_option(c("--output"), type="character", default="irt_params.json",
              help="Output JSON file for parameters [default: %default]", metavar="FILE"),
  make_option(c("--previous"), type="character", default=NULL,
              help="Previous window params JSON for drift detection", metavar="FILE"),
  make_option(c("--drift-threshold-b"), type="numeric", default=0.3,
              help="Difficulty drift threshold (Δb) [default: %default]"),
  make_option(c("--drift-threshold-a"), type="numeric", default=0.5,
              help="Discrimination drift threshold (Δa) [default: %default]"),
  make_option(c("--min-responses"), type="integer", default=30,
              help="Minimum responses per item [default: %default]")
)

parser <- OptionParser(usage="%prog [options]", option_list=option_list,
                      description="IRT calibration with drift detection")
args <- parse_args(parser)

# Validate inputs
if (is.null(args$input)) {
  stop("Error: --input is required")
}

if (!file.exists(args$input)) {
  stop(paste("Error: Input file not found:", args$input))
}

cat(sprintf("[INFO] Loading data from: %s\n", args$input))
cat(sprintf("[INFO] Model: %s\n", args$model))
cat(sprintf("[INFO] Output: %s\n", args$output))

# ==============================================================================
# Load and Prepare Data
# ==============================================================================
responses_df <- read.csv(args$input, stringsAsFactors=FALSE)

# Validate columns
required_cols <- c("user_id_hash", "item_id", "is_correct")
if (!all(required_cols %in% colnames(responses_df))) {
  stop(paste("Error: Input CSV must have columns:", paste(required_cols, collapse=", ")))
}

# Convert to wide format (user × item matrix)
response_matrix <- responses_df %>%
  select(user_id_hash, item_id, is_correct) %>%
  pivot_wider(names_from=item_id, values_from=is_correct, 
              values_fn=list(is_correct=function(x) as.integer(tail(x, 1)))) %>%
  select(-user_id_hash) %>%
  as.data.frame()

# Convert to numeric matrix
response_matrix[is.na(response_matrix)] <- NA
response_matrix <- as.matrix(response_matrix)

cat(sprintf("[INFO] Response matrix: %d users × %d items\n", 
            nrow(response_matrix), ncol(response_matrix)))

# Filter items with insufficient responses
item_n <- colSums(!is.na(response_matrix))
valid_items <- which(item_n >= args$min_responses)

if (length(valid_items) < ncol(response_matrix)) {
  cat(sprintf("[WARN] Dropping %d items with < %d responses\n",
              ncol(response_matrix) - length(valid_items), args$min_responses))
  response_matrix <- response_matrix[, valid_items, drop=FALSE]
}

if (ncol(response_matrix) < 3) {
  stop("Error: Insufficient items for calibration (need >= 3)")
}

# ==============================================================================
# Fit IRT Model
# ==============================================================================
cat(sprintf("[INFO] Fitting %s model...\n", args$model))

fit <- tryCatch({
  if (args$model == "1PL") {
    mirt(response_matrix, model=1, itemtype="Rasch", verbose=FALSE)
  } else if (args$model == "2PL") {
    mirt(response_matrix, model=1, itemtype="2PL", verbose=FALSE)
  } else if (args$model == "3PL") {
    mirt(response_matrix, model=1, itemtype="3PL", verbose=FALSE)
  } else {
    stop(paste("Error: Unknown model:", args$model))
  }
}, error = function(e) {
  stop(paste("Error fitting model:", e$message))
})

cat("[INFO] Model fitting complete\n")

# ==============================================================================
# Extract Parameters
# ==============================================================================
coefs <- coef(fit, IRTpars=TRUE, simplify=TRUE)
item_params <- as.data.frame(coefs$items)

# Add item IDs
item_params$item_id <- as.integer(colnames(response_matrix))

# Add sample sizes
item_params$n_responses <- colSums(!is.na(response_matrix))

# Rename columns to standard notation
if (args$model == "1PL") {
  item_params <- item_params %>%
    rename(b = b, a = a) %>%
    mutate(c = NA_real_, model = "1PL")
} else if (args$model == "2PL") {
  item_params <- item_params %>%
    rename(a = a, b = b) %>%
    mutate(c = NA_real_, model = "2PL")
} else if (args$model == "3PL") {
  item_params <- item_params %>%
    rename(a = a, b = b, c = g) %>%
    mutate(model = "3PL")
}

# Model fit statistics
model_fit <- M2(fit, type="C2", calcNull=FALSE)
loglik <- logLik(fit)

cat(sprintf("[INFO] Model log-likelihood: %.2f\n", loglik))
cat(sprintf("[INFO] M2 statistic: %.2f (df=%d, p=%.4f)\n",
            model_fit$M2, model_fit$df, model_fit$p)))

# ==============================================================================
# Drift Detection (if previous params provided)
# ==============================================================================
drift_flags <- rep(NA_character_, nrow(item_params))

if (!is.null(args$previous) && file.exists(args$previous)) {
  cat(sprintf("[INFO] Loading previous params from: %s\n", args$previous))
  
  prev_data <- fromJSON(args$previous)
  prev_params <- prev_data$parameters %>%
    select(item_id, a_prev=a, b_prev=b, c_prev=c)
  
  # Merge with current params
  item_params <- item_params %>%
    left_join(prev_params, by="item_id")
  
  # Calculate drift metrics
  item_params <- item_params %>%
    mutate(
      delta_b = ifelse(!is.na(b_prev), b - b_prev, NA_real_),
      delta_a = ifelse(!is.na(a_prev) & !is.na(a), a - a_prev, NA_real_),
      delta_c = ifelse(!is.na(c_prev) & !is.na(c), c - c_prev, NA_real_)
    )
  
  # Flag drift
  drift_flags <- case_when(
    !is.na(item_params$delta_b) & abs(item_params$delta_b) > args$drift_threshold_b ~ "b",
    !is.na(item_params$delta_a) & abs(item_params$delta_a) > args$drift_threshold_a ~ "a",
    TRUE ~ NA_character_
  )
  
  n_drift <- sum(!is.na(drift_flags))
  if (n_drift > 0) {
    cat(sprintf("[WARN] Detected %d items with parameter drift\n", n_drift))
  } else {
    cat("[INFO] No significant parameter drift detected\n")
  }
}

item_params$drift_flag <- drift_flags

# ==============================================================================
# Compute Information Curves (for INFO drift detection)
# ==============================================================================
theta_seq <- seq(-4, 4, length.out=81)
info_matrix <- testinfo(fit, Theta=matrix(theta_seq, ncol=1))

# Peak information location for each item
item_info <- lapply(1:ncol(response_matrix), function(i) {
  info_i <- iteminfo(extract.item(fit, i), Theta=matrix(theta_seq, ncol=1))
  peak_theta <- theta_seq[which.max(info_i)]
  peak_info <- max(info_i)
  list(peak_theta=peak_theta, peak_info=peak_info)
})

item_params$info_peak_theta <- sapply(item_info, function(x) x$peak_theta)
item_params$info_peak_value <- sapply(item_info, function(x) x$peak_info)

# ==============================================================================
# Output Results
# ==============================================================================
output_data <- list(
  model = args$model,
  loglik = as.numeric(loglik),
  n_items = nrow(item_params),
  n_users = nrow(response_matrix),
  fit_statistics = list(
    M2 = model_fit$M2,
    df = model_fit$df,
    p = model_fit$p,
    RMSEA = model_fit$RMSEA,
    CFI = model_fit$CFI,
    TLI = model_fit$TLI
  ),
  parameters = item_params %>%
    select(item_id, model, a, b, c, n_responses, 
           info_peak_theta, info_peak_value, drift_flag,
           starts_with("delta_")) %>%
    mutate(across(where(is.numeric), ~round(., 4)))
)

# Write JSON
write_json(output_data, args$output, pretty=TRUE, auto_unbox=TRUE)

cat(sprintf("[INFO] Results written to: %s\n", args$output))
cat("[INFO] Calibration complete ✓\n")
