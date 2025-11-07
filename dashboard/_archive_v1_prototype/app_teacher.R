#!/usr/bin/env Rscript
# ============================================================================
# 교사용 클래스 모니터링 대시보드
# ============================================================================
# 목표: 교사가 1분 안에 개입 대상을 결정할 수 있는 통합 분석 포털
#
# 핵심 기능:
# - 클래스 스냅샷: 평균 θ, 중앙값, 상·하위 10% 구간, 주간 성장률
# - 리스크 카드: 개선 저조, 출석 불규칙 학생 알림
# - 그룹 θ 히스토그램: 능력 분포 시각화 + 버킷별 추천 액션
# - 학생 드릴다운: θ 추이, 출석 타임라인, 취약 스킬 TOP3
#
# 실행:
#   Rscript -e 'shiny::runApp("dashboard/app_teacher.R", host="0.0.0.0", port=8081)'
#
# 개발 모드 (프록시 없이):
#   DEV_USER=teacher01 DEV_ORG_ID=org_001 DEV_ROLES=teacher \
#   Rscript -e 'shiny::runApp("dashboard/app_teacher.R", port=8081)'

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

# ============================================================================
# 설정 및 데이터 로드
# ============================================================================

DATASET_ROOT <- Sys.getenv("DATASET_ROOT", "data/datasets")

# 프록시 헤더 또는 개발 환경변수에서 사용자 정보 추출
get_user_context <- function(session) {
  headers <- session$request$HTTP_X_USER
  
  if (!is.null(headers) && nchar(headers) > 0) {
    # 프록시 헤더 사용
    list(
      user_id = session$request$HTTP_X_USER,
      org_id = session$request$HTTP_X_ORG_ID,
      roles = strsplit(session$request$HTTP_X_ROLES, ",")[[1]]
    )
  } else {
    # 개발 환경변수 사용
    list(
      user_id = Sys.getenv("DEV_USER", "teacher01"),
      org_id = Sys.getenv("DEV_ORG_ID", "org_001"),
      roles = strsplit(Sys.getenv("DEV_ROLES", "teacher"), ",")[[1]]
    )
  }
}

# 데이터셋 초기화 (없으면 부트스트랩)
init_datasets <- function() {
  if (!dir.exists(DATASET_ROOT) || 
      !file.exists(file.path(DATASET_ROOT, "classes.parquet"))) {
    cat("⚠️  데이터셋이 없습니다. 부트스트랩 스크립트를 실행합니다...\n")
    system("Rscript dashboard/bootstrap_data.R")
  }
}

init_datasets()

# Arrow 데이터셋 로드 (지연 로딩)
load_classes <- function() {
  read_parquet(file.path(DATASET_ROOT, "classes.parquet"))
}

load_students <- function() {
  read_parquet(file.path(DATASET_ROOT, "students.parquet"))
}

load_student_theta <- function(org_id = NULL, class_id = NULL) {
  ds <- open_dataset(file.path(DATASET_ROOT, "student_theta"))
  
  if (!is.null(org_id)) {
    ds <- ds %>% filter(org_id == !!org_id)
  }
  if (!is.null(class_id)) {
    ds <- ds %>% filter(class_id == !!class_id)
  }
  
  ds %>% collect()
}

load_attendance <- function(org_id = NULL, class_id = NULL) {
  ds <- open_dataset(file.path(DATASET_ROOT, "attendance"))
  
  if (!is.null(org_id)) {
    ds <- ds %>% filter(org_id == !!org_id)
  }
  if (!is.null(class_id)) {
    ds <- ds %>% filter(class_id == !!class_id)
  }
  
  ds %>% collect()
}

load_skill_weakness <- function() {
  read_parquet(file.path(DATASET_ROOT, "skill_weakness.parquet"))
}

load_response_stats <- function() {
  read_parquet(file.path(DATASET_ROOT, "response_stats.parquet"))
}

