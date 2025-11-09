/**
 * TipTap 에디터 팩토리
 */

import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { MathInline, MathBlock } from './mathNodes'
import { MathPaste } from './mathPasteRules'

export interface EditorOptions {
  element: HTMLElement
  content?: any
  onUpdate?: (editor: Editor) => void
  editable?: boolean
}

export function createMathEditor(options: EditorOptions): Editor {
  const { element, content, onUpdate, editable = true } = options

  const editor = new Editor({
    element,
    content,
    editable,
    extensions: [
      StarterKit,
      MathInline,
      MathBlock,
      MathPaste,
    ],
    onUpdate: ({ editor }) => {
      onUpdate?.(editor)
    },
  })

  return editor
}

export function tiptapToHTML(doc: any): string {
  const editor = new Editor({
    content: doc,
    extensions: [StarterKit, MathInline, MathBlock],
  })

  const html = editor.getHTML()
  editor.destroy()

  return html
}

export function tiptapToPlainText(doc: any): string {
  const parts: string[] = []

  function walk(node: any) {
    if (node.type === 'text') {
      parts.push(node.text || '')
    } else if (node.type === 'math-inline') {
      parts.push(` ${node.attrs.tex} `)
    } else if (node.type === 'math-block') {
      parts.push(`\n${node.attrs.tex}\n`)
    } else if (node.content) {
      node.content.forEach(walk)
    }
  }

  walk(doc)

  return parts.join('').replace(/\n{3,}/g, '\n\n').trim()
}

export { MathInline, MathBlock, MathPaste }
export type { MathAttrs } from './mathNodes'
