/**
 * Vue 3 디렉티브: v-mathjax
 */
import { typesetQueued } from '../mathjaxUtils';
export const vMathJax = {
    mounted(el) {
        typesetQueued(el);
    },
    updated(el) {
        typesetQueued(el);
    },
};
