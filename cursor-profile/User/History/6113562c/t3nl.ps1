# SSH 연결 지연 측정 스크립트
# PowerShell에서 실행: .\measure-ssh-latency.ps1

param(
    [string]$HostName = "dreamseed",
    [int]$Iterations = 5
)

Write-Host "=== SSH 연결 지연 측정 ===" -ForegroundColor Cyan
Write-Host "호스트: $HostName`n반복 횟수: $Iterations`n" -ForegroundColor Gray

$results = @()
$controlSocketDir = "$env:USERPROFILE\.ssh"

# 기존 ControlMaster 소켓 정리 (선택사항)
Write-Host "[1] 기존 ControlMaster 소켓 확인..." -ForegroundColor Yellow
if (Test-Path $controlSocketDir) {
    $sockets = Get-ChildItem -Path $controlSocketDir -Filter "cm-*" -ErrorAction SilentlyContinue
    if ($sockets) {
        Write-Host "  기존 소켓 발견: $($sockets.Count)개" -ForegroundColor Gray
        $clean = Read-Host "  정리하시겠습니까? (y/N)"
        if ($clean -eq 'y') {
            Remove-Item -Path $sockets.FullName -Force
            Write-Host "  ✓ 소켓 정리 완료" -ForegroundColor Green
        }
    } else {
        Write-Host "  기존 소켓 없음" -ForegroundColor Gray
    }
}
Write-Host ""

# 첫 연결 (ControlMaster 없이)
Write-Host "[2] 첫 연결 측정 (ControlMaster 없음)..." -ForegroundColor Yellow
$firstStart = Get-Date
ssh -o ControlMaster=no -T $HostName "echo 'first-connection'" 2>&1 | Out-Null
$firstEnd = Get-Date
$firstTime = ($firstEnd - $firstStart).TotalSeconds
Write-Host "  첫 연결: $([math]::Round($firstTime, 3))초" -ForegroundColor $(if ($firstTime -lt 0.5) { "Green" } elseif ($firstTime -lt 1.0) { "Yellow" } else { "Red" })
Write-Host ""

# ControlMaster를 사용한 반복 측정
Write-Host "[3] ControlMaster 재사용 연결 측정..." -ForegroundColor Yellow
for ($i = 1; $i -le $Iterations; $i++) {
    $start = Get-Date
    ssh -T $HostName "echo 'test-$i'" 2>&1 | Out-Null
    $end = Get-Date
    $elapsed = ($end - $start).TotalSeconds
    $results += $elapsed
    
    $color = if ($elapsed -lt 0.2) { "Green" } elseif ($elapsed -lt 0.5) { "Yellow" } else { "Red" }
    Write-Host "  시도 $i`: $([math]::Round($elapsed, 3))초" -ForegroundColor $color
}

Write-Host ""

# 통계
Write-Host "[4] 통계 요약" -ForegroundColor Yellow
$avg = ($results | Measure-Object -Average).Average
$min = ($results | Measure-Object -Minimum).Minimum
$max = ($results | Measure-Object -Maximum).Maximum
$median = ($results | Sort-Object)[[math]::Floor($results.Count / 2)]

Write-Host "  평균: $([math]::Round($avg, 3))초" -ForegroundColor $(if ($avg -lt 0.3) { "Green" } else { "Yellow" })
Write-Host "  최소: $([math]::Round($min, 3))초"
Write-Host "  최대: $([math]::Round($max, 3))초"
Write-Host "  중앙값: $([math]::Round($median, 3))초"
Write-Host ""

# 목표 달성 여부
Write-Host "[5] 목표 달성 여부" -ForegroundColor Yellow
if ($firstTime -lt 0.3 -and $avg -lt 0.2) {
    Write-Host "  ✓ 목표 달성! (첫 연결 < 0.3s, 재사용 < 0.2s)" -ForegroundColor Green
} elseif ($firstTime -lt 0.5 -and $avg -lt 0.3) {
    Write-Host "  △ 개선됨 (첫 연결 < 0.5s, 재사용 < 0.3s)" -ForegroundColor Yellow
} else {
    Write-Host "  ✗ 추가 최적화 필요" -ForegroundColor Red
    Write-Host "    - 서버 측 설정 확인 (UseDNS, PrintMotd 등)" -ForegroundColor Gray
    Write-Host "    - MOTD 스크립트 성능 확인" -ForegroundColor Gray
}

Write-Host "`n=== 측정 완료 ===" -ForegroundColor Cyan

