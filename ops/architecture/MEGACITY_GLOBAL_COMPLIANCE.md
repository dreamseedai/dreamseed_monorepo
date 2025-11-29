# 📘 DreamSeedAI MegaCity – Global Compliance Manual

## GDPR · PIPA · COPPA · FERPA · CCPA 준수 핸드북 (전 세계 개인정보 규제 대응)

**버전:** 1.0  
**작성일:** 2025-11-22  
**작성자:** DreamSeedAI Compliance · Legal · Security Team

---

# 📌 0. 개요 (Overview)

DreamSeedAI MegaCity는 **9개 Zone + AI Cluster + K-Zone(문화/멀티모달 AI)** 으로 구성된 글로벌 교육·문화 플랫폼입니다.

글로벌 확장을 위해 다음과 같은 다양한 국가·지역의 개인정보법을 동시에 준수해야 합니다:

## 적용 규제 범위

```
┌─────────────────────────────────────────────────────────┐
│           Global Compliance Framework                   │
└─────────────┬───────────────────────────────────────────┘
              │
    ┌─────────┼──────────┬──────────┬──────────┬──────────┐
    │         │          │          │          │          │
    ▼         ▼          ▼          ▼          ▼          │
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐      │
│  GDPR  ││  PIPA  ││ COPPA  ││ FERPA  ││  CCPA  │      │
│  (EU)  ││(Korea) ││  (US)  ││  (US)  ││  (US)  │      │
└────────┘└────────┘└────────┘└────────┘└────────┘      │
    │         │          │          │          │          │
    └─────────┴──────────┴──────────┴──────────┴──────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   ISO 27001/27701    │
              │  (Global Standards)  │
              └──────────────────────┘
```

### 규제 요약

| 규제 | 관할 | 적용 대상 | 주요 요구사항 |
|------|------|----------|--------------|
| **GDPR** | EU | EU 거주자 데이터 처리 | 동의, 권리 보장, DPIA, 국제 전송 규칙 |
| **PIPA** | 한국 | 한국 사용자 | 주민번호 금지, 만 14세 미만 보호, 제3자 제공 기록 |
| **COPPA** | 미국 | 13세 미만 아동 | 보호자 동의, 광고 금지, 삭제 요청 |
| **FERPA** | 미국 | 교육 기록 | 학생 성적 보호, 열람권, 접근 제한 |
| **CCPA** | 캘리포니아 | CA 거주자 | 알 권리, 삭제권, Opt-out |

본 문서는 MegaCity 전체가 따라야 하는 **글로벌 개인정보 보호 기준(Global Compliance Framework)** 을 정의합니다.

---

# 🧭 1. Compliance Framework Overview

MegaCity의 개인정보·데이터 보호 체계는 **5개 핵심 원칙**으로 구성됩니다.

## 1.1 핵심 원칙

```
┌─────────────────────────────────────────────────────────┐
│  1. Data Minimization (최소 수집)                       │
│     - 필수 정보만 수집 (이메일, 역할, 학습 데이터)     │
│     - 주민번호, GPS 위치 등 민감정보 수집 금지         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  2. Purpose Limitation (목적 제한)                      │
│     - 수집 목적 명시 및 동의                           │
│     - 목적 외 사용 금지                                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  3. Retention Limits (보존 기간 제한)                   │
│     - PII: 3년                                         │
│     - Logs: 1년                                        │
│     - AI 업로드 파일: 7~30일                           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  4. Security Measures (보안 조치)                       │
│     - Encryption (At-rest, In-transit, Column-level)   │
│     - Access Control (RBAC, PBAC, RLS)                 │
│     - Audit Logging                                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  5. User Rights (사용자 권리 보장)                      │
│     - Right to Access (열람권)                         │
│     - Right to Erasure (삭제권)                        │
│     - Right to Portability (이동권)                    │
│     - Right to Restrict Processing (처리 제한권)       │
└─────────────────────────────────────────────────────────┘
```

모든 Zone(UnivPrepAI, SkillPrepAI, MediaPrepAI, K-Zone 등)에서 동일하게 적용됩니다.

## 1.2 Compliance 운영 체계

```
┌──────────────────┐
│ Compliance Team  │  법률·규제 검토, 정책 수립
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Security Team   │  보안 조치 구현 (암호화, 접근제어)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Engineering     │  시스템 구현 (GDPR API, Audit Log)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Operations      │  일일 모니터링, 사용자 요청 처리
└──────────────────┘
```

---

# 🔐 2. GDPR (EU General Data Protection Regulation)

GDPR은 **세계에서 가장 강력한 개인정보 규제**이며, EU 거주자 데이터를 처리하는 모든 기업에 적용됩니다.

## 2.1 GDPR 핵심 원칙 (Article 5)

