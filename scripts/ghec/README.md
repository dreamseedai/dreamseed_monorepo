# GHEC hardening helper scripts

This folder contains small, reversible scripts to finish repo-level GitHub Enterprise features.

Prerequisites
- gh CLI authenticated with a token that has admin on this repo
- For rulesets: a `rulesets.json` at the repository root

Environment variables (optional)
- OWNER (default: dreamseedai)
- REPO (default: dreamseed_monorepo)
- ORG and TEAM_SLUG (for environment reviewers)

Scripts
- ensure_ruleset.sh
  - Creates/updates the repo ruleset from `rulesets.json`.
  - Usage: `OWNER=... REPO=... ./scripts/ghec/ensure_ruleset.sh`
- enable_security_features.sh
  - Enables secret scanning, push protection, dependency graph, and Dependabot alerts on the repo.
  - Usage: `OWNER=... REPO=... ./scripts/ghec/enable_security_features.sh`
- ensure_environments.sh
  - Ensures `staging` and `production` environments exist; optionally adds a required reviewer team.
  - Usage: `OWNER=... REPO=... ./scripts/ghec/ensure_environments.sh`
  - With reviewers: `ORG=... TEAM_SLUG=devops-team ./scripts/ghec/ensure_environments.sh`

Verification
- gh api /repos/$OWNER/$REPO/rulesets --jq '.[] | {id,name,target,enforcement}'
- gh api /repos/$OWNER/$REPO --jq '.security_and_analysis'
- gh api /repos/$OWNER/$REPO/environments --jq '.environments[].name'