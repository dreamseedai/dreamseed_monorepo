<script setup lang="ts">
/**
 * Vue 3 TipTap 렌더러 (MathJax 통합)
 */

import { ref, onMounted } from 'vue'
import StarterKit from '@tiptap/starter-kit'
import { Editor, EditorContent } from '@tiptap/vue-3'
import { MathInline, MathBlock } from '../mathNodes'
import { useMathJaxTypeset } from './useMathJaxTypeset'
import { typesetQueued } from '../mathjaxUtils'

const props = defineProps<{ content: any }>()
const containerRef = ref<HTMLElement | null>(null)

const editor = new Editor({
  editable: false,
  extensions: [StarterKit, MathInline, MathBlock],
  content: props.content,
})

useMathJaxTypeset(containerRef, [props.content])

onMounted(() => {
  editor.on('update', () => typesetQueued(containerRef.value ?? undefined))
})
</script>

<template>
  <div ref="containerRef">
    <EditorContent :editor="editor" />
  </div>
</template>
