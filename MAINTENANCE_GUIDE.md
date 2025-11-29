# 🧹 DreamSeed 모노레포 유지보수 가이드

## 📅 정기 정리 스케줄

### 주간 (매주 월요일)
```bash
# 자동 정리 스크립트 실행
./scripts/weekly-cleanup.sh

# 또는 dry-run으로 먼저 확인
./scripts/weekly-cleanup.sh --dry-run
```

**체크 항목**:
- ✅ 루트 디렉토리 파일 개수 (15개 이하 유지)
- ✅ 로그 파일 정리 (archive/logs-YYYYMM/로 이동)
- ✅ 임시 DB 파일 삭제
- ✅ 캐시 크기 확인 (100MB 초과 시 정리)
- ✅ 빈 디렉토리 확인
- ✅ 대용량 파일 체크 (100MB 이상)

### 월간 (매월 1일)
```bash
# 아카이브 오래된 파일 삭제 (90일 이상)
find archive -type f -mtime +90 -delete

# 캐시 전체 정리
pnpm clean:cache
rm -rf .pytest_cache .mypy_cache .ruff_cache

# 의존성 재설치
pnpm clean && pnpm install
```

### 분기별 (3개월마다)
- 사용하지 않는 디렉토리 점검
- 의존성 업데이트 검토
- 문서 업데이트

---

## 🛠️ 유지보수 스크립트

### 1. 주간 정리 (weekly-cleanup.sh)
```bash
./scripts/weekly-cleanup.sh          # 실제 실행
./scripts/weekly-cleanup.sh --dry-run # 시뮬레이션
```

**기능**:
- 로그 파일 자동 아카이브
- 임시 DB 파일 확인
- 캐시 크기 모니터링
- 빈 디렉토리 탐지
- 대용량 파일 경고

### 2. 루트 파일 정리 (organize-root-files.sh)
```bash
./scripts/organize-root-files.sh
```

**자동 분류**:
- `*STATUS*.md`, `*SUMMARY*.md` → `archive/docs/`
- `*.sh` 스크립트 → `archive/scripts/`
- `pyrightconfig*.json` → `archive/config/`
- `*_report_*.txt` → `archive/reports/`
- `*.log` → `archive/logs-YYYYMM/`

### 3. GitHub Actions (자동화)
```yaml
# .github/workflows/cleanup-check.yml
# 매주 월요일 자동 실행
```

**알림**:
- 루트 파일 10개 초과 시 경고
- 대용량 로그 파일 발견 시 알림
- 정리 리포트 자동 생성

---

## 📂 디렉토리 구조 원칙

### ✅ 루트에 유지해야 할 파일 (최대 15개)
```
docker-compose.yml       # 메인 Docker 설정
package.json            # NPM 루트 설정
package-lock.json       # NPM 의존성
pnpm-lock.yaml         # PNPM 의존성
pnpm-workspace.yaml    # PNPM 워크스페이스
pyproject.toml         # Python 프로젝트 설정
tsconfig.base.json     # TypeScript 베이스 설정
README.md              # 메인 문서
PROJECT_STRUCTURE.md   # 구조 문서
.gitignore             # Git 무시 파일
.env.example           # 환경 변수 예시
```

### 🗂️ Archive 구조
```
archive/
├── docs/              # 상태 문서, 가이드
├── scripts/           # 구버전 스크립트
├── config/            # 구버전 설정 파일
├── reports/           # 분석 리포트
├── logs-YYYYMM/       # 월별 로그 아카이브
└── deprecated/        # 사용 중단 코드
```

### 🚫 아카이브해야 할 파일
- `*STATUS*.md`, `*COMPLETE*.md` (상태 문서)
- `*.log` (로그 파일)
- `*.db` (임시 데이터베이스)
- `*_report_*.txt` (분석 리포트)
- `Dockerfile.*` (Docker 변형 파일)
- `docker-compose.*.yml` (Docker Compose 변형)

---

## 🔍 모니터링 지표

### 건강한 상태
- ✅ 루트 파일: 6-15개
- ✅ 로그 파일: 0개 (모두 아카이브)
- ✅ 임시 DB: 0개
- ✅ 캐시 크기: 각 100MB 이하
- ✅ 아카이브 파일: 200개 이하

### 경고 상태
- ⚠️ 루트 파일: 15-25개
- ⚠️ 로그 파일: 1-5개
- ⚠️ 캐시 크기: 100-500MB
- ⚠️ 아카이브 파일: 200-500개

### 위험 상태
- 🚨 루트 파일: 25개 이상 → **즉시 정리 필요**
- 🚨 로그 파일: 5개 이상 → **로그 로테이션 설정**
- 🚨 캐시 크기: 500MB 이상 → **캐시 삭제**
- 🚨 아카이브 파일: 500개 이상 → **오래된 파일 삭제**

---

## 🚀 빠른 정리 명령어

### 즉시 정리 (1분 이내)
```bash
# 루트 파일 자동 정리
./scripts/organize-root-files.sh

# 로그 삭제
rm -f *.log

# 임시 DB 삭제
rm -f dummy.db test*.db
```

### 캐시 정리 (5분 이내)
```bash
# Python 캐시
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
rm -rf .pytest_cache .mypy_cache .ruff_cache

# Node.js 캐시
pnpm clean:cache
rm -rf node_modules/.cache
```

### 전체 클린 빌드 (15분)
```bash
# 의존성 재설치
pnpm clean && pnpm install

# Python 환경 재생성
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

---

## 📋 체크리스트

### 주간 점검
- [ ] `weekly-cleanup.sh` 실행
- [ ] 루트 파일 개수 확인 (15개 이하)
- [ ] 로그 파일 아카이브
- [ ] GitHub Actions 결과 확인

### 월간 점검
- [ ] 아카이브 90일+ 파일 삭제
- [ ] 캐시 전체 정리
- [ ] 의존성 업데이트 검토
- [ ] 백업 상태 확인

### 분기별 점검
- [ ] 사용하지 않는 디렉토리 아카이브
- [ ] 문서 업데이트 (PROJECT_STRUCTURE.md)
- [ ] 보안 취약점 점검
- [ ] 성능 최적화 검토

---

## 🆘 문제 해결

### "루트 파일이 너무 많습니다"
```bash
# 1. 현재 상태 확인
ls -1 *.{py,sh,md,txt,log,db} 2>/dev/null | wc -l

# 2. 자동 정리
./scripts/organize-root-files.sh

# 3. 수동 확인
ls -lh *.md | head -20
```

### "캐시가 너무 큽니다"
```bash
# 1. 캐시 크기 확인
du -sh .pytest_cache .mypy_cache .ruff_cache node_modules/.cache

# 2. 안전하게 삭제
rm -rf .pytest_cache .mypy_cache .ruff_cache
pnpm clean:cache
```

### "빌드가 실패합니다"
```bash
# 1. 캐시 삭제
pnpm clean:cache

# 2. node_modules 재설치
rm -rf node_modules
pnpm install

# 3. Python 환경 재생성
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

---

## 📚 참고 문서

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 프로젝트 구조
- [.github/workflows/cleanup-check.yml](.github/workflows/cleanup-check.yml) - 자동화 설정
- [scripts/weekly-cleanup.sh](scripts/weekly-cleanup.sh) - 주간 정리 스크립트
- [scripts/organize-root-files.sh](scripts/organize-root-files.sh) - 파일 정리 스크립트

---

**마지막 업데이트**: 2025-11-09  
**담당자**: DreamSeed DevOps Team
