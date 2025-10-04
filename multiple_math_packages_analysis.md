# 다중 수학/화학 서식 패키지 사용 시 문제점과 해결방안

## 🚨 **다중 패키지 사용 시 발생하는 문제점들**

### 📊 **1. 렌더링 충돌 문제**

#### **문제점:**
```javascript
// MathLive와 KaTeX가 동시에 같은 요소를 렌더링하려 할 때
const mathField = document.getElementById('math-field');
const katexElement = document.getElementById('katex-element');

// 충돌 발생!
mathField.addEventListener('input', () => {
    // MathLive가 처리
});

katex.render('\\frac{1}{2}', katexElement);
// KaTeX가 처리 - 충돌!
```

#### **해결방안:**
```javascript
// 명확한 영역 분리
function renderMath(notation, type) {
    switch(type) {
        case 'basic':
            return renderWithMathLive(notation);
        case 'advanced':
            return renderWithKaTeX(notation);
        case 'chemistry':
            return renderWithChemDoodle(notation);
    }
}
```

### 📊 **2. 스타일 충돌 문제**

#### **문제점:**
```css
/* MathLive 스타일 */
.mathlive {
    font-family: 'KaTeX_Math', 'Times New Roman', serif;
    font-size: 16px;
}

/* KaTeX 스타일 */
.katex {
    font-family: 'KaTeX_Main', 'Times New Roman', serif;
    font-size: 18px;
}

/* ChemDoodle 스타일 */
.chemdoodle {
    font-family: 'Arial', sans-serif;
    font-size: 14px;
}
```

#### **해결방안:**
```css
/* 통합 스타일 시스템 */
.math-renderer {
    --math-font-family: 'KaTeX_Math', 'Times New Roman', serif;
    --math-font-size: 16px;
    --math-color: #000;
}

.mathlive { 
    font-family: var(--math-font-family);
    font-size: var(--math-font-size);
    color: var(--math-color);
}

.katex { 
    font-family: var(--math-font-family);
    font-size: var(--math-font-size);
    color: var(--math-color);
}
```

### 📊 **3. 성능 문제**

#### **문제점:**
```html
<!-- 모든 라이브러리를 한 번에 로드 -->
<script src="https://unpkg.com/mathlive/dist/mathlive.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<script src="https://web.chemdoodle.com/install/ChemDoodleWeb.js"></script>
<!-- 총 4MB+ 라이브러리 로드 -->
```

#### **해결방안:**
```javascript
// 동적 로딩
async function loadMathLibrary(type) {
    switch(type) {
        case 'mathlive':
            if (!window.MathLive) {
                await import('https://unpkg.com/mathlive/dist/mathlive.min.js');
            }
            break;
        case 'katex':
            if (!window.katex) {
                await import('https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js');
            }
            break;
        case 'chemdoodle':
            if (!window.ChemDoodle) {
                await import('https://web.chemdoodle.com/install/ChemDoodleWeb.js');
            }
            break;
    }
}
```

### 📊 **4. 입력 방식 불일치**

#### **문제점:**
```javascript
// MathLive: LaTeX 입력
mathField.setValue('\\frac{1}{2}');

// KaTeX: LaTeX 입력
katex.render('\\frac{1}{2}', element);

// ChemDoodle: SMILES 입력
chemDoodle.loadMolecule('CCO'); // 에탄올

// MathJax: MathML 입력
MathJax.typesetPromise([element]);
```

#### **해결방안:**
```javascript
// 통합 입력 시스템
class UnifiedMathInput {
    constructor() {
        this.inputType = 'latex'; // 기본 입력 타입
        this.renderers = new Map();
    }
    
    setInputType(type) {
        this.inputType = type;
    }
    
    async render(notation, targetElement) {
        const renderer = await this.getRenderer(notation);
        return renderer.render(notation, targetElement);
    }
    
    async getRenderer(notation) {
        if (this.isChemistry(notation)) {
            return await this.loadRenderer('chemdoodle');
        } else if (this.isAdvancedMath(notation)) {
            return await this.loadRenderer('katex');
        } else {
            return await this.loadRenderer('mathlive');
        }
    }
}
```

