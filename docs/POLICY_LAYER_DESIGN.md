# DreamSeedAI: 2. 정책 계층 (Policy Layer) 상세 설계

정책 계층은 거버넌스 계층의 원칙들을 실제 플랫폼 내 규칙과 로직으로 구현한 계층입니다. 쉽게 말해, 거버넌스가 "무엇을 해야 한다/하지 말아야 한다"를 정했다면, 정책 계층은 "그것을 실현하기 위해 시스템이 따라야 할 세부 규칙과 실행 방법"을 다룹니다.

---

## 1. 핵심 역할

*   **원칙의 구체화**: 거버넌스 계층에서 제시된 추상적인 원칙을 구체적인 정책 및 규칙으로 변환합니다.
*   **시스템 제어**: 시스템 계층의 동작을 제어하고, AI 알고리즘의 행동 범위를 정의합니다.
*   **실행 방법 명시**: 정책을 시행하기 위한 절차, 기술적 구현 방법, 및 책임 소재를 명확히 합니다.
*   **상황별 정책 적용**: 플랫폼 운영 상황에 따라 적절한 정책을 선택적으로 적용합니다.

---

## 2. 주요 구성 요소

### 2.1 정책 엔진 (Policy Engine)

정책 규칙을 평가하고 실행하는 핵심 컴포넌트입니다.

**구현 기술**: Open Policy Agent (OPA)

**특징**:
*   규칙 기반 시스템 (Rule-Based System): 사전 정의된 규칙에 따라 의사 결정 수행
*   Rego 언어: 선언적 정책 언어로 복잡한 규칙 표현 가능
*   실시간 평가: HTTP API를 통한 밀리초 단위 정책 평가
*   머신 러닝 통합 (선택): 학습된 모델을 사용하여 상황에 맞는 정책 적용

**DreamSeedAI 구현 현황**:
```
governance/
├── bundles/
│   ├── phase0.rego          # 기본 정책 (개발/테스트)
│   ├── phase1.rego          # 중급 정책 (스테이징)
│   └── production.rego      # 운영 정책 (프로덕션)
└── compiled/
    ├── phase0.json
    ├── phase1.json
    └── production.json
```

### 2.2 정책 저장소 (Policy Repository)

정책 규칙, 설정, 및 관련 메타데이터를 저장하는 시스템입니다.

**구현 방식**:
*   **Git 저장소**: 정책 소스 코드 버전 관리
*   **ConfigMap**: Kubernetes에서 컴파일된 정책 번들 저장
*   **데이터베이스**: 정책 메타데이터 및 실행 이력 저장

**DreamSeedAI 구현**:
```yaml
# ops/k8s/governance/base/configmap-policy-bundle.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: governance-policy-bundle
data:
  policy.json: |
    {컴파일된 OPA 정책 번들}
```

**버전 관리**:
*   정책 변경 시 Git 커밋으로 이력 추적
*   ConfigMap Hash를 통한 자동 Hot Reload
*   롤백 가능 (Git revert + 재배포)

### 2.3 정책 관리 인터페이스 (Policy Management Interface)

관리자가 정책을 생성, 수정, 삭제, 및 배포할 수 있는 시스템입니다.

**기능**:
*   정책 편집: Rego 코드 편집 및 검증
*   테스트: 정책 시뮬레이션 및 단위 테스트
*   배포: 환경별 정책 배포 (dev → staging → production)
*   감사: 정책 변경 이력 조회

**DreamSeedAI 구현 계획**:
*   **현재**: Git + 수동 배포
*   **향후**:
    *   Web UI: FastAPI 기반 정책 관리 대시보드
    *   API: RESTful API로 정책 CRUD
    *   승인 워크플로: 정책 변경 승인 프로세스

### 2.4 모니터링 및 감사 시스템 (Monitoring and Auditing System)

정책 시행 상황을 모니터링하고, 감사 기록을 생성합니다.

**DreamSeedAI 구현 현황**:

#### Prometheus 메트릭 (19개)
```yaml
# Governance 메트릭 (7개)
- governance_policy_evaluations_total      # 정책 평가 횟수
- governance_policy_deny_total             # 정책 거부 횟수
- governance_policy_bundle_reload_total    # 정책 번들 리로드 횟수
- governance_policy_errors_total           # 정책 평가 오류
- governance_policy_evaluation_duration    # 정책 평가 지연시간
- governance_policy_bundle_version         # 현재 정책 번들 버전
- governance_policy_hot_reload_success     # Hot Reload 성공 여부
```

#### 알림 규칙 (15개 중 정책 관련 5개)
```yaml
- GovernancePolicyBundleLoadFailure        # Critical: 정책 번들 로드 실패
- GovernancePolicyEvaluationErrors         # Warning: 정책 평가 오류 급증
- GovernanceHighDenyRate                   # Warning: 정책 거부율 높음
- GovernancePolicyBundleStale              # Warning: 정책 번들 오래됨
- GovernanceHotReloadFailure               # Warning: Hot Reload 실패
```

#### Grafana 대시보드
*   정책 평가 성공/실패율 시각화
*   정책별 거부율 추이
*   정책 평가 지연시간 분포
*   정책 번들 버전 이력

#### Alertmanager (Slack 통합)
*   Critical 알림: 즉시 Slack 전송 (빨강색)
*   Warning 알림: 30초 그룹화 후 전송 (주황색)

---

## 3. 정책 엔진 동작 방식

### 3.1 실행 흐름

```
1. 상황 인식
   ↓
2. 정책 검색
   ↓
3. 규칙 평가
   ↓
4. 액션 실행
   ↓
5. 로깅 및 감사
```

### 3.2 상세 단계

#### 1️⃣ 상황 인식
정책 엔진은 플랫폼 운영 시점에 대한 정보를 수집합니다.

**수집 데이터**:
*   요청 컨텍스트: user_id, role, phase, endpoint
*   학생 활동: 학습 활동, 콘텐츠 접근, 문제 제출
*   교사 작업: 관리 작업, 데이터 접근, 리포트 생성
*   시스템 이벤트: AI 모델 호출, 데이터베이스 쿼리, 외부 API 호출

**DreamSeedAI 구현**:
```python
# governance/backend/policy_middleware.py
async def policy_middleware(request: Request, call_next):
    # 1. 컨텍스트 수집
    user_id = request.headers.get("X-User-ID")
    role = request.headers.get("X-User-Role")
    phase = os.getenv("DEPLOYMENT_PHASE", "phase0")
    
    # 2. 정책 평가 입력 생성
    input_data = {
        "user": {"id": user_id, "role": role},
        "request": {
            "method": request.method,
            "path": request.url.path,
            "phase": phase
        }
    }
```

#### 2️⃣ 정책 검색
정책 엔진은 수집된 정보를 기반으로 해당 상황에 적용 가능한 정책 규칙을 검색합니다.

**DreamSeedAI 구현**:
```python
# governance/backend/policy_routes.py
ROUTE_POLICY_MAP = {
    r"^/api/curriculum/.*": {
        "policy": "curriculum_access",
        "require_feature_flag": "curriculum_management"
    },
    r"^/api/students/\d+/data$": {
        "policy": "student_data_access",
        "require_feature_flag": "student_data_access"
    },
    # ... 34개 엔드포인트 매핑
}
```

#### 3️⃣ 규칙 평가
정책 엔진은 검색된 정책 규칙을 평가하고, 규칙 충족 여부를 판단합니다.

**OPA 정책 평가**:
```python
# governance/backend/policy_controller.py
async def evaluate_policy(policy_name: str, input_data: dict) -> dict:
    response = await http_client.post(
        f"{OPA_URL}/v1/data/{policy_name}",
        json={"input": input_data}
    )
    result = response.json()["result"]
    
    # 메트릭 기록
    GOVERNANCE_EVALUATIONS.labels(
        policy=policy_name,
        decision="allow" if result["allow"] else "deny"
    ).inc()
    
    return result
```

**정책 예시 (Rego)**:
```rego
# governance/bundles/phase0.rego
package curriculum_access

default allow = false

# 교사는 모든 커리큘럼 접근 가능
allow {
    input.user.role == "teacher"
}

# 학생은 자신의 학년 커리큘럼만 접근 가능
allow {
    input.user.role == "student"
    input.request.grade == input.user.grade
}

# 거부 사유 생성
deny[msg] {
    not allow
    msg := sprintf("User %s cannot access curriculum", [input.user.id])
}
```

#### 4️⃣ 액션 실행
규칙을 충족하는 경우, 정책 엔진은 해당 규칙에 정의된 액션을 실행합니다.

**액션 유형**:
*   **허용 (Allow)**: 요청 통과, 다음 미들웨어로 이동
*   **거부 (Deny)**: HTTP 403 Forbidden 응답
*   **조건부 허용**: 특정 조건 충족 시 허용 (예: 데이터 마스킹 후 허용)
*   **알림**: 관리자에게 알림 전송 (예: 민감한 데이터 접근 시)
*   **로깅**: 감사 로그 기록

**DreamSeedAI 구현**:
```python
# governance/backend/policy_middleware.py
if not result["allow"]:
    # 거부 메트릭 기록
    GOVERNANCE_DENY.labels(
        policy=policy_name,
        reason=result.get("deny", ["unknown"])[0]
    ).inc()
    
    # 403 응답
    raise HTTPException(
        status_code=403,
        detail={"error": "Policy violation", "reason": result["deny"]}
    )

# 허용 - 요청 계속 진행
response = await call_next(request)
return response
```

#### 5️⃣ 로깅 및 감사
정책 엔진의 모든 활동은 감사 로그에 기록됩니다.

**로그 항목**:
*   타임스탬프
*   사용자 정보 (user_id, role)
*   요청 정보 (method, path, parameters)
*   정책 이름
*   평가 결과 (allow/deny)
*   거부 사유
*   실행 시간

**DreamSeedAI 구현**:
```python
# 구조화된 로깅
logger.info(
    "Policy evaluation",
    extra={
        "user_id": user_id,
        "role": role,
        "policy": policy_name,
        "decision": "allow" if result["allow"] else "deny",
        "duration_ms": duration * 1000
    }
)
```

**Prometheus 메트릭으로 집계**:
```promql
# 시간별 정책 거부율
rate(governance_policy_deny_total[5m]) 
  / 
rate(governance_policy_evaluations_total[5m])
```

---

## 4. 정책 예시

### 4.1 개인 정보 보호 정책

**규칙**: 학생 데이터는 익명화 처리 후 AI 모델 학습에 사용해야 한다.

**Rego 정책**:
```rego
package student_data_anonymization

default allow = false

# AI 학습용 데이터는 익명화 필수
allow {
    input.purpose == "ai_training"
    input.data.anonymized == true
}

# 익명화되지 않은 데이터 사용 거부
deny[msg] {
    input.purpose == "ai_training"
    input.data.anonymized != true
    msg := "Student data must be anonymized for AI training"
}
```

**액션**:
*   AI 모델 학습 전에 학생 ID, 이름 등 개인 식별 정보 제거
*   SHA-256 해시로 ID 변환
*   생년월일 → 연령대로 변환
*   이름 → 제거

**구현**:
```python
def anonymize_student_data(student_data: dict) -> dict:
    return {
        "student_hash": hashlib.sha256(student_data["id"].encode()).hexdigest(),
        "age_group": calculate_age_group(student_data["birth_date"]),
        "grade": student_data["grade"],
        "performance": student_data["performance"],
        # 개인 식별 정보 제거
    }
```

### 4.2 AI 콘텐츠 정책 (필터링 및 검열)

콘텐츠 정책은 DreamSeedAI에서 학생에게 제공되는 콘텐츠와 AI 응답이 거버넌스 원칙에 부합하도록 실시간으로 필터링하고 검열하는 규칙들을 포함합니다.

#### 4.2.1 목표

*   **안전한 학습 환경**: 학생들을 유해하거나 부적절한 콘텐츠로부터 보호
*   **윤리적 가치 준수**: AI 응답이 공정성, 객관성, 존중의 가치를 반영하도록 보장
*   **학습 목표 부합**: 콘텐츠가 교육 과정 및 학습 목표에 부합하도록 관리

#### 4.2.2 필터링 및 검열 대상

*   **AI 튜터 응답**: AI 튜터가 생성하는 모든 텍스트, 이미지, 오디오, 비디오 콘텐츠
*   **문항 은행 콘텐츠**: 시험 문제, 연습 문제, 설명 자료 및 관련 이미지/비디오
*   **사용자 생성 콘텐츠**: 학생 및 교사가 업로드하거나 생성하는 콘텐츠 (포럼 게시글, 과제 제출물)

#### 4.2.3 주요 정책 규칙

