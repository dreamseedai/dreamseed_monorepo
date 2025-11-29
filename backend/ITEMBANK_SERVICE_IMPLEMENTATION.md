# ItemBank Service Implementation Summary

## Overview

Implemented a centralized item selection service for adaptive testing, providing sophisticated item selection logic based on IRT (Item Response Theory) and CAT (Computerized Adaptive Testing) principles.

**Status**: ✅ **COMPLETE** - All 17 tests passing

---

## Files Created

### 1. Service Implementation
**File**: `backend/app/core/services/item_bank.py` (442 lines)

**Class**: `ItemBankService`

**Methods**:
```python
class ItemBankService:
    def __init__(self, session: Session)
    
    # Core pipeline methods
    def load_unattempted_items(exam_session_id, subject, topic) -> List[Item]
    def filter_by_difficulty(items, theta, window=1.0) -> List[Dict]
    def rank_by_information(theta, items) -> List[Dict]
    def get_candidate_items(exam_session_id, theta, subject, topic, window) -> List[Dict]
    def pick_best_item(ranked_items) -> Optional[Dict]
    
    # Future enhancement methods (placeholders)
    def apply_exposure_control(ranked_items, max_exposure) -> List[Dict]
    def apply_content_constraints(ranked_items, distributions) -> List[Dict]
```

### 2. Test Suite
**File**: `backend/tests/test_item_bank.py` (412 lines)

**Test Coverage**: 17 tests across 6 categories:
- Load unattempted items (3 tests)
- Difficulty window filtering (4 tests)
- Information-based ranking (3 tests)
- Combined candidate selection (3 tests)
- Pick best item (3 tests)
- Service initialization (1 test)

---

## Algorithm & Design

### Selection Pipeline

```
1. Load Unattempted Items
   ↓ Query DB excluding items in attempts table for session
   ↓ Optional: Filter by subject/topic
   
2. Difficulty Window Filter
   ↓ Keep items where |b - theta| ≤ window (default: 1.0)
   ↓ Fallback: Use all items if window too restrictive
   
3. Rank by Fisher Information
   ↓ Calculate I(θ) = a²P(θ)Q(θ) / [c + (1-c)P(θ)]²
   ↓ Sort descending (highest information first)
   
4. Pick Best Item
   ↓ Return item with maximum information
   
Result: Optimal item for reducing SE(θ)
```

### Key Concepts

**Difficulty Window (b parameter)**:
- `b` = difficulty in logits on the same scale as `theta`
- `|b - theta| ≤ window` focuses selection near student ability
- Default window = 1.0 logit (reasonable range)
- Smaller window = more focused selection
- Larger window = more variety

**Fisher Information**:
- Measures precision gain from administering an item
- Higher information = better measurement at current theta
- Maximum information when `theta ≈ b` and `a` is high
- Formula: `I(θ) = a²P(θ)Q(θ) / [c + (1-c)P(θ)]²`

**Fallback Logic**:
- If difficulty filter returns 0 items, use all unattempted items
- Prevents deadlock when window too restrictive
- Ensures exam can always continue

---

## Integration with Adaptive Exam Router

### Before (Inline Selection)
```python
# In adaptive_exam.py GET /api/adaptive/next
query = db.query(Item)
if attempted_ids:
    query = query.filter(~Item.id.in_(attempted_ids))
items = query.all()
candidate_items = [item.to_engine_format() for item in items]
next_item_dict = engine.pick_item(candidate_items)
```

### After (Using ItemBank)
```python
# In adaptive_exam.py GET /api/adaptive/next
from app.core.services.item_bank import ItemBankService

bank = ItemBankService(db)
candidates = bank.get_candidate_items(
    exam_session_id=exam_session.id,
    theta=float(exam_session.theta or 0.0),
    subject=exam_session.meta.get("subject"),  # Optional
    window=1.5  # Configurable
)
next_item_dict = bank.pick_best_item(candidates)
```

**Benefits**:
- ✅ Cleaner code (separation of concerns)
- ✅ Difficulty-based filtering (focuses on relevant items)
- ✅ Better item selection (maximum information criterion)
- ✅ Testable (mocked database in unit tests)
- ✅ Extensible (exposure control, content balancing ready)

---

## Test Results

### All Tests Passing ✅
```bash
$ pytest tests/test_item_bank.py -v

tests/test_item_bank.py::test_load_unattempted_items_no_attempts PASSED
tests/test_item_bank.py::test_load_unattempted_items_with_attempts PASSED
tests/test_item_bank.py::test_load_unattempted_items_with_topic_filter PASSED
tests/test_item_bank.py::test_filter_by_difficulty_within_window PASSED
tests/test_item_bank.py::test_filter_by_difficulty_narrow_window PASSED
tests/test_item_bank.py::test_filter_by_difficulty_high_theta PASSED
tests/test_item_bank.py::test_filter_by_difficulty_returns_dicts PASSED
tests/test_item_bank.py::test_rank_by_information PASSED
tests/test_item_bank.py::test_rank_by_information_includes_info PASSED
tests/test_item_bank.py::test_rank_by_information_sorted_descending PASSED
tests/test_item_bank.py::test_get_candidate_items_full_pipeline PASSED
tests/test_item_bank.py::test_get_candidate_items_fallback_when_no_match PASSED
tests/test_item_bank.py::test_get_candidate_items_empty_when_all_attempted PASSED
tests/test_item_bank.py::test_pick_best_item_returns_first PASSED
tests/test_item_bank.py::test_pick_best_item_returns_none_when_empty PASSED
tests/test_item_bank.py::test_pick_best_item_single_item PASSED
tests/test_item_bank.py::test_item_bank_service_initialization PASSED

17 passed, 1 skipped in 0.31s
```

