# 중요 파일 복구 가이드 (File Recovery Guide)

## 🚨 긴급 상황: 중요 파일이 사라졌을 때

### 1단계: 파일 히스토리 확인
```bash
# 파일이 Git에 있었는지 확인
git log --all --full-history -- "파일경로"

# 예시
git log --all --full-history -- "ops/architecture/MEGACITY_*.md"
```

### 2단계: 복구 커밋 찾기
```bash
# 파일이 추가된 커밋 찾기
git log --all --pretty=format:"%H %ai %s" --name-status -- "ops/architecture/" | grep "^A"

# 파일이 삭제된 커밋 찾기
git log --all --diff-filter=D -- "ops/architecture/"
```

### 3단계: 파일 복구
```bash
# 특정 커밋에서 전체 디렉토리 복구
git checkout <커밋ID> -- ops/architecture/

# 특정 파일만 복구
git checkout <커밋ID> -- ops/architecture/MEGACITY_MASTER_INDEX.md

# 복구 후 확인
ls -lh ops/architecture/
```

### 4단계: 커밋 및 푸시
```bash
# 복구된 파일 스테이징
git add ops/architecture/

# 커밋
git commit -S -m "docs: Restore critical architecture files"

# 푸시
git push
```

## 📋 중요 디렉토리 체크리스트

### 정기 확인 (매주 금요일)
```bash
# 아키텍처 문서
echo "Architecture docs: $(ls -1 ops/architecture/*.md 2>/dev/null | wc -l) files"
# 예상: 47개

# 유지보수 문서
echo "Maintenance docs: $(ls -1 ops/maintenance/*.md 2>/dev/null | wc -l) files"
# 예상: 9개

# Phase 문서
echo "Phase docs: $(find ops/phase* -name "*.md" 2>/dev/null | wc -l) files"
# 예상: 4개 이상

# 구현 문서
echo "Implementation docs: $(find docs/ -name "*.md" 2>/dev/null | wc -l) files"
```

### 브랜치 전환 시 체크
```bash
# 새 브랜치 생성 전
git status
git log --oneline -n 5

# 새 브랜치 생성
git checkout -b feature/새기능

# 중요 디렉토리 존재 확인
ls -d ops/architecture ops/maintenance ops/phase* docs/
```

## 🛡️ 예방 조치

### .gitignore 보호 설정 (이미 적용됨)
```gitignore
# PRIORITY 1: NEVER IGNORE THESE
!ops/
!ops/**
!docs/
!docs/**
```

### 로컬 백업 스크립트
```bash
# ~/backup_important_docs.sh
#!/bin/bash
BACKUP_DIR=~/dreamseed_backups
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

cd /home/won/projects/dreamseed_monorepo
tar -czf $BACKUP_DIR/docs_backup_$DATE.tar.gz \
  ops/architecture/ \
  ops/maintenance/ \
  ops/phase*/ \
  docs/

echo "Backup created: $BACKUP_DIR/docs_backup_$DATE.tar.gz"

# 30일 이상 된 백업 삭제
find $BACKUP_DIR -name "docs_backup_*.tar.gz" -mtime +30 -delete
```

실행 권한:
```bash
chmod +x ~/backup_important_docs.sh
```

주간 자동 백업 (crontab):
```bash
# 매주 금요일 오후 6시
0 18 * * 5 ~/backup_important_docs.sh
```

## 🔍 파일 검증 명령어

### 중요 문서 존재 확인
```bash
# 전체 체크
cat << 'EOF' | bash
echo "=== Critical Files Check ==="
echo "Architecture: $(ls -1 ops/architecture/*.md 2>/dev/null | wc -l)/47"
echo "Maintenance: $(ls -1 ops/maintenance/*.md 2>/dev/null | wc -l)/9+"
echo "Phase docs: $(find ops/phase* -name "*.md" 2>/dev/null | wc -l)/4+"
echo "Implementation: $(find docs/implementation -name "*.md" 2>/dev/null | wc -l)"
echo ""
echo "=== Git Tracking Status ==="
git ls-files ops/architecture/*.md | wc -l
git ls-files ops/maintenance/*.md | wc -l
EOF
```

### 최근 변경 확인
```bash
# 최근 1주일 내 변경된 중요 파일
git log --since="1 week ago" --name-only --pretty=format: -- \
  ops/architecture/ \
  ops/maintenance/ \
  ops/phase*/ \
  docs/ \
  | sort -u
```

## 📞 긴급 복구 사례

### 사례 1: 브랜치 전환 후 디렉토리 통째로 사라짐
```bash
# 문제: ops/architecture/ 디렉토리가 보이지 않음
ls ops/architecture/
# ls: cannot access 'ops/architecture/': No such file or directory

# 해결: Git 로그에서 찾기
git log --all --pretty=format:"%H %ai %s" -- ops/architecture/ | head -1
# 27896050c6d36711eacc31b3559e080c8018f49f 2025-11-28 23:56:53 ...

# 복구
git checkout 27896050 -- ops/architecture/
git add ops/architecture/
git commit -S -m "docs: Restore architecture directory"
git push
```

### 사례 2: 개별 파일 실수로 삭제
```bash
# 문제: CITY_ANALOGY.md 삭제됨
git rm ops/maintenance/CITY_ANALOGY.md  # 실수!

# 해결: 즉시 복구 (커밋 전)
git checkout HEAD -- ops/maintenance/CITY_ANALOGY.md

# 이미 커밋했다면
git log --oneline -- ops/maintenance/CITY_ANALOGY.md
git checkout <이전커밋> -- ops/maintenance/CITY_ANALOGY.md
```

### 사례 3: 여러 파일 동시 복구
```bash
# ops/architecture/ 전체 47개 파일 복구
git checkout 27896050 -- ops/architecture/

# 확인
ls -1 ops/architecture/*.md | wc -l
# 47

# 커밋
git add ops/architecture/
git commit -S -m "docs: Restore 47 MegaCity architecture files"
```

## 📚 참고 자료

- Git 공식 문서: https://git-scm.com/docs/git-checkout
- 파일 복구 튜토리얼: https://git-scm.com/book/en/v2/Git-Basics-Undoing-Things

## ⚠️ 주의사항

1. **Copilot_* 파일**: 개인 노트이므로 Git에서 무시됨 (정상)
2. **.history/ 폴더**: IDE 자동 생성 파일, 무시됨 (정상)
3. **node_modules/, .venv/**: 의존성 폴더, 무시됨 (정상)
4. **ops/, docs/ 하위 .md 파일**: 반드시 추적되어야 함! (중요)

## 🎯 복구 성공 사례 (2025-11-29)

**문제**: PR #82 닫고 새 브랜치(`feature/password-validation-v2`) 생성 시 `ops/architecture/` 디렉토리 전체 누락

**해결**:
```bash
git log --all --pretty=format:"%H %ai %s" --name-status -- ops/architecture/ | head -20
# 27896050에서 발견

git checkout 27896050 -- ops/architecture/
# 47개 파일 복구 완료

git add ops/architecture/
git commit -S -m "docs: Restore MegaCity architecture documentation (47 files)"
git push
```

**결과**: 34,480줄, 약 1MB의 중요 문서 복구 성공 ✅

---

**마지막 업데이트**: 2025-11-29  
**작성자**: DreamSeed DevOps Team  
**버전**: 1.0
