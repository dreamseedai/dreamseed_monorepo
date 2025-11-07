#!/usr/bin/env Rscript
# Real-time ETL pipeline for Teacher Dashboard
# Syncs attendance and response stats from external systems

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(httr)
  library(jsonlite)
  library(lubridate)
})

# ---------------------------
# Configuration
# ---------------------------
DATASET_ROOT <- Sys.getenv("DATASET_ROOT", "data/datasets")
ATTENDANCE_API <- Sys.getenv("ATTENDANCE_API", "http://localhost:8000/api/attendance")
RESPONSE_API <- Sys.getenv("RESPONSE_API", "http://localhost:8000/api/response_stats")
ETL_INTERVAL_SECONDS <- as.numeric(Sys.getenv("ETL_INTERVAL", "300"))  # 5 minutes default
API_TIMEOUT_SECONDS <- as.numeric(Sys.getenv("API_TIMEOUT", "10"))

# Authentication headers (if needed)
get_auth_headers <- function() {
  token <- Sys.getenv("ETL_API_TOKEN", "")
  if (nzchar(token)) {
    add_headers(Authorization = paste("Bearer", token))
  } else {
    add_headers()
  }
}

# ---------------------------
# ETL Functions
# ---------------------------

#' Sync attendance data from external system
#' @param since ISO8601 timestamp
#' @return Number of records synced
sync_attendance <- function(since = NULL) {
  tryCatch({
    message("[ETL attendance] fetching from ", ATTENDANCE_API)
    
    # Build query params
    params <- list()
    if (!is.null(since)) params$since <- since
    
    # Call API
    response <- GET(
      ATTENDANCE_API,
      query = params,
      get_auth_headers(),
      timeout(API_TIMEOUT_SECONDS)
    )
    
    if (status_code(response) != 200) {
      warning("[ETL attendance] API returned status ", status_code(response))
      return(0)
    }
    
    # Parse response
    data <- content(response, as = "parsed", type = "application/json")
    
    if (length(data$records) == 0) {
      message("[ETL attendance] no new records")
      return(0)
    }
    
    # Convert to data frame
    df <- bind_rows(lapply(data$records, as.data.frame, stringsAsFactors = FALSE))
    
    # Ensure required columns
    required <- c("org_id", "class_id", "student_id", "date", "status")
    missing <- setdiff(required, names(df))
    if (length(missing) > 0) {
      stop("Missing required columns: ", paste(missing, collapse = ", "))
    }
    
    # Append to dataset
    path <- file.path(DATASET_ROOT, "attendance")
    
    if (dir.exists(path)) {
      # Read existing, deduplicate, and write
      existing <- open_dataset(path) %>% collect()
      combined <- bind_rows(existing, df) %>%
        distinct(org_id, class_id, student_id, date, .keep_all = TRUE)
      
      # Overwrite with combined data
      unlink(path, recursive = TRUE)
      write_dataset(combined, path = path, format = "parquet", partitioning = c("org_id", "class_id"))
    } else {
      # First sync
      write_dataset(df, path = path, format = "parquet", partitioning = c("org_id", "class_id"))
    }
    
    message("[ETL attendance] synced ", nrow(df), " records")
    return(nrow(df))
    
  }, error = function(e) {
    warning("[ETL attendance] error: ", e$message)
    return(0)
  })
}

#' Sync response stats from external system
#' @param since ISO8601 timestamp
#' @return Number of records synced
sync_response_stats <- function(since = NULL) {
  tryCatch({
    message("[ETL response_stats] fetching from ", RESPONSE_API)
    
    params <- list()
    if (!is.null(since)) params$since <- since
    
    response <- GET(
      RESPONSE_API,
      query = params,
      get_auth_headers(),
      timeout(API_TIMEOUT_SECONDS)
    )
    
    if (status_code(response) != 200) {
      warning("[ETL response_stats] API returned status ", status_code(response))
      return(0)
    }
    
    data <- content(response, as = "parsed", type = "application/json")
    
    if (length(data$records) == 0) {
      message("[ETL response_stats] no new records")
      return(0)
    }
    
    df <- bind_rows(lapply(data$records, as.data.frame, stringsAsFactors = FALSE))
    
    required <- c("org_id", "class_id", "student_id", "guess_like_rate", "omit_rate")
    missing <- setdiff(required, names(df))
    if (length(missing) > 0) {
      stop("Missing required columns: ", paste(missing, collapse = ", "))
    }
    
    # Ensure optional columns exist
    if (!"rapid_fire_rate" %in% names(df)) df$rapid_fire_rate <- 0
    if (!"avg_response_time" %in% names(df)) df$avg_response_time <- NA_real_
    
    path <- file.path(DATASET_ROOT, "response_stats")
    
    if (dir.exists(path)) {
      existing <- open_dataset(path) %>% collect()
      combined <- bind_rows(existing, df) %>%
        group_by(org_id, class_id, student_id) %>%
        arrange(desc(row_number())) %>%
        slice(1) %>%
        ungroup()
      
      unlink(path, recursive = TRUE)
      write_dataset(combined, path = path, format = "parquet", partitioning = c("org_id", "class_id"))
    } else {
      write_dataset(df, path = path, format = "parquet", partitioning = c("org_id", "class_id"))
    }
    
    message("[ETL response_stats] synced ", nrow(df), " records")
    return(nrow(df))
    
  }, error = function(e) {
    warning("[ETL response_stats] error: ", e$message)
    return(0)
  })
}

# ---------------------------
# Main Loop
# ---------------------------
run_etl_loop <- function() {
  message("=== Real-time ETL Pipeline Started ===")
  message("DATASET_ROOT: ", DATASET_ROOT)
  message("ATTENDANCE_API: ", ATTENDANCE_API)
  message("RESPONSE_API: ", RESPONSE_API)
  message("Interval: ", ETL_INTERVAL_SECONDS, " seconds")
  message("=========================================\n")
  
  last_sync <- Sys.time() - ETL_INTERVAL_SECONDS
  
  while (TRUE) {
    now <- Sys.time()
    elapsed <- as.numeric(difftime(now, last_sync, units = "secs"))
    
    if (elapsed >= ETL_INTERVAL_SECONDS) {
      message("\n[", format(now, "%Y-%m-%d %H:%M:%S"), "] Starting ETL sync...")
      
      # Sync with ISO8601 timestamp
      since_iso <- format(last_sync, "%Y-%m-%dT%H:%M:%SZ")
      
      att_count <- sync_attendance(since = since_iso)
      resp_count <- sync_response_stats(since = since_iso)
      
      message("[ETL] Total synced: attendance=", att_count, ", response_stats=", resp_count)
      
      last_sync <- now
    }
    
    Sys.sleep(min(10, ETL_INTERVAL_SECONDS / 2))  # Check interval (max 10s)
  }
}

# ---------------------------
# CLI
# ---------------------------
if (!interactive()) {
  run_etl_loop()
}
