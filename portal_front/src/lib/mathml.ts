/**
 * MathML → MathJax 클라이언트 유틸리티
 * 
 * TipTap 에디터 통합:
 * - Wiris MathML 붙여넣기 처리
 * - TeX 변환 및 렌더링
 * - MathLive 편집기 연동
 */

/**
 * MathML을 TeX로 변환 (백엔드 API 호출)
 */
export async function convertMathMLToTeX(mathml: string): Promise<string> {
  try {
    const response = await fetch("/api/mathml/convert", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ mathml }),
    });

    if (!response.ok) {
      throw new Error(`변환 실패: ${response.statusText}`);
    }

    const data = await response.json();
    return data.tex;
  } catch (error) {
    console.error("MathML 변환 오류:", error);
    // 폴백: 원본 MathML 반환
    return `\\text{[MathML 변환 실패]}`;
  }
}

/**
 * HTML에서 MathML 추출
 */
export function extractMathMLFromHTML(html: string): string[] {
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");
  const mathElements = doc.querySelectorAll("math");

  return Array.from(mathElements).map((el) => el.outerHTML);
}

/**
 * Wiris 이미지를 MathML로 변환 (OCR 폴백)
 */
export async function convertWirisImageToTeX(imageUrl: string): Promise<string> {
  try {
    const response = await fetch("/api/mathml/ocr", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ imageUrl }),
    });

    if (!response.ok) {
      throw new Error(`OCR 실패: ${response.statusText}`);
    }

    const data = await response.json();
    return data.tex;
  } catch (error) {
    console.error("Wiris 이미지 변환 오류:", error);
    return `\\text{[이미지 변환 실패]}`;
  }
}

/**
 * MathJax 렌더링 (클라이언트)
 */
export function renderMathJax(element: HTMLElement): void {
  if (typeof window !== "undefined" && (window as any).MathJax) {
    (window as any).MathJax.typesetPromise([element]).catch((err: Error) => {
      console.error("MathJax 렌더링 오류:", err);
    });
  }
}

/**
 * MathLive 에디터 초기화
 */
export function initMathLiveEditor(
  element: HTMLElement,
  options?: {
    onInput?: (tex: string) => void;
    initialValue?: string;
    mode?: "math" | "chem";
  }
): void {
  if (typeof window !== "undefined" && (window as any).MathLive) {
    const mathfield = (window as any).MathLive.makeMathField(element, {
      virtualKeyboardMode: "manual",
      onContentDidChange: (mf: any) => {
        const tex = mf.getValue();
        options?.onInput?.(tex);
      },
    });

    if (options?.initialValue) {
      mathfield.setValue(options.initialValue);
    }

    // 화학식 모드
    if (options?.mode === "chem") {
      mathfield.setOptions({
        macros: {
          "\\ce": "\\text{#1}",
        },
      });
    }
  }
}

/**
 * TipTap 붙여넣기 핸들러
 */
export async function handleMathMLPaste(html: string): Promise<string> {
  const mathmlList = extractMathMLFromHTML(html);

  if (mathmlList.length === 0) {
    return html;
  }

  let result = html;

  for (const mathml of mathmlList) {
    const tex = await convertMathMLToTeX(mathml);
    // MathML을 TeX로 교체
    result = result.replace(mathml, `$${tex}$`);
  }

  return result;
}

/**
 * 접근성: MathSpeak 생성
 */
export function generateMathSpeak(tex: string): string {
  // 간단한 MathSpeak 변환 (실제로는 speech-rule-engine 사용)
  let speak = tex;

  // 기본 변환 규칙
  speak = speak.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "$1 over $2");
  speak = speak.replace(/\\sqrt\{([^}]+)\}/g, "square root of $1");
  speak = speak.replace(/\^(\d+)/g, "to the power $1");
  speak = speak.replace(/_(\d+)/g, "sub $1");
  speak = speak.replace(/\\sum/g, "sum");
  speak = speak.replace(/\\int/g, "integral");
  speak = speak.replace(/\\lim/g, "limit");

  return speak;
}

/**
 * 화학식 감지
 */
export function isChemicalFormula(tex: string): boolean {
  // \ce{} 패턴 또는 연속된 원소 기호
  return /\\ce\{/.test(tex) || /[A-Z][a-z]?\d+/.test(tex);
}

/**
 * TeX 정규화 (클라이언트 측)
 */
export function normalizeTex(tex: string): string {
  let normalized = tex;

  // 1. 연속 공백 제거
  normalized = normalized.replace(/\s+/g, " ").trim();

  // 2. 불필요한 중괄호 제거
  normalized = normalized.replace(/\{(\w)\}/g, "$1");

  // 3. 함수 키워드 정규화
  const functions = ["sin", "cos", "tan", "log", "ln", "lim", "det"];
  for (const func of functions) {
    normalized = normalized.replace(
      new RegExp(`(?<!\\\\)\\b${func}\\b`, "g"),
      `\\${func}`
    );
  }

  return normalized;
}
