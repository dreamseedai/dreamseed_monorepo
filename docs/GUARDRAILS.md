# DreamSeed V1 Guardrails — Tutor Only

## North Star (V1 · Tutor)
- 목표: 첫 PDF까지 ≤ **60분** (TTFP - Time To First PDF)
- 14일 내 재시험율 ≥ **40%**
- 트라이얼→유료 전환 ≥ **20%**

## In-Scope (딱 5개)
1) **튜터 3-스텝 위자드**: 목표 → 10문항 자동 배정 → 부모 PDF
2) **SeedTest 적응 모의**: 출제/응시/채점/θ 간단 추정
3) **Quick Assign Next 10**
4) **좌석 기반 결제(Stripe)**: Starter/Pro + 14일 트라이얼
5) **이벤트 로깅**: `wizard_*`, `exam_*`, `report_*` (TTFP 필수)

## Out-of-Scope (V1에서 절대 안 함)
- 전교/학년/학급 집계 대시보드, SSO, 학원 청구/지점, CRM/복잡 결제
- 복잡 권한/워크플로 커스터마이즈, 외부 SIS/SSO 통합
- 엔진/알고리즘 고도화(정확도 미세튜닝), 콘텐츠 대량 확장
- 학원/기관 관리 기능 (academy, organization 대시보드)
- 다중 지점/계층 구조 (multi-branch, school hierarchy)

## Decision Filter (모델이 제안해도 아래 5개 중 1개라도 NO면 보류)
- (User) 튜터가 **TTFP 감소** 또는 **재시험율 증가**에 즉시 기여하나?
- (Scope) 위 **In-Scope 5개** 중 하나를 직접 강화하나?
- (Simplicity) **1주 내** 출시 가능한가? 마이그레이션 필요 없는가?
- (Telemetry) **이벤트 키**가 명확한가? 측정 가능한가?
- (Cutline) Out-of-Scope와 충돌하지 않는가?

## "Dev 계약서" 전제 (Copilot/Cursor 사용 규칙)
- 변경 파일 경로·공개 시그니처·입출력·테스트·이벤트 키를 **150줄 내**로 요약 후 코딩 시작
- 코드 변경은 **지정 파일만**. 새로운 디펜던시는 **금지**
- 45분 타임박스 초과 시 중단하고 이슈로 스코프 재평가

## Definition of Done (모든 PR 공통)
- [ ] 이벤트 로깅(필수 키) 포함
- [ ] API/스크린 스냅샷(짧은 GIF/스크린샷 1장)
- [ ] 릴리즈 노트 2줄 (튜터 관점 이점)
- [ ] OPA 권한 체크 추가/수정 시 테스트 포함

## V1 Cut List (절대 하지 않음)
1. SSO/SAML 통합
2. 학원/지점 관리 기능
3. 전교/학년 집계 대시보드
4. 복잡한 결제/청구 시스템
5. 콘텐츠 대량 확장 (기존 문항 풀로 충분)

## Feature Flag 정책
- V2 기능은 `FEATURE_V2_*` 플래그 뒤에 숨기고 기본 OFF
- 예: `FEATURE_V2_ACADEMY=false`, `FEATURE_V2_SCHOOL_DASHBOARD=false`

## Tech Debt Log
- 이번 버전에 안 하는 개선 아이디어는 `DEBT.md`에 한 줄씩만 기록
- 스코프 욕심 분리 및 V2 백로그 관리용

---

*Last Updated: 2025-10-31*  
*Version: 1.0 - Tutor Only*
