Automation How-To

Run these commands from the portal_front directory:

  cd portal_front

1) Generate issue bodies with detailed checklists
- Edit project_management/github_issues.csv as needed
- Option A (local):
  python3 scripts/generate_issue_body_from_template.py project_management/github_issues.csv > project_management/github_issues_with_bodies.csv
- Option B (manual):
  Use SERVICE_SNIPPETS and CHECKLIST_BASE in scripts/generate_issue_body_from_template.py to craft bodies.

2) Bulk create issues (with or without bodies)
- If using bodies CSV:
  ./scripts/gh_issues_bulk.sh <owner> <repo> project_management/github_issues_with_bodies.csv <org> <project_number>
- Or using original CSV (auto minimal body):
  ./scripts/gh_issues_bulk.sh <owner> <repo> project_management/github_issues.csv <org> <project_number>

CSV columns
- Required: id,title,assignees,labels,story_points,branch
- Optional: body,reviewers,priority_label,iteration_title
  - body: markdown; supports \n for newlines
  - reviewers: comma/semicolon-separated GitHub logins for PRs
  - priority_label: directly sets Project “Priority” (overrides label-derived mapping)
  - iteration_title: directly sets Project “Iteration” title (overrides label-derived derivation)

Sample CSV with extended columns
  project_management/github_issues_extended.sample.csv
  # includes reviewers/priority_label/iteration_title examples

3) Projects automation
- Ensure repo secrets GH_TOKEN and PROJECT_NUMBER are set
- Labels: implementation/blocked/triage + sp:n + p1/p2 or priority:*
- Iteration: iter:YYYYwWW labels must match project iteration titles

Project field introspection and config skeleton
- Inspect current Project “Status”, “Priority”, “Iteration” options and generate a config skeleton:
  ./scripts/gh_project_introspect_fields.sh <org> <project_number> --output-config project_management/project_config.generated.json
- Review and merge into project_config.json (or export PROJECT_CONFIG_JSON to point to the generated file)

Finalize config to match board options
- Automatically choose the closest Status/Priority option names and write a finalized config:
  ./scripts/gh_project_finalize_config.sh <org> <project_number> --output portal_front/project_management/project_config.json

Precedence rules
- Priority: CSV priority_label > project_config.json priorityLabelMap via labels > fallback(p1/p2)
- Iteration: CSV iteration_title > label prefix via iterationFromLabelPrefix
- Reviewers: CSV reviewers ∪ --reviewers flag (merged, 중복 제거) > CODEOWNERS fallback

4) Branch protection
- Preview: use gh api to read current protection
- Apply environment-based checks:
  ./scripts/gh_apply_branch_protection_env.sh <owner> <repo> \
    --prod-checks "ci/build,ci/test,ci/deploy" \
    --staging-checks "ci/build,ci/test" \
    --base-checks "ci/lint"

Notes
- The repo execution environment may not allow running python directly; run commands locally or in CI.
- Adjust project_management/project_config.sample.json and export PROJECT_CONFIG_JSON to customize mappings.
