# Tech Debt Log (V1 → V2)

## Purpose
V1에서 의도적으로 하지 않는 개선 아이디어 및 V2 백로그를 한 줄씩 기록합니다.
**욕심 분리** 및 스코프 관리용.

---

## Infrastructure
- [ ] CloudWatch Alarms 고도화 (현재: 기본 메트릭만)
- [ ] Multi-region 배포 (현재: 단일 리전)
- [ ] Kubernetes auto-scaling 정책 최적화

## Authentication & Authorization
- [ ] SSO/SAML 통합 (Google Workspace, Azure AD)
- [ ] Fine-grained RBAC (현재: teacher/student/admin 3-tier)
- [ ] API rate limiting per user tier

## Analytics & Reporting
- [ ] 전교/학년 집계 대시보드
- [ ] 학급별 성취도 비교 리포트
- [ ] 장기 추세 분석 (6개월+)

## Academy/Organization Features
- [ ] 학원 지점 관리 (multi-branch)
- [ ] 학원별 커스텀 브랜딩
- [ ] 학원 청구/정산 시스템
- [ ] 조직 계층 구조 (organization hierarchy)

## IRT & Adaptive Engine
- [ ] IRT 모델 정확도 미세 튜닝 (현재: 2PL/3PL 기본)
- [ ] Bayesian Knowledge Tracing 통합
- [ ] Multi-dimensional IRT (MIRT)
- [ ] Real-time theta adjustment during exam

## Content & Item Management
- [ ] 대량 문항 임포트 (CSV/Excel)
- [ ] 문항 난이도 자동 캘리브레이션
- [ ] 콘텐츠 버전 관리 시스템
- [ ] 문항 추천 엔진 (collaborative filtering)

## Payment & Billing
- [ ] 복잡한 청구 정책 (volume discount, 지점별 집계)
- [ ] Invoice 자동 발송
- [ ] Payment method 다양화 (무통장, 카드 외)

## UX/UI Improvements
- [ ] 튜터 대시보드 커스터마이즈
- [ ] 학생별 학습 경로 시각화
- [ ] Mobile app (React Native)
- [ ] Dark mode

## DevOps & Tooling
- [ ] Feature flag 시스템 (LaunchDarkly 등)
- [ ] A/B testing infrastructure
- [ ] Chaos engineering (resilience testing)

## Data & ML
- [ ] Student behavior prediction (dropout risk)
- [ ] Recommendation system for next exam
- [ ] NLP for auto-tagging items

---

## How to Use
1. V1 작업 중 "이거 하면 좋겠지만 지금은 아니야" → 여기 한 줄 추가
2. 주간 리뷰에서 우선순위 재평가
3. V2 계획 시 이 리스트에서 선택

---

*Last Updated: 2025-10-31*  
*Version: 1.0*