# ============================================================================
# 분석 함수
# ============================================================================

# 클래스 스냅샷 계산
compute_class_snapshot <- function(class_id, org_id) {
  # 최근 θ 데이터
  theta_data <- load_student_theta(org_id, class_id) %>%
    arrange(student_id, date) %>%
    group_by(student_id) %>%
    slice_tail(n = 1) %>%
    ungroup()
  
  # 7일 전 θ 데이터
  theta_7d_ago <- load_student_theta(org_id, class_id) %>%
    filter(date == max(date) - days(7)) %>%
    select(student_id, theta_7d = theta)
  
  # 주간 성장률 계산
  theta_with_growth <- theta_data %>%
    left_join(theta_7d_ago, by = "student_id") %>%
    mutate(delta_7d = theta - coalesce(theta_7d, theta))
  
  # 통계 계산
  list(
    mean_theta = mean(theta_with_growth$theta, na.rm = TRUE),
    median_theta = median(theta_with_growth$theta, na.rm = TRUE),
    q10_theta = quantile(theta_with_growth$theta, 0.1, na.rm = TRUE),
    q90_theta = quantile(theta_with_growth$theta, 0.9, na.rm = TRUE),
    mean_growth_7d = mean(theta_with_growth$delta_7d, na.rm = TRUE),
    n_students = nrow(theta_with_growth)
  )
}

# 출석 안정도 계산
compute_attendance_stability <- function(class_id, org_id) {
  attendance_data <- load_attendance(org_id, class_id) %>%
    filter(date >= max(date) - days(30))  # 최근 30일
  
  total_days <- attendance_data %>%
    distinct(date) %>%
    nrow()
  
  attendance_summary <- attendance_data %>%
    group_by(student_id) %>%
    summarise(
      n_absent = sum(status == "absent"),
      n_late = sum(status == "late"),
      n_total = n(),
      .groups = "drop"
    ) %>%
    mutate(
      absence_rate = n_absent / n_total,
      late_rate = n_late / n_total,
      irregular = (n_absent + n_late) / n_total > 0.25
    )
  
  list(
    avg_absence_rate = mean(attendance_summary$absence_rate, na.rm = TRUE),
    avg_late_rate = mean(attendance_summary$late_rate, na.rm = TRUE),
    n_irregular = sum(attendance_summary$irregular, na.rm = TRUE)
  )
}

# 리스크 학생 탐지
detect_risk_students <- function(class_id, org_id) {
  # θ 성장 저조
  theta_data <- load_student_theta(org_id, class_id) %>%
    arrange(student_id, date) %>%
    group_by(student_id) %>%
    slice_tail(n = 1) %>%
    ungroup()
  
  theta_7d_ago <- load_student_theta(org_id, class_id) %>%
    filter(date == max(date) - days(7)) %>%
    select(student_id, theta_7d = theta)
  
  low_growth <- theta_data %>%
    left_join(theta_7d_ago, by = "student_id") %>%
    mutate(delta_7d = theta - coalesce(theta_7d, theta)) %>%
    filter(delta_7d < 0.02) %>%
    select(student_id, theta, delta_7d)
  
  # 출석 불규칙
  attendance_data <- load_attendance(org_id, class_id) %>%
    filter(date >= max(date) - days(30))
  
  irregular_attendance <- attendance_data %>%
    group_by(student_id) %>%
    summarise(
      n_absent = sum(status == "absent"),
      n_late = sum(status == "late"),
      n_total = n(),
      .groups = "drop"
    ) %>%
    mutate(irregular_rate = (n_absent + n_late) / n_total) %>%
    filter(irregular_rate > 0.25) %>%
    select(student_id, irregular_rate, n_absent, n_late)
  
  list(
    low_growth = low_growth,
    irregular_attendance = irregular_attendance
  )
}