| 원칙 | 설명 | DreamSeedAI 구현 |
|------|------|------------------|
| **Lawfulness** (적법성) | 법적 근거 필요 (동의, 계약, 법적 의무) | 사용자 동의 + 서비스 계약 |
| **Fairness** (공정성) | 사용자에게 불리하지 않게 처리 | 투명한 정책 공개 |
| **Transparency** (투명성) | 처리 방법 명확히 고지 | Privacy Policy, 동의 화면 |
| **Purpose Limitation** (목적 제한) | 수집 목적 외 사용 금지 | 학습 목적만 사용 |
| **Data Minimization** (최소화) | 필요한 정보만 수집 | 이메일, 역할만 수집 |
| **Accuracy** (정확성) | 데이터 정확성 유지 | 사용자 정정 기능 제공 |
| **Storage Limitation** (보존 제한) | 필요 기간만 보존 | PII 3년, Logs 1년 |
| **Integrity & Confidentiality** (기밀성) | 보안 조치 | 암호화, 접근제어 |
| **Accountability** (책임성) | 준수 증명 의무 | Audit Log, DPIA 문서 |

## 2.2 DreamSeedAI GDPR 준수 항목

### 2.2.1 최소 수집 (Data Minimization)

```python
# 회원가입 시 최소 정보만 수집
@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    # 필수 항목만 수집
    required_fields = {"email", "password", "name", "role"}
    
    # 불필요한 정보 거부
    if set(request.dict(exclude_unset=True).keys()) > required_fields:
        raise HTTPException(400, "GDPR violation: Collecting unnecessary data")
    
    user = await create_user(request)
    return {"user_id": user.id}
```

### 2.2.2 명확한 동의 (Consent - Article 7)

```python
@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    # 명시적 동의 필수
    if not request.consent_privacy_policy:
        raise HTTPException(400, "Privacy policy consent required (GDPR Article 7)")
    
    if not request.consent_data_processing:
        raise HTTPException(400, "Data processing consent required (GDPR Article 7)")
    
    # 동의 기록 저장
    await db.execute(
        """
        INSERT INTO user_consents (user_id, consent_type, consented_at, ip_address)
        VALUES (:user_id, :type, NOW(), :ip)
        """,
        {
            "user_id": user.id,
            "type": "privacy_policy",
            "ip": request.client_ip
        }
    )
    
    return {"user_id": user.id}
```

### 2.2.3 데이터 보존 기간 (Storage Limitation - Article 5(1)(e))

| 데이터 유형 | 보존 기간 | 법적 근거 |
|------------|----------|----------|
| **PII** (이메일, 이름, 전화번호) | 3년 | 서비스 제공 + 법적 의무 |
| **로그** (Access, Error) | 1년 | 보안 + 감사 |
| **AI 업로드 파일** | 7~30일 | 서비스 제공 |
| **시험 성적** | 5년 (익명화 후 보존) | 교육 기록 보존 |

```python
@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def enforce_gdpr_retention():
    """GDPR 보존 기간 자동 적용"""
    
    # PII 3년 후 삭제
    await db.execute(
        """
        UPDATE users SET
            email = 'deleted_' || id || '@gdpr.local',
            phone_encrypted = NULL,
            name = 'GDPR Deleted User',
            gdpr_deleted_at = NOW()
        WHERE created_at < NOW() - INTERVAL '3 years'
          AND gdpr_deleted_at IS NULL
        """
    )
    
    # 로그 1년 후 삭제
    await db.execute(
        "DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '1 year'"
    )
    
    # AI 업로드 파일 30일 후 삭제
    await r2_client.delete_objects_older_than("/tmp/ai/", days=30)
```

### 2.2.4 사용자 권리 (GDPR Chapter III)

#### Right to Access (Article 15)

```python
@app.get("/api/v1/gdpr/access")
async def gdpr_right_to_access(user: User = Depends(get_current_user)):
    """GDPR Article 15: Right to Access"""
    data = {
        "personal_info": {
            "email": user.email,
            "name": user.name,
            "phone": await decrypt_phone(user.id),
            "role": user.role,
            "created_at": user.created_at.isoformat()
        },
        "processing_purposes": [
            "Educational service provision",
            "AI-powered tutoring",
            "Exam management"
        ],
        "data_categories": ["Identity", "Contact", "Academic records", "AI usage logs"],
        "recipients": ["DreamSeedAI", "Cloudflare (CDN)", "AWS (Cloud storage)"],
        "retention_period": "3 years from account creation",
        "rights": [
            "Right to rectification (Article 16)",
            "Right to erasure (Article 17)",
            "Right to restrict processing (Article 18)",
            "Right to data portability (Article 20)"
        ],
        "exam_history": await get_exam_attempts(user.id),
        "ai_usage": await get_ai_requests(user.id),
        "audit_log": await get_audit_logs(user.id, last_n=100)
    }
    
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": "attachment; filename=gdpr_data_access.json"}
    )
```

#### Right to Erasure (Article 17 - "Right to be Forgotten")

