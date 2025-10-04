@echo off
REM Windows 네트워크 리셋 절차 (현장 지원용)
REM 목적: Windows 클라이언트 연결 문제 해결

echo ========================================
echo Windows 네트워크 리셋 절차 시작
echo ========================================
echo.

REM 1. 프록시/자동 구성 비활성 상태로 Chrome 테스트
echo [1/4] 프록시 비활성화 Chrome 테스트...
echo Chrome을 프록시 없이 시작합니다...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --proxy-server="direct://"
echo Chrome이 프록시 없이 시작되었습니다.
echo.
pause

REM 2. Winsock/IP 스택 리셋
echo [2/4] Winsock/IP 스택 리셋...
echo 주의: 이 작업 후 재부팅이 필요합니다.
echo.
set /p confirm="계속하시겠습니까? (y/N): "
if /i "%confirm%"=="y" (
    echo Winsock 리셋 중...
    netsh winsock reset
    echo.
    echo IP 스택 리셋 중...
    netsh int ip reset
    echo.
    echo 리셋 완료. 재부팅이 필요합니다.
    echo.
    set /p reboot="지금 재부팅하시겠습니까? (y/N): "
    if /i "%reboot%"=="y" (
        shutdown /r /t 10 /c "네트워크 리셋 후 재부팅"
    )
) else (
    echo 리셋을 건너뜁니다.
)
echo.

REM 3. 방화벽 규칙 확인 안내
echo [3/4] 방화벽 규칙 확인...
echo Windows 방화벽 설정을 엽니다...
echo '앱 허용'에서 사용하는 브라우저/터미널이 '개인' 네트워크에 체크되어 있는지 확인하세요.
echo.
control.exe /name Microsoft.WindowsFirewall
echo.
pause

REM 4. 네트워크 진단 명령어
echo [4/4] 네트워크 진단 명령어...
echo.
echo 다음 명령어들을 실행해보세요:
echo.
echo 1. 서버 ping 테스트:
echo    ping 192.168.68.116
echo.
echo 2. HTTP 연결 테스트:
echo    curl -I http://192.168.68.116:8083
echo.
echo 3. DNS 확인:
echo    nslookup staging.dreamseedai.com
echo.
echo 4. 네트워크 어댑터 상태:
echo    ipconfig /all
echo.
echo 5. 라우팅 테이블:
echo    route print
echo.

echo ========================================
echo Windows 리셋 절차 완료
echo ========================================
echo.
echo 추가 도움이 필요하면 다음을 확인하세요:
echo - Windows 이벤트 뷰어 (eventvwr.msc)
echo - 네트워크 어댑터 드라이버 업데이트
echo - 바이러스 백신 소프트웨어 설정
echo.
pause
