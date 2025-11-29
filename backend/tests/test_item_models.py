"""
Test suite for Item models (IRT/CAT support)

Tests Item, ItemChoice, ItemPool, and related functionality.
"""
import pytest
from decimal import Decimal

from app.models.item import Item, ItemChoice, ItemPool, ItemPoolMembership


def test_item_creation():
    """Test creating an Item with IRT parameters"""
    item = Item(
        topic="algebra",
        question_text="Solve for x: 2x + 5 = 13",
        correct_answer="4",
        explanation="Subtract 5, then divide by 2",
        a=Decimal("1.2"),
        b=Decimal("0.5"),
        c=Decimal("0.2"),
    )
    
    assert item.topic == "algebra"
    assert item.question_text == "Solve for x: 2x + 5 = 13"
    assert item.a == Decimal("1.2")
    assert item.b == Decimal("0.5")
    assert item.c == Decimal("0.2")


def test_item_to_engine_format():
    """Test converting Item to AdaptiveEngine format"""
    item = Item(
        id=123,
        topic="geometry",
        question_text="What is the area of a circle?",
        a=Decimal("1.5"),
        b=Decimal("0.0"),
        c=Decimal("0.2"),
    )
    
    engine_format = item.to_engine_format()
    
    assert engine_format["id"] == 123
    assert isinstance(engine_format["a"], float)
    assert isinstance(engine_format["b"], float)
    assert isinstance(engine_format["c"], float)
    assert engine_format["a"] == 1.5
    assert engine_format["b"] == 0.0
    assert engine_format["c"] == 0.2


def test_item_choice_creation():
    """Test creating ItemChoice for multiple choice questions"""
    choice = ItemChoice(
        item_id=1,
        choice_num=1,
        choice_text="x = 4",
        is_correct=1,
    )
    
    assert choice.item_id == 1
    assert choice.choice_num == 1
    assert choice.choice_text == "x = 4"
    assert choice.is_correct == 1


def test_item_pool_creation():
    """Test creating an ItemPool"""
    pool = ItemPool(
        name="Grade 8 Math Diagnostic",
        description="Placement test for 8th graders",
        subject="math",
        grade_level="8",
    )
    
    assert pool.name == "Grade 8 Math Diagnostic"
    assert pool.subject == "math"
    assert pool.grade_level == "8"


def test_item_pool_membership_creation():
    """Test creating item-pool membership"""
    membership = ItemPoolMembership(
        item_id=1,
        pool_id=1,
        sequence=1,
        weight=Decimal("1.5"),
    )
    
    assert membership.item_id == 1
    assert membership.pool_id == 1
    assert membership.sequence == 1
    assert membership.weight == Decimal("1.5")


def test_item_irt_parameter_ranges():
    """Test that IRT parameters are within expected ranges"""
    # Good item: moderate discrimination, medium difficulty, low guessing
    item = Item(
        question_text="Test question",
        a=Decimal("1.2"),  # 0.5-2.5 typical
        b=Decimal("0.0"),  # -3 to +3 typical
        c=Decimal("0.2"),  # 0-0.3 typical
    )
    
    # Check ranges
    assert 0.0 < float(item.a) < 3.0  # type: ignore
    assert -4.0 < float(item.b) < 4.0  # type: ignore
    assert 0.0 <= float(item.c) < 0.5  # type: ignore


def test_item_repr():
    """Test Item string representation"""
    item = Item(
        id=123,
        topic="algebra",
        a=Decimal("1.2"),
        b=Decimal("0.5"),
        c=Decimal("0.2"),
    )
    
    repr_str = repr(item)
    assert "Item" in repr_str
    assert "123" in repr_str
    assert "algebra" in repr_str


def test_item_choice_repr():
    """Test ItemChoice string representation"""
    choice = ItemChoice(
        item_id=1,
        choice_num=2,
        is_correct=1,
    )
    
    repr_str = repr(choice)
    assert "ItemChoice" in repr_str
    assert "item_id=1" in repr_str
    assert "num=2" in repr_str


def test_item_pool_repr():
    """Test ItemPool string representation"""
    pool = ItemPool(
        id=1,
        name="Test Pool",
        subject="math",
    )
    
    repr_str = repr(pool)
    assert "ItemPool" in repr_str
    assert "Test Pool" in repr_str
    assert "math" in repr_str


def test_multiple_choices_for_item():
    """Test creating multiple choices for one item"""
    choices = [
        ItemChoice(item_id=1, choice_num=1, choice_text="A", is_correct=0),
        ItemChoice(item_id=1, choice_num=2, choice_text="B", is_correct=1),
        ItemChoice(item_id=1, choice_num=3, choice_text="C", is_correct=0),
        ItemChoice(item_id=1, choice_num=4, choice_text="D", is_correct=0),
    ]
    
    assert len(choices) == 4
    assert sum(c.is_correct for c in choices) == 1  # Only one correct
    assert all(c.item_id == 1 for c in choices)


def test_item_metadata():
    """Test Item with JSONB metadata"""
    item = Item(
        question_text="Test",
        a=Decimal("1.0"),
        b=Decimal("0.0"),
        c=Decimal("0.2"),
        meta={
            "difficulty_label": "medium",
            "grade_level": 8,
            "standard": "CCSS.MATH.8.EE.A.2",
            "tags": ["linear_equations", "problem_solving"]
        }
    )
    
    assert item.meta is not None
    assert item.meta["difficulty_label"] == "medium"
    assert item.meta["grade_level"] == 8
    assert len(item.meta["tags"]) == 2


def test_item_pool_metadata():
    """Test ItemPool with configuration metadata"""
    pool = ItemPool(
        name="Timed Test",
        meta={
            "max_items": 20,
            "time_limit_minutes": 30,
            "adaptive": True,
            "termination_se": 0.3,
        }
    )
    
    assert pool.meta["max_items"] == 20
    assert pool.meta["time_limit_minutes"] == 30
    assert pool.meta["adaptive"] is True


def test_easy_item():
    """Test creating an easy item (negative b)"""
    item = Item(
        question_text="What is 2 + 2?",
        correct_answer="4",
        a=Decimal("1.0"),
        b=Decimal("-1.5"),  # Easy
        c=Decimal("0.25"),
    )
    
    assert float(item.b) < 0  # type: ignore
    assert item.correct_answer == "4"


def test_hard_item():
    """Test creating a hard item (positive b)"""
    item = Item(
        question_text="Solve the differential equation...",
        a=Decimal("1.8"),
        b=Decimal("2.0"),  # Hard
        c=Decimal("0.1"),
    )
    
    assert float(item.b) > 1.0  # type: ignore


def test_high_discrimination_item():
    """Test item with high discrimination (a)"""
    item = Item(
        question_text="Test",
        a=Decimal("2.5"),  # High discrimination
        b=Decimal("0.0"),
        c=Decimal("0.2"),
    )
    
    assert float(item.a) > 2.0  # type: ignore


def test_low_guessing_item():
    """Test item with very low guessing parameter"""
    item = Item(
        question_text="Open-ended question",
        a=Decimal("1.5"),
        b=Decimal("0.5"),
        c=Decimal("0.0"),  # No guessing for constructed response
    )
    
    assert float(item.c) == 0.0  # type: ignore


def test_pool_membership_with_weight():
    """Test weighted item in pool"""
    membership = ItemPoolMembership(
        item_id=1,
        pool_id=1,
        weight=Decimal("2.0"),  # Double weight
    )
    
    assert float(membership.weight) == 2.0  # type: ignore
