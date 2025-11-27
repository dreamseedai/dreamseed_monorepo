# Item Models Implementation Summary

**Date**: 2025-01-20  
**Status**: ✅ Complete - All tests passing (54/54)

## Overview

Added comprehensive Item bank infrastructure with IRT parameters for Adaptive Testing (CAT). This completes the adaptive testing system alongside the existing IRT engine and classes router.

## What Was Implemented

### 1. Item Models (`backend/app/models/item.py`)

Four new models for managing test items and item pools:

#### `Item` Model
- **Purpose**: Store questions with IRT parameters for adaptive testing
- **IRT Parameters** (3PL Model):
  - `a`: Discrimination (0.5-2.5 typical) - How well item distinguishes ability levels
  - `b`: Difficulty (-3 to +3 typical) - Item difficulty on theta scale
  - `c`: Guessing (0-0.3 typical) - Probability of guessing correctly
- **Content Fields**:
  - `question_text`: The question
  - `correct_answer`: For auto-grading
  - `explanation`: Solution explanation
  - `topic`: Subject area (algebra, geometry, etc.)
  - `meta`: JSONB for tags, standards, question type
- **Key Method**: `to_engine_format()` - Converts to AdaptiveEngine format
- **Relationships**: 
  - `attempts`: Many-to-one with Attempt (track responses)
  - `choices`: One-to-many with ItemChoice (multiple choice options)

#### `ItemChoice` Model
- **Purpose**: Multiple choice options for items
- **Fields**:
  - `item_id`: FK to Item (CASCADE delete)
  - `choice_num`: 1, 2, 3, 4, 5
  - `choice_text`: The choice text
  - `is_correct`: 0 or 1 (boolean)
- **Constraint**: Unique (item_id, choice_num)

#### `ItemPool` Model
- **Purpose**: Organize items into named collections
- **Fields**:
  - `name`: Unique name ("Grade 8 Math Diagnostic")
  - `description`: Pool description
  - `subject`: Subject area (math, english, science)
  - `grade_level`: Grade level (8, K, 12)
  - `meta`: JSONB for pool configuration (max_items, time_limit, etc.)
- **Relationships**: `items` - Many-to-many via ItemPoolMembership

#### `ItemPoolMembership` Model
- **Purpose**: N:N junction table with metadata
- **Fields**:
  - `item_id`: FK to Item (CASCADE delete)
  - `pool_id`: FK to ItemPool (CASCADE delete)
  - `sequence`: Optional ordering
  - `weight`: Item weight (default 1.0)
- **Primary Key**: Composite (item_id, pool_id)

### 2. Database Migration (`migrations/20251120_item_tables_irt_cat.sql`)

Created 4 tables with proper constraints:

```sql
-- Items table with IRT parameters
CREATE TABLE items (
    id BIGSERIAL PRIMARY KEY,
    topic VARCHAR(255),
    question_text TEXT NOT NULL,
    correct_answer TEXT,
    explanation TEXT,
    a NUMERIC(6,3) NOT NULL,  -- Discrimination
    b NUMERIC(6,3) NOT NULL,  -- Difficulty
    c NUMERIC(6,3) NOT NULL,  -- Guessing
    meta JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_items_topic ON items(topic);
CREATE INDEX idx_items_difficulty ON items(b);

-- Item choices (CASCADE delete)
CREATE TABLE item_choices (
    id BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    choice_num INTEGER NOT NULL,
    choice_text TEXT NOT NULL,
    is_correct INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_item_choices_item_id ON item_choices(item_id);
CREATE UNIQUE INDEX idx_item_choices_unique ON item_choices(item_id, choice_num);

-- Item pools
CREATE TABLE item_pools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    subject VARCHAR(100),
    grade_level VARCHAR(20),
    meta JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_item_pools_subject ON item_pools(subject);
CREATE INDEX idx_item_pools_grade ON item_pools(grade_level);

-- Item pool membership (N:N junction)
CREATE TABLE item_pool_membership (
    item_id BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    pool_id INTEGER NOT NULL REFERENCES item_pools(id) ON DELETE CASCADE,
    sequence INTEGER,
    weight NUMERIC(5,2) DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (item_id, pool_id)
);
CREATE INDEX idx_item_pool_membership_pool_id ON item_pool_membership(pool_id);
CREATE INDEX idx_item_pool_membership_sequence ON item_pool_membership(pool_id, sequence);

-- Update attempts table to add FK constraint
ALTER TABLE attempts
ADD CONSTRAINT fk_attempts_item_id 
FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE SET NULL;
```

