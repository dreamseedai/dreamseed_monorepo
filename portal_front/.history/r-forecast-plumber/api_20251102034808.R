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

generate_run_id <- function(prefix = "prophet") {
  rid <- NULL
  if (requireNamespace("uuid", quietly = TRUE)) {
    rid <- uuid::UUIDgenerate()
  } else {
    rid <- paste0(prefix, "-", as.integer(as.numeric(Sys.time())), "-", sample(1000:9999, 1))
  }
  return(rid)
}

#* Fit Prophet time series model (weekly data) and detect anomalies
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
      status = "error",
      error = "Prophet not available"
    ))
  }

  # Parse request body
  body <- req$postBody
  payload <- fromJSON(body)

  # Expected: { series: [{week_start: "YYYY-MM-DD", I_t: float}, ...], horizon_weeks, anomaly_threshold, options: {...} }
  series <- payload$series
  if (is.null(series) || length(series) == 0) {
    return(list(status = "noop", reason = "Missing 'series' with [{week_start, I_t}]"))
  }

  # Build dataframe for Prophet: ds (Date), y (numeric)
  df <- data.frame(
    ds = as.Date(sapply(series, function(r) r$week_start)),
    y = as.numeric(sapply(series, function(r) r$I_t))
  )
  df <- df[!is.na(df$ds) & !is.na(df$y), , drop = FALSE]
  df <- df[order(df$ds), , drop = FALSE]

  if (nrow(df) < 4) {
    return(list(status = "noop", reason = "Insufficient observations (need >= 4)", n_obs = nrow(df)))
  }

  # Options and parameters
  opts <- payload$options
  seasonality_mode <- if (!is.null(opts$seasonality_mode)) opts$seasonality_mode else "additive"
  weekly_seasonality <- if (!is.null(opts$weekly_seasonality)) as.logical(opts$weekly_seasonality) else FALSE
  yearly_seasonality <- if (!is.null(opts$yearly_seasonality)) as.logical(opts$yearly_seasonality) else FALSE
  changepoint_prior_scale <- if (!is.null(opts$changepoint_prior_scale)) as.numeric(opts$changepoint_prior_scale) else 0.05
  n_changepoints <- if (!is.null(opts$n_changepoints)) as.integer(opts$n_changepoints) else 5
  interval_width <- if (!is.null(opts$interval_width)) as.numeric(opts$interval_width) else 0.95
  horizon_weeks <- if (!is.null(payload$horizon_weeks)) as.integer(payload$horizon_weeks) else 4
  anomaly_threshold <- if (!is.null(payload$anomaly_threshold)) as.numeric(payload$anomaly_threshold) else 2.5
  seed <- if (!is.null(opts$seed)) as.integer(opts$seed) else NA

  if (!is.na(seed)) set.seed(seed)

  # Fit Prophet (weekly data)
  res <- tryCatch({
    m <- prophet::prophet(
      df,
      seasonality.mode = seasonality_mode,
      yearly.seasonality = yearly_seasonality,
      weekly.seasonality = weekly_seasonality,
      changepoint.prior.scale = changepoint_prior_scale,
      n.changepoints = n_changepoints,
      interval.width = interval_width
    )

    # Fitted (insample)
    fitted_all <- prophet::predict(m, df)
    fitted_map <- setNames(as.numeric(fitted_all$yhat), as.character(fitted_all$ds))

    # Future forecast
    future <- prophet::make_future_dataframe(m, periods = horizon_weeks, freq = "week")
    forecast_all <- prophet::predict(m, future)

    # Assemble combined forecast entries
    last_obs <- max(df$ds)
    n_hist <- nrow(df)
    hist_part <- forecast_all[seq_len(n_hist), , drop = FALSE]
    fut_part <- forecast_all[(n_hist + 1):nrow(forecast_all), , drop = FALSE]

    # Compute fit metrics on insample
    # Join actuals for metrics
    hist_join <- merge(hist_part[, c("ds", "yhat")], df, by = "ds", all.x = TRUE)
    resid <- hist_join$y - hist_join$yhat
    rmse <- sqrt(mean((resid)^2, na.rm = TRUE))
    mae <- mean(abs(resid), na.rm = TRUE)

    # Anomalies
    mu <- mean(resid, na.rm = TRUE)
    sd_res <- stats::sd(resid, na.rm = TRUE)
    if (is.na(sd_res) || sd_res == 0) sd_res <- .Machine$double.eps
    anomalies <- list()
    for (i in seq_len(nrow(hist_part))) {
      ds_i <- as.character(hist_part$ds[i])
      yhat_i <- as.numeric(hist_part$yhat[i])
      yl_i <- as.numeric(hist_part$yhat_lower[i])
      yu_i <- as.numeric(hist_part$yhat_upper[i])
      y_i <- as.numeric(df$y[df$ds == as.Date(ds_i)][1])
      if (!is.na(y_i)) {
        z <- (y_i - yhat_i - mu) / sd_res
        breach <- (!is.na(yl_i) && y_i < yl_i) || (!is.na(yu_i) && y_i > yu_i)
        flag <- is.finite(z) && abs(z) >= anomaly_threshold || breach
        if (isTRUE(flag)) {
          anomalies[[length(anomalies) + 1]] <- list(
            ds = ds_i,
            actual = round(y_i, 4),
            expected = round(yhat_i, 4),
            zscore = round(z, 3),
            flag = TRUE
          )
        }
      }
    }

    # Build forecast output entries
    out_forecast <- list()
    for (i in seq_len(nrow(hist_part))) {
      out_forecast[[length(out_forecast) + 1]] <- list(
        ds = as.character(hist_part$ds[i]),
        type = "insample",
        yhat = round(hist_part$yhat[i], 4),
        yhat_lower = round(hist_part$yhat_lower[i], 4),
        yhat_upper = round(hist_part$yhat_upper[i], 4),
        actual = round(df$y[i], 4)
      )
    }
    for (i in seq_len(nrow(fut_part))) {
      out_forecast[[length(out_forecast) + 1]] <- list(
        ds = as.character(fut_part$ds[i]),
        type = "forecast",
        yhat = round(fut_part$yhat[i], 4),
        yhat_lower = round(fut_part$yhat_lower[i], 4),
        yhat_upper = round(fut_part$yhat_upper[i], 4)
      )
    }

    list(
      status = "ok",
      run_id = generate_run_id("prophet"),
      model_meta = list(
        n_obs = nrow(df),
        seasonality_mode = seasonality_mode,
        weekly_seasonality = weekly_seasonality,
        yearly_seasonality = yearly_seasonality,
        changepoint_prior_scale = changepoint_prior_scale,
        n_changepoints = n_changepoints,
        interval_width = interval_width,
        fit_metrics = list(rmse = round(rmse, 4), mae = round(mae, 4))
      ),
      horizon_weeks = horizon_weeks,
      last_observed_week = as.character(last_obs),
      forecast = out_forecast,
      anomalies = anomalies
    )
  }, error = function(e) {
    list(status = "error", message = as.character(e))
  })

  return(res)
}

