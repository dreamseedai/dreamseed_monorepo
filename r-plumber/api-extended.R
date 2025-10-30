# Extended R Plumber API endpoints
# Add to api.R or load as additional file

#* Get random effects for specific groups
#* @post /glmm/ranef
#* @param model:list Compact model from /glmm/fit
#* @param group:character Group name (student_id or item_id)
#* @param ids:list Optional list of specific IDs to return
#* @serializer unboxedJSON
function(model, group, ids = NULL) {
  if (is.null(model) || is.null(group)) {
    res$status <- 400
    return(list(error = "invalid_input", message = "model and group required"))
  }
  
  # Extract random effects for the specified group
  re <- model$random_effects[[group]]
  
  if (is.null(re)) {
    res$status <- 404
    return(list(error = "group_not_found", message = sprintf("Group '%s' not found in model", group)))
  }
  
  # Filter by specific IDs if provided
  if (!is.null(ids) && length(ids) > 0) {
    re_filtered <- lapply(re, function(effect_list) {
      effect_list[names(effect_list) %in% ids]
    })
    re <- re_filtered
  }
  
  list(
    success = TRUE,
    group = group,
    random_effects = re,
    n_groups = length(re[[1]])
  )
}

#* Get model coefficients summary
#* @post /glmm/coef
#* @param model:list Compact model from /glmm/fit
#* @serializer unboxedJSON
function(model) {
  if (is.null(model)) {
    res$status <- 400
    return(list(error = "invalid_input", message = "model required"))
  }
  
  list(
    success = TRUE,
    fixed_effects = model$fixed_effects,
    random_effects_summary = lapply(model$random_effects, function(re_group) {
      lapply(re_group, function(effects) {
        list(
          mean = mean(unlist(effects)),
          sd = sd(unlist(effects)),
          min = min(unlist(effects)),
          max = max(unlist(effects)),
          n = length(effects)
        )
      })
    })
  )
}

#* Batch student ability estimates
#* @post /analysis/student-abilities
#* @param model:list Compact GLMM model
#* @param student_ids:list List of student IDs
#* @serializer unboxedJSON
function(model, student_ids) {
  if (is.null(model) || length(student_ids) == 0) {
    res$status <- 400
    return(list(error = "invalid_input"))
  }
  
  intercept <- model$fixed_effects$`(Intercept)` %||% 0
  student_effects <- model$random_effects$student_id$`(Intercept)` %||% list()
  
  abilities <- vapply(student_ids, function(sid) {
    intercept + (student_effects[[as.character(sid)]] %||% 0)
  }, numeric(1))
  
  list(
    success = TRUE,
    abilities = setNames(as.list(abilities), student_ids),
    mean_ability = mean(abilities),
    sd_ability = sd(abilities)
  )
}

#* Batch item difficulty estimates
#* @post /analysis/item-difficulties
#* @param model:list Compact GLMM model
#* @param item_ids:list List of item IDs
#* @serializer unboxedJSON
function(model, item_ids) {
  if (is.null(model) || length(item_ids) == 0) {
    res$status <- 400
    return(list(error = "invalid_input"))
  }
  
  intercept <- model$fixed_effects$`(Intercept)` %||% 0
  item_effects <- model$random_effects$item_id$`(Intercept)` %||% list()
  
  difficulties <- vapply(item_ids, function(iid) {
    # Difficulty is negative of item effect (higher difficulty = lower probability)
    -(intercept + (item_effects[[as.character(iid)]] %||% 0))
  }, numeric(1))
  
  list(
    success = TRUE,
    difficulties = setNames(as.list(difficulties), item_ids),
    mean_difficulty = mean(difficulties),
    sd_difficulty = sd(difficulties)
  )
}

