# 🧩 DreamSeedAI MegaCity – Team Structure & Roles

## 엔지니어링 · AI · DevOps · 콘텐츠 · PM · 운영 조직 구조 및 역할 정의

**버전:** 1.0  
**작성일:** 2025-11-21  
**작성자:** DreamSeedAI Organization & Architecture Team

---

# 📌 0. 개요 (Overview)

DreamSeedAI MegaCity는 9개 Zone(도메인), AI Cluster, SSO, 정책 엔진, 모니터링, DevOps 인프라를 포함한 **초대형 멀티플랫폼 도시 구조**입니다.

MegaCity의 성공적인 운영을 위해서는 **명확한 팀 구조, 역할, 책임(RACI)**이 필요합니다.
이 문서는 MegaCity 전체를 구성하는 조직 구조와 역할 정의를 제공합니다.

## 문서 목적

- MegaCity 전체 조직 구조 정의
- Division별 역할 및 책임 명확화
- 팀 간 협업 인터페이스 정의
- 인력 확장 계획(Phase 1~4) 제시
- 채용 및 온보딩 가이드라인 제공

---

# 🏙️ 1. MegaCity 전체 조직 구조 (High-Level Org Chart)

```
┌──────────────────────────────────────────────────────────┐
│              DreamSeedAI Holding (CEO/CTO)               │
└────┬─────────────────────────────────────────────────────┘
     │
     ├─────┬─────────────────────────────────────────────────
     │     │
     │     ▼
     │   ┌─────────────────────────────────────────────────┐
     │   │    Core Platform Division                       │
     │   │    (SSO, Policy, DB, Backend API)               │
     │   │    • Backend Engineers (3-5명)                  │
     │   │    • Platform Engineers (2-3명)                 │
     │   │    • Data Engineers (1-2명)                     │
     │   └─────────────────────────────────────────────────┘
     │
     ├─────┬─────────────────────────────────────────────────
     │     │
     │     ▼
     │   ┌─────────────────────────────────────────────────┐
     │   │    AI Systems Division                          │
     │   │    (LLM, Whisper, PoseNet, Diffusion)           │
     │   │    • AI Research Engineers (2-3명)              │
     │   │    • ML Engineers (2-3명)                       │
     │   │    • AI Infrastructure Engineers (1-2명)        │
     │   └─────────────────────────────────────────────────┘
     │
     ├─────┬─────────────────────────────────────────────────
     │     │
     │     ▼
     │   ┌─────────────────────────────────────────────────┐
     │   │    Product & Experience Division                │
     │   │    (UnivPrep/K-Zone 등 9개 Zone)                │
     │   │    • Product Managers (2-3명)                   │
     │   │    • Technical PM (1명)                         │
     │   │    • Zone Leads (9명, 파트타임 가능)            │
     │   └─────────────────────────────────────────────────┘
     │
     ├─────┬─────────────────────────────────────────────────
     │     │
     │     ▼
     │   ┌─────────────────────────────────────────────────┐
     │   │    DevOps & SRE Division                        │
     │   │    (Infra, Deployment, Monitoring)              │
     │   │    • DevOps Engineers (2-3명)                   │
     │   │    • SRE (Site Reliability Engineers) (2-3명)   │
     │   │    • Systems Engineers (1명)                    │
     │   └─────────────────────────────────────────────────┘
     │
     ├─────┬─────────────────────────────────────────────────
     │     │
     │     ▼
     │   ┌─────────────────────────────────────────────────┐
     │   │    Content & Curriculum Division                │
     │   │    (문제/강의/데이터셋)                         │
     │   │    • Curriculum Specialists (2-3명)             │
     │   │    • K-Zone Content Creators (2-3명)            │
     │   │    • Instructional Designers (1-2명)            │
     │   └─────────────────────────────────────────────────┘
     │
     ├─────┬─────────────────────────────────────────────────
     │     │
     │     ▼
     │   ┌─────────────────────────────────────────────────┐
     │   │    Design & Frontend Division                   │
     │   │    (UX/UI, Next.js)                             │
     │   │    • Frontend Engineers (3-4명)                 │
     │   │    • UX/UI Designers (2-3명)                    │
     │   │    • Product Designers (1-2명)                  │
     │   └─────────────────────────────────────────────────┘
     │
     └─────┬─────────────────────────────────────────────────
           │
           ▼
         ┌─────────────────────────────────────────────────┐
         │    Operations & Governance Division             │
         │    (Support, Compliance)                        │
         │    • Customer Support (2-4명)                   │
         │    • Compliance Officer (1명)                   │
         │    • K-Zone Community Managers (2-3명)          │
         └─────────────────────────────────────────────────┘
```

