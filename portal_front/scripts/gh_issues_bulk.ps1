Param(
  [Parameter(Mandatory=$true)][string]$Owner,
  [Parameter(Mandatory=$true)][string]$Repo,
  [Parameter(Mandatory=$true)][string]$CsvPath,
  [string]$Org,
  [int]$ProjectNumber,
  [switch]$CreateBranch,
  [switch]$CreatePR,
  [switch]$DraftPR,
  [switch]$DryRunProjects,
  [string]$Reviewers,
  [string]$Base = "main"
)

# Requires: gh CLI
if (-not (Test-Path $CsvPath)) { throw "CSV not found: $CsvPath" }

# Read CSV; expects headers: id,title,assignees,labels,story_points,branch
$csv = Import-Csv -Path $CsvPath

# Config: Status mapping and Story Points parsing
$configPath = $env:PROJECT_CONFIG_JSON
$statusMap = @{}
$spPrefix = if ($env:STORY_POINTS_LABEL_PREFIX) { $env:STORY_POINTS_LABEL_PREFIX } else { 'sp:' }
if ($configPath -and (Test-Path $configPath)) {
  try {
    $raw = Get-Content -Raw -Path $configPath
    $cfg = $raw | ConvertFrom-Json
    # Minimal schema validation
    $ok = $true
    if (-not $cfg.PSObject.Properties.Match('statusLabelMap')) { $ok = $false }
    elseif (-not ($cfg.statusLabelMap -is [System.Collections.IDictionary])) { $ok = $false }
    if ($cfg.PSObject.Properties.Match('storyPointsLabelPrefix') -and -not ($cfg.storyPointsLabelPrefix -is [string])) { $ok = $false }
    if ($ok) {
      if ($cfg.statusLabelMap) { $statusMap = $cfg.statusLabelMap }
      if ($cfg.storyPointsLabelPrefix) { $spPrefix = $cfg.storyPointsLabelPrefix }
    } else {
      Write-Warning "PROJECT_CONFIG_JSON failed schema validation; ignoring"
    }
  } catch { Write-Warning $_ }
} elseif ($env:PROJECT_STATUS_MAP_JSON) {
  try { $statusMap = $env:PROJECT_STATUS_MAP_JSON | ConvertFrom-Json } catch {}
}
if ($statusMap.Count -eq 0) {
  $statusMap = @{ implementation = 'In Progress'; blocked = 'Blocked'; done = 'Done' }
}

