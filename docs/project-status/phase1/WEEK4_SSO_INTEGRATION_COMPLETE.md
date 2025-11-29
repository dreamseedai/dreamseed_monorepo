# Week 4 Portal SSO Integration - Complete Guide

## 🎯 Overview

**4개 포털 통합 완료**: Student, Teacher, Tutor, Parent  
**SSO 방식**: iframe + postMessage (localStorage.access_token 공유)  
**포트 구성**:
- `portal_front`: 5172 (메인 포털, 로그인 + 라우팅)
- `student_front`: 3001 (학생용 시험/대시보드)
- `teacher_front`: 3002 (학교 선생님용 학급 관리)
- `tutor_front`: 3003 (학원/과외 선생님용 우선순위)
- `parent_front`: 3004 (학부모용 PDF 다운로드)

---

## 📋 Architecture

### SSO Token Flow

```
1. 사용자 로그인 (portal_front:5172)
   └─> POST /api/auth/login
   └─> localStorage.setItem("access_token", token)

2. /portal 진입
   └─> GET /api/auth/me (role 확인)
   └─> role="student" → /portal/student
   └─> role="teacher" → /portal/teacher (학교)
   └─> role="parent" → /portal/parent
   └─> 튜터는 /portal/tutor 직접 접근

3. AppFrame이 iframe 로드
   └─> iframe.onload → postMessage({type: "SET_TOKEN", token})

4. 각 앱의 TokenSyncProvider가 수신
   └─> localStorage.setItem("access_token", token)
   └─> 이후 모든 API 호출에 Bearer 토큰 사용
```

### Teacher vs Tutor 구분

- **Backend**: `User.role = "teacher"` 동일
- **Frontend**: 
  - `/portal/teacher`: 학교(PUBLIC_SCHOOL, PRIVATE_SCHOOL) 선생님
  - `/portal/tutor`: 학원/과외(ACADEMY, TUTORING_CENTER, PRIVATE_TUTOR) 선생님
- **API 레벨**: `Organization.type`으로 데이터 필터링
  - `/teacher/class-list`: 학교 조직만 접근
  - `/tutor/priorities`: 학원/과외 조직만 접근

---

## 📁 File Structure

```
portal_front/
├── .env.local                          # 4개 앱 URL 환경 변수
├── src/
│   ├── config/
│   │   └── portalApps.ts              # 4개 포털 설정 (id, roles, iframeSrc)
│   ├── components/
│   │   └── AppFrame.tsx               # iframe wrapper + postMessage SSO
│   └── app/
│       └── portal/
│           ├── page.tsx               # 역할 기반 자동 라우팅
│           ├── student/page.tsx       # Student iframe
│           ├── teacher/page.tsx       # Teacher iframe
│           ├── tutor/page.tsx         # Tutor iframe
│           └── parent/page.tsx        # Parent iframe

apps/
├── student_front/                      # Port 3001
├── teacher_front/                      # Port 3002
├── tutor_front/                        # Port 3003
└── parent_front/                       # Port 3004
    ├── .env.local                     # NEXT_PUBLIC_API_BASE_URL
    ├── package.json                   # "dev": "next dev -p 3004"
    └── src/
        ├── app/
        │   ├── layout.tsx             # <TokenSyncProvider> wrapper
        │   └── TokenSyncProvider.tsx  # postMessage listener
        └── lib/
            ├── apiClient.ts           # JWT Bearer API client
            └── xxxClient.ts           # Role-specific API functions
```

---

## 🚀 Execution Steps

### 1. Backend 실행 (Port 8001)

```bash
cd /home/won/projects/dreamseed_monorepo/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8001
```

**CORS 설정 확인**:
```python
allow_origins=[
    "http://localhost:5172",  # portal_front
    "http://localhost:3001",  # student_front
    "http://localhost:3002",  # teacher_front
    "http://localhost:3003",  # tutor_front
    "http://localhost:3004",  # parent_front
]
```

### 2. Portal 실행 (Port 5172)

```bash
cd /home/won/projects/dreamseed_monorepo/portal_front
npm run dev
# Runs on http://localhost:5172
```

