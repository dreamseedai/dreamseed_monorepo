# IRT Documentation Index / 문서 인덱스

This index lists all IRT documents with recommended reading order and bilingual summaries.  
이 인덱스는 권장 읽기 순서와 한글 요약을 포함한 모든 IRT 문서를 나열합니다.

---

## Recommended Order / 권장 순서

1. 01_IMPLEMENTATION_REPORT.md — System overview and architecture  
   시스템 전체 개요와 아키텍처
2. 02_CALIBRATION_METHODS_COMPARISON.md — mirt vs brms vs PyMC  
   캘리브레이션 방법 비교 (mirt, brms, PyMC)
3. 03_DRIFT_DETECTION_GUIDE.md — Practical drift/DIF detection  
   드리프트/DIF 실무 가이드
4. 04_API_INTEGRATION_GUIDE.md — Endpoints and patterns  
   API 엔드포인트와 통합 패턴
5. 05_FRONTEND_INTEGRATION_GUIDE.md — React/Next.js wiring  
   프론트엔드(React/Next.js) 통합 가이드
6. 06_DEPLOYMENT_GUIDE.md — Deploy, verify, rollback  
   배포, 검증, 롤백 가이드
7. 07_TROUBLESHOOTING_GUIDE.md — Diagnostics and fixes  
   문제 해결/진단 가이드
8. THRESHOLDS_AND_DIF.md — Drift thresholds & Bayesian DIF  
   드리프트 임계값 & 베이지안 DIF

---

## Document Links / 문서 링크

- 01 Implementation Report  
  English: Overall system accomplishments, components, performance, security, roadmap  
  한국어: 시스템 성과, 구성요소, 성능, 보안, 로드맵 개요  
  Path: `shared/irt/docs/01_IMPLEMENTATION_REPORT.md`  
  GitHub: https://github.com/dreamseedai/dreamseed_monorepo/blob/staging/attempt-view-lock-v1/shared/irt/docs/01_IMPLEMENTATION_REPORT.md

- 02 Calibration Methods Comparison  
  English: When to use mirt/brms/PyMC, examples, diagnostics  
  한국어: 각 방법의 장단점/의사결정 트리/실무 권장  
  Path: `shared/irt/docs/02_CALIBRATION_METHODS_COMPARISON.md`  
  GitHub: https://github.com/dreamseedai/dreamseed_monorepo/blob/staging/attempt-view-lock-v1/shared/irt/docs/02_CALIBRATION_METHODS_COMPARISON.md

- 03 Drift Detection Practical Guide  
  English: Parameter, information, Bayesian, SQL patterns  
  한국어: 임계값 표, SQL 쿼리, 한글 실무 예시  
  Path: `shared/irt/docs/03_DRIFT_DETECTION_GUIDE.md`  
  GitHub: https://github.com/dreamseedai/dreamseed_monorepo/blob/staging/attempt-view-lock-v1/shared/irt/docs/03_DRIFT_DETECTION_GUIDE.md

- 04 API Integration Guide  
  English: Auth, 12+ endpoints, error handling, rate limit  
  한국어: 빠른 시작, 주요 엔드포인트, Python/React 예제  
  Path: `shared/irt/docs/04_API_INTEGRATION_GUIDE.md`  
  GitHub: https://github.com/dreamseedai/dreamseed_monorepo/blob/staging/attempt-view-lock-v1/shared/irt/docs/04_API_INTEGRATION_GUIDE.md

- 05 Frontend Integration Guide  
  English: MonthlyDriftReport usage, i18n, styling  
  한국어: Vite/Next.js 통합, 커스텀 테마, 문제 해결  
  Path: `shared/irt/docs/05_FRONTEND_INTEGRATION_GUIDE.md`  
  GitHub: https://github.com/dreamseedai/dreamseed_monorepo/blob/staging/attempt-view-lock-v1/shared/irt/docs/05_FRONTEND_INTEGRATION_GUIDE.md

- 06 Deployment Guide  ️
  English: DB migration, Docker/K8s/SystemD, verify/rollback  
  한국어: 배포 체크리스트/한글 요약  
  Path: `shared/irt/docs/06_DEPLOYMENT_GUIDE.md`  
  GitHub: https://github.com/dreamseedai/dreamseed_monorepo/blob/staging/attempt-view-lock-v1/shared/irt/docs/06_DEPLOYMENT_GUIDE.md

- 07 Troubleshooting Guide  
  English: Quick flow, known errors, platform-specific fixes  
  한국어: 한글 빠른 진단, 자주 발생 문제  
  Path: `shared/irt/docs/07_TROUBLESHOOTING_GUIDE.md`  
  GitHub: https://github.com/dreamseedai/dreamseed_monorepo/blob/staging/attempt-view-lock-v1/shared/irt/docs/07_TROUBLESHOOTING_GUIDE.md

- Drift Thresholds and DIF  
  English: |Δb|/|Δa|/Δc thresholds, Bayesian DIF, SQL  
  한국어: 임계값/한글 요약 포함  
  Path: `shared/irt/docs/THRESHOLDS_AND_DIF.md`  
  GitHub: https://github.com/dreamseedai/dreamseed_monorepo/blob/staging/attempt-view-lock-v1/shared/irt/docs/THRESHOLDS_AND_DIF.md

---

## How to Use / 활용 방법

- Engineers: Start from 01 → 04/05 to integrate API/UI, then 06 to deploy  
  엔지니어: 01부터 읽고 API/UI 통합(04/05) 후 06으로 배포 진행
- Data Scientists: 02 → 03 with Bayesian DIF, then 01 for architecture  
  데이터 사이언티스트: 02/03 중심으로, 01로 전체 맥락 파악
- DevOps: 06 (deploy), 07 (troubleshoot), infra/nginx and systemd templates  
  데브옵스: 06 배포/07 문제해결, infra/nginx & systemd 템플릿 참조

---

## Related Locations / 관련 경로

- Frontend component: `shared/frontend/irt/MonthlyDriftReport.tsx`
- SystemD templates: `infra/systemd/`
- Nginx templates: `infra/nginx/`
- Migration file: `apps/seedtest_api/alembic/versions/20251105_1400_shared_irt_init.py`

---

Maintainers / 문의: DreamSeed AI Team  
Last Updated / 최종 업데이트: 2025-11-05
