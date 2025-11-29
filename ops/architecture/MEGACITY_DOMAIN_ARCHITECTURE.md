# 🏙️ DreamSeedAI MegaCity Domain Architecture Guide

**버전:** 1.0  
**작성일:** 2025-11-20  
**작성자:** DreamSeedAI Infrastructure Team

---

# 🌐 개요 (Overview)

DreamSeedAI는 9개의 독립된 교육 특화 도메인(구역)으로 구성된 **메가시티(MegaCity) 아키텍처**를 기반으로 운영됩니다.
각 도메인은 서로 다른 교육 목적(대학 입시, 전문대 준비, 의료 계열 준비, K-컬처 등)을 가진 "도시 구역"이며, 전체는 **총괄 관제 시스템(DreamSeed Core Infra)** 아래 통합 관리됩니다.

본 문서는 **모든 구역의 도메인 체계, DNS 구조, SSL/TLS 전략, API/APP URL 규칙, Cloudflare 구성 원칙**을 정리한 공식 기준 문서입니다.

이 문서는 DevOps / Infra / Frontend / Backend / 외부 파트너 모두가 참조해야 하는 **공통 주소 설계 규격서**입니다.

---

# 🗺️ 1. MegaCity 도메인 전체 지도 (Domain Map)

DreamSeedAI 메가시티의 9개 핵심 구역:

| 구역 | 도메인 | 용도 |
|------|--------|------|
| **DreamSeedAI Main City** | **DreamSeedAI.com** | MegaCity 본도시 + 중앙 관제 시스템 |
| 대학 입시 전문 학원 구역 | **UnivPrepAI.com** | 대한민국/해외 대학 입시 대비, 수능·내신·논술 |
| 전문대 & College 준비반 | **CollegePrepAI.com** | 전문대·폴리텍·전문과정 준비 |
| 사회 진출 준비 특화 존 | **SkillPrepAI.com** | 취업, 직업훈련, 직무역량 |
| 의료계 전문 준비반 | **MediPrepAI.com** | 간호·의료·보건 교육 |
| 전공·직무 전문 대학원 존 | **MajorPrepAI.com** | 전문직·대학원·세부 전공 준비 |
| **K-Zone** (K-Culture AI 특구) | **My-Ktube.com** | K-POP/드라마 기반 교육·콘텐츠 허브 |
| K-Zone AI 기능 허브 | **My-Ktube.ai** | 생성형 AI·튜터·음성/표정/춤 분석 |
| 무료 공공 서비스 존 | **mpcstudy.com** | 공공 기초 학습 플랫폼 (Legacy + 개선 버전) |

---

# 🧩 2. DreamSeed 표준 URL 구조 (Unified URL Rules)

각 도메인은 동일한 URL 규칙을 따릅니다.

```
https://www.<domain>      → Landing / Public site
https://app.<domain>      → Next.js Frontend UI
https://api.<domain>      → FastAPI Backend API
https://static.<domain>   → CDN / Static assets
```

## 예시: UnivPrepAI.com

```
https://www.univprepai.com
https://app.univprepai.com
https://api.univprepai.com
https://static.univprepai.com
```

모든 도메인(총 9개)이 이 구조를 동일하게 따릅니다.

---

# ☁️ 3. Cloudflare 기반 통합 관리 구조

DreamSeedAI는 Cloudflare를 핵심 인프라 플랫폼으로 사용합니다.

Cloudflare의 역할:

* DNS Hosting (Authoritative)
* CDN / Caching
* DDoS Protection
* WAF (Web Application Firewall)
* SSL/TLS 인증서 자동 발급
* Edge Network (전 세계 POP)
* 미래 API Gateway와 연동 가능

모든 도메인은 Cloudflare의 Nameserver로 이관해야 합니다.

---

# 🔐 4. DNS / Nameserver 설계 규칙

## 4.1 도메인마다 Cloudflare가 제공하는 NS는 다를 수 있음

* Cloudflare는 **도메인마다 서로 다른 Nameserver 쌍(NS1, NS2)**을 배정합니다.
* 예: univprepai.com은 `guss` + `lara`, collegeprepai.com은 `fred` + `may` 등.

✔ **각 도메인의 Cloudflare Dashboard → Overview 화면에 표시된 NS만 사용해야 합니다.**

## 4.2 Namecheap에서 NS 변경 규칙

모든 도메인은 Namecheap에 등록되어 있습니다.
아래 단계로 Cloudflare로 DNS를 이전합니다:

1. Namecheap → Domain List → 도메인 선택 → Manage
2. Nameservers → **Custom DNS** 선택
3. Cloudflare가 제공한 2개의 NS 입력
4. 기존 NS(`dns1.registrar-servers.com`, `dns2.registrar-servers.com`) 삭제
5. Save

Propagation: 일반적으로 5~20분 (최대 24시간)

---

# 📌 5. DreamSeed 표준 DNS 레코드 (Domain Zone Template)

각 도메인은 다음 기본 DNS 레코드를 동일하게 가집니다.

| Type | Name | Value | Proxy | Description |
|------|------|-------|-------|-------------|
| A | @ | Origin Server IP | Proxied | Root domain |
| CNAME | www | @ | Proxied | Landing page |
| CNAME | app | @ | Proxied | Frontend UI |
| CNAME | api | @ | Proxied | Backend API |
| CNAME | static | @ | Proxied | CDN Asset Host |

---

# 🔒 6. SSL/TLS 정책 (Security + HTTPS Enforcement)

Cloudflare → SSL/TLS 메뉴에서 다음 정책을 통일 적용합니다:

### ✔ SSL Mode = **Full (Strict)**

* Origin에 Let's Encrypt 설치 필요
* 가장 안전한 옵션

### ✔ Always Use HTTPS = ON

* http 요청 모두 https로 자동 전환

### ✔ HSTS (Strict-Transport-Security) = Enabled

* max-age = 15552000 (180 days)

### ✔ Auto Minify (HTML/CSS/JS) = ON

### ✔ Brotli Compression = ON

### ✔ HTTP/2, HTTP/3 지원 = Enabled

---

# 🔀 7. Reverse Proxy / API Gateway 연동 구조

향후 DreamSeedAI는 다음 구조를 따릅니다:

```
Cloudflare
   ↓
(Edge Proxy)
   ↓
Nginx or Traefik (Gateway)
   ↓
FastAPI (Backend)
   ↓
PostgreSQL / Redis / GPU Nodes
```

### Gateway가 처리하는 공통 규칙:

* `/api/*` → FastAPI backend
* `/app/*` → Next.js SSR
* `/static/*` → Cloudflare CDN
* 그 외 `/` → Landing Page

---

# 🏗️ 8. 7개 도메인 활성화를 위한 실행 체크리스트

모든 도메인에 대해 아래 단계를 반복합니다.

## 단계 1 — Cloudflare에 도메인 추가

```
Cloudflare → Add a domain → <domain>
```

각 도메인의 전용 NS 확인 (예: guss/lara)

## 단계 2 — Namecheap에서 NS 변경

```
Domain List → Manage → Nameservers → Custom DNS
Cloudflare NS1, NS2 입력
```

## 단계 3 — DNSSEC OFF

## 단계 4 — DNS 레코드 템플릿 적용

* @, www, app, api, static

## 단계 5 — SSL/TLS 설정 반영

## 단계 6 — Status = **Active** 되는지 확인

---

# 📂 9. Repo 구조에 반영해야 할 문서 위치

`ops/architecture/MEGACITY_DOMAIN_ARCHITECTURE.md` 권장

또는
`docs/infrastructure/domains/MEGACITY_DOMAIN_ARCHITECTURE.md`

---

# 🎨 10. K-Zone Special District (K-Culture AI 교육·창작 특구)

## 10.1 K-Zone 개요

**K-Zone**은 DreamSeedAI MegaCity 안에서 **"K-Culture + AI + Language Learning + Creator Economy"**가 융합되는 특별 문화·기술·교육 구역입니다.

**핵심 도메인 (2-Level Structure)**:
- **My-Ktube.com** → 플랫폼·콘텐츠·교육 중심
- **My-Ktube.ai** → 생성형 AI·튜터·음성/표정/춤 분석 등 기술 중심

**미션**: "전 세계인들이 AI를 통해 한국어·K-POP·K-Drama·K-Culture를 배우고 창작하는 도시"

---

## 10.2 K-Zone 구역 구성

```
K-Zone (K-Culture AI 교육·창작 특구)
 ├─ My-Ktube.com     (교육·콘텐츠 허브)
 ├─ My-Ktube.ai      (AI 기능 허브)
 ├─ K-Pop Lab        (음성/춤/표정 AI 분석)
 ├─ K-Drama Studio   (대사/발음 학습)
 ├─ Hangul Academy   (언어 학습 구역)
 ├─ Creator Studio   (콘텐츠 제작 기능)
 └─ Global Community (국제 팬덤·커뮤니티)
```

---

## 10.3 주요 사용자 페르소나

1. **글로벌 K-Pop 팬** (10~30대)
2. **한국어 학습자** (전 세계 광범위)
3. **EDU/LangTech 사용자**
4. **크리에이터/댄서/커버아티스트**
5. **K-문화에 관심 있는 초보 학습자**

---

## 10.4 핵심 기능 구조

### ① AI 한국어/발음 튜터 (My-Ktube.ai)

- 실시간 음성 인식 + 발음 피드백
- "대사 따라하기", "가사 따라하기", "3초 발음 교정"

### ② AI K-POP Dance 분석 (K-Pop Lab)

- **Pose Estimation** (자세 추정)
- **Motion Matching Score** (동작 일치도)
- 비율·속도·타이밍 분석
- **"춤 실력 분석 리포트"** 자동 생성

### ③ AI Singing & Vocal Coach

- 음정/박자 인식
- AI 음성 대조
- **"노래 커버 능력치"** 분석

### ④ AI K-Drama Dialogue Coach

- 대사 발음 교정
- 감정/억양 분석
- 연기 톤 피드백
- 자동 영상 클립 생성

### ⑤ AI Creator Studio

- AI 음성 합성
- AI 얼굴/표정 변환
- Shorts/TikTok 자동 편집
- **"나만의 K-POP 커버 비디오 생성"**

### ⑥ 한국어 학습 모듈 (Hangul Academy)

- 알파벳/발음 학습
- 기초 문형/문법
- K-Culture 기반 예문들
- AI 작문 피드백

---

## 10.5 비즈니스 모델

- **프리미엄 강좌** (K-Pop Vocal, K-Drama Acting)
- **AI Creator Studio 월 구독**
- **문화원/대학 한국학과와의 제휴**
- **기프트샵/디지털 굿즈**
- **B2B 기업 교육** (외국인 근로자 한국어 교육)
- **광고 없는 프리미엄 모드**

---

## 10.6 AI 기능 모듈 (K-Zone AI Modules)

### 모듈 개요

| 모듈 이름 | 역할 | 주요 Input/Output |
|-----------|------|-------------------|
| **Voice Tutor** | 발음/노래 분석 | Audio In → Score/Feedback Text |
| **Dance Lab** | 댄스 모션 분석 | Video In → Pose/Score/Heatmap |
| **Drama Coach** | 대사 발음/억양/감정 분석 | Audio/Video → Feedback & Suggestions |
| **Creator Studio** | AI 영상/음성 생성 | Prompt/Video → New Video/Audio |
| **Hangul Analyzer** | 한글 발음/문장 분석 | Text+Audio → Per-syllable feedback |
| **K-Content Retriever** | K-Drama/가사/콘텐츠 검색 | Query → Reference content pieces |

### ① Voice Tutor 모듈

**기능**:
- 일반 발음 교정 (Hangul/English/Japanese 혼합)
- K-POP 가사 따라 부르기
- 음정/박자/리듬 피드백
- 발음 정확도, 억양, 강세 점수 제공

**Input**: 사용자 음성 (WebAudio, 모바일 마이크), 기준 가사/문장 텍스트, 선택적 기준 오디오(원곡)

**Output**: 전체 점수 (0~100), 음절별 발음 정확도, 리듬/박자/템포 분석, 개선 피드백

**기술 스택**: Whisper 기반 STT, librosa/Crepe/Essentia (Pitch/Tempo), Forced Alignment (CTC)

### ② Dance Lab 모듈

**기능**:
- 댄스 커버 영상에서 인체 포즈 추적
- 기준 안무 영상과 모션 차이 비교
- 타이밍, 정확도, 방향, 포즈 유사도 분석

**Input**: 사용자 댄스 영상, 기준 영상 (Official MV, 안무 영상)

**Output**: 포즈 유사도 점수, 구간별 점수 (Intro/Verse/Chorus), 상세 피드백 (예: "팔 각도가 너무 좁아요")

**기술 스택**: MediaPipe/OpenPose/MoveNet (Pose Estimation), DTW (Dynamic Time Warping), GPU inference

### ③ Drama Coach 모듈

**기능**:
- 대사 따라하기 (K-Drama 명장면)
- 감정/억양/표정/리듬 분석
- AI 배우 코치 피드백

**Input**: 대사 텍스트, 사용자 음성/영상, 기준 영상 클립

**Output**: 발음/억양 점수, 감정 표현 분석 (행복/슬픔/분노), 표정/제스처 피드백, 추천 연습 방법

