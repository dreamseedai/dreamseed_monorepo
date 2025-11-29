# 🏆 DreamSeedAI Master Plan 문서 가이드

**작성일:** 2025-11-22  
**최종 업데이트:** 2025-11-24  
**목적:** 전체 프로젝트의 바탕이 되는 Master Plan 문서들을 체계적으로 안내

---

## 📚 Master Plan 문서란?

Master Plan 문서들은 DreamSeedAI MegaCity 프로젝트의 **전체 비전, 전략, 아키텍처, 실행 계획**을 담은 최상위 문서들입니다. Phase별 상태 문서들이 "현재 진행 상황"을 추적한다면, Master Plan은 "어디로 가는지, 어떻게 갈 것인지"를 정의합니다.

---

## 🎯 문서 읽기 순서 (추천)

### 신규 팀원 (1-2시간 Onboarding)

```
1. MEGACITY_MASTER_INDEX.md          (10분) - 전체 지도
   ↓
2. ARCHITECTURE_MASTERPLAN.md        (30분) - Phase 0-5 청사진
   ↓
3. MEGACITY_EXECUTION_CHECKLIST.md   (20분) - 실행 체크리스트
   ↓
4. Phase별 상태 문서                  (20분) - 현재 진행 상황
   ↓
5. 해당 팀 관련 문서                  (20분) - 역할별 상세
```

### 경영진 / 투자자 (30분 Brief)

```
1. MEGACITY_INVESTOR_WHITEPAPER.md   (10분) - Executive Summary
   ↓
2. MEGACITY_FINANCIAL_MODEL.md       (10분) - 재무 모델
   ↓
3. MEGACITY_MASTER_BOOK.md           (10분) - 전체 구조 이해
```

### 기술 리더 / 아키텍트 (2-3시간 Deep Dive)

```
1. ARCHITECTURE_MASTERPLAN.md        (40분) - 기술 청사진
   ↓
2. MEGACITY_V2_ARCHITECTURE.md       (30분) - 2027-2028 구조
   ↓
3. MEGACITY_V3_ARCHITECTURE.md       (30분) - 2029-2030 구조
   ↓
4. MEGACITY_AI_MODEL_STRATEGY.md     (20분) - AI 전략
   ↓
5. 각 도메인별 상세 문서              (60분) - Network, Database, Service 등
```

---

## 📖 Master Plan 문서 목록

### 🏆 Tier 1 - 최상위 Master Plan (필독)

#### 1. Architecture Masterplan
- **파일:** `/ops/maintenance/ARCHITECTURE_MASTERPLAN.md`
- **분량:** 1,119 줄
- **내용:** 100만 유저 AI 교육 플랫폼 종합 설계서
- **핵심:**
  - Phase 0-5 전체 로드맵
  - 인프라 기반시설 vs 탄력적 확장 구분
  - "도시처럼 설계하라" 철학
  - 월별 비용 및 수익 시뮬레이션
  - Hybrid Architecture (로컬 GPU + Cloud)

**읽어야 할 사람:** 전체 팀, 특히 Backend/DevOps/AI

---

#### 2. MegaCity Master Book
- **파일:** `/ops/architecture/MEGACITY_MASTER_BOOK.md`
- **분량:** 424 줄
- **내용:** 전사 공식 백과사전 - 12개 Book으로 구성
- **핵심:**
  - BOOK 1: Vision & Philosophy
  - BOOK 2: Architecture V1-V3
  - BOOK 3: AI Infrastructure
  - BOOK 4: Education Pedagogy
  - BOOK 5: Product Architecture
  - BOOK 6-12: Backend, Data, Security, DevOps, Operations, Global, Financials

**읽어야 할 사람:** 경영진, 팀 리더, 신규 리더

---

#### 3. MegaCity Master Index
- **파일:** `/ops/architecture/MEGACITY_MASTER_INDEX.md`
- **분량:** 249 줄
- **내용:** 전체 아키텍처 문서 네비게이션 가이드
- **핵심:**
  - 추천 읽기 순서
  - 9개 Zone 구조
  - 문서 간 연결 관계
  - Construction Timing

**읽어야 할 사람:** 신규 팀원, 협력사, 외주 개발자

---

### 🎯 Tier 2 - 실행 Master Plan

#### 4. MegaCity Execution Checklist
- **파일:** `/ops/architecture/MEGACITY_EXECUTION_CHECKLIST.md`
- **분량:** 1,336 줄
- **내용:** Phase 0 → Phase 4 실행 체크리스트
- **핵심:**
  - Phase별 Infrastructure/Backend/Frontend/AI/Governance 체크리스트
  - 9개 Zone 활성화 순서 (UnivPrepAI → SkillPrepAI → ...)
  - AI 모델 배포 우선순위 (vLLM 7B → 32B → 70B)
  - 보안/정책/감사 체크리스트
  - 현재 우선순위 (Phase 1 Core MVP)

