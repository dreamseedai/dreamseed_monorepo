variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "job_name" {
  description = "Cloud Run Job name"
  type        = string
}

variable "image" {
  description = "Container image URI for the job"
  type        = string
}

variable "env" {
  description = "Environment name (stg|prod)"
  type        = string
  default     = "stg"
}

variable "database_url" {
  description = "DATABASE_URL for Alembic"
  type        = string
  sensitive   = true
}

variable "command" {
  description = "Command to execute"
  type        = list(string)
  default     = ["/bin/sh"]
}

variable "args" {
  description = "Arguments for the command"
  type        = list(string)
  default     = ["-lc", "cd /app/seedtest_api && alembic -c alembic.ini upgrade head"]
}

variable "cpu" {
  description = "vCPU for job"
  type        = number
  default     = 1
}

variable "memory" {
  description = "Memory for job"
  type        = string
  default     = "512Mi"
}

variable "task_timeout" {
  description = "Timeout for a single task"
  type        = string
  default     = "600s"
}
