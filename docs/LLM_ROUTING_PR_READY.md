# LLM 스마트 라우팅 - PR Ready 버전

**전역 통합용 Monorepo PR** - 모든 백엔드 서비스에 즉시 적용 가능

## 📋 변경 사항 요약

### ✅ 완료된 작업

#### 1. **shared/llm 모듈 개선**
- ✅ `types.py` - 공통 타입 및 상수
- ✅ `providers.py` - LLM 프로바이더 어댑터 (로컬/DeepSeek)
- ✅ `lang_detect.py` - 혼합 언어 감지 추가 (char-gram 비율)
- ✅ `middleware.py` - FastAPI 미들웨어
- ✅ `smart_router.py` - 스마트 라우터
- ✅ `__init__.py` - export 업데이트

#### 2. **portal_front 프론트엔드**
- ✅ `src/lib/langDetect.ts` - 브라우저 언어 감지
- ✅ `src/api.ts` - X-Lang 헤더 자동 추가

#### 3. **문서 및 테스트**
- ✅ `docs/LLM_SMART_ROUTING.md` - 상세 기술 문서
- ✅ `docs/LLM_INTEGRATION_GUIDE.md` - 통합 가이드
- ✅ `ops/scripts/test_smart_routing.py` - 유닛 테스트
- ✅ `ops/scripts/test_lang_routing_all.sh` - 통합 테스트
- ✅ `.github/PULL_REQUEST_TEMPLATE/lang_routing.md` - PR 템플릿

## 🗂️ 파일 트리

```
dreamseed_monorepo/
├── shared/
│   └── llm/
│       ├── __init__.py              # ✨ 업데이트
│       ├── types.py                 # 🆕 추가
│       ├── providers.py             # 🆕 추가
│       ├── lang_detect.py           # ✨ 혼합 언어 감지 추가
│       ├── middleware.py            # ✅ 기존
│       ├── smart_router.py          # ✅ 기존
│       └── openai_compat.py         # ✅ 기존
│
├── portal_front/
│   └── src/
│       ├── lib/
│       │   └── langDetect.ts        # 🆕 추가
│       └── api.ts                   # ✨ X-Lang 헤더 추가
│
├── ops/
│   └── scripts/
│       ├── test_smart_routing.py    # ✅ 기존
│       └── test_lang_routing_all.sh # 🆕 추가
│
├── docs/
│   ├── LLM_SMART_ROUTING.md         # ✅ 기존
│   ├── LLM_INTEGRATION_GUIDE.md     # 🆕 추가
│   └── LLM_ROUTING_PR_READY.md      # 🆕 이 파일
│
└── .github/
    └── PULL_REQUEST_TEMPLATE/
        └── lang_routing.md          # 🆕 추가
```

## 🚀 즉시 적용 방법

### 1단계: 환경 변수 설정

```bash
# .env 파일에 추가
# 로컬 LLM 서버
LOCAL_KO_URL=http://127.0.0.1:9001/v1/chat/completions
LOCAL_EN_URL=http://127.0.0.1:9002/v1/chat/completions

# DeepSeek 클라우드
DEEPSEEK_API_KEY=sk-your-deepseek-key

# 기본 언어
DEFAULT_LANG=ko
```

### 2단계: FastAPI 서비스에 미들웨어 추가

```python
# apps/seedtest_api/app/main.py (또는 다른 서비스)
from fastapi import FastAPI
from shared.llm import LangRouteMiddleware

app = FastAPI()

# 미들웨어 등록 (한 줄만 추가!)
app.add_middleware(LangRouteMiddleware)
```

### 3단계: 채팅 라우터 추가 (선택)

```python
# apps/seedtest_api/app/routers/llm_chat.py
from fastapi import APIRouter, Request
from shared.llm import smart_chat_from_request, get_request_language

router = APIRouter(prefix="/api/v1/llm", tags=["LLM"])

@router.post("/chat")
async def chat(request: Request, message: str):
    response = await smart_chat_from_request(
        request=request,
        system="You are a helpful assistant",
        user=message
    )
    lang = get_request_language(request)
    return {
        "response": response,
        "detected_language": lang
    }
```

### 4단계: 테스트

```bash
# 유닛 테스트
python ops/scripts/test_smart_routing.py

# 통합 테스트 (모든 서비스)
./ops/scripts/test_lang_routing_all.sh

# 수동 테스트
curl -X POST http://localhost:8000/api/v1/llm/chat \
  -H "Accept-Language: ko-KR,ko;q=0.9" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요!"}'
```

## 📊 라우팅 정책

