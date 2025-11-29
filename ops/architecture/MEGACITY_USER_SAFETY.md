# 🛡️ DreamSeedAI MegaCity – User Safety Guide

## 학생 · 학부모 · 교사 보호 정책 · AI 안전 · 콘텐츠 안전 · 개인정보 보호 기준

**버전:** 1.0  
**작성일:** 2025-11-22  
**작성자:** DreamSeedAI User Safety & Trust Team

---

# 📌 0. 개요 (Overview)

DreamSeedAI MegaCity는 학생, 학부모, 교사, 일반 사용자 모두가 안전하게 사용할 수 있는 **신뢰 기반 교육·AI 플랫폼**을 목표로 합니다.

이 문서는 MegaCity의 모든 Zone(UnivPrepAI, SkillPrepAI, My-Ktube 등)에 공통 적용되는 **사용자 안전(User Safety) 기준**을 규정합니다.

## 문서 목적

- 학생, 학부모, 교사를 포함한 모든 사용자 보호
- 유해 콘텐츠 차단 및 AI 안전성 확보
- 개인정보 보호 및 프라이버시 권리 보장
- 안전 사고 대응 및 신고 시스템 구축
- 사용자 상호작용 안전 규정 정립

## 안전 체계 구조

```
┌─────────────────────────────────────────────────────────┐
│              DreamSeedAI MegaCity User Safety           │
└─────────────┬───────────────────────────────────────────┘
              │
    ┌─────────┼──────────┬──────────┬──────────┬──────────┐
    │         │          │          │          │          │
    ▼         ▼          ▼          ▼          ▼          │
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐      │
│Content ││   AI   ││Student ││Privacy ││  User  │      │
│ Safety ││ Safety ││ Safety ││Protectn││Interact│      │
└────────┘└────────┘└────────┘└────────┘└────────┘      │
    │         │          │          │          │          │
    └─────────┴──────────┴──────────┴──────────┴──────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Safety Monitoring   │
              │  & Incident Response │
              └──────────────────────┘
```

안전 항목은 다음 **5개 축**으로 구성됩니다:

```
1. 콘텐츠 안전 (Content Safety)
   - 유해 콘텐츠 차단
   - 경고/제한 콘텐츠 관리
   - Zone별 특수 규정

2. AI 안전 (AI Safety)
   - Prompt Injection 방지
   - 유해 출력 감지 및 필터링
   - 교육적 프레이밍
   - AI 역할 제한

3. 학습자 안전 (Student Safety)
   - 학생 계정 보호
   - 시험·성적 보호
   - 실시간 상호작용 안전

4. 개인정보/프라이버시 보호 (Privacy Protection)
   - 최소 정보 수집
   - 암호화 및 보안
   - GDPR/PIPA 권리 보장
   - 영상/음성 데이터 보호

5. 사용자 상호작용 안전 (User Interaction Safety)
   - Parent-Student 승인
   - Teacher-Student 상호작용
   - 커뮤니티 안전
```

---

# 🧩 1. 콘텐츠 안전 (Content Safety)

## 1.1 금지 콘텐츠 (Prohibited Content)

다음 콘텐츠는 전 Zone에서 **즉시 차단**됩니다:

### 금지 콘텐츠 카테고리

| 카테고리 | 설명 | 조치 | 처벌 |
|---------|------|------|------|
| **음란물/성적 콘텐츠** | 특히 미성년자 관련 모든 성적 콘텐츠 | 즉시 차단 + 계정 영구 정지 | 법적 신고 |
| **아동 학대/착취** | 아동 성 착취물(CSAM), 아동 학대 콘텐츠 | 즉시 차단 + 법 집행 기관 신고 | 계정 영구 정지 |
| **혐오/차별 표현** | 인종, 성별, 종교, 장애 기반 혐오 | 즉시 삭제 + 경고 | 3회 누적 시 계정 정지 |
| **자해/폭력/테러** | 자살 조장, 폭력 묘사, 테러 선동 | 즉시 차단 + 모니터링 | 계정 정지 + 법적 신고 |
| **도박/사기/불법** | 도박 사이트, 사기, 마약, 불법 활동 | 즉시 차단 | 계정 영구 정지 |
| **무단 얼굴/음성 합성** | K-Zone에서 동의 없는 Deepfake | 즉시 삭제 + 경고 | 2회 누적 시 계정 정지 |

### 콘텐츠 필터링 시스템

