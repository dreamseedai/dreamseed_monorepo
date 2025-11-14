# LLM 스마트 라우팅 시스템

Accept-Language 기반 자동 언어 감지 및 최적 모델 라우팅 시스템.

## 개요

DreamSeedAI의 멀티언어 서비스에서 **요청별로 가장 알맞은 LLM 모델로 자동 라우팅**하는 시스템입니다.

### 라우팅 정책

| 언어 | 모델 | 위치 | 지연시간 | 비용 |
|------|------|------|---------|------|
| 한국어 (ko) | Qwen2.5-7B-Instruct | 로컬 RTX 5090 | ~200ms | $0 |
| 영어 (en) | Llama-3.1-8B-Instruct | 로컬 RTX 5090 | ~250ms | $0 |
| 중국어 간체 (zh-Hans) | deepseek-chat | DeepSeek 클라우드 | ~500ms | ~$0.00012/메시지 |
| 중국어 번체 (zh-Hant) | deepseek-chat | DeepSeek 클라우드 | ~500ms | ~$0.00012/메시지 |

### 주요 기능

1. **Accept-Language 우선 감지**: 브라우저 설정을 최우선으로 사용
2. **다단계 폴백**: 강제 지정 → Accept-Language → 쿠키 → JWT → 기본값
3. **자동 모델 선택**: 언어별 최적 모델/엔드포인트 자동 선택
4. **폴백 메커니즘**: 클라우드 장애 시 로컬 모델로 자동 전환
5. **투명한 관측성**: X-Resolved-Lang 헤더로 감지된 언어 확인

## 아키텍처

```
┌─────────────┐
│   Browser   │ Accept-Language: ko-KR,ko;q=0.9,en;q=0.8
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│        LangRouteMiddleware                      │
│  1. Accept-Language 파싱                        │
│  2. 우선순위 기반 언어 감지                      │
│  3. request.state.route_lang 저장               │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│        SmartRouter                              │
│  - ko, en → 로컬 LLM (RTX 5090)                 │
│  - zh-Hans, zh-Hant → DeepSeek 클라우드         │
└──────┬──────────────────────────────────────────┘
       │
       ├─────────────┬──────────────┐
       ▼             ▼              ▼
   ┌────────┐  ┌─────────┐   ┌──────────┐
   │ Local  │  │ Local   │   │ DeepSeek │
   │ Ko/En  │  │ Ko/En   │   │  Cloud   │
   └────────┘  └─────────┘   └──────────┘
```

## 설치 및 설정

### 1. 환경 변수 설정

```bash
# .env 파일
# 로컬 LLM 서버 (RTX 5090)
LLM_BASE_URL_LOCAL=http://127.0.0.1:8001/v1
LLM_API_KEY_LOCAL=sk-local

# DeepSeek 클라우드
LLM_BASE_URL_DEEPSEEK=https://api.deepseek.com/v1
LLM_API_KEY_DEEPSEEK=sk-your-deepseek-key

# 언어별 모델
LLM_MODEL_KO=Qwen2.5-7B-Instruct
LLM_MODEL_EN=Llama-3.1-8B-Instruct
LLM_MODEL_ZH=deepseek-chat

# 기본 설정
DEFAULT_LANG=ko
LLM_TIMEOUT=8.0
LLM_MAX_TOKENS=200
```

### 2. FastAPI 앱에 미들웨어 추가

```python
from fastapi import FastAPI
from shared.llm.middleware import LangRouteMiddleware

app = FastAPI()

# 미들웨어 추가
app.add_middleware(LangRouteMiddleware)
```

### 3. 라우터에서 사용

```python
from fastapi import Request
from shared.llm.smart_router import smart_chat_from_request

@app.post("/api/chat")
async def chat(request: Request, message: str):
    """
    자동 언어 감지 및 라우팅 채팅 엔드포인트.
    """
    response = await smart_chat_from_request(
        request=request,
        system="You are a helpful assistant",
        user=message
    )
    return {"response": response}
```

## 사용 예시

### 예시 1: 자동 라우팅 (미들웨어 사용)

```python
from fastapi import Request
from shared.llm.smart_router import smart_chat_from_request

@app.post("/chat")
async def chat(request: Request, body: dict):
    # request.state.route_lang에서 자동 감지된 언어 사용
    response = await smart_chat_from_request(
        request=request,
        system="You are a helpful assistant",
        user=body["message"]
    )
    return {"response": response}
```

### 예시 2: 수동 언어 지정

```python
from shared.llm.smart_router import smart_chat

@app.post("/chat/{lang}")
async def chat(lang: str, message: str):
    # 언어 직접 지정
    response = await smart_chat(
        lang=lang,  # 'ko', 'en', 'zh-Hans', 'zh-Hant'
        system="You are a helpful assistant",
        user=message
    )
    return {"response": response}
```

### 예시 3: 언어 감지만 사용

```python
from fastapi import Request
from shared.llm.middleware import get_request_language

@app.get("/language")
async def get_language(request: Request):
    lang = get_request_language(request)
    return {"detected_language": lang}
```

