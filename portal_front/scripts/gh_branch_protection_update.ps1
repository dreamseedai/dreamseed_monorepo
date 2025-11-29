Param(
  [Parameter(Mandatory=$true)][string]$Owner,
  [Parameter(Mandatory=$true)][string]$Repo,
  [Parameter(Mandatory=$true)][string]$Branch,
  [Parameter(Mandatory=$true)][string]$RequiredChecksCsv
)

# Requires gh CLI admin access
$checks = $RequiredChecksCsv.Split(",") | ForEach-Object { @{ context = $_.Trim() } }
$body = @{ 
  required_status_checks = @{ strict = $true; checks = $checks }
  enforce_admins = $true
  required_pull_request_reviews = @{ required_approving_review_count = 1 }
  restrictions = $null
} | ConvertTo-Json -Depth 5

Write-Host "Applying protection on ${Owner}/${Repo}:${Branch}"
$uri = "/repos/${Owner}/${Repo}/branches/${Branch}/protection"
$body | gh api -X PUT -H "Accept: application/vnd.github+json" $uri --input -
Write-Host "Protection applied successfully"
