#Requires -Version 7
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# === 경로 정의 ===
$now = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $env:USERPROFILE "DevSyncBackups\$now"
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

$VSCodeSettings = Join-Path $env:APPDATA "Code\User\settings.json"
$CursorSettings = Join-Path $env:APPDATA "Cursor\User\settings.json"
$WindsurfSettings = Join-Path $env:APPDATA "Windsurf\User\settings.json"
$SSHConfig = Join-Path $env:USERPROFILE ".ssh\config"

# === 도우미 ===
function Backup-IfExists([string]$Path) {
  if (Test-Path $Path) {
    Copy-Item $Path (Join-Path $BackupRoot ([IO.Path]::GetFileName($Path))) -Force
  }
}

function Get-OrCreateJson([string]$Path) {
  if (-not (Test-Path $Path)) {
    New-Item -ItemType File -Force -Path $Path | Out-Null
    Set-Content -Path $Path -Value "{}" -Encoding UTF8
  }
  $raw = Get-Content $Path -Raw
  if ([string]::IsNullOrWhiteSpace($raw)) { $raw = "{}" }
  try { return $raw | ConvertFrom-Json -AsHashtable } catch { return @{} }
}

function Save-Json([hashtable]$Obj, [string]$Path) {
  ($Obj | ConvertTo-Json -Depth 10) | Set-Content -Path $Path -Encoding UTF8
}

Write-Host "=== DevSyncGuard: 시작 ==="

# 1) 백업
Backup-IfExists $VSCodeSettings
Backup-IfExists $CursorSettings
Backup-IfExists $WindsurfSettings
Backup-IfExists $SSHConfig
Write-Host "백업 완료 → $BackupRoot"

# 2) VS Code / Cursor: 자동 저장·Remote 사용 권장 설정 강화
foreach ($cfgPath in @($VSCodeSettings, $CursorSettings)) {
  $cfg = Get-OrCreateJson $cfgPath
  $cfg["files.autoSave"] = "afterDelay"
  $cfg["files.autoSaveDelay"] = 500
  # watcher 제외 패턴 최소화 권장
  if (-not $cfg.ContainsKey("files.watcherExclude")) { $cfg["files.watcherExclude"] = @{} }
  # 필요시 특정 대형 폴더만 제외; 전역 제외는 비권장
  Save-Json $cfg $cfgPath
  Write-Host "설정 적용: $cfgPath"
}

# 3) Windsurf: Live Sync 강제
$wcfg = Get-OrCreateJson $WindsurfSettings
$wcfg["remote.syncMode"] = "live"               # 즉시 동기화
$wcfg["remote.autoUploadOnSave"] = $true        # 저장 시 업로드
$wcfg["remote.autoDownloadChanges"] = $true     # 원격 변경 자동 pull
$wcfg["remote.conflictResolution"] = "remote"   # 충돌 시 remote 우선
# (선택) Pull 간격 단축 (ms)
$wcfg["remote.syncInterval"] = 1000
Save-Json $wcfg $WindsurfSettings
Write-Host "Windsurf Live Sync 적용: $WindsurfSettings"

# 4) SSH config에 공용 호스트 별칭 체크(선택)
$desiredHost = "dev-server"        # ★ 사용 중인 별칭으로 바꾸세요
if (Test-Path $SSHConfig) {
  $content = Get-Content $SSHConfig -Raw
  if ($content -notmatch "(?m)^Host\s+$([regex]::Escape($desiredHost))\s*$") {
    Write-Warning "SSH config에 Host '$desiredHost' 항목이 없습니다. 수동으로 추가를 권장합니다: $SSHConfig"
  } else {
    Write-Host "SSH config에 Host '$desiredHost' 확인됨"
  }
} else {
  Write-Warning "SSH config가 없습니다: $SSHConfig"
}

Write-Host "=== DevSyncGuard: 완료 ==="
