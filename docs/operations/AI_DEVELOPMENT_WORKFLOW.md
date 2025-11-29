# 🚀 DreamSeedAI AI-Enhanced Development Workflow

> **Continue + GPT + Windsurf + Copilot 협업 패턴 (표준 운영 문서)**  
> **작성일**: 2025-11-19  
> **목적**: DreamSeedAI AI-First 개발체계 정의

---

## 개요

DreamSeedAI는 개발 전 과정에 AI를 도입한 **AI-First 개발체계**를 채택한다.  
본 문서는 DreamSeedAI에서 사용하는 AI 개발 스택 4종의 역할과 협업 패턴을 정의한다.

---

## 1. 전체 개요 (AI 4-Layer Architecture)

DreamSeedAI 개발 구조는 다음 4개의 인공지능 계층으로 구성된다:

```
Continue  →  GPT  →  Windsurf  →  Copilot
(맥락/레포)   (두뇌)   (대규모 실행)   (정밀 작업)
```

### 역할 요약

| 도구 | 역할 | 비고 |
|------|------|------|
| **Continue** | 레포 전체를 읽고 "지속되는 컨텍스트" 제공 | GPT의 가장 큰 약점 보완 |
| **GPT** | 설계·분석·문서화·아키텍처 의사결정 | 최상위 두뇌 |
| **Windsurf** | 다중 파일, 대규모 리팩터링, 구조 변경 | 안전한 자동 코드 수정 |
| **Copilot** | 단일 파일/함수 단위 정밀 패치 | 가장 빠른 코드 생산 |

---

## 2. Continue – Persistent Context Layer

### "GPT의 눈" 역할

**GPT는 레포를 직접 읽을 수 없다.**  
Continue는 로컬 파일 시스템과 프로젝트 구조를 읽어 GPT에게 제공한다.

### Continue가 하는 일

- ✅ 레포 전체 스캔 (코드, 라우터, 컴포넌트, 문서)
- ✅ 변경 감지 및 GPT에게 자동 컨텍스트 제공
- ✅ 파일 검색 + 내용 요약
- ✅ "연속된 개발 흐름(Continuity)" 유지

### DreamSeedAI에서 Continue 사용 예

```bash
# 1. 관련 코드 전체 검색
"teacher/parent 관련 코드 전부 찾아줘"

# 2. 파일 구조 분석
"문항 에디터 관련 파일 목록 + 흐름 설명"

# 3. 문제 관련 파일 추적
"이 문제와 관련된 모든 파일/함수 트리 보여줘"

# 4. MVP 설계 제안
"레포 구조 기반으로 MVP 설계 제안해줘"
```

> **핵심**: Continue는 GPT에게 레포 전체를 보여 주는 **눈**이다.

---

## 3. GPT – Architectural Brain

### "설계자, 분석가, 아키텍트"

Continue가 프로젝트 맥락을 공급하면 GPT는 그 위에서 설계를 수행한다.

### GPT의 역할

- 🎨 기능 설계 (API/DB/UI/흐름)
- 🔍 문제 원인 분석 (race condition, hydration issues 등)
- 📝 문서화 및 리팩터링 전략 생성
- 🏗️ 기획·아키텍처·데이터 모델 설계
- 🚀 배포/운영 전략 제안

### DreamSeedAI에서 GPT 활용 예

```bash
# 1. 전체 구조 분석
"문제 에디터 파이프라인 전체 구조 설명해줘"

# 2. MVP 설계
"teacher/parent/tutor MVP 설계안 작성해줘"

# 3. 레포 기반 종합 분석
"Continue가 제공한 레포 맥락 기반으로 종합 분석해줘"

# 4. 인프라 최적화
"Nginx/HTTPS 배포 구조 최적화 설계해줘"

# 5. 버그 원인 도출
"Next.js sorting race condition 원인 도출 + 해결 설계"
```

> **핵심**: GPT는 DreamSeedAI의 **두뇌**다.

---

## 4. Windsurf – Large-Scale Executor

### "대규모 자동 리팩터링 전문가"

Windsurf는 여러 파일을 동시에 수정해야 하는 작업에 적합하다.

### Windsurf의 강점

- ⚡ 안전한 멀티파일 리팩터링 (apply plan → patch)
- 📁 폴더 구조 변경, 기능 분리, 컴포넌트 추출
- 🔧 코드 베이스 전체를 아우르는 작업
- 🛡️ 정리/정돈/리팩터 안정성이 높음