## 🛠️ **해결방안: 통합 수학 렌더링 시스템**

### **1. 계층적 렌더링 시스템**

```javascript
class MathRenderingSystem {
    constructor() {
        this.renderers = {
            basic: null,      // MathLive
            advanced: null,   // KaTeX
            chemistry: null,  // ChemDoodle
            dynamic: null     // Desmos
        };
        this.loadedLibraries = new Set();
    }
    
    async initialize() {
        // 필요한 라이브러리만 동적 로드
        await this.loadRenderer('basic');
    }
    
    async loadRenderer(type) {
        if (this.loadedLibraries.has(type)) return;
        
        switch(type) {
            case 'basic':
                await this.loadMathLive();
                break;
            case 'advanced':
                await this.loadKaTeX();
                break;
            case 'chemistry':
                await this.loadChemDoodle();
                break;
            case 'dynamic':
                await this.loadDesmos();
                break;
        }
        
        this.loadedLibraries.add(type);
    }
    
    async render(notation, targetElement, options = {}) {
        const rendererType = this.detectRendererType(notation, options);
        await this.loadRenderer(rendererType);
        
        return this.renderers[rendererType].render(notation, targetElement);
    }
    
    detectRendererType(notation, options) {
        if (options.forceType) return options.forceType;
        
        if (this.isChemistry(notation)) return 'chemistry';
        if (this.isAdvancedMath(notation)) return 'advanced';
        if (this.isDynamic(notation)) return 'dynamic';
        
        return 'basic';
    }
}
```

### **2. 통합 입력 인터페이스**

```javascript
class UnifiedMathInput {
    constructor(container) {
        this.container = container;
        this.renderer = new MathRenderingSystem();
        this.currentNotation = '';
        this.currentType = 'basic';
    }
    
    async initialize() {
        await this.renderer.initialize();
        this.setupInputInterface();
    }
    
    setupInputInterface() {
        // 통합 입력 필드
        this.inputField = document.createElement('math-field');
        this.inputField.addEventListener('input', (e) => {
            this.handleInput(e.target.getValue());
        });
        
        // 렌더링 타입 선택
        this.typeSelector = document.createElement('select');
        this.typeSelector.innerHTML = `
            <option value="basic">기본 수학</option>
            <option value="advanced">고급 수학</option>
            <option value="chemistry">화학</option>
            <option value="dynamic">동적 수학</option>
        `;
        this.typeSelector.addEventListener('change', (e) => {
            this.currentType = e.target.value;
            this.rerender();
        });
        
        // 렌더링 영역
        this.renderArea = document.createElement('div');
        this.renderArea.className = 'math-render-area';
        
        this.container.appendChild(this.typeSelector);
        this.container.appendChild(this.inputField);
        this.container.appendChild(this.renderArea);
    }
    
    async handleInput(notation) {
        this.currentNotation = notation;
        await this.rerender();
    }
    
    async rerender() {
        this.renderArea.innerHTML = '';
        await this.renderer.render(
            this.currentNotation, 
            this.renderArea, 
            { forceType: this.currentType }
        );
    }
}
```

### **3. 스타일 통합 시스템**

