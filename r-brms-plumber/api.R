# R BRMS Plumber API
# Bayesian Growth Models using brms/Stan

library(plumber)
library(brms)
library(jsonlite)
library(dplyr)

#* @apiTitle R BRMS Service
#* @apiDescription Bayesian growth models for goal probability prediction

#* Health check
#* @get /healthz
function() {
  list(
    status = "ok",
    service = "r-brms-plumber",
    version = "1.0.0",
    timestamp = Sys.time(),
    stan_version = rstan::stan_version()
  )
}

#* Fit Bayesian growth model
#* @post /growth/fit
#* @param req Request object
function(req) {
  tryCatch({
    # Parse request body
    body <- req$body
    data_rows <- body$data
    formula_str <- body$formula %||% "score ~ week + (week|student_id)"
    priors_spec <- body$priors
    n_samples <- body$n_samples %||% 2000
    n_chains <- body$n_chains %||% 4
    # Validate data
    if (is.null(data_rows) || length(data_rows) == 0) {
      stop("No data provided")
    }

    # Convert to data frame
    df <- do.call(rbind, lapply(data_rows, as.data.frame))

    # Ensure proper column types
    df$student_id <- as.character(df$student_id)
    df$week <- as.integer(df$week)
    df$score <- as.numeric(df$score)

    # Build priors
    priors <- c()
    if (!is.null(priors_spec)) {
      if (!is.null(priors_spec$intercept)) {
        p <- priors_spec$intercept
        priors <- c(priors,
          set_prior(
            paste0("normal(", p$mean, ",", p$sd, ")"),
            class = "Intercept"
          )
        )
      }
      if (!is.null(priors_spec$week)) {
        p <- priors_spec$week
        priors <- c(priors,
          set_prior(
            paste0("normal(", p$mean, ",", p$sd, ")"),
            class = "b",
            coef = "week"
          )
        )
      }
      if (!is.null(priors_spec$sd)) {
        p <- priors_spec$sd
        priors <- c(priors,
          set_prior(
            paste0("cauchy(", p$location, ",", p$scale, ")"),
            class = "sd"
          )
        )
      }
    }
    # Fit brms model
    formula_obj <- as.formula(formula_str)

    # Use silent mode and capture warnings
    fit <- brm(
      formula_obj,
      data = df,
      prior = priors,
      chains = n_chains,
      iter = n_samples / 2,
      warmup = n_samples / 4,
      cores = min(n_chains, parallel::detectCores()),
      silent = 2,
      refresh = 0,
      seed = 42
    )

    # Extract posterior summary
    posterior_summary <- as.data.frame(summary(fit)$fixed)
    posterior_summary$parameter <- rownames(posterior_summary)

    # Extract diagnostics
    diagnostics <- list(
      rhat = rhat(fit),
      ess_bulk = neff_ratio(fit),
      divergences = sum(nuts_params(fit, pars = "divergent__")$Value)
    )

    # Predict for each student (goal probability)
    # Use posterior_predict to get full distribution
    pred_samples <- posterior_predict(fit, newdata = df)

    # Compute per-student predictions
    predictions <- list()
    for (student in unique(df$student_id)) {
      student_rows <- which(df$student_id == student)
      if (length(student_rows) > 0) {
        # Get last week's prediction
        last_row <- student_rows[length(student_rows)]
        pred_dist <- pred_samples[, last_row]

        # Compute probability of reaching goal (e.g., score > 0.7)
        goal_threshold <- 0.7
        p_goal <- mean(pred_dist > goal_threshold)

        predictions[[student]] <- list(
          probability = p_goal,
          mean_score = mean(pred_dist),
          sd_score = sd(pred_dist),
          uncertainty = sd(pred_dist)
        )
      }
    }

    # Return results
    list(
      status = "success",
      n_obs = nrow(df),
      n_students = length(unique(df$student_id)),
      n_samples = n_samples,
      n_chains = n_chains,
      formula = formula_str,
      posterior_summary = lapply(seq_len(nrow(posterior_summary)), function(i) {
        list(
          parameter = posterior_summary$parameter[i],
          estimate = posterior_summary$Estimate[i],
          se = posterior_summary$Est.Error[i],
          lower = posterior_summary$`l-95% CI`[i],
          upper = posterior_summary$`u-95% CI`[i]
        )
      }),
      diagnostics = diagnostics,
      predictions = predictions
    )
  }, error = function(e) {
    list(
      status = "error",
      message = as.character(e$message),
      timestamp = Sys.time()
    )
  })
}

#* Predict goal probability for new data
#* @post /growth/predict
#* @param req Request object
function(req) {
  tryCatch({
    # Parse request body
    body <- req$body
    data_rows <- body$data
    goal_threshold <- body$goal_threshold %||% 0.7
    # Note: This endpoint requires a pre-fitted model
    # In production, you would load the model from disk or cache
    # For now, return a placeholder

    list(
      status = "error",
      message = paste(
        "Prediction endpoint requires a pre-fitted model.",
        "Use /growth/fit instead."
      ),
      timestamp = Sys.time()
    )

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
      spec$info$title <- "R BRMS Service"
      spec$info$version <- "1.0.0"
      spec$info$description <- "Bayesian growth models using brms/Stan"
      spec
    })
}
