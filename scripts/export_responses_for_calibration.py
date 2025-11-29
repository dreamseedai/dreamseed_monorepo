#!/usr/bin/env python3
"""
Export exam responses to CSV for R mirt calibration.

This script exports exam_session_responses in long format (user_id, item_id, u)
for offline 3PL IRT calibration using the R mirt package.

Usage:
    python scripts/export_responses_for_calibration.py --subject math --out data/responses.csv
    python scripts/export_responses_for_calibration.py --exam-id UUID --out data/responses.csv
    python scripts/export_responses_for_calibration.py --all --out data/all_responses.csv

Filters:
    - Only completed sessions (status='completed')
    - Only student responses (role='student')
    - Optional: Filter by subject or exam_id

Output CSV format:
    user_id,item_id,u
    550e8400-e29b-41d4-a716-446655440000,7dcb8d58-...,1
    550e8400-e29b-41d4-a716-446655440000,9efc9f61-...,0
    ...

The output can be directly loaded by R/irt_calibrate_mpc.R for mirt calibration.
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Import after adding to path
from app.models.exam_models import (  # type: ignore[import]
    Exam,
    ExamSession,
    ExamSessionResponse,
)
from app.core.database import ASYNC_DATABASE_URL  # type: ignore[import]


async def export_responses(
    output_path: Path,
    subject: Optional[str] = None,
    exam_id: Optional[str] = None,
    min_responses: int = 500,
) -> int:
    """
    Export exam responses to CSV for R mirt calibration.

    Args:
        output_path: Output CSV file path
        subject: Optional subject filter (e.g., "math", "english")
        exam_id: Optional exam UUID filter
        min_responses: Minimum number of responses required (default: 500)

    Returns:
        Number of responses exported

    Raises:
        ValueError: If fewer than min_responses found
    """
    # Create async engine
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Build query
        stmt = (
            select(ExamSessionResponse)
            .join(ExamSessionResponse.session)
            .join(ExamSession.exam)
            .join(ExamSessionResponse.item)
            .options(
                selectinload(ExamSessionResponse.session).selectinload(
                    ExamSession.exam
                ),
                selectinload(ExamSessionResponse.item),
            )
            .where(ExamSession.status == "completed")
            # .where(User.role == "student")  # TODO: Add user role filter when User model available
        )

        # Apply filters
        if subject:
            stmt = stmt.where(Exam.subject == subject)
        if exam_id:
            stmt = stmt.where(Exam.id == exam_id)

        # Execute query
        result = await session.execute(stmt)
        responses = result.scalars().all()

        # Check minimum threshold
        if len(responses) < min_responses:
            raise ValueError(
                f"Only {len(responses)} responses found, need at least {min_responses} "
                f"for reliable IRT calibration. Consider:\n"
                f"  - Removing subject/exam filter (use --all)\n"
                f"  - Collecting more response data\n"
                f"  - Lowering threshold with --min-responses"
            )

        # Write CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["user_id", "item_id", "u"])

            for resp in responses:
                writer.writerow(
                    [
                        str(resp.session.user_id),
                        str(resp.item_id),
                        1 if resp.is_correct else 0,
                    ]
                )

        print(f"✅ Exported {len(responses)} responses to {output_path}")

        # Print summary statistics
        unique_users = len(set(resp.session.user_id for resp in responses))
        unique_items = len(set(resp.item_id for resp in responses))
        correct_count = sum(1 for resp in responses if resp.is_correct)
        accuracy = correct_count / len(responses) if responses else 0

        print(f"\n📊 Summary:")
        print(f"  Students: {unique_users}")
        print(f"  Items: {unique_items}")
        print(f"  Responses per student: {len(responses) / unique_users:.1f}")
        print(f"  Responses per item: {len(responses) / unique_items:.1f}")
        print(f"  Overall accuracy: {accuracy:.1%}")

        if subject:
            print(f"  Subject: {subject}")
        if exam_id:
            print(f"  Exam ID: {exam_id}")

        return len(responses)


async def main():
    parser = argparse.ArgumentParser(
        description="Export exam responses for R mirt calibration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export math responses (requires 500+ responses)
  python scripts/export_responses_for_calibration.py --subject math --out data/math_responses.csv
  
  # Export specific exam
  python scripts/export_responses_for_calibration.py --exam-id UUID --out data/exam_responses.csv
  
  # Export all responses (no filter)
  python scripts/export_responses_for_calibration.py --all --out data/all_responses.csv
  
  # Lower threshold for testing
  python scripts/export_responses_for_calibration.py --subject math --min-responses 100 --out data/test.csv

Next step:
  Run R calibration with: Rscript R/irt_calibrate_mpc.R
        """,
    )

    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output CSV file path (e.g., data/responses.csv)",
    )

    filter_group = parser.add_mutually_exclusive_group(required=True)
    filter_group.add_argument(
        "--subject",
        type=str,
        help="Filter by subject (e.g., math, english)",
    )
    filter_group.add_argument(
        "--exam-id",
        type=str,
        help="Filter by exam UUID",
    )
    filter_group.add_argument(
        "--all",
        action="store_true",
        help="Export all responses (no filter)",
    )

    parser.add_argument(
        "--min-responses",
        type=int,
        default=500,
        help="Minimum number of responses required (default: 500)",
    )

    args = parser.parse_args()

    try:
        await export_responses(
            output_path=args.out,
            subject=args.subject,
            exam_id=args.exam_id,
            min_responses=args.min_responses,
        )

        print(f"\n✅ Ready for R mirt calibration:")
        print(f"   Rscript R/irt_calibrate_mpc.R")
        print(f"\n💡 Set environment variables:")
        print(f"   export PGDATABASE=dreamseed_dev")
        print(f"   export PGHOST=localhost")
        print(f"   export PGPORT=5433")
        print(f"   export PGUSER=dreamseed_user")
        print(f"   export PGPASSWORD=...")
        if args.subject:
            print(f"   export IRT_SUBJECT={args.subject}")
        if args.exam_id:
            print(f"   export IRT_EXAM_ID={args.exam_id}")

        return 0

    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
