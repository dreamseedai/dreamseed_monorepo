# PC 호스팅 전환 플랜
**목표**: DreamSeedAI.com을 수익 발생 전까지 로컬 PC에서 호스팅

## 📋 Phase 1: PC 환경 준비

### 1.1 하드웨어 체크리스트
- [ ] CPU: 최소 4코어 (8코어+ 권장)
- [ ] RAM: 최소 16GB (32GB+ 권장)
- [ ] 디스크: SSD 500GB+ (데이터베이스, 백업용)
- [ ] 네트워크: 고정 IP 또는 DDNS
- [ ] UPS: 정전 대비 (선택)

### 1.2 소프트웨어 스택
```bash
# 필수 설치
- Docker / Docker Compose (현재 사용 중인 서비스 그대로 이전)
- PostgreSQL (Cloud SQL 대체)
- Caddy 또는 Nginx (리버스 프록시 + SSL)
- Cloudflare Tunnel 또는 DDNS (도메인 연결)
```

---

## 🚀 Phase 2: GCP → PC 마이그레이션

### 2.1 데이터 백업 (GCP → 로컬)

```bash
# Cloud SQL 데이터 덤프
gcloud sql export sql seedtest-main \
  gs://univprepai-backups/sql/seedtest-$(date +%Y%m%d).sql \
  --database=seedtest

# 로컬로 다운로드
gsutil cp gs://univprepai-backups/sql/seedtest-*.sql ~/backups/

# PostgreSQL 복원
psql -U postgres -d seedtest < ~/backups/seedtest-*.sql
```

### 2.2 Docker Compose 설정 (로컬)

```yaml
# docker-compose.local.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart: unless-stopped

  seedtest_api:
    build: ./apps/seedtest_api
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@postgres:5432/seedtest
    restart: unless-stopped

  caddy:
    image: caddy:2
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    restart: unless-stopped

volumes:
  caddy_data:
```

### 2.3 Cloudflare Tunnel (무료 SSL + 도메인)

```bash
# Cloudflare Tunnel 설치 (공인 IP 없이도 도메인 연결)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# 인증
cloudflared tunnel login

# 터널 생성
cloudflared tunnel create dreamseedai

# 도메인 연결
cloudflared tunnel route dns dreamseedai dreamseedai.com

# 자동 시작 서비스 등록
sudo cloudflared service install
```

**Cloudflare 설정 (config.yml):**
```yaml
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: dreamseedai.com
    service: http://localhost:3000
  - hostname: api.dreamseedai.com
    service: http://localhost:8000
  - service: http_status:404
```

---

## 💰 Phase 3: 비용 비교

| 항목 | GCP (현재) | PC 호스팅 | 절감 |
|------|-----------|----------|------|
| 컴퓨팅 | CA$275/월 | CA$0 | ✅ |
| 데이터베이스 | CA$15/월 | CA$0 | ✅ |
| 네트워크 | CA$5/월 | CA$0 | ✅ |
| **월 비용** | **CA$10-20** | **전기세 CA$3-5** | **CA$15 절감** |
| **연 비용** | **CA$120-240** | **CA$36-60** | **CA$180 절감** |

**PC 전기세 계산:**
- PC 소비 전력: 100W (평균)
- 24/7 가동: 100W × 24h × 30일 = 72kWh/월
- 전기 요금: 72kWh × CA$0.15 = **CA$10.80/월**
- Docker만 가동 시 (아이들): ~CA$3-5/월

---

## 🎓 Phase 4: 학교/학원 계약 시 GCP 복원

### 4.1 즉시 복원 (5-10분)

```bash
# 1. GKE 클러스터 재생성
bash ~/projects/dreamseed_monorepo/scripts/gke-restore.sh

# 2. Cloud SQL 재시작
gcloud sql instances patch seedtest-main --activation-policy=ALWAYS

# 3. 백업에서 데이터 복원
kubectl apply -f /backup/dreamseed/gke-backup-20251106/all-resources.yaml

# 4. DNS 전환 (Cloudflare)
# dreamseedai.com A 레코드: PC IP → GCP Load Balancer IP
```