### DreamSeedAI에서 Windsurf 사용 예

```bash
# 1. 폴더 구조 정리
"admin_front 전체 폴더 구조 정리"

# 2. 모듈 분리
"monorepo 모듈 분리(teacher/parent/tutor)"

# 3. 프레임워크 마이그레이션
"오래된 리액트 페이지 → Next.js App Router 마이그레이션"

# 4. 공통 컴포넌트 추출
"공통 컴포넌트 폴더 생성, 반복 코드 제거"
```

> **핵심**: Windsurf는 대규모 자동화 스크립트 같은 **엔진**이다.

---

## 5. Copilot – Precision Editor

### "빠르고 정확한 한 파일/한 함수 작업"

Copilot은 **"수정 범위가 명확할 때"** 가장 잘 작동한다.

### Copilot이 잘하는 영역

- 📄 단일 파일 수정
- 🔧 함수 리팩터링
- 🐛 버그 패치
- ⚡ 빠른 새 컴포넌트 생성
- 🔌 API 연결 코드 작성
- 📝 단순 CRUD/폼 로직

### DreamSeedAI에서 Copilot 사용 예

```bash
# 1. CSS 수정
"TinyMCE 필터 CSS 수정"

# 2. 핸들러 개선
"정렬 onClick 핸들러 개선"

# 3. 단일 파일 패치
"admin_front에서 단일 파일 오류 패치"

# 4. UI 컴포넌트 구현
"Next.js UI 컴포넌트 빠른 구현"
```

> **핵심**: Copilot은 정밀 **외과 의사**다.

---

## 6. 네 도구의 협업 흐름 (DreamSeedAI 표준 패턴)

아래는 DreamSeedAI에서 확립된 가장 강력한 **6-단계 워크플로우**다.

### 🔵 1단계 — Continue: 레포 스캔 & 문맥 전달

**"문제 전체 그림을 먼저 파악"**

```bash
# 예시
/teacher 관련 코드 전부 찾아줘.
문항 에디터 파일 전체 구조 보여줘.
Next.js sorting 문제와 관련된 모든 파일 검색.
```

→ Continue가 레포 데이터를 GPT에게 공급.

---

### 🟡 2단계 — GPT: 설계/분석 수행

**"어떻게 고칠지, 어떻게 만들지 설계함"**

```bash
# 예시
Continue가 찾은 파일을 기반으로 전체 로직 재구성해줘.
sorting race condition 원인 분석 + 수정 설계 제안.
teacher/parent/tutor 대시보드 설계안 작성.
```

→ GPT가 해결책 또는 설계를 책임짐.

---

### 🟢 3단계 — Windsurf: 대규모 리팩터링

**"설계를 실제 코드 수준으로 대규모 적용"**

```bash
# 예시
GPT 설계안에 따라 admin_front 3개 파일 정리 + 컴포넌트 추출.
portal_front → Next.js App Router 구조로 전체 마이그레이션.
5개 파일에 걸친 수정 적용.
```

→ Windsurf는 대규모 작업을 안정적으로 자동 반영.

---

### 🔴 4단계 — Copilot: 정밀 패치 및 디테일 구현

**"마지막 10% 섬세한 부분 고치기"**

```bash
# 예시
onClick에서 filter 값 덮어쓰는 버그 패치.
img.Wirisformula filter CSS 고정.
questions.ts API 훅 최적화.
```

→ 작은 범위라면 Copilot이 가장 효율적.

---

### 🔵 5단계 — Deploy.sh + Nginx: 프로덕션 반영

**"DreamSeedAI 운영 반영 루틴"**

```bash
# 예시
./deploy_admin_front.sh
sudo systemctl restart admin-front
```

→ 모든 AI 작업이 끝난 후 즉시 운영 반영 가능.

---

### 🟢 6단계 — Continue: 검증 및 후속 분석

**"새롭게 적용된 구조가 맞는지 다시 확인"**

```bash
# 예시
방금 패치된 부분 다시 스캔해줘.
서브도메인 teacher/parent/tutor 연결 흐름 검토해줘.
```

→ Continue가 새로운 레포 상태를 다시 집계 → GPT가 재분석.

---

## 7. 실제 DreamSeedAI 개발 예시 (요약 사례)

