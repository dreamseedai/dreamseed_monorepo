# DreamSeed AI Platform 배포 가이드

## 📖 목차

1. [배포 개요](#배포-개요)
2. [개발 환경 배포](#개발-환경-배포)
3. [스테이징 환경 배포](#스테이징-환경-배포)
4. [프로덕션 환경 배포](#프로덕션-환경-배포)
5. [Docker 배포](#docker-배포)
6. [Kubernetes 배포](#kubernetes-배포)
7. [모니터링 설정](#모니터링-설정)
8. [백업 및 복구](#백업-및-복구)
9. [문제 해결](#문제-해결)

---

## 🚀 배포 개요

### 배포 환경 구성

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │    │    Staging      │    │   Production    │
│                 │    │                 │    │                 │
│ • Local Server  │───►│ • Test Server   │───►│ • Live Server   │
│ • Port 8002     │    │ • Port 8003     │    │ • Port 80/443   │
│ • Debug Mode    │    │ • Production    │    │ • SSL/TLS       │
│ • Hot Reload    │    │ • Monitoring    │    │ • Load Balancer │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 배포 전 체크리스트

- [ ] 코드 리뷰 완료
- [ ] 테스트 통과 (단위, 통합, E2E)
- [ ] 보안 스캔 완료
- [ ] 성능 테스트 완료
- [ ] 데이터베이스 마이그레이션 준비
- [ ] 환경 변수 설정
- [ ] SSL 인증서 준비
- [ ] 모니터링 설정
- [ ] 백업 전략 수립
- [ ] 롤백 계획 수립

---

## 🛠️ 개발 환경 배포

### 로컬 개발 서버 설정

#### 1. 시스템 요구사항
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip redis-server

# macOS (Homebrew)
brew install python@3.11 redis

# Windows (Chocolatey)
choco install python redis
```

#### 2. 프로젝트 설정
```bash
# 저장소 클론
git clone https://github.com/dreamseed/platform.git
cd platform

# 가상환경 생성 및 활성화
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

#### 3. 환경 변수 설정
```bash
# .env 파일 생성
cat > .env << EOF
PORT=8002
ENVIRONMENT=development
DEBUG=True
REDIS_URL=redis://localhost:6379
DB_PATH=./dreamseed_analytics.db
LOG_LEVEL=DEBUG
EOF
```

#### 4. 데이터베이스 초기화
```bash
# Redis 시작
redis-server

# 데이터베이스 초기화
python -c "
from api.dashboard_data import init_database
init_database()
print('데이터베이스 초기화 완료')
"
```

#### 5. 개발 서버 실행
```bash
# API 서버 실행
python api/dashboard_data.py

# 프론트엔드 서버 실행 (별도 터미널)
python -m http.server 9000
```

#### 6. 접속 확인
- **API 서버**: http://localhost:8002/healthz
- **관리자 패널**: http://localhost:9000/admin/
- **API 문서**: http://localhost:8002/docs

---

## 🧪 스테이징 환경 배포

### 스테이징 서버 설정

#### 1. 서버 준비
```bash
# Ubuntu 20.04+ 서버
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip redis-server nginx

# 사용자 생성
sudo useradd -m -s /bin/bash dreamseed
sudo usermod -aG sudo dreamseed
```

#### 2. 애플리케이션 배포
```bash
# 사용자 전환
sudo su - dreamseed

# 프로젝트 디렉토리 생성
mkdir -p /home/dreamseed/apps
cd /home/dreamseed/apps

# 코드 배포
git clone https://github.com/dreamseed/platform.git dreamseed
cd dreamseed

# 가상환경 설정
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. 환경 설정
```bash
# 스테이징 환경 변수
cat > .env << EOF
PORT=8003
ENVIRONMENT=staging
DEBUG=False
REDIS_URL=redis://localhost:6379
DB_PATH=/home/dreamseed/apps/dreamseed/dreamseed_analytics.db
LOG_LEVEL=INFO
EOF

# 데이터베이스 초기화
python -c "from api.dashboard_data import init_database; init_database()"
```

#### 4. systemd 서비스 설정
```bash
# 서비스 파일 생성
sudo tee /etc/systemd/system/dreamseed-staging.service > /dev/null << EOF
[Unit]
Description=DreamSeed Staging API Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=dreamseed
Group=dreamseed
WorkingDirectory=/home/dreamseed/apps/dreamseed
EnvironmentFile=/home/dreamseed/apps/dreamseed/.env
ExecStart=/home/dreamseed/apps/dreamseed/venv/bin/python api/dashboard_data.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable dreamseed-staging
sudo systemctl start dreamseed-staging
```

#### 5. Nginx 설정
```bash
# Nginx 설정 파일 생성
sudo tee /etc/nginx/sites-available/dreamseed-staging > /dev/null << EOF
server {
    listen 80;
    server_name staging.dreamseed.com;

    location / {
        proxy_pass http://localhost:8003;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 사이트 활성화
sudo ln -s /etc/nginx/sites-available/dreamseed-staging /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 6. 방화벽 설정
```bash
# UFW 설정
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

#### 7. 배포 스크립트 실행
```bash
# 배포 스크립트 실행
chmod +x deploy_staging.sh
./deploy_staging.sh
```

---

## 🌐 프로덕션 환경 배포

### 프로덕션 서버 설정

#### 1. 서버 준비
```bash
# Ubuntu 20.04+ 서버
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip redis-server nginx certbot python3-certbot-nginx

# 보안 강화
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

#### 2. SSL 인증서 설정
```bash
# Let's Encrypt 인증서 발급
sudo certbot --nginx -d dreamseedai.com -d www.dreamseedai.com

# 자동 갱신 설정
sudo crontab -e
# 다음 라인 추가:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 3. 애플리케이션 배포
```bash
# 사용자 생성
sudo useradd -m -s /bin/bash dreamseed
sudo usermod -aG sudo dreamseed

# 애플리케이션 디렉토리 생성
sudo mkdir -p /opt/dreamseed
sudo chown dreamseed:dreamseed /opt/dreamseed

# 코드 배포
sudo su - dreamseed
cd /opt/dreamseed
git clone https://github.com/dreamseed/platform.git .
```

#### 4. 프로덕션 환경 설정
```bash
# 프로덕션 환경 변수
cat > .env << EOF
PORT=8002
ENVIRONMENT=production
DEBUG=False
REDIS_URL=redis://localhost:6379
DB_PATH=/opt/dreamseed/data/dreamseed_analytics.db
LOG_LEVEL=WARNING
SECRET_KEY=your-secret-key-here
EOF

# 데이터 디렉토리 생성
mkdir -p /opt/dreamseed/data
mkdir -p /opt/dreamseed/logs
```

#### 5. Gunicorn 설정
```bash
# Gunicorn 설치
source venv/bin/activate
pip install gunicorn

# Gunicorn 설정 파일
cat > gunicorn.conf.py << EOF
import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '8002')}"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 4
timeout = 60
graceful_timeout = 30
keepalive = 5
accesslog = "/opt/dreamseed/logs/access.log"
errorlog = "/opt/dreamseed/logs/error.log"
loglevel = "info"
EOF
```

#### 6. systemd 서비스 설정
```bash
# 서비스 파일 생성
sudo tee /etc/systemd/system/dreamseed-api.service > /dev/null << EOF
[Unit]
Description=DreamSeed API Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=dreamseed
Group=dreamseed
WorkingDirectory=/opt/dreamseed
EnvironmentFile=/opt/dreamseed/.env
ExecStart=/opt/dreamseed/venv/bin/gunicorn --config gunicorn.conf.py api.dashboard_data:app
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable dreamseed-api
sudo systemctl start dreamseed-api
```

#### 7. Nginx 설정
```bash
# Nginx 설정 파일 생성
sudo tee /etc/nginx/sites-available/dreamseedai.com > /dev/null << EOF
server {
    listen 80;
    server_name dreamseedai.com www.dreamseedai.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dreamseedai.com www.dreamseedai.com;

    ssl_certificate /etc/letsencrypt/live/dreamseedai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dreamseedai.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://localhost:8002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 사이트 활성화
sudo ln -s /etc/nginx/sites-available/dreamseedai.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 8. 배포 스크립트 실행
```bash
# 배포 스크립트 실행
chmod +x deploy_production.sh
./deploy_production.sh
```

---

## 🐳 Docker 배포

### Docker Compose 배포

#### 1. Docker Compose 설정
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  dreamseed-api:
    build: .
    ports:
      - "8002:8002"
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379
      - DB_PATH=/app/data/dreamseed_analytics.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - dreamseed-api
    restart: unless-stopped

volumes:
  redis_data:
```

#### 2. Docker 배포 실행
```bash
# 프로덕션 환경으로 배포
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 서비스 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

### Kubernetes 배포

#### 1. Namespace 생성
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dreamseed
```

#### 2. ConfigMap 생성
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dreamseed-config
  namespace: dreamseed
data:
  ENVIRONMENT: "production"
  REDIS_URL: "redis://redis-service:6379"
  DB_PATH: "/app/data/dreamseed_analytics.db"
  LOG_LEVEL: "INFO"
```

#### 3. Secret 생성
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: dreamseed-secret
  namespace: dreamseed
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret-key>
  REDIS_PASSWORD: <base64-encoded-redis-password>
```

#### 4. Deployment 생성
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dreamseed-api
  namespace: dreamseed
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dreamseed-api
  template:
    metadata:
      labels:
        app: dreamseed-api
    spec:
      containers:
      - name: dreamseed-api
        image: dreamseed:latest
        ports:
        - containerPort: 8002
        envFrom:
        - configMapRef:
            name: dreamseed-config
        - secretRef:
            name: dreamseed-secret
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: dreamseed-data-pvc
```

#### 5. Service 생성
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: dreamseed-api-service
  namespace: dreamseed
spec:
  selector:
    app: dreamseed-api
  ports:
  - port: 80
    targetPort: 8002
  type: LoadBalancer
```

#### 6. Ingress 생성
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dreamseed-ingress
  namespace: dreamseed
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - dreamseedai.com
    - www.dreamseedai.com
    secretName: dreamseed-tls
  rules:
  - host: dreamseedai.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dreamseed-api-service
            port:
              number: 80
```

#### 7. Kubernetes 배포 실행
```bash
# 네임스페이스 생성
kubectl apply -f k8s/namespace.yaml

# ConfigMap 및 Secret 생성
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 애플리케이션 배포
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# 배포 상태 확인
kubectl get pods -n dreamseed
kubectl get services -n dreamseed
kubectl get ingress -n dreamseed
```

---

## 📊 모니터링 설정

### Prometheus 설정

#### 1. Prometheus 설치
```bash
# Prometheus 다운로드
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xzf prometheus-2.45.0.linux-amd64.tar.gz
sudo mv prometheus-2.45.0.linux-amd64 /opt/prometheus
```

#### 2. Prometheus 설정
```yaml
# /opt/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'dreamseed-api'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: /metrics
    scrape_interval: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
```

#### 3. systemd 서비스 설정
```bash
# Prometheus 서비스 파일
sudo tee /etc/systemd/system/prometheus.service > /dev/null << EOF
[Unit]
Description=Prometheus
After=network.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/opt/prometheus/prometheus --config.file=/opt/prometheus/prometheus.yml
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 사용자 생성
sudo useradd --no-create-home --shell /bin/false prometheus
sudo chown -R prometheus:prometheus /opt/prometheus

# 서비스 시작
sudo systemctl enable prometheus
sudo systemctl start prometheus
```

### Grafana 설정

#### 1. Grafana 설치
```bash
# Grafana 설치
wget https://dl.grafana.com/oss/release/grafana-10.0.0.linux-amd64.tar.gz
tar xzf grafana-10.0.0.linux-amd64.tar.gz
sudo mv grafana-10.0.0 /opt/grafana
```

#### 2. Grafana 설정
```bash
# Grafana 사용자 생성
sudo useradd --no-create-home --shell /bin/false grafana
sudo chown -R grafana:grafana /opt/grafana

# 서비스 파일 생성
sudo tee /etc/systemd/system/grafana.service > /dev/null << EOF
[Unit]
Description=Grafana
After=network.target

[Service]
Type=simple
User=grafana
Group=grafana
ExecStart=/opt/grafana/bin/grafana-server --config=/opt/grafana/conf/grafana.ini
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 서비스 시작
sudo systemctl enable grafana
sudo systemctl start grafana
```

#### 3. 대시보드 설정
- Grafana 접속: http://localhost:3000
- 기본 로그인: admin/admin
- Prometheus 데이터소스 추가
- DreamSeed 대시보드 임포트

---

## 💾 백업 및 복구

### 데이터베이스 백업

#### 1. 자동 백업 설정
```bash
# 백업 스크립트 생성
sudo tee /usr/local/bin/dreamseed-backup.sh > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/dreamseed"
DB_PATH="/opt/dreamseed/data/dreamseed_analytics.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# SQLite 백업
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/dreamseed_$DATE.db'"

# 압축
gzip "$BACKUP_DIR/dreamseed_$DATE.db"

# 오래된 백업 삭제 (14일 이상)
find $BACKUP_DIR -name "dreamseed_*.db.gz" -mtime +14 -delete

echo "백업 완료: dreamseed_$DATE.db.gz"
EOF

sudo chmod +x /usr/local/bin/dreamseed-backup.sh
```

#### 2. Cron 작업 설정
```bash
# 매일 오전 2시에 백업 실행
sudo crontab -e
# 다음 라인 추가:
# 0 2 * * * /usr/local/bin/dreamseed-backup.sh
```

### 애플리케이션 백업

#### 1. 전체 백업 스크립트
```bash
#!/bin/bash
# /usr/local/bin/dreamseed-full-backup.sh

BACKUP_DIR="/var/backups/dreamseed"
APP_DIR="/opt/dreamseed"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 애플리케이션 코드 백업
tar -czf "$BACKUP_DIR/dreamseed_app_$DATE.tar.gz" -C $APP_DIR .

# 데이터베이스 백업
sqlite3 "$APP_DIR/data/dreamseed_analytics.db" ".backup '$BACKUP_DIR/dreamseed_db_$DATE.db'"
gzip "$BACKUP_DIR/dreamseed_db_$DATE.db"

# 설정 파일 백업
tar -czf "$BACKUP_DIR/dreamseed_config_$DATE.tar.gz" /etc/nginx/sites-available/dreamseedai.com /etc/systemd/system/dreamseed-api.service

echo "전체 백업 완료: $DATE"
```

### 복구 절차

#### 1. 데이터베이스 복구
```bash
# 백업 파일 확인
ls -la /var/backups/dreamseed/

# 데이터베이스 복구
gunzip /var/backups/dreamseed/dreamseed_20240115_020000.db.gz
sqlite3 /opt/dreamseed/data/dreamseed_analytics.db ".restore /var/backups/dreamseed/dreamseed_20240115_020000.db"
```

#### 2. 애플리케이션 복구
```bash
# 서비스 중지
sudo systemctl stop dreamseed-api

# 애플리케이션 복구
tar -xzf /var/backups/dreamseed/dreamseed_app_20240115_020000.tar.gz -C /opt/dreamseed/

# 서비스 재시작
sudo systemctl start dreamseed-api
```

---

## 🔧 문제 해결

### 일반적인 문제

#### 1. 서비스 시작 실패
```bash
# 서비스 상태 확인
sudo systemctl status dreamseed-api

# 로그 확인
sudo journalctl -u dreamseed-api -f

# 수동 실행으로 오류 확인
cd /opt/dreamseed
source venv/bin/activate
python api/dashboard_data.py
```

#### 2. 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep :8002
sudo lsof -i :8002

# 프로세스 종료
sudo kill -9 <PID>
```

#### 3. 데이터베이스 연결 오류
```bash
# Redis 상태 확인
redis-cli ping

# 데이터베이스 파일 권한 확인
ls -la /opt/dreamseed/data/
sudo chown dreamseed:dreamseed /opt/dreamseed/data/dreamseed_analytics.db
```

#### 4. Nginx 오류
```bash
# Nginx 설정 테스트
sudo nginx -t

# Nginx 로그 확인
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### 성능 문제

#### 1. 메모리 사용량 확인
```bash
# 메모리 사용량 확인
free -h
ps aux --sort=-%mem | head -10

# Redis 메모리 사용량
redis-cli info memory
```

#### 2. CPU 사용량 확인
```bash
# CPU 사용량 확인
top
htop

# 프로세스별 CPU 사용량
ps aux --sort=-%cpu | head -10
```

#### 3. 디스크 사용량 확인
```bash
# 디스크 사용량 확인
df -h
du -sh /opt/dreamseed/data/
du -sh /var/log/
```

### 로그 분석

#### 1. 애플리케이션 로그
```bash
# 실시간 로그 확인
sudo tail -f /opt/dreamseed/logs/error.log
sudo tail -f /opt/dreamseed/logs/access.log

# 오류 로그 필터링
sudo grep -i error /opt/dreamseed/logs/error.log
sudo grep -i "500\|404\|403" /opt/dreamseed/logs/access.log
```

#### 2. 시스템 로그
```bash
# 시스템 로그 확인
sudo journalctl -u dreamseed-api --since "1 hour ago"
sudo journalctl -u nginx --since "1 hour ago"

# 오류 로그 필터링
sudo journalctl -p err -u dreamseed-api
```

### 모니터링 대시보드

#### 1. Prometheus 메트릭 확인
```bash
# 메트릭 엔드포인트 확인
curl http://localhost:8002/metrics

# 특정 메트릭 확인
curl http://localhost:8002/metrics | grep dreamseed_requests_total
```

#### 2. Grafana 대시보드
- Grafana 접속: http://localhost:3000
- 주요 메트릭:
  - 요청 수 (dreamseed_requests_total)
  - 응답 시간 (dreamseed_request_duration_seconds)
  - 활성 사용자 (dreamseed_active_users)
  - 캐시 히트율 (dreamseed_cache_hits)

---

## 📞 지원 및 문의

- **기술 지원**: tech@dreamseed.com
- **배포 지원**: deploy@dreamseed.com
- **긴급 상황**: emergency@dreamseed.com
- **문서**: https://docs.dreamseed.com
- **GitHub Issues**: [이슈 트래커](https://github.com/dreamseed/platform/issues)

---

*이 배포 가이드는 DreamSeed AI Platform v1.0.0 기준으로 작성되었습니다.*
*최신 업데이트: 2024년 1월 15일*

