# ⚖️ MegaCity Legal & Compliance Handbook

## GDPR · PIPA · COPPA · FERPA · EU AI Act · DMCA · 글로벌 규제 종합 대응 가이드

**버전:** 1.0  
**작성일:** 2025-11-23  
**작성자:** DreamSeedAI Legal · Compliance Team

---

# 📌 0. 개요 (Overview)

본 문서는 DreamSeedAI MegaCity가 운영되는 모든 지역(한국·APAC·미국·유럽)을 대상으로 하는  
**통합 법무·규제·데이터 보호·AI 규제 대응 핸드북**입니다.

포함 내용:

```
1. 글로벌 데이터 보호법(GDPR, PIPA, APPI, PDPA, CCPA/CPRA) 요약
2. 교육 분야 규제 (FERPA, COPPA)
3. AI 규제 (EU AI Act 2026)
4. 콘텐츠 규제 (DMCA, 저작권)
5. K-Zone 영상/음성 규제 준수
6. 국제 데이터 이전(Transfer) 가이드
7. DPIA / PIA(개인정보영향평가) 절차
8. 사용자 권리 요청 처리(삭제/정정/열람)
9. Data Retention & Minimization 정책
10. Incident Notification 규정
```

---

# 🛡️ 1. GDPR (EU) 핵심 요약

GDPR은 MegaCity EU 출시 시 가장 강력하게 영향을 미치는 규제.

### 1.1 GDPR 원칙(7대)

```
1) Lawfulness
2) Purpose Limitation
3) Data Minimization
4) Accuracy
5) Storage Limitation
6) Integrity & Confidentiality
7) Accountability
```

### 1.2 GDPR 대응

* Pseudonymization(가명처리) 필수
* Raw 음성/영상 7일 후 삭제
* 모델 학습 데이터: DPIA 필수
* EU → 한국/미국 데이터 이동 제한
* EU 지역 전용 서버(Frankfurt Region) 사용

### 1.3 GDPR 주요 조항 대응

#### Article 5 (원칙)

* Data Minimization 적용
* Purpose Limitation 명시

#### Article 6 (합법적 처리 근거)

* 계약 이행 (Contract)
* 정당한 이익 (Legitimate Interest)
* 동의 (Consent) - 13세 미만은 부모 동의

#### Article 15-22 (사용자 권리)

* Access (열람)
* Rectification (정정)
* Erasure (삭제)
* Portability (이동)
* Object (거부)

#### Article 33-34 (침해 신고)

* 72시간 내 감독기구 신고
* 사용자 직접 통지 (high risk)

---

# 🇰🇷 2. PIPA (대한민국)

한국 사용자 대상 기본 규제.

### 2.1 핵심

* 민감정보(얼굴·음성) 최소 수집
* 제3자 제공 금지 (학부모 동의 시 예외)
* 삭제 요청 30일 내 처리

### 2.2 주요 규정

#### 제15조 (개인정보의 수집·이용)

* 명시적 동의 필요
* 목적 외 사용 금지

#### 제17조 (개인정보의 제공)

* 제3자 제공 시 별도 동의
* AI 학습 = 제3자 제공으로 간주 가능

#### 제21조 (개인정보의 파기)

* 목적 달성 시 지체 없이 파기
* 영상/음성 7일 원칙 적용

#### 제23조 (민감정보의 처리 제한)

* 건강, 생체정보 등 민감정보
* Voice biometrics 주의 필요

### 2.3 만 14세 미만

* 법정대리인 동의 필수
* Parent–Student Flow 적용

---

# 🇺🇸 3. FERPA (학생 정보 보호)

UnivPrepAI, CollegePrepAI 핵심.

### 3.1 핵심 규정

```
학생 기록(Student Records) → 보호 대상
부모/학생만 접근 허용(18세 미만)
학교/기관 계약 필요
```

### 3.2 MegaCity 대응

* Student Dashboard Access Control 강화
* Parent–Student 승인 Flow 적용
* Educational Records 5년 보관 후 익명화

### 3.3 FERPA Exceptions

* Directory Information (제한적 공개 가능)
* School Officials (legitimate interest)
* Court Orders (법원 명령)

---

# 🇺🇸 4. COPPA (13세 미만 아동)