| 언어 | 모델 | 위치 | 지연시간 | 비용 |
|------|------|------|---------|------|
| ko | Qwen2.5-7B-Instruct | 로컬 RTX 5090 | ~200ms | $0 |
| en | Llama-3.1-8B-Instruct | 로컬 RTX 5090 | ~250ms | $0 |
| zh-Hans | deepseek-chat | DeepSeek 클라우드 | ~500ms | ~$0.00012/메시지 |
| zh-Hant | deepseek-chat | DeepSeek 클라우드 | ~500ms | ~$0.00012/메시지 |

## 🎯 우선순위 정책

언어 감지 우선순위:
1. **강제 언어** (쿼리 `?lang=` 또는 헤더 `X-Lang`)
2. **Accept-Language** 헤더 (브라우저 설정)
3. **쿠키** (`lang`)
4. **JWT 클레임** (`pref_lang`)
5. **기본값** (`ko`)

## 🔧 서비스별 적용 상태

| 서비스 | 포트 | 상태 | 비고 |
|--------|------|------|------|
| portal_front | 5172 | ✅ 완료 | 프론트엔드 (X-Lang 헤더 자동) |
| seedtest_api | 8000 | 🔄 적용 대기 | 메인 API |
| backend | 8001 | ⏳ 적용 대기 | |
| governance | 8002 | ⏳ 적용 대기 | |
| analytics | 8003 | ⏳ 적용 대기 | |

## ✅ 테스트 체크리스트

### 유닛 테스트
- [x] Accept-Language 파싱
- [x] 언어 코드 정규화
- [x] 언어 감지 우선순위
- [x] 혼합 언어 감지
- [x] 라우팅 결정

### 통합 테스트
- [ ] 한국어 브라우저 → 로컬 ko 모델
- [ ] 영어 브라우저 → 로컬 en 모델
- [ ] 중국어 간체 → DeepSeek
- [ ] 중국어 번체 → DeepSeek
- [ ] 강제 언어 지정 (?lang=)
- [ ] X-Lang 헤더 지정
- [ ] X-Resolved-Lang 응답 확인

### 성능 테스트
- [ ] 로컬 모델 지연시간 < 300ms
- [ ] 클라우드 모델 지연시간 < 1s
- [ ] 폴백 메커니즘 동작 확인

## 📚 문서

- **기술 문서**: [docs/LLM_SMART_ROUTING.md](./LLM_SMART_ROUTING.md)
- **통합 가이드**: [docs/LLM_INTEGRATION_GUIDE.md](./LLM_INTEGRATION_GUIDE.md)
- **모듈 README**: [shared/llm/README.md](../shared/llm/README.md)

## 🔐 보안 고려사항

1. **API 키 관리**
   - DeepSeek API 키는 환경 변수로 관리
   - Secret Manager 사용 (프로덕션)
   - 로그에 API 키 노출 금지

2. **에러 핸들링**
   - LLM API 장애 시 폴백
   - 타임아웃 설정 (기본 60초)
   - 에러 로깅 (민감 정보 제외)

## 🚦 배포 계획

### DEV
1. 환경 변수 설정
2. 로컬 LLM 서버 실행
3. 서비스 재시작
4. 테스트 실행

### STAGING
1. 환경 변수 설정 (Secret Manager)
2. 서비스 재시작
3. 통합 테스트
4. 성능 모니터링

### PRODUCTION
1. 카나리 배포 (10% → 50% → 100%)
2. 모니터링 (에러율, 지연시간, 비용)
3. 롤백 계획 준비
4. 알림 설정 (Slack/PagerDuty)

## 📈 모니터링

### 메트릭
- `llm_request_total` - 총 요청 수
- `llm_request_duration_seconds` - 요청 지연시간
- `llm_request_errors_total` - 에러 수
- `llm_detected_language` - 감지된 언어 분포
- `llm_provider_usage` - 프로바이더별 사용량

### 알림
- 에러율 > 5%
- 지연시간 > 2초 (P95)
- DeepSeek 비용 > $10/일

## 🎉 완료!

이제 **복붙-커밋-배포**만 하면 됩니다!

```bash
# 1. 테스트
python ops/scripts/test_smart_routing.py

# 2. 커밋
git add .
git commit -m "feat: Add LLM smart routing with Accept-Language support"

# 3. PR 생성
# .github/PULL_REQUEST_TEMPLATE/lang_routing.md 템플릿 사용

# 4. 배포
# CI/CD 파이프라인 실행
```

## 📞 문의

문제가 발생하면 다음 문서를 참조하세요:
- [LLM_INTEGRATION_GUIDE.md](./LLM_INTEGRATION_GUIDE.md) - 통합 가이드
- [LLM_SMART_ROUTING.md](./LLM_SMART_ROUTING.md) - 기술 문서
