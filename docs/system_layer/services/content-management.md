# 콘텐츠 관리 서비스 - 문항 은행 및 콘텐츠 관리 (Content Management Service)

시스템 계층에는 문항/콘텐츠 관리 서비스가 있어, DreamSeedAI의 핵심 자산인 문제 데이터베이스를 효율적으로 관리하고, AI 기반의 문항 생성 및 추천 기능을 제공합니다.

## 목차

1. [목표](#목표)
2. [주요 기능](#주요-기능)
3. [문항 데이터베이스 스키마](#문항-데이터베이스-스키마)
4. [IRT 파라미터 관리](#irt-파라미터-관리)
5. [지식 그래프 연동](#지식-그래프-연동)
6. [AI 기반 문항 생성](#ai-기반-문항-생성)
7. [데이터 파이프라인](#데이터-파이프라인)
8. [품질 보증 및 정책 준수](#품질-보증-및-정책-준수)
9. [구현 예시](#구현-예시)
10. [거버넌스 통합](#거버넌스-통합)

---

## 목표

- **체계적인 문항 관리**: 문항 풀 (item bank)의 모든 문제를 체계적으로 저장, 관리, 및 검색합니다.
- **콘텐츠 제작 지원**: 교사 및 콘텐츠 제작자의 문항 추가 및 수정 작업을 용이하게 합니다.
- **IRT 파라미터 관리**: 각 문항의 난이도, 변별도 등 IRT 파라미터를 관리하고, 새로운 문항에 대한 초기 난이도를 추정합니다.
- **지식 그래프 연동**: 문항과 학습 개념 간의 관계를 연결하고, 학생의 취약점을 파악하여 맞춤형 학습을 지원합니다.
- **AI 기반 문항 생성/추천**: 유사 문제 자동 생성 기능을 제공하여 문항 풀을 확장하고, 콘텐츠 제작 비용을 절감합니다.
- **품질 보증**: 생성된 문항의 품질을 교사 검수 및 학생 데이터 분석을 통해 지속적으로 검증하고 보정합니다.

---

## 주요 기능

### 1. 문항 데이터베이스

각 문항의 질문 텍스트, 정답, 해설, 난이도 파라미터 (IRT의 a, b, c 등), 관련 주제 태그, 언어, 참고 자료 등을 저장합니다.

### 2. 콘텐츠 관리 UI

교사나 콘텐츠 크리에이터가 UI를 통해 새 문제를 추가하거나 수정하면 그것을 DB에 반영합니다. 문항의 메타데이터 (난이도, 주제, 관련 개념)를 쉽게 편집할 수 있도록 지원합니다.

### 3. IRT 파라미터 관리

IRT 파라미터가 없는 신규 문항의 경우 초기 난이도를 설정하는 기능도 포함합니다. 예를 들어 AI를 활용한 문항 난이도 추정 – 입력된 문제를 과거 데이터가 없으면 일단 교사 추정으로 넣고, 데이터가 쌓이면 나중에 보정합니다.

### 4. 지식 그래프 연동

문항 은행은 지식 그래프 구조와 연동되어, 각 문항이 커리큘럼 상 어느 주제 (knowledge node)에 연결되는지, 선행지식은 무엇인지 등을 표현합니다.

### 5. AI 기반 문항 생성/추천

교사가 문제를 만들 때 유사 문제 자동 생성 기능을 사용하면 AI가 기존 기출이나 유사 패턴을 참고해 새로운 문제를 제안해 줍니다. 국내 사례로 족보닷컴의 AI 기출변형 기능처럼, DreamSeedAI도 기출 데이터를 바탕으로 새로운 변형 문제를 생성/추천하여 문항 풀을 확충하고 콘텐츠 제작 비용을 절감합니다.

### 6. 데이터 파이프라인

기존 데이터 소스 (예: 시험 문제, 강의 자료)에서 데이터를 수집하고 변환하는 ETL (Extract, Transform, Load) 파이프라인 구축. Amazon S3, Google Cloud Storage, 또는 Azure Blob Storage와 같은 객체 스토리지를 활용하여 대량의 학습 데이터를 저장하고 관리합니다.

---

## 문항 데이터베이스 스키마

### PostgreSQL 스키마

```sql
-- 문항 테이블
CREATE TABLE items (
    item_id VARCHAR(50) PRIMARY KEY,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL,  -- 'multiple_choice', 'short_answer', 'essay'
    answer TEXT NOT NULL,
    explanation TEXT,
    
    -- IRT 파라미터
    difficulty DECIMAL(5,3),      -- b (난이도): -3 ~ +3
    discrimination DECIMAL(5,3),  -- a (변별도): 0 ~ 2.5
    guessing DECIMAL(4,3),         -- c (추측도): 0 ~ 0.25
    
    -- 메타데이터
    language VARCHAR(10) DEFAULT 'ko',
    reference TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 품질 관리
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'review', 'approved', 'deprecated'
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    -- 통계
    times_used INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0
);

-- 문항-스킬 태그 관계 테이블
CREATE TABLE item_skill_tags (
    item_id VARCHAR(50) REFERENCES items(item_id),
    skill_tag VARCHAR(100),
    PRIMARY KEY (item_id, skill_tag)
);

-- 문항-커리큘럼 태그 관계 테이블
CREATE TABLE item_curriculum_tags (
    item_id VARCHAR(50) REFERENCES items(item_id),
    curriculum_tag VARCHAR(100),
    PRIMARY KEY (item_id, curriculum_tag)
);

-- 지식 그래프 노드 테이블
CREATE TABLE knowledge_nodes (
    node_id VARCHAR(50) PRIMARY KEY,
    node_type VARCHAR(20) NOT NULL,  -- 'concept', 'skill', 'topic'
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 지식 그래프 관계 테이블
CREATE TABLE knowledge_edges (
    source_node_id VARCHAR(50) REFERENCES knowledge_nodes(node_id),
    target_node_id VARCHAR(50) REFERENCES knowledge_nodes(node_id),
    edge_type VARCHAR(20) NOT NULL,  -- 'prerequisite', 'related', 'contains'
    weight DECIMAL(3,2) DEFAULT 1.0,
    PRIMARY KEY (source_node_id, target_node_id, edge_type)
);

-- 문항-지식 노드 관계 테이블
CREATE TABLE item_knowledge_mapping (
    item_id VARCHAR(50) REFERENCES items(item_id),
    node_id VARCHAR(50) REFERENCES knowledge_nodes(node_id),
    relevance_score DECIMAL(3,2) DEFAULT 1.0,
    PRIMARY KEY (item_id, node_id)
);

-- 인덱스
CREATE INDEX idx_items_difficulty ON items(difficulty);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_created_at ON items(created_at DESC);
CREATE INDEX idx_item_skill_tags_tag ON item_skill_tags(skill_tag);
CREATE INDEX idx_item_curriculum_tags_tag ON item_curriculum_tags(curriculum_tag);
```

### JSON 문항 예시

```json
{
  "item_id": "MATH-G9-001",
  "question_text": "이차방정식 x^2 + 5x + 6 = 0의 해를 구하시오.",
  "question_type": "short_answer",
  "answer": "x = -2 또는 x = -3",
  "explanation": "이차방정식을 인수분해하여 해를 구할 수 있습니다. (x+2)(x+3) = 0이므로 x = -2 또는 x = -3입니다.",
  
  "difficulty": 0.7,
  "discrimination": 1.2,
  "guessing": 0.2,
  
  "skill_tags": ["이차방정식", "인수분해"],
  "curriculum_tags": ["중학교 3학년 수학", "이차방정식"],
  
  "language": "ko",
  "reference": "수학 교과서 3단원",
  
  "status": "approved",
  "created_by": "teacher-uuid-123",
  "reviewed_by": "reviewer-uuid-456",
  
  "times_used": 125,
  "correct_count": 87,
  "total_count": 125
}
```

---

## IRT 파라미터 관리

### 1. 신규 문항 초기 난이도 추정

IRT 파라미터가 없는 신규 문항의 경우, 다음 방법으로 초기 난이도를 설정합니다:

#### A. 교사 추정 (Manual Estimation)

```python
from fastapi import FastAPI, Request
from governance.backend import require_policy

app = FastAPI()

@app.post("/api/items/create")
@require_policy("dreamseedai.content.create")
async def create_item(
    request: Request,
    item_data: dict,
    initial_difficulty: float = 0.0
):
    """
    새 문항 생성
    
    정책 검증:
    - 콘텐츠 제작 권한 확인
    - 교사 또는 관리자만 가능
    """
    # 초기 IRT 파라미터 설정 (교사 추정)
    item = {
        **item_data,
        "difficulty": initial_difficulty,
        "discrimination": 1.0,  # 기본값
        "guessing": 0.2,         # 기본값 (4지선다: 25%)
        "status": "draft"
    }
    
    # DB 저장
    await db.execute(
        """
        INSERT INTO items (item_id, question_text, answer, explanation,
                          difficulty, discrimination, guessing, status, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        item['item_id'], item['question_text'], item['answer'], item['explanation'],
        item['difficulty'], item['discrimination'], item['guessing'],
        item['status'], request.state.user_id
    )
    
    return {"item_id": item['item_id'], "status": "created"}
```

#### B. AI 기반 난이도 추정

AI를 이용하여 문제를 분석하고 난이도를 추정하는 API 제공:

```python
import openai
from typing import Optional

async def estimate_difficulty_with_ai(
    question_text: str,
    question_type: str,
    curriculum_tags: list[str]
) -> dict:
    """
    AI를 사용한 문항 난이도 추정
    
    Args:
        question_text: 문항 텍스트
        question_type: 문항 유형
        curriculum_tags: 커리큘럼 태그
    
    Returns:
        {"difficulty": float, "discrimination": float, "confidence": float}
    """
    # 유사 문항 검색
    similar_items = await search_similar_items(
        question_text,
        curriculum_tags,
        limit=10
    )
    
    # 유사 문항의 평균 난이도
    if similar_items:
        avg_difficulty = sum(item['difficulty'] for item in similar_items) / len(similar_items)
        avg_discrimination = sum(item['discrimination'] for item in similar_items) / len(similar_items)
        confidence = 0.7  # 유사 문항이 있으면 신뢰도 높음
    else:
        # AI 모델로 추정
        prompt = f"""
        다음 문항의 난이도를 -3(매우 쉬움) ~ +3(매우 어려움) 범위로 추정하세요.
        0은 중간 난이도를 의미합니다.
        
        문항 유형: {question_type}
        커리큘럼: {', '.join(curriculum_tags)}
        
        문항:
        {question_text}
        
        JSON 형식으로 응답하세요:
        {{"difficulty": <float>, "reasoning": "<설명>"}}
        """
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        avg_difficulty = result['difficulty']
        avg_discrimination = 1.0  # 기본값
        confidence = 0.5  # AI 추정은 신뢰도 중간
    
    return {
        "difficulty": avg_difficulty,
        "discrimination": avg_discrimination,
        "guessing": 0.2 if question_type == 'multiple_choice' else 0.0,
        "confidence": confidence
    }
```

### 2. 실시간 IRT 파라미터 보정

학생들의 응답 데이터가 축적되면 IRT 파라미터를 실시간으로 보정합니다:

```python
from scipy.optimize import minimize

async def calibrate_item_parameters(item_id: str):
    """
    문항 IRT 파라미터 보정 (실제 응답 데이터 기반)
    
    Args:
        item_id: 문항 ID
    """
    # 해당 문항에 대한 모든 응답 데이터 조회
    responses = await db.fetch_all(
        """
        SELECT lr.student_id, lr.score, s.current_theta
        FROM learning_records lr
        JOIN students s ON lr.student_id = s.id
        WHERE lr.item_id = $1 AND s.current_theta IS NOT NULL
        """,
        item_id
    )
    
    if len(responses) < 30:  # 최소 30개 응답 필요
        return None
    
    # Log-Likelihood 함수
    def log_likelihood(params):
        a, b, c = params
        ll = 0
        for response in responses:
            theta = response['current_theta']
            score = response['score']  # 1 (정답) or 0 (오답)
            
            # IRT 3PL 확률
            P = c + (1 - c) / (1 + np.exp(-a * (theta - b)))
            
            if score == 1:
                ll += np.log(P + 1e-10)
            else:
                ll += np.log(1 - P + 1e-10)
        
        return -ll  # 최소화를 위해 음수
    
    # 최적화 (초기값: 현재 파라미터)
    current_params = await get_item_parameters(item_id)
    initial_guess = [
        current_params['discrimination'],
        current_params['difficulty'],
        current_params['guessing']
    ]
    
    result = minimize(
        log_likelihood,
        initial_guess,
        bounds=[(0.1, 2.5), (-3, 3), (0, 0.35)],
        method='L-BFGS-B'
    )
    
    # 보정된 파라미터 저장
    new_a, new_b, new_c = result.x
    await db.execute(
        """
        UPDATE items
        SET discrimination = $1, difficulty = $2, guessing = $3, updated_at = NOW()
        WHERE item_id = $4
        """,
        new_a, new_b, new_c, item_id
    )
    
    return {"a": new_a, "b": new_b, "c": new_c}
```

---

## 지식 그래프 연동

문항 은행은 지식 그래프 구조와 연동되어, 각 문항이 커리큘럼 상 어느 주제 (knowledge node)에 연결되는지, 선행지식은 무엇인지 등을 표현합니다.

### 지식 그래프 예시

```json
{
  "node_id": "이차방정식",
  "type": "concept",
  "name": "이차방정식",
  "description": "미지수가 2차항까지 포함하는 방정식",
  "prerequisite": ["일차방정식", "인수분해"],
  "related_items": ["MATH-G9-001", "MATH-G9-002", "MATH-G9-015"]
}
```

### 지식 그래프 활용

#### 1. 취약 개념 파악

```python
async def identify_weak_concepts(student_id: str) -> list[dict]:
    """
    학생의 취약 개념 파악
    
    Args:
        student_id: 학생 ID
    
    Returns:
        취약 개념 리스트 (정답률 낮은 순)
    """
    # 학생의 학습 기록 조회
    query = """
        SELECT ikm.node_id, kn.name,
               COUNT(*) as total_attempts,
               SUM(CASE WHEN lr.score = 1 THEN 1 ELSE 0 END) as correct_count
        FROM learning_records lr
        JOIN item_knowledge_mapping ikm ON lr.item_id = ikm.item_id
        JOIN knowledge_nodes kn ON ikm.node_id = kn.node_id
        WHERE lr.student_id = $1
        GROUP BY ikm.node_id, kn.name
        HAVING COUNT(*) >= 3
        ORDER BY (SUM(CASE WHEN lr.score = 1 THEN 1 ELSE 0 END)::float / COUNT(*)) ASC
        LIMIT 5
    """
    
    weak_concepts = await db.fetch_all(query, student_id)
    
    result = []
    for concept in weak_concepts:
        accuracy = concept['correct_count'] / concept['total_attempts']
        result.append({
            "node_id": concept['node_id'],
            "name": concept['name'],
            "accuracy": accuracy,
            "total_attempts": concept['total_attempts']
        })
    
    return result
```

#### 2. 선행 학습 경로 추천

```python
async def recommend_learning_path(student_id: str, target_concept: str) -> list[str]:
    """
    특정 개념 학습을 위한 선행 학습 경로 추천
    
    Args:
        student_id: 학생 ID
        target_concept: 목표 개념 ID
    
    Returns:
        학습 경로 (선행 개념 순서대로)
    """
    # 선행 개념 조회 (재귀적으로)
    query = """
        WITH RECURSIVE prerequisites AS (
            -- 기본 케이스: 목표 개념
            SELECT node_id, target_node_id as prerequisite_id, 1 as depth
            FROM knowledge_edges
            WHERE source_node_id = $1 AND edge_type = 'prerequisite'
            
            UNION ALL
            
            -- 재귀 케이스: 선행 개념의 선행 개념
            SELECT ke.source_node_id, ke.target_node_id, p.depth + 1
            FROM knowledge_edges ke
            JOIN prerequisites p ON ke.source_node_id = p.prerequisite_id
            WHERE ke.edge_type = 'prerequisite' AND p.depth < 5
        )
        SELECT DISTINCT kn.node_id, kn.name, MIN(p.depth) as depth
        FROM prerequisites p
        JOIN knowledge_nodes kn ON p.prerequisite_id = kn.node_id
        GROUP BY kn.node_id, kn.name
        ORDER BY depth DESC
    """
    
    prerequisites = await db.fetch_all(query, target_concept)
    
    # 학생이 아직 마스터하지 못한 선행 개념만 필터링
    learning_path = []
    for prereq in prerequisites:
        mastery = await check_concept_mastery(student_id, prereq['node_id'])
        if mastery < 0.7:  # 70% 미만이면 학습 필요
            learning_path.append(prereq['node_id'])
    
    return learning_path
```

#### 3. 문항 추천 (지식 그래프 기반)

```python
async def recommend_items_for_concept(
    student_id: str,
    concept_id: str,
    count: int = 10
) -> list[dict]:
    """
    특정 개념에 대한 문항 추천
    
    Args:
        student_id: 학생 ID
        concept_id: 개념 ID
        count: 추천 문항 수
    
    Returns:
        추천 문항 리스트
    """
    # 학생의 현재 능력치 조회
    student = await db.fetch_one(
        "SELECT current_theta FROM students WHERE id = $1",
        student_id
    )
    theta = student['current_theta'] or 0.0
    
    # 해당 개념과 관련된 문항 중 학생이 안 푼 문항 조회
    query = """
        SELECT i.item_id, i.question_text, i.difficulty, i.discrimination, i.guessing
        FROM items i
        JOIN item_knowledge_mapping ikm ON i.item_id = ikm.item_id
        WHERE ikm.node_id = $1
          AND i.status = 'approved'
          AND i.item_id NOT IN (
              SELECT item_id FROM learning_records WHERE student_id = $2
          )
        ORDER BY ABS(i.difficulty - $3)  -- 학생 능력치와 유사한 난이도
        LIMIT $4
    """
    
    items = await db.fetch_all(query, concept_id, student_id, theta, count)
    
    return [dict(item) for item in items]
```

---

## AI 기반 문항 생성

교사가 문제를 만들 때 유사 문제 자동 생성 기능을 사용하면 AI가 기존 기출이나 유사 패턴을 참고해 새로운 문제를 제안해 줍니다.

### 1. 유사 문항 검색 (Semantic Search)

```python
from openai import AsyncOpenAI
import numpy as np

openai_client = AsyncOpenAI()

async def search_similar_items(
    query_text: str,
    curriculum_tags: list[str] = None,
    limit: int = 5
) -> list[dict]:
    """
    유사 문항 검색 (임베딩 기반)
    
    Args:
        query_text: 검색할 문항 텍스트
        curriculum_tags: 필터링할 커리큘럼 태그
        limit: 반환 개수
    
    Returns:
        유사 문항 리스트
    """
    # 쿼리 임베딩
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query_text
    )
    query_embedding = response.data[0].embedding
    
    # PostgreSQL의 pgvector 확장 사용 (벡터 검색)
    # 또는 별도의 벡터 DB (Pinecone, Weaviate 등) 사용 가능
    
    if curriculum_tags:
        tag_filter = "AND curriculum_tag = ANY($2)"
        params = [query_embedding, curriculum_tags, limit]
    else:
        tag_filter = ""
        params = [query_embedding, limit]
    
    query = f"""
        SELECT i.item_id, i.question_text, i.difficulty,
               (i.embedding <=> $1::vector) as distance
        FROM items i
        LEFT JOIN item_curriculum_tags ict ON i.item_id = ict.item_id
        WHERE i.status = 'approved' {tag_filter}
        ORDER BY i.embedding <=> $1::vector
        LIMIT ${len(params)}
    """
    
    similar_items = await db.fetch_all(query, *params)
    
    return [dict(item) for item in similar_items]
```

### 2. AI 기반 문항 생성

```python
async def generate_similar_item(
    source_item_id: str,
    variation_type: str = "numbers"
) -> dict:
    """
    기존 문항을 기반으로 변형 문항 생성
    
    Args:
        source_item_id: 원본 문항 ID
        variation_type: 변형 유형 ('numbers', 'context', 'difficulty')
    
    Returns:
        생성된 문항
    """
    # 원본 문항 조회
    source_item = await db.fetch_one(
        "SELECT * FROM items WHERE item_id = $1",
        source_item_id
    )
    
    # AI 프롬프트 생성
    if variation_type == "numbers":
        prompt = f"""
        다음 수학 문제의 숫자만 변경하여 새로운 문제를 생성하세요.
        난이도는 유지하되, 숫자를 다르게 변경하세요.
        
        원본 문제:
        {source_item['question_text']}
        
        원본 정답:
        {source_item['answer']}
        
        원본 해설:
        {source_item['explanation']}
        
        JSON 형식으로 응답하세요:
        {{
          "question_text": "<새 문제>",
          "answer": "<새 정답>",
          "explanation": "<새 해설>"
        }}
        """
    
    elif variation_type == "context":
        prompt = f"""
        다음 문제의 문맥(상황)을 변경하여 새로운 문제를 생성하세요.
        핵심 개념과 난이도는 유지하되, 상황을 다르게 설정하세요.
        
        원본 문제:
        {source_item['question_text']}
        
        JSON 형식으로 응답하세요:
        {{
          "question_text": "<새 문제>",
          "answer": "<새 정답>",
          "explanation": "<새 해설>"
        }}
        """
    
    elif variation_type == "difficulty":
        prompt = f"""
        다음 문제를 더 어렵게 변형하세요.
        추가 조건을 넣거나, 여러 단계를 거쳐야 풀 수 있도록 하세요.
        
        원본 문제:
        {source_item['question_text']}
        
        JSON 형식으로 응답하세요:
        {{
          "question_text": "<새 문제>",
          "answer": "<새 정답>",
          "explanation": "<새 해설>",
          "difficulty_increase": <난이도 증가량 (0.5 ~ 1.5)>
        }}
        """
    
    # AI 호출
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    generated = json.loads(response.choices[0].message.content)
    
    # 새 문항 ID 생성
    new_item_id = f"AI-GEN-{uuid.uuid4().hex[:8].upper()}"
    
    # 난이도 조정
    if variation_type == "difficulty" and "difficulty_increase" in generated:
        new_difficulty = source_item['difficulty'] + generated['difficulty_increase']
    else:
        new_difficulty = source_item['difficulty']
    
    # 새 문항 데이터 구성
    new_item = {
        "item_id": new_item_id,
        "question_text": generated['question_text'],
        "question_type": source_item['question_type'],
        "answer": generated['answer'],
        "explanation": generated.get('explanation', ''),
        "difficulty": new_difficulty,
        "discrimination": source_item['discrimination'],
        "guessing": source_item['guessing'],
        "status": "draft",  # 교사 검수 필요
        "source_item_id": source_item_id,
        "generation_method": f"ai_{variation_type}"
    }
    
    return new_item

@app.post("/api/items/generate")
@require_policy("dreamseedai.content.generate")
async def generate_item_variations(
    request: Request,
    source_item_id: str,
    count: int = 3,
    variation_type: str = "numbers"
):
    """
    AI 기반 문항 생성
    
    정책 검증:
    - 콘텐츠 생성 권한 확인
    - 교사만 가능
    """
    generated_items = []
    
    for _ in range(count):
        new_item = await generate_similar_item(source_item_id, variation_type)
        
        # DB 저장 (draft 상태)
        await db.execute(
            """
            INSERT INTO items (item_id, question_text, question_type, answer, explanation,
                              difficulty, discrimination, guessing, status, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            new_item['item_id'], new_item['question_text'], new_item['question_type'],
            new_item['answer'], new_item['explanation'],
            new_item['difficulty'], new_item['discrimination'], new_item['guessing'],
            new_item['status'], request.state.user_id
        )
        
        generated_items.append(new_item)
    
    return {"generated_items": generated_items}
```

---

## 데이터 파이프라인

기존 데이터 소스 (예: 시험 문제, 강의 자료)에서 데이터를 수집하고 변환하는 ETL (Extract, Transform, Load) 파이프라인 구축.

### ETL 파이프라인 아키텍처

```
[데이터 소스]
  ├─ 기출 문제 (PDF, 이미지)
  ├─ 교과서 (텍스트, 이미지)
  └─ 외부 API
         ↓
[Extract] (데이터 수집)
  ├─ OCR (문제 이미지 → 텍스트)
  ├─ PDF 파싱
  └─ API 호출
         ↓
[Transform] (데이터 변환)
  ├─ 텍스트 정제
  ├─ 메타데이터 추출 (난이도, 주제)
  ├─ 임베딩 생성
  └─ IRT 파라미터 추정
         ↓
[Load] (데이터 저장)
  ├─ PostgreSQL (문항 데이터)
  ├─ S3/MinIO (이미지, PDF)
  └─ Vector DB (임베딩)
```

### ETL 구현 예시

```python
import boto3
from PIL import Image
import pytesseract

# S3 클라이언트
s3_client = boto3.client('s3')

async def extract_items_from_pdf(pdf_path: str) -> list[dict]:
    """
    PDF 파일에서 문항 추출
    
    Args:
        pdf_path: PDF 파일 경로 (S3 또는 로컬)
    
    Returns:
        추출된 문항 리스트
    """
    # S3에서 PDF 다운로드
    if pdf_path.startswith('s3://'):
        bucket, key = pdf_path.replace('s3://', '').split('/', 1)
        local_path = f"/tmp/{key.split('/')[-1]}"
        s3_client.download_file(bucket, key, local_path)
    else:
        local_path = pdf_path
    
    # PDF를 이미지로 변환
    images = convert_from_path(local_path)
    
    extracted_items = []
    
    for page_num, image in enumerate(images):
        # OCR로 텍스트 추출
        text = pytesseract.image_to_string(image, lang='kor+eng')
        
        # 문항 파싱 (정규 표현식 또는 AI 사용)
        items = parse_items_from_text(text)
        
        for item in items:
            # 메타데이터 추가
            item['source'] = pdf_path
            item['page_number'] = page_num + 1
            
            # AI로 난이도 추정
            difficulty_estimate = await estimate_difficulty_with_ai(
                item['question_text'],
                item.get('question_type', 'multiple_choice'),
                item.get('curriculum_tags', [])
            )
            item.update(difficulty_estimate)
            
            # 임베딩 생성
            embedding = await generate_embedding(item['question_text'])
            item['embedding'] = embedding
            
            extracted_items.append(item)
    
    return extracted_items

async def load_items_to_database(items: list[dict]):
    """
    문항을 데이터베이스에 로드
    
    Args:
        items: 문항 리스트
    """
    for item in items:
        # DB에 삽입 (draft 상태)
        await db.execute(
            """
            INSERT INTO items (item_id, question_text, question_type, answer, explanation,
                              difficulty, discrimination, guessing, embedding, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'draft')
            ON CONFLICT (item_id) DO NOTHING
            """,
            item['item_id'], item['question_text'], item['question_type'],
            item['answer'], item['explanation'],
            item['difficulty'], item['discrimination'], item['guessing'],
            item['embedding']
        )
```

### 객체 스토리지 활용 (MinIO/S3)

```python
async def upload_item_media(
    item_id: str,
    media_file: bytes,
    media_type: str  # 'image', 'audio', 'video'
) -> str:
    """
    문항 미디어 파일을 S3에 업로드
    
    Args:
        item_id: 문항 ID
        media_file: 미디어 파일 바이트
        media_type: 미디어 유형
    
    Returns:
        S3 URL
    """
    bucket_name = "dreamseed-item-media"
    key = f"{media_type}/{item_id}/{uuid.uuid4()}.{get_extension(media_type)}"
    
    # S3 업로드
    s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=media_file,
        ContentType=get_content_type(media_type)
    )
    
    # URL 반환
    url = f"s3://{bucket_name}/{key}"
    return url
```

---

## 품질 보증 및 정책 준수

### 1. 교사 검수 워크플로우

AI가 생성한 문항은 반드시 교사 검수를 거쳐 은행에 등재됩니다.

```python
@app.post("/api/items/{item_id}/review")
@require_policy("dreamseedai.content.review")
async def review_item(
    request: Request,
    item_id: str,
    action: str,  # 'approve' or 'reject'
    feedback: str = None
):
    """
    문항 검수
    
    정책 검증:
    - 검수 권한 확인
    - 교사 또는 관리자만 가능
    """
    if action == "approve":
        # 승인
        await db.execute(
            """
            UPDATE items
            SET status = 'approved',
                reviewed_by = $1,
                reviewed_at = NOW()
            WHERE item_id = $2
            """,
            request.state.user_id,
            item_id
        )
        
        # 임베딩 생성 (검색용)
        item = await db.fetch_one("SELECT question_text FROM items WHERE item_id = $1", item_id)
        embedding = await generate_embedding(item['question_text'])
        await db.execute(
            "UPDATE items SET embedding = $1 WHERE item_id = $2",
            embedding, item_id
        )
        
    elif action == "reject":
        # 거부
        await db.execute(
            """
            UPDATE items
            SET status = 'rejected',
                reviewed_by = $1,
                reviewed_at = NOW(),
                review_feedback = $2
            WHERE item_id = $3
            """,
            request.state.user_id,
            feedback,
            item_id
        )
    
    return {"item_id": item_id, "status": action}
```

### 2. 데이터 검증 및 품질 관리

학생들의 정오답 데이터를 지속적으로 검증/보정하여 문항 품질을 유지합니다.

```python
async def monitor_item_quality():
    """
    문항 품질 모니터링 (배치 작업)
    
    - 정답률이 너무 높거나 낮은 문항 식별
    - IRT 파라미터 이상치 탐지
    - 변별도가 낮은 문항 식별
    """
    # 정답률이 95% 이상 또는 5% 이하인 문항
    extreme_items = await db.fetch_all(
        """
        SELECT item_id, question_text,
               correct_count::float / NULLIF(total_count, 0) as accuracy
        FROM items
        WHERE total_count >= 50
          AND (correct_count::float / total_count > 0.95
               OR correct_count::float / total_count < 0.05)
        """
    )
    
    for item in extreme_items:
        # 알림 생성
        await notify_content_team(
            f"문항 {item['item_id']}의 정답률이 비정상적입니다 ({item['accuracy']:.1%}). "
            "검토가 필요합니다."
        )
    
    # 변별도가 0.3 미만인 문항
    low_discrimination_items = await db.fetch_all(
        """
        SELECT item_id, question_text, discrimination
        FROM items
        WHERE total_count >= 30 AND discrimination < 0.3
        """
    )
    
    for item in low_discrimination_items:
        await notify_content_team(
            f"문항 {item['item_id']}의 변별도가 낮습니다 ({item['discrimination']:.2f}). "
            "문항 수정 또는 제거를 고려하세요."
        )
```

---

## 구현 예시

### FastAPI 엔드포인트 전체

```python
from fastapi import FastAPI, Request, HTTPException, UploadFile
from governance.backend import require_policy

app = FastAPI()

@app.get("/api/items/search")
async def search_items(
    query: str = None,
    curriculum_tags: list[str] = None,
    difficulty_min: float = -3,
    difficulty_max: float = 3,
    limit: int = 20
):
    """문항 검색"""
    
    if query:
        # 시맨틱 검색
        items = await search_similar_items(query, curriculum_tags, limit)
    else:
        # 필터링 검색
        items = await db.fetch_all(
            """
            SELECT i.*
            FROM items i
            LEFT JOIN item_curriculum_tags ict ON i.item_id = ict.item_id
            WHERE i.status = 'approved'
              AND i.difficulty BETWEEN $1 AND $2
              AND ($3::text[] IS NULL OR ict.curriculum_tag = ANY($3))
            LIMIT $4
            """,
            difficulty_min, difficulty_max, curriculum_tags, limit
        )
    
    return {"items": items}

@app.get("/api/items/{item_id}")
async def get_item(item_id: str):
    """문항 상세 조회"""
    
    item = await db.fetch_one(
        "SELECT * FROM items WHERE item_id = $1",
        item_id
    )
    
    if not item:
        raise HTTPException(404, "Item not found")
    
    return dict(item)

@app.post("/api/items/{item_id}/media")
@require_policy("dreamseedai.content.upload_media")
async def upload_item_media_endpoint(
    request: Request,
    item_id: str,
    file: UploadFile
):
    """문항 미디어 업로드"""
    
    media_bytes = await file.read()
    media_type = file.content_type.split('/')[0]  # 'image', 'audio', 'video'
    
    url = await upload_item_media(item_id, media_bytes, media_type)
    
    # 문항에 미디어 URL 연결
    await db.execute(
        "UPDATE items SET media_url = $1 WHERE item_id = $2",
        url, item_id
    )
    
    return {"media_url": url}
```

---

## 거버넌스 통합

콘텐츠 관리 서비스는 거버넌스 계층과 통합되어 정책을 준수합니다.

### 정책 적용 예시

```python
# 콘텐츠 생성 권한
@app.post("/api/items")
@require_policy("dreamseedai.content.create")
async def create_item_endpoint(request: Request, item_data: dict):
    """
    정책 검증:
    - 교사 또는 관리자만 생성 가능
    - 콘텐츠 생성 할당량 확인
    """
    # ... (구현 생략)

# AI 생성 문항 승인
@app.post("/api/items/{item_id}/approve")
@require_policy("dreamseedai.content.approve_ai_generated")
async def approve_ai_item(request: Request, item_id: str):
    """
    정책 검증:
    - AI 생성 문항은 반드시 교사 검수 필요
    - 승인 권한 확인
    """
    # ... (구현 생략)
```

**상세 예시**: [거버넌스 통합 예시](../governance-integration/examples.md)

---

## 참조 문서

- **시스템 계층 홈**: [../README.md](../README.md)
- **평가 엔진 서비스**: [assessment-engine.md](assessment-engine.md)
- **아키텍처 개요**: [../architecture/overview.md](../architecture/overview.md)
- **거버넌스 통합**: [../governance-integration/examples.md](../governance-integration/examples.md)
- **AI 모델 - IRT**: [../ai-models/irt-model.md](../ai-models/irt-model.md) (작성 예정)
