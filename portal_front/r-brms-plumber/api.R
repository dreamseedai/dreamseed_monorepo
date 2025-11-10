# plumber API for Bayesian growth (brms/rstanarm fallback)

suppressPackageStartupMessages({
  library(plumber)
  library(data.table)
  library(jsonlite)
})

# Try load brms; fallback to rstanarm if unavailable
HAS_BRMS <- requireNamespace("brms", quietly = TRUE)
HAS_RSAN <- requireNamespace("rstanarm", quietly = TRUE)

#* Health
#* @get /healthz
function(){ list(status="ok", service="r-brms-plumber", engine=if (HAS_BRMS) "brms" else if (HAS_RSAN) "rstanarm" else "none", time=as.character(Sys.time())) }

#* Fit Bayesian growth model: score ~ week + (week|student)
#* @post /growth/fit
#* @param payload:body JSON with rows = [{student, week, score}], family = gaussian/logit, iter, chains
function(req, res){
  payload <- tryCatch({
    body <- req$postBody
    if (is.raw(body)) body <- rawToChar(body)
    fromJSON(body, simplifyVector = FALSE)
  }, error=function(e){ res$status<-400; return(list(error=paste0("invalid_json: ", e$message))) })
  if (is.list(payload) && !is.null(payload$error)) return(payload)

  rows <- payload$rows
  if (is.null(rows)) { res$status<-400; return(list(error="missing rows")) }
  dt <- as.data.table(rbindlist(lapply(rows, as.list), fill=TRUE))
  req <- c("student","week","score")
  miss <- setdiff(req, names(dt))
  if (length(miss)>0) { res$status<-400; return(list(error=paste0("missing cols: ", paste(miss, collapse=",")))) }
  dt[, student := as.factor(student)]
  dt[, week := as.numeric(week)]
  dt[, score := as.numeric(score)]

  fam <- tolower(as.character(payload$family %||% "gaussian"))
  iter <- as.integer(payload$iter %||% 1000)
  chains <- as.integer(payload$chains %||% 2)

  fit_obj <- NULL
  engine <- NULL
  try({
    if (HAS_BRMS) {
      engine <- "brms"
      # Prior can be customized; using weakly informative default
      formula <- brms::bf(score ~ week + (week|student))
      family <- if (fam %in% c("bernoulli","logit")) brms::bernoulli() else brms::gaussian()
      fit_obj <- brms::brm(formula, data=dt, family=family, iter=iter, chains=chains, refresh=0)
    } else if (HAS_RSAN) {
      engine <- "rstanarm"
      formula <- stats::as.formula("score ~ week + (week|student)")
      if (fam %in% c("bernoulli","logit")) {
        fit_obj <- rstanarm::stan_glmer(formula, data=dt, family=stats::binomial(link="logit"), iter=iter, chains=chains, refresh=0)
      } else {
        fit_obj <- rstanarm::stan_lmer(formula, data=dt, iter=iter, chains=chains, refresh=0)
      }
    }
  }, silent=TRUE)

  if (is.null(fit_obj)) { res$status<-500; return(list(error="no_engine_or_fit_failed")) }

  # Posterior summary for week effect
  post <- tryCatch({
    if (HAS_BRMS) {
      ss <- brms::posterior_summary(fit_obj, pars=c("b_week"))
      list(mean = unname(ss[1,"Estimate"]) , l95 = unname(ss[1,"Q2.5"]), u95 = unname(ss[1,"Q97.5"]))
    } else {
      ss <- summary(fit_obj)$coefficients
      # Approximate normal CI for b_week
      est <- ss["week", "Estimate"]; se <- ss["week","Std. Error"]
      list(mean=unname(est), l95=unname(est-1.96*se), u95=unname(est+1.96*se))
    }
  }, error=function(e) list(mean=NA_real_, l95=NA_real_, u95=NA_real_))

  list(status="ok", engine=engine, posterior=post)
}

#* Predict goal attainment probability using posterior (toy: Normal approx)
#* @post /growth/predict
#* @param payload:body JSON with mean, sd, target
function(req, res){
  payload <- tryCatch({
    body <- req$postBody
    if (is.raw(body)) body <- rawToChar(body)
    fromJSON(body, simplifyVector = TRUE)
  }, error=function(e){ res$status<-400; return(list(error=paste0("invalid_json: ", e$message))) })
  mu <- as.numeric(payload$mean %||% NA)
  sd <- as.numeric(payload$sd %||% NA)
  target <- as.numeric(payload$target %||% NA)
  if (is.na(mu) || is.na(sd) || is.na(target) || sd<=0){ res$status<-400; return(list(error="invalid mean/sd/target")) }
  prob <- 1 - pnorm(target, mean=mu, sd=sd)
  list(status="ok", probability=prob)
}

if (identical(Sys.getenv("PLUMBER_RUN"), "true")){
  pr <- plumb("api.R"); pr$run(host="0.0.0.0", port=as.integer(Sys.getenv("PORT", 8000)))
}