**읽어야 할 사람:** PM, PO, 개발 팀 전체

---

#### 5. MegaCity Execution Board
- **파일:** `/ops/architecture/MEGACITY_EXECUTION_BOARD.md`
- **내용:** 2026-2027 Gantt 스타일 실행 보드
- **핵심:**
  - 주차별 실행 계획
  - 팀별 할당
  - 마일스톤 정의
  - Critical Path 식별

**읽어야 할 사람:** PM, Scrum Master, 팀 리더

---

#### 6. 2026 Execution Plan
- **파일:** `/ops/architecture/MEGACITY_2026_EXECUTION_PLAN.md`
- **내용:** 2026년 상세 실행 계획
- **핵심:**
  - 2026 Q1-Q4 계획
  - Zone별 런치 일정
  - 인력 증원 계획
  - 투자 유치 타이밍

**읽어야 할 사람:** 경영진, PM, CFO

---

#### 7. 2028-2031 Roadmap
- **파일:** `/ops/architecture/MEGACITY_ROADMAP_2028_2031.md`
- **내용:** 장기 비전 (AR/VR, Multi-Agent AI)
- **핵심:**
  - V3 Architecture (Autonomous AI Tutor)
  - Multi-modal Learning (AR/VR)
  - Multi-Agent System
  - 글로벌 1,000만 사용자

**읽어야 할 사람:** 경영진, CTO, 전략 기획

---

### 🏗️ Tier 3 - 아키텍처 상세

#### 8. MegaCity V2 Architecture
- **파일:** `/ops/architecture/MEGACITY_V2_ARCHITECTURE.md`
- **내용:** 2027-2028 Multi-region 아키텍처
- **핵심:**
  - Multi-region Deployment (Seoul, Tokyo, Virginia, Frankfurt)
  - Active-Active 구성
  - CDN + Edge Computing
  - 99.99% SLA

**읽어야 할 사람:** Backend, DevOps, SRE

---

#### 9. MegaCity V3 Architecture
- **파일:** `/ops/architecture/MEGACITY_V3_ARCHITECTURE.md`
- **내용:** 2029-2030 Autonomous AI Tutor 아키텍처
- **핵심:**
  - GPT-4 기반 자율 학습 플래너
  - Multi-Agent Collaboration
  - On-device AI (3B 모델)
  - Zero-shot Learning

**읽어야 할 사람:** AI Team, Backend, Product

---

#### 10-15. 도메인별 상세 아키텍처

| 문서 | 내용 | 담당 팀 |
|------|------|---------|
| **Network Architecture** | Cloudflare + Nginx/Traefik | DevOps |
| **Database Architecture** | PostgreSQL + Redis + RLS | Backend |
| **Service Topology** | 마이크로서비스 구조 | Backend |
| **AI Model Strategy** | LLM 라우팅 및 모델 선택 | AI Team |
| **AI Infrastructure** | GPU 서버 및 vLLM 구성 | AI + DevOps |
| **Education Pedagogy** | IRT/CAT/학습과학 | AI + Product |

---

### 💼 Tier 4 - 전략 & 비즈니스

#### 16. Investor Whitepaper
- **파일:** `/ops/architecture/MEGACITY_INVESTOR_WHITEPAPER.md`
- **내용:** 투자자용 백서
- **핵심:**
  - Executive Summary
  - 시장 분석 (TAM $50B)
  - 경쟁 우위
  - 재무 프로젝션
  - Exit Strategy

**읽어야 할 사람:** CEO, CFO, 투자 담당

---

#### 17. Financial Model
- **파일:** `/ops/architecture/MEGACITY_FINANCIAL_MODEL.md`
- **내용:** 3년 P&L 프로젝션
- **핵심:**
  - 월별 비용 분석
  - 수익 시뮬레이션
  - Break-even 분석
  - Unit Economics

**읽어야 할 사람:** CFO, 경영진, 투자자

---

#### 18. Global Launch Plan
- **파일:** `/ops/architecture/MEGACITY_GLOBAL_LAUNCH_PLAN.md`
- **내용:** APAC → US → EU 확장 전략
- **핵심:**
  - Phase 1: Korea (2026)
  - Phase 2: APAC (2027)
  - Phase 3: North America (2028)
  - Phase 4: Europe & Middle East (2029-2030)

**읽어야 할 사람:** 경영진, 마케팅, 사업개발

---

#### 19. Growth & GTM Strategy
- **파일:** `/ops/architecture/MEGACITY_GROWTH_GTM.md`
- **내용:** 성장 및 Go-to-Market 전략
- **핵심:**
  - Acquisition Funnel
  - Viral Loop 설계
  - B2C → B2B2C 전환
  - 파트너십 전략