---

# 🧠 2. AI Systems Division (AI 시스템 팀)

## 2.1 담당 영역

### Core AI Engines

- **vLLM 기반 LLM 엔진**: Llama 3.1, Qwen2.5, DeepSeek-R1, Seoul-Medium-KR
- **Whisper STT 엔진**: Large-v3, 발음 정확도 분석, 다국어 지원
- **PoseNet / MoveNet**: 동작 인식, 댄스 스코어링, DTW 비교
- **Multi-modal 모델**: Qwen2-VL, LLaVA-Next (Text + Image + Video)
- **Diffusion/TTS**: Stable Diffusion, Emotion-based TTS, Voice Clone
- **AI Router**: Engine/GPU/Model 선택, Zone별 라우팅

### Infrastructure

- **GPU Cluster**: RTX 5090 × 2-5, CUDA 12.2, 성능 모니터링
- **AI Backend Workers**: Redis Streams 기반 비동기 처리
- **Model Registry**: 버전 관리, A/B 테스팅

## 2.2 역할 정의

### ● AI Research Engineer

**책임:**
- LLM Fine-tuning / LoRA / QLoRA 연구
- Prompt Engineering 최적화 (Chain-of-Thought, Few-Shot)
- 교육/언어 분야 도메인 특화 모델 연구
- 모델 성능 벤치마크 및 평가

**필수 기술:**
- Python, PyTorch, HuggingFace Transformers
- LLM Fine-tuning (LoRA, QLoRA, PEFT)
- Prompt Engineering
- 교육/언어학 도메인 지식

**KPI:**
- 모델 정확도 (F1 Score, BLEU, ROUGE)
- Inference 속도 (< 2s per request)
- User feedback score (4.0+/5.0)

---

### ● Machine Learning Engineer

**책임:**
- Whisper/PoseNet 파이프라인 개발 및 최적화
- Multi-modal inference 엔진 구축
- AI Backend + Worker 파이프라인 설계
- 배치 처리 및 큐 관리 (Redis Streams)

**필수 기술:**
- Python, FastAPI, Docker
- Whisper, PoseNet, OpenCV
- Redis, PostgreSQL
- Async/Queue 처리

**KPI:**
- Inference latency (Whisper < 3s, PoseNet < 1s)
- Queue backlog (< 100 jobs)
- GPU utilization (70-90%)

---

### ● AI Infrastructure Engineer

**책임:**
- GPU 서버 구축/유지보수 (CUDA, Docker, Kubernetes)
- vLLM, TensorRT 성능 튜닝
- AI Cluster 모니터링 (Prometheus, Grafana)
- GPU 온도/메모리/사용률 관리

**필수 기술:**
- CUDA, NVIDIA Driver, nvidia-smi
- Docker, Kubernetes, Helm
- vLLM, TensorRT, ONNX
- Prometheus, Grafana

**KPI:**
- GPU uptime (99.5%+)
- GPU temperature (< 85°C)
- Model loading time (< 2분)

---

## 2.3 AI Division 워크플로우

```
1. AI Research Engineer → 새 모델 연구/Fine-tuning
2. ML Engineer → 모델을 API/Worker로 통합
3. AI Infra Engineer → GPU 클러스터에 배포
4. DevOps → 프로덕션 배포 및 모니터링
5. PM → 성능 데이터 기반 다음 Sprint 계획
```

---

# 🧩 3. Core Platform Engineering (백엔드·플랫폼)

## 3.1 담당 영역

### Backend Services

- **FastAPI Backend**: REST API, WebSocket, Async I/O
- **Exam Engine**: CAT (Computerized Adaptive Testing), 시험 생성/채점
- **SSO / Global ID**: 토큰 발급/검증, MFA/TOTP
- **RBAC / PBAC**: 역할 기반 + 정책 기반 접근 제어
- **Multi-tenant**: zone_id + org_id 격리, RLS 적용

### Database & Data Layer