```python
@app.delete("/api/v1/gdpr/erasure")
async def gdpr_right_to_erasure(user: User = Depends(get_current_user)):
    """GDPR Article 17: Right to Erasure"""
    
    # 1. PII 삭제/익명화
    await db.execute(
        """
        UPDATE users SET
            email = 'erased_' || id || '@gdpr.local',
            phone_encrypted = NULL,
            name = 'GDPR Erased User',
            gdpr_erased = TRUE,
            gdpr_erased_at = NOW()
        WHERE id = :id
        """,
        {"id": user.id}
    )
    
    # 2. Audit Log 익명화
    await db.execute(
        "UPDATE audit_log SET user_id = NULL WHERE user_id = :id",
        {"id": user.id}
    )
    
    # 3. AI 출력물 삭제
    await r2_client.delete_prefix(f"/users/{user.id}/")
    
    # 4. 시험 데이터 익명화 (통계는 유지 - Legitimate Interest)
    await db.execute(
        "UPDATE exam_attempts SET user_id = NULL, anonymized = TRUE WHERE user_id = :id",
        {"id": user.id}
    )
    
    # 5. 삭제 증명서 발급
    certificate = {
        "user_id": user.id,
        "email": user.email,
        "erased_at": datetime.now().isoformat(),
        "data_categories_erased": [
            "Personal identity",
            "Contact information",
            "AI usage logs",
            "Uploaded files"
        ],
        "retained_data": [
            "Anonymized exam statistics (GDPR Article 17(3)(d) - Public interest)"
        ]
    }
    
    return certificate
```

#### Right to Data Portability (Article 20)

```python
@app.get("/api/v1/gdpr/portability")
async def gdpr_right_to_portability(user: User = Depends(get_current_user)):
    """GDPR Article 20: Right to Data Portability"""
    
    # 구조화된 기계 판독 가능 형식 (JSON)
    portable_data = {
        "user": {
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "created_at": user.created_at.isoformat()
        },
        "exams": await get_exam_attempts_portable(user.id),
        "ai_conversations": await get_ai_conversations_portable(user.id),
        "learning_progress": await get_learning_progress(user.id)
    }
    
    return Response(
        content=json.dumps(portable_data, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=gdpr_portable_data.json"}
    )
```

#### Right to Restrict Processing (Article 18)

```python
@app.post("/api/v1/gdpr/restrict-processing")
async def gdpr_restrict_processing(user: User = Depends(get_current_user)):
    """GDPR Article 18: Right to Restrict Processing"""
    
    await db.execute(
        "UPDATE users SET processing_restricted = TRUE WHERE id = :id",
        {"id": user.id}
    )
    
    # AI 기능 비활성화
    await redis.setex(f"user:{user.id}:restricted", 86400 * 365, "true")
    
    return {"status": "restricted", "message": "Data processing restricted as per GDPR Article 18"}
```

### 2.2.5 DPIA (Data Protection Impact Assessment - Article 35)

다음 기능 추가 시 **반드시 DPIA 수행**:

```
✅ DPIA 필수 항목:
   - 얼굴 분석 (PoseNet)
   - 음성 분석 (Whisper)
   - Multi-modal AI 모델
   - 위치 기반 서비스
   - 대규모 프로파일링
```

#### DPIA 템플릿

```markdown
# DPIA - K-Zone PoseNet Dance Analysis

**Date:** 2025-11-22  
**Assessor:** DreamSeedAI Data Protection Officer

## 1. Description
K-Zone Dance Lab uses PoseNet to analyze dance movements from video.

## 2. Personal Data Processed
- Video recording (temporary)
- Pose keypoints (33 landmarks)
- User ID (linked to account)

## 3. Purpose
Educational dance learning and scoring.

## 4. Legal Basis
- User consent (GDPR Article 6(1)(a))

## 5. Data Minimization
- Only pose keypoints stored (not video)
- Video deleted after 7 days

## 6. Risks
- Risk 1: Unauthorized access to video → Mitigation: R2 private bucket + TLS
- Risk 2: Re-identification from pose data → Mitigation: No facial landmarks stored

## 7. Safeguards
- Encryption at rest (R2 server-side encryption)
- Encryption in transit (TLS 1.3)
- Access control (user can only view own data)
- Auto-deletion (7 days)

## 8. Conclusion
Risks are minimal and adequately mitigated. Proceed with implementation.

**Approved by:** DPO (Data Protection Officer)
```

### 2.2.6 국제 데이터 전송 (International Transfer - Chapter V)

```python
# EU 사용자는 EU 저장소 사용
if user.country in EU_COUNTRIES:
    storage_region = "eu-west-1"
    llm_endpoint = "https://dreamseed-eu.openai.azure.com"
else:
    storage_region = "us-east-1"
    llm_endpoint = "https://api.openai.com"

# Standard Contractual Clauses (SCC) 적용
# Cloudflare, AWS와 SCC 체결 필요
```

---

# 🇰🇷 3. PIPA (대한민국 개인정보보호법)

한국 사용자 대상 서비스는 **PIPA를 엄격히** 따라야 합니다.

## 3.1 PIPA 기본 원칙

