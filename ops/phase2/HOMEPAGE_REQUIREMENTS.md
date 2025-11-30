# Phase 2 완료 후 홈페이지 구성 가이드

**작성일**: 2025-11-29  
**전제 조건**: Phase 2 (IRT/CAT) ✅ 완료됨

---

## 🎯 홈페이지 핵심 가치 제안

### 두 가지 핵심 축

#### 1. 적응형 평가 (Phase 2 완료 ✅)
- **IRT 3PL 모델**: 정교한 능력치(θ) 측정
- **CAT 엔진**: 학생 수준에 맞는 문항 자동 선택
- **실시간 진단**: 즉각적인 강점/약점 파악
- **과학적 근거**: 표준화된 심리측정학 방법론

#### 2. 학습 개선 (Phase 2 기반)
- **개인 맞춤 학습**: θ 기반 추천 시스템
- **취약점 집중**: 약한 주제 자동 감지
- **진도 추적**: 실시간 능력치 변화 모니터링
- **AI 피드백**: 문제별 상세 해설 및 힌트

---

## 📊 Phase 2 완료 상태

### ✅ 구현 완료된 기능

| 컴포넌트 | 상태 | 테스트 | 비고 |
|---------|------|--------|------|
| IRT 3PL 모델 | ✅ | 27/27 | a, b, c 파라미터 |
| CAT 엔진 | ✅ | E2E | Maximum Information |
| Item Bank | ✅ | 17/17 | 4개 모델 |
| Adaptive Router | ✅ | E2E | 5개 API |
| Classes API | ✅ | 10/10 | 학급 관리 |

**총 테스트**: 54/54 ✅ (100% 통과)

### 🔗 API 엔드포인트 (준비 완료)

```
POST   /api/adaptive/start      # 적성검사 시작
GET    /api/adaptive/next       # 다음 문항 (CAT 알고리즘)
POST   /api/adaptive/answer     # 답안 제출 & θ 업데이트
GET    /api/adaptive/status     # 현재 능력치 조회
POST   /api/adaptive/end        # 검사 완료
```

---

## 🏠 홈페이지 구성 요구사항

### 1. 랜딩 페이지

#### Hero Section
```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  🎯 AI 기반 적응형 학습 플랫폼                          │
│                                                        │
│  당신의 실력을 정확하게 측정하고                          │
│  맞춤형 학습 경로를 제시합니다                            │
│                                                        │
│  [무료로 시작하기]  [적성검사 체험하기]                  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**필요한 콘텐츠**:
- 짧은 소개 비디오 (30초)
- 적응형 평가 시연 애니메이션
- 주요 통계 (예: "평균 20% 성적 향상")

---

#### 핵심 기능 소개 (3-Column Layout)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 📊 정밀 진단  │  │ 🎓 맞춤 학습  │  │ 📈 실시간 추적│
│              │  │              │  │              │
│ IRT 기반     │  │ AI 추천      │  │ 능력치 그래프│
│ 과학적 측정  │  │ 개인 맞춤    │  │ 진도 모니터링│
└──────────────┘  └──────────────┘  └──────────────┘
```

**1. 정밀 진단 섹션**
- IRT 3PL 모델 설명 (쉽게)
- CAT 알고리즘 시각화
- "일반 시험과 다른 점" 비교표

**2. 맞춤 학습 섹션**
- θ 기반 문제 추천 원리
- 취약점 자동 감지
- 학습 경로 예시

**3. 실시간 추적 섹션**
- 대시보드 스크린샷
- 능력치 변화 그래프 예시
- 학부모/교사 모니터링 기능

---

### 2. 적성검사 체험 페이지

#### 무료 체험 플로우

```
Step 1: 회원가입 (간편)
  ↓
Step 2: 짧은 튜토리얼
  ↓
Step 3: 15문항 적성검사 (CAT)
  ↓
Step 4: 즉시 결과 확인
  ↓
Step 5: 맞춤 학습 추천
```

**구현 요구사항**:
- **프론트엔드**: React/Next.js 컴포넌트
  - `<AdaptiveTestPlayer />`: 문항 표시
  - `<ThetaVisualization />`: 실시간 능력치 그래프
  - `<ResultDashboard />`: 검사 결과 요약
  
