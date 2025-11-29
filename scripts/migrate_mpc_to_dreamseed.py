"""
MPCStudy to DreamSeedAI ETL Script

Migrates questions from MPCStudy MySQL database to DreamSeedAI PostgreSQL
with IRT-ready schema and MathLive format.

Usage:
    python scripts/migrate_mpc_to_dreamseed.py --mysql-url "mysql://..." --batch-size 100

Environment Variables:
    MPC_MYSQL_URL: MySQL connection string (e.g., mysql://user:pass@host/mpc_db)
    DREAMSEED_PG_URL: PostgreSQL URL (from backend .env)

Database Schema Mapping:
    mpc_questions → items
        - id → new UUID
        - subject → subject
        - question_html → stem_html (Wiris → MathLive)
        - difficulty_level → b_difficulty (1-5 → -2 to +2)
        - answer_type = 'MCQ' → filter
        - correct_choice → used to set is_correct

    mpc_choices → item_options
        - id → new UUID
        - question_id → item_id (mapped)
        - label → label (A, B, C, D)
        - choice_html → text_html (Wiris → MathLive)
        - is_correct → computed from mpc_questions.correct_choice
"""

import argparse
import asyncio
import os
import sys
from typing import Dict, Optional
from uuid import uuid4

from sqlalchemy import create_engine, text

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import SessionLocal  # type: ignore[import-not-found]
from app.models.exam_models import Item, ItemOption  # type: ignore[import-not-found]
from app.services.wiris_converter import (  # type: ignore[import-not-found]
    convert_wiris_html_to_mathlive,
    estimate_initial_irt_params,
    sanitize_html,
)


