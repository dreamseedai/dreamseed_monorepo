#!/usr/bin/env bash
set -euo pipefail

DOMAIN=${1:?"domain"}

echo "🔍 Checking certificate expiry for $DOMAIN"

# Get certificate end date
end_date=$(openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" </dev/null 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
end_ts=$(date -d "$end_date" +%s)
now=$(date +%s)
days=$(( (end_ts - now) / 86400 ))

echo "📅 Certificate for $DOMAIN expires in $days days"

if [ $days -lt 14 ]; then
  echo "⚠️ Certificate expires in less than 14 days - renew soon!" >&2
  echo "🔧 Run: sudo certbot renew --nginx" >&2
  exit 1
elif [ $days -lt 30 ]; then
  echo "⚠️ Certificate expires in less than 30 days - schedule renewal" >&2
  exit 0
else
  echo "✅ Certificate is valid for more than 30 days"
  exit 0
fi
