# SSH 최적화 명령어 모음

## 1️⃣ 서버 설정 적용 (원라이너)

**서버 셸에서 실행:**

```bash
echo "UseDNS no
GSSAPIAuthentication no
PrintMotd no
PrintLastLog no" | sudo tee /etc/ssh/sshd_config.d/10-fast-login.conf >/dev/null \
&& sudo systemctl reload sshd \
&& echo "✅ sshd fast-login config applied"
```

**원복 (필요시):**
```bash
sudo rm /etc/ssh/sshd_config.d/10-fast-login.conf && sudo systemctl reload sshd
```

---

## 2️⃣ 빠른 측정 (PowerShell)

### 첫 연결 측정
```powershell
Measure-Command { ssh -T dreamseed true }
```

### 사용자/호스트 확인
```powershell
Measure-Command { ssh -T dreamseed "whoami && hostname" }
```

### ControlMaster 효과 확인 (3회 연속)
```powershell
1..3 | % { Measure-Command { ssh -T dreamseed true } | % TotalMilliseconds }
```

**목표:**
- 첫 실행: **< 300ms**
- 이후: **< 100-150ms**

---

## 3️⃣ (옵션) PAM MOTD 스크립트 확인

**서버에서 실행:**

```bash
for s in /etc/update-motd.d/*; do
  printf "=== %s ===\n" "$s"
  time bash "$s" >/dev/null
done
```

느린 스크립트 비활성화 예:
```bash
sudo chmod -x /etc/update-motd.d/50-something-slow
```

---

## 측정 결과 보고 형식

결과 수치만 알려주세요:
- 예: **"첫 0.28s / 이후 0.09s"**

추가 최적화가 필요하면 KEX/암호군 우선순위 튜닝으로 수십 ms 더 줄일 수 있습니다.

