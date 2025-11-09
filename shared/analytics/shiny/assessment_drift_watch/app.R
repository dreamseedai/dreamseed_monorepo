# ------------------------------------------------------------
# DreamSeedAI - Assessment Drift Watch (Shiny)
# ------------------------------------------------------------
library(shiny)
library(DBI)
library(RPostgres)
library(dplyr)
library(ggplot2)

pg_connect <- function() {
  dbConnect(
    RPostgres::Postgres(),
    host = Sys.getenv("DSA_PG_HOST", "localhost"),
    port = as.integer(Sys.getenv("DSA_PG_PORT", "5432")),
    user = Sys.getenv("DSA_PG_USER", ""),
    password = Sys.getenv("DSA_PG_PASSWORD", ""),
    dbname = Sys.getenv("DSA_PG_DB", "dreamseed")
  )
}

ui <- fluidPage(
  tags$head(tags$style(HTML("
    .card { border-radius:12px;padding:12px;margin-bottom:10px;border:1px solid #eee;}
    .hi { background:#ffeaea;}
    .mid { background:#fff4e0;}
    .lo { background:#e9f7ef;}
  "))),
  titlePanel("Assessment Drift Watch (DreamSeedAI)"),
  sidebarLayout(
    sidebarPanel(
      textInput("schema", "Schema", value = Sys.getenv("DSA_PG_SCHEMA", "analytics")),
      selectInput("lang", "Language", choices = c("all","ko","en","zh-Hans","zh-Hant"), selected="all"),
      textInput("region", "Region", value="all"),
      dateRangeInput("range", "Window", start = Sys.Date()-14, end = Sys.Date()),
      actionButton("reload", "Reload")
    ),
    mainPanel(
      fluidRow(
        column(12, uiOutput("narrative"))
      ),
      fluidRow(
        column(3, uiOutput("kpi_dtheta")),
        column(3, uiOutput("kpi_lastopt")),
        column(3, uiOutput("kpi_omit")),
        column(3, uiOutput("kpi_alerts"))
      ),
      hr(),
      plotOutput("ts_lastopt", height="260px"),
      plotOutput("ts_latency", height="260px"),
      hr(),
      h4("Anchor Δa/Δb/Δc (Top 50 by magnitude)"),
      tableOutput("tbl_anchor")
    )
  )
)

server <- function(input, output, session){
  vals <- reactiveVal(NULL)

  observeEvent(input$reload, {
    con <- pg_connect(); on.exit(dbDisconnect(con), add=TRUE)
    sch <- dbQuoteIdentifier(con, input$schema)
    lang <- if (input$lang=="all") NULL else input$lang
    region <- if (input$region=="all") NULL else input$region
    drange <- paste0(" ts >= '", input$range[1], "' AND ts < '", input$range[2] + 1, "' ")

    q_beh <- paste0("SELECT ts, user_lang, region, last_option_rate, omit_rate FROM ", sch, ".behavior_metrics WHERE ", drange, if(!is.null(lang)) " AND user_lang=$1 " else "", if(!is.null(region)) " AND region=$2 " else "", " ORDER BY ts;")
    q_lat <- paste0("SELECT ts, user_lang, region, latency_s FROM ", sch, ".latency_metrics WHERE ", drange, if(!is.null(lang)) " AND user_lang=$1 " else "", if(!is.null(region)) " AND region=$2 " else "", " ORDER BY ts;")
    q_dm  <- paste0("SELECT ts, user_lang, region, delta_theta_7d FROM ", sch, ".daily_metrics WHERE ", drange, if(!is.null(lang)) " AND user_lang=$1 " else "", if(!is.null(region)) " AND region=$2 " else "", ";")
    q_alerts_today <- paste0("SELECT alert_type FROM ", sch, ".alerts WHERE ts::date = CURRENT_DATE AND resolved=false;")
    q_anchor <- paste0("SELECT item_id, ROUND(delta_a_7d,3) AS delta_a, ROUND(delta_b_7d,3) AS delta_b, ROUND(delta_c_7d,3) AS delta_c FROM ", sch, ".irt_anchor_deltas WHERE ", drange, " ORDER BY GREATEST(ABS(delta_b_7d),ABS(delta_a_7d),ABS(delta_c_7d)) DESC LIMIT 50;")

    params <- list(); if(!is.null(lang)) params <- c(params, lang); if(!is.null(region)) params <- c(params, region)

    beh <- dbGetQuery(con, q_beh, params = params)
    lat <- dbGetQuery(con, q_lat, params = params)
    dm  <- dbGetQuery(con, q_dm, params = params)
    alr <- dbGetQuery(con, q_alerts_today)
    anc <- dbGetQuery(con, q_anchor)

    vals(list(beh=beh, lat=lat, dm=dm, alr=alr, anc=anc))
  }, ignoreInit = TRUE)

  observeEvent(TRUE, { # initial load
    shiny::updateActionButton(session, "reload", label = "Reload")
    shiny::isolate({ shiny::click("reload") })
  }, once = TRUE)

  output$kpi_dtheta <- renderUI({
    dm <- vals()$dm
    v <- if (nrow(dm)) mean(dm$delta_theta_7d, na.rm=TRUE) else NA
    lvl <- ifelse(is.na(v), "lo", ifelse(abs(v)>=0.1, "hi", ifelse(abs(v)>=0.05, "mid", "lo")))
    div(class=paste("card", lvl), h4("Δθ (7d)"), p(sprintf("%.3f", v)))
  })

  output$kpi_lastopt <- renderUI({
    beh <- vals()$beh
    v <- if (nrow(beh)) mean(beh$last_option_rate, na.rm=TRUE) else NA
    lvl <- ifelse(is.na(v), "lo", ifelse(v>=0.28, "hi", ifelse(v>=0.22, "mid", "lo")))
    div(class=paste("card", lvl), h4("Last Option Rate"), p(sprintf("%.1f%%", v*100)))
  })

  output$kpi_omit <- renderUI({
    beh <- vals()$beh
    v <- if (nrow(beh)) mean(beh$omit_rate, na.rm=TRUE) else NA
    lvl <- ifelse(is.na(v), "lo", ifelse(v>=0.12, "hi", ifelse(v>=0.08, "mid", "lo")))
    div(class=paste("card", lvl), h4("Omit Rate"), p(sprintf("%.1f%%", v*100)))
  })

  output$kpi_alerts <- renderUI({
    alr <- vals()$alr
    n <- if (nrow(alr)) nrow(alr) else 0
    lvl <- ifelse(n>=4, "hi", ifelse(n>=2, "mid", "lo"))
    div(class=paste("card", lvl), h4("Active Alerts (오늘)"), p(n))
  })

  output$narrative <- renderUI({
    anc <- vals()$anc
    hi_b <- if (nrow(anc)) sum(abs(anc$delta_b) > 0.35, na.rm=TRUE) else 0
    c_delta <- "n/a"
    if (nrow(anc)) {
      # proxy: use |delta_c| average as a narrative placeholder
      c_delta <- sprintf("%.3f", mean(abs(anc$delta_c), na.rm=TRUE))
    }
    kc_shift <- if (nrow(vals()$beh)) length(unique(paste(vals()$beh$user_lang, vals()$beh$region))) else 0
    HTML(sprintf("
      <div class='card'>
      <b>오늘의 진단</b>
      <ul>
        <li>Anchor Erosion: %s – Δb>0.35 항목 수: <b>%d</b></li>
        <li>Guessing Instability: %s – 평균 |Δc|: <b>%s</b></li>
        <li>Curriculum Shift: %s – 언어×지역 셀 변동 수: <b>%d</b></li>
      </ul>
      </div>",
      ifelse(hi_b>=5, "상", ifelse(hi_b>=2, "중", "하")),
      hi_b,
      ifelse(as.numeric(c_delta)>=0.06, "중~상", "하"),
      c_delta,
      ifelse(kc_shift>=6, "중", "하"),
      kc_shift
    ))
  })

  output$ts_lastopt <- renderPlot({
    beh <- vals()$beh
    validate(need(nrow(beh)>0, "데이터 없음"))
    ggplot(beh, aes(x=as.Date(ts), y=last_option_rate)) + geom_line() +
      labs(title="Last Option Rate (일별)", x=NULL, y="rate")
  })

  output$ts_latency <- renderPlot({
    lat <- vals()$lat
    validate(need(nrow(lat)>0, "데이터 없음"))
    ggplot(lat, aes(x=as.Date(ts), y=latency_s)) + geom_line() +
      labs(title="Median Latency (일별)", x=NULL, y="seconds")
  })

  output$tbl_anchor <- renderTable({
    vals()$anc
  })
}

shinyApp(ui, server)