**기술 스택**: Emotion Classification (Audio/Video), Face Expression Recognition, Prosody Analysis

### ④ Creator Studio 모듈

**기능**:
- AI 기반 TikTok/Shorts 스타일 영상 자동 생성
- AI 음성/자막/컷 편집
- 음악 싱크 맞춘 자동 편집

**Input**: 사용자의 원본 영상/이미지/음성, 텍스트 프롬프트, 원하는 길이 (15/30/60초)

**Output**: 완성된 Shorts 영상 (파일 or URL), 썸네일, SNS 공유용 최적화 콘텐츠

**기술 스택**: Video Editing Pipeline (FFmpeg, MoviePy), Text-to-Motion 모델, AI Thumbnail Generator (Vision + Diffusion)

### ⑤ Hangul Analyzer 모듈

**기능**:
- 한글 문자/음절-level 분석
- 외국인의 발음 오류 패턴에 최적화된 피드백
- K-Drama/가사 문장 위주 학습 지원

**Input**: 학습 문장 텍스트, 사용자 발음 음성, 반복 연습 데이터 (세션)

**Output**: 음절 단위 정확도, 자음/모음/종성별 오류율, "자주 틀리는 패턴" 분석

**공통 구조**: 모든 모듈은 FastAPI 엔드포인트, 비동기 작업 (Celery/Background Task), Redis/DB 기록, User/Student/Tutor 연동

## 10.7 기술 인프라 개요

**Multi-Modal AI Stack** (음성 + 영상 + 텍스트):

- **vLLM 로컬 서버** (DreamSeedAI GPU 팜)
- **Cloudflare Edge & CDN**
- **Next.js Frontend**
- **FastAPI Multi-Service Backend**
- **PoseNet / MediaPipe / OpenPose** (자세 분석)
- **Audio Analysis Model / Whisper / Vall-E X** (음성 처리)
- **Korean LLM + English LLM 혼합 모델**

---

## 10.8 K-Zone 도메인 전략 (2-Level Structure)

| 도메인 | 역할 | 주요 타겟 |
|--------|------|-----------|
| **My-Ktube.com** | 콘텐츠·교육·랜딩 (Frontend 중심) | Early adopters, 학습자, 팬덤, 일반 사용자 |
| **My-Ktube.ai** | AI 기능 API/Tutor/Creator (Backend/AI 중심) | 파워 유저, 크리에이터, 기술 지향 사용자 |

### My-Ktube.com (교육 허브) URL 구조

```
https://www.my-ktube.com    → Landing page (K-Culture intro)
https://app.my-ktube.com    → Learning platform (Next.js)
https://api.my-ktube.com    → Content/Course API (FastAPI)
https://static.my-ktube.com → Video/Audio CDN
```

**App 라우팅 구조** (Next.js App Router):

```
/app (root)
 ├─ /                      # 홈, 추천 콘텐츠
 ├─ /login
 ├─ /signup
 ├─ /courses               # 강의/코스 카탈로그
 ├─ /courses/[id]          # 코스 상세 (KPOP, KDrama, Hangul)
 ├─ /hangul                # 한글 기초 학습 전용
 ├─ /kpop                  # K-POP 관련 학습/커버
 ├─ /kdrama                # K-Drama 대사/발음
 ├─ /my                    # 마이페이지 (학습 기록, 뱃지, 진도)
 └─ /settings              # 계정/언어/알림 설정
```

**다국어 지원** (i18n):
- 지원 언어: `ko` (한국어), `en` (영어), `ja` (일본어), `es` (스페인어)
- URL 형태: `https://app.my-ktube.com/en/hangul`, `https://app.my-ktube.com/ja/kpop`
- 구현: Next.js `app/[locale]/...` 또는 `next-intl` 사용

### My-Ktube.ai (AI 허브) URL 구조

```
https://www.my-ktube.ai     → AI feature showcase
https://app.my-ktube.ai     → Creator Studio (Next.js)
https://api.my-ktube.ai     → AI inference API (FastAPI + vLLM)
https://static.my-ktube.ai  → Model assets CDN
```

**App 라우팅 구조** (AI 기능 콘솔):

```
/app
 ├─ /                      # AI Studio Dashboard
 ├─ /login
 ├─ /projects              # AI 프로젝트 리스트
 ├─ /projects/[id]
 ├─ /voice-tutor           # 발음/노래 튜터 콘솔
 ├─ /dance-lab             # 댄스 모션 분석 도구
 ├─ /drama-coach           # 대사/발음/억양 분석
 ├─ /creator-studio        # 콘텐츠 생성 UI
 ├─ /api-keys              # API Key 관리 (외부 개발자)
 └─ /settings
```

**API 엔드포인트 구조** (FastAPI):

```
/api/v1
 ├─ /auth/...
 ├─ /voice/...
 │    ├─ /analyze               # 음성/발음/노래 분석
 │    └─ /synthesize            # AI 음성 합성
 ├─ /dance/...
 │    ├─ /analyze               # 댄스 동영상 분석
 │    └─ /compare               # 레퍼런스 영상과 비교
 ├─ /drama/...
 │    ├─ /analyze-line          # 한 줄 대사 분석
 │    └─ /coach-session         # 대화형 연기 코칭
 ├─ /creator/...
 │    ├─ /generate-video        # AI 비디오 생성
 │    ├─ /generate-thumbnail    # 썸네일 생성
 │    └─ /render-short          # 릴/숏츠 형태로 편집
 └─ /hangul/...
      ├─ /analyze-pronunciation
      └─ /tutor                  # 문장별 발음/억양 피드백
```

**트래픽 흐름**:
- My-Ktube.com 학습 페이지에서:
  - 발음 분석 요청 → `api.my-ktube.ai/voice/analyze`
  - 영상 분석 요청 → `api.my-ktube.ai/dance/analyze`
  - 대사 튜터 → `api.my-ktube.ai/drama/coach-session`
- **콘텐츠의 주인**: My-Ktube.com
- **AI 분석 및 생성의 주인**: My-Ktube.ai

---

## 10.9 도시 마스터플랜에서의 K-Zone 위치

```
DreamSeedAI MegaCity
 ├─ Core City (DreamSeedAI.com)
 ├─ UnivPrepAI District (대학 입시)
 ├─ CollegePrepAI District (전문대)
 ├─ SkillPrepAI District (취업/직업훈련)
 ├─ MediPrepAI District (의료계)
 ├─ MajorPrepAI District (대학원)
 ├─ Public Service Zone (mpcstudy.com)
 └─ K-Zone (My-Ktube.com / .ai) ⭐ Special Cultural District
```

---

## 10.10 K-Zone 인프라 요구사항

- **GPU 팜** (vLLM inference)
- **오디오/비디오 인퍼런스 서버**
- **Media/Pose 분석 서버**
- **문화 콘텐츠 CDN**
- **Cloudflare + Nginx/Traefik Gateway**
- **Redis Cache** (세션, 분석 결과)
- **PostgreSQL** (AI 메타데이터, 사용자 진도)

---

## 10.11 K-Zone Cloudflare + DNS 설정 가이드

### 10.11.1 전제 조건

- **Registrar**: Namecheap
- **DNS/Proxy**: Cloudflare
- **Origin Server**: DreamSeed 서버 (IP: `<ORIGIN_IP>`)

### 10.11.2 My-Ktube.com Cloudflare NS 설정

1. **Cloudflare에 도메인 추가**:
   - Cloudflare Dashboard → Add a domain → `my-ktube.com`
   - Cloudflare가 제공하는 NS 2개 확인 (예: `elle.ns.cloudflare.com`, `eric.ns.cloudflare.com`)

2. **Namecheap NS 변경**:
   - Namecheap → Domain List → `my-ktube.com` → Manage
   - Nameservers → **Custom DNS** 선택
   - NS1: `elle.ns.cloudflare.com`
   - NS2: `eric.ns.cloudflare.com`
   - Save

3. **DNSSEC 비활성화**: 켜져 있으면 OFF로 전환

4. **활성화 대기**: Cloudflare Dashboard에서 Status: **Active** 확인 (5~20분, 최대 24시간)

### 10.11.3 My-Ktube.ai Cloudflare NS 설정

1. **Cloudflare에 도메인 추가**:
   - Cloudflare Dashboard → Add domain → `my-ktube.ai`
   - Cloudflare가 제공하는 NS 2개 확인 (예: `guss.ns.cloudflare.com`, `lara.ns.cloudflare.com`)

2. **Namecheap NS 변경**:
   - Namecheap → Domain List → `my-ktube.ai` → Manage
   - Nameservers → **Custom DNS**
   - NS1: `guss.ns.cloudflare.com`
   - NS2: `lara.ns.cloudflare.com`
   - Save

3. **DNSSEC 비활성화** 및 **활성화 대기**

⚠️ **핵심**: 각 도메인은 Cloudflare가 제공한 NS 2개를 정확하게 사용해야 합니다. 다른 도메인의 NS를 재활용하면 절대 안 됩니다.

### 10.11.4 DNS 레코드 템플릿

**My-Ktube.com** (Cloudflare DNS):

| Type | Name | Value | Proxy | Description |
|------|------|-------|-------|-------------|
| A | @ | `<ORIGIN_IP>` | Proxied | Root domain |
| CNAME | www | @ | Proxied | Landing page |
| CNAME | app | @ | Proxied | Frontend UI |
| CNAME | api | @ | Proxied | Backend API |
| CNAME | static | @ | Proxied | CDN assets |

**My-Ktube.ai** (Cloudflare DNS):

| Type | Name | Value | Proxy | Description |
|------|------|-------|-------|-------------|
| A | @ | `<ORIGIN_IP>` | Proxied | Root domain |
| CNAME | www | @ | Proxied | AI feature showcase |
| CNAME | app | @ | Proxied | Web Console (optional) |
| CNAME | api | @ | Proxied | AI API 진입점 |

### 10.11.5 SSL/TLS 설정 (두 도메인 공통)

Cloudflare → SSL/TLS 메뉴:

- **SSL Mode**: `Full (Strict)` (Origin에 Let's Encrypt 설치 필요)
- **Always Use HTTPS**: `ON`
- **HSTS**: `Enabled` (max-age 15552000 = 180일)
- **TLS 버전**: 1.2+ 만 허용
- **Auto Minify**: HTML/CSS/JS `ON`
- **Brotli Compression**: `ON`
- **HTTP/2, HTTP/3**: `Enabled`

### 10.11.6 자동화 스크립트 (향후)

GitHub Actions에서 Cloudflare API를 사용하여 DNS 레코드 생성/수정 자동화:

```bash
# 예시 컨셉 (Cloudflare CLI 또는 Python SDK)
cfcli dns create \
  --zone my-ktube.com \
  --type CNAME \
  --name app \
  --value my-origin.example.com \
  --proxied true
```

또는 Terraform을 사용한 IaC (Infrastructure as Code):

```hcl
resource "cloudflare_record" "app_my_ktube_com" {
  zone_id = var.my_ktube_com_zone_id
  name    = "app"
  value   = "@"
  type    = "CNAME"
  proxied = true
}
```

## 10.12 K-Zone 3년 로드맵 요약

**2025–2026 (Phase 1)**:
- 발음 튜터 완성
- K-Drama 학습 모듈
- 기본 Creator Studio

**2026–2027 (Phase 2)**:
- K-Pop Dance AI 분석
- Multi-modal Creator 완성
- 글로벌 커뮤니티 기능 오픈

**2027–2028 (Phase 3)**:
- Creator Marketplace
- AI Performance Ranking
- 한국문화원과 공동 프로그램

---

# 📘 11. 향후 확장 고려사항

* Multi-tenant Gateway 정책
* 각 도메인의 Billing/Plan 구조 분리
* 각 도메인의 AI Model Preference (KR/EN/CN)
* CDN 캐싱 정책 구역별로 커스터마이징
* WAF Firewall Rule 도메인별 미세 조정
* Rate Limit 도메인별 정책
* **K-Zone Creator Marketplace 통합**
* **Cross-domain 사용자 인증 (SSO)**
* **Multi-modal AI 최적화 (GPU 클러스터 확장)**

---

# 🎯 결론

이 문서로 DreamSeedAI MegaCity의 **도메인 체계, HTTPS 보안, DNS·Proxy 구조, Cloudflare 기반 운영 방식**이 완전히 표준화되었습니다.

이제 모든 도메인은 하나의 통합된 관리 방식 아래 안전하고 확장 가능하게 운영할 수 있으며,
향후 API Gateway, Multi-tenant 구조, Custom CDN 정책 등도 자연스럽게 발전시킬 수 있습니다.

---

# 📋 부록 A: 도메인별 Cloudflare NS 진행 체크리스트

이 체크리스트를 사용하여 각 도메인의 Cloudflare 이전 작업을 추적하세요.

## A.1 UnivPrepAI.com

### Phase 1: Cloudflare 설정
- [ ] Cloudflare Dashboard → Add domain → `univprepai.com`
- [ ] Cloudflare NS 2개 기록:
  - NS1: `_________________.ns.cloudflare.com`
  - NS2: `_________________.ns.cloudflare.com`
- [ ] Plan 선택 (Free / Pro / Business)
- [ ] Zone ID 기록: `_________________________________`

### Phase 2: Namecheap 설정
- [ ] Namecheap → Domain List → `univprepai.com` → Manage
- [ ] Nameservers → Custom DNS 선택
- [ ] Cloudflare NS1 입력
- [ ] Cloudflare NS2 입력
- [ ] 기존 NS 삭제 확인
- [ ] Save 클릭
- [ ] DNSSEC 확인 (켜져 있으면 OFF)

### Phase 3: DNS 레코드 설정
- [ ] A record: `@` → `<ORIGIN_IP>` (Proxied)
- [ ] CNAME: `www` → `@` (Proxied)
- [ ] CNAME: `app` → `@` (Proxied)
- [ ] CNAME: `api` → `@` (Proxied)
- [ ] CNAME: `static` → `@` (Proxied)

### Phase 4: SSL/TLS 설정
- [ ] SSL/TLS Mode: `Full (Strict)`
- [ ] Always Use HTTPS: `ON`
- [ ] HSTS: `Enabled` (max-age 15552000)
- [ ] Auto Minify: `ON` (HTML/CSS/JS)
- [ ] Brotli: `ON`
- [ ] HTTP/2, HTTP/3: `Enabled`

### Phase 5: 검증
- [ ] Cloudflare Status: `Active` 확인
- [ ] DNS propagation 확인: `nslookup univprepai.com`
- [ ] HTTPS 작동 확인: `https://www.univprepai.com`
- [ ] 서브도메인 확인: `app`, `api`, `static`
- [ ] SSL Labs 테스트: A+ 등급 확인

**완료 날짜:** `____/____/____`  
**담당자:** `________________`  
**비고:** `_______________________________`

---

## A.2 CollegePrepAI.com

### Phase 1: Cloudflare 설정
- [ ] Cloudflare Dashboard → Add domain → `collegeprepai.com`
- [ ] Cloudflare NS 2개 기록:
  - NS1: `_________________.ns.cloudflare.com`
  - NS2: `_________________.ns.cloudflare.com`
- [ ] Plan 선택 (Free / Pro / Business)
- [ ] Zone ID 기록: `_________________________________`

### Phase 2: Namecheap 설정
- [ ] Namecheap → Domain List → `collegeprepai.com` → Manage
- [ ] Nameservers → Custom DNS 선택
- [ ] Cloudflare NS1 입력
- [ ] Cloudflare NS2 입력
- [ ] 기존 NS 삭제 확인
- [ ] Save 클릭
- [ ] DNSSEC 확인 (켜져 있으면 OFF)

### Phase 3: DNS 레코드 설정
- [ ] A record: `@` → `<ORIGIN_IP>` (Proxied)
- [ ] CNAME: `www` → `@` (Proxied)
- [ ] CNAME: `app` → `@` (Proxied)
- [ ] CNAME: `api` → `@` (Proxied)
- [ ] CNAME: `static` → `@` (Proxied)

### Phase 4: SSL/TLS 설정
- [ ] SSL/TLS Mode: `Full (Strict)`
- [ ] Always Use HTTPS: `ON`
- [ ] HSTS: `Enabled` (max-age 15552000)
- [ ] Auto Minify: `ON` (HTML/CSS/JS)
- [ ] Brotli: `ON`
- [ ] HTTP/2, HTTP/3: `Enabled`

### Phase 5: 검증
- [ ] Cloudflare Status: `Active` 확인
- [ ] DNS propagation 확인: `nslookup collegeprepai.com`
- [ ] HTTPS 작동 확인: `https://www.collegeprepai.com`
- [ ] 서브도메인 확인: `app`, `api`, `static`
- [ ] SSL Labs 테스트: A+ 등급 확인

**완료 날짜:** `____/____/____`  
**담당자:** `________________`  
**비고:** `_______________________________`

---

## A.3 SkillPrepAI.com

### Phase 1: Cloudflare 설정
- [ ] Cloudflare Dashboard → Add domain → `skillprepai.com`
- [ ] Cloudflare NS 2개 기록:
  - NS1: `_________________.ns.cloudflare.com`
  - NS2: `_________________.ns.cloudflare.com`
- [ ] Plan 선택 (Free / Pro / Business)
- [ ] Zone ID 기록: `_________________________________`

### Phase 2: Namecheap 설정
- [ ] Namecheap → Domain List → `skillprepai.com` → Manage
- [ ] Nameservers → Custom DNS 선택
- [ ] Cloudflare NS1 입력
- [ ] Cloudflare NS2 입력
- [ ] 기존 NS 삭제 확인
- [ ] Save 클릭
- [ ] DNSSEC 확인 (켜져 있으면 OFF)

### Phase 3: DNS 레코드 설정
- [ ] A record: `@` → `<ORIGIN_IP>` (Proxied)
- [ ] CNAME: `www` → `@` (Proxied)
- [ ] CNAME: `app` → `@` (Proxied)
- [ ] CNAME: `api` → `@` (Proxied)
- [ ] CNAME: `static` → `@` (Proxied)

### Phase 4: SSL/TLS 설정
- [ ] SSL/TLS Mode: `Full (Strict)`
- [ ] Always Use HTTPS: `ON`
- [ ] HSTS: `Enabled` (max-age 15552000)
- [ ] Auto Minify: `ON` (HTML/CSS/JS)
- [ ] Brotli: `ON`
- [ ] HTTP/2, HTTP/3: `Enabled`

### Phase 5: 검증
- [ ] Cloudflare Status: `Active` 확인
- [ ] DNS propagation 확인: `nslookup skillprepai.com`
- [ ] HTTPS 작동 확인: `https://www.skillprepai.com`
- [ ] 서브도메인 확인: `app`, `api`, `static`
- [ ] SSL Labs 테스트: A+ 등급 확인

**완료 날짜:** `____/____/____`  
**담당자:** `________________`  
**비고:** `_______________________________`

---

## A.4 MediPrepAI.com

### Phase 1: Cloudflare 설정
- [ ] Cloudflare Dashboard → Add domain → `mediprepai.com`
- [ ] Cloudflare NS 2개 기록:
  - NS1: `_________________.ns.cloudflare.com`
  - NS2: `_________________.ns.cloudflare.com`
- [ ] Plan 선택 (Free / Pro / Business)
- [ ] Zone ID 기록: `_________________________________`

### Phase 2: Namecheap 설정
- [ ] Namecheap → Domain List → `mediprepai.com` → Manage
- [ ] Nameservers → Custom DNS 선택
- [ ] Cloudflare NS1 입력
- [ ] Cloudflare NS2 입력
- [ ] 기존 NS 삭제 확인
- [ ] Save 클릭
- [ ] DNSSEC 확인 (켜져 있으면 OFF)

### Phase 3: DNS 레코드 설정
- [ ] A record: `@` → `<ORIGIN_IP>` (Proxied)
- [ ] CNAME: `www` → `@` (Proxied)
- [ ] CNAME: `app` → `@` (Proxied)
- [ ] CNAME: `api` → `@` (Proxied)
- [ ] CNAME: `static` → `@` (Proxied)

### Phase 4: SSL/TLS 설정
- [ ] SSL/TLS Mode: `Full (Strict)`
- [ ] Always Use HTTPS: `ON`
- [ ] HSTS: `Enabled` (max-age 15552000)
- [ ] Auto Minify: `ON` (HTML/CSS/JS)
- [ ] Brotli: `ON`
- [ ] HTTP/2, HTTP/3: `Enabled`

### Phase 5: 검증
- [ ] Cloudflare Status: `Active` 확인
- [ ] DNS propagation 확인: `nslookup mediprepai.com`
- [ ] HTTPS 작동 확인: `https://www.mediprepai.com`
- [ ] 서브도메인 확인: `app`, `api`, `static`
- [ ] SSL Labs 테스트: A+ 등급 확인

**완료 날짜:** `____/____/____`  
**담당자:** `________________`  
**비고:** `_______________________________`

---

## A.5 MajorPrepAI.com

### Phase 1: Cloudflare 설정
- [ ] Cloudflare Dashboard → Add domain → `majorprepai.com`
- [ ] Cloudflare NS 2개 기록:
  - NS1: `_________________.ns.cloudflare.com`
  - NS2: `_________________.ns.cloudflare.com`
- [ ] Plan 선택 (Free / Pro / Business)
- [ ] Zone ID 기록: `_________________________________`

### Phase 2: Namecheap 설정
- [ ] Namecheap → Domain List → `majorprepai.com` → Manage
- [ ] Nameservers → Custom DNS 선택
- [ ] Cloudflare NS1 입력
- [ ] Cloudflare NS2 입력
- [ ] 기존 NS 삭제 확인
- [ ] Save 클릭
- [ ] DNSSEC 확인 (켜져 있으면 OFF)

### Phase 3: DNS 레코드 설정
- [ ] A record: `@` → `<ORIGIN_IP>` (Proxied)
- [ ] CNAME: `www` → `@` (Proxied)
- [ ] CNAME: `app` → `@` (Proxied)
- [ ] CNAME: `api` → `@` (Proxied)
- [ ] CNAME: `static` → `@` (Proxied)

### Phase 4: SSL/TLS 설정
- [ ] SSL/TLS Mode: `Full (Strict)`
- [ ] Always Use HTTPS: `ON`
- [ ] HSTS: `Enabled` (max-age 15552000)
- [ ] Auto Minify: `ON` (HTML/CSS/JS)
- [ ] Brotli: `ON`
- [ ] HTTP/2, HTTP/3: `Enabled`

### Phase 5: 검증
- [ ] Cloudflare Status: `Active` 확인
- [ ] DNS propagation 확인: `nslookup majorprepai.com`
- [ ] HTTPS 작동 확인: `https://www.majorprepai.com`
- [ ] 서브도메인 확인: `app`, `api`, `static`
- [ ] SSL Labs 테스트: A+ 등급 확인

**완료 날짜:** `____/____/____`  
**담당자:** `________________`  
**비고:** `_______________________________`

---

## A.6 My-Ktube.com

### Phase 1: Cloudflare 설정
- [ ] Cloudflare Dashboard → Add domain → `my-ktube.com`
- [ ] Cloudflare NS 2개 기록:
  - NS1: `_________________.ns.cloudflare.com`
  - NS2: `_________________.ns.cloudflare.com`
- [ ] Plan 선택 (Free / Pro / Business)
- [ ] Zone ID 기록: `_________________________________`

### Phase 2: Namecheap 설정
- [ ] Namecheap → Domain List → `my-ktube.com` → Manage
- [ ] Nameservers → Custom DNS 선택
- [ ] Cloudflare NS1 입력
- [ ] Cloudflare NS2 입력
- [ ] 기존 NS 삭제 확인
- [ ] Save 클릭
- [ ] DNSSEC 확인 (켜져 있으면 OFF)

### Phase 3: DNS 레코드 설정
- [ ] A record: `@` → `<ORIGIN_IP>` (Proxied)
- [ ] CNAME: `www` → `@` (Proxied)
- [ ] CNAME: `app` → `@` (Proxied)
- [ ] CNAME: `api` → `@` (Proxied)
- [ ] CNAME: `static` → `@` (Proxied)

### Phase 4: SSL/TLS 설정
- [ ] SSL/TLS Mode: `Full (Strict)`
- [ ] Always Use HTTPS: `ON`
- [ ] HSTS: `Enabled` (max-age 15552000)
- [ ] Auto Minify: `ON` (HTML/CSS/JS)
- [ ] Brotli: `ON`
- [ ] HTTP/2, HTTP/3: `Enabled`

### Phase 5: 검증
- [ ] Cloudflare Status: `Active` 확인
- [ ] DNS propagation 확인: `nslookup my-ktube.com`
- [ ] HTTPS 작동 확인: `https://www.my-ktube.com`
- [ ] 서브도메인 확인: `app`, `api`, `static`
- [ ] SSL Labs 테스트: A+ 등급 확인

**완료 날짜:** `____/____/____`  
**담당자:** `________________`  
**비고:** `_______________________________`

---

## A.7 My-Ktube.ai

### Phase 1: Cloudflare 설정
- [ ] Cloudflare Dashboard → Add domain → `my-ktube.ai`
- [ ] Cloudflare NS 2개 기록:
  - NS1: `_________________.ns.cloudflare.com`
  - NS2: `_________________.ns.cloudflare.com`
- [ ] Plan 선택 (Free / Pro / Business)
- [ ] Zone ID 기록: `_________________________________`

### Phase 2: Namecheap 설정
- [ ] Namecheap → Domain List → `my-ktube.ai` → Manage
- [ ] Nameservers → Custom DNS 선택
- [ ] Cloudflare NS1 입력
- [ ] Cloudflare NS2 입력
- [ ] 기존 NS 삭제 확인
- [ ] Save 클릭
- [ ] DNSSEC 확인 (켜져 있으면 OFF)

### Phase 3: DNS 레코드 설정
- [ ] A record: `@` → `<ORIGIN_IP>` (Proxied)
- [ ] CNAME: `www` → `@` (Proxied)
- [ ] CNAME: `app` → `@` (Proxied) *(optional)*
- [ ] CNAME: `api` → `@` (Proxied)

### Phase 4: SSL/TLS 설정
- [ ] SSL/TLS Mode: `Full (Strict)`
- [ ] Always Use HTTPS: `ON`
- [ ] HSTS: `Enabled` (max-age 15552000)
- [ ] Auto Minify: `ON` (HTML/CSS/JS)
- [ ] Brotli: `ON`
- [ ] HTTP/2, HTTP/3: `Enabled`

### Phase 5: 검증
- [ ] Cloudflare Status: `Active` 확인
- [ ] DNS propagation 확인: `nslookup my-ktube.ai`
- [ ] HTTPS 작동 확인: `https://www.my-ktube.ai`
- [ ] 서브도메인 확인: `api` (필수), `app` (선택)
- [ ] SSL Labs 테스트: A+ 등급 확인

**완료 날짜:** `____/____/____`  
**담당자:** `________________`  
**비고:** `_______________________________`

---

## A.8 mpcstudy.com

### Phase 1: Cloudflare 설정
- [ ] Cloudflare Dashboard → Add domain → `mpcstudy.com`
- [ ] Cloudflare NS 2개 기록:
  - NS1: `_________________.ns.cloudflare.com`
  - NS2: `_________________.ns.cloudflare.com`
- [ ] Plan 선택 (Free / Pro / Business)
- [ ] Zone ID 기록: `_________________________________`

### Phase 2: Namecheap 설정
- [ ] Namecheap → Domain List → `mpcstudy.com` → Manage
- [ ] Nameservers → Custom DNS 선택
- [ ] Cloudflare NS1 입력
- [ ] Cloudflare NS2 입력
- [ ] 기존 NS 삭제 확인
- [ ] Save 클릭
- [ ] DNSSEC 확인 (켜져 있으면 OFF)

### Phase 3: DNS 레코드 설정
- [ ] A record: `@` → `<ORIGIN_IP>` (Proxied)
- [ ] CNAME: `www` → `@` (Proxied)
- [ ] CNAME: `app` → `@` (Proxied)
- [ ] CNAME: `api` → `@` (Proxied)
- [ ] CNAME: `static` → `@` (Proxied)

### Phase 4: SSL/TLS 설정
- [ ] SSL/TLS Mode: `Full (Strict)`
- [ ] Always Use HTTPS: `ON`
- [ ] HSTS: `Enabled` (max-age 15552000)
- [ ] Auto Minify: `ON` (HTML/CSS/JS)
- [ ] Brotli: `ON`
- [ ] HTTP/2, HTTP/3: `Enabled`

### Phase 5: 검증
- [ ] Cloudflare Status: `Active` 확인
- [ ] DNS propagation 확인: `nslookup mpcstudy.com`
- [ ] HTTPS 작동 확인: `https://www.mpcstudy.com`
- [ ] 서브도메인 확인: `app`, `api`, `static`
- [ ] SSL Labs 테스트: A+ 등급 확인

**완료 날짜:** `____/____/____`  
**담당자:** `________________`  
**비고:** `_______________________________`

---

## A.9 전체 진행 상황 요약

| 도메인 | Status | 완료 날짜 | 담당자 | 비고 |
|--------|--------|-----------|--------|------|
| DreamSeedAI.com | ⬜ Not Started / 🟡 In Progress / ✅ Complete | | | |
| UnivPrepAI.com | ⬜ Not Started / 🟡 In Progress / ✅ Complete | | | |
| CollegePrepAI.com | ⬜ Not Started / 🟡 In Progress / ✅ Complete | | | |
| SkillPrepAI.com | ⬜ Not Started / 🟡 In Progress / ✅ Complete | | | |
| MediPrepAI.com | ⬜ Not Started / 🟡 In Progress / ✅ Complete | | | |
| MajorPrepAI.com | ⬜ Not Started / 🟡 In Progress / ✅ Complete | | | |
| My-Ktube.com | ⬜ Not Started / 🟡 In Progress / ✅ Complete | | | |
| My-Ktube.ai | ⬜ Not Started / 🟡 In Progress / ✅ Complete | | | |
| mpcstudy.com | ⬜ Not Started / 🟡 In Progress / ✅ Complete | | | |

**전체 진행률:** `____/9` 도메인 완료

---

## A.10 검증 명령어 참고

```bash
# DNS propagation 확인
nslookup <domain>
dig <domain> +short

# Cloudflare NS 확인
dig NS <domain> +short

# HTTPS 작동 확인
curl -I https://www.<domain>
curl -I https://app.<domain>
curl -I https://api.<domain>

# SSL 인증서 확인
openssl s_client -connect <domain>:443 -servername <domain> | openssl x509 -noout -dates

# SSL Labs 테스트
# https://www.ssllabs.com/ssltest/analyze.html?d=<domain>
```

---

**부록 완성:** 이 체크리스트를 복사하여 팀 협업 도구(Notion, Jira, GitHub Projects)에서 사용하세요.

---

# 📸 부록 B: Namecheap 단계별 스크린샷 가이드

이 가이드는 Namecheap에서 Cloudflare로 네임서버를 변경하는 전체 과정을 스크린샷과 함께 설명합니다.

---

## B.1 Namecheap 로그인 및 도메인 리스트 접근

### Step 1: Namecheap 로그인

1. 브라우저에서 `https://www.namecheap.com` 접속
2. 우측 상단 **Sign In** 클릭
3. Username과 Password 입력
4. **Log In** 클릭

**📸 스크린샷 설명:**
```
┌─────────────────────────────────────────┐
│  Namecheap                    [Sign In] │
│                                          │
│         Welcome to Namecheap            │
│                                          │
│  Username: [________________]           │
│  Password: [________________]           │
│                                          │
│           [ Log In ]                     │
│                                          │
└─────────────────────────────────────────┘
```

---

### Step 2: Domain List 접근

1. 로그인 후 상단 메뉴에서 **Domain List** 클릭
   - 또는 계정 드롭다운 → **Domain List** 선택
2. 보유한 모든 도메인 목록이 표시됨

**📸 스크린샷 설명:**
```
┌─────────────────────────────────────────────────────────────┐
│  Namecheap  [Domain List] [Products] [Account]             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Domain List (8)                           [+ Add Domain]   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Domain              Status    Expires    [Manage]      │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ univprepai.com      Active    2026-05   [Manage]      │ │
│  │ collegeprepai.com   Active    2026-05   [Manage]      │ │
│  │ skillprepai.com     Active    2026-05   [Manage]      │ │
│  │ mediprepai.com      Active    2026-05   [Manage]      │ │
│  │ majorprepai.com     Active    2026-05   [Manage]      │ │
│  │ my-ktube.com        Active    2026-06   [Manage]      │ │
│  │ my-ktube.ai         Active    2026-06   [Manage]      │ │
│  │ mpcstudy.com        Active    2025-12   [Manage]      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## B.2 도메인 관리 페이지 접근

### Step 3: 특정 도메인 선택

1. Domain List에서 변경할 도메인 찾기 (예: `univprepai.com`)
2. 해당 도메인 행의 **Manage** 버튼 클릭

**📸 스크린샷 설명:**
```
┌─────────────────────────────────────────────────────────────┐
│  Domain: univprepai.com                                     │
│                                                              │
│  [Details] [Advanced DNS] [Email Forwarding] [Renewal]     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Domain Information                                   │  │
│  │  Status: Active                                       │  │
│  │  Created: 2024-05-15                                 │  │
│  │  Expires: 2026-05-15                                 │  │
│  │                                                       │  │
│  │  Nameservers                                         │  │
│  │  ⚫ Namecheap BasicDNS                               │  │
│  │  ⚪ Custom DNS                                       │  │
│  │                                                       │  │
│  │  Current Nameservers:                                │  │
│  │  • dns1.registrar-servers.com                       │  │
│  │  • dns2.registrar-servers.com                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## B.3 Nameserver 설정 변경

### Step 4: Custom DNS 선택

1. **Nameservers** 섹션에서 **Custom DNS** 라디오 버튼 선택
2. 입력 필드가 활성화됨 (기본적으로 2개 필드 표시)

**📸 스크린샷 설명:**
```
┌──────────────────────────────────────────────────────────┐
│  Nameservers                                              │
│                                                            │
│  ⚪ Namecheap BasicDNS                                    │
│     Use Namecheap's default nameservers                  │
│                                                            │
│  ⚫ Custom DNS                                            │
│     Point to your own or third-party nameservers         │
│                                                            │
│     Nameserver 1: [_______________________________]      │
│                                                            │
│     Nameserver 2: [_______________________________]      │
│                                                            │
│                   [+ Add Nameserver]                      │
│                                                            │
│                   [✓ Save]                                │
└──────────────────────────────────────────────────────────┘
```

---

### Step 5: Cloudflare Nameserver 입력

1. **Nameserver 1** 필드에 Cloudflare NS1 입력
   - 예: `guss.ns.cloudflare.com`
2. **Nameserver 2** 필드에 Cloudflare NS2 입력
   - 예: `lara.ns.cloudflare.com`
3. 기존 Namecheap NS는 자동으로 제거됨

**⚠️ 중요:** Cloudflare Dashboard에 표시된 정확한 NS를 복사-붙여넣기 하세요!

**📸 스크린샷 설명:**
```
┌──────────────────────────────────────────────────────────┐
│  Nameservers                                              │
│                                                            │
│  ⚪ Namecheap BasicDNS                                    │
│                                                            │
│  ⚫ Custom DNS                                            │
│                                                            │
│     Nameserver 1: [guss.ns.cloudflare.com            ]   │
│                                                            │
│     Nameserver 2: [lara.ns.cloudflare.com            ]   │
│                                                            │
│                   [+ Add Nameserver]                      │
│                                                            │
│                   [✓ Save]                                │
└──────────────────────────────────────────────────────────┘
```

---

### Step 6: 저장 및 확인

1. 하단의 **✓ Save** 버튼 클릭
2. 확인 메시지가 나타남: "Nameservers updated successfully"
3. 변경사항이 즉시 반영됨

**📸 스크린샷 설명:**
```
┌──────────────────────────────────────────────────────────┐
│  ✅ Success!                                              │
│                                                            │
│  Nameservers have been updated successfully.             │
│  Changes may take up to 48 hours to propagate.           │
│                                                            │
│  Current Nameservers:                                     │
│  • guss.ns.cloudflare.com                                │
│  • lara.ns.cloudflare.com                                │
│                                                            │
│                   [ OK ]                                   │
└──────────────────────────────────────────────────────────┘
```

---

## B.4 DNSSEC 설정 확인 및 비활성화

### Step 7: Advanced DNS 탭 접근

1. 상단 메뉴에서 **Advanced DNS** 탭 클릭
2. DNSSEC 섹션으로 스크롤

**📸 스크린샷 설명:**
```
┌─────────────────────────────────────────────────────────────┐
│  Domain: univprepai.com                                     │
│                                                              │
│  [Details] [Advanced DNS] [Email Forwarding] [Renewal]     │
│           ▲ (현재 탭)                                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  HOST RECORDS                                         │  │
│  │  (Managed by Custom Nameservers)                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DNSSEC                                               │  │
│  │  ⚫ Enabled                                           │  │
│  │  ⚪ Disabled                                          │  │
│  │                                                       │  │
│  │  [Turn Off DNSSEC]                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

### Step 8: DNSSEC 비활성화 (필요시)

⚠️ **중요:** Cloudflare로 NS를 변경할 때는 Namecheap의 DNSSEC을 **반드시 꺼야 합니다**.

1. DNSSEC 섹션에서 **Disabled** 라디오 버튼 선택
2. **Turn Off DNSSEC** 버튼 클릭
3. 확인 팝업에서 **Yes, turn off** 클릭

**📸 스크린샷 설명:**
```
┌──────────────────────────────────────────────────────────┐
│  DNSSEC                                                   │
│                                                            │
│  ⚪ Enabled                                               │
│  ⚫ Disabled                                              │
│                                                            │
│  [ Turn Off DNSSEC ]                                      │
│                                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │  ⚠️  Confirm Action                                 │  │
│  │                                                      │  │
│  │  Are you sure you want to turn off DNSSEC?         │  │
│  │  This may take up to 24 hours to propagate.        │  │
│  │                                                      │  │
│  │     [Cancel]     [Yes, turn off]                    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

### Step 9: DNSSEC 비활성화 완료

**📸 스크린샷 설명:**
```
┌──────────────────────────────────────────────────────────┐
│  ✅ DNSSEC Disabled                                       │
│                                                            │
│  DNSSEC has been turned off for univprepai.com           │
│                                                            │
│  DNSSEC                                                   │
│  ⚪ Enabled                                               │
│  ⚫ Disabled ✓                                            │
│                                                            │
│  Status: Not active                                       │
└──────────────────────────────────────────────────────────┘
```

---

## B.5 변경사항 검증

### Step 10: Nameserver 변경 확인

1. **Details** 탭으로 돌아가기
2. Nameservers 섹션에서 변경사항 확인
3. Cloudflare NS가 표시되어야 함

**📸 스크린샷 설명:**
```
┌──────────────────────────────────────────────────────────┐
│  Domain Information                                       │
│                                                            │
│  Status: Active                                           │
│  Created: 2024-05-15                                     │
│  Expires: 2026-05-15                                     │
│                                                            │
│  Nameservers: Custom DNS ✓                               │
│  • guss.ns.cloudflare.com                                │
│  • lara.ns.cloudflare.com                                │
│                                                            │
│  Last Updated: 2025-11-20 14:32:15 UTC                   │
└──────────────────────────────────────────────────────────┘
```

---

### Step 11: 터미널에서 DNS 전파 확인

로컬 터미널에서 다음 명령어로 NS 변경 확인:

```bash
# Nameserver 확인
dig NS univprepai.com +short

# 출력 예시:
# guss.ns.cloudflare.com.
# lara.ns.cloudflare.com.
```

**📸 스크린샷 설명 (터미널):**
```
┌────────────────────────────────────────────────────────┐
│ $ dig NS univprepai.com +short                         │
│ guss.ns.cloudflare.com.                                │
│ lara.ns.cloudflare.com.                                │
│                                                         │
│ $ nslookup univprepai.com                              │
│ Server:  1.1.1.1                                       │
│ Address: 1.1.1.1#53                                    │
│                                                         │
│ Non-authoritative answer:                              │
│ Name:    univprepai.com                                │
│ Address: <ORIGIN_IP>                                   │
│                                                         │
│ $ █                                                     │
└────────────────────────────────────────────────────────┘
```

---

## B.6 Cloudflare에서 Active 상태 확인

### Step 12: Cloudflare Dashboard 확인

1. Cloudflare Dashboard 접속: `https://dash.cloudflare.com`
2. 변경한 도메인 클릭 (예: `univprepai.com`)
3. Overview 페이지에서 Status 확인

**📸 스크린샷 설명:**
```
┌─────────────────────────────────────────────────────────────┐
│  Cloudflare                          [univprepai.com ▼]     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ Great news! Cloudflare is now protecting your site      │
│                                                              │
│  Status: Active                                             │
│  Name Servers: guss.ns.cloudflare.com                       │
│                lara.ns.cloudflare.com                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Quick Actions                                        │  │
│  │  • Add DNS Record                                     │  │
│  │  • Configure SSL/TLS                                  │  │
│  │  • Set up Page Rules                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Analytics (Last 24 hours)                                  │
│  Requests: 0     Bandwidth: 0 B     Threats: 0             │
└─────────────────────────────────────────────────────────────┘
```

---

## B.7 전체 프로세스 타임라인

```
Time: 00:00  → Namecheap 로그인 및 Domain List 접근
       ↓
Time: 00:02  → 도메인 선택 (Manage 클릭)
       ↓
Time: 00:03  → Custom DNS 선택
       ↓
Time: 00:04  → Cloudflare NS 입력 (복사-붙여넣기)
       ↓
Time: 00:05  → 저장 (Save) 클릭
       ↓
Time: 00:06  → Advanced DNS 탭 → DNSSEC OFF
       ↓
Time: 00:08  → 변경사항 확인 (Details 탭)
       ↓
Time: 00:10  → 터미널에서 dig/nslookup 테스트
       ↓
Time: 00:15  → Cloudflare Dashboard에서 Active 확인
       ↓
Time: 5-20분 → DNS 전파 완료 (최대 24시간)
```

---

## B.8 문제 해결 (Troubleshooting)

### 문제 1: "Invalid Nameserver" 오류

**증상:**
```
❌ Invalid nameserver format
```

**해결방법:**
1. NS 끝에 `.` (점) 제거
   - ❌ 잘못: `guss.ns.cloudflare.com.`
   - ✅ 올바름: `guss.ns.cloudflare.com`
2. 공백 제거
3. 정확히 복사했는지 Cloudflare에서 재확인

---

### 문제 2: DNS 전파가 24시간 이상 걸림

**증상:**
```
$ dig NS univprepai.com +short
dns1.registrar-servers.com.  (← 여전히 이전 NS)
dns2.registrar-servers.com.
```

**해결방법:**
1. Namecheap에서 NS 변경 재확인
2. DNSSEC이 OFF인지 확인
3. DNS 캐시 클리어:
   ```bash
   # macOS/Linux
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
   
   # Windows
   ipconfig /flushdns
   ```
4. 다른 DNS 서버로 조회:
   ```bash
   dig @8.8.8.8 NS univprepai.com +short
   dig @1.1.1.1 NS univprepai.com +short
   ```

---

### 문제 3: Cloudflare Status가 "Pending" 상태

**증상:**
```
⏳ Status: Pending Nameserver Update
```

**해결방법:**
1. Namecheap에서 정확한 NS 입력 확인
2. 5-20분 대기 (정상적인 전파 시간)
3. Cloudflare에서 "Recheck Now" 버튼 클릭
4. 24시간 후에도 Pending이면 Cloudflare Support 문의

---

## B.9 모범 사례 (Best Practices)

### ✅ DO (권장)

1. **복사-붙여넣기 사용**
   - Cloudflare NS를 직접 타이핑하지 말고 복사
   - 오타 방지

2. **DNSSEC 먼저 비활성화**
   - NS 변경 전에 DNSSEC OFF
   - 충돌 방지

3. **한 번에 한 도메인씩**
   - 8개 도메인을 동시에 변경하지 말고 순차적으로
   - 문제 발생 시 디버깅 용이

4. **변경사항 기록**
   - 부록 A 체크리스트에 NS, Zone ID, 완료 날짜 기록
   - 팀원과 공유

5. **테스트 후 진행**
   - 첫 도메인 변경 후 완전히 Active 될 때까지 대기
   - 나머지 도메인 변경

---

### ❌ DON'T (피해야 할 것)

1. **다른 도메인의 NS 재사용 금지**
   - ❌ univprepai.com과 collegeprepai.com에 같은 NS 사용
   - ✅ 각 도메인은 Cloudflare가 제공한 고유 NS 사용

2. **DNSSEC 켜진 상태로 NS 변경 금지**
   - 전파 실패 또는 지연 발생 가능

3. **Namecheap BasicDNS로 되돌리지 말 것**
   - Cloudflare로 이전한 후에는 BasicDNS 사용 불가
   - DNS 레코드는 Cloudflare에서 관리

4. **NS 변경 후 즉시 DNS 레코드 수정 금지**
   - Active 상태 확인 후 DNS 레코드 작업 시작

---

## B.10 체크리스트 (각 도메인마다 반복)

```
□ 1. Namecheap 로그인
□ 2. Domain List → 도메인 선택 → Manage
□ 3. Custom DNS 선택
□ 4. Cloudflare NS1 입력
□ 5. Cloudflare NS2 입력
□ 6. Save 클릭
□ 7. Advanced DNS → DNSSEC OFF
□ 8. Details 탭에서 NS 변경 확인
□ 9. 터미널에서 dig NS <domain> 확인
□ 10. Cloudflare Dashboard → Active 확인
□ 11. 부록 A 체크리스트에 기록
```

---

**부록 B 완성:** 이 가이드를 참조하여 모든 도메인의 NS 변경을 안전하게 수행하세요.

---

# 🔀 부록 C: Reverse Proxy 템플릿 (Nginx / Traefik)

이 부록은 DreamSeedAI MegaCity의 모든 도메인을 위한 프로덕션급 Reverse Proxy 설정을 제공합니다.

---

## C.1 아키텍처 개요

```
Internet
   ↓
Cloudflare (Edge Proxy)
   ↓ (HTTPS, Proxied)
Reverse Proxy (Nginx or Traefik)
   ↓
┌──────────────┬──────────────┬──────────────┐
│  Next.js     │  FastAPI     │  Static CDN  │
│  (Frontend)  │  (Backend)   │  (Assets)    │
│  Port 3000   │  Port 8000   │  Port 9000   │
└──────────────┴──────────────┴──────────────┘
```

**역할:**
- **Cloudflare**: DDoS 방어, CDN, SSL/TLS 종료 (Edge)
- **Reverse Proxy**: Origin 라우팅, 로드밸런싱, 로컬 SSL
- **Upstream Services**: 실제 애플리케이션 서버

---

## C.2 Nginx 설정

### C.2.1 디렉토리 구조

```
/etc/nginx/
├── nginx.conf                    # 메인 설정
├── conf.d/
│   ├── upstream.conf             # Upstream 정의
│   ├── ssl.conf                  # SSL 공통 설정
│   └── security.conf             # 보안 헤더
└── sites-available/
    ├── univprepai.com.conf
    ├── collegeprepai.com.conf
    ├── skillprepai.com.conf
    ├── mediprepai.com.conf
    ├── majorprepai.com.conf
    ├── my-ktube.com.conf
    ├── my-ktube.ai.conf
    └── mpcstudy.com.conf
```

---

### C.2.2 메인 설정 (`nginx.conf`)

```nginx
# /etc/nginx/nginx.conf

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;

    # Buffer sizes
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 16k;

    # Timeouts
    client_body_timeout 12;
    client_header_timeout 12;
    send_timeout 10;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=app_limit:10m rate=30r/s;

    # Include configs
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

---

### C.2.3 Upstream 정의 (`conf.d/upstream.conf`)

```nginx
# /etc/nginx/conf.d/upstream.conf

# FastAPI Backend (모든 도메인 공통)
upstream backend_api {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    # server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;  # 추가 인스턴스
    keepalive 32;
}

# Next.js Frontend (모든 도메인 공통)
upstream frontend_app {
    least_conn;
    server 127.0.0.1:3000 max_fails=3 fail_timeout=30s;
    # server 127.0.0.1:3001 max_fails=3 fail_timeout=30s;  # 추가 인스턴스
    keepalive 32;
}

# Static Assets (CDN Origin)
upstream static_cdn {
    server 127.0.0.1:9000 max_fails=3 fail_timeout=30s;
    keepalive 16;
}

# K-Zone AI 전용 Backend
upstream kzone_ai_api {
    least_conn;
    server 127.0.0.1:8100 max_fails=3 fail_timeout=30s;
    # server 127.0.0.1:8101 max_fails=3 fail_timeout=30s;  # GPU 인스턴스 추가
    keepalive 32;
}
```

---

### C.2.4 SSL 공통 설정 (`conf.d/ssl.conf`)

```nginx
# /etc/nginx/conf.d/ssl.conf

# SSL 프로토콜 및 암호화
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;

# SSL 세션 캐시
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 1.1.1.1 1.0.0.1 valid=300s;
resolver_timeout 5s;

# Let's Encrypt 인증서 경로 (도메인별로 수정 필요)
# ssl_certificate /etc/letsencrypt/live/<domain>/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/<domain>/privkey.pem;
# ssl_trusted_certificate /etc/letsencrypt/live/<domain>/chain.pem;
```

---

### C.2.5 보안 헤더 (`conf.d/security.conf`)

```nginx
# /etc/nginx/conf.d/security.conf

# Security Headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# HSTS (Cloudflare에서 이미 처리되지만 Origin에서도 설정)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Content Security Policy (앱별로 커스터마이징 필요)
# add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

# Remove server header
server_tokens off;
```

---

### C.2.6 도메인별 설정 예시 (`sites-available/univprepai.com.conf`)

```nginx
# /etc/nginx/sites-available/univprepai.com.conf

# HTTP → HTTPS 리다이렉트
server {
    listen 80;
    listen [::]:80;
    server_name univprepai.com www.univprepai.com app.univprepai.com api.univprepai.com static.univprepai.com;

    # Let's Encrypt ACME Challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# www.univprepai.com (Landing)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name www.univprepai.com;

    ssl_certificate /etc/letsencrypt/live/univprepai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/univprepai.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/univprepai.com/chain.pem;

    # Cloudflare Real IP
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 131.0.72.0/22;
    real_ip_header CF-Connecting-IP;

    location / {
        proxy_pass http://frontend_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 90;
    }
}

# app.univprepai.com (Next.js Frontend)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name app.univprepai.com;

    ssl_certificate /etc/letsencrypt/live/univprepai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/univprepai.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/univprepai.com/chain.pem;

    # Rate limiting
    limit_req zone=app_limit burst=50 nodelay;

    # Cloudflare Real IP
    include /etc/nginx/snippets/cloudflare-ips.conf;
    real_ip_header CF-Connecting-IP;

    location / {
        proxy_pass http://frontend_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 90;
    }

    # Next.js static files
    location /_next/static {
        proxy_pass http://frontend_app;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, max-age=3600, immutable";
    }
}

