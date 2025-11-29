/**
 * TipTap Math 붙여넣기 규칙
 */

import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'

const chemLike = /(?:[A-Z][a-z]?\d*(?:[+-]?\d*)?){2,}/

export const MathPaste = Extension.create({
  name: 'mathPaste',

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: new PluginKey('mathPaste'),
        props: {
          handlePaste: (_view, event, _slice) => {
            const html = event.clipboardData?.getData('text/html')
            const text = event.clipboardData?.getData('text/plain')

            if (!html && !text) return false

            if (html) {
              const wirisMatch = /<img[^>]+class="[^"]*wiris[^"]*"[^>]*>/i.exec(html)
              if (wirisMatch) {
                const tag = wirisMatch[0]
                const mml = /data-mathml="([^"]+)"/.exec(tag)?.[1]
                const alt = /alt="([^"]+)"/.exec(tag)?.[1]
                const tex = (mml || alt || '').trim()

                if (tex) {
                  const lang = tex.includes('\\ce{') || chemLike.test(tex.replace(/\s+/g, ''))
                    ? 'chem'
                    : 'math'

                  this.editor.commands.setMathInline({ tex, lang })
                  return true
                }
              }

              const mathmlMatch = /<math[^>]*>.*?<\/math>/i.exec(html)
              if (mathmlMatch) {
                fetch('/api/mathml/convert', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ mathml: mathmlMatch[0] }),
                })
                  .then((res) => res.json())
                  .then((data) => {
                    const tex = data.tex || ''
                    const lang = tex.includes('\\ce{') || chemLike.test(tex.replace(/\s+/g, ''))
                      ? 'chem'
                      : 'math'
                    this.editor.commands.setMathInline({ tex, lang })
                  })
                  .catch((err) => console.error('MathML 변환 실패:', err))

                return true
              }
            }

            if (text) {
              const blockMatch = /\$\$(.+?)\$\$/s.exec(text)
              if (blockMatch) {
                const tex = blockMatch[1].trim()
                const lang = tex.includes('\\ce{') || chemLike.test(tex.replace(/\s+/g, ''))
                  ? 'chem'
                  : 'math'
                this.editor.commands.setMathBlock({ tex, lang })
                return true
              }

              const inlineMatch = /\$(.+?)\$/.exec(text)
              if (inlineMatch) {
                const tex = inlineMatch[1].trim()
                const lang = tex.includes('\\ce{') || chemLike.test(tex.replace(/\s+/g, ''))
                  ? 'chem'
                  : 'math'
                this.editor.commands.setMathInline({ tex, lang })
                return true
              }
            }

            return false
          },
        },
      }),
    ]
  },
})
