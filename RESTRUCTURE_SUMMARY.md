# 모노레포 구조화 - 실행 가이드

**작성일**: 2024-11-09  
**상태**: 준비 완료 ✅

---

## 🎯 목표

1. **검색 성능 개선**: 30+ 디렉토리 → 4개 핵심 디렉토리
2. **고립된 파일 제거**: 14개 빈/죽은 디렉토리 아카이브
3. **명확한 구조**: apps / services / shared / ops

---

## 📦 준비 완료 파일

### 1. `.gitignore` (최적화 완료 ✅)
- **이전**: 모든 `.md`, `.sh`, `tools/` 차단
- **이후**: 소스 코드와 문서 추적, 빌드 산출물만 제외
- **백업**: `.gitignore.backup`

### 2. `MONOREPO_RESTRUCTURE_PLAN.md` (상세 계획 ✅)
- 현재 문제점 분석
- 새로운 구조 설계
- 5단계 마이그레이션 계획
- 롤백 방법

### 3. `RESTRUCTURE_EXECUTE.sh` (실행 스크립트 ✅)
- 자동화된 구조화 스크립트
- Dry-run 모드 지원
- Git 히스토리 보존
- 안전한 에러 처리

---

## 🚀 실행 방법

### Step 1: Dry-run 테스트 (필수)
```bash
cd /home/won/projects/dreamseed_monorepo
./RESTRUCTURE_EXECUTE.sh --dry-run
```

**확인 사항:**
- 아카이브될 디렉토리 목록
- 이동될 디렉토리 경로
- 삭제될 파일 목록

### Step 2: 백업 생성 (필수)
```bash
# Git 브랜치 생성
git checkout -b restructure-monorepo

# 현재 상태 커밋
git add .
git commit -m "chore: 구조화 전 스냅샷"

# 원격 백업 (선택)
git push origin restructure-monorepo
```

### Step 3: 실제 실행
```bash
./RESTRUCTURE_EXECUTE.sh
```

**실행 시간**: 약 5-10분

### Step 4: 검증
```bash
# 1. 디렉토리 구조 확인
tree -L 2 -d

# 2. pnpm 워크스페이스 확인
pnpm list --depth 0

# 3. TypeScript 빌드 확인
pnpm build:all

# 4. Git 상태 확인
git status
```

### Step 5: 커밋
```bash
# 변경사항 확인
git diff --stat

# 스테이징
git add .

# 커밋
git commit -m "refactor: 모노레포 구조화

- 고립된 디렉토리 14개 아카이브
- apps/services/shared 구조로 재정리
- .gitignore 최적화
- 검색 성능 개선

Closes #XXX"

# 푸시
git push origin restructure-monorepo
```

---

## 📊 변경 사항 요약

### 아카이브 (14개)
```
❌ adaptive_engine/     → _archive/2024-11-09_adaptive_engine/
❌ admin_front/         → _archive/2024-11-09_admin_front/
❌ dreamseed/           → _archive/2024-11-09_dreamseed/
❌ dsadmin/             → _archive/2024-11-09_dsadmin/
❌ examples/            → _archive/2024-11-09_examples/
❌ frontend/            → _archive/2024-11-09_frontend/
❌ htmlcov/             → _archive/2024-11-09_htmlcov/
❌ mathml_env/          → _archive/2024-11-09_mathml_env/
❌ migrations/          → _archive/2024-11-09_migrations/
❌ monitoring/          → _archive/2024-11-09_monitoring/
❌ r-plumber/           → _archive/2024-11-09_r-plumber/
❌ shiny-admin/         → _archive/2024-11-09_shiny-admin/
❌ tests/               → _archive/2024-11-09_tests/
❌ webtests/            → _archive/2024-11-09_webtests/
```

### 재구성
```
✅ portal_front/        → apps/portal/
✅ portal_front/dashboard/ → apps/teacher-dashboard/
✅ backend/             → services/governance/
✅ apps/seedtest_api/   → services/seedtest-api/
✅ packages/            → _archive/ (빈 디렉토리)
✅ shared-analytics-ui/ → _archive/
```

