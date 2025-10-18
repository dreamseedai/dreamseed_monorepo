# GitHub Projects 보드 템플릿 (DreamSeed)

프로젝트 전 구간을 한 보드에서 추적하기 위한 템플릿입니다. 필요 시 조직/레포 Projects로 동일 구조를 생성하세요.

## 컬럼(views)
- Backlog: 아이디어/요구사항 수집
- Ready: 구현 준비 완료(요건 명확, 범위 확정)
- In Progress: 작업 중(연결된 브랜치/PR 표시)
- Review: PR 리뷰 중(필수 리뷰어/상태 체크 대기)
- Staging: 병합 후 스테이징 검증
- Production: 프로덕션 배포/검증
- Done: 완료(릴리스 노트 반영)
- Blocked: 의존성/이슈로 정지(이유 필수)

## 공통 필드
- Priority: P0/P1/P2/P3
- Size: XS/S/M/L/XL(대략적 난이도/공수)
- Service: api/web/report/infra/docs
- Area: editor/auth/reporting/data-pipeline/ai/observability
- Risk: low/medium/high(보안·가용성·규정)
- Release: vX.Y(릴리스 묶음)
- Milestone: (선택) 캘린더 이벤트와 연계

## 추천 자동화
- PR 연결 시 상태 Review로 이동
- PR 머지(main) 시 Staging → Production으로 자동 이동(환경 승인 시점 기준)
- 라벨 runtime-stability 포함 PR은 체크리스트 워크플로 코멘트 확인 후 Done으로 이동
- Blocked 사유 입력이 없으면 이동 금지

## 권장 필터/뷰
- My items: assignee = @me AND status != Done
- Runtime Stability: label includes runtime-stability
- Release readiness: Release = vX.Y AND status IN (Review, Staging)
- Risk hotlist: Risk = high AND status != Done

## gh CLI(선택)
```bash
# 로그인 후 프로젝트 생성 예시(Org 프로젝트)
# gh auth login
# gh project create --owner mpcstudy --title "DreamSeed Roadmap"
# gh project field-create "DreamSeed Roadmap" --owner mpcstudy --name Priority --data-type SINGLE_SELECT --options P0,P1,P2,P3
```