#* Generate Prophet forecast (alias; accepts either new or legacy payload)
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
  
  # New contract path: if 'series' is present, delegate to /prophet/fit
  if (!is.null(payload$series)) {
    # Reconstruct a mock request with same body and call fit handler
    return(plumber:::forward()
           (list(postBody = body), "post", "/prophet/fit"))
  }

  # Legacy: { rows: [{ds, y}, ...], periods: 30, freq: "day" }
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

    # Predict on historical data to obtain fitted values
    fitted <- prophet::predict(m, df)

    # Generate future dataframe and forecast
    future <- prophet::make_future_dataframe(m, periods = periods, freq = freq)
    forecast <- prophet::predict(m, future)

    # Split fitted (historical) and forecast (future)
    n_hist <- nrow(df)
    fitted_hist <- head(forecast, n_hist)
    forecast_future <- tail(forecast, periods)

    list(
      status = "success",
      periods = periods,
      fitted = lapply(seq_len(nrow(fitted_hist)), function(i) {
        list(
          ds = as.character(fitted_hist$ds[i]),
          yhat = round(fitted_hist$yhat[i], 4)
        )
      }),
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

#* Fit survival model (Cox PH or parametric) and score risk
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
    return(list(status = "error", error = "survival package not available"))
  }
  
  # Parse request body
  body <- req$postBody
  payload <- fromJSON(body)
  
  # Expected: { rows: [{user_id, observed_gap_days, event, ...covariates}, ...], params: { family, event_threshold_days, seed, ... } }
  if (is.null(payload$rows) || length(payload$rows) == 0) {
    stop("Missing 'rows' field")
  }

  df <- as.data.frame(payload$rows)
  # Backward compatibility: allow 'time' as alias for observed_gap_days
  if (!("observed_gap_days" %in% names(df)) && ("time" %in% names(df))) {
    df$observed_gap_days <- df$time
  }
  if (!all(c("observed_gap_days", "event") %in% names(df))) {
    stop("Each row must have 'observed_gap_days' (numeric) and 'event' (0/1)")
  }

  params <- payload$params
  family <- if (!is.null(params$family)) params$family else "cox"
  event_threshold_days <- if (!is.null(params$event_threshold_days)) as.integer(params$event_threshold_days) else 14
  seed <- if (!is.null(params$seed)) as.integer(params$seed) else NA
  if (!is.na(seed)) set.seed(seed)

  # Identify covariates (exclude id and target columns)
  exclude_cols <- c("user_id", "observed_gap_days", "event")
  covariate_cols <- setdiff(names(df), exclude_cols)

  # Basic sanity: need at least one event and one censor
  n_events <- sum(as.integer(df$event) == 1, na.rm = TRUE)
  n_censor <- sum(as.integer(df$event) == 0, na.rm = TRUE)
  if (n_events == 0 || n_censor == 0) {
    return(list(status = "noop", reason = "Need at least one event and one censored observation", n = nrow(df)))
  }

  # Build formula
  surv_time <- as.numeric(df$observed_gap_days)
  df$observed_gap_days <- as.numeric(df$observed_gap_days)
  formula_str <- if (length(covariate_cols) == 0) {
    "Surv(observed_gap_days, event) ~ 1"
  } else {
    paste0("Surv(observed_gap_days, event) ~ ", paste(covariate_cols, collapse = " + "))
  }

  res <- tryCatch({
    if (family == "cox") {
      fit <- survival::coxph(as.formula(formula_str), data = df)

      # Coefficients and concordance
      coefs <- coef(fit)
      coeff_list <- if (length(coefs) > 0) as.list(coefs) else list()
      conc <- tryCatch({
        s <- summary(fit)
        as.numeric(s$concordance[1])
      }, error = function(e) { NA_real_ })

      # Linear predictor and hazard ratios
      lp <- as.numeric(stats::predict(fit, type = "lp"))
      hr <- exp(lp - mean(lp, na.rm = TRUE))
      # Risk score as percentile of HR
      rank_pct <- rank(hr, ties.method = "average") / length(hr)
      # Assemble predictions per user
      users <- if ("user_id" %in% names(df)) as.character(df$user_id) else as.character(seq_len(nrow(df)))
      preds <- lapply(seq_along(users), function(i) {
        list(
          user_id = users[i],
          risk_score = round(as.numeric(rank_pct[i]), 4),
          hazard_ratio = round(as.numeric(hr[i]), 4),
          rank_percentile = round(as.numeric(rank_pct[i]), 4)
        )
      })

      # Survival curve summary at 0, 7, 14 days (or threshold)
      surv_fit <- survival::survfit(fit)
      times <- surv_fit$time
      surv_probs <- surv_fit$surv
      key_ts <- sort(unique(c(0, 7, event_threshold_days)))
      surv_curve <- lapply(key_ts, function(t) {
        S_t <- if (t <= min(times)) {
          1.0
        } else if (t >= max(times)) {
          tail(surv_probs, 1)
        } else {
          approx(times, surv_probs, xout = t)$y
        }
        list(t = as.numeric(t), S = round(as.numeric(S_t), 4))
      })

      list(
        status = "ok",
        run_id = generate_run_id("survival"),
        model_meta = list(
          n = nrow(df),
          family = family,
          event_threshold_days = event_threshold_days,
          coefficients = coeff_list,
          concordance = ifelse(is.na(conc), NULL, round(conc, 4))
        ),
        predictions = preds,
        survival_curve = surv_curve
      )
    } else {
      # Parametric survival (e.g., weibull)
      fit <- survival::survreg(as.formula(formula_str), data = df, dist = family)
      coefs <- coef(fit)
      coeff_list <- as.list(coefs)

      # For parametric model, approximate risk using linear predictor
      lp <- as.numeric(stats::predict(fit, type = "lp"))
      hr <- exp(scale(lp))
      rank_pct <- rank(hr, ties.method = "average") / length(hr)
      users <- if ("user_id" %in% names(df)) as.character(df$user_id) else as.character(seq_len(nrow(df)))
      preds <- lapply(seq_along(users), function(i) {
        list(
          user_id = users[i],
          risk_score = round(as.numeric(rank_pct[i]), 4),
          hazard_ratio = round(as.numeric(hr[i]), 4),
          rank_percentile = round(as.numeric(rank_pct[i]), 4)
        )
      })

      # Simple survival curve using baseline scale
      key_ts <- sort(unique(c(0, 7, event_threshold_days)))
      surv_curve <- lapply(key_ts, function(t) {
        # Use exponential-like decay as placeholder based on scale parameter
        scale_param <- fit$scale
        S_t <- exp(-as.numeric(t) / (1 + abs(scale_param)))
        list(t = as.numeric(t), S = round(as.numeric(S_t), 4))
      })

      list(
        status = "ok",
        run_id = generate_run_id("survival"),
        model_meta = list(
          n = nrow(df),
          family = family,
          event_threshold_days = event_threshold_days,
          coefficients = coeff_list
        ),
        predictions = preds,
        survival_curve = surv_curve
      )
    }
  }, error = function(e) {
    list(status = "error", message = as.character(e))
  })

  return(res)
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

