#!/usr/bin/env python3
"""
Batch update question.meta.irt from mirt_item_params.

This job syncs finalized IRT parameters from mirt_item_params to question.meta.irt.
Useful for:
- Backfilling question.meta after calibration
- Ensuring question.meta is in sync with calibration results
- Making IRT parameters available for online scoring

Environment:
  BATCH_SIZE (optional): Number of items to process per transaction (default: 100)
  DRY_RUN (optional): If "true", skip actual updates (default: false)
"""
# cSpell:ignore mirt
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


# Ensure "apps.*" imports work
def _ensure_project_root_on_path() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "apps" / "seedtest_api").is_dir():
            path_str = str(parent)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
            break


_ensure_project_root_on_path()

import sqlalchemy as sa
from apps.seedtest_api.services.db import get_session


def update_question_meta_batch(batch_size: int = 100, dry_run: bool = False) -> dict:
    """Update question.meta.irt from mirt_item_params.

    Args:
        batch_size: Number of items to process per transaction
        dry_run: If True, skip actual updates

    Returns:
        Dictionary with stats: {processed, updated, skipped, failed}
    """
    stats = {"processed": 0, "updated": 0, "skipped": 0, "failed": 0}

    stmt_select = sa.text(
        """
        SELECT 
            mip.item_id,
            mip.model,
            mip.params,
            mip.version,
            mip.fitted_at,
            q.id IS NOT NULL AS question_exists
        FROM mirt_item_params mip
        LEFT JOIN question q ON q.id::text = mip.item_id
        WHERE mip.fitted_at >= (
            SELECT MAX(fitted_at) - INTERVAL '7 days'
            FROM mirt_item_params
        )
        ORDER BY mip.fitted_at DESC
        LIMIT :limit
        """
    )

    stmt_update = sa.text(
        """
        UPDATE question
        SET meta = jsonb_set(
            COALESCE(meta, '{}'::jsonb),
            '{irt}',
            CAST(:irt_json::text AS jsonb),
            true
        ),
        updated_at = NOW()
        WHERE id = :question_id
        """
    )

    with get_session() as session:
        # Load recent item params
        result = session.execute(
            stmt_select,
            {"limit": batch_size * 10},  # Load more to account for missing questions
        )
        rows = result.mappings().all()

        if not rows:
            print("[INFO] No recent mirt_item_params found")
            return stats

        print(
            f"[INFO] Found {len(rows)} recent item params; processing in batches of {batch_size}"
        )

        for idx, row in enumerate(rows, 1):
            item_id_str = str(row["item_id"])
            question_exists = bool(row["question_exists"])

            if not question_exists:
                stats["skipped"] += 1
                if idx % 100 == 0:
                    print(
                        f"[PROGRESS] {idx}/{len(rows)} processed; updated={stats['updated']}, skipped={stats['skipped']}"
                    )
                continue

            try:
                # Extract IRT parameters
                params = (
                    row["params"]
                    if isinstance(row["params"], dict)
                    else json.loads(str(row["params"]))
                )
                question_id = int(item_id_str)

                irt_meta = {
                    "a": params.get("a"),
                    "b": params.get("b"),
                    "c": params.get("c"),
                    "model": str(row["model"] or "2PL"),
                    "version": str(row["version"] or "v1"),
                }
                # Remove None values
                irt_meta = {k: v for k, v in irt_meta.items() if v is not None}

                if not dry_run:
                    session.execute(
                        stmt_update,
                        {
                            "question_id": question_id,
                            "irt_json": json.dumps(irt_meta),
                        },
                    )

                stats["updated"] += 1

                # Commit in batches
                if idx % batch_size == 0:
                    if not dry_run:
                        session.commit()
                    print(
                        f"[PROGRESS] {idx}/{len(rows)} processed; updated={stats['updated']}, skipped={stats['skipped']}"
                    )

            except (ValueError, Exception) as e:
                stats["failed"] += 1
                print(f"[WARN] Failed to update question_id={item_id_str}: {e}")
                continue

        # Final commit
        if not dry_run:
            session.commit()

        stats["processed"] = len(rows)

    return stats


def main() -> int:
    """CLI entry point."""
    batch_size = int(os.getenv("BATCH_SIZE", "100"))
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    print(
        f"[INFO] Starting question.meta.irt update; batch_size={batch_size}, dry_run={dry_run}"
    )

    stats = update_question_meta_batch(batch_size=batch_size, dry_run=dry_run)

    print(
        f"[INFO] Update complete: processed={stats['processed']}, "
        f"updated={stats['updated']}, skipped={stats['skipped']}, failed={stats['failed']}"
    )

    if stats["failed"] > 0:
        return 1
    if stats["updated"] == 0 and stats["processed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
