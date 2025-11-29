# Phase 0: Infrastructure Foundation (인프라 기초 공사)

## 🎯 목표

**비용**: $100-200/month  
**기간**: Week 1-2 (2주)  
**사용자**: 0명 (인프라만 구축)

## 📋 체크리스트

### Week 1: 필수 인프라
- [ ] 인증/RBAC 시스템 (JWT + 4가지 역할)
- [ ] 모니터링 스택 (Prometheus + Grafana)
- [ ] 백업 자동화 (PostgreSQL → Backblaze B2)
- [ ] Rate Limiting (Redis 기반)

### Week 2: 개발 환경
- [ ] CI/CD 파이프라인 (GitHub Actions)
- [ ] 환경 변수 관리 (.env.example)
- [ ] 로컬 개발 환경 docker-compose
- [ ] 기본 헬스체크 엔드포인트

## 🏗️ 디렉토리 구조

```
ops/phase0/
├── README.md                    # 이 파일
├── scripts/                     # 설치 및 운영 스크립트
│   ├── setup_auth.sh           # 인증 시스템 설정
│   ├── setup_monitoring.sh     # 모니터링 스택 배포
│   ├── setup_backup.sh         # 백업 자동화 설정
│   ├── setup_ratelimit.sh      # Rate Limiter 설정
│   └── deploy_phase0.sh        # 전체 Phase 0 배포
├── configs/                     # 설정 파일
│   ├── auth/                   # 인증 관련 설정
│   ├── monitoring/             # Prometheus/Grafana 설정
│   ├── backup/                 # 백업 스크립트 및 설정
│   └── ratelimit/              # Rate Limiting 설정
└── monitoring/                  # 모니터링 대시보드 및 알림
    ├── dashboards/             # Grafana 대시보드 JSON
    └── alerts/                 # Prometheus 알림 규칙
```

## 🚀 빠른 시작

### 1. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 값 입력
```

### 2. Phase 0 전체 배포
```bash
cd ops/phase0/scripts
chmod +x *.sh
./deploy_phase0.sh
```

### 3. 상태 확인
```bash
# 모니터링 대시보드
open http://localhost:3000  # Grafana (admin/admin)

# Prometheus
open http://localhost:9090

# 헬스체크
curl http://localhost:8000/health
```

## 📊 검증 기준

Phase 0 완료 조건:
1. ✅ 모든 서비스 헬스체크 통과
2. ✅ Grafana에서 모든 메트릭 수집 확인
3. ✅ PostgreSQL 백업이 B2에 업로드 완료
4. ✅ Rate Limiter 101번째 요청 차단 확인
5. ✅ GitHub Actions CI 빌드 성공

## 💰 예상 비용

| 항목 | 비용 | 설명 |
|------|------|------|
| Cloudflare Pro | $20/month | DNS + CDN |
| Backblaze B2 | $5/month | 백업 저장소 (50GB) |
| 전력 (로컬 서버) | $50/month | 400W × 24h × $0.12/kWh |
| 예비 (모니터링 등) | $25/month | 기타 |
| **합계** | **$100/month** | Phase 0 |

## 🔗 관련 문서

- [ARCHITECTURE_MASTERPLAN.md](../maintenance/ARCHITECTURE_MASTERPLAN.md)
- [SCALING_STRATEGY.md](../maintenance/SCALING_STRATEGY.md)
- [DISASTER_RECOVERY.md](../maintenance/DISASTER_RECOVERY.md)

## 📞 문제 발생 시

1. 로그 확인: `docker-compose logs -f [service-name]`
2. 헬스체크: `./scripts/healthcheck.sh`
3. 롤백: `./scripts/rollback_phase0.sh`

---
**다음 단계**: Phase 0 완료 후 → [Phase 1: MVP Launch](../phase1/README.md)