- **PostgreSQL**: Schema 설계, RLS, Indexing, Partitioning
- **PgBouncer**: Connection pooling (2000 max connections)
- **Redis**: Session, CAT state, Rate limiting, Policy cache
- **Alembic**: DB migration, Zero-downtime 배포

## 3.2 역할 정의

### ● Backend Engineer

**책임:**
- FastAPI 기능 개발 및 최적화
- DB 모델링 (SQLAlchemy ORM)
- API 성능 최적화 (N+1 쿼리 제거, Caching)
- 단위 테스트 / 통합 테스트 (pytest)

**필수 기술:**
- Python, FastAPI, SQLAlchemy
- PostgreSQL, Redis
- Docker, Git, pytest
- RESTful API 설계

**KPI:**
- API latency p95 (< 500ms)
- Test coverage (> 80%)
- Code review turnaround (< 24시간)

---

### ● Platform Engineer

**책임:**
- 인증/보안/토큰/정책 엔진 설계
- API Gateway / Reverse Proxy 관리 (Nginx, Traefik)
- Multi-tenant 아키텍처 설계 및 유지
- Rate limiting, CORS, Security headers

**필수 기술:**
- Nginx, Traefik, API Gateway
- JWT, OAuth2, OIDC
- PostgreSQL RLS
- Security best practices

**KPI:**
- Token 무결성 (0 security incidents)
- API Gateway uptime (99.9%+)
- Multi-tenant 격리 검증 (100% 통과)

---

### ● Data Engineer

**책임:**
- mpcstudy → DreamSeed 데이터 ETL 파이프라인
- 문제/콘텐츠 정규화 및 품질 관리
- 분석 파이프라인 구성 (DAU/MAU/Retention)
- Data Warehouse 설계 (BigQuery, Snowflake)

**필수 기술:**
- Python, SQL, Pandas, PySpark
- ETL tools (Airflow, dbt)
- PostgreSQL, BigQuery
- Data modeling

**KPI:**
- ETL 성공률 (> 99%)
- 데이터 품질 (Duplicate < 1%, Missing < 0.5%)
- Pipeline latency (< 10분)

---

## 3.3 Core Platform 워크플로우

```
1. Backend Engineer → 기능 개발 (FastAPI)
2. Platform Engineer → 인증/보안/Gateway 통합
3. Data Engineer → 데이터 파이프라인 구축
4. DevOps → 배포 및 모니터링
5. QA → 통합 테스트 및 검증
```

---

# 💻 4. Design & Frontend Division

## 4.1 담당 영역

### Frontend Applications

- **Next.js / TypeScript / React**: SSR, CSR, ISR
- **각 Zone별 UI 개발**: UnivPrep, K-Zone 등 9개 도메인
- **Teacher/Parent Dashboard**: 학생 진도, 성적 분석, 승인 관리
- **K-Zone UI**: 음성/댄스 학습, 커뮤니티, 리더보드

### Design System

- **DreamSeedAI Design System**: 컴포넌트 라이브러리, 스타일 가이드
- **Responsive Design**: 모바일/태블릿/데스크톱
- **Accessibility**: WCAG 2.1 AA 준수

## 4.2 역할 정의

### ● Frontend Engineer

**책임:**
- Next.js SSR/CSR/ISR 기반 애플리케이션 개발
- TanStack Query (React Query) / Zustand 상태 관리
- 컴포넌트 라이브러리 개발 (Storybook)
- 성능 최적화 (Lighthouse score > 90)

**필수 기술:**
- Next.js, TypeScript, React
- TanStack Query, Zustand
- CSS-in-JS (Emotion, Styled-Components)
- Jest, React Testing Library

**KPI:**
- Lighthouse score (> 90)
- FCP (First Contentful Paint) < 1.5s
- CLS (Cumulative Layout Shift) < 0.1
- Code review turnaround (< 24시간)

---

### ● UX/UI Designer

**책임:**
- DreamSeedAI Design System 관리 (Figma)
- 모바일·웹 UI 프로토타입 제작
- 사용자 인터뷰 및 Usability Testing
- Design QA (디자인 구현 검증)

**필수 기술:**
- Figma, Sketch, Adobe XD
- Design System 설계
- Prototyping, Wireframing
- User Research

**KPI:**
- Design delivery 속도 (Sprint 내 100% 완료)
- Usability test score (> 4.0/5.0)
- Design-to-code consistency (> 95%)

---

### ● Product Designer

