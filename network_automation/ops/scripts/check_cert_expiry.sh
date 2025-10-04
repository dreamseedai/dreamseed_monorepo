#!/usr/bin/env bash
set -euo pipefail
DOMAIN=${1:?domain}
# days remaining
end_date=$(openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" </dev/null 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
end_ts=$(date -d "$end_date" +%s)
now=$(date +%s)
days=$(( (end_ts - now) / 86400 ))
echo "Cert for $DOMAIN expires in $days days"
if [ $days -lt 14 ]; then
  echo "⚠️ Renew soon" >&2
  exit 1
fi