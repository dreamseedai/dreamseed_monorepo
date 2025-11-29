#!/usr/bin/env Rscript
#
# R mirt Calibration Pipeline for DreamSeed IRT/CAT
#
# This script performs offline 3PL IRT calibration using the mirt package
# and writes results back to the PostgreSQL database.
#
# Workflow:
#   1. Load responses CSV from export_responses_for_calibration.py
#   2. Pivot to wide format (N students × J items)
#   3. Fit 3PL model: mod <- mirt(resp_mat, 1, itemtype="3PL")
#   4. Extract item parameters: coef(mod, IRTpars=TRUE)
#   5. Extract student abilities: fscores(mod, method="EAP")
#   6. Write item parameters to items table (a, b, c)
#   7. Write student abilities to irt_student_abilities table
#
# Requirements:
#   - R packages: tidyverse, mirt, RPostgres
#   - Environment variables: PGDATABASE, PGHOST, PGPORT, PGUSER, PGPASSWORD
#   - Optional: IRT_SUBJECT, IRT_EXAM_ID (for metadata)
#
# Usage:
#   # Set database credentials
#   export PGDATABASE=dreamseed_dev
#   export PGHOST=localhost
#   export PGPORT=5433
#   export PGUSER=dreamseed_user
#   export PGPASSWORD=your_password
#   export IRT_SUBJECT=math  # Optional
#   export IRT_EXAM_ID=550e8400-...  # Optional
#
#   # Run calibration
#   Rscript R/irt_calibrate_mpc.R
#
# Input:
#   - data/responses.csv (from export_responses_for_calibration.py)
#   - Format: user_id, item_id, u (0/1)
#
# Output:
#   - Updates items table: a_discrimination, b_difficulty, c_guessing
#   - Inserts into irt_student_abilities: user_id, subject, theta, theta_se
#   - Saves calibration summary to data/calibration_summary.txt
#
# Note:
#   This is an OFFLINE calibration pipeline. For online CAT, use the
#   Python EAP estimator (backend/app/services/irt_eap_estimator.py).

library(tidyverse)
library(mirt)
library(RPostgres)

# ============================================================================
# Configuration
# ============================================================================

# Database connection from environment variables
DB_CONFIG <- list(
  dbname = Sys.getenv("PGDATABASE", "dreamseed_dev"),
  host = Sys.getenv("PGHOST", "localhost"),
  port = as.integer(Sys.getenv("PGPORT", "5433")),
  user = Sys.getenv("PGUSER", "dreamseed_user"),
  password = Sys.getenv("PGPASSWORD", "")
)

# Optional metadata
IRT_SUBJECT <- Sys.getenv("IRT_SUBJECT", "")
IRT_EXAM_ID <- Sys.getenv("IRT_EXAM_ID", "")

# Input/output paths
INPUT_CSV <- "data/responses.csv"
OUTPUT_SUMMARY <- "data/calibration_summary.txt"

# Calibration settings
MIN_RESPONSES_PER_ITEM <- 30  # Minimum responses needed per item
MIN_RESPONSES_PER_USER <- 5   # Minimum responses needed per user

# ============================================================================
# Helper Functions
# ============================================================================

log_message <- function(msg) {
  cat(sprintf("[%s] %s\n", Sys.time(), msg))
}

log_error <- function(msg) {
  cat(sprintf("[ERROR %s] %s\n", Sys.time(), msg), file = stderr())
}

# ============================================================================
# Main Pipeline
# ============================================================================

