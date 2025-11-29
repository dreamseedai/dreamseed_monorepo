# Week 4 Alpha Test - Portal Integration Guide

**작성일:** 2025-11-25  
**목표:** portal_front에 student/tutor/parent 앱을 iframe + postMessage SSO로 통합

---

## 🎯 완성된 구조

### 통합 아키텍처
```
portal_front (http://localhost:5172)
├── / (홈) → Week 4 Alpha 섹션 카드
├── /portal → 역할별 자동 라우팅
│   ├── /portal/student → iframe(localhost:3001)
│   ├── /portal/tutor   → iframe(localhost:3002)
│   └── /portal/parent  → iframe(localhost:3003)
```

### SSO 토큰 흐름
1. **포털 로그인** → `localStorage.access_token` 저장
2. **iframe 로드** → `AppFrame` 컴포넌트가 `postMessage({type: "SET_TOKEN", token})` 전송
3. **앱 수신** → `TokenSyncProvider`가 토큰을 `localStorage`에 저장
4. **API 호출** → 각 앱의 `apiClient.ts`가 동일 토큰으로 backend 호출

---

## 📁 생성된 파일

### Portal Front (portal_front)
```
portal_front/
├── .env.local                              # ✅ 환경 변수
├── src/
│   ├── config/
│   │   └── portalApps.ts                   # ✅ 앱 설정 (역할, URL, 경로)
│   ├── components/
│   │   └── AppFrame.tsx                    # ✅ iframe + postMessage SSO
│   ├── app/
│   │   └── portal/
│   │       ├── page.tsx                    # ✅ 자동 라우팅 (/auth/me → role 확인)
│   │       ├── student/
│   │       │   └── page.tsx                # ✅ Student iframe
│   │       ├── tutor/
│   │       │   └── page.tsx                # ✅ Tutor iframe
│   │       └── parent/
│   │           └── page.tsx                # ✅ Parent iframe
│   └── pages/
│       └── Home.tsx                        # ✅ Week 4 Alpha 카드 (업데이트됨)
```

### Student Front (apps/student_front)
- **이미 완료**: `TokenSyncProvider` 존재 (기존 구현)

### Tutor Front (apps/tutor_front)
```
apps/tutor_front/
└── src/
    └── app/
        ├── TokenSyncProvider.tsx           # ✅ postMessage 수신
        └── layout.tsx                      # ✅ Provider로 감싸기
```

### Parent Front (apps/parent_front)
```
apps/parent_front/
└── src/
    └── app/
        ├── TokenSyncProvider.tsx           # ✅ postMessage 수신
        └── layout.tsx                      # ✅ Provider로 감싸기
```

---

## 🚀 실행 방법

### 1. 환경 변수 확인
각 앱의 `.env.local` 파일이 올바른지 확인:

**portal_front/.env.local**
```bash
NEXT_PUBLIC_STUDENT_APP_URL=http://localhost:3001
NEXT_PUBLIC_TUTOR_APP_URL=http://localhost:3002
NEXT_PUBLIC_PARENT_APP_URL=http://localhost:3003
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api
```

**apps/student_front/.env.local**
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api
```

**apps/tutor_front/.env.local**
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api
```

**apps/parent_front/.env.local**
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api
```

### 2. 포트 설정 (package.json)

각 앱의 `package.json`에서 `dev` 스크립트 포트 확인:

**apps/student_front/package.json**
```json
{
  "scripts": {
    "dev": "next dev -p 3001"
  }
}
```

**apps/tutor_front/package.json**
```json
{
  "scripts": {
    "dev": "next dev -p 3002"
  }
}
```

**apps/parent_front/package.json**
```json
{
  "scripts": {
    "dev": "next dev -p 3003"
  }
}
```

**portal_front/package.json** (이미 5172 포트 사용 중)

### 3. 모든 앱 실행

**Terminal 1 - Backend**
```bash
cd /home/won/projects/dreamseed_monorepo/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

**Terminal 2 - Portal**
```bash
cd /home/won/projects/dreamseed_monorepo/portal_front
npm run dev
# http://localhost:5172
```

