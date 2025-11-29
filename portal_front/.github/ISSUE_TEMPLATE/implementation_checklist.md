---
name: Implementation Checklist
about: Standard checklist for PR/Issue implementation
title: ""
labels: ["triage"]
assignees: []
---

## Summary
- Scope:
- Related Issues/PRs:
- Branch name:
- Story Points: 

## Acceptance Criteria
- [ ] Functional requirements satisfied
- [ ] Error handling and edge cases covered
- [ ] Observability (logs/metrics/traces) added
- [ ] Security (authz/scopes/secrets) reviewed
- [ ] Performance acceptable for expected load
- [ ] Compatibility (backward/forward) verified

## Tests
- [ ] Unit tests
- [ ] Integration tests
- [ ] E2E smoke (local or staging)
- [ ] Load test (if applicable)

## Docs
- [ ] README / ADR updated
- [ ] API docs / OpenAPI updated
- [ ] Runbooks / On-call notes

## Deployment
- [ ] K8s manifests updated (base/overlays)
- [ ] CI workflows updated
- [ ] Feature flags / config toggles documented

## Rollout & Monitoring
- [ ] Staged rollout plan
- [ ] Dashboards / Alerts configured
- [ ] Post-deploy validation steps
