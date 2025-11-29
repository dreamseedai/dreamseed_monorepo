# 🗄️ DreamSeedAI MegaCity – Internal Wiki Structure (Notion/Confluence Standard)

## MegaCity 전체 문서를 Wiki 형태로 체계화하는 내부 문서 구조 가이드

**버전:** 1.0  
**작성일:** 2025-11-23  
**작성자:** DreamSeedAI Documentation Team

---

# 📌 0. 개요 (Overview)

본 문서는 DreamSeedAI MegaCity의 방대한 아키텍처·정책·AI·DevOps·운영 문서를  
**Notion 또는 Confluence 스타일의 내부 Wiki 형태로 재구성**하기 위한 공식 구조입니다.

목표는 다음과 같습니다:

```
1) 모든 구성원이 쉽게 찾고 탐색할 수 있는 문서 구조 구축
2) MegaCity의 20+ 핵심 문서를 논리적 카테고리로 분류
3) 팀마다 필요한 문서를 빠르게 접근할 수 있도록 설계
4) 문서 업데이트 흐름과 변경 관리 기준 통합
```

---

# 🗂️ 1. Wiki 전체 구조 (Top-level Navigation)

Wiki 홈에는 아래 8개의 메인 카테고리가 표시됩니다:

```
🏙️ MegaCity Overview
🧭 Architecture
🧠 AI / Models
🛡️ Security & Governance
🛠️ DevOps & Operations
📚 Product & Roadmap
👥 Team & Organization
📘 Documentation Hub
```

---

# 🏙️ 2. MegaCity Overview

**(가장 처음 보는 페이지, 회사와 MegaCity 전체를 안내하는 랜딩 페이지)**

### 포함 문서:

* MegaCity Master Index
* What Is MegaCity?
* 9 Zone Overview
* AI Vision / Product Vision
* 2026–2028 전략 요약
* Leadership Principles 요약

### 페이지 구성:

```
Overview
 ├─ What is MegaCity?
 ├─ Mission & Vision
 ├─ 9 Zones Introduction
 ├─ AI Tutor Overview
 └─ Roadmap Summary Card
```

---

# 🧭 3. Architecture (Core System)

MegaCity 기술 전반을 이해하는 핵심 카테고리.

### 포함 문서:

* Domain Architecture
* Network Architecture
* Tenant Architecture
* MegaCity V2 Architecture
* MegaCity V3 Vision (향후)
* Database Architecture

### 구성 트리:

```
Architecture
 ├─ Domain Architecture
 ├─ Network Architecture
 ├─ Tenant Architecture
 ├─ Data Architecture
 │    └─ Schema / RLS / Partitioning
 ├─ MegaCity V2 Architecture
 └─ MegaCity V3 Architecture (2029~2030)
```

---

# 🧠 4. AI / Model Strategy

AI 전용 카테고리. Zone별 모델 전략과 Multi-modal 구성 포함.

### 포함 문서:

* AI Model Strategy (7B/14B/34B/70B Routing)
* Multi-Modal AI Architecture
* vLLM / Whisper / PoseNet 설정
* AI Safety Layer

### 구성 트리:

```
AI / Models
 ├─ AI Model Strategy
 ├─ LLM Routing Rules
 ├─ Multi-Modal Tutor
 ├─ vLLM Cluster Guide
 ├─ Whisper STT Guide
 ├─ PoseNet / Motion Pipeline
 └─ AI Safety Layer
```

---

# 🛡️ 5. Security & Governance

회사 보안/정책/승인/감사/규제 준수 문서.

### 포함 문서:

* Security Architecture
* Governance Operations Guide
* Compliance Manual (GDPR/PIPA/COPPA/FERPA/CCPA)
* User Safety Guide
* Token Hardening / WAF / PBAC

### 구성 트리:

```
Security & Governance
 ├─ Security Architecture
 ├─ Governance & Operations
 ├─ Compliance (GDPR/PIPA/FERPA/COPPA)
 ├─ User Safety Guide
 ├─ RBAC / PBAC Policies
 ├─ Audit Logging
 └─ Incident Response
```

---

# 🛠️ 6. DevOps & Operations

CI/CD, Monitoring, Incident, Release, Environment 구성 등.

### 포함 문서:

* DevOps Runbook
* Release Management Guide
* Monitoring & Observability Guide
* Cost Optimization (FinOps)
* Reverse Proxy / Cloudflare / DNS
* Infrastructure Deployment Scripts

### 구성 트리:

```
DevOps & Operations
 ├─ DevOps Runbook
 ├─ Release Management
 ├─ Monitoring & Observability
 ├─ FinOps (Cost Optimization)
 ├─ Cloudflare / DNS Setup
 ├─ Reverse Proxy (Traefik/Nginx)
 ├─ Environment Setup
 └─ Backup & DR Guide
```

---

# 📚 7. Product & Roadmap

PM / Design / Growth 팀이 활용하는 핵심 영역.

### 포함 문서:

* Product Roadmap 2025–2027
* Growth Engine & GTM Plan
* Zone Activation Plan
* UX Guidelines (향후)

### 구성 트리:

```
Product & Roadmap
 ├─ Product Roadmap
 ├─ Growth Engine / GTM
 ├─ Zone Activation Strategy
 ├─ Design System (Future)
 └─ Education Pedagogy Docs
```

---

# 👥 8. Team & Organization

회사 문화·규정·HR 문서 중심.

### 포함 문서:

* Organization Handbook
* Team Structure & Roles
* Hiring Guide / JD Templates
* Performance Review Guide
* Onboarding Pack

### 구성 트리:

```
Team & Organization
 ├─ Organization Handbook
 ├─ Team Structure & Roles
 ├─ Hiring & JD
 ├─ Performance Framework
 └─ Onboarding Pack
```

---

# 📘 9. Documentation Hub (문서의 문서)

Documentation Index 및 모든 문서 링크.

### 포함 문서:

* Documentation Index
* 문서 관리 규칙 (Versioning / Change Log)
* Naming Convention
* Templates (PRD/ADR/RFC)

### 구성 트리:

```
Documentation Hub
 ├─ Documentation Index
 ├─ Change Management
 ├─ Naming Convention
 ├─ Templates
 │    ├─ PRD Template
 │    ├─ ADR Template
 │    └─ RFC Template
 └─ Versioning Guide
```

---

# 📎 10. Wiki Naming & URL Rules

명확한 문서 주소/이름을 위해 다음 규칙을 사용합니다.

## 10.1 Naming Rules

```
MEGACITY_<CATEGORY>_<NAME>
ORG_<TEAM>_<NAME>
AI_<MODELNAME>_<GUIDE>
```

## 10.2 URL Rules (Notion/Confluence 기준)

```
/wiki/architecture/network
/wiki/security/governance
/wiki/ai/model-strategy
/wiki/devops/runbook
/wiki/product/roadmap
/wiki/team/handbook
/wiki/docs/index
```

---

# 🔄 11. Document Versioning Rules

```
vMAJOR.MINOR.PATCH
예: v1.2.0
```

* 모든 문서는 Version + Last Updated 포함
* 변경 발생 시 Change Log 기록

---

# 🏁 12. 결론

이 Internal Wiki Structure는 DreamSeedAI MegaCity의 모든 문서를  
**팀 전체가 이해·검색·공유할 수 있는 체계적인 내부 백과사전**으로 만드는 기준입니다.

이 구조를 기반으로 실제 Notion/Confluence Wiki 페이지를 만들면  
DreamSeedAI의 운영/아키텍처/AI/보안 문서들이 기업 수준으로 관리될 수 있습니다.