**Features**:
- ✅ Proper FK constraints with CASCADE/SET NULL
- ✅ Indexes on topic, difficulty, item_id, pool_id, sequence
- ✅ UNIQUE constraint on choice_num per item
- ✅ UNIQUE constraint on pool name
- ✅ Comments on all tables and key columns
- ✅ Sample data included (commented out)

### 3. Model Integration

Updated `backend/app/models/core_entities.py`:

```python
# Added FK constraint to item_id
item_id = Column(
    BigInteger, 
    ForeignKey("items.id", ondelete="SET NULL"), 
    nullable=True, 
    index=True
)

# Added relationship to Item
item = relationship("Item", back_populates="attempts")
```

Updated `backend/app/models/__init__.py`:

```python
from .item import (
    Item,
    ItemChoice,
    ItemPool,
    ItemPoolMembership,
)

__all__ = [
    # ... existing models ...
    "Item",
    "ItemChoice",
    "ItemPool",
    "ItemPoolMembership",
]
```

### 4. Test Suite (`backend/tests/test_item_models.py`)

17 comprehensive tests covering all functionality:

**Basic Model Tests** (5 tests):
- ✅ `test_item_creation` - Create Item with IRT parameters
- ✅ `test_item_to_engine_format` - Convert to AdaptiveEngine format
- ✅ `test_item_choice_creation` - Create ItemChoice
- ✅ `test_item_pool_creation` - Create ItemPool
- ✅ `test_item_pool_membership_creation` - Create membership

**Parameter Validation** (1 test):
- ✅ `test_item_irt_parameter_ranges` - Validate a, b, c ranges

**String Representations** (3 tests):
- ✅ `test_item_repr` - Item string
- ✅ `test_item_choice_repr` - Choice string
- ✅ `test_item_pool_repr` - Pool string

**Advanced Features** (8 tests):
- ✅ `test_multiple_choices_for_item` - 4 choices, 1 correct
- ✅ `test_item_metadata` - JSONB tags, standards
- ✅ `test_item_pool_metadata` - Pool config (max_items, time_limit)
- ✅ `test_easy_item` - Negative b parameter
- ✅ `test_hard_item` - Positive b parameter
- ✅ `test_high_discrimination_item` - High a parameter
- ✅ `test_low_guessing_item` - Zero c parameter
- ✅ `test_pool_membership_with_weight` - Weighted items

## Test Results

```bash
$ pytest tests/test_exam_engine.py tests/test_classes_router.py tests/test_item_models.py -v

✅ 54 passed in 0.51s

Breakdown:
- 27 IRT/CAT engine tests ✅
- 10 Classes router tests ✅
- 17 Item model tests ✅
```

## Usage Examples

### Create an Item

```python
from app.models import Item, ItemChoice

# Create item with IRT parameters
item = Item(
    topic="algebra",
    question_text="Solve for x: 2x + 5 = 13",
    correct_answer="4",
    explanation="Subtract 5 from both sides: 2x = 8. Then divide by 2: x = 4",
    a=1.2,   # Good discrimination
    b=0.5,   # Medium difficulty
    c=0.2,   # Low guessing
    meta={
        "tags": ["linear_equations", "single_variable"],
        "standards": ["CCSS.MATH.8.EE.C.7"],
        "question_type": "multiple_choice"
    }
)

# Add multiple choice options
choices = [
    ItemChoice(item_id=item.id, choice_num=1, choice_text="2", is_correct=0),
    ItemChoice(item_id=item.id, choice_num=2, choice_text="4", is_correct=1),
    ItemChoice(item_id=item.id, choice_num=3, choice_text="8", is_correct=0),
    ItemChoice(item_id=item.id, choice_num=4, choice_text="12", is_correct=0),
]
```