# api.univprepai.com (FastAPI Backend)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.univprepai.com;

    ssl_certificate /etc/letsencrypt/live/univprepai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/univprepai.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/univprepai.com/chain.pem;

    # Rate limiting (API는 더 엄격)
    limit_req zone=api_limit burst=20 nodelay;

    # Cloudflare Real IP
    include /etc/nginx/snippets/cloudflare-ips.conf;
    real_ip_header CF-Connecting-IP;

    location / {
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}

# static.univprepai.com (CDN Origin)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name static.univprepai.com;

    ssl_certificate /etc/letsencrypt/live/univprepai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/univprepai.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/univprepai.com/chain.pem;

    # Cloudflare Real IP
    include /etc/nginx/snippets/cloudflare-ips.conf;
    real_ip_header CF-Connecting-IP;

    location / {
        proxy_pass http://static_cdn;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_cache_valid 200 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
        add_header X-Content-Type-Options "nosniff";
    }
}
```

---

### C.2.7 Cloudflare IP Snippet (`snippets/cloudflare-ips.conf`)

```nginx
# /etc/nginx/snippets/cloudflare-ips.conf
# Cloudflare IP 범위 (주기적으로 업데이트 필요)

set_real_ip_from 173.245.48.0/20;
set_real_ip_from 103.21.244.0/22;
set_real_ip_from 103.22.200.0/22;
set_real_ip_from 103.31.4.0/22;
set_real_ip_from 141.101.64.0/18;
set_real_ip_from 108.162.192.0/18;
set_real_ip_from 190.93.240.0/20;
set_real_ip_from 188.114.96.0/20;
set_real_ip_from 197.234.240.0/22;
set_real_ip_from 198.41.128.0/17;
set_real_ip_from 162.158.0.0/15;
set_real_ip_from 104.16.0.0/13;
set_real_ip_from 104.24.0.0/14;
set_real_ip_from 172.64.0.0/13;
set_real_ip_from 131.0.72.0/22;

