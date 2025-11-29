# ------------------------------------------------------------
# plumber_drift.R
#  - Plumber API endpoints for IRT drift detection
#  - 파일 위치: /portal_front/r-irt-plumber/plumber_drift.R
#
# 실행:
#   library(plumber)
#   pr <- plumb("plumber_drift.R")
#   pr$run(host="0.0.0.0", port=8000)
# ------------------------------------------------------------

library(plumber)
library(jsonlite)

# Source the pipeline
source("irt_drift_pipeline.R")

#* @apiTitle IRT Drift Detection API
#* @apiDescription API for detecting item parameter drift in IRT models
#* @apiVersion 1.0.0

#* Health check
#* @get /health
function() {
  list(
    status = "ok",
    timestamp = Sys.time(),
    service = "irt-drift-api"
  )
}

#* Run drift detection pipeline
#* @post /drift/run
#* @param use_3pl:bool Use 3PL model (default: true)
#* @param multidim:bool Use multidimensional model (default: true)
#* @param K:int Number of dimensions for MIRT (default: 2)
#* @param iter:int MCMC iterations (default: 1000)
#* @param chains:int MCMC chains (default: 2)
#* @serializer json
function(use_3pl = TRUE, multidim = TRUE, K = 2, iter = 1000, chains = 2) {
  tryCatch({
    result <- run_drift(
      use_3pl = as.logical(use_3pl),
      multidim = as.logical(multidim),
      K = as.integer(K),
      iter = as.integer(iter),
      chains = as.integer(chains)
    )
    
    # Convert drift tibble to list for JSON
    result$drift <- as.list(result$drift)
    
    list(
      success = TRUE,
      data = result,
      timestamp = Sys.time()
    )
  }, error = function(e) {
    list(
      success = FALSE,
      error = as.character(e),
      timestamp = Sys.time()
    )
  })
}

#* Get drift items
#* @get /drift/items
#* @param since_days:int Days to look back (default: 30)
#* @param only_flagged:bool Only return flagged items (default: true)
#* @param limit:int Maximum results (default: 500)
#* @serializer json
function(since_days = 30, only_flagged = TRUE, limit = 500) {
  tryCatch({
    items <- get_drift_items(
      since_days = as.integer(since_days),
      only_flagged = as.logical(only_flagged),
      limit = as.integer(limit)
    )
    
    list(
      success = TRUE,
      count = nrow(items),
      data = items,
      timestamp = Sys.time()
    )
  }, error = function(e) {
    list(
      success = FALSE,
      error = as.character(e),
      timestamp = Sys.time()
    )
  })
}

#* Get latest item parameters
#* @post /params/latest
#* @param item_ids:list List of item IDs (optional)
#* @param limit:int Maximum results if no item_ids (default: 200)
#* @serializer json
function(req, item_ids = NULL, limit = 200) {
  tryCatch({
    # Parse JSON body if present
    if (!is.null(req$postBody)) {
      body <- jsonlite::fromJSON(req$postBody)
      if (!is.null(body$item_ids)) {
        item_ids <- body$item_ids
      }
    }
    
    params <- get_latest_params(
      item_ids = item_ids,
      limit = as.integer(limit)
    )
    
    list(
      success = TRUE,
      count = nrow(params),
      data = params,
      timestamp = Sys.time()
    )
  }, error = function(e) {
    list(
      success = FALSE,
      error = as.character(e),
      timestamp = Sys.time()
    )
  })
}

#* Get drift statistics summary
#* @get /drift/stats
#* @param since_days:int Days to look back (default: 30)
#* @serializer json
function(since_days = 30) {
  tryCatch({
    con <- pg_conn()
    on.exit(DBI::dbDisconnect(con), add = TRUE)
    
    sql <- sprintf("
      SELECT 
        COUNT(DISTINCT item_id) AS total_items,
        SUM(CASE WHEN flag_a THEN 1 ELSE 0 END) AS flagged_a,
        SUM(CASE WHEN flag_b THEN 1 ELSE 0 END) AS flagged_b,
        SUM(CASE WHEN flag_c THEN 1 ELSE 0 END) AS flagged_c,
        AVG(ABS(delta_a)) AS avg_abs_delta_a,
        AVG(ABS(delta_b)) AS avg_abs_delta_b,
        AVG(ABS(delta_c)) AS avg_abs_delta_c,
        MAX(created_at) AS last_run
      FROM item_drift_log
      WHERE created_at >= NOW() - INTERVAL '%d days'
    ", as.integer(since_days))
    
    stats <- DBI::dbGetQuery(con, sql)
    
    list(
      success = TRUE,
      data = stats,
      timestamp = Sys.time()
    )
  }, error = function(e) {
    list(
      success = FALSE,
      error = as.character(e),
      timestamp = Sys.time()
    )
  })
}

#* Get configuration
#* @get /config
#* @serializer json
function() {
  list(
    success = TRUE,
    data = DRIFT_CONF,
    timestamp = Sys.time()
  )
}

#* Update configuration (admin only)
#* @post /config
#* @param window_days:int Moving window size in days
#* @param tau_b:numeric Threshold for difficulty drift
#* @param tau_a:numeric Threshold for discrimination drift
#* @param tau_c:numeric Threshold for guessing drift
#* @param prob_thresh:numeric Probability threshold for flagging
#* @serializer json
function(req, window_days = NULL, tau_b = NULL, tau_a = NULL, tau_c = NULL, prob_thresh = NULL) {
  tryCatch({
    # Parse JSON body
    if (!is.null(req$postBody)) {
      body <- jsonlite::fromJSON(req$postBody)
      
      if (!is.null(body$window_days)) DRIFT_CONF$window_days <<- as.integer(body$window_days)
      if (!is.null(body$tau_b)) DRIFT_CONF$tau_b <<- as.numeric(body$tau_b)
      if (!is.null(body$tau_a)) DRIFT_CONF$tau_a <<- as.numeric(body$tau_a)
      if (!is.null(body$tau_c)) DRIFT_CONF$tau_c <<- as.numeric(body$tau_c)
      if (!is.null(body$prob_thresh)) DRIFT_CONF$prob_thresh <<- as.numeric(body$prob_thresh)
    }
    
    list(
      success = TRUE,
      message = "Configuration updated",
      data = DRIFT_CONF,
      timestamp = Sys.time()
    )
  }, error = function(e) {
    list(
      success = FALSE,
      error = as.character(e),
      timestamp = Sys.time()
    )
  })
}
