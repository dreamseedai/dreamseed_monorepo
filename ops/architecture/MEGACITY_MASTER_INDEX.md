# 🏙️ DreamSeedAI MegaCity – Master Index

## 전체 아키텍처 · 도메인 · 네트워크 · 테넌트 · SSO · 서비스 구조 안내서

**버전:** 1.1  
**작성일:** 2025-11-20  
**작성자:** DreamSeedAI Architecture & Infrastructure Team

---

# 📚 0. 이 문서의 역할

DreamSeedAI MegaCity의 모든 핵심 아키텍처 문서들을 **한 눈에 조망하고 연결하는 마스터 목차(Top-Level Index)** 역할을 합니다.

이 문서는 다음을 명확히 정의합니다:

* 전체 MegaCity 문서의 구조와 카테고리
* 어떤 문서를 어떤 순서로 읽어야 하는지
* MegaCity 착공 타이밍(Construction Timing) 및 전체 로드맵
* 각 문서가 담당하는 역할

DreamSeedAI MegaCity는 총 **9개 Zone(도메인)으로 구성된 거대 교육·AI 도시**이기 때문에, 이를 체계적으로 이해하기 위한 상위 레이어 문서가 필수적입니다. 이 문서가 바로 그 "도시 지도(Master Index)"입니다.

---

# 🧭 1. 추천 읽기 순서 (Top-down Architecture Overview)

MegaCity를 처음 접하는 팀원·협력사·외주개발사는 다음 순서대로 문서를 읽으면 전체 구조를 단 1~2시간 내에 이해할 수 있습니다.

## 1) 도시(Zone) 개념 · 도메인 구조

* **`MEGACITY_DOMAIN_ARCHITECTURE.md`**

## 2) 전체 네트워크·인프라 구조 (도로/철도/전력망)

* **`MEGACITY_NETWORK_ARCHITECTURE.md`**

## 3) 테넌트(학교/기관) 구조 · 데이터 격리

* **`MEGACITY_TENANT_ARCHITECTURE.md`**

## 4) 인증/SSO/정책 · 시민 ID 구조

* **`MEGACITY_AUTH_SSO_ARCHITECTURE.md`**

## 5) 엔진/서비스 · AI/Worker/Backend 구조

* **`MEGACITY_SERVICE_TOPOLOGY.md`**

## 6) K-Zone 상세 구성

* `K_ZONE_MASTERPLAN.md`
* `K_ZONE_URL_ARCHITECTURE.md`
* `K_ZONE_AI_MODULES.md`
* `K_ZONE_DNS_SETUP.md`

---

# 🗺️ 2. MegaCity 전체 Zone 구조 (Top Layer)

DreamSeedAI MegaCity는 9개의 독립된 교육·AI 도메인(Zone)으로 구성됩니다.

| Zone | Domain            | 역할                        |
| ---- | ----------------- | ------------------------- |
| Z1   | UnivPrepAI.com    | 대학 입시 특화 구역               |
| Z2   | CollegePrepAI.com | 전문대/폴리텍/편입                |
| Z3   | SkillPrepAI.com   | 직업·기술·취업 준비               |
| Z4   | MediPrepAI.com    | 간호·의료 계열                  |
| Z5   | MajorPrepAI.com   | 전공/대학원/전문직                |
| Z6   | My-Ktube.com      | K-Culture 교육·콘텐츠          |
| Z7   | My-Ktube.ai       | K-Culture AI 분석/생성        |
| Z8   | mpcstudy.com      | 공공 문제은행 서비스               |
| Z9   | DreamSeedAI.com   | 중앙 관리 도시(Core City + SSO) |

---

# 🌐 3. 네트워크 / 인프라 레이어

* **`MEGACITY_NETWORK_ARCHITECTURE.md`**

  * Cloudflare Edge (DNS · CDN · WAF · SSL)
  * Reverse Proxy (Nginx / Traefik)
  * Next.js Frontend Cluster
  * FastAPI Backend Cluster
  * Redis / PostgreSQL / GPU Cluster / Object Storage
  * Monitoring Stack

---

# 🏛️ 4. 테넌트/조직/구역 아키텍처

* **`MEGACITY_TENANT_ARCHITECTURE.md`**

  * org_id / zone_id 기반 Multi-Tenant
  * PostgreSQL RLS
  * Redis Key Namespace 설계
  * Zone ↔ Tenant ↔ User 계층 구조

---

# 🧑‍💻 5. 인증 / ID / SSO 레이어

* **`MEGACITY_AUTH_SSO_ARCHITECTURE.md`**

  * DreamSeed Global ID
  * Multi-domain Cookie & SSO
  * OIDC Central Auth Server
  * Parent–Student linking
  * RBAC + PBAC 정책
  * Token Lifecycle (Rotation)

---

# ⚙️ 6. 서비스 / 엔진 / AI 톱올로지

* **`MEGACITY_SERVICE_TOPOLOGY.md`**

  * FastAPI Services
  * K-Zone AI (Whisper, PoseNet, vLLM)
  * Worker / Queue / Eventing
  * Multi-Region 확장 계획

---

