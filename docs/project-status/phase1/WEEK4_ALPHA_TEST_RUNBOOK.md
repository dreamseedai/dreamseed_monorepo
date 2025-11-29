# Week 4 Alpha Test Runbook 🚀

**목표**: 4개 포털 통합 시스템을 실제 사용자(또는 롤플레이)로 1회 완전 테스트

**예상 소요 시간**: 90분 (준비 30분 + 테스트 60분)

**테스트 일시**: 2025-11-25 19:00 ~ 20:30

---

## 🎭 테스트 인원 구성

### 최소 구성 (1인 롤플레이 가능)

| 역할 | 계정 | 포털 | 주요 액션 |
|------|------|------|-----------|
| 👨‍🎓 학생 | student1@test.com | 3001 | CAT 시험 2회, 대시보드 확인 |
| 👨‍🎓 학생 | student2@test.com | 3001 | CAT 시험 1회 |
| 🏫 학교 선생님 | teacher@school.com | 3002 | 학급 목록, 코멘트 작성 |
| 👨‍🏫 학원 튜터 | tutor@academy.com | 3003 | 우선순위 리스트, 코멘트 작성 |
| 👨‍👩‍👧 학부모 | parent@test.com | 3004 | 자녀 선택, PDF 다운로드 |

### 이상적 구성 (5명 실제 테스터)

- **학생 2-3명**: 실제 중·고등학생 (친구/가족)
- **선생님 1명**: 학교/학원 교사 지인
- **학부모 1-2명**: 자녀 교육에 관심 있는 분
- **관찰자 1명**: 사용 과정을 옆에서 메모

---

## 📋 사전 준비 (30분)

### Step 1: 데이터베이스 준비 (10분)

```bash
# Terminal 1: Backend 디렉토리
cd /home/won/projects/dreamseed_monorepo/backend
source .venv/bin/activate

# 1. 마이그레이션 실행
alembic upgrade head

# 2. 테스트 데이터 시딩 (스크립트 필요 시 작성)
# python scripts/seed_week4_alpha.py

# 또는 SQL로 직접:
# psql -h localhost -p 5433 -U dreamseed_user -d dreamseed_dev
# INSERT INTO users (email, hashed_password, role, is_active) VALUES ...
# INSERT INTO parent_child_links (parent_id, child_id) VALUES ...
```

### Step 2: 5개 앱 실행 (10분)

```bash
# Terminal 1: Backend (Port 8001)
cd /home/won/projects/dreamseed_monorepo/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8001

# Terminal 2: Portal (Port 5172)
cd /home/won/projects/dreamseed_monorepo/portal_front
npm run dev

# Terminal 3: Student (Port 3001)
cd /home/won/projects/dreamseed_monorepo/apps/student_front
npm run dev

# Terminal 4: Teacher (Port 3002)
cd /home/won/projects/dreamseed_monorepo/apps/teacher_front
npm run dev

# Terminal 5: Tutor (Port 3003)
cd /home/won/projects/dreamseed_monorepo/apps/tutor_front
npm run dev

# Terminal 6: Parent (Port 3004)
cd /home/won/projects/dreamseed_monorepo/apps/parent_front
npm run dev
```

### Step 3: 헬스 체크 (5분)

```bash
# 1. Backend API 확인
curl http://localhost:8001/health
# Expected: {"status":"healthy","phase":"Phase 1 MVP"}

# 2. Portal 확인
curl http://localhost:5172
# Expected: HTML 응답

# 3. 4개 프론트 확인
curl http://localhost:3001  # Student
curl http://localhost:3002  # Teacher
curl http://localhost:3003  # Tutor
curl http://localhost:3004  # Parent
```

### Step 4: 브라우저 준비 (5분)

- **Chrome/Firefox** 최신 버전 사용
- **Developer Tools** 열어두기 (F12)
  - Console 탭: JavaScript 에러 확인
  - Network 탭: API 호출 확인
  - Application 탭: localStorage access_token 확인

---

## 🧪 테스트 시나리오 (60분)

