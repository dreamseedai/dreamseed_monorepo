# cSpell:ignore plumber prophet surv
# R Forecast Plumber API
# Endpoints: Prophet (time series), Survival Analysis (churn prediction)
#
# Prophet:
#   POST /prophet/fit - Fit prophet model on time series data
#   POST /prophet/predict - Generate forecast with uncertainty
#
# Survival:
#   POST /survival/fit - Fit Cox proportional hazards or parametric survival model
#   POST /survival/predict - Predict survival probability at time t

library(plumber)
library(jsonlite)

# Load required packages (install if missing)
load_package <- function(pkg) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    message(sprintf("Installing %s...", pkg))
    install.packages(pkg, repos = "https://cloud.r-project.org/")
    library(pkg, character.only = TRUE)
  }
}

# Prophet for time series forecasting
tryCatch({
  load_package("prophet")
  PROPHET_AVAILABLE <- TRUE
}, error = function(e) {
  message("Prophet not available, using fallback forecast")
  PROPHET_AVAILABLE <- FALSE
})

# Survival analysis
tryCatch({
  load_package("survival")
  SURVIVAL_AVAILABLE <- TRUE
}, error = function(e) {
  message("survival package not available")
  SURVIVAL_AVAILABLE <- FALSE
})

# Internal token auth (optional)
INTERNAL_TOKEN <- Sys.getenv("R_FORECAST_INTERNAL_TOKEN", "")

#* @apiTitle R Forecast Plumber API
#* @apiDescription Prophet time series and survival analysis endpoints

#* Health check
#* @get /healthz
function() {
  list(
    status = "ok",
    timestamp = Sys.time(),
    engines = list(
      prophet = PROPHET_AVAILABLE,
      survival = SURVIVAL_AVAILABLE
    )
  )
}

#* Fit Prophet time series model
#* @param req Request object
#* @post /prophet/fit
function(req) {
  # Auth check
  if (nchar(INTERNAL_TOKEN) > 0) {
    token <- req$HTTP_AUTHORIZATION
    if (is.null(token) || !grepl(paste0("Bearer ", INTERNAL_TOKEN), token, fixed = TRUE)) {
      token_alt <- req$HTTP_X_INTERNAL_TOKEN
      if (is.null(token_alt) || token_alt != INTERNAL_TOKEN) {
        stop("Unauthorized")
      }
    }
  }
  
  if (!PROPHET_AVAILABLE) {
    return(list(
      error = "Prophet not available",
      fallback = "linear_trend",
      slope = 0.0,
      intercept = 0.0
    ))
  }
  
  # Parse request body
  body <- req$postBody
  payload <- fromJSON(body)
  
  # Expected: { rows: [{ds: "2024-01-01", y: 0.75}, ...], seasonality_mode: "additive", ... }
  if (is.null(payload$rows) || length(payload$rows) == 0) {
    stop("Missing 'rows' field with [{ds, y}, ...]")
  }
  
  df <- as.data.frame(payload$rows)
  if (!all(c("ds", "y") %in% names(df))) {
    stop("Each row must have 'ds' (date) and 'y' (value)")
  }
  
  # Convert ds to Date if character
  if (is.character(df$ds)) {
    df$ds <- as.Date(df$ds)
  }
  
  # Fit prophet model
  seasonality_mode <- if (!is.null(payload$seasonality_mode)) payload$seasonality_mode else "additive"
  yearly_seasonality <- if (!is.null(payload$yearly_seasonality)) as.logical(payload$yearly_seasonality) else TRUE
  weekly_seasonality <- if (!is.null(payload$weekly_seasonality)) as.logical(payload$weekly_seasonality) else TRUE
  daily_seasonality <- if (!is.null(payload$daily_seasonality)) as.logical(payload$daily_seasonality) else FALSE
  
  tryCatch({
    m <- prophet::prophet(
      df,
      seasonality.mode = seasonality_mode,
      yearly.seasonality = yearly_seasonality,
      weekly.seasonality = weekly_seasonality,
      daily.seasonality = daily_seasonality
    )
    
    # Return model summary
    list(
      status = "success",
      n_obs = nrow(df),
      date_range = list(
        start = as.character(min(df$ds)),
        end = as.character(max(df$ds))
      ),
      params = list(
        seasonality_mode = seasonality_mode,
        yearly_seasonality = yearly_seasonality,
        weekly_seasonality = weekly_seasonality,
        daily_seasonality = daily_seasonality
      ),
      # Serialize model to base64 for predict endpoint
      model_id = digest::digest(m, algo = "md5")
    )
  }, error = function(e) {
    list(
      error = "Prophet fit failed",
      message = as.character(e),
      fallback = "linear_trend"
    )
  })
}