# θ 히스토그램 데이터
compute_theta_histogram <- function(class_id, org_id, bins = 24) {
  theta_data <- load_student_theta(org_id, class_id) %>%
    arrange(student_id, date) %>%
    group_by(student_id) %>%
    slice_tail(n = 1) %>%
    ungroup()
  
  theta_data %>%
    mutate(
      theta_bin = cut(theta, breaks = bins, include.lowest = TRUE)
    ) %>%
    count(theta_bin) %>%
    mutate(
      bin_center = as.numeric(str_extract(as.character(theta_bin), "-?[0-9.]+")) +
        (as.numeric(str_extract(str_extract(as.character(theta_bin), ",[^]]+"), "[0-9.]+")) -
           as.numeric(str_extract(as.character(theta_bin), "-?[0-9.]+"))) / 2,
      recommendation = case_when(
        bin_center < -1 ~ "보정 과제 필요",
        bin_center < 0 ~ "보충수업 권장",
        bin_center < 1 ~ "정상 진도",
        TRUE ~ "상향 도전 과제"
      )
    )
}

# 학생 상세 정보
get_student_details <- function(class_id, org_id) {
  students <- load_students() %>%
    filter(class_id == !!class_id, org_id == !!org_id)
  
  # 최근 4주 θ 추이
  theta_4w <- load_student_theta(org_id, class_id) %>%
    filter(date >= max(date) - days(28)) %>%
    arrange(student_id, date)
  
  # 최근 θ 및 성장률
  latest_theta <- theta_4w %>%
    group_by(student_id) %>%
    slice_tail(n = 1) %>%
    ungroup() %>%
    select(student_id, theta_latest = theta)
  
  theta_7d_ago <- theta_4w %>%
    filter(date == max(date) - days(7)) %>%
    select(student_id, theta_7d = theta)
  
  theta_summary <- latest_theta %>%
    left_join(theta_7d_ago, by = "student_id") %>%
    mutate(delta_7d = theta_latest - coalesce(theta_7d, theta_latest))
  
  # 출석 통계
  attendance_summary <- load_attendance(org_id, class_id) %>%
    filter(date >= max(date) - days(30)) %>%
    group_by(student_id) %>%
    summarise(
      n_absent = sum(status == "absent"),
      n_late = sum(status == "late"),
      n_total = n(),
      .groups = "drop"
    ) %>%
    mutate(irregular_rate = (n_absent + n_late) / n_total)
  
  # 취약 스킬 TOP3
  skills <- load_skill_weakness() %>%
    filter(class_id == !!class_id, org_id == !!org_id) %>%
    group_by(student_id) %>%
    arrange(skill_rank) %>%
    summarise(
      weak_skills = paste(skill[1:min(3, n())], collapse = ", "),
      .groups = "drop"
    )
  
  # 통합
  students %>%
    left_join(theta_summary, by = "student_id") %>%
    left_join(attendance_summary, by = "student_id") %>%
    left_join(skills, by = "student_id") %>%
    mutate(
      theta_latest = round(theta_latest, 2),
      delta_7d = round(delta_7d, 3),
      irregular_rate = round(irregular_rate, 2)
    ) %>%
    select(student_name, theta_latest, delta_7d, 
           n_absent, n_late, irregular_rate, weak_skills)
}

# ============================================================================
# UI
# ============================================================================