My-Ktube의 글로벌 사용을 고려하여 필수.

### 4.1 규정

```
13세 미만 → 부모 동의 필수
광고/프로파일링 금지
음성/영상 데이터 최소화
```

### 4.2 Verifiable Parental Consent

* Email + Verification Code
* Credit Card verification (대안)
* Video call verification (고위험)

### 4.3 COPPA Safe Harbor

* COPPA 인증 프로그램 참여 검토

---

# 🇯🇵 5. APPI (일본)

2027 APAC 확장 시 일본 핵심.

### 5.1 대응

* 일본 사용자 데이터는 Tokyo Region에 저장
* 얼굴/음성 데이터 7일 원칙 동일 적용

### 5.2 특이사항

* 개인정보위원회(PPC) 신고 필요 (특정 케이스)
* 해외 이전 시 본인 동의 필요

---

# 🇸🇬 6. PDPA (싱가포르)

### 6.1 핵심

* Consent-based approach
* Data Protection Officer (DPO) 지정
* Notification of data breach (3 days)

### 6.2 DNC (Do Not Call) Registry

* Marketing SMS/Email 주의

---

# 🇺🇸 7. CCPA/CPRA (캘리포니아)

### 7.1 핵심 요구사항

* "Do Not Sell My Info" 버튼 제공
* 데이터 삭제 요청 빠른 처리
* 민감 데이터(음성·영상) 분류

### 7.2 CPRA 추가 사항 (2023~)

* Sensitive Personal Information 보호 강화
* Automated Decision-Making 투명성

### 7.3 MegaCity 대응

* No Sale Policy (데이터 판매 없음 명시)
* Right to Delete API 구현

---

# 🇪🇺 8. EU AI Act (2026 시행)

AI Tutor/멀티모달 AI에 직접 적용.

### 8.1 MegaCity 분류

```
"High Risk AI System" (교육 분야에 해당)
```

### 8.2 요구사항

* 투명성(사용자에게 AI 사용 알림)
* 설명 가능성(xAI module 제공)
* 안전 모드와 Sandbox 모드 제공
* 인적 감독(Human oversight)
* 정확성·견고성 검증

### 8.3 금지되는 AI

* Social Scoring (MegaCity 해당 없음)
* Subliminal manipulation
* Exploiting vulnerabilities of children

### 8.4 Conformity Assessment

* Third-party certification 필요 가능성
* Technical documentation 유지

---

# 🎥 9. DMCA & 저작권

특히 My-Ktube AI와 Creator Studio에서 핵심.

### 9.1 규정

* 저작권 보호 음원/영상 업로드 금지
* 합법적 샘플/사용자 생성 콘텐츠만 AI 분석 가능
* Cover Dance/Voice는 "변환·분석 목적"으로 허용되나 저장 최소화

### 9.2 DMCA Safe Harbor

* Notice & Takedown 절차 구축
* Designated Agent 지정
* Repeat Infringer Policy

### 9.3 Fair Use

* Educational purpose
* Transformative use (AI analysis)
* Limited to necessary amount

---

# 🎵 10. K-Zone (음성/영상/모션) 규제 대응

### 10.1 원칙

```
Raw video/audio 7일 후 자동 삭제
Pose keypoints는 비식별 데이터로 장기 보관 가능
자동 삭제 정책 Transparency 페이지에 공개
```

### 10.2 Biometric Data

* 얼굴 인식 → 즉시 폐기
* Voice print → Feature만 보관
* Motion skeleton → 익명화 후 보관 가능

### 10.3 Content Moderation

* NSFW detection
* Hate speech filtering
* Deepfake prevention

---

# 🌍 11. International Data Transfer

### 11.1 원칙

```
Local-first 저장
Cross-region sync는 pseudonymized 데이터만
Model training은 익명화된 Feature Store 기반
```

### 11.2 Transfer Mechanisms

#### GDPR (EU → Non-EU)

* Standard Contractual Clauses (SCCs)
* Adequacy Decision (한국 일부 인정)
* Binding Corporate Rules (BCR)

#### APPI (Japan)

* Consent-based transfer
* Adequate protection

### 11.3 Data Localization

