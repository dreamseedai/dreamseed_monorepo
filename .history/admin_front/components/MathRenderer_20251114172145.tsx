'use client';

import { useEffect, useRef } from 'react';

interface MathRendererProps {
  content: string;
  className?: string;
}

// MathJax 타입 선언
declare global {
  interface Window {
    MathJax?: {
      typesetPromise?: (elements?: HTMLElement[]) => Promise<void>;
      startup?: {
        promise?: Promise<void>;
      };
    };
  }
}

/**
 * MathJax를 사용하여 MathML 및 LaTeX 수식을 렌더링합니다.
 * 
 * 지원 형식:
 * - MathML: <math>...</math> (네이티브 지원)
 * - 인라인 LaTeX: $...$, \(...\)
 * - 블록 LaTeX: $$...$$, \[...\]
 * - 연립방정식: \begin{cases}...\end{cases}
 */
export function MathRenderer({ content, className = '' }: MathRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !content) return;

    // HTML 콘텐츠 설정
    containerRef.current.innerHTML = content;

    // MathJax가 로드되면 수식 렌더링
    const renderMath = async () => {
      if (!containerRef.current) return;

      // MathJax가 로드될 때까지 대기
      if (window.MathJax?.startup?.promise) {
        await window.MathJax.startup.promise;
      }

      // MathJax로 수식 렌더링
      if (window.MathJax?.typesetPromise) {
        try {
          await window.MathJax.typesetPromise([containerRef.current]);
        } catch (err) {
          console.warn('MathJax 렌더링 실패:', err);
        }
      }
    };

    renderMath();
  }, [content]);

  return <div ref={containerRef} className={className} />;
}