| 원칙 | 설명 | DreamSeedAI 구현 |
|------|------|------------------|
| **목적 외 이용 금지** | 수집 목적 외 사용 불가 | 학습 목적만 사용 |
| **최소 수집** | 필요한 정보만 수집 | 이메일, 역할만 수집 |
| **수탁사 관리 의무** | 제3자 처리 시 계약 필요 | Cloudflare, AWS 계약 |
| **처리방침 공개 의무** | 웹사이트에 게시 | `/privacy-policy` 페이지 |
| **안전성 확보 조치** | 암호화, 접근제어 | pgcrypto, RBAC, RLS |

## 3.2 DreamSeedAI PIPA 준수 사항

### 3.2.1 주민등록번호 저장 금지 (법 제24조의2)

```python
# 주민등록번호 수집 절대 금지
PROHIBITED_FIELDS = ["ssn", "jumin_number", "resident_registration_number"]

@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    # 주민번호 수집 시도 차단
    for field in PROHIBITED_FIELDS:
        if hasattr(request, field):
            raise HTTPException(400, "PIPA 위반: 주민등록번호 수집 금지 (법 제24조의2)")
    
    user = await create_user(request)
    return {"user_id": user.id}
```

### 3.2.2 고유식별정보 암호화 (법 제24조)

```sql
-- 휴대폰 번호 암호화 (고유식별정보)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE users ADD COLUMN phone_encrypted BYTEA;

UPDATE users 
SET phone_encrypted = pgp_sym_encrypt(phone, current_setting('app.encryption_key'))
WHERE phone IS NOT NULL;
```

### 3.2.3 개인정보 영향평가 (PIA - 법 제33조)

```
✅ PIA 실시 대상:
   - 5만 명 이상 정보주체 정보 처리
   - 주민번호, 여권번호, 면허번호 등 고유식별정보 처리
   - 민감정보(건강, 생체인식 등) 처리
```

### 3.2.4 제3자 제공 기록 (법 제22조)

```python
# 제3자 제공 기록 (5년 보존)
@app.post("/api/v1/data/share-with-third-party")
async def share_data_with_third_party(request: ThirdPartyShareRequest):
    # 사용자 동의 확인
    consent = await db.fetchone(
        "SELECT * FROM third_party_consents WHERE user_id = :user_id AND recipient = :recipient",
        {"user_id": request.user_id, "recipient": request.recipient}
    )
    
    if not consent:
        raise HTTPException(403, "사용자 동의 필요 (PIPA 법 제17조)")
    
    # 제3자 제공 기록
    await db.execute(
        """
        INSERT INTO third_party_sharing_log (
            user_id, recipient, data_categories, purpose, shared_at, expires_at
        ) VALUES (:user_id, :recipient, :data_categories, :purpose, NOW(), :expires_at)
        """,
        {
            "user_id": request.user_id,
            "recipient": request.recipient,
            "data_categories": json.dumps(request.data_categories),
            "purpose": request.purpose,
            "expires_at": datetime.now() + timedelta(days=1825)  # 5년 보존
        }
    )
    
    return {"status": "shared"}
```

### 3.2.5 만 14세 미만 보호 (법 제22조)

```python
@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    # 만 14세 미만 체크
    age = calculate_age(request.birthdate)
    
    if age < 14:
        # 법정대리인(학부모) 동의 필요
        return {
            "status": "pending_parent_consent",
            "message": "만 14세 미만은 법정대리인 동의가 필요합니다 (PIPA 법 제22조)",
            "next_step": "parent_approval"
        }
    
    # 일반 회원가입 진행
    user = await create_user(request)
    return {"status": "success", "user_id": user.id}
```

---

# 🇺🇸 4. COPPA (미국 아동 온라인 개인정보 보호법)

K-Zone, Phonics/Hangul 학습 기능 등은 **COPPA 적용 가능**.

## 4.1 COPPA 규정 요약

| 요구사항 | 설명 | DreamSeedAI 구현 |
|---------|------|------------------|
| **13세 미만 보호자 동의** | 아동 정보 수집 시 부모 동의 필수 | Parent-Student 연결 |
| **광고/추적 금지** | 행동 기반 광고 금지 | 광고 없음 (교육 서비스) |
| **삭제 요청** | 부모 요청 시 즉시 삭제 | GDPR Right to Erasure 구현 |
| **보안 조치** | 아동 데이터 보호 | 암호화, 접근제어 |

## 4.2 DreamSeedAI COPPA 준수 사항

### 4.2.1 보호자 동의

```python
@app.post("/api/v1/auth/register-child")
async def register_child(request: ChildRegisterRequest):
    # 13세 미만 체크
    age = calculate_age(request.birthdate)
    
    if age < 13:
        # COPPA 적용: 보호자 동의 필수
        if not request.parent_email:
            raise HTTPException(400, "COPPA: Parent email required for children under 13")
        
        # 보호자에게 승인 요청 이메일 발송
        approval_token = generate_approval_token()
        await send_email(
            to=request.parent_email,
            subject="[DreamSeedAI] Child Account Approval Required (COPPA)",
            body=f"Your child wants to create an account. Approve: {FRONTEND_URL}/approve/{approval_token}"
        )
        
        return {
            "status": "pending_parent_approval",
            "message": "Email sent to parent for approval (COPPA compliance)"
        }
    
    # 13세 이상은 일반 회원가입
    user = await create_user(request)
    return {"user_id": user.id}
```

