# DreamSeedAI 실시간 드리프트 탐지 대시보드
# 서사형 모니터링 시스템

library(shiny)
library(dplyr)
library(ggplot2)
library(DT)
library(arrow)
library(lubridate)

# UI
ui <- fluidPage(
  tags$head(
    tags$style(HTML("
      .alert-card {
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        border-left: 5px solid;
      }
      .alert-high {
        background: #ffebee;
        border-left-color: #f44336;
      }
      .alert-medium {
        background: #fff8e1;
        border-left-color: #ff9800;
      }
      .alert-low {
        background: #e8f5e9;
        border-left-color: #4caf50;
      }
      .metric-box {
        background: #f5f5f5;
        padding: 10px;
        border-radius: 4px;
        margin: 5px 0;
      }
      .action-btn {
        margin-top: 10px;
      }
    "))
  ),
  
  titlePanel("🔍 DreamSeedAI Drift Watch"),
  
  fluidRow(
    column(
      width = 4,
      h3("오늘의 진단 카드"),
      uiOutput("narrative_cards"),
      hr(),
      h4("경보 통계"),
      verbatimTextOutput("alert_summary")
    ),
    
    column(
      width = 8,
      tabsetPanel(
        tabPanel(
          "IRT 파라미터",
          plotOutput("drift_plot_irt", height = "300px"),
          plotOutput("drift_plot_guessing", height = "300px")
        ),
        tabPanel(
          "행동 지표",
          plotOutput("drift_plot_behavior", height = "300px"),
          plotOutput("drift_plot_latency", height = "300px")
        ),
        tabPanel(
          "지역/언어",
          plotOutput("drift_plot_region", height = "400px"),
          DTOutput("region_table")
        ),
        tabPanel(
          "원인-조치",
          h4("권장 액션"),
          uiOutput("action_buttons"),
          hr(),
          h4("최근 조치 이력"),
          DTOutput("action_history")
        )
      )
    )
  )
)

# Server
server <- function(input, output, session) {
  
  # 데이터 로드 (실제로는 DB/API에서 가져옴)
  metrics <- reactive({
    # 샘플 데이터 생성
    days <- seq(Sys.Date() - 13, Sys.Date(), by = "day")
    
    list(
      irt = data.frame(
        day = days,
        delta_b = rnorm(14, mean = 0.1, sd = 0.15),
        delta_a = rnorm(14, mean = 0.05, sd = 0.10),
        delta_c = rnorm(14, mean = 0.02, sd = 0.03)
      ),
      behavior = data.frame(
        day = days,
        omit_rate = runif(14, 0.03, 0.10),
        last_option_rate = runif(14, 0.20, 0.35),
        latency_p95 = rnorm(14, mean = 100, sd = 20)
      ),
      region = data.frame(
        region = c("KR", "US", "CN", "JP"),
        accuracy = c(0.72, 0.68, 0.65, 0.70),
        count = c(1200, 800, 600, 400)
      )
    )
  })
  
  # 경보 생성
  alerts <- reactive({
    m <- metrics()
    
    # 최근 7일 평균
    recent_delta_b <- mean(tail(m$irt$delta_b, 7))
    recent_delta_c <- mean(tail(m$irt$delta_c, 7))
    recent_omit <- mean(tail(m$behavior$omit_rate, 7))
    recent_latency <- mean(tail(m$behavior$latency_p95, 7))
    
    alerts_list <- list()
    
    # Anchor Erosion
    if (abs(recent_delta_b) > 0.35) {
      level <- if (abs(recent_delta_b) > 0.70) "high" else "medium"
      alerts_list[[length(alerts_list) + 1]] <- list(
        type = "anchor_erosion",
        level = level,
        title = "Anchor Erosion",
        message = sprintf(
          "앵커 문항의 난이도 변화 Δb = %.3f (7일 이동창). P(drift) = %.2f. 대응: 재보정 큐에 편성.",
          recent_delta_b,
          min(abs(recent_delta_b) / 0.35, 1.0)
        ),
        action = "recalibrate_anchor"
      )
    }
    
    # Guessing Instability
    if (abs(recent_delta_c) > 0.06) {
      level <- if (abs(recent_delta_c) > 0.12) "high" else "medium"
      alerts_list[[length(alerts_list) + 1]] <- list(
        type = "guessing_instability",
        level = level,
        title = "Guessing Instability",
        message = sprintf(
          "추측도 변화 Δc = %+.3f (14일). 대응: 보기 난이도/길이 점검.",
          recent_delta_c
        ),
        action = "review_item_options"
      )
    }
    
    # Latency Creep
    if (recent_latency > 120) {
      level <- if (recent_latency > 150) "high" else "medium"
      alerts_list[[length(alerts_list) + 1]] <- list(
        type = "latency_creep",
        level = level,
        title = "Latency Creep",
        message = sprintf(
          "응답 시간 P95 = %.1f초. 피로/UI 지연 가능. 대응: 성능 프로파일링.",
          recent_latency
        ),
        action = "profile_performance"
      )
    }
    
    # Region-Language Drift
    acc_diff <- max(m$region$accuracy) - min(m$region$accuracy)
    if (acc_diff > 0.10) {
      level <- if (acc_diff > 0.20) "high" else "medium"
      max_region <- m$region$region[which.max(m$region$accuracy)]
      min_region <- m$region$region[which.min(m$region$accuracy)]
      
      alerts_list[[length(alerts_list) + 1]] <- list(
        type = "region_language_drift",
        level = level,
        title = "Region-Language Drift",
        message = sprintf(
          "지역별 정답률 격차: %s (%.1f%%) vs %s (%.1f%%). 대응: 언어별 문항 재검토.",
          max_region, max(m$region$accuracy) * 100,
          min_region, min(m$region$accuracy) * 100
        ),
        action = "review_language_items"
      )
    }
    
    alerts_list
  })
  
  # 서사 카드 렌더링
  output$narrative_cards <- renderUI({
    alert_list <- alerts()
    
    if (length(alert_list) == 0) {
      return(div(
        class = "alert-card alert-low",
        h4("✅ 정상"),
        p("현재 감지된 드리프트 없음")
      ))
    }
    
    lapply(alert_list, function(alert) {
      class_name <- paste0("alert-card alert-", alert$level)
      icon <- switch(
        alert$level,
        high = "🔴",
        medium = "🟠",
        low = "🟢"
      )
      
      div(
        class = class_name,
        h4(paste(icon, alert$title)),
        p(alert$message),
        actionButton(
          paste0("action_", alert$type),
          paste("조치:", alert$action),
          class = "btn btn-sm btn-primary action-btn"
        )
      )
    })
  })
  
  # 경보 통계
  output$alert_summary <- renderText({
    alert_list <- alerts()
    
    high_count <- sum(sapply(alert_list, function(a) a$level == "high"))
    medium_count <- sum(sapply(alert_list, function(a) a$level == "medium"))
    low_count <- sum(sapply(alert_list, function(a) a$level == "low"))
    
    sprintf(
      "총 경보: %d\n🔴 높음: %d\n🟠 중간: %d\n🟢 낮음: %d",
      length(alert_list),
      high_count,
      medium_count,
      low_count
    )
  })
  
  # IRT 파라미터 플롯
  output$drift_plot_irt <- renderPlot({
    m <- metrics()
    
    ggplot(m$irt, aes(x = day)) +
      geom_line(aes(y = delta_b, color = "Δb (난이도)"), size = 1) +
      geom_line(aes(y = delta_a, color = "Δa (변별도)"), size = 1) +
      geom_hline(yintercept = 0.35, linetype = "dashed", color = "red", alpha = 0.5) +
      geom_hline(yintercept = -0.35, linetype = "dashed", color = "red", alpha = 0.5) +
      labs(
        title = "IRT 파라미터 변화 (앵커 문항)",
        x = "날짜",
        y = "변화량",
        color = "파라미터"
      ) +
      theme_minimal() +
      theme(legend.position = "bottom")
  })
  
  output$drift_plot_guessing <- renderPlot({
    m <- metrics()
    
    ggplot(m$irt, aes(x = day, y = delta_c)) +
      geom_line(color = "#ff9800", size = 1) +
      geom_hline(yintercept = 0.06, linetype = "dashed", color = "red", alpha = 0.5) +
      geom_hline(yintercept = -0.06, linetype = "dashed", color = "red", alpha = 0.5) +
      labs(
        title = "추측도 변화 (Δc)",
        x = "날짜",
        y = "Δc"
      ) +
      theme_minimal()
  })
  
  # 행동 지표 플롯
  output$drift_plot_behavior <- renderPlot({
    m <- metrics()
    
    ggplot(m$behavior, aes(x = day)) +
      geom_line(aes(y = omit_rate * 100, color = "무응답률 (%)"), size = 1) +
      geom_line(aes(y = last_option_rate * 100, color = "마지막 보기 선택률 (%)"), size = 1) +
      geom_hline(yintercept = 8, linetype = "dashed", color = "red", alpha = 0.5) +
      labs(
        title = "행동 지표",
        x = "날짜",
        y = "비율 (%)",
        color = "지표"
      ) +
      theme_minimal() +
      theme(legend.position = "bottom")
  })
  
  output$drift_plot_latency <- renderPlot({
    m <- metrics()
    
    ggplot(m$behavior, aes(x = day, y = latency_p95)) +
      geom_line(color = "#2196f3", size = 1) +
      geom_hline(yintercept = 120, linetype = "dashed", color = "red", alpha = 0.5) +
      labs(
        title = "응답 시간 P95",
        x = "날짜",
        y = "시간 (초)"
      ) +
      theme_minimal()
  })
  
  # 지역/언어 플롯
  output$drift_plot_region <- renderPlot({
    m <- metrics()
    
    ggplot(m$region, aes(x = reorder(region, -accuracy), y = accuracy, fill = region)) +
      geom_col() +
      geom_text(aes(label = sprintf("%.1f%%", accuracy * 100)), vjust = -0.5) +
      labs(
        title = "지역별 정답률",
        x = "지역",
        y = "정답률"
      ) +
      scale_y_continuous(labels = scales::percent) +
      theme_minimal() +
      theme(legend.position = "none")
  })
  
  output$region_table <- renderDT({
    m <- metrics()
    datatable(
      m$region,
      colnames = c("지역", "정답률", "응답 수"),
      options = list(dom = 't', pageLength = 10)
    ) %>%
      formatPercentage('accuracy', 1)
  })
  
  # 액션 버튼
  output$action_buttons <- renderUI({
    alert_list <- alerts()
    
    if (length(alert_list) == 0) {
      return(p("현재 권장 조치 없음"))
    }
    
    unique_actions <- unique(sapply(alert_list, function(a) a$action))
    
    lapply(unique_actions, function(action) {
      actionButton(
        paste0("execute_", action),
        paste("실행:", action),
        class = "btn btn-warning",
        style = "margin: 5px;"
      )
    })
  })
  
  # 조치 이력 (샘플)
  output$action_history <- renderDT({
    history <- data.frame(
      timestamp = c("2025-11-09 08:00", "2025-11-08 14:30", "2025-11-07 09:15"),
      action = c("recalibrate_anchor", "review_item_options", "profile_performance"),
      status = c("완료", "진행중", "완료"),
      user = c("admin", "teacher1", "admin")
    )
    
    datatable(
      history,
      colnames = c("시간", "조치", "상태", "사용자"),
      options = list(dom = 't', pageLength = 10)
    )
  })
}

# 앱 실행
shinyApp(ui, server)
