"""
Questions API - PostgreSQL Integration
Serving 18894 questions from mpcstudy database
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Questions"])


class Question(BaseModel):
    id: int
    title: str
    difficulty: Optional[str] = None
    category: Optional[str] = None
    que_class: Optional[str] = None
    que_grade: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class QuestionCreate(BaseModel):
    title: str
    stem: str = ""
    difficulty: str = "1"
    topic: str = "수학"
    explanation: str = ""
    hint: str = ""
    resource: str = ""
    answer_text: str = ""
    options: List[str] = []
    answer: int = 0
    tags: List[str] = []


class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    stem: Optional[str] = None
    difficulty: Optional[str] = None
    topic: Optional[str] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    resource: Optional[str] = None
    answer_text: Optional[str] = None
    options: Optional[List[str]] = None
    answer: Optional[int] = None
    tags: Optional[List[str]] = None


class QuestionsResponse(BaseModel):
    results: List[Question]
    total: int
    page: int
    page_size: int


@router.get("/questions", response_model=QuestionsResponse)
async def get_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    q: Optional[str] = None,
    difficulty: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = Query("id", regex="^(id|created_at|updated_at|difficulty)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of questions from PostgreSQL problems table
    Total: 18894 questions from mpcstudy database
    """
    logger.info(f"GET /admin/questions page={page} page_size={page_size} q={q}")
    
    # Build WHERE clause
    where_clauses = []
    params = {}
    
    if q:
        # Try to parse as integer for ID search
        try:
            q_int = int(q)
            where_clauses.append("(id = :q_int OR title ILIKE :q OR category ILIKE :q)")
            params["q_int"] = q_int
            params["q"] = f"%{q}%"
        except ValueError:
            # Not a number, search only text fields
            where_clauses.append("(title ILIKE :q OR category ILIKE :q)")
            params["q"] = f"%{q}%"
    
    if difficulty:
        where_clauses.append("difficulty = :difficulty")
        params["difficulty"] = difficulty
    
    if category:
        where_clauses.append("category ILIKE :category")
        params["category"] = f"%{category}%"
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Count total
    count_query = f"SELECT COUNT(*) as total FROM problems WHERE {where_sql}"
    total_result = db.execute(text(count_query), params).fetchone()
    total = total_result[0] if total_result else 0
    
    # Fetch paginated results
    offset = (page - 1) * page_size
    query = f"""
        SELECT 
            id,
            title,
            difficulty,
            category,
            mysql_metadata->>'que_class' as que_class,
            mysql_metadata->>'que_grade' as que_grade,
            created_at,
            updated_at
        FROM problems 
        WHERE {where_sql}
        ORDER BY {sort_by} {order.upper()}
        LIMIT :limit OFFSET :offset
    """
    params.update({"limit": page_size, "offset": offset})
    
    result = db.execute(text(query), params)
    rows = result.fetchall()
    
    questions = [
        Question(
            id=row[0],
            title=row[1] or "",
            difficulty=row[2],
            category=row[3],
            que_class=row[4],
            que_grade=row[5],
            created_at=row[6].isoformat() if row[6] else None,
            updated_at=row[7].isoformat() if row[7] else None
        )
        for row in rows
    ]
    
    return QuestionsResponse(
        results=questions,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/questions/{question_id}")
async def get_question(question_id: int, db: Session = Depends(get_db)):
    """
    Get single question by ID from PostgreSQL
    """
    logger.info(f"GET /admin/questions/{question_id}")
    
    query = text("""
        SELECT 
            id, title, description, difficulty, category,
            mysql_metadata, created_at, updated_at
        FROM problems 
        WHERE id = :id
    """)
    
    result = db.execute(query, {"id": question_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    
    metadata = result[5] or {}
    
    # Fallback: use que_en_solution from legacy data if explanation is empty
    explanation = metadata.get('explanation', '') or metadata.get('que_en_solution', '')
    
    return {
        "id": result[0],
        "title": result[1],
        "stem": result[2] or "",
        "difficulty": result[3],
        "topic": result[4],
        "explanation": explanation,
        "hint": metadata.get('hint', ''),
        "resource": metadata.get('resource', ''),
        "answer_text": metadata.get('answer_text', ''),
        "options": metadata.get('options', []),
        "answer": metadata.get('answer', 0),
        "tags": metadata.get('tags', []),
        "created_at": result[6].isoformat() if result[6] else None,
        "updated_at": result[7].isoformat() if result[7] else None
    }


@router.post("/questions")
async def create_question(data: QuestionCreate, db: Session = Depends(get_db)):
    """
    Create a new question in PostgreSQL
    """
    logger.info(f"POST /admin/questions title={data.title}")
    
    try:
        # Get next mysql_id
        max_id_query = text("""
            SELECT COALESCE(MAX((mysql_metadata->>'mysql_id')::int), 18898) + 1 AS next_id
            FROM problems
            WHERE mysql_metadata ? 'mysql_id'
        """)
        next_id = db.execute(max_id_query).scalar()
        logger.info(f"Next mysql_id: {next_id}")
        
        # Build metadata JSONB with all additional fields
        import json
        import uuid
        metadata = {
            'mysql_id': next_id,
            'explanation': data.explanation or '',
            'hint': data.hint or '',
            'resource': data.resource or '',
            'answer_text': data.answer_text or '',
            'options': data.options or [],
            'answer': data.answer if data.answer is not None else 0,
            'tags': data.tags or []
        }
        
        insert_query = text("""
            INSERT INTO problems (uuid_legacy, title, description, difficulty, category, mysql_metadata, created_at, updated_at)
            VALUES (:uuid, :title, :description, :difficulty, :category, 
                    CAST(:metadata AS jsonb), NOW(), NOW())
            RETURNING id, title, description, difficulty, category, mysql_metadata, created_at, updated_at
        """)
        
        params = {
            "uuid": str(uuid.uuid4()),
            "title": data.title,
            "description": data.stem,
            "difficulty": data.difficulty,
            "category": data.topic,
            "metadata": json.dumps(metadata)
        }
        logger.info(f"Insert params: {params}")
        
        result = db.execute(insert_query, params)
        db.commit()
        
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create question")
        
        stored_metadata = row[5] or {}
        
        return {
            "id": row[0],
            "title": row[1],
            "stem": row[2] or "",
            "difficulty": row[3],
            "topic": row[4],
            "explanation": stored_metadata.get('explanation', ''),
            "hint": stored_metadata.get('hint', ''),
            "resource": stored_metadata.get('resource', ''),
            "answer_text": stored_metadata.get('answer_text', ''),
            "options": stored_metadata.get('options', []),
            "answer": stored_metadata.get('answer', 0),
            "tags": stored_metadata.get('tags', []),
            "created_at": row[6].isoformat() if row[6] else None,
            "updated_at": row[7].isoformat() if row[7] else None
        }
    except Exception as e:
        logger.error(f"Error creating question: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/questions/{question_id}")
async def update_question(question_id: int, data: QuestionUpdate, db: Session = Depends(get_db)):
    """
    Update a question in PostgreSQL
    Store additional fields in mysql_metadata JSONB
    """
    logger.info(f"PUT /admin/questions/{question_id}")
    
    # Build update query dynamically
    updates = []
    params: dict = {"id": question_id}
    
    # Main table fields
    if data.title is not None:
        updates.append("title = :title")
        params["title"] = data.title
    
    if data.stem is not None:
        updates.append("description = :description")
        params["description"] = data.stem
    
    if data.difficulty is not None:
        updates.append("difficulty = :difficulty")
        params["difficulty"] = data.difficulty
    
    if data.topic is not None:
        updates.append("category = :category")
        params["category"] = data.topic
    
    # Additional fields in mysql_metadata JSONB
    metadata_fields = {}
    if hasattr(data, 'explanation') and data.explanation is not None:
        metadata_fields['explanation'] = data.explanation
    if hasattr(data, 'hint') and data.hint is not None:
        metadata_fields['hint'] = data.hint
    if hasattr(data, 'resource') and data.resource is not None:
        metadata_fields['resource'] = data.resource
    if hasattr(data, 'answer_text') and data.answer_text is not None:
        metadata_fields['answer_text'] = data.answer_text
    if hasattr(data, 'options') and data.options is not None:
        metadata_fields['options'] = data.options
    if hasattr(data, 'answer') and data.answer is not None:
        metadata_fields['answer'] = data.answer
    if hasattr(data, 'tags') and data.tags is not None:
        metadata_fields['tags'] = data.tags
    
    if metadata_fields:
        import json
        updates.append("mysql_metadata = mysql_metadata || CAST(:metadata AS jsonb)")
        params["metadata"] = json.dumps(metadata_fields)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    updates.append("updated_at = NOW()")
    
    update_query = text(f"""
        UPDATE problems 
        SET {', '.join(updates)}
        WHERE id = :id
        RETURNING id, title, description, difficulty, category, mysql_metadata, created_at, updated_at
    """)
    
    result = db.execute(update_query, params)
    db.commit()
    
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Question not found")
    
    metadata = row[5] or {}
    
    return {
        "id": row[0],
        "title": row[1],
        "stem": row[2] or "",
        "difficulty": row[3],
        "topic": row[4],
        "explanation": metadata.get('explanation', ''),
        "hint": metadata.get('hint', ''),
        "resource": metadata.get('resource', ''),
        "answer_text": metadata.get('answer_text', ''),
        "options": metadata.get('options', []),
        "answer": metadata.get('answer', 0),
        "tags": metadata.get('tags', []),
        "created_at": row[6].isoformat() if row[6] else None,
        "updated_at": row[7].isoformat() if row[7] else None
    }


@router.delete("/questions/{question_id}")
async def delete_question(question_id: int, db: Session = Depends(get_db)):
    """
    Delete a question from PostgreSQL
    """
    logger.info(f"DELETE /admin/questions/{question_id}")
    
    delete_query = text("DELETE FROM problems WHERE id = :id RETURNING id")
    result = db.execute(delete_query, {"id": question_id})
    db.commit()
    
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question deleted successfully", "id": row[0]}


class TopicResponse(BaseModel):
    id: int
    name: str
    org_id: Optional[int] = None
    parent_topic_id: Optional[int] = None


@router.get("/topics", response_model=List[TopicResponse])
def get_topics(
    subject: Optional[str] = Query(None),
    org_id: Optional[int] = Query(None),
    include_global: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """
    토픽 목록 조회
    - subject: 과목 필터 (선택)
    - org_id: 조직 ID 필터 (선택)
    - include_global: 전역 토픽 포함 여부 (선택)
    """
    query = text("""
        SELECT id, name, org_id, parent_topic_id
        FROM topics
        WHERE 1=1
        ORDER BY id
        LIMIT 100
    """)
    
    try:
        result = db.execute(query)
        topics = []
        for row in result:
            topics.append({
                "id": row[0],
                "name": row[1],
                "org_id": row[2] if len(row) > 2 else None,
                "parent_topic_id": row[3] if len(row) > 3 else None
            })
        return topics
    except Exception as e:
        logger.warning(f"Topics table not found or error: {e}")
        # Fallback: 기본 토픽 목록 반환
        return [
            {"id": 1, "name": "수학", "org_id": None, "parent_topic_id": None},
            {"id": 2, "name": "물리", "org_id": None, "parent_topic_id": None},
            {"id": 3, "name": "화학", "org_id": None, "parent_topic_id": None},
            {"id": 4, "name": "생명과학", "org_id": None, "parent_topic_id": None},
            {"id": 5, "name": "지구과학", "org_id": None, "parent_topic_id": None},
        ]


@router.get("/questions/topics")
def get_topics_legacy(db: Session = Depends(get_db)):
    """
    레거시 토픽 엔드포인트 - 문자열 배열 반환
    """
    query = text("""
        SELECT id, name
        FROM topics
        ORDER BY id
        LIMIT 100
    """)
    
    try:
        result = db.execute(query)
        return [row[1] for row in result]
    except Exception as e:
        logger.warning(f"Topics table not found or error: {e}")
        return ["수학", "물리", "화학", "생명과학", "지구과학"]

