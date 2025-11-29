# 📕 DreamSeedAI MegaCity – Governance & Operations Guide

## 정책 · 승인 · 감사 · 보안 · GDPR/PIPA · 규제 준수 · 운영 거버넌스 프레임워크

**버전:** 1.0  
**작성일:** 2025-11-22  
**작성자:** DreamSeedAI Governance · Compliance · Architecture Team

---

# 📌 0. 개요 (Overview)

DreamSeedAI MegaCity는 9개 Zone과 Core City로 구성된 **교육 · AI · 문화 · CBT · 글로벌 멀티 플랫폼 도시**입니다.

이 문서는 MegaCity 전체의 운영을 규정하는 **최상위 Governance 문서**로서, 모든 정책, 보안, 감사, 데이터 보호, AI 안전성 규정을 포함합니다.

## 문서 목적

- MegaCity 전체 운영 거버넌스 프레임워크 정의
- 정책 관리, 승인, 감사 체계 표준화
- 보안 운영 규정 및 사고 대응 절차
- GDPR/PIPA 등 국제 규정 준수 가이드
- AI 거버넌스 및 윤리적 사용 규칙
- 변경 관리 및 문서화 기준

## 거버넌스 범위

```
┌─────────────────────────────────────────────────────────┐
│  1. Policy Governance (정책 관리 체계)                   │
│     • 정책 문서 구조 및 버전 관리                        │
│     • 정책 변경 프로세스                                 │
│     • 정책 검토 및 승인 체계                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  2. Access Governance (역할 · 승인 · 권한 체계)         │
│     • RBAC (Role-Based Access Control)                  │
│     • PBAC (Policy-Based Access Control)                │
│     • Approval Workflow                                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  3. Audit Governance (감사 규정)                        │
│     • Audit Log 기록 항목                               │
│     • 보존 정책 및 조회 권한                            │
│     • 감사 보고서 생성                                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  4. Security Governance (보안 운영 규정)                │
│     • 주간/월간 보안 점검                               │
│     • 비정상 이벤트 대응                                │
│     • 보안 사고 관리                                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  5. Data Governance (데이터 정책)                       │
│     • Data Retention (보존 정책)                        │
│     • Data Minimization (최소 수집)                     │
│     • Data Masking / Encryption                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  6. GDPR / PIPA (규정 준수)                             │
│     • GDPR 요구사항 (Access, Erasure, Portability)     │
│     • PIPA 준수 (한국 개인정보보호법)                   │
│     • Privacy Impact Assessment                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  7. AI Governance (AI 안전성 규정)                       │
│     • Prompt Injection 방지                             │
│     • AI 생성물 규제 대응                               │
│     • Bias / Fairness 검사                              │
│     • Abuse Detection                                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  8. Change Management (변경 관리 규정)                  │
│     • Change Request 프로세스                           │
│     • High-risk Change 승인                             │
│     • Change Freeze 정책                                │
└─────────────────────────────────────────────────────────┘
```

MegaCity의 **모든 Zone, API, AI 기능, 사용자 흐름**은 이 Governance 문서의 규칙 아래 동작해야 합니다.

---

# 🏛️ 1. Governance Framework (MegaCity 운영 체계)

MegaCity Governance는 **4개의 핵심 축**으로 이루어져 있습니다.

```
┌───────────────────────────────────────────────────────────┐
│                  MegaCity Governance                      │
└─────────────┬────────────────────────────────────────────┘
              │
    ┌─────────┼──────────┬──────────┬──────────┐
    │         │          │          │          │
    ▼         ▼          ▼          ▼          │
┌────────┐┌────────┐┌────────┐┌────────┐      │
│ Policy ││Security││  Data  ││   AI   │      │
│Governce││Governce││Governce││Governce│      │
└────────┘└────────┘└────────┘└────────┘      │
    │         │          │          │          │
    └─────────┴──────────┴──────────┴──────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Audit & Compliance  │
              │    (Cross-cutting)   │
              └──────────────────────┘
```

각 축은 독립적이지만 서로 긴밀히 연결되어 있으며, 변경 시 **Cross-Check**가 필요합니다.

## 1.1 Governance 운영 위원회

| 역할 | 책임 | 인원 |
|------|------|------|
| **Governance Committee Chair** | 전체 Governance 정책 승인 및 감독 | CTO/VP Engineering |
| **Policy Owner** | 정책 문서 관리 및 변경 승인 | PM Lead |
| **Security Officer** | 보안 정책 및 사고 관리 | Security Lead |
| **Compliance Officer** | GDPR/PIPA 준수 및 감사 | Legal/Compliance |
| **AI Ethics Lead** | AI 윤리 및 안전성 관리 | AI Lead |

## 1.2 Governance 회의 주기

```
Weekly: Security Review (보안 로그, 이상 패턴)
Monthly: Policy Review (정책 변경, 승인, 감사)
Quarterly: Compliance Audit (GDPR/PIPA 준수 검증)
Annually: Governance Framework Review (전체 개선)
```

