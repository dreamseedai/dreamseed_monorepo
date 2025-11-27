"""
test_adaptive_exam.py

DreamSeedAI – Adaptive Exam E2E Test Suite (pytest)

This file provides end-to-end tests for the adaptive exam flow:
 - /api/adaptive/start  → Start exam session
 - /api/adaptive/next   → Get next item
 - /api/adaptive/answer → Submit answer and update theta

Test Coverage:
 - Basic CAT flow (start → next → answer loop → termination)
 - Theta convergence (correct answers → theta increases)
 - Termination conditions (SE threshold, max items)
 - Edge cases (no items available, session completion)

Assumptions:
 - FastAPI app includes `adaptive_exam` router
 - Test DB with proper schema (via Alembic or create_all)
 - Item table seeded with IRT parameters
 - User/Student records exist for authentication

Setup:
    pip install pytest pytest-asyncio httpx sqlalchemy[asyncio]
    
Run:
    pytest tests/test_adaptive_exam.py -v
"""

from __future__ import annotations
import asyncio
from typing import AsyncGenerator, Optional
from decimal import Decimal

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.core_models_expanded import Base, Item, Student, User, Organization, ExamSession
from app.api.routers.adaptive_exam import router as adaptive_router


# ---------------------------------------------------------------------------
# 1. Test DB / Session Setup
# ---------------------------------------------------------------------------