# IPv6
set_real_ip_from 2400:cb00::/32;
set_real_ip_from 2606:4700::/32;
set_real_ip_from 2803:f800::/32;
set_real_ip_from 2405:b500::/32;
set_real_ip_from 2405:8100::/32;
set_real_ip_from 2a06:98c0::/29;
set_real_ip_from 2c0f:f248::/32;
```

---

### C.2.8 K-Zone AI 특화 설정 (`sites-available/my-ktube.ai.conf`)

```nginx
# /etc/nginx/sites-available/my-ktube.ai.conf

# api.my-ktube.ai (AI 전용 Backend)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.my-ktube.ai;

    ssl_certificate /etc/letsencrypt/live/my-ktube.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/my-ktube.ai/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/my-ktube.ai/chain.pem;

    # AI 요청은 오래 걸릴 수 있음
    client_max_body_size 500M;
    proxy_read_timeout 600;
    proxy_connect_timeout 600;
    proxy_send_timeout 600;

    # Cloudflare Real IP
    include /etc/nginx/snippets/cloudflare-ips.conf;
    real_ip_header CF-Connecting-IP;

    location / {
        proxy_pass http://kzone_ai_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;  # 실시간 스트리밍용
    }

    # AI 모델 inference (긴 타임아웃)
    location ~ ^/api/v1/(voice|dance|drama|creator|hangul)/ {
        proxy_pass http://kzone_ai_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 900;
        proxy_connect_timeout 300;
        proxy_send_timeout 900;
        proxy_buffering off;
    }
}
```

---

### C.2.9 Nginx 배포 스크립트

```bash
#!/bin/bash
# deploy-nginx.sh

