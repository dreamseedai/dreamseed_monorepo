/**
 * React 훅: MathJax typeset
 */

import { useEffect } from 'react'
import { typesetQueued } from '../mathjaxUtils'

export function useMathJaxTypeset(deps: any[] = [], root?: HTMLElement | null) {
  useEffect(() => {
    typesetQueued(root ?? undefined)
  }, deps)
}