### ✅ 문항 에디터 경로 분석

**워크플로우**: `Continue → GPT → Copilot`

**결과**: TinyMCE iframe CSS 문제 해결 (Dark/Light 모드)

```mermaid
graph LR
    A[Continue: 에디터 파일 스캔] --> B[GPT: CSS filter 설계]
    B --> C[Copilot: filter CSS 적용]
    C --> D[Deploy: 프로덕션 반영]
```

---

### ✅ admin_front 프로덕션 배포

**워크플로우**: `GPT → Nginx config → Deploy.sh → HTTPS`

**결과**: Nginx proxy + 서브도메인 구조 완성

```bash
admin.dreamseedai.com  # Nginx reverse proxy
├── /questions         # 문항 관리
├── /users             # 사용자 관리
└── /analytics         # 분석 대시보드
```

---

### ✅ teacher/parent/tutor MVP 설계

**워크플로우**: `Continue 레포 스캔 → GPT 설계 → Next.js App Router로 3개 페이지 구현`

**결과**:
```
portal_front/
├── src/pages/
│   ├── TeacherDashboard.tsx
│   ├── ParentDashboard.tsx
│   └── TutorDashboard.tsx
└── App.tsx (라우팅 추가)
```

---

## 8. 워크플로우 다이어그램

### 전체 AI 개발 파이프라인

```
┌─────────────────────────────────────────────────────────────┐
│                    DreamSeedAI AI Pipeline                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   1. Continue   │
                    │   (레포 스캔)    │
                    └────────┬────────┘
                             │ 맥락 전달
                             ▼
                    ┌─────────────────┐
                    │    2. GPT       │
                    │  (설계/분석)     │
                    └────────┬────────┘
                             │ 설계안
                             ▼
                    ┌─────────────────┐
                    │  3. Windsurf    │
                    │ (대규모 리팩터링) │
                    └────────┬────────┘
                             │ 코드 변경
                             ▼
                    ┌─────────────────┐
                    │  4. Copilot     │
                    │  (정밀 패치)     │
                    └────────┬────────┘
                             │ 최종 코드
                             ▼
                    ┌─────────────────┐
                    │  5. Deploy.sh   │
                    │  (프로덕션)      │
                    └────────┬────────┘
                             │ 검증 요청
                             ▼
                    ┌─────────────────┐
                    │  6. Continue    │
                    │  (재검증)        │
                    └─────────────────┘
```

---

## 9. 각 도구의 장단점 비교

| 도구 | 장점 | 단점 | 최적 사용 시점 |
|------|------|------|----------------|
| **Continue** | • 레포 전체 컨텍스트 제공<br>• GPT와 완벽 연동 | • 직접 코드 수정 불가 | 프로젝트 전체 분석 필요 시 |
| **GPT** | • 최고 수준 설계 능력<br>• 문서화 탁월 | • 레포 직접 접근 불가<br>• 코드 실행 불가 | 아키텍처 의사결정 시 |
| **Windsurf** | • 멀티파일 안전 수정<br>• 대규모 리팩터링 | • 단일 파일은 과함 | 구조 변경, 마이그레이션 |
| **Copilot** | • 가장 빠른 코드 생성<br>• IDE 통합 완벽 | • 큰 구조 변경 약함 | 함수/컴포넌트 단위 작업 |

---

## 10. DreamSeedAI 표준 개발 원칙

### ✅ DO (권장)

1. **큰 작업은 Continue → GPT → Windsurf 순서로**
2. **작은 패치는 Copilot으로 빠르게**
3. **설계 없이 코드부터 짜지 말 것** (GPT 먼저)
4. **변경 후 항상 Continue로 재검증**
5. **배포 전 Deploy.sh로 자동화**

### ❌ DON'T (지양)

1. **GPT 없이 Windsurf 단독 사용** (설계 없이 대규모 수정 위험)
2. **Copilot으로 멀티파일 작업** (충돌 발생 가능)
3. **Continue 없이 GPT에게 복잡한 레포 질문** (맥락 부족)
4. **수동 배포** (Deploy.sh 사용)
5. **문서화 생략** (모든 작업은 md 문서 남길 것)

---

## 11. 실전 팁

### Continue 활용 팁