---

# 🧩 2. Policy Governance (정책 관리 체계)

## 2.1 정책 문서 구조

모든 정책은 아래 **5단계 형식**을 따라야 합니다:

```
1. Purpose (목적)
2. Scope (적용 범위)
3. Definitions (용어 정의)
4. Rules (규칙)
5. Enforcement (시행 및 위반 시 조치)
```

### 정책 문서 예시

```markdown
# Password Policy v1.2

## 1. Purpose
사용자 계정 보안을 강화하기 위한 비밀번호 규칙을 정의합니다.

## 2. Scope
- 모든 MegaCity 사용자 (학생, 학부모, 교사, 관리자)
- 모든 Zone (UnivPrep, K-Zone 등)

## 3. Definitions
- **Strong Password**: 8자 이상, 대소문자, 숫자, 특수문자 포함

## 4. Rules
4.1. 최소 8자 이상
4.2. 대문자 1개 이상
4.3. 소문자 1개 이상
4.4. 숫자 1개 이상
4.5. 특수문자 1개 이상 (!@#$%^&*)
4.6. 이전 3개 비밀번호 재사용 금지
4.7. 90일마다 변경 권장 (강제 아님)

## 5. Enforcement
- 규칙 미준수 시 회원가입/비밀번호 변경 실패
- 관리자는 예외 없음
```

## 2.2 정책 카탈로그

| 정책 이름 | 버전 | 소유자 | 최종 업데이트 |
|----------|------|--------|--------------|
| **Password Policy** | v1.2 | Security Lead | 2025-10-15 |
| **Token Policy** | v2.0 | Platform Engineer | 2025-11-01 |
| **Data Retention Policy** | v1.0 | Compliance Officer | 2025-09-20 |
| **Parent-Student Verification Policy** | v1.1 | PM Lead | 2025-11-10 |
| **K-Zone Face/Voice Policy** | v1.0 | AI Ethics Lead | 2025-10-25 |
| **Exam Integrity Policy** | v1.0 | Product Manager | 2025-08-15 |
| **AI Usage Policy** | v2.1 | AI Ethics Lead | 2025-11-15 |

## 2.3 정책 변경 프로세스

```
┌──────────────┐
│  1. 작성     │  정책 초안 작성 (Policy Owner)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  2. 검토     │  이해관계자 검토 (PM, Backend, Frontend)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  3. 보안검토 │  Security Officer 승인
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  4. 승인     │  Governance Committee 승인
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  5. 배포     │  문서 배포 + 사용자 공지
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  6. 감사기록 │  Audit Log 기록
└──────────────┘
```

### 필수 검토자

```
□ Security Team (1명 이상)
□ PM 또는 Platform Owner (1명)
□ DevOps/SRE (1명, 시스템 영향 검증)
□ Legal/Compliance (규제 관련 정책만)
```

## 2.4 정책 버전 관리

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Change Log 필수**: 모든 변경 이력 기록

```markdown
## Change Log

### v1.2 (2025-11-15)
- 비밀번호 최소 길이 6자 → 8자로 변경
- 특수문자 필수 추가

### v1.1 (2025-09-01)
- 이전 비밀번호 재사용 금지 (3개)

### v1.0 (2025-06-01)
- 초기 정책 제정
```

---

# 🛂 3. Access Governance (역할 · 승인 · 권한 체계)

## 3.1 역할 기반 권한 (RBAC)

### 역할 정의

| 역할 | 권한 범위 | 사용자 수 (예상) |
|------|----------|------------------|
| **student** | 본인 시험, AI Tutor, Dashboard | 수만~수십만 |
| **parent** | 자녀 Dashboard, 성적 조회 | 수천~수만 |
| **teacher** | 반 관리, 시험 출제, 학생 관리 | 수백~수천 |
| **tutor** | AI Tutor 관리, 콘텐츠 관리 | 수십~수백 |
| **org_admin** | 조직 내 모든 관리 | 수십~수백 |
| **zone_admin** | Zone 전체 관리 | 9명 (Zone당 1명) |
| **sys_admin** | 전체 시스템 관리 | 2~5명 |

### 권한 매트릭스

| 기능 | student | parent | teacher | org_admin | zone_admin | sys_admin |
|------|---------|--------|---------|-----------|------------|----------|
| **시험 응시** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **AI Tutor 사용** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **자녀 성적 조회** | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **시험 출제** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **사용자 관리** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Zone 설정** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **시스템 설정** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

## 3.2 정책 기반 권한 (PBAC)

Policy Engine 규칙에 따라 **동적 권한 부여**.

### PBAC 규칙 예시

