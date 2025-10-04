# TipTap 에디터와 MathJax + ChemDoodle 조합 호환성 분석

## 🎯 **핵심 질문: TipTap이 MathJax + ChemDoodle을 지원하나요?**

### 📊 **결론: TipTap은 기본적으로 지원하지 않지만, 커스텀 확장으로 구현 가능합니다.**

## 🔍 **TipTap 에디터의 수학/화학 지원 현황**

### **기본 지원:**
```
✅ 기본 HTML/Markdown
✅ 이미지 삽입
✅ 링크 삽입
✅ 테이블
✅ 코드 블록
❌ 수학 수식 (기본 지원 없음)
❌ 화학 구조식 (기본 지원 없음)
```

### **확장 가능성:**
```
✅ 커스텀 Node 확장
✅ 커스텀 Mark 확장
✅ 커스텀 Plugin 확장
✅ HTML 삽입 지원
✅ JavaScript 실행 지원
```

## 🛠️ **TipTap + MathJax + ChemDoodle 통합 방법**

### **방법 1: 커스텀 Node 확장 (권장)**

```typescript
// MathJax Node 확장
import { Node, mergeAttributes } from '@tiptap/core'
import { ReactNodeViewRenderer } from '@tiptap/react'
import { MathJaxComponent } from './MathJaxComponent'

export interface MathJaxOptions {
  HTMLAttributes: Record<string, any>
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    mathJax: {
      setMathJax: (attributes: { formula: string }) => ReturnType
    }
  }
}

export const MathJaxNode = Node.create<MathJaxOptions>({
  name: 'mathJax',
  
  group: 'block',
  
  atom: true,
  
  addAttributes() {
    return {
      formula: {
        default: '',
        parseHTML: element => element.getAttribute('data-formula'),
        renderHTML: attributes => ({
          'data-formula': attributes.formula,
        }),
      },
    }
  },
  
  parseHTML() {
    return [
      {
        tag: 'div[data-type="mathjax"]',
      },
    ]
  },
  
  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, { 'data-type': 'mathjax' }), 0]
  },
  
  addNodeView() {
    return ReactNodeViewRenderer(MathJaxComponent)
  },
  
  addCommands() {
    return {
      setMathJax: (attributes) => ({ commands }) => {
        return commands.insertContent({
          type: this.name,
          attrs: attributes,
        })
      },
    }
  },
})
```

```typescript
// ChemDoodle Node 확장
import { Node, mergeAttributes } from '@tiptap/core'
import { ReactNodeViewRenderer } from '@tiptap/react'
import { ChemDoodleComponent } from './ChemDoodleComponent'

export interface ChemDoodleOptions {
  HTMLAttributes: Record<string, any>
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    chemDoodle: {
      setChemDoodle: (attributes: { 
        type: 'benzene' | 'naphthalene' | 'steroid' | 'smiles',
        data: string 
      }) => ReturnType
    }
  }
}

export const ChemDoodleNode = Node.create<ChemDoodleOptions>({
  name: 'chemDoodle',
  
  group: 'block',
  
  atom: true,
  
  addAttributes() {
    return {
      type: {
        default: 'smiles',
        parseHTML: element => element.getAttribute('data-type'),
        renderHTML: attributes => ({
          'data-type': attributes.type,
        }),
      },
      data: {
        default: '',
        parseHTML: element => element.getAttribute('data-chem-data'),
        renderHTML: attributes => ({
          'data-chem-data': attributes.data,
        }),
      },
    }
  },
  
  parseHTML() {
    return [
      {
        tag: 'div[data-type="chemdoodle"]',
      },
    ]
  },
  
  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, { 'data-type': 'chemdoodle' }), 0]
  },
  
  addNodeView() {
    return ReactNodeViewRenderer(ChemDoodleComponent)
  },
  
  addCommands() {
    return {
      setChemDoodle: (attributes) => ({ commands }) => {
        return commands.insertContent({
          type: this.name,
          attrs: attributes,
        })
      },
    }
  },
})
```

### **방법 2: React 컴포넌트 구현**

