# IRT Plumber API (mirt)

suppressPackageStartupMessages({
  library(plumber)
  library(mirt)
  library(data.table)
  library(jsonlite)
})

#* Health
#* @get /healthz
function(){ list(status="ok", service="r-irt-plumber", version=Sys.getenv("R_IRT_VERSION","v0.1"), time=as.character(Sys.time())) }

#* Calibrate IRT model (supports observations or responses)
#* @post /irt/calibrate
#* @param payload:body JSON with either:
#*   - observations: list of {user_id, item_id, is_correct}
#*   - or responses: matrix-like rows (persons) of 0/1/NA
#*   - optional: model ("2PL" default), anchors (list of {item_id, params:{a,b,c}, fixed:true|false})
function(req, res, payload){
  tryCatch({
    if (is.raw(payload)) payload <- rawToChar(payload)
    if (is.character(payload)) payload <- jsonlite::fromJSON(payload, simplifyVector = FALSE)

    # Build response matrix
    model_type <- if (!is.null(payload$model)) as.character(payload$model) else "2PL"

    resp <- NULL
    user_ids <- NULL
    item_ids <- NULL
    if (!is.null(payload$observations)) {
      # observations to wide 0/1/NA matrix
      obs <- data.table::rbindlist(lapply(payload$observations, as.list), fill = TRUE)
      if (!all(c("user_id","item_id","is_correct") %in% names(obs))) {
        res$status <- 400; return(list(error="observations must include user_id,item_id,is_correct"))
      }
      obs[, user_id := as.character(user_id)]
      obs[, item_id := as.character(item_id)]
      # Coerce is_correct to integer 0/1 with NA preserved
      obs[, is_correct := suppressWarnings(as.integer(ifelse(is.na(is_correct), NA, ifelse(as.logical(is_correct), 1, 0))))]
      # Aggregate duplicates by mean-round
      wide <- dcast(obs, user_id ~ item_id, value.var = "is_correct",
                    fun.aggregate = function(x) as.integer(round(mean(x, na.rm = TRUE))), fill = NA_integer_)
      user_ids <- wide[[1]]
      item_ids <- names(wide)[-1]
      resp <- as.matrix(wide[, -1, with = FALSE])
      rownames(resp) <- user_ids
      colnames(resp) <- item_ids
    } else if (!is.null(payload$responses)) {
      # responses: array of arrays (0/1/NA)
      resp <- do.call(rbind, lapply(payload$responses, function(r) unlist(r)))
      if (is.null(colnames(resp))) {
        colnames(resp) <- paste0("I", seq_len(ncol(resp)))
      }
      item_ids <- colnames(resp)
      # user_ids remain NULL in this case
    } else {
      res$status <- 400; return(list(error="missing observations or responses"))
    }

    # default unidimensional model (2PL/3PL)
    itemtype <- if (toupper(model_type) %in% c("2PL","3PL")) toupper(model_type) else "2PL"
    mod <- mirt::mirt(resp, 1, itemtype = itemtype, verbose = FALSE)

    # item params
    ip <- coef(mod, IRTpars = TRUE, simplify = TRUE)
    items <- lapply(names(ip), function(nm){
      v <- ip[[nm]]
      if (!is.numeric(v)) return(NULL)
      list(item_id = nm, params = list(a = unname(v['a']), b = unname(v['b']), c = unname(v['g'])))
    })
    items <- Filter(Negate(is.null), items)

    # ability (EAP) and SE with optional user_id
    fs <- fscores(mod, full.scores.SE = TRUE)
    abilities <- lapply(seq_len(nrow(fs)), function(i){
      out <- list(theta = unname(fs[i,1]), se = unname(fs[i,2]))
      if (!is.null(rownames(resp))) out$user_id <- rownames(resp)[i]
      out
    })

    # Optional: anchor-based linear linking (simple mean/sd on b)
    linking_constants <- NULL
    if (!is.null(payload$anchors)) {
      # Build named vectors of estimated and anchor b values for overlapping items
      est_b <- list()
      for (it in items) {
        est_b[[it$item_id]] <- as.numeric(it$params$b)
      }
      anc_b <- list()
      for (anc in payload$anchors) {
        id <- as.character(anc$item_id %||% anc$item)
        if (!is.null(anc$params) && !is.null(anc$params$b)) {
          anc_b[[id]] <- suppressWarnings(as.numeric(anc$params$b))
        }
      }
      common <- intersect(names(est_b), names(anc_b))
      if (length(common) >= 2) {
        est_vals <- as.numeric(unlist(est_b[common]))
        anc_vals <- as.numeric(unlist(anc_b[common]))
        if (all(is.finite(est_vals)) && all(is.finite(anc_vals))) {
          m_est <- mean(est_vals)
          s_est <- stats::sd(est_vals)
          m_anc <- mean(anc_vals)
          s_anc <- stats::sd(anc_vals)
          if (is.finite(s_est) && s_est > 0 && is.finite(s_anc) && s_anc > 0) {
            A <- s_anc / s_est
            B <- m_anc - A * m_est
            # Transform abilities and item params to anchor scale
            for (i in seq_along(abilities)) {
              abilities[[i]]$theta <- A * abilities[[i]]$theta + B
              if (!is.na(abilities[[i]]$se)) abilities[[i]]$se <- abs(A) * abilities[[i]]$se
            }
            for (i in seq_along(items)) {
              a_old <- as.numeric(items[[i]]$params$a)
              b_old <- as.numeric(items[[i]]$params$b)
              items[[i]]$params$a <- ifelse(is.finite(a_old) && A != 0, a_old / A, a_old)
              items[[i]]$params$b <- ifelse(is.finite(b_old), A * b_old + B, b_old)
            }
            linking_constants <- list(A = unname(A), B = unname(B), n_anchors_used = length(common))
          }
        }
      }
    }

    fit_meta <- list(
      run_id = paste0("irt-fit-", format(Sys.time(), "%Y%m%d%H%M%S")),
      model_spec = list(model = itemtype, n_persons = nrow(resp), n_items = ncol(resp)),
      linking_constants = linking_constants
    )

    list(status='ok', fit_meta=fit_meta, item_params=items, abilities=abilities)
  }, error=function(e){ res$status<-500; list(error=paste0('internal_error: ', conditionMessage(e))) })
}

