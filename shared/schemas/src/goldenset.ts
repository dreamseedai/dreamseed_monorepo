/**
 * GoldenSet 스키마 (Zod)
 */

import { z } from 'zod'

export const Locale = z.enum(['en', 'ko', 'zh-Hans', 'zh-Hant'])

export const GoldenSetItem = z.object({
  id: z.string().regex(/^[a-z0-9_\-]+$/),
  domain: z.enum(['math', 'chem']),
  locale: Locale.default('ko'),
  source_format: z.enum(['wiris-mathml', 'latex-tex', 'image-ocr']),
  payload: z.object({
    mathml: z.string().nullable().optional(),
    tex: z.string().nullable().optional(),
    image_path: z.string().nullable().optional(),
  }),
  expected: z.object({
    tex: z.string().min(1),
    svg_hash: z.string().optional().default(''),
    speech: z.string().optional().default(''),
  }),
  notes: z.string().optional().default(''),
  tags: z.array(z.string()).default([])
})

export type GoldenSetItem = z.infer<typeof GoldenSetItem>
export type Locale = z.infer<typeof Locale>