### Full Adaptive Testing Suite ✅
```bash
$ pytest tests/test_exam_engine.py tests/test_classes_router.py \
         tests/test_item_models.py tests/test_adaptive_exam_router.py \
         tests/test_item_bank.py -v

86 passed, 5 skipped in 0.90s
```

**Breakdown**:
- 27 IRT Engine tests ✅
- 10 Classes Router tests ✅
- 17 Item Models tests ✅
- 15 Adaptive Exam Router tests ✅
- 17 ItemBank Service tests ✅

---

## Usage Examples

### Basic Usage
```python
from app.core.services.item_bank import ItemBankService
from app.core.database import SessionLocal

# Initialize service
db = SessionLocal()
bank = ItemBankService(db)

# Get candidate items for exam session
candidates = bank.get_candidate_items(
    exam_session_id=123,
    theta=0.5
)

# Pick best item
next_item = bank.pick_best_item(candidates)
print(f"Next item ID: {next_item['id']}")
print(f"Fisher info: {next_item['info']:.3f}")
```

### With Subject/Topic Filtering
```python
# Filter by subject and topic
candidates = bank.get_candidate_items(
    exam_session_id=123,
    theta=0.5,
    subject="math",
    topic="algebra",
    window=1.5  # Wider difficulty window
)
```

### Integration with AdaptiveEngine
```python
from app.core.services.exam_engine import AdaptiveEngine
from app.core.services.item_bank import ItemBankService

# Initialize
engine = AdaptiveEngine(initial_theta=0.0)
bank = ItemBankService(db)

# Adaptive testing loop
while not engine.should_stop():
    # Get current state
    state = engine.get_state()
    
    # Select next item
    candidates = bank.get_candidate_items(
        exam_session_id=exam_id,
        theta=state["theta"]
    )
    next_item = bank.pick_best_item(candidates)
    
    if not next_item:
        break  # No more items
    
    # Present item, get response...
    is_correct = present_item_and_get_response(next_item)
    
    # Update engine
    engine.record_attempt(next_item, is_correct)
```

---

## Future Enhancements

### 1. Exposure Control
**Purpose**: Prevent item overuse

**Implementation**:
```python
def apply_exposure_control(self, ranked_items, max_exposure=0.25):
    """Keep items below exposure rate threshold"""
    total_exams = self.session.query(ExamSession).count()
    filtered = []
    for item_dict in ranked_items:
        item = self.session.query(Item).get(item_dict["id"])
        exposure_rate = item.exposure_count / total_exams
        if exposure_rate < max_exposure:
            filtered.append(item_dict)
    return filtered
```

**Database Changes**:
```python
# Add to Item model
exposure_count = Column(Integer, default=0)

# Increment on use
item.exposure_count += 1
```

### 2. Content Balancing
**Purpose**: Ensure topic distribution

**Implementation**:
```python
def apply_content_constraints(self, ranked_items, target_dist, current_dist):
    """Prefer under-represented topics"""
    scored = []
    for item in ranked_items:
        topic = item.get("topic")
        target_ratio = target_dist.get(topic, 0)
        current_ratio = current_dist.get(topic, 0) / sum(current_dist.values())
        
        # Score higher if under-represented
        content_score = max(0, target_ratio - current_ratio)
        scored.append((item, content_score))
    
    # Sort by combined info + content score
    scored.sort(key=lambda x: x[0]["info"] * (1 + x[1]), reverse=True)
    return [item for item, _ in scored]
```

**Usage**:
```python
exam_session.meta = {
    "target_distribution": {"algebra": 0.5, "geometry": 0.3, "calculus": 0.2}
}
```

### 3. Configuration System
```python
# Add to ExamSession or system config
ITEM_SELECTION_CONFIG = {
    "default_window": 1.5,
    "min_window": 0.5,
    "max_exposure": 0.25,
    "enable_content_balancing": True,
    "enable_exposure_control": True
}
```

### 4. Performance Optimization
- **Cache unattempted items**: Query once per session
- **Pre-compute information**: Store I(θ) at discrete θ values
- **Database-level filtering**: Push difficulty window to SQL
- **Index optimization**: Add indexes on `item.b`, `item.topic`

---

## Architecture Benefits

### Separation of Concerns
- **ItemBankService**: Item selection logic
- **AdaptiveEngine**: Theta estimation logic
- **Adaptive Router**: API endpoints & session management
- **Item Models**: Database storage

### Testability
- Unit tests with mocked database
- No database required for core logic tests
- Fast test execution (~0.3s for 17 tests)

### Extensibility
- Add new selection strategies without changing router
- Easy to implement exposure control
- Easy to add content balancing
- Configuration-driven behavior

### Maintainability
- Clear, documented methods
- Type hints throughout
- Comprehensive docstrings with examples
- Modular design

---

## Summary

The ItemBank service completes the adaptive testing infrastructure by providing:

1. ✅ **Intelligent Item Selection** - Maximum information criterion
2. ✅ **Difficulty Filtering** - Focus on items near student ability
3. ✅ **Fallback Logic** - Ensures exam can always continue
4. ✅ **Clean Architecture** - Separation of concerns
5. ✅ **Comprehensive Tests** - 17 passing unit tests
6. ✅ **Future-Ready** - Hooks for exposure control & content balancing

**Total Adaptive Testing Tests**: 86 passing ✅

The system is now production-ready for basic adaptive testing. Future enhancements (exposure control, content balancing) can be added incrementally without disrupting existing functionality.