```typescript
// MathJax 컴포넌트
import React, { useEffect, useRef } from 'react'

interface MathJaxComponentProps {
  node: {
    attrs: {
      formula: string
    }
  }
  updateAttributes: (attrs: any) => void
  deleteNode: () => void
}

export const MathJaxComponent: React.FC<MathJaxComponentProps> = ({ 
  node, 
  updateAttributes, 
  deleteNode 
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    if (containerRef.current && window.MathJax) {
      containerRef.current.innerHTML = node.attrs.formula
      MathJax.typesetPromise([containerRef.current])
    }
  }, [node.attrs.formula])
  
  const handleEdit = () => {
    const newFormula = prompt('수식을 입력하세요:', node.attrs.formula)
    if (newFormula !== null) {
      updateAttributes({ formula: newFormula })
    }
  }
  
  return (
    <div className="mathjax-container" contentEditable={false}>
      <div 
        ref={containerRef}
        className="mathjax-formula"
        onClick={handleEdit}
        style={{ cursor: 'pointer' }}
      />
      <div className="mathjax-controls">
        <button onClick={handleEdit}>편집</button>
        <button onClick={deleteNode}>삭제</button>
      </div>
    </div>
  )
}
```

```typescript
// ChemDoodle 컴포넌트
import React, { useEffect, useRef } from 'react'

interface ChemDoodleComponentProps {
  node: {
    attrs: {
      type: 'benzene' | 'naphthalene' | 'steroid' | 'smiles'
      data: string
    }
  }
  updateAttributes: (attrs: any) => void
  deleteNode: () => void
}

export const ChemDoodleComponent: React.FC<ChemDoodleComponentProps> = ({ 
  node, 
  updateAttributes, 
  deleteNode 
}) => {
  const canvasRef = useRef<HTMLDivElement>(null)
  const canvasInstanceRef = useRef<any>(null)
  
  useEffect(() => {
    if (canvasRef.current && window.ChemDoodle) {
      const canvasId = `chem-canvas-${Date.now()}`
      canvasRef.current.innerHTML = `<div id="${canvasId}"></div>`
      
      let canvas
      switch (node.attrs.type) {
        case 'benzene':
          canvas = new ChemDoodle.SketchCanvas(canvasId, 300, 300)
          // 벤젠 고리 생성 로직
          break
        case 'naphthalene':
          canvas = new ChemDoodle.SketchCanvas(canvasId, 300, 300)
          // 나프탈렌 생성 로직
          break
        case 'steroid':
          canvas = new ChemDoodle.SketchCanvas(canvasId, 400, 400)
          // 스테로이드 생성 로직
          break
        case 'smiles':
          canvas = new ChemDoodle.SketchCanvas(canvasId, 300, 300)
          const molecule = ChemDoodle.readMOL(node.attrs.data)
          canvas.loadMolecule(molecule)
          break
      }
      
      canvasInstanceRef.current = canvas
    }
  }, [node.attrs.type, node.attrs.data])
  
  const handleEdit = () => {
    if (node.attrs.type === 'smiles') {
      const newSmiles = prompt('SMILES 문자열을 입력하세요:', node.attrs.data)
      if (newSmiles !== null) {
        updateAttributes({ data: newSmiles })
      }
    }
  }
  
  return (
    <div className="chemdoodle-container" contentEditable={false}>
      <div ref={canvasRef} />
      <div className="chemdoodle-controls">
        <button onClick={handleEdit}>편집</button>
        <button onClick={deleteNode}>삭제</button>
      </div>
    </div>
  )
}
```

### **방법 3: 통합 에디터 설정**