```css
/* 통합 수학 렌더링 스타일 */
.math-render-system {
    --primary-font: 'KaTeX_Math', 'Times New Roman', serif;
    --secondary-font: 'Arial', sans-serif;
    --math-color: #000;
    --math-bg: #fff;
    --math-border: #ddd;
    --math-padding: 8px;
    --math-margin: 4px;
}

/* 기본 수학 (MathLive) */
.mathlive {
    font-family: var(--primary-font);
    color: var(--math-color);
    background: var(--math-bg);
    border: 1px solid var(--math-border);
    padding: var(--math-padding);
    margin: var(--math-margin);
}

/* 고급 수학 (KaTeX) */
.katex {
    font-family: var(--primary-font);
    color: var(--math-color);
    background: var(--math-bg);
    border: 1px solid var(--math-border);
    padding: var(--math-padding);
    margin: var(--math-margin);
}

/* 화학 (ChemDoodle) */
.chemdoodle {
    font-family: var(--secondary-font);
    color: var(--math-color);
    background: var(--math-bg);
    border: 1px solid var(--math-border);
    padding: var(--math-padding);
    margin: var(--math-margin);
}

/* 동적 수학 (Desmos) */
.desmos {
    font-family: var(--secondary-font);
    color: var(--math-color);
    background: var(--math-bg);
    border: 1px solid var(--math-border);
    padding: var(--math-padding);
    margin: var(--math-margin);
}
```

### **4. 성능 최적화**

```javascript
class OptimizedMathRenderer {
    constructor() {
        this.cache = new Map();
        this.loadingPromises = new Map();
        this.renderQueue = [];
        this.isProcessing = false;
    }
    
    async render(notation, targetElement, options = {}) {
        // 캐시 확인
        const cacheKey = this.getCacheKey(notation, options);
        if (this.cache.has(cacheKey)) {
            targetElement.innerHTML = this.cache.get(cacheKey);
            return;
        }
        
        // 렌더링 큐에 추가
        this.renderQueue.push({ notation, targetElement, options, cacheKey });
        
        if (!this.isProcessing) {
            this.processQueue();
        }
    }
    
    async processQueue() {
        this.isProcessing = true;
        
        while (this.renderQueue.length > 0) {
            const { notation, targetElement, options, cacheKey } = this.renderQueue.shift();
            
            try {
                const result = await this.doRender(notation, targetElement, options);
                this.cache.set(cacheKey, result);
            } catch (error) {
                console.error('Rendering error:', error);
            }
        }
        
        this.isProcessing = false;
    }
    
    getCacheKey(notation, options) {
        return `${notation}_${JSON.stringify(options)}`;
    }
}
```

## 🎯 **최종 권장사항**

### **1. 단계적 구현**
```
Phase 1: MathLive 기본 구현
Phase 2: KaTeX 고급 수학 추가
Phase 3: ChemDoodle 화학 추가
Phase 4: Desmos 동적 수학 추가
Phase 5: 통합 시스템 최적화
```

### **2. 사용자 경험 최적화**
```javascript
// 사용자에게 투명한 렌더링
const mathSystem = new MathRenderingSystem();

// 사용자는 하나의 인터페이스만 사용
mathSystem.render('H_2O', element);           // 자동으로 화학으로 인식
mathSystem.render('\\frac{1}{2}', element);   // 자동으로 수학으로 인식
mathSystem.render('x^2 + y^2 = 1', element);  // 자동으로 동적 수학으로 인식
```

### **3. 성능 모니터링**
```javascript
// 렌더링 성능 모니터링
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            renderTime: new Map(),
            cacheHitRate: 0,
            errorRate: 0
        };
    }
    
    recordRenderTime(notation, time) {
        this.metrics.renderTime.set(notation, time);
    }
    
    recordCacheHit() {
        this.metrics.cacheHitRate++;
    }
    
    recordError() {
        this.metrics.errorRate++;
    }
}
```

## 🎯 **결론**

### **문제점:**
- 렌더링 충돌
- 스타일 불일치
- 성능 저하
- 입력 방식 혼재

### **해결방안:**
- **통합 렌더링 시스템**: 계층적 렌더링
- **통합 입력 인터페이스**: 사용자 투명성
- **스타일 통합**: 일관된 디자인
- **성능 최적화**: 동적 로딩, 캐싱

### **최종 권장사항:**
**여러 패키지를 사용하되, 통합 시스템으로 관리하여 사용자에게는 하나의 인터페이스로 제공하는 것이 최선입니다!**