### Scenario 1: 학생 - CAT 시험 응시 (15분)

**목표**: θ 추정 → 대시보드 표시 확인

1. **로그인**:
   ```
   URL: http://localhost:5172
   Email: student1@test.com
   Password: password
   ```

2. **자동 라우팅 확인**:
   - 로그인 후 `/portal` 진입
   - **기대 결과**: `/portal/student` (3001 iframe)로 자동 이동
   - **체크**: URL이 `http://localhost:5172/portal/student`인지

3. **SSO 토큰 확인**:
   - F12 → Application → localStorage
   - **기대 결과**: `access_token` 존재
   - **체크**: Portal(5172)과 iframe 내부(3001) 모두에 토큰 있는지

4. **CAT 시험 응시**:
   - "시험 시작" 버튼 클릭
   - 문항 5-10개 응답 (정답/오답 섞어서)
   - **기대 결과**: 
     - 각 문항마다 난이도가 적응적으로 변함
     - θ 실시간 업데이트 (진행 바 또는 상태 표시)
   - **체크**: Console에 IRT 계산 에러 없는지

5. **대시보드 확인**:
   - 시험 완료 후 대시보드 페이지 이동
   - **기대 결과**:
     - θ 값 표시 (예: 0.45)
     - Band 표시 (A/B+/B/C/D)
     - SE 표시 (예: 0.35)
     - Risk Level (HIGH/MEDIUM/LOW)
   - **체크**: 
     - 값이 합리적인지 (θ: -3 ~ +3 범위)
     - Band와 θ가 일치하는지 (θ=0.45 → B+ 밴드)

6. **2차 시험 응시** (optional):
   - 같은 과목 다시 응시
   - **기대 결과**: θ가 변화하고, Δθ가 계산됨

**✅ 통과 조건**:
- [ ] 로그인 → 자동 라우팅 성공
- [ ] SSO 토큰 양쪽에 존재
- [ ] CAT 시험 완주 (에러 없이)
- [ ] 대시보드에 θ/Band/Risk 표시

**🐛 예상 버그**:
- SSO 토큰 안 넘어옴 → postMessage 타이밍 이슈
- θ 계산 에러 → IRT 엔진 파라미터 문제
- 대시보드 로딩 무한 → API 401/403 에러

---

### Scenario 2: 학교 선생님 - 학급 관리 (10분)

**목표**: 학생 목록 + θ 추적 + 코멘트 작성

1. **로그인**:
   ```
   URL: http://localhost:5172
   Email: teacher@school.com
   Password: password
   ```

2. **Teacher Portal 진입**:
   - **기대 결과**: `/portal/teacher` (3002 iframe)로 이동
   - **체크**: 학교 조직(PUBLIC_SCHOOL/PRIVATE_SCHOOL) 계정인지 확인

3. **학급 목록 조회**:
   - Subject 선택: "수학"
   - Class 선택: "3-1" (optional)
   - Window Days: 30일
   - **기대 결과**: 
     - GET `/api/teacher/class-list?subject=math&klass=3-1&window_days=30`
     - 학생 리스트 테이블 표시:
       | 이름 | θ | Band | Risk | Δθ14d |
       |------|---|------|------|-------|
       | 학생1 | 0.45 | B+ | LOW | +0.12 |

4. **학생 상세 보기** (optional):
   - 학생 행 클릭
   - **기대 결과**: 학생 상세 페이지 또는 모달

5. **코멘트 작성**:
   - 학생 선택 → "코멘트 작성" 버튼
   - 섹션별 입력:
     - Summary: "최근 4주간 꾸준히 성장"
     - Next 4W Plan: "함수 단원 집중 학습"
     - Parent Guidance: "가정에서 복습 권장"
   - 언어: 한국어
   - 상태: "Published"
   - **기대 결과**: 
     - POST `/api/teacher/reports/{student_id}/comments`
     - 성공 메시지 표시