set -e

echo "🚀 Deploying Nginx Configuration for DreamSeedAI MegaCity"

# 1. 설정 파일 복사
echo "📋 Copying configuration files..."
sudo cp nginx.conf /etc/nginx/
sudo cp conf.d/*.conf /etc/nginx/conf.d/
sudo cp sites-available/*.conf /etc/nginx/sites-available/

# 2. Sites-enabled 심볼릭 링크 생성
echo "🔗 Creating symbolic links..."
for domain in univprepai collegeprepai skillprepai mediprepai majorprepai my-ktube my-ktube.ai mpcstudy; do
    sudo ln -sf /etc/nginx/sites-available/${domain}.com.conf /etc/nginx/sites-enabled/
done

# 3. 설정 테스트
echo "✅ Testing Nginx configuration..."
sudo nginx -t

# 4. Nginx 재시작
echo "🔄 Reloading Nginx..."
sudo systemctl reload nginx

echo "✅ Nginx deployment completed!"
```

---

## C.3 Traefik 설정

### C.3.1 디렉토리 구조

```
/etc/traefik/
├── traefik.yml               # 메인 설정
├── dynamic/
│   ├── middlewares.yml       # 미들웨어 정의
│   ├── routers.yml           # 라우터 정의
│   └── services.yml          # 서비스 정의
└── acme.json                 # Let's Encrypt 인증서
```

---

### C.3.2 메인 설정 (`traefik.yml`)

```yaml
# /etc/traefik/traefik.yml

# Global configuration
global:
  checkNewVersion: true
  sendAnonymousUsage: false

# API and Dashboard
api:
  dashboard: true
  insecure: false

# Entry Points
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https

  websecure:
    address: ":443"
    http:
      tls:
        certResolver: cloudflare
    forwardedHeaders:
      trustedIPs:
        # Cloudflare IP ranges
        - "173.245.48.0/20"
        - "103.21.244.0/22"
        - "103.22.200.0/22"
        - "103.31.4.0/22"
        - "141.101.64.0/18"
        - "108.162.192.0/18"
        - "190.93.240.0/20"
        - "188.114.96.0/20"
        - "197.234.240.0/22"
        - "198.41.128.0/17"
        - "162.158.0.0/15"
        - "104.16.0.0/13"
        - "104.24.0.0/14"
        - "172.64.0.0/13"
        - "131.0.72.0/22"

# Certificate Resolvers
certificatesResolvers:
  cloudflare:
    acme:
      email: admin@dreamseedai.com
      storage: /etc/traefik/acme.json
      httpChallenge:
        entryPoint: web

# Providers
providers:
  file:
    directory: /etc/traefik/dynamic
    watch: true

# Logging
log:
  level: INFO
  filePath: /var/log/traefik/traefik.log

accessLog:
  filePath: /var/log/traefik/access.log
  format: json

# Metrics
metrics:
  prometheus:
    addEntryPointsLabels: true
    addServicesLabels: true
```

---

### C.3.3 미들웨어 (`dynamic/middlewares.yml`)

```yaml
# /etc/traefik/dynamic/middlewares.yml

http:
  middlewares:
    # Security Headers
    security-headers:
      headers:
        frameDeny: true
        contentTypeNosniff: true
        browserXssFilter: true
        referrerPolicy: "no-referrer-when-downgrade"
        customFrameOptionsValue: "SAMEORIGIN"
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
        customResponseHeaders:
          X-Forwarded-Proto: "https"

    # Rate Limiting (API)
    api-rate-limit:
      rateLimit:
        average: 10
        burst: 20
        period: 1s

    # Rate Limiting (App)
    app-rate-limit:
      rateLimit:
        average: 30
        burst: 50
        period: 1s

    # Compression
    gzip-compress:
      compress: {}

    # CORS (for API)
    cors-headers:
      headers:
        accessControlAllowMethods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
        accessControlAllowOriginList:
          - "https://app.univprepai.com"
          - "https://app.collegeprepai.com"
          - "https://app.skillprepai.com"
          - "https://app.mediprepai.com"
          - "https://app.majorprepai.com"
          - "https://app.my-ktube.com"
          - "https://app.my-ktube.ai"
          - "https://app.mpcstudy.com"
        accessControlAllowHeaders:
          - "*"
        accessControlAllowCredentials: true
        accessControlMaxAge: 86400

    # Redirect to www
    redirect-to-www:
      redirectRegex:
        regex: "^https://([^/]+)\\.([^/]+)/(.*)"
        replacement: "https://www.${1}.${2}/${3}"
        permanent: true
```

---

### C.3.4 서비스 (`dynamic/services.yml`)

```yaml
# /etc/traefik/dynamic/services.yml

http:
  services:
    # FastAPI Backend (공통)
    backend-api:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8000"
        healthCheck:
          path: /health
          interval: 30s
          timeout: 5s

    # Next.js Frontend (공통)
    frontend-app:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:3000"
        healthCheck:
          path: /
          interval: 30s
          timeout: 5s

    # Static CDN
    static-cdn:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:9000"

    # K-Zone AI Backend
    kzone-ai-api:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8100"
        healthCheck:
          path: /health
          interval: 60s
          timeout: 10s
```

---

### C.3.5 라우터 (`dynamic/routers.yml`)

```yaml
# /etc/traefik/dynamic/routers.yml

http:
  routers:
    # UnivPrepAI.com - www (Landing)
    univprepai-www:
      rule: "Host(`www.univprepai.com`) || Host(`univprepai.com`)"
      entryPoints:
        - websecure
      service: frontend-app
      middlewares:
        - security-headers
        - gzip-compress
        - app-rate-limit
      tls:
        certResolver: cloudflare

    # UnivPrepAI.com - app (Frontend)
    univprepai-app:
      rule: "Host(`app.univprepai.com`)"
      entryPoints:
        - websecure
      service: frontend-app
      middlewares:
        - security-headers
        - gzip-compress
        - app-rate-limit
      tls:
        certResolver: cloudflare

    # UnivPrepAI.com - api (Backend)
    univprepai-api:
      rule: "Host(`api.univprepai.com`)"
      entryPoints:
        - websecure
      service: backend-api
      middlewares:
        - security-headers
        - gzip-compress
        - api-rate-limit
        - cors-headers
      tls:
        certResolver: cloudflare

    # UnivPrepAI.com - static (CDN)
    univprepai-static:
      rule: "Host(`static.univprepai.com`)"
      entryPoints:
        - websecure
      service: static-cdn
      middlewares:
        - security-headers
        - gzip-compress
      tls:
        certResolver: cloudflare

    # My-Ktube.ai - api (AI Backend)
    my-ktube-ai-api:
      rule: "Host(`api.my-ktube.ai`)"
      entryPoints:
        - websecure
      service: kzone-ai-api
      middlewares:
        - security-headers
        - cors-headers
      tls:
        certResolver: cloudflare

    # (나머지 도메인도 동일한 패턴으로 추가)
```

---

### C.3.6 Docker Compose 배포

```yaml
# docker-compose.yml

version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    networks:
      - proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/traefik:/etc/traefik:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/log/traefik:/var/log/traefik
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.dreamseedai.com`)"
      - "traefik.http.routers.traefik.entrypoints=websecure"
      - "traefik.http.routers.traefik.tls.certresolver=cloudflare"
      - "traefik.http.routers.traefik.service=api@internal"

networks:
  proxy:
    external: true
```

---

## C.4 비교: Nginx vs Traefik

| 기능 | Nginx | Traefik |
|------|-------|---------|
| **성능** | ⭐⭐⭐⭐⭐ 매우 높음 | ⭐⭐⭐⭐ 높음 |
| **설정 난이도** | ⭐⭐⭐ 중간 (수동) | ⭐⭐⭐⭐ 쉬움 (자동) |
| **Docker 통합** | ⭐⭐ 수동 설정 | ⭐⭐⭐⭐⭐ 자동 발견 |
| **동적 설정** | ⭐⭐ Reload 필요 | ⭐⭐⭐⭐⭐ 실시간 |
| **SSL 관리** | ⭐⭐⭐ Certbot 필요 | ⭐⭐⭐⭐⭐ 자동 |
| **모니터링** | ⭐⭐⭐ 외부 도구 | ⭐⭐⭐⭐ 내장 대시보드 |
| **성숙도** | ⭐⭐⭐⭐⭐ 매우 안정적 | ⭐⭐⭐⭐ 안정적 |
| **커뮤니티** | ⭐⭐⭐⭐⭐ 매우 크다 | ⭐⭐⭐⭐ 크다 |

**추천:**
- **Nginx**: 최고 성능, 정적 설정, 전통적 배포
- **Traefik**: Docker/K8s 환경, 동적 설정, 쉬운 관리

---

## C.5 배포 체크리스트

### Nginx 배포
```bash
# 1. 패키지 설치
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx

# 2. 설정 파일 복사
sudo cp -r nginx/* /etc/nginx/

# 3. 심볼릭 링크 생성
sudo ln -sf /etc/nginx/sites-available/*.conf /etc/nginx/sites-enabled/

# 4. 설정 테스트
sudo nginx -t

# 5. Let's Encrypt 인증서 발급
sudo certbot --nginx -d univprepai.com -d www.univprepai.com -d app.univprepai.com -d api.univprepai.com -d static.univprepai.com

# 6. Nginx 시작
sudo systemctl enable nginx
sudo systemctl start nginx

# 7. 자동 갱신 설정
sudo crontab -e
# 추가: 0 3 * * * certbot renew --quiet && systemctl reload nginx
```

### Traefik 배포
```bash
# 1. Docker 설치 (이미 설치된 경우 스킵)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. 설정 파일 복사
sudo mkdir -p /etc/traefik/dynamic
sudo cp traefik.yml /etc/traefik/
sudo cp dynamic/*.yml /etc/traefik/dynamic/

# 3. acme.json 생성 (권한 중요!)
sudo touch /etc/traefik/acme.json
sudo chmod 600 /etc/traefik/acme.json

# 4. Docker 네트워크 생성
docker network create proxy

# 5. Traefik 시작
docker-compose up -d traefik

# 6. 로그 확인
docker logs -f traefik
```

---

**부록 C 완성:** Nginx 또는 Traefik을 선택하여 DreamSeedAI MegaCity를 프로덕션에 배포하세요.

---

# 🤖 부록 D: CI/CD 자동 DNS 업데이트 설계

이 부록은 GitHub Actions를 사용하여 Cloudflare DNS 레코드를 자동으로 관리하는 완전한 CI/CD 파이프라인을 제공합니다.

---

## D.1 아키텍처 개요

```
GitHub Repository (dreamseed_monorepo)
   ↓
GitHub Actions Workflow
   ↓
Cloudflare API (DNS Management)
   ↓
8개 도메인 DNS 레코드 자동 업데이트
```

**목표:**
1. Infrastructure as Code (IaC) - DNS를 코드로 관리
2. Git 기반 변경 이력 추적
3. Pull Request 기반 검토 및 승인
4. 자동 배포 및 롤백
5. 다중 환경 지원 (staging, production)

---

## D.2 디렉토리 구조

```
dreamseed_monorepo/
├── .github/
│   └── workflows/
│       ├── dns-deploy.yml           # DNS 배포 워크플로우
│       ├── dns-validate.yml         # DNS 검증 워크플로우
│       └── dns-sync.yml             # DNS 동기화 (scheduled)
├── ops/
│   └── dns/
│       ├── config/
│       │   ├── univprepai.com.yml
│       │   ├── collegeprepai.com.yml
│       │   ├── skillprepai.com.yml
│       │   ├── mediprepai.com.yml
│       │   ├── majorprepai.com.yml
│       │   ├── my-ktube.com.yml
│       │   ├── my-ktube.ai.yml
│       │   └── mpcstudy.com.yml
│       ├── scripts/
│       │   ├── deploy_dns.py        # DNS 배포 스크립트
│       │   ├── validate_dns.py      # DNS 검증 스크립트
│       │   └── sync_dns.py          # DNS 동기화 스크립트
│       ├── terraform/               # Terraform (대안)
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       └── README.md
└── README.md
```

---

## D.3 DNS 설정 파일 (YAML)

### D.3.1 도메인별 설정 예시 (`ops/dns/config/univprepai.com.yml`)

```yaml
# ops/dns/config/univprepai.com.yml

domain: univprepai.com
zone_id: YOUR_CLOUDFLARE_ZONE_ID  # Cloudflare Zone ID

# DNS Records
records:
  # Root domain
  - type: A
    name: "@"
    content: 1.2.3.4  # Origin Server IP
    ttl: 1  # 1 = Auto (Cloudflare proxy)
    proxied: true
    comment: "Root domain - Origin server"

  # www subdomain
  - type: CNAME
    name: "www"
    content: "@"
    ttl: 1
    proxied: true
    comment: "Landing page"

  # app subdomain (Next.js Frontend)
  - type: CNAME
    name: "app"
    content: "@"
    ttl: 1
    proxied: true
    comment: "Next.js Frontend UI"

  # api subdomain (FastAPI Backend)
  - type: CNAME
    name: "api"
    content: "@"
    ttl: 1
    proxied: true
    comment: "FastAPI Backend API"

  # static subdomain (CDN)
  - type: CNAME
    name: "static"
    content: "@"
    ttl: 1
    proxied: true
    comment: "CDN Static Assets"

  # MX Records (Email)
  - type: MX
    name: "@"
    content: "mail.univprepai.com"
    priority: 10
    ttl: 1
    proxied: false
    comment: "Mail server"

  # TXT Record (SPF)
  - type: TXT
    name: "@"
    content: "v=spf1 include:_spf.google.com ~all"
    ttl: 1
    proxied: false
    comment: "SPF record for Google Workspace"

  # TXT Record (DMARC)
  - type: TXT
    name: "_dmarc"
    content: "v=DMARC1; p=quarantine; rua=mailto:dmarc@univprepai.com"
    ttl: 1
    proxied: false
    comment: "DMARC policy"

# Cloudflare Settings
settings:
  ssl_mode: "full_strict"
  always_use_https: true
  hsts:
    enabled: true
    max_age: 15552000
    include_subdomains: true
    preload: true
  auto_minify:
    html: true
    css: true
    js: true
  brotli: true
  http2: true
  http3: true
  ipv6: true

# Firewall Rules (optional)
firewall_rules:
  - description: "Block bad bots"
    expression: "(cf.client.bot)"
    action: "block"
    enabled: true
```

---

### D.3.2 K-Zone AI 특화 설정 (`ops/dns/config/my-ktube.ai.yml`)

```yaml
# ops/dns/config/my-ktube.ai.yml

domain: my-ktube.ai
zone_id: YOUR_CLOUDFLARE_ZONE_ID

records:
  - type: A
    name: "@"
    content: 1.2.3.4
    ttl: 1
    proxied: true
    comment: "AI Hub root"

  - type: CNAME
    name: "www"
    content: "@"
    ttl: 1
    proxied: true
    comment: "AI feature showcase"

  - type: CNAME
    name: "app"
    content: "@"
    ttl: 1
    proxied: true
    comment: "Creator Studio (optional)"

  - type: CNAME
    name: "api"
    content: "@"
    ttl: 1
    proxied: true
    comment: "AI inference API (vLLM)"

settings:
  ssl_mode: "full_strict"
  always_use_https: true
  hsts:
    enabled: true
    max_age: 31536000
  auto_minify:
    html: true
    css: true
    js: true
  brotli: true
```

---

## D.4 Python 배포 스크립트

### D.4.1 DNS 배포 스크립트 (`ops/dns/scripts/deploy_dns.py`)

```python
#!/usr/bin/env python3
"""
DNS Deployment Script for DreamSeedAI MegaCity
Deploys DNS records to Cloudflare using YAML configuration files.
"""

import os
import sys
import yaml
import requests
from typing import Dict, List, Any

# Cloudflare API credentials (from environment)
CF_API_TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN')
CF_API_BASE = 'https://api.cloudflare.com/client/v4'

class CloudflareDNS:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }

    def get_zone_id(self, domain: str) -> str:
        """Get Cloudflare Zone ID for a domain."""
        url = f'{CF_API_BASE}/zones'
        params = {'name': domain}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['success'] and data['result']:
            return data['result'][0]['id']
        raise ValueError(f"Zone not found for domain: {domain}")

    def list_dns_records(self, zone_id: str) -> List[Dict[str, Any]]:
        """List all DNS records for a zone."""
        url = f'{CF_API_BASE}/zones/{zone_id}/dns_records'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data['result'] if data['success'] else []

    def create_dns_record(self, zone_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new DNS record."""
        url = f'{CF_API_BASE}/zones/{zone_id}/dns_records'
        payload = {
            'type': record['type'],
            'name': record['name'],
            'content': record['content'],
            'ttl': record.get('ttl', 1),
            'proxied': record.get('proxied', False),
        }
        
        # Add priority for MX records
        if record['type'] == 'MX':
            payload['priority'] = record.get('priority', 10)
        
        # Add comment if provided
        if 'comment' in record:
            payload['comment'] = record['comment']
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def update_dns_record(self, zone_id: str, record_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing DNS record."""
        url = f'{CF_API_BASE}/zones/{zone_id}/dns_records/{record_id}'
        payload = {
            'type': record['type'],
            'name': record['name'],
            'content': record['content'],
            'ttl': record.get('ttl', 1),
            'proxied': record.get('proxied', False),
        }
        
        if record['type'] == 'MX':
            payload['priority'] = record.get('priority', 10)
        
        if 'comment' in record:
            payload['comment'] = record['comment']
        
        response = requests.put(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def delete_dns_record(self, zone_id: str, record_id: str) -> Dict[str, Any]:
        """Delete a DNS record."""
        url = f'{CF_API_BASE}/zones/{zone_id}/dns_records/{record_id}'
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_zone_settings(self, zone_id: str, settings: Dict[str, Any]):
        """Update Cloudflare zone settings."""
        # SSL Mode
        if 'ssl_mode' in settings:
            url = f'{CF_API_BASE}/zones/{zone_id}/settings/ssl'
            payload = {'value': settings['ssl_mode']}
            requests.patch(url, headers=self.headers, json=payload)
        
        # Always Use HTTPS
        if 'always_use_https' in settings:
            url = f'{CF_API_BASE}/zones/{zone_id}/settings/always_use_https'
            payload = {'value': 'on' if settings['always_use_https'] else 'off'}
            requests.patch(url, headers=self.headers, json=payload)
        
        # HSTS
        if 'hsts' in settings and settings['hsts']['enabled']:
            url = f'{CF_API_BASE}/zones/{zone_id}/settings/security_header'
            payload = {
                'value': {
                    'strict_transport_security': {
                        'enabled': True,
                        'max_age': settings['hsts']['max_age'],
                        'include_subdomains': settings['hsts']['include_subdomains'],
                        'preload': settings['hsts']['preload']
                    }
                }
            }
            requests.patch(url, headers=self.headers, json=payload)
        
        # Auto Minify
        if 'auto_minify' in settings:
            url = f'{CF_API_BASE}/zones/{zone_id}/settings/minify'
            payload = {'value': settings['auto_minify']}
            requests.patch(url, headers=self.headers, json=payload)
        
        # Brotli
        if 'brotli' in settings:
            url = f'{CF_API_BASE}/zones/{zone_id}/settings/brotli'
            payload = {'value': 'on' if settings['brotli'] else 'off'}
            requests.patch(url, headers=self.headers, json=payload)

def load_config(config_file: str) -> Dict[str, Any]:
    """Load DNS configuration from YAML file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def deploy_dns(config_file: str, dry_run: bool = False):
    """Deploy DNS configuration to Cloudflare."""
    print(f"🚀 Deploying DNS for {config_file}")
    
    # Load configuration
    config = load_config(config_file)
    domain = config['domain']
    zone_id = config.get('zone_id')
    
    # Initialize Cloudflare client
    cf = CloudflareDNS(CF_API_TOKEN)
    
    # Get or verify zone ID
    if not zone_id:
        print(f"📍 Fetching Zone ID for {domain}...")
        zone_id = cf.get_zone_id(domain)
        print(f"   Zone ID: {zone_id}")
    
    # Get existing DNS records
    print(f"📋 Fetching existing DNS records...")
    existing_records = cf.list_dns_records(zone_id)
    existing_map = {(r['type'], r['name']): r for r in existing_records}
    
    # Deploy records
    print(f"🔧 Deploying {len(config['records'])} DNS records...")
    for record in config['records']:
        record_key = (record['type'], record['name'])
        
        if dry_run:
            print(f"   [DRY RUN] Would deploy: {record['type']} {record['name']} → {record['content']}")
            continue
        
        if record_key in existing_map:
            # Update existing record
            existing_record = existing_map[record_key]
            if existing_record['content'] != record['content'] or \
               existing_record.get('proxied') != record.get('proxied', False):
                print(f"   ✏️  Updating: {record['type']} {record['name']} → {record['content']}")
                cf.update_dns_record(zone_id, existing_record['id'], record)
            else:
                print(f"   ✅ Unchanged: {record['type']} {record['name']}")
        else:
            # Create new record
            print(f"   ➕ Creating: {record['type']} {record['name']} → {record['content']}")
            cf.create_dns_record(zone_id, record)
    
    # Update zone settings
    if 'settings' in config and not dry_run:
        print(f"⚙️  Updating zone settings...")
        cf.update_zone_settings(zone_id, config['settings'])
    
    print(f"✅ DNS deployment completed for {domain}")

def main():
    if not CF_API_TOKEN:
        print("❌ Error: CLOUDFLARE_API_TOKEN environment variable not set")
        sys.exit(1)
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Deploy DNS configuration to Cloudflare')
    parser.add_argument('config', help='Path to DNS configuration YAML file')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no changes)')
    args = parser.parse_args()
    
    try:
        deploy_dns(args.config, dry_run=args.dry_run)
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

### D.4.2 DNS 검증 스크립트 (`ops/dns/scripts/validate_dns.py`)

```python
#!/usr/bin/env python3
"""
DNS Validation Script
Validates DNS configuration files and checks live DNS records.
"""

import sys
import yaml
import dns.resolver
from typing import Dict, Any, List

def load_config(config_file: str) -> Dict[str, Any]:
    """Load DNS configuration from YAML file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate DNS configuration structure."""
    errors = []
    
    # Check required fields
    if 'domain' not in config:
        errors.append("Missing 'domain' field")
    
    if 'records' not in config or not isinstance(config['records'], list):
        errors.append("Missing or invalid 'records' field")
        return errors
    
    # Validate each record
    for i, record in enumerate(config['records']):
        if 'type' not in record:
            errors.append(f"Record {i}: Missing 'type' field")
        
        if 'name' not in record:
            errors.append(f"Record {i}: Missing 'name' field")
        
        if 'content' not in record:
            errors.append(f"Record {i}: Missing 'content' field")
        
        # Validate record type
        valid_types = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV']
        if record.get('type') not in valid_types:
            errors.append(f"Record {i}: Invalid type '{record.get('type')}'")
        
        # Validate MX priority
        if record.get('type') == 'MX' and 'priority' not in record:
            errors.append(f"Record {i}: MX record missing 'priority' field")
    
    return errors

def check_dns_propagation(domain: str, config: Dict[str, Any]):
    """Check if DNS records are properly propagated."""
    print(f"🔍 Checking DNS propagation for {domain}...")
    
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['1.1.1.1', '8.8.8.8']  # Cloudflare + Google DNS
    
    for record in config['records']:
        record_name = record['name'].replace('@', domain)
        if record['name'] != '@':
            record_name = f"{record['name']}.{domain}"
        
        try:
            if record['type'] == 'A':
                answers = resolver.resolve(record_name, 'A')
                print(f"   ✅ {record_name} (A): {answers[0]}")
            
            elif record['type'] == 'CNAME':
                answers = resolver.resolve(record_name, 'CNAME')
                print(f"   ✅ {record_name} (CNAME): {answers[0]}")
            
            elif record['type'] == 'MX':
                answers = resolver.resolve(record_name, 'MX')
                print(f"   ✅ {record_name} (MX): {answers[0].exchange}")
            
            elif record['type'] == 'TXT':
                answers = resolver.resolve(record_name, 'TXT')
                print(f"   ✅ {record_name} (TXT): {answers[0]}")
        
        except dns.resolver.NXDOMAIN:
            print(f"   ❌ {record_name} ({record['type']}): Domain does not exist")
        except dns.resolver.NoAnswer:
            print(f"   ⚠️  {record_name} ({record['type']}): No answer (might not be propagated yet)")
        except Exception as e:
            print(f"   ❌ {record_name} ({record['type']}): {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate DNS configuration')
    parser.add_argument('config', help='Path to DNS configuration YAML file')
    parser.add_argument('--check-propagation', action='store_true', 
                       help='Check DNS propagation (requires live DNS)')
    args = parser.parse_args()
    
    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        sys.exit(1)
    
    # Validate config
    print(f"📋 Validating {args.config}...")
    errors = validate_config(config)
    
    if errors:
        print("❌ Validation failed:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    
    print("✅ Configuration is valid")
    
    # Check DNS propagation
    if args.check_propagation:
        check_dns_propagation(config['domain'], config)

if __name__ == '__main__':
    main()
```

---

## D.5 GitHub Actions 워크플로우

### D.5.1 DNS 배포 워크플로우 (`.github/workflows/dns-deploy.yml`)

```yaml
name: Deploy DNS Configuration

on:
  push:
    branches:
      - main
    paths:
      - 'ops/dns/config/**/*.yml'
  pull_request:
    branches:
      - main
    paths:
      - 'ops/dns/config/**/*.yml'
  workflow_dispatch:
    inputs:
      domain:
        description: 'Domain to deploy (e.g., univprepai.com)'
        required: true
        type: string
      dry_run:
        description: 'Dry run mode (no changes)'
        required: false
        type: boolean
        default: false

