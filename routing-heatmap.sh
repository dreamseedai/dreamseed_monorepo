#!/bin/bash

# 🧪 실시간 라우팅 히트맵 (간단)
# 최근 1시간, 레인별/키워드별 히트 카운트

set -e

LOG_FILE="/tmp/router.log"

echo "🧪 DreamSeed AI 실시간 라우팅 히트맵"
echo "====================================="

if [ ! -f "$LOG_FILE" ]; then
  echo "❌ 로그 파일이 없습니다: $LOG_FILE"
  echo "💡 라우터를 실행하고 요청을 보내면 로그가 생성됩니다."
  exit 1
fi

# 최근 1시간 기준
SINCE=$(date -d '1 hour ago' +%Y-%m-%dT%H:)

echo "📅 분석 기간: 최근 1시간 (since $SINCE)"
echo ""

# 라우팅 히트맵 생성
echo "🔥 라우팅 히트맵 (최근 1시간)"
echo "================================"

awk -v since="$SINCE" '
  $1 ~ "^ts=" && $1 >= "ts="since { 
    for (i=1;i<=NF;i++) if ($i ~ /^lane=/) lane=$i;
    for (i=1;i<=NF;i++) if ($i ~ /^hint=/) hint=$i;
    gsub(/lane=|hint=|\"/,"",lane); gsub(/hint=|\"/,"",hint);
    split(hint,a,"\\|"); kw=a[1];
    c[lane":"kw]++
  }
  END { 
    print "📊 레인:키워드별 히트 수"
    print "------------------------"
    for (k in c) print c[k], k | "sort -nr"
  }' "$LOG_FILE" | head -20

echo ""

# 레인별 요약
echo "📊 레인별 요약 (최근 1시간)"
echo "============================="
awk -v since="$SINCE" '
  $1 ~ "^ts=" && $1 >= "ts="since { 
    for (i=1;i<=NF;i++) if ($i ~ /^lane=/) lane=$i;
    gsub(/lane=|\"/,"",lane);
    c[lane]++
  }
  END { 
    for (k in c) print c[k], k | "sort -nr"
  }' "$LOG_FILE"

echo ""

# 키워드별 요약
echo "📊 키워드별 요약 (최근 1시간)"
echo "==============================="
awk -v since="$SINCE" '
  $1 ~ "^ts=" && $1 >= "ts="since { 
    for (i=1;i<=NF;i++) if ($i ~ /^hint=/) hint=$i;
    gsub(/hint=|\"/,"",hint);
    split(hint,a,"\\|"); kw=a[1];
    c[kw]++
  }
  END { 
    for (k in c) print c[k], k | "sort -nr"
  }' "$LOG_FILE"

echo ""

# 실시간 모니터링 안내
echo "💡 실시간 모니터링"
echo "==================="
echo "실시간 히트맵: watch -n 30 './routing-heatmap.sh'"
echo "실시간 로그: tail -f $LOG_FILE"
echo ""

# 북마크용 한 줄 명령어
echo "🔖 북마크용 한 줄 명령어"
echo "========================"
echo "awk -v since=\"\$(date -d '1 hour ago' +%Y-%m-%dT%H:)\" '"
echo "  \$1 ~ \"^ts=\" && \$1 >= \"ts=\"since { "
echo "    for (i=1;i<=NF;i++) if (\$i ~ /^lane=/) lane=\$i;"
echo "    for (i=1;i<=NF;i++) if (\$i ~ /^hint=/) hint=\$i;"
echo "    gsub(/lane=|hint=|\"/,\"\",lane); gsub(/hint=|\"/,\"\",hint);"
echo "    split(hint,a,\"\\\\|\"); kw=a[1];"
echo "    c[lane\":\"kw]++"
echo "  }"
echo "  END { for (k in c) print c[k], k | \"sort -nr\" }' /tmp/router.log | head"