```bash
# 1. 특정 파일 패턴 검색
"*.tsx 파일 중에서 Dashboard 관련만 찾아줘"

# 2. 의존성 트리 분석
"QuestionForm.tsx가 의존하는 모든 파일 트리 보여줘"

# 3. 변경 영향 분석
"API_GUIDE.md 변경이 영향 주는 코드 찾아줘"
```

### GPT 활용 팁

```bash
# 1. 설계 요청 시 구체적으로
❌ "대시보드 만들어줘"
✅ "teacher/parent/tutor 대시보드 MVP 설계안 작성해줘. 
   각각 Summary/Actions/Links 섹션 필요"

# 2. 문제 분석 시 증상 상세히
❌ "버그 고쳐줘"
✅ "Next.js에서 정렬 클릭 시 필터가 초기화되는 race condition 
   원인 분석 + 해결책 제시"
```

### Windsurf 활용 팁

```bash
# 1. 변경 범위 명확히
"다음 3개 파일에서 SummaryCard 컴포넌트를 
 components/SummaryCard.tsx로 추출:
 - TeacherDashboard.tsx
 - ParentDashboard.tsx  
 - TutorDashboard.tsx"

# 2. Apply plan 먼저 확인
변경 계획 미리보기 → 승인 → 실행
```

### Copilot 활용 팁

```bash
# 1. 주석으로 의도 명확히
// TODO: Add dark mode support for WIRIS images
// Filter should be invert(1) in dark mode, none in light mode

# 2. 함수 시그니처 먼저 작성
function SummaryCard({ label, value }: { label: string; value: string }) {
  // Copilot이 자동 완성
}
```

---

## 12. 문제 해결 시 참고 흐름

### 예: "정렬이 작동하지 않음"

```
1. Continue: "정렬 관련 코드 전체 찾아줘"
   → questions.ts, QuestionList.tsx 파일 발견

2. GPT: "Continue가 찾은 파일 기반으로 정렬 로직 분석해줘"
   → onClick에서 setFilters가 이전 상태 덮어쓰는 race condition 발견

3. GPT: "해결책: useCallback + prev => ({ ...prev, sort }) 패턴 사용"

4. Copilot: QuestionList.tsx에서 해당 함수만 수정
   const handleSort = useCallback((field: string) => {
     setFilters(prev => ({ ...prev, sort: field }));
   }, []);

5. Deploy: npm run build && systemctl restart

6. Continue: "방금 수정한 정렬 로직 다시 검토해줘"
```

---

## 🔚 결론

이 문서는 DreamSeedAI의 **표준 AI-기반 개발 흐름**이다:

- **Continue** = 맥락 (레포 전체를 아는 눈)
- **GPT** = 설계·분석 (두뇌)
- **Windsurf** = 대규모 실행 엔진
- **Copilot** = 정밀 코드 생산자

이 4단계 워크플로우를 통해 DreamSeedAI는  
작은 수정부터 대규모 구조 개편까지 **끊김 없이(continue)** 발전할 수 있다.

---

## 13. Windsurf 제어 가이드 (중요!)

### 🌋 Windsurf는 "핵폭탄 공구"다

Windsurf는 강력하지만 위험한 도구입니다:
- ✅ **잘 쓰면**: 몇 시간 작업을 10분에 완료
- ⚠️ **잘못 쓰면**: 레포 전체를 흔들고 예상 못한 파급 효과

### 문제 상황: "꼬리에 꼬리를 물고 빨려들어간다"

```
Windsurf: "학생 리스트 만들었으니 이제 상세 페이지 하시죠?"
당신: "오케이" (빨려들어감)

Windsurf: "상세 페이지 만들었으니 차트 넣으시죠?"
당신: "좋네" (더 빨려들어감)

Windsurf: "차트 넣었으니 실시간 업데이트 하시죠?"
당신: "..." (어디까지 가는지 모르게 계속 감)

결과: 원래 계획보다 10배 큰 작업, 통제 불능
```

### ❌ Windsurf에게 절대 시키지 말아야 할 문장들

```bash
# 위험한 요청들
"이 레포 좀 정리해줘"
"전반적으로 개선해줘"
"이 디렉토리 구조 정리해줘"
"이 기능 좀 깔끔하게 다시 만들어줘"
"코드 리팩터링 해줘"

# 이건 거의 "레포 전체를 마음대로 손 봐도 된다"는 의미
→ DreamSeed처럼 큰 레포에서는 매우 위험!
```

