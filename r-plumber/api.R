# R Plumber API for Advanced Statistical Analysis (GLMM)
# Author: Dreamseed Analytics Team
# Description: Provides GLMM fitting, prediction, and forecasting endpoints

library(plumber)
library(lme4)
library(broom.mixed)
library(jsonlite)
library(data.table)

# Define %||% operator for NULL coalescing
`%||%` <- function(x, y) if (is.null(x)) y else x

#* @apiTitle Dreamseed R Analytics API
#* @apiDescription Advanced statistical analysis endpoints for educational data
#* @apiVersion 1.0.0

# Internal token filter (optional security)
#* @filter internal_token
function(req, res) {
  expected <- Sys.getenv("INTERNAL_TOKEN", "")
  provided <- req$HTTP_X_INTERNAL_TOKEN %||% ""
  
  if (nzchar(expected) && !identical(expected, provided)) {
    res$status <- 401
    return(list(error = "unauthorized", message = "Invalid or missing internal token"))
  }
  
  plumber::forward()
}

#* Health check endpoint
#* @get /healthz
#* @serializer unboxedJSON
function() {
  list(
    status = "healthy",
    service = "r-glmm-plumber",
    version = "1.0.0",
    timestamp = Sys.time(),
    r_version = paste(R.version$major, R.version$minor, sep = ".")
  )
}

# Safe GLMM fitting with error handling
safe_glmer <- function(formula_str, data, family = binomial) {
  warnings <- character(0)
  error_msg <- NULL
  model <- NULL
  
  tryCatch(
    withCallingHandlers(
      {
        form <- as.formula(formula_str)
        model <- lme4::glmer(form, data = data, family = family, 
                             control = glmerControl(optimizer = "bobyqa"))
      },
      warning = function(w) {
        warnings <<- c(warnings, conditionMessage(w))
        invokeRestart("muffleWarning")
      }
    ),
    error = function(e) {
      error_msg <<- conditionMessage(e)
    }
  )
  
  list(model = model, warnings = warnings, error = error_msg)
}

#* Fit binomial GLMM
#* @post /glmm/fit
#* @param observations:list List of observation objects with student_id, item_id, correct
#* @param formula:character Optional custom formula (default: "correct ~ 1 + (1|student_id) + (1|item_id)")
#* @serializer unboxedJSON
function(observations, formula = NULL) {
  # Validate input
  if (length(observations) == 0) {
    res$status <- 400
    return(list(error = "empty_data", message = "observations cannot be empty"))
  }
  
  # Convert to data.table
  dt <- rbindlist(observations, fill = TRUE)
  
  # Validate required columns
  required_cols <- c("student_id", "item_id", "correct")
  missing_cols <- setdiff(required_cols, names(dt))
  if (length(missing_cols) > 0) {
    res$status <- 400
    return(list(
      error = "missing_columns",
      message = sprintf("Missing required columns: %s", paste(missing_cols, collapse = ", "))
    ))
  }
  
  # Default formula
  if (is.null(formula) || !nzchar(formula)) {
    formula <- "correct ~ 1 + (1|student_id) + (1|item_id)"
  }
  
  # Fit model safely
  result <- safe_glmer(formula, dt, family = binomial)
  
  if (!is.null(result$error)) {
    res$status <- 500
    return(list(
      error = "fit_failed",
      message = result$error,
      warnings = result$warnings
    ))
  }
  
  model <- result$model
  
  # Extract compact model representation
  fixed_effects <- fixef(model)
  random_effects <- ranef(model)
  
  # Convert to serializable format
  compact_model <- list(
    formula = formula,
    fixed_effects = as.list(fixed_effects),
    random_effects = lapply(random_effects, function(re) {
      setNames(lapply(seq_len(ncol(re)), function(i) {
        setNames(as.list(re[, i]), rownames(re))
      }), colnames(re))
    }),
    convergence = model@optinfo$conv$opt,
    n_obs = nobs(model),
    warnings = result$warnings
  )
  
  list(
    success = TRUE,
    model = compact_model,
    summary = broom.mixed::tidy(model, effects = "fixed")
  )
}

#* Predict from compact GLMM model
#* @post /glmm/predict
#* @param model:list Compact model from /glmm/fit
#* @param newdata:list List of new observation objects
#* @serializer unboxedJSON
function(model, newdata) {
  # Validate inputs
  if (is.null(model) || length(newdata) == 0) {
    res$status <- 400
    return(list(error = "invalid_input", message = "model and newdata required"))
  }
  
  # Convert newdata to data.table
  dt <- rbindlist(newdata, fill = TRUE)
  
  # Extract fixed effects
  intercept <- model$fixed_effects$`(Intercept)` %||% 0
  
  # Extract random effects
  student_effects <- model$random_effects$student_id$`(Intercept)` %||% list()
  item_effects <- model$random_effects$item_id$`(Intercept)` %||% list()
  
  # Calculate predictions
  predictions <- vapply(seq_len(nrow(dt)), function(i) {
    student_id <- as.character(dt$student_id[i])
    item_id <- as.character(dt$item_id[i])
    
    # Linear predictor
    eta <- intercept +
      (student_effects[[student_id]] %||% 0) +
      (item_effects[[item_id]] %||% 0)
    
    # Inverse logit (probability)
    plogis(eta)
  }, numeric(1))
  
  list(
    success = TRUE,
    predictions = predictions,
    n_predictions = length(predictions)
  )
}

#* Forecast summary with Normal approximation
#* @post /forecast/summary
#* @param mean:numeric Mean of the distribution
#* @param sd:numeric Standard deviation
#* @param target:numeric Target value
#* @serializer unboxedJSON
function(mean, sd, target) {
  # Validate inputs
  if (is.na(mean) || is.na(sd) || is.na(target)) {
    res$status <- 400
    return(list(error = "invalid_input", message = "mean, sd, and target must be valid numbers"))
  }
  
  if (sd <= 0) {
    res$status <- 400
    return(list(error = "invalid_sd", message = "sd must be positive"))
  }
  
  # Calculate probabilities
  z_score <- (target - mean) / sd
  prob_above <- 1 - pnorm(z_score)
  prob_below <- pnorm(z_score)
  prob_match <- dnorm(z_score)  # Approximate
  
  list(
    success = TRUE,
    mean = mean,
    sd = sd,
    target = target,
    z_score = z_score,
    prob_above = prob_above,
    prob_below = prob_below,
    prob_match_approx = prob_match
  )
}

#* Model diagnostics (optional - for debugging)
#* @post /glmm/diagnose
#* @param observations:list Same as /glmm/fit
#* @param formula:character Optional formula
#* @serializer unboxedJSON
function(observations, formula = NULL) {
  if (length(observations) == 0) {
    res$status <- 400
    return(list(error = "empty_data"))
  }
  
  dt <- rbindlist(observations, fill = TRUE)
  
  if (is.null(formula) || !nzchar(formula)) {
    formula <- "correct ~ 1 + (1|student_id) + (1|item_id)"
  }
  
  result <- safe_glmer(formula, dt, family = binomial)
  
  if (!is.null(result$error)) {
    res$status <- 500
    return(list(error = "fit_failed", message = result$error))
  }
  
  model <- result$model
  
  # Diagnostics
  list(
    success = TRUE,
    convergence = model@optinfo$conv$opt,
    n_obs = nobs(model),
    n_groups = list(
      student_id = length(unique(dt$student_id)),
      item_id = length(unique(dt$item_id))
    ),
    aic = AIC(model),
    bic = BIC(model),
    warnings = result$warnings
  )
}