```python
# Rule 1: 시험 중 AI Tutor 차단
IF (exam.active == True) AND (user.role == 'student')
THEN deny(ai_tutor_access)

# Rule 2: 구독 미결제 시 Premium 기능 차단
IF (user.subscription == None) OR (user.subscription.expired == True)
THEN deny(premium_features)

# Rule 3: Zone 외부 접근 차단
IF (request.zone_id != user.zone_id)
THEN deny(access)

# Rule 4: 학부모는 본인 자녀만 조회 가능
IF (user.role == 'parent') AND (child.parent_id != user.id)
THEN deny(view_dashboard)
```

## 3.3 승인 체계 (Approval Workflow)

다음 작업은 **승인(Approval)** 이 필요합니다:

### 승인이 필요한 작업

| 작업 | 요청자 | 승인자 | 승인 기한 |
|------|--------|--------|----------|
| **Parent → Student 연결** | Parent | Student | 7일 |
| **Teacher → Org 가입** | Teacher | Org Admin | 3일 |
| **Admin 역할 부여** | Sys Admin | CTO | 1일 |
| **민감 데이터 접근** | Engineer | Security Lead | 1일 |
| **AI 모델 교체** | AI Engineer | AI Lead + SRE | 3일 |
| **DB Schema 변경** | Backend Engineer | Platform Lead + SRE | 5일 |

### Approval 흐름

```
┌──────────────┐
│  Requester   │  승인 요청 생성
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Approver(s) │  1~2명 승인 (역할에 따라)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Audit Log   │  승인 기록 저장
└──────────────┘
```

### Approval API 예시

```python
@app.post("/api/v1/approvals")
async def create_approval_request(
    request: ApprovalRequest,
    user: User = Depends(get_current_user)
):
    approval = await db.execute(
        """
        INSERT INTO approvals (requester_id, approver_id, action, resource, status)
        VALUES (:requester_id, :approver_id, :action, :resource, 'pending')
        RETURNING *
        """,
        {
            "requester_id": user.id,
            "approver_id": request.approver_id,
            "action": request.action,
            "resource": request.resource
        }
    )
    
    # 승인자에게 알림
    await send_notification(request.approver_id, "New approval request")
    
    return approval

@app.post("/api/v1/approvals/{approval_id}/approve")
async def approve_request(
    approval_id: int,
    user: User = Depends(get_current_user)
):
    approval = await db.fetchone("SELECT * FROM approvals WHERE id = :id", {"id": approval_id})
    
    if approval.approver_id != user.id:
        raise HTTPException(403, "Not authorized")
    
    await db.execute(
        "UPDATE approvals SET status = 'approved', approved_at = NOW() WHERE id = :id",
        {"id": approval_id}
    )
    
    # Audit Log 기록
    await log_audit(user.id, "approval_granted", approval_id)
    
    return {"status": "approved"}
```

---

# 📝 4. Audit Governance (감사 규정)

모든 민감한 작업/접근은 **Audit Log**로 기록되어야 합니다.

## 4.1 Audit 기록 항목

### Audit Log Schema

```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    zone_id VARCHAR(10) NOT NULL,
    org_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,  -- login, logout, create, update, delete, access
    resource_type VARCHAR(50) NOT NULL,  -- exam, user, ai_tutor, file, approval
    resource_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,  -- 추가 정보
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_audit_user_created (user_id, created_at),
    INDEX idx_audit_action_created (action, created_at),
    INDEX idx_audit_zone_created (zone_id, created_at)
);
```

### 기록해야 하는 이벤트

| 이벤트 유형 | action | resource_type | 예시 |
|-----------|--------|---------------|------|
| **로그인** | login | auth | 사용자 로그인 |
| **로그아웃** | logout | auth | 사용자 로그아웃 |
| **시험 응시** | attempt | exam | 학생 시험 시작 |
| **AI 사용** | access | ai_tutor | AI Tutor 질문 |
| **데이터 조회** | view | user | 학부모가 자녀 성적 조회 |
| **데이터 수정** | update | user | Admin이 사용자 정보 수정 |
| **데이터 삭제** | delete | user | 계정 삭제 |
| **권한 변경** | grant_role | user | Admin 역할 부여 |
| **승인** | approve | approval | Parent-Student 연결 승인 |

## 4.2 Audit 보존 정책

```
일반 로그: 1년 보관
보안 로그 (login, role_change): 2년 보관
GDPR Right-to-Erasure 적용 시: 익명화 처리 (user_id → NULL)
```

### Audit Log 자동 삭제

```sql
-- 1년 이상 된 일반 로그 삭제
DELETE FROM audit_log 
WHERE created_at < NOW() - INTERVAL '1 year'
  AND action NOT IN ('login', 'logout', 'grant_role');

-- 2년 이상 된 보안 로그 삭제
DELETE FROM audit_log 
WHERE created_at < NOW() - INTERVAL '2 years';
```

## 4.3 Audit 조회/다운로드 규정

### 조회 권한

```
sys_admin: 전체 조회 가능
zone_admin: 해당 Zone만 조회 가능
org_admin: 해당 Org만 조회 가능
일반 사용자: 조회 불가
```

