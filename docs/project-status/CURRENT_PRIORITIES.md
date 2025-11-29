# 🎯 현재 우선순위 작업

**업데이트:** 2025-11-24  
**검토 주기:** 매주 금요일

---

## 🔥 Critical (최우선 - 이번 주)

### 1. Phase 0.5 CAT/IRT 엔진 설계 완료
**담당:** AI Team  
**마감:** 2025-11-29  
**진행률:** 20%

#### 작업 내용
- [ ] CAT 알고리즘 설계 문서 작성
- [ ] IRT 파라미터 추정 방법 결정
- [ ] R Plumber 통합 방식 확정
- [ ] Python 구현 계획 수립

#### 블로커
- IRT 이론 전문가 부족
- R 환경 설정 미완료

#### 다음 액션
- AI Team 주간 회의 (화요일)
- R Plumber POC 작성 (수요일)
- 설계 리뷰 (금요일)

---

### 2. Phase 1 Admin Dashboard 로그인 API 연동
**담당:** Frontend Team  
**마감:** 2025-11-29  
**진행률:** 50%

#### 작업 내용
- [x] 로그인 폼 UI 구현
- [ ] API 클라이언트 설정
- [ ] 토큰 저장 로직 구현
- [ ] 에러 핸들링
- [ ] 리다이렉션 처리

#### 블로커
- API 문서 불완전
- 인증 플로우 불명확

#### 다음 액션
- Backend Team과 API 스펙 확인 (월요일)
- TanStack Query 설정 (화요일)
- 로그인 연동 완료 (목요일)

---

### 3. My-Ktube.ai 도메인 Cloudflare 이전
**담당:** DevOps Team  
**마감:** 2025-11-30  
**진행률:** 0%

#### 작업 내용
- [ ] Namecheap 계정 로그인
- [ ] Cloudflare Transfer Lock 해제
- [ ] Authorization Code 발급
- [ ] Cloudflare 이전 신청
- [ ] DNS 레코드 설정

#### 블로커
- 없음

#### 다음 액션
- Namecheap 작업 시작 (월요일 오전)
- Cloudflare 이전 (월요일 오후)
- DNS 전파 확인 (화요일)

---

## ⚠️ High (높음 - 다음 주)

### 4. Phase 0 DB Schema 완성
**담당:** Backend Team  
**마감:** 2025-12-06  
**진행률:** 50%

#### 작업 내용
- [x] 기본 4개 테이블 (users, problems, submissions, progress)
- [ ] 조직 관련 (organizations, zones)
- [ ] 시험 관련 (exams, exam_attempts, questions)
- [ ] 로깅 (ai_requests, audit_log)
- [ ] RLS 정책 적용

#### 예상 소요 시간
- 2일 (스키마 설계)
- 1일 (마이그레이션 작성)
- 1일 (RLS 정책 적용)

---

### 5. Phase 1 Admin Dashboard 홈 대시보드 개발
**담당:** Frontend Team  
**마감:** 2025-12-08  
**진행률:** 0%

#### 작업 내용
- [ ] 레이아웃 구조 설계
- [ ] 통계 카드 컴포넌트
- [ ] 최근 활동 리스트
- [ ] 차트 통합 (Recharts)
- [ ] API 연동

#### 의존성
- 로그인 API 연동 완료 필요

---

### 6. Phase 0.5 시드 데이터 생성 스크립트
**담당:** QA Team + Backend Team  
**마감:** 2025-12-10  
**진행률:** 0%

#### 작업 내용
- [ ] 사용자 생성 (100명)
- [ ] 조직 생성 (5개)
- [ ] 문제 생성 (1,000개)
- [ ] 답안 생성 (10,000개)
- [ ] Python 스크립트 작성

#### 예상 소요 시간
- 3일

---

## 📋 Medium (보통 - 2주 이내)

### 7. Reverse Proxy 구성
**담당:** DevOps Team  
**마감:** 2025-12-13  
**진행률:** 0%

#### 작업 내용
- [ ] Nginx vs Traefik 선택
- [ ] 설정 파일 작성
- [ ] Upstream 서버 설정
- [ ] Health Check 설정
- [ ] SSL/TLS 자동 갱신

---

### 8. API 문서 자동 생성 개선
**담당:** Backend Team  
**마감:** 2025-12-15  
**진행률:** 30%

#### 작업 내용
- [ ] FastAPI 스키마 개선
- [ ] 예제 요청/응답 추가
- [ ] 인증 플로우 설명
- [ ] Redoc 테마 커스터마이징

---

### 9. E2E 테스트 자동화
**담당:** QA Team  
**마감:** 2025-12-20  
**진행률:** 0%

#### 작업 내용
- [ ] pytest 설정
- [ ] API 테스트 작성
- [ ] 통합 테스트 작성
- [ ] CI/CD 통합

---

## 📅 주간 일정 (2025-11-25 ~ 2025-11-29)