**✅ 통과 조건**:
- [ ] Teacher Portal 접근 성공
- [ ] 학급 목록 API 호출 성공
- [ ] 학생 데이터 테이블 표시
- [ ] 코멘트 작성/저장 성공

**🐛 예상 버그**:
- 학급 목록 빈 배열 → StudentOrgEnrollment 데이터 없음
- θ 값 null → IRTStudentAbility 레코드 없음
- 코멘트 저장 실패 → report_comments 테이블 제약 조건

---

### Scenario 3: 튜터 - 우선순위 관리 (10분)

**목표**: 위험 학생 파악 + 개별 코멘트

1. **로그인**:
   ```
   Email: tutor@academy.com
   Password: password
   ```

2. **Tutor Portal 진입**:
   - **기대 결과**: `/portal/tutor` (3003 iframe)
   - **체크**: 학원/과외 조직(ACADEMY/TUTORING_CENTER) 계정

3. **우선순위 리스트 조회**:
   - Subject: "수학"
   - Window Days: 14일
   - **기대 결과**:
     - GET `/api/tutor/priorities?subject=math&windowDays=14`
     - 우선순위 순 정렬 (risk_level, Δθ14d 기반)
     - 테이블:
       | Priority | 학생 | θ | Δθ14d | Risk | Flags |
       |----------|------|---|-------|------|-------|
       | 1 | 학생2 | -0.8 | -0.25 | HIGH | 🚨 급락 |

4. **위험 학생 코멘트 작성**:
   - Priority 1 학생 선택
   - 코멘트 입력:
     - Summary: "개념 이해도 급락, 즉시 개입 필요"
     - Next 4W Plan: "기초 개념 재학습 + 1:1 튜터링"
     - Parent Guidance: "학습 동기 저하 우려, 상담 권장"
   - **기대 결과**: 저장 성공

**✅ 통과 조건**:
- [ ] Tutor Portal 접근 성공
- [ ] 우선순위 리스트 표시
- [ ] Priority 점수 계산 정확
- [ ] 코멘트 작성 성공

---

### Scenario 4: 학부모 - PDF 다운로드 (15분)

**목표**: 멀티소스 리포트 통합 확인

1. **로그인**:
   ```
   Email: parent@test.com
   Password: password
   ```

2. **Parent Portal 진입**:
   - **기대 결과**: `/portal/parent` (3004 iframe)

3. **자녀 목록 조회**:
   - **기대 결과**:
     - GET `/api/parent/children`
     - 드롭다운에 자녀 리스트 표시:
       - 학생1 (student1@test.com)
       - 학생2 (student2@test.com)

4. **자녀 선택 + 기간 선택**:
   - 자녀: "학생1"
   - 기간: "최근 4주" (last4w)
   - **기대 결과**: UI 업데이트

5. **PDF 다운로드**:
   - "다운로드" 버튼 클릭
   - **기대 결과**:
     - GET `/api/parent/reports/{student_id}/pdf?period=last4w`
     - 브라우저 다운로드 시작
     - 파일명: `DreamSeed_Report_{student_id}_last4w.pdf`

6. **PDF 내용 검증**:
   - PDF 열기
   - **체크 항목**:
     - [ ] 학생 정보 (이름, 학교, 학년)
     - [ ] 기간 표시 (2025-10-28 ~ 2025-11-25)
     - [ ] 과목별 요약:
       - [ ] θ 값
       - [ ] Band (A/B+/B/C/D)
       - [ ] Percentile
       - [ ] Δθ 4주
       - [ ] Risk Level
     - [ ] θ 추이 그래프 (시계열 차트)
     - [ ] 학교 선생님 코멘트 섹션:
       - [ ] Summary
       - [ ] Next 4W Plan
       - [ ] Parent Guidance
     - [ ] 튜터 코멘트 섹션 (있다면)
     - [ ] 종합 학부모 가이던스
     - [ ] 폰트/레이아웃 깨짐 없음

7. **다른 기간 테스트** (optional):
   - "최근 8주" 선택 → PDF 다운로드
   - **체크**: 기간이 바뀌면 데이터도 변경되는지

