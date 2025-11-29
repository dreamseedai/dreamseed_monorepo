# Continue 설정 가이드 (DreamSeedAI 프로젝트)

## 📋 개요

본 프로젝트는 **Gemini 2.0 Flash를 기본 모델**로 사용하여 빠른 개발 속도를 확보하고, 복잡한 작업에는 **Gemini 1.5 Pro**를 활용하는 전략을 채택합니다.

## 🚀 빠른 시작

### 1. 환경 변수 설정

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export GEMINI_API_KEY="your-gemini-api-key-here"
export ANTHROPIC_API_KEY="your-anthropic-key"  # Claude 사용 시
export OPENAI_API_KEY="your-openai-key"  # GPT 사용 시

# 적용
source ~/.bashrc
```

### 2. Continue 재시작

- VS Code에서 `Ctrl+Shift+P` → "Developer: Reload Window"
- 또는 Continue 확장 아이콘 클릭 → 모델 드롭다운에서 "Gemini 2.0 Flash" 확인

### 3. 테스트

Continue 채팅창에서:
```
안녕하세요! Gemini 2.0 Flash 모델로 연결되었나요?
```

---

## 🎯 모델 선택 전략

| 작업 유형 | 추천 모델 | 컨텍스트 | 속도 | 사용 예시 |
|----------|----------|---------|------|----------|
| **기본 작업** | Gemini 2.0 Flash | 1M | ⚡⚡⚡ | API 스켈레톤, UI 컴포넌트, 간단한 수정 |
| **복잡한 추론** | Gemini 1.5 Pro | 2M | ⚡⚡ | 상세 설계, 대규模 리팩터링, IRT 알고리즘 |
| **수학/알고리즘** | GPT-o1 | 128K | ⚡ | 복잡한 알고리즘, 수학 증명, 디버깅 |
| **코드 품질** | Claude Sonnet 4.5 | 200K | ⚡⚡ | 테스트 작성, 프로덕션 코드 리뷰 |
| **범용** | GPT-4o | 128K | ⚡⚡ | 문서화, 일반 코딩 |
| **자동완성** | Local Qwen2.5 | 32K | ⚡⚡⚡ | 실시간 코드 제안 (오프라인) |

### 모델 전환 방법

1. **Continue 채팅창 상단** 모델 드롭다운 클릭
2. 원하는 모델 선택
3. 또는 슬래시 명령어 사용:
   - `/flash` - Gemini 2.0 Flash로 전환
   - `/pro` - Gemini 1.5 Pro로 전환

---

## 💡 슬래시 명령어 (/prompts)

### 일반 명령어

| 명령어 | 설명 | 사용 예시 |
|-------|------|----------|
| `/ko` | 한국어 답변 고정 | 기획/분석 문서 작성 |
| `/zh` | 중국어 우선 | 중국 시장 대응 |
| `/flash` | Gemini 2.0 Flash로 빠른 작업 | UI/API/단순 수정 |
| `/pro` | Gemini 1.5 Pro로 복잡한 추론 | 리팩터/분석/설계 |
| `/local` | 로컬 모델로 코드 요약 | 오프라인 작업 |

### DreamSeed 전용 명령어

| 명령어 | 설명 | 출력 |
|-------|------|------|
| `/dreamseed-design` | 상세 설계 문서 작성 | 기능 개요, ERD, API 설계, 알고리즘 |
| `/dreamseed-api` | FastAPI 엔드포인트 스켈레톤 | Pydantic 모델, SQLAlchemy 쿼리, 에러 핸들링 |
| `/dreamseed-irt` | IRT/CAT 알고리즘 구현 | 3PL 모델, Bayesian 추정, DIF 분석 |
| `/refactor` | 다중 파일 리팩터 계획 | 영향 범위, 단계별 패치, 테스트 명령 |
| `/tests` | 테스트 보일러플레이트 생성 | pytest + FastAPI TestClient |
| `/perf` | 성능 최적화 체크리스트 | 쿼리 최적화, 캐싱 전략, 벤치마크 |

---

## 📚 실전 사용 예시

### 예시 1: API 엔드포인트 생성 (빠른 작업)

**현재 모델**: Gemini 2.0 Flash (기본)

```
/dreamseed-api

