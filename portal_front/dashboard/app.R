# Admin Dashboard (Shiny) with JWT/OIDC reverse-proxy claims and org/role data filtering
# Features:
# - Menus: Cohort Overview / IRT Calib / A/B Lab / Churn Monitor / Content Bank
# - AuthZ: Trusts verified claims injected by reverse proxy (e.g., X-User, X-Org-Id, X-Roles)
# - Data filtering per org/role
# - Performance: Arrow-backed datasets + DT (server-side) + Plotly interactivity

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
# Claims helpers (from reverse proxy headers)
# ---------------------------
parse_claims <- function(session) {
  req <- session$request
  get_header <- function(name, default = "") {
    # Convert header-style to Shiny's request naming (HTTP_...)
    key <- paste0("HTTP_", toupper(gsub("-", "_", name)))
    req[[key]] %||% default
  }
  # Primary headers expected from the reverse proxy after verification
  user  <- get_header("X-User") %||% Sys.getenv("DEV_USER", unset = "local_dev_user")
  org   <- get_header("X-Org-Id") %||% get_header("X-Org") %||% Sys.getenv("DEV_ORG_ID", unset = "org_001")
  roles_raw <- get_header("X-Roles") %||% Sys.getenv("DEV_ROLES", unset = "analyst")
  roles <- str_split(roles_raw, ",")[[1]] |> trimws() |> discard(~.x == "")

  list(user = user, org_id = org, roles = roles)
}

has_role <- function(claims, role) {
  role %in% (claims$roles %||% character())
}

filter_by_access <- function(ds, claims, resource = NULL) {
  # Admins see all orgs; otherwise restrict to the user's org
  if (!has_role(claims, "admin")) {
    if (!is.null(claims$org_id) && nzchar(claims$org_id)) {
      ds <- ds %>% dplyr::filter(org_id == !!claims$org_id)
    } else {
      # No org in claims -> return empty dataset
      ds <- ds %>% dplyr::filter(FALSE)
    }
  }

  # Optionally apply resource-specific role restrictions if needed
  if (identical(resource, "content")) {
    # Example: content_editor or admin can see; viewers limited to published content
    if (!(has_role(claims, "admin") || has_role(claims, "content_editor"))) {
      ds <- ds %>% dplyr::filter(status == "published")
    }
  }

  ds
}

