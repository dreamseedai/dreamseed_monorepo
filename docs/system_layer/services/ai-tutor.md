# AI 튜터/대화형 에이전트 (AI Tutor / Conversational Agent)

AI 튜터/대화형 에이전트는 DreamSeedAI 시스템 계층의 또 하나의 핵심 축입니다. 이는 대화형 챗봇으로 구현되어, 학생이 질문을 입력하면 자연어로 답변하거나 설명해주는 개인 맞춤형 학습 지원 서비스입니다.

## 목차

1. [목표](#목표)
2. [주요 기능](#주요-기능)
3. [시스템 아키텍처](#시스템-아키텍처)
4. [구현 상세](#구현-상세)
5. [프롬프트 엔지니어링](#프롬프트-엔지니어링)
6. [세션 컨텍스트 관리](#세션-컨텍스트-관리)
7. [지식 베이스 통합](#지식-베이스-통합)
8. [정책 준수](#정책-준수)
9. [구현 예시](#구현-예시)
10. [기술적 특징](#기술적-특징)
11. [사용 시나리오](#사용-시나리오)
12. [거버넌스 통합](#거버넌스-통합)

---

## 목표

- **개인 맞춤형 학습 지원**: 학생의 질문에 즉각적이고 정확하게 답변하여 학습 이해도를 높입니다.
- **자기 주도 학습 능력 향상**: 학생 스스로 문제를 해결하고 학습 목표를 달성할 수 있도록 돕습니다.
- **교사 부담 경감**: 반복적인 질문에 대한 답변을 자동화하여 교사의 업무 부담을 줄입니다.
- **흥미로운 학습 경험 제공**: 챗봇과의 자연스러운 대화를 통해 학습에 대한 흥미를 유발합니다.

---

## 주요 기능

### 1. 자연어 처리 (Natural Language Processing, NLP)

학생의 질문을 이해하고, 적절한 답변을 생성합니다.

**처리 단계**:
- 질문 분석 (의도 파악)
- 관련 개념 추출
- 학생 수준 파악
- 답변 생성
- 답변 검증

### 2. 문맥 인식 (Context Awareness)

학생 대화 내역을 축적하여, 앞에서 무슨 질문이 오갔는지 기억 (세션 컨텍스트 관리)하고 일관성 있는 답변을 하도록 합니다.

### 3. 지식 기반 (Knowledge Base)

교과 과정, 용어 사전, 참고 자료 등 학습 관련 정보를 저장하고, AI 튜터가 답변 생성 시 활용할 수 있도록 제공합니다.

### 4. 정책 준수

정책 계층과 연계되어, 민감하거나 금지된 주제에 대한 질문은 거부하거나 다른 대응을 하고 (예: "그 주제는 도와줄 수 없지만 ~"), 부적절한 요청은 완곡히 거절합니다.

### 5. 피드백 수집

학생들의 피드백을 수집하여 AI 튜터의 답변 품질을 개선합니다.

---

## 시스템 아키텍처

```
┌──────────────────────────────────────────────┐
│              학생 (Student)                   │
│         웹/모바일 앱에서 질문 입력              │
└──────────────────┬───────────────────────────┘
                   ↓
┌──────────────────────────────────────────────┐
│         AI 튜터 서비스 (AI Tutor Service)      │
│  ┌────────────────────────────────────────┐  │
│  │  1. 질문 수신 & 검증                    │  │
│  │  2. 세션 컨텍스트 조회                   │  │
│  │  3. 학생 프로파일 조회                   │  │
│  └────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────┘
                   ↓
┌──────────────────────────────────────────────┐
│        거버넌스 계층 (Governance Layer)        │
│  정책 검증: "질문이 금지 주제인가?"             │
│  - AI 콘텐츠 필터링                           │
│  - 학생 보호 정책                             │
└──────────────────┬───────────────────────────┘
                   ↓
┌──────────────────────────────────────────────┐
│      지식 베이스 (Knowledge Base)              │
│  - 교과 개념 사전                             │
│  - 선행 개념 관계                             │
│  - 참고 자료 (예시, 설명)                      │
└──────────────────┬───────────────────────────┘
                   ↓
┌──────────────────────────────────────────────┐
│    LLM (Large Language Model)                │
│  - OpenAI GPT-4                              │
│  - Google Gemini                             │
│  - 자체 학습 모델 (선택)                       │
│                                              │
│  프롬프트 구성:                               │
│  - 시스템 역할                                │
│  - 학생 정보                                  │
│  - 대화 이력                                  │
│  - 지식 베이스 정보                           │
│  - 질문                                      │
└──────────────────┬───────────────────────────┘
                   ↓
┌──────────────────────────────────────────────┐
│         답변 후처리 & 필터링                   │
│  - 부적절한 내용 제거                         │
│  - 정책 재검증                                │
│  - 답변 로깅                                  │
└──────────────────┬───────────────────────────┘
                   ↓
┌──────────────────────────────────────────────┐
│              학생에게 답변 반환                 │
│         + 관련 학습 자료 추천                  │
└──────────────────────────────────────────────┘
```

---

## 구현 상세

### 백엔드 구조

#### 1. 대형 언어 모델 (LLM) 호출

OpenAI API, Google Gemini API, 또는 자체 학습 모델 사용 (선택)

```python
from openai import AsyncOpenAI
import os

# LLM 클라이언트 (모듈화)
class LLMClient:
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        
        if provider == "openai":
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4"
        elif provider == "gemini":
            # Google Gemini 클라이언트
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.client = genai
            self.model = "gemini-pro"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def generate_response(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """LLM 응답 생성"""
        
        if self.provider == "openai":
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        elif self.provider == "gemini":
            # Gemini 구현
            model = self.client.GenerativeModel(self.model)
            # messages를 Gemini 형식으로 변환
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            response = await model.generate_content_async(prompt)
            return response.text
```

#### 2. 프롬프트 엔지니어링

DreamSeedAI 컨텍스트에 맞게 최적화된 프롬프트와 추가 정보를 제공하여 AI 튜터의 답변 품질을 향상시킵니다.

**예시**: 학생 수준에 맞는 설명을 생성하도록 합니다.

#### 3. 세션 컨텍스트 관리

학생 대화 내역을 저장하고 관리하여 AI 튜터가 이전 대화 내용을 기억하고 일관성 있는 답변을 할 수 있도록 지원합니다.

---

## 프롬프트 엔지니어링

### 프롬프트 구성 예시

```python
def build_tutor_prompt(
    student_profile: dict,
    question: str,
    related_concepts: list[dict],
    conversation_history: list[dict]
) -> list[dict]:
    """
    AI 튜터 프롬프트 구성
    
    Args:
        student_profile: 학생 정보 (학년, 현재 학습 주제 등)
        question: 학생의 질문
        related_concepts: 관련 개념 설명
        conversation_history: 대화 이력
    
    Returns:
        LLM 메시지 리스트
    """
    # 시스템 프롬프트
    system_prompt = f"""당신은 DreamSeedAI의 AI 튜터입니다. 학생의 질문에 친절하고 명확하게 답변하세요.

**학생 정보**:
- 학년: {student_profile['grade_level']}
- 현재 학습 주제: {student_profile['current_topic']}
- 능력 수준: {student_profile.get('ability_level', '중간')}

**답변 가이드라인**:
1. 학생의 수준에 맞는 쉬운 용어를 사용하세요
2. 단계별로 차근차근 설명하세요
3. 필요시 예시를 들어 설명하세요
4. 학생이 스스로 생각할 수 있도록 힌트를 제공하세요 (정답을 바로 주지 마세요)
5. 격려하고 긍정적인 태도를 유지하세요
6. 수식이 필요한 경우 LaTeX 형식을 사용하세요 (예: $x^2 + 5x + 6 = 0$)
"""
    
    # 관련 개념 정보 추가
    if related_concepts:
        concepts_text = "\n\n**관련 개념 정보**:\n"
        for concept in related_concepts:
            concepts_text += f"\n- **{concept['name']}**: {concept['description']}\n"
        system_prompt += concepts_text
    
    # 메시지 구성
    messages = [{"role": "system", "content": system_prompt}]
    
    # 대화 이력 추가 (최근 5개)
    if conversation_history:
        for msg in conversation_history[-5:]:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
    
    # 현재 질문 추가
    messages.append({"role": "user", "content": question})
    
    return messages
```

### 프롬프트 템플릿 예시

```
당신은 DreamSeedAI의 튜터 봇입니다. 학생의 질문에 친절하고 명확하게 답변하세요.

학생 정보:
  - 학년: 중학교 2학년
  - 과목: 수학
  - 현재 학습 주제: 이차방정식
  - 능력 수준: 중간

학생의 질문: {student_question}

관련 개념 정보:
  - **이차방정식**: 미지수가 2차항까지 포함하는 방정식 (예: ax^2 + bx + c = 0)
  - **인수분해**: 곱셈 형태로 나타내는 것 (예: x^2 + 5x + 6 = (x+2)(x+3))

선행 개념:
  - 일차방정식: 이차방정식을 풀기 위해서는 일차방정식의 해를 구하는 방법을 알아야 합니다.

답변 가이드라인:
1. 학생 수준에 맞는 쉬운 설명
2. 단계별 힌트 제공 (정답 직접 제공 X)
3. 예시와 함께 설명
4. 격려와 긍정적 피드백
```

---

## 세션 컨텍스트 관리

### 데이터베이스 스키마

```sql
-- AI 튜터 세션 테이블
CREATE TABLE ai_tutor_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id),
    
    -- 세션 정보
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'ended'
    
    -- 컨텍스트
    current_topic VARCHAR(200),
    conversation_count INTEGER DEFAULT 0,
    
    CONSTRAINT fk_student FOREIGN KEY (student_id) REFERENCES students(id)
);

-- 대화 이력 테이블
CREATE TABLE ai_tutor_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES ai_tutor_sessions(session_id),
    
    -- 메시지 정보
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    
    -- 메타데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    token_count INTEGER,
    
    -- 피드백
    student_rating INTEGER CHECK (student_rating BETWEEN 1 AND 5),
    helpful BOOLEAN,
    
    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES ai_tutor_sessions(session_id)
);

-- 인덱스
CREATE INDEX idx_tutor_sessions_student ON ai_tutor_sessions(student_id, last_activity_at DESC);
CREATE INDEX idx_tutor_messages_session ON ai_tutor_messages(session_id, created_at ASC);
```

### 세션 관리 구현

```python
import uuid
from datetime import datetime, timezone, timedelta

class TutorSessionManager:
    """AI 튜터 세션 관리"""
    
    async def get_or_create_session(
        self,
        student_id: str,
        current_topic: str = None
    ) -> str:
        """
        활성 세션 조회 또는 생성
        
        Args:
            student_id: 학생 ID
            current_topic: 현재 학습 주제
        
        Returns:
            session_id
        """
        # 최근 1시간 이내 활성 세션 조회
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        session = await db.fetch_one(
            """
            SELECT session_id FROM ai_tutor_sessions
            WHERE student_id = $1 
              AND status = 'active'
              AND last_activity_at >= $2
            ORDER BY last_activity_at DESC
            LIMIT 1
            """,
            student_id, cutoff_time
        )
        
        if session:
            # 기존 세션 활동 시간 업데이트
            await db.execute(
                "UPDATE ai_tutor_sessions SET last_activity_at = NOW() WHERE session_id = $1",
                session['session_id']
            )
            return session['session_id']
        
        # 새 세션 생성
        session_id = str(uuid.uuid4())
        await db.execute(
            """
            INSERT INTO ai_tutor_sessions (session_id, student_id, current_topic)
            VALUES ($1, $2, $3)
            """,
            session_id, student_id, current_topic
        )
        
        return session_id
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> list[dict]:
        """
        대화 이력 조회
        
        Args:
            session_id: 세션 ID
            limit: 최대 개수
        
        Returns:
            대화 이력
        """
        messages = await db.fetch_all(
            """
            SELECT role, content, created_at
            FROM ai_tutor_messages
            WHERE session_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            session_id, limit
        )
        
        # 시간 순으로 정렬 (오래된 것부터)
        return [dict(m) for m in reversed(messages)]
    
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        token_count: int = None
    ):
        """메시지 저장"""
        
        await db.execute(
            """
            INSERT INTO ai_tutor_messages (session_id, role, content, token_count)
            VALUES ($1, $2, $3, $4)
            """,
            session_id, role, content, token_count
        )
        
        # 세션 카운트 증가
        await db.execute(
            """
            UPDATE ai_tutor_sessions
            SET conversation_count = conversation_count + 1,
                last_activity_at = NOW()
            WHERE session_id = $1
            """,
            session_id
        )
```

---

## 지식 베이스 통합

### RAG (Retrieval-Augmented Generation)

```python
async def retrieve_relevant_knowledge(
    question: str,
    student_profile: dict,
    top_k: int = 3
) -> list[dict]:
    """
    질문과 관련된 지식 베이스 정보 검색
    
    Args:
        question: 학생 질문
        student_profile: 학생 프로파일
        top_k: 반환할 개수
    
    Returns:
        관련 개념 리스트
    """
    # 질문 임베딩 생성
    from openai import AsyncOpenAI
    openai_client = AsyncOpenAI()
    
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    )
    question_embedding = response.data[0].embedding
    
    # 벡터 검색 (pgvector 또는 별도 벡터 DB)
    query = """
        SELECT kn.node_id, kn.name, kn.description,
               (kn.embedding <=> $1::vector) as distance
        FROM knowledge_nodes kn
        WHERE kn.node_type = 'concept'
        ORDER BY kn.embedding <=> $1::vector
        LIMIT $2
    """
    
    concepts = await db.fetch_all(query, question_embedding, top_k)
    
    result = []
    for concept in concepts:
        # 선행 개념도 조회
        prerequisites = await db.fetch_all(
            """
            SELECT target_node_id, kn.name
            FROM knowledge_edges ke
            JOIN knowledge_nodes kn ON ke.target_node_id = kn.node_id
            WHERE ke.source_node_id = $1 AND ke.edge_type = 'prerequisite'
            """,
            concept['node_id']
        )
        
        result.append({
            "node_id": concept['node_id'],
            "name": concept['name'],
            "description": concept['description'],
            "prerequisites": [p['name'] for p in prerequisites]
        })
    
    return result
```

---

## 정책 준수

### 정책 적용

AI가 답을 만들기 전 정책 엔진이 "금지된 요청"으로 인지하고 처리를 중단하는 메커니즘. 이 레이어는 AI 모델이 출력을 생성하기 전에, 해당 논의 주제가 정책에 부합하는지 여부를 먼저 판단합니다.

```python
from governance.backend import get_policy_client

async def validate_tutor_request(
    student_id: str,
    question: str,
    session_id: str
) -> dict:
    """
    튜터 요청 정책 검증
    
    Args:
        student_id: 학생 ID
        question: 질문 내용
        session_id: 세션 ID
    
    Returns:
        {"allow": bool, "reason": str, "alternative_response": str}
    """
    policy_client = get_policy_client()
    
    # 정책 평가
    result = await policy_client.evaluate(
        "dreamseedai.ai_tutor.query",
        {
            "student_id": student_id,
            "question": question,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    
    if not result.get("allow"):
        # 거부 사유별 대체 응답
        reason = result.get("reason", "unknown")
        
        if "inappropriate_topic" in reason:
            alternative = "죄송합니다. 해당 주제에 대해서는 도움을 드릴 수 없습니다. 학습과 관련된 다른 질문이 있으신가요?"
        elif "off_topic" in reason:
            alternative = "학습과 관련된 질문에만 답변할 수 있습니다. 수학, 과학, 영어 등의 과목에 대해 질문해 주세요."
        elif "rate_limit" in reason:
            alternative = f"잠시 후 다시 시도해 주세요. (재시도: {result.get('retry_after', 60)}초 후)"
        else:
            alternative = "죄송합니다. 지금은 답변할 수 없습니다."
        
        return {
            "allow": False,
            "reason": reason,
            "alternative_response": alternative
        }
    
    return {"allow": True}
```

### 답변 후처리 필터링

```python
async def filter_ai_response(response: str) -> tuple[str, bool]:
    """
    AI 응답 필터링
    
    Args:
        response: AI 생성 응답
    
    Returns:
        (filtered_response, is_safe)
    """
    policy_client = get_policy_client()
    
    # 콘텐츠 필터링 정책
    result = await policy_client.evaluate(
        "dreamseedai.ai_content.filter",
        {
            "content": {
                "text": response,
                "type": "ai_generated",
                "context": "ai_tutor_response"
            }
        }
    )
    
    if not result.get("allow"):
        # 부적절한 내용 감지
        severity = result.get("severity", "medium")
        
        if severity == "high":
            # 심각한 경우: 안전한 기본 응답
            safe_response = "죄송합니다. 적절한 답변을 생성하지 못했습니다. 다른 방식으로 질문해 주시겠어요?"
            return safe_response, False
        else:
            # 경미한 경우: 경고와 함께 응답
            return response, True
    
    return response, True
```

---

## 구현 예시

### FastAPI 엔드포인트

```python
from fastapi import FastAPI, Request, HTTPException
from governance.backend import require_policy

app = FastAPI()

@app.post("/api/tutor/ask")
@require_policy("dreamseedai.ai_tutor.query")
async def ask_tutor(
    request: Request,
    student_id: str,
    question: str,
    current_topic: str = None
):
    """
    AI 튜터에게 질문
    
    정책 검증:
    - 학생만 질문 가능
    - 질문 내용 검증 (금지 주제, 부적절한 내용)
    - Rate limiting
    """
    # 1. 세션 관리
    session_manager = TutorSessionManager()
    session_id = await session_manager.get_or_create_session(
        student_id, current_topic
    )
    
    # 2. 질문 검증
    validation = await validate_tutor_request(student_id, question, session_id)
    if not validation['allow']:
        return {
            "response": validation['alternative_response'],
            "filtered": True
        }
    
    # 3. 학생 프로파일 조회
    student = await db.fetch_one(
        "SELECT grade_level, current_theta FROM students WHERE id = $1",
        student_id
    )
    
    student_profile = {
        "grade_level": student['grade_level'],
        "current_topic": current_topic or "일반",
        "ability_level": get_ability_level(student['current_theta'])
    }
    
    # 4. 관련 지식 검색 (RAG)
    related_concepts = await retrieve_relevant_knowledge(
        question, student_profile
    )
    
    # 5. 대화 이력 조회
    conversation_history = await session_manager.get_conversation_history(
        session_id, limit=5
    )
    
    # 6. 프롬프트 구성
    messages = build_tutor_prompt(
        student_profile,
        question,
        related_concepts,
        conversation_history
    )
    
    # 7. LLM 호출
    llm_client = LLMClient(provider=os.getenv("LLM_PROVIDER", "openai"))
    ai_response = await llm_client.generate_response(messages)
    
    # 8. 응답 필터링
    filtered_response, is_safe = await filter_ai_response(ai_response)
    
    if not is_safe:
        # 안전하지 않은 응답: 관리자 알림
        await notify_admins(
            f"AI 튜터가 부적절한 응답 생성: {ai_response[:100]}..."
        )
    
    # 9. 대화 저장
    await session_manager.save_message(session_id, "user", question)
    await session_manager.save_message(session_id, "assistant", filtered_response)
    
    # 10. 관련 학습 자료 추천
    recommended_resources = await recommend_resources(
        related_concepts, student_profile
    )
    
    return {
        "response": filtered_response,
        "session_id": session_id,
        "related_concepts": [c['name'] for c in related_concepts],
        "recommended_resources": recommended_resources
    }

@app.post("/api/tutor/feedback")
async def submit_tutor_feedback(
    message_id: str,
    rating: int,
    helpful: bool,
    comment: str = None
):
    """AI 튜터 응답에 대한 피드백 제출"""
    
    await db.execute(
        """
        UPDATE ai_tutor_messages
        SET student_rating = $1, helpful = $2
        WHERE id = $3
        """,
        rating, helpful, message_id
    )
    
    # 피드백 분석 (배치 작업)
    # 낮은 평점의 응답 패턴 분석하여 프롬프트 개선
    
    return {"status": "feedback_received"}
```

---

## 기술적 특징

### 1. 모듈화 설계

AI 튜터 서비스는 모듈화되어 있으므로, 추후 자체 모델이나 다른 API로 쉽게 교체할 수 있습니다.

**API Base URL만 환경변수로 교체하여 다른 LLM 연동 가능**:

```python
# .env 파일
LLM_PROVIDER=openai  # 또는 'gemini', 'custom'
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
CUSTOM_LLM_BASE_URL=http://localhost:8000/v1
```

### 2. 지속적인 개선

DreamSeedAI 개발 팀은 v0.3~v0.4 버전에서 프롬프트 엔지니어링, 추가 지식베이스 구축(예: 교과 개념 사전 연결) 등을 통해 AI 튜터의 품질을 지속적으로 개선할 예정입니다.

**개선 방향**:
- 프롬프트 A/B 테스팅
- 학생 피드백 기반 프롬프트 최적화
- 지식 베이스 확장 (교과서, 참고서 데이터)
- Fine-tuning (장기 계획)

### 3. 커스텀 지식

필요한 정보를 LLM에 넘겨서, 학생 수준에 맞는 설명을 생성하도록 합니다.

---

## 사용 시나리오

### 시나리오 1: 문제 풀이 도움

1. **학생**: "이 문제 모르겠어요. x^2 + 5x + 6 = 0 어떻게 풀어요?"

2. **시스템 처리**:
   - 학생이 풀고 있는 문제 확인
   - 학생의 이전 학습 기록 조회
   - 관련 개념 정보 (이차방정식, 인수분해) 검색
   - AI 튜터 모듈에 데이터 전달

3. **AI 튜터 모듈**:
   - LLM에 쿼리: "학생 수준에 맞는 쉬운 설명으로 제공"
   - 프롬프트: 중학교 2학년 수준, 단계별 힌트 제공

4. **AI 튜터 응답**:
```
이 문제는 이차방정식의 근을 구하는 문제입니다.

먼저, 인수분해를 시도해 보세요.

힌트: 6을 두 수의 곱으로 나타낼 수 있는 방법을 생각해 보세요.
그 두 수를 더하면 5가 되어야 합니다.

예를 들어:
- 1 × 6 = 6, 1 + 6 = 7 (X)
- 2 × 3 = 6, 2 + 3 = 5 (O)

그러면 x^2 + 5x + 6 = (x + 2)(x + 3) 이 됩니다.

이제 (x + 2)(x + 3) = 0을 만족하는 x 값을 찾아보세요!
```

5. **학생**: "아! x = -2 또는 x = -3이네요!"

6. **AI 튜터**: "정확합니다! 🎉 잘했어요. 인수분해를 이용하면 이차방정식을 쉽게 풀 수 있습니다."

### 시나리오 2: 개념 설명 요청

1. **학생**: "이차방정식이 뭐예요?"

2. **시스템**:
   - 지식 베이스에서 "이차방정식" 개념 검색
   - 학생 수준 (중2) 확인
   - 선행 개념 (일차방정식) 확인

3. **AI 튜터 응답**:
```
이차방정식은 미지수 x의 최고 차수가 2인 방정식입니다.

일반적인 형태:
ax^2 + bx + c = 0 (a ≠ 0)

예시:
- x^2 + 5x + 6 = 0
- 2x^2 - 3x + 1 = 0
- x^2 = 9

일차방정식 (예: x + 3 = 0)과 비교하면,
이차방정식은 x^2 항이 추가로 있어요.

이차방정식을 푸는 방법:
1. 인수분해
2. 근의 공식
3. 완전제곱식

어떤 방법에 대해 더 알고 싶으신가요?
```

---

## 거버넌스 통합

AI 튜터는 거버넌스 계층과 긴밀히 통합되어 있습니다.

### 정책 적용 예시

```python
# 1. 질문 전 검증
@require_policy("dreamseedai.ai_tutor.query")
async def ask_tutor(...):
    # 학생 신원 확인
    # 질문 내용 검증
    # Rate limiting
    pass

# 2. 응답 후 필터링
async def filter_ai_response(response):
    # 부적절한 내용 감지
    # 민감 정보 마스킹
    # 정책 위반 시 안전 응답 반환
    pass

# 3. 감사 로깅
# 모든 질문/응답 쌍 로깅
# 정책 위반 사항 별도 로깅
# 관리자 알림
```

**상세 예시**: [거버넌스 통합 예시](../governance-integration/examples.md#ai-튜터링-서비스)

---

## 참조 문서

- **시스템 계층 홈**: [../README.md](../README.md)
- **아키텍처 개요**: [../architecture/overview.md](../architecture/overview.md)
- **거버넌스 통합**: [../governance-integration/examples.md](../governance-integration/examples.md)
- **콘텐츠 관리**: [content-management.md](content-management.md) (지식 베이스)
- **분석 엔진**: [analytics-engine.md](analytics-engine.md) (피드백 분석)