**유해 콘텐츠 금지**:
*   폭력, 혐오, 차별, 성적 내용, 약물 사용, 자살, 자해 등 유해하거나 불법적인 콘텐츠 금지
*   정치적 또는 종교적 편향을 드러내는 콘텐츠 금지
*   타인의 개인 정보 또는 명예를 침해하는 콘텐츠 금지

**부적절한 언어 사용 금지**:
*   욕설, 비속어, 은어, 차별적 표현 등 부적절한 언어 사용 금지
*   공격적이거나 위협적인 언어 사용 금지

**연령 부적절 콘텐츠 제한**:
*   특정 연령대에 부적합한 주제 (예: 성, 폭력, 흡연)에 대한 콘텐츠 제한
*   만 13세 미만 학생 대상 데이터 수집 시 COPPA 준수

**학습 내용 관련성**:
*   콘텐츠가 교육 과정 및 학습 목표와 관련성이 있어야 함
*   허위 정보 또는 오해를 유발할 수 있는 콘텐츠 금지

#### 4.2.4 Rego 정책 구현

**기본 콘텐츠 안전성 정책**:
```rego
package ai_content_safety

default allow = false

# AI 생성 콘텐츠는 필터링 통과 필수
allow {
    input.content_type == "ai_generated"
    input.safety_check.passed == true
    input.safety_check.score >= 0.8
}

# 유해 콘텐츠 차단
deny[msg] {
    input.content_type == "ai_generated"
    input.safety_check.passed != true
    msg := sprintf("Content blocked: safety score %v", [input.safety_check.score])
}

# 연령별 콘텐츠 제한
deny[msg] {
    input.user.age < 13
    input.content.contains_sensitive_topics == true
    msg := "Age-inappropriate content blocked for user under 13"
}
```

**유해 언어 필터링 정책**:
```rego
package content_language_filter

import future.keywords.contains
import future.keywords.if

default allow = false

# 금지 단어 목록 (실제 구현에서는 외부 데이터로 관리)
prohibited_words := [
    "욕설1", "비속어1", "차별어1", "폭력어1"
]

# 텍스트에 금지 단어 포함 여부 확인
contains_prohibited_language(text) if {
    some word in prohibited_words
    contains(lower(text), word)
}

# 금지 언어 없으면 허용
allow {
    not contains_prohibited_language(input.content.text)
}

# 금지 언어 발견 시 차단
deny[msg] {
    contains_prohibited_language(input.content.text)
    msg := "Content contains prohibited language"
}
```

