/**
 * TipTap Math 노드 타입 정의
 */
export type MathLang = "math" | "chem";
export interface MathAttrs {
    tex: string;
    lang: MathLang;
}
/**
 * TipTap Commands 타입 확장
 */
declare module "@tiptap/core" {
    interface Commands<ReturnType> {
        mathInline: {
            setMathInline: (attrs: MathAttrs) => ReturnType;
            updateMathInline: (attrs: Partial<MathAttrs>) => ReturnType;
        };
        mathBlock: {
            setMathBlock: (attrs: MathAttrs) => ReturnType;
            updateMathBlock: (attrs: Partial<MathAttrs>) => ReturnType;
        };
    }
}
//# sourceMappingURL=types.d.ts.map