### 4.2.2 광고/추적 금지

```python
# COPPA: 13세 미만은 행동 기반 광고 금지
if user.age < 13:
    # 광고 ID 생성 금지
    # Google Analytics 비활성화
    # 제3자 쿠키 차단
    pass
```

### 4.2.3 보호자 삭제 요청

```python
@app.delete("/api/v1/coppa/delete-child-account")
async def delete_child_account(
    child_id: int,
    parent: User = Depends(get_current_user)
):
    # 부모-자녀 관계 확인
    link = await db.fetchone(
        "SELECT * FROM parent_student_links WHERE parent_id = :parent_id AND student_id = :child_id",
        {"parent_id": parent.id, "child_id": child_id}
    )
    
    if not link:
        raise HTTPException(403, "Not authorized to delete this account")
    
    # COPPA: 즉시 삭제 (30일 유예 없음)
    await hard_delete_user(child_id)
    
    return {"status": "deleted", "message": "Child account deleted per COPPA request"}
```

---

# 🎓 5. FERPA (미국 교육 기록 보호법)

미국 교육기관과의 제휴, 글로벌 확장 대비하여 **FERPA 준수**가 필요.

## 5.1 FERPA 핵심 사항

| 요구사항 | 설명 | DreamSeedAI 구현 |
|---------|------|------------------|
| **교육 기록 보호** | 학생 성적, 시험 결과 보호 | RLS, Parent-Student 연결 |
| **열람권** | 부모/학생에게 열람권 보장 | GDPR Right to Access 구현 |
| **동의 없는 공개 금지** | 제3자 공개 시 동의 필요 | 제3자 제공 기록 시스템 |
| **정확성 보장** | 부정확한 정보 정정 | Right to Rectification 구현 |

## 5.2 DreamSeedAI FERPA 준수 사항

### 5.2.1 교육 기록 분류

```python
# FERPA 보호 대상 데이터
FERPA_PROTECTED_DATA = [
    "exam_attempts",      # 시험 시도 기록
    "exam_scores",        # 성적
    "learning_progress",  # 학습 진도
    "teacher_feedback",   # 교사 피드백
    "behavioral_records"  # 행동 기록
]
```

### 5.2.2 접근 제어

```sql
-- FERPA RLS 정책: 학생 성적은 본인 + 부모 + 교사만 조회
CREATE POLICY ferpa_exam_scores_policy ON exam_attempts
FOR SELECT USING (
    auth.uid() = user_id  -- 본인
    OR auth.uid() IN (
        SELECT parent_id FROM parent_student_links 
        WHERE student_id = exam_attempts.user_id AND status = 'approved'
    )  -- 승인된 학부모
    OR auth.uid() IN (
        SELECT teacher_id FROM teacher_student_assignments 
        WHERE student_id = exam_attempts.user_id
    )  -- 담당 교사
    OR EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND role = 'sys_admin'
    )  -- 시스템 관리자 (FERPA 예외)
);
```

### 5.2.3 제3자 공개 제한

```python
@app.get("/api/v1/ferpa/student-records/{student_id}")
async def get_student_records(
    student_id: int,
    requester: User = Depends(get_current_user)
):
    # FERPA: 승인된 관계자만 조회 가능
    authorized = await check_ferpa_authorization(requester.id, student_id)
    
    if not authorized:
        raise HTTPException(403, "FERPA violation: Unauthorized access to education records")
    
    records = await get_student_educational_records(student_id)
    
    # FERPA 접근 로그 기록
    await log_ferpa_access(requester.id, student_id, "view_records")
    
    return records
```

### 5.2.4 성적 데이터 보존

```python
@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def ferpa_retention():
    """FERPA: 교육 기록 5년 보존 후 익명화"""
    await db.execute(
        """
        UPDATE exam_attempts SET
            user_id = NULL,
            anonymized = TRUE,
            ferpa_anonymized_at = NOW()
        WHERE created_at < NOW() - INTERVAL '5 years'
          AND anonymized = FALSE
        """
    )
```

---

# 🇺🇸 6. CCPA (캘리포니아 소비자 프라이버시 법)

## 6.1 CCPA 권리 (GDPR과 유사)

| 권리 | 설명 | DreamSeedAI 구현 |
|------|------|------------------|
| **Right to Know** | 수집 정보 알 권리 | GDPR Right to Access 재사용 |
| **Right to Delete** | 삭제 요청 권리 | GDPR Right to Erasure 재사용 |
| **Right to Opt-out** | 판매 거부 권리 | 개인정보 판매 없음 (N/A) |
| **Non-discrimination** | 권리 행사 시 차별 금지 | 서비스 동일하게 제공 |

## 6.2 DreamSeedAI CCPA 대응

### 6.2.1 개인정보 판매 없음

