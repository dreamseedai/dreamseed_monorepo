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

# ---------------------------
# Claims helpers (reverse-proxy injected headers)
# ---------------------------
parse_claims <- function(session) {
  req <- session$request
  get_header <- function(name, default = "") {
    key <- paste0("HTTP_", toupper(gsub("-", "_", name)))
    req[[key]] %||% default
  }
  list(
    user = get_header("X-User") %||% Sys.getenv("DEV_USER", unset = "local_teacher"),
    org_id = get_header("X-Org-Id") %||% Sys.getenv("DEV_ORG_ID", unset = "org_001"),
    roles = strsplit(get_header("X-Roles") %||% Sys.getenv("DEV_ROLES", unset = "teacher"), ",")[[1]] |> trimws()
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
      omit_rate = pmax(0, rnorm(n(), 0.06, 0.04))
    )
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
                column(4, helpText("목표: 1분 이내介入 결정을 위한 스냅샷 제공"))
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

  date_filter <- reactive({ req(input$class_dates); input$class_dates })

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
    low <- sum(lt$delta_7d < 0.02, na.rm = TRUE)
    total <- nrow(lt)
    valueBox(sprintf("%d명", low), "리스크: 개선 저조(Δ7d<0.02)", icon = icon("triangle-exclamation"), color = if (low/total > 0.3) "red" else if (low>0) "yellow" else "green")
  })

  output$vb_risk_attn <- renderValueBox({
    am <- attn_metrics_tbl()
    irregular <- sum((am$abs_rate + am$tardy_rate) > 0.25, na.rm = TRUE)
    total <- nrow(am)
    valueBox(sprintf("%d명", irregular), "리스크: 출석 불규칙", icon = icon("user-clock"), color = if (irregular/total > 0.2) "red" else if (irregular>0) "yellow" else "green")
  })

  # Histogram and bucket actions
  output$theta_hist <- renderPlotly({
    lt <- latest_theta_tbl()
    plot_ly(lt, x = ~theta, type = 'histogram', nbinsx = 24) %>%
      layout(xaxis = list(title = "θ"), yaxis = list(title = "학생 수"))
  })

  output$bucket_actions <- renderUI({
    tags$div(
      tags$small("버킷별 추천: θ<=-1.5 보정 과제 · -1.5~-0.5 보충수업 · -0.5~0.5 핵심 연습 · 0.5~1.5 상향 도전 · >1.5 심화/확장")
    )
  })

  # Students table with drilldown
  students_tbl <- reactive({
    lt <- latest_theta_tbl()
    am <- attn_metrics_tbl()
    skills <- skill_ds() %>% select(student_id, top3) %>% collect()
    students <- students_ds() %>% select(student_id, student_name) %>% collect()
    lt %>% left_join(am, by = "student_id") %>% left_join(skills, by = "student_id") %>% left_join(students, by = "student_id") %>%
      transmute(student_id, student_name, theta = round(theta,2), delta_7d = round(delta_7d,2), absences_14d = absences, tardies_14d = tardies, weak_tags = top3)
  })

  output$students_table <- renderDT({
    datatable(students_tbl(), selection = "single", rownames = FALSE, filter = "top",
              options = list(pageLength = 10, dom = 'ftip', scrollX = TRUE))
  }, server = TRUE)

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
