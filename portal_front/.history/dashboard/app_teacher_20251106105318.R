# Teacher-focused Class Monitor Dashboard (Shiny)
# Goal: enable a teacher to decide where to intervene within 1 minute
# Screen: Class snapshot + risk alerts (low improvement, attendance irregular) + group theta histogram + student drilldown

suppressPackageStartupMessages({
  library(shiny)
  library(shinydashboard)
  library(DT)
  library(arrow)
  library(dplyr)
  library(plotly)
  library(lubridate)
  library(stringr)
  library(tidyr)
  library(tibble)
  library(httr)
  library(yaml)
})

options(arrow.use_threads = TRUE)

`%||%` <- function(x, y) if (is.null(x) || length(x) == 0 || is.na(x) || identical(x, "")) y else x

# ---------------------------
# Risk thresholds (configurable via env vars)
# ---------------------------
RISK_THETA_DELTA_THRESHOLD <- as.numeric(Sys.getenv("RISK_THETA_DELTA", "0.02"))
RISK_ATTENDANCE_THRESHOLD <- as.numeric(Sys.getenv("RISK_ATTENDANCE", "0.25"))
RISK_GUESS_THRESHOLD <- as.numeric(Sys.getenv("RISK_GUESS", "0.15"))
RISK_OMIT_THRESHOLD <- as.numeric(Sys.getenv("RISK_OMIT", "0.12"))

# Assignment API endpoint
ASSIGNMENT_API_URL <- Sys.getenv("ASSIGNMENT_API_URL", "http://localhost:8000/api/assignments")

# ---------------------------
# Load assignment templates from YAML config
# ---------------------------
load_config <- function(config_path = "config/assignment_templates.yaml") {
  if (!file.exists(config_path)) {
    warning("[load_config] Config file not found: ", config_path, ". Using defaults.")
    return(list(
      templates = list(
        very_low = list(template_id = "remedial_basics", catalog_ids = list("MATH-1A", "MATH-1B")),
        low = list(template_id = "supplementary_review", catalog_ids = list("MATH-2A", "MATH-2B")),
        mid = list(template_id = "core_practice", catalog_ids = list("MATH-3A", "MATH-3B")),
        high = list(template_id = "challenge_advanced", catalog_ids = list("MATH-4A", "MATH-4B")),
        very_high = list(template_id = "enrichment_extension", catalog_ids = list("MATH-5A", "MATH-5B"))
      ),
      permissions = list(
        admin = list(can_assign = TRUE, can_view_all_classes = TRUE, can_modify_thresholds = TRUE),
        teacher = list(can_assign = TRUE, can_view_all_classes = FALSE, can_modify_thresholds = FALSE),
        counselor = list(can_assign = FALSE, can_view_all_classes = TRUE, can_modify_thresholds = FALSE),
        viewer = list(can_assign = FALSE, can_view_all_classes = FALSE, can_modify_thresholds = FALSE)
      )
    ))
  }
  tryCatch({
    yaml::yaml.load_file(config_path)
  }, error = function(e) {
    warning("[load_config] Failed to load YAML: ", e$message)
    return(NULL)
  })
}

CONFIG <- load_config()
ASSIGNMENT_TEMPLATES <- CONFIG$templates %||% list()
ROLE_PERMISSIONS <- CONFIG$permissions %||% list()


# ---------------------------
# Assignment API helper
# ---------------------------
call_assignment_api <- function(student_ids, template, claims, auth_bearer = NULL) {
  tryCatch({
    payload <- list(
      student_ids = as.list(student_ids),
      template = template,
      assigned_by = claims$user,
      org_id = claims$org_id,
      timestamp = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ")
    )
    
    headers <- list(
      `Content-Type` = "application/json",
      `X-User` = claims$user,
      `X-Org-Id` = claims$org_id
    )
    if (!is.null(auth_bearer) && nzchar(auth_bearer)) {
      headers$Authorization <- auth_bearer
    }

    response <- httr::POST(
      ASSIGNMENT_API_URL,
      body = payload,
      encode = "json",
      httr::add_headers(.headers = headers),
      httr::timeout(5)
    )
    
    if (httr::status_code(response) == 200 || httr::status_code(response) == 201) {
      message("[assignment API] success: ", length(student_ids), " students, template=", template)
      return(TRUE)
    } else {
      warning("[assignment API] failed: status ", httr::status_code(response))
      return(FALSE)
    }
  }, error = function(e) {
    warning("[assignment API] error: ", e$message)
    return(FALSE)
  })
}