#* Expected score for student on specific items
#* @post /analysis/expected-scores
#* @param model:list Compact GLMM model
#* @param student_id:character Student ID
#* @param item_ids:list List of item IDs
#* @serializer unboxedJSON
function(model, student_id, item_ids) {
  if (is.null(model) || is.null(student_id) || length(item_ids) == 0) {
    res$status <- 400
    return(list(error = "invalid_input"))
  }
  
  intercept <- model$fixed_effects$`(Intercept)` %||% 0
  student_effects <- model$random_effects$student_id$`(Intercept)` %||% list()
  item_effects <- model$random_effects$item_id$`(Intercept)` %||% list()
  
  student_effect <- student_effects[[as.character(student_id)]] %||% 0
  
  scores <- vapply(item_ids, function(iid) {
    item_effect <- item_effects[[as.character(iid)]] %||% 0
    eta <- intercept + student_effect + item_effect
    plogis(eta)  # Probability of correct
  }, numeric(1))
  
  list(
    success = TRUE,
    student_id = student_id,
    expected_scores = setNames(as.list(scores), item_ids),
    total_expected = sum(scores),
    average_probability = mean(scores)
  )
}

#* Recommend next items based on target difficulty
#* @post /analysis/recommend-items
#* @param model:list Compact GLMM model
#* @param student_id:character Student ID
#* @param item_pool:list List of available item IDs
#* @param target_probability:numeric Target success probability (default 0.7)
#* @param n_items:numeric Number of items to recommend (default 5)
#* @serializer unboxedJSON
function(model, student_id, item_pool, target_probability = 0.7, n_items = 5) {
  if (is.null(model) || is.null(student_id) || length(item_pool) == 0) {
    res$status <- 400
    return(list(error = "invalid_input"))
  }
  
  intercept <- model$fixed_effects$`(Intercept)` %||% 0
  student_effects <- model$random_effects$student_id$`(Intercept)` %||% list()
  item_effects <- model$random_effects$item_id$`(Intercept)` %||% list()
  
  student_effect <- student_effects[[as.character(student_id)]] %||% 0
  
  # Calculate probability for each item
  item_probs <- vapply(item_pool, function(iid) {
    item_effect <- item_effects[[as.character(iid)]] %||% 0
    eta <- intercept + student_effect + item_effect
    plogis(eta)
  }, numeric(1))
  
  # Calculate distance from target
  distances <- abs(item_probs - target_probability)
  
  # Get top n items closest to target
  n <- min(n_items, length(item_pool))
  top_indices <- order(distances)[1:n]
  
  list(
    success = TRUE,
    student_id = student_id,
    target_probability = target_probability,
    recommended_items = item_pool[top_indices],
    expected_probabilities = item_probs[top_indices],
    distances_from_target = distances[top_indices]
  )
}

#* Model comparison using AIC/BIC
#* @post /analysis/model-compare
#* @param observations:list Same as /glmm/fit
#* @param formulas:list List of formula strings to compare
#* @serializer unboxedJSON
function(observations, formulas) {
  if (length(observations) == 0 || length(formulas) == 0) {
    res$status <- 400
    return(list(error = "invalid_input"))
  }
  
  dt <- rbindlist(observations, fill = TRUE)
  
  results <- lapply(seq_along(formulas), function(i) {
    formula <- formulas[[i]]
    result <- safe_glmer(formula, dt, family = binomial)
    
    if (!is.null(result$error)) {
      return(list(
        formula = formula,
        converged = FALSE,
        error = result$error
      ))
    }
    
    model <- result$model
    list(
      formula = formula,
      converged = model@optinfo$conv$opt == 0,
      aic = AIC(model),
      bic = BIC(model),
      n_obs = nobs(model),
      warnings = result$warnings
    )
  })
  
  # Find best model
  aics <- sapply(results, function(r) if (r$converged) r$aic else Inf)
  best_idx <- which.min(aics)
  
  list(
    success = TRUE,
    comparisons = results,
    best_model = list(
      index = best_idx,
      formula = formulas[[best_idx]],
      aic = results[[best_idx]]$aic,
      bic = results[[best_idx]]$bic
    )
  )
}