**사용자 입력 검열 정책**:
```rego
package user_input_moderation

import future.keywords.if

default allow = false

# 개인정보 패턴 감지
contains_personal_info(text) if {
    # 전화번호 패턴 (한국)
    regex.match(`\d{3}-\d{4}-\d{4}`, text)
}

contains_personal_info(text) if {
    # 이메일 패턴
    regex.match(`[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`, text)
}

contains_personal_info(text) if {
    # 주민등록번호 패턴
    regex.match(`\d{6}-\d{7}`, text)
}

# 개인정보 없으면 허용
allow {
    not contains_personal_info(input.user_input)
}

# 개인정보 포함 시 차단
deny[msg] {
    contains_personal_info(input.user_input)
    msg := "User input contains personal information"
}
```

#### 4.2.5 구현 메커니즘

**1. 사전 학습 필터 (Pre-training Filters)**

AI 모델 학습 시, 유해하거나 편향된 데이터는 제외하고 학습합니다.

```python
# ai/training/data_filter.py
class TrainingDataFilter:
    def __init__(self, safety_threshold: float = 0.8):
        self.safety_threshold = safety_threshold
        self.safety_model = load_safety_classifier()
    
    def filter_training_data(self, dataset: List[dict]) -> List[dict]:
        """학습 데이터에서 유해 콘텐츠 제거"""
        filtered_data = []
        
        for item in dataset:
            # 안전성 점수 계산
            safety_score = self.safety_model.predict(item["content"])
            
            # 정책 평가
            policy_result = evaluate_policy("training_data_safety", {
                "content": item["content"],
                "safety_score": safety_score
            })
            
            if policy_result["allow"]:
                filtered_data.append(item)
            else:
                logger.warning(
                    f"Training data filtered: {policy_result['deny']}"
                )
        
        return filtered_data
    
    def fine_tune_with_ethical_data(self, model, ethical_dataset):
        """윤리적 데이터로 모델 미세 조정"""
        # 윤리적 가치를 반영한 데이터셋으로 fine-tuning
        filtered_data = self.filter_training_data(ethical_dataset)
        model.train(filtered_data)
        return model
```

**2. 실시간 필터 (Real-time Filters)**

AI가 생성하는 콘텐츠를 실시간으로 분석하고, 유해하거나 부적절한 내용을 탐지합니다.

```python
# ai/safety/realtime_filter.py
from transformers import pipeline
import re

class RealtimeContentFilter:
    def __init__(self):
        # NLP 기반 안전성 분류기
        self.text_classifier = pipeline(
            "text-classification",
            model="unitary/toxic-bert"
        )
        
        # 이미지 안전성 분류기
        self.image_classifier = pipeline(
            "image-classification",
            model="Falconsai/nsfw_image_detection"
        )
        
        # 금지 단어 목록 (정규 표현식)
        self.prohibited_patterns = [
            r'\b욕설\d+\b',
            r'\b비속어\d+\b',
            # ... 추가 패턴
        ]
    
    async def check_text_safety(self, text: str) -> dict:
        """텍스트 안전성 검사"""
        # 1. NLP 모델 검사
        result = self.text_classifier(text)[0]
        
        # 2. 패턴 매칭 검사
        has_prohibited = any(
            re.search(pattern, text) 
            for pattern in self.prohibited_patterns
        )
        
        return {
            "passed": result["label"] == "SAFE" and not has_prohibited,
            "score": result["score"] if result["label"] == "SAFE" else 0.0,
            "toxic_type": result["label"] if result["label"] != "SAFE" else None,
            "prohibited_pattern_found": has_prohibited
        }
    
    async def check_image_safety(self, image_url: str) -> dict:
        """이미지 안전성 검사"""
        result = self.image_classifier(image_url)[0]
        
        return {
            "passed": result["label"] == "normal",
            "score": result["score"] if result["label"] == "normal" else 0.0,
            "nsfw_type": result["label"] if result["label"] != "normal" else None
        }
    
    async def check_video_safety(self, video_url: str) -> dict:
        """비디오 안전성 검사 (프레임별 이미지 분석)"""
        # 비디오를 프레임으로 분할하여 각 프레임 검사
        frames = extract_frames(video_url, interval=1.0)  # 1초마다
        
        results = []
        for frame in frames:
            frame_result = await self.check_image_safety(frame)
            results.append(frame_result)
        
        # 모든 프레임이 안전해야 통과
        all_passed = all(r["passed"] for r in results)
        avg_score = sum(r["score"] for r in results) / len(results)
        
        return {
            "passed": all_passed,
            "score": avg_score,
            "total_frames": len(frames),
            "unsafe_frames": [i for i, r in enumerate(results) if not r["passed"]]
        }
```

**3. 콘텐츠 수정 및 차단**

정책 엔진은 유해 콘텐츠 탐지 시, 콘텐츠를 자동으로 수정하거나 차단합니다.

```python
# ai/content/moderator.py
async def generate_ai_content(prompt: str, user_id: str, user_age: int) -> str:
    """AI 콘텐츠 생성 및 필터링"""
    # 1. AI 콘텐츠 생성
    content = await ai_model.generate(prompt)
    
    # 2. 안전성 검사
    safety_filter = RealtimeContentFilter()
    safety_result = await safety_filter.check_text_safety(content)
    
    # 3. 정책 평가
    policy_result = await evaluate_policy("ai_content_safety", {
        "content_type": "ai_generated",
        "safety_check": safety_result,
        "user_id": user_id,
        "user": {"age": user_age},
        "content": {"contains_sensitive_topics": check_sensitive_topics(content)}
    })
    
    if not policy_result["allow"]:
        # Slack 알림
        await slack_notify(
            channel="#ai-safety-alerts",
            message=f"⚠️ AI content blocked for user {user_id}: {policy_result['deny']}"
        )
        
        # 관리자 검토 대기열에 추가
        await add_to_review_queue({
            "content": content,
            "user_id": user_id,
            "reason": policy_result["deny"],
            "timestamp": datetime.now()
        })
        
        # 사용자에게 안전한 대체 메시지 반환
        return "죄송합니다. 해당 내용은 안전성 검토가 필요합니다. 다른 질문을 해주세요."
    
    return content

async def moderate_user_content(content: str, content_type: str, user_id: str) -> dict:
    """사용자 생성 콘텐츠 검열"""
    safety_filter = RealtimeContentFilter()
    
    # 콘텐츠 타입별 검사
    if content_type == "text":
        safety_result = await safety_filter.check_text_safety(content)
    elif content_type == "image":
        safety_result = await safety_filter.check_image_safety(content)
    elif content_type == "video":
        safety_result = await safety_filter.check_video_safety(content)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")
    
    # 정책 평가
    policy_result = await evaluate_policy("user_content_moderation", {
        "content_type": content_type,
        "safety_check": safety_result,
        "user_id": user_id
    })
    
    return {
        "allowed": policy_result["allow"],
        "reason": policy_result.get("deny", [None])[0],
        "requires_review": not policy_result["allow"]
    }
```

**4. 사용자 신고 시스템**

학생, 교사, 학부모는 부적절한 콘텐츠를 신고할 수 있습니다.

```python
# api/routes/content_report.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

class ContentReport(BaseModel):
    content_id: str
    content_type: str  # "ai_response", "forum_post", "assignment", etc.
    reason: str
    description: str

@router.post("/api/content/report")
async def report_content(
    report: ContentReport,
    current_user: User = Depends(get_current_user)
):
    """부적절한 콘텐츠 신고"""
    # 1. 신고 내용 저장
    report_id = await db.content_reports.insert_one({
        "content_id": report.content_id,
        "content_type": report.content_type,
        "reported_by": current_user.id,
        "reason": report.reason,
        "description": report.description,
        "status": "pending",
        "created_at": datetime.now()
    })
    
    # 2. 콘텐츠 임시 숨김 처리
    await db.contents.update_one(
        {"id": report.content_id},
        {"$set": {"hidden": True, "hidden_reason": "user_report"}}
    )
    
    # 3. 관리자 알림
    await slack_notify(
        channel="#content-moderation",
        message=f"🚨 New content report: {report.content_type} - {report.reason}\n"
                f"Reporter: {current_user.name} ({current_user.role})\n"
                f"Review: /admin/reports/{report_id}"
    )
    
    # 4. 메트릭 기록
    CONTENT_REPORTS.labels(
        content_type=report.content_type,
        reason=report.reason
    ).inc()
    
    return {
        "success": True,
        "report_id": str(report_id),
        "message": "신고가 접수되었습니다. 관리자가 검토 후 조치할 예정입니다."
    }

@router.get("/api/admin/reports")
async def get_pending_reports(
    admin_user: User = Depends(require_admin)
):
    """관리자용 신고 목록 조회"""
    reports = await db.content_reports.find(
        {"status": "pending"}
    ).sort("created_at", -1).to_list(100)
    
    return reports

@router.post("/api/admin/reports/{report_id}/resolve")
async def resolve_report(
    report_id: str,
    action: str,  # "remove", "restore", "warn_user"
    admin_user: User = Depends(require_admin)
):
    """신고 처리"""
    report = await db.content_reports.find_one({"_id": ObjectId(report_id)})
    
    if action == "remove":
        # 콘텐츠 영구 삭제
        await db.contents.delete_one({"id": report["content_id"]})
    elif action == "restore":
        # 콘텐츠 복원
        await db.contents.update_one(
            {"id": report["content_id"]},
            {"$set": {"hidden": False}}
        )
    elif action == "warn_user":
        # 콘텐츠 작성자에게 경고
        content = await db.contents.find_one({"id": report["content_id"]})
        await send_warning(content["user_id"], report["reason"])
    
    # 신고 상태 업데이트
    await db.content_reports.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": {
            "status": "resolved",
            "action": action,
            "resolved_by": admin_user.id,
            "resolved_at": datetime.now()
        }}
    )
    
    return {"success": True}
```

#### 4.2.6 사용자 입력 검열

학생 입력에 금지된 내용 (예: 욕설, 개인정보)이 있으면 경고 또는 블록합니다.

```python
# api/middleware/input_filter.py
from fastapi import Request, HTTPException
import re

class UserInputFilterMiddleware:
    async def __call__(self, request: Request, call_next):
        # POST/PUT 요청의 body 검사
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body_str = body.decode('utf-8')
            
            # 정책 평가
            policy_result = await evaluate_policy("user_input_moderation", {
                "user_input": body_str
            })
            
            if not policy_result["allow"]:
                # 위반 메트릭 기록
                USER_INPUT_VIOLATIONS.labels(
                    reason=policy_result["deny"][0]
                ).inc()
                
                # 경고 반환
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Input validation failed",
                        "reason": policy_result["deny"][0],
                        "message": "입력 내용에 부적절한 정보가 포함되어 있습니다."
                    }
                )
        
        response = await call_next(request)
        return response

# 애플리케이션에 미들웨어 추가
app.middleware("http")(UserInputFilterMiddleware())
```

**반복 위반 처리**:
```python
# api/services/violation_tracker.py
class ViolationTracker:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def record_violation(self, user_id: str, violation_type: str):
        """위반 기록"""
        key = f"violations:{user_id}:{violation_type}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, 86400)  # 24시간 TTL
        
        # 위반 횟수에 따른 조치
        if count >= 3:
            await self.suspend_user(user_id, duration=3600)  # 1시간 정지
            await slack_notify(
                channel="#security-alerts",
                message=f"⚠️ User {user_id} suspended: 3+ {violation_type} violations"
            )
        elif count >= 5:
            await self.ban_user(user_id)  # 영구 차단
            await slack_notify(
                channel="#security-alerts",
                message=f"🚫 User {user_id} banned: 5+ {violation_type} violations"
            )
        
        return count
    
    async def suspend_user(self, user_id: str, duration: int):
        """사용자 일시 정지"""
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "suspended": True,
                "suspended_until": datetime.now() + timedelta(seconds=duration),
                "suspended_reason": "repeated_violations"
            }}
        )
    
    async def ban_user(self, user_id: str):
        """사용자 영구 차단"""
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "banned": True,
                "banned_at": datetime.now(),
                "banned_reason": "severe_repeated_violations"
            }}
        )
```

#### 4.2.7 모니터링 및 감사

**로그 기록**:
```python
# 모든 콘텐츠 필터링 활동 상세 기록
logger.info(
    "Content safety check",
    extra={
        "content_type": content_type,
        "user_id": user_id,
        "safety_score": safety_result["score"],
        "passed": safety_result["passed"],
        "decision": "allow" if policy_result["allow"] else "deny",
        "toxic_type": safety_result.get("toxic_type"),
        "timestamp": datetime.now().isoformat()
    }
)
```

**Prometheus 메트릭**:
```python
# governance/backend/metrics.py
CONTENT_SAFETY_CHECKS = Counter(
    'content_safety_checks_total',
    'Total content safety checks',
    ['content_type', 'decision']
)

CONTENT_SAFETY_SCORE = Histogram(
    'content_safety_score',
    'Content safety scores',
    ['content_type'],
    buckets=[0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
)

CONTENT_REPORTS = Counter(
    'content_reports_total',
    'Total content reports',
    ['content_type', 'reason']
)

USER_INPUT_VIOLATIONS = Counter(
    'user_input_violations_total',
    'Total user input violations',
    ['reason']
)
```

**정기적인 감사**:
```python
# scripts/audit_content_policies.py
async def audit_content_policies():
    """콘텐츠 정책 효과성 감사"""
    # 1. 최근 30일간 차단된 콘텐츠 분석
    blocked_contents = await db.audit_logs.find({
        "event": "content_blocked",
        "timestamp": {"$gte": datetime.now() - timedelta(days=30)}
    }).to_list(None)
    
    # 2. 차단 사유 통계
    block_reasons = {}
    for log in blocked_contents:
        reason = log["reason"]
        block_reasons[reason] = block_reasons.get(reason, 0) + 1
    
    # 3. 오탐지율 계산 (복원된 콘텐츠 비율)
    restored = await db.contents.count_documents({
        "hidden": False,
        "hidden_reason": "user_report",
        "restored_at": {"$gte": datetime.now() - timedelta(days=30)}
    })
    
    false_positive_rate = restored / len(blocked_contents) if blocked_contents else 0
    
    # 4. 보고서 생성
    report = {
        "period": "last_30_days",
        "total_blocked": len(blocked_contents),
        "block_reasons": block_reasons,
        "false_positive_rate": false_positive_rate,
        "recommendations": []
    }
    
    # 5. 개선 권장사항
    if false_positive_rate > 0.1:
        report["recommendations"].append(
            "High false positive rate detected. Review filtering thresholds."
        )
    
    return report
```

DreamSeedAI는 위와 같은 포괄적인 콘텐츠 정책을 통해 학생들에게 안전하고 윤리적인 학습 환경을 제공합니다.

### 4.3 접근 제어 정책 (Access Control Policies)

접근 제어 정책은 DreamSeedAI에서 누가 어떤 데이터와 기능에 접근할 수 있는지 정의한 핵심 규칙입니다.

#### 4.3.1 기본 원칙

*   **최소 권한 원칙 (Principle of Least Privilege)**: 사용자에게 필요한 최소한의 권한만 부여합니다.
*   **역할 기반 접근 제어 (Role-Based Access Control, RBAC)**: 사용자에게 역할을 부여하고, 역할에 따라 권한을 제어합니다.
*   **명시적 거부 (Explicit Deny)**: 특정 사용자에 대한 접근을 명시적으로 거부하는 규칙을 설정합니다.
*   **직무 분리 (Separation of Duties)**: 민감한 작업은 여러 역할로 분리하여 단일 사용자가 전체 프로세스를 제어할 수 없도록 합니다.

#### 4.3.2 역할별 접근 권한

**학생 (Student)**:
*   자신의 학습 데이터만 열람 가능
*   자신의 학습 활동 기록 조회
*   자신의 성적 및 진도 확인
*   할당된 학습 콘텐츠 접근

**교사 (Teacher)**:
*   자신이 담당하는 학급의 학생 데이터 열람
*   담당 학급 성적 데이터 조회 및 분석
*   학습 콘텐츠 관리 (생성, 수정, 삭제)
*   학생 학습 활동 모니터링

**학부모 (Parent)**:
*   자녀의 학습 데이터 열람
*   자녀의 성적 및 진도 확인
*   교사와의 커뮤니케이션 기록 조회

**관리자 (Administrator)**:
*   시스템의 모든 데이터 접근
*   모든 기능 사용 권한
*   사용자 관리 (생성, 수정, 삭제)
*   시스템 설정 변경

#### 4.3.3 규칙 예시: 교사의 학급별 접근 제어

**규칙**: 교사는 자신이 담당하는 학급의 학생 데이터에만 접근할 수 있다.

**Rego 정책**:
```rego
package student_data_access

default allow = false

# 학생은 자신의 데이터만 접근 가능
allow {
    input.user.role == "student"
    input.student.id == input.user.id
}

# 교사는 담당 학급 학생만 접근 가능
allow {
    input.user.role == "teacher"
    input.student.class_id == input.user.class_id
}

# 학부모는 자녀 데이터만 접근 가능
allow {
    input.user.role == "parent"
    input.student.id in input.user.children_ids
}

# 관리자는 모든 학생 데이터 접근 가능
allow {
    input.user.role == "admin"
}

# 접근 거부 사유 (학생)
deny[msg] {
    input.user.role == "student"
    input.student.id != input.user.id
    msg := "Students can only access their own data"
}

# 접근 거부 사유 (교사)
deny[msg] {
    input.user.role == "teacher"
    input.student.class_id != input.user.class_id
    msg := sprintf("Teacher can only access students in class %s", [input.user.class_id])
}

# 접근 거부 사유 (학부모)
deny[msg] {
    input.user.role == "parent"
    not (input.student.id in input.user.children_ids)
    msg := "Parents can only access their children's data"
}
```

**액션**:
*   교사의 데이터 접근 요청 시, 학급 ID를 검사하여 접근 권한 확인
*   거부 시 HTTP 403 응답
*   감사 로그: 접근 시도 기록

**구현**:
```python
@app.get("/api/students/{student_id}/data")
async def get_student_data(
    student_id: int,
    current_user: User = Depends(get_current_user)
):
    # 학생 정보 조회
    student = await db.get_student(student_id)
    
    # 정책 평가
    policy_result = await evaluate_policy("student_data_access", {
        "user": {
            "id": current_user.id,
            "role": current_user.role,
            "class_id": current_user.class_id,
            "children_ids": current_user.children_ids
        },
        "student": {
            "id": student.id,
            "class_id": student.class_id
        }
    })
    
    if not policy_result["allow"]:
        raise HTTPException(status_code=403, detail=policy_result["deny"])
    
    return student.data
```

#### 4.3.4 정책 시행 메커니즘 (Policy Enforcement Mechanisms)

정책은 다층 방어(Defense in Depth) 전략으로 여러 계층에서 시행됩니다.

##### 1️⃣ API Gateway 수준

**역할**: 모든 API 호출의 진입점에서 인증 및 권한 검사

**구현**:
```python
# governance/backend/policy_middleware.py
@app.middleware("http")
async def policy_enforcement_middleware(request: Request, call_next):
    # 1. 사용자 인증 확인
    user = await authenticate_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized"}
        )
    
    # 2. 요청 경로에 해당하는 정책 검색
    policy_name = get_policy_for_route(request.url.path)
    
    # 3. 정책 평가
    if policy_name:
        policy_result = await evaluate_policy(policy_name, {
            "user": user.dict(),
            "request": {
                "method": request.method,
                "path": request.url.path,
                "query": dict(request.query_params)
            }
        })
        
        # 4. 접근 거부
        if not policy_result["allow"]:
            GOVERNANCE_DENY.labels(
                policy=policy_name,
                reason=policy_result.get("deny", ["unknown"])[0]
            ).inc()
            
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Access denied",
                    "reason": policy_result["deny"]
                }
            )
    
    # 5. 요청 계속 진행
    response = await call_next(request)
    return response
```

**특징**:
*   모든 API 요청에 대한 중앙 집중식 정책 평가
*   권한이 없는 요청은 애플리케이션 로직 실행 전에 차단
*   Prometheus 메트릭으로 정책 거부 추적

##### 2️⃣ UI 제어 수준

**역할**: 사용자 인터페이스에서 권한이 없는 기능 숨김/비활성화

**구현 (React 예시)**:
```typescript
// frontend/components/StudentDataView.tsx
import { usePermission } from '@/hooks/usePermission';

function StudentDataView({ studentId }: Props) {
  const { hasPermission, loading } = usePermission('student_data_access', {
    user: currentUser,
    student: { id: studentId }
  });
  
  if (loading) return <Spinner />;
  
  // 권한이 없으면 컴포넌트 자체를 렌더링하지 않음
  if (!hasPermission) {
    return <AccessDenied message="You don't have permission to view this student's data" />;
  }
  
  return (
    <div>
      {/* 학생 데이터 표시 */}
      <StudentProfile studentId={studentId} />
      <StudentGrades studentId={studentId} />
    </div>
  );
}

// 조건부 버튼 렌더링
function AdminPanel() {
  const { hasRole } = useAuth();
  
  return (
    <div>
      {hasRole('admin') && (
        <Button onClick={handleDeleteUser}>Delete User</Button>
      )}
      {hasRole(['admin', 'teacher']) && (
        <Button onClick={handleExportData}>Export Data</Button>
      )}
    </div>
  );
}
```

**특징**:
*   사용자 경험 향상 (권한 없는 기능은 보이지 않음)
*   보안 강화 (클라이언트 측 추가 검증)
*   주의: UI 제어만으로는 충분하지 않으며, 서버 측 검증 필수

##### 3️⃣ 데이터베이스 접근 제어 수준

**역할**: 데이터베이스 쿼리 시 역할과 조직 ID 기반 데이터 필터링

**구현 (SQLAlchemy 예시)**:
```python
# models/student.py
from sqlalchemy import select
from sqlalchemy.orm import Session

class StudentRepository:
    def get_students_by_permission(
        self,
        db: Session,
        current_user: User
    ) -> list[Student]:
        """사용자 권한에 따라 접근 가능한 학생 목록 반환"""
        query = select(Student)
        
        # 학생: 자신만
        if current_user.role == "student":
            query = query.where(Student.id == current_user.id)
        
        # 교사: 담당 학급만
        elif current_user.role == "teacher":
            query = query.where(Student.class_id == current_user.class_id)
        
        # 학부모: 자녀만
        elif current_user.role == "parent":
            query = query.where(Student.id.in_(current_user.children_ids))
        
        # 관리자: 모두
        elif current_user.role == "admin":
            pass  # 필터링 없음
        
        else:
            # 알 수 없는 역할: 빈 결과 반환
            query = query.where(Student.id == -1)
        
        return db.execute(query).scalars().all()
```

**Row-Level Security (PostgreSQL)**:
```sql
-- Row-Level Security 활성화
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- 학생은 자신의 데이터만 조회
CREATE POLICY student_own_data ON students
    FOR SELECT
    TO student_role
    USING (id = current_user_id());

-- 교사는 담당 학급만 조회
CREATE POLICY teacher_class_data ON students
    FOR SELECT
    TO teacher_role
    USING (class_id = current_user_class_id());

-- 관리자는 모두 조회
CREATE POLICY admin_all_data ON students
    FOR ALL
    TO admin_role
    USING (true);
```

**특징**:
*   데이터베이스 레벨에서 추가 보안 계층
*   애플리케이션 버그로 인한 데이터 유출 방지
*   PostgreSQL RLS, MySQL 뷰, MongoDB Document-Level Security 활용

##### 4️⃣ 코드 기반 검사 수준

**역할**: 핵심 비즈니스 로직에서 명시적 권한 확인

**구현**:
```python
# services/grade_service.py
class GradeService:
    async def update_grade(
        self,
        student_id: int,
        grade_data: dict,
        current_user: User
    ) -> Grade:
        """성적 업데이트 (명시적 권한 검사)"""
        
        # 1. 학생 정보 조회
        student = await self.student_repo.get(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # 2. 권한 검사 (명시적)
        if current_user.role == "teacher":
            # 교사는 담당 학급만
            if student.class_id != current_user.class_id:
                raise HTTPException(
                    status_code=403,
                    detail=f"Teacher can only update grades for class {current_user.class_id}"
                )
        elif current_user.role == "admin":
            # 관리자는 모두 허용
            pass
        else:
            # 기타 역할은 거부
            raise HTTPException(
                status_code=403,
                detail=f"Role {current_user.role} cannot update grades"
            )
        
        # 3. 정책 평가 (OPA 이중 검증)
        policy_result = await evaluate_policy("grade_update", {
            "user": current_user.dict(),
            "student": student.dict(),
            "grade_data": grade_data
        })
        
        if not policy_result["allow"]:
            raise HTTPException(
                status_code=403,
                detail=policy_result["deny"]
            )
        
        # 4. 성적 업데이트 실행
        grade = await self.grade_repo.update(student_id, grade_data)
        
        # 5. 감사 로그
        await self.audit_log.create({
            "action": "grade_update",
            "user_id": current_user.id,
            "student_id": student_id,
            "timestamp": datetime.utcnow()
        })
        
        return grade
```

**특징**:
*   비즈니스 로직 수준에서 최종 권한 검사
*   OPA 정책과 코드 검사 이중 검증
*   명시적 예외 처리로 보안 강화

##### 5️⃣ 감사 로깅

**역할**: 모든 정책 시행 활동 기록 및 추적

**구현**:
```python
# services/audit_service.py
class AuditService:
    async def log_access_attempt(
        self,
        user_id: str,
        resource: str,
        action: str,
        allowed: bool,
        reason: Optional[str] = None
    ):
        """접근 시도 감사 로그 기록"""
        await self.db.audit_logs.insert_one({
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "allowed": allowed,
            "reason": reason,
            "ip_address": get_client_ip(),
            "user_agent": get_user_agent()
        })
        
        # Prometheus 메트릭
        AUDIT_LOG.labels(
            action=action,
            resource=resource,
            result="allowed" if allowed else "denied"
        ).inc()
```

**감사 로그 조회**:
```python
# 특정 사용자의 접근 거부 이력 조회
denied_accesses = await audit_service.query({
    "user_id": "user123",
    "allowed": False,
    "timestamp": {"$gte": datetime.utcnow() - timedelta(days=7)}
})

# 민감한 데이터 접근 이력 조회
sensitive_accesses = await audit_service.query({
    "resource": {"$in": ["student_data", "grade_data"]},
    "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=1)}
})
```

#### 4.3.5 다층 방어 전략 요약

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: API Gateway (정책 미들웨어)                         │
│  → 모든 요청 진입점에서 정책 평가                              │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: UI 제어                                            │
│  → 권한 없는 기능 숨김/비활성화                               │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: 데이터베이스 접근 제어                               │
│  → Row-Level Security, 쿼리 필터링                           │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: 코드 기반 검사                                      │
│  → 비즈니스 로직에서 명시적 권한 확인                          │
├─────────────────────────────────────────────────────────────┤
│ Layer 5: 감사 로깅                                           │
│  → 모든 접근 시도 기록 및 추적                                │
└─────────────────────────────────────────────────────────────┘
```

**이점**:
*   **심층 방어**: 한 계층이 뚫려도 다른 계층에서 차단
*   **조기 차단**: API Gateway에서 대부분의 불법 요청 차단
*   **감사 가능성**: 모든 접근 시도 추적
*   **보안 강화**: 여러 검증 단계로 보안 취약점 최소화

### 4.4 학습 알고리즘 정책

**규칙**: 새로운 AI 모델은 성능 평가를 통과한 후에만 프로덕션에 배포할 수 있다.

**Rego 정책**:
```rego
package ai_model_deployment

default allow = false

# AI 모델 배포 기준
allow {
    input.model.evaluation.accuracy >= 0.85
    input.model.evaluation.fairness_score >= 0.9
    input.model.evaluation.samples >= 10000
    input.model.approval_status == "approved"
}

# 배포 거부 사유
deny[msg] {
    input.model.evaluation.accuracy < 0.85
    msg := sprintf("Model accuracy %v below threshold 0.85", [input.model.evaluation.accuracy])
}

deny[msg] {
    input.model.evaluation.fairness_score < 0.9
    msg := sprintf("Model fairness score %v below threshold 0.9", [input.model.evaluation.fairness_score])
}

deny[msg] {
    input.model.approval_status != "approved"
    msg := "Model requires approval before deployment"
}
```

**액션**:
*   성능 평가 통과 시: 프로덕션 배포
*   성능 미달 시: 배포 중단, 개발팀 알림
*   승인 대기 중: 승인 요청 알림

**구현**:
```python
async def deploy_ai_model(model_id: str, evaluation_results: dict):
    # 정책 평가
    policy_result = await evaluate_policy("ai_model_deployment", {
        "model": {
            "id": model_id,
            "evaluation": evaluation_results,
            "approval_status": await get_approval_status(model_id)
        }
    })
    
    if not policy_result["allow"]:
        # Slack 알림
        await slack_notify(
            channel="#ml-ops",
            message=f"🚫 Model {model_id} deployment blocked: {policy_result['deny']}"
        )
        raise ValueError(f"Model deployment blocked: {policy_result['deny']}")
    
    # 배포 진행
    await kubernetes.deploy_model(model_id, environment="production")
    
    # 성공 알림
    await slack_notify(
        channel="#ml-ops",
        message=f"✅ Model {model_id} deployed to production"
    )
```

### 4.5 AI 행동 정책 (AI Behavior Policies)

AI 행동 정책은 DreamSeedAI에서 AI 모델의 행동 영역과 한계를 명확히 정의하는 규칙들을 포함합니다. 이 정책은 AI가 교육적 목적에 부합하고, 윤리적 및 법적 기준을 준수하며, 사용자에게 안전하고 신뢰할 수 있는 서비스를 제공하도록 보장하는 데 핵심적인 역할을 합니다.

#### 4.5.1 목표

*   **윤리적 AI 사용**: AI 모델이 DreamSeedAI의 핵심 가치와 윤리 원칙을 준수하도록 합니다.
*   **안전한 사용자 경험**: AI 모델이 유해하거나 부적절한 콘텐츠를 생성하지 않도록 합니다.
*   **학습 목표 집중**: AI 모델이 학습 활동과 관련된 질문에만 응답하고, 학생들의 학습에 집중하도록 지원합니다.
*   **전문 분야 존중**: AI 모델이 전문적인 지식 (의학, 법률 등)을 제공하는 것을 제한하고, 전문가의 도움을 받도록 안내합니다.

#### 4.5.2 주요 정책 규칙

**학습 목적 외 대화 금지**:
*   AI 튜터는 학습 내용과 직접 관련되지 않은 개인적인 대화 (사생활 상담, 연애 상담 등)를 수행하지 않습니다.
*   학생의 감정적인 어려움에 대한 공감은 제공하되, 전문적인 상담이 필요한 경우 전문가의 도움을 받도록 안내합니다.

**전문 분야 답변 제한**:
*   AI 튜터는 의학적 또는 법률적 조언을 제공하지 않습니다.
*   해당 분야의 전문가와 상담하도록 안내합니다.

**시험 상황에서의 힌트 제공 금지**:
*   학생이 시험 응시 중에는 AI 튜터의 힌트 제공 기능을 제한합니다.
*   학생의 자기 평가 및 복습을 돕는 기능은 시험 종료 후에 제공합니다.

**부적절한 요청 처리 금지**:
*   AI는 폭력적이거나 혐오적인 콘텐츠를 생성하는 요청을 거부합니다.
*   AI는 차별적이거나 불쾌감을 주는 언어를 사용하는 요청을 거부합니다.

#### 4.5.3 Rego 정책 구현

**학습 관련 질문 검증 정책**:
```rego
package ai_behavior_educational_focus

import future.keywords.if
import future.keywords.contains

default allow = false

# 허용되는 주제 카테고리
educational_topics := [
    "mathematics", "science", "language", "history",
    "geography", "computer_science", "arts", "music"
]

# 금지된 주제 카테고리
forbidden_topics := [
    "personal_counseling", "romantic_advice", "medical_advice",
    "legal_advice", "financial_advice", "political_opinion"
]

# 질문 분류 (실제로는 ML 모델 사용)
classify_question(question) := category {
    # 간단한 키워드 매칭 (실제로는 NLP 모델)
    category := "mathematics"  # 예시
}

# 교육 관련 질문 허용
allow {
    category := classify_question(input.question)
    category in educational_topics
}

# 금지된 주제 차단
deny[msg] {
    category := classify_question(input.question)
    category in forbidden_topics
    msg := sprintf("Question category '%s' is not allowed. AI tutor focuses on educational topics only.", [category])
}

# 전문 분야 안내 메시지
referral_message[msg] {
    category := classify_question(input.question)
    category == "medical_advice"
    msg := "의학적 조언은 전문 의료인과 상담하시기 바랍니다."
}

referral_message[msg] {
    category := classify_question(input.question)
    category == "legal_advice"
    msg := "법률적 조언은 전문 변호사와 상담하시기 바랍니다."
}
```

**시험 중 힌트 제공 제한 정책**:
```rego
package ai_behavior_exam_assistance

import future.keywords.if

default allow = false

# 일반 학습 모드에서는 힌트 허용
allow {
    input.context.mode == "learning"
    input.request.type == "hint"
}

# 시험 모드에서는 힌트 거부
deny[msg] {
    input.context.mode == "exam"
    input.request.type == "hint"
    msg := "Hints are not available during exams. Please complete the exam independently."
}

# 복습 모드에서는 상세 설명 허용
allow {
    input.context.mode == "review"
    input.request.type in ["hint", "solution", "explanation"]
}
```

**부적절한 요청 차단 정책**:
```rego
package ai_behavior_request_validation

import future.keywords.if
import future.keywords.contains

default allow = false

# 폭력/혐오 요청 감지 (간단한 예시)
contains_harmful_intent(request) if {
    harmful_keywords := ["폭력", "차별", "혐오", "괴롭힘"]
    some keyword in harmful_keywords
    contains(lower(request), keyword)
}

# 정상 요청 허용
allow {
    not contains_harmful_intent(input.request)
}

# 유해 요청 차단
deny[msg] {
    contains_harmful_intent(input.request)
    msg := "This request contains inappropriate content and cannot be processed."
}
```

#### 4.5.4 코그니티브 정책 레이어 (Cognitive Policy Layer)

DreamSeedAI의 핵심 기술로, AI 모델이 출력을 생성하기 **전에** 코그니티브 정책 레이어가 해당 논의 주제가 허용되는지 여부를 검토합니다. 이 사전 억제 방식은 단순 출력 결과를 검사해 지우는 사후 필터링보다 훨씬 강력하며, AI 안전성을 획기적으로 향상시킵니다.

**동작 원리**:

```
사용자 요청
    ↓
┌─────────────────────────────────────┐
│ Cognitive Policy Layer              │
│  1. 요청 의도 분석                   │
│  2. 정책 규칙 매칭                   │
│  3. 사전 허용/거부 결정              │
└─────────────────────────────────────┘
    ↓
허용된 경우만 → AI 모델 실행
    ↓
응답 생성 (정책 위반 가능성 ↓↓)
```

**구현 예시**:

```python
# ai/cognitive_policy_layer.py
from typing import Dict, Optional
from enum import Enum

class RequestCategory(Enum):
    EDUCATIONAL = "educational"
    PERSONAL_COUNSELING = "personal_counseling"
    MEDICAL_ADVICE = "medical_advice"
    LEGAL_ADVICE = "legal_advice"
    HARMFUL_INTENT = "harmful_intent"
    EXAM_CHEATING = "exam_cheating"

class PolicyDecision:
    def __init__(self, allowed: bool, reason: str = "", referral: str = ""):
        self.allowed = allowed
        self.reason = reason
        self.referral = referral
    
    def is_allowed(self) -> bool:
        return self.allowed
    
    def get_rejection_message(self) -> str:
        if self.referral:
            return f"{self.reason}\n\n{self.referral}"
        return self.reason

class CognitivePolicyLayer:
    def __init__(self, policy_engine, intent_classifier):
        self.policy_engine = policy_engine
        self.intent_classifier = intent_classifier
    
    async def check(self, user_input: str, context: Dict) -> PolicyDecision:
        """
        AI가 답을 만들기 전 정책 엔진이 요청을 검토하고 처리를 결정합니다.
        
        Args:
            user_input: 사용자의 질문/요청
            context: 컨텍스트 정보 (모드, 사용자 정보 등)
        
        Returns:
            PolicyDecision: 허용 여부 및 거부 사유
        """
        # 1. 요청 의도 분석
        intent = await self.intent_classifier.classify(user_input)
        category = self._map_intent_to_category(intent)
        
        # 2. 정책 규칙 매칭 및 평가
        policy_result = await self.policy_engine.evaluate("ai_behavior", {
            "question": user_input,
            "context": context,
            "request": {"type": intent.request_type},
            "category": category.value
        })
        
        # 3. 사전 허용/거부 결정
        if not policy_result["allow"]:
            # 거부 사유 생성
            reason = policy_result.get("deny", ["Request not allowed"])[0]
            referral = policy_result.get("referral_message", [""])[0]
            
            # 메트릭 기록
            COGNITIVE_POLICY_BLOCKS.labels(
                category=category.value,
                reason=reason
            ).inc()
            
            return PolicyDecision(
                allowed=False,
                reason=reason,
                referral=referral
            )
        
        # 허용된 경우
        COGNITIVE_POLICY_ALLOWS.labels(category=category.value).inc()
        return PolicyDecision(allowed=True)
    
    def _map_intent_to_category(self, intent) -> RequestCategory:
        """의도를 카테고리로 매핑"""
        # ML 모델 결과를 카테고리로 변환
        category_map = {
            "education": RequestCategory.EDUCATIONAL,
            "counseling": RequestCategory.PERSONAL_COUNSELING,
            "medical": RequestCategory.MEDICAL_ADVICE,
            "legal": RequestCategory.LEGAL_ADVICE,
            "harmful": RequestCategory.HARMFUL_INTENT,
            "exam_help": RequestCategory.EXAM_CHEATING
        }
        return category_map.get(intent.category, RequestCategory.EDUCATIONAL)

# 실제 사용 예시
async def generate_response(user_input: str, user_context: Dict, ai_model) -> str:
    """AI 모델을 사용하여 응답을 생성합니다."""
    
    # Cognitive Policy Layer 검사 (AI 실행 전)
    cognitive_layer = CognitivePolicyLayer(
        policy_engine=OPAEngine(),
        intent_classifier=IntentClassifier()
    )
    
    policy_decision = await cognitive_layer.check(user_input, user_context)
    
    if not policy_decision.is_allowed():
        # AI 모델 실행하지 않고 바로 거부 메시지 반환
        logger.warning(
            f"Request blocked by cognitive policy layer",
            extra={
                "user_input": user_input,
                "reason": policy_decision.reason
            }
        )
        return policy_decision.get_rejection_message()
    
    # 정책 통과한 경우에만 AI 모델 실행
    response = await ai_model.generate(user_input, context=user_context)
    
    # 추가 안전성 검사 (이중 검증)
    safety_check = await RealtimeContentFilter().check_text_safety(response)
    if not safety_check["passed"]:
        return "죄송합니다. 안전한 응답을 생성하지 못했습니다. 다른 방식으로 질문해주세요."
    
    return response
```

**실제 시나리오 예시**:

```python
# 시나리오 1: 부적절한 요청 (사전 차단)
user_input = "나쁜 말로 사람 놀리는 문장을 만들어줘"

# Cognitive Policy Layer 동작:
# 1. Intent Classifier → "harmful_intent" 분류
# 2. Policy 평가 → deny: "inappropriate content"
# 3. AI 모델 실행되지 않음 (차단)

response = await generate_response(user_input, context, ai_model)
# 결과: "This request contains inappropriate content and cannot be processed."

# 시나리오 2: 시험 중 힌트 요청 (사전 차단)
user_input = "이 문제 답 알려줘"
context = {"mode": "exam", "student_id": 123}

# Cognitive Policy Layer 동작:
# 1. Intent Classifier → "exam_help" 분류
# 2. Policy 평가 (context.mode == "exam") → deny
# 3. AI 모델 실행되지 않음 (차단)

response = await generate_response(user_input, context, ai_model)
# 결과: "Hints are not available during exams. Please complete the exam independently."

# 시나리오 3: 의학 조언 요청 (사전 차단 + 전문가 안내)
user_input = "두통이 심한데 무슨 약을 먹어야 할까?"

# Cognitive Policy Layer 동작:
# 1. Intent Classifier → "medical_advice" 분류
# 2. Policy 평가 → deny + referral_message
# 3. AI 모델 실행되지 않음 (차단)

response = await generate_response(user_input, context, ai_model)
# 결과: "AI tutor cannot provide medical advice.\n\n의학적 조언은 전문 의료인과 상담하시기 바랍니다."

# 시나리오 4: 정상 교육 질문 (허용)
user_input = "이차방정식 풀이 방법을 알려줘"

# Cognitive Policy Layer 동작:
# 1. Intent Classifier → "educational" 분류
# 2. Policy 평가 → allow
# 3. AI 모델 실행 ✅

response = await generate_response(user_input, context, ai_model)
# 결과: "이차방정식은 ax² + bx + c = 0 형태로 표현되며, 근의 공식을 사용하여 풀 수 있습니다..."
```

#### 4.5.5 구현 메커니즘

DreamSeedAI는 AI 행동 정책을 효과적으로 구현하기 위해 다음과 같은 메커니즘을 사용합니다.

**1. 사전 학습 데이터 정제**

AI 모델 학습에 사용되는 데이터셋에서 부적절하거나 편향된 내용을 제거합니다.

```python
# ai/training/ethical_data_curation.py
class EthicalDataCurator:
    def __init__(self, toxicity_classifier, bias_detector):
        self.toxicity_classifier = toxicity_classifier
        self.bias_detector = bias_detector
    
    async def curate_training_data(self, raw_dataset: List[Dict]) -> List[Dict]:
        """윤리적 기준에 따라 학습 데이터 큐레이션"""
        curated_data = []
        filtered_stats = {
            "toxic": 0,
            "biased": 0,
            "off_topic": 0,
            "total": len(raw_dataset)
        }
        
        for item in raw_dataset:
            # 1. 유해성 검사
            toxicity_score = await self.toxicity_classifier.predict(item["text"])
            if toxicity_score > 0.7:
                filtered_stats["toxic"] += 1
                continue
            
            # 2. 편향성 검사
            bias_result = await self.bias_detector.analyze(item["text"])
            if bias_result["has_bias"]:
                filtered_stats["biased"] += 1
                continue
            
            # 3. 교육 관련성 검사
            if not self._is_educational_content(item):
                filtered_stats["off_topic"] += 1
                continue
            
            # 통과한 데이터만 포함
            curated_data.append(item)
        
        # 통계 로깅
        logger.info(
            f"Data curation complete",
            extra={
                "original_size": filtered_stats["total"],
                "curated_size": len(curated_data),
                "filtered_toxic": filtered_stats["toxic"],
                "filtered_biased": filtered_stats["biased"],
                "filtered_off_topic": filtered_stats["off_topic"]
            }
        )
        
        return curated_data
    
    def _is_educational_content(self, item: Dict) -> bool:
        """교육 콘텐츠 여부 확인"""
        educational_keywords = [
            "학습", "교육", "수학", "과학", "역사", "언어",
            "문제 풀이", "설명", "개념", "원리"
        ]
        return any(kw in item["text"] for kw in educational_keywords)
```

**2. 실시간 필터링 (이중 검증)**

Cognitive Policy Layer 통과 후에도 추가 안전성 검사를 수행합니다.

```python
# ai/safety/dual_verification.py
class DualVerificationFilter:
    """이중 검증 필터 (Cognitive Policy + Output Filter)"""
    
    async def verify_response(
        self, 
        user_input: str, 
        ai_response: str,
        context: Dict
    ) -> Dict[str, any]:
        """
        1차: Cognitive Policy Layer (입력 검증)
        2차: Output Filter (출력 검증)
        """
        # 1차 검증은 이미 완료된 상태 (Cognitive Policy Layer)
        
        # 2차 검증: AI 응답 출력 검사
        safety_filter = RealtimeContentFilter()
        output_check = await safety_filter.check_text_safety(ai_response)
        
        # 교육 적합성 검사
        educational_check = self._check_educational_alignment(ai_response, context)
        
        # 최종 판정
        passed = output_check["passed"] and educational_check["passed"]
        
        return {
            "passed": passed,
            "output_safety": output_check,
            "educational_alignment": educational_check,
            "confidence": min(output_check["score"], educational_check["score"])
        }
    
    def _check_educational_alignment(self, response: str, context: Dict) -> Dict:
        """응답이 교육 목표에 부합하는지 확인"""
        # 응답 길이 적절성
        if len(response) > 2000:
            return {"passed": False, "reason": "Response too long", "score": 0.5}
        
        # 학습 모드별 적합성
        if context.get("mode") == "exam" and "정답은" in response:
            return {"passed": False, "reason": "Direct answer in exam mode", "score": 0.0}
        
        return {"passed": True, "score": 1.0}
```

**3. 강화 학습 (RLHF - Reinforcement Learning from Human Feedback)**

인간 피드백을 사용하여 AI 모델을 지속적으로 훈련하고 윤리적인 응답을 생성하도록 유도합니다.

```python
# ai/training/rlhf_trainer.py
class RLHFTrainer:
    """인간 피드백 기반 강화 학습"""
    
    def __init__(self, base_model, reward_model):
        self.base_model = base_model
        self.reward_model = reward_model
    
    async def collect_human_feedback(
        self, 
        interactions: List[Dict]
    ) -> List[Dict]:
        """교사 및 전문가 피드백 수집"""
        feedback_data = []
        
        for interaction in interactions:
            # UI를 통해 전문가에게 평가 요청
            rating = await self._request_expert_rating(
                question=interaction["question"],
                response=interaction["response"]
            )
            
            feedback_data.append({
                "question": interaction["question"],
                "response": interaction["response"],
                "rating": rating,  # 1-5 점수
                "expert_comments": rating.get("comments", "")
            })
        
        return feedback_data
    
    async def train_with_feedback(self, feedback_data: List[Dict]):
        """피드백 데이터로 모델 재학습"""
        # 보상 모델 업데이트
        await self.reward_model.train(feedback_data)
        
        # PPO (Proximal Policy Optimization) 알고리즘으로 모델 개선
        for epoch in range(10):
            for batch in self._create_batches(feedback_data):
                # 응답 생성
                responses = await self.base_model.generate_batch(
                    [item["question"] for item in batch]
                )
                
                # 보상 계산
                rewards = await self.reward_model.predict_rewards(
                    questions=[item["question"] for item in batch],
                    responses=responses
                )
                
                # 정책 업데이트 (높은 보상을 받는 응답 강화)
                loss = self._compute_ppo_loss(responses, rewards)
                await self.base_model.update(loss)
        
        logger.info(f"RLHF training complete: {len(feedback_data)} samples")
```

**4. 신고 시스템 통합**

사용자가 AI 생성 콘텐츠를 신고할 수 있으며, 신고 데이터는 모델 개선에 활용됩니다.

```python
# api/routes/ai_response_report.py
@router.post("/api/ai/report")
async def report_ai_response(
    report: AIResponseReport,
    current_user: User = Depends(get_current_user)
):
    """AI 응답 신고 (부적절한 답변, 오류 등)"""
    # 1. 신고 저장
    report_id = await db.ai_response_reports.insert_one({
        "conversation_id": report.conversation_id,
        "user_input": report.user_input,
        "ai_response": report.ai_response,
        "reported_by": current_user.id,
        "issue_type": report.issue_type,  # "inappropriate", "incorrect", "unhelpful"
        "description": report.description,
        "created_at": datetime.now()
    })
    
    # 2. AI 응답 임시 숨김
    await db.conversations.update_one(
        {"id": report.conversation_id},
        {"$set": {"ai_response_hidden": True}}
    )
    
    # 3. AI 윤리팀 알림
    await slack_notify(
        channel="#ai-ethics",
        message=f"🤖 AI response reported: {report.issue_type}\n"
                f"User: {current_user.name}\n"
                f"Review: /admin/ai-reports/{report_id}"
    )
    
    # 4. RLHF 데이터로 저장 (부정적 피드백)
    await rlhf_trainer.add_negative_feedback({
        "question": report.user_input,
        "response": report.ai_response,
        "rating": 1,  # 낮은 점수
        "issue": report.issue_type
    })
    
    return {"success": True, "report_id": str(report_id)}
```

#### 4.5.6 모니터링 및 감사

**Prometheus 메트릭**:
```python
# governance/backend/metrics.py
COGNITIVE_POLICY_BLOCKS = Counter(
    'cognitive_policy_blocks_total',
    'Total requests blocked by cognitive policy layer',
    ['category', 'reason']
)

COGNITIVE_POLICY_ALLOWS = Counter(
    'cognitive_policy_allows_total',
    'Total requests allowed by cognitive policy layer',
    ['category']
)

AI_RESPONSE_REPORTS = Counter(
    'ai_response_reports_total',
    'Total AI response reports',
    ['issue_type']
)

RLHF_TRAINING_ROUNDS = Counter(
    'rlhf_training_rounds_total',
    'Total RLHF training rounds'
)
```

**정기 감사 스크립트**:
```python
# scripts/audit_ai_behavior.py
async def audit_ai_behavior_policies():
    """AI 행동 정책 효과성 감사"""
    # 1. 최근 30일간 차단된 요청 분석
    blocked_requests = await db.audit_logs.find({
        "event": "cognitive_policy_block",
        "timestamp": {"$gte": datetime.now() - timedelta(days=30)}
    }).to_list(None)
    
    # 2. 카테고리별 차단 통계
    category_stats = {}
    for log in blocked_requests:
        category = log["category"]
        category_stats[category] = category_stats.get(category, 0) + 1
    
    # 3. AI 응답 신고 분석
    reports = await db.ai_response_reports.find({
        "created_at": {"$gte": datetime.now() - timedelta(days=30)}
    }).to_list(None)
    
    issue_stats = {}
    for report in reports:
        issue = report["issue_type"]
        issue_stats[issue] = issue_stats.get(issue, 0) + 1
    
    # 4. RLHF 효과성 평가
    rlhf_metrics = await analyze_rlhf_effectiveness()
    
    # 5. 보고서 생성
    report = {
        "period": "last_30_days",
        "cognitive_blocks": {
            "total": len(blocked_requests),
            "by_category": category_stats
        },
        "user_reports": {
            "total": len(reports),
            "by_issue": issue_stats
        },
        "rlhf_effectiveness": rlhf_metrics,
        "recommendations": []
    }
    
    # 6. 개선 권장사항
    if len(reports) > 100:
        report["recommendations"].append(
            "High number of AI response reports. Review model behavior and retrain."
        )
    
    if category_stats.get("medical_advice", 0) > 50:
        report["recommendations"].append(
            "Frequent medical advice requests detected. Improve user education."
        )
    
    return report

async def analyze_rlhf_effectiveness():
    """RLHF 훈련 효과성 분석"""
    # 훈련 전후 비교
    before_training = await get_model_performance_before_rlhf()
    after_training = await get_current_model_performance()
    
    return {
        "improvement": {
            "safety_score": after_training["safety"] - before_training["safety"],
            "helpfulness": after_training["helpful"] - before_training["helpful"],
            "accuracy": after_training["accuracy"] - before_training["accuracy"]
        },
        "training_rounds": await db.rlhf_training_logs.count_documents({}),
        "feedback_samples": await db.rlhf_feedback.count_documents({})
    }
```

**모니터링 대시보드 (Grafana)**:
```yaml
# Grafana Dashboard: AI Behavior Monitoring
panels:
  - title: "Cognitive Policy Blocks (Last 24h)"
    query: |
      sum(rate(cognitive_policy_blocks_total[24h])) by (category)
  
  - title: "AI Response Quality (User Reports)"
    query: |
      sum(rate(ai_response_reports_total[24h])) by (issue_type)
  
  - title: "RLHF Training Progress"
    query: |
      rlhf_training_rounds_total
  
  - title: "Policy Block Rate"
    query: |
      sum(rate(cognitive_policy_blocks_total[1h])) 
        / 
      sum(rate(cognitive_policy_allows_total[1h]))
```

DreamSeedAI는 위와 같은 정책 및 기술적 메커니즘을 통해, AI가 교육적 가치를 훼손하지 않고 긍정적인 학습 경험을 제공할 수 있도록 지속적으로 노력합니다.

### 4.6 승인/워크플로 정책 (Approval & Workflow Policies)

승인/워크플로 정책은 DreamSeedAI에서 교사나 학부모의 승인 절차가 필요한 상황들을 정의하고 처리하는 규칙입니다. 이 정책은 AI 시스템의 의사 결정에 대한 인간의 감독을 강화하고, 학생들에게 안전하고 적절한 학습 경험을 제공하기 위해 설계되었습니다.

#### 4.6.1 목표

*   **인간 감독 강화**: AI 시스템의 주요 결정에 대한 교사 및 학부모의 승인을 통해 오류 및 부적절한 콘텐츠 노출을 방지합니다.
*   **학습 환경 안전 보장**: 학생들에게 안전하고 적절한 학습 콘텐츠와 활동을 제공합니다.
*   **정책 준수**: 데이터 접근 및 사용에 대한 정책을 효과적으로 시행합니다.
*   **투명성 제공**: 모든 승인 절차를 추적하여 감사 가능성을 보장합니다.

#### 4.6.2 주요 정책 규칙

**고급 콘텐츠 접근**:
*   학생이 특정 수준 이상의 난이도를 가진 콘텐츠에 접근 요청 시 교사 승인 필요
*   민감한 사회 문제와 관련된 콘텐츠 접근 시 사전 승인 필수

**AI 생성 콘텐츠 검토**:
*   새로 생성된 AI 문제는 학생 노출 전 교사 검토 필수
*   교사는 문제의 정확성, 명확성, 교육 과정 연관성을 확인

**개인 정보 접근**:
*   학생의 민감한 개인 정보 (건강 정보, 상담 기록) 접근 시 학부모 동의 필요
*   데이터 접근 목적 및 범위 명시 필수

**외부 자료 링크**:
*   학생의 외부 웹사이트 또는 자료 접근 시 교사 승인 필요
*   유해하거나 부적절한 콘텐츠 노출 방지

**AI 튜터 개인 설정 변경**:
*   학습 방법이나 난이도 조정 시 교사 또는 학부모 승인 필요
*   설정 변경 이력 추적

#### 4.6.3 Rego 정책 구현

**고급 콘텐츠 접근 정책**:
```rego
package approval_advanced_content

import future.keywords.if

default allow = false

# 콘텐츠 난이도 레벨 정의
difficulty_threshold := 8  # 1-10 스케일

# 민감한 주제 목록
sensitive_topics := [
    "politics", "religion", "war", "violence",
    "discrimination", "controversial_history"
]

# 기본 콘텐츠는 승인 없이 접근 가능
allow {
    input.content.difficulty_level < difficulty_threshold
    not is_sensitive_topic(input.content.topic)
}

# 고급 콘텐츠는 교사 승인 필요
allow {
    input.content.difficulty_level >= difficulty_threshold
    input.approval.teacher_approved == true
    input.approval.approved_at != null
}

# 민감한 주제는 교사 승인 필요
allow {
    is_sensitive_topic(input.content.topic)
    input.approval.teacher_approved == true
}

# 민감한 주제 확인
is_sensitive_topic(topic) if {
    topic in sensitive_topics
}

# 승인 필요 사유
deny[msg] {
    input.content.difficulty_level >= difficulty_threshold
    input.approval.teacher_approved != true
    msg := sprintf("Advanced content (level %d) requires teacher approval", [input.content.difficulty_level])
}

deny[msg] {
    is_sensitive_topic(input.content.topic)
    input.approval.teacher_approved != true
    msg := sprintf("Sensitive topic '%s' requires teacher approval", [input.content.topic])
}
```

**AI 생성 콘텐츠 검토 정책**:
```rego
package approval_ai_generated_content

import future.keywords.if

default allow = false

# AI 생성 콘텐츠는 교사 검토 필수
allow {
    input.content.source == "ai_generated"
    input.content.status == "teacher_reviewed"
    input.content.approved_by != null
}

# 인간이 작성한 검증된 콘텐츠는 승인 불필요
allow {
    input.content.source == "human_created"
    input.content.verified == true
}

# 검토 대기 상태
deny[msg] {
    input.content.source == "ai_generated"
    input.content.status == "pending_review"
    msg := "AI-generated content is pending teacher review"
}

# 검토 거부됨
deny[msg] {
    input.content.source == "ai_generated"
    input.content.status == "rejected"
    msg := sprintf("Content rejected by teacher: %s", [input.content.rejection_reason])
}
```

**개인 정보 접근 승인 정책**:
```rego
package approval_personal_data_access

import future.keywords.if
import future.keywords.contains

default allow = false

# 민감한 개인 정보 카테고리
sensitive_data_categories := [
    "health_records", "counseling_records", 
    "family_information", "financial_data"
]

# 일반 학습 데이터는 승인 불필요
allow {
    not is_sensitive_data(input.data_category)
    input.user.role in ["teacher", "student"]
}

# 민감한 데이터는 학부모 동의 필요
allow {
    is_sensitive_data(input.data_category)
    input.approval.parent_consent == true
    input.approval.consent_date != null
    # 동의는 1년 유효
    consent_is_valid(input.approval.consent_date)
}

# 관리자는 모든 데이터 접근 가능 (감사 로그 기록)
allow {
    input.user.role == "administrator"
    input.purpose == "administrative_review"
}

is_sensitive_data(category) if {
    category in sensitive_data_categories
}

consent_is_valid(consent_date) if {
    # 실제 구현에서는 날짜 계산 로직 사용
    consent_date != null
}

deny[msg] {
    is_sensitive_data(input.data_category)
    input.approval.parent_consent != true
    msg := sprintf("Access to %s requires parent consent", [input.data_category])
}

deny[msg] {
    is_sensitive_data(input.data_category)
    input.approval.parent_consent == true
    not consent_is_valid(input.approval.consent_date)
    msg := "Parent consent has expired. Please request new consent."
}
```

**외부 링크 접근 승인 정책**:
```rego
package approval_external_links

import future.keywords.if
import future.keywords.contains

default allow = false

# 화이트리스트 도메인 (사전 승인됨)
whitelisted_domains := [
    "wikipedia.org", "khanacademy.org", "coursera.org",
    "edx.org", "mit.edu", "youtube.com/education"
]

# 화이트리스트 도메인은 승인 불필요
allow {
    is_whitelisted_domain(input.external_link.url)
}

# 기타 도메인은 교사 승인 필요
allow {
    not is_whitelisted_domain(input.external_link.url)
    input.approval.teacher_approved == true
    input.approval.approved_at != null
}

is_whitelisted_domain(url) if {
    some domain in whitelisted_domains
    contains(url, domain)
}

deny[msg] {
    not is_whitelisted_domain(input.external_link.url)
    input.approval.teacher_approved != true
    msg := sprintf("External link '%s' requires teacher approval", [input.external_link.url])
}
```

#### 4.6.4 구현 메커니즘

**1. 정책 엔진 통합**

승인 워크플로우를 관리하고, 해당 이벤트 발생 시 자동으로 승인 절차를 트리거합니다.

```python
# governance/backend/approval_engine.py
from enum import Enum
from typing import Optional, Dict, List
from datetime import datetime, timedelta

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ApprovalRequest:
    def __init__(
        self,
        request_id: str,
        request_type: str,
        requester_id: str,
        approver_role: str,
        content: Dict,
        reason: str = ""
    ):
        self.request_id = request_id
        self.request_type = request_type
        self.requester_id = requester_id
        self.approver_role = approver_role
        self.content = content
        self.reason = reason
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now()
        self.approved_by: Optional[str] = None
        self.approved_at: Optional[datetime] = None
        self.rejection_reason: Optional[str] = None

class ApprovalEngine:
    def __init__(self, policy_engine, notification_service, db):
        self.policy_engine = policy_engine
        self.notification_service = notification_service
        self.db = db
    
    async def request_approval(
        self,
        request_type: str,
        requester_id: str,
        content: Dict,
        reason: str = ""
    ) -> ApprovalRequest:
        """승인 요청 생성 및 처리"""
        
        # 1. 승인이 필요한지 정책 평가
        policy_result = await self._check_approval_required(
            request_type, requester_id, content
        )
        
        if not policy_result["approval_required"]:
            # 승인 불필요 - 즉시 허용
            return self._create_auto_approved_request(
                request_type, requester_id, content
            )
        
        # 2. 승인 요청 생성
        request = ApprovalRequest(
            request_id=generate_uuid(),
            request_type=request_type,
            requester_id=requester_id,
            approver_role=policy_result["approver_role"],
            content=content,
            reason=reason
        )
        
        # 3. 데이터베이스 저장
        await self.db.approval_requests.insert_one(request.__dict__)
        
        # 4. 승인자에게 알림 발송
        await self._send_approval_notification(request)
        
        # 5. 메트릭 기록
        APPROVAL_REQUESTS.labels(
            request_type=request_type,
            approver_role=request.approver_role
        ).inc()
        
        return request
    
    async def _check_approval_required(
        self, 
        request_type: str, 
        requester_id: str, 
        content: Dict
    ) -> Dict:
        """정책 엔진을 통해 승인 필요 여부 확인"""
        
        # 요청 타입별 정책 매핑
        policy_map = {
            "advanced_content_access": "approval_advanced_content",
            "ai_generated_content": "approval_ai_generated_content",
            "personal_data_access": "approval_personal_data_access",
            "external_link_access": "approval_external_links"
        }
        
        policy_name = policy_map.get(request_type)
        if not policy_name:
            return {"approval_required": False}
        
        # 정책 평가 (승인 없이)
        policy_input = {
            "content": content,
            "user": await self._get_user_info(requester_id),
            "approval": {
                "teacher_approved": False,
                "parent_consent": False
            }
        }
        
        result = await self.policy_engine.evaluate(policy_name, policy_input)
        
        if not result["allow"]:
            # 승인 필요
            approver_role = self._determine_approver_role(request_type)
            return {
                "approval_required": True,
                "approver_role": approver_role,
                "reason": result.get("deny", ["Approval required"])[0]
            }
        
        return {"approval_required": False}
    
    def _determine_approver_role(self, request_type: str) -> str:
        """요청 타입에 따른 승인자 역할 결정"""
        approver_map = {
            "advanced_content_access": "teacher",
            "ai_generated_content": "teacher",
            "personal_data_access": "parent",
            "external_link_access": "teacher"
        }
        return approver_map.get(request_type, "teacher")
    
    async def _send_approval_notification(self, request: ApprovalRequest):
        """승인자에게 알림 발송"""
        
        # 승인자 목록 가져오기
        approvers = await self._get_approvers(
            request.approver_role,
            request.requester_id
        )
        
        for approver in approvers:
            # 이메일 알림
            await self.notification_service.send_email(
                to=approver.email,
                subject=f"Approval Request: {request.request_type}",
                template="approval_request",
                context={
                    "request": request,
                    "requester_name": await self._get_user_name(request.requester_id),
                    "approval_link": f"/approvals/{request.request_id}"
                }
            )
            
            # 앱 푸시 알림
            await self.notification_service.send_push(
                user_id=approver.id,
                title="새로운 승인 요청",
                body=f"{request.request_type} 승인이 필요합니다.",
                data={"request_id": request.request_id}
            )
            
            # Slack 알림 (교사용)
            if request.approver_role == "teacher":
                await slack_notify(
                    channel="#teacher-approvals",
                    message=f"📋 New approval request: {request.request_type}\n"
                            f"From: {await self._get_user_name(request.requester_id)}\n"
                            f"Review: /approvals/{request.request_id}"
                )
    
    async def approve_request(
        self,
        request_id: str,
        approver_id: str,
        comments: str = ""
    ) -> bool:
        """승인 요청 승인"""
        
        # 1. 승인 요청 조회
        request = await self.db.approval_requests.find_one(
            {"request_id": request_id}
        )
        
        if not request or request["status"] != ApprovalStatus.PENDING.value:
            raise ValueError("Invalid or already processed approval request")
        
        # 2. 승인자 권한 확인
        approver = await self._get_user_info(approver_id)
        if approver["role"] != request["approver_role"]:
            raise PermissionError("User does not have permission to approve this request")
        
        # 3. 승인 처리
        await self.db.approval_requests.update_one(
            {"request_id": request_id},
            {"$set": {
                "status": ApprovalStatus.APPROVED.value,
                "approved_by": approver_id,
                "approved_at": datetime.now(),
                "comments": comments
            }}
        )
        
        # 4. 요청자에게 알림
        await self.notification_service.send_notification(
            user_id=request["requester_id"],
            title="승인 완료",
            body=f"{request['request_type']} 요청이 승인되었습니다.",
            data={"request_id": request_id}
        )
        
        # 5. 워크플로우 다음 단계 실행
        await self._execute_post_approval_workflow(request)
        
        # 6. 감사 로그 기록
        await self._log_approval_action(
            request_id=request_id,
            action="approved",
            approver_id=approver_id,
            comments=comments
        )
        
        # 7. 메트릭 기록
        APPROVAL_DECISIONS.labels(
            request_type=request["request_type"],
            decision="approved"
        ).inc()
        
        return True
    
    async def reject_request(
        self,
        request_id: str,
        approver_id: str,
        reason: str
    ) -> bool:
        """승인 요청 거부"""
        
        # 1. 승인 요청 조회
        request = await self.db.approval_requests.find_one(
            {"request_id": request_id}
        )
        
        if not request or request["status"] != ApprovalStatus.PENDING.value:
            raise ValueError("Invalid or already processed approval request")
        
        # 2. 승인자 권한 확인
        approver = await self._get_user_info(approver_id)
        if approver["role"] != request["approver_role"]:
            raise PermissionError("User does not have permission to reject this request")
        
        # 3. 거부 처리
        await self.db.approval_requests.update_one(
            {"request_id": request_id},
            {"$set": {
                "status": ApprovalStatus.REJECTED.value,
                "rejected_by": approver_id,
                "rejected_at": datetime.now(),
                "rejection_reason": reason
            }}
        )
        
        # 4. 요청자에게 알림
        await self.notification_service.send_notification(
            user_id=request["requester_id"],
            title="승인 거부",
            body=f"{request['request_type']} 요청이 거부되었습니다.",
            data={
                "request_id": request_id,
                "reason": reason
            }
        )
        
        # 5. 감사 로그 기록
        await self._log_approval_action(
            request_id=request_id,
            action="rejected",
            approver_id=approver_id,
            reason=reason
        )
        
        # 6. 메트릭 기록
        APPROVAL_DECISIONS.labels(
            request_type=request["request_type"],
            decision="rejected"
        ).inc()
        
        return True
    
    async def _execute_post_approval_workflow(self, request: Dict):
        """승인 후 워크플로우 실행"""
        
        workflow_handlers = {
            "advanced_content_access": self._grant_content_access,
            "ai_generated_content": self._publish_content,
            "personal_data_access": self._grant_data_access,
            "external_link_access": self._enable_external_link
        }
        
        handler = workflow_handlers.get(request["request_type"])
        if handler:
            await handler(request)
```

**2. 알림 시스템**

```python
# api/services/notification_service.py
class NotificationService:
    def __init__(self, email_client, push_client, sms_client):
        self.email_client = email_client
        self.push_client = push_client
        self.sms_client = sms_client
    
    async def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        channels: List[str] = ["push", "email"],
        data: Dict = None
    ):
        """다중 채널 알림 발송"""
        
        user = await get_user(user_id)
        
        if "push" in channels and user.push_enabled:
            await self.send_push(user_id, title, body, data)
        
        if "email" in channels and user.email_enabled:
            await self.send_email(
                to=user.email,
                subject=title,
                template="notification",
                context={"title": title, "body": body, "data": data}
            )
        
        if "sms" in channels and user.sms_enabled:
            await self.send_sms(user.phone, f"{title}: {body}")
