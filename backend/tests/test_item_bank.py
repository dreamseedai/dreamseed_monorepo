"""
Test suite for ItemBank Service

Tests item selection, filtering, and ranking for adaptive testing.
"""

import pytest
from unittest.mock import Mock, MagicMock
from decimal import Decimal

from app.core.services.item_bank import ItemBankService
from app.models.item import Item
from app.models.core_entities import Attempt


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Fixtures
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def item_bank(mock_db):
    """ItemBank service instance"""
    return ItemBankService(mock_db)


@pytest.fixture
def sample_items():
    """Sample items with varying difficulty"""
    return [
        Item(id=1, a=Decimal("1.5"), b=Decimal("-1.0"), c=Decimal("0.2"), topic="algebra"),
        Item(id=2, a=Decimal("1.2"), b=Decimal("0.0"), c=Decimal("0.2"), topic="algebra"),
        Item(id=3, a=Decimal("1.8"), b=Decimal("1.0"), c=Decimal("0.1"), topic="geometry"),
        Item(id=4, a=Decimal("1.0"), b=Decimal("2.0"), c=Decimal("0.25"), topic="calculus"),
        Item(id=5, a=Decimal("2.0"), b=Decimal("-0.5"), c=Decimal("0.15"), topic="algebra"),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Load Unattempted Items
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_load_unattempted_items_no_attempts(item_bank, mock_db, sample_items):
    """Test loading items when no attempts exist"""
    # Create query chain mocks
    mock_attempt_query = Mock()
    mock_attempt_query.filter.return_value = mock_attempt_query
    mock_attempt_query.all.return_value = []
    
    mock_item_query = Mock()
    mock_item_query.filter.return_value = mock_item_query
    mock_item_query.all.return_value = sample_items
    
    # Use list to track call order
    query_calls = [mock_attempt_query, mock_item_query]
    call_index = [0]
    
    def query_side_effect(*args, **kwargs):
        result = query_calls[call_index[0]]
        call_index[0] += 1
        return result
    
    mock_db.query.side_effect = query_side_effect
    
    items = item_bank.load_unattempted_items(exam_session_id=1)
    
    assert len(items) == 5
    assert items == sample_items


def test_load_unattempted_items_with_attempts(item_bank, mock_db, sample_items):
    """Test loading items excluding attempted ones"""
    # Mock attempted items
    attempted = [(1,), (3,)]  # Items 1 and 3 attempted
    
    mock_attempt_query = Mock()
    mock_attempt_query.filter.return_value = mock_attempt_query
    mock_attempt_query.all.return_value = attempted
    
    # Mock item query - return items 2, 4, 5
    unattempted = [sample_items[1], sample_items[3], sample_items[4]]
    mock_item_query = Mock()
    mock_item_query.filter.return_value = mock_item_query
    mock_item_query.all.return_value = unattempted
    
    query_calls = [mock_attempt_query, mock_item_query]
    call_index = [0]
    
    def query_side_effect(*args, **kwargs):
        result = query_calls[call_index[0]]
        call_index[0] += 1
        return result
    
    mock_db.query.side_effect = query_side_effect
    
    items = item_bank.load_unattempted_items(exam_session_id=1)
    
    assert len(items) == 3
    assert all(item.id not in [1, 3] for item in items)


def test_load_unattempted_items_with_topic_filter(item_bank, mock_db, sample_items):
    """Test loading items filtered by topic"""
    mock_attempt_query = Mock()
    mock_attempt_query.filter.return_value = mock_attempt_query
    mock_attempt_query.all.return_value = []
    
    # Mock item query - return only algebra items
    algebra_items = [item for item in sample_items if item.topic == "algebra"]
    mock_item_query = Mock()
    mock_item_query.filter.return_value = mock_item_query
    mock_item_query.all.return_value = algebra_items
    
    query_calls = [mock_attempt_query, mock_item_query]
    call_index = [0]
    
    def query_side_effect(*args, **kwargs):
        result = query_calls[call_index[0]]
        call_index[0] += 1
        return result
    
    mock_db.query.side_effect = query_side_effect
    
    items = item_bank.load_unattempted_items(
        exam_session_id=1,
        topic="algebra"
    )
    
    assert len(items) == 3
    assert all(item.topic == "algebra" for item in items)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Difficulty Window Filtering
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_filter_by_difficulty_within_window(item_bank, sample_items):
    """Test filtering items within difficulty window"""
    theta = 0.0
    window = 1.0
    
    filtered = item_bank.filter_by_difficulty(sample_items, theta, window)
    
    # Items with b in [-1.0, 1.0]: items 1, 2, 3, 5
    assert len(filtered) == 4
    item_ids = [item["id"] for item in filtered]
    assert 1 in item_ids  # b = -1.0
    assert 2 in item_ids  # b = 0.0
    assert 3 in item_ids  # b = 1.0
    assert 5 in item_ids  # b = -0.5
    assert 4 not in item_ids  # b = 2.0 (outside window)


def test_filter_by_difficulty_narrow_window(item_bank, sample_items):
    """Test filtering with narrow difficulty window"""
    theta = 0.0
    window = 0.5
    
    filtered = item_bank.filter_by_difficulty(sample_items, theta, window)
    
    # Items with b in [-0.5, 0.5]: items 2, 5
    assert len(filtered) == 2
    item_ids = [item["id"] for item in filtered]
    assert 2 in item_ids  # b = 0.0
    assert 5 in item_ids  # b = -0.5


def test_filter_by_difficulty_high_theta(item_bank, sample_items):
    """Test filtering for high ability student"""
    theta = 1.5
    window = 1.0
    
    filtered = item_bank.filter_by_difficulty(sample_items, theta, window)
    
    # Items with b in [0.5, 2.5]: items 3, 4
    assert len(filtered) == 2
    item_ids = [item["id"] for item in filtered]
    assert 3 in item_ids  # b = 1.0
    assert 4 in item_ids  # b = 2.0


def test_filter_by_difficulty_returns_dicts(item_bank, sample_items):
    """Test that filtering returns dicts with IRT params"""
    theta = 0.0
    window = 1.0
    
    filtered = item_bank.filter_by_difficulty(sample_items, theta, window)
    
    assert len(filtered) > 0
    for item_dict in filtered:
        assert "id" in item_dict
        assert "a" in item_dict
        assert "b" in item_dict
        assert "c" in item_dict
        assert isinstance(item_dict["a"], float)
        assert isinstance(item_dict["b"], float)
        assert isinstance(item_dict["c"], float)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Information-Based Ranking
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_rank_by_information(item_bank):
    """Test ranking items by Fisher information"""
    items = [
        {"id": 1, "a": 1.0, "b": -1.0, "c": 0.2},
        {"id": 2, "a": 1.5, "b": 0.0, "c": 0.2},
        {"id": 3, "a": 1.0, "b": 1.0, "c": 0.2},
    ]
    theta = 0.0
    
    ranked = item_bank.rank_by_information(theta, items)
    
    assert len(ranked) == 3
    # All items should have info key
    assert all("info" in item for item in ranked)
    # First item should have highest info
    assert ranked[0]["info"] >= ranked[1]["info"]
    assert ranked[1]["info"] >= ranked[2]["info"]
    # All info values should be positive
    assert all(item["info"] > 0 for item in ranked)


def test_rank_by_information_includes_info(item_bank):
    """Test that ranking includes Fisher information values"""
    items = [
        {"id": 1, "a": 1.2, "b": 0.5, "c": 0.2},
        {"id": 2, "a": 1.5, "b": -0.5, "c": 0.1},
    ]
    theta = 0.0
    
    ranked = item_bank.rank_by_information(theta, items)
    
    for item in ranked:
        assert "info" in item
        assert isinstance(item["info"], float)
        assert item["info"] >= 0


def test_rank_by_information_sorted_descending(item_bank):
    """Test that ranking is in descending order"""
    items = [
        {"id": 1, "a": 1.0, "b": -1.0, "c": 0.2},
        {"id": 2, "a": 1.5, "b": 0.0, "c": 0.2},
        {"id": 3, "a": 1.2, "b": 0.5, "c": 0.1},
    ]
    theta = 0.0
    
    ranked = item_bank.rank_by_information(theta, items)
    
    # Verify descending order
    for i in range(len(ranked) - 1):
        assert ranked[i]["info"] >= ranked[i + 1]["info"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Combined Candidate Selection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_get_candidate_items_full_pipeline(item_bank, mock_db, sample_items):
    """Test full candidate selection pipeline"""
    mock_attempt_query = Mock()
    mock_attempt_query.filter.return_value = mock_attempt_query
    mock_attempt_query.all.return_value = []
    
    mock_item_query = Mock()
    mock_item_query.filter.return_value = mock_item_query
    mock_item_query.all.return_value = sample_items
    
    query_calls = [mock_attempt_query, mock_item_query]
    call_index = [0]
    
    def query_side_effect(*args, **kwargs):
        result = query_calls[call_index[0]]
        call_index[0] += 1
        return result
    
    mock_db.query.side_effect = query_side_effect
    
    candidates = item_bank.get_candidate_items(
        exam_session_id=1,
        theta=0.0,
        window=1.0
    )
    
    assert len(candidates) > 0
    # Should be sorted by information
    for i in range(len(candidates) - 1):
        assert candidates[i]["info"] >= candidates[i + 1]["info"]


def test_get_candidate_items_fallback_when_no_match(item_bank, mock_db, sample_items):
    """Test fallback to all items when difficulty filter too restrictive"""
    mock_attempt_query = Mock()
    mock_attempt_query.filter.return_value = mock_attempt_query
    mock_attempt_query.all.return_value = []
    
    mock_item_query = Mock()
    mock_item_query.filter.return_value = mock_item_query
    mock_item_query.all.return_value = sample_items
    
    query_calls = [mock_attempt_query, mock_item_query]
    call_index = [0]
    
    def query_side_effect(*args, **kwargs):
        result = query_calls[call_index[0]]
        call_index[0] += 1
        return result
    
    mock_db.query.side_effect = query_side_effect
    
    # Use very narrow window at extreme theta
    candidates = item_bank.get_candidate_items(
        exam_session_id=1,
        theta=5.0,  # Very high theta
        window=0.1  # Very narrow window
    )
    
    # Should fall back to all items
    assert len(candidates) == 5


def test_get_candidate_items_empty_when_all_attempted(item_bank, mock_db):
    """Test empty result when all items attempted"""
    mock_attempt_query = Mock()
    mock_attempt_query.filter.return_value = mock_attempt_query
    mock_attempt_query.all.return_value = []
    
    mock_item_query = Mock()
    mock_item_query.filter.return_value = mock_item_query
    mock_item_query.all.return_value = []  # No unattempted items
    
    query_calls = [mock_attempt_query, mock_item_query]
    call_index = [0]
    
    def query_side_effect(*args, **kwargs):
        result = query_calls[call_index[0]]
        call_index[0] += 1
        return result
    
    mock_db.query.side_effect = query_side_effect
    
    candidates = item_bank.get_candidate_items(
        exam_session_id=1,
        theta=0.0
    )
    
    assert candidates == []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Pick Best Item
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_pick_best_item_returns_first(item_bank):
    """Test that pick_best_item returns first (highest info) item"""
    ranked = [
        {"id": 2, "a": 1.5, "b": 0.0, "c": 0.2, "info": 0.8},
        {"id": 1, "a": 1.0, "b": -1.0, "c": 0.2, "info": 0.5},
        {"id": 3, "a": 1.0, "b": 1.0, "c": 0.2, "info": 0.3},
    ]
    
    best = item_bank.pick_best_item(ranked)
    
    assert best is not None
    assert best["id"] == 2
    assert best["info"] == 0.8


def test_pick_best_item_returns_none_when_empty(item_bank):
    """Test that pick_best_item returns None for empty list"""
    best = item_bank.pick_best_item([])
    
    assert best is None


def test_pick_best_item_single_item(item_bank):
    """Test pick_best_item with single candidate"""
    ranked = [
        {"id": 1, "a": 1.2, "b": 0.5, "c": 0.2, "info": 0.6}
    ]
    
    best = item_bank.pick_best_item(ranked)
    
    assert best is not None
    assert best["id"] == 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Service Initialization
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_item_bank_service_initialization(mock_db):
    """Test ItemBankService initialization"""
    service = ItemBankService(mock_db)
    
    assert service.session == mock_db


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Integration Test Markers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.skip(reason="Requires database setup")
def test_item_bank_integration():
    """Integration test with real database"""
    # TODO: Implement when database is available
    pass