**✅ 통과 조건**:
- [ ] Parent Portal 접근 성공
- [ ] 자녀 목록 표시
- [ ] PDF 다운로드 성공 (HTTP 200)
- [ ] PDF 내용 완전성 (모든 섹션 존재)
- [ ] 멀티소스 통합 (teacher + tutor 코멘트 모두 포함)

**🐛 예상 버그**:
- 자녀 목록 빔 → parent_child_links 데이터 없음
- PDF 생성 500 에러 → WeasyPrint 설치/폰트 문제
- 코멘트 섹션 빔 → report_comments 데이터 없음
- 그래프 깨짐 → matplotlib PNG 생성 실패

---

### Scenario 5: SSO 통합 테스트 (10분)

**목표**: 토큰 동기화 확인

1. **Portal 로그인** (student 계정)
2. **Student Portal 진입** → localStorage 확인
3. **Teacher Portal 수동 이동**:
   - URL 직접 입력: `http://localhost:5172/portal/teacher`
   - **기대 결과**: 403 Forbidden (권한 없음)
4. **로그아웃**:
   - Portal에서 로그아웃 버튼
   - **기대 결과**:
     - localStorage에서 access_token 삭제
     - 4개 iframe 모두 토큰 삭제 (storage 이벤트)
5. **재로그인** (teacher 계정):
   - **기대 결과**:
     - 새 토큰 발급
     - 모든 iframe에 새 토큰 전파
     - Teacher Portal 정상 접근

**✅ 통과 조건**:
- [ ] 로그인 → 모든 iframe에 토큰 전파
- [ ] 역할 기반 접근 제어 (403 정상 동작)
- [ ] 로그아웃 → 모든 iframe 토큰 삭제
- [ ] 재로그인 → 새 토큰 전파

---

## 📊 테스트 결과 기록

### 체크리스트 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| Backend 실행 | ⬜ |  |
| 5개 프론트 실행 | ⬜ |  |
| Student: CAT 시험 | ⬜ |  |
| Student: 대시보드 | ⬜ |  |
| Teacher: 학급 목록 | ⬜ |  |
| Teacher: 코멘트 작성 | ⬜ |  |
| Tutor: 우선순위 | ⬜ |  |
| Tutor: 코멘트 작성 | ⬜ |  |
| Parent: 자녀 목록 | ⬜ |  |
| Parent: PDF 다운로드 | ⬜ |  |
| PDF 내용 완전성 | ⬜ |  |
| SSO 토큰 동기화 | ⬜ |  |
| 역할 기반 라우팅 | ⬜ |  |

### 발견된 이슈

| 번호 | 우선순위 | 이슈 설명 | 재현 방법 | 담당 |
|------|----------|-----------|-----------|------|
| 1 | 🔴 High |  |  |  |
| 2 | 🟡 Medium |  |  |  |
| 3 | 🟢 Low |  |  |  |

### 사용자 피드백 (정성적)

**좋았던 점 2가지**:
1. 
2. 

**혼란스러웠던 점 2가지**:
1. 
2. 

**꼭 추가됐으면 하는 것 1가지**:
1. 

---

## 🐛 트러블슈팅 가이드

### 1. SSO 토큰이 iframe에 안 넘어옴

**증상**: iframe 앱에서 401 Unauthorized

**진단**:
```javascript
// Portal(5172) Console
console.log(localStorage.getItem('access_token'));  // 있어야 함

// iframe(3001) Console
console.log(localStorage.getItem('access_token'));  // 비어있음
```

**해결**:
1. `portal_front/src/components/AppFrame.tsx` 확인:
   - postMessage 코드 있는지
   - iframe.onload 이벤트 등록되었는지
2. `apps/*/src/app/TokenSyncProvider.tsx` 확인:
   - addEventListener("message") 있는지