- **백엔드**: Phase 2 API 활용
  ```typescript
  // 이미 구현됨 ✅
  POST /api/adaptive/start
  GET  /api/adaptive/next
  POST /api/adaptive/answer
  GET  /api/adaptive/status
  ```

---

### 3. 가격 페이지

#### 요금제 (적응형 평가 기반)

```
┌─────────────────────────────────────────────────────┐
│  무료          │  베이직         │  프로              │
├─────────────────────────────────────────────────────┤
│  월 5회        │  월 20회        │  무제한             │
│  적성검사      │  적성검사       │  적성검사           │
│                │                │                   │
│  ₩0           │  ₩29,000/월    │  ₩99,000/월       │
│                │                │                   │
│  - 기본 리포트 │  - 상세 분석    │  - 전문 리포트     │
│  - 5문항 추천  │  - 50문항 추천  │  - 무제한 추천     │
│                │  - 진도 추적    │  - 1:1 튜터링      │
│                │                │  - API 접근        │
└─────────────────────────────────────────────────────┘
```

---

### 4. 교사/학부모 페이지

#### 교육자 대시보드 (이미 구현됨)

**위치**: `/portal_front/dashboard/`

**기능**:
- ✅ 학생별 θ 추적
- ✅ 학급 평균 분석
- ✅ 취약점 히트맵
- ✅ IRT 기반 리포트

**홈페이지 연동**:
```
/teachers → portal_front 대시보드 링크
/parents  → 학부모용 간소화 뷰
```

---

## 🎨 디자인 요구사항

### 핵심 시각 요소

#### 1. θ (Theta) 능력치 시각화
```typescript
// 원형 게이지 (예시)
<ThetaGauge 
  value={0.5}        // θ = 0.5
  min={-3}
  max={3}
  label="수학 능력"
/>
```

#### 2. IRT 곡선 애니메이션
```
P(θ) 그래프 (3PL)
┌─────────────────────┐
│   1.0 ──────────╭──  │  높은 능력자는
│                ╱    │  정답률 높음
│   0.5 ────╭───      │
│          ╱          │  낮은 능력자는
│   0.0 ──            │  추측 확률(c)
└─────────────────────┘
  -3    0    +3  (θ)
```

#### 3. 적응형 경로 시각화
```
문항 선택 과정
┌──────────────────────────────┐
│  문항 1 (b=0) → 정답 → θ↑    │
│  문항 2 (b=1) → 오답 → θ↓    │
│  문항 3 (b=0.5) → 정답 → θ↑  │
│  ...                         │
│  최종 θ = 0.65 ± 0.15       │
└──────────────────────────────┘
```

---

## 💻 기술 스택 (홈페이지)

### 프론트엔드

**권장**: Next.js 14 (App Router)

**이유**:
- SEO 필수 (랜딩 페이지)
- SSR로 빠른 초기 로딩
- 기존 `portal_front` 구조 활용 가능

**구조**:
```
portal_front/
├── app/
│   ├── page.tsx                  # 랜딩 페이지
│   ├── trial/
│   │   └── page.tsx              # 적성검사 체험
│   ├── pricing/
│   │   └── page.tsx              # 가격
│   ├── teachers/
│   │   └── page.tsx              # 교사용
│   └── parents/
│       └── page.tsx              # 학부모용
├── components/
│   ├── adaptive/
│   │   ├── ThetaGauge.tsx       # θ 게이지
│   │   ├── TestPlayer.tsx       # 검사 플레이어
│   │   └── ResultDashboard.tsx  # 결과 대시보드
│   └── marketing/
│       ├── Hero.tsx             # Hero 섹션
│       ├── Features.tsx         # 기능 소개
│       └── Testimonials.tsx     # 후기
└── lib/
    └── adaptive-api.ts          # Phase 2 API 클라이언트
```

---

### API 클라이언트 (예시)