async def migrate_mpc_questions(
    mysql_url: str,
    subject_filter: Optional[str] = None,
    batch_size: int = 100,
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Migrate MPCStudy questions to DreamSeedAI.

    Args:
        mysql_url: MySQL connection string
        subject_filter: Only migrate specific subject (e.g., 'math')
        batch_size: Number of questions per batch
        dry_run: If True, print actions without committing

    Returns:
        Statistics dict: {
            'questions_migrated': int,
            'options_created': int,
            'mapping_entries': int,
            'errors': int,
        }
    """
    stats = {
        "questions_migrated": 0,
        "options_created": 0,
        "mapping_entries": 0,
        "errors": 0,
    }

    # Connect to MySQL (source)
    mysql_engine = create_engine(mysql_url)

    # Connect to PostgreSQL (target)
    async_session = SessionLocal()

    try:
        with mysql_engine.connect() as mysql_conn:
            # Build query with optional subject filter
            query = """
                SELECT 
                    q.id, 
                    q.subject, 
                    q.question_html, 
                    q.difficulty_level, 
                    q.correct_choice,
                    q.chapter,
                    q.learning_objective
                FROM mpc_questions q
                WHERE q.answer_type = 'MCQ'
            """

            if subject_filter:
                query += f" AND q.subject = '{subject_filter}'"

            query += " ORDER BY q.id LIMIT :batch_size"

            print(f"📊 Fetching questions from MPCStudy...")
            if subject_filter:
                print(f"   Subject filter: {subject_filter}")

            result = mysql_conn.execute(text(query), {"batch_size": batch_size})
            questions = result.fetchall()

            print(f"✓ Found {len(questions)} questions to migrate\n")

            for idx, row in enumerate(questions, 1):
                mpc_id = row.id
                subject = row.subject
                question_html = row.question_html
                difficulty_level = row.difficulty_level or 3
                correct_choice = row.correct_choice  # e.g., "A"
                chapter = row.chapter
                learning_objective = row.learning_objective

                try:
                    print(
                        f"[{idx}/{len(questions)}] Processing MPC question {mpc_id}..."
                    )

                    # Convert Wiris HTML to MathLive
                    stem_html = convert_wiris_html_to_mathlive(question_html)
                    stem_html = sanitize_html(stem_html)

                    # Estimate initial IRT parameters
                    irt_params = estimate_initial_irt_params(
                        difficulty_level, num_choices=4
                    )

                    # Create Item
                    item = Item(
                        id=uuid4(),
                        subject=subject,
                        stem_html=stem_html,
                        a_discrimination=irt_params["a"],
                        b_difficulty=irt_params["b"],
                        c_guessing=irt_params["c"],
                        max_score=1.0,
                        is_active=True,
                        chapter=chapter,
                        learning_objective=learning_objective,
                    )

                    if not dry_run:
                        async_session.add(item)
                        await async_session.flush()  # Get item.id

                    print(f"   ✓ Item created: {item.id}")
                    print(f"      Subject: {subject}")
                    print(
                        f"      IRT: a={irt_params['a']:.1f}, b={irt_params['b']:+.1f}, c={irt_params['c']:.2f}"
                    )

                    stats["questions_migrated"] += 1

                    # Fetch choices for this question
                    choices_query = """
                        SELECT label, choice_html
                        FROM mpc_choices
                        WHERE question_id = :qid
                        ORDER BY label
                    """
                    choices = mysql_conn.execute(
                        text(choices_query), {"qid": mpc_id}
                    ).fetchall()

                    print(f"   ↳ Found {len(choices)} choices")

                    # Create ItemOptions
                    for choice in choices:
                        label = choice.label  # "A", "B", "C", "D"
                        choice_html = choice.choice_html

                        # Convert Wiris to MathLive
                        option_html = convert_wiris_html_to_mathlive(choice_html)
                        option_html = sanitize_html(option_html)

                        # Determine correctness
                        is_correct = label == correct_choice

                        option = ItemOption(
                            id=uuid4(),
                            item_id=item.id,
                            label=label,
                            text_html=option_html,
                            is_correct=is_correct,
                        )

                        if not dry_run:
                            async_session.add(option)

                        marker = "✓" if is_correct else " "
                        print(f"      [{marker}] {label}: {option_html[:50]}...")

                        stats["options_created"] += 1

                    # Create mapping entry (for traceability)
                    if not dry_run:
                        mapping_query = text(
                            """
                            INSERT INTO mpc_item_mapping (mpc_question_id, item_id, created_at)
                            VALUES (:mpc_id, :item_id, CURRENT_TIMESTAMP)
                        """
                        )
                        await async_session.execute(
                            mapping_query, {"mpc_id": mpc_id, "item_id": str(item.id)}
                        )

                    stats["mapping_entries"] += 1
                    print()

                except Exception as e:
                    print(f"   ✗ ERROR: {e}")
                    stats["errors"] += 1
                    continue

            # Commit transaction
            if not dry_run:
                await async_session.commit()
                print("✓ Transaction committed")
            else:
                print("⚠️  DRY RUN - No changes committed")

    finally:
        await async_session.close()

    return stats


async def create_exam_from_migrated_items(
    exam_title: str,
    subject: str,
    item_limit: int = 200,
) -> str:
    """
    Create an Exam using migrated items.

    Args:
        exam_title: Exam name (e.g., "MPC Math Diagnostic CAT")
        subject: Subject filter (e.g., "math")
        item_limit: Max items in pool

    Returns:
        Exam UUID
    """
    from app.models.exam_models import Exam, ExamItem  # type: ignore[import-not-found]
    from sqlalchemy import select

    async_session = SessionLocal()

    try:
        # Create exam
        exam = Exam(
            id=uuid4(),
            title=exam_title,
            description=f"Migrated from MPCStudy - {subject.upper()} questions",
            subject=subject,
            duration_minutes=60,
            max_questions=20,
            is_adaptive=True,
        )
        async_session.add(exam)
        await async_session.flush()

        print(f"✓ Created exam: {exam.title} ({exam.id})")

        # Find items with matching subject
        stmt = select(Item).where(Item.subject == subject).limit(item_limit)
        result = await async_session.execute(stmt)
        items = result.scalars().all()

        print(f"✓ Found {len(items)} items for subject '{subject}'")

        # Link items to exam
        for item in items:
            exam_item = ExamItem(
                exam_id=exam.id,
                item_id=item.id,
                fixed_order=None,  # CAT → no fixed order
            )
            async_session.add(exam_item)

        await async_session.commit()

        print(f"✓ Linked {len(items)} items to exam")
        print(f"\n🎉 Exam ready: /api/exams/{exam.id}")

        return str(exam.id)

    finally:
        await async_session.close()


async def main():
    parser = argparse.ArgumentParser(
        description="Migrate MPCStudy questions to DreamSeedAI"
    )
    parser.add_argument(
        "--mysql-url",
        default=os.getenv("MPC_MYSQL_URL"),
        help="MySQL connection string (or set MPC_MYSQL_URL env var)",
    )
    parser.add_argument(
        "--subject",
        default=None,
        help="Filter by subject (e.g., 'math', 'english')",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of questions per batch",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without committing to database",
    )
    parser.add_argument(
        "--create-exam",
        action="store_true",
        help="Create exam after migration",
    )

    args = parser.parse_args()

    if not args.mysql_url:
        print("❌ Error: MySQL URL not provided")
        print("   Set MPC_MYSQL_URL environment variable or use --mysql-url")
        sys.exit(1)

    print("🚀 MPCStudy → DreamSeedAI Migration")
    print("=" * 60)
    print(
        f"Source: {args.mysql_url.split('@')[1] if '@' in args.mysql_url else 'MySQL'}"
    )
    print(f"Target: DreamSeedAI PostgreSQL")
    print(f"Subject filter: {args.subject or 'All'}")
    print(f"Batch size: {args.batch_size}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 60)
    print()

    # Run migration
    stats = await migrate_mpc_questions(
        mysql_url=args.mysql_url,
        subject_filter=args.subject,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Migration Summary")
    print("=" * 60)
    print(f"Questions migrated: {stats['questions_migrated']}")
    print(f"Options created:    {stats['options_created']}")
    print(f"Mapping entries:    {stats['mapping_entries']}")
    print(f"Errors:             {stats['errors']}")
    print()

    if stats["errors"] > 0:
        print("⚠️  Some questions failed to migrate (see errors above)")
    else:
        print("✓ All questions migrated successfully!")

    # Optionally create exam
    if args.create_exam and not args.dry_run and stats["questions_migrated"] > 0:
        print("\n" + "=" * 60)
        print("Creating exam from migrated items...")

        exam_id = await create_exam_from_migrated_items(
            exam_title=(
                f"MPC {args.subject.upper()} Diagnostic CAT"
                if args.subject
                else "MPC Mixed CAT"
            ),
            subject=args.subject or "mixed",
            item_limit=200,
        )

        print(f"\n✓ Exam created: {exam_id}")


if __name__ == "__main__":
    asyncio.run(main())