function Resolve-StatusFromLabels([string]$labelsCsv) {
  $labels = ($labelsCsv -split ',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
  foreach ($kv in $statusMap.GetEnumerator()) {
    if ($labels -contains $kv.Key) { return $kv.Value }
  }
  return 'Inbox'
}

function Resolve-StoryPoints([string]$labelsCsv, [string]$fallback) {
  if ($fallback -and $fallback.Trim() -ne '') { return $fallback }
  $labels = ($labelsCsv -split ',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
  foreach ($l in $labels) {
    if ($l.StartsWith($spPrefix)) {
      $num = $l.Substring($spPrefix.Length)
      if ([int]::TryParse($num, [ref]([int]$null))) { return $num }
    }
  }
  return ''
}

function Invoke-GraphQL([string]$Query, [hashtable]$Vars) {
  $args = @('api','graphql','-f',"query=$Query")
  foreach ($k in $Vars.Keys) { $args += @('-F',"$k=$($Vars[$k])") }
  $json = & gh @args 2>$null
  if (-not $json) { throw 'GraphQL call failed' }
  return $json | ConvertFrom-Json
}

function Update-ProjectFields([string]$Owner,[string]$Repo,[int]$IssueNumber,[string]$Org,[int]$ProjectNumber,[string]$Status,[string]$StoryPoints) {
  if (-not $Org -or -not $ProjectNumber) { return }
  # Get node ids
  $q1 = 'query($org:String!,$repo:String!,$number:Int!){repository(owner:$org,name:$repo){issue(number:$number){id}}}'
  $r1 = Invoke-GraphQL $q1 @{ org=$Owner; repo=$Repo; number=$IssueNumber }
  $issueId = $r1.data.repository.issue.id
  if (-not $issueId) { throw 'Cannot resolve issue node id' }

  $q2 = 'query($org:String!,$number:Int!){organization(login:$org){projectV2(number:$number){id title fields(first:50){nodes{... on ProjectV2FieldCommon{id name} ... on ProjectV2SingleSelectField{id name options{id name}}}}}}}'
  $r2 = Invoke-GraphQL $q2 @{ org=$Org; number=$ProjectNumber }
  $project = $r2.data.organization.projectV2
  $projectId = $project.id
  $fields = $project.fields.nodes

  $q3 = 'mutation($project:ID!,$content:ID!){addProjectV2ItemById(input:{projectId:$project, contentId:$content}){item{id}}}'
  $r3 = Invoke-GraphQL $q3 @{ project=$projectId; content=$issueId }
  $itemId = $r3.data.addProjectV2ItemById.item.id

  $statusField = $fields | Where-Object { $_.name -eq 'Status' } | Select-Object -First 1
  if ($statusField -and $statusField.options) {
    $opt = $statusField.options | Where-Object { $_.name -eq $Status } | Select-Object -First 1
    if ($opt) {
      $m = 'mutation($project:ID!,$item:ID!,$field:ID!,$opt:String!){updateProjectV2ItemFieldValue(input:{projectId:$project,itemId:$item,fieldId:$field,value:{singleSelectOptionId:$opt}}){clientMutationId}}'
      Invoke-GraphQL $m @{ project=$projectId; item=$itemId; field=$statusField.id; opt=$opt.id } | Out-Null
    }
  }
  $spField = $fields | Where-Object { $_.name -eq 'Story Points' } | Select-Object -First 1
  if ($spField -and $StoryPoints) {
    $m2 = 'mutation($project:ID!,$item:ID!,$field:ID!,$sp:Float!){updateProjectV2ItemFieldValue(input:{projectId:$project,itemId:$item,fieldId:$field,value:{number:$sp}}){clientMutationId}}'
    Invoke-GraphQL $m2 @{ project=$projectId; item=$itemId; field=$spField.id; sp=$StoryPoints } | Out-Null
  }
}

function Get-DefaultReviewersFromCodeowners() {
  try {
    $root = (& git rev-parse --show-toplevel) 2>$null
    if (-not $root) { return '' }
    $c1 = Join-Path $root '.github/CODEOWNERS'
    $c2 = Join-Path $root 'CODEOWNERS'
    $path = if (Test-Path $c1) { $c1 } elseif (Test-Path $c2) { $c2 } else { $null }
    if (-not $path) { return '' }
    $lines = Get-Content -Path $path
    $wild = ($lines | Where-Object { $_ -match '^\s*\*' }) | Select-Object -Last 1
    if (-not $wild) { return '' }
    $owners = [regex]::Matches($wild, '@[A-Za-z0-9_.-]+') | ForEach-Object { $_.Value.TrimStart('@') }
    if ($owners.Count -gt 0) { return ($owners -join ',') } else { return '' }
  } catch { return '' }
}
foreach ($row in $csv) {
  $id = $row.id
  $title = $row.title
  $assignees = $row.assignees
  $labels = $row.labels
  $story = $row.story_points
  $branch = $row.branch
  $body = $row.PSObject.Properties.Match('body') ? $row.body : $null

  if (-not $body) {
    $body = @"
Auto-generated issue for roadmap item $id

Branch: $branch
Story Points: $story

Refer to .github/ISSUE_TEMPLATE/implementation_checklist.md for checklist.
"@
  }

  $labelArgs = @()
  foreach ($l in $labels.Split(",")) { if ($l.Trim()) { $labelArgs += @('--label', $l.Trim()) } }

  $assigneeArgs = @()
  foreach ($a in $assignees.Split(";")) { if ($a.Trim()) { $assigneeArgs += @('--assignee', $a.Trim()) } }

  Write-Host "Creating issue: [$id] $title"
  gh issue create `
    --repo "$Owner/$Repo" `
    --title "[$id] $title" `
    --body $body `
    @labelArgs `
    @assigneeArgs

  # Resolve created issue number
  $search = gh issue list --repo "$Owner/$Repo" --search "[$id] $title in:title" --state open --json number,title | ConvertFrom-Json
  $issueNumber = if ($search) { $search[0].number } else { $null }

  # Projects V2 update (optional)
  if ($Org -and $ProjectNumber -and $issueNumber) {
    $status = Resolve-StatusFromLabels $labels
    $sp = Resolve-StoryPoints $labels $story
    Write-Host "Project intent: org=$Org number=$ProjectNumber issue=#$issueNumber status=$status sp=$sp"
    if ($DryRunProjects) {
      Write-Host "DRY-RUN-PROJECTS: would update project fields and comment with https://github.com/orgs/$Org/projects/$ProjectNumber"
    } else {
      try { Update-ProjectFields -Owner $Owner -Repo $Repo -IssueNumber $issueNumber -Org $Org -ProjectNumber $ProjectNumber -Status $status -StoryPoints $sp } catch { Write-Warning $_ }
      try {
        $projUrl = "https://github.com/orgs/$Org/projects/$ProjectNumber"
        gh issue comment --repo "$Owner/$Repo" $issueNumber --body "Added to Project: $projUrl" | Out-Null
      } catch { Write-Warning $_ }
    }
  }

  # Branch and PR (optional)
  if ($CreateBranch -and $branch) {
    git fetch origin | Out-Null
    git checkout -B $branch $Base | Out-Null
    git push -u origin $branch | Out-Null
    if ($CreatePR) {
      # CODEOWNERS fallback if no reviewers provided
      $rv = $Reviewers
      if (-not $rv) { $rv = Get-DefaultReviewersFromCodeowners }
      # Build PR body from template
      $root = (& git rev-parse --show-toplevel) 2>$null
      $tplPath = if ($root) { Join-Path $root '.github/PULL_REQUEST_TEMPLATE.md' } else { $null }
      $tpl = if ($tplPath -and (Test-Path $tplPath)) { Get-Content -Raw -Path $tplPath } else { '' }
      $projUrl = if ($Org -and $ProjectNumber) { "https://github.com/orgs/$Org/projects/$ProjectNumber" } else { $null }
      $prBody = "$tpl`n`nCloses #$issueNumber"
      if ($projUrl) { $prBody = "$prBody`n`nLinked Project: $projUrl" }
      $prArgs = @('--repo',"$Owner/$Repo",'--head',$branch,'--base',$Base,'--title',"[$id] $title",'--body',$prBody)
      if ($DraftPR) { $prArgs += @('--draft') }
      if ($rv) { $prArgs += @('--reviewer', $rv) }
      gh pr create @prArgs | Out-Null
      if (-not $DryRunProjects) {
        try {
          $prInfo = gh pr view --repo "$Owner/$Repo" --head $branch --json number,url | ConvertFrom-Json
          if ($projUrl) { gh pr comment --repo "$Owner/$Repo" $prInfo.number --body "Linked Project: $projUrl" | Out-Null }
        } catch { Write-Warning $_ }
      }
    }
  }
}
Write-Host "Done."