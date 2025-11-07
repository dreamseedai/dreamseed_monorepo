#!/usr/bin/env python3
# cSpell:ignore taganchor
"""Tag anchor items for IRT calibration equating.

This job identifies and tags questions as "anchor" items based on various criteria:
- Existing IRT parameters (well-calibrated items)
- Statistical properties (difficulty, discrimination)
- Manual selection (pre-tagged items)
- Item response count threshold

Usage:
    # Dry-run mode (preview candidates)
    DRY_RUN=true python -m apps.seedtest_api.jobs.tag_anchor_items

    # Actual tagging
    python -m apps.seedtest_api.jobs.tag_anchor_items

    # Verify tags
    python -m apps.seedtest_api.jobs.tag_anchor_items verify
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

from sqlalchemy import text

from ..services.db import get_session


def find_anchor_candidates(
    session,
    min_responses: int = 100,
    min_irt_params: bool = True,
    require_stable_difficulty: bool = True,
    difficulty_range: tuple[float, float] = (-2.0, 2.0),
    discrimination_min: float = 0.5,
) -> List[Dict[str, Any]]:
    """Find candidate items for anchor tagging.

    Criteria:
    - Has IRT parameters in question.meta.irt or mirt_item_params
    - Sufficient response count
    - Difficulty within reasonable range
    - Discrimination above threshold
    - Stable across calibrations (optional)

    Returns list of dicts with: item_id, item_text, params, response_count, reason
    """
    candidates = []

    # Query items with IRT parameters and response counts
    stmt = text("""
        WITH item_stats AS (
            SELECT
                q.id,
                q.question_text,
                q.meta->'irt' AS meta_irt,
                COALESCE(
                    (SELECT params FROM mirt_item_params WHERE item_id = q.id::text ORDER BY fitted_at DESC LIMIT 1),
                    q.meta->'irt'
                ) AS irt_params,
                COUNT(DISTINCT a.student_id) AS user_count,
                COUNT(*) AS attempt_count,
                AVG(CASE WHEN a.correct THEN 1.0 ELSE 0.0 END) AS accuracy
            FROM question q
            LEFT JOIN attempt a ON a.item_id = q.id
            WHERE q.id IS NOT NULL
            GROUP BY q.id, q.question_text, q.meta
        )
        SELECT
            id,
            question_text,
            irt_params,
            user_count,
            attempt_count,
            accuracy
        FROM item_stats
        WHERE irt_params IS NOT NULL
          AND attempt_count >= :min_responses
        ORDER BY attempt_count DESC, user_count DESC
        LIMIT 500
    """)

    rows = session.execute(
        stmt,
        {
            "min_responses": min_responses,
        },
    ).mappings().all()

    for row in rows:
        item_id = row["id"]
        irt_params = row["irt_params"]

        # Parse IRT parameters
        if isinstance(irt_params, str):
            try:
                import json
                irt_params = json.loads(irt_params)
            except Exception:
                continue

        if not isinstance(irt_params, dict):
            continue

        # Extract a, b, c
        try:
            a = float(irt_params.get("a", 0))
            b = float(irt_params.get("b", 0))
            c = float(irt_params.get("c", 0))
        except (ValueError, TypeError):
            continue

        # Apply criteria
        reasons = []

        # Difficulty range check
        if require_stable_difficulty:
            if not (difficulty_range[0] <= b <= difficulty_range[1]):
                continue
            reasons.append(f"difficulty={b:.2f}")

        # Discrimination threshold
        if a < discrimination_min:
            continue
        reasons.append(f"discrimination={a:.2f}")

        # Response count
        reasons.append(f"responses={row['attempt_count']}")

        # Stability check (optional): check if params are consistent across calibrations
        if require_stable_difficulty:
            # Check variance in recent calibrations
            stmt_stability = text("""
                SELECT params->>'b' AS b_val
                FROM mirt_item_params
                WHERE item_id = :item_id
                  AND fitted_at >= NOW() - INTERVAL '90 days'
                ORDER BY fitted_at DESC
                LIMIT 5
            """)
            stability_rows = session.execute(
                stmt_stability, {"item_id": str(item_id)}
            ).fetchall()

            if len(stability_rows) >= 2:
                b_values = [
                    float(r[0]) for r in stability_rows if r[0] is not None
                ]
                if b_values:
                    b_std = (
                        sum((x - sum(b_values) / len(b_values)) ** 2 for x in b_values)
                        / len(b_values)
                    ) ** 0.5
                    if b_std > 0.5:  # High variance
                        continue
                    reasons.append(f"stable_std={b_std:.3f}")

        candidates.append(
            {
                "item_id": item_id,
                "item_text": row["question_text"][:100] if row["question_text"] else "",
                "params": {"a": a, "b": b, "c": c},
                "attempt_count": row["attempt_count"],
                "user_count": row["user_count"],
                "accuracy": float(row["accuracy"]) if row["accuracy"] else 0.0,
                "reasons": reasons,
            }
        )

    return candidates


def tag_items_as_anchor(
    session,
    item_ids: List[int],
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Tag items as anchors by adding "anchor" to question.meta.tags.

    Args:
        session: Database session
        item_ids: List of question IDs to tag
        dry_run: If True, only preview without making changes

    Returns:
        Dict with counts and details
    """
    if not item_ids:
        return {"tagged": 0, "skipped": 0, "errors": 0, "details": []}

    results = {"tagged": 0, "skipped": 0, "errors": 0, "details": []}

    for item_id in item_ids:
        try:
            # Check current tags
            stmt_check = text("""
                SELECT meta->'tags' AS current_tags
                FROM question
                WHERE id = :item_id
            """)
            row = session.execute(stmt_check, {"item_id": item_id}).fetchone()

            if not row:
                results["errors"] += 1
                results["details"].append(
                    {"item_id": item_id, "status": "not_found"}
                )
                continue

            current_tags = row[0]
            if isinstance(current_tags, str):
                try:
                    import json
                    current_tags = json.loads(current_tags)
                except Exception:
                    current_tags = []

            if not isinstance(current_tags, list):
                current_tags = []

            # Check if already tagged
            if "anchor" in current_tags:
                results["skipped"] += 1
                results["details"].append(
                    {"item_id": item_id, "status": "already_tagged"}
                )
                continue

            if not dry_run:
                # Add "anchor" tag
                new_tags = current_tags + ["anchor"]
                stmt_update = text("""
                    UPDATE question
                    SET meta = jsonb_set(
                        COALESCE(meta, '{}'::jsonb),
                        '{tags}',
                        CAST(:tags_json::text AS jsonb),
                        true
                    ),
                    updated_at = NOW()
                    WHERE id = :item_id
                """)
                session.execute(
                    stmt_update,
                    {
                        "item_id": item_id,
                        "tags_json": '["' + '","'.join(new_tags) + '"]',
                    },
                )
                results["tagged"] += 1
                results["details"].append(
                    {"item_id": item_id, "status": "tagged", "tags": new_tags}
                )
            else:
                # Dry-run: just preview
                results["tagged"] += 1  # Count as would-be tagged
                results["details"].append(
                    {
                        "item_id": item_id,
                        "status": "would_tag",
                        "current_tags": current_tags,
                        "new_tags": current_tags + ["anchor"],
                    }
                )

        except Exception as e:
            results["errors"] += 1
            results["details"].append(
                {"item_id": item_id, "status": "error", "error": str(e)}
            )

    if not dry_run:
        session.commit()

    return results


