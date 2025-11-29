"""
Week 3 Exam Flow - Seed Data

Creates sample exam data for testing:
- 1 Math diagnostic exam
- 10 math items with IRT parameters
- 4 options per item
- Links items to exam

Usage:
  python scripts/seed_week3_exam_data.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.exam_models import (  # type: ignore[import]
    Exam,
    Item,
    ItemOption,
    ExamItem,
)


# Sample math questions with IRT parameters
SAMPLE_ITEMS = [
    {
        "stem_html": "<p>Solve for x: 2x + 5 = 15</p>",
        "a": 1.2, "b": -1.0, "c": 0.2,  # Easy
        "options": [
            {"label": "A", "text": "5", "correct": True},
            {"label": "B", "text": "10", "correct": False},
            {"label": "C", "text": "7.5", "correct": False},
            {"label": "D", "text": "4", "correct": False},
        ]
    },
    {
        "stem_html": "<p>What is 15% of 80?</p>",
        "a": 1.3, "b": -0.5, "c": 0.15,  # Easy-Medium
        "options": [
            {"label": "A", "text": "10", "correct": False},
            {"label": "B", "text": "12", "correct": True},
            {"label": "C", "text": "15", "correct": False},
            {"label": "D", "text": "20", "correct": False},
        ]
    },
    {
        "stem_html": "<p>Solve the equation: x² - 5x + 6 = 0</p>",
        "a": 1.5, "b": 0.0, "c": 0.18,  # Medium
        "options": [
            {"label": "A", "text": "x = 2 or x = 3", "correct": True},
            {"label": "B", "text": "x = 1 or x = 6", "correct": False},
            {"label": "C", "text": "x = -2 or x = -3", "correct": False},
            {"label": "D", "text": "x = 0 or x = 5", "correct": False},
        ]
    },
    {
        "stem_html": "<p>Find the derivative of f(x) = 3x² + 2x - 5</p>",
        "a": 1.4, "b": 0.5, "c": 0.2,  # Medium-Hard
        "options": [
            {"label": "A", "text": "6x + 2", "correct": True},
            {"label": "B", "text": "3x + 2", "correct": False},
            {"label": "C", "text": "6x²", "correct": False},
            {"label": "D", "text": "3x² + 2", "correct": False},
        ]
    },
    {
        "stem_html": "<p>Evaluate the integral: ∫(2x + 1)dx</p>",
        "a": 1.6, "b": 1.0, "c": 0.15,  # Hard
        "options": [
            {"label": "A", "text": "x² + x + C", "correct": True},
            {"label": "B", "text": "2x² + x + C", "correct": False},
            {"label": "C", "text": "x + C", "correct": False},
            {"label": "D", "text": "2x + C", "correct": False},
        ]
    },
    {
        "stem_html": "<p>If sin(θ) = 0.5, what is θ in degrees (0° < θ < 90°)?</p>",
        "a": 1.3, "b": -0.3, "c": 0.2,  # Easy-Medium
        "options": [
            {"label": "A", "text": "30°", "correct": True},
            {"label": "B", "text": "45°", "correct": False},
            {"label": "C", "text": "60°", "correct": False},
            {"label": "D", "text": "90°", "correct": False},
        ]
    },
    {
        "stem_html": "<p>Simplify: (x³y²)/(xy)²</p>",
        "a": 1.4, "b": 0.3, "c": 0.18,  # Medium
        "options": [
            {"label": "A", "text": "x", "correct": True},
            {"label": "B", "text": "y", "correct": False},
            {"label": "C", "text": "x²", "correct": False},
            {"label": "D", "text": "xy", "correct": False},
        ]
    },
    {
        "stem_html": "<p>Find the slope of the line passing through (2, 3) and (6, 11)</p>",
        "a": 1.2, "b": -0.8, "c": 0.15,  # Easy
        "options": [
            {"label": "A", "text": "2", "correct": True},
            {"label": "B", "text": "4", "correct": False},
            {"label": "C", "text": "3", "correct": False},
            {"label": "D", "text": "1", "correct": False},
        ]
    },
    {
        "stem_html": "<p>Solve for x: log₂(x) = 4</p>",
        "a": 1.5, "b": 0.8, "c": 0.2,  # Medium-Hard
        "options": [
            {"label": "A", "text": "16", "correct": True},
            {"label": "B", "text": "8", "correct": False},
            {"label": "C", "text": "4", "correct": False},
            {"label": "D", "text": "2", "correct": False},
        ]
    },
    {
        "stem_html": "<p>Find the value of x: 2ˣ = 32</p>",
        "a": 1.3, "b": 0.0, "c": 0.18,  # Medium
        "options": [
            {"label": "A", "text": "5", "correct": True},
            {"label": "B", "text": "4", "correct": False},
            {"label": "C", "text": "6", "correct": False},
            {"label": "D", "text": "3", "correct": False},
        ]
    },
]


async def seed_data():
    """
    Seed exam data for Week 3 testing.
    """
    DATABASE_URL = "postgresql+asyncpg://dreamseed:dreamseed123@localhost:5433/dreamseed_db"
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Create exam
        exam = Exam(
            title="수학 진단 평가",
            description="CAT 적응형 평가 (약 10-15문항). 당신의 수학 실력을 정확히 측정합니다.",
            subject="math",
            duration_minutes=20,
            max_questions=10,
            is_adaptive=True,
        )
        session.add(exam)
        await session.flush()  # Get exam.id
        
        print(f"✅ Created exam: {exam.title} (ID: {exam.id})")
        
        # 2. Create items
        item_ids = []
        for i, item_data in enumerate(SAMPLE_ITEMS):
            item = Item(
                subject="math",
                stem_html=item_data["stem_html"],
                a_discrimination=item_data["a"],
                b_difficulty=item_data["b"],
                c_guessing=item_data["c"],
                max_score=1.0,
                is_active=True,
            )
            session.add(item)
            await session.flush()  # Get item.id
            item_ids.append(item.id)
            
            # 3. Create options for this item
            for opt_data in item_data["options"]:
                option = ItemOption(
                    item_id=item.id,
                    label=opt_data["label"],
                    text_html=opt_data["text"],
                    is_correct=opt_data["correct"],
                )
                session.add(option)
            
            print(f"  ✅ Created item {i+1}: {item.stem_html[:50]}... (ID: {item.id})")
        
        # 4. Link items to exam
        for item_id in item_ids:
            exam_item = ExamItem(
                exam_id=exam.id,
                item_id=item_id,
            )
            session.add(exam_item)
        
        await session.commit()
        print(f"\n✅ Seeded {len(SAMPLE_ITEMS)} items and linked to exam!")
        print(f"   Exam ID: {exam.id}")
        print(f"   Test at: http://localhost:3001/exams/{exam.id}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
