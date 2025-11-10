# UX Layer: Teacher & Admin Console

**Implementation Guide 13 of 14**

This guide covers the teacher/admin console implementation using R Shiny, parent portal, and administrative interfaces for managing students, classes, assessments, and platform settings.

---

## Table of Contents

1. [Overview](#overview)
2. [R Shiny Architecture](#r-shiny-architecture)
3. [Teacher Dashboard](#teacher-dashboard)
4. [Class Management](#class-management)
5. [Student Monitoring](#student-monitoring)
6. [Item Bank Management](#item-bank-management)
7. [Reports & Analytics](#reports--analytics)
8. [Admin Console](#admin-console)
9. [Parent Portal](#parent-portal)

---

## Overview

### Goals

The teacher and admin interfaces aim to:

- **Efficiency**: Enable teachers to manage classes and monitor students quickly
- **Insights**: Provide actionable analytics on student performance
- **Flexibility**: Allow customization of assessments and curricula
- **Control**: Give admins platform-wide oversight and configuration
- **Communication**: Facilitate parent-teacher-student collaboration

### Technology Stack

- **R Shiny**: Interactive web applications for dashboards and analytics
- **shinydashboard**: Dashboard layout framework
- **DT**: Interactive DataTables
- **plotly**: Interactive visualizations
- **shinyWidgets**: Enhanced UI widgets
- **pool**: Database connection pooling
- **API Integration**: REST API calls to Python/FastAPI backend

---

## R Shiny Architecture

### Application Structure

```
apps/
├── shiny-teacher/
│   ├── app.R                 # Main Shiny app entry point
│   ├── global.R              # Global variables and functions
│   ├── ui.R                  # UI definition
│   ├── server.R              # Server logic
│   ├── modules/
│   │   ├── mod_dashboard.R
│   │   ├── mod_students.R
│   │   ├── mod_assessments.R
│   │   ├── mod_reports.R
│   │   └── mod_settings.R
│   ├── utils/
│   │   ├── api_client.R      # API communication
│   │   ├── data_processing.R
│   │   └── plotting.R
│   └── www/
│       ├── custom.css
│       └── custom.js
└── shiny-admin/
    └── (similar structure)
```

### Global Configuration

```r
# global.R
library(shiny)
library(shinydashboard)
library(DT)
library(plotly)
library(dplyr)
library(tidyr)
library(ggplot2)
library(httr)
library(jsonlite)
library(pool)
library(shinyWidgets)

# API Configuration
API_BASE_URL <- Sys.getenv("API_BASE_URL", "http://localhost:8000")

# Database Connection Pool
db_pool <- dbPool(
  drv = RPostgres::Postgres(),
  dbname = Sys.getenv("DB_NAME", "dreamseed"),
  host = Sys.getenv("DB_HOST", "localhost"),
  port = as.integer(Sys.getenv("DB_PORT", 5432)),
  user = Sys.getenv("DB_USER"),
  password = Sys.getenv("DB_PASSWORD")
)

# Theme Colors
DREAMSEED_COLORS <- list(
  blue = "#0066CC",
  green = "#00CC66",
  orange = "#FF9933",
  purple = "#9933FF",
  red = "#CC0000"
)

# Helper function to make API calls
api_call <- function(endpoint, method = "GET", body = NULL, token = NULL) {
  url <- paste0(API_BASE_URL, endpoint)

  headers <- c(
    "Content-Type" = "application/json"
  )

  if (!is.null(token)) {
    headers <- c(headers, Authorization = paste("Bearer", token))
  }

  response <- switch(method,
    GET = GET(url, add_headers(.headers = headers)),
    POST = POST(url, body = toJSON(body, auto_unbox = TRUE),
                add_headers(.headers = headers)),
    PUT = PUT(url, body = toJSON(body, auto_unbox = TRUE),
              add_headers(.headers = headers)),
    DELETE = DELETE(url, add_headers(.headers = headers))
  )

  if (http_error(response)) {
    stop(sprintf("API Error: %s", content(response, "text")))
  }

  content(response, "parsed")
}

# Clean up on exit
onStop(function() {
  poolClose(db_pool)
})
```

### Main App Entry Point

```r
# app.R
source("global.R")
source("ui.R")
source("server.R")

# Run the application
shinyApp(ui = ui, server = server)
```

### UI Definition

```r
# ui.R
ui <- dashboardPage(
  skin = "blue",

  # Header
  dashboardHeader(
    title = "DreamSeed Teacher Console",

    # Notifications
    dropdownMenu(
      type = "notifications",
      icon = icon("bell"),
      badgeStatus = "warning",
      notificationItem(
        text = "5 students need attention",
        icon = icon("users"),
        status = "warning"
      ),
      notificationItem(
        text = "New assessment results available",
        icon = icon("chart-line"),
        status = "success"
      )
    ),

    # User menu
    dropdownMenu(
      type = "messages",
      icon = icon("user"),
      badgeStatus = NULL,
      messageItem(
        from = uiOutput("user_name"),
        message = "Teacher Profile",
        icon = icon("user-circle")
      )
    )
  ),

  # Sidebar
  dashboardSidebar(
    sidebarMenu(
      id = "sidebar_menu",
      menuItem("Dashboard", tabName = "dashboard", icon = icon("dashboard")),
      menuItem("My Classes", tabName = "classes", icon = icon("users")),
      menuItem("Students", tabName = "students", icon = icon("user-graduate")),
      menuItem("Assessments", tabName = "assessments", icon = icon("clipboard-check")),
      menuItem("Item Bank", tabName = "items", icon = icon("database")),
      menuItem("Reports", tabName = "reports", icon = icon("chart-bar")),
      menuItem("Settings", tabName = "settings", icon = icon("cog"))
    )
  ),

  # Body
  dashboardBody(
    # Custom CSS
    tags$head(
      tags$link(rel = "stylesheet", type = "text/css", href = "custom.css")
    ),

    tabItems(
      # Dashboard tab
      tabItem(
        tabName = "dashboard",
        mod_dashboard_ui("dashboard")
      ),

      # Classes tab
      tabItem(
        tabName = "classes",
        mod_classes_ui("classes")
      ),

      # Students tab
      tabItem(
        tabName = "students",
        mod_students_ui("students")
      ),

      # Assessments tab
      tabItem(
        tabName = "assessments",
        mod_assessments_ui("assessments")
      ),

      # Item Bank tab
      tabItem(
        tabName = "items",
        mod_items_ui("items")
      ),

      # Reports tab
      tabItem(
        tabName = "reports",
        mod_reports_ui("reports")
      ),

      # Settings tab
      tabItem(
        tabName = "settings",
        mod_settings_ui("settings")
      )
    )
  )
)
```

---

## Teacher Dashboard

### Dashboard Module UI

```r
# modules/mod_dashboard.R
mod_dashboard_ui <- function(id) {
  ns <- NS(id)

  tagList(
    fluidRow(
      # Summary boxes
      valueBoxOutput(ns("total_students"), width = 3),
      valueBoxOutput(ns("active_classes"), width = 3),
      valueBoxOutput(ns("avg_performance"), width = 3),
      valueBoxOutput(ns("at_risk_students"), width = 3)
    ),

    fluidRow(
      # Recent activity
      box(
        title = "Recent Assessment Results",
        status = "primary",
        solidHeader = TRUE,
        width = 8,
        plotlyOutput(ns("recent_assessments_plot"), height = 300)
      ),

      # Quick actions
      box(
        title = "Quick Actions",
        status = "info",
        solidHeader = TRUE,
        width = 4,
        actionButton(ns("btn_new_assessment"), "Create Assessment",
                     icon = icon("plus"), class = "btn-block btn-primary"),
        br(),
        actionButton(ns("btn_view_reports"), "View Reports",
                     icon = icon("chart-bar"), class = "btn-block btn-success"),
        br(),
        actionButton(ns("btn_manage_students"), "Manage Students",
                     icon = icon("users"), class = "btn-block btn-info")
      )
    ),

    fluidRow(
      # Class performance
      box(
        title = "Class Performance Overview",
        status = "success",
        solidHeader = TRUE,
        width = 6,
        plotlyOutput(ns("class_performance_plot"), height = 300)
      ),

      # Students needing attention
      box(
        title = "Students Needing Attention",
        status = "warning",
        solidHeader = TRUE,
        width = 6,
        DTOutput(ns("at_risk_table"))
      )
    )
  )
}

mod_dashboard_server <- function(id, session_data) {
  moduleServer(id, function(input, output, session) {

    # Summary metrics
    output$total_students <- renderValueBox({
      students <- api_call(
        sprintf("/api/teachers/%s/students", session_data$user_id),
        token = session_data$token
      )

      valueBox(
        length(students),
        "Total Students",
        icon = icon("user-graduate"),
        color = "blue"
      )
    })

    output$active_classes <- renderValueBox({
      classes <- api_call(
        sprintf("/api/teachers/%s/classes", session_data$user_id),
        token = session_data$token
      )

      valueBox(
        length(classes),
        "Active Classes",
        icon = icon("users"),
        color = "green"
      )
    })

    output$avg_performance <- renderValueBox({
      performance <- api_call(
        sprintf("/api/teachers/%s/performance", session_data$user_id),
        token = session_data$token
      )

      valueBox(
        sprintf("%.1f%%", performance$average * 100),
        "Avg Performance",
        icon = icon("chart-line"),
        color = "yellow"
      )
    })

    output$at_risk_students <- renderValueBox({
      at_risk <- api_call(
        sprintf("/api/teachers/%s/at-risk", session_data$user_id),
        token = session_data$token
      )

      valueBox(
        length(at_risk),
        "At-Risk Students",
        icon = icon("exclamation-triangle"),
        color = "red"
      )
    })

    # Recent assessments plot
    output$recent_assessments_plot <- renderPlotly({
      data <- api_call(
        sprintf("/api/teachers/%s/recent-assessments", session_data$user_id),
        token = session_data$token
      )

      df <- do.call(rbind, lapply(data, as.data.frame))

      plot_ly(df, x = ~date, y = ~avg_score, type = 'scatter', mode = 'lines+markers',
              name = 'Average Score', line = list(color = DREAMSEED_COLORS$blue)) %>%
        add_trace(y = ~median_score, name = 'Median Score',
                  line = list(color = DREAMSEED_COLORS$green)) %>%
        layout(
          title = "",
          xaxis = list(title = "Date"),
          yaxis = list(title = "Score", range = c(0, 100)),
          hovermode = "x unified"
        )
    })

    # Class performance plot
    output$class_performance_plot <- renderPlotly({
      data <- api_call(
        sprintf("/api/teachers/%s/class-performance", session_data$user_id),
        token = session_data$token
      )

      df <- do.call(rbind, lapply(data, as.data.frame))

      plot_ly(df, x = ~class_name, y = ~avg_score, type = 'bar',
              marker = list(color = DREAMSEED_COLORS$blue)) %>%
        layout(
          title = "",
          xaxis = list(title = "Class"),
          yaxis = list(title = "Average Score", range = c(0, 100))
        )
    })

    # At-risk students table
    output$at_risk_table <- renderDT({
      data <- api_call(
        sprintf("/api/teachers/%s/at-risk", session_data$user_id),
        token = session_data$token
      )

      df <- do.call(rbind, lapply(data, as.data.frame))

      datatable(
        df[, c("name", "class", "recent_score", "reason")],
        options = list(
          pageLength = 5,
          dom = 't'
        ),
        rownames = FALSE,
        colnames = c("Student", "Class", "Recent Score", "Reason")
      )
    })

    # Quick action handlers
    observeEvent(input$btn_new_assessment, {
      updateTabItems(session, "sidebar_menu", "assessments")
    })

    observeEvent(input$btn_view_reports, {
      updateTabItems(session, "sidebar_menu", "reports")
    })

    observeEvent(input$btn_manage_students, {
      updateTabItems(session, "sidebar_menu", "students")
    })
  })
}
```

---

## Class Management

### Classes Module

```r
# modules/mod_classes.R
mod_classes_ui <- function(id) {
  ns <- NS(id)

  tagList(
    fluidRow(
      box(
        title = "My Classes",
        status = "primary",
        solidHeader = TRUE,
        width = 12,
        actionButton(ns("btn_new_class"), "Create New Class",
                     icon = icon("plus"), class = "btn-primary"),
        br(), br(),
        DTOutput(ns("classes_table"))
      )
    ),

    # Class details modal
    bsModal(
      id = ns("class_modal"),
      title = "Class Details",
      trigger = NULL,
      size = "large",

      fluidRow(
        column(
          width = 6,
          h4("Class Information"),
          textInput(ns("class_name"), "Class Name", ""),
          textInput(ns("class_grade"), "Grade Level", ""),
          textInput(ns("class_subject"), "Subject", ""),
          textAreaInput(ns("class_description"), "Description", "", rows = 3)
        ),
        column(
          width = 6,
          h4("Schedule"),
          dateInput(ns("class_start_date"), "Start Date"),
          dateInput(ns("class_end_date"), "End Date"),
          textInput(ns("class_meeting_times"), "Meeting Times", "")
        )
      ),

      footer = tagList(
        modalButton("Cancel"),
        actionButton(ns("btn_save_class"), "Save", class = "btn-primary")
      )
    )
  )
}

mod_classes_server <- function(id, session_data) {
  moduleServer(id, function(input, output, session) {

    # Reactive value for class data
    classes_data <- reactiveVal()

    # Load classes
    observe({
      data <- api_call(
        sprintf("/api/teachers/%s/classes", session_data$user_id),
        token = session_data$token
      )
      classes_data(data)
    })

    # Classes table
    output$classes_table <- renderDT({
      req(classes_data())

      df <- do.call(rbind, lapply(classes_data(), as.data.frame))

      df$actions <- sprintf(
        '<button class="btn btn-sm btn-primary" onclick="Shiny.setInputValue(\'%s\', \'%s\')">View</button>
         <button class="btn btn-sm btn-info" onclick="Shiny.setInputValue(\'%s\', \'%s\')">Edit</button>',
        session$ns("view_class"), df$id,
        session$ns("edit_class"), df$id
      )

      datatable(
        df[, c("name", "grade", "subject", "student_count", "avg_performance", "actions")],
        escape = FALSE,
        options = list(
          pageLength = 10,
          dom = 'Bfrtip',
          buttons = c('copy', 'csv', 'excel')
        ),
        rownames = FALSE,
        colnames = c("Class Name", "Grade", "Subject", "Students", "Avg Performance", "Actions")
      )
    })

    # Create new class
    observeEvent(input$btn_new_class, {
      # Clear form
      updateTextInput(session, "class_name", value = "")
      updateTextInput(session, "class_grade", value = "")
      updateTextInput(session, "class_subject", value = "")
      updateTextAreaInput(session, "class_description", value = "")

      toggleModal(session, "class_modal", toggle = "open")
    })

    # Save class
    observeEvent(input$btn_save_class, {
      class_data <- list(
        name = input$class_name,
        grade = input$class_grade,
        subject = input$class_subject,
        description = input$class_description,
        start_date = as.character(input$class_start_date),
        end_date = as.character(input$class_end_date),
        meeting_times = input$class_meeting_times,
        teacher_id = session_data$user_id
      )

      tryCatch({
        api_call(
          "/api/classes",
          method = "POST",
          body = class_data,
          token = session_data$token
        )

        toggleModal(session, "class_modal", toggle = "close")
        showNotification("Class created successfully!", type = "message")

        # Refresh classes
        classes_data(api_call(
          sprintf("/api/teachers/%s/classes", session_data$user_id),
          token = session_data$token
        ))
      }, error = function(e) {
        showNotification(paste("Error:", e$message), type = "error")
      })
    })
  })
}
```

---

## Student Monitoring

### Student Profile View

```r
# modules/mod_students.R
mod_students_ui <- function(id) {
  ns <- NS(id)

  tagList(
    fluidRow(
      box(
        title = "Student List",
        status = "primary",
        solidHeader = TRUE,
        width = 12,

        # Filters
        fluidRow(
          column(4, selectInput(ns("filter_class"), "Filter by Class", choices = NULL)),
          column(4, selectInput(ns("filter_status"), "Filter by Status",
                                choices = c("All", "On Track", "At Risk", "Struggling"))),
          column(4, textInput(ns("search_student"), "Search Student", ""))
        ),

        DTOutput(ns("students_table"))
      )
    ),

    # Student detail modal
    bsModal(
      id = ns("student_modal"),
      title = uiOutput(ns("student_modal_title")),
      trigger = NULL,
      size = "large",

      tabsetPanel(
        tabPanel(
          "Overview",
          br(),
          fluidRow(
            column(6, uiOutput(ns("student_info"))),
            column(6, plotlyOutput(ns("student_ability_trend")))
          )
        ),
        tabPanel(
          "Performance",
          br(),
          plotlyOutput(ns("student_performance_plot")),
          br(),
          DTOutput(ns("student_assessments_table"))
        ),
        tabPanel(
          "Strengths & Weaknesses",
          br(),
          plotlyOutput(ns("student_topics_radar"))
        ),
        tabPanel(
          "AI Tutor Sessions",
          br(),
          DTOutput(ns("student_tutor_sessions"))
        )
      )
    )
  )
}

mod_students_server <- function(id, session_data) {
  moduleServer(id, function(input, output, session) {

    # Load classes for filter
    observe({
      classes <- api_call(
        sprintf("/api/teachers/%s/classes", session_data$user_id),
        token = session_data$token
      )

      class_choices <- c("All Classes" = "all")
      for (cls in classes) {
        class_choices[cls$name] <- cls$id
      }

      updateSelectInput(session, "filter_class", choices = class_choices)
    })

    # Students table
    output$students_table <- renderDT({
      students <- api_call(
        sprintf("/api/teachers/%s/students", session_data$user_id),
        token = session_data$token
      )

      df <- do.call(rbind, lapply(students, as.data.frame))

      # Apply filters
      if (input$filter_class != "all") {
        df <- df[df$class_id == input$filter_class, ]
      }

      if (input$filter_status != "All") {
        df <- df[df$status == input$filter_status, ]
      }

      if (nzchar(input$search_student)) {
        df <- df[grepl(input$search_student, df$name, ignore.case = TRUE), ]
      }

      # Add action buttons
      df$actions <- sprintf(
        '<button class="btn btn-sm btn-primary" onclick="Shiny.setInputValue(\'%s\', \'%s\')">View Profile</button>',
        session$ns("view_student"), df$id
      )

      datatable(
        df[, c("name", "class_name", "current_ability", "recent_score", "status", "actions")],
        escape = FALSE,
        options = list(pageLength = 15),
        rownames = FALSE,
        colnames = c("Student", "Class", "Ability (θ)", "Recent Score", "Status", "Actions")
      ) %>%
        formatStyle(
          'status',
          backgroundColor = styleEqual(
            c('On Track', 'At Risk', 'Struggling'),
            c('#d4edda', '#fff3cd', '#f8d7da')
          )
        )
    })

    # View student details
    observeEvent(input$view_student, {
      student_id <- input$view_student

      student <- api_call(
        sprintf("/api/students/%s", student_id),
        token = session_data$token
      )

      output$student_modal_title <- renderUI({
        h3(student$name)
      })

      output$student_info <- renderUI({
        tagList(
          p(strong("Class:"), student$class_name),
          p(strong("Current Ability (θ):"), sprintf("%.2f", student$current_ability)),
          p(strong("Assessments Completed:"), student$assessments_completed),
          p(strong("Study Time (This Month):"), sprintf("%d hours", student$study_hours)),
          p(strong("Status:"),
            span(student$status,
                 class = ifelse(student$status == "On Track", "badge badge-success", "badge badge-warning")))
        )
      })

      output$student_ability_trend <- renderPlotly({
        history <- api_call(
          sprintf("/api/students/%s/ability-history", student_id),
          token = session_data$token
        )

        df <- do.call(rbind, lapply(history, as.data.frame))

        plot_ly(df, x = ~date, y = ~ability, type = 'scatter', mode = 'lines+markers',
                line = list(color = DREAMSEED_COLORS$blue)) %>%
          layout(
            title = "Ability Growth Over Time",
            xaxis = list(title = "Date"),
            yaxis = list(title = "Ability (θ)")
          )
      })

      output$student_performance_plot <- renderPlotly({
        performance <- api_call(
          sprintf("/api/students/%s/performance", student_id),
          token = session_data$token
        )

        df <- do.call(rbind, lapply(performance, as.data.frame))

        plot_ly(df, x = ~assessment_date, y = ~score, type = 'bar',
                marker = list(color = DREAMSEED_COLORS$green)) %>%
          layout(
            title = "Assessment Scores",
            xaxis = list(title = "Assessment"),
            yaxis = list(title = "Score", range = c(0, 100))
          )
      })

      toggleModal(session, "student_modal", toggle = "open")
    })
  })
}
```

---

## Item Bank Management

### Item Bank Module

```r
# modules/mod_items.R
mod_items_ui <- function(id) {
  ns <- NS(id)

  tagList(
    fluidRow(
      box(
        title = "Item Bank",
        status = "primary",
        solidHeader = TRUE,
        width = 12,

        fluidRow(
          column(3, actionButton(ns("btn_add_item"), "Add New Item",
                                 icon = icon("plus"), class = "btn-primary btn-block")),
          column(3, selectInput(ns("filter_subject"), "Subject", choices = NULL)),
          column(3, selectInput(ns("filter_difficulty"), "Difficulty",
                                choices = c("All", "Easy", "Medium", "Hard"))),
          column(3, textInput(ns("search_item"), "Search", ""))
        ),

        br(),
        DTOutput(ns("items_table"))
      )
    ),

    # Item editor modal
    bsModal(
      id = ns("item_modal"),
      title = "Item Editor",
      trigger = NULL,
      size = "large",

      fluidRow(
        column(
          width = 8,
          textAreaInput(ns("item_content"), "Question Content (supports LaTeX)", "", rows = 4,
                        placeholder = "e.g., What is $\\\\int x^2 dx$?"),

          h5("Answer Options"),
          textInput(ns("option_a"), "Option A", ""),
          textInput(ns("option_b"), "Option B", ""),
          textInput(ns("option_c"), "Option C", ""),
          textInput(ns("option_d"), "Option D", ""),

          radioButtons(ns("correct_answer"), "Correct Answer",
                       choices = c("A", "B", "C", "D"), inline = TRUE)
        ),
        column(
          width = 4,
          selectInput(ns("item_subject"), "Subject", choices = NULL),
          selectInput(ns("item_topic"), "Topic", choices = NULL),
          numericInput(ns("item_difficulty"), "Difficulty (0-1)", value = 0.5,
                       min = 0, max = 1, step = 0.1),
          numericInput(ns("item_discrimination"), "Discrimination", value = 1.0,
                       min = 0, max = 3, step = 0.1),
          numericInput(ns("item_guessing"), "Guessing (c)", value = 0.25,
                       min = 0, max = 0.5, step = 0.05),

          checkboxInput(ns("item_active"), "Active", value = TRUE)
        )
      ),

      footer = tagList(
        modalButton("Cancel"),
        actionButton(ns("btn_save_item"), "Save Item", class = "btn-primary")
      )
    )
  )
}

mod_items_server <- function(id, session_data) {
  moduleServer(id, function(input, output, session) {

    # Load items
    items_data <- reactiveVal()

    observe({
      items <- api_call(
        "/api/items",
        token = session_data$token
      )
      items_data(items)
    })

    # Items table
    output$items_table <- renderDT({
      req(items_data())

      df <- do.call(rbind, lapply(items_data(), as.data.frame))

      # Apply filters
      if (input$filter_subject != "All") {
        df <- df[df$subject == input$filter_subject, ]
      }

      df$actions <- sprintf(
        '<button class="btn btn-sm btn-info" onclick="Shiny.setInputValue(\'%s\', \'%s\')">Edit</button>
         <button class="btn btn-sm btn-danger" onclick="Shiny.setInputValue(\'%s\', \'%s\')">Delete</button>',
        session$ns("edit_item"), df$id,
        session$ns("delete_item"), df$id
      )

      datatable(
        df[, c("content_preview", "subject", "topic", "difficulty", "discrimination", "active", "actions")],
        escape = FALSE,
        options = list(pageLength = 20),
        rownames = FALSE,
        colnames = c("Question", "Subject", "Topic", "Difficulty", "Discrimination", "Active", "Actions")
      )
    })

    # Save item
    observeEvent(input$btn_save_item, {
      item_data <- list(
        content = input$item_content,
        options = list(
          input$option_a,
          input$option_b,
          input$option_c,
          input$option_d
        ),
        correct_answer = match(input$correct_answer, c("A", "B", "C", "D")) - 1,
        subject = input$item_subject,
        topic = input$item_topic,
        difficulty = input$item_difficulty,
        discrimination = input$item_discrimination,
        guessing = input$item_guessing,
        active = input$item_active
      )

      tryCatch({
        api_call(
          "/api/items",
          method = "POST",
          body = item_data,
          token = session_data$token
        )

        toggleModal(session, "item_modal", toggle = "close")
        showNotification("Item saved successfully!", type = "message")

        # Refresh items
        items_data(api_call("/api/items", token = session_data$token))
      }, error = function(e) {
        showNotification(paste("Error:", e$message), type = "error")
      })
    })
  })
}
```

---

## Reports & Analytics

### Reports Module

```r
# modules/mod_reports.R
mod_reports_ui <- function(id) {
  ns <- NS(id)

  tagList(
    fluidRow(
      box(
        title = "Report Generator",
        status = "primary",
        solidHeader = TRUE,
        width = 12,

        fluidRow(
          column(3, selectInput(ns("report_type"), "Report Type",
                                choices = c("Class Performance", "Student Progress",
                                            "Item Analysis", "Comparative Analysis"))),
          column(3, selectInput(ns("report_class"), "Class", choices = NULL)),
          column(3, dateRangeInput(ns("report_dates"), "Date Range")),
          column(3, br(), actionButton(ns("btn_generate"), "Generate Report",
                                       class = "btn-primary btn-block"))
        )
      )
    ),

    fluidRow(
      box(
        title = "Report Output",
        status = "success",
        solidHeader = TRUE,
        width = 12,
        collapsible = TRUE,

        downloadButton(ns("download_pdf"), "Download PDF", class = "btn-info"),
        downloadButton(ns("download_excel"), "Download Excel", class = "btn-success"),

        br(), br(),
        uiOutput(ns("report_content"))
      )
    )
  )
}

mod_reports_server <- function(id, session_data) {
  moduleServer(id, function(input, output, session) {

    # Generate report
    report_data <- reactiveVal()

    observeEvent(input$btn_generate, {
      withProgress(message = 'Generating report...', value = 0, {

        incProgress(0.3, detail = "Fetching data...")

        data <- api_call(
          "/api/reports/generate",
          method = "POST",
          body = list(
            type = input$report_type,
            class_id = input$report_class,
            start_date = as.character(input$report_dates[1]),
            end_date = as.character(input$report_dates[2])
          ),
          token = session_data$token
        )

        incProgress(0.5, detail = "Processing...")

        report_data(data)

        incProgress(1, detail = "Complete!")
      })

      showNotification("Report generated successfully!", type = "message")
    })

    # Render report
    output$report_content <- renderUI({
      req(report_data())

      data <- report_data()

      tagList(
        h3(data$title),
        p(sprintf("Generated on: %s", Sys.Date())),
        hr(),

        # Summary statistics
        fluidRow(
          valueBox(data$total_students, "Students", icon = icon("users"), color = "blue", width = 3),
          valueBox(sprintf("%.1f%%", data$avg_score), "Avg Score", icon = icon("chart-line"), color = "green", width = 3),
          valueBox(data$assessments_count, "Assessments", icon = icon("clipboard"), color = "yellow", width = 3),
          valueBox(sprintf("%.2f", data$avg_ability), "Avg Ability", icon = icon("brain"), color = "purple", width = 3)
        ),

        # Charts
        plotlyOutput(session$ns("report_chart_1")),
        plotlyOutput(session$ns("report_chart_2"))
      )
    })
  })
}
```

---

## Admin Console

### Admin Dashboard

```r
# Admin-specific features
mod_admin_ui <- function(id) {
  ns <- NS(id)

  tagList(
    fluidRow(
      valueBoxOutput(ns("total_users"), width = 3),
      valueBoxOutput(ns("total_assessments"), width = 3),
      valueBoxOutput(ns("system_health"), width = 3),
      valueBoxOutput(ns("storage_usage"), width = 3)
    ),

    fluidRow(
      box(
        title = "Platform Usage",
        status = "primary",
        solidHeader = TRUE,
        width = 8,
        plotlyOutput(ns("usage_trend"))
      ),

      box(
        title = "System Alerts",
        status = "warning",
        solidHeader = TRUE,
        width = 4,
        uiOutput(ns("system_alerts"))
      )
    ),

    fluidRow(
      tabBox(
        title = "Administration",
        width = 12,

        tabPanel(
          "Users",
          DTOutput(ns("users_table")),
          actionButton(ns("btn_add_user"), "Add User", icon = icon("plus"))
        ),

        tabPanel(
          "Schools",
          DTOutput(ns("schools_table")),
          actionButton(ns("btn_add_school"), "Add School", icon = icon("plus"))
        ),

        tabPanel(
          "Settings",
          h4("Platform Configuration"),
          checkboxInput(ns("maintenance_mode"), "Maintenance Mode", FALSE),
          checkboxInput(ns("registration_enabled"), "Allow New Registrations", TRUE),
          numericInput(ns("max_session_duration"), "Max Session Duration (minutes)",
                       value = 120, min = 30, max = 480),
          actionButton(ns("btn_save_settings"), "Save Settings", class = "btn-primary")
        )
      )
    )
  )
}
```

---

## Parent Portal

### Parent Dashboard (Simplified)

```r
# modules/mod_parent.R
mod_parent_ui <- function(id) {
  ns <- NS(id)

  tagList(
    fluidRow(
      box(
        title = "My Children",
        status = "primary",
        solidHeader = TRUE,
        width = 12,
        selectInput(ns("selected_child"), "Select Child", choices = NULL),

        fluidRow(
          valueBoxOutput(ns("child_current_ability"), width = 4),
          valueBoxOutput(ns("child_recent_score"), width = 4),
          valueBoxOutput(ns("child_study_time"), width = 4)
        )
      )
    ),

    fluidRow(
      box(
        title = "Progress Overview",
        status = "success",
        solidHeader = TRUE,
        width = 8,
        plotlyOutput(ns("child_progress_chart"))
      ),

      box(
        title = "Recent Activity",
        status = "info",
        solidHeader = TRUE,
        width = 4,
        uiOutput(ns("child_recent_activity"))
      )
    ),

    fluidRow(
      box(
        title = "Strengths & Areas for Improvement",
        status = "warning",
        solidHeader = TRUE,
        width = 12,
        plotlyOutput(ns("child_topics_chart"))
      )
    )
  )
}

mod_parent_server <- function(id, session_data) {
  moduleServer(id, function(input, output, session) {

    # Load children
    observe({
      children <- api_call(
        sprintf("/api/parents/%s/children", session_data$user_id),
        token = session_data$token
      )

      child_choices <- setNames(
        sapply(children, function(x) x$id),
        sapply(children, function(x) x$name)
      )

      updateSelectInput(session, "selected_child", choices = child_choices)
    })

    # Child metrics
    output$child_current_ability <- renderValueBox({
      req(input$selected_child)

      child <- api_call(
        sprintf("/api/students/%s", input$selected_child),
        token = session_data$token
      )

      valueBox(
        sprintf("%.2f", child$current_ability),
        "Current Ability (θ)",
        icon = icon("brain"),
        color = "purple"
      )
    })

    output$child_recent_score <- renderValueBox({
      req(input$selected_child)

      child <- api_call(
        sprintf("/api/students/%s", input$selected_child),
        token = session_data$token
      )

      valueBox(
        sprintf("%d%%", child$recent_score),
        "Recent Score",
        icon = icon("chart-line"),
        color = "green"
      )
    })

    output$child_study_time <- renderValueBox({
      req(input$selected_child)

      child <- api_call(
        sprintf("/api/students/%s", input$selected_child),
        token = session_data$token
      )

      valueBox(
        sprintf("%d hrs", child$study_hours_month),
        "Study Time (This Month)",
        icon = icon("clock"),
        color = "blue"
      )
    })

    # Progress chart
    output$child_progress_chart <- renderPlotly({
      req(input$selected_child)

      history <- api_call(
        sprintf("/api/students/%s/ability-history", input$selected_child),
        token = session_data$token
      )

      df <- do.call(rbind, lapply(history, as.data.frame))

      plot_ly(df, x = ~date, y = ~ability, type = 'scatter', mode = 'lines+markers',
              line = list(color = DREAMSEED_COLORS$blue)) %>%
        layout(
          title = "Ability Growth",
          xaxis = list(title = "Date"),
          yaxis = list(title = "Ability (θ)")
        )
    })
  })
}
```

---

## Best Practices

### 1. R Shiny Performance

- **Use `reactiveVal()` and `observe()`**: For efficient reactive programming
- **Database Connection Pooling**: Use `pool` package to manage connections
- **Async Operations**: Use `future` and `promises` for long-running tasks
- **Caching**: Cache API responses to reduce load

### 2. Security

- **Authentication**: Validate tokens on every API call
- **Authorization**: Check user roles before rendering sensitive UI
- **Input Validation**: Sanitize all user inputs
- **HTTPS Only**: Deploy with SSL/TLS

### 3. User Experience

- **Loading Indicators**: Show progress bars for long operations
- **Error Handling**: Display user-friendly error messages
- **Responsive Tables**: Use DT with pagination and search
- **Export Options**: Provide PDF, Excel, CSV downloads

### 4. API Integration

- **Error Handling**: Gracefully handle API failures
- **Retry Logic**: Implement exponential backoff for failed requests
- **Rate Limiting**: Respect API rate limits
- **Logging**: Log all API calls for debugging

---

## Deployment

### Docker Configuration

```dockerfile
# Dockerfile for Shiny Teacher Console
FROM rocker/shiny:4.3.1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev

# Install R packages
RUN R -e "install.packages(c('shiny', 'shinydashboard', 'DT', 'plotly', \
    'dplyr', 'tidyr', 'ggplot2', 'httr', 'jsonlite', 'pool', \
    'RPostgres', 'shinyWidgets', 'shinyBS'))"

# Copy app files
COPY apps/shiny-teacher /srv/shiny-server/teacher

# Expose port
EXPOSE 3838

# Run app
CMD ["/usr/bin/shiny-server"]
```

### Environment Variables

```bash
# .env for Shiny apps
API_BASE_URL=https://api.dreamseed.ai
DB_HOST=postgres.dreamseed.ai
DB_PORT=5432
DB_NAME=dreamseed
DB_USER=shiny_user
DB_PASSWORD=<secure_password>
```

---

## Next Steps

Continue to:

- **[Guide 14: Accessibility & Performance](./14-ux-accessibility-performance.md)** - WCAG compliance and optimization

---

**Last Updated**: November 9, 2025  
**Version**: 1.0  
**Author**: DreamSeedAI Development Team