```
KR users → Seoul
JP users → Tokyo
EU users → Frankfurt
US users → Virginia
```

---

# 🛠️ 12. DPIA (Data Protection Impact Assessment)

LLM/Multi-modal 모델 학습 시 반드시 DPIA 수행.

### 12.1 필수 항목:

```
1) 데이터 종류
2) 보존 기간
3) 위험도 평가
4) 완화 조치
5) DPO 승인
```

### 12.2 DPIA 수행 시기

* 새로운 AI 모델 도입
* 대량의 민감정보 처리
* 시스템적 모니터링
* 아동 대상 프로파일링

### 12.3 DPIA Template

```
1. Processing Description
2. Necessity & Proportionality
3. Risk Identification
4. Mitigation Measures
5. Stakeholder Consultation
6. DPO Sign-off
```

---

# 🗑️ 13. Data Retention Policy

```
Raw Audio/Video → 7 days
Pose Keypoints → 90 days
User Logs → 1 year
Exam Attempts → 3 years
Invoices/Billing → 5 years
Anonymized Analytics → Indefinite
```

### 13.1 Retention Justification

* Legal obligation (5 years - accounting)
* Contract performance (3 years - education records)
* Legitimate interest (1 year - logs)

### 13.2 Deletion Process

* Automated deletion jobs (daily)
* Manual deletion requests (30 days SLA)
* Backup deletion (90 days)

---

# 🙋 14. User Rights Handling

### 14.1 삭제 요청 (Right to Erasure)

* 30일 내 처리
* AI 학습 데이터도 제거 (Data Shredding)
* Backups는 90일 내 파기

### 14.2 데이터 열람 요청 (Right to Access)

* JSON export 제공
* 30일 내 응답
* 무료 제공 (연 1회)

### 14.3 정정 요청 (Right to Rectification)

* 부정확한 정보 수정
* 15일 내 처리

### 14.4 이동 요청 (Right to Data Portability)

* 기계판독가능 형식 (JSON/CSV)
* 사용자 → 타 서비스 이동 지원

### 14.5 거부 요청 (Right to Object)

* Direct marketing 거부
* Automated decision-making 거부

---

# 📢 15. Incident Notification

### 15.1 보안 사고 발생 시:

```
GDPR → 72시간 내 신고
PIPA → 지체 없이 공지
CCPA → 사용자의 명시적 통지 필요
APPI → 3일 이내 신고
```

### 15.2 Notification Content

* Nature of breach
* Affected individuals count
* Likely consequences
* Mitigation measures
* Contact point

### 15.3 Notification Channels

* Email (primary)
* Status page
* In-app notification
* Press release (severe cases)

---

# 👨‍⚖️ 16. Roles & Responsibilities

### 16.1 Data Protection Officer (DPO)

* GDPR/PIPA compliance oversight
* DPIA review & approval
* User rights request handling
* Authority liaison

### 16.2 Legal Team

* Contract review
* Terms of Service updates
* Regulatory monitoring
* Litigation management

### 16.3 Engineering Team

* Privacy by Design implementation
* Technical controls
* Data deletion automation
* Security measures

### 16.4 Compliance Team

* Policy documentation
* Training & awareness
* Audit coordination
* Risk assessment

---

# 📚 17. Training & Awareness

### 17.1 Mandatory Training

* All employees: Data Protection Basics (annually)
* Engineering: Privacy by Design (bi-annually)
* Customer support: User Rights Handling (quarterly)

### 17.2 Training Topics

* GDPR/PIPA fundamentals
* User rights handling
* Incident response
* Secure coding practices

---

# 🏁 18. 결론

MegaCity Legal & Compliance Handbook은 DreamSeedAI가 글로벌 시장에서  
신뢰받는 AI 교육 플랫폼이 되기 위해 반드시 따라야 할 **법무·규제·데이터 보호 표준**을 정의한 문서입니다.

이 핸드북은 정기적으로 업데이트되며, 새로운 규제나 법률 변경사항이 발생할 때마다  
즉시 반영하여 MegaCity의 글로벌 규제 준수 상태를 유지합니다.

모든 팀원은 본 핸드북을 숙지하고, 의문사항이 있을 경우 Legal/Compliance 팀에  
즉시 문의해야 합니다.