**읽어야 할 사람:** 마케팅, 영업, Product

---

#### 20. Talent Playbook
- **파일:** `/ops/architecture/MEGACITY_TALENT_PLAYBOOK.md`
- **내용:** 채용 및 조직 구성
- **핵심:**
  - Phase별 인력 증원 계획
  - 역할별 JD
  - 성과 평가 체계
  - 보상 구조

**읽어야 할 사람:** HR, 경영진, 팀 리더

---

### 🔧 Tier 5 - 운영 & 관리

#### 21-25. 운영 문서

| 문서 | 내용 | 담당 팀 |
|------|------|---------|
| **Incident & Risk Playbook** | SRE 및 DR 절차 | DevOps, SRE |
| **DevOps Runbook** | 배포 및 운영 가이드 | DevOps |
| **Monitoring & Observability** | Prometheus + Grafana | DevOps |
| **Legal Compliance Handbook** | GDPR/PIPA/FERPA/COPPA | Legal, Compliance |
| **Security Architecture** | OWASP + AI Security | Security, Backend |

---

## 📊 문서 맵 (시각화)

```
┌─────────────────────────────────────────────────────────────┐
│                    MASTER PLAN HIERARCHY                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tier 1: 최상위 Master Plan                          │  │
│  │  - Architecture Masterplan                           │  │
│  │  - MegaCity Master Book                              │  │
│  │  - MegaCity Master Index                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tier 2: 실행 Master Plan                            │  │
│  │  - Execution Checklist (Phase 0-4)                   │  │
│  │  - Execution Board (2026-2027)                       │  │
│  │  - 2026 Execution Plan                               │  │
│  │  - 2028-2031 Roadmap                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tier 3: 아키텍처 상세                                │  │
│  │  - V2/V3 Architecture                                │  │
│  │  - Network/DB/Service Architecture                   │  │
│  │  - AI Model Strategy & Infrastructure                │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tier 4: 전략 & 비즈니스                              │  │
│  │  - Investor Whitepaper                               │  │
│  │  - Financial Model                                   │  │
│  │  - Global Launch Plan                                │  │
│  │  - Growth & GTM                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tier 5: 운영 & 관리                                  │  │
│  │  - Incident Playbook                                 │  │
│  │  - DevOps Runbook                                    │  │
│  │  - Monitoring                                        │  │
│  │  - Compliance & Security                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 역할별 필독 문서

### Backend Developer
1. Architecture Masterplan
2. Execution Checklist
3. V2 Architecture
4. Database Architecture
5. Service Topology

### Frontend Developer
1. Architecture Masterplan (인프라 이해)
2. Execution Checklist (Phase별 작업)
3. Product Requirement Book
4. Mobile Architecture (React Native)

### AI Engineer
1. Architecture Masterplan
2. AI Model Strategy
3. AI Infrastructure
4. Education Pedagogy Framework
5. V3 Architecture (Autonomous AI)

### DevOps / SRE
1. Architecture Masterplan
2. V2 Architecture (Multi-region)
3. Network Architecture
4. DevOps Runbook
5. Incident Playbook

### Product Manager
1. MegaCity Master Book
2. Execution Checklist
3. Product Requirement Book
4. Growth & GTM Strategy

### 경영진 / CEO
1. MegaCity Master Book
2. Investor Whitepaper
3. Financial Model
4. Global Launch Plan
5. Talent Playbook

---

## 🔄 문서 업데이트 주기

| Tier | 문서 유형 | 업데이트 주기 | 담당 |
|------|-----------|---------------|------|
| **Tier 1** | 최상위 Master Plan | 분기별 (3개월) | CTO + 아키텍트 |
| **Tier 2** | 실행 Master Plan | 월별 | PM + 팀 리더 |
| **Tier 3** | 아키텍처 상세 | Phase 전환 시 | 아키텍트 + 개발팀 |
| **Tier 4** | 전략 & 비즈니스 | 분기별 | 경영진 |
| **Tier 5** | 운영 & 관리 | 이슈 발생 시 | DevOps + 각 팀 |

---

## 📞 문서 관련 문의

- **아키텍처 문의**: CTO / 시니어 아키텍트
- **실행 계획 문의**: PM / Scrum Master
- **비즈니스 전략**: CEO / CFO
- **기술 상세**: 각 도메인 팀 리더

---

## 🔗 관련 링크

- [Phase별 상태 문서](./README.md)
- [현재 우선순위](./CURRENT_PRIORITIES.md)
- [Phase Overview](./PHASE_OVERVIEW.md)

---

**마지막 업데이트:** 2025-11-24  
**다음 검토:** 2026-02-24 (3개월 후)