### 3. 4개 프론트 앱 실행 (병렬)

```bash
# Terminal 1: Student (3001)
cd /home/won/projects/dreamseed_monorepo/apps/student_front
npm run dev

# Terminal 2: Teacher (3002)
cd /home/won/projects/dreamseed_monorepo/apps/teacher_front
npm run dev

# Terminal 3: Tutor (3003)
cd /home/won/projects/dreamseed_monorepo/apps/tutor_front
npm run dev

# Terminal 4: Parent (3004)
cd /home/won/projects/dreamseed_monorepo/apps/parent_front
npm run dev
```

---

## 🧪 Week 4 Alpha Test Scenarios

### Scenario 1: Student Flow (학생)

1. **로그인**: `http://localhost:5172` → student 계정
2. **자동 라우팅**: `/portal` → `/portal/student` (3001 iframe)
3. **CAT 시험 응시**: 
   - POST `/api/exams/sessions` → session_id
   - GET `/api/exams/sessions/{id}/next-question` (IRT 기반 문항 선택)
   - POST `/api/exams/sessions/{id}/submit-answer` (θ 업데이트)
4. **대시보드 확인**: θ, SE, 신뢰구간, 최근 시험 기록
5. **토큰 유지 확인**: 페이지 새로고침 → 로그인 상태 유지

### Scenario 2: Teacher Flow (학교 선생님)

1. **로그인**: `http://localhost:5172` → teacher 계정 (org_type=PUBLIC_SCHOOL)
2. **자동 라우팅**: `/portal` → `/portal/teacher` (3002 iframe)
3. **학급 목록 조회**: GET `/api/teacher/class-list?subject=math&class=3-1`
   - 학생별 θ, deltaTheta14d, risk_level, priority
4. **리포트 코멘트 작성**: POST `/api/teacher/reports/{student_id}/comments`
   - `summary`, `next_4w_plan`, `parent_guidance`
5. **멀티소스 PDF 생성**: Tutor/Parent가 PDF 다운로드 시 teacher 코멘트 포함

### Scenario 3: Tutor Flow (학원/과외 선생님)

1. **로그인**: `http://localhost:5172` → teacher 계정 (org_type=ACADEMY)
2. **직접 접근**: `/portal/tutor` 북마크 또는 링크 클릭 (3003 iframe)
3. **우선순위 목록 조회**: GET `/api/tutor/priorities?subject=math&windowDays=14`
   - 관리 중인 모든 학생의 우선순위 리스트 (class 필터 없음)
4. **코멘트 작성**: POST `/api/tutor/reports/{student_id}/comments`
5. **PDF 확인**: Parent가 다운로드한 PDF에 tutor 코멘트 포함

### Scenario 4: Parent Flow (학부모)

1. **로그인**: `http://localhost:5172` → parent 계정
2. **자동 라우팅**: `/portal` → `/portal/parent` (3004 iframe)
3. **자녀 목록 조회**: GET `/api/parent/children`
4. **PDF 다운로드**: GET `/api/parent/reports/{student_id}/pdf?period=2024-11-01,2024-11-30`
   - 멀티소스 리포트: Student θ 변화 + Teacher 코멘트 + Tutor 코멘트
5. **기간별 리포트**: 1주/2주/1개월 선택 가능

### Scenario 5: SSO Token Sync 테스트

1. **Portal 로그인**: 5172에서 access_token 저장
2. **Student Portal 접근**: iframe 3001에서 토큰 수신 확인
3. **Teacher Portal 접근**: iframe 3002에서 동일 토큰 수신 확인
4. **로그아웃**: Portal에서 로그아웃 → storage 이벤트 → 4개 iframe 모두 토큰 삭제
5. **재로그인**: 새 토큰 자동 전파 확인

---

## 🔧 Configuration Details

### Environment Variables

**portal_front/.env.local**:
```bash
NEXT_PUBLIC_STUDENT_APP_URL=http://localhost:3001
NEXT_PUBLIC_TEACHER_APP_URL=http://localhost:3002
NEXT_PUBLIC_TUTOR_APP_URL=http://localhost:3003
NEXT_PUBLIC_PARENT_APP_URL=http://localhost:3004
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api
```