jobs:
  validate:
    name: Validate DNS Configuration
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml requests dnspython

      - name: Validate all DNS configs
        run: |
          for config in ops/dns/config/*.yml; do
            echo "Validating $config..."
            python ops/dns/scripts/validate_dns.py "$config"
          done

  deploy:
    name: Deploy DNS Records
    runs-on: ubuntu-latest
    needs: validate
    if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
    environment: production
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml requests dnspython

      - name: Deploy DNS (All domains)
        if: github.event_name == 'push'
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
        run: |
          for config in ops/dns/config/*.yml; do
            echo "Deploying $config..."
            python ops/dns/scripts/deploy_dns.py "$config"
          done

      - name: Deploy DNS (Single domain)
        if: github.event_name == 'workflow_dispatch'
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
        run: |
          CONFIG="ops/dns/config/${{ github.event.inputs.domain }}.yml"
          if [ ! -f "$CONFIG" ]; then
            echo "❌ Config file not found: $CONFIG"
            exit 1
          fi
          
          if [ "${{ github.event.inputs.dry_run }}" = "true" ]; then
            echo "🔍 Running in DRY RUN mode..."
            python ops/dns/scripts/deploy_dns.py "$CONFIG" --dry-run
          else
            python ops/dns/scripts/deploy_dns.py "$CONFIG"
          fi

      - name: Verify DNS propagation
        run: |
          sleep 10  # Wait for DNS propagation
          for config in ops/dns/config/*.yml; do
            echo "Verifying $config..."
            python ops/dns/scripts/validate_dns.py "$config" --check-propagation
          done

      - name: Notify Slack (Success)
        if: success()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "✅ DNS Deployment Successful",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*DNS Deployment Successful* :white_check_mark:\n\nCommit: ${{ github.sha }}\nBranch: ${{ github.ref }}"
                  }
                }
              ]
            }

      - name: Notify Slack (Failure)
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "❌ DNS Deployment Failed",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*DNS Deployment Failed* :x:\n\nCommit: ${{ github.sha }}\nBranch: ${{ github.ref }}\n\nCheck workflow logs for details."
                  }
                }
              ]
            }
```

---

### D.5.2 DNS 동기화 워크플로우 (`.github/workflows/dns-sync.yml`)

```yaml
name: Sync DNS Configuration

on:
  schedule:
    # Run every day at 3 AM UTC
    - cron: '0 3 * * *'
  workflow_dispatch:

jobs:
  sync:
    name: Sync DNS from Cloudflare
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml requests

      - name: Sync DNS records
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
        run: |
          python ops/dns/scripts/sync_dns.py

      - name: Create Pull Request
        if: success()
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: 'chore: Sync DNS configuration from Cloudflare'
          title: 'DNS Sync: Update from Cloudflare'
          body: |
            ## DNS Configuration Sync
            
            This PR contains DNS configuration updates synced from Cloudflare.
            
            **Changes:**
            - Synced DNS records from live Cloudflare zones
            - Updated on: ${{ github.run_id }}
            
            **Review checklist:**
            - [ ] Verify all changes are expected
            - [ ] Check for any unexpected deletions
            - [ ] Confirm settings are correct
          branch: dns-sync-${{ github.run_id }}
          delete-branch: true
```

---

## D.6 Terraform 대안 (IaC)

### D.6.1 Main Configuration (`ops/dns/terraform/main.tf`)

```hcl
# ops/dns/terraform/main.tf

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
  
  backend "s3" {
    bucket = "dreamseedai-terraform-state"
    key    = "dns/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# UnivPrepAI.com
resource "cloudflare_zone" "univprepai" {
  account_id = var.cloudflare_account_id
  zone       = "univprepai.com"
}

resource "cloudflare_record" "univprepai_root" {
  zone_id = cloudflare_zone.univprepai.id
  name    = "@"
  value   = var.origin_ip
  type    = "A"
  ttl     = 1
  proxied = true
  comment = "Root domain - Origin server"
}

resource "cloudflare_record" "univprepai_www" {
  zone_id = cloudflare_zone.univprepai.id
  name    = "www"
  value   = "@"
  type    = "CNAME"
  ttl     = 1
  proxied = true
  comment = "Landing page"
}

resource "cloudflare_record" "univprepai_app" {
  zone_id = cloudflare_zone.univprepai.id
  name    = "app"
  value   = "@"
  type    = "CNAME"
  ttl     = 1
  proxied = true
  comment = "Next.js Frontend"
}

resource "cloudflare_record" "univprepai_api" {
  zone_id = cloudflare_zone.univprepai.id
  name    = "api"
  value   = "@"
  type    = "CNAME"
  ttl     = 1
  proxied = true
  comment = "FastAPI Backend"
}

resource "cloudflare_record" "univprepai_static" {
  zone_id = cloudflare_zone.univprepai.id
  name    = "static"
  value   = "@"
  type    = "CNAME"
  ttl     = 1
  proxied = true
  comment = "CDN Static Assets"
}

# Zone Settings
resource "cloudflare_zone_settings_override" "univprepai" {
  zone_id = cloudflare_zone.univprepai.id

  settings {
    ssl                      = "full_strict"
    always_use_https         = "on"
    automatic_https_rewrites = "on"
    brotli                   = "on"
    minify {
      css  = "on"
      html = "on"
      js   = "on"
    }
  }
}

# Repeat for other 7 domains...
```

---

### D.6.2 Variables (`ops/dns/terraform/variables.tf`)

```hcl
# ops/dns/terraform/variables.tf

variable "cloudflare_api_token" {
  description = "Cloudflare API Token"
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare Account ID"
  type        = string
}

variable "origin_ip" {
  description = "Origin Server IP Address"
  type        = string
  default     = "1.2.3.4"
}
```

---

## D.7 보안 및 권한 관리

### D.7.1 GitHub Secrets 설정

```bash
# GitHub Repository Settings → Secrets and variables → Actions

# Required secrets:
CLOUDFLARE_API_TOKEN=<your_cloudflare_api_token>
SLACK_WEBHOOK_URL=<your_slack_webhook_url>  # Optional
```

**Cloudflare API Token 생성:**
1. Cloudflare Dashboard → My Profile → API Tokens
2. Create Token → Edit zone DNS (템플릿 사용)
3. Permissions:
   - Zone / DNS / Edit
   - Zone / Zone Settings / Edit
4. Zone Resources:
   - Include / All zones
5. Copy token → GitHub Secrets에 추가

---

### D.7.2 RBAC (Role-Based Access Control)

```yaml
# GitHub Repository Settings → Environments → production

Protection rules:
  - Required reviewers: 2
  - Allowed branches: main
  - Wait timer: 5 minutes
  - Deployment protection rules
```

---

## D.8 사용 예시

### D.8.1 시나리오 1: 새 DNS 레코드 추가

```bash
# 1. 브랜치 생성
git checkout -b feat/add-mail-record

# 2. DNS 설정 파일 수정
vim ops/dns/config/univprepai.com.yml
# MX 레코드 추가

# 3. 로컬 검증
python ops/dns/scripts/validate_dns.py ops/dns/config/univprepai.com.yml

# 4. 커밋 및 푸시
git add ops/dns/config/univprepai.com.yml
git commit -m "feat: Add MX record for univprepai.com"
git push origin feat/add-mail-record

# 5. Pull Request 생성
# → GitHub Actions가 자동으로 검증

# 6. 리뷰 후 Merge
# → main 브랜치에 머지되면 자동 배포
```

---

### D.8.2 시나리오 2: Origin IP 변경 (긴급)

```bash
# 1. Manual workflow 실행
# GitHub Actions → Deploy DNS Configuration → Run workflow

# 2. 입력:
#    - domain: univprepai.com
#    - dry_run: true  (먼저 테스트)

# 3. Dry run 확인 후 실제 배포
#    - dry_run: false

# 4. 검증
dig @1.1.1.1 univprepai.com +short
```

---

### D.8.3 시나리오 3: 8개 도메인 일괄 배포

```bash
# 1. 모든 설정 파일 업데이트
for domain in univprepai collegeprepai skillprepai mediprepai majorprepai my-ktube my-ktube.ai mpcstudy; do
  vim ops/dns/config/${domain}.com.yml
done

# 2. 커밋 및 푸시
git add ops/dns/config/*.yml
git commit -m "feat: Update origin IP for all domains"
git push origin main

# 3. GitHub Actions가 모든 도메인 자동 배포
# 약 5-10분 소요
```

---

## D.9 모니터링 및 알림

### D.9.1 Slack 알림 설정

```yaml
# .github/workflows/dns-deploy.yml에 이미 포함됨

- name: Notify Slack
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "✅ DNS Deployment Successful",
        "blocks": [...]
      }
```

---

### D.9.2 DNS Health Check (Scheduled)

```yaml
# .github/workflows/dns-health-check.yml

name: DNS Health Check

on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Check DNS records
        run: |
          for domain in univprepai.com collegeprepai.com skillprepai.com mediprepai.com majorprepai.com my-ktube.com my-ktube.ai mpcstudy.com; do
            echo "Checking $domain..."
            dig @1.1.1.1 $domain +short || echo "❌ Failed: $domain"
            dig @1.1.1.1 www.$domain +short || echo "❌ Failed: www.$domain"
            dig @1.1.1.1 app.$domain +short || echo "❌ Failed: app.$domain"
            dig @1.1.1.1 api.$domain +short || echo "❌ Failed: api.$domain"
          done
```

---

## D.10 롤백 전략

### D.10.1 Git 기반 롤백

```bash
# 1. 이전 커밋으로 되돌리기
git log --oneline ops/dns/config/  # 이전 커밋 찾기
git revert <commit-hash>
git push origin main

# 2. GitHub Actions가 자동으로 이전 설정 배포
```

---

### D.10.2 수동 롤백 (긴급)

```bash
# 1. 백업 설정으로 복구
cp ops/dns/config/univprepai.com.yml.backup ops/dns/config/univprepai.com.yml

# 2. 수동 배포
python ops/dns/scripts/deploy_dns.py ops/dns/config/univprepai.com.yml

# 3. 검증
python ops/dns/scripts/validate_dns.py ops/dns/config/univprepai.com.yml --check-propagation
```

---

## D.11 체크리스트

### 초기 설정
```
□ 1. Cloudflare API Token 생성
□ 2. GitHub Secrets 추가 (CLOUDFLARE_API_TOKEN)
□ 3. ops/dns/config/ 디렉토리 생성
□ 4. 8개 도메인 YAML 파일 작성
□ 5. Python 스크립트 추가 (deploy, validate, sync)
□ 6. GitHub Actions 워크플로우 추가
□ 7. 첫 배포 테스트 (dry-run)
□ 8. 프로덕션 배포
□ 9. Slack 알림 설정 (선택)
□ 10. 문서화 완료
```

### 일상 운영
```
□ 1. DNS 변경 시 Pull Request 생성
□ 2. 리뷰어 2명 승인
□ 3. main 브랜치 머지
□ 4. GitHub Actions 자동 배포 확인
□ 5. DNS propagation 검증 (10분)
□ 6. Slack 알림 확인
```

---

**부록 D 완성:** GitHub Actions를 사용하여 DreamSeedAI MegaCity의 DNS를 자동으로 관리하세요.
