# R Forecast Plumber API
# Survival Analysis + Prophet Forecasting

library(plumber)
library(survival)
library(prophet)
library(jsonlite)
library(dplyr)

#* @apiTitle R Forecast Service
#* @apiDescription Survival analysis and Prophet forecasting for churn
#*   prediction and trend analysis

#* Health check
#* @get /healthz
function() {
  list(
    status = "ok",
    service = "r-forecast-plumber",
    version = "1.0.0",
    timestamp = Sys.time()
  )
}

#* Fit survival model (Cox PH) - V2 API
#* @post /survival/fit
#* @param req Request object
function(req) {
  tryCatch({
    # Parse request body
    body <- req$body
    rows <- body$rows
    family <- body$family %||% "cox"
    event_threshold_days <- body$event_threshold_days %||% 14

    # Validate data
    if (is.null(rows) || length(rows) == 0) {
      return(list(status = "noop", reason = "No data provided"))
    }

    # Convert to data frame
    df <- do.call(rbind, lapply(rows, as.data.frame))
    # Check minimum observations
    if (nrow(df) < 10) {
      return(list(
        status = "noop",
        reason = paste("Insufficient data: n =", nrow(df))
      ))
    }

    # Ensure numeric columns (flexible column names)
    df$observed_gap_days <- as.numeric(df$observed_gap_days)
    df$event <- as.integer(df$event)

    # Covariates (flexible names, use what's available)
    covariate_cols <- c(
      "sessions_28d", "mean_gap_days_28d", "A_t", "E_t", "R_t",
      "dwell_seconds_28d", "hints_28d"
    )
    available_covariates <- intersect(covariate_cols, names(df))

    if (length(available_covariates) == 0) {
      return(list(status = "error", message = "No covariates found"))
    }


    for (col in available_covariates) {
      df[[col]] <- as.numeric(df[[col]])
    }

    # Build formula dynamically
    covariates_str <- paste(available_covariates, collapse = " + ")
    formula_str <- paste("Surv(observed_gap_days, event) ~", covariates_str)
    formula_obj <- as.formula(formula_str)

    # Fit Cox PH model
    fit <- coxph(formula_obj, data = df)

    # Extract coefficients
    coefficients <- coef(fit)

    # Compute concordance
    concordance <- fit$concordance["concordance"]

    # Predict risk scores and hazard ratios
    risk_scores <- predict(fit, newdata = df, type = "risk")

    # Compute rank percentiles
    rank_percentiles <- rank(risk_scores) / length(risk_scores)

    # Build predictions list
    predictions <- lapply(seq_len(nrow(df)), function(i) {
      list(
        user_id = as.character(df$user_id[i]),
        risk_score = as.numeric(risk_scores[i]),
        hazard_ratio = as.numeric(
          exp(sum(coefficients * df[i, available_covariates]))
        ),
        rank_percentile = as.numeric(rank_percentiles[i])
      )
    })

    # Compute survival curve (baseline at mean covariates)
    newdata_baseline <- as.data.frame(lapply(df[, available_covariates], mean))
    surv_fit <- survfit(fit, newdata = newdata_baseline)
    survival_curve <- lapply(seq_len(length(surv_fit$time)), function(i) {
      list(t = surv_fit$time[i], S = surv_fit$surv[i])
    })

    # Generate run_id
    run_id <- paste0(
      format(Sys.time(), "%Y%m%d-%H%M%S"), "-", sample(1000:9999, 1)
    )

    # Return results (V2 format)
    list(
      status = "success",
      run_id = run_id,
      model_meta = list(
        family = family,
        event_threshold_days = event_threshold_days,
        formula = formula_str,
        coefficients = as.list(coefficients),
        concordance = as.numeric(concordance),
        n = nrow(df),
        n_events = sum(df$event)
      ),
      predictions = predictions,
      survival_curve = survival_curve
    )

  }, error = function(e) {
    list(
      status = "error",
      message = as.character(e$message),
      timestamp = Sys.time()
    )
  })
}