```python
# CCPA: DreamSeedAI는 개인정보를 제3자에게 판매하지 않음
# "Do Not Sell My Personal Information" 옵트아웃 불필요

# Privacy Policy에 명시:
"""
DreamSeedAI does not sell personal information to third parties.
We do not share data with advertisers or data brokers.
"""
```

### 6.2.2 삭제 요청 처리 (30일 이내)

```python
@app.delete("/api/v1/ccpa/delete")
async def ccpa_delete_request(user: User = Depends(get_current_user)):
    """CCPA: 삭제 요청 (30일 이내 처리)"""
    
    # 삭제 요청 기록
    await db.execute(
        """
        INSERT INTO deletion_requests (user_id, request_type, status, requested_at)
        VALUES (:user_id, 'ccpa', 'pending', NOW())
        """,
        {"user_id": user.id}
    )
    
    # 즉시 처리 (GDPR과 동일)
    await gdpr_right_to_erasure(user)
    
    return {
        "status": "deleted",
        "message": "Account deleted per CCPA request (processed within 30 days)"
    }
```

---

# 🔒 7. Security Controls (보안 조건)

## 7.1 암호화 (Encryption)

### 7.1.1 At-rest Encryption

```bash
# LUKS 볼륨 암호화
cryptsetup luksFormat /dev/sdb
cryptsetup open /dev/sdb pgdata
mkfs.ext4 /dev/mapper/pgdata
mount /dev/mapper/pgdata /var/lib/postgresql/data
```

```yaml
# PostgreSQL TDE (Transparent Data Encryption)
# pgcrypto for column-level encryption
CREATE EXTENSION pgcrypto;

ALTER TABLE users ADD COLUMN phone_encrypted BYTEA;
UPDATE users SET phone_encrypted = pgp_sym_encrypt(phone, 'encryption_key');
```

### 7.1.2 In-transit Encryption

```yaml
# PostgreSQL SSL
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_min_protocol_version = 'TLSv1.2'

# Nginx TLS 1.2+
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256';
```

### 7.1.3 Column-level Encryption

```sql
-- PII 컬럼 암호화
CREATE OR REPLACE FUNCTION encrypt_pii(data TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql;

-- 복호화 함수
CREATE OR REPLACE FUNCTION decrypt_pii(encrypted_data BYTEA)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(encrypted_data, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## 7.2 접근 제어 (Access Control)

### 7.2.1 RBAC + PBAC + RLS

```python
# RBAC (Role-Based Access Control)
ROLES = ["student", "parent", "teacher", "org_admin", "zone_admin", "sys_admin"]

# PBAC (Policy-Based Access Control)
if exam.active and user.role == "student":
    deny(ai_tutor_access)

# RLS (Row-Level Security)
CREATE POLICY student_data_policy ON users
FOR SELECT USING (id = auth.uid() OR auth.uid() IN (SELECT parent_id FROM parent_student_links));
```

### 7.2.2 Admin 권한 재검증 (월 1회)

```python
@app.on_event("startup")
@repeat_every(seconds=2592000)  # 30일마다
async def revalidate_admin_access():
    """Admin 권한 재검증"""
    admins = await db.fetch_all("SELECT * FROM users WHERE role IN ('sys_admin', 'zone_admin')")
    
    for admin in admins:
        # CTO/VP 승인 요청
        await send_email(
            to="cto@dreamseedai.com",
            subject=f"[Compliance] Admin Access Re-approval: {admin.email}",
            body=f"Please re-approve admin access for {admin.email}. Expires in 7 days."
        )
```

## 7.3 로깅/감사 (Audit)

### 7.3.1 Audit Log 보존

```python
@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def audit_log_retention():
    """Audit Log 1년 보존"""
    
    # 1년 이상 된 일반 로그 삭제
    await db.execute(
        "DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '1 year' AND action NOT IN ('login', 'grant_role')"
    )
    
    # 2년 이상 된 보안 로그 삭제
    await db.execute(
        "DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '2 years'"
    )
```

### 7.3.2 PII 익명화 후 전송

```python
def anonymize_audit_log(log: dict) -> dict:
    """EU 사용자 Audit Log 익명화"""
    if log["user_country"] in EU_COUNTRIES:
        log["user_id"] = hash_user_id(log["user_id"])  # 해시화
        log["ip_address"] = mask_ip(log["ip_address"])  # 마스킹
    
    return log
```

---

# 🧬 8. Data Lifecycle Management

## 8.1 수집 (Collection)

```python
# 최소 정보 수집
REQUIRED_FIELDS = {"email", "password", "name", "role"}

# 민감정보는 Opt-in
SENSITIVE_FIELDS = {"phone", "address", "birthdate"}

@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    # 민감정보 수집 시 동의 확인
    if request.phone and not request.consent_phone:
        raise HTTPException(400, "Phone collection requires consent")
    
    user = await create_user(request)
    return {"user_id": user.id}