main <- function() {
  log_message("🚀 Starting R mirt calibration pipeline")
  
  # -------------------------------------------------------------------------
  # Step 1: Load and validate data
  # -------------------------------------------------------------------------
  
  log_message("📂 Loading responses from CSV...")
  
  if (!file.exists(INPUT_CSV)) {
    log_error(sprintf("Input file not found: %s", INPUT_CSV))
    log_error("Run: python scripts/export_responses_for_calibration.py --subject math --out data/responses.csv")
    stop("Input file not found")
  }
  
  responses <- read_csv(INPUT_CSV, show_col_types = FALSE)
  log_message(sprintf("   Loaded %d responses", nrow(responses)))
  
  # Validate columns
  required_cols <- c("user_id", "item_id", "u")
  if (!all(required_cols %in% colnames(responses))) {
    log_error(sprintf("Missing required columns: %s", paste(required_cols, collapse=", ")))
    stop("Invalid CSV format")
  }
  
  # -------------------------------------------------------------------------
  # Step 2: Filter users/items by minimum responses
  # -------------------------------------------------------------------------
  
  log_message("🔍 Filtering by minimum response thresholds...")
  
  # Count responses per item
  item_counts <- responses %>%
    group_by(item_id) %>%
    summarize(n_responses = n(), .groups = "drop")
  
  valid_items <- item_counts %>%
    filter(n_responses >= MIN_RESPONSES_PER_ITEM) %>%
    pull(item_id)
  
  log_message(sprintf("   Items with >=%d responses: %d", MIN_RESPONSES_PER_ITEM, length(valid_items)))
  
  # Count responses per user
  user_counts <- responses %>%
    filter(item_id %in% valid_items) %>%
    group_by(user_id) %>%
    summarize(n_responses = n(), .groups = "drop")
  
  valid_users <- user_counts %>%
    filter(n_responses >= MIN_RESPONSES_PER_USER) %>%
    pull(user_id)
  
  log_message(sprintf("   Users with >=%d responses: %d", MIN_RESPONSES_PER_USER, length(valid_users)))
  
  # Filter to valid users/items
  responses_filtered <- responses %>%
    filter(user_id %in% valid_users, item_id %in% valid_items)
  
  log_message(sprintf("   Filtered responses: %d (%.1f%% of original)",
                     nrow(responses_filtered),
                     100 * nrow(responses_filtered) / nrow(responses)))
  
  # Check minimum data requirement
  if (nrow(responses_filtered) < 500) {
    log_error(sprintf("Only %d responses remain after filtering, need at least 500", nrow(responses_filtered)))
    stop("Insufficient data for calibration")
  }
  
  # -------------------------------------------------------------------------
  # Step 3: Pivot to wide format (response matrix)
  # -------------------------------------------------------------------------
  
  log_message("🔄 Converting to response matrix (wide format)...")
  
  resp_mat <- responses_filtered %>%
    select(user_id, item_id, u) %>%
    pivot_wider(
      names_from = item_id,
      values_from = u,
      values_fill = NA
    ) %>%
    column_to_rownames("user_id") %>%
    as.matrix()
  
  log_message(sprintf("   Response matrix: %d students × %d items", nrow(resp_mat), ncol(resp_mat)))
  
  # Calculate missingness
  missingness <- sum(is.na(resp_mat)) / (nrow(resp_mat) * ncol(resp_mat))
  log_message(sprintf("   Missingness: %.1f%%", 100 * missingness))
  
  # -------------------------------------------------------------------------
  # Step 4: Fit 3PL IRT model
  # -------------------------------------------------------------------------
  
  log_message("🧮 Fitting 3PL IRT model with mirt...")
  
  tryCatch({
    mod <- mirt(
      data = resp_mat,
      model = 1,  # Unidimensional
      itemtype = "3PL",
      verbose = TRUE
    )
    
    log_message("   ✅ Model converged successfully")
    
  }, error = function(e) {
    log_error(sprintf("Model fitting failed: %s", e$message))
    stop("mirt calibration failed")
  })
  
  # -------------------------------------------------------------------------
  # Step 5: Extract item parameters
  # -------------------------------------------------------------------------
  
  log_message("📊 Extracting item parameters...")
  
  item_pars <- coef(mod, IRTpars = TRUE, simplify = TRUE)$items
  item_pars_df <- as.data.frame(item_pars) %>%
    rownames_to_column("item_id") %>%
    rename(c = g) %>%  # mirt uses 'g' for guessing
    select(item_id, a, b, c)
  
  log_message(sprintf("   Extracted parameters for %d items", nrow(item_pars_df)))
  log_message(sprintf("   Mean a: %.3f (SD: %.3f)", mean(item_pars_df$a), sd(item_pars_df$a)))
  log_message(sprintf("   Mean b: %.3f (SD: %.3f)", mean(item_pars_df$b), sd(item_pars_df$b)))
  log_message(sprintf("   Mean c: %.3f (SD: %.3f)", mean(item_pars_df$c), sd(item_pars_df$c)))
  
  # -------------------------------------------------------------------------
  # Step 6: Extract student abilities (EAP)
  # -------------------------------------------------------------------------
  
  log_message("👤 Extracting student abilities (EAP)...")
  
  theta_scores <- fscores(mod, method = "EAP", full.scores = FALSE)
  theta_df <- as.data.frame(theta_scores) %>%
    rownames_to_column("user_id") %>%
    rename(theta = F1, theta_se = SE_F1) %>%
    select(user_id, theta, theta_se)
  
  log_message(sprintf("   Extracted abilities for %d students", nrow(theta_df)))
  log_message(sprintf("   Mean θ: %.3f (SD: %.3f)", mean(theta_df$theta), sd(theta_df$theta)))
  log_message(sprintf("   Mean SE: %.3f", mean(theta_df$theta_se)))
  
  # -------------------------------------------------------------------------
  # Step 7: Connect to database
  # -------------------------------------------------------------------------
  
  log_message("🔌 Connecting to PostgreSQL...")
  
  con <- tryCatch({
    dbConnect(
      Postgres(),
      dbname = DB_CONFIG$dbname,
      host = DB_CONFIG$host,
      port = DB_CONFIG$port,
      user = DB_CONFIG$user,
      password = DB_CONFIG$password
    )
  }, error = function(e) {
    log_error(sprintf("Database connection failed: %s", e$message))
    stop("Cannot connect to database")
  })
  
  on.exit(dbDisconnect(con))
  log_message("   ✅ Connected to database")
  
  # -------------------------------------------------------------------------
  # Step 8: Update items table
  # -------------------------------------------------------------------------
  
  log_message("💾 Writing item parameters to database...")
  
  n_updated <- 0
  for (i in 1:nrow(item_pars_df)) {
    item <- item_pars_df[i, ]
    
    sql <- sprintf(
      "UPDATE items SET a_discrimination = %f, b_difficulty = %f, c_guessing = %f WHERE id = '%s'",
      item$a, item$b, item$c, item$item_id
    )
    
    tryCatch({
      dbExecute(con, sql)
      n_updated <- n_updated + 1
    }, error = function(e) {
      log_error(sprintf("Failed to update item %s: %s", item$item_id, e$message))
    })
  }
  
  log_message(sprintf("   ✅ Updated %d items", n_updated))
  
  # -------------------------------------------------------------------------
  # Step 9: Insert student abilities
  # -------------------------------------------------------------------------
  
  log_message("💾 Writing student abilities to database...")
  
  # Add metadata columns
  theta_df <- theta_df %>%
    mutate(
      subject = ifelse(IRT_SUBJECT != "", IRT_SUBJECT, NA),
      exam_id = ifelse(IRT_EXAM_ID != "", IRT_EXAM_ID, NA),
      calibrated_at = Sys.time()
    )
  
  # Delete existing records for this subject/exam
  if (IRT_SUBJECT != "") {
    del_sql <- sprintf(
      "DELETE FROM irt_student_abilities WHERE subject = '%s'",
      IRT_SUBJECT
    )
    if (IRT_EXAM_ID != "") {
      del_sql <- sprintf("%s AND exam_id = '%s'", del_sql, IRT_EXAM_ID)
    }
    dbExecute(con, del_sql)
    log_message("   Deleted existing abilities for this subject/exam")
  }
  
  # Insert new records
  n_inserted <- 0
  for (i in 1:nrow(theta_df)) {
    student <- theta_df[i, ]
    
    sql <- sprintf(
      "INSERT INTO irt_student_abilities (user_id, subject, theta, theta_se, exam_id, calibrated_at) VALUES ('%s', %s, %f, %f, %s, '%s')",
      student$user_id,
      ifelse(is.na(student$subject), "NULL", sprintf("'%s'", student$subject)),
      student$theta,
      student$theta_se,
      ifelse(is.na(student$exam_id), "NULL", sprintf("'%s'", student$exam_id)),
      format(student$calibrated_at, "%Y-%m-%d %H:%M:%S")
    )
    
    tryCatch({
      dbExecute(con, sql)
      n_inserted <- n_inserted + 1
    }, error = function(e) {
      log_error(sprintf("Failed to insert student %s: %s", student$user_id, e$message))
    })
  }
  
  log_message(sprintf("   ✅ Inserted %d student abilities", n_inserted))
  
  # -------------------------------------------------------------------------
  # Step 10: Save calibration summary
  # -------------------------------------------------------------------------
  
  log_message("📄 Saving calibration summary...")
  
  summary_text <- paste0(
    "DreamSeed IRT Calibration Summary\n",
    "=================================\n\n",
    sprintf("Timestamp: %s\n", Sys.time()),
    sprintf("Subject: %s\n", ifelse(IRT_SUBJECT != "", IRT_SUBJECT, "ALL")),
    sprintf("Exam ID: %s\n\n", ifelse(IRT_EXAM_ID != "", IRT_EXAM_ID, "ALL")),
    "Data Statistics:\n",
    sprintf("  Total responses: %d\n", nrow(responses_filtered)),
    sprintf("  Students: %d\n", nrow(resp_mat)),
    sprintf("  Items: %d\n", ncol(resp_mat)),
    sprintf("  Missingness: %.1f%%\n\n", 100 * missingness),
    "Item Parameters (Mean ± SD):\n",
    sprintf("  Discrimination (a): %.3f ± %.3f\n", mean(item_pars_df$a), sd(item_pars_df$a)),
    sprintf("  Difficulty (b): %.3f ± %.3f\n", mean(item_pars_df$b), sd(item_pars_df$b)),
    sprintf("  Guessing (c): %.3f ± %.3f\n\n", mean(item_pars_df$c), sd(item_pars_df$c)),
    "Student Abilities (Mean ± SD):\n",
    sprintf("  Theta (θ): %.3f ± %.3f\n", mean(theta_df$theta), sd(theta_df$theta)),
    sprintf("  Standard Error: %.3f ± %.3f\n\n", mean(theta_df$theta_se), sd(theta_df$theta_se)),
    "Database Updates:\n",
    sprintf("  Items updated: %d\n", n_updated),
    sprintf("  Student abilities inserted: %d\n", n_inserted)
  )
  
  dir.create("data", showWarnings = FALSE)
  writeLines(summary_text, OUTPUT_SUMMARY)
  log_message(sprintf("   ✅ Saved summary to %s", OUTPUT_SUMMARY))
  
  # -------------------------------------------------------------------------
  # Done
  # -------------------------------------------------------------------------
  
  log_message("✅ Calibration pipeline completed successfully!")
  log_message(sprintf("   Updated %d items, inserted %d student abilities", n_updated, n_inserted))
  
  cat("\n")
  cat(summary_text)
  cat("\n")
}

