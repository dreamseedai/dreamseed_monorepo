GitHub Projects Automation (Labels/Assignees/Story Points)

Overview
- This doc outlines automations to move issues/cards in GitHub Projects based on labels/assignees/story points.

Options
1) Built-in Projects (Beta) workflows
   - Use project fields (Status, Iteration, Assignees) and built-in rules if available.

2) GitHub Actions automation (recommended for flexibility)
   - On labeled/assigned/edited events, call Projects GraphQL API to update fields/columns.

Action Workflow Example
- .github/workflows/project-automation.yml

Triggers
- issue labeled/unlabeled
- issue assigned/unassigned
- issue edited (to catch story points changes)

Logic
- Map labels to Status:
  - triage -> Inbox
  - implementation -> In Progress
  - blocked -> Blocked
  - done/closed -> Done
- Map assignees count to Swimlane/Owner field if configured
- Parse Story Points from issue body/title or a custom label (sp:3, sp:5, ...)

GraphQL Notes
- Use the ProjectsV2 API (projectsNext) to set fields by nodeId
- Required secrets: GH_TOKEN with project write scope

References
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project
- https://docs.github.com/en/graphql/guides/using-the-graphql-explorer