# ---------------------------
# Claims helpers (reverse-proxy injected headers) + IdP header mapping
# ---------------------------
canonicalize_roles <- function(raw_roles) {
  if (is.null(raw_roles) || length(raw_roles) == 0) return(character())
  rs <- tolower(trimws(raw_roles))
  canon <- character()
  if (any(grepl("admin|관리자|principal|교장|head", rs))) canon <- c(canon, "admin")
  if (any(grepl("teacher|교사|instructor|tutor", rs))) canon <- c(canon, "teacher")
  if (any(grepl("counsel|상담", rs))) canon <- c(canon, "counselor")
  if (any(grepl("viewer|read|analyst|조회", rs))) canon <- c(canon, "viewer")
  if (length(canon) == 0) canon <- unique(rs)
  unique(canon)
}

parse_claims <- function(session) {
  req <- session$request
  get_header <- function(name, default = "") {
    key <- paste0("HTTP_", toupper(gsub("-", "_", name)))
    req[[key]] %||% default
  }
  # Header name mapping via env (for existing IdP/proxy integration)
  H_USER   <- Sys.getenv("AUTH_HEADER_USER",   "X-User")
  H_ORG    <- Sys.getenv("AUTH_HEADER_ORG",    "X-Org-Id")
  H_ROLES  <- Sys.getenv("AUTH_HEADER_ROLES",  "X-Roles")
  H_GROUPS <- Sys.getenv("AUTH_HEADER_GROUPS", "X-Auth-Request-Groups")

  user_val <- get_header(H_USER) %||% get_header("X-Auth-Request-User") %||% Sys.getenv("DEV_USER", unset = "local_teacher")
  org_val  <- get_header(H_ORG)  %||% get_header("X-Org") %||% Sys.getenv("DEV_ORG_ID", unset = "org_001")
  roles_str <- get_header(H_ROLES)
  if (!nzchar(roles_str)) roles_str <- get_header(H_GROUPS)
  if (!nzchar(roles_str)) roles_str <- Sys.getenv("DEV_ROLES", unset = "teacher")
  raw_roles <- strsplit(roles_str, ",")[[1]] |> trimws()

  list(
    user = user_val,
    org_id = org_val,
    roles = canonicalize_roles(raw_roles),
    roles_raw = raw_roles
  )
}

has_role <- function(claims, role) role %in% (claims$roles %||% character())

filter_by_access <- function(ds, claims) {
  # Teachers/Admins: restrict to org; if teacher-specific constraints exist, apply here
  if (!is.null(claims$org_id) && nzchar(claims$org_id)) {
    ds <- ds %>% dplyr::filter(org_id == !!claims$org_id)
  } else {
    ds <- ds %>% dplyr::filter(FALSE)
  }
  ds
}

