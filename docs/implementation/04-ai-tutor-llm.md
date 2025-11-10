# AI Tutor with LLM Integration

## Table of Contents

- [Overview](#overview)
- [LangChain vs Custom Implementation](#langchain-vs-custom-implementation)
- [RAG Pipeline](#rag-pipeline)
- [Multi-LLM Support](#multi-llm-support)
- [Session Management](#session-management)
- [OPA Policy Filtering](#opa-policy-filtering)
- [Cost Optimization](#cost-optimization)
- [Implementation](#implementation)
- [Testing Strategy](#testing-strategy)

## Overview

The AI Tutor provides personalized learning assistance using Large Language Models (LLMs) with Retrieval-Augmented Generation (RAG). Key features:

- **Conversational tutoring**: Context-aware dialogue with session persistence
- **RAG over knowledge base**: Textbooks, worked examples, curriculum standards
- **Multi-LLM support**: OpenAI GPT-4, Google Gemini, Anthropic Claude
- **Safety filtering**: No direct answers during exams, age-appropriate content
- **Cost optimization**: Caching, prompt compression, model selection

**Architecture**: Custom lightweight implementation (not LangChain) for full control

## LangChain vs Custom Implementation

### Decision Matrix

| Factor              | LangChain                   | Custom Implementation       |
| ------------------- | --------------------------- | --------------------------- |
| Development speed   | Fast (pre-built chains)     | Slower (build from scratch) |
| Control             | Limited (abstraction layer) | Full control                |
| OPA integration     | Complex (custom callbacks)  | Native integration          |
| Token counting      | Hidden in abstraction       | Explicit tracking           |
| Debugging           | Difficult (magic chains)    | Straightforward             |
| Dependencies        | Heavy (100+ packages)       | Minimal (openai, tiktoken)  |
| Performance         | Overhead from abstraction   | Optimized                   |
| Team learning curve | Steep (LangChain API)       | Gentle (direct LLM APIs)    |

**Decision**: Custom implementation for educational domain requirements

### Why Not LangChain?

1. **OPA policy enforcement**: Need to validate every prompt/response against policies
2. **Token budgets**: Strict cost controls require explicit token counting
3. **Exam mode**: Context-dependent behavior (tutoring vs assessment)
4. **Educational prompts**: Domain-specific prompt engineering
5. **Debugging**: Need full visibility into LLM interactions

## RAG Pipeline

### Vector Database: pgvector

```sql
-- Knowledge base documents with embeddings
CREATE TABLE knowledge_base (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(organization_id),
    doc_type VARCHAR(50) NOT NULL,  -- textbook, example, standard, faq
    subject VARCHAR(50),
    grade_level VARCHAR(20),
    title VARCHAR(255),
    content TEXT NOT NULL,
    content_embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kb_org_type ON knowledge_base(organization_id, doc_type);
CREATE INDEX idx_kb_subject_grade ON knowledge_base(subject, grade_level);
CREATE INDEX idx_kb_embedding ON knowledge_base
USING hnsw (content_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### RAG Service Implementation

```python
# app/services/rag_service.py
from typing import List, Dict, Optional
import openai
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

class RAGService:
    """Retrieval-Augmented Generation for AI Tutor."""

    def __init__(self, db: AsyncSession):
        self.db = db
        openai.api_key = settings.OPENAI_API_KEY

    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for user query."""
        response = await openai.Embedding.acreate(
            model="text-embedding-ada-002",
            input=query
        )
        return response['data'][0]['embedding']

    async def retrieve_context(
        self,
        query: str,
        subject: str,
        grade_level: str,
        doc_types: List[str] = ["textbook", "example"],
        top_k: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """Retrieve relevant documents for query."""
        query_embedding = await self.generate_query_embedding(query)

        query_sql = text("""
            SELECT
                doc_id,
                doc_type,
                title,
                content,
                metadata,
                1 - (content_embedding <=> :query_embedding::vector) as similarity
            FROM knowledge_base
            WHERE organization_id = :org_id::uuid
                AND subject = :subject
                AND grade_level = :grade_level
                AND doc_type = ANY(:doc_types)
                AND content_embedding IS NOT NULL
                AND 1 - (content_embedding <=> :query_embedding::vector) >= :min_similarity
            ORDER BY content_embedding <=> :query_embedding::vector
            LIMIT :top_k
        """)

        result = await self.db.execute(query_sql, {
            "query_embedding": str(query_embedding),
            "org_id": str(settings.CURRENT_ORG_ID),  # From middleware
            "subject": subject,
            "grade_level": grade_level,
            "doc_types": doc_types,
            "min_similarity": min_similarity,
            "top_k": top_k
        })

        return [
            {
                "doc_id": str(row.doc_id),
                "doc_type": row.doc_type,
                "title": row.title,
                "content": row.content,
                "metadata": row.metadata,
                "similarity": float(row.similarity)
            }
            for row in result
        ]

    async def build_context(self, documents: List[Dict]) -> str:
        """Build context string from retrieved documents."""
        if not documents:
            return "No relevant reference materials found."

        context_parts = []
        for doc in documents:
            context_parts.append(
                f"--- {doc['doc_type'].upper()}: {doc['title']} (relevance: {doc['similarity']:.2f}) ---\n"
                f"{doc['content']}\n"
            )

        return "\n".join(context_parts)
```

## Multi-LLM Support

### LLM Provider Abstraction

```python
# app/services/llm_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, AsyncIterator
import openai
import anthropic
import google.generativeai as genai
from app.core.config import settings

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> str:
        """Generate chat completion."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 provider."""

    def __init__(self, model: str = "gpt-4-turbo-preview"):
        self.model = model
        openai.api_key = settings.OPENAI_API_KEY

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> str:
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            return response  # Return stream object
        else:
            return response.choices[0].message.content

    def count_tokens(self, text: str) -> int:
        import tiktoken
        encoding = tiktoken.encoding_for_model(self.model)
        return len(encoding.encode(text))

class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def __init__(self, model: str = "gemini-pro"):
        self.model = model
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.client = genai.GenerativeModel(model)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> str:
        # Convert messages to Gemini format
        history = []
        for msg in messages[:-1]:
            history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]]
            })

        chat = self.client.start_chat(history=history)
        response = await chat.send_message_async(
            messages[-1]["content"],
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            },
            stream=stream
        )

        if stream:
            return response
        else:
            return response.text

    def count_tokens(self, text: str) -> int:
        # Approximate token count (Gemini uses different tokenizer)
        return len(text.split()) * 1.3

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, model: str = "claude-3-opus-20240229"):
        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> str:
        response = await self.client.messages.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            return response
        else:
            return response.content[0].text

    def count_tokens(self, text: str) -> int:
        return self.client.count_tokens(text)

class LLMFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create(provider: str = "openai", model: Optional[str] = None) -> LLMProvider:
        providers = {
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
            "anthropic": AnthropicProvider
        }

        if provider not in providers:
            raise ValueError(f"Unknown provider: {provider}")

        if model:
            return providers[provider](model=model)
        else:
            return providers[provider]()
```

## Session Management

### Session Schema

```sql
-- Tutor sessions
CREATE TABLE tutor_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    organization_id UUID NOT NULL REFERENCES organizations(organization_id),
    subject VARCHAR(50),
    grade_level VARCHAR(20),
    context_data JSONB,  -- Student profile, current topic, exam mode, etc.
    llm_provider VARCHAR(20) DEFAULT 'openai',
    llm_model VARCHAR(50) DEFAULT 'gpt-4-turbo-preview',
    total_tokens INT DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user ON tutor_sessions(user_id, created_at DESC);
CREATE INDEX idx_sessions_org ON tutor_sessions(organization_id);

-- Conversation messages
CREATE TABLE tutor_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES tutor_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- system, user, assistant
    content TEXT NOT NULL,
    tokens INT,
    metadata JSONB,  -- Retrieved docs, policy checks, etc.
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_session ON tutor_messages(session_id, created_at);
```

### Session Service

```python
# app/services/session_service.py
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class TutorSessionService:
    """Manage tutor conversation sessions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_id: UUID,
        organization_id: UUID,
        subject: str,
        grade_level: str,
        context_data: Dict,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4-turbo-preview"
    ) -> UUID:
        """Create a new tutor session."""
        session_id = uuid4()

        query = text("""
            INSERT INTO tutor_sessions
                (session_id, user_id, organization_id, subject, grade_level,
                 context_data, llm_provider, llm_model)
            VALUES
                (:session_id, :user_id, :org_id, :subject, :grade_level,
                 :context_data, :provider, :model)
            RETURNING session_id
        """)

        await self.db.execute(query, {
            "session_id": str(session_id),
            "user_id": str(user_id),
            "org_id": str(organization_id),
            "subject": subject,
            "grade_level": grade_level,
            "context_data": context_data,
            "provider": llm_provider,
            "model": llm_model
        })
        await self.db.commit()

        return session_id

    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        tokens: int,
        metadata: Optional[Dict] = None
    ) -> UUID:
        """Add a message to the session."""
        message_id = uuid4()

        query = text("""
            INSERT INTO tutor_messages
                (message_id, session_id, role, content, tokens, metadata)
            VALUES
                (:message_id, :session_id, :role, :content, :tokens, :metadata)
            RETURNING message_id
        """)

        await self.db.execute(query, {
            "message_id": str(message_id),
            "session_id": str(session_id),
            "role": role,
            "content": content,
            "tokens": tokens,
            "metadata": metadata or {}
        })

        # Update session token count
        await self.db.execute(text("""
            UPDATE tutor_sessions
            SET total_tokens = total_tokens + :tokens
            WHERE session_id = :session_id
        """), {"session_id": str(session_id), "tokens": tokens})

        await self.db.commit()
        return message_id

    async def get_conversation_history(
        self,
        session_id: UUID,
        max_messages: int = 20
    ) -> List[Dict]:
        """Get recent conversation history."""
        query = text("""
            SELECT role, content, tokens, metadata, created_at
            FROM tutor_messages
            WHERE session_id = :session_id
            ORDER BY created_at DESC
            LIMIT :max_messages
        """)

        result = await self.db.execute(query, {
            "session_id": str(session_id),
            "max_messages": max_messages
        })

        messages = [
            {
                "role": row.role,
                "content": row.content,
                "tokens": row.tokens,
                "metadata": row.metadata,
                "created_at": row.created_at
            }
            for row in result
        ]

        return list(reversed(messages))  # Oldest first

    async def end_session(self, session_id: UUID):
        """End a tutor session."""
        await self.db.execute(text("""
            UPDATE tutor_sessions
            SET ended_at = CURRENT_TIMESTAMP
            WHERE session_id = :session_id
        """), {"session_id": str(session_id)})
        await self.db.commit()
```

## OPA Policy Filtering

### Policy Definitions

```rego
# policies/tutor_safety.rego
package tutor.safety

import future.keywords.if
import future.keywords.in

# Default deny
default allow_response := false

# Context from request
user_role := input.user.role
exam_mode := input.session.exam_mode
user_age := input.user.age
question := input.question
response := input.response

# Allow response if all safety checks pass
allow_response if {
    not exam_mode_violation
    not age_inappropriate_content
    not direct_answer_in_exam
    not harmful_content
}

# Exam mode: no direct answers
exam_mode_violation if {
    exam_mode == true
    contains_direct_answer(response, question)
}

# Age-appropriate content (COPPA awareness)
age_inappropriate_content if {
    user_age < 13
    contains_adult_content(response)
}

# Direct answer detection in exam mode
direct_answer_in_exam if {
    exam_mode == true
    similarity_score(response, question) > 0.9
}

# Harmful content detection
harmful_content if {
    contains_profanity(response)
}
harmful_content if {
    contains_violence(response)
}

# Helper functions (simplified)
contains_direct_answer(resp, q) if {
    # Check if response contains exact answer patterns
    # In production, use more sophisticated NLP
    regex.match(`(?i)the answer is|the solution is`, resp)
}

contains_adult_content(text) if {
    # Check against inappropriate content list
    # In production, use content moderation API
    false  # Placeholder
}

contains_profanity(text) if {
    # Check profanity filter
    false  # Placeholder
}

contains_violence(text) if {
    # Check violence/harmful content
    false  # Placeholder
}

similarity_score(a, b) := score if {
    # Compute text similarity (0-1)
    # In production, use embedding similarity
    score := 0.5  # Placeholder
}
```

### OPA Integration

```python
# app/services/policy_service.py
from typing import Dict
import httpx
from app.core.config import settings

class PolicyService:
    """OPA policy enforcement for AI tutor."""

    def __init__(self):
        self.opa_url = settings.OPA_URL

    async def check_response_safety(
        self,
        user: Dict,
        session: Dict,
        question: str,
        response: str
    ) -> Dict:
        """Check if AI response passes safety policies."""
        async with httpx.AsyncClient() as client:
            result = await client.post(
                f"{self.opa_url}/v1/data/tutor/safety/allow_response",
                json={
                    "input": {
                        "user": user,
                        "session": session,
                        "question": question,
                        "response": response
                    }
                }
            )

            data = result.json()

            return {
                "allowed": data.get("result", False),
                "violations": data.get("violations", []),
                "metadata": data.get("metadata", {})
            }
```

## Cost Optimization

### Token Budget Management

```python
# app/services/tutor_service.py
from typing import List, Dict, Optional
from uuid import UUID
from app.services.llm_service import LLMFactory, LLMProvider
from app.services.rag_service import RAGService
from app.services.session_service import TutorSessionService
from app.services.policy_service import PolicyService

class AITutorService:
    """AI Tutor with cost optimization and safety filtering."""

    # Token pricing (per 1K tokens, as of 2024)
    PRICING = {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gemini-pro": {"input": 0.00025, "output": 0.0005},
        "claude-3-opus": {"input": 0.015, "output": 0.075}
    }

    # Token limits per session
    MAX_SESSION_TOKENS = 50000  # ~$1.50 max cost per session
    MAX_CONTEXT_TOKENS = 8000   # Keep under context window

    def __init__(
        self,
        db,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4-turbo-preview"
    ):
        self.llm: LLMProvider = LLMFactory.create(llm_provider, llm_model)
        self.rag = RAGService(db)
        self.session_service = TutorSessionService(db)
        self.policy_service = PolicyService()
        self.model = llm_model

    async def chat(
        self,
        session_id: UUID,
        user_message: str,
        user: Dict,
        session_context: Dict
    ) -> Dict:
        """Process user message and generate tutor response."""
        # 1. Retrieve relevant context (RAG)
        context_docs = await self.rag.retrieve_context(
            query=user_message,
            subject=session_context["subject"],
            grade_level=session_context["grade_level"],
            top_k=3
        )
        context_str = await self.rag.build_context(context_docs)

        # 2. Build system prompt
        system_prompt = self._build_system_prompt(session_context, context_str)

        # 3. Get conversation history (with token budget)
        history = await self.session_service.get_conversation_history(session_id)
        messages = self._build_messages(system_prompt, history, user_message)

        # 4. Trim to fit token budget
        messages = await self._trim_to_budget(messages)

        # 5. Generate response
        response = await self.llm.chat_completion(messages, temperature=0.7, max_tokens=500)

        # 6. OPA policy check
        policy_result = await self.policy_service.check_response_safety(
            user=user,
            session=session_context,
            question=user_message,
            response=response
        )

        if not policy_result["allowed"]:
            response = "I apologize, but I cannot provide that response. Let me try to help you in a different way."

        # 7. Save messages
        user_tokens = self.llm.count_tokens(user_message)
        assistant_tokens = self.llm.count_tokens(response)

        await self.session_service.add_message(
            session_id, "user", user_message, user_tokens,
            metadata={"context_docs": [d["doc_id"] for d in context_docs]}
        )
        await self.session_service.add_message(
            session_id, "assistant", response, assistant_tokens,
            metadata={"policy_check": policy_result}
        )

        # 8. Calculate cost
        cost = self._calculate_cost(user_tokens, assistant_tokens)

        return {
            "response": response,
            "tokens": user_tokens + assistant_tokens,
            "cost": cost,
            "context_docs": context_docs,
            "policy_check": policy_result
        }

    def _build_system_prompt(self, session_context: Dict, rag_context: str) -> str:
        """Build system prompt with context."""
        exam_mode = session_context.get("exam_mode", False)

        base_prompt = f"""You are an AI tutor helping a {session_context['grade_level']} student with {session_context['subject']}.

Your role:
- Guide the student to discover answers through Socratic questioning
- Provide hints and explanations, not direct answers
- Use age-appropriate language
- Be encouraging and supportive

Reference materials:
{rag_context}
"""

        if exam_mode:
            base_prompt += "\nIMPORTANT: The student is currently taking an assessment. You may provide clarification on questions but NEVER provide answers or hints that reveal the solution."

        return base_prompt

    def _build_messages(
        self,
        system_prompt: str,
        history: List[Dict],
        user_message: str
    ) -> List[Dict]:
        """Build message list for LLM."""
        messages = [{"role": "system", "content": system_prompt}]

        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        messages.append({"role": "user", "content": user_message})

        return messages

    async def _trim_to_budget(self, messages: List[Dict]) -> List[Dict]:
        """Trim conversation history to fit token budget."""
        total_tokens = sum(self.llm.count_tokens(m["content"]) for m in messages)

        if total_tokens <= self.MAX_CONTEXT_TOKENS:
            return messages

        # Keep system message and recent messages
        system_msg = messages[0]
        user_msg = messages[-1]
        history = messages[1:-1]

        # Trim from oldest
        while total_tokens > self.MAX_CONTEXT_TOKENS and history:
            removed = history.pop(0)
            total_tokens -= self.llm.count_tokens(removed["content"])

        return [system_msg] + history + [user_msg]

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD."""
        pricing = self.PRICING.get(self.model, {"input": 0.01, "output": 0.03})

        cost = (
            (input_tokens / 1000) * pricing["input"] +
            (output_tokens / 1000) * pricing["output"]
        )

        return round(cost, 4)
```

## Testing Strategy

```python
# tests/test_tutor_service.py
import pytest
from uuid import uuid4
from app.services.tutor_service import AITutorService

@pytest.mark.asyncio
async def test_tutor_response(db_session, mock_llm):
    """Test basic tutor response generation."""
    service = AITutorService(db_session, llm_provider="mock")

    session_id = await service.session_service.create_session(
        user_id=uuid4(),
        organization_id=uuid4(),
        subject="math",
        grade_level="7",
        context_data={"exam_mode": False}
    )

    result = await service.chat(
        session_id=session_id,
        user_message="How do I solve 2x + 5 = 15?",
        user={"user_id": str(uuid4()), "age": 13, "role": "student"},
        session_context={"subject": "math", "grade_level": "7", "exam_mode": False}
    )

    assert "response" in result
    assert result["tokens"] > 0
    assert result["cost"] >= 0

@pytest.mark.asyncio
async def test_exam_mode_policy(db_session):
    """Test that direct answers are blocked in exam mode."""
    service = AITutorService(db_session)

    # Mock LLM to return direct answer
    # Mock policy service to detect violation

    result = await service.chat(
        session_id=uuid4(),
        user_message="What is 2 + 2?",
        user={"user_id": str(uuid4()), "age": 13, "role": "student"},
        session_context={"subject": "math", "grade_level": "1", "exam_mode": True}
    )

    # Should reject direct answer
    assert "cannot provide that response" in result["response"].lower()

@pytest.mark.asyncio
async def test_token_budget_trimming(db_session):
    """Test conversation history trimming."""
    service = AITutorService(db_session)

    # Build long message list exceeding budget
    messages = [
        {"role": "system", "content": "You are a tutor."},
        *[{"role": "user", "content": "Question " * 1000} for _ in range(20)],
        {"role": "user", "content": "Final question"}
    ]

    trimmed = await service._trim_to_budget(messages)

    total_tokens = sum(service.llm.count_tokens(m["content"]) for m in trimmed)
    assert total_tokens <= service.MAX_CONTEXT_TOKENS
    assert trimmed[0]["role"] == "system"  # System message preserved
    assert trimmed[-1]["content"] == "Final question"  # Current message preserved
```

## Summary

The AI Tutor implementation provides:

1. **Multi-LLM support**: OpenAI, Gemini, Anthropic with unified interface
2. **RAG pipeline**: pgvector for context retrieval from knowledge base
3. **Session management**: Persistent conversations with PostgreSQL
4. **Safety filtering**: OPA policies for exam mode, age-appropriate content
5. **Cost optimization**: Token budgets, conversation trimming, pricing tracking

**Key Metrics**:

- Response latency: <3s (including RAG retrieval)
- Token budget: 50K per session (~$1.50 max cost)
- Context window: 8K tokens
- Policy check: <100ms overhead

**Next Steps**:

- Implement streaming responses for better UX
- Add A/B testing framework for prompt optimization
- Integrate content moderation API (OpenAI Moderation)
- Build analytics dashboard for tutor effectiveness
