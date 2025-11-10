R Plumber GLMM/Forecast Microservice (v1.0)

Overview
- Purpose: On-demand GLMM fitting and fast probabilistic forecast to back SeedTest API reports/recommendations.
- Stack: R 4.3, plumber, lme4, data.table, jsonlite, broom.mixed.
- Endpoints:
  - GET /healthz – health check
  - POST /glmm/fit – fit GLMM: correct ~ 1 + (1|student_id) + (1|item_id)
  - POST /glmm/predict – predict probabilities for new (student_id, item_id)
  - POST /forecast/summary – Normal-approx reach probability (mu, sd, target)

Local Run
- R (no Docker):
  R -e "pr <- plumber::plumb('r-plumber/api.R'); pr$run(host='0.0.0.0', port=8000)"

- Docker:
  docker build -t r-glmm-plumber:dev ./r-plumber
  docker run --rm -p 8000:8000 -e PLUMBER_RUN=true r-glmm-plumber:dev

Quick Smoke via curl
- Health:
  curl -s http://localhost:8000/healthz | jq

- Fit GLMM:
  curl -s -X POST http://localhost:8000/glmm/fit \
    -H 'Content-Type: application/json' \
    -d '{
          "observations": [
            {"student_id": "s1", "item_id": "i1", "correct": 1},
            {"student_id": "s1", "item_id": "i2", "correct": 0},
            {"student_id": "s2", "item_id": "i1", "correct": 1},
            {"student_id": "s2", "item_id": "i2", "correct": 1}
          ]
        }' | jq '.status,.metrics'

- Predict:
  curl -s -X POST http://localhost:8000/glmm/predict \
    -H 'Content-Type: application/json' \
    -d '{
          "model": {"fixed_effects": {"(Intercept)": 0}, "ranef": {"student_id": [], "item_id": []}},
          "newdata": [{"student_id": "s1", "item_id": "i1"}]
        }' | jq

- Forecast (Normal):
  curl -s -X POST http://localhost:8000/forecast/summary \
    -H 'Content-Type: application/json' \
    -d '{"mean": 0.2, "sd": 0.6, "target": 0.0}' | jq

Kubernetes
- Kustomize (namespace seedtest by default):
  kubectl apply -k ops/k8s/r-plumber

- Ingress uses r-glmm-plumber.your-domain.com with cert-manager. Change host/issuer as needed or remove Ingress for internal-only service.

Security Notes
- Default manifest exposes Ingress; for internal-only, remove Ingress block and keep ClusterIP Service. Restrict network via NetworkPolicy.
- If external exposure is required, terminate TLS at ingress and lock to allow-listed IPs or require auth at edge.

Integration Pointers
- SeedTest API can POST observations to /glmm/fit, cache the compact model, and call /glmm/predict for batches.
- Forecast endpoint mirrors existing Python Normal approximation; can be swapped later with posterior summaries.

Versioning
- Image tag: ghcr.io/your-org/r-glmm-plumber:1.0.0
- Env: R_PLUMBER_VERSION=v1.0