### Convert to Engine Format

```python
# Get item from database
item = db.query(Item).filter_by(id=123).first()

# Convert to format expected by AdaptiveEngine
engine_format = item.to_engine_format()
# Returns: {"id": 123, "a": 1.2, "b": 0.5, "c": 0.2}

# Use with AdaptiveEngine
from app.core.services.exam_engine import AdaptiveEngine

engine = AdaptiveEngine(initial_theta=0.0)
available_items = [item.to_engine_format() for item in db.query(Item).all()]
next_item = engine.pick_item(available_items)
```

### Create Item Pool

```python
from app.models import ItemPool, ItemPoolMembership

# Create pool
pool = ItemPool(
    name="Grade 8 Math Diagnostic",
    description="Diagnostic assessment for 8th grade math",
    subject="math",
    grade_level="8",
    meta={
        "max_items": 20,
        "time_limit_minutes": 45,
        "difficulty_range": [-2, 2]
    }
)

# Add items to pool with weights
membership = ItemPoolMembership(
    item_id=item.id,
    pool_id=pool.id,
    sequence=1,
    weight=1.5  # Higher weight for this item
)
```

### Access Item from Attempt

```python
# Query attempt with item
attempt = db.query(Attempt).filter_by(id=1).first()

# Access item and IRT parameters
item = attempt.item
print(f"Item difficulty: {item.b}")
print(f"Item discrimination: {item.a}")
print(f"Question: {item.question_text}")
print(f"Explanation: {item.explanation}")
```

## Integration with AdaptiveEngine

The Item models integrate seamlessly with the existing `AdaptiveEngine`:

```python
def select_next_item_from_db(
    db: Session,
    exam_session_id: int,
    engine: AdaptiveEngine
) -> Item:
    """
    Select next item using AdaptiveEngine and database.
    
    Returns:
        Item object with full details (question_text, choices, etc.)
    """
    # Get items already attempted
    used_ids = (
        db.query(Attempt.item_id)
        .filter(Attempt.exam_session_id == exam_session_id)
        .all()
    )
    used_ids = [id[0] for id in used_ids if id[0] is not None]
    
    # Get available items
    available_items = (
        db.query(Item)
        .filter(~Item.id.in_(used_ids))
        .all()
    )
    
    # Convert to engine format
    items_dict = [item.to_engine_format() for item in available_items]
    
    # Let engine select based on IRT
    selected = engine.pick_item(items_dict)
    
    # Return full Item object
    return db.query(Item).filter(Item.id == selected["id"]).first()
```

## Database Schema

Entity Relationship Diagram:

```
┌─────────────────┐         ┌─────────────────┐
│   ItemPool      │◄────┬───┤ ItemPoolMember  │
│                 │     │   │  ship           │
│ • id (PK)       │     │   │ • item_id (PK)  │
│ • name (UNIQUE) │     │   │ • pool_id (PK)  │
│ • subject       │     │   │ • sequence      │
│ • grade_level   │     │   │ • weight        │
│ • meta          │     │   └─────────────────┘
└─────────────────┘     │            │
                        │            │
                        │            ▼
                        │   ┌─────────────────┐
                        └──►│   Item          │
                            │                 │
                            │ • id (PK)       │
                            │ • topic         │
                            │ • question_text │
                            │ • a (IRT)       │◄──┐
                            │ • b (IRT)       │   │
                            │ • c (IRT)       │   │
                            │ • meta          │   │
                            └─────────────────┘   │
                                     │            │
                                     │            │
                                     ▼            │
                            ┌─────────────────┐   │
                            │  ItemChoice     │   │
                            │                 │   │
                            │ • id (PK)       │   │
                            │ • item_id (FK)  │   │
                            │ • choice_num    │   │
                            │ • choice_text   │   │
                            │ • is_correct    │   │
                            └─────────────────┘   │
                                                  │
                            ┌─────────────────┐   │
                            │   Attempt       │   │
                            │                 │   │
                            │ • id (PK)       │   │
                            │ • item_id (FK)  │───┘
                            │ • student_id    │
                            │ • exam_session  │
                            │ • correct       │
                            │ • response_time │
                            └─────────────────┘
```

