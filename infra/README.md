# Infra (Terraform) Starter

This folder provides a minimal Terraform setup for:
- Artifact Registry (GAR) Docker repository
- Cloud Run service(s) for the backend (single or per-environment)

## Structure
- `versions.tf`: Terraform & provider versions
- `providers.tf`: Google provider configuration
- `variables.tf`: Input variables (project, region, repo, service, image, per-env, secrets)
- `artifact_registry.tf`: GAR repository
- `cloud_run.tf`: Cloud Run v2 service(s), runtime Service Account, IAM
- `outputs.tf`: Useful outputs

## Prerequisites
- Google Cloud project created
- Workload Identity Federation or local gcloud auth
- Enable required APIs:
  - Artifact Registry API
  - Cloud Run API
  - Cloud Build API (optional)

## Usage (single-service)

```bash
# Authenticate
gcloud auth application-default login

# Initialize
terraform init

# Review plan
terraform plan \
  -var="project_id=YOUR_PROJECT" \
  -var="region=asia-northeast3" \
  -var="repository_id=apps" \
  -var="service_name=seedtest-api" \
  -var="image_uri=asia-northeast3-docker.pkg.dev/YOUR_PROJECT/apps/seedtest-api:latest"

# Apply
terraform apply -auto-approve \
  -var="project_id=YOUR_PROJECT" \
  -var="region=asia-northeast3" \
  -var="repository_id=apps" \
  -var="service_name=seedtest-api" \
  -var="image_uri=asia-northeast3-docker.pkg.dev/YOUR_PROJECT/apps/seedtest-api:latest"
```

Adjust `image_uri` to the pushed image from CI.

### Usage (multi-environment)

Use the `environments` map to spin up separate Cloud Run services per environment (e.g., `stg`, `prod`). Each env can specify its own image and whether it should be publicly invokable.

Example `terraform.tfvars`:

```
project_id = "YOUR_PROJECT"
region     = "asia-northeast3"
repository_id = "apps"
service_name  = "seedtest-api"

environments = {
  stg = {
    image_uri      = "asia-northeast3-docker.pkg.dev/YOUR_PROJECT/apps/seedtest-api:stg"
    public_invoker = true
  }
  prod = {
    image_uri      = "asia-northeast3-docker.pkg.dev/YOUR_PROJECT/apps/seedtest-api:prod"
    public_invoker = false # behind IAP or allow only specific invokers later
  }
}

# Optional: Secret Manager wiring per environment
secrets_by_env = {
  stg = {
    SENTRY_DSN = { secret = "sentry_dsn", version = "latest" }
  }
  prod = {
    SENTRY_DSN = { secret = "sentry_dsn", version = "latest" }
  }
}
```

Then:

```bash
terraform init
terraform plan
terraform apply -auto-approve
```

### Runtime Service Account and secrets

- A runtime Service Account is created: `var.runtime_sa_name` (default `seedtest-api-runtime`).
- The Cloud Run services run as this SA and it is granted `roles/secretmanager.secretAccessor` at the project level for simplicity.
- Environment variables backed by Secret Manager can be injected via `secrets_by_env`:
  - Keys are the container env var names, values are `{ secret = "<secret-name>", version = "<version|latest>" }`.
  - For single-service mode, you can also use a `default` section: `secrets_by_env = { default = { ... } }`.

For tighter security, consider replacing the project-level role with per-secret bindings using `google_secret_manager_secret_iam_member` and restricting `public_invoker` to `false` with controlled invokers.
