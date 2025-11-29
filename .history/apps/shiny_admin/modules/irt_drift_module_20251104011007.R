# IRT Drift Monitor - Shiny Dashboard Module
# To be integrated into existing Shiny Admin dashboard

library(shiny)
library(shinydashboard)
library(DBI)
library(dplyr)
library(ggplot2)
library(plotly)
library(DT)

# Module UI
irtDriftUI <- function(id) {
  ns <- NS(id)
  
  tabItem(
    tabName = "irt_drift",
    fluidRow(
      # Summary boxes
      valueBoxOutput(ns("box_items_analyzed"), width = 3),
      valueBoxOutput(ns("box_alerts_total"), width = 3),
      valueBoxOutput(ns("box_alerts_severe"), width = 3),
      valueBoxOutput(ns("box_anchor_stability"), width = 3)
    ),
    
    fluidRow(
      box(
        title = "Drift Detection Runs",
        width = 12,
        status = "primary",
        solidHeader = TRUE,
        selectInput(
          ns("run_selector"),
          "Select Run:",
          choices = NULL,
          width = "300px"
        ),
        textOutput(ns("run_info"))
      )
    ),
    
    fluidRow(
      box(
        title = "Parameter Drift Heatmap (Recent vs Baseline)",
        width = 12,
        status = "info",
        solidHeader = TRUE,
        plotlyOutput(ns("drift_heatmap"), height = "500px")
      )
    ),
    
    fluidRow(
      box(
        title = "12-Week Drift Trend",
        width = 6,
        status = "warning",
        solidHeader = TRUE,
        plotlyOutput(ns("drift_trend"), height = "350px")
      ),
      box(
        title = "Anchor Item Stability",
        width = 6,
        status = "success",
        solidHeader = TRUE,
        plotlyOutput(ns("anchor_stability_plot"), height = "350px")
      )
    ),
    
    fluidRow(
      box(
        title = "Drift Alerts",
        width = 12,
        status = "danger",
        solidHeader = TRUE,
        collapsible = TRUE,
        fluidRow(
          column(
            4,
            selectInput(
              ns("alert_severity_filter"),
              "Severity:",
              choices = c("All", "severe", "moderate", "minor"),
              selected = "All"
            )
          ),
          column(
            4,
            selectInput(
              ns("alert_resolved_filter"),
              "Status:",
              choices = c("All", "Unresolved", "Resolved"),
              selected = "Unresolved"
            )
          ),
          column(
            4,
            actionButton(
              ns("refresh_alerts"),
              "Refresh",
              icon = icon("refresh"),
              class = "btn-primary"
            )
          )
        ),
        DTOutput(ns("alerts_table"))
      )
    ),
    
    fluidRow(
      box(
        title = "Item Detail Comparison",
        width = 12,
        status = "primary",
        collapsible = TRUE,
        collapsed = TRUE,
        fluidRow(
          column(
            6,
            selectInput(
              ns("item_detail_selector"),
              "Select Item:",
              choices = NULL,
              width = "100%"
            )
          ),
          column(
            6,
            actionButton(
              ns("view_item_detail"),
              "View Details",
              icon = icon("search"),
              class = "btn-info"
            )
          )
        ),
        plotlyOutput(ns("item_param_evolution"), height = "300px"),
        verbatimTextOutput(ns("item_detail_info"))
      )
    )
  )
}

