#!/usr/bin/env bash
set -euo pipefail

# Multi-cloud real IP provider sync (Cloudflare + AWS ELB + GCP LB + AWS VPC Subnets)
# Writes to /etc/nginx/conf.d/real_ip_providers.conf and reloads nginx iff changed.
# Safe to run repeatedly (idempotent).

OUT_DIR=/etc/nginx/conf.d
OUT_FILE="$OUT_DIR/real_ip_providers.conf"
TMP_DIR=$(mktemp -d)
TMP_FILE="$TMP_DIR/real_ip_providers.conf"
LOCK_FILE=/run/update_real_ip_providers.lock

# Provider URLs
CF_V4_URL="https://www.cloudflare.com/ips-v4"
CF_V6_URL="https://www.cloudflare.com/ips-v6"
AWS_URL="https://ip-ranges.amazonaws.com/ip-ranges.json"
GCP_URL="https://www.gstatic.com/ipranges/cloud.json"

# Provider toggles (environment variables)
CF_ENABLE=${CF_ENABLE:-yes}
AWS_ENABLE=${AWS_ENABLE:-no}
GCP_ENABLE=${GCP_ENABLE:-no}
AWS_VPC_SUBNETS=${AWS_VPC_SUBNETS:-no}

# GCP scope filter
GCP_SCOPE=${GCP_SCOPE:-GLOBAL}

# Optional flags
KEEP_LOCAL="yes"  # keep set_real_ip_from 127.0.0.1

exec 9>"$LOCK_FILE" || true
if ! flock -n 9; then
  echo "Another update is in progress; exiting." >&2
  exit 0
fi

mkdir -p "$OUT_DIR"

# Helper functions
fetch() {
  local url="$1"
  curl -fsSL "$url" || {
    echo "# Failed to fetch $url" >&2
    return 1
  }
}

append_set_lines() {
  while IFS= read -r line; do
    if [ -n "$line" ]; then
      echo "set_real_ip_from $line;"
    fi
  done
}

# Check for jq
if ! command -v jq >/dev/null 2>&1; then
  JQ_MISSING=1
fi

# Build output
{
  echo "# Auto-generated on $(date -u +%FT%TZ)"
  echo "# Providers: CF=$CF_ENABLE AWS=$AWS_ENABLE GCP=$GCP_ENABLE VPC_SUBNETS=$AWS_VPC_SUBNETS"
  [ "$KEEP_LOCAL" = "yes" ] && echo "set_real_ip_from 127.0.0.1;"

  # Cloudflare
  if [ "$CF_ENABLE" = "yes" ]; then
    echo "# Cloudflare"
    fetch "$CF_V4_URL" | awk 'NF' | append_set_lines || true
    fetch "$CF_V6_URL" | awk 'NF' | append_set_lines || true
  fi

  # AWS ELB (only service == ELB)
  if [ "$AWS_ENABLE" = "yes" ]; then
    echo "# AWS ELB (ip-ranges.json, service=ELB)"
    if [ -z "${JQ_MISSING:-}" ]; then
      fetch "$AWS_URL" | jq -r '.prefixes[] | select(.service=="ELB") | .ip_prefix' | append_set_lines || true
      fetch "$AWS_URL" | jq -r '.ipv6_prefixes[] | select(.service=="ELB") | .ipv6_prefix' | append_set_lines || true
    else
      # jq가 없을 때 Python으로 파싱 (표준 라이브러리만 사용)
      python3 - "$AWS_URL" <<'PY'
import json,sys,urllib.request
url=sys.argv[1]
with urllib.request.urlopen(url) as r:
    data=json.load(r)
for p in data.get('prefixes',[]):
    if p.get('service')=='ELB' and 'ip_prefix' in p:
        print(f"set_real_ip_from {p['ip_prefix']};")
for p in data.get('ipv6_prefixes',[]):
    if p.get('service')=='ELB' and 'ipv6_prefix' in p:
        print(f"set_real_ip_from {p['ipv6_prefix']};")
PY
    fi
    echo "# NOTE: For ALB/NLB, prefer trusting your VPC subnet CIDRs instead of ip-ranges.json."
  fi

  # GCP LB / Google Front Ends — scope filter
  if [ "$GCP_ENABLE" = "yes" ]; then
    echo "# GCP (cloud.json, scope=$GCP_SCOPE)"
    if [ -z "${JQ_MISSING:-}" ]; then
      fetch "$GCP_URL" | jq -r --arg S "$GCP_SCOPE" '.prefixes[] | select((.scope==$S) and (.ipv4Prefix or .ipv6Prefix)) | (.ipv4Prefix // .ipv6Prefix)' | append_set_lines || true
    else
      python3 - "$GCP_URL" "$GCP_SCOPE" <<'PY'
import json,sys,urllib.request
url,scope=sys.argv[1],sys.argv[2]
with urllib.request.urlopen(url) as r:
    data=json.load(r)
for p in data.get('prefixes',[]):
    if p.get('scope')==scope:
        cidr=p.get('ipv4Prefix') or p.get('ipv6Prefix')
        if cidr: print(f"set_real_ip_from {cidr};")
PY
    fi
  fi

  # AWS VPC Subnets (for ALB/NLB trust)
  if [ "$AWS_VPC_SUBNETS" = "yes" ]; then
    echo "# AWS VPC Subnets (for ALB/NLB trust)"
    if command -v aws >/dev/null 2>&1; then
      REGION=${AWS_REGION:-$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region 2>/dev/null || echo "")}
      VPCID=${AWS_VPC_ID:-$(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/ 2>/dev/null | head -n1 | xargs -I{} curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/{}/vpc-id 2>/dev/null || echo "")}
      if [ -n "$REGION" ] && [ -n "$VPCID" ]; then
        aws ec2 describe-subnets --region "$REGION" --filters "Name=vpc-id,Values=$VPCID" \
          --query 'Subnets[].CidrBlock' --output text 2>/dev/null | tr '\t' '\n' | append_set_lines || true
        aws ec2 describe-subnets --region "$REGION" --filters "Name=vpc-id,Values=$VPCID" \
          --query 'Subnets[].Ipv6CidrBlockAssociationSet[].Ipv6CidrBlock' --output text 2>/dev/null | tr '\t' '\n' | append_set_lines || true
      else
        echo "# ⚠️ Could not detect REGION/VPCID from metadata; set AWS_REGION and AWS_VPC_ID explicitly." >&2
      fi
    else
      echo "# ⚠️ AWS CLI not found; skipping VPC Subnets" >&2
    fi
  fi
} > "$TMP_FILE"

# replace atomically if changed
need_update=1
if [ -f "$OUT_FILE" ]; then
  if sha256sum "$OUT_FILE" "$TMP_FILE" | awk '{print $1}' | uniq -d | grep -q .; then
    need_update=0
  fi
fi

if [ "$need_update" -eq 1 ]; then
  cp -af "$TMP_FILE" "$OUT_FILE"
  if nginx -t; then
    systemctl reload nginx
    echo "✅ real_ip providers updated → nginx reloaded"
  else
    echo "❌ nginx -t failed; not reloading" >&2
    exit 1
  fi
else
  echo "No changes in provider CIDRs"
fi

rm -rf "$TMP_DIR" || true
