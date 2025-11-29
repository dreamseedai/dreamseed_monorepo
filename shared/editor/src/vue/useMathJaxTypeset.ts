/**
 * Vue 3 컴포저블: MathJax typeset
 */

import { onMounted, onUpdated, watch, type Ref } from 'vue'
import { typesetQueued } from '../mathjaxUtils'

export function useMathJaxTypeset(elRef: Ref<HTMLElement | null>, deps: any[] = []) {
  onMounted(() => typesetQueued(elRef.value ?? undefined))
  onUpdated(() => typesetQueued(elRef.value ?? undefined))
  watch(deps, () => typesetQueued(elRef.value ?? undefined))
}