# Module Server
irtDriftServer <- function(id, db_config) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns
    
    # Reactive database connection
    con <- reactive({
      req(db_config$url)
      dbConnect(RPostgres::Postgres(), db_config$url)
    })
    
    # Load available runs
    runs <- reactive({
      req(con())
      tbl(con(), "drift_alerts") %>%
        distinct(run_id) %>%
        arrange(desc(run_id)) %>%
        collect()
    })
    
    observe({
      run_choices <- runs()$run_id
      updateSelectInput(session, "run_selector", choices = run_choices)
    })
    
    # Current run data
    current_run_id <- reactive({
      req(input$run_selector)
      input$run_selector
    })
    
    calibrations <- reactive({
      req(current_run_id())
      tbl(con(), "item_calibration") %>%
        filter(run_id == current_run_id()) %>%
        collect()
    })
    
    alerts <- reactive({
      req(current_run_id())
      input$refresh_alerts  # Trigger on refresh
      
      query <- tbl(con(), "drift_alerts") %>%
        filter(run_id == current_run_id())
      
      if (input$alert_severity_filter != "All") {
        query <- query %>% filter(severity == input$alert_severity_filter)
      }
      
      if (input$alert_resolved_filter == "Unresolved") {
        query <- query %>% filter(is.na(resolved_at))
      } else if (input$alert_resolved_filter == "Resolved") {
        query <- query %>% filter(!is.na(resolved_at))
      }
      
      query %>% collect()
    })
    
    items <- reactive({
      req(con())
      tbl(con(), "items") %>% collect()
    })
    
    # Value boxes
    output$box_items_analyzed <- renderValueBox({
      n <- nrow(calibrations())
      valueBox(
        n,
        "Items Analyzed",
        icon = icon("list"),
        color = "blue"
      )
    })
    
    output$box_alerts_total <- renderValueBox({
      n <- nrow(alerts())
      valueBox(
        n,
        "Total Alerts",
        icon = icon("exclamation-triangle"),
        color = "yellow"
      )
    })
    
    output$box_alerts_severe <- renderValueBox({
      n <- sum(alerts()$severity == "severe")
      color <- if (n > 0) "red" else "green"
      valueBox(
        n,
        "Severe Alerts",
        icon = icon("times-circle"),
        color = color
      )
    })
    
    output$box_anchor_stability <- renderValueBox({
      anchor_items <- items() %>% filter(is_anchor == TRUE)
      anchor_calibs <- calibrations() %>%
        filter(item_id %in% anchor_items$id)
      
      # Compute average |Δb| from baseline (stub: need baseline window)
      stability_score <- "N/A"
      color <- "light-blue"
      
      valueBox(
        stability_score,
        "Anchor Stability",
        icon = icon("anchor"),
        color = color
      )
    })
    
    # Run info
    output$run_info <- renderText({
      rid <- current_run_id()
      n_cal <- nrow(calibrations())
      n_alert <- nrow(alerts())
      
      paste0(
        "Run: ", rid, " | ",
        n_cal, " items calibrated | ",
        n_alert, " alerts"
      )
    })
    
    # Drift heatmap
    output$drift_heatmap <- renderPlotly({
      cal <- calibrations()
      if (nrow(cal) == 0) return(NULL)
      
      # Compute deltas (stub: need baseline window join)
      # For demo, show parameter distribution
      heatmap_data <- cal %>%
        select(item_id, a_hat, b_hat, c_hat) %>%
        pivot_longer(cols = c(a_hat, b_hat, c_hat), names_to = "param", values_to = "value")
      
      p <- ggplot(heatmap_data, aes(x = param, y = item_id, fill = value)) +
        geom_tile() +
        scale_fill_gradient2(low = "blue", mid = "white", high = "red", midpoint = 0) +
        labs(title = "Item Parameters (Recent Window)", x = "Parameter", y = "Item") +
        theme_minimal() +
        theme(axis.text.y = element_blank())
      
      ggplotly(p)
    })
    
    # 12-week trend (stub: needs historical run data)
    output$drift_trend <- renderPlotly({
      # Placeholder: load last 12 runs and aggregate alerts
      trend_data <- data.frame(
        week = 1:12,
        alerts = sample(5:20, 12, replace = TRUE)
      )
      
      p <- ggplot(trend_data, aes(x = week, y = alerts)) +
        geom_line(color = "steelblue", size = 1) +
        geom_point(color = "steelblue", size = 2) +
        labs(title = "Weekly Alert Count (Last 12 Weeks)", x = "Week", y = "Alerts") +
        theme_minimal()
      
      ggplotly(p)
    })
    
    # Anchor stability plot
    output$anchor_stability_plot <- renderPlotly({
      anchor_items <- items() %>% filter(is_anchor == TRUE)
      anchor_calibs <- calibrations() %>%
        filter(item_id %in% anchor_items$id)
      
      if (nrow(anchor_calibs) == 0) {
        return(plotly_empty())
      }
      
      # Stub: plot b_hat with CI for anchors
      p <- ggplot(anchor_calibs, aes(x = item_id, y = b_hat)) +
        geom_point(size = 3, color = "darkgreen") +
        geom_errorbar(aes(ymin = b_l95, ymax = b_u95), width = 0.2, color = "darkgreen") +
        coord_flip() +
        labs(title = "Anchor Item Difficulty (b) with 95% CI", x = "Item", y = "b") +
        theme_minimal()
      
      ggplotly(p)
    })
    
    # Alerts table
    output$alerts_table <- renderDT({
      alerts_display <- alerts() %>%
        left_join(items(), by = c("item_id" = "id")) %>%
        select(item_id, metric, value, threshold, severity, is_anchor, resolved_at) %>%
        mutate(
          resolved = if_else(is.na(resolved_at), "No", "Yes"),
          value = round(value, 3),
          threshold = round(threshold, 3)
        ) %>%
        select(-resolved_at)
      
      datatable(
        alerts_display,
        options = list(
          pageLength = 15,
          order = list(list(4, "desc"))  # Sort by severity
        ),
        rownames = FALSE,
        filter = "top"
      )
    })
    
    # Item detail selector
    observe({
      item_choices <- unique(calibrations()$item_id)
      updateSelectInput(session, "item_detail_selector", choices = item_choices)
    })
    
    # Item parameter evolution (stub: needs historical calibrations)
    output$item_param_evolution <- renderPlotly({
      req(input$view_item_detail)
      item_id <- isolate(input$item_detail_selector)
      if (is.null(item_id)) return(NULL)
      
      # Stub: plot historical a,b,c for this item
      historical_data <- data.frame(
        window = 1:5,
        a = rnorm(5, 1.0, 0.1),
        b = rnorm(5, 0.0, 0.15),
        c = rnorm(5, 0.2, 0.02)
      )
      
      plot_data <- historical_data %>%
        pivot_longer(cols = c(a, b, c), names_to = "param", values_to = "value")
      
      p <- ggplot(plot_data, aes(x = window, y = value, color = param)) +
        geom_line(size = 1) +
        geom_point(size = 2) +
        labs(title = paste("Parameter Evolution for Item", item_id), x = "Window", y = "Value") +
        theme_minimal()
      
      ggplotly(p)
    })
    
    # Item detail info
    output$item_detail_info <- renderText({
      req(input$view_item_detail)
      item_id <- isolate(input$item_detail_selector)
      if (is.null(item_id)) return("")
      
      item_info <- items() %>% filter(id == item_id)
      recent_cal <- calibrations() %>% filter(item_id == !!item_id)
      
      if (nrow(recent_cal) == 0) return("No calibration data for this item.")
      
      paste0(
        "Item: ", item_id, "\n",
        "Anchor: ", ifelse(item_info$is_anchor, "Yes", "No"), "\n",
        "Recent Parameters:\n",
        "  a = ", round(recent_cal$a_hat, 3), " [", round(recent_cal$a_l95, 3), ", ", round(recent_cal$a_u95, 3), "]\n",
        "  b = ", round(recent_cal$b_hat, 3), " [", round(recent_cal$b_l95, 3), ", ", round(recent_cal$b_u95, 3), "]\n",
        "  c = ", round(recent_cal$c_hat, 3), " [", round(recent_cal$c_l95, 3), ", ", round(recent_cal$c_u95, 3), "]\n",
        "Sample Size: ", recent_cal$n, "\n"
      )
    })
    
    # Cleanup
    onStop(function() {
      if (!is.null(con())) dbDisconnect(con())
    })
  })
}

# Example integration into main dashboard
# In your main server.R or app.R:
#
# irtDriftServer("irt_drift_module", reactive({
#   list(url = Sys.getenv("DATABASE_URL"))
# }))
#
# In your UI (dashboardSidebar):
# menuItem("IRT Drift Monitor", tabName = "irt_drift", icon = icon("chart-line"))
#
# In your dashboardBody:
# irtDriftUI("irt_drift_module")