# ============================================================================
# Validate Environment
# ============================================================================

validate_environment <- function() {
  # Check required packages
  required_packages <- c("tidyverse", "mirt", "RPostgres")
  missing_packages <- required_packages[!sapply(required_packages, requireNamespace, quietly = TRUE)]
  
  if (length(missing_packages) > 0) {
    log_error(sprintf("Missing required packages: %s", paste(missing_packages, collapse = ", ")))
    log_error("Install with: install.packages(c('tidyverse', 'mirt', 'RPostgres'))")
    return(FALSE)
  }
  
  # Check database credentials
  if (DB_CONFIG$password == "") {
    log_error("PGPASSWORD environment variable not set")
    log_error("Set it with: export PGPASSWORD=your_password")
    return(FALSE)
  }
  
  return(TRUE)
}

# ============================================================================
# Execute
# ============================================================================

# Run main pipeline
if (!interactive()) {
  # Script is being run non-interactively (e.g., Rscript)
  if (!validate_environment()) {
    quit(status = 1)
  }
  
  tryCatch({
    main()
  }, error = function(e) {
    log_error(sprintf("Pipeline failed: %s", e$message))
    traceback()
    quit(status = 1)
  })
} else {
  # Script is being sourced in an interactive R session
  log_message("ℹ️  Script loaded in interactive mode. Run main() to start calibration.")
}