## 언어 감지 우선순위

1. **강제 언어** (최우선)
   - 쿼리 파라미터: `?lang=zh-Hans`
   - 헤더: `X-Lang: ko`

2. **Accept-Language 헤더** (권장)
   - 브라우저 설정: `Accept-Language: ko-KR,ko;q=0.9,en;q=0.8`

3. **쿠키**
   - `lang=en`

4. **JWT 클레임**
   - `{"pref_lang": "zh-Hans"}`

5. **기본값**
   - `ko` (환경변수 `DEFAULT_LANG`로 변경 가능)

## 테스트

### 테스트 1: 한국어 브라우저

```bash
curl -X POST http://localhost:8000/chat \
  -H "Accept-Language: ko-KR,ko;q=0.9" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요!"}'

# 응답 헤더: X-Resolved-Lang: ko
# 라우팅: 로컬 Qwen2.5-7B-Instruct
```

### 테스트 2: 중국어 브라우저

```bash
curl -X POST http://localhost:8000/chat \
  -H "Accept-Language: zh-Hans,zh;q=0.9" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好！"}'

# 응답 헤더: X-Resolved-Lang: zh-Hans
# 라우팅: DeepSeek 클라우드
```

### 테스트 3: 강제 언어 지정

```bash
curl -X POST "http://localhost:8000/chat?lang=en" \
  -H "Accept-Language: ko-KR,ko;q=0.9" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# 응답 헤더: X-Resolved-Lang: en
# 라우팅: 로컬 Llama-3.1-8B-Instruct
# (Accept-Language는 ko지만 강제 지정이 우선)
```

### 테스트 4: 폴백 메커니즘

```bash
# DeepSeek 장애 시뮬레이션 (잘못된 API 키)
export LLM_API_KEY_DEEPSEEK=invalid-key

curl -X POST http://localhost:8000/chat \
  -H "Accept-Language: zh-Hans" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好！"}'

# 로그: "Cloud API failed for zh-Hans, falling back to local"
# 라우팅: 로컬 Qwen2.5-7B-Instruct (폴백)
```

## 성능 최적화

### 1. 캐싱 (선택)

동일 프롬프트 결과를 단기 캐시하여 비용 절감:

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_cache_key(system: str, user: str) -> str:
    return hashlib.sha256(f"{system}:{user}".encode()).hexdigest()[:16]
```

### 2. 로컬 서버 최적화

```bash
# vLLM 서버 시작 (RTX 5090)
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --host 0.0.0.0 \
  --port 8001 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.9
```

### 3. 관측성

```python
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shared.llm.smart_router")

# 로그 예시:
# INFO: Routing to local (lang=ko, model=Qwen2.5-7B-Instruct)
# INFO: Routing to cloud (lang=zh-Hans, model=deepseek-chat)
# WARNING: Cloud API failed for zh-Hans, falling back to local
```

## 체크리스트

- [ ] 로컬 LLM 서버 실행 (RTX 5090)
- [ ] DeepSeek API 키 설정
- [ ] 환경 변수 설정 (.env)
- [ ] FastAPI 앱에 미들웨어 추가
- [ ] 한국어 브라우저 테스트
- [ ] 중국어 브라우저 테스트
- [ ] 강제 언어 지정 테스트
- [ ] 폴백 메커니즘 테스트
- [ ] 응답 헤더 X-Resolved-Lang 확인
- [ ] 로그 확인 (라우팅 정보)

## 문제 해결

### Q1: "X-Resolved-Lang 헤더가 없어요"
**A**: `LangRouteMiddleware`가 FastAPI 앱에 추가되었는지 확인하세요.

```python
app.add_middleware(LangRouteMiddleware)
```

### Q2: "항상 기본 언어(ko)로 감지돼요"
**A**: Accept-Language 헤더가 올바르게 전송되는지 확인하세요.

```bash
curl -v http://localhost:8000/chat \
  -H "Accept-Language: zh-Hans"
```

### Q3: "DeepSeek API 에러가 발생해요"
**A**: API 키가 올바른지 확인하세요.

```bash
echo $LLM_API_KEY_DEEPSEEK
# 또는
grep LLM_API_KEY_DEEPSEEK .env
```

### Q4: "폴백이 작동하지 않아요"
**A**: `SmartRouter`의 `enable_fallback=True`인지 확인하세요 (기본값).

## 참고 자료

- [FastAPI 미들웨어](https://fastapi.tiangolo.com/advanced/middleware/)
- [Accept-Language 헤더](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Language)
- [vLLM OpenAI API](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html)
- [DeepSeek API](https://platform.deepseek.com/api-docs/)

## 관련 파일

- `shared/llm/lang_detect.py`: 언어 감지 유틸리티
- `shared/llm/middleware.py`: FastAPI 미들웨어
- `shared/llm/smart_router.py`: 스마트 라우터
- `shared/llm/openai_compat.py`: OpenAI 호환 클라이언트
- `shared/config/llm.py`: LLM 설정
