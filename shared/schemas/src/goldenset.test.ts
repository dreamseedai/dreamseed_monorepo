/**
 * GoldenSet 스키마 테스트
 */

import { GoldenSetItem } from './goldenset'

test('validates a golden item', () => {
  const parsed = GoldenSetItem.parse({
    id: 'm_nested_sqrt_01',
    domain: 'math',
    locale: 'ko',
    source_format: 'latex-tex',
    payload: { mathml: null, tex: '\\sqrt{a+\\sqrt{b}}' },
    expected: { tex: '\\sqrt{a+\\sqrt{b}}' },
    tags: ['sqrt', 'nested']
  })
  
  expect(parsed.id).toBe('m_nested_sqrt_01')
  expect(parsed.domain).toBe('math')
  expect(parsed.expected.tex).toBe('\\sqrt{a+\\sqrt{b}}')
})

test('rejects invalid id format', () => {
  expect(() => {
    GoldenSetItem.parse({
      id: 'INVALID ID',  // 대문자 및 공백 불허
      domain: 'math',
      source_format: 'latex-tex',
      payload: {},
      expected: { tex: 'x' }
    })
  }).toThrow()
})