```python
from transformers import pipeline

# NSFW 이미지 탐지
nsfw_detector = pipeline("image-classification", model="Falconsai/nsfw_image_detection")

async def check_image_safety(image_path: str) -> dict:
    result = nsfw_detector(image_path)[0]
    
    if result["label"] == "nsfw" and result["score"] > 0.7:
        return {
            "is_safe": False,
            "reason": "NSFW content detected",
            "score": result["score"]
        }
    
    return {"is_safe": True}

# 텍스트 유해성 탐지
toxicity_detector = pipeline("text-classification", model="unitary/toxic-bert")

async def check_text_safety(text: str) -> dict:
    result = toxicity_detector(text)[0]
    
    if result["label"] == "toxic" and result["score"] > 0.7:
        return {
            "is_safe": False,
            "reason": "Toxic content detected",
            "type": result["label"],
            "score": result["score"]
        }
    
    return {"is_safe": True}

@app.post("/api/v1/content/upload")
async def upload_content(
    file: UploadFile,
    text: str,
    user: User = Depends(get_current_user)
):
    # 이미지 안전 검사
    if file.content_type.startswith("image/"):
        safety_check = await check_image_safety(file)
        if not safety_check["is_safe"]:
            await log_safety_incident("nsfw_image_blocked", user.id, safety_check)
            raise HTTPException(400, "Unsafe content detected")
    
    # 텍스트 안전 검사
    text_safety = await check_text_safety(text)
    if not text_safety["is_safe"]:
        await log_safety_incident("toxic_text_blocked", user.id, text_safety)
        raise HTTPException(400, "Unsafe content detected")
    
    # 업로드 진행
    return await upload_to_storage(file, text)
```

## 1.2 경고/제한 콘텐츠 (Warning Content)

다음 콘텐츠는 **경고 표시** 또는 **연령 제한** 적용:

### 경고 콘텐츠 카테고리

| 카테고리 | 조치 | 표시 |
|---------|------|------|
| **정치적 논쟁** | 중립적 프레이밍 또는 약화 | "⚠️ 정치적 콘텐츠" |
| **종교적 갈등** | 다양성 존중 프레이밍 | "⚠️ 종교적 콘텐츠" |
| **풍자/패러디** | 교육적 맥락 강조 | "⚠️ 풍자 콘텐츠" |
| **폭력적 게임** | 연령 제한 (18세+) | "🔞 18세 이상" |

### AI Safety Layer 재검토

```python
async def review_warning_content(content: str) -> dict:
    # AI 기반 콘텐츠 재작성
    safe_version = await llm_rewrite(
        content,
        system_prompt="""
        다음 콘텐츠를 교육적이고 건설적인 방식으로 재작성하세요.
        - 중립적 관점 유지
        - 다양성 존중
        - 학습자 정서 보호
        """
    )
    
    return {
        "original": content,
        "safe_version": safe_version,
        "warning": "이 콘텐츠는 안전을 위해 재작성되었습니다."
    }
```

## 1.3 K-Zone 전용 규정 (K-Zone Specific Rules)

K-Zone (My-Ktube, K-Zone Creator Studio)는 **엄격한 콘텐츠 규정**을 적용합니다.

### K-Zone 콘텐츠 규칙

```
1. 타인의 얼굴·음성 기반 합성은 본인 동의 필수 (Opt-in)
2. 동의 없는 Deepfake → 즉시 삭제 + 계정 경고
3. 영상/음성 업로드 시 민감한 얼굴 자동 모자이크 옵션 활성
4. Creator Studio 결과물은 30일 자동 삭제
5. K-POP 아티스트 음성 클로닝은 공식 라이선스만 허용
```

### K-Zone 동의 시스템

```python
@app.post("/api/v1/kzone/voice-consent")
async def request_voice_consent(
    request: VoiceConsentRequest,
    user: User = Depends(get_current_user)
):
    # 동의 요청 생성
    consent = await db.execute(
        """
        INSERT INTO voice_consents (requester_id, owner_id, voice_sample_url, status)
        VALUES (:requester_id, :owner_id, :voice_url, 'pending')
        RETURNING *
        """,
        {
            "requester_id": user.id,
            "owner_id": request.owner_id,
            "voice_url": request.voice_sample_url
        }
    )
    
    # 소유자에게 알림
    await send_notification(
        request.owner_id,
        f"{user.name}님이 귀하의 음성 사용을 요청했습니다.",
        consent_id=consent.id
    )
    
    return {"status": "pending", "consent_id": consent.id}

@app.post("/api/v1/kzone/voice-consent/{consent_id}/approve")
async def approve_voice_consent(
    consent_id: int,
    user: User = Depends(get_current_user)
):
    consent = await db.fetchone(
        "SELECT * FROM voice_consents WHERE id = :id AND owner_id = :user_id",
        {"id": consent_id, "user_id": user.id}
    )
    
    if not consent:
        raise HTTPException(404, "Consent not found")
    
    await db.execute(
        "UPDATE voice_consents SET status = 'approved', approved_at = NOW() WHERE id = :id",
        {"id": consent_id}
    )
    
    # Audit Log 기록
    await log_audit(user.id, "voice_consent_granted", consent_id)
    
    return {"status": "approved"}
```