#* Fit Prophet model for time series forecasting - V2 API
#* @post /prophet/fit
#* @param req Request object
function(req) {
  tryCatch({
    # Parse request body
    body <- req$body
    series <- body$series  # [{week_start, I_t}]
    horizon_weeks <- body$horizon_weeks %||% 4
    anomaly_threshold <- body$anomaly_threshold %||% 2.5
    options <- body$options %||% list()


    # Validate data
    if (is.null(series) || length(series) == 0) {
      return(list(status = "noop", reason = "No data provided"))
    }

    # Convert to data frame
    df <- do.call(rbind, lapply(series, as.data.frame))

    # Rename columns for Prophet (ds, y)
    if ("week_start" %in% names(df) && "I_t" %in% names(df)) {
      df$ds <- as.Date(df$week_start)
      df$y <- as.numeric(df$I_t)
    } else if ("ds" %in% names(df) && "y" %in% names(df)) {
      df$ds <- as.Date(df$ds)
      df$y <- as.numeric(df$y)
    } else {
      return(list(
        status = "error",
        message = "Data must have 'week_start'/'I_t' or 'ds'/'y' columns"
      ))
    }

    # Check minimum observations
    if (nrow(df) < 4) {
      return(list(
        status = "noop",
        reason = paste("Insufficient data: n =", nrow(df))
      ))
    }

    # Extract options
    yearly_seasonality <- options$yearly_seasonality %||% FALSE
    weekly_seasonality <- options$weekly_seasonality %||% FALSE
    changepoint_prior_scale <- options$changepoint_prior_scale %||% 0.05

    # Fit Prophet model
    m <- prophet(
      df[, c("ds", "y")],
      yearly.seasonality = yearly_seasonality,
      weekly.seasonality = weekly_seasonality,
      daily.seasonality = FALSE,
      changepoint.prior.scale = changepoint_prior_scale
    )

    # Make future dataframe
    future <- make_future_dataframe(m, periods = horizon_weeks, freq = "week")

    # Predict
    forecast_full <- predict(m, future)

    # Split into fitted (historical) and forecast (future)
    n_hist <- nrow(df)
    fitted <- forecast_full[1:n_hist, ]
    forecast <- forecast_full[(n_hist + 1):nrow(forecast_full), ]

    # Extract changepoints
    changepoints <- list()
    if (length(m$changepoints) > 0) {
      changepoints <- lapply(seq_len(length(m$changepoints)), function(i) {
        list(
          ds = as.character(m$changepoints[i]),
          delta = m$params$delta[1, i]
        )
      })
    }

    # Detect anomalies (compare actual vs fitted)
    anomalies <- list()
    merged <- merge(df, fitted[, c("ds", "yhat")], by = "ds", all.x = TRUE)
    merged$residual <- merged$y - merged$yhat

    if (nrow(merged) > 1) {
      residual_mean <- mean(merged$residual, na.rm = TRUE)
      residual_sd <- sd(merged$residual, na.rm = TRUE)

      if (!is.na(residual_sd) && residual_sd > 0) {
        merged$z_score <- (merged$residual - residual_mean) / residual_sd
        anomaly_rows <- merged[abs(merged$z_score) > anomaly_threshold, ]

        if (nrow(anomaly_rows) > 0) {
          anomalies <- lapply(seq_len(nrow(anomaly_rows)), function(i) {
            list(
              ds = as.character(anomaly_rows$ds[i]),
              y = anomaly_rows$y[i],
              yhat = anomaly_rows$yhat[i],
              residual = anomaly_rows$residual[i],
              anomaly_score = abs(anomaly_rows$z_score[i])
            )
          })
        }
      }
    }

    # Compute metrics (RMSE, MAE on fitted)
    rmse <- sqrt(mean(merged$residual^2, na.rm = TRUE))
    mae <- mean(abs(merged$residual), na.rm = TRUE)

    # Return results (V2 format)
    list(
      status = "success",
      model_meta = list(
        n_obs = nrow(df),
        horizon_weeks = horizon_weeks,
        n_changepoints = length(m$changepoints),
        changepoint_prior_scale = m$changepoint.prior.scale,
        seasonality_prior_scale = m$seasonality.prior.scale,
        metrics = list(
          rmse = rmse,
          mae = mae
        )
      ),
      fitted = lapply(seq_len(nrow(fitted)), function(i) {
        list(
          ds = as.character(fitted$ds[i]),
          yhat = fitted$yhat[i]
        )
      }),
      forecast = lapply(seq_len(nrow(forecast)), function(i) {
        list(
          ds = as.character(forecast$ds[i]),
          yhat = forecast$yhat[i],
          yhat_lower = forecast$yhat_lower[i],
          yhat_upper = forecast$yhat_upper[i]
        )
      }),
      changepoints = changepoints,
      anomalies = anomalies
    )

  }, error = function(e) {
    list(
      status = "error",
      message = as.character(e$message),
      timestamp = Sys.time()
    )
  })
}

