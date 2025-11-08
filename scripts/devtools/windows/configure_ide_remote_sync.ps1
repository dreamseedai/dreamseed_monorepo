<#
.SYNOPSIS
  Configure VS Code, Cursor, and Windsurf to use the same SSH remote and enable immediate sync.

.DESCRIPTION
  - Updates user settings for:
    * VS Code (Remote-SSH session behavior and save settings)
    * Cursor (same as VS Code)
    * Windsurf (SSH + Live Sync, auto upload/download, conflict: remote wins)
  - Optionally appends SSH host entry to user's ~/.ssh/config
  - Creates timestamped backups of settings before changes

  Note: Continue uses VS Code's remote session and requires no separate config.

.PARAMETER ServerHost
  SSH host (e.g., "won@server.example.com" or an alias present in ~/.ssh/config)

.PARAMETER RemotePath
  Absolute remote path to the project (e.g., "/home/won/projects/dreamseed_monorepo")

.PARAMETER ConfigureSSH
  If set, ensure an SSH Host entry exists in ~/.ssh/config (idempotent append)

.PARAMETER ApplyInotifyOnServer
  If set, will print the Linux commands to raise inotify limits. You can copy/run them on server.

.PARAMETER WhatIf
  Dry run. Shows planned changes without writing files.

.EXAMPLE
  ./configure_ide_remote_sync.ps1 -ServerHost "won@server" -RemotePath "/home/won/projects/dreamseed_monorepo" -ConfigureSSH -WhatIf

.EXAMPLE
  ./configure_ide_remote_sync.ps1 -ServerHost "won@server" -RemotePath "/home/won/projects/dreamseed_monorepo" -ConfigureSSH

#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)] [string] $ServerHost,
  [Parameter(Mandatory = $true)] [string] $RemotePath,
  [switch] $ConfigureSSH,
  [switch] $ApplyInotifyOnServer
)

function New-Backup {
  param([string] $Path)
  if (Test-Path -LiteralPath $Path) {
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $backup = "$Path.$ts.bak"
    Copy-Item -LiteralPath $Path -Destination $backup -Force
    Write-Host "Backup created: $backup" -ForegroundColor Yellow
  }
}

function New-ParentDirectoryIfMissing {
  param([string] $Path)
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
}

function Get-JsonObject {
  param([string] $Path)
  if (-not (Test-Path -LiteralPath $Path)) { return @{} }
  try {
    $raw = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
    if ([string]::IsNullOrWhiteSpace($raw)) { return @{} }
    $obj = $raw | ConvertFrom-Json -ErrorAction Stop
    # Convert PSObject to hashtable recursively
    return $obj | ConvertTo-Json -Depth 20 | ConvertFrom-Json -AsHashtable
  } catch {
    Write-Warning "Failed to parse JSON: $Path ($_). Using empty object."
    return @{}
  }
}

function Set-JsonFile {
  param([string] $Path, [hashtable] $Data)
  New-ParentDirectoryIfMissing -Path $Path
  $json = $Data | ConvertTo-Json -Depth 50
  if ($WhatIfPreference) {
    Write-Host "DRY-RUN: Would update $Path with:" -ForegroundColor Cyan
    Write-Output $json
  } else {
    Set-Content -LiteralPath $Path -Value $json -Encoding UTF8
    Write-Host "Updated: $Path" -ForegroundColor Green
  }
}

function Set-FlatKey {
  param([hashtable] $Root, [string] $Key, $Value)
  # keys may include dots (e.g., "remote.SSH.remotePlatform"); store as literal key
  $Root[$Key] = $Value
}

Write-Host "Configuring IDEs for remote: $ServerHost -> $RemotePath" -ForegroundColor Magenta

# Paths
$vscodeSettings = Join-Path $env:APPDATA 'Code/User/settings.json'
$cursorSettings = Join-Path $env:APPDATA 'Cursor/User/settings.json'
# Windsurf paths vary by version; try a few common locations
$windsurfCandidates = @(
  (Join-Path $env:APPDATA 'Windsurf/settings.json'),
  (Join-Path $env:APPDATA 'Windsurf/User/settings.json')
)

