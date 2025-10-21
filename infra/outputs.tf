output "artifact_registry_repo" {
  value       = google_artifact_registry_repository.apps.id
  description = "Artifact Registry repo resource ID"
}

output "cloud_run_service_name" {
  description = "Cloud Run service name (legacy single-service mode)"
  value       = length(var.environments) == 0 ? google_cloud_run_v2_service.backend[0].name : null
}

output "cloud_run_service_names_by_env" {
  description = "Map of env -> Cloud Run service names (multi-env mode)"
  value       = { for k, v in google_cloud_run_v2_service.backend_env : k => v.name }
}

output "runtime_service_account_email" {
  description = "Email of the Cloud Run runtime Service Account"
  value       = google_service_account.runtime.email
}
