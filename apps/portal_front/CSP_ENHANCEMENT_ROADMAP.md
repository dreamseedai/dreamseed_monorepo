# CSP (Content Security Policy) Enhancement Roadmap

## Current Status
- CSP includes `'unsafe-inline'` and `'unsafe-eval'` for compatibility
- Basic CSP: `default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'`

## Phase 1: Nonce Implementation (Priority: High)
- [ ] Generate nonce on server-side for each request
- [ ] Inject nonce into HTML templates
- [ ] Update CSP to use nonce: `script-src 'self' 'nonce-{NONCE}'`
- [ ] Remove `'unsafe-inline'` from script-src

## Phase 2: Hash Implementation (Priority: Medium)
- [ ] Calculate SHA-256 hashes for inline scripts/styles
- [ ] Update CSP to use hashes: `script-src 'self' 'sha256-{HASH}'`
- [ ] Remove remaining `'unsafe-inline'` directives

## Phase 3: Strict CSP (Priority: Low)
- [ ] Remove `'unsafe-eval'` (requires code review)
- [ ] Implement strict-dynamic for dynamic script loading
- [ ] Add report-uri for CSP violation monitoring

## Implementation Notes
- Test in staging environment first
- Monitor CSP violation reports
- Gradual rollout to avoid breaking functionality
- Consider using CSP reporting service (e.g., report-uri.com)

## Timeline
- Phase 1: Next sprint (2 weeks)
- Phase 2: Following sprint (2 weeks)
- Phase 3: Future enhancement (1 month)

## Files to Update
- `ops/nginx/dreamseed.conf.tpl` (CSP header)
- Frontend build process (nonce injection)
- Template rendering system
- CSP violation monitoring setup
