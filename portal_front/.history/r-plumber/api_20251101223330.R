# plumber API for GLMM diagnostics/forecast

# Load libraries
suppressPackageStartupMessages({
  library(plumber)
  library(lme4)
  library(data.table)
  library(jsonlite)
  library(broom.mixed)
})

# Helpers
inv_logit <- function(x) 1 / (1 + exp(-x))

safe_glmer <- function(formula, data, family = binomial(), control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))) {
  result <- list(model = NULL, warnings = NULL, error = NULL)
  w <- NULL
  res <- withCallingHandlers(
    tryCatch({
      m <- glmer(formula, data = data, family = family, control = control)
      m
    }, error = function(e) {
      result$error <<- paste0("glmer_error: ", conditionMessage(e))
      NULL
    }),
    warning = function(warn) {
      w <<- c(w, conditionMessage(warn))
      invokeRestart("muffleWarning")
    }
  )
  result$model <- res
  result$warnings <- w
  result
}

safe_lmer <- function(formula, data, control = lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))) {
  result <- list(model = NULL, warnings = NULL, error = NULL)
  w <- NULL
  res <- withCallingHandlers(
    tryCatch({
      m <- lmer(formula, data = data, control = control)
      m
    }, error = function(e) {
      result$error <<- paste0("lmer_error: ", conditionMessage(e))
      NULL
    }),
    warning = function(warn) {
      w <<- c(w, conditionMessage(warn))
      invokeRestart("muffleWarning")
    }
  )
  result$model <- res
  result$warnings <- w
  result
}

serialize_ranef <- function(model) {
  re <- ranef(model)
  out <- list()
  for (grp in names(re)) {
    dt <- data.table::as.data.table(re[[grp]], keep.rownames = TRUE)
    setnames(dt, c("id", names(dt)[2:ncol(dt)]))
    out[[grp]] <- dt
  }
  out
}

#* Health check
#* @get /healthz
function() {
  list(status = "ok", service = "r-glmm-plumber", version = Sys.getenv("R_PLUMBER_VERSION", "v1.0"), time = as.character(Sys.time()))
}

#* Fit a GLMM (binomial) with random intercepts for student and item
#* @post /glmm/fit
#* @param payload:body JSON payload with fields: observations (array of {student_id, item_id, correct}) and optional formula
function(req, res, payload) {
  tryCatch({
    if (is.raw(payload)) payload <- rawToChar(payload)
    if (is.character(payload)) payload <- jsonlite::fromJSON(payload, simplifyVector = FALSE)

    if (is.null(payload$observations)) {
      res$status <- 400
      return(list(error = "missing observations"))
    }

    dt <- data.table::rbindlist(lapply(payload$observations, as.list), fill = TRUE)
    # basic validation
    required <- c("student_id", "item_id", "correct")
    missing_cols <- setdiff(required, names(dt))
    if (length(missing_cols) > 0) {
      res$status <- 400
      return(list(error = paste0("missing columns: ", paste(missing_cols, collapse=","))))
    }

    dt[, `:=`(
      student_id = as.factor(student_id),
      item_id = as.factor(item_id),
      correct = as.integer(correct)
    )]

    fml <- if (!is.null(payload$formula)) as.formula(payload$formula) else as.formula("correct ~ 1 + (1|student_id) + (1|item_id)")

    fit <- safe_glmer(fml, dt, family = binomial())

    if (is.null(fit$model)) {
      res$status <- 500
      return(list(error = fit$error, warnings = fit$warnings))
    }

    model <- fit$model

    # Summaries
    fixef_vals <- as.list(lme4::fixef(model))
    conf_ok <- TRUE
    ll <- tryCatch(as.numeric(stats::logLik(model)), error = function(e) NA_real_)
    aic <- tryCatch(stats::AIC(model), error = function(e) NA_real_)
    bic <- tryCatch(stats::BIC(model), error = function(e) NA_real_)

    re_serialized <- serialize_ranef(model)

    # Return compact model representation for downstream prediction
    model_pack <- list(
      formula = as.character(formula(model)),
      family = "binomial",
      fixed_effects = fixef_vals,
      ranef = re_serialized,
      levels = list(
        student_id = levels(dt$student_id),
        item_id = levels(dt$item_id)
      )
    )

    list(
      status = "ok",
      metrics = list(logLik = ll, AIC = aic, BIC = bic),
      warnings = fit$warnings,
      model = model_pack
    )
  }, error = function(e) {
    res$status <- 500
    list(error = paste0("internal_error: ", conditionMessage(e)))
  })
}