```typescript
// lib/adaptive-api.ts
export class AdaptiveTestAPI {
  async startTest(userId: string): Promise<SessionId> {
    const res = await fetch('/api/adaptive/start', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId })
    });
    return res.json();
  }

  async getNextItem(sessionId: string): Promise<Item> {
    const res = await fetch(
      `/api/adaptive/next?exam_session_id=${sessionId}`
    );
    return res.json();
  }

  async submitAnswer(
    sessionId: string, 
    itemId: number, 
    isCorrect: boolean
  ): Promise<ThetaUpdate> {
    const res = await fetch('/api/adaptive/answer', {
      method: 'POST',
      body: JSON.stringify({
        exam_session_id: sessionId,
        item_id: itemId,
        is_correct: isCorrect
      })
    });
    return res.json();
  }

  async getStatus(sessionId: string): Promise<TestStatus> {
    const res = await fetch(
      `/api/adaptive/status?exam_session_id=${sessionId}`
    );
    return res.json();
  }
}
```

---

## 📝 콘텐츠 작성 가이드

### 일반 사용자용 설명

**❌ 나쁜 예**:
> "저희는 IRT 3PL 모델을 사용하여 최대 정보량 기준으로 문항을 선택합니다."

**✅ 좋은 예**:
> "당신의 실력에 딱 맞는 문제만 출제됩니다. 
> 너무 쉽거나 어려운 문제는 건너뛰고, 
> 정확한 실력 측정에 필요한 문제만 풀게 됩니다."

---

### 교육자용 설명

**전문 용어 사용 가능**:
> "IRT 기반 능력치 추정으로 표준 오차(SE) < 0.3 수준의 
> 정밀한 진단이 가능합니다. 3PL 모델의 변별도(a), 
> 난이도(b), 추측도(c) 파라미터를 활용하여..."

---

## 🚀 구현 우선순위

### Phase 1: MVP (2주)
- [ ] 랜딩 페이지 기본 구조
- [ ] 적성검사 체험 페이지 (Phase 2 API 연동)
- [ ] 회원가입/로그인
- [ ] θ 시각화 컴포넌트

### Phase 2: 콘텐츠 (2주)
- [ ] 기능 소개 섹션 (3-column)
- [ ] 가격 페이지
- [ ] 교사/학부모 페이지
- [ ] SEO 최적화

### Phase 3: 고급 기능 (2주)
- [ ] 실시간 θ 그래프 애니메이션
- [ ] IRT 곡선 인터랙티브 시각화
- [ ] 후기/사례 연구
- [ ] 블로그 (적응형 평가 설명)

---

## 🎯 성공 지표

### 전환율 목표
- 랜딩 페이지 → 체험: **30%**
- 체험 → 가입: **50%**
- 가입 → 유료: **10%**

### 기술 지표
- Lighthouse 점수: **90+**
- First Contentful Paint: **< 1.5s**
- Time to Interactive: **< 3s**

---

## 📚 참고 자료

### Phase 2 문서
- [IRT/CAT 구현 상세](./README.md)
- [Item Models](../../backend/ITEM_MODELS_IMPLEMENTATION.md)
- [Adaptive Router](../../backend/ADAPTIVE_EXAM_ROUTER_IMPLEMENTATION.md)

### 디자인 참고
- Khan Academy (적응형 학습)
- Duolingo (게이미피케이션)
- Brilliant.org (시각화)

### IRT 이론 (일반인용 설명)
- "왜 모든 학생이 같은 시험을 봐야 할까요?"
- "컴퓨터는 어떻게 당신의 실력을 알까요?"
- "20문제로 100문제만큼 정확하게"

---

## ✅ 체크리스트

### Phase 2 완료 확인
- [x] IRT 3PL 모델 구현
- [x] CAT 엔진 동작
- [x] Item Bank 준비
- [x] API 엔드포인트 5개
- [x] 54개 테스트 통과

### 홈페이지 준비
- [ ] Next.js 프로젝트 설정
- [ ] Phase 2 API 클라이언트
- [ ] θ 시각화 컴포넌트
- [ ] 적성검사 플레이어
- [ ] 랜딩 페이지 콘텐츠
- [ ] SEO 메타데이터
- [ ] 모바일 반응형

---

**다음 단계**: 
1. 홈페이지 디자인 시안 작성
2. Next.js 프로젝트 구조 생성
3. Phase 2 API 통합 테스트

**담당**: Frontend Team  
**협업**: Backend Team (Phase 2 완료)  
**예상 기간**: 6주
