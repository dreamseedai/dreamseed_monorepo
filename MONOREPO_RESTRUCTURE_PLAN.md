# DreamSeed Monorepo 구조화 계획

**작성일**: 2024-11-09  
**목적**: 검색 성능 개선, 고립된 파일 제거, 명확한 디렉토리 구조 확립

---

## 📋 현재 문제점

### 1. 고립된/죽은 디렉토리 (14개)
```
❌ adaptive_engine/     - 빈 디렉토리
❌ admin_front/         - 1개 파일만 존재
❌ dreamseed/           - 빈 디렉토리
❌ dsadmin/             - 빈 디렉토리
❌ examples/            - 빈 디렉토리
❌ frontend/            - 3개 파일만 (npm 캐시)
❌ htmlcov/             - 빈 디렉토리
❌ mathml_env/          - 빈 가상환경
❌ migrations/          - 빈 디렉토리
❌ monitoring/          - 빈 디렉토리
❌ r-plumber/           - 빈 디렉토리
❌ shiny-admin/         - 빈 디렉토리
❌ tests/               - 빈 디렉토리
❌ webtests/            - 빈 디렉토리
```

### 2. 중복/혼란스러운 구조
- `packages/` vs `shared/` - 동일한 목적
- `ops/` vs `monitoring/` - 운영 관련 중복
- `backend/` vs `apps/` - 백엔드 서비스 분산

### 3. 최상위 오염 파일
- `backend.log` (324KB)
- `server.log` (309KB)
- `dummy.db`
- `question_editor_quill.html` (148KB)
- `translator.py/` (디렉토리인데 .py 확장자)

### 4. 과도한 .gitignore 규칙
- 모든 `.md` 파일 차단
- 모든 `.sh` 스크립트 차단
- `tools/` 디렉토리 전체 차단
- 결과: 새 파일 생성 불가, 문서화 불가

---

## 🎯 새로운 표준 구조

```
dreamseed_monorepo/
├── apps/                       # 프론트엔드 애플리케이션
│   ├── portal/                # 메인 포털 (portal_front 이동)
│   ├── admin-dashboard/       # 관리자 대시보드
│   └── teacher-dashboard/     # 교사용 대시보드
│
├── services/                   # 백엔드 서비스 (Python FastAPI)
│   ├── seedtest-api/          # SeedTest API (apps/seedtest_api 이동)
│   ├── governance/            # 거버넌스 서비스 (backend 이동)
│   ├── irt-engine/            # IRT 엔진
│   └── assignment/            # 과제 배정 서비스
│
├── shared/                     # 공용 라이브러리 (pnpm workspace)
│   ├── editor/                # ✅ 에디터 컴포넌트
│   ├── mathml/                # ✅ MathML 변환
│   ├── etl/                   # ✅ ETL 유틸리티
│   ├── schemas/               # ✅ 공용 스키마
│   ├── auth/                  # ✅ 인증 모듈
│   ├── analytics/             # ✅ 분석 모듈
│   ├── llm/                   # ✅ LLM 통합
│   └── monitoring/            # ✅ 모니터링 미들웨어
│
├── ops/                        # 운영 및 인프라
│   ├── k8s/                   # Kubernetes 매니페스트
│   ├── grafana/               # Grafana 대시보드
│   ├── nginx/                 # Nginx 설정
│   ├── helm/                  # Helm 차트
│   └── scripts/               # 운영 스크립트
│
├── docs/                       # 문서
│   ├── architecture/          # 아키텍처 문서
│   ├── api/                   # API 문서
│   ├── deployment/            # 배포 가이드
│   ├── implementation/        # 구현 가이드
│   └── system_layer/          # 시스템 레이어 문서
│
├── tools/                      # 개발 도구
│   ├── vscode-extensions/     # VS Code 확장
│   └── scripts/               # 유틸리티 스크립트
│
├── data/                       # 데이터 (gitignore)
│   ├── datasets/              # 샘플 데이터셋
│   └── fixtures/              # 테스트 픽스처
│
├── _archive/                   # 아카이브 (날짜별 정리)
│   ├── 2024-11-09_adaptive_engine/
│   ├── 2024-11-09_admin_front/
│   ├── 2024-11-09_old_frontend/
│   └── README.md              # 아카이브 인덱스
│
├── .github/                    # GitHub 설정
├── .vscode/                    # VS Code 설정
├── package.json                # 루트 package.json
├── pnpm-workspace.yaml         # pnpm 워크스페이스
├── pyproject.toml              # Python 프로젝트 설정
├── tsconfig.base.json          # TypeScript 기본 설정
└── README.md                   # 메인 README
```

---

## 🚀 마이그레이션 단계

### Phase 1: 준비 (5분)
1. ✅ `.gitignore` 최적화 완료
2. ⏳ 현재 상태 스냅샷 생성
3. ⏳ 아카이브 디렉토리 생성

