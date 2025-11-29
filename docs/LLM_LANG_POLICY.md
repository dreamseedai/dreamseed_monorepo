# LLM 언어 정책

## 지원 언어

- **ko**: 한국어
- **en**: 영어
- **zh-Hans**: 중국어 간체
- **zh-Hant**: 중국어 번체

## 라우팅 정책

### 모델 선택

| 언어 | 모델 | 위치 | 지연시간 | 비용 |
|------|------|------|---------|------|
| ko | Qwen2.5-7B-Instruct | 로컬 RTX 5090 | ~200ms | $0 |
| en | Llama-3.1-8B-Instruct | 로컬 RTX 5090 | ~250ms | $0 |
| zh-Hans | deepseek-chat | DeepSeek 클라우드 | ~500ms | ~$0.00012/메시지 |
| zh-Hant | deepseek-chat | DeepSeek 클라우드 | ~500ms | ~$0.00012/메시지 |

### 우선순위

1. **강제 언어** (최우선)
   - 쿼리 파라미터: `?lang=ko`
   - HTTP 헤더: `X-Lang: zh-Hans`

2. **Accept-Language 헤더** (권장)
   - 브라우저 설정: `Accept-Language: ko-KR,ko;q=0.9,en;q=0.8`

3. **쿠키**
   - `lang=en`

4. **JWT 클레임**
   - `{"pref_lang": "zh-Hans"}`

5. **기본값**
   - `ko`

## 혼합 언어 처리

### 간단 모드 (기본)

문자 비율 기반으로 대표 언어 결정:

```python
from shared.llm import detect_from_text

text = "이 문장은 한국어. This is English. 这是中文。"
lang = detect_from_text(text, browser_hint="ko-KR")
# → 'ko' (한글 비율이 가장 높음)
```

### 정밀 모드 (선택)

문장 단위로 분할하여 각각 라우팅 (비용 증가):

```python
# 구현 예정
sentences = split_by_language(text)
for sentence, lang in sentences:
    response = await smart_chat(lang, system, sentence)
```

## 장애 폴백

### DeepSeek 장애 시

중국어 요청이 DeepSeek 장애로 실패하면 로컬 영어 모델로 폴백:

```python
try:
    response = await call_deepseek(body)
except Exception:
    # 로컬 EN으로 폴백
    response = await call_local_en(body)
```

### 로컬 모델 장애 시

로컬 모델 장애 시 에러 반환 (폴백 없음):

```python
try:
    response = await call_local_ko(body)
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

## 비용 최적화

### 캐싱

동일 프롬프트 결과를 단기 캐시 (5-30초):

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_cache_key(system: str, user: str) -> str:
    return hashlib.sha256(f"{system}:{user}".encode()).hexdigest()[:16]
```

### 배치 처리

여러 요청을 배치로 처리하여 비용 절감:

```python
# 구현 예정
responses = await batch_chat(requests)
```

## 관측성

### 응답 헤더

모든 응답에 감지된 언어 포함:

```
X-Resolved-Lang: ko
```

### 로깅

언어 감지 및 라우팅 로그:

```
INFO: Routing to local (lang=ko, model=Qwen2.5-7B-Instruct)
INFO: Routing to cloud (lang=zh-Hans, model=deepseek-chat)
WARNING: Cloud API failed for zh-Hans, falling back to local
```

### 메트릭

- `llm_request_total{lang, provider}` - 총 요청 수
- `llm_request_duration_seconds{lang, provider}` - 요청 지연시간
- `llm_request_errors_total{lang, provider}` - 에러 수
- `llm_cost_total{provider}` - 총 비용

## 보안

### API 키 관리

- DeepSeek API 키는 환경 변수로 관리
- Secret Manager 사용 (프로덕션)
- 로그에 API 키 노출 금지

### 에러 메시지

- 사용자에게 민감 정보 노출 금지
- 내부 에러는 로그에만 기록

## 참고 문서

- [LLM_SMART_ROUTING.md](./LLM_SMART_ROUTING.md) - 기술 문서
- [LLM_INTEGRATION_GUIDE.md](./LLM_INTEGRATION_GUIDE.md) - 통합 가이드
