resource "google_cloud_run_v2_job" "migrate" {
  name     = var.job_name
  location = var.region

  template {
    template {
      containers {
        image = var.image
        env {
          name  = "DATABASE_URL"
          value = var.database_url
        }
        env {
          name  = "ENV"
          value = var.env
        }
        resources {
          cpu_idle         = true
          limits = {
            cpu    = tostring(var.cpu)
            memory = var.memory
          }
        }
        command = var.command
        args    = var.args
      }
      timeout = var.task_timeout
    }
  }
}