## Next Steps

### 1. Apply Migration (HIGH PRIORITY)

```bash
# Apply migration to create tables
psql -U postgres -d dreamseed < migrations/20251120_item_tables_irt_cat.sql

# Verify tables created
psql -U postgres -d dreamseed -c "\dt items*"
```

### 2. Seed Sample Items (RECOMMENDED)

```bash
# Uncomment sample data in migration SQL and re-run
# Or create seed script with 20-30 items across difficulty levels
```

### 3. Create Items Management API (NEXT)

Endpoints to create:
- `POST /api/items` - Create new item with IRT parameters
- `GET /api/items` - List items (filter by topic, difficulty range)
- `GET /api/items/{id}` - Get item details
- `PUT /api/items/{id}` - Update item
- `POST /api/items/{id}/choices` - Add multiple choices
- `GET /api/pools` - List item pools
- `POST /api/pools` - Create pool
- `POST /api/pools/{id}/items` - Add items to pool

### 4. Integrate with Exam Router (IMPORTANT)

Update exam router to use Item database:

```python
# In app/api/routers/exams.py

@router.get("/exams/{exam_id}/next-item")
def get_next_item(exam_id: int, db: Session, current_user: dict):
    # Get exam session
    session = db.query(ExamSession).filter_by(id=exam_id).first()
    
    # Initialize engine with current theta
    engine = AdaptiveEngine(initial_theta=session.theta or 0.0)
    
    # Restore engine state from previous attempts
    attempts = db.query(Attempt).filter_by(exam_session_id=exam_id).all()
    for attempt in attempts:
        engine.record_attempt(
            params=attempt.item.to_engine_format(),
            correct=attempt.correct
        )
    
    # Select next item
    next_item = select_next_item_from_db(db, exam_id, engine)
    
    return {
        "item_id": next_item.id,
        "question_text": next_item.question_text,
        "choices": [
            {"num": c.choice_num, "text": c.choice_text}
            for c in next_item.choices
        ]
    }
```

### 5. Analytics & Calibration (FUTURE)

- Track item usage statistics
- Compare theoretical vs empirical difficulty
- Run IRT parameter estimation (EM algorithm)
- Update parameters based on response data

## Files Modified/Created

### Created:
1. `backend/app/models/item.py` (180 lines) - Item models
2. `migrations/20251120_item_tables_irt_cat.sql` (150 lines) - Database schema
3. `backend/tests/test_item_models.py` (180 lines) - Test suite
4. `backend/ITEM_MODELS_IMPLEMENTATION.md` (this file) - Documentation

### Modified:
1. `backend/app/models/core_entities.py` - Added Item FK and relationship to Attempt
2. `backend/app/models/__init__.py` - Added Item model exports

## Summary

The Item models complete the adaptive testing infrastructure:

✅ **Phase 1** - Schema Verification (INTEGER-based core entities)  
✅ **Phase 2** - Classes Router (3 endpoints, 10 tests)  
✅ **Phase 3** - IRT/CAT Engine (3PL model, 27 tests)  
✅ **Phase 4** - Item Models (4 models, 17 tests) ← **CURRENT**

**Total Test Coverage**: 54 tests passing
- IRT Engine: 27 tests ✅
- Classes Router: 10 tests ✅
- Item Models: 17 tests ✅

**System Ready For**:
1. Item creation and management via API
2. Pool-based item selection
3. Full adaptive testing with database-backed items
4. IRT parameter calibration
5. Item analytics and reporting

The system now has a complete adaptive testing infrastructure with:
- Robust IRT/CAT algorithm
- Teacher dashboard APIs
- Flexible item bank with IRT parameters
- Multiple choice support
- Item pooling and organization
- Full test coverage