def verify_anchor_tags(session) -> Dict[str, Any]:
    """Verify anchor tags and IRT parameters.

    Returns:
        Dict with verification results
    """
    # Count tagged items
    stmt_count = text("""
        SELECT COUNT(*) AS count
        FROM question
        WHERE meta->'tags' @> '["anchor"]'::jsonb
    """)
    tagged_count = session.execute(stmt_count).fetchone()[0]

    # Count items with IRT params
    stmt_irt = text("""
        SELECT COUNT(*) AS count
        FROM question
        WHERE meta ? 'irt'
          AND meta->'tags' @> '["anchor"]'::jsonb
    """)
    tagged_with_irt = session.execute(stmt_irt).fetchone()[0]

    # List tagged items
    stmt_list = text("""
        SELECT
            id,
            meta->'tags' AS tags,
            meta->'irt' AS irt_params,
            (SELECT COUNT(*) FROM attempt WHERE item_id = question.id) AS attempt_count
        FROM question
        WHERE meta->'tags' @> '["anchor"]'::jsonb
        ORDER BY id
        LIMIT 50
    """)
    tagged_items = session.execute(stmt_list).mappings().all()

    # Count items used in recent calibrations
    stmt_calib = text("""
        SELECT COUNT(DISTINCT mip.item_id) AS count
        FROM mirt_item_params mip
        JOIN question q ON q.id::text = mip.item_id
        WHERE q.meta->'tags' @> '["anchor"]'::jsonb
          AND mip.fitted_at >= NOW() - INTERVAL '30 days'
    """)
    calib_count = session.execute(stmt_calib).fetchone()[0]

    return {
        "tagged_count": tagged_count,
        "tagged_with_irt": tagged_with_irt,
        "used_in_recent_calibration": calib_count,
        "sample_items": [
            {
                "item_id": row["id"],
                "tags": row["tags"],
                "irt_params": row["irt_params"],
                "attempt_count": row["attempt_count"],
            }
            for row in tagged_items
        ],
    }


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Tag anchor items for IRT calibration equating"
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="tag",
        choices=["tag", "verify"],
        help="Action: 'tag' (default) or 'verify'",
    )
    parser.add_argument(
        "--min-responses",
        type=int,
        default=100,
        help="Minimum response count for anchor candidates (default: 100)",
    )
    parser.add_argument(
        "--difficulty-min",
        type=float,
        default=-2.0,
        help="Minimum difficulty (b parameter) (default: -2.0)",
    )
    parser.add_argument(
        "--difficulty-max",
        type=float,
        default=2.0,
        help="Maximum difficulty (b parameter) (default: 2.0)",
    )
    parser.add_argument(
        "--discrimination-min",
        type=float,
        default=0.5,
        help="Minimum discrimination (a parameter) (default: 0.5)",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=50,
        help="Maximum number of candidates to tag (default: 50)",
    )
    parser.add_argument(
        "--item-ids",
        type=str,
        help="Comma-separated list of item IDs to tag (overrides candidate search)",
    )

    args = parser.parse_args()

    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    with get_session() as session:
        if args.action == "verify":
            print("[VERIFY] Checking anchor tags...")
            results = verify_anchor_tags(session)
            print(f"\n✅ Tagged items: {results['tagged_count']}")
            print(f"✅ Tagged items with IRT params: {results['tagged_with_irt']}")
            print(
                f"✅ Used in recent calibration: {results['used_in_recent_calibration']}"
            )
            print("\n📋 Sample items:")
            for item in results["sample_items"][:10]:
                print(
                    f"  - Item {item['item_id']}: {item['attempt_count']} attempts, "
                    f"tags={item['tags']}, irt={item['irt_params'] is not None}"
                )
            return 0

        # Tag action
        if args.item_ids:
            # Tag specific items
            item_ids = [int(x.strip()) for x in args.item_ids.split(",") if x.strip()]
            print(f"[TAG] Tagging {len(item_ids)} specified items...")
            if dry_run:
                print("[DRY_RUN] Preview mode - no changes will be made")
        else:
            # Find candidates
            print("[SEARCH] Finding anchor candidates...")
            candidates = find_anchor_candidates(
                session,
                min_responses=args.min_responses,
                difficulty_range=(args.difficulty_min, args.difficulty_max),
                discrimination_min=args.discrimination_min,
            )

            if not candidates:
                print("[WARN] No candidates found matching criteria")
                return 1

            # Sort by quality (high discrimination, reasonable difficulty, high response count)
            candidates.sort(
                key=lambda x: (
                    x["params"]["a"],  # Higher discrimination
                    -abs(x["params"]["b"]),  # Closer to zero difficulty
                    x["attempt_count"],  # More responses
                ),
                reverse=True,
            )

            # Limit to top candidates
            top_candidates = candidates[: args.max_candidates]
            item_ids = [c["item_id"] for c in top_candidates]

            print(f"[FOUND] {len(candidates)} candidates, selecting top {len(item_ids)}")
            if dry_run:
                print("[DRY_RUN] Preview mode - no changes will be made")
                print("\n📋 Top candidates:")
                for i, cand in enumerate(top_candidates[:20], 1):
                    print(
                        f"  {i}. Item {cand['item_id']}: "
                        f"a={cand['params']['a']:.2f}, b={cand['params']['b']:.2f}, "
                        f"responses={cand['attempt_count']}, reasons={', '.join(cand['reasons'])}"
                    )

        # Tag items
        print(f"\n[TAG] Tagging {len(item_ids)} items as anchors...")
        results = tag_items_as_anchor(session, item_ids, dry_run=dry_run)

        print("\n✅ Results:")
        print(f"  - Tagged: {results['tagged']}")
        print(f"  - Skipped (already tagged): {results['skipped']}")
        print(f"  - Errors: {results['errors']}")

        if results["errors"] > 0:
            print("\n❌ Errors:")
            for detail in results["details"]:
                if detail.get("status") == "error":
                    print(f"  - Item {detail['item_id']}: {detail.get('error')}")

        if not dry_run:
            print("\n✅ Tagging complete!")
        else:
            print("\n[DRY_RUN] No changes made. Set DRY_RUN=false to apply changes.")

        return 0 if results["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