### Audit Log API

```python
@app.get("/api/v1/audit")
async def get_audit_logs(
    start_date: date,
    end_date: date,
    action: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    # 권한 확인
    if user.role not in ["sys_admin", "zone_admin", "org_admin"]:
        raise HTTPException(403, "Access denied")
    
    query = "SELECT * FROM audit_log WHERE created_at BETWEEN :start AND :end"
    params = {"start": start_date, "end": end_date}
    
    # Zone Admin은 해당 Zone만
    if user.role == "zone_admin":
        query += " AND zone_id = :zone_id"
        params["zone_id"] = user.zone_id
    
    # Org Admin은 해당 Org만
    if user.role == "org_admin":
        query += " AND org_id = :org_id"
        params["org_id"] = user.org_id
    
    logs = await db.fetch_all(query, params)
    return logs
```

### CSV 다운로드 (암호화 필요)

```python
@app.get("/api/v1/audit/export")
async def export_audit_logs(user: User = Depends(get_current_user)):
    if user.role != "sys_admin":
        raise HTTPException(403, "Access denied")
    
    logs = await db.fetch_all("SELECT * FROM audit_log WHERE created_at > NOW() - INTERVAL '1 year'")
    
    # CSV 생성
    csv_data = to_csv(logs)
    
    # 암호화 (AES-256)
    encrypted = encrypt_aes256(csv_data, key=AUDIT_EXPORT_KEY)
    
    return Response(
        content=encrypted,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=audit_export.csv.enc"}
    )
```

---

# 🔐 5. Security Governance (보안 운영 규정)

MegaCity Security Architecture에 기반하며, 다음 **운영 규칙**을 추가합니다.

## 5.1 주간 보안 점검 (Weekly Security Review)

### 점검 항목

```
□ WAF 차단 로그 확인 (Cloudflare)
  - SQL Injection 시도
  - XSS 시도
  - Bot 차단
  
□ API 오류 패턴 확인
  - 5xx 에러 급증
  - 특정 엔드포인트 실패 증가
  
□ 토큰 실패/재시도 패턴 분석
  - 동일 IP에서 login 실패 10회 이상
  - Token replay 시도
  
□ 비정상 AI 사용 패턴
  - 동일 사용자 AI 호출 100회+ (1시간)
  - Prompt injection 키워드 탐지
```

### 주간 보안 리포트 자동 생성

```python
@app.on_event("startup")
@repeat_every(seconds=604800)  # 1주
async def weekly_security_report():
    report = {
        "waf_blocks": await get_waf_blocks(last_week=True),
        "api_errors": await get_api_errors(last_week=True),
        "token_failures": await get_token_failures(last_week=True),
        "ai_abuse": await get_ai_abuse_attempts(last_week=True)
    }
    
    # Slack 알림
    await send_slack("#security", f"Weekly Security Report: {report}")
```

## 5.2 월간 보안 점검 (Monthly Security Review)

### 점검 항목

```
□ RBAC 상태 검증
  - 불필요한 admin 권한 제거
  - 퇴사자 계정 비활성화
  
□ Admin 권한 재승인
  - sys_admin 역할 재검증 (CTO 승인)
  
□ RLS 정책 검증
  - PostgreSQL RLS 정책 테스트
  - Tenant 격리 검증
  
□ PII 삭제 정책 검증
  - 삭제 요청 처리 현황
  - GDPR Right-to-Erasure 준수
  
□ 보안 패치 업데이트
  - OS 보안 패치
  - Dependency 취약점 업데이트 (Snyk, Dependabot)
```

## 5.3 비정상/위험 이벤트 대응

발견 즉시 **SRE + Security 팀**에 Slack 경보:

### 경고 조건

```
1. Login 실패 급증 (1시간 내 100+ 실패)
2. 특정 국가 IP 폭증 (평소 대비 10배 증가)
3. AI 생성 이상 동작 (반복적/공격적 콘텐츠)
4. DB Slow Query 급증 (10+ queries > 5s)
5. GPU 온도 과열 (> 90°C)
6. 비정상적 데이터 다운로드 (1GB+ in 1 hour)
```

### 자동 경고 스크립트

```python
@app.on_event("startup")
@repeat_every(seconds=300)  # 5분마다
async def security_monitor():
    # Login 실패 급증
    login_failures = await db.scalar(
        "SELECT count(*) FROM audit_log WHERE action = 'login_failed' AND created_at > NOW() - INTERVAL '1 hour'"
    )
    if login_failures > 100:
        await send_alert("🚨 Login failures > 100 in last hour")
    
    # 비정상 AI 사용
    ai_abuse = await db.scalar(
        "SELECT count(*) FROM ai_requests WHERE created_at > NOW() - INTERVAL '1 hour' GROUP BY user_id HAVING count(*) > 100"
    )
    if ai_abuse:
        await send_alert("🚨 AI abuse detected (100+ requests/hour)")
```

