# 워크스페이스 문제 해결 가이드

## 🔍 "Error while resolving settings from workspace" 해결

### 원인

이 오류는 일반적으로 다음과 같은 경우에 발생합니다:

1. **새로운 의존성 추가 후 IDE 미인식**
2. **TypeScript 설정 변경 후 캐시 문제**
3. **pnpm 워크스페이스 링크 문제**
4. **node_modules 불일치**

---

## ✅ 해결 방법

### 1단계: TypeScript 서버 재시작

**VS Code / Windsurf**:
```
Ctrl+Shift+P (또는 Cmd+Shift+P)
> TypeScript: Restart TS Server
```

### 2단계: pnpm 재설치

```bash
cd /home/won/projects/dreamseed_monorepo

# node_modules 삭제
rm -rf node_modules
rm -rf shared/*/node_modules

# 재설치
pnpm install
```

### 3단계: 빌드 확인

```bash
# shared 패키지 빌드
pnpm --filter @dreamseed/shared-editor build
pnpm --filter @dreamseed/shared-schemas build

# 빌드 결과 확인
ls -la shared/editor/dist/
ls -la shared/schemas/dist/
```

### 4단계: IDE 재시작

완전히 종료 후 재시작:
```bash
# Windsurf 프로세스 종료
pkill -9 windsurf

# 재시작
windsurf /home/won/projects/dreamseed_monorepo
```

---

## 🔧 추가 해결 방법

### TypeScript 캐시 삭제

```bash
# TypeScript 캐시 삭제
rm -rf shared/editor/.tsbuildinfo
rm -rf shared/schemas/.tsbuildinfo

# 재빌드
pnpm build
```

### pnpm 캐시 정리

```bash
# pnpm 캐시 정리
pnpm store prune

# 재설치
pnpm install
```

### Windsurf 설정 초기화

```bash
# Windsurf 설정 백업
cp ~/.config/Windsurf/User/settings.json ~/.config/Windsurf/User/settings.json.bak

# 워크스페이스 설정 삭제
rm -rf /home/won/projects/dreamseed_monorepo/.vscode/.windsurf/

# 재시작
```

---

## 📊 진단 명령어

### 워크스페이스 상태 확인

```bash
# pnpm 워크스페이스 목록
pnpm list -r --depth 0

# 의존성 트리
pnpm list -r @dreamseed/shared-editor
pnpm list -r @dreamseed/shared-schemas

# 링크 확인
ls -la node_modules/@dreamseed/
```

### TypeScript 설정 확인

```bash
# tsconfig 검증
cd shared/editor
npx tsc --noEmit

cd ../schemas
npx tsc --noEmit
```

### 경로 검증

```bash
# paths 동기화 확인
pnpm run check:paths
```

---

## 🚨 자주 발생하는 문제

### 문제 1: "Cannot find module '@dreamseed/shared-editor'"

**원인**: 패키지가 빌드되지 않음

**해결**:
```bash
pnpm --filter @dreamseed/shared-editor build
```

### 문제 2: "Module has no exported member"

**원인**: TypeScript 타입 정의 누락

**해결**:
```bash
# 타입 정의 확인
cat shared/editor/dist/index.d.ts

# 재빌드
pnpm --filter @dreamseed/shared-editor build
```

### 문제 3: peer dependencies 경고

**원인**: React/Vue가 설치되지 않음

**해결**:
```bash
# 루트에 devDependencies로 추가
pnpm add -Dw react @types/react
pnpm add -Dw vue
```

### 문제 4: "strict mode" 오류

**원인**: TypeScript strict 모드 활성화

**해결**:
```json
// shared/editor/tsconfig.json
{
  "compilerOptions": {
    "strict": false,
    "noImplicitAny": false
  }
}
```

---

## ✅ 최종 체크리스트

- [ ] `pnpm install` 성공
- [ ] `pnpm build` 성공
- [ ] `pnpm run check:paths` 성공
- [ ] `shared/editor/dist/` 존재
- [ ] `shared/schemas/dist/` 존재
- [ ] TypeScript 서버 재시작
- [ ] IDE 재시작

---

**워크스페이스 설정 문제 해결 완료\!** ✅

**즉시 실행**:
```bash
# 빠른 해결
pnpm install
pnpm build
# Ctrl+Shift+P > TypeScript: Restart TS Server
```
