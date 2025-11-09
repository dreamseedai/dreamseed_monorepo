# GoldenSet 사용법

## 📋 골든셋 구조

50문항 (수학 30 + 화학 20) JSONL 형식

### 파일 구조
```
goldenset/
├── goldenset.schema.json       # JSON Schema 정의
├── goldenset.sample.jsonl      # 예시 6문항 (확장 필요)
└── README.md                   # 이 파일
```

## 🚀 사용 순서

### 1. 골든셋 확장 (50문항)

`goldenset.sample.jsonl`을 편집하여 50문항으로 확장:
- 수학 30문항
- 화학 20문항

### 2. 초기 스냅샷 생성

```bash
cd ../node
npm ci
npm run snapshot:write
```

이 명령은:
- MathJax로 SVG 렌더링
- SHA256 해시 계산
- Speech Rule Engine으로 MathSpeak 생성
- `expected.svg_hash`와 `expected.speech` 자동 채움

### 3. 변환 파이프라인 실행

```bash
cd ../scripts
python cli.py --infile ../goldenset/goldenset.sample.jsonl --outfile out.jsonl
```

### 4. CI 회귀 테스트

GitHub Actions가 PR마다 자동 실행:
- SVG 해시 비교
- MathSpeak 검증
- PyTest 실행

## 📝 JSONL 포맷 예시

```json
{
  "id": "m_nested_sqrt_01",
  "domain": "math",
  "locale": "ko",
  "source_format": "wiris-mathml",
  "payload": {
    "mathml": "<math>...</math>",
    "tex": null,
    "image_path": null
  },
  "expected": {
    "tex": "\\sqrt{a+\\sqrt{b}}",
    "svg_hash": "abc123...",
    "speech": "square root of a plus square root of b"
  },
  "notes": "중첩 근호 기본",
  "tags": ["sqrt", "nested"]
}
```

## 🎯 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | string | 고유 ID (예: `m_nested_sqrt_01`) |
| `domain` | enum | `math` 또는 `chem` |
| `locale` | enum | `ko`, `en`, `zh-Hans`, `zh-Hant` |
| `source_format` | enum | `wiris-mathml`, `latex-tex`, `image-ocr` |
| `payload.mathml` | string | Wiris MathML 원본 |
| `payload.tex` | string | LaTeX 원본 |
| `payload.image_path` | string | 이미지 경로 (OCR용) |
| `expected.tex` | string | 의미 보존 TeX (MathJax 호환) |
| `expected.svg_hash` | string | SVG SHA256 해시 (자동 생성) |
| `expected.speech` | string | MathSpeak (자동 생성) |
| `notes` | string | 설명 |
| `tags` | array | 태그 목록 |

## 🔍 카테고리별 권장 문항 수

### 수학 (30문항)
- 중첩 근호: 5문항
- 복합 첨자: 5문항
- 분수/적분: 8문항
- 벡터/행렬: 4문항
- 극한/합: 4문항
- 복합 케이스: 4문항

### 화학 (20문항)
- 기본 반응식: 8문항
- 전하 표기: 4문항
- 산화수: 4문항
- 복합 반응: 4문항

## ✅ 검증 체크리스트

- [ ] 50문항 작성 완료 (수학 30 + 화학 20)
- [ ] `expected.tex` 수동 작성 (의미 보존 TeX)
- [ ] 초기 스냅샷 생성 (`npm run snapshot:write`)
- [ ] 스냅샷 검증 (`npm run snapshot:check`)
- [ ] PyTest 실행 (`pytest -v tests/`)
- [ ] CI 워크플로우 확인

## 🚨 주의사항

1. **백업**: 스냅샷 생성 시 `.bak.jsonl` 자동 생성
2. **해시 변경**: MathJax 버전 업그레이드 시 해시 재생성 필요
3. **MathSpeak**: 영어 기준, 다국어는 별도 처리
4. **화학식**: `\ce{...}` 문법 필수 (mhchem)

## 📚 참고 자료

- [MathML Spec](https://www.w3.org/TR/MathML3/)
- [MathJax Documentation](https://docs.mathjax.org/)
- [mhchem](https://mhchem.github.io/MathJax-mhchem/)
- [Speech Rule Engine](https://github.com/zorkow/speech-rule-engine)
