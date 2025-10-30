# Sentry Alert Rules

This folder contains an example ruleset to notify on error spikes and sustained error volume.

## Import via API

Sentry alert rules are typically managed via UI, but you can create/update via API.

- API Docs: https://docs.sentry.io/api/events/create-an-organization-rule/
- Example (curl):

```bash
ORG_SLUG=your-org
PROJECT_SLUG=seedtest-api
AUTH_TOKEN=your-sentry-token

curl -sS -H "Authorization: Bearer $AUTH_TOKEN" \
  -H 'Content-Type: application/json' \
  -X POST \
  https://sentry.io/api/0/projects/$ORG_SLUG/$PROJECT_SLUG/rules/ \
  -d @alert_rules.json
```

Adjust thresholds/intervals per your traffic. Consider adding channel actions (Slack, email, PagerDuty).