---

# 🧬 6. Data Governance (데이터 정책)

## 6.1 Data Retention (보존 정책)

| 데이터 유형 | 보존 기간 | 삭제 방법 |
|------------|----------|----------|
| **PII** (이름, 이메일, 전화번호) | 3년 (또는 법적 요구) | Hard delete or Hash |
| **Logs** (Access, Error) | 1년 | Auto-delete |
| **AI Embeddings** | 1년 | Hard delete |
| **Exam 시도 기록** | 5년 (교육 기록) | 익명화 후 통계 유지 |
| **K-Zone 음성/영상** | 90일 | Auto-delete |
| **Tmp AI 파일** | 24~72시간 | Auto-delete |

### 자동 삭제 스크립트

```python
@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def cleanup_expired_data():
    # Tmp AI 파일 삭제 (24시간)
    await s3.delete_objects_older_than("/tmp/ai/", days=1)
    
    # K-Zone 미디어 삭제 (90일)
    await s3.delete_objects_older_than("/kzone/user-uploads/", days=90)
    
    # 로그 삭제 (1년)
    await db.execute("DELETE FROM logs WHERE created_at < NOW() - INTERVAL '1 year'")
```

## 6.2 Data Minimization (최소 수집 원칙)

### 원칙

```
1. 학습 목적 외 불필요한 정보 수집 금지
2. Parent/Student 관계 데이터 최소화 (필요 시만 연결)
3. 위치 정보 수집 금지 (IP만 기록)
4. 생년월일 대신 연령대 수집
```

### 수집 금지 항목

```
❌ 주민등록번호
❌ 정확한 주소 (시/구까지만)
❌ GPS 위치 정보
❌ 신용카드 번호 (결제 대행사 처리)
❌ 민감 건강 정보
```

## 6.3 Data Masking (마스킹)

로그/대시보드에서 다음 필드 자동 마스킹:

### 마스킹 규칙

```python
def mask_email(email: str) -> str:
    """이메일 마스킹: hong****@gmail.com"""
    username, domain = email.split("@")
    return f"{username[0]}{'*' * (len(username)-1)}@{domain}"

def mask_phone(phone: str) -> str:
    """전화번호 마스킹: 010-****-1234"""
    return f"{phone[:3]}-****-{phone[-4:]}"

def mask_name(name: str) -> str:
    """이름 마스킹: 홍**"""
    return f"{name[0]}{'*' * (len(name)-1)}"
```

### Logging 자동 마스킹

```python
import logging

class PIIMaskingFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        # Email 마스킹
        msg = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     lambda m: mask_email(m.group()), msg)
        # Phone 마스킹
        msg = re.sub(r'\b\d{3}-\d{4}-\d{4}\b', 
                     lambda m: mask_phone(m.group()), msg)
        return msg

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(PIIMaskingFormatter())
```

## 6.4 Encryption (암호화)

### Column-Level Encryption (pgcrypto)

```sql
-- PII 암호화
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 전화번호 암호화
UPDATE users 
SET phone_encrypted = pgp_sym_encrypt(phone, 'encryption_key')
WHERE phone IS NOT NULL;

-- 복호화
SELECT 
    id,
    pgp_sym_decrypt(phone_encrypted::bytea, 'encryption_key') AS phone
FROM users;
```

### Application-Level Encryption (Fernet)

```python
from cryptography.fernet import Fernet

class PIIEncryptor:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()

# 사용
encryptor = PIIEncryptor(ENCRYPTION_KEY)
user.ssn_encrypted = encryptor.encrypt(user.ssn)
```

### DB Volume Encryption (LUKS)

```bash
# LUKS 볼륨 암호화
cryptsetup luksFormat /dev/sdb
cryptsetup open /dev/sdb pgdata
mkfs.ext4 /dev/mapper/pgdata
mount /dev/mapper/pgdata /var/lib/postgresql/data
```

### In-Transit Encryption (TLS 1.2+)

```yaml
# PostgreSQL SSL
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'
ssl_min_protocol_version = 'TLSv1.2'
```

---

# 🌍 7. GDPR / PIPA 규정 준수

## 7.1 GDPR 요구사항 (EU 사용자)

### Right to Access (접근권)

사용자는 자신의 데이터를 요청할 수 있습니다.

```python
@app.get("/api/v1/privacy/my-data")
async def get_my_data(user: User = Depends(get_current_user)):
    data = {
        "personal_info": await get_user_info(user.id),
        "exam_history": await get_exam_attempts(user.id),
        "ai_usage": await get_ai_requests(user.id),
        "audit_log": await get_audit_logs(user.id)
    }
    
    return JSONResponse(content=data)
```

### Right to Erasure (삭제권)

사용자는 계정 삭제를 요청할 수 있습니다.

