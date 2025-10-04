# Windows 클라이언트 네트워크/포트 진단 스크립트
# 사용법: PowerShell에서 .\diagnose_client.ps1 -ServerIP 192.168.68.116 -Port 8080

param(
    [string]$ServerIP = "192.168.68.116",
    [int]$Port = 8080
)

Write-Host "🔎 Windows 클라이언트 진단 시작 (ServerIP=$ServerIP, Port=$Port)"

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
    $response = Invoke-WebRequest -Uri "http://$ServerIP`:$Port" -Method Head -TimeoutSec 10
    Write-Host "✅ HTTP 응답 성공: $($response.StatusCode)"
} catch {
    Write-Host "❌ HTTP 요청 실패: $($_.Exception.Message)"
}

Write-Host "`n[6] telnet 연결 시도 (5초 타임아웃)"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $connect = $tcpClient.BeginConnect($ServerIP, $Port, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne(5000, $false)
    if ($wait) {
        $tcpClient.EndConnect($connect)
        Write-Host "✅ TCP 연결 성공"
        $tcpClient.Close()
    } else {
        Write-Host "❌ TCP 연결 타임아웃"
    }
} catch {
    Write-Host "❌ TCP 연결 실패: $($_.Exception.Message)"
}

Write-Host "`n[7] Windows 방화벽 상태 확인"
Get-NetFirewallProfile | Select-Object Name, Enabled

Write-Host "`n[8] 네트워크 어댑터 확인"
Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object Name, InterfaceDescription, LinkSpeed

Write-Host "`n[9] DNS 설정 확인"
Get-DnsClientServerAddress | Where-Object {$_.AddressFamily -eq 2} | Select-Object InterfaceAlias, ServerAddresses

Write-Host "`n✅ 진단 완료"
Write-Host "💡 해결 방법:"
Write-Host "   - Ping 실패 → 네트워크 연결 확인"
Write-Host "   - TCP 연결 실패 → Windows 방화벽 또는 회사 정책 확인"
Write-Host "   - HTTP 실패 → 브라우저 캐시/프록시 설정 확인"
Write-Host "   - 시크릿 모드로 브라우저 테스트 권장"