**Terminal 3 - Student**
```bash
cd /home/won/projects/dreamseed_monorepo/apps/student_front
npm run dev
# http://localhost:3001
```

**Terminal 4 - Tutor**
```bash
cd /home/won/projects/dreamseed_monorepo/apps/tutor_front
npm run dev
# http://localhost:3002
```

**Terminal 5 - Parent**
```bash
cd /home/won/projects/dreamseed_monorepo/apps/parent_front
npm run dev
# http://localhost:3003
```

---

## 🧪 Week 4 Alpha 테스트 시나리오

### 시나리오 1: 학생 (Student)
1. 포털 로그인 (student 계정)
2. 홈 화면 → "Student Portal" 카드 클릭
3. `/portal/student`로 이동 → student_front iframe 로드
4. 대시보드에서 능력치 확인:
   - θ (theta), band, percentile
   - Δθ 7일/14일 추세
   - 과목별 위험도 (risk level)

### 시나리오 2: 튜터 (Tutor)
1. 포털 로그인 (teacher/tutor 계정)
2. 홈 화면 → "Tutor Portal" 카드 클릭
3. `/portal/tutor`로 이동 → tutor_front iframe 로드
4. 우선순위 리스트 확인:
   - 학생별 θ, Δθ14d, 위험도, 플래그
   - "코멘트 작성" 버튼 클릭
5. 코멘트 입력 (summary/next_4w_plan/parent_guidance)
6. "저장 후 발행" → backend `/teacher/reports/{student_id}/comments`

### 시나리오 3: 학부모 (Parent)
1. 포털 로그인 (parent 계정)
2. 홈 화면 → "Parent Portal" 카드 클릭
3. `/portal/parent`로 이동 → parent_front iframe 로드
4. 자녀 선택 + 기간 선택 (최근 4주/8주)
5. "PDF 리포트 다운로드" 버튼 클릭
6. 리포트 확인:
   - 학교 선생님 코멘트
   - 학원 선생님 코멘트
   - 개인 튜터 코멘트
   - IRT/CAT 능력 분석

---

## 🔐 SSO 동작 확인

### 개발자 도구로 확인하기

1. **포털 로그인 후 토큰 확인**
   ```javascript
   // 개발자 도구 Console
   localStorage.getItem("access_token")
   ```

2. **iframe 내부 토큰 확인**
   - `/portal/student` 접속
   - iframe 내부로 이동 (개발자 도구에서 iframe 선택)
   - Console에서 `localStorage.getItem("access_token")` 실행
   - 포털과 동일한 토큰이 있어야 함

3. **postMessage 로그 확인**
   ```javascript
   // AppFrame.tsx에 임시로 추가
   console.log("Sending token to iframe:", token);
   
   // TokenSyncProvider.tsx에 임시로 추가
   console.log("Received SET_TOKEN message:", e.data);
   ```

---

## 🐛 트러블슈팅

### 문제 1: iframe이 빈 화면
- **원인**: 앱이 실행되지 않음
- **해결**: `npm run dev`로 3001/3002/3003 포트 확인

### 문제 2: 토큰이 전달되지 않음
- **원인**: postMessage 타이밍 이슈
- **해결**: `AppFrame.tsx`에서 `iframe.onload` 확인

### 문제 3: API 호출 401 에러
- **원인**: 토큰이 localStorage에 없거나 만료됨
- **해결**: 
  1. 포털에서 재로그인
  2. iframe 새로고침
  3. 개발자 도구에서 토큰 확인

### 문제 4: CORS 에러
- **원인**: Backend CORS 설정 누락
- **해결**: backend `main.py`에 origin 추가:
  ```python
  origins = [
      "http://localhost:5172",  # portal
      "http://localhost:3001",  # student
      "http://localhost:3002",  # tutor
      "http://localhost:3003",  # parent
  ]
  ```

---

## 📊 Week 4 알파 완료 기준