```

**3. 승인 인터페이스 API**

```python
# api/routes/approvals.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ApprovalRequestCreate(BaseModel):
    request_type: str
    content: Dict
    reason: str = ""

class ApprovalDecision(BaseModel):
    decision: str  # "approve" or "reject"
    comments: str = ""
    reason: str = ""  # for rejection

@router.post("/api/approvals/request")
async def create_approval_request(
    request: ApprovalRequestCreate,
    current_user: User = Depends(get_current_user)
):
    """승인 요청 생성"""
    approval_engine = ApprovalEngine(opa_engine, notification_service, db)
    
    approval_request = await approval_engine.request_approval(
        request_type=request.request_type,
        requester_id=current_user.id,
        content=request.content,
        reason=request.reason
    )
    
    return {
        "request_id": approval_request.request_id,
        "status": approval_request.status.value,
        "message": "Approval request created successfully" 
                   if approval_request.status == ApprovalStatus.PENDING
                   else "Request auto-approved"
    }

@router.get("/api/approvals/pending")
async def get_pending_approvals(
    current_user: User = Depends(get_current_user)
):
    """현재 사용자에게 할당된 대기 중인 승인 요청 조회"""
    
    # 역할에 따른 필터링
    approvals = await db.approval_requests.find({
        "approver_role": current_user.role,
        "status": ApprovalStatus.PENDING.value
    }).sort("created_at", -1).to_list(100)
    
    return approvals