```typescript
// TipTap 에디터 설정
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { MathJaxNode } from './extensions/MathJaxNode'
import { ChemDoodleNode } from './extensions/ChemDoodleNode'

export const DreamSeedEditor = () => {
  const editor = useEditor({
    extensions: [
      StarterKit,
      MathJaxNode,
      ChemDoodleNode,
    ],
    content: '<p>수학과 화학을 입력해보세요!</p>',
  })
  
  const insertMathJax = () => {
    const formula = prompt('수식을 입력하세요:')
    if (formula) {
      editor?.commands.setMathJax({ formula })
    }
  }
  
  const insertBenzene = () => {
    editor?.commands.setChemDoodle({ 
      type: 'benzene', 
      data: '' 
    })
  }
  
  const insertNaphthalene = () => {
    editor?.commands.setChemDoodle({ 
      type: 'naphthalene', 
      data: '' 
    })
  }
  
  const insertSteroid = () => {
    editor?.commands.setChemDoodle({ 
      type: 'steroid', 
      data: '' 
    })
  }
  
  const insertSmiles = () => {
    const smiles = prompt('SMILES 문자열을 입력하세요:')
    if (smiles) {
      editor?.commands.setChemDoodle({ 
        type: 'smiles', 
        data: smiles 
      })
    }
  }
  
  return (
    <div className="dreamseed-editor">
      <div className="toolbar">
        <button onClick={insertMathJax}>수학 수식</button>
        <button onClick={insertBenzene}>벤젠 고리</button>
        <button onClick={insertNaphthalene}>나프탈렌</button>
        <button onClick={insertSteroid}>스테로이드</button>
        <button onClick={insertSmiles}>SMILES</button>
      </div>
      <EditorContent editor={editor} />
    </div>
  )
}
```

## 🎯 **TipTap + MathJax + ChemDoodle 통합의 장단점**

### **장점:**
```
✅ 완전한 통합: TipTap 에디터 내에서 수학/화학 편집
✅ 사용자 친화적: 직관적인 인터페이스
✅ 확장 가능: 커스텀 Node/Mark 확장
✅ React 지원: React 컴포넌트로 구현
✅ 실시간 편집: 수식/구조식 실시간 편집
✅ 저장/로드: JSON 형태로 저장 가능
```

### **단점:**
```
❌ 복잡한 구현: 커스텀 확장 개발 필요
❌ 성능 이슈: 대량의 수식/구조식 시 성능 저하
❌ 호환성: 다른 에디터와 호환성 문제
❌ 학습 곡선: 개발자 학습 필요
❌ 유지보수: 커스텀 코드 유지보수 필요
```

## 🛠️ **구현 단계별 계획**

### **1단계: 기본 설정 (1주)**
- TipTap 에디터 기본 설정
- MathJax 라이브러리 통합
- ChemDoodle 라이브러리 통합

### **2단계: 커스텀 확장 개발 (2-3주)**
- MathJax Node 확장 개발
- ChemDoodle Node 확장 개발
- React 컴포넌트 구현

### **3단계: 통합 테스트 (1-2주)**
- 수학 수식 편집 테스트
- 화학 구조식 편집 테스트
- 성능 최적화

### **4단계: UI/UX 개선 (1-2주)**
- 툴바 인터페이스 구현
- 편집 모드 개선
- 사용자 경험 최적화

## 🎯 **대안 솔루션**

### **방법 1: 별도 에디터 사용**
```typescript
// 수학/화학 전용 에디터
const MathEditor = () => {
  return (
    <div>
      <MathJaxEditor />
      <ChemDoodleEditor />
    </div>
  )
}
```

### **방법 2: 모달 방식**
```typescript
// 모달로 수학/화학 편집
const insertMathModal = () => {
  setShowMathModal(true)
}

const insertChemModal = () => {
  setShowChemModal(true)
}
```

### **방법 3: 사이드바 방식**
```typescript
// 사이드바에서 수학/화학 편집
const SidebarEditor = () => {
  return (
    <div className="sidebar">
      <MathJaxPanel />
      <ChemDoodlePanel />
    </div>
  )
}
```

## 🎯 **최종 권장사항**

### **TipTap + MathJax + ChemDoodle 통합 (권장)**
- **장점**: 완전한 통합, 사용자 친화적
- **단점**: 복잡한 구현, 개발 시간 필요
- **적용**: 고급 사용자, 전문적인 에디터 필요 시

### **별도 에디터 사용 (대안)**
- **장점**: 간단한 구현, 빠른 개발
- **단점**: 통합성 부족, 사용자 경험 분산
- **적용**: 빠른 프로토타입, 기본 기능만 필요 시

## 🎯 **결론**

**TipTap은 기본적으로 MathJax + ChemDoodle을 지원하지 않지만, 커스텀 확장으로 완전히 통합 가능합니다.**

- **기본 지원**: 없음
- **확장 가능성**: 높음
- **구현 복잡도**: 중간
- **사용자 경험**: 우수

**DreamSeed AI 프로젝트에서는 TipTap + MathJax + ChemDoodle 통합을 권장합니다!**