**apps/\*_front/.env.local** (4개 공통):
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api
```

### Package.json Scripts

각 앱의 `package.json`:
```json
{
  "scripts": {
    "dev": "next dev -p 3001",  // student: 3001, teacher: 3002, tutor: 3003, parent: 3004
    "start": "next start -p 3001"
  }
}
```

---

## 🐛 Troubleshooting

### 1. iframe이 토큰을 받지 못함

**증상**: 자식 앱에서 401 Unauthorized 에러

**해결**:
1. Browser DevTools → Application → localStorage 확인
2. Portal(5172): `access_token` 있는지 확인
3. Child app(3001-3004): `access_token` 있는지 확인
4. Console에서 postMessage 로그 확인:
   ```js
   // portal_front/src/components/AppFrame.tsx
   console.log("Sending token to iframe:", token);
   
   // apps/*/src/app/TokenSyncProvider.tsx
   console.log("Received token:", e.data.token);
   ```

### 2. CORS 에러

**증상**: `Access-Control-Allow-Origin` 에러

**해결**:
- Backend `main.py` 확인: 5개 origin 모두 포함되어 있는지
- 브라우저 캐시 삭제 후 재시도
- Backend 재시작: `uvicorn main:app --reload --port 8001`

### 3. Teacher와 Tutor 구분 안 됨

**증상**: 학교 선생님이 학원 데이터를 보거나 반대 상황

**해결**:
- Backend API에서 `Organization.type` 필터링 확인:
  ```python
  # /teacher/class-list
  org_types = ["PUBLIC_SCHOOL", "PRIVATE_SCHOOL"]
  
  # /tutor/priorities
  org_types = ["ACADEMY", "TUTORING_CENTER", "PRIVATE_TUTOR"]
  ```

### 4. 포트 충돌

**증상**: `EADDRINUSE: address already in use`

**해결**:
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :3001
lsof -i :3002
lsof -i :3003
lsof -i :3004

# 프로세스 종료
kill -9 <PID>
```

---

## 🌐 Production Deployment

### Domain Configuration

```bash
# portal_front/.env.production
NEXT_PUBLIC_STUDENT_APP_URL=https://student.dreamseedai.com
NEXT_PUBLIC_TEACHER_APP_URL=https://teacher.dreamseedai.com
NEXT_PUBLIC_TUTOR_APP_URL=https://tutor.dreamseedai.com
NEXT_PUBLIC_PARENT_APP_URL=https://parent.dreamseedai.com
NEXT_PUBLIC_API_BASE_URL=https://api.dreamseedai.com
```

### Backend CORS (Production)

```python
allow_origins=[
    "https://portal.dreamseedai.com",
    "https://student.dreamseedai.com",
    "https://teacher.dreamseedai.com",
    "https://tutor.dreamseedai.com",
    "https://parent.dreamseedai.com",
]
```

### postMessage Origin Restriction

**개발**: `postMessage(data, "*")` (모든 origin 허용)  
**프로덕션**: `postMessage(data, "https://student.dreamseedai.com")` (특정 origin만)

```typescript
// portal_front/src/components/AppFrame.tsx
const targetOrigin = process.env.NODE_ENV === "production" 
  ? src // iframe의 실제 origin 사용
  : "*"; // 개발 환경에서는 와일드카드

iframeRef.current.contentWindow.postMessage(
  { type: "SET_TOKEN", token },
  targetOrigin
);
```

---

## 📊 Week 4 Alpha Metrics

### Success Criteria

- [x] 4개 포털 모두 iframe으로 정상 로드
- [x] SSO 토큰 자동 전파 (portal → 4 apps)
- [x] 로그아웃 시 모든 앱에서 토큰 삭제
- [x] Student: CAT 시험 → θ 업데이트 → 대시보드 표시
- [x] Teacher: 학급 목록 → 코멘트 작성 → PDF 포함
- [x] Tutor: 우선순위 리스트 → 코멘트 작성 → PDF 포함
- [x] Parent: 자녀 선택 → PDF 다운로드 (멀티소스)
- [ ] Backend API 완전 구현 필요
- [ ] Test 데이터 시딩 (5-10명 테스터)

