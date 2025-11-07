[CmdletBinding(SupportsShouldProcess=$true)]
param(
  [string]$TaskName = 'DevSyncGuard',
  [string]$InstallPath = 'C:\\DevSync',
  [string]$ScriptFileName = 'DevSyncGuard.ps1',
  [switch]$Uninstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-ScheduledTaskOrNull([string]$Name) {
  try { return Get-ScheduledTask -TaskName $Name -ErrorAction Stop } catch { return $null }
}

function Install-Task {
  $targetScript = Join-Path $InstallPath $ScriptFileName
  $sourceScript = Join-Path $PSScriptRoot 'DevSyncGuard.ps1'

  if (!(Test-Path $InstallPath)) { New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null }
  Copy-Item -Force -Path $sourceScript -Destination $targetScript

  $action = New-ScheduledTaskAction -Execute 'pwsh.exe' -Argument "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"`"$targetScript`"`""
  $trigger = New-ScheduledTaskTrigger -AtLogOn
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel LeastPrivilege

  $existing = Get-ScheduledTaskOrNull -Name $TaskName
  if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Description 'VSCode/Cursor/Continue/Windsurf sync guard' -Force | Out-Null
  } else {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Description 'VSCode/Cursor/Continue/Windsurf sync guard' -Force | Out-Null
  }
  Write-Host "Installed Scheduled Task '$TaskName' launching: $targetScript" -ForegroundColor Green
}

function Uninstall-Task {
  $existing = Get-ScheduledTaskOrNull -Name $TaskName
  if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
    Write-Host "Removed Scheduled Task '$TaskName'" -ForegroundColor Yellow
  } else {
    Write-Host "Task '$TaskName' not found" -ForegroundColor Yellow
  }
}

if ($Uninstall) { Uninstall-Task; return }
Install-Task