```python
@app.delete("/api/v1/privacy/delete-account")
async def delete_my_account(user: User = Depends(get_current_user)):
    # 1. PII 삭제/익명화
    await db.execute(
        """
        UPDATE users SET
            email = 'deleted_' || id || '@deleted.local',
            phone = NULL,
            name = 'Deleted User',
            deleted_at = NOW()
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
    await s3.delete_prefix(f"/users/{user.id}/")
    
    return {"status": "deleted"}
```

### Right to Portability (이동권)

사용자는 데이터를 다운로드할 수 있습니다.

```python
@app.get("/api/v1/privacy/export-data")
async def export_my_data(user: User = Depends(get_current_user)):
    data = await get_all_user_data(user.id)
    
    # JSON 다운로드
    return Response(
        content=json.dumps(data, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=my_data.json"}
    )
```

### Right to Restrict Processing (처리 제한권)

사용자는 데이터 처리를 제한할 수 있습니다.

```python
@app.post("/api/v1/privacy/restrict-processing")
async def restrict_processing(user: User = Depends(get_current_user)):
    await db.execute(
        "UPDATE users SET processing_restricted = TRUE WHERE id = :id",
        {"id": user.id}
    )
    
    return {"status": "restricted"}
```

## 7.2 PIPA (한국 개인정보보호법)

### 주요 요구사항

```
1. 주민등록번호 저장 금지 (법적 요구 시만 허용)
2. 최소 수집 원칙 (필요한 정보만)
3. 수탁사 관리 의무 (Cloudflare, AWS 등)
4. 개인정보 처리방침 고지 의무 (웹사이트 게시)
5. 14세 미만 법정대리인 동의 필요
```

### 14세 미만 사용자 처리

```python
@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    # 만 14세 미만 체크
    if calculate_age(request.birthdate) < 14:
        # 학부모 동의 필요
        return {
            "status": "pending",
            "message": "법정대리인(학부모) 동의가 필요합니다.",
            "next_step": "parent_approval"
        }
    
    # 일반 회원가입 진행
    user = await create_user(request)
    return {"status": "success", "user_id": user.id}
```

## 7.3 Privacy Impact Assessment (P.I.A)

신규 기능 추가 시 개인정보 영향평가 실시.

### PIA 체크리스트

```
□ 수집하는 개인정보 유형 (이름, 이메일, 전화번호 등)
□ 수집 목적 및 법적 근거
□ 보유 기간
□ 제3자 제공 여부 (Cloudflare, AWS 등)
□ 암호화 방법
□ 접근 권한 (누가 조회 가능?)
□ 삭제 정책
```

### PIA 템플릿

```markdown
# Privacy Impact Assessment - K-Zone PoseNet Feature

## 1. 수집하는 개인정보
- 비디오 (댄스 동작)
- 얼굴 이미지 (PoseNet keypoints만 추출)

## 2. 수집 목적
- K-POP 댄스 학습 및 스코어링

## 3. 법적 근거
- 사용자 동의 (Opt-in)

## 4. 보유 기간
- 90일 (이후 자동 삭제)

## 5. 제3자 제공
- 없음 (로컬 GPU 처리)

## 6. 암호화
- 전송 구간: TLS 1.2+
- 저장: R2 (Server-side encryption)

## 7. 접근 권한
- 본인만 조회 가능
- Admin 조회 불가

## 8. 삭제 정책
- 90일 자동 삭제
- 사용자 즉시 삭제 가능
```

## 7.4 International Data Transfer (국제 데이터 전송)

### 해외 AI 모델/API 사용 시

```
□ DPA (Data Processing Agreement) 체결 필요
□ EU 사용자 → EU 저장소 사용 고려
□ Standard Contractual Clauses (SCC) 검토
```

### 예시: OpenAI API 사용 시

```python
# EU 사용자는 Azure OpenAI (EU region) 사용
if user.country in EU_COUNTRIES:
    llm_endpoint = "https://dreamseed-eu.openai.azure.com"
else:
    llm_endpoint = "https://api.openai.com"
```

---

# 🤖 8. AI Governance (AI 안전성 규정)

AI 기능이 있는 MegaCity Zone은 다음 규칙을 따라야 합니다.

## 8.1 Prompt Injection 방지 규칙

### 차단 키워드

```python
BLOCKED_KEYWORDS = [
    "system:", "ignore previous", "override", "jailbreak",
    "bypass filters", "admin mode", "developer mode"
]

def detect_prompt_injection(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in BLOCKED_KEYWORDS)

@app.post("/api/v1/ai-tutor")
async def ai_tutor(request: AITutorRequest):
    if detect_prompt_injection(request.prompt):
        await log_security_event("prompt_injection_attempt", request.prompt[:100])
        raise HTTPException(400, "Invalid prompt detected")
    
    response = await call_llm(request.prompt)
    return response
```

## 8.2 AI 생성물 규제 대응

### 얼굴/음성 합성 규칙

