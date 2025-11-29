"""
test_adaptive_exam_redis.py

E2E tests for Redis-based adaptive testing system.

This test suite validates the full adaptive exam flow with Redis state storage:
1. Engine state persistence across requests
2. State recovery from DB if Redis fails
3. Concurrent exam handling
4. TTL and cleanup

Requirements:
    pip install pytest pytest-asyncio httpx fakeredis[aioredis]

Run tests:
    pytest backend/tests/test_adaptive_exam_redis.py -v
"""

from decimal import Decimal
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import get_current_user

# Import models (expanded test models)
from app.models.core_models_expanded import (
    Base,
    ExamSession,
    Item,
    Organization,
    Student,
)
from app.models.core_models_expanded import User as CoreUser

# Import API-layer models & security
from app.models.user import User as ApiUser

# Import services
from app.services.adaptive_state_store import AdaptiveEngineStateStore

# Fake Redis for testing
from fakeredis import aioredis as fakeredis
from httpx import AsyncClient

# Import app and dependencies
from main import app
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# ============================================================================
# Test Database Setup (In-Memory SQLite)
# ============================================================================


@pytest_asyncio.fixture
async def db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set True for SQL debugging
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================================================
# Redis Setup (Fake Redis)
# ============================================================================


@pytest_asyncio.fixture
async def fake_redis():
    """Create fake Redis client for testing (no server needed)."""
    client = fakeredis.FakeRedis(decode_responses=True, encoding="utf-8")
    yield client
    await client.flushall()  # Clear after each test


@pytest_asyncio.fixture
async def state_store(fake_redis):
    """Create AdaptiveEngineStateStore with fake Redis."""
    return AdaptiveEngineStateStore(fake_redis, default_ttl=3600)


# ============================================================================
# Test App Setup
# ============================================================================