### Phase 2: 아카이브 (10분)
고립된 디렉토리를 `_archive/`로 이동:
```bash
# 날짜 접두사로 정리
mv adaptive_engine _archive/2024-11-09_adaptive_engine
mv admin_front _archive/2024-11-09_admin_front
mv dreamseed _archive/2024-11-09_dreamseed
mv dsadmin _archive/2024-11-09_dsadmin
mv examples _archive/2024-11-09_examples
mv frontend _archive/2024-11-09_frontend
mv htmlcov _archive/2024-11-09_htmlcov
mv mathml_env _archive/2024-11-09_mathml_env
mv migrations _archive/2024-11-09_migrations
mv monitoring _archive/2024-11-09_monitoring
mv r-plumber _archive/2024-11-09_r-plumber
mv shiny-admin _archive/2024-11-09_shiny-admin
mv tests _archive/2024-11-09_tests
mv webtests _archive/2024-11-09_webtests
mv translator.py _archive/2024-11-09_translator.py
mv Caddyfile _archive/2024-11-09_Caddyfile
mv alembic _archive/2024-11-09_alembic
```

### Phase 3: 구조 재정리 (15분)

#### 3.1 Apps 디렉토리 정리
```bash
# portal_front → apps/portal
mkdir -p apps/portal
mv portal_front/* apps/portal/
rmdir portal_front

# 교사용 대시보드 분리
mkdir -p apps/teacher-dashboard
mv apps/portal/dashboard/* apps/teacher-dashboard/
```

#### 3.2 Services 디렉토리 생성
```bash
mkdir -p services

# backend → services/governance
mv backend services/governance

# apps/seedtest_api → services/seedtest-api
mv apps/seedtest_api services/seedtest-api
```

#### 3.3 Packages 통합
```bash
# packages/ 내용을 shared/로 이동 (중복 제거)
# 현재 packages/는 비어있거나 중복이므로 아카이브
mv packages _archive/2024-11-09_packages
```

#### 3.4 Shared-analytics-ui 통합
```bash
# shared-analytics-ui → apps/analytics-ui 또는 아카이브
mv shared-analytics-ui _archive/2024-11-09_shared-analytics-ui
```

### Phase 4: 설정 파일 업데이트 (10분)

#### 4.1 pnpm-workspace.yaml
```yaml
packages:
  - "apps/*"
  - "services/*"
  - "shared/*"
```

#### 4.2 package.json
```json
{
  "workspaces": [
    "apps/*",
    "services/*",
    "shared/*"
  ]
}
```

#### 4.3 tsconfig.base.json
```json
{
  "compilerOptions": {
    "paths": {
      "@dreamseed/shared-*": ["./shared/*/src"],
      "@dreamseed/apps-*": ["./apps/*/src"],
      "@dreamseed/services-*": ["./services/*/src"]
    }
  }
}
```

### Phase 5: 검증 (10분)
1. pnpm 워크스페이스 검증
2. TypeScript 경로 검증
3. 빌드 테스트
4. 문서 업데이트

---

## 📊 예상 효과

### 검색 성능
- **이전**: 전역 검색 시 30+ 디렉토리 스캔 → 타임아웃
- **이후**: 핵심 4개 디렉토리만 스캔 → 3-5초

### 디스크 사용량
- **이전**: 고립된 디렉토리 및 로그 파일로 인한 낭비
- **이후**: 정리된 구조, 아카이브로 분리

### 개발자 경험
- **이전**: 파일 위치 찾기 어려움, 중복 혼란
- **이후**: 명확한 위치, 일관된 네이밍

---

## ⚠️ 주의사항

1. **Git 히스토리 보존**
   - `git mv` 사용하여 히스토리 유지
   - 대량 이동 시 커밋 분리

2. **CI/CD 파이프라인 업데이트**
   - `.github/workflows/` 경로 수정 필요
   - Docker 빌드 경로 수정

3. **Import 경로 업데이트**
   - TypeScript: `@dreamseed/shared-*` 경로 확인
   - Python: 상대 경로 확인

4. **문서 링크 업데이트**
   - README.md 내부 링크
   - docs/ 디렉토리 상호 참조

---

## 🔄 롤백 계획

문제 발생 시:
```bash
# .gitignore 복원
cp .gitignore.backup .gitignore

# 아카이브에서 복원
mv _archive/2024-11-09_* ./

# Git 리셋
git reset --hard HEAD
```

---

## ✅ 체크리스트

### 실행 전
- [ ] 현재 브랜치 백업
- [ ] 로컬 변경사항 커밋
- [ ] 팀원에게 알림

### 실행 중
- [ ] Phase 1 완료
- [ ] Phase 2 완료
- [ ] Phase 3 완료
- [ ] Phase 4 완료
- [ ] Phase 5 완료

### 실행 후
- [ ] 빌드 성공 확인
- [ ] 테스트 통과 확인
- [ ] 문서 업데이트
- [ ] PR 생성

---

## 📚 참고 문서

- [Monorepo 베스트 프랙티스](https://monorepo.tools/)
- [pnpm Workspace](https://pnpm.io/workspaces)
- [TypeScript Project References](https://www.typescriptlang.org/docs/handbook/project-references.html)

---

**다음 단계**: `RESTRUCTURE_EXECUTE.sh` 스크립트 실행
