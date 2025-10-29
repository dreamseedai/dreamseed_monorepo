# GKE manifests (seedtest)

This folder contains production-ready manifests for the seedtest namespace.

Apply order
1. Namespace and policies
   - ops/k8s/namespace/
2. Internal services (no public Ingress)
   - ops/k8s/r-*-plumber/
3. Public-facing services
   - ops/k8s/seedtest-api/
   - ops/k8s/portal-frontend/
4. Batch and schedules
   - ops/k8s/jobs/
   - ops/k8s/cron/

Notes and gotchas
- cert-manager: ClusterIssuer name defaults to `letsencrypt`. Change if your issuer differs.
- ingress-nginx: seedtest-api NetworkPolicy assumes the ingress controller namespace is labeled `app.kubernetes.io/name=ingress-nginx`. Adjust if your cluster uses different labels.
- DNS and egress: NetworkPolicies explicitly allow DNS (UDP/TCP 53 to kube-system) and external HTTPS (443). Internal traffic to services uses container port 8000.
- HPA: Requires metrics-server to be installed and healthy.
- R Plumber health: Probes use `GET /health` on port 8000. Update if your services differ.
- Registry: Images point to `ghcr.io/dreamseedai/<app>:<tag>`. To switch to Artifact Registry, use `asia-northeast3-docker.pkg.dev/univprepai/dreamseed/<app>:<tag>`.

Quick apply
- kubectl apply -f ops/k8s/namespace/
- kubectl apply -f ops/k8s/r-glmm-plumber/
- kubectl apply -f ops/k8s/r-irt-plumber/
- kubectl apply -f ops/k8s/r-brms-plumber/
- kubectl apply -f ops/k8s/r-forecast-plumber/
- kubectl apply -f ops/k8s/seedtest-api/
- kubectl apply -f ops/k8s/portal-frontend/
- kubectl apply -f ops/k8s/jobs/
- kubectl apply -f ops/k8s/cron/

Verification
- kubectl -n seedtest get deploy,svc,hpa,pdb,ing
- kubectl -n seedtest describe networkpolicy seedtest-api-allow-ingress