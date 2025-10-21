# Cloud Run Job (Migrations)

Terraform module to create a Cloud Run Job for running Alembic migrations using the backend image.

## Inputs
- project_id: GCP project ID
- region: GCP region (e.g., asia-northeast3)
- job_name: Name of the Job (e.g., seedtest-api-migrate-stg)
- image: GAR image URI (e.g., asia-northeast3-docker.pkg.dev/PROJECT/apps/seedtest-api:SHA)
- env: Environment label (stg|prod)
- database_url: DATABASE_URL for Alembic
- command/args: Optional override (default runs `alembic upgrade head` inside /app/seedtest_api)

## Example

module "migrate_job" {
  source       = "./infra/cloudrun_jobs"
  project_id   = var.project_id
  region       = var.region
  job_name     = "seedtest-api-migrate-stg"
  image        = var.image
  env          = "stg"
  database_url = var.database_url
}

# Execute the job (out of band) via gcloud:
# gcloud run jobs execute seedtest-api-migrate-stg --region=asia-northeast3 --wait