```
1. 동의 기반 Opt-in (명시적 동의 필요)
2. 원본 보유자 확인 (얼굴/음성 소유권 검증)
3. AI 생성 표시 (워터마크 또는 메타데이터)
4. 미성년자 콘텐츠 생성 금지
```

### K-Zone Creator Studio 안전 규칙

```python
@app.post("/api/v1/kzone/voice-clone")
async def voice_clone(request: VoiceCloneRequest, user: User = Depends(get_current_user)):
    # 1. 동의 확인
    consent = await db.fetchone(
        "SELECT * FROM voice_consents WHERE user_id = :user_id AND voice_id = :voice_id",
        {"user_id": user.id, "voice_id": request.voice_id}
    )
    if not consent:
        raise HTTPException(403, "Voice cloning requires consent")
    
    # 2. AI 생성 워터마크
    audio = await generate_voice_clone(request.text, request.voice_id)
    watermarked_audio = add_watermark(audio, "AI-generated by DreamSeedAI")
    
    return {"audio_url": watermarked_audio}
```

## 8.3 Bias / Fairness 검사

교육 콘텐츠에서 편향된 출력 발생 시 자동 필터링.

### Bias Detection

```python
from transformers import pipeline

bias_detector = pipeline("text-classification", model="unbiased/bias-detection")

async def check_bias(text: str) -> dict:
    result = bias_detector(text)[0]
    
    if result["label"] == "biased" and result["score"] > 0.7:
        return {"is_biased": True, "score": result["score"]}
    
    return {"is_biased": False}

@app.post("/api/v1/ai-tutor")
async def ai_tutor(request: AITutorRequest):
    response = await call_llm(request.prompt)
    
    # Bias 검사
    bias_result = await check_bias(response)
    if bias_result["is_biased"]:
        await log_ai_safety_issue("bias_detected", response)
        response = "I apologize, but I cannot provide that response. Please rephrase your question."
    
    return {"response": response}
```

## 8.4 Abuse Detection (남용 탐지)

AI Router에서 실시간 모니터링:

### 탐지 항목

```
- 공격적 내용 (욕설, 폭력, 혐오)
- 음란/성적 콘텐츠
- 도배/스팸 (동일 내용 10회 이상)
- 비정상적 사용 패턴 (1시간 100+ 요청)
```

### Abuse Detection 구현

```python
from transformers import pipeline

toxicity_detector = pipeline("text-classification", model="unitary/toxic-bert")

async def detect_abuse(text: str) -> dict:
    result = toxicity_detector(text)[0]
    
    if result["label"] == "toxic" and result["score"] > 0.7:
        return {"is_abusive": True, "type": "toxicity", "score": result["score"]}
    
    # 도배 검사
    recent_requests = await redis.lrange(f"user:{user_id}:prompts", 0, 10)
    if recent_requests.count(text) > 3:
        return {"is_abusive": True, "type": "spam"}
    
    return {"is_abusive": False}

@app.post("/api/v1/ai-tutor")
async def ai_tutor(request: AITutorRequest, user: User = Depends(get_current_user)):
    # Abuse 검사
    abuse_result = await detect_abuse(request.prompt)
    if abuse_result["is_abusive"]:
        await log_security_event("ai_abuse_detected", request.prompt[:100])
        await notify_admin(f"AI abuse detected: {abuse_result['type']}")
        raise HTTPException(400, "Your request violates our AI usage policy")
    
    response = await call_llm(request.prompt)
    return {"response": response}
```

---

# 🔁 9. Change Management (변경 관리 규정)

## 9.1 Change Request (변경 요청) 프로세스

```
┌──────────────┐
│  1. CR 생성  │  Change Request 생성 (Jira, Linear)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  2. 검토     │  Technical Review (Backend/Frontend/AI)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  3. 승인     │  2명 승인 (PM/SRE/Security)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  4. 배포     │  Deployment (Rolling/Canary/Blue-Green)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  5. 감사기록 │  Audit Log 기록
└──────────────┘
```

## 9.2 High-Risk Change (고위험 변경)

다음 변경은 **고위험**으로 분류되며 추가 승인 필요:

| 변경 유형 | 위험도 | 승인자 | 배포 전략 |
|----------|--------|--------|----------|
| **DB Migration** | High | Platform Lead + SRE | Stage-First + Blue-Green |
| **AI 모델 교체** | High | AI Lead + SRE | Blue-Green |
| **Gateway 라우팅 변경** | High | Platform Lead + SRE | Canary 5% → 100% |
| **Authentication 변경** | Critical | Security Lead + CTO | Stage-First + Canary |
| **RLS 정책 변경** | Critical | Security Lead + Platform Lead | Stage-First |

### High-Risk Change 승인 예시

