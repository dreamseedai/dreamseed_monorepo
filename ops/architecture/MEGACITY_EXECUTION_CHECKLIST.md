# 🚀 DreamSeedAI MegaCity – Phase 0 → Phase 4 Execution Checklist

## Infrastructure · AI · DevOps · Backend · Frontend · Zone Activation · Governance 총괄 실행 로드맵

**버전:** 1.0  
**작성일:** 2025-11-22  
**작성자:** DreamSeedAI Architecture · DevOps · Product Team

---

# 📌 0. 개요 (Overview)

이 문서는 DreamSeedAI MegaCity의 **Phase 0 (Foundation) → Phase 4 (Global Scale)** 까지의 전체 실행 로드맵을 **체크리스트 형식**으로 정리한 **실전 To-Do 문서**입니다.

## 문서 목적

- Phase별 핵심 실행 항목 명확화
- DevOps, AI, Backend, Frontend, Governance 팀 간 실행 동기화
- 매일/매주/매월 운영 체크리스트 제공
- 9개 Zone 활성화 순서 및 조건 정의
- AI/정책/보안 실행 우선순위 명시

## Phase 타임라인

```
Phase 0 (Foundation)         2024 Q4 - 2025 Q1  [90% 완료]
Phase 1 (Core MVP)           2025 Q1 - 2025 Q2  [▶️ 지금 시작]
Phase 2 (Zone Expansion)     2025 Q3 - 2025 Q4
Phase 3 (Global Scale)       2026 Q1 - 2026 Q4
Phase 4 (AI Hyper-Scale)     2027+
```

---

# 📋 1. Phase별 전체 실행 체크리스트

## Phase 0 — Core Foundation (완료 90%)

### Infrastructure

- [x] ~~Domain 구매 (9개 도메인)~~
- [ ] **Cloudflare 도메인 이전** (8/9 완료, My-Ktube.ai 남음)
  - [x] UnivPrepAI.com
  - [x] CollegePrepAI.com
  - [x] SkillPrepAI.com
  - [x] MediPrepAI.com
  - [x] MediaPrepAI.com
  - [x] MajorPrepAI.com
  - [x] mpcstudy.com
  - [x] My-Ktube.com
  - [ ] My-Ktube.ai
