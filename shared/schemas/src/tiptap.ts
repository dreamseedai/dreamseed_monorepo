/**
 * TipTap JSON 스키마 (Zod)
 */

import { z } from 'zod'

export const MathLang = z.enum(['math', 'chem'])

export const MathInlineNode = z.object({
  type: z.literal('math-inline'),
  attrs: z.object({
    tex: z.string().min(1),
    lang: MathLang
  })
})

export const MathBlockNode = z.object({
  type: z.literal('math-block'),
  attrs: z.object({
    tex: z.string().min(1),
    lang: MathLang
  })
})

export const TextNode = z.object({
  type: z.literal('text'),
  text: z.string()
})

export const ParagraphNode = z.object({
  type: z.literal('paragraph'),
  content: z.array(z.union([TextNode, MathInlineNode])).optional()
})

export const TipTapDoc = z.object({
  type: z.literal('doc'),
  content: z.array(z.union([ParagraphNode, MathBlockNode]))
})

export type TipTapDoc = z.infer<typeof TipTapDoc>
export type MathInlineNode = z.infer<typeof MathInlineNode>
export type MathBlockNode = z.infer<typeof MathBlockNode>
export type TextNode = z.infer<typeof TextNode>
export type ParagraphNode = z.infer<typeof ParagraphNode>