**책임:**
- 교육/문화 UX 설계 (학습 경로, 시험 UX)
- K-Zone 인터랙션 디자인 (음성/댄스 UI)
- User Journey Mapping
- A/B 테스트 설계 및 분석

**필수 기술:**
- UX Design, User Research
- Journey Mapping, Personas
- A/B Testing, Analytics (Mixpanel, GA4)
- Prototyping tools

**KPI:**
- User activation rate (> 30%)
- Retention D7 (> 40%)
- Feature adoption rate (> 20%)

---

## 4.3 Frontend Division 워크플로우

```
1. Product Designer → User Research, Journey Mapping
2. UX/UI Designer → Wireframe, High-fidelity Design
3. Frontend Engineer → 구현 (Next.js)
4. QA → Cross-browser/device 테스트
5. PM → A/B 테스트 결과 분석
```

---

# 🛠️ 5. DevOps & SRE Division

## 5.1 담당 영역

### Infrastructure

- **Cloudflare → Gateway → API → DB**: 전체 라우팅 관리
- **CI/CD**: GitHub Actions, Docker, Kubernetes
- **Monitoring**: Prometheus, Grafana, Loki, Tempo
- **Backup & DR**: PostgreSQL WAL, Redis RDB, S3/R2/B2

### Reliability

- **On-call 운영**: 24/7 장애 대응 (P1~P4)
- **Incident Response**: Runbook 실행, Post-mortem 작성
- **Capacity Planning**: 서버/GPU/DB 리소스 관리

## 5.2 역할 정의

### ● DevOps Engineer

**책임:**
- Docker/Kubernetes 배포 및 관리
- CI/CD 파이프라인 구축 (GitHub Actions)
- Infrastructure as Code (Terraform, Ansible)
- Blue-Green / Canary Deployment

**필수 기술:**
- Docker, Kubernetes, Helm
- GitHub Actions, GitLab CI
- Terraform, Ansible
- Nginx, Traefik

**KPI:**
- Deployment frequency (주 2회 이상)
- Deployment success rate (> 98%)
- Rollback time (< 5분)

---

### ● Site Reliability Engineer (SRE)

**책임:**
- On-call 운영 (24/7 로테이션)
- 장애(P1~P4) 대응 및 복구
- Post-mortem 작성 및 재발 방지
- SLO/SLI 정의 및 모니터링

**필수 기술:**
- Linux, Bash, Python
- Prometheus, Grafana, Loki
- PostgreSQL, Redis
- Incident Management

**KPI:**
- MTTR (Mean Time To Recovery) < 30분 (P1)
- Uptime (99.9%+)
- Post-mortem 작성 (장애 후 24시간 내)

---

### ● Systems Engineer

