## Summary
- [ ] Change scoped to staging first
- [ ] Nginx config validated (`nginx -t`)
- [ ] Ports avoid browser-blocked list (no 6000, 6665–6669, 10080)
- [ ] HTTPS works (cert ok) and HSTS toggle considered (staging=OFF, prod=ON)
- [ ] CORS + cookies reviewed (SameSite=None; Secure; Domain=… if cross-site)
- [ ] CSP applied; exceptions documented (nonce/hash for 3p scripts)
- [ ] WebSocket/Upload limits/timeouts reviewed
- [ ] Playwright smoke passed (CI) & report attached

## Browser Compatibility Checklist
- [ ] Tested in Chrome (desktop + mobile)
- [ ] Tested in Firefox (desktop + mobile)
- [ ] Tested in Safari/WebKit
- [ ] Tested in incognito/private mode
- [ ] No console errors in browser dev tools
- [ ] All resources load successfully (200 status)
- [ ] HTTP → HTTPS redirect works (301/308)
- [ ] HSTS headers correct for environment (staging=off, prod=on)

## Security Headers
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: SAMEORIGIN
- [ ] Referrer-Policy: no-referrer-when-downgrade
- [ ] Content-Security-Policy configured
- [ ] HSTS considered (if HTTPS stable)

## API & CORS
- [ ] allow_origins is explicit (not '*')
- [ ] allow_credentials=True with explicit origins
- [ ] Cross-site cookies: SameSite=None; Secure; Domain=.<root-domain>
- [ ] Preflight Max-Age: 600 seconds
- [ ] /healthz endpoint available

## Performance & Limits
- [ ] client_max_body_size: 50m
- [ ] proxy_read_timeout: 300s
- [ ] WebSocket headers configured
- [ ] Static assets cached (immutable)

## Risk & Rollback
- Rollback steps:
  1. Revert nginx site to previous commit and reload
  2. Disable new service (`systemctl revert/stop`)
  3. Announce and verify via smoke test

## Testing
- [ ] Local testing completed
- [ ] Staging environment tested
- [ ] Playwright tests pass
- [ ] Manual browser testing completed
- [ ] Port policy check passed

## Deployment Notes
- [ ] Database migrations (if any)
- [ ] Environment variables updated
- [ ] Service restart required
- [ ] Cache invalidation needed
- [ ] Certificate renewal tested
