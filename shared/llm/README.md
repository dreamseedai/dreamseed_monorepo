# LLM 스마트 라우팅 시스템

Accept-Language 기반 자동 언어 감지 및 최적 모델 라우팅 시스템.

## 빠른 시작

### 1. FastAPI 앱에 미들웨어 추가

```python
from fastapi import FastAPI
from shared.llm import LangRouteMiddleware

app = FastAPI()
app.add_middleware(LangRouteMiddleware)
```

### 2. 자동 라우팅 사용

```python
from fastapi import Request
from shared.llm import smart_chat_from_request

@app.post("/chat")
async def chat(request: Request, message: str):
    response = await smart_chat_from_request(
        request=request,
        system="You are a helpful assistant",
        user=message
    )
    return {"response": response}
```

### 3. 수동 언어 지정

```python
from shared.llm import smart_chat

@app.post("/chat/{lang}")
async def chat(lang: str, message: str):
    response = await smart_chat(
        lang=lang,  # 'ko', 'en', 'zh-Hans', 'zh-Hant'
        system="You are a helpful assistant",
        user=message
    )
    return {"response": response}
```

## 라우팅 정책

| 언어 | 모델 | 위치 | 지연시간 |
|------|------|------|---------|
| ko | Qwen2.5-7B-Instruct | 로컬 RTX 5090 | ~200ms |
| en | Llama-3.1-8B-Instruct | 로컬 RTX 5090 | ~250ms |
| zh-Hans | deepseek-chat | DeepSeek 클라우드 | ~500ms |
| zh-Hant | deepseek-chat | DeepSeek 클라우드 | ~500ms |

## 환경 변수

```bash
# 로컬 LLM 서버
LLM_BASE_URL_LOCAL=http://127.0.0.1:8001/v1
LLM_API_KEY_LOCAL=sk-local

# DeepSeek 클라우드
LLM_BASE_URL_DEEPSEEK=https://api.deepseek.com/v1
LLM_API_KEY_DEEPSEEK=sk-your-key

# 모델 설정
LLM_MODEL_KO=Qwen2.5-7B-Instruct
LLM_MODEL_EN=Llama-3.1-8B-Instruct
LLM_MODEL_ZH=deepseek-chat

# 기본 설정
DEFAULT_LANG=ko
LLM_TIMEOUT=8.0
LLM_MAX_TOKENS=200
```

## 테스트

```bash
# 유닛 테스트
python ops/scripts/test_smart_routing.py

# 샘플 앱 실행
python ops/scripts/example_smart_routing_app.py

# API 테스트
./ops/scripts/test_smart_routing_api_sample.sh
```

## 모듈 구조

```
shared/llm/
├── __init__.py              # 모듈 export
├── lang_detect.py           # 언어 감지 유틸리티
├── middleware.py            # FastAPI 미들웨어
├── smart_router.py          # 스마트 라우터
├── openai_compat.py         # OpenAI 호환 클라이언트
└── README.md                # 이 파일
```

## 상세 문서

전체 문서는 [docs/LLM_SMART_ROUTING.md](../../docs/LLM_SMART_ROUTING.md)를 참조하세요.