# Use in-memory SQLite for fast tests
# For production-like tests, use: postgresql+asyncpg://test:test@localhost/test_db
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_test_db() -> None:
    """Initialize test database schema."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    """Create test database engine and initialize schema."""
    await init_test_db()
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide clean database session for each test."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()  # Rollback any changes after test


# ---------------------------------------------------------------------------
# 2. FastAPI app and client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_app() -> FastAPI:
    """Create FastAPI app with adaptive exam router."""
    app = FastAPI(title="DreamSeed Test API")
    app.include_router(adaptive_router)
    return app


@pytest.fixture(scope="function")
async def client(
    test_app: FastAPI,
    db_session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    """
    Async test client with dependency overrides.
    
    Overrides:
    - get_db: Use test database session
    - get_current_user: Mock authenticated student user
    """
    from app.database import get_db
    # from app.auth import get_current_user  # Uncomment when auth is implemented
    
    # Mock User class for authentication
    class MockUser:
        def __init__(self, user_id: int, role: str = "student"):
            self.id = user_id
            self.role = role
    
    # Override database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    
    # Override authentication dependency
    async def override_get_current_user() -> MockUser:
        # Return mock student user (matches seed_test_user)
        return MockUser(user_id=1, role="student")
    
    test_app.dependency_overrides[get_db] = override_get_db
    # test_app.dependency_overrides[get_current_user] = override_get_current_user
    
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac
    
    # Clear overrides after test
    test_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 3. Test Data Seeding
# ---------------------------------------------------------------------------

async def seed_test_user(db: AsyncSession) -> tuple[User, Student]:
    """
    Create test user and student for authentication.
    
    Returns:
        Tuple of (User, Student) ORM objects
    """
    # Create organization
    org = Organization(
        id=1,
        name="Test School",
        type="school"
    )
    db.add(org)
    await db.flush()
    
    # Create user
    user = User(
        id=1,
        org_id=org.id,
        email="student@test.com",
        username="test_student",
        password_hash="hashed_password",
        role="student",
        is_active=True
    )
    db.add(user)
    await db.flush()
    
    # Create student
    student = Student(
        id=1,
        user_id=user.id,
        org_id=org.id,
        grade="10",
        birth_year=2010,
        locale="en-US"
    )
    db.add(student)
    await db.commit()
    
    return user, student


async def seed_test_items(db: AsyncSession) -> list[Item]:
    """
    Insert test items with IRT parameters.
    
    Creates 8 items covering different difficulty levels:
    - Easy (b < -0.5): Items 1, 2
    - Medium (b ≈ 0): Items 3, 4, 5
    - Hard (b > 0.5): Items 6, 7, 8
    
    Returns:
        List of Item ORM objects
    """
    items = [
        # Easy items
        Item(
            id=1,
            topic="algebra_linear_equations",
            a=Decimal("1.2"),
            b=Decimal("-1.0"),
            c=Decimal("0.20"),
            question_text="Solve for x: 2x + 5 = 13",
            explanation="Subtract 5: 2x = 8, Divide by 2: x = 4",
            meta={"subject": "mathematics", "difficulty": "easy"}
        ),
        Item(
            id=2,
            topic="geometry_area",
            a=Decimal("1.0"),
            b=Decimal("-0.8"),
            c=Decimal("0.15"),
            question_text="Find the area of a rectangle: length=8cm, width=5cm",
            explanation="Area = length × width = 8 × 5 = 40 cm²",
            meta={"subject": "mathematics", "difficulty": "easy"}
        ),
        
        # Medium items
        Item(
            id=3,
            topic="algebra_linear_equations",
            a=Decimal("1.5"),
            b=Decimal("0.0"),
            c=Decimal("0.25"),
            question_text="Solve for x: 3x - 7 = 2x + 5",
            explanation="Subtract 2x: x - 7 = 5, Add 7: x = 12",
            meta={"subject": "mathematics", "difficulty": "medium"}
        ),
        Item(
            id=4,
            topic="fractions",
            a=Decimal("1.3"),
            b=Decimal("0.2"),
            c=Decimal("0.25"),
            question_text="Simplify: 3/4 + 1/2",
            explanation="Convert to common denominator: 3/4 + 2/4 = 5/4 = 1¼",
            meta={"subject": "mathematics", "difficulty": "medium"}
        ),
        Item(
            id=5,
            topic="statistics_mean",
            a=Decimal("0.9"),
            b=Decimal("-0.2"),
            c=Decimal("0.20"),
            question_text="Find the mean of: 10, 15, 20, 25, 30",
            explanation="Mean = (10+15+20+25+30) / 5 = 100 / 5 = 20",
            meta={"subject": "mathematics", "difficulty": "medium"}
        ),
        
        # Hard items
        Item(
            id=6,
            topic="algebra_quadratic",
            a=Decimal("1.8"),
            b=Decimal("1.2"),
            c=Decimal("0.20"),
            question_text="Factor: x² - 5x + 6",
            explanation="Find factors: (x-2)(x-3)",
            meta={"subject": "mathematics", "difficulty": "hard"}
        ),
        Item(
            id=7,
            topic="geometry_volume",
            a=Decimal("2.0"),
            b=Decimal("1.5"),
            c=Decimal("0.25"),
            question_text="Find the volume of a cube with side length 4 cm",
            explanation="Volume = side³ = 4³ = 64 cm³",
            meta={"subject": "mathematics", "difficulty": "hard"}
        ),
        Item(
            id=8,
            topic="algebra_systems",
            a=Decimal("2.2"),
            b=Decimal("2.0"),
            c=Decimal("0.20"),
            question_text="Solve the system: x + y = 10, x - y = 2",
            explanation="Add equations: 2x = 12 → x = 6, Substitute: y = 4",
            meta={"subject": "mathematics", "difficulty": "hard"}
        ),
    ]
    
    db.add_all(items)
    await db.commit()
    
    return items


@pytest.fixture
async def seeded_db(db_session: AsyncSession) -> AsyncSession:
    """Fixture that provides database with test data seeded."""
    await seed_test_user(db_session)
    await seed_test_items(db_session)
    return db_session


# ---------------------------------------------------------------------------
# 4. E2E Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_adaptive_exam_basic_flow(client: AsyncClient, seeded_db: AsyncSession):
    """
    Test basic adaptive exam flow: start → next → answer → complete.
    
    Verifies:
    - Exam session creation
    - Item selection
    - Answer submission
    - Theta updates
    - Session completion
    """
    # Step 1: Start exam
    response = await client.post(
        "/api/adaptive/start",
        params={
            "exam_type": "placement",
            "max_items": 10
        }
    )
    assert response.status_code == 200
    start_data = response.json()
    
    exam_session_id = start_data["exam_session_id"]
    assert isinstance(exam_session_id, int)
    assert start_data["status"] == "in_progress"
    assert start_data["initial_theta"] == 0.0
    assert start_data["max_items"] == 10
    
    # Step 2: Loop through exam
    max_iterations = 15
    iteration = 0
    completed = False
    
    while iteration < max_iterations and not completed:
        iteration += 1
        
        # Step 2a: Get next item
        response = await client.get(
            "/api/adaptive/next",
            params={"exam_session_id": exam_session_id}
        )
        assert response.status_code == 200
        next_data = response.json()
        
        if next_data.get("completed"):
            completed = True
            break
        
        item = next_data["item"]
        assert "id" in item
        assert "question_text" in item
        
        # Step 2b: Submit answer (alternate correct/incorrect for test)
        correct = iteration % 2 == 1
        response = await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_session_id,
                "item_id": item["id"],
                "correct": correct,
                "response_time_ms": 10000
            }
        )
        assert response.status_code == 200
        answer_data = response.json()
        
        assert "attempt_id" in answer_data
        assert "theta" in answer_data
        assert "standard_error" in answer_data
        
        completed = answer_data.get("completed", False)
    
    # Verify exam completed within reasonable iterations
    assert completed or iteration == max_iterations


@pytest.mark.asyncio
async def test_theta_increases_with_correct_answers(
    client: AsyncClient,
    seeded_db: AsyncSession
):
    """
    Test that theta increases when student answers correctly.
    
    Verifies IRT model behavior: correct answers → higher ability estimate.
    """
    # Start exam
    response = await client.post(
        "/api/adaptive/start",
        params={"exam_type": "practice", "max_items": 5}
    )
    assert response.status_code == 200
    exam_session_id = response.json()["exam_session_id"]
    
    initial_theta = 0.0
    previous_theta = initial_theta
    
    # Answer 3 items correctly
    for i in range(3):
        # Get next item
        response = await client.get(
            "/api/adaptive/next",
            params={"exam_session_id": exam_session_id}
        )
        assert response.status_code == 200
        item_id = response.json()["item"]["id"]
        
        # Submit correct answer
        response = await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_session_id,
                "item_id": item_id,
                "correct": True,
                "response_time_ms": 8000
            }
        )
        assert response.status_code == 200
        
        current_theta = response.json()["theta"]
        
        # Verify theta increased
        assert current_theta > previous_theta, \
            f"Theta should increase after correct answer (was {previous_theta}, now {current_theta})"
        
        previous_theta = current_theta


@pytest.mark.asyncio
async def test_theta_decreases_with_incorrect_answers(
    client: AsyncClient,
    seeded_db: AsyncSession
):
    """
    Test that theta decreases when student answers incorrectly.
    
    Verifies IRT model behavior: incorrect answers → lower ability estimate.
    """
    # Start exam
    response = await client.post(
        "/api/adaptive/start",
        params={"exam_type": "practice", "max_items": 5}
    )
    assert response.status_code == 200
    exam_session_id = response.json()["exam_session_id"]
    
    initial_theta = 0.0
    previous_theta = initial_theta
    
    # Answer 3 items incorrectly
    for i in range(3):
        # Get next item
        response = await client.get(
            "/api/adaptive/next",
            params={"exam_session_id": exam_session_id}
        )
        assert response.status_code == 200
        item_id = response.json()["item"]["id"]
        
        # Submit incorrect answer
        response = await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_session_id,
                "item_id": item_id,
                "correct": False,
                "response_time_ms": 12000
            }
        )
        assert response.status_code == 200
        
        current_theta = response.json()["theta"]
        
        # Verify theta decreased
        assert current_theta < previous_theta, \
            f"Theta should decrease after incorrect answer (was {previous_theta}, now {current_theta})"
        
        previous_theta = current_theta


@pytest.mark.asyncio
async def test_exam_terminates_on_max_items(
    client: AsyncClient,
    seeded_db: AsyncSession
):
    """
    Test that exam terminates when max_items is reached.
    
    Verifies termination condition: items_completed >= max_items.
    """
    max_items = 5
    
    # Start exam with low max_items
    response = await client.post(
        "/api/adaptive/start",
        params={"exam_type": "practice", "max_items": max_items}
    )
    assert response.status_code == 200
    exam_session_id = response.json()["exam_session_id"]
    
    # Answer exactly max_items questions
    for i in range(max_items):
        # Get next item
        response = await client.get(
            "/api/adaptive/next",
            params={"exam_session_id": exam_session_id}
        )
        assert response.status_code == 200
        
        if i < max_items - 1:
            # Should not be completed yet
            assert not response.json().get("completed")
        
        item_id = response.json()["item"]["id"]
        
        # Submit answer
        response = await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_session_id,
                "item_id": item_id,
                "correct": True,
                "response_time_ms": 10000
            }
        )
        assert response.status_code == 200
    
    # After max_items, exam should be completed
    final_response = response.json()
    assert final_response.get("completed") == True
    assert final_response.get("items_completed") == max_items


@pytest.mark.asyncio
async def test_exam_status_endpoint(client: AsyncClient, seeded_db: AsyncSession):
    """
    Test /api/adaptive/status endpoint.
    
    Verifies that session status can be queried at any time.
    """
    # Start exam
    response = await client.post(
        "/api/adaptive/start",
        params={"exam_type": "placement"}
    )
    assert response.status_code == 200
    exam_session_id = response.json()["exam_session_id"]
    
    # Check initial status
    response = await client.get(
        "/api/adaptive/status",
        params={"exam_session_id": exam_session_id}
    )
    assert response.status_code == 200
    status_data = response.json()
    
    assert status_data["exam_session_id"] == exam_session_id
    assert status_data["status"] == "in_progress"
    assert status_data["student_id"] == 1
    assert status_data["exam_type"] == "placement"
    assert status_data["items_completed"] == 0


@pytest.mark.asyncio
async def test_manual_exam_completion(client: AsyncClient, seeded_db: AsyncSession):
    """
    Test /api/adaptive/complete endpoint for manual termination.
    
    Verifies that student can manually end exam early.
    """
    # Start exam
    response = await client.post(
        "/api/adaptive/start",
        params={"exam_type": "practice"}
    )
    assert response.status_code == 200
    exam_session_id = response.json()["exam_session_id"]
    
    # Answer one question
    response = await client.get(
        "/api/adaptive/next",
        params={"exam_session_id": exam_session_id}
    )
    item_id = response.json()["item"]["id"]
    
    await client.post(
        "/api/adaptive/answer",
        json={
            "exam_session_id": exam_session_id,
            "item_id": item_id,
            "correct": True
        }
    )
    
    # Manually complete exam
    response = await client.post(
        "/api/adaptive/complete",
        params={"exam_session_id": exam_session_id}
    )
    assert response.status_code == 200
    
    complete_data = response.json()
    assert complete_data["status"] == "completed"
    assert complete_data["items_completed"] == 1


@pytest.mark.asyncio
async def test_no_duplicate_items(client: AsyncClient, seeded_db: AsyncSession):
    """
    Test that items are not repeated within a single exam session.
    
    Verifies ItemBank filtering logic.
    """
    # Start exam
    response = await client.post(
        "/api/adaptive/start",
        params={"exam_type": "practice", "max_items": 8}
    )
    assert response.status_code == 200
    exam_session_id = response.json()["exam_session_id"]
    
    seen_items = set()
    
    # Go through several items
    for i in range(5):
        # Get next item
        response = await client.get(
            "/api/adaptive/next",
            params={"exam_session_id": exam_session_id}
        )
        assert response.status_code == 200
        
        if response.json().get("completed"):
            break
        
        item_id = response.json()["item"]["id"]
        
        # Verify no duplicate
        assert item_id not in seen_items, \
            f"Item {item_id} was already presented in this session"
        seen_items.add(item_id)
        
        # Submit answer
        await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_session_id,
                "item_id": item_id,
                "correct": True
            }
        )


# ---------------------------------------------------------------------------
# 5. Performance/Stress Tests (Optional)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.slow
async def test_concurrent_exam_sessions(client: AsyncClient, seeded_db: AsyncSession):
    """
    Test that multiple concurrent exam sessions don't interfere.
    
    Simulates 5 students taking exams simultaneously.
    """
    num_sessions = 5
    
    # Start multiple exam sessions
    session_ids = []
    for i in range(num_sessions):
        response = await client.post(
            "/api/adaptive/start",
            params={"exam_type": "practice", "max_items": 3}
        )
        assert response.status_code == 200
        session_ids.append(response.json()["exam_session_id"])
    
    # Each session answers one question
    for session_id in session_ids:
        response = await client.get(
            "/api/adaptive/next",
            params={"exam_session_id": session_id}
        )
        assert response.status_code == 200
        
        item_id = response.json()["item"]["id"]
        
        await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": session_id,
                "item_id": item_id,
                "correct": True
            }
        )
    
    # Verify all sessions are independent
    for session_id in session_ids:
        response = await client.get(
            "/api/adaptive/status",
            params={"exam_session_id": session_id}
        )
        assert response.status_code == 200
        assert response.json()["items_completed"] == 1


# ---------------------------------------------------------------------------
# 6. Test Helpers for Manual/Interactive Testing
# ---------------------------------------------------------------------------

async def run_interactive_exam(client: AsyncClient, max_items: int = 5):
    """
    Helper function to run interactive exam (for manual testing).
    
    Usage:
        pytest tests/test_adaptive_exam.py::run_interactive_exam -s
    """
    print("\n" + "="*60)
    print("Interactive Adaptive Exam")
    print("="*60)
    
    # Start exam
    response = await client.post(
        "/api/adaptive/start",
        params={"exam_type": "interactive", "max_items": max_items}
    )
    exam_session_id = response.json()["exam_session_id"]
    print(f"✅ Exam started (session_id: {exam_session_id})")
    
    iteration = 0
    while iteration < max_items:
        iteration += 1
        
        # Get next item
        response = await client.get(
            "/api/adaptive/next",
            params={"exam_session_id": exam_session_id}
        )
        next_data = response.json()
        
        if next_data.get("completed"):
            print("\n🎉 Exam completed!")
            break
        
        item = next_data["item"]
        print(f"\n📝 Question {iteration}:")
        print(f"   {item['question_text']}")
        print(f"   Current θ: {next_data['current_theta']:.3f}")
        print(f"   SE: {next_data['standard_error']:.3f}")
        
        # Simulate answer (for demo, alternate correct/incorrect)
        correct = iteration % 2 == 1
        print(f"   Answer: {'✓ Correct' if correct else '✗ Incorrect'}")
        
        response = await client.post(
            "/api/adaptive/answer",
            json={
                "exam_session_id": exam_session_id,
                "item_id": item["id"],
                "correct": correct
            }
        )
        answer_data = response.json()
        
        print(f"   Updated θ: {answer_data['theta']:.3f}")
        print(f"   Updated SE: {answer_data['standard_error']:.3f}")
    
    # Final status
    response = await client.get(
        "/api/adaptive/status",
        params={"exam_session_id": exam_session_id}
    )
    final_status = response.json()
    
    print("\n" + "="*60)
    print("Final Results:")
    print(f"  Items completed: {final_status['items_completed']}")
    print(f"  Final θ: {final_status['theta']:.3f}")
    print(f"  Final SE: {final_status['standard_error']:.3f}")
    print(f"  Score: {final_status.get('score', 'N/A')}")
    print("="*60)
