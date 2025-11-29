/**
 * MathJax v3 유틸리티
 *
 * SSR 가드, 중복 호출 디바운스 포함
 */
let _mjxReady = null;
export function loadMathJaxIfNeeded() {
    if (typeof window === "undefined")
        return Promise.resolve();
    if (window.MathJax?.typesetPromise)
        return Promise.resolve(window.MathJax);
    if (!_mjxReady) {
        // 기본 설정: mhchem 포함
        window.MathJax = window.MathJax || {
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
            script.onload = () => resolve(window.MathJax);
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    return _mjxReady;
}
let _tick = null;
export async function typesetQueued(root) {
    if (typeof window === "undefined")
        return;
    await loadMathJaxIfNeeded();
    if (_tick)
        cancelAnimationFrame(_tick);
    _tick = requestAnimationFrame(async () => {
        const MJ = window.MathJax;
        if (MJ?.typesetPromise) {
            const scope = root ?? document;
            const nodes = Array.from(scope.querySelectorAll(".math-inline, .math-block"));
            await MJ.typesetPromise(nodes.length ? nodes : undefined);
        }
    });
}
//# sourceMappingURL=mathjaxUtils.js.map