@router.post("/api/approvals/{request_id}/decide")
async def decide_approval(
    request_id: str,
    decision: ApprovalDecision,
    current_user: User = Depends(get_current_user)
):
    """승인 요청에 대한 결정 (승인 또는 거부)"""
    approval_engine = ApprovalEngine(opa_engine, notification_service, db)
    
    try:
        if decision.decision == "approve":
            await approval_engine.approve_request(
                request_id=request_id,
                approver_id=current_user.id,
                comments=decision.comments
            )
            return {"success": True, "message": "Request approved"}
        
        elif decision.decision == "reject":
            if not decision.reason:
                raise HTTPException(
                    status_code=400,
                    detail="Rejection reason is required"
                )
            
            await approval_engine.reject_request(
                request_id=request_id,
                approver_id=current_user.id,
                reason=decision.reason
            )
            return {"success": True, "message": "Request rejected"}
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid decision. Must be 'approve' or 'reject'"
            )
    
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/approvals/history")
async def get_approval_history(
    current_user: User = Depends(get_current_user),
    days: int = 30
):
    """승인 이력 조회"""
    
    start_date = datetime.now() - timedelta(days=days)
    
    history = await db.approval_requests.find({
        "$or": [
            {"requester_id": current_user.id},
            {"approved_by": current_user.id},
            {"rejected_by": current_user.id}
        ],
        "created_at": {"$gte": start_date}
    }).sort("created_at", -1).to_list(200)
    
    return history