**책임:**
- 서버/네트워크 구성 (Nginx, Traefik, Firewall)
- 보안 정책 적용 (WAF, Rate Limiting, TLS)
- 시스템 성능 튜닝 (Kernel, TCP, File descriptors)
- SSL 인증서 관리 (Let's Encrypt, Cloudflare Origin)

**필수 기술:**
- Nginx, HAProxy, Traefik
- Firewall (UFW, iptables)
- TLS/SSL, Security hardening
- Linux system administration

**KPI:**
- Security incidents (0건)
- SSL certificate uptime (100%)
- System performance score (> 90)

---

## 5.3 DevOps & SRE 워크플로우

```
1. DevOps Engineer → CI/CD 파이프라인 구축
2. Backend/Frontend → Code push (main branch)
3. CI/CD → 자동 빌드/테스트/배포
4. SRE → Health check 모니터링
5. 장애 발생 시 → SRE On-call 대응
6. Post-Mortem → 재발 방지 정책 수립
```

---

# 📚 6. Content & Curriculum Division

## 6.1 담당 영역

### Educational Content

- **각 Zone별 교육 콘텐츠 제작**: UnivPrep, SkillPrep, MediPrep 등
- **문제은행(mpcstudy) 변환/정규화**: 80,000+ 문제 마이그레이션
- **커리큘럼 설계**: 학습 경로, 난이도 조정, 시험 출제 전략

### K-Zone Content

- **음성/비디오 데이터셋 관리**: K-POP, K-Drama 콘텐츠
- **발음/댄스 학습 자료**: 음성 인식, 동작 분석 데이터셋
- **크리에이터 스튜디오**: AI 생성 콘텐츠 (Diffusion, TTS)

## 6.2 역할 정의

### ● Curriculum Specialist

**책임:**
- UnivPrep/SkillPrep 교육 콘텐츠 개발
- 시험/커리큘럼 설계 (CAT 난이도 조정)
- 학습 효과 분석 (Retention, Completion rate)
- 교육 전문가(교사, 교수) 협업

**필수 기술:**
- 교육학/심리학 배경
- 문제 출제 및 난이도 조정
- 데이터 분석 (Excel, SQL)
- LMS (Learning Management System) 이해

**KPI:**
- 콘텐츠 생산량 (월 500+ 문제)
- 콘텐츠 품질 (학생 평가 > 4.0/5.0)
- Completion rate (> 60%)

---

### ● K-Zone Content Creator

**책임:**
- K-POP/Drama 기반 콘텐츠 제작
- 음성/댄스 교육자료 수집·편집
- 저작권 관리 (라이선스, 동의서)
- 크리에이터 커뮤니티 관리

**필수 기술:**
- 비디오/오디오 편집 (Premiere Pro, Audacity)
- 저작권 법률 이해
- K-POP/Drama 도메인 지식
- 커뮤니티 관리

**KPI:**
- 콘텐츠 생산량 (월 50+ 영상/오디오)
- 사용자 참여도 (Engagement rate > 30%)
- 저작권 이슈 (0건)

---

### ● Instructional Designer

**책임:**
- 학습 경로 / 시나리오 / 퀘스트 설계
- Gamification 요소 추가 (배지, 리더보드, 미션)
- 학습 효과 측정 (Learning Analytics)
- 멀티미디어 콘텐츠 설계 (비디오, 인터랙티브)

**필수 기술:**
- Instructional Design (ADDIE, SAM)
- Gamification 이론
- Learning Analytics
- Articulate Storyline, Camtasia

**KPI:**
- 학습 완료율 (> 60%)
- 학습 효과 (시험 점수 향상 > 10%)
- Gamification 참여도 (> 40%)

---

## 6.3 Content Division 워크플로우

```
1. Curriculum Specialist → 커리큘럼 설계
2. K-Zone Content Creator → 콘텐츠 제작
3. Instructional Designer → 학습 경로 및 Gamification 설계
4. Data Engineer → 콘텐츠 DB 저장 및 정규화
5. PM → 콘텐츠 성과 분석 및 다음 Sprint 계획
```

---

# 🎯 7. Product & PM Division

## 7.1 담당 영역

### Product Strategy

- **MegaCity 전체 Vision 관리**: Core → Zone 확장 전략
- **Zone별 Feature 우선순위 정의**: MoSCoW (Must, Should, Could, Won't)
- **Roadmap 운영**: Phase 1-4 확장 계획
- **사용자 리서치/데이터 분석**: DAU/MAU/Retention/ARPU

### Stakeholder Management

- **교사/학부모/학생 인터뷰**: Pain points, Feature requests
- **경쟁사 분석**: 벤치마크, Differentiation 전략
- **GTM (Go-to-Market) 전략**: Launch, Marketing, Pricing

## 7.2 역할 정의

### ● Product Manager

**책임:**
- 기능 우선순위(MoSCoW) 결정
- Sprint 계획 및 진행 (2주 Sprint)
- 사용자 인터뷰/요구사항 분석
- Roadmap 관리 (Phase 1-4)

**필수 기술:**
- Product Management 프레임워크 (Lean, Agile)
- User Research, Analytics (Mixpanel, GA4)
- Roadmap 도구 (Jira, Linear)
- Stakeholder communication

**KPI:**
- Feature delivery 속도 (Sprint 내 90% 완료)
- User satisfaction (NPS > 40)
- Roadmap 달성률 (> 80%)

---

### ● Technical Product Manager

**책임:**
- AI/Backend/DevOps 팀 조율
- 기술 의사결정 문서화 (Architecture Decision Records)
- 통합 아키텍처 이해 (MegaCity 전체)
- 기술 부채 관리 (Tech debt prioritization)

**필수 기술:**
- 백엔드/AI/DevOps 기술 이해
- Architecture design
- Technical writing
- Cross-functional communication

**KPI:**
- 기술 의사결정 속도 (< 1주)
- 기술 부채 감소 (분기별 -10%)
- Cross-team collaboration score (> 4.0/5.0)

---

## 7.3 PM Division 워크플로우

```
1. PM → 사용자 리서치, Feature 우선순위 결정
2. Technical PM → 기술 팀과 협의, 아키텍처 정의
3. Design/Frontend → UI/UX 설계
4. Backend/AI → 기능 개발
5. QA → 테스트 및 검증
6. PM → 성과 분석 및 다음 Sprint 계획
```

---

# 🤝 8. Operations & Support Division

## 8.1 담당 영역

### Customer Support

- **학생·학부모·교사 고객 지원**: 실시간 채팅, 이메일, 전화
- **Teacher/Parent 관리 지원**: 계정 설정, 승인, 문제 해결
- **FAQ / 헬프센터 관리**: 문서화, 자동화

### Compliance & Governance

- **Privacy/Compliance(PIPA/GDPR)**: 개인정보 보호, 로그 관리
- **Audit Log 관리**: 사용자 행동 추적, PII 삭제
- **보안 정책 준수**: WAF 로그, 침입 탐지

### Community Management

- **K-Zone 글로벌 커뮤니티 운영**: Discord, Slack, SNS
- **이벤트/콘테스트 기획**: K-POP 챌린지, 댄스 배틀
- **User-generated content 관리**: 저작권, 신고 처리

## 8.2 역할 정의

### ● Customer Support

**책임:**
- 실시간 채팅/문의 처리 (Zendesk, Intercom)
- Teacher/Parent 관리 지원
- FAQ / 헬프센터 관리
- Support ticket 분석 (Common issues)

**필수 기술:**
- Customer support tools (Zendesk, Intercom)
- 교육 플랫폼 이해
- 커뮤니케이션 스킬
- 문제 해결 능력

**KPI:**
- 응답 시간 (First response < 1시간)
- 해결 시간 (Resolution time < 24시간)
- Customer satisfaction (CSAT > 4.5/5.0)

---

### ● Compliance Officer

**책임:**
- 개인정보 보호 프로세스 유지 (PIPA, GDPR)
- 로그/Audit/PII 삭제 관리
- 보안 정책 준수 확인
- 데이터 요청 처리 (GDPR Article 15)

**필수 기술:**
- PIPA, GDPR, COPPA 법률 이해
- Audit log 분석
- Security best practices
- Legal compliance

**KPI:**
- Compliance audit 통과율 (100%)
- Data breach incidents (0건)
- PII 삭제 처리 시간 (< 30일)

---

### ● K-Zone Community Manager

**책임:**
- 지역별 커뮤니티 관리 (KR, JP, CN, EN)
- SNS/글로벌 커뮤니케이션 (Twitter, Instagram, TikTok)
- 이벤트/콘테스트 기획 및 운영
- User feedback 수집 및 PM 전달

**필수 기술:**
- Community management
- SNS marketing
- 다국어 (KR/EN/JP/CN)
- Event planning

**KPI:**
- Community engagement rate (> 30%)
- Event participation rate (> 20%)
- User feedback 수집 (월 100+ responses)

---

## 8.3 Operations Division 워크플로우

```
1. Customer Support → 문의 접수 및 처리
2. Compliance Officer → 개인정보 보호 프로세스 확인
3. K-Zone Community Manager → 커뮤니티 관리 및 피드백 수집
4. PM → 피드백 분석 및 Feature 우선순위 반영
```

---

# 🏗️ 9. Zone 운영팀 구조 (각 도메인별)

각 Zone(9개)은 아래 형태의 **경량 운영 크루(Lite Crew)** 로 운영됩니다:

```
┌────────────────────────────────────────────┐
│         Zone Lead (파트타임 가능)          │
│         (예: UnivPrep Zone Lead)           │
└──────────┬─────────────────────────────────┘
           │
           ├─────────────────────────────────
           │
           ▼
┌──────────────────────────────────────────┐
│   Content/Teacher Lead (1-2명)           │
│   • 해당 Zone 콘텐츠 제작                 │
│   • 교사 온보딩 및 교육                   │
└──────────────────────────────────────────┘
           │
           ├─────────────────────────────────
           │
           ▼
┌──────────────────────────────────────────┐
│   Frontend/Design 담당 (공유 가능)        │
│   • 해당 Zone UI/UX 개발                  │
│   • Design System 적용                    │
└──────────────────────────────────────────┘
           │
           ├─────────────────────────────────
           │
           ▼
┌──────────────────────────────────────────┐
│   Support 담당 (공유 가능)                │
│   • 해당 Zone 고객 지원                   │
│   • FAQ 관리                              │
└──────────────────────────────────────────┘
```

**기술적 백엔드는 Core Platform/AI/DevOps 팀이 중앙에서 제공.**

## 9.1 Zone별 인력 배치 예시

| Zone | Zone Lead | Content Lead | Frontend | Support | 비고 |
|------|-----------|--------------|----------|---------|------|
| **UnivPrepAI** (100) | 1명 | 1-2명 | 공유 | 공유 | Phase 1 |
| **CollegePrepAI** (200) | 1명 | 1명 | 공유 | 공유 | Phase 2 |
| **SkillPrepAI** (300) | 1명 | 1명 | 공유 | 공유 | Phase 2 |
| **MediPrepAI** (400) | 1명 | 1명 | 공유 | 공유 | Phase 3 |
| **MajorPrepAI** (500) | 1명 | 1명 | 공유 | 공유 | Phase 3 |
| **My-Ktube.com** (600) | 1명 | 2-3명 | 공유 | 공유 | Phase 2 |
| **My-Ktube.ai** (610) | 1명 | 2-3명 | 공유 | 공유 | Phase 2 |
| **mpcstudy** (900) | 1명 | 1명 | - | 공유 | 유지 보수 |
| **DreamSeedAI.com** (0) | CEO/PM | - | 전담 | 전담 | Core City |

---

# 📈 10. 팀 규모 확장 계획 (Scaling Plan)

## Phase 0 (Pre-Launch, ~1K 사용자)

### 인력 구성 (5-7명)

```
Founder/CEO (1명)
  └─ Product + Strategy

Backend Engineer (2명)
  └─ FastAPI + DB + SSO

AI Engineer (1명)
  └─ vLLM + Whisper

Frontend Engineer (1명)
  └─ Next.js

Designer (1명)
  └─ UX/UI

Content Specialist (1명, 파트타임 가능)
  └─ UnivPrep 콘텐츠
```

### 주요 목표

- Core Platform 구축 (SSO, RBAC, DB)
- UnivPrep Zone 출시
- mpcstudy 마이그레이션

---

## Phase 1 (Early Growth, ~10K 사용자)

### 인력 구성 (10-15명)

```
Leadership
  ├─ CEO/Founder (1명)
  ├─ CTO (1명)
  └─ PM (1명)

Backend Team (3-4명)
  ├─ Backend Engineer × 2
  └─ Platform Engineer × 1-2

AI Team (2-3명)
  ├─ AI Research Engineer × 1
  └─ ML Engineer × 1-2

Frontend Team (2명)
  ├─ Frontend Engineer × 2

Design Team (1명)
  └─ UX/UI Designer × 1

Content Team (2명)
  ├─ Curriculum Specialist × 1
  └─ K-Zone Content Creator × 1

Support (1명)
  └─ Customer Support × 1
```

### 주요 목표

- UnivPrep Zone 완성
- K-Zone (My-Ktube.ai) 출시
- AI Tutor 기능 강화

---

## Phase 2 (Rapid Growth, ~100K 사용자)

### 인력 구성 (25-35명)

```
Leadership (5명)
  ├─ CEO/Founder
  ├─ CTO
  ├─ VP Engineering
  ├─ VP Product
  └─ VP Operations

Core Platform (5-7명)
  ├─ Backend Engineers × 3-4
  ├─ Platform Engineers × 2-3

AI Systems (5-7명)
  ├─ AI Research Engineers × 2-3
  ├─ ML Engineers × 2-3
  └─ AI Infrastructure Engineer × 1

DevOps & SRE (4-5명)
  ├─ DevOps Engineers × 2-3
  └─ SRE × 2

Frontend & Design (5-6명)
  ├─ Frontend Engineers × 3-4
  ├─ UX/UI Designers × 2

Content & Curriculum (4-5명)
  ├─ Curriculum Specialists × 2
  ├─ K-Zone Content Creators × 2
  └─ Instructional Designer × 1

Product & PM (2-3명)
  ├─ Product Managers × 2
  └─ Technical PM × 1

Operations & Support (3-4명)
  ├─ Customer Support × 2
  ├─ Compliance Officer × 1
  └─ Community Manager × 1
```

### 주요 목표

- 9개 Zone 중 5-6개 운영
- Multi-region 배포 (Seoul → Tokyo)
- B2B/B2G 진출

---

## Phase 3 (Scale, ~1M 사용자)

### 인력 구성 (50-70명)

```
Full Division 구성
  ├─ Core Platform Division (10-12명)
  ├─ AI Systems Division (8-10명)
  ├─ DevOps & SRE Division (6-8명)
  ├─ Frontend & Design Division (8-10명)
  ├─ Content & Curriculum Division (8-10명)
  ├─ Product & PM Division (4-5명)
  ├─ Operations & Support Division (6-8명)
  └─ Leadership (5-7명)
```

### 주요 목표

- 9개 Zone 전체 운영
- Global expansion (US, EU, SEA)
- Enterprise features (SSO, SAML)

---

## Phase 4 (Global, 1M+ 사용자)

### 인력 구성 (100+ 명)

```
Multi-region 운영팀
  ├─ Seoul HQ (50명)
  ├─ Tokyo Office (20명)
  ├─ US Office (20명)
  └─ EU Office (10명)
```

### 주요 목표

- 글로벌 서비스 (20+ 국가)
- Enterprise 고객 (100+ 기업)
- IPO 준비

---

# 🎓 11. 채용 및 온보딩 가이드

## 11.1 채용 프로세스

```
1. JD (Job Description) 작성
2. 채용 공고 (LinkedIn, 원티드, 자사 사이트)
3. 서류 전형 (Resume, Portfolio)
4. 코딩 테스트 (Backend/Frontend/AI 포지션)
5. 기술 면접 (2-3 rounds)
6. 문화 적합도 면접 (Culture fit)
7. 최종 면접 (Leadership)
8. Offer 협상
```

## 11.2 온보딩 체크리스트

### Day 1 (첫 출근)

```
□ Workspace 설정 (노트북, 모니터, 액세서리)
□ 계정 생성 (GitHub, Slack, Email, 1Password)
□ Welcome Kit 제공 (팀 소개, 회사 소개)
□ 팀 미팅 (Team Lead + 팀원 소개)
```

### Week 1 (첫 주)

```
□ MegaCity 아키텍처 문서 읽기 (13개 문서)
□ Codebase tour (Backend/Frontend/AI)
□ 첫 번째 작은 Task 할당 (Good first issue)
□ 1:1 미팅 (Manager)
```

### Month 1 (첫 달)

```
□ 첫 번째 Feature 완성
□ Code review 프로세스 숙지
□ 팀 Sprint 참여 (Planning, Retro)
□ 30일 체크인 (Feedback)
```

## 11.3 핵심 역량 (Core Competencies)

### Technical Skills

- **Backend**: Python, FastAPI, PostgreSQL, Redis
- **Frontend**: Next.js, TypeScript, React
- **AI**: PyTorch, HuggingFace, vLLM, Whisper
- **DevOps**: Docker, Kubernetes, GitHub Actions
- **Cloud**: AWS, GCP, Cloudflare

### Soft Skills

- **Communication**: 명확하고 간결한 커뮤니케이션
- **Collaboration**: Cross-functional 팀 협업
- **Problem-solving**: 창의적 문제 해결
- **Ownership**: 책임감과 주도성
- **Learning**: 빠른 학습 능력

---

# 🏁 12. 결론

이 문서는 DreamSeedAI MegaCity 운영을 위한 공식 **조직 구조 및 역할 정의 문서**로,
MegaCity를 **Core → Multi-Zone → Global** 규모로 확장하기 위한 인적 기반을 정의합니다.

모든 Division이 협력하여 **MegaCity를 하나의 통합 AI 교육·문화 도시**로 성장시키는 것이 목표입니다.

## 핵심 조직 원칙

1. **Clear Roles & Responsibilities**: 명확한 역할과 책임 정의
2. **Cross-functional Collaboration**: 팀 간 협업 강화
3. **Data-Driven Decision**: 데이터 기반 의사결정
4. **Customer Obsession**: 사용자 중심 사고
5. **Continuous Learning**: 지속적인 학습과 성장
6. **Blameless Culture**: 실패를 학습 기회로 전환
7. **Scale with Structure**: 구조적 확장 (Phase 0 → Phase 4)

---

**문서 완료 - DreamSeedAI MegaCity Team Structure & Roles v1.0**
