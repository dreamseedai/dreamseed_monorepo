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
