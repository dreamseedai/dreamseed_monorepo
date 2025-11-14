# Project management automation

This folder contains samples and guides for bulk issue creation and GitHub Projects V2 updates.

## Prerequisites

- gh CLI authenticated with a token that can read/write Issues and Projects (used locally by scripts)
- Repository secrets configured for the workflow (see below)

## A. GitHub Secrets (Number mode recommended)

In your repository: Settings → Secrets and variables → Actions → New repository secret

Required (pick one mode):

- Number mode (recommended)
  - PROJECT_NUMBER = 42
  - PROJECT_ORG = your-org (optional; defaults to repository owner)
  - GH_TOKEN = token with Projects read/write + Repo read/write
    - GitHub App Installation Token or PAT(classic) with repo and project scopes
- URL mode (alternative)
  - PROJECT_URL = https://github.com/orgs/your-org/projects/42
  - PROJECT_TOKEN = token with Projects read/write

Optional:
- DEFAULT_REVIEWERS = user1,user2

Projects V2 fields (org project 42):
- Status: Single select (Inbox, In Progress, Blocked, Done)
- Story Points: Number
- Priority: Single select (P1, P2, High, Medium, …)
- Iteration: Iteration (e.g., 2025w01, 2025w02 created ahead of time)

## Project config JSON (optional)

- Sample: `project_config.sample.json` includes:
  - statusLabelMap, storyPointsLabelPrefix, priorityLabelMap, iterationFromLabelPrefix
- Copy and customize:

```bash
cp project_config.sample.json project_config.json
export PROJECT_CONFIG_JSON=$(pwd)/project_config.json
```

## B. One-time run (sample)

1) Dry-run

```bash
./scripts/gh_issues_bulk.sh your-org your-repo portal_front/project_management/github_issues.csv your-org 42 --dry-run --dry-run-projects
```

2) Real run for 1–2 issues only

```bash
head -n 3 portal_front/project_management/github_issues.csv > /tmp/github_issues_small.csv
./scripts/gh_issues_bulk.sh your-org your-repo /tmp/github_issues_small.csv your-org 42
```

3) Workflow automation check
- Add labels triage/implementation/blocked/p1/iter:2025w01 to a test issue
- Check Actions → Project Automation logs
- Verify Project 42 item shows Status, Story Points, Priority, Iteration

4) Branch protection (environment mapping)

```bash
./portal_front/scripts/gh_apply_branch_protection_env.sh your-org your-repo \
  --prod-checks "ci/build,ci/test,ci/deploy" \
  --staging-checks "ci/build,ci/test" \
  --base-checks "ci/lint"
```

- default branch → prod checks
- release/* → staging checks
- feature/* → base checks

5) Capture/summary checklist
- Project 42: item created with fields populated
- Actions logs include: Status updated, Story Points updated, Priority updated, Iteration updated
- Issues list shows the new [PR-XX] issues
- Branch protection: required checks set on main/release/*/feature/*

## C. Common issues

- Ensure Project 42 is an Organization-level project
- Option names must match exactly the project field options
- Iteration title must exist in the project before setting
- GH_TOKEN/PROJECT_TOKEN must include project scopes

## Files
- `github_issues.csv` (example list)
- `github_issues.csv.sample` (header + one sample row)
- `project_config.sample.json` (mapping defaults)
