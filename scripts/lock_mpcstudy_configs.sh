#!/usr/bin/env bash
set -euo pipefail

PHP_VER="${PHP_VER:-$(systemctl list-units --type=service --no-legend | awk '{print $1}' \
  | grep -E '^php[0-9]\.[0-9]-fpm\.service$' | sed -E 's/^php([0-9]\.[0-9])-fpm\.service/\1/' | head -n1 || true)}"

VHOST_A=/etc/nginx/sites-available/mpcstudy.com.conf
VHOST_E=/etc/nginx/sites-enabled/mpcstudy.com.conf
POOL="/etc/php/${PHP_VER}/fpm/pool.d/mpcstudy.conf"

echo "[lock] nginx vhost"
[ -f "$VHOST_A" ] && sudo chattr +i "$VHOST_A" || true
[ -L "$VHOST_E" ] && sudo chattr +i "$VHOST_E" || true
echo "  + immutable set (nginx vhost)"

if [ -n "${PHP_VER:-}" ] && [ -f "$POOL" ]; then
  echo "[lock] php-fpm pool ($POOL)"
  sudo chattr +i "$POOL" || true
  echo "  + immutable set (php-fpm pool)"
else
  echo "[lock] php-fpm pool not found (skipped)"
fi

echo "done. (unlock: sudo chattr -i <file>)"


