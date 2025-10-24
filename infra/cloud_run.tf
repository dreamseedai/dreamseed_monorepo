############################################
# Runtime Service Account and Permissions  #
############################################

resource "google_service_account" "runtime" {
  account_id   = var.runtime_sa_name
  display_name = "Cloud Run Runtime SA"
}

# Grant Secret Manager access at the project level for simplicity.
# For least privilege, bind to specific secrets via google_secret_manager_secret_iam_member.
resource "google_project_iam_member" "runtime_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

############################################
# Single-service (legacy) deployment path   #
############################################

resource "google_cloud_run_v2_service" "backend" {
  count    = length(var.environments) == 0 ? 1 : 0
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.runtime.email

    containers {
      image = var.image_uri
      ports {
        container_port = 8080
      }
      resources {
        cpu_idle = true
      }
      # Static env
      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }

      # Optional secret envs under a pseudo "default" environment key
      dynamic "env" {
        for_each = lookup(var.secrets_by_env, "default", {})
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
          }
        }
      }
    }
    scaling {
      max_instance_count = 10
    }
  }

  ingress = "INGRESS_TRAFFIC_ALL"
}

resource "google_cloud_run_service_iam_member" "invoker" {
  count    = length(var.environments) == 0 ? 1 : 0
  location = var.region
  project  = var.project_id
  service  = google_cloud_run_v2_service.backend[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

############################################
# Multi-environment deployment path         #
############################################

locals {
  env_settings = var.environments
}

resource "google_cloud_run_v2_service" "backend_env" {
  for_each = local.env_settings

  name     = coalesce(try(each.value.service_name, null), "${var.service_name}-${each.key}")
  location = var.region

  template {
    service_account = google_service_account.runtime.email

    containers {
      image = each.value.image_uri
      ports {
        container_port = 8080
      }
      resources {
        cpu_idle = true
      }
      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }

      # Secret Manager env wiring per environment
      dynamic "env" {
        for_each = lookup(var.secrets_by_env, each.key, {})
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
          }
        }
      }
    }
    scaling {
      max_instance_count = 10
    }
  }

  ingress = "INGRESS_TRAFFIC_ALL"
}

resource "google_cloud_run_service_iam_member" "invoker_env" {
  for_each = { for k, v in local.env_settings : k => v if try(v.public_invoker, true) }

  location = var.region
  project  = var.project_id
  service  = google_cloud_run_v2_service.backend_env[each.key].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
