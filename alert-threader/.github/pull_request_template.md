## Summary
- [ ] Change scoped to staging first
- [ ] Nginx config validated (`nginx -t`)
- [ ] Ports avoid browser‑blocked list (no 6000, 6665–6669, 10080)
- [ ] HTTPS works (cert ok) and HSTS toggle considered (staging=OFF, prod=ON)
- [ ] CORS + cookies reviewed (SameSite=None; Secure; Domain=… if cross‑site)
- [ ] CSP applied; exceptions documented (nonce/hash for 3p scripts)
- [ ] WebSocket/Upload limits/timeouts reviewed
- [ ] Playwright smoke passed (CI) & report attached

## Risk & Rollback
- Rollback steps:
  1. Revert nginx site to previous commit and reload
  2. Disable new service (`systemctl revert/stop`)
  3. Announce and verify via smoke test

## Testing
- [ ] Local testing completed
- [ ] Staging environment tested
- [ ] Playwright tests passed
- [ ] Security headers verified
- [ ] Performance impact assessed

## Deployment Notes
- [ ] Environment variables updated
- [ ] Secrets configured
- [ ] Monitoring alerts configured
- [ ] Documentation updated


