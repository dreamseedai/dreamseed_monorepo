# LLM 스마트 라우팅 통합 가이드

모든 FastAPI 백엔드 서비스에 LLM 스마트 라우팅을 적용하는 가이드입니다.

## 빠른 시작 (5분)

### 1. 미들웨어 추가

```python
# app/main.py
from fastapi import FastAPI
from shared.llm import LangRouteMiddleware

app = FastAPI()

# 미들웨어 등록 (다른 미들웨어보다 먼저 등록 권장)
app.add_middleware(LangRouteMiddleware)
```

### 2. 라우터에서 사용

```python
# app/routers/chat.py
from fastapi import APIRouter, Request
from shared.llm import smart_chat_from_request

router = APIRouter(prefix="/v1", tags=["chat"])

@router.post("/chat")
async def chat(request: Request, message: str):
    """
    자동 언어 감지 채팅 엔드포인트.
    
    Accept-Language 헤더 또는 X-Lang 헤더로 언어 자동 감지.
    """
    response = await smart_chat_from_request(
        request=request,
        system="You are a helpful assistant",
        user=message
    )
    return {"response": response}
```

### 3. 환경 변수 설정

```bash
# .env
# 로컬 LLM 서버
LOCAL_KO_URL=http://127.0.0.1:9001/v1/chat/completions
LOCAL_EN_URL=http://127.0.0.1:9002/v1/chat/completions

# DeepSeek 클라우드
DEEPSEEK_API_KEY=sk-your-deepseek-key

# 기본 언어
DEFAULT_LANG=ko
```

## 전체 통합 예시

### apps/seedtest_api 적용 예시

#### 1. 미들웨어 추가

```python
# apps/seedtest_api/app/main.py
from fastapi import FastAPI
from shared.llm import LangRouteMiddleware

app = FastAPI(title="SeedTest API")

# 기존 미들웨어
app.add_middleware(CorrelationIdMiddleware)

# LLM 라우팅 미들웨어 추가
app.add_middleware(LangRouteMiddleware)
```

#### 2. 채팅 라우터 생성

```python
# apps/seedtest_api/app/routers/llm_chat.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from shared.llm import smart_chat_from_request, get_request_language

router = APIRouter(prefix="/api/v1/llm", tags=["LLM"])

class ChatRequest(BaseModel):
    message: str
    system: str = "You are a helpful educational assistant"
    max_tokens: int = 200
    temperature: float = 0.7

class ChatResponse(BaseModel):
    response: str
    detected_language: str
    model_type: str  # 'local' or 'cloud'

@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    """
    자동 언어 감지 채팅.
    
    Headers:
        - Accept-Language: 브라우저 언어 설정
        - X-Lang: 강제 언어 지정 (ko, en, zh-Hans, zh-Hant)
    
    Query:
        - ?lang=ko: 강제 언어 지정
    """
    lang = get_request_language(request)
    
    try:
        response = await smart_chat_from_request(
            request=request,
            system=body.system,
            user=body.message,
            max_tokens=body.max_tokens,
            temperature=body.temperature
        )
        
        return ChatResponse(
            response=response,
            detected_language=lang,
            model_type="cloud" if lang.startswith("zh-") else "local"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM API error: {str(e)}"
        )

@router.get("/language")
async def get_language(request: Request):
    """현재 감지된 언어 확인"""
    lang = get_request_language(request)
    return {
        "detected_language": lang,
        "accept_language": request.headers.get("accept-language"),
        "x_lang": request.headers.get("x-lang"),
        "model_type": "cloud" if lang.startswith("zh-") else "local"
    }
```

#### 3. 라우터 등록

```python
# apps/seedtest_api/app/main.py
from .routers.llm_chat import router as llm_chat_router

app.include_router(llm_chat_router)
```

### backend/ 서비스 적용

동일한 패턴으로 적용:

```python
# backend/app/main.py
from fastapi import FastAPI
from shared.llm import LangRouteMiddleware

app = FastAPI()
app.add_middleware(LangRouteMiddleware)

# 라우터 추가
from .routers import chat
app.include_router(chat.router)
```

### governance/ 서비스 적용

```python
# governance/backend/main.py
from fastapi import FastAPI
from shared.llm import LangRouteMiddleware

app = FastAPI()
app.add_middleware(LangRouteMiddleware)
```