ui <- dashboardPage(
  dashboardHeader(title = "교사용 클래스 모니터"),
  
  dashboardSidebar(
    sidebarMenu(
      menuItem("대시보드", tabName = "dashboard", icon = icon("dashboard")),
      menuItem("학생 상세", tabName = "students", icon = icon("users"))
    ),
    
    hr(),
    
    selectInput("class_select", "클래스 선택:",
                choices = NULL,
                selected = NULL)
  ),
  
  dashboardBody(
    tabItems(
      # 대시보드 탭
      tabItem(
        tabName = "dashboard",
        
        h2("클래스 스냅샷"),
        
        fluidRow(
          valueBoxOutput("mean_theta_box"),
          valueBoxOutput("median_theta_box"),
          valueBoxOutput("growth_7d_box"),
          valueBoxOutput("n_students_box")
        ),
        
        fluidRow(
          box(
            title = "능력 분포 범위",
            width = 12,
            solidHeader = TRUE,
            status = "primary",
            textOutput("theta_range_text")
          )
        ),
        
        h2("리스크 알림"),
        
        fluidRow(
          box(
            title = "개선 저조 학생",
            width = 6,
            solidHeader = TRUE,
            status = "warning",
            DTOutput("low_growth_table")
          ),
          
          box(
            title = "출석 불규칙 학생",
            width = 6,
            solidHeader = TRUE,
            status = "danger",
            DTOutput("irregular_attendance_table")
          )
        ),
        
        h2("그룹 θ 히스토그램"),
        
        fluidRow(
          box(
            title = "능력 분포 및 추천 액션",
            width = 12,
            solidHeader = TRUE,
            status = "info",
            plotlyOutput("theta_histogram", height = "400px")
          )
        )
      ),
      
      # 학생 상세 탭
      tabItem(
        tabName = "students",
        
        h2("학생 목록 및 드릴다운"),
        
        fluidRow(
          box(
            title = "학생 상세 정보",
            width = 12,
            solidHeader = TRUE,
            status = "primary",
            DTOutput("student_details_table")
          )
        )
      )
    )
  )
)

# ============================================================================
# Server
# ============================================================================