### ✅ Windsurf는 이렇게만 쓰자

#### 1. 항상 파일/범위를 제한

```bash
# Good: 명확한 범위 지정
"이 한 파일만 수정해: portal_front/src/pages/teacher/StudentList.tsx"

"이 3개 파일까지만 건드려:
 - TeacherDashboard.tsx
 - ParentDashboard.tsx
 - TutorDashboard.tsx"

"TeacherDashboard 컴포넌트의 handleSort 함수만 리팩터링해"
```

#### 2. 항상 설계를 끝낸 뒤에만 실행

```
1. Continue: 레포 상태 파악
2. GPT: 설계 및 우선순위 결정  ← 여기서 멈춤
3. 나: 최종 결정
4. Windsurf: "집행자"로만 사용  ← 이때만 시작
```

### 🛡️ Windsurf 제어 템플릿

#### Template 1: 분석만 해, 수정 금지

```
Do not modify any files.

Only analyze the current code and summarize:
- which files are involved,
- what the current behavior is,
- and what you would change in a future step.

Analysis only, no edits.
```

#### Template 2: 이 파일 안에서만

```
You are allowed to edit ONLY this file:
- apps/portal_front/app/teacher/students/page.tsx

Do not touch any other file.

Goal:
- Add a simple detail panel when clicking on a student row.
- No API calls, use mock data only.
```

#### Template 3: 지금은 멈춰

```
Thanks, but I don't want to make any further changes right now.

Stop here with suggestions only.

I will decide the next step later.
```

#### Template 4: 제안만 해, 실행은 내가 결정

```
Good suggestions. I'll align the roadmap separately.

Right now I don't want any changes.
Stop here with analysis only.
```

---

## 14. AI 제안 3단계 필터

Windsurf나 GPT가 제안할 때 **항상 이 3가지를 체크**하세요:

### 🧱 필터 1: 이건 정말 지금 당장 필요한가?

```
질문:
- 지금 Phase/목표에 직접 관련 있는 변경인가?
- 아니면 "나중에 하면 좋은 리팩터링/개선"인가?

답변:
→ 지금 Phase 목표: Teacher 대시보드 MVP 완성
→ Teacher 학생 리스트: ✅ 필요
→ 실시간 업데이트: ❌ Phase 2에서
→ 고급 차트: ❌ Phase 3에서
```

### 🧱 필터 2: 변경 범위가 얼마나 넓은가?

```
한 파일/한 기능 안에서 끝나는가?
→ ✅ Copilot / 작은 수정으로 진행

여러 모듈/폴더를 건드리나?
→ ⚠️ 문서/티켓화 + 나중에
→ 또는 GPT와 상세 설계 후 Windsurf 사용
```

### 🧱 필터 3: 롤백 계획이 있나?

```
체크리스트:
- [ ] 브랜치 분리했나?
- [ ] 커밋 스냅샷 남겼나?
- [ ] "이전 상태로 되돌릴 수 있다"는 안전장치 있나?

하나라도 없으면:
→ "좋은 아이디어, 메모해두고 지금은 안 한다"
```

---

## 15. DreamSeed 레포 특성: "크고 얽힌 구조"

### 현재 DreamSeed 구조

```
dreamseed_monorepo/
├── admin_front/          # Next.js admin (포트 3100)
├── portal_front/         # Vite + React portal (포트 5172)
├── backend/              # FastAPI (포트 8002)
├── apps/
│   ├── analytics_api/
│   ├── portal_api/
│   └── seedtest_api/
├── scripts/              # 배포, ETL 스크립트
├── docs/                 # 문서 (architecture, operations, planning)
├── ops/                  # 운영 관련
└── Nginx, deploy.sh, 서브도메인들
```

**이 정도면 혼자서도 팀 레벨 시스템입니다.**

### Phase별 접근 방식

| Phase | 목표 | Windsurf 사용 범위 |
|-------|------|-------------------|
| **Phase 0** | 인프라/파이프라인 안정화 | ❌ 거의 사용 안 함 (구조 확정) |
| **Phase 1** | 핵심 기능만 추가 (MVP) | ⚠️ 제한적 사용 (파일 단위) |
| **Phase 2** | 리팩터링/구조 개선 | ✅ "큰 칼" 허용 (브랜치 분리) |
| **Phase 3** | 확장/최적화 | ✅ 대규모 작업 가능 |

