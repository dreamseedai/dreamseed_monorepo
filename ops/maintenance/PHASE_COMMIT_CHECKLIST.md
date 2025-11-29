# Phase 작업 커밋 체크리스트

⚠️ **매 Phase 완료 시 반드시 실행하세요!**

## 📋 체크리스트

### 1️⃣ 작업물 확인
```bash
# Phase N 파일 확인
ls -lh ops/phaseN/*.md
ls -lh ops/phaseN/scripts/*.sh
ls -lh backend/PHASEN_*.md
```

### 2️⃣ Git 상태 확인
```bash
git status
```

### 3️⃣ 강제 추가 (`.gitignore` 우회)
```bash
git add -f ops/phaseN/
git add -f backend/PHASEN_*.md
git add -f ops/maintenance/
```

### 4️⃣ 커밋
```bash
git commit -m "docs: Complete Phase N - [작업 내용 요약]

- ops/phaseN/README.md
- ops/phaseN/scripts/
- backend/PHASEN_COMPLETION_REPORT.md
"
```

### 5️⃣ 푸시 (선택사항)
```bash
git push origin $(git branch --show-current)
```

### 6️⃣ 검증
```bash
# Git에 추적되는지 확인
git ls-files ops/phaseN/ | wc -l

# 실제 파일 개수와 비교
find ops/phaseN -type f | wc -l
```

## 🛡️ 방어 전략

1. **즉시 커밋**: 작업 완료 후 바로 커밋 (늦어도 당일 내)
2. **강제 추가**: `.gitignore`의 `*.md` 규칙 때문에 `-f` 필수
3. **Local History**: VS Code 확장 기능으로 `.history/` 백업 유지
4. **원격 백업**: 중요한 마일스톤은 GitHub에 푸시

## ⚠️ 주의사항

- **절대 하지 말 것**: `git clean -fd` (untracked 파일 삭제)
- **Sparse Checkout**: 비활성화 상태 유지 (`git config core.sparseCheckout` → false)
- **`.gitignore` 규칙**: `*.md`가 있어서 `-f` 플래그 필수

## 📊 현재 상태

```bash
# 전체 Phase 파일 확인
find ops/phase* -type f 2>/dev/null | wc -l

# Git 추적 파일 확인
git ls-files ops/phase* | wc -l
```

## 🔄 복원 방법 (만약 파일이 사라진 경우)

1. `.history/` 폴더 확인:
```bash
find .history/ops/phase* -type f | sort
```

2. 최신 버전 찾기:
```bash
ls -lt .history/ops/phaseN/*.md | head -1
```

3. 복원:
```bash
cp .history/ops/phaseN/FILE_TIMESTAMP.md ops/phaseN/FILE.md
git add -f ops/phaseN/FILE.md
git commit -m "docs: Restore phaseN files from .history"
```

---

**마지막 업데이트**: 2025-11-13  
**작성자**: GitHub Copilot