#* Generate Prophet forecast
#* @param req Request object
#* @post /prophet/predict
function(req) {
  # Auth check
  if (nchar(INTERNAL_TOKEN) > 0) {
    token <- req$HTTP_AUTHORIZATION
    if (is.null(token) || !grepl(paste0("Bearer ", INTERNAL_TOKEN), token, fixed = TRUE)) {
      token_alt <- req$HTTP_X_INTERNAL_TOKEN
      if (is.null(token_alt) || token_alt != INTERNAL_TOKEN) {
        stop("Unauthorized")
      }
    }
  }
  
  if (!PROPHET_AVAILABLE) {
    # Fallback: linear extrapolation
    body <- req$postBody
    payload <- fromJSON(body)
    periods <- if (!is.null(payload$periods)) as.integer(payload$periods) else 7
    
    return(list(
      fallback = "linear_trend",
      forecast = lapply(1:periods, function(i) {
        list(ds = as.character(Sys.Date() + i), yhat = 0.0, yhat_lower = 0.0, yhat_upper = 0.0)
      })
    ))
  }
  
  # Parse request body
  body <- req$postBody
  payload <- fromJSON(body)
  
  # Expected: { rows: [{ds, y}, ...], periods: 30, freq: "day" }
  if (is.null(payload$rows) || length(payload$rows) == 0) {
    stop("Missing 'rows' field for refitting")
  }
  
  df <- as.data.frame(payload$rows)
  if (!all(c("ds", "y") %in% names(df))) {
    stop("Each row must have 'ds' and 'y'")
  }
  
  if (is.character(df$ds)) {
    df$ds <- as.Date(df$ds)
  }
  
  periods <- if (!is.null(payload$periods)) as.integer(payload$periods) else 30
  freq <- if (!is.null(payload$freq)) payload$freq else "day"
  
  tryCatch({
    # Refit model (stateless API)
    m <- prophet::prophet(df)
    
    # Generate future dataframe
    future <- prophet::make_future_dataframe(m, periods = periods, freq = freq)
    forecast <- prophet::predict(m, future)
    
    # Return forecast tail (future only)
    n_hist <- nrow(df)
    forecast_future <- tail(forecast, periods)
    
    list(
      status = "success",
      periods = periods,
      forecast = lapply(seq_len(nrow(forecast_future)), function(i) {
        list(
          ds = as.character(forecast_future$ds[i]),
          yhat = round(forecast_future$yhat[i], 4),
          yhat_lower = round(forecast_future$yhat_lower[i], 4),
          yhat_upper = round(forecast_future$yhat_upper[i], 4)
        )
      })
    )
  }, error = function(e) {
    list(
      error = "Prophet predict failed",
      message = as.character(e)
    )
  })
}

#* Fit survival model (Cox PH or parametric)
#* @param req Request object
#* @post /survival/fit
function(req) {
  # Auth check
  if (nchar(INTERNAL_TOKEN) > 0) {
    token <- req$HTTP_AUTHORIZATION
    if (is.null(token) || !grepl(paste0("Bearer ", INTERNAL_TOKEN), token, fixed = TRUE)) {
      token_alt <- req$HTTP_X_INTERNAL_TOKEN
      if (is.null(token_alt) || token_alt != INTERNAL_TOKEN) {
        stop("Unauthorized")
      }
    }
  }
  
  if (!SURVIVAL_AVAILABLE) {
    return(list(
      error = "survival package not available",
      fallback = "exponential",
      hazard_rate = 0.01
    ))
  }
  
  # Parse request body
  body <- req$postBody
  payload <- fromJSON(body)
  
  # Expected: { rows: [{time, event, ...covariates}, ...], model: "cox" | "exponential" | "weibull" }
  if (is.null(payload$rows) || length(payload$rows) == 0) {
    stop("Missing 'rows' field")
  }
  
  df <- as.data.frame(payload$rows)
  if (!all(c("time", "event") %in% names(df))) {
    stop("Each row must have 'time' (numeric) and 'event' (0/1)")
  }
  
  model_type <- if (!is.null(payload$model)) payload$model else "cox"
  
  tryCatch({
    if (model_type == "cox") {
      # Cox proportional hazards (requires covariates)
      covariate_cols <- setdiff(names(df), c("time", "event"))
      if (length(covariate_cols) == 0) {
        # Null model (no covariates)
        formula_str <- "Surv(time, event) ~ 1"
      } else {
        formula_str <- paste0("Surv(time, event) ~ ", paste(covariate_cols, collapse = " + "))
      }
      
      fit <- survival::coxph(as.formula(formula_str), data = df)
      
      list(
        status = "success",
        model = "cox",
        n_obs = nrow(df),
        n_events = sum(df$event),
        coefficients = if (length(coef(fit)) > 0) as.list(coef(fit)) else list(),
        summary = list(
          concordance = fit$concordance["concordance"]
        )
      )
    } else {
      # Parametric survival (exponential, weibull, etc.)
      formula_str <- "Surv(time, event) ~ 1"
      fit <- survival::survreg(as.formula(formula_str), data = df, dist = model_type)
      
      list(
        status = "success",
        model = model_type,
        n_obs = nrow(df),
        n_events = sum(df$event),
        coefficients = as.list(coef(fit)),
        scale = fit$scale
      )
    }
  }, error = function(e) {
    list(
      error = "Survival fit failed",
      message = as.character(e)
    )
  })
}

