# Vite + pnpm 워크스페이스 설정 가이드

완전한 모노레포 설정 (React/Vue 지원)

## 🎯 개요

이 가이드는 DreamSeedAI 모노레포에서 Vite 기반 앱을 설정하는 방법을 설명합니다.

---

## 📁 디렉토리 구조

```
dreamseed_monorepo/
├── pnpm-workspace.yaml        # pnpm 워크스페이스 설정
├── .npmrc                      # pnpm 설정
├── tsconfig.base.json          # 공용 TypeScript 설정
├── tools/
│   └── check-paths.mjs         # 경로 검증 스크립트
├── shared/
│   ├── editor/                 # @dreamseed/shared-editor
│   └── schemas/                # @dreamseed/shared-schemas
└── apps/
    ├── univprepai_project/     # React 앱 예시
    └── school_univprepai/      # Vue 앱 예시
```

---

## 🚀 빠른 시작

### 1. pnpm 설치

```bash
npm install -g pnpm@latest
```

### 2. 의존성 설치

```bash
# 루트에서 실행 (모든 워크스페이스 설치)
pnpm install
```

### 3. 경로 검증

```bash
pnpm run check:paths
```

---

## 📦 Vite 설정 (React)

### vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'
import path from 'node:path'

export default defineConfig({
  server: { host: '0.0.0.0', port: 5178 },
  plugins: [react(), tsconfigPaths()],
  resolve: {
    alias: {
      '@shared/editor': path.resolve(__dirname, '../../shared/editor/src'),
      '@shared/schemas': path.resolve(__dirname, '../../shared/schemas/src'),
    }
  },
  build: {
    sourcemap: true,
    outDir: 'dist'
  }
})
```

---

## 📦 Vite 설정 (Vue)

### vite.config.ts

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tsconfigPaths from 'vite-tsconfig-paths'
import path from 'node:path'

export default defineConfig({
  server: { host: '0.0.0.0', port: 5176 },
  plugins: [vue(), tsconfigPaths()],
  resolve: {
    alias: {
      '@shared/editor': path.resolve(__dirname, '../../shared/editor/src'),
      '@shared/schemas': path.resolve(__dirname, '../../shared/schemas/src'),
    }
  },
  build: { sourcemap: true, outDir: 'dist' }
})
```

---

## 🔧 앱별 tsconfig.json

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@shared/editor/*": ["../../shared/editor/src/*"],
      "@shared/schemas/*": ["../../shared/schemas/src/*"]
    }
  },
  "include": ["src", "vite.config.ts"]
}
```

---

## 📊 경로 검증

### check-paths.mjs

루트 `tsconfig.base.json`의 `paths`가 모든 앱에 반영되었는지 확인:

```bash
pnpm run check:paths
```

**출력 예시**:
```
✅ paths check OK (5 apps checked)
```

**실패 예시**:
```
[paths-missing] my-react-app: "@dreamseed/shared-editor" not mapped
❌ paths check failed (1 missing paths in 5 apps)
```

---

## 🚨 자주 발생하는 이슈

### 문제 1: 경로 충돌

**증상**: Vite alias와 TS paths가 서로 다름

**해결**:
```bash
pnpm run check:paths
```

### 문제 2: 중복 설치

**증상**: 앱별 `node_modules` 생성

**해결**:
```bash
# 루트에서만 설치
pnpm install

# 앱별 node_modules 삭제
rm -rf apps/*/node_modules
```

### 문제 3: 빌드 순서

**증상**: `@dreamseed/shared-editor` import 실패

**해결**:
```bash
# shared 패키지 먼저 빌드
pnpm --filter @dreamseed/shared-editor build
pnpm --filter @dreamseed/shared-schemas build

# 그 다음 앱 빌드
pnpm --filter my-react-app build
```

---

## ✅ 체크리스트

### 초기 설정
- [ ] pnpm 설치
- [ ] 루트에서 `pnpm install` 실행
- [ ] `pnpm run check:paths` 성공

### 앱 생성
- [ ] `package.json` 생성
- [ ] `tsconfig.json` 생성 (루트 상속)
- [ ] `vite.config.ts` 생성
- [ ] `src/` 디렉토리 생성

### 개발
- [ ] `pnpm --filter <app-name> dev` 실행
- [ ] HMR 동작 확인
- [ ] 경로 별칭 동작 확인

### 배포
- [ ] `pnpm --filter <app-name> build` 성공
- [ ] `dist/` 디렉토리 생성 확인
- [ ] CI 통과 확인

---

**완성도 높은 Vite + pnpm 워크스페이스 설정 완료!** 🎉

**즉시 실행**:
```bash
pnpm install
pnpm run check:paths
pnpm --filter <app-name> dev
```