### 삭제 (오염 파일)
```
🗑️ backend.log (324KB)
🗑️ server.log (309KB)
🗑️ batch_conversion.log
🗑️ dummy.db
🗑️ server.pid
🗑️ question_editor_quill.html
```

---

## 🔄 롤백 방법

### 방법 1: Git 리셋
```bash
git reset --hard HEAD~1
```

### 방법 2: .gitignore 복원
```bash
cp .gitignore.backup .gitignore
```

### 방법 3: 아카이브에서 복원
```bash
# 특정 디렉토리 복원
mv _archive/2024-11-09_adaptive_engine ./adaptive_engine

# 전체 복원
for dir in _archive/2024-11-09_*; do
    dirname=$(basename "$dir" | sed 's/2024-11-09_//')
    mv "$dir" "./$dirname"
done
```

---

## ⚠️ 주의사항

### CI/CD 업데이트 필요
```yaml
# .github/workflows/*.yml
# 이전
- run: cd portal_front && pnpm build

# 이후
- run: cd apps/portal && pnpm build
```

### Import 경로 확인
```typescript
// TypeScript - 자동으로 처리됨 (tsconfig paths)
import { Editor } from '@dreamseed/shared-editor'

// Python - 상대 경로 확인 필요
from services.governance.app import create_app
```

### 문서 링크 업데이트
- `README.md` 내부 링크
- `docs/` 디렉토리 상호 참조
- API 문서 경로

---

## 📈 예상 효과

### 검색 성능
| 항목 | 이전 | 이후 | 개선율 |
|-----|------|------|--------|
| 스캔 디렉토리 | 30+ | 4 | **87% 감소** |
| 검색 시간 | 타임아웃 | 3-5초 | **95% 개선** |
| 인덱싱 시간 | 수분 | 수초 | **90% 개선** |

### 디스크 사용량
| 항목 | 이전 | 이후 | 절감 |
|-----|------|------|------|
| 고립된 디렉토리 | 14개 | 0개 | **100%** |
| 로그 파일 | 633KB | 0KB | **100%** |
| 빈 디렉토리 | 10개 | 0개 | **100%** |

### 개발자 경험
- ✅ 파일 위치 명확
- ✅ 일관된 네이밍
- ✅ 빠른 검색
- ✅ 명확한 책임 분리

---

## 📚 참고 문서

- **상세 계획**: `MONOREPO_RESTRUCTURE_PLAN.md`
- **실행 스크립트**: `RESTRUCTURE_EXECUTE.sh`
- **아카이브 인덱스**: `_archive/README.md` (실행 후 생성)

---

## ✅ 체크리스트

### 실행 전
- [ ] `MONOREPO_RESTRUCTURE_PLAN.md` 읽기
- [ ] Dry-run 테스트 완료
- [ ] Git 브랜치 생성
- [ ] 현재 상태 커밋
- [ ] 팀원에게 알림

### 실행 중
- [ ] `./RESTRUCTURE_EXECUTE.sh` 실행
- [ ] 에러 없이 완료 확인
- [ ] 로그 확인

### 실행 후
- [ ] 디렉토리 구조 확인
- [ ] pnpm 워크스페이스 검증
- [ ] 빌드 테스트
- [ ] Git 커밋
- [ ] PR 생성
- [ ] CI/CD 업데이트
- [ ] 문서 업데이트

---

## 🆘 문제 해결

### Q: "git mv" 실패
```bash
# 일반 mv로 대체 (스크립트가 자동으로 처리)
mv source destination
git add .
```

### Q: pnpm 워크스페이스 에러
```bash
# 캐시 삭제 후 재설치
rm -rf node_modules
rm pnpm-lock.yaml
pnpm install
```

### Q: TypeScript 경로 에러
```bash
# tsconfig 재생성
pnpm build:all --force
```

---

**다음 단계**: Dry-run 테스트 실행
```bash
./RESTRUCTURE_EXECUTE.sh --dry-run
```
