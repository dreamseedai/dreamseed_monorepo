## What & Why
<!-- North Star 지표에 어떤 영향을? (TTFP / 14-day re-test / 전환) -->
<!-- In-Scope 5개 중 어느 항목 강화? -->

**North Star Impact:**
- [ ] TTFP 감소 (Time To First PDF ≤60분)
- [ ] 14일 재시험율 증가 (≥40%)
- [ ] 트라이얼→유료 전환 증가 (≥20%)

**In-Scope Item:** (1~5 중 선택)
- [ ] 1) 튜터 3-스텝 위자드
- [ ] 2) SeedTest 적응 모의
- [ ] 3) Quick Assign Next 10
- [ ] 4) 좌석 기반 결제 (Stripe)
- [ ] 5) 이벤트 로깅

**Description:**
<!-- 변경 사항 간단 설명 (2-3줄) -->

---

## Dev Contract (≤150 lines)

**Files to change:**
```
- path/to/file1.py
- path/to/file2.tsx
```

**Public interfaces:**
```python
# API endpoints or function signatures
def create_exam_session(user_id: str, exam_id: int) -> ExamSession:
    ...
```

**Inputs/Outputs:**
```
Input: { "user_id": "...", "exam_id": 123 }
Output: { "session_id": "...", "status": "ready" }
```

**Telemetry (events):**
```
- wizard_started { tutor_id, timestamp }
- exam_completed { session_id, duration_ms }
- report_generated { session_id, format: "pdf" }
```

**Tests:**
```
- test_exam_session_creation()
- test_report_generation_flow()
```

---

## Screenshots / Demo
<!-- 짧은 캡처 1~2장 또는 GIF -->
<!-- Before/After 비교 권장 -->

---

## Checklist

### V1 Scope Compliance
- [ ] Out-of-Scope에 해당 안 됨 (SSO, 학원관리, 전교대시보드 등)
- [ ] In-Scope 5개 중 하나를 직접 강화
- [ ] 1주 내 출시 가능 (마이그레이션 최소화)

### Implementation
- [ ] 이벤트 로깅 추가 (`wizard_*` / `exam_*` / `report_*`)
- [ ] 새 의존성 추가 없음 (package.json, requirements.txt)
- [ ] OPA/권한 변경 시 테스트 포함
- [ ] 유닛/통합 테스트 추가 또는 기존 테스트 통과

### Quality & Stability
- [ ] API/스크린 테스트 완료
- [ ] 릴리즈 노트 2줄 작성 (튜터 관점 이점)
- [ ] Decision Filter 5개 항목 모두 통과
- [ ] DB 마이그레이션 영향 없음 또는 마이그레이션 포함 (롤백 경로 명시)
- [ ] 보안 영향 검토 (JWT/JWKS/권한/비밀 관리)

---

## Release Notes (튜터 관점)
<!-- 2줄로 튜터가 얻는 이점 설명 -->
```
- [Feature] 튜터가 이제 XX를 YY 방식으로 할 수 있어 TTFP가 ZZ분 단축됩니다.
- [Improvement] 재시험 배정이 자동화되어 튜터 클릭 횟수가 N회 감소합니다.
```

**롤백 방법:**
<!-- 배포 후 문제 발생 시 롤백 절차 -->

---

## Runtime Stability
- 이 PR이 런타임 안정성에 영향이 있나요? 영향 있으면 라벨 `runtime-stability` 추가
- 병합 시, 자동 게시되는 체크리스트 코멘트를 따라 E2E 스모크 테스트를 실행하세요.

### 스모크 테스트 (필수 시)
- [ ] 핵심 경로 1 통과 (예: 로그인→문제풀기→결과)
- [ ] 핵심 경로 2 통과 (예: 업로드→검증→리포트)

---

<!-- 
참고: docs/GUARDRAILS.md
- North Star: TTFP ≤60분, 재시험율 ≥40%, 전환율 ≥20%
- In-Scope: 튜터 위자드, 적응 모의, Quick Assign, 결제, 로깅
- Out-of-Scope: SSO, 학원관리, 전교대시보드, 알고리즘 고도화
- Decision Filter: User/Scope/Simplicity/Telemetry/Cutline
-->