다음 요구사항으로 FastAPI 엔드포인트를 생성해주세요:
- 경로: GET /api/v1/irt-drift/alerts
- 파라미터: severity (optional), resolved (bool)
- 응답: 드리프트 알림 목록 (item_id, metric, value, severity)
- DB: PostgreSQL drift_alerts 테이블
```

**결과**: Pydantic 스키마 + SQLAlchemy 쿼리 + 에러 핸들링 코드 즉시 생성 ⚡

---

### 예시 2: IRT 드리프트 알고리즘 설계 (복잡한 추론)

**모델 전환**: Gemini 1.5 Pro (드롭다운 또는 `/pro` 입력)

```
/dreamseed-irt

IRT 드리프트 모니터링 시스템을 설계해주세요:
1. Anchor-based equating (σ²=0.05 for anchors, 0.25 for non-anchors)
2. Bayesian 3PL estimation (PyMC 또는 brms)
3. DIF 분석 (gender, grade, language, school)
4. 드리프트 감지 thresholds (Δb=0.25, Δa=0.2, Δc=0.03)

전체 아키텍처와 단계별 구현 계획을 제시해주세요.
```

**결과**: 수학적 근거 + 전체 시스템 설계 + 구현 단계 + 코드 예시 📊

---

### 예시 3: 대규모 리팩터링 (긴 컨텍스트)

**모델**: Gemini 1.5 Pro

```
/refactor

다음 파일들을 분석하고 리팩터링 계획을 세워주세요:
- apps/seedtest_api/routers/attempts.py (500줄)
- apps/seedtest_api/models/attempt.py (300줄)
- apps/seedtest_api/services/cat_engine.py (800줄)

목표: CAT 엔진과 어탬프트 라우터를 분리하여 의존성 감소
```

**결과**: 영향 범위 분석 + 단계별 마이그레이션 계획 + 롤백 포인트 🔧

---

### 예시 4: UI 컴포넌트 수정 (빠른 피드백)

**모델**: Gemini 2.0 Flash (기본)

```
다음 React 컴포넌트에 로딩 스피너를 추가해주세요:

[코드 붙여넣기]

Tailwind CSS를 사용하고, 데이터 로딩 중에만 표시되도록 해주세요.
```

**결과**: 즉시 수정된 컴포넌트 코드 + Tailwind 클래스 ⚡

---

### 예시 5: 테스트 작성 (코드 품질)

**모델 전환**: Claude Sonnet 4.5 (코드 품질 중시)

```
/tests

apps/seedtest_api/jobs/irt_drift_monitor.py의 detect_drift() 함수에 대한
pytest 테스트를 작성해주세요.

테스트 케이스:
- Δb threshold 위반
- Δa threshold 위반
- CI separation 감지
- 정상 케이스 (알림 없음)
```

**결과**: 완성도 높은 pytest 코드 + fixture + edge case 커버 ✅

---

## 🎓 모델별 특징 및 팁

### Gemini 2.0 Flash ⚡
- **장점**: 빠른 응답 속도, 1M 컨텍스트, 낮은 비용
- **용도**: 일상적인 코딩 작업의 80%
- **팁**: 코드 자동완성 느낌으로 빠르게 반복 실행

### Gemini 1.5 Pro 🧠
- **장점**: 2M 컨텍스트, 복잡한 추론, 높은 안정성
- **용도**: 설계/리팩터링/알고리즘 구현
- **팁**: 긴 대화나 여러 파일 동시 분석 시 사용

### GPT-o1 🔬
- **장점**: 추론 능력, 수학/알고리즘 특화, 긴 응답 (32K)
- **용도**: IRT 알고리즘, 복잡한 디버깅, 수학적 증명
- **팁**: 문제가 복잡할수록 강력 (단, 느림)
- **주의**: temperature 조정 불가 (자동 최적화)

### Claude Sonnet 4.5 🎨
- **장점**: 코드 품질, 가독성, 테스트 작성 능력
- **용도**: 프로덕션 코드 리뷰, 테스트 작성
- **팁**: 최종 PR 전 코드 검토에 활용

### GPT-4o 🌐
- **장점**: 범용성, 문서화 능력, 안정성
- **용도**: README 작성, 주석 개선, 일반 코딩
- **팁**: 비기술 문서 작성 시 유용

### Local Qwen2.5 💻
- **장점**: 오프라인 가능, 빠른 자동완성
- **용도**: 실시간 코드 제안
- **팁**: 인터넷 없이도 작업 가능

---

## 🔧 고급 설정

### 컨텍스트 길이 조정

```yaml
# .continue/config.yaml
models:
  - name: "Gemini 2.0 Flash (커스텀)"
    contextLength: 500000  # 500K로 축소 (더 빠른 응답)