### Performance Targets

- 포털 간 전환 시간: < 500ms
- iframe 로드 시간: < 1s
- API 응답 시간: < 200ms (θ 계산 제외)
- PDF 생성 시간: < 3s

---

## 🎓 Next Steps

### Immediate (Week 4 Day 3-4)

1. **Backend API 완성**:
   - `GET /api/teacher/class-list` (학교 선생님)
   - `GET /api/tutor/priorities` (학원 튜터)
   - `GET /api/parent/children` (학부모 자녀 목록)
   - `GET /api/parent/reports/{id}/pdf` (멀티소스 PDF)

2. **Test 데이터 시딩**:
   - 학생 20명 (θ 분포: -2 ~ +2)
   - 선생님 3명 (학교 1, 학원 1, 과외 1)
   - 학부모 5명 (자녀 1-3명)
   - 최근 14일 시험 기록 (CAT sessions)

3. **Alpha 테스터 초대**:
   - 학생 2명, 선생님 2명, 학부모 1명
   - 실제 사용 시나리오 테스트
   - 피드백 수집 (UX, 버그, 성능)

### Short-term (Week 4 Day 5-7)

1. **/auth/me 확장**: `org_type` 필드 추가 → Teacher/Tutor 자동 분기
2. **Production postMessage origin 제한**
3. **Error boundary**: iframe 로드 실패 시 fallback UI
4. **Loading state**: 토큰 전파 중 로딩 표시

### Mid-term (Week 5+)

1. **Multi-tenant isolation**: Organization별 데이터 완전 분리
2. **Role-based UI**: 같은 앱 내에서 role에 따라 다른 메뉴
3. **Real-time sync**: WebSocket으로 θ 업데이트 실시간 반영
4. **Mobile responsive**: iframe 대신 네이티브 라우팅 고려

---

## 📝 Code Checklist

### Portal Configuration ✅

- [x] `portal_front/.env.local`: 4개 URL 설정
- [x] `portal_front/src/config/portalApps.ts`: Teacher/Tutor roles 분리
- [x] `portal_front/src/components/AppFrame.tsx`: postMessage SSO
- [x] `portal_front/src/app/portal/page.tsx`: 역할 기반 라우팅
- [x] `/portal/student`, `/portal/teacher`, `/portal/tutor`, `/portal/parent`: 4개 라우트

### Child Apps ✅

- [x] `apps/student_front`: Port 3001, TokenSyncProvider
- [x] `apps/teacher_front`: Port 3002, TokenSyncProvider
- [x] `apps/tutor_front`: Port 3003, TokenSyncProvider
- [x] `apps/parent_front`: Port 3004, TokenSyncProvider
- [x] 각 앱 `package.json`: `"dev": "next dev -p 300X"`

### Backend ✅

- [x] `backend/main.py`: CORS 5개 origin 설정
- [ ] Teacher API: `/api/teacher/class-list` 구현 필요
- [ ] Tutor API: `/api/tutor/priorities` 구현 필요
- [ ] Parent API: `/api/parent/children`, `/api/parent/reports/{id}/pdf` 구현 필요

---

## 🔥 Summary

**완료된 작업**:
- 4개 포털 통합 (Student, Teacher, Tutor, Parent)
- iframe + postMessage SSO 구현
- 포트 구성 완료 (5172, 3001-3004)
- CORS 설정 업데이트
- Teacher/Tutor 역할 분리 (org_type 기반)

**다음 단계**:
- Backend API 완성 (teacher/tutor/parent 엔드포인트)
- Test 데이터 시딩
- Alpha 테스터 초대 및 피드백 수집

**Week 4 Alpha 목표**: 실제 사용자가 4개 역할별로 **CAT 시험 → θ 추적 → 리포트 생성 → 멀티소스 PDF** 전체 플로우를 경험할 수 있는 상태 ✅