@pytest_asyncio.fixture
async def test_app(db_session, fake_redis):
    """Create FastAPI test app with dependency overrides."""

    # Override database dependency
    async def override_get_db():
        yield db_session

    # Override Redis dependency
    def override_get_redis():
        return fake_redis

    # Override auth dependency - return mock authenticated API user
    def override_get_current_user():
        return ApiUser(
            id=1,
            email="student@test.com",
            hashed_password="fake",
            full_name="Test Student",
            role="student",
            is_active=True,
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield app

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing."""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Test Data Seeding
# ============================================================================


@pytest_asyncio.fixture
async def seeded_db(db_session):
    """Seed database with test data."""

    # Create organization
    org = Organization(
        name="Test University",
        type="school",
    )
    db_session.add(org)
    await db_session.flush()

    # Create user
    user = CoreUser(
        org_id=org.id,
        username="test_student",
        email="student@test.com",
        password_hash="hashed_password_here",
        role="student",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    # Create student
    student = Student(
        user_id=user.id,
        org_id=org.id,
        grade="10",
    )
    db_session.add(student)
    await db_session.flush()

    # Create test items (8 items: easy, medium, hard)
    items = [
        # Easy items (b < -0.5)
        Item(
            id=1,
            topic="Algebra",
            question_text="What is 2+2?",
            a=Decimal("1.0"),
            b=Decimal("-1.0"),
            c=Decimal("0.2"),
            meta={"difficulty": "easy", "correct_answer": "4"},
        ),
        Item(
            id=2,
            topic="Algebra",
            question_text="Solve: x + 3 = 7",
            a=Decimal("1.2"),
            b=Decimal("-0.8"),
            c=Decimal("0.15"),
            meta={"difficulty": "easy", "correct_answer": "4"},
        ),
        # Medium items (-0.5 <= b <= 0.5)
        Item(
            id=3,
            topic="Geometry",
            question_text="Area of square with side 5?",
            a=Decimal("1.5"),
            b=Decimal("0.0"),
            c=Decimal("0.2"),
            meta={"difficulty": "medium", "correct_answer": "25"},
        ),
        Item(
            id=4,
            topic="Algebra",
            question_text="Solve: 2x - 4 = 10",
            a=Decimal("1.3"),
            b=Decimal("0.2"),
            c=Decimal("0.1"),
            meta={"difficulty": "medium", "correct_answer": "7"},
        ),
        Item(
            id=5,
            topic="Geometry",
            question_text="Pythagorean theorem: a²+b²=?",
            a=Decimal("1.4"),
            b=Decimal("-0.3"),
            c=Decimal("0.15"),
            meta={"difficulty": "medium", "correct_answer": "c²"},
        ),
        # Hard items (b > 0.5)
        Item(
            id=6,
            topic="Calculus",
            question_text="Derivative of x³?",
            a=Decimal("1.8"),
            b=Decimal("1.0"),
            c=Decimal("0.2"),
            meta={"difficulty": "hard", "correct_answer": "3x²"},
        ),
        Item(
            id=7,
            topic="Calculus",
            question_text="∫(2x)dx = ?",
            a=Decimal("2.0"),
            b=Decimal("1.2"),
            c=Decimal("0.1"),
            meta={"difficulty": "hard", "correct_answer": "x²+C"},
        ),
        Item(
            id=8,
            topic="Algebra",
            question_text="Solve quadratic: x²-5x+6=0",
            a=Decimal("1.6"),
            b=Decimal("0.8"),
            c=Decimal("0.15"),
            meta={"difficulty": "hard", "correct_answer": "x=2 or x=3"},
        ),
    ]

    for item in items:
        db_session.add(item)

    await db_session.commit()

    return {"org": org, "user": user, "student": student, "items": items}


# ============================================================================
# Test Cases
# ============================================================================


@pytest.mark.asyncio
async def test_redis_engine_persistence(client, seeded_db, state_store):
    """Test that engine state persists in Redis across requests."""

    # Start exam
    response = await client.post(
        "/api/adaptive/start",
        json={
            "exam_type": "placement",
            "initial_theta": 0.0,
            "max_items": 10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    exam_session_id = data["exam_session_id"]

    # Verify engine state exists in Redis
    exists = await state_store.exists(exam_session_id)
    assert exists is True, "Engine state should be saved in Redis"

    # Get summary from Redis
    summary = await state_store.get_engine_summary(exam_session_id)
    assert summary is not None
    assert summary["theta"] == 0.0
    assert summary["items_completed"] == 0

    # Get next item
    response = await client.get(
        "/api/adaptive/next", params={"exam_session_id": exam_session_id}
    )
    assert response.status_code == 200
    item_data = response.json()["item"]

    # Submit correct answer
    response = await client.post(
        "/api/adaptive/answer",
        json={
            "exam_session_id": exam_session_id,
            "item_id": item_data["id"],
            "correct": True,
        },
    )
    assert response.status_code == 200

    # Verify engine state updated in Redis
    summary = await state_store.get_engine_summary(exam_session_id)
    assert summary["items_completed"] == 1
    assert summary["theta"] > 0.0, "Theta should increase after correct answer"

    # Complete exam
    response = await client.post(
        "/api/adaptive/complete", json={"exam_session_id": exam_session_id}
    )
    assert response.status_code == 200

    # Verify engine state deleted from Redis
    exists = await state_store.exists(exam_session_id)
    assert exists is False, "Engine state should be deleted after completion"


@pytest.mark.asyncio
async def test_redis_state_recovery_from_db(client, seeded_db, state_store, db_session):
    """Test that engine state can be recovered from DB if Redis fails."""

    # Start exam
    response = await client.post(
        "/api/adaptive/start",
        json={
            "exam_type": "practice",
            "max_items": 5,
        },
    )
    exam_session_id = response.json()["exam_session_id"]

    # Answer 3 items
    for i in range(3):
        response = await client.get(
            "/api/adaptive/next", params={"exam_session_id": exam_session_id}
        )
        item_id = response.json()["item"]["id"]

        await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_session_id,
                "item_id": item_id,
                "correct": True,
            },
        )

    # Get theta after 3 correct answers
    summary = await state_store.get_engine_summary(exam_session_id)
    theta_before = summary["theta"]
    assert summary["items_completed"] == 3

    # Simulate Redis failure - delete engine state
    await state_store.delete_engine(exam_session_id)
    exists = await state_store.exists(exam_session_id)
    assert exists is False, "Redis state should be deleted"

    # Answer 4th item - should reconstruct state from DB
    response = await client.get(
        "/api/adaptive/next", params={"exam_session_id": exam_session_id}
    )
    item_id = response.json()["item"]["id"]

    response = await client.post(
        "/api/adaptive/answer",
        json={
            "exam_session_id": exam_session_id,
            "item_id": item_id,
            "correct": True,
        },
    )

    # Verify state was reconstructed correctly
    summary = await state_store.get_engine_summary(exam_session_id)
    assert summary["items_completed"] == 4
    assert (
        abs(summary["theta"] - theta_before) < 1.0
    ), "Reconstructed theta should be close"


@pytest.mark.asyncio
async def test_redis_ttl_extension(client, seeded_db, state_store):
    """Test that TTL can be extended for long exams."""

    # Start exam
    response = await client.post(
        "/api/adaptive/start",
        json={
            "exam_type": "final",
            "max_items": 50,
        },
    )
    exam_session_id = response.json()["exam_session_id"]

    # Check initial TTL (should be ~7200 seconds / 2 hours)
    initial_ttl = await state_store.get_ttl(exam_session_id)
    assert initial_ttl > 7000, f"TTL should be ~7200s, got {initial_ttl}s"

    # Extend TTL by 1 hour
    success = await state_store.extend_ttl(exam_session_id, additional_seconds=3600)
    assert success is True

    # Verify TTL increased
    new_ttl = await state_store.get_ttl(exam_session_id)
    assert new_ttl > initial_ttl, "TTL should increase after extension"
    assert new_ttl > 10000, "TTL should be >10000s after extension"


@pytest.mark.asyncio
async def test_concurrent_exams_redis(client, seeded_db, state_store):
    """Test that multiple concurrent exams maintain separate states in Redis."""

    # Start 3 concurrent exams
    exam_ids = []
    for i in range(3):
        response = await client.post(
            "/api/adaptive/start",
            json={
                "exam_type": f"concurrent_test_{i}",
                "max_items": 10,
            },
        )
        exam_ids.append(response.json()["exam_session_id"])

    # Verify all 3 states exist in Redis
    active_sessions = await state_store.get_all_active_sessions()
    assert len(active_sessions) >= 3, "All exam sessions should be in Redis"

    # Answer items for each exam with different patterns
    # Exam 1: All correct
    for _ in range(3):
        response = await client.get(
            "/api/adaptive/next", params={"exam_session_id": exam_ids[0]}
        )
        item_id = response.json()["item"]["id"]
        await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_ids[0],
                "item_id": item_id,
                "correct": True,
            },
        )

    # Exam 2: All incorrect
    for _ in range(3):
        response = await client.get(
            "/api/adaptive/next", params={"exam_session_id": exam_ids[1]}
        )
        item_id = response.json()["item"]["id"]
        await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_ids[1],
                "item_id": item_id,
                "correct": False,
            },
        )

    # Exam 3: Mixed
    for i in range(3):
        response = await client.get(
            "/api/adaptive/next", params={"exam_session_id": exam_ids[2]}
        )
        item_id = response.json()["item"]["id"]
        await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_ids[2],
                "item_id": item_id,
                "correct": (i % 2 == 0),  # Alternating
            },
        )

    # Verify each exam has correct theta
    summary1 = await state_store.get_engine_summary(exam_ids[0])
    summary2 = await state_store.get_engine_summary(exam_ids[1])
    summary3 = await state_store.get_engine_summary(exam_ids[2])

    assert summary1["theta"] > 0.3, "All correct should increase theta"
    assert summary2["theta"] < -0.3, "All incorrect should decrease theta"
    assert -0.3 < summary3["theta"] < 0.3, "Mixed should be near 0"

    # All should have 3 items
    assert summary1["items_completed"] == 3
    assert summary2["items_completed"] == 3
    assert summary3["items_completed"] == 3


@pytest.mark.asyncio
async def test_redis_cleanup_on_completion(client, seeded_db, state_store):
    """Test that Redis state is properly cleaned up when exam completes."""

    # Start exam with max 3 items
    response = await client.post(
        "/api/adaptive/start",
        json={
            "exam_type": "cleanup_test",
            "max_items": 3,
        },
    )
    exam_session_id = response.json()["exam_session_id"]

    # Verify state exists
    exists = await state_store.exists(exam_session_id)
    assert exists is True

    # Answer 3 items (will trigger auto-completion)
    for _ in range(3):
        response = await client.get(
            "/api/adaptive/next", params={"exam_session_id": exam_session_id}
        )
        if response.json().get("completed"):
            break

        item_id = response.json()["item"]["id"]
        response = await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_session_id,
                "item_id": item_id,
                "correct": True,
            },
        )

        if response.json()["completed"]:
            break

    # Verify Redis state deleted after completion
    exists = await state_store.exists(exam_session_id)
    assert exists is False, "Redis state should be deleted when exam completes"


@pytest.mark.asyncio
async def test_theta_consistency_redis_vs_db(
    client, seeded_db, state_store, db_session
):
    """Test that theta stored in Redis matches theta in database."""

    # Start exam
    response = await client.post(
        "/api/adaptive/start",
        json={
            "exam_type": "consistency_test",
            "initial_theta": 0.5,
            "max_items": 10,
        },
    )
    exam_session_id = response.json()["exam_session_id"]

    # Answer 5 items
    for _ in range(5):
        response = await client.get(
            "/api/adaptive/next", params={"exam_session_id": exam_session_id}
        )
        item_id = response.json()["item"]["id"]

        response = await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_session_id,
                "item_id": item_id,
                "correct": True,
            },
        )

    # Get theta from Redis
    redis_summary = await state_store.get_engine_summary(exam_session_id)
    redis_theta = redis_summary["theta"]

    # Get theta from DB
    from sqlalchemy import select

    stmt = select(ExamSession).where(ExamSession.id == exam_session_id)
    result = await db_session.execute(stmt)
    exam_sess = result.scalar_one()
    db_theta = float(exam_sess.theta)

    # Verify consistency
    assert (
        abs(redis_theta - db_theta) < 0.001
    ), f"Redis theta ({redis_theta}) should match DB theta ({db_theta})"


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.asyncio
async def test_redis_performance_100_concurrent_saves(state_store):
    """Test Redis performance with 100 concurrent engine saves."""
    import asyncio

    from app.services.exam_engine import AdaptiveEngine

    async def save_engine(session_id: int):
        engine = AdaptiveEngine(initial_theta=0.0)
        engine.record_attempt(
            item_id=1, params={"a": 1.5, "b": 0.0, "c": 0.2}, correct=True
        )
        await state_store.save_engine(session_id, engine)

    # Save 100 engines concurrently
    tasks = [save_engine(i) for i in range(100)]
    await asyncio.gather(*tasks)

    # Verify all saved
    active = await state_store.get_all_active_sessions()
    assert len(active) >= 100, "All 100 engines should be saved"


@pytest.mark.asyncio
async def test_redis_performance_load_speed(state_store):
    """Test Redis load performance."""
    import time

    from app.services.exam_engine import AdaptiveEngine

    # Save engine
    engine = AdaptiveEngine(initial_theta=0.5)
    for i in range(20):
        engine.record_attempt(
            item_id=i, params={"a": 1.5, "b": 0.0, "c": 0.2}, correct=(i % 2 == 0)
        )

    await state_store.save_engine(999, engine)

    # Load 100 times and measure time
    start = time.time()
    loaded_engine = None
    for _ in range(100):
        loaded_engine = await state_store.load_engine(999)
    elapsed = time.time() - start

    # Should be <1 second for 100 loads
    assert elapsed < 1.0, f"100 Redis loads took {elapsed:.3f}s, should be <1s"
    assert loaded_engine is not None
    assert loaded_engine.theta == engine.theta
    assert len(loaded_engine.responses) == 20


# ============================================================================
# Helper for Interactive Testing
# ============================================================================


async def run_interactive_redis_exam():
    """
    Interactive exam demo with Redis state inspection.

    Run with:
        python -m pytest backend/tests/test_adaptive_exam_redis.py::run_interactive_redis_exam -s
    """
    print("\n" + "=" * 80)
    print("🧪 INTERACTIVE REDIS ADAPTIVE EXAM DEMO")
    print("=" * 80 + "\n")

    # Setup
    from app.services.exam_engine import AdaptiveEngine
    from fakeredis import aioredis as fakeredis

    redis_client = fakeredis.FakeRedis(decode_responses=True)
    store = AdaptiveEngineStateStore(redis_client)

    # Start exam
    exam_id = 1
    engine = AdaptiveEngine(initial_theta=0.0, max_items=5)
    await store.save_engine(exam_id, engine)

    print(f"📝 Exam Started (ID: {exam_id})")
    print(f"   Initial θ: {engine.theta:.3f}")
    print(f"   Max items: {engine.max_items}")

    # Simulate 5 items
    items = [
        {"id": 1, "a": 1.0, "b": -1.0, "c": 0.2, "correct": True},
        {"id": 2, "a": 1.5, "b": 0.0, "c": 0.15, "correct": True},
        {"id": 3, "a": 1.8, "b": 0.5, "c": 0.2, "correct": False},
        {"id": 4, "a": 1.3, "b": 0.2, "c": 0.1, "correct": True},
        {"id": 5, "a": 2.0, "b": 1.0, "c": 0.2, "correct": True},
    ]

    for i, item in enumerate(items, 1):
        # Load from Redis
        engine = await store.load_engine(exam_id)

        # Record attempt
        engine.record_attempt(
            item_id=item["id"],
            params={"a": item["a"], "b": item["b"], "c": item["c"]},
            correct=item["correct"],
        )

        # Save to Redis
        await store.save_engine(exam_id, engine)

        # Display
        summary = await store.get_engine_summary(exam_id)
        if summary is None:
            raise RuntimeError(
                f"Redis에 exam_id={exam_id} summary가 없습니다. "
                "save_engine이 실패했을 가능성이 있습니다."
            )

        print(f"\n📊 Item {i}/5:")
        print(f"   Difficulty (b): {item['b']:+.2f}")
        print(f"   Response: {'✅ Correct' if item['correct'] else '❌ Incorrect'}")
        print(f"   θ: {summary['theta']:+.3f}")
        print(f"   SE: {summary['standard_error']:.3f}")
        print(f"   TTL: {await store.get_ttl(exam_id)}s")

    # Completion
    await store.delete_engine(exam_id)
    print("\n✅ Exam Completed")
    print(f"   Final θ: {engine.theta:+.3f}")
    print(
        f"   Redis state: {'Deleted' if not await store.exists(exam_id) else 'Still exists'}"
    )
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_interactive_redis_exam())