```markdown
# Change Request: vLLM 모델 교체 (Qwen2.5-32B → Qwen2.5-72B)

**Risk Level:** High  
**Approvers:** AI Lead, SRE Lead  
**Deployment Strategy:** Blue-Green

## Impact Assessment
- GPU 메모리 사용량 2배 증가 (16GB → 32GB)
- Inference latency 10% 증가 예상
- 모델 품질 15% 향상 기대

## Rollback Plan
- Blue 환경 유지 (24시간)
- 1-click rollback (< 1분)

## Testing
- [x] Stage 환경 테스트 완료
- [x] Load Test 통과 (100 req/s)
- [x] GPU 메모리 모니터링 정상

## Approval
- [x] AI Lead (approved)
- [x] SRE Lead (approved)
- [x] PM (approved)
```

## 9.3 Change Freeze (변경 동결 기간)

안정적인 운영을 위해 특정 기간에는 변경을 금지합니다.

### Change Freeze 기간

```
1. 대학수학능력시험 (11월 셋째 주)
2. 편입시험 시즌 (6월)
3. 설날/추석 연휴
4. K-Zone 글로벌 이벤트 (사전 공지)
5. Phase 출시 주간 (UnivPrep, K-Zone 등)
```

### Change Freeze 예외

```
✅ P1 Hotfix (보안, 장애)
✅ 로그 레벨 변경
✅ Feature Flag 토글 (Off만 허용)

❌ 새 기능 배포
❌ AI 모델 교체
❌ DB Migration
❌ Infrastructure 변경
```

---

# 🧾 10. Governance Documentation Management (문서 관리)

모든 Governance 문서는 **Git 기반**으로 관리하며 버전 관리가 필요합니다.

## 10.1 문서 저장 위치

```
/ops/architecture/
  ├── MEGACITY_GOVERNANCE_OPERATIONS.md (이 문서)
  ├── MEGACITY_SECURITY_ARCHITECTURE.md
  ├── MEGACITY_POLICY_ENGINE.md
  └── ...

/docs/governance/
  ├── password_policy.md
  ├── token_policy.md
  ├── data_retention_policy.md
  ├── parent_student_policy.md
  └── ai_usage_policy.md

/docs/security/
  ├── incident_response.md
  ├── security_checklist.md
  └── ...

/docs/compliance/
  ├── gdpr_compliance.md
  ├── pipa_compliance.md
  └── ...
```

## 10.2 문서 버전 관리

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Change Log 필수**: 모든 변경 이력 기록
- **Git Commit**: 모든 변경은 Git으로 추적

### 문서 버전 예시

```markdown
# Password Policy

**Version:** 1.2.0  
**Last Updated:** 2025-11-15  
**Owner:** Security Lead

## Change Log

### v1.2.0 (2025-11-15)
- 비밀번호 최소 길이 6자 → 8자로 변경
- 특수문자 필수 추가

### v1.1.0 (2025-09-01)
- 이전 비밀번호 재사용 금지 (3개)

### v1.0.0 (2025-06-01)
- 초기 정책 제정
```

## 10.3 문서 유지보수 규칙

### Pull Request 필수

```
1. 모든 문서 변경은 PR 생성
2. 리뷰어 2명 승인 필요
3. Lint/Spell-check 통과
4. CI/CD 자동 배포
```

### 문서 리뷰 체크리스트

```
□ 문법 오류 없음 (Grammarly, markdownlint)
□ 코드 예시 테스트 완료
□ 최신 시스템 상태 반영
□ 관련 문서 링크 업데이트
□ Change Log 작성
```

## 10.4 문서 동기화

```
정책 변경 → 코드 구현 → 테스트 → 문서 업데이트
```

**원칙: Code와 Docs는 항상 동기화**

---

# 🏁 11. 결론

이 **Governance & Operations Guide**는 DreamSeedAI MegaCity 전체를 운영하는 데 필요한 **정책·보안·승인·감사·데이터·AI 거버넌스**를 통합한 최고 레벨의 운영 가이드입니다.

## 핵심 거버넌스 원칙

1. **Policy First**: 모든 기능은 정책 기반 설계
2. **Approval-Based**: 민감한 작업은 승인 필수
3. **Audit Everything**: 모든 행동 기록
4. **Security by Default**: 기본 보안 강화
5. **Privacy by Design**: 개인정보 보호 우선
6. **AI Safety**: AI 윤리 및 안전성 준수
7. **Continuous Improvement**: 분기별 Governance 리뷰

## Governance 준수 체크리스트

```
□ 모든 정책 문서 최신 버전 유지
□ RBAC/PBAC 정책 검증 (월 1회)
□ Audit Log 보존 정책 준수 (1~2년)
□ GDPR/PIPA 요구사항 충족
□ AI 안전성 검사 실시 (Prompt Injection, Bias, Abuse)
□ Change Management 프로세스 준수
□ 보안 점검 (주간/월간)
□ Governance 회의 (월 1회)
```

MegaCity가 **글로벌 교육·문화 플랫폼**으로 확장될 때도 이 Governance 문서가 **규정 기반 성장**을 뒷받침하게 됩니다.

---

**문서 완료 - DreamSeedAI MegaCity Governance & Operations Guide v1.0**