## 고급 사용법

### 1. 수동 언어 지정

```python
from shared.llm import smart_chat

@app.post("/chat/{lang}")
async def chat_with_lang(lang: str, message: str):
    """언어를 URL 경로로 직접 지정"""
    response = await smart_chat(
        lang=lang,  # 'ko', 'en', 'zh-Hans', 'zh-Hant'
        system="You are a helpful assistant",
        user=message
    )
    return {"response": response}
```

### 2. 텍스트 기반 언어 감지

```python
from shared.llm import detect_from_text

@app.post("/analyze-language")
async def analyze_language(text: str, request: Request):
    """텍스트 샘플에서 언어 감지"""
    browser_hint = request.headers.get("accept-language")
    detected_lang = detect_from_text(text, browser_hint=browser_hint)
    
    return {
        "text": text[:100],  # 샘플
        "detected_language": detected_lang,
        "browser_hint": browser_hint
    }
```

### 3. 프로바이더 직접 호출

```python
from shared.llm.providers import call_local_ko, call_deepseek

@app.post("/chat/local")
async def chat_local(message: str):
    """로컬 LLM 직접 호출"""
    body = {
        "model": "Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": message}
        ],
        "max_tokens": 200
    }
    response = await call_local_ko(body)
    return response

@app.post("/chat/deepseek")
async def chat_deepseek(message: str):
    """DeepSeek 클라우드 직접 호출"""
    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个有帮助的助手"},
            {"role": "user", "content": message}
        ],
        "max_tokens": 200
    }
    response = await call_deepseek(body)
    return response
```

## 테스트

### 1. 로컬 테스트

```bash
# 한국어 브라우저
curl -X POST http://localhost:8000/api/v1/llm/chat \
  -H "Accept-Language: ko-KR,ko;q=0.9" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요!"}'

# 중국어 브라우저
curl -X POST http://localhost:8000/api/v1/llm/chat \
  -H "Accept-Language: zh-Hans,zh;q=0.9" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好！"}'

# 강제 언어 지정
curl -X POST "http://localhost:8000/api/v1/llm/chat?lang=en" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

### 2. 응답 헤더 확인

```bash
curl -v http://localhost:8000/api/v1/llm/language \
  -H "Accept-Language: zh-Hans"

# 응답 헤더에서 확인:
# X-Resolved-Lang: zh-Hans
```

## 체크리스트

각 서비스별로 다음 항목을 확인하세요:

- [ ] `LangRouteMiddleware` 추가
- [ ] 환경 변수 설정 (LOCAL_KO_URL, LOCAL_EN_URL, DEEPSEEK_API_KEY)
- [ ] 채팅 라우터 구현
- [ ] 로컬 테스트 (한국어, 영어, 중국어)
- [ ] 응답 헤더 `X-Resolved-Lang` 확인
- [ ] 에러 핸들링 (LLM API 장애 시)
- [ ] 로깅 설정 (언어 감지 및 라우팅 로그)

## 서비스별 적용 상태

| 서비스 | 포트 | 상태 | 비고 |
|--------|------|------|------|
| portal_front | 5172 | ✅ 완료 | 프론트엔드 (X-Lang 헤더 자동 추가) |
| seedtest_api | 8000 | 🔄 진행 중 | 메인 API |
| backend | 8001 | ⏳ 대기 | |
| governance | 8002 | ⏳ 대기 | |
| analytics | 8003 | ⏳ 대기 | |
| ... | ... | ⏳ 대기 | |

## 문제 해결

### Q1: "X-Resolved-Lang 헤더가 없어요"
**A**: 미들웨어가 등록되었는지 확인하세요.

```python
app.add_middleware(LangRouteMiddleware)
```

### Q2: "DeepSeek API 에러"
**A**: API 키가 설정되었는지 확인하세요.

```bash
echo $DEEPSEEK_API_KEY
# 또는
grep DEEPSEEK_API_KEY .env
```

### Q3: "로컬 LLM 연결 실패"
**A**: 로컬 서버가 실행 중인지 확인하세요.

```bash
curl http://127.0.0.1:9001/v1/models
```

## 참고 문서

- [LLM_SMART_ROUTING.md](./LLM_SMART_ROUTING.md) - 상세 기술 문서
- [shared/llm/README.md](../shared/llm/README.md) - 모듈 사용법