#* Predict probabilities for new observations using a compact model representation
#* @post /glmm/predict
#* @param payload:body JSON payload with fields: model (from /glmm/fit) and newdata (array of {student_id, item_id})
function(req, res, payload) {
  tryCatch({
    if (is.raw(payload)) payload <- rawToChar(payload)
    if (is.character(payload)) payload <- jsonlite::fromJSON(payload, simplifyVector = FALSE)

    if (is.null(payload$model) || is.null(payload$newdata)) {
      res$status <- 400
      return(list(error = "missing model or newdata"))
    }

    m <- payload$model
    fixef_intercept <- as.numeric(m$fixed_effects[[1]])

    # Build lookup tables for random effects
    # Expect ranef list to have groups named like student_id and item_id with columns: id, `(Intercept)`
    re_student <- NULL
    re_item <- NULL
    if (!is.null(m$ranef$student_id)) {
      re_student <- data.table::as.data.table(m$ranef$student_id)
      setnames(re_student, make.names(names(re_student)))
    }
    if (!is.null(m$ranef$item_id)) {
      re_item <- data.table::as.data.table(m$ranef$item_id)
      setnames(re_item, make.names(names(re_item)))
    }

    nd <- data.table::rbindlist(lapply(payload$newdata, as.list), fill = TRUE)
    if (!all(c("student_id", "item_id") %in% names(nd))) {
      res$status <- 400
      return(list(error = "newdata must include student_id and item_id"))
    }

    setDT(nd)
    if (!is.null(re_student)) nd <- merge(nd, re_student, by.x = "student_id", by.y = "id", all.x = TRUE)
    if (!is.null(re_item)) nd <- merge(nd, re_item, by.x = "item_id", by.y = "id", all.x = TRUE, suffixes = c("_s", "_i"))

    # Column names may be `(Intercept)` or X.Intercept.
    if ("(Intercept)" %in% names(nd)) {
      setnames(nd, "(Intercept)", "intercept_s")
    }
    if ("(Intercept).1" %in% names(nd)) {
      setnames(nd, "(Intercept).1", "intercept_i")
    }
    if ("X.Intercept." %in% names(nd) && is.null(nd$intercept_s)) {
      setnames(nd, "X.Intercept.", "intercept_s")
    }
    if ("X.Intercept..1" %in% names(nd) && is.null(nd$intercept_i)) {
      setnames(nd, "X.Intercept..1", "intercept_i")
    }

    nd[is.na(intercept_s), intercept_s := 0]
    nd[is.na(intercept_i), intercept_i := 0]

    nd[, eta := fixef_intercept + intercept_s + intercept_i]
    nd[, p := inv_logit(eta)]

    list(status = "ok", predictions = nd[, .(student_id, item_id, eta, p)])
  }, error = function(e) {
    res$status <- 500
    list(error = paste0("internal_error: ", conditionMessage(e)))
  })
}

#* Forecast summary using Normal approximation (ability ~ N(mean, sd))
#* @post /forecast/summary
#* @param payload:body JSON payload with fields: mean, sd, target
function(req, res, payload) {
  tryCatch({
    if (is.raw(payload)) payload <- rawToChar(payload)
    if (is.character(payload)) payload <- jsonlite::fromJSON(payload, simplifyVector = TRUE)

    mu <- as.numeric(payload$mean)
    sigma <- as.numeric(payload$sd)
    target <- as.numeric(payload$target)

    if (any(is.na(c(mu, sigma, target))) || sigma <= 0) {
      res$status <- 400
      return(list(error = "invalid mean/sd/target"))
    }

    # P(X >= target) where X ~ N(mu, sigma)
    prob <- 1 - pnorm(target, mean = mu, sd = sigma)

    list(status = "ok", probability = prob, inputs = list(mean = mu, sd = sigma, target = target))
  }, error = function(e) {
    res$status <- 500
    list(error = paste0("internal_error: ", conditionMessage(e)))
  })
}

