# GitHub 조직/레포 설정 체크리스트 (DreamSeed Monorepo)

이 문서는 “개발 → 검토 → 배포 → 운영 → 거버넌스” 전 구간에서 GitHub를 일관되고 안전하게 사용하기 위한 체크리스트입니다. mpcstudy 조직과 dreamseed_monorepo 레포에 맞춰 작성되었습니다.

## 1) 조직(Organization) 보안·권한
- [ ] 모든 멤버 2FA 필수(Require two-factor authentication)
- [ ] (Enterprise 사용 시) SSO 설정 및 감사 로그 활성화
- [ ] 기본 레포 권한(Default repository permission): No permission
- [ ] 팀 단위 최소 권한(Write/Read) 부여, 외부 협업자 최소화
- [ ] Dependabot Alerts, Secret Scanning 활성화
- [ ] Actions 정책: Verified authors만 허용 등 신뢰도 높은 액션만 사용

## 2) 레포(main) 브랜치 보호 규칙
- [ ] Require a pull request before merging
  - [ ] Required approvals: 1~2 (팀 정책에 맞춤)
  - [ ] Dismiss stale approvals on new commits
  - [ ] Require review from Code Owners (CODEOWNERS 사용 시)
- [ ] Require status checks to pass before merging (필수 체크 선택)
  - [ ] Code Quality (flake8/black/isort/mypy/bandit/safety)
  - [ ] Unit Tests
  - [ ] Integration Tests
  - [ ] Docker Build Test
  - [ ] Prepare Deployment (main 전용)
- [ ] Require branches to be up to date before merging (권장)
- [ ] Enforce for admins, No force-push, No branch delete
- [ ] Linear history / Signed commits (선택)

참고: Required status checks 이름은 최소 1회 성공 실행 후 보호 규칙 UI에서 정확히 선택하세요.

## 3) CODEOWNERS(권장)
- [ ] `.github/CODEOWNERS` 추가 예시
  ```
  api/**          @team-backend
  apps/**         @team-backend
  portal_api/**   @team-backend
  portal_front/** @team-frontend
  ops/**          @team-platform
  .github/**      @team-platform
  docs/**         @team-docs
  ```

## 4) Actions 권한 최소화·환경 보호
- [ ] 환경 Environments: `staging`, `production`과 보호 규칙(승인자) 설정
- [ ] Job-level `permissions` 최소화(contents: read, pull-requests: write 등)
- [ ] 써드파티 액션 pin(버전/커밋 SHA), `concurrency`로 중복 실행 방지

## 5) Secrets/Variables 관리
- [ ] Slack Webhook 등 최소 시크릿만 GitHub에 보관
- [ ] 배포 파라미터는 Variables로 관리: `GCP_PROJECT`, `GKE_REGION`, `GKE_CLUSTER`, `KUSTOMIZE_OVERLAY` 등
- [ ] OpenAI/LLM 변수는 필요 시 Variables 사용(민감 항목은 외부 비밀관리)

## 6) OIDC + GCP Workload Identity (키리스)
- [ ] Actions OIDC 활성화, GCP Workload Identity Provider/Pool 구성
- [ ] 최소 권한의 GKE/Artifact Registry 역할을 Service Account에 부여
- [ ] GitHub에는 GCP 키를 저장하지 않음(키리스 원칙)

## 7) Git LFS / 대용량 아티팩트
- [ ] `.gitattributes`에 LFS 추적 확장자 지정(`*.bin *.pt *.pdf *.zip *.mp4` 등)
- [ ] 필요 시 LFS Data packs 구매, 장기 보관은 GCS/S3로 오프로딩 권장

## 8) 운영·가시성
- [ ] Slack 알림(빌드/배포/PR 머지 등) 채널 확인
- [ ] Post-merge 체크리스트 코멘트 워크플로 동작 확인
- [ ] Grafana/Prometheus 대시보드 링크를 릴리스 노트/운영 가이드에 첨부(선택)

---

적용 순서 제안
1) main 보호 규칙 + Required checks 설정
2) Actions 권한 최소화 + 환경 보호 규칙 적용
3) Org Secrets/Repo Variables 정리, Slack 연동
4) OIDC+WI 키리스 배포 점검
5) CODEOWNERS 도입으로 리뷰 플로우 안정화
