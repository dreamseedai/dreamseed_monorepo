/**
 * React 훅: MathJax typeset
 */
import { useEffect } from 'react';
import { typesetQueued } from '../mathjaxUtils';
export function useMathJaxTypeset(deps = [], root) {
    useEffect(() => {
        typesetQueued(root ?? undefined);
    }, deps);
}
//# sourceMappingURL=useMathJaxTypeset.js.map