# 🎵 7. K-Zone 문서(문화·AI 특구)

* `K_ZONE_MASTERPLAN.md`
* `K_ZONE_URL_ARCHITECTURE.md`
* `K_ZONE_AI_MODULES.md`
* `K_ZONE_DNS_SETUP.md`

---

# 🚧 8. MegaCity 착공 타이밍 (Construction Timing)

**🔥 매우 중요한 업데이트 (2025-11 반영)**

DreamSeedAI MegaCity는 "모든 Zone을 한 번에" 개장하는 모델이 아닙니다.
**Core City(DreamSeedAI.com)**가 안정적으로 활성화되면, 그 성장에 따라 자연스럽게 **Zone(구역)들이 줄줄이 확장되는 도시 성장 모델**입니다.

아래는 MegaCity 착공의 공식 기준입니다.

---

## 🚀 8.1 MegaCity 착공 기준 (Start Conditions)

다음 조건 중 **3개 이상 충족되면 착공 시작**이 가장 효율적입니다:

### ✔ 조건 1 — DAU 300~500명 (또는 사용자 1,000~5,000명)

### ✔ 조건 2 — Teacher/Parent Dashboard MVP 안정화

### ✔ 조건 3 — SSO(DreamSeed ID) 완성

### ✔ 조건 4 — K-Zone AI 모듈 1~2개 출시 (Voice Tutor, Dance Lab 등)

### ✔ 조건 5 — GPU Inference Pipeline(vLLM/Whisper) 안정화

**→ 결론: Phase 1 후반 ~ Phase 2 초입 = MegaCity 착공 시점**

---

# 🏗️ 8.2 MegaCity Construction Roadmap

MegaCity는 실제 도시처럼 "구역별 단계적 개발" 방식으로 확장됩니다.

```
Phase 0 — 기반시설 구축 (완료)
  - 인증/보안/백업/모니터링 완료
  - CI/CD · Reverse Proxy · DNS · GPU 등 기초 공사 100%

Phase 1 — Core City 출범 (DreamSeedAI.com)
  - UnivPrepAI MVP 오픈
  - AI Tutor v1
  - Teacher/Parent Dashboard
  - 사용자 기반 1,000명 확보

⭐ MegaCity 착공 시점 (Phase 1 후반 → Phase 2 초입)
  - CollegePrepAI.com 오픈
  - SkillPrepAI.com 오픈
  - My-Ktube.com(K-Zone Lite) 오픈

Phase 3 — MegaCity 70% 완성
  - MediPrepAI / MajorPrepAI 구역 개장
  - K-Zone 전체 기능 활성화
  - GPU Cluster 2~3대로 확장
  - 사용자 100,000 규모

Phase 4 — MegaCity Full Launch
  - 전체 9개 구역 운영
  - Multi-region 확장 (KR → US/EU)
  - 1,000,000명 도시 운영 가능
```

---

# 🌆 9. MegaCity 성장 지도 (Growth Flywheel)

**mpcstudy.com → DreamSeedAI Core → MegaCity 확장** 구조는 다음과 같이 자연스럽게 구현됩니다.

```
mpcstudy.com (600~800명/일)
   ↓ 자연 유입 → DreamSeedAI.com (AI Tutor)
   ↓ SSO 로그인 → Dashboard
   ↓ 필요에 따라 Zone 탐색
   ↓ UnivPrep / SkillPrep / K-Zone 등에서 전문학습
   ↓ MegaCity 전체 활성화
```

이 구조는 DreamSeedAI 플랫폼의 가장 큰 강점이며, MegaCity를 지속적으로 성장시키는 **유기적 Growth Engine**입니다.

---

# 📂 10. 문서 디렉토리 구조 (권장)

```text
/docs/megacity/
 ├─ MEGACITY_MASTER_INDEX.md
 ├─ MEGACITY_DOMAIN_ARCHITECTURE.md
 ├─ MEGACITY_NETWORK_ARCHITECTURE.md
 ├─ MEGACITY_TENANT_ARCHITECTURE.md
 ├─ MEGACITY_AUTH_SSO_ARCHITECTURE.md
 ├─ MEGACITY_SERVICE_TOPOLOGY.md
 ├─ K_ZONE_MASTERPLAN.md
 ├─ K_ZONE_URL_ARCHITECTURE.md
 ├─ K_ZONE_AI_MODULES.md
 └─ K_ZONE_DNS_SETUP.md
```

---

# ✅ 11. 이 인덱스를 어떻게 활용하면 좋은가?

## 새 팀원에게:

→ **"이 MASTER_INDEX부터 읽고, 링크된 문서들을 순서대로 보면 DreamSeedAI 전체 도시 설계를 이해할 수 있다."**

## 외주/협력사에게:

→ 도메인/네트워크/인증/서비스 설계를 하나의 패키지로 설명할 때 이 문서 하나로 전체 구조 공유.

## 나중에 문서가 더 많아져도:

→ 이 인덱스에 새 문서를 카테고리별로 추가만 해주면 언제나 한 곳에서 전체를 조망할 수 있습니다.

---

**문서 완료 - DreamSeedAI MegaCity Master Index v1.1**
