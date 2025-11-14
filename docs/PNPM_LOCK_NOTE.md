# pnpm-lock.yaml 관리 가이드

## 📌 중요 사항

`pnpm-lock.yaml`은 **자동 생성/관리 파일**입니다.

### ✅ 해야 할 일

1. **커밋 필수**: 재현성을 위해 반드시 Git에 커밋
2. **자동 생성**: `pnpm install` 실행 시 자동 생성
3. **버전 관리**: 의존성 변경 시 자동 업데이트

### ❌ 하지 말아야 할 일

1. **수동 편집**: 절대 수동으로 편집하지 마세요
2. **삭제 후 재생성**: 특별한 이유 없이 삭제하지 마세요
3. **무시**: `.gitignore`에 추가하지 마세요

---

## 🚀 사용 방법

### 초기 설정

```bash
# 루트에서 실행
pnpm install

# pnpm-lock.yaml 자동 생성됨
git add pnpm-lock.yaml
git commit -m "chore: add pnpm-lock.yaml"
```

### 의존성 추가

```bash
# 새 패키지 추가
pnpm add react

# pnpm-lock.yaml 자동 업데이트됨
git add pnpm-lock.yaml package.json
git commit -m "chore: add react dependency"
```

### CI/CD

```bash
# frozen-lockfile 사용 (프로덕션)
pnpm install --frozen-lockfile

# lockfile 없이 설치 (개발)
pnpm install --frozen-lockfile=false
```

---

## 🔍 문제 해결

### 문제: lockfile 충돌

**해결**:
```bash
# 충돌 해결 후
pnpm install
git add pnpm-lock.yaml
git commit
```

### 문제: 의존성 불일치

**해결**:
```bash
# lockfile 재생성
rm pnpm-lock.yaml
pnpm install
```

---

**pnpm-lock.yaml은 자동 관리됩니다\!** ✅
