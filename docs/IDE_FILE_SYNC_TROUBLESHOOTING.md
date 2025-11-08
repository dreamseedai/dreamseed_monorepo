# IDE 파일 동기화 문제 해결 가이드 (Linux)

VS Code와 Cursor IDE가 같은 프로젝트 폴더를 열었을 때 파일 변경이 실시간으로 동기화되지 않는 문제 해결 가이드.

## 🔍 현재 시스템 상태

✅ **inotify 리밋**: 524288 (충분함)
✅ **폴더 권한**: `/home/won/projects/dreamseed_monorepo` (won:won)
✅ **파일 시스템**: 로컬 디스크 (네트워크 드라이브 아님)

## 🧩 문제 진단

### 1. 빠른 확인 절차

```bash
# inotify 리밋 확인
cat /proc/sys/fs/inotify/max_user_watches

# 폴더 권한 확인
ls -ld /home/won/projects/dreamseed_monorepo

# 프로세스 확인
ps aux | grep -E "(code|cursor)" | grep -v grep
```

### 2. 테스트 파일 생성

```bash
# VS Code에서 test.txt 생성 후
# Cursor에서 즉시 보이는지 확인
ls -l --time-style=full-iso /home/won/projects/dreamseed_monorepo/test.txt
```

## ⚙️ 해결 방법

### 방법 1: IDE 재시작 (가장 빠름)

1. **VS Code**: `Ctrl + Shift + P` → `Developer: Reload Window`
2. **Cursor**: `Ctrl + Shift + P` → `Developer: Reload Window`

### 방법 2: Watcher 설정 확인

**VS Code / Cursor 설정 확인:**

1. `Ctrl + ,` (설정 열기)
2. 검색: `files.watcherExclude`
3. 현재 프로젝트 경로가 제외 목록에 있는지 확인
4. 있으면 제거

**workspace 설정 확인:**

`dreamseed.code-workspace` 파일에서 `files.watcherExclude` 섹션 확인. 
현재는 설정되어 있지 않으므로 문제 없음.

### 방법 3: inotify 리밋 상향 (필요 시)

현재 리밋(524288)이 충분하지만, 더 큰 프로젝트의 경우:

```bash
# 임시 적용 (재부팅 후 초기화됨)
sudo sysctl -w fs.inotify.max_user_watches=1048576

# 영구 적용
echo "fs.inotify.max_user_watches=1048576" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 방법 4: Watcher 프로세스 재등록

```bash
# Cursor watcher 재시작
killall -HUP cursor-server 2>/dev/null || true

# 또는 모든 IDE 프로세스 재시작
killall -HUP cursor-server code 2>/dev/null || true
```

### 방법 5: 파일 시스템 캐시 초기화

```bash
# 파일 시스템 동기화
sync

# inode 캐시 무효화 (주의: 성능에 영향)
sudo sysctl vm.drop_caches=2
```

## 🛠️ 진단 스크립트

다음 스크립트를 실행하여 자동으로 진단할 수 있습니다:

```bash
#!/bin/bash
# check_file_watcher.sh

echo "=== IDE 파일 Watcher 진단 ==="
echo ""

echo "1. inotify 리밋:"
cat /proc/sys/fs/inotify/max_user_watches

echo ""
echo "2. 프로젝트 폴더 권한:"
ls -ld /home/won/projects/dreamseed_monorepo

echo ""
echo "3. 실행 중인 IDE 프로세스:"
ps aux | grep -E "(code|cursor)" | grep -v grep | head -3

echo ""
echo "4. inotify 사용량:"
find /proc/*/fd -lname anon_inode:inotify -printf '%h\n' 2>/dev/null | wc -l

echo ""
echo "5. 테스트 파일 생성:"
echo "테스트 중..." > /home/won/projects/dreamseed_monorepo/.watcher_test
sleep 1
if [ -f /home/won/projects/dreamseed_monorepo/.watcher_test ]; then
    echo "✅ 파일 생성 성공"
    rm /home/won/projects/dreamseed_monorepo/.watcher_test
else
    echo "❌ 파일 생성 실패"
fi
```

## 💡 권장 설정

### VS Code / Cursor workspace 설정

`dreamseed.code-workspace`에 다음을 추가 (필요 시):

```json
{
  "settings": {
    "files.watcherExclude": {
      "**/.git/objects/**": true,
      "**/.git/subtree-cache/**": true,
      "**/node_modules/**": true,
      "**/.venv/**": true,
      "**/dist/**": true,
      "**/build/**": true
    },
    "files.watcherInclude": [
      "**/*.py",
      "**/*.ts",
      "**/*.tsx",
      "**/*.yaml",
      "**/*.yml",
      "**/*.md"
    ]
  }
}
```

## ✅ 확인 체크리스트

- [ ] 두 IDE 모두 같은 권한/유저로 실행
- [ ] inotify 리밋 충분 (524288 이상)
- [ ] 로컬 디스크 (SSD)에서 작업
- [ ] watcher 비활성화 패턴 제거
- [ ] IDE reload 완료
- [ ] 파일 시스템 캐시 정상

## 🚨 여전히 문제가 있으면

1. **한 IDE만 사용**: 가장 간단한 해결책
2. **파일 수동 새로고침**: `Ctrl + R` 또는 파일 탐색기 새로고침
3. **Git 상태 확인**: `git status`로 실제 파일 변경 확인
4. **로그 확인**: IDE 개발자 콘솔에서 watcher 오류 확인

---

**마지막 업데이트**: 2025-01-01
**환경**: Linux 6.8.0-84-generic, Ubuntu/Debian


