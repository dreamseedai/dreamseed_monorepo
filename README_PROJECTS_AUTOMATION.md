# Projects Automation

This repository can automatically add PRs/issues to a Projects v2 board and set their Status when labeled.

## Prerequisites

1) Repository variable (Project URL)
- `PROJECT_URL`: `https://github.com/orgs/<org>/projects/<number>`

2) Repository secret (Fine‑grained PAT or classic PAT)
- `PROJECTS_TOKEN`:
  - Fine‑grained PAT:
    - Organization permissions → Projects: Read & write
    - Repository permissions → Read
  - Classic PAT: `project` + `read:org` (and `repo` if needed)

## How it works

- On PR/issue opened (or labeled), workflow `.github/workflows/projects-add-and-update.yml` runs.
- `actions/add-to-project` adds the item to the board.
- If the item has label `runtime-stability`, a GitHub Script updates the board’s `Status` field to `In Progress`.

## Safe default (no-op)

- If `PROJECT_URL` or `PROJECTS_TOKEN` is not set, the workflow skips and does not fail (fork‑safe).

## Troubleshooting

- 403 → PAT lacks Org Projects write.
- Invalid URL → Double-check `PROJECT_URL` format and project number.
- Status didn’t update → Ensure the board has a `Status` field and an `In Progress` option (names must match exactly).
- Re-run: use `workflow_dispatch` from the Actions tab to test manually.

## Quick setup via CLI (optional)

```bash
# Set repo variable (replace with your org/number)
gh variable set PROJECT_URL --body "https://github.com/orgs/<org>/projects/<number>"

# Set repo secret (replace with your PAT)
gh secret set PROJECTS_TOKEN --body "<YOUR_FINE_GRAINED_PAT>"
```