### K-Zone 자동 모자이크

```python
import cv2
import mediapipe as mp

async def auto_blur_sensitive_areas(video_path: str) -> str:
    """민감 부위 자동 모자이크"""
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    
    cap = cv2.VideoCapture(video_path)
    output_path = f"{video_path}_blurred.mp4"
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (width, height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Pose 감지
        results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if results.pose_landmarks:
            # 민감 부위 좌표 추출 (예: 가슴, 골반)
            sensitive_areas = [
                results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER],
                results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER],
                # ... (민감 부위 keypoints)
            ]
            
            # 모자이크 적용
            for area in sensitive_areas:
                x, y = int(area.x * width), int(area.y * height)
                frame[y-50:y+50, x-50:x+50] = cv2.blur(frame[y-50:y+50, x-50:x+50], (50, 50))
        
        out.write(frame)
    
    cap.release()
    out.release()
    
    return output_path
```

---

# 🤖 2. AI 안전 (AI Safety)

## 2.1 Prompt Injection 방지 (Prompt Injection Defense)

AI 입력에서 다음 패턴은 **자동 차단**됩니다:

### Prompt Injection 탐지 패턴

```python
PROMPT_INJECTION_PATTERNS = [
    r"ignore previous",
    r"disregard.*instruction",
    r"jailbreak",
    r"system override",
    r"roleplay as malicious",
    r"pretend you are",
    r"act as.*admin",
    r"bypass.*filter",
    r"reveal.*prompt",
    r"show.*system.*message",
]

import re

def detect_prompt_injection(prompt: str) -> dict:
    """Prompt Injection 시도 탐지"""
    prompt_lower = prompt.lower()
    
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, prompt_lower):
            return {
                "is_safe": False,
                "reason": "Prompt injection detected",
                "pattern": pattern
            }
    
    return {"is_safe": True}

@app.post("/api/v1/ai-tutor")
async def ai_tutor(
    request: AITutorRequest,
    user: User = Depends(get_current_user)
):
    # Prompt Injection 검사
    safety_check = detect_prompt_injection(request.prompt)
    if not safety_check["is_safe"]:
        await log_safety_incident("prompt_injection_attempt", user.id, safety_check)
        raise HTTPException(400, "Invalid prompt detected")
    
    # AI 응답 생성
    response = await call_llm(request.prompt)
    return {"response": response}
```

## 2.2 유해 출력 감지 (Harmful Output Filter)

AI 응답에서 다음 표현 발견 시 **자동 필터링**:

### 유해 출력 카테고리

| 카테고리 | 예시 | 조치 |
|---------|------|------|
| **욕설/폭언** | 저속한 언어, 모욕 | 응답 재생성 |
| **폭력/자해** | 자살 조장, 폭력 묘사 | 응답 차단 + 경고 |
| **성적 콘텐츠** | 성적 암시, 묘사 | 응답 차단 |
| **차별/혐오** | 인종, 성별 기반 조롱 | 응답 재생성 |

### 유해 출력 필터링 구현

```python
from transformers import pipeline

hate_detector = pipeline("text-classification", model="facebook/roberta-hate-speech-dynabench-r4-target")

async def filter_harmful_output(text: str) -> dict:
    """AI 출력물 유해성 검사"""
    
    # Hate Speech 탐지
    hate_result = hate_detector(text)[0]
    if hate_result["label"] == "hate" and hate_result["score"] > 0.7:
        return {
            "is_safe": False,
            "reason": "Hate speech detected",
            "score": hate_result["score"]
        }
    
    # 욕설 키워드 검사
    PROFANITY_KEYWORDS = ["욕설1", "욕설2", "욕설3"]  # 실제 욕설은 별도 파일
    if any(word in text for word in PROFANITY_KEYWORDS):
        return {"is_safe": False, "reason": "Profanity detected"}
    
    return {"is_safe": True}

@app.post("/api/v1/ai-tutor")
async def ai_tutor(request: AITutorRequest):
    response = await call_llm(request.prompt)
    
    # 유해 출력 검사
    safety_check = await filter_harmful_output(response)
    
    if not safety_check["is_safe"]:
        await log_safety_incident("harmful_output_blocked", user.id, safety_check)
        
        # 응답 재생성 (최대 3회)
        for retry in range(3):
            response = await call_llm(
                request.prompt,
                system_prompt="건설적이고 교육적인 방식으로 답변하세요."
            )
            if (await filter_harmful_output(response))["is_safe"]:
                break
        else:
            response = "죄송합니다. 적절한 답변을 생성할 수 없습니다."
    
    return {"response": response}
```

