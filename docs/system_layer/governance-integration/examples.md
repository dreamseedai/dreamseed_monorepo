# 거버넌스 통합 예시 (Governance Integration Examples)

이 문서는 시스템 계층의 다양한 서비스에서 거버넌스 계층의 정책을 적용하는 실제 코드 예시를 제공합니다.

## 목차

1. [기본 패턴](#기본-패턴)
2. [AI 튜터링 서비스](#ai-튜터링-서비스)
3. [과제 배정 서비스](#과제-배정-서비스)
4. [데이터 접근 제어](#데이터-접근-제어)
5. [AI 콘텐츠 필터링](#ai-콘텐츠-필터링)
6. [시험 제출 관리](#시험-제출-관리)
7. [승인 워크플로우](#승인-워크플로우)
8. [속도 제한](#속도-제한)
9. [고급 패턴](#고급-패턴)

---

## 기본 패턴

### 1. 데코레이터 방식 (가장 간단)

```python
from fastapi import FastAPI, Request, HTTPException
from governance.backend import require_policy

app = FastAPI()

@app.post("/api/lessons")
@require_policy("dreamseedai.content.create")
async def create_lesson(request: Request, lesson_data: dict):
    """
    수업 콘텐츠를 생성합니다.
    
    정책 검증:
    - 사용자가 교사 역할인지 확인
    - 콘텐츠 생성 권한이 있는지 확인
    """
    # 정책 통과 후 실행됨
    lesson = await lesson_service.create(lesson_data)
    return {"lesson_id": lesson.id}
```

### 2. 미들웨어 방식 (글로벌 적용)

```python
from fastapi import FastAPI
from governance.backend import PolicyEnforcementMiddleware

app = FastAPI()

# 모든 요청에 정책 적용 (제외 경로 제외)
app.add_middleware(
    PolicyEnforcementMiddleware,
    excluded_paths=["/health", "/metrics", "/docs", "/openapi.json"]
)

@app.get("/api/protected-resource")
async def get_resource(request: Request):
    # 미들웨어가 자동으로 정책 검증
    # dreamseedai.access_control.allow 정책 사용
    return {"data": "protected"}
```

### 3. 수동 방식 (세밀한 제어)

```python
from fastapi import FastAPI, Request, HTTPException
from governance.backend import get_policy_client

app = FastAPI()

@app.post("/api/custom-operation")
async def custom_operation(request: Request, data: dict):
    """여러 정책을 순차적으로 검증하는 커스텀 로직"""
    
    policy_client = get_policy_client()
    user = request.state.user
    
    # 1단계: 접근 권한 검증
    access_result = await policy_client.evaluate(
        "dreamseedai.access_control.allow",
        {
            "user": {"id": user.id, "role": user.role},
            "resource": {"path": "/api/custom-operation", "method": "POST"}
        }
    )
    
    if not access_result.get("allow"):
        raise HTTPException(403, detail="Access denied")
    
    # 2단계: 속도 제한 검증
    rate_limit_result = await policy_client.evaluate(
        "dreamseedai.rate_limit.check",
        {
            "user": {"id": user.id},
            "action": "custom_operation",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    
    if not rate_limit_result.get("allow"):
        raise HTTPException(429, detail="Rate limit exceeded")
    
    # 모든 정책 통과 후 비즈니스 로직 실행
    result = await execute_custom_logic(data)
    return result
```

---

## AI 튜터링 서비스

### 질의응답 (AI Behavior Policy)

```python
from fastapi import FastAPI, Request, HTTPException
from governance.backend import require_policy, get_policy_client

app = FastAPI()

@app.post("/api/tutor/ask")
@require_policy("dreamseedai.ai_tutor.query")
async def ask_tutor(
    request: Request,
    student_id: str,
    question: str,
    context: dict = None
):
    """
    AI 튜터에게 질문합니다.
    
    정책 검증:
    - AI 사용 시간대 (학습 시간 내)
    - 학생의 AI 튜터 사용 권한
    - 질문 콘텐츠 필터링 (부적절한 내용 차단)
    """
    # 1. 학생 데이터 가져오기
    student = await get_student(student_id)
    
    # 2. 질문 분석
    topic = await analyze_question(question)
    difficulty = await estimate_difficulty(question)
    
    # 3. AI 응답 생성
    ai_response = await ai_tutoring_service.generate_response(
        student_data=student,
        question=question,
        topic=topic,
        difficulty=difficulty,
        context=context
    )
    
    # 4. 응답 콘텐츠 필터링 (AI Content Policy)
    policy_client = get_policy_client()
    filter_result = await policy_client.evaluate(
        "dreamseedai.ai_content.filter",
        {
            "user": {"id": student_id, "role": "student"},
            "content": {
                "text": ai_response,
                "type": "ai_generated",
                "topic": topic
            }
        }
    )
    
    if not filter_result.get("allow"):
        # 콘텐츠 정책 위반 시 안전한 응답 반환
        return {
            "response": "죄송합니다. 해당 질문에 대해 적절한 답변을 제공할 수 없습니다.",
            "reason": filter_result.get("reason"),
            "filtered": True
        }
    
    return {
        "response": ai_response,
        "topic": topic,
        "difficulty": difficulty,
        "filtered": False
    }
```

### 학습 자료 추천

```python
@app.get("/api/tutor/recommend/{student_id}")
@require_policy("dreamseedai.ai_tutor.recommend")
async def recommend_materials(
    request: Request,
    student_id: str,
    subject: str = None
):
    """
    학생에게 맞춤형 학습 자료를 추천합니다.
    
    정책 검증:
    - 학생의 개인 데이터 접근 권한
    - AI 추천 시스템 사용 권한
    """
    # 학생의 학습 이력 및 수준 분석
    learning_history = await get_learning_history(student_id)
    current_level = await estimate_student_level(student_id, subject)
    
    # AI 추천 시스템
    recommendations = await ai_recommendation_service.recommend(
        student_id=student_id,
        subject=subject,
        current_level=current_level,
        history=learning_history
    )
    
    return {
        "recommendations": recommendations,
        "student_level": current_level
    }
```

---

## 과제 배정 서비스

### 과제 생성 및 배정

```python
from datetime import datetime, timezone

@app.post("/api/assignments")
@require_policy("dreamseedai.assignment.create")
async def create_assignment(
    request: Request,
    student_ids: list[str],
    content_id: str,
    due_date: str,
    metadata: dict = None
):
    """
    학생들에게 과제를 배정합니다.
    
    정책 검증:
    - 교사가 해당 학생들의 담당 교사인지 확인
    - 과제 배정 권한 확인
    - 시간대 제약 확인 (예: 업무 시간 내)
    """
    teacher = request.state.user
    
    # 콘텐츠 정보 가져오기
    content = await get_content(content_id)
    
    # 각 학생에 대해 배정
    assignments = []
    for student_id in student_ids:
        # 학생 정보 확인
        student = await get_student(student_id)
        
        # 교사-학생 관계 확인 (정책에서 이미 검증되었지만 추가 확인)
        if not await is_teacher_of_student(teacher.id, student_id):
            raise HTTPException(403, detail=f"Not authorized for student {student_id}")
        
        # 과제 생성
        assignment = await assignment_service.create(
            student_id=student_id,
            content_id=content_id,
            teacher_id=teacher.id,
            due_date=due_date,
            metadata=metadata
        )
        
        assignments.append(assignment)
    
    # 알림 발송
    await notification_service.send_assignment_notification(
        student_ids=student_ids,
        assignment_title=content.title,
        due_date=due_date
    )
    
    return {
        "assignments": [{"id": a.id, "student_id": a.student_id} for a in assignments],
        "total": len(assignments)
    }
```

### 과제 제출

```python
@app.post("/api/assignments/{assignment_id}/submit")
@require_policy("dreamseedai.assignment.submit")
async def submit_assignment(
    request: Request,
    assignment_id: str,
    submission_data: dict
):
    """
    과제를 제출합니다.
    
    정책 검증:
    - 학생이 해당 과제에 배정되어 있는지 확인
    - 제출 마감일 확인
    - 이미 제출했는지 확인
    """
    student = request.state.user
    
    # 과제 정보 가져오기
    assignment = await get_assignment(assignment_id)
    
    # 마감일 확인 (추가 검증)
    if datetime.fromisoformat(assignment.due_date) < datetime.now(timezone.utc):
        raise HTTPException(400, detail="Assignment deadline has passed")
    
    # 제출 처리
    submission = await assignment_service.submit(
        assignment_id=assignment_id,
        student_id=student.id,
        data=submission_data,
        submitted_at=datetime.now(timezone.utc)
    )
    
    return {
        "submission_id": submission.id,
        "submitted_at": submission.submitted_at
    }
```

---

## 데이터 접근 제어

### 학생 학습 기록 조회

```python
@app.get("/api/students/{student_id}/records")
@require_policy("dreamseedai.data_protection.student_record")
async def get_student_records(
    request: Request,
    student_id: str,
    subject: str = None,
    date_from: str = None,
    date_to: str = None
):
    """
    학생의 학습 기록을 조회합니다.
    
    정책 검증:
    - 교사: 자신의 학급 학생만 조회 가능
    - 학생: 본인의 기록만 조회 가능
    - 관리자: 모든 학생 기록 조회 가능
    - 부모: 자녀의 기록만 조회 가능
    """
    user = request.state.user
    
    # 학습 기록 조회
    records = await get_learning_records(
        student_id=student_id,
        subject=subject,
        date_from=date_from,
        date_to=date_to
    )
    
    # 민감 정보 마스킹 (역할에 따라)
    if user.role == "parent":
        # 부모에게는 일부 민감한 정보 숨김
        records = mask_sensitive_data(records, level="parent")
    
    return {
        "student_id": student_id,
        "records": records,
        "total": len(records)
    }
```

### 개인정보(PII) 접근

```python
@app.get("/api/students/{student_id}/personal-info")
@require_policy("dreamseedai.data_protection.pii")
async def get_personal_info(
    request: Request,
    student_id: str
):
    """
    학생의 개인정보를 조회합니다.
    
    정책 검증:
    - 매우 제한적인 접근 (관리자, 본인만)
    - 접근 이유 필수 (감사 로그에 기록됨)
    - 데이터 마스킹 적용
    """
    user = request.state.user
    
    # 개인정보 가져오기
    personal_info = await get_student_personal_info(student_id)
    
    # 역할에 따라 마스킹
    if user.role != "admin":
        personal_info = mask_pii(personal_info, level="high")
    
    return {
        "student_id": student_id,
        "personal_info": personal_info
    }
```

---

## AI 콘텐츠 필터링

### 콘텐츠 생성 시 필터링

```python
@app.post("/api/ai/generate-content")
async def generate_ai_content(
    request: Request,
    prompt: str,
    content_type: str,
    target_age: int = None
):
    """
    AI가 교육 콘텐츠를 생성하고 필터링합니다.
    
    정책 검증:
    - AI 콘텐츠 정책 (부적절한 내용, 편향성 등)
    - 연령 적합성 검증
    """
    user = request.state.user
    
    # AI 콘텐츠 생성
    generated_content = await ai_service.generate_content(
        prompt=prompt,
        content_type=content_type,
        target_age=target_age
    )
    
    # 콘텐츠 필터링
    policy_client = get_policy_client()
    
    filter_result = await policy_client.evaluate(
        "dreamseedai.ai_content.filter",
        {
            "user": {"id": user.id, "role": user.role},
            "content": {
                "text": generated_content,
                "type": content_type,
                "target_age": target_age
            }
        }
    )
    
    if not filter_result.get("allow"):
        # 필터링된 경우
        violation_type = filter_result.get("violation_type", "unknown")
        
        # 심각도에 따라 처리
        if filter_result.get("severity") == "high":
            # 높은 심각도: 즉시 거부 및 관리자 알림
            await notification_service.alert_admins(
                type="content_violation",
                severity="high",
                user_id=user.id,
                content_preview=generated_content[:100],
                violation_type=violation_type
            )
            raise HTTPException(
                status_code=400,
                detail=f"Content violated policy: {violation_type}"
            )
        else:
            # 낮은 심각도: 경고와 함께 수정 제안
            return {
                "status": "filtered",
                "reason": filter_result.get("reason"),
                "violation_type": violation_type,
                "suggestion": "Please rephrase your prompt to avoid sensitive content"
            }
    
    return {
        "status": "success",
        "content": generated_content,
        "filtered": False
    }
```

---

## 시험 제출 관리

### 시험 제출 (복합 정책)

```python
@app.post("/api/exams/{exam_id}/submit")
@require_policy("dreamseedai.exam.submit")
async def submit_exam(
    request: Request,
    exam_id: str,
    answers: dict,
    metadata: dict = None
):
    """
    시험 답안을 제출합니다.
    
    정책 검증:
    - 시험 시간대 내인지 확인
    - 학생이 해당 시험에 등록되어 있는지 확인
    - 이미 제출했는지 확인
    - 부정행위 감지 (이상 패턴)
    """
    student = request.state.user
    
    # 시험 정보 가져오기
    exam = await get_exam(exam_id)
    
    # 추가 검증: 시험 시간
    now = datetime.now(timezone.utc)
    exam_start = datetime.fromisoformat(exam.start_time)
    exam_end = datetime.fromisoformat(exam.end_time)
    
    if now < exam_start:
        raise HTTPException(400, detail="Exam has not started yet")
    if now > exam_end:
        raise HTTPException(400, detail="Exam time has expired")
    
    # 이상 행동 감지 (정책 엔진 추가 호출)
    policy_client = get_policy_client()
    anomaly_result = await policy_client.evaluate(
        "dreamseedai.exam.anomaly_detection",
        {
            "user": {"id": student.id},
            "exam": {"id": exam_id},
            "metadata": metadata,
            "submission_time": now.isoformat()
        }
    )
    
    if not anomaly_result.get("allow"):
        # 이상 행동 감지 시
        await notification_service.alert_teachers(
            exam_id=exam_id,
            student_id=student.id,
            reason="Potential anomaly detected during exam submission"
        )
        # 제출은 허용하지만 플래그 표시
        flagged = True
    else:
        flagged = False
    
    # 제출 처리
    submission = await exam_service.submit(
        exam_id=exam_id,
        student_id=student.id,
        answers=answers,
        submitted_at=now,
        flagged=flagged
    )
    
    return {
        "submission_id": submission.id,
        "submitted_at": submission.submitted_at,
        "flagged": flagged
    }
```

---

## 승인 워크플로우

### 추가 시험 기회 요청

```python
@app.post("/api/approval/extra-exam-attempt")
@require_policy("dreamseedai.approval.request")
async def request_extra_exam_attempt(
    request: Request,
    exam_id: str,
    reason: str
):
    """
    추가 시험 기회를 요청합니다.
    
    정책 검증:
    - 학생이 요청 권한이 있는지 확인
    - 이미 요청했는지 확인
    """
    student = request.state.user
    
    # 승인 요청 생성
    approval_request = await approval_service.create_request(
        requester_id=student.id,
        action_type="extra_exam_attempt",
        target_id=exam_id,
        reason=reason,
        status="pending"
    )
    
    # 담당 교사에게 알림
    exam = await get_exam(exam_id)
    await notification_service.notify_teachers(
        class_id=exam.class_id,
        message=f"학생 {student.name}이(가) 추가 시험 기회를 요청했습니다.",
        approval_request_id=approval_request.id
    )
    
    return {
        "approval_request_id": approval_request.id,
        "status": "pending"
    }
```

### 승인 처리

```python
@app.post("/api/approval/{request_id}/approve")
@require_policy("dreamseedai.approval.approve")
async def approve_request(
    request: Request,
    request_id: str,
    approved: bool,
    comment: str = None
):
    """
    승인 요청을 처리합니다.
    
    정책 검증:
    - 교사 또는 관리자만 승인 가능
    - 자신의 학급 학생 요청만 승인 가능
    """
    approver = request.state.user
    
    # 승인 요청 정보 가져오기
    approval_request = await get_approval_request(request_id)
    
    # 승인 처리
    result = await approval_service.process(
        request_id=request_id,
        approver_id=approver.id,
        approved=approved,
        comment=comment,
        processed_at=datetime.now(timezone.utc)
    )
    
    # 요청자에게 알림
    await notification_service.notify_user(
        user_id=approval_request.requester_id,
        message=f"요청이 {'승인' if approved else '거부'}되었습니다.",
        details=comment
    )
    
    return {
        "request_id": request_id,
        "approved": approved,
        "processed_at": result.processed_at
    }
```

---

## 속도 제한

### API 호출 속도 제한

```python
@app.post("/api/ai/query")
async def ai_query(request: Request, query: str):
    """
    AI 서비스에 쿼리를 보냅니다.
    
    정책 검증:
    - 분당 요청 횟수 제한
    - 사용자 역할별 다른 제한
    """
    user = request.state.user
    
    # 속도 제한 검증
    policy_client = get_policy_client()
    rate_limit_result = await policy_client.evaluate(
        "dreamseedai.rate_limit.check",
        {
            "user": {"id": user.id, "role": user.role},
            "action": "ai_query",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    
    if not rate_limit_result.get("allow"):
        # 속도 제한 초과
        retry_after = rate_limit_result.get("retry_after", 60)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
    
    # AI 쿼리 처리
    result = await ai_service.query(query)
    
    return {"result": result}
```

---

## 고급 패턴

### 다중 정책 조합

```python
async def complex_operation_with_multiple_policies(
    user_id: str,
    resource_id: str,
    action: str
):
    """여러 정책을 조합하여 복잡한 비즈니스 로직 구현"""
    
    policy_client = get_policy_client()
    
    # 정책 체인 정의
    policy_chain = [
        {
            "name": "access_control",
            "policy": "dreamseedai.access_control.allow",
            "input": lambda: {
                "user": {"id": user_id},
                "resource": {"id": resource_id, "action": action}
            }
        },
        {
            "name": "rate_limit",
            "policy": "dreamseedai.rate_limit.check",
            "input": lambda: {
                "user": {"id": user_id},
                "action": action,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        },
        {
            "name": "data_protection",
            "policy": "dreamseedai.data_protection.check",
            "input": lambda: {
                "user": {"id": user_id},
                "resource": {"id": resource_id, "type": "sensitive"}
            }
        }
    ]
    
    # 순차 검증
    for policy_config in policy_chain:
        result = await policy_client.evaluate(
            policy_config["policy"],
            policy_config["input"]()
        )
        
        if not result.get("allow"):
            raise HTTPException(
                status_code=403,
                detail=f"Policy {policy_config['name']} denied: {result.get('reason')}"
            )
    
    # 모든 정책 통과
    return True
```

### 조건부 정책 적용

```python
@app.post("/api/content/publish")
async def publish_content(
    request: Request,
    content_id: str,
    target_audience: str
):
    """
    콘텐츠를 게시합니다.
    조건에 따라 다른 정책을 적용합니다.
    """
    user = request.state.user
    content = await get_content(content_id)
    
    policy_client = get_policy_client()
    
    # 대상 청중에 따라 다른 정책 적용
    if target_audience == "all":
        # 전체 공개: 엄격한 승인 필요
        policy_path = "dreamseedai.content.publish_public"
    elif target_audience == "class":
        # 학급 내 공개: 교사 권한 확인
        policy_path = "dreamseedai.content.publish_class"
    else:
        # 개인 공개: 기본 권한 확인
        policy_path = "dreamseedai.content.publish_private"
    
    result = await policy_client.evaluate(
        policy_path,
        {
            "user": {"id": user.id, "role": user.role},
            "content": {"id": content_id, "type": content.type},
            "target": {"audience": target_audience}
        }
    )
    
    if not result.get("allow"):
        raise HTTPException(403, detail=result.get("reason"))
    
    # 게시 처리
    await content_service.publish(content_id, target_audience)
    
    return {"status": "published", "audience": target_audience}
```

---

## 참조

- **거버넌스 계층**: [governance/backend/README.md](../../../governance/backend/README.md)
- **정책 파일**: [governance/policies/](../../../governance/policies/)
- **정책 적용 가이드**: [policy-enforcement.md](policy-enforcement.md)
- **감사 로깅 통합**: [audit-logging.md](audit-logging.md)
