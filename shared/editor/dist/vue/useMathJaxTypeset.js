/**
 * Vue 3 컴포저블: MathJax typeset
 */
import { onMounted, onUpdated, watch } from 'vue';
import { typesetQueued } from '../mathjaxUtils';
export function useMathJaxTypeset(elRef, deps = []) {
    onMounted(() => typesetQueued(elRef.value ?? undefined));
    onUpdated(() => typesetQueued(elRef.value ?? undefined));
    watch(deps, () => typesetQueued(elRef.value ?? undefined));
}
//# sourceMappingURL=useMathJaxTypeset.js.map