```

#### 4.6.5 승인 워크플로우 예시

**시나리오: 고급 콘텐츠 접근 요청**

```python
# 실제 워크플로우 실행 예시
async def student_requests_advanced_content(student_id: str, content_id: str):
    """학생이 고급 콘텐츠 접근 요청"""
    
    # 1. 콘텐츠 정보 조회
    content = await db.contents.find_one({"id": content_id})
    
    # 2. 승인 요청 생성
    approval_engine = ApprovalEngine(opa_engine, notification_service, db)
    
    request = await approval_engine.request_approval(
        request_type="advanced_content_access",
        requester_id=student_id,
        content={
            "content_id": content_id,
            "difficulty_level": content["difficulty_level"],
            "topic": content["topic"],
            "title": content["title"]
        },
        reason="Student requested access to advanced mathematics content"
    )
    
    # 3. 승인 대기 상태 반환
    if request.status == ApprovalStatus.PENDING:
        return {
            "access_granted": False,
            "message": "Your request has been sent to your teacher for approval.",
            "request_id": request.request_id
        }
    else:
        # 자동 승인된 경우
        return {
            "access_granted": True,
            "message": "Access granted to content.",
            "content": content
        }

# 교사가 승인한 후
async def teacher_approves_content_access(request_id: str, teacher_id: str):
    """교사가 콘텐츠 접근 승인"""
    
    approval_engine = ApprovalEngine(opa_engine, notification_service, db)
    
    # 승인 처리
    await approval_engine.approve_request(
        request_id=request_id,
        approver_id=teacher_id,
        comments="Content is appropriate for student's learning level"
    )
    
    # 자동으로 다음 동작 실행:
    # - 학생에게 콘텐츠 접근 권한 부여
    # - 학생에게 알림 발송
    # - 감사 로그 기록
