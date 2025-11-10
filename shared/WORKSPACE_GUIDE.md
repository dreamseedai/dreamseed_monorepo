# pnpm 워크스페이스 + TipTap MathJax 렌더러 가이드

완전한 모노레포 설정 (React/Vue 지원)

## 🎯 워크스페이스 구조

```
dreamseed_monorepo/
├── pnpm-workspace.yaml        # pnpm 워크스페이스 설정
├── package.json                # 루트 패키지 (워크스페이스 스크립트)
├── tsconfig.base.json          # 공용 TypeScript 설정
├── shared/
│   ├── editor/                 # @dreamseed/shared-editor
│   │   ├── src/
│   │   │   ├── react/         # React 렌더러
│   │   │   ├── vue/           # Vue 렌더러
│   │   │   ├── mathjaxUtils.ts
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json      # extends ../../tsconfig.base.json
│   ├── schemas/                # @dreamseed/shared-schemas
│   └── mathml/                 # MathML 변환 시스템
├── apps/                       # 프론트엔드 앱
└── services/                   # 백엔드 서비스
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

### 3. 빌드

```bash
# shared/* 패키지만 빌드
pnpm build

# 모든 패키지 빌드
pnpm build:all
```

### 4. 테스트

```bash
# shared/* 패키지만 테스트
pnpm test

# 모든 패키지 테스트
pnpm test:all
```

---

## 📦 패키지 사용법

### React 앱에서 사용

```tsx
import { ReactTipTapRenderer, useMathJaxTypeset } from '@dreamseed/shared-editor'

// 렌더러 사용
function MyComponent() {
  return <ReactTipTapRenderer content={tiptapDoc} />
}

// 훅 사용
function CustomRenderer() {
  const containerRef = useRef<HTMLDivElement>(null)
  useMathJaxTypeset([content], containerRef.current)
  
  return <div ref={containerRef}>{/* ... */}</div>
}
```

### Vue 앱에서 사용

```vue
<script setup lang="ts">
import { VueTipTapRenderer, vMathJax } from '@dreamseed/shared-editor'
</script>

<template>
  <div v-mathjax>
    <VueTipTapRenderer :content="tiptapDoc" />
  </div>
</template>
```

---

## 🔧 워크스페이스 명령어

### 특정 패키지만 빌드

```bash
# shared/editor만 빌드
pnpm --filter @dreamseed/shared-editor build

# shared/schemas만 빌드
pnpm --filter @dreamseed/shared-schemas build
```

### 특정 패키지에 의존성 추가

```bash
# shared/editor에 의존성 추가
pnpm --filter @dreamseed/shared-editor add react

# 루트에 devDependency 추가
pnpm add -Dw typescript
```

### 워크스페이스 간 의존성

```json
// apps/my-app/package.json
{
  "dependencies": {
    "@dreamseed/shared-editor": "workspace:*",
    "@dreamseed/shared-schemas": "workspace:*"
  }
}
```

---

## 📊 MathJax 렌더링 흐름

```
TipTap JSON 문서
    ↓
ReactTipTapRenderer / VueTipTapRenderer
    ↓
TipTap EditorContent 렌더링
    ↓
useMathJaxTypeset 훅 실행
    ↓
typesetQueued() 호출
    ↓
MathJax.typesetPromise()
    ↓
.math-inline, .math-block 노드 렌더링
```

---

## 🎨 MathJax 설정

### 기본 설정 (자동 로드)

`mathjaxUtils.ts`에서 자동으로 MathJax 스크립트를 로드합니다:

```typescript
window.MathJax = {
  tex: { packages: { '[+]': ['mhchem'] } },
  options: { skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }
}
```

### 커스텀 설정

```html
<\!-- public/index.html에 추가 -->
<script>
window.MathJax = {
  tex: {
    packages: { '[+]': ['mhchem', 'ams'] },
    inlineMath: [['$', '$']],
    displayMath: [['$$', '$$']]
  },
  svg: {
    fontCache: 'global'
  },
  options: {
    enableAssistiveMml: true
  }
}
</script>
```

---

## 🔍 문제 해결

### 문제 1: pnpm 명령어 실행 안 됨

**해결**:
```bash
# pnpm 재설치
npm install -g pnpm@latest

# 캐시 정리
pnpm store prune
```

### 문제 2: 워크스페이스 의존성 인식 안 됨

**해결**:
```bash
# 루트에서 재설치
rm -rf node_modules
pnpm install
```

### 문제 3: TypeScript 경로 인식 안 됨

**해결**:
```json
// tsconfig.json에서 baseUrl 확인
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "baseUrl": "."
  }
}
```

### 문제 4: MathJax 렌더링 안 됨

**해결**:
```typescript
// 수동으로 typeset 호출
import { typesetQueued } from '@dreamseed/shared-editor'

useEffect(() => {
  typesetQueued(document.body)
}, [content])
```

---

## ✅ 체크리스트

### 워크스페이스 설정
- [x] pnpm-workspace.yaml 생성
- [x] 루트 package.json 생성
- [x] tsconfig.base.json 생성

### shared/editor
- [x] mathjaxUtils.ts 생성
- [x] React 렌더러 생성
- [x] Vue 렌더러 생성
- [x] Barrel exports 업데이트
- [x] peer dependencies 설정

### shared/schemas
- [x] tsconfig.json 상속 설정

### 테스트
- [ ] React 앱에서 렌더러 테스트
- [ ] Vue 앱에서 렌더러 테스트
- [ ] MathJax 렌더링 확인

---

**완성도 높은 pnpm 워크스페이스 + TipTap MathJax 렌더러 완료\!** 🎉

**즉시 실행**:
```bash
pnpm install
pnpm build
pnpm test
```
