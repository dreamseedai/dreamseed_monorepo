variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  description = "GCP region (e.g., asia-northeast3)"
  default     = "asia-northeast3"
}

variable "repository_id" {
  type        = string
  description = "Artifact Registry repository ID"
  default     = "apps"
}

variable "service_name" {
  type        = string
  description = "Cloud Run service base name"
  default     = "seedtest-api"
}

variable "image_uri" {
  type        = string
  description = "Container image URI (e.g., region-docker.pkg.dev/project/repo/service:tag)"
}

# Per-environment configuration. Keys are environment names (e.g., "stg", "prod").
# Each environment can override image_uri and public invoker setting.
variable "environments" {
  description = "Per-environment Cloud Run settings"
  type = map(object({
    image_uri      = string
    public_invoker = optional(bool, true)
    service_name   = optional(string)
  }))
  default = {}
}

# Runtime Service Account for Cloud Run (used by all environments)
variable "runtime_sa_name" {
  type        = string
  description = "Runtime Service Account name for Cloud Run"
  default     = "seedtest-api-runtime"
}

# Secret Manager references by environment.
# Example:
# secrets_by_env = {
#   stg = {
#     SENTRY_DSN = { secret = "sentry_dsn", version = "latest" }
#   }
#   prod = {
#     SENTRY_DSN = { secret = "sentry_dsn", version = "latest" }
#   }
# }
variable "secrets_by_env" {
  description = "Map of environment to env var -> secret ref (name, version)"
  type = map(map(object({
    secret  = string
    version = string
  })))
  default = {}
}
