# 🛠️ DreamSeedAI MegaCity – DevOps Runbook

## 운영 매뉴얼 · 장애 대응 · 배포 전략 · DR(재해 복구) · CI/CD · SRE 절차

**버전:** 1.0  
**작성일:** 2025-11-21  
**작성자:** DreamSeedAI DevOps & SRE Team

---

# 📌 0. 개요 (Overview)

이 문서는 DreamSeedAI MegaCity 전체(9개 Zone + Core City + AI Cluster)의 안정적인 운영을 위한
**DevOps Runbook(운영 매뉴얼)** 입니다.

이 문서는 운영자가 다음을 할 수 있도록 설계되었습니다:

* 장애를 재현 없이 즉시 파악하고 해결
* 안전하게 서비스 배포·롤백
* 모니터링/알람 체계 유지
* DR(Disaster Recovery) 시나리오 수행
* CI/CD 파이프라인 관리

본 문서는 **SRE(On-call), DevOps 엔지니어, 백엔드/AI 엔지니어** 모두가 필수로 참조해야 합니다.

---

# 🧭 1. MegaCity 운영 개요 (Operations Overview)

MegaCity 운영은 다음 7개 시스템 레이어로 나누어 관리합니다:

```
1. DNS & Edge Layer (Cloudflare)
2. Reverse Proxy Layer (Nginx / Traefik)
3. Application Layer (FastAPI / Next.js)
4. Data Layer (PostgreSQL / Redis)
5. AI Cluster Layer (vLLM / Whisper / PoseNet / Diffusion)
6. Observability Layer (Prometheus / Grafana / Loki / Tempo)
7. Deployment Layer (CI/CD / GitHub Actions / IaC)
```

각 레이어는 장애 발생 시 다른 레이어에 영향을 줄 수 있으므로
**단계적 문제 분리(Isolation) 절차**가 매우 중요합니다.

## 1.1 운영 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                  Cloudflare Edge (DNS/WAF/DDoS)         │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Nginx/Traefik (Reverse Proxy)              │
│         SSL Termination · Rate Limiting · Routing       │
└─────────┬──────────────────────────┬────────────────────┘
          │                          │
┌─────────▼──────────┐    ┌─────────▼──────────────────┐
│   Application      │    │    AI Cluster              │
│   FastAPI Backend  │    │    vLLM / Whisper / Pose   │
│   Next.js Frontend │    │    GPU RTX 5090 × 2-5      │
└─────────┬──────────┘    └─────────┬──────────────────┘
          │                          │
┌─────────▼──────────────────────────▼────────────────────┐
│              Data Layer (PostgreSQL / Redis)            │
│         PgBouncer · Patroni · Sentinel · Cluster        │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│        Observability (Prometheus/Grafana/Loki/Tempo)    │
└─────────────────────────────────────────────────────────┘
```

## 1.2 운영 팀 역할

| 역할 | 책임 |
|------|------|
| **SRE (On-call)** | 24/7 장애 대응, 알람 모니터링, Runbook 실행 |
| **DevOps** | CI/CD 파이프라인, Infrastructure as Code, 배포 자동화 |
| **Backend Engineer** | 애플리케이션 코드, API 성능 최적화, DB 쿼리 튜닝 |
| **AI Engineer** | AI 모델 배포, GPU 클러스터 관리, 추론 성능 최적화 |
| **Security Engineer** | WAF 규칙, 보안 패치, 침입 탐지, 취약점 관리 |

## 1.3 주요 서버 목록

| 서버 | 역할 | IP | OS |
|------|------|----|----|
| `edge-proxy-01` | Nginx Primary | 10.0.1.10 | Ubuntu 22.04 |
| `backend-api-01` | FastAPI Primary | 10.0.2.10 | Ubuntu 22.04 |
| `backend-api-02` | FastAPI Replica | 10.0.2.11 | Ubuntu 22.04 |
| `gpu-cluster-01` | AI Primary (GPU1-2) | 10.0.3.10 | Ubuntu 22.04 |
| `gpu-cluster-02` | AI Replica (GPU3-5) | 10.0.3.11 | Ubuntu 22.04 |
| `db-primary-01` | PostgreSQL Primary | 10.0.4.10 | Ubuntu 22.04 |
| `db-replica-01` | PostgreSQL Replica | 10.0.4.11 | Ubuntu 22.04 |
| `redis-master-01` | Redis Primary | 10.0.5.10 | Ubuntu 22.04 |
| `redis-replica-01` | Redis Replica | 10.0.5.11 | Ubuntu 22.04 |
| `monitoring-01` | Prometheus/Grafana | 10.0.6.10 | Ubuntu 22.04 |

---

# 🚨 2. 장애 대응 매뉴얼 (Incident Response)

## 2.1 장애 등급 정의

```
P1 – 전 구역 서비스 중단 (API/DB/A.I. 불가)
     예: PostgreSQL 다운, 모든 API 5xx, GPU 클러스터 전체 다운
     대응 시간: 15분 이내
     알림: PagerDuty + Slack + SMS