```

### Temperature 조정

```yaml
completionOptions:
  temperature: 0.0  # 결정론적 출력 (테스트용)
  temperature: 0.2  # 균형 (기본 권장)
  temperature: 0.5  # 창의적 출력 (설계 문서)
```

### 자동완성 debounce 조정

```yaml
autocompleteOptions:
  debounceDelay: 100  # 더 빠른 제안 (공격적)
  debounceDelay: 300  # 타이핑 멈춘 후 제안 (보수적)
```

---

## 📊 성능 비교 (DreamSeed 프로젝트 기준)

| 작업 | Flash (초) | Pro (초) | Claude (초) |
|-----|-----------|---------|-----------|
| API 스켈레톤 (50줄) | 3-5 | 8-12 | 6-10 |
| 상세 설계 문서 (1000단어) | 15-20 | 25-35 | 20-30 |
| 리팩터링 계획 (5 파일) | 20-30 | 40-60 | 35-50 |
| 테스트 작성 (10 케이스) | 10-15 | 15-25 | 12-20 |

**권장**: 작업 시작은 Flash로, 복잡하면 Pro로 전환

---

## 🐛 문제 해결

### "API Key not found" 오류

```bash
# 환경 변수 확인
echo $GEMINI_API_KEY

# 없으면 추가
export GEMINI_API_KEY="your-key"

# VS Code 재시작 필수!
```

### "Context length exceeded" 오류

- Gemini 1.5 Pro로 전환 (2M 컨텍스트)
- 또는 대화 히스토리 초기화 (Continue 채팅창 휴지통 아이콘)

### 모델 응답이 느림

- Flash 모델 사용 확인
- 컨텍스트 길이 축소 (config.yaml)
- 인터넷 연결 확인

### 자동완성이 안 됨

- Local Qwen2.5 모델 확인: `ollama list`
- 없으면 설치: `ollama pull qwen2.5-coder:14b-q4_0`
- Continue 재시작

---

## 📈 프로젝트 적용 체크리스트

- [ ] GEMINI_API_KEY 환경 변수 설정
- [ ] Continue 확장 설치 (VS Code)
- [ ] Gemini 2.0 Flash 기본 모델 확인
- [ ] `/dreamseed-api` 명령어로 첫 API 생성 테스트
- [ ] Gemini 1.5 Pro로 복잡한 설계 문서 작성 테스트
- [ ] Local Qwen2.5 자동완성 테스트
- [ ] 팀원에게 가이드 공유

---

## 🎯 요약

1. **기본은 Gemini 2.0 Flash** - 빠른 작업의 80%
2. **복잡하면 Gemini 1.5 Pro** - 설계/리팩터링/긴 컨텍스트
3. **슬래시 명령어 활용** - `/dreamseed-api`, `/dreamseed-irt` 등
4. **모델 전환 유연하게** - 작업 특성에 맞게

**문의**: DreamSeedAI 개발팀 Slack #dev-tools 채널

---

*Last updated: November 6, 2025*