### 월요일 (2025-11-25) ✅
- [ ] My-Ktube.ai 도메인 이전 시작
- [ ] Frontend-Backend API 스펙 회의
- [ ] AI Team CAT 설계 회의

### 화요일 (2025-11-26)
- [ ] Admin Dashboard TanStack Query 설정
- [ ] R Plumber POC 작성
- [ ] My-Ktube.ai DNS 전파 확인

### 수요일 (2025-11-27)
- [ ] CAT 알고리즘 Python 구현 시작
- [ ] 로그인 에러 핸들링 구현

### 목요일 (2025-11-28)
- [ ] Admin Dashboard 로그인 연동 완료
- [ ] CAT 설계 문서 리뷰 준비

### 금요일 (2025-11-29)
- [ ] CAT 설계 리뷰 미팅
- [ ] 주간 진행 상황 업데이트
- [ ] 다음 주 우선순위 조정

---

## 🎯 2주 목표 (2025-11-25 ~ 2025-12-08)

### Phase 0 완료 (100%)
- [x] 8개 도메인 이전 완료
- [ ] My-Ktube.ai 도메인 이전
- [ ] DB Schema 11개 테이블 생성
- [ ] Reverse Proxy 구성

### Phase 0.5 진행 (40% → 60%)
- [ ] CAT/IRT 엔진 설계 완료
- [ ] Python 기본 구현
- [ ] 시드 데이터 스크립트 작성

### Phase 1 진행 (60% → 75%)
- [ ] Admin Dashboard 로그인 완료
- [ ] 홈 대시보드 개발
- [ ] 문제 관리 UI 시작

---

## 📊 팀별 우선순위

### AI Team
1. 🔥 CAT/IRT 엔진 설계 (Critical)
2. ⚠️ R Plumber POC (High)
3. 📋 Python 구현 계획 (Medium)

### Backend Team
1. ⚠️ DB Schema 완성 (High)
2. ⚠️ API 문서 개선 (High)
3. 📋 시드 데이터 협업 (Medium)

### Frontend Team
1. 🔥 Admin Dashboard 로그인 API 연동 (Critical)
2. ⚠️ 홈 대시보드 개발 (High)
3. 📋 문제 관리 UI (Medium)

### DevOps Team
1. 🔥 My-Ktube.ai 도메인 이전 (Critical)
2. 📋 Reverse Proxy 구성 (Medium)
3. 📋 테스트 환경 안정화 (Medium)

### QA Team
1. ⚠️ 시드 데이터 생성 (High)
2. 📋 E2E 테스트 자동화 (Medium)

---

## 🚦 블로커 현황

### Active Blockers (진행 중단)
- 없음

### At Risk (위험)
1. **CAT/IRT 엔진 설계 지연**
   - 현재 20% → 목표 100%
   - 리스크: Phase 0.5 전체 일정 지연
   - 완화: AI Team 집중 투입

2. **Frontend 개발 리소스 부족**
   - 현재 1명 → 필요 2명
   - 리스크: Phase 1 프론트엔드 지연
   - 완화: 외부 계약직 고려

### Monitoring (모니터링 중)
3. **API 문서 불완전**
   - 영향: Frontend 개발 속도 저하
   - 완화: 주간 sync 미팅

---

## 📈 진행률 추이

### 지난 주 (2025-11-18 ~ 2025-11-22)
```
Phase 0:   85% → 90% (+5%)  ✅
Phase 0.5: 35% → 40% (+5%)  🔄
Phase 1:   55% → 60% (+5%)  🔄
```

### 이번 주 목표 (2025-11-25 ~ 2025-11-29)
```
Phase 0:   90% → 95% (+5%)
Phase 0.5: 40% → 50% (+10%)
Phase 1:   60% → 70% (+10%)
```

### 2주 목표 (2025-11-25 ~ 2025-12-08)
```
Phase 0:   90% → 100% (+10%)  🎯 완료
Phase 0.5: 40% → 60%  (+20%)
Phase 1:   60% → 75%  (+15%)
```

---

## 🔔 다음 주요 마일스톤

1. **Phase 0 완료** - 2025-12-08
2. **Phase 0.5 CAT/IRT 엔진 설계 완료** - 2025-11-29
3. **Phase 1 Admin Dashboard 로그인 완료** - 2025-11-29
4. **Phase 1 홈 대시보드 완료** - 2025-12-08

---

## 📞 연락처 및 회의

### 주간 회의
- **월요일 10:00** - All Hands (전체 팀)
- **화요일 14:00** - AI Team Sync
- **수요일 10:00** - Frontend-Backend Sync
- **목요일 15:00** - DevOps Standup
- **금요일 16:00** - 주간 리뷰 (전체 팀)

### 담당자
- **AI Team Lead**: [AI팀장]
- **Backend Lead**: [백엔드팀장]
- **Frontend Lead**: [프론트팀장]
- **DevOps Lead**: [데브옵스팀장]
- **QA Lead**: [QA팀장]

---

**다음 업데이트:** 2025-11-29 (금요일 16:00)  
**작성자:** Project Manager
