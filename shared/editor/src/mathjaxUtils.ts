/**
 * MathJax v3 유틸리티
 *
 * SSR 가드, 중복 호출 디바운스 포함
 */

let _mjxReady: Promise<any> | null = null;

export function loadMathJaxIfNeeded(): Promise<any> {
  if (typeof window === "undefined") return Promise.resolve();
  if ((window as any).MathJax?.typesetPromise)
    return Promise.resolve((window as any).MathJax);

  if (!_mjxReady) {
    // 기본 설정: mhchem 포함
    (window as any).MathJax = (window as any).MathJax || {
      tex: { packages: { "[+]": ["mhchem"] } },
      options: {
        skipHtmlTags: [
          "script",
          "noscript",
          "style",
          "textarea",
          "pre",
          "code",
        ],
      },
    };
    _mjxReady = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js";
      script.async = true;
      script.onload = () => resolve((window as any).MathJax);
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
  return _mjxReady;
}

let _tick: number | null = null;

export async function typesetQueued(root?: HTMLElement | Document) {
  if (typeof window === "undefined") return;
  await loadMathJaxIfNeeded();
  if (_tick) cancelAnimationFrame(_tick);
  _tick = requestAnimationFrame(async () => {
    const MJ = (window as any).MathJax;
    if (MJ?.typesetPromise) {
      const scope = root ?? document;
      const nodes = Array.from(
        scope.querySelectorAll(".math-inline, .math-block")
      );
      await MJ.typesetPromise(nodes.length ? nodes : undefined);
    }
  });
}