3. 브라우저 Console에서 수동 테스트:
   ```javascript
   // Portal에서 실행
   const iframe = document.querySelector('iframe');
   iframe.contentWindow.postMessage({type: 'SET_TOKEN', token: 'test123'}, '*');
   
   // iframe에서 확인
   console.log(localStorage.getItem('access_token')); // 'test123' 나와야 함
   ```

### 2. CORS 에러

**증상**: Network 탭에 `Access-Control-Allow-Origin` 에러

**해결**:
```python
# backend/main.py 확인
allow_origins=[
    "http://localhost:5172",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
]
```

Backend 재시작: `uvicorn main:app --reload --port 8001`

### 3. PDF 생성 500 에러

**증상**: `/api/parent/reports/{id}/pdf` 호출 시 500

**진단**:
```bash
# Backend 터미널에서 에러 로그 확인
# 주로 WeasyPrint 또는 matplotlib 문제
```

**해결**:
```bash
# 1. WeasyPrint 재설치
pip install --upgrade weasyprint

# 2. 한글 폰트 확인 (Ubuntu)
sudo apt-get install fonts-nanum fonts-nanum-coding

# 3. matplotlib 백엔드 확인
# pdf_report_service.py 첫 줄에 matplotlib.use('Agg') 있는지
```

### 4. 테이블이 비어있음

**증상**: Teacher class-list 또는 Parent children이 빈 배열

**해결**:
```sql
-- DB 직접 확인
psql -h localhost -p 5433 -U dreamseed_user -d dreamseed_dev

-- 1. parent_child_links 확인
SELECT * FROM parent_child_links;

-- 2. StudentOrgEnrollment 확인
SELECT * FROM student_org_enrollments;

-- 3. IRTStudentAbility 확인
SELECT * FROM irt_student_abilities ORDER BY calibrated_at DESC LIMIT 10;

-- 없다면 수동 삽입 또는 seed 스크립트 실행
```

---

## 📦 다음 단계 (Alpha → Beta)

### Immediate Fixes (Week 4 Day 4-5)

발견된 🔴 High 이슈들 수정

### Phase 1B 후보 기능 (Week 5+)

- [ ] 실시간 θ 업데이트 (WebSocket)
- [ ] 학생별 학습 추천 (AI 기반)
- [ ] 모바일 반응형 UI
- [ ] 다국어 지원 (영어/한국어 토글)
- [ ] 학부모 알림 (이메일/SMS)
- [ ] 엑셀 다운로드 (teacher/tutor)

### Infrastructure 개선

- [ ] CI/CD 파이프라인 (GitHub Actions)
- [ ] Production 배포 (GCP/AWS)
- [ ] 모니터링 (Sentry, Datadog)
- [ ] 부하 테스트 (Locust)

---

## ✅ Alpha Test 성공 기준

**기술적 성공**:
- [ ] 5개 앱 모두 정상 실행
- [ ] SSO 토큰 동기화 100% 성공
- [ ] CAT 시험 → θ 계산 → 대시보드 표시 정상
- [ ] Teacher/Tutor 코멘트 → Parent PDF 통합 정상
- [ ] Critical bug 0개

**사용자 경험 성공**:
- [ ] 테스터가 매뉴얼 없이 30분 내 주요 기능 사용 가능
- [ ] "이걸 실제로 쓰고 싶다"는 피드백 1개 이상
- [ ] 혼란스러운 부분 명확히 파악 (다음 단계 개선 방향)

**비즈니스 검증**:
- [ ] Teacher가 학생 관리에 실제 도움된다고 느낌
- [ ] Parent가 PDF 리포트를 유용하다고 평가
- [ ] Student가 θ 추적이 동기부여된다고 느낌

---

## 🎉 결론

**현재 상태**: Phase 1A MVP 완성 ✅

**다음 마일스톤**: Week 4 Alpha Test 실행 → 피드백 수집 → Phase 1B 기획

**기대 효과**:
- IRT 기반 적응형 평가 시스템 실증
- 멀티소스 리포트의 실용성 검증
- 3축 조직 구조의 확장 가능성 확인

이제 진짜 "사람을 넣어서 돌려볼" 시간입니다! 🚀
