# 🛡️ 운영 안전 가드

## 🔄 **재기동 전략**

### **Docker Compose 방식 (권장)**
```yaml
# docker-compose.yml
version: '3.8'
services:
  dreamseed-mistral-7b:
    image: vllm/vllm-openai:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - HF_TOKEN=${HF_TOKEN}
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    command: >
      --model mistralai/Mistral-7B-Instruct-v0.3
      --dtype auto
      --max-model-len 6144
      --max-num-seqs 16
      --max-num-batched-tokens 2048
      --gpu-memory-utilization 0.82
```

### **Systemd 유닛 방식**
```ini
# /etc/systemd/system/dreamseed-ai.service
[Unit]
Description=DreamSeed AI Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/home/won/projects/dreamseed_monorepo/start-profile-s.sh
ExecStop=/home/won/projects/dreamseed_monorepo/stop-profile-s.sh
User=won
Group=won

[Install]
WantedBy=multi-user.target
```

## 🔒 **TLS/방화벽 보안**

### **내부망 + 로드밸런서 구성**
```bash
# 외부 노출 시 권장 구성
# 8010/8000은 내부망 + LB/HTTPS

# Nginx 리버스 프록시 예시
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **방화벽 설정**
```bash
# UFW 방화벽 설정
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 80/tcp    # HTTP (리다이렉트용)
sudo ufw deny 8000/tcp   # 내부 전용
sudo ufw deny 8001/tcp   # 내부 전용
sudo ufw deny 8002/tcp   # 내부 전용
sudo ufw deny 8010/tcp   # 내부 전용
sudo ufw enable
```

## 🔐 **비밀값 관리**

### **환경변수 파일**
```bash
# .env 파일 (Git에 커밋 금지)
HF_TOKEN=hf_your_token_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### **Gitignore 설정**
```gitignore
# .gitignore
.env
*.log
/tmp/
~/.cache/huggingface/
```

### **시크릿 매니저 사용**
```bash
# AWS Secrets Manager 예시
aws secretsmanager get-secret-value \
  --secret-id dreamseed/hf-token \
  --query SecretString --output text

# Kubernetes Secret 예시
kubectl create secret generic dreamseed-secrets \
  --from-literal=HF_TOKEN=hf_your_token_here
```

## 📊 **로그 수집**

### **Docker 로그 수집**
```bash
# 로그 수집 스크립트
#!/bin/bash
# collect-logs.sh

LOG_DIR="/var/log/dreamseed"
mkdir -p $LOG_DIR

# 컨테이너 로그 수집
docker logs dreamseed-mistral-7b > $LOG_DIR/mistral-7b-$(date +%Y%m%d).log 2>&1
docker logs dreamseed-qwen-7b > $LOG_DIR/qwen-7b-$(date +%Y%m%d).log 2>&1

# 라우터 요청/응답 시간 수집
tail -f /tmp/dreamseed-*.log >> $LOG_DIR/router-$(date +%Y%m%d).log
```

### **로그 로테이션**
```bash
# /etc/logrotate.d/dreamseed
/var/log/dreamseed/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 won won
}
```

## 🔍 **모니터링 설정**

### **시스템 메트릭 수집**
```bash
# 시스템 메트릭 수집 스크립트
#!/bin/bash
# system-metrics.sh

METRICS_FILE="/tmp/dreamseed-metrics.log"

# GPU 메트릭
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu \
  --format=csv,noheader,nounits >> $METRICS_FILE

# 메모리 메트릭
free -m | awk 'NR==2{print "memory_used_mb", $3}' >> $METRICS_FILE

# 디스크 메트릭
df -h / | awk 'NR==2{print "disk_usage_percent", $5}' >> $METRICS_FILE
```

### **알림 임계값**
```bash
# 알림 임계값 설정
GPU_MEMORY_THRESHOLD=90    # GPU 메모리 사용률 90%
DISK_USAGE_THRESHOLD=85    # 디스크 사용률 85%
RESPONSE_TIME_THRESHOLD=1000  # 응답 시간 1000ms
ERROR_RATE_THRESHOLD=5     # 에러율 5%
```

## 🚨 **장애 대응 절차**

### **1단계: 자동 복구**
```bash
# 자동 복구 스크립트
#!/bin/bash
# auto-recovery.sh

# 컨테이너 상태 확인
if ! docker ps | grep -q dreamseed-mistral-7b; then
    echo "컨테이너가 실행되지 않음. 자동 재시작..."
    ./start-profile-s.sh
fi

# API 응답 확인
if ! curl -s http://127.0.0.1:8000/v1/models > /dev/null; then
    echo "API 응답 실패. 컨테이너 재시작..."
    ./stop-profile-s.sh
    sleep 10
    ./start-profile-s.sh
fi
```

### **2단계: 수동 개입**
```bash
# 장애 대응 체크리스트
1. ./diagnose-issues.sh 실행
2. ./health-check-60s.sh 실행
3. 시스템 리소스 확인 (nvidia-smi, df -h)
4. 로그 분석 (docker logs, /tmp/dreamseed-*.log)
5. 필요시 모델 파라미터 조정
6. 필요시 시스템 재부팅
```

## 📋 **정기 점검 체크리스트**

### **일일 점검**
- [ ] `./health-check-60s.sh` 실행
- [ ] GPU 메모리 사용률 확인 (< 90%)
- [ ] 응답 시간 확인 (< 1000ms)
- [ ] 에러 로그 확인

### **주간 점검**
- [ ] `./load-test-10.sh` 실행
- [ ] `./cache-monitor.sh` 실행
- [ ] 시스템 메트릭 분석
- [ ] 보안 업데이트 확인

### **월간 점검**
- [ ] 모델 성능 평가
- [ ] 비용 최적화 검토
- [ ] 백업 상태 확인
- [ ] 장애 대응 절차 검토

---

**💡 이 가드라인을 따라 운영하면 안전하고 안정적인 서비스를 제공할 수 있습니다!** 🛡️