## 2.3 교육적 프레이밍 적용 (Educational Framing)

AI Tutor와 K-Zone AI는 응답을 다음 **교육적 규칙**으로 포맷팅:

### 교육적 프레이밍 규칙

```
1. 건설적/배려적 언어 사용
   - "틀렸어" → "다시 한번 생각해볼까요?"
   - "모르겠어" → "이 부분을 함께 살펴봅시다"

2. 교육적 목적 강조
   - 정답만 제공하지 않고 사고 과정 설명
   - 단계별 학습 유도

3. 학습자 정서 보호
   - 실수를 자연스러운 학습 과정으로 프레이밍
   - 긍정적 피드백 우선
```

### System Prompt 템플릿

```python
EDUCATIONAL_SYSTEM_PROMPT = """
당신은 DreamSeedAI의 교육 AI Tutor입니다.

**응답 규칙:**
1. 학생을 존중하고 배려하는 언어를 사용하세요.
2. 정답만 제공하지 말고, 사고 과정을 단계별로 설명하세요.
3. 학생의 실수는 학습의 기회로 프레이밍하세요.
4. 절대 사용하지 말아야 할 표현:
   - 욕설, 폭력적 언어
   - 차별적 표현
   - 성적 암시
   - "틀렸어", "바보같이" 등 부정적 표현

**예시:**
학생: "이 문제 답이 뭐예요?"
응답: "좋은 질문이에요! 함께 단계별로 풀어볼까요? 먼저..."
"""

async def call_educational_llm(prompt: str, user_context: dict) -> str:
    response = await call_llm(
        prompt,
        system_prompt=EDUCATIONAL_SYSTEM_PROMPT,
        temperature=0.7,
        max_tokens=500
    )
    return response
```

## 2.4 AI 민감 역할 제한 (AI Role Restrictions)

AI는 특정 **민감한 시나리오**를 수행할 수 없습니다:

### 금지된 AI 역할

```
❌ 심리 상담사 역할 (전문 상담 필요)
❌ 의사/의료진 진단 역할 (의료 면허 필요)
❌ 법률 전문가 역할 (법적 자문 불가)
❌ 금융 자문 역할 (투자 조언 금지)
❌ 위험한 행동 조언 (자해, 범죄 등)
```

### 역할 제한 구현

```python
RESTRICTED_ROLES = [
    "psychologist", "therapist", "counselor",
    "doctor", "physician", "medical",
    "lawyer", "attorney", "legal advisor",
    "financial advisor", "investment advisor"
]

def detect_restricted_role(prompt: str) -> dict:
    """민감 역할 요청 탐지"""
    prompt_lower = prompt.lower()
    
    for role in RESTRICTED_ROLES:
        if role in prompt_lower and any(
            keyword in prompt_lower 
            for keyword in ["act as", "roleplay", "pretend", "you are"]
        ):
            return {
                "is_restricted": True,
                "role": role,
                "message": f"AI는 {role} 역할을 수행할 수 없습니다."
            }
    
    return {"is_restricted": False}

@app.post("/api/v1/ai-tutor")
async def ai_tutor(request: AITutorRequest):
    # 역할 제한 검사
    role_check = detect_restricted_role(request.prompt)
    if role_check["is_restricted"]:
        return {
            "response": f"죄송합니다. {role_check['message']} 전문가와 상담하시기 바랍니다."
        }
    
    response = await call_llm(request.prompt)
    return {"response": response}
```

---

# 🧒 3. 학습자 안전 (Student Safety)

## 3.1 학생 계정 보호 (Student Account Protection)

### Parent-Student 연결 승인

```python
@app.post("/api/v1/parent/link-student")
async def link_student(
    request: LinkStudentRequest,
    parent: User = Depends(get_current_user)
):
    if parent.role != "parent":
        raise HTTPException(403, "Only parents can link students")
    
    # 학생에게 승인 요청
    link_request = await db.execute(
        """
        INSERT INTO parent_student_links (parent_id, student_id, status)
        VALUES (:parent_id, :student_id, 'pending')
        RETURNING *
        """,
        {"parent_id": parent.id, "student_id": request.student_id}
    )
    
    # 학생에게 알림
    await send_notification(
        request.student_id,
        f"{parent.name}님이 학부모 연결을 요청했습니다.",
        link_request_id=link_request.id
    )
    
    return {"status": "pending", "expires_in": "7 days"}

@app.post("/api/v1/student/approve-parent/{link_id}")
async def approve_parent_link(
    link_id: int,
    student: User = Depends(get_current_user)
):
    link = await db.fetchone(
        "SELECT * FROM parent_student_links WHERE id = :id AND student_id = :student_id",
        {"id": link_id, "student_id": student.id}
    )
    
    if not link:
        raise HTTPException(404, "Link request not found")
    
    await db.execute(
        "UPDATE parent_student_links SET status = 'approved', approved_at = NOW() WHERE id = :id",
        {"id": link_id}
    )
    
    # Audit Log 기록
    await log_audit(student.id, "parent_link_approved", link_id)
    
    return {"status": "approved"}
```