server <- function(input, output, session) {
  
  # 사용자 컨텍스트
  user_ctx <- reactive({
    get_user_context(session)
  })
  
  # 클래스 목록 로드 (org 필터링)
  observe({
    ctx <- user_ctx()
    classes <- load_classes() %>%
      filter(org_id == ctx$org_id)
    
    updateSelectInput(session, "class_select",
                      choices = setNames(classes$class_id, classes$class_name),
                      selected = classes$class_id[1])
  })
  
  # 선택된 클래스 정보
  selected_class <- reactive({
    req(input$class_select)
    load_classes() %>%
      filter(class_id == input$class_select) %>%
      slice(1)
  })
  
  # 클래스 스냅샷
  class_snapshot <- reactive({
    req(selected_class())
    compute_class_snapshot(selected_class()$class_id, selected_class()$org_id)
  })
  
  # 출석 안정도
  attendance_stability <- reactive({
    req(selected_class())
    compute_attendance_stability(selected_class()$class_id, selected_class()$org_id)
  })
  
  # 리스크 학생
  risk_students <- reactive({
    req(selected_class())
    detect_risk_students(selected_class()$class_id, selected_class()$org_id)
  })
  
  # θ 히스토그램
  theta_hist <- reactive({
    req(selected_class())
    compute_theta_histogram(selected_class()$class_id, selected_class()$org_id)
  })
  
  # 학생 상세
  student_details <- reactive({
    req(selected_class())
    get_student_details(selected_class()$class_id, selected_class()$org_id)
  })
  
  # ========================================================================
  # 출력: 클래스 스냅샷
  # ========================================================================
  
  output$mean_theta_box <- renderValueBox({
    snapshot <- class_snapshot()
    valueBox(
      round(snapshot$mean_theta, 2),
      "평균 θ",
      icon = icon("chart-line"),
      color = "blue"
    )
  })
  
  output$median_theta_box <- renderValueBox({
    snapshot <- class_snapshot()
    valueBox(
      round(snapshot$median_theta, 2),
      "중앙값 θ",
      icon = icon("chart-bar"),
      color = "light-blue"
    )
  })
  
  output$growth_7d_box <- renderValueBox({
    snapshot <- class_snapshot()
    growth <- round(snapshot$mean_growth_7d, 3)
    color <- if (growth >= 0.05) "green" else if (growth >= 0.02) "yellow" else "red"
    
    valueBox(
      growth,
      "주간 성장률 Δθ",
      icon = icon("arrow-up"),
      color = color
    )
  })
  
  output$n_students_box <- renderValueBox({
    snapshot <- class_snapshot()
    valueBox(
      snapshot$n_students,
      "학생 수",
      icon = icon("users"),
      color = "purple"
    )
  })
  
  output$theta_range_text <- renderText({
    snapshot <- class_snapshot()
    sprintf("하위 10%%: %.2f | 상위 10%%: %.2f (범위: %.2f)",
            snapshot$q10_theta,
            snapshot$q90_theta,
            snapshot$q90_theta - snapshot$q10_theta)
  })
  
  # ========================================================================
  # 출력: 리스크 알림
  # ========================================================================
  
  output$low_growth_table <- renderDT({
    risks <- risk_students()
    
    if (nrow(risks$low_growth) == 0) {
      data.frame(메시지 = "개선 저조 학생 없음")
    } else {
      students <- load_students()
      risks$low_growth %>%
        left_join(students %>% select(student_id, student_name), by = "student_id") %>%
        select(학생 = student_name, `현재 θ` = theta, `7일 성장` = delta_7d) %>%
        datatable(options = list(pageLength = 5, dom = 't'),
                  rownames = FALSE)
    }
  })
  
  output$irregular_attendance_table <- renderDT({
    risks <- risk_students()
    
    if (nrow(risks$irregular_attendance) == 0) {
      data.frame(메시지 = "출석 불규칙 학생 없음")
    } else {
      students <- load_students()
      risks$irregular_attendance %>%
        left_join(students %>% select(student_id, student_name), by = "student_id") %>%
        select(학생 = student_name, 결석 = n_absent, 지각 = n_late, 
               `불규칙률` = irregular_rate) %>%
        datatable(options = list(pageLength = 5, dom = 't'),
                  rownames = FALSE)
    }
  })
  
  # ========================================================================
  # 출력: θ 히스토그램
  # ========================================================================
  
  output$theta_histogram <- renderPlotly({
    hist_data <- theta_hist()
    
    plot_ly(hist_data, x = ~bin_center, y = ~n, type = 'bar',
            text = ~paste0("학생 수: ", n, "<br>추천: ", recommendation),
            hoverinfo = 'text',
            marker = list(
              color = ~case_when(
                bin_center < -1 ~ '#e74c3c',
                bin_center < 0 ~ '#f39c12',
                bin_center < 1 ~ '#3498db',
                TRUE ~ '#2ecc71'
              )
            )) %>%
      layout(
        title = "능력 분포 (θ)",
        xaxis = list(title = "θ 구간"),
        yaxis = list(title = "학생 수"),
        showlegend = FALSE
      )
  })
  
  # ========================================================================
  # 출력: 학생 상세
  # ========================================================================
  
  output$student_details_table <- renderDT({
    details <- student_details()
    
    datatable(
      details,
      colnames = c("학생명", "현재 θ", "7일 성장", "결석", "지각", 
                   "불규칙률", "취약 스킬 TOP3"),
      options = list(
        pageLength = 15,
        order = list(list(2, 'asc'), list(3, 'asc'), list(6, 'desc')),  # θ 낮음, 성장 낮음, 불규칙률 높음
        dom = 'frtip'
      ),
      rownames = FALSE
    ) %>%
      formatStyle(
        'delta_7d',
        backgroundColor = styleInterval(c(0.02, 0.05), c('#ffcccc', '#ffffcc', '#ccffcc', '#99ff99'))
      ) %>%
      formatStyle(
        'irregular_rate',
        backgroundColor = styleInterval(c(0.15, 0.25), c('#ccffcc', '#ffffcc', '#ffcccc', '#ff9999'))
      )
  })
}

# ============================================================================
# 앱 실행
# ============================================================================

shinyApp(ui, server)