# ---------------------------
# Bootstrap demo datasets (if absent)
# ---------------------------
init_datasets <- function() {
  base <- Sys.getenv("DATASET_ROOT", unset = file.path(getwd(), "data/datasets"))
  dir.create(base, recursive = TRUE, showWarnings = FALSE)

  ensure_dataset <- function(name, gen_fun) {
    path <- file.path(base, name)
    if (!dir.exists(path) || length(list.files(path, recursive = TRUE, pattern = "*.parquet$")) == 0) {
      dir.create(path, recursive = TRUE, showWarnings = FALSE)
      message("[bootstrap] generating demo dataset: ", name)
      df <- gen_fun()
      part_cols <- intersect(c("org_id", "class_id"), names(df))
      write_dataset(df, path = path, format = "parquet", partitioning = part_cols)
    }
    invisible(path)
  }

  set.seed(2025)

  # Classes
  ensure_dataset("classes", function() {
    orgs <- paste0("org_", sprintf("%03d", 1:10))
    classes <- tibble(
      org_id = rep(orgs, each = 10),
      class_id = paste0("CLS", sprintf("%04d", 1:(length(orgs)*10))),
      class_name = paste("Class", 1:(length(orgs)*10))
    )
    classes
  })

  # Students
  ensure_dataset("students", function() {
    classes <- arrow::open_dataset(file.path(base, "classes")) %>% collect()
    students <- classes %>% group_by(org_id, class_id, class_name) %>%
      do({
        n <- 30
        tibble(
          student_id = paste0("STD", sample(100000:999999, n, replace = FALSE)),
          student_name = paste("S", sample(1000:9999, n))
        )
      }) %>% ungroup()
    students
  })

  # Student theta time-series (last 90 days)
  ensure_dataset("student_theta", function() {
    students <- arrow::open_dataset(file.path(base, "students")) %>% collect()
    dates <- seq.Date(Sys.Date()-89, Sys.Date(), by = "day")
    students %>% group_by(org_id, class_id, student_id) %>% do({
      base_theta <- rnorm(1, 0, 0.6)
      noise <- cumsum(rnorm(length(dates), 0, 0.03))
      tibble(date = dates, theta = pmax(pmin(base_theta + noise, 3), -3))
    }) %>% ungroup()
  })

  # Attendance events (last 90 days)
  ensure_dataset("attendance", function() {
    students <- arrow::open_dataset(file.path(base, "students")) %>% collect()
    dates <- seq.Date(Sys.Date()-89, Sys.Date(), by = "day")
    students %>% group_by(org_id, class_id, student_id) %>% do({
      p_abs <- runif(1, 0.03, 0.10)
      p_tardy <- runif(1, 0.05, 0.15)
      status <- sample(c("present","tardy","absent"), length(dates), replace = TRUE,
                       prob = c(1-p_abs-p_tardy, p_tardy, p_abs))
      tibble(date = dates, status = status)
    }) %>% ungroup()
  })

  # Skill weaknesses (top3 tags per student)
  ensure_dataset("skill_weakness", function() {
    tag_pool <- c("인수분해","지수법칙","방정식","도형의 성질","확률","함수","부등식","미분","적분","벡터")
    students <- arrow::open_dataset(file.path(base, "students")) %>% collect()
    students %>% rowwise() %>% mutate(
      top3 = paste(sample(tag_pool, 3), collapse = ", ")
    ) %>% ungroup()
  })

  # Response anomaly stats (per student)
  ensure_dataset("response_stats", function() {
    students <- arrow::open_dataset(file.path(base, "students")) %>% collect()
    students %>% mutate(
      guess_like_rate = pmax(0, rnorm(n(), 0.08, 0.05)),
      omit_rate = pmax(0, rnorm(n(), 0.06, 0.04)),
      rapid_fire_rate = pmax(0, rnorm(n(), 0.05, 0.03)),
      avg_response_time = pmax(5, rnorm(n(), 45, 20))
    )
  })

  # Item-level response patterns (for heatmap)
  ensure_dataset("item_response_patterns", function() {
    students <- arrow::open_dataset(file.path(base, "students")) %>% collect()
    item_pool <- paste0("Q", sprintf("%04d", 1:100))
    students %>% group_by(org_id, class_id) %>% do({
      n_items <- 30
      items <- sample(item_pool, n_items)
      expand.grid(student_id = .$student_id, item_id = items, stringsAsFactors = FALSE) %>%
        mutate(
          guess_flag = runif(n()) < 0.10,
          omit_flag = runif(n()) < 0.08,
          rapid_flag = runif(n()) < 0.06
        )
    }) %>% ungroup()
  })

  base
}

open_ds <- function(base, name) {
  arrow::open_dataset(file.path(base, name), format = "parquet")
}

# ---------------------------
# UI
# ---------------------------
ui <- dashboardPage(
  skin = "purple",
  dashboardHeader(title = "Class Monitor", tags$li(class = "dropdown", uiOutput("user_badge"))),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Class Monitor", tabName = "class", icon = icon("chalkboard"))
    )
  ),
  dashboardBody(
    tabItems(
      tabItem(tabName = "class",
        fluidRow(
          box(width = 12, status = "primary", solidHeader = TRUE, title = "Class Controls",
              fluidRow(
                column(4, uiOutput("class_picker")),
                column(4, dateRangeInput("class_dates", "Date range", start = Sys.Date()-27, end = Sys.Date())),
                column(4, helpText("목표: 1분 이내介入 결정을 위한 스냅샷 제공"),
                tags$small(sprintf("임계값: Δ7d<%.2f, 출석>%.0f%%, 추측>%.0f%%, 무응답>%.0f%%",
                                    RISK_THETA_DELTA_THRESHOLD, 100*RISK_ATTENDANCE_THRESHOLD, 100*RISK_GUESS_THRESHOLD, 100*RISK_OMIT_THRESHOLD)))
              )
          )
        ),
        fluidRow(
          valueBoxOutput("vb_theta_mean", width = 3),
          valueBoxOutput("vb_theta_median", width = 3),
          valueBoxOutput("vb_theta_p10p90", width = 3),
          valueBoxOutput("vb_theta_growth", width = 3)
        ),
        fluidRow(
          valueBoxOutput("vb_attendance", width = 3),
          valueBoxOutput("vb_risk_improve", width = 3),
          valueBoxOutput("vb_risk_attn", width = 3),
          valueBoxOutput("vb_risk_response", width = 3)
        ),
        fluidRow(
          box(width = 6, status = "primary", solidHeader = TRUE, title = "그룹 θ 히스토그램",
              plotlyOutput("theta_hist", height = 350),
              uiOutput("bucket_actions")
          ),
          box(width = 6, status = "primary", solidHeader = TRUE, title = "학생 목록 (드릴다운: 행 선택)",
              DTOutput("students_table")
          )
        ),
        fluidRow(
          box(width = 12, status = "warning", solidHeader = TRUE, collapsible = TRUE, collapsed = TRUE,
              title = "문항 반응 이상 패턴 세부 분석",
              fluidRow(
                valueBoxOutput("vb_pure_guess", width = 3),
                valueBoxOutput("vb_strategic_omit", width = 3),
                valueBoxOutput("vb_rapid_fire", width = 3),
                valueBoxOutput("vb_multi_pattern", width = 3)
              ),
              fluidRow(
                column(12,
                  h4("문항별 이상치 히트맵 (상위 20개 문항)"),
                  plotlyOutput("item_anomaly_heatmap", height = 400)
                )
              )
          )
        )
      )
    )
  )
)

