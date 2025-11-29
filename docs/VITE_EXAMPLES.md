# Vite 앱 예시 코드

React/Vue 앱에서 shared 모듈 사용 예시

## 🎯 React 예시

### 1. TipTap 렌더러 사용

```tsx
// src/components/MathRenderer.tsx
import { ReactTipTapRenderer } from '@dreamseed/shared-editor'

const doc = {
  type: 'doc',
  content: [
    {
      type: 'paragraph',
      content: [{ type: 'text', text: '이차방정식: ' }]
    },
    {
      type: 'math-block',
      attrs: { tex: 'x=\\frac{-b\\pm\\sqrt{b^2-4ac}}{2a}', lang: 'math' }
    }
  ]
}

export default function MathRenderer() {
  return <ReactTipTapRenderer content={doc} />
}
```

### 2. 커스텀 훅 사용

```tsx
// src/components/CustomRenderer.tsx
import { useRef } from 'react'
import { useMathJaxTypeset } from '@dreamseed/shared-editor'

export default function CustomRenderer({ content }: { content: string }) {
  const containerRef = useRef<HTMLDivElement>(null)
  useMathJaxTypeset([content], containerRef.current)
  
  return (
    <div ref={containerRef}>
      <div className="math-inline">{content}</div>
    </div>
  )
}
```

### 3. Zod 스키마 검증

```tsx
// src/utils/validation.ts
import { TipTapDoc, GoldenSetItem } from '@dreamseed/shared-schemas'

export function validateDoc(data: unknown) {
  return TipTapDoc.parse(data)
}

export function validateGoldenItem(data: unknown) {
  return GoldenSetItem.parse(data)
}
```

---

## 🎯 Vue 예시

### 1. TipTap 렌더러 사용

```vue
<!-- src/components/MathRenderer.vue -->
<script setup lang="ts">
import { VueTipTapRenderer } from '@dreamseed/shared-editor'

const doc = {
  type: 'doc',
  content: [
    {
      type: 'paragraph',
      content: [{ type: 'text', text: '이차방정식: ' }]
    },
    {
      type: 'math-block',
      attrs: { tex: 'x=\\frac{-b\\pm\\sqrt{b^2-4ac}}{2a}', lang: 'math' }
    }
  ]
}
</script>

<template>
  <VueTipTapRenderer :content="doc" />
</template>
```

### 2. v-mathjax 디렉티브 사용

```vue
<!-- src/App.vue -->
<script setup lang="ts">
import { vMathJax } from '@dreamseed/shared-editor'
</script>

<template>
  <div v-mathjax>
    <div class="math-inline">x^2 + y^2 = r^2</div>
    <div class="math-block">\int_0^1 x^2\,dx</div>
  </div>
</template>
```

### 3. 컴포저블 사용

```vue
<!-- src/components/CustomRenderer.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { useMathJaxTypeset } from '@dreamseed/shared-editor'

const props = defineProps<{ content: string }>()
const containerRef = ref<HTMLElement | null>(null)

useMathJaxTypeset(containerRef, [props.content])
</script>

<template>
  <div ref="containerRef">
    <div class="math-inline">{{ content }}</div>
  </div>
</template>
```

---

## 📦 패키지 import 패턴

### 경로 별칭 사용

```typescript
// tsconfig.json paths 기반
import { ReactTipTapRenderer } from '@shared/editor/react/TipTapRenderer'
import { TipTapDoc } from '@shared/schemas/tiptap'
```

### 워크스페이스 패키지 사용

```typescript
// package.json dependencies 기반
import { ReactTipTapRenderer } from '@dreamseed/shared-editor'
import { TipTapDoc } from '@dreamseed/shared-schemas'
```

---

**완성도 높은 Vite 앱 예시 코드!** 🎉