# 1) VS Code settings
Write-Host "--> VS Code" -ForegroundColor Yellow
New-Backup -Path $vscodeSettings
$vs = Get-JsonObject -Path $vscodeSettings
Set-FlatKey -Root $vs -Key 'files.autoSave' -Value 'afterDelay'
Set-FlatKey -Root $vs -Key 'files.autoSaveDelay' -Value 500
Set-FlatKey -Root $vs -Key 'git.autofetch' -Value $false
Set-FlatKey -Root $vs -Key 'git.ignoreLimitWarning' -Value $true
# Hint remote platform for the host (optional but helpful)
$platformMap = @{}
$platformMap[$ServerHost] = 'linux'
Set-FlatKey -Root $vs -Key 'remote.SSH.remotePlatform' -Value $platformMap
Set-JsonFile -Path $vscodeSettings -Data $vs

# 2) Cursor settings (VS Code fork)
Write-Host "--> Cursor" -ForegroundColor Yellow
New-Backup -Path $cursorSettings
$cs = Get-JsonObject -Path $cursorSettings
Set-FlatKey -Root $cs -Key 'files.autoSave' -Value 'afterDelay'
Set-FlatKey -Root $cs -Key 'files.autoSaveDelay' -Value 500
Set-JsonFile -Path $cursorSettings -Data $cs

# 3) Windsurf settings (SSH + Live Sync)
foreach ($wsPath in $windsurfCandidates) {
  Write-Host "--> Windsurf ($wsPath)" -ForegroundColor Yellow
  New-Backup -Path $wsPath
  $ws = Get-JsonObject -Path $wsPath
  # Keys are indicative; adjust if your Windsurf version uses different names
  Set-FlatKey -Root $ws -Key 'remote.mode' -Value 'ssh'
  Set-FlatKey -Root $ws -Key 'remote.host' -Value $ServerHost
  Set-FlatKey -Root $ws -Key 'remote.path' -Value $RemotePath
  Set-FlatKey -Root $ws -Key 'sync.mode' -Value 'live'
  Set-FlatKey -Root $ws -Key 'sync.autoUpload' -Value $true
  Set-FlatKey -Root $ws -Key 'sync.autoDownload' -Value $true
  Set-FlatKey -Root $ws -Key 'sync.conflictResolution' -Value 'remote'
  Set-JsonFile -Path $wsPath -Data $ws
}

# 4) SSH config (optional)
if ($ConfigureSSH) {
  $sshDir = Join-Path $env:USERPROFILE '.ssh'
  $sshConfig = Join-Path $sshDir 'config'
  if (-not (Test-Path -LiteralPath $sshDir)) { New-Item -ItemType Directory -Path $sshDir -Force | Out-Null }
  if (-not (Test-Path -LiteralPath $sshConfig)) { New-Item -ItemType File -Path $sshConfig -Force | Out-Null }

  $configContent = Get-Content -LiteralPath $sshConfig -Raw
  if ($configContent -notmatch "(?m)^Host\s+\Q$ServerHost\E$") {
    # Derive user from 'user@host' if provided; otherwise fall back to current Windows user
    $derivedUser = if ($ServerHost -match '(.+)@(.+)') { $Matches[1] } else { $env:USERNAME }
    $block = @()
    $block += """Host $ServerHost"""
    $block += "  HostName $ServerHost"
    $block += "  User $derivedUser"
    $block += "  ServerAliveInterval 30"
    $block += "  ServerAliveCountMax 3"
    $blockText = ($block -join [Environment]::NewLine) + [Environment]::NewLine
    if ($WhatIfPreference) {
      Write-Host ("DRY-RUN: Would append SSH block to {0}:" -f $sshConfig) -ForegroundColor Cyan
      Write-Output $blockText
    } else {
      Add-Content -LiteralPath $sshConfig -Value $blockText
      Write-Host "Appended SSH host: $ServerHost" -ForegroundColor Green
    }
  } else {
    Write-Host "SSH host already present in config: $ServerHost" -ForegroundColor Green
  }
}

# 5) Server inotify instructions (print only)
if ($ApplyInotifyOnServer) {
  Write-Host "" -ForegroundColor DarkGray
  Write-Host "Run on the Linux server (requires sudo):" -ForegroundColor Yellow
  @'
sudo bash -c 'cat >/etc/sysctl.d/99-inotify.conf <<EOF
fs.inotify.max_user_watches=1048576
fs.inotify.max_user_instances=1024
EOF'
sudo sysctl --system
'@ | Write-Host
}

Write-Host "All done. Verify by opening the same remote folder in VS Code/Cursor, and Windsurf Live Sync." -ForegroundColor Magenta