#* Score abilities using given item params (2PL)
#* @post /irt/score
#* @param payload:body JSON with item_params and responses
function(req, res, payload){
  tryCatch({
    if (is.raw(payload)) payload <- rawToChar(payload)
    if (is.character(payload)) payload <- jsonlite::fromJSON(payload, simplifyVector = FALSE)

    if (is.null(payload$item_params) || is.null(payload$responses)){
      res$status <- 400; return(list(error='missing item_params or responses'))
    }

    # EAP scoring on a fixed theta grid using provided 2PL params (c optional)
    # responses: list of rows (0/1/NA)
    # item_params: list of {item, a, b, c}
    # Return per-person EAP theta and SE

    # Build parameter vectors aligned to item order
    items <- payload$item_params
    n_items <- length(items)
    a <- numeric(n_items)
    b <- numeric(n_items)
    c <- numeric(n_items)
    for (i in seq_len(n_items)){
      it <- items[[i]]
      a[i] <- suppressWarnings(as.numeric(it$a))
      b[i] <- suppressWarnings(as.numeric(it$b))
      c[i] <- if (!is.null(it$c)) suppressWarnings(as.numeric(it$c)) else 0
      if (is.na(a[i])) a[i] <- 1
      if (is.na(b[i])) b[i] <- 0
      if (is.na(c[i])) c[i] <- 0
    }

    theta_grid <- seq(-4, 4, length.out=81)
    prior <- dnorm(theta_grid)

    resp_list <- payload$responses
    n_persons <- length(resp_list)
    results <- vector("list", n_persons)
    for (p in seq_len(n_persons)){
      r <- unlist(resp_list[[p]])
      # pad/trim to n_items
      if (length(r) < n_items) r <- c(r, rep(NA, n_items - length(r)))
      if (length(r) > n_items) r <- r[seq_len(n_items)]
      # Likelihood over grid
      # P(correct|theta) = c + (1-c) * logistic(a*(theta - b))
      # logistic(x) = 1/(1+exp(-x))
      logits <- outer(theta_grid, a, FUN=function(th, aa) th * aa) - matrix(rep(a*b, each=length(theta_grid)), nrow=length(theta_grid))
      invlogit <- 1/(1+exp(-logits))
      P <- matrix(rep(c, each=length(theta_grid)), nrow=length(theta_grid)) + (1 - matrix(rep(c, each=length(theta_grid)), nrow=length(theta_grid))) * invlogit
      # Mask NAs (skip items not answered)
      mask1 <- matrix(as.numeric(r==1), nrow=length(theta_grid), ncol=n_items, byrow=TRUE)
      mask0 <- matrix(as.numeric(r==0), nrow=length(theta_grid), ncol=n_items, byrow=TRUE)
      ll <- rowSums(mask1 * log(P + 1e-12) + mask0 * log(1 - P + 1e-12), na.rm=TRUE)
      post_unnorm <- exp(ll) * prior
      Z <- sum(post_unnorm)
      if (!is.finite(Z) || Z<=0){
        # Degenerate; return NA
        results[[p]] <- list(theta=NA_real_, se=NA_real_)
      } else {
        post <- post_unnorm / Z
        eap <- sum(theta_grid * post)
        se <- sqrt(sum((theta_grid - eap)^2 * post))
        results[[p]] <- list(theta=unname(eap), se=unname(se))
      }
    }

    list(status='ok', abilities=results)
  }, error=function(e){ res$status<-500; list(error=paste0('internal_error: ', conditionMessage(e))) })
}
