#!/usr/bin/env bash
set -euo pipefail

# nxreload_safe: nginx 구문 체크 후 리로드 + mpcstudy vhost 무결성 확인
sudo tee /usr/local/bin/nxreload_safe >/dev/null <<'SH'
#!/usr/bin/env bash
set -euo pipefail
CFG="/etc/nginx/sites-available/mpcstudy.com.conf"
SUM_BEFORE=""
[ -f "$CFG" ] && SUM_BEFORE=$(sha256sum "$CFG" | awk '{print $1}')
sudo nginx -t >/dev/null
sudo systemctl reload nginx
if [ -f "$CFG" ]; then
  SUM_AFTER=$(sha256sum "$CFG" | awk '{print $1}')
  if [ "$SUM_BEFORE" != "$SUM_AFTER" ]; then
    echo "!! mpcstudy vhost changed during reload. investigate."; exit 1
  fi
fi
echo "nginx reloaded safely ✔"
SH
sudo chmod +x /usr/local/bin/nxreload_safe

# (선택) 짧은 별칭
if [ ! -f /usr/local/bin/nxreload ]; then
  echo -e '#!/usr/bin/env bash\nexec /usr/local/bin/nxreload_safe "$@"' | sudo tee /usr/local/bin/nxreload >/dev/null
  sudo chmod +x /usr/local/bin/nxreload
fi

echo "installed: /usr/local/bin/nxreload_safe"


