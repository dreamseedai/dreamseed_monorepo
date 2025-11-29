/**
 * Vue 3 디렉티브: v-mathjax
 */

import type { Directive } from 'vue'
import { typesetQueued } from '../mathjaxUtils'

export const vMathJax: Directive<HTMLElement, boolean | undefined> = {
  mounted(el) {
    typesetQueued(el)
  },
  updated(el) {
    typesetQueued(el)
  },
}
