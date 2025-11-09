/**
 * MathJax v3 유틸리티
 *
 * SSR 가드, 중복 호출 디바운스 포함
 */
export declare function loadMathJaxIfNeeded(): Promise<any>;
export declare function typesetQueued(root?: HTMLElement | Document): Promise<void>;
