# Browser-Compatibility Runbook

## Quick deploy (proxy + TLS)
```bash
sudo network_automation/ops/scripts/deploy_proxy_and_tls.sh dreamseedai.com /var/www/dreamseed/static http://127.0.0.1:8000/ on
```

## Safe dev static server
```bash
sudo network_automation/ops/scripts/ufw_setup.sh 8080
network_automation/ops/scripts/start_http_server.sh 8080 ./public
# open http://<server-ip>:8080
```

## FastAPI notes
- Use explicit allow_origins, not * when allow_credentials=True.
- Cross-site cookies require SameSite=None; Secure; Domain=.<root-domain>.
- Provide /healthz endpoint for monitoring and nginx pass-through.

## HSTS strategy
1. Enable HTTPS redirect. 
2. Run for several days. 
3. Enable HSTS with short max-age. 
4. Increase max-age when stable.

## Playwright smoke
```bash
cd webtests && npm ci && npm run install:browsers
TARGET_URL=https://staging.dreamseedai.com ENV=staging npm test
```

## Port policy
```bash
network_automation/ops/scripts/ports_policy.sh network_automation/ops/nginx
```

## How to apply
1) Copy files into your repo as shown.
2) Fill template variables and run `deploy_proxy_and_tls.sh` on the server (staging first).
3) Wire CI secret `SMOKE_TARGET_URL`.
4) Merge only when Playwright smoke passes and ops checklist is checked.