#* Predict survival probability
#* @param req Request object
#* @post /survival/predict
function(req) {
  # Auth check
  if (nchar(INTERNAL_TOKEN) > 0) {
    token <- req$HTTP_AUTHORIZATION
    if (is.null(token) || !grepl(paste0("Bearer ", INTERNAL_TOKEN), token, fixed = TRUE)) {
      token_alt <- req$HTTP_X_INTERNAL_TOKEN
      if (is.null(token_alt) || token_alt != INTERNAL_TOKEN) {
        stop("Unauthorized")
      }
    }
  }
  
  if (!SURVIVAL_AVAILABLE) {
    # Fallback: exponential survival S(t) = exp(-λt)
    body <- req$postBody
    payload <- fromJSON(body)
    time <- if (!is.null(payload$time)) as.numeric(payload$time) else 365
    hazard_rate <- 0.01  # Default λ
    
    return(list(
      fallback = "exponential",
      time = time,
      survival_prob = exp(-hazard_rate * time),
      hazard_rate = hazard_rate
    ))
  }
  
  # Parse request body
  body <- req$postBody
  payload <- fromJSON(body)
  
  # Expected: { rows: [{time, event, ...}], newdata: [{...covariates}], time: 365 }
  if (is.null(payload$rows) || length(payload$rows) == 0) {
    stop("Missing 'rows' for model fitting")
  }
  
  df <- as.data.frame(payload$rows)
  model_type <- if (!is.null(payload$model)) payload$model else "cox"
  time_point <- if (!is.null(payload$time)) as.numeric(payload$time) else 365
  
  tryCatch({
    if (model_type == "cox") {
      covariate_cols <- setdiff(names(df), c("time", "event"))
      if (length(covariate_cols) == 0) {
        formula_str <- "Surv(time, event) ~ 1"
      } else {
        formula_str <- paste0("Surv(time, event) ~ ", paste(covariate_cols, collapse = " + "))
      }
      
      fit <- survival::coxph(as.formula(formula_str), data = df)
      
      # Predict survival at time_point
      if (!is.null(payload$newdata)) {
        newdata <- as.data.frame(payload$newdata)
      } else {
        newdata <- df[1, covariate_cols, drop = FALSE]  # Use first row as example
      }
      
      surv_fit <- survival::survfit(fit, newdata = newdata)
      # Interpolate survival at time_point
      times <- surv_fit$time
      surv_probs <- surv_fit$surv
      
      if (time_point <= min(times)) {
        surv_prob <- 1.0
      } else if (time_point >= max(times)) {
        surv_prob <- tail(surv_probs, 1)
      } else {
        surv_prob <- approx(times, surv_probs, xout = time_point)$y
      }
      
      list(
        status = "success",
        model = "cox",
        time = time_point,
        survival_prob = round(surv_prob, 4)
      )
    } else {
      # Parametric survival
      formula_str <- "Surv(time, event) ~ 1"
      fit <- survival::survreg(as.formula(formula_str), data = df, dist = model_type)
      
      pred <- predict(fit, type = "response")
      # Compute survival probability at time_point (exponential: S(t) = exp(-t/scale))
      scale <- fit$scale
      surv_prob <- exp(-time_point / pred[1])
      
      list(
        status = "success",
        model = model_type,
        time = time_point,
        survival_prob = round(surv_prob, 4)
      )
    }
  }, error = function(e) {
    list(
      error = "Survival predict failed",
      message = as.character(e)
    )
  })
}