### 학생 계정 민감 기능 제한

```python
@app.post("/api/v1/ai-tutor")
async def ai_tutor(
    request: AITutorRequest,
    user: User = Depends(get_current_user)
):
    # 학생은 NSFW 콘텐츠 자동 필터링 (더 엄격)
    if user.role == "student":
        # 학생용 엄격 필터
        safety_check = await check_student_safe_content(request.prompt)
        if not safety_check["is_safe"]:
            raise HTTPException(400, "Content not suitable for students")
    
    response = await call_llm(request.prompt)
    return {"response": response}
```

## 3.2 시험·성적 보호 (Exam & Grade Protection)

### 성적 접근 권한

```sql
-- RLS 정책: 학생 성적은 본인 + 연결된 학부모 + 담당 교사만 조회
CREATE POLICY student_grades_policy ON exam_attempts
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
);
```

### 성적 데이터 보존 정책

```python
@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def cleanup_old_grades():
    """3년 이상 된 성적 데이터 익명화"""
    await db.execute(
        """
        UPDATE exam_attempts SET
            user_id = NULL,
            anonymized = TRUE,
            anonymized_at = NOW()
        WHERE created_at < NOW() - INTERVAL '3 years'
          AND anonymized = FALSE
        """
    )
```

## 3.3 실시간 상호작용 안전 (Real-time Interaction Safety)

### 음성/영상 자동 안전 마스크

```python
@app.post("/api/v1/kzone/dance-lab/upload")
async def upload_dance_video(
    file: UploadFile,
    user: User = Depends(get_current_user)
):
    # 학생 계정은 자동 모자이크 적용
    if user.role == "student":
        # 민감 부위 자동 블러
        safe_video = await auto_blur_sensitive_areas(file)
        upload_url = await upload_to_storage(safe_video)
    else:
        upload_url = await upload_to_storage(file)
    
    return {"video_url": upload_url}
```

---

# 🔐 4. 개인정보 및 프라이버시 보호 (Privacy Protection)

## 4.1 최소 정보 수집 원칙 (Data Minimization)

### 수집 정보

```
✅ 필수 수집:
   - 이메일 (또는 OAuth)
   - 비밀번호 (또는 OAuth)
   - 학습 관련 데이터 (시험 시도, AI 사용 기록)

❌ 수집 금지:
   - 주민등록번호
   - 정확한 주소 (시/구까지만)
   - GPS 위치
   - 신용카드 번호 (결제 대행사 처리)
   - 민감 건강 정보
```

### 최소 수집 검증

```python
@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    # 필수 항목만 수집
    required_fields = {"email", "password", "name", "role"}
    provided_fields = set(request.dict(exclude_unset=True).keys())
    
    # 불필요한 정보 수집 방지
    unnecessary_fields = provided_fields - required_fields
    if unnecessary_fields:
        raise HTTPException(400, f"Unnecessary fields: {unnecessary_fields}")
    
    user = await create_user(request)
    return {"user_id": user.id}
```

## 4.2 개인정보 암호화 (Data Encryption)

### DB 컬럼 단위 암호화 (pgcrypto)

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 전화번호 암호화
ALTER TABLE users ADD COLUMN phone_encrypted BYTEA;

UPDATE users 
SET phone_encrypted = pgp_sym_encrypt(phone, current_setting('app.encryption_key'))
WHERE phone IS NOT NULL;