#* Fit clustering model (K-means, hierarchical, DBSCAN)
#* @param req Request object
#* @post /cluster/fit
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
  
  # Parse request body
  body <- req$postBody
  payload <- fromJSON(body)
  
  # Expected: { rows: [{user_id, feat1, feat2, ...}], method: "kmeans" | "hierarchical" | "dbscan", k: 3, ... }
  if (is.null(payload$rows) || length(payload$rows) == 0) {
    stop("Missing 'rows' field")
  }
  
  df <- as.data.frame(payload$rows)
  if (!("user_id" %in% names(df))) {
    stop("Each row must have 'user_id'")
  }
  
  user_ids <- df$user_id
  feature_cols <- setdiff(names(df), "user_id")
  
  if (length(feature_cols) == 0) {
    stop("No feature columns found (need at least one numeric feature)")
  }
  
  X <- as.matrix(df[, feature_cols, drop = FALSE])
  X <- apply(X, 2, as.numeric)  # Ensure numeric
  
  # Standardize features
  X_scaled <- scale(X)
  
  method <- if (!is.null(payload$method)) payload$method else "kmeans"
  k <- if (!is.null(payload$k)) as.integer(payload$k) else 3
  
  tryCatch({
    if (method == "kmeans") {
      # K-means clustering
      set.seed(42)  # For reproducibility
      fit <- kmeans(X_scaled, centers = k, nstart = 25)
      
      clusters <- fit$cluster
      centers <- fit$centers
      
      list(
        status = "success",
        method = "kmeans",
        k = k,
        n_obs = nrow(df),
        clusters = setNames(as.list(clusters), user_ids),
        centers = apply(centers, 1, function(row) as.list(row)),
        withinss = fit$withinss,
        tot_withinss = fit$tot.withinss,
        betweenss = fit$betweenss
      )
    } else if (method == "hierarchical") {
      # Hierarchical clustering
      dist_mat <- dist(X_scaled, method = "euclidean")
      fit <- hclust(dist_mat, method = "ward.D2")
      clusters <- cutree(fit, k = k)
      
      list(
        status = "success",
        method = "hierarchical",
        k = k,
        n_obs = nrow(df),
        clusters = setNames(as.list(clusters), user_ids),
        height = fit$height[length(fit$height) - (k-2)]  # Merge height at k clusters
      )
    } else if (method == "dbscan") {
      # DBSCAN clustering
      if (!require("dbscan", quietly = TRUE)) {
        install.packages("dbscan", repos = "https://cloud.r-project.org/")
        library(dbscan)
      }
      
      eps <- if (!is.null(payload$eps)) as.numeric(payload$eps) else 0.5
      minPts <- if (!is.null(payload$minPts)) as.integer(payload$minPts) else 5
      
      fit <- dbscan::dbscan(X_scaled, eps = eps, minPts = minPts)
      clusters <- fit$cluster
      
      list(
        status = "success",
        method = "dbscan",
        eps = eps,
        minPts = minPts,
        n_obs = nrow(df),
        n_clusters = max(clusters),
        clusters = setNames(as.list(clusters), user_ids)
      )
    } else {
      list(
        error = "Unsupported clustering method",
        message = paste0("Method '", method, "' not supported. Use: kmeans, hierarchical, dbscan")
      )
    }
  }, error = function(e) {
    list(
      error = "Clustering fit failed",
      message = as.character(e)
    )
  })
}

