#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(DBI)
  library(RPostgres)
  library(glue)
})

log <- function(...) {
  ts <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  message(sprintf("[%s] %s", ts, paste0(..., collapse = "")))
}

get_target_date <- function() {
  td <- Sys.getenv("TARGET_DATE", unset = "")
  if (nzchar(td)) return(as.Date(td))
  as.Date(Sys.Date() - 1L) # default: yesterday
}

main <- function() {
  db_url <- Sys.getenv("DATABASE_URL", unset = "")
  if (!nzchar(db_url)) {
    stop("DATABASE_URL is not set")
  }

  # RPostgres/libpq accepts a connection URI in 'dbname'
  con <- dbConnect(RPostgres::Postgres(), dbname = db_url)
  on.exit({ try(DBI::dbDisconnect(con), silent = TRUE) }, add = TRUE)

  target_date <- get_target_date()
  d0 <- sprintf("%s 00:00:00+00", as.character(target_date))
  d1 <- sprintf("%s 00:00:00+00", as.character(target_date + 1L))

  log("Aggregate features_topic_daily for date=", as.character(target_date))

  sql <- glue::glue('
    INSERT INTO features_topic_daily
      (user_id, topic_id, date, attempts, correct, avg_time_ms, hints,
       rt_median, last_seen_at, computed_at)
    SELECT
      student_id::text AS user_id,
      topic_id,
      DATE(completed_at) AS date,
      COUNT(*) AS attempts,
      SUM(CASE WHEN correct THEN 1 ELSE 0 END)::int AS correct,
      AVG(response_time_ms)::int AS avg_time_ms,
      SUM(CASE WHEN hint_used THEN 1 ELSE 0 END)::int AS hints,
      PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms)::int AS rt_median,
      NOW() AS last_seen_at,
      NOW() AS computed_at
    FROM attempt
    WHERE completed_at >= {DBI::dbQuoteString(con, d0)}
      AND completed_at <  {DBI::dbQuoteString(con, d1)}
      AND student_id IS NOT NULL AND topic_id IS NOT NULL
    GROUP BY 1,2,3
    ON CONFLICT (user_id, topic_id, date)
    DO UPDATE SET
      attempts = EXCLUDED.attempts,
      correct = EXCLUDED.correct,
      avg_time_ms = EXCLUDED.avg_time_ms,
      hints = EXCLUDED.hints,
      rt_median = EXCLUDED.rt_median,
      last_seen_at = NOW(),
      computed_at = NOW();
  ')

  n <- DBI::dbExecute(con, sql)
  log("UPSERT completed. Rows affected=", n)
}

tryCatch({
  main()
}, error = function(e) {
  message("[FATAL] ", conditionMessage(e))
  quit(status = 1L)
})