# ---------------------------
# Arrow dataset bootstrap (demo data if none present)
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
      # Write partitioned by org_id when present
      part_cols <- intersect("org_id", names(df))
      write_dataset(df, path = path, format = "parquet", partitioning = part_cols)
    }
    invisible(path)
  }

  set.seed(42)

  # Cohorts dataset
  ensure_dataset("cohorts", function() {
    orgs <- paste0("org_", sprintf("%03d", 1:10))
    n <- 200000
    tibble(
      org_id = sample(orgs, n, replace = TRUE),
      cohort_id = paste0("C", sample(1000:9999, n, replace = TRUE)),
      user_id = paste0("U", sample(1e6:2e6, n, replace = TRUE)),
      joined_at = as_datetime("2023-01-01") + runif(n, 0, 360*24*3600),
      segment = sample(c("A", "B", "C", "D"), n, replace = TRUE),
      metric1 = rnorm(n, 50, 10),
      metric2 = runif(n, 0, 1)
    )
  })

  # IRT item calibrations
  ensure_dataset("irt_items", function() {
    items <- paste0("item_", 1:500)
    tibble(
      item_id = items,
      a = runif(length(items), 0.5, 2.5),
      b = rnorm(length(items), 0, 1.2),
      c = runif(length(items), 0.0, 0.3)
    )
  })

  # A/B experiments summary
  ensure_dataset("ab_experiments", function() {
    orgs <- paste0("org_", sprintf("%03d", 1:10))
    dates <- seq.Date(as.Date("2024-01-01"), as.Date("2024-09-30"), by = "day")
    grid <- tidyr::expand_grid(org_id = orgs, exp_id = paste0("exp_", 1:50), date = dates, variant = c("A","B"))
    grid %>%
      mutate(users = rpois(n(), 200) + 50,
             conversions = rbinom(n(), size = pmax(users,1), prob = if_else(variant=="A", 0.08, 0.085 + runif(n(), -0.01, 0.01))))
  })

  # Churn timeseries
  ensure_dataset("churn", function() {
    orgs <- paste0("org_", sprintf("%03d", 1:10))
    dates <- seq.Date(as.Date("2023-01-01"), as.Date(Sys.Date()), by = "week")
    tidyr::expand_grid(org_id = orgs, date = dates) %>%
      mutate(churn_rate = pmax(pmin(0.25, 0.12 + 0.05*sin(as.numeric(date)/20) + rnorm(n(), 0, 0.015)), 0))
  })

  # Content bank
  ensure_dataset("content", function() {
    orgs <- paste0("org_", sprintf("%03d", 1:10))
    n <- 50000
    tibble(
      org_id = sample(orgs, n, replace = TRUE),
      content_id = paste0("CNT", sample(100000:199999, n, replace = TRUE)),
      title = paste("Lesson", sample(1:5000, n, replace = TRUE)),
      tags = sample(c("math,algebra", "reading,comprehension", "science,physics", "coding,python"), n, replace = TRUE),
      updated_at = as_datetime("2024-01-01") + runif(n, 0, 180*24*3600),
      status = sample(c("draft","review","published"), n, replace = TRUE, prob = c(0.2,0.3,0.5))
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
  skin = "blue",
  dashboardHeader(title = "Admin Dashboard", tags$li(class = "dropdown", uiOutput("user_badge"))),
  dashboardSidebar(
    sidebarMenu(id = "tabs",
      menuItem("Cohort Overview", tabName = "cohort", icon = icon("users")),
      menuItem("IRT Calib", tabName = "irt", icon = icon("sliders")),
      menuItem("A/B Lab", tabName = "ab", icon = icon("flask")),
      menuItem("Churn Monitor", tabName = "churn", icon = icon("chart-line")),
      menuItem("Content Bank", tabName = "content", icon = icon("book"))
    )
  ),
  dashboardBody(
    tabItems(
      tabItem(tabName = "cohort",
        fluidRow(
          box(width = 12, title = "Cohort Overview", status = "primary", solidHeader = TRUE,
              fluidRow(
                column(3, selectInput("cohort_segment", "Segment", choices = c("All","A","B","C","D"), selected = "All")),
                column(3, dateRangeInput("cohort_dates", "Joined at", start = as.Date("2023-01-01"), end = Sys.Date())),
                column(3, numericInput("cohort_limit", "Max rows (collect)", value = 100000, min = 1000, step = 1000)),
                column(3, downloadButton("download_cohort", "Download CSV"))
              ),
              DTOutput("cohort_table")
          )
        )
      ),
      tabItem(tabName = "irt",
        fluidRow(
          box(width = 4, title = "Item Selection", status = "primary", solidHeader = TRUE,
              uiOutput("irt_item_picker"),
              sliderInput("irt_theta", "Theta range", min = -4, max = 4, value = c(-3,3), step = 0.1)
          ),
          box(width = 8, title = "Item Characteristic Curve (3PL)", status = "primary", solidHeader = TRUE,
              plotlyOutput("irt_plot", height = 500)
          )
        )
      ),
      tabItem(tabName = "ab",
        fluidRow(
          box(width = 12, title = "A/B Experiments", status = "primary", solidHeader = TRUE,
              fluidRow(
                column(3, dateRangeInput("ab_dates", "Date range", start = as.Date("2024-01-01"), end = Sys.Date())),
                column(3, textInput("ab_exp_filter", "Experiment contains", value = ""))
              ),
              DTOutput("ab_table"),
              plotlyOutput("ab_plot", height = 400)
          )
        )
      ),
      tabItem(tabName = "churn",
        fluidRow(
          box(width = 12, title = "Churn Monitor", status = "primary", solidHeader = TRUE,
              dateRangeInput("churn_dates", "Date range", start = as.Date("2023-01-01"), end = Sys.Date()),
              plotlyOutput("churn_plot", height = 450)
          )
        )
      ),
      tabItem(tabName = "content",
        fluidRow(
          box(width = 12, title = "Content Bank", status = "primary", solidHeader = TRUE,
              fluidRow(
                column(4, textInput("content_q", "Search title/tags", value = "")),
                column(3, selectInput("content_status", "Status", choices = c("All","draft","review","published"), selected = "All")),
                column(3, numericInput("content_limit", "Max rows (collect)", value = 50000, min = 1000, step = 1000))
              ),
              DTOutput("content_table")
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

  # ---------------- Cohort Overview ----------------
  cohorts_ds <- reactive({
    ds <- open_ds(base, "cohorts")
    ds <- filter_by_access(ds, claims)
    if (!is.null(input$cohort_dates)) {
      ds <- ds %>% filter(date(joined_at) >= !!input$cohort_dates[1], date(joined_at) <= !!input$cohort_dates[2])
    }
    if (!is.null(input$cohort_segment) && input$cohort_segment != "All") {
      ds <- ds %>% filter(segment == !!input$cohort_segment)
    }
    ds
  })

  cohorts_tbl <- reactive({
    limit <- input$cohort_limit %||% 100000
    cohorts_ds() %>% head(limit) %>% collect() %>% mutate(joined_at = as.character(joined_at))
  })

  output$cohort_table <- renderDT({
    datatable(cohorts_tbl(),
      rownames = FALSE,
      filter = "top",
      extensions = c("Buttons", "Scroller"),
      options = list(
        deferRender = TRUE, scrollX = TRUE, scrollY = 400, scroller = TRUE,
        dom = 'Bfrtip', buttons = c('copy','csv','excel'),
        pageLength = 50
      )
    )
  }, server = TRUE)

  output$download_cohort <- downloadHandler(
    filename = function() paste0("cohorts_", Sys.Date(), ".csv"),
    content = function(file) {
      # Stream out limited export to avoid memory pressure
      cohorts_ds() %>% head(input$cohort_limit %||% 100000) %>% collect() %>% readr::write_csv(file)
    }
  )

  # ---------------- IRT Calib ----------------
  irt_ds <- reactive({ open_ds(base, "irt_items") })

  output$irt_item_picker <- renderUI({
    items <- irt_ds() %>% select(item_id) %>% head(5000) %>% collect() %>% pull(item_id)
    selectizeInput("irt_items", "Items", choices = items, selected = head(items, 3), multiple = TRUE, options = list(maxItems = 5))
  })

  output$irt_plot <- renderPlotly({
    req(input$irt_items, input$irt_theta)
    items <- irt_ds() %>% filter(item_id %in% !!input$irt_items) %>% collect()
    theta <- seq(input$irt_theta[1], input$irt_theta[2], length.out = 200)
    curves <- purrr::map_dfr(1:nrow(items), function(i) {
      a <- items$a[i]; b <- items$b[i]; c <- items$c[i]
      p <- c + (1 - c) / (1 + exp(-a * (theta - b)))
      tibble(item_id = items$item_id[i], theta = theta, P = p)
    })

    plot_ly(curves, x = ~theta, y = ~P, color = ~item_id, type = 'scatter', mode = 'lines') %>%
      layout(yaxis = list(title = "P(correct)", rangemode = "tozero"), xaxis = list(title = "Theta"))
  })

  # ---------------- A/B Lab ----------------
  ab_ds <- reactive({
    ds <- open_ds(base, "ab_experiments")
    filter_by_access(ds, claims)
  })

  ab_tbl <- reactive({
    ds <- ab_ds()
    if (!is.null(input$ab_dates)) {
      ds <- ds %>% filter(date >= !!input$ab_dates[1], date <= !!input$ab_dates[2])
    }
    if (!is.null(input$ab_exp_filter) && nzchar(input$ab_exp_filter)) {
      ds <- ds %>% filter(str_detect(exp_id, fixed(!!input$ab_exp_filter, ignore_case = TRUE)))
    }
    ds %>%
      group_by(org_id, exp_id, variant) %>%
      summarise(users = sum(users, na.rm = TRUE), conversions = sum(conversions, na.rm = TRUE), .groups = 'drop') %>%
      mutate(cr = conversions / pmax(users, 1)) %>%
      arrange(desc(cr)) %>%
      head(50000) %>%
      collect()
  })

  output$ab_table <- renderDT({
    datatable(ab_tbl(), rownames = FALSE, extensions = c("Buttons", "Scroller"), options = list(
      deferRender = TRUE, scrollX = TRUE, scrollY = 300, scroller = TRUE, dom = 'Bfrtip', buttons = c('copy','csv','excel')
    ))
  }, server = TRUE)

  output$ab_plot <- renderPlotly({
    df <- ab_tbl() %>% group_by(exp_id, variant) %>% summarise(users = sum(users), conversions = sum(conversions), .groups = 'drop') %>% mutate(cr = conversions / pmax(users,1))
    plot_ly(df, x = ~exp_id, y = ~cr, color = ~variant, type = 'bar') %>%
      layout(yaxis = list(title = "Conversion rate"), xaxis = list(title = "Experiment", tickangle = -45))
  })

  # ---------------- Churn Monitor ----------------
  churn_ds <- reactive({
    ds <- open_ds(base, "churn")
    filter_by_access(ds, claims)
  })

  output$churn_plot <- renderPlotly({
    ds <- churn_ds()
    if (!is.null(input$churn_dates)) {
      ds <- ds %>% filter(date >= !!input$churn_dates[1], date <= !!input$churn_dates[2])
    }
    df <- ds %>% group_by(date) %>% summarise(churn_rate = mean(churn_rate, na.rm = TRUE), .groups = 'drop') %>% collect()
    plot_ly(df, x = ~date, y = ~churn_rate, type = 'scatter', mode = 'lines+markers') %>%
      layout(yaxis = list(title = "Churn rate"), xaxis = list(title = "Date"))
  })

  # ---------------- Content Bank ----------------
  content_ds <- reactive({
    ds <- open_ds(base, "content")
    filter_by_access(ds, claims, resource = "content")
  })

  content_tbl <- reactive({
    ds <- content_ds()
    if (!is.null(input$content_status) && input$content_status != "All") {
      ds <- ds %>% filter(status == !!input$content_status)
    }
    q <- input$content_q %||% ""
    if (nzchar(q)) {
      ds <- ds %>% filter(str_detect(title, fixed(!!q, ignore_case = TRUE)) | str_detect(tags, fixed(!!q, ignore_case = TRUE)))
    }
    ds %>% head(input$content_limit %||% 50000) %>% collect() %>% mutate(updated_at = as.character(updated_at))
  })

  output$content_table <- renderDT({
    datatable(content_tbl(), rownames = FALSE, filter = "top", extensions = c("Buttons","Scroller"), options = list(
      deferRender = TRUE, scrollX = TRUE, scrollY = 400, scroller = TRUE, dom = 'Bfrtip', buttons = c('copy','csv','excel')
    ))
  }, server = TRUE)
}

shinyApp(ui, server)
