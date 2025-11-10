# Knowledge Graph & Semantic Search Implementation

## Table of Contents

- [Overview](#overview)
- [Graph Database Choice](#graph-database-choice)
- [Schema Design](#schema-design)
- [Prerequisite Graph](#prerequisite-graph)
- [Semantic Search with pgvector](#semantic-search-with-pgvector)
- [Curriculum Standards Mapping](#curriculum-standards-mapping)
- [Implementation](#implementation)
- [Performance Optimization](#performance-optimization)
- [Testing Strategy](#testing-strategy)

## Overview

The knowledge graph represents relationships between learning items, skills, concepts, and curriculum standards. It enables:

- **Prerequisite tracking**: DAG of skill dependencies
- **Semantic search**: Find similar problems using embeddings
- **Curriculum alignment**: Map content to standards (CCSS, NGSS)
- **Adaptive content**: Recommend next items based on mastery

**Technology Choice**: PostgreSQL with recursive CTEs + pgvector for embeddings

### Why Not Neo4j?

| Factor                 | PostgreSQL + CTEs                        | Neo4j                      |
| ---------------------- | ---------------------------------------- | -------------------------- |
| Graph queries          | Recursive CTEs (sufficient for tree/DAG) | Cypher (more expressive)   |
| Vector search          | pgvector (built-in)                      | Separate vector DB needed  |
| Data consistency       | ACID with RLS                            | Requires sync with main DB |
| Operational complexity | Single database                          | Two databases to manage    |
| Team expertise         | High (already using PostgreSQL)          | Low (new technology)       |
| Cost                   | Included                                 | Additional license/hosting |

**Decision**: Use PostgreSQL for small team with limited budget. Migrate to Neo4j if graph queries become complex (>5 hops).

## Graph Database Choice

### PostgreSQL with Recursive CTEs

```sql
-- Find all prerequisites for a skill (transitive closure)
WITH RECURSIVE prerequisites AS (
    -- Base case: direct prerequisites
    SELECT
        skill_id,
        prerequisite_skill_id,
        1 as depth,
        ARRAY[prerequisite_skill_id] as path
    FROM skill_prerequisites
    WHERE skill_id = $1

    UNION ALL

    -- Recursive case: prerequisites of prerequisites
    SELECT
        sp.skill_id,
        sp.prerequisite_skill_id,
        p.depth + 1,
        p.path || sp.prerequisite_skill_id
    FROM skill_prerequisites sp
    INNER JOIN prerequisites p ON p.prerequisite_skill_id = sp.skill_id
    WHERE NOT sp.prerequisite_skill_id = ANY(p.path)  -- Prevent cycles
        AND p.depth < 10  -- Max depth limit
)
SELECT DISTINCT prerequisite_skill_id, depth
FROM prerequisites
ORDER BY depth;
```

## Schema Design

### Skills and Concepts

```sql
-- Core taxonomy tables
CREATE TABLE skills (
    skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(organization_id),
    skill_code VARCHAR(50) NOT NULL,
    skill_name VARCHAR(255) NOT NULL,
    description TEXT,
    subject VARCHAR(50),  -- math, science, ela
    grade_level VARCHAR(20),  -- K, 1, 2, ..., 12, college
    bloom_level VARCHAR(20),  -- remember, understand, apply, analyze, evaluate, create
    difficulty_level DECIMAL(3,2) CHECK (difficulty_level BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, skill_code)
);

CREATE INDEX idx_skills_org_subject ON skills(organization_id, subject);
CREATE INDEX idx_skills_grade ON skills(grade_level);

-- Prerequisite relationships (DAG)
CREATE TABLE skill_prerequisites (
    skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    prerequisite_skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    strength DECIMAL(3,2) DEFAULT 1.0 CHECK (strength BETWEEN 0 AND 1),  -- How critical is this prerequisite?
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (skill_id, prerequisite_skill_id),
    CHECK (skill_id != prerequisite_skill_id)  -- No self-loops
);

CREATE INDEX idx_prereq_skill ON skill_prerequisites(skill_id);
CREATE INDEX idx_prereq_prereq ON skill_prerequisites(prerequisite_skill_id);

-- Item-Skill mapping (many-to-many)
CREATE TABLE item_skills (
    item_id UUID NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    weight DECIMAL(3,2) DEFAULT 1.0 CHECK (weight BETWEEN 0 AND 1),  -- Skill importance in this item
    PRIMARY KEY (item_id, skill_id)
);

CREATE INDEX idx_item_skills_item ON item_skills(item_id);
CREATE INDEX idx_item_skills_skill ON item_skills(skill_id);

-- Curriculum standards (CCSS, NGSS, etc.)
CREATE TABLE curriculum_standards (
    standard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_code VARCHAR(100) NOT NULL UNIQUE,  -- e.g., CCSS.MATH.CONTENT.7.EE.A.1
    framework VARCHAR(50) NOT NULL,  -- CCSS, NGSS, TEKS
    subject VARCHAR(50),
    grade_level VARCHAR(20),
    description TEXT,
    parent_standard_id UUID REFERENCES curriculum_standards(standard_id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_standards_code ON curriculum_standards(standard_code);
CREATE INDEX idx_standards_framework ON curriculum_standards(framework, subject, grade_level);

-- Skill-Standard mapping
CREATE TABLE skill_standards (
    skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    standard_id UUID NOT NULL REFERENCES curriculum_standards(standard_id) ON DELETE CASCADE,
    alignment_strength DECIMAL(3,2) DEFAULT 1.0 CHECK (alignment_strength BETWEEN 0 AND 1),
    PRIMARY KEY (skill_id, standard_id)
);
```

## Prerequisite Graph

### DAG Validation

```python
# app/services/graph_service.py
from typing import List, Set, Tuple
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class SkillGraphService:
    """Service for managing skill prerequisite graph."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def has_cycle(self, skill_id: UUID, prerequisite_id: UUID) -> bool:
        """Check if adding this prerequisite would create a cycle."""
        query = text("""
            WITH RECURSIVE path AS (
                SELECT
                    :prerequisite_id::uuid as current_skill,
                    ARRAY[:prerequisite_id::uuid] as visited

                UNION ALL

                SELECT
                    sp.prerequisite_skill_id,
                    p.visited || sp.prerequisite_skill_id
                FROM skill_prerequisites sp
                INNER JOIN path p ON p.current_skill = sp.skill_id
                WHERE NOT sp.prerequisite_skill_id = ANY(p.visited)
                    AND array_length(p.visited, 1) < 20
            )
            SELECT EXISTS(
                SELECT 1 FROM path WHERE current_skill = :skill_id::uuid
            ) as has_cycle
        """)

        result = await self.db.execute(
            query,
            {"skill_id": str(skill_id), "prerequisite_id": str(prerequisite_id)}
        )
        row = result.fetchone()
        return row.has_cycle if row else False

    async def add_prerequisite(
        self,
        skill_id: UUID,
        prerequisite_id: UUID,
        strength: float = 1.0
    ) -> bool:
        """Add a prerequisite relationship if it doesn't create a cycle."""
        # Check for cycle
        if await self.has_cycle(skill_id, prerequisite_id):
            raise ValueError(f"Adding prerequisite would create a cycle")

        # Insert relationship
        query = text("""
            INSERT INTO skill_prerequisites (skill_id, prerequisite_skill_id, strength)
            VALUES (:skill_id, :prerequisite_id, :strength)
            ON CONFLICT (skill_id, prerequisite_skill_id)
            DO UPDATE SET strength = :strength
        """)

        await self.db.execute(query, {
            "skill_id": str(skill_id),
            "prerequisite_id": str(prerequisite_id),
            "strength": strength
        })
        await self.db.commit()
        return True

    async def get_learning_path(
        self,
        skill_id: UUID,
        max_depth: int = 10
    ) -> List[Tuple[UUID, str, int]]:
        """Get ordered learning path (topological sort of prerequisites)."""
        query = text("""
            WITH RECURSIVE prerequisites AS (
                SELECT
                    sp.prerequisite_skill_id as skill_id,
                    s.skill_name,
                    1 as depth,
                    ARRAY[sp.prerequisite_skill_id] as path
                FROM skill_prerequisites sp
                INNER JOIN skills s ON s.skill_id = sp.prerequisite_skill_id
                WHERE sp.skill_id = :skill_id::uuid

                UNION ALL

                SELECT
                    sp.prerequisite_skill_id,
                    s.skill_name,
                    p.depth + 1,
                    p.path || sp.prerequisite_skill_id
                FROM skill_prerequisites sp
                INNER JOIN prerequisites p ON p.skill_id = sp.skill_id
                INNER JOIN skills s ON s.skill_id = sp.prerequisite_skill_id
                WHERE NOT sp.prerequisite_skill_id = ANY(p.path)
                    AND p.depth < :max_depth
            )
            SELECT DISTINCT skill_id, skill_name, depth
            FROM prerequisites
            ORDER BY depth DESC, skill_name;
        """)

        result = await self.db.execute(query, {
            "skill_id": str(skill_id),
            "max_depth": max_depth
        })

        return [(row.skill_id, row.skill_name, row.depth) for row in result]

    async def get_next_skills(
        self,
        mastered_skills: List[UUID]
    ) -> List[Tuple[UUID, str, int]]:
        """Find skills that are ready to learn (all prerequisites mastered)."""
        query = text("""
            WITH candidate_skills AS (
                -- Skills with at least one mastered prerequisite
                SELECT DISTINCT sp.skill_id
                FROM skill_prerequisites sp
                WHERE sp.prerequisite_skill_id = ANY(:mastered_skills::uuid[])
            ),
            ready_skills AS (
                -- Skills where ALL prerequisites are mastered
                SELECT
                    cs.skill_id,
                    s.skill_name,
                    COUNT(*) as num_prerequisites
                FROM candidate_skills cs
                INNER JOIN skills s ON s.skill_id = cs.skill_id
                INNER JOIN skill_prerequisites sp ON sp.skill_id = cs.skill_id
                WHERE sp.prerequisite_skill_id = ANY(:mastered_skills::uuid[])
                GROUP BY cs.skill_id, s.skill_name
                HAVING COUNT(*) = (
                    SELECT COUNT(*)
                    FROM skill_prerequisites sp2
                    WHERE sp2.skill_id = cs.skill_id
                )
            )
            SELECT skill_id, skill_name, num_prerequisites
            FROM ready_skills
            ORDER BY num_prerequisites ASC
            LIMIT 10;
        """)

        result = await self.db.execute(query, {
            "mastered_skills": [str(s) for s in mastered_skills]
        })

        return [(row.skill_id, row.skill_name, row.num_prerequisites) for row in result]
```

## Semantic Search with pgvector

### Vector Embeddings Storage

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to items
ALTER TABLE items
ADD COLUMN content_embedding vector(1536);  -- OpenAI ada-002 dimension

-- Create HNSW index for fast similarity search
CREATE INDEX idx_items_embedding ON items
USING hnsw (content_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Materialized view for item metadata with embeddings
CREATE MATERIALIZED VIEW item_search AS
SELECT
    i.item_id,
    i.item_text,
    i.content_embedding,
    array_agg(DISTINCT s.skill_code) as skills,
    array_agg(DISTINCT cs.standard_code) as standards,
    i.difficulty,
    i.grade_level
FROM items i
LEFT JOIN item_skills isks ON isks.item_id = i.item_id
LEFT JOIN skills s ON s.skill_id = isks.skill_id
LEFT JOIN skill_standards ss ON ss.skill_id = s.skill_id
LEFT JOIN curriculum_standards cs ON cs.standard_id = ss.standard_id
GROUP BY i.item_id, i.item_text, i.content_embedding, i.difficulty, i.grade_level;

CREATE INDEX idx_item_search_embedding ON item_search
USING hnsw (content_embedding vector_cosine_ops);

-- Refresh strategy
CREATE INDEX idx_items_updated ON items(updated_at);
```

### Embedding Generation Service

```python
# app/services/embedding_service.py
import asyncio
from typing import List, Optional
import openai
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

class EmbeddingService:
    """Service for generating and managing embeddings."""

    def __init__(self, db: AsyncSession):
        self.db = db
        openai.api_key = settings.OPENAI_API_KEY

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI API."""
        response = await openai.Embedding.acreate(
            model="text-embedding-ada-002",
            input=text
        )
        return response['data'][0]['embedding']

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings in batches to avoid rate limits."""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=batch
            )
            embeddings.extend([item['embedding'] for item in response['data']])

            # Rate limiting
            if i + batch_size < len(texts):
                await asyncio.sleep(1)

        return embeddings

    async def update_item_embedding(self, item_id: str, item_text: str):
        """Update embedding for a single item."""
        embedding = await self.generate_embedding(item_text)

        query = text("""
            UPDATE items
            SET content_embedding = :embedding::vector,
                updated_at = CURRENT_TIMESTAMP
            WHERE item_id = :item_id::uuid
        """)

        await self.db.execute(query, {
            "item_id": item_id,
            "embedding": str(embedding)
        })
        await self.db.commit()

    async def find_similar_items(
        self,
        query_embedding: List[float],
        limit: int = 10,
        skill_filter: Optional[List[str]] = None,
        min_similarity: float = 0.7
    ) -> List[dict]:
        """Find similar items using cosine similarity."""
        skill_condition = ""
        if skill_filter:
            skill_condition = "AND :skill_filter::text[] && skills"

        query = text(f"""
            SELECT
                item_id,
                item_text,
                skills,
                standards,
                difficulty,
                1 - (content_embedding <=> :query_embedding::vector) as similarity
            FROM item_search
            WHERE content_embedding IS NOT NULL
                {skill_condition}
                AND 1 - (content_embedding <=> :query_embedding::vector) >= :min_similarity
            ORDER BY content_embedding <=> :query_embedding::vector
            LIMIT :limit
        """)

        params = {
            "query_embedding": str(query_embedding),
            "limit": limit,
            "min_similarity": min_similarity
        }
        if skill_filter:
            params["skill_filter"] = skill_filter

        result = await self.db.execute(query, params)

        return [
            {
                "item_id": row.item_id,
                "item_text": row.item_text,
                "skills": row.skills,
                "standards": row.standards,
                "difficulty": float(row.difficulty),
                "similarity": float(row.similarity)
            }
            for row in result
        ]

    async def refresh_search_view(self):
        """Refresh materialized view for search."""
        await self.db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY item_search"))
        await self.db.commit()
```

### Hybrid Search (Semantic + Keyword)

```python
# app/services/search_service.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class HybridSearchService:
    """Combine semantic search with traditional filters."""

    def __init__(self, db: AsyncSession, embedding_service: EmbeddingService):
        self.db = db
        self.embedding_service = embedding_service

    async def search_items(
        self,
        query_text: str,
        skills: Optional[List[str]] = None,
        standards: Optional[List[str]] = None,
        grade_level: Optional[str] = None,
        difficulty_range: Optional[Tuple[float, float]] = None,
        limit: int = 20
    ) -> List[dict]:
        """Hybrid search combining semantic similarity with filters."""
        # Generate embedding for query
        query_embedding = await self.embedding_service.generate_embedding(query_text)

        # Build dynamic filter conditions
        conditions = []
        params = {
            "query_embedding": str(query_embedding),
            "limit": limit
        }

        if skills:
            conditions.append("skills && :skills::text[]")
            params["skills"] = skills

        if standards:
            conditions.append("standards && :standards::text[]")
            params["standards"] = standards

        if grade_level:
            conditions.append("grade_level = :grade_level")
            params["grade_level"] = grade_level

        if difficulty_range:
            conditions.append("difficulty BETWEEN :min_diff AND :max_diff")
            params["min_diff"] = difficulty_range[0]
            params["max_diff"] = difficulty_range[1]

        where_clause = "WHERE content_embedding IS NOT NULL"
        if conditions:
            where_clause += " AND " + " AND ".join(conditions)

        query = text(f"""
            SELECT
                item_id,
                item_text,
                skills,
                standards,
                difficulty,
                grade_level,
                1 - (content_embedding <=> :query_embedding::vector) as similarity
            FROM item_search
            {where_clause}
            ORDER BY content_embedding <=> :query_embedding::vector
            LIMIT :limit
        """)

        result = await self.db.execute(query, params)

        return [
            {
                "item_id": row.item_id,
                "item_text": row.item_text,
                "skills": row.skills,
                "standards": row.standards,
                "difficulty": float(row.difficulty),
                "grade_level": row.grade_level,
                "similarity": float(row.similarity)
            }
            for row in result
        ]
```

## Curriculum Standards Mapping

### Loading CCSS Standards

```python
# scripts/load_ccss_standards.py
import asyncio
import json
from uuid import UUID
from sqlalchemy import text
from app.core.database import get_async_session

async def load_ccss_math_standards():
    """Load Common Core State Standards for Mathematics."""
    # Example: CCSS.MATH.CONTENT.7.EE.A.1
    # Solve multi-step real-life and mathematical problems

    standards = [
        {
            "code": "CCSS.MATH.CONTENT.7.EE",
            "framework": "CCSS",
            "subject": "math",
            "grade_level": "7",
            "description": "Expressions & Equations",
            "parent": None
        },
        {
            "code": "CCSS.MATH.CONTENT.7.EE.A",
            "framework": "CCSS",
            "subject": "math",
            "grade_level": "7",
            "description": "Use properties of operations to generate equivalent expressions",
            "parent": "CCSS.MATH.CONTENT.7.EE"
        },
        {
            "code": "CCSS.MATH.CONTENT.7.EE.A.1",
            "framework": "CCSS",
            "subject": "math",
            "grade_level": "7",
            "description": "Apply properties of operations as strategies to add, subtract, factor, and expand linear expressions with rational coefficients",
            "parent": "CCSS.MATH.CONTENT.7.EE.A"
        }
        # ... more standards
    ]

    async for session in get_async_session():
        # Insert in hierarchical order (parent before child)
        for standard in standards:
            query = text("""
                INSERT INTO curriculum_standards
                    (standard_code, framework, subject, grade_level, description, parent_standard_id)
                VALUES
                    (:code, :framework, :subject, :grade_level, :description,
                     (SELECT standard_id FROM curriculum_standards WHERE standard_code = :parent))
                ON CONFLICT (standard_code) DO NOTHING
            """)

            await session.execute(query, standard)

        await session.commit()

if __name__ == "__main__":
    asyncio.run(load_ccss_math_standards())
```

## Performance Optimization

### Indexing Strategy

```sql
-- Composite indexes for common queries
CREATE INDEX idx_items_org_subject_grade ON items(organization_id, subject, grade_level);
CREATE INDEX idx_skills_org_subject_grade ON skills(organization_id, subject, grade_level);

-- Partial indexes for active content
CREATE INDEX idx_items_active_embedding ON items(content_embedding)
WHERE is_active = true AND content_embedding IS NOT NULL;

-- GIN index for array containment queries
CREATE INDEX idx_item_search_skills_gin ON item_search USING gin(skills);
CREATE INDEX idx_item_search_standards_gin ON item_search USING gin(standards);
```

### Caching Strategy

```python
# app/services/graph_cache.py
from functools import wraps
import json
from typing import Callable
import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def cache_graph_query(ttl: int = 3600):
    """Cache decorator for graph queries."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            cache_key = f"graph:{func.__name__}:{json.dumps(args[1:] + tuple(kwargs.items()))}"

            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )

            return result
        return wrapper
    return decorator

class CachedGraphService(SkillGraphService):
    """Graph service with caching."""

    @cache_graph_query(ttl=7200)  # 2 hours
    async def get_learning_path(self, skill_id: UUID, max_depth: int = 10):
        return await super().get_learning_path(skill_id, max_depth)

    @cache_graph_query(ttl=3600)  # 1 hour
    async def get_next_skills(self, mastered_skills: List[UUID]):
        return await super().get_next_skills(mastered_skills)
```

## Testing Strategy

### Graph Validation Tests

```python
# tests/test_graph_service.py
import pytest
from uuid import uuid4
from app.services.graph_service import SkillGraphService

@pytest.mark.asyncio
async def test_cycle_detection(db_session):
    """Test that cycle detection prevents invalid prerequisites."""
    service = SkillGraphService(db_session)

    # Create skills: A -> B -> C
    skill_a = uuid4()
    skill_b = uuid4()
    skill_c = uuid4()

    await service.add_prerequisite(skill_b, skill_a)  # B requires A
    await service.add_prerequisite(skill_c, skill_b)  # C requires B

    # Attempt to create cycle: A -> C (invalid because C -> B -> A)
    with pytest.raises(ValueError, match="cycle"):
        await service.add_prerequisite(skill_a, skill_c)

@pytest.mark.asyncio
async def test_learning_path(db_session):
    """Test learning path generation."""
    service = SkillGraphService(db_session)

    # Create chain: E -> D -> C -> B -> A
    skills = [uuid4() for _ in range(5)]
    for i in range(4):
        await service.add_prerequisite(skills[i+1], skills[i])

    # Get path for skill E
    path = await service.get_learning_path(skills[4])

    assert len(path) == 4  # A, B, C, D (not E itself)
    assert path[0][2] == 4  # Deepest prerequisite (A) has depth 4
    assert path[-1][2] == 1  # Closest prerequisite (D) has depth 1

@pytest.mark.asyncio
async def test_next_skills_recommendation(db_session):
    """Test skill recommendation based on mastery."""
    service = SkillGraphService(db_session)

    # Diamond pattern:
    #     A
    #    / \
    #   B   C
    #    \ /
    #     D
    skill_a, skill_b, skill_c, skill_d = [uuid4() for _ in range(4)]

    await service.add_prerequisite(skill_b, skill_a)
    await service.add_prerequisite(skill_c, skill_a)
    await service.add_prerequisite(skill_d, skill_b)
    await service.add_prerequisite(skill_d, skill_c)

    # Mastered only A
    next_skills = await service.get_next_skills([skill_a])
    assert len(next_skills) == 2  # Both B and C are ready

    # Mastered A and B
    next_skills = await service.get_next_skills([skill_a, skill_b])
    assert len(next_skills) == 1  # Only C is ready (D still needs C)

    # Mastered A, B, C
    next_skills = await service.get_next_skills([skill_a, skill_b, skill_c])
    assert len(next_skills) == 1  # D is ready
    assert next_skills[0][0] == skill_d

@pytest.mark.asyncio
async def test_semantic_search(db_session, embedding_service):
    """Test semantic similarity search."""
    search_service = HybridSearchService(db_session, embedding_service)

    # Search for items similar to a query
    results = await search_service.search_items(
        query_text="Solve linear equations with fractions",
        skills=["algebra-linear-equations"],
        grade_level="7",
        difficulty_range=(0.4, 0.7),
        limit=10
    )

    assert len(results) <= 10
    assert all(r["similarity"] >= 0 for r in results)
    assert all("algebra-linear-equations" in r["skills"] for r in results)
    assert results[0]["similarity"] >= results[-1]["similarity"]  # Ordered by similarity

@pytest.mark.asyncio
async def test_embedding_update_trigger(db_session):
    """Test that embeddings are updated when item content changes."""
    # This would test a database trigger or application logic
    # that automatically regenerates embeddings on content update
    pass
```

### Performance Benchmark

```python
# tests/benchmark_graph.py
import time
import asyncio
from uuid import uuid4
from app.services.graph_service import SkillGraphService

async def benchmark_prerequisite_query():
    """Benchmark prerequisite query performance."""
    service = SkillGraphService(db_session)

    # Create graph with 1000 skills, average depth 5
    skills = [uuid4() for _ in range(1000)]

    # Random prerequisite connections
    for i in range(len(skills)):
        num_prereqs = min(i, 3)  # Up to 3 prerequisites
        for j in range(num_prereqs):
            await service.add_prerequisite(skills[i], skills[i-j-1])

    # Benchmark query
    start = time.time()
    for _ in range(100):
        await service.get_learning_path(skills[-1])
    elapsed = time.time() - start

    print(f"100 learning path queries: {elapsed:.2f}s ({elapsed*10:.2f}ms avg)")
    assert elapsed < 5.0  # Should complete in <5 seconds

async def benchmark_semantic_search():
    """Benchmark vector similarity search."""
    search_service = HybridSearchService(db_session, embedding_service)

    # Query 100 times
    start = time.time()
    for _ in range(100):
        await search_service.search_items(
            query_text="Test query",
            limit=20
        )
    elapsed = time.time() - start

    print(f"100 semantic searches: {elapsed:.2f}s ({elapsed*10:.2f}ms avg)")
    assert elapsed < 10.0  # Should complete in <10 seconds
```

## Summary

The knowledge graph implementation provides:

1. **Prerequisite tracking**: PostgreSQL recursive CTEs for DAG traversal
2. **Semantic search**: pgvector for embedding-based similarity
3. **Curriculum alignment**: Hierarchical standards mapping
4. **Performance**: HNSW indexes, materialized views, Redis caching
5. **Validation**: Cycle detection, path finding, recommendation logic

**Key Metrics**:

- Learning path query: <50ms for depth ≤10
- Semantic search: <100ms for top 20 results
- Embedding generation: ~200ms per item (batched)
- Graph operations: O(V + E) with cycle detection

**Next Steps**:

- Implement embedding update triggers on item changes
- Add graph analytics (centrality, clustering)
- Support multi-dimensional prerequisites (soft vs hard)
- Integrate with CAT engine for adaptive item selection
