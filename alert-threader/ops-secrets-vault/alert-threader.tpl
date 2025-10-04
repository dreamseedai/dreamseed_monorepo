{{ with secret "kv/data/alert-threader" }}
# =============================
# Alert Threader Environment (Vault)
# =============================
# 자동 생성: {{ now | date "2006-01-02 15:04:05" }}

# =============================
# Slack Bot Configuration
# =============================
SLACK_BOT_TOKEN={{ .Data.data.SLACK_BOT_TOKEN }}
SLACK_CHANNEL={{ .Data.data.SLACK_CHANNEL }}
ENVIRONMENT={{ .Data.data.ENVIRONMENT }}

# =============================
# Storage Configuration
# =============================
THREAD_STORE={{ .Data.data.THREAD_STORE }}
THREAD_STORE_FILE={{ .Data.data.THREAD_STORE_FILE }}

# =============================
# Redis Configuration
# =============================
REDIS_URL={{ .Data.data.REDIS_URL }}
REDIS_KEY_PREFIX={{ .Data.data.REDIS_KEY_PREFIX }}

# =============================
# Service Configuration
# =============================
BIND_HOST=0.0.0.0
BIND_PORT=9009

# =============================
# Security & Performance
# =============================
REDIS_TIMEOUT=5
LOG_LEVEL=info
MAX_CONCURRENT_ALERTS=100

# =============================
# Monitoring & Health
# =============================
HEALTH_CHECK_INTERVAL=30
ENABLE_STATS=true

# =============================
# Advanced Configuration
# =============================
THREAD_KEY_STRATEGY=simple
CACHE_TTL=86400
MAX_RETRIES=3
RETRY_DELAY=1000
{{ end }}