```

**전체 워크플로우**:

```
1. 학생이 고급 콘텐츠 접근 요청
   ↓
2. 시스템이 정책 엔진을 통해 승인 필요 여부 확인
   - 난이도 레벨 8 이상 → 승인 필요
   ↓
3. 승인 요청 생성 및 저장
   ↓
4. 교사에게 알림 발송
   - 이메일: "새로운 승인 요청"
   - 앱 푸시: "학생이 고급 콘텐츠 접근 요청"
   - Slack: "#teacher-approvals 채널"
   ↓
5. 교사가 승인 인터페이스에서 요청 확인
   - 콘텐츠 상세 정보 검토
   - 학생의 학습 레벨 확인
   ↓
6. 교사가 승인 또는 거부 결정
   - 승인: "학생의 수준에 적합함"
   - 거부: "아직 준비가 되지 않음"
   ↓
7. 시스템이 결정에 따라 자동 처리
   승인 시:
   - 학생에게 콘텐츠 접근 권한 부여
   - 학생에게 승인 알림 발송
   - 콘텐츠 제공
   
   거부 시:
   - 학생에게 거부 알림 발송 (사유 포함)
   - 대체 콘텐츠 추천
   ↓
8. 모든 승인 행위를 감사 로그에 기록
   - 타임스탬프
   - 요청자/승인자 ID
   - 결정 및 사유
   - 관련 콘텐츠 정보