```

## 8.2 저장 (Storage)

```python
# Cloudflare R2 (Private Bucket)
await r2_client.upload(
    key=f"users/{user_id}/profile.jpg",
    body=file,
    acl="private"  # 비공개
)

# Cold Storage → Backblaze B2
await b2_client.upload(
    key=f"archive/{user_id}/old_data.json",
    body=data,
    storage_class="GLACIER"  # 장기 보존
)
```

## 8.3 처리 (Processing)

```python
@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def cleanup_ai_temp_files():
    """AI 처리 파일 24~72시간 후 자동 삭제"""
    
    # Whisper 임시 파일 삭제 (72시간)
    await r2_client.delete_objects_older_than("/tmp/whisper/", days=3)
    
    # PoseNet 임시 파일 삭제 (24시간)
    await r2_client.delete_objects_older_than("/tmp/posenet/", days=1)
```

## 8.4 보존 (Retention)

| 데이터 유형 | 보존 기간 | 법적 근거 |
|------------|----------|----------|
| **PII** | 3년 | GDPR, PIPA |
| **로그** | 1년 | 보안 감사 |
| **학습 데이터 (비PII)** | 장기 보존 가능 | 서비스 개선 |
| **시험 성적** | 5년 (익명화 후) | FERPA |

## 8.5 삭제 (Erasure)

```python
@app.delete("/api/v1/account/delete")
async def delete_account(user: User = Depends(get_current_user)):
    """계정 삭제 (Soft-delete → 30일 후 Hard-delete)"""
    
    # 1. Soft-delete (즉시)
    await db.execute(
        "UPDATE users SET deleted_at = NOW(), deleted = TRUE WHERE id = :id",
        {"id": user.id}
    )
    
    # 2. 30일 유예 기간 (복구 가능)
    await schedule_hard_delete(user.id, days=30)
    
    return {"status": "scheduled_for_deletion", "hard_delete_at": datetime.now() + timedelta(days=30)}

@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def hard_delete_expired_accounts():
    """30일 경과 계정 Hard-delete"""
    await db.execute(
        """
        DELETE FROM users 
        WHERE deleted = TRUE 
          AND deleted_at < NOW() - INTERVAL '30 days'
        """
    )
```

---

# 🤖 9. AI Compliance

## 9.1 AI Safety Layer

```python
# 욕설/폭력/혐오 자동 필터링
from transformers import pipeline

toxicity_detector = pipeline("text-classification", model="unitary/toxic-bert")

async def check_ai_safety(text: str) -> dict:
    result = toxicity_detector(text)[0]
    
    if result["label"] == "toxic" and result["score"] > 0.7:
        return {"is_safe": False, "reason": "Toxic content detected"}
    
    return {"is_safe": True}
```

## 9.2 AI Fairness

```python
# 편향 탐지
bias_detector = pipeline("text-classification", model="unbiased/bias-detection")

async def check_ai_bias(text: str) -> dict:
    result = bias_detector(text)[0]
    
    if result["label"] == "biased" and result["score"] > 0.7:
        await log_ai_safety_issue("bias_detected", text)
        return {"is_biased": True}
    
    return {"is_biased": False}
```

## 9.3 모델 교체 DPIA

```markdown
# DPIA - vLLM Model Upgrade (Qwen2.5-32B → Qwen2.5-72B)

## 1. Impact
- Larger model may generate more complex responses
- Potential for increased bias in certain domains

## 2. Mitigation
- Blue-Green deployment (instant rollback)
- Bias testing on educational datasets
- 48-hour monitoring before full rollout

## 3. Approval
- AI Lead: ✅
- DPO: ✅
```

---

# 📝 10. User Rights Handling (권리 행사 처리 프로세스)

## 10.1 요청 절차

사용자는 다음 항목에 대해 요청 가능:

```
✅ Access (열람) → 30일 이내 제공
✅ Correction (정정) → 즉시 처리
✅ Deletion (삭제) → 즉시 Soft-delete, 30일 후 Hard-delete
✅ Export (이동) → 즉시 제공 (JSON)
✅ Restriction (처리 제한) → 즉시 적용
```

## 10.2 요청 검증

```python
@app.post("/api/v1/data-rights/request")
async def submit_data_rights_request(
    request: DataRightsRequest,
    user: User = Depends(get_current_user)
):
    # 본인 확인 (2FA)
    if request.request_type in ["deletion", "restriction"]:
        if not request.totp_code:
            raise HTTPException(400, "2FA required for sensitive requests")
        
        if not verify_totp(user.totp_secret, request.totp_code):
            raise HTTPException(403, "Invalid 2FA code")
    
    # 요청 기록
    rights_request = await db.execute(
        """
        INSERT INTO data_rights_requests (user_id, request_type, status, requested_at)
        VALUES (:user_id, :type, 'pending', NOW())
        RETURNING *
        """,
        {"user_id": user.id, "type": request.request_type}
    )
    
    # 처리 (대부분 즉시)
    if request.request_type == "access":
        data = await gdpr_right_to_access(user)
        await db.execute(
            "UPDATE data_rights_requests SET status = 'completed', completed_at = NOW() WHERE id = :id",
            {"id": rights_request.id}
        )
        return data
    
    elif request.request_type == "deletion":
        await gdpr_right_to_erasure(user)
        return {"status": "deleted"}
    
    # ... (기타 권리)