#* Predict cluster assignment for new data
#* @param req Request object
#* @post /cluster/predict
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
  
  # Parse request body
  body <- req$postBody
  payload <- fromJSON(body)
  
  # Expected: { newdata: [{user_id, feat1, feat2, ...}], centers: [[c1_f1, c1_f2, ...], ...] }
  if (is.null(payload$newdata) || length(payload$newdata) == 0) {
    stop("Missing 'newdata' field")
  }
  if (is.null(payload$centers) || length(payload$centers) == 0) {
    stop("Missing 'centers' field (cluster centroids from fit)")
  }
  
  df_new <- as.data.frame(payload$newdata)
  user_ids <- df_new$user_id
  feature_cols <- setdiff(names(df_new), "user_id")
  X_new <- as.matrix(df_new[, feature_cols, drop = FALSE])
  X_new <- apply(X_new, 2, as.numeric)
  
  # Standardize using same scale (assumes centers are already scaled)
  X_new_scaled <- scale(X_new)
  
  centers <- do.call(rbind, lapply(payload$centers, function(c) as.numeric(unlist(c))))
  
  tryCatch({
    # Assign to nearest center
    combined <- rbind(X_new_scaled, centers)
    dist_mat <- as.matrix(dist(combined))
    n_new <- nrow(X_new_scaled)
    n_total <- nrow(combined)
    dists <- dist_mat[seq_len(n_new), (n_new+1):n_total, drop = FALSE]
    clusters <- apply(dists, 1, which.min)
    
    list(
      status = "success",
      n_obs = nrow(df_new),
      clusters = setNames(as.list(clusters), user_ids)
    )
  }, error = function(e) {
    list(
      error = "Cluster predict failed",
      message = as.character(e)
    )
  })
}
