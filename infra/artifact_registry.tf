resource "google_artifact_registry_repository" "apps" {
  location      = var.region
  repository_id = var.repository_id
  description   = "Apps Docker images"
  format        = "DOCKER"
}