### 4.2 예상 복원 시간
- GKE Autopilot 생성: **3-5분**
- Cloud SQL 시작: **2-3분**
- 데이터 복원: **1-2분**
- DNS 전파: **1-5분**
- **총 소요 시간: 7-15분**

---

## 🛡️ Phase 5: 하이브리드 운영 (계약 후)

### 옵션 A: 학교별 전용 인스턴스 (GCP)
```
학교A → GCP Cloud Run (독립 DB)
학교B → GCP Cloud Run (독립 DB)
개인 → PC 호스팅
```

**장점:**
- 학교 데이터 격리 (보안)
- 비용을 학교에 청구 가능
- PC는 개발/테스트용

### 옵션 B: PC 메인 + GCP 백업
```
메인 서비스 → PC 호스팅
백업/DR → GCP (최소 구성)
```

**장점:**
- 비용 최소화
- 장애 시 GCP 자동 전환
- Cloudflare Load Balancing 활용

---

## 📝 마이그레이션 체크리스트

### PC 호스팅 전환 (수익 전)
- [ ] Docker Compose 로컬 테스트
- [ ] PostgreSQL 로컬 설치 + 데이터 마이그레이션
- [ ] Cloudflare Tunnel 설정
- [ ] SSL 인증서 자동 갱신 확인
- [ ] 백업 자동화 (rsync → 외장 HDD)
- [ ] GCP 리소스 완전 삭제 (비용 CA$0)

### GCP 복원 준비 (계약 대기)
- [ ] 복원 스크립트 테스트 (dry-run)
- [ ] 백업 최신화 (주 1회)
- [ ] 계약서 템플릿 (클라우드 비용 포함)
- [ ] SLA 문서 (99.9% 가동률 보장)

---

## 🚨 긴급 복원 프로토콜

**학교 계약 체결 즉시 (15분 안에 GCP 복원):**

```bash
# 원클릭 복원
bash ~/projects/dreamseed_monorepo/scripts/gcp-emergency-restore.sh

# 이 스크립트가 자동 실행:
# 1. GKE Autopilot 생성
# 2. Cloud SQL 시작
# 3. 최신 백업 복원
# 4. DNS A 레코드 변경 (Cloudflare API)
# 5. Health check (200 OK 확인)
```

---

## 💡 권장 전략

### 단기 (지금~3개월)
1. **PC 호스팅으로 전환**
2. GCP 완전 삭제 (월 CA$0)
3. Cloudflare Tunnel로 도메인 유지
4. 주 1회 백업 (GCP Storage에 업로드, CA$0.50/월)

### 중기 (계약 체결 시)
1. **15분 안에 GCP 복원**
2. 학교별 독립 인스턴스 (비용 청구)
3. PC는 개발 환경으로 유지

### 장기 (수익 안정화)
1. GCP 프로덕션 유지
2. PC는 개발/테스트
3. Multi-region 확장 (필요 시)

---

## 📞 다음 단계

지금 바로 실행 가능:
```bash
# 1. 로컬 Docker Compose 테스트
cd ~/projects/dreamseed_monorepo
docker-compose -f docker-compose.local.yml up

# 2. Cloudflare Tunnel 설정 (무료)
cloudflared tunnel login

# 3. GCP 리소스 완전 삭제 (선택)
APPLY=yes bash scripts/gke-post-delete-cleanup.sh
gcloud sql instances delete seedtest-main --quiet
```

**준비되셨으면 어떤 것부터 도와드릴까요?**
1. 로컬 Docker Compose 설정
2. Cloudflare Tunnel 설정
3. GCP 완전 삭제 스크립트
4. 긴급 복원 스크립트