-- 복호화 함수
CREATE OR REPLACE FUNCTION decrypt_phone(user_id INTEGER)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(
        (SELECT phone_encrypted FROM users WHERE id = user_id),
        current_setting('app.encryption_key')
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 파일 저장 암호화

```python
from cryptography.fernet import Fernet

class FileEncryptor:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    async def encrypt_and_upload(self, file: UploadFile) -> str:
        """파일 암호화 후 R2 업로드"""
        content = await file.read()
        encrypted = self.cipher.encrypt(content)
        
        # Cloudflare R2 업로드 (private)
        url = await r2_client.upload(
            key=f"encrypted/{file.filename}",
            body=encrypted,
            content_type=file.content_type,
            metadata={"encrypted": "true"}
        )
        
        return url
    
    async def download_and_decrypt(self, url: str) -> bytes:
        """R2에서 다운로드 후 복호화"""
        encrypted = await r2_client.download(url)
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted

# 사용
encryptor = FileEncryptor(ENCRYPTION_KEY)
url = await encryptor.encrypt_and_upload(file)
```

## 4.3 프라이버시 권리 (Privacy Rights)

GDPR/PIPA 기준:

### 1. Right to Access (열람권)

```python
@app.get("/api/v1/privacy/my-data")
async def get_my_data(user: User = Depends(get_current_user)):
    """사용자 데이터 전체 다운로드"""
    data = {
        "personal_info": {
            "email": user.email,
            "name": user.name,
            "phone": await decrypt_phone(user.id),
            "created_at": user.created_at
        },
        "exam_history": await get_exam_attempts(user.id),
        "ai_usage": await get_ai_requests(user.id),
        "audit_log": await get_audit_logs(user.id)
    }
    
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": "attachment; filename=my_data.json"}
    )
```

### 2. Right to Erasure (삭제권)

```python
@app.delete("/api/v1/privacy/delete-account")
async def delete_my_account(user: User = Depends(get_current_user)):
    """계정 삭제 (GDPR Right to Erasure)"""
    
    # 1. PII 삭제/익명화
    await db.execute(
        """
        UPDATE users SET
            email = 'deleted_' || id || '@deleted.local',
            phone_encrypted = NULL,
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
    await r2_client.delete_prefix(f"/users/{user.id}/")
    
    # 4. 성적 데이터 익명화 (통계는 유지)
    await db.execute(
        "UPDATE exam_attempts SET user_id = NULL, anonymized = TRUE WHERE user_id = :id",
        {"id": user.id}
    )
    
    return {"status": "deleted", "message": "Account deleted successfully"}
```

### 3. Right to Portability (이동권)

```python
@app.get("/api/v1/privacy/export-data")
async def export_my_data(user: User = Depends(get_current_user)):
    """데이터 이동권 (JSON 다운로드)"""
    data = await get_all_user_data(user.id)
    
    return Response(
        content=json.dumps(data, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=my_data.json"}
    )
```

### 4. Right to Restrict Processing (처리 제한권)

```python
@app.post("/api/v1/privacy/restrict-processing")
async def restrict_processing(user: User = Depends(get_current_user)):
    """데이터 처리 제한"""
    await db.execute(
        "UPDATE users SET processing_restricted = TRUE WHERE id = :id",
        {"id": user.id}
    )
    
    # 제한 중에는 AI 기능 비활성화
    await redis.setex(f"user:{user.id}:restricted", 86400, "true")
    
    return {"status": "restricted", "message": "Data processing restricted"}
```

## 4.4 영상/음성 보호 (Media Data Protection)

### 자동 삭제 정책

```python
@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def cleanup_media_files():
    """영상/음성 자동 삭제"""
    
    # Whisper 업로드 파일 7일 후 삭제
    await r2_client.delete_objects_older_than("/tmp/whisper/", days=7)
    
    # PoseNet 업로드 파일 7일 후 삭제
    await r2_client.delete_objects_older_than("/tmp/posenet/", days=7)
    
    # K-Zone Creator Studio 30일 후 삭제
    await r2_client.delete_objects_older_than("/kzone/creator-studio/", days=30)
```

---

# 👥 5. 사용자 상호작용 안전 (User Interaction Safety)

## 5.1 Parent–Student 승인 (Parent-Student Approval)

```
┌──────────────┐
│  Parent      │  연결 요청
│  Request     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Student     │  승인 (7일 이내)
│  Approval    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Connection  │  연결 확립
│  Established │
└──────────────┘
```

### 승인 만료 처리

```python
@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def expire_pending_links():
    """7일 경과 승인 요청 자동 만료"""
    await db.execute(
        """
        UPDATE parent_student_links SET
            status = 'expired',
            expired_at = NOW()
        WHERE status = 'pending'
          AND created_at < NOW() - INTERVAL '7 days'
        """
    )
```

## 5.2 Teacher–Student 상호작용 (Teacher-Student Interaction)

### 1:1 메시지 제한

```python
@app.post("/api/v1/messages/send")
async def send_message(
    request: MessageRequest,
    sender: User = Depends(get_current_user)
):
    # 학생↔교사 1:1 메시지는 제한
    if sender.role == "student" and request.recipient_role == "teacher":
        # 대시보드/그룹 채팅만 허용
        raise HTTPException(403, "Direct messaging is not allowed. Please use class dashboard.")
    
    # 교사→학생은 허용 (공지, 피드백)
    message = await create_message(sender.id, request.recipient_id, request.content)
    return message
```

### 채팅 로그 보존

```python
@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def cleanup_old_messages():
    """1년 이상 된 채팅 로그 삭제"""
    await db.execute(
        "DELETE FROM messages WHERE created_at < NOW() - INTERVAL '1 year'"
    )
```

## 5.3 커뮤니티 안전 (K-Zone Community Safety)

### 실시간 욕설/혐오 필터

```python
from profanity_check import predict

@app.post("/api/v1/kzone/chat")
async def send_chat_message(
    request: ChatRequest,
    user: User = Depends(get_current_user)
):
    # 욕설 검사
    is_profane = predict([request.message])[0] == 1
    
    if is_profane:
        # 경고 누적
        await increment_warning_count(user.id)
        
        # 경고 횟수 확인
        warning_count = await get_warning_count(user.id)
        
        if warning_count >= 3:
            # 3회 누적 → 24시간 채팅 금지
            await ban_user(user.id, duration=86400, reason="Repeated profanity")
            raise HTTPException(403, "You are temporarily banned from chat (24 hours)")
        
        raise HTTPException(400, "Your message contains inappropriate language")
    
    # 메시지 전송
    message = await broadcast_chat(request.message, user.id)
    return message
```

### 계정 밴 정책

```
1차 경고: 24시간 채팅 제한
2차 경고: 7일 채팅 제한
3차 경고: 30일 계정 정지
4차 경고: 영구 계정 정지
```

```python
async def ban_user(user_id: int, duration: int, reason: str):
    """사용자 계정 제한"""
    await db.execute(
        """
        INSERT INTO user_bans (user_id, duration, reason, expires_at)
        VALUES (:user_id, :duration, :reason, NOW() + INTERVAL ':duration seconds')
        """,
        {"user_id": user_id, "duration": duration, "reason": reason}
    )
    
    # Redis에 밴 정보 캐싱
    await redis.setex(f"user:{user_id}:banned", duration, reason)
    
    # Audit Log 기록
    await log_audit(user_id, "user_banned", {"duration": duration, "reason": reason})
```

---

# 🛠️ 6. 안전 사고 대응 프로세스 (Safety Incident Response)

## 6.1 사고 유형 (Incident Types)

| 사고 유형 | 심각도 | SLA | 담당자 |
|----------|--------|-----|--------|
| **유해 콘텐츠 출력** | P2 | 1시간 | Safety Team |
| **AI 출력 오류** | P3 | 4시간 | AI Team |
| **사용자 간 부적절 상호작용** | P2 | 1시간 | Community Manager |
| **개인정보 노출** | P1 | 15분 | Security + Legal |
| **CSAM (아동 성 착취물)** | P0 | 즉시 | Legal + Law Enforcement |

## 6.2 대응 절차 (Response Procedure)

```
┌──────────────────┐
│  1. 사고 감지    │  AI Filter / User Report / Automated Alert
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  2. 긴급 차단    │  콘텐츠 즉시 삭제 / 계정 일시 정지
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  3. Safety 검토  │  Safety Team 수동 검토
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  4. 원인 분석    │  AI 로그 분석 / 사용자 패턴 분석
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  5. 재발 방지    │  필터 업데이트 / 정책 변경 / 모델 재학습
└──────────────────┘
```

### 자동 사고 감지

```python
@app.on_event("startup")
@repeat_every(seconds=300)  # 5분마다
async def safety_incident_monitor():
    """안전 사고 자동 감지"""
    
    # 1. 유해 콘텐츠 급증 감지
    harmful_content_count = await db.scalar(
        "SELECT count(*) FROM safety_logs WHERE type = 'harmful_content' AND created_at > NOW() - INTERVAL '1 hour'"
    )
    if harmful_content_count > 10:
        await send_alert("🚨 Harmful content spike detected (10+ in last hour)")
    
    # 2. AI 출력 오류 급증
    ai_error_count = await db.scalar(
        "SELECT count(*) FROM safety_logs WHERE type = 'ai_error' AND created_at > NOW() - INTERVAL '1 hour'"
    )
    if ai_error_count > 50:
        await send_alert("⚠️ AI output error spike detected (50+ in last hour)")
    
    # 3. 사용자 신고 급증
    user_report_count = await db.scalar(
        "SELECT count(*) FROM user_reports WHERE created_at > NOW() - INTERVAL '1 hour'"
    )
    if user_report_count > 20:
        await send_alert("📢 User report spike detected (20+ in last hour)")
```

## 6.3 사용자 신고 시스템 (User Reporting System)

### 신고 버튼

```python
@app.post("/api/v1/report")
async def report_content(
    request: ReportRequest,
    user: User = Depends(get_current_user)
):
    """콘텐츠/사용자 신고"""
    report = await db.execute(
        """
        INSERT INTO user_reports (reporter_id, content_id, content_type, reason, description, status)
        VALUES (:reporter_id, :content_id, :content_type, :reason, :description, 'pending')
        RETURNING *
        """,
        {
            "reporter_id": user.id,
            "content_id": request.content_id,
            "content_type": request.content_type,  # 'message', 'video', 'image', 'user'
            "reason": request.reason,  # 'spam', 'harassment', 'inappropriate', 'hate'
            "description": request.description
        }
    )
    
    # Safety Team에 Slack 알림
    await send_slack(
        "#safety-alerts",
        f"New report: {request.content_type} - {request.reason}\nReporter: {user.email}"
    )
    
    return {"status": "pending", "report_id": report.id}
```

### 신고 처리 SLA

```
P0 (CSAM, 아동 학대): 즉시 처리 + 법 집행 기관 신고
P1 (개인정보 노출): 15분 이내
P2 (유해 콘텐츠, 괴롭힘): 1시간 이내
P3 (스팸, 기타): 24시간 이내
```

---

# 📋 7. 안전 관련 로그 및 보존 규정 (Safety Logs & Retention)

## 7.1 로그 보존 기간

| 로그 유형 | 보존 기간 | 삭제 방법 |
|----------|----------|----------|
| **유해 출력 로그** | 90일 | Auto-delete |
| **사용자 신고 사건** | 1년 | Anonymize |
| **AI Abuse 탐지 로그** | 180일 | Auto-delete |
| **계정 밴 기록** | 2년 | Anonymize |
| **CSAM 사고** | 영구 보존 | 법적 요구 시만 삭제 |

## 7.2 로그 자동 삭제

```python
@app.on_event("startup")
@repeat_every(seconds=86400)  # 1일마다
async def cleanup_safety_logs():
    """안전 로그 자동 삭제"""
    
    # 90일 이상 된 유해 출력 로그 삭제
    await db.execute(
        "DELETE FROM safety_logs WHERE type = 'harmful_output' AND created_at < NOW() - INTERVAL '90 days'"
    )
    
    # 180일 이상 된 AI Abuse 로그 삭제
    await db.execute(
        "DELETE FROM safety_logs WHERE type = 'ai_abuse' AND created_at < NOW() - INTERVAL '180 days'"
    )
    
    # 1년 이상 된 사용자 신고 익명화
    await db.execute(
        """
        UPDATE user_reports SET
            reporter_id = NULL,
            anonymized = TRUE
        WHERE created_at < NOW() - INTERVAL '1 year'
          AND anonymized = FALSE
        """
    )
```

---

# 🏁 8. 결론 (Conclusion)

이 **User Safety Guide**는 DreamSeedAI MegaCity의 교육·문화·AI 서비스가 **학생·학부모·교사 모두에게 안전하게 제공**될 수 있도록 보장하는 핵심 기준 문서입니다.

## 핵심 안전 원칙

```
1. 콘텐츠 안전 우선 (Content Safety First)
   - 유해 콘텐츠 즉시 차단
   - K-Zone 동의 기반 얼굴/음성 합성

2. AI 안전성 보장 (AI Safety)
   - Prompt Injection 방어
   - 유해 출력 자동 필터링
   - 교육적 프레이밍 적용

3. 학습자 보호 (Student Protection)
   - Parent-Student 승인 체계
   - 성적 데이터 접근 제한
   - 실시간 상호작용 안전

4. 프라이버시 최우선 (Privacy First)
   - 최소 정보 수집
   - 암호화 및 보안
   - GDPR/PIPA 권리 보장

5. 신속한 사고 대응 (Rapid Response)
   - 24시간 신고 처리 SLA
   - P0 사고 즉시 대응
   - 재발 방지 조치
```

## 안전 체크리스트

```
□ 콘텐츠 필터 (NSFW, Hate Speech, Violence) 활성
□ AI Prompt Injection 방어 활성
□ AI 출력 유해성 검사 활성
□ Parent-Student 승인 체계 운영
□ 성적 데이터 RLS 정책 적용
□ 개인정보 암호화 (pgcrypto) 적용
□ GDPR/PIPA 권리 (Access, Erasure, Portability) 구현
□ 사용자 신고 시스템 활성 (24시간 SLA)
□ 안전 로그 보존 정책 준수 (90일~2년)
□ 긴급 사고 대응 절차 문서화
```

MegaCity의 **AI Safety · Content Safety · Privacy 보호 · 역할·승인 체계**가 함께 동작하여 전체 사용자에게 **신뢰 기반 경험**을 제공합니다.

---

**문서 완료 - DreamSeedAI MegaCity User Safety Guide v1.0**