#* Fit clustering model (K-means)
#* @post /cluster/fit
#* @param req Request object
function(req) {
  tryCatch({
    # Parse request body
    body <- req$body
    data_rows <- body$data_rows
    method <- body$method %||% "kmeans"
    k <- body$k %||% 3

    # Validate data
    if (is.null(data_rows) || length(data_rows) == 0) {
      return(list(status = "noop", reason = "No data provided"))
    }

    # Convert to data frame
    df <- do.call(rbind, lapply(data_rows, as.data.frame))

    # Extract user IDs
    user_ids <- df$user_id

    # Extract feature columns (exclude user_id)
    feature_cols <- setdiff(names(df), "user_id")
    features <- df[, feature_cols, drop = FALSE]

    # Convert to numeric matrix
    feature_matrix <- as.matrix(sapply(features, as.numeric))
    # Check for missing values
    if (any(is.na(feature_matrix))) {
      # Impute with column means
      for (i in seq_len(ncol(feature_matrix))) {
        na_indices <- is.na(feature_matrix[, i])
        col_mean <- mean(feature_matrix[, i], na.rm = TRUE)
        feature_matrix[na_indices, i] <- col_mean
      }
    }

    # Check minimum observations
    if (nrow(feature_matrix) < k) {
      return(list(
        status = "noop",
        reason = paste(
          "Insufficient data: n =", nrow(feature_matrix), ", k =", k
        )
      ))
    }

    # Fit clustering model
    if (method == "kmeans") {
      # K-means clustering
      fit <- kmeans(feature_matrix, centers = k, nstart = 25, iter.max = 100)

      # Extract results
      clusters <- fit$cluster
      centers <- fit$centers
      withinss <- fit$withinss
      tot_withinss <- fit$tot.withinss
      betweenss <- fit$betweenss

      # Build cluster assignments
      cluster_map <- setNames(as.list(clusters), user_ids)

      # Convert centers to list of lists
      centers_list <- lapply(seq_len(nrow(centers)), function(i) {
        as.list(setNames(centers[i, ], colnames(centers)))
      })

      # Return results
      list(
        status = "success",
        method = method,
        k = k,
        clusters = cluster_map,
        centers = centers_list,
        withinss = as.list(withinss),
        tot_withinss = tot_withinss,
        betweenss = betweenss
      )

    } else {
      return(list(
        status = "error",
        message = paste("Unsupported method:", method)
      ))
    }

  }, error = function(e) {
    list(
      status = "error",
      message = as.character(e$message),
      timestamp = Sys.time()
    )
  })
}

#* @plumber
function(pr) {
  pr %>%
    pr_set_api_spec(function(spec) {
      spec$info$title <- "R Forecast Service"
      spec$info$version <- "2.0.0"
      spec$info$description <- paste(
        "Survival analysis, Prophet forecasting, and clustering"
      )
      spec
    })
}
