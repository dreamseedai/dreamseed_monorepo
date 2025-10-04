# Windows 클라이언트 네트워크/포트 진단 스크립트
# 사용법: PowerShell에서 .\diagnose_client.ps1 -ServerIP 192.168.68.116 -Port 9000

param(
    [string]$ServerIP = "192.168.68.116",
    [int]$Port = 9000
)

Write-Host "🔎 Windows 클라이언트 진단 시작 (ServerIP=$ServerIP, Port=$Port)"
Write-Host "=================================================="

Write-Host "`n[1] Ping 테스트"
ping -n 4 $ServerIP

Write-Host "`n[2] nslookup 테스트"
nslookup $ServerIP

Write-Host "`n[3] TCP 연결 시도 (Test-NetConnection)"
Test-NetConnection -ComputerName $ServerIP -Port $Port

Write-Host "`n[4] netstat 로 현재 연결 확인"
netstat -an | findstr ":$Port"

Write-Host "`n[5] curl 로 HTTP 응답 확인"
try {
    $response = Invoke-WebRequest -Uri "http://$ServerIP`:$Port/dreamseed_editor.html" -Method Head -TimeoutSec 10
    Write-Host "✅ HTTP 응답 성공: $($response.StatusCode)"
} catch {
    Write-Host "❌ curl 실패: $($_.Exception.Message)"
}

Write-Host "`n[6] 브라우저 캐시/쿠키 확인"
Write-Host "브라우저에서 다음을 시도해보세요:"
Write-Host "- 시크릿/프라이빗 모드로 접속"
Write-Host "- 캐시 삭제 후 재시도"
Write-Host "- 다른 브라우저로 테스트"

Write-Host "`n[7] Windows 방화벽 확인"
Write-Host "Windows 방화벽이 차단하고 있는지 확인하세요:"
Write-Host "- 제어판 → Windows Defender 방화벽"
Write-Host "- 임시로 방화벽 끄고 테스트"

Write-Host "`n[8] 프록시 설정 확인"
Write-Host "프록시 설정이 있는지 확인하세요:"
Write-Host "- 설정 → 네트워크 및 인터넷 → 프록시"
Write-Host "- '프록시 서버 사용'이 꺼져 있는지 확인"

Write-Host "`n[9] HSTS 설정 초기화 (Chrome)"
Write-Host "Chrome에서 HSTS 설정을 초기화하세요:"
Write-Host "- chrome://net-internals/#hsts"
Write-Host "- 'Delete domain security policies'에서 $ServerIP 입력"

Write-Host "`n[10] 네트워크 어댑터 확인"
Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object Name, InterfaceDescription, LinkSpeed

Write-Host "`n=================================================="
Write-Host "✅ 진단 완료!"
Write-Host "접속 URL: http://$ServerIP`:$Port/dreamseed_editor.html"
Write-Host "=================================================="