```

## 10.3 처리 SLA

| 권리 | GDPR SLA | CCPA SLA | DreamSeedAI SLA |
|------|---------|---------|-----------------|
| **Access** | 1개월 | N/A | 즉시 |
| **Deletion** | 1개월 | 45일 | 즉시 (Soft) + 30일 (Hard) |
| **Portability** | 1개월 | N/A | 즉시 |
| **Restriction** | 즉시 | N/A | 즉시 |

---

# 🧾 11. Documentation & Evidence (문서화 및 증거)

## 11.1 Compliance 문서 저장

규제 준수 증거(Evidence)는 다음 경로에 저장:

```
/docs/compliance/
  ├── gdpr/
  │   ├── dpia_posenet.md
  │   ├── dpia_whisper.md
  │   ├── scc_cloudflare.pdf
  │   └── scc_aws.pdf
  ├── pipa/
  │   ├── pia_report_2025.pdf
  │   ├── third_party_agreements/
  │   └── consent_records/
  ├── coppa/
  │   ├── parent_consent_logs.csv
  │   └── child_account_policies.md
  ├── ferpa/
  │   ├── ferpa_compliance_checklist.md
  │   └── access_logs/
  └── ccpa/
      ├── do_not_sell_policy.md
      └── deletion_requests/

/docs/audit/
  ├── 2025_q1_compliance_audit.pdf
  ├── 2025_q2_compliance_audit.pdf
  └── annual_compliance_report_2025.pdf
```

## 11.2 변경 이력 관리

```markdown
# Compliance Policy Change Log

## v1.2 (2025-11-22)
- GDPR DPIA 추가: K-Zone PoseNet
- PIPA 만 14세 미만 보호 강화
- COPPA 보호자 동의 프로세스 개선

## v1.1 (2025-10-15)
- FERPA RLS 정책 적용
- CCPA 삭제 요청 30일 SLA 설정

## v1.0 (2025-09-01)
- 초기 Compliance Framework 수립
```

## 11.3 연례 Compliance Review

```
✅ 연 1회 Compliance Review 필수
   - 모든 정책 문서 검토
   - DPIA 업데이트
   - 제3자 계약 갱신
   - Audit Log 분석
   - 위반 사항 확인

✅ 분기별 Internal Audit
   - 보안 조치 점검
   - 암호화 상태 확인
   - 접근 제어 검증
```

---

# 🏁 12. 결론

이 **Global Compliance Manual**은 DreamSeedAI MegaCity의 모든 Zone과 기능이 **국내(PIPA) · 국제(GDPR) · 아동(COPPA) · 교육(FERPA) · 지역(CCPA)** 규정을 모두 준수하도록 보안·데이터·AI·정책·운영을 통합한 **가장 중요한 준수 기준 문서**입니다.

## Compliance 준수 체크리스트

```
□ GDPR (EU)
  □ 최소 수집 원칙 적용
  □ 명확한 동의 획득
  □ DPIA 수행 (얼굴/음성 분석)
  □ 사용자 권리 API 구현 (Access, Erasure, Portability, Restriction)
  □ 국제 데이터 전송 SCC 체결
  □ 보존 기간 준수 (PII 3년, Logs 1년)

□ PIPA (한국)
  □ 주민등록번호 수집 금지
  □ 고유식별정보 암호화 (pgcrypto)
  □ 만 14세 미만 법정대리인 동의
  □ 제3자 제공 기록 (5년 보존)
  □ 개인정보 처리방침 공개

□ COPPA (미국 아동)
  □ 13세 미만 보호자 동의
  □ 광고/추적 금지
  □ 즉시 삭제 요청 처리

□ FERPA (미국 교육)
  □ 교육 기록 RLS 정책 적용
  □ Parent-Student 연결 기반 접근 제어
  □ 5년 보존 후 익명화

□ CCPA (캘리포니아)
  □ 개인정보 판매 없음 (명시)
  □ 삭제 요청 30일 이내 처리

□ 보안 조치
  □ 암호화 (At-rest: LUKS, In-transit: TLS 1.2+, Column: pgcrypto)
  □ 접근 제어 (RBAC, PBAC, RLS)
  □ Audit Log 1년 보존

□ AI Compliance
  □ AI Safety Layer (욕설/폭력/혐오 필터)
  □ AI Fairness (편향 탐지)
  □ 모델 교체 DPIA

□ 문서화
  □ DPIA 문서 작성 및 보관
  □ 제3자 계약서 보관
  □ 연례 Compliance Review 실시
```

MegaCity가 **글로벌 교육·문화 플랫폼**으로 확장될 때도 이 Compliance Manual이 **규정 기반 성장**을 뒷받침하게 됩니다.

---

**문서 완료 - DreamSeedAI MegaCity Global Compliance Manual v1.0**
