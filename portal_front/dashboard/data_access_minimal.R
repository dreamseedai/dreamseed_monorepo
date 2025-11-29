# Minimal schema data access layer for Teacher Dashboard
# Supports Arrow (Parquet) or Postgres backends via env variables
# Tables: student, session, attendance, irt_snapshot, skill_mastery, risk_flag

suppressPackageStartupMessages({
  library(dplyr)
  library(arrow)
})

# Config
use_min_schema <- function() {
  tolower(Sys.getenv("USE_MIN_SCHEMA", "false")) %in% c("1","true","yes","on")
}

min_backend <- function() {
  t <- tolower(Sys.getenv("MIN_SCHEMA_BACKEND", "arrow"))
  if (t %in% c("db","postgres","pg")) return("db")
  "arrow"
}

# Arrow backend helpers -----------------------------------------------------
min_arrow_root <- function() {
  Sys.getenv("MIN_SCHEMA_ARROW_ROOT", file.path(getwd(), "data/min_schema"))
}

min_arrow_exists <- function() {
  root <- min_arrow_root()
  dirs <- file.path(root, c("student","session","attendance","irt_snapshot","skill_mastery"))
  all(dir.exists(dirs))
}

open_min_ds <- function(name) {
  arrow::open_dataset(file.path(min_arrow_root(), name), format = "parquet")
}

# DB backend helpers --------------------------------------------------------
min_db_con <- local({
  .con <- NULL
  function() {
    if (!is.null(.con) && inherits(.con, "DBIConnection")) return(.con)
    if (min_backend() != "db") return(NULL)
    suppressPackageStartupMessages({
      library(DBI)
      library(RPostgres)
      library(dbplyr)
    })
    dsn <- Sys.getenv("PG_DSN", "")
    if (nzchar(dsn)) {
      .con <<- DBI::dbConnect(RPostgres::Postgres(), dsn = dsn)
    } else {
      .con <<- DBI::dbConnect(
        RPostgres::Postgres(),
        host = Sys.getenv("PGHOST", "localhost"),
        port = as.integer(Sys.getenv("PGPORT", "5432")),
        dbname = Sys.getenv("PGDATABASE", "dreamseed"),
        user = Sys.getenv("PGUSER", "postgres"),
        password = Sys.getenv("PGPASSWORD", "")
      )
    }
    .con
  }
})

tbl_student <- function() {
  if (min_backend() == "db") return(dplyr::tbl(min_db_con(), "student"))
  open_min_ds("student")
}

tbl_session <- function() {
  if (min_backend() == "db") return(dplyr::tbl(min_db_con(), "session"))
  open_min_ds("session")
}

tbl_attendance <- function() {
  if (min_backend() == "db") return(dplyr::tbl(min_db_con(), "attendance"))
  open_min_ds("attendance")
}

tbl_irt_snapshot <- function() {
  if (min_backend() == "db") return(dplyr::tbl(min_db_con(), "irt_snapshot"))
  open_min_ds("irt_snapshot")
}

tbl_skill_mastery <- function() {
  if (min_backend() == "db") return(dplyr::tbl(min_db_con(), "skill_mastery"))
  open_min_ds("skill_mastery")
}

tbl_risk_flag <- function() {
  if (min_backend() == "db") return(dplyr::tbl(min_db_con(), "risk_flag"))
  root <- min_arrow_root()
  if (dir.exists(file.path(root, "risk_flag"))) return(open_min_ds("risk_flag"))
  NULL
}

# Derived sources -----------------------------------------------------------
# Classes index derived from student and/or session tables
tbl_classes_index <- function() {
  s <- tbl_student()
  # Use mode grade per class if available; else NA
  classes <- s %>%
    group_by(class_id) %>%
    summarise(
      class_name = dplyr::first(class_id),
      grade = suppressWarnings(as.character(dplyr::first(grade))),
      .groups = "drop"
    ) %>%
    mutate(
      country = "USA",
      subject = "math",
      subject_level = NA_character_
    )
  classes
}

# Attendance joined with session to get date and class_id
tbl_attendance_joined <- function() {
  a <- tbl_attendance()
  se <- tbl_session()
  a %>% inner_join(se, by = c("session_id" = "id")) %>%
    select(student_id, class_id, date, status)
}

# Response stats derived from latest irt_snapshot per student
tbl_response_stats <- function() {
  irt <- tbl_irt_snapshot()
  # latest week per student
  latest_w <- irt %>%
    group_by(student_id) %>%
    summarise(week_start = max(week_start, na.rm = TRUE), .groups = "drop")
  irt %>% inner_join(latest_w, by = c("student_id","week_start")) %>%
    transmute(
      student_id,
      guess_like_rate = coalesce(c_hat, 0),
      omit_rate = coalesce(omit_rate, 0),
      rapid_fire_rate = 0,
      avg_response_time = NA_real_
    )
}

# Skill weakness top3 string per student
tbl_skill_weakness <- function() {
  sm <- tbl_skill_mastery()
  # rank by mastery ascending per student, take top 3
  # For Arrow/DB compatibility, collect then compute grouping safely
  df <- sm %>% select(student_id, skill_tag, mastery) %>% collect()
  if (nrow(df) == 0) return(dplyr::tbl_df(tibble(student_id = character(), top3 = character())))
  top3 <- df %>%
    group_by(student_id) %>%
    arrange(mastery, .by_group = TRUE) %>%
    slice_head(n = 3) %>%
    summarise(top3 = paste(skill_tag, collapse = ", "), .groups = "drop")
  dplyr::tbl_df(top3)
}

message("[data_access_minimal.R] ✓ Loaded (backend=", min_backend(), ", use_min_schema=", use_min_schema(), ")")