```

#### 4.6.6 감사 추적 (Audit Trail)

모든 승인 행위는 상세하게 기록되어 추후 감사 가능하도록 합니다.

```python
# governance/backend/audit_service.py
class ApprovalAuditService:
    def __init__(self, db, elasticsearch_client=None):
        self.db = db
        self.es = elasticsearch_client
    
    async def log_approval_action(
        self,
        request_id: str,
        action: str,  # "created", "approved", "rejected", "expired"
        actor_id: str,
        actor_role: str,
        details: Dict = None
    ):
        """승인 관련 행위 감사 로그 기록"""
        
        audit_log = {
            "timestamp": datetime.now(),
            "event_type": "approval_action",
            "request_id": request_id,
            "action": action,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "actor_name": await self._get_user_name(actor_id),
            "details": details or {},
            "ip_address": get_client_ip(),
            "user_agent": get_user_agent()
        }
        
        # MongoDB에 저장
        await self.db.audit_logs.insert_one(audit_log)
        
        # Elasticsearch에 저장 (검색 및 분석용)
        if self.es:
            await self.es.index(
                index="approval-audit-logs",
                body=audit_log
            )
        
        # 구조화된 로깅
        logger.info(
            "Approval action recorded",
            extra={
                "request_id": request_id,
                "action": action,
                "actor": actor_id,
                "role": actor_role
            }
        )
    
    async def get_approval_audit_trail(
        self,
        request_id: str
    ) -> List[Dict]:
        """특정 승인 요청의 전체 감사 추적 조회"""
        
        audit_trail = await self.db.audit_logs.find({
            "request_id": request_id
        }).sort("timestamp", 1).to_list(None)
        
        return audit_trail
    
    async def generate_approval_report(
        self,
        start_date: datetime,
        end_date: datetime,
        approver_role: str = None
    ) -> Dict:
        """승인 활동 보고서 생성"""
        
        query = {
            "timestamp": {"$gte": start_date, "$lte": end_date},
            "event_type": "approval_action"
        }
        
        if approver_role:
            query["actor_role"] = approver_role
        
        # 승인 통계
        logs = await self.db.audit_logs.find(query).to_list(None)
        
        stats = {
            "total_requests": 0,
            "approved": 0,
            "rejected": 0,
            "pending": 0,
            "by_type": {},
            "by_approver": {},
            "avg_approval_time": timedelta(0)
        }
        
        approval_times = []
        
        for log in logs:
            if log["action"] == "created":
                stats["total_requests"] += 1
                request_type = log["details"].get("request_type", "unknown")
                stats["by_type"][request_type] = stats["by_type"].get(request_type, 0) + 1
            
            elif log["action"] == "approved":
                stats["approved"] += 1
                approver = log["actor_name"]
                stats["by_approver"][approver] = stats["by_approver"].get(approver, 0) + 1
                
                # 승인 시간 계산 (요청 생성 ~ 승인)
                created_log = await self.db.audit_logs.find_one({
                    "request_id": log["request_id"],
                    "action": "created"
                })
                if created_log:
                    approval_time = log["timestamp"] - created_log["timestamp"]
                    approval_times.append(approval_time)
            
            elif log["action"] == "rejected":
                stats["rejected"] += 1
        
        # 평균 승인 시간 계산
        if approval_times:
            stats["avg_approval_time"] = sum(approval_times, timedelta(0)) / len(approval_times)
        
        return stats
```

**Prometheus 메트릭**:

```python
# governance/backend/metrics.py
APPROVAL_REQUESTS = Counter(
    'approval_requests_total',
    'Total approval requests',
    ['request_type', 'approver_role']
)

APPROVAL_DECISIONS = Counter(
    'approval_decisions_total',
    'Total approval decisions',
    ['request_type', 'decision']
)

APPROVAL_PROCESSING_TIME = Histogram(
    'approval_processing_time_seconds',
    'Time taken to process approval requests',
    ['request_type'],
    buckets=[60, 300, 900, 1800, 3600, 7200, 86400]  # 1분 ~ 1일
)

PENDING_APPROVALS = Gauge(
    'pending_approvals_count',
    'Current number of pending approval requests',
    ['approver_role']
)
```

**Grafana 대시보드**:

```yaml
# Grafana Dashboard: Approval Workflow Monitoring
panels:
  - title: "Approval Requests (Last 7 days)"
    query: |
      sum(increase(approval_requests_total[7d])) by (request_type)
  
  - title: "Approval Decision Rate"
    query: |
      sum(rate(approval_decisions_total{decision="approved"}[1h]))
        /
      sum(rate(approval_requests_total[1h]))
  
  - title: "Average Approval Processing Time"
    query: |
      avg(approval_processing_time_seconds) by (request_type)
  
  - title: "Pending Approvals"
    query: |
      pending_approvals_count
```

이러한 승인/워크플로 정책은 DreamSeedAI가 안전하고 신뢰할 수 있는 학습 환경을 제공하는 데 중요한 역할을 수행합니다. 인간 감독과 AI 자동화의 균형을 통해 효율성과 안전성을 동시에 확보합니다.

---

## 5. 정책 생명주기 관리

### 5.1 정책 개발

1. **정책 작성**: Rego 언어로 정책 규칙 작성
2. **단위 테스트**: OPA Test Framework로 정책 테스트
3. **시뮬레이션**: 실제 데이터로 정책 시뮬레이션

**테스트 예시**:
```rego
# governance/bundles/phase0_test.rego
test_teacher_can_access_own_class {
    allow with input as {
        "user": {"role": "teacher", "class_id": "A1"},
        "student": {"class_id": "A1"}
    }
}

test_teacher_cannot_access_other_class {
    not allow with input as {
        "user": {"role": "teacher", "class_id": "A1"},
        "student": {"class_id": "B1"}
    }
}
```

### 5.2 정책 배포

**배포 프로세스**:
```bash
# 1. 정책 컴파일
python governance/scripts/compile.py

# 2. 테스트 실행
opa test governance/bundles/

# 3. 커밋 및 푸시
git add governance/compiled/
git commit -m "feat(policy): Add student data access policy"
git push

# 4. Kubernetes 배포 (Kustomize)
kubectl apply -k ops/k8s/governance/overlays/phase0/

# 5. 검증
bash ops/k8s/governance/monitoring-validation.sh
```

**환경별 배포**:
*   **Dev**: 개발 환경에서 먼저 테스트
*   **Staging**: 프로덕션 유사 환경에서 검증
*   **Production**: 단계적 롤아웃 (Canary Deployment)

### 5.3 정책 모니터링

**실시간 모니터링**:
```bash
# Prometheus 쿼리
rate(governance_policy_deny_total[5m])  # 정책 거부율
histogram_quantile(0.95, governance_policy_evaluation_duration_bucket)  # P95 지연시간
```

**Grafana 대시보드**:
*   정책 평가 성공/실패율
*   정책별 거부 추이
*   정책 평가 지연시간 분포

**Slack 알림**:
*   Critical: 정책 번들 로드 실패
*   Warning: 정책 거부율 급증

### 5.4 정책 감사

**감사 항목**:
*   정책 변경 이력 (Git 커밋 로그)
*   정책 평가 결과 (Prometheus 메트릭)
*   정책 거부 사례 (구조화된 로그)

**규제 준수**:
*   GDPR: 개인정보 처리 정책 감사
*   교육법: 학생 데이터 보호 정책 감사

---

## 6. 고급 기능

### 6.1 Dynamic Policy Loading

**Hot Reload**:
*   ConfigMap 변경 감지
*   자동 정책 번들 리로드
*   무중단 정책 업데이트

**구현**:
```python
# governance/backend/policy_controller.py
async def reload_bundle():
    new_hash = await get_configmap_hash()
    if new_hash != current_hash:
        await opa_client.put("/v1/policies/main", policy_bundle)
        GOVERNANCE_BUNDLE_RELOAD.inc()
        logger.info("Policy bundle reloaded", extra={"hash": new_hash})
```

### 6.2 Policy as Code

**GitOps 워크플로우**:
*   정책 변경 → Git 커밋
*   Pull Request → 코드 리뷰
*   Merge → ArgoCD 자동 배포

**이점**:
*   버전 관리
*   변경 이력 추적
*   롤백 가능
*   코드 리뷰

### 6.3 A/B Testing

**정책 실험**:
*   새로운 정책을 일부 사용자에게만 적용
*   메트릭 비교 (거부율, 지연시간, 사용자 만족도)
*   점진적 롤아웃

**구현**:
```rego
package ab_testing

allow {
    # 50% 사용자에게만 새 정책 적용
    hash(input.user.id) % 100 < 50
    new_policy_allow
}

allow {
    hash(input.user.id) % 100 >= 50
    old_policy_allow
}
```

### 6.4 Machine Learning Integration

**ML 기반 정책**:
*   이상 탐지: 비정상적인 데이터 접근 패턴 탐지
*   추천: 사용자 행동 기반 정책 추천
*   예측: 정책 위반 사전 예측

**구현 계획**:
```python
async def ml_enhanced_policy(input_data: dict) -> bool:
    # 1. 기본 규칙 평가
    base_result = await evaluate_policy("base_policy", input_data)
    
    # 2. ML 모델 평가
    ml_score = await ml_model.predict(input_data)
    
    # 3. 결합 결정
    return base_result["allow"] and ml_score > 0.8
```

---

## 7. 현재 구현 상태

### ✅ 완성된 기능

*   **OPA 정책 엔진**: 3개 정책 번들 (phase0, phase1, production)
*   **백엔드 통합**: 34개 엔드포인트 정책 매핑
*   **미들웨어**: 자동 정책 평가 및 실행
*   **Hot Reload**: ConfigMap 기반 무중단 업데이트
*   **모니터링**: 19개 메트릭, 15개 알림 규칙
*   **대시보드**: Grafana 16 패널
*   **알림**: Slack 통합 (Alertmanager)
*   **문서화**: 14개 문서, 3,500+ 라인

### 🚧 개발 예정 기능

*   **정책 관리 UI**: Web 기반 정책 편집 인터페이스
*   **승인 워크플로우**: 정책 변경 승인 프로세스
*   **A/B 테스팅**: 정책 실험 프레임워크
*   **ML 통합**: 머신러닝 기반 정책 의사결정
*   **감사 대시보드**: 정책 감사 전용 대시보드

---

## 8. 참고 자료

**코드**:
*   `governance/bundles/`: OPA 정책 소스 코드
*   `governance/backend/`: FastAPI 백엔드 통합
*   `ops/k8s/governance/`: Kubernetes 배포 매니페스트

**문서**:
*   `ops/k8s/governance/DEPLOYMENT_RUNBOOK.md`: 배포 가이드
*   `ops/k8s/governance/MONITORING_VERIFICATION.md`: 모니터링 검증
*   `infra/monitoring/alertmanager/QUICKSTART_SLACK.md`: Slack 알림 설정

**외부 문서**:
*   [Open Policy Agent 공식 문서](https://www.openpolicyagent.org/docs/)
*   [Rego 언어 가이드](https://www.openpolicyagent.org/docs/latest/policy-language/)
*   [OPA Kubernetes Tutorial](https://www.openpolicyagent.org/docs/latest/kubernetes-tutorial/)

---

**작성일**: 2025-11-08  
**버전**: 1.0  
**상태**: Production-Ready
