# DreamSeed Browser Compatibility Runbook

## 🎯 Overview
This runbook ensures DreamSeed services pass modern browser security and compatibility requirements.

## 🚀 Quick Deploy (Proxy + TLS)

### Staging Deployment
```bash
# Deploy nginx proxy with TLS (HSTS off for staging)
sudo ops/scripts/deploy_proxy_and_tls.sh staging.dreamseedai.com /var/www/dreamseed/static http://127.0.0.1:8000/ off

# Enable HSTS after stability confirmed
sudo ops/scripts/deploy_proxy_and_tls.sh staging.dreamseedai.com /var/www/dreamseed/static http://127.0.0.1:8000/ on
```

### Production Deployment
```bash
# Deploy with HSTS enabled
sudo ops/scripts/deploy_proxy_and_tls.sh dreamseedai.com /var/www/dreamseed/static http://127.0.0.1:8000/ on
```

## 🔧 Safe Development Server

### Start HTTP Server (Browser-Safe Ports)
```bash
# Use safe ports only
ops/scripts/start_http_server.sh 8080 ./public
ops/scripts/start_http_server.sh 3000 ./public
ops/scripts/start_http_server.sh 5173 ./public

# Access via: http://<server-ip>:8080
```

### UFW Firewall Setup
```bash
# Configure firewall for port
sudo ops/scripts/ufw_setup.sh 8080
```

## 🧪 Browser Testing

### Playwright Smoke Tests
```bash
cd webtests
npm ci
npm run install:browsers

# Test against staging
TARGET_URL=https://staging.dreamseedai.com ENV=staging npm test

# Test against local
TARGET_URL=http://192.168.68.116:8080 ENV=staging npm test

# Headed mode for debugging
npm run test:headed
```

### Manual Browser Testing Checklist
- [ ] Chrome (desktop + mobile)
- [ ] Firefox (desktop + mobile)  
- [ ] Safari/WebKit
- [ ] Incognito/Private mode
- [ ] No console errors
- [ ] All resources load (200 status)
- [ ] HTTP → HTTPS redirect (301/308)
- [ ] HSTS headers correct for environment

## 🔒 Security Configuration

### FastAPI CORS + Cookies
```python
# Use explicit origins, never '*' with credentials
ALLOWED_ORIGINS = ["https://dreamseedai.com"]

# Cross-site cookies require SameSite=None; Secure; Domain
resp.set_cookie(
    key="session",
    value="value",
    httponly=True,
    secure=True,
    samesite="none",
    domain=".dreamseedai.com"
)
```

### Nginx Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: SAMEORIGIN
- Referrer-Policy: no-referrer-when-downgrade
- Content-Security-Policy: configured
- Strict-Transport-Security: when HTTPS stable

## 🚫 Browser-Blocked Ports

### Avoid These Ports
- 6000, 6665-6669, 10080 (Chrome/Edge block)
- Use safe ports: 80, 443, 8000, 8080, 3000, 5173

### Port Validation
```bash
# Check if port is blocked
ops/scripts/ports_policy.sh ops/nginx
```

## 📊 Monitoring & Logs

### Log Collection
```bash
# Gather all logs for debugging
ops/scripts/gather_logs.sh

# Check nginx status
sudo systemctl status nginx
sudo nginx -t

# Check certificate status
sudo certbot certificates
```

### Health Checks
```bash
# API health
curl https://dreamseedai.com/api/health

# Healthz endpoint
curl https://dreamseedai.com/healthz

# Certificate check
curl -I https://dreamseedai.com
```

### Certificate Expiry Monitoring
```bash
# Check certificate expiry
ops/scripts/check_cert_expiry.sh dreamseedai.com

# Set up cron job for monitoring
echo "0 9 * * * /path/to/ops/scripts/check_cert_expiry.sh dreamseedai.com" | crontab -
```

## 🔄 HSTS Strategy

### Phase 1: HTTPS Redirect
1. Enable HTTP → HTTPS redirect
2. Monitor for 7 days
3. Verify TLS auto-renewal works

### Phase 2: HSTS (Short)
1. Enable HSTS with short max-age (1 hour)
2. Monitor for 24 hours
3. Check for any issues

### Phase 3: HSTS (Long)
1. Increase max-age to 1 year
2. Consider includeSubDomains
3. Monitor for 7 days

### Phase 4: HSTS Preload (Optional)
1. Only after 30+ days of stability
2. Submit to HSTS preload list
3. Very difficult to rollback

## 🚨 Troubleshooting

### "Site can't be reached" in Browser
1. Check port is not blocked (6000, 6665-6669)
2. Verify UFW allows port
3. Check nginx config: `sudo nginx -t`
4. Test with curl first
5. Check browser console for errors

### CORS Issues
1. Verify allow_origins is explicit (not '*')
2. Check credentials setting
3. Verify preflight OPTIONS handling
4. Check nginx CORS headers

### Certificate Issues
1. Check certbot status: `sudo certbot certificates`
2. Test renewal: `sudo certbot renew --dry-run`
3. Check nginx SSL config
4. Verify domain DNS

## 📋 Pre-Deployment Checklist

- [ ] Nginx config validated (`nginx -t`)
- [ ] Ports avoid blocked list
- [ ] HTTPS certificate valid
- [ ] CORS configured correctly
- [ ] Playwright tests pass
- [ ] Manual browser testing completed
- [ ] UFW firewall configured
- [ ] Log collection working
- [ ] Health checks responding
- [ ] Rollback plan documented

## 🔗 Related Files

- `ops/nginx/dreamseed.conf.tpl` - Nginx template
- `ops/scripts/deploy_proxy_and_tls.sh` - Deployment script
- `ops/scripts/ports_policy.sh` - Port policy checker
- `webtests/` - Browser compatibility tests
- `backend/fastapi_snippets/cors_and_cookie.py` - API configuration
- `.github/workflows/playwright_smoke.yml` - CI tests
