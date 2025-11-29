#!/usr/bin/env python3
"""
Seed CAT Items with IRT Parameters

Generates 100+ test items with expert-estimated IRT parameters for CAT engine testing.

IRT Parameters:
- a (discrimination): 0.8 - 2.0 (higher = better discrimination)
- b (difficulty): -2.5 to +2.5 (higher = more difficult)
- c (guessing): 0.15 - 0.25 (probability of guessing correctly)

Subjects: Math, English, Science
Topics: Various per subject
Difficulty Distribution: Normal distribution centered at 0

Usage:
    python scripts/seed_cat_items.py

Requirements:
    - Database must be running
    - Alembic migrations must be applied
    - Virtual environment activated
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
import random

from app.models.item import Item, ItemChoice, ItemPool, ItemPoolMembership  # type: ignore[import-not-found]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:DreamSeedAi0908@127.0.0.1:5432/dreamseed_dev",
)

# Item generation settings
TOTAL_ITEMS = 120  # Generate 120 items (20% buffer)
ITEMS_PER_SUBJECT = 40  # 40 items per subject

# IRT parameter ranges (expert estimates)
IRT_PARAMS = {
    "a_min": 0.8,  # Minimum discrimination
    "a_max": 2.0,  # Maximum discrimination
    "b_min": -2.5,  # Minimum difficulty (easy)
    "b_max": 2.5,  # Maximum difficulty (hard)
    "c_min": 0.15,  # Minimum guessing
    "c_max": 0.25,  # Maximum guessing
}

# Subject and topic definitions
SUBJECTS = {
    "math": {
        "name": "Mathematics",
        "topics": [
            "algebra",
            "geometry",
            "calculus",
            "statistics",
            "linear_equations",
            "quadratic_equations",
            "trigonometry",
            "probability",
        ],
        "difficulty_distribution": "normal",  # Center at b=0
    },
    "english": {
        "name": "English",
        "topics": [
            "reading_comprehension",
            "grammar",
            "vocabulary",
            "writing",
            "literature_analysis",
            "sentence_structure",
            "punctuation",
            "essay",
        ],
        "difficulty_distribution": "normal",
    },
    "science": {
        "name": "Science",
        "topics": [
            "physics",
            "chemistry",
            "biology",
            "earth_science",
            "mechanics",
            "thermodynamics",
            "genetics",
            "ecology",
        ],
        "difficulty_distribution": "normal",
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IRT Parameter Generation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def generate_discrimination(seed: int | None = None) -> float:
    """
    Generate discrimination parameter (a).

    Higher discrimination = item better distinguishes between ability levels.
    Distribution: Slightly skewed towards higher values (1.0-1.5 most common)

    Returns:
        float: Discrimination value (0.8 - 2.0)
    """
    if seed is not None:
        random.seed(seed)

    # Use beta distribution to favor mid-high values
    # Beta(5, 2) gives right-skewed distribution
    beta_sample = random.betavariate(5, 2)

    # Map to [0.8, 2.0] range
    a = IRT_PARAMS["a_min"] + beta_sample * (IRT_PARAMS["a_max"] - IRT_PARAMS["a_min"])
    return round(a, 3)


def generate_difficulty(distribution: str = "normal", seed: int | None = None) -> float:
    """
    Generate difficulty parameter (b).

    Higher b = more difficult item.
    Distribution: Normal (bell curve) centered at 0, or uniform

    Args:
        distribution: "normal" or "uniform"

    Returns:
        float: Difficulty value (-2.5 to +2.5)
    """
    if seed is not None:
        random.seed(seed)

    if distribution == "normal":
        # Normal distribution: mean=0, sd=1.0
        # This gives good spread with most items in -2 to +2 range
        b = random.gauss(0.0, 1.0)
        # Clamp to range
        b = max(IRT_PARAMS["b_min"], min(IRT_PARAMS["b_max"], b))
    else:
        # Uniform distribution
        b = random.uniform(IRT_PARAMS["b_min"], IRT_PARAMS["b_max"])

    return round(b, 3)


def generate_guessing(seed: int | None = None) -> float:
    """
    Generate guessing parameter (c).

    For 4-choice questions: c ≈ 0.25 (random guessing)
    For 5-choice questions: c ≈ 0.20
    We use slightly lower values to account for partial knowledge.

    Returns:
        float: Guessing value (0.15 - 0.25)
    """
    if seed is not None:
        random.seed(seed)

    # Uniform distribution in range
    c = random.uniform(IRT_PARAMS["c_min"], IRT_PARAMS["c_max"])
    return round(c, 3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Question Content Generation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUESTION_TEMPLATES = {
    "math": {
        "algebra": [
            "Solve for x: {eq}",
            "Simplify the expression: {expr}",
            "Factor the polynomial: {poly}",
            "Evaluate: {eval_expr}",
        ],
        "geometry": [
            "Find the area of a {shape} with {dimensions}",
            "Calculate the perimeter of {shape}",
            "What is the volume of {solid}?",
            "Find the angle measure in {scenario}",
        ],
        "calculus": [
            "Find the derivative of f(x) = {func}",
            "Evaluate the integral: ∫{integrand} dx",
            "Find the limit as x approaches {val}: {limit_expr}",
            "Determine if the series converges: {series}",
        ],
    },
    "english": {
        "reading_comprehension": [
            "Based on the passage, what is the main idea?",
            "The author's tone can best be described as:",
            "Which statement best summarizes the argument?",
            "What inference can be drawn from paragraph {n}?",
        ],
        "grammar": [
            "Choose the correct verb form: {sentence}",
            "Which sentence is grammatically correct?",
            "Identify the error in: {sentence}",
            "Select the proper punctuation: {sentence}",
        ],
        "vocabulary": [
            "What does '{word}' most nearly mean?",
            "Choose the best synonym for '{word}':",
            "In context, '{word}' suggests:",
            "Which word best completes: {sentence}?",
        ],
    },
    "science": {
        "physics": [
            "A ball is thrown with velocity {v}. Calculate {quantity}.",
            "What is the force required to {action}?",
            "Calculate the {property} of a {system}.",
            "Which law explains {phenomenon}?",
        ],
        "chemistry": [
            "Balance the equation: {equation}",
            "What is the {property} of {compound}?",
            "Calculate the molarity of {solution}.",
            "Identify the product of: {reaction}",
        ],
        "biology": [
            "Which organelle is responsible for {function}?",
            "What is the process called when {description}?",
            "In genetics, {concept} refers to:",
            "Which system regulates {process}?",
        ],
    },
}


def generate_question_text(
    subject: str, topic: str, difficulty: float
) -> tuple[str, str]:
    """
    Generate question text and explanation based on subject/topic/difficulty.

    Args:
        subject: math, english, science
        topic: Specific topic within subject
        difficulty: b parameter (-2.5 to +2.5)

    Returns:
        tuple: (question_text, explanation)
    """
    templates = QUESTION_TEMPLATES.get(subject, {}).get(topic)

    if not templates:
        # Fallback generic question
        difficulty_label = (
            "easy" if difficulty < -1 else "medium" if difficulty < 1 else "hard"
        )
        return (
            f"{subject.title()} {topic.replace('_', ' ').title()} Question (Difficulty: {difficulty_label})",
            f"This is a placeholder {difficulty_label} question about {topic} in {subject}.",
        )

    # Select template
    template = random.choice(templates)

    # Generate question
    question = template.format(
        eq="2x + 5 = 13",
        expr="(3x² - 5x + 2)",
        poly="x² - 5x + 6",
        eval_expr="f(3) where f(x) = 2x² - x + 1",
        shape="triangle",
        dimensions="base 8cm and height 5cm",
        solid="cylinder with radius 3cm and height 10cm",
        scenario="a right triangle with legs 3 and 4",
        func="x³ - 2x² + x - 5",
        integrand="3x² + 2x - 1",
        val="0",
        limit_expr="(x² - 4)/(x - 2)",
        series="Σ(1/n²) from n=1 to ∞",
        n="2",
        sentence="The students (was/were) ready for the test",
        word="ubiquitous",
        v="10 m/s upward",
        quantity="maximum height",
        action="accelerate a 5kg mass at 2 m/s²",
        property="momentum",
        system="pendulum",
        phenomenon="inertia",
        equation="H₂ + O₂ → H₂O",
        compound="NaCl",
        solution="containing 0.5 mol NaOH in 2L water",
        reaction="CH₄ + 2O₂",
        function="protein synthesis",
        description="cells divide",
        concept="mitosis",
        process="blood sugar levels",
    )

    # Generate explanation
    explanation = (
        f"This question tests understanding of {topic.replace('_', ' ')} concepts. "
    )
    if difficulty < -1:
        explanation += "This is a straightforward application of basic principles."
    elif difficulty < 1:
        explanation += (
            "This requires intermediate understanding and multi-step reasoning."
        )
    else:
        explanation += (
            "This is an advanced problem requiring deep conceptual knowledge."
        )

    return question, explanation


def generate_choices(
    correct_answer: str, num_choices: int = 4
) -> list[tuple[int, str, bool]]:
    """
    Generate multiple choice options.

    Args:
        correct_answer: The correct answer text
        num_choices: Number of choices (default: 4)

    Returns:
        list: [(choice_num, text, is_correct), ...]
    """
    # Place correct answer at random position
    correct_pos = random.randint(1, num_choices)

    choices = []
    for i in range(1, num_choices + 1):
        if i == correct_pos:
            choices.append((i, correct_answer, True))
        else:
            # Generate plausible distractor
            choices.append((i, f"Distractor option {i}", False))

    return choices


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Database Operations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def create_item_pool(session, subject_key: str, subject_data: dict) -> ItemPool:
    """Create or get item pool for a subject."""
    pool = (
        session.query(ItemPool)
        .filter_by(name=f"{subject_data['name']} CAT Pool")
        .first()
    )

    if not pool:
        pool = ItemPool(
            name=f"{subject_data['name']} CAT Pool",
            description=f"Adaptive testing item pool for {subject_data['name']}",
            subject=subject_key,
            grade_level="mixed",
            meta={
                "difficulty_distribution": subject_data["difficulty_distribution"],
                "created_by": "seed_script",
                "version": "1.0",
            },
        )
        session.add(pool)
        session.flush()  # Get ID
        print(f"✅ Created item pool: {pool.name} (ID: {pool.id})")
    else:
        print(f"ℹ️  Item pool already exists: {pool.name} (ID: {pool.id})")

    return pool


def create_items_for_subject(
    session, subject_key: str, subject_data: dict, item_pool: ItemPool, count: int
) -> list[Item]:
    """
    Generate and save items for a specific subject.

    Args:
        session: SQLAlchemy session
        subject_key: Subject identifier (math, english, science)
        subject_data: Subject configuration
        item_pool: ItemPool to associate items with
        count: Number of items to generate

    Returns:
        list: Created Item objects
    """
    items = []
    topics = subject_data["topics"]
    distribution = subject_data["difficulty_distribution"]

    for i in range(count):
        # Rotate through topics
        topic = topics[i % len(topics)]

        # Generate IRT parameters
        a = generate_discrimination(seed=None)
        b = generate_difficulty(distribution, seed=None)
        c = generate_guessing(seed=None)

        # Generate content
        question_text, explanation = generate_question_text(subject_key, topic, b)
        correct_answer = "A"  # Placeholder - choice A is always correct

        # Create item
        item = Item(
            topic=topic,
            question_text=question_text,
            correct_answer=correct_answer,
            explanation=explanation,
            a=Decimal(str(a)),
            b=Decimal(str(b)),
            c=Decimal(str(c)),
            meta={
                "subject": subject_key,
                "difficulty_label": "easy" if b < -1 else "medium" if b < 1 else "hard",
                "generated": True,
                "version": "1.0",
            },
        )

        session.add(item)
        session.flush()  # Get ID

        # Create choices
        choices_data = generate_choices(correct_answer, num_choices=4)
        for choice_num, choice_text, is_correct in choices_data:
            choice = ItemChoice(
                item_id=item.id,
                choice_num=choice_num,
                choice_text=choice_text,
                is_correct=1 if is_correct else 0,
            )
            session.add(choice)

        # Add to pool
        membership = ItemPoolMembership(
            item_id=item.id,
            pool_id=item_pool.id,
            sequence=i + 1,
            weight=Decimal("1.0"),
        )
        session.add(membership)

        items.append(item)

        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{count} items for {subject_key}...")

    return items


def print_irt_statistics(items: list[Item], subject: str):
    """Print IRT parameter statistics for generated items."""
    a_values = [float(item.a) for item in items]
    b_values = [float(item.b) for item in items]
    c_values = [float(item.c) for item in items]

    print(f"\n📊 IRT Statistics for {subject.upper()}:")
    print(
        f"  Discrimination (a): min={min(a_values):.3f}, max={max(a_values):.3f}, "
        f"mean={sum(a_values)/len(a_values):.3f}"
    )
    print(
        f"  Difficulty (b):     min={min(b_values):.3f}, max={max(b_values):.3f}, "
        f"mean={sum(b_values)/len(b_values):.3f}"
    )
    print(
        f"  Guessing (c):       min={min(c_values):.3f}, max={max(c_values):.3f}, "
        f"mean={sum(c_values)/len(c_values):.3f}"
    )

    # Difficulty distribution
    easy = sum(1 for b in b_values if b < -1)
    medium = sum(1 for b in b_values if -1 <= b <= 1)
    hard = sum(1 for b in b_values if b > 1)
    print(f"  Difficulty Distribution: Easy={easy}, Medium={medium}, Hard={hard}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Execution
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main():
    """Main seed data generation function."""
    print("=" * 80)
    print("🌱 DreamSeed CAT Item Seeding Script")
    print("=" * 80)
    print(f"\nDatabase: {DATABASE_URL}")
    print(f"Target: {TOTAL_ITEMS} items ({ITEMS_PER_SUBJECT} per subject)")
    print(
        f"IRT Params: a=[{IRT_PARAMS['a_min']}, {IRT_PARAMS['a_max']}], "
        f"b=[{IRT_PARAMS['b_min']}, {IRT_PARAMS['b_max']}], "
        f"c=[{IRT_PARAMS['c_min']}, {IRT_PARAMS['c_max']}]"
    )
    print("\n" + "-" * 80)

    # Create engine and session
    engine = create_engine(DATABASE_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("\n🔍 Checking existing data...")
        existing_count = session.query(Item).count()
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing items in database.")
            response = input("Do you want to add more items? (yes/no): ").lower()
            if response != "yes":
                print("❌ Aborted by user.")
                return

        print("\n📝 Generating items by subject...")

        all_items = []

        for subject_key, subject_data in SUBJECTS.items():
            print(f"\n🎯 Subject: {subject_data['name']}")

            # Create/get item pool
            pool = create_item_pool(session, subject_key, subject_data)

            # Generate items
            items = create_items_for_subject(
                session, subject_key, subject_data, pool, ITEMS_PER_SUBJECT
            )

            all_items.extend(items)

            # Show statistics
            print_irt_statistics(items, subject_key)

        # Commit transaction
        print("\n💾 Saving to database...")
        session.commit()

        # Final summary
        print("\n" + "=" * 80)
        print("✅ SEED DATA GENERATION COMPLETE")
        print("=" * 80)
        print(f"\n📈 Summary:")
        print(f"  Total Items Created: {len(all_items)}")
        print(f"  Item Pools: {len(SUBJECTS)}")
        print(f"  Subjects: {', '.join(SUBJECTS.keys())}")

        # Distribution summary
        total_a = sum(float(item.a) for item in all_items)
        total_b = sum(float(item.b) for item in all_items)
        total_c = sum(float(item.c) for item in all_items)

        print(f"\n🎲 Overall IRT Parameters:")
        print(f"  Mean Discrimination (a): {total_a/len(all_items):.3f}")
        print(f"  Mean Difficulty (b):     {total_b/len(all_items):.3f}")
        print(f"  Mean Guessing (c):       {total_c/len(all_items):.3f}")

        print("\n✨ Ready for CAT engine testing!")
        print("\nNext steps:")
        print(
            "  1. Verify data: psql -d dreamseed_dev -c 'SELECT COUNT(*) FROM items;'"
        )
        print("  2. Run tests: pytest backend/tests/test_adaptive_exam_e2e.py -v")
        print("  3. Start API: cd backend && uvicorn main:app --reload")

    except Exception as e:
        print(f"\n❌ Error during seed generation: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
