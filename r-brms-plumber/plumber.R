# Plumber entry point for BRMS service
library(plumber)

pr <- plumb("api.R")
pr$run(host = "0.0.0.0", port = 8080)
