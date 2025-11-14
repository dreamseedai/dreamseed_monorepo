# Final Validation Report

## Overview
- Org/Repo/Project Number: <org>/<repo>/<number>
- Date/Time (UTC): <yyyy-mm-dd HH:MM>
- Performed by: <name>

## Secrets / Config
- Secrets presence and scopes
  - GH_TOKEN: <present/missing> (scopes: project read/write, repo read/write)
  - PROJECT_NUMBER: <value>
  - PROJECT_ORG / PROJECT_REPO: <values or defaults>
- Project fields configured
  - Status (options): <Inbox, In Progress, Blocked, Done>
  - Story Points (number): <present>
  - Priority (options): <P1, P2, High, Medium or actual names>
  - Iteration (titles available): <e.g., 2025w01, 2025w02>
- Project config JSON
  - Path: <project_management/project_config.json>
  - Key mappings: statusLabelMap, storyPointsLabelPrefix, priorityLabelMap, iterationFromLabelPrefix

## Execution Results
- Bulk issues
  - Created issues: n
  - Added to project: m
  - Field updates
    - Status updated: x / total
    - Story Points updated: y / total
    - Priority updated: z / total
    - Iteration updated: w / total
- Branch protection
  - main required checks: <list>
  - release/* required checks applied to: <branches>
  - feature/* required checks applied to: <branches>

## Captures (attach screenshots or links)
- Project board item view (shows Status/Points/Priority/Iteration)
- Actions → Project Automation logs (field update messages)
- Issues list/detail (new [PR-xx] issues)
- Branch protection settings (Required checks visible)

## Conclusion / Follow-ups
- Observations: <e.g., option name mismatches, missing iteration titles>
- Fixes applied or planned: <list>
- Next expected behavior in routine runs: <summary>
