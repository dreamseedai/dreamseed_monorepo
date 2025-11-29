# TipTap Math Editor

Inline/Block 수식 + 화학식 지원 (lang: 'math'|'chem')

## 🚀 빠른 시작

### 1. 에디터 생성

```typescript
import { createMathEditor } from '@/lib/editor'

const editor = createMathEditor({
  element: document.getElementById('editor')\!,
  content: {
    type: 'doc',
    content: [
      { type: 'paragraph', content: [{ type: 'text', text: '수식을 입력하세요...' }] }
    ]
  },
  onUpdate: (editor) => {
    console.log('Updated:', editor.getJSON())
  }
})
```

### 2. 수식 삽입

```typescript
// 인라인 수식
editor.commands.setMathInline({ tex: 'x^2 + y^2 = r^2', lang: 'math' })

// 블록 수식
editor.commands.setMathBlock({ tex: '\\int_0^1 x^2\\,dx = \\frac{1}{3}', lang: 'math' })

// 화학식
editor.commands.setMathInline({ tex: '\\ce{H2SO4}', lang: 'chem' })
```

### 3. 붙여넣기 지원

- `$x^2$` → math-inline
- `$$\int_0^1 x^2\,dx$$` → math-block
- Wiris 이미지 → math-inline
- MathML → math-inline (API 변환)

## 📚 API 문서

### createMathEditor(options)

```typescript
interface EditorOptions {
  element: HTMLElement        // 에디터 컨테이너
  content?: any               // 초기 TipTap JSON
  onUpdate?: (editor) => void // 업데이트 콜백
  editable?: boolean          // 편집 가능 여부 (기본: true)
}
```

### tiptapToHTML(doc)

TipTap JSON → HTML 변환

```typescript
const html = tiptapToHTML(editor.getJSON())
```

### tiptapToPlainText(doc)

TipTap JSON → 플레인 텍스트 (검색용)

```typescript
const plain = tiptapToPlainText(editor.getJSON())
```

## 🎨 노드 구조

### math-inline

```json
{
  "type": "math-inline",
  "attrs": {
    "tex": "x^2",
    "lang": "math"
  }
}
```

### math-block

```json
{
  "type": "math-block",
  "attrs": {
    "tex": "\\int_0^1 x^2\\,dx",
    "lang": "math"
  }
}
```

## 🔧 고급 사용법

### 수식 업데이트

```typescript
editor.commands.updateMathInline({ tex: 'x^3' })
editor.commands.updateMathBlock({ lang: 'chem' })
```

### 뷰어 모드

```typescript
const viewer = createMathEditor({
  element: document.getElementById('viewer')\!,
  content: savedDoc,
  editable: false
})
```

### MathJax 렌더링

```html
<script>
window.MathJax = {
  tex: { packages: {'[+]': ['mhchem']} },
}
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" async></script>
```

## ✅ 체크리스트

- [ ] TipTap 의존성 설치
- [ ] 에디터 생성
- [ ] Math 노드 등록
- [ ] 붙여넣기 규칙 등록
- [ ] MathJax 스크립트 로드