**현재는 Phase 1**:
- "작동하는 것 + MVP + 확장 가능성만 확보"가 핵심
- 레포 전체를 다시 깨끗하게 하는 작업은 **Phase 2에서**

---

## 16. Windsurf 사용 케이스 가이드

### ✅ Windsurf를 써도 되는 경우

```bash
1. 명확한 범위의 멀티파일 작업
   예: "3개 대시보드 페이지에서 SummaryCard 컴포넌트 추출"

2. 설계가 완전히 끝난 후
   예: "GPT가 작성한 설계대로 5개 파일 수정"

3. 폴더 구조 변경 (브랜치 분리 후)
   예: "teacher/ 폴더를 pages/teacher/로 이동, import 경로 자동 수정"

4. 대규모 리팩터링 (Phase 2+)
   예: "React 클래스 컴포넌트 → 함수형 컴포넌트 변환"

5. 반복 작업 자동화
   예: "10개 페이지에 동일한 헤더 컴포넌트 추가"
```

### ❌ Windsurf를 쓰면 안 되는 경우

```bash
1. 범위가 불명확할 때
   예: "코드 좀 개선해줘"

2. 설계가 안 끝났을 때
   예: "이 기능 어떻게 만들면 좋을까?"

3. 한 파일만 수정하면 될 때
   예: "이 함수 버그 고쳐줘" → Copilot 사용

4. 실험적인 변경
   예: "이 방식이 더 나을까?" → GPT와 상의 먼저

5. Phase 1 MVP 중간에 구조 변경
   예: "전체 폴더 구조 재정비" → Phase 2로 미루기
```

---

## 17. "AI가 주도"에서 → "내가 AI를 지휘"로

### 이전 모드 (AI-Driven)

```
GPT 제안
    ↓
뭔가 좋아 보임
    ↓
그대로 진행
    ↓
또 제안
    ↓
또 진행
    ↓
(무한 루프, 통제 불능)
```

### 새로운 모드 (Human-Directed)

```
1. Continue: "전체 상황 요약해봐"
    ↓
2. GPT: "이 상황에서 제일 효율적인 한 걸음만 추천해줘"
    ↓
3. 나: "그중 오늘은 이거 하나만 한다" ← 결정권
    ↓
4. Windsurf/Copilot: "이 파일/이 범위 안에서만 실행해"
    ↓
5. 완료 후 검증, 다음 단계 결정
```

### 핵심 원칙

```
당신 = 감독/총괄 (Architect)
GPT = 설계·전략 (Strategy)
Continue = 레포 이해/정보 수집 (Context)
Windsurf = 대규모 작업자 (Executor) ← 시키는 것만!
Copilot = 정밀 작업자 (Precision)
```

---

## 18. 실전 체크리스트: AI 작업 시작 전 5가지 질문

### 🔍 질문 1: 이 작업은 어느 Phase인가?

```
- [ ] Phase 0 (인프라) → 이미 완료
- [ ] Phase 1 (MVP) → 지금 여기
- [ ] Phase 2 (리팩터링) → 아직 아님
- [ ] Phase 3 (확장) → 나중에
```

### 🔍 질문 2: 이 작업의 우선순위는?

```
P0 (지금 당장): Teacher 대시보드 MVP 완성
P1 (이번 주): Parent/Tutor 대시보드 연동
P2 (다음 주): API 연동
P3 (Phase 2): 코드 정리, 리팩터링
P4 (Phase 3): 고급 기능
```

### 🔍 질문 3: 어느 도구를 쓸 것인가?

```
- Continue: 관련 파일 찾기, 전체 상황 파악
- GPT: 설계, 분석, 문서화
- Windsurf: 3개 이상 파일 수정 (범위 명확할 때만)
- Copilot: 1~2개 파일 수정
- 수동: 설정 파일, 민감한 변경
```

### 🔍 질문 4: 롤백 계획은?

```
- [ ] 새 브랜치 생성했나?
- [ ] 현재 상태 커밋했나?
- [ ] 변경 전 스냅샷 있나?
- [ ] 테스트 환경에서 먼저 해볼 수 있나?
```

### 🔍 질문 5: 성공 기준은?

```
예:
✅ Teacher 학생 리스트 페이지가 렌더링된다
✅ 검색/필터가 작동한다
✅ 상세 페이지 링크가 있다
✅ Dark mode가 작동한다

애매한 기준 (피하기):
❌ "좀 더 깔끔하게"
❌ "나중에 확장하기 쉽게"
```