P2 – 특정 Zone 중단 (예: api.univprepai.com)
     예: 특정 Zone API 장애, 특정 AI 엔진 장애
     대응 시간: 30분 이내
     알림: Slack + Email

P3 – 주요 기능 지연 (Exam / AI Inference latency 증가)
     예: p95 latency > 2s, GPU 메모리 > 90%
     대응 시간: 1시간 이내
     알림: Slack

P4 – 경미한 문제 (로그 증가 / 경고)
     예: 로그 에러율 증가, 디스크 사용량 증가
     대응 시간: 4시간 이내
     알림: Slack (Low Priority)
```

## 2.2 기본 대응 흐름

```
┌──────────────┐
│ AlertManager │  → Slack 알림 / PagerDuty 페이징
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  장애 선언   │  → Incident Channel 생성 (#incident-2025-11-21-001)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Runbook 적용 │  → 이 문서의 장애 유형별 절차 실행
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  원인 분석   │  → 로그, 메트릭, 트레이스 분석
└──────┬───────┘
       │
       ▼
┌──────────────┐
│     복구     │  → 서비스 정상화
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Post-Mortem  │  → 24시간 내 사후 보고서 작성
└──────────────┘
```

## 2.3 공통 초기 점검 명령어

```bash
# 1. Reverse Proxy 상태 점검
ssh edge-proxy-01
systemctl status nginx
journalctl -u nginx -n 200 --no-pager
nginx -t  # config test

# 2. Backend API 상태
curl -I https://api.univprepai.com/health
curl -I https://api.dreamseedai.com/health
ssh backend-api-01
systemctl status backend-api
journalctl -u backend-api -n 200 --no-pager

# 3. DB 연결 수 및 활성 쿼리
ssh db-primary-01
psql -U postgres -d dreamseed -c "SELECT count(*) FROM pg_stat_activity;"
psql -U postgres -d dreamseed -c "SELECT pid, query_start, state, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"

# 4. Redis 상태
ssh redis-master-01
redis-cli info memory
redis-cli info stats
redis-cli ping

# 5. GPU 상태
ssh gpu-cluster-01
nvidia-smi
watch -n 1 nvidia-smi  # 실시간 모니터링

# 6. Disk 사용량
df -h
du -sh /var/log/* | sort -rh | head -10

# 7. 메모리 사용량
free -h
ps aux --sort=-%mem | head -20

# 8. CPU 사용량
top -bn1 | head -20
htop
```

## 2.4 장애 유형별 대응

### 🔥 A. API 전체 다운 (P1)

**증상:**
- 모든 Zone API가 5xx 에러 반환
- Health check 실패
- Nginx 502/504 에러

**원인 후보:**

1. DB 커넥션 풀 고갈
2. Redis 장애
3. Reverse Proxy 실패(SSL/Cert)
4. FastAPI crash
5. 서버 OOM(Killed)

**조치 절차:**

```bash
# STEP 1: Nginx 재시작
ssh edge-proxy-01
systemctl restart nginx
systemctl status nginx

# STEP 2: Backend API 재시작
ssh backend-api-01
systemctl restart backend-api
journalctl -u backend-api -n 100 --no-pager

# STEP 3: PgBouncer 재시작
ssh db-primary-01
systemctl restart pgbouncer
psql -p 6432 -U postgres -c "SHOW POOLS;"

# STEP 4: DB 연결 확인
psql -U postgres -d dreamseed -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# STEP 5: Redis 확인
ssh redis-master-01
redis-cli ping
redis-cli info stats

# STEP 6: GPU 서버 과부하 여부 확인
ssh gpu-cluster-01
nvidia-smi
systemctl status vllm-server

# STEP 7: 로그 분석
tail -f /var/log/nginx/error.log
tail -f /var/log/backend-api/app.log
```

**복구 확인:**

```bash
# Health check
for zone in univprepai collegeprepai skillprepai; do
  echo "Testing $zone..."
  curl -I https://api.$zone.com/health
done
```

**에스컬레이션:**

- 10분 내 복구 실패 시 → Senior SRE 호출
- 20분 내 복구 실패 시 → CTO 호출

---

### 🔥 B. 특정 Zone API 장애 (P2)

**증상:**
- 특정 Zone만 장애 (예: api.my-ktube.ai)
- 다른 Zone은 정상

**원인 후보:**

1. 해당 Zone의 Backend 컨테이너 다운
2. Nginx upstream 설정 오류
3. Cloudflare Routing 문제
4. 도메인 인증서 갱신 실패

**조치 절차:**

```bash
# STEP 1: 해당 서버의 systemd 확인
ssh backend-api-01
systemctl status backend-api-kzone
journalctl -u backend-api-kzone -n 200 --no-pager

# STEP 2: 에러로그 (Loki) 확인
# Grafana → Loki → Query: {zone="kzone"} |= "error"

# STEP 3: Cloudflare Routing 확인
curl -I https://api.my-ktube.ai/health

# STEP 4: 도메인 인증서 갱신 문제 여부
openssl s_client -connect api.my-ktube.ai:443 -servername api.my-ktube.ai

# STEP 5: Nginx 설정 확인
ssh edge-proxy-01
nginx -t
grep "my-ktube.ai" /etc/nginx/sites-enabled/*

# STEP 6: Docker 컨테이너 재시작 (Docker 환경일 경우)
docker restart backend-api-kzone
docker logs backend-api-kzone --tail 100
```

---

### 🔥 C. AI Inference 지연 (Whisper / vLLM / PoseNet) (P3)

**증상:**
- AI Tutor 응답 시간 > 5초
- Whisper 음성 인식 지연
- PoseNet 자세 분석 타임아웃

**원인 후보:**

1. GPU 메모리 부족
2. GPU 온도 과열
3. 큐 backlog 증가 (Redis Streams)
4. 모델 로딩 실패
5. Batch size 과다

**조치 절차:**

```bash
# STEP 1: GPU 메모리/온도 확인
ssh gpu-cluster-01
nvidia-smi
# 확인 사항:
# - GPU Memory Used > 90% → 메모리 부족
# - GPU Temp > 85°C → 과열
# - GPU Utilization < 10% → 모델 미작동

# STEP 2: vLLM 서버 로그 확인
journalctl -u vllm-server -n 200 --no-pager
tail -f /var/log/vllm/inference.log

# STEP 3: Whisper batch size 축소
# /etc/systemd/system/whisper-server.service
# ExecStart=/usr/bin/python whisper_server.py --batch-size 4
systemctl restart whisper-server

# STEP 4: 큐 backlog 확인 (Redis Streams)
ssh redis-master-01
redis-cli XLEN ai:llm:queue
redis-cli XLEN ai:whisper:queue
redis-cli XLEN ai:posenet:queue

# STEP 5: GPU failover → Cloud GPU로 전환
# AI Router 설정 변경
redis-cli SET ai:engine:llm:fallback "cloud"
# 또는 환경 변수 변경
export AI_ENGINE_FALLBACK=cloud
systemctl restart backend-api

# STEP 6: 모델 재로딩
curl -X POST http://localhost:8100/api/reload-model
```

**성능 튜닝:**

```python
# vLLM 최적화 설정
vllm serve Qwen/Qwen2.5-32B-Instruct \
  --tensor-parallel-size 2 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.85 \  # 90% → 85%로 줄임
  --dtype bfloat16 \
  --max-num-seqs 32 \  # batch size 축소
  --disable-log-requests
```

---

### 🔥 D. DB 오래 걸리는 쿼리 (Slow Query) (P3)

**증상:**
- API 응답 시간 증가 (p95 > 2s)
- DB CPU 사용률 > 80%
- pg_stat_activity에 long-running 쿼리 발견

**원인 후보:**

1. 인덱스 누락
2. N+1 쿼리 문제
3. 페이징 없는 대용량 SELECT
4. 통계 정보 오래됨 (ANALYZE 필요)
5. Lock 대기 (Deadlock)

**조치 절차:**

```bash
# STEP 1: pg_stat_activity 확인
ssh db-primary-01
psql -U postgres -d dreamseed << EOF
SELECT 
  pid, 
  now() - query_start AS duration, 
  state, 
  query 
FROM pg_stat_activity 
WHERE state != 'idle' 
  AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;
EOF

# STEP 2: 느린 쿼리 Kill (주의!)
# pid 확인 후 kill
psql -U postgres -d dreamseed -c "SELECT pg_terminate_backend(12345);"

# STEP 3: 인덱스 누락 여부 확인
psql -U postgres -d dreamseed << EOF
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE tablename IN ('exam_attempts', 'exam_responses', 'users');
EOF

# STEP 4: ANALYZE 실행 (통계 정보 갱신)
psql -U postgres -d dreamseed -c "ANALYZE;"

# STEP 5: 쿼리 실행 계획 확인
psql -U postgres -d dreamseed << EOF
EXPLAIN ANALYZE
SELECT * FROM exam_attempts WHERE user_id = 123 AND exam_id = 456;
EOF

# STEP 6: Read Replica로 트래픽 분산 (심각 시)
# Nginx upstream에 replica 추가
upstream db_pool {
    server db-primary-01:5432 weight=2;
    server db-replica-01:5432 weight=1;
}
```

**인덱스 추가 예시:**

```sql
-- exam_attempts 테이블 인덱스
CREATE INDEX CONCURRENTLY idx_exam_attempts_user_exam 
ON exam_attempts(user_id, exam_id);

-- exam_responses 테이블 인덱스
CREATE INDEX CONCURRENTLY idx_exam_responses_attempt 
ON exam_responses(attempt_id);

-- 복합 인덱스 (zone_id + org_id)
CREATE INDEX CONCURRENTLY idx_users_zone_org 
ON users(zone_id, org_id);
```

---

### 🔥 E. Redis 장애 / 세션 대량 삭제 (P2)

**증상:**
- 모든 사용자 로그아웃
- CAT 시험 상태 손실
- Rate Limit 동작 안 함

**원인 후보:**

1. Redis 프로세스 다운
2. 메모리 부족 (OOM)
3. RDB/AOF 손상
4. Sentinel failover 실패

**조치 절차:**

```bash
# STEP 1: Redis ping 확인
ssh redis-master-01
redis-cli ping
# 응답 없으면 → 재시작

# STEP 2: 메모리 부족 여부 확인
redis-cli info memory
# used_memory_human 확인
# maxmemory 설정 확인

# STEP 3: RDB/AOF 손상 여부 확인
tail -f /var/log/redis/redis-server.log
# "Bad file format" → RDB 손상

# STEP 4: Redis 재시작
systemctl restart redis-server
systemctl status redis-server

# STEP 5: Sentinel/Cluster failover (클러스터 구성 시)
redis-cli -p 26379 sentinel masters
redis-cli -p 26379 sentinel failover mymaster

# STEP 6: 데이터 복구 (백업에서)
# RDB 파일 복원
cp /backup/dump.rdb /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb
systemctl restart redis-server
```

**메모리 부족 해결:**

```bash
# maxmemory 증가
redis-cli CONFIG SET maxmemory 8gb

# Eviction policy 확인
redis-cli CONFIG GET maxmemory-policy
# allkeys-lru 권장
```

---

### 🔥 F. Nginx / Reverse Proxy 장애 (P1)

**증상:**
- 502 Bad Gateway
- 504 Gateway Timeout
- SSL Handshake 실패

**원인 후보:**

1. Backend upstream 다운
2. Nginx worker 부족
3. SSL 인증서 만료
4. 파일 디스크립터 부족

**조치 절차:**

```bash
# STEP 1: Nginx 설정 테스트
ssh edge-proxy-01
nginx -t
# 설정 오류 있으면 수정 후 reload

# STEP 2: Nginx 재시작
systemctl restart nginx
systemctl status nginx

# STEP 3: Backend upstream 확인
curl -I http://10.0.2.10:8000/health

# STEP 4: SSL 인증서 확인
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout | grep "Not After"

# STEP 5: 파일 디스크립터 확인
ulimit -n
# 1024 미만이면 증가 필요
# /etc/security/limits.conf
nginx soft nofile 65535
nginx hard nofile 65535

# STEP 6: Nginx worker 설정 확인
# /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 2048;
```

---

### 🔥 G. Disk Full (P2)

**증상:**
- "No space left on device" 에러
- 로그 쓰기 실패
- 백업 실패

**조치 절차:**

```bash
# STEP 1: 디스크 사용량 확인
df -h
du -sh /var/log/* | sort -rh | head -10

# STEP 2: 대용량 로그 파일 삭제
# 주의: 현재 쓰고 있는 로그는 truncate 사용
truncate -s 0 /var/log/nginx/access.log

# STEP 3: Docker 이미지/컨테이너 정리
docker system prune -a --volumes -f

# STEP 4: Journalctl 로그 정리
journalctl --vacuum-time=7d
journalctl --vacuum-size=1G

# STEP 5: 임시 파일 정리
rm -rf /tmp/*
rm -rf /var/tmp/*

# STEP 6: 디스크 확장 (근본 해결)
# AWS EBS 볼륨 확장 또는 추가 디스크 마운트
```

---

## 2.5 장애 보고서 템플릿 (Post-Mortem)

```markdown
# Incident Post-Mortem

**Incident ID:** INC-2025-11-21-001  
**Date:** 2025-11-21  
**Duration:** 45분 (10:15 - 11:00 UTC)  
**Severity:** P2  
**Impacted Services:** api.univprepai.com  

## Summary

UnivPrepAI Zone의 API가 45분간 502 에러 반환.

## Timeline

- 10:15 - AlertManager가 Slack 알림 전송
- 10:17 - SRE 엔지니어 조사 시작
- 10:25 - Backend API 컨테이너 메모리 부족 확인
- 10:30 - 컨테이너 재시작
- 10:35 - 서비스 정상화
- 11:00 - 모니터링 확인 완료

## Root Cause

Backend API 컨테이너가 메모리 누수로 인해 OOM Killed 되었음.  
원인: SQLAlchemy 세션 미정리 → 메모리 누적.

## Impact

- 영향받은 사용자: 약 200명
- 실패한 API 요청: 약 3,000건
- 손실된 시험 세션: 5건 (복구 완료)

## Action Items

1. [ ] SQLAlchemy 세션 자동 정리 코드 추가
2. [ ] 메모리 사용량 알람 추가 (> 80%)
3. [ ] Backend API 컨테이너 메모리 제한 증가 (4GB → 8GB)
4. [ ] 주간 메모리 프로파일링 추가

## Prevention

- 메모리 누수 탐지를 위한 주간 리뷰
- Pre-production 환경에서 부하 테스트 강화
```

---

# 🚀 3. 배포 전략 (Deployment Strategy)

MegaCity는 GitHub Actions 기반 CI/CD를 사용합니다.

## 3.1 배포 종류

```
Rolling Deployment (FastAPI, Next.js)
  → 점진적으로 서버 하나씩 업데이트

Blue-Green Deployment (AI Engines)
  → 새 버전 배포 후 트래픽 전환

Canary Deployment (~5% 테스트)
  → 5% 트래픽으로 신규 버전 검증
```

## 3.2 배포 파이프라인 (GitHub Actions)

### Backend API 배포

```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend API

on:
  push:
    branches: ["main"]
    paths: ["backend/**"]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: |
          docker build -t registry.dreamseedai.com/backend:${{ github.sha }} backend/
          docker push registry.dreamseedai.com/backend:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          ssh ubuntu@backend-api-01 << 'EOF'
            docker pull registry.dreamseedai.com/backend:${{ github.sha }}
            docker tag registry.dreamseedai.com/backend:${{ github.sha }} backend:latest
            docker stop backend-api && docker rm backend-api
            docker run -d --name backend-api \
              --restart unless-stopped \
              -p 8000:8000 \
              -e DATABASE_URL=${{ secrets.DATABASE_URL }} \
              backend:latest
          EOF
      
      - name: Health check
        run: |
          sleep 10
          curl -f https://api.dreamseedai.com/health || exit 1
```

### AI Engine 배포 (Blue-Green)

```yaml
# .github/workflows/deploy-ai-engine.yml
name: Deploy AI Engine (Blue-Green)

on:
  workflow_dispatch:
    inputs:
      engine:
        description: 'AI Engine (vllm/whisper/posenet)'
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Green environment
        run: |
          ssh ubuntu@gpu-cluster-01 << 'EOF'
            docker pull registry.dreamseedai.com/${{ inputs.engine }}:latest
            docker run -d --name ${{ inputs.engine }}-green \
              --gpus all \
              -p 8101:8100 \
              registry.dreamseedai.com/${{ inputs.engine }}:latest
          EOF
      
      - name: Health check
        run: |
          sleep 30
          curl -f http://gpu-cluster-01:8101/health || exit 1
      
      - name: Switch traffic (Blue → Green)
        run: |
          # Nginx upstream 변경
          ssh ubuntu@edge-proxy-01 << 'EOF'
            sed -i 's/8100/8101/g' /etc/nginx/sites-enabled/ai-engine
            nginx -t && systemctl reload nginx
          EOF
      
      - name: Stop Blue environment
        run: |
          ssh ubuntu@gpu-cluster-01 << 'EOF'
            docker stop ${{ inputs.engine }}-blue
            docker rm ${{ inputs.engine }}-blue
            docker rename ${{ inputs.engine }}-green ${{ inputs.engine }}-blue
          EOF
```

## 3.3 롤백 전략

```bash
# STEP 1: 이전 버전 확인
docker images | grep backend

# STEP 2: 이전 버전으로 롤백
docker pull registry.dreamseedai.com/backend:abc123
docker stop backend-api
docker rm backend-api
docker run -d --name backend-api backend:abc123

# STEP 3: Health check
curl -f https://api.dreamseedai.com/health

# STEP 4: DB 롤백 (주의! 데이터 손실 가능)
# Alembic downgrade
cd backend
alembic downgrade -1
```

## 3.4 Zero-Downtime 배포 원칙

```nginx
# Nginx upstream 다중 노드
upstream backend_api {
    server backend-api-01:8000 max_fails=3 fail_timeout=30s;
    server backend-api-02:8000 max_fails=3 fail_timeout=30s;
}

# Health check
location /health {
    proxy_pass http://backend_api;
    proxy_next_upstream error timeout invalid_header http_500;
}
```

## 3.5 배포 체크리스트

### Pre-Deployment

```
□ 테스트 통과 확인 (pytest / jest)
□ DB 마이그레이션 실행 계획 확인
□ 백업 완료 확인
□ Rollback 절차 준비
□ On-call 엔지니어 대기
□ Monitoring Dashboard 열어두기
```

### During Deployment

```
□ Health check 모니터링
□ Error rate 모니터링
□ Latency 모니터링
□ User session 유지 확인
```

### Post-Deployment

```
□ Health check 정상 확인
□ API 기능 테스트 (Smoke Test)
□ Error rate < 1% 확인
□ Latency p95 < 500ms 확인
□ 30분간 모니터링
```

---

# 💾 4. 백업 전략 (Backup Strategy)

## 4.1 PostgreSQL 백업

### Daily Full Backup

```bash
# /etc/cron.daily/pg-backup.sh
#!/bin/bash
DATE=$(date +%F)
BACKUP_DIR=/backup/postgresql

pg_dump -U postgres -Fc dreamseed > $BACKUP_DIR/dreamseed-$DATE.dump

# R2/B2 업로드
aws s3 cp $BACKUP_DIR/dreamseed-$DATE.dump \
  s3://dreamseed-backups/postgresql/$DATE/

# 30일 이상 로컬 백업 삭제
find $BACKUP_DIR -name "*.dump" -mtime +30 -delete
```

### WAL Archive (실시간)

```bash
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://dreamseed-backups/wal/%f'
```

### Retention Policy

```
Daily Backup: 30일 보관
WAL Archive: 30일 보관
Monthly Backup: 1년 보관 (매월 1일)
```

## 4.2 Redis 백업

### RDB Snapshot (6시간마다)

```bash
# redis.conf
save 21600 1  # 6시간마다 1개 이상 변경 시

# 수동 백업
redis-cli BGSAVE
```

### AOF (Append Only File)

```bash
# redis.conf
appendonly yes
appendfsync everysec
```

### Redis 백업 스크립트

```bash
#!/bin/bash
DATE=$(date +%F-%H%M)
BACKUP_DIR=/backup/redis

# RDB 복사
cp /var/lib/redis/dump.rdb $BACKUP_DIR/dump-$DATE.rdb

# S3 업로드
aws s3 cp $BACKUP_DIR/dump-$DATE.rdb \
  s3://dreamseed-backups/redis/$DATE/

# 7일 이상 로컬 백업 삭제
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
```

## 4.3 Object Storage 백업

### R2 → B2 복제

```bash
# /etc/cron.daily/r2-to-b2-sync.sh
#!/bin/bash
rclone sync r2:dreamseed-storage b2:dreamseed-archive \
  --progress \
  --filter "+ /kzone/**" \
  --filter "+ /exams/**" \
  --filter "- *"
```

### Retention Policy

```
R2 (Primary): 30일
B2 (Archive): 90일
Glacier (Cold Storage): 1년+
```

## 4.4 백업 복구 테스트

```bash
# 분기별 복구 테스트 (3개월마다)
# STEP 1: 백업에서 복구
pg_restore -U postgres -d dreamseed_test /backup/dreamseed-2025-11-21.dump

# STEP 2: 데이터 무결성 확인
psql -U postgres -d dreamseed_test -c "SELECT count(*) FROM users;"

# STEP 3: 테스트 DB 삭제
psql -U postgres -c "DROP DATABASE dreamseed_test;"
```

---

# 🚑 5. DR (Disaster Recovery) Plan

## 5.1 DR 정의

**DR (Disaster Recovery)**: 전체 Region 또는 데이터센터가 다운되었을 때 서비스를 복구하는 절차.

## 5.2 DR 목표 (RTO/RPO)

```
RTO (Recovery Time Objective): 서비스 복구 목표 시간 = 4시간
RPO (Recovery Point Objective): 데이터 손실 허용 시간 = 1시간
```

## 5.3 DR 구성 요소

```
Primary Region: Seoul (ap-northeast-2)
Secondary Region: Tokyo (ap-northeast-1)
Backup Region: US-East (us-east-1)
```

### Multi-Region Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Cloudflare Global Load Balancer       │
│                   (Health Check + Failover)             │
└─────────┬──────────────────────────┬────────────────────┘
          │                          │
┌─────────▼──────────┐    ┌─────────▼──────────────────┐
│   Seoul Region     │    │   Tokyo Region (DR)        │
│   Primary          │    │   Standby                  │
│   - Backend API    │    │   - Backend API (Standby)  │
│   - PostgreSQL     │◄───┤   - PostgreSQL (Replica)   │
│   - Redis          │    │   - Redis (Replica)        │
│   - GPU Cluster    │    │   - GPU Cluster (Standby)  │
└────────────────────┘    └────────────────────────────┘
```

## 5.4 DR 절차

### STEP 1 — 장애 선언

```bash
# 장애 조건
- Seoul Region 전체 네트워크 장애 (5분 이상)
- PostgreSQL Primary 복구 불가능
- 데이터센터 물리적 재해 (화재, 지진, 침수)
```

### STEP 2 — Domain Failover (Cloudflare)

```bash
# Cloudflare Load Balancer 설정
# Primary Pool: Seoul Region
# Secondary Pool: Tokyo Region

# Health Check 실패 시 자동 Failover
# 또는 수동 Failover
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/load_balancers/{lb_id}" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -d '{
    "default_pools": ["tokyo-pool"]
  }'
```

### STEP 3 — DB 복구 (PITR - Point-in-Time Recovery)

```bash
# STEP 3.1: PostgreSQL Replica를 Primary로 승격
ssh ubuntu@tokyo-db-01
psql -U postgres -c "SELECT pg_promote();"

# STEP 3.2: WAL Archive에서 최신 데이터 복구
aws s3 sync s3://dreamseed-backups/wal/ /var/lib/postgresql/wal/
pg_ctl start -D /var/lib/postgresql/data

# STEP 3.3: 데이터 무결성 확인
psql -U postgres -d dreamseed -c "SELECT count(*) FROM users;"
```

### STEP 4 — AI Cluster 재가동

```bash
# GPU 클러스터 시작
ssh ubuntu@tokyo-gpu-01
systemctl start vllm-server
systemctl start whisper-server
systemctl start posenet-server

# 모델 로딩 확인 (5-10분 소요)
curl http://tokyo-gpu-01:8100/health
```

### STEP 5 — 서비스 정상화 확인

```bash
# Health check
curl -I https://api.dreamseedai.com/health

# Smoke test
curl -X POST https://api.dreamseedai.com/api/v1/ai-tutor \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt": "test"}'

# 모니터링 확인
# Grafana → Tokyo Region Dashboard
```

### STEP 6 — 사용자 공지

```
고객님께 알려드립니다.

일시적인 시스템 장애로 인해 DR 절차를 진행하였으며,
현재 서비스는 정상화되었습니다.

일부 데이터 지연이 있을 수 있으나 순차적으로 복구 중입니다.

불편을 드려 죄송합니다.
- DreamSeedAI 팀
```

## 5.5 DR 복구 테스트 (연 2회)

```bash
# DR 테스트 시나리오
# 1. Primary Region 인위적 중단
# 2. Failover 실행
# 3. Tokyo Region으로 트래픽 전환
# 4. 서비스 정상 동작 확인
# 5. Primary Region 복구
# 6. Failback 실행
```

---

# 🔎 6. Observability 연동

운영 중 발생하는 모든 문제는 Observability Stack으로 트래킹.

## 6.1 Prometheus Alerts

```yaml
# /etc/prometheus/rules/alerts.yml
groups:
  - name: api_alerts
    rules:
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API p95 latency > 2s"
      
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API error rate > 5%"
      
      - alert: HighGPUTemperature
        expr: nvidia_gpu_temperature_celsius > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU temperature > 85°C"
      
      - alert: HighDBConnections
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "DB connections > 90%"
```

## 6.2 Grafana Dashboards

### Dashboard 1: API Latency

```
- p50/p95/p99 latency (Zone별)
- Request rate (req/s)
- Error rate (%)
- Top 10 slow endpoints
```

### Dashboard 2: DB Health

```
- Active connections
- Slow queries
- Cache hit ratio
- Replication lag
```

### Dashboard 3: AI Cluster Performance

```
- GPU utilization (%)
- GPU memory used (GB)
- GPU temperature (°C)
- Inference latency (LLM/Whisper/PoseNet)
- Queue backlog (Redis Streams)
```

### Dashboard 4: Redis / Queue Backlog

```
- Memory usage
- Hit rate
- Evicted keys
- Queue length (ai:llm:queue, ai:whisper:queue)
```

## 6.3 Loki Logs

```bash
# Nginx access logs
{job="nginx"} |= "error"

# FastAPI app logs
{job="backend-api"} |= "Exception"

# Whisper/PoseNet AI logs
{job="ai-engine"} |= "OOM"
```

## 6.4 Tempo Distributed Tracing

```python
# OpenTelemetry 계측
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

tracer = trace.get_tracer(__name__)

@app.post("/api/v1/ai-tutor")
async def ai_tutor(request: AITutorRequest):
    with tracer.start_as_current_span("ai_tutor"):
        # DB 조회
        with tracer.start_as_current_span("db_query"):
            user = await get_user(request.user_id)
        
        # AI 추론
        with tracer.start_as_current_span("llm_inference"):
            response = await call_llm(request.prompt)
        
        return response
```

---

# 👥 7. On-call 운영 (SRE)

## 7.1 On-call 규칙

```
Coverage: 24/7
Rotation: 주간(평일) / 야간(주말) 교대
SLA: P1 = 15분, P2 = 30분, P3 = 1시간
Escalation: 30분 내 미해결 시 Senior SRE 호출
```

## 7.2 On-call 도구

- **Slack Alerts**: #alerts 채널
- **Grafana Alerts**: dashboard.dreamseedai.com
- **Cloudflare Alerts**: Email + Webhook
- **PagerDuty** (선택): SMS + 전화 페이징

## 7.3 On-call Rotation

| 주 | 평일 (Mon-Fri) | 주말 (Sat-Sun) |
|----|----------------|----------------|
| 1주차 | 엔지니어 A | 엔지니어 B |
| 2주차 | 엔지니어 B | 엔지니어 C |
| 3주차 | 엔지니어 C | 엔지니어 A |

## 7.4 On-call Playbook

```bash
# 알람 수신 시
1. Slack #alerts 확인
2. Grafana Dashboard 확인
3. 장애 등급 판단 (P1/P2/P3/P4)
4. Runbook 실행
5. #incident-YYYYMMDD-NNN 채널 생성
6. 복구 완료 후 Post-Mortem 작성
```

---

# 🔐 8. Secrets / 인증서 관리

## 8.1 Secrets 관리

### GitHub Secrets

```bash
# GitHub Repository Settings → Secrets
DATABASE_URL
REDIS_URL
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
CLOUDFLARE_API_TOKEN
ENCRYPTION_KEY
```

### Docker Secrets

```bash
# Docker Swarm 또는 Kubernetes Secrets
echo "postgresql://user:pass@host/db" | docker secret create db_url -
```

### OS 환경 변수

```bash
# /etc/environment (주의: 프로세스 재시작 필요)
DATABASE_URL="postgresql://..."
REDIS_URL="redis://..."
```

### Secrets 관리 원칙

```
1. 절대 Git에 커밋하지 않음 (.env → .gitignore)
2. 개발/스테이징/프로덕션 환경 분리
3. 주기적으로 로테이션 (90일)
4. 최소 권한 원칙 (Least Privilege)
```

## 8.2 인증서 (TLS) 관리

### Cloudflare Origin Certificates

```bash
# Cloudflare Dashboard → SSL/TLS → Origin Server
# 15년 유효 인증서 발급
# /etc/nginx/ssl/ 에 저장
```

### Let's Encrypt (자동 갱신)

```bash
# Certbot 설치
apt-get install certbot python3-certbot-nginx

# 인증서 발급
certbot --nginx -d api.dreamseedai.com

# 자동 갱신 (cron)
0 0 1 * * certbot renew --quiet
```

---

# 🛟 9. 운영 체크리스트

## 9.1 Daily (매일)

```
□ Grafana Dashboard 확인 (5분)
  - API latency, Error rate, GPU usage, DB connections

□ Error Rate 모니터링 (< 1%)

□ GPU 메모리 점검 (< 90%)

□ DB connection 수 점검 (< 500)

□ Disk 사용량 점검 (< 80%)
```

## 9.2 Weekly (매주)

```
□ 백업 정상 여부 확인
  - PostgreSQL backup 존재 확인
  - WAL archive 연속성 확인
  - Redis RDB 백업 확인

□ 느린 쿼리 점검 (pg_stat_statements)

□ Redis 메모리 점검 (Eviction 발생 여부)

□ 로그 파일 크기 확인 (> 10GB 시 정리)

□ SSL 인증서 만료일 확인 (< 30일 시 갱신)
```

## 9.3 Monthly (매월)

```
□ 모델 성능 검증
  - LLM 응답 품질 샘플링
  - Whisper 음성 인식 정확도
  - PoseNet 자세 인식 정확도

□ 비용 분석 (AI, CDN, GPU, Cloud)

□ 보안 점검 (WAF 로그, 침입 시도)

□ DR 복구 테스트 (분기 1회)

□ On-call Rotation 업데이트

□ Runbook 업데이트 (새로운 장애 사례 추가)
```

## 9.4 Quarterly (분기별)

```
□ DR 복구 테스트 실행

□ 백업 복구 테스트

□ 보안 취약점 스캔 (Trivy, Snyk)

□ 성능 부하 테스트 (k6, Locust)

□ 인프라 비용 최적화

□ Post-Mortem 리뷰 (지난 분기 장애 분석)
```

---

# 🏁 10. 결론

이 **DevOps Runbook**은 DreamSeedAI MegaCity의 안정성을 유지하기 위한 **운영/장애 대응/배포/DR** 전체 절차를 포함합니다.

MegaCity가 확장될수록 Runbook은 더욱 중요해지며, 이 문서는 향후 SRE 팀의 기반 문서로 사용됩니다.

## 핵심 운영 원칙

1. **Automate Everything**: 반복 작업은 자동화
2. **Monitor Everything**: 모든 메트릭 추적
3. **Document Everything**: 모든 장애는 Post-Mortem
4. **Test Failures**: DR/백업 복구 테스트 정기 실행
5. **Blameless Culture**: 장애는 시스템 개선 기회
6. **On-call Excellence**: 빠른 대응, 명확한 소통
7. **Continuous Improvement**: Runbook 지속 업데이트

---

**문서 완료 - DreamSeedAI MegaCity DevOps Runbook v1.0**