- [ ] **Reverse Proxy 초기 구성**
  - [ ] Nginx 설치 및 설정
  - [ ] Upstream 서버 설정 (Backend, AI Router)
  - [ ] Health Check 설정
  - [ ] SSL/TLS 인증서 자동 갱신 (Let's Encrypt)
- [x] ~~Core FastAPI 구조 확정~~
- [ ] **DB Schema 생성**
  - [ ] users, organizations, zones 테이블
  - [ ] exams, exam_attempts, questions 테이블
  - [ ] ai_requests, audit_log 테이블
  - [ ] RLS 정책 적용 (zone_id, org_id)
- [ ] **Redis 설치 및 Rate Limit 적용**
  - [ ] Redis 설치
  - [ ] Rate Limit 규칙 (10 req/s per user)
  - [ ] Session 저장소 설정
- [ ] **Monitoring Stack 구축**
  - [ ] Prometheus 설치 및 Exporter 설정
  - [ ] Grafana 설치 및 Dashboard 구성 (7개)
  - [ ] Loki 설치 (로그 집계)
  - [ ] AlertManager 설정 (Slack 연동)
- [ ] **Backup/DR 스크립트 설치**
  - [ ] PostgreSQL Daily Backup (pg_dump)
  - [ ] WAL Archive 설정
  - [ ] Redis RDB/AOF Backup
  - [ ] Cloudflare R2 → Backblaze B2 복제
  - [ ] DR 문서 작성 (RTO 4시간, RPO 1시간)

---

## Phase 1 — Core MVP (2025 Q1-Q2) [▶️ 지금 시작]

### Backend (FastAPI)

- [ ] **User Management API**
  - [ ] POST /api/v1/auth/register (회원가입)
  - [ ] POST /api/v1/auth/login (로그인)
  - [ ] POST /api/v1/auth/refresh (토큰 갱신)
  - [ ] GET /api/v1/users/me (내 정보 조회)
  - [ ] PUT /api/v1/users/me (정보 수정)
- [ ] **Organization & Zone API**
  - [ ] POST /api/v1/organizations (조직 생성)
  - [ ] GET /api/v1/organizations/{org_id} (조직 조회)
  - [ ] POST /api/v1/organizations/{org_id}/members (멤버 추가)
- [ ] **Exam Management API**
  - [ ] POST /api/v1/exams (시험 생성)
  - [ ] GET /api/v1/exams/{exam_id} (시험 조회)
  - [ ] POST /api/v1/exams/{exam_id}/attempts (시험 시도)
  - [ ] POST /api/v1/exams/{exam_id}/submit (답안 제출)
  - [ ] GET /api/v1/exams/{exam_id}/results (결과 조회)
- [ ] **CAT Engine v1**
  - [ ] IRT 파라미터 추정 (문항 난이도 θ)
  - [ ] Adaptive Question Selection
  - [ ] 실시간 능력치 업데이트
  - [ ] 종료 조건 (SE < 0.3 or N > 50)
- [ ] **AI Tutor v1 연결**
  - [ ] POST /api/v1/ai-tutor (질문 전송)
  - [ ] AI Router → vLLM 연동
  - [ ] Prompt Safety Layer (Injection 방지)
  - [ ] Response Safety Filter (유해 출력 차단)
- [ ] **Dashboard API**
  - [ ] GET /api/v1/dashboard/teacher (교사 대시보드)
  - [ ] GET /api/v1/dashboard/parent (학부모 대시보드)
  - [ ] GET /api/v1/dashboard/student (학생 대시보드)
  - [ ] Analytics API (학습 진도, 성적 분석)

### Frontend (Next.js)

- [ ] **Next.js 프로젝트 구조 확정**
  - [ ] `/apps/portal_front` (Core Portal)
  - [ ] `/apps/admin_front` (Admin Dashboard)
  - [ ] Zone별 독립 프론트엔드 구조 결정
- [ ] **Teacher Dashboard UI**
  - [ ] 로그인/회원가입 페이지
  - [ ] 반(Class) 관리 페이지
  - [ ] 시험 출제 페이지
  - [ ] 학생 성적 조회 페이지
  - [ ] 실시간 시험 모니터링 페이지
- [ ] **Parent Dashboard UI**
  - [ ] 로그인/회원가입 페이지
  - [ ] 자녀 연결 요청 페이지
  - [ ] 자녀 성적 조회 페이지
  - [ ] 학습 진도 시각화
- [ ] **Student Dashboard UI**
  - [ ] 로그인/회원가입 페이지
  - [ ] 시험 응시 페이지
  - [ ] AI Tutor 채팅 페이지
  - [ ] 내 성적/진도 페이지
- [ ] **Design System 구축**
  - [ ] Figma 디자인 시스템
  - [ ] Tailwind CSS 설정
  - [ ] Component Library (Button, Input, Card 등)

### AI Infrastructure

- [ ] **vLLM Server 설치 및 설정**
  - [ ] GPU 서버 구성 (RTX 5090 or A100)
  - [ ] vLLM 설치 (pip install vllm)
  - [ ] Qwen2.5-7B 모델 다운로드 및 로딩
  - [ ] vLLM API 서버 실행 (포트 8100)
  - [ ] Health Check API 구현
  - [ ] Prometheus Exporter 설정
- [ ] **Whisper Server 설치 및 설정**
  - [ ] Whisper Large-v3 모델 다운로드
  - [ ] Whisper API 서버 실행 (포트 8101)
  - [ ] Audio 파일 업로드 API
  - [ ] STT Latency 최적화 (목표 <1.5s)
- [ ] **AI Router 구현**
  - [ ] FastAPI AI Router 서버 (포트 8200)
  - [ ] vLLM/Whisper/PoseNet 라우팅 로직
  - [ ] Model Selection 로직 (7B/32B/70B)
  - [ ] Request Queue 관리 (Redis)

### DevOps & CI/CD

- [ ] **GitHub Actions CI/CD 파이프라인**
  - [ ] `.github/workflows/backend-ci.yml` (Backend 테스트/빌드)
  - [ ] `.github/workflows/frontend-ci.yml` (Frontend 테스트/빌드)
  - [ ] `.github/workflows/deploy-stage.yml` (Stage 배포)
  - [ ] `.github/workflows/deploy-prod.yml` (Prod 배포)
- [ ] **Canary Deployment 설정**
  - [ ] Nginx Canary 라우팅 (5% → 25% → 50% → 100%)
  - [ ] Prometheus 메트릭 모니터링
  - [ ] Auto-rollback 스크립트
- [ ] **Error Alerting**
  - [ ] Prometheus AlertManager 규칙
  - [ ] Slack Webhook 연동
  - [ ] P1-P4 Incident 분류
  - [ ] On-call Rotation 설정

### Security & Governance

- [ ] **RBAC/PBAC 정책 적용**
  - [ ] 7개 역할 정의 (student, parent, teacher, tutor, org_admin, zone_admin, sys_admin)
  - [ ] PostgreSQL RLS 정책 적용
  - [ ] Policy Engine 구현
- [ ] **Cloudflare WAF 규칙 적용**
  - [ ] OWASP Top-10 규칙 활성화
  - [ ] SQL Injection 차단
  - [ ] XSS 차단
  - [ ] Bot Management (Score < 30 차단)
- [ ] **AI Safety Layer**
  - [ ] Prompt Injection 키워드 필터
  - [ ] Harmful Output Detection (욕설/폭력/혐오)
  - [ ] Bias Detection
- [ ] **GDPR/PIPA 동의 페이지 생성**
  - [ ] Privacy Policy 페이지
  - [ ] Terms of Service 페이지
  - [ ] Consent Checkbox 구현
  - [ ] Consent Log 저장
- [ ] **Audit Log API**
  - [ ] POST /api/v1/audit-log (로그 기록)
  - [ ] GET /api/v1/audit-log (로그 조회, Admin만)

---

## Phase 2 — MegaCity Zone Expansion (2025 Q3-Q4)

### Zone Activation

- [ ] **SkillPrepAI.com 활성화**
  - [ ] Zone 설정 (zone_id: skillprep)
  - [ ] Frontend 배포
  - [ ] Backend API 연결
  - [ ] CBT 모드 활성화
  - [ ] 자격증 시험 콘텐츠 등록
- [ ] **CollegePrepAI.com 활성화**
  - [ ] Zone 설정 (zone_id: collegeprep)
  - [ ] Frontend 배포
  - [ ] 편입 시험 콘텐츠 등록
- [ ] **K-Zone Lite (Voice Tutor)**
  - [ ] My-Ktube.com Frontend 배포
  - [ ] Whisper 기반 발음 교정 기능
  - [ ] K-POP 학습 콘텐츠 등록
  - [ ] 한글 학습 콘텐츠 등록

### Backend Enhancements

- [ ] **Exam Analytics v2**
  - [ ] GET /api/v1/analytics/exam/{exam_id} (시험별 분석)
  - [ ] GET /api/v1/analytics/student/{student_id} (학생별 분석)
  - [ ] 학습 패턴 분석 (강점/약점)
  - [ ] 추천 학습 경로
- [ ] **CBT Mode 구현**
  - [ ] 시간 제한 (Timer)
  - [ ] 순차 문제 출제 (이전 문제 돌아가기 금지)
  - [ ] 자동 제출 (시간 초과 시)
  - [ ] 실시간 성적 집계

### AI Enhancements

- [ ] **PoseNet Pipeline 구현**
  - [ ] PoseNet 모델 설치 (TensorFlow.js 또는 MediaPipe)
  - [ ] Video 업로드 API
  - [ ] Pose Keypoints 추출 (33 landmarks)
  - [ ] Motion Comparison (DTW 알고리즘)
  - [ ] Dance Scoring API
- [ ] **Whisper Large Model 최적화**
  - [ ] FP16/INT8 Quantization
  - [ ] Batch Processing
  - [ ] STT Latency 목표 <1.2s
- [ ] **vLLM 32B 모델 추가**
  - [ ] Qwen2.5-32B 모델 다운로드
  - [ ] Model Routing 로직 (7B → 32B → 70B)
  - [ ] GPU Memory 최적화 (TP=2)

### DevOps

- [ ] **Multi-region Routing 준비**
  - [ ] Cloudflare Load Balancing 설정
  - [ ] Health Check 엔드포인트
  - [ ] Failover 정책
- [ ] **Canary Monitoring Dashboard**
  - [ ] Grafana Canary Dashboard 생성
  - [ ] Error Rate / Latency / Traffic 시각화

---

## Phase 3 — Global MegaCity (2026 Q1-Q4)

### K-Zone Full Activation

- [ ] **Dance Lab (PoseNet Full)**
  - [ ] 3D Pose Tracking (MediaPipe Pose + Depth)
  - [ ] Multi-user Comparison
  - [ ] Leaderboard 시스템
  - [ ] Social Sharing 기능
- [ ] **Drama Coach**
  - [ ] 대본 분석 AI (Emotion/Tone)
  - [ ] 연기 피드백 시스템
  - [ ] Voice Emotion Detection
- [ ] **Creator Studio**
  - [ ] Stable Diffusion 이미지 생성
  - [ ] TTS (Text-to-Speech) 음성 합성
  - [ ] Video Editing Pipeline
  - [ ] 동의 기반 얼굴/음성 합성 (Opt-in)
  - [ ] AI 생성물 워터마크

### AI Enhancements

- [ ] **Multi-modal Tutor**
  - [ ] Text + Image + Audio 통합 입력
  - [ ] Vision-Language Model (LLaVA, Qwen-VL)
  - [ ] Audio-to-Text-to-Response Pipeline
- [ ] **vLLM 70B 모델 추가**
  - [ ] Qwen2.5-70B 모델 (Premium 기능)
  - [ ] TP=4 (Tensor Parallelism)
  - [ ] GPU Memory 최적화
- [ ] **Study Path Planner AI**
  - [ ] 학습 경로 추천 AI
  - [ ] Weak Point 분석
  - [ ] Adaptive Study Plan 생성

### Operations

- [ ] **Multi-region Deployment**
  - [ ] Seoul (Primary)
  - [ ] Tokyo (Secondary)
  - [ ] US-East (Tertiary)
  - [ ] Cloudflare Geo-routing
- [ ] **Zone 운영 대시보드**
  - [ ] Zone별 사용자 수 / 트래픽 / 성적 모니터링
  - [ ] Zone Admin 전용 대시보드
  - [ ] Zone별 수익 분석

### Governance

- [ ] **EU GDPR 준수 강화**
  - [ ] EU 사용자 → EU 저장소 (GDPR Article 44)
  - [ ] SCC (Standard Contractual Clauses) 체결
  - [ ] DPIA 수행 (PoseNet, Whisper, Diffusion)
- [ ] **AI Fairness Audit**
  - [ ] Bias Detection 자동화
  - [ ] 교육 데이터 공정성 검증
  - [ ] Quarterly AI Ethics Review

---

## Phase 4 — AI Hyper-Scale (2027+)

### AI Infrastructure

- [ ] **100+ GPU Cluster**
  - [ ] Kubernetes GPU Scheduling
  - [ ] Multi-GPU Training Pipeline
  - [ ] Model Serving Optimization (vLLM TP=8)
- [ ] **Custom LLM Fine-tuning**
  - [ ] 교육 도메인 특화 LLM
  - [ ] 한국어 교육 데이터 Fine-tuning
  - [ ] LoRA/QLoRA 최적화
- [ ] **Edge AI Deployment**
  - [ ] Mobile AI (TensorFlow Lite)
  - [ ] On-device Inference

### Platform

- [ ] **MegaCity Marketplace**
  - [ ] Third-party 콘텐츠 마켓플레이스
  - [ ] API Marketplace (Exam Engine, AI Tutor API)
- [ ] **Global Expansion**
  - [ ] 일본 시장 진출 (My-Ktube.jp)
  - [ ] 동남아 시장 진출 (베트남, 태국)
  - [ ] 영어권 시장 진출 (미국, 캐나다)

---

# 📅 2. 매일/매주/매월 운영 체크리스트 (Daily/Weekly/Monthly Operations)

## 매일 (Daily) — SRE/DevOps

```
시간: 매일 오전 9:00 (30분)

□ Grafana Dashboard 확인 (7개)
  □ API Health Dashboard (req/s, error rate, latency)
  □ AI Cluster Dashboard (GPU util, temp, memory)
  □ Database Dashboard (connections, slow queries)
  □ Redis Dashboard (memory, hit rate)
  □ Network Dashboard (bandwidth, latency)
  □ System Dashboard (CPU, RAM, Disk)
  □ Business Dashboard (사용자 수, 시험 시도 수)

□ Error Rate 확인
  □ 5xx Error < 0.5%
  □ 4xx Error < 5%
  □ Slow Query (> 5s) = 0

□ AI GPU Load 확인
  □ GPU Utilization 70-90%
  □ GPU Temperature < 85°C
  □ GPU Memory < 95%

□ DB Connection Pool 상태 체크
  □ Active Connections < 80%
  □ Idle Connections > 20%
  □ Connection Wait Time < 100ms

□ Slack #alerts 채널 확인
  □ P1-P4 Incident 처리 현황
```

## 매주 (Weekly) — Security + DevOps

```
시간: 매주 월요일 오전 10:00 (1시간)

□ 정책 업데이트 검토
  □ RBAC/PBAC 정책 변경 사항
  □ 신규 정책 승인 (Policy Approval Queue)

□ Zone별 Uptime 체크
  □ UnivPrepAI.com Uptime > 99.9%
  □ SkillPrepAI.com Uptime > 99.9%
  □ My-Ktube.com Uptime > 99.9%
  □ (기타 Zone 동일)

□ Security Review
  □ WAF 차단 로그 확인 (SQL Injection, XSS 시도)
  □ Login 실패 급증 패턴 확인 (>100회/hr)
  □ 비정상 API 호출 패턴 확인

□ K-Zone 유해 출력 검토
  □ AI 생성 콘텐츠 Safety Log 검토 (90일 보존)
  □ 사용자 신고 사건 처리 (24시간 SLA)

□ Backup 검증
  □ PostgreSQL Backup 성공 확인
  □ WAL Archive 정상 여부
  □ Redis RDB/AOF Backup 확인
```

## 매월 (Monthly) — Governance + Compliance

```
시간: 매월 첫째 주 금요일 오후 2:00 (2시간)

□ Admin Role 재검증
  □ sys_admin 역할 재승인 (CTO 승인)
  □ zone_admin 역할 재승인
  □ 퇴사자 계정 비활성화

□ DB 백업 검증
  □ 백업 복원 테스트 (Staging 환경)
  □ PITR (Point-in-Time Recovery) 테스트

□ Audit Log 검토
  □ 민감 데이터 접근 로그 확인
  □ Admin 권한 사용 로그 확인
  □ 비정상 행동 패턴 분석

□ 비용 대시보드 확인
  □ GPU 비용 (목표: $4,000/월)
  □ Storage 비용 (목표: $100/월)
  □ Network 비용 (목표: $200/월)
  □ 총 비용 (목표: $4,500/월 이하)

□ GDPR/PIPA 준수 체크
  □ 삭제 요청 처리 현황 (30일 이내)
  □ PII 보존 기간 준수 (3년)
  □ 제3자 제공 기록 (5년 보존)

□ AI Safety Review
  □ Prompt Injection 시도 횟수
  □ Harmful Output 차단 횟수
  □ Bias Detection 결과
```

---

# 🗺️ 3. Zone Activation Checklist (9개 Zone 활성화 순서)

## Education Zones (교육 구역)

### 1. UnivPrepAI.com — Phase 1 (2025 Q1-Q2) ✅ 최우선

**Target**: 고등학생 (대학 입시)  
**핵심 기능**: 수능 모의고사, AI Tutor, CAT Engine

```
□ Phase 1 Prerequisites
  □ Core Platform 완성 (Backend + Frontend + AI)
  □ CAT Engine v1 완성
  □ AI Tutor v1 연결
  □ Teacher/Parent Dashboard 완성

□ Zone Setup
  □ zone_id: univprep
  □ Domain: UnivPrepAI.com
  □ Cloudflare DNS 설정
  □ SSL/TLS 인증서

□ Content
  □ 수능 기출문제 500개 등록
  □ 모의고사 10회분 등록
  □ AI Tutor Prompt 최적화 (수능 특화)

□ Marketing
  □ 랜딩 페이지 제작
  □ SEO 최적화 (키워드: 수능, 모의고사, AI 과외)
  □ 유튜브 채널 개설

□ Launch Criteria
  □ 베타 테스터 50명 모집
  □ 30일 안정성 테스트
  □ Error Rate < 0.5%
  □ Public Launch
```

### 2. SkillPrepAI.com — Phase 2 (2025 Q3)

**Target**: 성인 학습자 (자격증, 직업 교육)  
**핵심 기능**: CBT 모드, 자격증 시험 Practice

```
□ Phase 2 Prerequisites
  □ UnivPrepAI 3개월 안정 운영
  □ CBT Mode 개발 완료
  □ 자격증 시험 콘텐츠 확보 (100+ 자격증)

□ Zone Setup
  □ zone_id: skillprep
  □ Domain: SkillPrepAI.com
  □ CBT 시간 제한 기능
  □ 순차 출제 모드

□ Content
  □ 정보처리기사 기출 500문제
  □ 컴활/워드 기출 300문제
  □ 토익/토스 Practice 200문제

□ Launch Criteria
  □ 베타 테스터 100명
  □ CBT 안정성 검증
  □ Public Launch
```

### 3. CollegePrepAI.com — Phase 2 (2025 Q4)

**Target**: 전문대/편입 준비생  
**핵심 기능**: 편입 시험, 전문대 입시

```
□ Zone Setup
  □ zone_id: collegeprep
  □ Domain: CollegePrepAI.com

□ Content
  □ 편입 수학 기출 300문제
  □ 편입 영어 기출 300문제
  □ 전문대 모의고사 10회분

□ Launch Criteria
  □ 베타 테스터 50명
  □ 30일 안정 운영
  □ Public Launch
```

### 4. MediPrepAI.com — Phase 3 (2026 Q2)

**Target**: 간호/보건/의료 계열  
**핵심 기능**: 간호사 국가고시, 의료 자격증

```
□ Zone Setup
  □ zone_id: mediprep
  □ Domain: MediPrepAI.com

□ Content
  □ 간호사 국가고시 기출 1000문제
  □ 의료 전문 용어 학습
  □ 시뮬레이션 시험

□ Launch Criteria
  □ 의료 전문가 콘텐츠 검증
  □ Public Launch
```

### 5. MajorPrepAI.com — Phase 3 (2026 Q4)

**Target**: 전공/대학원 준비  
**핵심 기능**: 전공 시험, GRE/GMAT

```
□ Zone Setup
  □ zone_id: majorprep
  □ Domain: MajorPrepAI.com

□ Content
  □ 전공별 기출문제 (경영/경제/공학)
  □ GRE/GMAT Practice
  □ 대학원 입시 자료

□ Launch Criteria
  □ Public Launch
```

### 6. mpcstudy.com — Phase 1 (유지/데이터 연동)

**Target**: 모든 학습자 (공공 서비스)  
**핵심 기능**: 무료 학습 자료

```
□ Integration
  □ 기존 mpcstudy.com 데이터 마이그레이션
  □ Core Platform 연동
  □ 무료 콘텐츠 공개

□ Maintenance
  □ 기존 사용자 이전
  □ SEO 유지
```

### 7. MediaPrepAI.com — Phase 3 (2026 Q3)

**Target**: 크리에이터, 마케터  
**핵심 기능**: 콘텐츠 제작, SEO, 소셜 미디어 전략

```
□ Zone Setup
  □ zone_id: mediaprep
  □ Domain: MediaPrepAI.com

□ Content
  □ SEO 학습 자료
  □ 유튜브 크리에이터 가이드
  □ 소셜 미디어 마케팅

□ Launch Criteria
  □ Public Launch
```

## K-Zone (K-Culture AI Special District)

### 8. My-Ktube.com — Phase 2 (2025 Q4)

**Target**: 글로벌 K-Culture 팬  
**핵심 기능**: K-POP 학습, 한글 학습, Voice Tutor

```
□ Phase 2 Prerequisites
  □ Whisper Large-v3 최적화 완료 (STT < 1.2s)
  □ K-POP 콘텐츠 라이선스 확보
  □ 한글 학습 콘텐츠 제작

□ Zone Setup
  □ zone_id: kzone
  □ Domain: My-Ktube.com
  □ Multilingual Support (EN, JP, ZH, KO)

□ Content
  □ K-POP 노래 100곡 (가사 + 발음 가이드)
  □ 한글 학습 코스 (초급/중급/고급)
  □ K-Drama 대본 분석 10편

□ AI Features
  □ Voice Tutor (Whisper 기반 발음 교정)
  □ Real-time Feedback (정확도 % 표시)
  □ Progress Tracking

□ Launch Criteria
  □ 베타 테스터 200명 (글로벌)
  □ 30일 안정 운영
  □ Public Launch
```

### 9. My-Ktube.ai — Phase 3-4 (2026 Q4 - 2027 Q2)

**Target**: K-Culture 크리에이터  
**핵심 기능**: Dance Lab, Drama Coach, Creator Studio

```
□ Phase 3 Prerequisites
  □ PoseNet 3D Tracking 완성
  □ Stable Diffusion 통합
  □ TTS (Text-to-Speech) 구현
  □ 동의 기반 얼굴/음성 합성 시스템 (Opt-in)

□ Zone Setup
  □ zone_id: kzone_ai
  □ Domain: My-Ktube.ai
  □ AI Safety Layer 강화

□ AI Features
  □ Dance Lab (PoseNet)
    □ 3D Pose Tracking
    □ Motion Comparison (DTW)
    □ Dance Scoring
    □ Leaderboard
  
  □ Drama Coach
    □ 대본 분석 (Emotion/Tone)
    □ 연기 피드백
    □ Voice Emotion Detection
  
  □ Creator Studio
    □ 이미지 생성 (Stable Diffusion)
    □ 음성 합성 (TTS)
    □ Video Editing Pipeline
    □ 동의 기반 Deepfake (Opt-in)
    □ AI 생성물 워터마크

□ Safety & Governance
  □ GDPR/PIPA DPIA 수행
  □ 동의 시스템 구축 (Voice Consent API)
  □ 30일 자동 삭제 정책
  □ 유해 콘텐츠 필터링

□ Launch Criteria
  □ 베타 테스터 500명 (글로벌)
  □ 60일 안정 운영
  □ K-Culture 파트너십 확보 (엔터사)
  □ Public Launch
```

---

# 🤖 4. AI Infrastructure Execution Checklist

## LLM (Large Language Models)

### vLLM 7B (Phase 1) ✅ 최우선

```
□ Installation
  □ GPU 서버 준비 (RTX 5090 24GB 또는 A100 40GB)
  □ CUDA 12.1+ 설치
  □ pip install vllm
  □ Qwen2.5-7B 모델 다운로드 (Hugging Face)

□ Configuration
  □ vLLM API 서버 실행 (포트 8100)
  □ Tensor Parallelism (TP=1, 단일 GPU)
  □ KV Cache 튜닝 (--max-model-len 4096)
  □ Quantization (FP16, 옵션: INT8)

□ Optimization
  □ Inference Latency < 2.0s (per request)
  □ Throughput > 10 req/s
  □ GPU Utilization 70-90%

□ Monitoring
  □ Prometheus Exporter 설치
  □ Grafana Dashboard 생성
  □ Alerts: GPU Temp > 85°C, Latency > 3s
```

### vLLM 32B (Phase 2)

```
□ Prerequisites
  □ 2x GPU (A100 40GB or RTX 5090 24GB)
  □ vLLM 7B 안정 운영 3개월

□ Installation
  □ Qwen2.5-32B 모델 다운로드
  □ TP=2 (Tensor Parallelism)

□ Model Routing
  □ AI Router 구현 (FastAPI)
  □ Model Selection Logic:
    - 간단한 질문 (토큰 < 100) → 7B
    - 중간 복잡도 (토큰 100-500) → 32B
    - 복잡한 질문 (토큰 > 500) → 70B (Phase 3)

□ Optimization
  □ Inference Latency < 3.0s
  □ Throughput > 5 req/s
```

### vLLM 70B (Phase 3)

```
□ Prerequisites
  □ 4x GPU (A100 80GB)
  □ 32B 모델 안정 운영 6개월

□ Installation
  □ Qwen2.5-70B 모델 (Premium 기능)
  □ TP=4 (Tensor Parallelism)

□ Usage
  □ Premium 사용자만 접근
  □ 복잡한 교육 상담, 심화 분석

□ Optimization
  □ Inference Latency < 5.0s
  □ GPU Memory < 95%
```

### KV Cache Tuning (Phase 1-2)

```
□ vLLM KV Cache 설정
  □ --max-model-len 4096 (기본)
  □ --max-num-seqs 32 (동시 처리 요청 수)

□ Cache Hit Rate Monitoring
  □ 목표: Cache Hit Rate > 60%
  □ Latency 감소: 30-50%

□ Optimization
  □ Prefix Caching 활성화 (System Prompt 재사용)
  □ Cache Eviction Policy (LRU)
```

## Whisper (Speech-to-Text)

### Whisper Large-v3 (Phase 1) ✅

```
□ Installation
  □ pip install openai-whisper
  □ Whisper Large-v3 모델 다운로드
  □ GPU 서버 준비 (RTX 3090 24GB or A100)

□ API Server
  □ FastAPI Whisper Server (포트 8101)
  □ Audio Upload API (/api/v1/whisper/transcribe)
  □ Supported Formats: MP3, WAV, M4A

□ Optimization
  □ STT Latency < 1.5s (목표: 1.2s)
  □ Batch Processing (최대 10개 동시)
  □ FP16 Quantization

□ Features
  □ Language Detection (Auto)
  □ Korean/English Support
  □ Timestamp 추출

□ Monitoring
  □ Prometheus Exporter
  □ Latency p95 < 2.0s
  □ GPU Utilization 60-80%
```

### Whisper Optimization (Phase 2)

```
□ FP16/INT8 Quantization
  □ FP16 (99.5% accuracy, 50% memory)
  □ INT8 (98% accuracy, 75% memory reduction)

□ Batch Processing
  □ 동시 10개 요청 처리
  □ Queue 관리 (Redis)

□ STT Latency Goal
  □ < 1.2s (Phase 2 목표)
  □ < 1.0s (Phase 3 목표)
```

## PoseNet (Pose Estimation)

### PoseNet 2D (Phase 2) ✅

```
□ Installation
  □ TensorFlow.js PoseNet or MediaPipe Pose
  □ pip install mediapipe

□ API Server
  □ FastAPI PoseNet Server (포트 8102)
  □ Video Upload API (/api/v1/posenet/analyze)

□ Features
  □ 33 Pose Keypoints 추출
  □ Confidence Score 계산
  □ Motion Tracking (Frame-by-frame)

□ Dance Scoring
  □ Motion Comparison (DTW 알고리즘)
  □ Scoring: 0-100% 정확도
  □ Feedback: 어떤 동작이 틀렸는지

□ Optimization
  □ Processing Time < 5s (30s video)
  □ GPU Utilization 50-70%
```

### PoseNet 3D (Phase 3)

```
□ Installation
  □ MediaPipe Pose + Depth Estimation
  □ 3D Pose Reconstruction

□ Features
  □ 3D Pose Tracking
  □ Multi-user Comparison
  □ Spatial Accuracy

□ Optimization
  □ Processing Time < 10s (1min video)
```

## Stable Diffusion (Image Generation)

### Stable Diffusion v2.1 (Phase 3)

```
□ Installation
  □ pip install diffusers transformers
  □ Stable Diffusion v2.1 모델 다운로드
  □ GPU 서버 준비 (A100 40GB)

□ API Server
  □ FastAPI Diffusion Server (포트 8103)
  □ Text-to-Image API (/api/v1/diffusion/generate)

□ Features
  □ K-POP 아티스트 스타일 이미지 생성
  □ 학습 자료 일러스트 생성
  □ Creative Studio 기능

□ Safety
  □ NSFW Filter (Safety Checker)
  □ 동의 기반 얼굴 합성 (Opt-in)
  □ AI 생성물 워터마크

□ Optimization
  □ Generation Time < 10s (512x512)
  □ GPU Utilization 60-80%
```

## Creator Studio (Multi-modal Pipeline)

### Video Editing Pipeline (Phase 4)

```
□ Features
  □ TTS (Text-to-Speech) 음성 합성
  □ Lip-sync (입 모양 동기화)
  □ Background Music 합성
  □ Video Export (MP4, 1080p)

□ Tools
  □ FFmpeg (Video Processing)
  □ Coqui TTS (음성 합성)
  □ Wav2Lip (Lip-sync)

□ Safety
  □ 동의 기반 얼굴/음성 사용 (Voice Consent API)
  □ 30일 자동 삭제 정책
  □ GDPR/PIPA DPIA 수행
```

---

# 🔐 5. 정책/보안 실행 체크리스트 (Security & Governance)

## RBAC/PBAC 정책 적용

### RBAC (Phase 0-1) ✅

```
□ 7개 역할 정의
  □ student (학생)
  □ parent (학부모)
  □ teacher (교사)
  □ tutor (튜터)
  □ org_admin (조직 관리자)
  □ zone_admin (Zone 관리자)
  □ sys_admin (시스템 관리자)

□ PostgreSQL RLS 정책 적용
  □ users 테이블: 본인 또는 Parent/Teacher 연결 시만 조회
  □ exams 테이블: Zone/Org 격리
  □ exam_attempts 테이블: 본인 + Parent + Teacher만 조회

□ API 권한 검증
  □ @require_role("teacher") 데코레이터 구현
  □ @require_zone_access() 데코레이터 구현
```

### PBAC (Phase 1) ✅

```
□ Policy Engine 구현
  □ FastAPI Policy Middleware
  □ Policy Rules (JSON 또는 Python Dict)

□ 주요 정책
  □ 시험 중 AI Tutor 차단
    IF (exam.active == True) AND (user.role == 'student')
    THEN deny(ai_tutor_access)
  
  □ 구독 미결제 시 Premium 기능 차단
    IF (user.subscription == None) OR (user.subscription.expired == True)
    THEN deny(premium_features)
  
  □ Zone 외부 접근 차단
    IF (request.zone_id != user.zone_id)
    THEN deny(access)
```

## Cloudflare WAF 규칙 적용

### OWASP Top-10 (Phase 0-1) ✅

```
□ WAF 규칙 활성화
  □ SQL Injection 차단
  □ XSS (Cross-Site Scripting) 차단
  □ CSRF (Cross-Site Request Forgery) 차단
  □ Path Traversal 차단
  □ Remote Code Execution 차단

□ Bot Management
  □ Bot Score < 30 → 차단
  □ Challenge (Captcha) 활성화
  □ Rate Limiting (100 req/min per IP)

□ DDoS Protection
  □ L3/L4 DDoS (자동 차단)
  □ L7 DDoS (Challenge + Rate Limit)

□ Monitoring
  □ Cloudflare Analytics 확인
  □ 차단된 요청 로그 검토 (주간)
```

## AI Safety Layer

### Prompt Injection 방지 (Phase 1) ✅

```
□ Keyword Filter
  □ "ignore previous instructions" 차단
  □ "system override" 차단
  □ "jailbreak" 차단
  □ "bypass filter" 차단

□ Pattern Detection
  □ Regex 기반 Injection 패턴 탐지
  □ 의심 패턴 발견 시 로그 기록 + 차단

□ Monitoring
  □ Prompt Injection 시도 횟수 (주간 리포트)
  □ Slack 알림 (10+ 시도/시간)
```

### Harmful Output Detection (Phase 1) ✅

```
□ Toxicity Detection
  □ unitary/toxic-bert 모델 사용
  □ Toxicity Score > 0.7 → 차단

□ 욕설/폭력/혐오 키워드
  □ 한국어/영어 욕설 리스트
  □ 폭력/자해 키워드
  □ 성적 표현 키워드

□ Response 재생성
  □ 유해 출력 감지 시 최대 3회 재시도
  □ 3회 실패 시 "적절한 답변을 생성할 수 없습니다" 응답

□ Monitoring
  □ Harmful Output 차단 횟수 (주간 리포트)
```

### Bias Detection (Phase 2)

```
□ Bias Detector 설치
  □ unbiased/bias-detection 모델
  □ Bias Score > 0.7 → 로그 기록

□ Fairness Audit
  □ 교육 콘텐츠 편향 검사 (분기별)
  □ 성별/인종/지역 기반 편향 탐지

□ Mitigation
  □ 편향된 출력 재생성
  □ Prompt 수정
```

## GDPR/PIPA 동의 페이지 생성

### Privacy Policy (Phase 1) ✅

```
□ 페이지 생성
  □ /privacy-policy (한국어/영어)
  □ GDPR Article 13-14 준수 (수집 항목, 목적, 보존 기간 명시)
  □ PIPA 준수 (개인정보 처리방침 공개)

□ 내용
  □ 수집 정보: 이메일, 이름, 역할, 학습 기록
  □ 수집 목적: 서비스 제공, AI 개선, 통계 분석
  □ 보존 기간: PII 3년, 로그 1년, AI 업로드 7-30일
  □ 제3자 제공: Cloudflare (CDN), AWS (Cloud Storage)
  □ 사용자 권리: Access, Erasure, Portability, Restriction

□ 동의 Checkbox
  □ "개인정보 처리방침에 동의합니다" (필수)
  □ "데이터 처리에 동의합니다 (GDPR Article 6)" (필수)
```

### Terms of Service (Phase 1) ✅

```
□ 페이지 생성
  □ /terms-of-service (한국어/영어)

□ 내용
  □ 서비스 이용 규칙
  □ 금지 행위 (욕설, 혐오, 불법 콘텐츠)
  □ 계정 정지/삭제 정책
  □ 지적 재산권
  □ 면책 조항

□ 동의 Checkbox
  □ "서비스 이용약관에 동의합니다" (필수)
```

### Consent Log (Phase 1) ✅

```
□ DB Schema
  CREATE TABLE user_consents (
      id SERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES users(id),
      consent_type VARCHAR(50),  -- 'privacy_policy', 'terms_of_service'
      consented_at TIMESTAMP DEFAULT NOW(),
      ip_address INET,
      user_agent TEXT
  );

□ API
  □ POST /api/v1/consents (동의 기록)
  □ GET /api/v1/consents (동의 내역 조회)
```

## Parent-Student 승인 Flow 완성

### Approval Workflow (Phase 1) ✅

```
□ DB Schema
  CREATE TABLE parent_student_links (
      id SERIAL PRIMARY KEY,
      parent_id INTEGER REFERENCES users(id),
      student_id INTEGER REFERENCES users(id),
      status VARCHAR(20),  -- 'pending', 'approved', 'rejected', 'expired'
      requested_at TIMESTAMP DEFAULT NOW(),
      approved_at TIMESTAMP,
      expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days'
  );

□ API
  □ POST /api/v1/parent/link-student (부모가 연결 요청)
  □ POST /api/v1/student/approve-parent/{link_id} (학생이 승인)
  □ POST /api/v1/student/reject-parent/{link_id} (학생이 거부)

□ Notification
  □ 학생에게 이메일 알림 (연결 요청)
  □ 부모에게 알림 (승인/거부 결과)

□ Auto-expiry
  □ 7일 경과 시 자동 만료 (status = 'expired')
```

## Audit Log API

### Audit Log Schema (Phase 1) ✅

```
□ DB Schema
  CREATE TABLE audit_log (
      id BIGSERIAL PRIMARY KEY,
      user_id INTEGER,
      zone_id VARCHAR(10) NOT NULL,
      org_id INTEGER NOT NULL,
      action VARCHAR(50) NOT NULL,  -- 'login', 'logout', 'create', 'update', 'delete', 'access'
      resource_type VARCHAR(50) NOT NULL,  -- 'exam', 'user', 'ai_tutor', 'file'
      resource_id VARCHAR(100),
      ip_address INET,
      user_agent TEXT,
      metadata JSONB,
      created_at TIMESTAMP DEFAULT NOW(),
      INDEX idx_audit_user_created (user_id, created_at),
      INDEX idx_audit_action_created (action, created_at)
  );

□ API
  □ POST /api/v1/audit-log (로그 기록, Internal only)
  □ GET /api/v1/audit-log (로그 조회, sys_admin/zone_admin만)

□ Retention
  □ 1년 보존
  □ 1년 후 자동 삭제 (Daily Cron Job)
```

---

# 📚 6. 문서 실행 체크리스트 (Documentation)

## 문서 v1.0 태깅

```
□ 모든 Architecture 문서 v1.0 태깅
  □ MEGACITY_MASTER_INDEX.md v1.0
  □ MEGACITY_DOMAIN_ARCHITECTURE.md v1.0
  □ MEGACITY_NETWORK_ARCHITECTURE.md v1.0
  □ MEGACITY_TENANT_ARCHITECTURE.md v1.0
  □ MEGACITY_SERVICE_TOPOLOGY.md v1.0
  □ MEGACITY_AUTH_SSO_ARCHITECTURE.md v1.0
  □ MEGACITY_DATABASE_ARCHITECTURE.md v1.0
  □ MEGACITY_POLICY_ENGINE.md v1.0
  □ MEGACITY_AI_INFRASTRUCTURE.md v1.0
  □ MEGACITY_SECURITY_ARCHITECTURE.md v1.0
  □ MEGACITY_DEVOPS_RUNBOOK.md v1.0
  □ MEGACITY_RELEASE_MANAGEMENT.md v1.0
  □ MEGACITY_MONITORING_OBSERVABILITY.md v1.0
  □ MEGACITY_GOVERNANCE_OPERATIONS.md v1.0
  □ MEGACITY_GLOBAL_COMPLIANCE.md v1.0
  □ MEGACITY_USER_SAFETY.md v1.0
  □ MEGACITY_TEAM_STRUCTURE.md v1.0
  □ MEGACITY_GROWTH_GTM.md v1.0
  □ MEGACITY_COST_OPTIMIZATION.md v1.0
  □ MEGACITY_DOCUMENTATION_INDEX.md v1.0
  □ MEGACITY_EXECUTION_CHECKLIST.md v1.0 (이 문서)

□ Git Tag 생성
  □ git tag docs-v1.0
  □ git push origin docs-v1.0
```

## MegaCity Index 연결

```
□ MEGACITY_DOCUMENTATION_INDEX.md 업데이트
  □ 모든 문서 링크 확인
  □ 문서 간 의존성 명시
  □ 역할별 추천 문서 업데이트

□ README.md 업데이트
  □ /ops/architecture/README.md 생성
  □ Documentation Index 링크
```

## Release Management Guide 적용

```
□ Semantic Versioning 적용
  □ backend-api-vX.Y.Z
  □ frontend-vX.Y.Z
  □ ai-cluster-vX.Y.Z

□ Approval Workflow 구현
  □ GitHub Branch Protection (main)
  □ Required Reviewers (2명)
  □ CI/CD Checks (Test, Lint)

□ Deployment Strategies
  □ Rolling Deployment (기본)
  □ Canary Deployment (주요 기능)
  □ Blue-Green Deployment (AI Cluster)

□ Rollback Policy
  □ Auto-rollback Script (Prometheus 기반)
  □ Rollback Criteria (Error rate > 5%, Latency > 2.5s)
```

## FinOps 비용 절감 전략 적용

```
□ GPU 비용 절감
  □ RTX 5090 로컬 GPU 구매 ($2,000 투자, 연 $27K-$32K 절감)
  □ Off-peak GPU 축소 (23:00-08:00 → 1대만 운영)
  □ vLLM KV Cache 튜닝 (처리량 30% 증가)

□ LLM 비용 절감
  □ Model Routing (7B 60%, 32B 30%, 70B 10%)
  □ Prompt Compression (50% 토큰 감소)
  □ Response Caching (Redis, Hit 30%)

□ Storage 비용 절감
  □ Cloudflare R2 사용 (Egress free)
  □ Backblaze B2 Archive (Cold Storage)
  □ Auto-deletion (7-30일)

□ Network 비용 절감
  □ CDN Cache Hit Rate 90%+
  □ HTTP/3 + Brotli 압축
  □ Lazy Loading

□ 비용 모니터링
  □ Grafana Cost Dashboard 생성
  □ 월간 비용 리포트 (목표: $4,500 이하)
```

---

# 🏁 7. 결론 (Conclusion)

이 **Execution Checklist**는 DreamSeedAI MegaCity **Phase 0~4 전체 실행을 위한 실전 To-Do 문서**입니다.

## 핵심 실행 원칙

```
1. Phase별 순차 실행 (Phase 0 → 1 → 2 → 3 → 4)
2. 체크리스트 기반 진행 (□ → ☑️)
3. 매일/매주/매월 운영 체크리스트 준수
4. Zone별 활성화 조건 충족 후 Launch
5. AI/보안/정책 최우선 적용
6. 문서 v1.0 완성 및 유지보수
```

## 현재 우선순위 (Phase 1 — Core MVP)

```
🔥 최우선 (Week 1-2)
  1. Backend Core API 완성 (User, Exam, AI Tutor)
  2. Frontend Teacher/Parent Dashboard
  3. vLLM 7B 서버 구축
  4. Whisper Large-v3 서버 구축
  5. CI/CD 파이프라인 구축

⚡ 우선 (Week 3-4)
  6. CAT Engine v1 구현
  7. RBAC/PBAC 정책 적용
  8. Cloudflare WAF 규칙 적용
  9. AI Safety Layer 구현
  10. Monitoring Dashboard 구축

✅ 중요 (Month 2)
  11. UnivPrepAI.com 베타 테스트
  12. GDPR/PIPA 동의 페이지 생성
  13. Audit Log 시스템 구현
  14. Backup/DR 검증
  15. 문서 v1.0 태깅
```

DevOps, AI, Backend, Frontend, Governance **모든 팀이 이 체크리스트를 기준으로 실행**하게 됩니다.

---

**문서 완료 - DreamSeedAI MegaCity Phase 0 → Phase 4 Execution Checklist v1.0**

**Total Items**: 200+ 체크리스트 항목  
**Coverage**: Infrastructure, AI, Backend, Frontend, Security, Governance, Operations, Documentation  
**Timeline**: Phase 0 (90% 완료) → Phase 1 (지금 시작) → Phase 2-4 (2025-2027)