---

## 19. Windsurf 사고 방지 패턴

### Pattern 1: "스코프 고정"

```typescript
// Before (위험)
"Teacher 관련 전체 개선해줘"

// After (안전)
"portal_front/src/pages/teacher/StudentList.tsx 이 파일만 수정:
 - 검색 필터 추가
 - StatusBadge 컴포넌트 추출
 다른 파일은 건드리지 마"
```

### Pattern 2: "단계 나누기"

```typescript
// Before (한 번에 다)
"Teacher 페이지 전체 만들어줘"

// After (단계별)
"1단계: StudentList.tsx 기본 구조만 (Mock 데이터)
 2단계: 검색/필터 추가
 3단계: API 연동
 각 단계를 별도 커밋으로"
```

### Pattern 3: "제안 수집 → 나중에 결정"

```typescript
// Windsurf가 제안할 때
Windsurf: "다음은 이것도 하시죠?"

당신: "Good idea. Add it to backlog.
      I'll decide priority later.
      Do not implement now."
```

### Pattern 4: "Dry Run 먼저"

```typescript
// Before (바로 실행)
"이 구조로 리팩터링해줘"

// After (분석 먼저)
"먼저 분석만 해줘:
 - 어떤 파일들이 영향받나?
 - 예상 변경 사항은?
 - 위험 요소는?
 
 분석 결과 본 후 진행 여부 결정"
```

---

## 20. 긴급 상황 대응

### 🚨 Windsurf가 너무 많은 걸 바꿨을 때

```bash
# 1. 즉시 멈추기
git status  # 변경된 파일 확인

# 2. 변경사항 리뷰
git diff  # 변경 내용 확인

# 3. 필요한 것만 스테이징
git add -p  # 대화형으로 선택

# 4. 나머지는 되돌리기
git checkout .  # 모든 변경 취소
git checkout <file>  # 특정 파일만 취소

# 5. 다시 제한적으로 시작
"Only this file: <specific-file>"
```

### 🚨 변경 범위가 통제 불능일 때

```bash
# Option 1: 전체 롤백
git reset --hard HEAD

# Option 2: 새 브랜치로 대피
git checkout -b windsurf-experiment
git checkout main  # 원래 브랜치로 돌아감

# Option 3: 스태시에 저장
git stash save "windsurf-changes-review-later"
```

---

## 참고 문서

- `docs/architecture/ARCHITECTURE_MASTERPLAN.md` - 전체 아키텍처
- `docs/operations/AUTO_CLEANUP_STRATEGY.md` - 운영 자동화
- `docs/DASHBOARD_IMPLEMENTATION.md` - 대시보드 구현 가이드
- `DEPLOYMENT_GUIDE_attempt_view_lock.md` - 배포 절차

---

## 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|------|-----------|--------|
| 2025-11-19 | 초안 작성, 4-Layer AI 워크플로우 정의 | GitHub Copilot |
| 2025-11-19 | Windsurf 제어 가이드 추가 (섹션 13~20) | GitHub Copilot + GPT |

---

## 핵심 요약

### 🎯 가장 중요한 3가지 규칙

1. **Windsurf는 "집행자"일 뿐, "결정권자"가 아니다**
   - 설계/우선순위 = GPT + 당신
   - 실행 = Windsurf (명확한 범위 안에서만)

2. **AI 제안 = 참고용, 최종 결정 = 당신**
   - 3단계 필터 적용: 필요성/범위/롤백
   - "좋은 아이디어, 나중에" 도 훌륭한 선택

3. **Phase별로 Windsurf 사용 범위 다르게**
   - Phase 1 (MVP): 파일 단위, 제한적
   - Phase 2 (리팩터링): 대규모 허용
   - 지금은 Phase 1 → 조심스럽게

### 🛡️ 긴급 템플릿 (복사해서 사용)

```bash
# 분석만
"Do not modify any files. Analysis only."

# 한 파일만
"Only edit this file: <path>. Do not touch others."

# 멈춰
"Stop here. I will decide next step later."
```

---

**문서 작성**: GitHub Copilot + GPT  
**최종 업데이트**: 2025-11-19  
**버전**: 2.0 (Windsurf 제어 가이드 추가)