### Backend
- [ ] Alembic migration 실행 (`alembic upgrade head`)
- [ ] Seed 데이터 생성 (`python scripts/seed_week4_alpha.py`)
- [ ] 15개 API 엔드포인트 테스트 완료
- [ ] CORS 설정 (4개 origin)

### Frontend
- [x] portal_front: /portal 라우팅 구현
- [x] student_front: 대시보드 완료
- [x] tutor_front: 우선순위 리스트 + 코멘트 완료
- [x] parent_front: 자녀 선택 + PDF 다운로드 완료
- [x] SSO 통합 (iframe + postMessage)

### 테스트
- [ ] 학생 시나리오 (5명)
- [ ] 튜터 시나리오 (2명)
- [ ] 학부모 시나리오 (2명)
- [ ] PDF 리포트 생성 (10건 이상)
- [ ] 버그 리포트 수집

---

## 🎉 다음 단계 (Week 4 Day 3-7)

### Day 3: Backend 검증
- Migration 실행
- Seed 데이터 생성
- API 테스트 (curl/Postman)

### Day 4: Frontend 통합 테스트
- 3개 앱 동시 실행
- SSO 토큰 흐름 검증
- 크로스 브라우저 테스트

### Day 5: 알파 사용자 초대
- 5-10명 테스터 모집
- 테스트 가이드 배포
- 피드백 수집 폼 준비

### Day 6-7: 버그 픽스 & 개선
- Critical 버그 수정
- UI/UX 개선
- 성능 최적화 (< 500ms JSON, < 2s PDF)

---

## 📝 프로덕션 배포 준비

### 도메인 구성
```
https://portal.dreamseedai.com   → portal_front
https://student.dreamseedai.com  → student_front
https://tutor.dreamseedai.com    → tutor_front
https://parent.dreamseedai.com   → parent_front
https://api.dreamseedai.com      → backend
```

### 환경 변수 업데이트
**portal_front/.env.production**
```bash
NEXT_PUBLIC_STUDENT_APP_URL=https://student.dreamseedai.com
NEXT_PUBLIC_TUTOR_APP_URL=https://tutor.dreamseedai.com
NEXT_PUBLIC_PARENT_APP_URL=https://parent.dreamseedai.com
NEXT_PUBLIC_API_BASE_URL=https://api.dreamseedai.com/api
```

### postMessage origin 제한
**AppFrame.tsx 프로덕션 설정**
```typescript
// 개발: "*"
// 프로덕션: 정확한 origin
iframeRef.current.contentWindow.postMessage(
  { type: "SET_TOKEN", token },
  "https://student.dreamseedai.com"  // 각 앱별로 설정
);
```

---

## ✅ 체크리스트

### 파일 생성 확인
- [x] portal_front/.env.local
- [x] portal_front/src/config/portalApps.ts
- [x] portal_front/src/components/AppFrame.tsx
- [x] portal_front/src/app/portal/page.tsx
- [x] portal_front/src/app/portal/student/page.tsx
- [x] portal_front/src/app/portal/tutor/page.tsx
- [x] portal_front/src/app/portal/parent/page.tsx
- [x] portal_front/src/pages/Home.tsx (업데이트)
- [x] apps/tutor_front/src/app/TokenSyncProvider.tsx
- [x] apps/tutor_front/src/app/layout.tsx (업데이트)
- [x] apps/parent_front/src/app/TokenSyncProvider.tsx
- [x] apps/parent_front/src/app/layout.tsx (업데이트)

### 기능 구현 확인
- [x] 포털 자동 라우팅 (role 기반)
- [x] iframe 통합 (3개 앱)
- [x] postMessage SSO (토큰 전달)
- [x] TokenSyncProvider (토큰 수신)
- [x] 홈 화면 카드 (포털 링크)

### 다음 작업
- [ ] package.json 포트 설정 (3001/3002/3003)
- [ ] Backend CORS 설정
- [ ] 테스트 데이터 생성
- [ ] 알파 테스트 실행

---

**작성:** GitHub Copilot  
**Phase:** 1A - Week 4 Alpha Test  
**목표:** "실제 사람이 쓸 수 있는" IRT/CAT 리포트 엔진 통합 🚀