# ---------------------------
# Server
# ---------------------------
server <- function(input, output, session) {
  base <- init_datasets()
  claims <- parse_claims(session)
  assignment_auth <- session$request$HTTP_AUTHORIZATION %||% Sys.getenv("ASSIGNMENT_API_BEARER", unset = "")

  output$user_badge <- renderUI({
    tags$span(style = "padding-right:12px;",
      tags$span(class = "label label-info", paste0("User: ", claims$user)), " ",
      tags$span(class = "label label-success", paste0("Org: ", claims$org_id)), " ",
      tags$span(class = "label label-default", paste0("Roles: ", paste(claims$roles, collapse=",")))
    )
  })

  classes_ds <- reactive({ filter_by_access(open_ds(base, "classes"), claims) })

  output$class_picker <- renderUI({
    cs <- classes_ds() %>% select(class_id, class_name) %>% collect()
    choices <- setNames(cs$class_id, paste0(cs$class_name, " (", cs$class_id, ")"))
    selectInput("class_id", "Class", choices = choices, selected = head(cs$class_id,1))
  })

  # Helper reactives for selected class and date range
  theta_ds <- reactive({ filter_by_access(open_ds(base, "student_theta"), claims) %>% filter(class_id == !!input$class_id) })
  students_ds <- reactive({ filter_by_access(open_ds(base, "students"), claims) %>% filter(class_id == !!input$class_id) })
  attend_ds <- reactive({ filter_by_access(open_ds(base, "attendance"), claims) %>% filter(class_id == !!input$class_id) })
  skill_ds <- reactive({ filter_by_access(open_ds(base, "skill_weakness"), claims) %>% filter(class_id == !!input$class_id) })
  resp_ds <- reactive({ filter_by_access(open_ds(base, "response_stats"), claims) %>% filter(class_id == !!input$class_id) })
  item_resp_ds <- reactive({ filter_by_access(open_ds(base, "item_response_patterns"), claims) %>% filter(class_id == !!input$class_id) })

  date_filter <- reactive({ req(input$class_dates); input$class_dates })

  # Bucket filter state (reactive value)
  bucket_filter <- reactiveVal(NULL)

  # Latest theta per student within range and deltas
  latest_theta_tbl <- reactive({
    req(input$class_id)
    dr <- date_filter()
    df <- theta_ds() %>% filter(date >= !!dr[1], date <= !!dr[2]) %>% collect()
    # latest and one-week-ago
    latest <- df %>% group_by(student_id) %>% filter(date == max(date)) %>% summarise(theta = first(theta), .groups='drop')
    week_ago_date <- max(df$date) - 7
    week_ago <- df %>% group_by(student_id) %>% filter(date <= !!week_ago_date) %>% filter(date == max(date)) %>% summarise(theta_7d = first(theta), .groups='drop')
    out <- latest %>% left_join(week_ago, by = "student_id") %>% mutate(delta_7d = theta - (theta_7d %||% theta))
    out
  })

  # Attendance metrics per student in range
  attn_metrics_tbl <- reactive({
    dr <- date_filter()
    adf <- attend_ds() %>% filter(date >= !!dr[1], date <= !!dr[2]) %>% collect()
    adf %>% mutate(
      is_abs = status == "absent",
      is_tardy = status == "tardy"
    ) %>% group_by(student_id) %>% summarise(
      days = n(),
      absences = sum(is_abs),
      tardies = sum(is_tardy),
      abs_rate = absences / pmax(days,1),
      tardy_rate = tardies / pmax(days,1),
      .groups='drop'
    )
  })

  # Class snapshot KPIs
  output$vb_theta_mean <- renderValueBox({
    lt <- latest_theta_tbl()
    valueBox(sprintf("%.2f", mean(lt$theta, na.rm = TRUE)), "평균 θ", icon = icon("gauge"), color = "aqua")
  })

  output$vb_theta_median <- renderValueBox({
    lt <- latest_theta_tbl()
    valueBox(sprintf("%.2f", median(lt$theta, na.rm = TRUE)), "중앙값 θ", icon = icon("minus"), color = "light-blue")
  })

  output$vb_theta_p10p90 <- renderValueBox({
    lt <- latest_theta_tbl()
    q <- quantile(lt$theta, probs = c(0.1, 0.9), na.rm = TRUE)
    valueBox(sprintf("%.2f ~ %.2f", q[[1]], q[[2]]), "상·하위 10% 구간", icon = icon("arrows-left-right"), color = "teal")
  })

  output$vb_theta_growth <- renderValueBox({
    dr <- date_filter()
    df <- theta_ds() %>% filter(date >= !!(dr[1]-14), date <= !!dr[2]) %>% collect()
    end_week <- df %>% filter(date > max(date)-7)
    prev_week <- df %>% filter(date <= max(date)-7, date > max(date)-14)
    g <- mean(end_week$theta, na.rm = TRUE) - mean(prev_week$theta, na.rm = TRUE)
    valueBox(sprintf("%+.2f", g), "주간 성장률 Δθ", icon = icon("chart-line"), color = if (is.na(g) || g >= 0) "green" else "yellow")
  })

  output$vb_attendance <- renderValueBox({
    am <- attn_metrics_tbl()
    abs_r <- mean(am$abs_rate, na.rm = TRUE)
    tardy_r <- mean(am$tardy_rate, na.rm = TRUE)
    valueBox(sprintf("결석 %.0f%% · 지각 %.0f%%", 100*abs_r, 100*tardy_r), "출석 안정도(평균)", icon = icon("calendar-check"), color = if ((abs_r + tardy_r) < 0.25) "green" else "yellow")
  })

  # Risk detection
  output$vb_risk_improve <- renderValueBox({
    lt <- latest_theta_tbl()
    low <- sum(lt$delta_7d < RISK_THETA_DELTA_THRESHOLD, na.rm = TRUE)
    total <- nrow(lt)
    valueBox(sprintf("%d명", low), paste0("리스크: 개선 저조(Δ7d<", RISK_THETA_DELTA_THRESHOLD, ")"), icon = icon("triangle-exclamation"), color = if (low/total > 0.3) "red" else if (low>0) "yellow" else "green")
  })

  output$vb_risk_attn <- renderValueBox({
    am <- attn_metrics_tbl()
    irregular <- sum((am$abs_rate + am$tardy_rate) > RISK_ATTENDANCE_THRESHOLD, na.rm = TRUE)
    total <- nrow(am)
    valueBox(sprintf("%d명", irregular), "리스크: 출석 불규칙", icon = icon("user-clock"), color = if (irregular/total > 0.2) "red" else if (irregular>0) "yellow" else "green")
  })

  output$vb_risk_response <- renderValueBox({
    rsp <- resp_ds() %>% collect()
    anomaly <- sum((rsp$guess_like_rate > RISK_GUESS_THRESHOLD) | (rsp$omit_rate > RISK_OMIT_THRESHOLD), na.rm = TRUE)
    total <- nrow(rsp)
    valueBox(sprintf("%d명", anomaly), "리스크: 문항 반응 이상", icon = icon("exclamation-circle"), color = if (anomaly/total > 0.15) "red" else if (anomaly>0) "yellow" else "green")
  })

  # Detailed response pattern analysis
  output$vb_pure_guess <- renderValueBox({
    rsp <- resp_ds() %>% collect()
    pure_guess <- sum(rsp$guess_like_rate > RISK_GUESS_THRESHOLD & rsp$omit_rate < 0.05, na.rm = TRUE)
    valueBox(sprintf("%d명", pure_guess), "Pure Guessing", icon = icon("dice"), color = if (pure_guess > 0) "red" else "green")
  })

  output$vb_strategic_omit <- renderValueBox({
    rsp <- resp_ds() %>% collect()
    strategic <- sum(rsp$omit_rate > RISK_OMIT_THRESHOLD & rsp$guess_like_rate < 0.05, na.rm = TRUE)
    valueBox(sprintf("%d명", strategic), "Strategic Omit", icon = icon("ban"), color = if (strategic > 0) "orange" else "green")
  })

  output$vb_rapid_fire <- renderValueBox({
    rsp <- resp_ds() %>% collect()
    rapid <- sum(rsp$rapid_fire_rate > 0.10 & rsp$avg_response_time < 20, na.rm = TRUE)
    valueBox(sprintf("%d명", rapid), "Rapid-Fire", icon = icon("bolt"), color = if (rapid > 0) "yellow" else "green")
  })

  output$vb_multi_pattern <- renderValueBox({
    rsp <- resp_ds() %>% collect()
    multi <- sum(
      (rsp$guess_like_rate > RISK_GUESS_THRESHOLD) & 
      (rsp$omit_rate > RISK_OMIT_THRESHOLD) &
      (rsp$rapid_fire_rate > 0.10),
      na.rm = TRUE
    )
    valueBox(sprintf("%d명", multi), "복합 이상 패턴", icon = icon("exclamation-triangle"), color = if (multi > 0) "red" else "green")
  })

  # Item-level anomaly heatmap
  output$item_anomaly_heatmap <- renderPlotly({
    item_resp <- item_resp_ds() %>% collect()
    if (nrow(item_resp) == 0) {
      plot_ly() %>% layout(title = "데이터 없음")
    } else {
      # Calculate anomaly rate per item
      item_anom <- item_resp %>%
        group_by(item_id) %>%
        summarise(
          guess_rate = mean(guess_flag, na.rm = TRUE),
          omit_rate = mean(omit_flag, na.rm = TRUE),
          rapid_rate = mean(rapid_flag, na.rm = TRUE),
          total_anom = mean(guess_flag | omit_flag | rapid_flag, na.rm = TRUE),
          .groups = 'drop'
        ) %>%
        arrange(desc(total_anom)) %>%
        head(20)
      
      # Pivot for heatmap
      heatmap_data <- item_anom %>%
        select(item_id, guess_rate, omit_rate, rapid_rate) %>%
        tidyr::pivot_longer(cols = c(guess_rate, omit_rate, rapid_rate), names_to = "pattern", values_to = "rate")
      
      plot_ly(heatmap_data, x = ~item_id, y = ~pattern, z = ~rate, type = "heatmap", colors = "Reds") %>%
        layout(
          xaxis = list(title = "문항 ID (이상률 상위 20개)"),
          yaxis = list(title = "이상 패턴"),
          title = "문항별 반응 이상치 분포"
        )
    }
  })

  # Histogram and bucket actions
  output$theta_hist <- renderPlotly({
    lt <- latest_theta_tbl()
    # Create color-coded histogram by buckets
    lt_buckets <- lt %>% mutate(
      bucket = case_when(
        theta <= -1.5 ~ "매우낮음(<=-1.5)",
        theta <= -0.5 ~ "낮음(-1.5~-0.5)",
        theta <= 0.5 ~ "중간(-0.5~0.5)",
        theta <= 1.5 ~ "높음(0.5~1.5)",
        TRUE ~ "매우높음(>1.5)"
      ),
      bucket = factor(bucket, levels = c("매우낮음(<=-1.5)", "낮음(-1.5~-0.5)", "중간(-0.5~0.5)", "높음(0.5~1.5)", "매우높음(>1.5)"))
    )
    plot_ly(lt_buckets, x = ~theta, color = ~bucket, colors = c("#d32f2f","#f57c00","#fbc02d","#689f38","#388e3c"), type = 'histogram', nbinsx = 24) %>%
      layout(xaxis = list(title = "θ"), yaxis = list(title = "학생 수"), barmode = "stack")
  })

  output$bucket_actions <- renderUI({
    lt <- latest_theta_tbl()
    counts <- lt %>% summarise(
      very_low = sum(theta <= -1.5, na.rm = TRUE),
      low = sum(theta > -1.5 & theta <= -0.5, na.rm = TRUE),
      mid = sum(theta > -0.5 & theta <= 0.5, na.rm = TRUE),
      high = sum(theta > 0.5 & theta <= 1.5, na.rm = TRUE),
      very_high = sum(theta > 1.5, na.rm = TRUE)
    )
    bf <- bucket_filter()
    tags$div(
      tags$h5("버킷별 추천 액션 (클릭하여 학생 필터 + 과제 배정)"),
      tags$div(style="margin-bottom:8px;",
        if (!is.null(bf)) actionButton("clear_filter", "필터 초기화", icon = icon("times"), style="margin:2px; background-color:#e74c3c; color:white;") else NULL
      ),
      actionButton("act_very_low", sprintf("매우낮음 %d명 → 보정 과제", counts$very_low), style=paste0("margin:2px;", if(!is.null(bf) && bf=="very_low") "background-color:#2980b9; color:white;" else "")),
      actionButton("act_low", sprintf("낮음 %d명 → 보충수업", counts$low), style=paste0("margin:2px;", if(!is.null(bf) && bf=="low") "background-color:#2980b9; color:white;" else "")),
      actionButton("act_mid", sprintf("중간 %d명 → 핵심 연습", counts$mid), style=paste0("margin:2px;", if(!is.null(bf) && bf=="mid") "background-color:#2980b9; color:white;" else "")),
      actionButton("act_high", sprintf("높음 %d명 → 상향 도전", counts$high), style=paste0("margin:2px;", if(!is.null(bf) && bf=="high") "background-color:#2980b9; color:white;" else "")),
      actionButton("act_very_high", sprintf("매우높음 %d명 → 심화/확장", counts$very_high), style=paste0("margin:2px;", if(!is.null(bf) && bf=="very_high") "background-color:#2980b9; color:white;" else ""))
    )
  })

  # Students table with drilldown
  students_tbl <- reactive({
    lt <- latest_theta_tbl()
    am <- attn_metrics_tbl()
    skills <- skill_ds() %>% select(student_id, top3) %>% collect()
    students <- students_ds() %>% select(student_id, student_name) %>% collect()
    rsp <- resp_ds() %>% select(student_id, guess_like_rate, omit_rate) %>% collect()

    combined <- lt %>%
      left_join(am, by = "student_id") %>%
      left_join(skills, by = "student_id") %>%
      left_join(students, by = "student_id") %>%
      left_join(rsp, by = "student_id") %>%
      mutate(
        improve_flag = (delta_7d < RISK_THETA_DELTA_THRESHOLD),
        attn_flag = ((abs_rate + tardy_rate) > RISK_ATTENDANCE_THRESHOLD),
        resp_flag = ((guess_like_rate > RISK_GUESS_THRESHOLD) | (omit_rate > RISK_OMIT_THRESHOLD)),
        risk_score = improve_flag * 3 + attn_flag * 2 + resp_flag * 1
      ) %>%
      arrange(desc(risk_score), desc(improve_flag), desc(attn_flag), theta, delta_7d) %>%
      transmute(
        student_id, student_name, theta = round(theta,2), delta_7d = round(delta_7d,3),
        absences_14d = absences, tardies_14d = tardies,
        guess_rate = round(guess_like_rate,2), omit_rate = round(omit_rate,2),
        weak_tags = top3,
        risk_score
      )
    
    # Apply bucket filter if set
    bf <- bucket_filter()
    if (!is.null(bf)) {
      combined <- combined %>% filter(
        if (bf == "very_low") theta <= -1.5
        else if (bf == "low") theta > -1.5 & theta <= -0.5
        else if (bf == "mid") theta > -0.5 & theta <= 0.5
        else if (bf == "high") theta > 0.5 & theta <= 1.5
        else if (bf == "very_high") theta > 1.5
        else TRUE
      )
    }
    
    combined
  })

  output$students_table <- renderDT({
    datatable(students_tbl() %>% select(-risk_score), selection = "single", rownames = FALSE, filter = "top",
              options = list(pageLength = 15, dom = 'ftip', scrollX = TRUE))
  }, server = TRUE)

  # Bucket filter actions
  observeEvent(input$act_very_low, {
    bucket_filter("very_low")
    showNotification("매우낮음 학생 필터 적용 (θ <= -1.5)", type = "message", duration = 3)
    students <- students_tbl()
    if (nrow(students) > 0) {
      if (!(has_role(claims, "teacher") || has_role(claims, "admin"))) {
        showNotification("과제 배정 권한이 없습니다.", type = "error", duration = 4)
      } else {
        template_id <- ASSIGNMENT_TEMPLATES$very_low$template_id %||% "remedial_basics"
        ok <- call_assignment_api(students$student_id, template_id, claims, assignment_auth)
        showNotification(sprintf("보정 과제 배정: %d명 %s", nrow(students), if (ok) "성공" else "실패"), type = if (ok) "message" else "error", duration = 4)
      }
    }
  })
  observeEvent(input$act_low, {
    bucket_filter("low")
    showNotification("낮음 학생 필터 적용 (-1.5 < θ <= -0.5)", type = "message", duration = 3)
    students <- students_tbl()
    if (nrow(students) > 0) {
      if (!(has_role(claims, "teacher") || has_role(claims, "admin"))) {
        showNotification("과제 배정 권한이 없습니다.", type = "error", duration = 4)
      } else {
        template_id <- ASSIGNMENT_TEMPLATES$low$template_id %||% "supplementary_review"
        ok <- call_assignment_api(students$student_id, template_id, claims, assignment_auth)
        showNotification(sprintf("보충수업 배정: %d명 %s", nrow(students), if (ok) "성공" else "실패"), type = if (ok) "message" else "error", duration = 4)
      }
    }
  })
  observeEvent(input$act_mid, {
    bucket_filter("mid")
    showNotification("중간 학생 필터 적용 (-0.5 < θ <= 0.5)", type = "message", duration = 3)
    students <- students_tbl()
    if (nrow(students) > 0) {
      if (!(has_role(claims, "teacher") || has_role(claims, "admin"))) {
        showNotification("과제 배정 권한이 없습니다.", type = "error", duration = 4)
      } else {
        template_id <- ASSIGNMENT_TEMPLATES$mid$template_id %||% "core_practice"
        ok <- call_assignment_api(students$student_id, template_id, claims, assignment_auth)
        showNotification(sprintf("핵심 연습 배정: %d명 %s", nrow(students), if (ok) "성공" else "실패"), type = if (ok) "message" else "error", duration = 4)
      }
    }
  })
  observeEvent(input$act_high, {
    bucket_filter("high")
    showNotification("높음 학생 필터 적용 (0.5 < θ <= 1.5)", type = "message", duration = 3)
    students <- students_tbl()
    if (nrow(students) > 0) {
      if (!(has_role(claims, "teacher") || has_role(claims, "admin"))) {
        showNotification("과제 배정 권한이 없습니다.", type = "error", duration = 4)
      } else {
        template_id <- ASSIGNMENT_TEMPLATES$high$template_id %||% "challenge_advanced"
        ok <- call_assignment_api(students$student_id, template_id, claims, assignment_auth)
        showNotification(sprintf("상향 도전 배정: %d명 %s", nrow(students), if (ok) "성공" else "실패"), type = if (ok) "message" else "error", duration = 4)
      }
    }
  })
  observeEvent(input$act_very_high, {
    bucket_filter("very_high")
    showNotification("매우높음 학생 필터 적용 (θ > 1.5)", type = "message", duration = 3)
    students <- students_tbl()
    if (nrow(students) > 0) {
      if (!(has_role(claims, "teacher") || has_role(claims, "admin"))) {
        showNotification("과제 배정 권한이 없습니다.", type = "error", duration = 4)
      } else {
        template_id <- ASSIGNMENT_TEMPLATES$very_high$template_id %||% "enrichment_extension"
        ok <- call_assignment_api(students$student_id, template_id, claims, assignment_auth)
        showNotification(sprintf("심화/확장 배정: %d명 %s", nrow(students), if (ok) "성공" else "실패"), type = if (ok) "message" else "error", duration = 4)
      }
    }
  })
  
  # Clear filter button
  observeEvent(input$clear_filter, {
    bucket_filter(NULL)
    showNotification("필터 초기화", type = "message", duration = 2)
  })

  # Drilldown modal
  observeEvent(input$students_table_rows_selected, {
    idx <- input$students_table_rows_selected
    req(idx)
    row <- students_tbl()[idx, ]
    student_id <- row$student_id

    showModal(modalDialog(size = "l", easyClose = TRUE, title = paste0("학생 상세: ", row$student_name, " (", student_id, ")"),
      fluidRow(
        column(6, h4("최근 4주 θ 추이"), plotlyOutput("student_theta_plot", height = 250)),
        column(6, h4("출석 타임라인"), plotlyOutput("student_att_plot", height = 250))
      ),
      fluidRow(
        column(12, h4("취약 스킬태그 TOP3"), uiOutput("student_skills"))
      )
    ))

    # Render student subviews
    output$student_theta_plot <- renderPlotly({
      df <- theta_ds() %>% filter(student_id == !!student_id) %>% collect()
      df <- df %>% filter(date >= Sys.Date()-27)
      plot_ly(df, x = ~date, y = ~theta, type = 'scatter', mode = 'lines+markers') %>% layout(yaxis = list(title = "θ"), xaxis = list(title = ""))
    })

    output$student_att_plot <- renderPlotly({
      df <- attend_ds() %>% filter(student_id == !!student_id) %>% collect()
      df <- df %>% filter(date >= Sys.Date()-27)
      cols <- c(present = '#4CAF50', tardy = '#FFC107', absent = '#F44336')
      plot_ly(df, x = ~date, y = ~as.numeric(status != 'present'), type = 'bar', color = ~status, colors = cols) %>%
        layout(yaxis = list(title = "이상 여부", tickvals = c(0,1), ticktext = c("정상","이상")), barmode = 'stack', xaxis = list(title = ""))
    })

    output$student_skills <- renderUI({
      skills <- skill_ds() %>% filter(student_id == !!student_id) %>% select(top3) %>% collect()
      tags$span(skills$top3[[1]] %||% "")
    })
  })
}

shinyApp(ui, server)