#* Fit GLMM for progress (weekly scores)
#* @post /glmm/fit_progress
#* @param payload:body JSON with fields: rows (list of {student, topic, week, score}), formula (default: "score ~ week + (week|student) + (1|topic)"), family ("gaussian" or GLM family)
function(req, res, payload) {
  tryCatch({
    if (is.raw(payload)) payload <- rawToChar(payload)
    if (is.character(payload)) payload <- jsonlite::fromJSON(payload, simplifyVector = FALSE)

    rows <- payload$rows
    if (is.null(rows)) {
      res$status <- 400
      return(list(error = "missing rows"))
    }

    dt <- data.table::rbindlist(lapply(rows, as.list), fill = TRUE)
    req_cols <- c("student", "topic", "week", "score")
    miss <- setdiff(req_cols, names(dt))
    if (length(miss) > 0) {
      res$status <- 400
      return(list(error = paste0("missing columns: ", paste(miss, collapse=","))))
    }

    # Coerce types
    dt[, student := as.factor(student)]
    dt[, topic := as.factor(topic)]
    suppressWarnings({ dt[, week := as.integer(week)] })
    suppressWarnings({ dt[, score := as.numeric(score)] })
    dt <- dt[is.finite(score) & !is.na(week)]

    fml_txt <- if (!is.null(payload$formula)) payload$formula else "score ~ week + (week|student) + (1|topic)"
    fam_txt <- if (!is.null(payload$family)) payload$family else "gaussian"

    # Choose lmer for gaussian, glmer otherwise
    if (tolower(as.character(fam_txt)) %in% c("gaussian", "normal")) {
      fit <- safe_lmer(as.formula(fml_txt), dt)
      if (is.null(fit$model)) {
        res$status <- 500
        return(list(error = fit$error, warnings = fit$warnings))
      }
      model <- fit$model
      preds <- tryCatch(predict(model), error = function(e) rep(NA_real_, nrow(dt)))
      rmse <- tryCatch({
        v <- sqrt(mean((dt$score - preds)^2, na.rm = TRUE)); if (is.finite(v)) v else NA_real_
      }, error = function(e) NA_real_)
      ll <- tryCatch(as.numeric(stats::logLik(model)), error = function(e) NA_real_)
      aic <- tryCatch(stats::AIC(model), error = function(e) NA_real_)
      bic <- tryCatch(stats::BIC(model), error = function(e) NA_real_)
      re_serialized <- serialize_ranef(model)

      fit_meta <- list(
        run_id = paste0("glmm-fit-", format(Sys.time(), "%Y%m%d%H%M%S")),
        model_spec = list(
          formula = fml_txt,
          family = "gaussian",
          n = nrow(dt),
          groups = list(students = length(levels(dt$student)), topics = length(levels(dt$topic))),
          warnings = fit$warnings
        )
      )
      metrics <- list(logLik = ll, AIC = aic, BIC = bic, RMSE = rmse)
      return(list(status = "ok", fit_meta = fit_meta, metrics = metrics, random_effects = re_serialized))
    } else {
      # Fallback to binomial/logistic glmer if not gaussian
      fam <- switch(tolower(as.character(fam_txt)),
        binomial = binomial(),
        poisson = poisson(),
        Gamma = Gamma(),
        binomial()
      )
      fit <- safe_glmer(as.formula(fml_txt), dt, family = fam)
      if (is.null(fit$model)) {
        res$status <- 500
        return(list(error = fit$error, warnings = fit$warnings))
      }
      model <- fit$model
      ll <- tryCatch(as.numeric(stats::logLik(model)), error = function(e) NA_real_)
      aic <- tryCatch(stats::AIC(model), error = function(e) NA_real_)
      bic <- tryCatch(stats::BIC(model), error = function(e) NA_real_)
      re_serialized <- serialize_ranef(model)
      fit_meta <- list(
        run_id = paste0("glmm-fit-", format(Sys.time(), "%Y%m%d%H%M%S")),
        model_spec = list(
          formula = fml_txt,
          family = as.character(fam_txt),
          n = nrow(dt),
          groups = list(students = length(levels(dt$student)), topics = length(levels(dt$topic))),
          warnings = fit$warnings
        )
      )
      metrics <- list(logLik = ll, AIC = aic, BIC = bic)
      return(list(status = "ok", fit_meta = fit_meta, metrics = metrics, random_effects = re_serialized))
    }
  }, error = function(e) {
    res$status <- 500
    list(error = paste0("internal_error: ", conditionMessage(e)))
  })
}

# Run if called directly
if (identical(Sys.getenv("PLUMBER_RUN"), "true")) {
  ofile <- tryCatch(sys.frame(1)$ofile, error = function(e) NULL)
  pr <- plumb(file = if (!is.null(ofile)) ofile else "api.R")
  pr$run(host = "0.0.0.0", port = as.integer(Sys.getenv("PORT", 8000)))
}
