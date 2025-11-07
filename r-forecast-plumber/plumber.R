# Plumber entry point
library(plumber)

pr <- plumb("api.R")
pr$run(host = "0.0.0.0", port = 8080)
