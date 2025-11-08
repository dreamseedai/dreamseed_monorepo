# GCP 비용 알림 설정 가이드

## 1. 예산 설정

GCP Console → 결제 → 예산 및 알림

### 설정:
- 예산 이름: DreamSeed Monthly Budget
- 금액: $200/월
- 알림 임계값:
  - 50% ($100)
  - 80% ($160)
  - 100% ($200)
  - 120% ($240) - 긴급!

### 알림 수신자:
- won@dreamseed.ai
- dev-team@dreamseed.ai

### 조치:
- 100% 도달 시: 스테이징 DB 즉시 중지
- 120% 도달 시: 모든 비프로덕션 리소스 중지

---

## 2. Cloud Monitoring 알림

### CPU 사용률 알림:
- Cloud SQL CPU > 80% (10분 이상)
- → 인스턴스 크기 검토 필요

### 스토리지 알림:
- Cloud Storage > 1TB
- → 오래된 백업 정리

### 네트워크 알림:
- 송신 트래픽 > 100GB/일
- → DDoS/크롤러 확인

---

## 3. 비용 최적화 체크리스트

### 월초 (매월 1일):
- [ ] 지난달 비용 리뷰
- [ ] 서비스별 비용 분석
- [ ] 불필요한 리소스 삭제

### 주간 (매주 금요일):
- [ ] 스테이징 DB 중지 확인
- [ ] 미사용 VM 중지
- [ ] Cloud Storage 정리 (7일 이상)

### 일일:
- [ ] 비용 대시보드 확인 (5분)
- [ ] 이상 비용 감지 시 즉시 조치

---

## 4. 긴급 연락망

비용 폭증 시 연락:
1. DevOps 팀장: +82-10-xxxx-xxxx
2. CTO: +82-10-yyyy-yyyy
3. GCP 지원: support.google.com/cloud

---

## 5. 자동 중지 스크립트

비용 $250 초과 시 자동 실행:
```bash
# 모든 스테이징 리소스 중지
~/projects/dreamseed_monorepo/scripts/emergency-shutdown.sh
```

---

*"$900 사고를 두 번 반복하지 않기 위해"*
