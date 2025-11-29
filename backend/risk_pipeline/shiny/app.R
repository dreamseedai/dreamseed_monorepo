# DreamSeedAI 주간 리스크 대시보드 (Shiny)
# 교사용 필터/검색/정렬 + 테넌트 브랜딩

library(shiny)
library(arrow)
library(dplyr)
library(yaml)
library(DT)

# 설정
base_dir <- Sys.getenv("RISK_REPORTS_DIR", "/opt/dreamseedai/risk_pipeline/reports")
config_dir <- file.path(dirname(base_dir), "config")
tenants_file <- file.path(config_dir, "tenants.yaml")

# 테넌트 로드
tenants <- yaml::read_yaml(tenants_file)$tenants
org_choices <- setNames(
  sapply(tenants, `[[`, "org_id"),
  sapply(tenants, `[[`, "name")
)

# UI
ui <- fluidPage(
  # 동적 브랜딩 CSS
  uiOutput("brand_css"),
  
  # 헤더
  div(
    class = "header",
    style = "padding: 20px; margin-bottom: 20px; border-bottom: 2px solid #ddd;",
    uiOutput("header_logo"),
    h1(textOutput("title"), style = "display: inline-block; margin-left: 10px;")
  ),
  
  # 메인 레이아웃
  sidebarLayout(
    sidebarPanel(
      width = 3,
      
      # 테넌트 선택
      selectInput(
        "org",
        "Organization",
        choices = org_choices,
        selected = org_choices[1]
      ),
      
      # 날짜 선택
      dateInput(
        "date",
        "Report Date",
        value = Sys.Date()
      ),
      
      # 리스크 필터
      selectInput(
        "risk",
        "Overall Risk",
        choices = c("ALL", "CRIT", "WARN", "OK"),
        selected = "ALL"
      ),
      
      # 사용자 검색
      textInput(
        "uid",
        "Search User ID",
        placeholder = "Enter user ID..."
      ),
      
      hr(),
      
      # 통계 요약
      h4("Summary"),
      verbatimTextOutput("summary"),
      
      hr(),
      
      # 다운로드
      downloadButton("download_csv", "Download CSV", class = "btn-primary btn-block")
    ),
    
    mainPanel(
      width = 9,
      
      # 데이터 테이블
      DTOutput("tbl")
    )
  )
)

# Server
server <- function(input, output, session) {
  
  # 테넌트 정보 가져오기
  tenant_by_org <- function(oid) {
    idx <- which(sapply(tenants, `[[`, "org_id") == oid)
    if (length(idx) == 0) return(tenants[[1]])
    tenants[[idx]]
  }
  
  # 동적 브랜딩 CSS
  output$brand_css <- renderUI({
    t <- tenant_by_org(input$org)
    col <- t$branding$primary %||% "#0f6fff"
    
    tags$style(HTML(sprintf("
      h1, h2, h3, .navbar { color: %s; }
      .btn-primary { background: %s; border: none; }
      .btn-primary:hover { background: %s; opacity: 0.9; }
      .header { border-bottom-color: %s; }
    ", col, col, col, col)))
  })
  
  # 헤더 로고
  output$header_logo <- renderUI({
    t <- tenant_by_org(input$org)
    logo <- t$branding$logo
    
    if (!is.null(logo) && nzchar(logo)) {
      tags$img(
        src = logo,
        style = "height: 40px; vertical-align: middle; display: inline-block;"
      )
    }
  })
  
  # 제목
  output$title <- renderText({
    t <- tenant_by_org(input$org)
    paste(t$name, "— Weekly Risk Dashboard")
  })
  
  # 메트릭 데이터 로드
  metrics <- reactive({
    d <- format(input$date, "%Y-%m-%d")
    feather <- file.path(base_dir, d, sprintf("metrics_%s.feather", d))
    
    if (!file.exists(feather)) {
      return(data.frame())
    }
    
    tryCatch(
      read_feather(feather),
      error = function(e) {
        message("Error reading feather: ", e$message)
        data.frame()
      }
    )
  })
  
  # 필터링된 데이터
  filtered <- reactive({
    m <- metrics()
    
    if (nrow(m) == 0) {
      return(m)
    }
    
    # 조직 필터
    m <- m %>% filter(org_id == input$org)
    
    # 리스크 필터
    if (input$risk != "ALL") {
      m <- m %>% filter(risk_overall == input$risk)
    }
    
    # 사용자 검색
    if (nzchar(input$uid)) {
      m <- m %>% filter(grepl(input$uid, as.character(user_id), ignore.case = TRUE))
    }
    
    # 정렬: CRIT → WARN → OK, 그 다음 delta_7d 오름차순
    m %>% arrange(
      match(risk_overall, c("CRIT", "WARN", "OK")),
      delta_7d
    )
  })
  
  # 요약 통계
  output$summary <- renderText({
    m <- filtered()
    
    if (nrow(m) == 0) {
      return("No data available")
    }
    
    total <- nrow(m)
    crit <- sum(m$risk_overall == "CRIT", na.rm = TRUE)
    warn <- sum(m$risk_overall == "WARN", na.rm = TRUE)
    ok <- sum(m$risk_overall == "OK", na.rm = TRUE)
    
    sprintf(
      "Total: %d\nCRIT: %d (%.1f%%)\nWARN: %d (%.1f%%)\nOK: %d (%.1f%%)",
      total,
      crit, 100 * crit / total,
      warn, 100 * warn / total,
      ok, 100 * ok / total
    )
  })
  
  # 데이터 테이블
  output$tbl <- renderDT({
    m <- filtered()
    
    if (nrow(m) == 0) {
      return(datatable(data.frame(Message = "No data available")))
    }
    
    # 컬럼 선택 및 포맷팅
    display_cols <- c(
      "user_id", "risk_overall", "delta_7d", "theta_t",
      "omit_rate", "attend_rate", "n_obs",
      "risk_theta", "risk_omit", "risk_attend"
    )
    
    m_display <- m %>%
      select(any_of(display_cols)) %>%
      mutate(
        delta_7d = round(delta_7d, 3),
        theta_t = round(theta_t, 3),
        omit_rate = sprintf("%.1f%%", omit_rate * 100),
        attend_rate = sprintf("%.1f%%", attend_rate * 100)
      )
    
    datatable(
      m_display,
      options = list(
        pageLength = 25,
        scrollX = TRUE,
        order = list(list(1, 'asc'))  # risk_overall 기준 정렬
      ),
      rownames = FALSE
    ) %>%
      formatStyle(
        'risk_overall',
        backgroundColor = styleEqual(
          c('CRIT', 'WARN', 'OK'),
          c('#ffebee', '#fff8e1', '#e8f5e9')
        ),
        fontWeight = 'bold'
      )
  })
  
  # CSV 다운로드
  output$download_csv <- downloadHandler(
    filename = function() {
      sprintf(
        "risk_%s_%s.csv",
        input$org,
        format(input$date, "%Y-%m-%d")
      )
    },
    content = function(file) {
      write.csv(filtered(), file, row.names = FALSE)
    }
  )
}

# 앱 실행
shinyApp(ui, server)
